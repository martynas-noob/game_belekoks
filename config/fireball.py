import pygame
import math
import random
from dataclasses import dataclass
from config.config import world_to_screen, WIN_W, WIN_H, draw_light_mask


@dataclass
class Fireball:
    x: float
    y: float
    dx: float
    dy: float
    speed: float = 300.0
    radius: int = 22
    width: int = 46  # Wider than tall
    height: int = 31 # A bit less than width
    facing_left: bool = False
    exploding: bool = False
    explosion_frame: int = 0
    explosion_timer: float = 0.0
    damage: int = 0  # Now set by Game.py
    damage_min: int = 10
    damage_max: int = 15
    cost: int = 20  # Mana cost to cast fireball

    def __post_init__(self):
        # Only randomize if not set or set to 0
        if not self.damage or self.damage < 1:
            self.damage = random.randint(self.damage_min, self.damage_max)

    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height
        )

    def update(self, dt: float):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, img=None, explosion_imgs=None):
        px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
        # --- Fireball Glow ---
        glow_radius = 80  # You can adjust this for desired glow size
        fireball_center = (px, py)
        # Draw glow (light mask) under the fireball
        glow_mask = draw_light_mask(fireball_center, glow_radius)
        surf.blit(glow_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        if self.exploding and explosion_imgs:
            frame = min(self.explosion_frame, len(explosion_imgs) - 1)
            exp_img = explosion_imgs[frame]
            surf.blit(exp_img, (px - exp_img.get_width() // 2, py - exp_img.get_height() // 2))
        elif img:
            angle = -math.degrees(math.atan2(self.dy, self.dx))
            scaled_img = pygame.transform.scale(img, (self.width, self.height))
            rotated_img = pygame.transform.rotate(scaled_img, angle)
            surf.blit(rotated_img, (px - rotated_img.get_width() // 2, py - rotated_img.get_height() // 2))
        else:
            # Draw ellipse for fireball shape
            ellipse_rect = pygame.Rect(px - self.width // 2, py - self.height // 2, self.width, self.height)
            pygame.draw.ellipse(surf, (255, 120, 40), ellipse_rect)
