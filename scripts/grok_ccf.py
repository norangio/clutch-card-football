#!/usr/bin/env python3
"""
Clutch Card Football — with JOKER, PUNT, FG PROMPTS
"""

import random
from typing import List, Dict, Tuple, Optional
from collections import deque
from dataclasses import dataclass
from enum import Enum

from CCF_drive_chart import Drives

if __name__ != "__main__":
    from python.ccf_gui.framework import send_to_window

# from game_output import update_game_window

# pct good for Rate 1,2,3 : Z3, Z2, Z1

TABLE_FG = { 1: [65,75,85], 2: [70,80,90], 3: [75,85,90]}

# === ENUMS ===
class Color(Enum):
    RED = "red"
    BLACK = "black"

@dataclass
class Card:
    value: str
    suit: Optional[str] = None
    color: Optional[Color] = None

    def __post_init__(self):
        if self.value == "Joker":
            self.color = None
        elif self.suit in ("H", "D"):
            self.color = Color.RED
        elif self.suit in ("S", "C"):
            self.color = Color.BLACK

    def __str__(self):
        return f"{self.value}{self.suit}" if self.suit else "JOKER"


# === DECK & HELPERS ===
def create_deck():
    values = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    suits = ["H","D","S","C"]
    deck = [Card(v,s) for v in values for s in suits]
    deck.extend([Card("Joker") for _ in range(3)])
    random.shuffle(deck)
    return deque(deck)

def card_value(card: Card) -> int:
    if card.value == "Joker": return 15
    order = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,"J":11,"Q":12,"K":13,"A":14}
    return order[card.value]

# === FIELD ===
def move(pos: str, dist: int, direction: int = 1) -> Tuple[str, bool]:
    SEGMENTS = ["0","1", "2", "3", "Z3", "Z2", "Z1"]  # 0 for safety

    idx = SEGMENTS.index(str(pos))

    """
    new_idx = idx + dist * direction
    td = False
    if direction > 0 and new_idx >= len(SEGMENTS):
        td = True
        new_idx = len(SEGMENTS) - 1
    elif direction < 0 and new_idx < 0:
        new_idx = 0
    """    
    new_idx = idx + dist
    td = False
    safety=False
    if new_idx >= len(SEGMENTS):
        td = True
        new_idx = 1
    elif new_idx < 1:
        safety=True
        new_idx = 3

    return SEGMENTS[new_idx], td, safety

# === BONUS ===
def apply_bonus(base: int, bonus: str, card: Card, team_color: Color, end_pos: str) -> Tuple[int, bool]:
    extra = 0
    auto_td = False
    if card.color == team_color:
        if bonus == "yellow":
            extra += 1
        elif bonus == "orange" and end_pos == "Z1":
            auto_td = True
        elif bonus == "green":
            extra += 1
            if end_pos == "Z1":
                auto_td = True
    return extra, auto_td


def start (self, ccf_info: Dict, send_to_window, get_input):
    game = Game()
    game.start_with_setup ( ccf_info, send_to_window, get_input  ) 

# === TEAM ===
@dataclass
class Team:
    name: str
    rating: int
    kick_rating: int
    color: Color
    clutch: int
    clutch_used: bool
    mojo: int = 0
    hand: List[Card] = None
    score: int = 0

    def __post_init__(self):
        self.hand = []

    def play(self, idx: int) -> Card:
        return self.hand.pop(idx)

# === GAME ===
class Game:
    def __init__(self):
        self.deck = deque()
        self.quarter = 1
        self.human = None
        self.ai = None
        self.offense = None
        self.pos = "1"
        self.dir = 1
        self.dtables = None
        self.window_num=(-1)

    def input_int(self, prompt: str, min_v: int, max_v: int) -> int:
        while True:
            try:
                v = int(input(prompt))
                if min_v <= v <= max_v: return v
                if v==0: exit()
                self.ccf_print(f"Enter {min_v}–{max_v}")
            except: self.ccf_print("Invalid")

    def prompt(self, msg: str):
        self.ccf_print(f">>> {msg}")
        input("[Enter]")

    def show_mojo(self):
        mojoIcon="🔥"
        human_mojo=(" ".join([mojoIcon] * self.human.mojo))
        ai_mojo=(" ".join([mojoIcon] * self.ai.mojo))
        self.ccf_print (f'MOJO Human {human_mojo}  AI {ai_mojo}')

    def start_with_setup(self, ccf_info: Dict, send_to_window=None, get_input=None):

        if (send_to_window is None) or (get_input is None):
            """not using framework"""
            self.window_num=(-1)
        else:
            self.window_num=3

        self.ccf_print("=== CLUTCH CARD FOOTBALL ===",self.window_num )
        h_name  = ccf_info.get("human_team_name", "Player")
        h_color = ccf_info.get("human_team_color", "RED")
        self.ccf_print ( f'{h_name} is {h_color}',self.window_num )
        self.human = Team(h_name,
                          ccf_info.get("human_drive_rating", 6),
                          ccf_info.get("human_kick_rating", 2),
                          Color.RED if h_color.upper()=="RED" else Color.BLACK,
                          ccf_info.get("human_starting_clutch", 3),
                          False)
        self.ai = Team("AI",
                       ccf_info.get("robot_drive_rating", 6),
                       ccf_info.get("robot_kick_rating", 2),
                       Color.BLACK if self.human.color == Color.RED else Color.RED,
                       ccf_info.get("robot_starting_clutch", 3),
                       False)
        

        self.dtables = Drives()

        self.dtables.print_drive_row_horz(self.human.rating,self.ai.rating)
       
        self.start_quarter()


    def setup(self):
        self.ccf_print("=== CLUTCH CARD FOOTBALL ===", self.window_num )
        h_name = input("Your team name: ") or "Player"
        roll = random.randint(1,2)
        if (roll==1): self.ccf_print ( f'{h_name} is RED',self.window_num )
        else        : self.ccf_print ( f'{h_name} is BLACK',self.window_num )  
        self.human = Team(h_name,
                          self.input_int("Your rating (1-12): ",1,12),
                          self.input_int("Your kick rating (1-3): ",1,3),
                          Color.RED if roll == 1 else Color.BLACK,
                          self.input_int("Starting clutch (0-5): ",0,5),
                          False)
        self.ai = Team("AI",
                       self.input_int("AI rating (1-12): ",1,12),
                       self.input_int("AI kick rating (1-3): ",1,3),
                       Color.BLACK if self.human.color == Color.RED else Color.RED,
                       self.input_int("AI clutch (0-5): ",0,5),
                       False)
        
        # self.dtables = Drives(str(self.human),str(self.ai))
        self.dtables = Drives()
        # self.dtables.print_drive_row(self.human.rating)
        # self.dtables.print_drive_row(self.ai.rating)
        
        self.dtables.print_drive_row_horz(self.human.rating,self.ai.rating)
       
        self.start_quarter()

    def start_quarter(self):
        fresh = self.quarter in (1,3)
        if fresh:
            self.deck = create_deck()

        deal = {1:7, 2:6, 3:6, 4:8}.get(self.quarter, 7)
        if self.quarter in (1,3): self.human.hand.clear(); self.ai.hand.clear()
        for _ in range(deal):
            if self.deck: self.human.hand.append(self.deck.popleft())
            if self.deck: self.ai.hand.append(self.deck.popleft())

        self.pos = "1"
        self.offense, self.defense = (self.human, self.ai) if self.quarter % 2 == 1 else (self.ai, self.human)
        self.dir = 1
        self.ccf_print(f"\n=== QUARTER {self.quarter} ===",self.window_num )
        self.play_turns()

    def play_turns(self):

        if (self.quarter < 4):  turns = 6
        else:                   turns = 7

        for t in range(turns):
            self.offense.clutch_used=False
            self.play_turn()
            self.ccf_print (f'Play {t+1} of {turns}')
            self.score_board()
        self.end_quarter()

    def play_turn(self):
        if self.offense.name=="AI":
            self.ccf_print(f"\n--  ▶️ ▶️  🏈  Offense: 🤖 {self.offense.color.value} ",self.window_num )
        else:
            self.ccf_print(f"\n--  ▶️ ▶️  🏈  Offense: 👱 {self.offense.color.value} ",self.window_num )

        self.ccf_print(f"Ball at Segment: {self.pos}")

        # Play cards
        off_card = self.choose_card(self.offense, is_offense=True)
        def_card = self.choose_card(self.defense, is_offense=False)

        self.ccf_print(f"→ OFF:{self.offense.name}: {off_card} <🏈> DEF:{self.defense.name}: {def_card}",self.window_num )

        # WAR?
        if card_value(off_card) == card_value(def_card):
            self.handle_war()
            return

        # JOKER?
        if off_card.value == "Joker" or def_card.value == "Joker":
            self.handle_joker(off_card, def_card)
            return

        # MOJO DEF?
        if card_value(def_card) > card_value(off_card):
            if self.defense.mojo < 2:
                self.defense.mojo += 1
                self.ccf_print(f"→ {self.defense.name} gains Mojo ({self.defense.mojo}/2)",self.window_num )
            if self.defense.mojo == 2 and self.defense.clutch == 1:
                self.defense.clutch += 1
                self.defense.mojo = 0
                self.ccf_print(f"→ Mojo converted to Clutch Point!",self.window_num )

        # MOJO OFF?
        if card_value(off_card) >= card_value(def_card) + 4 :
            if self.offense.mojo < 2:
                self.offense.mojo += 1
                self.ccf_print(f"→ {self.offense.name} gains Mojo ({self.offense.mojo}/2)")
            if self.offense.mojo == 2 and self.offense.clutch == 1:
                self.offense.clutch += 1
                self.offense.mojo = 0
                self.ccf_print(f"→ Mojo converted to Clutch Point!",self.window_num )

        # DRIVE
        # table = Drives[str(self.offense.rating)]
        if (self.offense.name == "AI"): 
            movement = self.dtables.get_card_result( self.ai.color, self.ai.rating, str(off_card) )
        else:
            movement = self.dtables.get_card_result( self.human.color, self.human.rating, str(off_card) )

        self.ccf_print (f'        movement {movement}',self.window_num ) 
        new_pos, td, safety = move(self.pos, movement, self.dir)
        self.ccf_print (f"→ Move: {movement} to seg → {new_pos}" + (" TOUCHDOWN!" if td else ""),self.window_num )


        if td:
            self.offense.score += 6
            self.ccf_print(f"→ TOUCHDOWN! +6 pts",self.window_num )
            self.offense.score += self.extra_points()
            
            self.pos = "1"
            self.swap_sides()
        else:
            self.pos = new_pos
            self.post_move_decision()

        # self.swap_sides()

    def handle_joker(self, off_card: Card, def_card: Card):
        self.prompt(
            "JOKER PLAYED!\n"
            "Compare cards to determine big play or turnover.\n"
            f"Offense: {off_card} | Defense: {def_card}\n"
        )
        if (card_value(def_card)==15): 
            self.ccf_print (f'defense Joker',self.window_num )
            if (card_value(off_card)<11): 
                self.ccf_print (f'TURNOVER!',self.window_num )
                self.pos = "3"
                self.swap_sides()
            else:
                self.ccf_print (f'BIG LOSS -1 SEGMENT',self.window_num )
                new_pos, td, safety = move(self.pos, -1 , self.dir)
                if (td==True or safety==True): 
                    self.score_pts(td,safety)
                    self.swap_sides()
                else: 
                    self.pos = new_pos
                    self.post_move_decision()
        else:
            self.ccf_print (f'Offense Joker')
            if (card_value(def_card)<4) :
                self.score_pts(True,False)
            else:
                if (self.offense.name == "AI"): 
                    movement = self.dtables.get_card_result( self.ai.color, self.ai.rating, "AH" )
                else:
                    movement = self.dtables.get_card_result( self.human.color, self.human.rating, "AH" )

                self.ccf_print ( f'Offense AH Movement {movement}',self.window_num )
                new_pos, td, safety = move(self.pos, movement , self.dir)
                if (td==1):
                    self.score_pts(True,False)
                else:
                    self.pos = new_pos
                    self.post_move_decision()

    def score_pts(self, td, safety):
        if (td==True): 
            self.offense.score += 6
            self.ccf_print(f"→ TOUCHDOWN! +6 pts",self.window_num )
            self.offense.score += self.extra_points()
            
            self.pos = "1"
            self.swap_sides()
        if (safety==True):
            self.defense.score += 2
            self.ccf_print(f"→ Safety! +2 pts defense ",self.window_num )
            self.pos = "3"

    def handle_war(self):
        war_card = self.deck.popleft() if self.deck else Card("2","S")
        self.prompt(
            "WAR! Card drawn from deck.\n"
            "→ If matches DEFENSE color → Turnover at segment 3\n"
            "→ If matches OFFENSE color → Offense at Z3\n"
            f"Drawn: {war_card} ({war_card.color.value if war_card.color else 'Joker'})\n"
        )
        if ( self.offense.color == war_card.color ):
            self.pos="Z3"
            self.post_move_decision()
        else:    
            # Placeholder: turnover
            self.pos = "3"
            self.swap_sides()

    def post_move_decision(self):
        self.ccf_print(f"\nBall at {self.pos} \nOptions: ")
        final_choice = "P"  # "P"-punt "F"-fieldgoalAttempt "C"-clutch  "S"-shortPunt
        if self.pos in ("Z1","Z2","Z3"):
            if self.offense.clutch > 0 and self.offense.clutch_used == False:
                self.ccf_print("1. Clutch | 2. Field Goal | 3. ShortPunt",self.window_num )
                if self.offense == self.human:
                    choice = self.input_int("Choose [1-3]: ",1,3)
                    if (choice==1): final_choice="C"
                    if (choice==2): final_choice="F"
                    if (choice==3): final_choice="S"
                else:
                    """ AI choice """    
                    self.ccf_print (f'AI Choice ....',self.window_num )
                    final_choice=self.handle_ai_choice()
            else: 
                self.ccf_print("1. Field Goal | 2. ShortPunt")
                if self.offense == self.human:
                    choice = self.input_int("Choose [1-2]: ",1,2)
                    if (choice==1): final_choice="F"
                    if (choice==2): final_choice="S"
                else:
                    """ AI choice """    
                    self.ccf_print (f'AI Choice ....',self.window_num )
                    final_choice=self.handle_ai_choice()

        else :
            if self.offense.clutch > 0 and self.offense.clutch_used == False:
                self.ccf_print("1. Clutch | 2. Punt")
                if self.offense == self.human:
                    choice = self.input_int("Choose [1,2]: ",1,2)
                    if (choice==1): final_choice="C"
                    if (choice==2): final_choice="P"
                else:
                    """ AI choice """    
                    self.ccf_print (f'AI Choice ....',self.window_num )
                    final_choice=self.handle_ai_choice()
            else:
                self.ccf_print("Punt is only choice")
                if self.offense == self.human:
                    self.ccf_print (f'Human Punt',self.window_num )
                else:
                    self.ccf_print (f'AI Punt',self.window_num )
                final_choice = "P"

        ## final choices, punt, short punt, clutch,field goal
        if final_choice == "P":
            self.handle_punt()
        elif final_choice == "S":
            self.handle_short_punt()
        elif final_choice == "F":
            self.handle_field_goal(self.pos)
        elif final_choice == "C":
            self.offense.clutch_used=True
            self.handle_clutch()

    def handle_ai_choice(self):
        """ AI decide punt, clutch or field goal"""
        if self.pos in ("Z1","Z2","Z3"):
            choice="F"
        else:
            if self.offense.clutch > 0 and self.offense.clutch_used == False:
                choice="C"
            else:
                choice="P"
        return choice 

    def handle_punt(self):
        roll = random.randint(1,6)
        if   (roll==2): roll=1
        elif (roll==6): roll=5

        back = self.offense.kick_rating + roll
        self.prompt(
            f"PUNT!\n"
            f"Roll d6: {roll}\n"
            f"kick rating ({self.offense.kick_rating})\n"
            f"distance    ({back})\n"
        )
        # Placeholder: move back 3 + roll
        back = self.offense.kick_rating + roll
        self.pos, _, __ = move(self.pos, back, -self.dir)
        self.swap_sides()

    def handle_short_punt(self):
        """ shorter punt """
        back = 3-self.offense.kick_rating + random.randint(0,2)
        self.pos, _, __ = move(self.pos, back, -self.dir)
        self.swap_sides()

    def handle_field_goal(self, pos):
        """   Z3   Z2   Z1 
              7    5    4    # sum di rol and rating max 9
        """
        self.ccf_print (f'field goal attempt {pos}',self.window_num )
        success = { "Z3": 7, "Z2": 5, "Z1": 4 }

        roll = random.randint(1,6)
        total = self.offense.kick_rating + roll
        self.prompt(
            f"FIELD GOAL ATTEMPT!\n"
            f"Kick Rating: {self.offense.kick_rating} + {roll}(d6) ===> {total}\n"
            f"{self.pos}::  Z3(7) Z2(5) Z1(4)\n"
        )
        # Placeholder: success if total >= 15
        if total >= success[str(pos)]:
            self.offense.score += 3
            self.ccf_print("→ FIELD GOAL GOOD! +3",self.window_num )
            self.pos = "1"
            self.swap_sides()
        else:
            self.ccf_print("→ FG MISSED! {total}",self.window_num )
            if (self.pos=="Z3"): self.pos=3
            if (self.pos=="Z2"): self.pos=2
            if (self.pos=="Z1"): self.pos=1
            self.swap_sides()

    def extra_points(self):
        roll1 = random.randint(1,6)
        roll2 = random.randint(1,6)
        total=roll1+roll2
        if   total<5 : self.ccf_print (f'Zero Pt on Conversion',self.window_num ); return 0
        elif total>10: self.ccf_print (f'2 Pt conversion!!',self.window_num ); return 2
        else         : self.ccf_print (f'1 Pt conversion!!',self.window_num ); return 1

    def handle_clutch(self):
        self.offense.clutch -= 1
        extra_card = self.deck.popleft() if self.deck else Card("A","H") # empty ?
        self.prompt(
            f"CLUTCH USED! (Remaining: {self.offense.clutch})\n"
            f"Drew: {extra_card} ({extra_card.color.value if extra_card.color else 'Joker'})\n"
        )
        # Recursively resolve extra card (simplified)
        # move the extra....
        if (card_value(extra_card)==15):
            self.offense.score += 6
            self.ccf_print(f"→ TOUCHDOWN! +6 pts",self.window_num )
            self.offense.score += self.extra_points()
            self.pos = "1"
            self.swap_sides()
        else: 
            if (self.offense.name == "AI"): 
                movement = self.dtables.get_card_result( self.ai.color, self.ai.rating, str(extra_card) )
            else:
                movement = self.dtables.get_card_result( self.human.color, self.human.rating, str(extra_card) )

            new_pos, td, safety = move(self.pos, movement , self.dir)
            self.ccf_print(f"→ Move: {movement} seg → {new_pos}" + (" TOUCHDOWN!" if td else ""))

            if td:
                self.offense.score += 6
                self.ccf_print(f"→ TOUCHDOWN! +6 pts",self.window_num )
                self.offense.score += self.extra_points()
                self.pos = "1"
                self.swap_sides()
            else:
                self.pos = new_pos
                self.post_move_decision()

    def choose_card(self, team: Team, is_offense: bool) -> Card:
        if team == self.human:
            self.ccf_print("Human hand:",self.window_num )
            hand_s=""
            for i, c in enumerate(team.hand):
                hand_s += f"{i}: {c}  "
            self.ccf_print(hand_s,self.window_num )
            idx = self.input_int("Choose card: ", 0, len(team.hand)-1)
            return team.play(idx)
        else:
            # AI: high defense, low offense near goal
            if not is_offense:
                idx = max(range(len(team.hand)), key=lambda i: card_value(team.hand[i]))
            else:
                idx = min(range(len(team.hand)), key=lambda i: card_value(team.hand[i]))
            return team.play(idx)

    def swap_sides(self):
        # self.ccf_print ( f'off:{self.offense.name} def:{self.defense.name}' )
        self.offense, self.defense = self.defense, self.offense
        self.dir *= -1
        # self.ccf_print ( f'off:{self.offense.name} def:{self.defense.name}' )

    def end_quarter(self):
        self.score_board()
        self.quarter += 1
        if self.quarter <= 4:
            self.start_quarter()
        else:
            print("\n🏈 FINAL SCORE 🏈",self.window_num )
            print(f"{self.human.name}: {self.human.score}",self.window_num )
            print(f"{self.ai.name}: {self.ai.score}",self.window_num )
            print("YOU WIN!" if self.human.score > self.ai.score else "AI WINS!" if self.ai.score > self.human.score else "TIE!",self.window_num )
            exit()

    def score_board(self):
        print(f"\n===🏈🏈 {self.quarter}  | {self.human.name}: {self.human.score}  | {self.ai.name}: {self.ai.score}  🏈🏈===")
        clutchCoin="🪙"
        human_cc=(" ".join([clutchCoin] * self.human.clutch))
        robot_cc=(" ".join([clutchCoin] * self.ai.clutch))

        print(f"\n=== Clutch {self.human.name}: {human_cc}  AI: {robot_cc} ")
        self.show_mojo()
        self.update_gui()
       
    def update_gui(self):

        print(f"\n===🏈🏈 {self.quarter} \n| {self.human.name}: {self.human.score} \n| {self.ai.name}: {self.ai.score}  🏈🏈===",self.window_num )
        clutchCoin="🪙"
        human_cc=(" ".join([clutchCoin] * self.human.clutch))
        robot_cc=(" ".join([clutchCoin] * self.ai.clutch))

        print(f"\n=== Clutch {self.human.name}: {human_cc}  \nAI: {robot_cc} ",self.window_num )
        self.show_mojo()

    def ccf_print(self, msg: str, window: int = (-1)):

        if (window>0):
            send_to_window(window, msg)
        else:
            print (f'{msg}')

# === RUN ===
if __name__ == "__main__":

    ccf_info={}
    game = Game()
    # game.setup()
    game.start_with_setup ( ccf_info ) 