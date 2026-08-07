"""Option C — "Neon Arcade".

Keeps the arcade energy of the current build but drops the CRT grime: deep
indigo ground, neon cyan/magenta accents, glow instead of scanlines, chunky
rounded geometry. The drive chart becomes a horizontal strip under the field.
"""

import pygame

from lib import draw as d
from lib.mockdata import GamePhase
from ccf.drive_chart import DRIVE_CHART, get_drive_result

W, H = 960, 720

NAME = "Neon Arcade"
BLURB = "Modern evolution of the retro look — neon glow, no scanlines, chart strip."

# --- palette ---
BG = (13, 11, 31)
BG2 = (19, 16, 44)
PANEL = (25, 21, 58)
PANEL2 = (33, 28, 74)
BORDER = (60, 50, 122)
GRID = (23, 20, 52)
CYAN = (34, 211, 238)
MAGENTA = (244, 114, 182)
LIME = (163, 230, 53)
YELLOW = (250, 204, 21)
TEXT = (234, 232, 255)
MUTED = (156, 150, 202)
DIM = (110, 104, 160)

HUD_H = 96
FIELD_Y, FIELD_H = 96, 140
STRIP_Y, STRIP_H = 236, 42
MID_Y = STRIP_Y + STRIP_H
HAND_Y, HAND_H = 530, 110
ACT_Y, ACT_H = 640, 80
MID_H = HAND_Y - MID_Y

PAD = 20
LEFT_W = 596
RIGHT_X = PAD + LEFT_W + 16
RIGHT_W = W - PAD - RIGHT_X


def team_color(team):
    return (255, 94, 122) if team.color.value == "red" else (110, 200, 255)


def label(surf, s, pos, color=DIM, anchor="topleft", size=9, tracking=2):
    return d.text(surf, s, pos, d.font("inter", size, "bold"), color,
                  anchor=anchor, tracking=tracking, tight=True)


def _grid(surf):
    surf.fill(BG)
    for x in range(0, W, 40):
        pygame.draw.line(surf, GRID, (x, 0), (x, H))
    for y in range(0, H, 40):
        pygame.draw.line(surf, GRID, (0, y), (W, y))


# --- HUD --------------------------------------------------------------------

def _bar_pips(surf, x, cy, count, cap, color, w=13, h=6, gap=4):
    for i in range(cap):
        r = pygame.Rect(x + i * (w + gap), cy - h // 2, w, h)
        if i < count:
            d.rrect(surf, r, color, radius=3)
        else:
            d.rrect(surf, r, (44, 38, 92), radius=3)
    return x + cap * (w + gap) - gap


CLUTCH_W = 5 * 17 - 4
MOJO_W = 2 * 17 - 4


def _pod(surf, rect, team, on_off, right):
    col = team_color(team)
    if on_off:
        d.glow(surf, rect, col, radius=14, spread=16, a=52)
    d.rrect(surf, rect, PANEL, radius=14)
    d.rrect(surf, rect, col if on_off else BORDER, radius=14, width=2)

    x0, x1 = rect.x + 18, rect.right - 18
    name_y, score_y = rect.y + 21, rect.y + 53
    lab_f = d.font("inter", 8, "bold")
    cl_w = d.text_size("CLUTCH", lab_f, 2)[0]
    mj_w = d.text_size("MOJO", lab_f, 2)[0]

    if right:
        d.text(surf, team.name, (x1, name_y), d.font("cond", 27, "bold"), TEXT,
               anchor="midright", tracking=1, tight=True)
        d.text(surf, str(team.score), (x1, score_y), d.font("cond", 42, "bold"),
               col, anchor="midright", tight=True)
        bars_x = x1 - 70 - CLUTCH_W
        lab_anchor, lab_x = "midright", bars_x - 8
    else:
        d.text(surf, team.name, (x0, name_y), d.font("cond", 27, "bold"), TEXT,
               anchor="midleft", tracking=1, tight=True)
        d.text(surf, str(team.score), (x0, score_y), d.font("cond", 42, "bold"),
               col, anchor="midleft", tight=True)
        lab_x = x0 + 70
        bars_x = lab_x + max(cl_w, mj_w) + 10
        lab_anchor = "midleft"

    label(surf, "CLUTCH", (lab_x, rect.y + 44), DIM, lab_anchor, 8)
    _bar_pips(surf, bars_x, rect.y + 44, team.clutch, 5, YELLOW)
    label(surf, "MOJO", (lab_x, rect.y + 66), DIM, lab_anchor, 8)
    _bar_pips(surf, bars_x, rect.y + 66, team.mojo, 2, MAGENTA)

    if on_off:
        t = pygame.Rect(0, 0, 68, 16)
        if right:
            t.topleft = (rect.x + 14, rect.y + 12)
        else:
            t.topright = (rect.right - 14, rect.y + 12)
        d.rrect(surf, t, col, radius=8)
        d.text(surf, "ON OFFENSE", t.center, d.font("inter", 7, "bold"),
               BG, anchor="center", tracking=1, tight=True)


def _hud(surf, snap):
    pod_w = 380
    _pod(surf, pygame.Rect(PAD, 8, pod_w, HUD_H - 20), snap.human,
         snap.offense is snap.human, right=False)
    _pod(surf, pygame.Rect(W - PAD - pod_w, 8, pod_w, HUD_H - 20), snap.ai,
         snap.offense is snap.ai, right=True)

    cap = pygame.Rect(0, 0, 120, HUD_H - 20)
    cap.midtop = (W // 2, 8)
    d.glow(surf, cap, CYAN, radius=14, spread=12, a=44)
    d.rrect(surf, cap, PANEL2, radius=14)
    d.rrect(surf, cap, CYAN, radius=14, width=2)
    d.text(surf, f"Q{snap.quarter}", (cap.centerx, cap.y + 26),
           d.font("cond", 38, "bold"), CYAN, anchor="center", tight=True)
    label(surf, f"PLAY {snap.turn}/{snap.turns_in_quarter}",
          (cap.centerx, cap.y + 54), TEXT, "center", 9)
    label(surf, snap.difficulty.upper(), (cap.centerx, cap.bottom - 14),
          MAGENTA, "center", 8)


# --- field ------------------------------------------------------------------

LABELS = ["EZ", "1", "2", "3", "Z3", "Z2", "Z1", "EZ"]


def _field(surf, snap):
    mirror = snap.offense is not None and snap.offense.color.value != "red"
    labels = list(reversed(LABELS)) if mirror else list(LABELS)

    pad = PAD
    gap = 6
    total = W - pad * 2
    seg_w = (total - gap * 7) / 8.0
    top = FIELD_Y + 24
    hgt = FIELD_H - 40

    ball_rect = None
    for i, lab in enumerate(labels):
        x = pad + i * (seg_w + gap)
        r = pygame.Rect(int(x), top, int(seg_w), hgt)
        here = lab == snap.ball_pos
        is_ez = lab == "EZ"
        is_rz = lab.startswith("Z")

        tint = MAGENTA if is_rz else (CYAN if is_ez else BORDER)
        d.rrect(surf, r, PANEL if not is_ez else (30, 18, 58), radius=8)
        d.rrect(surf, r, d.alpha(tint, 150 if (is_rz or is_ez) else 255),
                radius=8, width=2)

        if is_ez:
            for hx in range(r.left - r.h, r.right, 18):
                pygame.draw.line(surf, d.alpha(CYAN, 16),
                                 (max(hx, r.left), r.bottom),
                                 (min(hx + r.h, r.right), r.top), 2)

        if here:
            ball_rect = r
        else:
            lab_col = TEXT if is_ez else (d.alpha(tint, 210) if is_rz else MUTED)
            d.text(surf, lab, r.center, d.font("cond", 24, "bold"), lab_col,
                   anchor="center", tight=True)

    if ball_rect is not None:
        col = team_color(snap.offense) if snap.offense else LIME
        d.glow(surf, ball_rect, col, radius=8, spread=16, a=90)
        d.rrect(surf, ball_rect, d.alpha(col, 40), radius=8)
        d.rrect(surf, ball_rect, col, radius=8, width=3)
        d.football(surf, (ball_rect.centerx, ball_rect.centery - 4), 52, 30,
                   (140, 84, 32), col)
        label(surf, snap.ball_pos, (ball_rect.centerx, ball_rect.bottom - 12),
              col, "center", 10)

    dirn = -1 if mirror else 1
    for k in range(3):
        d.chevron(surf, W // 2 + dirn * (18 + k * 11), FIELD_Y + 12, 5,
                  d.alpha(CYAN, 190 - k * 55), dirn, 2)
    label(surf, "DRIVE", (W // 2 - dirn * 22, FIELD_Y + 12), DIM,
          "midright" if dirn > 0 else "midleft", 8)


# --- drive chart strip ------------------------------------------------------

ORDER = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
BONUS = {"yellow": YELLOW, "orange": (251, 146, 60), "green": LIME}


def _chart_strip(surf, snap):
    rating = snap.offense.rating if snap.offense else 6
    chart = DRIVE_CHART.get(str(rating), {})
    label(surf, f"DRIVE CHART · RATING {rating}", (PAD, STRIP_Y + STRIP_H // 2),
          DIM, "midleft", 9)

    x0 = PAD + 168
    cw = (W - PAD - x0) / len(ORDER)
    for i, val in enumerate(ORDER):
        cell = pygame.Rect(int(x0 + i * cw), STRIP_Y + 6, int(cw) - 5, STRIP_H - 14)
        entry = chart.get(val, {"base": 0})
        b = entry.get("bonus")
        d.rrect(surf, cell, PANEL, radius=6)
        d.rrect(surf, cell, d.alpha(BONUS[b], 200) if b else BORDER, radius=6, width=1)
        d.text(surf, val, (cell.x + 7, cell.centery), d.font("inter", 10, "bold"),
               MUTED, anchor="midleft", tight=True)
        base = entry.get("base", 0)
        d.text(surf, f"+{base}" if base >= 0 else str(base),
               (cell.right - 7, cell.centery), d.font("inter", 11, "bold"),
               BONUS[b] if b else TEXT, anchor="midright", tight=True)


# --- mid stage --------------------------------------------------------------

def _neon_card(surf, rect, card, ring=None):
    ring = ring or BORDER
    d.rrect(surf, rect, PANEL2, radius=10)
    d.rrect(surf, rect, ring, radius=10, width=2)
    if card.value == "Joker":
        d.text(surf, "JOKER", rect.center, d.font("cond", 22, "bold"), YELLOW,
               anchor="center", tracking=1, tight=True)
        return
    ink = (255, 120, 140) if card.color and card.color.value == "red" else TEXT
    d.text(surf, card.value, (rect.centerx, rect.centery - 12),
           d.font("cond", 40, "bold"), ink, anchor="center", tight=True)
    d.suit(surf, card.suit, (rect.centerx, rect.centery + 22), 22, ink)


def _stage(surf, snap):
    rect = pygame.Rect(PAD, MID_Y + 10, LEFT_W, MID_H - 20)
    d.rrect(surf, rect, PANEL, radius=14)
    d.rrect(surf, rect, BORDER, radius=14, width=2)

    if snap.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        inner = rect.inflate(-56, -72)
        d.rrect(surf, inner, d.alpha(LIME, 16), radius=18)
        d.glow(surf, inner, LIME, radius=18, spread=20, a=120)
        d.rrect(surf, inner, d.alpha(LIME, 120), radius=18, width=2)
        d.text(surf, "TOUCHDOWN", (rect.centerx, rect.centery - 18),
               d.font("cond", 62, "bold"), LIME, anchor="center",
               tracking=4, tight=True)
        d.text(surf, f"{snap.offense.name}  +6", (rect.centerx, rect.centery + 30),
               d.font("cond", 26, "bold"), TEXT, anchor="center",
               tracking=1, tight=True)
        return

    if snap.off_card and snap.def_card:
        label(surf, "CARD BATTLE", (rect.centerx, rect.y + 20), DIM, "center", 9)
        cw, chh = 92, 122
        oc = pygame.Rect(0, 0, cw, chh)
        oc.center = (rect.centerx - 132, rect.centery + 12)
        dc = pygame.Rect(0, 0, cw, chh)
        dc.center = (rect.centerx + 132, rect.centery + 12)

        d.glow(surf, oc, team_color(snap.offense), radius=10, spread=12, a=60)
        _neon_card(surf, oc, snap.off_card, team_color(snap.offense))
        _neon_card(surf, dc, snap.def_card, team_color(snap.defense))
        label(surf, "OFFENSE", (oc.centerx, oc.bottom + 16),
              team_color(snap.offense), "center", 8)
        label(surf, "DEFENSE", (dc.centerx, dc.bottom + 16),
              team_color(snap.defense), "center", 8)

        d.text(surf, f"+{snap.movement}", (rect.centerx, rect.centery - 4),
               d.font("cond", 54, "bold"), LIME, anchor="center", tight=True)
        label(surf, "SEGMENTS", (rect.centerx, rect.centery + 30), MUTED, "center", 8)
        return

    label(surf, "YOUR MOVE", (rect.centerx, rect.y + 22), DIM, "center", 9)
    d.text(surf, snap.message or "", (rect.centerx, rect.centery - 6),
           d.font("cond", 40, "bold"), CYAN, anchor="center", tracking=1, tight=True)
    d.text(surf, "Click a card below, or press 0–9",
           (rect.centerx, rect.centery + 34), d.font("inter", 12, "regular"),
           MUTED, anchor="center", tight=True)


def _log(surf, snap):
    rect = pygame.Rect(RIGHT_X, MID_Y + 10, RIGHT_W, MID_H - 20)
    d.rrect(surf, rect, PANEL, radius=14)
    d.rrect(surf, rect, BORDER, radius=14, width=2)
    label(surf, "PLAY BY PLAY", (rect.x + 16, rect.y + 18), DIM)
    pygame.draw.line(surf, BORDER, (rect.x + 14, rect.y + 36),
                     (rect.right - 14, rect.y + 36))

    f = d.font("inter", 10, "regular")
    rows = (rect.h - 52) // 18
    msgs = snap.log_messages[-rows:]
    y = rect.y + 46
    for i, m in enumerate(msgs):
        col = MUTED if i >= len(msgs) - 3 else DIM
        if "TOUCHDOWN" in m:
            col = LIME
        elif "CLUTCH" in m or "MOJO" in m:
            col = MAGENTA
        elif m.startswith("==="):
            col = CYAN
        d.text(surf, m[:42], (rect.x + 16, y), f, col, tight=True)
        y += 18


# --- hand -------------------------------------------------------------------

def _hand(surf, snap):
    active = snap.phase in (GamePhase.WAITING_OFFENSE_CARD,
                            GamePhase.WAITING_DEFENSE_CARD)
    title = "PICK YOUR DEFENSE" if snap.phase == GamePhase.WAITING_DEFENSE_CARD \
        else "YOUR HAND"
    label(surf, title, (PAD, HAND_Y + 12), CYAN if active else DIM)
    label(surf, f"OPPONENT · {len(snap.ai.hand)}", (W - PAD, HAND_Y + 12),
          DIM, "topright")

    off = snap.offense or snap.human
    # Drive-chart yardage only means anything while we're the offense.
    show_yards = snap.offense is snap.human
    cards = snap.human.hand
    n = max(1, len(cards))
    gap, chh = 10, 66
    cw = min(104, (W - PAD * 2 - (n - 1) * gap) // n)

    x = PAD
    for i, card in enumerate(cards):
        r = pygame.Rect(x, HAND_Y + 30, cw, chh)
        sel = active and i == 0
        if sel:
            d.glow(surf, r, CYAN, radius=10, spread=13, a=80)
        d.rrect(surf, r, PANEL2 if not sel else (32, 46, 82), radius=10)
        d.rrect(surf, r, CYAN if sel else BORDER, radius=10, width=2)

        if card.value == "Joker":
            d.text(surf, "JOKER", (r.centerx, r.centery - 4),
                   d.font("cond", 20, "bold"), YELLOW, anchor="center",
                   tracking=1, tight=True)
        else:
            ink = (255, 120, 140) if card.color and card.color.value == "red" else TEXT
            d.text(surf, card.value, (r.x + 11, r.y + 22),
                   d.font("cond", 32, "bold"), ink, anchor="midleft", tight=True)
            d.suit(surf, card.suit, (r.right - 17, r.y + 22), 19, ink)
            if show_yards:
                yards = get_drive_result(off.color.value, off.rating,
                                         card.value, card.suit)
                col = LIME if yards > 0 else DIM
                badge = pygame.Rect(0, 0, r.w - 22, 20)
                badge.midbottom = (r.centerx, r.bottom - 8)
                d.rrect(surf, badge, d.alpha(col, 38), radius=6)
                d.text(surf, f"+{yards} SEG", badge.center,
                       d.font("inter", 10, "bold"), col, anchor="center", tight=True)

        d.text(surf, str(i), (r.x + 8, r.bottom - 9), d.font("inter", 8, "bold"),
               DIM, anchor="midleft", tight=True)
        x += cw + gap


# --- actions ----------------------------------------------------------------

def _btn(surf, rect, text, key, enabled, accent=CYAN, primary=False):
    if not enabled:
        d.rrect(surf, rect, (22, 19, 48), radius=10)
        d.rrect(surf, rect, (44, 38, 88), radius=10, width=2)
        d.text(surf, text, rect.center, d.font("cond", 22, "bold"), (82, 76, 128),
               anchor="center", tracking=1, tight=True)
        return
    if primary:
        d.glow(surf, rect, accent, radius=10, spread=12, a=80)
        d.rrect(surf, rect, accent, radius=10)
        ink, keyc = BG, d.alpha(BG, 150)
    else:
        d.rrect(surf, rect, PANEL2, radius=10)
        d.rrect(surf, rect, accent, radius=10, width=2)
        ink, keyc = TEXT, DIM
    d.text(surf, text, rect.center, d.font("cond", 22, "bold"), ink,
           anchor="center", tracking=1, tight=True)
    d.text(surf, key, (rect.right - 9, rect.y + 8), d.font("inter", 8, "bold"),
           keyc, anchor="topright", tight=True)


def _actions(surf, snap):
    cy = ACT_Y + ACT_H // 2
    if snap.phase == GamePhase.WAITING_EXTRA_POINT_CHOICE:
        specs = [("KICK PAT", "K", True, LIME, True),
                 ("GO FOR 2 · d6 ≥ 5", "2", True, MAGENTA, False)]
    elif snap.phase == GamePhase.WAITING_POST_MOVE:
        specs = [("PUNT", "1", snap.can_punt, CYAN, False),
                 ("FIELD GOAL", "2", snap.can_fg, LIME, snap.can_fg),
                 ("CLUTCH", "3", snap.can_clutch, YELLOW, False),
                 ("SHORT PUNT", "4", snap.can_short_punt, CYAN, False)]
    else:
        d.text(surf, "Pick a card to run the play", (W // 2, cy),
               d.font("inter", 13, "regular"), DIM, anchor="center", tight=True)
        return

    n = len(specs)
    bw = (W - PAD * 2 - (n - 1) * 12) // n
    for i, (t, k, en, acc, prim) in enumerate(specs):
        _btn(surf, pygame.Rect(PAD + i * (bw + 12), cy - 23, bw, 46),
             t, k, en, acc, prim)


def render(surf, snap):
    _grid(surf)
    _hud(surf, snap)
    _field(surf, snap)
    _chart_strip(surf, snap)
    _stage(surf, snap)
    _log(surf, snap)
    _hand(surf, snap)
    _actions(surf, snap)
