import datetime
import webbrowser
import ast
import operator
import os


# ==================================================
# JARVIS 5.0
# Android / Kivy Ready
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==================================================
# LANGUAGE BRAIN
# ==================================================

try:
    from language_brain import load_model, predict

    print("🧠 Language Brain ulanmoqda...")

    brain_model = load_model()

    if brain_model is None:
        print("❌ Language Brain yuklanmadi!")
        brain_ready = False
    else:
        print("✅ Language Brain tayyor!")
        brain_ready = True

except Exception as error:
    print("❌ Language Brain xatosi:")
    print(error)

    brain_model = None
    brain_ready = False


# ==================================================
# CALCULATOR
# ==================================================

operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod
}


def evaluate(node):

    if isinstance(node, ast.Constant):

        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError()


    if isinstance(node, ast.BinOp):

        left = evaluate(node.left)
        right = evaluate(node.right)

        operation = operators.get(type(node.op))

        if operation is None:
            raise ValueError()

        return operation(left, right)


    if isinstance(node, ast.UnaryOp):

        value = evaluate(node.operand)

        if isinstance(node.op, ast.USub):
            return -value

        if isinstance(node.op, ast.UAdd):
            return value

    raise ValueError()


def calculate(text):

    try:

        tree = ast.parse(
            text,
            mode="eval"
        )

        return evaluate(tree.body)

    except Exception:

        return None


# ==================================================
# ACTION ENGINE
# ==================================================

def action(intent):

    if intent == "greeting":

        return "Salom! Men JARVIS."


    if intent == "time":

        now = datetime.datetime.now()

        return "Hozir soat " + now.strftime("%H:%M")


    if intent == "youtube":

        try:

            webbrowser.open(
                "https://www.youtube.com"
            )

            return "YouTube'ni ochyapman."

        except Exception:

            return "YouTube'ni ochishda xatolik."


    if intent == "instagram":

        try:

            webbrowser.open(
                "https://www.instagram.com"
            )

            return "Instagram'ni ochyapman."

        except Exception:

            return "Instagram'ni ochishda xatolik."


    if intent == "goodbye":

        return "Xayr. JARVIS."


    return "Bu buyruqni hali bilmayman."


# ==================================================
# MAIN JARVIS FUNCTION
# ==================================================

def jarvis(text):

    text_lower = text.lower().strip()


    if not text_lower:

        return "Buyruq kiriting."


    # ==================================================
    # CALCULATOR
    # ==================================================

    if any(
        symbol in text_lower
        for symbol in ["+", "-", "*", "/", "%", "^"]
    ):

        expression = text_lower.replace("^", "**")

        result = calculate(expression)

        if result is not None:

            return "Natija: " + str(result)


    # ==================================================
    # LANGUAGE BRAIN
    # ==================================================

    if not brain_ready:

        return "🧠 Language Brain ishlamayapti."


    try:

        intent, confidence = predict(
            text_lower,
            brain_model
        )

    except Exception as error:

        print(
            "Brain prediction error:",
            error
        )

        return "Buyruqni tushunishda xatolik yuz berdi."


    # ==================================================
    # CONFIDENCE
    # ==================================================

    if confidence < 0.70:

        return "Bu buyruqni hali yaxshi tushunmadim."


    # ==================================================
    # ACTION
    # ==================================================

    response = action(intent)

    return (
        response
        + " [🧠 "
        + intent
        + ": "
        + f"{confidence:.2f}]"
    )


# ==================================================
# TERMINAL MODE
# ==================================================

def terminal_mode():

    print()
    print("========================================")
    print("🤖 JARVIS 5.0")
    print("========================================")
    print("🧠 Language Brain")
    print("⚙️ Action Engine")
    print("📱 Android Ready")
    print()

    print("🚀 JARVIS tayyor!")
    print("Chiqish uchun: exit")
    print()


    while True:

        try:

            text = input("Siz: ")

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print()
            print("JARVIS: Xayr!")

            break


        if text.lower().strip() == "exit":

            print("JARVIS: Xayr!")

            break


        response = jarvis(text)

        print(
            "JARVIS:",
            response
        )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    terminal_mode()