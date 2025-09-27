import pygame
from track import Track
from car import Car, CarState
from environment import Population
import colorsys

# ============================================================
#   Pygame and Window Setup
# ============================================================
pygame.init()
WIDTH, HEIGHT = 1600, 900
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Racing Simulator")
FONT = pygame.font.SysFont("Arial", 20)

def draw_text(surface, text, pos, color=(255, 255, 255)):
    """Helper to render text onto the Pygame window."""
    label = FONT.render(text, True, color)
    surface.blit(label, pos)


# ============================================================
#   Simulation Variables
# ============================================================
running = True
drawing = False
track = Track(WINDOW)

POPULATION_SIZE = 40
GENERATION_TIME = 30       # seconds per generation

population = None
population_count = 1
generation_timer = GENERATION_TIME

clock = pygame.time.Clock()
UI_X = WIDTH - 300

# ============================================================
#   UI State Variables
# ============================================================
show_history = True
show_sensors = False

# Button rectangles
BUTTON_WIDTH, BUTTON_HEIGHT = 100, 30
BTN_PADDING = 10

# Positions
btn_history_rect = pygame.Rect(BTN_PADDING, BTN_PADDING, BUTTON_WIDTH, BUTTON_HEIGHT)
btn_sensors_rect = pygame.Rect(BTN_PADDING, BTN_PADDING*2 + BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_HEIGHT)

# ============================================================
#   Fastest Time Tracking Variables
# ============================================================
all_time_best = None          # Best time across all generations
prev_gen_best = None          # Best time in previous generation
current_gen_best = -1         # Best time in current generation (-1 = none yet)


# ============================================================
#   Main Loop
# ============================================================
while running:
    # --- Timing ---
    dt = clock.tick(60) / 1000
    generation_timer -= dt
    
    # ========================================================
    #   Event Handling
    # ========================================================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if btn_history_rect.collidepoint(event.pos):
                show_history = not show_history
            elif btn_sensors_rect.collidepoint(event.pos):
                show_sensors = not show_sensors
            else:
                # Start drawing a new track
                drawing = True
                track.clear()
                track.add_point(event.pos)
                population = None  # reset AI

        elif event.type == pygame.MOUSEBUTTONUP and drawing:
            drawing = False
            track.smooth()
            track.draw()
            if track.points:
                population = Population(track, POPULATION_SIZE)
                generation_timer = GENERATION_TIME
                population_count = 1
                current_gen_best = -1
                prev_gen_best = None
                all_time_best = None

        elif event.type == pygame.MOUSEMOTION and drawing:
            track.add_point(event.pos)

    # Draw current track
    track.draw()

    # ========================================================
    #   Simulation Update
    # ========================================================
    if population:
        all_crashed = True
        for car in population.cars:
            car.think()
            car.update()
            if car.state != CarState.CRASHED:
                all_crashed = False

            # --- Update current generation fastest time ---
            if car.state == CarState.GOAL:
                car_time = GENERATION_TIME - generation_timer
                car_time = round(car_time, 2)  # hundredths of a second
                if current_gen_best == -1 or car_time < current_gen_best:
                    current_gen_best = car_time

        # --- Reset generation if time is up or all cars crashed ---
        if generation_timer <= 0 or all_crashed:
            population.evaluate_fitness()
            prev_best_score = max(car.score for car in population.cars)
            population.select_and_breed()
            generation_timer = GENERATION_TIME
            population_count += 1

            # --- Update fastest times ---
            prev_gen_best = current_gen_best if current_gen_best != -1 else None
            current_gen_best = -1
            if prev_gen_best is not None:
                if all_time_best is None or prev_gen_best < all_time_best:
                    all_time_best = prev_gen_best

    # ========================================================
    #   Rendering
    # ========================================================
    if population:
        # Sort cars by descending fitness
        population.cars.sort(key=lambda c: c.score, reverse=True)

        # Draw remaining cars
        for i, car in enumerate(population.cars):
            car.draw(history=(i < 1 and show_history), sensors=(i < 1 and show_sensors))

        # --- UI Stats ---
        draw_text(WINDOW, f"Time ({int((1 - (generation_timer / GENERATION_TIME)) * 100)}%): {int(GENERATION_TIME - generation_timer)}s / {int(GENERATION_TIME)}s", (UI_X, 10))
        draw_text(WINDOW, f"Generation: {population_count}", (UI_X, 35))

        # Fastest Time Display
        draw_text(WINDOW, f"All-Time Fastest: {all_time_best if all_time_best is not None else '---'}s", (UI_X, 85))
        draw_text(WINDOW, f"Previous Fastest: {prev_gen_best if prev_gen_best is not None else '---'}s", (UI_X, 135))
        draw_text(WINDOW, f"Current Fastest: {current_gen_best if current_gen_best != -1 else '---'}s", (UI_X, 160))
        
        # --- Buttons ---
        pygame.draw.rect(WINDOW, (100, 100, 100), btn_history_rect)
        pygame.draw.rect(WINDOW, (100, 100, 100), btn_sensors_rect)

        draw_text(WINDOW, f"History: {'On' if show_history else 'Off'}", (btn_history_rect.x + 5, btn_history_rect.y + 5))
        draw_text(WINDOW, f"Sensors: {'On' if show_sensors else 'Off'}", (btn_sensors_rect.x + 5, btn_sensors_rect.y + 5))


        # --- Top 20% Offspring Visualization ---
        if population.pcts:
            bar_width = WIDTH - 40  # leave 20px padding on each side
            bar_height = 20
            x_start = 20
            y_start = HEIGHT - bar_height - 20

            # Draw background bar
            pygame.draw.rect(WINDOW, (50, 50, 50), (x_start, y_start, bar_width, bar_height))

            # Draw each car's offspring block
            accumulated_width = 0
            n_cars = len(population.pcts)
            for i, pct in enumerate(population.pcts):
                block_width = int(bar_width * (pct / 100))

                # --- Dynamic color based on position in list ---
                hue = i / n_cars          # evenly spread hue from 0.0 → 1.0
                rgb_float = colorsys.hsv_to_rgb(hue, 0.8, 0.9)  # saturation=0.8, value=0.9
                color = tuple(int(c * 255) for c in rgb_float)

                pygame.draw.rect(WINDOW, color, (x_start + accumulated_width, y_start, block_width, bar_height))
                accumulated_width += block_width


    pygame.display.flip()

pygame.quit()
