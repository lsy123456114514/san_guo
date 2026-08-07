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
    "legion_red": (200, 50, 50),
    "legion_blue": (50, 100, 200),
    "legion_green": (50, 150, 50),
    "legion_purple": (150, 50, 200)
}

LEGION_RANKS = {
    1: {"name": "校尉", "icon": "🎖️", "bonus": {"attack": 0.05}, "required_contribution": 0},
    2: {"name": "偏将", "icon": "⚔️", "bonus": {"attack": 0.1, "defense": 0.05}, "required_contribution": 500},
    3: {"name": "中郎将", "icon": "🛡️", "bonus": {"attack": 0.15, "defense": 0.1}, "required_contribution": 1500},
    4: {"name": "将军", "icon": "⭐", "bonus": {"attack": 0.2, "defense": 0.15, "health": 0.1}, "required_contribution": 4000},
    5: {"name": "骠骑将军", "icon": "🏆", "bonus": {"attack": 0.3, "defense": 0.2, "health": 0.15}, "required_contribution": 10000},
    6: {"name": "大将军", "icon": "👑", "bonus": {"attack": 0.4, "defense": 0.3, "health": 0.25}, "required_contribution": 25000},
    7: {"name": "大司马", "icon": "🔮", "bonus": {"attack": 0.5, "defense": 0.4, "health": 0.35, "speed": 0.1}, "required_contribution": 50000}
}

LEGION_TASKS = {
    "daily_attack": {
        "name": "每日征讨",
        "description": "完成10次战斗",
        "type": "daily",
        "target_count": 10,
        "reward": {"contribution": 100, "金元宝": 50},
        "icon": "⚔️"
    },
    "daily_recruit": {
        "name": "每日招募",
        "description": "招募3名武将",
        "type": "daily",
        "target_count": 3,
        "reward": {"contribution": 150, "将魂": 100},
        "icon": "🎯"
    },
    "daily_equip": {
        "name": "每日锻造",
        "description": "强化装备5次",
        "type": "daily",
        "target_count": 5,
        "reward": {"contribution": 80, "金元宝": 30},
        "icon": "⚙️"
    },
    "weekly_battle": {
        "name": "周战强敌",
        "description": "击败50个敌人",
        "type": "weekly",
        "target_count": 50,
        "reward": {"contribution": 500, "神兵碎片": 20},
        "icon": "🐉"
    },
    "weekly_resource": {
        "name": "资源收集",
        "description": "收集1000单位资源",
        "type": "weekly",
        "target_count": 1000,
        "reward": {"contribution": 400, "金元宝": 200},
        "icon": "💰"
    },
    "monthly_hero": {
        "name": "名将收集",
        "description": "招募10名橙色品质武将",
        "type": "monthly",
        "target_count": 10,
        "reward": {"contribution": 2000, "神晶": 10, "金元宝": 1000},
        "icon": "⭐"
    }
}

LEGION_BOSSES = {
    "tiger": {
        "name": "白虎",
        "icon": "🐯",
        "health": 10000,
        "attack": 500,
        "defense": 200,
        "reward": {"contribution": 200, "金元宝": 100, "神兵碎片": 5},
        "level": 1
    },
    "dragon": {
        "name": "青龙",
        "icon": "🐉",
        "health": 50000,
        "attack": 1500,
        "defense": 800,
        "reward": {"contribution": 500, "金元宝": 300, "神兵碎片": 20},
        "level": 2
    },
    "phoenix": {
        "name": "朱雀",
        "icon": "🔥",
        "health": 150000,
        "attack": 3500,
        "defense": 2000,
        "reward": {"contribution": 1200, "金元宝": 800, "神晶": 5},
        "level": 3
    },
    "turtle": {
        "name": "玄武",
        "icon": "🐢",
        "health": 500000,
        "attack": 8000,
        "defense": 5000,
        "reward": {"contribution": 3000, "金元宝": 2000, "神晶": 20},
        "level": 4
    }
}

LEGION_LEVELS = {
    1: {"name": "小队", "max_members": 10, "required_exp": 0, "bonus": {"attack": 0.05}},
    2: {"name": "中队", "max_members": 20, "required_exp": 5000, "bonus": {"attack": 0.1}},
    3: {"name": "大队", "max_members": 35, "required_exp": 20000, "bonus": {"attack": 0.15, "defense": 0.05}},
    4: {"name": "营", "max_members": 50, "required_exp": 50000, "bonus": {"attack": 0.2, "defense": 0.1}},
    5: {"name": "团", "max_members": 80, "required_exp": 100000, "bonus": {"attack": 0.25, "defense": 0.15, "health": 0.1}},
    6: {"name": "旅", "max_members": 120, "required_exp": 200000, "bonus": {"attack": 0.35, "defense": 0.25, "health": 0.15}},
    7: {"name": "师", "max_members": 200, "required_exp": 500000, "bonus": {"attack": 0.5, "defense": 0.4, "health": 0.25}},
    8: {"name": "军", "max_members": 300, "required_exp": 1000000, "bonus": {"attack": 0.7, "defense": 0.55, "health": 0.4}}
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

class LegionSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "legion" not in data:
            data["legion"] = {
                "legions": {},
                "player_legion": None,
                "player_contribution": 0,
                "player_rank": 1,
                "tasks_progress": {},
                "boss_health": {"tiger": 10000, "dragon": 50000, "phoenix": 150000, "turtle": 500000},
                "boss_defeated": [],
                "legion_battle": {"enemy": None, "status": "idle"}
            }
        if "legions" not in data["legion"]:
            data["legion"]["legions"] = {}
        save()
    
    def create_legion(self, name, player_name):
        if data["legion"]["player_legion"]:
            return False, "您已加入军团"
        
        if name in data["legion"]["legions"]:
            return False, "军团名称已存在"
        
        cost = {"金元宝": 1000}
        if data["resources"].get("金元宝", 0) < cost["金元宝"]:
            return False, "资源不足：金元宝"
        
        data["resources"]["金元宝"] -= cost["金元宝"]
        
        data["legion"]["legions"][name] = {
            "name": name,
            "leader": player_name,
            "members": [{"name": player_name, "contribution": 0, "rank": 7}],
            "level": 1,
            "exp": 0,
            "created_time": pygame.time.get_ticks(),
            "description": "新成立的军团"
        }
        
        data["legion"]["player_legion"] = name
        data["legion"]["player_contribution"] = 0
        data["legion"]["player_rank"] = 7
        
        save()
        
        return True, f"军团创建成功！{name}"
    
    def join_legion(self, legion_name, player_name):
        if data["legion"]["player_legion"]:
            return False, "您已加入军团"
        
        if legion_name not in data["legion"]["legions"]:
            return False, "军团不存在"
        
        legion = data["legion"]["legions"][legion_name]
        if len(legion["members"]) >= LEGION_LEVELS[legion["level"]]["max_members"]:
            return False, "军团人数已满"
        
        legion["members"].append({"name": player_name, "contribution": 0, "rank": 1})
        data["legion"]["player_legion"] = legion_name
        data["legion"]["player_contribution"] = 0
        data["legion"]["player_rank"] = 1
        
        save()
        
        return True, f"加入军团成功！{legion_name}"
    
    def leave_legion(self, player_name):
        legion_name = data["legion"]["player_legion"]
        if not legion_name:
            return False, "您未加入军团"
        
        legion = data["legion"]["legions"][legion_name]
        if legion["leader"] == player_name:
            return False, "军团长不能退出，需先转让职位"
        
        for i, member in enumerate(legion["members"]):
            if member["name"] == player_name:
                legion["members"].pop(i)
                break
        
        data["legion"]["player_legion"] = None
        data["legion"]["player_contribution"] = 0
        data["legion"]["player_rank"] = 1
        
        save()
        
        return True, "退出军团成功"
    
    def get_legion_list(self):
        return list(data["legion"]["legions"].values())
    
    def get_current_legion(self):
        legion_name = data["legion"]["player_legion"]
        if not legion_name:
            return None
        return data["legion"]["legions"].get(legion_name)
    
    def contribute(self, amount):
        if not data["legion"]["player_legion"]:
            return False, "您未加入军团"
        
        if data["resources"].get("金元宝", 0) < amount:
            return False, "资源不足"
        
        data["resources"]["金元宝"] -= amount
        
        contribution = amount * 2
        data["legion"]["player_contribution"] += contribution
        
        legion_name = data["legion"]["player_legion"]
        legion = data["legion"]["legions"][legion_name]
        
        for member in legion["members"]:
            if member["name"] == data.get("username", "player"):
                member["contribution"] += contribution
                break
        
        legion["exp"] += contribution
        
        current_level = legion["level"]
        next_level = current_level + 1
        if next_level <= len(LEGION_LEVELS) and legion["exp"] >= LEGION_LEVELS[next_level]["required_exp"]:
            legion["level"] = next_level
        
        self._update_rank()
        
        save()
        
        return True, f"贡献成功！获得{contribution}贡献值"
    
    def _update_rank(self):
        contribution = data["legion"]["player_contribution"]
        for rank, info in sorted(LEGION_RANKS.items(), reverse=True):
            if contribution >= info["required_contribution"]:
                data["legion"]["player_rank"] = rank
                break
    
    def attack_boss(self, boss_id, damage):
        if not data["legion"]["player_legion"]:
            return False, "您未加入军团"
        
        boss_data = LEGION_BOSSES.get(boss_id)
        if not boss_data:
            return False, "Boss不存在"
        
        current_health = data["legion"]["boss_health"].get(boss_id, boss_data["health"])
        current_health -= damage
        
        if current_health <= 0:
            data["legion"]["boss_health"][boss_id] = boss_data["health"]
            if boss_id not in data["legion"]["boss_defeated"]:
                data["legion"]["boss_defeated"].append(boss_id)
            
            for resource, amount in boss_data["reward"].items():
                if resource == "contribution":
                    data["legion"]["player_contribution"] += amount
                    legion_name = data["legion"]["player_legion"]
                    legion = data["legion"]["legions"][legion_name]
                    for member in legion["members"]:
                        if member["name"] == data.get("username", "player"):
                            member["contribution"] += amount
                            break
                else:
                    data["resources"][resource] = data["resources"].get(resource, 0) + amount
            
            self._update_rank()
            save()
            return True, f"击杀Boss {boss_data['name']}！获得奖励！"
        else:
            data["legion"]["boss_health"][boss_id] = current_health
            contribution_gain = damage // 100
            data["legion"]["player_contribution"] += contribution_gain
            self._update_rank()
            save()
            return True, f"造成{damage}点伤害，获得{contribution_gain}贡献值"
    
    def get_task_progress(self, task_id):
        return data["legion"]["tasks_progress"].get(task_id, 0)
    
    def update_task_progress(self, task_id, amount):
        data["legion"]["tasks_progress"][task_id] = data["legion"]["tasks_progress"].get(task_id, 0) + amount
    
    def claim_task_reward(self, task_id):
        task = LEGION_TASKS.get(task_id)
        if not task:
            return False, "任务不存在"
        
        progress = self.get_task_progress(task_id)
        if progress < task["target_count"]:
            return False, "任务未完成"
        
        for resource, amount in task["reward"].items():
            if resource == "contribution":
                data["legion"]["player_contribution"] += amount
            else:
                data["resources"][resource] = data["resources"].get(resource, 0) + amount
        
        data["legion"]["tasks_progress"][task_id] = 0
        self._update_rank()
        save()
        
        return True, f"领取奖励成功！"

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

def draw_legion_card(surface, legion, x, y, width, height, font_main, font_small):
    level_data = LEGION_LEVELS[legion["level"]]
    
    bg_color = COLORS["legion_red"] if legion["level"] >= 5 else COLORS["legion_blue"]
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (*bg_color[:3], 150), (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, bg_color, (x, y, width, height), 2, border_radius=12)
    
    name_surf = font_main.render(legion["name"], True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + width // 2, y + 30))
    surface.blit(name_surf, name_rect)
    
    level_text = f"Lv.{legion['level']} {level_data['name']}"
    level_surf = font_small.render(level_text, True, COLORS["text_white"])
    surface.blit(level_surf, (x + 10, y + 60))
    
    member_count = len(legion["members"])
    max_members = level_data["max_members"]
    member_text = f"成员: {member_count}/{max_members}"
    member_surf = font_small.render(member_text, True, COLORS["text_gray"])
    surface.blit(member_surf, (x + width - 10 - member_surf.get_width(), y + 60))
    
    leader_text = f"军团长: {legion['leader']}"
    leader_surf = font_small.render(leader_text, True, COLORS["accent_purple"])
    surface.blit(leader_surf, (x + 10, y + 85))
    
    exp_text = f"经验: {legion['exp']}/{LEGION_LEVELS.get(legion['level'] + 1, {'required_exp': legion['exp']})['required_exp']}"
    exp_surf = font_small.render(exp_text, True, COLORS["text_gray"])
    surface.blit(exp_surf, (x + 10, y + 110))

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
        pygame.display.set_caption("军团系统")
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
        
        legion_system = LegionSystem()
        
        particles = []
        
        current_tab = "list"
        tabs = ["list", "create", "my", "tasks", "boss"]
        tab_names = ["军团列表", "创建军团", "我的军团", "军团任务", "军团Boss"]
        
        message = ""
        show_message = False
        message_timer = 0
        
        player_name = data.get("username", "player")
        
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
            
            draw_title(screen, "军团系统", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            tab_y = SCREEN_HEIGHT * 0.18
            tab_width = 120
            tab_height = 40
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
            
            if current_tab == "list":
                legions = legion_system.get_legion_list()
                
                if legions:
                    card_width = min(220, SCREEN_WIDTH * 0.24)
                    card_height = min(150, SCREEN_HEIGHT * 0.21)
                    cols = min(4, SCREEN_WIDTH // (card_width + 15))
                    start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 15)) // 2
                    
                    join_buttons = []
                    for i, legion in enumerate(legions):
                        row = i // cols
                        col = i % cols
                        x = start_x + col * (card_width + 15)
                        y = content_y + row * (card_height + 15)
                        
                        draw_legion_card(screen, legion, x, y, card_width, card_height, font_main, font_small)
                        
                        can_join = len(legion["members"]) < LEGION_LEVELS[legion["level"]]["max_members"]
                        if can_join:
                            join_btn = Button("加入", x + (card_width - 70) // 2, y + 115, 70, 30, font_small, COLORS["btn_green"], COLORS["btn_green_hover"])
                            join_btn.update((mx, my))
                            join_btn.draw(screen)
                            join_buttons.append((join_btn, legion["name"]))
                else:
                    empty_text = font_main.render("暂无军团，快去创建一个吧！", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "create":
                name_label = font_main.render("军团名称:", True, COLORS["text_white"])
                screen.blit(name_label, (SCREEN_WIDTH // 2 - 200, content_y))
                
                input_box = pygame.Rect(SCREEN_WIDTH // 2 - 50, content_y - 5, 250, 40)
                pygame.draw.rect(screen, COLORS["panel_bg"], input_box, border_radius=8)
                pygame.draw.rect(screen, COLORS["accent_gold"], input_box, 2, border_radius=8)
                
                cost_text = font_small.render("创建费用: 1000金元宝", True, COLORS["accent_orange"])
                screen.blit(cost_text, (SCREEN_WIDTH // 2 - cost_text.get_width() // 2, content_y + 60))
                
                create_btn = Button("创建军团", SCREEN_WIDTH // 2 - 100, content_y + 100, 200, 50, font_main, COLORS["btn_gold"], COLORS["btn_gold_hover"])
                create_btn.update((mx, my))
                create_btn.draw(screen)
            
            elif current_tab == "my":
                current_legion = legion_system.get_current_legion()
                
                if current_legion:
                    level_data = LEGION_LEVELS[current_legion["level"]]
                    rank_data = LEGION_RANKS[data["legion"]["player_rank"]]
                    
                    info_panel_x = SCREEN_WIDTH * 0.05
                    info_panel_y = content_y
                    info_panel_width = SCREEN_WIDTH * 0.9
                    info_panel_height = SCREEN_HEIGHT * 0.2
                    
                    info_surf = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
                    pygame.draw.rect(info_surf, COLORS["panel_bg"], (0, 0, info_panel_width, info_panel_height), border_radius=12)
                    screen.blit(info_surf, (info_panel_x, info_panel_y))
                    
                    legion_name_surf = font_title.render(current_legion["name"], True, COLORS["accent_gold"])
                    screen.blit(legion_name_surf, (info_panel_x + 20, info_panel_y + 20))
                    
                    level_text = f"等级: Lv.{current_legion['level']} {level_data['name']} | 成员: {len(current_legion['members'])}/{level_data['max_members']}"
                    level_surf = font_main.render(level_text, True, COLORS["text_white"])
                    screen.blit(level_surf, (info_panel_x + 20, info_panel_y + 70))
                    
                    contribution_text = f"您的贡献: {data['legion']['player_contribution']} | 职位: {rank_data['icon']} {rank_data['name']}"
                    contribution_surf = font_main.render(contribution_text, True, COLORS["accent_purple"])
                    screen.blit(contribution_surf, (info_panel_x + 20, info_panel_y + 110))
                    
                    contribute_btn = Button("贡献 (100金元宝=200贡献)", info_panel_x + info_panel_width - 300, info_panel_y + 20, 280, 40, font_small, COLORS["btn_blue"], COLORS["btn_blue_hover"])
                    contribute_btn.update((mx, my))
                    contribute_btn.draw(screen)
                    
                    leave_btn = Button("退出军团", info_panel_x + info_panel_width - 300, info_panel_y + 70, 140, 40, font_small, COLORS["accent_red"], (255, 100, 100))
                    leave_btn.update((mx, my))
                    leave_btn.draw(screen)
                    
                    members_y = content_y + info_panel_height + 20
                    members_title = font_main.render("军团成员:", True, COLORS["accent_gold"])
                    screen.blit(members_title, (info_panel_x, members_y))
                    
                    members_y += 40
                    for member in current_legion["members"][:10]:
                        member_rank = LEGION_RANKS.get(member["rank"], {"name": "未知", "icon": "🎖️"})
                        member_text = f"{member_rank['icon']} {member['name']} - 贡献: {member['contribution']}"
                        member_surf = font_small.render(member_text, True, COLORS["text_white"])
                        screen.blit(member_surf, (info_panel_x + 10, members_y))
                        members_y += 30
                else:
                    empty_text = font_main.render("您尚未加入军团", True, COLORS["text_gray"])
                    screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, content_y))
            
            elif current_tab == "tasks":
                tasks_y = content_y
                for task_id, task in LEGION_TASKS.items():
                    progress = legion_system.get_task_progress(task_id)
                    is_completed = progress >= task["target_count"]
                    
                    task_width = SCREEN_WIDTH * 0.9
                    task_height = 70
                    task_x = (SCREEN_WIDTH - task_width) // 2
                    
                    bg_color = COLORS["panel_bg"]
                    card_surf = pygame.Surface((task_width, task_height), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, bg_color, (0, 0, task_width, task_height), border_radius=10)
                    screen.blit(card_surf, (task_x, tasks_y))
                    
                    if is_completed:
                        pygame.draw.rect(screen, COLORS["accent_gold"], (task_x, tasks_y, task_width, task_height), 2, border_radius=10)
                    
                    icon_font = pygame.font.Font(None, int(35 * scale))
                    icon_surf = icon_font.render(task["icon"], True, COLORS["text_white"])
                    screen.blit(icon_surf, (task_x + 15, tasks_y + 15))
                    
                    name_surf = font_main.render(task["name"], True, COLORS["text_white"])
                    screen.blit(name_surf, (task_x + 60, tasks_y + 10))
                    
                    desc_surf = font_small.render(task["description"], True, COLORS["text_gray"])
                    screen.blit(desc_surf, (task_x + 60, tasks_y + 40))
                    
                    progress_text = f"{progress}/{task['target_count']}"
                    progress_surf = font_small.render(progress_text, True, COLORS["accent_green"] if is_completed else COLORS["text_gray"])
                    screen.blit(progress_surf, (task_x + task_width - 80, tasks_y + 25))
                    
                    if is_completed:
                        claim_btn = Button("领取", task_x + task_width - 70, tasks_y + 15, 60, 35, font_small, COLORS["btn_green"], COLORS["btn_green_hover"])
                        claim_btn.update((mx, my))
                        claim_btn.draw(screen)
                    
                    tasks_y += task_height + 15
            
            elif current_tab == "boss":
                boss_y = content_y
                for boss_id, boss_data in LEGION_BOSSES.items():
                    current_health = data["legion"]["boss_health"].get(boss_id, boss_data["health"])
                    health_percent = current_health / boss_data["health"]
                    
                    boss_width = SCREEN_WIDTH * 0.9
                    boss_height = 100
                    boss_x = (SCREEN_WIDTH - boss_width) // 2
                    
                    bg_color = COLORS["panel_bg"]
                    card_surf = pygame.Surface((boss_width, boss_height), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, bg_color, (0, 0, boss_width, boss_height), border_radius=12)
                    screen.blit(card_surf, (boss_x, boss_y))
                    
                    icon_font = pygame.font.Font(None, int(45 * scale))
                    icon_surf = icon_font.render(boss_data["icon"], True, COLORS["text_white"])
                    screen.blit(icon_surf, (boss_x + 20, boss_y + 25))
                    
                    name_surf = font_main.render(boss_data["name"], True, COLORS["accent_red"])
                    screen.blit(name_surf, (boss_x + 80, boss_y + 15))
                    
                    health_bar_width = boss_width - 200
                    health_bar_height = 20
                    health_bar_x = boss_x + 80
                    health_bar_y = boss_y + 50
                    
                    pygame.draw.rect(screen, COLORS["accent_red"], (health_bar_x, health_bar_y, health_bar_width, health_bar_height), border_radius=5)
                    pygame.draw.rect(screen, COLORS["accent_green"], (health_bar_x, health_bar_y, health_bar_width * health_percent, health_bar_height), border_radius=5)
                    
                    health_text = f"{current_health}/{boss_data['health']}"
                    health_surf = font_small.render(health_text, True, COLORS["text_white"])
                    screen.blit(health_surf, (boss_x + boss_width - 80, boss_y + 50))
                    
                    attack_btn = Button(f"攻击 ({boss_data['attack']}伤害)", boss_x + boss_width - 150, boss_y + 65, 140, 30, font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"])
                    attack_btn.update((mx, my))
                    attack_btn.draw(screen)
                    
                    boss_y += boss_height + 20
            
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
                    
                    if current_tab == "list" and 'join_buttons' in locals():
                        for btn, legion_name in join_buttons:
                            if btn.rect.collidepoint(mx, my):
                                success, msg = legion_system.join_legion(legion_name, player_name)
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                    
                    elif current_tab == "create":
                        create_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, content_y + 100, 200, 50)
                        if create_rect.collidepoint(mx, my):
                            success, msg = legion_system.create_legion(f"{player_name}的军团", player_name)
                            message = msg
                            show_message = True
                            message_timer = 0
                    
                    elif current_tab == "my" and current_legion:
                        info_panel_x = SCREEN_WIDTH * 0.05
                        info_panel_y = content_y
                        info_panel_width = SCREEN_WIDTH * 0.9
                        
                        contribute_rect = pygame.Rect(info_panel_x + info_panel_width - 300, info_panel_y + 20, 280, 40)
                        if contribute_rect.collidepoint(mx, my):
                            success, msg = legion_system.contribute(100)
                            message = msg
                            show_message = True
                            message_timer = 0
                        
                        leave_rect = pygame.Rect(info_panel_x + info_panel_width - 300, info_panel_y + 70, 140, 40)
                        if leave_rect.collidepoint(mx, my):
                            success, msg = legion_system.leave_legion(player_name)
                            message = msg
                            show_message = True
                            message_timer = 0
                    
                    elif current_tab == "tasks":
                        tasks_y = content_y
                        for task_id, task in LEGION_TASKS.items():
                            progress = legion_system.get_task_progress(task_id)
                            is_completed = progress >= task["target_count"]
                            
                            if is_completed:
                                task_width = SCREEN_WIDTH * 0.9
                                task_x = (SCREEN_WIDTH - task_width) // 2
                                claim_rect = pygame.Rect(task_x + task_width - 70, tasks_y + 15, 60, 35)
                                if claim_rect.collidepoint(mx, my):
                                    success, msg = legion_system.claim_task_reward(task_id)
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                    break
                            
                            tasks_y += 85
                    
                    elif current_tab == "boss":
                        boss_y = content_y
                        for boss_id, boss_data in LEGION_BOSSES.items():
                            boss_width = SCREEN_WIDTH * 0.9
                            boss_x = (SCREEN_WIDTH - boss_width) // 2
                            attack_rect = pygame.Rect(boss_x + boss_width - 150, boss_y + 65, 140, 30)
                            if attack_rect.collidepoint(mx, my):
                                success, msg = legion_system.attack_boss(boss_id, boss_data["attack"])
                                message = msg
                                show_message = True
                                message_timer = 0
                                break
                            
                            boss_y += 120
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("军团系统")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("军团系统", str(e))

if __name__ == "__main__":
    main()