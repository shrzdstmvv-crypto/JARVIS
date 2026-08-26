# ==========================================================
# JARVIS 6.0
# ANDROID PERMISSION TEST
# ==========================================================

import traceback


class PermissionManager:

    def __init__(self):

        self.android = False

        try:

            from android.permissions import (
                request_permissions,
                check_permission,
                Permission
            )

            self.request_permissions = request_permissions
            self.check_permission = check_permission
            self.Permission = Permission

            self.android = True

            print(
                "✅ Android Permission API yuklandi."
            )

        except Exception as error:

            print(
                "ℹ️ Android Permission API hozircha mavjud emas."
            )

            print(
                type(error).__name__,
                error
            )

    # ======================================================
    # REQUEST
    # ======================================================

    def request(self):

        if not self.android:

            print(
                "📱 APK muhitida permission so‘raladi."
            )

            return False

        try:

            permissions = [
                self.Permission.RECORD_AUDIO,
                self.Permission.CAMERA
            ]

            self.request_permissions(
                permissions,
                self.permission_callback
            )

            print(
                "🔐 Mikrofon va kamera permissionlari so‘raldi."
            )

            return True

        except Exception as error:

            print(
                "❌ PERMISSION ERROR:",
                error
            )

            traceback.print_exc()

            return False

    # ======================================================
    # CALLBACK
    # ======================================================

    def permission_callback(
        self,
        permissions,
        grants
    ):

        print(
            "🔐 Permission natijasi:"
        )

        for permission, granted in zip(
            permissions,
            grants
        ):

            print(
                permission,
                "→",
                "GRANTED" if granted else "DENIED"
            )

    # ======================================================
    # MICROPHONE
    # ======================================================

    def microphone_allowed(self):

        if not self.android:
            return False

        try:

            return self.check_permission(
                self.Permission.RECORD_AUDIO
            )

        except Exception as error:

            print(
                "MIC PERMISSION ERROR:",
                error
            )

            return False

    # ======================================================
    # CAMERA
    # ======================================================

    def camera_allowed(self):

        if not self.android:
            return False

        try:

            return self.check_permission(
                self.Permission.CAMERA
            )

        except Exception as error:

            print(
                "CAMERA PERMISSION ERROR:",
                error
            )

            return False

    # ======================================================
    # STATUS
    # ======================================================

    def status(self):

        return {
            "android": self.android,
            "microphone": self.microphone_allowed(),
            "camera": self.camera_allowed()
        }


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 40)
    print("🔐 JARVIS PERMISSION TEST")
    print("=" * 40)

    manager = PermissionManager()

    print()
    print(
        "STATUS:"
    )

    print(
        manager.status()
    )

    print()

    manager.request()