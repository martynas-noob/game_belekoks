from __future__ import annotations
import math
import sys
import warnings
import pygame
import os
import random
import pymunk
print("Pymunk version:", pymunk.version)  # Add this for debugging

import config.config as game_config  # Add this for access to all levels
from config.render import draw_game_frame, draw_inventory_overlay

from config.config import (
    WIN_W, WIN_H, FPS, LEVEL_1, COL_BG, world_to_screen, LEVEL_NAMES, LEVEL_MONSTER_MIN_MAX
)
from config.player import Player
from config.enemy import Enemy
from config.fireball import Fireball
from config.target import Target
from config.world import World
from config.camera import Camera
from config.utils import draw_light_mask
from config.combat import show_damage_numbers, draw_damage_numbers, show_health_bar, update_health_bars, draw_health_bars
from collision import Hitbox, check_entity_collision, resolve_enemy_collision
from config.item_db import (
    ITEM_SWORD, ITEM_STAFF, ITEM_BOW,
    ITEM_HELMET, ITEM_ARMOR, ITEM_BOOTS, ITEM_RING
)
from config.player import Item

warnings.filterwarnings("ignore", category=UserWarning)

# ----------------------------------------
#
# -----------------------------
# Game
# -----------------------------

class Game:
    def __init__(self, level_index=0, entry_door_idx=None, prev_level_index=None):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Belekoks Game")
        self.clock = pygame.time.Clock()

        # Load images and sounds with new paths
        self.monster_img_original = pygame.transform.scale(
            pygame.image.load("textures/NPC/slime/monster.png").convert_alpha(), (40, 60)
        )
        # Only load alternate/boss textures if they exist, else fallback to original
        try:
            self.monster_img_alt = pygame.transform.scale(
                pygame.image.load("textures/NPC/slime/monster_alt.png").convert_alpha(), (40, 60)
            )
        except Exception:
            self.monster_img_alt = self.monster_img_original
        try:
            self.monster_img_boss = pygame.transform.scale(
                pygame.image.load("textures/NPC/slime/monster_boss.png").convert_alpha(), (40, 60)
            )
        except Exception:
            self.monster_img_boss = self.monster_img_original
        self.target_img = pygame.transform.scale(
            pygame.image.load("textures/NPC/target/target.png").convert_alpha(), (40, 60)
        )
        try:
            self.target_img_alt = pygame.transform.scale(
                pygame.image.load("textures/NPC/target/target_alt.png").convert_alpha(), (40, 60)
            )
        except Exception:
            self.target_img_alt = self.target_img
        self.hero_img = pygame.transform.scale(
            pygame.image.load("textures/player_movement/hero.png").convert_alpha(), (40, 60)
        )
        self.torch_img = pygame.transform.scale(
            pygame.image.load("textures/torch/torch.png").convert_alpha(), (30, 60)
        )
        self.fireball_img = pygame.transform.scale(
            pygame.image.load("textures/effects/fireball/fireball.png").convert_alpha(), (40, 20)
        )
        self.explosion_imgs = [
            pygame.transform.scale(
                pygame.image.load(f"textures/effects/fireball_explosion/explosion{i}.png").convert_alpha(), (60, 60)
            )
            for i in range(1, 9)
        ]
        self.cast_sound = pygame.mixer.Sound("textures/effects/fireball/cast.mp3")
        self.explosion_sound = pygame.mixer.Sound("textures/effects/fireball_explosion/explosion.mp3")
        self.player_anim_frames = {
            "forward": [pygame.transform.scale(pygame.image.load(f"textures/player_movement/front{i}.png").convert_alpha(), (40, 60)) for i in range(1, 9)],
            "back":    [pygame.transform.scale(pygame.image.load(f"textures/player_movement/back{i}.png").convert_alpha(), (40, 60)) for i in range(1, 9)],
            "right":   [pygame.transform.scale(pygame.image.load(f"textures/player_movement/right{i}.png").convert_alpha(), (40, 60)) for i in range(1, 9)],
            "left":    [pygame.transform.scale(pygame.image.load(f"textures/player_movement/left{i}.png").convert_alpha(), (40, 60)) for i in range(1, 9)],
        }
        # Sword images
        self.sword_img = pygame.transform.scale(
            pygame.image.load("textures/sword/sword.png").convert_alpha(), (80, 80)
        )
        self.sword_slash_imgs = [
            pygame.transform.scale(
                pygame.image.load(f"textures/sword/sword_slash{i}.png").convert_alpha(), (60, 60)
            )
            for i in range(1, 9)
        ]
        self.sword_sound = pygame.mixer.Sound("textures/sword/sword_sound.mp3")
        self.slime_damage_sound = pygame.mixer.Sound("textures/NPC/slime/slime_damage.mp3")
        self.slime_moving_sound = pygame.mixer.Sound("textures/NPC/slime/slime_moving.mp3")
        self.slime_death_sound = pygame.mixer.Sound("textures/NPC/slime/slime_death.mp3")

        # --- Load door image before World ---
        self.door_img = pygame.transform.scale(
            pygame.image.load("textures/door/door_closed.png").convert_alpha(), (48, 72)
        )
        self.door_img_open = pygame.transform.scale(
            pygame.image.load("textures/door/door_open.png").convert_alpha(), (48, 72)
        )

        # Game state
        self.player = Player(200, 200)
        self.player.game_ref = self  # Set reference for damage overlay
        # --- Place all items in inventory at game start ---
        item_vars = [
            ITEM_SWORD, ITEM_STAFF, ITEM_BOW,
            ITEM_HELMET, ITEM_ARMOR, ITEM_BOOTS, ITEM_RING
        ]
        slot_map = {
            "Sword": "Main Hand",
            "Staff": "Main Hand",
            "Bow": "Main Hand",
            "Helmet": "Helmet",
            "Armor": "Armor",
            "Boots": "Boots",
            "Ring": "Accessory 1"
        }
        for i, item_var in enumerate(item_vars):
            # Assign correct slot for each item
            item_name = item_var.get("name")
            slot = slot_map.get(item_name, item_var.get("equip_slot"))
            item_var["equip_slot"] = slot
            if i < len(self.player.inventory):
                self.player.inventory[i] = Item(**item_var)
        # --- Add a random level 5 item for testing ---
        from config.item_db import ITEM_GROUPS, scale_item_stats
        import random
        group = random.choice(list(ITEM_GROUPS.values()))
        base_item = dict(random.choice(group))
        base_item["level"] = 5
        test_item = scale_item_stats(base_item, 5)
        self.player.inventory[7] = Item(**test_item)
        self.camera = Camera()
        # Provide a list of enemy/target images to World
        self.enemy_imgs = [self.monster_img_original, self.monster_img_alt, self.monster_img_boss]
        self.target_imgs = [self.target_img, self.target_img_alt]
        self.level_index = level_index  # Track current level index
        self.prev_level_index = prev_level_index  # Track previous level index for backtracking
        self.entry_door_idx = entry_door_idx  # Track which door was used to enter
        # Add this before self.load_level(...)
        self.defeated_enemies_per_level = {}  # Track defeated enemies by level index
        self.initial_enemy_positions_per_level = {}  # Track initial enemy positions per level
        # --- Skeleton walk animation frames ---
        self.skeleton_walk_frames = [
            pygame.transform.scale(
                pygame.image.load(f"textures/NPC/skeleton/skeleton_walk{i}.png").convert_alpha(), (40, 60)
            )
            for i in range(1, 9)
        ]
        # --- Skeleton attack animation frames ---
        self.skeleton_attack_frames = [
            pygame.transform.scale(
                pygame.image.load(f"textures/NPC/skeleton/skeleton_attack{i}.png").convert_alpha(), (40, 60)
            )
            for i in range(1, 9)
        ]

        self.load_level(self.level_index, entry_door_idx=self.entry_door_idx)
        self.fireballs = []
        self.torch_on_ground = True
        self.torch_following = False
        self.torch_ground_pos = (self.player.x + 60, self.player.y)
        self.torch_glow_radius = 220  # <-- Restore this line
        # Torch movement attributes
        self.torch_vel_x = random.choice([-1, 1]) * 80.0  # pixels/sec
        self.torch_vel_y = random.choice([-1, 1]) * 80.0
        self.torch_move_timer = 0.0
        # Torch wiggle animation
        self.torch_wiggle_timer = 0.0
        self.torch_wiggle_offset = (0, 0)
        self.darkness_alpha = 200  # <-- Add this line
        self.last_t_press_time = 0  # <-- Add this line
        self.torch_pickup_cooldown = 0.0  # <-- Add this line
        self.t_press_count = 0  # <-- Add this if not present
        self.damage_numbers = []
        self.target_health_bars = {}
        self.sword_swing_damage = None
        self.sword_swing_hit_targets = set()
        self.entity_hitboxes = []  # Store hitboxes for collision checks

        # Pymunk physics
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)

        # Create player body and shape
        self.player_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.player_body.position = (self.player.x, self.player.y)
        self.player_shape = pymunk.Circle(self.player_body, 20)
        self.player_shape.collision_type = 1
        self.space.add(self.player_body, self.player_shape)

        # Create enemy bodies and shapes
        self.enemy_bodies = []
        self.enemy_shapes = []
        for enemy in self.world.enemies:
            body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            body.position = (enemy.x, enemy.y)
            shape = pymunk.Circle(body, 20)
            shape.collision_type = 2
            self.space.add(body, shape)
            self.enemy_bodies.append(body)
            self.enemy_shapes.append(shape)

        # Create wall shapes (static bodies)
        self.wall_shapes = []
        for wall_rect in self.world.solids:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = (wall_rect.x, wall_rect.y)
            shape = pymunk.Poly.create_box(body, (wall_rect.width, wall_rect.height))
            shape.collision_type = 10  # Arbitrary wall type
            self.space.add(body, shape)
            self.wall_shapes.append(shape)

        # --- Add light mask cache ---
        self.light_mask_cache = {}

    def get_light_mask(self, radius):
        # --- Add this helper method for caching ---
        if radius not in self.light_mask_cache:
            mask = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            for r in range(radius, 0, -1):
                alpha = int(255 * (1 - r / radius))
                pygame.draw.circle(mask, (0, 0, 0, alpha), (radius, radius), r)
            self.light_mask_cache[radius] = mask
        return self.light_mask_cache[radius]

    def load_level(self, level_index, entry_door_pos=None, entry_door_idx=None):
        # Get all levels from config.py (LEVEL_1, LEVEL_2, etc.)
        level_keys = [k for k in dir(game_config) if k.startswith("LEVEL_")]
        level_keys.sort()  # Ensure LEVEL_1, LEVEL_2, ...
        self.level_keys = level_keys
        if 0 <= level_index < len(level_keys):
            level_layout = getattr(game_config, level_keys[level_index])
        else:
            level_layout = getattr(game_config, level_keys[0])
            self.level_index = 0
        game_level = self.level_index + 1  # Level 1-based
        # Get monster level min/max from config, fallback to (1, game_level)
        if self.level_index < len(LEVEL_MONSTER_MIN_MAX):
            monster_level_min, monster_level_max = LEVEL_MONSTER_MIN_MAX[self.level_index]
        else:
            monster_level_min, monster_level_max = 1, game_level
        self.world = World(
            level_layout,
            self.enemy_imgs,
            self.target_imgs,
            door_img=self.door_img,
            door_img_open=self.door_img_open,
            game_level=game_level,
            monster_level_min=monster_level_min,
            monster_level_max=monster_level_max,
            skeleton_walk_frames=self.skeleton_walk_frames,
            skeleton_attack_frames=self.skeleton_attack_frames
        )
        self.fireballs = []
        self.enemy_bodies = []
        self.enemy_shapes = []
        # --- Track and filter enemies by initial positions ---
        # Save initial enemy positions for this level if not already saved
        if self.level_index not in self.initial_enemy_positions_per_level:
            self.initial_enemy_positions_per_level[self.level_index] = [
                (enemy.x, enemy.y) for enemy in self.world.enemies
            ]
        # Remove defeated enemies for this level
        defeated = self.defeated_enemies_per_level.get(self.level_index, set())
        filtered_enemies = []
        for enemy in self.world.enemies:
            enemy_id = (enemy.x, enemy.y)
            if enemy_id not in defeated:
                filtered_enemies.append(enemy)
        self.world.enemies = filtered_enemies
        for enemy in self.world.enemies:
            body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            body.position = (enemy.x, enemy.y)
            shape = pymunk.Circle(body, 20)
            shape.collision_type = 2
            self.space.add(body, shape)
            self.enemy_bodies.append(body)
            self.enemy_shapes.append(shape)
        # Find all doors in the level
        door_positions = []
        for y, row in enumerate(level_layout):
            for x, ch in enumerate(row):
                if ch == '7':
                    door_positions.append((x * 48 + 24, y * 48 + 36))
        # Determine spawn position
        if entry_door_idx is not None and 0 <= entry_door_idx < len(door_positions):
            # Try to spawn player on a floor tile next to the entry door (prefer right, left, down, up)
            x, y = door_positions[entry_door_idx]
            tile_x = int((x - 24) // 48)
            tile_y = int((y - 36) // 48)
            offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            placed = False
            for dx, dy in offsets:
                nx, ny = tile_x + dx, tile_y + dy
                if 0 <= ny < len(level_layout) and 0 <= nx < len(level_layout[0]):
                    if level_layout[ny][nx] == '.':
                        self.player.x = nx * 48 + 24
                        self.player.y = ny * 48 + 36
                        placed = True
                        break
            if not placed:
                self.player.x, self.player.y = x, y
        elif entry_door_pos is not None:
            # Fallback for legacy logic
            x, y = entry_door_pos
            tile_x = int((x - 24) // 48)
            tile_y = int((y - 36) // 48)
            offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            placed = False
            for dx, dy in offsets:
                nx, ny = tile_x + dx, tile_y + dy
                if 0 <= ny < len(level_layout) and 0 <= nx < len(level_layout[0]):
                    if level_layout[ny][nx] == '.':
                        self.player.x = nx * 48 + 24
                        self.player.y = ny * 48 + 36
                        placed = True
                        break
            if not placed:
                self.player.x, self.player.y = entry_door_pos
        else:
            # If there are doors, always try to spawn next to the first door
            if door_positions:
                x, y = door_positions[0]
                tile_x = int((x - 24) // 48)
                tile_y = int((y - 36) // 48)
                offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                placed = False
                for dx, dy in offsets:
                    nx, ny = tile_x + dx, tile_y + dy
                    if 0 <= ny < len(level_layout) and 0 <= nx < len(level_layout[0]):
                        if level_layout[ny][nx] == '.':
                            self.player.x = nx * 48 + 24
                            self.player.y = ny * 48 + 36
                            placed = True
                            break
                if not placed:
                    self.player.x, self.player.y = door_positions[0]
            else:
                self.player.x, self.player.y = 200, 200
        self.player.hp = self.player.max_hp
        self.camera = Camera()
        self.door_positions = door_positions  # Store for later use
        self.door_transition = None  # (idx, start_time, direction)
        self.door_transition_duration = 2.0  # seconds
        self.level_name_timer = 5.0  # Show level name for 5 seconds
        self.inventory_open = False  # <-- Add this line
        self.inventory_tab = 0  # 0=Inventory, 1=Stats, 2=Skills
        self.dropped_items = []  # List of dropped items on ground
        self.dragged_item = None
        self.dragged_item_idx = None
        self.dragged_item_rect = None

    def run(self):
        print("Game loop started")  # Debug: confirm loop starts
        running = True
        game_over = False
        next_level_triggered = False  # Add this flag to prevent multiple triggers per frame
        last_door_idx = None  # Track which door was last used
        # --- Main event loop ---
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            shoot_fireball = False
            sword_swing = False
            next_level_triggered = False  # Reset at the start of each frame

            # --- Torch pickup cooldown decrement ---
            if self.torch_pickup_cooldown > 0:
                self.torch_pickup_cooldown -= dt

            # --- Game Over Check ---
            if self.player.hp <= 0:
                game_over = True

            for e in pygame.event.get():
                # --- DEBUG: Print all mouse events ---
                if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    print(f"DEBUG: Mouse event type={e.type}, button={getattr(e, 'button', None)}, pos={pygame.mouse.get_pos()}")
                if e.type == pygame.QUIT:
                    running = False
                elif self.inventory_open:
                    # --- DEBUG: Print mouse events in inventory ---
                    if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                        print(f"INVENTORY DEBUG: type={e.type}, button={getattr(e, 'button', None)}, tab={self.inventory_tab}, pos={pygame.mouse.get_pos()}")
                    if e.type == pygame.KEYDOWN:
                        if e.key in (pygame.K_i, pygame.K_TAB, pygame.K_ESCAPE):
                            self.inventory_open = False
                        elif e.key in (pygame.K_LEFT, pygame.K_a):
                            self.inventory_tab = (self.inventory_tab - 1) % 3
                        elif e.key in (pygame.K_RIGHT, pygame.K_d):
                            self.inventory_tab = (self.inventory_tab + 1) % 3
                        elif e.key == pygame.K_1:
                            self.inventory_tab = 0
                        elif e.key == pygame.K_2:
                            self.inventory_tab = 1
                        elif e.key == pygame.K_3:
                            self.inventory_tab = 2
                    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.inventory_tab == 1:
                        mx, my = pygame.mouse.get_pos()
                        # Centered and spaced buttons
                        btn_w, btn_h = 32, 32
                        btn_x = self.screen.get_width() // 2 + 180
                        btn_y_start = 220 + 11 * 40
                        stat_names = ["strength", "dexterity", "vitality", "intelligence"]
                        for i, stat in enumerate(stat_names):
                            btn_rect = pygame.Rect(btn_x, btn_y_start + i * 56, btn_w, btn_h)
                            if btn_rect.collidepoint(mx, my):
                                self.player.assign_stat(stat)
                                break
                    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.inventory_tab == 0:
                        mx, my = pygame.mouse.get_pos()
                        # Start dragging if left-click on inventory slot or equipment slot
                        if hasattr(self, "_inv_slot_rects"):
                            for idx, rect in enumerate(self._inv_slot_rects):
                                if rect.collidepoint(mx, my):
                                    item = self.player.inventory[idx]
                                    if item is not None:
                                        self.dragged_item = item
                                        self.dragged_item_idx = idx
                                        self.dragged_item_rect = rect
                                    break
                        # Equipment slots: allow dragging equipped items
                        if hasattr(self, "_equip_slot_rects"):
                            for slot_name, rect in self._equip_slot_rects.items():
                                if rect.collidepoint(mx, my):
                                    item = self.player.equipment.get(slot_name)
                                    if item is not None:
                                        self.dragged_item = item
                                        self.dragged_item_idx = slot_name  # Use slot name for equipment
                                        self.dragged_item_rect = rect
                                    break
                    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3 and self.inventory_tab == 0:
                        mx, my = pygame.mouse.get_pos()
                        # Right-click: instant equip from inventory to equipment
                        if hasattr(self, "_inv_slot_rects"):
                            for idx, rect in enumerate(self._inv_slot_rects):
                                if rect.collidepoint(mx, my):
                                    item = self.player.inventory[idx]
                                    if item is not None:
                                        # Fix: use item.get_slot() for Item objects
                                        slot = item.get_slot() if hasattr(item, "get_slot") else None
                                        target_slot = None
                                        for slot_name in self.player.equipment:
                                            if _slot_matches(item, slot_name):
                                                target_slot = slot_name
                                                break
                                        if target_slot:
                                            equip_rect = self._equip_slot_rects[target_slot]
                                            if hasattr(item, "level") and self.player.level < item.level:
                                                msg_x = rect.centerx
                                                msg_y = rect.top - 24
                                                self.damage_numbers.append({
                                                    "x": msg_x,
                                                    "y": msg_y,
                                                    "value": f"Level {item.level} required",
                                                    "timer": 1.2,
                                                    "alpha": 255,
                                                    "color": (255, 80, 80),
                                                    "duration": 1.2
                                                })
                                                break
                                            current_equipped = self.player.equipment.get(target_slot)
                                            self.player.equipment[target_slot] = item
                                            self.player.inventory[idx] = None
                                            if current_equipped is not None and current_equipped != item:
                                                for empty_idx in range(len(self.player.inventory)):
                                                    if self.player.inventory[empty_idx] is None:
                                                        self.player.inventory[empty_idx] = current_equipped
                                                        break
                                    break
                        # Right-click: instant unequip from equipment to inventory
                        if hasattr(self, "_equip_slot_rects"):
                            for slot_name, rect in self._equip_slot_rects.items():
                                if rect.collidepoint(mx, my):
                                    item = self.player.equipment.get(slot_name)
                                    if item is not None:
                                        # Find first empty inventory slot
                                        for idx in range(len(self.player.inventory)):
                                            if self.player.inventory[idx] is None:
                                                self.player.inventory[idx] = item
                                                self.player.equipment[slot_name] = None
                                                break
                                    break
                    elif e.type == pygame.MOUSEBUTTONUP and self.inventory_tab == 0:
                        mx, my = pygame.mouse.get_pos()
                        # Drag-and-drop logic
                        if self.dragged_item is not None:
                            dropped = False
                            # If dragging from inventory
                            if isinstance(self.dragged_item_idx, int):
                                # Drop on inventory slot: swap items
                                if hasattr(self, "_inv_slot_rects"):
                                    for idx, rect in enumerate(self._inv_slot_rects):
                                        if rect.collidepoint(mx, my):
                                            if idx != self.dragged_item_idx:
                                                self.player.inventory[self.dragged_item_idx], self.player.inventory[idx] = self.player.inventory[idx], self.player.inventory[self.dragged_item_idx]
                                            dropped = True
                                            break
                                # Drop on equipment slot: equip if allowed, else show "Level required" message
                                if not dropped and hasattr(self, "_equip_slot_rects"):
                                    for slot_name, rect in self._equip_slot_rects.items():
                                        if rect.collidepoint(mx, my):
                                            item = self.dragged_item
                                            # Show "Level required" message if not allowed
                                            if hasattr(item, "level") and self.player.level < item.level:
                                                msg_x = rect.centerx
                                                msg_y = rect.top - 24
                                                self.damage_numbers.append({
                                                    "x": msg_x,
                                                    "y": msg_y,
                                                    "value": f"Level {item.level} required",
                                                    "timer": 1.2,
                                                    "alpha": 255,
                                                    "color": (255, 80, 80),
                                                    "duration": 1.2
                                                })
                                                dropped = True
                                                break
                                            # Equip only if slot matches item's equip_slot (including accessories)
                                            if _slot_matches(item, slot_name):
                                                current_equipped = self.player.equipment.get(slot_name)
                                                self.player.equipment[slot_name] = item
                                                self.player.inventory[self.dragged_item_idx] = None
                                                if current_equipped is not None:
                                                    for idx2 in range(len(self.player.inventory)):
                                                        if self.player.inventory[idx2] is None:
                                                            self.player.inventory[idx2] = current_equipped
                                                            break
                                                dropped = True
                                                break
                                            dropped = True  # If slot does not match, just return item to inventory
                                            break
                            # If dragging from equipment
                            elif isinstance(self.dragged_item_idx, str):
                                # Drop on inventory slot: move equipped item to inventory slot (swap if occupied)
                                if hasattr(self, "_inv_slot_rects"):
                                    for idx, rect in enumerate(self._inv_slot_rects):
                                        if rect.collidepoint(mx, my):
                                            inv_item = self.player.inventory[idx]
                                            self.player.inventory[idx] = self.dragged_item
                                            self.player.equipment[self.dragged_item_idx] = inv_item
                                            dropped = True
                                            break
                                # Drop on another equipment slot: swap equipment if slot matches (including accessories)
                                if not dropped and hasattr(self, "_equip_slot_rects"):
                                    for slot_name, rect in self._equip_slot_rects.items():
                                        if rect.collidepoint(mx, my):
                                            item = self.dragged_item
                                            # Show "Level required" message if not allowed
                                            if hasattr(item, "level") and self.player.level < item.level:
                                                msg_x = rect.centerx
                                                msg_y = rect.top - 24
                                                self.damage_numbers.append({
                                                    "x": msg_x,
                                                    "y": msg_y,
                                                    "value": f"Level {item.level} required",
                                                    "timer": 1.2,
                                                    "alpha": 255,
                                                    "color": (255, 80, 80),
                                                    "duration": 1.2
                                                })
                                                dropped = True
                                                break
                                            if _slot_matches(item, slot_name):
                                                other_item = self.player.equipment.get(slot_name)
                                                self.player.equipment[slot_name] = item
                                                self.player.equipment[self.dragged_item_idx] = other_item
                                                dropped = True
                                                break
                                            dropped = True  # If slot does not match, just return item to original slot
                                            break
                            # --- Drop zone logic (lower third + 80px) ---
                            drop_zone_w, drop_zone_h = 420, 180
                            drop_zone_x = self.screen.get_width() // 2 - drop_zone_w // 2
                            drop_zone_y = int(self.screen.get_height() * 2 / 3 - drop_zone_h // 2 + 80)
                            drop_zone_rect = pygame.Rect(drop_zone_x, drop_zone_y, drop_zone_w, drop_zone_h)
                            if not dropped and drop_zone_rect.collidepoint(mx, my):
                                # Remove item from inventory or equipment
                                if isinstance(self.dragged_item_idx, int):
                                    self.player.inventory[self.dragged_item_idx] = None
                                elif isinstance(self.dragged_item_idx, str):
                                    self.player.equipment[self.dragged_item_idx] = None
                                dropped = True
                            # Drop outside: return item to original slot
                            if not dropped:
                                if isinstance(self.dragged_item_idx, int):
                                    self.player.inventory[self.dragged_item_idx] = self.dragged_item
                                elif isinstance(self.dragged_item_idx, str):
                                    self.player.equipment[self.dragged_item_idx] = self.dragged_item
                            self.dragged_item = None
                            self.dragged_item_idx = None
                            self.dragged_item_rect = None
                elif game_over:
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            running = False
                        elif e.key == pygame.K_r:
                            # Restart game: re-initialize everything and reset player HP
                            self.__init__()
                            self.player.hp = self.player.max_hp
                            game_over = False
                    elif e.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        if restart_rect.collidepoint(mx, my):
                            self.__init__()
                            self.player.hp = self.player.max_hp
                            game_over = False
                        elif exit_rect.collidepoint(mx, my):
                            running = False
                else:
                    # --- Player input handling ---
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            running = False
                        elif e.key in (pygame.K_i, pygame.K_TAB):
                            self.inventory_open = True
                        elif e.key == pygame.K_f:
                            shoot_fireball = True
                        elif e.key == pygame.K_t:
                            now = pygame.time.get_ticks()
                            if now - self.last_t_press_time < 400:
                                self.t_press_count += 1
                            else:
                                self.t_press_count = 1
                            self.last_t_press_time = now
                            # Double-tap T: torch follows player
                            if self.t_press_count == 2 and self.torch_pickup_cooldown <= 0 and self.torch_on_ground:
                                self.torch_following = True
                                self.torch_on_ground = False
                                self.torch_pickup_cooldown = 0.3
                                self.torch_vel_x = 0
                                self.torch_vel_y = 0
                            # Single-tap T: drop torch at its current location (only if following)
                            elif self.t_press_count == 1 and self.torch_pickup_cooldown <= 0 and self.torch_following:
                                self.torch_on_ground = True
                                self.torch_following = False
                                self.torch_pickup_cooldown = 0.3
                                self.torch_vel_x = random.choice([-1, 1]) * 80.0
                                self.torch_vel_y = random.choice([-1, 1]) * 80.0
                        elif e.key == pygame.K_RETURN:
                            # Try to open a nearby door
                            for door in getattr(self.world, "doors", []):
                                dist = math.hypot(self.player.x - door.x, self.player.y - door.y)
                                if dist < 80:
                                    door.open = True
                        elif e.key == pygame.K_r:
                            # Restart the current level
                            self.player.x, self.player.y = 200, 200  # Reset player position
                            self.player.hp = self.player.max_hp  # Restore player health
                            # self.world.reset()  # Reset the world (enemies, targets, etc.)
                            # Instead, reload the current level:
                            self.load_level(self.level_index, entry_door_idx=self.entry_door_idx)
                            game_over = False  # Reset game over state
                            next_level_triggered = False  # Ensure next level is not triggered
                    elif e.type == pygame.MOUSEBUTTONDOWN:
                        if e.button == 1:  # Left mouse button
                            sword_swing = True

            if self.inventory_open:
                draw_inventory_overlay(self, self.inventory_tab)
                # --- Draw dragged item if any ---
                if self.dragged_item is not None and self.dragged_item_rect is not None:
                    mx, my = pygame.mouse.get_pos()
                    slot_size = self.dragged_item_rect.width
                    if hasattr(self.dragged_item, "image") and self.dragged_item.image:
                        item_img = pygame.transform.scale(self.dragged_item.image, (slot_size - 12, slot_size - 12))
                        self.screen.blit(item_img, (mx - (slot_size - 12) // 2, my - (slot_size - 12) // 2))
                    else:
                        pygame.draw.circle(self.screen, (200, 200, 80), (mx, my), slot_size // 3)
                    # --- Draw drop zone (lower by extra 80 pixels) ---
                    drop_zone_w, drop_zone_h = 420, 180
                    drop_zone_x = self.screen.get_width() // 2 - drop_zone_w // 2
                    drop_zone_y = int(self.screen.get_height() * 2 / 3 - drop_zone_h // 2 + 80)
                    drop_zone_rect = pygame.Rect(drop_zone_x, drop_zone_y, drop_zone_w, drop_zone_h)
                    pygame.draw.rect(self.screen, (180, 180, 180), drop_zone_rect, border_radius=24)
                    dash_color = (120, 120, 120)
                    dash_len = 18
                    gap_len = 10
                    # Top edge
                    for x in range(drop_zone_x, drop_zone_x + drop_zone_w, dash_len + gap_len):
                        pygame.draw.line(self.screen, dash_color, (x, drop_zone_y), (min(x + dash_len, drop_zone_x + drop_zone_w), drop_zone_y), 3)
                    # Bottom edge
                    for x in range(drop_zone_x, drop_zone_x + drop_zone_w, dash_len + gap_len):
                        pygame.draw.line(self.screen, dash_color, (x, drop_zone_y + drop_zone_h), (min(x + dash_len, drop_zone_x + drop_zone_w), drop_zone_y + drop_zone_h), 3)
                    # Left edge
                    for y in range(drop_zone_y, drop_zone_y + drop_zone_h, dash_len + gap_len):
                        pygame.draw.line(self.screen, dash_color, (drop_zone_x, y), (drop_zone_x, min(y + dash_len, drop_zone_y + drop_zone_h)), 3)
                    # Right edge
                    for y in range(drop_zone_y, drop_zone_y + drop_zone_h, dash_len + gap_len):
                        pygame.draw.line(self.screen, dash_color, (drop_zone_x + drop_zone_w, y), (drop_zone_x + drop_zone_w, min(y + dash_len, drop_zone_y + drop_zone_h)), 3)
                    font = pygame.font.SysFont("arial", 36, bold=True)
                    drop_text = font.render("Drop Item Here", True, (60, 60, 60))
                    self.screen.blit(drop_text, (drop_zone_x + drop_zone_w // 2 - drop_text.get_width() // 2,
                                                 drop_zone_y + drop_zone_h // 2 - drop_text.get_height() // 2))
                # --- Fade "Level required" messages only in inventory overlay ---
                for dmg in self.damage_numbers[:]:
                    if isinstance(dmg.get("value", ""), str) and dmg.get("value", "").startswith("Level "):
                        dmg["timer"] -= dt
                        dmg["alpha"] = int(255 * (dmg["timer"] / dmg["duration"]))
                        if dmg["timer"] <= 0:
                            self.damage_numbers.remove(dmg)
                continue  # Pause game updates while inventory is open

            # Regenerate HP and Mana each frame (only when not paused)
            self.player.update_regeneration(dt)

            # --- Door transition animation logic ---
            if self.door_transition is not None:
                idx, start_time, direction = self.door_transition
                elapsed = pygame.time.get_ticks() / 500.0 - start_time
                # Open the door visually
                if 0 <= idx < len(getattr(self.world, "doors", [])):
                    getattr(self.world, "doors", [])[idx].open = True

                # --- DRAWING (with lighting) during transition ---
                self.screen.fill(COL_BG)
                self.world.draw(self.screen, self.camera.x, self.camera.y, self.camera.view_rect())

                # --- LIGHTING OVERLAY (same as normal frame) ---
                darkness = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
                darkness.fill((0, 0, 0, self.darkness_alpha))

                # Torch glow
                if self.torch_on_ground or self.torch_following:
                    torch_px, torch_py = world_to_screen(
                        self.torch_ground_pos[0] - 15 + self.torch_wiggle_offset[0],
                        self.torch_ground_pos[1] - 30 + self.torch_wiggle_offset[1],
                        self.camera.x, self.camera.y
                    )
                    torch_center = (torch_px + 15, torch_py + 30)
                else:
                    torch_center = None

                if torch_center:
                    mask = self.get_light_mask(self.torch_glow_radius)
                    x = torch_center[0] - self.torch_glow_radius
                    y = torch_center[1] - self.torch_glow_radius
                    darkness.blit(mask, (x, y), special_flags=pygame.BLEND_RGBA_SUB)

                # Fireball and explosion glow
                fireball_glow_radius = 80
                explosion_glow_radius = 180
                for fireball in self.fireballs:
                    fx, fy = world_to_screen(fireball.x, fireball.y, self.camera.x, self.camera.y)
                    fireball_center = (int(fx), int(fy))
                    if fireball.exploding:
                        mask = self.get_light_mask(explosion_glow_radius)
                        x = fireball_center[0] - explosion_glow_radius
                        y = fireball_center[1] - explosion_glow_radius
                        darkness.blit(mask, (x, y), special_flags=pygame.BLEND_RGBA_SUB)
                    else:
                        mask = self.get_light_mask(fireball_glow_radius)
                        x = fireball_center[0] - fireball_glow_radius
                        y = fireball_center[1] - fireball_glow_radius
                        darkness.blit(mask, (x, y), special_flags=pygame.BLEND_RGBA_SUB)

                self.screen.blit(darkness, (0, 0))
                pygame.display.flip()

                # After animation, actually change level
                if elapsed >= self.door_transition_duration:
                    if direction == "back":
                        prev_level_index = self.prev_level_index
                        prev_level_layout = getattr(game_config, self.level_keys[prev_level_index])
                        prev_doors = []
                        for y, row in enumerate(prev_level_layout):
                            for x, ch in enumerate(row):
                                if ch == '7':
                                    prev_doors.append((x * 48 + 24, y * 48 + 36))
                if elapsed >= self.door_transition_duration:
                    if direction == "back":
                        prev_level_index = self.prev_level_index
                        prev_level_layout = getattr(game_config, self.level_keys[prev_level_index])
                        prev_doors = []
                        for y, row in enumerate(prev_level_layout):
                            for x, ch in enumerate(row):
                                if ch == '7':
                                    prev_doors.append((x * 48 + 24, y * 48 + 36))
                        entry_idx = idx if idx < len(prev_doors) else 0
                        self.level_index = prev_level_index
                        self.prev_level_index = prev_level_index - 1 if prev_level_index > 0 else None
                        self.entry_door_idx = entry_idx
                        self.load_level(self.level_index, entry_door_idx=entry_idx)
                    else:
                        next_level_index = (self.level_index + 1) % len(self.level_keys)
                        next_level_layout = getattr(game_config, self.level_keys[next_level_index])
                        next_doors = []
                        for y, row in enumerate(next_level_layout):
                            for x, ch in enumerate(row):
                                if ch == '7':
                                    next_doors.append((x * 48 + 24, y * 48 + 36))
                        entry_idx = idx if idx < len(next_doors) else 0
                        self.prev_level_index = self.level_index
                        self.level_index = next_level_index
                        self.entry_door_idx = entry_idx
                        self.load_level(self.level_index, entry_door_idx=entry_idx)
                    self.door_transition = None
                    next_level_triggered = False
                continue  # Skip rest of loop this frame

            # --- After input handling, check for player entering open door ---
            for idx, door in enumerate(getattr(self.world, "doors", [])):
                dist = math.hypot(self.player.x - door.x, self.player.y - door.y)
                if door.open and dist < 80 and not next_level_triggered and self.door_transition is None:
                    print("Level complete! Loading next/previous level...")
                    # --- Backtrack logic: only allow backtracking if we are not at the first level ---
                    if self.prev_level_index is not None and self.level_index != 0 and idx == self.entry_door_idx:
                        # Start door transition for backtracking
                        self.door_transition = (idx, pygame.time.get_ticks() / 1000.0, "back")
                        next_level_triggered = True
                        break
                    # --- Forward logic ---
                    self.door_transition = (idx, pygame.time.get_ticks() / 1000.0, "forward")
                    next_level_triggered = True
                    break

            if game_over:
                # Draw game over overlay
                overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                font_big = pygame.font.SysFont("arial", 72, bold=True)
                font_btn = pygame.font.SysFont("arial", 36, bold=True)
                text_game_over = font_big.render("GAME OVER", True, (255, 80, 80))
                self.screen.blit(text_game_over, (WIN_W // 2 - text_game_over.get_width() // 2, WIN_H // 2 - 180))

                # Draw buttons
                restart_text = font_btn.render("Restart (R)", True, (255, 255, 255))
                exit_text = font_btn.render("Exit (ESC)", True, (255, 255, 255))
                restart_rect = pygame.Rect(WIN_W // 2 - 160, WIN_H // 2, 320, 60)
                exit_rect = pygame.Rect(WIN_W // 2 - 160, WIN_H // 2 + 80, 320, 60)
                pygame.draw.rect(self.screen, (80, 160, 80), restart_rect, border_radius=12)
                pygame.draw.rect(self.screen, (160, 80, 80), exit_rect, border_radius=12)
                self.screen.blit(restart_text, (restart_rect.x + restart_rect.width // 2 - restart_text.get_width() // 2,
                                                restart_rect.y + restart_rect.height // 2 - restart_text.get_height() // 2))
                self.screen.blit(exit_text, (exit_rect.x + exit_rect.width // 2 - exit_text.get_width() // 2,
                                             exit_rect.y + exit_rect.height // 2 - exit_text.get_height() // 2))
                pygame.display.flip()
                continue

            # --- Animation and combat logic ---
            # Update player animation
            self.player.update_animation(dt)
            # Update sword swing animation and logic
            if sword_swing and not self.player.sword_swinging:
                self.player.start_sword_swing()
                weapon = self.player.equipment.get("Main Hand")
                if weapon is not None and hasattr(weapon, "get_attack_damage"):
                    # Roll weapon damage
                    weapon_damage = weapon.get_attack_damage()
                    # Roll player base melee damage: 1-5 for strength 1, 6-10 for strength 2, etc.
                    min_dmg = 1 + (self.player.strength - 1) * 5
                    max_dmg = 5 + (self.player.strength - 1) * 5
                    player_base_melee_damage = random.randint(min_dmg, max_dmg)
                    # Final damage is product of both rolls
                    self.sword_swing_damage = weapon_damage * player_base_melee_damage
                else:
                    # No weapon: just roll player base melee damage
                    min_dmg = 1 + (self.player.strength - 1) * 5
                    max_dmg = 5 + (self.player.strength - 1) * 5
                    self.sword_swing_damage = random.randint(min_dmg, max_dmg)
                self.sword_swing_hit_targets = set()
                self.sword_sound.play()
            if hasattr(self.player, "update_sword"):
                self.player.update_sword(dt, len(self.sword_slash_imgs))

            # Fireball shooting logic
            if shoot_fireball:
                dx, dy = self.player.last_dir if hasattr(self.player, "last_dir") else (1, 0)
                if dx != 0 or dy != 0:
                    facing_left = dx < 0
                    fireball_cost = 20  # Match Fireball.cost default
                    if hasattr(self.player, "mana") and self.player.mana >= fireball_cost:
                        weapon = self.player.equipment.get("Main Hand")
                        weapon_magic = 1  # Default to 1 if not magic weapon
                        if weapon is not None and hasattr(weapon, "get_magic_damage"):
                            if getattr(weapon, "magic_min", 0) and getattr(weapon, "magic_max", 0):
                                weapon_magic = weapon.get_magic_damage() or 1
                        spell_damage = random.randint(self.player.intelligence * 10, self.player.intelligence * 10 + 9)
                        fireball_damage = weapon_magic * spell_damage
                        # Always pass fireball_damage as argument
                        fireball = Fireball(self.player.x, self.player.y, dx, dy, facing_left=facing_left, damage=fireball_damage, cost=fireball_cost)
                        self.fireballs.append(fireball)
                        self.player.mana -= fireball_cost
                        if self.player.mana < 0:
                            self.player.mana = 0
                        self.cast_sound.play()
                    else:
                        pass

            # --- Sword damage to targets and enemies ---
            if hasattr(self.player, "sword_swinging") and self.player.sword_swinging:
                # Calculate sword hitbox in front of player, facing mouse or last direction
                mx, my = pygame.mouse.get_pos()
                world_mx = mx + self.camera.x
                world_my = my + self.camera.y
                px, py = self.player.x, self.player.y

                dx = world_mx - px
                dy = world_my - py
                mag = math.hypot(dx, dy)
                if mag > 0:
                    dx /= mag
                    dy /= mag
                else:
                    dx, dy = self.player.last_dir

                sword_w, sword_h = 48, 48
                offset = 32
                hitbox_x = px + dx * offset - sword_w // 2
                hitbox_y = py + dy * offset - sword_h // 2
                sword_hitbox = pygame.Rect(int(hitbox_x), int(hitbox_y), sword_w, sword_h)

                # Targets
                for target in self.world.targets:
                    if (
                        hasattr(target, "respawn_timer") and target.respawn_timer <= 0
                        and sword_hitbox.colliderect(target.rect())
                        and id(target) not in self.sword_swing_hit_targets
                    ):
                        damage = self.sword_swing_damage if self.sword_swing_damage is not None else random.randint(10, 15)
                        target.hit_points -= damage
                        show_damage_numbers(self, target.x, target.y - 40, damage)
                        show_health_bar(self, target)
                        self.sword_swing_hit_targets.add(id(target))
                        if target.hit_points <= 0:
                            target.respawn_timer = 5.0
                            self.world.remove_target_solid(target)
                            target.hit_points = 300  # Reset HP for respawn

                # Enemies - now allow sword to kill enemies and remove their hitbox
                enemies_to_remove = set()
                for i, enemy in enumerate(self.world.enemies):
                    enemy_rect = enemy.draw_enemy() if hasattr(enemy, "draw_enemy") else pygame.Rect(enemy.x-20, enemy.y-30, 40, 60)
                    if (
                        hasattr(enemy, "hit_points")
                        and sword_hitbox.colliderect(enemy_rect)
                        and id(enemy) not in self.sword_swing_hit_targets
                    ):
                        damage = self.sword_swing_damage if self.sword_swing_damage is not None else random.randint(10, 15)
                        enemy.hit_points -= damage
                        show_damage_numbers(self, enemy.x, enemy.y - 40, damage)
                        show_health_bar(self, enemy)
                        self.sword_swing_hit_targets.add(id(enemy))
                        self.slime_damage_sound.play()
                        if enemy.hit_points <= 0:
                            self.slime_death_sound.play()
                            self.player.add_xp(getattr(enemy, "xp_reward", 5))
                            # --- Drop logic ---
                            drop_items = None
                            if hasattr(enemy, "get_drop"):
                                drop_items = enemy.get_drop()
                            if drop_items:
                                # drop_items is now a list, not a dict
                                for drop_item in drop_items:
                                    item_visual = drop_item.get("image", None)
                                    self.dropped_items.append({
                                        "item_data": drop_item,
                                        "x": enemy.x,
                                        "y": enemy.y,
                                        "image": item_visual,
                                        "rect": pygame.Rect(int(enemy.x-24), int(enemy.y-24), 48, 48)
                                    })
                            enemies_to_remove.add(i)
                            # --- Track defeated enemy by initial position ---
                            # Use initial positions from initial_enemy_positions_per_level
                            initial_positions = self.initial_enemy_positions_per_level.get(self.level_index, [])
                            # Find the closest initial position to this enemy
                            min_dist = float('inf')
                            closest_pos = None
                            for pos in initial_positions:
                                dist = math.hypot(enemy.x - pos[0], enemy.y - pos[1])
                                if dist < min_dist:
                                    min_dist = dist
                                    closest_pos = pos
                            if closest_pos is not None:
                                defeated = self.defeated_enemies_per_level.setdefault(self.level_index, set())
                                defeated.add(closest_pos)
                # Remove defeated enemies and their hitboxes
                self.world.enemies = [e for i, e in enumerate(self.world.enemies) if i not in enemies_to_remove]
                self.enemy_bodies = [b for i, b in enumerate(self.enemy_bodies) if i not in enemies_to_remove]
                self.enemy_shapes = [s for i, s in enumerate(self.enemy_shapes) if i not in enemies_to_remove]

            # Reset buffer only when animation ends
            if hasattr(self.player, "sword_swinging") and not self.player.sword_swinging:
                self.sword_swing_damage = None
                self.sword_swing_hit_targets = set()

            # --- Fireball update and combat ---
            fireballs_to_remove = set()
            enemies_to_remove = set()
            for f_idx, fireball in enumerate(self.fireballs):
                if hasattr(fireball, "exploding") and fireball.exploding:
                    fireball.explosion_timer += dt
                    if fireball.explosion_timer >= 0.05:
                        fireball.explosion_timer = 0.0
                        fireball.explosion_frame += 1
                        if fireball.explosion_frame >= len(self.explosion_imgs):
                            fireballs_to_remove.add(f_idx)
                    continue
                fireball.update(dt)
                if not (0 <= fireball.x < self.world.w * 48 and 0 <= fireball.y < self.world.h * 48):
                    if not fireball.exploding:
                        fireball.exploding = True
                        self.explosion_sound.play()
                    continue
                for i, enemy in enumerate(self.world.enemies):
                    # Fix: correct ternary syntax for enemy_rect
                    if hasattr(enemy, "draw_enemy"):
                        enemy_rect = enemy.draw_enemy()
                    else:
                        enemy_rect = pygame.Rect(enemy.x-20, enemy.y-30, 40, 60)
                    if fireball.rect().colliderect(enemy_rect):
                        if not fireball.exploding:
                            fireball.exploding = True
                            self.explosion_sound.play()
                        damage = fireball.damage  # <-- Use fireball's actual damage
                        if hasattr(enemy, "hit_points"):
                            enemy.hit_points -= damage
                            show_damage_numbers(self, enemy.x, enemy.y - 40, damage)
                            show_health_bar(self, enemy)
                            self.slime_damage_sound.play()
                            if enemy.hit_points <= 0:
                                self.slime_death_sound.play()
                                self.player.add_xp(getattr(enemy, "xp_reward", 5))
                                # --- Drop logic ---
                                drop_items = None
                                if hasattr(enemy, "get_drop"):
                                    drop_items = enemy.get_drop()
                                if drop_items:
                                    for drop_item in drop_items:
                                        item_visual = drop_item.get("image", None)
                                        self.dropped_items.append({
                                            "item_data": drop_item,
                                            "x": enemy.x,
                                            "y": enemy.y,
                                            "image": item_visual,
                                            "rect": pygame.Rect(int(enemy.x-24), int(enemy.y-24), 48, 48)
                                        })
                                enemies_to_remove.add(i)
                                # --- Track defeated enemy by initial position ---
                                initial_positions = self.initial_enemy_positions_per_level.get(self.level_index, [])
                                min_dist = float('inf')
                                closest_pos = None
                                for pos in initial_positions:
                                    dist = math.hypot(enemy.x - pos[0], enemy.y - pos[1])
                                    if dist < min_dist:
                                        min_dist = dist
                                        closest_pos = pos
                                if closest_pos is not None:
                                    defeated = self.defeated_enemies_per_level.setdefault(self.level_index, set())
                                    defeated.add(closest_pos)
                        break
                else:
                    for t_idx, target in enumerate(self.world.targets):
                        if hasattr(target, "respawn_timer") and target.respawn_timer <= 0 and fireball.rect().colliderect(target.rect()):
                            if not fireball.exploding:
                                fireball.exploding = True
                                self.explosion_sound.play()
                            damage = fireball.damage  # <-- Use fireball's actual damage
                            target.hit_points -= damage
                            show_damage_numbers(self, target.x, target.y - 40, damage)
                            show_health_bar(self, target)
                            if target.hit_points <= 0:
                                target.respawn_timer = 5.0
                                self.world.remove_target_solid(target)
                                target.hit_points = 300
                            break

            self.fireballs = [f for i, f in enumerate(self.fireballs) if i not in fireballs_to_remove]
            # Remove defeated enemies and their hitboxes in sync
            if enemies_to_remove:
                self.world.enemies = [e for i, e in enumerate(self.world.enemies) if i not in enemies_to_remove]
                self.enemy_bodies = [b for i, b in enumerate(self.enemy_bodies) if i not in enemies_to_remove]
                self.enemy_shapes = [s for i, s in enumerate(self.enemy_shapes) if i not in enemies_to_remove]

            # Update targets' respawn timers
            for target in self.world.targets:
                if target.respawn_timer > 0:
                    target.respawn_timer -= dt
                    if target.respawn_timer <= 0:
                        self.world.add_target_solid(target)

            # Camera update
            self.camera.update(self.player.x, self.player.y, dt)
            view = self.camera.view_rect()

            # --- DRAWING ---
            draw_game_frame(self, dt)
            # --- Dropped item pickup logic ---
            player_rect = self.player.rect()
            for dropped in self.dropped_items[:]:
                keys = pygame.key.get_pressed()
                if player_rect.colliderect(dropped["rect"]) and keys[pygame.K_e]:
                    # Find first empty inventory slot
                    for idx in range(len(self.player.inventory)):
                        if self.player.inventory[idx] is None:
                            from config.player import Item
                            self.player.inventory[idx] = Item(**dropped["item_data"])
                            break
                    self.dropped_items.remove(dropped)
            # Draw dropped items on ground with a shining effect and pickup hint
            for dropped in self.dropped_items:
                px, py = world_to_screen(dropped["x"], dropped["y"], self.camera.x, self.camera.y)
                # Draw item image if available
                if dropped["image"]:
                    img = pygame.transform.scale(dropped["image"], (40, 40))
                    self.screen.blit(img, (px - 20, py - 20))
                else:
                    # Always draw a circle for dropped items if no image
                    pygame.draw.circle(self.screen, (255, 215, 0), (px, py), 20)
                # --- Shining effect ---
                shine_radius = 28
                shine_alpha = int(128 + 64 * math.sin(pygame.time.get_ticks() / 300.0 + px + py))
                shine_surface = pygame.Surface((shine_radius*2, shine_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(shine_surface, (255, 255, 160, shine_alpha), (shine_radius, shine_radius), shine_radius)
                self.screen.blit(shine_surface, (px - shine_radius, py - shine_radius), special_flags=pygame.BLEND_RGBA_ADD)
                # --- Pickup hint ---
                if player_rect.colliderect(dropped["rect"]):
                    font = pygame.font.SysFont("arial", 22, bold=True)
                    hint_surf = font.render("Press E to pick up", True, (255, 255, 160))
                    # Draw hint just above the item
                    self.screen.blit(hint_surf, (px - hint_surf.get_width() // 2, py - 44))
                    # --- Draw fade message if present ---
                    for dmg in self.damage_numbers:
                        # Only check for string values before calling .startswith
                        if isinstance(dmg.get("value", ""), str) and dmg.get("value", "").startswith("Level ") and abs(dmg["x"] - px) < 40 and abs(dmg["y"] - (py - 44)) < 40:
                            msg_surf = font.render(str(dmg["value"]), True, dmg["color"])
                            msg_surf.set_alpha(dmg["alpha"])
                            self.screen.blit(msg_surf, (px - msg_surf.get_width() // 2, py - 72))
            # Remove all other drawing code from the main loop!

            mx, my = pygame.mouse.get_pos()
            world_mx = mx + self.camera.x
            world_my = my + self.camera.y
            self.player.update_direction_towards(world_mx, world_my)

            # Update health bars each frame
            update_health_bars(self, dt)
            # Draw health bars for targets
            draw_health_bars(self, self.screen, self.camera)

            # Example: check collision between player and each enemy manually
            for i, enemy_shape in enumerate(self.enemy_shapes):
                # Get positions
                px, py = self.player_body.position
                ex, ey = self.enemy_bodies[i].position
                # Get radii
                pr = self.player_shape.radius
                er = enemy_shape.radius
                # Check circle collision by distance
                dist = math.hypot(px - ex, py - ey)
                if dist < pr + er:
                    print("Player collided with enemy!")
                    # ...your logic...

            # You can add similar checks for other entities (torch, fireballs, etc.)
            # Example for torch (if you add a pymunk shape for it):
            # if self.player_shape.shapes_collide(self.torch_shape).points:
            #     print("Player collided with torch!")
            #     # ...your logic...

            # --- Player movement ---
            self.player.move_and_collide(dt, self.world.solids)
            self.player_body.position = (self.player.x, self.player.y)

            # --- Enemy movement and attack ---
            slime_moving = False
            # Remove old monster_target logic
            # Instead, for each enemy, determine if player or torch is in visibility range
            for i, enemy in enumerate(self.world.enemies):
                prev_x, prev_y = enemy.x, enemy.y
                other_enemy_rects = [e.draw_enemy() for j, e in enumerate(self.world.enemies) if j != i]
                player_rect = self.player.rect()
                # Determine target for each enemy
                player_in_range = enemy.sees_target(self.player.x, self.player.y)
                torch_in_range = False
                torch_pos = self.torch_ground_pos
                if self.torch_on_ground or self.torch_following:
                    torch_x, torch_y = torch_pos
                    torch_in_range = enemy.sees_target(torch_x, torch_y)
                # Only chase if player or torch is in range
                if player_in_range:
                    monster_target = (self.player.x, self.player.y)
                elif torch_in_range:
                    monster_target = torch_pos
                else:
                    monster_target = (enemy.x, enemy.y)  # Idle
                enemy.update(dt, monster_target, self.world.solids, player_rect, other_enemy_rects, player=self.player)
                # Defensive: only update enemy_bodies if index exists
                if i < len(self.enemy_bodies):
                    self.enemy_bodies[i].position = (enemy.x, enemy.y)
                if enemy.x != prev_x or enemy.y != prev_y:
                    slime_moving = True

            
            # --- Torch movement and wiggle logic ---
            if self.torch_following:
                # Smoothly move torch toward player, but cap movement per frame
                px, py = self.player.x, self.player.y
                tx, ty = self.torch_ground_pos
                dx = px - tx
                dy = py - ty
                dist = math.hypot(dx, dy)
                max_step = 320 * dt  # torch max speed (pixels/sec)
                if dist > 0.5:
                    step = min(dist, max_step)
                    move_x = dx / dist * step
                    move_y = dy / dist * step
                    # Calculate next position
                    next_tx = tx + move_x
                    next_ty = ty + move_y
                    torch_rect = pygame.Rect(int(next_tx - 8), int(next_ty - 16), 16, 32)
                    player_rect = self.player.rect()
                    # Prevent torch from entering player's hitbox in follow mode
                    if torch_rect.collidepoint(player_rect.topleft):
                        # Do not update torch position if it would collide
                        pass
                    else:
                        self.torch_ground_pos = (next_tx, next_ty)
                # Wiggle animation: update 8 times per second
                self.torch_wiggle_timer += dt
                if self.torch_wiggle_timer >= 0.125:
                    self.torch_wiggle_timer = 0.0
                    wiggle_x = random.randint(-4, 4)
                    wiggle_y = random.randint(-4, 4)
                    self.torch_wiggle_offset = (wiggle_x, wiggle_y)
            elif self.torch_on_ground:
                # Torch moves on its own when on ground
                self.torch_move_timer += dt
                if self.torch_move_timer > 2.0:
                    self.torch_move_timer = 0.0
                    self.torch_vel_x += random.uniform(-40, 40)
                    self.torch_vel_y += random.uniform(-40, 40)
                    speed = math.hypot(self.torch_vel_x, self.torch_vel_y)
                    max_speed = 120.0
                    if speed > max_speed:
                        self.torch_vel_x *= max_speed / speed
                        self.torch_vel_y *= max_speed / speed
                orig_tx, orig_ty = self.torch_ground_pos
                tx = orig_tx + self.torch_vel_x * dt
                ty = orig_ty + self.torch_vel_y * dt
                torch_rect = pygame.Rect(int(tx - 8), int(ty - 16), 16, 32)
                collided = False
                # Check collision with walls
                for wall in self.world.solids:
                    if torch_rect.colliderect(wall):
                        collided = True
                        break
                # Prevent torch from entering player's hitbox (rect)
                player_rect = self.player.rect()
                if torch_rect.collidepoint(player_rect.topleft):
                    collided = True
                    # Move torch back to previous position and bounce away
                    # Calculate direction away from player center
                    away_dx = tx - self.player.x
                    away_dy = ty - self.player.y
                    away_dist = math.hypot(away_dx, away_dy)
                    if away_dist > 0:
                        # Push torch away by the minimum amount to be outside player hitbox
                        push_strength = max(self.player.w, self.player.h) // 2 + 8
                        tx = self.player.x + (away_dx / away_dist) * (push_strength + 2)
                        ty = self.player.y + (away_dy / away_dist) * (push_strength + 2)
                    else:
                        # If exactly overlapping, move torch directly up
                        ty = self.player.y - (self.player.h // 2 + 8)
                if not collided:
                    self.torch_ground_pos = (tx, ty)
                else:
                    self.torch_ground_pos = (tx, ty)
                    self.torch_vel_x = -self.torch_vel_x * 0.8
                    self.torch_vel_y = -self.torch_vel_y * 0.8

    def player_near_torch(self):
        if self.torch_on_ground or self.torch_following:
            torch_px, torch_py = world_to_screen(
                self.torch_ground_pos[0] - 15 + self.torch_wiggle_offset[0],
                self.torch_ground_pos[1] - 30 + self.torch_wiggle_offset[1],
                self.camera.x, self.camera.y
            )
            torch_center = (torch_px + 15, torch_py + 30)
            dist = math.hypot(self.player.x - torch_center[0], self.player.y - torch_center[1])
            return dist < 100  # Considered near if within 100 pixels
        return False

def _slot_matches(item, slot_name):
    # Helper: allow "Accessory N" items to go to any "Accessory N" slot
    slot = item.get_slot() if hasattr(item, "get_slot") else None
    if slot is None:
        return False
    if slot == slot_name:
        return True
    # Allow "Accessory N" items to go to any "Accessory" slot
    if slot.startswith("Accessory") and slot_name.startswith("Accessory"):
        return True
    return False

if __name__ == "__main__":
    Game().run()