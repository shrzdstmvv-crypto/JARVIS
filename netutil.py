
import os
import urllib.request

try:
    import ssl
except ImportError:  # ssl bo'lmasa, faqat oddiy ulanish ishlaydi
    ssl = None

ANDROID_CERTS = "/system/etc/security/cacerts"


def _contexts():
    """HTTPS tekshiruvi uchun ketma-ket urinib ko'riladigan sozlamalar."""
    yield None  # standart

    if ssl is None:
        return

    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    # Android'ning o'z ishonchli sertifikatlari papkasi
    if os.path.isdir(ANDROID_CERTS):
        try:
            yield ssl.create_default_context(capath=ANDROID_CERTS)
        except Exception:
            pass


def fetch(url, timeout=12):
    """URL dan baytlarni oladi. Sertifikat xatosi bo'lsa, boshqa sozlama bilan urinadi."""
    request = urllib.request.Request(str(url), headers={"User-Agent": "JARVIS"})
    last = None

    for context in _contexts():
        try:
            with urllib.request.urlopen(
                request, timeout=timeout, context=context
            ) as response:
                return response.read()
        except Exception as error:
            last = error

    raise last if last is not None else RuntimeError("Ulanib bo'lmadi")
