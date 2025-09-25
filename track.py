from enum import Enum
import pygame

class TrackState(Enum):
    EMPTY = 0
    DRAWING = 1
    READY = 3

class Track:
    
    # Constants
    ROAD_WIDTH = 50
    RUNOFF_WIDTH = 50
    WALL_WIDTH = 20
    GOAL_WIDTH = 50
    
    DESIRED_DISTANCE = ROAD_WIDTH / 4
    
    TEMP_WIDTH = 5
    
    # Colors
    ROAD_COLOR = (50, 50, 50)
    RUNOFF_COLOR = (20, 100, 30)
    WALL_COLOR = (0, 0, 0)
    GRASS_COLOR = (2, 20, 0)
    GOAL_COLOR = (255, 255, 255)

    TEMP_COLOR = (255, 0, 0)
    
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.points = []
        self.state = TrackState.EMPTY
        self.length = 0.0  # Total track length in pixels
        
    def clear(self):
        self.points = []
        self.state = TrackState.EMPTY
        self.surface.fill((255, 255, 255))
        
    def add_point(self, point):
        self.points.append(point)
        if len(self.points) > 1:
            self.state = TrackState.DRAWING

            self.surface.fill((255, 255, 255))
            pygame.draw.lines(self.surface, Track.TEMP_COLOR, False, self.points, Track.TEMP_WIDTH)

    def draw(self):
                
        self.surface.fill(Track.GRASS_COLOR)

        for point in self.points:
            pygame.draw.circle(self.surface, Track.WALL_COLOR, point, (Track.ROAD_WIDTH // 2) + Track.RUNOFF_WIDTH + Track.WALL_WIDTH)

        for point in self.points:
            pygame.draw.circle(self.surface, Track.RUNOFF_COLOR, point, (Track.ROAD_WIDTH // 2) + Track.RUNOFF_WIDTH)

        for point in self.points:
            pygame.draw.circle(self.surface, Track.ROAD_COLOR, point, Track.ROAD_WIDTH // 2)

        if len(self.points) > 0:
            pygame.draw.circle(self.surface, Track.GOAL_COLOR, self.points[-1], Track.GOAL_WIDTH // 2)

    def smooth(self):
        if len(self.points) < 2:
            return
        DESIRED_DISTANCE = Track.ROAD_WIDTH / 4
        
        resolved = [self.points[0]]
        i = 1
        while i < len(self.points):
            a = resolved[-1]
            b = self.points[i]
            d = Track.distance(a, b)
            
            while d > DESIRED_DISTANCE:
                mid = Track.midpoint(a, b, percent=DESIRED_DISTANCE/d)
                resolved.append(mid)
                a = mid
                d = Track.distance(a, b) 
            
            if d < DESIRED_DISTANCE:
                i += 1
            else:
                resolved.append(b)
            
        self.points = resolved

    def get_length(self) -> float:
        if len(self.points) < 2:
            return 0.0


        # (len-2) full segments + final leftover segment
        total = (len(self.points) - 2) * Track.DESIRED_DISTANCE + Track.distance(self.points[-2], self.points[-1])

        self.length = total
        return total

    
    def get_length_remaining(self, x, y) -> float:
        if len(self.points) < 2:
            return 0.0

        # Find closest point
        closest_index = 0
        closest_dist = float('inf')
        for i, p in enumerate(self.points):
            d = Track.distance((x, y), p)
            if d < closest_dist:
                closest_dist = d
                closest_index = i


        if closest_index >= len(self.points) - 1:
            return 0.0

        total = (len(self.points) - closest_index - 2) * Track.DESIRED_DISTANCE
        total += Track.distance(self.points[-2], self.points[-1])
        return total

    @staticmethod
    def distance(p1, p2) -> float:
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
    
    @staticmethod
    def midpoint(p1, p2, percent=0.5):
        x = int(p1[0] + (p2[0] - p1[0]) * percent)
        y = int(p1[1] + (p2[1] - p1[1]) * percent)
        return (x, y)