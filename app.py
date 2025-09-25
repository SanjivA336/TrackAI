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
GENERATION_TIME = 30
SIMULATION_SPEED = 5 # Ticks per second

population = None
population_count = 0
generation_timer = GENERATION_TIME  # still in "seconds of simulation time"

clock = pygame.time.Clock()

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

        elif event.type == pygame.MOUSEMOTION and drawing:
            track.add_point(event.pos)

    track.draw()

    # --- Logic and Update Loop ---
    if population:
        for s in range(SIMULATION_SPEED):
            all_crashed = True
            for car in population.cars:
                if car.state != CarState.CRASHED:
                    car.think()
                    car.update()
                    all_crashed = False

            # --- Reset generation ---
            if generation_timer <= 0 or all_crashed:
                population.evaluate_fitness()
                population.select_and_breed()
                generation_timer = GENERATION_TIME
                population_count += 1

    # --- Rendering ---
    if population:
        for car in population.cars:
            car.draw(history=False, sensors=False)

        # Optionally, highlight the best car
        best_car = max(population.cars, key=lambda c: c.score)
        best_car.draw(history=True, sensors=False)
        
        draw_text(WINDOW, f"Time ({int((1 - (generation_timer / GENERATION_TIME)) * 100)}%): {int(GENERATION_TIME - generation_timer)}s / {int(GENERATION_TIME)}s", (WIDTH - 150, 10))

        draw_text(WINDOW, f"Generation: {population_count}", (WIDTH - 150, 35))
        
        draw_text(WINDOW, f"Top Score: {best_car.score}", (WIDTH - 150, 85))
        
        for i, pct in enumerate(population.pcts):
            draw_text(WINDOW, f"Top {i+1}: {pct:.1f}%", (WIDTH - 150, 110 + i*25))

    pygame.display.flip()

pygame.quit()
