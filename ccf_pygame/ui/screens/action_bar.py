"""Context prompts and playable action buttons."""

import pygame

from ccf.states import GamePhase
from ui import draw as d
from ui.layout import ACTION_H, ACTION_Y, W
from ui.theme import BORDER, DIM, GOLD, MUTED, PANEL, PANEL_HI, TEXT


class ActionBar:
    POST_SPECS = [
        ("PUNT", "1", "P", "can_punt"),
        ("FIELD GOAL", "2", "F", "can_fg"),
        ("CLUTCH", "3", "C", "can_clutch"),
        ("SHORT PUNT", "4", "S", "can_short_punt"),
    ]
    EXTRA_SPECS = [
        ("KICK PAT", "K", "K"),
        ("GO FOR 2  ·  d6 ≥ 5", "2", "2"),
    ]

    def __init__(self):
        self._phase = None
        self._buttons: list[tuple[pygame.Rect, str, bool]] = []

    @staticmethod
    def _button(surface, rect, label, key, enabled, primary=False):
        if enabled:
            base = GOLD if primary else PANEL_HI
            d.rrect(surface, rect, base, radius=10)
            d.rrect(surface, rect,
                    d.shade(base, 0.22 if primary else 0.10),
                    radius=10, width=1)
            ink = (26, 22, 6) if primary else TEXT
            key_color = d.alpha((26, 22, 6), 150) if primary else DIM
        else:
            d.rrect(surface, rect, (18, 22, 29), radius=10)
            d.rrect(surface, rect, (34, 40, 51), radius=10, width=1)
            ink, key_color = (74, 82, 96), (58, 65, 78)
        d.text(surface, label, rect.center, d.font("cond", 22, "bold"), ink,
               anchor="center", tracking=1, tight=True)
        d.text(surface, key, (rect.right - 10, rect.y + 8),
               d.font("inter", 9, "bold"), key_color,
               anchor="topright", tight=True)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        if self._phase == GamePhase.WAITING_POST_MOVE:
            key_map = {
                pygame.K_1: "P",
                pygame.K_2: "F",
                pygame.K_3: "C",
                pygame.K_4: "S",
            }
            choice = key_map.get(event.key)
            for _, button_choice, enabled in self._buttons:
                if choice == button_choice and enabled:
                    return choice
        elif self._phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            if event.key == pygame.K_k:
                return "K"
            if event.key == pygame.K_2:
                return "2"
        return None

    def handle_click(self, pos):
        for rect, choice, enabled in self._buttons:
            if enabled and rect.collidepoint(pos):
                return choice
        return None

    def draw(self, surface, snap):
        self._phase = snap.phase
        self._buttons.clear()
        d.grad_rect(surface, (0, ACTION_Y, W, ACTION_H),
                    PANEL, (14, 18, 24))
        pygame.draw.line(surface, BORDER, (0, ACTION_Y), (W, ACTION_Y))

        if snap.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            d.text(surface, "EXTRA POINT", (20, ACTION_Y + 16),
                   d.font("inter", 10, "bold"), DIM,
                   tracking=2, tight=True)
            button_w = (W - 40 - 14) // 2
            for index, (label, key, choice) in enumerate(self.EXTRA_SPECS):
                rect = pygame.Rect(20 + index * (button_w + 14),
                                   ACTION_Y + 30, button_w, 42)
                self._buttons.append((rect, choice, True))
                self._button(surface, rect, label, key, True,
                             primary=index == 0)
            return

        if snap.phase == GamePhase.WAITING_POST_MOVE:
            context = f"BALL AT {snap.ball_pos}"
            if snap.can_fg:
                context += "   ·   RED ZONE — FIELD GOAL AVAILABLE"
            d.text(surface, context, (20, ACTION_Y + 16),
                   d.font("inter", 10, "bold"),
                   GOLD if snap.can_fg else DIM, tracking=2, tight=True)
            button_w = (W - 40 - 3 * 12) // 4
            for index, (label, key, choice, flag) in enumerate(self.POST_SPECS):
                enabled = bool(getattr(snap, flag))
                rect = pygame.Rect(20 + index * (button_w + 12),
                                   ACTION_Y + 30, button_w, 42)
                self._buttons.append((rect, choice, enabled))
                self._button(surface, rect, label, key, enabled,
                             primary=label == "FIELD GOAL" and enabled)
            return

        if snap.phase in (GamePhase.WAITING_OFFENSE_CARD,
                          GamePhase.WAITING_DEFENSE_CARD):
            d.text(surface, "SELECT A CARD", (20, ACTION_Y + 16),
                   d.font("inter", 10, "bold"), GOLD,
                   tracking=2, tight=True)
            d.text(surface,
                   "Click a card, or press 0–9  ·  ↑ ↓ to move, ENTER to play",
                   (20, ACTION_Y + 36), d.font("inter", 13, "regular"), MUTED)
            return

        if snap.phase in (GamePhase.AI_PLAYING_CARD, GamePhase.AI_POST_MOVE):
            label = "AI TURN"
            hint = "The opponent is choosing..."
        else:
            label = "GAME IN PROGRESS"
            hint = "Click or press any key to continue"
        d.text(surface, label, (20, ACTION_Y + 16),
               d.font("inter", 10, "bold"), DIM,
               tracking=2, tight=True)
        d.text(surface, hint, (20, ACTION_Y + 36),
               d.font("inter", 13, "regular"), MUTED)
