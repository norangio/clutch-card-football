from time import sleep
from game_output import update_game_window

update_game_window("Starting...\n\n", font_size=16)
sleep(1)

for size in range(10, 18, 2):
    update_game_window(f"\nFont size: {size}\n" + ("@" * size), font_size=size, append=True)
    update_game_window(f"\nNext Line {size}\n", font_size=size, append=True)
    sleep(2)

input("Done. Press Enter to exit.")
