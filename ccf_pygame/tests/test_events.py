import json

import pytest

from ccf.events import (
    ALL_EVENT_TYPES,
    BallMovedEvent,
    CardPlayedEvent,
    CardsRevealedEvent,
    ClutchUsedEvent,
    ExtraPointResolvedEvent,
    FieldGoalResolvedEvent,
    GameEndedEvent,
    JokerResolvedEvent,
    MojoChangedEvent,
    MojoConvertedToClutchEvent,
    PossessionChangedEvent,
    PuntResolvedEvent,
    QuarterEndedEvent,
    QuarterStartedEvent,
    SafetyScoredEvent,
    TouchdownScoredEvent,
    WarCardRevealedEvent,
    WarStartedEvent,
)
from ccf.models import Card


ACE = Card("A", "H")
KING = Card("K", "S")


@pytest.fixture(params=[
    QuarterStartedEvent(1, "home", 7, "3"),
    CardPlayedEvent("home", "offense", ACE, 6),
    CardsRevealedEvent(ACE, KING, 14, 13, "offense"),
    WarStartedEvent(10),
    WarCardRevealedEvent(ACE, True, "advance"),
    JokerResolvedEvent("defense", 12, "turnover_z3"),
    BallMovedEvent("home", "3", "Z3", 1, "drive_chart", False, False),
    MojoChangedEvent("away", 1, 2, "won_card_battle"),
    MojoConvertedToClutchEvent("home", 2, "pre_play"),
    ClutchUsedEvent("home", 1, ACE),
    PossessionChangedEvent("home", "away", "3", "punt"),
    PuntResolvedEvent("home", "punt", 3, 5, "Z2", "2", False),
    FieldGoalResolvedEvent("away", True, 6, 10, 8, "Z1", 3, 10),
    TouchdownScoredEvent("home", 6, 13, "color_bonus"),
    SafetyScoredEvent("away", 2, 9),
    ExtraPointResolvedEvent("home", "K", True, None, 1, 14),
    QuarterEndedEvent(2, 14, 9),
    GameEndedEvent("home", 21, 16, False),
])
def event(request):
    return request.param


def test_all_events_are_json_round_trippable(event):
    payload = event.to_dict(seq=3)

    assert json.loads(json.dumps(payload)) == payload
    assert payload["seq"] == 3
    assert payload["type"] == event.type


def test_catalog_has_exactly_the_18_contract_types(event):
    assert len(ALL_EVENT_TYPES) == 18
    assert len(set(ALL_EVENT_TYPES)) == 18
    assert event.type in ALL_EVENT_TYPES


def test_cards_use_the_contract_shape():
    payload = CardPlayedEvent("home", "offense", ACE, 6).to_dict(0)

    assert payload["card"] == {
        "id": "AH",
        "value": "A",
        "suit": "H",
        "color": "red",
        "display": "A♥",
    }


def test_hidden_card_serializes_as_null():
    payload = CardPlayedEvent("away", "offense", None, 6).to_dict(0)

    assert payload["card"] is None


@pytest.mark.parametrize(
    "event",
    [
        PuntResolvedEvent("home", "short_punt", 2, None, "Z2", "3", False),
        ExtraPointResolvedEvent("home", "K", True, None, 1, 7),
    ],
)
def test_unavailable_rolls_are_null(event):
    assert event.to_dict(0)["roll"] is None


def test_contract_field_aliases_use_from_and_to():
    payload = BallMovedEvent(
        "home", "3", "Z3", 1, "drive_chart", False, False
    ).to_dict(0)

    assert payload["from"] == "3"
    assert payload["to"] == "Z3"
    assert "from_ball" not in payload
    assert "to_ball" not in payload


def test_event_sequence_rejects_negative_values():
    with pytest.raises(ValueError, match="non-negative"):
        WarStartedEvent(9).to_dict(-1)
