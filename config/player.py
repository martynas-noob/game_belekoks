import math
import pygame
from dataclasses import dataclass
from config.mili import start_sword_swing, update_sword, draw_with_sword  # Import sword logic
from config.config import world_to_screen


class Item:
    def __init__(
        self,
        name,
        item_type,      # e.g. "Main Hand", "Helmet", etc.
        equip_slot,     # e.g. "Main Hand", "Helmet", etc.
        item_class=None,# e.g. "melee", "range", "magic", "armor", "boots", "helmet", "accessory"
        image=None,
        attack_min=None,
        attack_max=None,
        attack_speed=None,
        armor=None,
        speed=None,
        bonus=None,
        level=1,
        magic_min=None,     # NEW: minimum magical damage
        magic_max=None      # NEW: maximum magical damage
    ):
        self.name = name
        self.item_type = item_type      # e.g. "melee", "range", "magic", "armor", etc.
        self.equip_slot = equip_slot    # e.g. "Main Hand", "Helmet", etc.
        self.item_class = item_class    # e.g. "melee", "range", "magic", "armor", etc.
        self.image = image
        self.attack_min = attack_min
        self.attack_max = attack_max
        self.attack_speed = attack_speed
        self.armor = armor
        self.speed = speed
        self.bonus = bonus
        self.level = level
        self.magic_min = magic_min
        self.magic_max = magic_max

    def get_slot(self):
        # Returns the equipment slot name this item should go to
        return self.equip_slot

    def get_attack_damage(self):
        if self.attack_min is not None and self.attack_max is not None:
            import random
            return random.randint(self.attack_min, self.attack_max)
        return None

    def get_magic_damage(self):
        # NEW: magical damage calculation, same formula as physical
        if self.magic_min is not None and self.magic_max is not None:
            import random
            return random.randint(self.magic_min, self.magic_max)
        return None

    def get_attack_speed(self):
        return self.attack_speed

@dataclass
class Player:
    x: float
    y: float
    w: int = 28
    h: int = 36
    # --- Stats ---
    strength: int = 1
    dexterity: int = 1
    vitality: int = 1
    intelligence: int = 1
    # --- Derived attributes ---
    speed: float = 240.0
    sprint_mult: float = 1.6
    stamina: int = 20
    max_hp: int = 100
    hp: int = 100
    max_mana: int = 100
    mana: int = 100
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
    sword_anim_speed: float = 0.04 # seconds per sword frame
    game_ref: object = None  # Reference to Game instance for damage overlay
    xp: int = 0
    max_xp: int = 10
    level: int = 1
    stat_points: int = 0
    # Equipment slots
    equipment: dict = None
    # Inventory slots (list of items, None if empty)
    inventory: list = None

    # --- Track base stats for scaling ---
    base_strength: int = 1
    base_dexterity: int = 1
    base_vitality: int = 1
    base_intelligence: int = 1

    def __post_init__(self):
        # Save base stats for scaling
        self.base_strength = self.strength
        self.base_dexterity = self.dexterity
        self.base_vitality = self.vitality
        self.base_intelligence = self.intelligence
        self.apply_level_scaling()
        # Equipment: slot_name -> item (None if empty)
        self.equipment = {
            "Helmet": None,
            "Armor": None,
            "Main Hand": Item("Sword", "melee", "Main Hand", item_class="melee", attack_min=1, attack_max=5, attack_speed=1.2, level=1),
            "Off Hand": None,
            "Boots": None,
            "Accessory 1": None,
            "Accessory 2": None,
            "Accessory 3": None,
            "Accessory 4": None,
        }
        # Inventory: 5x8 grid (40 slots)
        self.inventory = [None for _ in range(40)]

    def apply_level_scaling(self):
        # Scale only base stats by level, stat_points are added after scaling
        level_mult = 1 + 0.2 * (self.level - 1)
        self.strength = int(self.base_strength * level_mult) + self.stat_points_for("strength")
        self.dexterity = int(self.base_dexterity * level_mult) + self.stat_points_for("dexterity")
        self.vitality = int(self.base_vitality * level_mult) + self.stat_points_for("vitality")
        self.intelligence = int(self.base_intelligence * level_mult) + self.stat_points_for("intelligence")
        # Derived stats
        self.max_hp = int(self.vitality * 100)
        self.hp = min(getattr(self, "hp", self.max_hp), self.max_hp)
        self.max_stamina = int(self.vitality * 20)
        self.stamina = min(getattr(self, "stamina", self.max_stamina), self.max_stamina)
        self.speed = 180.0 + self.dexterity * 20
        self.max_mana = int(self.intelligence * 100)
        self.mana = min(getattr(self, "mana", self.max_mana), self.max_mana)

    def stat_points_for(self, stat):
        # Return assigned stat points for each stat
        if hasattr(self, "assigned_stat_points") and stat in self.assigned_stat_points:
            return self.assigned_stat_points[stat]
        return 0

    def assign_stat(self, stat: str):
        if self.stat_points > 0:
            # Track assigned stat points per stat
            if not hasattr(self, "assigned_stat_points"):
                self.assigned_stat_points = {"strength": 0, "dexterity": 0, "vitality": 0, "intelligence": 0}
            if stat in self.assigned_stat_points:
                self.assigned_stat_points[stat] += 1
                self.stat_points -= 1
                # Recalculate stats with assigned points
                self.apply_level_scaling()

    def start_sword_swing(self):
        start_sword_swing(self)

    def update_sword(self, dt: float, sword_anim_len: int):
        update_sword(self, dt, sword_anim_len)

    def draw_with_sword(self, surf, px, py, player_img, sword_img, sword_slash_imgs):
        # Shift player image and sword 18 pixels to the right
        px += 18
        draw_with_sword(self, surf, px, py, player_img, sword_img, sword_slash_imgs)

    def draw(self, surf, cam_x, cam_y, player_img=None, anim_frames=None):
        # Draw player shifted 18 pixels to the right
        px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
        px += 18
        img = None
        if anim_frames and self.anim_dir in anim_frames:
            img_list = anim_frames[self.anim_dir]
            if img_list:
                img = img_list[self.anim_index % len(img_list)]
        elif player_img:
            img = player_img
        if img:
            surf.blit(img, (px - self.w // 2, py - self.h // 2))

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
        # Do NOT normalize here, just return raw direction
        sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        move_mult = self.sprint_mult if sprinting else 1.0
        return dx, dy, move_mult

    def move_and_collide(self, dt: float, solids: list[pygame.Rect]) -> None:
        keys = pygame.key.get_pressed()
        dx, dy, mult = self.input_dir(keys)
        mag = math.hypot(dx, dy)
        if mag > 0:
            dx /= mag
            dy /= mag
            # Clamp tiny values to zero
            if abs(dx) < 1e-6: dx = 0.0
            if abs(dy) < 1e-6: dy = 0.0
        step = self.speed * mult * dt
        self.moving = (mag > 0)
        # Save previous position for collision revert
        prev_x, prev_y = self.x, self.y
        # X axis
        self.x += dx * step
        r = self.rect()
        for s in solids:
            if r.colliderect(s):
                self.x = prev_x  # revert only if collision
        # Y axis
        self.y += dy * step
        r = self.rect()
        for s in solids:
            if r.colliderect(s):
                self.y = prev_y  # revert only if collision

    def update_animation(self, dt: float):
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

    def get_sword_rect(self):
        # Sword size and offset must match draw_with_sword in mili.py
        SWORD_DRAW_SIZE = (48, 48)
        offset_x = -20 if self.facing_left else 20
        offset_y = 10
        px = self.x - 40  # match world_to_screen offset in Game.py
        py = self.y - 60
        sword_x = px + offset_x + 40  # +40 to undo px offset
        sword_y = py + offset_y + 60  # +60 to undo py offset
        return pygame.Rect(int(sword_x), int(sword_y), SWORD_DRAW_SIZE[0], SWORD_DRAW_SIZE[1])

    def add_xp(self, amount: int):
        self.xp += amount
        while self.xp >= self.max_xp:
            self.xp -= self.max_xp
            self.level += 1
            self.max_xp = 10 * self.level
            self.stat_points += 4  # Add 4 points per level up
            self.apply_level_scaling()  # Recalculate stats on level up

    def update_regeneration(self, dt: float):
        # HP regeneration: 10 * vitality * (level * 0.2) per second
        level_mult = 1 + 0.2 * (self.level - 1)
        hp_regen = 10 * self.vitality * level_mult
        mana_regen = 10 * self.intelligence * level_mult
        if hp_regen > 0 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + hp_regen * dt)
        if mana_regen > 0 and self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + mana_regen * dt)
            self.mana = min(self.max_mana, self.mana + mana_regen * dt)

    def get_total_armor(self):
        # Sum armor from all equipped items
        total_armor = 0
        for item in self.equipment.values():
            if item and hasattr(item, "armor") and item.armor:
                total_armor += item.armor
        return total_armor
