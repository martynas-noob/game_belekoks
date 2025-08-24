from __future__ import annotations
import math
import sys
from turtle import Screen
import pygame
import os
from dataclasses import dataclass
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# -----------------------------
# Config
# -----------------------------

WIN_W, WIN_H = 1920, 1080
PIXEL_SCALE = 1
FPS = 120

TILE_SIZE = 48
MAP_CHARS = {
    '#': 1,   # wall
    '.': 0,   # floor
    '0': 2,   # enemy spawn
    '8': 3,   # merged enemy spawn
    '5': 4,   # target
}

LEVEL_1 = [
    "############################",
    "#..........................#",
    "#............#.............#",
    "#..........5.#.......0.....#",
    "#..........5.#.......0.... #",
    "#............#.............#",
    "#..........................#",
    "#..........................#",
    "#...........000000000......#",
    "#..........................#",
    "#..........................#",
    "############################",

]

COL_BG = (22, 26, 33)
COL_FLOOR_A = (36, 42, 50)
COL_FLOOR_B = (32, 38, 46)
COL_WALL = (70, 86, 104)
COL_PLAYER = (240, 240, 240)
COL_ENEMY = (200, 70, 70)
COL_ACCENT = (160, 200, 255)

# ----------------------------------------
#
# -----------------------------
# Helpers
# -----------------------------

def world_to_screen(x: float, y: float, cam_x: float, cam_y: float) -> tuple[int, int]:
    return int(x - cam_x), int(y - cam_y)

# ----------------------------------------
#
# -----------------------------
# Player
# -----------------------------

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
        # Update last_dir and facing_left if moving
        if dx != 0 or dy != 0:
            self.last_dir = (dx, dy)
            if dx < 0:
                self.facing_left = True
            elif dx > 0:
                self.facing_left = False

# ----------------------------------------
#
# -----------------------------
# Enemy
# -----------------------------

@dataclass
class Enemy:
    x: float
    y: float
    w: int = 28
    h: int = 36
    speed: float = 280.0
    cooldown: float = 0.0  # seconds
    img: pygame.Surface = None  # Add this line
    facing_left: bool = False
    exploding: bool = False
    explosion_frame: int = 0
    explosion_timer: float = 0.0

    def draw_enemy(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, img=None, explosion_imgs=None):
        px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
        image = self.img
        if image:
            draw_img = pygame.transform.flip(image, True, False) if self.facing_left else image
            surf.blit(draw_img, (px - image.get_width() // 2, py - image.get_height() // 2))
        else:
            rect = pygame.Rect(px - self.w // 2, py - self.h // 2, self.w, self.h)
            pygame.draw.rect(surf, COL_ENEMY, rect, border_radius=6)

    def update(self, dt: float, player: Player, solids: list[pygame.Rect]):
        if self.cooldown > 0:
            self.cooldown -= dt
            return  # Don't move while on cooldown

        dx, dy = player.x - self.x, player.y - self.y
        # Set facing direction
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

# ----------------------------------------
#
# --- Add this Fireball class near Player/Enemy classes ---
@dataclass
class Fireball:
    x: float
    y: float
    dx: float
    dy: float
    speed: float = 300.0
    radius: int = 20
    facing_left: bool = False
    exploding: bool = False
    explosion_frame: int = 0
    explosion_timer: float = 0.0

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)

    def update(self, dt: float):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, img=None, explosion_imgs=None):
        px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
        if self.exploding and explosion_imgs:
            frame = min(self.explosion_frame, len(explosion_imgs) - 1)
            exp_img = explosion_imgs[frame]
            surf.blit(exp_img, (px - exp_img.get_width() // 2, py - exp_img.get_height() // 2))
        elif img:
            angle = -math.degrees(math.atan2(self.dy, self.dx))
            rotated_img = pygame.transform.rotate(img, angle)
            surf.blit(rotated_img, (px - rotated_img.get_width() // 2, py - rotated_img.get_height() // 2))
        else:
            pygame.draw.circle(surf, (255, 120, 40), (px, py), 15)

# ----------------------------------------
#
# -----------------------------
# Target
# -----------------------------

@dataclass
class Target:
    x: float
    y: float
    w: int = 40
    h: int = 60
    img: pygame.Surface = None
    respawn_timer: float = 0.0  # seconds

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        if self.respawn_timer <= 0 and self.img:
            px, py = world_to_screen(self.x, self.y, cam_x, cam_y)
            surf.blit(self.img, (px - self.w // 2, py - self.h // 2))

# ----------------------------------------
#
# -----------------------------
# World / Map
# -----------------------------

class World:
    def __init__(self, layout: list[str], monster_img: pygame.Surface, target_img: pygame.Surface):
        self.layout = layout
        self.w = len(layout[0])
        self.h = len(layout)
        self.solids: list[pygame.Rect] = []
        self.enemies: list[Enemy] = []
        self.targets: list[Target] = []
        for y, row in enumerate(layout):
            for x, ch in enumerate(row):
                if MAP_CHARS.get(ch, 0) == 1:
                    self.solids.append(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                elif MAP_CHARS.get(ch, 0) == 2:
                    img = pygame.transform.scale(monster_img, (40, 60)).convert_alpha()
                    self.enemies.append(Enemy(x*TILE_SIZE+TILE_SIZE/2, y*TILE_SIZE+TILE_SIZE/2, 28, 36, img=img))
                elif MAP_CHARS.get(ch, 0) == 3:
                    new_w = int(28 * 1.5)
                    new_h = int(36 * 1.5)
                    img = pygame.transform.scale(monster_img, (int(40*1.5), int(60*1.5))).convert_alpha()
                    self.enemies.append(Enemy(x*TILE_SIZE+TILE_SIZE/2, y*TILE_SIZE+TILE_SIZE/2, new_w, new_h, img=img))
                elif MAP_CHARS.get(ch, 0) == 4:
                    img = pygame.transform.scale(target_img, (40, 60)).convert_alpha()
                    tx = x*TILE_SIZE+TILE_SIZE/2
                    ty = y*TILE_SIZE+TILE_SIZE/2
                    self.targets.append(Target(tx, ty, 40, 60, img=img))
                    # Add a slightly smaller solid for the target
                    solid_rect = pygame.Rect(
                        int(tx - 20),  # 40/2
                        int(ty - 30),  # 60/2
                        40, 60
                    )
                    self.solids.append(solid_rect)

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
                ch = self.layout[ty][tx]
                if MAP_CHARS.get(ch, 0) == 1:
                    pygame.draw.rect(surf, COL_WALL, r)
                else:
                    col = COL_FLOOR_A if (tx+ty) % 2 == 0 else COL_FLOOR_B
                    pygame.draw.rect(surf, col, r)

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

# ----------------------------------------
#
# -----------------------------
# Camera
# -----------------------------

@dataclass
class Camera:
    x: float = 0
    y: float = 0
    lerp: float = 12.0

    def update(self, target_x: float, target_y: float, dt: float) -> None:
        desired_x = target_x - WIN_W/2
        desired_y = target_y - WIN_H/2
        self.x += (desired_x - self.x) * min(1.0, self.lerp*dt)
        self.y += (desired_y - self.y) * min(1.0, self.lerp*dt)

    def view_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), WIN_W, WIN_H)

# ----------------------------------------
#
# -----------------------------
# Game
# -----------------------------

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Top‑down 2D Base with Enemy")
        self.clock = pygame.time.Clock()
        self.monster_img_original = pygame.image.load("monster.png").convert_alpha()
        self.monster_img = pygame.transform.scale(self.monster_img_original, (40, 60))
        self.target_img = pygame.image.load("target.png").convert_alpha()
        self.target_img = pygame.transform.scale(self.target_img, (40, 60))
        self.world = World(LEVEL_1, self.monster_img_original, self.target_img)
        # Find player spawn (first floor tile)
        for y, row in enumerate(LEVEL_1):
            for x, ch in enumerate(row):
                if ch == '.':
                    spawn_x = x * TILE_SIZE + TILE_SIZE / 2
                    spawn_y = y * TILE_SIZE + TILE_SIZE / 2
                    break
            else:
                continue
            break
        self.spawn_x = spawn_x  # Save spawn position
        self.spawn_y = spawn_y
        self.player = Player(x=spawn_x, y=spawn_y)
        self.camera = Camera()
        self.font = pygame.font.Font(None, 24)
        self.hero_img = pygame.image.load("hero.png").convert_alpha()
        self.hero_img = pygame.transform.scale(self.hero_img, (40, 60))
        self.torch_img = pygame.image.load("torch.png").convert_alpha()
        self.torch_img = pygame.transform.scale(self.torch_img, (24, 48))  # Adjust size as needed
        self.fireball_img = pygame.image.load("fireball.png").convert_alpha()
        self.fireball_img = pygame.transform.scale(self.fireball_img, (60, 30))  # Bigger fireballs

        # Lighting overlay setup
        self.darkness_alpha = 180  # 0=fully bright, 255=fully dark
        self.torch_glow_radius = 120  # pixels

        self.fireballs: list[Fireball] = []

        self.explosion_imgs = [
            pygame.image.load(f"explosion{i}.png").convert_alpha()
            for i in range(1, 9)
        ]

        self.cast_sound = pygame.mixer.Sound("cast.mp3")
        self.explosion_sound = pygame.mixer.Sound("explosion.mp3")

    def draw_torch_glow(self, surface, center, radius):
        glow = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        for r in range(radius, 0, -2):
            # Alpha is highest at the edge, lowest in the center (center is brightest)
            alpha = int(self.darkness_alpha * (1 - (r / radius)) ** 2)
            color = (
                int(255 - 55 * (1 - r / radius)),
                int(240 - 60 * (1 - r / radius)),
                int(180 - 100 * (1 - r / radius)),
                alpha
            )
            pygame.draw.circle(glow, color, (radius, radius), r)
        surface.blit(glow, (center[0] - radius, center[1] - radius))

    def draw_fireball_glow(self, surface, center, radius):
        glow = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        for r in range(radius, 0, -2):
            alpha = int(self.darkness_alpha * (1 - (r / radius)) ** 2)
            color = (
                int(255 - 55 * (1 - r / radius)),
                int(240 - 60 * (1 - r / radius)),
                int(180 - 100 * (1 - r / radius)),
                alpha
            )
            pygame.draw.circle(glow, color, (radius, radius), r)
        surface.blit(glow, (center[0] - radius, center[1] - radius))

    def draw_light_mask(self, center, radius):
        mask = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        # Draw the torch glow first
        self.draw_torch_glow(mask, center, radius)
        # Block the light with walls (draw black rectangles with high alpha)
        cam_x, cam_y = self.camera.x, self.camera.y
        for wall in self.world.solids:
            wx, wy = wall.x - cam_x, wall.y - cam_y
            pygame.draw.rect(mask, (0, 0, 0, int(self.darkness_alpha * 0.95)), (wx, wy, wall.width, wall.height))
        return mask

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            shoot_fireball = False
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        running = False
                    elif e.key == pygame.K_f:
                        shoot_fireball = True

            # Add enemies in cooldown as solids for player collision
            enemy_solids = [e.draw_enemy() for e in self.world.enemies if e.cooldown > 0]
            self.player.move_and_collide(dt, self.world.solids + enemy_solids)

            # --- Fireball shooting ---
            if shoot_fireball:
                dx, dy = self.player.last_dir
                if dx != 0 or dy != 0:
                    facing_left = dx < 0
                    self.fireballs.append(Fireball(self.player.x, self.player.y, dx, dy, facing_left=facing_left))
                    self.cast_sound.play()  # <-- Play the sound here

            # --- Update fireballs and handle fireball-enemy collisions ---
            fireballs_to_remove = set()
            enemies_to_remove = set()

            def is_wall(rect):
                # A wall is a solid that does NOT overlap any active target
                for target in self.world.targets:
                    if target.respawn_timer <= 0 and rect.colliderect(target.rect()):
                        return False
                return True

            for f_idx, fireball in enumerate(self.fireballs):
                if fireball.exploding:
                    # Explosion animation: advance frame every 0.05s
                    fireball.explosion_timer += dt
                    if fireball.explosion_timer >= 0.05:
                        fireball.explosion_timer = 0.0
                        fireball.explosion_frame += 1
                        if fireball.explosion_frame >= len(self.explosion_imgs):
                            fireballs_to_remove.add(f_idx)
                    continue  # Don't move or check collisions if exploding
                fireball.update(dt)
                # Remove fireball if it hits a wall or goes off screen
                if not (0 <= fireball.x < self.world.w * TILE_SIZE and 0 <= fireball.y < self.world.h * TILE_SIZE):
                    if not fireball.exploding:
                        fireball.exploding = True
                        self.explosion_sound.play()
                    continue

                if any(is_wall(wall) and fireball.rect().colliderect(wall) for wall in self.world.solids):
                    if not fireball.exploding:
                        fireball.exploding = True
                        self.explosion_sound.play()
                    continue

                for e_idx, enemy in enumerate(self.world.enemies):
                    if fireball.rect().colliderect(enemy.draw_enemy()):
                        if not fireball.exploding:
                            fireball.exploding = True
                            self.explosion_sound.play()
                        enemies_to_remove.add(e_idx)
                        break
                else:
                    for t_idx, target in enumerate(self.world.targets):
                        if target.respawn_timer <= 0 and fireball.rect().colliderect(target.rect()):
                            if not fireball.exploding:
                                fireball.exploding = True
                                self.explosion_sound.play()
                            target.respawn_timer = 5.0
                            self.world.remove_target_solid(target)
                            break

            # Remove hit fireballs and enemies
            self.fireballs = [f for i, f in enumerate(self.fireballs) if i not in fireballs_to_remove]
            self.world.enemies = [e for i, e in enumerate(self.world.enemies) if i not in enemies_to_remove]

            # --- Fireball-target collision ---
            for f_idx, fireball in enumerate(self.fireballs):
                for t_idx, target in enumerate(self.world.targets):
                    if target.respawn_timer <= 0 and fireball.rect().colliderect(target.rect()):
                        fireballs_to_remove.add(f_idx)           # Remove the fireball
                        target.respawn_timer = 5.0               # Target disappears for 5 seconds
                        self.world.remove_target_solid(target)
                        break  # Only the first target hit by this fireball disappears

            for enemy in self.world.enemies:
                enemy.update(dt, self.player, self.world.solids)

            # --- Enemy-enemy collision and merging ---
            merged_indices = set()
            enemies = self.world.enemies
            n = len(enemies)
            i = 0
            while i < n:
                if i in merged_indices:
                    i += 1
                    continue
                e1 = enemies[i]
                group = [i]
                for j in range(i+1, n):
                    if j in merged_indices:
                        continue
                    e2 = enemies[j]
                    if e1.draw_enemy().colliderect(e2.draw_enemy()):
                        group.append(j)
                # If 3 or more enemies collide, merge them
                if len(group) >= 3:
                    # Compute average position
                    avg_x = sum(enemies[k].x for k in group) / len(group)
                    avg_y = sum(enemies[k].y for k in group) / len(group)
                    # Use the largest w/h among the group, then scale up
                    max_w = max(enemies[k].w for k in group)
                    max_h = max(enemies[k].h for k in group)
                    new_w = int(max_w * 1.5)
                    new_h = int(max_h * 1.5)
                    # Remove merged enemies
                    for k in sorted(group, reverse=True):
                        merged_indices.add(k)
                    # Add new merged enemy (with cooldown)
                    img = pygame.transform.scale(self.monster_img_original, (new_w, new_h))
                    self.world.enemies.append(Enemy(avg_x, avg_y, new_w, new_h, cooldown=3.0, img=img))
                i += 1
            # Remove merged enemies
            self.world.enemies = [e for idx, e in enumerate(self.world.enemies) if idx not in merged_indices]

            # --- Player-enemy collision ---
            player_rect = self.player.rect()
            for enemy in self.world.enemies:
                enemy_rect = enemy.draw_enemy()
                if player_rect.colliderect(enemy_rect) and enemy.cooldown <= 0:
                    dx = enemy.x - self.player.x
                    dy = enemy.y - self.player.y
                    dist = math.hypot(dx, dy)
                    if dist == 0:
                        dx, dy = 0, 1
                        dist = 1
                    dx /= dist
                    dy /= dist
                    enemy.x += dx * TILE_SIZE
                    enemy.y += dy * TILE_SIZE
                    enemy.cooldown = 3.0

            # --- Enemy-enemy collision resolution ---
            for i, enemy in enumerate(self.world.enemies):
                rect1 = enemy.draw_enemy()
                for j, other in enumerate(self.world.enemies):
                    if i == j:
                        continue
                    rect2 = other.draw_enemy()
                    if rect1.colliderect(rect2):
                        # Calculate overlap
                        dx = (rect1.centerx - rect2.centerx)
                        dy = (rect1.centery - rect2.centery)
                        if abs(dx) > abs(dy):
                            # Push along x
                            if dx > 0:
                                enemy.x += 1
                                other.x -= 1
                            else:
                                enemy.x -= 1
                                other.x += 1
                        else:
                            # Push along y
                            if dy > 0:
                                enemy.y += 1
                                other.y -= 1
                            else:
                                enemy.y -= 1
                                other.y += 1
                        # Update rect after push
                        rect1 = enemy.draw_enemy()
                        rect2 = other.draw_enemy()

            # --- Update target respawn timers ---
            for target in self.world.targets:
                if target.respawn_timer > 0:
                    target.respawn_timer -= dt
                    if target.respawn_timer <= 0:
                        self.world.add_target_solid(target)
                elif target.respawn_timer == 0:
                    # Already active, do nothing
                    pass

            self.camera.update(self.player.x, self.player.y, dt)

            # --- DRAWING ---
            self.screen.fill(COL_BG)
            view = self.camera.view_rect()
            self.world.draw(self.screen, self.camera.x, self.camera.y, view)
            for enemy in self.world.enemies:
                enemy.draw(self.screen, self.camera.x, self.camera.y)

            # --- Draw targets ---
            for target in self.world.targets:
                target.draw(self.screen, self.camera.x, self.camera.y)

            # --- Draw fireballs ---
            for fireball in self.fireballs:
                fireball.draw(self.screen, self.camera.x, self.camera.y, self.fireball_img, self.explosion_imgs)

            # --- LIGHTING OVERLAY ---
            darkness = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            darkness.fill((0, 0, 0, self.darkness_alpha))  # semi-transparent black

            # Torch position
            torch_offset_x = 18
            torch_offset_y = 10
            px, py = world_to_screen(self.player.x - 20, self.player.y - 30, self.camera.x, self.camera.y)
            torch_px = px + torch_offset_x
            torch_py = py + torch_offset_y
            torch_center = (torch_px + 10, torch_py + 32)

            # Create and apply the light mask (reacts to walls)
            light_mask = self.draw_light_mask(torch_center, self.torch_glow_radius)

            # Draw fireball glows on the light mask
            for fireball in self.fireballs:
                fx, fy = world_to_screen(fireball.x, fireball.y, self.camera.x, self.camera.y)
                self.draw_fireball_glow(light_mask, (fx, fy), 80)  # Adjust radius for desired glow size

            darkness.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

            # Blend the darkness layer over the screen
            self.screen.blit(darkness, (0, 0))

            # --- Draw player and torch ABOVE the glow ---
            draw_hero_img = pygame.transform.flip(self.hero_img, True, False) if self.player.facing_left else self.hero_img
            self.screen.blit(draw_hero_img, (px, py))
            torch_img = pygame.transform.flip(self.torch_img,True, False) if self.player.facing_left else self.torch_img
            self.screen.blit(torch_img, (torch_px, torch_py))

            # Uncomment to show HUD
            hud = f"Top‑down • Move: WASD/Arrows • Sprint: Shift • FPS: {self.clock.get_fps():.0f}"
            txt = self.font.render(hud, True, (230, 230, 230))
            self.screen.blit(txt, (12, 10))

            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    Game().run()
