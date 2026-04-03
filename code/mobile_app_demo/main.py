import os
# import numpy as np
# import cv2

from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.resources import resource_find
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.popup import Popup

# from camera import Camera2Capture

# --------------------------------------------------

class RootScreenManager(ScreenManager):
    pass

class StartScreen(Screen):
    pass

class ImageMethodScreen(Screen):
    pass

# --------------------------------------------------

class GameInfoPopup(AnchorLayout):
    pass

# --------------------------------------------------

class KingdomsApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.game_data = JsonStore(os.path.join(self.app_dir, "game_data.json"))


    def build(self):
        self.android = platform == "android"
        if self.android:
            from camera import Camera2Capture
            self.camera_class = Camera2Capture

            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA])


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
    # image retrieval methods # TODO 

    def take_new_photo(self): # TODO
        # open camera and take photo, then save to temp file and set selected_image_path
        # print("Open camera and take photo")
        if not self.android:
            print("Camera capture is only available on Android.")
            return

        # !
        from android.permissions import check_permission, Permission, request_permissions
        if not check_permission(Permission.CAMERA):
            request_permissions([Permission.CAMERA])
            # print("Camera permission requested. Tap again after granting permission.")
            return
        # !

        self.camera_capture = self.camera_class()
        self.camera_capture.capture(self.save_image)
        # self.detect_board()


    # def on_gallery_selection(self, selection):
    #     self._pending_gallery_selection = selection[0] if selection else ""


    # def use_selected_from_gallery(self):
    #     cv2 = self._get_cv2()
    #     if cv2 is None:
    #         return

    #     if not self._pending_gallery_selection:
    #         self.processing_status = "No image selected yet."
    #         return

    #     self.selected_image_path = self._pending_gallery_selection
    #     self.image = cv2.imread(self.selected_image_path)
    #     self._pending_gallery_selection = ""
    #     self.detect_board()

    # --------------------------------------------------
    # image display

    # def show_image(self, image):
    #     # cv2 = self._get_cv2()
    #     # if cv2 is None:
    #     #     return

    #     frame = image  # your cv2 image (numpy array)
    #     # 1. Convert BGR → RGB
    #     buf = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     # 2. Flip vertically
    #     buf = cv2.flip(buf, 0)
    #     # 3. Convert to bytes
    #     buf = buf.tobytes()
    #     # 4. Create texture
    #     texture = Texture.create(
    #         size=(frame.shape[1], frame.shape[0]),
    #         colorfmt='rgb'
    #     )
    #     # 5. Blit buffer
    #     texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
    #     # 6. Display in Image widget
    #     screen = self.root.get_screen("detected_board")
    #     screen.ids.board.texture = texture

    # --------------------------------------------------
    # data processing methods
    def save_image(self, data):
        # !
        # Camera callback can arrive off the main thread; schedule UI work safely.
        Clock.schedule_once(lambda dt: self._go_to_default("demo", "left"), 0)
        # !
        
        # convert bytes to cv2 image
        # nparr = np.frombuffer(data, np.uint8)
        # self.image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)


    # def detect_board(self):
    #     # from image_processing import rectify_image

    #     # self.image = rectify_image(self.image)
    #     self._go_to_default("detected_board", "left")
    #     self.show_image(self.image)

    # --------------------------------------------------


# --------------------------------------------------

if __name__ == '__main__':
    KingdomsApp().run()
