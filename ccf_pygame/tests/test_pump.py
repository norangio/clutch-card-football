"""Timer-free state-machine pumping for the web service."""

import pytest

from ccf.ai import Difficulty
from ccf.events import GameEndedEvent, QuarterStartedEvent
from ccf.models import Color
from ccf.state_machine import DECISION_PHASES, GameStateMachine
from ccf.states import GamePhase


def setup_game(*, ai_vs_ai=False, seed=42):
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
        ai_vs_ai=ai_vs_ai,
    )
    return game


def test_decision_phases_match_contract():
    assert DECISION_PHASES == {
        GamePhase.WAITING_OFFENSE_CARD,
        GamePhase.WAITING_DEFENSE_CARD,
        GamePhase.WAITING_POST_MOVE,
        GamePhase.WAITING_EXTRA_POINT_CHOICE,
        GamePhase.GAME_OVER,
    }
    assert GamePhase.WAITING_CONFIRM not in DECISION_PHASES


def test_pump_stops_at_first_human_decision_without_using_timers():
    game = setup_game()
    game._timer = -999

    events = game.pump()

    assert events == [QuarterStartedEvent(1, "home", 7, "1")]
    assert game.phase == GamePhase.WAITING_OFFENSE_CARD
    assert game._timer == -999


def test_ai_vs_ai_game_completes_through_one_pump_call():
    game = setup_game(ai_vs_ai=True)

    events = game.pump()

    assert isinstance(events[0], QuarterStartedEvent)
    assert isinstance(events[-1], GameEndedEvent)
    assert game.phase == GamePhase.GAME_OVER
    assert game.quarter == 5
    assert game.human.score >= 0
    assert game.ai.score >= 0


def test_pump_guard_raises_instead_of_hanging(monkeypatch):
    game = setup_game()
    monkeypatch.setattr(game, "_auto_transition", lambda: None)

    with pytest.raises(RuntimeError, match="exceeded max_steps=3"):
        game.pump(max_steps=3)


def test_pump_rejects_nonpositive_guard():
    game = setup_game()

    with pytest.raises(ValueError, match="at least 1"):
        game.pump(max_steps=0)


def test_pump_before_setup_fails_clearly():
    game = GameStateMachine(seed=1)

    with pytest.raises(RuntimeError, match="cannot advance phase SETUP_TEAMS"):
        game.pump()
