# Clutch Card Football — Project Notes

## Architecture

- `ccf_pygame/ccf/` contains pure game logic (rules, state machine, deck, drive chart)
- `ccf_pygame/ui/` contains Pygame rendering and interaction
- `ccf_pygame/game.py` is the native desktop entrypoint
- `ccf_pygame/main.py` is the browser/wasm entrypoint for `pygbag`
- `server/launcher.py` is a FastAPI launcher for streamed sessions
- `requirements-desktop.txt` contains game runtime dependencies
- `requirements-server.txt` contains launcher API dependencies

## Browser build (working)

- Build command: `./.venv-build/bin/python -m pygbag --build --archive --ume_block 0 --width 960 --height 720 --title "Clutch Card Football" ccf_pygame`
- Local test: pygbag's test server is required for local testing (it proxies CDN wheel downloads). Use the same command without `--build --archive` to start the dev server on port 8000.
- The `--html` flag should NOT be used — it produces incorrect embedded output.
- `ccf_pygame/requirements.txt` must NOT list `pygame-ce` (it's bundled in the WASM runtime; listing it causes a failed wheel fetch from localhost:8000 proxy).
- Desktop deps go in `requirements-desktop.txt` at repo root.

## Root causes of prior blank-gray-canvas bug

1. **Framebuffer mismatch**: pygbag defaulted to 1280x720 but the game uses 960x720. Fix: `--width 960 --height 720`.
2. **pygame-ce wheel fetch failure**: The `requirements.txt` listing `pygame-ce` caused the WASM runtime to try downloading the wheel from pygbag's localhost:8000 proxy, which doesn't exist in production. Without the wheel, `pygame.display` was unavailable. Fix: removed `pygame-ce` from in-package requirements.
3. **pygame.init() unavailable at top level in WASM**: The pygbag WASM build doesn't expose `pygame.init` directly. Fix: `main.py` runs a compat shim (backfilling submodules via `importlib`) before calling init.

## Browser architecture

- `main.py` handles all WASM-specific concerns: pygame compat shims, module-level init, error overlay DOM injection, and the async game loop.
- `app.py` accepts a pre-created `_screen` surface in browser mode (pygame init + `set_mode` done by main.py at module level, before async).
- Desktop path (`game.py`) is unchanged — `PygameApp()` handles full init internally.
- CRT effect and audio are disabled in browser mode by default.
- `from __future__ import annotations` across UI modules prevents eager `pygame.Surface`/`pygame.Rect` resolution at import time.
- `ccf_pygame/ui/keycodes.py` provides fallback key constants for WASM where `pygame.K_*` may not be available.

## Gameplay/UI conventions

- Visual field direction is offense-team based:
  - human offense: left-to-right
  - AI offense: right-to-left
- Browser input is mouse-first for game flow (card selection, decisions, continue screens).
- Keyboard input is reserved for setup text entry (team names) to avoid key-focus flakiness.
- Core game rules and scoring logic are unchanged.

## TODO (security hardening)

- Migrate deploy SSH access to a dedicated non-root VPS user across all apps.
- Keep one dedicated deploy keypair for GitHub Actions only (no personal key reuse).
- Remove deploy key(s) from `root` and disable root SSH login after migration verification.
