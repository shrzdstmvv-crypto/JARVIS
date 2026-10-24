
import json
import os
from difflib import SequenceMatcher


class Learner:
    """JARVIS o'rgatish rejimi.

    Foydalanuvchi o'rgatgan narsalar kodda emas, alohida faylda
    (jarvis_learned.json) saqlanadi. Android'da bu fayl ilova
    yangilanganda ham o'chmaydigan papkada turadi.
    """

    # "buyruq <so'z>" deganda ishlatiladigan nomlar
    ALIASES = {
        "salom": "greeting",
        "xayr": "goodbye",
        "soat": "time",
        "vaqt": "time",
        "sana": "date",
        "yordam": "help",
        "youtube": "youtube",
        "instagram": "instagram",
    }

    FUZZY_LIMIT = 0.85

    def __init__(self, normalize, file=None):
        self.normalize = normalize
        self.file = file or self._data_file()
        self.answers = {}
        self.phrases = {}
        self.load()

    def _data_file(self):
        local = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "jarvis_learned.json"
        )

        try:
            from android.storage import app_storage_path
            base = os.path.join(app_storage_path(), "JARVIS")
            os.makedirs(base, exist_ok=True)
            return os.path.join(base, "jarvis_learned.json")
        except Exception:
            return local

    # SAQLASH VA YUKLASH
    def load(self):
        self.answers = {}
        self.phrases = {}

        if not os.path.exists(self.file):
            return

        try:
            with open(self.file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data.get("answers"), dict):
                self.answers = data["answers"]

            if isinstance(data.get("phrases"), dict):
                self.phrases = data["phrases"]

        except Exception as error:
            print("Learner load error:", error)

    def save(self):
        try:
            temp = self.file + ".tmp"

            with open(temp, "w", encoding="utf-8") as file:
                json.dump(
                    {"answers": self.answers, "phrases": self.phrases},
                    file,
                    ensure_ascii=False,
                    indent=2
                )

            os.replace(temp, self.file)
            return True

        except Exception as error:
            print("Learner save error:", error)
            return False

    # O'RGATISH
    def add_answer(self, question, answer):
        key = self.normalize(question)
        answer = str(answer).strip()

        if not key or not answer:
            return False

        self.answers[key] = {"q": str(question).strip(), "a": answer}
        return self.save()

    def add_phrase(self, phrase, intent):
        key = self.normalize(phrase)

        if not key or not intent:
            return False

        self.phrases[key] = intent
        return self.save()

    def forget(self, question):
        key = self.normalize(question)
        removed = False

        if key in self.answers:
            del self.answers[key]
            removed = True

        if key in self.phrases:
            del self.phrases[key]
            removed = True

        if removed:
            self.save()

        return removed

    # QIDIRISH
    def exact_answer(self, text):
        item = self.answers.get(self.normalize(text))
        return item["a"] if item else None

    def _fuzzy(self, table, text):
        key = self.normalize(text)

        # Bir so'zli gaplarda taxminiy moslik ishlatilmaydi
        if not key or len(key.split()) < 2:
            return None

        best_key, best_score = None, 0.0

        for candidate in table:
            if len(candidate.split()) < 2:
                continue

            score = SequenceMatcher(None, key, candidate).ratio()

            if score > best_score:
                best_key, best_score = candidate, score

        if best_key is not None and best_score >= self.FUZZY_LIMIT:
            return best_key

        return None

    def fuzzy_answer(self, text):
        key = self._fuzzy(self.answers, text)
        return self.answers[key]["a"] if key else None

    def find_intent(self, text):
        key = self.normalize(text)

        if key in self.phrases:
            return self.phrases[key]

        match = self._fuzzy(self.phrases, text)
        return self.phrases[match] if match else None

    # MA'LUMOT
    def count(self):
        return len(self.answers) + len(self.phrases)

    def samples(self, limit=8):
        items = [item["q"] for item in self.answers.values()]
        items += list(self.phrases.keys())
        return items[-limit:]
