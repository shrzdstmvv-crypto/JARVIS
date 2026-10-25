
"""JARVIS o'z-o'zini yangilash tizimi.

Ilova kodi APK ichida turadi va o'zgarmaydi. O'zgartirishlar esa
doimiy papkadagi "overlay" papkasiga yoziladi: u yerdagi fayl APK
ichidagi bir xil nomli fayl o'rnini egallaydi. Ilova yangilanganda
overlay o'chmaydi. Xato o'zgarish ilovani yiqitsa, keyingi ishga
tushishda overlay avtomatik o'chiriladi va ilova asl holida ochiladi.
"""

import importlib
import json
import os
import shutil
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tiklash vositalari: ularni overlay orqali o'zgartirib bo'lmaydi
PROTECTED = {"selfupdate", "terminal", "main"}


# PAPKALAR
def data_dir():
    custom = os.environ.get("JARVIS_DATA_DIR")

    if custom:
        base = custom
    else:
        try:
            from android.storage import app_storage_path
            base = os.path.join(app_storage_path(), "JARVIS")
        except Exception:
            base = os.path.join(BASE_DIR, "_jarvis_data")

    os.makedirs(base, exist_ok=True)
    return base


def overlay_dir():
    return os.path.join(data_dir(), "overlay")


def skills_dir():
    path = os.path.join(data_dir(), "skills")
    os.makedirs(path, exist_ok=True)
    return path


def _marker():
    return os.path.join(data_dir(), "boot_pending")


def _error_file():
    return os.path.join(data_dir(), "last_boot_error.txt")


def _overlay_files():
    path = overlay_dir()

    if not os.path.isdir(path):
        return []

    return sorted(f for f in os.listdir(path) if f.endswith(".py"))


# ISHGA TUSHIRISH VA YIQILISHDAN HIMOYA
def prepare():
    """Ilova ochilishidan oldin chaqiriladi.

    Overlay'ni yoqadi. Oldingi ishga tushish tugallanmagan bo'lsa
    (ilova yiqilgan), overlay'ni o'chirib, xabar qaytaradi.
    """
    files = _overlay_files()

    if os.path.exists(_marker()):
        if files:
            return disable_overlay(
                "Oxirgi o'zgartirish ilovani ishga tushirmadi, "
                "shuning uchun bekor qilindi. Eski holatga qaytdim."
            )

        _remove(_marker())

    if files:
        _write(_marker(), str(time.time()))

        if overlay_dir() not in sys.path:
            sys.path.insert(0, overlay_dir())

    return None


def boot_ok():
    """Ilova muvaffaqiyatli ochilgach chaqiriladi."""
    _remove(_marker())


def disable_overlay(reason):
    path = overlay_dir()
    broken = path + "_broken"

    if path in sys.path:
        sys.path.remove(path)

    try:
        if os.path.isdir(broken):
            shutil.rmtree(broken)

        if os.path.isdir(path):
            os.rename(path, broken)
    except Exception as error:
        print("Overlay disable error:", error)

    _remove(_marker())
    _purge_overlay_modules(path)
    _write(_error_file(), reason)
    return reason + " (fayllar overlay_broken papkasida saqlandi)"


def import_failed(error):
    """Overlay'dagi kod import paytida xato bergan bo'lsa."""
    return disable_overlay(
        "O'zgartirilgan kod ochilmadi: " + repr(error)[:200]
        + ". Eski holatga qaytdim."
    )


def _purge_overlay_modules(path):
    for name, module in list(sys.modules.items()):
        file = getattr(module, "__file__", None) or ""

        if file.startswith(path):
            del sys.modules[name]

    importlib.invalidate_caches()


# O'ZGARTIRISH VOSITALARI
def _valid_name(name):
    name = str(name).strip()

    if name.endswith(".py"):
        name = name[:-3]

    if not name or not name.replace("_", "").isalnum():
        raise ValueError("Modul nomi noto'g'ri: " + repr(name))

    return name


def modules():
    """O'zgartirish mumkin bo'lgan modullar ro'yxati."""
    names = set()

    for file in os.listdir(BASE_DIR):
        if file.endswith(".py"):
            names.add(file[:-3])

    names.update(f[:-3] for f in _overlay_files())
    return sorted(n for n in names if n not in PROTECTED)


def source(name):
    name = _valid_name(name)
    overlay_file = os.path.join(overlay_dir(), name + ".py")
    bundled_file = os.path.join(BASE_DIR, name + ".py")

    for path in (overlay_file, bundled_file):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                return file.read()

    raise FileNotFoundError(
        name + ".py topilmadi (ilova ichida manba fayl bo'lmasligi mumkin)"
    )


def save(name, code):
    name = _valid_name(name)

    if name in PROTECTED:
        raise ValueError(name + " modulini o'zgartirib bo'lmaydi (himoyalangan).")

    code = str(code)
    compile(code, name + ".py", "exec")  # sintaksis xatosi bo'lsa to'xtaydi

    os.makedirs(overlay_dir(), exist_ok=True)
    target = os.path.join(overlay_dir(), name + ".py")

    if os.path.exists(target):
        shutil.copyfile(target, target + ".bak")

    _write(target, code)
    _remove(_error_file())

    if overlay_dir() not in sys.path:
        sys.path.insert(0, overlay_dir())

    importlib.invalidate_caches()
    return name + ".py saqlandi. Kuchga kirishi uchun reload() yoki ilovani qayta oching."


def patch(name, old, new):
    name = _valid_name(name)
    current = source(name)
    count = current.count(old)

    if count != 1:
        raise ValueError(
            "Almashtiriladigan matn " + str(count) + " marta uchradi "
            "(aynan 1 marta bo'lishi kerak)."
        )

    return save(name, current.replace(old, new, 1))


def revert(name):
    name = _valid_name(name)
    target = os.path.join(overlay_dir(), name + ".py")

    if not os.path.exists(target):
        return name + ".py da o'zgartirish yo'q."

    os.remove(target)
    importlib.invalidate_caches()
    return name + ".py asl holiga qaytarildi. reload() qiling."


def reset_all():
    path = overlay_dir()

    if path in sys.path:
        sys.path.remove(path)

    if os.path.isdir(path):
        shutil.rmtree(path)

    _remove(_marker())
    _purge_overlay_modules(path)
    return "Barcha o'zgartirishlar o'chirildi. Ilovani qayta oching."


def status():
    files = _overlay_files()

    if not files:
        return "O'zgartirilgan modul yo'q (hammasi asl holida)."

    return "O'zgartirilgan modullar: " + ", ".join(f[:-3] for f in files)


def last_error():
    path = _error_file()

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    return ""


# SOZLAMALAR (ilova ko'rinishi uchun, masalan klaviatura rejimi)
def _settings_path():
    return os.path.join(data_dir(), "ui_settings.json")


def get_setting(key, default=None):
    try:
        with open(_settings_path(), "r", encoding="utf-8") as file:
            return json.load(file).get(key, default)
    except Exception:
        return default


def set_setting(key, value):
    data = {}

    try:
        with open(_settings_path(), "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        pass

    data[key] = value
    _write(_settings_path(), json.dumps(data, ensure_ascii=False, indent=2))


# YORDAMCHILAR
def _write(path, text):
    temp = path + ".tmp"

    with open(temp, "w", encoding="utf-8") as file:
        file.write(text)

    os.replace(temp, path)


def _remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
