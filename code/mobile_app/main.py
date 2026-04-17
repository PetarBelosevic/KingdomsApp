import os
import sys
import cv2

current_dir = os.path.dirname(os.path.abspath(__file__)) # dataset_framework directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kivy.app import App
from kivy.lang import Builder
from kivy.resources import resource_find
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.graphics.texture import Texture
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.image import Image

try:
    from android.permissions import request_permissions, Permission
    from android.activity import bind as activity_bind

    from image_processing import rectify_image, BoardModel
    from game_logic import calculate_player_points
    from camera import OneShotCamera, CAMERA_REQUEST_CODE
    from gallery import GalleryPhotoPicker, GALLERY_REQUEST_CODE 
    ANDROID = True
except ImportError:
    ANDROID = False

# --------------------------------------------------

class RootScreenManager(ScreenManager):
    pass

class StartScreen(Screen):
    pass

class ImageMethodScreen(Screen):
    pass

class DetectedBoardScreen(Screen):
    pass

class BoardModelScreen(Screen):
    pass

class RoundResultsScreen(Screen):
    pass

# --------------------------------------------------

class GameInfoPopup(Popup):
    pass

class WinnerPopup(Popup):
    pass

class SymbolsLegendPopup(Popup):
    pass

# --------------------------------------------------

class BaseLabel(Label):
    pass


class RotatableImage(Image):
    angle = NumericProperty(0)
    rotation_scale = NumericProperty(1.0)

    def on_kv_post(self, base_widget):
        self._update_rotation_scale()

    def on_angle(self, instance, value):
        self._update_rotation_scale()

    def on_size(self, instance, value):
        self._update_rotation_scale()

    def on_texture(self, instance, value):
        self._update_rotation_scale()

    def _update_rotation_scale(self):
        if self.angle % 180 == 0:
            self.rotation_scale = 1.0
            return

        image_w, image_h = self.norm_image_size
        if image_w <= 0 or image_h <= 0 or self.width <= 0 or self.height <= 0:
            self.rotation_scale = 1.0
            return

        self.rotation_scale = min(self.width / image_h, self.height / image_w)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.angle = (self.angle + 90) % 180
            return True
        return super().on_touch_down(touch)

# --------------------------------------------------

class BaseTextInput(TextInput):
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
        """
        Check if the text is a valid prefix of any allowed token.
        Allowed tokens are: r1-r4, g1-g4, b1-b4, y1-y4, 1 to 6, -1 to -6, w, gm, d, m
        """
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
        """
        Return RGBA color tuple based on text content.
        Coloring scheme:\n
        Castle colors (r1-r4, g1-g4, b1-b4, y1-y4) → red, green, blue, yellow\n
        Numbers (1-6) → light blue\n
        Negative numbers (-1 to -6) → orange\n
        Special symbols (w, gm, d, m) → light purple\n
        Default (empty or invalid) → black\n
        """
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
    
# --------------------------------------------------

class KingdomsApp(App):
    round = StringProperty("")
    score = StringProperty("")
    winner = StringProperty("")
    back_button_text = StringProperty("Back")
    android = BooleanProperty(False)
    rotation_angle = NumericProperty(0)

    red_total = StringProperty("")
    red_last = StringProperty("")
    red_new = StringProperty("")
    green_total = StringProperty("")
    green_last = StringProperty("")
    green_new = StringProperty("")
    blue_total = StringProperty("")
    blue_last = StringProperty("")
    blue_new = StringProperty("")
    yellow_total = StringProperty("")
    yellow_last = StringProperty("")
    yellow_new = StringProperty("")


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.game_data = JsonStore(os.path.join(self.app_dir, "game_data.json"))
        models_dir = os.path.join(self.app_dir, "onnx_models")
        self.image = None
        self.board_model = None
        self.sorted_photos = []
        self._selected_photo_path = None
        
        if ANDROID:
            self.camera = OneShotCamera(self)
            self.gallery = GalleryPhotoPicker(self)
            self.board_model_processing_unit = BoardModel(path_to_models=models_dir)


    def build(self):
        self.android = platform == "android"
        if self.android:
            request_permissions([Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES])
            activity_bind(on_activity_result=self.on_activity_result)
    
        kv_path = resource_find("kingdoms_app.kv") or os.path.join(self.app_dir, "kingdoms_app.kv")
        root = Builder.load_file(kv_path)
        root.transition = SlideTransition(direction="left")
        self.determine_initial_screen(root)
        return root
    

    def determine_initial_screen(self, root):
        """Determine which screen to show on app start based on game data. If a round is in progress, show round results; otherwise, show start screen."""
        if self.game_data.exists("round") and self.game_data.get("round")["round"] > 0:
            root.current = "round_results"
            self.prepare_results()
        else:
            root.current = "start"

    # --------------------------------------------------
    # Generic methods

    def _go_to_default(self, screen_name, direction=None):
        """Changes screen with optional transition direction."""
        if direction is not None:
            self.root.transition.direction = direction
        self.root.current = screen_name


    def go_to(self, screen_name, direction=None, extra_work=None):
        """Changes screen with optional transition direction and then executes extra work (e.g. preparing the screen)."""
        self._go_to_default(screen_name, direction)
        if extra_work is not None:
            extra_work()


    def clear_metadata(self):
        """Clears image and board model data"""
        self.image = None
        self.board_model = None


    def clear_game(self):
        """Clears game results and metadata."""
        self.back_button_text = "Back"
        self.score = ""
        self.game_data.clear()
        self.clear_metadata()

    # --------------------------------------------------
    # Start screen methods

    def start_new_game(self):
        """Clears previous data, sets new game scores to 0, and goes to the image method selection screen."""
        self.clear_game()
        self.back_button_text = "Quit Game (without saving)"
        self.game_data.put("round", round=0)
        self.game_data.put("total_score", r=0, g=0, b=0, y=0)
        self.game_data.put("last_score", r=0, g=0, b=0, y=0)
        self.game_data.put("new_score", r=0, g=0, b=0, y=0)
        self._go_to_default("image_method", "left")


    def show_game_info(self):
        """Shows game info popup with instructions and rules."""
        popupWindow = GameInfoPopup()
        popupWindow.open() # show the popup

    # --------------------------------------------------
    # image display

    def show_image(self):
        """Displays the detected board image on the DetectedBoardScreen."""
        frame = self.image  # your cv2 image (numpy array)
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
    # board detection

    def detect_board(self):
        """Detects the board in the input image, rectifies it and then goes to the detected board screen to show the result."""     
        self.image = rectify_image(self.image)
        self.go_to("detected_board", "left", self.show_image)

    # --------------------------------------------------
    # board model generation

    def generate_board_model(self):
        """Generates the board model from the detected board image (if model is not already generated) using the BoardModel class, then goes to the board model screen to show the result."""
        if self.board_model is None:
            if self.board_model_processing_unit is None:
                return
            self.board_model = self.board_model_processing_unit.generate_board_model(self.image)

        self.go_to("board_model", "left", self._initialize_symbol_grid)


    def _initialize_symbol_grid(self):
        """Inserts detected symbols into the grid of TextInput widgets on the BoardModelScreen."""
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
        """Updates the board model based on the current text input in the grid on the BoardModelScreen."""
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
        """Updates the board model (in case changes were made), calculates player points for this round, updates game data with new scores and increments the round, and then goes to the round results screen."""
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


    def show_symbols_legend(self):
        """Shows the symbols legend popup with explanations of what each symbol means in the context of the game."""
        popupWindow = SymbolsLegendPopup()
        popupWindow.open() # show the popup
    
    # --------------------------------------------------
    # results screen methods

    def prepare_results(self):
        """Prepares text that shows scores for each player and the current round on the RoundResultsScreen based on game data."""
        round = self.game_data.get("round")["round"] if self.game_data.exists("round") else "-"
        total_scores = self.game_data.get("total_score") if self.game_data.exists("total_score") else {"r": "-", "g": "-", "b": "-", "y": "-"}
        new_scores = self.game_data.get("new_score") if self.game_data.exists("new_score") else {"r": "-", "g": "-", "b": "-", "y": "-"}
        last_scores = self.game_data.get("last_score") if self.game_data.exists("last_score") else {"r": 0, "g": 0, "b": 0, "y": 0}
        
        self.round = f"Round: {round}"
        score_rows = [
            ("Red", "r"),
            ("Green", "g"),
            ("Blue", "b"),
            ("Yellow", "y"),
        ]
        self.red_total = f"{total_scores['r']}"
        self.red_last = f"{last_scores['r']}"
        self.red_new = f"{new_scores['r']}"
        self.green_total = f"{total_scores['g']}"
        self.green_last = f"{last_scores['g']}"
        self.green_new = f"{new_scores['g']}"
        self.blue_total = f"{total_scores['b']}"
        self.blue_last = f"{last_scores['b']}"
        self.blue_new = f"{new_scores['b']}"
        self.yellow_total = f"{total_scores['y']}"
        self.yellow_last = f"{last_scores['y']}"
        self.yellow_new = f"{new_scores['y']}"
        
        self.score = "\n".join(
            f"{name:<6}: {total_scores[key]:>4}"
            for name, key in score_rows
        )


    def next_round(self):
        """Clears metadata, increments round number in game data, checks if the game has ended (after round 3) and either shows the winner or goes back to the image method selection screen or the start screen."""
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
        """Decreases the round number in game data (if it exists and is greater than 0) to allow going back to the previous round's results screen."""
        if self.game_data.exists("round"):
            current_round = self.game_data.get("round")["round"]
            if current_round > 0:
                self.game_data.put("round", round=current_round-1)


    def show_winner(self):
        """Shows the winner popup with the winner text based on game data and then goes back to the start screen when the popup is dismissed."""
        popupWindow = WinnerPopup()
        popupWindow.open() # show the popup

    # --------------------------------------------------
    # image retrieval methods via gallery 

    def start_gallery(self, *args):
        """Calls the method to start the gallery intent to pick an image from the device."""
        self.gallery.start_gallery(*args)

    # --------------------------------------------------- launch camera intent

    def start_camera(self, *args):
        """Calls the method to launch the camera intent to capture an image."""
        self.camera.start_camera(*args)

    # --------------------------------------------------- activity result back

    def on_activity_result(self, request_code, result_code, data):
        """Propagates activity results from camera and gallery intents to their respective handlers."""
        if request_code == CAMERA_REQUEST_CODE:
            self.camera.on_activity_result_callback(request_code, result_code, data)
        elif request_code == GALLERY_REQUEST_CODE:
            self.gallery.on_activity_result_callback(request_code, result_code, data)

# --------------------------------------------------

if __name__ == '__main__':
    KingdomsApp().run()