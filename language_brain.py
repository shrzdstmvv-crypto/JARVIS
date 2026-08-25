import json
import math
import os


# ==================================================
# JARVIS LANGUAGE BRAIN 5.0
# ==================================================

INTENTS = [
    "greeting",
    "time",
    "youtube",
    "instagram",
    "goodbye"
]


# ==================================================
# VOCABULARY
# ==================================================

WORDS = [
    "salom",
    "assalomu",
    "alaykum",
    "qandaysan",
    "jarvis",

    "soat",
    "soatni",
    "nechchi",
    "nechi",
    "necha",
    "nechta",
    "vaqt",
    "vaqtni",
    "hozir",
    "ayt",
    "ber",

    "youtube",
    "youtubeni",
    "videoni",
    "videolarni",
    "och",
    "ochib",
    "ishga",

    "instagram",
    "instagramni",

    "xayr",
    "hayr",
    "goodbye",
    "bye",
    "hayrli"
]


MODEL_FILE = os.path.join(
    os.path.dirname(__file__),
    "jarvis_brain.json"
)


# ==================================================
# SIGMOID
# ==================================================

def sigmoid(x):

    x = max(-60, min(60, x))

    return 1.0 / (
        1.0 + math.exp(-x)
    )


# ==================================================
# TEXT → VECTOR
# ==================================================

def text_to_vector(text):

    words = text.lower().split()

    return [
        1 if word in words else 0
        for word in WORDS
    ]


# ==================================================
# LOAD MODEL
# ==================================================

def load_model():

    if not os.path.exists(MODEL_FILE):

        print(
            "❌ jarvis_brain.json topilmadi!"
        )

        return None

    try:

        with open(
            MODEL_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            model = json.load(file)


        # ------------------------------------------
        # MODEL STRUCTURE
        # ------------------------------------------

        if len(model["hidden_weights"]) != 12:

            print(
                "❌ Hidden layer o‘lchami noto‘g‘ri!"
            )

            return None


        if len(model["hidden_weights"][0]) != len(WORDS):

            print(
                "❌ Input layer va WORDS mos emas!"
            )

            print(
                "Model:",
                len(model["hidden_weights"][0])
            )

            print(
                "WORDS:",
                len(WORDS)
            )

            return None


        if len(model["output_weights"]) != len(INTENTS):

            print(
                "❌ Output layer o‘lchami noto‘g‘ri!"
            )

            return None


        if len(model["output_weights"][0]) != 12:

            print(
                "❌ Hidden → Output o‘lchami noto‘g‘ri!"
            )

            return None


        print("💾 Model yuklandi")

        print(
            "📚 Input:",
            len(WORDS),
            "ta so‘z"
        )

        print(
            "🧠 Hidden:",
            12
        )

        print(
            "🎯 Output:",
            len(INTENTS),
            "ta intent"
        )

        print(
            "⚡ Training qilinmaydi"
        )

        return model


    except Exception as error:

        print(
            "❌ Modelni yuklashda xato:"
        )

        print(error)

        return None


# ==================================================
# FORWARD PASS
# ==================================================

def predict(text, model):

    inputs = text_to_vector(text)


    # ----------------------------------------------
    # HIDDEN
    # ----------------------------------------------

    hidden = []

    for i in range(12):

        total = model["hidden_bias"][i]

        for j in range(len(WORDS)):

            total += (
                inputs[j]
                * model["hidden_weights"][i][j]
            )

        hidden.append(
            sigmoid(total)
        )


    # ----------------------------------------------
    # OUTPUT
    # ----------------------------------------------

    outputs = []

    for i in range(len(INTENTS)):

        total = model["output_bias"][i]

        for j in range(12):

            total += (
                hidden[j]
                * model["output_weights"][i][j]
            )

        outputs.append(
            sigmoid(total)
        )


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

        # GREETING
        "salom",
        "assalomu alaykum",
        "qandaysan jarvis",

        # TIME
        "soat nechchi",
        "soat nechi",
        "soat necha",
        "hozir soat nechchi",
        "hozir soat nechi",
        "vaqt nechchi",

        # YOUTUBE
        "youtube och",
        "youtubeni och",
        "youtubeni ochib ber",

        # INSTAGRAM
        "instagram och",
        "instagramni och",

        # GOODBYE
        "xayr",
        "hayr",
        "goodbye"
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
    print("🤖 Live test")
    print("Chiqish: exit")
    print()


    while True:

        text = input(
            "Siz: "
        )


        if text.lower().strip() == "exit":

            print(
                "👋 JARVIS yopildi."
            )

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
            round(
                confidence,
                4
            )
        )


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    print(
        "================================"
    )

    print(
        "🧠 JARVIS LANGUAGE BRAIN 5.0"
    )

    print(
        "================================"
    )


    model = load_model()


    if model is None:

        print()
        print(
            "❌ JARVIS ishga tushmadi."
        )

    else:

        run_tests(model)

        live_mode(model)