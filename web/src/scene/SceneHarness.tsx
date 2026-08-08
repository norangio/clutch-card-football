/**
 * Dev harness for scene work. Open `/?scene=1`.
 *
 * Drives StadiumScene directly from a picked event so choreography can be
 * iterated on without playing a whole game to reach a rare beat. Every event
 * type in the contract is listed, including the ones that are hard to reach
 * naturally (safety, defensive joker, color-bonus touchdown).
 *
 * Not reachable from the game itself and not part of the production flow.
 */

import { useState } from "react";

import { ALL_SCENARIOS } from "../api/__fixtures__/scenarios";
import type { Ball, CardColor, GameEvent } from "../api/types";
import StadiumScene from "./StadiumScene";

/** Every event the fixtures contain, flattened and labelled by scenario. */
const CATALOG: Array<{ label: string; event: GameEvent; ball: Ball }> =
  Object.entries(ALL_SCENARIOS).flatMap(([name, res]) =>
    res.events.map((event) => ({
      label: `${name} · ${event.type}`,
      event,
      ball: event.type === "ball_moved" ? event.to : res.snapshot.ball,
    })),
  );

export default function SceneHarness() {
  const [index, setIndex] = useState(0);
  const [offense, setOffense] = useState<CardColor>("red");
  const [nonce, setNonce] = useState(0);
  const entry = CATALOG[index];

  if (!entry) return <div className="app">No fixtures.</div>;

  return (
    <div className="app">
      <div className="panel transport">
        <div className="group">
          <button className="chip" onClick={() => setIndex((i) => Math.max(0, i - 1))}>
            ← prev
          </button>
          <button
            className="chip"
            onClick={() => setIndex((i) => Math.min(CATALOG.length - 1, i + 1))}
          >
            next →
          </button>
          {/* Remounting replays one-shot effects like the confetti burst. */}
          <button className="chip" onClick={() => setNonce((n) => n + 1)}>
            replay
          </button>
          <button
            className="chip"
            aria-pressed={offense === "black"}
            onClick={() => setOffense((c) => (c === "red" ? "black" : "red"))}
          >
            offense: {offense}
          </button>
        </div>
        <span className="status">
          {index + 1} / {CATALOG.length}
        </span>
      </div>

      <div className="message">{entry.label}</div>

      <div className="panel stage" style={{ height: "62vh" }}>
        {/* No key here on purpose. Remounting the Canvas recreates the WebGL
            context, and R3F does not re-measure inside a fixed-height parent,
            so it comes back at the 300x150 default and never renders. Only the
            one-shot effects are keyed, via `replay`. */}
        <StadiumScene
          ball={entry.ball}
          offense={offense}
          event={entry.event}
          replay={nonce}
        />
      </div>

      <div className="panel">
        <div className="section-title">Event payload</div>
        <pre className="log" style={{ maxHeight: 160, whiteSpace: "pre-wrap" }}>
          {JSON.stringify(entry.event, null, 1)}
        </pre>
      </div>
    </div>
  );
}
