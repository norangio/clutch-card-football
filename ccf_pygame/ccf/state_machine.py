"""Game state machine — drives the full game flow without blocking calls."""

import random
from collections import deque
from typing import Optional

from .models import Card, Color, Team
from .deck import create_deck, card_value
from .field import move, SEGMENTS
from .drive_chart import get_card_result
from .rules import pat_kick, two_point_attempt, field_goal_attempt, punt_distance, short_punt_distance
from .ai import (Difficulty,
                 choose_card as ai_choose_card,
                 post_move_choice as ai_post_move,
                 extra_point_choice as ai_extra_point)
from .events import (
    BallMovedEvent,
    CardPlayedEvent,
    CardsRevealedEvent,
    ClutchUsedEvent,
    ExtraPointResolvedEvent,
    FieldGoalResolvedEvent,
    GameEndedEvent,
    GameEvent,
    JokerResolvedEvent,
    MojoChangedEvent,
    MojoConvertedToClutchEvent,
    PossessionChangedEvent,
    PuntResolvedEvent,
    QuarterEndedEvent,
    QuarterStartedEvent,
    SafetyScoredEvent,
    TouchdownScoredEvent,
    WarCardRevealedEvent,
    WarStartedEvent,
)
from .states import GamePhase, GameSnapshot

DECISION_PHASES = {
    GamePhase.WAITING_OFFENSE_CARD,
    GamePhase.WAITING_DEFENSE_CARD,
    GamePhase.WAITING_POST_MOVE,
    GamePhase.WAITING_EXTRA_POINT_CHOICE,
    GamePhase.GAME_OVER,
}


class GameStateMachine:
    def __init__(self, fps: int = 30, rng=None, seed: int | None = None):
        if rng is not None and seed is not None:
            raise ValueError("pass either rng or seed, not both")
        self._fps = fps
        self.seed = seed
        self._rng = random.Random(seed) if seed is not None else rng
        self.phase = GamePhase.SETUP_TEAMS
        self.deck: deque = deque()
        self.quarter = 1
        self.turn = 0
        self.turns_in_quarter = 6

        self.human: Optional[Team] = None
        self.ai: Optional[Team] = None
        self.offense: Optional[Team] = None
        self.defense: Optional[Team] = None

        self.difficulty = Difficulty.MEDIUM
        self.pos = "1"
        self.ai_vs_ai = False

        # Transient state for current play
        self._off_card: Optional[Card] = None
        self._def_card: Optional[Card] = None
        self._war_card: Optional[Card] = None
        self._clutch_card: Optional[Card] = None
        self._movement = 0
        self._new_pos = ""
        self._is_td = False
        self._is_safety = False
        self._extra_pts = 0
        self._extra_pts_desc = ""
        self._extra_pt_roll = 0
        self._scorer: Optional[Team] = None
        self._fg_success = False
        self._fg_roll = 0
        self._fg_total = 0
        self._fg_target = 0
        self._punt_dist = 0
        self._punt_roll = 0
        self._message = ""

        self.log: list[str] = []
        self._events: list[GameEvent] = []

        # Timer for auto-advance states (time-based, converted to frames at game FPS)
        self._timer = 0
        self._ai_delay_frames = max(1, int(0.75 * self._fps))
        self._auto_advance_delay = max(1, int(2.0 * self._fps))
        self._next_phase: Optional[GamePhase] = None
        self._pending_action = None  # callable for deferred logic

    def _apply_speed(self, fast: bool):
        if fast:
            self._auto_advance_delay = max(1, int(0.25 * self._fps))
            self._ai_delay_frames = max(1, int(0.1 * self._fps))
        else:
            self._auto_advance_delay = max(1, int(2.0 * self._fps))
            self._ai_delay_frames = max(1, int(0.75 * self._fps))

    def _log(self, msg: str):
        self.log.append(msg)

    def _emit(self, event: GameEvent) -> None:
        self._events.append(event)

    def _seat(self, team: Team) -> str:
        if team is self.human:
            return "home"
        if team is self.ai:
            return "away"
        raise ValueError("team does not belong to this game")

    def _emit_ball_moved(
        self,
        team: Team,
        from_ball: str,
        to_ball: str,
        segments: int,
        reason: str,
        *,
        is_touchdown: bool = False,
        is_safety: bool = False,
    ) -> None:
        self._emit(
            BallMovedEvent(
                self._seat(team),
                from_ball,
                to_ball,
                segments,
                reason,
                is_touchdown,
                is_safety,
            )
        )

    def snapshot(self) -> GameSnapshot:
        can_clutch, can_fg, can_punt, can_short = self._post_move_options()
        return GameSnapshot(
            phase=self.phase,
            quarter=self.quarter,
            turn=self.turn,
            turns_in_quarter=self.turns_in_quarter,
            ball_pos=self.pos,
            difficulty=self.difficulty.value,
            ai_vs_ai=self.ai_vs_ai,
            human=self.human,
            ai=self.ai,
            offense=self.offense,
            defense=self.defense,
            off_card=self._off_card,
            def_card=self._def_card,
            war_card=self._war_card,
            clutch_card=self._clutch_card,
            movement=self._movement,
            new_pos=self._new_pos,
            is_td=self._is_td,
            is_safety=self._is_safety,
            extra_pts=self._extra_pts,
            extra_pts_desc=self._extra_pts_desc,
            extra_pt_roll=self._extra_pt_roll,
            fg_success=self._fg_success,
            fg_roll=self._fg_roll,
            fg_total=self._fg_total,
            fg_target=self._fg_target,
            punt_distance=self._punt_dist,
            punt_roll=self._punt_roll,
            log_messages=list(self.log[-20:]),
            message=self._message,
            can_clutch=can_clutch,
            can_fg=can_fg,
            can_punt=can_punt,
            can_short_punt=can_short,
        )

    def _post_move_options(self):
        if self.offense is None:
            return False, False, True, False
        in_zone = self.pos in ("Z1", "Z2", "Z3")
        can_clutch = self.offense.clutch > 0 and not self.offense.clutch_used
        can_fg = in_zone
        can_punt = True
        can_short = in_zone
        return can_clutch, can_fg, can_punt, can_short

    # --- Public interface ---

    def provide_setup(self, human_name: str, human_rating: int, human_kick: int,
                      human_color: Color, human_clutch: int,
                      ai_name: str, ai_rating: int, ai_kick: int, ai_clutch: int,
                      difficulty: Difficulty = Difficulty.MEDIUM,
                      ai_vs_ai: bool = False):
        """Called from setup screen."""
        if isinstance(difficulty, str):
            difficulty = Difficulty(difficulty.lower())
        self.difficulty = difficulty
        self.human = Team(human_name, human_rating, human_kick, human_color, human_clutch)
        ai_color = Color.BLACK if human_color == Color.RED else Color.RED
        self.ai = Team(ai_name, ai_rating, ai_kick, ai_color, ai_clutch)
        self.ai_vs_ai = ai_vs_ai
        self._apply_speed(ai_vs_ai)
        self._log(f"=== CLUTCH CARD FOOTBALL ===")
        self._log(f"{human_name} ({human_color.value}) vs {ai_name} ({ai_color.value})"
                  + (" [AI vs AI]" if ai_vs_ai else ""))
        self._start_quarter()

    def provide_card(self, idx: int):
        """Human picks a card from hand."""
        if self.phase == GamePhase.WAITING_OFFENSE_CARD:
            self._off_card = self.offense.play(idx)
            self._log(f"{self.offense.name} plays {self._off_card.display}")
            self._emit(
                CardPlayedEvent(
                    self._seat(self.offense),
                    "offense",
                    self._off_card,
                    len(self.offense.hand),
                )
            )
            # Now defense plays
            if self.defense == self.human:
                self.phase = GamePhase.WAITING_DEFENSE_CARD
            else:
                self._ai_play_defense()
        elif self.phase == GamePhase.WAITING_DEFENSE_CARD:
            self._def_card = self.defense.play(idx)
            self._log(f"{self.defense.name} plays {self._def_card.display}")
            self._emit(
                CardPlayedEvent(
                    self._seat(self.defense),
                    "defense",
                    self._def_card,
                    len(self.defense.hand),
                )
            )
            self._resolve_cards()

    def provide_post_move(self, choice: str):
        """Human picks post-move action: 'P', 'F', 'C', 'S'."""
        if self.phase != GamePhase.WAITING_POST_MOVE:
            return
        self._execute_post_move(choice)

    def provide_extra_point_choice(self, choice: str):
        """Human picks extra point option: 'K' for PAT kick or '2' for 2-point attempt."""
        if self.phase != GamePhase.WAITING_EXTRA_POINT_CHOICE:
            return
        self._apply_extra_point(choice)

    def _apply_extra_point(self, choice: str):
        scorer = self._scorer or self.offense
        roll = None
        if choice == "K":
            pts, desc = pat_kick(rng=self._rng)
            self._extra_pts = pts
            self._extra_pts_desc = desc
            self._extra_pt_roll = 0
            scorer.score += pts
            self._message = desc
            self._log(f"PAT kick: {desc} (+{pts})")
        elif choice == "2":
            pts, roll, desc = two_point_attempt(rng=self._rng)
            self._extra_pts = pts
            self._extra_pts_desc = desc
            self._extra_pt_roll = roll
            scorer.score += pts
            self._message = desc
            self._log(f"2-point attempt: {desc} (+{pts})")
        else:
            return
        self._emit(
            ExtraPointResolvedEvent(
                self._seat(scorer),
                choice,
                pts > 0,
                roll,
                pts,
                scorer.score,
            )
        )
        self.phase = GamePhase.SHOWING_EXTRA_POINTS
        self._timer = 0

    def click_advance(self):
        """Player clicks/presses to advance from a showing state."""
        if self.phase == GamePhase.WAITING_CONFIRM:
            if self._pending_action:
                action = self._pending_action
                self._pending_action = None
                action()
            elif self._next_phase:
                self.phase = self._next_phase
                self._next_phase = None
        elif self._is_showing_phase():
            self._timer = self._auto_advance_delay  # force advance

    def advance(self):
        """Called once per frame for auto-advancing states."""
        if self.phase == GamePhase.AI_PLAYING_CARD:
            self._timer += 1
            if self._timer >= self._ai_delay_frames:
                self._timer = 0
                self._ai_play_offense()

        elif self.phase == GamePhase.AI_POST_MOVE:
            self._timer += 1
            if self._timer >= self._ai_delay_frames:
                self._timer = 0
                self._perform_ai_post_move()

        elif self._is_showing_phase():
            self._timer += 1
            if self._timer >= self._auto_advance_delay:
                self._timer = 0
                self._auto_transition()

    def _perform_ai_post_move(self):
        choice = ai_post_move(
            self.pos,
            self.offense.clutch,
            self.offense.clutch_used,
            difficulty=self.difficulty,
            team=self.offense,
            opponent=self.defense,
            deck_remaining=list(self.deck),
            rng=self._rng,
        )
        self._log(f"AI chooses: {choice}")
        self._execute_post_move(choice)

    def drain_events(self) -> list:
        """Return and clear events accumulated since the previous drain."""
        events = list(self._events)
        self._events.clear()
        return events

    def pump(self, max_steps: int = 200) -> list:
        """Run automatic transitions until a human decision is required.

        Unlike :meth:`advance`, this path has no frame timers. It is used by
        the web service, while Pygame keeps the existing timed presentation.
        """
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")

        steps = 0
        while self.phase not in DECISION_PHASES:
            if steps >= max_steps:
                raise RuntimeError(
                    f"pump exceeded max_steps={max_steps} in phase "
                    f"{self.phase.name}"
                )
            steps += 1

            if self.phase == GamePhase.AI_PLAYING_CARD:
                self._ai_play_offense()
            elif self.phase == GamePhase.AI_POST_MOVE:
                self._perform_ai_post_move()
            elif self._is_showing_phase():
                self._auto_transition()
            else:
                raise RuntimeError(
                    f"pump cannot advance phase {self.phase.name}"
                )

        return self.drain_events()

    def _is_showing_phase(self):
        return self.phase in (
            GamePhase.QUARTER_START, GamePhase.SHOWING_CARD_BATTLE,
            GamePhase.SHOWING_MOVEMENT, GamePhase.SHOWING_TOUCHDOWN,
            GamePhase.SHOWING_SAFETY, GamePhase.SHOWING_EXTRA_POINTS,
            GamePhase.SHOWING_WAR, GamePhase.SHOWING_JOKER,
            GamePhase.SHOWING_PUNT, GamePhase.SHOWING_FIELD_GOAL,
            GamePhase.SHOWING_CLUTCH, GamePhase.SHOWING_SHORT_PUNT,
            GamePhase.QUARTER_END,
        )

    def _auto_transition(self):
        """Handle auto-advance from showing states."""
        if self.phase == GamePhase.QUARTER_START:
            self._start_turn()
        elif self.phase == GamePhase.SHOWING_CARD_BATTLE:
            self._resolve_play()
        elif self.phase == GamePhase.SHOWING_MOVEMENT:
            if self._is_td:
                self._score_touchdown()
            elif self._is_safety:
                self._score_safety()
            else:
                self._enter_post_move()
        elif self.phase == GamePhase.SHOWING_TOUCHDOWN:
            scorer = self._scorer or self.offense
            if scorer == self.human and not self.ai_vs_ai:
                self.phase = GamePhase.WAITING_EXTRA_POINT_CHOICE
                self._timer = 0
            else:
                # AI chooses extra point (difficulty-aware)
                opponent = self.defense if scorer == self.offense else self.offense
                choice = ai_extra_point(self.difficulty,
                                        score_diff=scorer.score - opponent.score,
                                        quarter=self.quarter,
                                        rng=self._rng)
                self._log(f"AI chooses extra point: {choice}")
                self._apply_extra_point(choice)
        elif self.phase == GamePhase.SHOWING_EXTRA_POINTS:
            scorer = self._scorer or self.offense
            old_pos = self.pos
            self.pos = "1"
            if old_pos != self.pos:
                self._emit_ball_moved(
                    scorer, old_pos, self.pos, 0, "kickoff"
                )
            if self._scorer is None or self._scorer == self.offense:
                self._swap_sides(reason="touchdown")
            else:
                self._emit(
                    PossessionChangedEvent(
                        self._seat(scorer),
                        self._seat(self.offense),
                        self.pos,
                        "touchdown",
                    )
                )
            self._next_turn_or_end()
        elif self.phase == GamePhase.SHOWING_SAFETY:
            self.pos = "3"
            self._next_turn_or_end()
        elif self.phase == GamePhase.SHOWING_WAR:
            if self._war_card and self.offense and self._war_card.color == self.offense.color:
                old_pos = self.pos
                self.pos = "Z3"
                movement = SEGMENTS.index("Z3") - SEGMENTS.index(old_pos)
                self.offense.segments += movement
                self._emit_ball_moved(
                    self.offense, old_pos, self.pos, movement, "war"
                )
                self._enter_post_move()
            else:
                old_pos = self.pos
                self.pos = "3"
                movement = SEGMENTS.index("3") - SEGMENTS.index(old_pos)
                self._emit_ball_moved(
                    self.offense, old_pos, self.pos, movement, "turnover"
                )
                self._swap_sides(reason="war_turnover")
                self._next_turn_or_end()
        elif self.phase == GamePhase.SHOWING_JOKER:
            if self._pending_action:
                action = self._pending_action
                self._pending_action = None
                action()
        elif self.phase in (GamePhase.SHOWING_PUNT, GamePhase.SHOWING_SHORT_PUNT):
            reason = "punt" if self.phase == GamePhase.SHOWING_PUNT else "short_punt"
            self._swap_sides(reason=reason)
            self._next_turn_or_end()
        elif self.phase == GamePhase.SHOWING_FIELD_GOAL:
            old_pos = self.pos
            if self._fg_success:
                self.pos = "1"
                reason = "field_goal_made"
                move_reason = "kickoff"
            else:
                miss_map = {"Z3": "3", "Z2": "2", "Z1": "1"}
                self.pos = miss_map.get(self.pos, self.pos)
                reason = "field_goal_missed"
                move_reason = "turnover"
            if old_pos != self.pos:
                movement = SEGMENTS.index(self.pos) - SEGMENTS.index(old_pos)
                self._emit_ball_moved(
                    self.offense, old_pos, self.pos, movement, move_reason
                )
            self._swap_sides(reason=reason)
            self._next_turn_or_end()
        elif self.phase == GamePhase.SHOWING_CLUTCH:
            if self._pending_action:
                action = self._pending_action
                self._pending_action = None
                action()
        elif self.phase == GamePhase.QUARTER_END:
            self.quarter += 1
            if self.quarter <= 4:
                self._start_quarter()
            else:
                self._game_over()

    # --- Internal game flow ---

    def _start_quarter(self):
        previous_offense = self.offense
        fresh = self.quarter in (1, 3)
        if fresh:
            self.deck = create_deck(rng=self._rng)

        deal = {1: 7, 2: 6, 3: 7, 4: 8}.get(self.quarter, 7)
        if self.quarter in (1, 3):
            self.human.hand.clear()
            self.ai.hand.clear()
        for _ in range(deal):
            if self.deck:
                self.human.hand.append(self.deck.popleft())
            if self.deck:
                self.ai.hand.append(self.deck.popleft())

        if self.quarter in (1, 3):
            self.pos = "1"
        # Q1 human offense    
        if self.quarter == 1:
            self.offense, self.defense = self.human, self.ai
        # Q3 AI offense    
        if self.quarter == 3:
            self.offense, self.defense = self.ai, self.human

        # else:  # Q3  - AI ball
        #     self.offense, self.defense = self.ai, self.human

        self.turn = 0
        self.turns_in_quarter = 8 if self.quarter == 4 else 6
        receiver = self.offense.name
        self._message = f"QUARTER {self.quarter} -- {receiver} has ball"
        self._log(f"=== QUARTER {self.quarter} === {receiver} has ball")
        self.phase = GamePhase.QUARTER_START
        self._timer = 0
        self._emit(
            QuarterStartedEvent(
                self.quarter,
                self._seat(self.offense),
                deal,
                self.pos,
            )
        )
        if previous_offense is not None and previous_offense is not self.offense:
            self._emit(
                PossessionChangedEvent(
                    self._seat(previous_offense),
                    self._seat(self.offense),
                    self.pos,
                    "quarter_start",
                )
            )

    def _start_turn(self):
        self.turn += 1
        self.offense.clutch_used = False
        self._off_card = None
        self._def_card = None
        self._war_card = None
        self._clutch_card = None
        self._scorer = None
        self._is_td = False
        self._is_safety = False

        self._log(f"-- Play {self.turn}/{self.turns_in_quarter} | "
                  f"OFF: {self.offense.name} | Ball: {self.pos}")

        if self.offense == self.human and not self.ai_vs_ai:
            self.phase = GamePhase.WAITING_OFFENSE_CARD
        else:
            self.phase = GamePhase.AI_PLAYING_CARD
            self._timer = 0

    def _ai_play_offense(self):
        idx = ai_choose_card(self.pos, self.offense, True,
                             difficulty=self.difficulty,
                             opponent=self.defense,
                             deck_remaining=list(self.deck),
                             rng=self._rng)
        self._off_card = self.offense.play(idx)
        self._log(f"AI plays card ... ") # {self._off_card.display}")
        self._emit(
            CardPlayedEvent(
                self._seat(self.offense),
                "offense",
                self._off_card,
                len(self.offense.hand),
            )
        )

        if self.defense == self.human and not self.ai_vs_ai:
            self.phase = GamePhase.WAITING_DEFENSE_CARD
        else:
            self._ai_play_defense()

    def _ai_play_defense(self):
        idx = ai_choose_card(self.pos, self.defense, False,
                             difficulty=self.difficulty,
                             opponent=self.offense,
                             opponent_card=self._off_card,
                             deck_remaining=list(self.deck),
                             rng=self._rng)
        self._def_card = self.defense.play(idx)
        self._log(f"{self.defense.name} defends with {self._def_card.display}")
        self._emit(
            CardPlayedEvent(
                self._seat(self.defense),
                "defense",
                self._def_card,
                len(self.defense.hand),
            )
        )
        self._resolve_cards()

    def _resolve_cards(self):
        self._message = f"OFF: {self._off_card.display}  vs  DEF: {self._def_card.display}"
        self._log(self._message)
        off_val = card_value(self._off_card)
        def_val = card_value(self._def_card)
        winner = "tie"
        if off_val > def_val:
            winner = "offense"
        elif def_val > off_val:
            winner = "defense"
        self._emit(
            CardsRevealedEvent(
                self._off_card,
                self._def_card,
                off_val,
                def_val,
                winner,
            )
        )
        self.phase = GamePhase.SHOWING_CARD_BATTLE
        self._timer = 0

    def _resolve_play(self):
        off_val = card_value(self._off_card)
        def_val = card_value(self._def_card)

        # WAR
        if off_val == def_val:
            self._handle_war()
            return

        # JOKER
        if self._off_card.value == "Joker" or self._def_card.value == "Joker":
            self._handle_joker()
            return

        # MOJO for defense (defense won the card battle)
        if def_val > off_val:
            if self.defense.mojo < 2:
                old_mojo = self.defense.mojo
                self.defense.mojo += 1
                self._log(f"MOJO! {self.defense.name} won card battle ({self.defense.mojo}/2)")
                self._emit(
                    MojoChangedEvent(
                        self._seat(self.defense),
                        old_mojo,
                        self.defense.mojo,
                        "won_card_battle",
                    )
                )

        # MOJO for offense (dominating win by 4+)
        if off_val >= def_val + 4:
            if self.offense.mojo < 2:
                old_mojo = self.offense.mojo
                self.offense.mojo += 1
                self._log(f"MOJO! {self.offense.name} dominated by {off_val - def_val} ({self.offense.mojo}/2)")
                self._emit(
                    MojoChangedEvent(
                        self._seat(self.offense),
                        old_mojo,
                        self.offense.mojo,
                        "dominant_win",
                    )
                )

        # convert  2 mojo to clutch if clutch lo
        if ( self.offense.clutch == 0) and (self.offense.mojo == 2):
            self.offense.mojo = 0
            self.offense.clutch += 1
            self._log(f"MOJO CONVERTED to CLUTCH! {self.offense.name}")
            self._emit(
                MojoConvertedToClutchEvent(
                    self._seat(self.offense),
                    self.offense.clutch,
                    "pre_play",
                )
            )

        # DRIVE — get movement
        self._movement = get_card_result(
            self.offense.color.value, self.offense.rating, str(self._off_card)
        )
        old_pos = self.pos
        self._new_pos, self._is_td, self._is_safety = move(self.pos, self._movement)
        self.offense.segments += self._movement
        self._emit_ball_moved(
            self.offense,
            old_pos,
            self._new_pos,
            self._movement,
            "drive_chart",
            is_touchdown=self._is_td,
            is_safety=self._is_safety,
        )

        move_msg = f"Moved from {old_pos} -> {self._new_pos} (+{self._movement} segments)"
        if self._is_td:
            move_msg = f"Moved {old_pos} -> END ZONE (+{self._movement}) TOUCHDOWN!"
        elif self._is_safety:
            move_msg = f"Moved {old_pos} -> SAFETY! (+{self._movement})"
        self._log(move_msg)
        self._message = move_msg

        if not self._is_td and not self._is_safety:
            self.pos = self._new_pos

        self.phase = GamePhase.SHOWING_MOVEMENT
        self._timer = 0

    def _handle_war(self):
        self._war_card = self.deck.popleft() if self.deck else Card("2", "S")
        color_name = self._war_card.color.value if self._war_card.color else "Joker"
        self._log(f"WAR! Drew {self._war_card.display} ({color_name})")
        tied_value = card_value(self._off_card)
        matches = self._war_card.color == self.offense.color
        self._emit(WarStartedEvent(tied_value))
        self._emit(
            WarCardRevealedEvent(
                self._war_card,
                matches,
                "advance" if matches else "turnover",
            )
        )

        if matches:
            self._message = f"WAR! {self._war_card.display} - Offense to Z3!"
            self._log("Offense advances to Z3")
        else:
            self._message = f"WAR! {self._war_card.display} - TURNOVER!"
            self._log("Turnover! Defense ball at 3")

        self.phase = GamePhase.SHOWING_WAR
        self._timer = 0

    def _handle_joker(self):
        off_val = card_value(self._off_card)
        def_val = card_value(self._def_card)

        if def_val == 15:  # defense played joker
            if off_val < 4:
                self._message = "JOKER DEFENSE - DEFENSIVE TOUCHDOWN!"
                self._log("Defense Joker! Automatic defensive TD!")
                scorer = self.defense
                outcome = "touchdown"
                self._pending_action = lambda s=scorer: self._score_touchdown(
                    scorer=s, cause="defensive_joker"
                )
            elif off_val < 11:
                self._message = "JOKER DEFENSE - Defense ball at Z3!"
                self._log("Defense Joker! Turnover to Z3")
                outcome = "turnover_z3"
                self._pending_action = lambda: self._joker_turnover("Z3")
            else:
                self._message = "JOKER DEFENSE - No gain"
                self._log("Defense Joker! Offense stopped, no gain")
                outcome = "no_gain"
                self._pending_action = lambda: self._enter_post_move()
            played_by = "defense"
            opposing_value = off_val
        else:  # offense played joker
            if def_val < 4:
                self._message = "JOKER OFFENSE - TOUCHDOWN!"
                self._log("Offense Joker! Automatic TD!")
                outcome = "touchdown"
                self._pending_action = lambda: self._score_touchdown(cause="joker")
            elif def_val < 11:
                self._message = "JOKER OFFENSE - +3 segments!"
                self._log("Offense Joker! +3 segments")
                outcome = "advance_3"
                self._pending_action = lambda: self._joker_move(3)
            else:
                self._message = "JOKER OFFENSE - +1 segment"
                self._log("Offense Joker! +1 segment")
                outcome = "advance_1"
                self._pending_action = lambda: self._joker_move(1)
            played_by = "offense"
            opposing_value = def_val

        self._emit(JokerResolvedEvent(played_by, opposing_value, outcome))

        self.phase = GamePhase.SHOWING_JOKER
        self._timer = 0

    def _joker_turnover(self, target="3"):
        old_pos = self.pos
        self.pos = target
        movement = SEGMENTS.index(self.pos) - SEGMENTS.index(old_pos)
        self._emit_ball_moved(
            self.offense, old_pos, self.pos, movement, "turnover"
        )
        self._swap_sides(reason="joker_turnover")
        self._next_turn_or_end()

    def _joker_move(self, movement):
        new_pos, td, safety = move(self.pos, movement)
        self._movement = movement
        self._new_pos = new_pos
        self._is_td = td
        self._is_safety = safety
        self.offense.segments += movement
        self._log(f"Joker move {movement} -> {new_pos}")
        self._emit_ball_moved(
            self.offense,
            self.pos,
            new_pos,
            movement,
            "joker",
            is_touchdown=td,
            is_safety=safety,
        )

        if td:
            self._score_touchdown(cause="joker")
        else:
            self.pos = new_pos
            self._enter_post_move()

    def _score_touchdown(self, scorer=None, cause="drive"):
        scorer = scorer or self.offense
        self._scorer = scorer
        scorer.score += 6
        self._is_td = True
        self._message = f"TOUCHDOWN! {scorer.name} +6"
        self._log(f"TOUCHDOWN! {scorer.name} +6")
        self._emit(
            TouchdownScoredEvent(
                self._seat(scorer),
                6,
                scorer.score,
                cause,
            )
        )
        self.phase = GamePhase.SHOWING_TOUCHDOWN
        self._timer = 0

    def _score_safety(self):
        self.defense.score += 2
        self._message = f"SAFETY! {self.defense.name} +2"
        self._log(f"SAFETY! {self.defense.name} +2")
        self.pos = "3"
        self._emit(
            SafetyScoredEvent(
                self._seat(self.defense),
                2,
                self.defense.score,
            )
        )
        self.phase = GamePhase.SHOWING_SAFETY
        self._timer = 0

    # def _do_extra_points(self):
    #     pts, desc = extra_points()
    #     self._extra_pts = pts
    #     self._extra_pts_desc = desc
    #     self.offense.score += pts
    #     self._message = desc
    #     self._log(f"Extra points: {desc} (+{pts})")
    #     self.phase = GamePhase.SHOWING_EXTRA_POINTS
    #     self._timer = 0

    def _enter_post_move(self):
        if self.offense == self.human and not self.ai_vs_ai:
            self.phase = GamePhase.WAITING_POST_MOVE
        else:
            self.phase = GamePhase.AI_POST_MOVE
            self._timer = 0

    def _execute_post_move(self, choice: str):
        if choice == "P":
            self._do_punt()
        elif choice == "S":
            self._do_short_punt()
        elif choice == "F":
            self._do_field_goal()
        elif choice == "C":
            self.offense.clutch_used = True
            self._do_clutch()

    def _do_punt(self):
        dist, roll = punt_distance(self.offense.kick_rating, rng=self._rng)
        self._punt_dist = dist
        self._punt_roll = roll
        self._message = f"PUNT! Roll {roll} + Kick {self.offense.kick_rating} = {dist}"
        self._log(self._message)
        self.offense.punts += 1
        # Punt moves ball backwards for the offense (towards their own side)
        # Use negative movement to go backwards
        old_pos = self.pos
        idx = SEGMENTS.index(self.pos)
        new_idx = max(1, idx - dist)
        self.pos = SEGMENTS[new_idx]
        actual_movement = new_idx - idx
        self._emit(
            PuntResolvedEvent(
                self._seat(self.offense),
                "punt",
                dist,
                roll,
                old_pos,
                self.pos,
                abs(actual_movement) < dist,
            )
        )
        self._emit_ball_moved(
            self.offense, old_pos, self.pos, actual_movement, "punt"
        )
        self.phase = GamePhase.SHOWING_PUNT
        self._timer = 0

    def _do_short_punt(self):
        dist = short_punt_distance(self.offense.kick_rating, rng=self._rng)
        self._punt_dist = dist
        self._message = f"SHORT PUNT! Distance: {dist}"
        self._log(self._message)
        self.offense.punts += 1
        old_pos = self.pos
        idx = SEGMENTS.index(self.pos)
        new_idx = max(1, idx - dist)
        self.pos = SEGMENTS[new_idx]
        actual_movement = new_idx - idx
        self._emit(
            PuntResolvedEvent(
                self._seat(self.offense),
                "short_punt",
                dist,
                None,
                old_pos,
                self.pos,
                abs(actual_movement) < dist,
            )
        )
        self._emit_ball_moved(
            self.offense, old_pos, self.pos, actual_movement, "short_punt"
        )
        self.phase = GamePhase.SHOWING_SHORT_PUNT
        self._timer = 0

    def _do_field_goal(self):
        old_pos = self.pos
        success, roll, total, target = field_goal_attempt(
            self.offense.kick_rating, self.pos, rng=self._rng
        )
        self._fg_success = success
        self._fg_roll = roll
        self._fg_total = total
        self._fg_target = target
        self.offense.fg_att += 1
        if success:
            self.offense.fg_made += 1
            self.offense.score += 3
            self._message = f"FG GOOD! d6:[{roll}] + Kick {self.offense.kick_rating} = {total} (need {target}) → +3"
            self._log(f"FIELD GOAL GOOD! +3 ({self.offense.name})")
        else:
            self._message = f"FG MISSED! d6:[{roll}] + Kick {self.offense.kick_rating} = {total} (need {target})"
            self._log(f"FG missed! {total} < {target}")
        self._emit(
            FieldGoalResolvedEvent(
                self._seat(self.offense),
                success,
                roll,
                total,
                target,
                old_pos,
                3 if success else 0,
                self.offense.score,
            )
        )
        self.phase = GamePhase.SHOWING_FIELD_GOAL
        self._timer = 0

    def _do_clutch(self):
        self.offense.clutch -= 1
        if ( self.offense.mojo == 2 ) and (self.offense.clutch < 2) :
            self.offense.clutch += 1
            self.offense.mojo = 0
            self._log(f"2 Mojo and Clutch < 2 >> Award Clutch! ")
            self._emit(
                MojoConvertedToClutchEvent(
                    self._seat(self.offense),
                    self.offense.clutch,
                    "clutch_spend",
                )
            )
        self._clutch_card = self.deck.popleft() if self.deck else Card("A", "H")
        self._log(f"CLUTCH! Drew {self._clutch_card.display} (remaining: {self.offense.clutch})")
        self._message = f"CLUTCH! Drew {self._clutch_card.display}"
        self._emit(
            ClutchUsedEvent(
                self._seat(self.offense),
                self.offense.clutch,
                self._clutch_card,
            )
        )

        if card_value(self._clutch_card) == 15:  # Joker
            self._pending_action = lambda: self._score_touchdown(cause="clutch")
        else:
            movement = get_card_result(
                self.offense.color.value, self.offense.rating, str(self._clutch_card)
            )

            def clutch_resolve():
                new_pos, td, safety = move(self.pos, movement)
                self._movement = movement
                self._new_pos = new_pos
                self.offense.segments += movement
                self._log(f"Clutch move {movement} -> {new_pos}")
                self._emit_ball_moved(
                    self.offense,
                    self.pos,
                    new_pos,
                    movement,
                    "clutch",
                    is_touchdown=td,
                    is_safety=safety,
                )
                if td:
                    self._score_touchdown(cause="clutch")
                else:
                    self.pos = new_pos
                    self._enter_post_move()

            self._pending_action = clutch_resolve

        self.phase = GamePhase.SHOWING_CLUTCH
        self._timer = 0

    def _swap_sides(self, reason=None):
        previous_offense = self.offense
        self.offense, self.defense = self.defense, self.offense
        if reason is not None:
            self._emit(
                PossessionChangedEvent(
                    self._seat(previous_offense),
                    self._seat(self.offense),
                    self.pos,
                    reason,
                )
            )

    def _next_turn_or_end(self):
        if self.turn >= self.turns_in_quarter:
            self._end_quarter()
        else:
            self._start_turn()

    def _end_quarter(self):
        self._message = f"END OF QUARTER {self.quarter}"
        self._log(f"=== End Q{self.quarter} | "
                  f"{self.human.name}: {self.human.score} - "
                  f"{self.ai.name}: {self.ai.score} ===")
        self._emit(
            QuarterEndedEvent(
                self.quarter,
                self.human.score,
                self.ai.score,
            )
        )
        self.phase = GamePhase.QUARTER_END
        self._timer = 0

    def _game_over(self):
        if self.human.score > self.ai.score:
            result = f"{self.human.name} WINS!"
        elif self.ai.score > self.human.score:
            result = f"{self.ai.name} WINS!"
        else:
            result = "TIE GAME!"
        self._message = result
        self._log(f"FINAL: {self.human.name} {self.human.score} - {self.ai.name} {self.ai.score} | {result}")
        winner = None
        if self.human.score > self.ai.score:
            winner = "home"
        elif self.ai.score > self.human.score:
            winner = "away"
        self._emit(
            GameEndedEvent(
                winner,
                self.human.score,
                self.ai.score,
                winner is None,
            )
        )
        self.phase = GamePhase.GAME_OVER
