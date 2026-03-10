import tkinter as tk
from tkinter import font as tkfont

class GameWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ASCII Game Output")

        # Default font
        self.font = tkfont.Font(family="Consolas", size=14)

        # Text widget that resizes with window
        self.text = tk.Text(
            self.root,
            font=self.font,
            wrap="none"
        )
        self.text.pack(expand=True, fill="both")

        # Allow window resizing
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    def update_output(self, text: str, font_size: int = None, append: bool = False):
        """Update ASCII output and optionally change font size.

        By default this replaces the widget contents. Pass `append=True`
        to add to existing content (useful when sending incremental lines).
        """
        if font_size:
            self.font.configure(size=font_size)

        if not append:
            self.text.delete("1.0", "end")

        # Ensure text ends with a newline when appending multiple lines
        if append and not text.endswith("\n"):
            text = text + "\n"

        self.text.insert("end", text)
        # Scroll to the end so new lines are visible when appending
        self.text.see("end")

    def run(self):
        self.root.mainloop()

# Global instance
game_window = GameWindow()

if __name__ == '__main__':
    gw = GameWindow()
    gw.update_output("First line\n")       # replaces existing text
    gw.update_output("Second line", append=True)  # appends a new line
    gw.update_output("Third line", append=True)   # appends another line
    gw.run()