# Clutch Card Football — Project Notes

## Architecture

- `ccf_pygame/ccf/` contains pure game logic (rules, state machine, deck, drive chart)
- `ccf_pygame/ui/` contains Pygame rendering and interaction
- `ccf_pygame/game.py` is the native desktop entrypoint
- `server/launcher.py` is a FastAPI launcher for streamed sessions
- `requirements-desktop.txt` contains game runtime dependencies
- `requirements-server.txt` contains launcher API dependencies

## Native stream deployment model

- The launcher service runs on `127.0.0.1:8606`
- On session start, launcher starts:
  - `Xvfb` on `:99`
  - native `pygame` game process
  - `x11vnc` on `127.0.0.1:5900` (`-once`)
  - `websockify` on `127.0.0.1:8605` (serves noVNC static + websocket bridge)
- Launcher blocks `start` response until `x11vnc` and `websockify` listener ports are reachable.
- Launcher embeds `/vnc/vnc_lite.html` and aggressively refocuses viewer keyboard capture.
- `vnc_lite` URL params must avoid `view_only=false` (string coercion in lite mode can disable keyboard/mouse input).
- Caddy routes (inside an ordered `route { ... }` block):
  - `/websockify*` -> `127.0.0.1:8605` (before basic auth for reliable websocket upgrade)
  - basic auth applies to launcher UI/API and `/vnc/*`
  - `/vnc/*` -> `127.0.0.1:8605`
  - all other paths -> `127.0.0.1:8606`

## Session lifecycle rules

- One active stream session at a time.
- Launcher monitor thread shuts down all subprocesses when any session subprocess exits.
- Viewer disconnect triggers `x11vnc -once` exit, which tears down the session.
- Session timeout defaults to 90 minutes (`CCF_SESSION_TIMEOUT_SECONDS`).
- Websocket bridge idle timeout defaults to 5 minutes (`CCF_WS_IDLE_TIMEOUT_SECONDS`).

## Gameplay/UI conventions

- Visual field direction is offense-team based:
  - human offense: left-to-right
  - AI offense: right-to-left
- Stream input is mouse-first for game flow (card selection, decisions, continue screens).
- Keyboard input is reserved for setup text entry (team names) to avoid key-focus flakiness.
- Core game rules and scoring logic are unchanged.

## TODO (security hardening)

- Migrate deploy SSH access to a dedicated non-root VPS user across all apps.
- Keep one dedicated deploy keypair for GitHub Actions only (no personal key reuse).
- Remove deploy key(s) from `root` and disable root SSH login after migration verification.
