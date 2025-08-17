from __future__ import annotations
import math
import sys
from turtle import Screen
import pygame
import os
from dataclasses import dataclass

# -----------------------------
# Config
# -----------------------------
WIN_W, WIN_H = 1920, 1080
PIXEL_SCALE = 1
FPS = 120

TILE_SIZE = 48
MAP_CHARS = {
    '#': 1,   # wall
    '.': 0,  # floor
    '0': 2,  # enemy spawn
}

LEVEL_1 = [
    "####################################################################################################################",
    "#..#............#..........#.......................................................................................#",
    "#..######.......#..######..#.......................................................................................#",
    "#..#....#..............#...........................................................................................#",
    "#..#....#..######..##..#...######################################################################################..#",
    "#..#....#..#....#..#...#...#.......................................................................................#",
    "#..#....#..#....#..#...#...#.......................................................................................#",
    "#..######..#....#..#...#...#.......................................................................................#",
    "#..........#....#..#.......#.......................................................................................#",
    "#..........######..#########.......................................................................................#",
    "#..................................................................................................................#",
    "###############.........####.......................................................................................#",
    "################.....#############...........#######################################################################",
    "#..................................................................................................................#",
    "#..................................................................................................................#",
    "#..................................................................................................................#",
    "#.......................................................................................................0..........#",
    "#..................................................................................................................#",
    "#..................................................................................................................#",
    "#..................................................................................................................#",
    "################.....#############...........#######################################################################",

]

COL_BG = (22, 26, 33)
COL_FLOOR_A = (36, 42, 50)
COL_FLOOR_B = (32, 38, 46)
COL_WALL = (70, 86, 104)
COL_PLAYER = (240, 240, 240)
COL_ENEMY = (200, 70, 70)
COL_ACCENT = (160, 200, 255)

# -----------------------------
# Helpers
# -----------------------------

def world_to_screen(x: float, y: float, cam_x: float, cam_y: float) -> tuple[int, int]:
    return int(x - cam_x), int(y - cam_y)

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

    def draw_hero(x, y):
        input(hero_img, (x, y))

    # def rect(self) -> pygame.Rect:
    #     return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

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

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        px, py = world_to_screen(self.x - self.w/2, self.y - self.h/2, cam_x, cam_y)
        rect = pygame.Rect(px, py, self.w, self.h)
        pygame.draw.rect(surf, COL_PLAYER, rect, border_radius=6)
        pygame.draw.rect(surf, COL_ACCENT, (rect.centerx-2, rect.top+4, 4, 6), border_radius=2)

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

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.w/2), int(self.y - self.h/2), self.w, self.h)

    def update(self, dt: float, player: Player, solids: list[pygame.Rect]):
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            dx, dy = dx/dist, dy/dist
        step = self.speed * dt
        self.x += dx * step
        r = self.rect()
        for s in solids:
            if r.colliderect(s):
                if dx > 0:
                    r.right = s.left
                elif dx < 0:
                    r.left = s.right
        self.x = r.centerx

        self.y += dy * step
        r = self.rect()
        for s in solids:
            if r.colliderect(s):
                if dy > 0:
                    r.bottom = s.top
                elif dy < 0:
                    r.top = s.bottom
        self.y = r.centery

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        px, py = world_to_screen(self.x - self.w/2, self.y - self.h/2, cam_x, cam_y)
        rect = pygame.Rect(px, py, self.w, self.h)
        pygame.draw.rect(surf, COL_ENEMY, rect, border_radius=6)

# -----------------------------
# World / Map
# -----------------------------

class World:
    def __init__(self, layout: list[str]):
        self.layout = layout
        self.w = len(layout[0])
        self.h = len(layout)
        self.solids: list[pygame.Rect] = []
        self.enemies: list[Enemy] = []
        for y, row in enumerate(layout):
            for x, ch in enumerate(row):
                if MAP_CHARS.get(ch, 0) == 1:
                    self.solids.append(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                elif MAP_CHARS.get(ch, 0) == 2:
                    self.enemies.append(Enemy(x*TILE_SIZE+TILE_SIZE/2, y*TILE_SIZE+TILE_SIZE/2))

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

# -----------------------------
# Game
# -----------------------------

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Top‑down 2D Base with Enemy")
        self.clock = pygame.time.Clock()
        self.world = World(LEVEL_1)
        # self.player = Player(x=WIN_W/2, y=WIN_H/2)
        self.camera = Camera()
        self.font = pygame.font.Font(None, 24)
        self.player = pygame.image.load("hero.png").convert_alpha()
        self.player = pygame.transform.scale(self.player, (40, 60))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    running = False

            self.player.move_and_collide(dt, self.world.solids)
            for enemy in self.world.enemies:
                enemy.update(dt, self.player, self.world.solids)
            self.camera.update(self.player.x, self.player.y, dt)

            self.screen.fill(COL_BG)
            view = self.camera.view_rect()
            self.world.draw(self.screen, self.camera.x, self.camera.y, view)
            for enemy in self.world.enemies:
                enemy.draw(self.screen, self.camera.x, self.camera.y)
            self.player.draw(self.screen, self.camera.x, self.camera.y)

            # hud = f"Top‑down • Move: WASD/Arrows • Sprint: Shift • FPS: {self.clock.get_fps():.0f}"
            # txt = self.font.render(hud, True, (230, 230, 230))
            # self.screen.blit(txt, (12, 10))

            pygame.display.flip()
        pygame.quit()

# -----------------------------
# Entry
# -----------------------------

if __name__ == "__main__":
    Game().run()
