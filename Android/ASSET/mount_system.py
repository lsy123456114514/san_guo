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
    "mount_common": (150, 150, 150),
    "mount_rare": (70, 180, 255),
    "mount_epic": (150, 100, 255),
    "mount_legendary": (255, 200, 100),
    "mount_mythic": (255, 100, 200)
}

MOUNTS = {
    "brown_horse": {
        "name": "褐马",
        "description": "普通战马，适合行军",
        "icon": "🐴",
        "rarity": "common",
        "base_stats": {"speed": 10, "attack": 5},
        "growth": {"speed": 2, "attack": 1},
        "max_level": 20,
        "skill": None,
        "obtain_method": "商店购买",
        "cost": {"金元宝": 200}
    },
    "white_horse": {
        "name": "白马",
        "description": "西凉宝马，速度较快",
        "icon": "🐎",
        "rarity": "rare",
        "base_stats": {"speed": 25, "attack": 15, "defense": 10},
        "growth": {"speed": 4, "attack": 2, "defense": 2},
        "max_level": 30,
        "skill": {"name": "疾风", "description": "战斗开始时速度提升10%", "effect": {"speed_buff": 0.1}},
        "obtain_method": "活动奖励",
        "cost": {"金元宝": 800}
    },
    "black_horse": {
        "name": "乌骓",
        "description": "项羽坐骑，勇猛无比",
        "icon": "🐴",
        "rarity": "rare",
        "base_stats": {"speed": 30, "attack": 25, "health": 50},
        "growth": {"speed": 5, "attack": 4, "health": 8},
        "max_level": 35,
        "skill": {"name": "踏雪", "description": "受到攻击时有10%概率闪避", "effect": {"dodge_rate": 0.1}},
        "obtain_method": "副本掉落",
        "cost": {"金元宝": 1500}
    },
    "red_rabbit": {
        "name": "赤兔",
        "description": "关羽坐骑，日行千里",
        "icon": "🐇",
        "rarity": "legendary",
        "base_stats": {"speed": 60, "attack": 50, "critical": 0.1},
        "growth": {"speed": 8, "attack": 6, "critical": 0.01},
        "max_level": 50,
        "skill": {"name": "神速", "description": "速度提升30%，暴击时额外造成50%伤害", "effect": {"speed_multiplier": 1.3, "critical_bonus": 0.5}},
        "obtain_method": "限时活动",
        "cost": {"金元宝": 5000, "将魂": 1000}
    },
    "jade_lion": {
        "name": "玉狮子",
        "description": "赵云坐骑，神骏非凡",
        "icon": "🦁",
        "rarity": "legendary",
        "base_stats": {"speed": 50, "defense": 60, "health": 100},
        "growth": {"speed": 6, "defense": 8, "health": 15},
        "max_level": 50,
        "skill": {"name": "守护", "description": "为主将提供护盾，吸收20%伤害", "effect": {"shield_absorb": 0.2}},
        "obtain_method": "神兵锻造",
        "cost": {"金元宝": 6000, "神兵碎片": 50}
    },
    "blood_horse": {
        "name": "的卢",
        "description": "刘备坐骑，妨主却救主",
        "icon": "🐴",
        "rarity": "legendary",
        "base_stats": {"speed": 55, "attack": 40, "health": 80},
        "growth": {"speed": 7, "attack": 5, "health": 12},
        "max_level": 50,
        "skill": {"name": "跃檀溪", "description": "生命值低于30%时，闪避率提升50%", "effect": {"low_hp_dodge": 0.5}},
        "obtain_method": "剧情获得",
        "cost": {"金元宝": 4500, "将魂": 800}
    },
    "phoenix": {
        "name": "火凤凰",
        "description": "传说神鸟，浴火重生",
        "icon": "🔥",
        "rarity": "mythic",
        "base_stats": {"speed": 100, "attack": 100, "health": 200, "critical": 0.2},
        "growth": {"speed": 12, "attack": 10, "health": 25, "critical": 0.015},
        "max_level": 80,
        "skill": {"name": "涅槃", "description": "死亡时有30%概率复活并恢复50%生命", "effect": {"revive_rate": 0.3, "revive_health": 0.5}},
        "obtain_method": "神话召唤",
        "cost": {"金元宝": 20000, "神晶": 50}
    },
    "dragon": {
        "name": "青龙",
        "description": "上古神龙，威震天下",
        "icon": "🐉",
        "rarity": "mythic",
        "base_stats": {"speed": 120, "attack": 150, "defense": 100, "critical": 0.3},
        "growth": {"speed": 15, "attack": 15, "defense": 12, "critical": 0.02},
        "max_level": 100,
        "skill": {"name": "龙威", "description": "降低所有敌人20%攻击力，提升自身50%攻击力", "effect": {"enemy_debuff": 0.2, "self_buff": 0.5}},
        "obtain_method": "充值奖励",
        "cost": {"金元宝": 50000, "神晶": 100}
    }
}

RARITY_COLORS = {
    "common": {"name": "普通", "color": COLORS["mount_common"], "glow": (100, 100, 100)},
    "rare": {"name": "稀有", "color": COLORS["mount_rare"], "glow": (50, 150, 200)},
    "epic": {"name": "史诗", "color": COLORS["mount_epic"], "glow": (100, 50, 200)},
    "legendary": {"name": "传说", "color": COLORS["mount_legendary"], "glow": (200, 150, 50)},
    "mythic": {"name": "神话", "color": COLORS["mount_mythic"], "glow": (200, 50, 150)}
}

UPGRADE_COST = {
    "common": {"金元宝": 50, "粮草": 100},
    "rare": {"金元宝": 150, "粮草": 300},
    "epic": {"金元宝": 400, "粮草": 800},
    "legendary": {"金元宝": 1000, "粮草": 2000, "将魂": 100},
    "mythic": {"金元宝": 3000, "粮草": 5000, "将魂": 300, "神晶": 5}
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

class MountSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "mounts" not in data:
            data["mounts"] = {
                "inventory": [],
                "equipped": {},
                "levels": {},
                "exp": {}
            }
        if "resources" not in data:
            data["resources"] = {}
        if "粮草" not in data["resources"]:
            data["resources"]["粮草"] = 0
        save()
    
    def get_inventory(self):
        return data["mounts"]["inventory"]
    
    def get_equipped(self, hero_name):
        return data["mounts"]["equipped"].get(hero_name)
    
    def get_mount_level(self, mount_id):
        return data["mounts"]["levels"].get(mount_id, 1)
    
    def get_mount_exp(self, mount_id):
        return data["mounts"]["exp"].get(mount_id, 0)
    
    def purchase_mount(self, mount_id):
        mount_data = MOUNTS.get(mount_id)
        if not mount_data:
            return False, "坐骑不存在"
        
        for resource, amount in mount_data["cost"].items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        for resource, amount in mount_data["cost"].items():
            data["resources"][resource] -= amount
        
        mount_instance = {
            "id": mount_id,
            "name": mount_data["name"],
            "rarity": mount_data["rarity"],
            "level": 1,
            "exp": 0
        }
        
        data["mounts"]["inventory"].append(mount_instance)
        data["mounts"]["levels"][mount_id] = 1
        data["mounts"]["exp"][mount_id] = 0
        
        save()
        
        return True, f"购买成功！获得坐骑：{mount_data['name']}"
    
    def can_upgrade(self, mount_id):
        mount_instance = next((m for m in self.get_inventory() if m["id"] == mount_id), None)
        if not mount_instance:
            return False, "坐骑不在背包中"
        
        mount_data = MOUNTS.get(mount_id)
        level = self.get_mount_level(mount_id)
        
        if level >= mount_data["max_level"]:
            return False, "已达到最高等级"
        
        cost = UPGRADE_COST.get(mount_data["rarity"], {})
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount * level:
                return False, f"资源不足：{resource}"
        
        return True, "可以升级"
    
    def upgrade_mount(self, mount_id):
        can_do, msg = self.can_upgrade(mount_id)
        if not can_do:
            return False, msg
        
        mount_data = MOUNTS.get(mount_id)
        level = self.get_mount_level(mount_id)
        
        cost = UPGRADE_COST.get(mount_data["rarity"], {})
        for resource, amount in cost.items():
            data["resources"][resource] -= amount * level
        
        data["mounts"]["levels"][mount_id] = level + 1
        
        for i, mount in enumerate(data["mounts"]["inventory"]):
            if mount["id"] == mount_id:
                data["mounts"]["inventory"][i]["level"] = level + 1
                break
        
        save()
        
        return True, f"升级成功！坐骑等级提升至 {level + 1}"
    
    def can_equip(self, hero_name, mount_id):
        mount_instance = next((m for m in self.get_inventory() if m["id"] == mount_id), None)
        if not mount_instance:
            return False, "坐骑不在背包中"
        
        for hero, mid in data["mounts"]["equipped"].items():
            if mid == mount_id:
                return False, "该坐骑已装备给其他武将"
        
        return True, "可以装备"
    
    def equip_mount(self, hero_name, mount_id):
        can_do, msg = self.can_equip(hero_name, mount_id)
        if not can_do:
            return False, msg
        
        data["mounts"]["equipped"][hero_name] = mount_id
        save()
        
        return True, f"装备成功！{hero_name}骑乘{MOUNTS[mount_id]['name']}"
    
    def unequip_mount(self, hero_name):
        if hero_name not in data["mounts"]["equipped"]:
            return False, "该武将未装备坐骑"
        
        del data["mounts"]["equipped"][hero_name]
        save()
        
        return True, "卸下成功"
    
    def get_mount_stats(self, mount_id):
        mount_data = MOUNTS.get(mount_id)
        if not mount_data:
            return {}
        
        level = self.get_mount_level(mount_id)
        stats = {}
        
        for stat, base_value in mount_data["base_stats"].items():
            growth = mount_data["growth"].get(stat, 0)
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

def draw_mount_card(surface, mount, x, y, width, height, font_main, font_small):
    mount_data = MOUNTS.get(mount["id"])
    if not mount_data:
        return
    
    rarity_info = RARITY_COLORS[mount["rarity"]]
    bg_color = rarity_info["color"]
    
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (*bg_color[:3], 150), (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, bg_color, (x, y, width, height), 2, border_radius=12)
    
    icon_font = pygame.font.Font(None, 45)
    icon_surf = icon_font.render(mount_data["icon"], True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + width // 2, y + 35))
    surface.blit(icon_surf, icon_rect)
    
    name_surf = font_main.render(mount["name"], True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + width // 2, y + 80))
    surface.blit(name_surf, name_rect)
    
    rarity_text = rarity_info["name"]
    rarity_surf = font_small.render(rarity_text, True, bg_color)
    surface.blit(rarity_surf, (x + 10, y + 110))
    
    level_text = f"Lv.{mount['level']}/{mount_data['max_level']}"
    level_surf = font_small.render(level_text, True, COLORS["accent_green"])
    surface.blit(level_surf, (x + width - 10 - level_surf.get_width(), y + 110))
    
    stats = MountSystem().get_mount_stats(mount["id"])
    stat_y = y + 135
    for stat, value in list(stats.items())[:3]:
        stat_name = {"speed": "速度", "attack": "攻击", "defense": "防御", "health": "生命", "critical": "暴击"}.get(stat, stat)
        stat_text = f"{stat_name}: {value}"
        stat_surf = font_small.render(stat_text, True, COLORS["text_white"])
        surface.blit(stat_surf, (x + 10, stat_y))
        stat_y += 20
    
    skill = mount_data.get("skill")
    if skill:
        skill_text = f"✨ {skill['name']}"
        skill_surf = font_small.render(skill_text, True, COLORS["accent_purple"])
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
        pygame.display.set_caption("坐骑系统")
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
        
        mount_system = MountSystem()
        
        particles = []
        
        current_tab = "shop"
        tabs = ["shop", "inventory", "equip"]
        tab_names = ["坐骑商店", "坐骑背包", "装备坐骑"]
        
        message = ""
        show_message = False
        message_timer = 0
        
        selected_mount = None
        
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
            
            draw_title(screen, "坐骑系统", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
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
            
            inventory = mount_system.get_inventory()
            
            if current_tab == "shop":
                card_width = min(180, SCREEN_WIDTH * 0.2)
                card_height = min(160, SCREEN_HEIGHT * 0.22)
                cols = min(4, SCREEN_WIDTH // (card_width + 15))
                start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 15)) // 2
                
                shop_buttons = []
                for i, (mount_id, mount_data) in enumerate(MOUNTS.items()):
                    row = i // cols
                    col = i % cols
                    x = start_x + col * (card_width + 15)
                    y = content_y + row * (card_height + 15)
                    
                    already_have = any(m["id"] == mount_id for m in inventory)
                    
                    rarity_info = RARITY_COLORS[mount_data["rarity"]]
                    bg_color = rarity_info["color"]
                    
                    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                    opacity = 150 if not already_have else 80
                    pygame.draw.rect(card_surf, (*bg_color[:3], opacity), (0, 0, card_width, card_height), border_radius=12)
                    screen.blit(card_surf, (x, y))
                    
                    if already_have:
                        pygame.draw.rect(screen, (100, 100, 100), (x, y, card_width, card_height), 2, border_radius=12)
                    else:
                        pygame.draw.rect(screen, bg_color, (x, y, card_width, card_height), 2, border_radius=12)
                    
                    icon_font = pygame.font.Font(None, int(35 * scale))
                    icon_surf = icon_font.render(mount_data["icon"], True, COLORS["text_white"])
                    screen.blit(icon_surf, (x + card_width // 2 - icon_surf.get_width() // 2, y + 15))
                    
                    name_surf = font_small.render(mount_data["name"], True, COLORS["accent_gold"])
                    screen.blit(name_surf, (x + card_width // 2 - name_surf.get_width() // 2, y + 60))
                    
                    rarity_text = rarity_info["name"]
                    rarity_surf = font_small.render(rarity_text, True, bg_color)
                    screen.blit(rarity_surf, (x + 10, y + 85))
                    
                    if already_have:
                        owned_surf = font_small.render("✓ 已拥有", True, COLORS["accent_green"])
                        screen.blit(owned_surf, (x + card_width // 2 - owned_surf.get_width() // 2, y + 110))
                    else:
                        cost_text = ", ".join([f"{v}{k}" for k, v in mount_data["cost"].items()])
                        cost_surf = font_small.render(cost_text, True, COLORS["accent_orange"])
                        screen.blit(cost_surf, (x + card_width // 2 - cost_surf.get_width() // 2, y + 95))
                        
                        buy_btn = Button("购买", x + (card_width - 60) // 2, y + 125, 60, 30, font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"])
                        buy_btn.update((mx, my))
                        buy_btn.draw(screen)
                        shop_buttons.append((buy_btn, mount_id))
            
            elif current_tab == "inventory":
                if inventory:
                    card_width = min(200, SCREEN_WIDTH * 0.22)
                    card_height = min(180, SCREEN_HEIGHT * 0.25)
                    cols = min(4, SCREEN_WIDTH // (card_width + 15))
                    start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 15)) // 2
                    
                    mount_buttons = []
                    for i, mount in enumerate(inventory):
                        row = i // cols
                        col = i % cols
                        x = start_x + col * (card_width + 15)
                        y = content_y + row * (card_height + 15)
                        
                        draw_mount_card(screen, mount, x, y, card_width, card_height, font_main, font_small)
                        
                        card_rect = pygame.Rect(x, y, card_width, card_height)
                        is_selected = selected_mount == mount["id"]
                        if is_selected:
                            pygame.draw.rect(screen, COLORS["accent_gold"], card_rect, 4, border_radius=12)
                        
                        mount_buttons.append((card_rect, mount))
                    
                    if selected_mount:
                        mount = next((m for m in inventory if m["id"] == selected_mount), None)
                        if mount:
                            info_panel_x = SCREEN_WIDTH * 0.05
                            info_panel_y = SCREEN_HEIGHT * 0.82
                            info_panel_width = SCREEN_WIDTH * 0.9
                            info_panel_height = SCREEN_HEIGHT * 0.13
                            
                            info_surf = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
                            pygame.draw.rect(info_surf, COLORS["panel_bg"], (0, 0, info_panel_width, info_panel_height), border_radius=12)
                            screen.blit(info_surf, (info_panel_x, info_panel_y))
                            
                            mount_data = MOUNTS.get(mount["id"])
                            if mount_data:
                                can_upgrade, upgrade_msg = mount_system.can_upgrade(mount["id"])
                                upgrade_btn = Button(f"升级 ({mount['level']}/{mount_data['max_level']})", info_panel_x + 20, info_panel_y + 15, 200, 40, font_small, 
                                                   COLORS["btn_green"] if can_upgrade else COLORS["accent_red"], 
                                                   COLORS["btn_green_hover"] if can_upgrade else (200, 80, 80))
                                upgrade_btn.update((mx, my))
                                upgrade_btn.draw(screen)
                                
                                if mount_data.get("skill"):
                                    skill_text = f"技能: {mount_data['skill']['name']} - {mount_data['skill']['description']}"
                                    skill_surf = font_small.render(skill_text, True, COLORS["accent_purple"])
                                    screen.blit(skill_surf, (info_panel_x + 230, info_panel_y + 20))
                else:
                    empty_text = font_main.render("暂无坐骑，请先购买", True, COLORS["text_gray"])
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
                            
                            equipped_mount_id = mount_system.get_equipped(hero_name)
                            
                            bg_rect = pygame.Rect(start_x - 5, y - 5, btn_width + 10, btn_height + 10)
                            pygame.draw.rect(screen, COLORS["panel_bg"], bg_rect, border_radius=8)
                            
                            hero_surf = font_main.render(f"⚔️ {hero_name}", True, COLORS["accent_gold"])
                            screen.blit(hero_surf, (start_x, y + 15))
                            
                            if equipped_mount_id:
                                mount = next((m for m in inventory if m["id"] == equipped_mount_id), None)
                                if mount:
                                    mount_data = MOUNTS.get(mount["id"])
                                    mount_name_surf = font_small.render(f"坐骑: {mount_data['icon']} {mount['name']}", True, COLORS["accent_green"])
                                    screen.blit(mount_name_surf, (start_x + 120, y + 20))
                                    
                                    unequip_btn = Button("卸下", start_x + btn_width - 70, y + 10, 60, 30, font_small, COLORS["accent_red"], (255, 100, 100))
                                    unequip_btn.update((mx, my))
                                    unequip_btn.draw(screen)
                                    hero_buttons.append((unequip_btn, hero_name, None, "unequip"))
                            else:
                                empty_text = font_small.render("未装备坐骑", True, COLORS["text_gray"])
                                screen.blit(empty_text, (start_x + 120, y + 20))
                                
                                available_mounts = [m for m in inventory if m["id"] not in data["mounts"]["equipped"].values()]
                                if available_mounts:
                                    equip_btn = Button("装备坐骑", start_x + btn_width - 120, y + 10, 110, 30, font_small, COLORS["btn_green"], COLORS["btn_green_hover"])
                                    equip_btn.update((mx, my))
                                    equip_btn.draw(screen)
                                    hero_buttons.append((equip_btn, hero_name, available_mounts[0]["id"], "equip"))
                    else:
                        empty_text = font_main.render("暂无武将", True, COLORS["text_gray"])
                        screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
                else:
                    empty_text = font_main.render("暂无坐骑，请先购买", True, COLORS["text_gray"])
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
                    
                    if current_tab == "shop" and 'shop_buttons' in locals():
                        for btn, mount_id in shop_buttons:
                            if btn.rect.collidepoint(mx, my):
                                success, msg = mount_system.purchase_mount(mount_id)
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                    
                    elif current_tab == "inventory" and 'mount_buttons' in locals():
                        for rect, mount in mount_buttons:
                            if rect.collidepoint(mx, my):
                                selected_mount = mount["id"]
                                break
                        
                        if selected_mount:
                            mount = next((m for m in inventory if m["id"] == selected_mount), None)
                            if mount:
                                info_panel_x = SCREEN_WIDTH * 0.05
                                info_panel_y = SCREEN_HEIGHT * 0.82
                                
                                upgrade_rect = pygame.Rect(info_panel_x + 20, info_panel_y + 15, 200, 40)
                                if upgrade_rect.collidepoint(mx, my):
                                    success, msg = mount_system.upgrade_mount(mount["id"])
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                    
                    elif current_tab == "equip" and 'hero_buttons' in locals():
                        for btn, hero_name, mount_id, action in hero_buttons:
                            if btn.rect.collidepoint(mx, my):
                                if action == "unequip":
                                    success, msg = mount_system.unequip_mount(hero_name)
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                elif action == "equip":
                                    success, msg = mount_system.equip_mount(hero_name, mount_id)
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                break
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("坐骑系统")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("坐骑系统", str(e))

if __name__ == "__main__":
    main()