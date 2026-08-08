from copy import deepcopy

import pytest

from web_api.app import create_app
from web_api.store import MemorySessionStore
from web_api.tests.test_api import SETUP, request


def test_ai_vs_ai_create_completes_full_game_without_actions():
    setup = deepcopy(SETUP)
    setup["ai_vs_ai"] = True
    store = MemorySessionStore()
    app = create_app(
        store=store,
        seed_factory=lambda: 1001,
        id_factory=lambda: "ai-game",
    )

    status, created = request(app, "POST", "/api/games", setup)
    resume_status, resumed = request(app, "GET", "/api/games/ai-game")
    replay_status, replay = request(app, "GET", "/api/games/ai-game/replay")

    assert status == 200
    assert created["revision"] == 0
    assert created["snapshot"]["phase"] == "GAME_OVER"
    assert created["snapshot"]["required_action"] == "none"
    assert created["snapshot"]["result"] is not None
    assert created["snapshot"]["seed"] == 42
    assert len(created["events"]) > 200
    assert created["events"][0]["type"] == "quarter_started"
    assert created["events"][-1]["type"] == "game_ended"
    assert [event["seq"] for event in created["events"]] == list(
        range(len(created["events"]))
    )
    assert store.get("ai-game").revision == 0
    assert resume_status == 200
    assert resumed["events"] == []
    assert resumed["snapshot"] == created["snapshot"]
    assert replay_status == 200
    assert replay["seed"] == 42
    assert replay["events"] == created["events"]


def test_restart_preserves_full_setup_with_new_seed_and_identity():
    setup = {
        "home": {
            "name": "Black Knights",
            "rating": 12,
            "kick_rating": 3,
            "color": "black",
            "clutch": 3,
        },
        "away": {
            "name": "Red Raiders",
            "rating": 1,
            "kick_rating": 1,
            "clutch": 0,
        },
        "difficulty": "easy",
        "ai_vs_ai": True,
        "seed": 42,
    }
    ids = iter(["first-ai-game", "second-ai-game"])
    store = MemorySessionStore()
    app = create_app(
        store=store,
        seed_factory=lambda: 1001,
        id_factory=lambda: next(ids),
    )
    _, created = request(app, "POST", "/api/games", setup)

    status, restarted = request(
        app, "POST", "/api/games/first-ai-game/restart"
    )

    assert status == 200
    assert created["snapshot"]["game_id"] == "first-ai-game"
    assert restarted["snapshot"]["game_id"] == "second-ai-game"
    assert restarted["revision"] == 0
    assert restarted["snapshot"]["phase"] == "GAME_OVER"
    assert restarted["snapshot"]["seed"] == 1001
    assert restarted["events"][-1]["type"] == "game_ended"

    old_session = store.get("first-ai-game")
    new_session = store.get("second-ai-game")
    expected_setup = deepcopy(setup)
    expected_setup.pop("seed")
    assert old_session.setup == new_session.setup == expected_setup
    assert old_session.seed == 42
    assert new_session.seed == 1001
    assert new_session.revision == 0
    assert new_session.game.difficulty.value == "easy"
    assert new_session.game.ai_vs_ai is True
    assert (
        new_session.game.human.name,
        new_session.game.human.rating,
        new_session.game.human.kick_rating,
        new_session.game.human.color.value,
    ) == ("Black Knights", 12, 3, "black")
    assert (
        new_session.game.ai.name,
        new_session.game.ai.rating,
        new_session.game.ai.kick_rating,
        new_session.game.ai.color.value,
    ) == ("Red Raiders", 1, 1, "red")


def test_ai_vs_ai_defaults_false_for_existing_create_payloads():
    app = create_app(
        store=MemorySessionStore(),
        id_factory=lambda: "human-game",
    )

    status, created = request(app, "POST", "/api/games", SETUP)

    assert status == 200
    assert created["snapshot"]["phase"] == "WAITING_OFFENSE_CARD"
    assert created["snapshot"]["result"] is None


@pytest.mark.parametrize("value", [1, 0, "true", None])
def test_ai_vs_ai_requires_a_json_boolean(value):
    setup = deepcopy(SETUP)
    setup["ai_vs_ai"] = value
    app = create_app(store=MemorySessionStore())

    status, payload = request(app, "POST", "/api/games", setup)

    assert status == 400
    assert payload["error"]["code"] == "invalid_action"
