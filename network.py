import random
import math


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def sigmoid_derivative(x):
    return x * (1 - x)


class NeuralNetwork:

    def __init__(self):
        # 2 input → 3 hidden → 1 output

        self.hidden_weights = [
            [random.uniform(-1, 1), random.uniform(-1, 1)]
            for _ in range(3)
        ]

        self.hidden_bias = [
            random.uniform(-1, 1)
            for _ in range(3)
        ]

        self.output_weights = [
            random.uniform(-1, 1)
            for _ in range(3)
        ]

        self.output_bias = random.uniform(-1, 1)

    def forward(self, inputs):

        hidden = []

        for i in range(3):

            total = (
                inputs[0] * self.hidden_weights[i][0]
                + inputs[1] * self.hidden_weights[i][1]
                + self.hidden_bias[i]
            )

            hidden.append(sigmoid(total))

        output_total = self.output_bias

        for i in range(3):
            output_total += hidden[i] * self.output_weights[i]

        output = sigmoid(output_total)

        return hidden, output

    def train(self, inputs, target, learning_rate=1.0):

        hidden, output = self.forward(inputs)

        # Output xatosi
        output_error = target - output

        # Output gradient
        output_delta = (
            output_error *
            sigmoid_derivative(output)
        )

        # Eski output weights'larni saqlaymiz
        old_output_weights = self.output_weights[:]

        # Output layer'ni yangilash
        for i in range(3):
            self.output_weights[i] += (
                learning_rate *
                output_delta *
                hidden[i]
            )

        self.output_bias += (
            learning_rate *
            output_delta
        )

        # Hidden layer'ni yangilash
        for i in range(3):

            hidden_error = (
                output_delta *
                old_output_weights[i]
            )

            hidden_delta = (
                hidden_error *
                sigmoid_derivative(hidden[i])
            )

            self.hidden_weights[i][0] += (
                learning_rate *
                hidden_delta *
                inputs[0]
            )

            self.hidden_weights[i][1] += (
                learning_rate *
                hidden_delta *
                inputs[1]
            )

            self.hidden_bias[i] += (
                learning_rate *
                hidden_delta
            )

        return output, output_error


# =================================
# JARVIS BRAIN
# =================================

network = NeuralNetwork()

# XOR training data
data = [
    ([0, 0], 0),
    ([0, 1], 1),
    ([1, 0], 1),
    ([1, 1], 0)
]

print("🧠 JARVIS Neural Network")
print()
print("🎓 XOR o‘qitish boshlandi...")

for epoch in range(10000):

    total_error = 0

    for inputs, target in data:

        output, error = network.train(
            inputs,
            target
        )

        total_error += abs(error)

    if epoch % 1000 == 0:

        print(
            "Epoch:",
            epoch,
            "| Xato:",
            total_error
        )


print()
print("✅ O‘qitish tugadi!")

print()
print("🧪 TEST:")
print()

for inputs, target in data:

    hidden, output = network.forward(inputs)

    print(
        inputs,
        "→",
        round(output, 4),
        "| Kerak:",
        target
    )