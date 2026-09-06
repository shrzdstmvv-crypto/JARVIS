import json
import os
import re
from difflib import SequenceMatcher


class LanguageBrain:

    def __init__(self, brain_file=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        self.brain_file = brain_file or os.path.join(
            base_dir,
            "jarvis_brain.json"
        )

        self.intents = {}
        self.phrase_index = []
        self.last_intent = None

        self.load()

    def normalize(self, text):
        if text is None:
            return ""

        text = str(text).lower().strip()

        replacements = {
            "ʻ": "'",
            "ʼ": "'",
            "’": "'",
            "‘": "'",
            "`": "'",
            "´": "'",
            "o‘": "o'",
            "g‘": "g'",
            "o’": "o'",
            "g’": "g'"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁўғқҳзчшъьэюя' +\-*/().%]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def load(self):
        self.intents = {}
        self.phrase_index = []

        if not os.path.exists(self.brain_file):
            return False

        try:
            with open(self.brain_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                for intent, phrases in data.items():

                    if isinstance(phrases, list):
                        clean_phrases = []

                        for phrase in phrases:
                            if phrase is None:
                                continue

                            phrase = str(phrase).strip()

                            if not phrase:
                                continue

                            clean_phrases.append(phrase)

                        if clean_phrases:
                            self.intents[str(intent)] = clean_phrases

                    elif isinstance(phrases, str):
                        self.intents[str(intent)] = [phrases]

            elif isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    intent = item.get("intent")
                    phrases = item.get("phrases", [])

                    if not intent:
                        continue

                    if isinstance(phrases, str):
                        phrases = [phrases]

                    if not isinstance(phrases, list):
                        continue

                    clean_phrases = []

                    for phrase in phrases:
                        if phrase is None:
                            continue

                        phrase = str(phrase).strip()

                        if phrase:
                            clean_phrases.append(phrase)

                    if clean_phrases:
                        self.intents[str(intent)] = clean_phrases

            for intent, phrases in self.intents.items():
                for phrase in phrases:
                    normalized = self.normalize(phrase)

                    if normalized:
                        self.phrase_index.append(
                            (
                                intent,
                                phrase,
                                normalized
                            )
                        )

            return bool(self.intents)

        except Exception as error:
            print("Language Brain load error:", error)
            self.intents = {}
            self.phrase_index = []
            return False

    def special_intent(self, text):
        normalized = self.normalize(text)

        if not normalized:
            return None

        greeting_words = {
            "salom",
            "hello",
            "hi",
            "hey",
            "qalaysan",
            "yaxshimisan",
            "assalomu alaykum"
        }

        goodbye_words = {
            "xayr",
            "hayr",
            "bye",
            "goodbye",
            "ko'rishguncha",
            "ko'rishamiz"
        }

        words = set(normalized.split())

        if normalized in greeting_words:
            return "greeting", 0.99

        if normalized in goodbye_words:
            return "goodbye", 0.99

        if "salom" in words or "hello" in words or "hi" in words:
            if "jarvis" in words or len(words) <= 3:
                return "greeting", 0.97

        if (
            "assalomu" in words
            and "alaykum" in words
        ):
            return "greeting", 0.99

        if (
            "xayr" in words
            or "hayr" in words
            or "goodbye" in words
            or "bye" in words
        ):
            return "goodbye", 0.98

        return None

    def similarity(self, text, phrase):
        text = self.normalize(text)
        phrase = self.normalize(phrase)

        if not text or not phrase:
            return 0.0

        if text == phrase:
            return 1.0

        if phrase in text:
            return 0.95

        if text in phrase:
            return 0.90

        text_words = set(text.split())
        phrase_words = set(phrase.split())

        if not text_words or not phrase_words:
            return 0.0

        intersection = text_words & phrase_words
        union = text_words | phrase_words

        jaccard = len(intersection) / len(union)

        coverage = len(intersection) / len(phrase_words)

        sequence = SequenceMatcher(
            None,
            text,
            phrase
        ).ratio()

        score = (
            jaccard * 0.45
            + coverage * 0.30
            + sequence * 0.25
        )

        return min(score, 1.0)

    def predict(self, text):
        normalized = self.normalize(text)

        if not normalized:
            return "unknown", 0.0

        special = self.special_intent(normalized)

        if special:
            intent, confidence = special
            self.last_intent = intent
            return intent, confidence

        for intent, phrase, normalized_phrase in self.phrase_index:
            if normalized == normalized_phrase:
                self.last_intent = intent
                return intent, 1.0

        best_intent = None
        best_score = 0.0

        for intent, phrase, normalized_phrase in self.phrase_index:
            score = self.similarity(
                normalized,
                normalized_phrase
            )

            if score > best_score:
                best_score = score
                best_intent = intent

        words = normalized.split()

        if len(words) == 1:
            for intent, phrase, normalized_phrase in self.phrase_index:
                if normalized == normalized_phrase:
                    self.last_intent = intent
                    return intent, 1.0

            return "unknown", 0.0

        if best_intent is None:
            return "unknown", 0.0

        if best_score < 0.45:
            return "unknown", best_score

        self.last_intent = best_intent

        return best_intent, round(best_score, 3)

    def extract_parameters(self, text, intent=None):
        if text is None:
            return ""

        text = str(text).strip()

        if not text:
            return ""

        normalized = self.normalize(text)

        prefixes = [
            "youtube qidir",
            "youtube search",
            "youtube'dan qidir",
            "youtube dan qidir",
            "youtube ichidan qidir",
            "youtube och",
            "youtubeni och",
            "youtube ni och",
            "instagram och",
            "instagramni och",
            "instagram ni och",
            "hisobla",
            "hisoblab ber",
            "hisoblash",
            "matematikani hisobla",
            "matematik hisob"
        ]

        for prefix in prefixes:
            prefix_normalized = self.normalize(prefix)

            if normalized.startswith(prefix_normalized):
                return normalized[
                    len(prefix_normalized):
                ].strip()

        return text

    def get_intents(self):
        return list(self.intents.keys())

    def get_phrase_count(self):
        return len(self.phrase_index)

    def has_intent(self, intent):
        return str(intent) in self.intents

    def reload(self):
        return self.load()

    def info(self):
        return {
            "intents": len(self.intents),
            "phrases": len(self.phrase_index),
            "last_intent": self.last_intent,
            "brain_file": self.brain_file
        }


if __name__ == "__main__":
    brain = LanguageBrain()

    print("JARVIS LANGUAGE BRAIN")
    print("=" * 40)
    print("Intents:", len(brain.get_intents()))
    print("Phrases:", brain.get_phrase_count())

    tests = [
        "salom jarvis",
        "assalomu alaykum",
        "soat nechchi",
        "youtube och",
        "instagram och",
        "hisobla 25 + 17",
        "xayr",
        "noma'lum buyruq"
    ]

    for text in tests:
        intent, confidence = brain.predict(text)

        print()
        print("USER:", text)
        print("INTENT:", intent)
        print("CONFIDENCE:", confidence)