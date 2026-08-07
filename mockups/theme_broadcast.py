"""Option A — "Broadcast".

A modern sports-television look: a full-width score bar, a real turf field
band with hash marks, and the hand rendered as actual playing cards. Keeps the
drive chart as its own reference rail, exactly like the current build.
"""

import pygame

from lib import draw as d
from lib.mockdata import GamePhase

W, H = 960, 720

NAME = "Broadcast"
BLURB = "Sports-TV score bar, turf field, real playing cards, chart rail kept as-is."

# --- palette ---
BG = (11, 14, 19)
PANEL = (21, 26, 34)
PANEL_HI = (29, 36, 47)
BORDER = (46, 55, 69)
TEXT = (234, 239, 246)
MUTED = (140, 152, 170)
DIM = (95, 106, 122)
GOLD = (250, 204, 21)
RED = (226, 62, 62)
SILVER = (198, 208, 224)
GREEN_OK = (52, 199, 123)

FIELD_TOP = (30, 104, 51)
FIELD_BOT = (18, 68, 34)
ENDZONE = (15, 52, 27)
CARD_FACE = (247, 248, 251)
CARD_INK = (24, 28, 36)
CARD_RED = (200, 40, 48)

SCORE_H = 104
FIELD_Y, FIELD_H = 104, 124
BODY_Y = FIELD_Y + FIELD_H
ACTION_H = 84
ACTION_Y = H - ACTION_H
BODY_H = ACTION_Y - BODY_Y

RAIL_X, RAIL_W = 14, 252
CHART_W = 176
CHART_X = W - 14 - CHART_W
CEN_X = RAIL_X + RAIL_W + 12
CEN_W = CHART_X - 12 - CEN_X


def team_color(team):
    return RED if team.color.value == "red" else SILVER


# --- score bar --------------------------------------------------------------

PIP_LABEL = d.font("inter", 10, "bold")
ORANGE = (255, 138, 32)


def _pips_w(label, cap):
    return d.text_size(label, PIP_LABEL, 1)[0] + 10 + cap * 16 - 4


def _pips(surf, x, cy, label, count, cap, color, kind="dot"):
    d.text(surf, label, (x, cy), PIP_LABEL, DIM, anchor="midleft", tracking=1)
    px = x + d.text_size(label, PIP_LABEL, 1)[0] + 10
    for i in range(cap):
        c = color if i < count else (52, 60, 74)
        if kind == "star":
            d.star(surf, (px + 6, cy), 6, c)
        else:
            pygame.draw.circle(surf, c, (px + 5, cy), 5)
        px += 16
    return px - 4


def _score_bar(surf, snap):
    d.grad_rect(surf, (0, 0, W, SCORE_H), PANEL_HI, PANEL)
    pygame.draw.line(surf, GOLD, (0, SCORE_H - 2), (W, SCORE_H - 2), 2)

    f_name = d.font("cond", 34, "bold")
    f_score = d.font("inter", 36, "bold")
    row_cy = 33

    for side, team in (("L", snap.human), ("R", snap.ai)):
        col = team_color(team)
        nm_w = d.text_size(team.name, f_name, tight=True)[0]

        if side == "L":
            pygame.draw.rect(surf, col, (20, 13, 5, 40), border_radius=3)
            nx = 36
            d.text(surf, team.name, (nx, row_cy), f_name, TEXT,
                   anchor="midleft", tight=True)
            d.text(surf, str(team.score), (nx + nm_w + 20, row_cy), f_score,
                   TEXT, anchor="midleft", tight=True)
            tag_left = nx
        else:
            pygame.draw.rect(surf, col, (W - 25, 13, 5, 40), border_radius=3)
            nx = W - 36
            d.text(surf, team.name, (nx, row_cy), f_name, TEXT,
                   anchor="midright", tight=True)
            d.text(surf, str(team.score), (nx - nm_w - 20, row_cy), f_score,
                   TEXT, anchor="midright", tight=True)
            tag_left = None

        if snap.offense is team:
            tw = d.text_size("OFFENSE", d.font("inter", 9, "bold"), 1)[0]
            tag = pygame.Rect(0, 0, tw + 16, 15)
            if tag_left is not None:
                tag.topleft = (tag_left, 55)
            else:
                tag.topright = (nx, 55)
            d.rrect(surf, tag, GOLD, radius=7)
            d.text(surf, "OFFENSE", tag.center, d.font("inter", 9, "bold"),
                   (26, 22, 6), anchor="center", tracking=1, tight=True)

    # centre quarter pill
    pill = pygame.Rect(0, 0, 132, 56)
    pill.midtop = (W // 2, 10)
    d.rrect(surf, pill, (13, 17, 23), radius=10)
    d.rrect(surf, pill, BORDER, radius=10, width=1)
    d.text(surf, f"Q{snap.quarter}", (pill.centerx, pill.y + 20),
           d.font("cond", 32, "bold"), GOLD, anchor="center", tight=True)
    d.text(surf, f"PLAY {snap.turn} / {snap.turns_in_quarter}",
           (pill.centerx, pill.bottom - 12), d.font("inter", 10, "semibold"),
           MUTED, anchor="center", tracking=1, tight=True)

    # row 2 — clutch / mojo / difficulty
    cy = 84
    x = _pips(surf, 20, cy, "CLUTCH", snap.human.clutch, 5, GOLD, "star")
    _pips(surf, x + 20, cy, "MOJO", snap.human.mojo, 2, ORANGE)

    total = _pips_w("CLUTCH", 5) + 20 + _pips_w("MOJO", 2)
    x = _pips(surf, W - 20 - total, cy, "CLUTCH", snap.ai.clutch, 5, GOLD, "star")
    _pips(surf, x + 20, cy, "MOJO", snap.ai.mojo, 2, ORANGE)

    diff = snap.difficulty.upper()
    dc = {"EASY": GREEN_OK, "MEDIUM": GOLD, "HARD": RED}.get(diff, GOLD)
    label = f"AI · {diff}"
    r = pygame.Rect(0, 0, d.text_size(label, PIP_LABEL, 1)[0] + 18, 18)
    r.center = (W // 2, cy)
    d.rrect(surf, r, d.alpha(dc, 34), radius=9)
    d.text(surf, label, r.center, PIP_LABEL, dc, anchor="center",
           tracking=1, tight=True)


# --- field ------------------------------------------------------------------

LABELS = ["EZ", "1", "2", "3", "Z3", "Z2", "Z1", "EZ"]
ZONES = ["OWN G", "OWN 1", "OWN 2", "OWN 3", "RED", "RED", "RED", "END ZONE"]


def _field(surf, snap):
    rect = pygame.Rect(0, FIELD_Y, W, FIELD_H)
    d.grad_rect(surf, rect, FIELD_TOP, FIELD_BOT)

    mirror = snap.offense is not None and snap.offense.color.value != "red"
    labels = list(reversed(LABELS)) if mirror else list(LABELS)
    zones = list(reversed(ZONES)) if mirror else list(ZONES)

    pad = 16
    seg_w = (W - pad * 2) / 8.0
    top = FIELD_Y + 26
    bot = FIELD_Y + FIELD_H - 22

    for i, label in enumerate(labels):
        sx = pad + i * seg_w
        seg = pygame.Rect(int(sx), top, int(seg_w) + 1, bot - top)

        if label == "EZ":
            pygame.draw.rect(surf, ENDZONE, seg)
            for hx in range(seg.left - seg.h, seg.right, 14):
                pygame.draw.line(surf, d.alpha(SILVER, 22),
                                 (hx, seg.bottom), (hx + seg.h, seg.top), 2)
        elif label.startswith("Z"):
            pygame.draw.rect(surf, d.mix(FIELD_TOP, (150, 40, 40), 0.16), seg)

        pygame.draw.line(surf, d.alpha((255, 255, 255), 70),
                         (seg.right, top), (seg.right, bot))

        # hash marks
        for k in range(1, 4):
            hx = seg.left + seg.w * k / 4
            pygame.draw.line(surf, d.alpha((255, 255, 255), 34),
                             (hx, top + 4), (hx, top + 11))
            pygame.draw.line(surf, d.alpha((255, 255, 255), 34),
                             (hx, bot - 11), (hx, bot - 4))

        d.text(surf, label, (seg.centerx, FIELD_Y + 15),
               d.font("cond", 18, "bold"), d.alpha((255, 255, 255), 200),
               anchor="center", tight=True)
        d.text(surf, zones[i], (seg.centerx, FIELD_Y + FIELD_H - 12),
               d.font("inter", 8, "semibold"), d.alpha((255, 255, 255), 120),
               anchor="center", tracking=1, tight=True)

    # Drive direction reads from repeating chevrons rather than a text overlay,
    # so nothing collides with the segment labels.
    dirn = -1 if mirror else 1
    mid_y = (top + bot) // 2
    ball_cx = None
    for i, label in enumerate(labels):
        if label == snap.ball_pos:
            ball_cx = int(pad + i * seg_w + seg_w / 2)

    play_l, play_r = pad + seg_w, W - pad - seg_w  # between the end zones
    cx = play_l + 22
    while cx < play_r:
        if ball_cx is None or abs(cx - ball_cx) > 46:
            d.chevron(surf, cx, mid_y, 6, d.alpha((255, 255, 255), 20), dirn, 3)
        cx += 46

    if ball_cx is not None:
        seg_cx = ball_cx
        d.shadow(surf, pygame.Rect(seg_cx - 27, mid_y - 16, 54, 32),
                 radius=16, spread=10, a=130, offset=(0, 4))
        d.football(surf, (seg_cx, mid_y), 54, 32, (132, 80, 30),
                   team_color(snap.offense) if snap.offense else GOLD)


# --- hand -------------------------------------------------------------------

def _card_face(surf, rect, card, selected=False, index=None, scale=1.0):
    if selected:
        d.shadow(surf, rect, radius=8, spread=10, a=150, offset=(0, 5))

    is_joker = card.value == "Joker"
    face = (253, 246, 214) if is_joker else CARD_FACE
    d.rrect(surf, rect, face, radius=8)
    if selected:
        d.rrect(surf, rect.inflate(6, 6), GOLD, radius=11, width=3)
    else:
        d.rrect(surf, rect, (206, 212, 226), radius=8, width=1)

    if is_joker:
        d.text(surf, "JOKER", rect.center, d.font("cond", int(22 * scale), "bold"),
               (150, 92, 12), anchor="center", tracking=1, tight=True)
    else:
        ink = CARD_RED if card.color and card.color.value == "red" else CARD_INK
        d.text(surf, card.value, (rect.x + 9, rect.y + 9),
               d.font("inter", int(21 * scale), "bold"), ink, tight=True)
        d.suit(surf, card.suit, (rect.right - 24 * scale, rect.centery + 6 * scale),
               30 * scale, ink)

    if index is not None:
        chip = pygame.Rect(rect.x + 6, rect.bottom - 20, 16, 14)
        d.rrect(surf, chip, (222, 227, 238), radius=4)
        d.text(surf, str(index), chip.center, d.font("inter", 9, "bold"),
               (110, 118, 134), anchor="center", tight=True)


def _hand(surf, snap):
    rect = pygame.Rect(RAIL_X, BODY_Y + 8, RAIL_W, BODY_H - 16)
    d.rrect(surf, rect, PANEL, radius=12)
    d.rrect(surf, rect, BORDER, radius=12, width=1)

    active = snap.phase in (GamePhase.WAITING_OFFENSE_CARD,
                            GamePhase.WAITING_DEFENSE_CARD)
    title = "YOUR HAND" if snap.phase != GamePhase.WAITING_DEFENSE_CARD else "PICK DEFENSE"
    d.text(surf, title, (rect.x + 16, rect.y + 18), d.font("inter", 11, "bold"),
           GOLD if active else MUTED, tracking=2, tight=True)
    d.text(surf, str(len(snap.human.hand)), (rect.right - 16, rect.y + 13),
           d.font("inter", 12, "bold"), DIM, anchor="topright")
    d.hairline(surf, rect.x + 14, rect.y + 38, rect.right - 14, BORDER)

    # Two columns, row height derived from the count — a Q4 hand can reach 9.
    n = max(1, len(snap.human.hand))
    rows = (n + 1) // 2
    gap = 10
    y0 = rect.y + 50
    avail = (rect.bottom - 40) - y0
    ch = max(46, min(70, (avail - (rows - 1) * gap) // rows))
    cw = (rect.w - 32 - 12) // 2
    x0 = rect.x + 16
    for i, card in enumerate(snap.human.hand):
        col, row = i % 2, i // 2
        cr = pygame.Rect(x0 + col * (cw + 12), y0 + row * (ch + gap), cw, ch)
        _card_face(surf, cr, card, active and i == 0, i,
                   scale=0.86 if ch < 60 else 1.0)

    foot = rect.bottom - 30
    d.hairline(surf, rect.x + 14, foot - 10, rect.right - 14, BORDER)
    d.text(surf, "OPPONENT", (rect.x + 16, foot + 4), d.font("inter", 9, "bold"),
           DIM, tracking=1, tight=True)
    d.text(surf, f"{len(snap.ai.hand)} cards", (rect.right - 16, foot),
           d.font("inter", 10, "semibold"), MUTED, anchor="topright")


# --- centre -----------------------------------------------------------------

def _battle(surf, snap):
    rect = pygame.Rect(CEN_X, BODY_Y + 8, CEN_W, 138)
    d.rrect(surf, rect, PANEL, radius=12)
    d.rrect(surf, rect, BORDER, radius=12, width=1)

    if snap.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        d.text(surf, "TOUCHDOWN", (rect.centerx, rect.centery - 12),
               d.font("cond", 54, "bold"), GOLD, anchor="center",
               tracking=3, tight=True)
        d.text(surf, f"{snap.offense.name}  +6", (rect.centerx, rect.bottom - 26),
               d.font("inter", 13, "semibold"), TEXT, anchor="center", tight=True)
        return

    if snap.off_card and snap.def_card:
        d.text(surf, "THE PLAY", (rect.centerx, rect.y + 16),
               d.font("inter", 10, "bold"), DIM, anchor="center",
               tracking=2, tight=True)
        for tag, card, team, cx in (
            ("OFFENSE", snap.off_card, snap.offense, rect.centerx - 112),
            ("DEFENSE", snap.def_card, snap.defense, rect.centerx + 112),
        ):
            d.text(surf, tag, (cx, rect.y + 38), d.font("inter", 9, "bold"),
                   team_color(team), anchor="center", tracking=1, tight=True)
            cr = pygame.Rect(0, 0, 62, 54)
            cr.midtop = (cx, rect.y + 48)
            _card_face(surf, cr, card, scale=0.86)
            d.text(surf, team.name, (cx, rect.bottom - 18),
                   d.font("inter", 10, "semibold"), MUTED, anchor="center",
                   tight=True)

        d.text(surf, "VS", (rect.centerx, rect.y + 76),
               d.font("cond", 26, "bold"), DIM, anchor="center", tight=True)

        if snap.movement:
            badge = pygame.Rect(0, 0, 112, 22)
            badge.center = (rect.centerx, rect.y + 108)
            d.rrect(surf, badge, d.alpha(GREEN_OK, 40), radius=11)
            d.text(surf, f"+{snap.movement} SEGMENTS", badge.center,
                   d.font("inter", 10, "bold"), GREEN_OK, anchor="center",
                   tight=True)
        return

    d.text(surf, snap.message or "—", rect.center, d.font("cond", 30, "bold"),
           TEXT, anchor="center", tight=True)


def _log(surf, snap):
    top = BODY_Y + 8 + 138 + 10
    rect = pygame.Rect(CEN_X, top, CEN_W, BODY_Y + BODY_H - 8 - top)
    d.rrect(surf, rect, PANEL, radius=12)
    d.rrect(surf, rect, BORDER, radius=12, width=1)

    d.text(surf, "PLAY BY PLAY", (rect.x + 16, rect.y + 16),
           d.font("inter", 10, "bold"), DIM, tracking=2, tight=True)
    d.hairline(surf, rect.x + 14, rect.y + 32, rect.right - 14, BORDER)

    f = d.font("inter", 11, "regular")
    rows = (rect.h - 44) // 19
    msgs = snap.log_messages[-rows:]
    y = rect.y + 40
    for i, m in enumerate(msgs):
        fresh = i >= len(msgs) - 2
        col = TEXT if fresh else MUTED
        if m.startswith("==="):
            col = GOLD
        elif "TOUCHDOWN" in m or "CLUTCH" in m or "MOJO" in m:
            col = (255, 168, 60)
        d.text(surf, m[:64], (rect.x + 16, y), f, col)
        y += 19


def _chart(surf, snap):
    rect = pygame.Rect(CHART_X, BODY_Y + 8, CHART_W, BODY_H - 16)
    d.rrect(surf, rect, PANEL, radius=12)
    d.rrect(surf, rect, BORDER, radius=12, width=1)

    from ccf.drive_chart import DRIVE_CHART
    rating = snap.offense.rating if snap.offense else 6
    chart = DRIVE_CHART.get(str(rating), {})

    d.text(surf, "DRIVE CHART", (rect.x + 14, rect.y + 16),
           d.font("inter", 10, "bold"), DIM, tracking=2, tight=True)
    d.text(surf, f"RATING {rating}", (rect.x + 14, rect.y + 28),
           d.font("inter", 11, "bold"), GOLD)
    d.hairline(surf, rect.x + 12, rect.y + 48, rect.right - 12, BORDER)

    order = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    bonus_col = {"yellow": (240, 200, 60), "orange": (245, 145, 40),
                 "green": (60, 200, 110)}
    row_h = (rect.h - 62) / len(order)
    for i, val in enumerate(order):
        y = rect.y + 56 + i * row_h
        entry = chart.get(val, {"base": 0})
        if i % 2 == 0:
            d.rrect(surf, (rect.x + 8, int(y) - 2, rect.w - 16, int(row_h)),
                    (26, 32, 42), radius=5)
        d.text(surf, val, (rect.x + 18, y), d.font("inter", 11, "semibold"), TEXT)
        base = entry.get("base", 0)
        d.text(surf, f"+{base}" if base >= 0 else str(base),
               (rect.x + 96, y), d.font("inter", 11, "bold"),
               MUTED if base <= 0 else TEXT, anchor="topright")
        b = entry.get("bonus")
        if b:
            pygame.draw.circle(surf, bonus_col[b], (rect.right - 24, int(y) + 7), 5)


# --- action bar -------------------------------------------------------------

def _button(surf, rect, label, key, enabled, primary=False):
    if enabled:
        base = GOLD if primary else PANEL_HI
        d.rrect(surf, rect, base, radius=10)
        d.rrect(surf, rect, d.shade(base, 0.22 if primary else 0.10),
                radius=10, width=1)
        ink = (26, 22, 6) if primary else TEXT
        keyc = d.alpha((26, 22, 6), 150) if primary else DIM
    else:
        d.rrect(surf, rect, (18, 22, 29), radius=10)
        d.rrect(surf, rect, (34, 40, 51), radius=10, width=1)
        ink, keyc = (74, 82, 96), (58, 65, 78)

    d.text(surf, label, rect.center, d.font("cond", 22, "bold"), ink,
           anchor="center", tracking=1, tight=True)
    d.text(surf, key, (rect.right - 10, rect.y + 8), d.font("inter", 9, "bold"),
           keyc, anchor="topright", tight=True)


def _actions(surf, snap):
    d.grad_rect(surf, (0, ACTION_Y, W, ACTION_H), PANEL, (14, 18, 24))
    pygame.draw.line(surf, BORDER, (0, ACTION_Y), (W, ACTION_Y))

    phase = snap.phase
    if phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        d.text(surf, "EXTRA POINT", (20, ACTION_Y + 16),
               d.font("inter", 10, "bold"), DIM, tracking=2, tight=True)
        specs = [("KICK PAT", "K", True, True), ("GO FOR 2  ·  d6 ≥ 5", "2", True, False)]
        bw = (W - 40 - 14) // 2
        for i, (lab, k, en, prim) in enumerate(specs):
            _button(surf, pygame.Rect(20 + i * (bw + 14), ACTION_Y + 30, bw, 42),
                    lab, k, en, prim)
        return

    if phase == GamePhase.WAITING_POST_MOVE:
        ctx = f"BALL AT {snap.ball_pos}"
        if snap.can_fg:
            ctx += "   ·   RED ZONE — FIELD GOAL AVAILABLE"
        d.text(surf, ctx, (20, ACTION_Y + 16), d.font("inter", 10, "bold"),
               GOLD if snap.can_fg else DIM, tracking=2, tight=True)
        specs = [("PUNT", "1", snap.can_punt), ("FIELD GOAL", "2", snap.can_fg),
                 ("CLUTCH", "3", snap.can_clutch), ("SHORT PUNT", "4", snap.can_short_punt)]
        bw = (W - 40 - 3 * 12) // 4
        for i, (lab, k, en) in enumerate(specs):
            _button(surf, pygame.Rect(20 + i * (bw + 12), ACTION_Y + 30, bw, 42),
                    lab, k, en, primary=(lab == "FIELD GOAL" and en))
        return

    d.text(surf, "SELECT A CARD", (20, ACTION_Y + 16),
           d.font("inter", 10, "bold"), GOLD, tracking=2, tight=True)
    d.text(surf, "Click a card, or press 0–9  ·  ↑ ↓ to move, ENTER to play",
           (20, ACTION_Y + 36), d.font("inter", 13, "regular"), MUTED)


def render(surf, snap):
    surf.fill(BG)
    _score_bar(surf, snap)
    _field(surf, snap)
    _hand(surf, snap)
    _battle(surf, snap)
    _log(surf, snap)
    _chart(surf, snap)
    _actions(surf, snap)
