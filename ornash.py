# -*- coding: utf-8 -*-
"""JARVIS "ongi" - 3-qadam: o'rganish.

  * Siz tushunilmagan gapdan keyin darhol boshqa so'z bilan buyruqni
    aytsangiz, Jarvis ikkalasi bir xil ma'noda ekanini taklif qiladi va
    tasdig'ingiz bilan o'rganadi.
  * Qaysi gaplarni ko'p so'rashingizni va qaysi soatlarda so'rashingizni
    hisoblab boradi (4-qadamdagi tashabbus uchun asos).
  * "nimalarni o'rgandingiz", "ko'p so'raydiganlarim", "odatlarim" savollariga
    haqiqiy ma'lumot bilan javob beradi.

Ma'lumotlar Mind.data["learn"] ichida (ong.json), tashqi AI kerak emas.
"""
import re
from datetime import datetime

MAX_FREQ = 150
MAX_ALIASES = 100

# Faqat qo'shimcha matn talab qilmaydigan buyruqlar uchun sinonim o'rganiladi
SAFE_INTENTS = {
    "greeting", "goodbye", "time", "date", "youtube", "instagram",
    "help", "memory_info",
}

YES = {
    "ha", "ha o'rgan", "ha esla", "ha albatta", "albatta", "xo'p", "xop",
    "ok", "okey", "mayli", "ha shunday", "ha bir xil",
}
NO = {"yo'q", "yoq", "kerak emas", "yo'q kerak emas", "bekor", "shart emas"}

ASK_LEARNED = {
    "yangi so'zlar", "yangi so'zlarni ko'rsat", "sinonimlarim", "sinonimlar",
    "o'rganish hisoboti", "o'rganish natijalari", "qanday so'zlarni o'rgandin",
    "yangi so'zlarni o'rgandingmi",
}
ASK_FREQ = {
    "ko'p so'raydiganlarim", "eng ko'p nima so'rayman", "tez-tez so'raganlarim",
    "eng ko'p so'raganlarim", "ko'p so'ragan narsalarim", "eng ko'p so'raydiganim",
}
ASK_HABITS = {"odatlarim", "odatlarim qanday", "mening odatlarim", "odatlarim nima"}


class Adapt:
    def __init__(self, mind):
        self.mind = mind
        self.pending = None      # (phrase, intent)
        self.unk_turn = None     # oxirgi tushunilmagan gap raqami
        self.unk_text = None
        self._fresh = False

    @property
    def st(self):
        data = self.mind.data.setdefault("learn", {})
        data.setdefault("aliases", [])
        data.setdefault("freq", {})
        data.setdefault("hours", {})
        return data

    # ---------- foydalanuvchi so'rovlari ----------
    def handle(self, raw, n):
        if self.pending is not None:
            phrase, intent = self.pending
            self.pending = None

            if n in YES:
                return self._accept(phrase, intent)

            if n in NO:
                return "Xo'p, buni o'rganmayman."
            # boshqa gap: taklif bekor, gap odatdagidek ishlanadi

        if n in ASK_LEARNED:
            return self.learned()

        if n in ASK_FREQ:
            return self.frequent()

        if n in ASK_HABITS:
            return self.habits()

        return None

    def _learner(self):
        try:
            return self.mind.jarvis.learner
        except Exception:
            return None

    def _accept(self, phrase, intent):
        learner = self._learner()

        if learner is None or not learner.add_phrase(phrase, intent):
            return "Buni saqlab bo'lmadi."

        aliases = self.st["aliases"]
        aliases[:] = [a for a in aliases if a["p"] != phrase]
        aliases.append({"p": phrase, "i": intent,
                        "t": datetime.now().strftime("%Y-%m-%d")})
        del aliases[:-MAX_ALIASES]
        self.mind.save()

        from ozbilim import INTENT_LABEL
        return "O'rgandim: «" + phrase + "» endi «" + INTENT_LABEL.get(intent, intent) + "» buyrug'i."

    # ---------- har bir javobdan keyin ----------
    def suggest(self, raw, norm, source):
        """Hozirgi javobga qo'shiladigan taklif matni (yoki "")."""
        try:
            return self._suggest(raw, norm, source)
        except Exception as error:
            print("ONG suggest error:", error)
            return ""

    def _suggest(self, raw, norm, source):
        if not source or not source.startswith("buyruq:"):
            return ""

        if self.unk_turn is None or self.unk_text is None:
            return ""

        # faqat darhol oldingi gap tushunilmagan bo'lsa
        if self.unk_turn != int(self.mind.data.get("turns", 0)):
            return ""

        intent = source.split(":", 1)[1]
        phrase = self.unk_text.strip()
        key = phrase.lower()

        if intent not in SAFE_INTENTS:
            return ""

        if not (4 <= len(phrase) <= 60) or key == norm:
            return ""

        if self.mind._clean(key) in YES or self.mind._clean(key) in NO:
            return ""

        learner = self._learner()
        if learner is not None:
            try:
                if learner.find_intent(phrase):
                    return ""
            except Exception:
                pass

        self.pending = (phrase, intent)
        self._fresh = True
        self.unk_turn = None
        return "«" + phrase + "» ni ham shu buyruq deb o'rganaymi? (ha / yo'q)"

    def record(self, raw, norm, source):
        """Mind.observe ichidan: statistikani yig'adi (saqlashni Mind qiladi)."""
        source = source or "boshqa"
        turns = int(self.mind.data.get("turns", 0))

        if self.pending is not None and not self._fresh:
            self.pending = None  # taklif faqat keyingi gap uchun amal qiladi
        self._fresh = False

        if source == "tushunmadi":
            self.unk_turn = turns
            self.unk_text = str(raw).strip()
            counts = self.st.setdefault("unk", {})
            phrase = self.unk_text.lower()[:60]
            if phrase:
                counts[phrase] = counts.get(phrase, 0) + 1
                if len(counts) > 60:
                    for k in sorted(counts, key=counts.get)[:len(counts) - 60]:
                        counts.pop(k, None)
            return

        if source in ("ong", "oyrgatish", "boshqa"):
            return

        st = self.st
        key = norm.strip(" .,!?:;")
        if key:
            item = st["freq"].get(key) or {"n": 0, "s": source}
            item["n"] += 1
            item["s"] = source
            item["t"] = datetime.now().isoformat(timespec="seconds")
            st["freq"][key] = item

            if len(st["freq"]) > MAX_FREQ:
                weakest = sorted(st["freq"].items(),
                                 key=lambda kv: (kv[1]["n"], kv[1].get("t", "")))
                for k, _ in weakest[:len(st["freq"]) - MAX_FREQ]:
                    st["freq"].pop(k, None)

        hours = st["hours"].setdefault(source, [0] * 24)
        hours[datetime.now().hour] += 1

    # ---------- hisobotlar ----------
    def learned(self):
        lines = []
        aliases = self.st["aliases"]

        if aliases:
            lines.append("Yangi so'zlar (sinonimlar):")
            for a in aliases[-8:]:
                lines.append("• «" + a["p"] + "» = " + self._label("buyruq:" + a["i"]))

        learner = self._learner()
        try:
            count = int(learner.count()) if learner else 0
        except Exception:
            count = 0

        if count:
            lines.append("Siz o'rgatgan jami yozuvlar: " + str(count) + " ta")

        corrections = self.mind.data.get("self", {}).get("stats", {}).get("corrections", 0)
        if corrections:
            lines.append("Tuzatishlaringiz: " + str(corrections) + " ta")

        if not lines:
            return ("Hozircha yangi narsa o'rganmadim. Tushunmagan gapimdan keyin "
                    "boshqa so'z bilan buyruq bersangiz, o'rganishni taklif qilaman.")

        return "\n".join(lines)

    @staticmethod
    def _label(source):
        from ozbilim import SelfModel
        return SelfModel._label(source)

    def frequent(self):
        freq = self.st["freq"]
        items = [(k, v) for k, v in freq.items() if v["n"] >= 2]

        if not items:
            return "Hali takrorlangan so'rovlar yo'q. Ko'proq gaplashgach aytib bera olaman."

        items.sort(key=lambda kv: -kv[1]["n"])
        return "Eng ko'p so'raganlaringiz:\n" + "\n".join(
            "• " + k + " - " + str(v["n"]) + " marta" for k, v in items[:5])

    def habits(self):
        lines = []

        for source, hours in self.st["hours"].items():
            total = sum(hours)
            peak = max(hours)

            if total < 4 or peak < 3 or peak / float(total) < 0.4:
                continue

            hour = hours.index(peak)
            lines.append("• " + self._label(source) + ": ko'pincha soat " + str(hour) + " atrofida")

        if not lines:
            return ("Hali aniq odatingizni payqamadim: buning uchun bir xil narsani "
                    "kamida bir necha marta, taxminan bir vaqtda so'rashingiz kerak.")

        return "Payqaganlarim:\n" + "\n".join(lines)
