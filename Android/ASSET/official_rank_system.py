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
    "rank_bronze": (180, 150, 80),
    "rank_silver": (200, 200, 220),
    "rank_gold": (255, 215, 0),
    "rank_platinum": (100, 200, 255),
    "rank_diamond": (180, 100, 255),
    "rank_mythic": (255, 100, 200)
}

OFFICIAL_RANKS = {
    1: {"name": "平民", "icon": "👨", "color": COLORS["rank_bronze"], "bonus": {}, "required_score": 0, "daily_salary": {}},
    2: {"name": "伍长", "icon": "⚔️", "color": COLORS["rank_bronze"], "bonus": {"attack": 0.03}, "required_score": 100, "daily_salary": {"金元宝": 10}},
    3: {"name": "什长", "icon": "🛡️", "color": COLORS["rank_bronze"], "bonus": {"attack": 0.05, "defense": 0.03}, "required_score": 300, "daily_salary": {"金元宝": 25}},
    4: {"name": "百夫长", "icon": "⭐", "color": COLORS["rank_silver"], "bonus": {"attack": 0.08, "defense": 0.05}, "required_score": 600, "daily_salary": {"金元宝": 50}},
    5: {"name": "千夫长", "icon": "🌟", "color": COLORS["rank_silver"], "bonus": {"attack": 0.12, "defense": 0.08, "health": 0.05}, "required_score": 1000, "daily_salary": {"金元宝": 100}},
    6: {"name": "校尉", "icon": "🎖️", "color": COLORS["rank_silver"], "bonus": {"attack": 0.15, "defense": 0.1, "health": 0.1}, "required_score": 2000, "daily_salary": {"金元宝": 200, "将魂": 50}},
    7: {"name": "中郎将", "icon": "🏅", "color": COLORS["rank_gold"], "bonus": {"attack": 0.2, "defense": 0.15, "health": 0.15}, "required_score": 4000, "daily_salary": {"金元宝": 400, "将魂": 100}},
    8: {"name": "将军", "icon": "⚔️", "color": COLORS["rank_gold"], "bonus": {"attack": 0.25, "defense": 0.2, "health": 0.2}, "required_score": 8000, "daily_salary": {"金元宝": 800, "将魂": 200}},
    9: {"name": "骠骑将军", "icon": "🏆", "color": COLORS["rank_platinum"], "bonus": {"attack": 0.35, "defense": 0.28, "health": 0.25, "speed": 5}, "required_score": 15000, "daily_salary": {"金元宝": 1500, "将魂": 400, "神兵碎片": 10}},
    10: {"name": "大将军", "icon": "👑", "color": COLORS["rank_platinum"], "bonus": {"attack": 0.45, "defense": 0.35, "health": 0.35, "speed": 10}, "required_score": 30000, "daily_salary": {"金元宝": 3000, "将魂": 800, "神兵碎片": 25}},
    11: {"name": "大司马", "icon": "🔮", "color": COLORS["rank_diamond"], "bonus": {"attack": 0.6, "defense": 0.5, "health": 0.5, "speed": 15, "critical": 0.1}, "required_score": 60000, "daily_salary": {"金元宝": 6000, "将魂": 1500, "神晶": 5}},
    12: {"name": "丞相", "icon": "⚖️", "color": COLORS["rank_diamond"], "bonus": {"attack": 0.8, "defense": 0.65, "health": 0.65, "speed": 20, "critical": 0.15}, "required_score": 120000, "daily_salary": {"金元宝": 12000, "将魂": 3000, "神晶": 15}},
    13: {"name": "魏王", "icon": "👑", "color": COLORS["rank_mythic"], "bonus": {"attack": 1.0, "defense": 0.85, "health": 0.85, "speed": 30, "critical": 0.25}, "required_score": 250000, "daily_salary": {"金元宝": 25000, "将魂": 6000, "神晶": 40}},
    14: {"name": "皇帝", "icon": "⭐", "color": COLORS["rank_mythic"], "bonus": {"attack": 1.5, "defense": 1.2, "health": 1.2, "speed": 50, "critical": 0.4}, "required_score": 500000, "daily_salary": {"金元宝": 50000, "将魂": 12000, "神晶": 100}}
}

OFFICIAL_TASKS = {
    "battle_win": {"name": "征战沙场", "description": "赢得10场战斗", "target": 10, "reward": {"score": 100}, "icon": "⚔️", "type": "daily"},
    "hero_recruit": {"name": "招贤纳士", "description": "招募5名武将", "target": 5, "reward": {"score": 150}, "icon": "🎯", "type": "daily"},
    "equip_enhance": {"name": "装备强化", "description": "强化装备8次", "target": 8, "reward": {"score": 120}, "icon": "⚙️", "type": "daily"},
    "resource_collect": {"name": "屯粮积草", "description": "收集500单位资源", "target": 500, "reward": {"score": 80}, "icon": "💰", "type": "daily"},
    "daily_checkin": {"name": "每日签到", "description": "完成每日签到", "target": 1, "reward": {"score": 50}, "icon": "📅", "type": "daily"},
    "boss_kill": {"name": "击杀Boss", "description": "击杀3个Boss", "target": 3, "reward": {"score": 500}, "icon": "🐉", "type": "weekly"},
    "guild_contribute": {"name": "为国效力", "description": "贡献500贡献值", "target": 500, "reward": {"score": 300}, "icon": "🏛️", "type": "weekly"},
    "achievement_unlock": {"name": "功成名就", "description": "解锁5个成就", "target": 5, "reward": {"score": 800}, "icon": "🏆", "type": "weekly"},
    "hero_upgrade": {"name": "武将培养", "description": "升级武将至50级", "target": 1, "reward": {"score": 1000}, "icon": "⭐", "type": "monthly"},
    "rebirth_hero": {"name": "超凡入圣", "description": "完成1次武将转生", "target": 1, "reward": {"score": 2000}, "icon": "🔮", "type": "monthly"}
}

ACHIEVEMENT_BONUSES = {
    "total_battles_100": {"name": "久经沙场", "description": "累计战斗100场", "bonus": {"attack": 0.05}, "icon": "⚔️"},
    "total_battles_500": {"name": "百战百胜", "description": "累计战斗500场", "bonus": {"attack": 0.1}, "icon": "🏆"},
    "total_battles_1000": {"name": "战神", "description": "累计战斗1000场", "bonus": {"attack": 0.15}, "icon": "🌟"},
    "hero_collection_10": {"name": "初聚英才", "description": "拥有10名武将", "bonus": {"defense": 0.05}, "icon": "👥"},
    "hero_collection_50": {"name": "群英荟萃", "description": "拥有50名武将", "bonus": {"defense": 0.1}, "icon": "👑"},
    "hero_collection_100": {"name": "万将归心", "description": "拥有100名武将", "bonus": {"defense": 0.15}, "icon": "⭐"},
    "resource_collected_10000": {"name": "富甲一方", "description": "累计收集10000资源", "bonus": {"health": 0.05}, "icon": "💰"},
    "resource_collected_100000": {"name": "国库充盈", "description": "累计收集100000资源", "bonus": {"health": 0.1}, "icon": "🏛️"},
    "equipment_refined_10": {"name": "匠心独具", "description": "精炼装备10次", "bonus": {"attack": 0.03}, "icon": "⚙️"},
    "equipment_refined_100": {"name": "神匠", "description": "精炼装备100次", "bonus": {"attack": 0.08}, "icon": "🔧"},
    "divine_weapon_forged": {"name": "神兵天降", "description": "锻造第一把神兵", "bonus": {"critical": 0.05}, "icon": "⚔️"},
    "legion_leader": {"name": "一军之主", "description": "创建军团", "bonus": {"leadership": 50}, "icon": "👑"},
    "rebirth_first": {"name": "脱胎换骨", "description": "完成第一次武将转生", "bonus": {"all": 0.05}, "icon": "🔮"},
    "subordinate_recruit_10": {"name": "众星捧月", "description": "招募10名副将", "bonus": {"attack": 0.05}, "icon": "⭐"},
    "formation_master": {"name": "阵法大师", "description": "解锁所有阵法", "bonus": {"defense": 0.1}, "icon": "🌀"}
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

class OfficialRankSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "official_rank" not in data:
            data["official_rank"] = {
                "current_rank": 1,
                "score": 0,
                "tasks_progress": {},
                "achievements": [],
                "last_salary_time": 0
            }
        save()
    
    def get_current_rank(self):
        return data["official_rank"]["current_rank"]
    
    def get_score(self):
        return data["official_rank"]["score"]
    
    def get_rank_info(self, rank):
        return OFFICIAL_RANKS.get(rank, OFFICIAL_RANKS[1])
    
    def add_score(self, amount):
        data["official_rank"]["score"] += amount
        self._update_rank()
        save()
    
    def _update_rank(self):
        score = data["official_rank"]["score"]
        for rank in sorted(OFFICIAL_RANKS.keys(), reverse=True):
            if score >= OFFICIAL_RANKS[rank]["required_score"]:
                if rank > data["official_rank"]["current_rank"]:
                    data["official_rank"]["current_rank"] = rank
                break
    
    def get_total_bonus(self):
        current_rank = self.get_current_rank()
        rank_info = OFFICIAL_RANKS[current_rank]
        bonus = dict(rank_info["bonus"])
        
        for achievement in data["official_rank"]["achievements"]:
            ach_data = ACHIEVEMENT_BONUSES.get(achievement, {})
            ach_bonus = ach_data.get("bonus", {})
            for stat, value in ach_bonus.items():
                if stat == "all":
                    for s in ["attack", "defense", "health", "speed"]:
                        bonus[s] = bonus.get(s, 0) + value
                else:
                    bonus[stat] = bonus.get(stat, 0) + value
        
        return bonus
    
    def get_task_progress(self, task_id):
        return data["official_rank"]["tasks_progress"].get(task_id, 0)
    
    def update_task_progress(self, task_id, amount):
        data["official_rank"]["tasks_progress"][task_id] = data["official_rank"]["tasks_progress"].get(task_id, 0) + amount
    
    def claim_task_reward(self, task_id):
        task = OFFICIAL_TASKS.get(task_id)
        if not task:
            return False, "任务不存在"
        
        progress = self.get_task_progress(task_id)
        if progress < task["target"]:
            return False, "任务未完成"
        
        data["official_rank"]["tasks_progress"][task_id] = 0
        
        if "score" in task["reward"]:
            self.add_score(task["reward"]["score"])
        
        save()
        
        return True, f"领取奖励成功！获得{task['reward']['score']}声望"
    
    def can_claim_salary(self):
        last_time = data["official_rank"]["last_salary_time"]
        current_time = pygame.time.get_ticks()
        return current_time - last_time >= 86400000
    
    def claim_salary(self):
        if not self.can_claim_salary():
            return False, "今日俸禄已领取"
        
        current_rank = self.get_current_rank()
        rank_info = OFFICIAL_RANKS[current_rank]
        salary = rank_info["daily_salary"]
        
        for resource, amount in salary.items():
            data["resources"][resource] = data["resources"].get(resource, 0) + amount
        
        data["official_rank"]["last_salary_time"] = pygame.time.get_ticks()
        save()
        
        return True, f"领取俸禄成功！获得: {', '.join([f'{v}{k}' for k, v in salary.items()])}"
    
    def check_achievements(self):
        new_achievements = []
        
        total_battles = data.get("stats", {}).get("total_battles", 0)
        if total_battles >= 100 and "total_battles_100" not in data["official_rank"]["achievements"]:
            new_achievements.append("total_battles_100")
        if total_battles >= 500 and "total_battles_500" not in data["official_rank"]["achievements"]:
            new_achievements.append("total_battles_500")
        if total_battles >= 1000 and "total_battles_1000" not in data["official_rank"]["achievements"]:
            new_achievements.append("total_battles_1000")
        
        hero_count = len(data.get("hero_management", {}).get("heroes", {}))
        if hero_count >= 10 and "hero_collection_10" not in data["official_rank"]["achievements"]:
            new_achievements.append("hero_collection_10")
        if hero_count >= 50 and "hero_collection_50" not in data["official_rank"]["achievements"]:
            new_achievements.append("hero_collection_50")
        if hero_count >= 100 and "hero_collection_100" not in data["official_rank"]["achievements"]:
            new_achievements.append("hero_collection_100")
        
        for achievement in new_achievements:
            data["official_rank"]["achievements"].append(achievement)
        
        if new_achievements:
            save()
        
        return new_achievements

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

def draw_rank_progress(surface, current_rank, score, x, y, width, height, font_main, font_small):
    rank_info = OFFICIAL_RANKS[current_rank]
    next_rank = OFFICIAL_RANKS.get(current_rank + 1)
    
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, COLORS["panel_bg"], (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, rank_info["color"], (x, y, width, height), 2, border_radius=12)
    
    icon_font = pygame.font.Font(None, 50)
    icon_surf = icon_font.render(rank_info["icon"], True, rank_info["color"])
    surface.blit(icon_surf, (x + 20, y + 10))
    
    name_surf = font_title.render(rank_info["name"], True, rank_info["color"])
    surface.blit(name_surf, (x + 80, y + 10))
    
    if next_rank:
        current_required = OFFICIAL_RANKS[current_rank]["required_score"]
        next_required = next_rank["required_score"]
        progress = (score - current_required) / (next_required - current_required)
        progress = max(0, min(1, progress))
        
        score_text = f"声望: {score} / {next_required}"
        score_surf = font_main.render(score_text, True, COLORS["text_white"])
        surface.blit(score_surf, (x + 20, y + 70))
        
        bar_width = width - 40
        bar_height = 15
        bar_x = x + 20
        bar_y = y + 50
        
        pygame.draw.rect(surface, COLORS["text_gray"], (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        pygame.draw.rect(surface, rank_info["color"], (bar_x, bar_y, bar_width * progress, bar_height), border_radius=5)
        
        next_name_surf = font_small.render(f"下一职位: {next_rank['name']}", True, COLORS["accent_gold"])
        surface.blit(next_name_surf, (x + width - 200, y + 70))
    else:
        max_text = font_main.render("已达到最高职位！", True, COLORS["accent_gold"])
        surface.blit(max_text, (x + width // 2 - max_text.get_width() // 2, y + 50))

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
        pygame.display.set_caption("官职系统")
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
        
        rank_system = OfficialRankSystem()
        
        particles = []
        
        current_tab = "rank"
        tabs = ["rank", "tasks", "achievements", "bonus"]
        tab_names = ["官职晋升", "官职任务", "成就系统", "属性加成"]
        
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
            
            draw_title(screen, "官职系统", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            tab_y = SCREEN_HEIGHT * 0.18
            tab_width = 130
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
            
            if current_tab == "rank":
                current_rank = rank_system.get_current_rank()
                score = rank_system.get_score()
                
                draw_rank_progress(screen, current_rank, score, 
                                 SCREEN_WIDTH * 0.05, content_y, 
                                 SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.25, 
                                 font_main, font_small)
                
                rank_info = OFFICIAL_RANKS[current_rank]
                salary = rank_info["daily_salary"]
                
                salary_y = content_y + SCREEN_HEIGHT * 0.28
                salary_title = font_main.render("每日俸禄:", True, COLORS["accent_gold"])
                screen.blit(salary_title, (SCREEN_WIDTH * 0.05, salary_y))
                
                if salary:
                    salary_text = ", ".join([f"{v}{k}" for k, v in salary.items()])
                    salary_surf = font_main.render(salary_text, True, COLORS["text_white"])
                    screen.blit(salary_surf, (SCREEN_WIDTH * 0.2, salary_y))
                    
                    can_claim = rank_system.can_claim_salary()
                    claim_btn = Button("领取俸禄", SCREEN_WIDTH - 200, salary_y - 5, 150, 40, font_small, 
                                       COLORS["btn_gold"] if can_claim else COLORS["accent_red"], 
                                       COLORS["btn_gold_hover"] if can_claim else (200, 80, 80))
                    claim_btn.update((mx, my))
                    claim_btn.draw(screen)
                else:
                    no_salary_text = font_small.render("暂无俸禄", True, COLORS["text_gray"])
                    screen.blit(no_salary_text, (SCREEN_WIDTH * 0.2, salary_y))
                
                ranks_y = salary_y + 50
                ranks_title = font_main.render("官职列表:", True, COLORS["accent_gold"])
                screen.blit(ranks_title, (SCREEN_WIDTH * 0.05, ranks_y))
                
                ranks_y += 35
                for rank in sorted(OFFICIAL_RANKS.keys())[:8]:
                    info = OFFICIAL_RANKS[rank]
                    is_current = rank == current_rank
                    is_unlocked = score >= info["required_score"]
                    
                    row_height = 40
                    row_x = SCREEN_WIDTH * 0.05
                    
                    bg_color = info["color"] if is_current else COLORS["panel_bg"]
                    card_surf = pygame.Surface((SCREEN_WIDTH * 0.9, row_height), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, bg_color, (0, 0, SCREEN_WIDTH * 0.9, row_height), border_radius=5)
                    surface.blit(card_surf, (row_x, ranks_y))
                    
                    if is_current:
                        pygame.draw.rect(screen, COLORS["accent_gold"], (row_x, ranks_y, SCREEN_WIDTH * 0.9, row_height), 2, border_radius=5)
                    
                    icon_font = pygame.font.Font(None, int(25 * scale))
                    icon_surf = icon_font.render(info["icon"], True, info["color"])
                    screen.blit(icon_surf, (row_x + 10, ranks_y + 5))
                    
                    name_surf = font_small.render(info["name"], True, info["color"] if is_unlocked else COLORS["text_gray"])
                    screen.blit(name_surf, (row_x + 40, ranks_y + 5))
                    
                    req_text = f"声望: {info['required_score']}"
                    req_surf = font_small.render(req_text, True, COLORS["text_gray"])
                    screen.blit(req_surf, (SCREEN_WIDTH - 200, ranks_y + 5))
                    
                    ranks_y += row_height + 5
            
            elif current_tab == "tasks":
                tasks_y = content_y
                for task_id, task in OFFICIAL_TASKS.items():
                    progress = rank_system.get_task_progress(task_id)
                    is_completed = progress >= task["target"]
                    
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
                    
                    progress_text = f"{progress}/{task['target']}"
                    progress_surf = font_small.render(progress_text, True, COLORS["accent_green"] if is_completed else COLORS["text_gray"])
                    screen.blit(progress_surf, (task_x + task_width - 80, tasks_y + 25))
                    
                    if is_completed:
                        claim_btn = Button("领取", task_x + task_width - 70, tasks_y + 15, 60, 35, font_small, COLORS["btn_green"], COLORS["btn_green_hover"])
                        claim_btn.update((mx, my))
                        claim_btn.draw(screen)
                    
                    tasks_y += task_height + 15
            
            elif current_tab == "achievements":
                achievements = data["official_rank"].get("achievements", [])
                
                ach_y = content_y
                for ach_id, ach_data in ACHIEVEMENT_BONUSES.items():
                    is_unlocked = ach_id in achievements
                    
                    ach_width = SCREEN_WIDTH * 0.9
                    ach_height = 60
                    ach_x = (SCREEN_WIDTH - ach_width) // 2
                    
                    bg_color = COLORS["panel_bg"]
                    card_surf = pygame.Surface((ach_width, ach_height), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, bg_color, (0, 0, ach_width, ach_height), border_radius=10)
                    screen.blit(card_surf, (ach_x, ach_y))
                    
                    if is_unlocked:
                        pygame.draw.rect(screen, COLORS["accent_gold"], (ach_x, ach_y, ach_width, ach_height), 2, border_radius=10)
                    
                    icon_font = pygame.font.Font(None, int(30 * scale))
                    icon_color = COLORS["accent_gold"] if is_unlocked else COLORS["text_gray"]
                    icon_surf = icon_font.render(ach_data["icon"], True, icon_color)
                    screen.blit(icon_surf, (ach_x + 15, ach_y + 10))
                    
                    name_surf = font_main.render(ach_data["name"], True, icon_color)
                    screen.blit(name_surf, (ach_x + 55, ach_y + 10))
                    
                    desc_surf = font_small.render(ach_data["description"], True, COLORS["text_gray"])
                    screen.blit(desc_surf, (ach_x + 55, ach_y + 35))
                    
                    bonus_text = ""
                    for stat, value in ach_data.get("bonus", {}).items():
                        if stat == "all":
                            bonus_text += "全属性+"
                        elif stat == "attack":
                            bonus_text += "攻击+"
                        elif stat == "defense":
                            bonus_text += "防御+"
                        elif stat == "health":
                            bonus_text += "生命+"
                        elif stat == "speed":
                            bonus_text += "速度+"
                        elif stat == "critical":
                            bonus_text += "暴击+"
                        elif stat == "leadership":
                            bonus_text += "统帅+"
                        bonus_text += f"{int(value*100)}% "
                    
                    bonus_surf = font_small.render(bonus_text, True, COLORS["accent_green"] if is_unlocked else COLORS["text_gray"])
                    screen.blit(bonus_surf, (ach_x + ach_width - 200, ach_y + 20))
                    
                    ach_y += ach_height + 10
            
            elif current_tab == "bonus":
                bonus = rank_system.get_total_bonus()
                
                bonus_y = content_y
                title_surf = font_main.render("当前总属性加成:", True, COLORS["accent_gold"])
                screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, bonus_y))
                
                bonus_y += 50
                for stat, value in bonus.items():
                    stat_names = {"attack": "攻击力", "defense": "防御力", "health": "生命值", "speed": "速度", "critical": "暴击率", "leadership": "统帅"}
                    stat_name = stat_names.get(stat, stat)
                    value_text = f"+{int(value*100)}%" if isinstance(value, float) and value < 1 else f"+{int(value)}"
                    
                    bonus_width = SCREEN_WIDTH * 0.8
                    bonus_height = 50
                    bonus_x = (SCREEN_WIDTH - bonus_width) // 2
                    
                    bg_color = COLORS["panel_bg"]
                    card_surf = pygame.Surface((bonus_width, bonus_height), pygame.SRCALPHA)
                    pygame.draw.rect(card_surf, bg_color, (0, 0, bonus_width, bonus_height), border_radius=8)
                    screen.blit(card_surf, (bonus_x, bonus_y))
                    
                    stat_surf = font_main.render(f"{stat_name}:", True, COLORS["text_white"])
                    screen.blit(stat_surf, (bonus_x + 20, bonus_y + 10))
                    
                    value_surf = font_main.render(value_text, True, COLORS["accent_green"])
                    screen.blit(value_surf, (bonus_x + bonus_width - 100, bonus_y + 10))
                    
                    bonus_y += bonus_height + 10
            
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
                    
                    if current_tab == "rank":
                        can_claim = rank_system.can_claim_salary()
                        if can_claim:
                            claim_rect = pygame.Rect(SCREEN_WIDTH - 200, content_y + SCREEN_HEIGHT * 0.28 - 5, 150, 40)
                            if claim_rect.collidepoint(mx, my):
                                success, msg = rank_system.claim_salary()
                                message = msg
                                show_message = True
                                message_timer = 0
                    
                    elif current_tab == "tasks":
                        tasks_y = content_y
                        for task_id, task in OFFICIAL_TASKS.items():
                            progress = rank_system.get_task_progress(task_id)
                            is_completed = progress >= task["target"]
                            
                            if is_completed:
                                task_width = SCREEN_WIDTH * 0.9
                                task_x = (SCREEN_WIDTH - task_width) // 2
                                claim_rect = pygame.Rect(task_x + task_width - 70, tasks_y + 15, 60, 35)
                                if claim_rect.collidepoint(mx, my):
                                    success, msg = rank_system.claim_task_reward(task_id)
                                    message = msg
                                    show_message = True
                                    message_timer = 0
                                    break
                            
                            tasks_y += 85
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("官职系统")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("官职系统", str(e))

if __name__ == "__main__":
    main()