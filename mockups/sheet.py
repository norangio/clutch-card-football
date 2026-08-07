#!/usr/bin/env python3
"""Compose one contact sheet per theme — all four states in a 2x2 grid.

    python3 mockups/sheet.py

Run after render.py; reads mockups/out/<theme>-<state>.png.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pygame  # noqa: E402

from lib import draw as d      # noqa: E402
from lib.mockdata import STATES  # noqa: E402
import render as R             # noqa: E402

TILE_W, TILE_H = 960, 720
PAD, LABEL_H, TITLE_H = 16, 30, 54
BG = (16, 16, 19)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))

    keys = sorted(STATES)
    cols = 2
    rows = (len(keys) + cols - 1) // cols
    sw = PAD + cols * (TILE_W + PAD)
    sh = TITLE_H + rows * (LABEL_H + TILE_H + PAD)

    for theme_name in R.THEMES:
        import importlib
        try:
            theme = importlib.import_module(f"theme_{theme_name}")
        except ModuleNotFoundError:
            continue

        sheet = pygame.Surface((sw, sh))
        sheet.fill(BG)
        d.text(sheet, f"{theme.NAME}  —  {theme.BLURB}", (PAD, TITLE_H // 2),
               d.font("inter", 17, "semibold"), (238, 238, 242),
               anchor="midleft", tight=True)

        for i, key in enumerate(keys):
            cx, cy = i % cols, i // cols
            x = PAD + cx * (TILE_W + PAD)
            y = TITLE_H + cy * (LABEL_H + TILE_H + PAD)
            d.text(sheet, STATES[key][0].upper(), (x + 2, y + LABEL_H // 2 - 2),
                   d.font("inter", 11, "bold"), (140, 140, 152),
                   anchor="midleft", tracking=2, tight=True)
            img = pygame.image.load(os.path.join(R.OUT, f"{theme_name}-{key}.png"))
            sheet.blit(img, (x, y + LABEL_H))
            pygame.draw.rect(sheet, (52, 52, 60),
                             pygame.Rect(x, y + LABEL_H, TILE_W, TILE_H), 1)

        path = os.path.join(R.OUT, f"SHEET-{theme_name}.png")
        pygame.image.save(sheet, path)
        print(f"  {os.path.relpath(path, HERE)}")

    pygame.quit()


if __name__ == "__main__":
    main()
