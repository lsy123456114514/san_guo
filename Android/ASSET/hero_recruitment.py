#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武将招募系统
"""
import os
import sys
import pygame
import random
import math
from ASSET.game_data import data, save, logger, draw_gradient_bg, cull_dead, get_font
from ASSET.game_main_menu import Button, COLORS, init_fonts

# 全局变量
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None
screen = None
clock = None

# 武将品质
HERO_QUALITY = {
    "common": {"name": "普通", "color": (150, 150, 150), "probability": 60},
    "rare": {"name": "稀有", "color": (70, 130, 180), "probability": 30},
    "epic": {"name": "史诗", "color": (128, 0, 128), "probability": 8},
    "legendary": {"name": "传说", "color": (255, 215, 0), "probability": 2}
}

# 武将列表
HERO_LIST = {
    "common": [
        {"name": "廖化", "skill": "先锋", "description": "蜀汉老将，忠心耿耿"},
        {"name": "周仓", "skill": "护卫", "description": "关羽的部将，力大无穷"},
        {"name": "马岱", "skill": "骑射", "description": "马超的堂弟，擅长骑术"},
        {"name": "关平", "skill": "刀法", "description": "关羽之子，勇猛善战"},
        {"name": "张苞", "skill": "矛术", "description": "张飞之子，继承父业"}
    ],
    "rare": [
        {"name": "黄忠", "skill": "百步穿杨", "description": "蜀汉五虎上将之一，箭术无双"},
        {"name": "魏延", "skill": "奇袭", "description": "蜀汉大将，勇猛过人"},
        {"name": "甘宁", "skill": "水战", "description": "东吴猛将，水性极佳"},
        {"name": "周泰", "skill": "守护", "description": "东吴将领，忠勇可嘉"},
        {"name": "徐晃", "skill": "斧法", "description": "曹魏名将，治军严谨"}
    ],
    "epic": [
        {"name": "赵云", "skill": "龙胆亮枪", "description": "蜀汉五虎上将之一，常胜将军"},
        {"name": "马超", "skill": "西凉铁骑", "description": "蜀汉五虎上将之一，锦马超"},
        {"name": "典韦", "skill": "力拔山兮", "description": "曹魏猛将，忠勇护主"},
        {"name": "太史慈", "skill": "神亭岭", "description": "东吴名将，箭术精湛"},
        {"name": "颜良", "skill": "快刀", "description": "袁绍麾下大将，勇冠三军"}
    ],
    "legendary": [
        {"name": "关羽", "skill": "青龙偃月", "description": "武圣，蜀汉五虎上将之首"},
        {"name": "张飞", "skill": "丈八蛇矛", "description": "猛张飞，蜀汉五虎上将之一"},
        {"name": "吕布", "skill": "方天画戟", "description": "人中吕布，马中赤兔"},
        {"name": "诸葛亮", "skill": "空城计", "description": "卧龙，智谋无双"},
        {"name": "周瑜", "skill": "火烧赤壁", "description": "东吴大都督，英姿飒爽"}
    ]
}

# 招募消耗
RECRUIT_COST = {
    "normal": {"金元宝": 100},
    "advanced": {"金元宝": 500},
    "legendary": {"金元宝": 2000}
}

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
        alpha = int(255 * (self.life / self.max_life))
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
    
    # 静态装饰图案（不移动物品）
    for i in range(5):
        x = 50 + i * 150
        y = 50
        size = 2
        alpha = 40
        glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, alpha), (size * 2, size * 2), size * 2)
        surface.blit(glow_surf, (x - size * 2, y - size * 2))
    
    for i in range(5):
        x = 50 + i * 150
        y = height - 60
        size = 2
        alpha = 40
        glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, alpha), (size * 2, size * 2), size * 2)
        surface.blit(glow_surf, (x - size * 2, y - size * 2))

def recruit_hero(recruit_type):
    """招募武将"""
    # 检查资源
    cost = RECRUIT_COST[recruit_type]
    for resource, amount in cost.items():
        if data['resources'].get(resource, 0) < amount:
            return None, f"资源不足！需要{amount}{resource}"
    
    # 扣除资源
    for resource, amount in cost.items():
        data['resources'][resource] -= amount
    save()
    
    # 确定武将品质
    quality = None
    rand = random.randint(1, 100)
    cumulative = 0
    
    for q, info in HERO_QUALITY.items():
        cumulative += info['probability']
        if rand <= cumulative:
            quality = q
            break
    
    # 随机选择武将
    hero_pool = HERO_LIST[quality]
    hero = random.choice(hero_pool)
    
    # 生成武将数据
    hero_data = {
        "name": hero["name"],
        "quality": quality,
        "skill": hero["skill"],
        "description": hero["description"],
        "level": 1,
        "experience": 0,
        "attack": random.randint(50, 100) * (1 + HERO_QUALITY[quality]["probability"] / 20),
        "defense": random.randint(30, 80) * (1 + HERO_QUALITY[quality]["probability"] / 20),
        "health": random.randint(100, 200) * (1 + HERO_QUALITY[quality]["probability"] / 20),
        "loyalty": 100
    }
    
    # 添加到武将仓库
    if "heroes" not in data:
        data["heroes"] = []
    data["heroes"].append(hero_data)
    save()
    
    return hero_data, f"成功招募到{HERO_QUALITY[quality]['name']}武将：{hero['name']}"

def show_recruit_animation(hero_data):
    """显示招募动画"""
    global screen, clock
    width, height = screen.get_size()
    particles = []
    
    # 动画时长
    start_time = pygame.time.get_ticks()
    duration = 3000
    
    while pygame.time.get_ticks() - start_time < duration:
        # 处理事件，防止卡死
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        
        draw_background(screen, width, height)
        
        # 生成粒子（减少生成频率，提高性能）
        if random.random() < 0.15:
            particles.append(Particle(
                width // 2,
                height // 2,
                HERO_QUALITY[hero_data['quality']]['color'],
                random.uniform(1, 2),
                random.randint(2, 4),
                random.randint(40, 80)
            ))
        
        # 更新和绘制粒子
        for p in particles[:]:
            p.update()
            p.draw(screen)
        
        # 绘制武将信息
        if pygame.time.get_ticks() - start_time > 1000:
            # 品质颜色
            quality_color = HERO_QUALITY[hero_data['quality']]['color']
            
            # 武将名称
            name_surf = FONT_BIG.render(hero_data['name'], True, quality_color)
            name_rect = name_surf.get_rect(center=(width // 2, height // 2 - 50))
            screen.blit(name_surf, name_rect)
            
            # 品质
            quality_surf = FONT_MAIN.render(HERO_QUALITY[hero_data['quality']]['name'], True, quality_color)
            quality_rect = quality_surf.get_rect(center=(width // 2, height // 2))
            screen.blit(quality_surf, quality_rect)
            
            # 技能
            skill_surf = FONT_SMALL.render(f"技能：{hero_data['skill']}", True, (255, 255, 255))
            skill_rect = skill_surf.get_rect(center=(width // 2, height // 2 + 40))
            screen.blit(skill_surf, skill_rect)
        
        pygame.display.flip()
        clock.tick(60)

def main():
    """武将招募系统主函数"""
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG
    
    # 初始化pygame
    if not pygame.get_init():
        pygame.init()
    
    # 初始化字体
    init_fonts()
    # 使用与主菜单相同的字体
    from ASSET.game_main_menu import FONT_MAIN as MAIN_FONT, FONT_SMALL as SMALL_FONT, FONT_BIG as BIG_FONT
    FONT_MAIN = MAIN_FONT
    FONT_SMALL = SMALL_FONT
    FONT_BIG = BIG_FONT
    
    # 设置屏幕
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("武将招募")
    clock = pygame.time.Clock()
    
    # 按钮设置
    button_width = 200
    button_height = 60
    button_spacing = 20
    start_y = screen_height * 0.4
    
    # 创建按钮
    normal_btn = Button("普通招募 (100金元宝)", 
                      (screen_width - button_width) // 2, 
                      start_y, 
                      button_width, button_height, FONT_SMALL)
    
    advanced_btn = Button("高级招募 (500金元宝)", 
                        (screen_width - button_width) // 2, 
                        start_y + button_height + button_spacing, 
                        button_width, button_height, FONT_SMALL)
    
    legendary_btn = Button("传说招募 (2000金元宝)", 
                         (screen_width - button_width) // 2, 
                         start_y + 2 * (button_height + button_spacing), 
                         button_width, button_height, FONT_SMALL)
    
    back_btn = Button("返回主菜单", 
                     (screen_width - button_width) // 2, 
                     start_y + 4 * (button_height + button_spacing), 
                     button_width, button_height, FONT_SMALL, 
                     normal_color=(100, 100, 150))
    
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
                random.randint(100, 200)
            ))
        
        for p in particles[:]:
            p.update()
            p.x += math.sin(p.y * 0.02) * 0.5
            p.draw(screen)
        
        # 标题
        title_surf = FONT_BIG.render("武将招募", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(screen_width // 2, 100))
        screen.blit(title_surf, title_rect)
        
        # 资源显示
        resource_text = f"金元宝: {data['resources'].get('金元宝', 0)}"
        resource_surf = FONT_MAIN.render(resource_text, True, (255, 255, 255))
        resource_rect = resource_surf.get_rect(topright=(screen_width - 20, 20))
        screen.blit(resource_surf, resource_rect)
        
        # 按钮
        mouse_pos = pygame.mouse.get_pos()
        normal_btn.check_hover(mouse_pos)
        advanced_btn.check_hover(mouse_pos)
        legendary_btn.check_hover(mouse_pos)
        back_btn.check_hover(mouse_pos)
        
        normal_btn.draw(screen)
        advanced_btn.draw(screen)
        legendary_btn.draw(screen)
        back_btn.draw(screen)
        
        pygame.display.flip()
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if normal_btn.rect.collidepoint(event.pos):
                    hero, message = recruit_hero("normal")
                    if hero:
                        show_recruit_animation(hero)
                        # 显示成功消息
                        success_surf = FONT_MAIN.render(message, True, (80, 180, 80))
                        success_rect = success_surf.get_rect(center=(screen_width // 2, 500))
                        screen.blit(success_surf, success_rect)
                        pygame.display.flip()
                        pygame.time.wait(2000)
                    else:
                        # 显示失败消息
                        error_surf = FONT_MAIN.render(message, True, (200, 80, 80))
                        error_rect = error_surf.get_rect(center=(screen_width // 2, 500))
                        screen.blit(error_surf, error_rect)
                        pygame.display.flip()
                        pygame.time.wait(2000)
                
                elif advanced_btn.rect.collidepoint(event.pos):
                    hero, message = recruit_hero("advanced")
                    if hero:
                        show_recruit_animation(hero)
                        success_surf = FONT_MAIN.render(message, True, (80, 180, 80))
                        success_rect = success_surf.get_rect(center=(screen_width // 2, 500))
                        screen.blit(success_surf, success_rect)
                        pygame.display.flip()
                        pygame.time.wait(2000)
                    else:
                        error_surf = FONT_MAIN.render(message, True, (200, 80, 80))
                        error_rect = error_surf.get_rect(center=(screen_width // 2, 500))
                        screen.blit(error_surf, error_rect)
                        pygame.display.flip()
                        pygame.time.wait(2000)
                
                elif legendary_btn.rect.collidepoint(event.pos):
                    hero, message = recruit_hero("legendary")
                    if hero:
                        show_recruit_animation(hero)
                        success_surf = FONT_MAIN.render(message, True, (80, 180, 80))
                        success_rect = success_surf.get_rect(center=(screen_width // 2, 500))
                        screen.blit(success_surf, success_rect)
                        pygame.display.flip()
                        pygame.time.wait(2000)
                    else:
                        error_surf = FONT_MAIN.render(message, True, (200, 80, 80))
                        error_rect = error_surf.get_rect(center=(screen_width // 2, 500))
                        screen.blit(error_surf, error_rect)
                        pygame.display.flip()
                        pygame.time.wait(2000)
                
                elif back_btn.rect.collidepoint(event.pos):
                    running = False
        
        clock.tick(60)

if __name__ == '__main__':
    main()
