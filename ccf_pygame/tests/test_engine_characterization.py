"""Characterize pre-refactor engine behavior, including known defects.

These tests intentionally pin what the broadcast build does today. They are a
safety net for the presentation-independent engine work, not endorsements of
every behavior asserted here.
"""

from collections import deque
from unittest.mock import patch

from ccf.ai import Difficulty
from ccf.field import move
from ccf.models import Card, Color
from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase


def make_game(*, human_rating=6, human_clutch=3):
    game = GameStateMachine()
    game.provide_setup(
        "Human",
        human_rating,
        2,
        Color.RED,
        human_clutch,
        "Robot",
        6,
        2,
        3,
        difficulty=Difficulty.MEDIUM,
    )
    return game


def resolve_normal_play(game, *, position, offense_card, defense_card):
    game.pos = position
    game._off_card = offense_card
    game._def_card = defense_card
    game._resolve_play()


def test_orange_bonus_landing_on_z1_scores_automatic_touchdown():
    game = make_game(human_rating=5)

    resolve_normal_play(
        game,
        position="2",
        offense_card=Card("A", "H"),
        defense_card=Card("2", "S"),
    )

    assert game.phase == GamePhase.SHOWING_MOVEMENT
    assert game._movement == 4
    assert game._new_pos == "Z1"
    assert game._is_td is True
    assert game.pos == "Z1"

    game._auto_transition()

    assert game.human.score == 6
    assert game.drain_events()[-1].to_dict(0)["cause"] == "color_bonus"


def test_green_bonus_landing_on_z1_scores_automatic_touchdown():
    game = make_game(human_rating=7)

    resolve_normal_play(
        game,
        position="1",
        offense_card=Card("A", "H"),
        defense_card=Card("2", "S"),
    )

    assert game.phase == GamePhase.SHOWING_MOVEMENT
    assert game._movement == 5
    assert game._new_pos == "Z1"
    assert game._is_td is True
    assert game.pos == "Z1"

    game._auto_transition()

    assert game.human.score == 6
    assert game.drain_events()[-1].to_dict(0)["cause"] == "color_bonus"


def test_orange_bonus_requires_a_team_color_match():
    game = make_game(human_rating=5)

    resolve_normal_play(
        game,
        position="2",
        offense_card=Card("A", "S"),
        defense_card=Card("2", "H"),
    )

    assert game._new_pos == "Z1"
    assert game._is_td is False


def test_orange_move_past_z1_remains_a_normal_drive_touchdown():
    game = make_game(human_rating=9)

    resolve_normal_play(
        game,
        position="2",
        offense_card=Card("A", "H"),
        defense_card=Card("2", "S"),
    )

    assert game._movement == 5
    assert game._new_pos == "1"
    assert game._is_td is True

    game._auto_transition()

    assert game.drain_events()[-1].to_dict(0)["cause"] == "drive"


def test_internal_snapshot_contains_both_complete_hands():
    game = make_game()

    snapshot = game.snapshot()

    assert snapshot.human.hand is game.human.hand
    assert snapshot.ai.hand is game.ai.hand
    assert len(snapshot.human.hand) == 7
    assert len(snapshot.ai.hand) == 7


def test_internal_snapshot_contains_unrevealed_ai_offense_card():
    game = make_game()
    game.offense, game.defense = game.ai, game.human
    game.ai.hand = [Card("A", "S")]

    game._ai_play_offense()
    snapshot = game.snapshot()

    assert game.phase == GamePhase.WAITING_DEFENSE_CARD
    assert snapshot.off_card == Card("A", "S")


def test_punt_from_z1_moves_back_three_segments_without_safety():
    game = make_game()
    game.pos = "Z1"

    with patch("ccf.state_machine.punt_distance", return_value=(3, 1)):
        game._do_punt()

    assert game.phase == GamePhase.SHOWING_PUNT
    assert game.pos == "3"
    assert game._punt_dist == 3
    assert game._punt_roll == 1


def test_punt_is_clamped_at_segment_one():
    game = make_game()
    game.pos = "1"

    with patch("ccf.state_machine.punt_distance", return_value=(5, 3)):
        game._do_punt()

    assert game.phase == GamePhase.SHOWING_PUNT
    assert game.pos == "1"


def test_war_relocation_from_z2_does_not_decrement_segment_stat():
    game = make_game()
    game.pos = "Z2"
    game.deck = deque([Card("4", "H")])
    game._off_card = Card("8", "S")
    game._def_card = Card("8", "D")

    game._handle_war()
    game._auto_transition()

    assert game.pos == "Z3"
    assert game.human.segments == 0
    assert game.phase == GamePhase.WAITING_POST_MOVE
    ball_event = game.drain_events()[-1].to_dict(0)
    assert ball_event["type"] == "ball_moved"
    assert ball_event["from"] == "Z2"
    assert ball_event["to"] == "Z3"
    assert ball_event["segments"] == 0


def test_empty_deck_war_falls_back_to_black_two_and_turnover():
    game = make_game()
    game.deck.clear()
    game._off_card = Card("8", "H")
    game._def_card = Card("8", "S")

    game._handle_war()

    assert game._war_card == Card("2", "S")
    assert game.phase == GamePhase.SHOWING_WAR
    assert "TURNOVER" in game._message


def test_empty_deck_clutch_falls_back_to_ace_of_hearts():
    game = make_game(human_rating=6, human_clutch=1)
    game.deck.clear()
    game.pos = "1"

    game._do_clutch()

    assert game._clutch_card == Card("A", "H")
    assert game.phase == GamePhase.SHOWING_CLUTCH

    game._auto_transition()

    assert game.pos == move("1", 4)[0]
    assert game.phase == GamePhase.WAITING_POST_MOVE
