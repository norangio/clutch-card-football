# Clutch Card Football

Card-based football game. One Python rules engine, currently presented through a
Pygame desktop UI, with a browser 3-D edition in progress.

> **This repo is public.** Never commit the VPS IP, SSH targets, hostnames, or
> other infrastructure details to any tracked file, including this one.

---

## Current state (2026-08-07)

| | |
| --- | --- |
| **Active branch** | `web-edition` (trunk for all new work) |
| **`main`** | Old CRT UI + retired pygbag deploy. Do not build on it. |
| **Desktop UI** | Broadcast presentation, 960x720. Playable. |
| **Web 3-D edition** | Phase 0 done. Contract frozen at v2.1. Engine seeded + redacting serializers landed. Frontend HUD playable on fixtures. |
| **Hosting** | **None.** `ccf.norangio.dev` was taken down 2026-08-07. Local-only. |
| **Tests** | 127 passed, 2 skipped |

### What changed in Phase 0

`main` and the broadcast UI lived on two histories with **no merge base**:
`norangio/clutch-card-football` had all the deploy infrastructure and the old CRT
UI, while `sorangio/CodeDev` (remote `dad`, branch `agent/broadcast-ui`) had the
better engine and the broadcast UI. `web-edition` reconciles them: broadcast
engine and UI, on top of this repo's history.

The pygbag/WASM browser build was **retired**, not fixed. The broadcast
`PygameApp.__init__` takes no `browser_mode`/`_screen` arguments, so the old
`ccf_pygame/main.py` entry point could not construct it. Since the deployed
version was never really used, the site was taken down instead. Removed:
`ccf_pygame/main.py`, `scripts/build_browser.sh`,
`scripts/postprocess_browser_build.py`, `deploy.sh`, `deploy/`, `server/`,
`requirements-server.txt`, `.github/workflows/deploy.yml`.

All of it is recoverable from git history at `main` (`c0f2f4a`) if hosting ever
comes back.

---

## Running the game

```bash
cd ccf_pygame
pip install -r requirements.txt   # pygame-ce
python3 game.py
```

## Tests

```bash
cd ccf_pygame && python3 -m pytest test_ai.py test_ui.py -q
```

**59 passed, 2 skipped is the baseline. It must stay green at every commit.**
If a change needs the suite red, split it into two commits.

---

## Layout

```
ccf_pygame/
  ccf/                  the rules engine, no Pygame imports
    models.py           Card, Team, Color
    deck.py             deck construction, card values
    field.py            7 segments: 0 1 2 3 Z3 Z2 Z1
    drive_chart.py      (rating, card) -> movement
    rules.py            PAT, 2-point, field goal, punt
    ai.py               difficulty-aware AI
    state_machine.py    game flow, phases, transitions
    states.py           GamePhase enum, GameSnapshot
  ui/                   Pygame broadcast presentation
    app.py              application shell and frame loop
    screens/            score bar, hand rail, field band, action bar, ...
  test_ai.py, test_ui.py
mockups/                design exploration (broadcast / minimal / neon themes)
scripts/                original standalone scripts, pre-Pygame
```

Root-level `framework.py`, `game_window.py`, `launcher.py`, `ccf_run.py`, and
friends are the original pre-Pygame prototype. Not active. Left for reference.

---

## The 3-D web edition

Two documents are the plan of record. Read both before starting work:

- **[THREE_D_WEB_PLAN.md](THREE_D_WEB_PLAN.md)** what is being built and why
- **[AGENT_WORK_SPLIT.md](AGENT_WORK_SPLIT.md)** who builds which files

Architecture: the Python engine stays authoritative, a FastAPI service wraps it,
and a React + React Three Fiber frontend renders an ordered event stream. **The
rules never exist in TypeScript.**

### Agent ownership (strict)

| Owner | Files |
| --- | --- |
| **Sol** (Python) | `ccf_pygame/ccf/**`, `web_api/**`, `ccf_pygame/test_*.py`, `ccf_pygame/tests/**`, `ccf_pygame/ui/app.py` |
| **Claude** (TS + infra) | `web/**`, `ccf_pygame/ui/**` except `app.py`, all docs, all git work |

If you need a file you do not own, ask. Do not edit it. `docs/CONTRACT.md` is the
frozen interface (**v2.1**); changing a payload shape is its own commit, made
before any consumer changes.

> **Claude is paused (2026-08-07).** Sol holds git for the duration and works
> from **[SOL_QUEUE.md](SOL_QUEUE.md)**. Rules and the one permitted red-suite
> commit are described there. `web/` remains off-limits except
> `web/src/api/__fixtures__/generated/`.

---

## Known engine issues

Documented in detail in THREE_D_WEB_PLAN.md section 3. Summary:

1. **Hidden information leaks through `snapshot()`.** `Team.hand` rides inside
   the snapshot, and `_off_card` holds the AI's card during
   `WAITING_DEFENSE_CARD`. The Pygame UI hides this by convention, not by
   structure. A browser client would expose both. **Must be fixed before any
   HTTP surface exists.**
2. **Orange and green auto-touchdowns are never awarded.** `rules.apply_bonus()`
   is dead code, never imported. `drive_chart.py` defers those auto-TDs to
   "handled elsewhere", which does not exist. **Open question for the humans, do
   not fix silently** since it changes balance and diverges from dad's build.
3. Minor: dead `move()` call in `_do_punt()`; `offense.segments` can go negative
   on a war advance from Z2/Z1.

---

## Dad's repo (`sorangio/CodeDev`)

Configured as remote `dad`, **fetch only for now**. Nothing is pushed there yet.
Once the web edition is playable, publish a matching branch:

```bash
git push dad web-edition:refs/heads/web-edition
```

It lands as an **orphan branch** with no shared history, which is expected. See
THREE_D_WEB_PLAN.md section 1.6.

---

## Conventions

- Conventional commits: `type(scope): description`, subject under 72 chars,
  present tense, lowercase.
- `AGENTS.md` is a **symlink to this file**. Always edit `CLAUDE.md`. Never
  create or overwrite `AGENTS.md`.
- No em-dashes in prose.
