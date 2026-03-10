"""PygameApp — main loop with internal resolution and GPU-scaled display."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from ui.crt_effect import CRTEffect
from ui.colors import BG_DARK
from ui.screens.setup_screen import SetupScreen
from ui.screens.play_screen import PlayScreen
from ui.screens.game_over import GameOverScreen
from ccf.states import GamePhase
from ccf.state_machine import GameStateMachine
import ui.sounds as sounds


INTERNAL_W = 960
INTERNAL_H = 720
FPS = 60
IS_WEB = sys.platform == "emscripten"


class PygameApp:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            sounds.init_sounds()
        except Exception as exc:
            # Browser/headless environments may not expose or fully support audio.
            print(f"[audio] disabled: {exc}")
        pygame.display.set_caption("Clutch Card Football")

        self.internal = pygame.Surface((INTERNAL_W, INTERNAL_H))
        display_flags = 0 if IS_WEB else (pygame.SCALED | pygame.RESIZABLE)
        try:
            self.screen = pygame.display.set_mode((INTERNAL_W, INTERNAL_H), display_flags)
        except Exception as exc:
            # Browser canvas backends can reject desktop display flags.
            print(f"[display] fallback: {exc}")
            self.screen = pygame.display.set_mode((INTERNAL_W, INTERNAL_H))
        self.clock = pygame.time.Clock()
        self.crt = None if IS_WEB else CRTEffect(INTERNAL_W, INTERNAL_H)

        self.state_machine = GameStateMachine()
        self.setup_screen = SetupScreen()
        self.play_screen = PlayScreen(self.state_machine)
        self.game_over_screen = GameOverScreen()
        self.running = True

    def _tick(self):
        self._handle_events()
        self._update()
        self._draw()
        self.clock.tick(FPS)

    def run(self):
        while self.running:
            self._tick()
        pygame.quit()

    async def run_async(self):
        """Browser-friendly async loop used by pygbag."""
        while self.running:
            self._tick()
            await asyncio.sleep(0)
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            phase = self.state_machine.phase

            if phase == GamePhase.SETUP_TEAMS:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.setup_screen.handle_click(event.pos)
                else:
                    self.setup_screen.handle_event(event)
                if self.setup_screen.ready:
                    result = self.setup_screen.get_result()
                    self.state_machine.provide_setup(
                        result["human_name"], result["human_rating"],
                        result["human_kick"], result["human_color"],
                        result["human_clutch"], result["ai_name"],
                        result["ai_rating"], result["ai_kick"], result["ai_clutch"],
                    )
            elif phase == GamePhase.GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.game_over_screen.handle_click(event.pos)
                else:
                    self.game_over_screen.handle_event(event)
                if self.game_over_screen.play_again:
                    self._restart()
            else:
                self.play_screen.handle_event(event)

    def _update(self):
        phase = self.state_machine.phase
        if phase not in (GamePhase.SETUP_TEAMS, GamePhase.GAME_OVER):
            self.play_screen.update()

    def _draw(self):
        self.internal.fill(BG_DARK)
        phase = self.state_machine.phase

        if phase == GamePhase.SETUP_TEAMS:
            self.setup_screen.draw(self.internal)
        elif phase == GamePhase.GAME_OVER:
            snap = self.state_machine.snapshot()
            self.game_over_screen.draw(self.internal, snap)
        else:
            self.play_screen.draw(self.internal)

        # Apply CRT effects on desktop; browser builds skip this post-process step.
        if self.crt is not None:
            self.crt.apply(self.internal)

        # Blit to display — pygame.SCALED handles GPU scaling
        self.screen.blit(self.internal, (0, 0))
        pygame.display.flip()

    def _restart(self):
        self.state_machine = GameStateMachine()
        self.setup_screen = SetupScreen()
        self.play_screen = PlayScreen(self.state_machine)
        self.game_over_screen = GameOverScreen()


if __name__ == "__main__":
    PygameApp().run()
