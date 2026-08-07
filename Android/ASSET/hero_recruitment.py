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
from ASSET.game_data import data, save
from ASSET.game_main_menu import Button, COLORS, init_fonts
from ASSET.hero_database import (
    HERO_DATABASE, HERO_QUALITY as DB_HERO_QUALITY,
    FACTIONS, get_heroes_by_quality, get_random_hero
)

# 全局变量
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None
screen = None
clock = None

# 武将品质（来自hero_database，5个等级）
HERO_QUALITY = DB_HERO_QUALITY

# 武将列表从数据库动态构建（按品质分组）
def _build_hero_list():
    """从HERO_DATABASE构建按品质分组的武将列表"""
    result = {}
    for quality in HERO_QUALITY.keys():
        heroes = get_heroes_by_quality(quality)
        result[quality] = list(heroes.keys())
    return result

HERO_LIST = _build_hero_list()

# 招募消耗（5个等级）
RECRUIT_COST = {
    "normal":    {"金元宝": 100},     # 主要出普通/稀有
    "advanced":  {"金元宝": 500},     # 主要出稀有/史诗
    "epic":      {"金元宝": 2000},    # 主要出史诗/传说
    "legendary": {"金元宝": 8000},    # 主要出传说/神话
    "mythic":    {"金元宝": 30000}    # 必出神话
}

# 招募池概率配置（每个招募等级对应不同品质概率）
RECRUIT_PROBABILITY = {
    "normal":    {"common": 60, "rare": 30, "epic": 8, "legendary": 2, "mythic": 0},
    "advanced":  {"common": 25, "rare": 45, "epic": 22, "legendary": 7, "mythic": 1},
    "epic":      {"common": 5,  "rare": 25, "epic": 45, "legendary": 22, "mythic": 3},
    "legendary": {"common": 0,  "rare": 10, "epic": 35, "legendary": 45, "mythic": 10},
    "mythic":    {"common": 0,  "rare": 0,  "epic": 15, "legendary": 35, "mythic": 50}
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
    """招募武将（基于hero_database的详细数据）"""
    # 检查资源
    cost = RECRUIT_COST[recruit_type]
    for resource, amount in cost.items():
        if data['resources'].get(resource, 0) < amount:
            return None, f"资源不足！需要{amount}{resource}"

    # 扣除资源
    for resource, amount in cost.items():
        data['resources'][resource] -= amount
    save()

    # 根据招募等级确定武将品质（基于RECRUIT_PROBABILITY配置）
    prob_config = RECRUIT_PROBABILITY[recruit_type]
    rand = random.randint(1, 100)
    cumulative = 0
    quality = None
    for q, p in prob_config.items():
        cumulative += p
        if rand <= cumulative:
            quality = q
            break
    # 兜底：如果该等级概率全0（不应发生），随机选一个有武将的品质
    if quality is None or not HERO_LIST.get(quality):
        for q in ["mythic", "legendary", "epic", "rare", "common"]:
            if HERO_LIST.get(q):
                quality = q
                break

    # 随机选择武将
    hero_pool = HERO_LIST.get(quality, [])
    if not hero_pool:
        return None, "该品质武将池为空"
    hero_name = random.choice(hero_pool)
    hero_info = HERO_DATABASE[hero_name]

    # 基于数据库生成武将数据（含详细属性、技能、终极技、被动、背景）
    base = hero_info.get("base", {})
    growth = hero_info.get("growth", {})
    skill = hero_info.get("skill", {})
    ultimate = hero_info.get("ultimate", {})
    passive = hero_info.get("passive", {})

    hero_data = {
        "name": hero_name,
        "quality": quality,
        "faction": hero_info.get("faction", "qun"),
        "element": hero_info.get("element", "土"),
        "title": hero_info.get("title", ""),
        "weapon_type": hero_info.get("weapon_type", ""),
        "level": 1,
        "star": HERO_QUALITY[quality].get("stars", 1),
        "experience": 0,
        # 基础属性
        "attack": base.get("attack", 100),
        "defense": base.get("defense", 80),
        "health": base.get("health", 500),
        "speed": base.get("speed", 60),
        "critical": base.get("critical", 0.05),
        # 成长属性
        "growth_attack": growth.get("attack", 10),
        "growth_defense": growth.get("defense", 8),
        "growth_health": growth.get("health", 50),
        "growth_speed": growth.get("speed", 4),
        "growth_critical": growth.get("critical", 0.002),
        # 技能
        "skill_name": skill.get("name", ""),
        "skill_damage": skill.get("damage", 30),
        "skill_element": skill.get("element", hero_info.get("element", "土")),
        "skill_type": skill.get("type", "normal"),
        "skill_description": skill.get("description", ""),
        # 终极技
        "ultimate_name": ultimate.get("name", ""),
        "ultimate_damage": ultimate.get("damage", 100),
        "ultimate_element": ultimate.get("element", hero_info.get("element", "土")),
        "ultimate_type": ultimate.get("type", "normal"),
        "ultimate_description": ultimate.get("description", ""),
        # 被动
        "passive_name": passive.get("name", ""),
        "passive_description": passive.get("description", ""),
        # 背景
        "story": hero_info.get("story", ""),
        "exclusive_equipment": hero_info.get("exclusive_equipment", ""),
        # 状态
        "loyalty": 100,
        "rage": 0,
        "max_rage": 100,
        # 装备槽
        "equip_weapon": None,
        "equip_armor": None,
        "equip_helmet": None,
        "equip_accessory": None,
        "equip_boots": None,
        "equip_book": None,
        # 升级/突破/觉醒状态
        "breakthrough": 0,
        "awaken": 0,
        "rebirth_stage": 0
    }

    # 添加到武将仓库（data["heroes"]为dict，以武将名为key，与battle_system一致）
    if not isinstance(data.get("heroes"), dict):
        # 兼容旧版list结构：转换为dict
        old_list = data.get("heroes", [])
        data["heroes"] = {}
        if isinstance(old_list, list):
            for h in old_list:
                if isinstance(h, dict) and "name" in h:
                    data["heroes"][h["name"]] = h
    data["heroes"][hero_data["name"]] = hero_data
    save()

    return hero_data, f"成功招募到{HERO_QUALITY[quality]['name']}武将：{hero_name}（{hero_info.get('title', '')}）"

def show_recruit_animation(hero_data):
    """显示招募动画（增强版：展示武将详细属性）"""
    global screen, clock
    width, height = screen.get_size()
    particles = []

    # 动画时长（延长以展示更多信息）
    start_time = pygame.time.get_ticks()
    duration = 5000

    quality = hero_data.get('quality', 'common')
    quality_info = HERO_QUALITY.get(quality, {})
    quality_color = quality_info.get('color', (255, 255, 255))
    faction = hero_data.get('faction', 'qun')
    faction_info = FACTIONS.get(faction, {})
    faction_color = faction_info.get('color', (200, 200, 200))
    faction_name = faction_info.get('name', '?')

    while pygame.time.get_ticks() - start_time < duration:
        # 处理事件，防止卡死
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    return

        draw_background(screen, width, height)

        # 生成粒子（神话/传说品质粒子更多更绚丽）
        particle_chance = 0.15
        if quality in ("mythic", "legendary"):
            particle_chance = 0.3
        if random.random() < particle_chance:
            particles.append(Particle(
                random.randint(width // 4, 3 * width // 4),
                random.randint(height // 4, 3 * height // 4),
                quality_color,
                random.uniform(1, 3),
                random.randint(2, 5),
                random.randint(40, 100)
            ))

        # 更新和绘制粒子
        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)

        elapsed = pygame.time.get_ticks() - start_time
        if elapsed > 800:
            # 主面板背景
            panel_w, panel_h = 520, 460
            panel_x = (width - panel_w) // 2
            panel_y = (height - panel_h) // 2
            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (20, 20, 40, 220), (0, 0, panel_w, panel_h), border_radius=12)
            screen.blit(panel_surf, (panel_x, panel_y))
            # 品质色边框
            pygame.draw.rect(screen, quality_color, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=12)

            # 武将名称（大字）
            name_surf = FONT_BIG.render(hero_data['name'], True, quality_color)
            screen.blit(name_surf, name_surf.get_rect(center=(width // 2, panel_y + 45)))

            # 称号
            title = hero_data.get('title', '')
            if title:
                title_surf = FONT_MAIN.render(f"「{title}」", True, (255, 215, 0))
                screen.blit(title_surf, title_surf.get_rect(center=(width // 2, panel_y + 80)))

            # 品质+阵营+元素
            info_y = panel_y + 110
            info_text = f"{quality_info.get('name', '')} | {faction_name} | {hero_data.get('element', '?')}属性"
            info_surf = FONT_MAIN.render(info_text, True, faction_color)
            screen.blit(info_surf, info_surf.get_rect(center=(width // 2, info_y)))

            # 星级
            stars = quality_info.get('stars', 1)
            star_text = "★" * stars + "☆" * (5 - stars)
            star_surf = FONT_MAIN.render(star_text, True, quality_color)
            screen.blit(star_surf, star_surf.get_rect(center=(width // 2, info_y + 28)))

            # 属性
            attr_y = info_y + 60
            attrs = [
                f"攻击: {hero_data.get('attack', 0)}  (+{hero_data.get('growth_attack', 0)}/级)",
                f"防御: {hero_data.get('defense', 0)}  (+{hero_data.get('growth_defense', 0)}/级)",
                f"生命: {hero_data.get('health', 0)}  (+{hero_data.get('growth_health', 0)}/级)",
                f"速度: {hero_data.get('speed', 0)}  (+{hero_data.get('growth_speed', 0)}/级)",
                f"暴击: {int(hero_data.get('critical', 0) * 100)}%  (+{int(hero_data.get('growth_critical', 0) * 1000) / 10}%/级)",
            ]
            for i, attr in enumerate(attrs):
                attr_surf = FONT_SMALL.render(attr, True, (220, 220, 230))
                screen.blit(attr_surf, (panel_x + 40, attr_y + i * 22))

            # 技能
            skill_y = attr_y + 5 * 22 + 10
            skill_name = hero_data.get('skill_name', '')
            skill_desc = hero_data.get('skill_description', '')
            if skill_name:
                sn_surf = FONT_MAIN.render(f"【技能】{skill_name}  {hero_data.get('skill_damage', 0)}%", True, (100, 200, 255))
                screen.blit(sn_surf, (panel_x + 30, skill_y))
                if skill_desc:
                    # 长文本截断
                    if len(skill_desc) > 32:
                        skill_desc = skill_desc[:30] + "..."
                    sd_surf = FONT_SMALL.render(skill_desc, True, (200, 220, 240))
                    screen.blit(sd_surf, (panel_x + 40, skill_y + 26))

            # 终极技
            ulti_name = hero_data.get('ultimate_name', '')
            ulti_desc = hero_data.get('ultimate_description', '')
            if ulti_name:
                un_surf = FONT_MAIN.render(f"【终极】{ulti_name}  {hero_data.get('ultimate_damage', 0)}%", True, (255, 150, 100))
                screen.blit(un_surf, (panel_x + 30, skill_y + 56))
                if ulti_desc:
                    if len(ulti_desc) > 32:
                        ulti_desc = ulti_desc[:30] + "..."
                    ud_surf = FONT_SMALL.render(ulti_desc, True, (240, 210, 190))
                    screen.blit(ud_surf, (panel_x + 40, skill_y + 82))

            # 被动
            passive_name = hero_data.get('passive_name', '')
            passive_desc = hero_data.get('passive_description', '')
            if passive_name:
                pn_surf = FONT_MAIN.render(f"【被动】{passive_name}", True, (180, 255, 180))
                screen.blit(pn_surf, (panel_x + 30, skill_y + 112))
                if passive_desc:
                    if len(passive_desc) > 36:
                        passive_desc = passive_desc[:34] + "..."
                    pd_surf = FONT_SMALL.render(passive_desc, True, (200, 240, 200))
                    screen.blit(pd_surf, (panel_x + 40, skill_y + 138))

            # 提示
            if elapsed > 3000:
                tip_surf = FONT_SMALL.render("按回车/ESC继续...", True, (180, 180, 200))
                screen.blit(tip_surf, tip_surf.get_rect(center=(width // 2, panel_y + panel_h - 20)))

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

    # 按钮设置（5个招募等级 + 返回）
    button_width = 220
    button_height = 50
    button_spacing = 12
    start_y = 180

    # 创建按钮（5个招募等级）
    normal_btn = Button("普通招募 (100元宝) - 普通/稀有",
                      (screen_width - button_width) // 2,
                      start_y,
                      button_width, button_height, FONT_SMALL)

    advanced_btn = Button("高级招募 (500元宝) - 稀有/史诗",
                        (screen_width - button_width) // 2,
                        start_y + button_height + button_spacing,
                        button_width, button_height, FONT_SMALL)

    epic_btn = Button("史诗招募 (2000元宝) - 史诗/传说",
                    (screen_width - button_width) // 2,
                    start_y + 2 * (button_height + button_spacing),
                    button_width, button_height, FONT_SMALL)

    legendary_btn = Button("传说招募 (8000元宝) - 传说/神话",
                         (screen_width - button_width) // 2,
                         start_y + 3 * (button_height + button_spacing),
                         button_width, button_height, FONT_SMALL)

    mythic_btn = Button("神话招募 (30000元宝) - 必出神话!",
                      (screen_width - button_width) // 2,
                      start_y + 4 * (button_height + button_spacing),
                      button_width, button_height, FONT_SMALL)

    back_btn = Button("返回主菜单",
                     (screen_width - button_width) // 2,
                     start_y + 5 * (button_height + button_spacing) + 10,
                     button_width, button_height, FONT_SMALL,
                     normal_color=(100, 100, 150))

    # 武将数量统计
    hero_count = len(data.get("heroes", []))

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
            if p.life <= 0:
                particles.remove(p)

        # 标题
        title_surf = FONT_BIG.render("武将招募", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(screen_width // 2, 80))
        screen.blit(title_surf, title_rect)

        # 副标题：数据库统计
        subtitle = f"已收录 {len(HERO_DATABASE)} 位武将 | 己方武将: {len(data.get('heroes', []))}"
        sub_surf = FONT_SMALL.render(subtitle, True, (200, 200, 220))
        screen.blit(sub_surf, sub_surf.get_rect(center=(screen_width // 2, 115)))

        # 资源显示
        resource_text = f"金元宝: {data['resources'].get('金元宝', 0)}"
        resource_surf = FONT_MAIN.render(resource_text, True, (255, 255, 255))
        resource_rect = resource_surf.get_rect(topright=(screen_width - 20, 20))
        screen.blit(resource_surf, resource_rect)

        # 已拥有武将数
        hero_count_text = f"仓库: {len(data.get('heroes', []))} 位"
        hc_surf = FONT_MAIN.render(hero_count_text, True, (255, 255, 255))
        screen.blit(hc_surf, hc_surf.get_rect(topleft=(20, 20)))

        # 按钮
        mouse_pos = pygame.mouse.get_pos()
        normal_btn.check_hover(mouse_pos)
        advanced_btn.check_hover(mouse_pos)
        epic_btn.check_hover(mouse_pos)
        legendary_btn.check_hover(mouse_pos)
        mythic_btn.check_hover(mouse_pos)
        back_btn.check_hover(mouse_pos)

        normal_btn.draw(screen)
        advanced_btn.draw(screen)
        epic_btn.draw(screen)
        legendary_btn.draw(screen)
        mythic_btn.draw(screen)
        back_btn.draw(screen)

        # 底部说明
        tip_text = "不同等级招募池有不同的品质概率，神话招募必出神话武将！"
        tip_surf = FONT_SMALL.render(tip_text, True, (180, 180, 200))
        screen.blit(tip_surf, tip_surf.get_rect(center=(screen_width // 2, screen_height - 20)))

        pygame.display.flip()

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_btn = None
                recruit_type = None
                if normal_btn.rect.collidepoint(event.pos):
                    clicked_btn, recruit_type = normal_btn, "normal"
                elif advanced_btn.rect.collidepoint(event.pos):
                    clicked_btn, recruit_type = advanced_btn, "advanced"
                elif epic_btn.rect.collidepoint(event.pos):
                    clicked_btn, recruit_type = epic_btn, "epic"
                elif legendary_btn.rect.collidepoint(event.pos):
                    clicked_btn, recruit_type = legendary_btn, "legendary"
                elif mythic_btn.rect.collidepoint(event.pos):
                    clicked_btn, recruit_type = mythic_btn, "mythic"
                elif back_btn.rect.collidepoint(event.pos):
                    running = False
                    clicked_btn = "back"

                if recruit_type:
                    hero, message = recruit_hero(recruit_type)
                    if hero:
                        show_recruit_animation(hero)
                    # 显示结果消息
                    if hero:
                        msg_color = (80, 180, 80)
                    else:
                        msg_color = (200, 80, 80)
                    msg_surf = FONT_MAIN.render(message, True, msg_color)
                    msg_rect = msg_surf.get_rect(center=(screen_width // 2, screen_height - 50))
                    # 消息背景
                    bg_surf = pygame.Surface((msg_surf.get_width() + 20, msg_surf.get_height() + 10), pygame.SRCALPHA)
                    bg_surf.fill((20, 20, 30, 200))
                    screen.blit(bg_surf, (msg_rect.x - 10, msg_rect.y - 5))
                    screen.blit(msg_surf, msg_rect)
                    pygame.display.flip()
                    pygame.time.wait(1800)

        clock.tick(60)

if __name__ == '__main__':
    main()
