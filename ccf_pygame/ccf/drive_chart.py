"""Drive chart — maps (rating, card) to movement yards."""


SUIT_TO_COLOR = {
    "H": "red", "D": "red", "S": "black", "C": "black",
}

DRIVE_CHART = {
    "1": {
        "2": {"base": -1}, "3": {"base": 0}, "4": {"base": 1},
        "5": {"base": 1, "bonus": "yellow"}, "6": {"base": 2}, "7": {"base": 2},
        "8": {"base": 2}, "9": {"base": 2}, "10": {"base": 2, "bonus": "yellow"},
        "J": {"base": 3}, "Q": {"base": 3}, "K": {"base": 3}, "A": {"base": 4},
    },
    "2": {
        "2": {"base": -1}, "3": {"base": 0}, "4": {"base": 1, "bonus": "yellow"},
        "5": {"base": 2}, "6": {"base": 2}, "7": {"base": 2},
        "8": {"base": 2}, "9": {"base": 2}, "10": {"base": 2, "bonus": "yellow"},
        "J": {"base": 3}, "Q": {"base": 3}, "K": {"base": 3}, "A": {"base": 4},
    },
    "3": {
        "2": {"base": 0}, "3": {"base": 0}, "4": {"base": 1, "bonus": "yellow"},
        "5": {"base": 2}, "6": {"base": 2}, "7": {"base": 2},
        "8": {"base": 2}, "9": {"base": 2, "bonus": "yellow"}, "10": {"base": 3},
        "J": {"base": 3}, "Q": {"base": 3}, "K": {"base": 3}, "A": {"base": 4},
    },
    "4": {
        "2": {"base": 0}, "3": {"base": 0}, "4": {"base": 1, "bonus": "yellow"},
        "5": {"base": 2}, "6": {"base": 2}, "7": {"base": 2},
        "8": {"base": 2, "bonus": "yellow"}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3}, "Q": {"base": 3}, "K": {"base": 3}, "A": {"base": 4},
    },
    "5": {
        "2": {"base": 0}, "3": {"base": 1}, "4": {"base": 1, "bonus": "yellow"},
        "5": {"base": 2}, "6": {"base": 2}, "7": {"base": 2},
        "8": {"base": 2, "bonus": "yellow"}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3}, "Q": {"base": 3, "bonus": "yellow"}, "K": {"base": 4},
        "A": {"base": 4, "bonus": "orange"},
    },
    "6": {
        "2": {"base": 0}, "3": {"base": 1}, "4": {"base": 1, "bonus": "yellow"},
        "5": {"base": 2}, "6": {"base": 2}, "7": {"base": 2, "bonus": "yellow"},
        "8": {"base": 3}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3}, "Q": {"base": 3, "bonus": "yellow"}, "K": {"base": 4},
        "A": {"base": 4, "bonus": "orange"},
    },
    "7": {
        "2": {"base": 0}, "3": {"base": 1}, "4": {"base": 1, "bonus": "yellow"},
        "5": {"base": 2}, "6": {"base": 2, "bonus": "yellow"}, "7": {"base": 3},
        "8": {"base": 3}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3}, "Q": {"base": 3, "bonus": "yellow"}, "K": {"base": 4},
        "A": {"base": 4, "bonus": "green"},
    },
    "8": {
        "2": {"base": 0}, "3": {"base": 1}, "4": {"base": 1, "bonus": "yellow"},
        "5": {"base": 2}, "6": {"base": 2, "bonus": "yellow"}, "7": {"base": 3},
        "8": {"base": 3}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3, "bonus": "yellow"}, "Q": {"base": 4}, "K": {"base": 4},
        "A": {"base": 4, "bonus": "green"},
    },
    "9": {
        "2": {"base": 0}, "3": {"base": 1}, "4": {"base": 1, "bonus": "yellow"},
        "5": {"base": 2}, "6": {"base": 2, "bonus": "yellow"}, "7": {"base": 3},
        "8": {"base": 3}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3, "bonus": "yellow"}, "Q": {"base": 4},
        "K": {"base": 4, "bonus": "yellow"}, "A": {"base": 5, "bonus": "orange"},
    },
    "10": {
        "2": {"base": 0}, "3": {"base": 1, "bonus": "yellow"}, "4": {"base": 2},
        "5": {"base": 2}, "6": {"base": 2, "bonus": "yellow"}, "7": {"base": 3},
        "8": {"base": 3}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3, "bonus": "yellow"}, "Q": {"base": 4},
        "K": {"base": 4, "bonus": "yellow"}, "A": {"base": 5, "bonus": "orange"},
    },
    "11": {
        "2": {"base": 1}, "3": {"base": 1, "bonus": "yellow"}, "4": {"base": 2},
        "5": {"base": 2}, "6": {"base": 2, "bonus": "yellow"}, "7": {"base": 3},
        "8": {"base": 3}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3, "bonus": "yellow"}, "Q": {"base": 4},
        "K": {"base": 4, "bonus": "yellow"}, "A": {"base": 5, "bonus": "green"},
    },
    "12": {
        "2": {"base": 1, "bonus": "yellow"}, "3": {"base": 2}, "4": {"base": 2},
        "5": {"base": 2}, "6": {"base": 2, "bonus": "yellow"}, "7": {"base": 3},
        "8": {"base": 3}, "9": {"base": 3}, "10": {"base": 3},
        "J": {"base": 3, "bonus": "yellow"}, "Q": {"base": 4},
        "K": {"base": 4, "bonus": "yellow"}, "A": {"base": 5, "bonus": "green"},
    },
}


def get_card_color(suit: str) -> str | None:
    return SUIT_TO_COLOR.get(suit)


def get_card_result(team_color_str: str, rating: int, card_str: str) -> int:
    """Get movement from drive chart for a card string like '7H' or 'KS'."""
    card_value = card_str[:-1]
    card_suit = card_str[-1]
    return get_drive_result(team_color_str, rating, card_value, card_suit)


def get_drive_result(color: str, rate: int, card_value: str, card_suit: str = None) -> int:
    """Returns the final movement segments for a play."""
    color_str = str(color).lower()
    dice_str = str(rate)
    card_str = str(card_value).upper()

    entry = DRIVE_CHART.get(dice_str, {}).get(card_str)
    if not entry:
        return 0

    base_yards = entry["base"]
    bonus_type = entry.get("bonus")

    if not bonus_type or not card_suit:
        return base_yards

    card_color = get_card_color(card_suit)
    if card_color is None:
        return base_yards

    if card_color != color_str:
        return base_yards

    if bonus_type == "yellow":
        return base_yards + 1
    elif bonus_type == "orange":
        return base_yards  # orange bonus is auto-TD at Z1, handled elsewhere
    elif bonus_type == "green":
        return base_yards + 1  # green = +1 and Z1 auto-TD, handled elsewhere
    return base_yards
