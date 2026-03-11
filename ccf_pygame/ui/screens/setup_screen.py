"""Team setup screen."""

import pygame
from ui.colors import *
from ui.font import get_font


class SetupScreen:
    def __init__(self):
        self.font = get_font(12)
        self.title_font = get_font(18)
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
        ]
        self.selected = 0
        self.cursor_blink = 0
        self.ready = False
        self._result = None

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_s, pygame.K_j, pygame.K_KP2):
                self.selected = (self.selected + 1) % (len(self.fields) + 1)
            elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_k, pygame.K_KP8):
                self.selected = (self.selected - 1) % (len(self.fields) + 1)
            elif event.key == pygame.K_RETURN:
                if self.selected == len(self.fields):
                    self._submit()
            else:
                self._edit_field(event)

    def _edit_field(self, event):
        if self.selected >= len(self.fields):
            return
        f = self.fields[self.selected]
        if f["type"] == "text":
            if event.key == pygame.K_BACKSPACE:
                f["value"] = f["value"][:-1]
            elif event.unicode and event.unicode.isprintable() and len(f["value"]) < 12:
                f["value"] += event.unicode
        elif f["type"] == "int":
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_h, pygame.K_KP4):
                v = int(f["value"]) - 1
                f["value"] = str(max(f["min"], v))
            elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_l, pygame.K_KP6):
                v = int(f["value"]) + 1
                f["value"] = str(min(f["max"], v))
            elif event.unicode and event.unicode.isdigit():
                v = int(event.unicode)
                if f["min"] <= v <= f["max"]:
                    f["value"] = str(v)
        elif f["type"] == "choice":
            if event.key in (
                pygame.K_LEFT,
                pygame.K_RIGHT,
                pygame.K_a,
                pygame.K_d,
                pygame.K_h,
                pygame.K_l,
                pygame.K_KP4,
                pygame.K_KP6,
                pygame.K_SPACE,
            ):
                idx = f["choices"].index(f["value"])
                f["value"] = f["choices"][(idx + 1) % len(f["choices"])]

    def _submit(self):
        from ccf.models import Color
        self._result = {
            "human_name": self.fields[0]["value"] or "Player",
            "human_rating": int(self.fields[1]["value"]),
            "human_kick": int(self.fields[2]["value"]),
            "human_color": Color.RED if self.fields[3]["value"] == "RED" else Color.BLACK,
            "human_clutch": int(self.fields[4]["value"]),
            "ai_name": self.fields[5]["value"] or "Rivals",
            "ai_rating": int(self.fields[6]["value"]),
            "ai_kick": int(self.fields[7]["value"]),
            "ai_clutch": int(self.fields[8]["value"]),
        }
        self.ready = True

    def get_result(self):
        return self._result

    def handle_click(self, pos):
        x, y = pos
        # Check START button
        btn_y = 480
        btn_rect = pygame.Rect(390, btn_y, 180, 36)
        if btn_rect.collidepoint(x, y):
            self._submit()
            return

        # Check field rows
        start_y = 150
        for i in range(len(self.fields)):
            row_y = start_y + i * 39
            if row_y <= y < row_y + 36:
                self.selected = i
                f = self.fields[i]
                if f["type"] == "int":
                    if x < 600:
                        v = int(f["value"]) - 1
                        f["value"] = str(max(f["min"], v))
                    else:
                        v = int(f["value"]) + 1
                        f["value"] = str(min(f["max"], v))
                elif f["type"] == "choice":
                    idx = f["choices"].index(f["value"])
                    f["value"] = f["choices"][(idx + 1) % len(f["choices"])]
                break

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_DARK)
        self.cursor_blink = (self.cursor_blink + 1) % 60

        # Title
        title = self.title_font.render("CLUTCH CARD FOOTBALL", True, AMBER)
        surface.blit(title, (480 - title.get_width() // 2, 45))

        subtitle = self.font.render("TEAM SETUP", True, WHITE)
        surface.blit(subtitle, (480 - subtitle.get_width() // 2, 90))

        # Fields
        start_y = 150
        for i, f in enumerate(self.fields):
            y = start_y + i * 39
            is_sel = (i == self.selected)
            color = AMBER if is_sel else GRAY

            # Label
            label = self.font.render(f["label"], True, color)
            surface.blit(label, (150, y + 6))

            # Value
            val_text = f["value"]
            if f["type"] == "int":
                val_text = f"< {f['value']} >"
            elif f["type"] == "choice":
                val_text = f"< {f['value']} >"

            if f["type"] == "text" and is_sel and self.cursor_blink < 30:
                val_text += "_"

            val_surf = self.font.render(val_text, True, WHITE if not is_sel else HIGHLIGHT)
            surface.blit(val_surf, (525, y + 6))

            if is_sel:
                pygame.draw.rect(surface, color, (135, y, 690, 30), 1)

        # START button
        btn_y = start_y + len(self.fields) * 39 + 30
        is_start_sel = (self.selected == len(self.fields))
        btn_color = AMBER if is_start_sel else BUTTON_BORDER
        btn_rect = pygame.Rect(390, btn_y, 180, 36)
        pygame.draw.rect(surface, BUTTON_BG if not is_start_sel else BUTTON_HOVER, btn_rect)
        pygame.draw.rect(surface, btn_color, btn_rect, 2)
        start_text = self.font.render("START", True, AMBER)
        surface.blit(start_text, (480 - start_text.get_width() // 2, btn_y + 9))

        # Instructions
        inst = self.font.render("TAB/ARROWS/WASD: Navigate  ENTER: Start", True, DIM_TEXT)
        surface.blit(inst, (480 - inst.get_width() // 2, 660))
