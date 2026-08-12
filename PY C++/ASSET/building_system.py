#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""建造系统 - 资源栏顶部绘制逻辑"""

import pygame
import json
import os
from ASSET.game_data import data, save, BUILDINGS, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
from ASSET.game_main_menu import Button, draw_gradient_background

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

# 字体变量
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None

def draw_title(surface, text, y_pos, screen_width):
    """绘制带特效的标题"""
    global FONT_BIG
    # 发光效果
    for offset in range(5, 0, -1):
        alpha = 50 - offset * 8
        glow_surf = FONT_BIG.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    # 主标题
    title = FONT_BIG.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    
    # 阴影
    shadow = FONT_BIG.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)
    
    # 装饰线
    line_y = y_pos + 40
    pygame.draw.line(surface, COLORS["accent_gold"], 
                    (screen_width // 2 - 150, line_y),
                    (screen_width // 2 - 50, line_y), 3)
    pygame.draw.line(surface, COLORS["accent_gold"],
                    (screen_width // 2 + 50, line_y),
                    (screen_width // 2 + 150, line_y), 3)
    # 中间装饰
    pygame.draw.circle(surface, COLORS["accent_gold"], (screen_width // 2, line_y), 8)
    pygame.draw.circle(surface, COLORS["bg_dark"], (screen_width // 2, line_y), 5)

def draw_resource_panel(surface, x, y, width, height):
    """绘制资源面板"""
    global FONT_SMALL
    panel_rect = pygame.Rect(x, y, width, height)
    
    # 面板背景
    panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (30, 30, 55, 180), (0, 0, width, height), border_radius=10)
    surface.blit(panel_surf, (x, y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], panel_rect, 2, border_radius=10)
    
    # 资源图标和文字
    resources = [
        ("金元宝", data['resources']['金元宝'], COLORS["accent_gold"]),
        ("水", data['resources']['水'], COLORS["accent_blue"]),
        ("食物", data['resources']['食物'], (200, 150, 100))
    ]
    
    spacing = width // max(1, len(resources))
    for i, (icon, value, color) in enumerate(resources):
        icon_x = x + i * spacing + spacing // 2
        icon_y = y + height // 2
        
        # 资源名称背景
        pygame.draw.rect(surface, (40, 40, 70), (icon_x - 40, icon_y - 12, 80, 24), border_radius=12)
        pygame.draw.rect(surface, color, (icon_x - 40, icon_y - 12, 80, 24), 2, border_radius=12)
        
        # 文字
        text = FONT_SMALL.render(f"{icon}: {value}", True, COLORS["text_white"])
        text_rect = text.get_rect(center=(icon_x, icon_y))
        surface.blit(text, text_rect)

def main():
    """建筑系统主函数"""
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG
    
    # 初始化pygame
    if not pygame.get_init():
        pygame.init()
    
    # 获取屏幕大小
    if 'ANDROID_DATA' in os.environ:
        # Android设备使用全屏
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        screen = pygame.display.set_mode((screen_width, screen_height))
    else:
        # PC设备
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
    
    pygame.display.set_caption("建筑系统")
    clock = pygame.time.Clock()
    
    # 初始化字体
    global FONT_MAIN, FONT_SMALL, FONT_BIG
    # 使用支持中文的字体
    font_name = get_system_font_name()
    try:
        if font_name:
            FONT_MAIN = pygame.font.SysFont(font_name, 40)
            FONT_SMALL = pygame.font.SysFont(font_name, 28)
            FONT_BIG = pygame.font.SysFont(font_name, 60)
        else:
            FONT_MAIN = pygame.font.Font(None, 40)
            FONT_SMALL = pygame.font.Font(None, 28)
            FONT_BIG = pygame.font.Font(None, 60)
    except Exception as _e:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 28)
        FONT_BIG = pygame.font.Font(None, 60)
    
    # 确保建筑数据存在
    if "buildings" not in data:
        data["buildings"] = {}
    
    # 主循环
    running = True
    while running:
        # 渐变背景
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        draw_title(screen, "建筑系统", screen_height * 0.1, screen_width)
        
        # 资源面板
        panel_width = min(500, screen_width * 0.7)
        draw_resource_panel(screen, (screen_width - panel_width) // 2, 
                          screen_height * 0.18, panel_width, 50)
        
        # 建筑列表
        building_items = []
        button_width = min(400, screen_width * 0.5)
        button_height = min(80, screen_height * 0.12)
        button_spacing = min(15, screen_height * 0.02)
        start_y = screen_height * 0.3
        
        for building_id, building_info in BUILDINGS.items():
            # 获取建筑当前等级
            current_level = data["buildings"].get(building_id, 0)
            max_level = len(building_info["levels"])
            
            # 计算下一级升级成本
            if current_level < max_level:
                next_level_cost = building_info["levels"][current_level]["cost"]
                can_afford = all(data["resources"].get(res, 0) >= cost for res, cost in next_level_cost.items())
            else:
                next_level_cost = None
                can_afford = False
            
            # 创建建筑按钮
            if current_level < max_level:
                cost_text = " + ".join([f"{cost}{res}" for res, cost in next_level_cost.items()])
                button_text = f"{building_info['name']} (Lv.{current_level})\n{building_info['description']}\n升级成本: {cost_text}"
            else:
                button_text = f"{building_info['name']} (Lv.{current_level})\n{building_info['description']}\n已达到最高等级"
            
            y = start_y + len(building_items) * (button_height + button_spacing)
            if y + button_height > screen_height - 50:
                break
            
            # 根据是否可以升级设置按钮颜色
            if current_level < max_level and can_afford:
                button_color = COLORS["accent_green"]
            elif current_level < max_level:
                button_color = COLORS["accent_red"]
            else:
                button_color = COLORS["accent_blue_dark"]
            
            btn = Button(
                button_text,
                (screen_width - button_width) // 2,
                y,
                button_width,
                button_height,
                FONT_SMALL,
                normal_color=button_color
            )
            building_items.append((btn, building_id))
        
        # 返回按钮
        back_btn = Button(
            "返回主菜单",
            screen_width - 200,
            screen_height - 60,
            180,
            50,
            FONT_SMALL,
            normal_color=COLORS["accent_blue_dark"]
        )
        
        # 鼠标位置
        mouse_pos = pygame.mouse.get_pos()
        
        # 检查按钮悬停
        for btn, _ in building_items:
            btn.check_hover(mouse_pos)
        back_btn.check_hover(mouse_pos)
        
        # 绘制按钮
        for btn, _ in building_items:
            btn.draw(screen)
        back_btn.draw(screen)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                pygame.quit()
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 处理建筑升级
                for btn, building_id in building_items:
                    if btn.check_click(mouse_pos):
                        current_level = data["buildings"].get(building_id, 0)
                        max_level = len(BUILDINGS[building_id]["levels"])
                        
                        if current_level < max_level:
                            next_level_cost = BUILDINGS[building_id]["levels"][current_level]["cost"]
                            can_afford = all(data["resources"].get(res, 0) >= cost for res, cost in next_level_cost.items())
                            
                            if can_afford:
                                # 扣除资源
                                for res, cost in next_level_cost.items():
                                    data["resources"][res] -= cost
                                
                                # 升级建筑
                                data["buildings"][building_id] = current_level + 1
                                
                                # 应用建筑效果
                                apply_building_effects()
                                
                                # 保存数据
                                save()
                
                # 处理返回按钮
                if back_btn.check_click(mouse_pos):
                    save()
                    return
        
        pygame.display.flip()
        clock.tick(60)

def apply_building_effects():
    """应用建筑效果"""
    # 重置所有建筑效果
    data["resource_bonus"] = 1.0
    data["hero_attack_bonus"] = 1.0
    data["hero_defense_bonus"] = 1.0
    data["research_speed_bonus"] = 1.0
    data["gold_bonus"] = 1.0
    
    # 应用每个建筑的效果
    for building_id, level in data["buildings"].items():
        if building_id in BUILDINGS and level > 0:
            building_info = BUILDINGS[building_id]
            if level <= len(building_info["levels"]):
                effect = building_info["levels"][level - 1]["effect"]
                
                # 应用效果
                for key, value in effect.items():
                    if key == "resource_bonus":
                        data["resource_bonus"] += value
                    elif key == "hero_attack":
                        if "hero_attack_bonus" not in data:
                            data["hero_attack_bonus"] = 1.0
                        data["hero_attack_bonus"] += value
                    elif key == "hero_defense":
                        if "hero_defense_bonus" not in data:
                            data["hero_defense_bonus"] = 1.0
                        data["hero_defense_bonus"] += value
                    elif key == "research_speed":
                        if "research_speed_bonus" not in data:
                            data["research_speed_bonus"] = 1.0
                        data["research_speed_bonus"] += value
                    elif key == "gold_bonus":
                        data["gold_bonus"] += value

if __name__ == "__main__":
    main()
