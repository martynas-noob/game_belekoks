import pygame
from dataclasses import dataclass
from config.config import world_to_screen

@dataclass
class Door:
    x: float
    y: float
    w: int = 48
    h: int = 72
    img: pygame.Surface = None
    img_open: pygame.Surface = None
    open: bool = False

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
        if self.open and self.img_open:
            surf.blit(self.img_open, (px - self.w // 2, py - self.h // 2))
        elif self.img:
            surf.blit(self.img, (px - self.w // 2, py - self.h // 2))
        else:
            pygame.draw.rect(surf, (120, 80, 40), (px - self.w // 2, py - self.h // 2, self.w, self.h), border_radius=8)
