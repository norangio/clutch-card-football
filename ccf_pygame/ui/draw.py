"""Cached drawing primitives for the Broadcast presentation layer."""

import math

import pygame

from ui.fonts import font, text, text_size


def alpha(color, amount: int):
    return (color[0], color[1], color[2], amount)


def mix(c1, c2, t: float):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3))


def shade(color, t: float):
    target = (255, 255, 255) if t > 0 else (0, 0, 0)
    return mix(color, target, abs(t))


def rrect(surface, rect, color, radius=0, width=0):
    rect = pygame.Rect(rect)
    if len(color) == 4 and color[3] < 255:
        buffer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(buffer, color, buffer.get_rect(), width,
                         border_radius=radius)
        surface.blit(buffer, rect.topleft)
    else:
        pygame.draw.rect(surface, color, rect, width, border_radius=radius)
    return rect


_gradient_cache: dict[tuple, pygame.Surface] = {}
_rounded_gradient_cache: dict[tuple, pygame.Surface] = {}


def _gradient(size, c_top, c_bottom, vertical=True):
    key = (tuple(size), tuple(c_top), tuple(c_bottom), vertical)
    cached = _gradient_cache.get(key)
    if cached is not None:
        return cached

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
    result = pygame.transform.smoothscale(strip, (max(w, 1), max(h, 1)))
    _gradient_cache[key] = result
    return result


def grad_rect(surface, rect, c_top, c_bottom, radius=0, vertical=True):
    rect = pygame.Rect(rect)
    if radius:
        key = (rect.size, tuple(c_top), tuple(c_bottom), vertical, radius)
        gradient = _rounded_gradient_cache.get(key)
        if gradient is None:
            gradient = _gradient(rect.size, c_top, c_bottom, vertical).convert_alpha()
            mask = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                             border_radius=radius)
            gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            _rounded_gradient_cache[key] = gradient
    else:
        gradient = _gradient(rect.size, c_top, c_bottom, vertical)
    surface.blit(gradient, rect.topleft)
    return rect


_shadow_cache: dict[tuple, pygame.Surface] = {}
_glow_cache: dict[tuple, pygame.Surface] = {}


def shadow(surface, rect, radius=8, spread=10, a=90, offset=(0, 4)):
    rect = pygame.Rect(rect)
    key = (rect.size, radius, spread, a, (0, 0, 0))
    buffer = _shadow_cache.get(key)
    if buffer is None:
        buffer = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2),
                                pygame.SRCALPHA)
        for i in range(spread, 0, -1):
            t = i / spread
            layer_a = int(a * (1 - t) ** 2)
            if layer_a <= 0:
                continue
            layer = pygame.Rect(spread - i, spread - i,
                                rect.w + i * 2, rect.h + i * 2)
            pygame.draw.rect(buffer, (0, 0, 0, layer_a), layer,
                             border_radius=radius + i)
        _shadow_cache[key] = buffer
    surface.blit(buffer, (rect.x - spread + offset[0],
                          rect.y - spread + offset[1]))


def glow(surface, rect, color, radius=8, spread=14, a=110):
    rect = pygame.Rect(rect)
    key = (rect.size, radius, spread, a, tuple(color))
    buffer = _glow_cache.get(key)
    if buffer is None:
        buffer = pygame.Surface((rect.w + spread * 2, rect.h + spread * 2),
                                pygame.SRCALPHA)
        for i in range(spread, 0, -1):
            t = i / spread
            layer_a = int(a * (1 - t) ** 2.2)
            if layer_a <= 0:
                continue
            layer = pygame.Rect(spread - i, spread - i,
                                rect.w + i * 2, rect.h + i * 2)
            pygame.draw.rect(buffer, alpha(color, layer_a), layer, width=3,
                             border_radius=radius + i)
        _glow_cache[key] = buffer
    surface.blit(buffer, (rect.x - spread, rect.y - spread))


def hairline(surface, x1, y, x2, color):
    pygame.draw.line(surface, color, (x1, y), (x2, y))


def vline(surface, x, y1, y2, color):
    pygame.draw.line(surface, color, (x, y1), (x, y2))


def football(surface, center, w, h, fill, stroke, lace=(240, 240, 240)):
    rect = pygame.Rect(0, 0, w, h)
    rect.center = center
    pygame.draw.ellipse(surface, fill, rect)
    pygame.draw.ellipse(surface, stroke, rect, 2)
    cx, cy = center
    pygame.draw.line(surface, lace, (cx - w // 7, cy), (cx + w // 7, cy), 2)
    for off in (-w // 12, 0, w // 12):
        pygame.draw.line(surface, lace,
                         (cx + off, cy - h // 7),
                         (cx + off, cy + h // 7), 2)


def suit(surface, code, center, size, color):
    cx, cy = center
    half = size / 2.0
    if code == "D":
        pygame.draw.polygon(surface, color, [
            (cx, cy - half), (cx + half * 0.72, cy),
            (cx, cy + half), (cx - half * 0.72, cy),
        ])
    elif code == "H":
        radius = half * 0.52
        pygame.draw.circle(surface, color,
                           (int(cx - radius * 0.86), int(cy - radius * 0.42)),
                           int(radius))
        pygame.draw.circle(surface, color,
                           (int(cx + radius * 0.86), int(cy - radius * 0.42)),
                           int(radius))
        pygame.draw.polygon(surface, color, [
            (cx - half, cy - radius * 0.30),
            (cx + half, cy - radius * 0.30), (cx, cy + half),
        ])
    elif code == "S":
        radius = half * 0.50
        pygame.draw.circle(surface, color,
                           (int(cx - radius * 0.88), int(cy + radius * 0.34)),
                           int(radius))
        pygame.draw.circle(surface, color,
                           (int(cx + radius * 0.88), int(cy + radius * 0.34)),
                           int(radius))
        pygame.draw.polygon(surface, color, [
            (cx - half * 0.98, cy + radius * 0.24),
            (cx + half * 0.98, cy + radius * 0.24), (cx, cy - half),
        ])
        pygame.draw.polygon(surface, color, [
            (cx - half * 0.34, cy + half), (cx + half * 0.34, cy + half),
            (cx + half * 0.08, cy + half * 0.44),
            (cx - half * 0.08, cy + half * 0.44),
        ])
    elif code == "C":
        radius = half * 0.44
        pygame.draw.circle(surface, color,
                           (int(cx), int(cy - half * 0.42)), int(radius))
        pygame.draw.circle(surface, color,
                           (int(cx - radius * 1.42), int(cy + half * 0.20)),
                           int(radius))
        pygame.draw.circle(surface, color,
                           (int(cx + radius * 1.42), int(cy + half * 0.20)),
                           int(radius))
        pygame.draw.polygon(surface, color, [
            (cx - half * 0.42, cy + half), (cx + half * 0.42, cy + half),
            (cx + half * 0.10, cy + half * 0.16),
            (cx - half * 0.10, cy + half * 0.16),
        ])


def star(surface, center, r_out, color, points=5):
    cx, cy = center
    vertices = []
    for i in range(points * 2):
        radius = r_out if i % 2 == 0 else r_out * 0.45
        angle = -math.pi / 2 + i * math.pi / points
        vertices.append((cx + radius * math.cos(angle),
                         cy + radius * math.sin(angle)))
    pygame.draw.polygon(surface, color, vertices)


def chevron(surface, x, y, size, color, direction=1, width=3):
    pygame.draw.lines(surface, color, False, [
        (x, y - size), (x + size * direction, y), (x, y + size),
    ], width)
