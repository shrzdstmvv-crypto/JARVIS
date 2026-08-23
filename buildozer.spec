[app]

# JARVIS ilovasi
title = JARVIS

# Paket nomi
package.name = jarvis

# Paket domeni
package.domain = org.jarvis

# JARVIS papkasi
source.dir = .

# Kiradigan fayllar
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,wav,mp3

# Asosiy fayl
source.main = main.py

# Versiya
version = 1.0

# Python va Kivy
requirements = python3,kivy

# Ekran yo'nalishi
orientation = portrait

# Android ruxsatlari
android.permissions = INTERNET,RECORD_AUDIO

# Android arxitekturasi
android.archs = arm64-v8a

# Android API
android.api = 35

# Minimal Android versiyasi
android.minapi = 21

# Android NDK
android.ndk = 27c

# Android ilova nomi
android.entrypoint = org.kivy.android.PythonActivity

# Ilova oynasi
fullscreen = 0

# Loglar
log_level = 2


[buildozer]

# Log darajasi
log_level = 2

# Warning
warn_on_root = 1