import pygame
from dataclasses import dataclass
from config.config import world_to_screen


@dataclass
class Target:
    x: float
    y: float
    w: int = 40
    h: int = 60
    img: pygame.Surface = None
    respawn_timer: float = 0.0
    hit_points: int = 300  # Add hit points, default 3

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        from config.config import world_to_screen
        if self.respawn_timer <= 0 and self.img:
            px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
            surf.blit(self.img, (px - self.w // 2, py - self.h // 2))