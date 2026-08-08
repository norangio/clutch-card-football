# CCF Web Edition: Interface Contract

**Status:** FROZEN. Handoff H1 complete.
**Version:** 2.1
**Owner:** Claude drafts, Sol reviews, then both code against it.

This is the only interface between the Python engine and the browser. Once
frozen, changing anything here is **its own commit, merged before any consumer
changes**. Never change a payload shape and a consumer in the same commit.

---

## 0. Review outcome (H1)

Sol raised eight issues against v0. All eight were valid and all are fixed here.
Recorded because several are non-obvious and worth not re-litigating.

| # | Issue | Resolution |
| --- | --- | --- |
| 1 | **`seed` in an active snapshot reconstructs the whole deck** | Fixed, 4.1. The most serious finding. |
| 2 | `field_goal_resolved` lacked `score_after` | Fixed, 5.1. It violated my own rule in 5.2. |
| 3 | `possession_changed.reason` undefined | Enumerated, 5.1. |
| 4 | "every mutation is event-explained" was unachievable | Invariant scoped, 5.2. |
| 5 | Short punt has no roll to report | `roll` nullable, 5.1. |
| 6 | PAT kick discards its roll | `roll` nullable, 5.1. |
| 7 | Clutch card visibility was ambiguous | Clarified, 6. |
| 8 | Restart's id/revision behavior undefined | Specified, 7.3. |

**On issue 1.** `create_deck()` shuffles a fixed, publicly known starting order.
Given the seed, `random.Random(seed).shuffle(...)` reproduces the deck exactly:
verified, `Random(42)` yields `9S 7C AD 4C 6H 7H AS JOKER ...` every time. Since
hands are dealt off the top, a client with the seed can compute the AI's entire
hand and every future draw. That is a total information leak and it defeats the
entire redaction design in section 6. The repo is public, so the deck algorithm
is not a secret either.

**On issue 4.** The engine mutates cumulative stats (`segments`, `fg_made`,
`fg_att`, `punts`) with no natural event boundary. Rather than invent events
nobody animates, the invariant now covers presentation-relevant state only.

---

## 1. Conventions

- All payloads are JSON. `snake_case` keys. No `null` where a field can be
  omitted; prefer explicit `null` only where "absent" is meaningful (an
  unrevealed card).
- Times are irrelevant here; the server never sends timestamps.
- **Seats are stable for the whole game.** `"home"` is the human's team,
  `"away"` is the AI's. Possession moves between them; the seat labels do not.
  This is deliberate: it is what lets remote two-player work later without a
  contract change.
- The engine's internal `human`/`ai` map to `home`/`away` respectively.

---

## 2. Core types

### 2.1 Card

```json
{ "id": "AH", "value": "A", "suit": "H", "color": "red", "display": "A♥" }
```

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | `"{value}{suit}"`, or `"JOKER"`. **Not unique** across a game; three jokers share `"JOKER"`. Use array index for animation keys, not this. |
| `value` | string | `2`-`10`, `J`, `Q`, `K`, `A`, `Joker` |
| `suit` | string \| null | `H` `D` `S` `C`, `null` for Joker |
| `color` | string \| null | `"red"` \| `"black"`, `null` for Joker |
| `display` | string | Pre-rendered face, e.g. `"A♥"` or `"JOKER"` |

A card the viewer is not entitled to see is `null`, never a redacted object.
The frontend renders `null` as a face-down card.

### 2.2 Seat

```json
{
  "seat": "home",
  "name": "Wolverines",
  "color": "red",
  "rating": 7,
  "kick_rating": 2,
  "score": 14,
  "mojo": 1,
  "clutch": 2,
  "clutch_used": false,
  "hand": [ ],
  "hand_count": 6,
  "segments": 18,
  "fg_made": 1,
  "fg_att": 2,
  "punts": 3
}
```

`hand` is **present only for the viewer's own seat**. For the opponent it is
omitted entirely and only `hand_count` is sent. See section 6.

### 2.3 Field position

`"0" | "1" | "2" | "3" | "Z3" | "Z2" | "Z1"`, matching `ccf/field.py:SEGMENTS`.
Index 0 is unused in normal play. `Z1` is nearest the offense's end zone.

---

## 3. Phases and required actions

`WAITING_CONFIRM` is **excluded**: nothing in the engine assigns it (plan
section 3.4). Do not include it in `DECISION_PHASES` and do not define a
`confirm` action.

| Engine phase | `required_action` | Whose turn |
| --- | --- | --- |
| `WAITING_OFFENSE_CARD` | `play_card` | offense seat |
| `WAITING_DEFENSE_CARD` | `play_card` | defense seat |
| `WAITING_POST_MOVE` | `post_move` | offense seat |
| `WAITING_EXTRA_POINT_CHOICE` | `extra_point` | scoring seat |
| `GAME_OVER` | `none` | nobody |

Every other phase is transient: `pump()` runs through it and emits events. The
client never sees a snapshot resting in one.

---

## 4. Snapshot

Returned by every endpoint. Represents state **after** all events in the same
response have been applied. The client renders the events, then reconciles to
this.

```json
{
  "game_id": "b3f1c9e2",
  "revision": 13,
  "phase": "WAITING_POST_MOVE",
  "required_action": "post_move",
  "acting_seat": "home",
  "viewer_seat": "home",

  "quarter": 2,
  "play": 3,
  "plays_in_quarter": 6,

  "ball": "Z2",
  "offense_seat": "home",
  "defense_seat": "away",

  "home": { },
  "away": { },

  "play_cards": {
    "offense": { "id": "AH" },
    "defense": null,
    "war": null,
    "clutch": null
  },

  "legal_actions": [
    { "type": "post_move", "choice": "F", "enabled": true },
    { "type": "post_move", "choice": "C", "enabled": false,
      "disabled_reason": "no_clutch_remaining" }
  ],

  "log": [ ],
  "message": "Moved from 2 -> Z2 (+2 segments)",
  "result": null
}
```

### 4.1 Identity and sync

| Field | Type | Notes |
| --- | --- | --- |
| `game_id` | string | Opaque. Stored in browser local storage. |
| `revision` | int | Monotonic. Increments once per accepted action. |
| `seed` | int \| **absent** | **Present only once `result` is non-null.** See below. |

**`seed` must never appear while the game is live.** `create_deck()` shuffles a
fixed, publicly known starting order, so `random.Random(seed).shuffle(...)`
reproduces the deck exactly. Hands are dealt off the top, so a client holding the
seed can compute the AI's entire hand and every future draw. It would defeat
every rule in section 6. The repo is public, so the shuffle algorithm is not a
secret either.

Once `result` is non-null the game is decided and the seed is safe to send,
which is what makes a shareable replay link possible.

### 4.2 Flow

`phase` is the engine phase name verbatim. `required_action` is one of
`play_card`, `post_move`, `extra_point`, `none`. `acting_seat` is who must act,
or `null` when `required_action` is `none`. `viewer_seat` is who this payload
was rendered for; the frontend uses it to decide which side is "you".

### 4.3 `play_cards`

Cards revealed **so far this play**, subject to redaction. `null` means either
not yet played or not yet legal for this viewer to see. The frontend must not
distinguish these; both render face-down.

### 4.4 `legal_actions`

Every action the engine could accept in this phase, each with `enabled` and, when
disabled, a machine-readable `disabled_reason`. The frontend renders disabled
buttons rather than hiding them, so the player learns the rules.

For `required_action: "post_move"`:

| `choice` | Meaning | Proposed `disabled_reason` when unavailable |
| --- | --- | --- |
| `P` | Punt | always enabled |
| `F` | Field goal | `not_in_field_goal_range` (ball not in Z1/Z2/Z3) |
| `C` | Clutch | `no_clutch_remaining` or `clutch_already_used_this_play` |
| `S` | Short punt | `not_in_field_goal_range` |

For `required_action: "play_card"`, one entry per card index in the viewer's
hand, all enabled. For `extra_point`, `K` and `2`, both enabled.

Verified against `_post_move_options()`: `F` and `S` both gate on
`pos in ("Z1","Z2","Z3")`, `C` on `clutch > 0 and not clutch_used`, `P` is
unconditional.

### 4.5 `result`

`null` until the game ends, then:

```json
{ "winner": "home", "home_score": 28, "away_score": 21, "is_tie": false }
```

---

## 5. Events

Ordered array. The frontend plays them in sequence, then reconciles to the
snapshot.

**The invariant, scoped.** Every change to *presentation-relevant* state must be
explained by an event, and the frontend never diffs snapshots to infer what
happened. Presentation-relevant means: score, ball position, possession, mojo,
clutch, hand contents and counts, phase, and game result.

**Explicitly exempt:** the cumulative stats `segments`, `fg_made`, `fg_att`, and
`punts`. The engine mutates these inline with no natural event boundary, and
nothing animates them. They are snapshot-only; read them from the seat object.
Inventing events for them would add work with no consumer.

Common envelope:

```json
{ "seq": 0, "type": "ball_moved", "...type-specific fields": null }
```

`seq` is the index within this response, starting at 0.

### 5.1 Catalog

| Type | Fields |
| --- | --- |
| `quarter_started` | `quarter`, `offense_seat`, `dealt` (cards per hand), `ball` |
| `card_played` | `seat`, `role` (`offense`\|`defense`), `card` (nullable), `hand_count_after` |
| `cards_revealed` | `offense_card`, `defense_card`, `offense_value`, `defense_value`, `winner` (`offense`\|`defense`\|`tie`) |
| `war_started` | `tied_value` |
| `war_card_revealed` | `card`, `matches_offense_color`, `outcome` (`advance`\|`turnover`) |
| `joker_resolved` | `played_by` (`offense`\|`defense`), `opposing_value`, `outcome` (`touchdown`\|`turnover_z3`\|`no_gain`\|`advance_3`\|`advance_1`) |
| `ball_moved` | `seat`, `from`, `to`, `segments`, `reason` (`drive_chart`\|`joker`\|`clutch`\|`punt`\|`short_punt`\|`war`\|`turnover`\|`kickoff`), `is_touchdown`, `is_safety` |
| `mojo_changed` | `seat`, `from`, `to`, `reason` (`won_card_battle`\|`dominant_win`) |
| `mojo_converted_to_clutch` | `seat`, `clutch_after`, `trigger` (`pre_play`\|`clutch_spend`) |
| `clutch_used` | `seat`, `clutch_after`, `card` |
| `possession_changed` | `from_seat`, `to_seat`, `ball`, `reason` (`punt`\|`short_punt`\|`field_goal_made`\|`field_goal_missed`\|`war_turnover`\|`joker_turnover`\|`touchdown`\|`safety`\|`quarter_start`) |
| `punt_resolved` | `seat`, `kind` (`punt`\|`short_punt`), `distance`, `roll` (**null for `short_punt`**), `from`, `to`, `clamped` |
| `field_goal_resolved` | `seat`, `success`, `roll`, `total`, `target`, `from`, `points`, `score_after` |
| `touchdown_scored` | `seat`, `points`, `score_after`, `cause` (`drive`\|`joker`\|`clutch`\|`defensive_joker`\|`color_bonus`) |
| `safety_scored` | `seat` (the seat **awarded** the 2), `points`, `score_after` |
| `extra_point_resolved` | `seat`, `choice` (`K`\|`2`), `success`, `roll` (**null when `choice` is `K`**), `points`, `score_after` |
| `quarter_ended` | `quarter`, `home_score`, `away_score` |
| `game_ended` | `winner`, `home_score`, `away_score`, `is_tie` |

### 5.2 Rules

- **Redaction applies to events too.** A `card_played` for the opponent during
  `WAITING_DEFENSE_CARD` carries `card: null`. The card appears in the later
  `cards_revealed`.
- `ball_moved` is emitted for every position change including punts and
  turnovers, so the frontend has exactly one animation path for the ball.
  `punt_resolved` carries the dice detail; `ball_moved` carries the motion.
- Ordering within a play: `card_played` (offense), `card_played` (defense),
  `cards_revealed`, then any of war/joker/mojo, then `ball_moved`, then scoring.
- An event that changes a score must carry `score_after`, so the HUD never has
  to wait for the snapshot. That includes `field_goal_resolved`.
- **Two rolls are unavailable and are `null` by contract**, not by oversight.
  `short_punt_distance()` folds its `randint(0, 2)` straight into the returned
  distance, and `pat_kick()` discards its `randint(1, 6)` entirely. Surfacing
  them would mean changing those return signatures. That is a behavior-neutral
  change and can happen later if we want dice animations on those two plays, but
  it is **not** in Phase 1 scope. The frontend must render both without a die.

### 5.3 Known engine wrinkle

`_resolve_play()` awards defensive mojo, offensive dominance mojo, converts mojo
to clutch, and computes movement in one pass. Emit these as **separate ordered
events** (`mojo_changed`, `mojo_converted_to_clutch`, `ball_moved`) even though
the engine does them together. If that is impractical, raise it in review.

---

## 6. Redaction (security critical)

The engine has two live leaks (plan section 3.1), both characterized in
`ccf_pygame/tests/test_engine_characterization.py`. The serializer is
**viewer-scoped by construction**, not a filter applied afterward.

`serialize_snapshot(game, viewer_seat)` decides visibility from `(viewer_seat,
phase)`:

| Data | Visible to viewer |
| --- | --- |
| Own hand | always |
| Opponent hand | **never**. Only `hand_count`. |
| Own played card | once played |
| Opponent's played card | **only from `SHOWING_CARD_BATTLE` onward**, never during `WAITING_DEFENSE_CARD` |
| War card | from `SHOWING_WAR` onward |
| Clutch card | from `SHOWING_CLUTCH` onward, visible to **both** seats. It is drawn and immediately revealed, so there is no hidden window. |
| Deck contents | **never**, in any phase |
| Deck count | allowed |
| `seed` | **only once the game is over** (`result` non-null). See 4.1: it reconstructs the deck. |

**The `WAITING_DEFENSE_CARD` case is the important one.** The AI plays offense
first, so `_off_card` is set while the human is still choosing their defense. The
Pygame UI hides this by convention (it draws `"AI plays card ..."`). An HTTP
payload has no such convention. Leaking it hands the human a guaranteed win.

Required test: for every phase, assert no card the viewer is not entitled to see
appears **anywhere** in the serialized payload, including inside events. Assert
on the serialized JSON string, not on object attributes, so a nested leak cannot
slip through.

---

## 7. Endpoints

Base path `/api`. All responses are `{ revision, snapshot, events }` unless
noted.

| Method | Path | Body | Notes |
| --- | --- | --- | --- |
| `POST` | `/games` | setup | Creates a game. `events` covers dealing and quarter start. |
| `GET` | `/games/{id}` | | Resume. **`events` is always `[]`**; the snapshot is fully applied. |
| `POST` | `/games/{id}/actions` | action | The main endpoint. |
| `POST` | `/games/{id}/restart` | | New game, same setup. **Returns a new `game_id`.** See 7.3. |
| `GET` | `/games/{id}/replay` | | `{ seed, events: [...] }`. **404 while the game is live**; only available once `result` is non-null. Same seed leak as 4.1. |
| `GET` | `/healthz` | | `{ "status": "ok" }`. Not under `/api`. |

There is deliberately **no `/advance`**. `pump()` runs every automatic transition
server-side and returns the whole batch. The client owns pacing.

### 7.1 Create

```json
{
  "home": { "name": "Wolverines", "rating": 7, "kick_rating": 2,
            "color": "red", "clutch": 2 },
  "away": { "name": "Buckeyes", "rating": 6, "kick_rating": 2, "clutch": 2 },
  "difficulty": "hard",
  "seed": null
}
```

`away.color` is derived (the opposite of `home.color`); the engine only supports
red and black.

`seed: null` means the server **picks one and stores it**. It is *not* returned.
That would contradict 4.1 on the very first response and hand the client the
whole deck before the first card is played. The seed surfaces only once `result`
is non-null. A caller that passes an explicit `seed` obviously already knows it;
that is a debugging affordance, not a leak the server created.

### 7.2 Action

```json
{ "revision": 12, "type": "play_card", "card_index": 3 }
{ "revision": 12, "type": "post_move", "choice": "F" }
{ "revision": 12, "type": "extra_point", "choice": "2" }
```

`revision` is the client's last known value.

- Matches server revision → apply, pump, return `revision + 1`.
- **Less than** server revision → the client is behind, usually a double-submit
  or a retry. Return **`409`** with the current snapshot and `events: []`. Do
  not mutate. The client reconciles silently.
- Greater than server revision → `400`, client is impossible/corrupt.

This is what makes rapid tapping safe.

### 7.3 Restart

`POST /games/{id}/restart` **creates a new game and returns a new `game_id`**,
with a new seed and `revision` reset to 0. It does not reuse or reset the
existing game.

Rationale: reusing the id with a rewound revision is indistinguishable, from the
client's point of view, from a stale-revision conflict, and it would make the
409 rule in 7.2 ambiguous. A fresh id is unambiguous. The finished game also
stays intact for `/replay`.

The client must overwrite its stored `game_id` with the returned one. The old
game is left to normal expiry.

### 7.4 Errors

```json
{ "error": { "code": "illegal_action", "message": "...", "revision": 13 } }
```

| Code | HTTP | When |
| --- | --- | --- |
| `game_not_found` | 404 | Unknown or expired `game_id` |
| `stale_revision` | 409 | Client behind; snapshot included |
| `illegal_action` | 422 | Action not legal in this phase |
| `invalid_action` | 400 | Malformed, or `card_index` out of range |

---

## 8. Persistence

SQLite, one row per session: `game_id`, `seed`, `revision`, serialized engine
state, event log, `created_at`, `updated_at`.

Requirement: a server restart mid-game loses nothing. `GET /games/{id}` after a
restart returns a snapshot identical to the one before it.

The stored engine state contains the deck and both hands. It is **never** sent
to a client. Only `serialize_snapshot(game, viewer_seat)` output crosses the
wire.

---

## 9. Deferred

Not in v1, but the contract does not preclude them: remote two-player (seats and
per-viewer redaction already exist), spectator view (a viewer entitled to no
hand), WebSocket push (same payloads, different transport).

---

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 2.1 | 2026-08-07 | Fixes a self-contradiction Sol caught: 7.1 said a generated seed was "returned" at creation, which 4.1 forbids. Now "picked and stored". Wording only, no shape change. |
| 2 | 2026-08-07 | Adds `color_bonus` to `touchdown_scored.cause`. The orange/green auto-touchdown is being implemented (plan 3.2), and it deserves its own celebration since it is the rarest scoring path in the game. Additive only: no existing field changed. |
| 1 | 2026-08-07 | **Frozen.** All eight of Sol's review findings applied: seed withheld until game over (and `/replay` gated the same way), `score_after` on `field_goal_resolved`, `possession_changed.reason` enumerated, event invariant scoped to presentation-relevant state, `roll` nullable on short punt and PAT kick, clutch visibility clarified, restart returns a new `game_id`. |
| 0 | 2026-08-07 | Initial draft. |
