/**
 * Contract-shaped fixture builders, hand-authored from docs/CONTRACT.md v2.
 *
 * These exist so the frontend can be built and tested before Sol's serializers
 * land. When the real API arrives these are replaced with generated fixtures and
 * any divergence is a contract bug worth finding early.
 *
 * See AGENT_WORK_SPLIT.md section 5: this is deliberately NOT the same thing as
 * ccf_pygame/fixtures/transcripts/, which are engine-internal state fingerprints.
 */

import type {
  Ball, Card, CardColor, DistributiveOmit, GameEvent, GameResponse, LegalAction,
  Seat, SeatState, Snapshot, Suit,
} from "../types";

const SUIT_GLYPH: Record<Suit, string> = { H: "♥", D: "♦", S: "♠", C: "♣" };
const RED_SUITS: Suit[] = ["H", "D"];

/** Parse "AH" / "10S" / "JOKER" into a contract Card. */
export function card(spec: string): Card {
  if (spec === "JOKER") {
    return { id: "JOKER", value: "Joker", suit: null, color: null, display: "JOKER" };
  }
  const suit = spec.slice(-1) as Suit;
  const value = spec.slice(0, -1);
  const color: CardColor = RED_SUITS.includes(suit) ? "red" : "black";
  return { id: spec, value, suit, color, display: `${value}${SUIT_GLYPH[suit]}` };
}

export const cards = (...specs: string[]): Card[] => specs.map(card);

export function seat(overrides: Partial<SeatState> & { seat: Seat }): SeatState {
  const hand = overrides.hand;
  return {
    name: overrides.seat === "home" ? "Wolverines" : "Buckeyes",
    color: overrides.seat === "home" ? "red" : "black",
    rating: 7,
    kick_rating: 2,
    score: 0,
    mojo: 0,
    clutch: 2,
    clutch_used: false,
    hand_count: hand?.length ?? 7,
    segments: 0,
    fg_made: 0,
    fg_att: 0,
    punts: 0,
    ...overrides,
  };
}

const DEFAULT_HAND = cards("AH", "10D", "7S", "3C", "KH", "5S", "JOKER");

export function snapshot(overrides: Partial<Snapshot> = {}): Snapshot {
  return {
    game_id: "fixture-0001",
    revision: 1,
    phase: "WAITING_OFFENSE_CARD",
    required_action: "play_card",
    acting_seat: "home",
    viewer_seat: "home",
    quarter: 1,
    play: 1,
    plays_in_quarter: 6,
    ball: "1",
    offense_seat: "home",
    defense_seat: "away",
    home: seat({ seat: "home", hand: DEFAULT_HAND }),
    // Contract 2.2: the opponent's `hand` is ABSENT, not empty. Only a count.
    away: seat({ seat: "away", hand_count: 7 }),
    play_cards: { offense: null, defense: null, war: null, clutch: null },
    legal_actions: DEFAULT_HAND.map((_, i): LegalAction => ({
      type: "play_card", card_index: i, enabled: true,
    })),
    log: ["=== QUARTER 1 === Wolverines has ball"],
    message: "QUARTER 1 -- Wolverines has ball",
    result: null,
    ...overrides,
  };
}

export const postMoveActions = (
  opts: { fg?: boolean; clutch?: boolean } = {},
): LegalAction[] => [
  { type: "post_move", choice: "P", enabled: true },
  opts.fg
    ? { type: "post_move", choice: "F", enabled: true }
    : { type: "post_move", choice: "F", enabled: false, disabled_reason: "not_in_field_goal_range" },
  opts.clutch
    ? { type: "post_move", choice: "C", enabled: true }
    : { type: "post_move", choice: "C", enabled: false, disabled_reason: "no_clutch_remaining" },
  opts.fg
    ? { type: "post_move", choice: "S", enabled: true }
    : { type: "post_move", choice: "S", enabled: false, disabled_reason: "not_in_field_goal_range" },
];

export type UnsequencedEvent = DistributiveOmit<GameEvent, "seq">;

/** Attach sequential `seq` values, so fixtures never hand-number their events. */
export function sequence(events: UnsequencedEvent[]): GameEvent[] {
  return events.map((e, seq) => ({ ...e, seq }) as GameEvent);
}

export function response(
  snap: Snapshot,
  events: UnsequencedEvent[] = [],
): GameResponse {
  return { revision: snap.revision, snapshot: snap, events: sequence(events) };
}

export const ballPath = (from: Ball, to: Ball): { from: Ball; to: Ball } => ({ from, to });
