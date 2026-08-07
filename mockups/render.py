#!/usr/bin/env python3
"""Render the CCF UI mockups to PNG.

    python3 mockups/render.py                # every theme, every state
    python3 mockups/render.py broadcast      # one theme

Mockups are draw-only: they read a GameSnapshot and paint it. No game logic
is imported beyond the data models and the drive chart.
"""

import importlib
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pygame  # noqa: E402

from lib.mockdata import STATES  # noqa: E402

THEMES = ["broadcast", "minimal", "neon"]
OUT = os.path.join(HERE, "out")


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))

    wanted = sys.argv[1:] or THEMES
    os.makedirs(OUT, exist_ok=True)

    for theme_name in wanted:
        try:
            theme = importlib.import_module(f"theme_{theme_name}")
        except ModuleNotFoundError:
            print(f"  skip {theme_name} (not written yet)")
            continue

        surf = pygame.Surface((theme.W, theme.H))
        for key, (label, factory) in sorted(STATES.items()):
            surf.fill((0, 0, 0))
            theme.render(surf, factory())
            path = os.path.join(OUT, f"{theme_name}-{key}.png")
            pygame.image.save(surf, path)
            print(f"  {os.path.relpath(path, HERE)}  — {theme.NAME}: {label}")

    pygame.quit()


if __name__ == "__main__":
    main()
