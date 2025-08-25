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
    attack_range: int = 80
    attack_damage: int = 10
    attack_cooldown: float = 1.0
    attack_timer: float = 1.0
    visibility_range: int = 240  # Add this attribute for visibility range

    def draw_enemy(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
        image = self.img
        # Fix: Ensure image is a pygame.Surface and not a list or None
        if isinstance(image, list):
            image = image[0]
        if isinstance(image, pygame.Surface):
            # Use self.w and self.h for correct scaling
            draw_img = pygame.transform.scale(image, (self.w, self.h))
            draw_img = pygame.transform.flip(draw_img, True, False) if self.facing_left else draw_img
            surf.blit(draw_img, (px - self.w // 2, py - self.h // 2))
        else:
            rect = pygame.Rect(px - self.w // 2, py - self.h // 2, self.w, self.h)
            pygame.draw.rect(surf, (200, 70, 70), rect, border_radius=6)

    def can_attack_player(self, player_x, player_y) -> bool:
        dist = math.hypot(self.x - player_x, self.y - player_y)
        return dist < self.attack_range and self.attack_timer <= 0

    def sees_target(self, target_x, target_y) -> bool:
        """Return True if target is within visibility range."""
        dist = math.hypot(self.x - target_x, self.y - target_y)
        return dist <= self.visibility_range

    def update(self, dt: float, target_pos, solids: list[pygame.Rect], player_rect: pygame.Rect, other_enemies: list[pygame.Rect], player=None):
        if self.cooldown > 0:
            self.cooldown -= dt
            return
        # --- AGGRO LOGIC ---
        # Only chase player if within visibility range, ignore torch by default
        chase_pos = target_pos
        if player is not None and self.sees_target(player.x, player.y):
            chase_pos = (player.x, player.y)
        dx, dy = chase_pos[0] - self.x, chase_pos[1] - self.y
        if dx < 0:
            self.facing_left = True
        elif dx > 0:
            self.facing_left = False
        dist = math.hypot(dx, dy)
        if dist > 1:
            dx, dy = dx/dist, dy/dist
        step = self.speed * dt

        # Save original position
        orig_x, orig_y = self.x, self.y

        # X axis
        self.x += dx * step
        r = self.draw_enemy()
        collided = False
        for s in solids:
            if r.colliderect(s):
                collided = True
        if player_rect and r.colliderect(player_rect):
            collided = True
        for e_rect in other_enemies:
            if r.colliderect(e_rect):
                collided = True
        if collided:
            self.x = orig_x  # revert

        # Y axis
        self.y += dy * step
        r = self.draw_enemy()
        collided = False
        for s in solids:
            if r.colliderect(s):
                collided = True
        if player_rect and r.colliderect(player_rect):
            collided = True
        for e_rect in other_enemies:
            if r.colliderect(e_rect):
                collided = True
        if collided:
            self.y = orig_y  # revert

        # Attack timer update
        if self.attack_timer > 0:
            self.attack_timer -= dt
        # Enemy attack logic
        if player and self.can_attack_player(player.x, player.y):
            if hasattr(player, "hp"):
                player.hp -= self.attack_damage
                # Show damage number overlay at player position
                from config.combat import show_damage_numbers
                show_damage_numbers(player.game_ref, player.x, player.y - 40, self.attack_damage, color=(255, 255, 255))
            self.attack_timer = self.attack_cooldown