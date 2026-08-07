#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福利中心 - 免费游戏的良心所在
"""
import os
import sys
import pygame
import random
import math
import time
from ASSET.game_data import data, save
from ASSET.game_main_menu import Button, init_fonts, FloatingText

FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None
screen = None
clock = None

DAILY_REWARDS = [
    {"day": 1, "rewards": {"金元宝": 100, "食物": 50}},
    {"day": 2, "rewards": {"金元宝": 200, "木头": 50}},
    {"day": 3, "rewards": {"金元宝": 300, "煤炭": 50}},
    {"day": 4, "rewards": {"金元宝": 400, "水": 50}},
    {"day": 5, "rewards": {"金元宝": 500, "高级招募令": 1}},
    {"day": 6, "rewards": {"金元宝": 600, "稀有宠物蛋": 1}},
    {"day": 7, "rewards": {"金元宝": 1000, "顶级招募令": 1, "传说宠物蛋": 1}},
]

ONLINE_REWARDS = [
    {"seconds": 5, "rewards": {"金元宝": 50}},
    {"seconds": 15, "rewards": {"金元宝": 100, "食物": 30}},
    {"seconds": 30, "rewards": {"金元宝": 200, "木头": 30}},
    {"seconds": 60, "rewards": {"金元宝": 300, "煤炭": 30}},
    {"seconds": 120, "rewards": {"金元宝": 500, "高级招募令": 1}},
]

SATIRE_MESSAGES = [
    "别的游戏：首充6元送战神！我们：战神直接送！",
    "别的游戏：VIP15需要充值10万！我们：所有人都是VIP10！",
    "别的游戏：抽卡保底需要充648！我们：根本不需要抽卡！",
    "别的游戏：限时礼包错过等一年！我们：天天都是福利日！",
    "别的游戏：体力不够要花钱买！我们：体力无限随便浪！",
    "别的游戏：装备强化必失败！我们：强化100%成功！",
    "别的游戏：资源不够要充值！我们：资源随便拿！",
    "别的游戏：限时活动逼你氪！我们：永久免费福利！",
    "别的游戏：客服不理人！我们：良心开发在线！",
    "别的游戏：防沉迷不让玩！我们：畅玩无限制！",
    "别的游戏：每天签到逼你上线！我们：无限签到，奖励翻倍！",
    "别的游戏：三级平台全家付费！我们：全部免费畅玩！",
    "别的游戏：卫星经典还要钱！我们：经典内容随便玩！",
    "别的游戏：VIP专属客服！我们：全员专属客服！",
    "别的游戏：限时优惠套路深！我们：永久免费无套路！",
    "别的游戏：离线还要充值！我们：离线收益照样拿！",
    "别的游戏：装备绑定不能交易！我们：自由交易无限制！",
    "别的游戏：新玩家被老玩家欺负！我们：新手保护期超长！",
    "别的游戏：活动肝到吐！我们：轻松玩也能变强！",
    "别的游戏：服务器排队！我们：秒进不卡顿！",
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
    for y in range(height):
        ratio = y / height
        r = int(30 * (1 - ratio) + 50 * ratio)
        g = int(10 * (1 - ratio) + 30 * ratio)
        b = int(40 * (1 - ratio) + 60 * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    
    for i in range(15):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(2, 4)
        glow_surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, 30), (size * 3, size * 3), size * 3)
        surface.blit(glow_surf, (x - size * 3, y - size * 3))

def get_daily_reward_state():
    if "welfare" not in data:
        data["welfare"] = {}
    
    last_claim_time = data["welfare"].get("last_daily_claim_time", 0)
    current_time = time.time()
    
    if current_time - last_claim_time >= 1:
        consecutive_seconds = data["welfare"].get("consecutive_seconds", 0)
        return consecutive_seconds + 1, True
    return data["welfare"].get("consecutive_seconds", 0), False

def claim_daily_reward(day):
    if day <= len(DAILY_REWARDS):
        rewards = DAILY_REWARDS[day - 1]["rewards"].copy()
    else:
        base_rewards = DAILY_REWARDS[-1]["rewards"].copy()
        multiplier = day - 6
        
        rewards = {}
        for res, amt in base_rewards.items():
            rewards[res] = amt * multiplier
    
    if "resources" not in data:
        data["resources"] = {}
    
    for res, amt in rewards.items():
        if res in ["高级招募令", "顶级招募令", "稀有宠物蛋", "传说宠物蛋"]:
            if "inventory" not in data:
                data["inventory"] = {}
            data["inventory"][res] = data["inventory"].get(res, 0) + amt
        else:
            data["resources"][res] = data["resources"].get(res, 0) + amt
    
    if "welfare" not in data:
        data["welfare"] = {}
    
    data["welfare"]["last_daily_claim_time"] = time.time()
    data["welfare"]["consecutive_seconds"] = day
    
    save()
    return rewards

def get_online_reward_state():
    if "welfare" not in data:
        data["welfare"] = {}
    
    start_time = data["welfare"].get("online_start_time", time.time())
    elapsed_seconds = int(time.time() - start_time)
    
    claimed = data["welfare"].get("online_claimed", [])
    available = []
    
    for reward in ONLINE_REWARDS:
        if elapsed_seconds >= reward["seconds"] and reward["seconds"] not in claimed:
            available.append(reward)
    
    return elapsed_seconds, available, claimed

def claim_online_reward(seconds):
    for reward in ONLINE_REWARDS:
        if reward["seconds"] == seconds:
            if "resources" not in data:
                data["resources"] = {}
            
            for res, amt in reward["rewards"].items():
                if res in ["高级招募令"]:
                    if "inventory" not in data:
                        data["inventory"] = {}
                    data["inventory"][res] = data["inventory"].get(res, 0) + amt
                else:
                    data["resources"][res] = data["resources"].get(res, 0) + amt
            
            if "welfare" not in data:
                data["welfare"] = {}
            
            if "online_claimed" not in data["welfare"]:
                data["welfare"]["online_claimed"] = []
            
            data["welfare"]["online_claimed"].append(minutes)
            save()
            return reward["rewards"]
    return None

def get_vip_level():
    return 10

def get_vip_bonus():
    return {
        "damage_bonus": "200%",
        "gold_bonus": "100%",
        "exp_bonus": "150%",
        "drop_rate": "200%",
    }

def main():
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG
    
    if not pygame.get_init():
        pygame.init()
    
    init_fonts()
    from ASSET.game_main_menu import FONT_MAIN as MAIN_FONT, FONT_SMALL as SMALL_FONT, FONT_BIG as BIG_FONT
    FONT_MAIN = MAIN_FONT
    FONT_SMALL = SMALL_FONT
    FONT_BIG = BIG_FONT
    
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("福利中心")
    clock = pygame.time.Clock()
    
    button_width = 140
    button_height = 55
    
    back_btn = Button("返回", (screen_width - button_width) // 2, screen_height - button_height - 30, button_width, button_height, FONT_SMALL)
    
    particles = []
    floating_texts = []
    
    current_tab = "daily"
    satire_index = 0
    satire_timer = 0
    
    if "welfare" not in data:
        data["welfare"] = {}
        data["welfare"]["online_start_time"] = time.time()
        save()
    
    running = True
    while running:
        draw_background(screen, screen_width, screen_height)
        
        if random.random() < 0.15:
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
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)
        
        title_surf = FONT_BIG.render("🎁 福利中心", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(screen_width // 2, 50))
        screen.blit(title_surf, title_rect)
        
        vip_badge = pygame.Surface((120, 40), pygame.SRCALPHA)
        pygame.draw.rect(vip_badge, (255, 215, 0), (0, 0, 120, 40), border_radius=20)
        vip_text = FONT_SMALL.render("VIP 10", True, (0, 0, 0))
        vip_text_rect = vip_text.get_rect(center=(60, 20))
        vip_badge.blit(vip_text, vip_text_rect)
        screen.blit(vip_badge, (screen_width - 130, 35))
        
        tabs = [
            {"id": "daily", "text": "无限签到", "x": screen_width // 2 - 350},
            {"id": "online", "text": "在线奖励", "x": screen_width // 2 - 220},
            {"id": "vip", "text": "VIP特权", "x": screen_width // 2 - 90},
            {"id": "benefits", "text": "特色福利", "x": screen_width // 2 + 40},
            {"id": "wheel", "text": "幸运转盘", "x": screen_width // 2 + 170},
            {"id": "gift", "text": "每日礼包", "x": screen_width // 2 + 300},
            {"id": "satire", "text": "良心宣言", "x": screen_width // 2 + 430},
        ]
        
        for tab in tabs:
            tab_color = (255, 215, 0) if tab["id"] == current_tab else (150, 150, 150)
            tab_surf = FONT_SMALL.render(tab["text"], True, tab_color)
            tab_rect = tab_surf.get_rect(center=(tab["x"], 120))
            screen.blit(tab_surf, tab_rect)
            
            if tab["id"] == current_tab:
                pygame.draw.line(screen, (255, 215, 0), 
                               (tab_rect.left, tab_rect.bottom + 5), 
                               (tab_rect.right, tab_rect.bottom + 5), 3)
        
        mouse_pos = pygame.mouse.get_pos()
        
        if current_tab == "daily":
            daily_day, can_claim = get_daily_reward_state()
            
            panel_y = 160
            panel_surf = pygame.Surface((500, 300), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (40, 40, 70, 220), (0, 0, 500, 300), border_radius=15)
            screen.blit(panel_surf, ((screen_width - 500) // 2, panel_y))
            pygame.draw.rect(screen, (255, 215, 0), ((screen_width - 500) // 2, panel_y, 500, 300), 2, border_radius=15)
            
            title_text = FONT_MAIN.render("每秒签到", True, (255, 215, 0))
            screen.blit(title_text, ((screen_width - 500) // 2 + 20, panel_y + 20))
            
            day_text = FONT_SMALL.render(f"连续签到 {daily_day} 秒", True, (255, 255, 255))
            screen.blit(day_text, ((screen_width - 500) // 2 + 20, panel_y + 55))
            
            reward_list_y = panel_y + 90
            for i, reward in enumerate(DAILY_REWARDS):
                is_current = i + 1 == daily_day
                is_claimed = i + 1 < daily_day
                
                day_bg = (60, 60, 100) if not is_claimed else (50, 150, 50)
                if is_current and can_claim:
                    day_bg = (200, 150, 50)
                
                day_rect = pygame.Rect((screen_width - 500) // 2 + 25 + i * 65, reward_list_y, 55, 55)
                pygame.draw.rect(screen, day_bg, day_rect, border_radius=8)
                
                day_num = FONT_SMALL.render(str(reward["day"]), True, (255, 255, 255))
                day_num_rect = day_num.get_rect(center=day_rect.center)
                screen.blit(day_num, day_num_rect)
                
                if is_claimed:
                    check_text = FONT_SMALL.render("✓", True, (0, 255, 0))
                    check_rect = check_text.get_rect(center=(day_rect.centerx, day_rect.bottom - 8))
                    screen.blit(check_text, check_rect)
            
            claim_btn_y = panel_y + 170
            claim_btn = Button("领取奖励", (screen_width - button_width) // 2, claim_btn_y, button_width, button_height, FONT_SMALL)
            claim_btn.visible = can_claim
            
            if claim_btn.visible:
                claim_btn.check_hover(mouse_pos)
                claim_btn.draw(screen)
            
            if not can_claim:
                already_text = FONT_SMALL.render("本秒已领取", True, (150, 150, 150))
                already_rect = already_text.get_rect(center=(screen_width // 2, claim_btn_y + 27))
                screen.blit(already_text, already_rect)
            
            preview_title = FONT_SMALL.render("下一秒奖励预览：", True, (255, 215, 0))
            screen.blit(preview_title, ((screen_width - 500) // 2 + 20, panel_y + 230))
            
            preview_day = daily_day + 1
            
            if preview_day <= len(DAILY_REWARDS):
                preview_rewards = DAILY_REWARDS[preview_day - 1]["rewards"]
            else:
                base_rewards = DAILY_REWARDS[-1]["rewards"]
                multiplier = preview_day - 6
                preview_rewards = {res: amt * multiplier for res, amt in base_rewards.items()}
            
            reward_text = ", ".join([f"{k} × {v}" for k, v in preview_rewards.items()])
            reward_surf = FONT_SMALL.render(reward_text, True, (255, 255, 255))
            screen.blit(reward_surf, ((screen_width - 500) // 2 + 20, panel_y + 260))
        
        elif current_tab == "online":
            elapsed_seconds, available_rewards, claimed = get_online_reward_state()
            
            panel_y = 160
            panel_surf = pygame.Surface((500, 350), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (40, 40, 70, 220), (0, 0, 500, 350), border_radius=15)
            screen.blit(panel_surf, ((screen_width - 500) // 2, panel_y))
            pygame.draw.rect(screen, (255, 215, 0), ((screen_width - 500) // 2, panel_y, 500, 350), 2, border_radius=15)
            
            title_text = FONT_MAIN.render("在线奖励", True, (255, 215, 0))
            screen.blit(title_text, ((screen_width - 500) // 2 + 20, panel_y + 20))
            
            online_text = FONT_SMALL.render(f"已在线: {elapsed_seconds} 秒", True, (255, 255, 255))
            screen.blit(online_text, ((screen_width - 500) // 2 + 20, panel_y + 55))
            
            reward_list_y = panel_y + 90
            for reward in ONLINE_REWARDS:
                is_available = reward["seconds"] in [r["seconds"] for r in available_rewards]
                is_claimed = reward["seconds"] in claimed
                
                reward_bg = (60, 60, 100) if not is_claimed else (50, 150, 50)
                if is_available:
                    reward_bg = (200, 150, 50)
                
                reward_rect = pygame.Rect((screen_width - 500) // 2 + 20, reward_list_y, 460, 45)
                pygame.draw.rect(screen, reward_bg, reward_rect, border_radius=8)
                
                time_text = FONT_SMALL.render(f"在线{reward['seconds']}秒", True, (255, 255, 255))
                screen.blit(time_text, (reward_rect.left + 15, reward_rect.top + 12))
                
                reward_text = ", ".join([f"{k}×{v}" for k, v in reward["rewards"].items()])
                reward_text_surf = FONT_SMALL.render(reward_text, True, (255, 215, 0))
                screen.blit(reward_text_surf, (reward_rect.right - reward_text_surf.get_width() - 15, reward_rect.top + 12))
                
                if is_available:
                    claim_btn_small = Button("领取", reward_rect.right - 70, reward_rect.top + 5, 60, 35, FONT_SMALL)
                    claim_btn_small.check_hover(mouse_pos)
                    claim_btn_small.draw(screen)
                
                reward_list_y += 55
        
        elif current_tab == "vip":
            panel_y = 160
            panel_surf = pygame.Surface((500, 350), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (40, 40, 70, 220), (0, 0, 500, 350), border_radius=15)
            screen.blit(panel_surf, ((screen_width - 500) // 2, panel_y))
            pygame.draw.rect(screen, (255, 215, 0), ((screen_width - 500) // 2, panel_y, 500, 350), 2, border_radius=15)
            
            title_text = FONT_MAIN.render("VIP特权", True, (255, 215, 0))
            screen.blit(title_text, ((screen_width - 500) // 2 + 20, panel_y + 20))
            
            vip_level = get_vip_level()
            vip_text = FONT_BIG.render(f"VIP {vip_level}", True, (255, 215, 0))
            vip_rect = vip_text.get_rect(center=(screen_width // 2, panel_y + 80))
            screen.blit(vip_text, vip_rect)
            
            free_text = FONT_SMALL.render("所有人都是VIP10！无需充值！", True, (50, 200, 50))
            free_rect = free_text.get_rect(center=(screen_width // 2, panel_y + 120))
            screen.blit(free_text, free_rect)
            
            bonuses = get_vip_bonus()
            bonus_y = panel_y + 160
            
            for bonus_name, bonus_value in bonuses.items():
                bonus_bg = (60, 60, 100)
                bonus_rect = pygame.Rect((screen_width - 500) // 2 + 20, bonus_y, 460, 45)
                pygame.draw.rect(screen, bonus_bg, bonus_rect, border_radius=8)
                
                name_text = FONT_SMALL.render({
                    "damage_bonus": "伤害加成",
                    "gold_bonus": "金币加成",
                    "exp_bonus": "经验加成",
                    "drop_rate": "掉落率加成"
                }[bonus_name], True, (255, 255, 255))
                screen.blit(name_text, (bonus_rect.left + 15, bonus_rect.top + 12))
                
                value_text = FONT_SMALL.render(f"+{bonus_value}", True, (255, 215, 0))
                screen.blit(value_text, (bonus_rect.right - value_text.get_width() - 15, bonus_rect.top + 12))
                
                bonus_y += 55
        
        elif current_tab == "benefits":
            panel_y = 160
            panel_surf = pygame.Surface((600, 400), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (40, 40, 70, 220), (0, 0, 600, 400), border_radius=15)
            screen.blit(panel_surf, ((screen_width - 600) // 2, panel_y))
            pygame.draw.rect(screen, (255, 215, 0), ((screen_width - 600) // 2, panel_y, 600, 400), 2, border_radius=15)
            
            title_text = FONT_MAIN.render("特色福利", True, (255, 215, 0))
            screen.blit(title_text, ((screen_width - 600) // 2 + 20, panel_y + 20))
            
            benefits = [
                {
                    "name": "🎁 免费十连抽",
                    "desc": "点击直接获得10次招募机会！",
                    "icon": "🎲",
                    "rewards": {"高级招募令": 10},
                    "btn_text": "立即领取",
                    "cooltime": 30,
                    "key": "free_gacha"
                },
                {
                    "name": "⚡ 一键满级",
                    "desc": "所有武将直接升到满级！",
                    "icon": "⭐",
                    "rewards": {"武将经验": 999999},
                    "btn_text": "立即升级",
                    "cooltime": 60,
                    "key": "level_up"
                },
                {
                    "name": "💖 无限体力",
                    "desc": "体力直接恢复满！",
                    "icon": "❤️",
                    "rewards": {"体力": 999},
                    "btn_text": "恢复体力",
                    "cooltime": 15,
                    "key": "restore_stamina"
                },
                {
                    "name": "🛡️ 神装免费送",
                    "desc": "直接获得一套神级装备！",
                    "icon": "🏆",
                    "rewards": {"传说装备箱": 1},
                    "btn_text": "领取神装",
                    "cooltime": 120,
                    "key": "free_equip"
                },
                {
                    "name": "💰 离线收益",
                    "desc": "自动计算离线期间的收益！",
                    "icon": "💤",
                    "rewards": {"金元宝": 500, "食物": 200},
                    "btn_text": "领取收益",
                    "cooltime": 0,
                    "key": "offline_rewards"
                },
            ]
            
            benefit_y = panel_y + 70
            for benefit in benefits:
                benefit_rect = pygame.Rect((screen_width - 600) // 2 + 20, benefit_y, 560, 70)
                pygame.draw.rect(screen, (60, 60, 100), benefit_rect, border_radius=10)
                
                icon_surf = FONT_BIG.render(benefit["icon"], True, (255, 215, 0))
                screen.blit(icon_surf, (benefit_rect.left + 15, benefit_rect.top + 10))
                
                name_surf = FONT_MAIN.render(benefit["name"], True, (255, 255, 255))
                screen.blit(name_surf, (benefit_rect.left + 60, benefit_rect.top + 10))
                
                desc_surf = FONT_SMALL.render(benefit["desc"], True, (180, 180, 180))
                screen.blit(desc_surf, (benefit_rect.left + 60, benefit_rect.top + 40))
                
                now = time.time()
                last_time = data.get("welfare", {}).get(f"last_{benefit['key']}", 0)
                can_claim = now - last_time >= benefit["cooltime"]
                
                btn_x = benefit_rect.right - 110
                btn_y = benefit_rect.top + 15
                
                if can_claim:
                    benefit_btn = Button(benefit["btn_text"], btn_x, btn_y, 100, 40, FONT_SMALL)
                    benefit_btn.check_hover(mouse_pos)
                    benefit_btn.draw(screen)
                else:
                    remaining = int(benefit["cooltime"] - (now - last_time))
                    cool_text = FONT_SMALL.render(f"{remaining}秒后", True, (100, 100, 100))
                    cool_rect = cool_text.get_rect(center=(btn_x + 50, btn_y + 20))
                    screen.blit(cool_text, cool_rect)
                
                benefit_y += 85
        
        elif current_tab == "satire":
            panel_y = 160
            panel_surf = pygame.Surface((500, 350), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (40, 40, 70, 220), (0, 0, 500, 350), border_radius=15)
            screen.blit(panel_surf, ((screen_width - 500) // 2, panel_y))
            pygame.draw.rect(screen, (255, 215, 0), ((screen_width - 500) // 2, panel_y, 500, 350), 2, border_radius=15)
            
            title_text = FONT_MAIN.render("良心宣言", True, (255, 215, 0))
            screen.blit(title_text, ((screen_width - 500) // 2 + 20, panel_y + 20))
            
            satire_timer += 1
            if satire_timer > 180:
                satire_index = (satire_index + 1) % len(SATIRE_MESSAGES)
                satire_timer = 0
            
            message = SATIRE_MESSAGES[satire_index]
            message_lines = []
            words = message.split()
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                if FONT_SMALL.size(test_line)[0] > 460:
                    message_lines.append(current_line)
                    current_line = word + " "
                else:
                    current_line = test_line
            if current_line:
                message_lines.append(current_line)
            
            msg_y = panel_y + 70
            for line in message_lines:
                line_surf = FONT_SMALL.render(line, True, (255, 255, 255))
                line_rect = line_surf.get_rect(center=(screen_width // 2, msg_y))
                screen.blit(line_surf, line_rect)
                msg_y += 35
            
            fake_btn = Button("💰 限时充值648", (screen_width - 200) // 2, panel_y + 250, 200, 50, FONT_SMALL, normal_color=(220, 100, 50))
            fake_btn.check_hover(mouse_pos)
            fake_btn.draw(screen)
        
        elif current_tab == "wheel":
            panel_y = 160
            panel_surf = pygame.Surface((600, 400), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (40, 40, 70, 220), (0, 0, 600, 400), border_radius=15)
            screen.blit(panel_surf, ((screen_width - 600) // 2, panel_y))
            pygame.draw.rect(screen, (255, 215, 0), ((screen_width - 600) // 2, panel_y, 600, 400), 2, border_radius=15)
            
            title_text = FONT_MAIN.render("🎰 幸运转盘", True, (255, 215, 0))
            screen.blit(title_text, ((screen_width - 600) // 2 + 20, panel_y + 20))
            
            wheel_center_x = screen_width // 2
            wheel_center_y = panel_y + 220
            wheel_radius = 120
            
            prizes = [
                {"name": "金元宝 ×1000", "color": (255, 215, 0), "weight": 5, "rewards": {"金元宝": 1000}},
                {"name": "传说宠物蛋", "color": (128, 0, 128), "weight": 1, "rewards": {"传说宠物蛋": 1}},
                {"name": "金元宝 ×500", "color": (255, 150, 0), "weight": 10, "rewards": {"金元宝": 500}},
                {"name": "顶级招募令", "color": (255, 100, 100), "weight": 2, "rewards": {"顶级招募令": 1}},
                {"name": "金元宝 ×300", "color": (255, 200, 100), "weight": 15, "rewards": {"金元宝": 300}},
                {"name": "高级招募令", "color": (100, 150, 255), "weight": 5, "rewards": {"高级招募令": 2}},
                {"name": "金元宝 ×200", "color": (200, 230, 255), "weight": 20, "rewards": {"金元宝": 200}},
                {"name": "稀有宠物蛋", "color": (100, 255, 100), "weight": 3, "rewards": {"稀有宠物蛋": 1}},
            ]
            
            total_weight = sum(p["weight"] for p in prizes)
            angle_per_prize = 360 / len(prizes)
            
            for i, prize in enumerate(prizes):
                start_angle = i * angle_per_prize - 90
                end_angle = (i + 1) * angle_per_prize - 90
                
                start_rad = math.radians(start_angle)
                end_rad = math.radians(end_angle)
                
                points = [
                    (wheel_center_x, wheel_center_y),
                    (wheel_center_x + wheel_radius * math.cos(start_rad), wheel_center_y + wheel_radius * math.sin(start_rad)),
                    (wheel_center_x + wheel_radius * math.cos(end_rad), wheel_center_y + wheel_radius * math.sin(end_rad))
                ]
                
                pygame.draw.polygon(screen, prize["color"], points)
                pygame.draw.polygon(screen, (0, 0, 0), points, 2)
                
                mid_angle = (start_angle + end_angle) / 2
                mid_rad = math.radians(mid_angle)
                text_x = wheel_center_x + (wheel_radius * 0.6) * math.cos(mid_rad)
                text_y = wheel_center_y + (wheel_radius * 0.6) * math.sin(mid_rad)
                
                prize_text = FONT_SMALL.render(prize["name"], True, (0, 0, 0))
                text_rect = prize_text.get_rect(center=(text_x, text_y))
                screen.blit(prize_text, text_rect)
            
            pygame.draw.circle(screen, (0, 0, 0), (wheel_center_x, wheel_center_y), 25)
            pygame.draw.circle(screen, (255, 215, 0), (wheel_center_x, wheel_center_y), 20)
            
            arrow_angle = data.get("welfare", {}).get("wheel_angle", 0)
            arrow_x = wheel_center_x + (wheel_radius + 30) * math.cos(math.radians(arrow_angle))
            arrow_y = wheel_center_y + (wheel_radius + 30) * math.sin(math.radians(arrow_angle))
            pygame.draw.polygon(screen, (255, 215, 0), [
                (arrow_x, arrow_y),
                (arrow_x - 15, arrow_y + 10),
                (arrow_x + 15, arrow_y + 10)
            ])
            
            spin_btn = Button("免费抽奖", (screen_width - 150) // 2, panel_y + 350, 150, 45, FONT_SMALL)
            spin_btn.check_hover(mouse_pos)
            spin_btn.draw(screen)
        
        elif current_tab == "gift":
            panel_y = 160
            panel_surf = pygame.Surface((600, 400), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (40, 40, 70, 220), (0, 0, 600, 400), border_radius=15)
            screen.blit(panel_surf, ((screen_width - 600) // 2, panel_y))
            pygame.draw.rect(screen, (255, 215, 0), ((screen_width - 600) // 2, panel_y, 600, 400), 2, border_radius=15)
            
            title_text = FONT_MAIN.render("🎁 每日礼包", True, (255, 215, 0))
            screen.blit(title_text, ((screen_width - 600) // 2 + 20, panel_y + 20))
            
            daily_gifts = [
                {
                    "name": "新手礼包",
                    "icon": "🎒",
                    "rewards": {"金元宝": 200, "食物": 100},
                    "unlocked": True,
                    "btn_text": "领取"
                },
                {
                    "name": "进阶礼包",
                    "icon": "🎯",
                    "rewards": {"金元宝": 500, "高级招募令": 2},
                    "unlocked": True,
                    "btn_text": "领取"
                },
                {
                    "name": "豪华礼包",
                    "icon": "💎",
                    "rewards": {"金元宝": 1000, "顶级招募令": 1, "稀有宠物蛋": 1},
                    "unlocked": True,
                    "btn_text": "领取"
                },
                {
                    "name": "至尊礼包",
                    "icon": "👑",
                    "rewards": {"金元宝": 2000, "顶级招募令": 3, "传说宠物蛋": 1},
                    "unlocked": True,
                    "btn_text": "领取"
                },
            ]
            
            gift_y = panel_y + 70
            for gift in daily_gifts:
                gift_rect = pygame.Rect((screen_width - 600) // 2 + 20, gift_y, 560, 70)
                pygame.draw.rect(screen, (60, 60, 100), gift_rect, border_radius=10)
                
                icon_surf = FONT_BIG.render(gift["icon"], True, (255, 215, 0))
                screen.blit(icon_surf, (gift_rect.left + 15, gift_rect.top + 10))
                
                name_surf = FONT_MAIN.render(gift["name"], True, (255, 255, 255))
                screen.blit(name_surf, (gift_rect.left + 60, gift_rect.top + 10))
                
                reward_str = ", ".join([f"{v}{k}" for k, v in gift["rewards"].items()])
                reward_surf = FONT_SMALL.render(reward_str, True, (180, 180, 180))
                screen.blit(reward_surf, (gift_rect.left + 60, gift_rect.top + 40))
                
                gift_btn = Button(gift["btn_text"], gift_rect.right - 110, gift_rect.top + 15, 100, 40, FONT_SMALL)
                gift_btn.check_hover(mouse_pos)
                gift_btn.draw(screen)
                
                gift_y += 85
        
        back_btn.check_hover(mouse_pos)
        back_btn.draw(screen)
        
        for text in floating_texts[:]:
            text.update()
            text.draw(screen)
            if not text.active:
                floating_texts.remove(text)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for tab in tabs:
                    tab_surf = FONT_SMALL.render(tab["text"], True, (255, 215, 0))
                    tab_rect = tab_surf.get_rect(center=(tab["x"], 120))
                    if tab_rect.collidepoint(event.pos):
                        current_tab = tab["id"]
                
                if back_btn.rect.collidepoint(event.pos):
                    running = False
                
                if current_tab == "daily":
                    if claim_btn.visible and claim_btn.rect.collidepoint(event.pos):
                        rewards = claim_daily_reward(daily_day)
                        reward_text = ", ".join([f"+{v} {k}" for k, v in rewards.items()])
                        floating_texts.append(FloatingText(
                            f"领取成功！{reward_text}", 
                            screen_width // 2, screen_height // 2, 
                            (50, 200, 50), FONT_MAIN
                        ))
                
                elif current_tab == "online":
                    for reward in ONLINE_REWARDS:
                        is_available = reward["seconds"] in [r["seconds"] for r in available_rewards]
                        if is_available:
                            reward_rect = pygame.Rect((screen_width - 500) // 2 + 20, reward_list_y, 460, 45)
                            claim_btn_small = Button("领取", reward_rect.right - 70, reward_rect.top + 5, 60, 35, FONT_SMALL)
                            if claim_btn_small.rect.collidepoint(event.pos):
                                claimed_rewards = claim_online_reward(reward["seconds"])
                                if claimed_rewards:
                                    reward_text = ", ".join([f"+{v} {k}" for k, v in claimed_rewards.items()])
                                    floating_texts.append(FloatingText(
                                        f"领取成功！{reward_text}", 
                                        screen_width // 2, screen_height // 2, 
                                        (50, 200, 50), FONT_MAIN
                                    ))
                
                elif current_tab == "wheel":
                    spin_btn = Button("免费抽奖", (screen_width - 150) // 2, panel_y + 350, 150, 45, FONT_SMALL)
                    if spin_btn.rect.collidepoint(event.pos):
                        prizes = [
                            {"name": "金元宝 ×1000", "weight": 5, "rewards": {"金元宝": 1000}},
                            {"name": "传说宠物蛋", "weight": 1, "rewards": {"传说宠物蛋": 1}},
                            {"name": "金元宝 ×500", "weight": 10, "rewards": {"金元宝": 500}},
                            {"name": "顶级招募令", "weight": 2, "rewards": {"顶级招募令": 1}},
                            {"name": "金元宝 ×300", "weight": 15, "rewards": {"金元宝": 300}},
                            {"name": "高级招募令", "weight": 5, "rewards": {"高级招募令": 2}},
                            {"name": "金元宝 ×200", "weight": 20, "rewards": {"金元宝": 200}},
                            {"name": "稀有宠物蛋", "weight": 3, "rewards": {"稀有宠物蛋": 1}},
                        ]
                        
                        total_weight = sum(p["weight"] for p in prizes)
                        rand = random.random() * total_weight
                        current = 0
                        for prize in prizes:
                            current += prize["weight"]
                            if rand < current:
                                if "resources" not in data:
                                    data["resources"] = {}
                                if "inventory" not in data:
                                    data["inventory"] = {}
                                
                                for res, amt in prize["rewards"].items():
                                    if res in ["高级招募令", "顶级招募令", "稀有宠物蛋", "传说宠物蛋"]:
                                        data["inventory"][res] = data["inventory"].get(res, 0) + amt
                                    else:
                                        data["resources"][res] = data["resources"].get(res, 0) + amt
                                
                                save()
                                
                                reward_text = ", ".join([f"+{v} {k}" for k, v in prize["rewards"].items()])
                                floating_texts.append(FloatingText(
                                    f"🎉 恭喜获得: {reward_text}", 
                                    screen_width // 2, screen_height // 2, 
                                    (255, 215, 0), FONT_MAIN
                                ))
                                
                                new_angle = data.get("welfare", {}).get("wheel_angle", 0) + 360 + random.randint(0, 360)
                                if "welfare" not in data:
                                    data["welfare"] = {}
                                data["welfare"]["wheel_angle"] = new_angle
                                save()
                                break
                
                elif current_tab == "gift":
                    daily_gifts = [
                        {"name": "新手礼包", "rewards": {"金元宝": 200, "食物": 100}},
                        {"name": "进阶礼包", "rewards": {"金元宝": 500, "高级招募令": 2}},
                        {"name": "豪华礼包", "rewards": {"金元宝": 1000, "顶级招募令": 1, "稀有宠物蛋": 1}},
                        {"name": "至尊礼包", "rewards": {"金元宝": 2000, "顶级招募令": 3, "传说宠物蛋": 1}},
                    ]
                    
                    gift_y = panel_y + 70
                    for i, gift in enumerate(daily_gifts):
                        gift_rect = pygame.Rect((screen_width - 600) // 2 + 20, gift_y, 560, 70)
                        gift_btn = Button("领取", gift_rect.right - 110, gift_rect.top + 15, 100, 40, FONT_SMALL)
                        
                        if gift_btn.rect.collidepoint(event.pos):
                            if "resources" not in data:
                                data["resources"] = {}
                            if "inventory" not in data:
                                data["inventory"] = {}
                            
                            for res, amt in gift["rewards"].items():
                                if res in ["高级招募令", "顶级招募令", "稀有宠物蛋", "传说宠物蛋"]:
                                    data["inventory"][res] = data["inventory"].get(res, 0) + amt
                                else:
                                    data["resources"][res] = data["resources"].get(res, 0) + amt
                            
                            save()
                            
                            reward_text = ", ".join([f"+{v} {k}" for k, v in gift["rewards"].items()])
                            floating_texts.append(FloatingText(
                                f"🎁 领取成功: {reward_text}", 
                                screen_width // 2, screen_height // 2, 
                                (50, 200, 50), FONT_MAIN
                            ))
                        gift_y += 85
                
                elif current_tab == "satire":
                    fake_btn = Button("💰 限时充值648", (screen_width - 200) // 2, panel_y + 250, 200, 50, FONT_SMALL, normal_color=(220, 100, 50))
                    if fake_btn.rect.collidepoint(event.pos):
                        floating_texts.append(FloatingText(
                            "想都别想！全免费！", 
                            screen_width // 2, screen_height // 2, 
                            (255, 215, 0), FONT_MAIN
                        ))
                
                elif current_tab == "benefits":
                    benefits = [
                        {"name": "🎁 免费十连抽", "rewards": {"高级招募令": 10}, "cooltime": 30, "key": "free_gacha", "btn_text": "立即领取"},
                        {"name": "⚡ 一键满级", "rewards": {"武将经验": 999999}, "cooltime": 60, "key": "level_up", "btn_text": "立即升级"},
                        {"name": "💖 无限体力", "rewards": {"体力": 999}, "cooltime": 15, "key": "restore_stamina", "btn_text": "恢复体力"},
                        {"name": "🛡️ 神装免费送", "rewards": {"传说装备箱": 1}, "cooltime": 120, "key": "free_equip", "btn_text": "领取神装"},
                        {"name": "💰 离线收益", "rewards": {"金元宝": 500, "食物": 200}, "cooltime": 0, "key": "offline_rewards", "btn_text": "领取收益"},
                    ]
                    
                    benefit_y = panel_y + 70
                    for benefit in benefits:
                        benefit_rect = pygame.Rect((screen_width - 600) // 2 + 20, benefit_y, 560, 70)
                        btn_x = benefit_rect.right - 110
                        btn_y = benefit_rect.top + 15
                        
                        now = time.time()
                        last_time = data.get("welfare", {}).get(f"last_{benefit['key']}", 0)
                        can_claim = now - last_time >= benefit["cooltime"]
                        
                        if can_claim:
                            benefit_btn = Button(benefit["btn_text"], btn_x, btn_y, 100, 40, FONT_SMALL)
                            if benefit_btn.rect.collidepoint(event.pos):
                                if "resources" not in data:
                                    data["resources"] = {}
                                if "inventory" not in data:
                                    data["inventory"] = {}
                                
                                for res, amt in benefit["rewards"].items():
                                    if res in ["高级招募令", "传说装备箱"]:
                                        data["inventory"][res] = data["inventory"].get(res, 0) + amt
                                    else:
                                        data["resources"][res] = data["resources"].get(res, 0) + amt
                                
                                if "welfare" not in data:
                                    data["welfare"] = {}
                                data["welfare"][f"last_{benefit['key']}"] = now
                                save()
                                
                                reward_text = ", ".join([f"+{v} {k}" for k, v in benefit["rewards"].items()])
                                floating_texts.append(FloatingText(
                                    f"领取成功！{reward_text}", 
                                    screen_width // 2, screen_height // 2, 
                                    (50, 200, 50), FONT_MAIN
                                ))
                        
                        benefit_y += 85
        
        clock.tick(60)

if __name__ == '__main__':
    main()