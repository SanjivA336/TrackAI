from car import Car, CarState
import random

class Population:
    def __init__(self, track, size=100):
        self.track = track
        self.size = size
        self.cars = [Car(track) for _ in range(size)]
        self.generation = 0
        self.pcts = []

    def evaluate_fitness(self):
        # Fitness based on distance along track
        for car in self.cars:
            car.finalize_fitness()

    def select_and_breed(self):
        # Sort by fitness descending
        self.cars.sort(key=lambda c: c.score, reverse=True)
        top10 = self.cars[:max(1, self.size//10)]
        total_fitness = sum(c.score for c in top10)
        self.pcts = []
        
        next_gen = [Car(self.track, brain=top10[0].brain.clone())]  # elitism: keep best car
        for car in top10:
            n_offspring = int((car.score / total_fitness) * (self.size - 1))
            self.pcts.append((car.score / total_fitness) * 100)
            for _ in range(n_offspring):
                child_brain = car.brain.clone()
                child_brain.mutate(rate=0.1)
                next_gen.append(Car(self.track, brain=child_brain))

        # Fill up population if under size
        while len(next_gen) < self.size:
            parent = random.choice(top10)
            child_brain = parent.brain.clone()
            child_brain.mutate(rate=0.1)
            next_gen.append(Car(self.track, brain=child_brain))

        self.cars = next_gen
        self.generation += 1

    def all_done(self):
        return all(car.state == CarState.CRASHED for car in self.cars)
