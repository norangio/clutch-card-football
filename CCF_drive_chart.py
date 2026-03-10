"""
DriveChart module for clutch_card_football game engine

This module is designed to be imported and controlled by other code (choice 2 from the conversation).
It does not prompt for terminal input when imported.
"""

class Drives:
    def __init__(self):

        self.drive_chart = {
                    "1": {
                        "2":  {"base": -1},
                        "3":  {"base":  0},
                        "4":  {"base":  1},
                        "5":  {"base":  1, "bonus": "yellow"},
                        "6":  {"base":  2},
                        "7":  {"base":  2},
                        "8":  {"base":  2},
                        "9":  {"base":  2},
                        "10": {"base":  2, "bonus": "yellow"},
                        "J":  {"base":  3},
                        "Q":  {"base":  3},
                        "K":  {"base":  3},
                        "A":  {"base":  4}
                        },
                    "2": {
                        "2":  {"base": -1},
                        "3":  {"base":  0},
                        "4":  {"base":  1, "bonus": "yellow"},
                        "5":  {"base":  2},
                        "6":  {"base":  2},
                        "7":  {"base":  2},
                        "8":  {"base":  2},
                        "9":  {"base":  2},
                        "10": {"base":  2, "bonus": "yellow"},
                        "J":  {"base":  3},
                        "Q":  {"base":  3},
                        "K":  {"base":  3},
                        "A":  {"base":  4}
                        },
                    "3": {
                        "2":  {"base":  0},
                        "3":  {"base":  0},
                        "4":  {"base":  1, "bonus": "yellow"},
                        "5":  {"base":  2},
                        "6":  {"base":  2},
                        "7":  {"base":  2},
                        "8":  {"base":  2},
                        "9":  {"base":  2, "bonus": "yellow"},
                        "10": {"base":  3},
                        "J":  {"base":  3},
                        "Q":  {"base":  3},
                        "K":  {"base":  3},
                        "A":  {"base":  4}
                        },
                    "4": {
                        "2":  {"base":  0},
                        "3":  {"base":  0},
                        "4":  {"base":  1, "bonus": "yellow"},
                        "5":  {"base":  2},
                        "6":  {"base":  2},
                        "7":  {"base":  2},
                        "8":  {"base":  2, "bonus": "yellow"},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3},
                        "Q":  {"base":  3},
                        "K":  {"base":  3},
                        "A":  {"base":  4}
                        },
                    "5": {
                        "2":  {"base":  0},
                        "3":  {"base":  1},
                        "4":  {"base":  1, "bonus": "yellow"},
                        "5":  {"base":  2},
                        "6":  {"base":  2},
                        "7":  {"base":  2},
                        "8":  {"base":  2, "bonus": "yellow"},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3},
                        "Q":  {"base":  3, "bonus": "yellow"},
                        "K":  {"base":  4},
                        "A":  {"base":  4, "bonus": "orange"}
                        },
                    "6": {
                        "2":  {"base":  0},
                        "3":  {"base":  1},
                        "4":  {"base":  1, "bonus": "yellow"},
                        "5":  {"base":  2},
                        "6":  {"base":  2},
                        "7":  {"base":  2, "bonus": "yellow"},
                        "8":  {"base":  3},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3},
                        "Q":  {"base":  3, "bonus": "yellow"},
                        "K":  {"base":  4},
                        "A":  {"base":  4, "bonus": "orange"}
                        },
                    "7": {
                        "2":  {"base":  0},
                        "3":  {"base":  1},
                        "4":  {"base":  1, "bonus": "yellow"},
                        "5":  {"base":  2},
                        "6":  {"base":  2, "bonus": "yellow"},
                        "7":  {"base":  3},
                        "8":  {"base":  3},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3},
                        "Q":  {"base":  3, "bonus": "yellow"},
                        "K":  {"base":  4},
                        "A":  {"base":  4, "bonus": "green"}
                        },
                    "8": {
                        "2":  {"base":  0},
                        "3":  {"base":  1},
                        "4":  {"base":  1, "bonus": "yellow"},
                        "5":  {"base":  2},
                        "6":  {"base":  2, "bonus": "yellow"},
                        "7":  {"base":  3},
                        "8":  {"base":  3},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3, "bonus": "yellow"},
                        "Q":  {"base":  4},
                        "K":  {"base":  4},
                        "A":  {"base":  4, "bonus": "green"}
                        },
                    "9": {
                        "2":  {"base":  0},
                        "3":  {"base":  1},
                        "4":  {"base":  1, "bonus": "yellow"},
                        "5":  {"base":  2},
                        "6":  {"base":  2, "bonus": "yellow"},
                        "7":  {"base":  3},
                        "8":  {"base":  3},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3, "bonus": "yellow"},
                        "Q":  {"base":  4},
                        "K":  {"base":  4, "bonus": "yellow"},
                        "A":  {"base":  5, "bonus": "orange"}
                        },
                    "10": {
                        "2":  {"base":  0},
                        "3":  {"base":  1, "bonus": "yellow"},
                        "4":  {"base":  2},
                        "5":  {"base":  2},
                        "6":  {"base":  2, "bonus": "yellow"},
                        "7":  {"base":  3},
                        "8":  {"base":  3},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3, "bonus": "yellow"},
                        "Q":  {"base":  4},
                        "K":  {"base":  4, "bonus": "yellow"},
                        "A":  {"base":  5, "bonus": "orange"}
                        },
                    "11": {
                        "2":  {"base":  1},
                        "3":  {"base":  1, "bonus": "yellow"},
                        "4":  {"base":  2},
                        "5":  {"base":  2},
                        "6":  {"base":  2, "bonus": "yellow"},
                        "7":  {"base":  3},
                        "8":  {"base":  3},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3, "bonus": "yellow"},
                        "Q":  {"base":  4},
                        "K":  {"base":  4, "bonus": "yellow"},
                        "A":  {"base":  5, "bonus": "green"}
                        },
                    "12": {
                        "2":  {"base":  1, "bonus": "yellow"},
                        "3":  {"base":  2},
                        "4":  {"base":  2},
                        "5":  {"base":  2},
                        "6":  {"base":  2, "bonus": "yellow"},
                        "7":  {"base":  3},
                        "8":  {"base":  3},
                        "9":  {"base":  3},
                        "10": {"base":  3},
                        "J":  {"base":  3, "bonus": "yellow"},
                        "Q":  {"base":  4},
                        "K":  {"base":  4, "bonus": "yellow"},
                        "A":  {"base":  5, "bonus": "green"}
                        }
                    # "JOKER": {"effect": "turnover"}
                }

    # Suit → color mapping
        self.SUIT_TO_COLOR = {
            "di": "red",      # diamonds
            "diamonds": "red",
            "hearts": "red",
            "he": "red",
            "sp": "black",    # spades
            "spades": "black",
            "cl": "black",    # clubs
            "clubs": "black",
            "club": "black"
        }

    @staticmethod
    def get_card_color(self, suit: str) -> str:
        """Convert suit (full name or 2-letter) → 'red' or 'black'"""
        return self.SUIT_TO_COLOR.get(suit.lower(), None)

    def get_card_result(self, team_color: str, rating: int, card: str ):
        """ convert card string to value AND suit """

        card_value=card[:-1]
        card_suit =card[-1]
        return self.get_drive_result(team_color, rating, card_value, card_suit )
        

    # @classmethod
    def get_drive_result(self, color: str, rate: int, card_value: str, card_suit: str = None) -> int:
        """
        Returns the final yardage for a play.

        Args:
            color: "red" or "black" (team color)
            rate: 2–12 (int)
            card_value: "2" to "10", "J", "Q", "K", "A"
            card_suit:  suit string like "hearts", "di", "spades", etc.
                        If None → no bonus applied

        Returns:
            int: final yards gained (can be negative)
        """
        color_str = str(color).lower()
        dice_str = str(rate)
        card_str = str(card_value).upper()

        # Get the raw entry
        entry = self.drive_chart.get(dice_str, {}).get(card_str)
        if not entry:
            return 0  # or raise ValueError if you prefer

        base_yards = entry["base"]
        bonus_color = entry.get("bonus")   # e.g. "yellow", "orange", "green" or missing

        # No bonus → just return base
        if not bonus_color or not card_suit:
            return base_yards

        # Determine if the card is red or black
        card_color = self.get_card_color(self,card_suit)
        if card_color is None:
            return base_yards  # unknown suit → no bonus

        # Bonus only triggers when suit color matches bonus color requirement
        # Yellow = any red card
        # Orange = any black card
        # Green = face card (J/Q/K) of matching color
        if bonus_color == "yellow" and card_color == "red" and color_str == "red":
            return base_yards + 1
        elif bonus_color == "yellow" and card_color == "black" and color_str == "black":
            return base_yards + 1
        elif bonus_color == "orange" and card_color == "red"  and color_str == "red":
            return base_yards + 0.5
        elif bonus_color == "orange" and card_color == "black" and color_str == "black":
            return base_yards + 0.5
        elif bonus_color == "green" and card_color == "red"  and color_str == "red":
            return base_yards + 1.5
        elif bonus_color == "green" and card_color == "black" and color_str == "black":
            return base_yards + 1.5
        else:
            # No bonus applied
            return base_yards
    
    def print_drive_row(self, rating):
        """
        Prints a formatted table for a single dice total (e.g., 7)
        """
        dice_str = str(rating)
        #print (f'rating: {dice_str}')
        if dice_str not in self.drive_chart:
            //print(f"Rating {rating} not found in drive chart!")
            return

        row = self.drive_chart[dice_str]

        ##print(f"\n{'='*60}")
        ## print(f"{'RATING =':<4} {rating}")
        ## print(f"{'='*60}")
        ## print(f"{'Card':<6}  {'Total Yards'}")
        ## print("-" * 60)

        # Sort cards in play order: 2 to 10, then J, Q, K, A
        card_order = [str(i) for i in range(2, 11)] + ["J", "Q", "K", "A"]

        for card in card_order:
            if card not in row:
                continue
            data = row[card]
            base = data["base"]
            bonus = data.get("bonus", "-")
            total = f"{base}"
            if bonus != "-":
                total += f" + {self.bonus(bonus)}"

            ## print(f"{card:<6} {total}")
    
    ## print(f"{'='*60}\n")


    def bonus (self, value: str):
        if (value=="yellow"): return "1 iff Team Color"
        if (value=="orange"): return "Z1 TD"
        if (value=="green"): return  "1 iff Team Color, Z1 TD"

    def print_drive_row_horz(self, human_rating, ai_rating):

        symbol={"yellow": "!", "orange": "+", "green": "*"}
        s="     "
        ## print (f'Ratings {human_rating} {ai_rating}')
        for key,val in self.drive_chart[str(human_rating)].items():
            s=s+f' {key:2s}'
        ## print(s)

        def add_symbol(val):
            if (val=="yellow"): return symbol["yellow"]
            if (val=="orange"): return symbol["orange"]
            if (val=="green") : return symbol["green"]
            return " "
        
        s="Human "
        for key,val in self.drive_chart[str(human_rating)].items():
            char=" "
            for k,v in val.items():
                if (k=="bonus") : char=add_symbol(v)
            s=s+f'{val["base"]}{char} '
        ## print(s)    

        s="AI    "
        for key,val in self.drive_chart[str(ai_rating)].items():
            char=" "
            for k,v in val.items():
                if (k=="bonus") : char=add_symbol(v)
            s=s+f'{val["base"]}{char} '
        ## print(s)    


