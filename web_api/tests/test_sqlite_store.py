import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from web_api.app import create_app
from web_api.store import SESSION_TTL_DAYS, SQLiteSessionStore
from web_api.tests.test_api import SETUP, create_game, request


def action_from(snapshot):
    action = next(item for item in snapshot["legal_actions"] if item["enabled"])
    payload = {"revision": snapshot["revision"], "type": action["type"]}
    if "card_index" in action:
        payload["card_index"] = action["card_index"]
    if "choice" in action:
        payload["choice"] = action["choice"]
    return payload


def test_session_survives_store_close_and_process_style_reopen(tmp_path):
    database = tmp_path / "sessions.sqlite3"
    first_store = SQLiteSessionStore(database)
    first_app = create_app(
        store=first_store,
        id_factory=lambda: "persistent-game",
    )
    created = create_game(first_app)
    game_id = created["snapshot"]["game_id"]

    action = action_from(created["snapshot"])
    action_status, _ = request(
        first_app,
        "POST",
        f"/api/games/{game_id}/actions",
        action,
    )
    before_status, before = request(
        first_app, "GET", f"/api/games/{game_id}"
    )
    first_store.close()

    second_store = SQLiteSessionStore(database)
    second_app = create_app(store=second_store)
    after_status, after = request(
        second_app, "GET", f"/api/games/{game_id}"
    )

    assert action_status == 200
    assert before_status == 200
    assert after_status == 200
    assert after == before

    continued_action = action_from(after["snapshot"])
    continued_status, continued = request(
        second_app,
        "POST",
        f"/api/games/{game_id}/actions",
        continued_action,
    )
    assert continued_status == 200
    assert continued["revision"] == after["revision"] + 1
    second_store.close()


def test_sqlite_row_contains_required_internal_state_and_timestamps(tmp_path):
    database = tmp_path / "sessions.sqlite3"
    store = SQLiteSessionStore(database)
    app = create_app(store=store, id_factory=lambda: "row-shape")

    create_game(app, SETUP)
    store.close()

    connection = sqlite3.connect(database)
    row = connection.execute(
        """
        SELECT game_id, seed, revision, engine_state, event_log,
               created_at, updated_at
        FROM sessions
        """
    ).fetchone()
    connection.close()

    assert row[0] == "row-shape"
    assert row[1] == "42"
    assert row[2] == 0
    assert len(row[3]) > 100
    assert len(row[4]) > 20
    assert row[5]
    assert row[6]


def test_expired_session_is_swept_while_recent_session_survives(tmp_path):
    now = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)
    database = tmp_path / "sessions.sqlite3"
    ids = iter(["expired-game", "recent-game"])
    store = SQLiteSessionStore(database, clock=lambda: now)
    app = create_app(store=store, id_factory=lambda: next(ids))

    expired = create_game(app)["snapshot"]["game_id"]
    recent = create_game(app)["snapshot"]["game_id"]
    stale_timestamp = (
        now - timedelta(days=SESSION_TTL_DAYS, seconds=1)
    ).isoformat()
    connection = sqlite3.connect(database)
    connection.execute(
        "UPDATE sessions SET updated_at = ? WHERE game_id = ?",
        (stale_timestamp, expired),
    )
    connection.commit()
    connection.close()

    removed = store.cleanup_expired(now=now)
    expired_status, expired_payload = request(
        app, "GET", f"/api/games/{expired}"
    )
    recent_status, recent_payload = request(
        app, "GET", f"/api/games/{recent}"
    )

    assert removed == 1
    assert expired_status == 404
    assert expired_payload["error"]["code"] == "game_not_found"
    assert recent_status == 200
    assert recent_payload["snapshot"]["game_id"] == recent
    store.close()


def test_overlapping_actions_across_app_instances_commit_exactly_once(tmp_path):
    database = tmp_path / "sessions.sqlite3"
    first_store = SQLiteSessionStore(database)
    first_app = create_app(
        store=first_store,
        id_factory=lambda: "shared-game",
    )
    created = create_game(first_app)
    second_store = SQLiteSessionStore(database)
    second_app = create_app(store=second_store)
    path = "/api/games/shared-game/actions"
    action = {"revision": 0, "type": "play_card", "card_index": 0}

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(request, first_app, "POST", path, action)
        second_future = pool.submit(request, second_app, "POST", path, action)
        responses = [first_future.result(), second_future.result()]

    statuses = sorted(status for status, _payload in responses)
    winner = next(payload for status, payload in responses if status == 200)
    loser = next(payload for status, payload in responses if status == 409)
    persisted = first_store.get("shared-game")

    assert statuses == [200, 409]
    assert loser["error"]["code"] == "stale_revision"
    assert loser["snapshot"] == winner["snapshot"]
    assert persisted.revision == 1
    assert len(persisted.event_log) == (
        len(created["events"]) + len(winner["events"])
    )

    first_store.close()
    second_store.close()
    reopened = SQLiteSessionStore(database)
    resumed = reopened.get("shared-game")
    assert resumed.revision == 1
    assert len(resumed.event_log) == len(persisted.event_log)
    reopened.close()
