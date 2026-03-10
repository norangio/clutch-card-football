"""Game rules: bonus, extra points, field goals, punts."""

import random
from typing import Tuple

from .models import Card, Color

TABLE_FG = {1: [65, 75, 85], 2: [70, 80, 90], 3: [75, 85, 90]}
FG_SUCCESS = {"Z3": 7, "Z2": 5, "Z1": 4}


def apply_bonus(base: int, bonus: str, card: Card, team_color: Color, end_pos: str) -> Tuple[int, bool]:
    extra = 0
    auto_td = False
    if card.color == team_color:
        if bonus == "yellow":
            extra += 1
        elif bonus == "orange" and end_pos == "Z1":
            auto_td = True
        elif bonus == "green":
            extra += 1
            if end_pos == "Z1":
                auto_td = True
    return extra, auto_td


def pat_kick() -> Tuple[int, str]:
    """PAT kick — ."""
    roll = random.randint(1, 6)
    if (roll > 1):
        return 1, "PAT KICK! +1 pt"
    else:
        return 0, "PAT KICK Missed !"


def two_point_attempt() -> Tuple[int, int, str]:
    """2-point conversion attempt. Returns (points, roll, description)."""
    roll = random.randint(1, 6)
    if roll >= 5:
        return 2, roll, f"2PT! Rolled {roll} (need 5+) → +2 pts!"
    return 0, roll, f"2PT failed. Rolled {roll} (need 5+) → 0 pts"


def field_goal_attempt(kick_rating: int, pos: str) -> Tuple[bool, int, int, int]:
    """Attempt a FG. Returns (success, roll, total, target)."""
    target = FG_SUCCESS.get(pos, 99)
    roll = random.randint(1, 6)
    total = kick_rating + roll
    return total >= target, roll, total, target


def punt_distance(kick_rating: int) -> Tuple[int, int]:
    """Calculate punt distance. Returns (total_distance, roll)."""
    roll = random.randint(1, 6)
    if roll == 2:
        roll = 1
    elif (roll == 4) or ( roll == 3):
        roll = 2
    elif (roll == 6) or (roll == 5):
        roll = 3
    
    return kick_rating + roll, roll


def short_punt_distance(kick_rating: int) -> int:
    return 3 - kick_rating + random.randint(0, 2)
