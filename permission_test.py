from kivy.app import App
from kivy.uix.button import Button
from android.permissions import request_permissions, Permission


class PermissionTest(App):

    def build(self):
        button = Button(text="🎙️ Mikrofon ruxsatini so‘rash")
        button.bind(on_press=self.ask_permission)
        return button

    def ask_permission(self, instance):
        request_permissions([Permission.RECORD_AUDIO])


if __name__ == "__main__":
    PermissionTest().run()