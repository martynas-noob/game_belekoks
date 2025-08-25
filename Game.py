from __future__ import annotations
import math
import sys
import warnings
import pygame
import os
import random
import pymunk
print("Pymunk version:", pymunk.version)  # Add this for debugging

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
from collision import Hitbox, check_entity_collision, resolve_enemy_collision

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

        # Game state
        self.player = Player(200, 200)
        self.player.game_ref = self  # Set reference for damage overlay
        self.camera = Camera()
        # Provide a list of enemy/target images to World
        self.enemy_imgs = [self.monster_img_original, self.monster_img_alt, self.monster_img_boss]
        self.target_imgs = [self.target_img, self.target_img_alt]
        self.world = World(LEVEL_1, self.enemy_imgs, self.target_imgs)
        self.fireballs = []
        self.torch_on_ground = True
        # Place torch 60 pixels to the right of the player
        self.torch_ground_pos = (self.player.x + 60, self.player.y)
        self.torch_following = False  # Add this line
        self.torch_glow_radius = 220
        self.darkness_alpha = 200
        self.torch_pickup_cooldown = 0.0
        self.last_t_press_time = 0
        self.t_press_count = 0
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

    def run(self):
        print("Game loop started")  # Debug: confirm loop starts
        running = True
        game_over = False
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            shoot_fireball = False
            sword_swing = False

            # --- Game Over Check ---
            if self.player.hp <= 0:
                game_over = True

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
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
                    elif e.type == pygame.MOUSEBUTTONDOWN:
                        if e.button == 1:  # Left mouse button
                            sword_swing = True

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
            if hasattr(self.player, "update_animation"):
                self.player.update_animation(dt)
            # Update sword swing animation and logic
            if sword_swing and not self.player.sword_swinging:
                self.player.start_sword_swing()
                self.sword_swing_damage = random.randint(10, 15)
                self.sword_swing_hit_targets = set()
                self.sword_sound.play()
            if hasattr(self.player, "update_sword"):
                self.player.update_sword(dt, len(self.sword_slash_imgs))

            # Fireball shooting logic
            if shoot_fireball:
                dx, dy = self.player.last_dir if hasattr(self.player, "last_dir") else (1, 0)
                if dx != 0 or dy != 0:
                    facing_left = dx < 0
                    fireball = Fireball(self.player.x, self.player.y, dx, dy, facing_left=facing_left)
                    self.fireballs.append(fireball)
                    self.cast_sound.play()

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
                            enemies_to_remove.add(i)
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
                    enemy_rect = enemy.draw_enemy() if hasattr(enemy, "draw_enemy") else pygame.Rect(enemy.x-20, enemy.y-30, 40, 60)
                    if fireball.rect().colliderect(enemy_rect):
                        if not fireball.exploding:
                            fireball.exploding = True
                            self.explosion_sound.play()
                        damage = random.randint(10, 15)
                        if hasattr(enemy, "hit_points"):
                            enemy.hit_points -= damage
                            show_damage_numbers(self, enemy.x, enemy.y - 40, damage)
                            show_health_bar(self, enemy)
                            self.slime_damage_sound.play()
                            if enemy.hit_points <= 0:
                                self.slime_death_sound.play()
                                enemies_to_remove.add(i)
                        break
                else:
                    for t_idx, target in enumerate(self.world.targets):
                        if hasattr(target, "respawn_timer") and target.respawn_timer <= 0 and fireball.rect().colliderect(target.rect()):
                            if not fireball.exploding:
                                fireball.exploding = True
                                self.explosion_sound.play()
                            damage = random.randint(10, 15)
                            target.hit_points -= damage
                            show_damage_numbers(self, target.x, target.y - 40, damage)
                            show_health_bar(self, target)
                            if target.hit_points <= 0:
                                target.respawn_timer = 5.0
                                self.world.remove_target_solid(target)
                                target.hit_points = 300
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

            # --- Draw player HP bar (big, top left) ---
            big_hp_bar_width = 400
            big_hp_bar_height = 32
            hp_ratio = max(0, self.player.hp / self.player.max_hp)
            bar_x = 40
            bar_y = 20  # Move closer to top edge
            pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, big_hp_bar_width, big_hp_bar_height), border_radius=10)
            pygame.draw.rect(self.screen, (255, 80, 80), (bar_x, bar_y, int(big_hp_bar_width * hp_ratio), big_hp_bar_height), border_radius=10)
            pygame.draw.rect(self.screen, (0, 0, 0), (bar_x, bar_y, big_hp_bar_width, big_hp_bar_height), 4, border_radius=10)
            # Draw HP text
            font = pygame.font.SysFont("arial", 28, bold=True)
            hp_text = f"HP: {self.player.hp} / {self.player.max_hp}"
            text_surf = font.render(hp_text, True, (255, 255, 255))
            self.screen.blit(text_surf, (bar_x + 12, bar_y + big_hp_bar_height // 2 - text_surf.get_height() // 2))

            # Draw enemy sprites with animation FIRST (before hitboxes)
            for i, enemy in enumerate(self.world.enemies):
                ex, ey = world_to_screen(self.enemy_bodies[i].position[0], self.enemy_bodies[i].position[1], self.camera.x, self.camera.y)
                enemy.draw(self.screen, self.camera.x, self.camera.y)

            # Draw target sprites
            for target in self.world.targets:
                target.draw(self.screen, self.camera.x, self.camera.y)

            # Draw player sprite with animation and sword
            player_px, player_py = world_to_screen(self.player_body.position[0] - 40, self.player_body.position[1] - 60, self.camera.x, self.camera.y)
            anim_dir = self.player.anim_dir
            frame = self.player.anim_index
            player_img = self.player_anim_frames[anim_dir][frame]
            self.player.draw_with_sword(self.screen, player_px, player_py, player_img, self.sword_img, self.sword_slash_imgs)

            # Draw torch sprite
            if self.torch_on_ground or self.torch_following:
                torch_px, torch_py = world_to_screen(self.torch_ground_pos[0] - 15, self.torch_ground_pos[1] - 30, self.camera.x, self.camera.y)
                self.screen.blit(self.torch_img, (torch_px, torch_py))

            # Draw fireball sprites
            for fireball in self.fireballs:
                fx, fy = world_to_screen(fireball.x, fireball.y, self.camera.x, self.camera.y)
                fireball.draw(self.screen, self.camera.x, self.camera.y, self.fireball_img, self.explosion_imgs)

            # --- Draw colored hitboxes for all entities ---

            # Player hitbox (circle, blue)
            player_px, player_py = world_to_screen(self.player_body.position[0], self.player_body.position[1], self.camera.x, self.camera.y)
            pygame.draw.circle(self.screen, (0, 0, 255), (int(player_px), int(player_py)), int(self.player_shape.radius), 2)
            # Player HP overlay (white, matches damage overlay)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(player_px), int(player_py)), int(self.player_shape.radius) - 4, 2)

            # Enemy hitboxes (circle, green) and damage overlay (white)
            for i, enemy_body in enumerate(self.enemy_bodies):
                ex, ey = world_to_screen(enemy_body.position[0], enemy_body.position[1], self.camera.x, self.camera.y)
                radius = int(self.enemy_shapes[i].radius)
                pygame.draw.circle(self.screen, (0, 255, 0), (int(ex), int(ey)), radius, 2)
                # White overlay for damage hitbox (slightly smaller)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(ex), int(ey)), radius - 4, 2)
                # Dotted inlay for enemy attack range (e.g., 80px)
                attack_range = 80
                for angle in range(0, 360, 18):
                    rad = math.radians(angle)
                    dot_x = int(ex + math.cos(rad) * attack_range)
                    dot_y = int(ey + math.sin(rad) * attack_range)
                    pygame.draw.circle(self.screen, (200, 200, 200), (dot_x, dot_y), 3)

            # Torch hitbox (rect, purple)
            if self.torch_on_ground or self.torch_following:
                torch_px, torch_py = world_to_screen(self.torch_ground_pos[0], self.torch_ground_pos[1], self.camera.x, self.camera.y)
                torch_rect = pygame.Rect(int(torch_px - 8), int(torch_py - 16), 16, 32)
                pygame.draw.rect(self.screen, (128, 0, 128), torch_rect, 2)

            # Wall hitboxes (rect, gray with black outline)
            for wall_shape in self.wall_shapes:
                wall_bb = wall_shape.bb
                wall_rect = pygame.Rect(
                    int(wall_bb.left - self.camera.x),
                    int(wall_bb.top - self.camera.y),
                    int(wall_bb.right - wall_bb.left),
                    int(wall_bb.bottom - wall_bb.top)
                )
                pygame.draw.rect(self.screen, (100, 100, 100), wall_rect, 2)  # gray inner
                pygame.draw.rect(self.screen, (0, 0, 0), wall_rect, 4)        # black outline

            # Target hitboxes (rect, yellow)
            for target in self.world.targets:
                tx, ty = world_to_screen(target.x, target.y, self.camera.x, self.camera.y)
                # Center hitbox on target sprite
                target_rect = pygame.Rect(
                    int(tx - target.w // 2),
                    int(ty - target.h // 2),
                    target.w, target.h
                )
                pygame.draw.rect(self.screen, (255, 255, 0), target_rect, 2)

            # Fireball hitboxes (rect, orange)
            for fireball in self.fireballs:
                fx, fy = world_to_screen(fireball.x, fireball.y, self.camera.x, self.camera.y)
                fireball_rect = pygame.Rect(int(fx - 20), int(fy - 10), 40, 20)
                pygame.draw.rect(self.screen, (255, 128, 0), fireball_rect, 2)

            # Melee attack hitbox (sword) - red
            if self.player.sword_swinging:
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

                sword_px, sword_py = world_to_screen(hitbox_x, hitbox_y, self.camera.x, self.camera.y)
                sword_hitbox = pygame.Rect(int(sword_px), int(sword_py), sword_w, sword_h)
                pygame.draw.rect(self.screen, (255, 0, 0), sword_hitbox, 2)

            # --- Now draw overlays/effects above hitboxes ---
            draw_damage_numbers(self, self.screen, self.camera, dt)
            draw_health_bars(self, self.screen, self.camera)
            update_health_bars(self, dt)

            # --- LIGHTING OVERLAY ---
            darkness = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            darkness.fill((0, 0, 0, self.darkness_alpha))

            # Torch glow
            # FIX: Ensure torch_center is defined before use
            if self.torch_on_ground or self.torch_following:
                torch_px, torch_py = world_to_screen(self.torch_ground_pos[0] - 15, self.torch_ground_pos[1] - 30, self.camera.x, self.camera.y)
                torch_center = (torch_px + 15, torch_py + 30)
            else:
                torch_center = None

            if torch_center:
                light_mask = draw_light_mask(torch_center, self.torch_glow_radius)
                darkness.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

            # Fireball and explosion glow
            fireball_glow_radius = 80  # Normal fireball glow
            explosion_glow_radius = 180  # Bigger explosion glow
            for fireball in self.fireballs:
                fx, fy = world_to_screen(fireball.x, fireball.y, self.camera.x, self.camera.y)
                fireball_center = (int(fx), int(fy))
                if fireball.exploding:
                    explosion_light = draw_light_mask(fireball_center, explosion_glow_radius)
                    darkness.blit(explosion_light, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
                else:
                    fireball_light = draw_light_mask(fireball_center, fireball_glow_radius)
                    darkness.blit(fireball_light, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

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
            if self.torch_on_ground or self.torch_following:
                torch_px, torch_py = world_to_screen(self.torch_ground_pos[0] - 15, self.torch_ground_pos[1] - 30, self.camera.x, self.camera.y)
                torch_center = (torch_px + 15, torch_py + 30)
            else:
                torch_center = None

            if torch_center is None:
                monster_target = self.torch_ground_pos
            elif self.player_near_torch():
                monster_target = (self.player.x, self.player.y)
            else:
                monster_target = self.torch_ground_pos

            for i, enemy in enumerate(self.world.enemies):
                prev_x, prev_y = enemy.x, enemy.y
                other_enemy_rects = [e.draw_enemy() for j, e in enumerate(self.world.enemies) if j != i]
                player_rect = self.player.rect()
                enemy.update(dt, monster_target, self.world.solids, player_rect, other_enemy_rects, player=self.player)
                self.enemy_bodies[i].position = (enemy.x, enemy.y)
                if enemy.x != prev_x or enemy.y != prev_y:
                    slime_moving = True

            # --- Draw player HP bar ---
            hp_bar_width = 200
            hp_bar_height = 18
            hp_ratio = max(0, self.player.hp / self.player.max_hp)
            pygame.draw.rect(self.screen, (40, 40, 40), (30, 30, hp_bar_width, hp_bar_height), border_radius=6)
            pygame.draw.rect(self.screen, (255, 80, 80), (30, 30, int(hp_bar_width * hp_ratio), hp_bar_height), border_radius=6)
            pygame.draw.rect(self.screen, (0, 0, 0), (30, 30, hp_bar_width, hp_bar_height), 2, border_radius=6)

            # --- Draw player HP bar (big, top left) ---
            big_hp_bar_width = 400
            big_hp_bar_height = 32
            hp_ratio = max(0, self.player.hp / self.player.max_hp)
            bar_x = 40
            bar_y = 20  # Move closer to top edge
            pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, big_hp_bar_width, big_hp_bar_height), border_radius=10)
            pygame.draw.rect(self.screen, (255, 80, 80), (bar_x, bar_y, int(big_hp_bar_width * hp_ratio), big_hp_bar_height), border_radius=10)
            pygame.draw.rect(self.screen, (0, 0, 0), (bar_x, bar_y, big_hp_bar_width, big_hp_bar_height), 4, border_radius=10)
            # Draw HP text
            font = pygame.font.SysFont("arial", 28, bold=True)
            hp_text = f"HP: {self.player.hp} / {self.player.max_hp}"
            text_surf = font.render(hp_text, True, (255, 255, 255))
            self.screen.blit(text_surf, (bar_x + 12, bar_y + big_hp_bar_height // 2 - text_surf.get_height() // 2))

    def player_near_torch(self, distance=100):
        px, py = self.player.x, self.player.y
        tx, ty = self.torch_ground_pos
        return math.hypot(px - tx, py - ty) < distance

    def show_health_bars(self):
        for target in self.world.targets:
            if target.respawn_timer <= 0:
                show_health_bar(self, target)
        # Remove the enemy damage loop from here, it should NOT be inside show_health_bars
        # ...existing code...

if __name__ == "__main__":
    Game().run()