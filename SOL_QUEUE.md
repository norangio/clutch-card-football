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

From plan section 8, anything not yet covered: color bonuses as implemented
after task 5, both joker directions across all value ranges, war both outcomes,
field goals made and missed at each of Z1/Z2/Z3, clutch including the
joker-clutch path, mojo accumulation and conversion, quarter dealing and
possession handoff, empty-deck fallbacks.

### 10. A generated fixture dump for the frontend

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
