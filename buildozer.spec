[app]

# ==========================================================
# JARVIS 6.0
# ==========================================================

title = JARVIS

package.name = jarvis

package.domain = org.jarvis

source.dir = .

source.include_exts = py,json,png,jpg,jpeg,wav,mp3

version = 6.0

requirements = python3,kivy,pyjnius

orientation = portrait

fullscreen = 0


# ==========================================================
# ANDROID
# ==========================================================

android.api = 33

android.minapi = 21

android.sdk = 33

android.ndk = 25b


# ==========================================================
# ANDROID PERMISSIONS
# ==========================================================

android.permissions = RECORD_AUDIO,CAMERA,INTERNET


# ==========================================================
# ANDROID FEATURES
# ==========================================================

android.archs = arm64-v8a

android.allow_backup = True

android.copy_libs = 1


# ==========================================================
# STARTUP
# ==========================================================

# JARVIS uchun asosiy fayl
entrypoint = main.py


# ==========================================================
# PRESPLASH
# ==========================================================

presplash.filename = %(source.dir)s/assets/presplash.png


# ==========================================================
# ICON
# ==========================================================

icon.filename = %(source.dir)s/assets/icon.png


# ==========================================================
# BUILD
# ==========================================================

android.accept_sdk_license = True

android.enable_androidx = True


[buildozer]

# ==========================================================
# LOG LEVEL
# ==========================================================

log_level = 2

warn_on_root = 1