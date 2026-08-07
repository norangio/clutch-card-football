"""Cached drive-chart reference rail."""

import pygame

from ccf.drive_chart import DRIVE_CHART
from ui import draw as d
from ui.layout import CHART_RECT
from ui.theme import BONUS, BORDER, DIM, GOLD, MUTED, PANEL, TEXT


class ChartRail:
    ORDER = ["2", "3", "4", "5", "6", "7", "8", "9", "10",
             "J", "Q", "K", "A"]

    def __init__(self):
        self._layers: dict[tuple[int, bool], pygame.Surface] = {}

    def _build_layer(self, rating, mirror):
        del mirror  # Kept in the cache key because possession direction changes.
        rect = pygame.Rect(0, 0, CHART_RECT.w, CHART_RECT.h)
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        d.rrect(surface, rect, PANEL, radius=12)
        d.rrect(surface, rect, BORDER, radius=12, width=1)

        chart = DRIVE_CHART.get(str(rating), {})
        d.text(surface, "DRIVE CHART", (14, 16),
               d.font("inter", 10, "bold"), DIM, tracking=2, tight=True)
        d.text(surface, f"RATING {rating}", (14, 28),
               d.font("inter", 11, "bold"), GOLD)
        d.hairline(surface, 12, 48, rect.right - 12, BORDER)

        row_h = (rect.h - 62) / len(self.ORDER)
        for index, value in enumerate(self.ORDER):
            y = 56 + index * row_h
            entry = chart.get(value, {"base": 0})
            if index % 2 == 0:
                d.rrect(surface, (8, int(y) - 2, rect.w - 16, int(row_h)),
                        (26, 32, 42), radius=5)
            d.text(surface, value, (18, y),
                   d.font("inter", 11, "semibold"), TEXT)
            base = entry.get("base", 0)
            d.text(surface, f"{base:+d}", (96, y),
                   d.font("inter", 11, "bold"),
                   MUTED if base <= 0 else TEXT, anchor="topright")
            bonus = entry.get("bonus")
            if bonus:
                pygame.draw.circle(surface, BONUS[bonus],
                                   (rect.right - 24, int(y) + 7), 5)
        return surface

    def draw(self, surface, snap):
        rating = snap.offense.rating if snap.offense else 6
        mirror = bool(snap.offense and snap.offense.color.value != "red")
        key = (rating, mirror)
        if key not in self._layers:
            self._layers[key] = self._build_layer(*key)
        surface.blit(self._layers[key], CHART_RECT.topleft)
