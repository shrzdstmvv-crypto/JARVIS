import sys
import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock


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
# IMPORT JARVIS ENGINE
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

        return (
            "JARVIS engine yuklanmadi."
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

        root = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10
        )


        # ==================================================
        # TITLE
        # ==================================================

        title = Label(
            text="🤖 JARVIS",
            font_size=32,
            size_hint_y=None,
            height=65
        )

        root.add_widget(
            title
        )


        # ==================================================
        # STATUS
        # ==================================================

        self.status = Label(
            text=(
                "🟢 JARVIS tayyor"
                if JARVIS_READY
                else
                "🔴 JARVIS engine xato"
            ),
            font_size=16,
            size_hint_y=None,
            height=35
        )

        root.add_widget(
            self.status
        )


        # ==================================================
        # OUTPUT
        # ==================================================

        scroll = ScrollView()

        self.output = Label(
            text=(
                "JARVIS ishga tayyor.\n\n"
                "Sinab ko‘ring:\n"
                "• salom\n"
                "• soat nechchi\n"
                "• youtube och\n"
                "• instagramni och\n"
                "• 25*4\n"
            ),
            font_size=18,
            halign="left",
            valign="top",
            size_hint_y=None
        )

        self.output.bind(
            texture_size=self.output.setter(
                "size"
            )
        )

        scroll.add_widget(
            self.output
        )

        root.add_widget(
            scroll
        )


        # ==================================================
        # INPUT
        # ==================================================

        self.input = TextInput(
            hint_text="Buyruqni yozing...",
            multiline=False,
            font_size=20,
            size_hint_y=None,
            height=55
        )

        self.input.bind(
            on_text_validate=self.process_command
        )

        root.add_widget(
            self.input
        )


        # ==================================================
        # BUTTON
        # ==================================================

        button = Button(
            text="▶  JARVIS",
            font_size=20,
            size_hint_y=None,
            height=60
        )

        button.bind(
            on_press=self.process_command
        )

        root.add_widget(
            button
        )


        return root


    # ==================================================
    # PROCESS COMMAND
    # ==================================================

    def process_command(
        self,
        instance
    ):

        command = (
            self.input.text
            .strip()
        )


        if not command:

            return


        # ==============================================
        # USER MESSAGE
        # ==============================================

        self.output.text += (
            "\n\nSiz: "
            + command
        )


        # ==============================================
        # JARVIS BRAIN
        # ==============================================

        try:

            response = jarvis(
                command
            )

        except Exception as error:

            response = (
                "Xatolik: "
                + str(error)
            )


        # ==============================================
        # RESPONSE
        # ==============================================

        self.output.text += (
            "\nJARVIS: "
            + response
        )


        # ==============================================
        # CLEAR INPUT
        # ==============================================

        self.input.text = ""


        # ==============================================
        # SCROLL DOWN
        # ==============================================

        Clock.schedule_once(
            self.scroll_to_bottom,
            0.1
        )


    # ==================================================
    # SCROLL
    # ==================================================

    def scroll_to_bottom(
        self,
        dt
    ):

        try:

            scroll = self.output.parent

            scroll.scroll_y = 0

        except Exception:

            pass


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    JarvisApp().run()