import re

# Misollar:
#   budilnik 6:20 ga qo'y        6:20 ga budilnik qo'y
#   soat 7 ga budilnik qo'y      kechqurun 8 ga budilnik qo'y
#   30 daqiqadan keyin suv ichishni eslat
#   5 daqiqaga taymer qo'y       eslatma qo'y 10 daqiqadan keyin choy
# "re:" - gapning istalgan joyida shu so'z bo'lsa ishlaydi
TRIGGERS = [
    "re:\\bbudilnik", "re:\\buyg'ot", "re:\\btaymer", "re:\\beslat\\w*"
]

UNITS = {
    "soniya": 1, "sekund": 1,
    "daqiqa": 60, "minut": 60,
    "soat": 3600
}

FILLER = {
    "keyin", "eslat", "eslatib", "eslatma", "qo'y", "qoy", "taymer",
    "budilnik", "menga", "iltimos", "ga", "da", "dan", "jarvis", "meni"
}


def parse_alarm(text):
    """Matndan (soat, daqiqa) topadi, topilmasa None."""
    match = re.search(r"(\d{1,2})\s*[:.]\s*(\d{2})", text)

    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
    else:
        match = re.search(
            r"(?:soat\s*)?\b(\d{1,2})\s*(?:ga|da|dan)\b", text
        )

        if not match:
            return None

        hour, minute = int(match.group(1)), 0

    # "kechqurun 8 ga" -> 20:00
    if hour < 12 and re.search(
        r"kechqurun|kechki|kechasi|tushdan keyin|oqshom", text
    ):
        hour += 12

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None

    return hour, minute


def parse_timer(text):
    """Matndan (soniya, xabar) topadi, topilmasa None."""
    match = re.search(
        r"(\d+)\s*(soniya|sekund|daqiqa|minut|soat)\w*", text
    )

    if not match:
        return None

    seconds = int(match.group(1)) * UNITS[match.group(2)]

    rest = (text[:match.start()] + " " + text[match.end():]).split()
    message = " ".join(w for w in rest if w not in FILLER)

    return seconds, message or "Eslatma"


def _send(action, extras):
    """Android soat ilovasiga buyruq yuboradi."""
    from jnius import autoclass

    Intent = autoclass("android.content.Intent")
    AlarmClock = autoclass("android.provider.AlarmClock")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")

    intent = Intent(getattr(AlarmClock, action))

    for key, value in extras:
        name = getattr(AlarmClock, key)

        if isinstance(value, bool):
            intent.putExtra(name, value)
        elif isinstance(value, int):
            intent.putExtra(name, value)
        else:
            intent.putExtra(name, str(value))

    PythonActivity.mActivity.startActivity(intent)


def run(text, jarvis):
    norm = jarvis._normalize(text)

    try:
        if "budilnik" in norm or "uyg'ot" in norm:
            found = parse_alarm(norm)

            if not found:
                return "Vaqtni ayting, masalan: budilnik 6:20 ga qo'y"

            hour, minute = found
            _send("ACTION_SET_ALARM", [
                ("EXTRA_HOUR", hour),
                ("EXTRA_MINUTES", minute),
                ("EXTRA_MESSAGE", "JARVIS"),
                ("EXTRA_SKIP_UI", True)
            ])
            return "Budilnik %02d:%02d ga qo'yildi." % (hour, minute)

        found = parse_timer(norm)

        if not found:
            return (
                "Qancha vaqtdan keyin? Masalan: "
                "30 daqiqadan keyin suv ichishni eslat"
            )

        seconds, message = found
        _send("ACTION_SET_TIMER", [
            ("EXTRA_LENGTH", seconds),
            ("EXTRA_MESSAGE", message),
            ("EXTRA_SKIP_UI", True)
        ])

        minutes, rest = divmod(seconds, 60)
        shown = (str(minutes) + " daqiqa") if not rest else (str(seconds) + " soniya")

        if seconds >= 3600 and seconds % 3600 == 0:
            shown = str(seconds // 3600) + " soat"

        return "Eslatma qo'yildi (%s): %s" % (shown, message)

    except Exception as error:
        return "Qo'yib bo'lmadi: " + repr(error)[:150]
