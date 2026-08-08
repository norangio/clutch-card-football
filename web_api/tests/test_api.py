import asyncio
import json

from ccf_pygame.ccf.states import GamePhase

from web_api.app import create_app
from web_api.store import MemorySessionStore


SETUP = {
    "home": {
        "name": "Wolverines",
        "rating": 7,
        "kick_rating": 2,
        "color": "red",
        "clutch": 2,
    },
    "away": {
        "name": "Buckeyes",
        "rating": 6,
        "kick_rating": 2,
        "clutch": 2,
    },
    "difficulty": "hard",
    "seed": 42,
}


async def _asgi_request(app, method, path, body=None):
    raw_body = b"" if body is None else json.dumps(body).encode()
    request_sent = False
    response = {"status": None, "headers": [], "body": bytearray()}

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {
                "type": "http.request",
                "body": raw_body,
                "more_body": False,
            }
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.start":
            response["status"] = message["status"]
            response["headers"] = message.get("headers", [])
        elif message["type"] == "http.response.body":
            response["body"].extend(message.get("body", b""))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(raw_body)).encode()),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    await app(scope, receive, send)
    parsed = json.loads(response["body"]) if response["body"] else None
    return response["status"], parsed


def request(app, method, path, body=None):
    return asyncio.run(_asgi_request(app, method, path, body))


def make_app():
    seeds = iter([1001, 1002, 1003])
    ids = iter(["game-one", "game-two", "game-three"])
    store = MemorySessionStore()
    app = create_app(
        store=store,
        seed_factory=lambda: next(seeds),
        id_factory=lambda: next(ids),
    )
    return app, store


def create_game(app, setup=None):
    status, payload = request(app, "POST", "/api/games", setup or SETUP)
    assert status == 200
    return payload


def test_health_create_and_resume_follow_contract():
    app, _ = make_app()

    status, health = request(app, "GET", "/healthz")
    created = create_game(app)
    game_id = created["snapshot"]["game_id"]
    resume_status, resumed = request(app, "GET", f"/api/games/{game_id}")

    assert status == 200
    assert health == {"status": "ok"}
    assert created["revision"] == 0
    assert created["snapshot"]["phase"] == "WAITING_OFFENSE_CARD"
    assert created["snapshot"]["viewer_seat"] == "home"
    assert created["events"][0]["type"] == "quarter_started"
    assert "seed" not in json.dumps(created)
    assert "hand" in created["snapshot"]["home"]
    assert "hand" not in created["snapshot"]["away"]
    assert resume_status == 200
    assert resumed["events"] == []
    assert resumed["snapshot"] == created["snapshot"]


def test_accepted_action_increments_once_and_duplicate_is_non_mutating_409():
    app, _ = make_app()
    created = create_game(app)
    game_id = created["snapshot"]["game_id"]
    action = {"revision": 0, "type": "play_card", "card_index": 0}

    status, accepted = request(
        app, "POST", f"/api/games/{game_id}/actions", action
    )
    stale_status, stale = request(
        app, "POST", f"/api/games/{game_id}/actions", action
    )
    _, resumed = request(app, "GET", f"/api/games/{game_id}")

    assert status == 200
    assert accepted["revision"] == 1
    opponent_plays = [
        event
        for event in accepted["events"]
        if event["type"] == "card_played" and event["seat"] == "away"
    ]
    assert opponent_plays
    assert all(event["card"] is None for event in opponent_plays)
    assert any(event["type"] == "cards_revealed" for event in accepted["events"])
    assert stale_status == 409
    assert stale["error"]["code"] == "stale_revision"
    assert stale["revision"] == 1
    assert stale["events"] == []
    assert stale["snapshot"] == accepted["snapshot"]
    assert resumed["snapshot"] == accepted["snapshot"]


def test_future_revision_illegal_phase_and_bad_card_have_contract_errors():
    app, _ = make_app()
    created = create_game(app)
    game_id = created["snapshot"]["game_id"]
    path = f"/api/games/{game_id}/actions"

    future_status, future = request(
        app,
        "POST",
        path,
        {"revision": 9, "type": "play_card", "card_index": 0},
    )
    illegal_status, illegal = request(
        app,
        "POST",
        path,
        {"revision": 0, "type": "post_move", "choice": "P"},
    )
    bad_status, bad = request(
        app,
        "POST",
        path,
        {"revision": 0, "type": "play_card", "card_index": 999},
    )

    assert future_status == 400
    assert future["error"]["code"] == "invalid_action"
    assert illegal_status == 422
    assert illegal["error"]["code"] == "illegal_action"
    assert bad_status == 400
    assert bad["error"]["code"] == "invalid_action"


def test_malformed_actions_are_400_not_fastapi_default_422():
    app, _ = make_app()
    created = create_game(app)
    game_id = created["snapshot"]["game_id"]

    status, payload = request(
        app,
        "POST",
        f"/api/games/{game_id}/actions",
        {"revision": 0, "type": "play_card"},
    )

    assert status == 400
    assert payload["error"]["code"] == "invalid_action"
    assert payload["error"]["revision"] == 0


def test_live_replay_is_404_and_restart_uses_new_identity_and_seed():
    app, store = make_app()
    setup = {**SETUP, "seed": None}
    created = create_game(app, setup)
    old_id = created["snapshot"]["game_id"]

    replay_status, replay = request(app, "GET", f"/api/games/{old_id}/replay")
    restart_status, restarted = request(
        app, "POST", f"/api/games/{old_id}/restart"
    )
    old_status, _ = request(app, "GET", f"/api/games/{old_id}")

    assert replay_status == 404
    assert replay["error"]["code"] == "game_not_found"
    assert "seed" not in json.dumps(replay)
    assert restart_status == 200
    assert restarted["revision"] == 0
    assert restarted["snapshot"]["game_id"] != old_id
    assert store.get(old_id).seed == 1001
    assert store.get(restarted["snapshot"]["game_id"]).seed == 1002
    assert old_status == 200


def test_completed_replay_returns_seed_and_full_event_log():
    app, store = make_app()
    created = create_game(app)
    game_id = created["snapshot"]["game_id"]
    session = store.get(game_id)
    session.game.ai_vs_ai = True
    session.game.phase = GamePhase.AI_PLAYING_CARD
    events = session.game.pump()
    session.event_log.extend(events)
    store.save(session)

    status, replay = request(app, "GET", f"/api/games/{game_id}/replay")

    assert status == 200
    assert replay["seed"] == 42
    assert replay["events"][0]["type"] == "quarter_started"
    assert replay["events"][-1]["type"] == "game_ended"
    assert [event["seq"] for event in replay["events"]] == list(
        range(len(replay["events"]))
    )


def test_unknown_game_and_advance_route_are_404():
    app, _ = make_app()

    status, payload = request(app, "GET", "/api/games/missing")
    advance_status, _ = request(app, "POST", "/api/games/missing/advance", {})

    assert status == 404
    assert payload["error"]["code"] == "game_not_found"
    assert advance_status == 404
