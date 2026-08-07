import os
import pygame
import random
import math
import time
from datetime import datetime, timedelta
from ASSET.game_data import data, save, get_system_font_name, load_sound
from ASSET import safe_exit

COLORS = {
    "bg_dark": (15, 20, 35),
    "bg_light": (25, 30, 50),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 220),
    "accent_green": (60, 200, 100),
    "accent_purple": (180, 100, 220),
    "accent_red": (220, 80, 80),
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
        self.angle = random.uniform(0, 2 * math.pi)
        self.rotation_speed = random.uniform(-0.1, 0.1)
        self.glow_radius = size * 2
    
    def update(self):
        self.speed_y += self.gravity
        self.x += self.speed_x
        self.y += self.speed_y
        self.angle += self.rotation_speed
        self.life -= 1
        self.size = max(0.5, self.size - 0.05)
        self.glow_radius = max(0, self.glow_radius - 0.1)
    
    def draw(self, surface):
        if self.glow_radius > 0:
            glow_surf = pygame.Surface((self.glow_radius * 2, self.glow_radius * 2), pygame.SRCALPHA)
            alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
            glow_color = (*self.color[:3], alpha // 4)
            pygame.draw.circle(glow_surf, glow_color, (int(self.glow_radius), int(self.glow_radius)), int(self.glow_radius))
            surface.blit(glow_surf, (int(self.x - self.glow_radius), int(self.y - self.glow_radius)))
        
        alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
        color = (*self.color[:3], alpha)
        particle_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, color, (int(self.size), int(self.size)), int(self.size))
        rotated_surf = pygame.transform.rotate(particle_surf, math.degrees(self.angle))
        rotated_rect = rotated_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_surf, rotated_rect)

class FloatingText:
    def __init__(self, text, x, y, color, font):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.life = 50
        self.max_life = 50
        self.speed_y = -1.5
        self.scale = 1.0
    
    def update(self):
        self.y += self.speed_y
        self.life -= 1
        if self.life > 40:
            self.scale = min(1.3, self.scale + 0.03)
        else:
            self.scale = max(1.0, self.scale - 0.02)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
        text_surf = self.font.render(self.text, True, self.color)
        scaled_size = (int(text_surf.get_width() * self.scale), int(text_surf.get_height() * self.scale))
        scaled_surf = pygame.transform.scale(text_surf, scaled_size)
        scaled_surf.set_alpha(alpha)
        rect = scaled_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(scaled_surf, rect)

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

class CheckinCard:
    def __init__(self, day, reward, bonus, is_checked, is_today, x, y, width, height, font):
        self.day = day
        self.reward = reward
        self.bonus = bonus
        self.is_checked = is_checked
        self.is_today = is_today
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.particles = []
    
    def draw(self, surface):
        if self.is_checked:
            bg_color = (60, 180, 100, 200)
        elif self.is_today:
            bg_color = (255, 215, 0, 200)
        else:
            bg_color = (35, 40, 60, 200)
        
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=12)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 2, border_radius=12)
        
        if self.is_today:
            day_text = self.font.render(f"第{self.day}天", True, (30, 30, 60))
        else:
            day_text = self.font.render(f"第{self.day}天", True, COLORS["text_white"])
        day_rect = day_text.get_rect(center=(self.rect.x + self.rect.width // 2, self.rect.y + 25))
        surface.blit(day_text, day_rect)
        
        reward_str = "+".join([f"{k}×{v}" for k, v in self.reward.items()])
        if self.bonus:
            reward_str += f"\n★{self.bonus['item']}×{self.bonus['count']}"
        
        if self.is_today:
            reward_text = self.font.render(reward_str, True, (30, 30, 60))
        else:
            reward_text = self.font.render(reward_str, True, COLORS["accent_gold"])
        reward_rect = reward_text.get_rect(center=(self.rect.x + self.rect.width // 2, self.rect.y + 55))
        surface.blit(reward_text, reward_rect)
        
        if self.is_checked:
            check_text = self.font.render("✓", True, COLORS["text_white"])
            check_rect = check_text.get_rect(center=(self.rect.x + self.rect.width - 20, self.rect.y + 20))
            surface.blit(check_text, check_rect)
        elif self.is_today:
            today_text = self.font.render("今天", True, (30, 30, 60))
            today_rect = today_text.get_rect(center=(self.rect.x + self.rect.width - 25, self.rect.y + 20))
            surface.blit(today_text, today_rect)

class CheckinCenter:
    def __init__(self):
        self._init_data()
        self.rewards = self._load_rewards()
        self.streak_rewards = self._load_streak_rewards()
    
    def _init_data(self):
        if "checkin_center" not in data:
            data["checkin_center"] = {
                "last_checkin_date": "",
                "consecutive_days": 0,
                "monthly_checkins": 0,
                "total_checkins": 0,
                "current_month": int(time.strftime("%Y%m")),
                "claimed_rewards": [],
                "claimed_streak_rewards": [],
                "checkins": {}
            }
            save()
    
    def _load_rewards(self):
        return [
            {"day": 1, "rewards": {"金元宝": 50, "经验": 100}, "bonus": None},
            {"day": 2, "rewards": {"金元宝": 60, "经验": 150}, "bonus": None},
            {"day": 3, "rewards": {"金元宝": 70, "经验": 200}, "bonus": None},
            {"day": 4, "rewards": {"金元宝": 80, "经验": 250}, "bonus": None},
            {"day": 5, "rewards": {"金元宝": 100, "经验": 300}, "bonus": {"item": "中级经验丹", "count": 1}},
            {"day": 6, "rewards": {"金元宝": 120, "经验": 350}, "bonus": None},
            {"day": 7, "rewards": {"金元宝": 200, "经验": 500}, "bonus": {"item": "高级招募令", "count": 1}},
            {"day": 8, "rewards": {"金元宝": 100, "经验": 200}, "bonus": None},
            {"day": 9, "rewards": {"金元宝": 110, "经验": 250}, "bonus": None},
            {"day": 10, "rewards": {"金元宝": 120, "经验": 300}, "bonus": {"item": "中级经验丹", "count": 2}},
            {"day": 11, "rewards": {"金元宝": 130, "经验": 350}, "bonus": None},
            {"day": 12, "rewards": {"金元宝": 140, "经验": 400}, "bonus": None},
            {"day": 13, "rewards": {"金元宝": 150, "经验": 450}, "bonus": None},
            {"day": 14, "rewards": {"金元宝": 300, "经验": 600}, "bonus": {"item": "顶级招募令", "count": 1}},
            {"day": 15, "rewards": {"金元宝": 150, "经验": 300}, "bonus": {"item": "装备精炼石", "count": 5}},
            {"day": 16, "rewards": {"金元宝": 160, "经验": 350}, "bonus": None},
            {"day": 17, "rewards": {"金元宝": 170, "经验": 400}, "bonus": None},
            {"day": 18, "rewards": {"金元宝": 180, "经验": 450}, "bonus": None},
            {"day": 19, "rewards": {"金元宝": 190, "经验": 500}, "bonus": {"item": "中级经验丹", "count": 3}},
            {"day": 20, "rewards": {"金元宝": 200, "经验": 550}, "bonus": {"item": "高级招募令", "count": 1}},
            {"day": 21, "rewards": {"金元宝": 210, "经验": 600}, "bonus": None},
            {"day": 22, "rewards": {"金元宝": 220, "经验": 650}, "bonus": None},
            {"day": 23, "rewards": {"金元宝": 230, "经验": 700}, "bonus": None},
            {"day": 24, "rewards": {"金元宝": 240, "经验": 750}, "bonus": None},
            {"day": 25, "rewards": {"金元宝": 250, "经验": 800}, "bonus": {"item": "顶级招募令", "count": 1}},
            {"day": 26, "rewards": {"金元宝": 260, "经验": 850}, "bonus": {"item": "装备精炼石", "count": 10}},
            {"day": 27, "rewards": {"金元宝": 270, "经验": 900}, "bonus": None},
            {"day": 28, "rewards": {"金元宝": 280, "经验": 950}, "bonus": None},
            {"day": 29, "rewards": {"金元宝": 290, "经验": 1000}, "bonus": None},
            {"day": 30, "rewards": {"金元宝": 500, "经验": 1500}, "bonus": {"item": "稀有武将碎片", "count": 50}}
        ]
    
    def _load_streak_rewards(self):
        return [
            {"days": 7, "name": "一周签到", "rewards": {"金元宝": 100, "中级经验丹": 1}},
            {"days": 14, "name": "两周签到", "rewards": {"金元宝": 200, "高级招募令": 1}},
            {"days": 21, "name": "三周签到", "rewards": {"金元宝": 300, "稀有武将碎片": 20}},
            {"days": 30, "name": "整月签到", "rewards": {"金元宝": 500, "传说武将碎片": 30}}
        ]
    
    def can_checkin(self):
        today = time.strftime("%Y-%m-%d")
        return data["checkin_center"]["last_checkin_date"] != today
    
    def get_consecutive_days(self):
        return data["checkin_center"]["consecutive_days"]
    
    def get_monthly_checkins(self):
        current_month = int(time.strftime("%Y%m"))
        if data["checkin_center"]["current_month"] != current_month:
            data["checkin_center"]["monthly_checkins"] = 0
            data["checkin_center"]["current_month"] = current_month
            save()
        return data["checkin_center"]["monthly_checkins"]
    
    def claim_reward(self):
        if not self.can_checkin():
            return False, "今天已经签到过了"
        
        today = time.strftime("%Y-%m-%d")
        current_month = int(time.strftime("%Y%m"))
        
        if data["checkin_center"]["current_month"] != current_month:
            data["checkin_center"]["monthly_checkins"] = 0
            data["checkin_center"]["current_month"] = current_month
            data["checkin_center"]["consecutive_days"] = 0
        
        last_date = data["checkin_center"]["last_checkin_date"]
        if last_date:
            last_time = time.mktime(time.strptime(last_date, "%Y-%m-%d"))
            today_time = time.mktime(time.strptime(today, "%Y-%m-%d"))
            days_diff = (today_time - last_time) / (24 * 3600)
            
            if days_diff == 1:
                data["checkin_center"]["consecutive_days"] += 1
            elif days_diff > 1:
                data["checkin_center"]["consecutive_days"] = 1
        else:
            data["checkin_center"]["consecutive_days"] = 1
        
        data["checkin_center"]["monthly_checkins"] += 1
        data["checkin_center"]["total_checkins"] += 1
        data["checkin_center"]["last_checkin_date"] = today
        data["checkin_center"]["checkins"][today] = time.time()
        
        day = data["checkin_center"]["monthly_checkins"]
        if day <= len(self.rewards):
            reward = self.rewards[day - 1]
            claimed_id = f"{current_month}_{day}"
            
            for resource, amount in reward["rewards"].items():
                if resource in data["resources"]:
                    data["resources"][resource] = data["resources"].get(resource, 0) + amount
                else:
                    data["resources"][resource] = amount
            
            if reward["bonus"]:
                bonus_item = reward["bonus"]["item"]
                bonus_count = reward["bonus"]["count"]
                if "items" not in data:
                    data["items"] = {}
                data["items"][bonus_item] = data["items"].get(bonus_item, 0) + bonus_count
            
            data["checkin_center"]["claimed_rewards"].append(claimed_id)
            
            self._check_streak_rewards()
            
            save()
            return True, reward
        else:
            return False, "本月签到次数已达上限"
    
    def _check_streak_rewards(self):
        consecutive = data["checkin_center"]["consecutive_days"]
        for streak in self.streak_rewards:
            if consecutive >= streak["days"]:
                streak_id = f"streak_{streak['days']}"
                if streak_id not in data["checkin_center"]["claimed_streak_rewards"]:
                    data["checkin_center"]["claimed_streak_rewards"].append(streak_id)
                    for reward_type, amount in streak["rewards"].items():
                        if reward_type in data["resources"]:
                            data["resources"][reward_type] = data["resources"].get(reward_type, 0) + amount
                        else:
                            data["resources"][reward_type] = amount
    
    def get_rewards_status(self):
        current_month = int(time.strftime("%Y%m"))
        status = []
        
        for i, reward in enumerate(self.rewards):
            day = i + 1
            claimed_id = f"{current_month}_{day}"
            claimed = claimed_id in data["checkin_center"]["claimed_rewards"]
            available = day <= self.get_monthly_checkins() + 1
            
            status.append({
                "day": day,
                "rewards": reward["rewards"],
                "bonus": reward["bonus"],
                "claimed": claimed,
                "available": available
            })
        
        return status
    
    def get_streak_rewards_status(self):
        consecutive = self.get_consecutive_days()
        status = []
        
        for streak in self.streak_rewards:
            claimed_id = f"streak_{streak['days']}"
            claimed = claimed_id in data["checkin_center"]["claimed_streak_rewards"]
            available = consecutive >= streak["days"]
            
            status.append({
                "days": streak["days"],
                "name": streak["name"],
                "rewards": streak["rewards"],
                "claimed": claimed,
                "available": available,
                "progress": min(100, int(consecutive / streak["days"] * 100))
            })
        
        return status

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
                SCREEN_WIDTH = 900
                SCREEN_HEIGHT = 700
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("签到中心")
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
        font_small = init_font(20)
        
        checkin_center = CheckinCenter()
        
        particles = []
        checkin_particles = []
        floating_texts = []
        
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
            
            for p in checkin_particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    checkin_particles.remove(p)
            
            for ft in floating_texts[:]:
                ft.update()
                ft.draw(screen)
                if ft.life <= 0:
                    floating_texts.remove(ft)
            
            draw_title(screen, "签到中心", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            consecutive_days = checkin_center.get_consecutive_days()
            monthly_checkins = checkin_center.get_monthly_checkins()
            total_checkins = data["checkin_center"]["total_checkins"]
            
            stats_y = SCREEN_HEIGHT * 0.18
            stats_spacing = SCREEN_WIDTH // 3
            
            stat_texts = [
                f"连续签到: {consecutive_days}天",
                f"本月签到: {monthly_checkins}天",
                f"累计签到: {total_checkins}天"
            ]
            
            for i, stat in enumerate(stat_texts):
                stat_surf = font_main.render(stat, True, COLORS["accent_blue"])
                stat_rect = stat_surf.get_rect(center=(stats_spacing * (i + 0.5), stats_y))
                screen.blit(stat_surf, stat_rect)
            
            rewards_status = checkin_center.get_rewards_status()
            
            tab_height = 45
            tab_y = SCREEN_HEIGHT * 0.26
            daily_tab = Button("每日签到", 50, tab_y, 150, tab_height, font_main, COLORS["btn_gold"], COLORS["btn_gold_hover"])
            streak_tab = Button("连续奖励", 220, tab_y, 150, tab_height, font_main)
            
            daily_tab.update((mx, my))
            streak_tab.update((mx, my))
            daily_tab.draw(screen)
            streak_tab.draw(screen)
            
            content_y = SCREEN_HEIGHT * 0.34
            
            cards = []
            card_width = min(110, SCREEN_WIDTH * 0.12)
            card_height = min(95, SCREEN_HEIGHT * 0.13)
            
            for i, status in enumerate(rewards_status[:7]):
                day = status["day"]
                is_checked = status["claimed"]
                is_today = day == monthly_checkins + 1 and not is_checked
                x = 50 + i * (card_width + 12)
                y = content_y
                card = CheckinCard(day, status["rewards"], status["bonus"], is_checked, is_today, x, y, card_width, card_height, font_small)
                cards.append(card)
                card.draw(screen)
            
            can_checkin = checkin_center.can_checkin()
            if can_checkin:
                checkin_btn = Button("立即签到", (SCREEN_WIDTH - 200) // 2, content_y + card_height + 30, 200, 60, font_main, COLORS["btn_green"], COLORS["btn_green_hover"])
                checkin_btn.update((mx, my))
                checkin_btn.draw(screen)
            else:
                checked_btn = Button("今日已签到", (SCREEN_WIDTH - 200) // 2, content_y + card_height + 30, 200, 60, font_main, (50, 80, 50), (70, 100, 70))
                checked_btn.update((mx, my))
                checked_btn.draw(screen)
            
            streak_y = content_y + card_height + 120
            streak_title = font_main.render("🎁 连续签到奖励", True, COLORS["accent_purple"])
            screen.blit(streak_title, (50, streak_y))
            
            streak_rewards_status = checkin_center.get_streak_rewards_status()
            for i, streak in enumerate(streak_rewards_status):
                streak_y += 50
                
                streak_bg = pygame.Rect(50, streak_y, SCREEN_WIDTH - 100, 60)
                pygame.draw.rect(screen, COLORS["panel_bg"], streak_bg, border_radius=10)
                pygame.draw.rect(screen, COLORS["accent_gold"], streak_bg, 2, border_radius=10)
                
                name_text = font_main.render(f"{streak['name']} ({streak['days']}天)", True, COLORS["text_white"])
                screen.blit(name_text, (70, streak_y + 10))
                
                rewards_text = ", ".join([f"{k}×{v}" for k, v in streak["rewards"].items()])
                rewards_surf = font_small.render(rewards_text, True, COLORS["accent_gold"])
                screen.blit(rewards_surf, (70, streak_y + 35))
                
                progress_bar = pygame.Rect(SCREEN_WIDTH - 250, streak_y + 20, 180, 20)
                pygame.draw.rect(screen, (50, 50, 70), progress_bar, border_radius=10)
                
                progress_fill = pygame.Rect(SCREEN_WIDTH - 250, streak_y + 20, int(180 * streak["progress"] / 100), 20)
                pygame.draw.rect(screen, COLORS["accent_green"], progress_fill, border_radius=10)
                
                progress_text = font_small.render(f"{streak['progress']}%", True, COLORS["text_white"])
                screen.blit(progress_text, (SCREEN_WIDTH - 70, streak_y + 18))
                
                if streak["claimed"]:
                    check_text = font_main.render("✓", True, COLORS["accent_green"])
                    screen.blit(check_text, (SCREEN_WIDTH - 60, streak_y + 15))
            
            return_btn = Button("返回", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, font_main)
            return_btn.update((mx, my))
            return_btn.draw(screen)
            
            if show_message:
                message_surf = font_main.render(message, True, COLORS["accent_green"])
                message_rect = message_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.88))
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
                    if can_checkin and checkin_btn.rect.collidepoint(mx, my):
                        success, msg = checkin_center.claim_reward()
                        if success:
                            reward_str = "+".join([f"{k}×{v}" for k, v in msg["rewards"].items()])
                            if msg["bonus"]:
                                reward_str += f" + {msg['bonus']['item']}×{msg['bonus']['count']}"
                            message = f"签到成功！获得：{reward_str}"
                            show_message = True
                            message_timer = 0
                            
                            for _ in range(30):
                                checkin_particles.append(Particle(
                                    SCREEN_WIDTH // 2, content_y + card_height + 60,
                                    COLORS["accent_gold"], 3, 3, 50
                                ))
                            
                            floating_texts.append(FloatingText(
                                f"+{msg['rewards']['金元宝']} 金元宝",
                                SCREEN_WIDTH // 2, content_y + card_height + 30,
                                COLORS["accent_gold"], font_main
                            ))
                    elif return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("签到中心")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("签到中心", str(e))

if __name__ == "__main__":
    main()