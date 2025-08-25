import pygame
from config.config import world_to_screen

class Hitbox:
    def __init__(self, rect: pygame.Rect, color: tuple[int, int, int, int]):
        self.rect = rect
        self.color = color

    def draw(self, surface, camera):
        x, y = world_to_screen(self.rect.x, self.rect.y, camera.x, camera.y)
        hitbox_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        hitbox_surface.fill(self.color)
        surface.blit(hitbox_surface, (x, y))

def check_entity_collision(proposed_rect, entity_hitboxes, ignore_rect=None):
    for hitbox in entity_hitboxes:
        if ignore_rect is not None and hitbox.rect == ignore_rect:
            continue
        if proposed_rect.colliderect(hitbox.rect):
            return True
    return False

def resolve_enemy_collision(enemy, entity_hitboxes):
    enemy_rect = enemy.draw_enemy()
    for hitbox in entity_hitboxes:
        if hitbox.rect == enemy_rect:
            continue
        if enemy_rect.colliderect(hitbox.rect):
            return True
    return False
