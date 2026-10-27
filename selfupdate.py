
"""JARVIS o'z-o'zini yangilash tizimi.

Ilova kodi APK ichida turadi va o'zgarmaydi. O'zgartirishlar esa
doimiy papkadagi "overlay" papkasiga yoziladi: u yerdagi fayl APK
ichidagi bir xil nomli fayl o'rnini egallaydi. Ilova yangilanganda
overlay o'chmaydi. Xato o'zgarish ilovani yiqitsa, keyingi ishga
tushishda overlay avtomatik o'chiriladi va ilova asl holida ochiladi.
"""

import difflib
import importlib
import json
import os
import shutil
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tiklash vositalari: ularni overlay orqali o'zgartirib bo'lmaydi
PROTECTED = {"selfupdate", "terminal", "main", "jarvis_app_classic"}

# Ekran bilan bog'liq modullar: o'zgargach ilovani qayta ishga tushirish kerak
RESTART_MODULES = {"jarvis_app", "image_handler", "voice_input", "tts", "chats"}

# Ko'rinish versiyasi: yangi ko'rinish yiqilsa, shu versiya uchun klassik
# ko'rinishda ochiladi. Yangi versiya chiqqanda qayta sinab ko'riladi.
UI_BUILD = "ui-3"
USE_CLASSIC = False


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


# YANGI BUILD BILAN BIRLASHTIRISH (3 tomonlama merge)
def merge3(base, ours, theirs):
    """Qatorlar bo'yicha uch tomonlama birlashtirish.

    base - overlay saqlanganda APK'dagi asl kod, ours - foydalanuvchi
    o'zgartirgani, theirs - yangi build'dagi kod.
    Qaytaradi: (matn, to'qnashuv_bormi). To'qnashuvda "ours" olinadi.
    """
    b = base.splitlines(True)
    o = ours.splitlines(True)
    t = theirs.splitlines(True)

    hunks = []

    for side, lines in (("o", o), ("t", t)):
        matcher = difflib.SequenceMatcher(None, b, lines, autojunk=False)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                hunks.append((i1, i2, side, lines[j1:j2]))

    hunks.sort(key=lambda h: (h[0], h[1]))

    def region(cs, ce, side):
        text, pos = [], cs

        for i1, i2, hs, rep in hunks:
            if hs == side and cs <= i1 and i2 <= ce:
                text.extend(b[pos:i1])
                text.extend(rep)
                pos = i2

        text.extend(b[pos:ce])
        return text

    result, pos, conflict, index = [], 0, False, 0

    while index < len(hunks):
        cs, ce = hunks[index][0], hunks[index][1]
        cluster = [hunks[index]]
        index += 1

        while index < len(hunks) and (
            hunks[index][0] < ce
            or (hunks[index][0] == ce and hunks[index][0] == hunks[index][1])
            or (hunks[index][0] == cs and hunks[index][1] == cs)
        ):
            ce = max(ce, hunks[index][1])
            cluster.append(hunks[index])
            index += 1

        result.extend(b[pos:cs])
        sides = {h[2] for h in cluster}
        ours_text = region(cs, ce, "o")
        theirs_text = region(cs, ce, "t")

        if sides == {"o"}:
            result.extend(ours_text)
        elif sides == {"t"}:
            result.extend(theirs_text)
        elif ours_text == theirs_text:
            result.extend(ours_text)
        else:
            conflict = True
            result.extend(ours_text)

        pos = ce

    result.extend(b[pos:])
    return "".join(result), conflict


def _base_path(name):
    return os.path.join(overlay_dir(), ".base", name + ".py")


def _read(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def _bundled_text(name):
    path = os.path.join(BASE_DIR, name + ".py")
    return _read(path) if os.path.exists(path) else None


def _sync_overlay():
    """Yangi build kelganda overlay'dagi o'zgarishlarni yangi kod bilan
    birlashtiradi. Foydalanuvchi o'zgartirishlari yo'qolmaydi."""
    messages = []

    for file in _overlay_files():
        name = file[:-3]
        overlay_file = os.path.join(overlay_dir(), file)

        try:
            theirs = _bundled_text(name)

            if theirs is None:
                continue  # faqat overlay'da bor yangi modul

            ours = _read(overlay_file)
            base_file = _base_path(name)

            if not os.path.exists(base_file):
                os.makedirs(os.path.dirname(base_file), exist_ok=True)
                _write(base_file, theirs)
                continue

            base = _read(base_file)

            if base == theirs:
                continue  # yangi build bu modulni o'zgartirmagan

            if ours == base:
                # Foydalanuvchi aslida hech narsa o'zgartirmagan
                os.remove(overlay_file)
                os.remove(base_file)
                messages.append(name + ".py: yangi build'dagi versiya olindi.")
                continue

            merged, conflict = merge3(base, ours, theirs)

            try:
                compile(merged, name + ".py", "exec")
            except SyntaxError:
                conflict = True

            if not conflict:
                _write(overlay_file, merged)
                messages.append(
                    name + ".py: sizning o'zgartirishlaringiz yangi "
                    "build bilan birlashtirildi."
                )
            else:
                messages.append(
                    name + ".py: yangi build bilan to'qnashdi, sizning "
                    "o'zgartirishingiz saqlandi. Yangisini olish: "
                    "take_new(\"" + name + "\"), farqni ko'rish: diff(\""
                    + name + "\")."
                )

            _write(base_file, theirs)

        except Exception as error:
            print("Overlay sync error:", name, error)

    return messages


# ISHGA TUSHIRISH VA YIQILISHDAN HIMOYA
def prepare():
    """Ilova ochilishidan oldin chaqiriladi.

    1) Yangi build bo'lsa, overlay'ni birlashtiradi.
    2) Oldingi ishga tushish tugallanmagan bo'lsa (ilova yiqilgan):
       overlay bo'lsa uni o'chiradi, bo'lmasa (ketma-ket 2 marta) klassik
       ko'rinishga o'tadi.
    Foydalanuvchiga ko'rsatiladigan xabarni qaytaradi (yoki None).
    """
    global USE_CLASSIC
    messages = _sync_overlay()
    files = _overlay_files()

    unfinished = 0

    if os.path.exists(_marker()):
        try:
            unfinished = int(_read(_marker()).strip() or "0") + 1
        except Exception:
            unfinished = 1

    if unfinished >= 1 and files:
        messages.append(disable_overlay(
            "Oxirgi o'zgartirish ilovani ishga tushirmadi, "
            "shuning uchun bekor qilindi. Eski holatga qaytdim."
        ))
        files = []
        unfinished = 0
    elif unfinished >= 2:
        set_setting("ui_fail_build", UI_BUILD)
        messages.append(
            "Yangi ko'rinish ketma-ket ochilmadi, shuning uchun klassik "
            "ko'rinishda ochildi. Qayta sinash: terminalda ui(\"new\")."
        )
        unfinished = 0

    if get_setting("ui_fail_build") == UI_BUILD:
        USE_CLASSIC = True

    _write(_marker(), str(unfinished))

    if files and overlay_dir() not in sys.path:
        sys.path.insert(0, overlay_dir())

    return " ".join(messages) if messages else None


def boot_ok():
    """Ilova muvaffaqiyatli ochilgach chaqiriladi."""
    _remove(_marker())


def mark_ui_failed():
    set_setting("ui_fail_build", UI_BUILD)


def set_ui(mode):
    if mode == "classic":
        set_setting("ui_fail_build", UI_BUILD)
        return "Klassik ko'rinish yoqildi. Ilovani qayta oching."

    set_setting("ui_fail_build", "")
    return "Yangi ko'rinish yoqildi. Ilovani qayta oching."


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
    if not _overlay_files():
        return "Ilova kodida xato: " + repr(error)[:200]

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

    # Yangi build bilan birlashtirish uchun asl kodni eslab qolamiz
    bundled = _bundled_text(name)
    base_file = _base_path(name)

    if bundled is not None and not os.path.exists(base_file):
        os.makedirs(os.path.dirname(base_file), exist_ok=True)
        _write(base_file, bundled)

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
    _remove(_base_path(name))
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


def diff(name):
    name = _valid_name(name)
    bundled = _bundled_text(name)

    if bundled is None:
        return name + ".py APK ichida yo'q (faqat overlay'da)."

    overlay_file = os.path.join(overlay_dir(), name + ".py")

    if not os.path.exists(overlay_file):
        return name + ".py o'zgartirilmagan."

    lines = difflib.unified_diff(
        bundled.splitlines(), _read(overlay_file).splitlines(),
        "APK", "sizniki", lineterm=""
    )
    return "\n".join(lines) or "Farq yo'q."


def take_new(name):
    """Yangi build'dagi versiyani olib, o'z o'zgartirishlarni tashlash."""
    return revert(name)


def apply_hint(name):
    """Saqlangandan keyin nima qilish kerakligini aytadi."""
    name = _valid_name(name)
    return "restart" if name in RESTART_MODULES else "reload"


def restart_app():
    """Ilovani o'zi qayta ishga tushiradi. Muvaffaqiyatli bo'lsa qaytmaydi."""
    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        PendingIntent = autoclass("android.app.PendingIntent")
        AlarmManager = autoclass("android.app.AlarmManager")
        System = autoclass("java.lang.System")

        activity = PythonActivity.mActivity
        package = activity.getPackageName()
        launch = activity.getPackageManager().getLaunchIntentForPackage(package)
        launch.addFlags(
            Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK
        )

        pending = PendingIntent.getActivity(
            activity, 0, launch,
            PendingIntent.FLAG_CANCEL_CURRENT | PendingIntent.FLAG_IMMUTABLE
        )
        from jnius import cast

        alarms = cast(
            "android.app.AlarmManager", activity.getSystemService("alarm")
        )
        alarms.set(AlarmManager.RTC, System.currentTimeMillis() + 500, pending)

        _remove(_marker())
        os._exit(0)

    except Exception as error:
        return "Avtomatik qayta ishga tushmadi (" + repr(error)[:120] + \
            "). Ilovani qo'lda yopib qayta oching."


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
