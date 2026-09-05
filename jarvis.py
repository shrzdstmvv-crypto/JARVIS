import os
import subprocess
import webbrowser
from datetime import datetime

from language_brain import LanguageBrain
from memory import Memory


class JARVIS:

    def __init__(self):

        self.brain = LanguageBrain()
        self.memory = Memory()

        self.current_image = None
        self.image_name = None

        print("Language Brain yuklandi.")
        print("Memory yuklandi.")
        print("JARVIS 6.0 Core tayyor.")

    def process(self, text):

        if text is None:
            return "Buyruq bo‘sh."

        text = str(text).strip()

        if not text:
            return "Buyruq bo‘sh."

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

        try:

            intent, confidence = self.brain.predict(
                text
            )

            print(
                f"{text} -> "
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

        response = self.execute(
            intent,
            text,
            confidence
        )

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

    def process_image(
        self,
        image_path,
        image_name=None
    ):

        if not image_path:

            return (
                "Rasm yo‘li topilmadi."
            )

        image_path = str(
            image_path
        )

        if not os.path.exists(
            image_path
        ):

            return (
                "Rasm fayli topilmadi."
            )

        if image_name:

            image_name = str(
                image_name
            ).strip()

        else:

            image_name = os.path.basename(
                image_path
            )

        self.current_image = image_path
        self.image_name = image_name

        image_info = (
            "Rasm qabul qilindi: "
            + image_name
        )

        try:

            self.memory.add(
                "user",
                "[IMAGE] " + image_name
            )

        except Exception as error:

            print(
                "IMAGE MEMORY USER ERROR:",
                error
            )

        try:

            self.memory.add(
                "jarvis",
                image_info
            )

        except Exception as error:

            print(
                "IMAGE MEMORY JARVIS ERROR:",
                error
            )

        print(
            "IMAGE RECEIVED:",
            image_path
        )

        print(
            "IMAGE NAME:",
            image_name
        )

        return image_info

    def execute(
        self,
        intent,
        text,
        confidence
    ):

        if intent == "greeting":

            return "Salom! Men JARVIS."

        if intent == "time":

            now = datetime.now()

            return (
                f"Hozir soat "
                f"{now.strftime('%H:%M')}."
            )

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

        if intent == "calculator":

            return self.calculate(
                text
            )

        if intent == "goodbye":

            return "Xayr!"

        return (
            "Kechirasiz, bu buyruqni hali "
            "to‘liq tushunmadim."
        )

    def calculate(self, text):

        try:

            expression = str(
                text
            ).lower()

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

            if not expression:

                return (
                    "Hisoblash uchun "
                    "ifoda topilmadi."
                )

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

            result = eval(
                expression,
                {
                    "__builtins__": {}
                },
                {}
            )

            if isinstance(
                result,
                float
            ):

                if result.is_integer():

                    result = int(
                        result
                    )

            return f"Javob: {result}"

        except ZeroDivisionError:

            return (
                "Nolga bo‘lish mumkin emas."
            )

        except Exception as error:

            print(
                "CALCULATOR ERROR:",
                error
            )

            return (
                "Hisoblashda "
                "xatolik yuz berdi."
            )

    def open_url(self, url):

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

    def get_memory(self):

        try:

            return self.memory.history()

        except Exception as error:

            print(
                "GET MEMORY ERROR:",
                error
            )

            return []

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

    def get_current_image(self):

        return self.current_image

    def get_current_image_name(self):

        return self.image_name


def terminal_test():

    print()
    print("=" * 40)
    print("JARVIS 6.0")
    print("=" * 40)

    try:

        assistant = JARVIS()

    except Exception as error:

        print()
        print(
            "JARVIS CORE YUKLANMADI"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        return

    print()
    print(
        "JARVIS tayyor!"
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


if __name__ == "__main__":

    terminal_test()