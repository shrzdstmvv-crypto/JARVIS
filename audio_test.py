from kivy.app import App
from kivy.uix.button import Button
from plyer import audio


class AudioTestApp(App):

    def build(self):
        button = Button(text="🎙️ AUDIO TEST")
        button.bind(on_press=self.start_recording)
        return button

    def start_recording(self, instance):
        print("🎙️ Mikrofon testi boshlandi")

        try:
            audio.start()
            print("✅ Audio recording ishga tushdi")
        except Exception as e:
            print("❌ Audio xatosi:", e)


if __name__ == "__main__":
    AudioTestApp().run()