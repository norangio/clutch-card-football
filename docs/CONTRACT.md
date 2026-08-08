# CCF Web Edition: Interface Contract

**Status:** DRAFT, awaiting Sol's review (handoff H1).
**Version:** 0 (unfrozen). Becomes 1 on sign-off.
**Owner:** Claude drafts, Sol reviews, then both code against it.

This is the only interface between the Python engine and the browser. Once
frozen, changing anything here is **its own commit, merged before any consumer
changes**. Never change a payload shape and a consumer in the same commit.

---

## 0. Sol: what to check before signing off

The parts most likely to be wrong, because they were written from reading the
engine rather than from implementing against it:

1. **Can `pump()` cleanly emit every event in section 5?** Some transitions
   collapse several changes into one step (`_resolve_play` awards mojo, converts
   mojo to clutch, computes movement, and may score, all before the phase
   changes). If splitting those into ordered events is awkward, say so now.
2. **Is `mojo_converted_to_clutch` distinguishable from `mojo_changed`?** The
   conversion in `_resolve_play` and the second one in `_do_clutch` have
   different triggers. Two events or one with a `reason`?
3. **`legal_actions` disabled reasons** (section 4.4) are my guesses at the
   engine's actual constraints. Correct them.
4. **Anything in the snapshot that is expensive to compute** every request.

Reply with concrete edits, not approval-in-principle. Phase 1 starts when this
says `Version: 1`.

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
  "seed": 42,
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
| `seed` | int | Echoed for debugging and replay. Not secret. |

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

> **Sol:** these reasons are inferred from `_post_move_options()`. Correct the
> strings and the conditions if they do not match.

### 4.5 `result`

`null` until the game ends, then:

```json
{ "winner": "home", "home_score": 28, "away_score": 21, "is_tie": false }
```

---

## 5. Events

Ordered array. The frontend plays them in sequence, then reconciles to the
snapshot. Every mutation the snapshot reflects **must** be explained by an
event; the frontend never diffs snapshots to infer what happened.

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
| `possession_changed` | `from_seat`, `to_seat`, `ball`, `reason` |
| `punt_resolved` | `seat`, `kind` (`punt`\|`short_punt`), `distance`, `roll`, `from`, `to`, `clamped` |
| `field_goal_resolved` | `seat`, `success`, `roll`, `total`, `target`, `from`, `points` |
| `touchdown_scored` | `seat`, `points`, `score_after`, `cause` (`drive`\|`joker`\|`clutch`\|`defensive_joker`) |
| `safety_scored` | `seat` (the seat **awarded** the 2), `points`, `score_after` |
| `extra_point_resolved` | `seat`, `choice` (`K`\|`2`), `success`, `roll`, `points`, `score_after` |
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
  to wait for the snapshot.

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
| Clutch card | from `SHOWING_CLUTCH` onward, and only for the drawing seat's own view until revealed |
| Deck contents | **never**, in any phase |
| Deck count | allowed |
| `seed` | allowed |

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
| `POST` | `/games/{id}/restart` | | New game, same setup, new seed. |
| `GET` | `/games/{id}/replay` | | `{ seed, events: [...] }`, whole history. Debug only. |
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
red and black. `seed: null` means the server picks one and returns it.

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

### 7.3 Errors

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
| 0 | 2026-08-07 | Initial draft. Awaiting Sol's review. |
