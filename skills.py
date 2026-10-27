
import importlib.util
import os
import re
import traceback

import selfupdate

SKILL_TEMPLATE = '''TRIGGERS = ["salom dunyo"]


def run(text, jarvis):
    return "Salom!"
'''


class SkillManager:
    """Foydalanuvchi yozgan ko'nikmalar (skills).

    Har bir ko'nikma skills papkasidagi alohida .py fayl:

        TRIGGERS = ["soat nechi", "eslatma qo'y*", "re:\\bsuv\\b"]
        # * - gap shu bilan boshlansa;  re: - oddiy ibora (regex)

        def run(text, jarvis):
            return "javob matni"
    """

    def __init__(self, engine):
        self.engine = engine
        self.skills = []
        self.errors = {}
        self.load()

    def _folders(self):
        # Avval ilova ichidagi tayyor ko'nikmalar, keyin foydalanuvchiniki
        # (bir xil nomli bo'lsa, foydalanuvchiniki ustun turadi)
        builtin = os.path.join(selfupdate.BASE_DIR, "skills_builtin")
        return [builtin, selfupdate.skills_dir()]

    def _files(self):
        files = {}

        for folder in self._folders():
            if not os.path.isdir(folder):
                continue

            for file in sorted(os.listdir(folder)):
                if file.endswith(".py"):
                    files[file[:-3]] = os.path.join(folder, file)

        return files

    def load(self):
        self.skills = []
        self.errors = {}

        for name, path in sorted(self._files().items()):
            file = name + ".py"
            folder = os.path.dirname(path)

            try:
                spec = importlib.util.spec_from_file_location(
                    "jarvis_skill_" + name,
                    os.path.join(folder, file)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                triggers = []

                for t in getattr(module, "TRIGGERS", []):
                    t = str(t).strip()

                    if not t:
                        continue

                    if t.startswith("re:"):
                        triggers.append(t)  # regex: o'zgartirmaymiz
                    else:
                        triggers.append(
                            self.engine.brain.normalize(t.rstrip("*"))
                            + ("*" if t.endswith("*") else "")
                        )

                if not triggers or not callable(getattr(module, "run", None)):
                    raise ValueError("TRIGGERS va run(text, jarvis) kerak")

                self.skills.append({
                    "name": name,
                    "triggers": triggers,
                    "run": module.run
                })

            except Exception as error:
                self.errors[name] = repr(error)[:200]

        return len(self.skills)

    def match(self, normalized):
        if not normalized:
            return None

        for skill in self.skills:
            for trigger in skill["triggers"]:
                if trigger.startswith("re:"):
                    try:
                        if re.search(trigger[3:], normalized):
                            return skill
                    except re.error:
                        pass

                elif trigger.endswith("*"):
                    prefix = trigger[:-1].strip()

                    if prefix and (
                        normalized == prefix
                        or normalized.startswith(prefix + " ")
                    ):
                        return skill

                elif normalized == trigger:
                    return skill

                elif len(trigger.split()) >= 2 and re.search(
                    r"(?<!\S)" + re.escape(trigger) + r"(?!\S)",
                    normalized
                ):
                    return skill

        return None

    def run(self, skill, text):
        try:
            result = skill["run"](text, self.engine)
        except Exception:
            last = traceback.format_exc().strip().splitlines()[-1]
            return "«" + skill["name"] + "» ko'nikmasida xato: " + last

        # None - ko'nikma bu gapni o'ziniki deb hisoblamadi: boshqa buyruqlarga o'tiladi
        return None if result is None else str(result)

    def names(self):
        return [s["name"] for s in self.skills]

    def save(self, name, code):
        name = selfupdate._valid_name(name)
        compile(str(code), name + ".py", "exec")

        path = os.path.join(selfupdate.skills_dir(), name + ".py")
        selfupdate._write(path, str(code))
        count = self.load()

        if name in self.errors:
            return (
                name + " saqlandi, lekin ishlamadi: " + self.errors[name]
            )

        return name + " ko'nikmasi saqlandi (jami: " + str(count) + ")."

    def remove(self, name):
        name = selfupdate._valid_name(name)
        path = os.path.join(selfupdate.skills_dir(), name + ".py")

        if not os.path.exists(path):
            return name + " ko'nikmasi topilmadi."

        os.remove(path)
        self.load()
        return name + " ko'nikmasi o'chirildi."

    def source(self, name):
        name = selfupdate._valid_name(name)
        path = self._files().get(name)

        if path is None:
            return SKILL_TEMPLATE

        with open(path, "r", encoding="utf-8") as file:
            return file.read()
