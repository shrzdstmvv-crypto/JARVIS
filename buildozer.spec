[app]

title = JARVIS
package.name = jarvis
package.domain = org.jarvis

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,wav,mp3

source.main = main.py

version = 1.0

# ==============================
# PYTHON + KIVY
# ==============================
requirements = python3,kivy

orientation = portrait

# ==============================
# JARVIS ANDROID PERMISSIONS
# ==============================
android.permissions = INTERNET,RECORD_AUDIO,CAMERA,VIBRATE

# ==============================
# ARCHITECTURE
# ==============================
android.archs = arm64-v8a

# ==============================
# ANDROID
# ==============================
android.api = 35
android.minapi = 21
android.ndk = 27c

android.accept_sdk_license = True

# ==============================
# KIVY ACTIVITY
# ==============================
android.entrypoint = org.kivy.android.PythonActivity

fullscreen = 0

log_level = 2


[buildozer]

log_level = 2
warn_on_root = 1