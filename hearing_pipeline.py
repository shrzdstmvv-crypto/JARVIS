from hearing import Hearing
from stt import SpeechToText


class HearingPipeline:

    def __init__(self):
        self.hearing = Hearing()
        self.stt = SpeechToText()

    def process(self, text):
        # STT
        text = self.stt.process(text)

        # Hearing
        text = self.hearing.receive_text(text)

        return text


if __name__ == "__main__":

    pipeline = HearingPipeline()

    print("???️ JARVIS HEARING PIPELINE")
    print("Chiqish uchun: exit")
    print()

    while True:

        text = input("???️ Siz: ")

        if text.lower() == "exit":
            break

        result = pipeline.process(text)

        print("??? JARVIS qabul qildi:", result)
