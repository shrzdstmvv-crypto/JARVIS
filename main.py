import os
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

Window.softinput_mode = "below_target"

BG = (0.035, 0.035, 0.045, 1)
PANEL = (0.065, 0.065, 0.080, 1)
INPUT_BG = (0.075, 0.075, 0.095, 1)

USER_BUBBLE = (0.10, 0.23, 0.42, 1)
JARVIS_BUBBLE = (0.075, 0.075, 0.095, 1)

WHITE = (1, 1, 1, 1)
GRAY = (0.60, 0.60, 0.66, 1)


class RoundedBox(BoxLayout):

    def __init__(self, bg_color=PANEL, radius=18, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(radius)]
            )

        self.bind(
            pos=self.update_rect,
            size=self.update_rect
        )

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class MessageBubble(RoundedBox):

    def __init__(self, text, user=False, **kwargs):

        bubble_color = USER_BUBBLE if user else JARVIS_BUBBLE

        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            padding=[
                dp(14),
                dp(9),
                dp(14),
                dp(10)
            ],
            spacing=dp(3),
            bg_color=bubble_color,
            radius=17,
            **kwargs
        )

        name = Label(
            text="You" if user else "JARVIS",
            size_hint_y=None,
            height=dp(20),
            font_size=dp(12),
            color=GRAY,
            halign="left",
            valign="middle"
        )

        name.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        message = Label(
            text=str(text),
            size_hint_y=None,
            font_size=dp(16),
            color=WHITE,
            halign="left",
            valign="top"
        )

        message.bind(
            texture_size=self.update_message
        )

        self.add_widget(name)
        self.add_widget(message)

        self.message = message

        Clock.schedule_once(
            lambda dt: self.update_height(),
            0
        )

    def update_message(self, instance, size):
        instance.height = size[1]
        self.update_height()

    def update_height(self):
        if hasattr(self, "message"):
            self.height = (
                dp(9)
                + dp(20)
                + dp(3)
                + self.message.texture_size[1]
                + dp(10)
            )


class JarvisApp(App):

    def build(self):

        self.title = "JARVIS"
        self.first_message = False
        self.assistant = None
        self.core_error = ""
        self.selected_image = None
        self.listening = False
        self.voice = None
        self.permission_manager = None
        self.android_activity = None

        self.setup_permissions()
        self.setup_activity_result()

        self.root = FloatLayout()

        with self.root.canvas.before:
            Color(*BG)
            self.background = RoundedRectangle(
                pos=self.root.pos,
                size=self.root.size
            )

        self.root.bind(
            pos=self.update_background,
            size=self.update_background
        )

        try:
            from image_handler import ImageHandler

            self.image_handler = ImageHandler(
                callback=self.image_selected
            )

            print("Image Handler yuklandi.")

        except Exception as error:
            self.image_handler = None
            print("Image Handler:", error)

        try:
            from jarvis import JARVIS

            self.assistant = JARVIS()

            print("JARVIS CORE YUKLANDI")

        except Exception as error:

            self.assistant = None

            self.core_error = (
                f"{type(error).__name__}: {error}"
            )

            print("JARVIS CORE YUKLANMADI")
            print(self.core_error)

            traceback.print_exc()

        self.show_splash()

        return self.root

    def setup_activity_result(self):

        try:
            from android import activity

            self.android_activity = activity

            activity.bind(
                on_activity_result=self.on_activity_result
            )

            print("Activity callback ulandi.")

        except Exception as error:
            self.android_activity = None
            print("Activity callback mavjud emas:", error)

    def on_stop(self):

        try:
            if self.android_activity:
                self.android_activity.unbind(
                    on_activity_result=self.on_activity_result
                )
        except Exception:
            pass

    def setup_permissions(self):

        try:
            from permission_test import PermissionManager

            self.permission_manager = PermissionManager()

            if self.permission_manager.android:

                Clock.schedule_once(
                    lambda dt: self.request_permissions(),
                    0.8
                )

        except Exception as error:
            print("Permission setup:", error)

    def request_permissions(self):

        if self.permission_manager is None:
            return

        try:
            self.permission_manager.request()
        except Exception as error:
            print("Permission error:", error)

    def update_background(self, *args):
        self.background.pos = self.root.pos
        self.background.size = self.root.size

    def show_splash(self):

        self.root.clear_widgets()

        splash = FloatLayout()

        title = Label(
            text="JARVIS",
            font_size=dp(52),
            bold=True,
            color=WHITE,
            size_hint=(1, None),
            height=dp(90),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.53
            }
        )

        version = Label(
            text="6.0",
            font_size=dp(17),
            color=GRAY,
            size_hint=(1, None),
            height=dp(40),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.44
            }
        )

        splash.add_widget(title)
        splash.add_widget(version)

        self.root.add_widget(splash)

        Clock.schedule_once(
            self.show_main,
            1.5
        )

    def show_main(self, *args):

        self.root.clear_widgets()

        main = BoxLayout(
            orientation="vertical"
        )

        header = BoxLayout(
            size_hint_y=None,
            height=dp(64),
            padding=[
                dp(18),
                dp(8)
            ]
        )

        title = Label(
            text="JARVIS",
            font_size=dp(24),
            bold=True,
            color=WHITE,
            halign="left",
            valign="middle"
        )

        title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        header.add_widget(title)
        main.add_widget(header)

        self.scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(3)
        )

        self.chat = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[
                dp(12),
                dp(12)
            ],
            size_hint_y=None
        )

        self.chat.bind(
            minimum_height=self.chat.setter("height")
        )

        self.scroll.add_widget(self.chat)
        main.add_widget(self.scroll)

        self.welcome = Label(
            text="Hi, I'm Jarvis.",
            font_size=dp(25),
            color=WHITE,
            size_hint_y=None,
            height=dp(65),
            halign="center",
            valign="middle"
        )

        self.welcome.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.chat.add_widget(self.welcome)

        bottom = BoxLayout(
            size_hint_y=None,
            height=dp(72),
            padding=[
                dp(8),
                dp(8)
            ],
            spacing=dp(6)
        )

        self.mic_button = Button(
            text="🎤",
            font_size=dp(21),
            size_hint_x=None,
            width=dp(48),
            background_normal="",
            background_down="",
            background_color=(
                0.08,
                0.08,
                0.10,
                1
            )
        )

        self.mic_button.bind(
            on_release=self.microphone
        )

        camera = Button(
            text="📷",
            font_size=dp(20),
            size_hint_x=None,
            width=dp(48),
            background_normal="",
            background_down="",
            background_color=(
                0.08,
                0.08,
                0.10,
                1
            )
        )

        camera.bind(
            on_release=self.camera
        )

        gallery = Button(
            text="🖼️",
            font_size=dp(20),
            size_hint_x=None,
            width=dp(48),
            background_normal="",
            background_down="",
            background_color=(
                0.08,
                0.08,
                0.10,
                1
            )
        )

        gallery.bind(
            on_release=self.gallery
        )

        self.input = TextInput(
            hint_text="Ask Jarvis...",
            multiline=False,
            font_size=dp(16),
            foreground_color=WHITE,
            hint_text_color=(
                0.55,
                0.55,
                0.60,
                1
            ),
            background_color=INPUT_BG,
            background_normal="",
            background_active="",
            cursor_color=WHITE,
            padding=[
                dp(14),
                dp(12)
            ]
        )

        self.input.bind(
            on_text_validate=self.send
        )

        send = Button(
            text="➤",
            font_size=dp(24),
            size_hint_x=None,
            width=dp(52),
            background_normal="",
            background_down="",
            background_color=(
                0.10,
                0.23,
                0.42,
                1
            )
        )

        send.bind(
            on_release=self.send
        )

        bottom.add_widget(self.mic_button)
        bottom.add_widget(camera)
        bottom.add_widget(gallery)
        bottom.add_widget(self.input)
        bottom.add_widget(send)

        main.add_widget(bottom)

        self.root.add_widget(main)

    def send(self, *args):

        text = self.input.text.strip()

        if not text:
            return

        if not self.first_message:

            self.first_message = True

            if self.welcome.parent:
                self.chat.remove_widget(self.welcome)

        self.add_message(text, True)

        self.input.text = ""

        Clock.schedule_once(
            lambda dt: self.process(text),
            0.05
        )

    def process(self, text):

        if self.assistant is None:

            self.add_message(
                "JARVIS Core yuklanmadi.\n\n"
                + self.core_error,
                False
            )

            return

        try:

            response = self.assistant.process(text)

            if response is None:
                response = "JARVIS javob qaytarmadi."

            self.add_message(
                str(response),
                False
            )

        except Exception as error:

            print("PROCESS ERROR:", error)

            traceback.print_exc()

            self.add_message(
                "JARVIS xatosi:\n\n"
                f"{type(error).__name__}: {error}",
                False
            )

    def add_message(self, text, user=False):

        bubble = MessageBubble(
            text=text,
            user=user
        )

        self.chat.add_widget(bubble)

        Clock.schedule_once(
            self.scroll_bottom,
            0.05
        )

    def scroll_bottom(self, *args):
        self.scroll.scroll_y = 0

    def microphone(self, *args):

        if self.listening:
            return

        try:

            if (
                self.permission_manager
                and self.permission_manager.android
            ):

                if not self.permission_manager.microphone_allowed():

                    self.add_message(
                        "Mikrofon uchun ruxsat kerak.",
                        False
                    )

                    self.permission_manager.request()

                    return

            from voice_input import VoiceInput

            self.voice = VoiceInput()

            self.listening = True

            self.mic_button.text = "🔴"

            self.add_message(
                "🎤 Tinglayapman...",
                False
            )

            success = self.voice.listen()

            if not success:

                self.listening = False
                self.mic_button.text = "🎤"

                self.add_message(
                    "Mikrofonni ishga tushirib bo‘lmadi.",
                    False
                )

        except Exception as error:

            self.listening = False
            self.mic_button.text = "🎤"

            print("VOICE ERROR:", error)

            traceback.print_exc()

            self.add_message(
                "Mikrofonni ishga tushirib bo‘lmadi.",
                False
            )

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != 1001:
            return False

        self.listening = False

        Clock.schedule_once(
            lambda dt:
            self.finish_voice_result(
                request_code,
                result_code,
                intent
            ),
            0
        )

        return True

    def finish_voice_result(
        self,
        request_code,
        result_code,
        intent
    ):

        self.mic_button.text = "🎤"

        if self.voice is None:

            self.add_message(
                "VoiceInput mavjud emas.",
                False
            )

            return

        try:

            success = self.voice.handle_result(
                request_code,
                result_code,
                intent
            )

            if not success:

                self.add_message(
                    "Ovoz aniqlanmadi. Qayta urinib ko‘ring.",
                    False
                )

                return

            text = self.voice.get_result()

            if not text:

                self.add_message(
                    "Ovoz aniqlanmadi.",
                    False
                )

                return

            print(
                "RECOGNIZED:",
                text
            )

            self.input.text = text
            self.send()

        except Exception as error:

            print(
                "SPEECH RESULT ERROR:",
                error
            )

            traceback.print_exc()

            self.add_message(
                "Ovoz natijasini o‘qishda xatolik.",
                False
            )

        finally:

            self.listening = False
            self.mic_button.text = "🎤"

    def camera(self, *args):

        if self.image_handler is None:

            self.add_message(
                "Image Handler yuklanmagan.",
                False
            )

            return

        if (
            self.permission_manager
            and self.permission_manager.android
        ):

            if not self.permission_manager.camera_allowed():

                self.add_message(
                    "Kamera uchun ruxsat kerak.",
                    False
                )

                self.permission_manager.request()

                return

        success = self.image_handler.open_camera()

        if success:

            self.add_message(
                "Kamera ishga tushirildi.",
                False
            )

        else:

            self.add_message(
                "Kamera hozircha APK bosqichida ulanadi.",
                False
            )

    def gallery(self, *args):

        if self.image_handler is None:

            self.add_message(
                "Image Handler yuklanmagan.",
                False
            )

            return

        success = self.image_handler.open_gallery()

        if success:

            self.add_message(
                "Galereya ochildi.",
                False
            )

        else:

            self.add_message(
                "Galereya hozircha APK bosqichida ulanadi.",
                False
            )

    def image_selected(self, path):

        self.selected_image = path

        filename = os.path.basename(path)

        self.add_message(
            "Rasm tanlandi:\n" + filename,
            False
        )

        print(
            "IMAGE:",
            path
        )


if __name__ == "__main__":
    JarvisApp().run()