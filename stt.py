class SpeechToText:

    def __init__(self):

        self.last_text = None
        self.last_error = None

    # ======================================================
    # PROCESS RESULT
    # ======================================================

    def process(self, text):

        self.last_error = None

        if text is None:

            self.last_text = None

            return None

        text = str(
            text
        ).strip()

        if not text:

            self.last_text = None

            return None

        self.last_text = text

        print(
            "📝 STT:",
            text
        )

        return text

    # ======================================================
    # NORMALIZE
    # ======================================================

    def normalize(self, text):

        if text is None:
            return ""

        text = str(
            text
        ).strip()

        # Ortiqcha bo'shliqlar
        text = " ".join(
            text.split()
        )

        return text

    # ======================================================
    # RESULT
    # ======================================================

    def get_last_text(self):

        return self.last_text

    # ======================================================
    # ERROR
    # ======================================================

    def set_error(self, error):

        self.last_error = error

        print(
            "❌ STT ERROR:",
            error
        )

    def get_error(self):

        return self.last_error

    # ======================================================
    # CLEAR
    # ======================================================

    def clear(self):

        self.last_text = None
        self.last_error = None


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 40)
    print("📝 JARVIS SPEECH TO TEXT")
    print("=" * 40)

    stt = SpeechToText()

    test = stt.process(
        "salom jarvis"
    )

    print(
        "Natija:",
        test
    )

    print(
        "Normalize:",
        stt.normalize(test)
    )