import ast
import datetime
import operator
import os
import webbrowser


# ==================================================
# JARVIS 5.0
# CORE ENGINE
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ==================================================
# ANDROID DETECTION
# ==================================================

ANDROID = False

try:

    from android import activity
    from android.content import Intent
    from android.net import Uri

    ANDROID = True

    print("📱 Android API aniqlandi.")

except Exception as error:

    print(
        "ℹ️ Android API mavjud emas:",
        error
    )


# ==================================================
# LANGUAGE BRAIN
# ==================================================

try:

    from language_brain import (
        load_model,
        predict
    )

    print(
        "🧠 Language Brain ulanmoqda..."
    )

    brain_model = load_model()

    if brain_model is None:

        brain_ready = False

        print(
            "❌ Language Brain tayyor emas."
        )

    else:

        brain_ready = True

        print(
            "✅ Language Brain tayyor!"
        )

except Exception as error:

    print(
        "❌ Language Brain xatosi:"
    )

    print(error)

    brain_model = None
    brain_ready = False


# ==================================================
# CALCULATOR
# ==================================================

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod
}


def evaluate(node):

    if isinstance(
        node,
        ast.Constant
    ):

        if isinstance(
            node.value,
            (int, float)
        ):

            return node.value

        raise ValueError(
            "Faqat sonlarga ruxsat beriladi."
        )


    if isinstance(
        node,
        ast.BinOp
    ):

        left = evaluate(
            node.left
        )

        right = evaluate(
            node.right
        )

        operation = OPERATORS.get(
            type(node.op)
        )

        if operation is None:

            raise ValueError(
                "Bu operator qo‘llab-quvvatlanmaydi."
            )

        return operation(
            left,
            right
        )


    if isinstance(
        node,
        ast.UnaryOp
    ):

        value = evaluate(
            node.operand
        )

        if isinstance(
            node.op,
            ast.USub
        ):

            return -value

        if isinstance(
            node.op,
            ast.UAdd
        ):

            return value


    raise ValueError(
        "Noto‘g‘ri matematik ifoda."
    )


def calculate(text):

    try:

        tree = ast.parse(
            text,
            mode="eval"
        )

        return evaluate(
            tree.body
        )

    except Exception:

        return None


# ==================================================
# ANDROID INTENT
# ==================================================

def android_intent(
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
            "❌ Android Intent xatosi:",
            error
        )

        return False


# ==================================================
# CAMERA
# ==================================================

def open_camera():

    return android_intent(
        "android.media.action.IMAGE_CAPTURE"
    )


# ==================================================
# CONTACTS
# ==================================================

def open_contacts():

    return android_intent(
        "android.intent.action.VIEW",
        "content://contacts/people/"
    )


# ==================================================
# PHONE
# ==================================================

def open_phone():

    return android_intent(
        "android.intent.action.DIAL"
    )


# ==================================================
# SMS
# ==================================================

def open_sms():

    return android_intent(
        "android.intent.action.SENDTO",
        "smsto:"
    )


# ==================================================
# MAPS
# ==================================================

def open_maps():

    return android_intent(
        "android.intent.action.VIEW",
        "geo:0,0?q="
    )


# ==================================================
# YOUTUBE
# ==================================================

def open_youtube():

    try:

        webbrowser.open(
            "https://www.youtube.com"
        )

        return True

    except Exception as error:

        print(
            "YouTube xatosi:",
            error
        )

        return False


# ==================================================
# INSTAGRAM
# ==================================================

def open_instagram():

    try:

        webbrowser.open(
            "https://www.instagram.com"
        )

        return True

    except Exception as error:

        print(
            "Instagram xatosi:",
            error
        )

        return False


# ==================================================
# ACTION ENGINE
# ==================================================

def action(intent):


    # --------------------------------------------------
    # GREETING
    # --------------------------------------------------

    if intent == "greeting":

        return (
            "Salom! Men JARVIS."
        )


    # --------------------------------------------------
    # TIME
    # --------------------------------------------------

    if intent == "time":

        now = datetime.datetime.now()

        return (
            "Hozir soat "
            + now.strftime("%H:%M")
        )


    # --------------------------------------------------
    # YOUTUBE
    # --------------------------------------------------

    if intent == "youtube":

        if open_youtube():

            return (
                "YouTube'ni ochyapman."
            )

        return (
            "YouTube'ni ochishda xatolik."
        )


    # --------------------------------------------------
    # INSTAGRAM
    # --------------------------------------------------

    if intent == "instagram":

        if open_instagram():

            return (
                "Instagram'ni ochyapman."
            )

        return (
            "Instagram'ni ochishda xatolik."
        )


    # --------------------------------------------------
    # GOODBYE
    # --------------------------------------------------

    if intent == "goodbye":

        return (
            "Xayr. JARVIS."
        )


    # --------------------------------------------------
    # ANDROID CAMERA
    # --------------------------------------------------

    if intent == "camera":

        if open_camera():

            return (
                "Kamerani ochyapman."
            )

        return (
            "Kamerani ochib bo‘lmadi."
        )


    # --------------------------------------------------
    # CONTACTS
    # --------------------------------------------------

    if intent == "contacts":

        if open_contacts():

            return (
                "Kontaktlarni ochyapman."
            )

        return (
            "Kontaktlarni ochib bo‘lmadi."
        )


    # --------------------------------------------------
    # PHONE
    # --------------------------------------------------

    if intent == "phone":

        if open_phone():

            return (
                "Telefon oynasini ochyapman."
            )

        return (
            "Telefon oynasini ochib bo‘lmadi."
        )


    # --------------------------------------------------
    # SMS
    # --------------------------------------------------

    if intent == "sms":

        if open_sms():

            return (
                "SMS oynasini ochyapman."
            )

        return (
            "SMS oynasini ochib bo‘lmadi."
        )


    # --------------------------------------------------
    # MAPS
    # --------------------------------------------------

    if intent == "maps":

        if open_maps():

            return (
                "Xaritani ochyapman."
            )

        return (
            "Xaritani ochib bo‘lmadi."
        )


    # --------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------

    return (
        "Bu buyruqni hali bilmayman."
    )


# ==================================================
# DIRECT COMMAND
# ==================================================

def direct_command(text):

    text = (
        text
        .lower()
        .strip()
    )


    # CAMERA

    if (
        "kamerani och" in text
        or "kamera och" in text
        or text == "kamera"
    ):

        return "camera"


    # CONTACTS

    if (
        "kontaktlarni och" in text
        or "kontaktni och" in text
        or "kontakt och" in text
        or text == "kontakt"
    ):

        return "contacts"


    # PHONE

    if (
        "telefonni och" in text
        or "telefon och" in text
        or text == "telefon"
    ):

        return "phone"


    # SMS

    if (
        "smsni och" in text
        or "sms och" in text
        or text == "sms"
    ):

        return "sms"


    # MAPS

    if (
        "xaritani och" in text
        or "xarita och" in text
        or text == "xarita"
    ):

        return "maps"


    return None


# ==================================================
# CALCULATOR DETECTION
# ==================================================

def try_calculator(text):

    expression = (
        text
        .lower()
        .strip()
    )


    expression = expression.replace(
        "^",
        "**"
    )


    allowed_characters = (
        "0123456789"
        "+-*/%.() "
    )


    if not expression:

        return None


    if not all(
        char in allowed_characters
        for char in expression
    ):

        return None


    if not any(
        symbol in expression
        for symbol in (
            "+",
            "-",
            "*",
            "/",
            "%",
            "**"
        )
    ):

        return None


    return calculate(
        expression
    )


# ==================================================
# MAIN JARVIS FUNCTION
# ==================================================

def jarvis(text):

    text_lower = (
        str(text)
        .lower()
        .strip()
    )


    if not text_lower:

        return (
            "Buyruq kiriting."
        )


    # ==================================================
    # DIRECT COMMAND
    # ==================================================

    direct = direct_command(
        text_lower
    )


    if direct is not None:

        return action(
            direct
        )


    # ==================================================
    # CALCULATOR
    # ==================================================

    result = try_calculator(
        text_lower
    )


    if result is not None:

        return (
            "Natija: "
            + str(result)
        )


    # ==================================================
    # LANGUAGE BRAIN
    # ==================================================

    if not brain_ready:

        return (
            "🧠 Language Brain "
            "ishlamayapti."
        )


    try:

        intent, confidence = predict(
            text_lower,
            brain_model
        )


    except Exception as error:

        print(
            "❌ Brain prediction xatosi:",
            error
        )

        return (
            "Buyruqni tushunishda "
            "xatolik yuz berdi."
        )


    # ==================================================
    # CONFIDENCE
    # ==================================================

    if confidence < 0.70:

        return (
            "Bu buyruqni hali "
            "yaxshi tushunmadim."
        )


    # ==================================================
    # ACTION
    # ==================================================

    return action(
        intent
    )


# ==================================================
# TERMINAL MODE
# ==================================================

def terminal_mode():

    print()
    print(
        "========================================"
    )
    print(
        "🤖 JARVIS 5.0"
    )
    print(
        "========================================"
    )

    print(
        "🧠 Language Brain"
    )

    print(
        "⚙️ Action Engine"
    )

    print(
        "📱 Android Ready"
    )

    print()

    print(
        "🚀 JARVIS tayyor!"
    )

    print(
        "Chiqish uchun: exit"
    )

    print()


    while True:

        try:

            text = input(
                "Siz: "
            )

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print()
            print(
                "JARVIS: Xayr!"
            )

            break


        if (
            text
            .lower()
            .strip()
            == "exit"
        ):

            print(
                "JARVIS: Xayr!"
            )

            break


        response = jarvis(
            text
        )


        print(
            "JARVIS:",
            response
        )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    terminal_mode()