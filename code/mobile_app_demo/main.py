import os
import sys
import cv2
from pathlib import Path
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__)) # dataset_framework directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

    
from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.resources import resource_find
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput

from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window

from kivy.properties import StringProperty

from kivy.uix.popup import Popup

from image_processing import rectify_image, BoardModel
from game_logic import calculate_player_points

# from mobile_app_demo.camera import OneShotCamera

try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.activity import bind as activity_bind
    from jnius import autoclass, cast
    ANDROID = True
except ImportError:
    ANDROID = False
CAMERA_REQUEST_CODE = 1001
GALLERY_REQUEST_CODE = 1002


# --------------------------------------------------

class RootScreenManager(ScreenManager):
    pass

class StartScreen(Screen):
    pass

class ImageMethodScreen(Screen):
    pass

# class GalleryScreen(Screen):
#     pass
    # def populate_thumbnails(self):
    #     """Populate gallery grid with thumbnail buttons."""
    #     if not hasattr(self, 'gallery_grid'):
    #         return
        
    #     grid = self.gallery_grid
    #     grid.clear_widgets()
        
    #     # Get app instance and sorted photos
    #     app = App.get_running_app()
    #     if not hasattr(app, 'sorted_photos') or not app.sorted_photos:
    #         return
        
    #     # Create thumbnail button for each photo
    #     for photo_path in app.sorted_photos:
    #         btn = app.create_thumbnail_button(photo_path)
    #         grid.add_widget(btn)

class DetectedBoardScreen(Screen):
    pass

class BoardModelScreen(Screen):
    pass

class RoundResultsScreen(Screen):
    pass

# --------------------------------------------------

class GameInfoPopup(AnchorLayout):
    pass

class WinnerPopup(AnchorLayout):
    pass

# --------------------------------------------------

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
    
# --------------------------------------------------
    

class KingdomsApp(App):
    round = StringProperty("")
    score = StringProperty("")
    winner = StringProperty("")


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.game_data = JsonStore(os.path.join(self.app_dir, "game_data.json"))
        models_dir = os.path.join(self.app_dir, "onnx_models")
        self.board_model_processing_unit = BoardModel(path_to_models=models_dir)
        self.image = None
        self.board_model = None
        self.sorted_photos = []
        self._selected_photo_path = None


    def build(self):
        self.android = platform == "android"
        if self.android:
        #     from camera import Camera2Capture
        #     self.camera_class = Camera2Capture
            # from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES])
            activity_bind(on_activity_result=self.on_activity_result)
    
        kv_path = resource_find("helloworld.kv") or os.path.join(self.app_dir, "helloworld.kv") # TODO change
        root = Builder.load_file(kv_path)
        root.transition = SlideTransition(direction="left")
        self.determine_initial_screen(root)
        return root
    

    def determine_initial_screen(self, root):
        if self.game_data.exists("round") and self.game_data.get("round")["round"] > 0:
            root.current = "round_results"
            self.prepare_results()
        else:
            root.current = "start"


    def on_pause(self):
        return True
    
    # --------------------------------------------------
    # Generic methods

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
    # image display

    def show_image(self):
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
        self.image = rectify_image(self.image)
        self.go_to("detected_board", "left", self.show_image)

    # --------------------------------------------------
    # board model generation

    def generate_board_model(self):
        if self.board_model_processing_unit is None:
            return

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
    # image retrieval methods via custom gallery 
    # idea from https://groups.google.com/g/kivy-users/c/bjsG2j9bptI/m/-Oe_aGo0newJ

    def start_gallery(self, *args):
        print(f"DEBUG: start_gallery called, ANDROID={ANDROID}")
        if not ANDROID:
            print("DEBUG: Not on Android, returning")
            return
        has_perm = check_permission(Permission.READ_EXTERNAL_STORAGE) or check_permission(Permission.READ_MEDIA_IMAGES)
        print(f"DEBUG: READ_EXTERNAL_STORAGE={check_permission(Permission.READ_EXTERNAL_STORAGE)}, READ_MEDIA_IMAGES={check_permission(Permission.READ_MEDIA_IMAGES)}")
        if not has_perm:
            print("DEBUG: Requesting READ_MEDIA_IMAGES and READ_EXTERNAL_STORAGE permissions")
            request_permissions([Permission.READ_MEDIA_IMAGES, Permission.READ_EXTERNAL_STORAGE])
            return
        try:
            print("DEBUG: Launching gallery intent")
            self._launch_gallery()
        except Exception as e:
            print(f"DEBUG: Exception in start_gallery: {e}")
            import traceback
            traceback.print_exc()


    def _launch_gallery(self):
        Intent         = autoclass('android.content.Intent')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity

        self.activity = activity

        intent = Intent()
        intent.setAction(Intent.ACTION_PICK)
        intent.setType("image/*")

        activity.startActivityForResult(intent, GALLERY_REQUEST_CODE)

    
    def _load_photo_from_gallery(self, intent):
        """Load photo from gallery intent result."""
        try:
            if intent is None:
                print("DEBUG: intent is None")
                return
            
            MediaStore_Images_Media_DATA = "_data"
            currentActivity = self.activity

            selectedImage = intent.getData()
            print(f"DEBUG: selectedImage = {selectedImage}")
            if selectedImage is None:
                print("DEBUG: selectedImage is None")
                return

            filePathColumn = [MediaStore_Images_Media_DATA]
            cursor = currentActivity.getContentResolver().query(selectedImage, filePathColumn, None, None, None)
            
            if cursor is None:
                print("DEBUG: cursor is None")
                return
            
            if not cursor.moveToFirst():
                print("DEBUG: cursor.moveToFirst() returned False")
                cursor.close()
                return

            columnIndex = cursor.getColumnIndex(filePathColumn[0])
            print(f"DEBUG: columnIndex = {columnIndex}")
            if columnIndex < 0:
                print("DEBUG: columnIndex < 0")
                cursor.close()
                return
            
            picturePath = cursor.getString(columnIndex)
            cursor.close()
            print(f"DEBUG: picturePath = {picturePath}")

            if not picturePath or not os.path.exists(picturePath):
                print(f"DEBUG: picturePath invalid or doesn't exist: {picturePath}")
                return

            self.image = cv2.imread(picturePath)
            print(f"DEBUG: cv2.imread returned image: {self.image is not None}")
            if self.image is None:
                print("DEBUG: cv2.imread failed")
                return

            print("DEBUG: Scheduling detect_board")
            Clock.schedule_once(lambda dt: self.detect_board(), 0.0) # !
        except Exception as e:
            print(f"DEBUG: Exception in _load_photo_from_gallery: {e}")
            import traceback
            traceback.print_exc()


    # def get_sorted_photos(self, directory, limit=100):
    #     """Get photo files sorted by modification time (newest first).
        
    #     Args:
    #         directory: Path to photo directory
    #         limit: Maximum number of photos to return (default 100)
        
    #     Returns:
    #         List of file paths sorted newest first (up to limit)
    #     """
    #     try:
    #         files = []
    #         for filename in os.listdir(directory):
    #             filepath = os.path.join(directory, filename)
    #             if os.path.isfile(filepath):
    #                 ext = os.path.splitext(filename)[1].lower()
    #                 if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
    #                     try:
    #                         mtime = os.path.getmtime(filepath)
    #                         files.append((filepath, mtime))
    #                     except OSError:
    #                         pass
            
    #         files.sort(key=lambda x: x[1], reverse=True)
    #         sorted_paths = [f[0] for f in files[:limit]]
    #         return sorted_paths
    #     except Exception as e:
    #         print(f'get_sorted_photos error: {e}')
    #         return []


    # def load_gallery(self):
    #     """Load sorted photos when entering gallery screen."""
    #     gallery_dir = "/storage/emulated/0/DCIM/Camera"
    #     self.sorted_photos = self.get_sorted_photos(gallery_dir, limit=100)
    #     self._selected_photo_path = None


    # def create_thumbnail_button(self, photo_path):
    #     """Create a button with thumbnail for a photo."""
    #     btn = Button(size_hint_y=None, height=150)
    #     try:
    #         # Create thumbnail texture
    #         img = cv2.imread(photo_path)
    #         if img is not None:
    #             # Resize for thumbnail
    #             img = cv2.resize(img, (150, 150))
    #             # Convert BGR to RGB
    #             img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    #             # Convert to bytes
    #             buf = img.tobytes()
    #             # Create texture
    #             texture = Texture.create(size=(150, 150), colorfmt='rgb')
    #             texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
    #             btn.background_normal = ''
    #             btn.canvas.clear()
    #             with btn.canvas:
    #                 from kivy.graphics import Rectangle
    #                 Rectangle(texture=texture, pos=btn.pos, size=btn.size)
    #     except:
    #         btn.text = "Error"
        
    #     # Bind photo path to button
    #     btn.photo_path = photo_path
    #     btn.bind(on_press=self.on_thumbnail_press)
    #     return btn


    # def on_thumbnail_press(self, instance):
    #     """Handle thumbnail selection."""
    #     self._selected_photo_path = instance.photo_path


    # def use_selected_from_gallery(self):
    #     """Load the selected photo and detect board."""
    #     if not self._selected_photo_path:
    #         return

    #     try:
    #         self.image = cv2.imread(self._selected_photo_path)
    #         if self.image is None:
    #             return
    #         self.detect_board()
    #     except Exception as e:
    #         pass

    # --------------------------------------------------

    # Camera intent methods (Android only)
    # --------------------------------------------------- launch camera intent

    def start_camera(self, *args):
        if not ANDROID:
            return
        if not check_permission(Permission.CAMERA):
            request_permissions([Permission.CAMERA])
            return
        try:
            self._launch_camera()
        except Exception:
            pass


    def _launch_camera(self):
        Intent         = autoclass('android.content.Intent')
        MediaStore     = autoclass('android.provider.MediaStore')
        MediaImages    = autoclass('android.provider.MediaStore$Images$Media')
        MediaColumns   = autoclass('android.provider.MediaStore$MediaColumns')
        ContentValues  = autoclass('android.content.ContentValues')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Build_VERSION  = autoclass('android.os.Build$VERSION')

        activity = PythonActivity.mActivity
        context  = activity.getApplicationContext()

        values = ContentValues()
        # Use MediaColumns (declaring class) — these now resolve correctly
        values.put(MediaColumns.DISPLAY_NAME, 'kivy_temp_photo.jpg')
        values.put(MediaColumns.MIME_TYPE,    'image/jpeg')
        if Build_VERSION.SDK_INT >= 29:
            # RELATIVE_PATH is also declared on MediaColumns (API 29+)
            values.put(MediaColumns.RELATIVE_PATH, 'Pictures/KivyTemp')

        self.temp_photo_uri = context.getContentResolver().insert(MediaImages.EXTERNAL_CONTENT_URI, values)

        if self.temp_photo_uri is None:
            return

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        # Cast Uri → Parcelable so pyjnius picks the right putExtra() overload
        intent.putExtra(MediaStore.EXTRA_OUTPUT, cast('android.os.Parcelable', self.temp_photo_uri))

        activity.startActivityForResult(intent, CAMERA_REQUEST_CODE)

    # --------------------------------------------------- activity result back

    def on_activity_result(self, request_code, result_code, data):
        Activity = autoclass('android.app.Activity')
        if result_code != Activity.RESULT_OK:
            if request_code == CAMERA_REQUEST_CODE:
                self._cleanup_mediastore()
            return

        if request_code == CAMERA_REQUEST_CODE:
            try:
                self._load_photo()
            except Exception:
                self._cleanup_mediastore()
        
        elif request_code == GALLERY_REQUEST_CODE:
            try:
                self._load_photo_from_gallery(data)
            except Exception:
                pass


    def _load_photo(self):
        PythonActivity   = autoclass('org.kivy.android.PythonActivity')
        BitmapFactory    = autoclass('android.graphics.BitmapFactory')
        CompressFormat   = autoclass('android.graphics.Bitmap$CompressFormat')
        FileOutputStream = autoclass('java.io.FileOutputStream')

        activity = PythonActivity.mActivity
        context  = activity.getApplicationContext()

        cache_dir = activity.getCacheDir().getAbsolutePath()
        self.temp_cache_file = os.path.join(cache_dir, 'kivy_display.jpg')

        istream = context.getContentResolver().openInputStream(
            self.temp_photo_uri)
        bitmap = BitmapFactory.decodeStream(istream)
        istream.close()

        if bitmap is None:
            self._cleanup_mediastore()
            return

        fos = FileOutputStream(self.temp_cache_file)
        bitmap.compress(CompressFormat.JPEG, 95, fos)
        fos.flush()
        fos.close()
        bitmap.recycle()

        # !
        # Verify file was written
        if not os.path.exists(self.temp_cache_file):
            self._cleanup_mediastore()
            return
        
        file_size = os.path.getsize(self.temp_cache_file)

        # Load image for board detection (same as use_selected_from_gallery)
        try:
            self.image = cv2.imread(self.temp_cache_file)
            if self.image is None:
                self._cleanup_mediastore()
                self._cleanup_all(None)
                return
            # Proceed with board detection
            Clock.schedule_once(self._process_photo, 0.0)
        except Exception as e:
            self._cleanup_mediastore()
            self._cleanup_all(None)
            return

    # ---------------------------------------------------------------- cleanup

    def _process_photo(self, dt):
        """Called after image is loaded - detect board then cleanup."""
        try:
            self.detect_board()
        except Exception as e:
            pass
        finally:
            Clock.schedule_once(self._cleanup_all, 0.1)


    def _cleanup_all(self, dt):
        if self.temp_cache_file and os.path.exists(self.temp_cache_file):
            try:
                os.remove(self.temp_cache_file)
            except OSError:
                pass
        self.temp_cache_file = None
        self._cleanup_mediastore()


    def _cleanup_mediastore(self):
        if self.temp_photo_uri is None:
            return
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity.getApplicationContext()
            context.getContentResolver().delete(
                self.temp_photo_uri, None, None)
        except Exception:
            pass
        self.temp_photo_uri = None

# --------------------------------------------------

if __name__ == '__main__':
    KingdomsApp().run()


# Your solution kinda works, but it is buggy. First, when screen switches to the gallery screen the app freezes as it still takes too much to list all the images and then sort and filter them. Also, Thumbnails are buggy and most of them are just black. Howerver selection works, so functionality is theoretically ok, just the user experience is terrible