import json
import os
from datetime import datetime


class Memory:

    def __init__(self):

        self.file = os.path.join(
            os.path.dirname(__file__),
            "jarvis_memory.json"
        )

        self.data = []

        self.load()

    # ======================================================
    # LOAD
    # ======================================================

    def load(self):

        if not os.path.exists(self.file):

            self.data = []

            return

        try:

            with open(
                self.file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

                if isinstance(data, list):

                    self.data = data

                else:

                    self.data = []

        except Exception as error:

            print(
                "⚠️ Memory yuklanmadi:",
                error
            )

            self.data = []

    # ======================================================
    # SAVE
    # ======================================================

    def save(self):

        try:

            with open(
                self.file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    self.data,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            return True

        except Exception as error:

            print(
                "❌ Memory saqlanmadi:",
                error
            )

            return False

    # ======================================================
    # ADD
    # ======================================================

    def add(
        self,
        role,
        message
    ):

        if not message:
            return

        item = {

            "role": str(role),

            "message": str(message),

            "time": datetime.now().isoformat(
                timespec="seconds"
            )
        }

        self.data.append(
            item
        )

        self.save()

    # ======================================================
    # HISTORY
    # ======================================================

    def history(
        self,
        limit=None
    ):

        if limit is None:

            return list(
                self.data
            )

        return list(
            self.data[-limit:]
        )

    # ======================================================
    # LAST
    # ======================================================

    def last(self):

        if not self.data:

            return None

        return self.data[-1]

    # ======================================================
    # CLEAR
    # ======================================================

    def clear(self):

        self.data = []

        self.save()

    # ======================================================
    # COUNT
    # ======================================================

    def count(self):

        return len(
            self.data
        )


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 40)
    print("🧠 JARVIS MEMORY")
    print("=" * 40)

    memory = Memory()

    memory.add(
        "user",
        "salom"
    )

    memory.add(
        "jarvis",
        "Salom! Men JARVIS."
    )

    print()
    print(
        "Xotira:",
        memory.history()
    )

    print()
    print(
        "Soni:",
        memory.count()
    )