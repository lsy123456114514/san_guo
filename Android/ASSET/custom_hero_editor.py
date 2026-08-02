import os
import sys
import json
import pygame
import random
import math
from ASSET.game_data import data, save, RESOURCES
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


QUALITY_COLORS = {
    "common": (150, 150, 150),
    "rare": (70, 130, 220),
    "epic": (180, 100, 220),
    "legendary": (255, 215, 0)
}

ELEMENTS = ["火", "水", "土", "风", "雷", "光", "暗"]
FACTIONS = {"shu": "蜀", "wei": "魏", "wu": "吴", "qun": "群", "jin": "晋"}


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
        
        if self.max_val == self.min_val:
            ratio = 0.0
        else:
            ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        ratio = max(0.0, min(1.0, ratio))
        fill_width = int(self.width * ratio)
        pygame.draw.rect(surface, COLORS["accent_gold"], (self.x, self.y + self.height // 2 - 4, fill_width, 8), border_radius=4)
        
        thumb_x = self.x + fill_width - 8
        thumb_y = self.y + self.height // 2 - 8
        pygame.draw.circle(surface, COLORS["accent_gold"], (thumb_x + 8, thumb_y + 8), 8)
        
        if self.label:
            label_surf = self.font.render(self.label, True, COLORS["text_gray"])
            surface.blit(label_surf, (self.x, self.y - 25))
        
        value_surf = self.font.render(f"{int(self.value)}", True, COLORS["text_white"])
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
        if self.width == 0:
            return
        ratio = max(0, min(1, (mouse_x - self.x) / self.width))
        self.value = int(self.min_val + ratio * (self.max_val - self.min_val))
        if self.on_change:
            self.on_change(self.value)


class Dropdown:
    def __init__(self, x, y, width, height, font, options, initial_index=0, on_change=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.options = options
        self.current_index = initial_index
        self.on_change = on_change
        self.is_open = False
        self.hovered = False
    
    def draw(self, surface, draw_options=True):
        color = COLORS["input_bg"]
        border_color = COLORS["accent_gold"]
        
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height), border_radius=5)
        pygame.draw.rect(surface, border_color, (self.x, self.y, self.width, self.height), 2, border_radius=5)
        
        current_text = self.options[self.current_index] if isinstance(self.options[self.current_index], str) else self.options[self.current_index][0]
        text_surf = self.font.render(current_text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(left=self.x + 10, centery=self.y + self.height // 2)
        surface.blit(text_surf, text_rect)
        
        arrow_surf = self.font.render("▼", True, COLORS["text_gray"])
        arrow_rect = arrow_surf.get_rect(right=self.x + self.width - 10, centery=self.y + self.height // 2)
        surface.blit(arrow_surf, arrow_rect)
        
        if self.is_open and draw_options:
            dropdown_y = self.y + self.height + 5
            for i, option in enumerate(self.options):
                option_text = option if isinstance(option, str) else option[0]
                bg_color = (80, 100, 140) if i == self.current_index else COLORS["input_bg"]
                pygame.draw.rect(surface, bg_color, (self.x, dropdown_y + i * self.height, self.width, self.height), border_radius=3)
                
                text_surf = self.font.render(option_text, True, COLORS["text_white"])
                text_rect = text_surf.get_rect(left=self.x + 10, centery=dropdown_y + i * self.height + self.height // 2)
                surface.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_open:
                dropdown_y = self.y + self.height + 5
                for i, option in enumerate(self.options):
                    if self.x <= event.pos[0] <= self.x + self.width and dropdown_y + i * self.height <= event.pos[1] <= dropdown_y + (i + 1) * self.height:
                        self.current_index = i
                        self.is_open = False
                        if self.on_change:
                            option_value = option if isinstance(option, str) else option[1]
                            self.on_change(option_value)
                        return True
                if not (self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height):
                    self.is_open = False
                    return True
            elif self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= self.y + self.height:
                self.is_open = True
                return True
        return False
    
    def is_clicked_outside(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_open:
            dropdown_y = self.y + self.height + 5
            dropdown_bottom = dropdown_y + len(self.options) * self.height
            if not (self.x <= event.pos[0] <= self.x + self.width and self.y <= event.pos[1] <= dropdown_bottom):
                self.is_open = False
                return True
        return False
    
    def get_dropdown_rect(self):
        if self.is_open:
            dropdown_y = self.y + self.height + 5
            return pygame.Rect(self.x, dropdown_y, self.width, len(self.options) * self.height)
        return None


def draw_panel(surface, x, y, width, height, title=""):
    pygame.draw.rect(surface, COLORS["bg_panel"], (x, y, width, height), border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_gold"], (x, y, width, height), 2, border_radius=10)
    
    if title:
        title_surf = FONT_MAIN.render(title, True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(left=x + 20, top=y + 15)
        surface.blit(title_surf, title_rect)


def main():
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG, FONT_TINY
    
    if not pygame.get_init():
        pygame.init()
    
    screen_width = 1000
    screen_height = 700
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("自定义武将编辑器")
    clock = pygame.time.Clock()
    
    FONT_MAIN = pygame.font.Font(None, 36)
    FONT_SMALL = pygame.font.Font(None, 24)
    FONT_BIG = pygame.font.Font(None, 50)
    FONT_TINY = pygame.font.Font(None, 20)
    
    info("自定义武将编辑器启动")
    
    hero_name_input = TextInput(100, 100, 200, 40, FONT_SMALL, "我的武将")
    quality_dropdown = Dropdown(100, 160, 200, 40, FONT_SMALL, ["common", "rare", "epic", "legendary"], 3)
    element_dropdown = Dropdown(100, 220, 200, 40, FONT_SMALL, ELEMENTS, 0)
    
    faction_options = [(v, k) for k, v in FACTIONS.items()]
    faction_dropdown = Dropdown(100, 280, 200, 40, FONT_SMALL, faction_options, 0)
    
    hp_slider = Slider(100, 350, 200, 40, 50, 1000, 100, FONT_SMALL, "生命值")
    attack_slider = Slider(100, 410, 200, 40, 5, 200, 10, FONT_SMALL, "攻击力")
    defense_slider = Slider(100, 470, 200, 40, 3, 100, 5, FONT_SMALL, "防御力")
    speed_slider = Slider(100, 530, 200, 40, 1, 50, 5, FONT_SMALL, "速度")
    
    skill_name_input = TextInput(500, 100, 200, 40, FONT_SMALL, "普通技能")
    skill_damage_slider = Slider(500, 160, 200, 40, 10, 500, 50, FONT_SMALL, "技能伤害")
    skill_element_dropdown = Dropdown(500, 220, 200, 40, FONT_SMALL, ELEMENTS, 0)
    
    ultimate_name_input = TextInput(750, 100, 200, 40, FONT_SMALL, "终极技能")
    ultimate_damage_slider = Slider(750, 160, 200, 40, 50, 2000, 200, FONT_SMALL, "终极伤害")
    ultimate_element_dropdown = Dropdown(750, 220, 200, 40, FONT_SMALL, ELEMENTS, 0)
    
    passive_name_input = TextInput(500, 300, 200, 40, FONT_SMALL, "被动技能")
    passive_desc_input = TextInput(500, 360, 350, 40, FONT_SMALL, "被动效果描述")
    
    create_btn = Button("创建武将", 100, 600, 200, 50, FONT_MAIN, normal_color=COLORS["btn_green"], 
                       action=lambda: create_custom_hero())
    random_btn = Button("随机生成", 350, 600, 200, 50, FONT_MAIN, normal_color=(70, 130, 220), 
                       action=lambda: randomize_hero())
    back_btn = Button("返回", 750, 600, 200, 50, FONT_MAIN)
    
    cached_labels = {
        'title': FONT_BIG.render("自定义武将编辑器", True, COLORS["accent_gold"]),
        'hero_name': FONT_SMALL.render("武将名称:", True, COLORS["text_gray"]),
        'quality': FONT_SMALL.render("品质:", True, COLORS["text_gray"]),
        'element': FONT_SMALL.render("元素:", True, COLORS["text_gray"]),
        'faction': FONT_SMALL.render("势力:", True, COLORS["text_gray"]),
        'base_attrs': FONT_SMALL.render("基础属性", True, COLORS["accent_gold"]),
        'skill_name': FONT_SMALL.render("普通技能名称:", True, COLORS["text_gray"]),
        'skill_damage': FONT_SMALL.render("技能伤害:", True, COLORS["text_gray"]),
        'skill_element': FONT_SMALL.render("技能元素:", True, COLORS["text_gray"]),
        'passive_name': FONT_SMALL.render("被动技能名称:", True, COLORS["text_gray"]),
        'passive_desc': FONT_SMALL.render("被动效果:", True, COLORS["text_gray"]),
        'ultimate_name': FONT_SMALL.render("终极技能名称:", True, COLORS["text_gray"]),
        'ultimate_damage': FONT_SMALL.render("终极伤害:", True, COLORS["text_gray"]),
        'ultimate_element': FONT_SMALL.render("终极元素:", True, COLORS["text_gray"]),
        'basic_info': "基础信息",
        'skill_settings': "技能设置",
        'ultimate_skill': "终极技能"
    }
    
    floating_texts = []
    
    def show_floating_text(text, x, y, color=COLORS["accent_gold"]):
        text_surf = FONT_MAIN.render(text, True, color)
        floating_texts.append({
            'text': text,
            'x': x,
            'y': y,
            'color': color,
            'alpha': 255,
            'life': 60,
            'surface': text_surf,
            'rect': text_surf.get_rect(center=(x, y))
        })
    
    def create_custom_hero():
        hero_name = hero_name_input.text.strip()
        if not hero_name:
            show_floating_text("请输入武将名称！", screen_width // 2, screen_height // 2, COLORS["accent_red"])
            return
        
        quality = quality_dropdown.options[quality_dropdown.current_index]
        element = element_dropdown.options[element_dropdown.current_index]
        faction_key = faction_dropdown.options[faction_dropdown.current_index][1]
        
        new_hero = {
            "name": hero_name,
            "base_attributes": {
                "hp": hp_slider.value,
                "attack": attack_slider.value,
                "defense": defense_slider.value,
                "speed": speed_slider.value
            },
            "growth_attributes": {
                "hp": hp_slider.value // 20,
                "attack": attack_slider.value // 10,
                "defense": defense_slider.value // 5,
                "speed": speed_slider.value // 5
            },
            "skill": {
                "name": skill_name_input.text.strip() or "普通攻击",
                "damage": skill_damage_slider.value,
                "element": skill_element_dropdown.options[skill_element_dropdown.current_index],
                "cooldown": 3
            },
            "ultimate": {
                "name": ultimate_name_input.text.strip() or "终极技能",
                "damage": ultimate_damage_slider.value,
                "element": ultimate_element_dropdown.options[ultimate_element_dropdown.current_index],
                "cooldown": 10,
                "energy_cost": 100
            },
            "passive": {
                "name": passive_name_input.text.strip() or "被动技能",
                "effect": passive_desc_input.text.strip() or "无特殊效果",
                "trigger_condition": "always"
            },
            "element": element,
            "quality": quality,
            "faction": faction_key,
            "description": f"玩家自定义武将：{hero_name}",
            "story": f"{hero_name}是一位由玩家创造的传奇武将，拥有独特的能力和背景故事。",
            "exclusive_equipment": None
        }
        
        HERO_DATABASE[hero_name] = new_hero
        
        if 'custom_heroes' not in data:
            data['custom_heroes'] = {}
        data['custom_heroes'][hero_name] = new_hero
        
        if hero_name not in data['heroes']:
            data['heroes'][hero_name] = {
                'name': hero_name,
                'level': 1,
                'experience': 0,
                'hp': hp_slider.value,
                'attack': attack_slider.value,
                'defense': defense_slider.value,
                'speed': speed_slider.value,
                'element': element,
                'quality': quality,
                'faction': faction_key,
                'skills': [],
                'equipment': {'weapon': None, 'armor': None, 'horse': None, 'book': None},
                'bond_bonuses': {},
                'awakened': False,
                'rebirth_count': 0,
                'is_custom': True
            }
        
        save()
        show_floating_text(f"武将 '{hero_name}' 创建成功！", screen_width // 2, screen_height // 2, COLORS["accent_green"])
        info(f"玩家创建自定义武将: {hero_name}")
    
    def randomize_hero():
        hero_name_input.text = f"神秘武将_{random.randint(1000, 9999)}"
        quality_dropdown.current_index = random.randint(0, 3)
        element_dropdown.current_index = random.randint(0, len(ELEMENTS) - 1)
        faction_dropdown.current_index = random.randint(0, len(faction_options) - 1)
        
        hp_slider.value = random.randint(100, 500)
        attack_slider.value = random.randint(10, 100)
        defense_slider.value = random.randint(5, 50)
        speed_slider.value = random.randint(5, 30)
        
        skill_damage_slider.value = random.randint(50, 200)
        skill_element_dropdown.current_index = random.randint(0, len(ELEMENTS) - 1)
        
        ultimate_damage_slider.value = random.randint(200, 1000)
        ultimate_element_dropdown.current_index = random.randint(0, len(ELEMENTS) - 1)
        
        skill_name_input.text = ["旋风斩", "烈焰风暴", "寒冰箭", "雷霆一击", "暗影突袭"][random.randint(0, 4)]
        ultimate_name_input.text = ["万军破", "天地毁灭", "星辰陨落", "末日审判", "龙神降临"][random.randint(0, 4)]
        passive_name_input.text = ["战神", "守护", "疾风", "智慧", "幸运"][random.randint(0, 4)]
        passive_desc_input.text = ["战斗中攻击力提升20%", "受到伤害减少15%", "速度提升30%", "经验获取增加25%", "暴击率提升10%"][random.randint(0, 4)]
        
        show_floating_text("随机生成完成！", screen_width // 2, screen_height // 2, COLORS["accent_gold"])
    
    running = True
    while running:
        screen.fill(COLORS["bg_dark"])
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                safe_exit("自定义武将编辑器")
                return
            
            handled = False
            
            open_dropdowns = [d for d in [quality_dropdown, element_dropdown, faction_dropdown, 
                                          skill_element_dropdown, ultimate_element_dropdown] if d.is_open]
            
            for dropdown in open_dropdowns:
                if dropdown.handle_event(event):
                    handled = True
                    break
            
            if not handled:
                for dropdown in [quality_dropdown, element_dropdown, faction_dropdown, 
                                skill_element_dropdown, ultimate_element_dropdown]:
                    if dropdown.is_clicked_outside(event):
                        handled = True
                        break
            
            if not handled:
                handled = hero_name_input.handle_event(event)
            
            if not handled:
                handled = quality_dropdown.handle_event(event)
            
            if not handled:
                handled = element_dropdown.handle_event(event)
            
            if not handled:
                handled = faction_dropdown.handle_event(event)
            
            if not handled:
                handled = hp_slider.handle_event(event)
            
            if not handled:
                handled = attack_slider.handle_event(event)
            
            if not handled:
                handled = defense_slider.handle_event(event)
            
            if not handled:
                handled = speed_slider.handle_event(event)
            
            if not handled:
                handled = skill_name_input.handle_event(event)
            
            if not handled:
                handled = skill_damage_slider.handle_event(event)
            
            if not handled:
                handled = skill_element_dropdown.handle_event(event)
            
            if not handled:
                handled = ultimate_name_input.handle_event(event)
            
            if not handled:
                handled = ultimate_damage_slider.handle_event(event)
            
            if not handled:
                handled = ultimate_element_dropdown.handle_event(event)
            
            if not handled:
                handled = passive_name_input.handle_event(event)
            
            if not handled:
                handled = passive_desc_input.handle_event(event)
            
            if not handled:
                if create_btn.handle_event(event):
                    create_btn.reset_clicked()
                    handled = True
            
            if not handled:
                if random_btn.handle_event(event):
                    random_btn.reset_clicked()
                    handled = True
            
            if not handled:
                if back_btn.handle_event(event) and back_btn.clicked:
                    save()
                    running = False
                    back_btn.reset_clicked()
                    handled = True
        
        try:
            title_rect = cached_labels['title'].get_rect(center=(screen_width // 2, 40))
            screen.blit(cached_labels['title'], title_rect)
            
            draw_panel(screen, 30, 70, 320, 510, cached_labels['basic_info'])
            
            screen.blit(cached_labels['hero_name'], (50, 95))
            hero_name_input.draw(screen)
            
            screen.blit(cached_labels['quality'], (50, 155))
            quality_dropdown.draw(screen, draw_options=False)
            
            screen.blit(cached_labels['element'], (50, 215))
            element_dropdown.draw(screen, draw_options=False)
            
            screen.blit(cached_labels['faction'], (50, 275))
            faction_dropdown.draw(screen, draw_options=False)
            
            screen.blit(cached_labels['base_attrs'], (50, 330))
            
            hp_slider.draw(screen)
            attack_slider.draw(screen)
            defense_slider.draw(screen)
            speed_slider.draw(screen)
            
            draw_panel(screen, 360, 70, 320, 510, cached_labels['skill_settings'])
            
            screen.blit(cached_labels['skill_name'], (380, 95))
            skill_name_input.draw(screen)
            
            screen.blit(cached_labels['skill_damage'], (380, 155))
            skill_damage_slider.draw(screen)
            
            screen.blit(cached_labels['skill_element'], (380, 215))
            skill_element_dropdown.draw(screen, draw_options=False)
            
            screen.blit(cached_labels['passive_name'], (380, 295))
            passive_name_input.draw(screen)
            
            screen.blit(cached_labels['passive_desc'], (380, 355))
            passive_desc_input.draw(screen)
            
            draw_panel(screen, 690, 70, 280, 350, cached_labels['ultimate_skill'])
            
            screen.blit(cached_labels['ultimate_name'], (710, 95))
            ultimate_name_input.draw(screen)
            
            screen.blit(cached_labels['ultimate_damage'], (710, 155))
            ultimate_damage_slider.draw(screen)
            
            screen.blit(cached_labels['ultimate_element'], (710, 215))
            ultimate_element_dropdown.draw(screen, draw_options=False)
            
            create_btn.draw(screen)
            random_btn.draw(screen)
            back_btn.draw(screen)
            
            for dropdown in [quality_dropdown, element_dropdown, faction_dropdown, 
                            skill_element_dropdown, ultimate_element_dropdown]:
                if dropdown.is_open:
                    dropdown.draw(screen, draw_options=True)
            
            for ft in floating_texts[:]:
                ft['y'] -= 2
                ft['alpha'] -= 4
                ft['life'] -= 1
                if ft['life'] <= 0 or ft['alpha'] <= 0:
                    floating_texts.remove(ft)
                    continue
                ft['surface'].set_alpha(ft['alpha'])
                ft['rect'].center = (ft['x'], ft['y'])
                screen.blit(ft['surface'], ft['rect'])
            
            pygame.display.flip()
        except Exception as e:
            error(f"自定义武将编辑器渲染错误: {e}")
            screen.fill(COLORS["bg_dark"])
            error_text = FONT_MAIN.render("渲染出错，正在恢复...", True, COLORS["accent_red"])
            screen.blit(error_text, (screen_width // 2 - 150, screen_height // 2))
            pygame.display.flip()
            pygame.time.delay(1000)
        
        clock.tick(30)
    
    save()
    info("自定义武将编辑器关闭")


if __name__ == "__main__":
    main()