import sqlite3

from web_api.app import create_app
from web_api.store import SQLiteSessionStore
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
