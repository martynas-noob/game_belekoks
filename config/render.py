import pygame
from config.config import COL_BG, world_to_screen, WIN_W, WIN_H
from config.combat import draw_damage_numbers, draw_health_bars, update_health_bars
import math

def draw_game_frame(game, dt):
    # Fill background and draw world
    game.screen.fill(COL_BG)
    view = game.camera.view_rect()
    game.world.draw(game.screen, game.camera.x, game.camera.y, view)

    # --- Draw player HP bar (big, top left) ---
    big_hp_bar_width = 400
    big_hp_bar_height = 32
    hp_ratio = max(0, game.player.hp / game.player.max_hp)
    bar_x = 40
    bar_y = 20
    font = pygame.font.SysFont("arial", 28, bold=True)
    pygame.draw.rect(game.screen, (40, 40, 40), (bar_x, bar_y, big_hp_bar_width, big_hp_bar_height), border_radius=10)
    pygame.draw.rect(game.screen, (255, 80, 80), (bar_x, bar_y, int(big_hp_bar_width * hp_ratio), big_hp_bar_height), border_radius=10)
    pygame.draw.rect(game.screen, (0, 0, 0), (bar_x, bar_y, big_hp_bar_width, big_hp_bar_height), 4, border_radius=10)
    hp_text = f"HP: {game.player.hp} / {game.player.max_hp}"
    text_surf = font.render(hp_text, True, (255, 255, 255))
    game.screen.blit(text_surf, (bar_x + 12, bar_y + big_hp_bar_height // 2 - text_surf.get_height() // 2))

    # --- Draw stamina bar ---
    stamina_bar_width = big_hp_bar_width
    stamina_bar_height = 24
    stamina_ratio = max(0, game.player.stamina / (game.player.vitality * 20))
    stamina_y = bar_y + big_hp_bar_height + 12
    pygame.draw.rect(game.screen, (40, 40, 40), (bar_x, stamina_y, stamina_bar_width, stamina_bar_height), border_radius=10)
    pygame.draw.rect(game.screen, (80, 200, 80), (bar_x, stamina_y, int(stamina_bar_width * stamina_ratio), stamina_bar_height), border_radius=10)
    pygame.draw.rect(game.screen, (0, 0, 0), (bar_x, stamina_y, stamina_bar_width, stamina_bar_height), 3, border_radius=10)
    stamina_text = f"Stamina: {game.player.stamina} / {game.player.vitality * 20}"
    stamina_surf = font.render(stamina_text, True, (255, 255, 255))
    game.screen.blit(stamina_surf, (bar_x + 12, stamina_y + stamina_bar_height // 2 - stamina_surf.get_height() // 2))

    # --- Draw mana bar ---
    mana_bar_width = big_hp_bar_width
    mana_bar_height = 24
    mana_ratio = max(0, game.player.mana / game.player.max_mana)
    mana_y = stamina_y + stamina_bar_height + 12
    pygame.draw.rect(game.screen, (40, 40, 40), (bar_x, mana_y, mana_bar_width, mana_bar_height), border_radius=10)
    pygame.draw.rect(game.screen, (80, 80, 200), (bar_x, mana_y, int(mana_bar_width * mana_ratio), mana_bar_height), border_radius=10)
    pygame.draw.rect(game.screen, (0, 0, 0), (bar_x, mana_y, mana_bar_width, mana_bar_height), 3, border_radius=10)
    mana_text = f"Mana: {game.player.mana} / {game.player.max_mana}"
    mana_surf = font.render(mana_text, True, (255, 255, 255))
    game.screen.blit(mana_surf, (bar_x + 12, mana_y + mana_bar_height // 2 - mana_surf.get_height() // 2))

    # --- Draw XP bar (below mana bar) ---
    xp_bar_width = big_hp_bar_width
    xp_bar_height = 18
    xp_y = mana_y + mana_bar_height + 12
    xp_ratio = min(1.0, max(0, game.player.xp / game.player.max_xp))
    pygame.draw.rect(game.screen, (40, 40, 40), (bar_x, xp_y, xp_bar_width, xp_bar_height), border_radius=10)
    pygame.draw.rect(game.screen, (255, 215, 0), (bar_x, xp_y, int(xp_bar_width * xp_ratio), xp_bar_height), border_radius=10)
    pygame.draw.rect(game.screen, (0, 0, 0), (bar_x, xp_y, xp_bar_width, xp_bar_height), 2, border_radius=10)
    xp_text = f"XP: {game.player.xp} / {game.player.max_xp}   Level: {game.player.level}"
    xp_surf = font.render(xp_text, True, (255, 255, 255))
    game.screen.blit(xp_surf, (bar_x + 12, xp_y + xp_bar_height // 2 - xp_surf.get_height() // 2))

    # --- Player debug info ---
    debug_font = pygame.font.SysFont("arial", 16)
    debug_info = [
        f"Pos: ({game.player.x:.1f}, {game.player.y:.1f})",
        f"Vel: ({game.player_body.velocity[0]:.1f}, {game.player_body.velocity[1]:.1f})",
        f"HP: {game.player.hp}",
        f"Stamina: {game.player.stamina}",
        f"Mana: {game.player.mana}",
        f"Level: {game.level_index + 1}",
        f"Enemies: {len(game.world.enemies)}",
        f"Targets: {len(game.world.targets)}",
    ]
    for i, line in enumerate(debug_info):
        text_surf = debug_font.render(line, True, (255, 255, 255))
        game.screen.blit(text_surf, (10, 10 + i * 20))

    # --- Draw entities ---
    for i, enemy in enumerate(game.world.enemies):
        if i < len(game.enemy_bodies):
            ex, ey = world_to_screen(game.enemy_bodies[i].position[0], game.enemy_bodies[i].position[1], game.camera.x, game.camera.y)
        else:
            ex, ey = world_to_screen(enemy.x, enemy.y, game.camera.x, game.camera.y)
        enemy.draw(game.screen, game.camera.x, game.camera.y)
        # Draw monster level below hitbox
        level_font = pygame.font.SysFont("arial", 18, bold=True)
        level_text = f"Lv {getattr(enemy, 'level', 1)}"
        text_surf = level_font.render(level_text, True, (255, 215, 0))
        text_x = int(ex - text_surf.get_width() // 2)
        text_y = int(ey + getattr(enemy, "h", 36) // 2 + 8)
        game.screen.blit(text_surf, (text_x, text_y))
    for target in game.world.targets:
        target.draw(game.screen, game.camera.x, game.camera.y)
    player_px, player_py = world_to_screen(game.player_body.position[0] - 40, game.player_body.position[1] - 60, game.camera.x, game.camera.y)
    anim_dir = game.player.anim_dir
    frame = game.player.anim_index
    player_img = game.player_anim_frames[anim_dir][frame]
    game.player.draw_with_sword(game.screen, player_px, player_py, player_img, game.sword_img, game.sword_slash_imgs)
    if game.torch_on_ground or game.torch_following:
        torch_px, torch_py = world_to_screen(
            game.torch_ground_pos[0] - 15 + game.torch_wiggle_offset[0],
            game.torch_ground_pos[1] - 30 + game.torch_wiggle_offset[1],
            game.camera.x, game.camera.y
        )
        game.screen.blit(game.torch_img, (torch_px, torch_py))
    for fireball in game.fireballs:
        fx, fy = world_to_screen(fireball.x, fireball.y, game.camera.x, game.camera.y)
        fireball.draw(game.screen, game.camera.x, game.camera.y, game.fireball_img, game.explosion_imgs)

    # --- Draw colored hitboxes ---
    player_px, player_py = world_to_screen(game.player_body.position[0], game.player_body.position[1], game.camera.x, game.camera.y)
    pygame.draw.circle(game.screen, (0, 0, 255), (int(player_px), int(player_py)), int(game.player_shape.radius))
    pygame.draw.circle(game.screen, (255, 255, 255), (int(player_px), int(player_py)), int(game.player_shape.radius) - 4, 2)
    for i, enemy_body in enumerate(game.enemy_bodies):
        if i < len(game.enemy_shapes):
            ex, ey = world_to_screen(enemy_body.position[0], enemy_body.position[1], game.camera.x, game.camera.y)
            radius = int(game.enemy_shapes[i].radius)
        else:
            ex, ey = 0, 0
            radius = 20
        pygame.draw.circle(game.screen, (0, 255, 0), (int(ex), int(ey)), radius, 2)
        pygame.draw.circle(game.screen, (255, 255, 255), (int(ex), int(ey)), radius - 4, 2)
        attack_range = 80
        for angle in range(0, 360, 18):
            rad = math.radians(angle)
            dot_x = int(ex + math.cos(rad) * attack_range)
            dot_y = int(ey + math.sin(rad) * attack_range)
            pygame.draw.circle(game.screen, (200, 200, 200), (dot_x, dot_y), 3)
        if i < len(game.world.enemies):
            visibility_range = getattr(game.world.enemies[i], "visibility_range", 240)
            pygame.draw.circle(game.screen, (255, 255, 0), (int(ex), int(ey)), int(visibility_range), 1)
    if game.torch_on_ground or game.torch_following:
        torch_px, torch_py = world_to_screen(
            game.torch_ground_pos[0] + game.torch_wiggle_offset[0],
            game.torch_ground_pos[1] + game.torch_wiggle_offset[1],
            game.camera.x, game.camera.y
        )
        torch_rect = pygame.Rect(int(torch_px - 8), int(torch_py - 16), 16, 32)
        pygame.draw.rect(game.screen, (128, 0, 128), torch_rect, 2)
    for wall_shape in game.wall_shapes:
        wall_bb = wall_shape.bb
        wall_rect = pygame.Rect(
            int(wall_bb.left - game.camera.x),
            int(wall_bb.top - game.camera.y),
            int(wall_bb.right - wall_bb.left),
            int(wall_bb.bottom - wall_bb.top)
        )
        pygame.draw.rect(game.screen, (100, 100, 100), wall_rect, 2)
        pygame.draw.rect(game.screen, (0, 0, 0), wall_rect, 4)
    for target in game.world.targets:
        tx, ty = world_to_screen(target.x, target.y, game.camera.x, game.camera.y)
        target_rect = pygame.Rect(
            int(tx - target.w // 2),
            int(ty - target.h // 2),
            target.w, target.h
        )
        pygame.draw.rect(game.screen, (255, 255, 0), target_rect, 2)
    for fireball in game.fireballs:
        fx, fy = world_to_screen(fireball.x, fireball.y, game.camera.x, game.camera.y)
        fireball_rect = pygame.Rect(int(fx - 20), int(fy - 10), 40, 20)
        pygame.draw.rect(game.screen, (255, 128, 0), fireball_rect, 2)
    if game.player.sword_swinging:
        mx, my = pygame.mouse.get_pos()
        world_mx = mx + game.camera.x
        world_my = my + game.camera.y
        px, py = game.player.x, game.player.y
        dx = world_mx - px
        dy = world_my - py
        mag = math.hypot(dx, dy)
        if mag > 0:
            dx /= mag
            dy /= mag
        else:
            dx, dy = game.player.last_dir
        sword_w, sword_h = 48, 48
        offset = 32
        hitbox_x = px + dx * offset - sword_w // 2
        hitbox_y = py + dy * offset - sword_h // 2
        sword_px, sword_py = world_to_screen(hitbox_x, hitbox_y, game.camera.x, game.camera.y)
        sword_hitbox = pygame.Rect(int(sword_px), int(sword_py), sword_w, sword_h)
        pygame.draw.rect(game.screen, (255, 0, 0), sword_hitbox, 2)

    # --- Overlays/effects ---
    draw_damage_numbers(game, game.screen, game.camera, dt)
    draw_health_bars(game, game.screen, game.camera)
    update_health_bars(game, dt)

    # --- LIGHTING OVERLAY ---
    darkness = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, game.darkness_alpha))
    if game.torch_on_ground or game.torch_following:
        torch_px, torch_py = world_to_screen(
            game.torch_ground_pos[0] - 15 + game.torch_wiggle_offset[0],
            game.torch_ground_pos[1] - 30 + game.torch_wiggle_offset[1],
            game.camera.x, game.camera.y
        )
        torch_center = (torch_px + 15, torch_py + 30)
    else:
        torch_center = None
    if torch_center:
        mask = game.get_light_mask(game.torch_glow_radius)
        x = torch_center[0] - game.torch_glow_radius
        y = torch_center[1] - game.torch_glow_radius
        darkness.blit(mask, (x, y), special_flags=pygame.BLEND_RGBA_SUB)
    fireball_glow_radius = 80
    explosion_glow_radius = 180
    for fireball in game.fireballs:
        fx, fy = world_to_screen(fireball.x, fireball.y, game.camera.x, game.camera.y)
        fireball_center = (int(fx), int(fy))
        if fireball.exploding:
            mask = game.get_light_mask(explosion_glow_radius)
            x = fireball_center[0] - explosion_glow_radius
            y = fireball_center[1] - explosion_glow_radius
            darkness.blit(mask, (x, y), special_flags=pygame.BLEND_RGBA_SUB)
        else:
            mask = game.get_light_mask(fireball_glow_radius)
            x = fireball_center[0] - fireball_glow_radius
            y = fireball_center[1] - fireball_glow_radius
            darkness.blit(mask, (x, y), special_flags=pygame.BLEND_RGBA_SUB)
    game.screen.blit(darkness, (0, 0))
    pygame.display.flip()
