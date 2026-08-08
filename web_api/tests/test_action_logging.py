import json
import logging

from web_api.app import create_app
from web_api.store import MemorySessionStore
from web_api.tests.test_api import SETUP, create_game, request


EXPECTED_KEYS = {
    "action_type",
    "duration_ms",
    "event_count",
    "game_id",
    "outcome",
    "phase_after",
    "phase_before",
    "revision",
}


def test_action_logs_are_structured_and_allowlist_only(caplog):
    app = create_app(
        store=MemorySessionStore(),
        id_factory=lambda: "logged-game",
    )
    created = create_game(app, SETUP)
    action = {"revision": 0, "type": "play_card", "card_index": 0}

    with caplog.at_level(logging.INFO, logger="ccf.api.actions"):
        accepted_status, accepted = request(
            app,
            "POST",
            "/api/games/logged-game/actions",
            action,
        )
        stale_status, _ = request(
            app,
            "POST",
            "/api/games/logged-game/actions",
            action,
        )

    records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "ccf.api.actions"
    ]
    assert accepted_status == 200
    assert stale_status == 409
    assert len(records) == 2

    accepted_log, stale_log = records
    assert set(accepted_log) == EXPECTED_KEYS
    assert accepted_log == {
        **accepted_log,
        "action_type": "play_card",
        "event_count": len(accepted["events"]),
        "game_id": "logged-game",
        "outcome": "accepted",
        "phase_before": created["snapshot"]["phase"],
        "phase_after": accepted["snapshot"]["phase"],
        "revision": 0,
    }
    assert isinstance(accepted_log["duration_ms"], (int, float))
    assert accepted_log["duration_ms"] >= 0
    assert set(stale_log) == EXPECTED_KEYS
    assert stale_log["outcome"] == "stale_revision"
    assert stale_log["event_count"] == 0

    # Exact-key validation is the primary leak guard. These string assertions
    # additionally catch accidental embedding of common secret-bearing fields.
    wire = "\n".join(record.getMessage() for record in caplog.records)
    for forbidden in (
        "card_index",
        '"choice"',
        '"hand"',
        '"snapshot"',
        '"events"',
        '"seed"',
        "Wolverines",
        "Buckeyes",
    ):
        assert forbidden not in wire
