from stt import SpeechToText


class Hearing:

    def __init__(self, callback=None):

        self.callback = callback

        self.stt = SpeechToText()

        self.listening = False

        self.last_text = None
        self.last_error = None

    # ======================================================
    # START
    # ======================================================

    def start(self):

        if self.listening:

            return False

        self.listening = True

        self.last_text = None
        self.last_error = None

        print(
            "🎤 Hearing started."
        )

        return True

    # ======================================================
    # RECEIVE
    # ======================================================

    def receive(self, text):

        if not text:

            return None

        try:

            text = self.stt.normalize(
                text
            )

            if not text:

                return None

            text = self.stt.process(
                text
            )

            self.last_text = text

            self.listening = False

            print(
                "👂 Heard:",
                text
            )

            if self.callback:

                try:

                    self.callback(
                        text
                    )

                except Exception as error:

                    print(
                        "❌ HEARING CALLBACK ERROR:",
                        error
                    )

            return text

        except Exception as error:

            self.set_error(
                error
            )

            return None

    # ======================================================
    # ERROR
    # ======================================================

    def set_error(self, error):

        self.last_error = error

        self.listening = False

        self.stt.set_error(
            error
        )

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

        self.listening = False

        print(
            "🎤 Hearing stopped."
        )

    # ======================================================
    # STATUS
    # ======================================================

    def is_listening(self):

        return self.listening

    # ======================================================
    # LAST TEXT
    # ======================================================

    def get_last_text(self):

        return self.last_text

    # ======================================================
    # LAST ERROR
    # ======================================================

    def get_last_error(self):

        return self.last_error

    # ======================================================
    # RESET
    # ======================================================

    def reset(self):

        self.listening = False

        self.last_text = None

        self.last_error = None

        self.stt.clear()


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 40)
    print("👂 JARVIS HEARING")
    print("=" * 40)

    def callback(text, error=None):

        if error:

            print(
                "Callback error:",
                error
            )

        elif text:

            print(
                "Callback text:",
                text
            )

    hearing = Hearing(
        callback=callback
    )

    print(
        "✅ Hearing yaratildi."
    )

    hearing.start()

    hearing.receive(
        "salom jarvis"
    )