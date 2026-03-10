# Clutch Card Football

Retro college football card game built with `pygame-ce`, deployed as a native streamed session (not wasm/browser-transpiled).

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

## Deployment model (native stream)

Users open `https://ccf.norangio.dev`, click **Start Session**, and play through a streamed noVNC view of the real desktop game running on the VPS.

Runtime stack on VPS:
- `Xvfb` virtual display (`:99`)
- native `pygame` process (`ccf_pygame/game.py`)
- `x11vnc` exposing the display locally
- `websockify` + noVNC files for browser transport
- `FastAPI` launcher API/UI on `127.0.0.1:8606`
- `Caddy` reverse proxy + basic auth on `ccf.norangio.dev`

Session behavior:
- one active session at a time
- session stops automatically if the game exits
- session stops automatically after viewer disconnect (`x11vnc -once`)
- manual stop available from launcher UI

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

## Service operations

```bash
systemctl status clutch-card-football
journalctl -u clutch-card-football -f
```

Session logs:
- `/opt/clutch-card-football/logs/xvfb.log`
- `/opt/clutch-card-football/logs/game.log`
- `/opt/clutch-card-football/logs/x11vnc.log`
- `/opt/clutch-card-football/logs/websockify.log`

## Notes

- GUI field direction is team-based: human offense renders left-to-right, AI offense right-to-left.
- This deployment path prioritizes gameplay fidelity over perfect browser-native performance.
