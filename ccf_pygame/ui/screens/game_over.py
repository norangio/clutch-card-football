"""Game over screen with final score and play again button."""

import pygame
from ui.colors import *
from ui.font import get_font
from ccf.states import GameSnapshot


class GameOverScreen:
    def __init__(self):
        self.font = get_font(12)
        self.title_font = get_font(22)
        self.score_font = get_font(16)
        self.play_again = False
        self._btn_rect = pygame.Rect(360, 510, 240, 45)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.play_again = True

    def handle_click(self, pos):
        if self._btn_rect.collidepoint(pos):
            self.play_again = True

    def draw(self, surface: pygame.Surface, snap: GameSnapshot):
        surface.fill(BG_DARK)

        # Title
        title = self.title_font.render("GAME OVER", True, AMBER)
        surface.blit(title, (480 - title.get_width() // 2, 120))

        if not snap.human or not snap.ai:
            return

        # Final score
        h_color = RED_TEAM if snap.human.color.value == "red" else BLACK_TEAM
        a_color = RED_TEAM if snap.ai.color.value == "red" else BLACK_TEAM

        h_text = self.score_font.render(f"{snap.human.name}: {snap.human.score}", True, h_color)
        surface.blit(h_text, (480 - h_text.get_width() // 2, 240))

        a_text = self.score_font.render(f"AI: {snap.ai.score}", True, a_color)
        surface.blit(a_text, (480 - a_text.get_width() // 2, 300))

        # Result
        result_text = snap.message
        result_color = TD_GOLD if "WIN" in result_text and "AI" not in result_text else SAFETY_RED
        if "TIE" in result_text:
            result_color = WHITE
        result = self.title_font.render(result_text, True, result_color)
        surface.blit(result, (480 - result.get_width() // 2, 390))

        # Play again button
        pygame.draw.rect(surface, BUTTON_BG, self._btn_rect)
        pygame.draw.rect(surface, BUTTON_BORDER, self._btn_rect, 2)
        btn_text = self.font.render("PLAY AGAIN", True, AMBER)
        surface.blit(btn_text, (480 - btn_text.get_width() // 2, 522))

        inst = self.font.render("ENTER to play again", True, DIM_TEXT)
        surface.blit(inst, (480 - inst.get_width() // 2, 600))
