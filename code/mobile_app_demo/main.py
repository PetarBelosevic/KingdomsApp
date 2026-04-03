import os

from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.resources import resource_find
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.popup import Popup

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
        print("Open camera and take photo")
        # from camera import Camera2Capture

        # camera = Camera2Capture()
        # camera.capture(self.detect_board)


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

if __name__ == '__main__':
    KingdomsApp().run()
