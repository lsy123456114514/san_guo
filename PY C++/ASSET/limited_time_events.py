"""限时活动系统 - 节日、庆典特殊奖励"""

import os
import pygame
import datetime
import random
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
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
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 200),
    "panel_bg": (30, 30, 55, 200)
}

class Button:
    def __init__(self, text, x, y, width, height, font, 
                 normal_color=COLORS["accent_blue"], 
                 hover_color=COLORS["accent_blue_light"], 
                 text_color=COLORS["text_white"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.is_clicked = False
        self.click_timer = 0
    
    def draw(self, surface):
        # 按钮颜色
        color = self.hover_color if self.is_hovered else self.normal_color
        if self.is_clicked:
            color = COLORS["accent_blue_dark"]
        
        # 渐变效果
        for i in range(self.rect.height):
            alpha = 255 - int(50 * (i / self.rect.height))
            gradient_color = tuple(min(255, c + 20) for c in color[:3])
            pygame.draw.line(surface, gradient_color, 
                           (self.rect.x, self.rect.y + i),
                           (self.rect.x + self.rect.width, self.rect.y + i))
        
        # 按钮边框
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=10)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 1, border_radius=10)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        # 文字阴影
        shadow_surf = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def check_click(self, mouse_pos):
        if self.is_hovered and pygame.mouse.get_pressed()[0]:
            if not self.is_clicked:
                self.is_clicked = True
                self.click_timer = pygame.time.get_ticks()
                return True
        elif self.is_clicked:
            if pygame.time.get_ticks() - self.click_timer > 200:
                self.is_clicked = False
        return False

def draw_title(surface, text, y_pos, screen_width, font_big):
    """绘制带特效的标题"""
    # 发光效果
    for offset in range(5, 0, -1):
        alpha = 50 - offset * 8
        glow_surf = font_big.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    # 主标题
    title = font_big.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    
    # 阴影
    shadow = font_big.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)

def show_message(surface, message, font_main):
    """显示提示消息"""
    screen_width = surface.get_width()
    screen_height = surface.get_height()
    
    # 半透明遮罩
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))
    
    # 消息面板
    panel_width = 400
    panel_height = 150
    panel_x = (screen_width - panel_width) // 2
    panel_y = (screen_height - panel_height) // 2
    
    panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (40, 40, 70, 200), (0, 0, panel_width, panel_height), border_radius=15)
    surface.blit(panel_surf, (panel_x, panel_y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], 
                    (panel_x, panel_y, panel_width, panel_height), 3, border_radius=15)
    
    # 文字
    text_surf = font_main.render(message, True, COLORS["text_white"])
    text_rect = text_surf.get_rect(center=(screen_width // 2, panel_y + panel_height // 2))
    surface.blit(text_surf, text_rect)
    
    pygame.display.flip()
    pygame.time.wait(2000)

class LimitedTimeEvents:
    """限时活动系统"""
    def __init__(self):
        # 初始化限时活动数据
        if "limited_time_events" not in data:
            data["limited_time_events"] = {
                "active": [],  # 活跃的限时活动
                "completed": [],  # 已完成的限时活动
                "last_updated": datetime.datetime.now().isoformat()
            }
        
        # 预定义的限时活动
        self.events = [
            {
                "id": "event_spring_festival",
                "name": "春节限时活动",
                "description": "完成10次战斗，获得春节限定奖励",
                "duration": 7 * 24 * 60 * 60,  # 7天
                "objective": {"type": "battle_completed", "count": 10},
                "rewards": {"金元宝": 300, "春节限定皮肤": 1, "红包": 5},
                "start_time": None,
                "end_time": None,
                "status": "inactive",
                "progress": 0
            },
            {
                "id": "event_valentine",
                "name": "情人节限时活动",
                "description": "收集99朵玫瑰，获得情人节限定时装",
                "duration": 3 * 24 * 60 * 60,  # 3天
                "objective": {"type": "collect_rose", "count": 99},
                "rewards": {"金元宝": 200, "情人节时装": 1, "玫瑰": 99},
                "start_time": None,
                "end_time": None,
                "status": "inactive",
                "progress": 0
            },
            {
                "id": "event_summer_festival",
                "name": "夏季庆典活动",
                "description": "完成5次小游戏，获得夏季限定坐骑",
                "duration": 5 * 24 * 60 * 60,  # 5天
                "objective": {"type": "mini_game_played", "count": 5},
                "rewards": {"金元宝": 250, "夏季限定坐骑": 1, "西瓜": 100},
                "start_time": None,
                "end_time": None,
                "status": "inactive",
                "progress": 0
            },
            {
                "id": "event_anniversary",
                "name": "周年庆典活动",
                "description": "完成20次任务，获得周年限定武将",
                "duration": 10 * 24 * 60 * 60,  # 10天
                "objective": {"type": "quest_completed", "count": 20},
                "rewards": {"金元宝": 500, "周年限定武将": 1, "传说装备": 1},
                "start_time": None,
                "end_time": None,
                "status": "inactive",
                "progress": 0
            },
            {
                "id": "event_halloween",
                "name": "万圣节活动",
                "description": "收集50个南瓜灯，获得万圣节限定皮肤",
                "duration": 3 * 24 * 60 * 60,  # 3天
                "objective": {"type": "collect_pumpkin", "count": 50},
                "rewards": {"金元宝": 200, "万圣节皮肤": 1, "南瓜灯": 50},
                "start_time": None,
                "end_time": None,
                "status": "inactive",
                "progress": 0
            }
        ]
        
        # 初始化活动
        self.initialize_events()
        self.update_event_status()
    
    def initialize_events(self):
        """初始化活动"""
        # 检查是否需要初始化活动
        if not data["limited_time_events"]["active"]:
            # 随机激活一个活动
            event = random.choice(self.events)
            event["start_time"] = datetime.datetime.now().isoformat()
            event["end_time"] = (datetime.datetime.now() + datetime.timedelta(seconds=event["duration"])).isoformat()
            event["status"] = "active"
            event["progress"] = 0
            data["limited_time_events"]["active"].append(event)
            save()
    
    def update_event_status(self):
        """更新活动状态"""
        current_time = datetime.datetime.now()
        active_events = data["limited_time_events"]["active"].copy()
        
        for event in active_events:
            end_time = datetime.datetime.fromisoformat(event["end_time"])
            if current_time > end_time:
                # 活动结束
                event["status"] = "expired"
                data["limited_time_events"]["completed"].append(event)
                data["limited_time_events"]["active"].remove(event)
        
        # 检查是否需要激活新活动
        if not data["limited_time_events"]["active"]:
            # 随机激活一个新活动
            available_events = [e for e in self.events if not any(ce["id"] == e["id"] for ce in data["limited_time_events"]["completed"])]
            if available_events:
                event = random.choice(available_events)
                event["start_time"] = datetime.datetime.now().isoformat()
                event["end_time"] = (datetime.datetime.now() + datetime.timedelta(seconds=event["duration"])).isoformat()
                event["status"] = "active"
                event["progress"] = 0
                data["limited_time_events"]["active"].append(event)
        
        data["limited_time_events"]["last_updated"] = datetime.datetime.now().isoformat()
        save()
    
    def update_event_progress(self, event_type, **kwargs):
        """更新活动进度"""
        for event in data["limited_time_events"]["active"]:
            if event["status"] == "active":
                if event["objective"]["type"] == event_type:
                    event["progress"] += kwargs.get("count", 1)
                    
                    # 检查活动是否完成
                    if event["progress"] >= event["objective"]["count"]:
                        event["status"] = "completed"
                        self.claim_reward(event)
        
        self.update_event_status()
        save()
    
    def claim_reward(self, event):
        """领取活动奖励"""
        # 发放奖励
        for reward, amount in event["rewards"].items():
            if reward in data["resources"]:
                data["resources"][reward] = data["resources"].get(reward, 0) + amount
            else:
                # 处理特殊奖励（如皮肤、武将等）
                pass
        
        # 将活动移至已完成
        data["limited_time_events"]["completed"].append(event)
        data["limited_time_events"]["active"].remove(event)
        save()
    
    def get_active_events(self):
        """获取活跃的活动"""
        self.update_event_status()
        return data["limited_time_events"]["active"]
    
    def get_completed_events(self):
        """获取已完成的活动"""
        return data["limited_time_events"]["completed"]

def draw_countdown(surface, end_time, x, y, font_main):
    """绘制倒计时"""
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

def draw_event_details(screen, event, y_offset, screen_width, font_main, font_small):
    """绘制活动详情"""
    event_rect = pygame.Rect(50, y_offset, screen_width - 100, 120)
    
    # 背景
    if event["status"] == "completed":
        bg_color = (40, 70, 40, 200)
    elif event["status"] == "active":
        bg_color = (40, 40, 70, 200)
    else:
        bg_color = (70, 40, 40, 200)
    
    pygame.draw.rect(screen, bg_color, event_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS["accent_gold"], event_rect, 2, border_radius=10)
    
    # 活动信息
    name_surf = font_main.render(event["name"], True, COLORS["accent_gold"])
    desc_surf = font_small.render(event["description"], True, COLORS["text_white"])
    progress_surf = font_small.render(f"进度: {event['progress']}/{event['objective']['count']}", True, COLORS["text_gray"])
    
    screen.blit(name_surf, (60, y_offset + 10))
    screen.blit(desc_surf, (60, y_offset + 40))
    screen.blit(progress_surf, (60, y_offset + 70))
    
    # 倒计时
    if event["status"] == "active":
        draw_countdown(screen, event["end_time"], 60, y_offset + 90, font_small)
    
    # 奖励信息
    rewards_text = "奖励: " + ", ".join([f"{k}*{v}" for k, v in event["rewards"].items()])
    rewards_surf = font_small.render(rewards_text, True, (255, 210, 0))
    screen.blit(rewards_surf, (screen_width // 2, y_offset + 40))
    
    # 领取按钮
    if event["status"] == "completed":
        claim_btn = Button("领取奖励", screen_width - 150, y_offset + 40, 120, 50, font_small, normal_color=COLORS["accent_green"])
        claim_btn.draw(screen)
        return claim_btn
    
    return None

def main():
    """限时活动系统主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
        
        # 分辨率适配
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            # 使用设置的分辨率
            from ASSET.game_data import SETTINGS
            resolution = SETTINGS['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 1024
                SCREEN_HEIGHT = 768
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("限时活动")
        clock = pygame.time.Clock()

        # 字体初始化
        def init_font(size):
            return get_font(size)

        font_big = init_font(48)
        font_main = init_font(32)
        font_small = init_font(24)

        # 系统初始化
        event_system = LimitedTimeEvents()

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 标题
            draw_title(screen, "限时活动", SCREEN_HEIGHT * 0.1, SCREEN_WIDTH, font_big)
            
            # 导航按钮
            back_btn = Button("返回", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, font_small)
            back_btn.check_hover((mx, my))
            back_btn.draw(screen)
            
            # 活跃活动
            y_offset = SCREEN_HEIGHT * 0.2
            active_events = event_system.get_active_events()
            
            if active_events:
                active_title = font_main.render("进行中的活动", True, COLORS["accent_gold"])
                screen.blit(active_title, (50, y_offset))
                y_offset += 40
                
                claim_buttons = []
                for event in active_events:
                    claim_btn = draw_event_details(screen, event, y_offset, SCREEN_WIDTH, font_main, font_small)
                    if claim_btn:
                        claim_buttons.append((claim_btn, event))
                    y_offset += 130
            else:
                no_event_text = font_main.render("当前暂无限时活动，敬请期待！", True, COLORS["text_gray"])
                screen.blit(no_event_text, (50, y_offset))
            
            # 已完成活动
            completed_events = event_system.get_completed_events()
            if completed_events:
                y_offset += 30
                completed_title = font_main.render("已结束的活动", True, COLORS["text_gray"])
                screen.blit(completed_title, (50, y_offset))
                y_offset += 40
                
                for event in completed_events[-3:]:  # 只显示最近3个已完成的活动
                    draw_event_details(screen, event, y_offset, SCREEN_WIDTH, font_main, font_small)
                    y_offset += 130
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 处理返回按钮
                    if back_btn.rect.collidepoint(event.pos):
                        running = False
                    
                    # 处理领取按钮
                    for claim_btn, event_data in claim_buttons:
                        if claim_btn.rect.collidepoint(event.pos):
                            event_system.claim_reward(event_data)
                            show_message(screen, f"活动 {event_data['name']} 奖励已领取！", font_main)
            
            clock.tick(60)
        
        safe_exit("限时活动系统")
    except Exception as e:
        logger.info(f"异常：{str(e)}")
        logger.info("详细错误信息：")
        import traceback
        traceback.print_exc()
        safe_exit("限时活动系统", str(e))

if __name__ == "__main__":
    main()
