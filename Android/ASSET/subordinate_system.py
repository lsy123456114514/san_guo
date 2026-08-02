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

SUBORDINATE_RARITY = {
    "common": {"name": "普通", "color": (150, 150, 150), "multiplier": 1.0, "probability": 50},
    "rare": {"name": "稀有", "color": (70, 130, 180), "multiplier": 1.3, "probability": 35},
    "epic": {"name": "史诗", "color": (128, 0, 128), "multiplier": 1.6, "probability": 12},
    "legendary": {"name": "传说", "color": (255, 215, 0), "multiplier": 2.0, "probability": 3}
}

SUBORDINATE_SKILLS = {
    "attack_boost": {"name": "攻击支援", "description": "为主将提供攻击力加成", "effect": {"attack": 0.1}, "icon": "⚔️"},
    "defense_boost": {"name": "防御支援", "description": "为主将提供防御力加成", "effect": {"defense": 0.1}, "icon": "🛡️"},
    "health_boost": {"name": "生命支援", "description": "为主将提供生命值加成", "effect": {"health": 0.15}, "icon": "❤️"},
    "critical_boost": {"name": "暴击支援", "description": "为主将提供暴击率加成", "effect": {"critical": 0.05}, "icon": "💥"},
    "speed_boost": {"name": "速度支援", "description": "为主将提供速度加成", "effect": {"speed": 10}, "icon": "⚡"},
    "heal_on_hit": {"name": "治疗支援", "description": "主将攻击时恢复生命", "effect": {"heal_on_hit": 0.05}, "icon": "💚"},
    "damage_reduction": {"name": "减伤支援", "description": "为主将提供伤害减免", "effect": {"damage_reduction": 0.05}, "icon": "🔰"},
    "skill_enhance": {"name": "技能支援", "description": "增强主将技能效果", "effect": {"skill_damage": 0.1}, "icon": "✨"},
    "rage_boost": {"name": "怒气支援", "description": "加速主将怒气积累", "effect": {"rage_gain": 0.2}, "icon": "🔥"},
    "element_boost": {"name": "元素支援", "description": "增强主将元素效果", "effect": {"element_damage": 0.15}, "icon": "💎"}
}

SUBORDINATE_POOL = [
    {"name": "周仓", "rarity": "common", "skill": "defense_boost", "element": "土", "description": "关羽部将，忠心耿耿"},
    {"name": "关平", "rarity": "rare", "skill": "attack_boost", "element": "火", "description": "关羽之子，勇猛善战"},
    {"name": "马岱", "rarity": "common", "skill": "speed_boost", "element": "风", "description": "马超堂弟，擅长骑术"},
    {"name": "廖化", "rarity": "common", "skill": "health_boost", "element": "水", "description": "蜀汉老将，经验丰富"},
    {"name": "张苞", "rarity": "rare", "skill": "critical_boost", "element": "火", "description": "张飞之子，继承父业"},
    {"name": "关兴", "rarity": "rare", "skill": "attack_boost", "element": "火", "description": "关羽之子，英勇无敌"},
    {"name": "赵统", "rarity": "common", "skill": "heal_on_hit", "element": "风", "description": "赵云长子，传承家风"},
    {"name": "赵广", "rarity": "common", "skill": "speed_boost", "element": "风", "description": "赵云次子，身手敏捷"},
    {"name": "张绍", "rarity": "common", "skill": "health_boost", "element": "土", "description": "张飞之子，文武双全"},
    {"name": "马休", "rarity": "common", "skill": "attack_boost", "element": "风", "description": "马超之子，勇力过人"},
    {"name": "马铁", "rarity": "common", "skill": "defense_boost", "element": "风", "description": "马超之子，沉稳可靠"},
    {"name": "黄叙", "rarity": "epic", "skill": "element_boost", "element": "土", "description": "黄忠之子，箭术精湛"},
    {"name": "诸葛瞻", "rarity": "epic", "skill": "skill_enhance", "element": "水", "description": "诸葛亮之子，忠孝两全"},
    {"name": "诸葛尚", "rarity": "legendary", "skill": "critical_boost", "element": "风", "description": "诸葛亮之孙，勇猛无双"},
    {"name": "姜维副将", "rarity": "epic", "skill": "element_boost", "element": "风", "description": "姜维的得力副将"},
    {"name": "魏延副将", "rarity": "rare", "skill": "damage_reduction", "element": "火", "description": "魏延的先锋副将"},
    {"name": "庞统副将", "rarity": "epic", "skill": "skill_enhance", "element": "水", "description": "庞统的参谋"},
    {"name": "法正副将", "rarity": "rare", "skill": "critical_boost", "element": "风", "description": "法正的助手"},
    {"name": "蒋琬副将", "rarity": "common", "skill": "health_boost", "element": "水", "description": "蒋琬的幕僚"},
    {"name": "费祎副将", "rarity": "common", "skill": "heal_on_hit", "element": "水", "description": "费祎的助手"}
]

ELEMENT_COLORS = {
    "火": (255, 100, 100),
    "水": (100, 150, 255),
    "土": (150, 100, 50),
    "风": (100, 200, 100),
    "雷": (200, 100, 255)
}

SUBORDINATE_SLOTS = 2

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

class SubordinateSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "subordinates" not in data:
            data["subordinates"] = {
                "inventory": [],
                "equipped": {},
                "level": {}
            }
        save()
    
    def get_inventory(self):
        return data["subordinates"]["inventory"]
    
    def get_equipped(self, hero_name):
        return data["subordinates"]["equipped"].get(hero_name, [])
    
    def get_level(self, subordinate_name):
        return data["subordinates"]["level"].get(subordinate_name, 1)
    
    def can_recruit(self):
        cost = {"金元宝": 200}
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        return True, "可以招募"
    
    def recruit_subordinate(self):
        can_do, msg = self.can_recruit()
        if not can_do:
            return False, msg
        
        data["resources"]["金元宝"] -= 200
        
        rand = random.randint(1, 100)
        cumulative = 0
        rarity = "common"
        for r, info in SUBORDINATE_RARITY.items():
            cumulative += info["probability"]
            if rand <= cumulative:
                rarity = r
                break
        
        pool = [s for s in SUBORDINATE_POOL if s["rarity"] == rarity]
        subordinate = random.choice(pool)
        
        subordinate_data = {
            "name": subordinate["name"],
            "rarity": subordinate["rarity"],
            "skill": subordinate["skill"],
            "element": subordinate["element"],
            "description": subordinate["description"],
            "level": 1,
            "exp": 0
        }
        
        data["subordinates"]["inventory"].append(subordinate_data)
        save()
        
        return True, f"招募成功！获得{SUBORDINATE_RARITY[rarity]['name']}副将：{subordinate['name']}"
    
    def can_equip(self, hero_name, subordinate_name):
        equipped = self.get_equipped(hero_name)
        if len(equipped) >= SUBORDINATE_SLOTS:
            return False, "副将槽位已满"
        
        inventory = self.get_inventory()
        subordinate = next((s for s in inventory if s["name"] == subordinate_name), None)
        if not subordinate:
            return False, "副将不在背包中"
        
        for hero, subs in data["subordinates"]["equipped"].items():
            if subordinate_name in [s["name"] for s in subs]:
                return False, "该副将已装备给其他武将"
        
        return True, "可以装备"
    
    def equip_subordinate(self, hero_name, subordinate_name):
        can_do, msg = self.can_equip(hero_name, subordinate_name)
        if not can_do:
            return False, msg
        
        inventory = self.get_inventory()
        subordinate = next((s for s in inventory if s["name"] == subordinate_name), None)
        
        if hero_name not in data["subordinates"]["equipped"]:
            data["subordinates"]["equipped"][hero_name] = []
        
        data["subordinates"]["equipped"][hero_name].append(subordinate)
        save()
        
        return True, f"装备成功！{subordinate_name}成为{hero_name}的副将"
    
    def unequip_subordinate(self, hero_name, subordinate_name):
        if hero_name not in data["subordinates"]["equipped"]:
            return False, "该武将没有装备副将"
        
        equipped = data["subordinates"]["equipped"][hero_name]
        for i, sub in enumerate(equipped):
            if sub["name"] == subordinate_name:
                data["subordinates"]["equipped"][hero_name].pop(i)
                save()
                return True, f"卸下成功！{subordinate_name}"
        
        return False, "该副将未装备给此武将"
    
    def get_subordinate_bonus(self, subordinate):
        skill = SUBORDINATE_SKILLS.get(subordinate["skill"], {})
        rarity_multiplier = SUBORDINATE_RARITY[subordinate["rarity"]]["multiplier"]
        level = subordinate.get("level", 1)
        
        bonus = {}
        for stat, value in skill.get("effect", {}).items():
            bonus[stat] = value * rarity_multiplier * level
        
        return bonus
    
    def calculate_total_bonus(self, hero_name):
        equipped = self.get_equipped(hero_name)
        total_bonus = {
            "attack": 0.0,
            "defense": 0.0,
            "health": 0.0,
            "critical": 0.0,
            "speed": 0,
            "heal_on_hit": 0.0,
            "damage_reduction": 0.0,
            "skill_damage": 0.0,
            "rage_gain": 0.0,
            "element_damage": 0.0
        }
        
        for subordinate in equipped:
            bonus = self.get_subordinate_bonus(subordinate)
            for stat, value in bonus.items():
                if stat in total_bonus:
                    total_bonus[stat] += value
        
        return total_bonus

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

def draw_subordinate_card(surface, subordinate, x, y, width, height, font_main, font_small):
    rarity_info = SUBORDINATE_RARITY[subordinate["rarity"]]
    bg_color = rarity_info["color"]
    
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (*bg_color[:3], 150), (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, bg_color, (x, y, width, height), 2, border_radius=12)
    
    skill = SUBORDINATE_SKILLS.get(subordinate["skill"], {})
    icon = skill.get("icon", "👤")
    icon_font = pygame.font.Font(None, 40)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + width // 2, y + 35))
    surface.blit(icon_surf, icon_rect)
    
    name_surf = font_main.render(subordinate["name"], True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + width // 2, y + 75))
    surface.blit(name_surf, name_rect)
    
    rarity_text = rarity_info["name"]
    rarity_surf = font_small.render(rarity_text, True, bg_color)
    surface.blit(rarity_surf, (x + 10, y + 100))
    
    element_text = f"元素: {subordinate['element']}"
    element_color = ELEMENT_COLORS.get(subordinate['element'], (255, 255, 255))
    element_surf = font_small.render(element_text, True, element_color)
    surface.blit(element_surf, (x + width - 10 - element_surf.get_width(), y + 100))
    
    skill_name = skill.get("name", "未知技能")
    skill_surf = font_small.render(skill_name, True, COLORS["text_white"])
    surface.blit(skill_surf, (x + 10, y + 125))
    
    level_text = f"Lv.{subordinate.get('level', 1)}"
    level_surf = font_small.render(level_text, True, COLORS["accent_green"])
    surface.blit(level_surf, (x + width - 10 - level_surf.get_width(), y + 125))

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
        pygame.display.set_caption("副将系统")
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
        
        subordinate_system = SubordinateSystem()
        
        particles = []
        
        current_tab = "inventory"
        tabs = ["inventory", "equip", "recruit"]
        tab_names = ["副将背包", "装备副将", "招募副将"]
        
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
            
            draw_title(screen, "副将系统", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
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
            
            inventory = subordinate_system.get_inventory()
            
            if current_tab == "inventory":
                if inventory:
                    card_width = min(150, SCREEN_WIDTH * 0.16)
                    card_height = min(160, SCREEN_HEIGHT * 0.22)
                    cols = min(5, SCREEN_WIDTH // (card_width + 15))
                    start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 15)) // 2
                    
                    for i, subordinate in enumerate(inventory):
                        row = i // cols
                        col = i % cols
                        x = start_x + col * (card_width + 15)
                        y = content_y + row * (card_height + 15)
                        
                        draw_subordinate_card(screen, subordinate, x, y, card_width, card_height, font_main, font_small)
                else:
                    empty_text = font_main.render("暂无副将，请先招募", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "equip":
                if "hero_management" in data and data["hero_management"].get("heroes"):
                    heroes = data["hero_management"]["heroes"]
                    btn_width = min(200, SCREEN_WIDTH * 0.22)
                    btn_height = 60
                    start_x = (SCREEN_WIDTH - btn_width) // 2
                    
                    hero_buttons = []
                    for i, (hero_name, hero_data) in enumerate(heroes.items()):
                        y = content_y + i * (btn_height + 30)
                        if y > SCREEN_HEIGHT - 150:
                            break
                        
                        equipped = subordinate_system.get_equipped(hero_name)
                        bonus = subordinate_system.calculate_total_bonus(hero_name)
                        
                        bg_rect = pygame.Rect(start_x - 10, y - 5, btn_width + 20, btn_height + 40)
                        pygame.draw.rect(screen, COLORS["panel_bg"], bg_rect, border_radius=10)
                        pygame.draw.rect(screen, COLORS["accent_gold"], bg_rect, 2, border_radius=10)
                        
                        hero_surf = font_main.render(f"⚔️ {hero_name}", True, COLORS["accent_gold"])
                        screen.blit(hero_surf, (start_x, y))
                        
                        if equipped:
                            for j, sub in enumerate(equipped):
                                sub_text = f"  {j+1}. {sub['name']}"
                                sub_surf = font_small.render(sub_text, True, COLORS["text_white"])
                                screen.blit(sub_surf, (start_x + 10, y + 30))
                                
                                unequip_btn = Button(f"卸下", start_x + btn_width - 70, y + 25, 60, 30, font_small, COLORS["accent_red"], (255, 100, 100))
                                unequip_btn.update((mx, my))
                                unequip_btn.draw(screen)
                                hero_buttons.append((unequip_btn, hero_name, sub["name"], "unequip"))
                        else:
                            empty_text = font_small.render("  未装备副将", True, COLORS["text_gray"])
                            screen.blit(empty_text, (start_x + 10, y + 30))
                        
                        if bonus:
                            bonus_text = ""
                            if bonus["attack"] > 0:
                                bonus_text += f"⚔️+{int(bonus['attack']*100)}% "
                            if bonus["defense"] > 0:
                                bonus_text += f"🛡️+{int(bonus['defense']*100)}% "
                            if bonus["health"] > 0:
                                bonus_text += f"❤️+{int(bonus['health']*100)}% "
                            
                            if bonus_text:
                                bonus_surf = font_small.render(bonus_text, True, COLORS["accent_green"])
                                screen.blit(bonus_surf, (start_x, y + 65))
                        
                        available_subs = [s for s in inventory if s["name"] not in [sub["name"] for sub in equipped]]
                        if len(equipped) < SUBORDINATE_SLOTS and available_subs:
                            equip_btn = Button(f"装备副将", start_x, y + 70, btn_width, 40, font_small, COLORS["btn_green"], COLORS["btn_green_hover"])
                            equip_btn.update((mx, my))
                            equip_btn.draw(screen)
                            hero_buttons.append((equip_btn, hero_name, None, "equip_select"))
            elif current_tab == "recruit":
                recruit_btn = Button("🎲 招募副将 (200金元宝)", (SCREEN_WIDTH - 300) // 2, content_y, 300, 70, font_main, COLORS["btn_gold"], COLORS["btn_gold_hover"])
                recruit_btn.update((mx, my))
                recruit_btn.draw(screen)
                
                rarity_desc_y = content_y + 100
                for rarity, info in SUBORDINATE_RARITY.items():
                    rarity_text = f"{info['name']}: {info['probability']}%"
                    rarity_surf = font_small.render(rarity_text, True, info["color"])
                    screen.blit(rarity_surf, (SCREEN_WIDTH // 2 - 100 + (list(SUBORDINATE_RARITY.keys()).index(rarity) * 120), rarity_desc_y))
                
                if inventory:
                    recent_y = content_y + 150
                    recent_text = font_main.render("最近招募的副将:", True, COLORS["accent_gold"])
                    screen.blit(recent_text, (50, recent_y))
                    
                    recent_y += 40
                    for subordinate in inventory[-5:]:
                        draw_subordinate_card(screen, subordinate, 50, recent_y, 120, 140, font_main, font_small)
                        recent_y += 150
            
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
                    
                    if current_tab == "recruit" and recruit_btn.rect.collidepoint(mx, my):
                        success, msg = subordinate_system.recruit_subordinate()
                        message = msg
                        show_message = True
                        message_timer = 0
                    
                    elif current_tab == "equip" and 'hero_buttons' in locals():
                        for btn, hero_name, sub_name, action in hero_buttons:
                            if btn.rect.collidepoint(mx, my):
                                if action == "unequip":
                                    success, msg = subordinate_system.unequip_subordinate(hero_name, sub_name)
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                elif action == "equip_select":
                                    available_subs = [s for s in inventory if s["name"] not in [sub["name"] for sub in subordinate_system.get_equipped(hero_name)]]
                                    if available_subs:
                                        sub = available_subs[0]
                                        success, msg = subordinate_system.equip_subordinate(hero_name, sub["name"])
                                        message = msg
                                        show_message = True
                                        message_timer = 0
                                break
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("副将系统")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("副将系统", str(e))

if __name__ == "__main__":
    main()