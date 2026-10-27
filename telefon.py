import difflib
import json
import os
import re
import urllib.parse

# Telefon bilan ishlash: qo'ng'iroq, SMS, kontaktlar, batareya, fonar, ovoz,
# ilovalarni ochish, sozlamalar, qidiruv, xarita, ovozli javob.
TRIGGERS = [
    r"re:\bqo'?ng'?iroq|\bzvonok|\bqongirog",
    r"re:\bsms\b",
    r"re:\bkontakt",
    r"re:\bbatareya|\bzaryad|\bakkumulyator",
    r"re:\bfonar",
    r"re:\bovoz\w*\b",
    r"re:\bgoogle|\bgugl",
    r"re:\bxarita|\byo'nalish|\byo'l ko'rsat",
    r"re:\b(?:och|ochib ber|ochib bering|ishga tushir|kir)\b",
]

SKIP_WORDS = ("youtube", "yutub", "instagram", "insta")

ACTIONS = {
    "wifi": "android.settings.WIFI_SETTINGS",
    "wi-fi": "android.settings.WIFI_SETTINGS",
    "bluetooth": "android.settings.BLUETOOTH_SETTINGS",
    "sozlamalar": "android.settings.SETTINGS",
    "ekran": "android.settings.DISPLAY_SETTINGS",
    "yorqinlik": "android.settings.DISPLAY_SETTINGS",
    "ilovalar": "android.settings.APPLICATION_SETTINGS",
    "joylashuv": "android.settings.LOCATION_SOURCE_SETTINGS",
    "gps": "android.settings.LOCATION_SOURCE_SETTINGS",
    "kamera": "android.media.action.STILL_IMAGE_CAMERA",
}

ALIASES = {
    "telegram": "org.telegram.messenger",
    "whatsapp": "com.whatsapp",
    "chrome": "com.android.chrome",
    "gmail": "com.google.android.gm",
}

FILLER = {
    "qo'ng'iroq", "qongiroq", "qil", "qilish", "ber", "bering", "menga",
    "iltimos", "jarvis", "och", "ochib", "ishga", "tushir", "kir", "sms",
    "yoz", "yubor", "jo'nat", "kontakt", "kontaktlar", "saqla", "qo'sh",
    "ni", "ga", "ka", "qa", "ilovasini", "ilovani", "ilova", "dasturini"
}


# ---------- Android yordamchilari ----------
def _activity():
    from jnius import autoclass
    return autoclass("org.kivy.android.PythonActivity").mActivity


def _service(name, cls):
    from jnius import cast
    return cast(cls, _activity().getSystemService(name))


def _open(action, uri=None, extras=None):
    from jnius import autoclass

    Intent = autoclass("android.content.Intent")

    if uri is not None:
        Uri = autoclass("android.net.Uri")
        intent = Intent(action, Uri.parse(uri))
    else:
        intent = Intent(action)

    for key, value in (extras or {}).items():
        intent.putExtra(key, value)

    _activity().startActivity(intent)


# ---------- kontaktlar ----------
def _contacts_path():
    import selfupdate
    return os.path.join(selfupdate.data_dir(), "contacts.json")


def _load_contacts():
    try:
        with open(_contacts_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_contacts(data):
    with open(_contacts_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _number(text):
    match = re.search(r"\+?\d[\d\s\-()]{5,}\d", text)

    if not match:
        return None

    digits = re.sub(r"[^\d+]", "", match.group(0))
    return digits


def _find_contact(words):
    contacts = _load_contacts()

    for w in words:
        for name, number in contacts.items():
            if w == name or (len(name) >= 3 and w.startswith(name)):
                return name, number

    return None, None


def _words(norm):
    return [w for w in norm.split() if w not in FILLER]


# ---------- ilova qidirish ----------
def _find_app(query):
    query = query.strip()

    if not query:
        return None

    if query in ALIASES:
        return ALIASES[query]

    activity = _activity()
    pm = activity.getPackageManager()
    apps = pm.getInstalledApplications(0)
    best, best_score = None, 0.0

    for i in range(apps.size()):
        app = apps.get(i)
        label = str(pm.getApplicationLabel(app)).lower()

        if pm.getLaunchIntentForPackage(app.packageName) is None:
            continue

        if label == query or label.startswith(query) or query.startswith(label):
            score = 1.0
        else:
            score = difflib.SequenceMatcher(None, query, label).ratio()

        if score > best_score:
            best, best_score = app.packageName, score

    return best if best_score >= 0.75 else None


def run(text, jarvis):
    norm = jarvis._normalize(text)
    words = norm.split()

    if any(s in norm for s in SKIP_WORDS):
        return None

    try:
        # --- ovozli javob (matn o'qish) ---
        if "ovozli javob" in norm:
            import selfupdate
            on = not re.search(r"o'chir|yopib|to'xtat|kerak emas", norm)
            selfupdate.set_setting("tts", on)
            return "Ovozli javob " + ("yoqildi." if on else "o'chirildi.")

        # --- kontaktlar ---
        if "kontakt" in norm:
            match = re.search(
                r"kontakt\w*\s+(?:saqla|qo'sh|yoz)\w*\s+(.+?)\s+(\+?\d[\d\s\-]{5,})",
                norm
            )

            if match:
                name = match.group(1).strip()
                number = re.sub(r"[^\d+]", "", match.group(2))
                contacts = _load_contacts()
                contacts[name] = number
                _save_contacts(contacts)
                return "«" + name + "» kontakti saqlandi."

            contacts = _load_contacts()

            if re.search(r"o'chir", norm):
                name, _ = _find_contact(_words(norm))

                if name:
                    contacts = _load_contacts()
                    contacts.pop(name, None)
                    _save_contacts(contacts)
                    return "«" + name + "» kontakti o'chirildi."

            if not contacts:
                return "Kontakt yo'q. Qo'shish: kontakt saqla onam 998901234567"

            return "Kontaktlar: " + ", ".join(sorted(contacts))

        # --- SMS ---
        if re.search(r"\bsms\b", norm):
            before, _, after = norm.partition("sms")
            message = re.sub(r"^\s*(?:yoz|yubor|jo'nat)\w*\s*", "", after).strip()
            number = _number(before) or _number(after)
            name, saved = _find_contact(_words(before))
            number = number or saved

            if not number:
                return "Kimga? Masalan: onamga sms yoz salom (avval kontakt saqlang)."

            body = re.sub(r"\+?\d[\d\s\-]{5,}\d", "", message).strip()
            _open("android.intent.action.SENDTO", "smsto:" + number, {"sms_body": body})
            return "SMS oynasi ochildi. Yuborish tugmasini bosing."

        # --- qo'ng'iroq ---
        if re.search(r"qo'?ng'?iroq|zvonok|qongirog", norm):
            number = _number(norm)
            name, saved = _find_contact(_words(norm))
            number = number or saved

            if not number:
                return "Kimga? Raqamni ayting yoki avval «kontakt saqla onam 99890...» deng."

            _open("android.intent.action.DIAL", "tel:" + number)
            return "Raqam terildi" + (" (" + name + ")" if name else "") + ". Qo'ng'iroq tugmasini bosing."

        # --- batareya ---
        if re.search(r"batareya|zaryad|akkumulyator", norm) and not re.search(r"\boch\b|sozlama", norm):
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            IntentFilter = autoclass("android.content.IntentFilter")
            status = _activity().registerReceiver(None, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            level = status.getIntExtra("level", -1)
            scale = status.getIntExtra("scale", 100)
            plugged = status.getIntExtra("plugged", 0)
            percent = round(level * 100 / scale) if level >= 0 and scale > 0 else None

            if percent is None:
                return "Batareya holatini aniqlab bo'lmadi."

            return "Batareya: %d%%%s." % (percent, " (zaryadlanyapti)" if plugged else "")

        # --- fonar ---
        if "fonar" in norm:
            on = not re.search(r"o'chir|yopib|so'ndir", norm)
            manager = _service("camera", "android.hardware.camera2.CameraManager")
            ids = manager.getCameraIdList()
            manager.setTorchMode(ids[0], on)
            return "Fonar " + ("yoqildi." if on else "o'chirildi.")

        # --- ovoz balandligi ---
        if re.search(r"\bovoz\w*", norm):
            audio = _service("audio", "android.media.AudioManager")
            stream = 3  # STREAM_MUSIC

            if re.search(r"max|maksimal|to'liq|eng baland", norm):
                audio.setStreamVolume(stream, audio.getStreamMaxVolume(stream), 1)
            elif re.search(r"balandlat|ko'tar|oshir|baland|ko'proq|kuchaytir", norm):
                for _ in range(2):
                    audio.adjustStreamVolume(stream, 1, 1)
            elif re.search(r"pasaytir|kamaytir|past|kamroq|sekinlat", norm):
                for _ in range(2):
                    audio.adjustStreamVolume(stream, -1, 1)
            elif re.search(r"o'chir|ovozsiz|jim", norm):
                audio.adjustStreamVolume(stream, -100, 1)
            elif re.search(r"\byoq\b|qaytar", norm):
                audio.adjustStreamVolume(stream, 100, 1)
            else:
                return None

            return "Ovoz: %d/%d" % (audio.getStreamVolume(stream), audio.getStreamMaxVolume(stream))

        # --- google qidiruvi ---
        if re.search(r"\bgoogle|\bgugl", norm):
            query = " ".join(
                w for w in words
                if not re.match(r"(google|gugl|qidir|izla|top|ber|menga|da|dan)['’]?\w*$", w)
            ).strip()

            if not query:
                return "Nimani qidiray? Masalan: google'da Toshkent tarixi qidir"

            _open("android.intent.action.VIEW", "https://www.google.com/search?q=" + urllib.parse.quote(query))
            return "Google'da qidiryapman: " + query

        # --- xarita ---
        if re.search(r"\bxarita|\byo'nalish|\byo'l ko'rsat", norm):
            place = " ".join(
                re.sub(r"(ga|ka|qa|ni|dan|da)$", "", w) if len(w) > 5 else w
                for w in words
                if not re.match(r"(xarita|yo'nalish|yo'l|ko'rsat|ga|da|dan|ni|menga|ber)\w*$", w)
            ).strip()
            uri = "geo:0,0?q=" + urllib.parse.quote(place) if place else "geo:0,0"
            _open("android.intent.action.VIEW", uri)
            return "Xaritada ochdim" + (": " + place if place else ".")

        # --- ilova yoki sozlamani ochish ---
        if re.search(r"\b(?:och|ochib ber|ochib bering|ishga tushir|kir)\b", norm):
            for key, action in ACTIONS.items():
                if key in norm:
                    _open(action)
                    return key.capitalize() + " ochildi."

            query = " ".join(w for w in words if w not in FILLER and not re.match(r"(och|ochib|ishga|tushir|kir)\w*$", w))
            query = re.sub(r"(ni|ga)$", "", query).strip()
            package = _find_app(query)

            if package is None:
                return None

            launch = _activity().getPackageManager().getLaunchIntentForPackage(package)

            if launch is None:
                return None

            _activity().startActivity(launch)
            return query.capitalize() + " ochildi."

    except Exception as error:
        return "Bajarib bo'lmadi: " + repr(error)[:150]

    return None
