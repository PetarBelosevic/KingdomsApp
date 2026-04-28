import os
import cv2
from kivy.clock import Clock

try:
    from android.permissions import request_permissions, Permission, check_permission
    from jnius import autoclass, cast
    ANDROID = True
except ImportError:
    ANDROID = False

CAMERA_REQUEST_CODE = 1001


class OneShotCamera:
    def __init__(self, app):
        if not ANDROID:
            raise RuntimeError("OneShotCamera is only available on Android")
        self.app = app
    
    
    # Camera intent methods (Android only) (from Claude)
    def start_camera(self, *args):
        """Checks for permissions, then launch camera intent to capture an image."""
        if not ANDROID:
            return
        if not check_permission(Permission.CAMERA):
            request_permissions([Permission.CAMERA])
            return
        try:
            self._launch_camera() # !
        except Exception:
            pass


    def _launch_camera(self):
        """Launches the camera intent to capture an image and save it to a temporary file."""
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

    def on_activity_result_callback(self, request_code, result_code, intent):
        """Handles results from camera intent, loads the captured image. Also handles cleanup of temporary files and media store entries."""
        Activity = autoclass('android.app.Activity')
        if result_code != Activity.RESULT_OK:
            if request_code == CAMERA_REQUEST_CODE:
                self._cleanup_mediastore()
            return
        try:
            self._load_photo() # !
        except Exception:
            self._cleanup_mediastore() # !


    def _load_photo(self):
        """Load photo from camera intent result, and initiates board detection."""
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
            self.app.image = cv2.imread(self.temp_cache_file)
            if self.app.image is None:
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
            self.app.detect_board()
        except Exception as e:
            pass
        finally:
            Clock.schedule_once(self._cleanup_all, 0.1)


    def _cleanup_all(self, dt):
        """Cleans up temporary files and media store entries after processing the captured image."""
        if self.temp_cache_file and os.path.exists(self.temp_cache_file):
            try:
                os.remove(self.temp_cache_file)
            except OSError:
                pass
        self.temp_cache_file = None
        self._cleanup_mediastore()


    def _cleanup_mediastore(self):
        """Deletes the temporary photo entry from the media store to prevent cluttering the user's gallery with temporary files."""
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