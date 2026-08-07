import os
import time
import pygame
import random
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
from ASSET.languages import get_text
from ASSET import safe_exit

# 颜色主题
COLORS = {
    "bg_dark": (10, 10, 25),
    "bg_light": (20, 20, 45),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 180),
    "accent_blue_light": (100, 149, 237),
    "accent_blue_dark": (50, 100, 150),
    "accent_red": (200, 80, 80),
    "accent_green": (80, 180, 80),
    "accent_purple": (128, 0, 128),
    "text_white": (255, 255, 255),
    "text_grey": (150, 150, 150),
    "btn_blue": (60, 120, 200),
    "btn_blue_hover": (80, 160, 255),
    "btn_gold": (200, 160, 50),
    "btn_gold_hover": (255, 200, 80)
}

# 季节类型
SEASONS = [
    {
        "name": "春季",
        "description": "春暖花开，万物复苏",
        "month_range": (3, 5),
        "effects": {
            "resource_bonus": 0.15,
            "heal_bonus": 0.1,
            "fishing_bonus": 0.15
        },
        "color": (100, 200, 100),
        "ambient_effect": "flowers"
    },
    {
        "name": "夏季",
        "description": "烈日炎炎，酷暑难耐",
        "month_range": (6, 8),
        "effects": {
            "resource_bonus": 0.1,
            "attack_bonus": 0.05,
            "fishing_bonus": 0.2
        },
        "color": (255, 150, 50),
        "ambient_effect": "sunshine"
    },
    {
        "name": "秋季",
        "description": "秋风送爽，硕果累累",
        "month_range": (9, 11),
        "effects": {
            "resource_bonus": 0.2,
            "gold_bonus": 0.1,
            "fishing_bonus": 0.1
        },
        "color": (200, 100, 50),
        "ambient_effect": "leaves"
    },
    {
        "name": "冬季",
        "description": "白雪皑皑，银装素裹",
        "month_range": (12, 2),
        "effects": {
            "resource_bonus": -0.1,
            "defense_bonus": 0.1,
            "fishing_bonus": -0.1
        },
        "color": (200, 200, 255),
        "ambient_effect": "snow"
    }
]

# 时间段类型
TIME_OF_DAY = [
    {
        "name": "黎明",
        "hour_range": (5, 6),
        "effects": {
            "visibility": 0.8,
            "mood_bonus": 0.05
        },
        "color": (255, 150, 100),
        "bg_color": (30, 40, 60)
    },
    {
        "name": "上午",
        "hour_range": (7, 11),
        "effects": {
            "visibility": 1.0,
            "resource_bonus": 0.05
        },
        "color": (255, 200, 100),
        "bg_color": (40, 50, 80)
    },
    {
        "name": "中午",
        "hour_range": (12, 13),
        "effects": {
            "visibility": 1.0,
            "attack_bonus": 0.05
        },
        "color": (255, 255, 200),
        "bg_color": (50, 60, 100)
    },
    {
        "name": "下午",
        "hour_range": (14, 17),
        "effects": {
            "visibility": 0.95,
            "resource_bonus": 0.05
        },
        "color": (255, 180, 100),
        "bg_color": (40, 50, 80)
    },
    {
        "name": "黄昏",
        "hour_range": (18, 19),
        "effects": {
            "visibility": 0.7,
            "mood_bonus": -0.05
        },
        "color": (255, 100, 100),
        "bg_color": (30, 30, 50)
    },
    {
        "name": "夜晚",
        "hour_range": (20, 23),
        "effects": {
            "visibility": 0.5,
            "stealth_bonus": 0.2,
            "resource_bonus": -0.05
        },
        "color": (100, 100, 200),
        "bg_color": (10, 10, 30)
    },
    {
        "name": "深夜",
        "hour_range": (0, 4),
        "effects": {
            "visibility": 0.3,
            "stealth_bonus": 0.3,
            "mood_bonus": -0.1
        },
        "color": (50, 50, 150),
        "bg_color": (5, 5, 20)
    }
]

# 天气类型
WEATHER_TYPES = [
    {
        "name": "晴天",
        "description": "阳光明媚，适合户外活动",
        "effects": {
            "fishing_bonus": 0.1,
            "resource_bonus": 0.1,
            "pet_happiness_bonus": 5
        },
        "color": (255, 215, 0),
        "icon": "☀️"
    },
    {
        "name": "多云",
        "description": "天空多云，天气凉爽",
        "effects": {
            "fishing_bonus": 0.05,
            "resource_bonus": 0.05,
            "pet_happiness_bonus": 2
        },
        "color": (150, 150, 150),
        "icon": "☁️"
    },
    {
        "name": "雨天",
        "description": "下雨了，钓鱼的好时机",
        "effects": {
            "fishing_bonus": 0.2,
            "resource_bonus": -0.1,
            "pet_happiness_bonus": -3
        },
        "color": (70, 130, 180),
        "icon": "🌧️"
    },
    {
        "name": "雷暴",
        "description": "雷电交加，不宜外出",
        "effects": {
            "fishing_bonus": -0.2,
            "resource_bonus": -0.2,
            "pet_happiness_bonus": -5,
            "attack_bonus": 0.1
        },
        "color": (50, 50, 100),
        "icon": "⛈️"
    },
    {
        "name": "雪天",
        "description": "雪花飞舞，银装素裹",
        "effects": {
            "fishing_bonus": -0.1,
            "resource_bonus": -0.1,
            "pet_happiness_bonus": 3,
            "defense_bonus": 0.1
        },
        "color": (200, 200, 255),
        "icon": "❄️"
    },
    {
        "name": "雾天",
        "description": "大雾弥漫，视线受阻",
        "effects": {
            "visibility": 0.5,
            "stealth_bonus": 0.15
        },
        "color": (180, 180, 180),
        "icon": "🌫️"
    },
    {
        "name": "沙尘暴",
        "description": "风沙漫天，寸步难行",
        "effects": {
            "visibility": 0.4,
            "resource_bonus": -0.15
        },
        "color": (180, 140, 100),
        "icon": "🌪️"
    }
]

# 节日类型
HOLIDAYS = [
    {
        "name": "春节",
        "month": 1,
        "day": 1,
        "description": "中国传统节日，新年的开始",
        "effects": {
            "resource_bonus": 0.5,
            "gold_bonus": 0.3
        },
        "color": (255, 0, 0)
    },
    {
        "name": "元宵节",
        "month": 1,
        "day": 15,
        "description": "中国传统节日，吃元宵",
        "effects": {
            "resource_bonus": 0.3,
            "gold_bonus": 0.2
        },
        "color": (255, 165, 0)
    },
    {
        "name": "清明节",
        "month": 4,
        "day": 4,
        "description": "中国传统节日，扫墓祭祖",
        "effects": {
            "resource_bonus": 0.2,
            "gold_bonus": 0.1
        },
        "color": (0, 255, 0)
    },
    {
        "name": "端午节",
        "month": 5,
        "day": 5,
        "description": "中国传统节日，吃粽子",
        "effects": {
            "resource_bonus": 0.3,
            "gold_bonus": 0.2
        },
        "color": (255, 105, 180)
    },
    {
        "name": "中秋节",
        "month": 8,
        "day": 15,
        "description": "中国传统节日，赏月吃月饼",
        "effects": {
            "resource_bonus": 0.4,
            "gold_bonus": 0.25
        },
        "color": (255, 215, 0)
    },
    {
        "name": "国庆节",
        "month": 10,
        "day": 1,
        "description": "国庆节，庆祝国家成立",
        "effects": {
            "resource_bonus": 0.5,
            "gold_bonus": 0.3
        },
        "color": (255, 0, 0)
    }
]

class WeatherSystem:
    def __init__(self):
        """初始化天气系统"""
        # 确保天气数据存在
        if "weather" not in data:
            data["weather"] = {
                "current_weather": None,
                "weather_start_time": 0,
                "weather_duration": 0,
                "current_holiday": None,
                "current_season": None,
                "current_time_of_day": None,
                "game_time": time.time(),
                "time_speed": 1.0
            }
        
        # 初始化天气
        self.update_weather()
        # 检查节日
        self.check_holiday()
        # 检查季节
        self.check_season()
        # 检查时间段
        self.check_time_of_day()
    
    def update_weather(self):
        """更新天气"""
        current_time = time.time()
        
        # 检查天气是否需要更新
        if data["weather"]["current_weather"] is None or \
           current_time >= data["weather"]["weather_start_time"] + data["weather"]["weather_duration"]:
            # 根据季节选择天气
            season = self.get_current_season()
            available_weathers = WEATHER_TYPES.copy()
            
            # 根据季节过滤天气
            if season and season["name"] == "冬季":
                available_weathers = [w for w in available_weathers if w["name"] in ["雪天", "多云", "晴天", "雾天"]]
            elif season and season["name"] == "夏季":
                available_weathers = [w for w in available_weathers if w["name"] in ["晴天", "雷暴", "雨天", "多云"]]
            
            # 随机选择天气
            weather = random.choice(available_weathers)
            data["weather"]["current_weather"] = weather
            data["weather"]["weather_start_time"] = current_time
            # 天气持续时间：1-3小时随机
            data["weather"]["weather_duration"] = random.randint(1, 3) * 3600
            
            # 保存数据
            save()
    
    def check_holiday(self):
        """检查是否有节日"""
        current_time = time.localtime()
        current_month = current_time.tm_mon
        current_day = current_time.tm_mday
        
        # 检查是否有节日
        current_holiday = None
        for holiday in HOLIDAYS:
            if holiday["month"] == current_month and holiday["day"] == current_day:
                current_holiday = holiday
                break
        
        data["weather"]["current_holiday"] = current_holiday
        save()
    
    def check_season(self):
        """检查当前季节"""
        current_time = time.localtime()
        current_month = current_time.tm_mon
        
        # 检查季节
        current_season = None
        for season in SEASONS:
            month_range = season["month_range"]
            if month_range[0] <= month_range[1]:
                if month_range[0] <= current_month <= month_range[1]:
                    current_season = season
                    break
            else:
                # 跨年度季节（冬季）
                if current_month >= month_range[0] or current_month <= month_range[1]:
                    current_season = season
                    break
        
        data["weather"]["current_season"] = current_season
        save()
    
    def check_time_of_day(self):
        """检查当前时间段"""
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        
        # 检查时间段
        current_time_of_day = None
        for time_info in TIME_OF_DAY:
            hour_range = time_info["hour_range"]
            if hour_range[0] <= hour_range[1]:
                if hour_range[0] <= current_hour <= hour_range[1]:
                    current_time_of_day = time_info
                    break
            else:
                # 跨午夜时间段（深夜）
                if current_hour >= hour_range[0] or current_hour <= hour_range[1]:
                    current_time_of_day = time_info
                    break
        
        data["weather"]["current_time_of_day"] = current_time_of_day
        save()
    
    def update_game_time(self, delta_time=1.0):
        """更新游戏时间"""
        data["weather"]["game_time"] += delta_time * data["weather"]["time_speed"]
        # 每小时更新一次天气相关信息
        if random.random() < 0.001:  # 大约每1000帧更新一次
            self.check_season()
            self.check_time_of_day()
            self.update_weather()
            self.check_holiday()
    
    def set_time_speed(self, speed):
        """设置时间流速"""
        data["weather"]["time_speed"] = max(0.1, min(5.0, speed))
        save()
    
    def get_current_weather(self):
        """获取当前天气"""
        self.update_weather()
        return data["weather"]["current_weather"]
    
    def get_current_holiday(self):
        """获取当前节日"""
        self.check_holiday()
        return data["weather"]["current_holiday"]
    
    def get_current_season(self):
        """获取当前季节"""
        self.check_season()
        return data["weather"]["current_season"]
    
    def get_current_time_of_day(self):
        """获取当前时间段"""
        self.check_time_of_day()
        return data["weather"]["current_time_of_day"]
    
    def get_weather_effects(self):
        """获取天气效果"""
        weather = self.get_current_weather()
        if weather:
            return weather["effects"]
        return {}
    
    def get_holiday_effects(self):
        """获取节日效果"""
        holiday = self.get_current_holiday()
        if holiday:
            return holiday["effects"]
        return {}
    
    def get_season_effects(self):
        """获取季节效果"""
        season = self.get_current_season()
        if season:
            return season["effects"]
        return {}
    
    def get_time_of_day_effects(self):
        """获取时间段效果"""
        time_info = self.get_current_time_of_day()
        if time_info:
            return time_info["effects"]
        return {}
    
    def get_all_effects(self):
        """获取所有效果"""
        effects = {}
        
        # 季节效果
        season_effects = self.get_season_effects()
        for key, value in season_effects.items():
            effects[key] = effects.get(key, 0) + value
        
        # 时间段效果
        time_effects = self.get_time_of_day_effects()
        for key, value in time_effects.items():
            effects[key] = effects.get(key, 0) + value
        
        # 天气效果
        weather_effects = self.get_weather_effects()
        for key, value in weather_effects.items():
            effects[key] = effects.get(key, 0) + value
        
        # 节日效果
        holiday_effects = self.get_holiday_effects()
        for key, value in holiday_effects.items():
            effects[key] = effects.get(key, 0) + value
        
        return effects
    
    def get_ambient_effect(self):
        """获取环境特效类型"""
        season = self.get_current_season()
        if season:
            return season["ambient_effect"]
        return None

def draw_gradient_bg(surface, color1, color2):
    """绘制渐变背景"""
    for y in range(surface.get_height()):
        ratio = y / surface.get_height()
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (surface.get_width(), y))

def show_message(surface, message, font):
    """显示消息"""
    text_surface = font.render(message, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
    
    # 绘制背景
    bg_rect = text_rect.inflate(20, 10)
    pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect, border_radius=5)
    
    # 绘制文本
    surface.blit(text_surface, text_rect)
    pygame.display.flip()
    
    # 等待1秒
    pygame.time.wait(1000)

def init_font(size):
    return get_font(size)

class Button:
    def __init__(self, text, x, y, width, height, font, normal_color=COLORS["btn_blue"], hover_color=COLORS["btn_blue_hover"]):
        """初始化按钮"""
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.hovered = False
    
    def check_hover(self, mouse_pos):
        """检查鼠标是否悬停"""
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def check_click(self, mouse_pos):
        """检查鼠标是否点击"""
        return self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        """绘制按钮"""
        # 绘制按钮背景
        color = self.hover_color if self.hovered else self.normal_color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        
        # 绘制按钮文本
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

class ScrollableContainer:
    def __init__(self, x, y, width, height):
        """初始化滚动容器"""
        self.rect = pygame.Rect(x, y, width, height)
        self.content_height = 0
        self.scroll_y = 0
        self.max_scroll = 0
        self.is_dragging = False
        self.drag_start_y = 0
    
    def update_content_height(self, height):
        """更新内容高度"""
        self.content_height = height
        self.max_scroll = max(0, self.content_height - self.rect.height)
    
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self.drag_start_y = event.pos[1] - self.scroll_y
            elif event.button == 4:  # 鼠标滚轮向上
                self.scroll_y = max(0, self.scroll_y - 20)
            elif event.button == 5:  # 鼠标滚轮向下
                self.scroll_y = min(self.max_scroll, self.scroll_y + 20)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self.scroll_y = event.pos[1] - self.drag_start_y
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))
    
    def draw(self, surface):
        """绘制滚动容器"""
        # 绘制容器背景
        pygame.draw.rect(surface, (30, 30, 50), self.rect, border_radius=10)
        
        # 绘制滚动条
        if self.content_height > self.rect.height:
            scrollbar_height = (self.rect.height / self.content_height) * self.rect.height
            scrollbar_y = (self.scroll_y / self.max_scroll) * (self.rect.height - scrollbar_height)
            scrollbar_rect = pygame.Rect(self.rect.right - 10, self.rect.y + scrollbar_y, 8, scrollbar_height)
            pygame.draw.rect(surface, (100, 100, 100), scrollbar_rect, border_radius=4)
    
    def get_relative_pos(self, x, y):
        """获取相对位置"""
        return (x, y - self.scroll_y)

def draw_weather_system(surface, font_big, font_main, font_small, weather_system, container=None):
    """绘制天气系统"""
    screen_width = surface.get_width()
    screen_height = surface.get_height()
    margin = 20
    
    # 标题
    title = font_big.render("天气与节日系统", True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, 50))
    surface.blit(title, title_rect)
    
    # 计算内容高度
    content_height = 120  # 标题高度
    
    # 当前天气
    current_weather = weather_system.get_current_weather()
    if current_weather:
        content_height += 120  # 天气信息高度
        
        # 天气效果
        effects = current_weather['effects']
        content_height += len(effects) * 30  # 每个效果30像素高度
    
    # 当前节日
    current_holiday = weather_system.get_current_holiday()
    if current_holiday:
        content_height += 120  # 节日信息高度
        
        # 节日效果
        effects = current_holiday['effects']
        content_height += len(effects) * 30  # 每个效果30像素高度
    
    # 所有效果
    all_effects = weather_system.get_all_effects()
    if all_effects:
        content_height += 80  # 总效果标题高度
        content_height += len(all_effects) * 30  # 每个效果30像素高度
    
    # 如果提供了容器，更新其内容高度
    if container:
        container.update_content_height(content_height)
    
    # 绘制内容
    y_offset = 120  # 标题下方开始
    
    # 当前天气
    if current_weather:
        weather_text = font_main.render(f"当前天气: {current_weather['name']}", True, current_weather['color'])
        weather_desc = font_small.render(current_weather['description'], True, COLORS["text_white"])
        
        # 确保文本不会超出屏幕
        max_width = screen_width - 2 * margin
        
        if weather_text.get_width() > max_width:
            # 调整字体大小
            scale_factor = max_width / weather_text.get_width()
            new_font_size = int(font_main.get_height() * scale_factor)
            scaled_font = pygame.font.SysFont(font_main.get_name(), new_font_size)
            weather_text = scaled_font.render(f"当前天气: {current_weather['name']}", True, current_weather['color'])
        
        if weather_desc.get_width() > max_width:
            # 调整字体大小
            scale_factor = max_width / weather_desc.get_width()
            new_font_size = int(font_small.get_height() * scale_factor)
            scaled_font = pygame.font.SysFont(font_small.get_name(), new_font_size)
            weather_desc = scaled_font.render(current_weather['description'], True, COLORS["text_white"])
        
        # 计算绘制位置
        draw_y = y_offset
        if container:
            draw_y -= container.scroll_y
        
        surface.blit(weather_text, (margin, draw_y))
        surface.blit(weather_desc, (margin, draw_y + 40))
        
        # 天气效果
        effects = current_weather['effects']
        effect_y = draw_y + 80
        for key, value in effects.items():
            effect_name = {
                "fishing_bonus": "钓鱼成功率",
                "resource_bonus": "资源产出",
                "pet_happiness_bonus": "宠物快乐度"
            }.get(key, key)
            effect_value = f"{value * 100:.0f}%" if isinstance(value, float) else value
            effect_text = font_small.render(f"{effect_name}: {effect_value}", True, COLORS["text_white"])
            
            # 确保文本不会超出屏幕
            if effect_text.get_width() > max_width:
                # 调整字体大小
                scale_factor = max_width / effect_text.get_width()
                new_font_size = int(font_small.get_height() * scale_factor)
                scaled_font = pygame.font.SysFont(font_small.get_name(), new_font_size)
                effect_text = scaled_font.render(f"{effect_name}: {effect_value}", True, COLORS["text_white"])
            
            surface.blit(effect_text, (margin, effect_y))
            effect_y += 30
        
        y_offset += 120 + len(effects) * 30
    
    # 当前节日
    if current_holiday:
        holiday_text = font_main.render(f"当前节日: {current_holiday['name']}", True, current_holiday['color'])
        holiday_desc = font_small.render(current_holiday['description'], True, COLORS["text_white"])
        
        # 确保文本不会超出屏幕
        max_width = screen_width - 2 * margin
        
        if holiday_text.get_width() > max_width:
            # 调整字体大小
            scale_factor = max_width / holiday_text.get_width()
            new_font_size = int(font_main.get_height() * scale_factor)
            scaled_font = pygame.font.SysFont(font_main.get_name(), new_font_size)
            holiday_text = scaled_font.render(f"当前节日: {current_holiday['name']}", True, current_holiday['color'])
        
        if holiday_desc.get_width() > max_width:
            # 调整字体大小
            scale_factor = max_width / holiday_desc.get_width()
            new_font_size = int(font_small.get_height() * scale_factor)
            scaled_font = pygame.font.SysFont(font_small.get_name(), new_font_size)
            holiday_desc = scaled_font.render(current_holiday['description'], True, COLORS["text_white"])
        
        # 计算绘制位置
        draw_y = y_offset
        if container:
            draw_y -= container.scroll_y
        
        surface.blit(holiday_text, (margin, draw_y))
        surface.blit(holiday_desc, (margin, draw_y + 40))
        
        # 节日效果
        effects = current_holiday['effects']
        effect_y = draw_y + 80
        for key, value in effects.items():
            effect_name = {
                "resource_bonus": "资源产出",
                "gold_bonus": "金元宝获得"
            }.get(key, key)
            effect_value = f"{value * 100:.0f}%" if isinstance(value, float) else value
            effect_text = font_small.render(f"{effect_name}: {effect_value}", True, COLORS["text_white"])
            
            # 确保文本不会超出屏幕
            if effect_text.get_width() > max_width:
                # 调整字体大小
                scale_factor = max_width / effect_text.get_width()
                new_font_size = int(font_small.get_height() * scale_factor)
                scaled_font = pygame.font.SysFont(font_small.get_name(), new_font_size)
                effect_text = scaled_font.render(f"{effect_name}: {effect_value}", True, COLORS["text_white"])
            
            surface.blit(effect_text, (margin, effect_y))
            effect_y += 30
        
        y_offset += 120 + len(effects) * 30
    
    # 所有效果
    if all_effects:
        total_effects_text = font_main.render("总效果:", True, COLORS["accent_blue"])
        
        # 确保文本不会超出屏幕
        max_width = screen_width - 2 * margin
        
        if total_effects_text.get_width() > max_width:
            # 调整字体大小
            scale_factor = max_width / total_effects_text.get_width()
            new_font_size = int(font_main.get_height() * scale_factor)
            scaled_font = pygame.font.SysFont(font_main.get_name(), new_font_size)
            total_effects_text = scaled_font.render("总效果:", True, COLORS["accent_blue"])
        
        # 计算绘制位置
        draw_y = y_offset
        if container:
            draw_y -= container.scroll_y
        
        surface.blit(total_effects_text, (margin, draw_y))
        
        effect_y = draw_y + 40
        for key, value in all_effects.items():
            effect_name = {
                "fishing_bonus": "钓鱼成功率",
                "resource_bonus": "资源产出",
                "pet_happiness_bonus": "宠物快乐度",
                "gold_bonus": "金元宝获得"
            }.get(key, key)
            effect_value = f"{value * 100:.0f}%" if isinstance(value, float) else value
            effect_text = font_small.render(f"{effect_name}: {effect_value}", True, COLORS["text_white"])
            
            # 确保文本不会超出屏幕
            if effect_text.get_width() > max_width:
                # 调整字体大小
                scale_factor = max_width / effect_text.get_width()
                new_font_size = int(font_small.get_height() * scale_factor)
                scaled_font = pygame.font.SysFont(font_small.get_name(), new_font_size)
                effect_text = scaled_font.render(f"{effect_name}: {effect_value}", True, COLORS["text_white"])
            
            surface.blit(effect_text, (margin, effect_y))
            effect_y += 30

def main():
    """天气系统主函数"""
    try:
        # 初始化
        pygame.init()
        
        # 屏幕设置
        SCREEN_WIDTH = 800
        SCREEN_HEIGHT = 600
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("天气与节日系统")
        
        # 时钟
        clock = pygame.time.Clock()
        
        # 字体
        font_big = init_font(48)
        font_main = init_font(32)
        font_small = init_font(24)
        
        # 系统初始化
        weather_system = WeatherSystem()
        
        # 创建滚动容器
        container_width = SCREEN_WIDTH - 40
        container_height = SCREEN_HEIGHT - 150
        container = ScrollableContainer(20, 100, container_width, container_height)
        
        # 创建按钮
        back_btn = Button("返回", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, font_small)
        
        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 绘制滚动容器
            container.draw(screen)
            
            # 绘制天气系统内容到容器中
            # 创建一个临时表面来绘制内容
            temp_surface = pygame.Surface((container_width, container.content_height), pygame.SRCALPHA)
            draw_weather_system(temp_surface, font_big, font_main, font_small, weather_system, container)
            
            # 将临时表面的内容绘制到屏幕上
            screen.blit(temp_surface, (container.rect.x, container.rect.y - container.scroll_y))
            
            # 检查按钮悬停
            back_btn.check_hover((mx, my))
            
            # 绘制按钮
            back_btn.draw(screen)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # 处理滚动容器事件
                container.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 处理返回按钮
                    if back_btn.check_click((mx, my)):
                        running = False
            
            clock.tick(60)
        
        safe_exit("天气系统")
    except Exception as e:
        logger.info(f"异常：{str(e)}")
        logger.info("详细错误信息：")
        import traceback
        traceback.print_exc()
        safe_exit("天气系统", str(e))

if __name__ == "__main__":
    main()
