"""Antialiased Broadcast font loading and tightly anchored text."""

from pathlib import Path

import pygame

FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"

_FAMILIES = {
    "inter": {
        "regular": "Inter-Regular.ttf",
        "medium": "Inter-SemiBold.ttf",
        "semibold": "Inter-SemiBold.ttf",
        "bold": "Inter-Bold.ttf",
    },
    "cond": {
        "regular": "BarlowCondensed-Bold.ttf",
        "medium": "BarlowCondensed-Bold.ttf",
        "semibold": "BarlowCondensed-Bold.ttf",
        "bold": "BarlowCondensed-Bold.ttf",
    },
}

_font_cache: dict[tuple[str, int, str], pygame.font.Font] = {}
_font_meta: dict[int, tuple[str, int, str]] = {}
_text_cache: dict[tuple, pygame.Surface] = {}


def font(family: str = "inter", size: int = 14,
         weight: str = "regular") -> pygame.font.Font:
    key = (family, size, weight)
    if key not in _font_cache:
        family_files = _FAMILIES.get(family, _FAMILIES["inter"])
        filename = family_files.get(weight, family_files["regular"])
        path = FONTS_DIR / filename
        loaded = pygame.font.Font(str(path) if path.exists() else None, size)
        _font_cache[key] = loaded
        _font_meta[id(loaded)] = key
    return _font_cache[key]


def _render_text(value: str, f: pygame.font.Font, color,
                 tracking: int = 0) -> pygame.Surface:
    """Render with tracking measured from the same advances used to draw."""
    value = str(value)
    family, size, weight = _font_meta.get(
        id(f), ("inter", max(1, f.get_height()), "regular")
    )
    fallback = font("inter", size, weight)

    glyph_fonts = []
    used_fallback = False
    for char in value:
        metrics = f.metrics(char)[0]
        missing_ink = (not char.isspace() and metrics is not None
                       and metrics[:4] == (0, 0, 0, 0))
        glyph_font = fallback if missing_ink and family != "inter" else f
        used_fallback = used_fallback or glyph_font is not f
        glyph_fonts.append(glyph_font)

    if not tracking and not used_fallback:
        return f.render(value, True, color)

    advances = [glyph_font.size(char)[0]
                for char, glyph_font in zip(value, glyph_fonts)]
    width = sum(advances) + tracking * max(0, len(value) - 1)
    height = max([f.get_height(), *(glyph_font.get_height()
                                    for glyph_font in glyph_fonts)])
    result = pygame.Surface((max(width, 1), height), pygame.SRCALPHA)
    x = 0
    for char, glyph_font, advance in zip(value, glyph_fonts, advances):
        result.blit(glyph_font.render(char, True, color), (x, 0))
        x += advance + tracking
    return result


def rendered(value, f: pygame.font.Font, color, tracking: int = 0,
             tight: bool = False) -> pygame.Surface:
    """Return a cached antialiased text surface."""
    value = "" if value is None else str(value)
    key = (id(f), value, tuple(color), tracking, tight)
    cached = _text_cache.get(key)
    if cached is not None:
        return cached

    result = _render_text(value, f, color, tracking)
    if tight:
        bounds = result.get_bounding_rect()
        if bounds.w and bounds.h:
            result = result.subsurface(bounds).copy()
    _text_cache[key] = result
    return result


def text_size(value, f: pygame.font.Font, tracking: int = 0,
              tight: bool = False) -> tuple[int, int]:
    if not value:
        return (0, 0 if tight else f.get_height())
    return rendered(value, f, (255, 255, 255), tracking, tight).get_size()


def text(surface: pygame.Surface, value, pos, f: pygame.font.Font, color,
         anchor: str = "topleft", tracking: int = 0, tight: bool = False):
    glyphs = rendered(value, f, color, tracking, tight)
    rect = glyphs.get_rect(**{anchor: pos})
    surface.blit(glyphs, rect)
    return rect
