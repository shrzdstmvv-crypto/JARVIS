import importlib
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import selfupdate

# Yangi build bo'lsa overlay (o'zgartirishlar) yangi kod bilan birlashtiriladi.
# Oldingi ishga tushish yiqilgan bo'lsa: overlay o'chiriladi yoki klassik
# ko'rinishga o'tiladi. Foydalanuvchiga ko'rsatiladigan xabar qaytariladi.
BOOT_MESSAGE = selfupdate.prepare()


def _add(message, extra):
    return (message + " " + extra).strip() if message else extra


ui_name = "jarvis_app_classic" if selfupdate.USE_CLASSIC else "jarvis_app"

try:
    ui = importlib.import_module(ui_name)
except Exception as error:
    # O'zgartirilgan kod ochilmadi: asl holatga qaytib qayta urinamiz
    BOOT_MESSAGE = _add(BOOT_MESSAGE, selfupdate.import_failed(error))

    try:
        ui = importlib.import_module(ui_name)
    except Exception:
        if ui_name == "jarvis_app_classic":
            raise

        # Yangi ko'rinish ochilmadi: klassik ko'rinishga o'tamiz
        selfupdate.mark_ui_failed()
        BOOT_MESSAGE = _add(
            BOOT_MESSAGE,
            "Yangi ko'rinish ochilmadi, klassik ko'rinishda ochildi. "
            "Qayta sinash: terminalda ui(\"new\")."
        )
        ui = importlib.import_module("jarvis_app_classic")

ui.BOOT_MESSAGE = BOOT_MESSAGE

if __name__ == "__main__":
    ui.JarvisApp().run()
