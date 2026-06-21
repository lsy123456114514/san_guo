import os
import pygame
import platform
import time
import random
import math
from ASSET.game_data import data, save, get_system_font_name, load_sound, EQUIP_SKILLS, HERO_SKILLS, ELEMENTS, GUNS, HERO_BONDS, ELEMENT_SYNERGIES, ELEMENT_WEAKNESS
from ASSET.weather_system import WeatherSystem
from ASSET.event_system import EventSystem
from ASSET import safe_exit

def update_battle_stats(win, player_heroes, enemy_heroes):
    """更新战斗统计数据到存档"""
    if "battle_stats" not in data:
        data["battle_stats"] = {
            "total_battles": 0,
            "victories": 0,
            "defeats": 0,
            "max_combo": 0,
            "ultimate_used_count": 0
        }
    
    data["battle_stats"]["total_battles"] += 1
    
    if win:
        data["battle_stats"]["victories"] += 1
    else:
        data["battle_stats"]["defeats"] += 1
    
    # 更新最大连击数
    max_combo = max([h.combo_count for h in player_heroes] + [0])
    data["battle_stats"]["max_combo"] = max(data["battle_stats"]["max_combo"], max_combo)
    
    # 更新必杀技使用次数
    ultimate_count = sum([h.rage for h in player_heroes]) // 100
    data["battle_stats"]["ultimate_used_count"] += ultimate_count
    
    save()

# 颜色主题
COLORS = {
    "bg_dark": (15, 15, 30),
    "bg_light": (25, 25, 45),
    "accent_gold": (255, 215, 0),
    "accent_red": (220, 60, 60),
    "accent_green": (60, 220, 100),
    "accent_blue": (70, 130, 220),
    "accent_purple": (180, 100, 220),
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 200),
    "hp_green": (60, 200, 60),
    "hp_red": (220, 60, 60),
    "hp_bg": (60, 60, 80)
}

class Particle:
    def __init__(self, x, y, color, speed, size, life, angle=None):
        self.x = x
        self.y = y
        self.color = color
        if angle is not None:
            self.speed_x = math.cos(angle) * speed
            self.speed_y = math.sin(angle) * speed
        else:
            self.speed_x = random.uniform(-speed, speed)
            self.speed_y = random.uniform(-speed, speed)
        self.size = size
        self.life = life
        self.max_life = life
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += 0.2  # 重力
        self.life -= 1
        self.size = max(0.5, self.size - 0.03)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class FloatingText:
    def __init__(self, text, x, y, color, font, is_damage=True):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.life = 50
        self.max_life = 50
        self.speed_y = -2 if is_damage else -1
        self.scale = 1.0
    
    def update(self):
        self.y += self.speed_y
        self.life -= 1
        if self.life > 40:
            self.scale = min(1.5, self.scale + 0.05)
        else:
            self.scale = max(1.0, self.scale - 0.02)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        text_surf = self.font.render(self.text, True, self.color)
        scaled_size = (int(text_surf.get_width() * self.scale), int(text_surf.get_height() * self.scale))
        scaled_surf = pygame.transform.scale(text_surf, scaled_size)
        scaled_surf.set_alpha(alpha)
        rect = scaled_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(scaled_surf, rect)

class AnimatedButton:
    def __init__(self, x, y, width, height, text, font, 
                 normal_color=(200, 50, 50), hover_color=(230, 80, 80),
                 text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.scale = 1.0
        self.glow_alpha = 0
        self.particles = []
    
    def update(self, mouse_pos):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered:
            self.scale = min(1.05, self.scale + 0.01)
            self.glow_alpha = min(100, self.glow_alpha + 5)
            if not was_hovered:
                for _ in range(5):
                    self.particles.append(Particle(
                        random.randint(self.rect.x, self.rect.x + self.rect.width),
                        self.rect.y + self.rect.height,
                        COLORS["accent_gold"],
                        2, random.randint(2, 4), 20
                    ))
        else:
            self.scale = max(1.0, self.scale - 0.01)
            self.glow_alpha = max(0, self.glow_alpha - 5)
        
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
    
    def draw(self, surface):
        # 发光效果
        if self.glow_alpha > 0:
            glow_surf = pygame.Surface((self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*self.hover_color[:3], self.glow_alpha),
                           (10, 10, self.rect.width, self.rect.height), border_radius=10)
            surface.blit(glow_surf, (self.rect.x - 10, self.rect.y - 10))
        
        # 按钮主体
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_x = self.rect.x + (self.rect.width - scaled_width) // 2
        scaled_y = self.rect.y + (self.rect.height - scaled_height) // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        color = self.hover_color if self.is_hovered else self.normal_color
        
        # 渐变按钮
        for i in range(scaled_height):
            ratio = i / scaled_height
            r = int(color[0] * (1 - ratio * 0.3))
            g = int(color[1] * (1 - ratio * 0.3))
            b = int(color[2] * (1 - ratio * 0.3))
            pygame.draw.line(surface, (r, g, b), 
                           (scaled_x, scaled_y + i), 
                           (scaled_x + scaled_width, scaled_y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], scaled_rect, 2, border_radius=8)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)
        
        # 粒子
        for p in self.particles:
            p.draw(surface)

def draw_gradient_background(surface, color1, color2):
    """绘制渐变背景"""
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_health_bar(surface, x, y, width, height, current, maximum, color):
    """绘制血条"""
    ratio = max(0, current / maximum)
    
    # 背景
    pygame.draw.rect(surface, COLORS["hp_bg"], (x, y, width, height), border_radius=5)
    
    # 血条
    if ratio > 0:
        bar_width = int(width * ratio)
        # 渐变
        for i in range(bar_width):
            r = int(color[0] * (1 - i / bar_width * 0.3))
            g = int(color[1] * (1 - i / bar_width * 0.3))
            b = int(color[2] * (1 - i / bar_width * 0.3))
            pygame.draw.line(surface, (r, g, b), (x + i, y), (x + i, y + height))
    
    # 边框
    pygame.draw.rect(surface, COLORS["text_white"], (x, y, width, height), 2, border_radius=5)
    
    # 数值
    font = pygame.font.Font(None, 24)
    text = font.render(f"{current}/{maximum}", True, COLORS["text_white"])
    text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
    surface.blit(text, text_rect)

def draw_character_card(surface, x, y, is_player, hp, max_hp, level, font):
    """绘制角色卡片"""
    card_width = 200
    card_height = 250
    
    # 卡片背景
    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (40, 40, 70, 200), (0, 0, card_width, card_height), border_radius=15)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, COLORS["accent_gold"], (x, y, card_width, card_height), 2, border_radius=15)
    
    # 角色图标
    icon = "🛡️" if is_player else "👹"
    icon_font = pygame.font.Font(None, 80)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + card_width // 2, y + 70))
    surface.blit(icon_surf, icon_rect)
    
    # 名称
    name = "玩家" if is_player else "敌人"
    name_surf = font.render(name, True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + card_width // 2, y + 130))
    surface.blit(name_surf, name_rect)
    
    # 等级
    level_surf = font.render(f"Lv.{level}", True, COLORS["text_gray"])
    level_rect = level_surf.get_rect(center=(x + card_width // 2, y + 160))
    surface.blit(level_surf, level_rect)
    
    # 血条
    hp_color = COLORS["hp_green"] if is_player else COLORS["hp_red"]
    draw_health_bar(surface, x + 20, y + 190, card_width - 40, 25, hp, max_hp, hp_color)

def draw_skill_effect(surface, center_x, center_y, skill_type):
    """绘制技能特效"""
    if skill_type == "weapon":
        # 武器技能：剑气效果
        for i in range(5):
            length = 100 + i * 20
            width = 5 + i
            alpha = max(0, 200 - i * 40)
            effect_surf = pygame.Surface((length, width), pygame.SRCALPHA)
            pygame.draw.rect(effect_surf, (*COLORS["accent_red"][:3], alpha), (0, 0, length, width))
            # 旋转效果
            rotated_surf = pygame.transform.rotate(effect_surf, i * 10)
            surface.blit(rotated_surf, (center_x - 150 - length // 2, center_y - width // 2))
    elif skill_type == "armor":
        # 防具技能：防御护盾效果
        for i in range(4):
            radius = 50 + i * 20
            alpha = max(0, 150 - i * 40)
            effect_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(effect_surf, (*COLORS["accent_green"][:3], alpha), (radius, radius), radius, 3)
            surface.blit(effect_surf, (center_x - 150 - radius, center_y - radius))
    elif skill_type == "horse":
        # 坐骑技能：速度提升效果
        for i in range(6):
            x = center_x - 150 + i * 30
            y = center_y - 20 + random.randint(-10, 10)
            alpha = max(0, 200 - i * 30)
            effect_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(effect_surf, (*COLORS["accent_blue"][:3], alpha), (10, 10), 5)
            surface.blit(effect_surf, (x, y))
    else:  # book
        # 书籍技能：魔法书效果
        for i in range(5):
            radius = 30 + i * 15
            alpha = max(0, 180 - i * 40)
            effect_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(effect_surf, (*COLORS["accent_purple"][:3], alpha), (radius, radius), radius, 2)
            # 星形效果
            points = []
            for j in range(5):
                angle = math.pi / 2 + j * math.pi * 2 / 5
                px = radius + math.cos(angle) * radius
                py = radius + math.sin(angle) * radius
                points.append((px, py))
            pygame.draw.polygon(effect_surf, (*COLORS["accent_gold"][:3], alpha), points)
            surface.blit(effect_surf, (center_x - 150 - radius, center_y - radius))

def draw_battle_effect(surface, center_x, center_y, is_player_attack):
    """绘制战斗特效"""
    # 冲击波效果
    for i in range(3):
        radius = 20 + i * 15
        alpha = max(0, 150 - i * 40)
        color = COLORS["accent_blue"] if is_player_attack else COLORS["accent_red"]
        effect_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(effect_surf, (*color[:3], alpha), (radius, radius), radius, 3)
        target_x = center_x - 150 if is_player_attack else center_x + 150
        surface.blit(effect_surf, (target_x - radius, center_y - radius))

# 元素颜色映射
ELEMENT_COLORS = {
    "火": (255, 100, 100),
    "水": (100, 150, 255),
    "土": (150, 100, 50),
    "风": (100, 200, 100),
    "雷": (200, 100, 255)
}

# 武将图标
HERO_ICONS = {
    "赵云": "⚔️",
    "关羽": "🗡️",
    "张飞": "🛡️",
    "马超": "🐎",
    "黄忠": "🏹",
    "诸葛亮": "🧠",
    "周瑜": "🔥",
    "吕布": "💥",
    "貂蝉": "🌸",
    "华佗": "🌿"
}

# 小弟类
class Minion:
    def __init__(self, element):
        self.element = element
        self.max_hp = 30
        self.hp = self.max_hp
        self.damage = 10
    
    def attack(self, target):
        target.hp = max(0, target.hp - self.damage)
        return self.damage

# 武将类
class Hero:
    def __init__(self, name, level=1):
        self.name = name
        self.level = level
        self.skill = HERO_SKILLS.get(name, {
            "name": "普通攻击",
            "damage": 20,
            "element": "火",
            "description": "基础攻击"
        })
        self.max_hp = 100 + level * 20
        self.hp = self.max_hp
        self.element = self.skill["element"]
        # 根据等级生成小弟
        self.minions = []
        minion_count = min(5, level)
        for i in range(minion_count):
            minion = Minion(self.element)
            self.minions.append(minion)
        # 装备技能
        self.equip_skills = {
            "weapon": None,
            "armor": None,
            "horse": None,
            "book": None
        }
        # 枪械数据
        self.gun = None
        self.gun_multiplier = 1.0
        self.base_power = 100 + level * 20
        # 羁绊效果数据
        self.active_bonds = []
        self.bond_bonuses = {
            "damage_bonus": 0.0,
            "hp_bonus": 0.0,
            "crit_bonus": 0.0,
            "skill_damage": 0.0,
            "heal_bonus": 0.0,
            "speed_bonus": 0.0
        }
        # 元素共鸣效果
        self.element_buffs = []
        self.shield = 0
        self.slow_turns = 0
        self.burn_turns = 0
        self.burn_damage = 0
        # 连击系统
        self.combo_count = 0
        self.max_combo = 10
        self.combo_timer = 0
        self.combo_timeout = 3000
        # 必杀技系统
        self.rage = 0
        self.max_rage = 100
        self.rage_per_hit = 10
        self.ultimate_skill = self.get_ultimate_skill()
    
    def get_ultimate_skill(self):
        """获取必杀技"""
        ultimate_skills = {
            "赵云": {"name": "七进七出", "damage": 150, "element": "风", "rage_cost": 100, "description": "赵云的终极技能，连续攻击敌人"},
            "关羽": {"name": "青龙偃月斩", "damage": 200, "element": "火", "rage_cost": 100, "description": "关羽的终极技能，强力斩击"},
            "张飞": {"name": "怒吼", "damage": 180, "element": "土", "rage_cost": 100, "description": "张飞的终极技能，震退敌人"},
            "诸葛亮": {"name": "天雷阵", "damage": 220, "element": "雷", "rage_cost": 100, "description": "诸葛亮的终极技能，召唤天雷"},
            "曹操": {"name": "乱世枭雄", "damage": 190, "element": "火", "rage_cost": 100, "description": "曹操的终极技能，统御攻击"},
            "吕布": {"name": "战神降临", "damage": 250, "element": "雷", "rage_cost": 100, "description": "吕布的终极技能，无敌攻击"},
            "貂蝉": {"name": "倾国倾城", "damage": 160, "element": "水", "rage_cost": 100, "description": "貂蝉的终极技能，魅惑攻击"},
            "黄忠": {"name": "百步穿杨", "damage": 210, "element": "风", "rage_cost": 100, "description": "黄忠的终极技能，远程狙击"},
            "马超": {"name": "西凉风暴", "damage": 180, "element": "土", "rage_cost": 100, "description": "马超的终极技能，骑兵突击"},
            "周瑜": {"name": "业火焚城", "damage": 230, "element": "火", "rage_cost": 100, "description": "周瑜的终极技能，火烧连营"}
        }
        return ultimate_skills.get(self.name, {
            "name": "必杀技",
            "damage": 150,
            "element": self.element,
            "rage_cost": 100,
            "description": "强力必杀技"
        })
    
    def add_combo(self):
        """增加连击数"""
        if self.combo_count < self.max_combo:
            self.combo_count += 1
        self.combo_timer = pygame.time.get_ticks()
    
    def reset_combo(self):
        """重置连击"""
        self.combo_count = 0
    
    def update_combo(self):
        """更新连击状态"""
        if pygame.time.get_ticks() - self.combo_timer > self.combo_timeout:
            self.reset_combo()
    
    def get_combo_bonus(self):
        """获取连击伤害加成"""
        return 1.0 + (self.combo_count * 0.1)
    
    def add_rage(self, amount=10):
        """增加怒气"""
        self.rage = min(self.max_rage, self.rage + amount)
    
    def can_use_ultimate(self):
        """检查是否可以使用必杀技"""
        return self.rage >= self.ultimate_skill["rage_cost"]
    
    def use_ultimate(self, target):
        """使用必杀技"""
        if not self.can_use_ultimate():
            return 0, False
        
        self.rage -= self.ultimate_skill["rage_cost"]
        damage = self.ultimate_skill["damage"] * (1 + self.bond_bonuses["damage_bonus"])
        damage *= self.get_combo_bonus()
        
        target.hp = max(0, target.hp - damage)
        
        # 重置连击
        self.reset_combo()
        
        return damage, True

    def apply_bond_effects(self, all_hero_names):
        """检查并应用羁绊效果"""
        self.active_bonds = []
        for bond_id, bond_data in HERO_BONDS.items():
            bond_heroes = bond_data["heroes"]
            # 检查是否满足羁绊条件
            common_heroes = set(all_hero_names) & set(bond_heroes)
            if len(common_heroes) >= len(bond_heroes):
                # 完全满足羁绊
                self.active_bonds.append(bond_id)
                effect = bond_data["effect"]
                if effect["type"] in self.bond_bonuses:
                    self.bond_bonuses[effect["type"]] += effect["value"]

    def get_power_with_gun(self):
        """获取带枪械加成的武力值"""
        base_power = self.skill["damage"] + self.level * 5
        return base_power * self.gun_multiplier * (1 + self.bond_bonuses["damage_bonus"])

    def has_bullets(self):
        """检查是否有足够的子弹"""
        if not self.gun:
            return True
        gun_data = GUNS.get(self.gun, {})
        bullet_type = gun_data.get("bullet_type", "普通子弹")
        bullet_cost = gun_data.get("bullets_per_round", 1)
        return data["resources"].get(bullet_type, 0) >= bullet_cost

    def consume_bullets(self):
        """消耗子弹"""
        if not self.gun:
            return True
        gun_data = GUNS.get(self.gun, {})
        bullet_type = gun_data.get("bullet_type", "普通子弹")
        bullet_cost = gun_data.get("bullets_per_round", 1)
        if data["resources"].get(bullet_type, 0) >= bullet_cost:
            data["resources"][bullet_type] -= bullet_cost
            save()
            return True
        return False

    def set_gun(self, gun_type):
        """设置枪械"""
        if gun_type and gun_type in GUNS:
            self.gun = gun_type
            self.gun_multiplier = GUNS[gun_type]["damage_multiplier"]
        else:
            self.gun = None
            self.gun_multiplier = 1.0

    def attack(self, target):
        damage = self.skill["damage"] + self.level * 5
        # 应用羁绊攻击加成
        damage *= (1 + self.bond_bonuses["damage_bonus"])
        # 应用暴击
        if random.random() < self.bond_bonuses["crit_bonus"]:
            damage *= 1.5
        # 应用枪械
        if self.gun and self.has_bullets():
            damage *= self.gun_multiplier
            self.consume_bullets()
        target.hp = max(0, target.hp - damage)
        
        # 检查元素弱点
        synergy_key = f"{self.element}_{target.element}"
        if synergy_key in ELEMENT_SYNERGIES:
            synergy = ELEMENT_SYNERGIES[synergy_key]
            synergy_type = synergy.get("type")
            if synergy_type == "steam":
                extra_damage = synergy["damage"]
                target.hp = max(0, target.hp - extra_damage)
                damage += extra_damage
            elif synergy_type == "wildfire" and synergy.get("aoe"):
                pass  # AOE效果在战斗回合中处理
            elif synergy_type == "lava":
                target.burn_turns = 3
                target.burn_damage = 10
            elif synergy_type == "frost":
                target.slow_turns = synergy.get("slow", 1)
        
        # 检查元素弱点加成
        if target.element in ELEMENT_WEAKNESS:
            weakness = ELEMENT_WEAKNESS[target.element]
            if self.element == weakness["weak_to"]:
                damage *= weakness["bonus"]
                target.hp = max(0, target.hp - int(damage * 0.5))  # 额外弱点伤害
        
        return damage
    
    def use_skill(self, skill_type, target):
        """使用装备技能"""
        if skill_type in self.equip_skills and self.equip_skills[skill_type]:
            skill = self.equip_skills[skill_type]
            if skill_type == "weapon":
                # 武器技能：高伤害
                damage = skill["damage"] * 1.5
                target.hp = max(0, target.hp - damage)
                return damage, "weapon"
            elif skill_type == "armor":
                # 防具技能：恢复生命值
                heal = skill["defense"] * 2
                self.hp = min(self.max_hp, self.hp + heal)
                return heal, "armor"
            elif skill_type == "horse":
                # 坐骑技能：速度加成，增加攻击力
                speed_bonus = skill["speed"] * 0.1
                damage = self.skill["damage"] * (1 + speed_bonus)
                target.hp = max(0, target.hp - damage)
                return damage, "horse"
            elif skill_type == "book":
                # 书籍技能：暴击
                critical = skill["critical"]
                damage = self.skill["damage"] * 2 if random.random() < critical else self.skill["damage"]
                target.hp = max(0, target.hp - damage)
                return damage, "book"
        return 0, None

# 绘制小弟
def draw_minion(surface, x, y, minion, is_player):
    """绘制小弟"""
    minion_size = 30
    
    # 小弟图标
    icon = "👾"
    icon_font = pygame.font.Font(None, 24)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    
    # 小弟背景
    minion_color = ELEMENT_COLORS.get(minion.element, (255, 215, 0))
    pygame.draw.circle(surface, minion_color, (x, y), minion_size // 2)
    pygame.draw.circle(surface, COLORS["text_white"], (x, y), minion_size // 2, 1)
    
    # 绘制图标
    icon_rect = icon_surf.get_rect(center=(x, y))
    surface.blit(icon_surf, icon_rect)
    
    # 血条
    hp_ratio = minion.hp / minion.max_hp
    hp_width = minion_size - 4
    hp_height = 4
    hp_x = x - hp_width // 2
    hp_y = y + minion_size // 2 + 5
    
    # 血条背景
    pygame.draw.rect(surface, COLORS["hp_bg"], (hp_x, hp_y, hp_width, hp_height), border_radius=2)
    
    # 血条
    if hp_ratio > 0:
        bar_width = int(hp_width * hp_ratio)
        hp_color = COLORS["hp_green"] if hp_ratio > 0.5 else COLORS["hp_red"]
        pygame.draw.rect(surface, hp_color, (hp_x, hp_y, bar_width, hp_height), border_radius=2)

# 绘制武将卡片
def draw_hero_card(surface, x, y, hero, is_player, font_normal, font_small):
    """绘制武将卡片"""
    card_width = 180
    card_height = 220

    # 卡片背景
    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
    bg_color = (40, 60, 80, 200) if is_player else (80, 40, 40, 200)
    pygame.draw.rect(card_surf, bg_color, (0, 0, card_width, card_height), border_radius=15)
    surface.blit(card_surf, (x, y))

    # 边框
    border_color = ELEMENT_COLORS.get(hero.element, (255, 215, 0))
    pygame.draw.rect(surface, border_color, (x, y, card_width, card_height), 2, border_radius=15)

    # 武将图标
    icon = HERO_ICONS.get(hero.name, "👤")
    icon_font = pygame.font.Font(None, 60)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + card_width // 2, y + 60))
    surface.blit(icon_surf, icon_rect)

    # 名称
    name_surf = font_normal.render(hero.name, True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + card_width // 2, y + 110))
    surface.blit(name_surf, name_rect)

    # 技能
    skill_surf = font_small.render(hero.skill["name"], True, COLORS["text_white"])
    skill_rect = skill_surf.get_rect(center=(x + card_width // 2, y + 140))
    surface.blit(skill_surf, skill_rect)

    # 元素
    element_surf = font_small.render(f"元素: {hero.element}", True, border_color)
    element_rect = element_surf.get_rect(center=(x + card_width // 2, y + 165))
    surface.blit(element_surf, element_rect)

    # 枪械信息
    if hero.gun:
        gun_info_text = f"🔫 {GUNS[hero.gun]['name']} {hero.gun_multiplier}x"
        gun_color = COLORS["accent_red"]
        gun_surf = font_small.render(gun_info_text, True, gun_color)
        gun_rect = gun_surf.get_rect(center=(x + card_width // 2, y + 185))
        surface.blit(gun_surf, gun_rect)
    
    # 羁绊信息
    if hero.active_bonds:
        bond_texts = []
        for bond_id in hero.active_bonds:
            bond_data = HERO_BONDS[bond_id]
            bond_texts.append(f"✨{bond_data['name']}")
        bond_display = " ".join(bond_texts)
        bond_surf = font_small.render(bond_display, True, COLORS["accent_gold"])
        bond_rect = bond_surf.get_rect(center=(x + card_width // 2, y + 205))
        surface.blit(bond_surf, bond_rect)
        # 调整小弟位置
        minion_y = y + card_height + 10
    else:
        # 小弟数量
        minion_count = sum(1 for m in hero.minions if m.hp > 0)
        minion_text = f"小弟: {minion_count}/{len(hero.minions)}"
        minion_surf = font_small.render(minion_text, True, COLORS["text_white"])
        minion_rect = minion_surf.get_rect(center=(x + card_width // 2, y + 205))
        surface.blit(minion_surf, minion_rect)

    # 血条
    hp_ratio = hero.hp / hero.max_hp
    hp_width = card_width - 30
    hp_height = 15
    hp_x = x + 15
    hp_y = y + card_height - 25

    # 血条背景
    pygame.draw.rect(surface, COLORS["hp_bg"], (hp_x, hp_y, hp_width, hp_height), border_radius=5)

    # 血条
    if hp_ratio > 0:
        bar_width = int(hp_width * hp_ratio)
        hp_color = COLORS["hp_green"] if hp_ratio > 0.5 else COLORS["hp_red"]
        pygame.draw.rect(surface, hp_color, (hp_x, hp_y, bar_width, hp_height), border_radius=5)

    # 边框
    pygame.draw.rect(surface, COLORS["text_white"], (hp_x, hp_y, hp_width, hp_height), 1, border_radius=5)

    # 生命值
    hp_text = f"{hero.hp}/{hero.max_hp}"
    hp_surf = font_small.render(hp_text, True, COLORS["text_white"])
    hp_rect = hp_surf.get_rect(center=(x + card_width // 2, y + card_height - 8))
    surface.blit(hp_surf, hp_rect)

    # 绘制小弟
    if hero.hp > 0:
        minion_x = x + 20
        minion_y_calc = y + card_height + 10
        for i, minion in enumerate(hero.minions):
            if minion.hp > 0:
                draw_minion(surface, minion_x, minion_y_calc, minion, is_player)
                minion_x += 40

# 绘制元素特效
def draw_element_effect(surface, center_x, center_y, element):
    """绘制元素特效"""
    color = ELEMENT_COLORS.get(element, (255, 215, 0))
    
    # 元素粒子
    for i in range(8):
        radius = 5 + i * 3
        alpha = max(0, 200 - i * 25)
        effect_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(effect_surf, (*color[:3], alpha), (radius, radius), radius)
        surface.blit(effect_surf, (center_x - radius, center_y - radius))

# 武将阵营配置
HERO_FACTIONS = {
    "赵云": "蜀",
    "关羽": "蜀",
    "张飞": "蜀",
    "马超": "蜀",
    "黄忠": "蜀",
    "诸葛亮": "蜀",
    "刘备": "蜀",
    "魏延": "蜀",
    "庞统": "蜀",
    "姜维": "蜀",
    "周瑜": "吴",
    "孙权": "吴",
    "甘宁": "吴",
    "吕布": "群雄",
    "貂蝉": "群雄",
    "华佗": "群雄",
    "曹操": "魏",
    "张辽": "魏",
    "许褚": "魏",
    "典韦": "魏",
    "司马懿": "魏"
}

# 选择武将函数
def select_heroes(screen, font_title, font_normal, font_small, clock=None):
    """选择上阵武将"""
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    # 如果没有传入clock，使用本地clock
    if clock is None:
        clock = pygame.time.Clock()
    
    # 获取可用武将
    available_heroes = list(data["heroes"].keys())
    if not available_heroes:
        # 如果没有武将，使用默认武将
        available_heroes = list(HERO_SKILLS.keys())[:3]
    
    # 选择的武将
    selected_heroes = []
    max_heroes = min(5, 1 + data["normal_dungeon"] // 2)
    
    # 按钮设置
    button_width = min(200, SCREEN_WIDTH * 0.3)
    button_height = min(50, SCREEN_HEIGHT * 0.07)
    button_spacing = min(15, SCREEN_HEIGHT * 0.025)
    
    # 主循环
    running = True
    scroll_offset = 0
    while running:
        mx, my = pygame.mouse.get_pos()
        
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        title_surf = font_title.render("选择上阵武将", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title_surf, title_rect)
        
        # 选择提示
        hint_surf = font_normal.render(f"请选择 {max_heroes} 个武将上阵", True, COLORS["text_white"])
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(hint_surf, hint_rect)
        
        # 绘制可用武将
        hero_buttons = []
        start_y = 120
        for i, hero_name in enumerate(available_heroes):
            y = start_y + i * (button_height + button_spacing) - scroll_offset
            if y > -button_height and y < SCREEN_HEIGHT - 100:
                # 检查是否已选择
                is_selected = hero_name in selected_heroes
                # 按钮颜色
                button_color = COLORS["accent_green"] if is_selected else COLORS["accent_blue"]
                hover_color = COLORS["accent_green"] if is_selected else COLORS["accent_blue"]
                
                # 创建按钮
                btn = AnimatedButton(
                    (SCREEN_WIDTH - button_width) // 2,
                    y,
                    button_width,
                    button_height,
                    f"{hero_name} (Lv.{data['heroes'].get(hero_name, {}).get('star', 1)})",
                    font_normal,
                    normal_color=button_color,
                    hover_color=hover_color
                )
                btn.update((mx, my))
                btn.draw(screen)
                hero_buttons.append((btn, hero_name))
        
        # 绘制已选择的武将
        selected_text = font_normal.render("已选择: " + ", ".join(selected_heroes) if selected_heroes else "已选择: 无", True, COLORS["text_white"])
        screen.blit(selected_text, (20, SCREEN_HEIGHT - 80))
        
        # 确认按钮
        confirm_btn = AnimatedButton(
            (SCREEN_WIDTH - button_width) // 2,
            SCREEN_HEIGHT - 60,
            button_width,
            button_height,
            "确认选择",
            font_normal,
            normal_color=COLORS["accent_green"],
            hover_color=COLORS["accent_green"]
        )
        confirm_btn.update((mx, my))
        confirm_btn.draw(screen)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return []
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 处理武将选择
                for btn, hero_name in hero_buttons:
                    if btn.rect.collidepoint(mx, my):
                        if hero_name in selected_heroes:
                            selected_heroes.remove(hero_name)
                        elif len(selected_heroes) < max_heroes:
                            selected_heroes.append(hero_name)
                # 处理确认按钮
                if confirm_btn.rect.collidepoint(mx, my) and len(selected_heroes) >= 1:
                    return selected_heroes
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset = max(0, scroll_offset - event.y * 30)
        
        pygame.display.flip()
        clock.tick(60)
    
    return []

# 选择宠物函数
def select_pet(screen, font_title, font_normal, font_small, clock=None):
    """选择上阵宠物"""
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    # 如果没有传入clock，使用本地clock
    if clock is None:
        clock = pygame.time.Clock()
    
    # 获取可用宠物
    available_pets = []
    if 'pet' in data:
        available_pets.append(data['pet'])
    if 'pet_warehouse' in data:
        available_pets.extend(data['pet_warehouse'])
    
    # 过滤出等级够高的宠物（至少3级）
    available_pets = [pet for pet in available_pets if pet.get('level', 1) >= 3]
    
    # 如果没有符合条件的宠物，返回None
    if not available_pets:
        return None
    
    # 按钮设置
    button_width = min(250, SCREEN_WIDTH * 0.4)
    button_height = min(60, SCREEN_HEIGHT * 0.08)
    button_spacing = min(20, SCREEN_HEIGHT * 0.03)
    
    # 主循环
    running = True
    selected_pet = None
    while running:
        mx, my = pygame.mouse.get_pos()
        
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        title_surf = font_title.render("选择上阵宠物", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title_surf, title_rect)
        
        # 绘制可用宠物
        pet_buttons = []
        start_y = 100
        for i, pet_dict in enumerate(available_pets):
            y = start_y + i * (button_height + button_spacing)
            if y < SCREEN_HEIGHT - 100:
                # 宠物信息
                pet_name = pet_dict.get('name', '未知宠物')
                pet_level = pet_dict.get('level', 1)
                pet_type = pet_dict.get('type', '普通')
                
                # 按钮
                btn = AnimatedButton(
                    (SCREEN_WIDTH - button_width) // 2,
                    y,
                    button_width,
                    button_height,
                    f"{pet_name} (Lv.{pet_level}, {pet_type})",
                    font_normal,
                    normal_color=COLORS["accent_purple"],
                    hover_color=COLORS["accent_purple"]
                )
                btn.update((mx, my))
                btn.draw(screen)
                pet_buttons.append((btn, pet_dict))
        
        # 跳过按钮
        skip_btn = AnimatedButton(
            (SCREEN_WIDTH - button_width) // 2,
            SCREEN_HEIGHT - 60,
            button_width,
            button_height,
            "跳过选择",
            font_normal,
            normal_color=(100, 100, 150),
            hover_color=(120, 120, 180)
        )
        skip_btn.update((mx, my))
        skip_btn.draw(screen)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 处理宠物选择
                for btn, pet_dict in pet_buttons:
                    if btn.rect.collidepoint(mx, my):
                        selected_pet = pet_dict
                        return selected_pet
                # 处理跳过按钮
                if skip_btn.rect.collidepoint(mx, my):
                    return None
        
        pygame.display.flip()
        clock.tick(60)
    
    return None

# 应用阵营增益
def apply_faction_bonus(heroes):
    """应用阵营增益"""
    # 统计各阵营的武将数量
    faction_count = {}
    for hero in heroes:
        faction = HERO_FACTIONS.get(hero.name, "无")
        faction_count[faction] = faction_count.get(faction, 0) + 1
    
    # 应用增益
    for hero in heroes:
        faction = HERO_FACTIONS.get(hero.name, "无")
        count = faction_count.get(faction, 0)
        if count >= 2:
            # 2个同阵营武将：攻击力+10%
            hero.skill["damage"] *= 1.1
        if count >= 3:
            # 3个同阵营武将：生命值+15%
            hero.max_hp *= 1.15
            hero.hp = hero.max_hp
        if count >= 4:
            # 4个同阵营武将：防御力+20%
            for minion in hero.minions:
                minion.max_hp *= 1.2
                minion.hp = minion.max_hp
        if count >= 5:
            # 5个同阵营武将：所有属性+25%
            hero.skill["damage"] *= 1.25
            hero.max_hp *= 1.25
            hero.hp = hero.max_hp
            for minion in hero.minions:
                minion.max_hp *= 1.25
                minion.hp = minion.max_hp
                minion.damage *= 1.25

# 应用宠物增益
def apply_pet_bonus(heroes, pet):
    """应用宠物增益"""
    if pet:
        # 根据宠物等级和属性提供增益
        level = pet.get('level', 1)
        attack_bonus = pet.get('attributes', {}).get('attack', 10) * 0.01
        defense_bonus = pet.get('attributes', {}).get('defense', 5) * 0.01
        speed_bonus = pet.get('attributes', {}).get('speed', 8) * 0.005
        
        for hero in heroes:
            # 攻击力增益
            hero.skill["damage"] *= (1 + attack_bonus * level * 0.1)
            # 生命值增益
            hero.max_hp *= (1 + defense_bonus * level * 0.1)
            hero.hp = hero.max_hp
            # 速度增益（影响攻击顺序）
            for minion in hero.minions:
                minion.damage *= (1 + speed_bonus * level * 0.1)

# 武将战斗主函数
def main():
    """武将回合制战斗主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
            pygame.mixer.init()
        
        # 分辨率适配
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            # 使用设置的分辨率
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 800
                SCREEN_HEIGHT = 600
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("⚔️ 武将回合制战斗")
        clock = pygame.time.Clock()

        # 字体初始化
        def init_font(size):
            font_name = get_system_font_name()
            try:
                return pygame.font.SysFont(font_name, size)
            except Exception:
                return pygame.font.Font(None, size)

        font_title = init_font(36 if not 'ANDROID_DATA' in os.environ else 52)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        font_damage = init_font(32 if not 'ANDROID_DATA' in os.environ else 48)

        # 加载音效
        attack_sound = load_sound("attack.wav")
        win_sound = load_sound("win.wav")
        skill_sound = load_sound("skill.wav")

        def play_sound(sound):
            if sound and data['settings']['sound']['enable']:
                try:
                    sound.play()
                except Exception:
                    pass

        # 天气系统初始化
        weather_system = WeatherSystem()
        current_weather = weather_system.get_current_weather()
        weather_effects = weather_system.get_weather_effects()
        
        # 天气影响战斗的效果
        weather_bonus = {
            "晴天": {"attack_bonus": 0.1, "defense_bonus": 0.0},
            "多云": {"attack_bonus": 0.05, "defense_bonus": 0.05},
            "雨天": {"attack_bonus": -0.1, "defense_bonus": 0.1, "water_element_bonus": 0.2},
            "雷暴": {"attack_bonus": 0.15, "defense_bonus": -0.1, "thunder_damage": 20, "lightning_element_bonus": 0.3},
            "雪天": {"attack_bonus": -0.05, "defense_bonus": 0.15, "ice_element_bonus": 0.2}
        }

        def get_weather_bonus():
            """获取天气加成"""
            if current_weather:
                return weather_bonus.get(current_weather["name"], {})
            return {}

        def apply_weather_effects(heroes, is_player):
            """对武将应用天气效果"""
            bonus = get_weather_bonus()
            for hero in heroes:
                # 攻击力加成
                attack_bonus = bonus.get("attack_bonus", 0)
                hero.skill["damage"] *= (1 + attack_bonus)
                
                # 防御力加成（应用到小弟）
                defense_bonus = bonus.get("defense_bonus", 0)
                for minion in hero.minions:
                    minion.max_hp = int(minion.max_hp * (1 + defense_bonus))
                    minion.hp = minion.max_hp
                
                # 元素特定加成
                element_bonus_key = f"{hero.element}_element_bonus"
                if element_bonus_key in bonus:
                    hero.skill["damage"] *= (1 + bonus[element_bonus_key])

        # 获取玩家等级
        player_level = data["normal_dungeon"]
        
        # 选择上阵武将
        selected_hero_names = select_heroes(screen, font_title, font_normal, font_small)
        if not selected_hero_names:
            # 如果没有选择武将，返回
            return
        
        # 选择上阵宠物
        selected_pet = select_pet(screen, font_title, font_normal, font_small)
        
        # 初始化装备技能
        equip_skills = {
            "weapon": EQUIP_SKILLS.get("weapon", {}).get(data["equips"].get("weapon", 0), None),
            "armor": EQUIP_SKILLS.get("armor", {}).get(data["equips"].get("armor", 0), None),
            "horse": EQUIP_SKILLS.get("horse", {}).get(data["equips"].get("horse", 0), None),
            "book": EQUIP_SKILLS.get("book", {}).get(data["equips"].get("book", 0), None)
        }
        
        # 玩家武将
        player_heroes = []
        for hero_name in selected_hero_names:
            star = data["heroes"].get(hero_name, {}).get("star", 1)
            hero = Hero(hero_name, star)
            # 分配装备技能
            hero.equip_skills = equip_skills.copy()
            # 分配枪械
            if hero_name in data.get("hero_guns", {}):
                gun_info = data["hero_guns"][hero_name]
                hero.set_gun(gun_info.get("gun_type"))
                # 应用枪械升级倍率
                gun_level = gun_info.get("gun_level", 1)
                base_multiplier = GUNS[gun_info.get("gun_type")]["damage_multiplier"]
                hero.gun_multiplier = gun_info.get("gun_multiplier", base_multiplier)
            player_heroes.append(hero)
        
        # 应用武将羁绊效果
        all_player_hero_names = [h.name for h in player_heroes]
        for hero in player_heroes:
            hero.apply_bond_effects(all_player_hero_names)
        
        # 应用阵营增益
        apply_faction_bonus(player_heroes)
        
        # 应用宠物增益
        apply_pet_bonus(player_heroes, selected_pet)
        
        # 应用天气效果
        apply_weather_effects(player_heroes, True)
        
        # 敌人武将 - 增加难度梯度
        enemy_heroes = []
        enemy_names = list(HERO_SKILLS.keys())
        random.shuffle(enemy_names)
        
        # 敌人等级随着玩家等级提升而增加，但保持合理的难度梯度
        enemy_level = min(player_level, player_level // 2 + 3)
        
        for hero_name in enemy_names[:max_heroes]:
            hero = Hero(hero_name, enemy_level)
            # 敌人装备技能随着难度提升而增强
            enemy_equip_skills = {
                "weapon": {"damage": 15 + player_level * 2, "defense": 0, "speed": 0, "critical": 0.1 + player_level * 0.01},
                "armor": {"damage": 0, "defense": 10 + player_level * 1.5, "speed": 0, "critical": 0},
                "horse": {"damage": 0, "defense": 0, "speed": 3 + player_level * 0.2, "critical": 0},
                "book": {"damage": 0, "defense": 0, "speed": 0, "critical": 0.2 + player_level * 0.01}
            }
            hero.equip_skills = enemy_equip_skills
            enemy_heroes.append(hero)
        
        # 应用天气效果到敌人
        apply_weather_effects(enemy_heroes, False)

        # 战斗数据
        turn = 0
        battle_over = False
        win = False
        animating = False
        animation_timer = 0
        current_attack = None  # (attacker, target, damage, element)

        # 物资产出 - 增加稳定奖励和难度梯度
        base_reward = data["normal_dungeon"]
        # 随着难度增加，奖励逐渐提升，但保持稳定增长
        battle_rewards = {
            "水": int(10 * base_reward * (1 + base_reward * 0.05)),
            "煤炭": int(5 * base_reward * (1 + base_reward * 0.05)),
            "木头": int(8 * base_reward * (1 + base_reward * 0.05)),
            "食物": int(7 * base_reward * (1 + base_reward * 0.05)),
            "金元宝": int(2 * base_reward * (1 + base_reward * 0.08)),
            "普通子弹": int(5 * base_reward * (1 + base_reward * 0.03)),
            "高级子弹": int(3 * base_reward * (1 + base_reward * 0.02)),
            "稀有子弹": int(1 * base_reward * (1 + base_reward * 0.01))
        }

        # 增加额外奖励机会
        if random.random() < 0.3:
            # 有30%几率获得额外奖励
            extra_reward = random.choice(["水", "煤炭", "木头", "食物", "金元宝"])
            battle_rewards[extra_reward] += int(battle_rewards[extra_reward] * 0.5)

        # 特效
        particles = []
        floating_texts = []
        
        # 装备技能卡片
        skill_cards = []
        card_width = min(120, SCREEN_WIDTH * 0.15)
        card_height = min(80, SCREEN_HEIGHT * 0.12)
        card_y = SCREEN_HEIGHT - card_height - 30
        
        # 技能类型和颜色
        skill_info = [
            ("weapon", "⚔️ 武器", (200, 60, 60), (240, 90, 90)),
            ("armor", "🛡️ 防具", (60, 120, 60), (80, 160, 80)),
            ("horse", "🐎 坐骑", (60, 120, 200), (80, 160, 255)),
            ("book", "📚 书籍", (180, 100, 220), (200, 130, 255))
        ]
        
        for i, (skill_type, skill_name, normal_color, hover_color) in enumerate(skill_info):
            x = 50 + i * (card_width + 15)
            if x + card_width > SCREEN_WIDTH - 50:
                break
            card = AnimatedButton(
                x, card_y,
                card_width, card_height, skill_name, font_small,
                normal_color=normal_color, hover_color=hover_color
            )
            skill_cards.append((card, skill_type))

        # 武将技能卡片
        hero_skill_cards = []
        hero_card_width = min(150, SCREEN_WIDTH * 0.18)
        hero_card_height = min(80, SCREEN_HEIGHT * 0.12)
        hero_card_y = SCREEN_HEIGHT - hero_card_height - card_height - 50

        # 必杀技卡片
        ultimate_card_width = min(200, SCREEN_WIDTH * 0.25)
        ultimate_card_height = min(70, SCREEN_HEIGHT * 0.1)
        ultimate_card_y = SCREEN_HEIGHT - card_height - hero_card_height - ultimate_card_height - 70
        ultimate_card = AnimatedButton(
            (SCREEN_WIDTH - ultimate_card_width) // 2, ultimate_card_y,
            ultimate_card_width, ultimate_card_height, "🔥 必杀技", font_small,
            normal_color=(200, 50, 50), hover_color=(255, 80, 80)
        )


        # 返回按钮（提前创建）
        return_btn_width = min(180, SCREEN_WIDTH * 0.25)
        return_btn_height = min(50, SCREEN_HEIGHT * 0.08)
        return_btn_y = SCREEN_HEIGHT - return_btn_height - 30
        return_btn = AnimatedButton(
            (SCREEN_WIDTH - return_btn_width) // 2, return_btn_y,
            return_btn_width, return_btn_height, "↩️ 返回", font_normal,
            normal_color=(60, 150, 60), hover_color=(80, 200, 80)
        )

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 背景装饰
            for i in range(5):
                y = 100 + i * 100
                alpha = 20 + i * 10
                pygame.draw.line(screen, (*COLORS["accent_gold"][:3], alpha), (0, y), (SCREEN_WIDTH, y), 1)

            if not battle_over:
                # 标题
                title_surf = font_title.render("⚔️ 武将回合制战斗", True, COLORS["accent_gold"])
                title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
                screen.blit(title_surf, title_rect)
                
                # 回合数
                turn_surf = font_normal.render(f"第 {turn} 回合", True, COLORS["text_gray"])
                turn_rect = turn_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
                screen.blit(turn_surf, turn_rect)
                
                # 天气显示
                if current_weather:
                    weather_icon = {"晴天": "☀️", "多云": "☁️", "雨天": "🌧️", "雷暴": "⛈️", "雪天": "❄️"}.get(current_weather["name"], "🌤️")
                    weather_text = f"{weather_icon} {current_weather['name']}"
                    weather_surf = font_small.render(weather_text, True, current_weather["color"])
                    screen.blit(weather_surf, (20, 20))

                # 绘制玩家武将
                player_y = 120
                for i, hero in enumerate(player_heroes):
                    if hero.hp > 0:
                        x = 50 + i * 200
                        if x + 180 > SCREEN_WIDTH // 2:
                            break
                        draw_hero_card(screen, x, player_y, hero, True, font_normal, font_small)

                # 绘制敌人武将
                enemy_y = 120
                for i, hero in enumerate(enemy_heroes):
                    if hero.hp > 0:
                        x = SCREEN_WIDTH - 230 - i * 200
                        if x < SCREEN_WIDTH // 2:
                            break
                        draw_hero_card(screen, x, enemy_y, hero, False, font_normal, font_small)

                # 战斗特效
                if animating:
                    animation_timer += 1
                    if current_attack:
                        attacker, target, damage, element = current_attack
                        # 计算攻击位置
                        if hasattr(attacker, 'name'):  # 是武将
                            try:
                                if attacker in player_heroes:
                                    attacker_x = 50 + player_heroes.index(attacker) * 200 + 90
                                elif attacker in enemy_heroes:
                                    attacker_x = SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90
                                else:
                                    attacker_x = SCREEN_WIDTH // 2
                            except Exception:
                                attacker_x = SCREEN_WIDTH // 2
                        else:  # 是小弟
                            # 找到小弟所属的武将
                            attacker_x = SCREEN_WIDTH // 2
                            try:
                                for hero in player_heroes:
                                    if attacker in hero.minions:
                                        attacker_x = 50 + player_heroes.index(hero) * 200 + 90
                                        break
                                else:
                                    for hero in enemy_heroes:
                                        if attacker in hero.minions:
                                            attacker_x = SCREEN_WIDTH - 230 - enemy_heroes.index(hero) * 200 + 90
                                            break
                            except Exception:
                                pass
                        
                        try:
                            if target in player_heroes:
                                target_x = 50 + player_heroes.index(target) * 200 + 90
                            elif target in enemy_heroes:
                                target_x = SCREEN_WIDTH - 230 - enemy_heroes.index(target) * 200 + 90
                            else:
                                target_x = SCREEN_WIDTH // 2
                        except Exception:
                            target_x = SCREEN_WIDTH // 2
                        # 绘制攻击特效
                        draw_element_effect(screen, target_x, 230, element)
                    if animation_timer > 30:
                        animating = False
                        animation_timer = 0
                        current_attack = None

                # 武将技能卡片
            hero_skill_cards = []
            for i, hero in enumerate(player_heroes):
                if hero.hp > 0:
                    x = 50 + i * (hero_card_width + 15)
                    if x + hero_card_width > SCREEN_WIDTH - 50:
                        break
                    # 创建武将技能卡片
                    card = AnimatedButton(
                        x, hero_card_y,
                        hero_card_width, hero_card_height, f"{hero.name}: {hero.skill['name']}", font_small,
                        normal_color=ELEMENT_COLORS.get(hero.element, (200, 150, 50)),
                        hover_color=ELEMENT_COLORS.get(hero.element, (240, 190, 90))
                    )
                    if not animating:
                        card.update((mx, my))
                    card.draw(screen)
                    hero_skill_cards.append((card, hero))

            # 技能卡片
            for card, skill_type in skill_cards:
                if not animating:
                    card.update((mx, my))
                card.draw(screen)

            # 更新武将连击状态
            for hero in player_heroes + enemy_heroes:
                hero.update_combo()

            # 绘制连击显示
            combo_text = font_small.render(f"连击: {max(h.combo_count for h in player_heroes)}", True, COLORS["accent_gold"])
            screen.blit(combo_text, (SCREEN_WIDTH // 2 - 60, 50))

            # 绘制怒气条
            if player_heroes:
                main_hero = player_heroes[0]
                rage_ratio = main_hero.rage / main_hero.max_rage
                rage_width = 200
                rage_height = 20
                rage_x = SCREEN_WIDTH // 2 - rage_width // 2
                rage_y = 30
                
                pygame.draw.rect(screen, COLORS["hp_bg"], (rage_x, rage_y, rage_width, rage_height), border_radius=10)
                rage_bar_width = int(rage_width * rage_ratio)
                pygame.draw.rect(screen, (255, 100, 50), (rage_x, rage_y, rage_bar_width, rage_height), border_radius=10)
                pygame.draw.rect(screen, COLORS["text_white"], (rage_x, rage_y, rage_width, rage_height), 2, border_radius=10)
                
                rage_text = font_small.render(f"怒气: {main_hero.rage}/{main_hero.max_rage}", True, COLORS["text_white"])
                screen.blit(rage_text, (SCREEN_WIDTH // 2 - 50, rage_y - 20))

            # 必杀技按钮
            has_rage = any(h.can_use_ultimate() for h in player_heroes if h.hp > 0)
            if has_rage:
                ultimate_card.text = f"🔥 {main_hero.ultimate_skill['name']}"
                ultimate_card.normal_color = (255, 80, 80)
                ultimate_card.hover_color = (255, 120, 120)
            else:
                ultimate_card.text = "🔥 必杀技 (蓄力中)"
                ultimate_card.normal_color = (100, 50, 50)
                ultimate_card.hover_color = (120, 60, 60)
            
            if not animating:
                ultimate_card.update((mx, my))
                ultimate_card.draw(screen)

                # 武将信息
                hero_info_y = SCREEN_HEIGHT - card_height - hero_card_height - 130
                info_text = f"我方武将: {sum(1 for h in player_heroes if h.hp > 0)}/{len(player_heroes)}"
                info_surf = font_small.render(info_text, True, COLORS["text_white"])
                screen.blit(info_surf, (50, hero_info_y))

                info_text = f"敌方武将: {sum(1 for h in enemy_heroes if h.hp > 0)}/{len(enemy_heroes)}"
                info_surf = font_small.render(info_text, True, COLORS["text_white"])
                screen.blit(info_surf, (SCREEN_WIDTH - 200, hero_info_y))

                bullet_info_y = hero_info_y + 25
                for bullet_type in ["普通子弹", "高级子弹", "稀有子弹"]:
                    amount = data["resources"].get(bullet_type, 0)
                    bullet_icon = "🔫"
                    bullet_text = f"{bullet_icon} {bullet_type}: {amount}"
                    bullet_surf = font_small.render(bullet_text, True, COLORS["text_gray"])
                    screen.blit(bullet_surf, (50, bullet_info_y))
                    bullet_info_y += 20

                # 更新和绘制特效
                for p in particles[:]:
                    p.update()
                    p.draw(screen)
                    if p.life <= 0:
                        particles.remove(p)

                for ft in floating_texts[:]:
                    ft.update()
                    ft.draw(screen)
                    if ft.life <= 0:
                        floating_texts.remove(ft)

                # 事件处理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.MOUSEBUTTONDOWN and not animating:
                        # 必杀技按钮点击
                        if ultimate_card.rect.collidepoint(mx, my) and not battle_over:
                            play_sound(skill_sound)
                            animating = True
                            animation_timer = 0
                            
                            # 找到可以使用必杀技的武将
                            for hero in player_heroes:
                                if hero.hp > 0 and hero.can_use_ultimate():
                                    alive_enemies = [h for h in enemy_heroes if h.hp > 0]
                                    if alive_enemies:
                                        target = random.choice(alive_enemies)
                                        damage, success = hero.use_ultimate(target)
                                        if success:
                                            current_attack = (hero, target, damage, hero.element)
                                            
                                            # 伤害数字（特殊效果）
                                            target_x = SCREEN_WIDTH - 230 - enemy_heroes.index(target) * 200 + 90
                                            damage_text = f"💥 -{int(damage)}"
                                            floating_texts.append(FloatingText(
                                                damage_text, target_x, 200,
                                                (255, 100, 50), font_damage
                                            ))
                                            
                                            # 必杀技特效 - 流星效果
                                            for _ in range(3):
                                                particles.append(Particle(
                                                    random.randint(0, SCREEN_WIDTH), 0,
                                                    (255, 150, 50), 0, 10, random.randint(30, 50)
                                                ))
                                            
                                            # 大量爆炸粒子
                                            for _ in range(50):
                                                particles.append(Particle(
                                                    target_x, 230,
                                                    (255, 200, 100), 8, random.randint(5, 15), 60
                                                ))
                                            
                                            # 检查敌人是否全部死亡
                                            if all(h.hp <= 0 for h in enemy_heroes):
                                                battle_over = True
                                                win = True
                                                play_sound(win_sound)
                                                for res, amt in battle_rewards.items():
                                                    data["resources"][res] = data["resources"].get(res, 0) + amt
                                                data["normal_dungeon"] += 1
                                                save()
                                                
                                                for _ in range(50):
                                                    particles.append(Particle(
                                                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                        COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                                    ))
                                            else:
                                                # 敌人回合
                                                for attacker in enemy_heroes:
                                                    if attacker.hp > 0:
                                                        alive_players = [h for h in player_heroes if h.hp > 0]
                                                        if alive_players:
                                                            target = random.choice(alive_players)
                                                            damage = attacker.attack(target)
                                                            current_attack = (attacker, target, damage, attacker.element)
                                                            
                                                            target_x = 50 + player_heroes.index(target) * 200 + 90
                                                            damage_text = f"-{int(damage)}"
                                                            floating_texts.append(FloatingText(
                                                                damage_text, target_x, 200,
                                                                ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]), font_damage
                                                            ))
                                                            
                                                            draw_element_effect(screen, target_x, 230, attacker.element)
                                                            
                                                            if all(h.hp <= 0 for h in player_heroes):
                                                                battle_over = True
                                                                win = False
                                                                break
                                                        else:
                                                            battle_over = True
                                                            win = False
                                                            break
                                            
                                            turn += 1
                                            break
                            break
                        
                        # 武将技能卡片点击
                        for card, hero in hero_skill_cards:
                            if card.rect.collidepoint(mx, my) and not battle_over:
                                play_sound(skill_sound)
                                animating = True
                                animation_timer = 0
                                
                                # 玩家使用武将技能（大招）
                                if hero.hp > 0:
                                    # 选择一个活着的敌人
                                    alive_enemies = [h for h in enemy_heroes if h.hp > 0]
                                    if alive_enemies:
                                        target = random.choice(alive_enemies)
                                        # 使用武将的大招（技能）
                                        damage = hero.attack(target) * hero.get_combo_bonus()
                                        hero.add_combo()
                                        hero.add_rage()
                                        if damage > 0:
                                            current_attack = (hero, target, damage, hero.element)
                                            
                                            # 伤害数字
                                            target_x = SCREEN_WIDTH - 230 - enemy_heroes.index(target) * 200 + 90
                                            damage_text = f"-{int(damage)}"
                                            floating_texts.append(FloatingText(
                                                damage_text, target_x, 200,
                                                ELEMENT_COLORS.get(hero.element, COLORS["accent_red"]), font_damage
                                            ))
                                            
                                            # 技能特效
                                            draw_element_effect(screen, target_x, 230, hero.element)
                                            
                                            # 技能粒子
                                            for _ in range(20):
                                                angle = math.atan2(230 - 230, target_x - (50 + player_heroes.index(hero) * 200 + 90))
                                                particles.append(Particle(
                                                    50 + player_heroes.index(hero) * 200 + 90,
                                                    230,
                                                    ELEMENT_COLORS.get(hero.element, COLORS["accent_red"]),
                                                    6, random.randint(5, 10), 50, angle
                                                ))
                                            
                                            # 小弟攻击
                                            for minion in hero.minions:
                                                if minion.hp > 0:
                                                    damage = minion.attack(target)
                                                    current_attack = (minion, target, damage, minion.element)
                                                    
                                                    # 伤害数字
                                                    damage_text = f"-{damage}"
                                                    floating_texts.append(FloatingText(
                                                        damage_text, target_x, 200,
                                                        ELEMENT_COLORS.get(minion.element, COLORS["accent_red"]), font_small
                                                    ))
                                                    
                                                    # 攻击粒子
                                                    for _ in range(8):
                                                        angle = math.atan2(230 - 230, target_x - (50 + player_heroes.index(hero) * 200 + 90))
                                                        particles.append(Particle(
                                                            50 + player_heroes.index(hero) * 200 + 90,
                                                            230,
                                                            ELEMENT_COLORS.get(minion.element, COLORS["accent_red"]),
                                                            3, random.randint(3, 5), 30, angle
                                                        ))
                                            
                                            # 检查敌人是否全部死亡
                                            if all(h.hp <= 0 for h in enemy_heroes):
                                                battle_over = True
                                                win = True
                                                play_sound(win_sound)
                                                # 发放奖励
                                                for res, amt in battle_rewards.items():
                                                    data["resources"][res] = data["resources"].get(res, 0) + amt
                                                data["normal_dungeon"] += 1
                                                save()
                                                
                                                # 胜利特效
                                                for _ in range(50):
                                                    particles.append(Particle(
                                                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                        COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                                    ))
                                            else:
                                                # 敌人回合
                                                for attacker in enemy_heroes:
                                                    if attacker.hp > 0:
                                                        # 选择一个活着的玩家武将
                                                        alive_players = [h for h in player_heroes if h.hp > 0]
                                                        if alive_players:
                                                            target = random.choice(alive_players)
                                                            # 敌人使用技能
                                                            damage = attacker.attack(target)
                                                            if damage > 0:
                                                                current_attack = (attacker, target, damage, attacker.element)
                                                                
                                                                # 伤害数字
                                                                target_x = 50 + player_heroes.index(target) * 200 + 90
                                                                damage_text = f"-{int(damage)}"
                                                                floating_texts.append(FloatingText(
                                                                    damage_text, target_x, 200,
                                                                    ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]), font_damage
                                                                ))
                                                                
                                                                # 技能特效
                                                                draw_element_effect(screen, target_x, 230, attacker.element)
                                                                
                                                                # 技能粒子
                                                                for _ in range(20):
                                                                    angle = math.atan2(230 - 230, target_x - (SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90))
                                                                    particles.append(Particle(
                                                                        SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90,
                                                                        230,
                                                                        ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]),
                                                                        6, random.randint(5, 10), 50, angle
                                                                    ))
                                                                
                                                                # 小弟攻击
                                                                for minion in attacker.minions:
                                                                    if minion.hp > 0:
                                                                        damage = minion.attack(target)
                                                                        current_attack = (minion, target, damage, minion.element)
                                                                        
                                                                        # 伤害数字
                                                                        damage_text = f"-{damage}"
                                                                        floating_texts.append(FloatingText(
                                                                            damage_text, target_x, 200,
                                                                            ELEMENT_COLORS.get(minion.element, COLORS["accent_red"]), font_small
                                                                        ))
                                                                        
                                                                        # 攻击粒子
                                                                        for _ in range(8):
                                                                            angle = math.atan2(230 - 230, target_x - (SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90))
                                                                            particles.append(Particle(
                                                                                SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90,
                                                                                230,
                                                                                ELEMENT_COLORS.get(minion.element, COLORS["accent_red"]),
                                                                                3, random.randint(3, 5), 30, angle
                                                                            ))
                                                                
                                                                # 检查玩家是否全部死亡
                                                                if all(h.hp <= 0 for h in player_heroes):
                                                                    battle_over = True
                                                                    win = False
                                                                    # 失败特效
                                                                    for _ in range(30):
                                                                        particles.append(Particle(
                                                                            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                                            COLORS["accent_red"], 6, random.randint(3, 8), 60
                                                                        ))
                                                                    break
                                                        else:
                                                            # 没有玩家了
                                                            battle_over = True
                                                            win = False
                                                            # 失败特效
                                                            for _ in range(30):
                                                                particles.append(Particle(
                                                                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                                    COLORS["accent_red"], 6, random.randint(3, 8), 60
                                                                ))
                                                            break
                                            
                                            # 回合结束 - 处理元素效果
                                            for hero in player_heroes + enemy_heroes:
                                                if hero.hp > 0:
                                                    # 处理灼烧效果
                                                    if hero.burn_turns > 0:
                                                        burn_dmg = hero.burn_damage
                                                        hero.hp = max(0, hero.hp - burn_dmg)
                                                        floating_texts.append(FloatingText(
                                                            hero.name if hasattr(hero, 'name') else "小弟",
                                                            f"灼烧 -{burn_dmg}", COLORS["accent_red"],
                                                            SCREEN_WIDTH // 2, 300
                                                        ))
                                                        hero.burn_turns -= 1
                                                    # 处理护盾
                                                    if hero.shield > 0:
                                                        hero.shield = 0
                                                    # 处理减速
                                                    if hero.slow_turns > 0:
                                                        hero.slow_turns -= 1
                                            
                                            # 回合结束
                                            turn += 1
                                    else:
                                        # 没有敌人了
                                        battle_over = True
                                        win = True
                                        play_sound(win_sound)
                                        # 发放奖励
                                        for res, amt in battle_rewards.items():
                                            data["resources"][res] = data["resources"].get(res, 0) + amt
                                        data["normal_dungeon"] += 1
                                        save()
                                        
                                        # 胜利特效
                                        for _ in range(50):
                                            particles.append(Particle(
                                                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                            ))
                        
                        # 技能卡片点击
                        for card, skill_type in skill_cards:
                            if card.rect.collidepoint(mx, my) and not battle_over:
                                play_sound(skill_sound)
                                animating = True
                                animation_timer = 0
                                
                                # 玩家使用装备技能
                                for attacker in player_heroes:
                                    if attacker.hp > 0:
                                        # 选择一个活着的敌人
                                        alive_enemies = [h for h in enemy_heroes if h.hp > 0]
                                        if alive_enemies:
                                            target = random.choice(alive_enemies)
                                            damage, skill_effect = attacker.use_skill(skill_type, target)
                                            if damage > 0:
                                                current_attack = (attacker, target, damage, attacker.element)
                                                
                                                # 伤害数字
                                                target_x = SCREEN_WIDTH - 230 - enemy_heroes.index(target) * 200 + 90
                                                if skill_type == "armor":
                                                    # 防具技能：恢复
                                                    damage_text = f"+{int(damage)}"
                                                    floating_texts.append(FloatingText(
                                                        damage_text, 50 + player_heroes.index(attacker) * 200 + 90, 200,
                                                        COLORS["accent_green"], font_damage, False
                                                    ))
                                                else:
                                                    # 其他技能：伤害
                                                    damage_text = f"-{int(damage)}"
                                                    floating_texts.append(FloatingText(
                                                        damage_text, target_x, 200,
                                                        ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]), font_damage
                                                    ))
                                                
                                                # 技能特效
                                                if skill_effect:
                                                    draw_skill_effect(screen, 50 + player_heroes.index(attacker) * 200 + 90, 230, skill_effect)
                                                
                                                # 技能粒子
                                                for _ in range(20):
                                                    angle = math.atan2(230 - 230, target_x - (50 + player_heroes.index(attacker) * 200 + 90))
                                                    particles.append(Particle(
                                                        50 + player_heroes.index(attacker) * 200 + 90,
                                                        230,
                                                        ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]),
                                                        6, random.randint(5, 10), 50, angle
                                                    ))
                                                
                                                # 检查敌人是否全部死亡
                                                if all(h.hp <= 0 for h in enemy_heroes):
                                                    battle_over = True
                                                    win = True
                                                    play_sound(win_sound)
                                                    # 发放奖励
                                                    for res, amt in battle_rewards.items():
                                                        data["resources"][res] = data["resources"].get(res, 0) + amt
                                                    data["normal_dungeon"] += 1
                                                    save()
                                                    
                                                    # 胜利特效
                                                    for _ in range(50):
                                                        particles.append(Particle(
                                                            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                            COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                                        ))
                                                    break
                                        else:
                                            # 没有敌人了
                                            battle_over = True
                                            win = True
                                            play_sound(win_sound)
                                            # 发放奖励
                                            for res, amt in battle_rewards.items():
                                                data["resources"][res] = data["resources"].get(res, 0) + amt
                                            data["normal_dungeon"] += 1
                                            save()
                                            
                                            # 胜利特效
                                            for _ in range(50):
                                                particles.append(Particle(
                                                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                    COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                                ))
                                            break
                                
                                # 敌人回合
                                if not battle_over:
                                    for attacker in enemy_heroes:
                                        if attacker.hp > 0:
                                            # 选择一个活着的玩家武将
                                            alive_players = [h for h in player_heroes if h.hp > 0]
                                            if alive_players:
                                                target = random.choice(alive_players)
                                                # 敌人也使用技能
                                                skill_types = ["weapon", "armor", "horse", "book"]
                                                skill_type = random.choice(skill_types)
                                                damage, skill_effect = attacker.use_skill(skill_type, target)
                                                if damage > 0:
                                                    current_attack = (attacker, target, damage, attacker.element)
                                                    
                                                    # 伤害数字
                                                    target_x = 50 + player_heroes.index(target) * 200 + 90
                                                    if skill_type == "armor":
                                                        # 防具技能：恢复
                                                        damage_text = f"+{int(damage)}"
                                                        floating_texts.append(FloatingText(
                                                            damage_text, SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90, 200,
                                                            COLORS["accent_green"], font_damage, False
                                                        ))
                                                    else:
                                                        # 其他技能：伤害
                                                        damage_text = f"-{int(damage)}"
                                                        floating_texts.append(FloatingText(
                                                            damage_text, target_x, 200,
                                                            ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]), font_damage
                                                        ))
                                                    
                                                    # 技能特效
                                                    if skill_effect:
                                                        draw_skill_effect(screen, SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90, 230, skill_effect)
                                                    
                                                    # 技能粒子
                                                    for _ in range(20):
                                                        angle = math.atan2(230 - 230, target_x - (SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90))
                                                        particles.append(Particle(
                                                            SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90,
                                                            230,
                                                            ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]),
                                                            6, random.randint(5, 10), 50, angle
                                                        ))
                                                    
                                                    # 检查玩家是否全部死亡
                                                    if all(h.hp <= 0 for h in player_heroes):
                                                        battle_over = True
                                                        win = False
                                                        break
                                                else:
                                                    # 如果技能没有效果，使用普通攻击
                                                    damage = attacker.attack(target)
                                                    current_attack = (attacker, target, damage, attacker.element)
                                                    
                                                    # 伤害数字
                                                    target_x = 50 + player_heroes.index(target) * 200 + 90
                                                    damage_text = f"-{damage}"
                                                    floating_texts.append(FloatingText(
                                                        damage_text, target_x, 200,
                                                        ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]), font_damage
                                                    ))
                                                    
                                                    # 攻击粒子
                                                    for _ in range(15):
                                                        angle = math.atan2(230 - 230, target_x - (SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90))
                                                        particles.append(Particle(
                                                            SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90,
                                                            230,
                                                            ELEMENT_COLORS.get(attacker.element, COLORS["accent_red"]),
                                                            5, random.randint(4, 8), 40, angle
                                                        ))
                                                        
                                                    # 检查玩家是否全部死亡
                                                    if all(h.hp <= 0 for h in player_heroes):
                                                        battle_over = True
                                                        win = False
                                                        break
                                            else:
                                                # 没有玩家了
                                                battle_over = True
                                                win = False
                                                break
                                
                                turn += 1
                                break
                        

            else:
                # 战斗结果
                if win:
                    # 胜利标题
                    win_surf = font_title.render("🎉 战斗胜利！", True, COLORS["accent_green"])
                    win_rect = win_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
                    screen.blit(win_surf, win_rect)
                    
                    # 奖励面板
                    panel_y = 140
                    panel_surf = pygame.Surface((400, 280), pygame.SRCALPHA)
                    pygame.draw.rect(panel_surf, (40, 40, 70, 200), (0, 0, 400, 280), border_radius=15)
                    screen.blit(panel_surf, ((SCREEN_WIDTH - 400) // 2, panel_y))
                    pygame.draw.rect(screen, COLORS["accent_gold"], 
                                   ((SCREEN_WIDTH - 400) // 2, panel_y, 400, 280), 2, border_radius=15)
                    
                    # 奖励标题
                    reward_title = font_normal.render("💎 获得奖励", True, COLORS["accent_gold"])
                    screen.blit(reward_title, ((SCREEN_WIDTH - 400) // 2 + 20, panel_y + 20))
                    
                    # 奖励列表
                    y_offset = panel_y + 70
                    for res, amt in battle_rewards.items():
                        icon = {"水": "💧", "煤炭": "⚫", "木头": "🪵", "食物": "🍞", "金元宝": "💰", "普通子弹": "🔫", "高级子弹": "🔫🔫", "稀有子弹": "🔫🔥"}.get(res, "📦")
                        reward_text = font_small.render(f"{icon} {res} × {amt}", True, COLORS["text_white"])
                        screen.blit(reward_text, ((SCREEN_WIDTH - 400) // 2 + 40, y_offset))
                        y_offset += 40
                else:
                    # 失败标题
                    lose_surf = font_title.render("💀 战斗失败！", True, COLORS["accent_red"])
                    lose_rect = lose_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
                    screen.blit(lose_surf, lose_rect)
                    
                    hint_surf = font_normal.render("请重新挑战", True, COLORS["text_gray"])
                    hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, 220))
                    screen.blit(hint_surf, hint_rect)

                # 返回按钮（使用预先创建的按钮）
                return_btn.update((mx, my))
                return_btn.draw(screen)

                # 特效
                for p in particles[:]:
                    p.update()
                    p.draw(screen)
                    if p.life <= 0:
                        particles.remove(p)

                # 事件处理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if return_btn.rect.collidepoint(mx, my):
                            running = False

            pygame.display.flip()
            clock.tick(60)

        # 确保退出时更新统计
        if battle_over:
            update_battle_stats(win, player_heroes, enemy_heroes)
        
        safe_exit("战斗模块")
    except Exception as e:
        safe_exit("战斗模块", str(e))

if __name__ == "__main__":
    main()
