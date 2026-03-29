from jnius import autoclass, PythonJavaClass, java_method
try:
    from android import activity
    from android.permissions import request_permissions, Permission
    ANDROID = True
except ImportError:
    ANDROID = False

# Android classes
Context = autoclass('android.content.Context')
CameraManager = autoclass('android.hardware.camera2.CameraManager')
CameraDevice = autoclass('android.hardware.camera2.CameraDevice')
CaptureRequest = autoclass('android.hardware.camera2.CaptureRequest')
ImageReader = autoclass('android.media.ImageReader')
ImageFormat = autoclass('android.graphics.ImageFormat')


# -------------------------
# Image Listener
# -------------------------
class _ImageListener(PythonJavaClass):
    __javainterfaces__ = ['android/media/ImageReader$OnImageAvailableListener']
    __javacontext__ = 'app'

    def __init__(self, outer):
        super().__init__()
        self.outer = outer

    @java_method('()V')
    def onImageAvailable(self, reader):
        image = reader.acquireLatestImage()
        if not image:
            return

        plane = image.getPlanes()[0]
        buffer = plane.getBuffer()

        data = bytes(buffer.remaining())
        buffer.get(data)

        image.close()

        # Send result back to Python
        self.outer._on_image(data)


# -------------------------
# Camera Device Callback
# -------------------------
class _StateCallback(PythonJavaClass):
    __javainterfaces__ = ['android/hardware/camera2/CameraDevice$StateCallback']
    __javacontext__ = 'app'

    def __init__(self, outer):
        super().__init__()
        self.outer = outer

    @java_method('(Landroid/hardware/camera2/CameraDevice;)V')
    def onOpened(self, camera):
        self.outer.camera = camera
        self.outer._create_session()

    @java_method('(Landroid/hardware/camera2/CameraDevice;)V')
    def onDisconnected(self, camera):
        camera.close()

    @java_method('(Landroid/hardware/camera2/CameraDevice;I)V')
    def onError(self, camera, error):
        camera.close()


# -------------------------
# Capture Session Callback
# -------------------------
class _SessionCallback(PythonJavaClass):
    __javainterfaces__ = ['android/hardware/camera2/CameraCaptureSession$StateCallback']
    __javacontext__ = 'app'

    def __init__(self, outer):
        super().__init__()
        self.outer = outer

    @java_method('(Landroid/hardware/camera2/CameraCaptureSession;)V')
    def onConfigured(self, session):
        self.outer.session = session
        self.outer._take_picture()

    @java_method('(Landroid/hardware/camera2/CameraCaptureSession;)V')
    def onConfigureFailed(self, session):
        print("Camera session configuration failed")


# -------------------------
# Main Class
# -------------------------
class Camera2Capture:

    def __init__(self, width=1920*4, height=1080*4):
        self.context = activity.getApplicationContext()
        self.manager = self.context.getSystemService(Context.CAMERA_SERVICE)

        self.width = width
        self.height = height

        self.camera = None
        self.session = None
        self.reader = None

        self.callback = None

    # -------------------------
    # Public API
    # -------------------------
    def capture(self, callback):
        """
        Capture one image.
        callback(bytes) will be called with JPEG data.
        """
        self.callback = callback

        camera_id = self.manager.getCameraIdList()[0]

        # Setup ImageReader
        self.reader = ImageReader.newInstance(
            self.width,
            self.height,
            ImageFormat.JPEG,
            1
        )

        self.image_listener = _ImageListener(self)
        self.reader.setOnImageAvailableListener(self.image_listener, None)

        # Open camera
        self.state_cb = _StateCallback(self)
        self.manager.openCamera(camera_id, self.state_cb, None)

    # -------------------------
    # Internal pipeline
    # -------------------------
    def _create_session(self):
        surfaces = [self.reader.getSurface()]

        self.session_cb = _SessionCallback(self)

        self.camera.createCaptureSession(
            surfaces,
            self.session_cb,
            None
        )

    def _take_picture(self):
        builder = self.camera.createCaptureRequest(
            CameraDevice.TEMPLATE_STILL_CAPTURE
        )

        builder.addTarget(self.reader.getSurface())

        self.session.capture(
            builder.build(),
            None,
            None
        )

    def _on_image(self, data):
        if self.callback:
            self.callback(data)

        self._cleanup()

    # -------------------------
    # Cleanup
    # -------------------------
    def _cleanup(self):
        try:
            if self.session:
                self.session.close()
            if self.camera:
                self.camera.close()
            if self.reader:
                self.reader.close()
        except Exception as e:
            print("Cleanup error:", e)

        self.session = None
        self.camera = None
        self.reader = None





# from jnius import autoclass, PythonJavaClass, java_method, cast
# from android import activity

# # Android classes
# CameraManager = autoclass('android.hardware.camera2.CameraManager')
# ImageReader = autoclass('android.media.ImageReader')
# Surface = autoclass('android.view.Surface')
# ImageFormat = autoclass('android.graphics.ImageFormat')

# Context = autoclass('android.content.Context')


# class ImageListener(PythonJavaClass):
#     __javainterfaces__ = ['android/media/ImageReader$OnImageAvailableListener']
#     __javacontext__ = 'app'

#     def __init__(self, callback):
#         super().__init__()
#         self.callback = callback

#     @java_method('()V')
#     def onImageAvailable(self, reader):
#         image = reader.acquireLatestImage()
#         if image:
#             plane = image.getPlanes()[0]
#             buffer = plane.getBuffer()

#             # Convert Java ByteBuffer → Python bytes
#             data = bytes(buffer.remaining())
#             buffer.get(data)

#             image.close()

#             # Send to Python
#             self.callback(data)


# class CameraCapture:
#     def __init__(self):
#         self.context = activity.getApplicationContext()
#         self.manager = self.context.getSystemService(Context.CAMERA_SERVICE)

#     def capture_once(self, callback):
#         camera_id = self.manager.getCameraIdList()[0]

#         # Create ImageReader (full-res JPEG)
#         self.reader = ImageReader.newInstance(
#             1920, 1080,  # you can increase later
#             ImageFormat.JPEG,
#             1
#         )

#         self.listener = ImageListener(callback)
#         self.reader.setOnImageAvailableListener(self.listener, None)

#         # ⚠️ FULL Camera2 setup omitted here (next step)
#         print("Camera setup started (needs session wiring)")





# CameraDevice = autoclass('android.hardware.camera2.CameraDevice')
# CaptureRequest = autoclass('android.hardware.camera2.CaptureRequest')


# class StateCallback(PythonJavaClass):
#     __javainterfaces__ = ['android/hardware/camera2/CameraDevice$StateCallback']
#     __javacontext__ = 'app'

#     def __init__(self, outer):
#         super().__init__()
#         self.outer = outer

#     @java_method('(Landroid/hardware/camera2/CameraDevice;)V')
#     def onOpened(self, camera):
#         self.outer.camera = camera
#         self.outer.create_session()

#     @java_method('(Landroid/hardware/camera2/CameraDevice;)V')
#     def onDisconnected(self, camera):
#         camera.close()

#     @java_method('(Landroid/hardware/camera2/CameraDevice;I)V')
#     def onError(self, camera, error):
#         camera.close()


# class CameraCapture(CameraCapture):  # extend previous

#     def capture_once(self, callback):
#         super().capture_once(callback)

#         self.state_cb = StateCallback(self)
#         self.manager.openCamera(camera_id, self.state_cb, None)

#     def create_session(self):
#         surfaces = [self.reader.getSurface()]

#         def on_configured(session):
#             self.session = session
#             self.take_picture()

#         SessionCallback = autoclass(
#             'android.hardware.camera2.CameraCaptureSession$StateCallback'
#         )

#         # ⚠️ In real code you'd wrap this properly with PythonJavaClass
#         self.camera.createCaptureSession(
#             surfaces,
#             None,
#             None
#         )

#     def take_picture(self):
#         request_builder = self.camera.createCaptureRequest(
#             CameraDevice.TEMPLATE_STILL_CAPTURE
#         )

#         request_builder.addTarget(self.reader.getSurface())

#         self.session.capture(
#             request_builder.build(),
#             None,
#             None
#         )