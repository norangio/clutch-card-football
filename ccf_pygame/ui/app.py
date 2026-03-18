"""PygameApp — shared desktop/browser game loop."""

import asyncio
import importlib
import os
import sys

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


def _ensure_pygame_compat():
    module_aliases = {
        "display": "pygame.display",
        "draw": "pygame.draw",
        "event": "pygame.event",
        "font": "pygame.font",
        "key": "pygame.key",
        "mixer": "pygame.mixer",
        "time": "pygame.time",
    }
    for attr, module_name in module_aliases.items():
        if hasattr(pygame, attr):
            continue
        try:
            setattr(pygame, attr, importlib.import_module(module_name))
        except Exception:
            pass

    attr_aliases = {
        "init": ("pygame.base", "init"),
        "quit": ("pygame.base", "quit"),
        "Surface": ("pygame.surface", "Surface"),
        "Rect": ("pygame.rect", "Rect"),
        "Color": ("pygame.color", "Color"),
    }
    for attr, (module_name, name) in attr_aliases.items():
        if hasattr(pygame, attr):
            continue
        try:
            module = importlib.import_module(module_name)
            setattr(pygame, attr, getattr(module, name))
        except Exception:
            pass


_ensure_pygame_compat()


def _init_pygame_modules():
    init_fn = getattr(pygame, "init", None)
    if callable(init_fn):
        init_fn()
        return

    for module_name in ("display", "font", "mixer"):
        module = getattr(pygame, module_name, None)
        if module is None:
            continue
        init = getattr(module, "init", None)
        if callable(init):
            init()


def _quit_pygame_modules():
    quit_fn = getattr(pygame, "quit", None)
    if callable(quit_fn):
        quit_fn()
        return

    for module_name in ("mixer", "font", "display"):
        module = getattr(pygame, module_name, None)
        if module is None:
            continue
        quit_module = getattr(module, "quit", None)
        if callable(quit_module):
            quit_module()


class PygameApp:
    def __init__(
        self,
        *,
        browser_mode: bool | None = None,
        enable_audio: bool | None = None,
        enable_crt: bool | None = None,
        _screen=None,
    ):
        self.browser_mode = sys.platform == "emscripten" if browser_mode is None else browser_mode
        self.audio_enabled = False
        self.crt = None
        self._shutdown = False

        if enable_audio is None:
            enable_audio = not self.browser_mode

        if _screen is not None:
            # Browser path: pygame already initialised by main.py at module level
            self.screen = _screen
        else:
            # Desktop path: full init here
            _init_pygame_modules()
            pygame.display.set_caption("Clutch Card Football")
            display_flags = pygame.SCALED | pygame.RESIZABLE
            try:
                self.screen = pygame.display.set_mode((INTERNAL_W, INTERNAL_H), display_flags)
            except pygame.error as exc:
                print(f"[display] falling back to default flags: {exc}")
                self.screen = pygame.display.set_mode((INTERNAL_W, INTERNAL_H))

        self.audio_enabled = self._init_audio(enable_audio)
        self.internal = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self.clock = pygame.time.Clock()

        if enable_crt is None:
            enable_crt = not self.browser_mode
        if enable_crt:
            self.crt = CRTEffect(INTERNAL_W, INTERNAL_H)

        self.state_machine = GameStateMachine()
        self.setup_screen = SetupScreen()
        self.play_screen = PlayScreen(self.state_machine)
        self.game_over_screen = GameOverScreen()
        self.running = True

    def _init_audio(self, enabled: bool) -> bool:
        if not enabled:
            return False

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except pygame.error as exc:
            print(f"[audio] mixer disabled: {exc}")
            return False

        sounds.init_sounds()
        return True

    def run(self):
        try:
            while self.running:
                self.tick()
        finally:
            self.shutdown()

    async def run_async(self):
        try:
            while self.running:
                self.tick()
                await asyncio.sleep(0)
        finally:
            self.shutdown()

    def tick(self):
        self._handle_events()
        self._update()
        self._draw()
        self.clock.tick(FPS)

    def shutdown(self):
        if self._shutdown:
            return
        _quit_pygame_modules()
        self._shutdown = True

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.browser_mode:
                    continue
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

        if self.crt is not None:
            self.crt.apply(self.internal)

        # Present the internal render surface on the active display target.
        self.screen.blit(self.internal, (0, 0))
        pygame.display.flip()

    def _restart(self):
        self.state_machine = GameStateMachine()
        self.setup_screen = SetupScreen()
        self.play_screen = PlayScreen(self.state_machine)
        self.game_over_screen = GameOverScreen()


if __name__ == "__main__":
    PygameApp().run()
