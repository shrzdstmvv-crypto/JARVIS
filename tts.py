
import re

import selfupdate

# Tillar ketma-ketligi: o'zbekcha ovoz o'rnatilmagan bo'lsa, turkcha ovoz
# (lotin yozuvi va talaffuzi o'zbekchaga yaqin) ishlatiladi.
AUTO_ORDER = [("uz", "UZ"), ("uz", ""), ("tr", "TR")]
CHOICES = ["auto", "uz", "tr", "ru", "en"]
CHUNK = 3000


def clean_text(text):
    """O'qishga xalaqit beradigan belgilarni tozalaydi."""
    text = str(text)
    text = text.replace("•", ". ").replace("«", "").replace("»", "")
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)   # emoji
    text = re.sub(r"[_*#`~|<>\[\]{}]", " ", text)
    text = re.sub(r"\n+", ". ", text)
    text = re.sub(r"([:;,])\s*\.", r"\1", text)
    text = re.sub(r"(?:\s*\.\s*){2,}", ". ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    if not text.strip(" ."):
        return ""

    return text if text[-1] in ".!?" else text + "."


def split_chunks(text, limit=CHUNK):
    """Uzun matnni gap chegaralarida bo'laklarga ajratadi."""
    parts, current = [], ""

    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if len(current) + len(sentence) + 1 > limit and current:
            parts.append(current)
            current = ""

        while len(sentence) > limit:
            parts.append(sentence[:limit])
            sentence = sentence[limit:]

        current = (current + " " + sentence).strip()

    if current:
        parts.append(current)

    return parts


class Speaker:
    """Android TextToSpeech orqali javoblarni ovoz chiqarib o'qiydi."""

    def __init__(self):
        self.tts = None
        self.ready = False
        self.pending = None
        self.error = None
        self.language = None
        self._listener = None
        self._init_status = None
        self._init()

    def _init(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method

            outer = self

            class InitListener(PythonJavaClass):
                __javainterfaces__ = [
                    "android/speech/tts/TextToSpeech$OnInitListener"
                ]
                __javacontext__ = "app"

                @java_method("(I)V")
                def onInit(self, status):
                    outer._on_init(status)

            TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            self._listener = InitListener()
            self.tts = TextToSpeech(PythonActivity.mActivity, self._listener)

            # Tizim javobni konstruktor ichidayoq berib yuborgan bo'lsa
            if self._init_status is not None and not self.ready:
                self._on_init(self._init_status)

        except Exception as error:
            self.error = "Ovoz tizimi ochilmadi: " + repr(error)[:120]
            print("TTS INIT ERROR:", error)

    def _on_init(self, status):
        self._init_status = status

        if self.tts is None:
            return  # _init oxirida qayta chaqiriladi

        if status != 0:
            self.error = "Ovoz tizimi ishga tushmadi."
            return

        self.ready = True
        self.apply_language()

        if self.pending:
            text, self.pending = self.pending, None
            self.speak(text)

    def apply_language(self):
        """Tanlangan (yoki avtomatik) tilni o'rnatadi."""
        if self.tts is None:
            return

        try:
            from jnius import autoclass

            Locale = autoclass("java.util.Locale")
            choice = selfupdate.get_setting("tts_lang", "auto")

            if choice and choice != "auto":
                order = [(choice, "")]
            else:
                order = AUTO_ORDER

            for lang, country in order:
                locale = Locale(lang, country) if country else Locale(lang)

                # LANG_AVAILABLE = 0, COUNTRY_AVAILABLE = 1, ... manfiy = yo'q
                if self.tts.setLanguage(locale) >= 0:
                    self.language = lang + ("-" + country if country else "")
                    return

            self.language = None
            self.error = "Tanlangan tilda ovoz o'rnatilmagan."

        except Exception as error:
            self.error = "Til o'rnatilmadi: " + repr(error)[:120]

    def describe(self):
        if self.language is None:
            return self.error or "ovoz tayyor emas"

        return self.language

    def speak(self, text):
        text = clean_text(text)

        if not text or self.tts is None:
            return False

        if not self.ready:
            self.pending = text
            return True

        try:
            for index, chunk in enumerate(split_chunks(text)):
                # 0 = oldingisini to'xtatib boshlash, 1 = navbatga qo'shish
                self.tts.speak(chunk, 0 if index == 0 else 1, None, "jarvis")

            return True

        except Exception as error:
            self.error = "O'qib bo'lmadi: " + repr(error)[:120]
            return False

    def stop(self):
        self.pending = None

        try:
            if self.tts is not None and self.ready:
                self.tts.stop()
        except Exception:
            pass

    def shutdown(self):
        try:
            if self.tts is not None:
                self.tts.shutdown()
        except Exception:
            pass
