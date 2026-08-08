"""Statistical proof that the three AI difficulty levels form a real ladder."""

from dataclasses import dataclass

import pytest

from ccf.ai import (
    Difficulty,
    choose_card,
    extra_point_choice,
    post_move_choice,
)
from ccf.models import Color
from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase

SEEDS_PER_ORIENTATION = 20


@dataclass
class PairingResult:
    wins: int = 0
    losses: int = 0
    ties: int = 0
    score_differential: int = 0


def play_mixed_difficulty_game(
    seed: int,
    *,
    home_difficulty: Difficulty,
    away_difficulty: Difficulty,
) -> tuple[int, int]:
    """Run the home seat through AI helpers at its own difficulty.

    The engine controls the away seat using its normal difficulty setting. The
    home seat is the engine's nominal human, so this small test controller calls
    the same AI decision functions whenever a human decision boundary appears.
    """
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
        difficulty=away_difficulty,
    )
    actions = 0

    while game.phase != GamePhase.GAME_OVER:
        game.pump()
        if game.phase == GamePhase.GAME_OVER:
            break

        if game.phase in (
            GamePhase.WAITING_OFFENSE_CARD,
            GamePhase.WAITING_DEFENSE_CARD,
        ):
            is_offense = game.phase == GamePhase.WAITING_OFFENSE_CARD
            team = game.offense if is_offense else game.defense
            opponent = game.defense if is_offense else game.offense
            card_index = choose_card(
                game.pos,
                team,
                is_offense,
                difficulty=home_difficulty,
                opponent=opponent,
                opponent_card=None if is_offense else game._off_card,
                deck_remaining=list(game.deck),
                rng=game._rng,
            )
            game.provide_card(card_index)
        elif game.phase == GamePhase.WAITING_POST_MOVE:
            choice = post_move_choice(
                game.pos,
                game.offense.clutch,
                game.offense.clutch_used,
                difficulty=home_difficulty,
                team=game.offense,
                opponent=game.defense,
                deck_remaining=list(game.deck),
                rng=game._rng,
            )
            game.provide_post_move(choice)
        elif game.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            scorer = game._scorer or game.offense
            opponent = (
                game.defense if scorer is game.offense else game.offense
            )
            choice = extra_point_choice(
                home_difficulty,
                score_diff=scorer.score - opponent.score,
                quarter=game.quarter,
                rng=game._rng,
            )
            game.provide_extra_point_choice(choice)
        else:
            raise AssertionError(f"unexpected decision phase: {game.phase}")

        actions += 1
        assert actions < 100

    return game.human.score, game.ai.score


def run_pairing(
    stronger: Difficulty,
    weaker: Difficulty,
) -> PairingResult:
    result = PairingResult()
    for seed in range(SEEDS_PER_ORIENTATION):
        for stronger_is_home in (True, False):
            home_difficulty = stronger if stronger_is_home else weaker
            away_difficulty = weaker if stronger_is_home else stronger
            home_score, away_score = play_mixed_difficulty_game(
                seed,
                home_difficulty=home_difficulty,
                away_difficulty=away_difficulty,
            )
            stronger_score, weaker_score = (
                (home_score, away_score)
                if stronger_is_home
                else (away_score, home_score)
            )
            result.score_differential += stronger_score - weaker_score
            if stronger_score > weaker_score:
                result.wins += 1
            elif stronger_score < weaker_score:
                result.losses += 1
            else:
                result.ties += 1
    return result


@pytest.mark.parametrize(
    "stronger,weaker",
    [
        (Difficulty.MEDIUM, Difficulty.EASY),
        (Difficulty.HARD, Difficulty.MEDIUM),
        (Difficulty.HARD, Difficulty.EASY),
    ],
)
def test_stronger_difficulty_wins_meaningfully_more_than_half(stronger, weaker):
    result = run_pairing(stronger, weaker)
    total_games = SEEDS_PER_ORIENTATION * 2

    assert result.wins >= int(total_games * 0.60), (
        f"{stronger.value} did not establish an advantage over {weaker.value}: "
        f"{result}"
    )
    assert result.wins > result.losses
    assert result.score_differential > 0
