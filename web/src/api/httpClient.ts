/**
 * The real client. Talks to the FastAPI service through Vite's /api proxy, so
 * the app stays same-origin in dev and in any future deploy.
 *
 * Implements the same GameClient interface as the mock, so nothing above this
 * file knows which one is in use.
 */

import { StaleRevisionError, type GameClient } from "./mockClient";
import type { Action, ApiError, CreateGameRequest, GameResponse } from "./types";

const BASE = "/api";

/** Non-409 failures, surfaced to the user. */
export class ApiRequestError extends Error {
  constructor(readonly code: string, message: string, readonly status: number) {
    super(message);
    this.name = "ApiRequestError";
  }
}

async function parseError(res: Response): Promise<ApiError["error"]> {
  try {
    const body = (await res.json()) as Partial<ApiError>;
    if (body.error) return body.error;
  } catch {
    /* fall through to a generic shape */
  }
  return { code: "invalid_action", message: res.statusText || "request failed" };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (cause) {
    // Network-level failure. Distinct from an API error so the UI can offer a
    // retry rather than a reload.
    throw new ApiRequestError("network", "Could not reach the game server.", 0);
  }

  if (res.ok) return (await res.json()) as T;

  // Vite proxies /api, so a stopped backend surfaces as a gateway error rather
  // than a contract error. "Bad Gateway" tells the player nothing actionable.
  if (res.status >= 502 && res.status <= 504) {
    throw new ApiRequestError(
      "network",
      "The game server is not running. Start it with ./run-local.sh",
      res.status,
    );
  }

  const error = await parseError(res);

  // Contract 7.2: a 409 is not a failure. The server hands back current state
  // and the client reconciles silently. This is what makes rapid tapping safe.
  if (res.status === 409) {
    const body = (await tryJson(res.clone())) as GameResponse | null;
    if (body?.snapshot) throw new StaleRevisionError({ ...body, events: [] });
  }

  throw new ApiRequestError(error.code, error.message, res.status);
}

async function tryJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export function createHttpClient(): GameClient {
  return {
    createGame: (req: CreateGameRequest) =>
      request<GameResponse>("/games", { method: "POST", body: JSON.stringify(req) }),

    getGame: (gameId: string) => request<GameResponse>(`/games/${gameId}`),

    act: (gameId: string, action: Action) =>
      request<GameResponse>(`/games/${gameId}/actions`, {
        method: "POST",
        body: JSON.stringify(action),
      }),

    restart: (gameId: string) =>
      request<GameResponse>(`/games/${gameId}/restart`, { method: "POST" }),
  };
}
