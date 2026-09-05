import os
import shutil

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from jarvis import JARVIS
from image_handler import ImageHandler


class ChatBubble(BoxLayout):

    text = StringProperty("")
    is_user = False

    def __init__(
        self,
        text="",
        is_user=False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.text = text
        self.is_user = is_user

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.padding = dp(10)
        self.spacing = dp(5)

        label = Label(
            text=text,
            size_hint_y=None,
            text_size=(dp(300), None),
            halign="left",
            valign="middle",
            font_size=dp(16)
        )

        label.bind(
            texture_size=self.update_height
        )

        self.add_widget(label)

        self.height = max(
            dp(50),
            label.texture_size[1] + dp(20)
        )

    def update_height(
        self,
        instance,
        value
    ):
        self.height = max(
            dp(50),
            value[1] + dp(20)
        )


class JARVISApp(App):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.assistant = None
        self.image_handler = None

        self.selected_image = None
        self.pending_image = None
        self.pending_image_name = False

        self.chat_layout = None
        self.scroll_view = None
        self.input_field = None

        self.welcome_label = None

    def build(self):

        Window.clearcolor = (
            0.05,
            0.05,
            0.05,
            1
        )

        try:
            self.assistant = JARVIS()
        except Exception as error:

            print(
                "JARVIS INIT ERROR:",
                error
            )

            self.assistant = None

        self.image_handler = ImageHandler(
            callback=self.image_selected
        )

        root = BoxLayout(
            orientation="vertical"
        )

        header = BoxLayout(
            size_hint_y=None,
            height=dp(70),
            padding=dp(12)
        )

        title = Label(
            text="JARVIS",
            font_size=dp(28),
            bold=True
        )

        status = Label(
            text="Online",
            font_size=dp(14)
        )

        header.add_widget(title)
        header.add_widget(status)

        root.add_widget(header)

        self.scroll_view = ScrollView(
            do_scroll_x=False
        )

        self.chat_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(10),
            spacing=dp(8)
        )

        self.chat_layout.bind(
            minimum_height=self.chat_layout.setter(
                "height"
            )
        )

        self.scroll_view.add_widget(
            self.chat_layout
        )

        root.add_widget(
            self.scroll_view
        )

        self.welcome_label = Label(
            text="Hi, I'm Jarvis.",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(22)
        )

        self.chat_layout.add_widget(
            self.welcome_label
        )

        input_bar = BoxLayout(
            size_hint_y=None,
            height=dp(70),
            padding=dp(8),
            spacing=dp(6)
        )

        gallery_button = Button(
            text="🖼️",
            font_size=dp(24),
            size_hint_x=None,
            width=dp(55)
        )

        gallery_button.bind(
            on_release=self.open_gallery
        )

        camera_button = Button(
            text="📷",
            font_size=dp(24),
            size_hint_x=None,
            width=dp(55)
        )

        camera_button.bind(
            on_release=self.open_camera
        )

        mic_button = Button(
            text="🎤",
            font_size=dp(24),
            size_hint_x=None,
            width=dp(55)
        )

        mic_button.bind(
            on_release=self.start_voice
        )

        self.input_field = TextInput(
            hint_text="Xabar yozing...",
            multiline=False,
            font_size=dp(17)
        )

        self.input_field.bind(
            on_text_validate=self.send
        )

        send_button = Button(
            text="➤",
            font_size=dp(25),
            size_hint_x=None,
            width=dp(55)
        )

        send_button.bind(
            on_release=self.send
        )

        input_bar.add_widget(
            gallery_button
        )

        input_bar.add_widget(
            camera_button
        )

        input_bar.add_widget(
            mic_button
        )

        input_bar.add_widget(
            self.input_field
        )

        input_bar.add_widget(
            send_button
        )

        root.add_widget(
            input_bar
        )

        Clock.schedule_once(
            self.scroll_bottom,
            0.2
        )

        return root

    def add_message(
        self,
        text,
        is_user
    ):

        if self.welcome_label is not None:

            if self.welcome_label.parent:

                self.chat_layout.remove_widget(
                    self.welcome_label
                )

            self.welcome_label = None

        bubble = ChatBubble(
            text=str(text),
            is_user=is_user
        )

        self.chat_layout.add_widget(
            bubble
        )

        Clock.schedule_once(
            self.scroll_bottom,
            0.1
        )

    def scroll_bottom(
        self,
        *args
    ):

        if self.scroll_view is not None:

            self.scroll_view.scroll_y = 0

    def send(
        self,
        *args
    ):

        if self.input_field is None:
            return

        text = self.input_field.text.strip()

        if not text:
            return

        if self.pending_image_name:

            self.add_message(
                text,
                True
            )

            self.save_named_image(
                text
            )

            return

        self.input_field.text = ""

        self.add_message(
            text,
            True
        )

        if self.assistant is None:

            self.add_message(
                "JARVIS Core yuklanmagan.",
                False
            )

            return

        try:

            response = self.assistant.process(
                text
            )

            self.add_message(
                response,
                False
            )

        except Exception as error:

            print(
                "SEND ERROR:",
                error
            )

            self.add_message(
                "JARVIS ishlashida xatolik:\n"
                + str(error),
                False
            )

    def open_gallery(
        self,
        *args
    ):

        if self.image_handler is None:

            self.add_message(
                "Image Handler yuklanmagan.",
                False
            )

            return

        try:

            success = (
                self.image_handler.open_gallery()
            )

            if not success:

                self.add_message(
                    "Galereyani ochib bo‘lmadi.",
                    False
                )

        except Exception as error:

            print(
                "GALLERY BUTTON ERROR:",
                error
            )

            self.add_message(
                "Galereyani ochishda xatolik:\n"
                + str(error),
                False
            )

    def open_camera(
        self,
        *args
    ):

        if self.image_handler is None:

            self.add_message(
                "Image Handler yuklanmagan.",
                False
            )

            return

        try:

            success = (
                self.image_handler.open_camera()
            )

            if not success:

                self.add_message(
                    "Kamerani ishga tushirib bo‘lmadi.",
                    False
                )

        except Exception as error:

            print(
                "CAMERA BUTTON ERROR:",
                error
            )

            self.add_message(
                "Kamerani ochishda xatolik:\n"
                + str(error),
                False
            )

    def start_voice(
        self,
        *args
    ):

        try:

            from voice_input import VoiceInput

            self.voice_input = VoiceInput(
                callback=self.voice_result
            )

            self.voice_input.start()

        except Exception as error:

            print(
                "VOICE ERROR:",
                error
            )

            self.add_message(
                "Ovozli kiritishda xatolik:\n"
                + str(error),
                False
            )

    def voice_result(
        self,
        text
    ):

        if not text:
            return

        self.input_field.text = str(
            text
        )

        Clock.schedule_once(
            self.send,
            0.1
        )

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        try:

            if self.image_handler is None:
                return

            handled = (
                self.image_handler.handle_result(
                    request_code,
                    result_code,
                    intent
                )
            )

            if not handled:

                print(
                    "ACTIVITY RESULT NOT HANDLED:",
                    request_code
                )

        except Exception as error:

            print(
                "ACTIVITY RESULT ERROR:",
                error
            )

            self.add_message(
                "Rasmni olishda xatolik:\n"
                + str(error),
                False
            )

    def image_selected(
        self,
        path
    ):

        if not path:
            return

        path = str(path)

        if not os.path.exists(path):

            self.add_message(
                "Rasm fayli topilmadi.",
                False
            )

            return

        self.selected_image = path
        self.pending_image = path
        self.pending_image_name = True

        filename = os.path.basename(
            path
        )

        self.add_message(
            "Rasm tanlandi: " + filename,
            False
        )

        self.add_message(
            "Bu rasmni qanday nom bilan saqlay?",
            False
        )

        self.input_field.text = ""

        self.input_field.hint_text = (
            "Rasm nomini yozing..."
        )

    def get_image_directory(
        self
    ):

        try:

            from android.storage import (
                app_storage_path
            )

            base = app_storage_path()

        except Exception:

            base = self.user_data_dir

        directory = os.path.join(
            base,
            "JARVIS",
            "images"
        )

        os.makedirs(
            directory,
            exist_ok=True
        )

        return directory

    def save_named_image(
        self,
        name
    ):

        if not self.pending_image:

            self.add_message(
                "Saqlash uchun rasm topilmadi.",
                False
            )

            return

        try:

            clean_name = str(
                name
            ).strip()

            if not clean_name:

                self.add_message(
                    "Rasm nomini kiriting.",
                    False
                )

                return

            invalid_chars = (
                '<>:"/\\|?*'
            )

            for char in invalid_chars:

                clean_name = (
                    clean_name.replace(
                        char,
                        "_"
                    )
                )

            if not clean_name.lower().endswith(
                (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                )
            ):

                clean_name += ".jpg"

            image_directory = (
                self.get_image_directory()
            )

            os.makedirs(
                image_directory,
                exist_ok=True
            )

            destination = os.path.join(
                image_directory,
                clean_name
            )

            shutil.copy2(
                self.pending_image,
                destination
            )

            if not os.path.exists(
                destination
            ):

                self.add_message(
                    "Rasmni saqlashda xatolik yuz berdi.",
                    False
                )

                return

            self.selected_image = destination

            self.add_message(
                "Rasm saqlandi:\n"
                + clean_name,
                False
            )

            if self.assistant is not None:

                response = (
                    self.assistant.process_image(
                        destination,
                        clean_name
                    )
                )

                self.add_message(
                    response,
                    False
                )

            self.pending_image = None
            self.pending_image_name = False

            self.input_field.text = ""

            self.input_field.hint_text = (
                "Xabar yozing..."
            )

        except Exception as error:

            print(
                "SAVE IMAGE ERROR:",
                error
            )

            self.add_message(
                "Rasmni saqlashda xatolik:\n"
                + str(error),
                False
            )

    def on_start(
        self
    ):

        try:

            from android import activity

            activity.bind(
                on_activity_result=
                self.on_activity_result
            )

        except Exception as error:

            print(
                "ACTIVITY BIND ERROR:",
                error
            )


if __name__ == "__main__":

    JARVISApp().run()