from __future__ import annotations

"""7-segment football field visualization."""

import pygame
from ui.colors import *
from ui.font import get_font


class FieldView:
    SEGMENTS = [
        ("EZ", "OWN G"),
        ("1", "OWN 1"),
        ("2", "OWN 2"),
        ("3", "OWN 3"),
        ("Z3", "RED ZONE"),
        ("Z2", "RED ZONE"),
        ("Z1", "RED ZONE"),
        ("EZ", "END ZONE"),
    ]

    def __init__(self):
        self.font = get_font(12)
        self.small_font = get_font(10)
        self.zone_font = get_font(8)

    def draw(self, surface: pygame.Surface, ball_pos: str,
             x: int, y: int, w: int, h: int, offense_name: str = "",
             offense_left_to_right: bool = True):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, FIELD_GREEN, rect)
        pygame.draw.rect(surface, FIELD_LINE, rect, 1)

        seg_count = 8  # segments 0, 1,2,3,Z3,Z2,Z1,EZ
        seg_w = (w - 30) // seg_count
        start_x = x + 15
        segments = self.SEGMENTS if offense_left_to_right else list(reversed(self.SEGMENTS))

        for i, (label, zone_name) in enumerate(segments):
            sx = start_x + i * seg_w

            # Segment box
            seg_rect = pygame.Rect(sx, y + 30, seg_w - 6, h - 60)
            if label == "EZ":
                pygame.draw.rect(surface, FIELD_ENDZONE, seg_rect)
            elif label.startswith("Z"):
                # Slightly different shade for red zone
                pygame.draw.rect(surface, (25, 110, 25), seg_rect)
            else:
                pygame.draw.rect(surface, FIELD_GREEN, seg_rect)
            pygame.draw.rect(surface, FIELD_LINE, seg_rect, 1)

            # Segment label
            lbl = self.small_font.render(label, True, WHITE)
            surface.blit(lbl, (sx + seg_w // 2 - lbl.get_width() // 2, y + 34))

            # Zone description below
            zone_lbl = self.zone_font.render(zone_name, True, DIM_TEXT)
            surface.blit(zone_lbl, (sx + seg_w // 2 - zone_lbl.get_width() // 2, y + h - 24))

            # Ball marker
            if label == ball_pos:
                bx = sx + seg_w // 2
                by = y + h // 2 + 2
                # football shape as marker...
                football_rect = pygame.Rect(bx-25,by-15,50,30)
                pygame.draw.ellipse(surface, BALL_BROWN, football_rect)
                pygame.draw.ellipse(surface, WHITE, football_rect, 3)
                ball_text = self.small_font.render("|||", True, WHITE)
                surface.blit(ball_text, (bx - ball_text.get_width() // 2, by - ball_text.get_height() // 2))

        # Direction arrow
        if offense_left_to_right:
            arrow_text = ">>>  " + offense_name + "  >>>"
        else:
            arrow_text = "<<<  " + offense_name + "  <<<"
        arrow = self.small_font.render(arrow_text, True, AMBER)
        surface.blit(arrow, (x + w // 2 - arrow.get_width() // 2, y + 6))
