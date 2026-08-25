import json
import math
import os
import random


# ==================================================
# JARVIS 5.0 BRAIN TRAINER
# ==================================================

INTENTS = [
    "greeting",
    "time",
    "youtube",
    "instagram",
    "goodbye"
]


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


HIDDEN_SIZE = 12

LEARNING_RATE = 0.5

EPOCHS = 8000


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
# TRAINING DATA
# ==================================================

DATA = [

    # --------------------------
    # GREETING
    # --------------------------

    ("salom", "greeting"),
    ("salom jarvis", "greeting"),
    ("assalomu alaykum", "greeting"),
    ("alaykum assalom", "greeting"),
    ("qandaysan", "greeting"),
    ("qandaysan jarvis", "greeting"),

    # --------------------------
    # TIME
    # --------------------------

    ("soat nechchi", "time"),
    ("soat nechi", "time"),
    ("soat necha", "time"),
    ("hozir soat nechchi", "time"),
    ("hozir soat nechi", "time"),
    ("hozir soat necha", "time"),
    ("vaqt nechchi", "time"),
    ("vaqt nechi", "time"),
    ("vaqt necha", "time"),
    ("soatni ayt", "time"),
    ("vaqtni ayt", "time"),
    ("hozirgi vaqtni ayt", "time"),

    # --------------------------
    # YOUTUBE
    # --------------------------

    ("youtube och", "youtube"),
    ("youtubeni och", "youtube"),
    ("youtube ni och", "youtube"),
    ("youtubeni ochib ber", "youtube"),
    ("youtube ochib ber", "youtube"),
    ("youtube ishga tushir", "youtube"),
    ("youtube ni ishga tushir", "youtube"),
    ("videolarni och", "youtube"),
    ("videoni och", "youtube"),

    # --------------------------
    # INSTAGRAM
    # --------------------------

    ("instagram och", "instagram"),
    ("instagramni och", "instagram"),
    ("instagram ni och", "instagram"),
    ("instagramni ochib ber", "instagram"),
    ("instagram ochib ber", "instagram"),
    ("instagram ishga tushir", "instagram"),

    # --------------------------
    # GOODBYE
    # --------------------------

    ("xayr", "goodbye"),
    ("hayr", "goodbye"),
    ("goodbye", "goodbye"),
    ("bye", "goodbye"),
    ("xayr jarvis", "goodbye"),
    ("hayr jarvis", "goodbye"),
    ("ko'rishguncha", "goodbye")
]


# ==================================================
# TEXT → VECTOR
# ==================================================

def vectorize(text):

    words = text.lower().split()

    return [
        1 if word in words else 0
        for word in WORDS
    ]


# ==================================================
# INITIALIZE NETWORK
# ==================================================

random.seed(42)


hidden_weights = [
    [
        random.uniform(-0.5, 0.5)
        for _ in WORDS
    ]
    for _ in range(HIDDEN_SIZE)
]


hidden_bias = [
    random.uniform(-0.5, 0.5)
    for _ in range(HIDDEN_SIZE)
]


output_weights = [
    [
        random.uniform(-0.5, 0.5)
        for _ in range(HIDDEN_SIZE)
    ]
    for _ in INTENTS
]


output_bias = [
    random.uniform(-0.5, 0.5)
    for _ in INTENTS
]


# ==================================================
# TRAIN
# ==================================================

print()
print("================================")
print("🧠 JARVIS BRAIN TRAINER 5.0")
print("================================")
print()

print(
    "📚 Lug‘at:",
    len(WORDS)
)

print(
    "🎯 Intent:",
    len(INTENTS)
)

print(
    "🧠 Hidden:",
    HIDDEN_SIZE
)

print(
    "📖 Training:",
    len(DATA),
    "ta misol"
)

print()


for epoch in range(EPOCHS):

    random.shuffle(DATA)

    total_error = 0.0


    for text, intent in DATA:

        inputs = vectorize(text)

        target_index = INTENTS.index(
            intent
        )


        # --------------------------
        # FORWARD: HIDDEN
        # --------------------------

        hidden = []

        for i in range(HIDDEN_SIZE):

            total = hidden_bias[i]

            for j in range(len(WORDS)):

                total += (
                    inputs[j]
                    * hidden_weights[i][j]
                )

            hidden.append(
                sigmoid(total)
            )


        # --------------------------
        # FORWARD: OUTPUT
        # --------------------------

        outputs = []

        for i in range(len(INTENTS)):

            total = output_bias[i]

            for j in range(HIDDEN_SIZE):

                total += (
                    hidden[j]
                    * output_weights[i][j]
                )

            outputs.append(
                sigmoid(total)
            )


        # --------------------------
        # OUTPUT ERROR
        # --------------------------

        output_delta = []

        for i in range(len(INTENTS)):

            target = (
                1.0
                if i == target_index
                else 0.0
            )

            error = target - outputs[i]

            total_error += abs(error)

            delta = (
                error
                * outputs[i]
                * (1 - outputs[i])
            )

            output_delta.append(
                delta
            )


        # --------------------------
        # SAVE OLD WEIGHTS
        # --------------------------

        old_output_weights = [
            row[:]
            for row in output_weights
        ]


        # --------------------------
        # UPDATE OUTPUT
        # --------------------------

        for i in range(len(INTENTS)):

            for j in range(HIDDEN_SIZE):

                output_weights[i][j] += (
                    LEARNING_RATE
                    * output_delta[i]
                    * hidden[j]
                )

            output_bias[i] += (
                LEARNING_RATE
                * output_delta[i]
            )


        # --------------------------
        # HIDDEN ERROR
        # --------------------------

        hidden_delta = []

        for j in range(HIDDEN_SIZE):

            error = 0.0

            for i in range(len(INTENTS)):

                error += (
                    output_delta[i]
                    * old_output_weights[i][j]
                )

            delta = (
                error
                * hidden[j]
                * (1 - hidden[j])
            )

            hidden_delta.append(
                delta
            )


        # --------------------------
        # UPDATE HIDDEN
        # --------------------------

        for j in range(HIDDEN_SIZE):

            for k in range(len(WORDS)):

                hidden_weights[j][k] += (
                    LEARNING_RATE
                    * hidden_delta[j]
                    * inputs[k]
                )

            hidden_bias[j] += (
                LEARNING_RATE
                * hidden_delta[j]
            )


    if epoch % 1000 == 0:

        print(
            "Epoch:",
            epoch,
            "| Xato:",
            round(total_error, 4)
        )


# ==================================================
# SAVE MODEL
# ==================================================

model = {

    "hidden_weights":
        hidden_weights,

    "hidden_bias":
        hidden_bias,

    "output_weights":
        output_weights,

    "output_bias":
        output_bias
}


with open(
    MODEL_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        model,
        file,
        ensure_ascii=False,
        indent=2
    )


print()
print("================================")
print("✅ TRAINING TUGADI")
print("================================")
print()

print(
    "💾 Model saqlandi:"
)

print(
    MODEL_FILE
)

print()

print(
    "📚 Input:",
    len(WORDS)
)

print(
    "🧠 Hidden:",
    HIDDEN_SIZE
)

print(
    "🎯 Output:",
    len(INTENTS)
)

print()

print(
    "🚀 Endi language_brain.py ni"
)

print(
    "ishga tushirish mumkin."
)