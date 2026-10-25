import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import selfupdate

# Overlay (o'zgartirilgan kod) bo'lsa yoqiladi. Oldingi ishga tushish
# yiqilgan bo'lsa, overlay o'chiriladi va xabar qaytariladi.
BOOT_MESSAGE = selfupdate.prepare()

try:
    import jarvis_app
except Exception as error:
    # O'zgartirilgan kod ochilmadi: asl holatga qaytamiz
    BOOT_MESSAGE = selfupdate.import_failed(error)
    import jarvis_app

jarvis_app.BOOT_MESSAGE = BOOT_MESSAGE

if __name__ == "__main__":
    jarvis_app.JarvisApp().run()
