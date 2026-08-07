"""Option B — "Minimal".

A restrained, typography-led product UI. The field becomes an abstract
progress track instead of painted turf, and the drive chart is folded onto the
cards themselves — each card shows the yardage it would gain, so the lookup
table stops being a thing you read in parallel.
"""

import pygame

from lib import draw as d
from lib.mockdata import GamePhase
from ccf.drive_chart import get_drive_result

W, H = 960, 720

NAME = "Minimal"
BLURB = "Quiet product UI; abstract field track; drive chart folded onto each card."

# --- palette ---
BG = (9, 9, 11)
PANEL = (19, 19, 22)
PANEL_2 = (26, 26, 31)
BORDER = (38, 38, 45)
BORDER_HI = (60, 60, 70)
TEXT = (244, 244, 246)
MUTED = (150, 150, 162)
DIM = (104, 104, 118)
FAINT = (62, 62, 72)
ACCENT = (52, 211, 153)
AMBER = (251, 191, 36)
RED = (248, 113, 113)
SLATE = (148, 163, 184)

HEAD_H = 80
FIELD_Y, FIELD_H = 80, 92
CONT_Y = FIELD_Y + FIELD_H
HAND_Y, HAND_H = 544, 104
ACT_Y, ACT_H = HAND_Y + HAND_H, H - (HAND_Y + HAND_H)
CONT_H = HAND_Y - CONT_Y

PAD = 24
LEFT_W = 574
RIGHT_X = PAD + LEFT_W + 16
RIGHT_W = W - PAD - RIGHT_X

F_LABEL = d.font("inter", 9, "bold")


def team_color(team):
    return RED if team.color.value == "red" else SLATE


def label(surf, s, pos, color=DIM, anchor="topleft", size=9):
    return d.text(surf, s, pos, d.font("inter", size, "bold"), color,
                  anchor=anchor, tracking=2, tight=True)


def panel(surf, rect, radius=12, fill=PANEL, border=BORDER):
    d.rrect(surf, rect, fill, radius=radius)
    d.rrect(surf, rect, border, radius=radius, width=1)
    return pygame.Rect(rect)


def pips(surf, x, cy, count, cap, color, r=4, gap=11):
    for i in range(cap):
        pygame.draw.circle(surf, color if i < count else FAINT, (x + i * gap, cy), r)
    return x + cap * gap


def card_yardage(snap, card):
    """What this card is worth on the current drive chart."""
    if card.value == "Joker":
        return None
    off = snap.offense or snap.human
    return get_drive_result(off.color.value, off.rating, card.value, card.suit)


# --- header -----------------------------------------------------------------

def _header(surf, snap):
    pygame.draw.line(surf, BORDER, (0, HEAD_H - 1), (W, HEAD_H - 1))

    f_name = d.font("inter", 13, "semibold")
    f_score = d.font("inter", 32, "bold")
    cy = 40

    for side, team in (("L", snap.human), ("R", snap.ai)):
        on_off = snap.offense is team
        col = team_color(team)
        nm_w = d.text_size(team.name, f_name, 2, tight=True)[0]

        if side == "L":
            pygame.draw.circle(surf, col, (PAD + 4, cy), 4)
            nx = PAD + 18
            d.text(surf, team.name, (nx, cy), f_name, TEXT if on_off else MUTED,
                   anchor="midleft", tracking=2, tight=True)
            sx = nx + nm_w + 18
            d.text(surf, str(team.score), (sx, cy), f_score, TEXT,
                   anchor="midleft", tight=True)
            if on_off:
                pygame.draw.line(surf, ACCENT, (nx, cy + 20),
                                 (nx + nm_w, cy + 20), 2)
        else:
            pygame.draw.circle(surf, col, (W - PAD - 4, cy), 4)
            nx = W - PAD - 18
            d.text(surf, team.name, (nx, cy), f_name, TEXT if on_off else MUTED,
                   anchor="midright", tracking=2, tight=True)
            sx = nx - nm_w - 18
            d.text(surf, str(team.score), (sx, cy), f_score, TEXT,
                   anchor="midright", tight=True)
            if on_off:
                pygame.draw.line(surf, ACCENT, (nx - nm_w, cy + 20),
                                 (nx, cy + 20), 2)

    label(surf, f"QUARTER {snap.quarter}", (W // 2, cy - 9), MUTED, "center", 10)
    label(surf, f"PLAY {snap.turn} OF {snap.turns_in_quarter}  ·  AI {snap.difficulty.upper()}",
          (W // 2, cy + 11), DIM, "center", 9)


# --- field track ------------------------------------------------------------

LABELS = ["EZ", "1", "2", "3", "Z3", "Z2", "Z1", "EZ"]
ZONES = {"EZ": "END ZONE", "1": "OWN 1", "2": "OWN 2", "3": "OWN 3",
         "Z3": "RED ZONE", "Z2": "RED ZONE", "Z1": "RED ZONE"}


def _field(surf, snap):
    mirror = snap.offense is not None and snap.offense.color.value != "red"
    labels = list(reversed(LABELS)) if mirror else list(LABELS)

    x0, x1 = PAD + 10, W - PAD - 10
    span = x1 - x0
    step = span / 8.0
    ty = FIELD_Y + 46

    pygame.draw.line(surf, (30, 30, 36), (x0, ty), (x1, ty), 6)

    ball_x = None
    for i, lab in enumerate(labels):
        cx = x0 + step * (i + 0.5)
        here = lab == snap.ball_pos
        if here:
            ball_x = cx

        is_ez = lab == "EZ"
        is_rz = lab.startswith("Z")
        tick = ACCENT if here else (AMBER if is_rz else (FAINT if is_ez else DIM))
        pygame.draw.line(surf, tick if here else (44, 44, 52),
                         (cx, ty - 7), (cx, ty + 7), 2)

        d.text(surf, lab, (cx, FIELD_Y + 20), d.font("inter", 10, "bold"),
               TEXT if here else (AMBER if is_rz else DIM), anchor="center",
               tracking=1, tight=True)

    # segment boundaries, faint
    for i in range(1, 8):
        bx = x0 + step * i
        pygame.draw.line(surf, (26, 26, 32), (bx, ty - 3), (bx, ty + 3), 1)

    if ball_x is not None:
        pygame.draw.circle(surf, BG, (int(ball_x), ty), 11)
        pygame.draw.circle(surf, ACCENT, (int(ball_x), ty), 7)
        pygame.draw.circle(surf, d.alpha(ACCENT, 60), (int(ball_x), ty), 12, 2)
        label(surf, ZONES.get(snap.ball_pos, snap.ball_pos),
              (ball_x, ty + 22), ACCENT, "center", 9)

    arrow_x = x0 - 2 if mirror else x1 + 2
    d.chevron(surf, arrow_x, ty, 5, DIM, -1 if mirror else 1, 2)


# --- content ----------------------------------------------------------------

def _mini_card(surf, rect, card, ink_light=True):
    d.rrect(surf, rect, PANEL_2, radius=8)
    d.rrect(surf, rect, BORDER_HI, radius=8, width=1)
    if card.value == "Joker":
        d.text(surf, "JOKER", rect.center, d.font("inter", 10, "bold"), AMBER,
               anchor="center", tracking=1, tight=True)
        return
    ink = RED if card.color and card.color.value == "red" else TEXT
    d.text(surf, card.value, (rect.centerx, rect.centery - 8),
           d.font("inter", 20, "bold"), ink, anchor="center", tight=True)
    d.suit(surf, card.suit, (rect.centerx, rect.centery + 14), 15, ink)


def _status(surf, snap):
    rect = panel(surf, (PAD, CONT_Y + 12, LEFT_W, 150))

    if snap.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        label(surf, "RESULT", (rect.x + 18, rect.y + 18))
        d.text(surf, "Touchdown", (rect.x + 18, rect.y + 52),
               d.font("inter", 34, "bold"), ACCENT, tight=True)
        d.text(surf, f"{snap.offense.name} +6  ·  now choose the extra point",
               (rect.x + 18, rect.bottom - 30), d.font("inter", 13, "regular"),
               MUTED, tight=True)
        return

    if snap.off_card and snap.def_card:
        label(surf, "LAST PLAY", (rect.x + 18, rect.y + 18))
        cw, chh = 58, 74
        ox = rect.x + 18
        _mini_card(surf, pygame.Rect(ox, rect.y + 42, cw, chh), snap.off_card)
        label(surf, "OFFENSE", (ox, rect.y + 128), team_color(snap.offense))
        _mini_card(surf, pygame.Rect(ox + cw + 30, rect.y + 42, cw, chh), snap.def_card)
        label(surf, "DEFENSE", (ox + cw + 30, rect.y + 128), team_color(snap.defense))
        d.text(surf, "vs", (ox + cw + 15, rect.y + 79), d.font("inter", 12, "regular"),
               DIM, anchor="center", tight=True)

        tx = ox + cw * 2 + 70
        d.text(surf, f"+{snap.movement}", (tx, rect.y + 54),
               d.font("inter", 40, "bold"), ACCENT, tight=True)
        d.text(surf, "segments gained", (tx, rect.y + 100),
               d.font("inter", 12, "regular"), MUTED, tight=True)
        d.text(surf, f"ball now at {snap.ball_pos}", (tx, rect.y + 120),
               d.font("inter", 12, "regular"), DIM, tight=True)
        return

    defending = snap.phase == GamePhase.WAITING_DEFENSE_CARD
    label(surf, "YOUR MOVE", (rect.x + 18, rect.y + 18))
    d.text(surf, "Pick a defense card" if defending else "Pick an offense card",
           (rect.x + 18, rect.y + 52), d.font("inter", 26, "semibold"), TEXT,
           tight=True)
    hint = ("The higher rank wins the battle — their card stays hidden."
            if defending
            else "Each card shows the segments it gains at your drive rating.")
    d.text(surf, hint, (rect.x + 18, rect.bottom - 44),
           d.font("inter", 13, "regular"), MUTED, tight=True)
    d.text(surf, "Click one, or press 0–9.", (rect.x + 18, rect.bottom - 26),
           d.font("inter", 13, "regular"), DIM, tight=True)


def _log(surf, snap):
    top = CONT_Y + 12 + 150 + 14
    rect = panel(surf, (PAD, top, LEFT_W, HAND_Y - 12 - top))
    label(surf, "PLAY BY PLAY", (rect.x + 18, rect.y + 16))
    pygame.draw.line(surf, BORDER, (rect.x + 16, rect.y + 36),
                     (rect.right - 16, rect.y + 36))

    f = d.font("inter", 11, "regular")
    rows = (rect.h - 50) // 19
    msgs = snap.log_messages[-rows:]
    y = rect.y + 46
    for i, m in enumerate(msgs):
        col = MUTED if i >= len(msgs) - 3 else DIM
        if m.startswith("==="):
            col = TEXT
        elif "TOUCHDOWN" in m:
            col = ACCENT
        elif "CLUTCH" in m or "MOJO" in m:
            col = AMBER
        d.text(surf, m[:72], (rect.x + 18, y), f, col, tight=True)
        y += 19


def _team_card(surf, rect, team, is_off, cards_left):
    panel(surf, rect, radius=10, fill=PANEL)
    pygame.draw.circle(surf, team_color(team), (rect.x + 18, rect.y + 22), 4)
    d.text(surf, team.name, (rect.x + 32, rect.y + 22),
           d.font("inter", 12, "semibold"), TEXT, anchor="midleft",
           tracking=1, tight=True)
    if is_off:
        t = pygame.Rect(0, 0, 30, 15)
        t.midright = (rect.right - 16, rect.y + 22)
        d.rrect(surf, t, d.alpha(ACCENT, 38), radius=7)
        d.text(surf, "OFF", t.center, d.font("inter", 8, "bold"), ACCENT,
               anchor="center", tracking=1, tight=True)

    rows = [
        ("DRIVE RATING", str(team.rating), TEXT),
        ("KICK RATING", str(team.kick_rating), TEXT),
    ]
    y = rect.y + 48
    for name, val, col in rows:
        label(surf, name, (rect.x + 18, y + 5))
        d.text(surf, val, (rect.right - 18, y + 5), d.font("inter", 12, "bold"),
               col, anchor="topright", tight=True)
        y += 24

    label(surf, "CLUTCH", (rect.x + 18, y + 5))
    pips(surf, rect.right - 18 - 4 * 11, y + 9, team.clutch, 5, AMBER)
    y += 24
    label(surf, "MOJO", (rect.x + 18, y + 5))
    pips(surf, rect.right - 18 - 1 * 11, y + 9, team.mojo, 2, ACCENT)
    y += 26

    pygame.draw.line(surf, BORDER, (rect.x + 16, y), (rect.right - 16, y))
    label(surf, "CARDS IN HAND", (rect.x + 18, y + 12))
    d.text(surf, str(cards_left), (rect.right - 18, y + 10),
           d.font("inter", 12, "bold"), MUTED, anchor="topright", tight=True)


def _rail(surf, snap):
    h = (HAND_Y - 12 - (CONT_Y + 12) - 14) // 2
    _team_card(surf, pygame.Rect(RIGHT_X, CONT_Y + 12, RIGHT_W, h),
               snap.human, snap.offense is snap.human, len(snap.human.hand))
    _team_card(surf, pygame.Rect(RIGHT_X, CONT_Y + 12 + h + 14, RIGHT_W, h),
               snap.ai, snap.offense is snap.ai, len(snap.ai.hand))


# --- hand -------------------------------------------------------------------

def _hand_card(surf, rect, card, yards, index, selected):
    fill = PANEL_2 if not selected else (32, 42, 38)
    d.rrect(surf, rect, fill, radius=10)
    d.rrect(surf, rect, ACCENT if selected else BORDER_HI, radius=10,
            width=2 if selected else 1)

    if card.value == "Joker":
        d.text(surf, "JOKER", (rect.x + 12, rect.y + 20),
               d.font("inter", 13, "bold"), AMBER, anchor="midleft",
               tracking=1, tight=True)
        d.text(surf, "wild", (rect.x + 12, rect.bottom - 18),
               d.font("inter", 13, "semibold"), DIM, anchor="midleft", tight=True)
    else:
        ink = RED if card.color and card.color.value == "red" else TEXT
        d.text(surf, card.value, (rect.x + 12, rect.y + 20),
               d.font("inter", 22, "bold"), ink, anchor="midleft", tight=True)
        d.suit(surf, card.suit, (rect.right - 19, rect.y + 20), 19, ink)
        if yards is not None:
            col = ACCENT if yards > 0 else (DIM if yards == 0 else RED)
            d.text(surf, f"+{yards}" if yards >= 0 else str(yards),
                   (rect.x + 12, rect.bottom - 18),
                   d.font("inter", 15, "bold"), col, anchor="midleft", tight=True)

    chip = pygame.Rect(0, 0, 17, 15)
    chip.bottomright = (rect.right - 10, rect.bottom - 10)
    d.rrect(surf, chip, (36, 36, 43), radius=4)
    d.text(surf, str(index), chip.center, d.font("inter", 9, "bold"), MUTED,
           anchor="center", tight=True)


def _hand(surf, snap):
    pygame.draw.line(surf, BORDER, (0, HAND_Y), (W, HAND_Y))
    active = snap.phase in (GamePhase.WAITING_OFFENSE_CARD,
                            GamePhase.WAITING_DEFENSE_CARD)
    title = "PICK YOUR DEFENSE" if snap.phase == GamePhase.WAITING_DEFENSE_CARD \
        else "YOUR HAND"
    label(surf, title, (PAD, HAND_Y + 12), ACCENT if active else DIM)
    label(surf, f"OPPONENT HOLDS {len(snap.ai.hand)}", (W - PAD, HAND_Y + 12),
          DIM, "topright")

    # Card width follows the count so a full Q4 hand of 9 still fits the strip.
    cards = snap.human.hand
    n = max(1, len(cards))
    gap, chh = 10, 62
    cw = min(96, (W - PAD * 2 - (n - 1) * gap) // n)
    # On defense the drive chart doesn't apply — those numbers would be a lie.
    show_yards = snap.offense is snap.human
    x = PAD
    for i, card in enumerate(cards):
        r = pygame.Rect(x, HAND_Y + 30, cw, chh)
        _hand_card(surf, r, card,
                   card_yardage(snap, card) if show_yards else None,
                   i, active and i == 0)
        x += cw + gap


# --- actions ----------------------------------------------------------------

def _btn(surf, rect, text, key, enabled, primary=False):
    if not enabled:
        d.rrect(surf, rect, (15, 15, 18), radius=9)
        d.rrect(surf, rect, (30, 30, 36), radius=9, width=1)
        d.text(surf, text, rect.center, d.font("inter", 13, "semibold"),
               (66, 66, 76), anchor="center", tight=True)
        return
    if primary:
        d.rrect(surf, rect, ACCENT, radius=9)
        ink, keyc = (6, 26, 18), (6, 26, 18)
    else:
        d.rrect(surf, rect, PANEL_2, radius=9)
        d.rrect(surf, rect, BORDER_HI, radius=9, width=1)
        ink, keyc = TEXT, DIM
    d.text(surf, text, (rect.centerx, rect.centery), d.font("inter", 13, "semibold"),
           ink, anchor="center", tight=True)
    d.text(surf, key, (rect.right - 10, rect.centery), d.font("inter", 9, "bold"),
           d.alpha(keyc, 170) if primary else keyc, anchor="midright", tight=True)


def _actions(surf, snap):
    pygame.draw.line(surf, BORDER, (0, ACT_Y), (W, ACT_Y))
    cy = ACT_Y + ACT_H // 2

    if snap.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        specs = [("Kick PAT", "K", True, True), ("Go for 2  ·  d6 ≥ 5", "2", True, False)]
    elif snap.phase == GamePhase.WAITING_POST_MOVE:
        specs = [("Punt", "1", snap.can_punt, False),
                 ("Field goal", "2", snap.can_fg, snap.can_fg),
                 ("Clutch", "3", snap.can_clutch, False),
                 ("Short punt", "4", snap.can_short_punt, False)]
    else:
        label(surf, "WAITING ON YOU", (PAD, cy - 5), DIM)
        tail = ("Choose a card above to defend the play."
                if snap.phase == GamePhase.WAITING_DEFENSE_CARD
                else "Choose a card above to run the play.")
        d.text(surf, tail, (W - PAD, cy), d.font("inter", 13, "regular"), MUTED,
               anchor="midright", tight=True)
        return

    n = len(specs)
    bw = (W - PAD * 2 - (n - 1) * 12) // n
    for i, (t, k, en, prim) in enumerate(specs):
        _btn(surf, pygame.Rect(PAD + i * (bw + 12), cy - 21, bw, 42), t, k, en, prim)


def render(surf, snap):
    surf.fill(BG)
    _header(surf, snap)
    _field(surf, snap)
    _status(surf, snap)
    _log(surf, snap)
    _rail(surf, snap)
    _hand(surf, snap)
    _actions(surf, snap)
