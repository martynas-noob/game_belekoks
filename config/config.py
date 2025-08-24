import pygame



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
    "#..........................#",
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

def world_to_screen(x: float, y: float, cam_x: float, cam_y: float) -> tuple[int, int]:
    return int(x - cam_x), int(y - cam_y)


def draw_light_mask(center, radius):
    """Returns a surface with a circular transparent area for the torch glow."""
    mask = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        alpha = int(255 * (1 - r / radius))
        pygame.draw.circle(mask, (0, 0, 0, alpha), center, r)
    return mask