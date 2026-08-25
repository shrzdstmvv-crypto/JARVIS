import sys
import os
import json
from datetime import datetime

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

from kivy.graphics import Color
from kivy.graphics import RoundedRectangle


# ==================================================
# JARVIS PATH
# ==================================================

JARVIS_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if JARVIS_DIR not in sys.path:
    sys.path.insert(0, JARVIS_DIR)


# ==================================================
# JARVIS ENGINE
# ==================================================

try:

    from jarvis import jarvis

    JARVIS_READY = True

except Exception as error:

    print(
        "JARVIS import xatosi:",
        error
    )

    JARVIS_READY = False

    def jarvis(text):
        return "JARVIS engine yuklanmadi."


# ==================================================
# ANDROID
# ==================================================

ANDROID = False
PythonActivity = None

try:

    from android import activity

    from android.content import Intent

    from android.net import Uri

    from jnius import autoclass

    PythonActivity = autoclass(
        "org.kivy.android.PythonActivity"
    )

    ANDROID = True

    print(
        "📱 Android API tayyor."
    )

except Exception as error:

    print(
        "ℹ️ Android API mavjud emas:",
        error
    )


# ==================================================
# SPEECH REQUEST CODE
# ==================================================

SPEECH_REQUEST_CODE = 5001


# ==================================================
# MEMORY
# ==================================================

MEMORY_FILE = os.path.join(
    JARVIS_DIR,
    "jarvis_memory.json"
)


def load_memory():

    if not os.path.exists(
        MEMORY_FILE
    ):

        return []

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(
            data,
            list
        ):

            return data

    except Exception as error:

        print(
            "Memory yuklash xatosi:",
            error
        )

    return []


def save_memory(
    memory
):

    try:

        with open(
            MEMORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                memory,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as error:

        print(
            "Memory saqlash xatosi:",
            error
        )


# ==================================================
# CAMERA
# ==================================================

def open_camera():

    if not ANDROID:

        print(
            "📷 Kamera: Android APK kerak."
        )

        return False

    try:

        intent = Intent(
            "android.media.action.IMAGE_CAPTURE"
        )

        intent.addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK
        )

        activity.startActivity(
            intent
        )

        return True

    except Exception as error:

        print(
            "Camera xatosi:",
            error
        )

        return False


# ==================================================
# GALLERY
# ==================================================

def open_gallery():

    if not ANDROID:

        print(
            "🖼️ Galereya: Android APK kerak."
        )

        return False

    try:

        intent = Intent(
            "android.intent.action.PICK"
        )

        intent.setType(
            "image/*"
        )

        intent.addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK
        )

        activity.startActivity(
            intent
        )

        return True

    except Exception as error:

        print(
            "Gallery xatosi:",
            error
        )

        return False


# ==================================================
# SPEECH
# ==================================================

def start_speech():

    if not ANDROID:

        print(
            "🎤 Speech: Android APK kerak."
        )

        return False

    try:

        intent = Intent(
            "android.speech.action.RECOGNIZE_SPEECH"
        )

        intent.putExtra(
            "android.speech.extra.LANGUAGE_MODEL",
            "free_form"
        )

        intent.putExtra(
            "android.speech.extra.PROMPT",
            "JARVIS tinglamoqda..."
        )

        # O'zbek tilini so'raymiz
        intent.putExtra(
            "android.speech.extra.LANGUAGE",
            "uz-UZ"
        )

        intent.putExtra(
            "android.speech.extra.MAX_RESULTS",
            5
        )

        PythonActivity.mActivity.startActivityForResult(
            intent,
            SPEECH_REQUEST_CODE
        )

        return True

    except Exception as error:

        print(
            "Speech xatosi:",
            error
        )

        return False


# ==================================================
# MESSAGE BUBBLE
# ==================================================

class MessageBubble(BoxLayout):

    def __init__(
        self,
        text,
        is_user=False,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.orientation = "vertical"

        self.size_hint_y = None

        self.padding = (
            dp(16),
            dp(11),
            dp(16),
            dp(11)
        )

        self.spacing = dp(2)

        self.is_user = is_user


        # ==========================================
        # TEXT
        # ==========================================

        self.label = Label(

            text=str(text),

            font_size=dp(18),

            color=(
                1,
                1,
                1,
                1
            ),

            halign="left",

            valign="middle",

            size_hint_y=None
        )


        self.label.bind(
            texture_size=self.update_height
        )


        self.add_widget(
            self.label
        )


        # ==========================================
        # BUBBLE
        # ==========================================

        with self.canvas.before:

            if self.is_user:

                # USER = BLUE

                Color(
                    0.08,
                    0.38,
                    0.90,
                    1
                )

            else:

                # JARVIS = DARK

                Color(
                    0.18,
                    0.18,
                    0.20,
                    1
                )

            self.background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[
                    dp(18)
                ]
            )


        self.bind(
            pos=self.update_background,
            size=self.update_background
        )


    def update_height(
        self,
        instance,
        size
    ):

        self.label.text_size = (
            dp(320),
            None
        )

        self.height = (
            size[1] +
            dp(22)
        )


    def update_background(
        self,
        instance,
        value
    ):

        self.background.pos = self.pos

        self.background.size = self.size


# ==================================================
# MENU
# ==================================================

class MenuPanel(BoxLayout):

    def __init__(
        self,
        close_callback,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.orientation = "vertical"

        self.padding = dp(18)

        self.spacing = dp(10)


        # ==========================================
        # MENU TITLE
        # ==========================================

        title = Label(

            text="☰  MENYU",

            font_size=dp(25),

            size_hint_y=None,

            height=dp(55),

            halign="left"
        )

        self.add_widget(
            title
        )


        # ==========================================
        # MENU ITEMS
        # ==========================================

        items = [

            "🏠  Bosh sahifa",

            "🧠  Brain",

            "🎙️  Ovoz",

            "🧠  Memory",

            "⚙️  Sozlamalar",

            "ℹ️  JARVIS haqida"

        ]


        for item in items:

            button = Button(

                text=item,

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

            self.add_widget(
                button
            )


        # ==========================================
        # CLOSE
        # ==========================================

        close = Button(

            text="✕  Yopish",

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
            on_press=lambda x:
            close_callback()
        )

        self.add_widget(
            close
        )


# ==================================================
# JARVIS APP
# ==================================================

class JarvisApp(App):


    # ==================================================
    # BUILD
    # ==================================================

    def build(self):

        self.title = "JARVIS"

        self.memory = load_memory()


        # ==========================================
        # ANDROID SPEECH CALLBACK
        # ==========================================

        if ANDROID:

            try:

                activity.bind(
                    on_activity_result=
                    self.on_activity_result
                )

                print(
                    "🎙️ Speech callback tayyor."
                )

            except Exception as error:

                print(
                    "Speech callback xatosi:",
                    error
                )


        # ==========================================
        # ROOT
        # ==========================================

        self.root_layout = BoxLayout(
            orientation="vertical"
        )


        # ==========================================
        # TOP BAR
        # ==========================================

        top = BoxLayout(

            orientation="horizontal",

            size_hint_y=None,

            height=dp(58),

            padding=(
                dp(8),
                dp(5)
            )
        )


        # ==========================================
        # MENU BUTTON
        # ==========================================

        menu_button = Button(

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


        menu_button.bind(
            on_press=self.open_menu
        )


        top.add_widget(
            menu_button
        )


        # ==========================================
        # EMPTY CENTER
        # ==========================================

        top.add_widget(
            Label(
                text=""
            )
        )


        self.root_layout.add_widget(
            top
        )


        # ==========================================
        # CHAT
        # ==========================================

        self.scroll = ScrollView(

            do_scroll_x=False,

            bar_width=dp(3)
        )


        self.chat = GridLayout(

            cols=1,

            spacing=dp(10),

            padding=(
                dp(12),
                dp(12)
            ),

            size_hint_y=None
        )


        self.chat.bind(
            minimum_height=
            self.chat.setter(
                "height"
            )
        )


        self.scroll.add_widget(
            self.chat
        )


        self.root_layout.add_widget(
            self.scroll
        )


        # ==========================================
        # BOTTOM
        # ==========================================

        bottom = BoxLayout(

            orientation="horizontal",

            size_hint_y=None,

            height=dp(68),

            spacing=dp(5),

            padding=dp(7)
        )


        # ==========================================
        # GALLERY
        # ==========================================

        gallery = Button(

            text="🖼️",

            font_size=dp(20),

            size_hint_x=None,

            width=dp(50)
        )


        gallery.bind(
            on_press=self.gallery_pressed
        )


        bottom.add_widget(
            gallery
        )


        # ==========================================
        # CAMERA
        # ==========================================

        camera = Button(

            text="📷",

            font_size=dp(20),

            size_hint_x=None,

            width=dp(50)
        )


        camera.bind(
            on_press=self.camera_pressed
        )


        bottom.add_widget(
            camera
        )


        # ==========================================
        # TEXT INPUT
        # ==========================================

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
            on_text_validate=
            self.send_message
        )


        bottom.add_widget(
            self.input
        )


        # ==========================================
        # MICROPHONE
        # ==========================================

        mic = Button(

            text="🎙️",

            font_size=dp(20),

            size_hint_x=None,

            width=dp(50)
        )


        mic.bind(
            on_press=
            self.microphone_pressed
        )


        bottom.add_widget(
            mic
        )


        # ==========================================
        # SEND BLUE
        # ==========================================

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
            on_press=
            self.send_message
        )


        bottom.add_widget(
            send
        )


        self.root_layout.add_widget(
            bottom
        )


        # ==========================================
        # WELCOME
        # ==========================================

        Clock.schedule_once(
            self.show_welcome,
            0.3
        )


        return self.root_layout


    # ==================================================
    # WELCOME
    # ==================================================

    def show_welcome(
        self,
        dt
    ):

        self.add_message(

            "Salom! Men JARVIS.\n"
            "Sizga yordam berishga tayyorman.",

            False
        )


    # ==================================================
    # ADD MESSAGE
    # ==================================================

    def add_message(
        self,
        text,
        is_user=False
    ):

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


    # ==================================================
    # PROCESS COMMAND
    # ==================================================

    def process_command(
        self,
        command
    ):

        command = command.strip()

        if not command:
            return


        # ==========================================
        # USER MESSAGE
        # ==========================================

        self.add_message(
            command,
            True
        )


        # ==========================================
        # MEMORY
        # ==========================================

        self.memory.append({

            "role": "user",

            "text": command,

            "time":
            datetime.now().isoformat()

        })


        # ==========================================
        # JARVIS ENGINE
        # ==========================================

        try:

            response = jarvis(
                command
            )

        except Exception as error:

            response = (
                "Xatolik yuz berdi: "
                + str(error)
            )


        # ==========================================
        # JARVIS MESSAGE
        # ==========================================

        self.add_message(
            response,
            False
        )


        # ==========================================
        # MEMORY
        # ==========================================

        self.memory.append({

            "role": "jarvis",

            "text": str(response),

            "time":
            datetime.now().isoformat()

        })


        save_memory(
            self.memory
        )


    # ==================================================
    # SEND TEXT MESSAGE
    # ==================================================

    def send_message(
        self,
        instance=None
    ):

        command = (
            self.input.text.strip()
        )


        if not command:
            return


        self.input.text = ""


        self.process_command(
            command
        )


    # ==================================================
    # MICROPHONE
    # ==================================================

    def microphone_pressed(
        self,
        instance
    ):

        if start_speech():

            self.add_message(
                "🎙️ Tinglayapman...",
                False
            )

        else:

            self.add_message(

                "🎙️ Ovozli boshqaruv "
                "Android APK ichida ishlaydi.",

                False
            )


    # ==================================================
    # SPEECH RESULT
    # ==================================================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != SPEECH_REQUEST_CODE:

            return


        if intent is None:

            return


        try:

            results = intent.getStringArrayListExtra(
                "android.speech.extra.RESULTS"
            )


            if results is None:

                self.add_message(
                    "🎙️ Ovoz aniqlanmadi.",
                    False
                )

                return


            if results.size() == 0:

                self.add_message(
                    "🎙️ Ovoz aniqlanmadi.",
                    False
                )

                return


            # ======================================
            # FIRST RESULT
            # ======================================

            text = str(
                results.get(0)
            ).strip()


            if not text:

                return


            print(
                "🎙️ Siz:",
                text
            )


            # ======================================
            # REMOVE "TINGLAYAPMAN" MESSAGE
            # ======================================

            try:

                if len(self.chat.children) > 0:

                    widget = self.chat.children[0]

                    if isinstance(
                        widget,
                        MessageBubble
                    ):

                        if (
                            widget.label.text
                            ==
                            "🎙️ Tinglayapman..."
                        ):

                            self.chat.remove_widget(
                                widget
                            )

            except Exception:

                pass


            # ======================================
            # PROCESS VOICE COMMAND
            # ======================================

            self.process_command(
                text
            )


        except Exception as error:

            print(
                "🎙️ Voice result xatosi:",
                error
            )


            self.add_message(

                "🎙️ Ovozni "
                "tushunishda xatolik.",

                False
            )


    # ==================================================
    # CAMERA
    # ==================================================

    def camera_pressed(
        self,
        instance
    ):

        if open_camera():

            self.add_message(
                "📷 Kamera ochildi.",
                False
            )

        else:

            self.add_message(

                "📷 Kamera Android APK "
                "ichida ishlaydi.",

                False
            )


    # ==================================================
    # GALLERY
    # ==================================================

    def gallery_pressed(
        self,
        instance
    ):

        if open_gallery():

            self.add_message(
                "🖼️ Galereya ochildi.",
                False
            )

        else:

            self.add_message(

                "🖼️ Galereya Android APK "
                "ichida ishlaydi.",

                False
            )


    # ==================================================
    # MENU
    # ==================================================

    def open_menu(
        self,
        instance
    ):

        panel = MenuPanel(
            self.close_menu
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


    def close_menu(
        self
    ):

        if hasattr(
            self,
            "menu_popup"
        ):

            self.menu_popup.dismiss()


    # ==================================================
    # SCROLL
    # ==================================================

    def scroll_bottom(
        self,
        dt
    ):

        try:

            self.scroll.scroll_y = 0

        except Exception:

            pass


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    JarvisApp().run()