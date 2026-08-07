#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏背景故事介绍
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

# 背景故事内容
STORY_CHAPTERS = [
    {
        "title": "东汉末年，天下大乱",
        "content": "东汉末年，政治腐败，民不聊生。张角领导的黄巾起义爆发，天下陷入混乱。各地豪强纷纷崛起，形成了诸侯割据的局面。",
        "image": None
    },
    {
        "title": "群雄逐鹿，三国鼎立",
        "content": "在这个动荡的时代，曹操、刘备、孙权等英雄豪杰相继崛起。经过一系列的战争和政治斗争，最终形成了魏、蜀、吴三国鼎立的局面。",
        "image": None
    },
    {
        "title": "你的征程开始",
        "content": "你是一位胸怀大志的年轻君主，在这个乱世中崛起。你将招募武将，发展势力，与其他诸侯争夺天下霸权。",
        "image": None
    },
    {
        "title": "招募猛将，壮大势力",
        "content": "通过武将招募系统，你可以招募到关羽、张飞、赵云等三国名将。每个武将都有独特的技能和属性，合理搭配武将是取胜的关键。",
        "image": None
    },
    {
        "title": "发展经济，增强实力",
        "content": "除了军事力量，经济发展也至关重要。通过建筑系统和科技树，你可以提高资源产出，增强国家实力。",
        "image": None
    },
    {
        "title": "外交联盟，战略布局",
        "content": "在这个充满变数的时代，外交和战略同样重要。你可以与其他玩家联盟，共同对抗强敌，也可以使用谋略分化敌人。",
        "image": None
    },
    {
        "title": "统一天下，成就霸业",
        "content": "你的最终目标是统一中原，成就不世霸业。通过不断的征战和发展，你将逐步扩大势力范围，最终实现天下一统的梦想。",
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
    for i in range(10):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(1, 2)
        alpha = random.randint(20, 50)
        glow_surf = pygame.Surface((size * 8, size * 8), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, alpha), (size * 4, size * 4), size * 4)
        surface.blit(glow_surf, (x - size * 4, y - size * 4))

def main():
    """背景故事介绍主函数"""
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
    pygame.display.set_caption("游戏背景故事")
    clock = pygame.time.Clock()
    
    # 故事章节
    current_chapter = 0
    total_chapters = len(STORY_CHAPTERS)
    
    # 按钮设置
    button_width = 120
    button_height = 50
    
    # 创建按钮
    next_btn = Button("下一章", screen_width - button_width - 30, screen_height - button_height - 30, button_width, button_height, FONT_SMALL)
    prev_btn = Button("上一章", 30, screen_height - button_height - 30, button_width, button_height, FONT_SMALL)
    back_btn = Button("返回", screen_width // 2 - button_width // 2, screen_height - button_height - 30, button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
    
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
        
        # 绘制故事内容
        chapter = STORY_CHAPTERS[current_chapter]
        
        # 标题
        title_surf = FONT_BIG.render(chapter["title"], True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        screen.blit(title_surf, title_rect)
        
        # 内容
        content_lines = []
        words = chapter["content"].split()
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
        
        for i, line in enumerate(content_lines):
            content_surf = FONT_SMALL.render(line, True, (255, 255, 255))
            content_rect = content_surf.get_rect(center=(screen_width // 2, 220 + i * 40))
            screen.blit(content_surf, content_rect)
        
        # 章节指示器
        indicator_width = screen_width * 0.6
        indicator_height = 20
        indicator_x = (screen_width - indicator_width) // 2
        indicator_y = 140
        
        # 背景
        pygame.draw.rect(screen, (50, 50, 80), (indicator_x, indicator_y, indicator_width, indicator_height), border_radius=10)
        
        # 进度
        progress_width = indicator_width * (current_chapter + 1) / total_chapters
        pygame.draw.rect(screen, (255, 215, 0), (indicator_x, indicator_y, progress_width, indicator_height), border_radius=10)
        
        # 章节文字
        chapter_text = f"章节 {current_chapter + 1}/{total_chapters}"
        chapter_surf = FONT_SMALL.render(chapter_text, True, (255, 255, 255))
        chapter_rect = chapter_surf.get_rect(center=(screen_width // 2, indicator_y + indicator_height + 15))
        screen.blit(chapter_surf, chapter_rect)
        
        # 按钮
        mouse_pos = pygame.mouse.get_pos()
        next_btn.check_hover(mouse_pos)
        prev_btn.check_hover(mouse_pos)
        back_btn.check_hover(mouse_pos)
        
        # 控制按钮显示
        prev_btn.visible = current_chapter > 0
        next_btn.visible = current_chapter < total_chapters - 1
        back_btn.visible = True
        
        if prev_btn.visible:
            prev_btn.draw(screen)
        if next_btn.visible:
            next_btn.draw(screen)
        if back_btn.visible:
            back_btn.draw(screen)
        
        pygame.display.flip()
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if next_btn.visible and next_btn.rect.collidepoint(event.pos):
                    if current_chapter < total_chapters - 1:
                        current_chapter += 1
                
                elif prev_btn.visible and prev_btn.rect.collidepoint(event.pos):
                    if current_chapter > 0:
                        current_chapter -= 1
                
                elif back_btn.visible and back_btn.rect.collidepoint(event.pos):
                    running = False
        
        clock.tick(60)

if __name__ == '__main__':
    main()
