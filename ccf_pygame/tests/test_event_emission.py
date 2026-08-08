"""End-to-end checks for the engine's contract event stream."""

from ccf.ai import Difficulty
from ccf.events import ALL_EVENT_TYPES
from ccf.models import Color
from ccf.state_machine import GameStateMachine
from ccf.states import GamePhase


def play_seeded_game():
    game = GameStateMachine(seed=42)
    game.provide_setup(
        "Home",
        2,
        2,
        Color.RED,
        1,
        "Away",
        2,
        2,
        1,
        difficulty=Difficulty.MEDIUM,
        ai_vs_ai=True,
    )
    return game, game.pump()


def test_seeded_game_emits_every_contract_event_type():
    _, events = play_seeded_game()

    assert {event.type for event in events} == set(ALL_EVENT_TYPES)


def test_full_game_reports_contract_deal_sizes_for_all_four_quarters():
    _, events = play_seeded_game()

    quarters = [
        (event.quarter, event.dealt)
        for event in events
        if event.type == "quarter_started"
    ]
    assert quarters == [(1, 7), (2, 6), (3, 7), (4, 8)]


def test_card_event_order_is_play_play_reveal():
    _, events = play_seeded_game()

    for index, event in enumerate(events):
        if event.type == "cards_revealed":
            assert [item.type for item in events[index - 2:index]] == [
                "card_played",
                "card_played",
            ]


def test_events_reconstruct_final_presentation_state():
    game, events = play_seeded_game()
    state = {
        "score": {"home": 0, "away": 0},
        "ball": "1",
        "offense": None,
        "mojo": {"home": 0, "away": 0},
        "clutch": {"home": 1, "away": 1},
        "clutch_used": {"home": False, "away": False},
        "hand_count": {"home": 0, "away": 0},
        "phase": GamePhase.SETUP_TEAMS,
        "result": None,
    }

    for event in events:
        payload = event.to_dict(0)
        event_type = event.type
        if event_type == "quarter_started":
            for seat in ("home", "away"):
                if payload["quarter"] in (1, 3):
                    state["hand_count"][seat] = payload["dealt"]
                else:
                    state["hand_count"][seat] += payload["dealt"]
            state["ball"] = payload["ball"]
            state["offense"] = payload["offense_seat"]
        elif event_type == "card_played":
            seat = payload["seat"]
            state["hand_count"][seat] = payload["hand_count_after"]
            if payload["role"] == "offense":
                state["clutch_used"][seat] = False
        elif event_type == "ball_moved":
            state["ball"] = payload["to"]
        elif event_type == "mojo_changed":
            state["mojo"][payload["seat"]] = payload["to"]
        elif event_type == "mojo_converted_to_clutch":
            seat = payload["seat"]
            state["mojo"][seat] = 0
            state["clutch"][seat] = payload["clutch_after"]
        elif event_type == "clutch_used":
            seat = payload["seat"]
            state["clutch"][seat] = payload["clutch_after"]
            state["clutch_used"][seat] = True
        elif event_type == "possession_changed":
            state["offense"] = payload["to_seat"]
            state["ball"] = payload["ball"]
        elif event_type in {
            "field_goal_resolved",
            "touchdown_scored",
            "safety_scored",
            "extra_point_resolved",
        }:
            state["score"][payload["seat"]] = payload["score_after"]
        elif event_type == "game_ended":
            state["phase"] = GamePhase.GAME_OVER
            state["result"] = {
                "winner": payload["winner"],
                "home_score": payload["home_score"],
                "away_score": payload["away_score"],
                "is_tie": payload["is_tie"],
            }

    assert state["score"] == {
        "home": game.human.score,
        "away": game.ai.score,
    }
    assert state["ball"] == game.pos
    assert state["offense"] == game._seat(game.offense)
    assert state["mojo"] == {
        "home": game.human.mojo,
        "away": game.ai.mojo,
    }
    assert state["clutch"] == {
        "home": game.human.clutch,
        "away": game.ai.clutch,
    }
    assert state["clutch_used"] == {
        "home": game.human.clutch_used,
        "away": game.ai.clutch_used,
    }
    assert state["hand_count"] == {
        "home": len(game.human.hand),
        "away": len(game.ai.hand),
    }
    assert state["phase"] == game.phase
    winner = None
    if game.human.score > game.ai.score:
        winner = "home"
    elif game.ai.score > game.human.score:
        winner = "away"
    assert state["result"] == {
        "winner": winner,
        "home_score": game.human.score,
        "away_score": game.ai.score,
        "is_tie": game.human.score == game.ai.score,
    }
