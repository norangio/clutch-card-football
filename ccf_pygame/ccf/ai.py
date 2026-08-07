"""AI card selection and decision logic with difficulty levels.

Difficulty levels:
  - EASY:   deliberately weak (random picks, wasteful decisions)
  - MEDIUM: solid heuristics using the drive chart
  - HARD:   Monte Carlo search over the remaining deck
"""

import random
from enum import Enum

from .models import Card, Team
from .deck import card_value
from .drive_chart import get_drive_result
from .field import SEGMENTS, move
from .rules import field_goal_attempt, punt_distance, short_punt_distance


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# --- Monte Carlo parameters ---
MC_EPISODES = 120
TD_VALUE = 12.0
SAFETY_VALUE = 6.0
MOJO_W = 0.4
PTS_W = 2.0
FIELD_W = 0.5

_VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
_SUITS = ["H", "D", "S", "C"]


def choose_card(pos: str, team: Team, is_offense: bool,
                difficulty: Difficulty = Difficulty.MEDIUM,
                opponent: Team = None, opponent_card: Card = None,
                deck_remaining: list = None) -> int:
    """Return the index of the card the AI should play."""
    if not team.hand:
        return 0

    if difficulty == Difficulty.EASY:
        return random.randrange(len(team.hand))

    if is_offense:
        if difficulty == Difficulty.HARD:
            return _mc_offense(pos, team, opponent, list(deck_remaining or []))
        return _medium_offense(pos, team)

    # defense
    if difficulty == Difficulty.HARD:
        return _mc_defense(pos, team, opponent, opponent_card, list(deck_remaining or []))
    return _medium_defense(team, opponent_card)


def post_move_choice(pos: str, clutch: int, clutch_used: bool,
                     difficulty: Difficulty = Difficulty.MEDIUM,
                     team: Team = None, opponent: Team = None,
                     deck_remaining: list = None) -> str:
    """AI chooses post-move action. Returns 'P', 'F', 'C', or 'S'."""
    if difficulty == Difficulty.EASY:
        if clutch > 0 and not clutch_used and random.random() < 0.4:
            return "C"
        if pos in ("Z1", "Z2", "Z3"):
            return random.choice(["P", "F"])
        return "P"

    if difficulty == Difficulty.HARD and team is not None:
        return _mc_post_move(pos, team, opponent, list(deck_remaining or []))

    # MEDIUM
    if clutch > 1 and not clutch_used:
        return "C"
    if pos in ("Z1", "Z2", "Z3") and not clutch_used:
        if clutch > 0:
            return "C"
        return "F"
    return "P"


def extra_point_choice(difficulty: Difficulty = Difficulty.MEDIUM,
                       score_diff: int = 0, quarter: int = 1) -> str:
    """AI chooses extra point: 'K' (kick PAT) or '2' (two-point attempt)."""
    if difficulty == Difficulty.EASY:
        return random.choice(["K", "2"])
    if difficulty == Difficulty.HARD and quarter == 4 and score_diff <= -8:
        return "2"
    return "K"


# --- Medium heuristics ---

def _card_move(card: Card, rating: int, color) -> int:
    if card.value == "Joker":
        return get_drive_result(color, rating, "A", "H")
    return get_drive_result(color, rating, card.value, card.suit)


def _medium_offense(pos: str, team: Team) -> int:
    hand = team.hand

    def move_score(card: Card) -> int:
        return _card_move(card, team.rating, team.color.value)

    if pos in ("Z1", "Z2", "Z3"):
        dist_to_td = len(SEGMENTS) - SEGMENTS.index(pos)
        scoring = [i for i, c in enumerate(hand) if move_score(c) >= dist_to_td]
        if scoring:
            return min(scoring, key=lambda i: card_value(hand[i]))
        return min(range(len(hand)), key=lambda i: card_value(hand[i]))
    return max(range(len(hand)), key=lambda i: (move_score(hand[i]), card_value(hand[i])))


def _medium_defense(team: Team, opponent_card: Card) -> int:
    if opponent_card is not None and card_value(opponent_card) < 11:
        for i, c in enumerate(team.hand):
            if c.value == "Joker":
                return i
    return max(range(len(team.hand)), key=lambda i: card_value(team.hand[i]))


# --- Monte Carlo helpers ---

def _full_pool():
    return [(v, s) for v in _VALUES for s in _SUITS] + [("Joker", None)] * 3


def _opponent_pool(ai_hand, deck_remaining):
    """Multiset of cards the opponent still holds (full deck minus AI hand and remaining deck)."""
    pool = _full_pool()
    for c in ai_hand:
        if (c.value, c.suit) in pool:
            pool.remove((c.value, c.suit))
    for c in deck_remaining:
        if (c.value, c.suit) in pool:
            pool.remove((c.value, c.suit))
    return pool


def _sample(cards):
    if not cards:
        return Card("2", "S")
    return random.choice(cards)


def _sample_card(pool) -> Card:
    v, s = _sample(pool)
    return Card(v, s)


def _pos_value(pos: str) -> int:
    try:
        return SEGMENTS.index(pos)
    except ValueError:
        return 0


def _simulate_play(off_card: Card, def_card: Card, pos: str,
                   off_team: Team, def_team: Team, deck_remaining: list) -> dict:
    """Resolve a single play (war card sampled from the deck). Returns outcome dict."""
    off_val = card_value(off_card)
    def_val = card_value(def_card)
    result = {"new_pos": pos, "td": False, "safety": False,
              "turnover": False, "def_td": False, "off_mojo": 0, "def_mojo": 0}

    if off_val == def_val:
        war = _sample(deck_remaining)
        if war.color == off_team.color:
            result["new_pos"] = "Z3"
        else:
            result["new_pos"] = "3"
            result["turnover"] = True
        return result

    if off_card.value == "Joker" or def_card.value == "Joker":
        if def_val == 15:
            if off_val < 4:
                result["def_td"] = True
            elif off_val < 11:
                result["new_pos"] = "Z3"
                result["turnover"] = True
            else:
                result["new_pos"] = pos
            return result
        if def_val < 4:
            result["td"] = True
        elif def_val < 11:
            result["new_pos"], result["td"], result["safety"] = move(pos, 3)
        else:
            result["new_pos"], result["td"], result["safety"] = move(pos, 1)
        return result

    if def_val > off_val and def_team.mojo < 2:
        result["def_mojo"] = 1
    if off_val >= def_val + 4 and off_team.mojo < 2:
        result["off_mojo"] = 1

    movement = get_drive_result(off_team.color.value, off_team.rating, off_card.value, off_card.suit)
    result["new_pos"], result["td"], result["safety"] = move(pos, movement)
    return result


def _outcome_value(out: dict, perspective: str) -> float:
    new_pos = out["new_pos"]
    if perspective == "offense":
        if out["td"]:
            value = TD_VALUE
        elif out["def_td"]:
            value = -TD_VALUE
        elif out["safety"]:
            value = -SAFETY_VALUE
        else:
            value = _pos_value(new_pos)
        if out["turnover"]:
            value = -_pos_value(new_pos)
        value += MOJO_W * out["off_mojo"] - MOJO_W * out["def_mojo"]
        return value

    if out["def_td"]:
        value = TD_VALUE
    elif out["td"]:
        value = -TD_VALUE
    elif out["safety"]:
        value = SAFETY_VALUE
    else:
        value = -_pos_value(new_pos)
    if out["turnover"]:
        value = _pos_value(new_pos)
    value += MOJO_W * out["def_mojo"] - MOJO_W * out["off_mojo"]
    return value


def _mc_offense(pos: str, team: Team, opponent: Team, deck_remaining: list) -> int:
    pool = _opponent_pool(team.hand, deck_remaining)
    scores = []
    for card in team.hand:
        total = 0.0
        for _ in range(MC_EPISODES):
            opp_card = _sample_card(pool)
            out = _simulate_play(card, opp_card, pos, team, opponent, deck_remaining)
            total += _outcome_value(out, "offense")
        scores.append(total / MC_EPISODES)
    return max(range(len(team.hand)), key=lambda i: (scores[i], card_value(team.hand[i])))


def _mc_defense(pos: str, team: Team, opponent: Team, opponent_card: Card,
                deck_remaining: list) -> int:
    off_card = opponent_card or Card("2", "S")
    scores = []
    for card in team.hand:
        total = 0.0
        for _ in range(MC_EPISODES):
            out = _simulate_play(off_card, card, pos, opponent, team, deck_remaining)
            total += _outcome_value(out, "defense")
        scores.append(total / MC_EPISODES)
    return max(range(len(team.hand)), key=lambda i: scores[i])


# --- Monte Carlo post-move ---

def _mc_post_move(pos: str, team: Team, opponent: Team, deck_remaining: list) -> str:
    in_zone = pos in ("Z1", "Z2", "Z3")
    actions = ["P"]
    scores = {"P": _mc_punt_value(pos, team)}
    if in_zone:
        actions += ["F", "S"]
        scores["F"] = _mc_fg_value(pos, team)
        scores["S"] = _mc_short_punt_value(pos, team)
    if team.clutch > 0 and not team.clutch_used:
        actions.append("C")
        scores["C"] = _mc_clutch_value(pos, team, deck_remaining)
    return max(actions, key=lambda a: scores[a])


def _mc_punt_value(pos: str, team: Team) -> float:
    total = 0.0
    for _ in range(MC_EPISODES):
        dist, _ = punt_distance(team.kick_rating)
        idx = max(1, SEGMENTS.index(pos) - dist)
        total += -_pos_value(SEGMENTS[idx]) * FIELD_W
    return total / MC_EPISODES


def _mc_short_punt_value(pos: str, team: Team) -> float:
    total = 0.0
    for _ in range(MC_EPISODES):
        dist = short_punt_distance(team.kick_rating)
        idx = max(1, SEGMENTS.index(pos) - dist)
        total += -_pos_value(SEGMENTS[idx]) * FIELD_W
    return total / MC_EPISODES


def _mc_fg_value(pos: str, team: Team) -> float:
    total = 0.0
    miss_map = {"Z3": "3", "Z2": "2", "Z1": "1"}
    for _ in range(MC_EPISODES):
        success, _roll, _total, _target = field_goal_attempt(team.kick_rating, pos)
        if success:
            total += 3 * PTS_W - _pos_value("1") * FIELD_W
        else:
            total += -_pos_value(miss_map[pos]) * FIELD_W
    return total / MC_EPISODES


def _mc_clutch_value(pos: str, team: Team, deck_remaining: list) -> float:
    total = 0.0
    for _ in range(MC_EPISODES):
        card = _sample(deck_remaining)
        if card_value(card) == 15:
            total += TD_VALUE
        else:
            movement = get_drive_result(team.color.value, team.rating, card.value, card.suit)
            new_pos, td, safety = move(pos, movement)
            if td:
                total += TD_VALUE
            else:
                total += _pos_value(new_pos) * FIELD_W
    return total / MC_EPISODES
