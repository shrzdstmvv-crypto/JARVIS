
import json
import os
import time
import uuid

import selfupdate

MAX_CHATS = 60
MAX_MESSAGES = 400


class ChatStore:
    """Suhbatlar ro'yxati va ularning xabarlari (telefonda saqlanadi).

    Har bir suhbat: {"id", "title", "updated", "messages": [...]}
    Xabar: {"k": "t" (matn) yoki "i" (rasm), "t": matn/yo'l, "u": foydalanuvchimi}
    """

    def __init__(self, file=None):
        self.file = file or os.path.join(selfupdate.data_dir(), "chats.json")
        self.data = {"current": None, "chats": []}
        self.load()

    # SAQLASH VA YUKLASH
    def load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            if isinstance(data.get("chats"), list):
                self.data = {
                    "current": data.get("current"),
                    "chats": [c for c in data["chats"] if c.get("id")]
                }
        except Exception:
            pass

        if self._find(self.data.get("current")) is None:
            self.data["current"] = (
                self.data["chats"][0]["id"] if self.data["chats"] else None
            )

    def save(self):
        try:
            temp = self.file + ".tmp"

            with open(temp, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, ensure_ascii=False)

            os.replace(temp, self.file)
        except Exception as error:
            print("ChatStore save error:", error)

    # QIDIRISH
    def _find(self, chat_id):
        for chat in self.data["chats"]:
            if chat["id"] == chat_id:
                return chat

        return None

    def current(self):
        chat = self._find(self.data["current"])

        if chat is None:
            chat = self.new_chat()

        return chat

    def list(self):
        """Yangi yangilanganlari birinchi: [(id, sarlavha), ...]"""
        chats = sorted(
            self.data["chats"], key=lambda c: c.get("updated", 0), reverse=True
        )
        return [(c["id"], c.get("title") or "Yangi chat") for c in chats]

    # O'ZGARTIRISH
    def new_chat(self):
        # Bo'sh suhbat bor bo'lsa, yangisini yaratmaymiz
        for chat in self.data["chats"]:
            if not chat["messages"]:
                self.data["current"] = chat["id"]
                chat["updated"] = time.time()
                self.save()
                return chat

        chat = {
            "id": uuid.uuid4().hex[:10],
            "title": "",
            "updated": time.time(),
            "messages": []
        }
        self.data["chats"].append(chat)
        self.data["chats"] = sorted(
            self.data["chats"], key=lambda c: c.get("updated", 0)
        )[-MAX_CHATS:]
        self.data["current"] = chat["id"]
        self.save()
        return chat

    def switch(self, chat_id):
        if self._find(chat_id) is not None:
            self.data["current"] = chat_id
            self.save()

    def add(self, kind, text, is_user):
        chat = self.current()
        chat["messages"].append({"k": kind, "t": str(text), "u": bool(is_user)})
        chat["messages"] = chat["messages"][-MAX_MESSAGES:]
        chat["updated"] = time.time()

        if is_user and kind == "t" and not chat["title"]:
            line = str(text).strip().splitlines()[0] if str(text).strip() else ""
            chat["title"] = line[:30] + ("..." if len(line) > 30 else "")

        self.save()

    def delete(self, chat_id):
        chat = self._find(chat_id)

        if chat is None:
            return

        self.data["chats"].remove(chat)

        if self.data["current"] == chat_id:
            self.data["current"] = (
                self.list()[0][0] if self.data["chats"] else None
            )

        self.save()

    def rename(self, chat_id, title):
        chat = self._find(chat_id)

        if chat is not None and str(title).strip():
            chat["title"] = str(title).strip()[:40]
            self.save()
