"""炼丹系统 - 资源合成、丹药炼制与冷却"""

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

class AlchemySystem:
    """炼金系统"""
    def __init__(self):
        # 初始化炼金数据
        if "alchemy" not in data:
            data["alchemy"] = {
                "recipes": [],
                "potions": []
            }
        
        # 初始化配方列表
        self.recipes = [
            {
                "id": "potion_health",
                "name": "生命药水",
                "type": "potion",
                "ingredients": {
                    "水": 2,
                    "食物": 1
                },
                "effect": {"health": 50},
                "time": 60,  # 制作时间（秒）
                "unlocked": True
            },
            {
                "id": "potion_mana",
                "name": "魔法药水",
                "type": "potion",
                "ingredients": {
                    "水": 2,
                    "煤炭": 1
                },
                "effect": {"mana": 50},
                "time": 60,
                "unlocked": True
            },
            {
                "id": "potion_strength",
                "name": "力量药水",
                "type": "potion",
                "ingredients": {
                    "水": 2,
                    "木头": 1
                },
                "effect": {"strength": 10},
                "time": 90,
                "unlocked": False
            },
            {
                "id": "potion_speed",
                "name": "速度药水",
                "type": "potion",
                "ingredients": {
                    "水": 2,
                    "金元宝": 1
                },
                "effect": {"speed": 10},
                "time": 90,
                "unlocked": False
            }
        ]
        
        # 初始化炼金数据
        self.initialize_alchemy()
    
    def initialize_alchemy(self):
        """初始化炼金数据"""
        # 初始化配方
        if not data["alchemy"]["recipes"]:
            data["alchemy"]["recipes"] = self.recipes.copy()
        
        # 初始化药水
        if not data["alchemy"]["potions"]:
            data["alchemy"]["potions"] = []
        
        save()
    
    def has_ingredients(self, recipe):
        """检查是否有足够的材料"""
        for ingredient, amount in recipe["ingredients"].items():
            if data["resources"].get(ingredient, 0) < amount:
                return False
        return True
    
    def craft_potion(self, recipe_id):
        """制作药水"""
        for recipe in data["alchemy"]["recipes"]:
            if recipe["id"] == recipe_id and recipe["unlocked"]:
                if self.has_ingredients(recipe):
                    # 消耗材料
                    for ingredient, amount in recipe["ingredients"].items():
                        data["resources"][ingredient] -= amount
                    
                    # 计算制作时间
                    base_time = data.get('settings', {}).get('time', {}).get('base_time', 60)
                    time_required = recipe["time"]
                    
                    # 创建时间任务
                    task = {
                        "id": f"task_{time.time()}",
                        "type": "craft_potion",
                        "recipe_id": recipe_id,
                        "recipe_name": recipe["name"],
                        "effect": recipe["effect"],
                        "start_time": time.time(),
                        "end_time": time.time() + time_required,
                        "status": "active"
                    }
                    
                    # 添加到时间任务
                    if "time_tasks" not in data:
                        data["time_tasks"] = {
                            "active": [],
                            "completed": []
                        }
                    
                    data["time_tasks"]["active"].append(task)
                    save()
                    return True, f"药水制作已开始，需要 {int(time_required)} 秒"
                else:
                    return False, "材料不足"
        return False, "配方不存在或未解锁"
    
    def use_potion(self, potion_id):
        """使用药水"""
        for potion in data["alchemy"]["potions"]:
            if potion["id"] == potion_id:
                # 应用药水效果
                for effect, value in potion["effect"].items():
                    # 这里可以添加药水效果的具体实现
                    pass
                
                # 移除药水
                data["alchemy"]["potions"].remove(potion)
                save()
                return True, f"使用了 {potion['name']}"
        return False, "药水不存在"
    
    def get_unlocked_recipes(self):
        """获取已解锁的配方"""
        return [recipe for recipe in data["alchemy"]["recipes"] if recipe["unlocked"]]
    
    def get_potions(self):
        """获取所有药水"""
        return data["alchemy"]["potions"]

def draw_alchemy_system(screen, font_big, font_main, font_small):
    """绘制炼金系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "炼金系统", screen_height * 0.1, screen_width, font_big)
    
    alchemy_system = AlchemySystem()
    
    # 配方列表
    y_offset = screen_height * 0.2
    
    # 已解锁的配方
    recipes_title = font_main.render("可制作的药水", True, COLORS["accent_gold"])
    screen.blit(recipes_title, (50, y_offset))
    y_offset += 40
    
    unlocked_recipes = alchemy_system.get_unlocked_recipes()
    if not unlocked_recipes:
        empty_surf = font_small.render("暂无解锁的配方", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for recipe in unlocked_recipes:
            recipe_rect = pygame.Rect(50, y_offset, screen_width - 100, 100)
            
            # 背景
            pygame.draw.rect(screen, (40, 40, 70, 200), recipe_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["accent_gold"], recipe_rect, 2, border_radius=10)
            
            # 配方信息
            name_surf = font_main.render(recipe["name"], True, COLORS["accent_gold"])
            ingredients_text = "材料: " + ", ".join([f"{k} x{v}" for k, v in recipe["ingredients"].items()])
            ingredients_surf = font_small.render(ingredients_text, True, COLORS["text_white"])
            effect_text = "效果: " + ", ".join([f"{k}:+{v}" for k, v in recipe["effect"].items()])
            effect_surf = font_small.render(effect_text, True, COLORS["text_white"])
            time_surf = font_small.render(f"制作时间: {recipe['time']}秒", True, COLORS["text_gray"])
            
            screen.blit(name_surf, (60, y_offset + 10))
            screen.blit(ingredients_surf, (60, y_offset + 35))
            screen.blit(effect_surf, (60, y_offset + 60))
            screen.blit(time_surf, (60, y_offset + 85))
            
            # 制作按钮
            craft_btn = Button("制作", screen_width - 150, y_offset + 30, 100, 40, font_small, normal_color=COLORS["accent_green"])
            craft_btn.draw(screen)
            
            y_offset += 110
    
    # 药水列表
    y_offset += 20
    potions_title = font_main.render("我的药水", True, COLORS["accent_blue"])
    screen.blit(potions_title, (50, y_offset))
    y_offset += 40
    
    potions = alchemy_system.get_potions()
    if not potions:
        empty_surf = font_small.render("暂无药水", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for potion in potions:
            potion_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
            
            # 背景
            pygame.draw.rect(screen, (40, 40, 70, 200), potion_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["accent_blue"], potion_rect, 2, border_radius=10)
            
            # 药水信息
            name_surf = font_main.render(potion["name"], True, COLORS["accent_blue"])
            effect_text = "效果: " + ", ".join([f"{k}:+{v}" for k, v in potion["effect"].items()])
            effect_surf = font_small.render(effect_text, True, COLORS["text_white"])
            
            screen.blit(name_surf, (60, y_offset + 10))
            screen.blit(effect_surf, (60, y_offset + 40))
            
            # 使用按钮
            use_btn = Button("使用", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
            use_btn.draw(screen)
            
            y_offset += 90

def main():
    """炼金系统主函数"""
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
        pygame.display.set_caption("炼金系统")
        clock = pygame.time.Clock()

        # 字体初始化（根据屏幕大小自适应）
        def init_font(size):
            return get_font(size)

        font_big = init_font(48)
        font_main = init_font(32)
        font_small = init_font(24)

        # 系统初始化
        alchemy_system = AlchemySystem()

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 处理时间任务
            current_time = time.time()
            completed_tasks = []
            
            if "time_tasks" in data:
                for task in data["time_tasks"]["active"]:
                    if current_time >= task["end_time"]:
                        # 任务完成，执行相应操作
                        if task["type"] == "craft_potion":
                            # 制作药水完成
                            potion = {
                                "id": f"potion_{time.time()}",
                                "name": task["recipe_name"],
                                "effect": task["effect"],
                                "created_at": datetime.datetime.now().isoformat()
                            }
                            data["alchemy"]["potions"].append(potion)
                            show_message(screen, f"药水 {task['recipe_name']} 制作完成！", font_main)
                        
                        # 标记任务为已完成
                        task["status"] = "completed"
                        completed_tasks.append(task)
            
            # 移动已完成的任务到completed列表
            if "time_tasks" in data:
                for task in completed_tasks:
                    data["time_tasks"]["active"].remove(task)
                    data["time_tasks"]["completed"].append(task)
            
            # 保存数据
            if completed_tasks:
                save()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 导航按钮
            back_btn = Button("返回", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, font_small)
            back_btn.check_hover((mx, my))
            back_btn.draw(screen)
            
            # 绘制炼金系统
            draw_alchemy_system(screen, font_big, font_main, font_small)
            
            # 绘制时间任务状态
            if "time_tasks" in data and data["time_tasks"]["active"]:
                task_y = 50
                for task in data["time_tasks"]["active"]:
                    if task["type"] == "craft_potion":
                        remaining_time = max(0, int(task["end_time"] - current_time))
                        task_text = f"制作 {task['recipe_name']}: {remaining_time}秒"
                        task_surf = font_small.render(task_text, True, COLORS["accent_gold"])
                        screen.blit(task_surf, (SCREEN_WIDTH - 300, task_y))
                        task_y += 30
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 处理返回按钮
                    if back_btn.rect.collidepoint(event.pos):
                        running = False
                    
                    # 处理制作按钮
                    y_offset = SCREEN_HEIGHT * 0.2 + 40
                    for recipe in alchemy_system.get_unlocked_recipes():
                        craft_btn = Button("制作", SCREEN_WIDTH - 150, y_offset + 30, 100, 40, font_small)
                        if craft_btn.rect.collidepoint(event.pos):
                            success, message = alchemy_system.craft_potion(recipe["id"])
                            show_message(screen, message, font_main)
                        y_offset += 110
                    
                    # 处理使用按钮
                    y_offset = SCREEN_HEIGHT * 0.2 + 40 + len(alchemy_system.get_unlocked_recipes()) * 110 + 20 + 40
                    for potion in alchemy_system.get_potions():
                        use_btn = Button("使用", SCREEN_WIDTH - 150, y_offset + 20, 100, 40, font_small)
                        if use_btn.rect.collidepoint(event.pos):
                            success, message = alchemy_system.use_potion(potion["id"])
                            show_message(screen, message, font_main)
                        y_offset += 90
            
            clock.tick(60)
        
        safe_exit("炼金系统")
    except Exception as e:
        logger.info(f"异常：{str(e)}")
        logger.info("详细错误信息：")
        import traceback
        traceback.print_exc()
        safe_exit("炼金系统", str(e))

if __name__ == "__main__":
    main()
