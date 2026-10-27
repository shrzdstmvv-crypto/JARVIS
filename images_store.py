
import json
import os
from datetime import datetime
from difflib import SequenceMatcher


class ImageStore:
    """Qabul qilingan rasmlar ro'yxati: nomi va fayl manzili.

    Rasmlarning o'zi ilovaning yopiq papkasida turadi, bu yerda esa
    ularning nomlari saqlanadi. Ro'yxat ilova yangilanganda ham
    o'chmaydigan papkada (jarvis_images.json) turadi.
    """

    # Qidiruvda e'tiborga olinmaydigan so'zlar
    STOP_WORDS = {
        "rasm", "rasmi", "rasmini", "rasmni", "rasmim", "rasmimni",
        "surat", "suratim", "suratni", "suratini",
        "foto", "fotosi", "fotosini", "fotosurat",
        "ko'rsat", "ko'rsatib", "ko'rsating", "ko'rsatgin",
        "ber", "bering", "top", "topib", "chiqar", "och", "qani",
        "oxirgi", "menga", "iltimos", "jarvis", "bu", "shu", "ayt",
        "mening", "meni", "men", "ni", "va"
    }

    FILENAME = "jarvis_images.json"

    def __init__(self, normalize, file=None):
        self.normalize = normalize
        self.file = file or self._data_file()
        self.entries = []
        self.load()

    def _data_file(self):
        local = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            self.FILENAME
        )

        try:
            from android.storage import app_storage_path
            base = os.path.join(app_storage_path(), "JARVIS")
            os.makedirs(base, exist_ok=True)
            return os.path.join(base, self.FILENAME)
        except Exception:
            return local

    # SAQLASH VA YUKLASH
    def load(self):
        self.entries = []

        if not os.path.exists(self.file):
            return

        try:
            with open(self.file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("path"):
                        self.entries.append({
                            "path": str(item["path"]),
                            "name": str(item.get("name", "")),
                            "orig": str(item.get("orig", "")),
                            "added": str(item.get("added", ""))
                        })

        except Exception as error:
            print("ImageStore load error:", error)

    def save(self):
        try:
            temp = self.file + ".tmp"

            with open(temp, "w", encoding="utf-8") as file:
                json.dump(self.entries, file, ensure_ascii=False, indent=2)

            os.replace(temp, self.file)
            return True

        except Exception as error:
            print("ImageStore save error:", error)
            return False

    # RASM QO'SHISH VA NOMLASH
    def _entry(self, path):
        for entry in self.entries:
            if entry["path"] == path:
                return entry
        return None

    def add(self, path, orig=""):
        path = str(path)
        entry = self._entry(path)

        if entry is None:
            entry = {
                "path": path,
                "name": "",
                "orig": str(orig),
                "added": datetime.now().isoformat(timespec="seconds")
            }
            self.entries.append(entry)
            self.save()

        return entry

    def _unique_name(self, name, skip_entry=None):
        taken = {
            self.normalize(e["name"])
            for e in self.entries
            if e["name"] and e is not skip_entry
        }

        candidate = name
        number = 2

        while self.normalize(candidate) in taken:
            candidate = name + " " + str(number)
            number += 1

        return candidate

    def set_name(self, path, name):
        entry = self._entry(str(path))
        name = str(name).strip()

        if entry is None or not self.normalize(name):
            return None

        entry["name"] = self._unique_name(name, entry)
        self.save()
        return entry["name"]

    def name_last(self, name):
        entry = self.last()

        if entry is None:
            return None

        return self.set_name(entry["path"], name)

    # QIDIRISH
    def _alive(self):
        return [e for e in self.entries if os.path.exists(e["path"])]

    def last(self):
        alive = self._alive()
        return alive[-1] if alive else None

    def names(self):
        return [e["name"] for e in self._alive() if e["name"]]

    def count(self):
        return len(self._alive())

    @staticmethod
    def _same_word(a, b):
        if a == b:
            return True

        # Qo'shimchalar uchun: "mashinam" va "mashinamni"
        if min(len(a), len(b)) >= 4 and (
            a.startswith(b) or b.startswith(a)
        ):
            return True

        # Yozuv xatolari uchun
        if min(len(a), len(b)) >= 5:
            return SequenceMatcher(None, a, b).ratio() >= 0.85

        return False

    def find(self, text):
        words = set(self.normalize(text).split()) - self.STOP_WORDS

        if not words:
            return None

        best, best_size = None, 0

        # Yangilaridan boshlab qidiramiz
        for entry in reversed(self._alive()):
            if not entry["name"]:
                continue

            name_words = (
                set(self.normalize(entry["name"]).split()) - self.STOP_WORDS
            )

            if not name_words:
                continue

            matched = all(
                any(self._same_word(w, n) for w in words)
                for n in name_words
            )

            if matched and len(name_words) > best_size:
                best, best_size = entry, len(name_words)

        if best is not None:
            return best

        # Nomning faqat bir qismi aytilgan bo'lsa ("hisobot" -> "oylik hisobot")
        for entry in reversed(self._alive()):
            if not entry["name"]:
                continue

            name_words = (
                set(self.normalize(entry["name"]).split()) - self.STOP_WORDS
            )

            if name_words and all(
                any(self._same_word(w, n) for n in name_words)
                for w in words
            ):
                return entry

        return None

    # O'CHIRISH
    def remove(self, entry):
        if entry in self.entries:
            self.entries.remove(entry)
            self.save()

        try:
            if os.path.exists(entry["path"]):
                os.remove(entry["path"])
        except Exception as error:
            print("ImageStore remove error:", error)


class FileStore(ImageStore):
    """Yuklangan fayllar (hujjat, PDF va hokazo): nom bilan saqlash va topish."""

    FILENAME = "jarvis_files.json"

    STOP_WORDS = ImageStore.STOP_WORDS | {
        "fayl", "faylni", "faylini", "faylim", "faylimni", "fayllar",
        "hujjat", "hujjatni", "hujjatim", "yuklab", "yukla", "saqla",
        "yubor", "ochib"
    }
