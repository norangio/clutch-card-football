"""Contract-v2.1 HTTP API for Clutch Card Football."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import Callable
import json
import logging
import os
from pathlib import Path
from threading import RLock
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ccf_pygame.ccf.ai import Difficulty
from ccf_pygame.ccf.models import Color
from ccf_pygame.ccf.serializers import serialize_events, serialize_snapshot
from ccf_pygame.ccf.state_machine import GameStateMachine
from ccf_pygame.ccf.states import GamePhase

from .schemas import Action, CreateGameRequest, GameResponse, ReplayResponse
from .store import GameSession, MemorySessionStore, SQLiteSessionStore

VIEWER_SEAT = "home"
ACTION_LOGGER = logging.getLogger("ccf.api.actions")


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        revision: int | None = None,
        snapshot: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.revision = revision
        self.snapshot = snapshot


def _error_payload(error: ApiError) -> dict:
    detail = {"code": error.code, "message": error.message}
    if error.revision is not None:
        detail["revision"] = error.revision
    payload = {"error": detail}
    if error.snapshot is not None:
        payload.update(
            {
                "revision": error.revision,
                "snapshot": error.snapshot,
                "events": [],
            }
        )
    return payload


def _build_game(setup: dict, seed: int) -> GameStateMachine:
    game = GameStateMachine(seed=seed)
    home = setup["home"]
    away = setup["away"]
    game.provide_setup(
        home["name"],
        home["rating"],
        home["kick_rating"],
        Color(home["color"]),
        home["clutch"],
        away["name"],
        away["rating"],
        away["kick_rating"],
        away["clutch"],
        difficulty=Difficulty(setup["difficulty"]),
        ai_vs_ai=setup.get("ai_vs_ai", False),
    )
    return game


def create_app(
    *,
    store=None,
    seed_factory: Callable[[], int] | None = None,
    id_factory: Callable[[], str] | None = None,
) -> FastAPI:
    session_store = store or MemorySessionStore()
    next_seed = seed_factory or (lambda: secrets.randbits(63))
    next_id = id_factory or (lambda: uuid.uuid4().hex)
    mutation_lock = RLock()

    api = FastAPI(title="Clutch Card Football API", version="2.1")
    api.state.session_store = session_store

    def cleanup_expired_sessions() -> int:
        cleanup = getattr(session_store, "cleanup_expired", None)
        return cleanup() if cleanup is not None else 0

    cleanup_expired_sessions()

    def require_session(game_id: str) -> GameSession:
        cleanup_expired_sessions()
        session = session_store.get(game_id)
        if session is None:
            raise ApiError("game_not_found", "game not found", 404)
        return session

    def snapshot_for(session: GameSession) -> dict:
        return serialize_snapshot(
            session.game,
            VIEWER_SEAT,
            game_id=session.game_id,
            revision=session.revision,
        )

    def response_for(session: GameSession, events) -> dict:
        return {
            "revision": session.revision,
            "snapshot": snapshot_for(session),
            "events": serialize_events(events, VIEWER_SEAT),
        }

    def create_session(setup: dict, requested_seed: int | None) -> tuple[GameSession, list]:
        cleanup_expired_sessions()
        seed = requested_seed if requested_seed is not None else next_seed()
        game = _build_game(setup, seed)
        events = game.pump()
        session = GameSession(
            game_id=next_id(),
            seed=seed,
            revision=0,
            setup=setup,
            game=game,
            event_log=list(events),
        )
        session_store.add(session)
        return session, events

    @api.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError):
        return JSONResponse(_error_payload(exc), status_code=exc.status_code)

    @api.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        revision = None
        parts = request.url.path.strip("/").split("/")
        if len(parts) >= 3 and parts[:2] == ["api", "games"]:
            session = session_store.get(parts[2])
            if session is not None:
                revision = session.revision
        message = exc.errors()[0].get("msg", "invalid request")
        error = ApiError(
            "invalid_action",
            message,
            400,
            revision=revision,
        )
        return JSONResponse(_error_payload(error), status_code=400)

    @api.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @api.post("/api/games", response_model=GameResponse)
    def create_game(request: CreateGameRequest):
        setup = request.model_dump(exclude={"seed"})
        session, events = create_session(setup, request.seed)
        return response_for(session, events)

    @api.get("/api/games/{game_id}", response_model=GameResponse)
    def get_game(game_id: str):
        session = require_session(game_id)
        return response_for(session, [])

    def apply_action_locked(game_id: str, action: Action):
        session = require_session(game_id)
        if action.revision < session.revision:
            raise ApiError(
                "stale_revision",
                "client revision is stale",
                409,
                revision=session.revision,
                snapshot=snapshot_for(session),
            )
        if action.revision > session.revision:
            raise ApiError(
                "invalid_action",
                "client revision is ahead of the server",
                400,
                revision=session.revision,
            )

        expected_revision = session.revision
        game = session.game
        expected = {
            GamePhase.WAITING_OFFENSE_CARD: "play_card",
            GamePhase.WAITING_DEFENSE_CARD: "play_card",
            GamePhase.WAITING_POST_MOVE: "post_move",
            GamePhase.WAITING_EXTRA_POINT_CHOICE: "extra_point",
        }.get(game.phase)
        if action.type != expected:
            raise ApiError(
                "illegal_action",
                f"{action.type} is not legal in phase {game.phase.name}",
                422,
                revision=session.revision,
            )

        if action.type == "play_card":
            team = (
                game.offense
                if game.phase == GamePhase.WAITING_OFFENSE_CARD
                else game.defense
            )
            if action.card_index < 0 or action.card_index >= len(team.hand):
                raise ApiError(
                    "invalid_action",
                    "card_index is out of range",
                    400,
                    revision=session.revision,
                )
            game.provide_card(action.card_index)
        elif action.type == "post_move":
            legal = {
                item["choice"]: item["enabled"]
                for item in serialize_snapshot(
                    game,
                    VIEWER_SEAT,
                    game_id=session.game_id,
                    revision=session.revision,
                )["legal_actions"]
            }
            if not legal.get(action.choice, False):
                raise ApiError(
                    "illegal_action",
                    f"post-move choice {action.choice} is disabled",
                    422,
                    revision=session.revision,
                )
            game.provide_post_move(action.choice)
        else:
            game.provide_extra_point_choice(action.choice)

        events = game.pump()
        session.revision += 1
        session.event_log.extend(events)
        save_if_revision = getattr(session_store, "save_if_revision", None)
        if save_if_revision is None:
            session_store.save(session)
        elif not save_if_revision(
            session,
            expected_revision=expected_revision,
        ):
            current = require_session(game_id)
            raise ApiError(
                "stale_revision",
                "client revision is stale",
                409,
                revision=current.revision,
                snapshot=snapshot_for(current),
            )
        return response_for(session, events)

    @api.post("/api/games/{game_id}/actions", response_model=GameResponse)
    def apply_action(game_id: str, action: Action):
        # FastAPI runs sync handlers in a thread pool. Keep revision check,
        # mutation, and persistence atomic so two rapid taps cannot both win.
        started = perf_counter()
        phase_before = None
        phase_after = None
        event_count = 0
        outcome = "internal_error"
        try:
            with mutation_lock:
                existing = session_store.get(game_id)
                if existing is not None:
                    phase_before = existing.game.phase.name
                response = apply_action_locked(game_id, action)
                phase_after = response["snapshot"]["phase"]
                event_count = len(response["events"])
                outcome = "accepted"
                return response
        except ApiError as error:
            outcome = error.code
            if error.snapshot is not None:
                phase_after = error.snapshot["phase"]
            else:
                phase_after = phase_before
            raise
        finally:
            ACTION_LOGGER.info(
                json.dumps(
                    {
                        "action_type": action.type,
                        "duration_ms": round(
                            (perf_counter() - started) * 1000,
                            3,
                        ),
                        "event_count": event_count,
                        "game_id": game_id,
                        "outcome": outcome,
                        "phase_after": phase_after,
                        "phase_before": phase_before,
                        "revision": action.revision,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )

    @api.post("/api/games/{game_id}/restart", response_model=GameResponse)
    def restart_game(game_id: str):
        old_session = require_session(game_id)
        session, events = create_session(old_session.setup, next_seed())
        return response_for(session, events)

    @api.get("/api/games/{game_id}/replay", response_model=ReplayResponse)
    def replay_game(game_id: str):
        session = require_session(game_id)
        if session.game.phase != GamePhase.GAME_OVER:
            # Do not confirm that a live game exists: its seed is sensitive.
            raise ApiError("game_not_found", "replay not found", 404)
        return {
            "seed": session.seed,
            "events": serialize_events(session.event_log, VIEWER_SEAT),
        }

    return api


_default_db = Path(
    os.environ.get(
        "CCF_DB_PATH",
        Path(__file__).parent / "data" / "sessions.sqlite3",
    )
)
app = create_app(store=SQLiteSessionStore(_default_db))
