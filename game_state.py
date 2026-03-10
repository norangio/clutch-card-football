import time
import sys

def run(send_to_window, get_input):
    send_to_window(0, "🌄 Welcome to the game!")
    send_to_window(1, "⚙ Game engine warming up…")
    send_to_window(2, "📜 Status window ready.")

    time.sleep(1)

    name = get_input("Enter ball Positions")
    send_to_window(1," 🥅🥅🥅🥅 ")

    while True:
        cmd = get_input("Next Postion > ")

        if cmd.lower() == "quit":
            send_to_window(1, "Shutting down…")
            sys.exit()

        # send_to_window(2, f"You typed: {cmd}")
        time.sleep(0.1)
