# -*- coding: utf-8 -*-
"""JARVIS "ongi" - 5-qadam: fikrlash (rejalashtirish).

Bir gapda bir necha buyruq aytilsa, Jarvis ularni qadamlarga bo'lib,
ketma-ket bajaradi:

    "soat nechi va bugun sana nima"
    "avval soatni ayt, keyin sanani ayt"

Xavfsizlik qoidalari:
  * Faqat HAMMA qism alohida buyruq sifatida tanilsa reja tuziladi
    (aks holda gap odatdagidek ishlanadi, "va" so'zi uchun adashmaydi).
  * Tozalash, o'chirish, unutish kabi xavfli so'zlar bo'lsa reja tuzilmaydi.
  * Eng ko'pi bilan 6 qadam. Bir qadam bajarilmasa, qolganlari davom etadi
    va oxirida qaysi biri bajarilmagani aytiladi.

"qanday bajarasan: ..." - gapni bajarmasdan, qadamlarini ko'rsatadi.
"""
import re

MAX_STEPS = 6

DANGER = re.compile(
    r"\b(tozala\w*|o'chir\w*|unut\w*|delete|rm|format\w*|reset\w*|"
    r"qayta tikla\w*|tiklash)\b"
)

SKIP_START = re.compile(r"^(?:o'rgat|unut|eslab qol|reja:|terminal|run\b)")

PREVIEW = re.compile(r"^(?:qanday bajarasan|rejani ko'rsat|reja ko'rsat|qadamlarga bo'l)\s*:?\s*(.+)$")

LEAD = re.compile(r"^(?:avval|oldin|birinchi(?:dan)?|dastlab)\s+", re.I)

SEPARATORS = re.compile(
    r"\s*(?:;|\n)\s*"
    r"|\s*,\s+(?:va\s+)?(?:keyin(?:\s+esa)?|so'ng(?:ra)?|undan keyin|shundan keyin)\s+"
    r"|\s+(?:va\s+)?(?:keyin(?:\s+esa)?|so'ng(?:ra)?|undan keyin|shundan keyin)\s+"
    r"|\s*,\s+(?:va\s+)?"
    r"|\s+(?:va|hamda)\s+",
    re.I,
)

APOSTROPHES = "ʻʼ’‘`´"


def _fix(text):
    for ch in APOSTROPHES:
        text = text.replace(ch, "'")
    return text


class Planner:
    def __init__(self, mind):
        self.mind = mind

    # ---------- bo'lish ----------
    def split(self, raw):
        text = LEAD.sub("", _fix(str(raw).strip()))
        parts = [p.strip(" .!?") for p in SEPARATORS.split(text)]
        return [p for p in parts if len(p) >= 2]

    # ---------- tanish (hech narsa bajarmasdan) ----------
    def understood(self, part):
        engine = self.mind.jarvis
        if engine is None:
            return False

        try:
            norm = engine._normalize(part)

            if engine.skills.match(norm) is not None:
                return True

            if engine.detect_local_command(norm):
                return True

            if engine.learner.find_intent(part):
                return True

            return bool(engine._brain_knows(part))
        except Exception as error:
            print("ONG planner understood error:", error)
            return False

    def taught(self, text):
        """Butun gap foydalanuvchi o'rgatgan javob yoki buyruq bo'lsa True."""
        engine = self.mind.jarvis
        try:
            if engine.learner.find_intent(text):
                return True
            return engine.learner.fuzzy_answer(text) is not None
        except Exception:
            return False

    # ---------- asosiy kirish ----------
    def handle(self, raw, n):
        engine = self.mind.jarvis
        if engine is None or getattr(engine, "_in_plan", False):
            return None

        text = _fix(str(raw).strip())
        low = text.lower()

        preview = PREVIEW.match(low)
        if preview:
            return self.preview(text[len(text) - len(preview.group(1)):])

        if len(text) < 5 or SKIP_START.match(low) or DANGER.search(low):
            return None

        parts = self.split(text)
        if not (2 <= len(parts) <= MAX_STEPS):
            return None

        # Siz o'rgatgan gap bo'lsa (masalan, "salom va xayr"), bo'lmaymiz
        if self.taught(text):
            return None

        if not all(self.understood(p) for p in parts):
            return None

        self.mind.source_hint = "reja"
        return self.execute(parts)

    def preview(self, text):
        parts = self.split(text)

        if len(parts) < 2:
            return "Bu gap bitta qadamdan iborat: bajarish uchun shunchaki yozing."

        lines = []
        for index, part in enumerate(parts[:MAX_STEPS], 1):
            mark = "" if self.understood(part) else " (tushunmadim)"
            lines.append(str(index) + ") " + part + mark)

        return "Bajarish rejasi:\n" + "\n".join(lines)

    def execute(self, parts):
        engine = self.mind.jarvis
        results = []
        failed = []

        engine._in_plan = True
        try:
            for index, part in enumerate(parts, 1):
                try:
                    reply = engine.process(part)
                except Exception as error:
                    print("ONG plan step error:", error)
                    reply = None

                # Qadam o'rgatish so'rovini ochib qo'ygan bo'lsa, uni yopamiz
                if getattr(engine, "pending_teach", None) is not None:
                    engine.pending_teach = None
                    reply = None

                reply = str(reply).strip() if reply else ""

                if not reply:
                    failed.append(part)
                    reply = "bajarilmadi"

                results.append(str(index) + ") " + reply)
        finally:
            engine._in_plan = False

        head = str(len(parts)) + " qadamni bajardim:\n"
        tail = ""

        if failed:
            tail = "\n\nBajarilmadi: " + "; ".join(failed)

        return head + "\n".join(results) + tail
