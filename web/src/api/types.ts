/**
 * Derived from docs/CONTRACT.md v1. The document is the source of truth.
 *
 * If you need to change a shape here, change the contract first, in its own
 * commit, then regenerate. Never edit this to match the server.
 */

// ---------------------------------------------------------------- core types

export type Seat = "home" | "away";
export type CardColor = "red" | "black";
export type Suit = "H" | "D" | "S" | "C";

/** Field segments, matching ccf/field.py:SEGMENTS. Index 0 is unused in play. */
export type Ball = "0" | "1" | "2" | "3" | "Z3" | "Z2" | "Z1";

export interface Card {
  /** `{value}{suit}` or "JOKER". NOT unique: three jokers share "JOKER". */
  id: string;
  value: string;
  suit: Suit | null;
  color: CardColor | null;
  /** Pre-rendered face, e.g. "A♥". */
  display: string;
}

/**
 * A card the viewer may not see. Contract section 2.1: hidden cards are null,
 * never a redacted object. Renders face-down.
 */
export type MaybeCard = Card | null;

export interface SeatState {
  seat: Seat;
  name: string;
  color: CardColor;
  rating: number;
  kick_rating: number;
  score: number;
  mojo: number;
  clutch: number;
  clutch_used: boolean;
  /** Present ONLY for the viewer's own seat. Absent for the opponent. */
  hand?: Card[];
  hand_count: number;
  // Cumulative stats. Snapshot-only: no events explain these (contract 5.2).
  segments: number;
  fg_made: number;
  fg_att: number;
  punts: number;
}

// -------------------------------------------------------------------- phases

export type Phase =
  | "WAITING_OFFENSE_CARD"
  | "WAITING_DEFENSE_CARD"
  | "WAITING_POST_MOVE"
  | "WAITING_EXTRA_POINT_CHOICE"
  | "GAME_OVER";

export type RequiredAction = "play_card" | "post_move" | "extra_point" | "none";

export type PostMoveChoice = "P" | "F" | "C" | "S";
export type ExtraPointChoice = "K" | "2";

export type DisabledReason =
  | "not_in_field_goal_range"
  | "no_clutch_remaining"
  | "clutch_already_used_this_play";

export type LegalAction =
  | { type: "play_card"; card_index: number; enabled: boolean; disabled_reason?: DisabledReason }
  | { type: "post_move"; choice: PostMoveChoice; enabled: boolean; disabled_reason?: DisabledReason }
  | { type: "extra_point"; choice: ExtraPointChoice; enabled: boolean; disabled_reason?: DisabledReason };

// ------------------------------------------------------------------ snapshot

export interface GameResult {
  winner: Seat | null;
  home_score: number;
  away_score: number;
  is_tie: boolean;
}

export interface Snapshot {
  game_id: string;
  revision: number;
  /**
   * Present ONLY once `result` is non-null. Contract 4.1: the seed
   * reconstructs the entire deck, so it is withheld while the game is live.
   */
  seed?: number;

  phase: Phase;
  required_action: RequiredAction;
  acting_seat: Seat | null;
  viewer_seat: Seat;

  quarter: number;
  play: number;
  plays_in_quarter: number;

  ball: Ball;
  offense_seat: Seat;
  defense_seat: Seat;

  home: SeatState;
  away: SeatState;

  play_cards: {
    offense: MaybeCard;
    defense: MaybeCard;
    war: MaybeCard;
    clutch: MaybeCard;
  };

  legal_actions: LegalAction[];
  log: string[];
  message: string;
  result: GameResult | null;
}

// -------------------------------------------------------------------- events

export type MoveReason =
  | "drive_chart" | "joker" | "clutch" | "punt"
  | "short_punt" | "war" | "turnover" | "kickoff";

/**
 * `color_bonus` is the orange/green auto-touchdown (contract v2, plan 3.2): a
 * color-matched card landing exactly on Z1. Rarest scoring path in the game, so
 * it gets its own celebration.
 */
export type TouchdownCause =
  | "drive" | "joker" | "clutch" | "defensive_joker" | "color_bonus";

export type PossessionReason =
  | "punt" | "short_punt" | "field_goal_made" | "field_goal_missed"
  | "war_turnover" | "joker_turnover" | "touchdown" | "safety" | "quarter_start";

interface EventBase<T extends string> {
  /** Index within this response, starting at 0. */
  seq: number;
  type: T;
}

export type GameEvent =
  | (EventBase<"quarter_started"> & { quarter: number; offense_seat: Seat; dealt: number; ball: Ball })
  | (EventBase<"card_played"> & { seat: Seat; role: "offense" | "defense"; card: MaybeCard; hand_count_after: number })
  | (EventBase<"cards_revealed"> & { offense_card: Card; defense_card: Card; offense_value: number; defense_value: number; winner: "offense" | "defense" | "tie" })
  | (EventBase<"war_started"> & { tied_value: number })
  | (EventBase<"war_card_revealed"> & { card: Card; matches_offense_color: boolean; outcome: "advance" | "turnover" })
  | (EventBase<"joker_resolved"> & { played_by: "offense" | "defense"; opposing_value: number; outcome: "touchdown" | "turnover_z3" | "no_gain" | "advance_3" | "advance_1" })
  | (EventBase<"ball_moved"> & { seat: Seat; from: Ball; to: Ball; segments: number; reason: MoveReason; is_touchdown: boolean; is_safety: boolean })
  | (EventBase<"mojo_changed"> & { seat: Seat; from: number; to: number; reason: "won_card_battle" | "dominant_win" })
  | (EventBase<"mojo_converted_to_clutch"> & { seat: Seat; clutch_after: number; trigger: "pre_play" | "clutch_spend" })
  | (EventBase<"clutch_used"> & { seat: Seat; clutch_after: number; card: Card })
  | (EventBase<"possession_changed"> & { from_seat: Seat; to_seat: Seat; ball: Ball; reason: PossessionReason })
  /** `roll` is null for short_punt: the engine folds it into distance (contract 5.2). */
  | (EventBase<"punt_resolved"> & { seat: Seat; kind: "punt" | "short_punt"; distance: number; roll: number | null; from: Ball; to: Ball; clamped: boolean })
  | (EventBase<"field_goal_resolved"> & { seat: Seat; success: boolean; roll: number; total: number; target: number; from: Ball; points: number; score_after: number })
  | (EventBase<"touchdown_scored"> & { seat: Seat; points: number; score_after: number; cause: TouchdownCause })
  | (EventBase<"safety_scored"> & { seat: Seat; points: number; score_after: number })
  /** `roll` is null when choice is "K": pat_kick() discards it (contract 5.2). */
  | (EventBase<"extra_point_resolved"> & { seat: Seat; choice: ExtraPointChoice; success: boolean; roll: number | null; points: number; score_after: number })
  | (EventBase<"quarter_ended"> & { quarter: number; home_score: number; away_score: number })
  | (EventBase<"game_ended"> & { winner: Seat | null; home_score: number; away_score: number; is_tie: boolean });

export type GameEventType = GameEvent["type"];

/** Every event type in the contract. The animation registry must cover all of these. */
export const ALL_EVENT_TYPES = [
  "quarter_started", "card_played", "cards_revealed", "war_started",
  "war_card_revealed", "joker_resolved", "ball_moved", "mojo_changed",
  "mojo_converted_to_clutch", "clutch_used", "possession_changed",
  "punt_resolved", "field_goal_resolved", "touchdown_scored", "safety_scored",
  "extra_point_resolved", "quarter_ended", "game_ended",
] as const;

/**
 * Compile-time proof that ALL_EVENT_TYPES matches GameEvent exactly, in both
 * directions. Add an event to the union without listing it here (or vice versa)
 * and the build fails.
 *
 * `satisfies readonly GameEventType[]` alone is NOT enough: it only proves each
 * element is a valid type, not that every type is present.
 */
export type Assert<T extends true> = T;
export type _NoMissingEventTypes = Assert<
  [Exclude<GameEventType, (typeof ALL_EVENT_TYPES)[number]>] extends [never] ? true : false
>;
export type _NoExtraEventTypes = Assert<
  [Exclude<(typeof ALL_EVENT_TYPES)[number], GameEventType>] extends [never] ? true : false
>;

// ----------------------------------------------------------------- transport

/**
 * A plain `Omit<Union, K>` collapses a discriminated union to its common keys,
 * which silently accepts payloads that mix variants. Distribute instead.
 */
export type DistributiveOmit<T, K extends PropertyKey> =
  T extends unknown ? Omit<T, K> : never;

export interface GameResponse {
  revision: number;
  snapshot: Snapshot;
  events: GameEvent[];
}

/** An action before the client stamps its revision on it. */
export type UnversionedAction = DistributiveOmit<Action, "revision">;

export type Action =
  | { revision: number; type: "play_card"; card_index: number }
  | { revision: number; type: "post_move"; choice: PostMoveChoice }
  | { revision: number; type: "extra_point"; choice: ExtraPointChoice };

export interface CreateGameRequest {
  home: { name: string; rating: number; kick_rating: number; color: CardColor; clutch: number };
  away: { name: string; rating: number; kick_rating: number; clutch: number };
  difficulty: "easy" | "medium" | "hard";
  seed: number | null;
}

export type ApiErrorCode =
  | "game_not_found" | "stale_revision" | "illegal_action" | "invalid_action";

export interface ApiError {
  error: { code: ApiErrorCode; message: string; revision?: number };
}
