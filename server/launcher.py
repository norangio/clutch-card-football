"""Single-session launcher for streaming native Pygame over noVNC."""

from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

ROOT = Path(os.environ.get("CCF_ROOT", "/opt/clutch-card-football"))
RUN_DIR = Path(os.environ.get("CCF_RUN_DIR", str(ROOT / "run")))
LOG_DIR = Path(os.environ.get("CCF_LOG_DIR", str(ROOT / "logs")))
DISPLAY = os.environ.get("CCF_DISPLAY", ":99")
VNC_PORT = int(os.environ.get("CCF_VNC_PORT", "5900"))
WS_PORT = int(os.environ.get("CCF_WS_PORT", "8605"))
NOVNC_WEB = os.environ.get("CCF_NOVNC_WEB", "/usr/share/novnc")
WS_IDLE_TIMEOUT = int(os.environ.get("CCF_WS_IDLE_TIMEOUT_SECONDS", "300"))
SESSION_TIMEOUT = int(os.environ.get("CCF_SESSION_TIMEOUT_SECONDS", "5400"))
GAME_WIDTH = int(os.environ.get("CCF_GAME_WIDTH", "1280"))
GAME_HEIGHT = int(os.environ.get("CCF_GAME_HEIGHT", "720"))
VENV_PYTHON = ROOT / "venv" / "bin" / "python"
GAME_ENTRY = ROOT / "ccf_pygame" / "game.py"
VNC_URL = "/vnc/vnc_lite.html?autoconnect=true&resize=remote&reconnect=true&view_only=false&path=websockify"


@dataclass
class SessionState:
    owner: str
    started_at: float
    processes: dict[str, subprocess.Popen]
    log_handles: list[IO[str]]
    stop_reason: str = ""


app = FastAPI(title="Clutch Card Football Launcher")
_lock = threading.Lock()
_session: SessionState | None = None


INDEX_HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Clutch Card Football</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #0b1220; color: #e2e8f0; }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
    h1 { margin: 0 0 10px; font-size: 28px; }
    p { color: #94a3b8; }
    .panel { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-top: 16px; }
    .controls { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }
    button { border: 1px solid #334155; background: #1e293b; color: #e2e8f0; padding: 10px 14px; border-radius: 8px; cursor: pointer; font-weight: 600; }
    button.primary { background: #dc2626; border-color: #dc2626; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    #status { margin-top: 12px; font-weight: 600; }
    #viewer { width: 100%; height: 72vh; border: 1px solid #334155; border-radius: 12px; display: none; margin-top: 14px; background: #020617; }
    .hint { font-size: 14px; color: #94a3b8; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Clutch Card Football (Native Stream)</h1>
    <p>This runs the original desktop game on the VPS and streams it to your browser.</p>

    <div class=\"panel\">
      <div class=\"controls\">
        <button id=\"startBtn\" class=\"primary\">Start Session</button>
        <button id=\"stopBtn\">Stop Session</button>
      </div>
      <div id=\"status\">Checking session status...</div>
      <div class=\"hint\">One active session at a time. Click once inside the game view to lock keyboard input.</div>
      <iframe id=\"viewer\" title=\"Clutch Card Football Stream\" tabindex=\"0\"></iframe>
    </div>
  </div>

  <script>
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusEl = document.getElementById('status');
    const viewer = document.getElementById('viewer');
    const vncUrl = %VNC_URL%;

    function setStatus(text, isError = false) {
      statusEl.textContent = text;
      statusEl.style.color = isError ? '#f87171' : '#e2e8f0';
    }

    function showViewer(show) {
      viewer.style.display = show ? 'block' : 'none';
      if (!show) {
        viewer.src = 'about:blank';
      }
    }

    function focusViewerInput() {
      if (viewer.style.display !== 'block') return;
      try {
        viewer.focus();
        const win = viewer.contentWindow;
        if (!win) return;
        win.focus();

        // noVNC global UI object exists in vnc_lite and can refocus RFB keyboard capture.
        if (win.UI && win.UI.rfb && typeof win.UI.rfb.focus === 'function') {
          win.UI.rfb.focus();
        }

        const doc = win.document;
        if (!doc) return;
        const canvas = doc.getElementById('noVNC_canvas');
        if (canvas) {
          canvas.tabIndex = 0;
          canvas.focus();
        } else if (doc.body) {
          doc.body.tabIndex = -1;
          doc.body.focus();
        }
      } catch (_) {
        // Keep UX stable if iframe content isn't accessible yet.
      }
    }

    async function fetchStatus() {
      const res = await fetch('/api/status', { cache: 'no-store' });
      const data = await res.json();
      if (data.running) {
        setStatus(`Running (owner: ${data.owner}, started: ${new Date(data.started_at * 1000).toLocaleTimeString()})`);
        if (!viewer.src || viewer.src === 'about:blank') {
          viewer.src = `${vncUrl}&t=${Date.now()}`;
        }
        showViewer(true);
        setTimeout(focusViewerInput, 200);
      } else {
        setStatus(data.stop_reason ? `Idle (${data.stop_reason})` : 'Idle');
        showViewer(false);
      }
      return data;
    }

    async function startSession() {
      startBtn.disabled = true;
      try {
        const res = await fetch('/api/start', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Start failed');
        }
        setStatus('Session started. Connecting viewer...');
        viewer.src = `${data.vnc_url}&t=${Date.now()}`;
        showViewer(true);
        setTimeout(focusViewerInput, 250);
      } catch (err) {
        setStatus(`Start error: ${err.message}`, true);
      } finally {
        startBtn.disabled = false;
        await fetchStatus();
      }
    }

    async function stopSession() {
      stopBtn.disabled = true;
      try {
        await fetch('/api/stop', { method: 'POST' });
      } finally {
        stopBtn.disabled = false;
        await fetchStatus();
      }
    }

    startBtn.addEventListener('click', startSession);
    stopBtn.addEventListener('click', stopSession);
    viewer.addEventListener('load', () => {
      setTimeout(focusViewerInput, 150);
      setTimeout(focusViewerInput, 700);
    });
    viewer.addEventListener('click', focusViewerInput);
    viewer.addEventListener('mouseenter', focusViewerInput);
    document.addEventListener('keydown', (event) => {
      if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
        return;
      }
      if (viewer.style.display !== 'block') {
        return;
      }
      event.preventDefault();
      focusViewerInput();
    });

    fetchStatus().catch(() => setStatus('Unable to check status', true));
    setInterval(() => { fetchStatus().catch(() => {}); }, 5000);
  </script>
</body>
</html>
""".replace("%VNC_URL%", repr(VNC_URL))


def _display_number() -> str:
    return DISPLAY.split(":")[-1].split(".")[0]


def _session_running(state: SessionState) -> bool:
    return all(proc.poll() is None for proc in state.processes.values())


def _require_command(name: str):
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command not found: {name}")


def _ensure_paths():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _wait_for_x_socket(timeout_sec: int = 8):
    x_socket = Path(f"/tmp/.X11-unix/X{_display_number()}")
    start = time.time()
    while time.time() - start < timeout_sec:
        if x_socket.exists():
            return
        time.sleep(0.2)
    raise RuntimeError(f"Xvfb did not start on {DISPLAY}")


def _open_log(name: str) -> IO[str]:
    log = open(LOG_DIR / f"{name}.log", "a", encoding="utf-8")
    log.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} start {name} ===\n")
    log.flush()
    return log


def _wait_for_tcp(host: str, port: int, timeout_sec: float = 8.0):
    deadline = time.time() + timeout_sec
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.4):
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.15)
    detail = f": {last_error}" if last_error else ""
    raise RuntimeError(f"Timed out waiting for {host}:{port}{detail}")


def _spawn(name: str, cmd: list[str], env: dict[str, str], logs: list[IO[str]]) -> subprocess.Popen:
    handle = _open_log(name)
    logs.append(handle)
    return subprocess.Popen(
        cmd,
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def _terminate_process(proc: subprocess.Popen, timeout_sec: float = 4.0):
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except Exception:
        proc.terminate()
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.1)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except Exception:
        proc.kill()


def _stop_session_locked(reason: str):
    global _session
    state = _session
    _session = None
    if state is None:
        return

    state.stop_reason = reason

    for name in ("websockify", "x11vnc", "game", "xvfb"):
        proc = state.processes.get(name)
        if proc is not None:
            _terminate_process(proc)

    for handle in state.log_handles:
        try:
            handle.write(f"=== stop: {reason} ===\n")
            handle.close()
        except Exception:
            pass


def _monitor_session(started_at: float):
    while True:
        time.sleep(1)
        with _lock:
            state = _session
            if state is None or state.started_at != started_at:
                return

            if time.time() - state.started_at > SESSION_TIMEOUT:
                _stop_session_locked("session timed out")
                return

            for name, proc in state.processes.items():
                code = proc.poll()
                if code is not None:
                    _stop_session_locked(f"{name} exited ({code})")
                    return


def _start_session_locked(owner: str) -> SessionState:
    global _session

    if _session is not None and _session_running(_session):
        return _session

    if _session is not None:
        _stop_session_locked("cleaning stale session")

    for cmd in ("Xvfb", "x11vnc", "websockify"):
        _require_command(cmd)

    if not Path(NOVNC_WEB).is_dir():
        raise RuntimeError(f"noVNC web root not found: {NOVNC_WEB}")

    if not VENV_PYTHON.exists():
        raise RuntimeError(f"Python venv missing: {VENV_PYTHON}")

    if not GAME_ENTRY.exists():
        raise RuntimeError(f"Game entrypoint missing: {GAME_ENTRY}")

    _ensure_paths()

    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    env.setdefault("SDL_AUDIODRIVER", "dummy")

    logs: list[IO[str]] = []
    procs: dict[str, subprocess.Popen] = {}

    try:
        procs["xvfb"] = _spawn(
            "xvfb",
            [
                "Xvfb",
                DISPLAY,
                "-screen",
                "0",
                f"{GAME_WIDTH}x{GAME_HEIGHT}x24",
                "-nolisten",
                "tcp",
                "-ac",
            ],
            env,
            logs,
        )
        _wait_for_x_socket()

        procs["game"] = _spawn(
            "game",
            [str(VENV_PYTHON), str(GAME_ENTRY)],
            env,
            logs,
        )

        procs["x11vnc"] = _spawn(
            "x11vnc",
            [
                "x11vnc",
                "-display",
                DISPLAY,
                "-rfbport",
                str(VNC_PORT),
                "-localhost",
                "-nopw",
                "-once",
                "-shared",
                "-quiet",
            ],
            env,
            logs,
        )
        _wait_for_tcp("127.0.0.1", VNC_PORT)

        procs["websockify"] = _spawn(
            "websockify",
            [
                "websockify",
                "--web",
                NOVNC_WEB,
                "--idle-timeout",
                str(WS_IDLE_TIMEOUT),
                f"127.0.0.1:{WS_PORT}",
                f"127.0.0.1:{VNC_PORT}",
            ],
            env,
            logs,
        )
        _wait_for_tcp("127.0.0.1", WS_PORT)

        state = SessionState(owner=owner, started_at=time.time(), processes=procs, log_handles=logs)
        _session = state

        monitor = threading.Thread(target=_monitor_session, args=(state.started_at,), daemon=True)
        monitor.start()
        return state
    except Exception:
        for proc in procs.values():
            _terminate_process(proc)
        for handle in logs:
            try:
                handle.close()
            except Exception:
                pass
        raise


def _payload(state: SessionState | None) -> dict:
    if state is None:
        return {"running": False, "stop_reason": "not running"}
    return {
        "running": _session_running(state),
        "owner": state.owner,
        "started_at": state.started_at,
        "vnc_url": VNC_URL,
        "stop_reason": state.stop_reason,
    }


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return INDEX_HTML


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.get("/api/status")
def status() -> dict:
    with _lock:
        state = _session
        if state is not None and not _session_running(state):
            _stop_session_locked("detected stopped process")
            state = _session
        return _payload(state)


@app.post("/api/start")
def start(request: Request) -> dict:
    owner = request.headers.get("x-remote-user", "authenticated-user")
    with _lock:
        try:
            state = _start_session_locked(owner)
            return _payload(state)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/stop")
def stop() -> dict:
    with _lock:
        _stop_session_locked("stopped by user")
        return {"running": False}
