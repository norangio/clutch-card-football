"""Deck creation and card value helpers."""

import random
from collections import deque

from .models import Card


def create_deck() -> deque:
    values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    suits = ["H", "D", "S", "C"]
    deck = [Card(v, s) for v in values for s in suits]
    deck.extend([Card("Joker") for _ in range(3)])
    random.shuffle(deck)
    return deque(deck)


CARD_ORDER = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14,
}


def card_value(card: Card) -> int:
    if card.value == "Joker":
        return 15
    return CARD_ORDER[card.value]
