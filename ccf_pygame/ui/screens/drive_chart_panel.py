"""Drive chart panel — shows card movement lookup for current offense team."""

import pygame
from ui.colors import *
from ui.font import get_font
from ccf.drive_chart import DRIVE_CHART, SUIT_TO_COLOR

CARD_ORDER = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# Bonus indicator colors
BONUS_COLORS = {
    "yellow": (230, 200, 50),
    "orange": (230, 130, 30),
    "green": (60, 200, 80),
}


class DriveChartPanel:
    def __init__(self):
        self.header_font = get_font(10)
        self.row_font = get_font(8)

    def draw(self, surface: pygame.Surface, rating: int, team_color_str: str,
             x: int, y: int, w: int, h: int):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, BG_PANEL, rect)
        pygame.draw.rect(surface, SCORE_BORDER, rect, 1)

        # Header
        header = self.header_font.render(f"CHART | R{rating}", True, AMBER)
        surface.blit(header, (x + 6, y + 4))

        chart = DRIVE_CHART.get(str(rating), {})
        row_h = max(12, (h - 22) // len(CARD_ORDER))
        col_card = 6
        col_base = col_card + 28
        col_bonus = col_base + 22

        # Column labels
        label_y = y + 17
        surface.blit(self.row_font.render("CRD", True, DIM_TEXT), (x + col_card, label_y))
        surface.blit(self.row_font.render("MOV", True, DIM_TEXT), (x + col_base, label_y))
        surface.blit(self.row_font.render("BON", True, DIM_TEXT), (x + col_bonus, label_y))

        for i, card_val in enumerate(CARD_ORDER):
            row_y = y + 28 + i * row_h
            entry = chart.get(card_val, {"base": 0})
            base = entry.get("base", 0)
            bonus_type = entry.get("bonus")

            # Card value
            cv = self.row_font.render(card_val, True, WHITE)
            surface.blit(cv, (x + col_card, row_y))

            # Base movement
            base_str = f"+{base}" if base >= 0 else str(base)
            bv = self.row_font.render(base_str, True, WHITE)
            surface.blit(bv, (x + col_base, row_y))

            # Bonus indicator
            if bonus_type:
                dot_color = BONUS_COLORS.get(bonus_type, WHITE)
                # Dim if team color doesn't match (bonus won't trigger)
                dot_x = x + col_bonus + 4
                dot_y = row_y + 4
                pygame.draw.circle(surface, dot_color, (dot_x, dot_y), 4)
                label_char = bonus_type[0].upper()
                bl = self.row_font.render(label_char, True, BG_DARK)
                surface.blit(bl, (dot_x - bl.get_width() // 2, dot_y - bl.get_height() // 2))
