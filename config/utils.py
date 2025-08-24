import pygame
from config.config import WIN_W, WIN_H

def draw_light_mask(center, radius):
    """Returns a surface with a circular transparent area for the torch glow."""
    mask = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        alpha = int(255 * (1 - r / radius))
        pygame.draw.circle(mask, (0, 0, 0, alpha), center, r)
    return mask