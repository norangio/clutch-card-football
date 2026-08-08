from copy import deepcopy

from web_api.app import create_app
from web_api.store import MemorySessionStore
from web_api.tests.test_api import SETUP, request


def first_enabled_action(response):
    legal = next(
        action
        for action in response["snapshot"]["legal_actions"]
        if action["enabled"]
    )
    payload = {"revision": response["revision"], "type": legal["type"]}
    for field in ("card_index", "choice"):
        if field in legal:
            payload[field] = legal[field]
    return payload


def test_seeded_http_game_emits_serialized_safety_and_score():
    setup = deepcopy(SETUP)
    setup["seed"] = 0
    setup["home"]["rating"] = 2
    setup["away"]["rating"] = 2
    app = create_app(
        store=MemorySessionStore(),
        id_factory=lambda: "safety-game",
    )
    status, response = request(app, "POST", "/api/games", setup)
    assert status == 200

    safety_response = None
    for _ in range(100):
        status, response = request(
            app,
            "POST",
            "/api/games/safety-game/actions",
            first_enabled_action(response),
        )
        assert status == 200
        if any(event["type"] == "safety_scored" for event in response["events"]):
            safety_response = response
            break

    assert safety_response is not None
    events = safety_response["events"]
    safety_index = next(
        index for index, event in enumerate(events)
        if event["type"] == "safety_scored"
    )
    movement = events[safety_index - 1]
    safety = events[safety_index]

    assert movement["type"] == "ball_moved"
    assert movement["is_safety"] is True
    assert movement["to"] == "3"
    assert safety == {
        "seq": safety_index,
        "type": "safety_scored",
        "seat": "away",
        "points": 2,
        "score_after": safety_response["snapshot"]["away"]["score"],
    }
    opponent_plays = [
        event for event in events
        if event["type"] == "card_played" and event["seat"] == "away"
    ]
    assert all(event["card"] is None for event in opponent_plays)
