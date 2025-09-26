import pygame
from track import Track
from car import Car, CarState
from environment import Population  # We'll create this
import time

# --- Pygame setup ---
pygame.init()
WIDTH, HEIGHT = 1600, 900
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Racing Simulator")
FONT = pygame.font.SysFont("Arial", 20)  # white text, size 20

def draw_text(surface, text, pos, color=(255, 255, 255)):
    label = FONT.render(text, True, color)
    surface.blit(label, pos)


# --- Simulation variables ---
running = True
drawing = False
track = Track(WINDOW)

POPULATION_SIZE = 50
GENERATION_TIME = 20
SIMULATION_SPEED = 1 # Ticks per second

population = None
population_count = 1
generation_timer = GENERATION_TIME  # still in "seconds of simulation time"

clock = pygame.time.Clock()

UI_X = WIDTH - 300

prev_best_score = 0

# --- Main loop ---
while running:
    dt = clock.tick(60) / 1000
    generation_timer -= dt * SIMULATION_SPEED

    # --- Event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            drawing = True
            track.clear()
            track.add_point(event.pos)
            population = None  # reset AI

        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
            track.smooth()
            track.draw()
            if track.points:
                population = Population(track, POPULATION_SIZE)
                generation_timer = GENERATION_TIME
                population_count = 1

        elif event.type == pygame.MOUSEMOTION and drawing:
            track.add_point(event.pos)

    track.draw()

    # --- Logic and Update Loop ---
    if population:
        for s in range(SIMULATION_SPEED):
            all_crashed = True
            for car in population.cars:
                car.think()
                car.update()
                if car.state != CarState.CRASHED:
                    all_crashed = False

            # --- Reset generation ---
            if generation_timer <= 0 or all_crashed:
                population.evaluate_fitness()
                prev_best_score = max(car.score for car in population.cars)
                population.select_and_breed()
                generation_timer = GENERATION_TIME
                population_count += 1

    # --- Rendering ---
    if population:
        top_car = max(population.cars, key=lambda c: c.score)
        top_car.draw(history=True, sensors=True)
        
        for car in population.cars:
            if car != top_car:
                car.draw(history=False, sensors=False)

        draw_text(WINDOW, f"Time ({int((1 - (generation_timer / GENERATION_TIME)) * 100)}%): {int(GENERATION_TIME - generation_timer)}s / {int(GENERATION_TIME)}s", (UI_X, 10))

        draw_text(WINDOW, f"Generation: {population_count}", (UI_X, 35))

        draw_text(WINDOW, f"Prev Best: {int(prev_best_score)}", (UI_X, 60))

        draw_text(WINDOW, f"Current Best: {int(top_car.score)}", (UI_X, 85))

        draw_text(WINDOW, f"Percent Improvement: {int(((top_car.score - prev_best_score) / abs(prev_best_score) * 100) if prev_best_score else 0):.1f}%", (UI_X, 110))

        for i, pct in enumerate(population.pcts):
            draw_text(WINDOW, f"Top {i+1}: {pct:.1f}%", (UI_X, 135 + i*25))

    pygame.display.flip()

pygame.quit()
