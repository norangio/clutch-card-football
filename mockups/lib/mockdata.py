"""Representative GameSnapshots for the UI mockups.

These build genuine ``GameSnapshot`` / ``Team`` / ``Card`` objects from the real
game package, so every mockup reads exactly the same data the live UI reads.
Nothing here touches the state machine or alters any rule.
"""

import os
import sys

_PKG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "clutch-card-football", "ccf_pygame",
)
if not os.path.isdir(_PKG):
    _PKG = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "ccf_pygame",
    )
sys.path.insert(0, _PKG)

from ccf.models import Card, Color, Team          # noqa: E402
from ccf.states import GamePhase, GameSnapshot    # noqa: E402


def _teams():
    home = Team("BULLDOGS", rating=8, kick_rating=2, color=Color.RED, clutch=2)
    away = Team("RIVALS", rating=7, kick_rating=3, color=Color.BLACK, clutch=1)
    home.score, away.score = 17, 14
    home.mojo, away.mojo = 1, 2
    home.fg_made, home.fg_att, home.punts = 1, 2, 3
    away.fg_made, away.fg_att, away.punts = 2, 2, 4
    home.hand = [
        Card("7", "H"), Card("K", "S"), Card("4", "D"), Card("A", "H"),
        Card("Joker"), Card("9", "C"), Card("Q", "D"),
    ]
    away.hand = [Card("3", "S"), Card("J", "H"), Card("8", "C"),
                 Card("2", "D"), Card("10", "S"), Card("5", "C")]
    return home, away


LOG = [
    "=== QUARTER 3 === RIVALS has ball",
    "-- Play 3/6 | OFF: BULLDOGS | Ball: 2",
    "BULLDOGS plays 7H",
    "RIVALS defends with 3S",
    "MOJO! BULLDOGS dominated by 4 (1/2)",
    "Moved from 1 -> 2 (+1 segments)",
    "-- Play 4/6 | OFF: BULLDOGS | Ball: 2",
    "BULLDOGS plays KS",
    "RIVALS defends with 8C",
    "Moved from 2 -> Z3 (+2 segments)",
    "CLUTCH! Drew AH (remaining: 2)",
    "Clutch move 4 -> Z2",
]


def _base(phase, **kw):
    home, away = _teams()
    snap = GameSnapshot(
        phase=phase,
        quarter=3,
        turn=4,
        turns_in_quarter=6,
        difficulty="hard",
        human=home,
        ai=away,
        offense=home,
        defense=away,
        log_messages=list(LOG),
    )
    for k, v in kw.items():
        setattr(snap, k, v)
    return snap


def select_card():
    """Human on offense, choosing a card from hand."""
    return _base(
        GamePhase.WAITING_OFFENSE_CARD,
        ball_pos="2",
        message="Pick your OFFENSE card",
        can_clutch=True, can_fg=False, can_punt=True, can_short_punt=False,
    )


def red_zone_decision():
    """Post-move decision in the red zone — every action button live."""
    snap = _base(
        GamePhase.WAITING_POST_MOVE,
        ball_pos="Z2",
        off_card=Card("K", "S"),
        def_card=Card("8", "C"),
        movement=2,
        new_pos="Z2",
        message="Ball at Z2",
        can_clutch=True, can_fg=True, can_punt=True, can_short_punt=True,
    )
    snap.human.hand = snap.human.hand[:5]
    return snap


def touchdown():
    """Touchdown scored, waiting on the extra-point choice."""
    snap = _base(
        GamePhase.WAITING_EXTRA_POINT_CHOICE,
        ball_pos="Z1",
        off_card=Card("A", "H"),
        def_card=Card("5", "C"),
        movement=4,
        is_td=True,
        message="TOUCHDOWN! BULLDOGS +6",
    )
    snap.human.score = 23
    snap.human.hand = snap.human.hand[:4]
    snap.log_messages = LOG + ["TOUCHDOWN! BULLDOGS +6"]
    return snap


def full_hand_defense():
    """Q4 worst case: 8 dealt on top of a leftover = 9 cards, human defending.

    This is the layout stress test — every hand rail has to survive it.
    """
    snap = _base(
        GamePhase.WAITING_DEFENSE_CARD,
        quarter=4,
        turn=1,
        turns_in_quarter=8,
        ball_pos="3",
        off_card=Card("J", "S"),
        message="Pick your DEFENSE card",
        can_clutch=False, can_fg=False, can_punt=True, can_short_punt=False,
    )
    snap.offense, snap.defense = snap.ai, snap.human
    snap.human.hand = [
        Card("2", "S"), Card("5", "H"), Card("6", "D"), Card("8", "S"),
        Card("10", "H"), Card("J", "C"), Card("Q", "S"), Card("K", "H"),
        Card("A", "D"),
    ]
    snap.ai.hand = snap.ai.hand[:4]
    snap.log_messages = LOG[-6:] + ["=== QUARTER 4 === RIVALS has ball",
                                    "-- Play 1/8 | OFF: RIVALS | Ball: 3",
                                    "AI plays card ..."]
    return snap


STATES = {
    "1-select": ("Choosing a card", select_card),
    "2-redzone": ("Red-zone decision", red_zone_decision),
    "3-touchdown": ("Touchdown / extra point", touchdown),
    "4-fullhand": ("Full 9-card hand, on defense", full_hand_defense),
}
