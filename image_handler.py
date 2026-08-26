class ImageHandler:

    def __init__(self, callback=None):
        self.callback = callback
        self.current_image = None

    # ======================================================
    # CAMERA
    # APK BOSQICHIDA ANDROID CAMERA API BILAN ULANADI
    # ======================================================

    def open_camera(self):
        print("📷 Camera: APK bosqichida Android Camera API ulanadi.")
        return False

    # ======================================================
    # GALLERY
    # APK BOSQICHIDA ANDROID FILE PICKER BILAN ULANADI
    # ======================================================

    def open_gallery(self):
        print("🖼️ Gallery: APK bosqichida Android File Picker ulanadi.")
        return False

    # ======================================================
    # IMAGE
    # ======================================================

    def set_image(self, path):

        if not path:
            return False

        self.current_image = str(path)

        print(
            "🖼️ Selected image:",
            self.current_image
        )

        if self.callback:

            try:
                self.callback(
                    self.current_image
                )

            except Exception as error:

                print(
                    "IMAGE CALLBACK ERROR:",
                    error
                )

        return True

    # ======================================================
    # GET IMAGE
    # ======================================================

    def get_image(self):
        return self.current_image

    # ======================================================
    # CLEAR IMAGE
    # ======================================================

    def clear(self):
        self.current_image = None