"""AI card selection and decision logic."""

from .models import Team
from .deck import card_value


def choose_card(pos: str, team: Team, is_offense: bool) -> int:
    """Return the index of the card the AI should play."""
    # defense returns MAX
    if not is_offense:
        return max(range(len(team.hand)), key=lambda i: card_value(team.hand[i]))
    # offense max-1 if not in red zone
    else:
        if pos in ("Z1", "Z2", "Z3"):
            return min(range(len(team.hand)), key=lambda i: card_value(team.hand[i]))
        else:
            return max(range(len(team.hand)), key=lambda i: card_value(team.hand[i]))

def post_move_choice(pos: str, clutch: int, clutch_used: bool) -> str:
    """AI chooses post-move action. Returns 'P', 'F', 'C', or 'S'."""

    # use clutch if greater than 1 OR in red zone
    if clutch > 1 and not clutch_used:
        return "C"
    else:
        if pos in ("Z1", "Z2", "Z3") and not clutch_used:
            if clutch > 0:
                return "C"
            else:
                return "F"
        else:
            return "P"
        
