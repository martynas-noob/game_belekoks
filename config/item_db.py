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
