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

**Web edition (3-D, the active build):**

```bash
./run-local.sh
```

Starts FastAPI on `:8000` and Vite on `:5173`, creating the venv and installing
deps on first run. Open `http://localhost:5173`. Append `?mock=1` to run the
frontend on fixtures with no backend, which is useful for scene work.

**Pygame desktop edition:**

```bash
cd ccf_pygame
pip install -r requirements.txt   # pygame-ce
python3 game.py
```

## Tests

```bash
cd ccf_pygame && python3 -m pytest test_ai.py test_ui.py test_transcripts.py tests/ -q
```

**127 passed, 2 skipped is the baseline. It must stay green at every commit.**
If a change needs the suite red, split it into two commits. The single
exception is SOL_QUEUE.md task 5, where breaking the transcripts is the point.

`test_transcripts.py` compares against 12 seeded golden games. If it goes red,
a change altered gameplay. Do not regenerate the fixtures to make it pass;
read the diff first.

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

### ~~FIRST THING WHEN CLAUDE RESUMES: the actual 3-D field~~ DONE 2026-08-08

Nick saw the Phase 1b screenshot and said it "doesn't look like a 3-D rendering
of an actual game... I want to see stuff moving up and down a 3-D field."

He is right, and nothing is broken: `hud/components.tsx:Field` is a deliberate
flat CSS placeholder, and the plan puts 3-D in Phase 3. But the reaction is the
useful part. **The 3-D field is the thing he actually wants to see, and it
should be pulled forward rather than waiting for the full Phase 2 API
integration.** The fixtures already drive a complete play loop, so the R3F
scene can be built against them with no backend at all.

**Shipped:** `src/scene/StadiumScene.tsx`. Procedural tabletop, no external
assets: felt bed on a wood table, six segments, uprights, instanced crowd
blocks, team-coloured end zone, and a football that eases between segments with
a hop (taller arc on kicks). Fixed broadcast/endzone/wide camera shots that lerp
between each other, no free orbit. The HUD stayed in HTML.

The scene follows the **event stream**, not the snapshot: during playback the
ball sits where the current `ball_moved` says, so motion is visible instead of
already applied.

Still to do in Phase 3/4: per-event choreography (war, joker, clutch reveals),
confetti on scores, a low-quality mode, and card meshes on the table.

---

## Known engine issues

Documented in detail in THREE_D_WEB_PLAN.md section 3. Summary:

1. ~~Hidden information leaks through `snapshot()`.~~ **FIXED.** `serializers.py`
   decides visibility from `(viewer_seat, phase)` at construction. The raw
   `GameSnapshot` still carries both hands, so it must never be serialized
   directly; always go through `serialize_snapshot(game, viewer_seat)`.
2. **Orange and green auto-touchdowns are never awarded.** `rules.apply_bonus()`
   is dead code. **Decided 2026-08-07: implement it** (plan 3.2). Assigned as
   SOL_QUEUE.md task 5. Until that lands, the current non-award behavior is
   pinned by `tests/test_engine_characterization.py`.
3. **`WAITING_CONFIRM` is dead state**, never assigned. Keep it out of
   `DECISION_PHASES`; a test asserts it stays unassigned.
4. Minor: dead `move()` call in `_do_punt()`; `offense.segments` can go negative
   on a war advance from Z2/Z1. Both pinned by characterization tests.

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

---

## Known issue: 3-D canvas blank after a page reload

**Status: diagnosed, NOT fixed. 2026-08-08.**

Reproduction, with a freshly started dev server:

1. Load `http://localhost:5173` → canvas is `1142x329`, scene renders correctly.
2. Reload the page → canvas is `300x150` (the HTML default), scene never draws.
3. Restart the dev server → correct again on first load.

The game itself is unaffected: the HUD, the API, actions and resume all work.
Only the 3-D panel goes blank.

**What is happening.** R3F sizes its canvas from `react-use-measure`, which
reads the container once on mount. If that read returns zero the canvas keeps
the 300x150 default, and because the container's size never subsequently
*changes*, the ResizeObserver never fires again, so it never recovers. No
console error is produced, which is what makes it look like a build problem.

**Ruled out** (each tested and reverted):

- The scene effects. Bisected all four out; still reproduces.
- The loading placeholder / wrapper div. Fully reverted; still reproduces.
- `choreograph` breaking Fast Refresh. Real problem, now fixed by moving it to
  `scene/choreograph.ts`, but not the cause.
- Dispatching a synthetic `resize` after mount.
- Gating the Canvas behind a measured size, keying it on those dimensions, and
  `resize={{ debounce: 0, scroll: false }}`. **Note:** R3F's `style` prop styles
  its outer div, *not* the canvas, so sizing that div does not size the canvas.

**Important caveat.** Every measurement was taken through the automated browser
pane, which was reported hidden during some runs. A hidden window can legitimately
report zero layout, so this may be partly an artefact of the harness rather than
something a person with a visible window would hit. **Check it in a normal
Safari/Chrome window before spending more time on it.**

**Next thing to try:** an explicit `<canvas>` handed to R3F via the `gl` prop, or
forcing a remount keyed on `document.visibilityState`.
