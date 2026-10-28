# -*- coding: utf-8 -*-
"""JARVIS "ongi" - 1-qadam: xotira va kontekst.

Nima qiladi:
  * Foydalanuvchi haqidagi faktlarni (ism, yosh, shahar, kasb, yoqtirganlari)
    suhbatdan o'zi ajratib oladi va ong.json faylida doimiy saqlaydi.
  * Suhbat kontekstini tushunadi: "yana", "qayta ayt", "nima dedim",
    "nima haqida gaplashdik".
  * "men haqimda nima bilasan", "yoshim nechida" kabi savollarga javob beradi.
  * "ismimni unut" kabi buyruqlar bilan faktni o'chiradi.

Tashqi AI yoki internet kerak emas.
"""
import json
import os
import re
import shutil
from datetime import datetime

from ozbilim import SelfModel
from ornash import Adapt
from tashabbus import Initiative
from fikr import Planner

MAX_LOG = 200
MAX_LIKES = 30

REPEAT_CMD = {
    "yana", "yana bir marta", "yana bir bor", "takrorla", "takrorlang",
    "qaytar", "qaytaring", "oldingisini qayta bajar", "oldingisini bajar",
    "oldingisi", "shuni yana qil", "yana shuni qil", "yana qil",
}

REPEAT_ANSWER = {
    "qayta ayt", "qayta ayting", "nima deding", "nima dedingiz",
    "eshitmadim", "tushunmadim", "yana ayt", "yana ayting",
    "javobni takrorla", "javobingni takrorla",
}

ASK_LAST_USER = {
    "nima dedim", "oldin nima dedim", "nima so'radim", "oldin nima so'radim",
    "oldingi savolim nima edi", "oldingi savolim", "men nima dedim",
}

ASK_TOPICS = {
    "nima haqida gaplashdik", "nimalar haqida gaplashdik",
    "nima gaplashdik", "bugun nima gaplashdik", "nimalar so'radim",
}

ASK_ABOUT_ME = (
    "men haqimda nima bilasan", "men haqimda nimalarni bilasan",
    "men haqimda nimalar bilasan", "meni taniysanmi", "men kimman",
    "men haqimda eslaganlaring", "meni bilasanmi",
)

LABELS = {
    "ism": "Ismingiz",
    "yosh": "Yoshingiz",
    "shahar": "Shahringiz",
    "kasb": "Kasbingiz",
}


def _data_file():
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ong.json")

    try:
        from android.storage import app_storage_path
        base = os.path.join(app_storage_path(), "JARVIS")
    except Exception:
        return bundled

    try:
        os.makedirs(base, exist_ok=True)
        target = os.path.join(base, "ong.json")

        if not os.path.exists(target) and os.path.exists(bundled):
            shutil.copyfile(bundled, target)

        return target
    except Exception as error:
        print("ONG path error:", error)
        return bundled


def _cap(value):
    value = str(value).strip()
    return value[:1].upper() + value[1:] if value else value


class Mind:
    def __init__(self, jarvis=None, legacy_facts=None):
        self.jarvis = jarvis
        self.legacy_facts = legacy_facts  # () -> [str]
        self.file = _data_file()
        self.data = self._empty()
        self.last_cmd = None
        self.selfmodel = SelfModel(self)
        self.adapt = Adapt(self)
        self.initiative = Initiative(self)
        self.planner = Planner(self)
        self.source_hint = None
        self.load()

    # ---------- saqlash ----------
    @staticmethod
    def _empty():
        return {
            "profile": {},
            "likes": [],
            "dislikes": [],
            "extra": {},
            "self": {},
            "learn": {},
            "init": {},
            "log": [],
            "first_seen": datetime.now().isoformat(timespec="seconds"),
            "turns": 0,
        }

    def load(self):
        try:
            if os.path.exists(self.file):
                with open(self.file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)

                if isinstance(loaded, dict):
                    base = self._empty()
                    base.update(loaded)
                    self.data = base

            hist = [e for e in self.data["log"] if e.get("u")]
            self.last_cmd = None

            for entry in reversed(hist):
                if entry.get("cmd"):
                    self.last_cmd = entry["u"]
                    break
        except Exception as error:
            print("ONG load error:", error)
            self.data = self._empty()

    def save(self):
        try:
            tmp = self.file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.file)
        except Exception as error:
            print("ONG save error:", error)

    def clear(self):
        self.data = self._empty()
        self.last_cmd = None
        self.save()

    # ---------- foydalanish uchun ----------
    @property
    def name(self):
        return self.data["profile"].get("ism", "")

    def get(self, key, default=""):
        return self.data["profile"].get(key, default)

    def set(self, key, value):
        self.data["profile"][key] = str(value).strip()
        self.save()

    def take_source(self):
        """Ong javobi qaysi turdan ekanini aytadi (masalan, "reja")."""
        hint, self.source_hint = self.source_hint, None
        return hint

    def awaiting(self):
        """Jarvis o'z taklifiga (ha / yo'q) javob kutyaptimi."""
        return self.adapt.pending is not None or self.initiative.pending is not None

    def suggest(self, raw, norm, source):
        """Javobga qo'shiladigan o'rganish taklifi (yoki "")."""
        clean = self._clean(norm or "")
        return (
            self.adapt.suggest(raw, clean, source)
            or self.initiative.suggest(raw, clean, source)
        )

    # ---------- asosiy kirish nuqtalari ----------
    def handle(self, raw, norm):
        """Javob qaytaradi yoki None (boshqa ishlovchilarga o'tadi)."""
        try:
            return self._handle(raw, norm)
        except Exception as error:
            print("ONG handle error:", error)
            return None

    def observe(self, raw, response, norm=None, source=None, correction=False):
        """Har bir javobdan keyin chaqiriladi: suhbatni yozib boradi."""
        try:
            self._observe(raw, response, norm)
            self.selfmodel.record(raw, response, source, correction)
            self.adapt.record(raw, self._clean(norm if norm is not None else str(raw).lower()), source)
            self.initiative.record()
            self.save()
        except Exception as error:
            print("ONG observe error:", error)

    # ---------- ichki ----------
    def _clean(self, norm):
        return norm.strip(" .,!?:;")

    def _handle(self, raw, norm):
        n = self._clean(norm)
        if not n:
            return None

        planned = self.planner.handle(raw, n)
        if planned:
            return planned

        if n in REPEAT_CMD:
            return self._repeat_command()

        if n in REPEAT_ANSWER:
            return self._repeat_answer()

        if n in ASK_LAST_USER:
            return self._ask_last_user()

        if n in ASK_TOPICS:
            return self._ask_topics()

        learned = self.adapt.handle(raw, n)
        if learned:
            return learned

        taken = self.initiative.handle(raw, n)
        if taken:
            return taken

        own = self.selfmodel.handle(raw, n)
        if own:
            return own

        forgot = self._forget(n)
        if forgot:
            return forgot

        if any(p in n for p in ASK_ABOUT_ME):
            return self._about_me()

        answer = self._answer_profile_question(n)
        if answer:
            return answer

        return self._learn_statement(n)

    # --- takrorlash ---
    def _repeat_command(self):
        if not self.last_cmd or self.jarvis is None:
            return "Takrorlash uchun oldingi buyruq topilmadi."

        cmd = self.last_cmd
        reply = self.jarvis.process(cmd)
        return reply if reply else "Bajarildi."

    def _last_entry(self, key="a"):
        for entry in reversed(self.data["log"]):
            if entry.get(key):
                return entry
        return None

    def _repeat_answer(self):
        entry = None
        for e in reversed(self.data["log"]):
            if e.get("a") and not e.get("meta"):
                entry = e
                break
        if not entry:
            return "Hali hech narsa demadim."
        return entry["a"]

    def _ask_last_user(self):
        entry = None
        for e in reversed(self.data["log"]):
            if e.get("u") and not e.get("meta"):
                entry = e
                break
        if not entry:
            return "Hali hech narsa demadingiz."
        return "Siz: \"" + entry["u"] + "\" dedingiz."

    def _ask_topics(self):
        today = datetime.now().strftime("%Y-%m-%d")
        items = []

        for entry in self.data["log"]:
            if not entry.get("u") or not str(entry.get("t", "")).startswith(today):
                continue
            if entry.get("meta"):
                continue
            if entry["u"] in items:
                items.remove(entry["u"])
            items.append(entry["u"])

        if not items:
            return "Bugun hali gaplashmadik."

        last = items[-6:]
        return "Bugun shular haqida gaplashdik:\n" + "\n".join("• " + x for x in last)

    # --- profil ---
    def _about_me(self):
        lines = []
        prof = self.data["profile"]

        for key in ("ism", "yosh", "shahar", "kasb"):
            if prof.get(key):
                lines.append(LABELS[key] + ": " + _cap(prof[key]))

        for key, value in self.data["extra"].items():
            lines.append(_cap(key) + ": " + value)

        if self.data["likes"]:
            lines.append("Yoqtirasiz: " + ", ".join(self.data["likes"][-10:]))

        if self.data["dislikes"]:
            lines.append("Yoqtirmaysiz: " + ", ".join(self.data["dislikes"][-10:]))

        try:
            legacy = self.legacy_facts() if self.legacy_facts else []
        except Exception:
            legacy = []

        for fact in legacy[-10:]:
            if fact.startswith("name="):
                continue
            lines.append(_cap(fact))

        if not lines:
            return ("Hozircha siz haqingizda hech narsa bilmayman. "
                    "Ismingiz, yoshingiz, shahringiz yoki nimani yoqtirishingizni "
                    "ayting, eslab qolaman. Masalan: \"ismim Ali\".")

        return "Siz haqingizda bilganlarim:\n" + "\n".join("• " + x for x in lines)

    def _answer_profile_question(self, n):
        prof = self.data["profile"]

        if re.search(r"\b(ismim|ismimni)\b.*\b(nima|ayt|eslaysanmi|bilasanmi)\b", n):
            if prof.get("ism"):
                return "Ismingiz " + _cap(prof["ism"]) + "."
            return None

        if re.search(r"\byoshim\b.*\b(nechi|nechida|necha)\b", n) or n in ("yoshimni ayt",):
            if prof.get("yosh"):
                return "Siz " + prof["yosh"] + " yoshdasiz."
            return "Yoshingizni hali bilmayman. \"Yoshim 25\" deb aytsangiz, eslab qolaman."

        if re.search(r"qayerda yashayman|shahrim\w* (nima|qaysi)|qayerlikman", n):
            if prof.get("shahar"):
                return "Siz " + _cap(prof["shahar"]) + "da yashaysiz."
            return "Shahringizni hali bilmayman. \"Men Toshkentda yashayman\" deb ayting."

        if re.search(r"kasbim\w* (nima|qaysi)|nima ish qilaman|qayerda ishlayman", n):
            if prof.get("kasb"):
                return "Kasbingiz: " + prof["kasb"] + "."
            return "Kasbingizni hali bilmayman. \"Kasbim dasturchi\" deb ayting."

        if re.search(r"nimani yoqtiraman|nimalarni yoqtiraman|nimani yaxshi ko'raman", n):
            if self.data["likes"]:
                return "Siz shularni yoqtirasiz: " + ", ".join(self.data["likes"]) + "."
            return "Nimalarni yoqtirishingizni hali bilmayman."

        match = re.match(r"(?:mening )?sevimli (.+?)(?:im|m)? (?:nima|qaysi)$", n)
        if match:
            key = "sevimli " + match.group(1).strip()
            val = self.data["extra"].get(key)
            if val:
                return "Sevimli " + match.group(1).strip() + "ingiz: " + val + "."
            return None

        return None

    def _forget(self, n):
        if re.search(r"men haqimda(gi)? (hamma|barcha)\w* (narsa\w* )?(ni )?unut", n) or n in (
            "meni unut", "hammasini unut", "men haqimdagi hamma narsani unut",
        ):
            if n == "hammasini unut":
                return None  # ehtimol, boshqa narsa nazarda tutilgan
            self.data["profile"] = {}
            self.data["likes"] = []
            self.data["dislikes"] = []
            self.data["extra"] = {}
            self.save()
            return "Siz haqingizdagi hamma ma'lumotni unutdim."

        mapping = (
            (r"^ismim\w* unut", "ism", "ismingizni"),
            (r"^yoshim\w* unut", "yosh", "yoshingizni"),
            (r"^shahrim\w* unut", "shahar", "shahringizni"),
            (r"^kasbim\w* unut", "kasb", "kasbingizni"),
        )

        for pattern, key, label in mapping:
            if re.search(pattern, n):
                if self.data["profile"].pop(key, None) is not None:
                    self.save()
                    return "Xo'p, " + label + " unutdim."
                return "Men baribir " + label + " bilmas edim."

        if re.search(r"^yoqtirgan\w* (narsa\w*|lar\w*)\w* unut|^yoqtirganlarimni unut", n):
            self.data["likes"] = []
            self.data["dislikes"] = []
            self.save()
            return "Yoqtirgan va yoqtirmagan narsalaringizni unutdim."

        return None

    # --- suhbatdan faktlarni ajratib olish ---
    def _learn_statement(self, n):
        prof = self.data["profile"]

        match = re.match(r"^(?:mening )?ismim ([a-zа-яё'\-]+)$", n)
        if match:
            name = match.group(1)
            if name in ("nima", "kim", "nimaligini"):
                return None
            old = prof.get("ism")
            prof["ism"] = name
            self.save()
            if old and old.lower() != name.lower():
                return "Yaxshi, endi sizni " + _cap(name) + " deb chaqiraman."
            return "Tanishganimdan xursandman, " + _cap(name) + "!"

        match = re.match(r"^(?:mening )?yoshim (\d{1,3})(?: da)?$", n) or re.match(
            r"^men (\d{1,3}) yoshdaman$", n)
        if match:
            age = int(match.group(1))
            if 3 <= age <= 120:
                prof["yosh"] = str(age)
                self.save()
                return "Tushundim, " + str(age) + " yosh. Eslab qoldim."
            return None

        match = re.match(r"^men ([a-zа-яё'\-]+?)(?:da|dan|ta|tada) yashayman$", n) or re.match(
            r"^men ([a-zа-яё'\-]+?)(?:lik|likman)$", n)
        if match:
            city = match.group(1).strip("'")
            if len(city) >= 3:
                prof["shahar"] = city
                self.save()
                return _cap(city) + " - yaxshi joy. Eslab qoldim."
            return None

        match = re.match(r"^(?:mening )?(?:kasbim|ishim) ([a-zа-яё' \-]{3,40})$", n)
        if match:
            job = match.group(1).strip()
            if job not in ("nima", "qaysi"):
                prof["kasb"] = job
                self.save()
                return "Tushundim, kasbingiz: " + job + "."
            return None

        match = re.match(r"^(?:men )?(.{2,40}?)(?:ni|ni juda|ni ko'p) (?:yoqtiraman|yaxshi ko'raman)$", n)
        if match:
            item = match.group(1).strip()
            if item and not re.search(r"\b(nimani|nima|kimni)\b", item):
                self._add_pref("likes", item)
                self.data["dislikes"] = [x for x in self.data["dislikes"] if x != item]
                self.save()
                return "Yaxshi, " + item + " yoqishini eslab qoldim."
            return None

        match = re.match(r"^(?:men )?(.{2,40}?)ni (?:yoqtirmayman|yoqtirmay man|yomon ko'raman)$", n)
        if match:
            item = match.group(1).strip()
            if item and not re.search(r"\b(nimani|nima|kimni)\b", item):
                self._add_pref("dislikes", item)
                self.data["likes"] = [x for x in self.data["likes"] if x != item]
                self.save()
                return "Tushundim, " + item + " yoqmasligini eslab qoldim."
            return None

        match = re.match(r"^(?:mening )?sevimli ([a-zа-яё' ]{2,25}?)(?:im|m|i)? ([a-zа-яё0-9' \-]{2,40})$", n)
        if match:
            key = "sevimli " + match.group(1).strip()
            val = match.group(2).strip()
            command_like = re.search(r"sevimli \S*ni\b", n) or re.search(
                r"\b(qo'y|och|ayt|top|qil|ko'rsat|chaqir|yoq|o'chir|boshla)$", val)
            if val and val not in ("nima", "qaysi") and not command_like:
                self.data["extra"][key] = val
                self.save()
                return "Eslab qoldim: " + key + " - " + val + "."
            return None

        return None

    def _add_pref(self, key, item):
        items = self.data[key]
        if item in items:
            items.remove(item)
        items.append(item)
        del items[:-MAX_LIKES]

    # --- suhbat jurnali ---
    def _observe(self, raw, response, norm=None):
        norm = self._clean(norm if norm is not None else str(raw).lower())
        meta = (
            norm in REPEAT_CMD or norm in REPEAT_ANSWER
            or norm in ASK_LAST_USER or norm in ASK_TOPICS
        )

        pending = False
        if self.jarvis is not None:
            for attr in ("pending_teach", "pending_correct",
                         "pending_image_name", "pending_file_name"):
                if getattr(self.jarvis, attr, None) is not None:
                    pending = True

        is_cmd = (not meta) and (not pending) and bool(response)

        entry = {
            "t": datetime.now().isoformat(timespec="seconds"),
            "u": str(raw).strip()[:300],
            "a": str(response)[:600],
        }
        if meta:
            entry["meta"] = 1
        if is_cmd:
            entry["cmd"] = 1
            self.last_cmd = entry["u"]

        self.data["log"].append(entry)
        del self.data["log"][:-MAX_LOG]
        self.data["turns"] = int(self.data.get("turns", 0)) + 1
        self.save()
