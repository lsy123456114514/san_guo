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
    "btn_gold_hover": (255, 200, 80)
}

FORMATIONS = {
    "heng": {
        "name": "一字长蛇阵",
        "description": "横向排列，攻击力强，适合进攻",
        "icon": "🐍",
        "bonus": {"attack": 0.15, "speed": 5},
        "positions": [(100, 350), (250, 350), (400, 350), (550, 350), (700, 350)],
        "color": (255, 100, 100),
        "type": "offense"
    },
    "dui": {
        "name": "雁行阵",
        "description": "斜向排列，机动灵活，适合伏击",
        "icon": "🦢",
        "bonus": {"speed": 15, "critical": 0.08},
        "positions": [(150, 250), (300, 320), (450, 390), (600, 320), (750, 250)],
        "color": (100, 150, 255),
        "type": "speed"
    },
    "yuan": {
        "name": "混元阵",
        "description": "圆形排列，攻守兼备，适合持久",
        "icon": "🌀",
        "bonus": {"defense": 0.12, "health": 0.1},
        "positions": [(450, 150), (700, 280), (650, 500), (250, 500), (200, 280)],
        "color": (150, 100, 50),
        "type": "defense"
    },
    "ba": {
        "name": "八卦阵",
        "description": "诸葛亮发明，迷惑敌人，防御极强",
        "icon": "☯️",
        "bonus": {"defense": 0.2, "damage_reduction": 0.1},
        "positions": [(300, 200), (550, 200), (700, 380), (550, 560), (300, 560), (150, 380)],
        "color": (128, 0, 128),
        "type": "defense"
    },
    "long": {
        "name": "龙腾阵",
        "description": "龙形排列，气势磅礴，全体加成",
        "icon": "🐉",
        "bonus": {"attack": 0.1, "defense": 0.1, "speed": 5},
        "positions": [(450, 100), (650, 250), (750, 450), (600, 600), (300, 600), (150, 450), (250, 250)],
        "color": (255, 215, 0),
        "type": "balanced"
    },
    "feng": {
        "name": "锋矢阵",
        "description": "箭矢形状，前锋突击，伤害集中",
        "icon": "🏹",
        "bonus": {"attack": 0.25, "critical": 0.1},
        "positions": [(450, 150), (300, 300), (600, 300), (200, 450), (700, 450)],
        "color": (255, 140, 50),
        "type": "offense"
    },
    "lian": {
        "name": "连环阵",
        "description": "环环相扣，互相支援，续航强",
        "icon": "🔗",
        "bonus": {"heal_on_hit": 0.08, "rage_gain": 0.15},
        "positions": [(450, 200), (250, 280), (650, 280), (250, 480), (650, 480), (450, 560)],
        "color": (100, 200, 100),
        "type": "support"
    },
    "tian": {
        "name": "天罡阵",
        "description": "北斗七星排列，神秘力量，全属性提升",
        "icon": "⭐",
        "bonus": {"attack": 0.12, "defense": 0.08, "speed": 8, "critical": 0.05},
        "positions": [(450, 80), (650, 180), (750, 350), (650, 520), (450, 620), (250, 520), (150, 350), (250, 180)],
        "color": (200, 100, 255),
        "type": "balanced"
    }
}

FORMATION_TYPES = {
    "offense": {"name": "攻击型", "color": (255, 100, 100)},
    "defense": {"name": "防御型", "color": (100, 150, 255)},
    "speed": {"name": "速度型", "color": (100, 200, 100)},
    "support": {"name": "辅助型", "color": (150, 150, 100)},
    "balanced": {"name": "平衡型", "color": (255, 215, 0)}
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

class FormationSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "formation" not in data:
            data["formation"] = {
                "current_formation": "heng",
                "unlocked_formations": ["heng"],
                "formation_level": {"heng": 1},
                "hero_positions": {}
            }
        save()
    
    def get_current_formation(self):
        return data["formation"]["current_formation"]
    
    def get_unlocked_formations(self):
        return data["formation"]["unlocked_formations"]
    
    def get_formation_level(self, formation_id):
        return data["formation"]["formation_level"].get(formation_id, 1)
    
    def unlock_formation(self, formation_id):
        cost = self.get_unlock_cost(formation_id)
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        if formation_id not in data["formation"]["unlocked_formations"]:
            data["formation"]["unlocked_formations"].append(formation_id)
        
        if formation_id not in data["formation"]["formation_level"]:
            data["formation"]["formation_level"][formation_id] = 1
        
        save()
        return True, f"解锁成功！{FORMATIONS[formation_id]['name']}"
    
    def get_unlock_cost(self, formation_id):
        base_cost = {"金元宝": 500, "将魂": 200}
        index = list(FORMATIONS.keys()).index(formation_id)
        multiplier = 1 + (index * 0.5)
        return {
            "金元宝": int(base_cost["金元宝"] * multiplier),
            "将魂": int(base_cost["将魂"] * multiplier)
        }
    
    def upgrade_formation(self, formation_id):
        if formation_id not in data["formation"]["unlocked_formations"]:
            return False, "阵法未解锁"
        
        level = self.get_formation_level(formation_id)
        if level >= 10:
            return False, "阵法已达到最高等级"
        
        cost = {"金元宝": 100 * level, "将魂": 50 * level}
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        data["formation"]["formation_level"][formation_id] += 1
        save()
        
        return True, f"升级成功！{FORMATIONS[formation_id]['name']} Lv.{level + 1}"
    
    def set_current_formation(self, formation_id):
        if formation_id not in data["formation"]["unlocked_formations"]:
            return False, "阵法未解锁"
        
        data["formation"]["current_formation"] = formation_id
        save()
        return True, f"已切换至{FORMATIONS[formation_id]['name']}"
    
    def set_hero_position(self, formation_id, position_index, hero_name):
        formation = FORMATIONS[formation_id]
        if position_index >= len(formation["positions"]):
            return False, "位置无效"
        
        current_positions = data["formation"]["hero_positions"].get(formation_id, {})
        
        for idx, name in list(current_positions.items()):
            if name == hero_name:
                del current_positions[idx]
        
        current_positions[str(position_index)] = hero_name
        data["formation"]["hero_positions"][formation_id] = current_positions
        save()
        
        return True, f"{hero_name}已放置在位置{position_index + 1}"
    
    def get_formation_bonus(self, formation_id):
        formation = FORMATIONS[formation_id]
        level = self.get_formation_level(formation_id)
        level_multiplier = 1 + (level - 1) * 0.1
        
        bonus = {}
        for stat, value in formation["bonus"].items():
            bonus[stat] = value * level_multiplier
        
        return bonus
    
    def get_total_bonus(self):
        current = self.get_current_formation()
        return self.get_formation_bonus(current)

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

def draw_formation_grid(surface, formation_id, scale, font_small):
    formation = FORMATIONS[formation_id]
    positions = formation["positions"]
    color = formation["color"]
    
    grid_x = 100 * scale
    grid_y = 150 * scale
    grid_width = 600 * scale
    grid_height = 400 * scale
    
    bg_surf = pygame.Surface((grid_width, grid_height), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (*COLORS["panel_bg"][:3], 100), (0, 0, grid_width, grid_height), border_radius=12)
    surface.blit(bg_surf, (grid_x, grid_y))
    pygame.draw.rect(surface, color, (grid_x, grid_y, grid_width, grid_height), 2, border_radius=12)
    
    hero_positions = data["formation"]["hero_positions"].get(formation_id, {})
    heroes = data["hero_management"].get("heroes", {}) if "hero_management" in data else {}
    
    for i, (px, py) in enumerate(positions):
        scaled_x = grid_x + (px - 100) * (grid_width / 600)
        scaled_y = grid_y + (py - 100) * (grid_height / 500)
        
        radius = 45 * scale
        
        pygame.draw.circle(surface, color, (int(scaled_x), int(scaled_y)), int(radius), 3)
        
        alpha = 30
        pygame.draw.circle(surface, (*color[:3], alpha), (int(scaled_x), int(scaled_y)), int(radius - 3))
        
        hero_name = hero_positions.get(str(i))
        if hero_name and hero_name in heroes:
            hero_data = heroes[hero_name]
            hp_percent = hero_data.get("current_health", 100) / hero_data.get("max_health", 100)
            
            hp_bar_width = 60 * scale
            hp_bar_height = 6 * scale
            hp_bar_x = scaled_x - hp_bar_width / 2
            hp_bar_y = scaled_y - radius - 15 * scale
            
            pygame.draw.rect(surface, COLORS["accent_red"], (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), border_radius=3)
            pygame.draw.rect(surface, COLORS["accent_green"], (hp_bar_x, hp_bar_y, hp_bar_width * hp_percent, hp_bar_height), border_radius=3)
            
            name_surf = font_small.render(hero_name, True, COLORS["text_white"])
            name_rect = name_surf.get_rect(center=(scaled_x, scaled_y))
            surface.blit(name_surf, name_rect)
            
            icon_font = pygame.font.Font(None, int(30 * scale))
            icon_surf = icon_font.render("⚔️", True, COLORS["accent_gold"])
            surface.blit(icon_surf, (scaled_x - icon_surf.get_width() // 2, scaled_y - radius + 10 * scale))
        else:
            empty_surf = font_small.render(f"空位{i+1}", True, COLORS["text_gray"])
            empty_rect = empty_surf.get_rect(center=(scaled_x, scaled_y))
            surface.blit(empty_surf, empty_rect)

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
        pygame.display.set_caption("阵法系统")
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
        
        formation_system = FormationSystem()
        
        particles = []
        
        current_tab = "select"
        tabs = ["select", "unlock", "upgrade"]
        tab_names = ["选择阵法", "解锁阵法", "升级阵法"]
        
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
            
            draw_title(screen, "阵法系统", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
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
            
            unlocked = formation_system.get_unlocked_formations()
            current_formation = formation_system.get_current_formation()
            
            if current_tab == "select":
                for i, (form_id, form_data) in enumerate(FORMATIONS.items()):
                    is_unlocked = form_id in unlocked
                    is_current = form_id == current_formation
                    
                    card_width = min(200, SCREEN_WIDTH * 0.22)
                    card_height = min(180, SCREEN_HEIGHT * 0.25)
                    cols = min(4, SCREEN_WIDTH // (card_width + 20))
                    x = 50 + (i % cols) * (card_width + 20)
                    y = content_y + (i // cols) * (card_height + 20)
                    
                    bg_color = form_data["color"] if is_unlocked else COLORS["text_gray"]
                    alpha = 200 if is_unlocked else 100
                    
                    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, (*bg_color[:3], alpha), (0, 0, card_width, card_height), border_radius=12)
                    screen.blit(card_surf, (x, y))
                    pygame.draw.rect(screen, bg_color, (x, y, card_width, card_height), 2, border_radius=12)
                    
                    if is_current:
                        pygame.draw.rect(screen, COLORS["accent_gold"], (x, y, card_width, card_height), 4, border_radius=12)
                        current_text = font_small.render("当前阵法", True, COLORS["accent_gold"])
                        screen.blit(current_text, (x + 10, y + 10))
                    
                    icon_font = pygame.font.Font(None, int(45 * scale))
                    icon_surf = icon_font.render(form_data["icon"], True, COLORS["text_white"])
                    icon_rect = icon_surf.get_rect(center=(x + card_width // 2, y + 40))
                    screen.blit(icon_surf, icon_rect)
                    
                    name_surf = font_main.render(form_data["name"], True, COLORS["text_white"])
                    name_rect = name_surf.get_rect(center=(x + card_width // 2, y + 85))
                    screen.blit(name_surf, name_rect)
                    
                    type_info = FORMATION_TYPES[form_data["type"]]
                    type_surf = font_small.render(type_info["name"], True, type_info["color"])
                    screen.blit(type_surf, (x + 10, y + 110))
                    
                    if is_unlocked:
                        level = formation_system.get_formation_level(form_id)
                        level_surf = font_small.render(f"Lv.{level}", True, COLORS["accent_green"])
                        screen.blit(level_surf, (x + card_width - 10 - level_surf.get_width(), y + 110))
                        
                        if not is_current:
                            select_btn = Button("选择", x + (card_width - 80) // 2, y + 140, 80, 30, font_small, COLORS["btn_green"], COLORS["btn_green_hover"])
                            select_btn.update((mx, my))
                            select_btn.draw(screen)
                            tab_buttons.append((select_btn, f"select_{form_id}"))
                    else:
                        locked_surf = font_small.render("🔒 未解锁", True, COLORS["text_gray"])
                        screen.blit(locked_surf, (x + card_width // 2 - locked_surf.get_width() // 2, y + 140))
                
                draw_formation_grid(screen, current_formation, scale, font_small)
                
                bonus = formation_system.get_total_bonus()
                bonus_text = ""
                if bonus.get("attack", 0) > 0:
                    bonus_text += f"⚔️+{int(bonus['attack']*100)}% "
                if bonus.get("defense", 0) > 0:
                    bonus_text += f"🛡️+{int(bonus['defense']*100)}% "
                if bonus.get("speed", 0) > 0:
                    bonus_text += f"⚡+{int(bonus['speed'])} "
                if bonus.get("critical", 0) > 0:
                    bonus_text += f"💥+{int(bonus['critical']*100)}% "
                if bonus.get("health", 0) > 0:
                    bonus_text += f"❤️+{int(bonus['health']*100)}% "
                if bonus.get("damage_reduction", 0) > 0:
                    bonus_text += f"🔰+{int(bonus['damage_reduction']*100)}% "
                
                if bonus_text:
                    bonus_surf = font_main.render(f"当前阵法加成: {bonus_text}", True, COLORS["accent_gold"])
                    screen.blit(bonus_surf, (SCREEN_WIDTH // 2 - bonus_surf.get_width() // 2, SCREEN_HEIGHT * 0.88))
            
            elif current_tab == "unlock":
                for i, (form_id, form_data) in enumerate(FORMATIONS.items()):
                    is_unlocked = form_id in unlocked
                    
                    card_width = min(280, SCREEN_WIDTH * 0.3)
                    card_height = 80
                    x = (SCREEN_WIDTH - card_width) // 2
                    y = content_y + i * (card_height + 20)
                    
                    bg_color = form_data["color"] if is_unlocked else COLORS["text_gray"]
                    alpha = 200 if is_unlocked else 100
                    
                    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, (*bg_color[:3], alpha), (0, 0, card_width, card_height), border_radius=10)
                    screen.blit(card_surf, (x, y))
                    pygame.draw.rect(screen, bg_color, (x, y, card_width, card_height), 2, border_radius=10)
                    
                    icon_font = pygame.font.Font(None, int(35 * scale))
                    icon_surf = icon_font.render(form_data["icon"], True, COLORS["text_white"])
                    screen.blit(icon_surf, (x + 20, y + card_height // 2 - icon_surf.get_height() // 2))
                    
                    name_surf = font_main.render(form_data["name"], True, COLORS["text_white"])
                    screen.blit(name_surf, (x + 70, y + 15))
                    
                    desc_surf = font_small.render(form_data["description"], True, COLORS["text_gray"])
                    screen.blit(desc_surf, (x + 70, y + 45))
                    
                    if is_unlocked:
                        unlocked_surf = font_small.render("✓ 已解锁", True, COLORS["accent_green"])
                        screen.blit(unlocked_surf, (x + card_width - 100, y + card_height // 2 - unlocked_surf.get_height() // 2))
                    else:
                        cost = formation_system.get_unlock_cost(form_id)
                        cost_text = f"{cost['金元宝']}金元宝 {cost['将魂']}将魂"
                        cost_surf = font_small.render(cost_text, True, COLORS["accent_orange"])
                        screen.blit(cost_surf, (x + card_width - 200, y + 20))
                        
                        unlock_btn = Button("解锁", x + card_width - 80, y + 25, 70, 30, font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"])
                        unlock_btn.update((mx, my))
                        unlock_btn.draw(screen)
                        tab_buttons.append((unlock_btn, f"unlock_{form_id}"))
            
            elif current_tab == "upgrade":
                for i, (form_id, form_data) in enumerate(FORMATIONS.items()):
                    is_unlocked = form_id in unlocked
                    if not is_unlocked:
                        continue
                    
                    level = formation_system.get_formation_level(form_id)
                    is_max = level >= 10
                    
                    card_width = min(280, SCREEN_WIDTH * 0.3)
                    card_height = 100
                    x = (SCREEN_WIDTH - card_width) // 2
                    y = content_y + i * (card_height + 20)
                    
                    bg_color = form_data["color"]
                    alpha = 200
                    
                    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, (*bg_color[:3], alpha), (0, 0, card_width, card_height), border_radius=10)
                    screen.blit(card_surf, (x, y))
                    pygame.draw.rect(screen, bg_color, (x, y, card_width, card_height), 2, border_radius=10)
                    
                    icon_font = pygame.font.Font(None, int(35 * scale))
                    icon_surf = icon_font.render(form_data["icon"], True, COLORS["text_white"])
                    screen.blit(icon_surf, (x + 20, y + card_height // 2 - icon_surf.get_height() // 2))
                    
                    name_surf = font_main.render(form_data["name"], True, COLORS["text_white"])
                    screen.blit(name_surf, (x + 70, y + 10))
                    
                    level_text = f"等级: {level}/10"
                    level_surf = font_small.render(level_text, True, COLORS["accent_gold"])
                    screen.blit(level_surf, (x + 70, y + 40))
                    
                    bonus = formation_system.get_formation_bonus(form_id)
                    bonus_text = ""
                    for stat, value in bonus.items():
                        if stat == "attack":
                            bonus_text += f"⚔️+{int(value*100)}% "
                        elif stat == "defense":
                            bonus_text += f"🛡️+{int(value*100)}% "
                        elif stat == "speed":
                            bonus_text += f"⚡+{int(value)} "
                        elif stat == "critical":
                            bonus_text += f"💥+{int(value*100)}% "
                        elif stat == "health":
                            bonus_text += f"❤️+{int(value*100)}% "
                        elif stat == "damage_reduction":
                            bonus_text += f"🔰+{int(value*100)}% "
                    
                    if bonus_text:
                        bonus_surf = font_small.render(f"加成: {bonus_text}", True, COLORS["text_white"])
                        screen.blit(bonus_surf, (x + 70, y + 70))
                    
                    if not is_max:
                        cost = {"金元宝": 100 * level, "将魂": 50 * level}
                        cost_text = f"{cost['金元宝']}金元宝 {cost['将魂']}将魂"
                        cost_surf = font_small.render(cost_text, True, COLORS["accent_orange"])
                        screen.blit(cost_surf, (x + card_width - 200, y + 20))
                        
                        upgrade_btn = Button("升级", x + card_width - 80, y + 45, 70, 30, font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"])
                        upgrade_btn.update((mx, my))
                        upgrade_btn.draw(screen)
                        tab_buttons.append((upgrade_btn, f"upgrade_{form_id}"))
                    else:
                        max_text = font_small.render("已满级", True, COLORS["accent_green"])
                        screen.blit(max_text, (x + card_width - 80, y + 50))
            
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
                    for btn, action in tab_buttons:
                        if btn.rect.collidepoint(mx, my):
                            if action in tabs:
                                current_tab = action
                            elif action.startswith("select_"):
                                form_id = action.replace("select_", "")
                                success, msg = formation_system.set_current_formation(form_id)
                                message = msg
                                show_message = True
                                message_timer = 0
                            elif action.startswith("unlock_"):
                                form_id = action.replace("unlock_", "")
                                success, msg = formation_system.unlock_formation(form_id)
                                message = msg
                                show_message = True
                                message_timer = 0
                            elif action.startswith("upgrade_"):
                                form_id = action.replace("upgrade_", "")
                                success, msg = formation_system.upgrade_formation(form_id)
                                message = msg
                                show_message = True
                                message_timer = 0
                            break
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("阵法系统")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("阵法系统", str(e))

if __name__ == "__main__":
    main()