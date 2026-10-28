# -*- coding: utf-8 -*-
"""JARVIS "ongi" - 2-qadam: o'zini bilish.

Jarvis o'zi haqida haqiqiy ma'lumotlarga tayanib javob beradi:
  * nimalarni qila oladi (haqiqiy ko'nikmalar va xususiyatlar ro'yxatidan)
  * bugun nimalar qildi (har bir javob qaysi ishlovchidan chiqqani yoziladi)
  * qayerda xato qildi (tushunmagan gaplar, ishlamagan buyruqlar, tuzatishlar)
  * umumiy holati (statistika)

Ma'lumotlar Mind.data["self"] ichida, ong.json faylida saqlanadi.
"""
import re
from datetime import datetime

MAX_UNKNOWN = 30
MAX_ERRORS = 20
KEEP_DAYS = 14

CAPS = {
    "nima qila olasan", "nimalarni qila olasan", "nimalar qila olasan",
    "nima qila olasiz", "imkoniyatlaring", "qobiliyatlaring",
    "ko'nikmalaring", "nimaga qodirsan", "nimalarga qodirsan",
    "imkoniyatlaring qanday", "qanday ko'nikmalaring bor",
}

TODAY = {
    "bugun nima qildik", "bugun nima qilding", "bugun nima ish qilding",
    "bugungi ishlar", "bugungi hisobot", "kunlik hisobot", "bugun nimalar qilding",
}

ERRORS = {
    "xatolaring", "xatolaring nima", "qayerda xato qilding",
    "qayerda xato qildim", "nimani bilmading", "nimalarni bilmading",
    "nimalarni tushunmading", "qaysi gaplarni tushunmading",
    "kamchiliklaring", "kamchiliklaring nima", "xatolarni ko'rsat",
}

CLEAR_ERRORS = {"xatolarni tozala", "xatolar ro'yxatini tozala", "kamchiliklarni tozala"}

STATUS = {
    "o'zing haqingda ayt", "o'zing haqingda gapir", "holat hisoboti",
    "statistika", "hisobot", "o'zingni tahlil qil", "o'zingni baholab ber",
}

SKILL_INFO = {
    "budilnik": "budilnik va taymer qo'yish",
    "telefon": "qo'ng'iroq, SMS, batareya, fonar, ovoz, ilovalarni ochish, qidiruv, xarita",
    "ob_havo": "ob-havo ma'lumoti",
    "suhbat": "oddiy suhbat, hazil, maqollar",
}

INTENT_LABEL = {
    "greeting": "Salomlashish", "goodbye": "Xayrlashish",
    "time": "Vaqtni aytish", "date": "Sanani aytish",
    "calculator": "Hisob-kitob", "youtube": "YouTube ochish",
    "youtube_search": "YouTube qidiruvi", "instagram": "Instagram ochish",
    "help": "Yordam", "memory_info": "Xotira haqida ma'lumot",
    "clear_memory": "Xotirani tozalash", "recall_memory": "Xotiradan eslash",
    "recall_name": "Ismni eslash", "remember": "Eslab qolish",
    "terminal": "Terminalni ochish",
}

FEATURE_WORDS = {
    "hisob": "hisob-kitob", "hisobla": "hisob-kitob", "kalkulyator": "hisob-kitob",
    "soat": "vaqtni aytish", "vaqt": "vaqtni aytish", "sana": "sanani aytish",
    "youtube": "YouTube ochish va qidirish", "instagram": "Instagram ochish",
    "rasm": "rasmlarni nomlab saqlash va topish", "fayl": "fayllarni nomlab saqlash va topish",
    "eslab": "siz haqingizda eslab qolish", "yodla": "siz haqingizda eslab qolish",
    "terminal": "terminal orqali o'zini o'zgartirish", "o'rgan": "yangi javoblarni o'rganish",
}

STOP = {
    "buni", "shuni", "sen", "siz", "iltimos", "jarvis", "menga", "uchun",
    "ham", "yana", "mening", "bunday", "narsani", "narsa", "mumkinmi",
    "qila", "ayta", "qo'ya", "ocha", "yoza", "bera", "ko'rsata", "topa",
    "bajara", "yubora", "chiqara", "saqlay", "ochib", "qilib", "aytib",
}

ERROR_MARKERS = (
    "ko'nikmasida xato", "qo'yib bo'lmadi", "xatolik yuz berdi",
    "bajarib bo'lmadi", "ishlamadi", "topib bo'lmadi",
)


def _today():
    return datetime.now().strftime("%Y-%m-%d")


class SelfModel:
    def __init__(self, mind):
        self.mind = mind
        self.started = datetime.now()

    # ---------- saqlash ----------
    @property
    def st(self):
        data = self.mind.data.setdefault("self", {})
        data.setdefault("stats", {"ok": 0, "unknown": 0, "errors": 0, "corrections": 0})
        data.setdefault("unknown", [])
        data.setdefault("errors", [])
        data.setdefault("daily", {})
        data.setdefault("since", datetime.now().isoformat(timespec="seconds"))
        return data

    def record(self, raw, response, source, correction=False):
        """Mind.observe ichidan chaqiriladi (saqlashni Mind o'zi qiladi)."""
        st = self.st
        text = str(raw).strip()[:200]
        response = str(response or "")
        source = source or "boshqa"

        if correction:
            st["stats"]["corrections"] += 1

        if source == "tushunmadi":
            st["stats"]["unknown"] += 1
            if text in st["unknown"]:
                st["unknown"].remove(text)
            st["unknown"].append(text)
            del st["unknown"][:-MAX_UNKNOWN]
        else:
            st["stats"]["ok"] += 1

        low = response.lower()
        if any(marker in low for marker in ERROR_MARKERS):
            st["stats"]["errors"] += 1
            st["errors"].append({
                "t": datetime.now().isoformat(timespec="seconds"),
                "u": text,
                "e": response[:160],
            })
            del st["errors"][:-MAX_ERRORS]

        day = st["daily"].setdefault(_today(), {})
        day[source] = day.get(source, 0) + 1

        for old in sorted(st["daily"])[:-KEEP_DAYS]:
            st["daily"].pop(old, None)

    # ---------- javoblar ----------
    def handle(self, raw, n):
        if n in CAPS:
            return self.capabilities()

        if n in TODAY:
            return self.today()

        if n in ERRORS:
            return self.mistakes()

        if n in CLEAR_ERRORS:
            st = self.st
            st["unknown"] = []
            st["errors"] = []
            self.mind.save()
            return "Xatolar va tushunmagan gaplar ro'yxati tozalandi."

        if n in STATUS:
            return self.status()

        match = re.match(r"^(.+?)\s+(?:olasanmi|olasizmi|olasan mi|qilaolasanmi)$", n)
        if match:
            return self.can_i(match.group(1))

        return None

    def _engine(self):
        return self.mind.jarvis

    def _skills(self):
        engine = self._engine()
        try:
            return list(engine.skills.skills)
        except Exception:
            return []

    def _count(self, attr):
        try:
            return int(getattr(self._engine(), attr).count())
        except Exception:
            return 0

    def _learned(self):
        try:
            return int(self._engine().learner.count())
        except Exception:
            return 0

    def capabilities(self):
        lines = [
            "Hisob-kitob, vaqt va sana",
            "YouTube va Instagram ochish",
            "Siz haqingizda eslab qolish (ism, yosh, shahar, yoqtirganlaringiz)",
            "Rasm va fayllarni nomlab saqlash, topish, galereya/yuklamalarga chiqarish",
            "Terminal orqali o'zimni o'zgartirish va yangi ko'nikma yozish",
        ]

        learned = self._learned()
        lines.append("Siz o'rgatgan javoblar: " + str(learned) + " ta")

        for skill in self._skills():
            name = skill.get("name", "")
            info = SKILL_INFO.get(name)
            lines.append("Ko'nikma «" + name + "»" + (": " + info if info else ""))

        errors = getattr(self._engine().skills, "errors", {}) if self._engine() else {}
        for name in errors:
            lines.append("«" + name + "» ko'nikmasi yuklanmadi (xato bor)")

        return "Men qila oladigan ishlar:\n" + "\n".join("• " + x for x in lines)

    def can_i(self, topic):
        tokens = [t for t in re.findall(r"[a-zа-яё']+", topic) if len(t) >= 4 and t not in STOP]

        if not tokens:
            return "Nimani qila olishimni aniqroq yozing. Masalan: \"budilnik qo'ya olasanmi\"."

        for skill in self._skills():
            hay = skill.get("name", "").replace("_", " ").lower()

            for trigger in skill.get("triggers", []):
                hay += " " + re.sub(r"[\\?|()\[\]]|\bb\b", "", str(trigger)).lower()

            for token in tokens:
                stem = token[:5] if len(token) > 5 else token
                if stem in hay:
                    info = SKILL_INFO.get(skill["name"])
                    return "Ha, qila olaman. Bu «" + skill["name"] + "» ko'nikmamda bor" + (
                        " (" + info + ")." if info else ".")

        for token in tokens:
            for key, feature in FEATURE_WORDS.items():
                if token.startswith(key):
                    return "Ha, qila olaman: " + feature + "."

        return ("Bunday ko'nikma hozircha topilmadi. Terminal orqali yangi "
                "ko'nikma yozib o'rgatsangiz, qila olaman.")

    def today(self):
        day = self.st["daily"].get(_today())
        if not day:
            return "Bugun hali hech narsa qilmadik."

        parts = []
        for source, count in sorted(day.items(), key=lambda kv: -kv[1]):
            parts.append("• " + self._label(source) + ": " + str(count) + " marta")

        total = sum(day.values())
        return "Bugun " + str(total) + " ta so'rov bajardim:\n" + "\n".join(parts)

    @staticmethod
    def _label(source):
        if source.startswith("buyruq:"):
            intent = source.split(":", 1)[1]
            return INTENT_LABEL.get(intent, intent)
        if source.startswith("konikma:"):
            return "Ko'nikma «" + source.split(":", 1)[1] + "»"
        return {
            "ong": "Xotira va kontekst",
            "reja": "Ko'p qadamli buyruqlar",
            "oyrgatilgan": "O'rgatilgan javoblar",
            "oyrgatish": "O'rgatish, rasm va fayllar",
            "tushunmadi": "Tushunmagan gaplar",
            "boshqa": "Boshqa",
        }.get(source, source)

    def mistakes(self):
        st = self.st
        parts = []

        if st["unknown"]:
            parts.append("Tushunmagan gaplarim:\n" + "\n".join(
                "• " + u for u in st["unknown"][-8:]))

        if st["errors"]:
            parts.append("Ishlamagan buyruqlar:\n" + "\n".join(
                "• " + e["u"] + " -> " + e["e"] for e in st["errors"][-5:]))

        if st["stats"]["corrections"]:
            parts.append("Siz meni " + str(st["stats"]["corrections"]) + " marta tuzatgansiz.")

        if not parts:
            return "Hozircha tushunmagan gaplarim yoki xatolarim qayd etilmagan."

        parts.append("Gaplarni o'rgatsangiz yoki terminalda ko'nikma yozsangiz, keyingi safar bilaman.")
        return "\n\n".join(parts)

    def status(self):
        st = self.st
        ok, unknown = st["stats"]["ok"], st["stats"]["unknown"]
        total = ok + unknown
        lines = []

        since = st.get("since", "")[:10]
        lines.append("Hisob boshlangan: " + (since or "bugun"))
        lines.append("Jami so'rovlar: " + str(total))

        if total:
            lines.append("Tushunganlarim: " + str(round(100 * ok / total)) + "%")

        lines.append("Tushunmaganlarim: " + str(unknown))
        lines.append("Ishlamagan buyruqlar: " + str(st["stats"]["errors"]))
        lines.append("Tuzatishlar: " + str(st["stats"]["corrections"]))
        lines.append("O'rgatilgan javoblar: " + str(self._learned()) + " ta")
        lines.append("Ko'nikmalar: " + str(len(self._skills())) + " ta")
        lines.append("Rasmlar: " + str(self._count("images")) + ", fayllar: " + str(self._count("files")))

        prof = len(self.mind.data.get("profile", {}))
        lines.append("Siz haqingizda ma'lumotlar: " + str(prof) + " ta")

        return "Mening holatim:\n" + "\n".join("• " + x for x in lines)
