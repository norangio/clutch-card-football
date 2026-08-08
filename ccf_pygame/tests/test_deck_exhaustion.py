"""Audit the half-deck consumption bound under legal play."""

from ccf.ai import Difficulty
from ccf.events import ClutchUsedEvent, WarStartedEvent
from ccf.models import Card, Color
from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase

_ORIGINAL_START_QUARTER = GameStateMachine._start_quarter


def _matching_suit(color: Color) -> str:
    return "H" if color == Color.RED else "S"


def _run_structural_maximum(monkeypatch, clutch_half):
    """Force every structurally available war and spend clutch in one half.

    With N non-war plays, at most floor(N / 2) extra clutch tokens can be
    earned from mojo, while those N plays remove N possible war draws. Thus
    all-war play plus the six setup tokens is the maximum draw pattern.
    """
    half_remaining = {}

    def track_half_boundary(machine):
        if machine.quarter == 3:
            half_remaining[1] = len(machine.deck)
        _ORIGINAL_START_QUARTER(machine)

    monkeypatch.setattr(GameStateMachine, "_start_quarter", track_half_boundary)
    game = GameStateMachine(seed=42)

    def post_move_choice(*_args, **_kwargs):
        team = game.offense
        in_selected_half = (game.quarter <= 2) == (clutch_half == 1)
        if in_selected_half and team.clutch > 0 and not team.clutch_used:
            return "C"
        return "P"

    monkeypatch.setattr("ccf.state_machine.ai_post_move", post_move_choice)
    game.provide_setup(
        "Home",
        6,
        2,
        Color.RED,
        3,
        "Away",
        6,
        2,
        3,
        difficulty=Difficulty.EASY,
    )

    events = []
    while game.phase != GamePhase.GAME_OVER:
        events.extend(game.pump())

        if game.phase == GamePhase.WAITING_OFFENSE_CARD:
            # The engine immediately lets the AI defend. Make every card in
            # both hands tie without changing hand or deck sizes.
            for team in (game.offense, game.defense):
                for index in range(len(team.hand)):
                    team.hand[index] = Card("2", _matching_suit(team.color))
            game.provide_card(0)
        elif game.phase == GamePhase.WAITING_DEFENSE_CARD:
            # AI offense has already selected; match its exact value.
            game.defense.hand[0] = Card(
                game._off_card.value,
                None if game._off_card.value == "Joker" else "H",
            )
            game.provide_card(0)
        elif game.phase == GamePhase.WAITING_POST_MOVE:
            in_selected_half = (game.quarter <= 2) == (clutch_half == 1)
            choice = (
                "C"
                if in_selected_half
                and game.offense.clutch > 0
                and not game.offense.clutch_used
                else "P"
            )
            game.provide_post_move(choice)
        elif game.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
            game.provide_extra_point_choice("K")

        if game.phase == GamePhase.SHOWING_CARD_BATTLE:
            assert game.deck, "the supposedly unreachable fallback was reached"
            # Guarantee that each war advances and reaches the post-move menu.
            game.deck[0] = Card("2", _matching_suit(game.offense.color))

    events.extend(game.drain_events())
    return game, events, half_remaining[1]


def test_structural_maximum_draw_pattern_never_reaches_empty_deck(monkeypatch):
    """An over-approximation of real play leaves the fixed fallbacks unused."""
    first_game, first_events, first_half_remaining = _run_structural_maximum(
        monkeypatch, clutch_half=1
    )
    second_game, second_events, preserved_half_remaining = (
        _run_structural_maximum(monkeypatch, clutch_half=2)
    )

    assert first_half_remaining == 11
    assert len(first_game.deck) == 11
    assert preserved_half_remaining == 17
    assert len(second_game.deck) == 5
    for events in (first_events, second_events):
        assert sum(isinstance(event, WarStartedEvent) for event in events) == 26
        assert sum(isinstance(event, ClutchUsedEvent) for event in events) == 6
