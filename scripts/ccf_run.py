import time
import random
import sys
from numpy import roll

# from py_games.CCF.py_ccf_deal import Color
# from python.ccf_gui.framework import get_input 

# from  scripts.grok_ccf import *  

import scripts.grok_ccf as GrokCCF

def input_int(self, prompt: str, min_v: int, max_v: int) -> int:
    while True:
        try:
            v = int(input(prompt))
            if min_v <= v <= max_v: return v
            if v==0: exit()
            print(f"Enter {min_v}–{max_v}")
        except: print("Invalid")

def prompt(self, msg: str):
    print(f">>> {msg}")
    input("[Enter]")

def run(send_to_window, get_input):
  
    ht_name   = get_input("Human Team Name ")
    ht_drate  = get_input("Your drive rating (1-12): "),
    ht_krate  = get_input("Your kick  rating (1-3): "),
    ht_clutch = get_input("Starting clutch (0-5): "),
    ht_mojo   = 0

    rt_name   = get_input("Robot Team Name ")
    rt_drate  = get_input("Robot drive rating (1-12): "),
    rt_krate  = get_input("Robot kick  rating (1-3): "),
    rt_clutch = get_input("Robot clutch (0-5): "),
    rt_mojo   = 0

    ccf_info = {
        "human_team_name": ht_name,
        "human_drive_rating": int(ht_drate),
        "human_kick_rating": int(ht_krate),
        "human_starting_clutch": int(ht_clutch),
        "human_mojo": ht_mojo,
        "robot_team_name": rt_name,
        "robot_drive_rating": int(rt_drate),
        "robot_kick_rating": int(rt_krate),
        "robot_starting_clutch": int(rt_clutch),
        "robot_mojo": rt_mojo,
    }

    send_to_window(0,"Windo0")
    send_to_window(1,"Windo1")
    send_to_window(2,"Windo2 ♠️")
    time.sleep(1)

    while True:
        boogers   = get_input("boiogers")

    # game_on = True
    # while (game_on):

    #   game = GrokCCF.Game()

    #   game.start ( ccf_info, send_to_window, get_input ) 

    #   game_on = ( get_input("Play again? (y/n) ").lower() == "y" )

    