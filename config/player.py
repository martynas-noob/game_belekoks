import math
import pygame
from dataclasses import dataclass

@dataclass
class Player:
    def start_sword_swing(self):
        if not self.sword_swinging:
            self.sword_swinging = True
            self.sword_anim_index = 0
            self.sword_anim_timer = 0.0

    def update_sword(self, dt: float, sword_anim_len: int):
        if self.sword_swinging:
            self.sword_anim_timer += dt
            if self.sword_anim_timer >= self.sword_anim_speed:
                self.sword_anim_timer = 0.0
                self.sword_anim_index += 1
                if self.sword_anim_index >= sword_anim_len:
                    self.sword_swinging = False
                    self.sword_anim_index = 0

    def draw_with_sword(self, surf, px, py, player_img, sword_img, sword_slash_imgs):
        # Always use the same size for sword (idle and swinging)
        SWORD_DRAW_SIZE = (80, 80)  # Use the idle sword size

        # Draw sword (behind or in front depending on facing)
        if self.sword_swinging and sword_slash_imgs:
            sword_frame = min(self.sword_anim_index, len(sword_slash_imgs)-1)
            sword_anim_img = sword_slash_imgs[sword_frame]
            # Scale sword slash frame to idle sword size
            if sword_anim_img.get_size() != SWORD_DRAW_SIZE:
                sword_anim_img = pygame.transform.scale(sword_anim_img, SWORD_DRAW_SIZE)
            offset_x = -45 if self.facing_left else 20
            offset_y = 0
            if self.facing_left:
                sword_anim_img = pygame.transform.flip(sword_anim_img, True, False)
            surf.blit(player_img, (px, py))
            surf.blit(sword_anim_img, (px + offset_x, py + offset_y))
        else:
            # Idle sword
            draw_sword_img = sword_img
            if sword_img.get_size() != SWORD_DRAW_SIZE:
                draw_sword_img = pygame.transform.scale(sword_img, SWORD_DRAW_SIZE)
            if self.facing_left:
                draw_sword_img = pygame.transform.flip(draw_sword_img, True, False)
            offset_x = -45 if self.facing_left else 20
            offset_y = 0
            surf.blit(player_img, (px, py))
            surf.blit(draw_sword_img, (px + offset_x, py + offset_y))
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
    # Sword state
    sword_swinging: bool = False
    sword_anim_index: int = 0
    sword_anim_timer: float = 0.0
    sword_anim_speed: float = 0.03  # seconds per sword frame

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