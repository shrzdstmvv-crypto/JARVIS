class SpeechToText:
    def __init__(self):
        self.text = ""

    def process(self, text):
        self.text = text.strip()
        return self.text

    def get_text(self):
        return self.text


if __name__ == "__main__":
    stt = SpeechToText()

    print("JARVIS STT System")
    print("Test uchun matn kiriting.")

    while True:
        text = input("🎙️ Siz: ")

        if text.lower() == "exit":
            break

        result = stt.process(text)
        print("🧠 STT:", result)