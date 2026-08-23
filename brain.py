import random


class Neuron:

    def __init__(self):
        self.weight = random.uniform(-1, 1)
        self.bias = random.uniform(-1, 1)

    def predict(self, x):
        return x * self.weight + self.bias

    def train(self, x, target, learning_rate=0.1):
        prediction = self.predict(x)

        error = target - prediction

        self.weight += learning_rate * error * x
        self.bias += learning_rate * error

        return prediction, error


# =========================
# JARVIS BRAIN
# =========================

neuron = Neuron()

print("🧠 JARVIS o‘rganuvchi neyroni")
print()
print("Boshlang‘ich:")
print("Weight:", neuron.weight)
print("Bias:", neuron.bias)

# O‘quv ma'lumotlari
data = [
    (0, 0),
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8)
]

print()
print("🎓 O‘qitish boshlandi...")

for epoch in range(100):

    total_error = 0

    for x, target in data:

        prediction, error = neuron.train(x, target)

        total_error += abs(error)

    if epoch % 10 == 0:
        print(
            "Epoch:",
            epoch,
            "| Xato:",
            total_error
        )


print()
print("✅ O‘qitish tugadi!")

print()
print("Yakuniy:")
print("Weight:", neuron.weight)
print("Bias:", neuron.bias)

print()
print("🧪 Test:")

for x in [0, 1, 2, 3, 4, 5, 10]:

    result = neuron.predict(x)

    print(
        "Input:",
        x,
        "→",
        result
    )