import os
import threading
import runpy
from game_window import game_window

SCRIPTS_DIR = "scripts"

def choose_script():
    files = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py")]

    print("\nChoose a script to run:")
    for i, f in enumerate(files, 1):
        print(f"{i}) {f}")

    choice = int(input("\nEnter number: "))
    return os.path.join(SCRIPTS_DIR, files[choice - 1])

def run_script(path: str):
    try:
        runpy.run_path(path, run_name="__main__")
    except Exception as e:
        print(f"Script error: {e}")

def main():
    script_path = choose_script()

    # # Start game window in its own thread
    # t1 = threading.Thread(target=game_window.run, daemon=True)
    # t1.start()

    # Run user script in main thread (so input() works)
    run_script(script_path)

if __name__ == "__main__":
    main()
