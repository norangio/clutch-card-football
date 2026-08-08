"""Generate a deterministic, contract-shaped full-game fixture dump."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ccf_pygame.ccf.ai import Difficulty
from ccf_pygame.ccf.models import Color
from ccf_pygame.ccf.serializers import serialize_events, serialize_snapshot
from ccf_pygame.ccf.state_machine import GameStateMachine
from ccf_pygame.ccf.states import GamePhase

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = REPO_ROOT / "web" / "src" / "api" / "__fixtures__" / "generated"


def _response(game, events, revision: int, game_id: str) -> dict:
    return {
        "revision": revision,
        "snapshot": serialize_snapshot(
            game,
            "home",
            game_id=game_id,
            revision=revision,
        ),
        "events": serialize_events(events, "home"),
    }


def _apply_first_enabled_action(game, snapshot: dict) -> None:
    action = next(item for item in snapshot["legal_actions"] if item["enabled"])
    if action["type"] == "play_card":
        game.provide_card(action["card_index"])
    elif action["type"] == "post_move":
        game.provide_post_move(action["choice"])
    elif action["type"] == "extra_point":
        game.provide_extra_point_choice(action["choice"])
    else:
        raise RuntimeError(f"unsupported generated action: {action['type']}")


def generate(seed: int = 42) -> list[dict]:
    """Play one full game and return only contract ``GameResponse`` objects."""
    game_id = f"generated-seed-{seed}"
    game = GameStateMachine(seed=seed)
    game.provide_setup(
        "Wolverines",
        7,
        2,
        Color.RED,
        2,
        "Buckeyes",
        6,
        2,
        2,
        difficulty=Difficulty.HARD,
    )
    revision = 0
    responses = [_response(game, game.pump(), revision, game_id)]

    while game.phase != GamePhase.GAME_OVER:
        _apply_first_enabled_action(game, responses[-1]["snapshot"])
        events = game.pump()
        revision += 1
        responses.append(_response(game, events, revision, game_id))
        if revision >= 100:
            raise RuntimeError("generated game exceeded 100 accepted actions")

    return responses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output or GENERATED_DIR / f"seed{args.seed}-full-game.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(generate(args.seed), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
