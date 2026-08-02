import os
import sys
import json
import pygame
import platform
import random
import math
from ASSET.game_data import data, save, default_save, RESOURCES, GUNS, SETTINGS, safe_get, ensure_keys
from ASSET.hero_database import HERO_DATABASE, EQUIPMENT_DATABASE, HERO_BONDS
from ASSET.log_system import info, warning, error
from ASSET import safe_exit


FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None
FONT_TINY = None 
screen = None
clock = None

COLORS = {
    "bg_dark": (10, 15, 30),
    "bg_panel": (25, 30, 50, 220),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 220),
    "accent_green": (60, 200, 100),
    "accent_red": (220, 80, 80),
    "accent_purple": (180, 100, 220),
    "text_white": (255, 255, 255),
    "text_gray": (160, 170, 190),
    "text_gold": (255, 215, 0),
    "btn_normal": (60, 80, 120),
    "btn_hover": (80, 110, 160),
    "btn_green": (50, 150, 80),
    "btn_red": (180, 60, 60)
}


class Button:
    def __init__(self, text, x, y, width, height, font, normal_color=(60, 80, 120), hover_color=(80, 110, 160), text_color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.clicked = False
    
    def draw(self, surface):
        color = self.hover_color if self.hovered else self.normal_color
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height), border_radius=8)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        surface.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height:
                self.clicked = True
                return True
        return False
    
    def reset_clicked(self):
        self.clicked = False


class ScrollablePanel:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.scroll_offset = 0
        self.max_scroll = 0
        self.is_scrolling = False
        self.last_mouse_y = 0
        self.content_height = 0
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - 50)
                return True
            elif event.button == 5:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 50)
                return True
            elif event.button == 1:
                if self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height:
                    self.is_scrolling = True
                    self.last_mouse_y = event.pos[1]
                    return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_scrolling = False
        elif event.type == pygame.MOUSEMOTION:
            if self.is_scrolling:
                delta_y = event.pos[1] - self.last_mouse_y
                self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - delta_y))
                self.last_mouse_y = event.pos[1]
                return True
        return False
    
    def draw_scrollbar(self, surface):
        if self.max_scroll > 0:
            scrollbar_height = max(50, self.height * self.height / self.content_height)
            scrollbar_y_ratio = self.scroll_offset / self.max_scroll
            scrollbar_y = self.y + (self.height - scrollbar_height) * scrollbar_y_ratio
            
            pygame.draw.rect(surface, (60, 60, 80), (self.x + self.width - 10, self.y + 5, 6, self.height - 10), border_radius=3)
            pygame.draw.rect(surface, (150, 130, 80), (self.x + self.width - 10, scrollbar_y, 6, scrollbar_height), border_radius=3)


class TextInput:
    def __init__(self, x, y, width, height, font, initial_text="", max_length=50):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.text = initial_text
        self.max_length = max_length
        self.active = False
        self.hovered = False
    
    def draw(self, surface):
        color = (80, 100, 140) if self.active else (50, 60, 90)
        border_color = COLORS["accent_gold"] if self.active else (80, 80, 100)
        
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height), border_radius=5)
        pygame.draw.rect(surface, border_color, (self.x, self.y, self.width, self.height), 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(left=self.x + 10, centerx=self.x + self.width // 2, centery=self.y + self.height // 2)
        surface.blit(text_surf, text_rect)
        
        if self.active and len(self.text) < self.max_length:
            cursor_x = self.x + 10 + self.font.size(self.text)[0]
            pygame.draw.line(surface, COLORS["accent_gold"], (cursor_x, self.y + 5), (cursor_x, self.y + self.height - 5), 2)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height
            return self.active
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_ESCAPE:
                self.active = False
            elif len(self.text) < self.max_length:
                self.text += event.unicode
            return True
        return False


class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, font, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.font = font
        self.label = label
        self.dragging = False
    
    def draw(self, surface):
        pygame.draw.rect(surface, (50, 60, 90), (self.x, self.y + self.height // 2 - 4, self.width, 8), border_radius=4)
        
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_width = int(self.width * ratio)
        pygame.draw.rect(surface, COLORS["accent_gold"], (self.x, self.y + self.height // 2 - 4, fill_width, 8), border_radius=4)
        
        thumb_x = self.x + fill_width - 8
        thumb_y = self.y + self.height // 2 - 8
        pygame.draw.circle(surface, COLORS["accent_gold"], (thumb_x + 8, thumb_y + 8), 8)
        
        if self.label:
            label_surf = self.font.render(self.label, True, COLORS["text_gray"])
            surface.blit(label_surf, (self.x, self.y - 20))
        
        value_surf = self.font.render(f"{self.value:.2f}", True, COLORS["text_white"])
        value_rect = value_surf.get_rect(right=self.x + self.width, centery=self.y + self.height // 2)
        surface.blit(value_surf, value_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height:
                self.dragging = True
                self._update_value(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])
            return True
        return False
    
    def _update_value(self, mouse_x):
        ratio = max(0, min(1, (mouse_x - self.x) / self.width))
        self.value = self.min_val + ratio * (self.max_val - self.min_val)


dev_guide = {
    "intro": """
欢迎来到开发者控制台！

我们相信玩家才是游戏的主人。如果你觉得游戏哪里不舒服、哪里不合理，
不用忍受，直接动手改！这里告诉你所有配置文件的位置和修改方法。

修改前提示：
1. 建议先备份 save.json 文件
2. 修改配置后重启游戏生效
3. 所有数据文件都可以用记事本打开编辑
    """,
    "save_file": """
【存档文件】save.json
位置：Android/ASSET/save.json

这个文件存储了你所有的游戏进度，包括：
- resources: 资源数量（金元宝、食物、木头等）
- heroes: 拥有的武将及属性
- equips: 装备列表
- settings: 游戏设置
- achievements: 成就进度

修改方法：
找到对应的键值对，直接修改数值即可。
例如：
  "resources": {
    "金元宝": 1000,    <- 修改这个数字
    "食物": 500
  }
    """,
    "hero_database": """
【武将数据库】hero_database.py
位置：Android/ASSET/hero_database.py

这个文件定义了所有武将的属性，包括：
- base_attributes: 基础属性（hp, attack, defense, speed）
- growth_attributes: 成长属性
- skill: 技能（名称、伤害、元素）
- ultimate: 终极技能
- passive: 被动技能
- element: 元素属性
- quality: 品质（普通、稀有、史诗、传说）
- faction: 势力

修改方法：
找到你想修改的武将，修改对应属性值。
例如修改赵云的攻击力：
"赵云": {
    "base_attributes": {
        "hp": 100,
        "attack": 50,    <- 修改这里
        "defense": 15,
        "speed": 25
    },
    ...
}

注意：修改后新建的武将才会生效，已拥有的武将需要重新获得。
    """,
    "equipment_database": """
【装备数据库】equipment_database.py
位置：Android/ASSET/equipment_database.py

这个文件定义了所有装备的属性，包括：
- type: 装备类型（weapon, armor, horse, book）
- rarity: 稀有度
- attributes: 属性加成
- description: 描述

修改方法：
找到你想修改的装备，修改对应属性。
例如修改青龙偃月刀的攻击力：
"青龙偃月刀": {
    "type": "weapon",
    "rarity": "legendary",
    "attributes": {
        "attack": 100    <- 修改这里
    },
    ...
}
    """,
    "game_data": """
【游戏配置】game_data.py
位置：Android/ASSET/game_data.py

这个文件包含游戏的核心配置：
- RESOURCES: 资源列表
- GUNS: 枪械配置
- HERO_BONDS: 羁绊配置
- ELEMENT_SYNERGIES: 元素共鸣
- ELEMENT_WEAKNESS: 元素克制
- TECH_TREE: 科技树
- BUILDINGS: 建筑配置
- TALENT_TREE: 天赋树
- DAILY_TASKS / WEEKLY_TASKS: 任务配置

修改方法：
修改对应的字典值即可。
例如修改科技树升级费用：
"resource_basic": {
    "cost": {"金元宝": 100}    <- 修改费用
}
    """,
    "welfare_center": """
【福利配置】welfare_center.py
位置：Android/ASSET/welfare_center.py

这个文件配置福利系统：
- DAILY_REWARDS: 签到奖励
- ONLINE_REWARDS: 在线奖励
- SATIRE_MESSAGES: 讽刺文案

修改方法：
直接修改奖励数值或添加新奖励。
    """,
    "shop_system": """
【商城配置】shop_system.py
位置：Android/ASSET/shop_system.py

这个文件配置商城商品：
- resources: 资源商品价格
- heroes: 武将招募价格
- equipment: 装备价格

修改方法：
修改商品的价格或添加新商品。
    """,
    "advanced_tips": """
【进阶修改技巧】

1. 修改战斗公式
   位置：battle_system.py
   找到 calculate_damage 函数，修改伤害计算公式。

2. 修改掉落率
   位置：battle_system.py
   找到 generate_battle_drops 函数，修改掉落概率。

3. 修改经验曲线
   位置：hero_management.py
   找到升级经验计算逻辑。

4. 添加新武将
   位置：hero_database.py
   按照现有格式添加新武将数据。

5. 添加新装备
   位置：equipment_database.py
   按照现有格式添加新装备数据。

6. 添加新活动
   位置：activity_system.py
   添加新的活动逻辑。

7. 修改界面样式
   位置：game_main_menu.py
   修改颜色、按钮大小、布局等。

8. 修改音效
   位置：sounds/ 目录
   替换对应的音效文件。
    """,
    "tips": """
【小贴士】

- 所有 .py 文件修改后需要重启游戏生效
- .json 文件修改后在游戏内读取存档即可生效
- 修改前建议备份原文件
- 可以用 Ctrl+F 快速查找需要修改的内容
- 如果修改后游戏崩溃，删除修改或恢复备份即可
- 数值不要设置过大，可能导致显示异常或计算问题
- 如果不知道改哪里，可以查看日志文件 logs/game.log
    """
}


def draw_panel(surface, x, y, width, height, title=""):
    pygame.draw.rect(surface, COLORS["bg_panel"], (x, y, width, height), border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_gold"], (x, y, width, height), 2, border_radius=10)
    
    if title:
        title_surf = FONT_MAIN.render(title, True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(left=x + 20, top=y + 15)
        surface.blit(title_surf, title_rect)


def draw_text_multiline(surface, text, x, y, width, font, color, line_spacing=18):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= width - 20:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)
    
    for i, line in enumerate(lines):
        text_surf = font.render(line, True, color)
        surface.blit(text_surf, (x + 10, y + i * line_spacing))
    
    return y + len(lines) * line_spacing


def render_guide_page(surface, panel, page_name):
    panel.content_height = 1000
    panel.max_scroll = max(0, panel.content_height - panel.height + 40)
    
    content_y = 60 - panel.scroll_offset
    text = dev_guide.get(page_name, "未找到页面内容")
    
    draw_text_multiline(surface, text, panel.x + 20, content_y, panel.width - 40, FONT_SMALL, COLORS["text_white"], line_spacing=22)


def main():
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG, FONT_TINY
    
    if not pygame.get_init():
        pygame.init()
    
    screen_width = 900
    screen_height = 650
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("开发者控制台 - 你的游戏你做主")
    clock = pygame.time.Clock()
    
    FONT_MAIN = pygame.font.Font(None, 36)
    FONT_SMALL = pygame.font.Font(None, 24)
    FONT_BIG = pygame.font.Font(None, 50)
    FONT_TINY = pygame.font.Font(None, 20)
    
    info("开发者控制台启动")
    
    current_page = "intro"
    scroll_panel = ScrollablePanel(320, 80, 550, 540)
    
    menu_items = [
        ("介绍", "intro"),
        ("存档文件", "save_file"),
        ("武将数据库", "hero_database"),
        ("装备数据库", "equipment_database"),
        ("游戏配置", "game_data"),
        ("福利配置", "welfare_center"),
        ("商城配置", "shop_system"),
        ("进阶技巧", "advanced_tips"),
        ("小贴士", "tips")
    ]
    
    buttons = []
    btn_width = 280
    btn_height = 40
    start_y = 80
    for i, (text, page) in enumerate(menu_items):
        btn = Button(text, 15, start_y + i * (btn_height + 5), btn_width, btn_height, FONT_SMALL, 
                     normal_color=COLORS["btn_normal"], hover_color=COLORS["btn_hover"])
        buttons.append((btn, page))
    
    reset_btn = Button("重置所有数据", 15, start_y + len(menu_items) * (btn_height + 5) + 20, btn_width, btn_height, 
                      FONT_SMALL, normal_color=COLORS["btn_red"], hover_color=(200, 80, 80))
    give_all_btn = Button("解锁全部功能", 15, start_y + len(menu_items) * (btn_height + 5) + 70, btn_width, btn_height, 
                         FONT_SMALL, normal_color=COLORS["btn_green"], hover_color=(70, 180, 100))
    config_edit_btn = Button("配置编辑器", 15, start_y + len(menu_items) * (btn_height + 5) + 120, btn_width, btn_height, 
                            FONT_SMALL, normal_color=(70, 130, 220), hover_color=(90, 150, 240))
    hero_edit_btn = Button("自定义武将", 15, start_y + len(menu_items) * (btn_height + 5) + 170, btn_width, btn_height, 
                          FONT_SMALL, normal_color=(180, 100, 220), hover_color=(200, 120, 240))
    back_btn = Button("返回主菜单", 15, screen_height - 60, btn_width, btn_height, FONT_SMALL)
    
    floating_texts = []
    
    def show_floating_text(text, x, y, color=COLORS["accent_gold"]):
        floating_texts.append({
            'text': text,
            'x': x,
            'y': y,
            'color': color,
            'alpha': 255,
            'life': 60
        })
    
    running = True
    while running:
        screen.fill(COLORS["bg_dark"])
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                safe_exit("开发者控制台")
                return
            
            if scroll_panel.handle_event(event):
                pass
            else:
                for btn, page in buttons:
                    if btn.handle_event(event) and btn.clicked:
                        current_page = page
                        scroll_panel.scroll_offset = 0
                        btn.reset_clicked()
                
                if reset_btn.handle_event(event) and reset_btn.clicked:
                    confirm_reset = True
                    if confirm_reset:
                        global data
                        data = default_save.copy()
                        save()
                        show_floating_text("数据已重置！", screen_width // 2, screen_height // 2, COLORS["accent_red"])
                    reset_btn.reset_clicked()
                
                if give_all_btn.handle_event(event) and give_all_btn.clicked:
                    for resource in RESOURCES:
                        data['resources'][resource] = 999999
                    for hero_name in HERO_DATABASE:
                        if hero_name not in data['heroes']:
                            data['heroes'][hero_name] = {
                                'name': hero_name,
                                'level': 100,
                                'experience': 0,
                                'hp': HERO_DATABASE[hero_name].get('base_attributes', {}).get('hp', 100) * 10,
                                'attack': HERO_DATABASE[hero_name].get('base_attributes', {}).get('attack', 10) * 10,
                                'defense': HERO_DATABASE[hero_name].get('base_attributes', {}).get('defense', 5) * 10,
                                'speed': HERO_DATABASE[hero_name].get('base_attributes', {}).get('speed', 5) * 10,
                                'element': HERO_DATABASE[hero_name].get('element', '土'),
                                'quality': HERO_DATABASE[hero_name].get('quality', 'common'),
                                'faction': HERO_DATABASE[hero_name].get('faction', 'qun'),
                                'skills': [],
                                'equipment': {'weapon': None, 'armor': None, 'horse': None, 'book': None},
                                'bond_bonuses': {},
                                'awakened': True,
                                'rebirth_count': 5
                            }
                    for equip_name, equip_info in EQUIPMENT_DATABASE.items():
                        equip_type = equip_info.get('type', 'weapon')
                        if equip_type not in data['equips']:
                            data['equips'][equip_type] = []
                        if equip_name not in data['equips'][equip_type]:
                            data['equips'][equip_type].append(equip_name)
                    data['vip'] = {'level': 10}
                    save()
                    show_floating_text("全部功能已解锁！", screen_width // 2, screen_height // 2, COLORS["accent_green"])
                    give_all_btn.reset_clicked()
                
                if config_edit_btn.handle_event(event) and config_edit_btn.clicked:
                    try:
                        from ASSET.config_editor import main as config_main
                        config_main()
                    except Exception as e:
                        error(f"启动配置编辑器失败: {e}")
                        show_floating_text("配置编辑器启动失败", screen_width // 2, screen_height // 2, COLORS["accent_red"])
                    config_edit_btn.reset_clicked()
                
                if hero_edit_btn.handle_event(event) and hero_edit_btn.clicked:
                    try:
                        from ASSET.custom_hero_editor import main as hero_main
                        hero_main()
                    except Exception as e:
                        error(f"启动自定义武将编辑器失败: {e}")
                        show_floating_text("自定义武将编辑器启动失败", screen_width // 2, screen_height // 2, COLORS["accent_red"])
                    hero_edit_btn.reset_clicked()
                
                if back_btn.handle_event(event) and back_btn.clicked:
                    running = False
                    back_btn.reset_clicked()
        
        title_surf = FONT_BIG.render("开发者控制台", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(screen_width // 2, 40))
        screen.blit(title_surf, title_rect)
        
        draw_panel(screen, 10, 70, 300, 550, "修改指南")
        for btn, page in buttons:
            btn.draw(screen)
        
        reset_btn.draw(screen)
        give_all_btn.draw(screen)
        config_edit_btn.draw(screen)
        hero_edit_btn.draw(screen)
        back_btn.draw(screen)
        
        draw_panel(screen, 315, 70, 570, 560, dev_guide.get(current_page, {}).get('title', current_page))
        render_guide_page(screen, scroll_panel, current_page)
        scroll_panel.draw_scrollbar(screen)
        
        for ft in floating_texts[:]:
            ft['y'] -= 2
            ft['alpha'] -= 4
            ft['life'] -= 1
            if ft['life'] <= 0 or ft['alpha'] <= 0:
                floating_texts.remove(ft)
                continue
            text_surf = FONT_MAIN.render(ft['text'], True, ft['color'])
            text_surf.set_alpha(ft['alpha'])
            text_rect = text_surf.get_rect(center=(ft['x'], ft['y']))
            screen.blit(text_surf, text_rect)
        
        pygame.display.flip()
        clock.tick(30)
    
    info("开发者控制台关闭")


if __name__ == "__main__":
    main()