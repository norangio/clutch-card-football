"""Headless regression tests for the Broadcast presentation layer."""

import os
from time import perf_counter
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ccf.models import Card, Color, Team
from ccf.states import GamePhase, GameSnapshot
from ui.app import PygameApp
from ui import draw as d
from ui.layout import HAND_RECT
from ui.screens.action_bar import ActionBar
from ui.screens.hand_rail import HandRail
from ui.screens.play_panel import PlayPanel
from ui.screens.play_screen import PlayScreen
from ui.screens.setup_screen import SetupScreen


@pytest.fixture(scope="module", autouse=True)
def pygame_display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def surface():
    return pygame.Surface((960, 720))


def make_snapshot(phase=GamePhase.WAITING_OFFENSE_CARD, hand_count=7):
    human = Team("BULLDOGS", 8, 2, Color.RED, 3)
    ai = Team("RIVALS", 7, 3, Color.BLACK, 2)
    cards = [
        Card("2", "S"), Card("5", "H"), Card("6", "D"),
        Card("8", "S"), Card("10", "H"), Card("J", "C"),
        Card("Q", "S"), Card("K", "H"), Card("A", "D"),
    ]
    human.hand = cards[:hand_count]
    ai.hand = [Card("3", "S"), Card("7", "D"), Card("Joker")]
    return GameSnapshot(
        phase=phase,
        quarter=4,
        turn=1,
        turns_in_quarter=8,
        ball_pos="Z2",
        difficulty="hard",
        human=human,
        ai=ai,
        offense=human,
        defense=ai,
        off_card=Card("K", "S"),
        def_card=Card("8", "C"),
        movement=2,
        extra_pts_desc="2-point conversion GOOD!",
        extra_pt_roll=6,
        message="Ready",
        log_messages=["=== QUARTER 4 ===", "TOUCHDOWN! BULLDOGS +6"],
        can_punt=True,
        can_fg=True,
        can_clutch=True,
        can_short_punt=True,
    )


def key_event(key, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode)


def test_one_to_nine_cards_fit_and_click_their_own_rect(surface):
    rail = HandRail()
    for count in range(1, 10):
        snap = make_snapshot(hand_count=count)
        rail.draw(surface, snap)
        assert len(rail.card_rects) == count
        for index, rect in enumerate(rail.card_rects):
            assert HAND_RECT.contains(rect)
            assert rect.bottom <= HAND_RECT.bottom - 40
            for point in (rect.topleft, (rect.right - 1, rect.y),
                          (rect.x, rect.bottom - 1),
                          (rect.right - 1, rect.bottom - 1), rect.center):
                assert rail.handle_click(point) == index


def test_hand_keyboard_bindings(surface):
    rail = HandRail()
    rail.draw(surface, make_snapshot(hand_count=9))
    assert rail.handle_event(key_event(pygame.K_8, "8")) == 8
    rail.selected = 4
    assert rail.handle_event(key_event(pygame.K_UP)) is None
    assert rail.selected == 3
    assert rail.handle_event(key_event(pygame.K_DOWN)) is None
    assert rail.selected == 4
    assert rail.handle_event(key_event(pygame.K_SPACE, " ")) == 4


def test_waiting_for_defense_never_draws_hidden_offense_card(surface):
    snap = make_snapshot(GamePhase.WAITING_DEFENSE_CARD)
    snap.offense, snap.defense = snap.ai, snap.human
    snap.def_card = None
    with patch("ui.screens.play_panel.draw_card_face") as card_draw:
        PlayPanel().draw(surface, snap)
    card_draw.assert_not_called()


@pytest.mark.parametrize("phase", list(GamePhase))
def test_every_play_phase_renders_deliberately(surface, phase):
    if phase in (GamePhase.SETUP_TEAMS, GamePhase.GAME_OVER):
        pytest.skip("Dedicated full-screen phase")
    snap = make_snapshot(phase)
    if phase == GamePhase.SHOWING_TOUCHDOWN:
        snap.message = "TOUCHDOWN! BULLDOGS +6"
    elif phase == GamePhase.SHOWING_SAFETY:
        snap.message = "SAFETY! RIVALS +2"
    elif phase == GamePhase.SHOWING_WAR:
        snap.message = "WAR! Turnover"
    PlayPanel().draw(surface, snap)


def test_action_bindings_honor_enabled_flags(surface):
    snap = make_snapshot(GamePhase.WAITING_POST_MOVE)
    snap.can_fg = False
    snap.can_clutch = False
    bar = ActionBar()
    bar.draw(surface, snap)
    assert bar.handle_event(key_event(pygame.K_1, "1")) == "P"
    assert bar.handle_event(key_event(pygame.K_2, "2")) is None
    assert bar.handle_event(key_event(pygame.K_3, "3")) is None
    assert bar.handle_event(key_event(pygame.K_4, "4")) == "S"
    disabled_fg = bar._buttons[1][0]
    assert bar.handle_click(disabled_fg.center) is None
    assert bar.handle_click(bar._buttons[0][0].center) == "P"


def test_extra_point_keyboard_and_mouse_bindings(surface):
    bar = ActionBar()
    bar.draw(surface, make_snapshot(GamePhase.WAITING_EXTRA_POINT_CHOICE))
    assert bar.handle_event(key_event(pygame.K_k, "k")) == "K"
    assert bar.handle_event(key_event(pygame.K_2, "2")) == "2"
    assert bar.handle_click(bar._buttons[0][0].center) == "K"
    assert bar.handle_click(bar._buttons[1][0].center) == "2"


def test_display_font_falls_back_for_arrow_without_tofu(surface):
    rendered = d.text(surface, "FG GOOD → +3", (10, 10),
                      d.font("cond", 30, "bold"), (255, 255, 255))
    assert rendered.w > d.text_size("FG GOOD  +3",
                                    d.font("cond", 30, "bold"))[0]


def test_setup_defaults_and_mouse_keyboard_start():
    setup = SetupScreen()
    original_rating = setup.fields[1]["value"]
    setup.handle_click(setup._right_rects[1].center)
    assert int(setup.fields[1]["value"]) == int(original_rating) + 1
    setup.handle_click(setup._left_rects[1].center)
    assert setup.fields[1]["value"] == original_rating
    setup.handle_click(setup.START_RECT.center)
    result = setup.get_result()
    assert result["human_name"] == "Bulldogs"
    assert result["human_rating"] == 6
    assert result["human_kick"] == 2
    assert result["human_color"] == Color.RED
    assert result["human_clutch"] == 3
    assert result["ai_name"] == "Rivals"
    assert result["ai_rating"] == 6
    assert result["ai_kick"] == 2
    assert result["ai_clutch"] == 3
    assert result["difficulty"] == "medium"
    assert result["ai_vs_ai"] is False

    keyboard = SetupScreen()
    keyboard.handle_event(key_event(pygame.K_UP))
    keyboard.handle_event(key_event(pygame.K_RETURN, "\r"))
    assert keyboard.ready


def test_warm_play_screen_draw_stays_under_budget(surface):
    class FakeStateMachine:
        snap = make_snapshot()

        def snapshot(self):
            return self.snap

    screen = PlayScreen(FakeStateMachine())
    for _ in range(4):
        screen.draw(surface)
    started = perf_counter()
    for _ in range(60):
        screen.draw(surface)
    average_ms = (perf_counter() - started) * 1000 / 60
    assert average_ms < 8.0


def test_real_app_event_queue_start_card_action_pat_and_restart():
    app = PygameApp()
    pygame.event.clear()

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        button=1,
        pos=SetupScreen.START_RECT.center,
    ))
    app._handle_events()
    assert app.state_machine.phase == GamePhase.QUARTER_START
    app._draw()

    app.state_machine._auto_advance_delay = 1
    app.state_machine._ai_delay_frames = 1
    app.state_machine.advance()
    assert app.state_machine.phase == GamePhase.WAITING_OFFENSE_CARD

    pygame.event.post(key_event(pygame.K_0, "0"))
    app._handle_events()
    assert app.state_machine.phase == GamePhase.SHOWING_CARD_BATTLE

    app.state_machine.phase = GamePhase.WAITING_POST_MOVE
    app.state_machine.pos = "1"
    app._draw()
    pygame.event.post(key_event(pygame.K_1, "1"))
    app._handle_events()
    assert app.state_machine.phase == GamePhase.SHOWING_PUNT

    app.state_machine.phase = GamePhase.WAITING_EXTRA_POINT_CHOICE
    app.state_machine._scorer = app.state_machine.human
    app._draw()
    pygame.event.post(key_event(pygame.K_k, "k"))
    app._handle_events()
    assert app.state_machine.phase == GamePhase.SHOWING_EXTRA_POINTS

    app.state_machine.phase = GamePhase.GAME_OVER
    pygame.event.post(key_event(pygame.K_RETURN, "\r"))
    app._handle_events()
    assert app.state_machine.phase == GamePhase.SETUP_TEAMS
