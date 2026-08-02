import os
import pygame
import random
import math
from ASSET.game_data import data, save, get_system_font_name
from ASSET.hero_database import EQUIPMENT_DATABASE
from ASSET import safe_exit

COLORS = {
    "bg_dark": (15, 20, 35),
    "bg_light": (25, 30, 50),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 220),
    "accent_green": (60, 200, 100),
    "accent_purple": (180, 100, 220),
    "accent_red": (220, 80, 80),
    "accent_orange": (255, 140, 50),
    "text_white": (255, 255, 255),
    "text_gray": (160, 170, 190),
    "panel_bg": (35, 40, 60, 230),
    "btn_green": (50, 160, 80),
    "btn_green_hover": (70, 200, 100),
    "btn_blue": (60, 120, 200),
    "btn_blue_hover": (80, 160, 255),
    "btn_gold": (200, 160, 50),
    "btn_gold_hover": (255, 200, 80),
    "btn_purple": (160, 80, 200),
    "btn_purple_hover": (200, 100, 255),
    "quality_common": (150, 150, 150),
    "quality_rare": (70, 130, 180),
    "quality_epic": (128, 0, 128),
    "quality_legendary": (255, 215, 0),
    "quality_mythic": (255, 50, 50)
}

QUALITY_INFO = {
    "common": {"name": "普通", "color": COLORS["quality_common"], "multiplier": 1.0},
    "rare": {"name": "稀有", "color": COLORS["quality_rare"], "multiplier": 1.3},
    "epic": {"name": "史诗", "color": COLORS["quality_epic"], "multiplier": 1.6},
    "legendary": {"name": "传说", "color": COLORS["quality_legendary"], "multiplier": 2.0},
    "mythic": {"name": "神话", "color": COLORS["quality_mythic"], "multiplier": 3.0}
}

EQUIP_TYPES = {
    "weapon": {"name": "武器", "icon": "⚔️", "main_stat": "attack"},
    "armor": {"name": "防具", "icon": "🛡️", "main_stat": "defense"},
    "accessory": {"name": "饰品", "icon": "💍", "main_stat": "critical"},
    "boots": {"name": "靴子", "icon": "👢", "main_stat": "speed"},
    "helmet": {"name": "头盔", "icon": "⛑️", "main_stat": "health"}
}

REFINE_LEVELS = [
    {"level": 0, "name": "普通", "bonus": 0.0, "cost": {}},
    {"level": 1, "name": "+1", "bonus": 0.1, "cost": {"精炼石": 1, "金元宝": 50}},
    {"level": 2, "name": "+2", "bonus": 0.2, "cost": {"精炼石": 2, "金元宝": 100}},
    {"level": 3, "name": "精炼", "bonus": 0.35, "cost": {"精炼石": 5, "金元宝": 200}},
    {"level": 4, "name": "+4", "bonus": 0.5, "cost": {"精炼石": 10, "金元宝": 500}},
    {"level": 5, "name": "+5", "bonus": 0.7, "cost": {"精炼石": 20, "金元宝": 1000}},
    {"level": 6, "name": "精铸", "bonus": 1.0, "cost": {"高级精炼石": 5, "金元宝": 2000}},
    {"level": 7, "name": "+7", "bonus": 1.3, "cost": {"高级精炼石": 10, "金元宝": 5000}},
    {"level": 8, "name": "+8", "bonus": 1.6, "cost": {"高级精炼石": 20, "金元宝": 10000}},
    {"level": 9, "name": "神铸", "bonus": 2.0, "cost": {"顶级精炼石": 10, "金元宝": 20000}},
    {"level": 10, "name": "传说", "bonus": 2.5, "cost": {"顶级精炼石": 20, "金元宝": 50000}}
]

GEM_TYPES = {
    "ruby": {"name": "红宝石", "color": (255, 80, 80), "effect": {"attack": 50}, "slot": "weapon"},
    "sapphire": {"name": "蓝宝石", "color": (80, 150, 255), "effect": {"defense": 30}, "slot": "armor"},
    "emerald": {"name": "绿宝石", "color": (80, 200, 100), "effect": {"health": 200}, "slot": "helmet"},
    "topaz": {"name": "黄宝石", "color": (255, 200, 80), "effect": {"critical": 0.05}, "slot": "accessory"},
    "amethyst": {"name": "紫水晶", "color": (180, 100, 220), "effect": {"speed": 10}, "slot": "boots"},
    "diamond": {"name": "钻石", "color": (200, 200, 220), "effect": {"attack": 100, "critical": 0.03}, "slot": "all"}
}

SETS = {
    "dragon_set": {
        "name": "龙鳞套装",
        "description": "传说中的龙鳞制成的套装，拥有强大的防御能力",
        "parts": ["龙鳞铠甲", "龙鳞头盔", "龙鳞靴子"],
        "bonuses": {
            2: {"defense": 0.2, "health": 0.1},
            3: {"defense": 0.4, "health": 0.2, "damage_reduction": 0.1}
        },
        "bonus_description": {
            2: "装备2件：防御力+20%，生命值+10%",
            3: "装备3件：防御力+40%，生命值+20%，减伤+10%"
        }
    },
    "phoenix_set": {
        "name": "凤凰套装",
        "description": "浴火重生的凤凰之火淬炼而成，攻击力惊人",
        "parts": ["凤凰之剑", "凤凰护符", "凤凰战靴"],
        "bonuses": {
            2: {"attack": 0.25, "critical": 0.05},
            3: {"attack": 0.5, "critical": 0.1, "burn_damage": 50}
        },
        "bonus_description": {
            2: "装备2件：攻击力+25%，暴击率+5%",
            3: "装备3件：攻击力+50%，暴击率+10%，攻击附带灼烧"
        }
    },
    "tiger_set": {
        "name": "猛虎套装",
        "description": "以猛虎之力锻造，攻守兼备",
        "parts": ["虎牙之刃", "虎皮战甲", "虎爪护符"],
        "bonuses": {
            2: {"attack": 0.15, "defense": 0.15},
            3: {"attack": 0.3, "defense": 0.3, "attack_speed": 0.2}
        },
        "bonus_description": {
            2: "装备2件：攻击力+15%，防御力+15%",
            3: "装备3件：攻击力+30%，防御力+30%，攻速+20%"
        }
    },
    "turtle_set": {
        "name": "玄武套装",
        "description": "玄武之力加持，坚如磐石",
        "parts": ["玄武护盾", "玄武头盔", "玄武护符"],
        "bonuses": {
            2: {"health": 0.3, "defense": 0.1},
            3: {"health": 0.6, "defense": 0.25, "heal_regen": 20}
        },
        "bonus_description": {
            2: "装备2件：生命值+30%，防御力+10%",
            3: "装备3件：生命值+60%，防御力+25%，每秒回血20"
        }
    }
}

FORGE_RECIPES = {
    "dragon_scale": {
        "name": "龙鳞",
        "materials": {"铁锭": 10, "皮革": 5, "宝石": 2},
        "result": "龙鳞铠甲",
        "quality": "epic"
    },
    "phoenix_feather": {
        "name": "凤凰之羽",
        "materials": {"精钢": 8, "火焰精华": 3, "宝石": 3},
        "result": "凤凰之剑",
        "quality": "legendary"
    },
    "tiger_bone": {
        "name": "虎骨",
        "materials": {"铁锭": 6, "皮革": 8, "宝石": 1},
        "result": "虎皮战甲",
        "quality": "rare"
    },
    "turtle_shell": {
        "name": "玄武壳",
        "materials": {"精钢": 10, "皮革": 10, "宝石": 2},
        "result": "玄武护盾",
        "quality": "epic"
    }
}

class Particle:
    def __init__(self, x, y, color, speed, size, life):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = random.uniform(-speed, speed)
        self.speed_y = random.uniform(-speed, speed)
        self.size = size
        self.life = life
        self.max_life = life
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        self.size = max(0.5, self.size - 0.05)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color[:3], alpha)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

class Button:
    def __init__(self, text, x, y, width, height, font, normal_color=COLORS["btn_blue"], hover_color=COLORS["btn_blue_hover"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.is_hovered = False
    
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.normal_color
        
        for i in range(self.rect.height):
            ratio = i / self.rect.height
            r = int(color[0] * (1 - ratio * 0.3))
            g = int(color[1] * (1 - ratio * 0.3))
            b = int(color[2] * (1 - ratio * 0.3))
            pygame.draw.line(surface, (r, g, b), 
                           (self.rect.x, self.rect.y + i), 
                           (self.rect.x + self.rect.width, self.rect.y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class EquipmentManagementSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "equipment_management" not in data:
            data["equipment_management"] = {
                "inventory": [],
                "equipped": {},
                "refined": {},
                "gemmed": {},
                "sets": {}
            }
        
        if "equips" in data and isinstance(data["equips"], dict):
            for equip_type, equip_id in data["equips"].items():
                if equip_id > 0 and equip_type in EQUIP_TYPES:
                    equip_name = self._get_equip_name(equip_type, equip_id)
                    if equip_name:
                        if equip_name not in data["equipment_management"]["inventory"]:
                            data["equipment_management"]["inventory"].append(equip_name)
                        data["equipment_management"]["equipped"][equip_type] = equip_name
            
            if "hero_guns" in data:
                for hero_name, gun_info in data["hero_guns"].items():
                    if gun_info.get("gun_type"):
                        gun_name = gun_info["gun_type"]
                        if gun_name not in data["equipment_management"]["inventory"]:
                            data["equipment_management"]["inventory"].append(gun_name)
            save()
    
    def _get_equip_name(self, equip_type, equip_id):
        equip_names = {
            "weapon": ["铁剑", "精钢剑", "烈焰剑", "雷霆剑", "龙渊剑", "轩辕剑", "凤凰之剑", "虎牙之刃"],
            "armor": ["皮甲", "铁甲", "锁子甲", "板甲", "龙鳞铠甲", "玄武护盾", "虎皮战甲"],
            "horse": ["骏马", "千里马", "汗血宝马", "赤兔马", "的卢"],
            "book": ["兵法", "天书", "奇门遁甲", "孙子兵法", "遁甲天书"],
            "accessory": ["戒指", "项链", "护符", "凤凰护符", "虎爪护符", "玄武护符"],
            "boots": ["布鞋", "皮靴", "铁靴", "疾风靴", "凤凰战靴"],
            "helmet": ["皮帽", "铁盔", "钢盔", "龙鳞头盔", "玄武头盔"]
        }
        names = equip_names.get(equip_type, [])
        if equip_id - 1 < len(names):
            return names[equip_id - 1]
        return None
    
    def get_inventory(self):
        return data["equipment_management"]["inventory"]
    
    def get_equipped(self):
        return data["equipment_management"]["equipped"]
    
    def get_refine_level(self, equip_name):
        return data["equipment_management"]["refined"].get(equip_name, 0)
    
    def get_gems(self, equip_name):
        return data["equipment_management"]["gemmed"].get(equip_name, [])
    
    def calculate_equip_stats(self, equip_name):
        equip_type = self._get_equip_type(equip_name)
        if not equip_type:
            return None
        
        base_stats = {
            "attack": 100,
            "defense": 80,
            "health": 200,
            "critical": 0.05,
            "speed": 10
        }
        
        quality = self._get_equip_quality(equip_name)
        quality_multiplier = QUALITY_INFO[quality]["multiplier"]
        
        for stat in base_stats:
            base_stats[stat] *= quality_multiplier
        
        refine_level = self.get_refine_level(equip_name)
        if refine_level > 0:
            refine_index = min(refine_level, len(REFINE_LEVELS) - 1)
            refine_bonus = REFINE_LEVELS[refine_index]["bonus"]
            main_stat = EQUIP_TYPES[equip_type]["main_stat"]
            if main_stat in base_stats:
                if main_stat == "critical" or main_stat == "speed":
                    base_stats[main_stat] += refine_bonus
                else:
                    base_stats[main_stat] *= (1 + refine_bonus)
        
        gems = self.get_gems(equip_name)
        for gem_type in gems:
            gem = GEM_TYPES.get(gem_type, {})
            for stat, value in gem.get("effect", {}).items():
                if stat in base_stats:
                    base_stats[stat] += value
        
        return {
            "name": equip_name,
            "type": equip_type,
            "quality": quality,
            "refine_level": refine_level,
            "gems": gems,
            "stats": base_stats,
            "power": int(base_stats["attack"] + base_stats["defense"] + base_stats["health"])
        }
    
    def _get_equip_type(self, equip_name):
        for equip_type, info in EQUIP_TYPES.items():
            if equip_name in [
                "铁剑", "精钢剑", "烈焰剑", "雷霆剑", "龙渊剑", "轩辕剑", "凤凰之剑", "虎牙之刃"
            ]:
                return "weapon"
            elif equip_name in [
                "皮甲", "铁甲", "锁子甲", "板甲", "龙鳞铠甲", "玄武护盾", "虎皮战甲"
            ]:
                return "armor"
            elif equip_name in ["戒指", "项链", "护符", "凤凰护符", "虎爪护符", "玄武护符"]:
                return "accessory"
            elif equip_name in ["布鞋", "皮靴", "铁靴", "疾风靴", "凤凰战靴"]:
                return "boots"
            elif equip_name in ["皮帽", "铁盔", "钢盔", "龙鳞头盔", "玄武头盔"]:
                return "helmet"
        return None
    
    def _get_equip_quality(self, equip_name):
        # 从EQUIPMENT_DATABASE获取品质，覆盖全部59件装备
        equip_info = EQUIPMENT_DATABASE.get(equip_name, {})
        return equip_info.get("rarity", "common")
    
    def can_refine(self, equip_name):
        current_level = self.get_refine_level(equip_name)
        if current_level >= len(REFINE_LEVELS) - 1:
            return False, "已达到最高精炼等级"
        
        cost = REFINE_LEVELS[current_level + 1]["cost"]
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        return True, "可以精炼"
    
    def refine_equip(self, equip_name):
        can_do, msg = self.can_refine(equip_name)
        if not can_do:
            return False, msg
        
        current_level = self.get_refine_level(equip_name)
        cost = REFINE_LEVELS[current_level + 1]["cost"]
        
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        data["equipment_management"]["refined"][equip_name] = current_level + 1
        save()
        
        new_level_name = REFINE_LEVELS[current_level + 1]["name"]
        return True, f"精炼成功！{equip_name} {new_level_name}"
    
    def can_gem(self, equip_name, gem_type):
        gems = self.get_gems(equip_name)
        if len(gems) >= 3:
            return False, "已达到最大镶嵌数量"
        
        if gem_type in gems:
            return False, "已镶嵌相同类型宝石"
        
        gem = GEM_TYPES.get(gem_type, {})
        equip_type = self._get_equip_type(equip_name)
        
        if gem.get("slot") != "all" and gem.get("slot") != equip_type:
            return False, f"{gem.get('name', '')}只能镶嵌在{gem.get('slot', '')}上"
        
        return True, "可以镶嵌"
    
    def gem_equip(self, equip_name, gem_type):
        can_do, msg = self.can_gem(equip_name, gem_type)
        if not can_do:
            return False, msg
        
        gems = self.get_gems(equip_name)
        gems.append(gem_type)
        data["equipment_management"]["gemmed"][equip_name] = gems
        save()
        
        gem = GEM_TYPES.get(gem_type, {})
        return True, f"镶嵌成功！{gem.get('name', '')}"
    
    def get_set_bonuses(self):
        equipped = self.get_equipped()
        equipped_names = list(equipped.values())
        
        active_bonuses = []
        for set_id, set_data in SETS.items():
            parts = set_data["parts"]
            matched = [part for part in parts if part in equipped_names]
            count = len(matched)
            
            if count >= 2:
                bonus_levels = sorted(set_data["bonuses"].keys())
                for level in bonus_levels:
                    if count >= level:
                        active_bonuses.append({
                            "set_name": set_data["name"],
                            "description": set_data["bonus_description"][level],
                            "count": count,
                            "total_parts": len(parts),
                            "bonus": set_data["bonuses"][level]
                        })
        
        return active_bonuses
    
    def can_forge(self, recipe_id):
        recipe = FORGE_RECIPES.get(recipe_id, {})
        if not recipe:
            return False, "配方不存在"
        
        materials = recipe.get("materials", {})
        for material, amount in materials.items():
            if data["resources"].get(material, 0) < amount:
                return False, f"材料不足：{material}"
        
        return True, "可以锻造"
    
    def forge_equip(self, recipe_id):
        can_do, msg = self.can_forge(recipe_id)
        if not can_do:
            return False, msg
        
        recipe = FORGE_RECIPES[recipe_id]
        materials = recipe["materials"]
        
        for material, amount in materials.items():
            data["resources"][material] -= amount
        
        result = recipe["result"]
        if result not in data["equipment_management"]["inventory"]:
            data["equipment_management"]["inventory"].append(result)
        
        save()
        return True, f"锻造成功！获得{recipe['quality']}装备：{result}"

def draw_gradient_background(surface, color1, color2):
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_title(surface, text, y, screen_width, font):
    for offset in range(5, 0, -1):
        alpha = 50 - offset * 8
        glow_surf = font.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    title = font.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y))
    
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)

def draw_equip_card(surface, equip_stats, x, y, width, height, font_main, font_small):
    bg_color = QUALITY_INFO[equip_stats["quality"]]["color"]
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (*bg_color[:3], 150), (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, bg_color, (x, y, width, height), 2, border_radius=12)
    
    equip_type = EQUIP_TYPES.get(equip_stats["type"], {})
    icon = equip_type.get("icon", "📦")
    icon_font = pygame.font.Font(None, 45)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + width // 2, y + 35))
    surface.blit(icon_surf, icon_rect)
    
    name_surf = font_main.render(equip_stats["name"], True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + width // 2, y + 80))
    surface.blit(name_surf, name_rect)
    
    type_text = equip_type.get("name", "未知")
    type_surf = font_small.render(type_text, True, COLORS["text_white"])
    surface.blit(type_surf, (x + 10, y + 110))
    
    refine_level = equip_stats["refine_level"]
    if refine_level > 0:
        refine_name = REFINE_LEVELS[refine_level]["name"]
        refine_text = f"精炼{refine_name}"
        refine_surf = font_small.render(refine_text, True, COLORS["accent_green"])
        surface.blit(refine_surf, (x + width - 10 - refine_surf.get_width(), y + 110))
    
    gems = equip_stats["gems"]
    if gems:
        gems_text = " ".join([GEM_TYPES.get(g, {}).get("name", g)[:2] for g in gems])
        gems_surf = font_small.render(f"宝石: {gems_text}", True, COLORS["accent_purple"])
        surface.blit(gems_surf, (x + 10, y + 135))
    
    power_text = font_main.render(f"战力: {equip_stats['power']}", True, COLORS["accent_gold"])
    power_rect = power_text.get_rect(center=(x + width // 2, y + 165))
    surface.blit(power_text, power_rect)
    
    stats = equip_stats["stats"]
    stat_y = y + 195
    stat_items = [("⚔️", "攻击", int(stats["attack"])), ("🛡️", "防御", int(stats["defense"])), ("❤️", "生命", int(stats["health"]))]
    for icon, name, value in stat_items:
        stat_text = f"{icon} {name}: {value}"
        stat_surf = font_small.render(stat_text, True, COLORS["text_white"])
        surface.blit(stat_surf, (x + 15, stat_y))
        stat_y += 20

def main():
    try:
        if not pygame.get_init():
            pygame.init()
        
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 900
                SCREEN_HEIGHT = 700
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("装备管理")
        clock = pygame.time.Clock()
        
        scale = min(SCREEN_WIDTH / 900, SCREEN_HEIGHT / 700)
        
        def init_font(size):
            font_name = get_system_font_name()
            adjusted_size = int(size * scale)
            try:
                return pygame.font.SysFont(font_name, adjusted_size)
            except Exception:
                return pygame.font.Font(None, adjusted_size)
        
        font_title = init_font(48)
        font_main = init_font(28)
        font_small = init_font(22)
        
        equip_management = EquipmentManagementSystem()
        
        particles = []
        
        current_tab = "inventory"
        tabs = ["inventory", "refine", "forge", "gem", "sets"]
        tab_names = ["装备背包", "精炼", "锻造", "镶嵌", "套装"]
        
        selected_equip = None
        message = ""
        show_message = False
        message_timer = 0
        
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            if random.random() < 0.05:
                particles.append(Particle(
                    random.randint(0, SCREEN_WIDTH),
                    random.randint(0, SCREEN_HEIGHT),
                    COLORS["accent_gold"], 0.5, 2, 100
                ))
            
            for p in particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    particles.remove(p)
            
            draw_title(screen, "装备管理", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            tab_y = SCREEN_HEIGHT * 0.18
            tab_width = 110
            tab_height = 45
            tab_start_x = (SCREEN_WIDTH - len(tabs) * (tab_width + 15)) // 2
            
            tab_buttons = []
            for i, (tab_id, tab_name) in enumerate(zip(tabs, tab_names)):
                x = tab_start_x + i * (tab_width + 15)
                is_selected = current_tab == tab_id
                btn_color = COLORS["btn_gold"] if is_selected else COLORS["btn_blue"]
                hover_color = COLORS["btn_gold_hover"] if is_selected else COLORS["btn_blue_hover"]
                
                btn = Button(tab_name, x, tab_y, tab_width, tab_height, font_small, btn_color, hover_color)
                btn.update((mx, my))
                btn.draw(screen)
                tab_buttons.append((btn, tab_id))
            
            content_y = SCREEN_HEIGHT * 0.28
            
            inventory = equip_management.get_inventory()
            
            if current_tab == "inventory":
                if inventory:
                    card_width = min(180, SCREEN_WIDTH * 0.2)
                    card_height = min(250, SCREEN_HEIGHT * 0.33)
                    cols = min(4, SCREEN_WIDTH // (card_width + 20))
                    start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 20)) // 2
                    
                    equip_buttons = []
                    for i, equip_name in enumerate(inventory):
                        row = i // cols
                        col = i % cols
                        x = start_x + col * (card_width + 20)
                        y = content_y + row * (card_height + 20)
                        
                        stats = equip_management.calculate_equip_stats(equip_name)
                        if stats:
                            draw_equip_card(screen, stats, x, y, card_width, card_height, font_main, font_small)
                            card_rect = pygame.Rect(x, y, card_width, card_height)
                            equip_buttons.append((card_rect, equip_name))
                else:
                    empty_text = font_main.render("暂无装备", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "refine":
                if inventory:
                    btn_width = min(200, SCREEN_WIDTH * 0.22)
                    btn_height = 50
                    start_x = (SCREEN_WIDTH - btn_width) // 2
                    
                    equip_buttons = []
                    for i, equip_name in enumerate(inventory):
                        y = content_y + i * (btn_height + 10)
                        if y > SCREEN_HEIGHT - 100:
                            break
                        
                        refine_level = equip_management.get_refine_level(equip_name)
                        refine_name = REFINE_LEVELS[refine_level]["name"]
                        
                        can_do, msg = equip_management.can_refine(equip_name)
                        if can_do:
                            next_level = REFINE_LEVELS[refine_level + 1]
                            btn_text = f"{equip_name} ({refine_name}) → {next_level['name']}"
                            btn_color = COLORS["btn_green"]
                            hover_color = COLORS["btn_green_hover"]
                        else:
                            btn_text = f"{equip_name} ({refine_name}) - {msg}"
                            btn_color = (100, 100, 120)
                            hover_color = (120, 120, 150)
                        
                        btn = Button(btn_text, start_x, y, btn_width, btn_height, font_small, btn_color, hover_color)
                        btn.update((mx, my))
                        btn.draw(screen)
                        equip_buttons.append((btn, equip_name, "refine"))
                else:
                    empty_text = font_main.render("暂无装备", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "forge":
                btn_width = min(250, SCREEN_WIDTH * 0.28)
                btn_height = 60
                start_x = (SCREEN_WIDTH - btn_width) // 2
                
                forge_buttons = []
                for i, (recipe_id, recipe) in enumerate(FORGE_RECIPES.items()):
                    y = content_y + i * (btn_height + 20)
                    if y > SCREEN_HEIGHT - 100:
                        break
                    
                    can_do, msg = equip_management.can_forge(recipe_id)
                    if can_do:
                        btn_text = f"🔨 {recipe['name']} → {recipe['result']}"
                        btn_color = COLORS["btn_orange"]
                        hover_color = (255, 180, 80)
                    else:
                        btn_text = f"🔨 {recipe['name']} → {recipe['result']} ({msg})"
                        btn_color = (100, 100, 120)
                        hover_color = (120, 120, 150)
                    
                    btn = Button(btn_text, start_x, y, btn_width, btn_height, font_small, btn_color, hover_color)
                    btn.update((mx, my))
                    btn.draw(screen)
                    forge_buttons.append((btn, recipe_id))
                    
                    materials = recipe.get("materials", {})
                    mat_text = ", ".join([f"{k}×{v}" for k, v in materials.items()])
                    mat_surf = font_small.render(f"材料: {mat_text}", True, COLORS["text_gray"])
                    screen.blit(mat_surf, (start_x, y + btn_height + 5))
            
            elif current_tab == "gem":
                if inventory:
                    btn_width = min(200, SCREEN_WIDTH * 0.22)
                    btn_height = 50
                    start_x = (SCREEN_WIDTH - btn_width) // 2
                    
                    equip_buttons = []
                    for i, equip_name in enumerate(inventory):
                        y = content_y + i * (btn_height + 10)
                        if y > SCREEN_HEIGHT - 150:
                            break
                        
                        gems = equip_management.get_gems(equip_name)
                        gem_text = ", ".join([GEM_TYPES.get(g, {}).get("name", g) for g in gems]) if gems else "无"
                        
                        btn_text = f"{equip_name} - 宝石: {gem_text}"
                        btn = Button(btn_text, start_x, y, btn_width, btn_height, font_small)
                        btn.update((mx, my))
                        btn.draw(screen)
                        equip_buttons.append((btn, equip_name))
                        
                        if len(gems) < 3:
                            gem_y = y + btn_height + 5
                            for gem_type, gem in GEM_TYPES.items():
                                can_do, msg = equip_management.can_gem(equip_name, gem_type)
                                if can_do:
                                    gem_btn = Button(f"💎 {gem['name']}", start_x + btn_width + 20, gem_y, 120, 35, font_small, COLORS["btn_purple"], COLORS["btn_purple_hover"])
                                    gem_btn.update((mx, my))
                                    gem_btn.draw(screen)
                                    equip_buttons.append((gem_btn, equip_name, "gem", gem_type))
                                    gem_y += 40
            elif current_tab == "sets":
                set_bonuses = equip_management.get_set_bonuses()
                
                if set_bonuses:
                    for i, bonus in enumerate(set_bonuses):
                        bg_color = (40, 70, 40, 200) if bonus["count"] == bonus["total_parts"] else (40, 40, 70, 200)
                        set_rect = pygame.Rect(50, content_y + i * 100, SCREEN_WIDTH - 100, 85)
                        pygame.draw.rect(screen, bg_color, set_rect, border_radius=12)
                        pygame.draw.rect(screen, COLORS["accent_gold"], set_rect, 2, border_radius=12)
                        
                        name_surf = font_main.render(f"✨ {bonus['set_name']}", True, COLORS["accent_gold"])
                        screen.blit(name_surf, (65, content_y + i * 100 + 15))
                        
                        desc_surf = font_small.render(bonus["description"], True, COLORS["text_white"])
                        screen.blit(desc_surf, (65, content_y + i * 100 + 45))
                        
                        progress_text = f"进度: {bonus['count']}/{bonus['total_parts']}"
                        progress_surf = font_small.render(progress_text, True, COLORS["accent_blue"])
                        screen.blit(progress_surf, (SCREEN_WIDTH - 150, content_y + i * 100 + 35))
                else:
                    empty_text = font_main.render("暂无激活的套装效果", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
                
                for set_id, set_data in SETS.items():
                    y = content_y + 250
                    set_rect = pygame.Rect(50, y, SCREEN_WIDTH - 100, 70)
                    pygame.draw.rect(screen, COLORS["panel_bg"], set_rect, border_radius=10)
                    pygame.draw.rect(screen, COLORS["accent_gold"], set_rect, 1, border_radius=10)
                    
                    name_surf = font_main.render(f"📦 {set_data['name']}", True, COLORS["text_white"])
                    screen.blit(name_surf, (65, y + 15))
                    
                    parts_text = ", ".join(set_data["parts"])
                    parts_surf = font_small.render(f"组成: {parts_text}", True, COLORS["text_gray"])
                    screen.blit(parts_surf, (65, y + 45))
            
            return_btn = Button("返回", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, font_main)
            return_btn.update((mx, my))
            return_btn.draw(screen)
            
            if show_message:
                message_surf = font_main.render(message, True, COLORS["accent_green"])
                message_rect = message_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.9))
                pygame.draw.rect(screen, (35, 40, 60, 230), 
                               (message_rect.x - 20, message_rect.y - 10, message_rect.width + 40, message_rect.height + 20), 
                               border_radius=8)
                screen.blit(message_surf, message_rect)
                message_timer += 1
                if message_timer > 60:
                    show_message = False
                    message_timer = 0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn, tab_id in tab_buttons:
                        if btn.rect.collidepoint(mx, my):
                            current_tab = tab_id
                            break
                    
                    if current_tab == "refine" and 'equip_buttons' in locals():
                        for btn, equip_name, action in equip_buttons:
                            if btn.rect.collidepoint(mx, my):
                                success, msg = equip_management.refine_equip(equip_name)
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                    
                    elif current_tab == "forge" and 'forge_buttons' in locals():
                        for btn, recipe_id in forge_buttons:
                            if btn.rect.collidepoint(mx, my):
                                success, msg = equip_management.forge_equip(recipe_id)
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                    
                    elif current_tab == "gem" and 'equip_buttons' in locals():
                        for item in equip_buttons:
                            if len(item) == 4:
                                btn, equip_name, action, gem_type = item
                                if btn.rect.collidepoint(mx, my):
                                    success, msg = equip_management.gem_equip(equip_name, gem_type)
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                    break
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("装备管理")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("装备管理", str(e))

if __name__ == "__main__":
    main()