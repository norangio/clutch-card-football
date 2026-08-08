import json

from web_api.generate_fixtures import generate


DECISION_PHASES = {
    "WAITING_OFFENSE_CARD",
    "WAITING_DEFENSE_CARD",
    "WAITING_POST_MOVE",
    "WAITING_EXTRA_POINT_CHOICE",
    "GAME_OVER",
}


def test_generated_fixture_is_deterministic_and_contract_shaped():
    responses = generate(42)

    assert responses == generate(42)
    assert responses[0]["revision"] == 0
    assert responses[-1]["snapshot"]["phase"] == "GAME_OVER"
    assert len(responses) < 100

    for revision, response in enumerate(responses):
        assert set(response) == {"revision", "snapshot", "events"}
        assert response["revision"] == revision
        assert response["snapshot"]["revision"] == revision
        assert response["snapshot"]["phase"] in DECISION_PHASES
        assert response["snapshot"]["viewer_seat"] == "home"
        assert "hand" in response["snapshot"]["home"]
        assert "hand" not in response["snapshot"]["away"]
        assert [event["seq"] for event in response["events"]] == list(
            range(len(response["events"]))
        )
        for event in response["events"]:
            if event["type"] == "card_played" and event["seat"] == "away":
                assert event["card"] is None

        if response["snapshot"]["result"] is None:
            assert "seed" not in response["snapshot"]
        else:
            assert response["snapshot"]["seed"] == 42

    # Ensure the dump itself is ordinary JSON, with no Python-only values.
    assert json.loads(json.dumps(responses)) == responses
