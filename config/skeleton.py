import pygame
from dataclasses import dataclass, field
from config.enemy import Enemy
import random  # Import random for dodge chance

@dataclass
class Skeleton(Enemy):
    walk_frames: list = field(default_factory=list)
    attack_frames: list = field(default_factory=list)
    attack_anim_index: int = 0
    attack_anim_timer: float = 0.0
    attack_anim_speed: float = 0.10  # seconds per attack frame
    # --- New fields for movement pause logic ---
    pause_timer: float = 0.0
    player_was_close: bool = False
    torch_buffer_timer: float = 0.0
    torch_last_chase_pos: tuple = None
    weapon_drop_rate: float = 0.99  # Set high for testing
    armor_drop_rate: float = 0.10
    accessory_drop_rate: float = 0.02
    lowest_drop_level: int = 2  # Skeletons drop items of at least level 2

    def __post_init__(self):
        # Make skeleton 40% bigger
        self.w = int(self.w * 1.4)
        self.h = int(self.h * 1.4)
        super().__post_init__()
        if self.walk_frames:
            self.img = self.walk_frames
        # Skeleton-specific stats (optional, adjust as needed)
        self.strength = 2
        self.dexterity = 2
        self.vitality = 1
        self.intelligence = 1
        self.max_hp = self.vitality * 100 * self.level
        self.hit_points = self.max_hp
        self.stamina = self.vitality * 20 * self.level
        self.speed = 180.0 + self.dexterity * 20 * self.level
        self.attack_damage = 12 * self.level
        self.xp_reward = self.level * 7
        self.attacking = False
        # Make sure to set drop rates correctly for testing
        self.weapon_drop_rate = 0.99
        self.armor_drop_rate = 0.20
        self.accessory_drop_rate = 0.01
        self.lowest_drop_level = 2  # Or set dynamically based on skeleton type/level

    def start_attack(self):
        self.attacking = True
        self.attack_anim_index = 0
        self.attack_anim_timer = 0.0

    def update_attack_anim(self, dt):
        if self.attacking and self.attack_frames:
            self.attack_anim_timer += dt
            if self.attack_anim_timer >= self.attack_anim_speed:
                self.attack_anim_timer = 0.0
                self.attack_anim_index += 1
                if self.attack_anim_index >= len(self.attack_frames):
                    self.attack_anim_index = 0
                    self.attacking = False

    def update(self, dt, target_pos, solids, player_rect, other_enemies, player=None, fairy=None):
        # --- Skeleton movement pause logic ---
        player_close = False
        if player:
            dist = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
            if dist < getattr(self, "attack_range", 80):
                player_close = True

        # Fairy aggro logic (keep distance)
        fairy_in_range = False
        chase_pos = (self.x, self.y)
        if fairy is not None and hasattr(fairy, "x") and hasattr(fairy, "y") and self.sees_target(fairy.x, fairy.y):
            fx, fy = fairy.x, fairy.y
            dx, dy = fx - self.x, fy - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            keep_distance = 80
            if dist > keep_distance:
                chase_pos = (fx, fy)
            else:
                if dist > 1:
                    chase_pos = (fx - dx / dist * keep_distance, fy - dy / dist * keep_distance)
                else:
                    chase_pos = (self.x, self.y)
            fairy_in_range = True

        # Torch aggro logic (move towards torch, never away, keep attack_range distance)
        torch_in_range = False
        if player and hasattr(player, "game_ref") and hasattr(player.game_ref, "torch_ground_pos"):
            torch_pos = player.game_ref.torch_ground_pos
            dx, dy = torch_pos[0] - self.x, torch_pos[1] - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            keep_distance = getattr(self, "attack_range", 80)
            # --- Torch buffer logic ---
            if not hasattr(self, "torch_buffer_timer"):
                self.torch_buffer_timer = 0.0
                self.torch_last_chase_pos = (self.x, self.y)
            self.torch_buffer_timer -= dt
            if self.sees_target(torch_pos[0], torch_pos[1]):
                if dist < keep_distance:
                    # Torch is inside attack circle, do not change position (allow torch to enter)
                    chase_pos = (self.x, self.y)
                elif self.torch_buffer_timer <= 0:
                    # Only move towards the torch, never away, but keep attack_range distance
                    chase_pos = (torch_pos[0] - dx / dist * keep_distance, torch_pos[1] - dy / dist * keep_distance)
                    self.torch_last_chase_pos = chase_pos
                    self.torch_buffer_timer = 0.5
                else:
                    chase_pos = self.torch_last_chase_pos
                torch_in_range = True

        if player_close:
            self.pause_timer = 0.0
            self.player_was_close = True
            # --- Attack logic and animation trigger ---
            if not self.attacking:
                self.start_attack()
            self.update_attack_anim(dt)
            # Always try to attack if in range, regardless of attack_timer
            if self.attack_timer <= 0 and hasattr(self, "can_attack_player") and self.can_attack_player(player.x, player.y):
                dodge_chance = min(0.5, player.dexterity * 0.03)
                if random.random() > dodge_chance:
                    if hasattr(player, "hp"):
                        attack_damage = random.randint(self.strength * 10, self.strength * 10 + 9)
                        player.hp -= attack_damage
                        from config.combat import show_damage_numbers
                        show_damage_numbers(player.game_ref, player.x, player.y - 40, attack_damage, color=(255, 255, 255))
                self.attack_timer = self.attack_cooldown
            else:
                if hasattr(self, "attack_timer"):
                    self.attack_timer = max(0, self.attack_timer - dt)
            return  # Stop moving and only attack/animate
        else:
            if self.player_was_close:
                self.pause_timer += dt
                if self.pause_timer < 1.0:
                    if self.attacking:
                        self.update_attack_anim(dt)
                    if hasattr(self, "attack_timer"):
                        self.attack_timer = max(0, self.attack_timer - dt)
                    return
                else:
                    self.player_was_close = False
                    self.pause_timer = 0.0

        # If fairy is visible, follow it but keep distance
        if fairy is not None and hasattr(fairy, "x") and hasattr(fairy, "y") and self.sees_target(fairy.x, fairy.y):
            fx, fy = fairy.x, fairy.y
            dx, dy = fx - self.x, fy - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            keep_distance = 80
            if dist > keep_distance:
                chase_pos = (fx, fy)
            else:
                if dist > 1:
                    chase_pos = (fx - dx / dist * keep_distance, fy - dy / dist * keep_distance)
                else:
                    chase_pos = (self.x, self.y)
            super().update(dt, chase_pos, solids, player_rect, other_enemies, player=player, fairy=fairy)
            return

        # If torch is visible, follow it but keep distance or stop if in attack range
        if torch_in_range:
            Enemy.update(self, dt, chase_pos, solids, player_rect, other_enemies, player=player, fairy=fairy)
            return

        # If not close or pause expired, do normal update
        super().update(dt, target_pos, solids, player_rect, other_enemies, player=player, fairy=fairy)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        px, py = self.x - cam_x, self.y - cam_y
        image = None
        if self.attacking and self.attack_frames:
            frame = self.attack_anim_index % len(self.attack_frames)
            image = self.attack_frames[frame]
        elif isinstance(self.img, list) and self.img:
            frame = int(pygame.time.get_ticks() / 120) % len(self.img)
            image = self.img[frame]
        else:
            image = self.img
        if isinstance(image, pygame.Surface):
            draw_img = pygame.transform.scale(image, (self.w, self.h))
            draw_img = pygame.transform.flip(draw_img, True, False) if self.facing_left else draw_img
            surf.blit(draw_img, (int(px - self.w // 2), int(py - self.h // 2)))
        else:
            rect = pygame.Rect(int(px - self.w // 2), int(py - self.h // 2), self.w, self.h)
            pygame.draw.rect(surf, (200, 200, 200), rect, border_radius=6)
            pygame.draw.rect(surf, (200, 200, 200), rect, border_radius=6)
            image = self.img
        if isinstance(image, pygame.Surface):
            draw_img = pygame.transform.scale(image, (self.w, self.h))
            draw_img = pygame.transform.flip(draw_img, True, False) if self.facing_left else draw_img
            surf.blit(draw_img, (int(px - self.w // 2), int(py - self.h // 2)))
        else:
            rect = pygame.Rect(int(px - self.w // 2), int(py - self.h // 2), self.w, self.h)
            pygame.draw.rect(surf, (200, 200, 200), rect, border_radius=6)
            pygame.draw.rect(surf, (200, 200, 200), rect, border_radius=6)
