"""Top scoreboard bar."""

import pygame
from ui.colors import *
from ui.font import get_font
from ccf.states import GamePhase, GameSnapshot


class Scoreboard:
    def __init__(self):
        self.font = get_font(12)
        self.small_font = get_font(10)
        self.height = 72

    def draw(self, surface: pygame.Surface, snap: GameSnapshot, x: int, y: int, w: int):
        rect = pygame.Rect(x, y, w, self.height)
        pygame.draw.rect(surface, SCORE_BG, rect)
        pygame.draw.rect(surface, SCORE_BORDER, rect, 1)

        if not snap.human or not snap.ai:
            return

        # --- Row 1 (y+10): Q | OFF/DEF | scores | play counter ---
        row1_y = y + 10

        # Quarter
        q_text = self.font.render(f"Q{snap.quarter}", True, AMBER)
        surface.blit(q_text, (x + 12, row1_y))

        # OFF/DEF indicator
        if snap.offense:
            role = "OFF" if snap.offense == snap.human else "DEF"
            role_color = TD_GOLD if role == "OFF" else SAFETY_RED
            role_text = self.small_font.render(role, True, role_color)
            surface.blit(role_text, (x + 60, row1_y + 2))

        # Scores
        h_color = RED_TEAM if snap.human.color.value == "red" else BLACK_TEAM
        a_color = RED_TEAM if snap.ai.color.value == "red" else BLACK_TEAM

        h_name = self.font.render(snap.human.name, True, h_color)
        surface.blit(h_name, (x + 110, row1_y))
        h_score = self.font.render(str(snap.human.score), True, WHITE)
        surface.blit(h_score, (x + 110 + h_name.get_width() + 12, row1_y))

        dash = self.font.render("-", True, GRAY)
        dash_x = x + 110 + h_name.get_width() + 12 + h_score.get_width() + 8
        surface.blit(dash, (dash_x, row1_y))

        a_label = self.font.render(snap.ai.name, True, a_color)
        surface.blit(a_label, (dash_x + 24, row1_y))
        a_score = self.font.render(str(snap.ai.score), True, WHITE)
        surface.blit(a_score, (dash_x + 24 + a_label.get_width() + 12, row1_y))

        # Play counter
        play_x = x + w - 60
        pt = self.font.render(f"{snap.turn}/{snap.turns_in_quarter}", True, DIM_TEXT)
        surface.blit(pt, (play_x, row1_y))

        # --- Row 2 (y+38): human CC + Mojo | spacer | AI CC + Mojo ---
        row2_y = y + 38

        # Human CC and Mojo
        cc_label = self.small_font.render("CC:", True, CLUTCH_YELLOW)
        surface.blit(cc_label, (x + 12, row2_y))
        coins = "*" * snap.human.clutch
        ct = self.small_font.render(coins if coins else "-", True, CLUTCH_YELLOW)
        surface.blit(ct, (x + 12 + cc_label.get_width() + 4, row2_y))

        mojo_label = self.small_font.render("MOJO:", True, MOJO_ORANGE)
        mojo_x = x + 12 + cc_label.get_width() + 4 + ct.get_width() + 16
        surface.blit(mojo_label, (mojo_x, row2_y))
        mojo_dots = "*" * snap.human.mojo
        md = self.small_font.render(mojo_dots if mojo_dots else "-", True, MOJO_ORANGE)
        surface.blit(md, (mojo_x + mojo_label.get_width() + 4, row2_y))

        # AI CC and Mojo (right-aligned section)
        ai_section_x = x + w // 2 + 60
        ai_cc_label = self.small_font.render(f"{snap.ai.name} CC:", True, CLUTCH_YELLOW)
        surface.blit(ai_cc_label, (ai_section_x, row2_y))
        ai_coins = "*" * snap.ai.clutch
        ai_ct = self.small_font.render(ai_coins if ai_coins else "-", True, CLUTCH_YELLOW)
        surface.blit(ai_ct, (ai_section_x + ai_cc_label.get_width() + 4, row2_y))

        ai_mojo_label = self.small_font.render("MOJO:", True, MOJO_ORANGE)
        ai_mojo_x = ai_section_x + ai_cc_label.get_width() + 4 + ai_ct.get_width() + 16
        surface.blit(ai_mojo_label, (ai_mojo_x, row2_y))
        ai_mojo_dots = "*" * snap.ai.mojo
        ai_md = self.small_font.render(ai_mojo_dots if ai_mojo_dots else "-", True, MOJO_ORANGE)
        surface.blit(ai_md, (ai_mojo_x + ai_mojo_label.get_width() + 4, row2_y))
