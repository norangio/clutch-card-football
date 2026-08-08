import { describe, expect, it } from "vitest";

import { ALL_EVENT_TYPES, type GameEventType } from "../types";
import { ALL_SCENARIOS, DRIVE_SEQUENCE } from "./scenarios";

const everyEvent = Object.values(ALL_SCENARIOS).flatMap((r) => r.events);

describe("fixture coverage", () => {
  it("exercises every event type in the contract", () => {
    const covered = new Set<GameEventType>(everyEvent.map((e) => e.type));
    const missing = ALL_EVENT_TYPES.filter((t) => !covered.has(t));
    expect(missing, `event types with no fixture: ${missing.join(", ")}`).toEqual([]);
  });

  it("numbers events sequentially from 0 within each response", () => {
    for (const [name, res] of Object.entries(ALL_SCENARIOS)) {
      expect(res.events.map((e) => e.seq), name).toEqual(res.events.map((_, i) => i));
    }
  });

  it("keeps revision consistent between response and snapshot", () => {
    for (const [name, res] of Object.entries(ALL_SCENARIOS)) {
      expect(res.revision, name).toBe(res.snapshot.revision);
    }
  });
});

describe("redaction invariants (contract section 6)", () => {
  it("never includes the opponent's hand", () => {
    for (const [name, res] of Object.entries(ALL_SCENARIOS)) {
      const { snapshot } = res;
      const opponent = snapshot.viewer_seat === "home" ? snapshot.away : snapshot.home;
      expect(opponent.hand, `${name} leaked the opponent hand`).toBeUndefined();
    }
  });

  it("always includes the viewer's own hand", () => {
    for (const [name, res] of Object.entries(ALL_SCENARIOS)) {
      const { snapshot } = res;
      const own = snapshot.viewer_seat === "home" ? snapshot.home : snapshot.away;
      expect(Array.isArray(own.hand), `${name} is missing the viewer hand`).toBe(true);
    }
  });

  it("withholds the seed until the game is over", () => {
    for (const [name, res] of Object.entries(ALL_SCENARIOS)) {
      const { snapshot } = res;
      if (snapshot.result === null) {
        expect(snapshot.seed, `${name} leaked the seed mid-game`).toBeUndefined();
      }
    }
  });

  it("hides the opponent card while defense is still choosing", () => {
    for (const [name, res] of Object.entries(ALL_SCENARIOS)) {
      const { snapshot } = res;
      if (snapshot.phase === "WAITING_DEFENSE_CARD") {
        const offenseIsOpponent = snapshot.offense_seat !== snapshot.viewer_seat;
        if (offenseIsOpponent) {
          expect(snapshot.play_cards.offense, `${name} leaked the AI's card`).toBeNull();
        }
      }
    }
  });

  it("marks a card_played for the opponent as null", () => {
    const opponentPlays = everyEvent.filter(
      (e) => e.type === "card_played" && e.seat === "away",
    );
    expect(opponentPlays.length).toBeGreaterThan(0);
    for (const event of opponentPlays) {
      if (event.type !== "card_played") continue;
      expect(event.card, "opponent card_played must be redacted").toBeNull();
    }
  });
});

describe("contract field rules", () => {
  it("sends roll: null for short punts, a number for full punts", () => {
    for (const event of everyEvent) {
      if (event.type !== "punt_resolved") continue;
      if (event.kind === "short_punt") expect(event.roll).toBeNull();
      else expect(typeof event.roll).toBe("number");
    }
  });

  it("sends roll: null for PAT kicks, a number for two-point tries", () => {
    for (const event of everyEvent) {
      if (event.type !== "extra_point_resolved") continue;
      if (event.choice === "K") expect(event.roll).toBeNull();
      else expect(typeof event.roll).toBe("number");
    }
  });

  it("carries score_after on every scoring event", () => {
    const scoring = everyEvent.filter((e) =>
      ["touchdown_scored", "safety_scored", "field_goal_resolved", "extra_point_resolved"]
        .includes(e.type),
    );
    expect(scoring.length).toBeGreaterThan(0);
    for (const event of scoring) {
      expect(event, `${event.type} missing score_after`).toHaveProperty("score_after");
    }
  });

  it("gives the drive sequence monotonic-or-equal revisions", () => {
    const revisions = DRIVE_SEQUENCE.map((r) => r.revision);
    const sorted = [...revisions].sort((a, b) => a - b);
    expect(revisions).toEqual(sorted);
  });
});
