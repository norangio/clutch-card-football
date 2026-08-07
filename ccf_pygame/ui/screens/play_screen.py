"""Composite Broadcast game screen and input routing."""

from time import perf_counter

import pygame

from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase, GameSnapshot
from ui.layout import HAND_RECT
from ui.screens.action_bar import ActionBar
from ui.screens.chart_rail import ChartRail
from ui.screens.field_band import FieldBand
from ui.screens.hand_rail import HandRail
from ui.screens.log_panel import LogPanel
from ui.screens.play_panel import PlayPanel
from ui.screens.score_bar import ScoreBar
from ui.theme import BG
import ui.sounds as sounds


class PlayScreen:
    def __init__(self, state_machine: GameStateMachine):
        self.sm = state_machine
        self.score_bar = ScoreBar()
        self.field_band = FieldBand()
        self.hand_rail = HandRail()
        self.play_panel = PlayPanel()
        self.log_panel = LogPanel()
        self.chart_rail = ChartRail()
        self.action_bar = ActionBar()
        self._prev_phase: GamePhase | None = None
        self.last_draw_ms = 0.0

    def handle_event(self, event: pygame.event.Event):
        snap = self.sm.snapshot()
        phase = snap.phase
        self.hand_rail.update(snap)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos, snap)
            return

        if phase in (GamePhase.WAITING_OFFENSE_CARD,
                     GamePhase.WAITING_DEFENSE_CARD):
            result = self.hand_rail.handle_event(event)
            if result is not None:
                self.sm.provide_card(result)
        elif phase == GamePhase.WAITING_POST_MOVE:
            choice = self.action_bar.handle_event(event)
            if choice:
                self.sm.provide_post_move(choice)
        elif phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            choice = self.action_bar.handle_event(event)
            if choice:
                self.sm.provide_extra_point_choice(choice)
        elif event.type == pygame.KEYDOWN:
            self.sm.click_advance()

    def _handle_click(self, pos, snap):
        phase = snap.phase
        if phase in (GamePhase.WAITING_OFFENSE_CARD,
                     GamePhase.WAITING_DEFENSE_CARD):
            result = (self.hand_rail.handle_click(pos)
                      if HAND_RECT.collidepoint(pos) else None)
            if result is not None:
                self.sm.provide_card(result)
            else:
                self.sm.click_advance()
        elif phase == GamePhase.WAITING_POST_MOVE:
            choice = self.action_bar.handle_click(pos)
            if choice:
                self.sm.provide_post_move(choice)
        elif phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            choice = self.action_bar.handle_click(pos)
            if choice:
                self.sm.provide_extra_point_choice(choice)
        else:
            self.sm.click_advance()

    def update(self):
        self.sm.advance()
        snap = self.sm.snapshot()
        self._trigger_sounds(snap)
        self._prev_phase = snap.phase

    def _trigger_sounds(self, snap: GameSnapshot):
        phase = snap.phase
        previous = self._prev_phase
        if (previous == GamePhase.SHOWING_MOVEMENT
                and phase != GamePhase.SHOWING_MOVEMENT
                and snap.movement > 0):
            sounds.play("first_down")
        if (previous != GamePhase.SHOWING_TOUCHDOWN
                and phase == GamePhase.SHOWING_TOUCHDOWN):
            sounds.play("touchdown")
        if (previous != GamePhase.SHOWING_FIELD_GOAL
                and phase == GamePhase.SHOWING_FIELD_GOAL
                and snap.fg_success):
            sounds.play("field_goal")
        if (previous != GamePhase.GAME_OVER
                and phase == GamePhase.GAME_OVER
                and snap.human and snap.ai
                and snap.human.score > snap.ai.score):
            sounds.play("win")

    def draw(self, surface: pygame.Surface):
        started = perf_counter()
        surface.fill(BG)
        snap = self.sm.snapshot()
        self.score_bar.draw(surface, snap)
        self.field_band.draw(surface, snap)
        self.hand_rail.draw(surface, snap)
        self.play_panel.draw(surface, snap)
        self.log_panel.draw(surface, snap)
        self.chart_rail.draw(surface, snap)
        self.action_bar.draw(surface, snap)
        self.last_draw_ms = (perf_counter() - started) * 1000.0
