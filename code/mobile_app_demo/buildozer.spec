[app]

title        = KivyCameraTest
package.name = camerademo
package.domain = com.example

source.dir  = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

requirements = python3,kivy,pyjnius,android,numpy,opencv,pillow
# ,pillow

orientation = portrait

android.minapi   = 26
android.api      = 33
android.ndk_api  = 26
android.archs    = arm64-v8a

# CAMERA          - launch ACTION_IMAGE_CAPTURE
# WRITE_EXTERNAL_STORAGE - insert into MediaStore on Android 8-9 (API < 29)
#                  On Android 10+ this permission is ignored by the OS
#                  (not needed for own MediaStore entries) but harmless to list.
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE

fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
