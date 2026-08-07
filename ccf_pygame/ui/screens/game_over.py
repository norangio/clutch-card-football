"""Broadcast final score and stats screen."""

import pygame

from ccf.states import GameSnapshot
from ui import draw as d
from ui.layout import W
from ui.theme import (BG, BORDER, DIM, GOLD, MUTED, PANEL, RED, TEXT,
                      team_color)


class GameOverScreen:
    def __init__(self):
        self.play_again = False
        self._button = pygame.Rect(360, 584, 240, 48)
        self._stats = pygame.Rect(220, 390, 520, 160)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.play_again = True

    def handle_click(self, pos):
        if self._button.collidepoint(pos):
            self.play_again = True

    @staticmethod
    def _team_block(surface, team, center_x, ai_suffix):
        rect = pygame.Rect(0, 0, 330, 112)
        rect.center = (center_x, 286)
        d.rrect(surface, rect, PANEL, radius=12)
        d.rrect(surface, rect, BORDER, radius=12, width=1)
        color = team_color(team)
        pygame.draw.rect(surface, color,
                         (rect.x + 16, rect.y + 20, 5, 48),
                         border_radius=3)
        name = team.name + (" (AI)" if ai_suffix else "")
        d.text(surface, name, (rect.x + 34, rect.y + 32),
               d.font("cond", 30, "bold"), TEXT,
               anchor="midleft", tight=True)
        d.text(surface, str(team.score), (rect.right - 24, rect.y + 32),
               d.font("inter", 42, "bold"), color,
               anchor="midright", tight=True)
        d.text(surface, f"RATING {team.rating}  ·  KICK {team.kick_rating}",
               (rect.x + 34, rect.bottom - 24),
               d.font("inter", 10, "semibold"), MUTED,
               tracking=1, tight=True)

    @staticmethod
    def _percent(team):
        if not team.fg_att:
            return "0%"
        return f"{int(round(team.fg_made / team.fg_att * 100))}%"

    def draw(self, surface: pygame.Surface, snap: GameSnapshot):
        surface.fill(BG)
        d.text(surface, "GAME OVER", (W // 2, 80),
               d.font("cond", 48, "bold"), MUTED,
               anchor="center", tracking=2, tight=True)
        if not snap.human or not snap.ai:
            return

        if snap.human.score > snap.ai.score:
            result_color = GOLD
        elif snap.human.score < snap.ai.score:
            result_color = RED
        else:
            result_color = TEXT
        d.text(surface, snap.message, (W // 2, 146),
               d.font("cond", 56, "bold"), result_color,
               anchor="center", tracking=1, tight=True)

        self._team_block(surface, snap.human, 260, snap.ai_vs_ai)
        self._team_block(surface, snap.ai, 700, snap.ai_vs_ai)

        d.rrect(surface, self._stats, PANEL, radius=12)
        d.rrect(surface, self._stats, BORDER, radius=12, width=1)
        label_x = self._stats.x + 24
        human_x = self._stats.centerx + 55
        ai_x = self._stats.right - 58
        d.text(surface, "FINAL STATS", (label_x, self._stats.y + 18),
               d.font("inter", 10, "bold"), DIM, tracking=2, tight=True)
        d.text(surface, snap.human.name, (human_x, self._stats.y + 18),
               d.font("inter", 11, "bold"), team_color(snap.human),
               anchor="midtop", tight=True)
        d.text(surface, snap.ai.name, (ai_x, self._stats.y + 18),
               d.font("inter", 11, "bold"), team_color(snap.ai),
               anchor="midtop", tight=True)
        d.hairline(surface, self._stats.x + 18, self._stats.y + 42,
                   self._stats.right - 18, BORDER)

        rows = [
            ("SEGMENTS", str(snap.human.segments), str(snap.ai.segments)),
            ("FG MADE / ATT",
             f"{snap.human.fg_made}/{snap.human.fg_att}  {self._percent(snap.human)}",
             f"{snap.ai.fg_made}/{snap.ai.fg_att}  {self._percent(snap.ai)}"),
            ("PUNTS", str(snap.human.punts), str(snap.ai.punts)),
        ]
        for index, (label, human_value, ai_value) in enumerate(rows):
            y = self._stats.y + 58 + index * 30
            d.text(surface, label, (label_x, y),
                   d.font("inter", 11, "semibold"), MUTED)
            d.text(surface, human_value, (human_x, y),
                   d.font("inter", 12, "bold"), TEXT, anchor="midtop")
            d.text(surface, ai_value, (ai_x, y),
                   d.font("inter", 12, "bold"), TEXT, anchor="midtop")

        d.rrect(surface, self._button, GOLD, radius=10)
        d.rrect(surface, self._button, d.shade(GOLD, -0.18),
                radius=10, width=1)
        d.text(surface, "PLAY AGAIN", self._button.center,
               d.font("cond", 24, "bold"), (26, 22, 6),
               anchor="center", tracking=1, tight=True)
        d.text(surface, "Press ENTER or click to restart", (W // 2, 660),
               d.font("inter", 11, "regular"), DIM,
               anchor="center", tight=True)
