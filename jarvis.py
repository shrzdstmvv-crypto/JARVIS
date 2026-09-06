import ast
import math
import os
import re
import subprocess
import webbrowser
from datetime import datetime

from language_brain import LanguageBrain
from memory import Memory


class JARVIS:

    def __init__(self):
        self.brain = LanguageBrain()
        self.memory = Memory()

        self.running = True
        self.current_image = None

        self.responses = {
            "greeting": [
                "Salom! Men JARVIS. Sizga qanday yordam bera olaman?",
                "Salom! Qanday yordam beray?",
                "Assalomu alaykum! JARVIS tayyor."
            ],
            "goodbye": [
                "Xayr! Yana kerak bo'lsam, shu yerdaman.",
                "Xayr! Kun yaxshi o'tsin.",
                "Ko'rishguncha!"
            ]
        }

    def process(self, text):
        text = str(text).strip()

        if not text:
            return "Buyruqni tushunmadim."

        if not self.running:
            self.running = True

        try:
            intent, confidence = self.brain.predict(text)
        except Exception:
            intent = "unknown"
            confidence = 0.0

        local_intent = self.detect_local_command(text)

        if local_intent:
            intent = local_intent

        try:
            response = self.execute(intent, text)
        except Exception as error:
            response = "Buyruqni bajarishda xatolik yuz berdi."

        if response is None:
            response = ""

        response = str(response)

        self._memory_add("user", text)
        self._memory_add("assistant", response)

        return response

    def detect_local_command(self, text):
        normalized = self._normalize(text)

        if not normalized:
            return None

        if self._is_goodbye(normalized):
            return "goodbye"

        if self._is_greeting(normalized):
            return "greeting"

        if self._is_youtube_search(normalized):
            return "youtube_search"

        if self._is_youtube(normalized):
            return "youtube"

        if self._is_instagram(normalized):
            return "instagram"

        if self._is_help(normalized):
            return "help"

        if self._is_clear_memory(normalized):
            return "clear_memory"

        if self._is_memory_info(normalized):
            return "memory_info"

        if self._is_date(normalized):
            return "date"

        if self._is_time(normalized):
            return "time"

        if self._is_calculator(normalized):
            return "calculator"

        return None

    def execute(self, intent, text):
        if intent == "greeting":
            return self._random_response("greeting")

        if intent == "goodbye":
            self.running = False
            return self._random_response("goodbye")

        if intent == "time":
            return self.get_time()

        if intent == "date":
            return self.get_date()

        if intent == "youtube":
            return self.open_youtube()

        if intent == "youtube_search":
            query = self.extract_youtube_query(text)

            if not query:
                return self.open_youtube()

            return self.search_youtube(query)

        if intent == "instagram":
            return self.open_instagram()

        if intent == "calculator":
            expression = self.extract_calculation(text)

            if not expression:
                return "Hisoblash uchun misol yozing."

            return self.calculate(expression)

        if intent == "help":
            return self.help()

        if intent == "memory_info":
            return self.memory_info()

        if intent == "clear_memory":
            return self.clear_memory()

        return self.unknown()

    def get_time(self):
        now = datetime.now()

        return (
            "Hozir soat "
            + now.strftime("%H:%M")
            + "."
        )

    def get_date(self):
        now = datetime.now()

        months = {
            1: "yanvar",
            2: "fevral",
            3: "mart",
            4: "aprel",
            5: "may",
            6: "iyun",
            7: "iyul",
            8: "avgust",
            9: "sentabr",
            10: "oktabr",
            11: "noyabr",
            12: "dekabr"
        }

        return (
            "Bugun "
            + str(now.day)
            + " "
            + months.get(now.month, "")
            + " "
            + str(now.year)
            + "-yil."
        )

    def open_youtube(self):
        url = "https://www.youtube.com"

        if self.open_url(url):
            return "YouTube ochildi."

        return "YouTube'ni ochib bo'lmadi."

    def search_youtube(self, query):
        query = str(query).strip()

        if not query:
            return self.open_youtube()

        url = (
            "https://www.youtube.com/results?search_query="
            + webbrowser.quote(query)
            if hasattr(webbrowser, "quote")
            else "https://www.youtube.com/results?search_query="
            + self.url_encode(query)
        )

        if self.open_url(url):
            return "YouTube'da qidirilmoqda."

        return "YouTube qidiruvini ochib bo'lmadi."

    def open_instagram(self):
        app_url = "instagram://app"
        web_url = "https://www.instagram.com"

        try:
            result = subprocess.run(
                [
                    "am",
                    "start",
                    "-a",
                    "android.intent.action.VIEW",
                    "-d",
                    app_url
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if result.returncode == 0:
                return "Instagram ochildi."

        except Exception:
            pass

        if self.open_url(web_url):
            return "Instagram ochildi."

        return "Instagram'ni ochib bo'lmadi."

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

        except Exception:
            pass

        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False

    def calculate(self, expression):
        expression = self.clean_expression(expression)

        if not expression:
            return "Hisoblash uchun to'g'ri misol kerak."

        try:
            tree = ast.parse(
                expression,
                mode="eval"
            )

            result = self.safe_eval(tree.body)

            if isinstance(result, float):
                if math.isfinite(result):
                    if result.is_integer():
                        result = int(result)
                else:
                    return "Natija aniqlanmadi."

            return "Javob: " + str(result)

        except ZeroDivisionError:
            return "Nolga bo'lish mumkin emas."

        except Exception:
            return "Bu matematik ifodani hisoblay olmadim."

    def clean_expression(self, expression):
        expression = str(expression).strip()

        expression = expression.replace(",", ".")
        expression = expression.replace("×", "*")
        expression = expression.replace("÷", "/")
        expression = expression.replace("−", "-")

        expression = re.sub(
            r"\bkvadrat ildiz\b",
            "sqrt",
            expression,
            flags=re.IGNORECASE
        )

        expression = re.sub(
            r"\bildiz\b",
            "sqrt",
            expression,
            flags=re.IGNORECASE
        )

        expression = re.sub(
            r"\bkvadrat\b",
            "**2",
            expression,
            flags=re.IGNORECASE
        )

        expression = re.sub(
            r"\bkub\b",
            "**3",
            expression,
            flags=re.IGNORECASE
        )

        expression = re.sub(
            r"[^0-9a-zA-Z_+\-*/().,% ]",
            "",
            expression
        )

        return expression.strip()

    def safe_eval(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value

            raise ValueError()

        if isinstance(node, ast.Num):
            return node.n

        if isinstance(node, ast.BinOp):
            left = self.safe_eval(node.left)
            right = self.safe_eval(node.right)

            operations = {
                ast.Add: lambda: left + right,
                ast.Sub: lambda: left - right,
                ast.Mult: lambda: left * right,
                ast.Div: lambda: left / right,
                ast.FloorDiv: lambda: left // right,
                ast.Mod: lambda: left % right,
                ast.Pow: lambda: left ** right
            }

            operation = operations.get(type(node.op))

            if operation is None:
                raise ValueError()

            result = operation()

            if isinstance(result, (int, float)):
                if abs(result) > 10**100:
                    raise ValueError()

            return result

        if isinstance(node, ast.UnaryOp):
            value = self.safe_eval(node.operand)

            if isinstance(node.op, ast.UAdd):
                return +value

            if isinstance(node.op, ast.USub):
                return -value

            raise ValueError()

        if isinstance(node, ast.Name):
            constants = {
                "pi": math.pi,
                "e": math.e
            }

            if node.id in constants:
                return constants[node.id]

            raise ValueError()

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError()

            name = node.func.id

            functions = {
                "sqrt": math.sqrt,
                "abs": abs,
                "sin": lambda x: math.sin(math.radians(x)),
                "cos": lambda x: math.cos(math.radians(x)),
                "tan": lambda x: math.tan(math.radians(x)),
                "log": math.log10,
                "log10": math.log10,
                "ln": math.log,
                "exp": math.exp,
                "factorial": self.safe_factorial,
                "comb": math.comb,
                "perm": math.perm
            }

            function = functions.get(name)

            if function is None:
                raise ValueError()

            args = [
                self.safe_eval(argument)
                for argument in node.args
            ]

            return function(*args)

        raise ValueError()

    def safe_factorial(self, value):
        value = int(value)

        if value < 0 or value > 100:
            raise ValueError()

        return math.factorial(value)

    def extract_calculation(self, text):
        text = str(text).strip()

        prefixes = [
            "matematikani hisobla",
            "matematik hisob",
            "hisoblab ber",
            "hisoblash",
            "hisobla",
            "hisob-kitob qil",
            "matematikani yech",
            "misolni yech"
        ]

        normalized = self._normalize(text)

        for prefix in prefixes:
            prefix_normalized = self._normalize(prefix)

            if normalized.startswith(prefix_normalized):
                return normalized[
                    len(prefix_normalized):
                ].strip()

        return text

    def extract_youtube_query(self, text):
        text = str(text).strip()

        prefixes = [
            "youtube'dan qidir",
            "youtubedan qidir",
            "youtube dan qidir",
            "youtube ichidan qidir",
            "youtube qidir",
            "youtube search",
            "youtubeda qidir"
        ]

        normalized = self._normalize(text)

        for prefix in prefixes:
            prefix_normalized = self._normalize(prefix)

            if normalized.startswith(prefix_normalized):
                return normalized[
                    len(prefix_normalized):
                ].strip()

        return ""

    def help(self):
        return (
            "Men quyidagilarni bajara olaman:\n"
            "• Vaqtni aytish\n"
            "• Sanani aytish\n"
            "• YouTube ochish\n"
            "• YouTube'dan qidirish\n"
            "• Instagram ochish\n"
            "• Matematik hisoblash\n"
            "• Xotira haqida ma'lumot berish\n"
            "• Salomlashish"
        )

    def memory_info(self):
        info = self.memory.info()

        return (
            "Memory: "
            + str(info.get("total", 0))
            + " ta yozuv saqlangan."
        )

    def clear_memory(self):
        self.memory.clear()
        return "Memory tozalandi."

    def process_image(self, path):
        if not path:
            return False

        path = str(path)

        if not os.path.exists(path):
            return False

        self.current_image = path

        self._memory_add(
            "system",
            "Rasm qabul qilindi: " + os.path.basename(path)
        )

        return True

    def unknown(self):
        return "Kechirasiz, bu buyruqni hali to'liq tushunmadim."

    def _memory_add(self, role, message):
        try:
            self.memory.add(role, message)
        except TypeError:
            try:
                self.memory.add(message)
            except Exception:
                pass
        except Exception:
            pass

    def _normalize(self, text):
        text = str(text).lower().strip()

        replacements = {
            "ʻ": "'",
            "ʼ": "'",
            "’": "'",
            "‘": "'",
            "`": "'",
            "´": "'"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    def _is_greeting(self, text):
        greetings = [
            "salom",
            "salom jarvis",
            "assalomu alaykum",
            "assalomu alaykum jarvis",
            "hello",
            "hi",
            "hey jarvis",
            "qalaysan",
            "yaxshimisan"
        ]

        return text in greetings

    def _is_goodbye(self, text):
        goodbyes = [
            "xayr",
            "hayr",
            "bye",
            "goodbye",
            "ko'rishguncha",
            "ko'rishamiz",
            "jarvis xayr"
        ]

        return text in goodbyes

    def _is_youtube_search(self, text):
        prefixes = [
            "youtube qidir",
            "youtubedan qidir",
            "youtube dan qidir",
            "youtube ichidan qidir",
            "youtube'dan qidir",
            "youtube search",
            "youtubeda qidir"
        ]

        return any(
            text.startswith(prefix)
            for prefix in prefixes
        )

    def _is_youtube(self, text):
        commands = [
            "youtube",
            "youtube och",
            "youtubeni och",
            "youtube ni och",
            "youtube ishga tushir",
            "youtubeni ishga tushir",
            "youtube dasturini och"
        ]

        return text in commands

    def _is_instagram(self, text):
        commands = [
            "instagram",
            "instagram och",
            "instagramni och",
            "instagram ni och",
            "instagram ishga tushir",
            "instagramni ishga tushir",
            "instagram dasturini och"
        ]

        return text in commands

    def _is_help(self, text):
        commands = [
            "yordam",
            "yordam ber",
            "nimalar qila olasan",
            "nima qila olasan",
            "buyruqlar",
            "buyruqlarni ko'rsat",
            "yordam menyusi",
            "help"
        ]

        return text in commands

    def _is_clear_memory(self, text):
        commands = [
            "xotirani tozalash",
            "xotirani o'chir",
            "memoryni tozalash",
            "memoryni o'chir",
            "barcha xotirani o'chir",
            "hamma xotirani o'chir"
        ]

        return text in commands

    def _is_memory_info(self, text):
        commands = [
            "xotirani ko'rsat",
            "memoryni ko'rsat",
            "memory",
            "xotira",
            "nimalarni eslaysan",
            "qancha narsani eslaysan",
            "xotira haqida"
        ]

        return text in commands

    def _is_date(self, text):
        commands = [
            "bugun sana nima",
            "bugungi sana",
            "sana nima",
            "bugun nechanchi",
            "bugun qaysi sana",
            "sanani ayt",
            "bugungi sanani ayt"
        ]

        return text in commands

    def _is_time(self, text):
        commands = [
            "soat nechchi",
            "soat nechi",
            "hozir soat nechchi",
            "hozir soat nechi",
            "vaqtni ayt",
            "vaqtni ko'rsat",
            "hozirgi vaqt",
            "vaqt"
        ]

        return text in commands

    def _is_calculator(self, text):
        if text.startswith("hisobla"):
            return True

        if text.startswith("hisoblab ber"):
            return True

        if text.startswith("hisoblash"):
            return True

        if text.startswith("matematikani hisobla"):
            return True

        if text.startswith("matematik hisob"):
            return True

        if text.startswith("misolni yech"):
            return True

        if text.startswith("matematikani yech"):
            return True

        return bool(
            re.search(
                r"\d\s*[\+\-\*\/%]\s*\d",
                text
            )
        )

    def _random_response(self, intent):
        responses = self.responses.get(intent, [])

        if not responses:
            return ""

        return responses[
            datetime.now().microsecond % len(responses)
        ]

    def url_encode(self, text):
        from urllib.parse import quote

        return quote(
            str(text),
            safe=""
        )


if __name__ == "__main__":
    jarvis = JARVIS()

    print("JARVIS 6.0")
    print("=" * 40)

    while jarvis.running:
        try:
            user_input = input("USER: ").strip()

            if not user_input:
                continue

            response = jarvis.process(user_input)

            print("JARVIS:", response)

        except KeyboardInterrupt:
            print("\nJARVIS yopildi.")
            break

        except Exception as error:
            print("Xatolik:", error)