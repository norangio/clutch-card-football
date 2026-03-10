#!/usr/bin/env python3
"""Browser entry point for pygbag."""

import asyncio
import traceback

from ui.app import PygameApp


async def main():
    try:
        app = PygameApp()
        await app.run_async()
    except Exception:
        # Keep stack trace visible in browser dev tools if startup fails.
        tb = traceback.format_exc()
        print(tb)
        try:
            import pygame

            if not pygame.get_init():
                pygame.init()
            if not pygame.font.get_init():
                pygame.font.init()

            screen = pygame.display.set_mode((960, 720))
            font = pygame.font.Font(None, 24)
            lines = ["Startup error (send screenshot):"] + tb.splitlines()[:24]

            while True:
                screen.fill((24, 24, 24))
                y = 16
                for line in lines:
                    surf = font.render(line[:140], True, (255, 120, 120))
                    screen.blit(surf, (12, y))
                    y += 26
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                await asyncio.sleep(0)
        except Exception:
            while True:
                await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
