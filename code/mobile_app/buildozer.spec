[app]

title        = Kingdoms by Reiner Knizia
package.name = kingdomsapp
package.domain = org.test

source.dir  = .
source.include_exts = py,png,jpg,kv,atlas,json,onnx,data
source.include_patterns = onnx_models/*

version = 1.0

requirements = python3,kivy,pyjnius,android,numpy,opencv,pillow
android.gradle_dependencies = com.microsoft.onnxruntime:onnxruntime-android:1.22.0

orientation = portrait

android.minapi   = 26
android.api      = 34
android.ndk_api  = 26
android.archs    = arm64-v8a

# CAMERA          - launch ACTION_IMAGE_CAPTURE
# WRITE_EXTERNAL_STORAGE - insert into MediaStore on Android 8-9 (API < 29)
#                  On Android 10+ this permission is ignored by the OS
#                  (not needed for own MediaStore entries) but harmless to list.
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, MANAGE_MEDIA, READ_MEDIA_IMAGES

fullscreen = 0

# [buildozer]
# log_level = 2
# warn_on_root = 1
