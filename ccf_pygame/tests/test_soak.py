"""Long-running, deterministic engine soak tests.

Run explicitly with::

    python3 -m pytest -m slow tests/test_soak.py -q -s
"""

from collections import Counter
from statistics import mean, pstdev

import pytest

from ccf.ai import Difficulty
from ccf.events import (
    CardPlayedEvent,
    ExtraPointResolvedEvent,
    FieldGoalResolvedEvent,
    SafetyScoredEvent,
    TouchdownScoredEvent,
)
from ccf.field import SEGMENTS
from ccf.models import Color
from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase

GAMES_PER_DIFFICULTY = 1_000
SCORING_PATHS = (
    "extra_point:kick",
    "extra_point:two",
    "field_goal",
    "safety",
    "touchdown:clutch",
    "touchdown:color_bonus",
    "touchdown:defensive_joker",
    "touchdown:drive",
    "touchdown:joker",
)


def _scoring_path(event) -> str | None:
    if isinstance(event, TouchdownScoredEvent):
        return f"touchdown:{event.cause}"
    if isinstance(event, FieldGoalResolvedEvent) and event.success:
        return "field_goal"
    if isinstance(event, SafetyScoredEvent):
        return "safety"
    if isinstance(event, ExtraPointResolvedEvent) and event.success:
        return "extra_point:kick" if event.choice == "K" else "extra_point:two"
    return None


@pytest.mark.slow
@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_one_thousand_games_reach_plausible_game_over(difficulty):
    scores: list[int] = []
    scoring_paths: Counter[str] = Counter({path: 0 for path in SCORING_PATHS})
    ties = 0

    for seed in range(GAMES_PER_DIFFICULTY):
        game = GameStateMachine(seed=seed)
        game.provide_setup(
            "Home",
            6,
            2,
            Color.RED,
            2,
            "Away",
            6,
            2,
            2,
            difficulty=difficulty,
            ai_vs_ai=True,
        )

        # Any runaway automatic transition raises from pump's built-in guard.
        events = game.pump()
        offensive_actions = sum(
            isinstance(event, CardPlayedEvent) and event.role == "offense"
            for event in events
        )

        assert game.phase == GamePhase.GAME_OVER
        assert 20 <= offensive_actions <= 30
        assert game.human.score >= 0
        assert game.ai.score >= 0
        assert game.pos in SEGMENTS

        scores.extend((game.human.score, game.ai.score))
        ties += game.human.score == game.ai.score
        for event in events:
            path = _scoring_path(event)
            if path is not None:
                scoring_paths[path] += 1

    distribution = (
        f"min={min(scores)}, max={max(scores)}, mean={mean(scores):.2f}, "
        f"stddev={pstdev(scores):.2f}, ties={ties / GAMES_PER_DIFFICULTY:.1%}"
    )
    path_rates = ", ".join(
        f"{path}={count / GAMES_PER_DIFFICULTY:.3f}/game"
        for path, count in sorted(scoring_paths.items())
    )
    print(f"\n{difficulty.value}: {distribution}; scoring events/game: {path_rates}")
