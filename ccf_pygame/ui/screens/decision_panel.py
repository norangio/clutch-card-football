from __future__ import annotations

"""Post-move decision buttons: Punt, FG, Clutch, Short Punt. Also extra point choice."""

import pygame
from ui.colors import *
from ui.font import get_font
from ui.keycodes import K, ONE, TWO, THREE, FOUR


class DecisionPanel:
    BUTTONS = [
        {"key": "P", "label": "PUNT", "shortcut": ONE},
        {"key": "F", "label": "FIELD GOAL", "shortcut": TWO},
        {"key": "C", "label": "CLUTCH", "shortcut": THREE},
        {"key": "S", "label": "SHORT PUNT", "shortcut": FOUR},
    ]

    EP_BUTTONS = [
        {"key": "K", "label": "KICK ", "shortcut": K},
        {"key": "2", "label": "GO FOR 2 (d6>=5)", "shortcut": TWO},
    ]

    # Map ball positions to context descriptions
    POS_CONTEXT = {
        "1": "Ball at OWN 1",
        "2": "Ball at OWN 2",
        "3": "Ball at OWN 3",
        "Z3": "Ball in RED ZONE (Z3) -- FG available!",
        "Z2": "Ball in RED ZONE (Z2) -- FG available!",
        "Z1": "Ball in RED ZONE (Z1) -- FG available!",
    }

    def __init__(self):
        self.font = get_font(12)
        self.context_font = get_font(10)
        self._active = False
        self._ep_choice_active = False
        self._can_punt = True
        self._can_fg = False
        self._can_clutch = False
        self._can_short = False
        self._hover = -1
        self._btn_rects: list[pygame.Rect] = []
        self._ball_pos = "1"

    def update(self, can_punt: bool, can_fg: bool, can_clutch: bool, can_short: bool,
               active: bool, ball_pos: str = "1", ep_choice_active: bool = False):
        self._can_punt = can_punt
        self._can_fg = can_fg
        self._can_clutch = can_clutch
        self._can_short = can_short
        self._active = active
        self._ball_pos = ball_pos
        self._ep_choice_active = ep_choice_active

    def _is_enabled(self, key: str) -> bool:
        return {
            "P": self._can_punt,
            "F": self._can_fg,
            "C": self._can_clutch,
            "S": self._can_short,
        }.get(key, False)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self._ep_choice_active:
            if event.type == pygame.KEYDOWN:
                for btn in self.EP_BUTTONS:
                    if event.key == btn["shortcut"]:
                        return btn["key"]
            return None
        if not self._active:
            return None
        if event.type == pygame.KEYDOWN:
            for btn in self.BUTTONS:
                if event.key == btn["shortcut"] and self._is_enabled(btn["key"]):
                    return btn["key"]
        return None

    def handle_click(self, pos) -> str | None:
        if self._ep_choice_active:
            for i, rect in enumerate(self._btn_rects):
                if rect.collidepoint(pos):
                    return self.EP_BUTTONS[i]["key"]
            return None
        if not self._active:
            return None
        for i, rect in enumerate(self._btn_rects):
            if rect.collidepoint(pos) and self._is_enabled(self.BUTTONS[i]["key"]):
                return self.BUTTONS[i]["key"]
        return None

    def draw(self, surface: pygame.Surface, x: int, y: int, w: int, h: int):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, BG_PANEL, rect)
        pygame.draw.rect(surface, SCORE_BORDER, rect, 1)

        if self._ep_choice_active:
            self._draw_ep_choice(surface, x, y, w, h)
            return

        if not self._active:
            return

        # Context line showing field position
        context = self.POS_CONTEXT.get(self._ball_pos, f"Ball at {self._ball_pos}")
        if self._can_clutch:
            context += " | Clutch available"
        ctx_surf = self.context_font.render(context, True, HIGHLIGHT)
        surface.blit(ctx_surf, (x + 12, y + 6))

        header = self.font.render("CHOOSE ACTION:", True, AMBER)
        surface.blit(header, (x + 12, y + 24))

        self._btn_rects.clear()
        btn_x = x + 12
        btn_y = y + 44
        btn_w = (w - 36) // 4

        for i, btn in enumerate(self.BUTTONS):
            enabled = self._is_enabled(btn["key"])
            br = pygame.Rect(btn_x, btn_y, btn_w - 6, 22)
            self._btn_rects.append(br)

            if enabled:
                pygame.draw.rect(surface, BUTTON_BG, br)
                pygame.draw.rect(surface, BUTTON_BORDER, br, 1)
                label_color = AMBER
            else:
                pygame.draw.rect(surface, BG_DARK, br)
                label_color = DIM_TEXT

            shortcut = str(i + 1)
            label = self.font.render(f"{shortcut}:{btn['label']}", True, label_color)
            surface.blit(label, (btn_x + 6, btn_y + 3))
            btn_x += btn_w

    def _draw_ep_choice(self, surface: pygame.Surface, x: int, y: int, w: int, h: int):
        header = self.font.render("EXTRA POINT — CHOOSE:", True, AMBER)
        surface.blit(header, (x + 12, y + 8))

        self._btn_rects.clear()
        btn_w = (w - 36) // 2
        btn_x = x + 12
        btn_y = y + 36

        for i, btn in enumerate(self.EP_BUTTONS):
            br = pygame.Rect(btn_x, btn_y, btn_w - 6, 26)
            self._btn_rects.append(br)
            pygame.draw.rect(surface, BUTTON_BG, br)
            pygame.draw.rect(surface, BUTTON_BORDER, br, 1)
            label = self.font.render(f"[{btn['key']}] {btn['label']}", True, HIGHLIGHT)
            surface.blit(label, (btn_x + 8, btn_y + 5))
            btn_x += btn_w
