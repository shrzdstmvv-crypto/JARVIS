import json
import os


class LanguageBrain:

    def __init__(self):

        self.model_file = os.path.join(
            os.path.dirname(__file__),
            "jarvis_brain.json"
        )

        self.words = []
        self.intents = []

        self.model = {}

        self.load_model()

    # ======================================================
    # LOAD MODEL
    # ======================================================

    def load_model(self):

        if not os.path.exists(
            self.model_file
        ):

            raise FileNotFoundError(
                "jarvis_brain.json topilmadi."
            )

        try:

            with open(
                self.model_file,
                "r",
                encoding="utf-8"
            ) as file:

                self.model = json.load(file)

        except Exception as error:

            raise RuntimeError(
                f"Brain modelini yuklashda xatolik: "
                f"{error}"
            )

        # --------------------------------------------------
        # WORDS
        # --------------------------------------------------

        self.words = self.model.get(
            "words",
            []
        )

        # --------------------------------------------------
        # INTENTS
        # --------------------------------------------------

        self.intents = self.model.get(
            "intents",
            []
        )

        print(
            f"📚 Lug‘at: {len(self.words)} ta so‘z"
        )

        print(
            f"🎯 Intent: {len(self.intents)}"
        )

        print(
            "💾 Model yuklandi"
        )

        print(
            "⚡ Training qilinmaydi"
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

        text = str(
            text
        ).strip().lower()

        if not text:

            return (
                "unknown",
                0.0
            )

        # --------------------------------------------------
        # INTENTLARNI TEKSHIRISH
        # --------------------------------------------------

        best_intent = "unknown"
        best_score = 0.0

        for intent_data in self.intents:

            intent_name = intent_data.get(
                "intent",
                intent_data.get(
                    "tag",
                    ""
                )
            )

            patterns = intent_data.get(
                "patterns",
                []
            )

            for pattern in patterns:

                pattern = str(
                    pattern
                ).strip().lower()

                if not pattern:
                    continue

                # To‘liq moslik
                if text == pattern:

                    return (
                        intent_name,
                        0.999
                    )

                # So‘zlar bo‘yicha moslik
                text_words = set(
                    text.split()
                )

                pattern_words = set(
                    pattern.split()
                )

                if not pattern_words:
                    continue

                common = (
                    text_words
                    & pattern_words
                )

                score = (
                    len(common)
                    /
                    len(pattern_words)
                )

                if score > best_score:

                    best_score = score

                    best_intent = (
                        intent_name
                    )

        # --------------------------------------------------
        # MINIMUM CONFIDENCE
        # --------------------------------------------------

        if best_score < 0.25:

            return (
                "unknown",
                best_score
            )

        return (
            best_intent,
            min(
                best_score,
                0.999
            )
        )

    # ======================================================
    # GET WORDS
    # ======================================================

    def get_words(self):

        return list(
            self.words
        )

    # ======================================================
    # GET INTENTS
    # ======================================================

    def get_intents(self):

        return list(
            self.intents
        )

    # ======================================================
    # MODEL INFO
    # ======================================================

    def info(self):

        return {

            "words":
                len(self.words),

            "intents":
                len(self.intents),

            "model":
                self.model_file,

            "training":
                False
        }


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 40)
    print("🧠 JARVIS LANGUAGE BRAIN")
    print("=" * 40)

    try:

        brain = LanguageBrain()

        tests = [
            "salom",
            "soat nechchi",
            "youtube och",
            "instagramni och",
            "xayr"
        ]

        print()
        print("🧪 TEST")
        print()

        for text in tests:

            intent, confidence = (
                brain.predict(text)
            )

            print(
                f"{text} → "
                f"{intent} | "
                f"{confidence:.4f}"
            )

    except Exception as error:

        print()
        print(
            "❌ BRAIN ERROR:"
        )

        print(
            type(error).__name__,
            error
        )