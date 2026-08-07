"""Golden transcript regression tests.

These pin engine behavior captured BEFORE the Phase 1 refactor. A failure here
means a change altered gameplay. That is either a bug, or an intentional change
that requires regenerating the fixtures:

    python3 scripts/capture_transcripts.py

Never regenerate just to make a red test go green. Confirm the diff is the
change you meant to make first. See THREE_D_WEB_PLAN.md section 5.3.
"""

import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from capture_transcripts import (  # noqa: E402
    CASES,
    FIXTURE_DIR,
    SAFETY_SEEDS,
    SCRIPTED_CASES,
    capture,
)
from ccf.ai import Difficulty  # noqa: E402
from ccf.states import GamePhase  # noqa: E402


def _load(name):
    path = os.path.join(FIXTURE_DIR, name)
    if not os.path.exists(path):
        pytest.fail(f"missing fixture {name}; run scripts/capture_transcripts.py")
    with open(path) as handle:
        return json.load(handle)


def _compare(expected, actual, name):
    assert actual["final"] == expected["final"], (
        f"{name}: final score drifted "
        f"{expected['final']} -> {actual['final']}"
    )
    assert actual["state_count"] == expected["state_count"], (
        f"{name}: state count drifted "
        f"{expected['state_count']} -> {actual['state_count']}"
    )
    for index, (want, got) in enumerate(zip(expected["states"], actual["states"])):
        assert got == want, (
            f"{name}: state {index} drifted\n  expected {want}\n  actual   {got}"
        )
    assert actual["log"] == expected["log"], f"{name}: game log drifted"


@pytest.mark.parametrize("seed,difficulty", CASES)
def test_ai_vs_ai_transcript_is_stable(seed, difficulty):
    name = f"seed{seed}-{difficulty.value}.json"
    _compare(_load(name), capture(seed, difficulty), name)


@pytest.mark.parametrize("seed,difficulty", SCRIPTED_CASES)
def test_scripted_human_transcript_is_stable(seed, difficulty):
    name = f"human-seed{seed}-{difficulty.value}.json"
    _compare(_load(name), capture(seed, difficulty, scripted=True), name)


@pytest.mark.parametrize("seed", SAFETY_SEEDS)
def test_low_rating_transcript_is_stable(seed):
    name = f"lowrating-seed{seed}.json"
    actual = capture(seed, Difficulty.MEDIUM, scripted=True, ratings=(1, 1))
    _compare(_load(name), actual, name)


def test_same_seed_reproduces_same_game():
    """The determinism the whole fixture strategy depends on."""
    first = capture(42, Difficulty.HARD)
    second = capture(42, Difficulty.HARD)
    assert first == second


def test_different_seeds_diverge():
    assert capture(42, Difficulty.HARD)["states"] != \
        capture(43, Difficulty.HARD)["states"]


def test_transcripts_cover_every_reachable_phase():
    """Guards the coverage claim in THREE_D_WEB_PLAN.md.

    SETUP_TEAMS is left before the first sample is taken. WAITING_CONFIRM is
    dead state: nothing in the engine ever assigns it (see plan section 3.4).
    """
    unreachable = {GamePhase.SETUP_TEAMS.name, GamePhase.WAITING_CONFIRM.name}
    covered = set()
    for name in os.listdir(FIXTURE_DIR):
        if name.endswith(".json"):
            covered.update(_load(name)["phases_visited"])

    expected = {phase.name for phase in GamePhase} - unreachable
    assert expected <= covered, f"phases lost coverage: {sorted(expected - covered)}"


def test_waiting_confirm_is_still_unassigned():
    """If this fails, WAITING_CONFIRM became reachable and needs a transcript."""
    source = os.path.join(REPO_ROOT, "ccf_pygame", "ccf", "state_machine.py")
    with open(source) as handle:
        body = handle.read()
    assert "phase = GamePhase.WAITING_CONFIRM" not in body
