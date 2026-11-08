# -*- coding: utf-8 -*-
"""Qo'lsiz rejim: "Jarvis" deb chaqirsangiz tinglaydi, bajaradi va ovoz bilan javob beradi.

Qanday ishlaydi:
  uxlash   -> doimiy tinglaydi, faqat "Jarvis" so'zini kutadi (boshqa gaplarni e'tiborsiz qoldiradi)
  uyg'oq   -> "Jarvis" deganingizdan keyin ~9 soniya davomida ismsiz ham buyruq qabul qiladi
  band     -> buyruq bajarilayotganda va javob o'qilayotganda mikrofon o'chiq (o'zini eshitmaydi)

"Quloq" (ovozni matnga aylantirish) almashtiriladigan qism: hozir Android'ning
SpeechRecognizer xizmati, keyinroq Jarvisning o'z oflayn quloqi bilan almashtiriladi.

Cheklov: ilova ochiq va ekran yoniq bo'lishi kerak (fon xizmati alohida qadam).
"""
import difflib
import re
import time

WAKE_WORD = "jarvis"
WAKE_VARIANTS = ("yarvis", "jorvis", "djarvis", "jarviz", "jarvise", "jarvisga")

CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "s",
    "ч": "ch", "ш": "sh", "ъ": "'", "ы": "i", "э": "e", "ю": "yu", "я": "ya",
    "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}

STOP_PHRASES = (
    "uxla", "uxlab qol", "tinglama", "tinglashni toxtat", "tinglashni to'xtat",
    "qolsiz rejimni ochir", "qolsiz rejimni o'chir", "qo'lsiz rejimni o'chir",
    "bas qil", "boldi uxla", "bo'ldi uxla",
)


def normalize(text):
    t = str(text).lower()
    for ch in "ʻʼ’‘`´":
        t = t.replace(ch, "'")
    t = "".join(CYRILLIC.get(c, c) for c in t)
    return re.sub(r"[^a-z0-9' ]+", " ", t)


def find_wake(text):
    """("jarvis soat nechi") -> (True, "soat nechi"). Topilmasa (False, "")."""
    raw = [w for w in re.split(r"\s+", str(text).strip()) if w]

    for index, word in enumerate(raw[:5]):
        token = normalize(word).strip()
        if not token:
            continue

        close = 5 <= len(token) <= 8 and difflib.SequenceMatcher(None, token, WAKE_WORD).ratio() >= 0.8
        if token == WAKE_WORD or close or token in WAKE_VARIANTS:
            return True, " ".join(raw[index + 1:]).strip(" ,.!?;:-")

    return False, ""


def wants_stop(text):
    t = normalize(text).replace("'", "")
    return any(p.replace("'", "") in t for p in STOP_PHRASES)


class HandsFree:
    AWAKE_WINDOW = 9.0
    REPLY_TIMEOUT = 120.0

    def __init__(self, app, ears, clock=None, now=time.time):
        self.app = app
        self.ears = ears
        self.now = now
        if clock is None:
            from kivy.clock import Clock as clock
        self.clock = clock

        self.running = False
        self.spoken = []            # (gap, vaqt): Jarvisning o'zi aytgan gaplar
        self.state = "sleep"
        self.deadline = 0.0
        self.failures = 0
        self.warned = False
        self._poll = None

    # ---------- boshqaruv ----------
    def start(self):
        if self.running:
            return
        self.running = True
        self.state = "sleep"
        self.failures = 0
        self.warned = False
        self.ears.start(self)
        self.ears.keep_screen_on(True)
        self._listen()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.state = "sleep"
        if self._poll is not None:
            self._poll.cancel()
            self._poll = None
        self.ears.stop()
        self.ears.keep_screen_on(False)

    def note_spoken(self, text):
        """Jarvis gapirgan har bir gapni eslab qoladi (o'zini eshitib qolmaslik uchun)."""
        self.spoken.append((str(text), self.now()))
        del self.spoken[:-8]

    def _is_echo(self, text):
        heard = normalize(text).split()
        if not heard:
            return True

        joined = "".join(heard)
        now = self.now()

        for said, when in self.spoken:
            if now - when > 90:
                continue

            words = normalize(said).split()
            if not words:
                continue

            said_joined = "".join(words)
            if len(joined) >= 5 and joined in said_joined:
                return True
            if len(heard) >= 2 and sum(w in words for w in heard) / float(len(heard)) >= 0.6:
                return True
            if len(joined) >= 6 and difflib.SequenceMatcher(None, joined, said_joined).ratio() >= 0.7:
                return True

        return False

    # ---------- "quloq"dan keladigan xabarlar (istalgan oqimdan) ----------
    def heard(self, texts):
        self.clock.schedule_once(lambda dt: self._on_text(list(texts)), 0)

    def silence(self):
        self.clock.schedule_once(lambda dt: self._on_silence(), 0)

    def failed(self, message, fatal=False):
        self.clock.schedule_once(lambda dt: self._on_failed(message, fatal), 0)

    # ---------- asosiy mantiq (Kivy asosiy oqimida) ----------
    def _on_text(self, texts):
        if not self.running or not texts:
            return

        self.failures = 0

        if self.state == "busy":
            return                  # javob tayyorlanayotganda kelgan kech natija

        texts = [t for t in texts if not self._is_echo(t)]
        if not texts:
            self._listen()          # bu Jarvisning o'z ovozi edi
            return

        if self.state == "awake":
            if any(wants_stop(t) for t in texts):
                self.app.handsfree_stopped_by_voice()
            else:
                self._run(texts[0])
            return

        for text in texts:
            found, rest = find_wake(text)
            if found:
                if rest and wants_stop(rest):
                    self.app.handsfree_stopped_by_voice()
                elif rest:
                    self._run(rest)
                else:
                    self._ack()
                return

        self._listen()          # "Jarvis" aytilmadi - e'tiborsiz

    def _on_silence(self):
        if not self.running:
            return
        if self.state == "awake" and self.now() > self.deadline:
            self.state = "sleep"
        self._listen()

    def _on_failed(self, message, fatal):
        if not self.running:
            return
        if fatal:
            self.app.handsfree_stopped_by_error(message)
            return

        self.failures += 1
        if self.failures >= 3 and not self.warned:
            self.warned = True
            self.app.add_message("Qo'lsiz rejim: " + str(message), False, save=False)

        self._listen(delay=min(1.0 * (2 ** (self.failures - 1)), 10.0))

    def _listen(self, delay=0.25):
        if self.running:
            self.clock.schedule_once(lambda dt: self.running and self.ears.listen(), delay)

    def _ack(self):
        self.state = "busy"
        self.app.handsfree_say("Eshitaman.")
        self._after_speech(self._awake_listen)

    def _run(self, command):
        self.state = "busy"
        self.clock.schedule_once(lambda dt: self.app.process_command(command), 0)
        self._after_speech(self._awake_listen, delay=0.5)

    def _awake_listen(self):
        if not self.running:
            return
        self.state = "awake"
        self.deadline = self.now() + self.AWAKE_WINDOW
        self._listen()

    def _after_speech(self, callback, delay=0.5):
        """Buyruq bajarilib, javob o'qib bo'lingach callback ni chaqiradi."""
        started = self.now()
        if self._poll is not None:
            self._poll.cancel()

        def check(dt):
            if not self.running:
                self._poll.cancel()
                return False
            if (self.app.busy or self.app.is_speaking()) and self.now() - started < self.REPLY_TIMEOUT:
                return None
            self._poll.cancel()
            self._poll = None
            # xona aks-sadosi va dinamik "dumi" so'nsin, keyin mikrofonni ochamiz
            self.clock.schedule_once(lambda dt: callback(), 0.8)

        # birinchi tekshiruv biroz kechikib boshlansin (busy bayrog'i o'rnatilib bo'lsin)
        self._poll = self.clock.schedule_interval(check, max(0.3, delay))


# ============================ Android quloq ============================
_keep = []      # Java'ga uzatilgan Runnable'larni GC o'chirib yubormasligi uchun


def run_on_main(function):
    """Fon xizmatida: funksiyani Android'ning asosiy oqimida bajaradi (SpeechRecognizer shuni talab qiladi)."""
    from jnius import PythonJavaClass, java_method, autoclass

    class Task(PythonJavaClass):
        __javainterfaces__ = ["java/lang/Runnable"]
        __javacontext__ = "app"

        @java_method("()V")
        def run(self):
            try:
                function()
            except Exception as error:
                print("RUN_ON_MAIN ERROR:", error)
            finally:
                if task in _keep:
                    _keep.remove(task)

    task = Task()
    _keep.append(task)
    looper = autoclass("android.os.Looper").getMainLooper()
    autoclass("android.os.Handler")(looper).post(task)


class AndroidEars:
    """Android SpeechRecognizer orqali tinglaydi (Google xizmati; keyin o'z quloqimiz bilan almashadi)."""

    def __init__(self, service=False):
        self.service = service
        self.wake_lock = None
        self.engine = None
        self.recognizer = None
        self.listener = None
        self.lang = "uz-UZ"

    def start(self, engine):
        self.engine = engine
        self._make_listener()

    def _make_listener(self):
        from jnius import PythonJavaClass, java_method

        ears = self

        class Listener(PythonJavaClass):
            __javainterfaces__ = ["android/speech/RecognitionListener"]
            __javacontext__ = "app"

            @java_method("(Landroid/os/Bundle;)V")
            def onReadyForSpeech(self, params):
                pass

            @java_method("()V")
            def onBeginningOfSpeech(self):
                pass

            @java_method("(F)V")
            def onRmsChanged(self, rms):
                pass

            @java_method("([B)V")
            def onBufferReceived(self, buffer):
                pass

            @java_method("()V")
            def onEndOfSpeech(self):
                pass

            @java_method("(I)V")
            def onError(self, code):
                ears._on_error(int(code))

            @java_method("(Landroid/os/Bundle;)V")
            def onResults(self, results):
                ears._on_results(results)

            @java_method("(Landroid/os/Bundle;)V")
            def onPartialResults(self, results):
                pass

            @java_method("(ILandroid/os/Bundle;)V")
            def onEvent(self, event, params):
                pass

        self.listener = Listener()

    def _on_results(self, results):
        texts = []
        try:
            items = results.getStringArrayList("results_recognition")
            for i in range(items.size()):
                texts.append(str(items.get(i)))
        except Exception as error:
            print("QULOQ RESULT ERROR:", error)

        if texts:
            self.engine.heard(texts)
        else:
            self.engine.silence()

    def _on_error(self, code):
        # 6 = gapirilmadi, 7 = tushunilmadi: oddiy holat, qayta tinglaymiz
        if code in (6, 7):
            self.engine.silence()
        elif code == 9:
            self.engine.failed("Mikrofon ruxsati yo'q. Telefon sozlamalarida JARVIS uchun mikrofonni yoqing.", True)
        elif code in (1, 2, 4):
            self.engine.failed("Ovoz tanish xizmatiga ulanib bo'lmadi (internetni tekshiring).")
        elif code in (3, 5, 8):
            self._destroy()
            self.engine.failed("Ovoz tanish xizmati qayta ishga tushirilmoqda (kod %d)." % code)
        else:
            self.engine.failed("Ovoz tanishda xato (kod %d)." % code)

    def listen(self):
        self._listen_ui()

    def _ui(self, function):
        if self.service:
            return lambda: run_on_main(function)

        from android.runnable import run_on_ui_thread
        return run_on_ui_thread(function)

    def _context(self):
        from jnius import autoclass

        if self.service:
            return autoclass("org.kivy.android.PythonService").mService
        return autoclass("org.kivy.android.PythonActivity").mActivity

    def _listen_ui(self):
        def work():
            try:
                from jnius import autoclass

                SpeechRecognizer = autoclass("android.speech.SpeechRecognizer")
                Intent = autoclass("android.content.Intent")
                RecognizerIntent = autoclass("android.speech.RecognizerIntent")
                activity = self._context()

                if not SpeechRecognizer.isRecognitionAvailable(activity):
                    self.engine.failed("Telefonda ovozni tanish xizmati topilmadi.", True)
                    return

                if self.recognizer is None:
                    self.recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
                    self.recognizer.setRecognitionListener(self.listener)

                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, self.lang)
                intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                intent.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, activity.getPackageName())
                self.recognizer.startListening(intent)
            except Exception as error:
                print("QULOQ LISTEN ERROR:", error)
                self.engine.failed("Tinglashni boshlab bo'lmadi: " + repr(error)[:100])

        self._ui(work)()

    def _destroy(self):
        def work():
            try:
                if self.recognizer is not None:
                    self.recognizer.destroy()
            except Exception:
                pass
            self.recognizer = None

        self._ui(work)()

    def stop(self):
        self._destroy()
        if self.service:
            self._wake_lock(False)

    def _wake_lock(self, on):
        """Fon xizmatida ekran o'chiq bo'lsa ham protsessor uxlab qolmasin."""
        try:
            from jnius import autoclass

            if on and self.wake_lock is None:
                context = self._context()
                power = context.getSystemService("power")
                self.wake_lock = power.newWakeLock(1, "jarvis:fon")   # PARTIAL_WAKE_LOCK
                self.wake_lock.acquire()
            elif not on and self.wake_lock is not None:
                self.wake_lock.release()
                self.wake_lock = None
        except Exception as error:
            print("WAKE LOCK ERROR:", error)

    def keep_screen_on(self, on):
        if self.service:
            self._wake_lock(on)
            return

        def work():
            try:
                from jnius import autoclass
                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                window = activity.getWindow()
                (window.addFlags if on else window.clearFlags)(128)   # FLAG_KEEP_SCREEN_ON
            except Exception as error:
                print("KEEP SCREEN ERROR:", error)

        self._ui(work)()
