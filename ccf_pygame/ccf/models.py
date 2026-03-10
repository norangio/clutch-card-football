"""Core data models for Clutch Card Football."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Color(Enum):
    RED = "red"
    BLACK = "black"


@dataclass
class Card:
    value: str
    suit: Optional[str] = None
    color: Optional[Color] = None

    def __post_init__(self):
        if self.value == "Joker":
            self.color = None
        elif self.suit in ("H", "D"):
            self.color = Color.RED
        elif self.suit in ("S", "C"):
            self.color = Color.BLACK

    def __str__(self):
        return f"{self.value}{self.suit}" if self.suit else "JOKER"

    @property
    def display_suit(self) -> str:
        suit_map = {"H": "\u2665", "D": "\u2666", "S": "\u2660", "C": "\u2663"}
        if self.suit:
            return suit_map.get(self.suit, self.suit)
        return ""

    @property
    def display(self) -> str:
        if self.value == "Joker":
            return "JOKER"
        return f"{self.value}{self.display_suit}"


@dataclass
class Team:
    name: str
    rating: int
    kick_rating: int
    color: Color
    clutch: int
    clutch_used: bool = False
    mojo: int = 0
    hand: List[Card] = field(default_factory=list)
    score: int = 0

    def play(self, idx: int) -> Card:
        return self.hand.pop(idx)
