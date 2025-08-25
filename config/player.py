import math
import pygame
from dataclasses import dataclass

@dataclass
class Player:
    x: float
    y: float
    w: int = 28
    h: int = 36
    speed: float = 240.0
    sprint_mult: float = 1.6
    last_dir: tuple[float, float] = (1, 0)
    facing_left: bool = False
    anim_dir: str = "forward"
    moving: bool = False
    anim_index: int = 0
    anim_timer: float = 0.0
    anim_speed: float = 0.12  # seconds per frame

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

    def input_dir(self, keys: pygame.key.ScancodeWrapper) -> tuple[float, float, float]:
        dx = dy = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        mag = math.hypot(dx, dy)
        if mag:
            dx, dy = dx/mag, dy/mag
        sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        return dx, dy, (self.sprint_mult if sprinting else 1.0)

    def move_and_collide(self, dt: float, solids: list[pygame.Rect]) -> None:
        keys = pygame.key.get_pressed()
        dx, dy, mult = self.input_dir(keys)
        step = self.speed * mult * dt
        self.moving = (dx != 0 or dy != 0)
        # X axis
        self.x += dx * step
        r = self.rect()
        for s in solids:
            if r.colliderect(s):
                if dx > 0:
                    r.right = s.left
                elif dx < 0:
                    r.left = s.right
        self.x = r.centerx
        # Y axis
        self.y += dy * step
        r = self.rect()
        for s in solids:
            if r.colliderect(s):
                if dy > 0:
                    r.bottom = s.top
                elif dy < 0:
                    r.top = s.bottom
        self.y = r.centery

        # Animation frame logic (optional, keep as before)
        if self.moving:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0.0
                self.anim_index = (self.anim_index + 1) % 8
        else:
            self.anim_index = 0
            self.anim_timer = 0.0

    def update_direction_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        mag = math.hypot(dx, dy)
        if mag > 0:
            dx /= mag
            dy /= mag
            self.last_dir = (dx, dy)
            # Set facing_left for left/right animation
            if dx < 0:
                self.facing_left = True
            elif dx > 0:
                self.facing_left = False
            # Set anim_dir for up/down/left/right animation
            if abs(dx) > abs(dy):
                self.anim_dir = "left" if dx < 0 else "right"
            else:
                self.anim_dir = "forward" if dy > 0 else "back"