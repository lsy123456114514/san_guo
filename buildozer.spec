[app]
title = 三国霸业
package.name = sangoheroes
package.domain = org.sangoheroes
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,json
source.exclude_dirs = build, dist, __pycache__,Output
version = 1.0.0

android.api = 33
android.permissions = INTERNET,WAKE_LOCK,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.fullscreen = 1
android.icon = data/icon.png
android.presplash = data/splash.png

requirements = python3,kivy

orientation = landscape

[buildozer]
log_level = 2
warn_on_root = 1