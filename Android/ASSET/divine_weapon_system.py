import os
import pygame
import random
import math
from ASSET.game_data import data, save, get_system_font_name
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
    "divine_purple": (128, 0, 128),
    "divine_gold": (255, 215, 0),
    "divine_red": (255, 0, 0),
    "divine_blue": (0, 150, 255)
}

DIVINE_WEAPONS = {
    "guandu": {
        "name": "青龙偃月刀",
        "description": "关羽所持神兵，刀长九尺五寸，重八十二斤",
        "icon": "⚔️",
        "type": "blade",
        "rarity": "legendary",
        "base_stats": {"attack": 500, "critical": 0.2},
        "unique_skill": {
            "name": "青龙啸月",
            "description": "攻击时有20%概率召唤青龙虚影，造成200%伤害并附加灼烧效果",
            "trigger_rate": 0.2,
            "damage_multiplier": 2.0,
            "effect": "burn"
        },
        "growth": {"attack": 50, "critical": 0.02},
        "evolution_target": "qinglong_ascended"
    },
    "zhangfei": {
        "name": "丈八蛇矛",
        "description": "张飞所持神兵，矛长一丈八尺，如蛇般灵动",
        "icon": "🔱",
        "type": "spear",
        "rarity": "legendary",
        "base_stats": {"attack": 450, "speed": 30},
        "unique_skill": {
            "name": "蛇矛乱舞",
            "description": "攻击时有15%概率发动三连击，每击造成80%伤害",
            "trigger_rate": 0.15,
            "hits": 3,
            "damage_per_hit": 0.8
        },
        "growth": {"attack": 45, "speed": 5},
        "evolution_target": "shemang_ascended"
    },
    "zhaoyun": {
        "name": "龙胆亮银枪",
        "description": "赵云所持神兵，枪身闪烁银光，攻防兼备",
        "icon": "🏹",
        "type": "spear",
        "rarity": "legendary",
        "base_stats": {"attack": 420, "defense": 100, "speed": 20},
        "unique_skill": {
            "name": "龙胆守护",
            "description": "受到攻击时有25%概率触发护盾，吸收30%伤害",
            "trigger_rate": 0.25,
            "shield_absorb": 0.3
        },
        "growth": {"attack": 40, "defense": 15, "speed": 3},
        "evolution_target": "longdan_ascended"
    },
    "machao": {
        "name": "虎头湛金枪",
        "description": "马超所持神兵，枪头似虎，威力无穷",
        "icon": "🐯",
        "type": "spear",
        "rarity": "legendary",
        "base_stats": {"attack": 480, "critical": 0.15},
        "unique_skill": {
            "name": "猛虎下山",
            "description": "暴击时额外造成100%伤害，并击退敌人",
            "extra_damage": 1.0,
            "knockback": True
        },
        "growth": {"attack": 48, "critical": 0.015},
        "evolution_target": "huhu_ascended"
    },
    "huangzhong": {
        "name": "宝雕弓",
        "description": "黄忠所持神兵，弓力千钧，百步穿杨",
        "icon": "🎯",
        "type": "bow",
        "rarity": "legendary",
        "base_stats": {"attack": 380, "critical": 0.3},
        "unique_skill": {
            "name": "百步穿杨",
            "description": "攻击时有10%概率无视防御，直接造成真实伤害",
            "trigger_rate": 0.1,
            "true_damage": True
        },
        "growth": {"attack": 38, "critical": 0.03},
        "evolution_target": "baodiao_ascended"
    },
    "zhugekongming": {
        "name": "羽扇",
        "description": "诸葛亮所持神兵，扇出风云，决胜千里",
        "icon": "🪭",
        "type": "staff",
        "rarity": "legendary",
        "base_stats": {"attack": 300, "skill_damage": 0.5},
        "unique_skill": {
            "name": "奇门遁甲",
            "description": "技能伤害提升50%，并有30%概率使敌人混乱",
            "skill_bonus": 0.5,
            "confusion_rate": 0.3
        },
        "growth": {"attack": 30, "skill_damage": 0.05},
        "evolution_target": "yushan_ascended"
    },
    "caocao": {
        "name": "倚天剑",
        "description": "曹操所持神兵，剑出倚天，号令天下",
        "icon": "🗡️",
        "type": "sword",
        "rarity": "legendary",
        "base_stats": {"attack": 400, "leadership": 100},
        "unique_skill": {
            "name": "倚天号令",
            "description": "提升全体友军10%攻击力，持续3回合",
            "aura_bonus": 0.1,
            "duration": 3
        },
        "growth": {"attack": 40, "leadership": 10},
        "evolution_target": "yitian_ascended"
    },
    "sunquan": {
        "name": "古锭刀",
        "description": "孙权所持神兵，刀身古朴，暗藏锋芒",
        "icon": "⚔️",
        "type": "blade",
        "rarity": "legendary",
        "base_stats": {"attack": 350, "defense": 150},
        "unique_skill": {
            "name": "江东守护",
            "description": "生命值每降低10%，防御力提升10%",
            "defense_percent": 0.1,
            "trigger_percent": 0.1
        },
        "growth": {"attack": 35, "defense": 15},
        "evolution_target": "guding_ascended"
    }
}

ASCENDED_WEAPONS = {
    "qinglong_ascended": {
        "name": "圣龙偃月刀",
        "description": "青龙偃月刀进化形态，龙威震天",
        "icon": "🐉",
        "type": "blade",
        "rarity": "mythic",
        "base_stats": {"attack": 1200, "critical": 0.4},
        "unique_skill": {
            "name": "圣龙降临",
            "description": "攻击时有30%概率召唤圣龙，造成400%伤害并附加神圣灼烧",
            "trigger_rate": 0.3,
            "damage_multiplier": 4.0,
            "effect": "divine_burn"
        },
        "growth": {"attack": 80, "critical": 0.03}
    },
    "shemang_ascended": {
        "name": "神龙蛇矛",
        "description": "丈八蛇矛进化形态，化龙腾飞",
        "icon": "🐉",
        "type": "spear",
        "rarity": "mythic",
        "base_stats": {"attack": 1100, "speed": 80},
        "unique_skill": {
            "name": "神龙乱舞",
            "description": "攻击时有25%概率发动五连击，每击造成100%伤害",
            "trigger_rate": 0.25,
            "hits": 5,
            "damage_per_hit": 1.0
        },
        "growth": {"attack": 70, "speed": 8}
    },
    "longdan_ascended": {
        "name": "神龙胆",
        "description": "龙胆亮银枪进化形态，神枪护体",
        "icon": "🌟",
        "type": "spear",
        "rarity": "mythic",
        "base_stats": {"attack": 1000, "defense": 300, "speed": 50},
        "unique_skill": {
            "name": "神枪守护",
            "description": "受到攻击时有40%概率触发护盾，吸收50%伤害，并反弹20%",
            "trigger_rate": 0.4,
            "shield_absorb": 0.5,
            "reflect": 0.2
        },
        "growth": {"attack": 65, "defense": 25, "speed": 5}
    },
    "huhu_ascended": {
        "name": "神虎湛金枪",
        "description": "虎头湛金枪进化形态，虎啸山林",
        "icon": "🐅",
        "type": "spear",
        "rarity": "mythic",
        "base_stats": {"attack": 1150, "critical": 0.35},
        "unique_skill": {
            "name": "神虎灭世",
            "description": "暴击时额外造成250%伤害，并眩晕敌人1回合",
            "extra_damage": 2.5,
            "stun": True
        },
        "growth": {"attack": 75, "critical": 0.025}
    },
    "baodiao_ascended": {
        "name": "神弓震天",
        "description": "宝雕弓进化形态，箭落星辰",
        "icon": "⭐",
        "type": "bow",
        "rarity": "mythic",
        "base_stats": {"attack": 900, "critical": 0.5},
        "unique_skill": {
            "name": "星辰坠落",
            "description": "攻击时有20%概率无视防御造成真实伤害，并有10%概率秒杀低血量敌人",
            "trigger_rate": 0.2,
            "true_damage": True,
            "execute_rate": 0.1
        },
        "growth": {"attack": 60, "critical": 0.04}
    },
    "yushan_ascended": {
        "name": "天机扇",
        "description": "羽扇进化形态，洞察天机",
        "icon": "🔮",
        "type": "staff",
        "rarity": "mythic",
        "base_stats": {"attack": 750, "skill_damage": 1.0},
        "unique_skill": {
            "name": "天机神算",
            "description": "技能伤害提升100%，并有50%概率使敌人混乱或冰冻",
            "skill_bonus": 1.0,
            "confusion_rate": 0.3,
            "freeze_rate": 0.2
        },
        "growth": {"attack": 50, "skill_damage": 0.08}
    },
    "yitian_ascended": {
        "name": "天帝剑",
        "description": "倚天剑进化形态，天命所归",
        "icon": "👑",
        "type": "sword",
        "rarity": "mythic",
        "base_stats": {"attack": 1000, "leadership": 300},
        "unique_skill": {
            "name": "天命号令",
            "description": "提升全体友军25%攻击力和15%防御力，持续5回合",
            "aura_attack_bonus": 0.25,
            "aura_defense_bonus": 0.15,
            "duration": 5
        },
        "growth": {"attack": 65, "leadership": 20}
    },
    "guding_ascended": {
        "name": "万古神刀",
        "description": "古锭刀进化形态，万古长存",
        "icon": "🏛️",
        "type": "blade",
        "rarity": "mythic",
        "base_stats": {"attack": 850, "defense": 400},
        "unique_skill": {
            "name": "万古不灭",
            "description": "生命值每降低10%，防御力提升20%，攻击力提升10%",
            "defense_percent": 0.2,
            "attack_percent": 0.1,
            "trigger_percent": 0.1
        },
        "growth": {"attack": 55, "defense": 30}
    }
}

RARITY_COLORS = {
    "legendary": {"name": "传说", "color": (255, 215, 0), "glow": (255, 165, 0)},
    "mythic": {"name": "神话", "color": (255, 100, 255), "glow": (180, 0, 255)}
}

EVOLUTION_COST = {
    "legendary": {"金元宝": 5000, "将魂": 3000, "神兵碎片": 100},
    "mythic": {"金元宝": 15000, "将魂": 10000, "神晶": 50}
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
        alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
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

class DivineWeaponSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "divine_weapons" not in data:
            data["divine_weapons"] = {
                "inventory": [],
                "equipped": {},
                "levels": {},
                "awakened": []
            }
        if "resources" not in data:
            data["resources"] = {}
        if "神兵碎片" not in data["resources"]:
            data["resources"]["神兵碎片"] = 0
        if "神晶" not in data["resources"]:
            data["resources"]["神晶"] = 0
        save()
    
    def get_inventory(self):
        return data["divine_weapons"]["inventory"]
    
    def get_equipped(self, hero_name):
        return data["divine_weapons"]["equipped"].get(hero_name)
    
    def get_weapon_level(self, weapon_id):
        return data["divine_weapons"]["levels"].get(weapon_id, 1)
    
    def is_awakened(self, weapon_id):
        return weapon_id in data["divine_weapons"]["awakened"]
    
    def forge_weapon(self, weapon_id):
        weapon_data = DIVINE_WEAPONS.get(weapon_id)
        if not weapon_data:
            return False, "神兵不存在"
        
        cost = EVOLUTION_COST["legendary"]
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        weapon_instance = {
            "id": weapon_id,
            "name": weapon_data["name"],
            "type": weapon_data["type"],
            "rarity": weapon_data["rarity"],
            "level": 1,
            "exp": 0
        }
        
        data["divine_weapons"]["inventory"].append(weapon_instance)
        save()
        
        return True, f"锻造成功！获得神兵：{weapon_data['name']}"
    
    def can_upgrade(self, weapon_id):
        level = self.get_weapon_level(weapon_id)
        if level >= 50:
            return False, "已达到最高等级"
        
        cost = {"金元宝": level * 100, "神兵碎片": level * 10}
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        return True, "可以升级"
    
    def upgrade_weapon(self, weapon_id):
        can_do, msg = self.can_upgrade(weapon_id)
        if not can_do:
            return False, msg
        
        level = self.get_weapon_level(weapon_id)
        cost = {"金元宝": level * 100, "神兵碎片": level * 10}
        
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        data["divine_weapons"]["levels"][weapon_id] = level + 1
        save()
        
        return True, f"升级成功！等级提升至 {level + 1}"
    
    def can_awaken(self, weapon_id):
        weapon_instance = next((w for w in self.get_inventory() if w["id"] == weapon_id), None)
        if not weapon_instance:
            return False, "神兵不在背包中"
        
        if self.is_awakened(weapon_id):
            return False, "已觉醒"
        
        level = self.get_weapon_level(weapon_id)
        if level < 30:
            return False, "需要30级才能觉醒"
        
        cost = EVOLUTION_COST["mythic"]
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        return True, "可以觉醒"
    
    def awaken_weapon(self, weapon_id):
        can_do, msg = self.can_awaken(weapon_id)
        if not can_do:
            return False, msg
        
        cost = EVOLUTION_COST["mythic"]
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        data["divine_weapons"]["awakened"].append(weapon_id)
        
        for i, w in enumerate(data["divine_weapons"]["inventory"]):
            if w["id"] == weapon_id:
                weapon_data = DIVINE_WEAPONS.get(weapon_id)
                if weapon_data and weapon_data.get("evolution_target"):
                    new_id = weapon_data["evolution_target"]
                    ascended_data = ASCENDED_WEAPONS.get(new_id)
                    if ascended_data:
                        data["divine_weapons"]["inventory"][i] = {
                            "id": new_id,
                            "name": ascended_data["name"],
                            "type": ascended_data["type"],
                            "rarity": ascended_data["rarity"],
                            "level": 1,
                            "exp": 0
                        }
                        data["divine_weapons"]["levels"][new_id] = 1
                        data["divine_weapons"]["awakened"].remove(weapon_id)
                        data["divine_weapons"]["awakened"].append(new_id)
                        break
        
        save()
        
        return True, "觉醒成功！神兵进化为神话品质"
    
    def can_equip(self, hero_name, weapon_id):
        weapon_instance = next((w for w in self.get_inventory() if w["id"] == weapon_id), None)
        if not weapon_instance:
            return False, "神兵不在背包中"
        
        for hero, wid in data["divine_weapons"]["equipped"].items():
            if wid == weapon_id:
                return False, "该神兵已装备给其他武将"
        
        return True, "可以装备"
    
    def equip_weapon(self, hero_name, weapon_id):
        can_do, msg = self.can_equip(hero_name, weapon_id)
        if not can_do:
            return False, msg
        
        data["divine_weapons"]["equipped"][hero_name] = weapon_id
        save()
        
        return True, f"装备成功！"
    
    def unequip_weapon(self, hero_name):
        if hero_name not in data["divine_weapons"]["equipped"]:
            return False, "该武将未装备神兵"
        
        del data["divine_weapons"]["equipped"][hero_name]
        save()
        
        return True, "卸下成功"
    
    def get_weapon_stats(self, weapon_id):
        all_weapons = {**DIVINE_WEAPONS, **ASCENDED_WEAPONS}
        weapon_data = all_weapons.get(weapon_id)
        if not weapon_data:
            return {}
        
        level = self.get_weapon_level(weapon_id)
        stats = {}
        
        for stat, base_value in weapon_data["base_stats"].items():
            growth = weapon_data["growth"].get(stat, 0)
            stats[stat] = int(base_value + growth * (level - 1))
        
        return stats

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

def draw_weapon_card(surface, weapon, x, y, width, height, font_main, font_small):
    all_weapons = {**DIVINE_WEAPONS, **ASCENDED_WEAPONS}
    weapon_data = all_weapons.get(weapon["id"])
    if not weapon_data:
        return
    
    rarity_info = RARITY_COLORS[weapon["rarity"]]
    bg_color = rarity_info["color"]
    
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (*bg_color[:3], 150), (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, bg_color, (x, y, width, height), 2, border_radius=12)
    
    icon_font = pygame.font.Font(None, 45)
    icon_surf = icon_font.render(weapon_data["icon"], True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + width // 2, y + 35))
    surface.blit(icon_surf, icon_rect)
    
    name_surf = font_main.render(weapon["name"], True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + width // 2, y + 80))
    surface.blit(name_surf, name_rect)
    
    rarity_text = rarity_info["name"]
    rarity_surf = font_small.render(rarity_text, True, bg_color)
    surface.blit(rarity_surf, (x + 10, y + 110))
    
    level_text = f"Lv.{weapon['level']}"
    level_surf = font_small.render(level_text, True, COLORS["accent_green"])
    surface.blit(level_surf, (x + width - 10 - level_surf.get_width(), y + 110))
    
    stats = DivineWeaponSystem().get_weapon_stats(weapon["id"])
    stat_y = y + 135
    for stat, value in list(stats.items())[:3]:
        stat_name = {"attack": "攻击", "defense": "防御", "critical": "暴击", "speed": "速度", "skill_damage": "技能", "leadership": "统帅"}.get(stat, stat)
        stat_text = f"{stat_name}: {value}"
        stat_surf = font_small.render(stat_text, True, COLORS["text_white"])
        surface.blit(stat_surf, (x + 10, stat_y))
        stat_y += 20
    
    skill = weapon_data.get("unique_skill", {})
    skill_name = skill.get("name", "")
    if skill_name:
        skill_surf = font_small.render(f"✨ {skill_name}", True, COLORS["accent_purple"])
        surface.blit(skill_surf, (x + 10, stat_y))

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
        pygame.display.set_caption("神兵系统")
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
        
        weapon_system = DivineWeaponSystem()
        
        particles = []
        
        current_tab = "forge"
        tabs = ["forge", "inventory", "equip"]
        tab_names = ["锻造神兵", "神兵背包", "装备神兵"]
        
        message = ""
        show_message = False
        message_timer = 0
        
        selected_weapon = None
        
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
            
            draw_title(screen, "神兵系统", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            tab_y = SCREEN_HEIGHT * 0.18
            tab_width = 140
            tab_height = 45
            tab_start_x = (SCREEN_WIDTH - len(tabs) * (tab_width + 20)) // 2
            
            tab_buttons = []
            for i, (tab_id, tab_name) in enumerate(zip(tabs, tab_names)):
                x = tab_start_x + i * (tab_width + 20)
                is_selected = current_tab == tab_id
                btn_color = COLORS["btn_gold"] if is_selected else COLORS["btn_blue"]
                hover_color = COLORS["btn_gold_hover"] if is_selected else COLORS["btn_blue_hover"]
                
                btn = Button(tab_name, x, tab_y, tab_width, tab_height, font_small, btn_color, hover_color)
                btn.update((mx, my))
                btn.draw(screen)
                tab_buttons.append((btn, tab_id))
            
            content_y = SCREEN_HEIGHT * 0.28
            
            inventory = weapon_system.get_inventory()
            
            if current_tab == "forge":
                forge_cost = EVOLUTION_COST["legendary"]
                cost_text = font_main.render(f"锻造消耗: {forge_cost['金元宝']}金元宝, {forge_cost['将魂']}将魂, {forge_cost['神兵碎片']}神兵碎片", 
                                           True, COLORS["accent_orange"])
                screen.blit(cost_text, (SCREEN_WIDTH // 2 - cost_text.get_width() // 2, content_y))
                
                card_width = min(180, SCREEN_WIDTH * 0.2)
                card_height = min(150, SCREEN_HEIGHT * 0.21)
                cols = min(4, SCREEN_WIDTH // (card_width + 15))
                start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 15)) // 2
                
                forge_buttons = []
                for i, (weapon_id, weapon_data) in enumerate(DIVINE_WEAPONS.items()):
                    row = i // cols
                    col = i % cols
                    x = start_x + col * (card_width + 15)
                    y = content_y + 60 + row * (card_height + 15)
                    
                    already_have = any(w["id"] == weapon_id or w["id"] == weapon_data.get("evolution_target") for w in inventory)
                    
                    rarity_info = RARITY_COLORS[weapon_data["rarity"]]
                    bg_color = rarity_info["color"]
                    
                    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                    opacity = 150 if not already_have else 80
                    pygame.draw.rect(card_surf, (*bg_color[:3], opacity), (0, 0, card_width, card_height), border_radius=12)
                    surface.blit(card_surf, (x, y))
                    
                    if already_have:
                        pygame.draw.rect(screen, (100, 100, 100), (x, y, card_width, card_height), 2, border_radius=12)
                    else:
                        pygame.draw.rect(screen, bg_color, (x, y, card_width, card_height), 2, border_radius=12)
                    
                    icon_font = pygame.font.Font(None, int(35 * scale))
                    icon_surf = icon_font.render(weapon_data["icon"], True, COLORS["text_white"])
                    surface.blit(icon_surf, (x + card_width // 2 - icon_surf.get_width() // 2, y + 20))
                    
                    name_surf = font_small.render(weapon_data["name"], True, COLORS["accent_gold"])
                    surface.blit(name_surf, (x + card_width // 2 - name_surf.get_width() // 2, y + 60))
                    
                    if already_have:
                        owned_surf = font_small.render("✓ 已拥有", True, COLORS["accent_green"])
                        surface.blit(owned_surf, (x + card_width // 2 - owned_surf.get_width() // 2, y + 95))
                    else:
                        forge_btn = Button("锻造", x + (card_width - 60) // 2, y + 95, 60, 30, font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"])
                        forge_btn.update((mx, my))
                        forge_btn.draw(screen)
                        forge_buttons.append((forge_btn, weapon_id))
            
            elif current_tab == "inventory":
                if inventory:
                    card_width = min(200, SCREEN_WIDTH * 0.22)
                    card_height = min(200, SCREEN_HEIGHT * 0.28)
                    cols = min(4, SCREEN_WIDTH // (card_width + 15))
                    start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 15)) // 2
                    
                    weapon_buttons = []
                    for i, weapon in enumerate(inventory):
                        row = i // cols
                        col = i % cols
                        x = start_x + col * (card_width + 15)
                        y = content_y + row * (card_height + 15)
                        
                        draw_weapon_card(screen, weapon, x, y, card_width, card_height, font_main, font_small)
                        
                        card_rect = pygame.Rect(x, y, card_width, card_height)
                        is_selected = selected_weapon == weapon["id"]
                        if is_selected:
                            pygame.draw.rect(screen, COLORS["accent_gold"], card_rect, 4, border_radius=12)
                        
                        weapon_buttons.append((card_rect, weapon))
                    
                    if selected_weapon:
                        weapon = next((w for w in inventory if w["id"] == selected_weapon), None)
                        if weapon:
                            info_panel_x = SCREEN_WIDTH * 0.05
                            info_panel_y = SCREEN_HEIGHT * 0.82
                            info_panel_width = SCREEN_WIDTH * 0.9
                            info_panel_height = SCREEN_HEIGHT * 0.13
                            
                            info_surf = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
                            pygame.draw.rect(info_surf, COLORS["panel_bg"], (0, 0, info_panel_width, info_panel_height), border_radius=12)
                            screen.blit(info_surf, (info_panel_x, info_panel_y))
                            
                            can_upgrade, upgrade_msg = weapon_system.can_upgrade(weapon["id"])
                            upgrade_btn = Button(f"升级 ({weapon['level']}/50)", info_panel_x + 20, info_panel_y + 15, 150, 40, font_small, 
                                               COLORS["btn_green"] if can_upgrade else COLORS["accent_red"], 
                                               COLORS["btn_green_hover"] if can_upgrade else (200, 80, 80))
                            upgrade_btn.update((mx, my))
                            upgrade_btn.draw(screen)
                            
                            can_awaken, awaken_msg = weapon_system.can_awaken(weapon["id"])
                            awaken_btn = Button(f"觉醒", info_panel_x + 180, info_panel_y + 15, 120, 40, font_small, 
                                               COLORS["btn_purple"] if can_awaken else COLORS["accent_red"], 
                                               (200, 100, 255) if can_awaken else (200, 80, 80))
                            awaken_btn.update((mx, my))
                            awaken_btn.draw(screen)
                else:
                    empty_text = font_main.render("暂无神兵，请先锻造", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "equip":
                if inventory:
                    heroes = data["hero_management"].get("heroes", {}) if "hero_management" in data else {}
                    
                    if heroes:
                        btn_width = min(250, SCREEN_WIDTH * 0.28)
                        btn_height = 50
                        start_x = SCREEN_WIDTH * 0.05
                        
                        hero_buttons = []
                        for i, (hero_name, hero_data) in enumerate(heroes.items()):
                            y = content_y + i * (btn_height + 20)
                            if y > SCREEN_HEIGHT - 200:
                                break
                            
                            equipped_weapon_id = weapon_system.get_equipped(hero_name)
                            
                            bg_rect = pygame.Rect(start_x - 5, y - 5, btn_width + 10, btn_height + 10)
                            pygame.draw.rect(screen, COLORS["panel_bg"], bg_rect, border_radius=8)
                            
                            hero_surf = font_main.render(f"⚔️ {hero_name}", True, COLORS["accent_gold"])
                            screen.blit(hero_surf, (start_x, y + 15))
                            
                            if equipped_weapon_id:
                                weapon = next((w for w in inventory if w["id"] == equipped_weapon_id), None)
                                if weapon:
                                    weapon_name_surf = font_small.render(f"装备: {weapon['name']}", True, COLORS["accent_green"])
                                    screen.blit(weapon_name_surf, (start_x + 120, y + 20))
                                    
                                    unequip_btn = Button("卸下", start_x + btn_width - 70, y + 10, 60, 30, font_small, COLORS["accent_red"], (255, 100, 100))
                                    unequip_btn.update((mx, my))
                                    unequip_btn.draw(screen)
                                    hero_buttons.append((unequip_btn, hero_name, None, "unequip"))
                            else:
                                empty_text = font_small.render("未装备神兵", True, COLORS["text_gray"])
                                screen.blit(empty_text, (start_x + 120, y + 20))
                                
                                available_weapons = [w for w in inventory if w["id"] not in data["divine_weapons"]["equipped"].values()]
                                if available_weapons:
                                    equip_btn = Button("装备神兵", start_x + btn_width - 120, y + 10, 110, 30, font_small, COLORS["btn_green"], COLORS["btn_green_hover"])
                                    equip_btn.update((mx, my))
                                    equip_btn.draw(screen)
                                    hero_buttons.append((equip_btn, hero_name, available_weapons[0]["id"], "equip"))
                    else:
                        empty_text = font_main.render("暂无武将", True, COLORS["text_gray"])
                        screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
                else:
                    empty_text = font_main.render("暂无神兵，请先锻造", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
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
                    
                    if current_tab == "forge" and 'forge_buttons' in locals():
                        for btn, weapon_id in forge_buttons:
                            if btn.rect.collidepoint(mx, my):
                                success, msg = weapon_system.forge_weapon(weapon_id)
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                    
                    elif current_tab == "inventory" and 'weapon_buttons' in locals():
                        for rect, weapon in weapon_buttons:
                            if rect.collidepoint(mx, my):
                                selected_weapon = weapon["id"]
                                break
                        
                        if selected_weapon:
                            weapon = next((w for w in inventory if w["id"] == selected_weapon), None)
                            if weapon:
                                info_panel_x = SCREEN_WIDTH * 0.05
                                info_panel_y = SCREEN_HEIGHT * 0.82
                                
                                upgrade_rect = pygame.Rect(info_panel_x + 20, info_panel_y + 15, 150, 40)
                                if upgrade_rect.collidepoint(mx, my):
                                    success, msg = weapon_system.upgrade_weapon(weapon["id"])
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                
                                awaken_rect = pygame.Rect(info_panel_x + 180, info_panel_y + 15, 120, 40)
                                if awaken_rect.collidepoint(mx, my):
                                    success, msg = weapon_system.awaken_weapon(weapon["id"])
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                    
                    elif current_tab == "equip" and 'hero_buttons' in locals():
                        for btn, hero_name, weapon_id, action in hero_buttons:
                            if btn.rect.collidepoint(mx, my):
                                if action == "unequip":
                                    success, msg = weapon_system.unequip_weapon(hero_name)
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                elif action == "equip":
                                    success, msg = weapon_system.equip_weapon(hero_name, weapon_id)
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                break
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("神兵系统")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("神兵系统", str(e))

if __name__ == "__main__":
    main()