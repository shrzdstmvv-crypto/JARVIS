
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

        TRIGGERS = ["soat nechi", "eslatma qo'y*"]   # * - gap shu bilan boshlansa

        def run(text, jarvis):
            return "javob matni"
    """

    def __init__(self, engine):
        self.engine = engine
        self.skills = []
        self.errors = {}
        self.load()

    def load(self):
        self.skills = []
        self.errors = {}
        folder = selfupdate.skills_dir()

        for file in sorted(os.listdir(folder)):
            if not file.endswith(".py"):
                continue

            name = file[:-3]

            try:
                spec = importlib.util.spec_from_file_location(
                    "jarvis_skill_" + name,
                    os.path.join(folder, file)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                triggers = [
                    self.engine.brain.normalize(t.rstrip("*")) + (
                        "*" if t.endswith("*") else ""
                    )
                    for t in getattr(module, "TRIGGERS", [])
                    if str(t).strip()
                ]

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
                if trigger.endswith("*"):
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

        return "" if result is None else str(result)

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
        path = os.path.join(selfupdate.skills_dir(), name + ".py")

        if not os.path.exists(path):
            return SKILL_TEMPLATE

        with open(path, "r", encoding="utf-8") as file:
            return file.read()
