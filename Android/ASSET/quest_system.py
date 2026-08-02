import os
import pygame
import time
from datetime import datetime, timedelta
from ASSET.game_data import data, save, get_system_font_name
from ASSET.task_chain_system import TaskChainSystem
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
        self.hover = False
    
    def draw(self, surface):
        color = COLORS["btn_green_hover"] if self.hover else COLORS["btn_green"]
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

def draw_gradient_background(surface, color1, color2):
    """绘制渐变背景"""
    height = surface.get_height()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (surface.get_width(), y))

def main():
    """任务系统主界面"""
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG
    
    try:
        if not pygame.get_init():
            pygame.init()
        
        resolution = data['settings']['graphics']['resolution']
        try:
            width, height = map(int, resolution.split('x'))
        except ValueError:
            width, height = 800, 600
        
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("📋 任务系统")
        clock = pygame.time.Clock()
        
        # 加载字体
        font_name = get_system_font_name()
        try:
            FONT_MAIN = pygame.font.SysFont(font_name, 28)
            FONT_SMALL = pygame.font.SysFont(font_name, 22)
            FONT_BIG = pygame.font.SysFont(font_name, 36)
        except Exception:
            FONT_MAIN = pygame.font.Font(None, 28)
            FONT_SMALL = pygame.font.Font(None, 22)
            FONT_BIG = pygame.font.Font(None, 36)
        
        # 初始化任务系统
        task_system = TaskChainSystem()
        
        running = True
        selected_tab = "daily"  # daily, weekly, main
        
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 绘制背景
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 标题
            title_surf = FONT_BIG.render("📋 任务系统", True, COLORS["accent_gold"])
            title_rect = title_surf.get_rect(center=(width // 2, 40))
            screen.blit(title_surf, title_rect)
            
            # 标签页按钮
            tab_width = 120
            tab_height = 45
            tab_y = 100
            
            daily_btn = Button("每日任务", 50, tab_y, tab_width, tab_height, FONT_MAIN)
            weekly_btn = Button("每周任务", 180, tab_y, tab_width, tab_height, FONT_MAIN)
            main_btn = Button("主线任务", 310, tab_y, tab_width, tab_height, FONT_MAIN)
            
            daily_btn.update((mx, my))
            weekly_btn.update((mx, my))
            main_btn.update((mx, my))
            
            # 设置标签颜色
            if selected_tab == "daily":
                daily_btn.hover = True
            elif selected_tab == "weekly":
                weekly_btn.hover = True
            elif selected_tab == "main":
                main_btn.hover = True
            
            daily_btn.draw(screen)
            weekly_btn.draw(screen)
            main_btn.draw(screen)
            
            # 显示任务列表
            task_list_y = 160
            if selected_tab == "daily":
                tasks = task_system.daily_tasks_list
            elif selected_tab == "weekly":
                tasks = task_system.weekly_tasks_list
            else:
                tasks = []
            
            for i, task in enumerate(tasks[:6]):
                task_y = task_list_y + i * 80
                task_bg = pygame.Rect(50, task_y, width - 100, 70)
                pygame.draw.rect(screen, COLORS["panel_bg"], task_bg, border_radius=10)
                
                # 任务名称
                name_surf = FONT_MAIN.render(task.get("name", "未知任务"), True, COLORS["text_white"])
                screen.blit(name_surf, (70, task_y + 15))
                
                # 任务描述
                desc_surf = FONT_SMALL.render(task.get("description", ""), True, COLORS["text_gray"])
                screen.blit(desc_surf, (70, task_y + 40))
                
                # 任务进度
                progress = task_system.data["task_progress"].get(task.get("id", ""), 0)
                total = task.get("target", 1)
                progress_percent = min(100, int(progress / total * 100))
                
                progress_bg = pygame.Rect(width - 200, task_y + 25, 150, 20)
                pygame.draw.rect(screen, (50, 50, 70), progress_bg, border_radius=10)
                
                progress_fill = pygame.Rect(width - 200, task_y + 25, int(150 * progress_percent / 100), 20)
                pygame.draw.rect(screen, COLORS["accent_green"], progress_fill, border_radius=10)
                
                progress_text = FONT_SMALL.render(f"{progress}/{total}", True, COLORS["text_white"])
                screen.blit(progress_text, (width - 120, task_y + 25))
            
            # 返回按钮
            return_btn = Button("返回", width - 150, height - 60, 100, 45, FONT_MAIN)
            return_btn.update((mx, my))
            return_btn.draw(screen)
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if daily_btn.rect.collidepoint(mx, my):
                        selected_tab = "daily"
                    elif weekly_btn.rect.collidepoint(mx, my):
                        selected_tab = "weekly"
                    elif main_btn.rect.collidepoint(mx, my):
                        selected_tab = "main"
                    elif return_btn.rect.collidepoint(mx, my):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("任务系统")
    
    except Exception as e:
        safe_exit("任务系统", str(e))

if __name__ == "__main__":
    main()
