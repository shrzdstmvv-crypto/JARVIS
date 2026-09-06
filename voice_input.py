import traceback


class VoiceInput:

    REQUEST_CODE = 1001

    def __init__(self):
        self.result = None
        self.error = None
        self.listening = False
        self.activity = None

    def listen(self):
        self.reset()

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

            self.listening = True

            self.activity.startActivityForResult(
                intent,
                self.REQUEST_CODE
            )

            return True

        except Exception as error:
            self.set_error(error)
            return False

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

            Activity = autoclass(
                "android.app.Activity"
            )

            if result_code != Activity.RESULT_OK:
                self.set_error(
                    "Ovozli buyruq bekor qilindi."
                )
                return False

            if data is None:
                self.set_error(
                    "Ovoz natijasi olinmadi."
                )
                return False

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
                    "Bo'sh ovoz natijasi."
                )
                return False

            self.set_result(text)

            return True

        except Exception as error:
            self.set_error(error)
            traceback.print_exc()
            return False

    def set_result(self, text):
        if text is None:
            self.result = None
        else:
            text = str(text).strip()

            self.result = text if text else None

        self.error = None
        self.listening = False

    def set_error(self, error):
        if isinstance(error, Exception):
            self.error = str(error)
        else:
            self.error = str(error)

        self.result = None
        self.listening = False

    def get_result(self):
        return self.result

    def get_error(self):
        return self.error

    def is_listening(self):
        return self.listening

    def reset(self):
        self.result = None
        self.error = None
        self.listening = False

    def cancel(self):
        self.listening = False

    def available(self):
        try:
            from jnius import autoclass

            autoclass(
                "android.speech.RecognizerIntent"
            )

            return True

        except Exception:
            return False


if __name__ == "__main__":
    voice = VoiceInput()

    print("JARVIS VOICE INPUT")
    print("=" * 40)
    print("Available:", voice.available())
    print("Listening:", voice.is_listening())