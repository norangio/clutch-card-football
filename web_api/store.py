"""In-memory sessions used by the API; SQLite persistence replaces this next."""

from __future__ import annotations

from dataclasses import dataclass, field

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
