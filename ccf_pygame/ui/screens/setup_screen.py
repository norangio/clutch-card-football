"""Broadcast team setup screen with mouse and keyboard controls."""

import pygame

from ui import draw as d
from ui.layout import W
from ui.theme import BG, BORDER, DIM, GOLD, MUTED, PANEL, PANEL_HI, TEXT


class SetupScreen:
    COLUMN = pygame.Rect(200, 84, 560, 484)
    ROW_H = 38
    ROW_STEP = 44
    START_RECT = pygame.Rect(370, 584, 220, 48)

    def __init__(self):
        self.fields = [
            {"label": "TEAM NAME", "value": "Bulldogs", "type": "text"},
            {"label": "RATING", "value": "6", "type": "int", "min": 1, "max": 12},
            {"label": "KICK RATING", "value": "2", "type": "int", "min": 1, "max": 3},
            {"label": "COLOR", "value": "RED", "type": "choice", "choices": ["RED", "BLACK"]},
            {"label": "CLUTCH", "value": "3", "type": "int", "min": 0, "max": 5},
            {"label": "AI NAME", "value": "Rivals", "type": "text"},
            {"label": "AI RATING", "value": "6", "type": "int", "min": 1, "max": 12},
            {"label": "AI KICK", "value": "2", "type": "int", "min": 1, "max": 3},
            {"label": "AI CLUTCH", "value": "3", "type": "int", "min": 0, "max": 5},
            {"label": "AI DIFFICULTY", "value": "MEDIUM", "type": "choice",
             "choices": ["EASY", "MEDIUM", "HARD"]},
            {"label": "MODE", "value": "HUMAN vs AI", "type": "choice",
             "choices": ["HUMAN vs AI", "AI vs AI"]},
        ]
        self.selected = 0
        self.cursor_blink = 0
        self.ready = False
        self._result = None
        self._row_rects = [
            pygame.Rect(self.COLUMN.x, self.COLUMN.y + index * self.ROW_STEP,
                        self.COLUMN.w, self.ROW_H)
            for index in range(len(self.fields))
        ]
        self._left_rects = [pygame.Rect(row.right - 170, row.y, 38, row.h)
                            for row in self._row_rects]
        self._right_rects = [pygame.Rect(row.right - 38, row.y, 38, row.h)
                             for row in self._row_rects]

    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_TAB, pygame.K_DOWN):
            self.selected = (self.selected + 1) % (len(self.fields) + 1)
        elif event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % (len(self.fields) + 1)
        elif event.key == pygame.K_RETURN:
            if self.selected == len(self.fields):
                self._submit()
        else:
            self._edit_field(event)

    def _adjust(self, field, direction):
        if field["type"] == "int":
            value = int(field["value"]) + direction
            field["value"] = str(max(field["min"], min(field["max"], value)))
        elif field["type"] == "choice":
            choices = field["choices"]
            index = choices.index(field["value"])
            field["value"] = choices[(index + direction) % len(choices)]

    def _edit_field(self, event):
        if self.selected >= len(self.fields):
            return
        field = self.fields[self.selected]
        if field["type"] == "text":
            if event.key == pygame.K_BACKSPACE:
                field["value"] = field["value"][:-1]
            elif (event.unicode and event.unicode.isascii()
                  and event.unicode.isprintable()
                  and len(field["value"]) < 12):
                field["value"] += event.unicode
        elif event.key == pygame.K_LEFT:
            self._adjust(field, -1)
        elif event.key in (pygame.K_RIGHT, pygame.K_SPACE):
            self._adjust(field, 1)
        elif field["type"] == "int" and event.unicode.isdigit():
            # Keep the original single-key quick entry behavior.
            value = int(event.unicode)
            if field["min"] <= value <= field["max"]:
                field["value"] = str(value)

    def _submit(self):
        from ccf.models import Color
        self._result = {
            "human_name": self.fields[0]["value"] or "Player",
            "human_rating": int(self.fields[1]["value"]),
            "human_kick": int(self.fields[2]["value"]),
            "human_color": (Color.RED if self.fields[3]["value"] == "RED"
                            else Color.BLACK),
            "human_clutch": int(self.fields[4]["value"]),
            "ai_name": self.fields[5]["value"] or "Rivals",
            "ai_rating": int(self.fields[6]["value"]),
            "ai_kick": int(self.fields[7]["value"]),
            "ai_clutch": int(self.fields[8]["value"]),
            "difficulty": self.fields[9]["value"].lower(),
            "ai_vs_ai": self.fields[10]["value"] == "AI vs AI",
        }
        self.ready = True

    def get_result(self):
        return self._result

    def handle_click(self, pos):
        if self.START_RECT.collidepoint(pos):
            self.selected = len(self.fields)
            self._submit()
            return
        for index, row in enumerate(self._row_rects):
            if not row.collidepoint(pos):
                continue
            self.selected = index
            field = self.fields[index]
            if field["type"] in ("int", "choice"):
                if self._left_rects[index].collidepoint(pos):
                    self._adjust(field, -1)
                elif self._right_rects[index].collidepoint(pos):
                    self._adjust(field, 1)
            return

    def draw(self, surface: pygame.Surface):
        surface.fill(BG)
        self.cursor_blink = (self.cursor_blink + 1) % 60
        d.text(surface, "CLUTCH CARD FOOTBALL", (W // 2, 36),
               d.font("cond", 42, "bold"), GOLD,
               anchor="center", tracking=1, tight=True)
        d.text(surface, "TEAM SETUP", (W // 2, 66),
               d.font("inter", 10, "bold"), DIM,
               anchor="center", tracking=3, tight=True)

        for index, (field, row) in enumerate(zip(self.fields, self._row_rects)):
            selected = index == self.selected
            d.rrect(surface, row, PANEL_HI if selected else PANEL, radius=8)
            d.rrect(surface, row, GOLD if selected else BORDER,
                    radius=8, width=1)
            d.text(surface, field["label"], (row.x + 16, row.centery),
                   d.font("inter", 13, "semibold"), MUTED,
                   anchor="midleft", tight=True)

            value = field["value"]
            if (field["type"] == "text" and selected
                    and self.cursor_blink < 30):
                value += "_"
            if field["type"] in ("int", "choice"):
                chevron_color = GOLD if selected else DIM
                d.chevron(surface, self._left_rects[index].centerx + 4,
                          self._left_rects[index].centery, 6,
                          chevron_color, direction=-1, width=2)
                d.chevron(surface, self._right_rects[index].centerx - 4,
                          self._right_rects[index].centery, 6,
                          chevron_color, direction=1, width=2)
                value_center = ((self._left_rects[index].right
                                 + self._right_rects[index].left) // 2,
                                row.centery)
                d.text(surface, value, value_center,
                       d.font("inter", 15, "bold"), TEXT,
                       anchor="center", tight=True)
            else:
                d.text(surface, value, (row.right - 16, row.centery),
                       d.font("inter", 15, "bold"), TEXT,
                       anchor="midright", tight=True)

        selected_start = self.selected == len(self.fields)
        if selected_start:
            d.shadow(surface, self.START_RECT, radius=10, spread=8,
                     a=100, offset=(0, 3))
        d.rrect(surface, self.START_RECT, GOLD, radius=10)
        d.rrect(surface, self.START_RECT,
                TEXT if selected_start else d.shade(GOLD, -0.18),
                radius=10, width=2 if selected_start else 1)
        d.text(surface, "START GAME", self.START_RECT.center,
               d.font("cond", 24, "bold"), (26, 22, 6),
               anchor="center", tracking=1, tight=True)
        d.text(surface,
               "TAB / ↑ ↓ navigate  ·  LEFT / RIGHT edit  ·  ENTER start",
               (W // 2, 674), d.font("inter", 11, "regular"), DIM,
               anchor="center", tight=True)
