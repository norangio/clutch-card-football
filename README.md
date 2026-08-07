# Clutch Card Football

Card-based football game. Two teams face off over four quarters, playing cards
from their hands to drive the ball down a seven-segment field and score.

One Python rules engine drives every presentation layer. Today that is a Pygame
desktop UI; a browser 3-D edition is in progress.

## Play it

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-desktop.txt
python3 ccf_pygame/game.py
```

The game runs at 960x720. Mouse-first, with keyboard entry for team names during
setup.

## Tests

```bash
cd ccf_pygame && python3 -m pytest test_ai.py test_ui.py -q
```

Baseline is 59 passed, 2 skipped.

## Layout

```
ccf_pygame/ccf/     rules engine, no Pygame imports
ccf_pygame/ui/      Pygame broadcast presentation
mockups/            design exploration (broadcast / minimal / neon)
scripts/            original standalone scripts, pre-Pygame
```

## The 3-D web edition

Planning is complete and Phase 0 has landed on the `web-edition` branch. The
architecture keeps the Python engine authoritative, wraps it in a FastAPI
service, and renders an ordered event stream in React and React Three Fiber.

- [THREE_D_WEB_PLAN.md](THREE_D_WEB_PLAN.md) what is being built and why
- [AGENT_WORK_SPLIT.md](AGENT_WORK_SPLIT.md) file ownership across the two agents
- [CLAUDE.md](CLAUDE.md) project conventions and current state

The first release runs locally. There is no hosted deployment.

## History

The repo carries two lineages. `main` holds the original CRT-styled UI and a
`pygbag`/WASM browser build that was deployed behind a reverse proxy. The
broadcast UI and the improved AI came from `sorangio/CodeDev` on a completely
separate history.

`web-edition` reconciles them. The `pygbag` build and its deploy pipeline were
retired on 2026-08-07, since the hosted version was not being used and the
broadcast UI was incompatible with the WASM entry point. Everything removed is
recoverable from `main` at `c0f2f4a`.

## Notes

- Field direction is team-based: human offense renders left to right, AI offense
  right to left.
- `AGENTS.md` is a symlink to `CLAUDE.md`. Always edit `CLAUDE.md`.
