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
from kivy.graphics import Color, RoundedRectangle


# ==================================================
# JARVIS PATH
# ==================================================

JARVIS_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if JARVIS_DIR not in sys.path:

    sys.path.insert(
        0,
        JARVIS_DIR
    )


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

try:

    from android import activity
    from android.content import Intent
    from android.net import Uri

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
# ANDROID INTENT
# ==================================================

def open_android_intent(
    action,
    uri=None,
    mime_type=None
):

    if not ANDROID:

        return False

    try:

        intent = Intent(
            action
        )

        if uri is not None:

            intent.setData(
                Uri.parse(uri)
            )

        if mime_type is not None:

            intent.setType(
                mime_type
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
            "Android Intent xatosi:",
            error
        )

        return False


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

        intent.addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK
        )

        activity.startActivity(
            intent
        )

        return True

    except Exception as error:

        print(
            "Speech xatosi:",
            error
        )

        return False


# ==================================================
# CHAT BUBBLE
# ==================================================

class ChatBubble(BoxLayout):

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
            dp(15),
            dp(11)
        )

        self.spacing = dp(3)

        self.is_user = is_user


        # ==========================================
        # TEXT
        # ==========================================

        self.label = Label(
            text=str(text),
            font_size=dp(19),
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
            texture_size=self.text_size_changed
        )

        self.add_widget(
            self.label
        )


        # ==========================================
        # BACKGROUND
        # ==========================================

        with self.canvas.before:

            if self.is_user:

                Color(
                    0.10,
                    0.35,
                    0.65,
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
                radius=[
                    dp(18)
                ]
            )


        self.bind(
            pos=self.update_background,
            size=self.update_background
        )


        Clock.schedule_once(
            self.refresh,
            0
        )


    def text_size_changed(
        self,
        instance,
        size
    ):

        instance.text_size = (
            dp(320),
            None
        )

        self.height = (
            size[1]
            + dp(24)
        )


    def update_background(
        self,
        instance,
        value
    ):

        self.background.pos = self.pos

        self.background.size = self.size


    def refresh(
        self,
        dt
    ):

        self.label.text_size = (
            dp(320),
            None
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


        # ==============================================
        # ROOT
        # ==============================================

        root = BoxLayout(
            orientation="vertical"
        )


        # ==============================================
        # HEADER
        # ==============================================

        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(78),
            padding=(
                dp(18),
                dp(7)
            )
        )


        title = Label(
            text="🤖 JARVIS",
            font_size=dp(28),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(42)
        )


        status = Label(
            text=(
                "● Online"
                if JARVIS_READY
                else
                "● Engine xatosi"
            ),
            font_size=dp(14),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(24)
        )


        header.add_widget(
            title
        )

        header.add_widget(
            status
        )

        root.add_widget(
            header
        )


        # ==============================================
        # CHAT
        # ==============================================

        self.scroll = ScrollView(
            do_scroll_x=False
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


        root.add_widget(
            self.scroll
        )


        # ==============================================
        # INPUT BAR
        # ==============================================

        bottom = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(70),
            spacing=dp(5),
            padding=dp(7)
        )


        # ==============================================
        # GALLERY BUTTON
        # ==============================================

        gallery_button = Button(
            text="🖼️",
            font_size=dp(21),
            size_hint_x=None,
            width=dp(52)
        )

        gallery_button.bind(
            on_press=self.gallery_pressed
        )

        bottom.add_widget(
            gallery_button
        )


        # ==============================================
        # CAMERA BUTTON
        # ==============================================

        camera_button = Button(
            text="📷",
            font_size=dp(21),
            size_hint_x=None,
            width=dp(52)
        )

        camera_button.bind(
            on_press=self.camera_pressed
        )

        bottom.add_widget(
            camera_button
        )


        # ==============================================
        # TEXT INPUT
        # ==============================================

        self.input = TextInput(
            hint_text="Xabar yozing...",
            multiline=False,
            font_size=dp(19),
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


        # ==============================================
        # MICROPHONE
        # ==============================================

        mic_button = Button(
            text="🎤",
            font_size=dp(21),
            size_hint_x=None,
            width=dp(52)
        )


        mic_button.bind(
            on_press=self.microphone_pressed
        )


        bottom.add_widget(
            mic_button
        )


        # ==============================================
        # SEND
        # ==============================================

        send_button = Button(
            text="➤",
            font_size=dp(23),
            size_hint_x=None,
            width=dp(52)
        )


        send_button.bind(
            on_press=self.send_message
        )


        bottom.add_widget(
            send_button
        )


        root.add_widget(
            bottom
        )


        # ==============================================
        # WELCOME
        # ==============================================

        Clock.schedule_once(
            self.show_welcome,
            0.3
        )


        return root


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

        bubble = ChatBubble(
            text=str(text),
            is_user=is_user
        )


        self.chat.add_widget(
            bubble
        )


        Clock.schedule_once(
            self.scroll_bottom,
            0.15
        )


    # ==================================================
    # SEND MESSAGE
    # ==================================================

    def send_message(
        self,
        instance=None
    ):

        command = (
            self.input.text
            .strip()
        )


        if not command:

            return


        self.input.text = ""


        # ==============================================
        # USER
        # ==============================================

        self.add_message(
            command,
            True
        )


        self.memory.append(
            {
                "role": "user",
                "text": command,
                "time": datetime.now().isoformat()
            }
        )


        # ==============================================
        # JARVIS
        # ==============================================

        try:

            response = jarvis(
                command
            )

        except Exception as error:

            response = (
                "Xatolik yuz berdi: "
                + str(error)
            )


        self.add_message(
            response,
            False
        )


        # ==============================================
        # MEMORY
        # ==============================================

        self.memory.append(
            {
                "role": "jarvis",
                "text": str(response),
                "time": datetime.now().isoformat()
            }
        )


        save_memory(
            self.memory
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
                "🎤 Tinglayapman...",
                False
            )

        else:

            self.add_message(
                "🎤 Ovozli boshqaruv "
                "Android APK ichida ishlaydi.",
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