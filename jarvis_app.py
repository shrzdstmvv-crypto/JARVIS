
import os
import sys
import threading

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle


# main.py ishga tushirishdan oldin to'ldiradi
BOOT_MESSAGE = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import selfupdate
from terminal import Terminal
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
            ("Terminal", self.terminal),
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

    def terminal(self, instance):
        self.app.show_terminal()

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
        self.terminal = Terminal(app=self, engine=self.engine)
        self.term_text = ""
        self.term_out = None
        self.term_in = None
        self.term_popup = None
        self.edit_target = None
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

        # Ishga tushish muvaffaqiyatli bo'ldi: yiqilishdan himoya belgisini olib tashlaymiz
        Clock.schedule_once(lambda dt: selfupdate.boot_ok(), 3)

        if BOOT_MESSAGE:
            Clock.schedule_once(
                lambda dt: self.add_message(BOOT_MESSAGE, False), 1
            )

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

        # Jarvis biror rasmni topib bergan bo'lsa, uni chatda ko'rsatamiz
        path = getattr(self.engine, "image_to_show", None)

        if path:
            self.engine.image_to_show = None
            self.show_image(path)

        if getattr(self.engine, "open_terminal", False):
            self.engine.open_terminal = False
            Clock.schedule_once(lambda dt: self.show_terminal(), 0.1)

    def show_image(self, path):
        try:
            self.chat.add_widget(
                Image(
                    source=str(path),
                    size_hint_y=None,
                    height=dp(240)
                )
            )
            Clock.schedule_once(self.scroll_bottom, 0.1)
        except Exception as error:
            print("IMAGE SHOW ERROR:", error)

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
                self.add_message(
                    self.image_handler.error
                    or "Kamerani ochib bo'lmadi.",
                    False
                )
        except Exception as error:
            self.add_message(
                "Kamerani ochishda xatolik: " + str(error),
                False
            )

    def gallery_pressed(self, instance):
        try:
            if not self.image_handler.open_gallery():
                self.add_message(
                    self.image_handler.error
                    or "Galereyani ochib bo'lmadi.",
                    False
                )
        except Exception as error:
            self.add_message(
                "Galereyani ochishda xatolik: " + str(error),
                False
            )

    @mainthread
    def image_received(self, path):
        self.remove_welcome()
        self.show_image(path)

        reply = "Rasm qabul qilindi."

        try:
            if hasattr(self.engine, "process_image"):
                result = self.engine.process_image(path)

                if isinstance(result, str) and result:
                    reply = result
        except Exception as error:
            reply = "Rasmni qayta ishlashda xatolik: " + str(error)

        self.add_message(reply, False)

    @mainthread
    def finish_voice(self, success):
        self.remove_listening_bubble()

        if success:
            recognized_text = self.voice.get_result()

            if recognized_text:
                self.process_command(recognized_text)
        else:
            error = self.voice.get_error()

            if error:
                self.add_message(error, False)

    @mainthread
    def show_error(self, text):
        self.add_message(text, False)

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):
        # Bu funksiya Android oqimida chaqiriladi, shuning uchun
        # ekranga tegishli ishlar @mainthread orqali bajariladi.
        if request_code == self.voice.REQUEST_CODE:
            success = self.voice.handle_result(
                request_code,
                result_code,
                intent
            )
            self.finish_voice(success)
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
                self.show_error("Rasmni olishda xatolik: " + str(error))

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

    # JARVIS'NI QAYTA YUKLASH (ilovani yopmasdan)
    def reload_engine(self):
        import importlib

        try:
            importlib.invalidate_caches()

            for name in (
                "language_brain", "learning", "images_store",
                "memory", "skills", "jarvis"
            ):
                module = sys.modules.get(name)

                if module is not None:
                    importlib.reload(module)

            import jarvis as jarvis_module
            engine = jarvis_module.JARVIS()

        except Exception as error:
            return (
                "Qayta yuklashda xato (eski holat saqlandi): "
                + repr(error)[:300]
            )

        self.engine = engine
        self.memory = engine.memory
        self.terminal.set_engine(engine)
        return "Jarvis qayta yuklandi."

    # TERMINAL OYNASI
    def _mono_font(self):
        try:
            from kivy.resources import resource_find
            path = resource_find("data/fonts/RobotoMono-Regular.ttf")

            if path:
                return path
        except Exception:
            pass

        return "Roboto"

    def show_terminal(self, instance=None):
        self.close_menu()

        if self.term_popup is not None:
            return

        font = self._mono_font()

        if not self.term_text:
            self.term_text = (
                "JARVIS TERMINAL\n"
                "Python kod yozing yoki !buyruq bilan shell ishlating.\n"
                "Yordam uchun: help\n"
                + selfupdate.status() + "\n"
            )

        content = BoxLayout(
            orientation="vertical",
            padding=dp(6),
            spacing=dp(6)
        )

        self.term_out = TextInput(
            text=self.term_text,
            readonly=True,
            multiline=True,
            font_name=font,
            font_size=dp(12),
            background_color=(0.04, 0.05, 0.08, 1),
            foreground_color=(0.75, 0.95, 0.8, 1),
            cursor_color=(0, 0, 0, 0)
        )
        content.add_widget(self.term_out)

        self.term_in = TextInput(
            multiline=True,
            font_name=font,
            font_size=dp(13),
            size_hint_y=None,
            height=dp(120),
            hint_text="Python kod yoki !buyruq (help yozing)",
            background_color=(0.10, 0.11, 0.14, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.3, 0.8, 1, 1),
            write_tab=False
        )
        content.add_widget(self.term_in)

        row = BoxLayout(
            size_hint_y=None,
            height=dp(46),
            spacing=dp(6)
        )

        for text, handler, color in (
            ("Ishga tushir", self.term_run, (0.08, 0.38, 0.90, 1)),
            ("Saqlash", self.term_save, (0.10, 0.50, 0.30, 1)),
            ("Tozala", self.term_clear, (0.25, 0.25, 0.30, 1)),
            ("Yopish", self.term_close, (0.50, 0.15, 0.15, 1))
        ):
            button = Button(
                text=text,
                font_size=dp(14),
                background_normal="",
                background_color=color
            )
            button.bind(on_press=handler)
            row.add_widget(button)

        content.add_widget(row)

        # Klaviatura ochilganda oyna kichrayib, yozish maydoni ko'rinib turadi
        try:
            from kivy.core.window import Window
            self._old_softinput = Window.softinput_mode
            Window.softinput_mode = "resize"
        except Exception:
            self._old_softinput = None

        self.term_popup = Popup(
            title="Terminal",
            content=content,
            size_hint=(1, 1),
            auto_dismiss=False
        )
        self.term_popup.open()
        Clock.schedule_once(self._term_scroll_end, 0.3)

    def term_close(self, instance=None):
        if self.term_popup is not None:
            self.term_popup.dismiss()

        self.term_popup = None
        self.term_out = None
        self.term_in = None

        try:
            from kivy.core.window import Window
            Window.softinput_mode = self._old_softinput or ""
        except Exception:
            pass

    def term_clear(self, instance=None):
        self.term_text = ""
        self.edit_target = None

        if self.term_out is not None:
            self.term_out.text = ""

        if self.term_in is not None:
            self.term_in.text = ""

    def _echo(self, code):
        lines = code.rstrip().splitlines() or [""]
        return ">>> " + lines[0] + "".join("\n... " + x for x in lines[1:])

    def term_run(self, instance=None):
        if self.term_in is None:
            return

        code = self.term_in.text

        if not code.strip():
            return

        # Tahrirlash rejimida "Ishga tushir" faqat sintaksisni tekshiradi
        if self.edit_target is not None:
            self._term_append(
                ">>> sintaksis tekshiruvi\n"
                + self.terminal.check_syntax(code)
            )
            return

        self.term_in.text = ""
        self._term_append(self._echo(code))

        threading.Thread(
            target=self._term_worker,
            args=(code,),
            daemon=True
        ).start()

    def _term_worker(self, code):
        output = self.terminal.execute(code)
        self._term_done(output)

    @mainthread
    def _term_done(self, output):
        if output:
            self._term_append(output)

        pending = self.terminal.pending_edit

        if pending is not None and self.term_in is not None:
            self.terminal.pending_edit = None
            kind, name, text = pending
            self.edit_target = (kind, name)
            self.term_in.text = text
            self.term_in.cursor = (0, 0)

    def term_save(self, instance=None):
        if self.term_in is None:
            return

        if self.edit_target is None:
            self._term_append(
                "Avval edit('modul') yoki edit_skill('nom') deb oching."
            )
            return

        kind, name = self.edit_target
        message = self.terminal.save_edit(kind, name, self.term_in.text)
        self._term_append(message)

        if not message.startswith("Saqlab bo'lmadi"):
            self.edit_target = None
            self.term_in.text = ""

            if kind == "module":
                self._term_append("Kuchga kirishi uchun yozing: reload")

    def _term_append(self, text):
        self.term_text = (self.term_text + str(text) + "\n")[-200000:]

        if self.term_out is not None:
            self.term_out.text = self.term_text
            Clock.schedule_once(self._term_scroll_end, 0.05)

    def _term_scroll_end(self, dt=0):
        try:
            if self.term_out is not None:
                self.term_out.cursor = self.term_out.get_cursor_from_index(
                    len(self.term_out.text)
                )
        except Exception:
            pass
