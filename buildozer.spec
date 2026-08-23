[app]

# JARVIS nomi
title = JARVIS

# Android paket nomi
package.name = jarvis

# Paket domeni
package.domain = org.jarvis

# Asosiy loyiha papkasi
source.dir = .

# Loyihaga kiritiladigan fayllar
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,wav,mp3

# Asosiy Python fayl
source.main = main.py

# Versiya
version = 1.0

# Python + Kivy
requirements = python3,kivy

# Telefon yo'nalishi
orientation = portrait

# Android ruxsatlari
android.permissions = INTERNET,RECORD_AUDIO

# Faqat ARM64
android.archs = arm64-v8a

# Android API
android.api = 35

# Minimal Android API
android.minapi = 21

# Android NDK
android.ndk = 27c

# SDK license avtomatik qabul qilinsin
android.accept_sdk_license = True

# Kivy Android Activity
android.entrypoint = org.kivy.android.PythonActivity

# Fullscreen emas
fullscreen = 0

# Log darajasi
log_level = 2


[buildozer]

# Buildozer log darajasi
log_level = 2

# Root bilan ishlashga ruxsat
warn_on_root = 1