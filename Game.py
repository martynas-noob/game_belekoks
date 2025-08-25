from __future__ import annotations
import math
import sys
import warnings
import pygame
import os
import random

from config.config import (
    WIN_W, WIN_H, FPS, LEVEL_1, COL_BG, world_to_screen
)
from config.player import Player
from config.enemy import Enemy
from config.fireball import Fireball
from config.target import Target
from config.world import World
from config.camera import Camera
from config.utils import draw_light_mask
from config.combat import show_damage_numbers, draw_damage_numbers, show_health_bar, update_health_bars, draw_health_bars

warnings.filterwarnings("ignore", category=UserWarning)

# ----------------------------------------
#
# -----------------------------
# Game
# -----------------------------

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Belekoks Game")
        self.clock = pygame.time.Clock()

        # Load images and sounds with new paths
        self.monster_img_original = pygame.transform.scale(
            pygame.image.load("textures/NPC/slime/monster.png").convert_alpha(), (40, 60)
        )
        self.target_img = pygame.transform.scale(
            pygame.image.load("textures/NPC/target/target.png").convert_alpha(), (40, 60)
        )
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

        # Game state
        self.player = Player(200, 200)
        self.camera = Camera()
        self.world = World(LEVEL_1, self.monster_img_original, self.target_img)
        self.fireballs = []
        self.torch_on_ground = True
        self.torch_ground_pos = (self.player.x, self.player.y)
        self.torch_following = False  # Add this line
        self.torch_glow_radius = 220
        self.darkness_alpha = 200
        self.torch_pickup_cooldown = 0.0
        self.last_t_press_time = 0
        self.t_press_count = 0
        self.damage_numbers = []
        self.target_health_bars = {}

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
                    elif e.key == pygame.K_t:
                        now = pygame.time.get_ticks()
                        if not self.torch_on_ground:
                            self.torch_on_ground = True
                            self.torch_ground_pos = (self.player.x, self.player.y)
                            self.torch_pickup_cooldown = 0.3
                            self.t_press_count = 0
                            self.torch_following = False  # Stop following when dropped
                        else:
                            # Torch is on ground: check for double-tap within 400ms
                            if now - self.last_t_press_time < 400:
                                self.t_press_count += 1
                            else:
                                self.t_press_count = 1
                            self.last_t_press_time = now
                            if self.t_press_count == 2 and self.torch_pickup_cooldown <= 0:
                                self.torch_on_ground = False
                                self.t_press_count = 0
                                self.torch_pickup_cooldown = 0.3
                                self.torch_following = True  # Start following the player
            keys = pygame.key.get_pressed()
            # Player movement
            enemy_solids = [e.draw_enemy() for e in self.world.enemies]
            self.player.move_and_collide(dt, self.world.solids + enemy_solids)

            # Torch follow logic
            if self.torch_following:
                tx, ty = self.torch_ground_pos
                px, py = self.player.x, self.player.y
                dx, dy = px - tx, py - ty
                dist = math.hypot(dx, dy)
                if dist > 1:
                    dx, dy = dx / dist, dy / dist
                    torch_speed = 280.0  # Same as enemy speed
                    self.torch_ground_pos = (
                        tx + dx * torch_speed * dt,
                        ty + dy * torch_speed * dt
                    )
                else:
                    self.torch_ground_pos = (px, py)

            # Torch pickup cooldown timer
            if self.torch_pickup_cooldown > 0:
                self.torch_pickup_cooldown -= dt

            # Fireball shooting
            if shoot_fireball:
                dx, dy = self.player.last_dir
                if dx != 0 or dy != 0:
                    facing_left = dx < 0
                    fireball = Fireball(self.player.x, self.player.y, dx, dy, facing_left=facing_left)
                    self.fireballs.append(fireball)
                    self.cast_sound.play()

            # --- Calculate torch_center before using it ---
            if self.torch_on_ground or self.torch_following:
                torch_px, torch_py = world_to_screen(self.torch_ground_pos[0] - 15, self.torch_ground_pos[1] - 30, self.camera.x, self.camera.y)
                torch_center = (torch_px + 15, torch_py + 30)
            else:
                torch_center = None

            # Update enemies
            if torch_center is None:
                # No torch/light: monsters go to the torch's last position
                monster_target = self.torch_ground_pos
            elif self.player_near_torch():
                # Player is near the torch: monsters go to the player
                monster_target = (self.player.x, self.player.y)
            else:
                # Player is in darkness: monsters go to the torch
                monster_target = self.torch_ground_pos

            for enemy in self.world.enemies:
                enemy.update(dt, monster_target, self.world.solids)

            # Update fireballs and handle collisions
            fireballs_to_remove = set()
            enemies_to_remove = set()

            def is_wall(rect):
                for target in self.world.targets:
                    if target.respawn_timer <= 0 and rect.colliderect(target.rect()):
                        return False
                return True

            for f_idx, fireball in enumerate(self.fireballs):
                if fireball.exploding:
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
                            # Deal random damage between 10 and 15
                            damage = random.randint(10, 15)
                            target.hit_points -= damage
                            # --- Add damage number effect ---
                            show_damage_numbers(self, target.x, target.y - 40, fireball.damage)
                            show_health_bar(self, target)
                            if target.hit_points <= 0:
                                target.respawn_timer = 5.0
                                self.world.remove_target_solid(target)
                                target.hit_points = 300  # Reset HP for respawn
                            break

            self.fireballs = [f for i, f in enumerate(self.fireballs) if i not in fireballs_to_remove]
            self.world.enemies = [e for i, e in enumerate(self.world.enemies) if i not in enemies_to_remove]

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
            self.screen.fill(COL_BG)
            self.world.draw(self.screen, self.camera.x, self.camera.y, view)
            for enemy in self.world.enemies:
                enemy.draw(self.screen, self.camera.x, self.camera.y)
            for target in self.world.targets:
                target.draw(self.screen, self.camera.x, self.camera.y)
            for fireball in self.fireballs:
                fireball.draw(self.screen, self.camera.x, self.camera.y, self.fireball_img, self.explosion_imgs)
            draw_damage_numbers(self, self.screen, self.camera, dt)
            draw_health_bars(self, self.screen, self.camera)
            update_health_bars(self, dt)

            # Draw player animation
            player_px, player_py = world_to_screen(self.player.x - 40, self.player.y - 60, self.camera.x, self.camera.y)
            anim_dir = self.player.anim_dir
            frame = self.player.anim_index
            player_img = self.player_anim_frames[anim_dir][frame]
            self.screen.blit(player_img, (player_px, player_py))

            # Torch drawing and glow
            if self.torch_on_ground or self.torch_following:
                torch_px, torch_py = world_to_screen(self.torch_ground_pos[0] - 15, self.torch_ground_pos[1] - 30, self.camera.x, self.camera.y)
                torch_center = (torch_px + 15, torch_py + 30)
                self.screen.blit(self.torch_img, (torch_px, torch_py))
            else:
                torch_center = None  # Or handle lighting accordingly

            # --- LIGHTING OVERLAY ---
            darkness = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            darkness.fill((0, 0, 0, self.darkness_alpha))

            if torch_center:
                light_mask = draw_light_mask(torch_center, self.torch_glow_radius)
                darkness.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

            self.screen.blit(darkness, (0, 0))

            pygame.display.flip()

            mx, my = pygame.mouse.get_pos()
            world_mx = mx + self.camera.x
            world_my = my + self.camera.y
            self.player.update_direction_towards(world_mx, world_my)

            # Update health bars each frame
            update_health_bars(self, dt)
            # Draw health bars for targets
            draw_health_bars(self, self.screen, self.camera)

    def player_near_torch(self, distance=100):
        px, py = self.player.x, self.player.y
        tx, ty = self.torch_ground_pos
        return math.hypot(px - tx, py - ty) < distance

    def show_health_bars(self):
        for target in self.world.targets:
            if target.respawn_timer <= 0:
                show_health_bar(self, target)

if __name__ == "__main__":
    Game().run()
