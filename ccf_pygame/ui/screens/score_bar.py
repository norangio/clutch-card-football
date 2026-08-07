"""Full-width Broadcast score bar."""

import pygame

from ui import draw as d
from ui.layout import SCORE_H, W
from ui.theme import (BORDER, DIM, GOLD, GREEN_OK, MUTED, ORANGE, PANEL,
                      PANEL_HI, RED, TEXT, team_color)

PIP_LABEL = None


class ScoreBar:
    def __init__(self):
        global PIP_LABEL
        PIP_LABEL = PIP_LABEL or d.font("inter", 10, "bold")

    @staticmethod
    def _pips_width(label, cap):
        return d.text_size(label, PIP_LABEL, 1)[0] + 10 + cap * 16 - 4

    @staticmethod
    def _pips(surface, x, cy, label, count, cap, color, kind="dot"):
        d.text(surface, label, (x, cy), PIP_LABEL, DIM,
               anchor="midleft", tracking=1)
        px = x + d.text_size(label, PIP_LABEL, 1)[0] + 10
        for index in range(cap):
            pip_color = color if index < count else (52, 60, 74)
            if kind == "star":
                d.star(surface, (px + 6, cy), 6, pip_color)
            else:
                pygame.draw.circle(surface, pip_color, (px + 5, cy), 5)
            px += 16
        return px - 4

    def draw(self, surface, snap):
        if snap.human is None or snap.ai is None:
            return
        d.grad_rect(surface, (0, 0, W, SCORE_H), PANEL_HI, PANEL)
        pygame.draw.line(surface, GOLD, (0, SCORE_H - 2),
                         (W, SCORE_H - 2), 2)

        name_font = d.font("cond", 34, "bold")
        score_font = d.font("inter", 36, "bold")
        row_cy = 33

        for side, team in (("left", snap.human), ("right", snap.ai)):
            color = team_color(team)
            name_width = d.text_size(team.name, name_font, tight=True)[0]
            if side == "left":
                pygame.draw.rect(surface, color, (20, 13, 5, 40),
                                 border_radius=3)
                name_x = 36
                d.text(surface, team.name, (name_x, row_cy), name_font, TEXT,
                       anchor="midleft", tight=True)
                d.text(surface, str(team.score),
                       (name_x + name_width + 20, row_cy), score_font, TEXT,
                       anchor="midleft", tight=True)
                tag_left = name_x
            else:
                pygame.draw.rect(surface, color, (W - 25, 13, 5, 40),
                                 border_radius=3)
                name_x = W - 36
                d.text(surface, team.name, (name_x, row_cy), name_font, TEXT,
                       anchor="midright", tight=True)
                d.text(surface, str(team.score),
                       (name_x - name_width - 20, row_cy), score_font, TEXT,
                       anchor="midright", tight=True)
                tag_left = None

            if snap.offense is team:
                tag_font = d.font("inter", 9, "bold")
                tag_width = d.text_size("OFFENSE", tag_font, 1)[0]
                tag = pygame.Rect(0, 0, tag_width + 16, 15)
                if tag_left is not None:
                    tag.topleft = (tag_left, 55)
                else:
                    tag.topright = (name_x, 55)
                d.rrect(surface, tag, GOLD, radius=7)
                d.text(surface, "OFFENSE", tag.center, tag_font, (26, 22, 6),
                       anchor="center", tracking=1, tight=True)

        pill = pygame.Rect(0, 0, 132, 56)
        pill.midtop = (W // 2, 10)
        d.rrect(surface, pill, (13, 17, 23), radius=10)
        d.rrect(surface, pill, BORDER, radius=10, width=1)
        d.text(surface, f"Q{snap.quarter}", (pill.centerx, pill.y + 20),
               d.font("cond", 32, "bold"), GOLD,
               anchor="center", tight=True)
        d.text(surface, f"PLAY {snap.turn} / {snap.turns_in_quarter}",
               (pill.centerx, pill.bottom - 12),
               d.font("inter", 10, "semibold"), MUTED,
               anchor="center", tracking=1, tight=True)

        cy = 84
        x = self._pips(surface, 20, cy, "CLUTCH", snap.human.clutch, 5,
                       GOLD, "star")
        self._pips(surface, x + 20, cy, "MOJO", snap.human.mojo, 2, ORANGE)

        total = (self._pips_width("CLUTCH", 5) + 20
                 + self._pips_width("MOJO", 2))
        x = self._pips(surface, W - 20 - total, cy, "CLUTCH",
                       snap.ai.clutch, 5, GOLD, "star")
        self._pips(surface, x + 20, cy, "MOJO", snap.ai.mojo, 2, ORANGE)

        difficulty = snap.difficulty.upper()
        difficulty_color = {
            "EASY": GREEN_OK,
            "MEDIUM": GOLD,
            "HARD": RED,
        }.get(difficulty, GOLD)
        label = f"AI · {difficulty}"
        chip = pygame.Rect(0, 0,
                           d.text_size(label, PIP_LABEL, 1)[0] + 18, 18)
        chip.center = (W // 2, cy)
        d.rrect(surface, chip, d.alpha(difficulty_color, 34), radius=9)
        d.text(surface, label, chip.center, PIP_LABEL, difficulty_color,
               anchor="center", tracking=1, tight=True)
