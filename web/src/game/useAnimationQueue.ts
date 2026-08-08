/**
 * The animation director (plan section 7.4).
 *
 * One coordinator owns event playback. Components never react to snapshot
 * changes independently, because that is how state and animation drift apart.
 *
 * Responsibilities: hold the ordered event queue, lock input while it drains,
 * expose the currently-playing event, and support skip and speed.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { ALL_EVENT_TYPES, type GameEvent, type GameEventType } from "../api/types";

export type Speed = "normal" | "fast" | "instant";

const SPEED_SCALE: Record<Speed, number> = { normal: 1, fast: 0.45, instant: 0 };

/** Base beat per event type, in ms. Plan section 4's timing table. */
export const EVENT_DURATION: Record<GameEventType, number> = {
  quarter_started: 1200,
  card_played: 550,
  cards_revealed: 1000,
  war_started: 700,
  war_card_revealed: 1600,
  joker_resolved: 1500,
  ball_moved: 1100,
  mojo_changed: 400,
  mojo_converted_to_clutch: 700,
  clutch_used: 1300,
  possession_changed: 700,
  punt_resolved: 1200,
  field_goal_resolved: 1500,
  touchdown_scored: 2000,
  safety_scored: 1300,
  extra_point_resolved: 1000,
  quarter_ended: 1200,
  game_ended: 2500,
};

/**
 * Compile-time proof the timing table covers every event. A missing entry would
 * otherwise surface as an undefined duration and a stuck queue.
 */
type Assert<T extends true> = T;
export type _DurationsCoverAllEvents = Assert<
  [Exclude<GameEventType, keyof typeof EVENT_DURATION>] extends [never] ? true : false
>;

export interface AnimationQueue {
  /** The event currently on screen, or null when idle. */
  current: GameEvent | null;
  /** True while events remain. Input must stay locked. */
  isPlaying: boolean;
  pending: number;
  speed: Speed;
  setSpeed: (s: Speed) => void;
  /** Drain immediately. Final state must match watching it through. */
  skip: () => void;
  enqueue: (events: GameEvent[]) => void;
}

export function useAnimationQueue(
  onEventApplied?: (event: GameEvent) => void,
): AnimationQueue {
  const [queue, setQueue] = useState<GameEvent[]>([]);
  const [current, setCurrent] = useState<GameEvent | null>(null);
  const [speed, setSpeed] = useState<Speed>("normal");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const applied = useRef(onEventApplied);
  applied.current = onEventApplied;

  const clear = () => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  };

  // Two effects on purpose. Advancing and timing MUST NOT share one effect:
  // setCurrent/setQueue change that effect's own deps, so its cleanup fires
  // immediately and cancels the timer it just set. The queue then freezes with
  // input locked forever. Splitting them keeps the timer's lifetime tied to
  // `current` alone.

  // 1. Pull the next event when idle.
  useEffect(() => {
    if (current !== null || queue.length === 0) return;
    const next = queue[0];
    if (!next) return;
    setCurrent(next);
    setQueue((q) => q.slice(1));
  }, [queue, current]);

  // 2. Hold the current event on screen for its beat, then retire it.
  useEffect(() => {
    if (current === null) return;
    const ms = EVENT_DURATION[current.type] * SPEED_SCALE[speed];
    const finish = () => {
      applied.current?.(current);
      setCurrent(null);
      timer.current = null;
    };
    if (ms === 0) {
      finish();
      return;
    }
    timer.current = setTimeout(finish, ms);
    return clear;
  }, [current, speed]);

  useEffect(() => clear, []);

  const enqueue = useCallback((events: GameEvent[]) => {
    if (events.length > 0) setQueue((q) => [...q, ...events]);
  }, []);

  const skip = useCallback(() => {
    clear();
    setQueue((remaining) => {
      // Apply everything still outstanding so the end state is identical to
      // having watched it. Skipping must never diverge from playing.
      setCurrent((playing) => {
        if (playing) applied.current?.(playing);
        return null;
      });
      remaining.forEach((e) => applied.current?.(e));
      return [];
    });
  }, []);

  return {
    current,
    isPlaying: current !== null || queue.length > 0,
    pending: queue.length + (current ? 1 : 0),
    speed,
    setSpeed,
    skip,
    enqueue,
  };
}

/** Guards the registry invariant from plan section 7.4. */
export const KNOWN_EVENT_TYPES: ReadonlySet<GameEventType> = new Set(ALL_EVENT_TYPES);
