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
    hp_text = f"HP: {int(game.player.hp)} / {game.player.max_hp}"
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
    stamina_text = f"Stamina: {int(game.player.stamina)} / {game.player.vitality * 20}"
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
    mana_text = f"Mana: {int(game.player.mana)} / {game.player.max_mana}"
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
    xp_text = f"XP: {int(game.player.xp)} / {game.player.max_xp}   Level: {game.player.level}"
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

def draw_inventory_overlay(game, tab_index=0):
    overlay = pygame.Surface((game.screen.get_width(), game.screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    game.screen.blit(overlay, (0, 0))
    font = pygame.font.SysFont("arial", 48, bold=True)

    # --- Tabs ---
    tab_names = ["Inventory", "Stats", "Skills"]
    tab_font = pygame.font.SysFont("arial", 32, bold=True)
    tab_w = 220
    tab_h = 48
    tab_y = 40
    tab_x_start = game.screen.get_width() // 2 - tab_w * len(tab_names) // 2
    for i, name in enumerate(tab_names):
        tab_x = tab_x_start + i * tab_w
        color = (255, 215, 0) if i == tab_index else (120, 120, 120)
        pygame.draw.rect(game.screen, color, (tab_x, tab_y, tab_w, tab_h), border_radius=12)
        tab_text = tab_font.render(name, True, (0, 0, 0))
        game.screen.blit(tab_text, (tab_x + tab_w // 2 - tab_text.get_width() // 2, tab_y + tab_h // 2 - tab_text.get_height() // 2))

    # --- Tab content ---
    if tab_index == 0:
        # Inventory tab
        title = font.render("INVENTORY", True, (255, 255, 255))
        game.screen.blit(title, (game.screen.get_width() // 2 - title.get_width() // 2, 120))
        inv_font = pygame.font.SysFont("arial", 28)
        slot_font = pygame.font.SysFont("arial", 22, bold=True)

        # Divide screen
        left_x = game.screen.get_width() // 4
        right_x = 3 * game.screen.get_width() // 4
        center_y = 220

        # --- Equipment HUD (left side) ---
        slot_size = 64
        slot_gap = 24
        equip_slots = {
            "Helmet": (left_x, center_y),
            "Armor": (left_x, center_y + slot_size + slot_gap),
            "Main Hand": (left_x - slot_size - slot_gap, center_y + 2 * (slot_size + slot_gap)),
            "Off Hand": (left_x + slot_size + slot_gap, center_y + 2 * (slot_size + slot_gap)),
            "Boots": (left_x, center_y + 3 * (slot_size + slot_gap)),
        }
        acc_y = center_y + 4 * (slot_size + slot_gap)
        acc_x_start = left_x - 2 * (slot_size + slot_gap) + slot_size // 2
        accessory_slots = []
        for i in range(4):
            accessory_slots.append((acc_x_start + i * (slot_size + slot_gap), acc_y))

        # Draw equipment slots and items
        slot_rects = {}
        hovered_item = None
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Draw equipment slots and items
        slot_rects = {}
        for name, (sx, sy) in equip_slots.items():
            rect = pygame.Rect(sx - slot_size // 2, sy - slot_size // 2, slot_size, slot_size)
            slot_rects[name] = rect
            pygame.draw.rect(game.screen, (80, 80, 80), rect, border_radius=10)
            pygame.draw.rect(game.screen, (160, 160, 160), rect, 3, border_radius=10)
            label = slot_font.render(name, True, (220, 220, 220))
            game.screen.blit(label, (sx - label.get_width() // 2, sy + slot_size // 2 + 4))
            item = game.player.equipment.get(name)
            if item is not None:
                if hasattr(item, "image") and item.image:
                    item_img = pygame.transform.scale(item.image, (slot_size - 12, slot_size - 12))
                    game.screen.blit(item_img, (sx - (slot_size - 12) // 2, sy - (slot_size - 12) // 2))
                elif item.name == "Sword" and hasattr(game, "sword_img") and game.sword_img:
                    sword_img = pygame.transform.scale(game.sword_img, (slot_size - 12, slot_size - 12))
                    game.screen.blit(sword_img, (sx - (slot_size - 12) // 2, sy - (slot_size - 12) // 2))
                else:
                    pygame.draw.circle(game.screen, (200, 200, 80), (sx, sy), slot_size // 3)
                if rect.collidepoint(mouse_x, mouse_y):
                    hovered_item = item

        for i, (sx, sy) in enumerate(accessory_slots):
            name = f"Accessory {i+1}"
            rect = pygame.Rect(sx - slot_size // 2, sy - slot_size // 2, slot_size, slot_size)
            slot_rects[name] = rect
            pygame.draw.rect(game.screen, (80, 80, 80), rect, border_radius=10)
            pygame.draw.rect(game.screen, (160, 160, 160), rect, 3, border_radius=10)
            label = slot_font.render(name, True, (220, 220, 220))
            game.screen.blit(label, (sx - label.get_width() // 2, sy + slot_size // 2 + 4))
            item = game.player.equipment.get(name)
            if item is not None:
                if hasattr(item, "image") and item.image:
                    item_img = pygame.transform.scale(item.image, (slot_size - 12, slot_size - 12))
                    game.screen.blit(item_img, (sx - (slot_size - 12) // 2, sy - (slot_size - 12) // 2))
                else:
                    pygame.draw.circle(game.screen, (200, 200, 80), (sx, sy), slot_size // 3)
                if rect.collidepoint(mouse_x, mouse_y):
                    hovered_item = item

        # Inventory grid (right side)
        inv_cols, inv_rows = 5, 8
        inv_slot_size = 56
        inv_gap = 12
        grid_start_x = right_x - ((inv_cols * inv_slot_size + (inv_cols - 1) * inv_gap) // 2)
        grid_start_y = center_y
        inv_rects = []
        for row in range(inv_rows):
            for col in range(inv_cols):
                idx = row * inv_cols + col
                sx = grid_start_x + col * (inv_slot_size + inv_gap)
                sy = grid_start_y + row * (inv_slot_size + inv_gap)
                rect = pygame.Rect(sx, sy, inv_slot_size, inv_slot_size)
                inv_rects.append(rect)
                pygame.draw.rect(game.screen, (60, 60, 60), rect, border_radius=8)
                pygame.draw.rect(game.screen, (120, 120, 120), rect, 2, border_radius=8)
                item = game.player.inventory[idx]
                if item is not None:
                    if hasattr(item, "image") and item.image:
                        item_img = pygame.transform.scale(item.image, (inv_slot_size - 12, inv_slot_size - 12))
                        game.screen.blit(item_img, (sx + (inv_slot_size - item_img.get_width()) // 2, sy + (inv_slot_size - item_img.get_height()) // 2))
                    elif hasattr(item, "name") and item.name == "Sword" and hasattr(game, "sword_img") and game.sword_img:
                        sword_img = pygame.transform.scale(game.sword_img, (inv_slot_size - 12, inv_slot_size - 12))
                        game.screen.blit(sword_img, (sx + (inv_slot_size - sword_img.get_width()) // 2, sy + (inv_slot_size - sword_img.get_height()) // 2))
                    else:
                        pygame.draw.circle(game.screen, (200, 200, 80), (sx + inv_slot_size // 2, sy + inv_slot_size // 2), inv_slot_size // 3)
                    if rect.collidepoint(mouse_x, mouse_y):
                        hovered_item = item

        # --- Drag and drop logic (simple click to move) ---
        game._equip_slot_rects = slot_rects
        game._inv_slot_rects = inv_rects

        inv_text = inv_font.render("Click equipment/inventory slots to move items.", True, (220, 220, 220))
        game.screen.blit(inv_text, (right_x - inv_text.get_width() // 2, grid_start_y + inv_rows * (inv_slot_size + inv_gap) + 32))

        # --- Item stats hub ---
        if hovered_item is not None:
            hub_w, hub_h = 320, 180
            hub_x = mouse_x + 24
            hub_y = mouse_y + 24
            # Prevent hub from going off screen
            if hub_x + hub_w > game.screen.get_width():
                hub_x = game.screen.get_width() - hub_w - 16
            if hub_y + hub_h > game.screen.get_height():
                hub_y = game.screen.get_height() - hub_h - 16
            hub_rect = pygame.Rect(hub_x, hub_y, hub_w, hub_h)
            pygame.draw.rect(game.screen, (30, 30, 30), hub_rect, border_radius=14)
            pygame.draw.rect(game.screen, (160, 160, 160), hub_rect, 3, border_radius=14)
            stat_font = pygame.font.SysFont("arial", 24, bold=True)
            lines = [
                f"Name: {getattr(hovered_item, 'name', '')}",
                f"Type: {getattr(hovered_item, 'item_type', '')}",
                f"Level: {getattr(hovered_item, 'level', 1)}"
            ]
            # Weapon stats
            if hasattr(hovered_item, "attack_min") and hasattr(hovered_item, "attack_max") and hovered_item.attack_min is not None:
                lines.append(f"Attack: {hovered_item.attack_min} - {hovered_item.attack_max}")
            if hasattr(hovered_item, "attack_speed") and hovered_item.attack_speed is not None:
                lines.append(f"Attack Speed: {hovered_item.attack_speed}")
            # Add more stats here if needed

            for i, line in enumerate(lines):
                stat_surf = stat_font.render(line, True, (220, 220, 220))
                game.screen.blit(stat_surf, (hub_x + 18, hub_y + 18 + i * 32))
    elif tab_index == 1:
        # Stats tab
        title = font.render("PLAYER STATS", True, (255, 255, 255))
        game.screen.blit(title, (game.screen.get_width() // 2 - title.get_width() // 2, 120))
        stats_font = pygame.font.SysFont("arial", 28)
        stats = [
            f"Level: {game.player.level}",
            f"XP: {int(game.player.xp)} / {game.player.max_xp}",
            f"HP: {int(game.player.hp)} / {game.player.max_hp}",
            f"Mana: {int(game.player.mana)} / {game.player.max_mana}",
            f"Stamina: {int(game.player.stamina)} / {game.player.vitality * 20}",
        ]
        for i, line in enumerate(stats):
            stat_surf = stats_font.render(line, True, (220, 220, 220))
            game.screen.blit(stat_surf, (game.screen.get_width() // 2 - stat_surf.get_width() // 2, 220 + i * 40))
        # Regeneration calculations (rounded)
        hp_regen = int(round(10 * game.player.vitality * (game.player.level * 0.2)))
        mana_regen = int(round(10 * game.player.intelligence * (game.player.level * 0.2)))
        regen_font = pygame.font.SysFont("arial", 24, bold=True)
        hp_regen_text = f"HP Regeneration: {hp_regen} / sec"
        mana_regen_text = f"Mana Regeneration: {mana_regen} / sec"
        hp_regen_surf = regen_font.render(hp_regen_text, True, (120, 255, 120))
        mana_regen_surf = regen_font.render(mana_regen_text, True, (120, 180, 255))
        game.screen.blit(hp_regen_surf, (game.screen.get_width() // 2 - hp_regen_surf.get_width() // 2, 220 + 6 * 40))
        game.screen.blit(mana_regen_surf, (game.screen.get_width() // 2 - mana_regen_surf.get_width() // 2, 220 + 7 * 40))

        # --- Damage calculations ---
        # Base damage (player's base melee damage range)
        min_base = 1 + (game.player.strength - 1) * 5
        max_base = 5 + (game.player.strength - 1) * 5
        base_damage_text = f"Base Damage: {min_base} - {max_base}"

        # Final damage (with weapon equipped)
        weapon = game.player.equipment.get("Main Hand")
        if weapon is not None and hasattr(weapon, "get_attack_damage") and weapon.attack_min is not None:
            min_final = weapon.attack_min * min_base
            max_final = weapon.attack_max * max_base
            final_damage_text = f"Final Damage: {min_final} - {max_final}"
        else:
            final_damage_text = f"Final Damage: {min_base} - {max_base}"

        dmg_font = pygame.font.SysFont("arial", 24, bold=True)
        base_surf = dmg_font.render(base_damage_text, True, (255, 180, 80))
        final_surf = dmg_font.render(final_damage_text, True, (80, 180, 255))
        game.screen.blit(base_surf, (game.screen.get_width() // 2 - base_surf.get_width() // 2, 220 + 8 * 40))
        game.screen.blit(final_surf, (game.screen.get_width() // 2 - final_surf.get_width() // 2, 220 + 9 * 40))

        # Stat points (now below damage)
        points_font = pygame.font.SysFont("arial", 24, bold=True)
        points_text = f"Unassigned Stat Points: {game.player.stat_points}"
        points_surf = points_font.render(points_text, True, (255, 215, 0))
        game.screen.blit(points_surf, (game.screen.get_width() // 2 - points_surf.get_width() // 2, 220 + 10 * 40))
        # Stat assign buttons (centered and spaced)
        stat_names = ["Strength", "Dexterity", "Vitality", "Intelligence"]
        stat_values = [game.player.strength, game.player.dexterity, game.player.vitality, game.player.intelligence]
        btn_font = pygame.font.SysFont("arial", 28, bold=True)
        btn_w, btn_h = 32, 32
        btn_x = game.screen.get_width() // 2 + 180
        btn_y_start = 220 + 11 * 40
        stat_x = game.screen.get_width() // 2 - 120
        for i, (name, value) in enumerate(zip(stat_names, stat_values)):
            stat_line = f"{name}: {value}"
            stat_surf = stats_font.render(stat_line, True, (220, 220, 220))
            y_pos = btn_y_start + i * 56
            game.screen.blit(stat_surf, (stat_x, y_pos))
            # Draw [+] button
            btn_rect = pygame.Rect(btn_x, y_pos, btn_w, btn_h)
            color = (80, 200, 80) if game.player.stat_points > 0 else (120, 120, 120)
            pygame.draw.rect(game.screen, color, btn_rect, border_radius=8)
            plus_surf = btn_font.render("+", True, (0, 0, 0))
            game.screen.blit(plus_surf, (btn_rect.x + btn_w // 2 - plus_surf.get_width() // 2, btn_rect.y + btn_h // 2 - plus_surf.get_height() // 2))
    elif tab_index == 2:
        # Skills tab
        title = font.render("SKILLS", True, (255, 255, 255))
        game.screen.blit(title, (game.screen.get_width() // 2 - title.get_width() // 2, 120))
        skills_font = pygame.font.SysFont("arial", 28)
        skills = [
            "Fireball   [Select]",
            # TODO: List more skills and selection logic
        ]
        for i, line in enumerate(skills):
            skill_surf = skills_font.render(line, True, (220, 220, 220))
            game.screen.blit(skill_surf, (game.screen.get_width() // 2 - skill_surf.get_width() // 2, 220 + i * 40))

    # --- Instructions ---
    hint_font = pygame.font.SysFont("arial", 24)
    hint = hint_font.render("Press I or Tab to close | ←/→ or 1/2/3 to switch tabs", True, (180, 180, 180))
    game.screen.blit(hint, (game.screen.get_width() // 2 - hint.get_width() // 2, game.screen.get_height() - 80))
    pygame.display.flip()
    hint = hint_font.render("Press I or Tab to close | ←/→ or 1/2/3 to switch tabs", True, (180, 180, 180))
    game.screen.blit(hint, (game.screen.get_width() // 2 - hint.get_width() // 2, game.screen.get_height() - 80))
    pygame.display.flip()
