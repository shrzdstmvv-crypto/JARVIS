import os
import time

from jnius import autoclass
from kivy.clock import Clock


class ImageHandler:

    CAMERA_REQUEST = 1002
    GALLERY_REQUEST = 1003

    def __init__(self, callback=None):

        self.callback = callback
        self.current_image = None
        self.camera_path = None

    def get_storage_dir(self):

        try:

            from android.storage import app_storage_path

            base = app_storage_path()

        except Exception:

            base = os.path.expanduser("~")

        path = os.path.join(
            base,
            "JARVIS",
            "images"
        )

        os.makedirs(
            path,
            exist_ok=True
        )

        return path

    def open_camera(self):

        try:

            Intent = autoclass(
                "android.content.Intent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity = PythonActivity.mActivity

            intent = Intent(
                Intent.ACTION_IMAGE_CAPTURE
            )

            activity.startActivityForResult(
                intent,
                self.CAMERA_REQUEST
            )

            print(
                "CAMERA OPENED"
            )

            return True

        except Exception as error:

            print(
                "CAMERA ERROR:",
                error
            )

            return False

    def open_gallery(self):

        try:

            Intent = autoclass(
                "android.content.Intent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity = PythonActivity.mActivity

            intent = Intent(
                Intent.ACTION_OPEN_DOCUMENT
            )

            intent.setType(
                "image/*"
            )

            intent.addCategory(
                Intent.CATEGORY_OPENABLE
            )

            intent.addFlags(
                Intent.FLAG_GRANT_READ_URI_PERMISSION
            )

            activity.startActivityForResult(
                intent,
                self.GALLERY_REQUEST
            )

            print(
                "GALLERY OPENED"
            )

            return True

        except Exception as error:

            print(
                "GALLERY ERROR:",
                error
            )

            return False

    def handle_result(
        self,
        request_code,
        result_code,
        intent
    ):

        try:

            Activity = autoclass(
                "android.app.Activity"
            )

            print(
                "ACTIVITY RESULT:",
                request_code,
                result_code
            )

            if result_code != Activity.RESULT_OK:

                print(
                    "ACTIVITY CANCELLED"
                )

                return False

            if request_code == self.CAMERA_REQUEST:

                return self.handle_camera_result(
                    intent
                )

            if request_code == self.GALLERY_REQUEST:

                return self.handle_gallery_result(
                    intent
                )

            return False

        except Exception as error:

            print(
                "IMAGE RESULT ERROR:",
                error
            )

            return False

    def handle_camera_result(
        self,
        intent
    ):

        try:

            if intent is None:

                print(
                    "CAMERA INTENT EMPTY"
                )

                return False

            extras = intent.getExtras()

            if extras is None:

                print(
                    "CAMERA EXTRAS EMPTY"
                )

                return False

            bitmap = extras.get(
                "data"
            )

            if bitmap is None:

                print(
                    "CAMERA BITMAP EMPTY"
                )

                return False

            filename = (
                "camera_"
                + str(int(time.time()))
                + ".jpg"
            )

            path = os.path.join(
                self.get_storage_dir(),
                filename
            )

            FileOutputStream = autoclass(
                "java.io.FileOutputStream"
            )

            BitmapCompressFormat = autoclass(
                "android.graphics.Bitmap$CompressFormat"
            )

            output = FileOutputStream(
                path
            )

            bitmap.compress(
                BitmapCompressFormat.JPEG,
                95,
                output
            )

            output.flush()
            output.close()

            if not os.path.exists(
                path
            ):

                print(
                    "CAMERA FILE NOT CREATED"
                )

                return False

            if os.path.getsize(
                path
            ) <= 0:

                print(
                    "CAMERA FILE EMPTY"
                )

                return False

            print(
                "CAMERA FILE:",
                path
            )

            return self.set_image(
                path
            )

        except Exception as error:

            print(
                "CAMERA SAVE ERROR:",
                error
            )

            return False

    def handle_gallery_result(
        self,
        intent
    ):

        try:

            if intent is None:

                print(
                    "GALLERY INTENT EMPTY"
                )

                return False

            uri = intent.getData()

            if uri is None:

                print(
                    "GALLERY URI EMPTY"
                )

                return False

            print(
                "GALLERY URI:",
                uri.toString()
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity = PythonActivity.mActivity

            resolver = (
                activity.getContentResolver()
            )

            input_stream = (
                resolver.openInputStream(
                    uri
                )
            )

            if input_stream is None:

                print(
                    "INPUT STREAM EMPTY"
                )

                return False

            filename = (
                "gallery_"
                + str(int(time.time()))
                + ".jpg"
            )

            destination = os.path.join(
                self.get_storage_dir(),
                filename
            )

            FileOutputStream = autoclass(
                "java.io.FileOutputStream"
            )

            output_stream = FileOutputStream(
                destination
            )

            buffer = bytearray(
                16384
            )

            while True:

                count = input_stream.read(
                    buffer
                )

                if count == -1:
                    break

                if count > 0:

                    output_stream.write(
                        buffer,
                        0,
                        count
                    )

            output_stream.flush()
            output_stream.close()
            input_stream.close()

            if not os.path.exists(
                destination
            ):

                print(
                    "GALLERY FILE NOT CREATED"
                )

                return False

            file_size = os.path.getsize(
                destination
            )

            print(
                "GALLERY FILE:",
                destination
            )

            print(
                "GALLERY FILE SIZE:",
                file_size
            )

            if file_size <= 0:

                print(
                    "GALLERY FILE EMPTY"
                )

                return False

            return self.set_image(
                destination
            )

        except Exception as error:

            print(
                "GALLERY SAVE ERROR:",
                error
            )

            return False

    def set_image(
        self,
        path
    ):

        if not path:

            return False

        path = str(
            path
        )

        if not os.path.exists(
            path
        ):

            print(
                "IMAGE DOES NOT EXIST:",
                path
            )

            return False

        if os.path.getsize(
            path
        ) <= 0:

            print(
                "IMAGE IS EMPTY:",
                path
            )

            return False

        self.current_image = path

        print(
            "IMAGE FILE:",
            self.current_image
        )

        if self.callback:

            Clock.schedule_once(
                lambda dt: self.call_callback(
                    path
                ),
                0
            )

        return True

    def call_callback(
        self,
        path
    ):

        try:

            if self.callback:

                self.callback(
                    path
                )

                print(
                    "IMAGE CALLBACK SENT:",
                    path
                )

        except Exception as error:

            print(
                "IMAGE CALLBACK ERROR:",
                error
            )

    def get_image(self):

        return self.current_image

    def clear(self):

        self.current_image = None
        self.camera_path = None