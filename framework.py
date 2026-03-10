from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.text import Text

import threading
import queue
import time
import importlib

console = Console()

# Queues for the 3 top windows
window_queues = [queue.Queue(), queue.Queue(), queue.Queue()]

# Queue for terminal input
input_queue = queue.Queue()

# Shared text buffers
window_buffers = ["", "", ""]
terminal_buffer = ""


# -----------------------------
# API exposed to game scripts
# -----------------------------
def send_to_window(window_id: int, message: str):
    """Game script calls this to update one of the 3 top windows."""
    if 0 <= window_id <= 2:
        # if (window_id==1) : window_queues[window_id].clear

        # new code to clear
        if ( window_id <= 2 ):  #
            # new code to clear
            window_buffers[window_id] = ""

            while not window_queues[window_id].empty():
                try:
                    window_queues[window_id].get_nowait()
                except queue.Empty:
                    break
        # end new code 

        for l in message: 
            window_queues[window_id].put(l)


def get_input(prompt="> "):
    """Game script calls this instead of input()."""
    send_to_terminal(prompt)
    return input_queue.get()


def send_to_terminal(message: str):
    """Append text to the bottom terminal window."""
    global terminal_buffer
    terminal_buffer += message  + "\n"


# -----------------------------
# Layout creation
# -----------------------------
def build_layout():
    layout = Layout()

    # Make bottom window larger (ratio 3 vs 2)
    layout.split(
        Layout(name="top",    ratio=2),
        Layout(name="bottom", ratio=2)
    )

    # Make middle window wider (2x the width of left/right)
    layout["top"].split_row(
        Layout(name="win1", ratio=2),
        Layout(name="win2", ratio=5),
        Layout(name="win3", ratio=2)
    )

    return layout


# -----------------------------
# Rendering logic
# -----------------------------
def render_layout(layout):
    # Drain queues into buffers
    for i in range(3):
        while not window_queues[i].empty():
            msg = window_queues[i].get()
            window_buffers[i] += msg + "\n"

    layout["win1"].update(
        Panel(
            window_buffers[0],
            title="[bold white] H U M A N [/bold white]",
            border_style="bright_cyan"
        )
    )

    layout["win2"].update(
        Panel(
            window_buffers[1],
            title="[bold white] C C F [/bold white]",
            border_style="bright_magenta"
        )
    )

    layout["win3"].update(
        Panel(
            window_buffers[2],
            title="[bold white] R O B O T [/bold white]",
            border_style="bright_green"
        )
    )

    layout["bottom"].update(
        Panel(
            terminal_buffer,
            title="[bold white] A C T I O N S [/bold white]",
            border_style="yellow"
        )
    )


# -----------------------------
# Input thread (non-blocking)
# -----------------------------
def input_thread():
    global terminal_buffer
    while True:
        user_input = console.input("")
        terminal_buffer += f"> {user_input}\n"

        # -- clear q before adding new input 
        while not input_queue.empty():
            try:
                input_queue.get_nowait()
            except queue.Empty:
                break
            # input_queue.get()

        input_queue.put(user_input)


# -----------------------------
# Game loader
# -----------------------------
def run_game(game_module_name):
    game_module = importlib.import_module(game_module_name)
    game_module.run(send_to_window, get_input)


# -----------------------------
# Main loop
# -----------------------------
def main():
    layout = build_layout()

    # Start input thread
    threading.Thread(target=input_thread, daemon=True).start()

    # Start game script thread (change module name here)
    threading.Thread(target=run_game, args=("test_game",), daemon=True).start()

    # Live rendering loop
    with Live(layout, refresh_per_second=20, screen=True):
        while True:
            render_layout(layout)
            time.sleep(0.05)


if __name__ == "__main__":
    main()
