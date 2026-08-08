/**
 * Replays the hand-authored fixtures behind the same interface the real client
 * will implement. Lets the whole frontend be built and tested before Sol's
 * FastAPI service exists.
 *
 * Swapped for the HTTP client at Phase 2 integration. Nothing outside this file
 * should know which one is in use.
 */

import type { Action, CreateGameRequest, GameResponse } from "./types";
import { DRIVE_SEQUENCE } from "./__fixtures__/scenarios";

export interface GameClient {
  createGame(req: CreateGameRequest): Promise<GameResponse>;
  getGame(gameId: string): Promise<GameResponse>;
  act(gameId: string, action: Action): Promise<GameResponse>;
  restart(gameId: string): Promise<GameResponse>;
}

/** Thrown for a 409, matching the contract's stale-revision rule (7.2). */
export class StaleRevisionError extends Error {
  constructor(readonly current: GameResponse) {
    super("stale revision");
    this.name = "StaleRevisionError";
  }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export interface MockOptions {
  /** Simulated latency, so loading states are exercised rather than assumed. */
  latencyMs?: number;
}

export function createMockClient(opts: MockOptions = {}): GameClient {
  const latency = opts.latencyMs ?? 120;
  let cursor = 0;

  const current = (): GameResponse => {
    const step = DRIVE_SEQUENCE[Math.min(cursor, DRIVE_SEQUENCE.length - 1)];
    if (!step) throw new Error("fixture sequence is empty");
    return step;
  };

  /** Resume returns state with no events: the client already played them (7). */
  const asResume = (res: GameResponse): GameResponse => ({ ...res, events: [] });

  return {
    async createGame() {
      await sleep(latency);
      cursor = 0;
      return current();
    },

    async getGame() {
      await sleep(latency);
      return asResume(current());
    },

    async act(_gameId, action) {
      await sleep(latency);
      const expected = current().revision;
      if (action.revision < expected) {
        // Contract 7.2: reject without mutating, hand back current state.
        throw new StaleRevisionError(asResume(current()));
      }
      cursor = Math.min(cursor + 1, DRIVE_SEQUENCE.length - 1);
      return current();
    },

    async restart() {
      await sleep(latency);
      cursor = 0;
      // Contract 7.3: restart yields a NEW game_id.
      const first = current();
      return {
        ...first,
        snapshot: { ...first.snapshot, game_id: `fixture-${Date.now().toString(36)}` },
      };
    },
  };
}
