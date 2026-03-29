import tkinter as tk
from tkinter import messagebox
import json
import os
from PIL import Image, ImageTk
import sys

current_dir = os.path.dirname(os.path.abspath(__file__)) # dataset_framework directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from variables import IMAGE_DIR, GROUND_TRUTH_LABELS


class ImageLabelingUI:
    """
    Simple GUI application for labeling cell images. 
    It allows the user to label each cell image with its type (castle or card) and specific attributes (color and rank for castle, card type and value for card). 
    The labels are saved in a JSON file. 
    The user can also review and edit existing labels.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Image Labeling Tool")
        self.root.geometry("800x700")
        
        self.image_dir = IMAGE_DIR
        self.labels_file = GROUND_TRUTH_LABELS
        self.labels = {}
        self.current_index = 0
        self.image_files = []
        self.preselect_data = None
        self.card_value_var = None
        self.card_special_var = None
        self.castle_color_var = None
        self.castle_rank_var = None
        
        self.show_main_menu()
    

    def show_main_menu(self):
        """
        Displays main menu.
        Menu allows user to choose between reviewing/editing existing labels and labeling unlabeled images.
        It also checks if the labels file exists and creates it if it doesn't.
        """
        self.clear_window()
        tk.Label(self.root, text="Image Labeling Tool", font=("Arial", 16, "bold")).pack(pady=20)
        
        # create labels.json if it doesn't exist or is empty
        if not os.path.exists(self.labels_file) or os.path.getsize(self.labels_file) == 0:
            with open(self.labels_file, 'w') as f:
                json.dump({}, f)

        tk.Button(self.root, text="Review Labeled Images", command=self.set_review_mode, width=30, height=2).pack(pady=10)
        tk.Button(self.root, text="Label Unlabeled Images", command=self.set_labeling_mode, width=30, height=2).pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.root.quit, width=30, height=2).pack(pady=10)
    

    def set_review_mode(self):
        """
        Sets up reviewing mode.
        If there are no labeled images, appropriate message is shown and user is returned to main menu.
        If labeled images exist, method calls labeling interface method for the first labeled image.
        """
        try:
            with open(self.labels_file, 'r') as f:
                self.labels = json.load(f)
            self.image_files = list(self.labels.keys())
            self.current_index = 0
            if self.image_files:
                self.show_labeling_interface(edit_mode=True)
            else:
                messagebox.showinfo("Info", "No labeled images found")
                self.show_main_menu()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load labels: {str(e)}")
    

    def set_labeling_mode(self):
        """
        Sets up labeling mode.
        Method loads all images from the image directory and checks which of them are not labeled yet.
        If all images are labeled, appropriate message is shown and user is returned to main menu.
        Else, method calls labeling interface method for the first unlabeled image.
        """
        try:
            if os.path.exists(self.labels_file):
                with open(self.labels_file, 'r') as f:
                    self.labels = json.load(f)
            else:
                self.labels = {}
            
            all_images = [f for f in os.listdir(self.image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            self.image_files = [img for img in all_images if img not in self.labels]
            
            self.current_index = 0
            if self.image_files:
                self.show_labeling_interface(edit_mode=False)
            else:
                messagebox.showinfo("Info", "All images are already labeled")
                self.show_main_menu()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load images: {str(e)}")
    

    def show_labeling_interface(self, edit_mode=False):
        """
        Displays starting labeling interface for the current image.
        If edit_mode is True, interface is set up for reviewing/editing existing labels, else it is set up for labeling unlabeled images.
        If in edit mode and current image has existing label, the label options are preselected based on the existing label data.
        Method shows the current image, file info, navigation buttons and buttons for selecting object type (castle or card).
        if the image has an existing label, the object type is preselected.

        :param edit_mode: if True, interface is set up for reviewing/editing existing labels, else it is set up for labeling unlabeled images
        """
        self.clear_window()
        self.edit_mode = edit_mode
        self.card_value_var = None
        self.card_special_var = None
        self.castle_color_var = None
        self.castle_rank_var = None

        if not self.image_files:
            messagebox.showinfo("Done", "No more images")
            self.show_main_menu()
            return

        current_file = self.image_files[self.current_index]
        image_path = os.path.join(self.image_dir, current_file)

        # Display image
        try:
            img = Image.open(image_path)
            img.thumbnail((800, 800))
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(self.root, image=photo)
            img_label.image = photo
            img_label.pack(pady=10)
        except Exception as e:
            tk.Label(self.root, text=f"Error loading image: {str(e)}").pack()

        # File info
        tk.Label(self.root, text=f"{current_file} ({self.current_index + 1}/{len(self.image_files)})", font=("Arial", 10)).pack()

        # Buttons
        navigation_buttons = tk.Frame(self.root)
        navigation_buttons.pack(pady=10)
        tk.Button(navigation_buttons, text="← Previous", command=self.previous_image).pack(side=tk.LEFT, padx=5)
        tk.Button(navigation_buttons, text="Save & Next →", command=self.save_and_next).pack(side=tk.LEFT, padx=5)
        tk.Button(navigation_buttons, text="Back to Menu", command=self.back_to_menu).pack(side=tk.LEFT, padx=5)

        # Label input
        tk.Label(self.root, text="Select object type:", font=("Arial", 12)).pack(pady=10)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.label_entry = {}
        self.preselect_data = None
        if self.edit_mode and current_file in self.labels:
            self.preselect_data = self.labels[current_file]

        tk.Button(button_frame, text="Castle", command=self.show_castle_options, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Card", command=self.show_card_options, width=15).pack(side=tk.LEFT, padx=5)
        self.empty_button = tk.Button(button_frame, text="Empty", command=self.empty_selected, width=15)
        self.empty_button.pack(side=tk.LEFT, padx=5)

        self.options_frame = tk.Frame(self.root)
        self.options_frame.pack_forget()

        # If in edit mode, auto-select the object type and show options
        if self.preselect_data:
            cell_type = self.preselect_data.get("cell_type")
            if cell_type == "castle":
                self.show_castle_options(preselect=True)
            elif cell_type == "card":
                self.show_card_options(preselect=True)
            elif cell_type == "empty":
                self.empty_selected()


    def empty_selected(self):
            """
            Clears options frame and sets label entry to {"cell_type": "empty"} when empty cell type is selected.
            """
            self.label_entry = {"cell_type": "empty"}
            self.empty_button.config(relief="sunken")
            if self.options_frame:
                self.options_frame.destroy()


    def show_castle_options(self, preselect=False):
        """
        Expands labeling options when castle type is selected.
        New options include color (red, green, blue, yellow) and rank (1, 2, 3, 4).
        
        :param preselect: if True, the options are preselected based on the existing label data. This should be True when in edit mode and current image has existing label.
        """
        self.label_entry = {}
        self.label_entry["cell_type"] = "castle"
        self.label_entry["castle"] = {}
        # clear previous options
        self.empty_button.config(relief="raised")
        if self.options_frame:
            self.options_frame.destroy()
        self.options_frame = tk.Frame(self.root)
        self.options_frame.pack(pady=10)

        # Variables to store selections
        color_var = tk.StringVar()
        rank_var = tk.IntVar()
        self.label_entry["castle"]["color"] = color_var
        self.label_entry["castle"]["rank"] = rank_var
        self.castle_color_var = color_var
        self.castle_rank_var = rank_var

        # Preselect if in edit mode
        if preselect and self.preselect_data:
            castle_data = self.preselect_data.get("castle", {})
            color_var.set(castle_data.get("color", ""))
            rank_var.set(castle_data.get("rank", 0))

        tk.Label(self.options_frame, text="Select Color:", font=("Arial", 12)).pack(pady=5)
        colors = ['red', 'green', 'blue', 'yellow']
        color_frame = tk.Frame(self.options_frame)
        color_frame.pack(pady=5)
        for color in colors:
            tk.Radiobutton(color_frame, text=color.capitalize(), variable=color_var, value=color, borderwidth=2, relief="raised", width=12, indicatoron=False).pack(side=tk.LEFT, padx=5)

        tk.Label(self.options_frame, text="Select Castle Rank:", font=("Arial", 12)).pack(pady=5)
        ranks = [1, 2, 3, 4]
        rank_frame = tk.Frame(self.options_frame)
        rank_frame.pack(pady=5)
        for rank in ranks:
            tk.Radiobutton(rank_frame, text=f"Rank {rank}", variable=rank_var, value=rank, borderwidth=2, relief="raised", width=12, indicatoron=False).pack(side=tk.LEFT, padx=5)


    def show_card_options(self, preselect=False):
        """
        Expands labeling options when card type is selected.
        New options include card type (number or special).

        :param preselect: if True, the options are preselected based on the existing label data. This should be True when in edit mode and current image has existing label.
        """
        self.label_entry = {}
        self.label_entry["cell_type"] = "card"
        self.label_entry["card"] = {}
        # clear previous options
        self.empty_button.config(relief="raised")
        if self.options_frame:
            self.options_frame.destroy()
        self.options_frame = tk.Frame(self.root)
        self.options_frame.pack(pady=10)

        tk.Label(self.options_frame, text="Select Card Kind:", font=("Arial", 12)).pack(pady=5)
        self.card_options_frame = None

        # If preselect, determine which card type to show
        card_type = None
        if preselect and self.preselect_data:
            card_data = self.preselect_data.get("card", {})
            card_type = card_data.get("card_type")
        # buttons for number and special
        tk.Button(self.options_frame, text="Number Card", command=self.show_number_card_options, width=20).pack(pady=5)
        tk.Button(self.options_frame, text="Special Card", command=self.show_special_card_options, width=20).pack(pady=5)

        # If preselect, show the correct card options and preselect values
        if card_type == "number":
            self.show_number_card_options(preselect=True)
        elif card_type == "special":
            self.show_special_card_options(preselect=True)


    def show_number_card_options(self, preselect=False):
        """
        Expands labeling options when number card type is selected.
        New options include card value (-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6).

        :param preselect: if True, the options are preselected based on the existing label data. This should be True when in edit mode and current image has existing label.
        """
        self.label_entry["card"]["card_type"] = "number"
        if hasattr(self, 'card_options_frame') and self.card_options_frame:
            self.card_options_frame.destroy()
        self.card_options_frame = tk.Frame(self.options_frame)
        self.card_options_frame.pack(pady=5)

        tk.Label(self.card_options_frame, text="Enter Number:").pack()
        value_var = tk.IntVar()
        self.card_value_var = value_var
        self.label_entry["card"]["value"] = value_var
        numbers = [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6]
        button_frame = tk.Frame(self.card_options_frame)
        button_frame.pack(pady=5)
        for num in numbers:
            display_text = f"+{num}" if num > 0 else str(num)
            tk.Radiobutton(button_frame, text=display_text, variable=value_var, value=num, borderwidth=2, relief="raised", width=4, indicatoron=False).pack(side=tk.LEFT, padx=2)

        # Preselect value if in edit mode
        if preselect and self.preselect_data:
            card_data = self.preselect_data.get("card", {})
            value_var.set(card_data.get("value", 0))


    def show_special_card_options(self, preselect=False):
        """
        Expands labeling options when special card type is selected.
        New options include special card type (dragon, mountain, wizard, gold mine).

        :param preselect: if True, the options are preselected based on the existing label data. This should be True when in edit mode and current image has existing label.
        """
        self.label_entry["card"]["card_type"] = "special"
        if hasattr(self, 'card_options_frame') and self.card_options_frame:
            self.card_options_frame.destroy()
        self.card_options_frame = tk.Frame(self.options_frame)
        self.card_options_frame.pack(pady=5)

        tk.Label(self.card_options_frame, text="Select Special Card Type:", font=("Arial", 12)).pack(pady=5)
        special_var = tk.StringVar()
        self.card_special_var = special_var
        self.label_entry["card"]["special_type"] = special_var
        special_types = ['dragon', 'mountain', 'wizard', 'gold mine']
        special_frame = tk.Frame(self.card_options_frame)
        special_frame.pack(pady=5)
        for t in special_types:
            tk.Radiobutton(special_frame, text=t, variable=special_var, value=t, borderwidth=2, relief="raised", width=12, indicatoron=False).pack(side=tk.LEFT, padx=5)

        # Preselect value if in edit mode
        if preselect and self.preselect_data:
            card_data = self.preselect_data.get("card", {})
            special_var.set(card_data.get("special_type", ""))


    def save_label(self, force=True):
        """
        Stores the current label selections for the current image in the labels dictionary and saves it to the JSON file.

        :param force: if True, method checks if all required options are selected and shows warning if not. If False, method doesn't save labels if values are missing.
        """
        current_file = self.image_files[self.current_index]
        
        if not self.validate_label():
            if force:
                messagebox.showwarning("Warning", "Please select an object type before proceeding.")
            return False

        self.labels[current_file] = self.label_entry

        # save to the file
        try:
            with open(self.labels_file, 'w') as f:
                json.dump(self.labels, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save labels: {str(e)}")
        return True


    def save_and_next(self):
        """
        Forces to save current label selection and moves to the next image if saving is succesful.
        """
        if not self.save_label(force=True):
            return

        self.current_index += 1
        if self.current_index < len(self.image_files):
            self.show_labeling_interface(self.edit_mode)
        else:
            messagebox.showinfo("Complete", "All images labeled!")
            self.show_main_menu()
    

    def previous_image(self):
        """
        Tries to save current label and moves to the previous image.
        If saving was not succesful, changes on the current label selection will not be saved.
        """
        self.save_label(force=False)
        if self.current_index > 0:
            # Try to save current labels before moving to previous image
            self.current_index -= 1
            self.show_labeling_interface(self.edit_mode)
    

    def back_to_menu(self):
        """
        Returns to the main menu without saving current label selection.
        """
        self.label_entry = {}
        self.show_main_menu()
    

    def clear_window(self):
        """
        Destroys all widgets in the window.
        This is used to clear the window before showing a new interface (main menu, labeling interface).
        """
        for widget in self.root.winfo_children():
            widget.destroy()


    def validate_label(self):
        """
        Checks if the current label entry is complete and transforms tk.Variable values to regular Python values if neccesary.

        Complete and valid empty cell label must have following structure:\n
        {\n
            "cell_type": "empty"\n
        }\n

        Complete and valid card label must have following structure:\n
        {\n
            "cell_type": "card",\n
            "card": {\n
                "card_type": "number",\n
                "value": -6 | -5 | -4 | -3 | -2 | -1 | 1 | 2 | 3 | 4 | 5 | 6
            }
        }\n
        or\n
        {\n
            "cell_type": "card",\n
            "card": {\n
                "card_type": "special",\n
                "special_type": "dragon" | "mountain" | "wizard" | "gold mine"
            }
        }\n

        Complete and valid castle label must have following structure:\n
        {\n
            "cell_type": "castle",\n
            "castle": {\n
                "color": "red" | "green" | "blue" | "yellow",\n
                "rank": 1 | 2 | 3 | 4 \n
            } \n
        }
        """
        label = self.label_entry
        type = label.get("cell_type", None)
        if not type:
            return False
        
        if type == "empty":
            return True
            
        for key in label[type]:
            value = label[type][key].get() if isinstance(label[type][key], tk.Variable) else label[type][key]
            if not value:
                return False
            else:
                label[type][key] = value

        if type == "card":
            card_type = label[type].get("card_type", None)
            if card_type == "number":
                value = label[type].get("value", None)
                if not value or value not in [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6]:
                    return False
            elif card_type == "special":
                spec_type = label[type].get("special_type", None)
                if not spec_type or spec_type not in ['dragon', 'mountain', 'wizard', 'gold mine']:
                    return False
        elif type == "castle":
            color = label[type].get("color", None)
            rank = label[type].get("rank", None)
            if not color or color not in ['red', 'green', 'blue', 'yellow']:
                return False
            if not rank or rank not in [1, 2, 3, 4]:
                return False
        else:
            return False
        
        self.label_entry = label
        return True



if __name__ == "__main__":
    root = tk.Tk()
    app = ImageLabelingUI(root)
    root.mainloop()