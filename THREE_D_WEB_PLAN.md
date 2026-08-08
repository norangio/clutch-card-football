# Clutch Card Football: 3-D Web Edition

**Status:** finalized plan of record. Supersedes the earlier draft of this file.
**Date:** 2026-08-07
**Companion doc:** [AGENT_WORK_SPLIT.md](AGENT_WORK_SPLIT.md) (who builds what)

---

## 1. Locked decisions

These were open questions in the draft. They are now settled and the rest of this
document assumes them.

| Decision | Choice |
| --- | --- |
| **Deployment** | **Local-first.** v1 runs on localhost via one command, same posture as launching the Pygame build today. Hosting is a deferred, optional Phase 5. |
| **Live site** | **Taken down 2026-08-07.** The hosted pygbag build was never really used, and the broadcast UI was incompatible with its WASM entry point. There is no hosted CCF. |
| **Play mode** | Solo vs the existing AI for v1. Remote head-to-head is out of scope but the contract must not preclude it. |
| **Visual tone** | Premium tabletop. Miniature stadium on a table, soft studio lighting, chunky low-poly, felt and wood materials. |
| **Pygame edition** | Stays first-class. Shared engine, adapter kept working, doubles as a fast test harness. The pygbag/WASM build is retired. |
| **Trunk** | `origin/main` (`norangio/clutch-card-football`) becomes the single source of truth and is where all work happens for now. The broadcast work is ported onto it. |
| **Dad's repo** | Eventually gets a **matching branch** on `sorangio/CodeDev` mirroring the new edition, so he can follow along. Not now. See 1.6. |

Going local-first is the single biggest scope reduction available. It removes
Caddy, systemd, TLS, session expiry, and rollback from the critical path, and it
means a broken build never takes down something the family is using.

---

## 1.5 Who builds what

Two agents build this. **Sol owns Python. Claude owns TypeScript, plus git and
infra.** They meet at one frozen JSON contract and never edit the same file.
Section headings below are tagged with their owner. Full task lists, acceptance
criteria, and handoff points are in [AGENT_WORK_SPLIT.md](AGENT_WORK_SPLIT.md).

| Area | Owner | Files |
| --- | --- | --- |
| Engine, events, serializers | **Sol** | `ccf_pygame/ccf/**` |
| FastAPI service, SQLite sessions | **Sol** | `web_api/**` |
| Engine + API + redaction tests | **Sol** | `ccf_pygame/test_*.py`, `ccf_pygame/tests/**` |
| Pygame adapter | **Sol** | `ccf_pygame/ui/app.py` only |
| React HUD, R3F scene, animation director | **Claude** | `web/**` |
| Broadcast Pygame UI | **Claude** | `ccf_pygame/ui/**` except `app.py` |
| Git, branches, remotes, merges | **Claude** | repo-wide |
| Deploy, Caddy, launch config, docs | **Claude** | `deploy/`, `.github/`, `*.md`, `.claude/` |
| Interface spec | **Claude** drafts, **Sol** reviews, then frozen | `docs/CONTRACT.md` |

**The rule that makes this work:** if you need a file you do not own, ask the
other agent. Do not edit it. The Python/TypeScript boundary is a clean partition
of the tree with exactly one interface across it.

**Neither agent may:** change a contract payload shape and a consumer of it in
the same commit. Update `docs/CONTRACT.md` first, in its own commit, then both
sides pull.

---

## 1.6 Dad's repo (`sorangio/CodeDev`)

All work happens in `norangio/clutch-card-football` for now. Once the web edition
is real (Phase 2 at the earliest, when there is something playable to show), we
publish a **matching branch** to `dad` so he can follow the work.

Two things to know when that day comes:

1. **It lands as an orphan branch.** The histories are unrelated (see 2.1), so
   the branch will share no commits with his `trunk` and cannot be fast-forwarded
   or normally merged into it. That is fine and expected, but he should be told,
   otherwise the branch looks broken.
2. **Push access is confirmed but not admin.** The `norangio` account has
   `push: true` on the repo, so `git push dad <branch>` works. It cannot create
   protected-branch rules or change settings.

Suggested branch name: `web-edition`. Publish with an explicit refspec so there
is no chance of touching his trunk:

```bash
git push dad web-edition:refs/heads/web-edition
```

**Until then, nothing is pushed to `dad`.** The remote stays configured for
fetching only.

---

## 2. What is actually in the repo today

The draft plan was written without this. It changes the sequencing materially.

### 2.1 The trunk split is real and has no merge base

`git merge-base origin/main HEAD` returns **nothing**. The two histories are
completely unrelated. They split as follows:

| | `origin/main` (norangio) | `agent/broadcast-ui` (from `dad`, current checkout) |
| --- | --- | --- |
| Engine quality | older | **better** (smarter AI, more phases) |
| UI | retro CRT | **broadcast presentation** |
| `deploy.sh`, `deploy/Caddyfile.snippet`, `deploy/clutch-card-football.service` | **yes** | no |
| `.github/workflows/deploy.yml` | **yes** | no |
| `scripts/build_browser.sh`, `scripts/postprocess_browser_build.py` | **yes** | no |
| `requirements-server.txt`, `server/launcher.py` | **yes** | no |
| Currently deployed | **yes** | no |

So the good code and the good infrastructure are on opposite sides. That is the
first thing to fix, and it is the reason Phase 0 exists.

### 2.2 The engine diff is small

Only four engine files differ between the branches:

```
ccf/ai.py             +309 / -21
ccf/state_machine.py  +110 / -64
ccf/models.py         +4  / -0
ccf/states.py         +2  / -0
```

`deck.py`, `drive_chart.py`, `field.py`, and `rules.py` are **byte-identical**.
The port is a tractable, reviewable change, not a merge nightmare.

### 2.3 The live site is static, not a service

```
ccf.norangio.dev {
    root * /opt/clutch-card-football/ccf_pygame/build/web
    basic_auth { ccf_football ... }
    handle /cdn/* { reverse_proxy https://pygame-web.github.io }
    try_files {path} /index.html
    file_server
}
```

Caddy served the pygbag build directly off disk. `systemctl is-active
clutch-card-football` reported **inactive**; that unit was the abandoned noVNC
streaming approach.

**Removed in Phase 0.** The vhost was deleted from the Caddyfile (backup at
`/etc/caddy/Caddyfile.bak-20260807-232052`), Caddy reloaded, and the deploy
workflow disabled. `/opt/clutch-card-football` is still on disk, so this is
reversible. If hosting ever returns it needs a new Caddy block and a new
service; nothing here is reusable for a React app.

### 2.4 Test baseline

Was **59 passed, 2 skipped**. Phase 0 added `test_transcripts.py`, bringing it
to **75 passed, 2 skipped**. It must stay green through every phase.

The transcripts are the meaningful part. A one-character rules change (the
two-point threshold, 5+ to 4+) passes all 59 original tests and is caught only
by the transcripts.

### 2.5 Documentation symlinks are broken on both sides

- Working tree: `claude.md -> AGENTS.md`, and `AGENTS.md` did not exist.
- `origin/main`: `AGENTS.md` symlinked to `CLAUDE.md`, which was **in
  `.gitignore`**, so the target could never exist.

Both dangled, in opposite directions. **Fixed in Phase 0**: `CLAUDE.md` removed
from `.gitignore` and written as the real file, `AGENTS.md` symlinks to it, and
the stray lowercase `claude.md` was deleted. That last one mattered: on a
case-insensitive macOS filesystem, `claude.md -> AGENTS.md -> CLAUDE.md` is a
symlink loop, and writing the file failed with `ELOOP` until it was removed.

---

## 3. Engine defects found during review &nbsp;&nbsp;`[owner: Sol]`

These are **pre-existing**, not introduced by the refactor. They must be
characterized by fixtures *before* any restructuring, otherwise we will not know
whether a later behavior change was intentional.

### 3.1 Hidden information leaks through `snapshot()` (must fix)

Two separate leaks, both fatal for a browser client where the payload is visible
in devtools:

1. **Full opponent hand.** `GameSnapshot` carries `human: Team` and `ai: Team`,
   and `Team` has `hand: List[Card]`. Serializing the snapshot naively hands the
   client the AI's entire hand.

2. **The AI's offensive card, before the human commits their defense.** In
   `_ai_play_offense()` (`ccf_pygame/ccf/state_machine.py:376`), `self._off_card`
   is set and the phase becomes `WAITING_DEFENSE_CARD`. The Pygame UI hides this
   by *convention*, drawing `"AI plays card ..."`. There is no structural
   protection. The web API would ship the human a live cheat.

The fix is not "never expose an AI card". It is **redaction driven by phase**:
a serializer that takes a viewer identity and the current phase and decides what
is legal to reveal. This needs its own test file.

### 3.2 Orange and green auto-touchdowns: DECIDED, implement them

`rules.apply_bonus()` is **dead code**, never imported or called.
`drive_chart.get_drive_result()` returns:

```python
elif bonus_type == "orange":
    return base_yards  # orange bonus is auto-TD at Z1, handled elsewhere
elif bonus_type == "green":
    return base_yards + 1  # green = +1 and Z1 auto-TD, handled elsewhere
```

"Handled elsewhere" does not exist. Green's `+1` is applied; **neither auto-TD
is**. The structural reason it was missed: `get_card_result()` is called in
`_resolve_play()` *before* `move()`, so `end_pos` is unknown at that point.

**Decision (2026-08-07): implement it.** Reasoning:

1. It is **designed intent, not a house rule.** The drive chart carries explicit
   `bonus: "orange"` and `bonus: "green"` data, and `apply_bonus()` exists and
   documents the behavior. This is an unfinished feature, not a deliberate
   simplification. The alternative is deleting a designed mechanic.
2. **It is a highlight moment**, which directly serves the 3-D presentation.
   Landing exactly on Z1 with a color-matched Ace becoming an instant touchdown
   is the rarest and most dramatic scoring path in the game. That is worth
   animating and worth having exist.
3. **Divergence is no longer a real cost.** Both editions now come from this
   trunk, and dad's repo gets a matching branch, so the change carries to him
   rather than splitting the rules.

Rule as implemented: when a **color-matched** card whose drive-chart entry
carries an `orange` or `green` bonus produces a move that **lands exactly on
Z1**, the play is an automatic touchdown. Green keeps its existing `+1`. A move
that runs past Z1 is already a touchdown by normal rules and is unaffected.

**This is a behavior change**, so it is the one place the golden transcripts are
expected to break. Process: Sol implements and flips the two characterization
tests; Claude then regenerates the transcripts and reviews the diff to confirm
only auto-touchdown plays moved. Regenerating without reading the diff defeats
the fixtures.

Contract v2 adds `color_bonus` to `touchdown_scored.cause` so the celebration
can be distinct.

### 3.3 Minor issues

- `_do_punt()` (`state_machine.py:582`) calls `move(self.pos, dist)` and
  **discards the result**, then recomputes with index math. The discarded call
  was also directionally wrong (positive `dist` moves forward). Dead line, safe
  to delete. The `max(1, idx - dist)` clamp is the real behavior and means a punt
  can never cause a safety, which is probably intended but is currently implicit.
- `_handle_war()` adds `SEGMENTS.index("Z3") - SEGMENTS.index(old_pos)` to
  `offense.segments`, which goes **negative** if the ball was already past Z3
  (at Z2 or Z1). Stat-tracking only, no gameplay effect.
- Empty-deck fallbacks (`Card("2","S")` in war, `Card("A","H")` in clutch) are
  deterministic but untested. Needs a fixture.
- `_apply_speed()` couples presentation speed to `ai_vs_ai`. The web edition
  ignores this entirely; speed becomes a client concern.

### 3.4 `WAITING_CONFIRM` is dead state

Nothing in the engine ever assigns `GamePhase.WAITING_CONFIRM`. It is handled in
`click_advance()` and rendered in `ui/screens/play_panel.py:134`, but both
branches are unreachable. `_next_phase` is likewise initialized to `None` and
only ever read, never set.

**Impact on Phase 1:** do not put it in `DECISION_PHASES`, and do not define a
`confirm` action in the contract. `test_transcripts.py` asserts it stays
unassigned, so if someone makes it reachable the test will say so.

### 3.5 `test_ai.py` leaked global state (fixed in Phase 0)

`test_ai.py` mutated the module global `ai_mod.MC_EPISODES` at three sites (to
400, 400, and 60) and never restored it. The hard AI runs `MC_EPISODES` Monte
Carlo rollouts per decision, each drawing from the RNG, so a leaked value
changed both its choices and the number of RNG draws. Any later test in the same
process saw a different game.

Fixed with `addCleanup` at each site. `capture_transcripts.py` also pins
`MC_EPISODES` explicitly, so transcripts can never depend on test execution
order. Worth knowing because it is exactly the class of bug that makes a
"reproducible" seed not reproduce.

---

## 4. Architecture

Unchanged from the draft in its essentials, which were correct. One Python
engine, two presentations, an event stream between them.

```text
Browser (localhost:5173)
├── React HUD (HTML/CSS)      scoreboard, hand, actions, log, drive chart
├── R3F tabletop scene        field, ball, cards, cameras, effects
└── Animation director        consumes ordered events, locks input
          │
          │  HTTP (Vite proxies /api -> :8000, so one origin)
          ▼
FastAPI session service (localhost:8000)
├── SQLite session store
└── Redacting serializers
          ▼
ccf/ engine  (models, deck, drive_chart, field, rules, ai, state_machine)
          ▲
          └── Pygame adapter (unchanged presentation, same engine)
```

Two rules that carry the whole design:

1. **The rules never exist in TypeScript.** The frontend renders events. It never
   decides an outcome.
2. **Every state change is explained by an event.** No animation infers what
   happened by diffing snapshots.

---

## 5. The engine refactor is smaller than it looks &nbsp;&nbsp;`[owner: Sol]`

The draft framed this as a large restructuring. It is not. `advance()` is the
**only** frame-coupled method in the entire engine, and `_auto_transition()` is
already a clean discrete step function. The work is:

### 5.1 Add a pump, do not rewrite the state machine

```python
DECISION_PHASES = {
    GamePhase.SETUP_TEAMS,
    GamePhase.WAITING_OFFENSE_CARD,
    GamePhase.WAITING_DEFENSE_CARD,
    GamePhase.WAITING_POST_MOVE,
    GamePhase.WAITING_EXTRA_POINT_CHOICE,
    GamePhase.GAME_OVER,
}

def pump(self, max_steps: int = 200) -> list[GameEvent]:
    """Run every automatic transition until a human decision is required.

    Replaces frame-timer advancement. Records an event per transition.
    """
```

`pump()` loops: if the phase is an AI turn, run the AI immediately (no delay
frames); if it is a showing phase, call `_auto_transition()`; if it is a decision
phase, stop and return the accumulated events. The `max_steps` guard turns any
future infinite loop into a clean error instead of a hang.

The Pygame adapter keeps its existing `advance()` path unchanged. Both call the
same underlying transitions.

### 5.2 Seeded randomness, in two commits

`random` is used as a **module global** in three files: `deck.py` (shuffle),
`rules.py` (five `randint` calls), `ai.py` (four call sites). Threading a seed
means touching all three.

Do it as two separate commits so the safety net survives:

- **Commit A (plumbing only).** Add an optional `rng` parameter defaulting to
  `None`, meaning "use the global `random` module". Call order is unchanged, so
  the 59 existing tests and all Phase 0 golden transcripts stay byte-identical.
  This commit is provably behavior-preserving.
- **Commit B (activate).** `GameStateMachine.__init__(seed=...)` creates
  `random.Random(seed)` and passes it down. Transcripts now differ from the
  global-RNG ones (different draw sequence), which is expected. The new invariant
  is "same seed reproduces the same game", verified against freshly captured
  fixtures.

### 5.3 Golden transcripts can be captured *before* any refactor

Because all three modules share Python's global RNG, calling `random.seed(42)` at
process start makes the entire game **deterministic today**, with zero code
changes. Phase 0 can therefore record full-game transcripts as regression
fixtures before a single line is restructured. This is what makes the whole plan
safe, and it is why Phase 0 comes first.

### 5.4 Event contract

JSON-safe, ordered, sufficient to animate and to explain. Event types:

`quarter_started`, `card_played`, `cards_revealed`, `war_started`,
`war_card_revealed`, `joker_resolved`, `ball_moved`, `mojo_changed`,
`mojo_converted_to_clutch`, `clutch_used`, `possession_changed`, `punt_resolved`,
`field_goal_resolved`, `touchdown_scored`, `safety_scored`,
`extra_point_resolved`, `quarter_ended`, `game_ended`.

```json
{ "type": "ball_moved", "team": "home", "from": "2", "to": "Z2",
  "segments": 3, "reason": "drive_chart", "is_td": false, "is_safety": false }
```

Every event includes only what is needed to render it. Design rule: **if the
frontend has to look at the snapshot to animate an event, the event is
underspecified.**

### 5.5 Snapshot

Includes: session id, revision, phase, required action, quarter, play number and
plays remaining, ball position, possession, scores, ratings, colors, mojo,
clutch, **the viewer's hand only**, opponent hand *count*, cards revealed so far
this play, legal actions with disabled reasons, recent log, game result.

Excludes, always: the deck, the opponent's hand, any card not yet revealed by the
rules.

---

## 6. API &nbsp;&nbsp;`[owner: Sol]`

Plain HTTP. No WebSockets until remote multiplayer, which is out of scope.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/games` | Create from setup choices, returns id + seed |
| `GET` | `/api/games/{id}` | Load or resume |
| `POST` | `/api/games/{id}/actions` | Submit card or post-play decision |
| `POST` | `/api/games/{id}/restart` | New game, same setup |
| `GET` | `/api/games/{id}/replay` | Full event history (debug, replay) |
| `GET` | `/healthz` | Health check |

Note there is **no `/advance`**. `pump()` runs every automatic transition
server-side and returns the whole event batch with the action response. The
client owns pacing, not the server. This is simpler than the draft and removes a
round trip per animation.

Actions carry the client's last known `revision`. A stale or duplicated revision
is rejected without mutating state, which kills double-submit from impatient
tapping.

```json
// request
{ "revision": 12, "type": "play_card", "card_index": 3 }
// response
{ "revision": 13, "snapshot": { }, "events": [ ] }
```

**Storage:** SQLite, one row per session, holding serialized state, seed,
revision, and event log. Even locally this is worth it, because it is what makes
"refresh the browser and your game is still there" work. Roughly thirty lines.

---

## 7. Frontend &nbsp;&nbsp;`[owner: Claude]`

```text
web/
├── src/
│   ├── api/        client.ts, types.ts, __fixtures__/
│   ├── game/       GamePage.tsx, useGameSession.ts, useAnimationQueue.ts
│   ├── hud/        Scoreboard, CardHand, ActionBar, DriveChart, GameLog
│   ├── scene/      StadiumScene, CameraDirector, Field, Ball, CardStage,
│   │               Lighting, effects/
│   └── setup/      SetupScreen.tsx
└── public/assets/
```

### 7.1 No Blender. Procedural geometry only.

This is the most important correction to the draft, which proposed modeling in
Blender and exporting `.glb`. Neither agent can model in Blender, and a
dependency on hand-authored assets is what turns this project into an unfinished
one.

Everything is built from R3F primitives and code:

- Field: a `<Plane>` with a generated segment texture, or seven extruded boxes.
- Stadium bowl: revolved/extruded boxes, instanced crowd blocks.
- Uprights: three cylinders.
- Ball: a scaled icosahedron or lathe geometry. One small CC0 `.glb` is the
  single permitted exception if the procedural one looks wrong.
- Cards: thin boxes with canvas-generated face textures.
- Clutch coin: a cylinder with an emissive rim.
- Confetti: instanced planes.

Premium tabletop tone comes from **lighting and material**, not polygon count:
soft area lights, a subtle contact shadow, felt roughness, a warm key with a cool
rim. This is achievable entirely in code and degrades gracefully.

### 7.2 Card identity has one source

The HTML hand and the 3-D reveal card must render from the same card
identity module, so they cannot disagree about what was played.

### 7.3 Camera director

Fixed shots, no free orbit. Default elevated sideline; push to midfield for the
card battle; lateral track for movement; behind the uprights for a field goal;
wide overhead for a punt; low end zone for a touchdown; centered reveal for
war and joker. Always return to default. Reduced-motion replaces travel with
cuts.

### 7.4 Animation director

One coordinator, not components independently reacting to state. It receives the
ordered event list, locks input, plays each event with its registered camera and
scene animation, updates the HUD at the right beat, supports skip and speed, and
unlocks the next legal action only when the queue drains.

Use an explicit timeline rather than scattered `setTimeout`s.

**Registry invariant, enforced by test:** every event type in the contract maps
to a registered handler. An unknown event type is a loud failure in dev and a
silent instant state-apply in production, never a stuck queue.

---

## 8. Testing

Owners: **Sol** writes engine, redaction, contract, and API tests. **Claude**
writes frontend tests and drives the browser end-to-end runs.

**Engine (pytest). `[Sol]`** Keep the 59 green. Add: card comparison and movement, color
bonuses *as currently implemented* (see 3.2), both joker directions across all
value ranges, war both outcomes, touchdown, safety, PAT and two-point, field goal
made and missed at each of Z1/Z2/Z3, punt and short punt, clutch including the
joker-clutch path, mojo accumulation and clutch conversion, quarter dealing and
possession handoff, empty-deck fallbacks, full seeded games at each difficulty.

**Redaction (its own file). `[Sol]`** For every phase, assert the serialized payload
contains no card the viewer is not entitled to see. Explicitly assert the
`WAITING_DEFENSE_CARD` case from 3.1.

**Contract. `[Sol]`** Snapshot validates against schema; event order is stable for a
fixed seed; every score, position, possession, mojo, and clutch delta is
explained by an event; invalid or replayed revisions do not mutate; a reloaded
session is identical.

**Frontend. `[Claude]`** Every event type has a handler; skipping produces the same final
scene state as watching; rapid clicks cannot double-submit; refresh resumes from
every decision phase; the game is playable with the 3-D layer disabled.

**End to end. `[Claude]`** Full games vs easy, medium, and hard AI; AI vs AI for coverage;
refresh mid-quarter; server restart with a live session; Chrome and **Safari**
(your primary browser, and WebKit's WebGL behavior differs from Chromium's).

---

## 9. Phases

Each phase is tagged with its owner. Where a phase is split, the two halves run
in parallel and are listed separately.

### Phase 0: Trunk reconciliation and behavior lock &nbsp;&nbsp;`[Claude]` &nbsp;**DONE 2026-08-07**

- [x] Branch `web-edition` created off `origin/main`. Ported the four changed
      engine files and the broadcast `ui/` layer onto it. `main` is untouched.
- [x] Retired the pygbag build and its deploy pipeline; took the live site down.
- [x] `dad` remains fetch only. Nothing pushed there (see 1.6).
- [x] Docs symlink repaired: real `CLAUDE.md`, `AGENTS.md` symlinked to it,
      stray `claude.md` removed, `CLAUDE.md` un-ignored.
- [x] Scrubbed the VPS IP from this public repo (and from `f1-analytics` and
      `investment-simulations-streamlit`, which had the same leak).
- [x] Golden transcripts captured: 12 fixtures at
      `ccf_pygame/fixtures/transcripts/`, covering every reachable `GamePhase`,
      with `test_transcripts.py` verifying them.
- [x] Fixed a pre-existing test-pollution bug that made seeds non-reproducible
      (see 3.5).
- [x] 75 passed, 2 skipped, order-independent.
- [x] Sol's `tests/test_engine_characterization.py` landed and committed: all
      five section 3 defects pinned. 84 passed, 2 skipped.
- [x] `docs/CONTRACT.md` **frozen at Version 1**. Sol raised eight findings,
      all valid, all applied. The serious one: an active snapshot exposed
      `seed`, which reconstructs the entire deck.
- [x] **H1 complete.** Phase 1a is unblocked.
- [x] Seeded RNG **commit A** (behavior-neutral plumbing) landed.
- [ ] Raise the 3.2 orange/green question with the humans. **Open**, does not
      block any phase.

**Exit:** one branch holds the best engine and the best UI; tests green; golden
transcripts committed and proven to catch regressions; the contract is drafted.

**Handoff H1: complete 2026-08-07.** `docs/CONTRACT.md` is frozen at Version 1.
Its section 0 records the eight findings and their resolutions so they do not
get re-litigated.

### Phase 1a: Presentation-independent engine &nbsp;&nbsp;`[Sol]`

- `pump()` and the decision-phase set.
- Event dataclasses and emission at every transition.
- Seeded RNG, commits A then B.
- Redacting serializers plus the redaction test file. **Do this first**; two live
  leaks are documented in 3.1 and every other shape depends on it.
- Pygame adapter (`ui/app.py`) updated, still playable.

**Exit:** every state mutation emits an event; a seed reproduces a game exactly;
no payload leaks hidden cards; Pygame plays end to end; 59 tests still green.

### Phase 1b: Frontend against fixtures &nbsp;&nbsp;`[Claude; runs in parallel with 1a]`

- Mock API client that replays the Phase 0 fixtures.
- Setup screen, scoreboard, hand, action bar, log, drive chart.
- Flat 2-D field placeholder (a CSS strip with a ball marker).
- Animation queue with skip, speed, sound, reduced motion.

**Exit:** a full game is playable in the browser driven entirely by fixture data,
with no backend running. **Claude is not blocked on Sol at any point here.**

### Phase 2: Local browser MVP, no 3-D &nbsp;&nbsp;`[Sol builds the API, Claude integrates]`

- **Sol:** FastAPI, SQLite sessions, all six endpoints, revision guard,
  `tests/test_api.py`.
- **Claude:** swap the mock client for the real one; refresh and resume; error
  and reconnect states; one-command local run wired into `.claude/launch.json`.

**Exit:** a complete four-quarter game is playable in a browser on localhost with
zero 3-D assets. **This is the real MVP and the point where the project has
delivered value.** Everything after this is presentation.

**Handoff H3:** expect a round of contract drift fixes at integration. Budget a
session for it rather than treating it as a surprise.

### Phase 3: 3-D vertical slice &nbsp;&nbsp;`[Claude]` &nbsp;**PULL FORWARD**

> **Priority note, 2026-08-07.** Nick saw the Phase 1b HUD and expected to see a
> 3-D field with the ball moving. The flat field is a deliberate placeholder,
> but this phase should start **before** Phase 2 API integration rather than
> after. The fixtures already drive a full play loop, so the scene can be built
> with no backend. Minimum first deliverable: seven segments, a real ball mesh
> tweening between them on `ball_moved`, broadcast camera. HUD stays in HTML.

- Procedural tabletop stadium and field. No Blender (see 7.1).
- Camera director with default plus event shots.
- Animate card play, reveal, ordinary movement, touchdown.
- Verify by screenshot in both Chrome and Safari.

**Exit:** one full drive feels coherent, and every control is still easy to hit.

### Phase 4: Full event coverage &nbsp;&nbsp;`[Claude, with Sol on call for engine gaps]`

- War, joker, punt, short punt, field goal, PAT, two-point.
- Clutch and mojo effects.
- Quarter and game-end presentation.
- Low-quality graphics mode.

**Exit:** every engine event has a tested visual treatment; no outcome is an
unexplained state jump.

**Handoff H4:** when an event lacks a field needed to animate it, Claude files it
against Sol. Contract change first, then both sides.

### Phase 5 (optional, deferred): Hosting &nbsp;&nbsp;`[Claude]`

Only if we decide we want it. New Caddy block, new systemd unit, basic_auth
reusing the existing `ccf_football` credential, SQLite stored outside the release
directory. The existing pygbag site stays up as fallback until the new one is
proven.

---

## 10. Explicitly out of scope for v1

Remote human-vs-human, accounts, matchmaking, phone portrait layout, per-team
3-D models, custom stadium builder, spectator mode. The event contract, session
ids, revisions, and per-viewer redaction are designed so that adding
head-to-head later is an extension rather than a rewrite, but none of it is built
now.

---

## 11. Risks

| Risk | Mitigation |
| --- | --- |
| Refactor silently changes game behavior | Golden transcripts captured in Phase 0 *before* any change (5.3); seeding split into a provably-neutral commit A |
| Snapshot leaks the AI's hand or card | Phase-driven redacting serializers and a dedicated test file (3.1) |
| Animation and state desynchronize | Authoritative ordered events, one director, registry-coverage test |
| Two agents collide in the same files | Strict file ownership and a frozen contract (see AGENT_WORK_SPLIT.md) |
| Frontend blocked waiting on backend | Frontend builds against committed fixture payloads from day one |
| 3-D assets never get made | Procedural geometry only, no Blender dependency (7.1) |
| 3-D makes the game harder to play | All interaction stays in HTML; fixed cameras; large targets |
| Animations get tedious by game three | Skip, fast, instant, remembered preference |
| Pygame and web rules diverge | One Python engine, both editions, shared test suite |
| Breaking what the family currently uses | Local-first; the live pygbag site is never modified |

---

## 12. Acceptance criteria for v1

- A full four-quarter solo game can be started and finished in a browser on
  localhost.
- Rules and AI behavior match the Pygame edition, verified by shared fixtures.
- Every outcome is explained both visually and in text.
- Card selection and decisions work with mouse and touch.
- Refresh resumes the game from any decision phase.
- Animations can be skipped and sped up; sound can be muted; reduced motion
  works.
- No API payload contains a card the viewer is not entitled to see.
- The Pygame edition still passes its suite and is still playable.
- Runs smoothly in Safari and Chrome on the target laptop.
