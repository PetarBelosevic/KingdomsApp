import sys
import cv2
import os

from kivy.uix.screenmanager import Builder, Screen, ScreenManager, SlideTransition
from kivy.app import App
# from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore
from kivy.properties import StringProperty
from kivy.graphics.texture import Texture
from kivy.uix.textinput import TextInput, platform
from kivy.resources import resource_find
try:
    from android.permissions import request_permissions, Permission
    
#     # Source - https://stackoverflow.com/a/68888334
#     # Posted by Husam Fathi
#     # Retrieved 2026-03-29, License - CC BY-SA 4.0
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES, Permission.CAMERA])
except ImportError:
    pass

current_dir = os.path.dirname(os.path.abspath(__file__)) # dataset_framework directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from image_processing import rectify_image, BoardModel
from game_logic import calculate_player_points
from camera import Camera2Capture


class RootScreenManager(ScreenManager):
    pass

class StartScreen(Screen):
    pass

class ImageMethodScreen(Screen):
    pass

class GalleryScreen(Screen):
    pass

class DetectedBoardScreen(Screen):
    pass

class BoardModelScreen(Screen):
    pass

class RoundResultsScreen(Screen):
    pass

class GameInfoPopup(AnchorLayout):
    pass

class WinnerPopup(AnchorLayout):
    pass

class BaseTextInput(TextInput):
    # We validate input in insert_text; TextInput input_filter must be None,
    # a known keyword ("int"/"float"), or a callable.
    input_filter = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        bold_font = resource_find("Roboto-Bold.ttf")
        if bold_font:
            self.font_name = bold_font
        self.bind(text=self._update_text_color)
        self._update_text_color(self, self.text)


    def insert_text(self, substring, from_undo=False):
        # Keep only allowed characters and reject edits that cannot produce a valid token.
        filtered = "".join(ch for ch in substring if ch.lower() in "rgbywdm0123456-")
        if not filtered:
            return

        cursor = self.cursor_index()
        candidate = (self.text[:cursor] + filtered + self.text[cursor:]).lower()
        if self._is_valid_prefix(candidate):
            return super().insert_text(filtered, from_undo=from_undo)


    @staticmethod
    def _is_valid_prefix(text):
        if text == "":
            return True

        if text in {"r", "g", "b", "y", "-", "w", "d", "m", "gm"}:
            return True

        if len(text) == 1 and text in {"1", "2", "3", "4", "5", "6"}:
            return True

        if len(text) == 2 and text[0] in {"r", "g", "b", "y"} and text[1] in {"1", "2", "3", "4"}:
            return True

        if len(text) == 2 and text[0] == "-" and text[1] in {"1", "2", "3", "4", "5", "6"}:
            return True

        return False
    
    
    def _update_text_color(self, instance, value):
        """Update text color and border based on content."""
        color = self._get_color_for_text(value)
        self.foreground_color = color
    

    def _get_color_for_text(self, text):
        """Return RGBA color tuple based on text content."""
        text = text.strip()
        
        # Castle colors (red, green, blue, yellow)
        if text.lower() in ['r1', 'r2', 'r3', 'r4']:
            return (1, 0, 0, 1)  # Red
        elif text.lower() in ['g1', 'g2', 'g3', 'g4']:
            return (0, 0.8, 0, 1)  # Green
        elif text.lower() in ['b1', 'b2', 'b3', 'b4']:
            return (0, 0, 1, 1)  # Blue
        elif text.lower() in ['y1', 'y2', 'y3', 'y4']:
            return (0.8, 0.8, 0.0, 1)  # yellow
        
        # Numbers (1-6) - light blue
        elif text in ['1', '2', '3', '4', '5', '6']:
            return (0.5, 0.8, 1.0, 1)  # light blue
        
        # Negative numbers (-1 to -6) - orange
        elif text in ['-1', '-2', '-3', '-4', '-5', '-6']:
            return (0.9, 0.5, 0, 1)  # orange
        
        # Special symbols (w, gm, d, m) - light purple
        elif text.lower() in ['w', 'gm', 'd', 'm']:
            return (0.5, 0.3, 0.9, 1)  # purple
        
        # Default (empty or invalid) - black
        else:
            return (0, 0, 0, 1)  # Black
    


class KingdomsApp(App):
    round = StringProperty("")
    score = StringProperty("")
    winner = StringProperty("")
    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_data = JsonStore("mobile_app/game_data.json")
        self.image = None
        self.board_model = None
        self.board_model_processing_unit = BoardModel()


    def build(self):
        self.android = platform == "android"

        root = Builder.load_file("kingdoms_game.kv")
        root.transition = SlideTransition(direction="left")
        self.determine_initial_screen(root)
        return root
    

    def _go_to_default(self, screen_name, direction=None):
        if direction is not None:
            self.root.transition.direction = direction
        self.root.current = screen_name


    def go_to(self, screen_name, direction=None, extra_work=None):
        self._go_to_default(screen_name, direction)
        if extra_work is not None:
            extra_work()

    
    def clear_metadata(self):
        self.image = None
        self.board_model = None


    def clear_game(self):
        self.game_data.clear()
        self.clear_metadata()


    def determine_initial_screen(self, root):
        if self.game_data.exists("round") and self.game_data.get("round")["round"] > 0:
            root.current = "round_results"
            self.prepare_results()
        else:
            root.current = "start"

    # --------------------------------------------------
    # Start screen methods

    def start_new_game(self):
        self.clear_game()
        self.game_data.put("round", round=0)
        self.game_data.put("total_score", r=0, g=0, b=0, y=0)
        self.game_data.put("last_score", r=0, g=0, b=0, y=0)
        self.game_data.put("new_score", r=0, g=0, b=0, y=0)
        self._go_to_default("image_method", "left")


    def show_game_info(self):
        show = GameInfoPopup() 
        popupWindow = Popup(title="Game Info", content=show, size_hint=(0.8,0.8))
        popupWindow.open() # show the popup

    # --------------------------------------------------
    # image retrieval methods # TODO 

    def take_new_photo(self): # TODO
        # open camera and take photo, then save to temp file and set selected_image_path
        # print("Open camera and take photo")
        camera = Camera2Capture()
        camera.capture(self.detect_board)


    def on_gallery_selection(self, selection):
        self._pending_gallery_selection = selection[0] if selection else ""


    def use_selected_from_gallery(self):
        if not self._pending_gallery_selection:
            self.processing_status = "No image selected yet."
            return

        self.selected_image_path = self._pending_gallery_selection
        self.image = cv2.imread(self.selected_image_path)
        self._pending_gallery_selection = ""
        self.detect_board()

    # --------------------------------------------------
    # image display

    def show_image(self, image):
        frame = image  # your cv2 image (numpy array)
        # 1. Convert BGR → RGB
        buf = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 2. Flip vertically
        buf = cv2.flip(buf, 0)
        # 3. Convert to bytes
        buf = buf.tobytes()
        # 4. Create texture
        texture = Texture.create(
            size=(frame.shape[1], frame.shape[0]),
            colorfmt='rgb'
        )
        # 5. Blit buffer
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        # 6. Display in Image widget
        screen = self.root.get_screen("detected_board")
        screen.ids.board.texture = texture
    
    # --------------------------------------------------
    # data processing methods

    def detect_board(self):
        self.image = rectify_image(self.image)
        self._go_to_default("detected_board", "left")
        self.show_image(self.image)

    
    def generate_board_model(self):
        self.board_model = self.board_model_processing_unit.generate_board_model(self.image)
        self.go_to("board_model", "left", self._initialize_symbol_grid)

    
    def _initialize_symbol_grid(self):
        grid = self.root.get_screen("board_model").ids.board_model
        grid.clear_widgets()

        for row in self.board_model:
            for symbol in row:
                if isinstance(symbol, int):
                    symbol = str(symbol)
                    
                cell = BaseTextInput(
                    text=symbol
                )
                grid.add_widget(cell)

    
    def update_board_model_from_input(self):
        grid = self.root.get_screen("board_model").ids.board_model
        updated_model = []
        n = len(self.board_model)
        m = len(self.board_model[0]) if n > 0 else 0
        for i, row in enumerate(self.board_model):
            updated_row = []
            for j, _ in enumerate(row):
                cell = grid.children[n * m - (i * m + j) - 1]
                text = cell.text.strip()
                # cast to int if possible, otherwise keep as string
                if text.lstrip("-").isdigit():
                    updated_row.append(int(text))
                else:
                    updated_row.append(cell.text)
            updated_model.append(updated_row)
        self.board_model = updated_model


    def calculate_scores(self):
        self.update_board_model_from_input()

        if not self.game_data.exists("last_score"):
            self.game_data.put("last_score", r=0, g=0, b=0, y=0)
        
        points = calculate_player_points(self.board_model)
        self.game_data.put("new_score", **points)

        # sum last and new scores to get total score
        total_score = {color: self.game_data.get("last_score")[color] + points[color] for color in ["r", "g", "b", "y"]}
        self.game_data.put("total_score", **total_score)

        if self.game_data.exists("round"):
            current_round = self.game_data.get("round")["round"]
            self.game_data.put("round", round=current_round+1)
        self.go_to("round_results", "left", self.prepare_results)

    # --------------------------------------------------
    # results screen methods

    def prepare_results(self):
        round = self.game_data.get("round")["round"] if self.game_data.exists("round") else "-"
        total_scores = self.game_data.get("total_score") if self.game_data.exists("total_score") else {"r": "-", "g": "-", "b": "-", "y": "-"}
        new_scores = self.game_data.get("new_score") if self.game_data.exists("new_score") else {"r": "-", "g": "-", "b": "-", "y": "-"}
        last_scores = self.game_data.get("last_score") if self.game_data.exists("last_score") else {"r": 0, "g": 0, "b": 0, "y": 0}
        
        self.round = f"Round: {round}"
        score_rows = [
            ("red", "r"),
            ("green", "g"),
            ("blue", "b"),
            ("yellow", "y"),
        ]
        self.score = "\n".join(
            f"{name:<6}: {total_scores[key]:>3} ({last_scores[key]:>3} + {new_scores[key]:>3})"
            for name, key in score_rows
        )


    def next_round(self):
        self.clear_metadata()
        if self.game_data.exists("round"):
            current_round = self.game_data.get("round")["round"]
            if current_round == 3:
                # find the max score and determine winner
                total_scores = self.game_data.get("total_score")
                max_score = max(total_scores.values())
                winners = [color for color, score in total_scores.items() if score == max_score]
                # replace color keys with color names
                color_names = {"r": "Red", "g": "Green", "b": "Blue", "y": "Yellow"}
                winners = [color_names[color] for color in winners]

                if len(winners) == 1:
                    self.winner = f"{winners[0]} won!"
                else:
                    self.winner = f"{', '.join(winners)} tied for the win!"

                self.show_winner()
            else:
                # last_score becomes total_score for the next round
                total_score = self.game_data.get("total_score")
                self.game_data.put("last_score", **total_score)
                self._go_to_default("image_method", "left")
        else:
            self.go_to("start", "left", self.clear_game)


    def decrease_round(self):
        if self.game_data.exists("round"):
            current_round = self.game_data.get("round")["round"]
            if current_round > 0:
                self.game_data.put("round", round=current_round-1)


    def show_winner(self):
        show = WinnerPopup()
        popupWindow = Popup(title="Winner", content=show, size_hint=(0.6,0.3))
        popupWindow.bind(on_dismiss=lambda _: self.go_to("start", "left", self.clear_game))
        popupWindow.open() # show the popup

    # --------------------------------------------------


if __name__ == "__main__":
    KingdomsApp().run()