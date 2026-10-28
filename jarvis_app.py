
import os
import sys
import threading

from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock, mainthread
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


# main.py ishga tushirishdan oldin to'ldiradi
BOOT_MESSAGE = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import selfupdate
from chats import ChatStore
from terminal import Terminal
from jarvis import JARVIS
from voice_input import VoiceInput
from image_handler import ImageHandler


# RANGLAR
BG = (0.043, 0.047, 0.063, 1)
PANEL = (0.085, 0.095, 0.125, 1)
FIELD = (0.145, 0.158, 0.205, 1)
USER_BUBBLE = (0.19, 0.22, 0.31, 1)
TEXT = (0.93, 0.94, 0.97, 1)
MUTED = (0.60, 0.64, 0.72, 1)
ACCENT = (0.36, 0.78, 1.0, 1)
DANGER = (0.90, 0.35, 0.38, 1)


def _window():
    from kivy.core.window import Window
    return Window


def _natural_width(text, font_size):
    """Matnning bir qatordagi tabiiy kengligi (pufak torayishi uchun)."""
    try:
        from kivy.core.text import Label as CoreLabel

        lines = str(text).split("\n")
        longest = max(lines, key=len) if lines else ""
        core = CoreLabel(text=longest, font_size=font_size)
        core.refresh()
        return core.texture.width if core.texture else None
    except Exception:
        return None


def flat_button(text, handler, height=dp(46), bg=PANEL, color=TEXT,
                font=dp(15), align="left"):
    button = Button(
        text=text,
        size_hint_y=None,
        height=height,
        font_size=font,
        color=color,
        halign=align,
        valign="middle",
        background_normal="",
        background_down="",
        background_color=bg
    )
    button.bind(
        size=lambda b, s: setattr(b, "text_size", (s[0] - dp(24), s[1]))
    )
    button.padding_x = dp(12)

    if handler is not None:
        button.bind(on_release=handler)

    return button


def paint_background(widget, color, radius=0):
    with widget.canvas.before:
        Color(*color)

        if radius:
            shape = RoundedRectangle(
                pos=widget.pos, size=widget.size, radius=[radius]
            )
        else:
            shape = Rectangle(pos=widget.pos, size=widget.size)

    def update(*args):
        shape.pos = widget.pos
        shape.size = widget.size

    widget.bind(pos=update, size=update)
    return shape


# ---------------------------------------------------------------- IKONALAR
class IconButton(ButtonBehavior, Widget):
    """Kanvasda chizilgan ikona tugma (emoji shriftiga bog'liq emas)."""

    def __init__(self, kind, color=TEXT, bg=None, **kwargs):
        super().__init__(**kwargs)
        self.kind = kind
        self.icon_color = color
        self.icon_bg = bg
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw)
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        s = min(self.width, self.height)
        cx, cy = self.center_x, self.center_y
        dim = 0.55 if self.state == "down" else 1.0
        r, g, b, a = self.icon_color
        w = max(dp(1.6), s * 0.045)

        with self.canvas:
            if self.icon_bg is not None:
                Color(*self.icon_bg)
                d = s * 0.86
                Ellipse(pos=(cx - d / 2, cy - d / 2), size=(d, d))

            Color(r * dim, g * dim, b * dim, a)

            if self.kind == "menu":
                for dy in (-0.17, 0.0, 0.17):
                    Line(
                        points=[cx - 0.27 * s, cy + dy * s,
                                cx + 0.27 * s, cy + dy * s],
                        width=w * 1.15, cap="round"
                    )

            elif self.kind == "plus":
                Line(points=[cx - 0.2 * s, cy, cx + 0.2 * s, cy],
                     width=w * 1.2, cap="round")
                Line(points=[cx, cy - 0.2 * s, cx, cy + 0.2 * s],
                     width=w * 1.2, cap="round")

            elif self.kind == "mic":
                RoundedRectangle(
                    pos=(cx - 0.08 * s, cy - 0.04 * s),
                    size=(0.16 * s, 0.30 * s), radius=[0.08 * s]
                )
                Line(circle=(cx, cy + 0.04 * s, 0.17 * s, 90, 270), width=w)
                Line(points=[cx, cy - 0.13 * s, cx, cy - 0.25 * s], width=w)
                Line(points=[cx - 0.09 * s, cy - 0.25 * s,
                             cx + 0.09 * s, cy - 0.25 * s],
                     width=w, cap="round")

            elif self.kind == "send":
                Line(points=[cx, cy - 0.15 * s, cx, cy + 0.15 * s],
                     width=w * 1.2, cap="round")
                Line(points=[cx - 0.11 * s, cy + 0.04 * s, cx,
                             cy + 0.16 * s, cx + 0.11 * s, cy + 0.04 * s],
                     width=w * 1.2, cap="round", joint="round")

            elif self.kind == "close":
                Line(points=[cx - 0.14 * s, cy - 0.14 * s,
                             cx + 0.14 * s, cy + 0.14 * s],
                     width=w, cap="round")
                Line(points=[cx - 0.14 * s, cy + 0.14 * s,
                             cx + 0.14 * s, cy - 0.14 * s],
                     width=w, cap="round")

            elif self.kind in ("up", "down"):
                sign = 1 if self.kind == "up" else -1
                Line(points=[cx - 0.16 * s, cy - 0.07 * s * sign,
                             cx, cy + 0.09 * s * sign,
                             cx + 0.16 * s, cy - 0.07 * s * sign],
                     width=w * 1.2, cap="round", joint="round")


class Scrim(ButtonBehavior, Widget):
    """Menyu ochiq paytda orqa fonni xiralashtiradi; bosilsa menyuni yopadi."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(0, 0, 0, 0.55)
            self._rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


# ---------------------------------------------------------------- XABARLAR
class MessageRow(BoxLayout):
    """Foydalanuvchi xabari: o'ng tomonda pufak. JARVIS: chapda oddiy matn."""

    def __init__(self, text, is_user, max_width, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            padding=(dp(10), dp(3), dp(10), dp(3)),
            spacing=dp(8),
            **kwargs
        )
        self.height = dp(40)
        self.is_user = is_user
        text = str(text)

        if is_user:
            self._build_user(text, max_width)
        else:
            self._build_assistant(text)

    def _build_user(self, text, max_width):
        pad_x, pad_y, font = dp(14), dp(10), dp(16)
        limit = max(dp(80), max_width - 2 * pad_x)
        natural = _natural_width(text, font)
        inner = min(limit, (natural + dp(4)) if natural else limit)

        self.bubble = BoxLayout(
            size_hint=(None, None),
            padding=(pad_x, pad_y, pad_x, pad_y)
        )
        paint_background(self.bubble, USER_BUBBLE, dp(18))

        self.label = Label(
            text=text,
            font_size=font,
            color=TEXT,
            size_hint=(None, None),
            halign="left",
            valign="top",
            text_size=(inner, None)
        )
        self.label.bind(texture_size=self._fit_user)
        self.bubble.add_widget(self.label)

        self.add_widget(Widget())  # chap tomonni bo'sh qoldiradi
        self.add_widget(self.bubble)
        self._pad = (pad_x, pad_y)

    def _fit_user(self, label, size):
        label.size = size
        self.bubble.size = (
            size[0] + 2 * self._pad[0], size[1] + 2 * self._pad[1]
        )
        self.height = self.bubble.height + dp(6)

    def _build_assistant(self, text):
        avatar = Label(
            text="J",
            bold=True,
            font_size=dp(15),
            color=(0.02, 0.05, 0.10, 1),
            size_hint=(None, None),
            size=(dp(28), dp(28))
        )

        with avatar.canvas.before:
            Color(*ACCENT)
            circle = Ellipse(pos=avatar.pos, size=avatar.size)

        avatar.bind(
            pos=lambda w, v: setattr(circle, "pos", w.pos),
            size=lambda w, v: setattr(circle, "size", w.size)
        )

        # Avatar yuqorida turishi uchun ustun ichiga joylanadi
        holder = BoxLayout(
            orientation="vertical", size_hint=(None, 1), width=dp(28)
        )
        holder.add_widget(avatar)
        holder.add_widget(Widget())
        self.add_widget(holder)

        self.label = Label(
            text=text,
            font_size=dp(16),
            color=TEXT,
            size_hint=(1, None),
            halign="left",
            valign="top"
        )
        self.label.bind(texture_size=self._fit_assistant)
        self.bind(width=self._wrap_assistant)
        self.add_widget(self.label)

    def _wrap_assistant(self, row, width):
        self.label.text_size = (max(dp(60), width - dp(56)), None)

    def _fit_assistant(self, label, size):
        label.height = size[1]
        self.height = max(dp(34), size[1] + dp(8))


# ---------------------------------------------------------------- ILOVA
class JarvisApp(App):

    # ----------------------------------------------------------- QURISH
    def build(self):
        self.title = "JARVIS"
        self._apply_keyboard_mode()

        self.engine = JARVIS()
        self.memory = self.engine.memory
        self.chats = ChatStore()
        self.terminal = Terminal(app=self, engine=self.engine)

        self.term_text = ""
        self.term_out = None
        self.term_in = None
        self.term_popup = None
        self.edit_target = None
        self.settings_popup = None
        self.plus_menu = None
        self.confirm_reset = False

        self.voice = VoiceInput()
        self.listening_bubble = None
        self.welcome = None
        self.busy = False
        self.thinking = None
        self.thinking_event = None
        self.speaker = None
        self.drawer_open = False

        self.image_handler = self._make_image_handler()

        self.layout = FloatLayout()
        main = BoxLayout(orientation="vertical", size_hint=(1, 1))
        paint_background(main, BG)

        main.add_widget(self.build_header())
        main.add_widget(self.build_chat_area())
        main.add_widget(self.build_input_bar())
        self.layout.add_widget(main)

        self.build_drawer()

        Clock.schedule_once(self.load_chat, 0.15)

        # Ishga tushish muvaffaqiyatli bo'ldi: yiqilishdan himoya belgisini olib tashlaymiz
        Clock.schedule_once(lambda dt: selfupdate.boot_ok(), 3)

        if BOOT_MESSAGE:
            Clock.schedule_once(
                lambda dt: self.add_message(BOOT_MESSAGE, False, save=False), 1
            )

        try:
            from android import activity
            activity.bind(on_activity_result=self.on_activity_result)
            self.android_activity = activity
        except Exception:
            self.android_activity = None

        try:
            _window().bind(on_keyboard=self._on_back)
        except Exception:
            pass

        return self.layout

    def _make_image_handler(self):
        try:
            return ImageHandler(
                callback=self.image_received,
                file_callback=self.file_received
            )
        except TypeError:
            # Eski ImageHandler fayl qabul qilishni bilmaydi
            return ImageHandler(callback=self.image_received)

    def _apply_keyboard_mode(self):
        try:
            _window().softinput_mode = selfupdate.get_setting(
                "softinput_mode", "resize"
            )
        except Exception as error:
            print("SOFTINPUT ERROR:", error)

    def _on_back(self, window, key, *args):
        if key == 27 and self.drawer_open:
            self.close_drawer()
            return True

        return False

    # ------------------------------------------------------ YUQORI QISM
    def build_header(self):
        header = BoxLayout(
            size_hint_y=None,
            height=dp(56),
            padding=(dp(8), dp(6), dp(8), dp(6))
        )
        paint_background(header, BG)

        self.menu_button = IconButton(
            "menu", size_hint=(None, 1), width=dp(48)
        )
        self.menu_button.bind(on_release=lambda *a: self.toggle_drawer())
        header.add_widget(self.menu_button)
        header.add_widget(Widget())
        return header

    # --------------------------------------------------------- CHAT OYNASI
    def build_chat_area(self):
        area = BoxLayout(orientation="vertical")
        background = os.path.join(BASE_DIR, "chat_bg.png")

        with area.canvas.before:
            Color(1, 1, 1, 1)

            if os.path.exists(background):
                shape = Rectangle(
                    source=background, pos=area.pos, size=area.size
                )
            else:
                Color(*BG)
                shape = Rectangle(pos=area.pos, size=area.size)

        area.bind(
            pos=lambda w, v: setattr(shape, "pos", w.pos),
            size=lambda w, v: setattr(shape, "size", w.size)
        )

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.chat = GridLayout(
            cols=1,
            spacing=dp(6),
            padding=(dp(2), dp(10), dp(2), dp(10)),
            size_hint_y=None
        )
        self.chat.bind(minimum_height=self.chat.setter("height"))
        self.scroll.add_widget(self.chat)
        area.add_widget(self.scroll)
        return area

    def load_chat(self, dt=0):
        """Hozirgi suhbat xabarlarini ekranga chiqaradi."""
        self.chat.clear_widgets()
        self.welcome = None
        chat = self.chats.current()

        if not chat["messages"]:
            self.show_welcome()
            return

        for item in chat["messages"]:
            if item.get("k") == "i":
                if os.path.exists(item.get("t", "")):
                    self.show_image(item["t"], save=False)
            else:
                self.add_message(item.get("t", ""), item.get("u", False), save=False)

    def show_welcome(self):
        try:
            text = self.engine.welcome_text()
        except Exception:
            text = "Salom! Men JARVIS."

        self.welcome = self.add_message(text, False, save=False)

    def remove_welcome(self):
        if self.welcome is not None:
            if self.welcome.parent is not None:
                self.welcome.parent.remove_widget(self.welcome)

            self.welcome = None

    def add_message(self, text, is_user=False, save=True):
        max_width = _window().width * 0.80

        row = MessageRow(str(text), is_user, max_width)
        self.chat.add_widget(row)

        if save:
            self.chats.add("t", text, is_user)

        Clock.schedule_once(self.scroll_bottom, 0.1)
        return row

    def show_image(self, path, save=True):
        try:
            self.chat.add_widget(
                Image(source=str(path), size_hint_y=None, height=dp(240))
            )

            if save:
                self.chats.add("i", path, False)

            Clock.schedule_once(self.scroll_bottom, 0.1)
        except Exception as error:
            print("IMAGE SHOW ERROR:", error)

    def scroll_bottom(self, dt=0):
        try:
            self.scroll.scroll_y = 0
        except Exception:
            pass

    # ------------------------------------------------- YOZISH MAYDONI
    def build_input_bar(self):
        outer = BoxLayout(
            size_hint_y=None,
            height=dp(66),
            padding=(dp(10), dp(6), dp(10), dp(10))
        )
        paint_background(outer, BG)
        self.input_outer = outer

        box = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(2))
        paint_background(box, FIELD, dp(26))
        self.input_box = box

        plus = IconButton("plus", size_hint=(None, 1), width=dp(46))
        plus.bind(on_release=lambda *a: self.show_plus_menu())

        self.input = TextInput(
            multiline=True,
            hint_text="Xabar yozing",
            hint_text_color=MUTED,
            foreground_color=TEXT,
            cursor_color=ACCENT,
            background_color=(0, 0, 0, 0),
            font_size=dp(16),
            padding=(dp(6), dp(14), dp(6), dp(10)),
            write_tab=False
        )

        mic = IconButton("mic", size_hint=(None, 1), width=dp(44))
        mic.bind(on_release=self.microphone_pressed)

        send = IconButton(
            "send", color=(0.02, 0.05, 0.10, 1), bg=ACCENT,
            size_hint=(None, 1), width=dp(50)
        )
        send.bind(on_release=self.send_message)

        for widget in (plus, self.input, mic, send):
            box.add_widget(widget)

        outer.add_widget(box)
        box.bind(height=lambda w, h: setattr(outer, "height", h + dp(16)))

        try:
            self.input.bind(minimum_height=self._input_resized)
        except Exception:
            pass

        self.input.bind(text=self._input_resized)
        return outer

    def _input_resized(self, *args):
        try:
            content = self.input.minimum_height
        except Exception:
            content = dp(24) * (self.input.text.count("\n") + 1) + dp(24)

        self.input_box.height = max(dp(52), min(dp(150), content + dp(4)))

    def send_message(self, instance=None):
        command = self.input.text.strip()

        if not command:
            return

        self.input.text = ""
        self.process_command(command)

    # ------------------------------------------------------ "+" MENYUSI
    def show_plus_menu(self):
        if self.plus_menu is not None:
            return

        content = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(2))
        paint_background(content, (0.11, 0.125, 0.165, 1), dp(18))

        for text, handler in (
            ("Kamera", self.camera_pressed),
            ("Galereya", self.gallery_pressed),
            ("Fayl", self.file_pressed)
        ):
            content.add_widget(
                flat_button(text, handler, bg=(0, 0, 0, 0), font=dp(16))
            )

        try:
            menu = ModalView(
                size_hint=(None, None),
                size=(dp(210), dp(3 * 46 + 22)),
                pos_hint={"x": 0.03, "y": 0.13},
                background="",
                background_color=(0, 0, 0, 0),
                overlay_color=(0, 0, 0, 0.35),
                auto_dismiss=True
            )
        except TypeError:
            menu = ModalView(
                size_hint=(None, None),
                size=(dp(210), dp(3 * 46 + 22)),
                pos_hint={"x": 0.03, "y": 0.13},
                auto_dismiss=True
            )
        menu.add_widget(content)
        menu.bind(on_dismiss=lambda *a: setattr(self, "plus_menu", None))
        self.plus_menu = menu
        menu.open()

    def close_plus_menu(self):
        if self.plus_menu is not None:
            self.plus_menu.dismiss()

    # ------------------------------------------- KAMERA, GALEREYA, FAYL
    def ensure_camera_permission(self):
        try:
            from android.permissions import (
                check_permission, request_permissions, Permission
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
            "tugmani qayta bosing.", False, save=False
        )
        return False

    def _open_picker(self, function_name, title):
        function = getattr(self.image_handler, function_name, None)

        if function is None:
            self.add_message(title + " hozircha mavjud emas.", False, save=False)
            return

        try:
            if not function():
                self.add_message(
                    self.image_handler.error or (title + " ochib bo'lmadi."),
                    False, save=False
                )
        except Exception as error:
            self.add_message(title + " xatosi: " + str(error), False, save=False)

    def camera_pressed(self, instance=None):
        self.close_plus_menu()

        if self.ensure_camera_permission():
            self._open_picker("open_camera", "Kamera")

    def gallery_pressed(self, instance=None):
        self.close_plus_menu()
        self._open_picker("open_gallery", "Galereya")

    def file_pressed(self, instance=None):
        self.close_plus_menu()
        self._open_picker("open_file_picker", "Fayl tanlash")

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
    def file_received(self, path, name=""):
        self.remove_welcome()
        label = name or os.path.basename(str(path))
        self.add_message("Fayl: " + label, True)
        reply = "Fayl qabul qilindi."

        try:
            if hasattr(self.engine, "process_file"):
                reply = self.engine.process_file(path, name) or reply
        except Exception as error:
            reply = "Faylni qayta ishlashda xatolik: " + str(error)

        self.add_message(reply, False)

    # ----------------------------------------------------------- OVOZ
    def microphone_pressed(self, instance=None):
        if self.voice.is_listening():
            return

        self.remove_listening_bubble()

        if self.voice.listen():
            self.listening_bubble = self.add_message(
                "Tinglayapman...", False, save=False
            )
        else:
            error = self.voice.get_error()
            self.add_message(
                error or "Ovozli boshqaruvni ishga tushirib bo'lmadi.",
                False, save=False
            )

    def remove_listening_bubble(self):
        if self.listening_bubble is not None:
            if self.listening_bubble.parent is not None:
                self.listening_bubble.parent.remove_widget(self.listening_bubble)

            self.listening_bubble = None

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
                self.add_message(error, False, save=False)

    @mainthread
    def show_error(self, text):
        self.add_message(text, False, save=False)

    def on_activity_result(self, request_code, result_code, intent):
        # Android oqimidan chaqiriladi: ekranga tegishli ishlar @mainthread orqali
        if request_code == self.voice.REQUEST_CODE:
            success = self.voice.handle_result(request_code, result_code, intent)
            self.finish_voice(success)
            return

        codes = (
            self.image_handler.CAMERA_REQUEST,
            self.image_handler.GALLERY_REQUEST,
            getattr(self.image_handler, "FILE_REQUEST", None)
        )

        if request_code in codes:
            try:
                self.image_handler.handle_result(request_code, result_code, intent)
            except Exception as error:
                self.show_error("Olishda xatolik: " + str(error))

    # ------------------------------------------------------- BUYRUQLAR
    def process_command(self, command):
        command = str(command).strip()

        if not command:
            return

        if self.busy:
            self.add_message(
                "Oldingi buyruq bajarilmoqda, biroz kuting.", False, save=False
            )
            return

        self._stop_speaking()
        self.remove_welcome()
        self.add_message(command, True)
        self.busy = True
        self.thinking_event = Clock.schedule_once(self._show_thinking, 0.7)

        threading.Thread(
            target=self._worker, args=(command,), daemon=True
        ).start()

    def _worker(self, command):
        # Uzoq ishlar (masalan internetdan ob-havo) ekranni qotirmasligi uchun
        try:
            response = self.engine.process(command)
        except Exception as error:
            response = "Xatolik yuz berdi: " + str(error)

        self._deliver(response)

    def _show_thinking(self, dt):
        self.thinking = self.add_message("...", False, save=False)

    def _clear_thinking(self):
        if self.thinking_event is not None:
            self.thinking_event.cancel()
            self.thinking_event = None

        if self.thinking is not None:
            if self.thinking.parent is not None:
                self.thinking.parent.remove_widget(self.thinking)

            self.thinking = None

    @mainthread
    def _deliver(self, response):
        self.busy = False
        self._clear_thinking()
        text = "" if response is None else str(response)

        if text:
            self.add_message(text, False)
            self._speak(text)

        path = getattr(self.engine, "image_to_show", None)

        if path:
            self.engine.image_to_show = None
            self.show_image(path)

        export = getattr(self.engine, "image_to_export", None)

        if export:
            self.engine.image_to_export = None
            self.export_item(export, "export_to_gallery", "Galereyaga saqlandi: ")

        file_export = getattr(self.engine, "file_to_export", None)

        if file_export:
            self.engine.file_to_export = None
            self.export_item(
                file_export[:2], "export_file_to_downloads",
                "Telefonga saqlandi: "
            )

        if getattr(self.engine, "open_terminal", False):
            self.engine.open_terminal = False
            Clock.schedule_once(lambda dt: self.show_terminal(), 0.1)

    def export_item(self, entry, function_name, success_text):
        path, name = entry[0], entry[1]
        function = getattr(self.image_handler, function_name, None)

        if function is None:
            self.add_message("Saqlash hozircha mavjud emas.", False, save=False)
            return

        try:
            ok, info = function(path, name)
        except Exception as error:
            ok, info = False, repr(error)[:150]

        self.add_message(
            (success_text + info) if ok else ("Saqlab bo'lmadi: " + info),
            False, save=False
        )

    # ----------------------------------------------------- OVOZLI JAVOB
    def _speak(self, text):
        if not selfupdate.get_setting("tts", True):
            return

        problem = None

        try:
            if self.speaker is None:
                from tts import Speaker
                self.speaker = Speaker()

            self.speaker.speak(text)
            problem = self.speaker.error
        except Exception as error:
            print("TTS ERROR:", error)
            problem = repr(error)[:120]

        # Ovoz ishlamasa, sababini bir marta chatda ko'rsatamiz
        if problem and not getattr(self, "_tts_warned", False):
            self._tts_warned = True
            self.add_message(
                "Ovozli javob ishlamadi: " + str(problem) + " "
                "Sozlamalar > Ovoz tili tugmasini bosib boshqa tilni sinab ko'ring "
                "yoki telefonda «Google matnni ovozga aylantirish» yoqilganini tekshiring.",
                False, save=False
            )

    def _stop_speaking(self):
        try:
            if self.speaker is not None:
                self.speaker.stop()
        except Exception:
            pass

    # ------------------------------------------------- YON MENYU (DRAWER)
    def build_drawer(self):
        width = min(dp(320), _window().width * 0.84)

        self.scrim = Scrim(size_hint=(1, 1))
        self.scrim.bind(on_release=lambda *a: self.close_drawer())

        self.drawer = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=width,
            padding=(dp(10), dp(14), dp(10), dp(10)),
            spacing=dp(6)
        )
        paint_background(self.drawer, PANEL)

        self.drawer.add_widget(
            flat_button(
                "Yangi chat", lambda *a: self.new_chat(),
                bg=ACCENT, color=(0.02, 0.05, 0.10, 1), align="center",
                font=dp(16)
            )
        )

        self.drawer.add_widget(
            Label(
                text="Chatlar", font_size=dp(13), color=MUTED,
                size_hint_y=None, height=dp(28), halign="left",
                text_size=(width - dp(30), None)
            )
        )

        self.drawer_scroll = ScrollView(do_scroll_x=False, bar_width=dp(2))
        self.drawer_list = GridLayout(
            cols=1, spacing=dp(2), size_hint_y=None
        )
        self.drawer_list.bind(minimum_height=self.drawer_list.setter("height"))
        self.drawer_scroll.add_widget(self.drawer_list)
        self.drawer.add_widget(self.drawer_scroll)

        self.drawer.add_widget(
            flat_button("Terminal", lambda *a: self._drawer_then(self.show_terminal))
        )
        self.drawer.add_widget(
            flat_button("Sozlamalar", lambda *a: self._drawer_then(self.show_settings))
        )

    def refresh_drawer(self):
        self.drawer_list.clear_widgets()
        current = self.chats.current()["id"]

        for chat_id, title in self.chats.list():
            row = BoxLayout(size_hint_y=None, height=dp(46))
            selected = chat_id == current
            row.add_widget(
                flat_button(
                    title,
                    lambda b, cid=chat_id: self.open_chat(cid),
                    bg=(0.16, 0.19, 0.27, 1) if selected else (0, 0, 0, 0)
                )
            )
            delete = IconButton(
                "close", color=MUTED, size_hint=(None, 1), width=dp(40)
            )
            delete.bind(on_release=lambda b, cid=chat_id: self.delete_chat(cid))
            row.add_widget(delete)
            self.drawer_list.add_widget(row)

    def toggle_drawer(self):
        if self.drawer_open:
            self.close_drawer()
        else:
            self.open_drawer()

    def open_drawer(self):
        if self.drawer_open:
            return

        self.drawer_open = True
        self.refresh_drawer()
        self.drawer.x = -self.drawer.width
        self.scrim.opacity = 0

        self.layout.add_widget(self.scrim)
        self.layout.add_widget(self.drawer)

        Animation(opacity=1, duration=0.18).start(self.scrim)
        Animation(x=0, duration=0.2, t="out_cubic").start(self.drawer)

    def close_drawer(self, *args):
        if not self.drawer_open:
            return

        self.drawer_open = False
        slide = Animation(x=-self.drawer.width, duration=0.18, t="in_cubic")
        slide.bind(on_complete=lambda *a: self._remove_drawer())
        slide.start(self.drawer)
        Animation(opacity=0, duration=0.15).start(self.scrim)

    def _remove_drawer(self):
        if self.drawer_open:
            return

        for widget in (self.scrim, self.drawer):
            if widget.parent is not None:
                widget.parent.remove_widget(widget)

    def _drawer_then(self, action):
        self.close_drawer()
        Clock.schedule_once(lambda dt: action(), 0.22)

    # --------------------------------------------------------- CHATLAR
    def new_chat(self):
        self._stop_speaking()
        self.chats.new_chat()

        if hasattr(self.engine, "reset_dialog"):
            self.engine.reset_dialog()

        self.close_drawer()
        self.load_chat()

    def open_chat(self, chat_id):
        self.chats.switch(chat_id)

        if hasattr(self.engine, "reset_dialog"):
            self.engine.reset_dialog()

        self.close_drawer()
        self.load_chat()

    def delete_chat(self, chat_id):
        was_current = self.chats.current()["id"] == chat_id
        self.chats.delete(chat_id)
        self.refresh_drawer()

        if was_current:
            self.load_chat()

    # ------------------------------------------------------ SOZLAMALAR
    def _toggle_text(self, label, key, default):
        return label + ": " + (
            "yoqilgan" if selfupdate.get_setting(key, default) else "o'chiq"
        )

    def show_settings(self):
        if self.settings_popup is not None:
            return

        self.confirm_reset = False
        content = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        scroll = ScrollView(do_scroll_x=False)
        rows = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        rows.bind(minimum_height=rows.setter("height"))

        def toggle(button, key, default, label):
            selfupdate.set_setting(key, not selfupdate.get_setting(key, default))
            button.text = self._toggle_text(label, key, default)

        tts_button = flat_button("", None, bg=FIELD)
        tts_button.text = self._toggle_text("Ovozli javob", "tts", True)
        tts_button.bind(
            on_release=lambda b: toggle(b, "tts", True, "Ovozli javob")
        )

        mic_button = flat_button("", None, bg=FIELD)
        mic_button.text = self._toggle_text(
            "Internetsiz mikrofon (imkon bo'lsa)", "offline_mic", False
        )
        mic_button.bind(
            on_release=lambda b: toggle(
                b, "offline_mic", False, "Internetsiz mikrofon (imkon bo'lsa)"
            )
        )

        modes = ["resize", "below_target", "pan", "scale", ""]

        def keyboard_label():
            current = _window().softinput_mode
            return "Klaviatura rejimi: " + (current or "o'chiq")

        keyboard_button = flat_button(keyboard_label(), None, bg=FIELD)

        def next_mode(button):
            current = _window().softinput_mode

            try:
                nxt = modes[(modes.index(current) + 1) % len(modes)]
            except ValueError:
                nxt = modes[0]

            self.set_keyboard_mode(nxt or "off")
            button.text = keyboard_label()

        keyboard_button.bind(on_release=next_mode)

        def lang_label():
            return "Ovoz tili: " + selfupdate.get_setting("tts_lang", "auto")

        lang_button = flat_button(lang_label(), None, bg=FIELD)

        def next_lang(button):
            choices = ["auto", "uz", "tr", "ru", "en"]
            current = selfupdate.get_setting("tts_lang", "auto")

            try:
                nxt = choices[(choices.index(current) + 1) % len(choices)]
            except ValueError:
                nxt = "auto"

            selfupdate.set_setting("tts_lang", nxt)
            button.text = lang_label()

            try:
                if self.speaker is None:
                    from tts import Speaker
                    self.speaker = Speaker()

                self.speaker.apply_language()
                self.speaker.speak("Salom, men JARVIS.")
                show_info("Ovoz tili: " + str(self.speaker.describe()))
            except Exception as error:
                show_info("Ovoz sinovi o'xshamadi: " + repr(error)[:80])

        lang_button.bind(on_release=next_lang)

        def voice_settings(button):
            show_info(self.open_android_settings(
                "android.settings.VOICE_INPUT_SETTINGS"
            ) or "Ochildi: Google ovoz kiritish > Oflayn tanish > til yuklang.")

        info_label = Label(
            text="", font_size=dp(14), color=MUTED,
            size_hint_y=None, height=dp(48), halign="left", valign="middle"
        )
        info_label.bind(
            size=lambda w, s: setattr(w, "text_size", (s[0] - dp(8), s[1]))
        )

        def show_info(text):
            info_label.text = text

        def memory_info(button):
            try:
                count = self.engine.memory.count()
            except Exception:
                count = 0

            show_info("Xotirada " + str(count) + " ta yozuv.")

        def memory_clear(button):
            show_info(self.engine.process("xotirani tozala"))

        def classic(button):
            show_info(selfupdate.set_ui("classic"))

        def reset(button):
            if not self.confirm_reset:
                self.confirm_reset = True
                button.text = "Aniqmi? Tasdiqlash uchun yana bosing"
                return

            show_info(selfupdate.reset_all())
            self.confirm_reset = False
            button.text = "Terminaldagi o'zgartirishlarni tiklash"

        rows.add_widget(tts_button)
        rows.add_widget(mic_button)
        rows.add_widget(lang_button)
        rows.add_widget(
            flat_button("Internetsiz mikrofon: til yuklash", voice_settings, bg=FIELD)
        )
        rows.add_widget(keyboard_button)
        rows.add_widget(flat_button("Xotira haqida", memory_info, bg=FIELD))
        rows.add_widget(flat_button("Xotirani tozalash", memory_clear, bg=FIELD))
        rows.add_widget(
            flat_button("Klassik ko'rinishga o'tish", classic, bg=FIELD)
        )
        rows.add_widget(
            flat_button(
                "Terminaldagi o'zgartirishlarni tiklash", reset,
                bg=FIELD, color=DANGER
            )
        )
        rows.add_widget(
            flat_button(
                "Ilova haqida",
                lambda b: show_info(
                    "JARVIS, ko'rinish " + selfupdate.UI_BUILD
                    + ". " + selfupdate.status()
                ),
                bg=FIELD
            )
        )

        scroll.add_widget(rows)
        content.add_widget(scroll)
        content.add_widget(info_label)
        content.add_widget(
            flat_button("Yopish", lambda b: self.close_settings(),
                        bg=ACCENT, color=(0.02, 0.05, 0.10, 1), align="center")
        )

        self.settings_popup = Popup(
            title="Sozlamalar",
            content=content,
            size_hint=(0.94, 0.82),
            auto_dismiss=False
        )
        self.settings_popup.open()

    def open_android_settings(self, action):
        try:
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            PythonActivity.mActivity.startActivity(Intent(action))
            return ""
        except Exception as error:
            return "Ochib bo'lmadi: " + repr(error)[:100]

    def close_settings(self):
        if self.settings_popup is not None:
            self.settings_popup.dismiss()

        self.settings_popup = None

    MODES = ("below_target", "pan", "scale", "resize", "")

    def keyboard_mode_info(self):
        try:
            current = _window().softinput_mode or "off"
        except Exception:
            current = "noma'lum"

        return (
            "Hozirgi rejim: " + current + "\n"
            "Mumkin: below_target, pan, scale, resize, off\n"
            "Almashtirish: kb(\"resize\")"
        )

    def set_keyboard_mode(self, mode):
        mode = "" if mode in ("off", None) else str(mode)

        if mode not in self.MODES:
            return "Noto'g'ri rejim. Mumkin: below_target, pan, scale, resize, off"

        try:
            _window().softinput_mode = mode
            selfupdate.set_setting("softinput_mode", mode)
        except Exception as error:
            return "Rejimni o'rnatib bo'lmadi: " + repr(error)[:150]

        return (
            "Klaviatura rejimi: " + (mode or "off") + ". "
            "Chatdagi yozish maydonini bosib sinab ko'ring."
        )

    # --------------------------------------- JARVIS'NI QAYTA YUKLASH
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

    # -------------------------------------------------------- TERMINAL
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
            orientation="vertical", padding=dp(6), spacing=dp(6)
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

        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))

        for text, handler, color in (
            ("Ishga tushir", self.term_run, (0.08, 0.38, 0.90, 1)),
            ("Saqlash", self.term_save, (0.10, 0.50, 0.30, 1)),
            ("Tozala", self.term_clear, (0.25, 0.25, 0.30, 1)),
            ("Yopish", self.term_close, (0.50, 0.15, 0.15, 1))
        ):
            button = Button(
                text=text, font_size=dp(14),
                background_normal="", background_color=color
            )
            button.bind(on_press=handler)
            row.add_widget(button)

        up = IconButton("up", size_hint=(None, 1), width=dp(40))
        up.bind(on_release=lambda *a: self.term_history(-1))
        down = IconButton("down", size_hint=(None, 1), width=dp(40))
        down.bind(on_release=lambda *a: self.term_history(1))
        row.add_widget(up)
        row.add_widget(down)

        content.add_widget(row)
        content.add_widget(self.term_in)

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

    def term_clear(self, instance=None):
        self.term_text = ""
        self.edit_target = None

        if self.term_out is not None:
            self.term_out.text = ""

        if self.term_in is not None:
            self.term_in.text = ""

    def term_history(self, direction):
        if self.term_in is None or self.edit_target is not None:
            return

        text = self.terminal.history_step(direction)

        if text is not None:
            self.term_in.text = text

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
                ">>> sintaksis tekshiruvi\n" + self.terminal.check_syntax(code)
            )
            return

        self.term_in.text = ""
        self._term_append(self._echo(code))

        threading.Thread(
            target=self._term_worker, args=(code,), daemon=True
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
                "Avval edit('modul') yoki edit('/yo'l/fayl') deb oching."
            )
            return

        kind, name = self.edit_target
        message = self.terminal.save_edit(kind, name, self.term_in.text)
        self._term_append(message)

        if not message.startswith("Saqlab bo'lmadi"):
            self.edit_target = None
            self.term_in.text = ""

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

    # ------------------------------------------------------- HAYOT TSIKLI
    def on_pause(self):
        return True

    def on_resume(self):
        self.remove_listening_bubble()

    def on_stop(self):
        self.remove_listening_bubble()
        self._stop_speaking()

        if self.android_activity is not None:
            try:
                self.android_activity.unbind(
                    on_activity_result=self.on_activity_result
                )
            except Exception:
                pass
