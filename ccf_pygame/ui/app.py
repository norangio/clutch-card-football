"""Pygame application shell for the 960x720 Broadcast UI."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase
from ui.layout import H as INTERNAL_H
from ui.layout import W as INTERNAL_W
from ui.screens.game_over import GameOverScreen
from ui.screens.play_screen import PlayScreen
from ui.screens.setup_screen import SetupScreen
from ui.theme import BG
import ui.sounds as sounds

FPS = 30


class PygameApp:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            sounds.init_sounds()
        except pygame.error as error:
            print(f"[sounds] Audio unavailable: {error}")
        pygame.display.set_caption("Clutch Card Football")

        self.internal = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self.screen = pygame.display.set_mode(
            (INTERNAL_W, INTERNAL_H), pygame.SCALED | pygame.RESIZABLE
        )
        self.clock = pygame.time.Clock()
        self.state_machine = GameStateMachine(fps=FPS)
        self.setup_screen = SetupScreen()
        self.play_screen = PlayScreen(self.state_machine)
        self.game_over_screen = GameOverScreen()
        self.running = True

    def tick(self):
        """Run one non-blocking frame; usable by desktop or a future WASM loop."""
        if not self.running:
            return False
        self._handle_events()
        if self.running:
            self._update()
            self._draw()
            self.clock.tick(FPS)
        return self.running

    def run(self):
        while self.tick():
            pass
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
                    ai_vs_ai = result.get("ai_vs_ai", False)
                    sounds.set_muted(ai_vs_ai)
                    self.state_machine.provide_setup(
                        result["human_name"], result["human_rating"],
                        result["human_kick"], result["human_color"],
                        result["human_clutch"], result["ai_name"],
                        result["ai_rating"], result["ai_kick"],
                        result["ai_clutch"], result["difficulty"],
                        ai_vs_ai=ai_vs_ai,
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
        if self.state_machine.phase not in (
                GamePhase.SETUP_TEAMS, GamePhase.GAME_OVER):
            self.play_screen.update()

    def _draw(self):
        self.internal.fill(BG)
        phase = self.state_machine.phase
        if phase == GamePhase.SETUP_TEAMS:
            self.setup_screen.draw(self.internal)
        elif phase == GamePhase.GAME_OVER:
            self.game_over_screen.draw(self.internal,
                                       self.state_machine.snapshot())
        else:
            self.play_screen.draw(self.internal)

        self.screen.blit(self.internal, (0, 0))
        pygame.display.flip()

    def _restart(self):
        self.state_machine = GameStateMachine(fps=FPS)
        self.setup_screen = SetupScreen()
        self.play_screen = PlayScreen(self.state_machine)
        self.game_over_screen = GameOverScreen()
        sounds.set_muted(False)


if __name__ == "__main__":
    PygameApp().run()
