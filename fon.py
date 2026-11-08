# -*- coding: utf-8 -*-
"""JARVIS fon rejimi: ilova yopiq yoki ekran o'chiq bo'lsa ham "Jarvis" deganingizni eshitadi.

Ikki qism:
  * fon xizmati (service.py -> run_service): alohida jarayonda ishlaydi, doimiy bildirishnoma
    bilan, tinglaydi, buyruqni bajaradi va o'z ovozi bilan javob beradi;
  * ilova tomoni (ensure_running/pop_log/status): xizmatni yoqadi, holatini va suhbat jurnalini o'qiydi.

Ikkala jarayon bir-biriga faqat fayllar orqali bog'lanadi (holat va jurnal), shuning uchun
xizmat xotira/o'rganish fayllarini o'zgartirmaydi (ikki jarayon bir-birining ustidan yozib yubormasin).

Cheklov: fon xizmati telefon oynasini ochishi shart bo'lgan amallarni (qo'ng'iroq, budilnik,
ilova ochish) Android qoidalari tufayli bajara olmaydi; buni ochiq aytadi.
"""
import json
import os
import threading
import time
import traceback

STATUS_FILE = "fon_holat.json"
LOG_FILE = "fon_jurnal.jsonl"
ALIVE_SECONDS = 20


# ======================= fayllar (ikkala tomon) =======================
def _dir():
    import selfupdate
    return selfupdate.data_dir()


def _path(name):
    return os.path.join(_dir(), name)


def write_status(**fields):
    try:
        data = read_status()
        data.update(fields)
        data["alive"] = time.time()
        tmp = _path(STATUS_FILE) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, _path(STATUS_FILE))
    except Exception as error:
        print("FON STATUS ERROR:", error)


def read_status():
    try:
        with open(_path(STATUS_FILE), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def is_running():
    data = read_status()
    return bool(data.get("running")) and time.time() - float(data.get("alive", 0)) < ALIVE_SECONDS


def describe():
    data = read_status()
    if not data:
        return "Fon xizmati hali ishga tushmagan."

    lines = []
    lines.append("Holat: " + ("ishlayapti" if is_running() else "to'xtagan"))
    if data.get("state"):
        lines.append("Bosqich: " + str(data["state"]))
    if data.get("heard"):
        lines.append("Oxirgi eshitgani: " + str(data["heard"])[:80])
    if data.get("error"):
        lines.append("Xato: " + str(data["error"])[:300])
    if data.get("alive"):
        lines.append("Oxirgi signal: %d soniya oldin" % (time.time() - float(data["alive"])))
    return "\n".join(lines)


def append_log(user, reply):
    try:
        with open(_path(LOG_FILE), "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.time(), "u": user, "a": reply}, ensure_ascii=False) + "\n")
    except Exception as error:
        print("FON LOG ERROR:", error)


def pop_log():
    """Ilova ochilganda: fon rejimida bo'lgan suhbatni olib, jurnalni bo'shatadi."""
    source = _path(LOG_FILE)
    taken = source + ".r"
    items = []
    try:
        if not os.path.exists(source):
            return items
        os.replace(source, taken)
        with open(taken, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    items.append(json.loads(line))
                except Exception:
                    pass
        os.remove(taken)
    except Exception as error:
        print("FON POP ERROR:", error)
    return items


# ======================= ilova tomoni =======================
SERVICE_CLASS = "org.jarvis.jarvis.ServiceJarvis"


def start_service():
    """Fon xizmatini ishga tushiradi. (True, "") yoki (False, sabab)."""
    try:
        from jnius import autoclass

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        service = autoclass(SERVICE_CLASS)

        started = False
        errors = []

        # bildirishnomali variant: (kontekst, ikonka, sarlavha, matn, argument)
        for icon in ("icon", ""):
            try:
                service.start(activity, icon, "JARVIS", "«Jarvis» deb chaqiring", "fon")
                started = True
                break
            except Exception as error:
                errors.append(repr(error)[:80])

        if not started:
            try:
                service.start(activity, "fon")
                started = True
            except Exception as error:
                errors.append(repr(error)[:80])

        if not started:
            return False, "; ".join(errors)

        write_status(running=False, state="xizmat so'raldi", error="")
        return True, ""
    except Exception as error:
        return False, repr(error)[:200]


def stop_service():
    try:
        from jnius import autoclass

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        autoclass(SERVICE_CLASS).stop(activity)
    except Exception as error:
        print("FON STOP ERROR:", error)
    write_status(running=False, state="to'xtatildi")


# ======================= xizmat tomoni =======================
class _Event:
    def __init__(self, callback, at, interval):
        self.callback = callback
        self.at = at
        self.interval = interval
        self.dead = False

    def cancel(self):
        self.dead = True


class SimpleClock:
    """Kivy Clock'ga o'xshash oddiy rejalovchi (xizmatda Kivy oynasi yo'q)."""

    def __init__(self):
        self.cv = threading.Condition()
        self.items = []
        self.stopped = False

    def now(self):
        return time.time()

    def _add(self, callback, delay, interval):
        event = _Event(callback, time.time() + float(delay), interval)
        with self.cv:
            self.items.append(event)
            self.cv.notify()
        return event

    def schedule_once(self, callback, delay=0):
        return self._add(callback, delay, None)

    def schedule_interval(self, callback, interval):
        return self._add(callback, interval, interval)

    def stop(self):
        with self.cv:
            self.stopped = True
            self.cv.notify()

    def run(self):
        while True:
            with self.cv:
                if self.stopped:
                    return
                self.items = [e for e in self.items if not e.dead]
                now = time.time()
                due = [e for e in self.items if e.at <= now]
                if not due:
                    wait = min([e.at - now for e in self.items] + [1.0])
                    self.cv.wait(timeout=max(0.01, wait))
                    continue
                event = min(due, key=lambda e: e.at)

            try:
                result = event.callback(0)
            except Exception:
                print("FON CLOCK ERROR:", traceback.format_exc())
                result = False

            if event.interval is not None and not event.dead and result is not False:
                event.at = time.time() + event.interval
            else:
                event.dead = True


NEEDS_APP = (
    "ko'nikmasida xato", "ko'nikmasida", "Traceback", "NoneType", "mActivity",
)


class HeadlessApp:
    """HandsFree dvigateli kutadigan 'ilova' vazifasini xizmat ichida bajaradi."""

    def __init__(self, engine, voice, clock):
        self.engine = engine
        self.voice = voice
        self.clock = clock
        self.busy = False
        self.hands = None
        self.stop_requested = False

    # --- HandsFree talab qiladigan usullar ---
    def process_command(self, text):
        self.busy = True
        try:
            try:
                reply = self.engine.process(text)
            except Exception as error:
                print("FON PROCESS ERROR:", error)
                reply = None

            reply = str(reply).strip() if reply else ""
            if not reply or any(marker in reply for marker in NEEDS_APP):
                reply = ("Buni ilova yopiq paytda bajara olmayman. "
                         "Ilovani oching va qayta ayting.")

            append_log(text, reply)
            write_status(heard=text, state="javob berildi")
            self.say(reply)
        finally:
            self.busy = False

    def say(self, text):
        try:
            from tts import clean_text
            spoken = clean_text(text)
        except Exception:
            spoken = str(text)

        if self.hands is not None:
            self.hands.note_spoken(spoken)
        self.voice.speak(spoken)

    def is_speaking(self):
        try:
            return bool(self.voice.is_busy())
        except Exception:
            return False

    def add_message(self, text, is_user=False, save=True):
        append_log(None, text)

    def handsfree_say(self, text):
        append_log(None, text)
        self.say(text)

    def handsfree_stopped_by_voice(self):
        self.say("Xo'p, uxlayman.")
        append_log(None, "Fon rejimi ovoz bilan o'chirildi.")
        self.shutdown()

    def handsfree_stopped_by_error(self, message):
        append_log(None, "Fon rejimi to'xtadi: " + str(message))
        write_status(error=str(message), state="xato bilan to'xtadi")
        self.shutdown()

    def shutdown(self):
        if self.stop_requested:
            return
        self.stop_requested = True

        # xizmat jarayonini ham to'xtatamiz (ovoz aytib bo'lingach)
        def finish(dt):
            try:
                if self.hands is not None:
                    self.hands.stop()
            finally:
                write_status(running=False, state="to'xtatildi")
                try:
                    from jnius import autoclass
                    autoclass("org.kivy.android.PythonService").mService.stopSelf()
                except Exception:
                    pass
                self.clock.stop()
            return False

        started = time.time()

        def wait(dt):
            # ovoz tugagach (yoki 15 soniyadan keyin) xizmatni to'xtatamiz
            if self.is_speaking() and time.time() - started < 15:
                return None
            self.clock.schedule_once(finish, 0.5)
            return False

        self.clock.schedule_interval(wait, 0.4)


def build_engine():
    from jarvis import JARVIS

    engine = JARVIS()
    engine.handsfree = True                       # o'rgatish va takliflar o'chiq
    # Xizmat fayllarga yozmaydi: ilova bilan bir-birining ustidan yozib yubormaslik uchun
    engine._memory_add = lambda *a, **k: None
    try:
        engine.mind.save = lambda *a, **k: None
    except Exception:
        pass
    return engine


def run_service(engine_factory=None, ears_factory=None, voice_factory=None, clock=None):
    clock = clock or SimpleClock()
    write_status(running=True, state="ishga tushmoqda", error="")

    try:
        engine = (engine_factory or build_engine)()

        if voice_factory is None:
            from ovoz import OwnVoice
            voice_factory = OwnVoice
        voice = voice_factory()

        from quloq import AndroidEars, HandsFree

        app = HeadlessApp(engine, voice, clock)
        ears = (ears_factory or (lambda: AndroidEars(service=True)))()
        hands = HandsFree(app, ears, clock=clock, now=time.time)
        app.hands = hands
        hands.start()

        def beat(dt):
            write_status(running=True, state=hands.state if hands.running else "to'xtagan")

        beat(0)
        clock.schedule_interval(beat, 5)
        write_status(running=True, state="tinglayapti")
        clock.run()
    except Exception:
        text = traceback.format_exc()
        print("FON SERVICE ERROR:", text)
        write_status(running=False, state="yiqildi", error=text[-400:])
