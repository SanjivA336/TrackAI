import random
import math

class NeuralNetwork:
    def __init__(self, input_size, hidden_size, output_size):
        # Initialize weights randomly
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # weights: input -> hidden
        self.w1 = [[random.uniform(-1, 1) for _ in range(hidden_size)] for _ in range(input_size)]
        # weights: hidden -> output
        self.w2 = [[random.uniform(-1, 1) for _ in range(output_size)] for _ in range(hidden_size)]

    def forward(self, inputs):
        # Simple sigmoid activation
        hidden = [0.0] * self.hidden_size
        for i in range(self.hidden_size):
            hidden[i] = sum(inputs[j] * self.w1[j][i] for j in range(self.input_size))
            hidden[i] = math.tanh(hidden[i])  # output in [-1,1]

        outputs = [0.0] * self.output_size
        for i in range(self.output_size):
            outputs[i] = sum(hidden[j] * self.w2[j][i] for j in range(self.hidden_size))
            outputs[i] = math.tanh(outputs[i])  # output in [-1,1]

        return outputs

    def clone(self):
        # Create a copy of the network
        clone = NeuralNetwork(self.input_size, self.hidden_size, self.output_size)
        clone.w1 = [row[:] for row in self.w1]
        clone.w2 = [row[:] for row in self.w2]
        return clone

    def mutate(self, rate=0.1):
        # Small random changes to weights
        for i in range(self.input_size):
            for j in range(self.hidden_size):
                if random.random() < rate:
                    self.w1[i][j] += random.uniform(-0.5, 0.5)
        for i in range(self.hidden_size):
            for j in range(self.output_size):
                if random.random() < rate:
                    self.w2[i][j] += random.uniform(-0.5, 0.5)
