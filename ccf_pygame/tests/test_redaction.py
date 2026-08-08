"""Contract snapshot serialization and hidden-information tests."""

from collections import deque
from copy import deepcopy
from dataclasses import fields, replace
import json

import pytest

from ccf.ai import Difficulty
from ccf.events import CardPlayedEvent, CardsRevealedEvent
from ccf.models import Card, Color
from ccf.serializers import (
    PLAY_CARDS_REVEALED_PHASES,
    serialize_card,
    serialize_events,
    serialize_legal_actions,
    serialize_play_cards,
    serialize_snapshot,
)
from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase


def make_game(seed=42):
    game = GameStateMachine(seed=seed)
    game.provide_setup(
        "Home",
        7,
        2,
        Color.RED,
        3,
        "Away",
        6,
        2,
        3,
        difficulty=Difficulty.MEDIUM,
    )
    game._start_turn()
    return game


def set_ai_offense(game):
    game.offense, game.defense = game.ai, game.human


def serialized(game, viewer="home", revision=0):
    return serialize_snapshot(
        game,
        viewer,
        game_id="game-1",
        revision=revision,
    )


def test_card_shape_matches_contract():
    assert serialize_card(Card("A", "H")) == {
        "id": "AH",
        "value": "A",
        "suit": "H",
        "color": "red",
        "display": "A♥",
    }
    assert serialize_card(Card("Joker")) == {
        "id": "JOKER",
        "value": "Joker",
        "suit": None,
        "color": None,
        "display": "JOKER",
    }


def test_only_viewer_seat_contains_hand():
    game = make_game()

    home_view = serialized(game, "home")
    away_view = serialized(game, "away")

    assert len(home_view["home"]["hand"]) == 7
    assert "hand" not in home_view["away"]
    assert len(away_view["away"]["hand"]) == 7
    assert "hand" not in away_view["home"]
    assert home_view["away"]["hand_count"] == 7
    assert away_view["home"]["hand_count"] == 7


def test_waiting_defense_payload_contains_no_ai_card_or_hand_anywhere():
    game = make_game()
    set_ai_offense(game)
    game.phase = GamePhase.WAITING_DEFENSE_CARD
    game.ai.hand = [Card("Q", "S")]
    game.human.hand = [Card("2", "H")]
    game._off_card = Card("K", "S")
    game._def_card = None
    game.log.clear()
    game._message = "AI plays card ..."

    payload = serialized(game, "home")
    wire = json.dumps(payload, sort_keys=True)

    assert payload["play_cards"]["offense"] is None
    assert payload["home"]["hand"][0]["id"] == "2H"
    assert "hand" not in payload["away"]
    assert "KS" not in wire
    assert "QS" not in wire
    assert "K♠" not in wire
    assert "Q♠" not in wire


def test_waiting_defense_event_json_contains_no_opponent_card_anywhere():
    game = make_game()
    game.drain_events()
    set_ai_offense(game)
    game.ai.hand = [Card("K", "S")]
    game.phase = GamePhase.AI_PLAYING_CARD

    game._ai_play_offense()
    events = game.drain_events()
    home_wire = json.dumps(
        serialize_events(events, "home"), sort_keys=True, ensure_ascii=False
    )
    away_wire = json.dumps(
        serialize_events(events, "away"), sort_keys=True, ensure_ascii=False
    )

    assert game.phase == GamePhase.WAITING_DEFENSE_CARD
    assert events[0].card == Card("K", "S")
    assert "KS" not in home_wire
    assert "K♠" not in home_wire
    assert "KS" in away_wire
    assert "K♠" in away_wire


def test_card_played_stays_hidden_until_public_reveal_event():
    events = [
        CardPlayedEvent("home", "offense", Card("A", "H"), 6),
        CardPlayedEvent("away", "defense", Card("K", "S"), 6),
        CardsRevealedEvent(
            Card("A", "H"), Card("K", "S"), 14, 13, "offense"
        ),
    ]

    payload = serialize_events(events, "home")
    wire = json.dumps(payload, sort_keys=True)

    assert payload[0]["card"]["id"] == "AH"
    assert payload[1]["card"] is None
    assert payload[2]["defense_card"]["id"] == "KS"
    assert wire.count('"id": "KS"') == 1
    assert [event["seq"] for event in payload] == [0, 1, 2]


@pytest.mark.parametrize(
    "phase",
    [
        GamePhase.WAITING_OFFENSE_CARD,
        GamePhase.WAITING_DEFENSE_CARD,
        GamePhase.WAITING_POST_MOVE,
        GamePhase.WAITING_EXTRA_POINT_CHOICE,
        GamePhase.GAME_OVER,
    ],
)
def test_opponent_hand_never_appears_in_any_public_snapshot(phase):
    game = make_game()
    game.human.hand = [Card("2", "H")]
    game.ai.hand = [Card("Q", "S")]
    game.phase = phase
    if phase == GamePhase.WAITING_DEFENSE_CARD:
        set_ai_offense(game)
        game._off_card = Card("K", "S")
    elif phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        game._scorer = game.human
    game.log.clear()
    game._message = ""

    wire = json.dumps(serialized(game, "home"), sort_keys=True)

    assert "QS" not in wire
    assert "Q♠" not in wire


def test_owner_can_see_own_played_card_while_opponent_cannot():
    game = make_game()
    set_ai_offense(game)
    game.phase = GamePhase.WAITING_DEFENSE_CARD
    game._off_card = Card("K", "S")

    assert serialize_play_cards(game, "home")["offense"] is None
    assert serialize_play_cards(game, "away")["offense"]["id"] == "KS"


@pytest.mark.parametrize("phase", list(GamePhase))
def test_opponent_played_card_visibility_is_phase_driven(phase):
    game = make_game()
    set_ai_offense(game)
    game.phase = phase
    game._off_card = Card("K", "S")
    game._def_card = Card("2", "H")

    cards = serialize_play_cards(game, "home")

    if phase in PLAY_CARDS_REVEALED_PHASES:
        assert cards["offense"]["id"] == "KS"
        assert cards["defense"]["id"] == "2H"
    elif phase == GamePhase.WAITING_DEFENSE_CARD:
        assert cards["offense"] is None
        assert cards["defense"]["id"] == "2H"
    else:
        assert cards["offense"] is None
        assert cards["defense"] is None


def test_war_card_is_hidden_until_war_reveal():
    game = make_game()
    game._war_card = Card("4", "D")
    game.phase = GamePhase.SHOWING_CARD_BATTLE
    assert serialize_play_cards(game, "home")["war"] is None

    game.phase = GamePhase.SHOWING_WAR
    assert serialize_play_cards(game, "home")["war"]["id"] == "4D"
    assert serialize_play_cards(game, "away")["war"]["id"] == "4D"


def test_clutch_card_is_revealed_to_both_seats_immediately():
    game = make_game()
    game._clutch_card = Card("9", "C")
    game.phase = GamePhase.SHOWING_CLUTCH

    assert serialize_play_cards(game, "home")["clutch"]["id"] == "9C"
    assert serialize_play_cards(game, "away")["clutch"]["id"] == "9C"


def test_live_snapshot_omits_seed_and_completed_snapshot_includes_it():
    game = make_game(seed=1337)

    assert "seed" not in serialized(game)

    game.phase = GamePhase.GAME_OVER
    game.human.score = 21
    game.ai.score = 17
    payload = serialized(game)

    assert payload["seed"] == 1337
    assert payload["result"] == {
        "winner": "home",
        "home_score": 21,
        "away_score": 17,
        "is_tie": False,
    }


def test_tied_game_has_null_winner():
    game = make_game(seed=8)
    game.phase = GamePhase.GAME_OVER
    game.human.score = game.ai.score = 14

    assert serialized(game)["result"] == {
        "winner": None,
        "home_score": 14,
        "away_score": 14,
        "is_tie": True,
    }


def test_post_move_legal_actions_include_disabled_reasons():
    game = make_game()
    game.phase = GamePhase.WAITING_POST_MOVE
    game.pos = "1"
    game.offense = game.human
    game.human.clutch = 0

    actions = serialize_legal_actions(game, "home")

    assert actions == [
        {"type": "post_move", "choice": "P", "enabled": True},
        {
            "type": "post_move",
            "choice": "F",
            "enabled": False,
            "disabled_reason": "not_in_field_goal_range",
        },
        {
            "type": "post_move",
            "choice": "C",
            "enabled": False,
            "disabled_reason": "no_clutch_remaining",
        },
        {
            "type": "post_move",
            "choice": "S",
            "enabled": False,
            "disabled_reason": "not_in_field_goal_range",
        },
    ]


def test_nonacting_viewer_gets_no_legal_actions():
    game = make_game()
    game.phase = GamePhase.WAITING_OFFENSE_CARD
    game.offense = game.human

    assert serialize_legal_actions(game, "away") == []


def test_transient_phase_cannot_cross_snapshot_boundary():
    game = make_game()
    game.phase = GamePhase.SHOWING_CARD_BATTLE

    with pytest.raises(ValueError, match="transient phase"):
        serialized(game)


def test_unknown_viewer_is_rejected():
    game = make_game()

    with pytest.raises(ValueError, match="unknown viewer seat"):
        serialized(game, "spectator")


def _card_key(card):
    payload = serialize_card(card)
    return tuple(payload[key] for key in ("id", "value", "suit", "color", "display"))


def _wire_card_keys(value):
    """Recursively find card-shaped objects without assuming payload paths."""
    keys = set()
    if isinstance(value, dict):
        card_fields = {"id", "value", "suit", "color", "display"}
        if card_fields <= value.keys():
            keys.add(tuple(value[key] for key in ("id", "value", "suit", "color", "display")))
        for nested in value.values():
            keys.update(_wire_card_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_wire_card_keys(nested))
    return keys


def _event_public_cards(events, viewer_seat):
    public = []
    for event in events:
        for field in fields(event):
            value = getattr(event, field.name)
            if not isinstance(value, Card):
                continue
            if isinstance(event, CardPlayedEvent) and event.seat != viewer_seat:
                continue
            public.append(value)
    return public


def _snapshot_public_cards(game, viewer_seat):
    viewer = game.human if viewer_seat == "home" else game.ai
    public = list(viewer.hand)

    # At the only partially revealed decision boundary, each played card is
    # visible solely to its owner. At later decision boundaries both cards are
    # already revealed. War and clutch draws are public as soon as they exist.
    if game.phase == GamePhase.WAITING_DEFENSE_CARD:
        if game._off_card is not None and (
            (game.offense is game.human) == (viewer_seat == "home")
        ):
            public.append(game._off_card)
        if game._def_card is not None and (
            (game.defense is game.human) == (viewer_seat == "home")
        ):
            public.append(game._def_card)
    elif game.phase in (
        GamePhase.WAITING_POST_MOVE,
        GamePhase.WAITING_EXTRA_POINT_CHOICE,
        GamePhase.GAME_OVER,
    ):
        public.extend(
            card for card in (game._off_card, game._def_card) if card is not None
        )

    public.extend(
        card for card in (game._war_card, game._clutch_card) if card is not None
    )
    return public


def _canary_clone(game, viewer_seat):
    """Replace every ground-truth hidden card with a unique serialization canary."""
    clone = deepcopy(game)
    counter = 0

    def hide(card):
        nonlocal counter
        counter += 1
        marker = f"LEAK_MARKER_{viewer_seat}_{counter}"
        return Card(marker, "X")

    clone.deck = deque(hide(card) for card in clone.deck)
    opponent = clone.ai if viewer_seat == "home" else clone.human
    opponent.hand = [hide(card) for card in opponent.hand]

    if clone.phase == GamePhase.WAITING_DEFENSE_CARD:
        if clone._off_card is not None and (
            (clone.offense is clone.human) != (viewer_seat == "home")
        ):
            clone._off_card = hide(clone._off_card)
        if clone._def_card is not None and (
            (clone.defense is clone.human) != (viewer_seat == "home")
        ):
            clone._def_card = hide(clone._def_card)

    return clone


def _canary_events(events, viewer_seat):
    canary_events = deepcopy(events)
    for index, event in enumerate(canary_events):
        if (
            isinstance(event, CardPlayedEvent)
            and event.seat != viewer_seat
            and event.card is not None
        ):
            canary_events[index] = replace(
                event,
                card=Card(f"LEAK_MARKER_EVENT_{viewer_seat}_{index}", "X"),
            )
    return canary_events


def _assert_ground_truth_redaction(game, events, viewer_seat, revision):
    snapshot = serialize_snapshot(
        game,
        viewer_seat,
        game_id="fuzz-game",
        revision=revision,
    )
    event_payloads = serialize_events(events, viewer_seat)
    payload = {"snapshot": snapshot, "events": event_payloads}

    allowed_cards = _snapshot_public_cards(game, viewer_seat)
    allowed_cards.extend(_event_public_cards(events, viewer_seat))
    allowed_keys = {_card_key(card) for card in allowed_cards}
    unexpected = _wire_card_keys(payload) - allowed_keys
    assert not unexpected, (
        f"{viewer_seat} saw cards outside engine ground truth in "
        f"{game.phase.name}: {unexpected}"
    )

    viewer_key = viewer_seat
    opponent_key = "away" if viewer_seat == "home" else "home"
    viewer_team = game.human if viewer_seat == "home" else game.ai
    assert snapshot[viewer_key]["hand"] == [
        serialize_card(card) for card in viewer_team.hand
    ]
    assert "hand" not in snapshot[opponent_key]
    assert ("seed" in snapshot) == (game.phase == GamePhase.GAME_OVER)

    canary_game = _canary_clone(game, viewer_seat)
    canary_payload = {
        "snapshot": serialize_snapshot(
            canary_game,
            viewer_seat,
            game_id="fuzz-game",
            revision=revision,
        ),
        "events": serialize_events(
            _canary_events(events, viewer_seat), viewer_seat
        ),
    }
    canary_wire = json.dumps(canary_payload, ensure_ascii=False, sort_keys=True)
    assert "LEAK_MARKER" not in canary_wire, (
        f"{viewer_seat} hidden-card canary leaked in {game.phase.name}"
    )


def _take_fuzz_action(game, seed, step):
    if game.phase in (
        GamePhase.WAITING_OFFENSE_CARD,
        GamePhase.WAITING_DEFENSE_CARD,
    ):
        team = (
            game.offense
            if game.phase == GamePhase.WAITING_OFFENSE_CARD
            else game.defense
        )
        game.provide_card((seed + step) % len(team.hand))
    elif game.phase == GamePhase.WAITING_POST_MOVE:
        enabled = {
            action["choice"]
            for action in serialize_legal_actions(game, "home")
            if action["enabled"]
        }
        preference = ("C", "F", "S", "P")
        offset = (seed + step) % len(preference)
        choice = next(
            choice
            for choice in preference[offset:] + preference[:offset]
            if choice in enabled
        )
        game.provide_post_move(choice)
    elif game.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        game.provide_extra_point_choice("K" if (seed + step) % 2 else "2")
    else:
        raise AssertionError(f"unexpected fuzz decision: {game.phase.name}")


def test_seeded_games_never_serialize_a_ground_truth_hidden_card():
    serialized_boundaries = 0
    for seed in range(30):
        game = GameStateMachine(seed=seed)
        game.provide_setup(
            "Home",
            7,
            2,
            Color.RED,
            3,
            "Away",
            6,
            2,
            3,
            difficulty=Difficulty.MEDIUM,
        )
        revision = 0
        events = game.pump()

        while True:
            for viewer_seat in ("home", "away"):
                _assert_ground_truth_redaction(
                    game, events, viewer_seat, revision
                )
                serialized_boundaries += 1
            if game.phase == GamePhase.GAME_OVER:
                break

            _take_fuzz_action(game, seed, revision)
            revision += 1
            events = game.pump()
            assert revision < 100

    assert serialized_boundaries >= 2_000
