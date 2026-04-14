import os
import cv2
from kivy.clock import Clock

try:
    from android.permissions import request_permissions, Permission, check_permission
    from jnius import autoclass
    ANDROID = True
except ImportError:
    ANDROID = False

GALLERY_REQUEST_CODE = 1002


class GalleryPhotoPicker:
    def __init__(self, app):
        if not ANDROID:
            raise RuntimeError("GalleryPhotoPicker is only available on Android")
        self.app = app
    
    # image retrieval methods via custom gallery 
    # idea from https://groups.google.com/g/kivy-users/c/bjsG2j9bptI/m/-Oe_aGo0newJ
    def start_gallery(self, *args):
        """Checks for permissions, then launch gallery intent to pick an image."""
        if not ANDROID:
            return
        has_perm = check_permission(Permission.READ_EXTERNAL_STORAGE) or check_permission(Permission.READ_MEDIA_IMAGES)
        if not has_perm:
            request_permissions([Permission.READ_MEDIA_IMAGES, Permission.READ_EXTERNAL_STORAGE])
            return
        try:
            self._launch_gallery()
        except Exception as e:
            pass


    def _launch_gallery(self):
        """Launches the gallery intent to pick an image from the device."""
        Intent         = autoclass('android.content.Intent')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity

        self.activity = activity

        intent = Intent()
        intent.setAction(Intent.ACTION_PICK)
        intent.setType("image/*")

        activity.startActivityForResult(intent, GALLERY_REQUEST_CODE)

    
    def on_activity_result_callback(self, request_code, result_code, intent):
        """Handles results from gallery intent, loads the selected image."""
        Activity = autoclass('android.app.Activity')
        if result_code != Activity.RESULT_OK:
            return
        try:
            self._load_photo_from_gallery(intent) # !
        except Exception:
            pass

    
    def _load_photo_from_gallery(self, intent):
        """Load photo from gallery intent result, gives it to the app and starts board detection."""
        if intent is None:
            return
        
        MediaStore_Images_Media_DATA = "_data"
        currentActivity = self.activity
        selectedImage = intent.getData()
        if selectedImage is None:
            return

        filePathColumn = [MediaStore_Images_Media_DATA]
        cursor = currentActivity.getContentResolver().query(selectedImage, filePathColumn, None, None, None)
        if cursor is None:
            return
        if not cursor.moveToFirst():
            cursor.close()
            return

        columnIndex = cursor.getColumnIndex(filePathColumn[0])
        if columnIndex < 0:
            cursor.close()
            return
        
        picturePath = cursor.getString(columnIndex)
        cursor.close()
        if not picturePath or not os.path.exists(picturePath):
            return

        self.app.image = cv2.imread(picturePath)
        if self.app.image is None:
            return

        Clock.schedule_once(lambda dt: self.app.detect_board(), 0.0)