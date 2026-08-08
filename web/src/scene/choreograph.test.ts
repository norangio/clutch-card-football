import { describe, expect, it } from "vitest";

import { ALL_EVENT_TYPES, type GameEvent } from "../api/types";
import { ALL_SCENARIOS } from "../api/__fixtures__/scenarios";
import { choreograph } from "./choreograph";

const everyEvent = Object.values(ALL_SCENARIOS).flatMap((r) => r.events);

describe("choreograph", () => {
  it("handles every event type without throwing or going undefined", () => {
    // Plan 7.4's registry invariant: an unknown event must never leave the
    // scene in an undefined state, which is how a queue silently wedges.
    for (const type of ALL_EVENT_TYPES) {
      const sample = everyEvent.find((e) => e.type === type);
      expect(sample, `no fixture for ${type}`).toBeDefined();
      const cue = choreograph(sample as GameEvent);
      expect(["run", "punt", "kick"]).toContain(cue.mode);
      expect(["broadcast", "endzone", "wide", "drama"]).toContain(cue.shot);
    }
  });

  it("falls back to the default shot when idle", () => {
    const cue = choreograph(null);
    expect(cue.shot).toBe("broadcast");
    expect(cue.mode).toBe("run");
    expect(cue.celebrating).toBe(false);
  });

  it("celebrates only on a touchdown", () => {
    for (const e of everyEvent) {
      expect(choreograph(e).celebrating).toBe(e.type === "touchdown_scored");
    }
  });

  it("cuts to the end zone for kicks and scores", () => {
    const kick = everyEvent.find((e) => e.type === "field_goal_resolved");
    const td = everyEvent.find((e) => e.type === "touchdown_scored");
    expect(choreograph(kick!).shot).toBe("endzone");
    expect(choreograph(td!).shot).toBe("endzone");
  });

  it("arcs the ball for punts and kicks but not for runs", () => {
    const punt = everyEvent.find(
      (e) => e.type === "punt_resolved" && e.kind === "punt",
    );
    const fg = everyEvent.find((e) => e.type === "field_goal_resolved");
    const run = everyEvent.find(
      (e) => e.type === "ball_moved" && e.reason === "drive_chart",
    );
    expect(choreograph(punt!).mode).toBe("punt");
    expect(choreograph(fg!).mode).toBe("kick");
    expect(choreograph(run!).mode).toBe("run");
  });

  it("goes dark for war, joker and clutch", () => {
    for (const type of ["war_started", "war_card_revealed", "joker_resolved", "clutch_used"]) {
      const e = everyEvent.find((x) => x.type === type);
      expect(choreograph(e!).dramatic, type).toBe(true);
    }
    const run = everyEvent.find((e) => e.type === "ball_moved");
    expect(choreograph(run!).dramatic).toBe(false);
  });
});
