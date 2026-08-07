"""Two-column playable card hand rail."""

import pygame

from ccf.states import GamePhase
from ui import draw as d
from ui.layout import HAND_RECT
from ui.theme import (BORDER, CARD_FACE, CARD_INK, CARD_RED, DIM, GOLD,
                      MUTED, PANEL)


def draw_card_face(surface, rect, card, selected=False, index=None, scale=1.0):
    rect = pygame.Rect(rect)
    if selected:
        d.shadow(surface, rect, radius=8, spread=10, a=150, offset=(0, 5))

    is_joker = card.value == "Joker"
    face = (253, 246, 214) if is_joker else CARD_FACE
    d.rrect(surface, rect, face, radius=8)
    if selected:
        d.rrect(surface, rect.inflate(6, 6), GOLD, radius=11, width=3)
    else:
        d.rrect(surface, rect, (206, 212, 226), radius=8, width=1)

    if is_joker:
        d.text(surface, "JOKER", rect.center,
               d.font("cond", int(22 * scale), "bold"), (150, 92, 12),
               anchor="center", tracking=1, tight=True)
    else:
        ink = CARD_RED if card.color and card.color.value == "red" else CARD_INK
        d.text(surface, card.value, (rect.x + 9, rect.y + 9),
               d.font("inter", int(21 * scale), "bold"), ink, tight=True)
        d.suit(surface, card.suit,
               (rect.right - 24 * scale, rect.centery + 6 * scale),
               30 * scale, ink)

    if index is not None:
        chip = pygame.Rect(rect.x + 6, rect.bottom - 20, 16, 14)
        d.rrect(surface, chip, (222, 227, 238), radius=4)
        d.text(surface, str(index), chip.center,
               d.font("inter", 9, "bold"), (110, 118, 134),
               anchor="center", tight=True)


class HandRail:
    def __init__(self):
        self.selected = 0
        self._cards = []
        self._opponent_count = 0
        self._active = False
        self._phase = None
        self._card_rects: list[pygame.Rect] = []

    @property
    def card_rects(self):
        return tuple(self._card_rects)

    def update(self, snap):
        self._cards = list(snap.human.hand) if snap.human else []
        self._opponent_count = len(snap.ai.hand) if snap.ai else 0
        self._phase = snap.phase
        self._active = snap.phase in (
            GamePhase.WAITING_OFFENSE_CARD,
            GamePhase.WAITING_DEFENSE_CARD,
        )
        if self.selected >= len(self._cards):
            self.selected = max(0, len(self._cards) - 1)
        self._card_rects = self._layout_cards(len(self._cards))

    @staticmethod
    def _layout_cards(count):
        rect = HAND_RECT
        count_for_layout = max(1, count)
        rows = (count_for_layout + 1) // 2
        gap = 10
        y0 = rect.y + 50
        available = (rect.bottom - 40) - y0
        card_h = max(46, min(70,
                            (available - (rows - 1) * gap) // rows))
        card_w = (rect.w - 32 - 12) // 2
        x0 = rect.x + 16
        return [
            pygame.Rect(x0 + (index % 2) * (card_w + 12),
                        y0 + (index // 2) * (card_h + gap),
                        card_w, card_h)
            for index in range(count)
        ]

    def handle_event(self, event):
        if not self._active or not self._cards or event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_UP:
            self.selected = max(0, self.selected - 1)
        elif event.key == pygame.K_DOWN:
            self.selected = min(len(self._cards) - 1, self.selected + 1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return self.selected
        elif event.unicode and event.unicode.isdigit():
            index = int(event.unicode)
            if 0 <= index < len(self._cards):
                self.selected = index
                return index
        return None

    def handle_click(self, pos):
        if not self._active:
            return None
        for index, rect in enumerate(self._card_rects):
            if rect.collidepoint(pos):
                self.selected = index
                return index
        return None

    def draw(self, surface, snap):
        self.update(snap)
        rect = HAND_RECT
        d.rrect(surface, rect, PANEL, radius=12)
        d.rrect(surface, rect, BORDER, radius=12, width=1)

        title = ("PICK DEFENSE"
                 if self._phase == GamePhase.WAITING_DEFENSE_CARD
                 else "YOUR HAND")
        d.text(surface, title, (rect.x + 16, rect.y + 18),
               d.font("inter", 11, "bold"), GOLD if self._active else MUTED,
               tracking=2, tight=True)
        d.text(surface, str(len(self._cards)), (rect.right - 16, rect.y + 13),
               d.font("inter", 12, "bold"), DIM, anchor="topright")
        d.hairline(surface, rect.x + 14, rect.y + 38, rect.right - 14, BORDER)

        for index, (card, card_rect) in enumerate(zip(self._cards,
                                                      self._card_rects)):
            scale = 0.86 if card_rect.h < 60 else 1.0
            draw_card_face(surface, card_rect, card,
                           selected=self._active and index == self.selected,
                           index=index, scale=scale)

        footer = rect.bottom - 30
        d.hairline(surface, rect.x + 14, footer - 10,
                   rect.right - 14, BORDER)
        d.text(surface, "OPPONENT", (rect.x + 16, footer + 4),
               d.font("inter", 9, "bold"), DIM, tracking=1, tight=True)
        d.text(surface, f"{self._opponent_count} cards",
               (rect.right - 16, footer), d.font("inter", 10, "semibold"),
               MUTED, anchor="topright")
