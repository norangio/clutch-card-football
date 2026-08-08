"""Targeted coverage for special-play and scoring branches."""

from collections import deque
from unittest.mock import patch

import pytest

from ccf.ai import Difficulty
from ccf.models import Card, Color
from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase


def make_game(*, clutch=1):
    game = GameStateMachine(seed=123)
    game.provide_setup(
        "Home",
        6,
        2,
        Color.RED,
        clutch,
        "Away",
        6,
        2,
        1,
        difficulty=Difficulty.MEDIUM,
    )
    game.drain_events()
    return game


@pytest.mark.parametrize(
    "played_by,opposing_card,outcome,score_seat,position,offense_seat",
    [
        ("offense", Card("2", "S"), "touchdown", "home", "1", "home"),
        ("offense", Card("7", "S"), "advance_3", None, "Z3", "home"),
        ("offense", Card("Q", "S"), "advance_1", None, "2", "home"),
        ("defense", Card("2", "H"), "touchdown", "away", "1", "home"),
        ("defense", Card("7", "H"), "turnover_z3", None, "Z3", "away"),
        ("defense", Card("Q", "H"), "no_gain", None, "1", "home"),
    ],
)
def test_joker_branches_emit_and_resolve(
    played_by,
    opposing_card,
    outcome,
    score_seat,
    position,
    offense_seat,
):
    game = make_game()
    game.pos = "1"
    if played_by == "offense":
        game._off_card = Card("Joker")
        game._def_card = opposing_card
    else:
        game._off_card = opposing_card
        game._def_card = Card("Joker")

    game._handle_joker()
    event = game.drain_events()[0].to_dict(0)
    game._auto_transition()

    assert event == {
        "seq": 0,
        "type": "joker_resolved",
        "played_by": played_by,
        "opposing_value": {
            "2": 2,
            "7": 7,
            "Q": 12,
        }[opposing_card.value],
        "outcome": outcome,
    }
    assert game.pos == position
    assert game._seat(game.offense) == offense_seat
    if score_seat == "home":
        assert game.human.score == 6
        assert game.drain_events()[-1].to_dict(0)["cause"] == "joker"
    elif score_seat == "away":
        assert game.ai.score == 6
        assert game.drain_events()[-1].to_dict(0)["cause"] == "defensive_joker"


@pytest.mark.parametrize(
    "war_card,outcome,position,offense_seat",
    [
        (Card("4", "H"), "advance", "Z3", "home"),
        (Card("4", "S"), "turnover", "3", "away"),
    ],
)
def test_war_both_outcomes(war_card, outcome, position, offense_seat):
    game = make_game()
    game.pos = "2"
    game.deck = deque([war_card])
    game._off_card = Card("8", "H")
    game._def_card = Card("8", "S")

    game._handle_war()
    reveal = game.drain_events()[-1].to_dict(0)
    game._auto_transition()

    assert reveal["outcome"] == outcome
    assert reveal["matches_offense_color"] is (outcome == "advance")
    assert game.pos == position
    assert game._seat(game.offense) == offense_seat


@pytest.mark.parametrize("position", ["Z1", "Z2", "Z3"])
@pytest.mark.parametrize("success", [True, False])
def test_field_goal_made_and_missed_from_every_zone(position, success):
    game = make_game()
    game.pos = position
    target = {"Z1": 4, "Z2": 5, "Z3": 7}[position]
    roll = 6 if success else 1
    total = target if success else target - 1

    with patch(
        "ccf.state_machine.field_goal_attempt",
        return_value=(success, roll, total, target),
    ):
        game._do_field_goal()

    resolved = game.drain_events()[0].to_dict(0)
    game._auto_transition()
    transition_events = [event.to_dict(0) for event in game.drain_events()]

    assert resolved["from"] == position
    assert resolved["success"] is success
    assert resolved["points"] == (3 if success else 0)
    assert resolved["score_after"] == (3 if success else 0)
    assert game.pos == (
        "1" if success else {"Z1": "1", "Z2": "2", "Z3": "3"}[position]
    )
    assert game._seat(game.offense) == "away"
    assert transition_events[-1]["type"] == "possession_changed"
    assert transition_events[-1]["reason"] == (
        "field_goal_made" if success else "field_goal_missed"
    )


def test_clutch_joker_spends_token_and_scores_with_clutch_cause():
    game = make_game(clutch=1)
    game.phase = GamePhase.WAITING_POST_MOVE
    game.deck = deque([Card("Joker")])

    game._execute_post_move("C")
    used = game.drain_events()[-1].to_dict(0)
    game._auto_transition()
    scored = game.drain_events()[-1].to_dict(0)

    assert used["type"] == "clutch_used"
    assert used["clutch_after"] == 0
    assert used["card"]["id"] == "JOKER"
    assert game.human.clutch_used is True
    assert game.human.score == 6
    assert scored["cause"] == "clutch"


def test_mojo_accumulates_then_converts_to_clutch_in_event_order():
    game = make_game(clutch=0)
    game.human.mojo = 1
    game._off_card = Card("A", "H")
    game._def_card = Card("2", "S")

    game._resolve_play()
    events = [event.to_dict(index) for index, event in enumerate(game.drain_events())]

    assert game.human.mojo == 0
    assert game.human.clutch == 1
    assert [event["type"] for event in events[:2]] == [
        "mojo_changed",
        "mojo_converted_to_clutch",
    ]
    assert events[0]["from"] == 1
    assert events[0]["to"] == 2
    assert events[1]["trigger"] == "pre_play"


def test_halftime_resets_hands_and_hands_possession_to_away():
    game = make_game()
    game.human.hand = [Card("2", "H")]
    game.ai.hand = [Card("3", "S")]
    game.offense, game.defense = game.human, game.ai
    game.quarter = 3
    game.pos = "Z2"

    game._start_quarter()
    events = [event.to_dict(index) for index, event in enumerate(game.drain_events())]

    assert len(game.human.hand) == 7
    assert len(game.ai.hand) == 7
    assert game.pos == "1"
    assert game.offense is game.ai
    assert events[0] == {
        "seq": 0,
        "type": "quarter_started",
        "quarter": 3,
        "offense_seat": "away",
        "dealt": 7,
        "ball": "1",
    }
    assert events[1]["type"] == "possession_changed"
    assert events[1]["reason"] == "quarter_start"
