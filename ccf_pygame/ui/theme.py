"""Broadcast UI design tokens."""

BG = (11, 14, 19)
PANEL = (21, 26, 34)
PANEL_HI = (29, 36, 47)
BORDER = (46, 55, 69)
TEXT = (234, 239, 246)
MUTED = (140, 152, 170)
DIM = (95, 106, 122)
GOLD = (250, 204, 21)
RED = (226, 62, 62)
SILVER = (198, 208, 224)
GREEN_OK = (52, 199, 123)
ORANGE = (255, 138, 32)

FIELD_TOP = (30, 104, 51)
FIELD_BOT = (18, 68, 34)
ENDZONE = (15, 52, 27)
CARD_FACE = (247, 248, 251)
CARD_INK = (24, 28, 36)
CARD_RED = (200, 40, 48)

BONUS = {
    "yellow": (240, 200, 60),
    "orange": (245, 145, 40),
    "green": (60, 200, 110),
}

PANEL_RADIUS = 12
BUTTON_RADIUS = 10


def team_color(team):
    """Return the legible Broadcast accent for a team."""
    if team is not None and team.color.value == "red":
        return RED
    return SILVER
