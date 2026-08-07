# Implementation Plan: Splitting the Work Between Claude and GPT Sol

**Companion to:** [THREE_D_WEB_PLAN.md](THREE_D_WEB_PLAN.md)
**Date:** 2026-08-07

---

## 1. The split in one line

**Sol owns Python. Claude owns TypeScript, plus git and infra.**
They meet at one frozen JSON contract and never edit the same file.

---

## 2. Why this way round

The split is chosen for two reasons, and the second matters more than the first.

**Reason one: task shape fits each agent.**

The backend is a single language, self-contained, and has unambiguous pass/fail
criteria: pytest is green, a seed reproduces a game byte for byte, redaction
tests find no leaked cards. There is almost no aesthetic judgment once the
contract is frozen. That is the shape of work a Codex-style agent does most
reliably, because success is machine-checkable at every step and there is nothing
to have taste about.

The frontend is the opposite. R3F scene composition, camera framing, lighting for
the "premium tabletop" tone, and animation pacing all require looking at rendered
output and iterating on it. Claude Code has a browser pane, can screenshot, read
the console, and loop on the result, so the verification loop is closed without a
human in it. The git surgery in Phase 0 and any eventual VPS work also sit with
Claude, which has the workspace conventions, the deploy and vps skills, and SSH
context already loaded.

**Reason two, the real one: file ownership prevents collisions.**

Two agents editing one repo is a merge-conflict generator unless ownership is
absolute. The Python/TypeScript boundary happens to be a clean partition of the
file tree with exactly one interface between the halves. That is worth more than
any marginal skill matching.

The assignment could be reversed and would still work, but worse: Sol would be
iterating on 3-D look without a tight visual feedback loop, and Claude's context
advantage on the repo's history and the VPS would go unused.

---

## 3. File ownership

Absolute. If you need a file you do not own, ask the other agent, do not edit it.

### Sol owns

```
ccf_pygame/ccf/*.py            engine: models, deck, drive_chart, field,
                               rules, ai, state_machine, states
ccf_pygame/ccf/events.py       NEW: event dataclasses
ccf_pygame/ccf/serializers.py  NEW: redacting JSON serializers
ccf_pygame/ui/app.py           the ONE UI file Sol touches (adapter update)
ccf_pygame/test_*.py           existing engine tests
ccf_pygame/tests/              NEW: contract, redaction, transcript tests
web_api/                       NEW: entire FastAPI package
requirements-server.txt
```

### Claude owns

```
web/                           entire React + R3F app
docs/CONTRACT.md               the frozen interface spec
ccf_pygame/ui/  (except app.py)  broadcast UI
.claude/launch.json
deploy.sh, deploy/, .github/workflows/
CLAUDE.md, AGENTS.md, README.md, *_PLAN.md
git history, branches, remotes, all merges
```

### Neither owns unilaterally

```
docs/CONTRACT.md               Claude writes it; changes require both to agree
```

---

## 4. The contract is the whole interface

One document, `docs/CONTRACT.md`, defines:

- the snapshot JSON shape
- every event type and its payload fields
- the endpoint list, request and response shapes
- the redaction rules, phase by phase

**Process:**

1. Claude writes the first draft at the end of Phase 0.
2. Sol reviews it and flags anything the engine cannot cleanly produce. This
   review is required, not optional. Sol has read the state machine and will
   catch fields that are expensive or impossible to populate.
3. It freezes. Both agents code against it.
4. Any later change: update `CONTRACT.md` **first**, in its own commit, and both
   agents pull before continuing. Never change a payload shape and a consumer in
   the same commit.

`web/src/api/types.ts` is derived from the contract by Claude.
`web_api/schemas.py` is derived from the contract by Sol. Neither is the source
of truth; the document is.

---

## 5. Sequencing, and how nobody waits

Naive sequencing serializes everything: Claude does Phase 0, Sol does Phase 1,
then Claude does the frontend. That wastes most of the calendar.

The unblock is **fixtures**. At the end of Phase 0, Claude captures seeded golden
transcripts (possible today with `random.seed(N)`, see plan section 5.3) and
commits them as static JSON at `web/src/api/__fixtures__/`. Claude then builds
the entire frontend against a mock client that replays those fixtures. The real
API gets swapped in behind the same interface at Phase 2 integration.

**Consequence: Claude is never blocked on Sol after Phase 0.** The frontend is
developed and tested end to end before the backend exists.

```
Phase 0   Claude  ████  trunk merge, transcripts, contract draft
                        │
                  ┌─────┴─────┐
Phase 1   Sol     │  ████████ │  engine: pump, events, seeding, redaction
          Claude  │  ████████ │  frontend: HUD + scene, against fixtures
                  └─────┬─────┘
Phase 2   both        ████     integration: real API replaces the mock
Phase 3-4 Claude      ████████ 3-D slice, then full event coverage
                      (Sol on call for engine gaps only)
```

The one hard dependency: **Sol cannot start until Phase 0 lands**, because Phase
0 decides which branch is trunk and Sol's work would otherwise be built on the
wrong engine.

---

## 6. Sol's assignment

### Phase 1: presentation-independent engine

| # | Task | Acceptance |
| --- | --- | --- |
| 1.1 | `pump()` + `DECISION_PHASES` set | AI vs AI game plays to completion with zero frame timers; `max_steps` guard trips cleanly rather than hanging |
| 1.2 | `events.py` dataclasses for all 18 event types | Matches `CONTRACT.md` exactly; every type is JSON-round-trippable |
| 1.3 | Emit events at every transition | Test: every score, ball position, possession, mojo, and clutch delta in a full game is explained by an event. No unexplained diffs. |
| 1.4 | Seeded RNG, **commit A** (plumbing, `rng=None` default) | 59 existing tests green; golden transcripts byte-identical. Provably behavior-neutral. |
| 1.5 | Seeded RNG, **commit B** (activate per-game `Random(seed)`) | Same seed reproduces the same full game across processes |
| 1.6 | `serializers.py` with phase-driven redaction | See below. Highest-priority task in the phase. |
| 1.7 | `tests/test_redaction.py` | For every phase, no card the viewer is not entitled to see appears anywhere in the payload |
| 1.8 | Update `ui/app.py` to the new contract | Pygame plays a full game; 59 tests green |
| 1.9 | Characterization fixtures for the section 3 defects | Current behavior pinned, including the orange/green non-award |

**Task 1.6 is the one to get right.** Two known leaks, both in plan section 3.1:
`Team.hand` rides along inside the snapshot, and `_off_card` holds the AI's
offensive card while the phase is `WAITING_DEFENSE_CARD`. The serializer takes a
viewer and the phase and decides what is legal to reveal. It is not a filter
bolted on afterward.

### Phase 2: API

| # | Task | Acceptance |
| --- | --- | --- |
| 2.1 | FastAPI app, all six endpoints | Contract-conformant responses |
| 2.2 | SQLite session store | Session survives a server restart |
| 2.3 | Revision guard | A stale or replayed revision is rejected and mutates nothing |
| 2.4 | `tests/test_api.py` | Full game driven purely through HTTP |

### Standing rules for Sol

- Never edit anything under `web/`, `deploy/`, `.github/`, or the docs.
- Never change a contract payload without updating `CONTRACT.md` first, in its
  own commit.
- The 59 existing tests stay green at every single commit. If a commit needs
  them red, it is two commits.
- Do not "fix" the orange/green auto-TD (plan 3.2). Pin current behavior in a
  fixture and leave it.

---

## 7. Claude's assignment

### Phase 0: trunk and baseline

| # | Task | Acceptance |
| --- | --- | --- |
| 0.1 | Port broadcast engine + `ui/` onto `origin/main` | Four engine files and the broadcast UI land on trunk with all infra intact |
| 0.2 | Keep `dad` fetch-only for now | Nothing pushed to `sorangio/CodeDev`. A matching `web-edition` branch goes there once Phase 2 is playable (plan 1.6). Documented in CLAUDE.md. |
| 0.3 | Fix the docs symlinks | Real `CLAUDE.md`, `AGENTS.md` symlinked to it, per workspace convention |
| 0.4 | Capture seeded golden transcripts | Full games at each difficulty, committed as fixtures |
| 0.5 | Draft `docs/CONTRACT.md` | Sol reviews before freeze |
| 0.6 | Verify 59 tests green on reconciled trunk | Green |

### Phase 1 (parallel with Sol): frontend against fixtures

Mock API client replaying fixtures; setup screen; scoreboard; card hand; action
bar; game log; drive chart panel; flat 2-D field placeholder; the animation
queue with skip, speed, sound, and reduced motion.

**Acceptance:** a full game is playable in the browser driven entirely by fixture
data, with no backend running.

### Phase 2: integration

Swap the mock for the real client; refresh and resume; error and reconnect
states; one-command local run wired into `.claude/launch.json`.

**Acceptance:** a full four-quarter game against the real API on localhost. This
is the MVP.

### Phases 3 and 4: the 3-D layer

Procedural tabletop stadium, camera director, then per-event animation coverage,
then low-quality mode. Verified by screenshot in **both** Chrome and Safari.

### Standing rules for Claude

- Never edit anything under `ccf_pygame/ccf/`, `web_api/`, or `ui/app.py`.
- Rules logic never appears in TypeScript. If the frontend seems to need a rules
  decision, the event is underspecified. File it against Sol.
- Verify in real Safari, not only the Chromium preview.

---

## 8. Handoff points

Four moments where the agents actually have to talk.

| # | When | What changes hands |
| --- | --- | --- |
| **H1** | End of Phase 0 | Claude to Sol: trunk is ready, here is `CONTRACT.md` and the golden transcripts. Sol reviews the contract and either signs off or requests changes. Nothing starts until sign-off. |
| **H2** | Sol finishes 1.6 | Sol to Claude: redaction shape is settled, so `types.ts` can be finalized. This is the field list most likely to shift, so it gates the frontend's type layer specifically, not the whole frontend. |
| **H3** | Start of Phase 2 integration | Sol to Claude: API is live on `:8000`. Claude swaps the mock client. Expect a round of contract drift fixes here; budget for it. |
| **H4** | Phase 4, per event | Claude to Sol: an event lacks a field needed to animate it. Contract change first, then both sides. |

---

## 9. Prompt to hand Sol at H1

> You are working on `clutch-card-football`, a card football game. We are adding
> a browser edition with a 3-D presentation layer. Read `THREE_D_WEB_PLAN.md`
> and `AGENT_WORK_SPLIT.md` first; they are the plan of record.
>
> You own the Python side only: `ccf_pygame/ccf/`, `ccf_pygame/ui/app.py`,
> `ccf_pygame/tests/`, and the new `web_api/` package. Another agent owns
> `web/`, the docs, and all git and deploy work. Do not edit their files.
>
> `docs/CONTRACT.md` is the frozen interface between us. Review it before you
> start and flag anything the engine cannot cleanly produce. After it is frozen,
> any change to it is its own commit, made before any consumer changes.
>
> Your work is Phase 1 and Phase 2 of section 6 in `AGENT_WORK_SPLIT.md`.
> Start with 1.6, the redacting serializers, because plan section 3.1 documents
> two live hidden-information leaks and everything else depends on that shape.
>
> Hard constraints:
> - `cd ccf_pygame && python3 -m pytest test_ai.py test_ui.py` must report 59
>   passed at every commit. If a change needs them red, split it into two commits.
> - The Pygame edition stays playable. It shares the engine.
> - Do not fix the orange/green auto-touchdown gap in plan section 3.2. It is a
>   deliberate open question for the humans. Pin the current behavior in a fixture.
> - Conventional commits, subject under 72 chars.

---

## 10. What to watch for

- **Contract drift at H3 is the likeliest source of lost time.** Both agents will
  have made small independent assumptions. Budget a session for reconciliation
  rather than treating it as a surprise.
- **Sol touching `ui/app.py` is the only ownership overlap.** It is unavoidable,
  since the adapter must follow the engine. Claude should not edit that file for
  the duration of Phase 1.
- **If Sol finishes Phase 1 early**, the useful next task is expanding engine test
  coverage from plan section 8, not starting on the API ahead of the contract
  freeze.
- **The orange/green question (plan 3.2) needs a human answer** before the game is
  considered rules-complete. It does not block any phase, but it should not be
  forgotten either.
