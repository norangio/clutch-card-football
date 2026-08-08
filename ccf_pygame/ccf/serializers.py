"""Viewer-scoped JSON serializers for the web contract.

Internal snapshots deliberately contain both teams and all transient cards.
Nothing in this module serializes an internal dataclass wholesale; every public
field is constructed explicitly so hidden state cannot ride along by accident.
"""

from __future__ import annotations

from typing import Any

from .models import Card, Team
from .states import GamePhase

SEATS = {"home", "away"}

REQUIRED_ACTIONS = {
    GamePhase.WAITING_OFFENSE_CARD: "play_card",
    GamePhase.WAITING_DEFENSE_CARD: "play_card",
    GamePhase.WAITING_POST_MOVE: "post_move",
    GamePhase.WAITING_EXTRA_POINT_CHOICE: "extra_point",
    GamePhase.GAME_OVER: "none",
}

# Once the card battle begins, both played cards are public for the rest of the
# play. QUARTER_START and the card-selection phases intentionally are absent so
# stale internal card references cannot leak into a new play.
PLAY_CARDS_REVEALED_PHASES = {
    GamePhase.SHOWING_CARD_BATTLE,
    GamePhase.SHOWING_MOVEMENT,
    GamePhase.SHOWING_TOUCHDOWN,
    GamePhase.SHOWING_SAFETY,
    GamePhase.WAITING_EXTRA_POINT_CHOICE,
    GamePhase.SHOWING_EXTRA_POINTS,
    GamePhase.SHOWING_WAR,
    GamePhase.SHOWING_JOKER,
    GamePhase.WAITING_POST_MOVE,
    GamePhase.AI_POST_MOVE,
    GamePhase.SHOWING_PUNT,
    GamePhase.SHOWING_FIELD_GOAL,
    GamePhase.SHOWING_CLUTCH,
    GamePhase.SHOWING_SHORT_PUNT,
    GamePhase.WAITING_CONFIRM,
    GamePhase.QUARTER_END,
    GamePhase.GAME_OVER,
}

WAR_CARD_REVEALED_PHASES = {
    GamePhase.SHOWING_WAR,
    GamePhase.WAITING_POST_MOVE,
    GamePhase.AI_POST_MOVE,
    GamePhase.SHOWING_PUNT,
    GamePhase.SHOWING_FIELD_GOAL,
    GamePhase.SHOWING_CLUTCH,
    GamePhase.SHOWING_SHORT_PUNT,
    GamePhase.QUARTER_END,
    GamePhase.GAME_OVER,
}

CLUTCH_CARD_REVEALED_PHASES = {
    GamePhase.SHOWING_CLUTCH,
    GamePhase.WAITING_POST_MOVE,
    GamePhase.AI_POST_MOVE,
    GamePhase.SHOWING_TOUCHDOWN,
    GamePhase.WAITING_EXTRA_POINT_CHOICE,
    GamePhase.SHOWING_EXTRA_POINTS,
    GamePhase.SHOWING_PUNT,
    GamePhase.SHOWING_FIELD_GOAL,
    GamePhase.SHOWING_SHORT_PUNT,
    GamePhase.QUARTER_END,
    GamePhase.GAME_OVER,
}


def serialize_card(card: Card | None) -> dict[str, Any] | None:
    if card is None:
        return None
    return {
        "id": str(card),
        "value": card.value,
        "suit": card.suit,
        "color": card.color.value if card.color else None,
        "display": card.display,
    }


def _validate_viewer(viewer_seat: str) -> None:
    if viewer_seat not in SEATS:
        raise ValueError(f"unknown viewer seat: {viewer_seat!r}")


def seat_for_team(game, team: Team | None) -> str | None:
    if team is None:
        return None
    if team is game.human:
        return "home"
    if team is game.ai:
        return "away"
    raise ValueError("team does not belong to this game")


def serialize_seat(game, seat: str, viewer_seat: str) -> dict[str, Any]:
    _validate_viewer(viewer_seat)
    if seat not in SEATS:
        raise ValueError(f"unknown seat: {seat!r}")

    team = game.human if seat == "home" else game.ai
    if team is None:
        raise ValueError("game setup is incomplete")

    payload = {
        "seat": seat,
        "name": team.name,
        "color": team.color.value,
        "rating": team.rating,
        "kick_rating": team.kick_rating,
        "score": team.score,
        "mojo": team.mojo,
        "clutch": team.clutch,
        "clutch_used": team.clutch_used,
        "hand_count": len(team.hand),
        "segments": team.segments,
        "fg_made": team.fg_made,
        "fg_att": team.fg_att,
        "punts": team.punts,
    }
    if seat == viewer_seat:
        payload["hand"] = [serialize_card(card) for card in team.hand]
    return payload


def _played_card(
    game,
    card: Card | None,
    card_seat: str | None,
    viewer_seat: str,
) -> dict[str, Any] | None:
    if card is None or card_seat is None:
        return None

    # WAITING_DEFENSE_CARD is the only decision phase with a played but
    # unrevealed opponent card. The player who owns it may see it; the opponent
    # may not. Earlier phases are treated as a new play and reveal nothing.
    if game.phase == GamePhase.WAITING_DEFENSE_CARD:
        return serialize_card(card) if card_seat == viewer_seat else None
    if game.phase in PLAY_CARDS_REVEALED_PHASES:
        return serialize_card(card)
    return None


def serialize_play_cards(game, viewer_seat: str) -> dict[str, Any]:
    """Serialize transient cards with phase- and viewer-aware visibility."""
    _validate_viewer(viewer_seat)
    offense_seat = seat_for_team(game, game.offense)
    defense_seat = seat_for_team(game, game.defense)
    return {
        "offense": _played_card(
            game, game._off_card, offense_seat, viewer_seat
        ),
        "defense": _played_card(
            game, game._def_card, defense_seat, viewer_seat
        ),
        "war": (
            serialize_card(game._war_card)
            if game.phase in WAR_CARD_REVEALED_PHASES
            else None
        ),
        "clutch": (
            serialize_card(game._clutch_card)
            if game.phase in CLUTCH_CARD_REVEALED_PHASES
            else None
        ),
    }


def _acting_seat(game) -> str | None:
    if game.phase in (
        GamePhase.WAITING_OFFENSE_CARD,
        GamePhase.WAITING_POST_MOVE,
    ):
        return seat_for_team(game, game.offense)
    if game.phase == GamePhase.WAITING_DEFENSE_CARD:
        return seat_for_team(game, game.defense)
    if game.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        return seat_for_team(game, game._scorer or game.offense)
    return None


def _action(
    action_type: str,
    *,
    choice: str | None = None,
    card_index: int | None = None,
    enabled: bool = True,
    disabled_reason: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": action_type}
    if choice is not None:
        payload["choice"] = choice
    if card_index is not None:
        payload["card_index"] = card_index
    payload["enabled"] = enabled
    if not enabled and disabled_reason is not None:
        payload["disabled_reason"] = disabled_reason
    return payload


def serialize_legal_actions(game, viewer_seat: str) -> list[dict[str, Any]]:
    _validate_viewer(viewer_seat)
    if _acting_seat(game) != viewer_seat:
        return []

    if game.phase in (
        GamePhase.WAITING_OFFENSE_CARD,
        GamePhase.WAITING_DEFENSE_CARD,
    ):
        team = game.offense if game.phase == GamePhase.WAITING_OFFENSE_CARD \
            else game.defense
        return [
            _action("play_card", card_index=index)
            for index in range(len(team.hand))
        ]

    if game.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        return [
            _action("extra_point", choice="K"),
            _action("extra_point", choice="2"),
        ]

    if game.phase != GamePhase.WAITING_POST_MOVE:
        return []

    in_range = game.pos in ("Z1", "Z2", "Z3")
    offense = game.offense
    if offense.clutch <= 0:
        clutch_enabled = False
        clutch_reason = "no_clutch_remaining"
    elif offense.clutch_used:
        clutch_enabled = False
        clutch_reason = "clutch_already_used_this_play"
    else:
        clutch_enabled = True
        clutch_reason = None

    return [
        _action("post_move", choice="P"),
        _action(
            "post_move",
            choice="F",
            enabled=in_range,
            disabled_reason=None if in_range else "not_in_field_goal_range",
        ),
        _action(
            "post_move",
            choice="C",
            enabled=clutch_enabled,
            disabled_reason=clutch_reason,
        ),
        _action(
            "post_move",
            choice="S",
            enabled=in_range,
            disabled_reason=None if in_range else "not_in_field_goal_range",
        ),
    ]


def _serialize_result(game) -> dict[str, Any] | None:
    if game.phase != GamePhase.GAME_OVER:
        return None
    home_score = game.human.score
    away_score = game.ai.score
    is_tie = home_score == away_score
    if is_tie:
        winner = None
    else:
        winner = "home" if home_score > away_score else "away"
    return {
        "winner": winner,
        "home_score": home_score,
        "away_score": away_score,
        "is_tie": is_tie,
    }


def serialize_snapshot(
    game,
    viewer_seat: str,
    *,
    game_id: str,
    revision: int,
) -> dict[str, Any]:
    """Return a contract-v1 snapshot safe for ``viewer_seat``.

    The API must pump through transient presentation phases before calling this
    function. Rejecting them here prevents a server bug from emitting a phase
    the TypeScript client cannot represent.
    """
    _validate_viewer(viewer_seat)
    if game.phase not in REQUIRED_ACTIONS:
        raise ValueError(f"cannot serialize transient phase: {game.phase.name}")
    if game.human is None or game.ai is None:
        raise ValueError("game setup is incomplete")

    result = _serialize_result(game)
    offense_seat = seat_for_team(game, game.offense)
    defense_seat = seat_for_team(game, game.defense)
    payload = {
        "game_id": game_id,
        "revision": revision,
        "phase": game.phase.name,
        "required_action": REQUIRED_ACTIONS[game.phase],
        "acting_seat": _acting_seat(game),
        "viewer_seat": viewer_seat,
        "quarter": game.quarter,
        "play": game.turn,
        "plays_in_quarter": game.turns_in_quarter,
        "ball": game.pos,
        "offense_seat": offense_seat,
        "defense_seat": defense_seat,
        "home": serialize_seat(game, "home", viewer_seat),
        "away": serialize_seat(game, "away", viewer_seat),
        "play_cards": serialize_play_cards(game, viewer_seat),
        "legal_actions": serialize_legal_actions(game, viewer_seat),
        "log": list(game.log[-20:]),
        "message": game._message,
        "result": result,
    }
    if result is not None and game.seed is not None:
        payload["seed"] = game.seed
    return payload
