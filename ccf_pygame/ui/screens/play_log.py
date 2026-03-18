from __future__ import annotations

"""Scrolling play-by-play text log."""

import pygame
from ui.colors import *
from ui.font import get_font


class PlayLog:
    def __init__(self):
        self.font = get_font(10)
        self._max_visible = 12

    def draw(self, surface: pygame.Surface, messages: list[str],
             x: int, y: int, w: int, h: int):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, BG_PANEL, rect)
        pygame.draw.rect(surface, SCORE_BORDER, rect, 1)

        header = self.font.render("PLAY LOG", True, AMBER)
        surface.blit(header, (x + 9, y + 6))

        visible = messages[-self._max_visible:]
        line_y = y + 26
        for msg in visible:
            display = msg[:80]
            text = self.font.render(f"> {display}", True, GRAY)
            surface.blit(text, (x + 9, line_y))
            line_y += 18
