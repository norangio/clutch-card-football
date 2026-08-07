#!/usr/bin/env python3
"""Capture seeded golden transcripts of full games as regression fixtures.

These pin the engine's behavior BEFORE the Phase 1 refactor (pump/events/seeded
RNG). Any unintended behavior change shows up as a transcript diff.

Determinism works today with zero engine changes because deck.py, rules.py, and
ai.py all use Python's module-global `random`, so seeding it once at process
start fixes the entire game. See THREE_D_WEB_PLAN.md section 5.3.

Regenerate:  python3 scripts/capture_transcripts.py
Verify:      cd ccf_pygame && python3 -m pytest test_transcripts.py -q

IMPORTANT: only regenerate when a behavior change is intentional. Regenerating
to make a failing test pass defeats the entire point of these fixtures.
"""

import json
import os
import random
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_ROOT = os.path.join(REPO_ROOT, "ccf_pygame")
sys.path.insert(0, PKG_ROOT)

import ccf.ai as ai_mod                            # noqa: E402
from ccf.ai import Difficulty                      # noqa: E402
from ccf.models import Color                       # noqa: E402
from ccf.state_machine import GameStateMachine     # noqa: E402
from ccf.states import GamePhase                   # noqa: E402

FIXTURE_DIR = os.path.join(PKG_ROOT, "fixtures", "transcripts")
MAX_STEPS = 200_000

# Monte Carlo rollout count the fixtures were recorded at. Matches ai.py's
# default; pinned here so transcripts never depend on test execution order.
MC_EPISODES_FIXTURE = 120

# (seed, difficulty) pairs. AI vs AI so no human input is needed and the run
# exercises the whole state machine.
CASES = [
    (42, Difficulty.EASY),
    (42, Difficulty.MEDIUM),
    (42, Difficulty.HARD),
    (1337, Difficulty.MEDIUM),
    (1337, Difficulty.HARD),
    (2024, Difficulty.HARD),
]

# Human-vs-AI runs driven by _scripted_human, to reach the WAITING_* phases.
SCRIPTED_CASES = [
    (42, Difficulty.HARD),
    (1337, Difficulty.MEDIUM),
    (2024, Difficulty.EASY),
]

# Rating-1 teams, whose drive-chart entries include negative movement.
SAFETY_SEEDS = [7, 99, 314]


def _card(card):
    return None if card is None else str(card)


def fingerprint(game):
    """State values that must not drift. Excludes frame timers by design."""
    return {
        "phase": game.phase.name,
        "quarter": game.quarter,
        "turn": game.turn,
        "ball": game.pos,
        "offense": game.offense.name if game.offense else None,
        "home_score": game.human.score,
        "away_score": game.ai.score,
        "home_mojo": game.human.mojo,
        "away_mojo": game.ai.mojo,
        "home_clutch": game.human.clutch,
        "away_clutch": game.ai.clutch,
        "home_hand": len(game.human.hand),
        "away_hand": len(game.ai.hand),
        "off_card": _card(game._off_card),
        "def_card": _card(game._def_card),
        "war_card": _card(game._war_card),
        "clutch_card": _card(game._clutch_card),
        "movement": game._movement,
    }


def _scripted_human(game, turn_counter):
    """Deterministic stand-in for a human player.

    Deliberately biased toward the rarer branches (clutch, short punt, two-point)
    so the transcripts exercise phases a passive policy would never reach.
    """
    phase = game.phase
    if phase in (GamePhase.WAITING_OFFENSE_CARD, GamePhase.WAITING_DEFENSE_CARD):
        hand = game.offense.hand if phase == GamePhase.WAITING_OFFENSE_CARD \
            else game.defense.hand
        game.provide_card(turn_counter % len(hand) if hand else 0)
        return True
    if phase == GamePhase.WAITING_POST_MOVE:
        can_clutch, can_fg, can_punt, can_short = game._post_move_options()
        if can_clutch:
            choice = "C"
        elif can_short and turn_counter % 2 == 0:
            choice = "S"
        elif can_fg:
            choice = "F"
        else:
            choice = "P"
        game.provide_post_move(choice)
        return True
    if phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        game.provide_extra_point_choice("2" if turn_counter % 2 else "K")
        return True
    if phase == GamePhase.WAITING_CONFIRM:
        game.click_advance()
        return True
    return False


def _run(game, scripted):
    states, last, steps, decisions = [], None, 0, 0
    while game.phase != GamePhase.GAME_OVER and steps < MAX_STEPS:
        current = fingerprint(game)
        if current != last:
            states.append(current)
            last = current
        if scripted and _scripted_human(game, decisions):
            decisions += 1
        else:
            game.advance()
        steps += 1
    if steps >= MAX_STEPS:
        raise RuntimeError("game did not terminate")
    states.append(fingerprint(game))
    return states


def capture(seed, difficulty, scripted=False, ratings=(7, 6), kicks=(2, 2)):
    # The hard AI runs MC_EPISODES Monte Carlo rollouts per decision, each
    # drawing from the RNG, so this value is part of the scenario. Pin it:
    # test_ai.py mutates the module global, and an ambient value would make
    # transcripts depend on test execution order.
    ai_mod.MC_EPISODES = MC_EPISODES_FIXTURE

    random.seed(seed)
    game = GameStateMachine(fps=30)
    game.provide_setup(
        "HOME", ratings[0], kicks[0], Color.RED, 1,
        "AWAY", ratings[1], kicks[1], 1,
        difficulty, ai_vs_ai=not scripted,
    )

    states = _run(game, scripted)

    return {
        "seed": seed,
        "difficulty": difficulty.value,
        "mode": "scripted_human" if scripted else "ai_vs_ai",
        "ratings": list(ratings),
        "final": {
            "home_score": game.human.score,
            "away_score": game.ai.score,
            "quarter": game.quarter,
        },
        "phases_visited": sorted({s["phase"] for s in states}),
        "state_count": len(states),
        "states": states,
        "log": game.log,
    }


def _write(name, data, all_phases):
    path = os.path.join(FIXTURE_DIR, name)
    with open(path, "w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    all_phases.update(data["phases_visited"])
    print(f"  {name:30s} {data['state_count']:4d} states  "
          f"{data['final']['home_score']:3d}-{data['final']['away_score']:<3d}")


def main():
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    all_phases = set()

    for seed, difficulty in CASES:
        data = capture(seed, difficulty)
        _write(f"seed{seed}-{difficulty.value}.json", data, all_phases)

    # Scripted-human runs reach the WAITING_* phases and the short-punt branch.
    for seed, difficulty in SCRIPTED_CASES:
        data = capture(seed, difficulty, scripted=True)
        _write(f"human-seed{seed}-{difficulty.value}.json", data, all_phases)

    # Rating-1 offenses draw negative movement from the drive chart, which is
    # the only route to a safety.
    for seed in SAFETY_SEEDS:
        data = capture(seed, Difficulty.MEDIUM, scripted=True, ratings=(1, 1))
        _write(f"lowrating-seed{seed}.json", data, all_phases)

    every = {p.name for p in GamePhase}
    missing = sorted(every - all_phases)
    print(f"\nPhases covered: {len(all_phases)}/{len(every)}")
    if missing:
        print("NOT covered by any transcript:")
        for phase in missing:
            print(f"  - {phase}")
    else:
        print("Every GamePhase is exercised.")


if __name__ == "__main__":
    main()
