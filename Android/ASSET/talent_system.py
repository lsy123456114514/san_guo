#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天赋系统 - 天赋树加点与属性加成"""

import pygame
import os
from ASSET.game_data import data, save, TALENT_TREE, get_system_font_name, create_font, logger, draw_gradient_bg, cull_dead, get_font
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
    """天赋系统主函数"""
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
        # PC设备：复用当前显示表面，避免改分辨率导致返回错位
        cur_surface = pygame.display.get_surface()
        if cur_surface is not None:
            screen_width, screen_height = cur_surface.get_size()
            screen = cur_surface
        else:
            screen_width, screen_height = 800, 600
            screen = pygame.display.set_mode((screen_width, screen_height))
    
    pygame.display.set_caption("天赋系统")
    clock = pygame.time.Clock()
    
    # 初始化字体
    global FONT_MAIN, FONT_SMALL, FONT_BIG
    # 使用支持中文的字体
    try:
        FONT_MAIN = get_font(40)
        FONT_SMALL = get_font(28)
        FONT_BIG = get_font(60)
    except Exception as _e:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 28)
        FONT_BIG = pygame.font.Font(None, 60)
    
    # 确保天赋数据存在
    if "talents" not in data:
        data["talents"] = {
            "points": 0,
            "unlocked": []
        }
    
    # 主循环
    running = True
    while running:
        # 渐变背景
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        draw_title(screen, "天赋系统", screen_height * 0.1, screen_width)
        
        # 资源面板
        panel_width = min(500, screen_width * 0.7)
        draw_resource_panel(screen, (screen_width - panel_width) // 2, 
                          screen_height * 0.18, panel_width, 50)
        
        # 天赋点数显示
        talent_points = data["talents"].get("points", 0)
        points_text = f"可用天赋点: {talent_points}"
        points_surf = FONT_MAIN.render(points_text, True, COLORS["accent_gold"])
        screen.blit(points_surf, (screen_width // 2 - points_surf.get_width() // 2, screen_height * 0.25))

        # 天赋点来源提示
        tip_surf = FONT_SMALL.render("天赋点来源：每日签到 +1，武将招募成功 +1", True, COLORS["text_gray"])
        screen.blit(tip_surf, (screen_width // 2 - tip_surf.get_width() // 2, screen_height * 0.25 + 30))
        
        # 天赋树
        talent_items = []
        button_width = min(350, screen_width * 0.45)
        button_height = min(70, screen_height * 0.1)
        button_spacing = min(10, screen_height * 0.015)
        start_y = screen_height * 0.35
        
        # 绘制每个天赋类别
        category_y = start_y
        for category_id, category_info in TALENT_TREE.items():
            # 类别标题
            category_text = f"{category_info['name']}: {category_info['description']}"
            category_surf = FONT_MAIN.render(category_text, True, COLORS["accent_blue"])
            screen.blit(category_surf, (screen_width // 2 - category_surf.get_width() // 2, category_y))
            category_y += 40
            
            # 类别下的天赋
            for talent in category_info["talents"]:
                # 检查天赋是否已解锁
                is_unlocked = talent["id"] in data["talents"].get("unlocked", [])
                
                # 计算是否可以解锁
                can_unlock = not is_unlocked and talent["cost"] <= talent_points
                
                # 创建天赋按钮
                button_text = f"{talent['name']}\n{talent['description']}\n消耗: {talent['cost']}点"
                if is_unlocked:
                    button_text += " (已解锁)"
                
                y = category_y + len(talent_items) * (button_height + button_spacing)
                if y + button_height > screen_height - 50:
                    break
                
                # 根据状态设置按钮颜色
                if is_unlocked:
                    button_color = COLORS["accent_green"]
                elif can_unlock:
                    button_color = COLORS["accent_blue"]
                else:
                    button_color = COLORS["accent_red"]
                
                btn = Button(
                    button_text,
                    (screen_width - button_width) // 2,
                    y,
                    button_width,
                    button_height,
                    FONT_SMALL,
                    normal_color=button_color
                )
                talent_items.append((btn, talent))
            
            category_y += len(category_info["talents"]) * (button_height + button_spacing) + 20
        
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
        for btn, _ in talent_items:
            btn.check_hover(mouse_pos)
        back_btn.check_hover(mouse_pos)
        
        # 绘制按钮
        for btn, _ in talent_items:
            btn.draw(screen)
        back_btn.draw(screen)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 处理天赋解锁
                for btn, talent in talent_items:
                    if btn.check_click(mouse_pos):
                        is_unlocked = talent["id"] in data["talents"].get("unlocked", [])
                        can_unlock = not is_unlocked and talent["cost"] <= data["talents"].get("points", 0)
                        
                        if can_unlock:
                            # 扣除天赋点
                            data["talents"]["points"] -= talent["cost"]
                            
                            # 解锁天赋
                            if "unlocked" not in data["talents"]:
                                data["talents"]["unlocked"] = []
                            data["talents"]["unlocked"].append(talent["id"])
                            
                            # 应用天赋效果
                            apply_talent_effects()
                            
                            # 保存数据
                            save()
                
                # 处理返回按钮
                if back_btn.check_click(mouse_pos):
                    save()
                    return
        
        pygame.display.flip()
        clock.tick(60)

def apply_talent_effects():
    """应用天赋效果"""
    # 重置所有天赋效果
    data["talent_effects"] = {}
    
    # 应用每个解锁的天赋
    for talent_id in data["talents"].get("unlocked", []):
        # 查找天赋
        for category_info in TALENT_TREE.values():
            for talent in category_info["talents"]:
                if talent["id"] == talent_id:
                    # 应用天赋效果
                    for key, value in talent["effect"].items():
                        if key not in data["talent_effects"]:
                            data["talent_effects"][key] = 0
                        data["talent_effects"][key] += value
                    break

if __name__ == "__main__":
    main()
