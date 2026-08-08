"""Typed domain events emitted by the game engine.

Events keep engine-native values (notably :class:`Card`) until the response
boundary. ``to_dict`` produces the exact JSON shape in CONTRACT.md section 5.
The response-local ``seq`` number is deliberately not stored on the event.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from typing import ClassVar, Literal, TypeAlias

from .models import Card

Seat: TypeAlias = Literal["home", "away"]
Ball: TypeAlias = Literal["0", "1", "2", "3", "Z3", "Z2", "Z1"]


def _serialize_card(card: Card) -> dict:
    return {
        "id": str(card),
        "value": card.value,
        "suit": card.suit,
        "color": card.color.value if card.color else None,
        "display": card.display,
    }


def _json_value(value):
    if isinstance(value, Card):
        return _serialize_card(value)
    if isinstance(value, Enum):
        return value.value
    return value


class Event:
    """Base class for contract events."""

    type: ClassVar[str]
    _field_aliases: ClassVar[dict[str, str]] = {}

    def to_dict(self, seq: int) -> dict:
        if seq < 0:
            raise ValueError("event seq must be non-negative")
        payload = {"seq": seq, "type": self.type}
        payload.update(
            {
                self._field_aliases.get(field.name, field.name): _json_value(
                    getattr(self, field.name)
                )
                for field in fields(self)
            }
        )
        return payload


@dataclass(frozen=True)
class QuarterStartedEvent(Event):
    type: ClassVar[str] = "quarter_started"
    quarter: int
    offense_seat: Seat
    dealt: int
    ball: Ball


@dataclass(frozen=True)
class CardPlayedEvent(Event):
    type: ClassVar[str] = "card_played"
    seat: Seat
    role: Literal["offense", "defense"]
    card: Card | None
    hand_count_after: int


@dataclass(frozen=True)
class CardsRevealedEvent(Event):
    type: ClassVar[str] = "cards_revealed"
    offense_card: Card
    defense_card: Card
    offense_value: int
    defense_value: int
    winner: Literal["offense", "defense", "tie"]


@dataclass(frozen=True)
class WarStartedEvent(Event):
    type: ClassVar[str] = "war_started"
    tied_value: int


@dataclass(frozen=True)
class WarCardRevealedEvent(Event):
    type: ClassVar[str] = "war_card_revealed"
    card: Card
    matches_offense_color: bool
    outcome: Literal["advance", "turnover"]


@dataclass(frozen=True)
class JokerResolvedEvent(Event):
    type: ClassVar[str] = "joker_resolved"
    played_by: Literal["offense", "defense"]
    opposing_value: int
    outcome: Literal[
        "touchdown", "turnover_z3", "no_gain", "advance_3", "advance_1"
    ]


@dataclass(frozen=True)
class BallMovedEvent(Event):
    type: ClassVar[str] = "ball_moved"
    _field_aliases: ClassVar[dict[str, str]] = {
        "from_ball": "from",
        "to_ball": "to",
    }
    seat: Seat
    from_ball: Ball
    to_ball: Ball
    segments: int
    reason: Literal[
        "drive_chart",
        "joker",
        "clutch",
        "punt",
        "short_punt",
        "war",
        "turnover",
        "kickoff",
    ]
    is_touchdown: bool
    is_safety: bool


@dataclass(frozen=True)
class MojoChangedEvent(Event):
    type: ClassVar[str] = "mojo_changed"
    _field_aliases: ClassVar[dict[str, str]] = {
        "from_value": "from",
        "to_value": "to",
    }
    seat: Seat
    from_value: int
    to_value: int
    reason: Literal["won_card_battle", "dominant_win"]


@dataclass(frozen=True)
class MojoConvertedToClutchEvent(Event):
    type: ClassVar[str] = "mojo_converted_to_clutch"
    seat: Seat
    clutch_after: int
    trigger: Literal["pre_play", "clutch_spend"]


@dataclass(frozen=True)
class ClutchUsedEvent(Event):
    type: ClassVar[str] = "clutch_used"
    seat: Seat
    clutch_after: int
    card: Card


@dataclass(frozen=True)
class PossessionChangedEvent(Event):
    type: ClassVar[str] = "possession_changed"
    from_seat: Seat
    to_seat: Seat
    ball: Ball
    reason: Literal[
        "punt",
        "short_punt",
        "field_goal_made",
        "field_goal_missed",
        "war_turnover",
        "joker_turnover",
        "touchdown",
        "safety",
        "quarter_start",
    ]


@dataclass(frozen=True)
class PuntResolvedEvent(Event):
    type: ClassVar[str] = "punt_resolved"
    _field_aliases: ClassVar[dict[str, str]] = {
        "from_ball": "from",
        "to_ball": "to",
    }
    seat: Seat
    kind: Literal["punt", "short_punt"]
    distance: int
    roll: int | None
    from_ball: Ball
    to_ball: Ball
    clamped: bool


@dataclass(frozen=True)
class FieldGoalResolvedEvent(Event):
    type: ClassVar[str] = "field_goal_resolved"
    _field_aliases: ClassVar[dict[str, str]] = {"from_ball": "from"}
    seat: Seat
    success: bool
    roll: int
    total: int
    target: int
    from_ball: Ball
    points: int
    score_after: int


@dataclass(frozen=True)
class TouchdownScoredEvent(Event):
    type: ClassVar[str] = "touchdown_scored"
    seat: Seat
    points: int
    score_after: int
    cause: Literal[
        "drive", "joker", "clutch", "defensive_joker", "color_bonus"
    ]


@dataclass(frozen=True)
class SafetyScoredEvent(Event):
    type: ClassVar[str] = "safety_scored"
    seat: Seat
    points: int
    score_after: int


@dataclass(frozen=True)
class ExtraPointResolvedEvent(Event):
    type: ClassVar[str] = "extra_point_resolved"
    seat: Seat
    choice: Literal["K", "2"]
    success: bool
    roll: int | None
    points: int
    score_after: int


@dataclass(frozen=True)
class QuarterEndedEvent(Event):
    type: ClassVar[str] = "quarter_ended"
    quarter: int
    home_score: int
    away_score: int


@dataclass(frozen=True)
class GameEndedEvent(Event):
    type: ClassVar[str] = "game_ended"
    winner: Seat | None
    home_score: int
    away_score: int
    is_tie: bool


GameEvent: TypeAlias = (
    QuarterStartedEvent
    | CardPlayedEvent
    | CardsRevealedEvent
    | WarStartedEvent
    | WarCardRevealedEvent
    | JokerResolvedEvent
    | BallMovedEvent
    | MojoChangedEvent
    | MojoConvertedToClutchEvent
    | ClutchUsedEvent
    | PossessionChangedEvent
    | PuntResolvedEvent
    | FieldGoalResolvedEvent
    | TouchdownScoredEvent
    | SafetyScoredEvent
    | ExtraPointResolvedEvent
    | QuarterEndedEvent
    | GameEndedEvent
)

ALL_EVENT_TYPES = (
    "quarter_started",
    "card_played",
    "cards_revealed",
    "war_started",
    "war_card_revealed",
    "joker_resolved",
    "ball_moved",
    "mojo_changed",
    "mojo_converted_to_clutch",
    "clutch_used",
    "possession_changed",
    "punt_resolved",
    "field_goal_resolved",
    "touchdown_scored",
    "safety_scored",
    "extra_point_resolved",
    "quarter_ended",
    "game_ended",
)
