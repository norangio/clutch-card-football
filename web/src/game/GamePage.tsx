import { useCallback, useEffect, useRef, useState } from "react";

import { createMockClient, StaleRevisionError, type GameClient } from "../api/mockClient";
import { createHttpClient } from "../api/httpClient";
import type { Action, GameResponse, LegalAction, UnversionedAction } from "../api/types";
import { ActionBar, CardBattle, GameLog, Hand, Scoreboard } from "../hud/components";
import StadiumScene from "../scene/StadiumScene";
import { useAnimationQueue, type Speed } from "./useAnimationQueue";

const SPEEDS: Speed[] = ["normal", "fast", "instant"];
const STORAGE_KEY = "ccf.game_id";

/**
 * Module-level, NOT a default parameter. `client = createMockClient()` in the
 * signature builds a new client on every render, so the bootstrap effect keyed
 * on [client] re-fires forever and re-enqueues the opening events.
 */
const defaultClient = pickClient();

/**
 * Real API by default. `?mock=1` forces the fixtures, which is how the scene
 * and animations stay workable when the backend is not running.
 */
function pickClient(): GameClient {
  const useMock =
    typeof location !== "undefined" &&
    new URLSearchParams(location.search).has("mock");
  return useMock ? createMockClient() : createHttpClient();
}

const prefersReducedMotion = () =>
  typeof matchMedia === "function" &&
  matchMedia("(prefers-reduced-motion: reduce)").matches;

export default function GamePage({ client = defaultClient }: { client?: GameClient }) {
  const [state, setState] = useState<GameResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const queue = useAnimationQueue();
  const inFlight = useRef(false);

  useEffect(() => {
    let cancelled = false;
    const stored = localStorage.getItem(STORAGE_KEY);

    // Resume first, fall back to a new game if the id is unknown or expired.
    const start = stored
      ? client.getGame(stored).catch(() => createFresh())
      : createFresh();

    function createFresh() {
      return client.createGame({
        home: { name: "Wolverines", rating: 7, kick_rating: 2, color: "red", clutch: 2 },
        away: { name: "Buckeyes", rating: 6, kick_rating: 2, clutch: 2 },
        difficulty: "hard",
        seed: null,
      });
    }

    start
      .then((res) => {
        if (cancelled) return;
        localStorage.setItem(STORAGE_KEY, res.snapshot.game_id);
        setState(res);
        queue.enqueue(res.events);
      })
      .catch((e: unknown) =>
        !cancelled && setError(e instanceof Error ? e.message : String(e)));
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client]);

  useEffect(() => {
    if (prefersReducedMotion()) queue.setSpeed("instant");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submit = useCallback(
    async (action: UnversionedAction) => {
      if (!state || inFlight.current || queue.isPlaying) return;
      inFlight.current = true;
      setBusy(true);
      setError(null);
      try {
        const res = await client.act(state.snapshot.game_id, {
          ...action, revision: state.revision,
        } as Action);
        setState(res);
        queue.enqueue(res.events);
      } catch (e) {
        // Contract 7.2: a 409 is a silent reconcile, not an error to surface.
        if (e instanceof StaleRevisionError) setState(e.current);
        else setError(e instanceof Error ? e.message : String(e));
      } finally {
        inFlight.current = false;
        setBusy(false);
      }
    },
    [client, state, queue],
  );

  const onAction = useCallback(
    (a: LegalAction) => {
      if (a.type === "post_move") void submit({ type: "post_move", choice: a.choice });
      else if (a.type === "extra_point") void submit({ type: "extra_point", choice: a.choice });
    },
    [submit],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.key === " " || e.key === "Enter") && queue.isPlaying) {
        e.preventDefault();
        queue.skip();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [queue]);

  if (error) {
    return (
      <div className="app">
        <div className="panel" role="alert">
          <div className="section-title">Something went wrong</div>
          <p>{error}</p>
          <button className="btn primary" onClick={() => location.reload()}>Reload</button>
        </div>
      </div>
    );
  }

  if (!state) {
    return (
      <div className="app">
        <div className="panel"><span className="status">Dealing cards…</span></div>
      </div>
    );
  }

  const { snapshot } = state;
  const offenseColor =
    snapshot.offense_seat === "home" ? snapshot.home.color : snapshot.away.color;
  const locked = queue.isPlaying || busy;

  // The scene follows the event stream, not the snapshot: during playback the
  // ball should be where the CURRENT event says, so motion is visible rather
  // than already applied. Contract 5.2 guarantees a ball_moved for every
  // position change, which is what makes this the single animation path.
  const playing = queue.current;
  const sceneBall = playing?.type === "ball_moved" ? playing.to : snapshot.ball;

  return (
    <div className="app">
      <Scoreboard snapshot={snapshot} />

      <div className="panel stage">
        <StadiumScene ball={sceneBall} offense={offenseColor} event={playing} />
      </div>

      <div className="message" aria-live="polite">
        {queue.current ? describe(queue.current.type) : snapshot.message}
      </div>

      <div className="panel"><CardBattle snapshot={snapshot} /></div>

      <div className="panel transport">
        <div className="group">
          <button className="chip" onClick={queue.skip} disabled={!queue.isPlaying}>
            Skip
          </button>
          {SPEEDS.map((s) => (
            <button key={s} className="chip" aria-pressed={queue.speed === s}
                    onClick={() => queue.setSpeed(s)}>
              {s}
            </button>
          ))}
        </div>
        <span className="status">
          rev {state.revision}
          {queue.pending > 0 ? ` · ${queue.pending} queued` : ""}
          {locked ? " · input locked" : ""}
        </span>
      </div>

      <div className={`panel ${locked ? "locked" : ""}`}>
        <Hand snapshot={snapshot} locked={locked}
              onPlay={(i) => void submit({ type: "play_card", card_index: i })} />
      </div>

      <div className={`panel ${locked ? "locked" : ""}`}>
        <ActionBar snapshot={snapshot} locked={locked} onAction={onAction} />
      </div>

      <div className="panel"><GameLog log={snapshot.log} /></div>
    </div>
  );
}

function describe(type: string): string {
  const label = type.replace(/_/g, " ");
  return label.charAt(0).toUpperCase() + label.slice(1);
}
