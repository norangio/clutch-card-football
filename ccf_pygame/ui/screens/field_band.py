"""Cached Broadcast football field band."""

import pygame

from ui import draw as d
from ui.layout import FIELD_H, FIELD_Y, W
from ui.theme import (ENDZONE, FIELD_BOT, FIELD_TOP, GOLD, SILVER,
                      team_color)

LABELS = ["EZ", "1", "2", "3", "Z3", "Z2", "Z1", "EZ"]
ZONES = ["OWN G", "OWN 1", "OWN 2", "OWN 3", "RED", "RED", "RED",
         "END ZONE"]


class FieldBand:
    def __init__(self):
        self._layers: dict[bool, pygame.Surface] = {}
        self._chevron_layers: dict[tuple[bool, int], pygame.Surface] = {}

    @staticmethod
    def _mirrored(snap):
        return snap.offense is not None and snap.offense.color.value != "red"

    def _build_layer(self, mirror: bool):
        surface = pygame.Surface((W, FIELD_H))
        d.grad_rect(surface, surface.get_rect(), FIELD_TOP, FIELD_BOT)

        labels = list(reversed(LABELS)) if mirror else list(LABELS)
        zones = list(reversed(ZONES)) if mirror else list(ZONES)
        pad = 16
        segment_width = (W - pad * 2) / 8.0
        top = 26
        bottom = FIELD_H - 22

        for index, label in enumerate(labels):
            x = pad + index * segment_width
            segment = pygame.Rect(int(x), top, int(segment_width) + 1,
                                  bottom - top)
            if label == "EZ":
                pygame.draw.rect(surface, ENDZONE, segment)
                for hatch_x in range(segment.left - segment.h,
                                     segment.right, 14):
                    pygame.draw.line(surface, d.alpha(SILVER, 22),
                                     (hatch_x, segment.bottom),
                                     (hatch_x + segment.h, segment.top), 2)
            elif label.startswith("Z"):
                pygame.draw.rect(surface,
                                 d.mix(FIELD_TOP, (150, 40, 40), 0.16),
                                 segment)

            pygame.draw.line(surface, d.alpha((255, 255, 255), 70),
                             (segment.right, top), (segment.right, bottom))
            for quarter in range(1, 4):
                hash_x = segment.left + segment.w * quarter / 4
                pygame.draw.line(surface, d.alpha((255, 255, 255), 34),
                                 (hash_x, top + 4), (hash_x, top + 11))
                pygame.draw.line(surface, d.alpha((255, 255, 255), 34),
                                 (hash_x, bottom - 11),
                                 (hash_x, bottom - 4))

            d.text(surface, label, (segment.centerx, 15),
                   d.font("cond", 18, "bold"),
                   d.alpha((255, 255, 255), 200),
                   anchor="center", tight=True)
            d.text(surface, zones[index], (segment.centerx, FIELD_H - 12),
                   d.font("inter", 8, "semibold"),
                   d.alpha((255, 255, 255), 120),
                   anchor="center", tracking=1, tight=True)

        return surface

    def _chevrons(self, mirror, ball_x):
        key = (mirror, ball_x)
        if key not in self._chevron_layers:
            layer = pygame.Surface((W, FIELD_H), pygame.SRCALPHA)
            pad = 16
            segment_width = (W - pad * 2) / 8.0
            play_left = pad + segment_width
            play_right = W - pad - segment_width
            mid_y = (26 + FIELD_H - 22) // 2
            direction = -1 if mirror else 1
            chevron_x = play_left + 22
            while chevron_x < play_right:
                if abs(chevron_x - ball_x) > 46:
                    d.chevron(layer, chevron_x, mid_y, 6,
                              d.alpha((255, 255, 255), 20), direction, 3)
                chevron_x += 46
            self._chevron_layers[key] = layer
        return self._chevron_layers[key]

    def draw(self, surface, snap):
        mirror = self._mirrored(snap)
        if mirror not in self._layers:
            self._layers[mirror] = self._build_layer(mirror)
        surface.blit(self._layers[mirror], (0, FIELD_Y))

        labels = list(reversed(LABELS)) if mirror else LABELS
        pad = 16
        segment_width = (W - pad * 2) / 8.0
        ball_x = None
        for index, label in enumerate(labels):
            if label == snap.ball_pos:
                ball_x = int(pad + index * segment_width + segment_width / 2)
                break
        if ball_x is None:
            return

        mid_y = FIELD_Y + (26 + FIELD_H - 22) // 2
        surface.blit(self._chevrons(mirror, ball_x), (0, FIELD_Y))
        d.shadow(surface, pygame.Rect(ball_x - 27, mid_y - 16, 54, 32),
                 radius=16, spread=10, a=130, offset=(0, 4))
        d.football(surface, (ball_x, mid_y), 54, 32, (132, 80, 30),
                   team_color(snap.offense) if snap.offense else GOLD)
