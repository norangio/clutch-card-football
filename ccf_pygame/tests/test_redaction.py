"""Contract-v1 snapshot serialization and hidden-information tests."""

import json

import pytest

from ccf.ai import Difficulty
from ccf.models import Card, Color
from ccf.serializers import (
    PLAY_CARDS_REVEALED_PHASES,
    serialize_card,
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
