import os
import pygame
import json
import random
import math
from datetime import datetime, timedelta
from ASSET.game_data import data, save
from ASSET import safe_exit

# 颜色主题
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
    "btn_blue_hover": (80, 160, 255)
}

class Button:
    def __init__(self, text, x, y, width, height, font):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.is_hovered = False
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        # 按钮背景
        color = (50, 60, 90) if not self.is_hovered else (60, 70, 110)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 2, border_radius=8)
        
        # 文字
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class CheckinCard:
    def __init__(self, day, reward, is_checked, is_today, x, y, width, height, font):
        self.day = day
        self.reward = reward
        self.is_checked = is_checked
        self.is_today = is_today
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
    
    def draw(self, surface):
        # 卡片背景
        if self.is_checked:
            bg_color = (60, 180, 100, 200)
        elif self.is_today:
            bg_color = (255, 215, 0, 200)
        else:
            bg_color = (35, 40, 60, 200)
        
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=12)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 2, border_radius=12)
        
        # 日期
        if self.is_today:
            day_text = self.font.render(f"第{self.day}天", True, (30, 30, 60))  # 深色文字
        else:
            day_text = self.font.render(f"第{self.day}天", True, COLORS["text_white"])
        day_rect = day_text.get_rect(center=(self.rect.x + self.rect.width // 2, self.rect.y + 25))
        surface.blit(day_text, day_rect)
        
        # 奖励
        if self.is_today:
            reward_text = self.font.render(f"{self.reward}", True, (30, 30, 60))  # 深色文字
        else:
            reward_text = self.font.render(f"{self.reward}", True, COLORS["accent_gold"])
        reward_rect = reward_text.get_rect(center=(self.rect.x + self.rect.width // 2, self.rect.y + 60))
        surface.blit(reward_text, reward_rect)
        
        # 状态
        if self.is_checked:
            check_text = self.font.render("✓", True, COLORS["text_white"])
            check_rect = check_text.get_rect(center=(self.rect.x + self.rect.width - 20, self.rect.y + 20))
            surface.blit(check_text, check_rect)
        elif self.is_today:
            today_text = self.font.render("今天", True, (30, 30, 60))  # 深色文字
            today_rect = today_text.get_rect(center=(self.rect.x + self.rect.width - 25, self.rect.y + 20))
            surface.blit(today_text, today_rect)

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

def draw_gradient_background(surface, color1, color2):
    """绘制渐变背景"""
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_title(surface, text, y, screen_width):
    """绘制标题"""
    font = pygame.font.Font(None, 60)
    title_surf = font.render(text, True, COLORS["accent_gold"])
    title_rect = title_surf.get_rect(center=(screen_width // 2, y))
    surface.blit(title_surf, title_rect)
    
    # 标题下划线
    underline_width = title_rect.width * 1.2
    underline_x = (screen_width - underline_width) // 2
    pygame.draw.line(surface, COLORS["accent_gold"], 
                   (underline_x, y + 35), (underline_x + underline_width, y + 35), 3)

def get_system_font_name():
    """获取系统字体名称"""
    if 'ANDROID_DATA' in os.environ:
        return None
    
    # 尝试常见的中文字体
    fonts = ["Microsoft YaHei", "SimHei", "Arial", "sans-serif"]
    for font in fonts:
        try:
            test_font = pygame.font.SysFont(font, 24)
            if test_font:
                return font
        except Exception:
            pass
    return None

def get_today_date():
    """获取今天的日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")

def check_in():
    """执行签到操作"""
    # 确保签到数据存在
    if 'checkin' not in data:
        data['checkin'] = {
            'last_checkin': '',
            'consecutive_days': 0,
            'total_checkins': 0,
            'rewards_claimed': []
        }
        save()
    
    checkin_data = data['checkin']
    today = get_today_date()
    
    # 检查今天是否已经签到
    if checkin_data['last_checkin'] == today:
        return False, "今天已经签到过了"
    
    # 检查是否是连续签到
    last_date = checkin_data['last_checkin']
    if last_date:
        try:
            last_checkin_date = datetime.strptime(last_date, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            days_diff = (today_date - last_checkin_date).days
            
            if days_diff == 1:
                # 连续签到
                checkin_data['consecutive_days'] += 1
            elif days_diff > 1:
                # 中断连续签到
                checkin_data['consecutive_days'] = 1
            else:
                # 同一天，不更新
                return False, "今天已经签到过了"
        except ValueError:
            checkin_data['consecutive_days'] = 1
    else:
        # 第一次签到
        checkin_data['consecutive_days'] = 1
    
    # 更新签到数据
    checkin_data['last_checkin'] = today
    checkin_data['total_checkins'] += 1
    
    # 计算奖励
    day = checkin_data['consecutive_days']
    rewards = {
        1: "金元宝×50",
        2: "金元宝×80",
        3: "金元宝×100",
        4: "金元宝×120",
        5: "金元宝×150",
        6: "金元宝×180",
        7: "金元宝×200 + 时间卡×1"
    }
    
    # 超过7天，循环奖励
    if day > 7:
        day = day % 7
        if day == 0:
            day = 7
    
    reward = rewards.get(day, "金元宝×50")
    
    # 发放奖励
    if "金元宝" in reward:
        amount = int(reward.split("×")[1].split()[0])
        data['resources']['金元宝'] = data['resources'].get('金元宝', 0) + amount
    
    if "时间卡" in reward:
        amount = int(reward.split("+")[-1].split("×")[1])
        data['resources']['时间卡'] = data['resources'].get('时间卡', 0) + amount
    
    # 记录奖励
    checkin_data['rewards_claimed'].append({
        'date': today,
        'day': checkin_data['consecutive_days'],
        'reward': reward
    })
    
    save()
    return True, f"签到成功！获得奖励：{reward}"

def main():
    """每日签到系统主函数"""
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
                SCREEN_WIDTH = 900
                SCREEN_HEIGHT = 700
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("每日签到")
        clock = pygame.time.Clock()

        # 计算缩放因子
        scale = min(SCREEN_WIDTH / 900, SCREEN_HEIGHT / 700)

        # 字体初始化（根据屏幕大小自适应）
        def init_font(size):
            font_name = get_system_font_name()
            # 根据屏幕大小调整字体
            adjusted_size = int(size * scale)
            try:
                return pygame.font.SysFont(font_name, adjusted_size)
            except Exception:
                return pygame.font.Font(None, adjusted_size)

        font_title = init_font(36 if not 'ANDROID_DATA' in os.environ else 52)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)

        # 确保签到数据存在
        if 'checkin' not in data:
            data['checkin'] = {
                'last_checkin': '',
                'consecutive_days': 0,
                'total_checkins': 0,
                'rewards_claimed': []
            }
            save()

        checkin_data = data['checkin']
        today = get_today_date()
        is_checked_today = checkin_data['last_checkin'] == today
        consecutive_days = checkin_data['consecutive_days']

        # 签到奖励设置
        rewards = [
            "金元宝×50",
            "金元宝×80",
            "金元宝×100",
            "金元宝×120",
            "金元宝×150",
            "金元宝×180",
            "金元宝×200 + 时间卡×1"
        ]

        # 创建签到卡片
        cards = []
        card_width = min(120, SCREEN_WIDTH * 0.13)
        card_height = min(100, SCREEN_HEIGHT * 0.14)
        start_x = (SCREEN_WIDTH - 7 * (card_width + 15)) // 2
        start_y = SCREEN_HEIGHT * 0.35

        for i in range(7):
            day = i + 1
            is_checked = day <= consecutive_days
            is_today = day == consecutive_days + 1 and not is_checked_today
            x = start_x + i * (card_width + 15)
            y = start_y
            card = CheckinCard(day, rewards[i], is_checked, is_today, x, y, card_width, card_height, font_small)
            cards.append(card)

        # 装饰粒子
        particles = []
        # 签到特效粒子
        checkin_particles = []

        # 消息
        message = ""
        show_message = False
        message_timer = 0

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 装饰粒子
            if random.random() < 0.1:
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

            # 签到特效粒子
            for p in checkin_particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    checkin_particles.remove(p)

            # 标题
            draw_title(screen, "每日签到", SCREEN_HEIGHT * 0.12, SCREEN_WIDTH)

            # 连续签到天数
            streak_text = font_normal.render(f"连续签到：{consecutive_days} 天", True, COLORS["accent_blue"])
            streak_rect = streak_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.22))
            screen.blit(streak_text, streak_rect)

            # 绘制签到卡片
            for card in cards:
                card.draw(screen)

            # 签到按钮
            if not is_checked_today:
                checkin_btn = Button("立即签到", (SCREEN_WIDTH - 200) // 2, SCREEN_HEIGHT * 0.7, 200, 60, font_normal)
                checkin_btn.check_hover((mx, my))
                checkin_btn.draw(screen)
            else:
                checked_btn = Button("今日已签到", (SCREEN_WIDTH - 200) // 2, SCREEN_HEIGHT * 0.7, 200, 60, font_normal)
                checked_btn.check_hover((mx, my))
                checked_btn.draw(screen)

            # 返回按钮
            return_btn = Button("返回主菜单", (SCREEN_WIDTH - 200) // 2, SCREEN_HEIGHT - 80, 200, 50, font_normal)
            return_btn.check_hover((mx, my))
            return_btn.draw(screen)

            # 显示消息
            if show_message:
                message_surf = font_normal.render(message, True, COLORS["accent_green"])
                message_rect = message_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.85))
                pygame.draw.rect(screen, (35, 40, 60, 230), 
                               (message_rect.x - 20, message_rect.y - 10, message_rect.width + 40, message_rect.height + 20), 
                               border_radius=8)
                screen.blit(message_surf, message_rect)
                message_timer += 1
                if message_timer > 60:
                    show_message = False
                    message_timer = 0

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 签到按钮
                    if not is_checked_today:
                        checkin_btn_rect = pygame.Rect((SCREEN_WIDTH - 200) // 2, SCREEN_HEIGHT * 0.7, 200, 60)
                        if checkin_btn_rect.collidepoint(mx, my):
                            success, msg = check_in()
                            if success:
                                message = msg
                                show_message = True
                                message_timer = 0
                                # 生成签到特效
                                for _ in range(30):
                                    checkin_particles.append(Particle(
                                        SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.7 + 30,
                                        COLORS["accent_gold"], 3, 3, 50
                                    ))
                                # 重新获取签到数据
                                checkin_data = data['checkin']
                                is_checked_today = checkin_data['last_checkin'] == today
                                consecutive_days = checkin_data['consecutive_days']
                                # 更新卡片
                                cards = []
                                for i in range(7):
                                    day = i + 1
                                    is_checked = day <= consecutive_days
                                    is_today = day == consecutive_days + 1 and not is_checked_today
                                    x = start_x + i * (card_width + 15)
                                    y = start_y
                                    card = CheckinCard(day, rewards[i], is_checked, is_today, x, y, card_width, card_height, font_small)
                                    cards.append(card)
                    
                    # 返回按钮
                    if return_btn.rect.collidepoint(mx, my):
                        running = False

            pygame.display.flip()
            clock.tick(60)

        safe_exit("每日签到")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("每日签到", str(e))

if __name__ == "__main__":
    main()