"""Retro 8-bit synthesized sounds using stdlib array (no numpy required)."""

import array
import math
import pygame

_SAMPLE_RATE = 44100
_sounds: dict = {}
_initialized = False


def _make_tone(freq: float, duration_ms: int, volume: float = 0.25) -> pygame.mixer.Sound:
    """Generate a square-wave tone as a pygame Sound (stereo 16-bit)."""
    n_samples = int(_SAMPLE_RATE * duration_ms / 1000)
    buf = array.array('h', [0] * (n_samples * 2))  # stereo interleaved
    peak = int(volume * 32767)
    for i in range(n_samples):
        t = i / _SAMPLE_RATE
        val = peak if math.sin(2 * math.pi * freq * t) >= 0 else -peak
        buf[i * 2] = val      # left channel
        buf[i * 2 + 1] = val  # right channel
    return pygame.mixer.Sound(buffer=buf)


def _concat_tones(notes: list[tuple[float, int]], volume: float = 0.25) -> pygame.mixer.Sound:
    """Concatenate multiple (freq, duration_ms) notes into one Sound."""
    combined = array.array('h')
    peak = int(volume * 32767)
    for freq, dur_ms in notes:
        n_samples = int(_SAMPLE_RATE * dur_ms / 1000)
        for i in range(n_samples):
            t = i / _SAMPLE_RATE
            val = peak if math.sin(2 * math.pi * freq * t) >= 0 else -peak
            combined.append(val)   # left
            combined.append(val)   # right
    return pygame.mixer.Sound(buffer=combined)


def init_sounds():
    """Initialize all sound effects. Call after pygame.mixer.init()."""
    global _initialized, _sounds
    if _initialized:
        return

    # Note frequencies
    C5  = 523.25
    D5  = 587.33
    E5  = 659.25
    G5  = 783.99
    C6  = 1046.50

    try:
        _sounds["first_down"] = _concat_tones([(C5, 120), (E5, 120)])
        _sounds["touchdown"]  = _concat_tones([(C5, 150), (E5, 150), (G5, 150), (C6, 150)])
        _sounds["field_goal"] = _concat_tones([(E5, 150), (G5, 150)])
        _sounds["win"]        = _concat_tones([(C5, 200), (D5, 200), (E5, 200), (G5, 200), (C6, 200)])
    except Exception as e:
        print(f"[sounds] Failed to generate sounds: {e}")

    _initialized = True


def play(name: str):
    """Play a named sound effect if available."""
    if not _initialized:
        return
    sound = _sounds.get(name)
    if sound:
        sound.play()
