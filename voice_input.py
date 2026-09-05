import traceback


class VoiceInput:

    REQUEST_CODE = 1001

    def __init__(self):

        self.result = None
        self.error = None
        self.listening = False
        self.activity = None

    # ======================================================
    # LISTEN
    # ======================================================

    def listen(self):

        # Har yangi bosishda eski natijani tozalaymiz
        self.result = None
        self.error = None

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

            self.activity = PythonActivity.mActivity

            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            # Uzbek
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

            # Natijani kutayotgan holat
            self.listening = True

            self.activity.startActivityForResult(
                intent,
                self.REQUEST_CODE
            )

            print(
                "🎤 Android Speech Recognizer ishga tushdi."
            )

            return True

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

            return False

    # ======================================================
    # ANDROID RESULT
    # ======================================================

    def handle_result(
        self,
        request_code,
        result_code,
        data
    ):

        try:

            if request_code != self.REQUEST_CODE:

                return False

            self.listening = False

            if data is None:

                self.set_error(
                    "Speech Recognizer natija qaytarmadi."
                )

                return False

            from jnius import autoclass

            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            results = data.getStringArrayListExtra(
                RecognizerIntent.EXTRA_RESULTS
            )

            if results is None:

                self.set_error(
                    "Ovoz aniqlanmadi."
                )

                return False

            if results.size() == 0:

                self.set_error(
                    "Ovoz aniqlanmadi."
                )

                return False

            text = str(
                results.get(0)
            ).strip()

            if not text:

                self.set_error(
                    "Bo‘sh ovoz natijasi."
                )

                return False

            self.set_result(
                text
            )

            return True

        except Exception as error:

            self.set_error(
                error
            )

            traceback.print_exc()

            return False

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