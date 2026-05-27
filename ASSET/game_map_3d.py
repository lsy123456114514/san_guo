import pygame
import math
import random
import json
import os
import time
from ASSET.game_data import data, save, get_system_font_name, load_sound
from ASSET import safe_exit

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    opengl_available = True
except ImportError:
    opengl_available = False

try:
    from renderer_bindings import renderer
    c_renderer_available = renderer.is_available
except ImportError:
    c_renderer_available = False
    renderer = None

COLORS = {
    "bg_dark": (20, 20, 30),
    "bg_light": (30, 30, 50),
    "text_white": (255, 255, 255),
    "accent_gold": (255, 215, 0),
    "accent_green": (50, 205, 50),
    "accent_red": (255, 69, 0),
    "accent_blue": (64, 128, 255),
    "accent_blue_dark": (30, 60, 120)
}

MAP_SIZE = (2000, 2000)
MAX_LOCATIONS = 50
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
MINIMAP_SIZE = 200
INVENTORY_SLOTS = 36
MAX_PICKUP_DISTANCE = 5

MC_BLOCKS = {
    "air": {"color": (0, 0, 0, 0), "solid": False, "transparent": True},
    "stone": {"color": (128, 128, 128), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dirt": {"color": (139, 90, 43), "solid": True, "transparent": False, "hardness": 0.5, "tool": "shovel"},
    "grass": {"color": (34, 139, 34), "solid": True, "transparent": False, "hardness": 0.6, "tool": "shovel"},
    "cobblestone": {"color": (96, 96, 96), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "oak_log": {"color": (101, 67, 33), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "oak_planks": {"color": (188, 152, 98), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "oak_leaves": {"color": (50, 150, 50), "solid": False, "transparent": True, "hardness": 0.2, "tool": "shears"},
    "sand": {"color": (230, 220, 170), "solid": True, "transparent": False, "hardness": 0.5, "tool": "shovel"},
    "gravel": {"color": (150, 140, 130), "solid": True, "transparent": False, "hardness": 0.6, "tool": "shovel"},
    "water": {"color": (30, 60, 200, 150), "solid": False, "transparent": True, "hardness": 100, "source": True},
    "lava": {"color": (255, 80, 0), "solid": False, "transparent": True, "hardness": 100, "emissive": True},
    "glass": {"color": (200, 220, 255, 100), "solid": True, "transparent": True, "hardness": 0.3, "tool": "none"},
    "brick": {"color": (180, 80, 60), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "coal_ore": {"color": (100, 100, 100), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "iron_ore": {"color": (170, 140, 120), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "gold_ore": {"color": (230, 200, 100), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "diamond_ore": {"color": (60, 220, 220), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "oak_sapling": {"color": (50, 180, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "bedrock": {"color": (50, 50, 50), "solid": True, "transparent": False, "hardness": -1},
    "snow": {"color": (255, 255, 255), "solid": True, "transparent": False, "hardness": 0.2, "tool": "shovel"},
    "ice": {"color": (150, 180, 255, 200), "solid": True, "transparent": True, "hardness": 0.5},
    "clay": {"color": (170, 170, 180), "solid": True, "transparent": False, "hardness": 0.6, "tool": "shovel"},
    "oak_wood": {"color": (120, 80, 40), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "oak_slab": {"color": (180, 140, 90), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "oak_stairs": {"color": (175, 145, 95), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "oak_door": {"color": (140, 100, 60), "solid": True, "transparent": False, "hardness": 3.0, "tool": "axe"},
    "oak_fence": {"color": (160, 120, 80), "solid": False, "transparent": True, "hardness": 2.0, "tool": "axe"},
    "oak_trapdoor": {"color": (130, 90, 50), "solid": True, "transparent": False, "hardness": 3.0, "tool": "axe"},
    "oak_button": {"color": (160, 130, 90), "solid": False, "transparent": True, "hardness": 0.5},
    "oak_pressure_plate": {"color": (180, 150, 100), "solid": False, "transparent": True, "hardness": 0.5},
    "wall_torch": {"color": (255, 200, 50), "solid": False, "transparent": True, "hardness": 0.0, "emissive": True},
    "floor_torch": {"color": (255, 180, 50), "solid": False, "transparent": True, "hardness": 0.0, "emissive": True},
    "redstone_lamp": {"color": (150, 50, 50), "solid": True, "transparent": False, "hardness": 0.3, "tool": "pickaxe"},
    "glowstone": {"color": (255, 200, 100), "solid": True, "transparent": False, "hardness": 0.3, "emissive": True},
    "sea_lantern": {"color": (180, 220, 220), "solid": True, "transparent": True, "hardness": 0.3, "emissive": True},
    "obsidian": {"color": (20, 10, 30), "solid": True, "transparent": False, "hardness": 50, "tool": "diamond_pickaxe"},
    "netherrack": {"color": (110, 50, 50), "solid": True, "transparent": False, "hardness": 0.4, "tool": "pickaxe"},
    "soul_sand": {"color": (80, 65, 50), "solid": True, "transparent": False, "hardness": 0.5, "tool": "shovel"},
    "nether_bricks": {"color": (45, 25, 35), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "quartz_block": {"color": (230, 225, 215), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "end_stone": {"color": (220, 220, 180), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "purpur_block": {"color": (170, 120, 170), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "prismarine": {"color": (80, 150, 130), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "prismarine_bricks": {"color": (90, 160, 140), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dark_prismarine": {"color": (50, 90, 80), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "sea_pickle": {"color": (100, 180, 100), "solid": False, "transparent": True, "hardness": 0.0},
    "kelp": {"color": (50, 130, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "seagrass": {"color": (40, 130, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "coral_block": {"color": (200, 100, 120), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "coral": {"color": (180, 80, 100), "solid": False, "transparent": True, "hardness": 0.0},
    "coral_fan": {"color": (160, 70, 90), "solid": False, "transparent": True, "hardness": 0.0},
    "sandstone": {"color": (220, 200, 140), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "red_sandstone": {"color": (180, 90, 40), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "smooth_stone": {"color": (140, 140, 145), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "andesite": {"color": (130, 130, 135), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "diorite": {"color": (180, 180, 185), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "granite": {"color": (150, 100, 85), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "polished_andesite": {"color": (140, 140, 145), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "polished_diorite": {"color": (190, 190, 195), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "polished_granite": {"color": (160, 110, 95), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "cobblestone_slab": {"color": (105, 105, 110), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "cobblestone_stairs": {"color": (100, 100, 105), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "cobblestone_wall": {"color": (100, 100, 105), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "mossy_cobblestone": {"color": (80, 100, 80), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "stone_bricks": {"color": (120, 120, 125), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "chiseled_stone_bricks": {"color": (115, 115, 120), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "cracked_stone_bricks": {"color": (125, 125, 130), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "mossy_stone_bricks": {"color": (90, 110, 90), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "iron_block": {"color": (220, 220, 220), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "gold_block": {"color": (255, 215, 0), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "diamond_block": {"color": (60, 220, 220), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "emerald_block": {"color": (50, 220, 100), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "lapis_block": {"color": (40, 60, 180), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "redstone_block": {"color": (180, 20, 20), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "coal_block": {"color": (40, 40, 40), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "netherite_block": {"color": (50, 40, 50), "solid": True, "transparent": False, "hardness": 50, "tool": "diamond_pickaxe"},
    "hay_block": {"color": (200, 180, 80), "solid": True, "transparent": False, "hardness": 1.0, "tool": "sickle"},
    "melon": {"color": (80, 140, 40), "solid": True, "transparent": False, "hardness": 1.0, "tool": "axe"},
    "pumpkin": {"color": (200, 130, 30), "solid": True, "transparent": False, "hardness": 1.0, "tool": "axe"},
    "carved_pumpkin": {"color": (210, 140, 40), "solid": True, "transparent": False, "hardness": 1.0, "tool": "axe"},
    "jack_o_lantern": {"color": (220, 150, 50), "solid": True, "transparent": False, "hardness": 1.0, "emissive": True, "tool": "axe"},
    "terracotta": {"color": (155, 95, 70), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "white_terracotta": {"color": (210, 180, 160), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "orange_terracotta": {"color": (165, 85, 45), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "magenta_terracotta": {"color": (150, 90, 110), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "light_blue_terracotta": {"color": (115, 110, 140), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "yellow_terracotta": {"color": (190, 135, 45), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "lime_terracotta": {"color": (105, 120, 60), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "pink_terracotta": {"color": (160, 80, 75), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "gray_terracotta": {"color": (60, 40, 35), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "light_gray_terracotta": {"color": (135, 105, 95), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "cyan_terracotta": {"color": (85, 90, 90), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "purple_terracotta": {"color": (120, 70, 85), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "blue_terracotta": {"color": (75, 60, 90), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "brown_terracotta": {"color": (80, 55, 40), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "green_terracotta": {"color": (80, 85, 50), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "red_terracotta": {"color": (145, 65, 55), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "black_terracotta": {"color": (40, 30, 25), "solid": True, "transparent": False, "hardness": 1.8, "tool": "shovel"},
    "concrete": {"color": (160, 160, 170), "solid": True, "transparent": False, "hardness": 2.0},
    "white_concrete": {"color": (210, 215, 220), "solid": True, "transparent": False, "hardness": 2.0},
    "orange_concrete": {"color": (225, 100, 15), "solid": True, "transparent": False, "hardness": 2.0},
    "magenta_concrete": {"color": (170, 50, 150), "solid": True, "transparent": False, "hardness": 2.0},
    "light_blue_concrete": {"color": (40, 130, 220), "solid": True, "transparent": False, "hardness": 2.0},
    "yellow_concrete": {"color": (250, 210, 30), "solid": True, "transparent": False, "hardness": 2.0},
    "lime_concrete": {"color": (95, 170, 25), "solid": True, "transparent": False, "hardness": 2.0},
    "pink_concrete": {"color": (215, 130, 150), "solid": True, "transparent": False, "hardness": 2.0},
    "gray_concrete": {"color": (55, 60, 65), "solid": True, "transparent": False, "hardness": 2.0},
    "light_gray_concrete": {"color": (130, 130, 135), "solid": True, "transparent": False, "hardness": 2.0},
    "cyan_concrete": {"color": (25, 120, 150), "solid": True, "transparent": False, "hardness": 2.0},
    "purple_concrete": {"color": (100, 35, 140), "solid": True, "transparent": False, "hardness": 2.0},
    "blue_concrete": {"color": (45, 60, 150), "solid": True, "transparent": False, "hardness": 2.0},
    "brown_concrete": {"color": (115, 75, 45), "solid": True, "transparent": False, "hardness": 2.0},
    "green_concrete": {"color": (75, 95, 30), "solid": True, "transparent": False, "hardness": 2.0},
    "red_concrete": {"color": (150, 30, 25), "solid": True, "transparent": False, "hardness": 2.0},
    "black_concrete": {"color": (10, 12, 16), "solid": True, "transparent": False, "hardness": 2.0},
    "concrete_powder": {"color": (165, 165, 175), "solid": True, "transparent": False, "hardness": 0.5, "gravity": True},
    "white_concrete_powder": {"color": (215, 220, 225), "solid": True, "transparent": False, "hardness": 0.5, "gravity": True},
    "wool": {"color": (220, 220, 220), "solid": True, "transparent": False, "hardness": 0.8, "tool": "shears"},
    "carpet": {"color": (180, 180, 180), "solid": False, "transparent": True, "hardness": 0.1, "tool": "shears"},
    "cake": {"color": (230, 200, 180), "solid": False, "transparent": False, "hardness": 0.5},
    "white_bed": {"color": (230, 230, 230), "solid": False, "transparent": False, "hardness": 0.2},
    "black_bed": {"color": (30, 30, 35), "solid": False, "transparent": False, "hardness": 0.2},
    "brown_bed": {"color": (100, 70, 50), "solid": False, "transparent": False, "hardness": 0.2},
    "bookshelf": {"color": (160, 120, 80), "solid": True, "transparent": False, "hardness": 1.5, "tool": "axe"},
    "chest": {"color": (160, 120, 80), "solid": True, "transparent": False, "hardness": 2.5},
    "ender_chest": {"color": (20, 40, 40), "solid": True, "transparent": False, "hardness": 22.5},
    "furnace": {"color": (120, 120, 120), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe"},
    "blast_furnace": {"color": (120, 120, 130), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe"},
    "smoker": {"color": (140, 100, 80), "solid": True, "transparent": False, "hardness": 3.5, "tool": "axe"},
    "cartography_table": {"color": (140, 120, 90), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "crafting_table": {"color": (150, 110, 70), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "enchanting_table": {"color": (150, 100, 200), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "anvil": {"color": (120, 120, 130), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "grindstone": {"color": (130, 130, 135), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "stonecutter": {"color": (140, 140, 145), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe"},
    "loom": {"color": (140, 110, 90), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "lectern": {"color": (160, 130, 100), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "smithing_table": {"color": (130, 110, 90), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "composter": {"color": (140, 110, 80), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "barrel": {"color": (150, 110, 80), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "smithing_table": {"color": (130, 110, 90), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "bell": {"color": (180, 160, 90), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "campfire": {"color": (140, 100, 60), "solid": False, "transparent": True, "hardness": 1.0, "emissive": True},
    "soul_campfire": {"color": (80, 60, 40), "solid": False, "transparent": True, "hardness": 1.0, "emissive": True},
    "lantern": {"color": (255, 200, 100), "solid": False, "transparent": True, "hardness": 1.0, "emissive": True},
    "soul_lantern": {"color": (150, 180, 200), "solid": False, "transparent": True, "hardness": 1.0, "emissive": True},
    "candle": {"color": (240, 240, 220), "solid": False, "transparent": True, "hardness": 0.1},
    "end_rod": {"color": (220, 220, 220), "solid": False, "transparent": True, "hardness": 0.0, "emissive": True},
    "chain": {"color": (100, 100, 110), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "iron_bars": {"color": (150, 150, 160), "solid": False, "transparent": True, "hardness": 5.0, "tool": "pickaxe"},
    "glass_pane": {"color": (200, 220, 255, 150), "solid": False, "transparent": True, "hardness": 0.3},
    "iron_door": {"color": (180, 180, 190), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "iron_trapdoor": {"color": (180, 180, 190), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "oak_sign": {"color": (160, 130, 90), "solid": False, "transparent": True, "hardness": 1.0},
    "spruce_sign": {"color": (130, 100, 60), "solid": False, "transparent": True, "hardness": 1.0},
    "birch_sign": {"color": (200, 190, 160), "solid": False, "transparent": True, "hardness": 1.0},
    "jungle_sign": {"color": (170, 130, 90), "solid": False, "transparent": True, "hardness": 1.0},
    "acacia_sign": {"color": (170, 100, 60), "solid": False, "transparent": True, "hardness": 1.0},
    "dark_oak_sign": {"color": (60, 40, 25), "solid": False, "transparent": True, "hardness": 1.0},
    "oak_hanging_sign": {"color": (140, 110, 70), "solid": False, "transparent": True, "hardness": 1.0},
    "item_frame": {"color": (160, 130, 80), "solid": False, "transparent": True, "hardness": 1.0},
    "glow_item_frame": {"color": (170, 140, 90), "solid": False, "transparent": True, "hardness": 1.0, "emissive": True},
    "painting": {"color": (180, 140, 100), "solid": False, "transparent": True, "hardness": 1.0},
    "flower_pot": {"color": (180, 100, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "armor_stand": {"color": (120, 120, 130), "solid": False, "transparent": False, "hardness": 2.5},
    "player_head": {"color": (200, 160, 120), "solid": False, "transparent": False, "hardness": 1.0},
    "zombie_head": {"color": (80, 130, 80), "solid": False, "transparent": False, "hardness": 1.0},
    "skeleton_skull": {"color": (210, 210, 200), "solid": False, "transparent": False, "hardness": 1.0},
    "wither_skeleton_skull": {"color": (50, 50, 60), "solid": False, "transparent": False, "hardness": 1.0},
    "dragon_head": {"color": (120, 80, 140), "solid": False, "transparent": False, "hardness": 1.0},
    "beehive": {"color": (180, 140, 80), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "bee_nest": {"color": (170, 150, 80), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "honey_block": {"color": (230, 180, 60), "solid": True, "transparent": False, "hardness": 0.0},
    "honeycomb_block": {"color": (240, 190, 70), "solid": True, "transparent": False, "hardness": 0.0},
    "lodestone": {"color": (100, 100, 110), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe"},
    "sculk_sensor": {"color": (20, 30, 40), "solid": False, "transparent": True, "hardness": 1.5, "tool": "pickaxe"},
    "sculk_catalyst": {"color": (25, 35, 45), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "sculk_shrieker": {"color": (30, 40, 50), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "sculk_vein": {"color": (15, 25, 35), "solid": False, "transparent": True, "hardness": 0.0},
    "moss_block": {"color": (80, 120, 60), "solid": True, "transparent": False, "hardness": 0.1, "tool": "shovel"},
    "moss_carpet": {"color": (70, 110, 50), "solid": False, "transparent": True, "hardness": 0.1, "tool": "shears"},
    "sponge": {"color": (200, 200, 80), "solid": True, "transparent": False, "hardness": 0.6, "tool": "shovel"},
    "wet_sponge": {"color": (180, 190, 100), "solid": True, "transparent": False, "hardness": 0.6, "tool": "shovel"},
    "turtle_egg": {"color": (220, 220, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "dragon_egg": {"color": (40, 30, 50), "solid": False, "transparent": False, "hardness": 3.0},
    " warden_spawn": {"color": (50, 55, 60), "solid": False, "transparent": False, "hardness": 0.0},
    "respawn_anchor": {"color": (50, 50, 80), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "crying_obsidian": {"color": (30, 20, 40), "solid": True, "transparent": False, "hardness": 50, "tool": "diamond_pickaxe"},
    "shulker_box": {"color": (150, 100, 160), "solid": True, "transparent": False, "hardness": 2.5},
    "undyed_shulker_box": {"color": (170, 150, 170), "solid": True, "transparent": False, "hardness": 2.5},
    "loom": {"color": (140, 110, 90), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "fletching_table": {"color": (180, 150, 100), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "brewing_stand": {"color": (120, 120, 130), "solid": False, "transparent": True, "hardness": 0.5, "tool": "pickaxe"},
    "cauldron": {"color": (120, 120, 130), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "water_cauldron": {"color": (40, 80, 200, 180), "solid": True, "transparent": True, "hardness": 2.0, "tool": "pickaxe"},
    "lavacauldron": {"color": (220, 60, 0, 180), "solid": True, "transparent": True, "hardness": 2.0, "tool": "pickaxe"},
    "flower_pot": {"color": (180, 100, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_oak_sapling": {"color": (50, 180, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_spruce_sapling": {"color": (40, 170, 40), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_birch_sapling": {"color": (60, 190, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_jungle_sapling": {"color": (55, 175, 55), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_acacia_sapling": {"color": (45, 165, 45), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_dark_oak_sapling": {"color": (35, 155, 35), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_fern": {"color": (60, 150, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_dandelion": {"color": (240, 220, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_poppy": {"color": (220, 50, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_blue_orchid": {"color": (50, 50, 200), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_allium": {"color": (180, 100, 180), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_azure_bluet": {"color": (240, 240, 240), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_red_tulip": {"color": (200, 40, 40), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_orange_tulip": {"color": (220, 100, 30), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_white_tulip": {"color": (240, 240, 230), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_pink_tulip": {"color": (240, 150, 170), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_oxeye_daisy": {"color": (230, 230, 200), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_cornflower": {"color": (80, 120, 220), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_lily_of_the_valley": {"color": (230, 235, 220), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_wither_rose": {"color": (40, 40, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_red_mushroom": {"color": (220, 80, 80), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_brown_mushroom": {"color": (160, 120, 80), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_dead_bush": {"color": (120, 90, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_azalea_bush": {"color": (60, 180, 80), "solid": False, "transparent": True, "hardness": 0.0},
    "potted_flowering_azalea_bush": {"color": (70, 190, 90), "solid": False, "transparent": True, "hardness": 0.0},
    "chain_command_block": {"color": (140, 150, 130), "solid": True, "transparent": False, "hardness": 0.0},
    "repeating_command_block": {"color": (140, 100, 130), "solid": True, "transparent": False, "hardness": 0.0},
    "command_block": {"color": (140, 80, 100), "solid": True, "transparent": False, "hardness": 0.0},
    "chain": {"color": (100, 100, 110), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe"},
    "lightning_rod": {"color": (210, 170, 120), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "daylight_detector": {"color": (160, 150, 130), "solid": True, "transparent": False, "hardness": 0.0},
    "daylight_detector_inverted": {"color": (140, 130, 110), "solid": True, "transparent": False, "hardness": 0.0},
    "target": {"color": (200, 200, 200), "solid": True, "transparent": False, "hardness": 0.0},
    "scaffolding": {"color": (160, 130, 100), "solid": False, "transparent": True, "hardness": 0.0},
    "brick_stairs": {"color": (170, 80, 60), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "oak_stairs": {"color": (175, 145, 95), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "spruce_stairs": {"color": (110, 80, 45), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "birch_stairs": {"color": (195, 180, 140), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "jungle_stairs": {"color": (155, 115, 75), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "acacia_stairs": {"color": (160, 90, 55), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "dark_oak_stairs": {"color": (65, 45, 25), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "cobblestone_stairs": {"color": (100, 100, 105), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "sandstone_stairs": {"color": (210, 190, 130), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "red_sandstone_stairs": {"color": (170, 85, 35), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "prismarine_stairs": {"color": (80, 150, 130), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "prismarine_brick_stairs": {"color": (90, 160, 140), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dark_prismarine_stairs": {"color": (50, 90, 80), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "quartz_stairs": {"color": (220, 215, 205), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "purpur_stairs": {"color": (160, 110, 160), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "nether_brick_stairs": {"color": (50, 30, 40), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "red_nether_brick_stairs": {"color": (60, 20, 20), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "stone_stairs": {"color": (140, 140, 145), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "smooth_quartz_stairs": {"color": (225, 220, 210), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "smooth_red_sandstone_stairs": {"color": (175, 90, 40), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "granite_stairs": {"color": (150, 100, 85), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "andesite_stairs": {"color": (130, 130, 135), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "diorite_stairs": {"color": (180, 180, 185), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "polished_granite_stairs": {"color": (160, 110, 95), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "polished_diorite_stairs": {"color": (190, 190, 195), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "polished_andesite_stairs": {"color": (140, 140, 145), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "mossy_cobblestone_stairs": {"color": (80, 100, 80), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "mossy_stone_brick_stairs": {"color": (90, 110, 90), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "end_stone_brick_stairs": {"color": (215, 215, 175), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "stone_brick_stairs": {"color": (120, 120, 125), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "oak_slab": {"color": (180, 140, 90), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "spruce_slab": {"color": (115, 85, 50), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "birch_slab": {"color": (195, 180, 140), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "jungle_slab": {"color": (160, 120, 80), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "acacia_slab": {"color": (165, 95, 60), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "dark_oak_slab": {"color": (70, 50, 30), "solid": True, "transparent": False, "hardness": 2.0, "tool": "axe"},
    "cobblestone_slab": {"color": (105, 105, 110), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "sandstone_slab": {"color": (210, 190, 130), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "red_sandstone_slab": {"color": (170, 85, 35), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "quartz_slab": {"color": (220, 215, 205), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "prismarine_slab": {"color": (80, 150, 130), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "prismarine_brick_slab": {"color": (90, 160, 140), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dark_prismarine_slab": {"color": (50, 90, 80), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "purpur_slab": {"color": (160, 110, 160), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "smooth_stone_slab": {"color": (145, 145, 150), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "smooth_quartz_slab": {"color": (225, 220, 210), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "smooth_red_sandstone_slab": {"color": (175, 90, 40), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "cobblestone_wall": {"color": (100, 100, 105), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "mossy_cobblestone_wall": {"color": (80, 100, 80), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "granite_wall": {"color": (150, 100, 85), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "diorite_wall": {"color": (180, 180, 185), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "andesite_wall": {"color": (130, 130, 135), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "sandstone_wall": {"color": (210, 190, 130), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "red_sandstone_wall": {"color": (170, 85, 35), "solid": True, "transparent": False, "hardness": 0.8, "tool": "pickaxe"},
    "brick_wall": {"color": (170, 80, 60), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "stone_brick_wall": {"color": (120, 120, 125), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "mossy_stone_brick_wall": {"color": (90, 110, 90), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "nether_brick_wall": {"color": (50, 30, 40), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe"},
    "end_stone_brick_wall": {"color": (215, 215, 175), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "prismarine_wall": {"color": (80, 150, 130), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "redstone_torch": {"color": (180, 30, 30), "solid": False, "transparent": True, "hardness": 0.0, "emissive": True},
    "redstone_wire": {"color": (180, 30, 30), "solid": False, "transparent": True, "hardness": 0.0},
    "repeater": {"color": (160, 60, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "comparator": {"color": (160, 60, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "piston": {"color": (150, 150, 155), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "sticky_piston": {"color": (150, 150, 155), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "observer": {"color": (130, 130, 135), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "hopper": {"color": (120, 120, 130), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe"},
    "dropper": {"color": (120, 120, 125), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe"},
    "dispenser": {"color": (120, 120, 125), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe"},
    "lever": {"color": (120, 100, 80), "solid": False, "transparent": True, "hardness": 1.0},
    "stone_button": {"color": (140, 140, 145), "solid": False, "transparent": True, "hardness": 0.5},
    "oak_button": {"color": (160, 130, 90), "solid": False, "transparent": True, "hardness": 0.5},
    "tripwire_hook": {"color": (160, 140, 100), "solid": False, "transparent": True, "hardness": 0.0},
    "trapped_chest": {"color": (160, 120, 80), "solid": True, "transparent": False, "hardness": 2.5},
    "tnt": {"color": (200, 80, 60), "solid": True, "transparent": False, "hardness": 0.0},
    "note_block": {"color": (160, 130, 80), "solid": True, "transparent": False, "hardness": 0.8, "tool": "axe"},
    "jukebox": {"color": (150, 110, 70), "solid": True, "transparent": False, "hardness": 2.5, "tool": "axe"},
    "record_13": {"color": (200, 200, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "record_cat": {"color": (50, 200, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "record_blocks": {"color": (200, 50, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "record_chirp": {"color": (50, 200, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "record_far": {"color": (50, 50, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "record_mall": {"color": (200, 50, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "record_mellohi": {"color": (200, 100, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "record_stal": {"color": (100, 50, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "record_strad": {"color": (200, 200, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "record_ward": {"color": (50, 100, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "record_11": {"color": (50, 200, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "record_wait": {"color": (200, 200, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "gold_ingot": {"color": (255, 215, 0), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_ingot": {"color": (220, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond": {"color": (60, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "emerald": {"color": (50, 220, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "lapis_lazuli": {"color": (40, 60, 180), "solid": False, "transparent": False, "hardness": 0.1},
    "coal": {"color": (40, 40, 40), "solid": False, "transparent": False, "hardness": 0.1},
    "charcoal": {"color": (60, 50, 40), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_ingot": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "wooden_pickaxe": {"color": (180, 140, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "stone_pickaxe": {"color": (140, 140, 145), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_pickaxe": {"color": (220, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_pickaxe": {"color": (60, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_pickaxe": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "wooden_axe": {"color": (180, 140, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "stone_axe": {"color": (140, 140, 145), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_axe": {"color": (220, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_axe": {"color": (60, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_axe": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "wooden_shovel": {"color": (180, 140, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "stone_shovel": {"color": (140, 140, 145), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_shovel": {"color": (220, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_shovel": {"color": (60, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_shovel": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "wooden_hoe": {"color": (180, 140, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "stone_hoe": {"color": (140, 140, 145), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_hoe": {"color": (220, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_hoe": {"color": (60, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_hoe": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "wooden_sword": {"color": (180, 140, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "stone_sword": {"color": (140, 140, 145), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_sword": {"color": (220, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_sword": {"color": (60, 220, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_sword": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "bow": {"color": (150, 110, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "crossbow": {"color": (150, 110, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "arrow": {"color": (180, 150, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "shield": {"color": (140, 110, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "trident": {"color": (60, 200, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "fishing_rod": {"color": (150, 110, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "carrot_on_a_stick": {"color": (230, 150, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "warped_fungus_on_a_stick": {"color": (40, 180, 140), "solid": False, "transparent": False, "hardness": 0.1},
    "oak_boat": {"color": (160, 120, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "spruce_boat": {"color": (100, 70, 40), "solid": False, "transparent": False, "hardness": 0.1},
    "birch_boat": {"color": (190, 175, 140), "solid": False, "transparent": False, "hardness": 0.1},
    "jungle_boat": {"color": (150, 110, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "acacia_boat": {"color": (160, 90, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "dark_oak_boat": {"color": (60, 40, 25), "solid": False, "transparent": False, "hardness": 0.1},
    "saddle": {"color": (120, 80, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "horse_armor_leather": {"color": (140, 100, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "horse_armor_iron": {"color": (200, 200, 210), "solid": False, "transparent": False, "hardness": 0.1},
    "horse_armor_gold": {"color": (250, 210, 0), "solid": False, "transparent": False, "hardness": 0.1},
    "horse_armor_diamond": {"color": (60, 210, 210), "solid": False, "transparent": False, "hardness": 0.1},
    "leather_helmet": {"color": (140, 100, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "leather_chestplate": {"color": (140, 100, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "leather_leggings": {"color": (140, 100, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "leather_boots": {"color": (140, 100, 70), "solid": False, "transparent": False, "hardness": 0.1},
    "chainmail_helmet": {"color": (120, 120, 130), "solid": False, "transparent": False, "hardness": 0.1},
    "chainmail_chestplate": {"color": (120, 120, 130), "solid": False, "transparent": False, "hardness": 0.1},
    "chainmail_leggings": {"color": (120, 120, 130), "solid": False, "transparent": False, "hardness": 0.1},
    "chainmail_boots": {"color": (120, 120, 130), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_helmet": {"color": (210, 210, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_chestplate": {"color": (210, 210, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_leggings": {"color": (210, 210, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "iron_boots": {"color": (210, 210, 220), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_helmet": {"color": (60, 210, 210), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_chestplate": {"color": (60, 210, 210), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_leggings": {"color": (60, 210, 210), "solid": False, "transparent": False, "hardness": 0.1},
    "diamond_boots": {"color": (60, 210, 210), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_helmet": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_chestplate": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_leggings": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "netherite_boots": {"color": (60, 50, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "turtle_helmet": {"color": (140, 190, 180), "solid": False, "transparent": False, "hardness": 0.1},
    "elytra": {"color": (180, 180, 160), "solid": False, "transparent": False, "hardness": 0.1},
    "totem_of_undying": {"color": (255, 215, 0), "solid": False, "transparent": False, "hardness": 0.1},
    "enchanted_golden_apple": {"color": (255, 220, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "golden_apple": {"color": (255, 200, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "apple": {"color": (200, 150, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "bread": {"color": (220, 190, 140), "solid": False, "transparent": False, "hardness": 0.1},
    "cooked_beef": {"color": (110, 60, 40), "solid": False, "transparent": False, "hardness": 0.1},
    "raw_beef": {"color": (180, 60, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "cooked_chicken": {"color": (200, 160, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "raw_chicken": {"color": (200, 180, 180), "solid": False, "transparent": False, "hardness": 0.1},
    "cooked_mutton": {"color": (190, 150, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "raw_mutton": {"color": (200, 180, 180), "solid": False, "transparent": False, "hardness": 0.1},
    "cooked_porkchop": {"color": (170, 120, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "raw_porkchop": {"color": (200, 150, 160), "solid": False, "transparent": False, "hardness": 0.1},
    "cooked_rabbit": {"color": (180, 140, 110), "solid": False, "transparent": False, "hardness": 0.1},
    "raw_rabbit": {"color": (200, 180, 180), "solid": False, "transparent": False, "hardness": 0.1},
    "cooked_cod": {"color": (200, 180, 140), "solid": False, "transparent": False, "hardness": 0.1},
    "raw_cod": {"color": (200, 200, 180), "solid": False, "transparent": False, "hardness": 0.1},
    "cooked_salmon": {"color": (200, 140, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "raw_salmon": {"color": (220, 140, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "tropical_fish": {"color": (220, 180, 140), "solid": False, "transparent": False, "hardness": 0.1},
    "pufferfish": {"color": (200, 200, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "rotten_flesh": {"color": (120, 100, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "spider_eye": {"color": (180, 60, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "cooked_spider_eye": {"color": (140, 80, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "rabbit_stew": {"color": (180, 140, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "mushroom_stew": {"color": (180, 140, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "beetroot_soup": {"color": (140, 60, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "suspicious_stew": {"color": (180, 150, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "pumpkin_pie": {"color": (220, 180, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "cake": {"color": (230, 200, 180), "solid": False, "transparent": False, "hardness": 0.1},
    "cookie": {"color": (200, 170, 130), "solid": False, "transparent": False, "hardness": 0.1},
    "melon_slice": {"color": (140, 190, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "dried_kelp": {"color": (80, 140, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "carrot": {"color": (230, 130, 30), "solid": False, "transparent": False, "hardness": 0.1},
    "golden_carrot": {"color": (255, 200, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "potato": {"color": (210, 180, 140), "solid": False, "transparent": False, "hardness": 0.1},
    "baked_potato": {"color": (220, 170, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "poisonous_potato": {"color": (180, 160, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "beetroot": {"color": (150, 40, 40), "solid": False, "transparent": False, "hardness": 0.1},
    "sweet_berries": {"color": (60, 140, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "glow_berries": {"color": (220, 200, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "chorus_fruit": {"color": (180, 120, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "popped_chorus_fruit": {"color": (200, 160, 200), "solid": False, "transparent": False, "hardness": 0.1},
    "wheat": {"color": (220, 200, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "wheat_seeds": {"color": (220, 210, 120), "solid": False, "transparent": False, "hardness": 0.1},
    "pumpkin_seeds": {"color": (200, 160, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "melon_seeds": {"color": (160, 190, 100), "solid": False, "transparent": False, "hardness": 0.1},
    "beetroot_seeds": {"color": (170, 60, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "oak_sapling": {"color": (50, 180, 50), "solid": False, "transparent": False, "hardness": 0.1},
    "spruce_sapling": {"color": (40, 170, 40), "solid": False, "transparent": False, "hardness": 0.1},
    "birch_sapling": {"color": (60, 190, 60), "solid": False, "transparent": False, "hardness": 0.1},
    "jungle_sapling": {"color": (55, 175, 55), "solid": False, "transparent": False, "hardness": 0.1},
    "acacia_sapling": {"color": (45, 165, 45), "solid": False, "transparent": False, "hardness": 0.1},
    "dark_oak_sapling": {"color": (35, 155, 35), "solid": False, "transparent": False, "hardness": 0.1},
    "azalea": {"color": (60, 180, 80), "solid": False, "transparent": False, "hardness": 0.1},
    "flowering_azalea": {"color": (70, 190, 90), "solid": False, "transparent": False, "hardness": 0.1},
    "oak_leaves": {"color": (50, 150, 50), "solid": False, "transparent": True, "hardness": 0.2},
    "spruce_leaves": {"color": (40, 120, 40), "solid": False, "transparent": True, "hardness": 0.2},
    "birch_leaves": {"color": (60, 160, 60), "solid": False, "transparent": True, "hardness": 0.2},
    "jungle_leaves": {"color": (50, 140, 50), "solid": False, "transparent": True, "hardness": 0.2},
    "acacia_leaves": {"color": (55, 155, 55), "solid": False, "transparent": True, "hardness": 0.2},
    "dark_oak_leaves": {"color": (40, 130, 40), "solid": False, "transparent": True, "hardness": 0.2},
    "vine": {"color": (50, 130, 50), "solid": False, "transparent": True, "hardness": 0.1},
    "lily_pad": {"color": (40, 140, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "spore_blossom": {"color": (200, 180, 220), "solid": False, "transparent": True, "hardness": 0.0},
    "hanging_roots": {"color": (100, 80, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "small_dripleaf": {"color": (50, 140, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "big_dripleaf": {"color": (50, 140, 50), "solid": False, "transparent": True, "hardness": 0.1},
    "moss_carpet": {"color": (70, 110, 50), "solid": False, "transparent": True, "hardness": 0.1},
    "rooted_dirt": {"color": (130, 85, 40), "solid": True, "transparent": False, "hardness": 0.5, "tool": "shovel"},
    "grass_block": {"color": (90, 160, 60), "solid": True, "transparent": False, "hardness": 0.6, "tool": "shovel"},
    "podzol": {"color": (90, 60, 30), "solid": True, "transparent": False, "hardness": 0.5, "tool": "shovel"},
    "mycelium": {"color": (140, 100, 130), "solid": True, "transparent": False, "hardness": 0.6, "tool": "shovel"},
    "dirt_path": {"color": (120, 85, 50), "solid": True, "transparent": False, "hardness": 0.5, "tool": "shovel"},
    "farmland": {"color": (120, 80, 50), "solid": True, "transparent": False, "hardness": 0.6, "tool": "shovel"},
    "grass": {"color": (80, 160, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "tall_grass": {"color": (70, 150, 45), "solid": False, "transparent": True, "hardness": 0.0},
    "fern": {"color": (70, 140, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "large_fern": {"color": (70, 140, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_bush": {"color": (120, 90, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "seagrass": {"color": (40, 130, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "kelp": {"color": (50, 130, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "sea_pickle": {"color": (100, 180, 100), "solid": False, "transparent": True, "hardness": 0.0},
    "bamboo": {"color": (140, 180, 80), "solid": False, "transparent": True, "hardness": 0.0},
    "sugar_cane": {"color": (140, 200, 100), "solid": False, "transparent": True, "hardness": 0.0},
    "cactus": {"color": (20, 140, 60), "solid": True, "transparent": False, "hardness": 0.4},
    "sweet_berry_bush": {"color": (60, 140, 200), "solid": False, "transparent": True, "hardness": 0.0},
    "cave_vines": {"color": (50, 130, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "cave_vines_plant": {"color": (50, 130, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "glow_lichen": {"color": (150, 200, 100), "solid": False, "transparent": True, "hardness": 0.0, "emissive": True},
    "lily_of_the_valley": {"color": (230, 235, 220), "solid": False, "transparent": False, "hardness": 0.0},
    "wither_rose": {"color": (40, 40, 50), "solid": False, "transparent": False, "hardness": 0.0},
    "cornflower": {"color": (80, 120, 220), "solid": False, "transparent": False, "hardness": 0.0},
    "lily_of_the_valley": {"color": (230, 235, 220), "solid": False, "transparent": False, "hardness": 0.0},
    "wither_rose": {"color": (40, 40, 50), "solid": False, "transparent": False, "hardness": 0.0},
    "sunflower": {"color": (240, 220, 60), "solid": False, "transparent": False, "hardness": 0.0},
    "lilac": {"color": (180, 120, 180), "solid": False, "transparent": False, "hardness": 0.0},
    "rose_bush": {"color": (200, 50, 50), "solid": False, "transparent": False, "hardness": 0.0},
    "peony": {"color": (200, 160, 180), "solid": False, "transparent": False, "hardness": 0.0},
    "tall_grass": {"color": (70, 150, 45), "solid": False, "transparent": True, "hardness": 0.0},
    "large_fern": {"color": (70, 140, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "dandelion": {"color": (240, 220, 50), "solid": False, "transparent": False, "hardness": 0.0},
    "poppy": {"color": (220, 50, 50), "solid": False, "transparent": False, "hardness": 0.0},
    "blue_orchid": {"color": (50, 50, 200), "solid": False, "transparent": False, "hardness": 0.0},
    "allium": {"color": (180, 100, 180), "solid": False, "transparent": False, "hardness": 0.0},
    "azure_bluet": {"color": (240, 240, 240), "solid": False, "transparent": False, "hardness": 0.0},
    "red_tulip": {"color": (200, 40, 40), "solid": False, "transparent": False, "hardness": 0.0},
    "orange_tulip": {"color": (220, 100, 30), "solid": False, "transparent": False, "hardness": 0.0},
    "white_tulip": {"color": (240, 240, 230), "solid": False, "transparent": False, "hardness": 0.0},
    "pink_tulip": {"color": (240, 150, 170), "solid": False, "transparent": False, "hardness": 0.0},
    "oxeye_daisy": {"color": (230, 230, 200), "solid": False, "transparent": False, "hardness": 0.0},
    "cornflower": {"color": (80, 120, 220), "solid": False, "transparent": False, "hardness": 0.0},
    "lily_pad": {"color": (40, 140, 50), "solid": False, "transparent": True, "hardness": 0.0},
    "brain_coral_block": {"color": (200, 100, 120), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "bubble_coral_block": {"color": (140, 80, 180), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "fire_coral_block": {"color": (180, 60, 60), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "horn_coral_block": {"color": (220, 200, 80), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "tube_coral_block": {"color": (60, 100, 200), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dead_brain_coral_block": {"color": (130, 125, 115), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dead_bubble_coral_block": {"color": (130, 125, 115), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dead_fire_coral_block": {"color": (130, 125, 115), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dead_horn_coral_block": {"color": (130, 125, 115), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "dead_tube_coral_block": {"color": (130, 125, 115), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe"},
    "brain_coral": {"color": (200, 100, 120), "solid": False, "transparent": True, "hardness": 0.0},
    "bubble_coral": {"color": (140, 80, 180), "solid": False, "transparent": True, "hardness": 0.0},
    "fire_coral": {"color": (180, 60, 60), "solid": False, "transparent": True, "hardness": 0.0},
    "horn_coral": {"color": (220, 200, 80), "solid": False, "transparent": True, "hardness": 0.0},
    "tube_coral": {"color": (60, 100, 200), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_brain_coral": {"color": (130, 125, 115), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_bubble_coral": {"color": (130, 125, 115), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_fire_coral": {"color": (130, 125, 115), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_horn_coral": {"color": (130, 125, 115), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_tube_coral": {"color": (130, 125, 115), "solid": False, "transparent": True, "hardness": 0.0},
    "brain_coral_fan": {"color": (190, 95, 115), "solid": False, "transparent": True, "hardness": 0.0},
    "bubble_coral_fan": {"color": (135, 75, 175), "solid": False, "transparent": True, "hardness": 0.0},
    "fire_coral_fan": {"color": (170, 55, 55), "solid": False, "transparent": True, "hardness": 0.0},
    "horn_coral_fan": {"color": (210, 195, 75), "solid": False, "transparent": True, "hardness": 0.0},
    "tube_coral_fan": {"color": (55, 95, 195), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_brain_coral_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_bubble_coral_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_fire_coral_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_horn_coral_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_tube_coral_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "brain_coral_wall_fan": {"color": (190, 95, 115), "solid": False, "transparent": True, "hardness": 0.0},
    "bubble_coral_wall_fan": {"color": (135, 75, 175), "solid": False, "transparent": True, "hardness": 0.0},
    "fire_coral_wall_fan": {"color": (170, 55, 55), "solid": False, "transparent": True, "hardness": 0.0},
    "horn_coral_wall_fan": {"color": (210, 195, 75), "solid": False, "transparent": True, "hardness": 0.0},
    "tube_coral_wall_fan": {"color": (55, 95, 195), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_brain_coral_wall_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_bubble_coral_wall_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_fire_coral_wall_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_horn_coral_wall_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    "dead_tube_coral_wall_fan": {"color": (120, 115, 105), "solid": False, "transparent": True, "hardness": 0.0},
    
    "tech_machine_frame": {"color": (100, 110, 120), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe", "tech": True},
    "tech_energy_core": {"color": (0, 150, 255), "solid": True, "transparent": True, "hardness": 4.0, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_generator": {"color": (50, 70, 90), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe", "tech": True},
    "tech_matter_transporter": {"color": (100, 50, 150), "solid": True, "transparent": True, "hardness": 4.0, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_laser_node": {"color": (255, 0, 50), "solid": True, "transparent": True, "hardness": 3.0, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_solar_panel": {"color": (20, 40, 60), "solid": True, "transparent": False, "hardness": 2.5, "tool": "pickaxe", "tech": True},
    "tech_quantum_storage": {"color": (80, 200, 200), "solid": True, "transparent": True, "hardness": 4.0, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_nano_assembler": {"color": (200, 200, 220), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe", "tech": True},
    "tech_hologram_projector": {"color": (150, 100, 200), "solid": False, "transparent": True, "hardness": 3.0, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_force_field": {"color": (100, 180, 255, 100), "solid": True, "transparent": True, "hardness": -1, "tech": True},
    "tech_anti_gravity": {"color": (50, 255, 200), "solid": True, "transparent": True, "hardness": 4.0, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_teleporter": {"color": (200, 50, 200), "solid": False, "transparent": True, "hardness": 4.5, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_fabricator": {"color": (120, 100, 80), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe", "tech": True},
    "tech_reactor": {"color": (30, 30, 50), "solid": True, "transparent": False, "hardness": 5.0, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_fusion_core": {"color": (255, 200, 100), "solid": True, "transparent": True, "hardness": 4.5, "tool": "pickaxe", "emissive": True, "tech": True},
    "tech_circuit_board": {"color": (50, 80, 50), "solid": True, "transparent": False, "hardness": 1.5, "tool": "pickaxe", "tech": True},
    "tech_advanced_chip": {"color": (100, 150, 200), "solid": True, "transparent": False, "hardness": 2.0, "tool": "pickaxe", "tech": True},
    "tech_plasma_conduit": {"color": (200, 100, 50), "solid": True, "transparent": True, "hardness": 3.5, "tool": "pickaxe", "tech": True},
    "tech_gravity_plate": {"color": (100, 80, 120), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe", "tech": True},
    "tech_security_door": {"color": (80, 100, 120), "solid": True, "transparent": False, "hardness": 4.0, "tool": "pickaxe", "tech": True},
    "tech_cooling_unit": {"color": (70, 130, 160), "solid": True, "transparent": False, "hardness": 3.0, "tool": "pickaxe", "tech": True},
    "tech_autominer": {"color": (150, 70, 50), "solid": True, "transparent": False, "hardness": 3.5, "tool": "pickaxe", "tech": True},
    "tech_energy_cable": {"color": (60, 60, 70), "solid": False, "transparent": True, "hardness": 1.0, "tool": "none", "tech": True},
    
    "gun_ak47": {"color": (80, 60, 40), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 25, "fire_rate": 0.15, "ammo_type": "ammo_762"},
    "gun_m4a1": {"color": (60, 60, 60), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 20, "fire_rate": 0.12, "ammo_type": "ammo_556"},
    "gun_awp": {"color": (50, 50, 50), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 100, "fire_rate": 1.5, "ammo_type": "ammo_762"},
    "gun_mp5": {"color": (70, 70, 70), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 15, "fire_rate": 0.08, "ammo_type": "ammo_9mm"},
    "gun_m1911": {"color": (50, 50, 50), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 18, "fire_rate": 0.2, "ammo_type": "ammo_45acp"},
    "gun_glock": {"color": (40, 40, 40), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 12, "fire_rate": 0.15, "ammo_type": "ammo_9mm"},
    "gun_scarh": {"color": (55, 55, 55), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 30, "fire_rate": 0.1, "ammo_type": "ammo_762"},
    "gun_p90": {"color": (65, 65, 65), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 18, "fire_rate": 0.06, "ammo_type": "ammo_57mm"},
    "gun_uzi": {"color": (45, 45, 45), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 10, "fire_rate": 0.05, "ammo_type": "ammo_9mm"},
    "gun_deserteagle": {"color": (60, 50, 40), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 35, "fire_rate": 0.3, "ammo_type": "ammo_50ae"},
    "gun_barrett": {"color": (40, 40, 40), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 150, "fire_rate": 2.0, "ammo_type": "ammo_50bmg"},
    "gun_rpg": {"color": (70, 50, 40), "solid": False, "transparent": False, "hardness": 0.1, "gun": True, "damage": 200, "fire_rate": 3.0, "ammo_type": "ammo_rpg"},
    
    "ammo_762": {"color": (180, 140, 100), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": "7.62mm"},
    "ammo_556": {"color": (160, 130, 90), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": "5.56mm"},
    "ammo_9mm": {"color": (200, 180, 140), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": "9mm"},
    "ammo_45acp": {"color": (190, 170, 130), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": ".45 ACP"},
    "ammo_50ae": {"color": (220, 200, 160), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": ".50 AE"},
    "ammo_50bmg": {"color": (210, 190, 150), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": ".50 BMG"},
    "ammo_57mm": {"color": (170, 150, 110), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": "5.7mm"},
    "ammo_rpg": {"color": (100, 80, 60), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": "RPG"},
    "ammo_arrow": {"color": (140, 100, 60), "solid": False, "transparent": False, "hardness": 0.1, "ammo": True, "caliber": "arrow"},
    
    "attachment_scope_4x": {"color": (40, 40, 50), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "scope", "zoom": 4},
    "attachment_scope_8x": {"color": (30, 30, 40), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "scope", "zoom": 8},
    "attachment_scope_red_dot": {"color": (50, 50, 60), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "scope", "zoom": 1},
    "attachment_silencer": {"color": (35, 35, 35), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "silencer"},
    "attachment_extended_mag": {"color": (45, 45, 45), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "mag", "bonus": 20},
    "attachment_grip": {"color": (55, 55, 55), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "grip"},
    "attachment_laser": {"color": (60, 40, 40), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "laser"},
    "attachment_flashlight": {"color": (70, 70, 70), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "flashlight"},
    "attachment_bipod": {"color": (50, 50, 50), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "bipod"},
    "attachment_stock": {"color": (60, 50, 40), "solid": False, "transparent": False, "hardness": 0.1, "attachment": True, "type": "stock"}
}

class GameMap3D:
    def __init__(self):
        self.screen = None
        self.clock = None
        self.font_main = None
        self.font_small = None
        self.locations = []
        self.player_pos = [0, 0, 0]
        self.camera = {
            "x": 0,
            "y": 10,
            "z": 20,
            "pitch": -20,
            "yaw": 0,
            "speed": 0.5,
            "mode": "first"
        }
        self.mouse_sensitivity = 0.05
        self.is_mouse_locked = False
        self.followers = []
        self.follow_target = None
        self.message = None
        self.message_timer = 0
        self.velocity = [0, 0, 0]
        self.gravity = -0.35
        self.friction = 0.85
        self.npcs = []
        self.selected_npc = None
        self.npc_interaction_distance = 8
        self.large_structures = []
        self.render_cache = {}
        self.cache_valid = False
        self.selected_location = None
        self.owned_territories = []
        self.trees = []
        self.inventory = [None] * INVENTORY_SLOTS
        self.selected_slot = 0
        self.pickups = []
        self.block_world = {}
        self.minimap_enabled = True
        self.inventory_open = False
        self.tech_blocks = []
        self.energy_level = 100
        self.tech_mode = False
        self.teleporter_targets = []
        self.last_tech_interact = 0
        self.generals = []
        self.projectiles = []
        self.pets = []
        self.enemies = []
        self.player_health = 20
        self.player_max_health = 20
        self.has_saddle = False
        self.marketplace = []
        self.marketplace_timer = 0
        self.marketplace_refresh_interval = 300
        self.marketplace_open = False

    def initialize(self):
        if not opengl_available:
            print("错误: OpenGL不可用，无法启动3D地图")
            return False
        
        try:
            pygame.init()
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
            self.screen = pygame.display.get_surface()
            self.clock = pygame.time.Clock()
            
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glClearColor(0.1, 0.1, 0.2, 1.0)
            
            light_position = [1.0, 1.0, 1.0, 0.0]
            glLightfv(GL_LIGHT0, GL_POSITION, light_position)
            
            font_name = get_system_font_name()
            try:
                if font_name:
                    self.font_main = pygame.font.SysFont(font_name, 40)
                    self.font_small = pygame.font.SysFont(font_name, 24)
                else:
                    self.font_main = pygame.font.Font(None, 40)
                    self.font_small = pygame.font.Font(None, 24)
            except Exception:
                self.font_main = pygame.font.Font(None, 40)
                self.font_small = pygame.font.Font(None, 24)
            
            self.load_map_data()
            self.load_owned_territories()
            self.show_performance_warning()
            
            if self.locations:
                first_loc = self.locations[0]
                self.player_pos = [first_loc["x"] + 50, 2, first_loc["y"] + 50]
                self.update_camera()
            
            self.generate_trees()
            self.generate_tech_blocks()
            self.generate_large_structures()
            self.generate_npcs()
            self.cache_terrain()
            
            return True
        except Exception as e:
            print(f"初始化错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_performance_warning(self):
        warning = "3D主城 - 按右键与NPC交互 | E进入地点 | R收集资源"
        text_surf = self.font_main.render(warning, True, COLORS["accent_gold"])
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        bg_rect = pygame.Rect(text_rect.x-20, text_rect.y-10, text_rect.width+40, text_rect.height+20)
        pygame.draw.rect(self.screen, (30, 30, 55, 200), bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["accent_gold"], bg_rect, 2, border_radius=10)
        
        self.screen.blit(text_surf, text_rect)
        pygame.display.flip()
        pygame.time.wait(2000)
    
    def load_map_data(self):
        try:
            username = data.get("username", "")
            password = data.get("password", "")
            if not username or not password:
                print("错误: 未登录，无法加载地图数据")
                return
            
            map_path = self.get_map_data_path()
            if not os.path.exists(map_path):
                print("地图数据文件不存在，将生成新地图")
                self.locations = self.generate_locations(MAX_LOCATIONS)
                self.save_map_data(self.locations)
            else:
                with open(map_path, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                
                if map_data.get("username") != username:
                    print("错误: 地图数据与当前用户不匹配")
                    self.locations = self.generate_locations(MAX_LOCATIONS)
                    self.save_map_data(self.locations)
                    return
                
                version = map_data.get("version", "0.0")
                if version == "1.0":
                    blocks = map_data.get("blocks", [])
                    self.locations = []
                    for block in blocks:
                        loc = {
                            "x": block["x"],
                            "y": block["y"],
                            "type": block["type"],
                            "level": block.get("level", 1),
                            "power": block.get("power", 0),
                            "owner": block.get("owner", "neutral"),
                            "color": block.get("color", (0.5, 0.5, 0.5)),
                            "height": block.get("height", 8),
                            "rotation_id": block.get("rotation_id", 0),
                            "facing_id": block.get("facing_id", 0)
                        }
                        self.locations.append(loc)
                    
                    self.trees = []
                    for tree_data in map_data.get("trees", []):
                        self.trees.append((
                            tree_data["x"],
                            tree_data["y"],
                            tree_data.get("scale", 1.0)
                        ))
                    
                    self.large_structures = []
                    for struct_data in map_data.get("structures", []):
                        self.large_structures.append({
                            "x": struct_data["x"],
                            "z": struct_data["y"],
                            "name": struct_data["type"],
                            "size": struct_data.get("size", 20),
                            "height": struct_data.get("height", 15),
                            "color": (0.6, 0.5, 0.4)
                        })
                    
                    if map_data.get("player_pos"):
                        self.player_pos = map_data.get("player_pos", self.player_pos)
                    
                    if map_data.get("player_inventory"):
                        data["resources"] = map_data.get("player_inventory", {})
                    
                    print(f"成功加载地图数据v{version}，包含 {len(self.locations)} 个地点")
                else:
                    self.locations = map_data.get("locations", [])
                    print(f"成功加载地图数据v{version}，包含 {len(self.locations)} 个地点")
        except Exception as e:
            print(f"加载地图数据失败: {e}")
            self.locations = self.generate_locations(MAX_LOCATIONS)
            self.save_map_data(self.locations)
    
    def load_owned_territories(self):
        try:
            self.owned_territories = data.get('territory', {}).get('owned_territories', [])
            print(f"已加载 {len(self.owned_territories)} 个占领地点")
        except Exception as e:
            print(f"加载占领数据失败: {e}")
            self.owned_territories = []
    
    def get_map_data_path(self):
        username = data.get("username", "")
        safe_username = username.replace('\\', '_').replace('/', '_').replace(':', '_')
        return f"map_data_{safe_username}.json"
    
    def save_map_data(self, locations):
        try:
            username = data.get("username", "")
            if not username:
                return False
            
            blocks = []
            for loc in locations:
                block = {
                    "id": len(blocks) + 1,
                    "type": loc["type"],
                    "x": loc["x"],
                    "y": loc["y"],
                    "z": 0,
                    "level": loc.get("level", 1),
                    "power": loc.get("power", 0),
                    "owner": loc.get("owner", "neutral"),
                    "rotation_id": random.randint(0, 3),
                    "facing_id": self.calculate_facing_id(loc),
                    "color": loc.get("color", (0.5, 0.5, 0.5)),
                    "height": loc.get("height", 8)
                }
                blocks.append(block)
            
            trees = []
            for tree in self.trees:
                tree_block = {
                    "id": len(trees) + 1000,
                    "type": "tree",
                    "x": tree[0],
                    "y": tree[1],
                    "z": 0,
                    "scale": tree[2],
                    "rotation_id": random.randint(0, 3),
                    "facing_id": 0
                }
                trees.append(tree_block)
            
            structures = []
            for struct in self.large_structures:
                struct_block = {
                    "id": len(structures) + 2000,
                    "type": struct["name"],
                    "x": struct["x"],
                    "y": struct["z"],
                    "z": 0,
                    "size": struct["size"],
                    "height": struct["height"],
                    "rotation_id": random.randint(0, 3),
                    "facing_id": 0
                }
                structures.append(struct_block)
            
            map_data = {
                "version": "1.0",
                "username": username,
                "timestamp": time.time(),
                "blocks": blocks,
                "trees": trees,
                "structures": structures,
                "player_pos": self.player_pos,
                "player_inventory": data.get("resources", {})
            }
            
            map_path = self.get_map_data_path()
            with open(map_path, 'w', encoding='utf-8') as f:
                json.dump(map_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存地图数据失败: {e}")
            return False
    
    def calculate_facing_id(self, loc):
        camera_yaw = self.camera["yaw"]
        angle = math.atan2(
            loc["y"] - self.player_pos[2],
            loc["x"] - self.player_pos[0]
        )
        angle_deg = math.degrees(angle) - camera_yaw
        angle_deg = (angle_deg + 180) % 360 - 180
        
        if -45 <= angle_deg < 45:
            return 0
        elif 45 <= angle_deg < 135:
            return 1
        elif -135 <= angle_deg < -45:
            return 2
        else:
            return 3
    
    def generate_locations(self, count):
        locations = []
        LOCATION_TYPES = {
            "矿产": {"power": 80, "color": (0.7, 0.7, 0.75), "height": 8},
            "农田": {"power": 50, "color": (0.4, 0.8, 0.4), "height": 5},
            "煤矿": {"power": 70, "color": (0.3, 0.3, 0.35), "height": 6},
            "水井": {"power": 40, "color": (0.3, 0.6, 0.9), "height": 4},
            "敌对单位": {"power": 120, "color": (0.9, 0.3, 0.3), "height": 10}
        }
        
        for i in range(count):
            while True:
                x = random.randint(100, MAP_SIZE[0] - 100)
                y = random.randint(100, MAP_SIZE[1] - 100)
                
                valid = True
                for loc in locations:
                    distance = math.hypot(x - loc["x"], y - loc["y"])
                    if distance < 150:
                        valid = False
                        break
                if valid:
                    break
            
            loc_type = random.choice(list(LOCATION_TYPES.keys()))
            level = random.randint(1, 10)
            power = int(LOCATION_TYPES[loc_type]["power"] * (0.5 + level * 0.1))
            
            is_owned = loc_type != "敌对单位" and random.random() < 0.2
            
            locations.append({
                "x": x,
                "y": y,
                "type": loc_type,
                "level": level,
                "power": power,
                "owner": "player" if is_owned else "enemy" if loc_type == "敌对单位" else "neutral",
                "color": LOCATION_TYPES[loc_type]["color"],
                "height": LOCATION_TYPES[loc_type]["height"]
            })
        
        return locations
    
    def generate_trees(self):
        self.trees = []
        tree_count = 300
        
        for _ in range(tree_count):
            x = random.randint(-1800, 1800)
            z = random.randint(-1800, 1800)
            
            too_close = False
            for loc in self.locations:
                if math.hypot(x - loc["x"], z - loc["y"]) < 40:
                    too_close = True
                    break
            for tree in self.trees:
                if math.hypot(x - tree[0], z - tree[1]) < 8:
                    too_close = True
                    break
            
            if not too_close:
                self.trees.append((x, z, random.uniform(0.8, 1.5)))
    
    def generate_tech_blocks(self):
        self.tech_blocks = []
        tech_block_names = [
            "tech_machine_frame", "tech_energy_core", "tech_generator",
            "tech_solar_panel", "tech_quantum_storage", "tech_nano_assembler",
            "tech_circuit_board", "tech_fusion_core", "tech_autominer",
            "tech_fabricator", "tech_energy_cable", "tech_laser_node"
        ]
        
        for _ in range(40):
            while True:
                x = random.randint(-1200, 1200)
                z = random.randint(-1200, 1200)
                
                too_close = False
                for loc in self.locations:
                    if math.hypot(x - loc["x"], z - loc["y"]) < 60:
                        too_close = True
                        break
                for tb in self.tech_blocks:
                    if math.hypot(x - tb["x"], z - tb["z"]) < 30:
                        too_close = True
                        break
                
                if not too_close:
                    break
            
            tech_type = random.choice(tech_block_names)
            self.tech_blocks.append({
                "x": x,
                "z": z,
                "type": tech_type,
                "rotation": random.randint(0, 3),
                "active": random.random() < 0.7,
                "energy": random.randint(50, 200)
            })
    
    def generate_large_structures(self):
        self.large_structures = []
        
        STRUCTURE_TYPES = [
            {"name": "皇宫", "size": 30, "height": 25, "color": (0.8, 0.7, 0.2), "icon": "🏛️"},
            {"name": "城墙", "size": 60, "height": 12, "color": (0.5, 0.5, 0.5), "icon": "🧱"},
            {"name": "塔楼", "size": 15, "height": 30, "color": (0.6, 0.5, 0.4), "icon": "🗼"},
            {"name": "神庙", "size": 20, "height": 18, "color": (0.7, 0.6, 0.5), "icon": "⛩️"},
            {"name": "仓库", "size": 25, "height": 10, "color": (0.6, 0.4, 0.3), "icon": "🏭"}
        ]
        
        for _ in range(8):
            while True:
                x = random.randint(-1500, 1500)
                z = random.randint(-1500, 1500)
                
                too_close = False
                for struct in self.large_structures:
                    if math.hypot(x - struct["x"], z - struct["z"]) < 200:
                        too_close = True
                        break
                if not too_close:
                    break
            
            struct_type = random.choice(STRUCTURE_TYPES)
            self.large_structures.append({
                "x": x,
                "z": z,
                **struct_type
            })
    
    def generate_npcs(self):
        self.npcs = []
        
        NPC_TYPES = [
            {"name": "武将招募官", "dialogue": "欢迎来到主城！需要招募武将吗？", "action": "hero_recruit", "module": "hero_recruitment.py", "color": (0.2, 0.6, 0.8)},
            {"name": "商人", "dialogue": "欢迎光临！我这里有各种珍贵物品。", "action": "shop", "module": "shop_system.py", "color": (0.8, 0.6, 0.2)},
            {"name": "任务发布者", "dialogue": "勇士，我有一个危险的任务...", "action": "quest", "module": "quest_system.py", "color": (0.6, 0.3, 0.8)},
            {"name": "铁匠", "dialogue": "需要打造或强化装备吗？", "action": "equipment", "module": "equipment_system.py", "color": (0.5, 0.5, 0.5)},
            {"name": "药师", "dialogue": "我可以帮你炼制药剂。", "action": "alchemy", "module": "alchemy_system.py", "color": (0.3, 0.7, 0.3)},
            {"name": "史官", "dialogue": "想听三国的故事吗？", "action": "story", "module": "background_story.py", "color": (0.7, 0.5, 0.3)},
            {"name": "军需官", "dialogue": "需要补给吗？金元宝、时间卡应有尽有！", "action": "resources", "module": "shop_system.py", "color": (0.2, 0.5, 0.8)},
            {"name": "竞技场管理员", "dialogue": "想参加PVP竞技吗？", "action": "pvp", "module": "pvp_p2p.py", "color": (0.8, 0.3, 0.3)}
        ]
        
        for npc_type in NPC_TYPES:
            while True:
                x = random.randint(-500, 500)
                z = random.randint(-500, 500)
                
                too_close = False
                for npc in self.npcs:
                    if math.hypot(x - npc["x"], z - npc["z"]) < 50:
                        too_close = True
                        break
                if not too_close:
                    break
            
            self.npcs.append({
                "x": x,
                "z": z,
                "y": 0,
                **npc_type,
                "animation_offset": random.uniform(0, math.pi * 2),
                "move_dir": random.uniform(0, math.pi * 2),
                "move_speed": random.uniform(0.3, 0.8),
                "original_x": x,
                "original_z": z,
                "wander_range": 15
            })
    
    def cache_terrain(self):
        self.render_cache = {
            "trees": [],
            "locations": [],
            "structures": [],
            "npcs": []
        }
        
        for tree in self.trees:
            x, z, scale = tree
            self.render_cache["trees"].append({
                "x": x,
                "z": z,
                "scale": scale
            })
        
        for loc in self.locations:
            self.render_cache["locations"].append({
                "x": loc["x"],
                "y": loc["y"],
                "type": loc["type"],
                "color": loc["color"],
                "owner": loc["owner"],
                "level": loc["level"]
            })
        
        for struct in self.large_structures:
            self.render_cache["structures"].append({
                "x": struct["x"],
                "z": struct["z"],
                "size": struct["size"],
                "height": struct["height"],
                "color": struct["color"],
                "name": struct["name"]
            })
        
        self.cache_valid = True
        print("地形缓存已生成")
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        move_speed = self.camera["speed"] * (0.4 if keys[pygame.K_LSHIFT] else 1.0)
        
        if keys[pygame.K_w]:
            self.move_forward(move_speed)
        if keys[pygame.K_s]:
            self.move_backward(move_speed)
        if keys[pygame.K_a]:
            self.move_left(move_speed)
        if keys[pygame.K_d]:
            self.move_right(move_speed)
        if keys[pygame.K_SPACE]:
            if self.player_pos[1] <= 0.5:
                self.velocity[1] = 6.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.is_mouse_locked:
                        self.is_mouse_locked = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        return False
                elif event.key == pygame.K_TAB:
                    self.is_mouse_locked = not self.is_mouse_locked
                    pygame.mouse.set_visible(not self.is_mouse_locked)
                    pygame.event.set_grab(self.is_mouse_locked)
                elif event.key == pygame.K_f:
                    if self.follow_target:
                        self.follow_target = None
                        self.message = "取消跟随"
                    else:
                        if self.locations:
                            closest_loc = min(self.locations, key=lambda loc: math.hypot(loc["x"] - self.player_pos[0], loc["y"] - self.player_pos[2]))
                            self.follow_target = closest_loc
                            self.message = f"开始跟随: {closest_loc['type']}"
                        else:
                            self.message = "没有可跟随的地点"
                    self.message_timer = 2000
                elif event.key == pygame.K_F5:
                    self.camera["mode"] = "third" if self.camera["mode"] == "first" else "first"
                    self.message = f"切换到{'第三人称' if self.camera['mode'] == 'third' else '第一人称'}视角"
                    self.message_timer = 2000
                elif event.key == pygame.K_m:
                    self.minimap_enabled = not self.minimap_enabled
                    self.message = f"小地图: {'开启' if self.minimap_enabled else '关闭'}"
                    self.message_timer = 2000
                elif event.key == pygame.K_i:
                    self.inventory_open = not self.inventory_open
                    if self.inventory_open:
                        self.is_mouse_locked = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    elif not self.inventory_open:
                        self.is_mouse_locked = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                elif self.inventory_open:
                    if event.key == pygame.K_1:
                        self.selected_slot = 0
                    elif event.key == pygame.K_2:
                        self.selected_slot = 1
                    elif event.key == pygame.K_3:
                        self.selected_slot = 2
                    elif event.key == pygame.K_4:
                        self.selected_slot = 3
                    elif event.key == pygame.K_5:
                        self.selected_slot = 4
                    elif event.key == pygame.K_6:
                        self.selected_slot = 5
                    elif event.key == pygame.K_7:
                        self.selected_slot = 6
                    elif event.key == pygame.K_8:
                        self.selected_slot = 7
                    elif event.key == pygame.K_9:
                        self.selected_slot = 8
                elif event.key == pygame.K_e:
                    self.check_location_interaction()
                elif event.key == pygame.K_r:
                    self.collect_nearby_resources()
                elif event.key == pygame.K_q:
                    if not self.equip_general_weapon():
                        self.message = "附近没有可装备武器的武将"
                        self.message_timer = 2000
                elif event.key == pygame.K_t:
                    self.marketplace_open = not self.marketplace_open
                    if self.marketplace_open:
                        if not self.marketplace:
                            self.refresh_marketplace()
                        self.is_mouse_locked = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        self.is_mouse_locked = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.inventory_open:
                        mouse_pos = pygame.mouse.get_pos()
                        self.handle_inventory_click(mouse_pos)
                    elif not self.is_mouse_locked:
                        self.is_mouse_locked = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self.message = "鼠标已锁定，按Tab键解锁"
                        self.message_timer = 3000
                    else:
                        if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                            self.try_place_block()
                        else:
                            self.try_mine_block()
                elif event.button == 3:
                    if not self.inventory_open:
                        selected_item = self.inventory[self.selected_slot]
                        if selected_item and self.can_use_item(selected_item["item"]):
                            self.use_item(selected_item)
                        elif not self.check_tech_interaction():
                            if not self.check_npc_interaction():
                                self.try_interact_block()
                elif event.button == 4:
                    self.selected_slot = (self.selected_slot - 1) % 9
                elif event.button == 5:
                    self.selected_slot = (self.selected_slot + 1) % 9
            elif event.type == pygame.MOUSEMOTION:
                if self.is_mouse_locked:
                    rel_x, rel_y = event.rel
                    self.camera["yaw"] += rel_x * self.mouse_sensitivity
                    self.camera["pitch"] -= rel_y * self.mouse_sensitivity
                    self.camera["pitch"] = max(-89, min(89, self.camera["pitch"]))
        
        return True
    
    def can_use_item(self, item_name):
        weapon_items = ["bow", "crossbow", "trident"]
        gun_items = ["gun_ak47", "gun_m4a1", "gun_awp", "gun_mp5", "gun_m1911", "gun_glock",
                    "gun_scarh", "gun_p90", "gun_uzi", "gun_deserteagle", "gun_barrett", "gun_rpg"]
        food_items = [
            "apple", "bread", "cooked_beef", "raw_beef", "cooked_chicken", "raw_chicken",
            "cooked_mutton", "raw_mutton", "cooked_porkchop", "raw_porkchop",
            "cooked_rabbit", "raw_rabbit", "cooked_cod", "raw_cod", "cooked_salmon", "raw_salmon",
            "pumpkin_pie", "cake", "cookie", "melon_slice", "carrot", "golden_carrot",
            "potato", "baked_potato", "beetroot", "sweet_berries", "glow_berries",
            "chorus_fruit", "rabbit_stew", "mushroom_stew", "beetroot_soup", "suspicious_stew"
        ]
        pet_items = ["oak_boat", "saddle", "horse_armor_leather", "horse_armor_iron", 
                    "horse_armor_gold", "horse_armor_diamond"]
        potion_items = ["enchanted_golden_apple", "golden_apple"]
        
        if item_name in weapon_items:
            return True
        if item_name in gun_items:
            return True
        if item_name in food_items:
            return True
        if item_name in pet_items:
            return True
        if item_name in potion_items:
            return True
        if item_name.startswith("pet_"):
            return True
        if item_name.startswith("武将卡_") or item_name.startswith("general_"):
            return True
        if item_name in ["diamond_sword", "iron_sword", "stone_sword", "wooden_sword", "netherite_sword"]:
            return True
        if item_name.startswith("attachment_"):
            return True
        
        return False
    
    def use_item(self, item):
        item_name = item["item"]
        
        weapon_items = ["bow", "crossbow", "trident"]
        gun_items = ["gun_ak47", "gun_m4a1", "gun_awp", "gun_mp5", "gun_m1911", "gun_glock",
                    "gun_scarh", "gun_p90", "gun_uzi", "gun_deserteagle", "gun_barrett", "gun_rpg"]
        
        if item_name in weapon_items:
            self.shoot_projectile(item_name)
            return
        
        if item_name in gun_items:
            self.shoot_gun(item_name)
            return
        
        if item_name.startswith("attachment_"):
            self.attach_attachment(item_name)
            return
        
        food_items = [
            "apple", "bread", "cooked_beef", "raw_beef", "cooked_chicken", "raw_chicken",
            "cooked_mutton", "raw_mutton", "cooked_porkchop", "raw_porkchop",
            "cooked_rabbit", "raw_rabbit", "cooked_cod", "raw_cod", "cooked_salmon", "raw_salmon",
            "pumpkin_pie", "cake", "cookie", "melon_slice", "carrot", "golden_carrot",
            "potato", "baked_potato", "beetroot", "sweet_berries", "glow_berries",
            "chorus_fruit", "rabbit_stew", "mushroom_stew", "beetroot_soup", "suspicious_stew"
        ]
        if item_name in food_items:
            self.eat_food(item)
            return
        
        potion_items = ["enchanted_golden_apple", "golden_apple"]
        if item_name in potion_items:
            self.drink_potion(item)
            return
        
        if item_name.startswith("pet_"):
            self.summon_pet(item_name)
            return
        
        if item_name.startswith("武将卡_") or item_name.startswith("general_"):
            self.summon_general(item_name)
            return
        
        if item_name in ["diamond_sword", "iron_sword", "stone_sword", "wooden_sword", "netherite_sword"]:
            self.swing_sword(item)
            return
        
        if item_name == "saddle":
            self.equip_saddle()
            return
    
    def shoot_projectile(self, weapon_type):
        if not hasattr(self, 'last_shot_time'):
            self.last_shot_time = 0
        
        current_time = time.time()
        if current_time - self.last_shot_time < 0.5:
            return
        
        self.last_shot_time = current_time
        
        yaw_rad = math.radians(self.camera["yaw"])
        pitch_rad = math.radians(self.camera["pitch"])
        
        if weapon_type == "bow":
            projectile = {
                "type": "arrow",
                "x": self.player_pos[0],
                "y": self.player_pos[1] + 1.5,
                "z": self.player_pos[2],
                "velocity": [
                    math.cos(yaw_rad) * math.cos(pitch_rad) * 1.5,
                    math.sin(pitch_rad) * 1.5,
                    math.sin(yaw_rad) * math.cos(pitch_rad) * 1.5
                ],
                "lifetime": 200
            }
            self.message = "🏹 射出一支箭！"
        elif weapon_type == "crossbow":
            projectile = {
                "type": "bolt",
                "x": self.player_pos[0],
                "y": self.player_pos[1] + 1.5,
                "z": self.player_pos[2],
                "velocity": [
                    math.cos(yaw_rad) * math.cos(pitch_rad) * 2.0,
                    math.sin(pitch_rad) * 2.0,
                    math.sin(yaw_rad) * math.cos(pitch_rad) * 2.0
                ],
                "lifetime": 150
            }
            self.message = "⚔️ 射出一支弩箭！"
        elif weapon_type == "trident":
            projectile = {
                "type": "trident",
                "x": self.player_pos[0],
                "y": self.player_pos[1] + 1.5,
                "z": self.player_pos[2],
                "velocity": [
                    math.cos(yaw_rad) * math.cos(pitch_rad) * 1.8,
                    math.sin(pitch_rad) * 1.8,
                    math.sin(yaw_rad) * math.cos(pitch_rad) * 1.8
                ],
                "lifetime": 180
            }
            self.message = "🔱 投出三叉戟！"
        
        self.projectiles.append(projectile)
        self.message_timer = 2000
    
    def shoot_gun(self, gun_type):
        if not hasattr(self, 'last_gun_shot_time'):
            self.last_gun_shot_time = 0
        
        current_time = time.time()
        gun_data = MC_BLOCKS.get(gun_type, {})
        fire_rate = gun_data.get("fire_rate", 0.2)
        
        if current_time - self.last_gun_shot_time < fire_rate:
            return
        
        self.last_gun_shot_time = current_time
        
        ammo_type = gun_data.get("ammo_type", "ammo_9mm")
        damage = gun_data.get("damage", 15)
        
        has_ammo = False
        for i, inv_item in enumerate(self.inventory):
            if inv_item and inv_item["item"] == ammo_type:
                has_ammo = True
                if inv_item["count"] > 1:
                    self.inventory[i]["count"] -= 1
                else:
                    self.inventory[i] = None
                break
        
        if not has_ammo:
            self.message = "⚠️ 没有弹药！需要 " + ammo_type
            self.message_timer = 2000
            return
        
        yaw_rad = math.radians(self.camera["yaw"])
        pitch_rad = math.radians(self.camera["pitch"])
        
        speed = 3.0
        if gun_type in ["gun_awp", "gun_barrett"]:
            speed = 5.0
        elif gun_type in ["gun_mp5", "gun_p90", "gun_uzi"]:
            speed = 2.5
        
        projectile = {
            "type": "bullet",
            "x": self.player_pos[0],
            "y": self.player_pos[1] + 1.5,
            "z": self.player_pos[2],
            "velocity": [
                math.cos(yaw_rad) * math.cos(pitch_rad) * speed,
                math.sin(pitch_rad) * speed,
                math.sin(yaw_rad) * math.cos(pitch_rad) * speed
            ],
            "lifetime": 100,
            "damage": damage
        }
        
        self.projectiles.append(projectile)
        
        gun_names = {
            "gun_ak47": "AK-47", "gun_m4a1": "M4A1", "gun_awp": "AWP",
            "gun_mp5": "MP5", "gun_m1911": "M1911", "gun_glock": "Glock",
            "gun_scarh": "SCAR-H", "gun_p90": "P90", "gun_uzi": "Uzi",
            "gun_deserteagle": "沙漠之鹰", "gun_barrett": "巴雷特", "gun_rpg": "RPG"
        }
        gun_name = gun_names.get(gun_type, gun_type)
        self.message = f"🔫 {gun_name} 开火！伤害:{damage}"
        self.message_timer = 1500
    
    def attach_attachment(self, attachment_type):
        selected_item = self.inventory[self.selected_slot]
        if not selected_item:
            self.message = "⚠️ 请先选择一把枪械"
            self.message_timer = 2000
            return
        
        gun_items = ["gun_ak47", "gun_m4a1", "gun_awp", "gun_mp5", "gun_m1911", "gun_glock",
                    "gun_scarh", "gun_p90", "gun_uzi", "gun_deserteagle", "gun_barrett", "gun_rpg"]
        
        if selected_item["item"] not in gun_items:
            self.message = "⚠️ 只能给枪械装备配件"
            self.message_timer = 2000
            return
        
        if "attachments" not in selected_item:
            selected_item["attachments"] = []
        
        attachment_data = MC_BLOCKS.get(attachment_type, {})
        attachment_type_str = attachment_data.get("type", "unknown")
        
        for existing in selected_item["attachments"]:
            if existing.get("type") == attachment_type_str:
                self.message = f"⚠️ 已经装备了{attachment_type_str}类型配件"
                self.message_timer = 2000
                return
        
        selected_item["attachments"].append({
            "item": attachment_type,
            "type": attachment_type_str,
            "zoom": attachment_data.get("zoom", 0),
            "bonus": attachment_data.get("bonus", 0)
        })
        
        for i, inv_item in enumerate(self.inventory):
            if inv_item and inv_item["item"] == attachment_type:
                if inv_item["count"] > 1:
                    self.inventory[i]["count"] -= 1
                else:
                    self.inventory[i] = None
                break
        
        attachment_names = {
            "attachment_scope_4x": "4倍镜", "attachment_scope_8x": "8倍镜",
            "attachment_scope_red_dot": "红点瞄准镜", "attachment_silencer": "消音器",
            "attachment_extended_mag": "扩容弹匣", "attachment_grip": "握把",
            "attachment_laser": "激光瞄准器", "attachment_flashlight": "战术手电",
            "attachment_bipod": "两脚架", "attachment_stock": "枪托"
        }
        att_name = attachment_names.get(attachment_type, attachment_type)
        self.message = f"🔧 已装备配件: {att_name}"
        self.message_timer = 2000
    
    def eat_food(self, item):
        food_values = {
            "apple": 4, "bread": 5, "cooked_beef": 8, "raw_beef": 3,
            "cooked_chicken": 6, "raw_chicken": 2, "cooked_mutton": 8, "raw_mutton": 2,
            "cooked_porkchop": 8, "raw_porkchop": 3, "cooked_rabbit": 5, "raw_rabbit": 3,
            "cooked_cod": 5, "raw_cod": 2, "cooked_salmon": 6, "raw_salmon": 2,
            "pumpkin_pie": 8, "cake": 14, "cookie": 2, "melon_slice": 2,
            "carrot": 4, "golden_carrot": 10, "potato": 1, "baked_potato": 5,
            "beetroot": 2, "sweet_berries": 2, "glow_berries": 4,
            "chorus_fruit": 4, "rabbit_stew": 10, "mushroom_stew": 6,
            "beetroot_soup": 6, "suspicious_stew": 6
        }
        
        food_value = food_values.get(item["item"], 2)
        
        if not hasattr(self, 'player_health'):
            self.player_health = 20
        if not hasattr(self, 'player_max_health'):
            self.player_max_health = 20
        
        self.player_health = min(self.player_health + food_value, self.player_max_health)
        
        if item["count"] > 1:
            self.inventory[self.selected_slot]["count"] -= 1
        else:
            self.inventory[self.selected_slot] = None
        
        food_names = {
            "apple": "苹果", "bread": "面包", "cooked_beef": "熟牛肉", "cooked_chicken": "熟鸡肉",
            "pumpkin_pie": "南瓜派", "cake": "蛋糕", "golden_carrot": "金胡萝卜",
            "baked_potato": "烤土豆"
        }
        food_name = food_names.get(item["item"], item["item"])
        self.message = f"🍖 食用{food_name}，恢复{food_value}点生命！"
        self.message_timer = 2000
    
    def drink_potion(self, item):
        if item["item"] == "golden_apple":
            heal_amount = 4
            self.message = "🍎 食用金苹果，附有微弱治疗效果！"
        else:
            heal_amount = 8
            self.message = "✨ 食用附魔金苹果，获得生命恢复效果！"
        
        if not hasattr(self, 'player_health'):
            self.player_health = 20
        if not hasattr(self, 'player_max_health'):
            self.player_max_health = 20
        
        self.player_health = min(self.player_health + heal_amount, self.player_max_health)
        
        if item["count"] > 1:
            self.inventory[self.selected_slot]["count"] -= 1
        else:
            self.inventory[self.selected_slot] = None
        self.message_timer = 2000
    
    def equip_general_weapon(self):
        selected_item = self.inventory[self.selected_slot]
        if not selected_item:
            return False
        
        item_name = selected_item["item"]
        weapon_types = ["bow", "crossbow", "trident", "diamond_sword", "iron_sword", "stone_sword", "wooden_sword", "netherite_sword"]
        
        if item_name not in weapon_types:
            return False
        
        for general in self.generals:
            distance = math.hypot(
                general["x"] - self.player_pos[0],
                general["z"] - self.player_pos[2]
            )
            if distance < 5:
                general["weapon"] = item_name
                
                if selected_item["count"] > 1:
                    self.inventory[self.selected_slot]["count"] -= 1
                else:
                    self.inventory[self.selected_slot] = None
                
                weapon_names = {
                    "bow": "弓", "crossbow": "弩", "trident": "三叉戟",
                    "diamond_sword": "钻石剑", "iron_sword": "铁剑",
                    "stone_sword": "石剑", "wooden_sword": "木剑", "netherite_sword": "下界合金剑"
                }
                weapon_name = weapon_names.get(item_name, item_name)
                self.message = f"⚔️ {general['name']} 装备了{weapon_name}！"
                self.message_timer = 3000
                return True
        
        return False
    
    def swing_sword(self, item):
        self.message = "⚔️ 挥剑攻击！"
        self.message_timer = 1500
        
        sword_range = 4.0
        hit_entities = []
        
        for npc in self.npcs[:]:
            distance = math.hypot(
                npc["x"] - self.player_pos[0],
                npc["z"] - self.player_pos[2]
            )
            if distance <= sword_range:
                hit_entities.append(("npc", npc))
        
        for general in self.generals[:]:
            distance = math.hypot(
                general["x"] - self.player_pos[0],
                general["z"] - self.player_pos[2]
            )
            if distance <= sword_range:
                hit_entities.append(("general", general))
        
        for enemy in self.enemies[:]:
            distance = math.hypot(
                enemy["x"] - self.player_pos[0],
                enemy["z"] - self.player_pos[2]
            )
            if distance <= sword_range:
                hit_entities.append(("enemy", enemy))
        
        for entity_type, entity in hit_entities:
            if entity_type == "npc":
                entity["health"] = entity.get("health", 20) - 5
            elif entity_type == "general":
                entity["hp"] = entity.get("hp", 100) - 5
            elif entity_type == "enemy":
                entity["health"] = entity.get("health", 20) - 10
                if entity["health"] <= 0:
                    self.enemies.remove(entity)
                    self.spawn_loot(entity["x"], entity["z"])
    
    def summon_pet(self, pet_type):
        yaw_rad = math.radians(self.camera["yaw"])
        spawn_distance = 2.0
        spawn_x = self.player_pos[0] + math.cos(yaw_rad) * spawn_distance
        spawn_z = self.player_pos[2] + math.sin(yaw_rad) * spawn_distance
        
        pet_data = self.get_pet_data(pet_type)
        pet = {
            "type": "pet",
            "name": pet_data["name"],
            "x": spawn_x,
            "y": 0,
            "z": spawn_z,
            "health": pet_data["health"],
            "max_health": pet_data["health"],
            "damage": pet_data["damage"],
            "color": pet_data["color"],
            "size": pet_data["size"],
            "following": True
        }
        
        self.pets.append(pet)
        
        if self.inventory[self.selected_slot]["count"] > 1:
            self.inventory[self.selected_slot]["count"] -= 1
        else:
            self.inventory[self.selected_slot] = None
        
        self.message = f"🐾 召唤宠物: {pet_data['name']}！"
        self.message_timer = 3000
    
    def get_pet_data(self, pet_type):
        pet_database = {
            "pet_wolf": {"name": "狼", "health": 20, "damage": 5, "color": (0.5, 0.5, 0.5), "size": 1.2},
            "pet_cat": {"name": "猫", "health": 10, "damage": 2, "color": (0.8, 0.6, 0.4), "size": 0.8},
            "pet_horse": {"name": "马", "health": 30, "damage": 3, "color": (0.6, 0.4, 0.2), "size": 1.5},
            "pet_pig": {"name": "猪", "health": 10, "damage": 1, "color": (0.9, 0.7, 0.7), "size": 1.0},
            "pet_cow": {"name": "牛", "health": 20, "damage": 2, "color": (0.4, 0.3, 0.3), "size": 1.3},
            "pet_sheep": {"name": "羊", "health": 10, "damage": 1, "color": (0.9, 0.9, 0.9), "size": 1.1},
            "pet_chicken": {"name": "鸡", "health": 4, "damage": 0, "color": (0.9, 0.8, 0.6), "size": 0.6},
            "pet_rabbit": {"name": "兔子", "health": 3, "damage": 0, "color": (0.8, 0.7, 0.6), "size": 0.5}
        }
        return pet_database.get(pet_type, {"name": "未知宠物", "health": 10, "damage": 2, "color": (0.5, 0.5, 0.5), "size": 1.0})
    
    def equip_saddle(self):
        self.has_saddle = True
        if self.inventory[self.selected_slot]["count"] > 1:
            self.inventory[self.selected_slot]["count"] -= 1
        else:
            self.inventory[self.selected_slot] = None
        self.message = "🫏 装备马鞍成功！可以骑乘马匹了！"
        self.message_timer = 2000
    
    def try_mine_block(self):
        selected_item = self.inventory[self.selected_slot]
        if not selected_item:
            return
        
        item_name = selected_item["item"]
        
        if item_name in ["wooden_pickaxe", "stone_pickaxe", "iron_pickaxe", "diamond_pickaxe", "netherite_pickaxe"]:
            self.mine_with_pickaxe(selected_item)
        elif item_name in ["wooden_shovel", "stone_shovel", "iron_shovel", "diamond_shovel", "netherite_shovel"]:
            self.mine_with_shovel(selected_item)
        elif item_name in ["wooden_axe", "stone_axe", "iron_axe", "diamond_axe", "netherite_axe"]:
            self.mine_with_axe(selected_item)
        else:
            self.mine_with_hand(selected_item)
    
    def mine_with_hand(self, item):
        self.message = "空手无法破坏方块"
        self.message_timer = 1500
    
    def mine_with_pickaxe(self, item):
        self.message = "⛏️ 正在挖掘..."
        self.message_timer = 1000
        tool_tiers = {
            "wooden_pickaxe": 1.0,
            "stone_pickaxe": 1.5,
            "iron_pickaxe": 2.0,
            "diamond_pickaxe": 2.5,
            "netherite_pickaxe": 3.0
        }
        efficiency = tool_tiers.get(item["item"], 1.0)
        self.message = f"⛏️ 效率 {efficiency}x"
    
    def mine_with_shovel(self, item):
        self.message = "🔨 正在铲..."
        self.message_timer = 1000
    
    def mine_with_axe(self, item):
        self.message = "🪓 正在砍..."
        self.message_timer = 1000
    
    def try_place_block(self):
        selected_item = self.inventory[self.selected_slot]
        if not selected_item:
            return
        
        item_name = selected_item["item"]
        
        if item_name in MC_BLOCKS:
            block_data = MC_BLOCKS[item_name]
            if block_data.get("solid", True):
                yaw_rad = math.radians(self.camera["yaw"])
                place_distance = 4.0
                place_x = self.player_pos[0] + math.cos(yaw_rad) * place_distance
                place_z = self.player_pos[2] + math.sin(yaw_rad) * place_distance
                place_y = self.player_pos[1] - 1.0
                
                if self.inventory[self.selected_slot]["count"] > 1:
                    self.inventory[self.selected_slot]["count"] -= 1
                else:
                    self.inventory[self.selected_slot] = None
                
                self.spawn_pickup(item_name, place_x, place_z, 1)
                self.message = f"放置: {item_name}"
                self.message_timer = 1500
            else:
                self.message = "无法放置透明方块"
                self.message_timer = 1500
        else:
                if item_name.startswith("武将卡_") or item_name.startswith("general_"):
                    self.summon_general(item_name)
                else:
                    self.message = "无法放置该物品"
                    self.message_timer = 1500
    
    def try_interact_block(self):
        yaw_rad = math.radians(self.camera["yaw"])
        interact_distance = 5.0
        target_x = self.player_pos[0] + math.cos(yaw_rad) * interact_distance
        target_z = self.player_pos[2] + math.sin(yaw_rad) * interact_distance
        
        for tech_block in self.tech_blocks:
            if math.hypot(tech_block["x"] - target_x, tech_block["z"] - target_z) < 3:
                self.check_tech_interaction()
                return
        
        self.try_pickup_item()
    
    def summon_general(self, card_name):
        general_data = self.get_general_from_card(card_name)
        if not general_data:
            self.message = "无效的武将卡"
            self.message_timer = 2000
            return
        
        yaw_rad = math.radians(self.camera["yaw"])
        spawn_distance = 3.0
        spawn_x = self.player_pos[0] + math.cos(yaw_rad) * spawn_distance
        spawn_z = self.player_pos[2] + math.sin(yaw_rad) * spawn_distance
        
        general = {
            "type": "general",
            "name": general_data["name"],
            "x": spawn_x,
            "z": spawn_z,
            "level": general_data.get("level", 1),
            "power": general_data.get("power", 100),
            "hp": general_data.get("hp", 100),
            "max_hp": general_data.get("hp", 100),
            "equipment": general_data.get("equipment", {}),
            "skills": general_data.get("skills", []),
            "color": (0.8, 0.6, 0.2)
        }
        
        self.generals.append(general)
        
        self.inventory[self.selected_slot] = None
        
        self.message = f"⚔️ 召唤武将: {general_data['name']}"
        self.message_timer = 3000
    
    def get_general_from_card(self, card_name):
        generals_db = data.get("generals", {})
        
        if card_name.startswith("武将卡_"):
            general_id = card_name.replace("武将卡_", "")
        else:
            general_id = card_name.replace("general_", "")
        
        for general_id_key, general_data in generals_db.items():
            if general_id_key == general_id or general_data.get("name", "").replace(" ", "_") == general_id:
                return general_data
        
        return {
            "name": general_id.replace("_", " ").title(),
            "level": 1,
            "power": 100,
            "hp": 100,
            "equipment": {},
            "skills": ["攻击", "防御"]
        }
    
    def check_tech_interaction(self):
        current_time = time.time()
        if current_time - self.last_tech_interact < 0.5:
            return False
        
        for tech_block in self.tech_blocks:
            distance = math.hypot(
                tech_block["x"] - self.player_pos[0],
                tech_block["z"] - self.player_pos[2]
            )
            if distance < 5:
                self.last_tech_interact = current_time
                tech_type = tech_block["type"]
                tech_block["active"] = not tech_block.get("active", True)
                
                messages = {
                    "tech_energy_core": "⚡ 能量核心已" + ("激活" if tech_block["active"] else "关闭"),
                    "tech_generator": "🔋 发电机已" + ("启动" if tech_block["active"] else "停止"),
                    "tech_matter_transporter": "🌀 物质传输器已" + ("激活" if tech_block["active"] else "关闭"),
                    "tech_laser_node": "💥 激光节点已" + ("激活" if tech_block["active"] else "关闭"),
                    "tech_quantum_storage": "💎 量子存储已" + ("激活" if tech_block["active"] else "关闭"),
                    "tech_fusion_core": "☀️ 聚变核心已" + ("激活" if tech_block["active"] else "关闭"),
                    "tech_teleporter": "🌟 传送门已" + ("激活" if tech_block["active"] else "关闭"),
                    "tech_hologram_projector": "🎭 全息投影仪已" + ("激活" if tech_block["active"] else "关闭"),
                }
                
                self.message = messages.get(tech_type, "✨ 科技方块已" + ("激活" if tech_block["active"] else "关闭"))
                self.message_timer = 2000
                
                if tech_block["active"] and random.random() < 0.4:
                    drop_items = ["gold_ingot", "iron_ingot", "diamond", "tech_advanced_chip", "tech_circuit_board"]
                    drop_item = random.choice(drop_items)
                    self.spawn_pickup(drop_item, tech_block["x"], tech_block["z"], 1)
                
                if tech_type == "tech_teleporter" and tech_block["active"]:
                    if self.teleporter_targets:
                        target = random.choice(self.teleporter_targets)
                        self.player_pos = [target["x"], 2, target["z"]]
                        self.message = "✨ 传送完成！"
                    else:
                        self.teleporter_targets.append({
                            "x": tech_block["x"],
                            "z": tech_block["z"]
                        })
                        self.message = "🎯 传送目标已设置！"
                
                return True
        return False
    
    def try_pickup_item(self):
        for pickup in self.pickups[:]:
            distance = math.hypot(
                pickup["x"] - self.player_pos[0],
                pickup["y"] - self.player_pos[2]
            )
            if distance <= MAX_PICKUP_DISTANCE:
                self.pickup_item(pickup)
                self.pickups.remove(pickup)
                return
        self.message = "附近没有可拾取的物品"
        self.message_timer = 2000
    
    def pickup_item(self, pickup):
        item = pickup["item"]
        stack_size = pickup.get("count", 1)
        
        for i in range(INVENTORY_SLOTS):
            if self.inventory[i] and self.inventory[i]["item"] == item:
                self.inventory[i]["count"] += stack_size
                self.message = f"拾取: {item} x{stack_size}"
                self.message_timer = 2000
                save()
                return
        
        for i in range(INVENTORY_SLOTS):
            if self.inventory[i] is None:
                self.inventory[i] = {"item": item, "count": stack_size}
                self.message = f"拾取: {item} x{stack_size}"
                self.message_timer = 2000
                save()
                return
        
        self.message = "背包已满！"
        self.message_timer = 2000
    
    def handle_inventory_click(self, mouse_pos):
        slot_size = 50
        slot_spacing = 5
        start_x = SCREEN_WIDTH // 2 - (9 * slot_size + 8 * slot_spacing) // 2
        start_y = SCREEN_HEIGHT // 2 - 2 * (slot_size + slot_spacing)
        
        for i in range(INVENTORY_SLOTS):
            slot_x = start_x + (i % 9) * (slot_size + slot_spacing)
            slot_y = start_y + (i // 9) * (slot_size + slot_spacing)
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            
            if slot_rect.collidepoint(mouse_pos):
                if i == self.selected_slot:
                    pass
                elif self.inventory[i]:
                    temp = self.inventory[i]
                    self.inventory[i] = self.inventory[self.selected_slot]
                    self.inventory[self.selected_slot] = temp
                elif self.inventory[self.selected_slot]:
                    self.inventory[i] = self.inventory[self.selected_slot]
                    self.inventory[self.selected_slot] = None
    
    def spawn_pickup(self, item, x, y, count=1):
        pickup = {
            "item": item,
            "x": x,
            "y": y,
            "count": count,
            "lifetime": 300
        }
        self.pickups.append(pickup)
    
    def spawn_enemy(self):
        if len(self.enemies) >= 15:
            return
        
        enemy_types = [
            {"name": "僵尸", "health": 20, "damage": 5, "color": (0.4, 0.6, 0.3), "speed": 0.3},
            {"name": "骷髅", "health": 15, "damage": 4, "color": (0.9, 0.9, 0.8), "speed": 0.4},
            {"name": "蜘蛛", "health": 12, "damage": 3, "color": (0.2, 0.2, 0.2), "speed": 0.5},
            {"name": "苦力怕", "health": 18, "damage": 10, "color": (0.5, 0.9, 0.4), "speed": 0.35}
        ]
        
        enemy_type = random.choice(enemy_types)
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(50, 100)
        
        enemy = {
            "type": enemy_type["name"],
            "x": self.player_pos[0] + math.cos(angle) * distance,
            "z": self.player_pos[2] + math.sin(angle) * distance,
            "health": enemy_type["health"],
            "max_health": enemy_type["health"],
            "damage": enemy_type["damage"],
            "color": enemy_type["color"],
            "speed": enemy_type["speed"],
            "attack_cooldown": 0
        }
        
        self.enemies.append(enemy)
    
    def update_enemies(self):
        if random.random() < 0.005 and len(self.enemies) < 10:
            self.spawn_enemy()
        
        for enemy in self.enemies[:]:
            dx = self.player_pos[0] - enemy["x"]
            dz = self.player_pos[2] - enemy["z"]
            distance = math.hypot(dx, dz)
            
            if distance > 1:
                enemy["x"] += (dx / distance) * enemy["speed"]
                enemy["z"] += (dz / distance) * enemy["speed"]
            
            if enemy.get("attack_cooldown", 0) > 0:
                enemy["attack_cooldown"] -= 1
            
            if distance < 2 and enemy["attack_cooldown"] <= 0:
                self.player_health -= enemy["damage"]
                enemy["attack_cooldown"] = 60
                self.message = f"💀 {enemy['type']} 攻击了你！-{enemy['damage']}生命"
                self.message_timer = 2000
            
            for general in self.generals[:]:
                gx = general["x"] - enemy["x"]
                gz = general["z"] - enemy["z"]
                g_dist = math.hypot(gx, gz)
                
                if g_dist > 1:
                    general["x"] += (gx / g_dist) * enemy["speed"] * 0.8
                    general["z"] += (gz / g_dist) * enemy["speed"] * 0.8
                
                if g_dist < 2 and general.get("attack_cooldown", 0) <= 0:
                    enemy["health"] -= 5
                    general["attack_cooldown"] = 40
                    if enemy["health"] <= 0:
                        self.enemies.remove(enemy)
                        self.spawn_loot(enemy["x"], enemy["z"])
                        self.message = f"⚔️ {general['name']} 击败了{enemy['type']}！"
                        self.message_timer = 2000
    
    def refresh_marketplace(self):
        self.marketplace = []
        
        gun_items = ["gun_ak47", "gun_m4a1", "gun_awp", "gun_mp5", "gun_m1911", "gun_glock",
                    "gun_scarh", "gun_p90", "gun_uzi", "gun_deserteagle", "gun_barrett", "gun_rpg"]
        ammo_items = ["ammo_762", "ammo_556", "ammo_9mm", "ammo_45acp", "ammo_50ae", "ammo_50bmg", "ammo_57mm", "ammo_rpg"]
        attachment_items = ["attachment_scope_4x", "attachment_scope_8x", "attachment_scope_red_dot",
                          "attachment_silencer", "attachment_extended_mag", "attachment_grip",
                          "attachment_laser", "attachment_flashlight", "attachment_bipod", "attachment_stock"]
        rare_items = ["diamond", "emerald", "netherite_ingot", "golden_apple", "enchanted_golden_apple",
                     "tech_advanced_chip", "tech_fusion_core"]
        
        all_items = gun_items + ammo_items + attachment_items + rare_items
        
        for _ in range(10):
            item = random.choice(all_items)
            base_price = 50
            
            if item.startswith("gun_"):
                gun_data = MC_BLOCKS.get(item, {})
                damage = gun_data.get("damage", 15)
                base_price = damage * 5
            elif item.startswith("ammo_"):
                base_price = random.randint(10, 30)
            elif item.startswith("attachment_"):
                base_price = random.randint(30, 100)
            elif item in rare_items:
                base_price = random.randint(100, 500)
            
            price_variation = random.uniform(0.8, 1.5)
            final_price = int(base_price * price_variation)
            
            self.marketplace.append({
                "item": item,
                "price": final_price,
                "count": random.randint(1, 10),
                "seller": random.choice(["系统商人", "玩家A", "玩家B", "神秘商人"])
            })
        
        self.message = "🏪 交易行已刷新！新商品上架"
        self.message_timer = 3000
    
    def buy_from_marketplace(self, index):
        if index < 0 or index >= len(self.marketplace):
            return
        
        item_data = self.marketplace[index]
        price = item_data["price"]
        item_name = item_data["item"]
        count = item_data["count"]
        
        resources = data.get('resources', {})
        gold = resources.get('金元宝', 0)
        
        if gold < price:
            self.message = f"⚠️ 金元宝不足！需要{price}，当前{gold}"
            self.message_timer = 2000
            return
        
        resources['金元宝'] = gold - price
        data['resources'] = resources
        save()
        
        for i, inv_item in enumerate(self.inventory):
            if inv_item and inv_item["item"] == item_name:
                self.inventory[i]["count"] += count
                self.marketplace.remove(item_data)
                self.message = f"✅ 购买成功: {item_name} x{count}"
                self.message_timer = 2000
                return
        
        for i, inv_item in enumerate(self.inventory):
            if inv_item is None:
                self.inventory[i] = {"item": item_name, "count": count}
                self.marketplace.remove(item_data)
                self.message = f"✅ 购买成功: {item_name} x{count}"
                self.message_timer = 2000
                return
        
        self.message = "⚠️ 背包已满！"
        self.message_timer = 2000
    
    def update_marketplace(self):
        self.marketplace_timer += 1
        if self.marketplace_timer >= self.marketplace_refresh_interval:
            self.marketplace_timer = 0
            self.refresh_marketplace()
    
    def update_projectiles(self):
        for projectile in self.projectiles[:]:
            projectile["x"] += projectile["velocity"][0]
            projectile["y"] += projectile["velocity"][1]
            projectile["z"] += projectile["velocity"][2]
            projectile["velocity"][1] -= 0.02
            projectile["lifetime"] -= 1
            
            if projectile["lifetime"] <= 0 or projectile["y"] < 0:
                self.projectiles.remove(projectile)
                continue
            
            for enemy in self.enemies[:]:
                distance = math.hypot(
                    enemy["x"] - projectile["x"],
                    enemy["z"] - projectile["z"]
                )
                if distance < 2:
                    enemy["health"] = enemy.get("health", 20) - 15
                    self.projectiles.remove(projectile)
                    if enemy["health"] <= 0:
                        self.enemies.remove(enemy)
                        self.spawn_loot(enemy["x"], enemy["z"])
                    break
    
    def update_pickups(self):
        if random.random() < 0.005 and len(self.pickups) < 30:
            common_drops = [
                "dirt", "grass", "stone", "cobblestone", "oak_log", "oak_planks",
                "iron_ingot", "coal", "sand", "gravel", "clay",
                "wooden_sword", "stone_sword", "iron_sword", "diamond_sword",
                "wooden_pickaxe", "stone_pickaxe", "iron_pickaxe", "diamond_pickaxe",
                "apple", "bread", "cooked_beef", "cooked_chicken",
                "carrot", "potato", "baked_potato", "beetroot"
            ]
            rare_drops = [
                "gold_ingot", "diamond", "emerald", "lapis_lazuli", "redstone",
                "tech_advanced_chip", "tech_circuit_board", "netherite_ingot",
                "golden_apple", "enchanted_golden_apple", "diamond_sword",
                "netherite_sword", "bow", "crossbow", "trident",
                "iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots",
                "diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots"
            ]
            
            if random.random() < 0.15:
                item = random.choice(rare_drops)
            else:
                item = random.choice(common_drops)
            
            x = self.player_pos[0] + random.randint(-30, 30)
            z = self.player_pos[2] + random.randint(-30, 30)
            self.spawn_pickup(item, x, z, random.randint(1, 3))
        
        for pickup in self.pickups[:]:
            pickup["lifetime"] -= 1
            
            if "bob_offset" not in pickup:
                pickup["bob_offset"] = random.uniform(0, math.pi * 2)
            if "rotation" not in pickup:
                pickup["rotation"] = 0
            if "target_x" not in pickup:
                pickup["target_x"] = None
                pickup["target_z"] = None
            if "speed" not in pickup:
                pickup["speed"] = 0
            
            pickup["rotation"] += 0.05
            pickup["bob_offset"] += 0.1
            
            distance = math.hypot(
                pickup["x"] - self.player_pos[0],
                pickup["y"] - self.player_pos[2]
            )
            
            if distance <= MAX_PICKUP_DISTANCE and not self.inventory_open:
                dx = self.player_pos[0] - pickup["x"]
                dz = self.player_pos[2] - pickup["y"]
                pickup["speed"] = min(pickup["speed"] + 0.3, 1.5)
                pickup["x"] += dx / distance * pickup["speed"]
                pickup["y"] += dz / distance * pickup["speed"]
                
                if distance < 1.0:
                    self.pickup_item(pickup)
                    self.pickups.remove(pickup)
                    continue
            
            if pickup["lifetime"] <= 0:
                self.pickups.remove(pickup)
    
    def draw_minimap(self):
        if not self.minimap_enabled:
            return
        
        minimap_size = MINIMAP_SIZE
        minimap_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
        
        pygame.draw.rect(minimap_surface, (20, 20, 40, 180), (0, 0, minimap_size, minimap_size), border_radius=10)
        pygame.draw.rect(minimap_surface, COLORS["accent_gold"], (0, 0, minimap_size, minimap_size), 2, border_radius=10)
        
        scale = minimap_size / 400
        center_x = minimap_size // 2
        center_y = minimap_size // 2
        
        for loc in self.locations:
            rel_x = (loc["x"] - self.player_pos[0]) * scale
            rel_y = (loc["y"] - self.player_pos[2]) * scale
            
            if -minimap_size//2 <= rel_x <= minimap_size//2 and -minimap_size//2 <= rel_y <= minimap_size//2:
                map_x = int(center_x + rel_x)
                map_y = int(center_y + rel_y)
                
                if loc.get("owner") == "player":
                    color = (50, 205, 50)
                elif loc.get("owner") == "enemy":
                    color = (255, 69, 0)
                else:
                    color = (150, 150, 150)
                
                pygame.draw.circle(minimap_surface, color, (map_x, map_y), 3)
        
        for pickup in self.pickups:
            rel_x = (pickup["x"] - self.player_pos[0]) * scale
            rel_y = (pickup["y"] - self.player_pos[2]) * scale
            
            if -minimap_size//2 <= rel_x <= minimap_size//2 and -minimap_size//2 <= rel_y <= minimap_size//2:
                map_x = int(center_x + rel_x)
                map_y = int(center_y + rel_y)
                pygame.draw.circle(minimap_surface, (255, 255, 100), (map_x, map_y), 2)
        
        player_arrow_x = center_x
        player_arrow_y = center_y
        
        yaw_rad = math.radians(self.camera["yaw"])
        arrow_length = 8
        arrow_end_x = int(player_arrow_x + math.sin(yaw_rad) * arrow_length)
        arrow_end_y = int(player_arrow_y - math.cos(yaw_rad) * arrow_length)
        
        pygame.draw.circle(minimap_surface, (255, 255, 255), (player_arrow_x, player_arrow_y), 3)
        pygame.draw.line(minimap_surface, (255, 255, 255), (player_arrow_x, player_arrow_y), (arrow_end_x, arrow_end_y), 2)
        
        self.screen.blit(minimap_surface, (10, 10))
        
        label_surf = self.font_small.render("小地图 M", True, (200, 200, 200))
        self.screen.blit(label_surf, (10, MINIMAP_SIZE + 15))
    
    def draw_inventory(self):
        if not self.inventory_open:
            return
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        slot_size = 50
        slot_spacing = 5
        inventory_width = 9 * slot_size + 8 * slot_spacing + 40
        inventory_height = 4 * (slot_size + slot_spacing) + 80
        
        inventory_x = SCREEN_WIDTH // 2 - inventory_width // 2
        inventory_y = SCREEN_HEIGHT // 2 - inventory_height // 2
        
        inventory_surf = pygame.Surface((inventory_width, inventory_height), pygame.SRCALPHA)
        pygame.draw.rect(inventory_surf, (40, 40, 60, 230), (0, 0, inventory_width, inventory_height), border_radius=15)
        pygame.draw.rect(inventory_surf, COLORS["accent_gold"], (0, 0, inventory_width, inventory_height), 3, border_radius=15)
        
        title_surf = self.font_main.render("背包 I", True, COLORS["accent_gold"])
        inventory_surf.blit(title_surf, (20, 15))
        
        start_x = 20
        start_y = 50
        
        hotbar_labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        
        for i in range(INVENTORY_SLOTS):
            slot_x = start_x + (i % 9) * (slot_size + slot_spacing)
            slot_y = start_y + (i // 9) * (slot_size + slot_spacing)
            
            if i == self.selected_slot:
                pygame.draw.rect(inventory_surf, (100, 100, 150), (slot_x - 3, slot_y - 3, slot_size + 6, slot_size + 6), border_radius=8)
                pygame.draw.rect(inventory_surf, COLORS["accent_blue"], (slot_x - 3, slot_y - 3, slot_size + 6, slot_size + 6), 3, border_radius=8)
            else:
                pygame.draw.rect(inventory_surf, (60, 60, 80), (slot_x, slot_y, slot_size, slot_size), border_radius=6)
                pygame.draw.rect(inventory_surf, (100, 100, 120), (slot_x, slot_y, slot_size, slot_size), 2, border_radius=6)
            
            if i < 9:
                label_surf = self.font_small.render(hotbar_labels[i], True, (150, 150, 150))
                inventory_surf.blit(label_surf, (slot_x + 3, slot_y + 3))
            
            if self.inventory[i]:
                item = self.inventory[i]
                item_name = item["item"]
                item_count = item["count"]
                
                block_data = MC_BLOCKS.get(item_name, MC_BLOCKS.get("stone", {}))
                color = block_data.get("color", (128, 128, 128))
                if len(color) == 4:
                    item_surf = pygame.Surface((slot_size - 10, slot_size - 10), pygame.SRCALPHA)
                    pygame.draw.rect(item_surf, color, (0, 0, slot_size - 10, slot_size - 10), border_radius=4)
                else:
                    item_surf = pygame.Surface((slot_size - 10, slot_size - 10))
                    pygame.draw.rect(item_surf, color, (0, 0, slot_size - 10, slot_size - 10), border_radius=4)
                
                inventory_surf.blit(item_surf, (slot_x + 5, slot_y + 5))
                
                if item_count > 1:
                    count_surf = self.font_small.render(str(item_count), True, (255, 255, 255))
                    inventory_surf.blit(count_surf, (slot_x + slot_size - 25, slot_y + slot_size - 20))
        
        hint_surf = self.font_small.render("点击交换物品 | 数字键选择快捷栏 | I键关闭", True, (150, 150, 150))
        inventory_surf.blit(hint_surf, (20, inventory_height - 30))
        
        self.screen.blit(inventory_surf, (inventory_x, inventory_y))
    
    def draw_hotbar(self):
        if self.inventory_open:
            return
        
        slot_size = 40
        slot_spacing = 3
        hotbar_width = 9 * slot_size + 8 * slot_spacing + 20
        hotbar_height = slot_size + 15
        hotbar_x = SCREEN_WIDTH // 2 - hotbar_width // 2
        hotbar_y = SCREEN_HEIGHT - hotbar_height - 10
        
        hotbar_surf = pygame.Surface((hotbar_width, hotbar_height), pygame.SRCALPHA)
        pygame.draw.rect(hotbar_surf, (30, 30, 50, 200), (0, 0, hotbar_width, hotbar_height), border_radius=10)
        pygame.draw.rect(hotbar_surf, (80, 80, 100), (0, 0, hotbar_width, hotbar_height), 2, border_radius=10)
        
        start_x = 10
        start_y = 8
        
        for i in range(9):
            slot_x = start_x + i * (slot_size + slot_spacing)
            
            if i == self.selected_slot:
                pygame.draw.rect(hotbar_surf, (80, 80, 120), (slot_x - 2, start_y - 2, slot_size + 4, slot_size + 4), border_radius=6)
                pygame.draw.rect(hotbar_surf, COLORS["accent_blue"], (slot_x - 2, start_y - 2, slot_size + 4, slot_size + 4), 2, border_radius=6)
            else:
                pygame.draw.rect(hotbar_surf, (50, 50, 70), (slot_x, start_y, slot_size, slot_size), border_radius=4)
            
            if self.inventory[i]:
                item = self.inventory[i]
                block_data = MC_BLOCKS.get(item["item"], MC_BLOCKS.get("stone", {}))
                color = block_data.get("color", (128, 128, 128))
                
                item_surf = pygame.Surface((slot_size - 6, slot_size - 6))
                if len(color) == 4:
                    item_surf.fill((0, 0, 0, 0))
                    pygame.draw.rect(item_surf, color[:3], (0, 0, slot_size - 6, slot_size - 6), border_radius=3)
                else:
                    pygame.draw.rect(item_surf, color, (0, 0, slot_size - 6, slot_size - 6), border_radius=3)
                
                hotbar_surf.blit(item_surf, (slot_x + 3, start_y + 3))
                
                if item["count"] > 1:
                    count_surf = self.font_small.render(str(item["count"]), True, (255, 255, 255))
                    hotbar_surf.blit(count_surf, (slot_x + slot_size - 18, start_y + slot_size - 16))
        
        self.screen.blit(hotbar_surf, (hotbar_x, hotbar_y))
    
    def check_npc_interaction(self):
        for npc in self.npcs:
            distance = math.hypot(
                npc["x"] - self.player_pos[0],
                npc["z"] - self.player_pos[2]
            )
            if distance <= self.npc_interaction_distance:
                self.selected_npc = npc
                self.message = f"右键NPC: {npc['name']}"
                self.message_timer = 3000
                self.show_npc_dialog(npc)
                return
        
        self.selected_npc = None
        self.message = "附近没有NPC"
        self.message_timer = 2000
    
    def show_npc_dialog(self, npc):
        self.npc_dialog_active = True
        self.selected_option = 0
        
        options = [
            {"text": f"进入{npc['name']}功能", "action": "enter"},
            {"text": "继续探索", "action": "cancel"}
        ]
        
        while self.npc_dialog_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.npc_dialog_active = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if options[self.selected_option]["action"] == "enter":
                            self.npc_dialog_active = False
                            self.execute_npc_action(npc)
                            return
                        else:
                            self.npc_dialog_active = False
                            return
                    elif event.key == pygame.K_ESCAPE:
                        self.npc_dialog_active = False
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        for i, option in enumerate(options):
                            option_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 180 + i * 40, 300, 35)
                            if option_rect.collidepoint(mouse_pos):
                                if option["action"] == "enter":
                                    self.npc_dialog_active = False
                                    self.execute_npc_action(npc)
                                    return
                                else:
                                    self.npc_dialog_active = False
                                    return
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw_3d_scene()
            
            dialog_width = 400
            dialog_height = 200
            dialog_x = SCREEN_WIDTH // 2 - dialog_width // 2
            dialog_y = SCREEN_HEIGHT - 250
            
            dialog_surf = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
            pygame.draw.rect(dialog_surf, (20, 20, 40, 230), (0, 0, dialog_width, dialog_height), border_radius=15)
            pygame.draw.rect(dialog_surf, COLORS["accent_gold"], (0, 0, dialog_width, dialog_height), 3, border_radius=15)
            
            name_surf = self.font_main.render(npc["name"], True, COLORS["accent_gold"])
            dialog_surf.blit(name_surf, (20, 15))
            
            dialogue_surf = self.font_small.render(npc["dialogue"], True, COLORS["text_white"])
            dialog_surf.blit(dialogue_surf, (20, 55))
            
            pygame.draw.line(dialog_surf, COLORS["accent_gold"], (20, 90), (dialog_width - 20, 90), 1)
            
            for i, option in enumerate(options):
                option_y = 100 + i * 40
                option_rect = pygame.Rect(20, option_y, dialog_width - 40, 35)
                
                if i == self.selected_option:
                    pygame.draw.rect(dialog_surf, (60, 60, 100), option_rect, border_radius=8)
                    pygame.draw.rect(dialog_surf, COLORS["accent_gold"], option_rect, 2, border_radius=8)
                    option_color = COLORS["accent_gold"]
                else:
                    pygame.draw.rect(dialog_surf, (40, 40, 70), option_rect, border_radius=8)
                    option_color = COLORS["text_white"]
                
                option_surf = self.font_small.render(option["text"], True, option_color)
                dialog_surf.blit(option_surf, (option_rect.x + 15, option_rect.y + 8))
            
            self.screen.blit(dialog_surf, (dialog_x, dialog_y))
            
            hint_surf = self.font_small.render("↑↓选择 | 回车确认 | ESC取消", True, (150, 150, 150))
            self.screen.blit(hint_surf, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT - 40))
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def execute_npc_action(self, npc):
        module_file = npc.get("module", "")
        if module_file:
            self.message = f"正在打开: {npc['name']}"
            self.message_timer = 2000
            
            pygame.time.wait(500)
            
            try:
                if module_file == "hero_recruitment.py":
                    from ASSET.hero_recruitment import main as hero_main
                    hero_main()
                elif module_file == "shop_system.py":
                    from ASSET.shop_system import main as shop_main
                    shop_main()
                elif module_file == "quest_system.py":
                    from ASSET.quest_system import main as quest_main
                    quest_main()
                elif module_file == "equipment_system.py":
                    from ASSET.equipment_system import main as equipment_main
                    equipment_main()
                elif module_file == "alchemy_system.py":
                    from ASSET.alchemy_system import main as alchemy_main
                    alchemy_main()
                elif module_file == "background_story.py":
                    from ASSET.background_story import main as story_main
                    story_main()
                elif module_file == "pvp_p2p.py":
                    from ASSET.pvp_p2p import main as pvp_main
                    pvp_main()
                else:
                    self.message = f"功能模块 {module_file} 尚未实现"
                    self.message_timer = 2000
            except Exception as e:
                self.message = f"打开功能失败: {str(e)[:20]}"
                self.message_timer = 2000
            
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
            self.screen = pygame.display.get_surface()
    
    def check_location_interaction(self):
        interaction_distance = 25
        closest_location = None
        closest_distance = float('inf')
        
        for loc in self.locations:
            distance = math.hypot(
                loc["x"] - self.player_pos[0],
                loc["y"] - self.player_pos[2]
            )
            if distance < closest_distance:
                closest_distance = distance
                closest_location = loc
        
        if closest_location and closest_distance <= interaction_distance:
            self.show_location_dialog(closest_location)
        else:
            self.message = "附近没有可进入的地点"
            self.message_timer = 2000
    
    def show_location_dialog(self, loc):
        self.location_dialog_active = True
        self.selected_option = 0
        
        loc_type = loc.get("type", "地点")
        owner = loc.get("owner", "neutral")
        level = loc.get("level", 1)
        power = loc.get("power", 0)
        
        if owner == "player":
            options = [
                {"text": "进入地点", "action": "enter"},
                {"text": "查看详情", "action": "info"},
                {"text": "离开", "action": "cancel"}
            ]
        elif owner == "enemy":
            options = [
                {"text": "挑战占领", "action": "battle"},
                {"text": "查看详情", "action": "info"},
                {"text": "离开", "action": "cancel"}
            ]
        else:
            options = [
                {"text": "尝试占领", "action": "capture"},
                {"text": "查看详情", "action": "info"},
                {"text": "离开", "action": "cancel"}
            ]
        
        while self.location_dialog_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.location_dialog_active = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        action = options[self.selected_option]["action"]
                        self.location_dialog_active = False
                        self.handle_location_action(loc, action)
                        return
                    elif event.key == pygame.K_ESCAPE:
                        self.location_dialog_active = False
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        for i, option in enumerate(options):
                            option_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 220 + i * 40, 300, 35)
                            if option_rect.collidepoint(mouse_pos):
                                action = option["action"]
                                self.location_dialog_active = False
                                self.handle_location_action(loc, action)
                                return
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw_3d_scene()
            
            dialog_width = 400
            dialog_height = 280
            dialog_x = SCREEN_WIDTH // 2 - dialog_width // 2
            dialog_y = SCREEN_HEIGHT - 330
            
            dialog_surf = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
            pygame.draw.rect(dialog_surf, (20, 20, 40, 230), (0, 0, dialog_width, dialog_height), border_radius=15)
            pygame.draw.rect(dialog_surf, COLORS["accent_gold"], (0, 0, dialog_width, dialog_height), 3, border_radius=15)
            
            name_surf = self.font_main.render(loc_type, True, COLORS["accent_gold"])
            dialog_surf.blit(name_surf, (20, 15))
            
            owner_text = f"归属: {'已占领' if owner == 'player' else '敌方' if owner == 'enemy' else '中立'}"
            owner_color = COLORS["accent_green"] if owner == "player" else COLORS["accent_red"] if owner == "enemy" else COLORS["text_white"]
            owner_surf = self.font_small.render(owner_text, True, owner_color)
            dialog_surf.blit(owner_surf, (20, 55))
            
            level_surf = self.font_small.render(f"等级: {level}", True, COLORS["text_white"])
            dialog_surf.blit(level_surf, (20, 80))
            
            power_surf = self.font_small.render(f"战力: {power}", True, COLORS["text_white"])
            dialog_surf.blit(power_surf, (20, 105))
            
            pygame.draw.line(dialog_surf, COLORS["accent_gold"], (20, 135), (dialog_width - 20, 135), 1)
            
            for i, option in enumerate(options):
                option_y = 145 + i * 40
                option_rect = pygame.Rect(20, option_y, dialog_width - 40, 35)
                
                if i == self.selected_option:
                    pygame.draw.rect(dialog_surf, (60, 60, 100), option_rect, border_radius=8)
                    pygame.draw.rect(dialog_surf, COLORS["accent_gold"], option_rect, 2, border_radius=8)
                    option_color = COLORS["accent_gold"]
                else:
                    pygame.draw.rect(dialog_surf, (40, 40, 70), option_rect, border_radius=8)
                    option_color = COLORS["text_white"]
                
                option_surf = self.font_small.render(option["text"], True, option_color)
                dialog_surf.blit(option_surf, (option_rect.x + 15, option_rect.y + 8))
            
            self.screen.blit(dialog_surf, (dialog_x, dialog_y))
            
            hint_surf = self.font_small.render("↑↓选择 | 回车确认 | ESC取消", True, (150, 150, 150))
            self.screen.blit(hint_surf, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT - 40))
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def handle_location_action(self, loc, action):
        if action == "enter":
            self.message = f"进入 {loc['type']}..."
            self.message_timer = 2000
            try:
                from ASSET.game_map_pygame import main as map_main
                map_main()
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
                self.screen = pygame.display.get_surface()
            except Exception as e:
                self.message = f"进入失败: {str(e)[:20]}"
                self.message_timer = 2000
        elif action == "battle":
            self.message = f"开始挑战 {loc['type']}..."
            self.message_timer = 2000
            try:
                from ASSET.battle_system import main as battle_main
                battle_main()
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
                self.screen = pygame.display.get_surface()
                self.message = f"战斗结束!"
                self.message_timer = 3000
            except Exception as e:
                self.message = f"挑战失败: {str(e)[:20]}"
                self.message_timer = 2000
        elif action == "capture":
            self.message = f"尝试占领 {loc['type']}..."
            self.message_timer = 2000
            loc["owner"] = "player"
            self.message = f"成功占领 {loc['type']}!"
            self.message_timer = 3000
        elif action == "info":
            info_text = f"{loc['type']} - 等级{loc.get('level', 1)} - 战力{loc.get('power', 0)}"
            self.message = info_text
            self.message_timer = 3000
    
    def collect_nearby_resources(self):
        collect_distance = 30
        collected = {"金元宝": 0, "煤炭": 0, "食物": 0, "水": 0}
        
        for loc in self.locations:
            if loc.get("owner") == "player":
                distance = math.hypot(
                    loc["x"] - self.player_pos[0],
                    loc["y"] - self.player_pos[2]
                )
                if distance <= collect_distance:
                    loc_type = loc.get("type", "")
                    level = loc.get("level", 1)
                    
                    if loc_type == "矿产":
                        gold_bonus = level * 5
                        collected["金元宝"] += gold_bonus
                    elif loc_type == "煤矿":
                        coal_bonus = level * 10
                        collected["煤炭"] += coal_bonus
                    elif loc_type == "农田":
                        food_bonus = level * 15
                        water_bonus = level * 5
                        collected["食物"] += food_bonus
                        collected["水"] += water_bonus
                    elif loc_type == "水井":
                        water_bonus = level * 12
                        collected["水"] += water_bonus
        
        total_collected = sum(collected.values())
        if total_collected > 0:
            resources = data.get('resources', {})
            for resource, amount in collected.items():
                if amount > 0:
                    resources[resource] = resources.get(resource, 0) + amount
            data['resources'] = resources
            save()
            
            msg_parts = []
            if collected["金元宝"] > 0:
                msg_parts.append(f"金元宝+{collected['金元宝']}")
            if collected["煤炭"] > 0:
                msg_parts.append(f"煤炭+{collected['煤炭']}")
            if collected["食物"] > 0:
                msg_parts.append(f"食物+{collected['食物']}")
            if collected["水"] > 0:
                msg_parts.append(f"水+{collected['水']}")
            
            self.message = "收集: " + " ".join(msg_parts)
            self.message_timer = 3000
        else:
            self.message = "附近没有可收集的资源"
            self.message_timer = 2000
    
    def move_forward(self, speed):
        yaw_rad = math.radians(self.camera["yaw"])
        self.velocity[0] += math.cos(yaw_rad) * speed
        self.velocity[2] += math.sin(yaw_rad) * speed
        self.update_camera()
    
    def move_backward(self, speed):
        yaw_rad = math.radians(self.camera["yaw"])
        self.velocity[0] -= math.cos(yaw_rad) * speed
        self.velocity[2] -= math.sin(yaw_rad) * speed
        self.update_camera()
    
    def move_left(self, speed):
        yaw_rad = math.radians(self.camera["yaw"])
        self.velocity[0] -= math.sin(yaw_rad) * speed
        self.velocity[2] += math.cos(yaw_rad) * speed
        self.update_camera()
    
    def move_right(self, speed):
        yaw_rad = math.radians(self.camera["yaw"])
        self.velocity[0] += math.sin(yaw_rad) * speed
        self.velocity[2] -= math.cos(yaw_rad) * speed
        self.update_camera()
    
    def update_camera(self):
        yaw_rad = math.radians(self.camera["yaw"])
        pitch_rad = math.radians(self.camera["pitch"])
        
        if self.camera["mode"] == "first":
            distance = 0.5
            self.camera["x"] = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 1.8 + math.sin(pitch_rad) * distance
            self.camera["z"] = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * distance
        else:
            distance = 6.0
            self.camera["x"] = self.player_pos[0] - math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 2.5 - math.sin(pitch_rad) * distance
            self.camera["z"] = self.player_pos[2] - math.sin(yaw_rad) * math.cos(pitch_rad) * distance
    
    def move_to_mouse(self):
        mx, my = pygame.mouse.get_pos()
        self.follow_target = {
            "x": self.player_pos[0] + (mx - SCREEN_WIDTH//2) * 0.15,
            "y": self.player_pos[2] + (my - SCREEN_HEIGHT//2) * 0.15
        }
        self.message = "移动到指定位置"
        self.message_timer = 2000
    
    def update_followers(self):
        if self.follow_target:
            for follower in self.followers:
                dx = self.follow_target["x"] - follower["x"]
                dz = self.follow_target["y"] - follower["z"]
                distance = math.hypot(dx, dz)
                if distance > 1:
                    follower["x"] += dx / distance * 0.3
                    follower["z"] += dz / distance * 0.3
    
    def update_npcs(self):
        for npc in self.npcs:
            npc["animation_offset"] += 0.02
            
            wander_angle = npc["move_dir"] + time.time() * npc["move_speed"]
            npc["x"] = npc["original_x"] + math.sin(wander_angle) * npc["wander_range"]
            npc["z"] = npc["original_z"] + math.cos(wander_angle) * npc["wander_range"]
    
    def draw_3d_scene(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(60, SCREEN_WIDTH / SCREEN_HEIGHT, 0.1, 5000.0)
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            yaw_rad = math.radians(self.camera["yaw"])
            pitch_rad = math.radians(self.camera["pitch"])
            
            look_distance = 10
            look_x = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * look_distance
            look_y = self.player_pos[1] + 1.8 + math.sin(pitch_rad) * look_distance
            look_z = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * look_distance
            
            gluLookAt(
                self.camera["x"], self.camera["y"], self.camera["z"],
                look_x, look_y, look_z,
                0, 1, 0
            )
            
            if c_renderer_available and renderer:
                self.draw_3d_scene_cpp()
            else:
                self.draw_3d_scene_python()
            
            pygame.display.flip()
        except Exception as e:
            print(f"渲染错误: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_3d_scene_cpp(self):
        try:
            renderer.render_terrain(self.player_pos)
            
            if hasattr(self, 'trees'):
                renderer.render_trees(self.trees)
            
            renderer.render_structures(self.large_structures)
            renderer.render_locations(self.locations)
            renderer.render_npcs(self.npcs)
            renderer.render_enemies(self.enemies)
            renderer.render_generals(self.generals)
            renderer.render_pets(self.pets)
            
            if self.camera["mode"] == "third":
                player_data = {
                    "x": self.player_pos[0],
                    "y": self.player_pos[1],
                    "z": self.player_pos[2],
                    "color": (0.8, 0.8, 0.8),
                    "yaw": self.camera["yaw"]
                }
                renderer.render_player(player_data)
            
            renderer.render_followers(self.followers)
            
            for tech_block in self.tech_blocks:
                renderer.render_tech_block(tech_block, MC_BLOCKS)
            
            renderer.render_projectiles(self.projectiles)
            renderer.render_pickups(self.pickups, MC_BLOCKS)
        except Exception as e:
            print(f"C++渲染器错误: {e}")
            self.draw_3d_scene_python()
    
    def draw_3d_scene_python(self):
        try:
            self.draw_terrain()
            
            if hasattr(self, 'trees'):
                for tree in self.trees:
                    x, z, scale = tree
                    self.draw_tree(x, z, scale)
            
            for struct in self.large_structures:
                self.draw_large_structure(struct)
            
            for loc in self.locations:
                self.draw_location(loc)
            
            for npc in self.npcs:
                self.draw_npc(npc)
            
            for enemy in self.enemies:
                self.draw_enemy(enemy)
            
            for general in self.generals:
                self.draw_general(general)
            
            for pet in self.pets:
                self.draw_pet(pet)
            
            if self.camera["mode"] == "third":
                self.draw_player()
            
            for follower in self.followers:
                self.draw_follower(follower)
            
            for tech_block in self.tech_blocks:
                self.draw_tech_block(tech_block)
            
            self.draw_projectiles()
            self.draw_pickups()
        except Exception as e:
            print(f"Python渲染错误: {e}")
    
    def draw_terrain(self):
        try:
            glDisable(GL_LIGHTING)
            
            block_size = 5
            height = -2
            
            visible_range = 200
            
            start_x = int((self.player_pos[0] - visible_range) / block_size) * block_size
            end_x = int((self.player_pos[0] + visible_range) / block_size) * block_size
            start_z = int((self.player_pos[2] - visible_range) / block_size) * block_size
            end_z = int((self.player_pos[2] + visible_range) / block_size) * block_size
            
            for x in range(start_x, end_x, block_size):
                for z in range(start_z, end_z, block_size):
                    noise = math.sin(x * 0.008) * math.cos(z * 0.008) * 3 + \
                            math.sin(x * 0.015) * math.sin(z * 0.015) * 2
                    block_y = height + noise
                    
                    if block_y < self.player_pos[1] - 30:
                        continue
                    
                    grass_color_intensity = 0.2 + noise * 0.05
                    glColor3f(0.2 + grass_color_intensity, 0.5 + grass_color_intensity, 0.2 + grass_color_intensity)
                    
                    glBegin(GL_QUADS)
                    glVertex3f(x, block_y, z)
                    glVertex3f(x + block_size, block_y, z)
                    glVertex3f(x + block_size, block_y, z + block_size)
                    glVertex3f(x, block_y, z + block_size)
                    glEnd()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            print(f"绘制地形错误: {e}")
    
    def spawn_loot(self, x, z):
        loot_items = ["iron_ingot", "gold_ingot", "diamond", "coal", "bread", "arrow"]
        for _ in range(random.randint(1, 4)):
            item = random.choice(loot_items)
            offset_x = random.uniform(-2, 2)
            offset_z = random.uniform(-2, 2)
            self.spawn_pickup(item, x + offset_x, z + offset_z, 1)
    
    def draw_projectiles(self):
        try:
            glDisable(GL_LIGHTING)
            
            for projectile in self.projectiles:
                x, y, z = projectile["x"], projectile["y"], projectile["z"]
                proj_type = projectile["type"]
                
                glPushMatrix()
                glTranslatef(x, y, z)
                
                if proj_type == "arrow":
                    glColor3f(0.6, 0.4, 0.2)
                    glBegin(GL_LINES)
                    glVertex3f(0, 0, 0)
                    glVertex3f(0, 0.5, 0)
                    glEnd()
                    
                    glColor3f(0.9, 0.9, 0.9)
                    glBegin(GL_LINES)
                    glVertex3f(0, 0.5, 0)
                    glVertex3f(0, 0.8, 0)
                    glEnd()
                
                elif proj_type == "bolt":
                    glColor3f(0.5, 0.5, 0.5)
                    glBegin(GL_LINES)
                    glVertex3f(0, 0, 0)
                    glVertex3f(0, 0.6, 0)
                    glEnd()
                    
                    glColor3f(0.3, 0.3, 0.3)
                    glBegin(GL_LINES)
                    glVertex3f(-0.1, 0.1, 0)
                    glVertex3f(0.1, 0.1, 0)
                    glEnd()
                
                elif proj_type == "trident":
                    glColor3f(0.3, 0.5, 0.8)
                    glBegin(GL_LINES)
                    glVertex3f(0, 0, 0)
                    glVertex3f(0, 1.0, 0)
                    glEnd()
                    
                    glColor3f(0.2, 0.4, 0.7)
                    glBegin(GL_LINES)
                    glVertex3f(-0.15, 0.2, 0)
                    glVertex3f(0, 0.5, 0)
                    glEnd()
                    glBegin(GL_LINES)
                    glVertex3f(0.15, 0.2, 0)
                    glVertex3f(0, 0.5, 0)
                    glEnd()
                
                glPopMatrix()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            print(f"绘制投射物错误: {e}")
    
    def draw_pickups(self):
        try:
            glDisable(GL_LIGHTING)
            
            for pickup in self.pickups:
                x = pickup["x"]
                z = pickup["y"]
                bob_y = math.sin(pickup.get("bob_offset", 0)) * 0.15 + 0.3
                rotation = pickup.get("rotation", 0)
                
                item_name = pickup["item"]
                block_data = MC_BLOCKS.get(item_name, MC_BLOCKS.get("stone", {}))
                color = block_data.get("color", (128, 128, 128))
                
                if len(color) == 4:
                    r, g, b, a = color
                else:
                    r, g, b = color
                    a = 1.0
                
                glColor4f(r/255, g/255, b/255, a)
                
                glPushMatrix()
                glTranslatef(x, bob_y, z)
                glRotatef(math.degrees(rotation), 0, 1, 0)
                
                size = 0.35
                glBegin(GL_QUADS)
                
                glVertex3f(-size, -size, -size)
                glVertex3f(size, -size, -size)
                glVertex3f(size, size, -size)
                glVertex3f(-size, size, -size)
                
                glVertex3f(size, -size, -size)
                glVertex3f(size, -size, size)
                glVertex3f(size, size, size)
                glVertex3f(size, size, -size)
                
                glVertex3f(size, -size, size)
                glVertex3f(-size, -size, size)
                glVertex3f(-size, size, size)
                glVertex3f(size, size, size)
                
                glVertex3f(-size, -size, size)
                glVertex3f(-size, -size, -size)
                glVertex3f(-size, size, -size)
                glVertex3f(-size, size, size)
                
                glVertex3f(-size, size, -size)
                glVertex3f(size, size, -size)
                glVertex3f(size, size, size)
                glVertex3f(-size, size, size)
                
                glVertex3f(-size, -size, size)
                glVertex3f(size, -size, size)
                glVertex3f(size, -size, -size)
                glVertex3f(-size, -size, -size)
                
                glEnd()
                
                glPopMatrix()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            print(f"绘制掉落物错误: {e}")
    
    def draw_tech_block(self, tech_block):
        try:
            glDisable(GL_LIGHTING)
            
            x, z = tech_block["x"], tech_block["z"]
            tech_type = tech_block["type"]
            active = tech_block.get("active", False)
            rotation = tech_block.get("rotation", 0)
            
            block_data = MC_BLOCKS.get(tech_type, MC_BLOCKS.get("stone", {}))
            color = block_data.get("color", (100, 100, 110))
            
            if len(color) == 4:
                r, g, b, a = color
                glColor4f(r/255, g/255, b/255, a)
            else:
                r, g, b = color
                glColor3f(r/255, g/255, b/255)
            
            glPushMatrix()
            glTranslatef(x, 0.5, z)
            glRotatef(rotation * 90, 0, 1, 0)
            
            block_size = 1.5
            
            glBegin(GL_QUADS)
            
            glVertex3f(-block_size/2, 0, -block_size/2)
            glVertex3f(block_size/2, 0, -block_size/2)
            glVertex3f(block_size/2, block_size, -block_size/2)
            glVertex3f(-block_size/2, block_size, -block_size/2)
            
            glVertex3f(block_size/2, 0, -block_size/2)
            glVertex3f(block_size/2, 0, block_size/2)
            glVertex3f(block_size/2, block_size, block_size/2)
            glVertex3f(block_size/2, block_size, -block_size/2)
            
            glVertex3f(block_size/2, 0, block_size/2)
            glVertex3f(-block_size/2, 0, block_size/2)
            glVertex3f(-block_size/2, block_size, block_size/2)
            glVertex3f(block_size/2, block_size, block_size/2)
            
            glVertex3f(-block_size/2, 0, block_size/2)
            glVertex3f(-block_size/2, 0, -block_size/2)
            glVertex3f(-block_size/2, block_size, -block_size/2)
            glVertex3f(-block_size/2, block_size, block_size/2)
            
            glVertex3f(-block_size/2, block_size, -block_size/2)
            glVertex3f(block_size/2, block_size, -block_size/2)
            glVertex3f(block_size/2, block_size, block_size/2)
            glVertex3f(-block_size/2, block_size, block_size/2)
            
            glVertex3f(-block_size/2, 0, block_size/2)
            glVertex3f(block_size/2, 0, block_size/2)
            glVertex3f(block_size/2, 0, -block_size/2)
            glVertex3f(-block_size/2, 0, -block_size/2)
            
            glEnd()
            
            if block_data.get("emissive", False) and active:
                pulse = math.sin(time.time() * 3) * 0.2 + 0.8
                glColor4f(r/255*pulse*1.5, g/255*pulse*1.5, b/255*pulse*1.5, 0.5)
                glBegin(GL_QUADS)
                offset = 0.1
                glVertex3f(-block_size/2 - offset, -offset, -block_size/2 - offset)
                glVertex3f(block_size/2 + offset, -offset, -block_size/2 - offset)
                glVertex3f(block_size/2 + offset, block_size + offset, -block_size/2 - offset)
                glVertex3f(-block_size/2 - offset, block_size + offset, -block_size/2 - offset)
                glEnd()
            
            glPopMatrix()
            glEnable(GL_LIGHTING)
        except Exception as e:
            print(f"绘制科技方块错误: {e}")
    
    def draw_tree(self, x, z, scale=1.0):
        try:
            glDisable(GL_LIGHTING)
            
            glPushMatrix()
            glTranslatef(x, -1, z)
            glScalef(scale, scale, scale)
            
            trunk_height = 3
            trunk_width = 0.3
            
            glColor3f(0.4, 0.25, 0.1)
            glBegin(GL_QUADS)
            glVertex3f(-trunk_width, 0, -trunk_width)
            glVertex3f(trunk_width, 0, -trunk_width)
            glVertex3f(trunk_width, trunk_height, -trunk_width)
            glVertex3f(-trunk_width, trunk_height, -trunk_width)
            
            glVertex3f(trunk_width, 0, -trunk_width)
            glVertex3f(trunk_width, 0, trunk_width)
            glVertex3f(trunk_width, trunk_height, trunk_width)
            glVertex3f(trunk_width, trunk_height, -trunk_width)
            
            glVertex3f(trunk_width, 0, trunk_width)
            glVertex3f(-trunk_width, 0, trunk_width)
            glVertex3f(-trunk_width, trunk_height, trunk_width)
            glVertex3f(trunk_width, trunk_height, trunk_width)
            
            glVertex3f(-trunk_width, 0, trunk_width)
            glVertex3f(-trunk_width, 0, -trunk_width)
            glVertex3f(-trunk_width, trunk_height, -trunk_width)
            glVertex3f(-trunk_width, trunk_height, trunk_width)
            glEnd()
            
            leaves_base = trunk_height + 0.5
            leaf_colors = [(0.2, 0.6, 0.2), (0.15, 0.55, 0.15), (0.25, 0.65, 0.25)]
            
            for layer, layer_height in enumerate([1.5, 1.2, 0.8]):
                y = leaves_base + layer * 0.6
                size = 2.0 - layer * 0.35
                color = leaf_colors[layer % len(leaf_colors)]
                glColor3f(*color)
                
                glBegin(GL_QUADS)
                glVertex3f(-size, y, -size)
                glVertex3f(size, y, -size)
                glVertex3f(size, y + layer_height, -size)
                glVertex3f(-size, y + layer_height, -size)
                
                glVertex3f(size, y, -size)
                glVertex3f(size, y, size)
                glVertex3f(size, y + layer_height, size)
                glVertex3f(size, y + layer_height, -size)
                
                glVertex3f(size, y, size)
                glVertex3f(-size, y, size)
                glVertex3f(-size, y + layer_height, size)
                glVertex3f(size, y + layer_height, size)
                
                glVertex3f(-size, y, size)
                glVertex3f(-size, y, -size)
                glVertex3f(-size, y + layer_height, -size)
                glVertex3f(-size, y + layer_height, size)
                glEnd()
            
            glPopMatrix()
            glEnable(GL_LIGHTING)
        except Exception as e:
            print(f"绘制树木错误: {e}")
    
    def draw_large_structure(self, struct):
        try:
            x, z = struct["x"], struct["z"]
            size = struct["size"]
            height = struct["height"]
            color = struct["color"]
            
            glPushMatrix()
            glTranslatef(x, 0, z)
            
            glDisable(GL_LIGHTING)
            
            glColor3f(*color)
            
            glBegin(GL_QUADS)
            glVertex3f(-size/2, 0, -size/2)
            glVertex3f(size/2, 0, -size/2)
            glVertex3f(size/2, height, -size/2)
            glVertex3f(-size/2, height, -size/2)
            
            glVertex3f(size/2, 0, -size/2)
            glVertex3f(size/2, 0, size/2)
            glVertex3f(size/2, height, size/2)
            glVertex3f(size/2, height, -size/2)
            
            glVertex3f(size/2, 0, size/2)
            glVertex3f(-size/2, 0, size/2)
            glVertex3f(-size/2, height, size/2)
            glVertex3f(size/2, height, size/2)
            
            glVertex3f(-size/2, 0, size/2)
            glVertex3f(-size/2, 0, -size/2)
            glVertex3f(-size/2, height, -size/2)
            glVertex3f(-size/2, height, size/2)
            glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制大型结构错误: {e}")
    
    def draw_location(self, loc):
        try:
            x, z = loc["x"], loc["y"]
            loc_type = loc.get("type", "矿产")
            color = loc.get("color", (0.6, 0.5, 0.4))
            owner = loc.get("owner", "neutral")
            height = loc.get("height", 8)
            rotation_id = loc.get("rotation_id", 0)
            
            facing_id = self.calculate_facing_id(loc)
            
            glPushMatrix()
            glTranslatef(x, 0, z)
            
            glRotatef(rotation_id * 90, 0, 1, 0)
            
            glDisable(GL_LIGHTING)
            
            base_width = 15
            base_depth = 15
            base_height = 2
            
            if owner == "player":
                glColor3f(0.3, 0.6, 0.3)
            elif owner == "enemy":
                glColor3f(0.6, 0.3, 0.3)
            else:
                glColor3f(*color)
            
            glBegin(GL_QUADS)
            glVertex3f(-base_width/2, 0, -base_depth/2)
            glVertex3f(base_width/2, 0, -base_depth/2)
            glVertex3f(base_width/2, base_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height, -base_depth/2)
            
            glVertex3f(base_width/2, 0, -base_depth/2)
            glVertex3f(base_width/2, 0, base_depth/2)
            glVertex3f(base_width/2, base_height, base_depth/2)
            glVertex3f(base_width/2, base_height, -base_depth/2)
            
            glVertex3f(base_width/2, 0, base_depth/2)
            glVertex3f(-base_width/2, 0, base_depth/2)
            glVertex3f(-base_width/2, base_height, base_depth/2)
            glVertex3f(base_width/2, base_height, base_depth/2)
            
            glVertex3f(-base_width/2, 0, base_depth/2)
            glVertex3f(-base_width/2, 0, -base_depth/2)
            glVertex3f(-base_width/2, base_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height, base_depth/2)
            glEnd()
            
            wall_height = height
            facing_colors = {
                0: (color[0] * 1.2, color[1] * 1.2, color[2] * 1.2),
                1: (color[0] * 0.9, color[1] * 0.9, color[2] * 0.9),
                2: (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8),
                3: (color[0] * 0.7, color[1] * 0.7, color[2] * 0.7)
            }
            facing_color = facing_colors.get(facing_id, color)
            glColor3f(*facing_color)
            
            glBegin(GL_QUADS)
            glVertex3f(-base_width/2, base_height, -base_depth/2)
            glVertex3f(base_width/2, base_height, -base_depth/2)
            glVertex3f(base_width/2, base_height + wall_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height + wall_height, -base_depth/2)
            
            glVertex3f(base_width/2, base_height, -base_depth/2)
            glVertex3f(base_width/2, base_height, base_depth/2)
            glVertex3f(base_width/2, base_height + wall_height, base_depth/2)
            glVertex3f(base_width/2, base_height + wall_height, -base_depth/2)
            
            glVertex3f(base_width/2, base_height, base_depth/2)
            glVertex3f(-base_width/2, base_height, base_depth/2)
            glVertex3f(-base_width/2, base_height + wall_height, base_depth/2)
            glVertex3f(base_width/2, base_height + wall_height, base_depth/2)
            
            glVertex3f(-base_width/2, base_height, base_depth/2)
            glVertex3f(-base_width/2, base_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height + wall_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height + wall_height, base_depth/2)
            glEnd()
            
            if owner == "player":
                glColor3f(0.8, 0.8, 0)
                glBegin(GL_LINE_LOOP)
                glVertex3f(-base_width/2 - 2, base_height + wall_height + 5, -base_depth/2 - 2)
                glVertex3f(base_width/2 + 2, base_height + wall_height + 5, -base_depth/2 - 2)
                glVertex3f(base_width/2 + 2, base_height + wall_height + 5, base_depth/2 + 2)
                glVertex3f(-base_width/2 - 2, base_height + wall_height + 5, base_depth/2 + 2)
                glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制地点错误: {e}")
    
    def draw_enemy(self, enemy):
        try:
            glPushMatrix()
            glTranslatef(enemy["x"], 0, enemy["z"])
            
            glDisable(GL_LIGHTING)
            glColor3f(*enemy["color"])
            
            glBegin(GL_QUADS)
            glVertex3f(-0.5, 0, -0.5)
            glVertex3f(0.5, 0, -0.5)
            glVertex3f(0.5, 1.8, -0.5)
            glVertex3f(-0.5, 1.8, -0.5)
            
            glVertex3f(0.5, 0, -0.5)
            glVertex3f(0.5, 0, 0.5)
            glVertex3f(0.5, 1.8, 0.5)
            glVertex3f(0.5, 1.8, -0.5)
            
            glVertex3f(0.5, 0, 0.5)
            glVertex3f(-0.5, 0, 0.5)
            glVertex3f(-0.5, 1.8, 0.5)
            glVertex3f(0.5, 1.8, 0.5)
            
            glVertex3f(-0.5, 0, 0.5)
            glVertex3f(-0.5, 0, -0.5)
            glVertex3f(-0.5, 1.8, -0.5)
            glVertex3f(-0.5, 1.8, 0.5)
            glEnd()
            
            if enemy["health"] < enemy["max_health"]:
                health_percent = enemy["health"] / enemy["max_health"]
                glColor3f(1, 0, 0)
                glBegin(GL_LINES)
                glVertex3f(-0.6, 2.2, 0)
                glVertex3f(-0.6 + 1.2 * health_percent, 2.2, 0)
                glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制敌人错误: {e}")
    
    def draw_general(self, general):
        try:
            glPushMatrix()
            glTranslatef(general["x"], 0, general["z"])
            
            glDisable(GL_LIGHTING)
            glColor3f(*general.get("color", (0.8, 0.6, 0.2)))
            
            glBegin(GL_QUADS)
            glVertex3f(-0.6, 0, -0.6)
            glVertex3f(0.6, 0, -0.6)
            glVertex3f(0.6, 2.0, -0.6)
            glVertex3f(-0.6, 2.0, -0.6)
            
            glVertex3f(0.6, 0, -0.6)
            glVertex3f(0.6, 0, 0.6)
            glVertex3f(0.6, 2.0, 0.6)
            glVertex3f(0.6, 2.0, -0.6)
            
            glVertex3f(0.6, 0, 0.6)
            glVertex3f(-0.6, 0, 0.6)
            glVertex3f(-0.6, 2.0, 0.6)
            glVertex3f(0.6, 2.0, 0.6)
            
            glVertex3f(-0.6, 0, 0.6)
            glVertex3f(-0.6, 0, -0.6)
            glVertex3f(-0.6, 2.0, -0.6)
            glVertex3f(-0.6, 2.0, 0.6)
            glEnd()
            
            if general.get("weapon"):
                glColor3f(0.6, 0.6, 0.6)
                glBegin(GL_LINES)
                glVertex3f(0.6, 1.2, 0)
                glVertex3f(1.2, 1.2, 0)
                glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制武将错误: {e}")
    
    def draw_pet(self, pet):
        try:
            glPushMatrix()
            glTranslatef(pet["x"], 0, pet["z"])
            
            glDisable(GL_LIGHTING)
            glColor3f(*pet.get("color", (0.6, 0.4, 0.2)))
            
            size = pet.get("size", 1.0)
            glScalef(size, size, size)
            
            glBegin(GL_QUADS)
            glVertex3f(-0.4, 0, -0.4)
            glVertex3f(0.4, 0, -0.4)
            glVertex3f(0.4, 1.0, -0.4)
            glVertex3f(-0.4, 1.0, -0.4)
            glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制宠物错误: {e}")
    
    def draw_npc(self, npc):
        try:
            glPushMatrix()
            glTranslatef(npc["x"], npc["y"], npc["z"])
            
            glDisable(GL_LIGHTING)
            
            bounce = math.sin(npc["animation_offset"]) * 0.2
            
            glColor3f(*npc["color"])
            
            body_height = 1.8
            body_width = 0.4
            body_depth = 0.3
            
            glTranslatef(0, body_height/2 + bounce, 0)
            
            glBegin(GL_QUADS)
            glVertex3f(-body_width/2, -body_height/2, -body_depth/2)
            glVertex3f(body_width/2, -body_height/2, -body_depth/2)
            glVertex3f(body_width/2, body_height/2, -body_depth/2)
            glVertex3f(-body_width/2, body_height/2, -body_depth/2)
            
            glVertex3f(body_width/2, -body_height/2, -body_depth/2)
            glVertex3f(body_width/2, -body_height/2, body_depth/2)
            glVertex3f(body_width/2, body_height/2, body_depth/2)
            glVertex3f(body_width/2, body_height/2, -body_depth/2)
            
            glVertex3f(body_width/2, -body_height/2, body_depth/2)
            glVertex3f(-body_width/2, -body_height/2, body_depth/2)
            glVertex3f(-body_width/2, body_height/2, body_depth/2)
            glVertex3f(body_width/2, body_height/2, body_depth/2)
            
            glVertex3f(-body_width/2, -body_height/2, body_depth/2)
            glVertex3f(-body_width/2, -body_height/2, -body_depth/2)
            glVertex3f(-body_width/2, body_height/2, -body_depth/2)
            glVertex3f(-body_width/2, body_height/2, body_depth/2)
            glEnd()
            
            distance_to_player = math.hypot(
                npc["x"] - self.player_pos[0],
                npc["z"] - self.player_pos[2]
            )
            
            if distance_to_player <= self.npc_interaction_distance:
                glColor3f(1.0, 1.0, 0.0)
                glBegin(GL_LINE_LOOP)
                for i in range(12):
                    angle = i * math.pi * 2 / 12
                    r = 1.2
                    glVertex3f(r * math.cos(angle), 2.5 + math.sin(time.time() * 3) * 0.2, r * math.sin(angle))
                glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制NPC错误: {e}")
    
    def draw_player(self):
        try:
            glPushMatrix()
            player_x, player_y, player_z = self.player_pos[0], self.player_pos[1], self.player_pos[2]
            glTranslatef(player_x, player_y, player_z)
            
            glDisable(GL_LIGHTING)
            
            glColor3f(0.2, 0.4, 0.8)
            glBegin(GL_QUADS)
            glVertex3f(-0.25, 0, -0.15)
            glVertex3f(0.25, 0, -0.15)
            glVertex3f(0.25, 1.8, -0.15)
            glVertex3f(-0.25, 1.8, -0.15)
            
            glVertex3f(0.25, 0, -0.15)
            glVertex3f(0.25, 0, 0.15)
            glVertex3f(0.25, 1.8, 0.15)
            glVertex3f(0.25, 1.8, -0.15)
            
            glVertex3f(0.25, 0, 0.15)
            glVertex3f(-0.25, 0, 0.15)
            glVertex3f(-0.25, 1.8, 0.15)
            glVertex3f(0.25, 1.8, 0.15)
            
            glVertex3f(-0.25, 0, 0.15)
            glVertex3f(-0.25, 0, -0.15)
            glVertex3f(-0.25, 1.8, -0.15)
            glVertex3f(-0.25, 1.8, 0.15)
            glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制玩家错误: {e}")
    
    def draw_follower(self, follower):
        try:
            glPushMatrix()
            glTranslatef(follower["x"], follower["y"], follower["z"])
            
            glDisable(GL_LIGHTING)
            
            glColor3f(0.6, 0.8, 0.4)
            
            glBegin(GL_QUADS)
            glVertex3f(-0.75, 0, -0.75)
            glVertex3f(0.75, 0, -0.75)
            glVertex3f(0.75, 1.5, -0.75)
            glVertex3f(-0.75, 1.5, -0.75)
            
            glVertex3f(0.75, 0, -0.75)
            glVertex3f(0.75, 0, 0.75)
            glVertex3f(0.75, 1.5, 0.75)
            glVertex3f(0.75, 1.5, -0.75)
            
            glVertex3f(0.75, 0, 0.75)
            glVertex3f(-0.75, 0, 0.75)
            glVertex3f(-0.75, 1.5, 0.75)
            glVertex3f(0.75, 1.5, 0.75)
            
            glVertex3f(-0.75, 0, 0.75)
            glVertex3f(-0.75, 0, -0.75)
            glVertex3f(-0.75, 1.5, -0.75)
            glVertex3f(-0.75, 1.5, 0.75)
            glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制跟随者错误: {e}")
    
    def draw_hud(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        pos_text = f"位置: ({int(self.player_pos[0])}, {int(self.player_pos[1])}, {int(self.player_pos[2])})"
        pos_surf = self.font_small.render(pos_text, True, COLORS["text_white"])
        self.screen.blit(pos_surf, (10, 10))
        
        if self.follow_target:
            follow_text = f"跟随: {self.follow_target.get('type', '位置')}"
            follow_surf = self.font_small.render(follow_text, True, COLORS["accent_green"])
            self.screen.blit(follow_surf, (10, 40))
        
        resources = data.get('resources', {})
        gold = resources.get('金元宝', 0)
        coal = resources.get('煤炭', 0)
        food = resources.get('食物', 0)
        water = resources.get('水', 0)
        resource_text = f"金元宝:{gold} 煤炭:{coal} 食物:{food} 水:{water}"
        resource_surf = self.font_small.render(resource_text, True, COLORS["accent_gold"])
        self.screen.blit(resource_surf, (10, 70))
        
        owned_count = len([loc for loc in self.locations if loc.get('owner') == 'player'])
        total_count = len(self.locations)
        territory_text = f"占领地点: {owned_count}/{total_count}"
        territory_surf = self.font_small.render(territory_text, True, COLORS["accent_green"])
        self.screen.blit(territory_surf, (10, 100))
        
        if self.message and self.message_timer > 0:
            msg_surf = self.font_main.render(self.message, True, COLORS["accent_gold"])
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            self.screen.blit(msg_surf, msg_rect)
            self.message_timer -= self.clock.get_time()
            if self.message_timer < 0:
                self.message = None
        
        controls = [
            "WASD: 移动",
            "空格: 跳跃",
            "E: 进入地点",
            "R: 收集资源",
            "I: 背包",
            "M: 小地图",
            "Tab: 锁定鼠标",
            "F: 跟随模式",
            "F5: 切换视角",
            "Q: 给武将装备武器",
            "Shift+左键: 放置方块",
            "左键: 挖掘/攻击",
            "右键: 使用物品/交互"
        ]
        
        for i, control in enumerate(controls):
            control_surf = self.font_small.render(control, True, (200, 200, 200))
            self.screen.blit(control_surf, (SCREEN_WIDTH - 150, 10 + i * 25))
        
        glEnable(GL_DEPTH_TEST)
    
    def update_physics(self):
        self.velocity[1] += self.gravity
        
        self.velocity[0] *= self.friction
        self.velocity[2] *= self.friction
        
        if abs(self.velocity[0]) < 0.01:
            self.velocity[0] = 0
        if abs(self.velocity[2]) < 0.01:
            self.velocity[2] = 0
        
        self.player_pos[0] += self.velocity[0]
        self.player_pos[1] += self.velocity[1]
        self.player_pos[2] += self.velocity[2]
        
        if self.player_pos[1] < 0:
            self.player_pos[1] = 0
            self.velocity[1] = 0
        
        self.player_pos[0] = max(-1800, min(1800, self.player_pos[0]))
        self.player_pos[2] = max(-1800, min(1800, self.player_pos[2]))
        
        self.update_camera()
    
    def run(self):
        if not self.initialize():
            return
        
        running = True
        while running:
            self.clock.tick(60)
            
            running = self.handle_input()
            
            self.update_physics()
            self.update_npcs()
            self.update_followers()
            self.update_enemies()
            self.update_marketplace()
            self.update_projectiles()
            self.update_pickups()
            
            self.draw_3d_scene()
            
            if not self.inventory_open:
                self.draw_hud()
                self.draw_minimap()
                self.draw_hotbar()
            else:
                self.draw_inventory()
            
            pygame.display.flip()
        
        pygame.quit()

def main():
    game = GameMap3D()
    game.run()
