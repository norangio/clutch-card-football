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


def test_restart_preserves_ai_vs_ai_mode_with_new_seed_and_identity():
    setup = deepcopy(SETUP)
    setup["ai_vs_ai"] = True
    ids = iter(["first-ai-game", "second-ai-game"])
    app = create_app(
        store=MemorySessionStore(),
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
