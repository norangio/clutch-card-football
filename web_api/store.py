"""Session stores for the Clutch Card Football API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import pickle
import sqlite3
from threading import RLock

from ccf_pygame.ccf.events import GameEvent
from ccf_pygame.ccf.state_machine import GameStateMachine


@dataclass
class GameSession:
    game_id: str
    seed: int
    revision: int
    setup: dict
    game: GameStateMachine
    event_log: list[GameEvent] = field(default_factory=list)


class MemorySessionStore:
    def __init__(self):
        self._sessions: dict[str, GameSession] = {}

    def add(self, session: GameSession) -> None:
        self._sessions[session.game_id] = session

    def get(self, game_id: str) -> GameSession | None:
        return self._sessions.get(game_id)

    def save(self, session: GameSession) -> None:
        self._sessions[session.game_id] = session

    def close(self) -> None:
        pass


class SQLiteSessionStore:
    """Durable one-row-per-game storage.

    Engine state and the internal event log are trusted server-side pickle
    blobs. They are never returned directly; HTTP responses always pass
    through the viewer-scoped serializers.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(
            self.path,
            timeout=5,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                game_id TEXT PRIMARY KEY,
                seed TEXT NOT NULL,
                revision INTEGER NOT NULL,
                setup_json TEXT NOT NULL,
                engine_state BLOB NOT NULL,
                event_log BLOB NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _engine_blob(session: GameSession) -> bytes:
        return pickle.dumps(session.game, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _events_blob(session: GameSession) -> bytes:
        return pickle.dumps(session.event_log, protocol=pickle.HIGHEST_PROTOCOL)

    def add(self, session: GameSession) -> None:
        now = self._now()
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO sessions (
                    game_id, seed, revision, setup_json, engine_state,
                    event_log, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.game_id,
                    str(session.seed),
                    session.revision,
                    json.dumps(session.setup, sort_keys=True),
                    self._engine_blob(session),
                    self._events_blob(session),
                    now,
                    now,
                ),
            )

    def get(self, game_id: str) -> GameSession | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT game_id, seed, revision, setup_json, engine_state,
                       event_log
                FROM sessions
                WHERE game_id = ?
                """,
                (game_id,),
            ).fetchone()
        if row is None:
            return None
        return GameSession(
            game_id=row["game_id"],
            seed=int(row["seed"]),
            revision=row["revision"],
            setup=json.loads(row["setup_json"]),
            game=pickle.loads(row["engine_state"]),
            event_log=pickle.loads(row["event_log"]),
        )

    def save(self, session: GameSession) -> None:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                UPDATE sessions
                SET seed = ?, revision = ?, setup_json = ?, engine_state = ?,
                    event_log = ?, updated_at = ?
                WHERE game_id = ?
                """,
                (
                    str(session.seed),
                    session.revision,
                    json.dumps(session.setup, sort_keys=True),
                    self._engine_blob(session),
                    self._events_blob(session),
                    self._now(),
                    session.game_id,
                ),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"unknown game_id: {session.game_id}")

    def close(self) -> None:
        with self._lock:
            self._connection.close()
