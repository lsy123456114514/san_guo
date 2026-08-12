"""钓鱼系统 - 等待上钩、时间任务、资源奖励"""

import os
import time
import pygame
import random
import datetime
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

class FishingSystem:
    """钓鱼系统"""
    def __init__(self):
        # 初始化钓鱼数据
        if "fishing" not in data:
            data["fishing"] = {
                "caught_fish": [],
                "fishing_rod": "普通鱼竿",
                "fishing_level": 1,
                "fishing_exp": 0
            }
        
        # 初始化鱼类列表
        self.fish_types = [
            {
                "name": "小金鱼",
                "rarity": "普通",
                "value": 10,
                "exp": 5,
                "catch_rate": 0.8
            },
            {
                "name": "鲈鱼",
                "rarity": "稀有",
                "value": 50,
                "exp": 15,
                "catch_rate": 0.4
            },
            {
                "name": "三文鱼",
                "rarity": "稀有",
                "value": 80,
                "exp": 20,
                "catch_rate": 0.3
            },
            {
                "name": "鲨鱼",
                "rarity": "史诗",
                "value": 200,
                "exp": 50,
                "catch_rate": 0.1
            },
            {
                "name": "金龙鱼",
                "rarity": "传说",
                "value": 500,
                "exp": 100,
                "catch_rate": 0.05
            }
        ]
        
        # 初始化钓鱼数据
        self.initialize_fishing()
    
    def initialize_fishing(self):
        """初始化钓鱼数据"""
        # 确保钓鱼数据存在
        if "fishing" not in data:
            data["fishing"] = {
                "caught_fish": [],
                "fishing_rod": "普通鱼竿",
                "fishing_level": 1,
                "fishing_exp": 0
            }
        
        save()
    
    def go_fishing(self):
        """钓鱼"""
        # 计算钓鱼时间
        base_time = data.get('settings', {}).get('time', {}).get('base_time', 60)
        time_required = base_time // 2  # 钓鱼时间为基础时间的一半
        
        # 创建时间任务
        task_id = f"fishing_{int(time.time())}"
        task = {
            "id": task_id,
            "type": "fishing",
            "start_time": time.time(),
            "end_time": time.time() + time_required,
            "status": "in_progress",
            "result": None
        }
        
        # 添加到时间任务列表
        if "time_tasks" not in data:
            data["time_tasks"] = {
                "active": [],
                "completed": []
            }
        if "active" not in data["time_tasks"]:
            data["time_tasks"]["active"] = []
        data["time_tasks"]["active"].append(task)
        
        # 保存数据
        save()
        
        return True, f"开始钓鱼，预计需要 {time_required} 秒..."
    
    def process_fishing_task(self, task):
        """处理钓鱼任务"""
        # 钓鱼过程中可能会钓到鱼
        caught_fish = []
        # 模拟钓鱼过程
        for _ in range(10):  # 模拟10次尝试
            # 随机决定是否钓到鱼
            if random.random() < 0.3:  # 30%的几率钓到鱼
                # 随机选择鱼的种类
                for fish in self.fish_types:
                    if random.random() < fish["catch_rate"]:
                        caught_fish.append(fish)
                        break
        
        # 处理钓到的鱼
        total_value = 0
        total_exp = 0
        for fish in caught_fish:
            total_value += fish["value"]
            total_exp += fish["exp"]
            
            # 添加到已钓到的鱼列表
            fish_data = {
                "name": fish["name"],
                "rarity": fish["rarity"],
                "value": fish["value"],
                "caught_at": datetime.datetime.now().isoformat()
            }
            data["fishing"]["caught_fish"].append(fish_data)
        
        # 增加钓鱼经验
        data["fishing"]["fishing_exp"] += total_exp
        
        # 检查是否升级
        self.check_level_up()
        
        # 增加金元宝
        data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + total_value
        
        # 保存数据
        save()
        
        if caught_fish:
            fish_names = [fish["name"] for fish in caught_fish]
            fish_list = ", ".join(fish_names)
            return f"钓到了：{fish_list}，获得 {total_value} 金元宝！"
        else:
            return "这次钓鱼没有收获。"
    
    def check_level_up(self):
        """检查是否升级"""
        level = data["fishing"]["fishing_level"]
        exp = data["fishing"]["fishing_exp"]
        
        # 升级所需经验
        required_exp = 100 * level
        
        if exp >= required_exp:
            # 升级
            data["fishing"]["fishing_level"] += 1
            data["fishing"]["fishing_exp"] -= required_exp
            
            # 升级鱼竿
            if data["fishing"]["fishing_level"] >= 5:
                data["fishing"]["fishing_rod"] = "高级鱼竿"
            elif data["fishing"]["fishing_level"] >= 10:
                data["fishing"]["fishing_rod"] = "大师鱼竿"
            
            save()
            return True
        
        return False
    
    def get_caught_fish(self):
        """获取已钓到的鱼"""
        return data["fishing"]["caught_fish"]
    
    def get_fishing_status(self):
        """获取钓鱼状态"""
        return {
            "level": data["fishing"]["fishing_level"],
            "exp": data["fishing"]["fishing_exp"],
            "rod": data["fishing"]["fishing_rod"],
            "total_caught": len(data["fishing"]["caught_fish"])
        }

def draw_fishing_system(screen, font_big, font_main, font_small):
    """绘制钓鱼系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "钓鱼系统", screen_height * 0.1, screen_width, font_big)
    
    fishing_system = FishingSystem()
    
    # 钓鱼状态
    y_offset = screen_height * 0.2
    status = fishing_system.get_fishing_status()
    
    status_title = font_main.render("钓鱼状态", True, COLORS["accent_gold"])
    screen.blit(status_title, (50, y_offset))
    y_offset += 40
    
    level_surf = font_small.render(f"钓鱼等级: {status['level']}", True, COLORS["text_white"])
    exp_surf = font_small.render(f"经验值: {status['exp']}", True, COLORS["text_white"])
    rod_surf = font_small.render(f"当前鱼竿: {status['rod']}", True, COLORS["text_white"])
    total_surf = font_small.render(f"总钓鱼数: {status['total_caught']}", True, COLORS["text_white"])
    
    screen.blit(level_surf, (60, y_offset))
    screen.blit(exp_surf, (60, y_offset + 30))
    screen.blit(rod_surf, (60, y_offset + 60))
    screen.blit(total_surf, (60, y_offset + 90))
    
    # 已钓到的鱼
    y_offset += 120
    fish_title = font_main.render("已钓到的鱼", True, COLORS["accent_blue"])
    screen.blit(fish_title, (50, y_offset))
    y_offset += 40
    
    caught_fish = fishing_system.get_caught_fish()
    if not caught_fish:
        empty_surf = font_small.render("暂无钓鱼记录", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        # 只显示最近10条记录
        recent_fish = caught_fish[-10:]
        for fish in reversed(recent_fish):
            fish_rect = pygame.Rect(50, y_offset, screen_width - 100, 60)
            
            # 背景
            if fish["rarity"] == "普通":
                bg_color = (40, 40, 70, 200)
                border_color = COLORS["text_white"]
            elif fish["rarity"] == "稀有":
                bg_color = (40, 60, 70, 200)
                border_color = COLORS["accent_blue"]
            elif fish["rarity"] == "史诗":
                bg_color = (60, 40, 70, 200)
                border_color = COLORS["accent_purple"]
            else:  # 传说
                bg_color = (70, 60, 40, 200)
                border_color = COLORS["accent_gold"]
            
            pygame.draw.rect(screen, bg_color, fish_rect, border_radius=10)
            pygame.draw.rect(screen, border_color, fish_rect, 2, border_radius=10)
            
            # 鱼的信息
            name_surf = font_main.render(fish["name"], True, border_color)
            value_surf = font_small.render(f"价值: {fish['value']} 金元宝", True, COLORS["text_white"])
            
            screen.blit(name_surf, (60, y_offset + 10))
            screen.blit(value_surf, (60, y_offset + 35))
            
            y_offset += 70

def main():
    """钓鱼系统主函数"""
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
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 900
                SCREEN_HEIGHT = 700
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("钓鱼系统")
        clock = pygame.time.Clock()

        # 字体初始化（根据屏幕大小自适应）
        def init_font(size):
            return get_font(size)

        font_big = init_font(48)
        font_main = init_font(32)
        font_small = init_font(24)

        # 系统初始化
        fishing_system = FishingSystem()

        # 创建按钮
        back_btn = Button("返回", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, font_small)
        fish_btn = Button("开始钓鱼", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 150, 200, 60, font_main, normal_color=COLORS["accent_green"])
        
        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 检查时间任务
            if "time_tasks" in data and "active" in data["time_tasks"]:
                completed_tasks = []
                for task in data["time_tasks"]["active"]:
                    if task["status"] == "in_progress" and time.time() >= task["end_time"]:
                        # 处理钓鱼任务
                        if task["type"] == "fishing":
                            result = fishing_system.process_fishing_task(task)
                            show_message(screen, result, font_main)
                        # 标记任务为已完成
                        task["status"] = "completed"
                        task["result"] = result
                        completed_tasks.append(task)
                
                # 移除已完成的任务
                data["time_tasks"]["active"] = [task for task in data["time_tasks"]["active"] if task["status"] != "completed"]
                if completed_tasks:
                    # 将已完成的任务添加到completed列表
                    if "completed" not in data["time_tasks"]:
                        data["time_tasks"]["completed"] = []
                    data["time_tasks"]["completed"].extend(completed_tasks)
                    save()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 绘制钓鱼系统
            draw_fishing_system(screen, font_big, font_main, font_small)
            
            # 检查按钮悬停
            back_btn.check_hover((mx, my))
            fish_btn.check_hover((mx, my))
            
            # 绘制按钮
            back_btn.draw(screen)
            fish_btn.draw(screen)
            
            # 显示当前时间任务
            if "time_tasks" in data and "active" in data["time_tasks"] and data["time_tasks"]["active"]:
                y_offset = 50
                for task in data["time_tasks"]["active"]:
                    if task["status"] == "in_progress":
                        # 计算进度
                        total_time = task["end_time"] - task["start_time"]
                        elapsed_time = time.time() - task["start_time"]
                        if total_time <= 0:
                            logger.warning("[钓鱼] 时间任务 total_time=%s 异常，进度置 1.0", total_time)
                            progress = 1.0
                        else:
                            progress = min(1.0, elapsed_time / total_time)
                        remaining_time = max(0, int(task["end_time"] - time.time()))
                        
                        # 显示任务文本背景
                        task_text = f"钓鱼中... 剩余 {remaining_time} 秒"
                        text_surface = font_small.render(task_text, True, (255, 255, 255))
                        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                        # 绘制背景矩形，清除旧的文本
                        bg_rect = text_rect.inflate(20, 10)
                        pygame.draw.rect(screen, COLORS["bg_dark"], bg_rect, border_radius=5)
                        screen.blit(text_surface, text_rect)
                        
                        # 显示进度条
                        progress_bar_width = SCREEN_WIDTH * 0.6
                        progress_bar_height = 20
                        progress_bar_x = (SCREEN_WIDTH - progress_bar_width) // 2
                        progress_bar_y = y_offset + 30
                        
                        # 绘制进度条背景
                        pygame.draw.rect(screen, (50, 50, 50), (
                            progress_bar_x, progress_bar_y, 
                            progress_bar_width, progress_bar_height
                        ), border_radius=10)
                        
                        # 绘制进度条填充
                        filled_width = int(progress_bar_width * progress)
                        pygame.draw.rect(screen, COLORS["accent_green"], (
                            progress_bar_x, progress_bar_y, 
                            filled_width, progress_bar_height
                        ), border_radius=10)
                        
                        # 绘制进度条边框
                        pygame.draw.rect(screen, (100, 100, 100), (
                            progress_bar_x, progress_bar_y, 
                            progress_bar_width, progress_bar_height
                        ), 2, border_radius=10)
                        
                        y_offset += 80
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 处理返回按钮
                    if back_btn.rect.collidepoint(event.pos):
                        running = False
                    # 处理钓鱼按钮
                    if fish_btn.rect.collidepoint(event.pos):
                        success, message = fishing_system.go_fishing()
                        show_message(screen, message, font_main)
            
            clock.tick(60)
        
        safe_exit("钓鱼系统")
    except Exception as e:
        logger.info(f"异常：{str(e)}")
        logger.info("详细错误信息：")
        import traceback
        traceback.print_exc()
        safe_exit("钓鱼系统", str(e))

if __name__ == "__main__":
    main()
