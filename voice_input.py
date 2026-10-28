
class VoiceInput:
    REQUEST_CODE = 1001

    def __init__(self):
        self.result = None
        self.error = None
        self.listening = False
        self.activity = None

    def _intent(self, full=True):
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        RecognizerIntent = autoclass("android.speech.RecognizerIntent")

        intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        intent.putExtra(
            RecognizerIntent.EXTRA_LANGUAGE_MODEL,
            RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
        )

        if not full:
            return intent

        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "uz-UZ")
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "uz-UZ")
        intent.putExtra(
            RecognizerIntent.EXTRA_PROMPT, "JARVIS sizni tinglamoqda..."
        )
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)

        # Internetsiz tanish faqat sozlamada yoqilgan bo'lsa so'raladi.
        # Odatiy holatda o'chiq: til paketi yo'q telefonlarda xato bermasligi uchun.
        try:
            import selfupdate
            prefer_offline = selfupdate.get_setting("offline_mic", False)
        except Exception:
            prefer_offline = False

        if prefer_offline:
            intent.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, True)

        return intent

    def listen(self):
        self.reset()

        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            self.activity = PythonActivity.mActivity
        except Exception as error:
            self.set_error("Android muhiti topilmadi: " + repr(error)[:100])
            return False

        # Telefonda ovozni tanish xizmati bormi?
        try:
            probe = self._intent(full=False)
            if probe.resolveActivity(self.activity.getPackageManager()) is None:
                self.set_error(
                    "Telefonda ovozni tanish xizmati topilmadi. "
                    "Google ilovasini (Google ovoz kiritish) o'rnating yoki yoqing."
                )
                return False
        except Exception as error:
            print("VOICE PROBE ERROR:", error)

        last_error = None

        # 1) to'liq so'rov, 2) faqat eng sodda so'rov (til ko'rsatmasiz)
        for full in (True, False):
            try:
                intent = self._intent(full=full)
                self.listening = True
                self.activity.startActivityForResult(intent, self.REQUEST_CODE)
                return True
            except Exception as error:
                last_error = error
                self.listening = False
                print("VOICE START ERROR (full=%s): %s" % (full, error))

        self.set_error("Mikrofonni ochib bo'lmadi: " + repr(last_error)[:140])
        return False

    def handle_result(self, request_code, result_code, data):
        try:
            from jnius import autoclass

            if request_code != self.REQUEST_CODE:
                return False

            self.listening = False

            Activity = autoclass("android.app.Activity")

            if result_code != Activity.RESULT_OK:
                self.set_error(self.describe_code(result_code))
                return False

            if data is None:
                self.set_error("Ovoz natijasi olinmadi.")
                return False

            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            results = data.getStringArrayListExtra(
                RecognizerIntent.EXTRA_RESULTS
            )

            if results is None or results.size() == 0:
                self.set_error("Ovoz aniqlanmadi. Qayta urinib ko‘ring.")
                return False

            recognized_text = str(results.get(0)).strip()

            if not recognized_text:
                self.set_error("Bo‘sh ovoz natijasi.")
                return False

            self.set_result(recognized_text)
            return True

        except Exception as error:
            self.set_error(error)
            return False

    @staticmethod
    def describe_code(code):
        first = 1  # Activity.RESULT_FIRST_USER
        known = {
            first + 1: "Mikrofon xatosi. Mikrofon ruxsatini tekshiring.",
            first + 2: "Ovoz tanish xizmati xatosi. Google ilovasini yangilang.",
            first + 3: ("Internet xatosi. Sozlamalarda «Internetsiz mikrofon» ni "
                        "o'chiring yoki internetni tekshiring."),
            first + 4: "Hech narsa eshitilmadi. Qayta urinib ko'ring.",
            first + 5: "Ovoz serveri xatosi. Birozdan keyin qayta urinib ko'ring.",
        }
        if code == 0:
            return "Ovozli buyruq bekor qilindi."
        return known.get(code, "Ovozni tanib bo'lmadi (kod " + str(code) + ").")

    def set_result(self, text):
        text = "" if text is None else str(text).strip()
        self.result = text if text else None
        self.error = None
        self.listening = False

    def set_error(self, error):
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
            autoclass("android.speech.RecognizerIntent")
            return True
        except Exception:
            return False


if __name__ == "__main__":
    voice = VoiceInput()

    print("JARVIS VOICE INPUT")
    print("=" * 40)
    print("Available:", voice.available())
    print("Listening:", voice.is_listening())
