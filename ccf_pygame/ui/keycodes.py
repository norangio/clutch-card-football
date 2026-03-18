from __future__ import annotations

import pygame


def _code(name: str, fallback: int) -> int:
    return getattr(pygame, name, fallback)


RETURN = _code("K_RETURN", 13)
BACKSPACE = _code("K_BACKSPACE", 8)
SPACE = _code("K_SPACE", 32)

UP = _code("K_UP", -1)
DOWN = _code("K_DOWN", -1)
LEFT = _code("K_LEFT", -1)
RIGHT = _code("K_RIGHT", -1)

A = _code("K_a", ord("a"))
D = _code("K_d", ord("d"))
H = _code("K_h", ord("h"))
J = _code("K_j", ord("j"))
K = _code("K_k", ord("k"))
L = _code("K_l", ord("l"))
S = _code("K_s", ord("s"))
W = _code("K_w", ord("w"))

ONE = _code("K_1", ord("1"))
TWO = _code("K_2", ord("2"))
THREE = _code("K_3", ord("3"))
FOUR = _code("K_4", ord("4"))

KP2 = _code("K_KP2", -1)
KP4 = _code("K_KP4", -1)
KP6 = _code("K_KP6", -1)
KP8 = _code("K_KP8", -1)
