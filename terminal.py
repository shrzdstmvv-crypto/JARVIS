
import ast
import contextlib
import importlib
import io
import os
import re
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

FAYLLAR
  pwd()  cd(yo'l)  ls(yo'l)  cat(fayl)  write(fayl, matn)  sh(buyruq)
  get(url)            internetdan matn olish

O'Z-O'ZINI O'ZGARTIRISH
  files()             o'zgartirsa bo'ladigan modullar
  show("jarvis")      modul kodini ko'rish
  edit("jarvis")      kodni tahrirlash oynasiga yuklash, so'ng Saqlash
  patch("jarvis", "eski matn", "yangi matn")
  save("modul", kod)  modulni to'liq yozish
  revert("jarvis")    asl holiga qaytarish
  overlay()           nimalar o'zgartirilgan
  reset_all()         hamma o'zgartirishni o'chirish
  reload()            Jarvis'ni qayta yuklash (ilovasiz)

KO'NIKMALAR (yangi buyruqlar)
  skills()  skill("nom", kod)  edit_skill("nom")  rm_skill("nom")

Oddiy nomlarni qavssiz ham yozsa bo'ladi: help, files, skills
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

                # <terminal> qatoridan boshlab ko'rsatamiz
                node = tb
                while node is not None and (
                    node.tb_frame.f_code.co_filename != "<terminal>"
                ):
                    node = node.tb_next

                tb = node
                lines = traceback.format_exception(type(error), error, tb)
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
            request = urllib.request.Request(
                str(url), headers={"User-Agent": "JARVIS"}
            )

            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")

        def files():
            print("Modullar: " + ", ".join(selfupdate.modules()))
            print(selfupdate.status())

        def show(name):
            print(selfupdate.source(name))

        def edit(name):
            terminal.pending_edit = ("module", name, selfupdate.source(name))
            print(
                name + ".py tahrirlash oynasiga yuklandi. "
                "O'zgartirib, «Saqlash» ni bosing."
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

        def skills():
            manager = terminal._skills()
            names = manager.names() if manager else []
            print("Ko'nikmalar: " + (", ".join(names) or "yo'q"))

            if manager and manager.errors:
                for key, value in manager.errors.items():
                    print("  xato " + key + ": " + value)

        def skill(name, code):
            print(terminal._skills().save(name, code))

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
            "reload": reload, "skills": skills, "skill": skill,
            "edit_skill": edit_skill, "rm_skill": rm_skill
        }

        no_args = {
            "help", "pwd", "files", "overlay", "reload", "skills"
        }

        for key, function in helpers.items():
            self.ns[key] = Command(function) if key in no_args else function

        self.ns["app"] = self.app
        self.ns["jarvis"] = self.engine
        self.ns["terminal"] = self

    def _skills(self):
        return getattr(self.engine, "skills", None)

    # SAQLASH (tahrirlash oynasidan)
    def save_edit(self, kind, name, code):
        try:
            if kind == "skill":
                return self._skills().save(name, code)

            return selfupdate.save(name, code)
        except Exception as error:
            return "Saqlab bo'lmadi: " + str(error)

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
