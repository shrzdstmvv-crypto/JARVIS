import traceback


class VoiceInput:

    REQUEST_CODE = 1001

    def __init__(self):

        self.result = None
        self.error = None
        self.listening = False

    # ======================================================
    # LISTEN
    # ======================================================

    def listen(self):

        self.result = None
        self.error = None
        self.listening = False

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            activity = PythonActivity.mActivity

            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "uz-UZ"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                "uz-UZ"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_PROMPT,
                "JARVIS sizni tinglamoqda..."
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_MAX_RESULTS,
                1
            )

            # Android Speech Recognizer
            activity.startActivityForResult(
                intent,
                self.REQUEST_CODE
            )

            self.listening = True

            print(
                "🎤 Android Speech Recognizer ishga tushdi."
            )

            return None

        except Exception as error:

            self.error = error
            self.listening = False

            print(
                "❌ VOICE INPUT ERROR:"
            )

            print(
                type(error).__name__,
                error
            )

            traceback.print_exc()

            return None

    # ======================================================
    # SET RESULT
    # ======================================================

    def set_result(
        self,
        text
    ):

        if text:

            self.result = str(
                text
            ).strip()

        self.listening = False

        print(
            "🎤 VOICE RESULT:",
            self.result
        )

    # ======================================================
    # SET ERROR
    # ======================================================

    def set_error(
        self,
        error
    ):

        self.error = error
        self.listening = False

        print(
            "❌ VOICE ERROR:",
            error
        )

    # ======================================================
    # GET RESULT
    # ======================================================

    def get_result(self):

        return self.result

    # ======================================================
    # GET ERROR
    # ======================================================

    def get_error(self):

        return self.error

    # ======================================================
    # IS LISTENING
    # ======================================================

    def is_listening(self):

        return self.listening

    # ======================================================
    # RESET
    # ======================================================

    def reset(self):

        self.result = None
        self.error = None
        self.listening = False


# ==========================================================
# TERMINAL TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 40)
    print("🎤 JARVIS VOICE INPUT")
    print("=" * 40)

    try:

        voice = VoiceInput()

        print(
            "VoiceInput yaratildi."
        )

        print(
            "Android APK ichida "
            "Speech Recognizer ishlaydi."
        )

    except Exception as error:

        print(
            "❌ ERROR:",
            error
        )