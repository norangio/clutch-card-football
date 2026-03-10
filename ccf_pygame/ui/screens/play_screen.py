"""Main game composite screen — wires field, hand, scoreboard, log, decisions, card battle."""

import pygame
from ui.colors import *
from ui.font import get_font
from ccf.states import GamePhase, GameSnapshot
from ccf.state_machine import GameStateMachine
from ui.screens.scoreboard import Scoreboard
from ui.screens.field_view import FieldView
from ui.screens.card_hand import CardHand
from ui.screens.card_battle import CardBattle
from ui.screens.play_log import PlayLog
from ui.screens.decision_panel import DecisionPanel
from ui.screens.drive_chart_panel import DriveChartPanel
import ui.sounds as sounds

# Internal resolution
W = 960
H = 720


class PlayScreen:
    """Layout (960x720):
    Top:     Scoreboard (full width, 72px)
    Left:    CardHand (195px wide, top ~400px) + DriveChart (bottom ~248px)
    Right:   FieldView (top), CardBattle (mid), PlayLog (lower), DecisionPanel (bottom)
    """

    def __init__(self, state_machine: GameStateMachine):
        self.sm = state_machine
        self.font = get_font(12)
        self.scoreboard = Scoreboard()
        self.field_view = FieldView()
        self.card_hand = CardHand()
        self.card_battle = CardBattle()
        self.play_log = PlayLog()
        self.decision_panel = DecisionPanel()
        self.drive_chart = DriveChartPanel()

        # Layout constants
        self.HAND_W = 195
        self.SCORE_H = 72
        self.FIELD_H = 120
        self.BATTLE_H = 82
        self.DECISION_H = 72

        # Split left panel: card hand top, drive chart bottom
        self.HAND_H = 400
        self.CHART_H = H - self.SCORE_H - self.HAND_H  # ~248px

        # Sound tracking — track previous phase to trigger on transitions
        self._prev_phase: GamePhase | None = None
        self._prev_ball_pos: str = "1"

    def handle_event(self, event: pygame.event.Event):
        snap = self.sm.snapshot()
        phase = snap.phase

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos, snap)
            return

        if phase in (GamePhase.WAITING_OFFENSE_CARD, GamePhase.WAITING_DEFENSE_CARD):
            result = self.card_hand.handle_event(event)
            if result is not None:
                self.sm.provide_card(result)

        elif phase == GamePhase.WAITING_POST_MOVE:
            choice = self.decision_panel.handle_event(event)
            if choice:
                self.sm.provide_post_move(choice)

        elif phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            choice = self.decision_panel.handle_event(event)
            if choice:
                self.sm.provide_extra_point_choice(choice)

        elif event.type == pygame.KEYDOWN:
            self.sm.click_advance()

    def _handle_click(self, pos, snap):
        phase = snap.phase
        hand_rect = pygame.Rect(0, self.SCORE_H, self.HAND_W, H - self.SCORE_H)

        if phase in (GamePhase.WAITING_OFFENSE_CARD, GamePhase.WAITING_DEFENSE_CARD):
            result = self.card_hand.handle_click(pos, hand_rect)
            if result is not None:
                self.sm.provide_card(result)
            else:
                self.sm.click_advance()

        elif phase == GamePhase.WAITING_POST_MOVE:
            choice = self.decision_panel.handle_click(pos)
            if choice:
                self.sm.provide_post_move(choice)

        elif phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            choice = self.decision_panel.handle_click(pos)
            if choice:
                self.sm.provide_extra_point_choice(choice)
        else:
            self.sm.click_advance()

    def update(self):
        self.sm.advance()
        snap = self.sm.snapshot()
        self._trigger_sounds(snap)
        self._prev_phase = snap.phase
        self._prev_ball_pos = snap.ball_pos

    def _trigger_sounds(self, snap: GameSnapshot):
        phase = snap.phase
        prev = self._prev_phase

        if prev == GamePhase.SHOWING_MOVEMENT and phase != GamePhase.SHOWING_MOVEMENT:
            # First down sound: ball moved forward at least one segment
            if snap.movement > 0:
                sounds.play("first_down")

        if prev != GamePhase.SHOWING_TOUCHDOWN and phase == GamePhase.SHOWING_TOUCHDOWN:
            sounds.play("touchdown")

        if prev != GamePhase.SHOWING_FIELD_GOAL and phase == GamePhase.SHOWING_FIELD_GOAL:
            if snap.fg_success:
                sounds.play("field_goal")

        if prev != GamePhase.GAME_OVER and phase == GamePhase.GAME_OVER:
            if snap.human and snap.ai and snap.human.score > snap.ai.score:
                sounds.play("win")

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_DARK)
        snap = self.sm.snapshot()

        right_x = self.HAND_W
        right_w = W - self.HAND_W

        # Scoreboard
        self.scoreboard.draw(surface, snap, 0, 0, W)

        # Card hand (top of left panel)
        hand_y = self.SCORE_H
        if snap.human:
            if snap.phase in (GamePhase.WAITING_OFFENSE_CARD, GamePhase.WAITING_DEFENSE_CARD):
                self.card_hand.update(snap.human.hand, True, len(snap.ai.hand) if snap.ai else 0)
            else:
                self.card_hand.update(snap.human.hand if snap.human else [], False,
                                     len(snap.ai.hand) if snap.ai else 0)
        self.card_hand.draw(surface, 0, hand_y, self.HAND_W, self.HAND_H)

        # Drive chart (bottom of left panel)
        chart_y = hand_y + self.HAND_H
        if snap.offense:
            self.drive_chart.draw(surface, snap.offense.rating, snap.offense.color.value,
                                  0, chart_y, self.HAND_W, self.CHART_H)

        # Field view
        field_y = self.SCORE_H
        off_name = snap.offense.name if snap.offense else ""
        self.field_view.draw(surface, snap.ball_pos, right_x, field_y, right_w, self.FIELD_H, off_name)

        # Card battle
        battle_y = field_y + self.FIELD_H
        off_name = snap.offense.name if snap.offense else ""
        def_name = snap.defense.name if snap.defense else ""

        battle_msg = ""
        show_cards = snap.phase in (
            GamePhase.SHOWING_CARD_BATTLE, GamePhase.SHOWING_MOVEMENT,
            GamePhase.SHOWING_JOKER, GamePhase.SHOWING_WAR,
        )

        if snap.phase == GamePhase.SHOWING_TOUCHDOWN:
            battle_msg = "TOUCHDOWN!"
        elif snap.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            battle_msg = "TOUCHDOWN! Choose extra point:"
        elif snap.phase == GamePhase.SHOWING_SAFETY:
            battle_msg = "SAFETY!"
        elif snap.phase == GamePhase.SHOWING_EXTRA_POINTS:
            roll_str = f" | d6:[{snap.extra_pt_roll}]" if snap.extra_pt_roll else ""
            battle_msg = snap.extra_pts_desc + roll_str
        elif snap.phase == GamePhase.SHOWING_WAR:
            battle_msg = snap.message
            show_cards = False
        elif snap.phase == GamePhase.SHOWING_PUNT:
            battle_msg = snap.message
        elif snap.phase == GamePhase.SHOWING_SHORT_PUNT:
            battle_msg = snap.message
        elif snap.phase == GamePhase.SHOWING_FIELD_GOAL:
            battle_msg = snap.message
        elif snap.phase == GamePhase.SHOWING_CLUTCH:
            battle_msg = snap.message
        elif snap.phase == GamePhase.SHOWING_MOVEMENT:
            battle_msg = snap.message
        elif snap.phase == GamePhase.QUARTER_START:
            battle_msg = snap.message
        elif snap.phase == GamePhase.QUARTER_END:
            battle_msg = snap.message
        elif snap.phase == GamePhase.AI_PLAYING_CARD:
            battle_msg = "AI is thinking..."
        elif snap.phase == GamePhase.AI_POST_MOVE:
            battle_msg = "AI choosing action..."
        elif snap.phase == GamePhase.WAITING_OFFENSE_CARD:
            battle_msg = "Pick your OFFENSE card"
        elif snap.phase == GamePhase.WAITING_DEFENSE_CARD:
            battle_msg = "Pick your DEFENSE card"
        elif snap.phase == GamePhase.WAITING_POST_MOVE:
            battle_msg = f"Ball at {snap.ball_pos}"

        if show_cards and snap.off_card and snap.def_card:
            self.card_battle.draw(surface, snap.off_card, snap.def_card,
                                 off_name, def_name, right_x, battle_y, right_w, self.BATTLE_H)
        else:
            self.card_battle.draw(surface, None, None, "", "",
                                 right_x, battle_y, right_w, self.BATTLE_H, battle_msg)

        # Play log
        decision_y = H - self.DECISION_H
        log_y = battle_y + self.BATTLE_H
        log_h = decision_y - log_y
        self.play_log.draw(surface, snap.log_messages, right_x, log_y, right_w, log_h)

        # Decision panel
        is_deciding = snap.phase == GamePhase.WAITING_POST_MOVE
        ep_choice = snap.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE
        self.decision_panel.update(snap.can_punt, snap.can_fg, snap.can_clutch,
                                   snap.can_short_punt, is_deciding, snap.ball_pos,
                                   ep_choice_active=ep_choice)
        self.decision_panel.draw(surface, right_x, decision_y, right_w, self.DECISION_H)

        # Phase-specific prompt at bottom
        if snap.phase in (GamePhase.WAITING_OFFENSE_CARD, GamePhase.WAITING_DEFENSE_CARD):
            role = "OFFENSE" if snap.phase == GamePhase.WAITING_OFFENSE_CARD else "DEFENSE"
            prompt = self.font.render(f"Select {role} card (0-9 or arrows+enter)", True, HIGHLIGHT)
            surface.blit(prompt, (right_x + 12, H - 24))
        elif self.sm._is_showing_phase():
            prompt = self.font.render("Click or press any key to continue", True, DIM_TEXT)
            surface.blit(prompt, (right_x + 12, H - 24))
