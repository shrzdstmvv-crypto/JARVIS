[app]

title = JARVIS
package.name = jarvis
package.domain = org.jarvis

source.dir = .
source.include_exts = py,json,png,jpg,jpeg,wav,mp3,kv

version = 6.0
requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/jarvis_icon.png

android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.archs = arm64-v8a

android.permissions = RECORD_AUDIO,CAMERA,INTERNET

android.accept_sdk_license = True
android.enable_androidx = True
android.allow_backup = True
android.copy_libs = 1

[buildozer]

log_level = 2
warn_on_root = 1