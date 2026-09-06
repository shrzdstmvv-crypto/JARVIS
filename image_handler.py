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
        self.camera_uri = None

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

        os.makedirs(path, exist_ok=True)

        return path

    def open_camera(self):
        try:
            Intent = autoclass(
                "android.content.Intent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            MediaStore = autoclass(
                "android.provider.MediaStore"
            )

            ContentValues = autoclass(
                "android.content.ContentValues"
            )

            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            filename = (
                "camera_"
                + str(int(time.time()))
                + ".jpg"
            )

            values = ContentValues()

            values.put(
                MediaStore.Images.Media.DISPLAY_NAME,
                filename
            )

            values.put(
                MediaStore.Images.Media.MIME_TYPE,
                "image/jpeg"
            )

            values.put(
                MediaStore.Images.Media.RELATIVE_PATH,
                "Pictures/JARVIS"
            )

            uri = resolver.insert(
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                values
            )

            if uri is None:
                print("CAMERA URI CREATE ERROR")
                return False

            self.camera_uri = uri
            self.camera_path = None

            intent = Intent(
                Intent.ACTION_IMAGE_CAPTURE
            )

            intent.putExtra(
                Intent.EXTRA_OUTPUT,
                uri
            )

            intent.addFlags(
                Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )

            intent.addFlags(
                Intent.FLAG_GRANT_READ_URI_PERMISSION
            )

            activity.startActivityForResult(
                intent,
                self.CAMERA_REQUEST
            )

            print("CAMERA OPENED")
            print("CAMERA URI:", uri.toString())

            return True

        except Exception as error:
            print("CAMERA ERROR:", error)
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

            intent.setType("image/*")

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

            print("GALLERY OPENED")

            return True

        except Exception as error:
            print("GALLERY ERROR:", error)
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
                print("ACTIVITY CANCELLED")

                if request_code == self.CAMERA_REQUEST:
                    self.delete_camera_uri()

                return False

            if request_code == self.CAMERA_REQUEST:
                return self.handle_camera_result()

            if request_code == self.GALLERY_REQUEST:
                return self.handle_gallery_result(intent)

            return False

        except Exception as error:
            print("IMAGE RESULT ERROR:", error)
            return False

    def handle_camera_result(self):
        try:
            if self.camera_uri is None:
                print("CAMERA URI EMPTY")
                return False

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            input_stream = resolver.openInputStream(
                self.camera_uri
            )

            if input_stream is None:
                print("CAMERA INPUT STREAM EMPTY")
                return False

            filename = (
                "camera_"
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

            buffer = bytearray(16384)

            while True:
                count = input_stream.read(buffer)

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

            if not os.path.exists(destination):
                print(
                    "CAMERA FILE NOT CREATED"
                )
                return False

            file_size = os.path.getsize(
                destination
            )

            print(
                "CAMERA FILE:",
                destination
            )

            print(
                "CAMERA FILE SIZE:",
                file_size
            )

            if file_size <= 0:
                print("CAMERA FILE EMPTY")
                return False

            self.camera_path = destination

            return self.set_image(
                destination
            )

        except Exception as error:
            print("CAMERA SAVE ERROR:", error)
            return False

    def delete_camera_uri(self):
        try:
            if self.camera_uri is None:
                return

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            resolver.delete(
                self.camera_uri,
                None,
                None
            )

            self.camera_uri = None

        except Exception as error:
            print(
                "CAMERA URI DELETE ERROR:",
                error
            )

    def handle_gallery_result(self, intent):
        try:
            if intent is None:
                print("GALLERY INTENT EMPTY")
                return False

            uri = intent.getData()

            if uri is None:
                print("GALLERY URI EMPTY")
                return False

            print(
                "GALLERY URI:",
                uri.toString()
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity = PythonActivity.mActivity

            resolver = activity.getContentResolver()

            input_stream = resolver.openInputStream(uri)

            if input_stream is None:
                print("INPUT STREAM EMPTY")
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

            buffer = bytearray(16384)

            while True:
                count = input_stream.read(buffer)

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

            if not os.path.exists(destination):
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
                print("GALLERY FILE EMPTY")
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

    def set_image(self, path):
        if not path:
            return False

        path = str(path)

        if not os.path.exists(path):
            print(
                "IMAGE DOES NOT EXIST:",
                path
            )
            return False

        if os.path.getsize(path) <= 0:
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
                lambda dt: self.call_callback(path),
                0
            )

        return True

    def call_callback(self, path):
        try:
            if self.callback:
                self.callback(path)

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
        self.camera_uri = None