
import os
import time
import mimetypes

from jnius import autoclass, cast
from kivy.clock import Clock


class ImageHandler:

    CAMERA_REQUEST = 1002
    GALLERY_REQUEST = 1003

    def __init__(self, callback=None):
        self.callback = callback
        self.current_image = None
        self.camera_path = None
        self.camera_uri = None
        self.error = None

    def get_storage_dir(self):
        try:
            from android.storage import app_storage_path
            base = app_storage_path()
        except Exception:
            base = os.path.expanduser("~")

        path = os.path.join(base, "JARVIS", "images")
        os.makedirs(path, exist_ok=True)
        return path

    def open_camera(self):
        step = "boshlash"
        try:
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            # Ichki klass: pyjnius uchun "$" bilan alohida yuklanadi
            ImagesMedia = autoclass(
                "android.provider.MediaStore$Images$Media"
            )
            ContentValues = autoclass("android.content.ContentValues")

            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            filename = "camera_" + str(int(time.time())) + ".jpg"
            step = "ContentValues"
            values = ContentValues()
            values.put("_display_name", filename)
            values.put("mime_type", "image/jpeg")
            values.put("relative_path", "Pictures/JARVIS")

            step = "MediaStore insert"

            uri = resolver.insert(
                ImagesMedia.EXTERNAL_CONTENT_URI,
                values
            )

            if uri is None:
                print("CAMERA URI CREATE ERROR")
                self.error = "Kamera uchun fayl yaratib bo'lmadi."
                return False

            self.camera_uri = uri
            self.camera_path = None

            step = "Intent"
            intent = Intent("android.media.action.IMAGE_CAPTURE")
            intent.putExtra("output", cast("android.os.Parcelable", uri))
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            step = "startActivity"
            activity.startActivityForResult(
                intent,
                self.CAMERA_REQUEST
            )

            print("CAMERA OPENED:", uri.toString())
            return True

        except Exception as error:
            print("CAMERA ERROR:", error)
            self.error = (
                "Kamera xatosi (" + step + "): " + repr(error)[:200]
            )
            self.delete_camera_uri()
            return False

    def open_gallery(self):
        try:
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            activity = PythonActivity.mActivity

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.setType("image/*")
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            activity.startActivityForResult(
                intent,
                self.GALLERY_REQUEST
            )

            print("GALLERY OPENED")
            return True

        except Exception as error:
            print("GALLERY ERROR:", error)
            self.error = "Galereya xatosi: " + str(error)
            return False

    def handle_result(self, request_code, result_code, intent):
        try:
            Activity = autoclass("android.app.Activity")

            print("ACTIVITY RESULT:", request_code, result_code)

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

    def export_to_gallery(self, path, name):
        """Rasmni telefon galereyasiga (Pictures/JARVIS) saqlaydi.

        Qaytaradi: (True, "Pictures/JARVIS/fayl.jpg") yoki (False, sabab).
        """
        output_stream = None
        step = "boshlash"

        try:
            if not os.path.exists(path):
                return False, "Rasm fayli topilmadi."

            ContentValues = autoclass("android.content.ContentValues")
            ImagesMedia = autoclass(
                "android.provider.MediaStore$Images$Media"
            )
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            resolver = PythonActivity.mActivity.getContentResolver()

            safe = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in str(name)
            ).strip("_") or "rasm"
            extension = os.path.splitext(path)[1].lower() or ".jpg"
            filename = safe + "_" + str(int(time.time())) + extension
            mime = "image/png" if extension == ".png" else "image/jpeg"

            step = "yaratish"
            values = ContentValues()
            values.put("_display_name", filename)
            values.put("mime_type", mime)
            values.put("relative_path", "Pictures/JARVIS")
            uri = resolver.insert(ImagesMedia.EXTERNAL_CONTENT_URI, values)

            if uri is None:
                return False, "Galereyada fayl yaratib bo'lmadi."

            step = "yozish"
            output_stream = resolver.openOutputStream(uri)

            with open(path, "rb") as source:
                while True:
                    chunk = source.read(16384)

                    if not chunk:
                        break

                    output_stream.write(bytearray(chunk), 0, len(chunk))

            output_stream.flush()
            return True, "Pictures/JARVIS/" + filename

        except Exception as error:
            print("EXPORT ERROR:", error)
            return False, "(" + step + ") " + repr(error)[:150]

        finally:
            try:
                if output_stream is not None:
                    output_stream.close()
            except Exception:
                pass

    def copy_stream(self, input_stream, destination):
        output_stream = None

        try:
            FileOutputStream = autoclass("java.io.FileOutputStream")
            output_stream = FileOutputStream(destination)

            buffer = bytearray(16384)

            while True:
                count = input_stream.read(buffer)

                if count == -1:
                    break

                if count > 0:
                    output_stream.write(buffer, 0, count)

            output_stream.flush()
            return True

        except Exception as error:
            print("STREAM COPY ERROR:", error)
            return False

        finally:
            try:
                if output_stream is not None:
                    output_stream.close()
            except Exception:
                pass

            try:
                if input_stream is not None:
                    input_stream.close()
            except Exception:
                pass

    def handle_camera_result(self):
        try:
            if self.camera_uri is None:
                print("CAMERA URI EMPTY")
                return False

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            input_stream = resolver.openInputStream(self.camera_uri)

            if input_stream is None:
                print("CAMERA INPUT STREAM EMPTY")
                return False

            filename = "camera_" + str(int(time.time())) + ".jpg"
            destination = os.path.join(self.get_storage_dir(), filename)

            if not self.copy_stream(input_stream, destination):
                return False

            if not os.path.exists(destination):
                print("CAMERA FILE NOT CREATED")
                return False

            if os.path.getsize(destination) <= 0:
                print("CAMERA FILE EMPTY")
                return False

            self.camera_path = destination
            return self.set_image(destination)

        except Exception as error:
            print("CAMERA SAVE ERROR:", error)
            return False

    def delete_camera_uri(self):
        try:
            if self.camera_uri is None:
                return

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            resolver.delete(self.camera_uri, None, None)
            self.camera_uri = None

        except Exception as error:
            print("CAMERA URI DELETE ERROR:", error)

    def handle_gallery_result(self, intent):
        try:
            if intent is None:
                print("GALLERY INTENT EMPTY")
                return False

            uri = intent.getData()

            if uri is None:
                print("GALLERY URI EMPTY")
                return False

            print("GALLERY URI:", uri.toString())

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            mime_type = resolver.getType(uri)

            extension = mimetypes.guess_extension(
                str(mime_type)
            ) if mime_type else None

            if not extension:
                extension = ".jpg"

            if extension == ".jpe":
                extension = ".jpg"

            filename = (
                "gallery_"
                + str(int(time.time()))
                + extension
            )

            destination = os.path.join(
                self.get_storage_dir(),
                filename
            )

            input_stream = resolver.openInputStream(uri)

            if input_stream is None:
                print("GALLERY INPUT STREAM EMPTY")
                return False

            if not self.copy_stream(input_stream, destination):
                return False

            if not os.path.exists(destination):
                print("GALLERY FILE NOT CREATED")
                return False

            if os.path.getsize(destination) <= 0:
                print("GALLERY FILE EMPTY")
                return False

            print("GALLERY FILE:", destination)
            print("GALLERY FILE SIZE:", os.path.getsize(destination))

            return self.set_image(destination)

        except Exception as error:
            print("GALLERY SAVE ERROR:", error)
            return False

    def set_image(self, path):
        if not path:
            return False

        path = str(path)

        if not os.path.exists(path):
            print("IMAGE DOES NOT EXIST:", path)
            return False

        if os.path.getsize(path) <= 0:
            print("IMAGE IS EMPTY:", path)
            return False

        self.current_image = path

        print("IMAGE FILE:", self.current_image)

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
                print("IMAGE CALLBACK SENT:", path)

        except Exception as error:
            print("IMAGE CALLBACK ERROR:", error)

    def get_image(self):
        return self.current_image

    def clear(self):
        self.current_image = None
        self.camera_path = None
        self.camera_uri = None
