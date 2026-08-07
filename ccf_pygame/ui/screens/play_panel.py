"""Phase-aware centre play panel."""

import pygame

from ccf.states import GamePhase
from ui import draw as d
from ui.layout import PLAY_RECT
from ui.screens.hand_rail import draw_card_face
from ui.theme import (BORDER, DIM, GOLD, GREEN_OK, MUTED, PANEL, RED, TEXT,
                      team_color)


class PlayPanel:
    @staticmethod
    def _panel(surface):
        d.rrect(surface, PLAY_RECT, PANEL, radius=12)
        d.rrect(surface, PLAY_RECT, BORDER, radius=12, width=1)

    @staticmethod
    def _touchdown_detail(snap):
        message = snap.message or ""
        if message.upper().startswith("TOUCHDOWN!"):
            return message.split("!", 1)[1].strip()
        return f"{snap.offense.name}  +6" if snap.offense else "+6"

    @staticmethod
    def _message(surface, message, color=TEXT, size=30, subline=None):
        rect = PLAY_RECT
        message = message or "—"
        chosen = size
        while chosen > 20:
            font = d.font("cond", chosen, "bold")
            if d.text_size(message, font, tight=True)[0] <= rect.w - 36:
                break
            chosen -= 2
        y = rect.centery - (10 if subline else 0)
        d.text(surface, message, (rect.centerx, y),
               d.font("cond", chosen, "bold"), color,
               anchor="center", tight=True)
        if subline:
            d.text(surface, subline, (rect.centerx, rect.bottom - 24),
                   d.font("inter", 11, "semibold"), MUTED,
                   anchor="center", tight=True)

    @staticmethod
    def _touchdown(surface, snap):
        rect = PLAY_RECT
        d.text(surface, "TOUCHDOWN", (rect.centerx, rect.centery - 12),
               d.font("cond", 54, "bold"), GOLD,
               anchor="center", tracking=3, tight=True)
        d.text(surface, PlayPanel._touchdown_detail(snap),
               (rect.centerx, rect.bottom - 26),
               d.font("inter", 13, "semibold"), TEXT,
               anchor="center", tight=True)

    @staticmethod
    def _safety(surface, snap):
        rect = PLAY_RECT
        d.text(surface, "SAFETY!", (rect.centerx, rect.centery - 12),
               d.font("cond", 52, "bold"), RED,
               anchor="center", tracking=2, tight=True)
        detail = (snap.message or "").split("!", 1)[-1].strip()
        if detail:
            d.text(surface, detail, (rect.centerx, rect.bottom - 26),
                   d.font("inter", 13, "semibold"), TEXT,
                   anchor="center", tight=True)

    @staticmethod
    def _cards(surface, snap, title="THE PLAY", movement=False):
        rect = PLAY_RECT
        d.text(surface, title, (rect.centerx, rect.y + 16),
               d.font("inter", 10, "bold"), DIM,
               anchor="center", tracking=2, tight=True)
        for tag, card, team, center_x in (
            ("OFFENSE", snap.off_card, snap.offense, rect.centerx - 112),
            ("DEFENSE", snap.def_card, snap.defense, rect.centerx + 112),
        ):
            d.text(surface, tag, (center_x, rect.y + 38),
                   d.font("inter", 9, "bold"), team_color(team),
                   anchor="center", tracking=1, tight=True)
            card_rect = pygame.Rect(0, 0, 62, 54)
            card_rect.midtop = (center_x, rect.y + 48)
            draw_card_face(surface, card_rect, card, scale=0.86)
            d.text(surface, team.name if team else "",
                   (center_x, rect.bottom - 18),
                   d.font("inter", 10, "semibold"), MUTED,
                   anchor="center", tight=True)

        d.text(surface, "VS", (rect.centerx, rect.y + 76),
               d.font("cond", 26, "bold"), DIM,
               anchor="center", tight=True)
        if movement:
            badge = pygame.Rect(0, 0, 112, 22)
            badge.center = (rect.centerx, rect.y + 108)
            d.rrect(surface, badge, d.alpha(GREEN_OK, 40), radius=11)
            d.text(surface, f"{snap.movement:+d} SEGMENTS", badge.center,
                   d.font("inter", 10, "bold"), GREEN_OK,
                   anchor="center", tight=True)

    def draw(self, surface, snap):
        self._panel(surface)
        phase = snap.phase

        if phase in (GamePhase.SHOWING_TOUCHDOWN,
                     GamePhase.WAITING_EXTRA_POINT_CHOICE):
            self._touchdown(surface, snap)
        elif phase == GamePhase.SHOWING_SAFETY:
            self._safety(surface, snap)
        elif phase == GamePhase.SHOWING_EXTRA_POINTS:
            roll = f"d6:[{snap.extra_pt_roll}]" if snap.extra_pt_roll else None
            self._message(surface, snap.extra_pts_desc or snap.message,
                          GOLD if snap.extra_pts else TEXT, 32, roll)
        elif phase == GamePhase.SHOWING_WAR:
            # Cards are intentionally hidden for WAR.
            self._message(surface, snap.message, GOLD, 30)
        elif phase == GamePhase.SHOWING_JOKER and snap.off_card and snap.def_card:
            self._cards(surface, snap, title=snap.message or "JOKER")
        elif phase in (GamePhase.SHOWING_CARD_BATTLE,
                       GamePhase.SHOWING_MOVEMENT) \
                and snap.off_card and snap.def_card:
            self._cards(surface, snap,
                        movement=phase == GamePhase.SHOWING_MOVEMENT)
        elif phase == GamePhase.WAITING_OFFENSE_CARD:
            self._message(surface, "Pick your OFFENSE card")
        elif phase == GamePhase.WAITING_DEFENSE_CARD:
            # Do not use snap.off_card here: it contains the hidden AI card.
            self._message(surface, "Pick your DEFENSE card")
        elif phase == GamePhase.AI_PLAYING_CARD:
            self._message(surface, "AI is thinking...", MUTED)
        elif phase == GamePhase.WAITING_POST_MOVE:
            self._message(surface, f"Ball at {snap.ball_pos}")
        elif phase == GamePhase.AI_POST_MOVE:
            self._message(surface, "AI choosing action...", MUTED)
        elif phase == GamePhase.WAITING_CONFIRM:
            self._message(surface, snap.message, subline="click to continue")
        else:
            self._message(surface, snap.message)
