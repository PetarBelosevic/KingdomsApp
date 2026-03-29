import tkinter as tk
import time

from labeling_ui import ImageLabelingUI


class ImageLabelingUIShortcuts(ImageLabelingUI):
    """
    UI for labeling images with shortcuts for quick label selection.
    """
    def __init__(self, master):
        super().__init__(master)

        self.shortcuts_enabled = False
        self.number_card_sign = 1
        self.last_number_abs = None
        self.card_value_var = None
        self.card_special_var = None
        self.castle_color_var = None
        self.castle_rank_var = None
        self.pending_castle_color = None
        self.pending_castle_rank = None
        self.pending_castle_time = 0.0
        self.castle_combo_window_s = 1.0
        self.keyboard_hint_label = None


    def enable_shortcuts(self):
        """
        Enables keyboard shortcuts for faster labeling.
        """
        self.shortcuts_enabled = True
        self.root.bind("<Key>", self.on_key_press)


    def disable_shortcuts(self):
        """
        Disables keyboard shortcuts.
        """
        self.shortcuts_enabled = False
        self.root.unbind("<Key>")


    def ensure_number_card_mode(self):
        """
        Selects number card mode if not already in that mode. 
        This is used when setting card value through shortcuts to ensure that correct options are shown and correct label structure is set.
        """
        if self.label_entry.get("cell_type") != "card":
            self.show_card_options()
        if self.label_entry.get("card", {}).get("card_type") != "number":
            self.show_number_card_options()


    def set_castle_selection(self, color, rank):
        """
        Sets castle selection based on color and rank. 
        This is used for keyboard shortcuts that allow setting castle color and rank by pressing color key followed by rank key or vice versa within a short time window.
        """
        if color not in ["red", "green", "blue", "yellow"]:
            return
        if rank not in [1, 2, 3, 4]:
            return
        
        if self.label_entry.get("cell_type") != "castle":
            self.show_castle_options()

        if self.castle_color_var:
            self.castle_color_var.set(color)
        if self.castle_rank_var:
            self.castle_rank_var.set(rank)


    def set_number_card_value(self, value):
        """
        Sets number card value in the label entry. 
        This is used for keyboard shortcuts that allow setting card value by pressing number key.

        :param value: integer, an absolute value of the card (1, 2, 3, 4, 5, 6) - sign is determined by self.number_card_sign
        """
        if value not in [1, 2, 3, 4, 5, 6]:
            return
        self.ensure_number_card_mode()
        signed_value = self.number_card_sign * value
        self.last_number_abs = value
        self.label_entry["card"]["value"].set(signed_value)


    def toggle_number_card_sign(self):
        """
        Toggles the sign of the number card value and updates self.number_card_sign and value stored in label_entry accordingly.
        """
        self.ensure_number_card_mode()
        self.number_card_sign *= -1

        current_value = self.label_entry["card"]["value"].get()
        if current_value:
            self.label_entry["card"]["value"].set(-current_value)
            self.last_number_abs = abs(current_value)
        elif self.last_number_abs:
            self.label_entry["card"]["value"].set(self.number_card_sign * self.last_number_abs)


    def on_key_press(self, event):
        """
        Handles keyboard press event and interprets it as a shortcut for labeling actions.
        Supported shortcuts:\n
            - Left Arrow or Backspace: go to previous image\n
            - Right Arrow or Enter: save current label and go to next image\n
            - Esc: back to main menu\n
            - 1-6: set number card value\n
            - -: toggle sign of number card value\n
            - R/G/B/Y + 1-4: set castle color and castle rank\n
            - W: select wizard special card type\n
            - M: select mountain special card type\n
            - G: select gold mine special card type\n
            - D: select dragon special card type \n
            - E: select empty cell type
        """
        if not self.shortcuts_enabled:
            return

        keysym = event.keysym
        char = event.char

        if keysym in ["Return", "KP_Enter", "Right"]:
            self.save_and_next()
            return "break"
        if keysym in ["BackSpace", "Left"]:
            self.previous_image()
            return "break"
        if keysym == "Escape":
            self.back_to_menu()
            return "break"

        lower_char = char.lower() if char else ""

        if lower_char == "e":
            self.empty_selected()
            return "break"

        if lower_char in ["w", "d", "g", "m"]:
            self.show_card_options()
            self.show_special_card_options()
            special_map = {
                "w": "wizard",
                "d": "dragon",
                "g": "gold mine",
                "m": "mountain",
            }
            if self.card_special_var:
                self.card_special_var.set(special_map[lower_char])
            if lower_char != "g":
                return "break"

        if char in ["1", "2", "3", "4", "5", "6"]:
            rank_value = int(char)
            if rank_value in [1, 2, 3, 4]:
                now = time.monotonic()
                if self.pending_castle_color and (now - self.pending_castle_time) <= self.castle_combo_window_s:
                    self.set_castle_selection(self.pending_castle_color, rank_value)
                    self.pending_castle_color = None
                    self.pending_castle_rank = None
                    return "break"
                self.pending_castle_rank = rank_value
                self.pending_castle_time = now
                # return "break"
            self.set_number_card_value(rank_value)
            return "break"

        if keysym == "minus" or char == "-":
            self.toggle_number_card_sign()
            return "break"

        if lower_char in ["r", "g", "b", "y"]:
            color_map = {
                "r": "red",
                "g": "green",
                "b": "blue",
                "y": "yellow",
            }
            now = time.monotonic()
            if self.pending_castle_rank and (now - self.pending_castle_time) <= self.castle_combo_window_s:
                self.set_castle_selection(color_map[lower_char], self.pending_castle_rank)
                self.pending_castle_color = None
                self.pending_castle_rank = None
                return "break"
            self.pending_castle_color = color_map[lower_char]
            self.pending_castle_time = now
            return "break"


    def show_main_menu(self):
        self.disable_shortcuts()
        return super().show_main_menu()


    def show_labeling_interface(self, edit_mode=False):
        self.enable_shortcuts()
        self.number_card_sign = 1
        self.last_number_abs = None
        self.pending_castle_color = None
        self.pending_castle_rank = None
        self.pending_castle_time = 0.0
        
        super().show_labeling_interface(edit_mode)

        if self.keyboard_hint_label:
            self.keyboard_hint_label.destroy()
        self.keyboard_hint_label = tk.Label(
            self.root,
            text="Shortcuts:\nLeft Arrow/Backspace: Previous; Right Arrow/Enter: Save+Next; Esc: menu;\nE: empty cell;\n1-6: set card number value; -: toggle sign;\nw: wizard card, m: mountain card, g: gold mine card, d: dragon card;\nr/g/b/y + 1-4: castle rank and color",
            font=("Arial", 10),
            fg="gray"
        )
        self.keyboard_hint_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self.keyboard_hint_label.pack(pady=8)
        

    def show_number_card_options(self, preselect=False):
        super().show_number_card_options(preselect)
        if preselect and self.preselect_data:
            selected_value = self.preselect_data.get("card", {}).get("value", 0)
            if selected_value:
                self.number_card_sign = -1 if selected_value < 0 else 1
                self.last_number_abs = abs(selected_value)



if __name__ == "__main__":
    root = tk.Tk()
    app = ImageLabelingUIShortcuts(root)
    root.mainloop()