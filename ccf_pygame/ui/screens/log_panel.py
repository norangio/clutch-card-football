"""Broadcast play-by-play log."""

from ui import draw as d
from ui.layout import LOG_RECT
from ui.theme import BORDER, DIM, GOLD, MUTED, ORANGE, PANEL, TEXT


class LogPanel:
    def draw(self, surface, snap):
        rect = LOG_RECT
        d.rrect(surface, rect, PANEL, radius=12)
        d.rrect(surface, rect, BORDER, radius=12, width=1)
        d.text(surface, "PLAY BY PLAY", (rect.x + 16, rect.y + 16),
               d.font("inter", 10, "bold"), DIM, tracking=2, tight=True)
        d.hairline(surface, rect.x + 14, rect.y + 32,
                   rect.right - 14, BORDER)

        font = d.font("inter", 11, "regular")
        rows = (rect.h - 44) // 19
        messages = snap.log_messages[-rows:]
        y = rect.y + 40
        for index, message in enumerate(messages):
            fresh = index >= len(messages) - 2
            color = TEXT if fresh else MUTED
            upper = message.upper()
            if message.startswith("==="):
                color = GOLD
            elif ("TOUCHDOWN" in upper or "CLUTCH" in upper
                  or "MOJO" in upper):
                color = ORANGE
            d.text(surface, message[:64], (rect.x + 16, y), font, color)
            y += 19
