import os
import sys
import json
import pygame
import platform
import random
import math
from ASSET.game_data import data, save, default_save, RESOURCES, GUNS, SETTINGS
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
    "btn_normal": (60, 80, 120),
    "btn_hover": (80, 110, 160),
    "btn_green": (50, 150, 80),
    "btn_red": (180, 60, 60),
    "input_bg": (40, 50, 80),
    "input_border": (80, 100, 140)
}


class Button:
    def __init__(self, text, x, y, width, height, font, normal_color=(60, 80, 120), hover_color=(80, 110, 160), text_color=(255, 255, 255), action=None):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.action = action
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
                if self.action:
                    self.action()
                return True
        return False
    
    def reset_clicked(self):
        self.clicked = False


class TextInput:
    def __init__(self, x, y, width, height, font, initial_text="", max_length=50, on_change=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.text = initial_text
        self.max_length = max_length
        self.on_change = on_change
        self.active = False
        self.hovered = False
    
    def draw(self, surface):
        color = (80, 100, 140) if self.active else COLORS["input_bg"]
        border_color = COLORS["accent_gold"] if self.active else COLORS["input_border"]
        
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height), border_radius=5)
        pygame.draw.rect(surface, border_color, (self.x, self.y, self.width, self.height), 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(left=self.x + 10, centery=self.y + self.height // 2)
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
                if self.on_change:
                    self.on_change(self.text)
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_ESCAPE:
                self.active = False
            elif len(self.text) < self.max_length:
                self.text += event.unicode
                if self.on_change:
                    self.on_change(self.text)
            return True
        return False


class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, font, label="", on_change=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.font = font
        self.label = label
        self.on_change = on_change
        self.dragging = False
    
    def draw(self, surface):
        pygame.draw.rect(surface, COLORS["input_bg"], (self.x, self.y + self.height // 2 - 4, self.width, 8), border_radius=4)
        
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_width = int(self.width * ratio)
        pygame.draw.rect(surface, COLORS["accent_gold"], (self.x, self.y + self.height // 2 - 4, fill_width, 8), border_radius=4)
        
        thumb_x = self.x + fill_width - 8
        thumb_y = self.y + self.height // 2 - 8
        pygame.draw.circle(surface, COLORS["accent_gold"], (thumb_x + 8, thumb_y + 8), 8)
        
        if self.label:
            label_surf = self.font.render(self.label, True, COLORS["text_gray"])
            surface.blit(label_surf, (self.x, self.y - 25))
        
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
        if self.on_change:
            self.on_change(self.value)


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


class ConfigCategory:
    def __init__(self, name, items):
        self.name = name
        self.items = items


def draw_panel(surface, x, y, width, height, title=""):
    pygame.draw.rect(surface, COLORS["bg_panel"], (x, y, width, height), border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_gold"], (x, y, width, height), 2, border_radius=10)
    
    if title:
        title_surf = FONT_MAIN.render(title, True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(left=x + 20, top=y + 15)
        surface.blit(title_surf, title_rect)


def render_config_panel(surface, panel, config_items):
    panel.content_height = len(config_items) * 80 + 40
    panel.max_scroll = max(0, panel.content_height - panel.height + 40)
    
    y = 40 - panel.scroll_offset
    
    for item in config_items:
        if y > panel.height:
            break
        if y + 60 < 0:
            y += 80
            continue
        
        label_text = item['label']
        label_surf = FONT_SMALL.render(label_text, True, COLORS["text_white"])
        surface.blit(label_surf, (panel.x + 20, y))
        
        if item['type'] == 'slider':
            slider = item['widget']
            slider.y = y + 30
            slider.draw(surface)
        elif item['type'] == 'input':
            input_box = item['widget']
            input_box.y = y + 25
            input_box.draw(surface)
        elif item['type'] == 'button':
            btn = item['widget']
            btn.y = y + 25
            btn.draw(surface)
        
        y += 80


def main():
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG, FONT_TINY
    
    if not pygame.get_init():
        pygame.init()
    
    screen_width = 950
    screen_height = 650
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("配置编辑器 - 自定义你的游戏")
    clock = pygame.time.Clock()
    
    FONT_MAIN = pygame.font.Font(None, 36)
    FONT_SMALL = pygame.font.Font(None, 24)
    FONT_BIG = pygame.font.Font(None, 50)
    FONT_TINY = pygame.font.Font(None, 20)
    
    info("配置编辑器启动")
    
    current_category = 0
    scroll_panel = ScrollablePanel(280, 80, 650, 540)
    
    config_categories = []
    
    resource_items = []
    for resource in RESOURCES:
        current_val = data['resources'].get(resource, 0)
        def create_slider(resource_name=resource, default_val=current_val):
            def on_change(val):
                data['resources'][resource_name] = int(val)
            return Slider(340, 0, 550, 40, 0, 999999, default_val, FONT_SMALL, label=resource_name, on_change=on_change)
        
        resource_items.append({
            'label': f"资源: {resource}",
            'type': 'slider',
            'widget': create_slider()
        })
    config_categories.append(ConfigCategory("资源配置", resource_items))
    
    vip_items = []
    vip_level = data.get('vip', {}).get('level', 0)
    vip_items.append({
        'label': "VIP等级",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0, 10, vip_level, FONT_SMALL, label="VIP等级", 
                        on_change=lambda val: data.setdefault('vip', {}).__setitem__('level', int(val)))
    })
    
    vip_items.append({
        'label': "一键解锁全部VIP特权",
        'type': 'button',
        'widget': Button("解锁", 680, 0, 100, 35, FONT_TINY, normal_color=COLORS["btn_green"],
                        action=lambda: data.__setitem__('vip', {'level': 10}))
    })
    config_categories.append(ConfigCategory("VIP配置", vip_items))
    
    battle_items = []
    battle_items.append({
        'label': "基础伤害倍率",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.1, 10.0, 1.0, FONT_SMALL, label="基础伤害倍率",
                        on_change=lambda val: data.setdefault('battle_settings', {}).__setitem__('damage_multiplier', val))
    })
    battle_items.append({
        'label': "金币掉落倍率",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.1, 20.0, 1.0, FONT_SMALL, label="金币掉落倍率",
                        on_change=lambda val: data.setdefault('battle_settings', {}).__setitem__('gold_multiplier', val))
    })
    battle_items.append({
        'label': "经验获取倍率",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.1, 20.0, 1.0, FONT_SMALL, label="经验获取倍率",
                        on_change=lambda val: data.setdefault('battle_settings', {}).__setitem__('exp_multiplier', val))
    })
    battle_items.append({
        'label': "稀有物品掉落率",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.01, 1.0, 0.1, FONT_SMALL, label="稀有物品掉落率",
                        on_change=lambda val: data.setdefault('battle_settings', {}).__setitem__('rare_drop_rate', val))
    })
    config_categories.append(ConfigCategory("战斗配置", battle_items))
    
    hero_items = []
    hero_items.append({
        'label': "武将基础等级",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 1, 200, 1, FONT_SMALL, label="武将基础等级",
                        on_change=lambda val: data.setdefault('hero_settings', {}).__setitem__('base_level', int(val)))
    })
    hero_items.append({
        'label': "武将属性倍率",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.1, 10.0, 1.0, FONT_SMALL, label="武将属性倍率",
                        on_change=lambda val: data.setdefault('hero_settings', {}).__setitem__('stat_multiplier', val))
    })
    config_categories.append(ConfigCategory("武将配置", hero_items))
    
    shop_items = []
    shop_items.append({
        'label': "商城商品折扣",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.1, 1.0, 1.0, FONT_SMALL, label="商城商品折扣",
                        on_change=lambda val: data.setdefault('shop_settings', {}).__setitem__('discount', val))
    })
    shop_items.append({
        'label': "十连抽必出橙将",
        'type': 'button',
        'widget': Button("启用", 680, 0, 100, 35, FONT_TINY, normal_color=COLORS["btn_green"],
                        action=lambda: data.setdefault('shop_settings', {}).__setitem__('guaranteed_legendary', True))
    })
    shop_items.append({
        'label': "关闭十连抽必出橙将",
        'type': 'button',
        'widget': Button("关闭", 680, 0, 100, 35, FONT_TINY, normal_color=COLORS["btn_red"],
                        action=lambda: data.setdefault('shop_settings', {}).__setitem__('guaranteed_legendary', False))
    })
    config_categories.append(ConfigCategory("商城配置", shop_items))
    
    welfare_items = []
    welfare_items.append({
        'label': "签到奖励倍率",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.1, 10.0, 1.0, FONT_SMALL, label="签到奖励倍率",
                        on_change=lambda val: data.setdefault('welfare_settings', {}).__setitem__('checkin_multiplier', val))
    })
    welfare_items.append({
        'label': "在线奖励倍率",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.1, 10.0, 1.0, FONT_SMALL, label="在线奖励倍率",
                        on_change=lambda val: data.setdefault('welfare_settings', {}).__setitem__('online_multiplier', val))
    })
    config_categories.append(ConfigCategory("福利配置", welfare_items))
    
    game_items = []
    game_items.append({
        'label': "游戏速度倍率",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 0.5, 3.0, 1.0, FONT_SMALL, label="游戏速度倍率",
                        on_change=lambda val: data.setdefault('game_settings', {}).__setitem__('speed_multiplier', val))
    })
    game_items.append({
        'label': "自动保存间隔(分钟)",
        'type': 'slider',
        'widget': Slider(340, 0, 550, 40, 1, 60, 5, FONT_SMALL, label="自动保存间隔",
                        on_change=lambda val: data.setdefault('game_settings', {}).__setitem__('auto_save_interval', int(val)))
    })
    config_categories.append(ConfigCategory("游戏配置", game_items))
    
    category_buttons = []
    btn_width = 240
    btn_height = 40
    start_y = 80
    for i, category in enumerate(config_categories):
        btn = Button(category.name, 20, start_y + i * (btn_height + 5), btn_width, btn_height, FONT_SMALL)
        category_buttons.append((btn, i))
    
    save_btn = Button("保存配置", 20, start_y + len(config_categories) * (btn_height + 5) + 20, btn_width, btn_height, 
                     FONT_SMALL, normal_color=COLORS["btn_green"])
    reset_btn = Button("重置配置", 20, start_y + len(config_categories) * (btn_height + 5) + 70, btn_width, btn_height, 
                      FONT_SMALL, normal_color=COLORS["btn_red"])
    back_btn = Button("返回主菜单", 20, screen_height - 60, btn_width, btn_height, FONT_SMALL)
    
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
                save()
                safe_exit("配置编辑器")
                return
            
            handled = False
            
            if scroll_panel.handle_event(event):
                handled = True
            
            if not handled:
                for btn, idx in category_buttons:
                    if btn.handle_event(event) and btn.clicked:
                        current_category = idx
                        scroll_panel.scroll_offset = 0
                        btn.reset_clicked()
                        handled = True
                        break
                
                if not handled:
                    if save_btn.handle_event(event) and save_btn.clicked:
                        save()
                        show_floating_text("配置已保存！", screen_width // 2, screen_height // 2, COLORS["accent_green"])
                        save_btn.reset_clicked()
                        handled = True
                    
                    if not handled and reset_btn.handle_event(event) and reset_btn.clicked:
                        for category in config_categories:
                            for item in category.items:
                                if item['type'] == 'slider':
                                    item['widget'].value = item['widget'].min_val + (item['widget'].max_val - item['widget'].min_val) / 2
                                elif item['type'] == 'input':
                                    item['widget'].text = ""
                        show_floating_text("配置已重置！", screen_width // 2, screen_height // 2, COLORS["accent_red"])
                        reset_btn.reset_clicked()
                        handled = True
                    
                    if not handled and back_btn.handle_event(event) and back_btn.clicked:
                        save()
                        running = False
                        back_btn.reset_clicked()
                        handled = True
            
            if not handled:
                for item in config_categories[current_category].items:
                    if item['type'] == 'slider':
                        if item['widget'].handle_event(event):
                            handled = True
                            break
                    elif item['type'] == 'input':
                        if item['widget'].handle_event(event):
                            handled = True
                            break
                    elif item['type'] == 'button':
                        if item['widget'].handle_event(event):
                            handled = True
                            break
        
        title_surf = FONT_BIG.render("配置编辑器", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(screen_width // 2, 40))
        screen.blit(title_surf, title_rect)
        
        draw_panel(screen, 15, 70, 260, 550, "配置分类")
        for btn, idx in category_buttons:
            if idx == current_category:
                btn.normal_color = COLORS["accent_gold"]
                btn.text_color = COLORS["bg_dark"]
            else:
                btn.normal_color = COLORS["btn_normal"]
                btn.text_color = COLORS["text_white"]
            btn.draw(screen)
        
        save_btn.draw(screen)
        reset_btn.draw(screen)
        back_btn.draw(screen)
        
        draw_panel(screen, 285, 70, 650, 560, config_categories[current_category].name)
        render_config_panel(screen, scroll_panel, config_categories[current_category].items)
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
    
    save()
    info("配置编辑器关闭")


if __name__ == "__main__":
    main()