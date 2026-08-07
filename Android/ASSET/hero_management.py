import os
import pygame
import random
import math
from ASSET.game_data import data, save, get_system_font_name, HERO_SKILLS, HERO_BONDS
from ASSET.hero_database import HERO_DATABASE, FACTIONS as HERO_FACTION_MAP
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

ELEMENT_COLORS = {
    "火": (255, 100, 100),
    "水": (100, 150, 255),
    "土": (150, 100, 50),
    "风": (100, 200, 100),
    "雷": (200, 100, 255),
    "暗": (80, 80, 120),
    "木": (50, 200, 100)
}

WEAPON_ICONS = {
    "枪": "⚔️", "刀": "🗡️", "剑": "⚔️", "戟": "💥",
    "弓": "🏹", "斧": "🪓", "锤": "🔨", "鞭": "🪢",
    "棍": "🥋", "扇": "🪭", "琴": "🎹", "书": "📖",
    "医": "🌿", "骑": "🐎"
}

HERO_ICONS = {
    "赵云": "⚔️", "关羽": "🗡️", "张飞": "🛡️", "马超": "🐎", "黄忠": "🏹",
    "诸葛亮": "🧠", "周瑜": "🔥", "吕布": "💥", "貂蝉": "🌸", "华佗": "🌿",
    "曹操": "👑", "张辽": "⚔️", "许褚": "💪", "典韦": "🗡️", "司马懿": "🦉",
    "孙权": "👑", "甘宁": "⚔️", "吕蒙": "🗡️", "陆逊": "🔥", "孙策": "⚔️",
    "刘备": "👑", "魏延": "⚔️", "庞统": "🧠", "姜维": "⚔️", "黄盖": "🛡️",
    "袁绍": "👑", "袁术": "👑", "董卓": "👹", "王允": "🧠", "夏侯渊": "🏹",
    "曹洪": "🛡️", "张济": "⚔️", "张郃": "🏹", "夏侯惇": "⚔️", "荀彧": "🧠",
    "郭嘉": "🧠", "贾诩": "🦉", "蒋钦": "⚔️", "徐盛": "🛡️", "潘璋": "⚔️"
}

def get_hero_icon(hero_name):
    if hero_name in HERO_ICONS:
        return HERO_ICONS[hero_name]
    hero_info = HERO_DATABASE.get(hero_name, {})
    weapon_type = hero_info.get("weapon_type", "")
    return WEAPON_ICONS.get(weapon_type, "⚔️")

ADVANCEMENT_LEVELS = [
    {"level": 1, "name": "凡", "bonus": {"attack": 0.1, "defense": 0.1, "health": 0.1}, "cost": {"金元宝": 100, "经验": 500}},
    {"level": 2, "name": "铁", "bonus": {"attack": 0.2, "defense": 0.2, "health": 0.2}, "cost": {"金元宝": 300, "经验": 1000}},
    {"level": 3, "name": "铜", "bonus": {"attack": 0.35, "defense": 0.35, "health": 0.35}, "cost": {"金元宝": 500, "经验": 2000}},
    {"level": 4, "name": "银", "bonus": {"attack": 0.5, "defense": 0.5, "health": 0.5}, "cost": {"金元宝": 1000, "经验": 5000}},
    {"level": 5, "name": "金", "bonus": {"attack": 0.75, "defense": 0.75, "health": 0.75}, "cost": {"金元宝": 2000, "经验": 10000}},
    {"level": 6, "name": "玉", "bonus": {"attack": 1.0, "defense": 1.0, "health": 1.0}, "cost": {"金元宝": 5000, "经验": 20000}},
    {"level": 7, "name": "仙", "bonus": {"attack": 1.3, "defense": 1.3, "health": 1.3}, "cost": {"金元宝": 10000, "经验": 50000}},
    {"level": 8, "name": "圣", "bonus": {"attack": 1.6, "defense": 1.6, "health": 1.6}, "cost": {"金元宝": 20000, "经验": 100000}}
]

AWAKENING_STAGES = [
    {"stage": 0, "name": "未觉醒", "bonus": {}, "skill_enhance": 0},
    {"stage": 1, "name": "初醒", "bonus": {"attack": 0.15, "critical_chance": 0.05}, "skill_enhance": 0.2, "cost": {"金元宝": 500, "武将碎片": 20}},
    {"stage": 2, "name": "觉醒", "bonus": {"attack": 0.3, "critical_chance": 0.1, "skill_damage": 0.3}, "skill_enhance": 0.5, "cost": {"金元宝": 1500, "武将碎片": 50}},
    {"stage": 3, "name": "超觉醒", "bonus": {"attack": 0.5, "critical_chance": 0.15, "skill_damage": 0.5, "heal_on_kill": 0.2}, "skill_enhance": 0.8, "cost": {"金元宝": 5000, "武将碎片": 100}},
    {"stage": 4, "name": "神觉醒", "bonus": {"attack": 0.8, "critical_chance": 0.2, "skill_damage": 0.8, "heal_on_kill": 0.3, "damage_reduction": 0.1}, "skill_enhance": 1.2, "cost": {"金元宝": 15000, "武将碎片": 200}}
]

STAR_COSTS = [
    {"stars": 1, "cost": {"金元宝": 0}},
    {"stars": 2, "cost": {"金元宝": 200, "武将碎片": 10}},
    {"stars": 3, "cost": {"金元宝": 500, "武将碎片": 30}},
    {"stars": 4, "cost": {"金元宝": 1000, "武将碎片": 50}},
    {"stars": 5, "cost": {"金元宝": 2000, "武将碎片": 100}},
    {"stars": 6, "cost": {"金元宝": 5000, "武将碎片": 200}},
    {"stars": 7, "cost": {"金元宝": 10000, "武将碎片": 400}},
    {"stars": 8, "cost": {"金元宝": 20000, "武将碎片": 800}},
    {"stars": 9, "cost": {"金元宝": 50000, "武将碎片": 1500}},
    {"stars": 10, "cost": {"金元宝": 100000, "武将碎片": 3000}}
]

class Particle:
    def __init__(self, x, y, color, speed, size, life, gravity=0.1):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = random.uniform(-speed, speed)
        self.speed_y = random.uniform(-speed, speed)
        self.gravity = gravity
        self.size = size
        self.life = life
        self.max_life = life
    
    def update(self):
        self.speed_y += self.gravity
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

class HeroManagementSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "hero_management" not in data:
            data["hero_management"] = {
                "heroes": {},
                "bonds": {},
                "collection": []
            }
        
        if "heroes" in data and isinstance(data["heroes"], list):
            for hero in data["heroes"]:
                hero_name = hero["name"]
                if hero_name not in data["hero_management"]["heroes"]:
                    data["hero_management"]["heroes"][hero_name] = {
                        "level": hero.get("level", 1),
                        "experience": hero.get("experience", 0),
                        "attack": hero.get("attack", 100),
                        "defense": hero.get("defense", 50),
                        "health": hero.get("health", 200),
                        "quality": hero.get("quality", "common"),
                        "skill": hero.get("skill", "普通攻击"),
                        "advancement": 1,
                        "awakening": 0,
                        "star": hero.get("star", 1),
                        "equipped_skills": {},
                        "element": hero.get("element", "火"),
                        "faction": self._get_faction(hero_name)
                    }
            save()
    
    def _get_faction(self, hero_name):
        # 从HERO_DATABASE动态获取阵营（覆盖全部135名武将）
        hero_info = HERO_DATABASE.get(hero_name, {})
        faction_key = hero_info.get("faction", "qun")
        return HERO_FACTION_MAP.get(faction_key, {}).get("name", "群")
    
    def get_hero(self, hero_name):
        return data["hero_management"]["heroes"].get(hero_name, None)
    
    def get_all_heroes(self):
        return data["hero_management"]["heroes"]
    
    def calculate_stats(self, hero_name):
        hero = self.get_hero(hero_name)
        if not hero:
            return None
        
        base_stats = {
            "attack": hero["attack"],
            "defense": hero["defense"],
            "health": hero["health"]
        }
        
        quality_multiplier = QUALITY_INFO[hero["quality"]]["multiplier"]
        base_stats["attack"] *= quality_multiplier
        base_stats["defense"] *= quality_multiplier
        base_stats["health"] *= quality_multiplier
        
        if hero["advancement"] > 0:
            adv_index = min(hero["advancement"] - 1, len(ADVANCEMENT_LEVELS) - 1)
            adv_bonus = ADVANCEMENT_LEVELS[adv_index]["bonus"]
            base_stats["attack"] *= (1 + adv_bonus["attack"])
            base_stats["defense"] *= (1 + adv_bonus["defense"])
            base_stats["health"] *= (1 + adv_bonus["health"])
        
        if hero["awakening"] > 0:
            awak_index = min(hero["awakening"], len(AWAKENING_STAGES) - 1)
            awak_bonus = AWAKENING_STAGES[awak_index]["bonus"]
            base_stats["attack"] *= (1 + awak_bonus.get("attack", 0))
            base_stats["defense"] *= (1 + awak_bonus.get("defense", 0))
            base_stats["health"] *= (1 + awak_bonus.get("health", 0))
        
        star_multiplier = 1.0 + (hero["star"] - 1) * 0.2
        base_stats["attack"] *= star_multiplier
        base_stats["defense"] *= star_multiplier
        base_stats["health"] *= star_multiplier
        
        return {
            "attack": int(base_stats["attack"]),
            "defense": int(base_stats["defense"]),
            "health": int(base_stats["health"]),
            "power": int(base_stats["attack"] + base_stats["defense"] + base_stats["health"])
        }
    
    def can_advance(self, hero_name):
        hero = self.get_hero(hero_name)
        if not hero:
            return False, "武将不存在"
        
        current_adv = hero["advancement"]
        if current_adv >= len(ADVANCEMENT_LEVELS):
            return False, "已达到最高进阶等级"
        
        cost = ADVANCEMENT_LEVELS[current_adv]["cost"]
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        return True, "可以进阶"
    
    def advance_hero(self, hero_name):
        can_do, msg = self.can_advance(hero_name)
        if not can_do:
            return False, msg
        
        hero = self.get_hero(hero_name)
        current_adv = hero["advancement"]
        cost = ADVANCEMENT_LEVELS[current_adv]["cost"]
        
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        hero["advancement"] += 1
        hero["level"] += 5
        
        save()
        return True, f"进阶成功！当前进阶等级：{ADVANCEMENT_LEVELS[hero['advancement']-1]['name']}"
    
    def can_awaken(self, hero_name):
        hero = self.get_hero(hero_name)
        if not hero:
            return False, "武将不存在"
        
        current_awak = hero["awakening"]
        if current_awak >= len(AWAKENING_STAGES) - 1:
            return False, "已达到最高觉醒阶段"
        
        cost = AWAKENING_STAGES[current_awak + 1]["cost"]
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        return True, "可以觉醒"
    
    def awaken_hero(self, hero_name):
        can_do, msg = self.can_awaken(hero_name)
        if not can_do:
            return False, msg
        
        hero = self.get_hero(hero_name)
        current_awak = hero["awakening"]
        cost = AWAKENING_STAGES[current_awak + 1]["cost"]
        
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        hero["awakening"] += 1
        
        save()
        return True, f"觉醒成功！当前觉醒阶段：{AWAKENING_STAGES[hero['awakening']]['name']}"
    
    def can_star_up(self, hero_name):
        hero = self.get_hero(hero_name)
        if not hero:
            return False, "武将不存在"
        
        current_star = hero["star"]
        if current_star >= 10:
            return False, "已达到最高星级"
        
        cost_index = min(current_star, len(STAR_COSTS) - 1)
        cost = STAR_COSTS[cost_index]["cost"]
        
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        return True, "可以升星"
    
    def star_up_hero(self, hero_name):
        can_do, msg = self.can_star_up(hero_name)
        if not can_do:
            return False, msg
        
        hero = self.get_hero(hero_name)
        current_star = hero["star"]
        cost_index = min(current_star, len(STAR_COSTS) - 1)
        cost = STAR_COSTS[cost_index]["cost"]
        
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        hero["star"] += 1
        
        save()
        return True, f"升星成功！当前星级：{hero['star']}星"
    
    def get_bonds(self, hero_name):
        active_bonds = []
        all_hero_names = list(data["hero_management"]["heroes"].keys())
        
        for bond_id, bond_data in HERO_BONDS.items():
            bond_heroes = bond_data["heroes"]
            common_heroes = set(all_hero_names) & set(bond_heroes)
            
            if hero_name in bond_heroes:
                is_active = len(common_heroes) >= len(bond_heroes)
                progress = len(common_heroes) / len(bond_heroes)
                
                active_bonds.append({
                    "id": bond_id,
                    "name": bond_data["name"],
                    "description": bond_data.get("description", bond_data.get("effect", {}).get("description", "")),
                    "heroes": bond_heroes,
                    "effect": bond_data["effect"],
                    "active": is_active,
                    "progress": progress,
                    "owned": list(common_heroes),
                    "missing": list(set(bond_heroes) - common_heroes)
                })
        
        return active_bonds

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

def draw_hero_card(surface, hero_name, stats, x, y, width, height, font_main, font_small, hero_management):
    hero = hero_management.get_hero(hero_name)
    if not hero:
        return
    
    bg_color = QUALITY_INFO[hero["quality"]]["color"]
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (*bg_color[:3], 150), (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, bg_color, (x, y, width, height), 2, border_radius=12)
    
    icon = get_hero_icon(hero_name)
    icon_font = pygame.font.Font(None, 50)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + width // 2, y + 40))
    surface.blit(icon_surf, icon_rect)
    
    name_surf = font_main.render(hero_name, True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + width // 2, y + 95))
    surface.blit(name_surf, name_rect)
    
    quality_text = QUALITY_INFO[hero["quality"]]["name"]
    quality_surf = font_small.render(quality_text, True, QUALITY_INFO[hero["quality"]]["color"])
    surface.blit(quality_surf, (x + 10, y + 120))
    
    star_text = "⭐" * hero["star"]
    star_surf = font_small.render(star_text, True, COLORS["accent_gold"])
    surface.blit(star_surf, (x + width - 10 - star_surf.get_width(), y + 120))
    
    adv_name = ADVANCEMENT_LEVELS[hero["advancement"] - 1]["name"]
    adv_text = f"进阶: {adv_name}"
    adv_surf = font_small.render(adv_text, True, COLORS["accent_blue"])
    surface.blit(adv_surf, (x + 10, y + 145))
    
    awak_name = AWAKENING_STAGES[hero["awakening"]]["name"]
    awak_text = f"觉醒: {awak_name}"
    awak_surf = font_small.render(awak_text, True, COLORS["accent_purple"])
    surface.blit(awak_surf, (x + width - 10 - awak_surf.get_width(), y + 145))
    
    if stats:
        power_text = font_main.render(f"战力: {stats['power']}", True, COLORS["accent_gold"])
        power_rect = power_text.get_rect(center=(x + width // 2, y + 180))
        surface.blit(power_text, power_rect)
        
        stat_y = y + 210
        stat_items = [("⚔️", "攻击", stats["attack"]), ("🛡️", "防御", stats["defense"]), ("❤️", "生命", stats["health"])]
        for icon, name, value in stat_items:
            stat_text = f"{icon} {name}: {value}"
            stat_surf = font_small.render(stat_text, True, COLORS["text_white"])
            surface.blit(stat_surf, (x + 15, stat_y))
            stat_y += 22

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
        pygame.display.set_caption("武将管理")
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
        
        hero_management = HeroManagementSystem()
        
        particles = []
        
        current_tab = "hero_list"
        tabs = ["hero_list", "advance", "awaken", "star", "bonds"]
        tab_names = ["武将列表", "进阶", "觉醒", "升星", "羁绊"]
        
        selected_hero = None
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
            
            draw_title(screen, "武将管理", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            tab_y = SCREEN_HEIGHT * 0.18
            tab_width = 120
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
            
            heroes = hero_management.get_all_heroes()
            
            if current_tab == "hero_list":
                if heroes:
                    card_width = min(200, SCREEN_WIDTH * 0.22)
                    card_height = min(260, SCREEN_HEIGHT * 0.35)
                    cols = min(4, SCREEN_WIDTH // (card_width + 20))
                    start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 20)) // 2
                    
                    hero_buttons = []
                    for i, (hero_name, hero_data) in enumerate(heroes.items()):
                        row = i // cols
                        col = i % cols
                        x = start_x + col * (card_width + 20)
                        y = content_y + row * (card_height + 20)
                        
                        stats = hero_management.calculate_stats(hero_name)
                        draw_hero_card(screen, hero_name, stats, x, y, card_width, card_height, font_main, font_small, hero_management)
                        
                        card_rect = pygame.Rect(x, y, card_width, card_height)
                        hero_buttons.append((card_rect, hero_name))
                else:
                    empty_text = font_main.render("暂无武将，请先招募", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "advance":
                if heroes:
                    hero_names = list(heroes.keys())
                    btn_width = min(180, SCREEN_WIDTH * 0.2)
                    btn_height = 50
                    start_x = (SCREEN_WIDTH - btn_width) // 2
                    
                    hero_buttons = []
                    for i, hero_name in enumerate(hero_names):
                        y = content_y + i * (btn_height + 10)
                        if y > SCREEN_HEIGHT - 100:
                            break
                        
                        hero = heroes[hero_name]
                        adv_level = hero["advancement"]
                        adv_name = ADVANCEMENT_LEVELS[adv_level - 1]["name"]
                        
                        can_do, msg = hero_management.can_advance(hero_name)
                        if can_do:
                            next_adv = ADVANCEMENT_LEVELS[adv_level]
                            btn_text = f"{hero_name} - {adv_name} → {next_adv['name']}"
                            btn_color = COLORS["btn_green"]
                            hover_color = COLORS["btn_green_hover"]
                        else:
                            btn_text = f"{hero_name} - {adv_name} ({msg})"
                            btn_color = (100, 100, 120)
                            hover_color = (120, 120, 150)
                        
                        btn = Button(btn_text, start_x, y, btn_width, btn_height, font_small, btn_color, hover_color)
                        btn.update((mx, my))
                        btn.draw(screen)
                        hero_buttons.append((btn, hero_name, "advance"))
                
                else:
                    empty_text = font_main.render("暂无武将，请先招募", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "awaken":
                if heroes:
                    hero_names = list(heroes.keys())
                    btn_width = min(180, SCREEN_WIDTH * 0.2)
                    btn_height = 50
                    start_x = (SCREEN_WIDTH - btn_width) // 2
                    
                    hero_buttons = []
                    for i, hero_name in enumerate(hero_names):
                        y = content_y + i * (btn_height + 10)
                        if y > SCREEN_HEIGHT - 100:
                            break
                        
                        hero = heroes[hero_name]
                        awak_stage = hero["awakening"]
                        awak_name = AWAKENING_STAGES[awak_stage]["name"]
                        
                        can_do, msg = hero_management.can_awaken(hero_name)
                        if can_do:
                            next_awak = AWAKENING_STAGES[awak_stage + 1]
                            btn_text = f"{hero_name} - {awak_name} → {next_awak['name']}"
                            btn_color = COLORS["btn_purple"]
                            hover_color = COLORS["btn_purple_hover"]
                        else:
                            btn_text = f"{hero_name} - {awak_name} ({msg})"
                            btn_color = (100, 100, 120)
                            hover_color = (120, 120, 150)
                        
                        btn = Button(btn_text, start_x, y, btn_width, btn_height, font_small, btn_color, hover_color)
                        btn.update((mx, my))
                        btn.draw(screen)
                        hero_buttons.append((btn, hero_name, "awaken"))
                
                else:
                    empty_text = font_main.render("暂无武将，请先招募", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "star":
                if heroes:
                    hero_names = list(heroes.keys())
                    btn_width = min(180, SCREEN_WIDTH * 0.2)
                    btn_height = 50
                    start_x = (SCREEN_WIDTH - btn_width) // 2
                    
                    hero_buttons = []
                    for i, hero_name in enumerate(hero_names):
                        y = content_y + i * (btn_height + 10)
                        if y > SCREEN_HEIGHT - 100:
                            break
                        
                        hero = heroes[hero_name]
                        star = hero["star"]
                        
                        can_do, msg = hero_management.can_star_up(hero_name)
                        if can_do:
                            btn_text = f"{hero_name} - {star}⭐ → {star+1}⭐"
                            btn_color = COLORS["btn_gold"]
                            hover_color = COLORS["btn_gold_hover"]
                        else:
                            btn_text = f"{hero_name} - {star}⭐ ({msg})"
                            btn_color = (100, 100, 120)
                            hover_color = (120, 120, 150)
                        
                        btn = Button(btn_text, start_x, y, btn_width, btn_height, font_small, btn_color, hover_color)
                        btn.update((mx, my))
                        btn.draw(screen)
                        hero_buttons.append((btn, hero_name, "star"))
                
                else:
                    empty_text = font_main.render("暂无武将，请先招募", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "bonds":
                if heroes:
                    hero_names = list(heroes.keys())
                    
                    for i, hero_name in enumerate(hero_names):
                        bonds = hero_management.get_bonds(hero_name)
                        if bonds:
                            hero_surf = font_main.render(f"⚔️ {hero_name}", True, COLORS["accent_gold"])
                            screen.blit(hero_surf, (50, content_y + i * 200))
                            
                            bond_y = content_y + i * 200 + 35
                            for bond in bonds:
                                bg_color = (40, 70, 40, 200) if bond["active"] else (40, 40, 70, 200)
                                bond_rect = pygame.Rect(50, bond_y, SCREEN_WIDTH - 100, 80)
                                pygame.draw.rect(screen, bg_color, bond_rect, border_radius=10)
                                pygame.draw.rect(screen, COLORS["accent_gold"], bond_rect, 2, border_radius=10)
                                
                                name_surf = font_small.render(f"✨ {bond['name']}", True, COLORS["accent_gold"])
                                screen.blit(name_surf, (65, bond_y + 10))
                                
                                desc_surf = font_small.render(bond["description"], True, COLORS["text_white"])
                                screen.blit(desc_surf, (65, bond_y + 35))
                                
                                effect_text = f"效果: {bond['effect']['type']}+{bond['effect']['value']*100}%"
                                effect_surf = font_small.render(effect_text, True, COLORS["accent_green"])
                                screen.blit(effect_surf, (SCREEN_WIDTH - 250, bond_y + 10))
                                
                                progress_text = f"进度: {int(bond['progress']*100)}%"
                                progress_surf = font_small.render(progress_text, True, COLORS["accent_blue"])
                                screen.blit(progress_surf, (SCREEN_WIDTH - 250, bond_y + 40))
                                
                                if not bond["active"] and bond["missing"]:
                                    missing_text = f"缺少: {', '.join(bond['missing'])}"
                                    missing_surf = font_small.render(missing_text, True, COLORS["accent_red"])
                                    screen.blit(missing_surf, (65, bond_y + 60))
                                
                                bond_y += 90
                else:
                    empty_text = font_main.render("暂无武将，请先招募", True, COLORS["text_gray"])
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
                    
                    if current_tab == "advance" and 'hero_buttons' in locals():
                        for btn, hero_name, action in hero_buttons:
                            if btn.rect.collidepoint(mx, my):
                                success, msg = hero_management.advance_hero(hero_name)
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                    
                    elif current_tab == "awaken" and 'hero_buttons' in locals():
                        for btn, hero_name, action in hero_buttons:
                            if btn.rect.collidepoint(mx, my):
                                success, msg = hero_management.awaken_hero(hero_name)
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                    
                    elif current_tab == "star" and 'hero_buttons' in locals():
                        for btn, hero_name, action in hero_buttons:
                            if btn.rect.collidepoint(mx, my):
                                success, msg = hero_management.star_up_hero(hero_name)
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("武将管理")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("武将管理", str(e))

if __name__ == "__main__":
    main()