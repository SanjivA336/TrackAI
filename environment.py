from car import Car, CarState
import random


class Population:
    def __init__(self, track, size=100):
        # --- Population state ---
        self.track = track
        self.size = size
        self.cars = [Car(track) for _ in range(size)]
        self.generation = 0
        self.pcts = []

    # ================= Fitness =================
    def evaluate_fitness(self):
        """Calculate fitness for each car."""
        for car in self.cars:
            car.finalize_fitness()

    # ================= Selection & Breeding =================
    def select_and_breed(self):
        """Select top performers, normalize scores, and create the next generation."""
        # Sort cars by descending fitness
        self.cars.sort(key=lambda c: c.score, reverse=True)

        # Elite selection
        ELITE_PERCENTAGE = 0.2
        top = self.cars[:max(2, int(len(self.cars) * ELITE_PERCENTAGE))]

        # Normalize scores so lowest in top group is 0
        min_score = top[-1].score
        for car in top:
            car.score -= min_score

        total_score = sum(c.score for c in top) + 1e-6
        self.pcts = []

        next_gen = []
        for car in top:
            # Proportional offspring count
            n_offspring = int((car.score / total_score) * self.size)
            self.pcts.append((car.score / total_score) * 100)

            # Clone and mutate offspring
            for _ in range(n_offspring):
                child_brain = car.brain.clone()
                child_brain.mutate(rate=0.1)
                next_gen.append(Car(self.track, brain=child_brain))

        # Fill to population size if needed
        while len(next_gen) < self.size:
            parent = random.choice(self.cars[max(2, int(len(self.cars) * ELITE_PERCENTAGE)):])
            child_brain = parent.brain.clone()
            child_brain.mutate(rate=0.1)
            next_gen.append(Car(self.track, brain=child_brain))

        # Replace population
        self.cars = next_gen
        self.generation += 1

    # ================= Status =================
    def all_done(self):
        """Check if all cars have crashed."""
        return all(car.state == CarState.CRASHED for car in self.cars)
