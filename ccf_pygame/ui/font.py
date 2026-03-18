from __future__ import annotations

"""Pixel font loader — Press Start 2P or fallback."""

import os
import pygame

_font_cache: dict[int, pygame.font.Font] = {}
_font_path: str | None = None


def _find_font() -> str | None:
    global _font_path
    if _font_path is not None:
        return _font_path

    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base, "assets", "fonts", "press_start_2p.ttf"),
        os.path.join(base, "assets", "fonts", "PressStart2P-Regular.ttf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            _font_path = path
            return _font_path
    _font_path = ""  # empty string = not found, use fallback
    return _font_path


def get_font(size: int = 8) -> pygame.font.Font:
    if size in _font_cache:
        return _font_cache[size]

    path = _find_font()
    if path:
        font = pygame.font.Font(path, size)
    else:
        # Fallback to a monospace system font
        font = pygame.font.SysFont("courier", size + 4)

    _font_cache[size] = font
    return font
