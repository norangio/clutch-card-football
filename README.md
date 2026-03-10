# Clutch Card Football

Retro-styled college football card game built with `pygame-ce`, now deployable in desktop mode and browser mode.

## Latest upstream source included

This repo was migrated from `sorangio/CodeDev` branch `scott/pygame-ui`.
The most recent upstream update included here is commit `e217617` from **March 8, 2026 4:51:42 PM PT**.

## Run locally (desktop)

```bash
cd ccf_pygame
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 game.py
```

## Browser build (local)

```bash
python3 -m venv .venv-web
source .venv-web/bin/activate
pip install pygbag
python -m pygbag --build ccf_pygame
```

Build output:
- `ccf_pygame/build/web/index.html`

## Deploy (Hetzner + GitHub Actions)

Deploys follow the same GitHub-source-of-truth pattern as other norangio.dev apps.

### Required GitHub Actions secrets

- `VPS_HOST` (example: `5.78.109.38`)
- `VPS_USER` (example: `root`)
- `VPS_SSH_KEY` (private key content used by Actions)

### One-time VPS setup

1. Add domain A record in Cloudflare:
   - `ccf.norangio.dev -> <your-vps-ip>`
2. Add Caddy block from `deploy/Caddyfile.snippet` to `/etc/caddy/Caddyfile`
3. Reload Caddy:
   - `sudo systemctl reload caddy`

### Automatic deploy

- Push to `main` to trigger `.github/workflows/deploy.yml`
- Workflow SSHes to VPS, syncs `/opt/clutch-card-football`, runs `deploy/server-deploy.sh`
- Server script builds browser assets with `pygbag`, then restarts `clutch-card-football` systemd service

### Manual deploy

```bash
./deploy.sh
```

or for a specific branch:

```bash
./deploy.sh main
```

## Services

- App dir: `/opt/clutch-card-football`
- Service: `systemctl status clutch-card-football`
- Logs: `journalctl -u clutch-card-football -f`
- URL: `https://ccf.norangio.dev`

## Notes

- GUI field now flips direction by offense team: human offense drives left-to-right, AI offense drives right-to-left.
- Game logic is unchanged; this is a rendering-direction update only.
