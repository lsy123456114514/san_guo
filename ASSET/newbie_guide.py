#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新手引导系统
"""
import os
import sys
import pygame
import math
import random
from ASSET.game_data import data, save
from ASSET.game_main_menu import Button, COLORS, init_fonts

# 全局变量
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None
screen = None
clock = None

# 引导步骤
GUIDE_STEPS = [
    {
        "title": "欢迎来到三国霸业",
        "content": "东汉末年，天下大乱，黄巾起义爆发，诸侯割据。你是一位胸怀大志的年轻君主，在这个动荡的时代崛起。你的目标是招募猛将，发展势力，最终统一中原，成就不世霸业。",
        "image": None
    },
    {
        "title": "游戏界面介绍",
        "content": "游戏主界面上方是资源面板，显示金元宝、木材、粮食等资源。中间是功能菜单，包含游戏核心、游戏系统、社交与排行、其他功能等下拉菜单。下方是保存、读取、设置和退出按钮。",
        "image": None
    },
    {
        "title": "游戏核心功能",
        "content": "点击'游戏核心'下拉菜单，可以进入PVP联机与其他玩家对战，游戏地图探索世界，3D地图体验立体场景，副本挑战获取稀有奖励。这些是游戏的核心玩法。",
        "image": None
    },
    {
        "title": "武将招募系统",
        "content": "在'游戏系统'中选择'武将招募'，花费金元宝招募强力武将。有普通、高级、传说三种招募方式，传说级武将如关羽、张飞、吕布等拥有超强能力，是你称霸中原的得力助手。",
        "image": None
    },
    {
        "title": "资源管理",
        "content": "金元宝是游戏中的通用货币，用于招募武将、购买物品。木材和粮食用于建筑和军队。资源可以通过任务、副本、社交系统获取。合理管理资源是发展势力的关键。",
        "image": None
    },
    {
        "title": "装备系统",
        "content": "在'游戏系统'中选择'装备系统'，可以为武将穿戴装备，提升属性。装备分为武器、防具、饰品等类型，品质从普通到传说不等。通过副本和活动可以获取高级装备。",
        "image": None
    },
    {
        "title": "宠物系统",
        "content": "宠物可以为你提供额外的属性加成和特殊技能。在'游戏系统'中选择'宠物系统'，可以孵化、培养和进化宠物。不同宠物有不同的技能和属性，合理搭配宠物可以大幅提升战斗力。",
        "image": None
    },
    {
        "title": "社交与排行榜",
        "content": "通过'社交与排行'，你可以查看个人成就，参与排行榜竞争，每日签到领取奖励，与其他玩家进行社交互动和交易。社交系统是游戏中获取资源和建立联盟的重要途径。",
        "image": None
    },
    {
        "title": "科技与建筑",
        "content": "科技树系统可以提升各种属性和解锁新功能。建筑系统可以建造和升级各种建筑，提高资源产出和军队实力。合理规划科技和建筑发展是长期发展的基础。",
        "image": None
    },
    {
        "title": "任务系统",
        "content": "任务系统提供各种目标和奖励，包括主线任务、支线任务、日常任务等。完成任务可以获得经验、资源和稀有物品。定期查看任务面板，完成任务是快速发展的捷径。",
        "image": None
    },
    {
        "title": "钓鱼与炼金",
        "content": "钓鱼系统可以获取各种鱼类和稀有物品。炼金系统可以制作药水和其他消耗品。这些休闲系统不仅有趣，还能为你提供额外的资源和物品。",
        "image": None
    },
    {
        "title": "游戏设置",
        "content": "在'其他功能'中选择'游戏设置'，可以调整分辨率、全屏模式、音效等设置。根据你的设备性能和个人喜好进行调整，获得最佳游戏体验。",
        "image": None
    },
    {
        "title": "开始你的征程",
        "content": "现在，你已经了解了游戏的基本功能和玩法。点击'游戏核心'中的'游戏地图'，开始你的三国征程吧！招募猛将，发展势力，与其他玩家竞争，最终统一中原，成就属于你的霸业！",
        "image": None
    }
]

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
        self.size = max(1, self.size - 0.1)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
        color = self.color[:3]
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

def draw_background(surface, width, height):
    """绘制背景"""
    # 渐变背景
    for y in range(height):
        ratio = y / height
        r = int(40 * (1 - ratio) + 20 * ratio)
        g = int(20 * (1 - ratio) + 10 * ratio)
        b = int(30 * (1 - ratio) + 40 * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    
    # 装饰光点
    for i in range(8):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(1, 2)
        alpha = random.randint(30, 60)
        glow_surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, alpha), (size * 3, size * 3), size * 3)
        surface.blit(glow_surf, (x - size * 3, y - size * 3))

def main():
    """新手引导系统主函数"""
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG
    
    # 确保pygame已导入
    import pygame
    
    # 初始化pygame
    if not pygame.get_init():
        pygame.init()
    
    # 初始化字体
    init_fonts()
    # 从game_main_menu模块导入已初始化的字体
    from ASSET.game_main_menu import FONT_MAIN as MAIN_FONT, FONT_SMALL as SMALL_FONT, FONT_BIG as BIG_FONT
    FONT_MAIN = MAIN_FONT
    FONT_SMALL = SMALL_FONT
    FONT_BIG = BIG_FONT
    
    # 获取当前屏幕大小
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    
    # 设置屏幕（保持当前分辨率）
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("新手引导")
    clock = pygame.time.Clock()
    
    # 引导步骤
    current_step = 0
    total_steps = len(GUIDE_STEPS)
    
    # 按钮设置
    button_width = 120
    button_height = 50
    
    # 创建按钮
    next_btn = Button("下一步", screen_width - button_width - 30, screen_height - button_height - 30, button_width, button_height, FONT_SMALL)
    prev_btn = Button("上一步", 30, screen_height - button_height - 30, button_width, button_height, FONT_SMALL)
    skip_btn = Button("跳过", screen_width // 2 - button_width // 2, screen_height - button_height - 30, button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
    
    # 装饰粒子
    particles = []
    
    running = True
    while running:
        # 绘制背景
        draw_background(screen, screen_width, screen_height)
        
        # 装饰粒子
        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                -10,
                (255, 215, 0),
                random.uniform(1, 2),
                random.randint(2, 4),
                random.randint(100, 150)
            ))
        
        for p in particles[:]:
            p.update()
            p.x += math.sin(p.y * 0.02) * 0.5
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)
        
        # 绘制引导内容
        step = GUIDE_STEPS[current_step]
        
        # 标题
        title_surf = FONT_BIG.render(step["title"], True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        screen.blit(title_surf, title_rect)
        
        # 内容
        content_lines = []
        words = step["content"].split()
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if FONT_SMALL.size(test_line)[0] > screen_width - 100:
                content_lines.append(current_line)
                current_line = word + " "
            else:
                current_line = test_line
        if current_line:
            content_lines.append(current_line)
        
        # 调整内容起始位置，确保不与步骤指示器重叠
        start_y = 220
        max_lines = (screen_height - start_y - 100) // 40  # 确保内容不超出屏幕
        display_lines = content_lines[:max_lines]
        
        for i, line in enumerate(display_lines):
            content_surf = FONT_SMALL.render(line, True, (255, 255, 255))
            content_rect = content_surf.get_rect(center=(screen_width // 2, start_y + i * 40))
            screen.blit(content_surf, content_rect)
        
        # 步骤指示器
        indicator_width = screen_width * 0.6
        indicator_height = 20
        indicator_x = (screen_width - indicator_width) // 2
        indicator_y = 140
        
        # 背景
        pygame.draw.rect(screen, (50, 50, 80), (indicator_x, indicator_y, indicator_width, indicator_height), border_radius=10)
        
        # 进度
        progress_width = indicator_width * (current_step + 1) / total_steps
        pygame.draw.rect(screen, (255, 215, 0), (indicator_x, indicator_y, progress_width, indicator_height), border_radius=10)
        
        # 步骤文字
        step_text = f"步骤 {current_step + 1}/{total_steps}"
        step_surf = FONT_SMALL.render(step_text, True, (255, 255, 255))
        step_rect = step_surf.get_rect(center=(screen_width // 2, indicator_y + indicator_height + 15))
        screen.blit(step_surf, step_rect)
        
        # 按钮
        mouse_pos = pygame.mouse.get_pos()
        next_btn.check_hover(mouse_pos)
        prev_btn.check_hover(mouse_pos)
        skip_btn.check_hover(mouse_pos)
        
        # 控制按钮显示
        prev_btn.visible = current_step > 0
        next_btn.visible = current_step < total_steps - 1
        skip_btn.visible = True
        
        if prev_btn.visible:
            prev_btn.draw(screen)
        if next_btn.visible:
            next_btn.draw(screen)
        if skip_btn.visible:
            skip_btn.draw(screen)
        
        pygame.display.flip()
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if next_btn.visible and next_btn.rect.collidepoint(event.pos):
                    if current_step < total_steps - 1:
                        current_step += 1
                
                elif prev_btn.visible and prev_btn.rect.collidepoint(event.pos):
                    if current_step > 0:
                        current_step -= 1
                
                elif skip_btn.visible and skip_btn.rect.collidepoint(event.pos):
                    # 标记引导完成
                    data["tutorial_completed"] = True
                    save()
                    running = False
                
                # 最后一步点击任意位置完成
                if current_step == total_steps - 1:
                    data["tutorial_completed"] = True
                    save()
                    running = False
        
        clock.tick(60)

if __name__ == '__main__':
    main()
