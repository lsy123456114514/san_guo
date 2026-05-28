[app]
title = 三国霸业
package.name = sangoheroes
package.domain = org.sangoheroes
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,json,so,dll
source.exclude_dirs = build, dist, __pycache__,Output
version = 1.0.0

android.api = 33
android.permissions = INTERNET,WAKE_LOCK,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA
android.fullscreen = 1
android.icon = data/icon.png
android.presplash = data/splash.png

requirements = python3,kivy,pygame,pygame_sdl2,numpy,requests,pillow,pyjnius

orientation = landscape

android.add_assets = ASSET/ data/

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.enable_androidx = True
android.buildtools = 33.0.0
android.minapi = 21
android.maxapi = 33

android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

android.add_libs = libopengl_renderer.so