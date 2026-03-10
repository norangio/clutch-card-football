"""Field segment movement logic."""

from typing import Tuple

SEGMENTS = ["0", "1", "2", "3", "Z3", "Z2", "Z1"]


def move(pos: str, dist: int) -> Tuple[str, bool, bool]:
    """Move the ball on the field.

    Returns (new_position, is_touchdown, is_safety).
    """
    idx = SEGMENTS.index(str(pos))
    new_idx = idx + dist
    td = False
    safety = False
    if new_idx >= len(SEGMENTS):
        td = True
        new_idx = 1
    elif new_idx < 1:
        safety = True
        new_idx = 3
    return SEGMENTS[new_idx], td, safety
