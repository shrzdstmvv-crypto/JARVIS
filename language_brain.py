import json
import os
import re
import math


class LanguageBrain:

    def __init__(self):

        print("========================================")
        print("🧠 JARVIS LANGUAGE BRAIN")
        print("========================================")

        self.model_file = os.path.join(
            os.path.dirname(__file__),
            "jarvis_brain.json"
        )

        self.brain = {}
        self.intents = []
        self.words = []

        self.load_model()

    # ======================================================
    # LOAD MODEL
    # ======================================================

    def load_model(self):

        try:

            with open(
                self.model_file,
                "r",
                encoding="utf-8"
            ) as file:

                self.brain = json.load(file)

            if not isinstance(self.brain, dict):

                raise ValueError(
                    "Model formati noto‘g‘ri."
                )

            self.intents = list(
                self.brain.keys()
            )

            # Lug‘atni avtomatik yaratish
            vocabulary = set()

            for phrases in self.brain.values():

                if not isinstance(phrases, list):
                    continue

                for phrase in phrases:

                    words = self.tokenize(
                        phrase
                    )

                    vocabulary.update(
                        words
                    )

            self.words = sorted(
                vocabulary
            )

            print(
                f"📚 Lug‘at: {len(self.words)} ta so‘z"
            )

            print(
                f"🎯 Intent: {len(self.intents)}"
            )

            print("💾 Model yuklandi")
            print("⚡ Training qilinmaydi")

        except Exception as error:

            print(
                "❌ Model yuklanmadi:",
                error
            )

            self.brain = {}
            self.intents = []
            self.words = []

    # ======================================================
    # TOKENIZER
    # ======================================================

    def tokenize(self, text):

        text = str(text).lower()

        return re.findall(
            r"[a-zA-ZÀ-ÿА-Яа-яʻ’'0-9]+",
            text
        )

    # ======================================================
    # NORMALIZE
    # ======================================================

    def normalize(self, text):

        text = str(text).lower().strip()

        text = text.replace(
            "’",
            "'"
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # ======================================================
    # SIMILARITY
    # ======================================================

    def similarity(
        self,
        user_text,
        phrase
    ):

        user_text = self.normalize(
            user_text
        )

        phrase = self.normalize(
            phrase
        )

        # To‘liq moslik
        if user_text == phrase:

            return 1.0

        user_words = set(
            self.tokenize(user_text)
        )

        phrase_words = set(
            self.tokenize(phrase)
        )

        if not user_words or not phrase_words:

            return 0.0

        # So‘zlar kesishmasi
        common = (
            user_words &
            phrase_words
        )

        if not common:

            return 0.0

        # Jaccard similarity
        union = (
            user_words |
            phrase_words
        )

        score = len(common) / len(union)

        # Foydalanuvchi so‘zlarining
        # phrase ichida qanchasi borligi
        coverage = (
            len(common) /
            len(user_words)
        )

        # Ikki ko‘rsatkichni birlashtirish
        final_score = (
            score * 0.4 +
            coverage * 0.6
        )

        return min(
            final_score,
            0.99
        )

    # ======================================================
    # PREDICT
    # ======================================================

    def predict(self, text):

        if not text:

            return (
                "unknown",
                0.0
            )

        if not self.brain:

            return (
                "unknown",
                0.0
            )

        text = str(text).strip()

        best_intent = "unknown"

        best_score = 0.0

        # Har bir intent
        for intent, phrases in self.brain.items():

            if not isinstance(
                phrases,
                list
            ):

                continue

            for phrase in phrases:

                score = self.similarity(
                    text,
                    phrase
                )

                if score > best_score:

                    best_score = score

                    best_intent = intent

        # Juda kuchli exact match
        normalized_text = self.normalize(
            text
        )

        for intent, phrases in self.brain.items():

            if not isinstance(
                phrases,
                list
            ):

                continue

            for phrase in phrases:

                if normalized_text == self.normalize(
                    phrase
                ):

                    return (
                        intent,
                        1.0
                    )

        # Threshold
        if best_score < 0.25:

            return (
                "unknown",
                best_score
            )

        return (
            best_intent,
            best_score
        )


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    brain = LanguageBrain()

    print()
    print("🧪 TEST")
    print()

    tests = [

        "salom",

        "soat nechchi",

        "youtube och",

        "instagramni och",

        "xayr",

        "2 + 2",

        "hisobla"
    ]

    for text in tests:

        intent, confidence = brain.predict(
            text
        )

        print(
            f"{text} → "
            f"{intent} | "
            f"{confidence:.4f}"
        )