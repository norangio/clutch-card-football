from __future__ import annotations

"""Offense vs Defense card comparison display."""

import pygame
from ui.colors import *
from ui.font import get_font
from ccf.models import Card, Color


class CardBattle:
    def __init__(self):
        self.font = get_font(12)
        self.big_font = get_font(16)
        self.detail_font = get_font(10)

    def draw(self, surface: pygame.Surface, off_card: Card | None, def_card: Card | None,
             off_name: str, def_name: str, x: int, y: int, w: int, h: int,
             message: str = ""):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, BG_PANEL, rect)
        pygame.draw.rect(surface, SCORE_BORDER, rect, 1)

        if off_card is None and def_card is None and not message:
            return

        if message:
            msg_surf = self.font.render(message, True, HIGHLIGHT)
            surface.blit(msg_surf, (x + w // 2 - msg_surf.get_width() // 2, y + h // 2 - 8))
            return

        # Draw card matchup
        mid = x + w // 2

        if off_card:
            off_color = CARD_RED if off_card.color and off_card.color == Color.RED else CARD_BLACK
            if off_card.value == "Joker":
                off_color = HIGHLIGHT
            off_label = self.font.render(f"OFF: {off_name}", True, AMBER)
            surface.blit(off_label, (mid - 210, y + 10))
            off_text = self.big_font.render(off_card.display, True, off_color)
            surface.blit(off_text, (mid - 210, y + 32))

        vs = self.font.render("vs", True, DIM_TEXT)
        surface.blit(vs, (mid - vs.get_width() // 2, y + 32))

        if def_card:
            def_color = CARD_RED if def_card.color and def_card.color == Color.RED else CARD_BLACK
            if def_card.value == "Joker":
                def_color = HIGHLIGHT
            def_label = self.font.render(f"DEF: {def_name}", True, AMBER)
            surface.blit(def_label, (mid + 60, y + 10))
            def_text = self.big_font.render(def_card.display, True, def_color)
            surface.blit(def_text, (mid + 60, y + 32))
