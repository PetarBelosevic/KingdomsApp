import os
import traceback
from kivy.clock import Clock

try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.activity import bind as activity_bind
    from jnius import autoclass, cast
    ANDROID = True
except ImportError:
    ANDROID = False


from kivy.uix.popup import Popup
from kivy.uix.label import Label


CAMERA_REQUEST_CODE = 1001


class OneShotCamera:
    def __init__(self, app):
        if not ANDROID:
            raise RuntimeError("OneShotCamera is only available on Android")
        self.app = app
        activity_bind(on_activity_result=self.on_activity_result)
        Build_VERSION = autoclass('android.os.Build$VERSION')
        perms = [Permission.CAMERA]
        if Build_VERSION.SDK_INT < 29:
            perms.append(Permission.WRITE_EXTERNAL_STORAGE)
        if not all(check_permission(p) for p in perms):
            request_permissions(perms)


    def set_status(self, msg):
        print(f'[CameraApp] {msg}')
        self.app.demo_text = msg


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
        # ── KEY FIX ───────────────────────────────────────────────────────────
        # Column name constants (DISPLAY_NAME, MIME_TYPE, RELATIVE_PATH) are
        # declared on MediaStore$MediaColumns, NOT on MediaStore$Images$Media.
        # pyjnius does NOT resolve inherited static fields through subclasses,
        # so MediaImages.DISPLAY_NAME returns None → "Invalid column" crash.
        # Always use the declaring class for static constants.
        MediaColumns   = autoclass('android.provider.MediaStore$MediaColumns')
        # ─────────────────────────────────────────────────────────────────────
        ContentValues  = autoclass('android.content.ContentValues')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Build_VERSION  = autoclass('android.os.Build$VERSION')

        activity = PythonActivity.mActivity
        context  = activity.getApplicationContext()

        self.set_status('Building ContentValues...')

        values = ContentValues()
        # Use MediaColumns (declaring class) — these now resolve correctly
        values.put(MediaColumns.DISPLAY_NAME, 'kivy_temp_photo.jpg')
        values.put(MediaColumns.MIME_TYPE,    'image/jpeg')
        if Build_VERSION.SDK_INT >= 29:
            # RELATIVE_PATH is also declared on MediaColumns (API 29+)
            values.put(MediaColumns.RELATIVE_PATH, 'Pictures/KivyTemp')

        self.set_status('Inserting into MediaStore...')

        self.temp_photo_uri = context.getContentResolver().insert(
            MediaImages.EXTERNAL_CONTENT_URI, values)

        if self.temp_photo_uri is None:
            self.set_status('Error: MediaStore.insert() returned null.\n'
                            'Check WRITE_EXTERNAL_STORAGE on Android < 10.')
            return

        self.set_status(f'URI OK: {self.temp_photo_uri.toString()[:60]}')

        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        # Cast Uri → Parcelable so pyjnius picks the right putExtra() overload
        intent.putExtra(MediaStore.EXTRA_OUTPUT,
                        cast('android.os.Parcelable', self.temp_photo_uri))

        activity.startActivityForResult(intent, CAMERA_REQUEST_CODE)
        self.set_status('Camera open — take your photo...')

    # --------------------------------------------------- activity result back

    def on_activity_result(self, request_code, result_code, data):
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

        self.set_status('Photo loaded! Cleaning up in 1 s...')
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








    # def capture(self):
    #     if not ANDROID:
    #         return
    #     if not check_permission(Permission.CAMERA):
    #         request_permissions([Permission.CAMERA])
    #         return
    #     try:
    #         self._launch_camera()
    #     except Exception:
    #         pass


    # def _launch_camera(self):
    #     Intent         = autoclass('android.content.Intent')
    #     MediaStore     = autoclass('android.provider.MediaStore')
    #     MediaImages    = autoclass('android.provider.MediaStore$Images$Media')
    #     MediaColumns   = autoclass('android.provider.MediaStore$MediaColumns')
    #     ContentValues  = autoclass('android.content.ContentValues')
    #     PythonActivity = autoclass('org.kivy.android.PythonActivity')
    #     Build_VERSION  = autoclass('android.os.Build$VERSION')

    #     activity = PythonActivity.mActivity
    #     context  = activity.getApplicationContext()

    #     values = ContentValues()
    #     # Use MediaColumns (declaring class)
    #     values.put(MediaColumns.DISPLAY_NAME, 'kivy_temp_photo.jpg')
    #     values.put(MediaColumns.MIME_TYPE,    'image/jpeg')
    #     if Build_VERSION.SDK_INT >= 29:
    #         # RELATIVE_PATH is also declared on MediaColumns (API 29+)
    #         values.put(MediaColumns.RELATIVE_PATH, 'Pictures/KivyTemp')

    #     self.temp_photo_uri = context.getContentResolver().insert(MediaImages.EXTERNAL_CONTENT_URI, values)

    #     if self.temp_photo_uri is None:
    #         return

    #     intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
    #     # Cast Uri -> Parcelable so pyjnius picks the right putExtra() overload
    #     intent.putExtra(MediaStore.EXTRA_OUTPUT, cast('android.os.Parcelable', self.temp_photo_uri))

    #     activity.startActivityForResult(intent, CAMERA_REQUEST_CODE)



    # def on_activity_result(self, request_code, result_code, data):
    #     if request_code != CAMERA_REQUEST_CODE:
    #         return
    #     Activity = autoclass('android.app.Activity')
    #     if result_code != Activity.RESULT_OK:
    #         self._cleanup_mediastore()
    #         return
    #     try:
    #         self._load_photo()
    #     except Exception:
    #         self._cleanup_mediastore()


    # def _load_photo(self):
    #     PythonActivity   = autoclass('org.kivy.android.PythonActivity')
    #     BitmapFactory    = autoclass('android.graphics.BitmapFactory')
    #     CompressFormat   = autoclass('android.graphics.Bitmap$CompressFormat')
    #     FileOutputStream = autoclass('java.io.FileOutputStream')

    #     activity = PythonActivity.mActivity
    #     context  = activity.getApplicationContext()

    #     cache_dir = activity.getCacheDir().getAbsolutePath()
    #     self.temp_cache_file = os.path.join(cache_dir, 'kivy_display.jpg')

    #     istream = context.getContentResolver().openInputStream(
    #         self.temp_photo_uri)
    #     bitmap = BitmapFactory.decodeStream(istream)
    #     istream.close()

    #     if bitmap is None:
    #         self._cleanup_mediastore()
    #         return

    #     fos = FileOutputStream(self.temp_cache_file)
    #     bitmap.compress(CompressFormat.JPEG, 95, fos)
    #     fos.flush()
    #     fos.close()

    #     # self.app.image = bitmap

    #     bitmap.recycle()

    #     self._cleanup_all()


    # def _load_photo2(self):

    #     popup = Popup(title="Hello", content=Label(text=f"Entered _load_photo"), size_hint=(0.8, 0.8))
    #     popup.open()

    #     PythonActivity   = autoclass('org.kivy.android.PythonActivity')
    #     BitmapFactory    = autoclass('android.graphics.BitmapFactory')
    #     ByteArrayOutputStream = autoclass('java.io.ByteArrayOutputStream')

    #     activity = PythonActivity.mActivity
    #     context  = activity.getApplicationContext()

    #     istream = context.getContentResolver().openInputStream(self.temp_photo_uri)
    #     bitmap = BitmapFactory.decodeStream(istream)
    #     istream.close()

    #     popup = Popup(title="Hello", content=Label(text=f"Here!"), size_hint=(0.8, 0.8))
    #     popup.open()

    #     if bitmap is None:
    #         self._cleanup_mediastore()
    #         return

    #     baos = ByteArrayOutputStream()
    #     CompressFormat = autoclass('android.graphics.Bitmap$CompressFormat')
    #     bitmap.compress(CompressFormat.PNG, 100, baos)  # lossless, keeps full data
    #     bitmap.recycle()
    #     byte_array = baos.toByteArray()
    #     baos.close()

    #     # import numpy as np
    #     # import io
    #     # from PIL import Image as PILImage

    #     png_bytes = bytes(byte_array)
    #     # pil_img   = PILImage.open(io.BytesIO(png_bytes)).convert('RGB')
    #     # numpy_img = np.array(pil_img)       # shape: (height, width, 3), dtype uint8

    #     # Hand off to your external object
    #     # self.app = numpy_img
    #     self.app = png_bytes

    #     self._cleanup_mediastore()

    #     # frame_bgr = cv2.imread(self.temp_cache_file, cv2.IMREAD_COLOR) # HxWx3 uint8, BGR
    #     # if frame_bgr is None:
    #     #     self._cleanup_mediastore()
    #     #     return

    #     # frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB) # HxWx3 uint8, RGB
    #     # self.app.image = frame_rgb

    #     # bitmap.recycle()
    #     # Clock.schedule_once(self._cleanup_all, 1.0)



    # def _cleanup_all(self):
    #     if self.temp_cache_file and os.path.exists(self.temp_cache_file):
    #         try:
    #             os.remove(self.temp_cache_file)
    #         except OSError:
    #             pass
    #     self.temp_cache_file = None
    #     self._cleanup_mediastore()


    # def _cleanup_mediastore(self):
    #     if self.temp_photo_uri is None:
    #         return
    #     try:
    #         PythonActivity = autoclass('org.kivy.android.PythonActivity')
    #         context = PythonActivity.mActivity.getApplicationContext()
    #         context.getContentResolver().delete(self.temp_photo_uri, None, None)
    #     except Exception:
    #         pass
    #     self.temp_photo_uri = None
