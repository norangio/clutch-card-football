"""Player hand display with card selection."""

import pygame
from ui.colors import *
from ui.font import get_font
from ccf.models import Card, Color


class CardHand:
    def __init__(self):
        self.font = get_font(12)
        self.small_font = get_font(10)
        self.selected = 0
        self._cards = []
        self._selectable = False
        self._ai_card_count = 0

    def update(self, hand: list[Card], selectable: bool, ai_count: int = 0):
        self._cards = hand
        self._selectable = selectable
        self._ai_card_count = ai_count
        if self.selected >= len(hand):
            self.selected = max(0, len(hand) - 1)

    def handle_event(self, event: pygame.event.Event) -> int | None:
        """Returns selected card index or None."""
        if not self._selectable or not self._cards:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w, pygame.K_k, pygame.K_KP8):
                self.selected = max(0, self.selected - 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_j, pygame.K_KP2):
                self.selected = min(len(self._cards) - 1, self.selected + 1)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.selected
            elif event.unicode and event.unicode.isdigit():
                idx = int(event.unicode)
                if 0 <= idx < len(self._cards):
                    self.selected = idx
                    return idx
        return None

    def handle_click(self, pos, area_rect: pygame.Rect) -> int | None:
        if not self._selectable or not self._cards:
            return None
        x, y = pos
        if not area_rect.collidepoint(x, y):
            return None
        rel_y = y - area_rect.y - 45
        card_h = 27
        idx = rel_y // card_h
        if 0 <= idx < len(self._cards):
            self.selected = idx
            return idx
        return None

    def draw(self, surface: pygame.Surface, x: int, y: int, w: int, h: int):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, BG_PANEL, rect)
        pygame.draw.rect(surface, SCORE_BORDER, rect, 1)

        # Header
        header_text = "YOUR HAND" if self._selectable else "HAND"
        header = self.font.render(header_text, True, AMBER)
        surface.blit(header, (x + 9, y + 9))

        # Cards
        card_y = y + 36
        for i, card in enumerate(self._cards):
            is_sel = (i == self.selected and self._selectable)
            card_color = CARD_RED if card.color and card.color == Color.RED else CARD_BLACK
            if card.value == "Joker":
                card_color = HIGHLIGHT

            prefix = ">" if is_sel else " "
            text = f"{prefix}{i}: {card.display}"
            color = CARD_SELECTED if is_sel else card_color
            ct = self.font.render(text, True, color)
            surface.blit(ct, (x + 9, card_y))
            card_y += 27

        # AI card count
        ai_y = y + h - 36
        ai_text = self.font.render(f"AI: {self._ai_card_count}", True, DIM_TEXT)
        surface.blit(ai_text, (x + 9, ai_y))
