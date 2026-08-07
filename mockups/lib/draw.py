"""Shared drawing helpers for the CCF UI mockups.

Pure presentation utilities — no game logic lives here. Everything is plain
pygame surface work, so anything a mockup draws can move straight into
``ccf_pygame/ui/`` once a direction is picked.
"""

import os
import pygame

FONTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts"
)

# family -> weight -> filename
_FAMILIES = {
    "inter": {
        "regular": "Inter-Regular.ttf",
        "medium": "Inter-Medium.ttf",
        "semibold": "Inter-SemiBold.ttf",
        "bold": "Inter-Bold.ttf",
    },
    "cond": {
        "regular": "BarlowCondensed-Regular.ttf",
        "medium": "BarlowCondensed-SemiBold.ttf",
        "semibold": "BarlowCondensed-SemiBold.ttf",
        "bold": "BarlowCondensed-Bold.ttf",
    },
}

_font_cache: dict[tuple, pygame.font.Font] = {}


def font(family: str = "inter", size: int = 14, weight: str = "regular") -> pygame.font.Font:
    key = (family, size, weight)
    if key in _font_cache:
        return _font_cache[key]
    fname = _FAMILIES.get(family, _FAMILIES["inter"]).get(weight, "Inter-Regular.ttf")
    path = os.path.join(FONTS_DIR, fname)
    f = pygame.font.Font(path if os.path.exists(path) else None, size)
    _font_cache[key] = f
    return f


# --- colour utilities -------------------------------------------------------

def alpha(color, a: int):
    """Return ``color`` with an explicit alpha channel."""
    return (color[0], color[1], color[2], a)


def mix(c1, c2, t: float):
    """Linear blend between two RGB colours; t=0 gives c1, t=1 gives c2."""
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3))


def shade(color, t: float):
    """Darken (t<0) or lighten (t>0) a colour by a fraction."""
    target = (255, 255, 255) if t > 0 else (0, 0, 0)
    return mix(color, target, abs(t))


# --- text -------------------------------------------------------------------

def _render_text(s: str, f: pygame.font.Font, color, tracking: int) -> pygame.Surface:
    """Render ``s``, applying per-character tracking when asked.

    Tracking has to lay glyphs out by hand (pygame has no letter-spacing), so
    the buffer is measured from the same per-character advances used to draw —
    measuring with the kerned whole-string width clips the last glyph.
    """
    if not tracking:
        return f.render(s, True, color)

    adv = [f.size(ch)[0] for ch in s]
    w = sum(adv) + tracking * max(0, len(s) - 1)
    buf = pygame.Surface((max(w, 1), f.get_height()), pygame.SRCALPHA)
    cx = 0
    for ch, a in zip(s, adv):
        buf.blit(f.render(ch, True, color), (cx, 0))
        cx += a + tracking
    return buf


def text_size(s: str, f: pygame.font.Font, tracking: int = 0, tight=False) -> tuple[int, int]:
    if not s:
        return (0, 0 if tight else f.get_height())
    surf = _render_text(str(s), f, (255, 255, 255), tracking)
    if tight:
        bb = surf.get_bounding_rect()
        return (bb.w, bb.h)
    return surf.get_size()


def text(surface, s, pos, f, color, anchor="topleft", tracking=0, tight=False):
    """Draw ``s`` and return its bounding rect.

    ``tight=True`` crops the glyph box to its inked pixels before anchoring.
    The mockups mix Inter with Barlow Condensed, whose line boxes have very
    different leading, so tight anchoring is the only way to get optical
    centring that holds across both families.
    """
    s = "" if s is None else str(s)
    surf = _render_text(s, f, color, tracking)

    if tight:
        bb = surf.get_bounding_rect()
        if bb.w and bb.h:
            surf = surf.subsurface(bb).copy()

    rect = surf.get_rect(**{anchor: pos})
    surface.blit(surf, rect)
    return rect


# --- shapes -----------------------------------------------------------------

def rrect(surface, rect, color, radius=0, width=0):
    """Rounded rectangle, filled or stroked. Supports RGBA colours."""
    rect = pygame.Rect(rect)
    if len(color) == 4 and color[3] < 255:
        buf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(buf, color, buf.get_rect(), width, border_radius=radius)
        surface.blit(buf, rect.topleft)
    else:
        pygame.draw.rect(surface, color, rect, width, border_radius=radius)
    return rect


def _gradient(size, c_top, c_bottom, vertical=True):
    """Small gradient strip scaled up — cheap and smooth."""
    w, h = size
    if vertical:
        strip = pygame.Surface((1, max(h, 2)))
        for y in range(max(h, 2)):
            t = y / max(1, max(h, 2) - 1)
            strip.set_at((0, y), mix(c_top, c_bottom, t))
    else:
        strip = pygame.Surface((max(w, 2), 1))
        for x in range(max(w, 2)):
            t = x / max(1, max(w, 2) - 1)
            strip.set_at((x, 0), mix(c_top, c_bottom, t))
    return pygame.transform.smoothscale(strip, (max(w, 1), max(h, 1)))


def grad_rect(surface, rect, c_top, c_bottom, radius=0, vertical=True):
    """Gradient-filled rectangle, optionally with rounded corners."""
    rect = pygame.Rect(rect)
    g = _gradient(rect.size, c_top, c_bottom, vertical).convert_alpha()
    if radius:
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        g.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(g, rect.topleft)
    return rect


def shadow(surface, rect, radius=8, spread=10, a=90, offset=(0, 4)):
    """Soft drop shadow built from stacked translucent rounded rects."""
    rect = pygame.Rect(rect)
    buf = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
    for i in range(spread, 0, -1):
        t = i / spread
        layer_a = int(a * (1 - t) ** 2)
        if layer_a <= 0:
            continue
        r = pygame.Rect(spread - i, spread - i, rect.w + i * 2, rect.h + i * 2)
        pygame.draw.rect(buf, (0, 0, 0, layer_a), r, border_radius=radius + i)
    surface.blit(buf, (rect.x - spread + offset[0], rect.y - spread + offset[1]))


def glow(surface, rect, color, radius=8, spread=14, a=110):
    """Coloured outer halo — the neon theme's main depth cue.

    Drawn as expanding *rings* rather than filled rects: stacked fills build up
    to a near-opaque slab over the interior, which washes out anything the
    caller paints inside afterwards.
    """
    rect = pygame.Rect(rect)
    buf = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2), pygame.SRCALPHA)
    for i in range(spread, 0, -1):
        t = i / spread
        layer_a = int(a * (1 - t) ** 2.2)
        if layer_a <= 0:
            continue
        r = pygame.Rect(spread - i, spread - i, rect.w + i * 2, rect.h + i * 2)
        pygame.draw.rect(buf, alpha(color, layer_a), r, width=3,
                         border_radius=radius + i)
    surface.blit(buf, (rect.x - spread, rect.y - spread))


def hairline(surface, x1, y, x2, color):
    pygame.draw.line(surface, color, (x1, y), (x2, y))


def vline(surface, x, y1, y2, color):
    pygame.draw.line(surface, color, (x, y1), (x, y2))


def football(surface, center, w, h, fill, stroke, lace=(240, 240, 240)):
    """Draw a football marker with laces."""
    r = pygame.Rect(0, 0, w, h)
    r.center = center
    pygame.draw.ellipse(surface, fill, r)
    pygame.draw.ellipse(surface, stroke, r, 2)
    cx, cy = center
    pygame.draw.line(surface, lace, (cx - w // 7, cy), (cx + w // 7, cy), 2)
    for off in (-w // 12, 0, w // 12):
        pygame.draw.line(surface, lace, (cx + off, cy - h // 7), (cx + off, cy + h // 7), 2)


def suit(surface, code, center, size, color):
    """Draw a card suit as vector art.

    Drawn rather than typeset so the pips stay crisp at the small sizes the
    hand uses, and so we never depend on a font shipping U+2660..U+2663.
    """
    cx, cy = center
    s = size / 2.0

    if code == "D":
        pygame.draw.polygon(surface, color, [
            (cx, cy - s), (cx + s * 0.72, cy), (cx, cy + s), (cx - s * 0.72, cy),
        ])

    elif code == "H":
        r = s * 0.52
        pygame.draw.circle(surface, color, (int(cx - r * 0.86), int(cy - r * 0.42)), int(r))
        pygame.draw.circle(surface, color, (int(cx + r * 0.86), int(cy - r * 0.42)), int(r))
        pygame.draw.polygon(surface, color, [
            (cx - s, cy - r * 0.30), (cx + s, cy - r * 0.30), (cx, cy + s),
        ])

    elif code == "S":
        r = s * 0.50
        pygame.draw.circle(surface, color, (int(cx - r * 0.88), int(cy + r * 0.34)), int(r))
        pygame.draw.circle(surface, color, (int(cx + r * 0.88), int(cy + r * 0.34)), int(r))
        pygame.draw.polygon(surface, color, [
            (cx - s * 0.98, cy + r * 0.24), (cx + s * 0.98, cy + r * 0.24), (cx, cy - s),
        ])
        pygame.draw.polygon(surface, color, [
            (cx - s * 0.34, cy + s), (cx + s * 0.34, cy + s),
            (cx + s * 0.08, cy + s * 0.44), (cx - s * 0.08, cy + s * 0.44),
        ])

    elif code == "C":
        r = s * 0.44
        pygame.draw.circle(surface, color, (int(cx), int(cy - s * 0.42)), int(r))
        pygame.draw.circle(surface, color, (int(cx - r * 1.42), int(cy + s * 0.20)), int(r))
        pygame.draw.circle(surface, color, (int(cx + r * 1.42), int(cy + s * 0.20)), int(r))
        pygame.draw.polygon(surface, color, [
            (cx - s * 0.42, cy + s), (cx + s * 0.42, cy + s),
            (cx + s * 0.10, cy + s * 0.16), (cx - s * 0.10, cy + s * 0.16),
        ])


def star(surface, center, r_out, color, points=5):
    """Small star — used for clutch pips."""
    import math
    cx, cy = center
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_out * 0.45
        a = -math.pi / 2 + i * math.pi / points
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(surface, color, pts)


def chevron(surface, x, y, size, color, direction=1, width=3):
    """Directional chevron; direction 1 points right, -1 points left."""
    pygame.draw.lines(
        surface, color, False,
        [(x, y - size), (x + size * direction, y), (x, y + size)],
        width,
    )
