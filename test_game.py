
import time
import random
import sys 

HUMAN_TEAM_INFO = [
    "Team: htname  👱 ",
    "Rate: hr",
    "Kick: hk",
    "",
    "         D R I V R         ",
    " 2 3 4 5 6 7 8 9 10 J Q K A",
    " ==========================",
    "-1 0 1 1 2 2 3 2  3 3 3 4 4 ",
    "",
    "",
    "",
    "",
    "",
    "",
    "Clutch Coin  [hcoin]                     H_COIN ",
    " ",
    "Mojo Fire    [hfire]                     H_FIRE "

]

ROBOT_TEAM_INFO = [
    "Team: rtname 🐻",
    "Rate: rr",
    "Kick: rk",
    "",
    "         D R I V R         ",
    " 2 3 4 5 6 7 8 9 10 J Q K A",
    " ==========================",
    "-1 0 1 1 2 2 3 2  3 3 3 4 4 ",
    "",
    "",
    "",
    "",
    "",
    "",
    "Clutch Coin  [rcoin]                       R_COIN ",
    " ",
    "Mojo Fire    [rfire]                       R_FIRE "
]

CCF_INFO = ["🏈🏈 CCF 🏈🏈"  ]

CLUTCH_COIN = { 0: " ✖️               ",
                1: " 🏆               ",
                2: " 🏆 🏆            ",
                3: " 🏆 🏆 🏆         ",
                4: " 🏆 🏆 🏆 🏆     ",
                5: " 🏆 🏆 🏆 🏆 🏆  ",
               }

MOJO_FIRE   = { 0: " ✖️               ",
                1: " 🔥               ",
                2: " 🔥 🔥            ",
                3: " 🔥 🔥 🔥         ",
                4: " 🔥 🔥 🔥 🔥     ",
                5: " 🔥 🔥 🔥 🔥 🔥  ",
               }

MESSAGES = [
    "Player moved north 🧭",
    "Enemy spotted 👹",
    "Treasure found 💰",
    "Health restored ❤️",
    "New quest available 📜",
    "Weather changing… 🌧",
    "Inventory updated 🎒",
    "Level up! ⭐",
]

CCF_MESSAGES =  [ "Type 'quit' to stop the test."] 

CCF_FIELD = [
            "     C L U T C H   C A R D        ♦️ ♠️ ❤️ ♣️     F O O T B A L L       ",
            "                                                                         ",
            "                               ---> 🟥🟥🟥  --->                        ",
            "                                                                         ",
            "    | ===== | ==== 1|  ==== 2| ==== 3|  ====Z3|  ====Z2|  ====Z1|G ==== | ",
            "    | /[1]/    [2]      [3]     [4]      [5]      [6]      [7] | /[8]/ | BALL",
            "    | /[1]/    [2]      [3]     [4]      [5]      [6]      [7] | /[8]/ | POSS",
            "    | ==== G|Z1==== |Z2===== |Z3==== |3 ===== |2 ===== |1 ===== | ===== | ",
            "                                                                         ",
            "                               <--- ⬛⬛⬛ <---                          "
            "                                                                          ",
            "                                                                          ",
            "   SCORE                           🟥  [rtp]                        RPTS ",
            "                                   ⬛  [btp]                        BPTS ",
            "                                   QTR  [qq]                        QQTR ",

            ]



def run(send_to_window, get_input):
    # Initial startup messages
    send_to_window(0, HUMAN_TEAM_INFO )
    # send_to_window(1, CCF_FIELD        )
    send_to_window(2, ROBOT_TEAM_INFO )

    time.sleep(1)

    # Main loop
    loop=True
    rcoin=0
    rfire=0
    bcoin=0 
    bfire=0

    while loop:
        # Randomly update one of the 3 windows
        # win = random.randint(0, 2)
        # msg = random.choice(MESSAGES)
        # send_to_window(win, msg)

        # Ask for a command
        ballpos = get_input("Position(1-8) ")
        
        color   = "r" if (random.randint(0,1)==0) else "b"

        rcoin = rcoin+1 if rcoin<5 else 0
        rfire = rfire+1 if rfire<5 else 0
        bcoin = bcoin+1 if bcoin<5 else 0
        bfire = bfire+1 if bfire<5 else 0

        red_pts = random.randint(0, 50)
        blk_pts = random.randint(0, 50)
        quarter  = random.randint(1, 4)

        NEW_FLD_INFO=[]
        NEW_FLD_INFO = symbol_update( CCF_FIELD,    "🏈🏈", ballpos, "BALL")
        NEW_FLD_INFO = symbol_update( NEW_FLD_INFO, "🟥🟥" if (color.lower())=="r" else "⬛⬛", ballpos, "POSS")
        NEW_FLD_INFO = symbol_update( NEW_FLD_INFO, f' {red_pts} ', "rtp", "RPTS")
        NEW_FLD_INFO = symbol_update( NEW_FLD_INFO, f' {blk_pts} ', "btp", "BPTS")
        NEW_FLD_INFO = symbol_update( NEW_FLD_INFO, f' {quarter} ' , "qq",  "QQTR")

        NEW_FLD_INFO_X=[]
        for line in NEW_FLD_INFO:
            for n in range(1,9):
                line  = line.replace(f"[{n}]", f"   ")
            NEW_FLD_INFO_X.append(line)

        send_to_window(1, NEW_FLD_INFO_X )

        NEW_HUMAN_INFO=[]
        NEW_HUMAN_INFO = symbol_update( HUMAN_TEAM_INFO, CLUTCH_COIN[rcoin], "hcoin", "H_COIN")
        NEW_HUMAN_INFO = symbol_update( NEW_HUMAN_INFO,  MOJO_FIRE[rfire]  , "hfire", "H_FIRE")
        send_to_window(0, NEW_HUMAN_INFO )

        NEW_ROBOT_INFO=[]
        NEW_ROBOT_INFO = symbol_update( ROBOT_TEAM_INFO, CLUTCH_COIN[bcoin], "rcoin", "R_COIN")
        NEW_ROBOT_INFO = symbol_update( NEW_ROBOT_INFO,  MOJO_FIRE[bfire]  , "rfire", "R_FIRE")
        send_to_window(2, NEW_ROBOT_INFO )


        time.sleep(0.2)

def symbol_update( in_line: str, reps: str, chars: str, line: str):
        nsl=[]
        replace_str="["+chars+"]"
        for l in in_line:
            if l.find(line)>0 : 
                field_update=l.replace(replace_str,reps)
                field_update=field_update.replace(line,"       ")
                nsl.append(field_update)
            else:    
                nsl.append(l)

        return nsl

