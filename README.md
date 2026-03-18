# Clutch Card Football

Retro college football card game built with `pygame-ce`. The repo now supports both the native desktop runtime and a browser-native wasm build via `pygbag`.

## Latest upstream source included

This repo was migrated from `sorangio/CodeDev` branch `scott/pygame-ui`.
The most recent upstream update included here is commit `e217617` from **March 8, 2026 4:51:42 PM PT**.

## Local development (desktop game)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-desktop.txt
python3 ccf_pygame/game.py
```

## Local development (browser build with pygbag)

Official `pygbag` docs currently require a root `main.py` with an async game loop, and the latest PyPI release is `0.9.3` from February 12, 2026.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-desktop.txt
pip install "pygbag>=0.9.3,<1"
python3 -m pygbag --ume_block 0 ccf_pygame
```

Build artifacts are emitted under `ccf_pygame/build/web/`. For a build-only pass:

```bash
./scripts/build_browser.sh
```

Browser runtime notes:
- `ccf_pygame/main.py` is the wasm/browser entrypoint packaged by `pygbag`
- `ccf_pygame/ui/app.py` now exposes a shared async-safe loop for desktop and browser runs
- Production uses the embedded `pygbag --html` build and copies `ccf_pygame.html` to `index.html`
- CRT post-processing is disabled in browser mode by default to preserve frame budget
- Audio initialization is best-effort so the game still runs if the browser blocks mixer startup
- Browser builds use `--ume_block 0` so the setup screen can render immediately without a preload click gate

## Production deployment (browser-native)

Users open `https://ccf.norangio.dev` and load the static `pygbag` bundle directly in the browser.

Runtime stack on VPS:
- `pygbag` embedded HTML build step on deploy (`ccf_pygame/build/web/`)
- static `index.html` served directly by `Caddy`
- `Caddy` basic auth on `ccf.norangio.dev`
- runtime JS/wasm loaded from the official `pygame-web.github.io` CDN referenced by the generated `index.html`

Behavior note:
- there is no remote desktop session anymore; the game logic and rendering now execute in-browser via wasm

## Deploy (Hetzner + GitHub Actions)

Push to `main` to auto-deploy.

### Required GitHub Actions secrets

- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`

### One-time VPS setup

1. Add DNS A record in Cloudflare:
   - `ccf.norangio.dev -> <your-vps-ip>`
2. Add Caddy block from `deploy/Caddyfile.snippet` to `/etc/caddy/Caddyfile`
3. Reload Caddy:
   - `sudo systemctl reload caddy`

### Manual deploy

```bash
./deploy.sh
# or
./deploy.sh main
```

## Build operations

```bash
./scripts/build_browser.sh
```

Built assets:
- `/opt/clutch-card-football/ccf_pygame/build/web/index.html`
- `/opt/clutch-card-football/ccf_pygame/build/web/ccf_pygame.html`

## Notes

- GUI field direction is team-based: human offense renders left-to-right, AI offense right-to-left.
- Current control mode is mouse-first for browser reliability.
- Keyboard entry is kept for team-name text fields only during setup.
- Production no longer relies on Xvfb, x11vnc, or noVNC.

## Security TODO

- Move all app deploy workflows to a dedicated non-root VPS user.
- Use one dedicated GitHub Actions deploy keypair only (not personal workstation keys).
- After migration, remove deploy access from `root` and disable root SSH login.
