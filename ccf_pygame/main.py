#!/usr/bin/env python3
"""Browser entrypoint for pygbag.

Pygbag expects:
  1. pygame init + display.set_mode at module level (synchronous)
  2. An async main() with `await asyncio.sleep(0)` in the loop
  3. asyncio.run(main()) at module level
"""

import asyncio
import sys
import os
import traceback

# --- status / error overlay helpers (DOM manipulation in WASM) -----------

def _set_status(message: str):
    print(f"[ccf] {message}")
    try:
        import platform
        doc = platform.document
        badge = doc.getElementById("ccf-status")
        if badge is None:
            badge = doc.createElement("pre")
            badge.id = "ccf-status"
            badge.style.position = "fixed"
            badge.style.top = "8px"
            badge.style.left = "8px"
            badge.style.zIndex = "999999"
            badge.style.maxWidth = "90vw"
            badge.style.padding = "8px 12px"
            badge.style.background = "rgba(0,0,0,0.85)"
            badge.style.color = "#0f0"
            badge.style.font = "13px/1.3 monospace"
            badge.style.whiteSpace = "pre-wrap"
            doc.body.appendChild(badge)
        badge.innerText = message
    except Exception:
        pass


def _show_error(details: str):
    print(details)
    try:
        import platform
        doc = platform.document
        overlay = doc.getElementById("ccf-error")
        if overlay is None:
            overlay = doc.createElement("pre")
            overlay.id = "ccf-error"
            overlay.style.position = "fixed"
            overlay.style.top = "8px"
            overlay.style.left = "8px"
            overlay.style.zIndex = "1000000"
            overlay.style.maxWidth = "90vw"
            overlay.style.maxHeight = "90vh"
            overlay.style.overflow = "auto"
            overlay.style.padding = "10px 14px"
            overlay.style.background = "#200"
            overlay.style.color = "#fcc"
            overlay.style.font = "13px/1.3 monospace"
            overlay.style.whiteSpace = "pre-wrap"
            doc.body.appendChild(overlay)
        overlay.innerText = details[-2000:]
    except Exception:
        pass


def _clear_status():
    try:
        import platform
        doc = platform.document
        badge = doc.getElementById("ccf-status")
        if badge:
            badge.remove()
    except Exception:
        pass


# --- module-level pygame init (synchronous, before async main) -----------

_set_status("importing pygame")

try:
    # Ensure package root is on sys.path (pygbag extracts to assets/)
    _pkg_root = os.path.dirname(os.path.abspath(__file__))
    if _pkg_root not in sys.path:
        sys.path.insert(0, _pkg_root)

    import importlib
    import pygame

    # Backfill pygame submodules/attrs that may not be top-level in WASM builds
    for attr, mod in (
        ("display", "pygame.display"), ("draw", "pygame.draw"),
        ("event", "pygame.event"), ("font", "pygame.font"),
        ("key", "pygame.key"), ("mixer", "pygame.mixer"),
        ("time", "pygame.time"),
    ):
        if not hasattr(pygame, attr):
            try:
                setattr(pygame, attr, importlib.import_module(mod))
            except Exception:
                pass

    for attr, (mod, name) in (
        ("init", ("pygame.base", "init")), ("quit", ("pygame.base", "quit")),
        ("Surface", ("pygame.surface", "Surface")),
        ("Rect", ("pygame.rect", "Rect")),
        ("Color", ("pygame.color", "Color")),
    ):
        if not hasattr(pygame, attr):
            try:
                setattr(pygame, attr, getattr(importlib.import_module(mod), name))
            except Exception:
                pass

    # Init pygame — try top-level init, fall back to per-module init
    _set_status("pygame init")
    init_fn = getattr(pygame, "init", None)
    if callable(init_fn):
        init_fn()
    else:
        for sub in ("display", "font"):
            m = getattr(pygame, sub, None)
            if m and hasattr(m, "init"):
                m.init()

    _set_status("display.set_mode(960x720)")
    screen = pygame.display.set_mode((960, 720), 0)
    pygame.display.set_caption("Clutch Card Football")

    _set_status("importing app")
    from ui.app import PygameApp

    _set_status("constructing app")
    app = PygameApp(browser_mode=True, _screen=screen)

except Exception:
    _show_error(traceback.format_exc())
    app = None


# --- async main loop ----------------------------------------------------

async def main():
    if app is None:
        _set_status("app failed to initialize — see error overlay")
        while True:
            await asyncio.sleep(1)

    _set_status("entering game loop")
    _clear_status()

    try:
        while app.running:
            app.tick()
            await asyncio.sleep(0)
    except Exception:
        _show_error(traceback.format_exc())
        while True:
            await asyncio.sleep(1)


asyncio.run(main())
