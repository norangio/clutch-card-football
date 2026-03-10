"""Game phases and snapshot dataclass for the state machine."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from .models import Card, Team


class GamePhase(Enum):
    # Setup
    SETUP_TEAMS = auto()

    # Quarter flow
    QUARTER_START = auto()

    # Card play
    WAITING_OFFENSE_CARD = auto()
    WAITING_DEFENSE_CARD = auto()
    AI_PLAYING_CARD = auto()
    SHOWING_CARD_BATTLE = auto()

    # Movement
    SHOWING_MOVEMENT = auto()

    # Scoring
    SHOWING_TOUCHDOWN = auto()
    SHOWING_SAFETY = auto()
    WAITING_EXTRA_POINT_CHOICE = auto()
    SHOWING_EXTRA_POINTS = auto()

    # Special plays
    SHOWING_WAR = auto()
    SHOWING_JOKER = auto()

    # Post-move
    WAITING_POST_MOVE = auto()
    AI_POST_MOVE = auto()
    SHOWING_PUNT = auto()
    SHOWING_FIELD_GOAL = auto()
    SHOWING_CLUTCH = auto()
    SHOWING_SHORT_PUNT = auto()

    # Confirm / transition
    WAITING_CONFIRM = auto()
    QUARTER_END = auto()
    GAME_OVER = auto()


@dataclass
class GameSnapshot:
    """Read-only view of game state for rendering."""
    phase: GamePhase
    quarter: int = 1
    turn: int = 0
    turns_in_quarter: int = 6
    ball_pos: str = "1"

    human: Optional[Team] = None
    ai: Optional[Team] = None
    offense: Optional[Team] = None
    defense: Optional[Team] = None

    off_card: Optional[Card] = None
    def_card: Optional[Card] = None
    war_card: Optional[Card] = None
    clutch_card: Optional[Card] = None

    movement: int = 0
    new_pos: str = ""
    is_td: bool = False
    is_safety: bool = False

    extra_pts: int = 0
    extra_pts_desc: str = ""
    extra_pt_roll: int = 0

    fg_success: bool = False
    fg_roll: int = 0
    fg_total: int = 0
    fg_target: int = 0

    punt_distance: int = 0
    punt_roll: int = 0

    log_messages: List[str] = field(default_factory=list)
    message: str = ""

    # Post-move options available
    can_clutch: bool = False
    can_fg: bool = False
    can_punt: bool = True
    can_short_punt: bool = False
