from voice_input import VoiceInput


class HearingPipeline:

    def __init__(self, callback=None):

        self.callback = callback

        self.voice = VoiceInput()

        self.active = False

    # ======================================================
    # START LISTENING
    # ======================================================

    def start(self):

        if self.active:
            return False

        self.active = True

        try:

            self.voice.reset()

            self.voice.listen()

            return True

        except Exception as error:

            self.active = False

            print(
                "❌ HEARING PIPELINE ERROR:",
                error
            )

            if self.callback:

                try:

                    self.callback(
                        None,
                        error
                    )

                except Exception:
                    pass

            return False

    # ======================================================
    # RESULT
    # ======================================================

    def result(self, text):

        self.active = False

        if not text:
            return None

        text = str(text).strip()

        if not text:
            return None

        print(
            "🎤 HEARING:",
            text
        )

        if self.callback:

            try:

                self.callback(
                    text,
                    None
                )

            except Exception as error:

                print(
                    "CALLBACK ERROR:",
                    error
                )

        return text

    # ======================================================
    # ERROR
    # ======================================================

    def error(self, error):

        self.active = False

        print(
            "❌ HEARING ERROR:",
            error
        )

        if self.callback:

            try:

                self.callback(
                    None,
                    error
                )

            except Exception:
                pass

    # ======================================================
    # STOP
    # ======================================================

    def stop(self):

        self.active = False

        try:

            self.voice.reset()

        except Exception:
            pass

    # ======================================================
    # STATUS
    # ======================================================

    def is_active(self):

        return self.active


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 40)
    print("🎤 JARVIS HEARING PIPELINE")
    print("=" * 40)

    pipeline = HearingPipeline()

    print(
        "✅ HearingPipeline yaratildi."
    )

    print(
        "📱 Haqiqiy Android ovozli ishlash "
        "APK bosqichida amalga oshadi."
    )