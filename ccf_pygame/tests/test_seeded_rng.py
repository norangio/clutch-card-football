"""Per-game RNG isolation and reproducibility."""

import random

import pytest

from ccf.ai import Difficulty
from ccf.models import Color
from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase


def make_seeded_game(seed):
    game = GameStateMachine(fps=1, seed=seed)
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
        ai_vs_ai=True,
    )
    return game


def finish(game):
    for _ in range(10_000):
        if game.phase == GamePhase.GAME_OVER:
            return {
                "home_score": game.human.score,
                "away_score": game.ai.score,
                "home_stats": (
                    game.human.segments,
                    game.human.fg_made,
                    game.human.fg_att,
                    game.human.punts,
                ),
                "away_stats": (
                    game.ai.segments,
                    game.ai.fg_made,
                    game.ai.fg_att,
                    game.ai.punts,
                ),
                "log": list(game.log),
            }
        game.advance()
    raise AssertionError(f"seeded game did not finish: {game.phase}")


def test_same_seed_reproduces_full_game_without_global_seed():
    first = finish(make_seeded_game(42))

    random.seed(987654321)
    for _ in range(100):
        random.random()

    second = finish(make_seeded_game(42))

    assert second == first


def test_different_seeds_produce_different_initial_deals():
    first = make_seeded_game(42)
    second = make_seeded_game(43)

    first_cards = [str(card) for card in first.human.hand + first.ai.hand]
    second_cards = [str(card) for card in second.human.hand + second.ai.hand]

    assert second_cards != first_cards


def test_injected_rng_matches_equivalent_seed():
    seeded = make_seeded_game(42)

    injected = GameStateMachine(fps=1, rng=random.Random(42))
    injected.provide_setup(
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
        ai_vs_ai=True,
    )

    assert [str(card) for card in injected.human.hand] == [
        str(card) for card in seeded.human.hand
    ]
    assert [str(card) for card in injected.ai.hand] == [
        str(card) for card in seeded.ai.hand
    ]


def test_seed_and_rng_are_mutually_exclusive():
    with pytest.raises(ValueError, match="either rng or seed"):
        GameStateMachine(seed=42, rng=random.Random(42))
