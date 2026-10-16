
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
from voice_input import VoiceInput
from image_handler import ImageHandler


class MessageBubble(BoxLayout):

    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = (dp(15), dp(10), dp(15), dp(10))
        self.spacing = dp(2)

        self.label = Label(
            text=str(text),
            font_size=dp(18),
            color=(1, 1, 1, 1),
            halign="left",
            valign="middle",
            size_hint_y=None
        )

        self.label.bind(texture_size=self.update_height)
        self.add_widget(self.label)

        with self.canvas.before:
            if is_user:
                Color(0.08, 0.38, 0.90, 1)
            else:
                Color(0.18, 0.18, 0.20, 1)

            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(18)]
            )

        self.bind(
            pos=self.update_background,
            size=self.update_background,
            width=self.update_label_width
        )

    def update_height(self, instance, size):
        self.label.text_size = (max(dp(50), self.width - dp(30)), None)
        self.height = max(dp(42), size[1] + dp(20))

    def update_label_width(self, instance, width):
        self.label.text_size = (max(dp(50), width - dp(30)), None)

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
                background_color=(0.12, 0.12, 0.14, 1)
            )
            button.bind(on_press=callback)
            self.add_widget(button)

        close = Button(
            text="Yopish",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(52),
            background_normal="",
            background_color=(0.08, 0.38, 0.90, 1)
        )
        close.bind(on_press=lambda instance: self.app.close_menu())
        self.add_widget(close)

    def home(self, instance):
        self.app.close_menu()

    def brain(self, instance):
        self.app.show_popup("Brain", "JARVIS Language Brain faol.")

    def voice(self, instance):
        self.app.show_popup("Ovoz", "Ovozli boshqaruv tayyor.")

    def memory(self, instance):
        self.app.show_memory()

    def settings(self, instance):
        self.app.show_popup("Sozlamalar", "JARVIS 6.0")

    def about(self, instance):
        self.app.show_popup(
            "JARVIS",
            "JARVIS 6.0\nShaxsiy AI yordamchi."
        )


class JarvisApp(App):

    def build(self):
        self.title = "JARVIS"

        self.engine = JARVIS()
        self.memory = self.engine.memory
        self.voice = VoiceInput()
        self.listening_bubble = None
        self.menu_popup = None
        self.welcome = None

        self.image_handler = ImageHandler(
            callback=self.image_received
        )

        self.root_layout = BoxLayout(orientation="vertical")

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
            minimum_height=self.chat.setter("height")
        )

        self.scroll.add_widget(self.chat)
        self.root_layout.add_widget(self.scroll)

        self.build_bottom()

        Clock.schedule_once(self.show_welcome, 0.2)

        try:
            from android import activity
            activity.bind(on_activity_result=self.on_activity_result)
            self.android_activity = activity
        except Exception:
            self.android_activity = None

        return self.root_layout

    def build_top(self):
        top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(62),
            padding=(dp(8), dp(5))
        )

        menu = Button(
            text="MENYU",
            font_size=dp(15),
            bold=True,
            size_hint_x=None,
            width=dp(80),
            background_normal="",
            background_color=(0, 0, 0, 0)
        )
        menu.bind(on_press=self.open_menu)
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
            text="Rasm",
            font_size=dp(13),
            size_hint_x=None,
            width=dp(52)
        )
        gallery.bind(on_press=self.gallery_pressed)
        bottom.add_widget(gallery)

        camera = Button(
            text="Kamera",
            font_size=dp(13),
            size_hint_x=None,
            width=dp(64)
        )
        camera.bind(on_press=self.camera_pressed)
        bottom.add_widget(camera)

        self.input = TextInput(
            hint_text="Xabar yozing...",
            multiline=False,
            font_size=dp(18),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            background_color=(0.16, 0.16, 0.18, 1),
            padding=(dp(12), dp(12))
        )
        self.input.bind(on_text_validate=self.send_message)
        bottom.add_widget(self.input)

        mic = Button(
            text="Ovoz",
            font_size=dp(13),
            size_hint_x=None,
            width=dp(52)
        )
        mic.bind(on_press=self.microphone_pressed)
        bottom.add_widget(mic)

        send = Button(
            text="Yubor",
            font_size=dp(13),
            bold=True,
            size_hint_x=None,
            width=dp(58),
            background_normal="",
            background_color=(0.08, 0.38, 0.90, 1)
        )
        send.bind(on_press=self.send_message)
        bottom.add_widget(send)

        self.root_layout.add_widget(bottom)

    def show_welcome(self, dt):
        if self.welcome is not None:
            return

        self.welcome = Label(
            text="Hi, I'm Jarvis.",
            font_size=dp(26),
            size_hint_y=None,
            height=dp(70)
        )
        self.chat.add_widget(self.welcome)
        Clock.schedule_once(self.scroll_bottom, 0.1)

    def remove_welcome(self):
        if self.welcome is not None:
            if self.welcome.parent is not None:
                self.welcome.parent.remove_widget(self.welcome)
            self.welcome = None

    def add_message(self, text, is_user=False):
        bubble = MessageBubble(
            text=str(text),
            is_user=is_user
        )
        self.chat.add_widget(bubble)
        Clock.schedule_once(self.scroll_bottom, 0.1)
        return bubble

    def remove_listening_bubble(self):
        if self.listening_bubble is not None:
            if self.listening_bubble.parent is not None:
                self.listening_bubble.parent.remove_widget(
                    self.listening_bubble
                )
            self.listening_bubble = None

    def process_command(self, command):
        command = str(command).strip()

        if not command:
            return

        self.remove_welcome()
        self.add_message(command, True)

        try:
            response = self.engine.process(command)
        except Exception as error:
            response = "Xatolik yuz berdi: " + str(error)

        if response is None:
            response = ""

        self.add_message(str(response), False)

    def send_message(self, instance=None):
        command = self.input.text.strip()

        if not command:
            return

        self.input.text = ""
        self.process_command(command)

    def microphone_pressed(self, instance):
        if self.voice.is_listening():
            return

        self.remove_listening_bubble()

        if self.voice.listen():
            self.listening_bubble = self.add_message(
                "Tinglayapman...",
                False
            )
        else:
            error = self.voice.get_error()
            self.add_message(
                error or "Ovozli boshqaruvni ishga tushirib bo'lmadi.",
                False
            )

    def ensure_camera_permission(self):
        try:
            from android.permissions import (
                check_permission,
                request_permissions,
                Permission
            )
        except Exception:
            return True  # Android emas (kompyuterda sinov)

        try:
            if check_permission(Permission.CAMERA):
                return True

            request_permissions([Permission.CAMERA])
        except Exception as error:
            print("PERMISSION ERROR:", error)
            return True

        self.add_message(
            "Kamera uchun ruxsat so'raldi. Ruxsat berib, "
            "tugmani qayta bosing.",
            False
        )
        return False

    def camera_pressed(self, instance):
        if not self.ensure_camera_permission():
            return

        try:
            if not self.image_handler.open_camera():
                self.add_message("Kamerani ochib bo'lmadi.", False)
        except Exception as error:
            self.add_message(
                "Kamerani ochishda xatolik: " + str(error),
                False
            )

    def gallery_pressed(self, instance):
        try:
            if not self.image_handler.open_gallery():
                self.add_message("Galereyani ochib bo'lmadi.", False)
        except Exception as error:
            self.add_message(
                "Galereyani ochishda xatolik: " + str(error),
                False
            )

    def image_received(self, path):
        self.add_message("Rasm qabul qilindi.", False)

        try:
            if hasattr(self.engine, "process_image"):
                result = self.engine.process_image(path)

                if result:
                    self.add_message(str(result), False)
        except Exception as error:
            self.add_message(
                "Rasmni qayta ishlashda xatolik: " + str(error),
                False
            )

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):
        if request_code == self.voice.REQUEST_CODE:
            self.remove_listening_bubble()

            success = self.voice.handle_result(
                request_code,
                result_code,
                intent
            )

            if success:
                recognized_text = self.voice.get_result()

                if recognized_text:
                    self.process_command(recognized_text)
            else:
                error = self.voice.get_error()

                if error:
                    self.add_message(error, False)

            return

        if request_code in (
            self.image_handler.CAMERA_REQUEST,
            self.image_handler.GALLERY_REQUEST
        ):
            try:
                self.image_handler.handle_result(
                    request_code,
                    result_code,
                    intent
                )
            except Exception as error:
                self.add_message(
                    "Rasmni olishda xatolik: " + str(error),
                    False
                )

    def open_menu(self, instance):
        if self.menu_popup is not None:
            try:
                if self.menu_popup.parent is not None:
                    return
            except Exception:
                pass

        panel = MenuPanel(self)

        self.menu_popup = Popup(
            title="",
            content=panel,
            size_hint=(None, 1),
            width=dp(300),
            separator_height=0,
            auto_dismiss=True
        )
        self.menu_popup.open()

    def close_menu(self):
        if self.menu_popup is not None:
            try:
                self.menu_popup.dismiss()
            except Exception:
                pass
            self.menu_popup = None

    def show_memory(self):
        self.close_menu()

        try:
            count = self.engine.memory.count()
        except Exception:
            count = 0

        self.show_popup(
            "Memory",
            "Saqlangan yozuvlar: " + str(count)
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
        label.bind(
            width=lambda instance, value: setattr(
                instance,
                "text_size",
                (value, None)
            )
        )
        content.add_widget(label)

        close = Button(
            text="Yopish",
            size_hint_y=None,
            height=dp(48)
        )
        content.add_widget(close)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.85, 0.45)
        )
        close.bind(on_press=popup.dismiss)
        popup.open()

    def scroll_bottom(self, dt):
        try:
            self.scroll.scroll_y = 0
        except Exception:
            pass

    def on_pause(self):
        return True

    def on_resume(self):
        self.remove_listening_bubble()

    def on_stop(self):
        self.remove_listening_bubble()

        if self.android_activity is not None:
            try:
                self.android_activity.unbind(
                    on_activity_result=self.on_activity_result
                )
            except Exception:
                pass


if __name__ == "__main__":
    JarvisApp().run()
