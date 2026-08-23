import json
import math
import os


# ==================================================
# JARVIS LANGUAGE BRAIN
# ==================================================

INTENTS = [
    "greeting",
    "time",
    "youtube",
    "instagram",
    "goodbye"
]


# MUHIM:
# Bu tartib eski training paytidagi sorted(words)
# tartibiga mos.
WORDS = [
    "alaykum",
    "assalomu",
    "ayt",
    "ber",
    "hayr",
    "hozir",
    "instagram",
    "instagramni",
    "ishga",
    "jarvis",
    "ko'rishguncha",
    "nechchi",
    "ni",
    "och",
    "ochib",
    "qandaysan",
    "salom",
    "soat",
    "soatni",
    "tushir",
    "vaqt",
    "vaqtni",
    "videolarni",
    "xayr",
    "youtube",
    "youtubeni"
]


MODEL_FILE = os.path.join(
    os.path.dirname(__file__),
    "jarvis_brain.json"
)


# ==================================================
# ACTIVATION
# ==================================================

def sigmoid(x):

    x = max(-60, min(60, x))

    return 1.0 / (1.0 + math.exp(-x))


# ==================================================
# TEXT → VECTOR
# ==================================================

def text_to_vector(text):

    sentence_words = text.lower().split()

    vector = []

    for word in WORDS:

        if word in sentence_words:
            vector.append(1)
        else:
            vector.append(0)

    return vector


# ==================================================
# LOAD MODEL
# ==================================================

def load_model():

    if not os.path.exists(MODEL_FILE):

        print("❌ jarvis_brain.json topilmadi!")

        return None

    try:

        with open(
            MODEL_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            model = json.load(file)

        # Model o‘lchamini tekshiramiz

        if len(model["hidden_weights"]) != 12:

            print("❌ Hidden layer o‘lchami noto‘g‘ri!")

            return None

        if len(model["hidden_weights"][0]) != 26:

            print("❌ Input layer o‘lchami noto‘g‘ri!")

            return None

        if len(model["output_weights"]) != 5:

            print("❌ Output layer o‘lchami noto‘g‘ri!")

            return None

        if len(model["output_weights"][0]) != 12:

            print("❌ Output weight o‘lchami noto‘g‘ri!")

            return None

        print("💾 Model yuklandi")
        print("⚡ Training qilinmaydi")

        return model

    except Exception as error:

        print("❌ Modelni yuklashda xato:")
        print(error)

        return None


# ==================================================
# FORWARD PASS
# ==================================================

def predict(text, model):

    inputs = text_to_vector(text)

    # --------------------------
    # HIDDEN LAYER
    # --------------------------

    hidden = []

    for i in range(12):

        total = model["hidden_bias"][i]

        for j in range(26):

            total += (
                inputs[j]
                * model["hidden_weights"][i][j]
            )

        hidden.append(
            sigmoid(total)
        )

    # --------------------------
    # OUTPUT LAYER
    # --------------------------

    outputs = []

    for i in range(5):

        total = model["output_bias"][i]

        for j in range(12):

            total += (
                hidden[j]
                * model["output_weights"][i][j]
            )

        outputs.append(
            sigmoid(total)
        )

    # Eng katta output

    best_index = outputs.index(
        max(outputs)
    )

    intent = INTENTS[best_index]

    confidence = outputs[best_index]

    return intent, confidence


# ==================================================
# TEST
# ==================================================

def run_tests(model):

    print()
    print("🧪 JARVIS BRAIN TEST")
    print()

    tests = [
        "salom",
        "soat nechchi",
        "youtube och",
        "instagramni och",
        "xayr"
    ]

    for text in tests:

        intent, confidence = predict(
            text,
            model
        )

        print(
            text,
            "→",
            intent,
            "|",
            round(confidence, 4)
        )


# ==================================================
# LIVE MODE
# ==================================================

def live_mode(model):

    print()
    print("🤖 Language Brain tayyor!")
    print("Chiqish uchun: exit")
    print()

    while True:

        text = input("Siz: ")

        if text.lower().strip() == "exit":

            print("👋 JARVIS yopildi.")

            break

        if not text.strip():

            continue

        intent, confidence = predict(
            text,
            model
        )

        print(
            "🧠 Intent:",
            intent
        )

        print(
            "📊 Ishonch:",
            round(confidence, 4)
        )


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    print("================================")
    print("🧠 JARVIS LANGUAGE BRAIN")
    print("================================")

    print()

    print(
        "📚 Lug‘at:",
        len(WORDS),
        "ta so‘z"
    )

    print(
        "🎯 Intent:",
        len(INTENTS)
    )

    print()

    model = load_model()

    if model is None:

        print()
        print(
            "❌ JARVIS ishga tushmadi."
        )

    else:

        run_tests(model)

        live_mode(model)