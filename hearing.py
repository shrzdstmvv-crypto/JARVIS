class Hearing:
    def __init__(self):
        self.last_text = ""

    def receive_text(self, text):
        self.last_text = text
        return text

    def get_last_text(self):
        return self.last_text


if __name__ == "__main__":
    hearing = Hearing()

    print("JARVIS Hearing System")
    print("Matn kiriting. Chiqish uchun: exit")

    while True:
        text = input("Siz: ")

        if text.lower() == "exit":
            break

        result = hearing.receive_text(text)
        print("JARVIS eshitdi:", result)