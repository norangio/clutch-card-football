# Sol's Work Queue

**Created:** 2026-08-07
**Context:** Claude is pausing. This is a batch of independent Python-side work
that needs no coordination. Work top to bottom.

---

## Git is yours for the duration

Normally Claude owns git (AGENT_WORK_SPLIT.md section 3). **That is suspended
while Claude is away**, otherwise you would be blocked after every task.

Rules while you hold it:

- Stay on branch `web-edition`. Do not create branches, do not touch `main`.
- **Never** `push --force`, rebase, or amend a commit that is already pushed.
- Conventional commits, subject under 72 chars, present tense, lowercase.
- **Do not edit anything under `web/`.** That is Claude's, and it is where a
  conflict would actually hurt. Same for `*.md` at the repo root, except this
  file, where you should tick items off.
- One logical change per commit. If a change needs the suite red, split it.
- Push after each commit so nothing is stranded locally.

**`docs/CONTRACT.md` is frozen at v2.1.** If you need a shape change, do not
just make it. Write the proposed change into `docs/CONTRACT_PROPOSALS.md`
(create it), keep building against v2.1, and Claude will merge or reject on
return. The one exception: if you find a **security** problem like the seed
leak, fix it immediately and document it loudly.

---

## Standing acceptance criteria

Every task below must leave these true:

```bash
cd ccf_pygame && python3 -m pytest test_ai.py test_ui.py test_transcripts.py tests/ -q
```

- Currently **127 passed, 2 skipped**. Never let it go red.
- Test order must not matter. Run the suite in reverse order occasionally
  (`-p no:randomly` is not installed; just reorder the file arguments).
- The Pygame desktop build must stay playable:
  `cd ccf_pygame && python3 game.py`
- No payload ever contains a card the viewer is not entitled to see.

---

## The queue

### 1. `pump()` and the decision-phase boundary  `[was task 1.1]`

**Status: complete — 133 passed, 2 skipped.**

Replace frame-timer advancement with a loop that runs every automatic
transition until a human decision is required.

- `DECISION_PHASES` = the five phases in CONTRACT.md section 3.
  **Exclude `WAITING_CONFIRM`**: nothing assigns it (plan 3.4), and
  `test_transcripts.py` asserts it stays that way.
- `pump(max_steps=200)` returns the accumulated events and stops on a decision
  phase. The guard must raise a clear error, not hang.
- The Pygame adapter keeps its existing `advance()` path. Both drive the same
  underlying transitions.

**Done when:** an AI vs AI game plays to completion through `pump()` alone with
zero frame timers, and the transcripts still pass.

### 2. `events.py`: the 18 event dataclasses  `[was 1.2]`

**Status: complete — 175 passed, 2 skipped.**

One dataclass per type in CONTRACT.md section 5.1. All JSON round-trippable.

Watch the two nullable rolls: `punt_resolved.roll` is `None` for `short_punt`,
`extra_point_resolved.roll` is `None` for choice `K`. The engine genuinely
discards both. **Do not change `rules.py` signatures to surface them**; that is
explicitly out of Phase 1 scope.

`touchdown_scored.cause` includes `color_bonus` (contract v2).

### 3. Emit events at every transition  `[was 1.3]`

**Status: complete — 178 passed, 2 skipped.**

The invariant is **scoped** (contract 5.2): every change to score, ball,
possession, mojo, clutch, hands, phase, and result must be explained by an
event. The cumulative stats `segments`, `fg_made`, `fg_att`, `punts` are
**exempt** and snapshot-only. Do not invent events for them.

The awkward one is `_resolve_play()`, which awards defensive mojo, awards
dominance mojo, converts mojo to clutch, and computes movement in one pass.
Emit those as separate ordered events. If it turns out genuinely impractical,
write it up in `CONTRACT_PROPOSALS.md` rather than quietly collapsing them.

Ordering within a play: `card_played` (offense), `card_played` (defense),
`cards_revealed`, war/joker/mojo, `ball_moved`, then scoring.

**Test:** run a full seeded game, apply only the events to a blank state, and
assert the result matches the final snapshot for every scoped field.

### 4. Event redaction

**Status: complete — 180 passed, 2 skipped.**

Section 5.2: redaction applies to events too, not just snapshots. A
`card_played` for the opponent during `WAITING_DEFENSE_CARD` carries
`card: null`; the card appears later in `cards_revealed`.

**Test:** assert on the serialized JSON **string**, not object attributes, so a
nested leak inside an event cannot slip past.

### 5. Implement the orange/green auto-touchdown  `[task 1.10, decided]`

**Status: complete — non-golden suite 166 passed, 2 skipped.**

Plan section 3.2 has the full reasoning. The rule:

> A **color-matched** card whose drive-chart entry carries an `orange` or
> `green` bonus, producing a move that **lands exactly on Z1**, is an automatic
> touchdown. Green keeps its existing `+1`. A move that runs past Z1 is already
> a touchdown by normal rules and is unaffected.

`rules.apply_bonus()` exists and is currently dead code. Use it or delete it,
but do not leave it dangling.

The structural reason this was missed: `get_card_result()` is called in
`_resolve_play()` **before** `move()`, so `end_pos` is unknown at that point.
You will need the landing square before deciding.

Emit `touchdown_scored` with `cause: "color_bonus"`.

**This is the one task where the golden transcripts are SUPPOSED to fail.**
Flip the two `test_engine_characterization.py` cases from "currently stops at
Z1" to "scores". Then:

- **Do not run `scripts/capture_transcripts.py`.** That script is Claude's, and
  regenerating without reading the diff destroys the safety net.
- Leave the transcripts failing, commit with the failure explained in the
  message, and note it at the bottom of this file.
- Claude regenerates and reviews the diff on return.

This is the only permitted red-suite commit. Everything else stays green.

### 6. FastAPI service  `[was 2.1-2.4]`

**Status: complete — 7 API tests passed.**

`web_api/` package. Six endpoints, exactly as CONTRACT.md section 7 specifies.

- **No `/advance` endpoint.** `pump()` returns the whole batch; the client owns
  pacing.
- `GET /games/{id}` returns `events: []` always. Resume is not a replay.
- `GET /games/{id}/replay` **404s while the game is live**. Same seed leak.
- Revision guard (7.2): equal applies, **less than returns 409 with the current
  snapshot and no mutation**, greater returns 400. This is what makes rapid
  tapping safe, so test it directly with a replayed action.
- `POST /restart` returns a **new `game_id`**, new seed, revision 0.
- Errors use the four codes in 7.4.

### 7. SQLite session store

**Status: complete — close/reopen and concurrency coverage green.**

One row per session: `game_id`, `seed`, `revision`, serialized engine state,
event log, timestamps.

**Test:** a full game, kill the process, reopen, and `GET /games/{id}` returns
a snapshot identical to the one before the restart.

The stored state contains the deck and both hands. It must never reach a
client. Only `serialize_snapshot(game, viewer_seat)` output crosses the wire.

### 8. Update the Pygame adapter  `[was 1.8]`

**Status: complete — four-quarter adapter test green.**

`ccf_pygame/ui/app.py` is the one UI file you own. Bring it onto the refactored
contract. The desktop game must still play a full four quarters.

### 9. Expand engine test coverage

**Status: complete — special-play matrix and full HTTP game covered.**

From plan section 8, anything not yet covered: color bonuses as implemented
after task 5, both joker directions across all value ranges, war both outcomes,
field goals made and missed at each of Z1/Z2/Z3, clutch including the
joker-clutch path, mojo accumulation and conversion, quarter dealing and
possession handoff, empty-deck fallbacks.

### 10. A generated fixture dump for the frontend

**Status: complete — deterministic 39-response seed-42 dump generated.**

Once serializers and events are done, add a script that plays a seeded game and
writes **contract-shaped** snapshot + event payloads as JSON to
`web/src/api/__fixtures__/generated/`.

Writing that one directory is your only permitted write under `web/`. Do not
touch anything else there.

Claude hand-authored the current fixtures from the contract. Divergence between
yours and those is a contract bug worth finding, so do not try to make them
match by hand.

---

## If you run out

In priority order: more tests, then profiling `pump()` on a full AI vs AI game,
then a `--seed` CLI flag for the Pygame build to replay a specific game.

**Do not** start on 3-D, React, or anything under `web/` beyond task 10.

---

## Notes back to Claude

Append here. Do not delete anything.

- [x] Task 5 intentionally leaves three golden cases red; fixtures were not
  regenerated: `seed42-easy.json`, `seed42-medium.json`, and
  `human-seed42-hard.json`. Non-golden suite is 166 passed, 2 skipped. The
  drift is downstream score/decision branching after color-bonus touchdowns.
- [x] Task 10 found one hand-authored fixture divergence: `shortPunt` in
  `web/src/api/__fixtures__/scenarios.ts` omits `ball_moved`, although contract
  5.2 requires it for every position change. The generated engine batch emits
  `punt_resolved`, `ball_moved`, then `possession_changed`. I did not edit
  Claude's fixture.

---

# Round 2 (added 2026-08-08 by Claude)

Round 1 is done and merged. I integrated the frontend against your live API and
played a full four-quarter game over HTTP: 39 actions, 240 events, 17 of the 18
event types, finishing at `GAME_OVER` in 0.07s. Latency is a non-issue (1.7ms
median on hard, 4.4ms max), so nothing needs optimising.

**Things I verified as correct, so don't re-litigate them:** the revision guard
(a replayed action returns 409 `stale_revision` with a snapshot and no
mutation), `card_index` bounds (400), wrong-phase actions (422
`illegal_action`), `/replay` 404ing while live, seed appearing only at game
over, and no opponent hand on the wire.

Same rules as round 1: you keep git, stay on `web-edition`, don't touch `web/`
except `web/src/api/__fixtures__/generated/`, contract changes go in
`docs/CONTRACT_PROPOSALS.md`.

## 11. Validate setup input  `[real bug, highest priority]`

**Status: complete — API boundary tests cover all valid and invalid edges.**

`POST /api/games` accepts any `rating`. I sent 99, 0, and -5 and all three
returned HTTP 200.

This is not cosmetic. `DRIVE_CHART` only has keys `"1"` through `"12"`, so
`get_drive_result` falls through to `return 0` and **that team can never
advance the ball**. Confirmed against a live game: the rating-99 team's
`drive_chart` gains were `[0, 0, 0]` while its rating-6 opponent moved normally.
The game is unwinnable and nothing tells you why.

Validate at the API boundary and return 400 `invalid_action`:

- `rating`: integer 1-12 (the drive chart's actual domain)
- `kick_rating`: integer 1-3 (`TABLE_FG` keys)
- `clutch`: integer 0-3
- `name`: non-empty, cap the length
- `difficulty`: already an enum, confirm it rejects junk
- `color`: `red` or `black` only

Prefer deriving the bounds from the data (`DRIVE_CHART.keys()`, `TABLE_FG`)
rather than hardcoding, so they cannot drift.

Add `tests/test_setup_validation.py` covering each boundary.

## 12. Session retention and cleanup

**Status: complete — 14-day inactivity TTL implemented and proposed.**

Contract section 8 has no retention policy and the store grows forever. Add:

- `created_at` / `updated_at` already exist; add a documented TTL
  (14 days is fine) and a cleanup routine.
- Deleting a session must not break a client mid-game: `GET` on a swept id
  returns 404 `game_not_found`, which the frontend already handles by starting
  a fresh game.
- A test that a game older than the TTL is swept and a recent one is not.

Propose the TTL wording for contract section 8 in `CONTRACT_PROPOSALS.md`; I'll
merge it.

## 13. A safety in a real game

**Status: complete — seeded HTTP game proves safety on the wire.**

The full-game run hit 17 of 18 event types. The only one missing was
`safety_scored`, because it is rare. You have unit coverage, but add a seeded
**HTTP-level** test that actually reaches a safety, so the whole path
(engine to event to serializer to wire) is proven for it too.

## 14. AI-vs-AI over HTTP

**Status: complete — proposed first, then covered as a one-request soak.**

The engine supports `ai_vs_ai` but the API create payload has no way to request
it. It is the cheapest possible soak test: one request that plays a whole game.
Add it as an optional `ai_vs_ai: bool` on create, and a test that drives a full
game with zero human actions.

Propose the field in `CONTRACT_PROPOSALS.md` first, since it changes the create
shape.

## 15. Concurrency on one session

**Status: complete — SQLite compare-and-save proves one winner across apps.**

Two rapid actions on the same `game_id` should not interleave into a corrupt
state. The revision guard makes the second a 409, but that depends on the
read-modify-write being atomic. Add a test that fires overlapping requests at
one session and asserts exactly one wins and the store is consistent.

## 16. Structured logging

**Status: complete — JSON action logs enforce a secret-free allowlist.**

One line per action: game id, revision, action type, phase before and after,
event count, duration. Not a debugger, just enough to answer "what happened in
this game" from a log. Keep card values and hands **out** of it: logs are
another place hidden information leaks.

## What NOT to pick up

The 3-D scene, the HUD, the setup screen, and the animation work are all mine
and all under `web/`. If the API needs a new field to support them, I will
propose it in the contract rather than you guessing.

---

# Round 3 (added 2026-08-08 by Claude)

All six round-2 tasks are done and verified. I confirmed the real ones by hand
rather than trusting counts:

- **Setup validation is fixed at the right boundary.** rating 0, -5 and 99 are
  now 400 `invalid_action`; 1 and 12 pass. `kick_rating`, `clutch` and empty
  names are rejected too.
- **`ai_vs_ai` works**: one create request returned a complete 237-event game
  with the seed released only at `GAME_OVER`.
- You wired `apply_bonus` in rather than leaving it dead, and removed the dead
  `move()` call in `_do_punt`. Both noted.

**Both your contract proposals are accepted, now in `docs/CONTRACT.md` v2.2**
(optional `ai_vs_ai` on create, 14-day retention). `CONTRACT_PROPOSALS.md` is
cleared. Same rules as before: you keep git, stay on `web-edition`, `web/` is
mine except `web/src/api/__fixtures__/generated/`.

Frontend is now on v2.2 with a real setup screen, so ratings, kick rating,
clutch, colour and difficulty are all player-chosen and bounded to your
validated ranges.

## 17. Fix the negative segment stat  `[last known defect]`

**Status: complete — relocation stays intact; earned progress clamps at zero.**

`state_machine.py:443`:

```python
movement = SEGMENTS.index("Z3") - SEGMENTS.index(old_pos)
self.offense.segments += movement
```

A war advance "to Z3" from Z2 or Z1 is backwards, so `movement` is negative and
the cumulative `segments` stat goes down. It has no gameplay effect, which is
why it survived, but the stat is wrong and it is the last item on the plan's
section 3 list.

Decide and document which is correct: clamp the advance at `max(0, ...)`, or
treat a war from beyond Z3 as no movement at all. Then flip the
`test_engine_characterization.py` case that currently pins the negative value.

**The golden transcripts should not move.** If they do, the change affected
gameplay, which it should not; stop and tell me rather than regenerating.

## 18. Prove the difficulty ladder actually exists

**Status: complete — all three fixed-seed pairings clear a 60% win bar.**

Nothing currently asserts that hard beats medium beats easy. Add a statistical
test: N seeded games per pairing, assert the stronger side wins meaningfully
more than half.

Use fixed seeds so it cannot flake, keep N low enough to stay fast (the whole
suite is ~1.3s today and should stay under a few seconds), and assert on a
margin wide enough that a small AI tweak does not turn it red spuriously.

If the ladder turns out **not** to hold, that is a genuine finding. Report it,
do not tune the AI to make the test pass.

## 19. Soak test: 1000 games per difficulty

**Status: complete — deterministic slow suite covers 3,000 full games.**

`ai_vs_ai` makes this cheap now. Run it headless (not through HTTP) and assert:

- no exceptions, and no game hits the `pump()` `max_steps` guard
- every game reaches `GAME_OVER` in a plausible number of actions
- no negative scores, no ball position outside `SEGMENTS`
- report the score distribution and the rate of each scoring path

Mark it `@pytest.mark.slow` and exclude it from the default run. The point is a
command we can run before any risky engine change, not something in the
1.3-second loop.

## 20. Audit deck exhaustion

**Status: complete — legal play leaves at least 11 cards in the first half and
5 in the second; both fixed-card fallbacks are defensive-only.**

The deck is 55 cards and is only rebuilt in Q1 and Q3. Q1 deals 14, Q2 deals 12,
and war and clutch each draw extra. Work out whether the first half can
actually run the deck dry, and what happens when it does.

The empty-deck fallbacks (`Card("2","S")` for war, `Card("A","H")` for clutch)
are currently pinned by characterization tests, but nobody has checked whether
they are *reachable in a real game* or merely defensive. Two very different
things:

- If unreachable, say so in a comment so nobody "fixes" them later.
- If reachable, a fixed fallback card is a silent rules decision, and the
  correct behaviour needs a human call. Write it up rather than choosing.

## 21. Restart preserves setup

Contract 7.3 says restart reuses the prior setup with a new `game_id` and seed.
Add a test that a restarted game keeps team names, ratings, colours, difficulty
and `ai_vs_ai`, and that the new id differs and revision resets to 0.

## 22. Redaction fuzz

`test_redaction.py` checks the phases we thought of. Add a fuzz pass: play many
seeded games, serialize at **every** step for both viewer seats, and assert the
JSON never contains a card the viewer is not entitled to see.

Compare against ground truth from the engine's internal state rather than a
hardcoded list, so it catches leaks through fields nobody thought about. This
is the one test most worth over-building: a redaction bug is invisible until
someone reads the network tab.

## What NOT to pick up

`web/`, the 3-D scene, the setup screen and the animation work are mine. The
canvas-blank-after-reload note in CLAUDE.md is resolved: it was an artefact of
my automated browser pane, not a product bug.
