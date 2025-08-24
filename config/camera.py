from dataclasses import dataclass
import pygame
from config.config import WIN_W, WIN_H

@dataclass
class Camera:
    x: float = 0
    y: float = 0
    lerp: float = 12.0

    def update(self, target_x: float, target_y: float, dt: float) -> None:
        desired_x = target_x - WIN_W/2
        desired_y = target_y - WIN_H/2
        self.x += (desired_x - self.x) * min(1.0, self.lerp*dt)
        self.y += (desired_y - self.y) * min(1.0, self.lerp*dt)

    def view_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), WIN_W, WIN_H)