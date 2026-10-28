# -*- coding: utf-8 -*-
"""JARVIS "ongi" - 4-qadam: tashabbus.

Jarvis o'zi ham taklif qila oladi (faqat javob bergandan keyin, sizni
bezovta qilmaydigan tarzda):
  * Odat: odatda shu soatda so'raydigan narsangizni taklif qiladi
    ("Odatda shu vaqtda «Ob-havo» so'raysiz. Hozir aytaymi?").
  * Takror: bir gapni 2 marta so'rab, tushunilmagan bo'lsa, o'rgatishni eslatadi.
  * Tanishuv: ismingizni bilmasa, bir marta so'raydi.

Cheklovlar: kuniga ko'pi bilan 3 ta, takliflar orasida kamida 6 ta gap,
bir odat kuniga bir marta, 2 marta rad etilgan odat qayta taklif qilinmaydi.
"tashabbusni o'chir" bilan butunlay o'chiriladi.
Ilova yopiq bo'lganda Jarvis o'zi xabar yubora olmaydi: takliflar suhbat paytida chiqadi.
"""
from datetime import datetime

MAX_PER_DAY = 3
MIN_GAP = 6
MIN_TURNS_FOR_NAME = 6
MAX_DECLINES = 2

YES = {
    "ha", "ha ayt", "ayt", "ha albatta", "albatta", "xo'p", "xop", "ok",
    "okey", "mayli", "ha marhamat", "marhamat", "ha kerak",
}
NO = {"yo'q", "yoq", "kerak emas", "hozir emas", "shart emas", "yo'q kerak emas"}

OFF = {
    "tashabbusni o'chir", "takliflarni o'chir", "takliflar kerak emas",
    "o'zing taklif qilma", "taklif qilma", "tashabbus kerak emas",
}
ON = {"tashabbusni yoq", "takliflarni yoq", "taklif qil", "tashabbusni yoqish"}
STATUS = {"tashabbus holati", "takliflar holati"}

NORMAL = ("buyruq:", "konikma:", "oyrgatilgan")


def _now():
    return datetime.now()


class Initiative:
    def __init__(self, mind):
        self.mind = mind
        self.pending = None   # (source, command)
        self._fresh = False

    @property
    def st(self):
        data = self.mind.data.setdefault("init", {})
        data.setdefault("on", True)
        data.setdefault("day", "")
        data.setdefault("count", 0)
        data.setdefault("last_turn", -100)
        data.setdefault("offered", {})
        data.setdefault("declines", {})
        data.setdefault("asked_name", False)
        return data

    # ---------- foydalanuvchi buyruqlari va javoblari ----------
    def handle(self, raw, n):
        if self.pending is not None:
            source, command = self.pending
            self.pending = None

            if n in YES:
                return self._run(command)

            if n in NO:
                st = self.st
                st["declines"][source] = st["declines"].get(source, 0) + 1
                self.mind.save()
                return "Xo'p."
            # boshqa gap: taklif bekor

        if n in OFF:
            self.st["on"] = False
            self.mind.save()
            return "Xo'p, endi o'zim taklif qilmayman. Qayta yoqish uchun: \"tashabbusni yoq\"."

        if n in ON:
            self.st["on"] = True
            self.mind.save()
            return "Yaxshi, ba'zan o'zim taklif beraman (kuniga ko'pi bilan 3 ta)."

        if n in STATUS:
            st = self.st
            state = "yoqilgan" if st["on"] else "o'chirilgan"
            today = st["count"] if st["day"] == _now().strftime("%Y-%m-%d") else 0
            return "Tashabbus " + state + ". Bugun " + str(today) + " ta taklif qildim."

        return None

    def _run(self, command):
        engine = self.mind.jarvis
        if engine is None:
            return None
        reply = engine.process(command)
        return reply if reply else "Bajarildi."

    # ---------- takliflar ----------
    def suggest(self, raw, norm, source):
        try:
            return self._suggest(norm, source)
        except Exception as error:
            print("ONG initiative error:", error)
            return ""

    def _busy(self):
        engine = self.mind.jarvis
        if engine is None:
            return True
        for attr in ("pending_teach", "pending_correct",
                     "pending_image_name", "pending_file_name"):
            if getattr(engine, attr, None) is not None:
                return True
        return False

    def _suggest(self, norm, source):
        st = self.st

        if not st["on"] or not source or not source.startswith(NORMAL) or self._busy():
            return ""

        if self.mind.adapt.pending is not None:
            return ""

        now = _now()
        today = now.strftime("%Y-%m-%d")

        if st["day"] != today:
            st["day"] = today
            st["count"] = 0
            st["offered"] = {k: v for k, v in st["offered"].items() if not k.startswith("h:")}

        turn = int(self.mind.data.get("turns", 0)) + 1

        if st["count"] >= MAX_PER_DAY or turn - int(st["last_turn"]) < MIN_GAP:
            return ""

        text = self._habit(source, now) or self._repeat_unknown() or self._ask_name(turn)

        if text:
            st["count"] += 1
            st["last_turn"] = turn
            self._fresh = True

        return text or ""

    def _habit(self, current, now):
        st = self.st
        hours = self.mind.adapt.st["hours"]
        freq = self.mind.adapt.st["freq"]

        for source, counts in hours.items():
            if source == current or st["declines"].get(source, 0) >= MAX_DECLINES:
                continue

            key = "h:" + source
            if st["offered"].get(key):
                continue

            total, peak = sum(counts), max(counts)
            if total < 4 or peak < 3 or peak / float(total) < 0.4:
                continue

            hour = counts.index(peak)
            if min((now.hour - hour) % 24, (hour - now.hour) % 24) > 1:
                continue

            options = [(k, v["n"]) for k, v in freq.items() if v.get("s") == source]
            if not options:
                continue

            command = max(options, key=lambda kv: kv[1])[0]
            st["offered"][key] = 1
            self.pending = (source, command)

            from ozbilim import SelfModel
            label = SelfModel._label(source)
            return "Odatda shu vaqtda «" + label + "» so'raysiz. Hozir bajaraymi? (ha / yo'q)"

        return ""

    def _repeat_unknown(self):
        st = self.st
        counts = self.mind.adapt.st.get("unk", {})

        for phrase, count in counts.items():
            key = "u:" + phrase
            if count >= 2 and not st["offered"].get(key):
                st["offered"][key] = 1
                return ("«" + phrase + "» ni " + str(count) + " marta so'radingiz, lekin "
                        "tushunmadim. Javobini o'rgatsangiz eslab qolaman: "
                        "o'rgat: " + phrase + " = javob")

        return ""

    def _ask_name(self, turn):
        st = self.st
        if st["asked_name"] or self.mind.name:
            return ""
        if int(self.mind.data.get("turns", 0)) < MIN_TURNS_FOR_NAME:
            return ""
        st["asked_name"] = True
        return "Aytgancha, sizni nima deb chaqirsam bo'ladi? Masalan: ismim Ali"

    def record(self):
        """Mind.observe ichidan: taklif faqat keyingi gap uchun amal qiladi."""
        if self.pending is not None and not self._fresh:
            self.pending = None
        self._fresh = False
