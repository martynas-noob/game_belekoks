import pygame
import math
from dataclasses import dataclass
from config.config import world_to_screen


@dataclass
class Fireball:
    x: float
    y: float
    dx: float
    dy: float
    speed: float = 300.0
    radius: int = 20
    facing_left: bool = False
    exploding: bool = False
    explosion_frame: int = 0
    explosion_timer: float = 0.0

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)

    def update(self, dt: float):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, img=None, explosion_imgs=None):
        px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
        if self.exploding and explosion_imgs:
            frame = min(self.explosion_frame, len(explosion_imgs) - 1)
            exp_img = explosion_imgs[frame]
            surf.blit(exp_img, (px - exp_img.get_width() // 2, py - exp_img.get_height() // 2))
        elif img:
            angle = -math.degrees(math.atan2(self.dy, self.dx))
            rotated_img = pygame.transform.rotate(img, angle)
            surf.blit(rotated_img, (px - rotated_img.get_width() // 2, py - rotated_img.get_height() // 2))
        else:
            pygame.draw.circle(surf, (255, 120, 40), (px, py), 15)
