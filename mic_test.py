from kivy.app import App
from kivy.uix.button import Button


class MicTestApp(App):
    def build(self):
        button = Button(text="🎙️ Mikrofonni tekshirish")
        return button


if __name__ == "__main__":
    MicTestApp().run()