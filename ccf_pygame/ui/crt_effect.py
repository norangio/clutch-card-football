from __future__ import annotations

"""CRT retro post-processing: scanlines + vignette."""

import pygame


class CRTEffect:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._scanline_surface = self._make_scanlines()
        self._vignette_surface = self._make_vignette()

    def _make_scanlines(self) -> pygame.Surface:
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 1):
            pygame.draw.line(surf, (0, 0, 0, 76), (0, y), (self.width, y))  # ~30% opacity
        return surf

    def _make_vignette(self) -> pygame.Surface:
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width // 2, self.height // 2
        max_dist = (cx ** 2 + cy ** 2) ** 0.5

        for ring in range(0, int(max_dist), 4):
            t = ring / max_dist
            if t < 0.5:
                continue
            alpha = int((t - 0.5) * 2.0 * 120)  # ramp from 0 to 120
            alpha = min(alpha, 120)
            pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), int(max_dist) - ring, 4)

        return surf

    def apply(self, surface: pygame.Surface):
        surface.blit(self._scanline_surface, (0, 0))
        surface.blit(self._vignette_surface, (0, 0))
