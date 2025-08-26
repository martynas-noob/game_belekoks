import pygame
from config.config import world_to_screen

def show_damage_numbers(game, x, y, value, color=(255, 80, 80), duration=1.0):
    """Add a damage number to the game's list for display."""
    game.damage_numbers.append({
        "x": x,
        "y": y,
        "value": value,
        "timer": duration,
        "alpha": 255,
        "color": color,
        "duration": duration
    })

def draw_damage_numbers(game, screen, camera, dt):
    font = pygame.font.SysFont("arial", 28, bold=True)
    for dmg in game.damage_numbers[:]:
        dmg["y"] -= 30 * dt  # float upward
        dmg["timer"] -= dt
        dmg["alpha"] = int(255 * (dmg["timer"] / dmg["duration"]))
        if dmg["timer"] <= 0:
            game.damage_numbers.remove(dmg)
            continue
        dmg_surf = font.render(str(dmg["value"]), True, dmg["color"])
        dmg_surf.set_alpha(dmg["alpha"])
        px, py = world_to_screen(dmg["x"], dmg["y"], camera.x, camera.y)
        screen.blit(dmg_surf, (px - dmg_surf.get_width() // 2, py))

def show_health_bar(game, target, duration=2.0):
    """Show or refresh the health bar for a target or enemy."""
    # Use max_hp from the object if present, otherwise fallback
    max_hp = getattr(target, "max_hp", None)
    if max_hp is None:
        max_hp = getattr(target, "hit_points", None)
    if max_hp is None:
        max_hp = getattr(target, "max_hit_points", 300)
    game.target_health_bars[id(target)] = {
        "timer": duration,
        "hp": target.hit_points,
        "max_hp": max_hp,
        "x": target.x,
        "y": target.y - 60
    }

def update_health_bars(game, dt):
    """Update timers and remove expired health bars."""
    for bar in list(game.target_health_bars.values()):
        bar["timer"] -= dt
    for tid in [tid for tid, bar in game.target_health_bars.items() if bar["timer"] <= 0]:
        del game.target_health_bars[tid]

def draw_health_bars(game, screen, camera):
    """Draw all active health bars."""
    for bar in game.target_health_bars.values():
        px, py = world_to_screen(bar["x"], bar["y"], camera.x, camera.y)
        width = 48
        height = 8
        pygame.draw.rect(screen, (40, 40, 40), (px - width // 2, py, width, height), border_radius=4)
        hp_ratio = max(0, bar["hp"] / bar["max_hp"])
        pygame.draw.rect(screen, (120, 255, 120), (px - width // 2 + 2, py + 2, int((width - 4) * hp_ratio), height - 4), border_radius=3)
        pygame.draw.rect(screen, (0, 0, 0), (px - width // 2, py, width, height), 2, border_radius=4)

