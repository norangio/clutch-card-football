/**
 * Maps a game event to how the scene should behave.
 *
 * Deliberately its own module: exporting a non-component alongside a default
 * component export breaks Vite's Fast Refresh ("incompatible export"), which
 * leaves the R3F canvas wedged at its 300x150 default with the render loop
 * never starting. Keep component files exporting only components.
 */

import type { GameEvent } from "../api/types";

export type Shot = "broadcast" | "endzone" | "wide" | "drama";
export type BallMode = "run" | "punt" | "kick";

export interface Cue {
  mode: BallMode;
  shot: Shot;
  celebrating: boolean;
  dramatic: boolean;
  safety: boolean;
  dramaColor: string;
}

export function choreograph(event: GameEvent | null | undefined): Cue {
  const t = event?.type;
  const celebrating = t === "touchdown_scored";
  const dramatic =
    t === "war_started" || t === "war_card_revealed" ||
    t === "joker_resolved" || t === "clutch_used";
  const kicking = t === "field_goal_resolved" || t === "extra_point_resolved";

  const mode: BallMode =
    kicking ? "kick"
    : t === "punt_resolved" ||
      (event?.type === "ball_moved" &&
        (event.reason === "punt" || event.reason === "short_punt")) ? "punt"
    : "run";

  const shot: Shot =
    kicking || celebrating ? "endzone"
    : dramatic ? "drama"
    : t === "punt_resolved" ? "wide"
    : "broadcast";

  return {
    mode, shot, celebrating, dramatic,
    safety: t === "safety_scored",
    dramaColor: t === "joker_resolved" ? "#e8c86a" : "#9fd6ff",
  };
}
