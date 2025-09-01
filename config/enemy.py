import pygame
from dataclasses import dataclass
import math
import random
from config.config import world_to_screen
from config.item_db import ITEM_GROUPS


def roll_drops(level, lowest_drop_level, weapon_drop_rate, armor_drop_rate, accessory_drop_rate):
    import random
    from config.item_db import ITEM_GROUPS, scale_item_stats
    drops = []
    # Weapon drop
    if random.random() < weapon_drop_rate:
        base_item = dict(random.choice(ITEM_GROUPS["weapon"]))
        item_level = random.randint(lowest_drop_level, level)
        base_item["level"] = item_level
        item = scale_item_stats(base_item, item_level)
        drops.append(item)
    # Armor drop
    if random.random() < armor_drop_rate:
        base_item = dict(random.choice(ITEM_GROUPS["armor"]))
        item_level = random.randint(lowest_drop_level, level)
        base_item["level"] = item_level
        item = scale_item_stats(base_item, item_level)
        drops.append(item)
    # Accessory drop
    if random.random() < accessory_drop_rate:
        base_item = dict(random.choice(ITEM_GROUPS["accessory"]))
        item_level = random.randint(lowest_drop_level, level)
        base_item["level"] = item_level
        item = scale_item_stats(base_item, item_level)
        drops.append(item)
    return drops if drops else None


@dataclass
class Enemy:
    x: float
    y: float
    w: int = 28
    h: int = 36
    # --- Stats ---
    strength: int = 1
    dexterity: int = 1
    vitality: int = 1
    intelligence: int = 1
    level: int = 1
    xp_reward: int = 5
    # --- Derived attributes ---
    speed: float = 280.0
    hit_points: int = 100
    max_hp: int = 100  # <-- Add this line
    stamina: int = 20
    attack_damage: int = 10
    cooldown: float = 0.0
    img: pygame.Surface = None
    facing_left: bool = False
    respawn_timer: float = 0.0
    attack_range: int = 80
    attack_cooldown: float = 1.0
    attack_timer: float = 1.0
    visibility_range: int = 240  # Add this attribute for visibility range
    torch_buffer_timer: float = 0.0  # Add buffer timer for torch following
    torch_last_chase_pos: tuple = None
    # --- Idle movement attributes ---
    idle_dir: tuple[float, float] = (0.0, 0.0)
    idle_timer: float = 0.0
    idle_speed: float = 60.0  # Slow idle speed
    weapon_drop_rate: float = 0.05  # Default for slime
    armor_drop_rate: float = 0.99
    accessory_drop_rate: float = 0.99  # 2% default
    lowest_drop_level: int = 1  # New: minimum item level for drops

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

    def __post_init__(self):
        # Scale stats and xp by level
        self.max_hp = self.vitality * 100 * self.level
        self.hit_points = self.max_hp
        self.stamina = self.vitality * 20 * self.level
        self.speed = 180.0 + self.dexterity * 20 * self.level
        self.attack_damage = random.randint(self.strength * 10 * self.level, self.strength * 10 * self.level + 9)
        if not hasattr(self, "xp_reward") or self.xp_reward == 5:
            self.xp_reward = self.level * 5

    def get_drop(self):
        # Use shared drop logic for all monsters
        return roll_drops(
            self.level,
            self.lowest_drop_level,
            self.weapon_drop_rate,
            self.armor_drop_rate,
            self.accessory_drop_rate
        )

    def update(self, dt: float, target_pos, solids: list[pygame.Rect], player_rect: pygame.Rect, other_enemies: list[pygame.Rect], player=None, fairy=None):
        if self.cooldown > 0:
            self.cooldown -= dt
            return
        # --- AGGRO LOGIC ---
        chase_pos = (self.x, self.y)  # Idle by default
        player_in_range = False
        torch_in_range = False
        fairy_in_range = False

        # Check player visibility
        if player is not None and self.sees_target(player.x, player.y):
            chase_pos = (player.x, player.y)
            player_in_range = True
        # Check torch visibility
        elif hasattr(player, "game_ref") and hasattr(player.game_ref, "torch_ground_pos"):
            torch_pos = player.game_ref.torch_ground_pos
            if self.sees_target(torch_pos[0], torch_pos[1]):
                tx, ty = torch_pos
                dx, dy = tx - self.x, ty - self.y
                dist = math.hypot(dx, dy)
                keep_distance = self.attack_range  # Keep distance equal to attack circle
                if dist < keep_distance:
                    # Torch is inside attack circle, do not change position (allow torch to enter)
                    chase_pos = (self.x, self.y)
                else:
                    # Only move towards the torch, never away, but keep attack_range distance
                    if dist > keep_distance:
                        chase_pos = (tx - dx / dist * keep_distance, ty - dy / dist * keep_distance)
                    else:
                        chase_pos = (self.x, self.y)
                torch_in_range = True
        # Check fairy visibility
        if fairy is not None and hasattr(fairy, "x") and hasattr(fairy, "y") and self.sees_target(fairy.x, fairy.y):
            # Keep a distance from the fairy (e.g., 80 pixels)
            fx, fy = fairy.x, fairy.y
            dx, dy = fx - self.x, fy - self.y
            dist = math.hypot(dx, dy)
            keep_distance = 80
            if dist > keep_distance:
                chase_pos = (fx, fy)
            else:
                # Stay at the edge of the keep_distance circle
                if dist > 1:
                    chase_pos = (fx - dx / dist * keep_distance, fy - dy / dist * keep_distance)
                else:
                    chase_pos = (self.x, self.y)
            fairy_in_range = True

        # --- Idle movement logic ---
        if not (player_in_range or torch_in_range or fairy_in_range):
            # Update idle direction every second
            self.idle_timer += dt
            if self.idle_timer >= 1.0 or self.idle_dir == (0.0, 0.0):
                angle = random.uniform(0, 2 * math.pi)
                self.idle_dir = (math.cos(angle), math.sin(angle))
                self.idle_timer = 0.0
            dx, dy = self.idle_dir
            step = self.idle_speed * dt
        else:
            dx, dy = chase_pos[0] - self.x, chase_pos[1] - self.y
            if dx < 0:
                self.facing_left = True
            elif dx > 0:
                self.facing_left = False
            dist = math.hypot(dx, dy)
            if dist > 1:
                dx, dy = dx/dist, dy/dist
            else:
                dx, dy = 0, 0
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
            # --- Dodge chance based on player dexterity ---
            dodge_chance = min(0.5, player.dexterity * 0.03)  # max 50% dodge
            if random.random() > dodge_chance:
                if hasattr(player, "hp"):
                    # Calculate attack damage every attack
                    attack_damage = random.randint(self.strength * 10, self.strength * 10 + 9)
                    player.hp -= attack_damage
                    from config.combat import show_damage_numbers
                    show_damage_numbers(player.game_ref, player.x, player.y - 40, attack_damage, color=(255, 255, 255))
            self.attack_timer = self.attack_cooldown