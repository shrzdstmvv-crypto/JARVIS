import json
import os
from datetime import datetime


class Memory:

    def __init__(self):
        self.file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "jarvis_memory.json"
        )

        self.data = []
        self.load()

    def load(self):
        if not os.path.exists(self.file):
            self.data = []
            return True

        try:
            with open(self.file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                self.data = []
                return False

            self.data = []

            for item in raw_data:
                if not isinstance(item, dict):
                    continue

                role = item.get("role", "unknown")

                message = item.get("message")

                if message is None:
                    message = item.get("text")

                if message is None:
                    continue

                role = str(role).strip().lower()

                if role == "jarvis":
                    role = "assistant"

                if role not in {
                    "user",
                    "assistant",
                    "system",
                    "unknown"
                }:
                    role = "unknown"

                timestamp = item.get("time")

                if not timestamp:
                    timestamp = datetime.now().isoformat(
                        timespec="seconds"
                    )

                self.data.append({
                    "role": role,
                    "message": str(message),
                    "time": str(timestamp)
                })

            return True

        except Exception as error:
            print("Memory load error:", error)
            self.data = []
            return False

    def save(self):
        try:
            directory = os.path.dirname(self.file)

            if directory:
                os.makedirs(directory, exist_ok=True)

            temporary_file = self.file + ".tmp"

            with open(
                temporary_file,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    self.data,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            os.replace(
                temporary_file,
                self.file
            )

            return True

        except Exception as error:
            print("Memory save error:", error)

            try:
                temporary_file = self.file + ".tmp"

                if os.path.exists(temporary_file):
                    os.remove(temporary_file)
            except Exception:
                pass

            return False

    def add(self, role, message):
        if message is None:
            return False

        message = str(message).strip()

        if not message:
            return False

        role = str(role).strip().lower()

        if role == "jarvis":
            role = "assistant"

        if role not in {
            "user",
            "assistant",
            "system",
            "unknown"
        }:
            role = "unknown"

        self.data.append({
            "role": role,
            "message": message,
            "time": datetime.now().isoformat(
                timespec="seconds"
            )
        })

        return self.save()

    def history(self, limit=None):
        if limit is None:
            return list(self.data)

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return list(self.data)

        if limit <= 0:
            return []

        return list(self.data[-limit:])

    def last(self):
        if not self.data:
            return None

        return dict(self.data[-1])

    def last_user_message(self):
        for item in reversed(self.data):
            if item.get("role") == "user":
                return dict(item)

        return None

    def last_assistant_message(self):
        for item in reversed(self.data):
            if item.get("role") == "assistant":
                return dict(item)

        return None

    def search(self, query, limit=10):
        if query is None:
            return []

        query = str(query).strip().lower()

        if not query:
            return []

        results = []

        for item in reversed(self.data):
            message = str(
                item.get("message", "")
            ).lower()

            if query in message:
                results.append(dict(item))

                if len(results) >= limit:
                    break

        return results

    def recent_context(self, limit=10):
        context = []

        for item in self.history(limit):
            role = item.get("role", "unknown")
            message = item.get("message", "")

            if not message:
                continue

            context.append({
                "role": role,
                "message": message
            })

        return context

    def count(self):
        return len(self.data)

    def count_by_role(self, role):
        role = str(role).strip().lower()

        if role == "jarvis":
            role = "assistant"

        return sum(
            1
            for item in self.data
            if item.get("role") == role
        )

    def clear(self):
        self.data = []
        return self.save()

    def delete_last(self):
        if not self.data:
            return False

        self.data.pop()
        return self.save()

    def export_data(self):
        return list(self.data)

    def info(self):
        return {
            "total": self.count(),
            "user": self.count_by_role("user"),
            "assistant": self.count_by_role("assistant"),
            "system": self.count_by_role("system"),
            "file": self.file
        }


if __name__ == "__main__":
    memory = Memory()

    print("JARVIS MEMORY")
    print("=" * 40)
    print("Total:", memory.count())
    print("User:", memory.count_by_role("user"))
    print("Assistant:", memory.count_by_role("assistant"))