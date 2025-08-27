import pygame
import math
from config.config import TILE_SIZE, MAP_CHARS, COL_FLOOR_A, COL_FLOOR_B
from config.enemy import Enemy
from config.target import Target
from config.skeleton import Skeleton  # <-- Add this import
import random

class World:
    def __init__(self, level_layout, enemy_imgs, target_imgs, door_img=None, door_img_open=None, game_level=1, monster_level_min=1, monster_level_max=1, skeleton_walk_frames=None, skeleton_attack_frames=None):
        self.layout = level_layout
        self.w = len(level_layout[0])
        self.h = len(level_layout)
        self.solids: list[pygame.Rect] = []
        self.enemies: list[Enemy] = []
        self.targets: list[Target] = []
        self.doors: list = []  # Add this line
        self.door_img = door_img  # Store door image
        self.door_img_open = door_img_open  # Store open door image
        # Load wall and ground textures
        self.wall_texture = pygame.image.load("textures/map/wall.jpg").convert()
        self.wall_texture = pygame.transform.scale(self.wall_texture, (TILE_SIZE, TILE_SIZE))
        self.ground_texture = pygame.image.load("textures/map/ground.png").convert()
        self.ground_texture = pygame.transform.scale(self.ground_texture, (TILE_SIZE, TILE_SIZE))
        for y, row in enumerate(level_layout):
            for x, ch in enumerate(row):
                if MAP_CHARS.get(ch, 0) == 1:
                    self.solids.append(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                elif MAP_CHARS.get(ch, 0) == 2:
                    img = random.choice(enemy_imgs)
                    img = pygame.transform.scale(img, (40, 60)).convert_alpha()
                    # Monster level: monster_level_min..monster_level_max
                    level = random.randint(monster_level_min, monster_level_max)
                    self.enemies.append(Enemy(x*TILE_SIZE+TILE_SIZE/2, y*TILE_SIZE+TILE_SIZE/2, 28, 36, img=img, level=level))
                elif MAP_CHARS.get(ch, 0) == 3:
                    img = random.choice(enemy_imgs)
                    img = pygame.transform.scale(img, (int(40*1.5), int(60*1.5))).convert_alpha()
                    new_w = int(28 * 1.5)
                    new_h = int(36 * 1.5)
                    # Big monster level: monster_level_min..monster_level_max
                    level = random.randint(monster_level_min, monster_level_max)
                    self.enemies.append(Enemy(x*TILE_SIZE+TILE_SIZE/2, y*TILE_SIZE+TILE_SIZE/2, new_w, new_h, img=img, level=level))
                elif MAP_CHARS.get(ch, 0) == 4:
                    img = random.choice(target_imgs)
                    img = pygame.transform.scale(img, (40, 60)).convert_alpha()
                    tx = x*TILE_SIZE+TILE_SIZE/2
                    ty = y*TILE_SIZE+TILE_SIZE/2
                    self.targets.append(Target(tx, ty, 40, 60, img=img))
                    solid_rect = pygame.Rect(
                        int(tx - 20),  # 40/2
                        int(ty - 30),  # 60/2
                        40, 60
                    )
                    self.solids.append(solid_rect)
                elif MAP_CHARS.get(ch, 0) == 5:
                    # Door
                    from config.door import Door
                    tx = x*TILE_SIZE+TILE_SIZE/2
                    ty = y*TILE_SIZE+TILE_SIZE/2
                    door = Door(tx, ty, 48, 72, img=self.door_img, img_open=self.door_img_open)
                    self.doors.append(door)
                    solid_rect = pygame.Rect(
                        int(tx - 24),  # 48/2
                        int(ty - 36),  # 72/2
                        48, 72
                    )
                    self.solids.append(solid_rect)
                elif MAP_CHARS.get(ch, 0) == 6:
                    walk_frames = skeleton_walk_frames if skeleton_walk_frames is not None else None
                    attack_frames = skeleton_attack_frames if skeleton_attack_frames is not None else None
                    new_w = int(28 * 1.4)
                    new_h = int(36 * 1.4)
                    level = random.randint(monster_level_min, monster_level_max)
                    self.enemies.append(Skeleton(
                        x*TILE_SIZE+TILE_SIZE//2,
                        y*TILE_SIZE+TILE_SIZE//2,
                        new_w, new_h,
                        walk_frames=walk_frames,
                        attack_frames=attack_frames,
                        level=level
                    ))

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, view_rect: pygame.Rect) -> None:
        start_x = max(0, view_rect.left // TILE_SIZE)
        end_x = min(self.w, math.ceil(view_rect.right / TILE_SIZE))
        start_y = max(0, view_rect.top // TILE_SIZE)
        end_y = min(self.h, math.ceil(view_rect.bottom / TILE_SIZE))
        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                world_x = tx*TILE_SIZE - cam_x
                world_y = ty*TILE_SIZE - cam_y
                r = pygame.Rect(world_x, world_y, TILE_SIZE, TILE_SIZE)
                # Bounds checking for ty and tx
                if ty < 0 or ty >= len(self.layout):
                    continue  # Skip out-of-bounds rows
                row = self.layout[ty]
                if tx < 0 or tx >= len(row):
                    continue  # Skip out-of-bounds columns
                ch = row[tx]
                if MAP_CHARS.get(ch, 0) == 1:
                    surf.blit(self.wall_texture, r)
                else:
                    surf.blit(self.ground_texture, r)

        # Draw doors after tiles
        for door in getattr(self, "doors", []):
            door.draw(surf, cam_x, cam_y)

    def remove_target_solid(self, target: Target):
        target_rect = pygame.Rect(
            int(target.x - target.w // 2),
            int(target.y - target.h // 2),
            target.w, target.h
        )
        self.solids = [r for r in self.solids if not r.colliderect(target_rect)]

    def add_target_solid(self, target: Target):
        target_rect = pygame.Rect(
            int(target.x - target.w // 2),
            int(target.y - target.h // 2),
            target.w, target.h
        )
        self.solids.append(target_rect)

    def update(self, dt: float, target_pos, solids: list[pygame.Rect], player_rect: pygame.Rect, other_enemies: list[pygame.Rect], player=None):
        # ...existing code...
        for i, enemy in enumerate(self.enemies):
            # ...existing code...
            # Skeleton attack animation trigger
            if hasattr(enemy, "start_attack") and hasattr(enemy, "update_attack_anim"):
                # Only trigger attack animation if close to player and can attack
                if player and hasattr(enemy, "can_attack_player") and enemy.can_attack_player(player.x, player.y):
                    if not enemy.attacking:
                        enemy.start_attack()
                enemy.update_attack_anim(dt)
            # ...existing code...