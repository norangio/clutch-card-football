"""Headless tests for AI difficulty (easy / medium / hard).

Run from the ccf_pygame directory:
    python test_ai.py
"""

import random
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ccf.ai as ai_mod
from ccf.ai import (Difficulty, choose_card, post_move_choice, extra_point_choice)
from ccf.models import Card, Color, Team
from ccf.deck import card_value
from ccf.drive_chart import get_drive_result
from ccf.field import move as move_pos
from ccf.states import GamePhase
from ccf.state_machine import GameStateMachine


def make_team(name="T", rating=6, kick=2, color=Color.RED, clutch=3, hand=None):
    t = Team(name, rating, kick, color, clutch)
    if hand is not None:
        t.hand = list(hand)
    return t


def drive_of(card, rating, color):
    if card.value == "Joker":
        return get_drive_result(color, rating, "A", "H")
    return get_drive_result(color, rating, card.value, card.suit)


class CardChoiceTest(unittest.TestCase):

    def test_medium_offense_picks_max_movement(self):
        hand = [Card("2", "S"), Card("A", "H"), Card("8", "C"), Card("J", "D")]
        team = make_team(rating=6, color=Color.RED, hand=hand)
        idx = choose_card("1", team, True, difficulty=Difficulty.MEDIUM)
        moves = [drive_of(c, 6, "red") for c in hand]
        self.assertEqual(drive_of(hand[idx], 6, "red"), max(moves))

    def test_hard_offense_picks_max_movement(self):
        hand = [Card("2", "S"), Card("A", "H"), Card("8", "C"), Card("J", "D")]
        team = make_team(rating=6, color=Color.RED, hand=hand)
        opponent = make_team(rating=6, color=Color.BLACK, hand=[Card("9", "C")])
        self.addCleanup(setattr, ai_mod, "MC_EPISODES", ai_mod.MC_EPISODES)
        ai_mod.MC_EPISODES = 400
        random.seed(42)
        idx = choose_card("1", team, True, difficulty=Difficulty.HARD,
                          opponent=opponent, deck_remaining=[])
        moves = [drive_of(c, 6, "red") for c in hand]
        self.assertEqual(drive_of(hand[idx], 6, "red"), max(moves))

    def test_hard_defense_beats_known_offense(self):
        off_card = Card("7", "S")
        hand = [Card("8", "C"), Card("2", "H"), Card("3", "D")]
        def_team = make_team(rating=6, color=Color.RED, hand=hand)
        off_team = make_team(rating=6, color=Color.BLACK, hand=[off_card])
        self.addCleanup(setattr, ai_mod, "MC_EPISODES", ai_mod.MC_EPISODES)
        ai_mod.MC_EPISODES = 400
        random.seed(7)
        idx = choose_card("1", def_team, False, difficulty=Difficulty.HARD,
                          opponent=off_team, opponent_card=off_card, deck_remaining=[])
        self.assertGreaterEqual(card_value(def_team.hand[idx]), card_value(off_card))

    def test_medium_defense_plays_joker_on_turnover(self):
        off_card = Card("5", "C")
        hand = [Card("2", "S"), Card("K", "D"), Card("Joker")]
        def_team = make_team(rating=6, color=Color.RED, hand=hand)
        idx = choose_card("1", def_team, False, difficulty=Difficulty.MEDIUM,
                          opponent_card=off_card)
        self.assertEqual(def_team.hand[idx].value, "Joker")


class PostMoveTest(unittest.TestCase):

    def test_medium_post_move(self):
        self.assertEqual(post_move_choice("1", 0, False, difficulty=Difficulty.MEDIUM), "P")
        self.assertEqual(post_move_choice("Z2", 0, False, difficulty=Difficulty.MEDIUM), "F")
        self.assertEqual(post_move_choice("Z2", 1, False, difficulty=Difficulty.MEDIUM), "C")
        self.assertEqual(post_move_choice("1", 3, False, difficulty=Difficulty.MEDIUM), "C")

    def test_easy_post_move_punts_outside_zone(self):
        for _ in range(20):
            self.assertEqual(post_move_choice("1", 0, False, difficulty=Difficulty.EASY), "P")

    def test_easy_post_move_random_in_zone(self):
        seen = set()
        for _ in range(200):
            seen.add(post_move_choice("Z2", 0, False, difficulty=Difficulty.EASY))
        self.assertTrue(seen <= {"P", "F"})


class ExtraPointTest(unittest.TestCase):

    def test_medium_always_kicks(self):
        self.assertEqual(extra_point_choice(Difficulty.MEDIUM, 0, 1), "K")

    def test_hard_goes_for_two_late_when_trailing(self):
        self.assertEqual(extra_point_choice(Difficulty.HARD, -8, 4), "2")
        self.assertEqual(extra_point_choice(Difficulty.HARD, -8, 2), "K")
        self.assertEqual(extra_point_choice(Difficulty.HARD, 0, 4), "K")

    def test_easy_random(self):
        choices = {extra_point_choice(Difficulty.EASY, 0, 1) for _ in range(100)}
        self.assertTrue(choices <= {"K", "2"})


class FullGameTest(unittest.TestCase):

    def test_hard_beats_easy_full_games(self):
        self.addCleanup(setattr, ai_mod, "MC_EPISODES", ai_mod.MC_EPISODES)
        ai_mod.MC_EPISODES = 60
        n = 30
        hard_total = 0
        easy_total = 0
        hard_wins = 0
        for i in range(n):
            _, ai_score = simulate_game(Difficulty.HARD, Difficulty.EASY, seed=2000 + i)
            hard_total += ai_score
        for i in range(n):
            _, ai_score = simulate_game(Difficulty.EASY, Difficulty.EASY, seed=2000 + i)
            easy_total += ai_score
            if ai_score > 0:
                hard_wins += 1
        print(f"\n[sim] hard avg {hard_total / n:.2f} vs easy avg {easy_total / n:.2f} "
              f"over {n} games")
        self.assertGreater(hard_total, easy_total)


def simulate_game(ai_difficulty, human_difficulty, seed=0):
    """Play a full headless game. Returns (human_score, ai_score)."""
    random.seed(seed)
    sm = GameStateMachine()
    sm.provide_setup("Human", 6, 2, Color.RED, 3,
                     "Robot", 6, 2, 3, difficulty=ai_difficulty)

    guard = 0
    while sm.phase != GamePhase.GAME_OVER and guard < 200000:
        guard += 1
        if sm.phase in (GamePhase.WAITING_OFFENSE_CARD, GamePhase.WAITING_DEFENSE_CARD):
            human_is_offense = sm.offense == sm.human
            idx = choose_card(
                sm.pos,
                sm.human if human_is_offense else sm.defense,
                human_is_offense,
                difficulty=human_difficulty,
                opponent=(sm.defense if human_is_offense else sm.offense),
                opponent_card=sm._off_card,
                deck_remaining=list(sm.deck),
            )
            sm.provide_card(idx)
        elif sm.phase == GamePhase.WAITING_POST_MOVE:
            choice = post_move_choice(
                sm.pos, sm.offense.clutch, sm.offense.clutch_used,
                difficulty=human_difficulty, team=sm.offense,
                opponent=sm.defense, deck_remaining=list(sm.deck),
            )
            sm.provide_post_move(choice)
        elif sm.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            scorer = sm._scorer or sm.offense
            opponent = sm.defense if scorer == sm.offense else sm.offense
            choice = extra_point_choice(
                human_difficulty,
                score_diff=scorer.score - opponent.score,
                quarter=sm.quarter,
            )
            sm.provide_extra_point_choice(choice)
        else:
            sm.advance()

    if sm.phase != GamePhase.GAME_OVER:
        raise RuntimeError(f"Simulation did not finish (phase={sm.phase}, guard={guard})")
    return sm.human.score, sm.ai.score


class JokerRuleTest(unittest.TestCase):
    """New joker scale: offense (def<4 TD, 4-10 +3, J-A +1); defense (off<4 TD, 4-10 Z3, J-A no gain)."""

    def _sim(self, off_card, def_card, pos="1"):
        off_team = make_team(name="O", color=Color.RED)
        def_team = make_team(name="D", color=Color.BLACK)
        return ai_mod._simulate_play(off_card, def_card, pos, off_team, def_team, [])

    def test_offense_joker_td_vs_def_2(self):
        out = self._sim(Card("Joker"), Card("2", "S"))
        self.assertTrue(out["td"])
        self.assertFalse(out["turnover"])
        self.assertFalse(out["def_td"])

    def test_offense_joker_gain_3_vs_def_7(self):
        out = self._sim(Card("Joker"), Card("7", "C"))
        self.assertEqual(out["new_pos"], move_pos("1", 3)[0])
        self.assertFalse(out["td"])
        self.assertFalse(out["turnover"])

    def test_offense_joker_gain_1_vs_def_king(self):
        out = self._sim(Card("Joker"), Card("K", "D"))
        self.assertEqual(out["new_pos"], move_pos("1", 1)[0])
        self.assertFalse(out["td"])
        self.assertFalse(out["turnover"])

    def test_defense_joker_td_vs_off_2(self):
        out = self._sim(Card("2", "S"), Card("Joker"))
        self.assertTrue(out["def_td"])
        self.assertFalse(out["td"])
        self.assertFalse(out["turnover"])

    def test_defense_joker_z3_vs_off_7(self):
        out = self._sim(Card("7", "S"), Card("Joker"))
        self.assertEqual(out["new_pos"], "Z3")
        self.assertTrue(out["turnover"])
        self.assertFalse(out["def_td"])

    def test_defense_joker_no_gain_vs_off_ace(self):
        out = self._sim(Card("A", "H"), Card("Joker"))
        self.assertEqual(out["new_pos"], "1")
        self.assertFalse(out["turnover"])
        self.assertFalse(out["td"])
        self.assertFalse(out["def_td"])


class JokerStateMachineTest(unittest.TestCase):
    """Integration of the joker rules through the real state machine."""

    def _sm(self):
        sm = GameStateMachine()
        sm.provide_setup("Human", 6, 2, Color.RED, 3,
                         "Robot", 6, 2, 3, difficulty=Difficulty.MEDIUM)
        return sm

    def _step(self, sm):
        """Advance until the phase changes (runs one auto-transition)."""
        start = sm.phase
        guard = 0
        while sm.phase == start and guard < 1000:
            sm.advance()
            guard += 1
        if sm.phase == start:
            raise RuntimeError(f"phase did not change from {start}")

    def test_offense_joker_td_scores(self):
        sm = self._sm()
        sm._off_card = Card("Joker")
        sm._def_card = Card("2", "S")
        sm.pos = "1"
        sm._resolve_play()
        self.assertEqual(sm.phase, GamePhase.SHOWING_JOKER)
        self._step(sm)
        self.assertEqual(sm.human.score, 6)
        self.assertEqual(sm.phase, GamePhase.SHOWING_TOUCHDOWN)

    def test_offense_joker_gain_3(self):
        sm = self._sm()
        sm._off_card = Card("Joker")
        sm._def_card = Card("7", "C")
        sm.pos = "1"
        sm._resolve_play()
        self._step(sm)
        self.assertEqual(sm.pos, move_pos("1", 3)[0])
        self.assertEqual(sm.phase, GamePhase.WAITING_POST_MOVE)

    def test_defense_joker_td_then_pat_possession(self):
        sm = self._sm()
        sm.offense, sm.defense = sm.ai, sm.human  # human on defense
        sm._off_card = Card("2", "S")
        sm._def_card = Card("Joker")
        sm.pos = "1"
        sm._resolve_play()
        self.assertEqual(sm.phase, GamePhase.SHOWING_JOKER)
        self._step(sm)  # resolve joker -> defensive TD
        self.assertEqual(sm.human.score, 6)
        self.assertEqual(sm.phase, GamePhase.SHOWING_TOUCHDOWN)
        self._step(sm)  # scorer is human -> ask for PAT
        self.assertEqual(sm.phase, GamePhase.WAITING_EXTRA_POINT_CHOICE)
        random.seed(3)
        sm.provide_extra_point_choice("K")
        self.assertEqual(sm.phase, GamePhase.SHOWING_EXTRA_POINTS)
        self.assertGreaterEqual(sm.human.score, 6)
        self._step(sm)  # possession: non-scoring team (AI) keeps the ball at 1
        self.assertEqual(sm.pos, "1")
        self.assertEqual(sm.offense, sm.ai)

    def test_defense_joker_z3_turnover(self):
        sm = self._sm()
        sm._off_card = Card("7", "S")
        sm._def_card = Card("Joker")
        sm.pos = "1"
        sm._resolve_play()
        self._step(sm)
        self.assertEqual(sm.pos, "Z3")
        self.assertEqual(sm.offense, sm.ai)
        self.assertEqual(sm.defense, sm.human)

    def test_defense_joker_no_gain_keeps_ball(self):
        sm = self._sm()
        sm._off_card = Card("A", "H")
        sm._def_card = Card("Joker")
        sm.pos = "1"
        sm._resolve_play()
        self._step(sm)
        self.assertEqual(sm.pos, "1")
        self.assertEqual(sm.offense, sm.human)
        self.assertEqual(sm.phase, GamePhase.WAITING_POST_MOVE)


class StatsTest(unittest.TestCase):
    """End-of-game stats tracking: segments, FG made/att, punts."""

    def _sm(self, kick=2):
        sm = GameStateMachine()
        sm.provide_setup("Human", 6, kick, Color.RED, 3,
                         "Robot", 6, 2, 3, difficulty=Difficulty.MEDIUM)
        return sm

    def _step(self, sm):
        start = sm.phase
        guard = 0
        while sm.phase == start and guard < 1000:
            sm.advance()
            guard += 1
        if sm.phase == start:
            raise RuntimeError(f"phase did not change from {start}")

    def test_offense_joker_tracks_segments(self):
        sm = self._sm()
        sm._off_card = Card("Joker")
        sm._def_card = Card("7", "C")
        sm.pos = "1"
        sm._resolve_play()
        self._step(sm)
        self.assertEqual(sm.human.segments, 3)

    def test_punt_tracks_punts(self):
        sm = self._sm()
        sm._do_punt()
        self.assertEqual(sm.human.punts, 1)

    def test_short_punt_tracks_punts(self):
        sm = self._sm()
        sm._do_short_punt()
        self.assertEqual(sm.human.punts, 1)

    def test_fg_tracks_attempt_and_make(self):
        sm = self._sm(kick=6)  # high kick -> Z3 FG is guaranteed
        sm.pos = "Z3"
        sm._do_field_goal()
        self.assertEqual(sm.human.fg_att, 1)
        self.assertEqual(sm.human.fg_made, 1)
        self.assertEqual(sm.human.score, 3)


class AiVsAiTest(unittest.TestCase):
    """AI vs AI mode: both teams are driven by the AI; no human input needed."""

    WAITING_PHASES = (
        GamePhase.WAITING_OFFENSE_CARD, GamePhase.WAITING_DEFENSE_CARD,
        GamePhase.WAITING_POST_MOVE, GamePhase.WAITING_EXTRA_POINT_CHOICE,
    )

    def _sm(self, difficulty=Difficulty.MEDIUM, seed=0):
        random.seed(seed)
        sm = GameStateMachine()
        sm.provide_setup("Team A", 7, 2, Color.RED, 3,
                         "Team B", 6, 2, 3, difficulty=difficulty,
                         ai_vs_ai=True)
        return sm

    def test_full_game_completes_without_human_input(self):
        sm = self._sm()
        guard = 0
        while sm.phase != GamePhase.GAME_OVER and guard < 300000:
            guard += 1
            self.assertNotIn(sm.phase, self.WAITING_PHASES,
                             f"AI vs AI reached human-waiting phase {sm.phase}")
            sm.advance()
        self.assertEqual(sm.phase, GamePhase.GAME_OVER)
        self.assertIsNotNone(sm.human.score)
        self.assertIsNotNone(sm.ai.score)

    def test_snapshot_flag(self):
        sm = self._sm()
        self.assertTrue(sm.snapshot().ai_vs_ai)

    def test_fast_delays_applied(self):
        sm = self._sm()
        self.assertLess(sm._auto_advance_delay, int(2.0 * sm._fps))
        self.assertLess(sm._ai_delay_frames, int(0.75 * sm._fps))

    def test_normal_mode_not_ai_vs_ai(self):
        random.seed(0)
        sm = GameStateMachine()
        sm.provide_setup("Human", 6, 2, Color.RED, 3, "Robot", 6, 2, 3)
        self.assertFalse(sm.snapshot().ai_vs_ai)
        self.assertEqual(sm._auto_advance_delay, int(2.0 * sm._fps))


if __name__ == "__main__":
    unittest.main(verbosity=2)
