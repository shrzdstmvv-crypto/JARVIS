
import ast
import math
import os
import re
import subprocess
import webbrowser
from datetime import datetime
from urllib.parse import quote

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

    # ASOSIY ISH JARAYONI
    def process(self, text):
        text = str(text).strip()
        if not text:
            return "Buyruqni tushunmadim."

        self.running = True
        normalized = self._normalize(text)

        # Buyruqni aniqlash
        intent = self.detect_local_command(normalized)

        if not intent:
            try:
                intent, confidence = self.brain.predict(text)
            except Exception:
                intent = "unknown"

        # Buyruqni bajarish
        try:
            response = self.execute(intent, text)
        except Exception as error:
            response = "Buyruqni bajarishda xatolik yuz berdi."
            print("JARVIS ERROR:", error)

        if response is None:
            response = ""

        response = str(response)

        # Xabarlarni xotiraga yozish
        self._memory_add("user", text)
        self._memory_add("assistant", response)

        return response

    # BUYRUQLARNI ANIQLASH
    def detect_local_command(self, text):
        if not text:
            return None

        if self._is_remember_request(text):
            return "remember"

        if self._is_recall_name(text):
            return "recall_name"

        if self._is_recall_memory(text):
            return "recall_memory"

        if self._is_goodbye(text):
            return "goodbye"

        if self._is_greeting(text):
            return "greeting"

        if self._is_youtube_search(text):
            return "youtube_search"

        if self._is_youtube(text):
            return "youtube"

        if self._is_instagram(text):
            return "instagram"

        if self._is_help(text):
            return "help"

        if self._is_clear_memory(text):
            return "clear_memory"

        if self._is_memory_info(text):
            return "memory_info"

        if self._is_date(text):
            return "date"

        if self._is_time(text):
            return "time"

        if self._is_calculator(text):
            return "calculator"

        return None

    # BUYRUQLARNI BAJARISH
    def execute(self, intent, text):
        if intent == "greeting":
            return self._random_response("greeting")

        if intent == "goodbye":
            self.running = False
            return self._random_response("goodbye")

        if intent == "remember":
            return self.remember_fact(text)

        if intent == "recall_name":
            return self.recall_name()

        if intent == "recall_memory":
            return self.recall_memory(text)

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

    # XOTIRA: ESLAB QOLISH
    def _is_remember_request(self, text):
        phrases = [
            "buni eslab qol",
            "shuni eslab qol",
            "eslab qol",
            "yodlab qol",
            "yodda saqla",
            "buni unutma"
        ]
        return any(phrase in text for phrase in phrases)

    
    def remember_fact(self, text):
        normalized = self._normalize(text)

        # Buyruq boshidagi ortiqcha so'zlarni olib tashlash
        fact = re.sub(
            r"^(eslab qol|yodlab qol|yodda saqla|unutma)\s*[:,\-]?\s*",
            "",
            normalized
        ).strip(" .,!?:;")

        fact = re.sub(
            r"\s*(buni|shuni)?\s*(eslab qol|yodlab qol|yodda saqla|unutma)[.!?]*$",
            "",
            fact
        ).strip(" .,!?:;")

        if not fact:
            return "Nimani eslab qolishim kerakligini aniqroq yozing."

        # Ismni alohida saqlash
        match = re.search(r"(?:mening\s+)?ismim\s+(.+)", fact)
        if match:
            name = match.group(1).strip(" .,!?:;")
            self._memory_add("system", "JARVIS_FACT:name=" + name)
            return "Tushundim. Ismingizni xotiramga saqladim."

        self._memory_add("system", "JARVIS_FACT:" + fact)
        return "Tushundim. Bu ma'lumotni xotiramga saqladim."


        # XOTIRA: ISMNI QAYTA TOPISH
    def _is_recall_name(self, text):
        phrases = [
            "mening ismim nima",
            "ismim nima",
            "ismimni ayt",
            "meni taniysanmi",
            "ismimni eslaysanmi"
        ]
        return any(phrase in text for phrase in phrases)

    def recall_name(self):
        try:
            records = self.memory.history()

            # Avval maxsus saqlangan faktlarni qidirish
            for record in reversed(records):
                if record.get("role") != "system":
                    continue

                message = str(record.get("message", ""))
                match = re.search(
                    r"JARVIS_FACT:name=(.+)",
                    message,
                    re.IGNORECASE
                )
                if match:
                    name = match.group(1).strip()
                    if name:
                        return "Sizning ismingiz " + name.capitalize() + "."

            # Eski suhbatlardan ham ismni qidirish
            for record in reversed(records):
                if record.get("role") != "user":
                    continue

                message = self._normalize(record.get("message", ""))
                match = re.search(
                    r"mening ismim\s+([a-zа-яё'-]+)",
                    message,
                    re.IGNORECASE
                )
                if match:
                    return "Sizning ismingiz " + match.group(1).capitalize() + "."

            return "Ismingiz xotiramda topilmadi."

        except Exception as error:
            print("MEMORY ERROR:", error)
            return "Xotirani o'qishda xatolik yuz berdi."

    # XOTIRA: UMUMIY QIDIRUV
    
    def _is_recall_memory(self, text):
        phrases = [
            "nimalarni eslaysan",
            "men haqimda nima bilasan",
            "men haqimda nimalarni bilasan",
            "men haqimda eslaganlaring",
            "eslab qolganlaringni ayt",
            "xotirangda nima bor"
        ]

        if any(phrase in text for phrase in phrases):
            return True

        # "Mening sevimli o'yinim nima?" kabi savollar
        if (
            text.startswith("mening ")
            and (" nima" in text or " qaysi" in text)
        ):
            return True

        return False


    
    def recall_memory(self, text=""):
        try:
            records = self.memory.history()
            facts = []

            for record in records:
                if record.get("role") != "system":
                    continue

                message = str(record.get("message", ""))
                if message.startswith("JARVIS_FACT:"):
                    fact = message.replace("JARVIS_FACT:", "", 1).strip()

                    if fact.startswith("name="):
                        fact = "Ismi: " + fact.split("=", 1)[1]

                    if fact not in facts:
                        facts.append(fact)

            if not facts:
                return "Hozircha xotiramda alohida saqlangan ma'lumot yo'q."

            # Umumiy xotira haqida so'rov
            normalized = self._normalize(text)
            general_questions = [
                "nimalarni eslaysan",
                "men haqimda nima bilasan",
                "men haqimda nimalarni bilasan",
                "men haqimda eslaganlaring",
                "eslab qolganlaringni ayt",
                "xotirangda nima bor"
            ]

            if any(q in normalized for q in general_questions):
                return "Xotiramda saqlangan ma'lumotlar:\n" + "\n".join(
                    "• " + fact for fact in facts[-20:]
                )

            # Savoldagi asosiy so'zlarni ajratish
            ignored = {
                "mening", "men", "nima", "qaysi", "qanaqa",
                "haqida", "ayt", "eslaysanmi", "eslaysan",
                "iltimos", "jarvis", "bu", "shu"
            }

            question_words = set(re.findall(r"[a-zа-яё0-9']+", normalized))
            question_words -= ignored

            best_fact = None
            best_score = 0

            for fact in reversed(facts):
                fact_normalized = self._normalize(fact)
                fact_words = set(re.findall(r"[a-zа-яё0-9']+", fact_normalized))
                fact_words -= ignored

                common = question_words.intersection(fact_words)
                score = len(common)

                if score > best_score:
                    best_score = score
                    best_fact = fact

            if best_fact and best_score > 0:
                if best_fact.startswith("name="):
                    return "Ismingiz " + best_fact.split("=", 1)[1] + "."

                return "Xotiramda bu ma'lumot bor: " + best_fact

            return "Bu savolga mos ma'lumot xotiramda topilmadi."

        except Exception as error:
            print("MEMORY ERROR:", error)
            return "Xotirani o'qishda xatolik yuz berdi."


        # VAQT VA SANA
    def get_time(self):
        return "Hozir soat " + datetime.now().strftime("%H:%M") + "."

    def get_date(self):
        now = datetime.now()
        months = [
            "yanvar", "fevral", "mart", "aprel",
            "may", "iyun", "iyul", "avgust",
            "sentabr", "oktabr", "noyabr", "dekabr"
        ]
        return (
            "Bugun " + str(now.day) + " " +
            months[now.month - 1] + " " +
            str(now.year) + "-yil."
        )

    # YOUTUBE
    def open_youtube(self):
        if self.open_url("https://www.youtube.com"):
            return "YouTube ochildi."
        return "YouTube'ni ochib bo'lmadi."

    def search_youtube(self, query):
        url = "https://www.youtube.com/results?search_query=" + quote(query)
        if self.open_url(url):
            return "YouTube'da qidirilmoqda."
        return "YouTube qidiruvini ochib bo'lmadi."

    def extract_youtube_query(self, text):
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
            if normalized.startswith(prefix):
                return normalized[len(prefix):].strip()

        return ""

    # INSTAGRAM VA HAVOLALAR
    def open_instagram(self):
        try:
            result = subprocess.run(
                [
                    "am", "start",
                    "-a", "android.intent.action.VIEW",
                    "-d", "instagram://app"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                return "Instagram ochildi."
        except Exception:
            pass

        if self.open_url("https://www.instagram.com"):
            return "Instagram ochildi."

        return "Instagram'ni ochib bo'lmadi."

    def open_url(self, url):
        try:
            result = subprocess.run(
                [
                    "am", "start",
                    "-a", "android.intent.action.VIEW",
                    "-d", url
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

        try:
            return bool(webbrowser.open(url))
        except Exception:
            return False

    # KALKULYATOR
    def _is_calculator(self, text):
        prefixes = [
            "hisobla", "hisoblab ber", "hisoblash",
            "matematikani hisobla", "matematik hisob",
            "misolni yech", "matematikani yech"
        ]
        return (
            any(text.startswith(p) for p in prefixes)
            or bool(re.search(r"\d\s*[\+\-\*/%]\s*\d", text))
        )

    def extract_calculation(self, text):
        normalized = self._normalize(text)
        prefixes = [
            "matematikani hisobla", "matematik hisob",
            "hisoblab ber", "hisoblash", "hisobla",
            "hisob-kitob qil", "matematikani yech",
            "misolni yech"
        ]

        for prefix in prefixes:
            if normalized.startswith(prefix):
                return normalized[len(prefix):].strip()

        return text.strip()

    def calculate(self, expression):
        expression = str(expression).strip()
        expression = expression.replace(",", ".")
        expression = expression.replace("×", "*")
        expression = expression.replace("÷", "/")
        expression = expression.replace("−", "-")

        if not expression or len(expression) > 100:
            return "Hisoblash uchun to'g'ri misol kiriting."

        try:
            tree = ast.parse(expression, mode="eval")
            result = self.safe_eval(tree.body)

            if isinstance(result, float):
                if not math.isfinite(result):
                    return "Natija aniqlanmadi."
                if result.is_integer():
                    result = int(result)

            return "Javob: " + str(result)

        except ZeroDivisionError:
            return "Nolga bo'lish mumkin emas."
        except Exception:
            return "Bu matematik ifodani hisoblay olmadim."

    def safe_eval(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Ruxsat etilmagan qiymat")

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
                raise ValueError("Ruxsat etilmagan amal")

            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Daraja juda katta")

            result = operation()
            if isinstance(result, (int, float)) and abs(result) > 10**100:
                raise ValueError("Natija juda katta")
            return result

        if isinstance(node, ast.UnaryOp):
            value = self.safe_eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.USub):
                return -value
            raise ValueError("Ruxsat etilmagan amal")

        if isinstance(node, ast.Name):
            constants = {"pi": math.pi, "e": math.e}
            if node.id in constants:
                return constants[node.id]
            raise ValueError("Noma'lum qiymat")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Ruxsat etilmagan funksiya")

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
                "factorial": self.safe_factorial
            }

            function = functions.get(node.func.id)
            if function is None or len(node.args) != 1:
                raise ValueError("Ruxsat etilmagan funksiya")

            args = [self.safe_eval(arg) for arg in node.args]
            return function(*args)

        raise ValueError("Ruxsat etilmagan ifoda")

    def safe_factorial(self, value):
        if not isinstance(value, int) or value < 0 or value > 100:
            raise ValueError("Faktorial qiymati noto'g'ri")
        return math.factorial(value)

    # YORDAM VA XOTIRA BOSHQARUVI
    def help(self):
        return (
            "Men quyidagilarni bajara olaman:\n"
            "• Vaqtni aytish\n"
            "• Sanani aytish\n"
            "• YouTube ochish va qidirish\n"
            "• Instagram ochish\n"
            "• Matematik hisoblash\n"
            "• Ma'lumotni eslab qolish\n"
            "• Ismingizni eslash\n"
            "• Xotiradagi ma'lumotlarni ko'rsatish\n"
            "• Xotira haqida ma'lumot berish\n"
            "• Salomlashish"
        )

    def memory_info(self):
        try:
            info = self.memory.info()
            total = info.get("total", 0)
            return "Xotirada " + str(total) + " ta yozuv saqlangan."
        except Exception:
            return "Xotira ma'lumotini olib bo'lmadi."

    def clear_memory(self):
        try:
            self.memory.clear()
            return "Xotira tozalandi."
        except Exception:
            return "Xotirani tozalashda xatolik yuz berdi."

    # RASM QABUL QILISH
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

    # XOTIRAGA YOZISH
    def _memory_add(self, role, message):
        try:
            self.memory.add(role, message)
        except TypeError:
            try:
                self.memory.add(message)
            except Exception as error:
                print("MEMORY ADD ERROR:", error)
        except Exception as error:
            print("MEMORY ADD ERROR:", error)

    # MATNNI NORMALIZATSIYA QILISH
    def _normalize(self, text):
        text = str(text).lower().strip()

        replacements = {
            "ʻ": "'", "ʼ": "'", "’": "'",
            "‘": "'", "`": "'", "´": "'"
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        return re.sub(r"\s+", " ", text)

    # BUYRUQLARNI TEKSHIRISH
    def _is_greeting(self, text):
        return text in [
            "salom", "salom jarvis",
            "assalomu alaykum",
            "assalomu alaykum jarvis",
            "hello", "hi", "hey jarvis",
            "qalaysan", "yaxshimisan"
        ]

    def _is_goodbye(self, text):
        return text in [
            "xayr", "hayr", "bye", "goodbye",
            "ko'rishguncha", "ko'rishamiz",
            "jarvis xayr"
        ]

    def _is_youtube_search(self, text):
        return any(text.startswith(prefix) for prefix in [
            "youtube qidir", "youtubedan qidir",
            "youtube dan qidir", "youtube ichidan qidir",
            "youtube'dan qidir", "youtube search",
            "youtubeda qidir"
        ])

    def _is_youtube(self, text):
        return text in [
            "youtube", "youtube och", "youtubeni och",
            "youtube ni och", "youtube ishga tushir",
            "youtubeni ishga tushir",
            "youtube dasturini och"
        ]

    def _is_instagram(self, text):
        return text in [
            "instagram", "instagram och",
            "instagramni och", "instagram ni och",
            "instagram ishga tushir",
            "instagramni ishga tushir",
            "instagram dasturini och"
        ]

    def _is_help(self, text):
        return text in [
            "yordam", "yordam ber",
            "nimalar qila olasan", "nima qila olasan",
            "buyruqlar", "buyruqlarni ko'rsat",
            "yordam menyusi", "help"
        ]

    def _is_clear_memory(self, text):
        return text in [
            "xotirani tozalash", "xotirani o'chir",
            "memoryni tozalash", "memoryni o'chir",
            "barcha xotirani o'chir",
            "hamma xotirani o'chir"
        ]

    def _is_memory_info(self, text):
        return text in [
            "xotirani ko'rsat", "memoryni ko'rsat",
            "memory", "xotira",
            "qancha narsani eslaysan",
            "xotira haqida"
        ]

    def _is_date(self, text):
        return text in [
            "bugun sana nima", "bugungi sana",
            "sana nima", "bugun nechanchi",
            "bugun qaysi sana", "sanani ayt",
            "bugungi sanani ayt"
        ]
    def _is_time(self, text):
        return text in [
            "soat nechchi", "soat nechi",
            "hozir soat nechchi", "hozir soat nechi",
            "vaqtni ayt", "vaqtni ko'rsat",
            "hozirgi vaqt", "vaqt"
        ]

    def _random_response(self, intent):
        responses = self.responses.get(intent, [])
        if not responses:
            return ""
        return responses[datetime.now().microsecond % len(responses)]
    def unknown(self):
        return "Kechirasiz, bu buyruqni hali to'liq tushunmadim."


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
