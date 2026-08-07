import os
import pygame
import random
import math
import time
import datetime
from ASSET.game_data import data, save, get_system_font_name, load_sound
from ASSET import safe_exit
from ASSET import snake_game, push_box, breakout, minesweeper, game_2048, tetris, gobang

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
        self.particles = []
    
    def update(self, mouse_pos):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered and not was_hovered:
            for _ in range(3):
                self.particles.append(Particle(
                    random.randint(self.rect.x, self.rect.x + self.rect.width),
                    self.rect.y + self.rect.height,
                    COLORS["accent_gold"],
                    2, random.randint(2, 4), 20
                ))
        
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
    
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
        
        for p in self.particles:
            p.draw(surface)

class EventCenter:
    def __init__(self):
        self._init_data()
        self.mini_games = self._load_mini_games()
        self.limited_events = self._load_limited_events()
        self.seasonal_events = self._load_seasonal_events()
        self.update_event_status()
    
    def _init_data(self):
        if "event_center" not in data:
            data["event_center"] = {
                "mini_games_played": {},
                "limited_events": {
                    "active": [],
                    "completed": [],
                    "last_updated": datetime.datetime.now().isoformat()
                },
                "seasonal_events": {
                    "active": [],
                    "completed": [],
                    "claimed_rewards": []
                },
                "daily_bonus_claimed": False,
                "weekly_bonus_claimed": False,
                "battle_pass": {
                    "level": 1,
                    "xp": 0,
                    "claimed_rewards": []
                }
            }
            save()
    
    def _load_mini_games(self):
        return [
            {"id": "snake", "name": "🐍 贪吃蛇", "func": snake_game.main, "reward": {"金元宝": 20}, "icon": "🐍"},
            {"id": "push_box", "name": "📦 推箱子", "func": push_box.main, "reward": {"金元宝": 30}, "icon": "📦"},
            {"id": "breakout", "name": "🎯 打砖块", "func": breakout.main, "reward": {"金元宝": 25}, "icon": "🎯"},
            {"id": "minesweeper", "name": "💣 扫雷", "func": minesweeper.main, "reward": {"金元宝": 35}, "icon": "💣"},
            {"id": "game_2048", "name": "🔢 2048", "func": game_2048.main, "reward": {"金元宝": 20}, "icon": "🔢"},
            {"id": "tetris", "name": "🧱 俄罗斯方块", "func": tetris.main, "reward": {"金元宝": 25}, "icon": "🧱"},
            {"id": "gobang", "name": "⚫ 五子棋", "func": gobang.main, "reward": {"金元宝": 40}, "icon": "⚫"}
        ]
    
    def _load_limited_events(self):
        return [
            {
                "id": "event_spring_festival",
                "name": "春节限时活动",
                "description": "完成10次战斗，获得春节限定奖励",
                "duration": 7 * 24 * 60 * 60,
                "objective": {"type": "battle_completed", "count": 10},
                "rewards": {"金元宝": 300, "春节限定皮肤": 1, "红包": 5},
                "icon": "🧧",
                "color": COLORS["accent_red"]
            },
            {
                "id": "event_valentine",
                "name": "情人节限时活动",
                "description": "收集99朵玫瑰，获得情人节限定时装",
                "duration": 3 * 24 * 60 * 60,
                "objective": {"type": "collect_rose", "count": 99},
                "rewards": {"金元宝": 200, "情人节时装": 1, "玫瑰": 99},
                "icon": "🌹",
                "color": COLORS["accent_red"]
            },
            {
                "id": "event_summer_festival",
                "name": "夏季庆典活动",
                "description": "完成5次小游戏，获得夏季限定坐骑",
                "duration": 5 * 24 * 60 * 60,
                "objective": {"type": "mini_game_played", "count": 5},
                "rewards": {"金元宝": 250, "夏季限定坐骑": 1, "西瓜": 100},
                "icon": "🍉",
                "color": COLORS["accent_green"]
            },
            {
                "id": "event_anniversary",
                "name": "周年庆典活动",
                "description": "完成20次任务，获得周年限定武将",
                "duration": 10 * 24 * 60 * 60,
                "objective": {"type": "quest_completed", "count": 20},
                "rewards": {"金元宝": 500, "周年限定武将": 1, "传说装备": 1},
                "icon": "🎂",
                "color": COLORS["accent_gold"]
            },
            {
                "id": "event_halloween",
                "name": "万圣节活动",
                "description": "收集50个南瓜灯，获得万圣节限定皮肤",
                "duration": 3 * 24 * 60 * 60,
                "objective": {"type": "collect_pumpkin", "count": 50},
                "rewards": {"金元宝": 200, "万圣节皮肤": 1, "南瓜灯": 50},
                "icon": "🎃",
                "color": COLORS["accent_orange"]
            },
            {
                "id": "event_mid_autumn",
                "name": "中秋节活动",
                "description": "完成8次战斗，获得中秋限定奖励",
                "duration": 5 * 24 * 60 * 60,
                "objective": {"type": "battle_completed", "count": 8},
                "rewards": {"金元宝": 280, "月饼": 50, "中秋限定头像": 1},
                "icon": "🥮",
                "color": COLORS["accent_orange"]
            }
        ]
    
    def _load_seasonal_events(self):
        return [
            {"id": "daily_login", "name": "每日登录", "description": "每日登录游戏领取奖励", "icon": "🎁", "rewards": {"金元宝": 100, "经验": 200}, "type": "daily"},
            {"id": "first_recharge", "name": "首充大礼", "description": "首次充值获得双倍奖励", "icon": "💰", "rewards": {"金元宝": 500, "传说武将碎片": 50}, "type": "limited"},
            {"id": "weekend_bonus", "name": "周末狂欢", "description": "周末登录领取双倍奖励", "icon": "🎉", "rewards": {"金元宝": 300, "高级招募令": 1}, "type": "weekend"},
            {"id": "consume_reward", "name": "消费返利", "description": "累计消费金元宝返利", "icon": "🛒", "rewards": {"金元宝": 200, "稀有武将碎片": 30}, "type": "consume"},
            {"id": "battle_pass", "name": "战斗通行证", "description": "完成赛季任务获得奖励", "icon": "⚔️", "rewards": {"金元宝": 1000, "顶级招募令": 2}, "type": "season"},
            {"id": "new_server", "name": "新手特惠", "description": "新服务器专属福利", "icon": "🌟", "rewards": {"金元宝": 800, "传说武将": 1}, "type": "newbie"}
        ]
    
    def update_event_status(self):
        current_time = datetime.datetime.now()
        
        active_events = data["event_center"]["limited_events"]["active"].copy()
        for event in active_events:
            if "end_time" in event:
                end_time = datetime.datetime.fromisoformat(event["end_time"])
                if current_time > end_time:
                    event["status"] = "expired"
                    data["event_center"]["limited_events"]["completed"].append(event)
                    data["event_center"]["limited_events"]["active"].remove(event)
        
        if not data["event_center"]["limited_events"]["active"]:
            available_events = [e for e in self.limited_events if not any(ce["id"] == e["id"] for ce in data["event_center"]["limited_events"]["completed"])]
            if available_events:
                event = random.choice(available_events).copy()
                event["start_time"] = datetime.datetime.now().isoformat()
                event["end_time"] = (datetime.datetime.now() + datetime.timedelta(seconds=event["duration"])).isoformat()
                event["status"] = "active"
                event["progress"] = 0
                data["event_center"]["limited_events"]["active"].append(event)
        
        data["event_center"]["limited_events"]["last_updated"] = datetime.datetime.now().isoformat()
        
        today = time.strftime("%Y-%m-%d")
        weekday = time.strftime("%w")
        
        data["event_center"]["seasonal_events"]["active"] = []
        for event in self.seasonal_events:
            if event["type"] == "daily":
                data["event_center"]["seasonal_events"]["active"].append(event)
            elif event["type"] == "weekend" and weekday in ["0", "6"]:
                data["event_center"]["seasonal_events"]["active"].append(event)
            elif event["type"] == "season":
                data["event_center"]["seasonal_events"]["active"].append(event)
        
        save()
    
    def play_mini_game(self, game_id):
        game = next((g for g in self.mini_games if g["id"] == game_id), None)
        if game:
            if game_id not in data["event_center"]["mini_games_played"]:
                data["event_center"]["mini_games_played"][game_id] = 0
            data["event_center"]["mini_games_played"][game_id] += 1
            
            for resource, amount in game["reward"].items():
                if resource in data["resources"]:
                    data["resources"][resource] = data["resources"].get(resource, 0) + amount
            
            self.update_event_progress("mini_game_played", count=1)
            save()
            
            return True, game["reward"]
        return False, None
    
    def update_event_progress(self, event_type, **kwargs):
        for event in data["event_center"]["limited_events"]["active"]:
            if event.get("status") == "active":
                if event["objective"]["type"] == event_type:
                    event["progress"] = event.get("progress", 0) + kwargs.get("count", 1)
                    
                    if event["progress"] >= event["objective"]["count"]:
                        event["status"] = "completed"
                        self.claim_event_reward(event)
        
        self.update_event_status()
        save()
    
    def claim_event_reward(self, event):
        for reward, amount in event["rewards"].items():
            if reward in data["resources"]:
                data["resources"][reward] = data["resources"].get(reward, 0) + amount
        
        if event in data["event_center"]["limited_events"]["active"]:
            data["event_center"]["limited_events"]["completed"].append(event)
            data["event_center"]["limited_events"]["active"].remove(event)
        save()
    
    def get_active_limited_events(self):
        self.update_event_status()
        return data["event_center"]["limited_events"]["active"]
    
    def get_completed_limited_events(self):
        return data["event_center"]["limited_events"]["completed"]
    
    def get_active_seasonal_events(self):
        return data["event_center"]["seasonal_events"]["active"]
    
    def claim_seasonal_reward(self, event_id):
        event = next((e for e in self.seasonal_events if e["id"] == event_id), None)
        if not event:
            return False, "活动不存在"
        
        claimed_id = f"seasonal_{event_id}"
        if claimed_id in data["event_center"]["seasonal_events"]["claimed_rewards"]:
            return False, "奖励已领取"
        
        for reward, amount in event["rewards"].items():
            if reward in data["resources"]:
                data["resources"][reward] = data["resources"].get(reward, 0) + amount
        
        data["event_center"]["seasonal_events"]["claimed_rewards"].append(claimed_id)
        save()
        
        return True, event["rewards"]

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
    
    line_y = y + 40
    pygame.draw.line(surface, COLORS["accent_gold"], 
                    (screen_width // 2 - 150, line_y),
                    (screen_width // 2 - 50, line_y), 3)
    pygame.draw.line(surface, COLORS["accent_gold"],
                    (screen_width // 2 + 50, line_y),
                    (screen_width // 2 + 150, line_y), 3)
    pygame.draw.circle(surface, COLORS["accent_gold"], (screen_width // 2, line_y), 8)
    pygame.draw.circle(surface, COLORS["bg_dark"], (screen_width // 2, line_y), 5)

def draw_countdown(surface, end_time, x, y, font_main):
    end_datetime = datetime.datetime.fromisoformat(end_time)
    current_time = datetime.datetime.now()
    time_left = end_datetime - current_time
    
    if time_left.total_seconds() > 0:
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            countdown_text = f"剩余: {days}天 {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            countdown_text = f"剩余: {hours:02d}:{minutes:02d}:{seconds:02d}"
        
        text_surf = font_main.render(countdown_text, True, COLORS["accent_red"])
        surface.blit(text_surf, (x, y))
    else:
        text_surf = font_main.render("活动已结束", True, COLORS["text_gray"])
        surface.blit(text_surf, (x, y))

def draw_event_card(surface, event, y_offset, screen_width, font_main, font_small):
    card_rect = pygame.Rect(50, y_offset, screen_width - 100, 130)
    
    if event.get("status") == "completed":
        bg_color = (40, 70, 40, 200)
    elif event.get("status") == "active":
        bg_color = (40, 40, 70, 200)
    else:
        bg_color = (70, 40, 40, 200)
    
    pygame.draw.rect(surface, bg_color, card_rect, border_radius=12)
    pygame.draw.rect(surface, COLORS["accent_gold"], card_rect, 2, border_radius=12)
    
    icon_text = font_main.render(event.get("icon", "🎮"), True, COLORS["accent_gold"])
    screen.blit(icon_text, (65, y_offset + 15))
    
    name_surf = font_main.render(event["name"], True, COLORS["accent_gold"])
    screen.blit(name_surf, (110, y_offset + 15))
    
    desc_surf = font_small.render(event["description"], True, COLORS["text_white"])
    screen.blit(desc_surf, (110, y_offset + 45))
    
    if "progress" in event:
        progress_surf = font_small.render(f"进度: {event['progress']}/{event['objective']['count']}", True, COLORS["text_gray"])
        screen.blit(progress_surf, (110, y_offset + 75))
        
        progress_bar = pygame.Rect(110, y_offset + 95, 250, 15)
        pygame.draw.rect(surface, (50, 50, 70), progress_bar, border_radius=8)
        
        progress_ratio = min(1, event["progress"] / event["objective"]["count"])
        progress_fill = pygame.Rect(110, y_offset + 95, int(250 * progress_ratio), 15)
        pygame.draw.rect(surface, COLORS["accent_green"], progress_fill, border_radius=8)
    
    rewards_text = "奖励: " + ", ".join([f"{k}×{v}" for k, v in event["rewards"].items()])
    rewards_surf = font_small.render(rewards_text, True, (255, 210, 0))
    screen.blit(rewards_surf, (screen_width // 2 + 50, y_offset + 35))
    
    if "end_time" in event and event.get("status") == "active":
        draw_countdown(surface, event["end_time"], screen_width // 2 + 50, y_offset + 65, font_small)
    
    if event.get("status") == "completed":
        claim_btn = Button("领取奖励", screen_width - 150, y_offset + 40, 120, 50, font_small, COLORS["btn_green"])
        claim_btn.draw(surface)
        return claim_btn
    
    return None

def draw_seasonal_event(surface, event, y_offset, screen_width, font_main, font_small):
    card_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
    pygame.draw.rect(surface, COLORS["panel_bg"], card_rect, border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_gold"], card_rect, 2, border_radius=10)
    
    icon_text = font_main.render(event["icon"], True, COLORS["accent_gold"])
    screen.blit(icon_text, (65, y_offset + 25))
    
    name_surf = font_main.render(event["name"], True, COLORS["text_white"])
    screen.blit(name_surf, (110, y_offset + 15))
    
    desc_surf = font_small.render(event["description"], True, COLORS["text_gray"])
    screen.blit(desc_surf, (110, y_offset + 45))
    
    rewards_text = ", ".join([f"{k}×{v}" for k, v in event["rewards"].items()])
    rewards_surf = font_small.render(rewards_text, True, (255, 210, 0))
    screen.blit(rewards_surf, (screen_width // 2 + 50, y_offset + 30))
    
    claimed_id = f"seasonal_{event['id']}"
    if claimed_id in data["event_center"]["seasonal_events"]["claimed_rewards"]:
        claimed_text = font_small.render("已领取", True, COLORS["accent_green"])
        screen.blit(claimed_text, (screen_width - 100, y_offset + 30))
        return None
    else:
        claim_btn = Button("领取", screen_width - 150, y_offset + 20, 100, 40, font_small, COLORS["btn_green"])
        claim_btn.draw(surface)
        return claim_btn

def main():
    try:
        if not pygame.get_init():
            pygame.init()
            pygame.mixer.init()
        
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
                SCREEN_WIDTH = 1024
                SCREEN_HEIGHT = 768
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("活动中心")
        clock = pygame.time.Clock()
        
        scale = min(SCREEN_WIDTH / 1024, SCREEN_HEIGHT / 768)
        
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
        
        event_center = EventCenter()
        
        particles = []
        
        current_tab = "limited"
        tabs = ["limited", "seasonal", "mini_games"]
        tab_names = ["限时活动", "日常活动", "小游戏"]
        
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
            
            draw_title(screen, "活动中心", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            tab_y = SCREEN_HEIGHT * 0.18
            tab_width = 150
            tab_height = 45
            tab_start_x = (SCREEN_WIDTH - len(tabs) * (tab_width + 20)) // 2
            
            tab_buttons = []
            for i, (tab_id, tab_name) in enumerate(zip(tabs, tab_names)):
                x = tab_start_x + i * (tab_width + 20)
                is_selected = current_tab == tab_id
                btn_color = COLORS["btn_gold"] if is_selected else COLORS["btn_blue"]
                hover_color = COLORS["btn_gold_hover"] if is_selected else COLORS["btn_blue_hover"]
                btn = Button(tab_name, x, tab_y, tab_width, tab_height, font_main, btn_color, hover_color)
                btn.update((mx, my))
                btn.draw(screen)
                tab_buttons.append((btn, tab_id))
            
            content_y = SCREEN_HEIGHT * 0.26
            
            if current_tab == "limited":
                active_events = event_center.get_active_limited_events()
                completed_events = event_center.get_completed_limited_events()
                
                if active_events:
                    active_title = font_main.render("🎯 进行中的活动", True, COLORS["accent_gold"])
                    screen.blit(active_title, (50, content_y))
                    content_y += 40
                    
                    claim_buttons = []
                    for event in active_events:
                        claim_btn = draw_event_card(screen, event, content_y, SCREEN_WIDTH, font_main, font_small)
                        if claim_btn:
                            claim_buttons.append((claim_btn, event))
                        content_y += 140
                
                if completed_events:
                    content_y += 20
                    completed_title = font_main.render("🏆 已结束的活动", True, COLORS["text_gray"])
                    screen.blit(completed_title, (50, content_y))
                    content_y += 40
                    
                    for event in completed_events[-3:]:
                        draw_event_card(screen, event, content_y, SCREEN_WIDTH, font_main, font_small)
                        content_y += 140
            
            elif current_tab == "seasonal":
                seasonal_events = event_center.get_active_seasonal_events()
                
                if seasonal_events:
                    seasonal_title = font_main.render("🎁 日常活动", True, COLORS["accent_gold"])
                    screen.blit(seasonal_title, (50, content_y))
                    content_y += 40
                    
                    claim_buttons = []
                    for event in seasonal_events:
                        claim_btn = draw_seasonal_event(screen, event, content_y, SCREEN_WIDTH, font_main, font_small)
                        if claim_btn:
                            claim_buttons.append((claim_btn, event))
                        content_y += 90
            
            elif current_tab == "mini_games":
                mini_title = font_main.render("🎮 小游戏中心", True, COLORS["accent_gold"])
                screen.blit(mini_title, (50, content_y))
                content_y += 40
                
                btn_width = min(150, SCREEN_WIDTH * 0.18)
                btn_height = min(80, SCREEN_HEIGHT * 0.1)
                btn_spacing = 20
                
                cols = min(3, SCREEN_WIDTH // (btn_width + btn_spacing))
                start_x = (SCREEN_WIDTH - (cols * btn_width + (cols - 1) * btn_spacing)) // 2
                
                game_buttons = []
                for i, game in enumerate(event_center.mini_games):
                    row = i // cols
                    col = i % cols
                    x = start_x + col * (btn_width + btn_spacing)
                    y = content_y + row * (btn_height + btn_spacing)
                    
                    game_btn = Button(f"{game['icon']} {game['name']}", x, y, btn_width, btn_height, font_main)
                    game_btn.update((mx, my))
                    game_btn.draw(screen)
                    
                    reward_text = font_small.render(f"奖励: {game['reward']['金元宝']}金元宝", True, COLORS["accent_gold"])
                    reward_rect = reward_text.get_rect(center=(x + btn_width // 2, y + btn_height + 20))
                    screen.blit(reward_text, reward_rect)
                    
                    game_buttons.append((game_btn, game))
            
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
                    
                    if current_tab == "limited":
                        if 'claim_buttons' in locals():
                            for claim_btn, event_data in claim_buttons:
                                if claim_btn.rect.collidepoint(mx, my):
                                    event_center.claim_event_reward(event_data)
                                    message = f"奖励已领取！"
                                    show_message = True
                                    message_timer = 0
                    
                    elif current_tab == "seasonal":
                        if 'claim_buttons' in locals():
                            for claim_btn, event_data in claim_buttons:
                                if claim_btn.rect.collidepoint(mx, my):
                                    success, msg = event_center.claim_seasonal_reward(event_data["id"])
                                    if success:
                                        reward_str = ", ".join([f"{k}×{v}" for k, v in msg.items()])
                                        message = f"领取成功！获得：{reward_str}"
                                    else:
                                        message = msg
                                    show_message = True
                                    message_timer = 0
                    
                    elif current_tab == "mini_games":
                        for game_btn, game in game_buttons:
                            if game_btn.rect.collidepoint(mx, my):
                                game["func"]()
                                success, reward = event_center.play_mini_game(game["id"])
                                if success:
                                    message = f"完成游戏！获得 {reward['金元宝']} 金元宝"
                                    show_message = True
                                    message_timer = 0
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("活动中心")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("活动中心", str(e))

if __name__ == "__main__":
    main()