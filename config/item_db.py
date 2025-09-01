import pygame

def get_icon(path):
    # Only load icon if display is initialized
    if pygame.display.get_init():
        return pygame.image.load(path).convert_alpha()
    return None

# Load icons (replace with correct paths if needed)
ICON_SWORD = get_icon("textures/sword/sword.png")
ICON_STAFF = get_icon("textures/sword/sword_slash1.png")
ICON_BOW = get_icon("textures/player_movement/back1.png")
ICON_HELMET = get_icon("textures/player_movement/front1.png")
ICON_ARMOR = get_icon("textures/player_movement/right1.png")
ICON_BOOTS = get_icon("textures/player_movement/left1.png")
ICON_RING = get_icon("textures/torch/torch.png")

# Melee weapon
ITEM_SWORD = {
    "name": "Sword",
    "item_type": "melee",
    "equip_slot": "Main Hand",
    "item_class": "melee",
    "image": ICON_SWORD,
    "attack_min": 1,
    "attack_max": 5,
    "attack_speed": 1.2,
    "level": 1,
    "magic_min": 0,   # magical damage
    "magic_max": 0    # magical damage
}

# Magic weapon
ITEM_STAFF = {
    "name": "Staff",
    "item_type": "magic",
    "equip_slot": "Main Hand",
    "item_class": "magic",
    "image": ICON_STAFF,
    "attack_min": 2,
    "attack_max": 7,
    "attack_speed": 1.0,
    "level": 1,
    "magic_min": 3,   # magical damage
    "magic_max": 8    # magical damage
}

# Range weapon
ITEM_BOW = {
    "name": "Bow",
    "item_type": "range",
    "equip_slot": "Main Hand",
    "item_class": "range",
    "image": ICON_BOW,
    "attack_min": 1,
    "attack_max": 4,
    "attack_speed": 1.5,
    "level": 1,
    "magic_min": 0,   # magical damage
    "magic_max": 0    # magical damage
}

# Helmet
ITEM_HELMET = {
    "name": "Helmet",
    "item_type": "helmet",
    "equip_slot": "Helmet",
    "item_class": "helmet",
    "image": ICON_HELMET,
    "armor": 2,
    "level": 1,
}

# Armor
ITEM_ARMOR = {
    "name": "Armor",
    "item_type": "armor",
    "equip_slot": "Armor",
    "item_class": "armor",
    "image": ICON_ARMOR,
    "armor": 5,
    "level": 1,
}

# Boots
ITEM_BOOTS = {
    "name": "Boots",
    "item_type": "boots",
    "equip_slot": "Boots",
    "item_class": "boots",
    "image": ICON_BOOTS,
    "speed": 10,
    "level": 1,
}

# Accessory
ITEM_RING = {
    "name": "Ring",
    "item_type": "accessory",
    "equip_slot": "Accessory 1",
    "item_class": "accessory",
    "image": ICON_RING,
    "bonus": "mana+20",
    "level": 1,
}

WEAPON_ITEMS = [ITEM_SWORD, ITEM_STAFF, ITEM_BOW]
ARMOR_ITEMS = [ITEM_HELMET, ITEM_ARMOR, ITEM_BOOTS]
ACCESSORY_ITEMS = [ITEM_RING]

ITEM_GROUPS = {
    "weapon": WEAPON_ITEMS,
    "armor": ARMOR_ITEMS,
    "accessory": ACCESSORY_ITEMS,
}

def scale_item_stats(item: dict, level: int) -> dict:
    """Scale item stats by 1.2^level for damage, armor, speed, etc."""
    scaled = dict(item)
    level_mult = 1.2 ** (level - 1)
    # Scale attack
    if "attack_min" in scaled and scaled["attack_min"] is not None:
        scaled["attack_min"] = int(scaled["attack_min"] * level_mult)
    if "attack_max" in scaled and scaled["attack_max"] is not None:
        scaled["attack_max"] = int(scaled["attack_max"] * level_mult)
    # Scale magic
    if "magic_min" in scaled and scaled["magic_min"] is not None:
        scaled["magic_min"] = int(scaled["magic_min"] * level_mult)
    if "magic_max" in scaled and scaled["magic_max"] is not None:
        scaled["magic_max"] = int(scaled["magic_max"] * level_mult)
    # Scale armor
    if "armor" in scaled and scaled["armor"] is not None:
        scaled["armor"] = int(scaled["armor"] * level_mult)
    # Scale speed
    if "speed" in scaled and scaled["speed"] is not None:
        scaled["speed"] = int(scaled["speed"] * level_mult)
    # You can add more scaling for other numeric attributes if needed
    return scaled
