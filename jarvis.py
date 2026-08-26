import subprocess
import webbrowser
from datetime import datetime

from language_brain import LanguageBrain
from memory import Memory


class JARVIS:

    def __init__(self):

        self.brain = LanguageBrain()
        self.memory = Memory()

        print("🧠 Language Brain yuklandi.")
        print("💾 Memory yuklandi.")
        print("🤖 JARVIS 6.0 Core tayyor.")

    # ======================================================
    # PROCESS
    # ======================================================

    def process(self, text):

        if text is None:
            return "Buyruq bo‘sh."

        text = str(text).strip()

        if not text:
            return "Buyruq bo‘sh."

        # --------------------------------------------------
        # MEMORY — USER
        # --------------------------------------------------

        try:

            self.memory.add(
                "user",
                text
            )

        except Exception as error:

            print(
                "MEMORY USER ERROR:",
                error
            )

        # --------------------------------------------------
        # LANGUAGE BRAIN
        # --------------------------------------------------

        try:

            intent, confidence = self.brain.predict(
                text
            )

            print(
                f"🧠 {text} → "
                f"{intent} | "
                f"{confidence}"
            )

        except Exception as error:

            print(
                "BRAIN ERROR:",
                error
            )

            return (
                "JARVIS Brain ishlashida "
                "xatolik yuz berdi."
            )

        # --------------------------------------------------
        # ACTION
        # --------------------------------------------------

        response = self.execute(
            intent,
            text,
            confidence
        )

        # --------------------------------------------------
        # MEMORY — JARVIS
        # --------------------------------------------------

        try:

            self.memory.add(
                "jarvis",
                response
            )

        except Exception as error:

            print(
                "MEMORY JARVIS ERROR:",
                error
            )

        return response

    # ======================================================
    # ACTION ENGINE
    # ======================================================

    def execute(
        self,
        intent,
        text,
        confidence
    ):

        # --------------------------------------------------
        # GREETING
        # --------------------------------------------------

        if intent == "greeting":

            return "Salom! Men JARVIS."

        # --------------------------------------------------
        # TIME
        # --------------------------------------------------

        if intent == "time":

            now = datetime.now()

            return (
                f"Hozir soat "
                f"{now.strftime('%H:%M')}."
            )

        # --------------------------------------------------
        # YOUTUBE
        # --------------------------------------------------

        if intent == "youtube":

            success = self.open_url(
                "https://www.youtube.com"
            )

            if success:

                return "YouTube ochilmoqda."

            return (
                "YouTube'ni ochishda "
                "xatolik yuz berdi."
            )

        # --------------------------------------------------
        # INSTAGRAM
        # --------------------------------------------------

        if intent == "instagram":

            success = self.open_url(
                "https://www.instagram.com"
            )

            if success:

                return "Instagram ochilmoqda."

            return (
                "Instagram'ni ochishda "
                "xatolik yuz berdi."
            )

        # --------------------------------------------------
        # CALCULATOR
        # --------------------------------------------------

        if intent == "calculator":

            return self.calculate(
                text
            )

        # --------------------------------------------------
        # GOODBYE
        # --------------------------------------------------

        if intent == "goodbye":

            return "Xayr!"

        # --------------------------------------------------
        # UNKNOWN
        # --------------------------------------------------

        return (
            "Kechirasiz, bu buyruqni hali "
            "to‘liq tushunmadim."
        )

    # ======================================================
    # CALCULATOR
    # ======================================================

    def calculate(self, text):

        try:

            expression = str(
                text
            ).lower()

            # ------------------------------------------------
            # KERAKSIZ SO'ZLAR
            # ------------------------------------------------

            words_to_remove = [

                "hisobla",
                "hisoblab ber",
                "hisoblash",

                "javobini top",
                "javobini chiqar",

                "natijani top",
                "natijani chiqar",

                "necha bo'ladi",
                "necha boladi",

                "qancha bo'ladi",
                "qancha boladi",

                "qancha",
                "necha"
            ]

            for word in words_to_remove:

                expression = expression.replace(
                    word,
                    ""
                )

            expression = expression.strip()

            # ------------------------------------------------
            # BO'SH IFODA
            # ------------------------------------------------

            if not expression:

                return (
                    "Hisoblash uchun "
                    "ifoda topilmadi."
                )

            # ------------------------------------------------
            # XAVFSIZ BELGILAR
            # ------------------------------------------------

            allowed = (
                "0123456789"
                "+-*/(). "
            )

            for character in expression:

                if character not in allowed:

                    return (
                        "Faqat oddiy matematik "
                        "ifodalarni hisoblay olaman."
                    )

            # ------------------------------------------------
            # HISOBLASH
            # ------------------------------------------------

            result = eval(
                expression,
                {
                    "__builtins__": {}
                },
                {}
            )

            # ------------------------------------------------
            # FLOAT → INTEGER
            # ------------------------------------------------

            if isinstance(
                result,
                float
            ):

                if result.is_integer():

                    result = int(
                        result
                    )

            return f"Javob: {result}"

        # ----------------------------------------------------
        # ZERO DIVISION
        # ----------------------------------------------------

        except ZeroDivisionError:

            return "Nolga bo‘lish mumkin emas."

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        except Exception as error:

            print(
                "CALCULATOR ERROR:",
                error
            )

            return (
                "Hisoblashda "
                "xatolik yuz berdi."
            )

    # ======================================================
    # OPEN URL
    # ======================================================

    def open_url(self, url):

        # --------------------------------------------------
        # ANDROID
        # --------------------------------------------------

        try:

            result = subprocess.run(
                [
                    "am",
                    "start",
                    "-a",
                    "android.intent.action.VIEW",
                    "-d",
                    url
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if result.returncode == 0:

                return True

        except Exception as error:

            print(
                "ANDROID URL ERROR:",
                error
            )

        # --------------------------------------------------
        # FALLBACK
        # --------------------------------------------------

        try:

            opened = webbrowser.open(
                url
            )

            return bool(
                opened
            )

        except Exception as error:

            print(
                "WEB URL ERROR:",
                error
            )

            return False

    # ======================================================
    # MEMORY
    # ======================================================

    def get_memory(self):

        try:

            return self.memory.history()

        except Exception as error:

            print(
                "GET MEMORY ERROR:",
                error
            )

            return []

    # ======================================================
    # CLEAR MEMORY
    # ======================================================

    def clear_memory(self):

        try:

            self.memory.clear()

            return "Xotira tozalandi."

        except Exception as error:

            print(
                "CLEAR MEMORY ERROR:",
                error
            )

            return (
                "Xotirani tozalashda "
                "xatolik yuz berdi."
            )


# ==========================================================
# TERMINAL TEST
# ==========================================================

def terminal_test():

    print()
    print("=" * 40)
    print("🤖 JARVIS 6.0")
    print("=" * 40)

    try:

        assistant = JARVIS()

    except Exception as error:

        print()
        print(
            "❌ JARVIS CORE YUKLANMADI"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        return

    print()
    print(
        "🚀 JARVIS tayyor!"
    )

    print(
        "Chiqish uchun: xayr"
    )

    print()

    while True:

        try:

            user_text = input(
                "Siz: "
            ).strip()

        except KeyboardInterrupt:

            print()
            break

        except EOFError:

            print()
            break

        if not user_text:

            continue

        response = assistant.process(
            user_text
        )

        print(
            "JARVIS:",
            response
        )

        if user_text.lower() in [
            "xayr",
            "hayr",
            "bye",
            "goodbye"
        ]:

            break


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    terminal_test()