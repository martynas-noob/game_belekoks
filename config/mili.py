import pygame

def start_sword_swing(player):
    if not player.sword_swinging:
        player.sword_swinging = True
        player.sword_anim_index = 0
        player.sword_anim_timer = 0.0

def update_sword(player, dt: float, sword_anim_len: int):
    if player.sword_swinging:
        player.sword_anim_timer += dt
        if player.sword_anim_timer >= player.sword_anim_speed:
            player.sword_anim_timer = 0.0
            player.sword_anim_index += 1
            if player.sword_anim_index >= sword_anim_len:
                player.sword_swinging = False
                player.sword_anim_index = 0

def draw_with_sword(player, surf, px, py, player_img, sword_img, sword_slash_imgs):
    SWORD_DRAW_SIZE = (48, 48)  # 40% smaller than original (80, 80)
    if player.sword_swinging and sword_slash_imgs:
        sword_frame = min(player.sword_anim_index, len(sword_slash_imgs)-1)
        sword_anim_img = sword_slash_imgs[sword_frame]
        if sword_anim_img.get_size() != SWORD_DRAW_SIZE:
            sword_anim_img = pygame.transform.scale(sword_anim_img, SWORD_DRAW_SIZE)
        offset_x = -20 if player.facing_left else 20
        offset_y = 10
        if player.facing_left:
            sword_anim_img = pygame.transform.flip(sword_anim_img, True, False)
        surf.blit(player_img, (px, py))
        surf.blit(sword_anim_img, (px + offset_x, py + offset_y))
    else:
        draw_sword_img = sword_img
        if sword_img.get_size() != SWORD_DRAW_SIZE:
            draw_sword_img = pygame.transform.scale(sword_img, SWORD_DRAW_SIZE)
        if player.facing_left:
            draw_sword_img = pygame.transform.flip(draw_sword_img, True, False)
        offset_x = -20 if player.facing_left else 20
        offset_y = 10
        surf.blit(player_img, (px, py))
        surf.blit(draw_sword_img, (px + offset_x, py + offset_y))
