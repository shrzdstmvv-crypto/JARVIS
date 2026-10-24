
import ast
import math
import os
import re
import subprocess
import webbrowser
from datetime import datetime
from urllib.parse import quote

from language_brain import LanguageBrain
from learning import Learner
from images_store import ImageStore
from memory import Memory


class JARVIS:
    def __init__(self):
        self.brain = LanguageBrain()
        self.memory = Memory()
        self.learner = Learner(self.brain.normalize)
        self.images = ImageStore(self.brain.normalize)
        self.pending_teach = None
        self.pending_correct = None
        self.pending_image_name = None
        self.last_learned = None
        self.declined = set()
        self.image_to_show = None
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

        previous_learned = self.last_learned
        self.last_learned = None

        # 1. Kutilayotgan savollar, o'rgatish va rasm buyruqlari
        had_pending = (
            self.pending_teach is not None
            or self.pending_correct is not None
            or self.pending_image_name is not None
        )
        response = self.learning_step(text, previous_learned)

        # Kutilayotgan savol bekor bo'lib, gap yangi buyruq bo'lsa, uni
        # o'rgatish buyruqlari qatorida qayta tekshiramiz
        if response is None and had_pending:
            response = self.learning_step(text, previous_learned)

        # 2. Aniq o'rgatilgan javob
        if response is None:
            answer = self.learner.exact_answer(text)

            if answer is not None:
                response = answer
                self.last_learned = text

        # 3. Oddiy buyruqlar
        if response is None:
            response = self.route_command(text, normalized)

        if response is None:
            response = ""

        response = str(response)

        # Xabarlarni xotiraga yozish
        self._memory_add("user", text)
        self._memory_add("assistant", response)

        return response

    def route_command(self, text, normalized):
        intent = (
            self.detect_local_command(normalized)
            or self.learner.find_intent(text)
        )

        if not intent:
            try:
                intent, confidence = self.brain.predict(text)
            except Exception:
                intent = "unknown"

        if intent == "unknown":
            answer = self.learner.fuzzy_answer(text)

            if answer is not None:
                self.last_learned = text
                return answer

            return self.start_teaching(text)

        try:
            response = self.execute(intent, text)
        except Exception as error:
            print("JARVIS ERROR:", error)
            return "Buyruqni bajarishda xatolik yuz berdi."

        # Xotirada javob topilmasa, o'rgatishni taklif qilamiz
        if intent == "recall_memory" and response in self.NOT_FOUND_REPLIES:
            return self.start_teaching(text)

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
                normalized = normalized[len(prefix):].strip()
                break
        else:
            normalized = text.strip()

        # "2+3*4 nechchi", "5*5 nechaga teng" kabi qo'shimcha so'zlar
        normalized = re.sub(
            r"\b(nechchi|nechi|necha\w*|teng|bo'ladi|boladi|"
            r"natijasi|javobi|qancha)\b",
            " ",
            normalized,
            flags=re.IGNORECASE
        )

        return re.sub(r"\s+", " ", normalized).strip(" =?")

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
            "• Salomlashish\n"
            "• Yangi gaplarni o'rganish (o'rgat: savol = javob)\n"
            "• Rasmlarni nomlash va topib berish"
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
            return "Rasm topilmadi."

        path = str(path)

        if not os.path.exists(path):
            return "Rasm faylini topib bo'lmadi."

        self.current_image = path
        self.pending_teach = None
        self.pending_correct = None
        self.images.add(path)
        self.pending_image_name = path

        self._memory_add(
            "system",
            "Rasm qabul qilindi: " + os.path.basename(path)
        )

        return (
            "Rasm qabul qilindi. Unga qanday nom berasiz? "
            "(masalan: mashina). Nomsiz qoldirish uchun: bekor."
        )

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
    # O'RGATISH REJIMI
    SKIP_WORDS = {
        "bekor", "bekor qil", "yo'q", "yoq", "kerak emas",
        "o'tkazib yubor", "otkazib yubor", "qoldir"
    }

    WRONG_WORDS = {
        "xato", "noto'g'ri", "notogri", "bu xato", "bu noto'g'ri",
        "javobing xato", "javobing noto'g'ri", "noto'g'ri javob"
    }

    NOT_FOUND_REPLIES = {
        "Hozircha xotiramda alohida saqlangan ma'lumot yo'q.",
        "Bu savolga mos ma'lumot xotiramda topilmadi."
    }

    def ask_to_teach(self):
        return (
            "Bu gapni tushunmadim. Menga o'rgating: shunga qanday "
            "javob berishim kerak? Javobni yozing yoki mavjud buyruqni "
            "ko'rsating (masalan: buyruq soat). "
            "O'tkazib yuborish uchun: bekor."
        )

    def start_teaching(self, text):
        # Oldin "bekor" degan gapni qayta so'ramaymiz
        if self._normalize(text) in self.declined:
            return self.unknown()

        self.pending_teach = text
        return self.ask_to_teach()

    def _brain_knows(self, text):
        # Faqat ishonchli (deyarli aniq) moslik bo'lsa buyruq deb hisoblaymiz
        try:
            intent, confidence = self.brain.predict(text)
            return intent != "unknown" and confidence >= 0.9
        except Exception:
            return False

    LEARN_LIST_WORDS = {
        "o'rganganlar", "o'rganganlarim", "organganlar",
        "nimalarni o'rgandingiz", "nimalarni o'rgandim",
        "nimalarni organding", "nimalarni o'rgandin"
    }

    def _is_meta_command(self, text, normalized):
        if normalized in self.LEARN_LIST_WORDS:
            return True

        if re.match(r"^(?:o[ʻʼ’‘`'´]?rgat|unut)\b", text.strip(),
                    re.IGNORECASE):
            return True

        words = normalized.split()

        if not any(w.startswith(("rasm", "surat", "foto")) for w in words):
            return False

        # Rasm buyruqlari: ko'rsat, nomla, ro'yxat, o'chir
        return bool(
            any(w.startswith(self.SHOW_PREFIXES) for w in words)
            or any(w.startswith(("o'chir", "ochir", "rasmlar")) for w in words)
            or "deb" in words
            or "nomi" in words
        )

    def _looks_like_command(self, text, normalized):
        return bool(
            self._is_meta_command(text, normalized)
            or self._is_remember_request(normalized)
            or self._is_recall_name(normalized)
            or self.learner.find_intent(text)
            or self._brain_knows(text)
        )

    def learning_step(self, text, previous_learned=None):
        raw = text.strip()
        normalized = self._normalize(raw)

        # Kutilayotgan savollarga javob
        if self.pending_image_name is not None:
            return self._handle_image_name(text)

        if self.pending_teach is not None:
            return self._handle_teach_answer(text)

        if self.pending_correct is not None:
            return self._handle_correction(text)

        # "bekor" yolg'iz kelsa
        if normalized in self.SKIP_WORDS:
            return "Xo'p."

        # Oxirgi o'rgatilgan javob xato bo'lsa, to'g'rilash
        if previous_learned is not None and normalized in self.WRONG_WORDS:
            self.pending_correct = previous_learned
            return "Kechirasiz. To'g'ri javobni yozing (yoki: bekor)."

        # o'rgat: savol = javob
        match = re.match(
            r"^o[ʻʼ’‘`'´]?rgat\s*:?\s*(.+?)\s*=\s*(.+)$",
            raw,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            if self.learner.add_answer(match.group(1), match.group(2)):
                return "Esladim. Endi shu gapga shunday javob beraman."

            return "O'rgatishda xatolik yuz berdi."

        # unut: savol
        match = re.match(r"^unut\s*:?\s*(.+)$", raw, re.IGNORECASE)

        if match:
            if self.learner.forget(match.group(1)):
                return "Unutdim."

            return "Bunday o'rgatilgan gap topilmadi."

        # O'rgangan narsalar ro'yxati
        if normalized in self.LEARN_LIST_WORDS:
            return self.learned_list()

        return self.image_command(raw, normalized)

    def learned_list(self):
        count = self.learner.count()

        if count == 0:
            return "Hali hech narsa o'rganmadim."

        lines = "\n".join("• " + q for q in self.learner.samples(10))
        return (
            "Men " + str(count) + " ta narsani o'rganganman. "
            "Oxirgilari:\n" + lines
        )

    def _handle_teach_answer(self, text):
        original = self.pending_teach
        normalized = self._normalize(text)

        if normalized in self.SKIP_WORDS:
            self.pending_teach = None
            self.declined.add(self._normalize(original))
            return "Xo'p, o'tkazib yubordim."

        # Foydalanuvchi yangi buyruq bergan bo'lsa, o'rgatishni bekor qilamiz
        if self._looks_like_command(text, normalized):
            self.pending_teach = None
            return None

        # buyruq <nom>
        match = re.match(r"^buyruq\s+(\S+)$", normalized)

        if match:
            intent = self.learner.ALIASES.get(match.group(1))

            if not intent:
                names = ", ".join(sorted(self.learner.ALIASES))
                return "Bunday buyruq yo'q. Mavjudlari: " + names + "."

            self.learner.add_phrase(original, intent)
            self.pending_teach = None
            return (
                "Tushundim. Endi bu gapni «" + match.group(1)
                + "» buyrug'i deb bilaman."
            )

        # Oddiy javob sifatida saqlash
        self.pending_teach = None

        if self.learner.add_answer(original, text):
            return "Esladim. Endi shu gapga shunday javob beraman."

        return "O'rgatishda xatolik yuz berdi."

    def _handle_correction(self, text):
        question = self.pending_correct
        normalized = self._normalize(text)

        if normalized in self.SKIP_WORDS:
            self.pending_correct = None
            return "Xo'p, o'zgartirmadim."

        if self._looks_like_command(text, normalized):
            self.pending_correct = None
            return None

        self.pending_correct = None

        if self.learner.add_answer(question, text):
            return "To'g'rilab qo'ydim. Rahmat!"

        return "To'g'rilashda xatolik yuz berdi."

    # RASMLAR: NOMLASH VA TOPIB BERISH
    SHOW_PREFIXES = (
        "ko'rs", "top", "ber", "chiqar", "och", "qani", "korsat"
    )

    def _handle_image_name(self, text):
        path = self.pending_image_name
        normalized = self._normalize(text)

        if normalized in self.SKIP_WORDS:
            self.pending_image_name = None
            return (
                "Xo'p, rasm nomsiz saqlandi. Keyin «oxirgi rasmni "
                "mashina deb nomla» desangiz nom berasiz."
            )

        # Uzun gap yoki buyruq bo'lsa, nomlashni to'xtatamiz
        if (
            len(normalized.split()) > 6
            or self._looks_like_command(text, normalized)
            or any(
                w.startswith(("rasm", "surat", "foto"))
                for w in normalized.split()
            )
        ):
            self.pending_image_name = None
            return None

        name = text.strip().strip("\"'«»“”.,!?")
        cleaned = re.sub(
            r"^(?:uning nomi|nomi|bu)\s+", "", name, flags=re.IGNORECASE
        ).strip()

        if cleaned:
            name = cleaned

        self.pending_image_name = None
        final = self.images.set_name(path, name[:40])

        if not final:
            return "Nomni saqlab bo'lmadi. Boshqa nom yozib ko'ring."

        return (
            "Saqladim: «" + final + "». «" + final
            + " rasmini ko'rsat» desangiz, topib beraman."
        )

    def image_command(self, raw, normalized):
        words = normalized.split()

        if not any(w.startswith(("rasm", "surat", "foto")) for w in words):
            return None

        # Oxirgi rasmni nomlash: "oxirgi rasmni mashina deb nomla"
        match = re.search(
            r"(?:rasm\w*|surat\w*|foto\w*)\s+(.+?)\s+deb\s+"
            r"(?:nomla\w*|ata\w*|saqla\w*)",
            raw,
            re.IGNORECASE
        )

        if not match:
            match = re.search(
                r"(?:rasm\w*|surat\w*)\s+nomi\s+(.+)$",
                raw,
                re.IGNORECASE
            )

        if match:
            name = match.group(1).strip().strip("\"'«»“”.,!?")
            final = self.images.name_last(name)

            if not final:
                return "Hali saqlangan rasm yo'q. Avval rasm yuboring."

            return "Oxirgi rasmga «" + final + "» deb nom berdim."

        # Rasmlar ro'yxati
        filler = {
            "ro'yxati", "royxati", "ko'rsat", "ko'rsatib", "ber", "barcha",
            "hamma", "menga", "qanday", "bor", "bormi", "mening",
            "saqlangan", "iltimos", "jarvis", "qaysi", "nechta", "qani",
            "ayt", "chiqar"
        }

        if any(w.startswith("rasmlar") for w in words) and not [
            w for w in words
            if not w.startswith("rasmlar") and w not in filler
        ]:
            return self.image_list()

        # O'chirish
        if any(w.startswith("o'chir") or w.startswith("ochir")
               for w in words):
            entry = self.images.find(normalized)

            if entry is None:
                return "Bunday nomli rasm topilmadi."

            name = entry["name"]
            self.images.remove(entry)
            return "«" + name + "» rasmini o'chirdim."

        # Topib berish
        wants_show = any(w.startswith(self.SHOW_PREFIXES) for w in words)

        if "oxirgi" in words and wants_show:
            entry = self.images.last()
        else:
            entry = self.images.find(normalized)

        if entry is not None:
            self.image_to_show = entry["path"]
            label = entry["name"] or "Oxirgi rasm"
            return "«" + label + "» rasmi:"

        if wants_show:
            return self.image_not_found()

        return None

    def image_list(self):
        names = self.images.names()

        if not names:
            if self.images.count():
                return (
                    "Rasmlaringiz bor, lekin hali nomsiz. «Oxirgi rasmni "
                    "mashina deb nomla» deb nom bering."
                )
            return "Hali saqlangan rasm yo'q."

        lines = "\n".join("• " + n for n in names)
        return (
            "Saqlangan rasmlar (" + str(len(names)) + "):\n" + lines
            + "\nKo'rish uchun: «nomi rasmini ko'rsat»."
        )

    def image_not_found(self):
        names = self.images.names()

        if not names:
            return "Hali nomlangan rasm yo'q."

        return (
            "Bunday nomli rasm topilmadi. Nomlari: " + ", ".join(names) + "."
        )

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
