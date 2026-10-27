
import ast
import contextlib
import fnmatch
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import traceback
import urllib.request

import selfupdate

SHELL_WORDS = {
    "ls", "cd", "pwd", "cat", "mkdir", "rm", "cp", "mv", "echo", "ps",
    "df", "du", "date", "whoami", "id", "uname", "env", "head", "tail",
    "wc", "grep", "find", "touch", "chmod", "stat", "sleep", "top",
    "ping", "getprop", "ip", "ifconfig", "netstat", "free", "uptime",
    "which", "tree", "sort", "uniq", "tr", "cut", "sed", "awk"
}

# Python kodga o'xshash qatorlar: x = 1, ls(), ls.x, ls[0]
PYTHON_LIKE = re.compile(r"^\w+(\s*=(?!=)|\(|\.\w|\[)")

MAX_OUTPUT = 60000

HELP_TEXT = """JARVIS TERMINAL
Python kod yozing yoki !buyruq bilan shell ishlating
(ls, cat, cp, mv, rm, ps, ping... kabi oddiy buyruqlar !siz ham ishlaydi).
Yuqoriga/pastga tugmalari oldingi buyruqlarni qaytaradi.

FAYLLAR
  pwd()  cd(yo'l)  ls(yo'l)  tree(yo'l)  cat(fayl)  write(fayl, matn)
  find("*.py")  grep("matn")  cp(a, b)  mv(a, b)  rm(yo'l)  mkdir(yo'l)
  run("skript.py")    Python faylni ishga tushirish
  sh(buyruq)  get(url)

TAHRIRLASH (o'zgarishlar telefonda saqlanadi, yangilanishda yo'qolmaydi)
  edit("jarvis")          modulni tahrirlash oynasiga yuklash
  edit("/yo'l/fayl.txt")  istalgan faylni tahrirlash (yangisini ham yaratadi)
  Saqlash tugmasi saqlaydi va o'zi qo'llaydi: oddiy modul darhol qayta
  yuklanadi, ekran modullari uchun ilova o'zi qayta ochiladi.
  auto(False)             o'zi qo'llashni o'chirish, auto(True) yoqish

O'ZGARTIRISH
  files()   show("jarvis")   patch("jarvis", "eski", "yangi")
  save("modul", kod)   revert("jarvis")   diff("jarvis")
  take_new("jarvis")   yangi build'dagi versiyani olish
  overlay()  reset_all()  reload()  restart()
  Yangi build chiqqanda sizning o'zgartirishlaringiz yangisi bilan
  avtomatik birlashtiriladi. To'qnashsa, sizniki saqlanadi.

KO'NIKMALAR (yangi buyruqlar)
  skills()  skill("nom", kod)  edit_skill("nom")  rm_skill("nom")

KO'RINISH VA MA'LUMOT
  kb()  kb("resize")      klaviatura rejimi
  ui("classic")  ui("new")   ko'rinishni tanlash
  info()  paths()  history()

Oddiy nomlarni qavssiz ham yozsa bo'ladi: help, files, skills, info
"""


class Command:
    """Qavssiz yozilganda ham ishlaydigan yordamchi (masalan: files)."""

    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def __repr__(self):
        return "<buyruq>"


class Terminal:

    def __init__(self, app=None, engine=None):
        self.app = app
        self.engine = engine
        self.cwd = selfupdate.data_dir()
        self.pending_edit = None
        self.history = self._load_history()
        self.history_pos = None
        self.ns = {"__name__": "__terminal__"}
        self._build_namespace()

    def set_engine(self, engine):
        self.engine = engine
        self.ns["jarvis"] = engine

    # ASOSIY ISHGA TUSHIRISH
    def execute(self, text, timeout=25):
        text = str(text).rstrip()

        if not text.strip():
            return ""

        self._remember(text)
        result = {}

        def work():
            try:
                result["out"] = self._dispatch(text)
            except BaseException as error:
                result["out"] = "Xatolik: " + repr(error)

        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            return (
                "[" + str(timeout) + " soniyada tugamadi. "
                "Kod fonda davom etadi.]"
            )

        output = result.get("out", "")

        if len(output) > MAX_OUTPUT:
            output = output[:MAX_OUTPUT] + "\n[... natija qisqartirildi]"

        return output

    def check_syntax(self, code):
        try:
            compile(str(code), "<tahrir>", "exec")
            return "Sintaksis to'g'ri."
        except SyntaxError as error:
            return "Sintaksis xatosi: qator %s: %s" % (
                error.lineno, error.msg
            )

    def _dispatch(self, text):
        stripped = text.strip()

        if stripped.startswith("!"):
            return self._shell(stripped[1:].strip())

        if self._looks_like_shell(stripped):
            return self._shell(stripped)

        return self._python(text)

    def _looks_like_shell(self, line):
        if "\n" in line:
            return False

        first = line.split()[0] if line.split() else ""

        return first in SHELL_WORDS and not PYTHON_LIKE.match(line)

    # PYTHON
    def _python(self, code):
        buffer = io.StringIO()

        with contextlib.redirect_stdout(buffer), \
                contextlib.redirect_stderr(buffer):
            try:
                value = self._run_code(code)

                if isinstance(value, Command):
                    value = value()

                if value is not None:
                    print(value if isinstance(value, str) else repr(value))

            except SystemExit:
                print("exit() bu yerda ishlamaydi.")
            except BaseException as error:
                # Terminalning ichki qatorlarini ko'rsatmaymiz
                tb = sys.exc_info()[2]

                # Terminal va tizim modullarining ichki qatorlarini yashiramiz
                frames = [
                    f for f in traceback.extract_tb(tb)
                    if not f.filename.endswith(
                        ("terminal.py", "selfupdate.py", "skills.py")
                    )
                ]
                lines = traceback.format_list(frames[-4:])
                lines += traceback.format_exception_only(type(error), error)
                print("".join(lines).rstrip()[-1500:])

        return buffer.getvalue().rstrip("\n")

    def _run_code(self, code):
        """Oxirgi qator ifoda bo'lsa, natijasini qaytaradi (REPL kabi)."""
        tree = ast.parse(code, "<terminal>", "exec")

        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last = ast.Expression(tree.body.pop().value)
            exec(compile(tree, "<terminal>", "exec"), self.ns)
            return eval(compile(last, "<terminal>", "eval"), self.ns)

        exec(compile(tree, "<terminal>", "exec"), self.ns)
        return None

    # SHELL
    def _shell(self, command, timeout=30):
        command = command.strip()

        if not command:
            return ""

        parts = command.split(None, 1)

        if parts[0] == "cd":
            target = parts[1].strip() if len(parts) > 1 else selfupdate.data_dir()
            return self._cd(target)

        env = dict(os.environ)
        env["PATH"] = "/system/bin:/system/xbin:" + env.get("PATH", "")
        shell = "/system/bin/sh" if os.path.exists("/system/bin/sh") else "/bin/sh"

        try:
            process = subprocess.run(
                [shell, "-c", command],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
        except subprocess.TimeoutExpired:
            return "[" + str(timeout) + " soniyada tugamadi, to'xtatildi.]"
        except Exception as error:
            return "Shell xatosi: " + repr(error)

        output = (process.stdout or "") + (process.stderr or "")
        output = output.rstrip("\n")

        if process.returncode != 0:
            output += "\n[chiqish kodi: " + str(process.returncode) + "]"

        return output.strip("\n")

    def _cd(self, target):
        target = os.path.expanduser(target.strip().strip("'\""))
        path = os.path.normpath(os.path.join(self.cwd, target))

        if not os.path.isdir(path):
            return "Papka topilmadi: " + path

        self.cwd = path
        return self.cwd

    # YORDAMCHI FUNKSIYALAR (Python rejimida ishlatiladi)
    def _build_namespace(self):
        terminal = self

        def help_():
            print(HELP_TEXT)

        def pwd():
            print(terminal.cwd)

        def cd(path=None):
            print(terminal._cd(path or selfupdate.data_dir()))

        def ls(path="."):
            full = os.path.join(terminal.cwd, os.path.expanduser(str(path)))

            for name in sorted(os.listdir(full)):
                mark = "/" if os.path.isdir(os.path.join(full, name)) else ""
                print(name + mark)

        def cat(path):
            full = os.path.join(terminal.cwd, os.path.expanduser(str(path)))

            with open(full, "r", encoding="utf-8", errors="replace") as file:
                print(file.read())

        def write(path, text):
            full = os.path.join(terminal.cwd, os.path.expanduser(str(path)))

            with open(full, "w", encoding="utf-8") as file:
                file.write(str(text))

            print(full + " yozildi (" + str(len(str(text))) + " belgi)")

        def sh(command):
            print(terminal._shell(str(command)))

        def get(url):
            import netutil
            return netutil.fetch(url, 20).decode("utf-8", errors="replace")

        def files():
            print("Modullar: " + ", ".join(selfupdate.modules()))
            print(selfupdate.status())

        def show(name):
            print(selfupdate.source(name))

        def edit(target):
            kind, name, text = terminal._edit_target(target)
            terminal.pending_edit = (kind, name, text)

            shown = name + (".py" if kind == "module" else "")
            print(
                shown + " tahrirlash oynasiga yuklandi. O'zgartirib, "
                "«Saqlash» ni bosing" + (
                    " (avtomatik qo'llanadi)."
                    if selfupdate.get_setting("auto_apply", True) else "."
                )
            )

        def save(name, code):
            print(selfupdate.save(name, code))

        def patch(name, old, new):
            print(selfupdate.patch(name, old, new))

        def revert(name):
            print(selfupdate.revert(name))

        def overlay():
            print(selfupdate.status())
            error = selfupdate.last_error()

            if error:
                print("Oxirgi muammo: " + error)

        def reset_all():
            print(selfupdate.reset_all())

        def reload():
            print(terminal.reload_engine())

        def kb(mode=None):
            if terminal.app is None or not hasattr(
                terminal.app, "set_keyboard_mode"
            ):
                print("Bu faqat ilovada ishlaydi.")
                return

            if mode is None:
                print(terminal.app.keyboard_mode_info())
            else:
                print(terminal.app.set_keyboard_mode(mode))

        def skills():
            manager = terminal._skills()
            names = manager.names() if manager else []
            print("Ko'nikmalar: " + (", ".join(names) or "yo'q"))

            if manager and manager.errors:
                for key, value in manager.errors.items():
                    print("  xato " + key + ": " + value)

        def skill(name, code):
            print(terminal._skills().save(name, code))

        def tree(path=".", depth=2):
            root = terminal._abs(path)

            def walk(folder, level):
                try:
                    names = sorted(os.listdir(folder))
                except Exception as error:
                    print("  " * level + "[" + str(error) + "]")
                    return

                for name in names:
                    full = os.path.join(folder, name)
                    is_dir = os.path.isdir(full)
                    print("  " * level + name + ("/" if is_dir else ""))

                    if is_dir and level + 1 < int(depth):
                        walk(full, level + 1)

            print(root)
            walk(root, 0)

        def find(pattern, path="."):
            root = terminal._abs(path)
            count = 0

            for folder, dirs, names in os.walk(root):
                for name in dirs + names:
                    if fnmatch.fnmatch(name, str(pattern)) or str(pattern) in name:
                        print(os.path.join(folder, name))
                        count += 1

                        if count >= 300:
                            print("[300 ta natija bilan to'xtadi]")
                            return

            if not count:
                print("Topilmadi.")

        def grep(text, path="."):
            root = terminal._abs(path)
            count = 0
            files_ = [root] if os.path.isfile(root) else [
                os.path.join(f, n)
                for f, _, ns in os.walk(root) for n in ns
            ]

            for full in files_:
                try:
                    if os.path.getsize(full) > 500000:
                        continue

                    with open(full, "r", encoding="utf-8", errors="strict") as fh:
                        for number, line in enumerate(fh, 1):
                            if str(text) in line:
                                print("%s:%d: %s" % (full, number, line.rstrip()[:160]))
                                count += 1

                                if count >= 100:
                                    print("[100 ta natija bilan to'xtadi]")
                                    return
                except Exception:
                    continue

            if not count:
                print("Topilmadi.")

        def cp(src, dst):
            a, b = terminal._abs(src), terminal._abs(dst)

            if os.path.isdir(a):
                shutil.copytree(a, b)
            else:
                shutil.copy2(a, b)

            print("Nusxalandi: " + b)

        def mv(src, dst):
            b = terminal._abs(dst)
            shutil.move(terminal._abs(src), b)
            print("Ko'chirildi: " + b)

        def rm(path, recursive=False):
            full = terminal._abs(path)
            guarded = {
                os.path.abspath(selfupdate.data_dir()),
                os.path.abspath(selfupdate.BASE_DIR), os.sep
            }

            if os.path.abspath(full) in guarded:
                print("Bu papkani o'chirib bo'lmaydi.")
                return

            if os.path.isdir(full):
                if not recursive:
                    print("Bu papka. O'chirish uchun: rm(\"" + str(path) + "\", True)")
                    return

                shutil.rmtree(full)
            else:
                os.remove(full)

            print("O'chirildi: " + full)

        def mkdir(path):
            full = terminal._abs(path)
            os.makedirs(full, exist_ok=True)
            print("Papka: " + full)

        def run_(path):
            full = terminal._abs(path)

            with open(full, "r", encoding="utf-8") as fh:
                code = fh.read()

            exec(compile(code, full, "exec"), terminal.ns)

        def paths():
            print("Ilova kodi : " + selfupdate.BASE_DIR)
            print("Ma'lumotlar: " + selfupdate.data_dir())
            print("O'zgartirishlar: " + selfupdate.overlay_dir())
            print("Ko'nikmalar: " + selfupdate.skills_dir())

        def info():
            import platform

            usage = shutil.disk_usage(selfupdate.data_dir())
            print("Python    : " + platform.python_version())
            print("Tizim     : " + platform.platform())
            print("Bo'sh joy : %.1f GB" % (usage.free / 1e9))
            print("Ko'rinish : " + selfupdate.UI_BUILD
                  + (" (klassik)" if selfupdate.USE_CLASSIC else ""))
            print("Avto qo'llash: " + str(selfupdate.get_setting("auto_apply", True)))
            print(selfupdate.status())

        def history():
            for number, line in enumerate(terminal.history[-30:], 1):
                print(str(number) + "  " + line.replace("\n", " ⏎ ")[:120])

        def auto(on=True):
            selfupdate.set_setting("auto_apply", bool(on))
            print("Avtomatik qo'llash: " + ("yoqildi" if on else "o'chirildi"))

        def restart():
            print(terminal._schedule_restart())

        def ui(mode="new"):
            print(selfupdate.set_ui(mode))

        def diff(name):
            print(selfupdate.diff(name))

        def take_new(name):
            print(selfupdate.take_new(name))

        def edit_skill(name):
            manager = terminal._skills()
            terminal.pending_edit = ("skill", name, manager.source(name))
            print(
                "«" + name + "» ko'nikmasi tahrirlash oynasiga yuklandi. "
                "«Saqlash» ni bosing."
            )

        def rm_skill(name):
            print(terminal._skills().remove(name))

        helpers = {
            "help": help_, "pwd": pwd, "cd": cd, "ls": ls, "cat": cat,
            "write": write, "sh": sh, "get": get, "files": files,
            "show": show, "edit": edit, "save": save, "patch": patch,
            "revert": revert, "overlay": overlay, "reset_all": reset_all,
            "reload": reload, "skills": skills, "skill": skill, "kb": kb,
            "edit_skill": edit_skill, "rm_skill": rm_skill,
            "tree": tree, "find": find, "grep": grep, "cp": cp, "mv": mv,
            "rm": rm, "mkdir": mkdir, "run": run_, "paths": paths,
            "info": info, "history": history, "auto": auto,
            "restart": restart, "ui": ui, "diff": diff, "take_new": take_new
        }

        no_args = {
            "help", "pwd", "files", "overlay", "reload", "skills",
            "paths", "info", "history", "restart"
        }

        for key, function in helpers.items():
            self.ns[key] = Command(function) if key in no_args else function

        self.ns["app"] = self.app
        self.ns["jarvis"] = self.engine
        self.ns["terminal"] = self

    def _skills(self):
        return getattr(self.engine, "skills", None)

    # TAHRIRLASH MAQSADI VA SAQLASH
    def _abs(self, path):
        return os.path.normpath(
            os.path.join(self.cwd, os.path.expanduser(str(path)))
        )

    def _edit_target(self, target):
        """Modul nomi yoki fayl yo'lini (kind, name, text) ga aylantiradi."""
        text = str(target).strip()
        name = text[:-3] if text.endswith(".py") else text

        if re.fullmatch(r"\w+", name):
            if name in selfupdate.PROTECTED:
                raise ValueError(
                    name + " himoyalangan modul: uni o'zgartirib bo'lmaydi "
                    "(tiklash vositasi)."
                )

            try:
                return "module", name, selfupdate.source(name)
            except FileNotFoundError:
                manager = self._skills()

                if manager is not None and name in manager._files():
                    return "skill", name, manager.source(name)

                if not os.path.exists(self._abs(text)):
                    raise FileNotFoundError(
                        "«" + text + "» nomli modul, ko'nikma yoki fayl topilmadi."
                    )

        path = self._abs(text)

        # Ilova kodi papkasidagi .py fayl modul sifatida saqlanadi
        if os.path.dirname(path) == selfupdate.BASE_DIR and path.endswith(".py"):
            name = os.path.basename(path)[:-3]

            if name in selfupdate.PROTECTED:
                raise ValueError(name + " himoyalangan modul.")

            return "module", name, selfupdate.source(name)

        if os.path.exists(path) and os.path.getsize(path) > 300000:
            raise ValueError("Fayl juda katta (300 KB dan oshiq).")

        content = ""

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()

        return "file", path, content

    def _save_file(self, path, code):
        folder = os.path.dirname(path)

        if folder:
            os.makedirs(folder, exist_ok=True)

        if os.path.exists(path):
            shutil.copyfile(path, path + ".bak")

        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(code))

        return "Saqlandi: " + path + " (" + str(len(str(code))) + " belgi)"

    def _schedule_restart(self):
        threading.Timer(1.5, selfupdate.restart_app).start()
        return "Ilova 2 soniyadan keyin qayta ishga tushadi..."

    def apply(self, name):
        """Saqlangan modulni kuchga kiritadi (yuklash yoki qayta ochish)."""
        if selfupdate.apply_hint(name) == "reload":
            return self.reload_engine()

        return self._schedule_restart()

    def save_edit(self, kind, name, code):
        try:
            if kind == "skill":
                return self._skills().save(name, code)

            if kind == "file":
                return self._save_file(name, code)

            message = selfupdate.save(name, code)

            if selfupdate.get_setting("auto_apply", True):
                message += "\n" + self.apply(name)

            return message

        except Exception as error:
            return "Saqlab bo'lmadi: " + str(error)

    # BUYRUQLAR TARIXI
    def _history_file(self):
        return os.path.join(selfupdate.data_dir(), "terminal_history.json")

    def _load_history(self):
        try:
            with open(self._history_file(), "r", encoding="utf-8") as fh:
                data = json.load(fh)

            return [str(x) for x in data][-100:]
        except Exception:
            return []

    def _remember(self, text):
        self.history_pos = None

        if self.history and self.history[-1] == text:
            return

        self.history.append(text)
        self.history = self.history[-100:]

        try:
            selfupdate._write(
                self._history_file(),
                json.dumps(self.history, ensure_ascii=False)
            )
        except Exception:
            pass

    def history_step(self, direction):
        """Yuqoriga (-1) yoki pastga (+1) yurish. Matnni qaytaradi."""
        if not self.history:
            return None

        if self.history_pos is None:
            self.history_pos = len(self.history)

        self.history_pos = max(
            0, min(len(self.history), self.history_pos + direction)
        )

        if self.history_pos >= len(self.history):
            return ""

        return self.history[self.history_pos]

    # QAYTA YUKLASH
    def reload_engine(self):
        if self.app is not None and hasattr(self.app, "reload_engine"):
            return self.app.reload_engine()

        importlib.invalidate_caches()

        for name in (
            "language_brain", "learning", "images_store",
            "memory", "skills", "jarvis"
        ):
            module = sys.modules.get(name)

            if module is not None:
                importlib.reload(module)

        import jarvis as jarvis_module
        self.set_engine(jarvis_module.JARVIS())
        return "Jarvis qayta yuklandi."
