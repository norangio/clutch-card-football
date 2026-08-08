/**
 * A scripted drive, expressed purely as contract payloads.
 *
 * Every event type in ALL_EVENT_TYPES appears at least once across these
 * scenarios, so the animation registry can be exercised end to end with no
 * backend running.
 */

import type { GameResponse, Snapshot } from "../types";
import { card, cards, postMoveActions, response, seat, snapshot } from "./builders";

const HAND = cards("AH", "10D", "7S", "3C", "KH", "5S", "JOKER");

/** 1. Kickoff: quarter starts, human on offense, waiting for a card. */
export const quarterStart: GameResponse = response(
  snapshot({ revision: 1 }),
  [{ type: "quarter_started", quarter: 1, offense_seat: "home", dealt: 7, ball: "1" }],
);

/** 2. Ordinary play: both cards revealed, offense wins, ball advances. */
export const ordinaryPlay: GameResponse = response(
  snapshot({
    revision: 2,
    phase: "WAITING_POST_MOVE",
    required_action: "post_move",
    ball: "3",
    home: seat({ seat: "home", hand: HAND.slice(1), segments: 2 }),
    away: seat({ seat: "away", hand_count: 6, mojo: 0 }),
    play_cards: { offense: card("AH"), defense: card("7S"), war: null, clutch: null },
    legal_actions: postMoveActions({ clutch: true }),
    message: "Moved from 1 -> 3 (+2 segments)",
  }),
  [
    { type: "card_played", seat: "home", role: "offense", card: card("AH"), hand_count_after: 6 },
    { type: "card_played", seat: "away", role: "defense", card: null, hand_count_after: 6 },
    {
      type: "cards_revealed", offense_card: card("AH"), defense_card: card("7S"),
      offense_value: 14, defense_value: 7, winner: "offense",
    },
    {
      type: "ball_moved", seat: "home", from: "1", to: "3", segments: 2,
      reason: "drive_chart", is_touchdown: false, is_safety: false,
    },
  ],
);

/** 3. Defense wins the battle and earns mojo. */
export const defenseWinsMojo: GameResponse = response(
  snapshot({
    revision: 3,
    phase: "WAITING_POST_MOVE",
    required_action: "post_move",
    ball: "3",
    away: seat({ seat: "away", hand_count: 5, mojo: 1 }),
    play_cards: { offense: card("3C"), defense: card("KH"), war: null, clutch: null },
    legal_actions: postMoveActions({ clutch: true }),
  }),
  [
    { type: "cards_revealed", offense_card: card("3C"), defense_card: card("KH"), offense_value: 3, defense_value: 13, winner: "defense" },
    { type: "mojo_changed", seat: "away", from: 0, to: 1, reason: "won_card_battle" },
    { type: "ball_moved", seat: "home", from: "3", to: "3", segments: 0, reason: "drive_chart", is_touchdown: false, is_safety: false },
  ],
);

/** 4. War: tied values, deck card decides. */
export const warAdvance: GameResponse = response(
  snapshot({
    revision: 4,
    phase: "WAITING_POST_MOVE",
    required_action: "post_move",
    ball: "Z3",
    play_cards: { offense: card("8S"), defense: card("8D"), war: card("4H"), clutch: null },
    legal_actions: postMoveActions({ fg: true, clutch: true }),
    message: "WAR! 4♥ - Offense to Z3!",
  }),
  [
    { type: "cards_revealed", offense_card: card("8S"), defense_card: card("8D"), offense_value: 8, defense_value: 8, winner: "tie" },
    { type: "war_started", tied_value: 8 },
    { type: "war_card_revealed", card: card("4H"), matches_offense_color: true, outcome: "advance" },
    { type: "ball_moved", seat: "home", from: "3", to: "Z3", segments: 1, reason: "war", is_touchdown: false, is_safety: false },
  ],
);

/** 5. Joker played by offense against a low card: automatic touchdown, then PAT. */
export const jokerTouchdown: GameResponse = response(
  snapshot({
    revision: 5,
    phase: "WAITING_EXTRA_POINT_CHOICE",
    required_action: "extra_point",
    ball: "Z1",
    home: seat({ seat: "home", hand: HAND.slice(2), score: 6 }),
    play_cards: { offense: card("JOKER"), defense: card("3C"), war: null, clutch: null },
    legal_actions: [
      { type: "extra_point", choice: "K", enabled: true },
      { type: "extra_point", choice: "2", enabled: true },
    ],
    message: "TOUCHDOWN! Wolverines +6",
  }),
  [
    { type: "cards_revealed", offense_card: card("JOKER"), defense_card: card("3C"), offense_value: 15, defense_value: 3, winner: "offense" },
    { type: "joker_resolved", played_by: "offense", opposing_value: 3, outcome: "touchdown" },
    { type: "touchdown_scored", seat: "home", points: 6, score_after: 6, cause: "joker" },
  ],
);

/** 6. The rarest path: color-matched Ace lands exactly on Z1 (contract v2). */
export const colorBonusTouchdown: GameResponse = response(
  snapshot({
    revision: 6,
    phase: "WAITING_EXTRA_POINT_CHOICE",
    required_action: "extra_point",
    ball: "Z1",
    home: seat({ seat: "home", hand: HAND.slice(1), score: 6 }),
    play_cards: { offense: card("AH"), defense: card("5S"), war: null, clutch: null },
    legal_actions: [
      { type: "extra_point", choice: "K", enabled: true },
      { type: "extra_point", choice: "2", enabled: true },
    ],
    message: "TOUCHDOWN! Color bonus!",
  }),
  [
    { type: "cards_revealed", offense_card: card("AH"), defense_card: card("5S"), offense_value: 14, defense_value: 5, winner: "offense" },
    { type: "ball_moved", seat: "home", from: "2", to: "Z1", segments: 4, reason: "drive_chart", is_touchdown: true, is_safety: false },
    { type: "touchdown_scored", seat: "home", points: 6, score_after: 6, cause: "color_bonus" },
  ],
);

/** 7. Extra point, both variants. Note roll is null for the kick. */
export const patKick: GameResponse = response(
  snapshot({ revision: 7, ball: "1", home: seat({ seat: "home", hand: HAND, score: 7 }), offense_seat: "away", defense_seat: "home", acting_seat: "away", required_action: "none" }),
  [
    { type: "extra_point_resolved", seat: "home", choice: "K", success: true, roll: null, points: 1, score_after: 7 },
    { type: "possession_changed", from_seat: "home", to_seat: "away", ball: "1", reason: "touchdown" },
  ],
);

export const twoPointAttempt: GameResponse = response(
  snapshot({ revision: 7, ball: "1", home: seat({ seat: "home", hand: HAND, score: 8 }) }),
  [{ type: "extra_point_resolved", seat: "home", choice: "2", success: true, roll: 5, points: 2, score_after: 8 }],
);

/** 8. Clutch: spend a token, draw a bonus card, advance. */
export const clutchPlay: GameResponse = response(
  snapshot({
    revision: 8,
    phase: "WAITING_POST_MOVE",
    required_action: "post_move",
    ball: "Z2",
    home: seat({ seat: "home", hand: HAND.slice(1), clutch: 1, clutch_used: true }),
    play_cards: { offense: card("7S"), defense: card("3C"), war: null, clutch: card("10D") },
    legal_actions: postMoveActions({ fg: true }),
    message: "CLUTCH! Drew 10♦",
  }),
  [
    { type: "clutch_used", seat: "home", clutch_after: 1, card: card("10D") },
    { type: "ball_moved", seat: "home", from: "Z3", to: "Z2", segments: 1, reason: "clutch", is_touchdown: false, is_safety: false },
  ],
);

/** 9. Mojo converting to clutch. */
export const mojoConversion: GameResponse = response(
  snapshot({ revision: 9, home: seat({ seat: "home", hand: HAND, mojo: 0, clutch: 1 }) }),
  [
    { type: "mojo_changed", seat: "home", from: 1, to: 2, reason: "dominant_win" },
    { type: "mojo_converted_to_clutch", seat: "home", clutch_after: 1, trigger: "pre_play" },
  ],
);

/** 10. Punt: roll present. Short punt: roll null by contract. */
export const punt: GameResponse = response(
  snapshot({ revision: 10, ball: "1", offense_seat: "away", defense_seat: "home", acting_seat: "away", required_action: "none", home: seat({ seat: "home", hand: HAND, punts: 1 }) }),
  [
    { type: "punt_resolved", seat: "home", kind: "punt", distance: 4, roll: 2, from: "Z1", to: "2", clamped: false },
    { type: "ball_moved", seat: "home", from: "Z1", to: "2", segments: -4, reason: "punt", is_touchdown: false, is_safety: false },
    { type: "possession_changed", from_seat: "home", to_seat: "away", ball: "2", reason: "punt" },
  ],
);

export const shortPunt: GameResponse = response(
  snapshot({ revision: 10, ball: "3", offense_seat: "away", defense_seat: "home", acting_seat: "away", required_action: "none" }),
  [
    { type: "punt_resolved", seat: "home", kind: "short_punt", distance: 2, roll: null, from: "Z2", to: "3", clamped: false },
    { type: "possession_changed", from_seat: "home", to_seat: "away", ball: "3", reason: "short_punt" },
  ],
);

/** 11. Field goal, made and missed. */
export const fieldGoalGood: GameResponse = response(
  snapshot({ revision: 11, ball: "1", home: seat({ seat: "home", hand: HAND, score: 3, fg_made: 1, fg_att: 1 }), offense_seat: "away", defense_seat: "home", acting_seat: "away", required_action: "none" }),
  [
    { type: "field_goal_resolved", seat: "home", success: true, roll: 5, total: 7, target: 7, from: "Z3", points: 3, score_after: 3 },
    { type: "possession_changed", from_seat: "home", to_seat: "away", ball: "1", reason: "field_goal_made" },
  ],
);

export const fieldGoalMissed: GameResponse = response(
  snapshot({ revision: 11, ball: "3", home: seat({ seat: "home", hand: HAND, fg_att: 1 }), offense_seat: "away", defense_seat: "home", acting_seat: "away", required_action: "none" }),
  [
    { type: "field_goal_resolved", seat: "home", success: false, roll: 2, total: 4, target: 7, from: "Z3", points: 0, score_after: 0 },
    { type: "possession_changed", from_seat: "home", to_seat: "away", ball: "3", reason: "field_goal_missed" },
  ],
);

/** 12. Safety: the DEFENSE is awarded 2. */
export const safety: GameResponse = response(
  snapshot({ revision: 12, ball: "3", away: seat({ seat: "away", hand_count: 5, score: 2 }) }),
  [
    { type: "ball_moved", seat: "home", from: "1", to: "3", segments: -1, reason: "drive_chart", is_touchdown: false, is_safety: true },
    { type: "safety_scored", seat: "away", points: 2, score_after: 2 },
  ],
);

/** 13. Quarter and game end. */
export const quarterEnd: GameResponse = response(
  snapshot({ revision: 13, quarter: 2, play: 1 }),
  [
    { type: "quarter_ended", quarter: 1, home_score: 14, away_score: 7 },
    { type: "quarter_started", quarter: 2, offense_seat: "home", dealt: 6, ball: "1" },
  ],
);

export const gameOver: GameResponse = response(
  snapshot({
    revision: 40,
    phase: "GAME_OVER",
    required_action: "none",
    acting_seat: null,
    quarter: 4,
    // Contract 4.1: seed appears ONLY now that result is non-null.
    seed: 42,
    home: seat({ seat: "home", hand: [], hand_count: 0, score: 28 }),
    away: seat({ seat: "away", hand_count: 0, score: 21 }),
    legal_actions: [],
    message: "Wolverines WINS!",
    result: { winner: "home", home_score: 28, away_score: 21, is_tie: false },
  }),
  [{ type: "game_ended", winner: "home", home_score: 28, away_score: 21, is_tie: false }],
);

/** 14. Defensive joker: the DEFENSE scores. */
export const defensiveJokerTouchdown: GameResponse = response(
  snapshot({
    revision: 14,
    ball: "1",
    away: seat({ seat: "away", hand_count: 5, score: 6 }),
    play_cards: { offense: card("3C"), defense: card("JOKER"), war: null, clutch: null },
    required_action: "none",
    acting_seat: null,
  }),
  [
    { type: "cards_revealed", offense_card: card("3C"), defense_card: card("JOKER"), offense_value: 3, defense_value: 15, winner: "defense" },
    { type: "joker_resolved", played_by: "defense", opposing_value: 3, outcome: "touchdown" },
    { type: "touchdown_scored", seat: "away", points: 6, score_after: 6, cause: "defensive_joker" },
  ],
);

/**
 * Ordered walkthrough used by the mock client and the demo.
 *
 * Each scenario above is authored standalone, so their revision numbers are
 * illustrative and collide. Composing them into one drive renumbers revisions
 * sequentially, which is what a real session would do.
 */
const orderedScenarios: GameResponse[] = [
  quarterStart, ordinaryPlay, defenseWinsMojo, warAdvance, clutchPlay,
  fieldGoalGood, punt, jokerTouchdown, patKick, colorBonusTouchdown,
  twoPointAttempt, defensiveJokerTouchdown, safety, shortPunt,
  fieldGoalMissed, mojoConversion, quarterEnd, gameOver,
];

function withRevision(res: GameResponse, revision: number): GameResponse {
  const snap: Snapshot = { ...res.snapshot, revision };
  return { revision, snapshot: snap, events: res.events };
}

export const DRIVE_SEQUENCE: GameResponse[] = orderedScenarios.map((res, i) =>
  withRevision(res, i + 1),
);

export const ALL_SCENARIOS: Record<string, GameResponse> = {
  quarterStart, ordinaryPlay, defenseWinsMojo, warAdvance, jokerTouchdown,
  colorBonusTouchdown, patKick, twoPointAttempt, clutchPlay, mojoConversion,
  punt, shortPunt, fieldGoalGood, fieldGoalMissed, safety, quarterEnd,
  gameOver, defensiveJokerTouchdown,
};
