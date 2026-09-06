import os
import sys

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from jarvis import JARVIS
from memory import Memory
from voice_input import VoiceInput
from image_handler import ImageHandler


class MessageBubble(BoxLayout):

    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = (
            dp(15),
            dp(10),
            dp(15),
            dp(10)
        )
        self.spacing = dp(2)

        self.label = Label(
            text=str(text),
            font_size=dp(18),
            color=(1, 1, 1, 1),
            halign="left",
            valign="middle",
            size_hint_y=None
        )

        self.label.bind(
            texture_size=self.update_height
        )

        self.add_widget(self.label)

        with self.canvas.before:
            if is_user:
                Color(
                    0.08,
                    0.38,
                    0.90,
                    1
                )
            else:
                Color(
                    0.18,
                    0.18,
                    0.20,
                    1
                )

            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(18)]
            )

        self.bind(
            pos=self.update_background,
            size=self.update_background
        )

    def update_height(self, instance, size):
        self.label.text_size = (
            self.width - dp(30),
            None
        )

        self.height = size[1] + dp(20)

    def update_background(self, instance, value):
        self.background.pos = self.pos
        self.background.size = self.size


class MenuPanel(BoxLayout):

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.app = app
        self.orientation = "vertical"
        self.padding = dp(18)
        self.spacing = dp(10)

        title = Label(
            text="MENYU",
            font_size=dp(25),
            size_hint_y=None,
            height=dp(55)
        )

        self.add_widget(title)

        items = [
            ("Bosh sahifa", self.home),
            ("Brain", self.brain),
            ("Ovoz", self.voice),
            ("Memory", self.memory),
            ("Sozlamalar", self.settings),
            ("JARVIS haqida", self.about)
        ]

        for name, callback in items:
            button = Button(
                text=name,
                font_size=dp(18),
                size_hint_y=None,
                height=dp(52),
                background_normal="",
                background_color=(
                    0.12,
                    0.12,
                    0.14,
                    1
                )
            )

            button.bind(
                on_press=callback
            )

            self.add_widget(button)

        close = Button(
            text="Yopish",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(52),
            background_normal="",
            background_color=(
                0.08,
                0.38,
                0.90,
                1
            )
        )

        close.bind(
            on_press=lambda x: self.app.close_menu()
        )

        self.add_widget(close)

    def home(self, instance):
        self.app.close_menu()

    def brain(self, instance):
        self.app.show_popup(
            "Brain",
            "JARVIS Language Brain faol."
        )

    def voice(self, instance):
        self.app.show_popup(
            "Ovoz",
            "Ovozli boshqaruv tayyor."
        )

    def memory(self, instance):
        self.app.show_memory()

    def settings(self, instance):
        self.app.show_popup(
            "Sozlamalar",
            "JARVIS 6.0"
        )

    def about(self, instance):
        self.app.show_popup(
            "JARVIS",
            "JARVIS 6.0\nShaxsiy AI yordamchi."
        )


class JarvisApp(App):

    def build(self):
        self.title = "JARVIS"

        self.engine = JARVIS()
        self.memory = Memory()
        self.voice = VoiceInput()

        self.image_handler = ImageHandler(
            callback=self.image_received
        )

        self.root_layout = BoxLayout(
            orientation="vertical"
        )

        self.build_top()

        self.scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3)
        )

        self.chat = GridLayout(
            cols=1,
            spacing=dp(10),
            padding=dp(12),
            size_hint_y=None
        )

        self.chat.bind(
            minimum_height=self.chat.setter(
                "height"
            )
        )

        self.scroll.add_widget(self.chat)

        self.root_layout.add_widget(
            self.scroll
        )

        self.build_bottom()

        Clock.schedule_once(
            self.show_welcome,
            0.2
        )

        try:
            from android import activity

            activity.bind(
                on_activity_result=
                self.on_activity_result
            )
        except Exception:
            pass

        return self.root_layout

    def build_top(self):
        top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(62),
            padding=(
                dp(8),
                dp(5)
            )
        )

        menu = Button(
            text="☰",
            font_size=dp(28),
            size_hint_x=None,
            width=dp(55),
            background_normal="",
            background_color=(
                0,
                0,
                0,
                0
            )
        )

        menu.bind(
            on_press=self.open_menu
        )

        top.add_widget(menu)

        title = Label(
            text="JARVIS",
            font_size=dp(24),
            bold=True
        )

        top.add_widget(title)

        self.root_layout.add_widget(top)

    def build_bottom(self):
        bottom = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(68),
            spacing=dp(5),
            padding=dp(7)
        )

        gallery = Button(
            text="🖼️",
            font_size=dp(20),
            size_hint_x=None,
            width=dp(50)
        )

        gallery.bind(
            on_press=self.gallery_pressed
        )

        bottom.add_widget(gallery)

        camera = Button(
            text="📷",
            font_size=dp(20),
            size_hint_x=None,
            width=dp(50)
        )

        camera.bind(
            on_press=self.camera_pressed
        )

        bottom.add_widget(camera)

        self.input = TextInput(
            hint_text="Xabar yozing...",
            multiline=False,
            font_size=dp(18),
            padding=(
                dp(12),
                dp(12)
            )
        )

        self.input.bind(
            on_text_validate=self.send_message
        )

        bottom.add_widget(
            self.input
        )

        mic = Button(
            text="🎤",
            font_size=dp(20),
            size_hint_x=None,
            width=dp(50)
        )

        mic.bind(
            on_press=self.microphone_pressed
        )

        bottom.add_widget(mic)

        send = Button(
            text="➤",
            font_size=dp(24),
            size_hint_x=None,
            width=dp(52),
            background_normal="",
            background_color=(
                0.08,
                0.38,
                0.90,
                1
            )
        )

        send.bind(
            on_press=self.send_message
        )

        bottom.add_widget(send)

        self.root_layout.add_widget(
            bottom
        )

    def show_welcome(self, dt):
        self.welcome = Label(
            text="Hi, I'm Jarvis.",
            font_size=dp(26),
            size_hint_y=None,
            height=dp(70)
        )

        self.chat.add_widget(
            self.welcome
        )

        Clock.schedule_once(
            self.scroll_bottom,
            0.1
        )

    def remove_welcome(self):
        if hasattr(self, "welcome"):
            if self.welcome.parent:
                self.welcome.parent.remove_widget(
                    self.welcome
                )

            del self.welcome

    def add_message(self, text, is_user=False):
        bubble = MessageBubble(
            text=str(text),
            is_user=is_user
        )

        self.chat.add_widget(
            bubble
        )

        Clock.schedule_once(
            self.scroll_bottom,
            0.1
        )

    def process_command(self, command):
        command = str(command).strip()

        if not command:
            return

        self.remove_welcome()

        self.add_message(
            command,
            True
        )

        try:
            response = self.engine.process(
                command
            )
        except Exception as error:
            response = (
                "Xatolik yuz berdi: "
                + str(error)
            )

        if response is None:
            response = ""

        response = str(response)

        self.add_message(
            response,
            False
        )

    def send_message(self, instance=None):
        command = self.input.text.strip()

        if not command:
            return

        self.input.text = ""

        self.process_command(
            command
        )

    def microphone_pressed(self, instance):
        if self.voice.is_listening():
            return

        if self.voice.listen():
            self.add_message(
                "Tinglayapman...",
                False
            )

    def camera_pressed(self, instance):
        self.image_handler.open_camera()

    def gallery_pressed(self, instance):
        self.image_handler.open_gallery()

    def image_received(self, path):
        self.add_message(
            "Rasm qabul qilindi.",
            False
        )

        try:
            if hasattr(
                self.engine,
                "process_image"
            ):
                self.engine.process_image(
                    path
                )
        except Exception:
            pass

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):
        if request_code == self.voice.REQUEST_CODE:
            if self.voice.handle_result(
                request_code,
                result_code,
                intent
            ):
                text = self.voice.get_result()

                if text:
                    for widget in list(
                        self.chat.children
                    ):
                        if isinstance(
                            widget,
                            MessageBubble
                        ):
                            if widget.label.text == "Tinglayapman...":
                                self.chat.remove_widget(
                                    widget
                                )
                                break

                    self.process_command(
                        text
                    )

            return

        if request_code in (
            self.image_handler.CAMERA_REQUEST,
            self.image_handler.GALLERY_REQUEST
        ):
            self.image_handler.handle_result(
                request_code,
                result_code,
                intent
            )

    def open_menu(self, instance):
        panel = MenuPanel(
            self
        )

        self.menu_popup = Popup(
            title="",
            content=panel,
            size_hint=(
                None,
                1
            ),
            width=dp(300),
            separator_height=0,
            auto_dismiss=True
        )

        self.menu_popup.open()

    def close_menu(self):
        if hasattr(
            self,
            "menu_popup"
        ):
            self.menu_popup.dismiss()

    def show_memory(self):
        self.close_menu()

        count = self.memory.count()

        self.show_popup(
            "Memory",
            "Saqlangan yozuvlar: "
            + str(count)
        )

    def show_popup(self, title, text):
        content = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        label = Label(
            text=str(text),
            font_size=dp(18),
            halign="center",
            valign="middle"
        )

        content.add_widget(
            label
        )

        close = Button(
            text="Yopish",
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(
            close
        )

        popup = Popup(
            title=title,
            content=content,
            size_hint=(
                0.85,
                0.45
            )
        )

        close.bind(
            on_press=popup.dismiss
        )

        popup.open()

    def scroll_bottom(self, dt):
        try:
            self.scroll.scroll_y = 0
        except Exception:
            pass


if __name__ == "__main__":
    JarvisApp().run()