import pygame
from enum import Enum
import math
from track import Track
from neural import NeuralNetwork

# ============================================================
#   Car State Enum
# ============================================================
class CarState(Enum):
    CRASHED = 0
    ON_GRASS = 1
    ON_ROAD = 2
    GOAL = 3


# ============================================================
#   Car History Node
# ============================================================
class CarHistoryNode:
    NODE_SIZE = 3

    def __init__(self, surface, position: pygame.Vector2, acceleration: float):
        self.surface = surface
        self.position = position.copy()
        self.acceleration = acceleration

    def draw(self):
        """Draw history node with color indicating acceleration (red = brake, green = accel)."""
        # Normalize acceleration into [-1, 1]
        norm = max(-1, min(1, self.acceleration / Car.ACCELERATION_RATE))

        if self.acceleration < 0:
            # From red to yellow
            r, g, b = 255, int(255 * (1 + norm)), 0
        else:
            # From yellow to green
            r, g, b = int(255 * (1 - norm)), 255, 0

        alpha = int(255 * 0.2)  # 20% opacity
        color = (r, g, b, alpha)

        # Temporary surface with alpha blending
        node_surf = pygame.Surface((self.NODE_SIZE * 2, self.NODE_SIZE * 2), pygame.SRCALPHA)
        pygame.draw.circle(node_surf, color, (self.NODE_SIZE, self.NODE_SIZE), self.NODE_SIZE)
        self.surface.blit(node_surf, self.position - pygame.Vector2(self.NODE_SIZE, self.NODE_SIZE))


# ============================================================
#   Car Class
# ============================================================
class Car:
    # --- Movement constants ---
    ACCELERATION_RATE = 0.2
    TURN_RATE = 15
    MAX_VELOCITY = 20
    CAR_COLOR = (200, 150, 0)

    # --- Scoring constants ---
    GRASS_PENALTY = -10
    CRASH_PENALTY = -20
    DISTANCE_SPEED_REWARD = 50
    GOAL_REWARD = 100
    END_GOAL_REWARD = 1000

    def __init__(self, track: Track, brain=None):
        # Track and brain
        self.track = track
        self.brain = brain if brain else NeuralNetwork(input_size=10, hidden_size=10, output_size=2)

        # Initial position and velocity
        self.position = pygame.Vector2(track.points[0]) if track.points else pygame.Vector2(100.0, 100.0)
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = 0

        # Initial facing angle (aligned with first segment if possible)
        if len(track.points) >= 2:
            first_vec = pygame.Vector2(track.points[1]) - pygame.Vector2(track.points[0])
            self.angle = math.degrees(math.atan2(first_vec.y, first_vec.x))
        else:
            self.angle = 0.0

        # State, score, and history
        self.state = CarState.ON_ROAD
        self.history = []
        self.score = 0.0

    # ========================================================
    #   Actions
    # ========================================================
    def accelerate(self, pct):
        """Apply forward/backward acceleration."""
        self.acceleration = max(-1, min(1, pct)) * self.ACCELERATION_RATE

    def turn(self, pct):
        """Apply turning based on speed (harder to turn at high speed)."""
        pct = max(-1, min(1, pct))
        speed_factor = 1 - min(self.velocity.length() / self.MAX_VELOCITY, 1)
        self.angle += pct * self.TURN_RATE * speed_factor

    # ========================================================
    #   Main Update
    # ========================================================
    def update(self):
        """Update car movement, collisions, sensors, and history."""
        if self.state == CarState.CRASHED:
            self.velocity = pygame.Vector2(0, 0)
            self.acceleration = 0
            self.score += self.CRASH_PENALTY
            return
        elif self.state == CarState.GOAL:
            self.velocity = pygame.Vector2(0, 0)
            self.acceleration = 0
            self.score += self.GOAL_REWARD
            return

        # Forward direction vector
        forward = pygame.Vector2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle)))

        # Apply acceleration
        self.velocity += forward * self.acceleration

        # Decompose velocity into forward and lateral components
        if self.velocity.length() > 0:
            v_forward = forward.normalize() * self.velocity.dot(forward)
            v_lateral = self.velocity - v_forward
        else:
            v_forward = pygame.Vector2(0, 0)
            v_lateral = pygame.Vector2(0, 0)

        # Determine current surface type
        color = self.track.surface.get_at((int(self.position.x), int(self.position.y)))[:3]
        MAX_STATIC_LATERAL = 0.2

        if color == Track.ROAD_COLOR:
            forward_resistance, lateral_static, lateral_kinetic = 0, 0.8, 0.4
            self.state = CarState.ON_ROAD
        elif color == Track.GOAL_COLOR:
            forward_resistance, lateral_static, lateral_kinetic = 0, 0.8, 0.4
            self.state = CarState.GOAL
        else:
            forward_resistance, lateral_static, lateral_kinetic = 0.1, 0.3, 0.2
            self.state = CarState.ON_GRASS
            self.score += self.GRASS_PENALTY

        # Apply resistances
        v_forward *= (1 - forward_resistance)
        v_lateral *= (1 - lateral_static) if v_lateral.length() <= MAX_STATIC_LATERAL else (1 - lateral_kinetic)
        self.velocity = v_forward + v_lateral

        # Cap velocity
        if self.velocity.length() > self.MAX_VELOCITY:
            self.velocity.scale_to_length(self.MAX_VELOCITY)

        # Update position
        self.position += self.velocity
        self.check_collision()
        self.check_sensors(arc=360, resolution=8, max_distance=10000)

        # Record history
        self.history.append(CarHistoryNode(self.track.surface, self.position, self.acceleration))

        self.acceleration = 0

    # ========================================================
    #   Sensing
    # ========================================================
    def check_collision(self):
        """Check for collision with walls."""
        radius = 5
        collided = False
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x = int(self.position.x + math.cos(rad) * radius)
            y = int(self.position.y + math.sin(rad) * radius)
            if self.track.surface.get_at((x, y))[:3] == Track.WALL_COLOR:
                collided = True
                break
        if collided:
            self.velocity = pygame.Vector2(0, 0)
            self.state = CarState.CRASHED
            self.score += self.CRASH_PENALTY

    def check_sensors(self, arc=180, resolution=8, max_distance=150):
        """Cast sensor rays and return distances until wall."""
        readings = []
        for i in range(resolution):
            ray_angle = math.radians(self.angle + (i * arc / resolution) - arc / 2)
            dir_vector = pygame.Vector2(math.cos(ray_angle), math.sin(ray_angle))
            distance = 0
            while distance < max_distance:
                test_pos = self.position + dir_vector * distance
                if self.track.surface.get_at((int(test_pos.x), int(test_pos.y)))[:3] == Track.WALL_COLOR:
                    break
                distance += 1
            readings.append(distance)
        return readings

    # ========================================================
    #   Intelligence
    # ========================================================
    def think(self):
        """Evaluate sensors and velocity, then act using neural network outputs."""
        traveled = (self.track.get_length() - self.track.get_length_remaining(self.position.x, self.position.y)) / self.track.get_length()
        self.score += (traveled * Car.DISTANCE_SPEED_REWARD) if traveled > 0.2 else ((1 - traveled) * Car.CRASH_PENALTY)

        inputs = (
            self.check_sensors()
            + [self.velocity.length() / self.MAX_VELOCITY,
               self.angle / 360,
               self.state.value / 4,
               traveled / self.track.get_length()]
        )
        output = self.brain.forward(inputs)
        if (self.state != CarState.CRASHED) and (self.state != CarState.GOAL):
            self.accelerate(output[0])
            self.turn(output[1])

    def finalize_fitness(self):
        """Add final reward if goal is reached."""
        traveled = self.track.get_length() - self.track.get_length_remaining(self.position.x, self.position.y)
        if self.state == CarState.GOAL:
            self.score += self.END_GOAL_REWARD

    # ========================================================
    #   Rendering
    # ========================================================
    def draw(self, history=True, sensors=False):
        """Draw car body with dynamic color, history, and sensors (if enabled)."""
        
        
        # Normalize velocity into [0, 1]
        norm = max(0, min(1, self.velocity.length() / Car.MAX_VELOCITY))

        # Compute color channels
        traveled = self.track.get_length() - self.track.get_length_remaining(self.position.x, self.position.y)
        blue = int(255 * (traveled / (self.track.get_length())))
        if self.velocity.length() < Car.MAX_VELOCITY * 0.5:
            red = 127
            green = int(255 * norm)
        else:
            red = int(255 * (1 - norm))
            green = 127

        if self.state == CarState.CRASHED:
            color = (20, 20, 40)  # Gray for crashed
        else:
            color = (red, green, blue)

        # Car triangle (tip, rear-left, rear-right)
        length, width = 12, 8
        forward = pygame.Vector2(math.cos(math.radians(self.angle)), math.sin(math.radians(self.angle)))
        right = pygame.Vector2(-forward.y, forward.x)
        tip = self.position + forward * length / 2
        rear_left = self.position - forward * length / 2 + right * width / 2
        rear_right = self.position - forward * length / 2 - right * width / 2

        pygame.draw.polygon(self.track.surface, color, [tip, rear_left, rear_right])

        if history:
            self.draw_history()
        if sensors:
            self.draw_sensors()

    def draw_sensors(self, arc=180, resolution=8, max_distance=150, color=(0, 255, 0)):
        """Draw visible sensor rays."""
        for i in range(resolution):
            ray_angle = math.radians(self.angle + (i * arc / resolution) - arc / 2)
            dir_vector = pygame.Vector2(math.cos(ray_angle), math.sin(ray_angle))
            distance = 0
            while distance < max_distance:
                test_pos = self.position + dir_vector * distance
                if self.track.surface.get_at((int(test_pos.x), int(test_pos.y)))[:3] == Track.WALL_COLOR:
                    break
                distance += 1
            pygame.draw.line(self.track.surface, color, self.position, self.position + dir_vector * distance, 1)

    def draw_history(self):
        """Draw all history nodes."""
        for node in self.history:
            node.draw()
