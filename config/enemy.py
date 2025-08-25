import pygame
from dataclasses import dataclass
import math
from config.config import world_to_screen


@dataclass
class Enemy:
    x: float
    y: float
    w: int = 28
    h: int = 36
    speed: float = 280.0
    cooldown: float = 0.0
    img: pygame.Surface = None
    facing_left: bool = False
    hit_points: int = 100  # or 300 to match targets
    respawn_timer: float = 0.0

    def draw_enemy(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
        image = self.img
        if image:
            draw_img = pygame.transform.flip(image, True, False) if self.facing_left else image
            surf.blit(draw_img, (px - image.get_width() // 2, py - image.get_height() // 2))
        else:
            rect = pygame.Rect(px - self.w // 2, py - self.h // 2, self.w, self.h)
            pygame.draw.rect(surf, (200, 70, 70), rect, border_radius=6)

    def update(self, dt: float, target_pos, solids: list[pygame.Rect]):
        if self.cooldown > 0:
            self.cooldown -= dt
            return
        dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
        if dx < 0:
            self.facing_left = True
        elif dx > 0:
            self.facing_left = False
        dist = math.hypot(dx, dy)
        if dist > 1:
            dx, dy = dx/dist, dy/dist
        step = self.speed * dt
        self.x += dx * step
        r = self.draw_enemy()
        for s in solids:
            if r.colliderect(s):
                if dx > 0:
                    r.right = s.left
                elif dx < 0:
                    r.left = s.right
        self.x = r.centerx
        self.y += dy * step
        r = self.draw_enemy()
        for s in solids:
            if r.colliderect(s):
                if dy > 0:
                    r.bottom = s.top
                elif dy < 0:
                    r.top = s.bottom
        self.y = r.centery