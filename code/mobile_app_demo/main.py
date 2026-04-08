import os
import cv2
# import numpy as np
# import time


from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from kivy.resources import resource_find
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.anchorlayout import AnchorLayout

from kivy.properties import StringProperty

from kivy.uix.popup import Popup
from kivy.uix.label import Label
import traceback

# from mobile_app_demo.camera import OneShotCamera

# if platform == "android":
#     from jnius import autoclass, cast
#     from android import activity, mActivity

#     Activity = autoclass('android.app.Activity')
#     Intent = autoclass('android.content.Intent')
#     MediaStore = autoclass('android.provider.MediaStore')
#     Environment = autoclass('android.os.Environment')
#     File = autoclass('java.io.File')
#     FileProvider = autoclass('androidx.core.content.FileProvider')

try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.activity import bind as activity_bind
    from jnius import autoclass, cast
    ANDROID = True
except ImportError:
    ANDROID = False
CAMERA_REQUEST_CODE = 1001

# from camera import OneShotCamera



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
    demo_text = StringProperty("demo")

    def set_status(self, msg):
        print(f'[CameraApp] {msg}')
        self.demo_text = msg


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.game_data = JsonStore(os.path.join(self.app_dir, "game_data.json"))


    def build(self):
        self.android = platform == "android"
        if self.android:
        #     from camera import Camera2Capture
        #     self.camera_class = Camera2Capture
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA])
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


    def go_to_demo(self, dt):
        self._go_to_default("demo", "left")


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

    def take_picture(self):
        self.start_camera()
        self.go_to("demo", "left")


    def on_gallery_selection(self, selection):
        self._pending_gallery_selection = selection[0] if selection else ""


    def use_selected_from_gallery(self):
        cv2 = self._get_cv2()
        if cv2 is None:
            return

        if not self._pending_gallery_selection:
            self.processing_status = "No image selected yet."
            return

        self.selected_image_path = self._pending_gallery_selection
        self.image = cv2.imread(self.selected_image_path)
        self._pending_gallery_selection = ""
        self.detect_board()

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



    # def detect_board(self):
    #     # from image_processing import rectify_image

    #     # self.image = rectify_image(self.image)
    #     self._go_to_default("detected_board", "left")
    #     self.show_image(self.image)

    # --------------------------------------------------

    # Camera intent methods (Android only)
    # --------------------------------------------------- launch camera intent

    def start_camera(self, *args):
        if not ANDROID:
            self.set_status('Android only.')
            return
        if not check_permission(Permission.CAMERA):
            self.set_status('Camera permission denied.')
            request_permissions([Permission.CAMERA])
            return
        try:
            self._launch_camera()
        except Exception:
            err = traceback.format_exc()
            print(err)
            self.set_status(f'Error:\n{err[-400:]}')


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
            self.set_status('Error: MediaStore.insert() returned null.\n'
                            'Check WRITE_EXTERNAL_STORAGE on Android < 10.')
            return

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        # Cast Uri → Parcelable so pyjnius picks the right putExtra() overload
        intent.putExtra(MediaStore.EXTRA_OUTPUT, cast('android.os.Parcelable', self.temp_photo_uri))

        activity.startActivityForResult(intent, CAMERA_REQUEST_CODE)
        self.set_status('Camera open — take your photo...')

    # --------------------------------------------------- activity result back

    def on_activity_result(self, request_code, result_code, data):
        self.set_status('Returned from camera intent, processing result...')

        if request_code != CAMERA_REQUEST_CODE:
            return
        Activity = autoclass('android.app.Activity')
        if result_code != Activity.RESULT_OK:
            self._cleanup_mediastore()
            self.set_status('Photo cancelled.')
            return
        try:
            self._load_photo()
        except Exception:
            err = traceback.format_exc()
            print(err)
            self.set_status(f'Load error:\n{err[-400:]}')
            self._cleanup_mediastore()


    def _load_photo(self):
        self.set_status('Decoding photo...')

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
            self.set_status('Error: BitmapFactory returned null.')
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
            self.set_status('Error: Cache file not created.')
            self._cleanup_mediastore()
            return
        
        file_size = os.path.getsize(self.temp_cache_file)
        self.set_status(f'Cache file created: {file_size} bytes. Loading with cv2...')

        # Load image for board detection (same as use_selected_from_gallery)
        try:
            self.image = cv2.imread(self.temp_cache_file)
            if self.image is None:
                self.set_status('Error: cv2.imread returned None.')
                self._cleanup_mediastore()
                self._cleanup_all(None)
                return
            self.set_status(f'Image loaded: {self.image.shape}. Cleaning up in 1 s...')
        except Exception as e:
            self.set_status(f'Error loading image: {str(e)[:100]}')
            print(f'cv2.imread error: {traceback.format_exc()}')
            self._cleanup_mediastore()
            self._cleanup_all(None)
            return
        # !

        Clock.schedule_once(self._cleanup_all, 1.0)

    # ---------------------------------------------------------------- cleanup

    def _cleanup_all(self, dt):
        if self.temp_cache_file and os.path.exists(self.temp_cache_file):
            try:
                os.remove(self.temp_cache_file)
            except OSError:
                pass
        self.temp_cache_file = None
        self._cleanup_mediastore()
        self.set_status('Photo displayed (temp files deleted).')


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
