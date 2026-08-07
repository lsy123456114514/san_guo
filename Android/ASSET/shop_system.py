import os
import pygame
import random
import math
import sys
import traceback
import qrcode
from io import BytesIO
from ASSET.game_data import data, save, get_system_font_name, load_sound
from ASSET import safe_exit

# 颜色主题
COLORS = {
    "bg_dark": (15, 20, 35),
    "bg_light": (25, 30, 50),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 220),
    "accent_green": (60, 200, 100),
    "accent_purple": (180, 100, 220),
    "accent_red": (220, 80, 80),
    "text_white": (255, 255, 255),
    "text_gray": (160, 170, 190),
    "panel_bg": (35, 40, 60, 230),
    "btn_green": (50, 160, 80),
    "btn_green_hover": (70, 200, 100),
    "btn_blue": (60, 120, 200),
    "btn_blue_hover": (80, 160, 255),
    "btn_gold": (200, 160, 50),
    "btn_gold_hover": (255, 200, 80)
}

# 商品图标
RESOURCE_ICONS = {
    "水": "水",
    "煤炭": "煤炭",
    "木头": "木头",
    "食物": "食物",
    "金元宝": "金元宝",
    "时间卡": "时间卡",
    "时间卡+": "时间卡+",
    "时间卡++": "时间卡++",
    "宠物食物": "宠物食物",
    "宠物蛋": "宠物蛋",
    "稀有宠物蛋": "稀有宠物蛋",
    "史诗宠物蛋": "史诗宠物蛋",
    "传说宠物蛋": "传说宠物蛋"
}

HERO_ICONS = {
    "张飞": "张飞",
    "关羽": "关羽",
    "赵云": "赵云",
    "马超": "马超",
    "黄忠": "黄忠",
    "诸葛亮": "诸葛亮"
}

# 装备图标
EQUIP_ICONS = {
    "青龙偃月刀": "青龙偃月刀",
    "锁子甲": "锁子甲",
    "的卢马": "的卢马",
    "孙子兵法": "孙子兵法"
}

# 购物车数据结构
class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item_type, name, amount=1, extra_data=None):
        for item in self.items:
            if item['item_type'] == item_type and item['name'] == name:
                item['amount'] += amount
                return True
        self.items.append({
            'item_type': item_type,
            'name': name,
            'amount': amount,
            'extra_data': extra_data
        })
        return True
    
    def remove_item(self, index):
        if 0 <= index < len(self.items):
            removed = self.items.pop(index)
            return True, removed
        return False, None
    
    def update_amount(self, index, amount):
        if 0 <= index < len(self.items):
            if amount <= 0:
                return self.remove_item(index)
            self.items[index]['amount'] = amount
            return True, self.items[index]
        return False, None
    
    def clear(self):
        self.items = []
    
    def get_total_count(self):
        return sum(item['amount'] for item in self.items)
    
    def is_empty(self):
        return len(self.items) == 0

class Particle:
    def __init__(self, x, y, color, speed, size, life):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = random.uniform(-speed, speed)
        self.speed_y = random.uniform(-speed, speed)
        # 重力效果
        self.gravity = 0.1
        self.size = size
        self.life = life
        self.max_life = life
        # 初始角度
        self.angle = random.uniform(0, 2 * math.pi)
        # 旋转速度
        self.rotation_speed = random.uniform(-0.1, 0.1)
        # 发光效果参数
        self.glow_radius = size * 2
    
    def update(self):
        # 应用重力
        self.speed_y += self.gravity
        # 更新位置
        self.x += self.speed_x
        self.y += self.speed_y
        # 更新角度
        self.angle += self.rotation_speed
        # 生命周期
        self.life -= 1
        # 大小变化
        self.size = max(0.5, self.size - 0.05)
        # 发光半径变化
        self.glow_radius = max(0, self.glow_radius - 0.1)
    
    def draw(self, surface):
        # 发光效果
        if self.glow_radius > 0:
            glow_surf = pygame.Surface((self.glow_radius * 2, self.glow_radius * 2), pygame.SRCALPHA)
            # 颜色渐变
            alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
            glow_color = (*self.color[:3], alpha // 4)
            pygame.draw.circle(glow_surf, glow_color, (int(self.glow_radius), int(self.glow_radius)), int(self.glow_radius))
            surface.blit(glow_surf, (int(self.x - self.glow_radius), int(self.y - self.glow_radius)))
        
        # 粒子主体
        alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
        color = (*self.color[:3], alpha)
        # 绘制旋转的粒子
        particle_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, color, (int(self.size), int(self.size)), int(self.size))
        # 旋转粒子
        rotated_surf = pygame.transform.rotate(particle_surf, math.degrees(self.angle))
        rotated_rect = rotated_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_surf, rotated_rect)

class FloatingText:
    def __init__(self, text, x, y, color, font):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.life = 50
        self.max_life = 50
        self.speed_y = -1.5
        self.scale = 1.0
    
    def update(self):
        self.y += self.speed_y
        self.life -= 1
        if self.life > 40:
            self.scale = min(1.3, self.scale + 0.03)
        else:
            self.scale = max(1.0, self.scale - 0.02)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
        text_surf = self.font.render(self.text, True, self.color)
        scaled_size = (int(text_surf.get_width() * self.scale), int(text_surf.get_height() * self.scale))
        scaled_surf = pygame.transform.scale(text_surf, scaled_size)
        scaled_surf.set_alpha(alpha)
        rect = scaled_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(scaled_surf, rect)

class ScrollableContainer:
    def __init__(self, x, y, width, height, screen):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen = screen
        self.scroll_y = 0
        self.content_height = 0
        self.is_scrolling = False
        self.last_mouse_y = 0
        self.scrollbar_width = 10
        self.scrollbar_height = 50
    
    def handle_event(self, event, mouse_pos):
        # 处理鼠标事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # 检查是否点击滚动条
                scrollbar_x = self.x + self.width - self.scrollbar_width - 5
                scrollbar_y = self.y + 5 + (self.scroll_y / self.content_height) * (self.height - 10 - self.scrollbar_height)
                if scrollbar_x <= mouse_pos[0] <= scrollbar_x + self.scrollbar_width and \
                   scrollbar_y <= mouse_pos[1] <= scrollbar_y + self.scrollbar_height:
                    self.is_scrolling = True
                    self.last_mouse_y = mouse_pos[1]
                    return True  # 返回True表示点击了滚动条
            elif event.button == 4:  # 鼠标滚轮向上
                self.scroll_y = max(0, self.scroll_y - 20)
            elif event.button == 5:  # 鼠标滚轮向下
                self.scroll_y = min(self.content_height - self.height, self.scroll_y + 20)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_scrolling = False
        elif event.type == pygame.MOUSEMOTION:
            if self.is_scrolling:
                delta_y = mouse_pos[1] - self.last_mouse_y
                scroll_ratio = delta_y / (self.height - self.scrollbar_height)
                self.scroll_y += scroll_ratio * self.content_height
                self.scroll_y = max(0, min(self.content_height - self.height, self.scroll_y))
                self.last_mouse_y = mouse_pos[1]
        return False  # 返回False表示没有点击滚动条
    
    def draw_background(self):
        """只绘制容器背景和边框（在按钮之前调用）"""
        # 绘制容器背景
        container_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(container_surf, (30, 35, 55, 180), (0, 0, self.width, self.height), border_radius=8)
        self.screen.blit(container_surf, (self.x, self.y))
        
        # 绘制边框
        pygame.draw.rect(self.screen, COLORS["accent_gold"], (self.x, self.y, self.width, self.height), 2, border_radius=8)
    
    def draw(self):
        """绘制滚动条（在按钮之后调用）"""
        # 绘制滚动条
        if self.content_height > self.height:
            scrollbar_x = self.x + self.width - self.scrollbar_width - 5
            scrollbar_y = self.y + 5 + (self.scroll_y / self.content_height) * (self.height - 10 - self.scrollbar_height)
            pygame.draw.rect(self.screen, (80, 90, 120), 
                           (scrollbar_x, scrollbar_y, self.scrollbar_width, self.scrollbar_height), 
                           border_radius=5)
            pygame.draw.rect(self.screen, COLORS["accent_gold"], 
                           (scrollbar_x, scrollbar_y, self.scrollbar_width, self.scrollbar_height), 
                           1, border_radius=5)

class AnimatedButton:
    def __init__(self, x, y, width, height, text, font, 
                 normal_color, hover_color, text_color=(255, 255, 255), scale=1.0):
        # 保存原始尺寸和位置
        self.original_x = x
        self.original_y = y
        self.original_width = width
        self.original_height = height
        self.text = text
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.scale = 1.0
        self.glow_alpha = 0
        self.particles = []
        self.screen_scale = scale
        # 添加计数器，控制粒子创建频率
        self.particle_cooldown = 0
        self.particle_cooldown_max = 15  # 每15帧最多创建一次粒子
        # 初始化矩形
        self.update_rect()
    
    def update_rect(self):
        """根据当前缩放因子更新按钮矩形"""
        self.rect = pygame.Rect(
            int(self.original_x * self.screen_scale),
            int(self.original_y * self.screen_scale),
            int(self.original_width * self.screen_scale),
            int(self.original_height * self.screen_scale)
        )
    
    def update(self, mouse_pos):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # 更新粒子冷却计数器
        if self.particle_cooldown > 0:
            self.particle_cooldown -= 1
        
        if self.is_hovered:
            self.scale = min(1.05, self.scale + 0.02)
            self.glow_alpha = min(100, self.glow_alpha + 8)
            # 只有当鼠标刚刚进入按钮区域，并且冷却时间已到，才创建粒子
            if not was_hovered and self.particle_cooldown <= 0:
                for _ in range(8):
                    # 基于缩放后的按钮位置创建粒子
                    scaled_width = int(self.rect.width * self.scale)
                    scaled_height = int(self.rect.height * self.scale)
                    scaled_x = self.rect.x + (self.rect.width - scaled_width) // 2
                    scaled_y = self.rect.y + (self.rect.height - scaled_height) // 2
                    
                    # 从按钮顶部随机位置生成粒子，避免在按钮下方生成
                    x = random.randint(scaled_x, scaled_x + scaled_width)
                    y = scaled_y - 10  # 在按钮上方生成粒子
                    
                    # 随机速度，确保粒子向上移动且有水平随机性
                    speed_x = random.uniform(-2, 2)  # 增加水平速度范围
                    speed_y = random.uniform(-5, -3)  # 增加向上速度，确保粒子向上飞
                    
                    # 基于按钮颜色生成粒子颜色
                    if self.hover_color == COLORS["btn_green_hover"]:
                        # 绿色按钮使用绿色系粒子
                        particle_color = random.choice([(50, 200, 100), (70, 220, 120), (30, 180, 80)])
                    elif self.hover_color == COLORS["btn_blue_hover"]:
                        # 蓝色按钮使用蓝色系粒子
                        particle_color = random.choice([(60, 120, 200), (80, 160, 255), (40, 100, 180)])
                    elif self.hover_color == COLORS["btn_gold_hover"]:
                        # 金色按钮使用金色系粒子
                        particle_color = random.choice([(200, 160, 50), (255, 200, 80), (180, 140, 30)])
                    else:
                        # 默认使用金色粒子
                        particle_color = COLORS["accent_gold"]
                    
                    # 创建粒子
                    particle = Particle(
                        x, y, particle_color,
                        2, random.uniform(2, 5), random.randint(25, 35)
                    )
                    
                    # 覆盖速度值
                    particle.speed_x = speed_x
                    particle.speed_y = speed_y
                    particle.gravity = 0.01  # 非常小的重力，几乎可以忽略
                    
                    # 添加随机性
                    particle.rotation_speed = random.uniform(-0.2, 0.2)
                    particle.glow_radius = particle.size * 3
                    
                    self.particles.append(particle)
                # 重置冷却计数器
                self.particle_cooldown = self.particle_cooldown_max
        else:
            self.scale = max(1.0, self.scale - 0.02)
            self.glow_alpha = max(0, self.glow_alpha - 8)
        
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
    
    def draw(self, surface):
        # 发光效果
        if self.glow_alpha > 0:
            glow_surf = pygame.Surface((self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*self.hover_color[:3], self.glow_alpha),
                           (10, 10, self.rect.width, self.rect.height), border_radius=10)
            surface.blit(glow_surf, (self.rect.x - 10, self.rect.y - 10))
        
        # 按钮主体
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_x = self.rect.x + (self.rect.width - scaled_width) // 2
        scaled_y = self.rect.y + (self.rect.height - scaled_height) // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        color = self.hover_color if self.is_hovered else self.normal_color
        
        # 渐变按钮
        for i in range(scaled_height):
            ratio = i / scaled_height
            r = int(color[0] * (1 - ratio * 0.25))
            g = int(color[1] * (1 - ratio * 0.25))
            b = int(color[2] * (1 - ratio * 0.25))
            pygame.draw.line(surface, (r, g, b), 
                           (scaled_x, scaled_y + i), 
                           (scaled_x + scaled_width, scaled_y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], scaled_rect, 2, border_radius=8)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)
        
        # 粒子
        for p in self.particles:
            p.draw(surface)

def draw_gradient_background(surface, color1, color2):
    """绘制渐变背景"""
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_shop_item_card(surface, x, y, width, height, icon, name, info, font_small, font_icon, scale=1.0):
    """绘制商品卡片"""
    # 卡片背景
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (40, 45, 65, 220), (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], (x, y, width, height), 2, border_radius=12)
    
    # 名称
    name_surf = font_small.render(name, True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + width // 2, y + height * 0.4))
    surface.blit(name_surf, name_rect)
    
    # 信息
    info_surf = font_small.render(info, True, COLORS["text_gray"])
    info_rect = info_surf.get_rect(center=(x + width // 2, y + height * 0.6))
    surface.blit(info_surf, info_rect)

def draw_resource_bar(surface, x, y, screen_width, font_small, scale=1.0):
    """绘制资源栏"""
    bar_height = int(45 * scale)
    max_items_per_row = 6
    
    # 背景
    bar_surf = pygame.Surface((screen_width - 40, bar_height * 2), pygame.SRCALPHA)
    pygame.draw.rect(bar_surf, (30, 35, 55, 200), (0, 0, screen_width - 40, bar_height * 2), border_radius=8)
    surface.blit(bar_surf, (x, y))
    pygame.draw.rect(surface, COLORS["accent_gold"], (x, y, screen_width - 40, bar_height * 2), 1, border_radius=8)
    
    # 资源显示（无表情）
    resource_names = ['金元宝', '水', '食物', '煤炭', '木头', '时间卡', '时间卡+', '时间卡++']
    
    # 过滤掉数量为0的资源
    display_resources = [(name, data['resources'].get(name, 0)) for name in resource_names if data['resources'].get(name, 0) > 0]
    
    if not display_resources:
        # 至少显示金元宝
        display_resources = [('金元宝', data['resources'].get('金元宝', 0))]
    
    # 计算每行显示的资源数量
    items_per_row = min(max_items_per_row, len(display_resources))
    spacing = (screen_width - 60) // items_per_row
    
    # 分多行显示
    for i, (name, amount) in enumerate(display_resources):
        row = i // max_items_per_row
        col = i % max_items_per_row
        
        name_surf = font_small.render(name, True, COLORS["text_white"])
        amount_surf = font_small.render(str(amount), True, COLORS["accent_gold"])
        
        item_x = x + 20 + col * spacing
        item_y = y + row * 25 * scale
        surface.blit(name_surf, (item_x, item_y))
        surface.blit(amount_surf, (item_x, item_y + 18 * scale))

def main():
    """商城主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
            pygame.mixer.init()
        
        # 分辨率适配
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            # 使用设置的分辨率
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 900
                SCREEN_HEIGHT = 700
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("游戏商城")
        clock = pygame.time.Clock()

        # 计算缩放因子
        scale = min(SCREEN_WIDTH / 900, SCREEN_HEIGHT / 700)

        # 字体初始化（根据屏幕大小自适应）
        def init_font(size):
            # 尝试多个字体，按优先级排序
            font_list = [
                get_system_font_name(),  # 系统字体
                "Arial Unicode MS",       # 支持多语言和emoji
                "SimHei",               # 黑体
                "Microsoft YaHei",      # 微软雅黑
                None                     # 默认字体
            ]
            
            adjusted_size = int(size * scale)
            
            for font_name in font_list:
                try:
                    if font_name:
                        font = pygame.font.SysFont(font_name, adjusted_size)
                    else:
                        font = pygame.font.Font(None, adjusted_size)
                    
                    # 测试字体是否能正确渲染中文
                    test_text = "测试中文 金元宝"
                    test_surface = font.render(test_text, True, (255, 255, 255))
                    if test_surface and test_surface.get_width() > 0:
                        return font
                except Exception:
                    continue
            
            # 最后使用默认字体
            return pygame.font.Font(None, adjusted_size)

        font_title = init_font(36 if not 'ANDROID_DATA' in os.environ else 52)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        font_icon = init_font(36 if not 'ANDROID_DATA' in os.environ else 48)

        # 加载音效
        click_sound = load_sound("click.wav")
        success_sound = load_sound("success.wav")

        def play_sound(sound):
            if sound and data['settings']['sound']['enable']:
                try:
                    sound.play()
                except Exception:
                    pass

        # 购买逻辑（全部免费）
        def buy_resource(resource_name, amount):
            # 处理不同品质的宠物蛋
            if resource_name == "稀有宠物蛋":
                data["resources"]["rare_pet_eggs"] = data["resources"].get("rare_pet_eggs", 0) + amount
            elif resource_name == "史诗宠物蛋":
                data["resources"]["epic_pet_eggs"] = data["resources"].get("epic_pet_eggs", 0) + amount
            elif resource_name == "传说宠物蛋":
                data["resources"]["legendary_pet_eggs"] = data["resources"].get("legendary_pet_eggs", 0) + amount
            else:
                data["resources"][resource_name] = data["resources"].get(resource_name, 0) + amount
            save()
            return True

        def buy_hero_fragments(hero_name, fragments):
            data["hero_fragments"][hero_name] = data["hero_fragments"].get(hero_name, 0) + fragments
            save()
            return True

        def buy_equip(equip_name, equip_type):
            if "equips" not in data:
                data["equips"] = {}
            if equip_type not in data["equips"]:
                data["equips"][equip_type] = []
            data["equips"][equip_type].append(equip_name)
            save()
            return True

        def random_draw_hero():
            """随机抽卡"""
            HERO_POOL = ["张飞","关羽","赵云","马超","黄忠","刘备","诸葛亮","吕布"]
            hero = random.choice(HERO_POOL)
            fragments = random.randint(1, 5)
            data["hero_fragments"][hero] = data["hero_fragments"].get(hero, 0) + fragments
            save()
            return hero, fragments

        TIME_CARD_RECIPES = {
            "时间卡": {
                "水": 100,
                "煤炭": 50,
                "木头": 80,
                "食物": 60
            },
            "时间卡+": {
                "水": 200,
                "煤炭": 100,
                "木头": 160,
                "食物": 120
            },
            "时间卡++": {
                "水": 300,
                "煤炭": 150,
                "木头": 240,
                "食物": 180
            }
        }

        def craft_time_card(card_level="时间卡"):
            """合成时间卡"""
            required_resources = TIME_CARD_RECIPES.get(card_level, TIME_CARD_RECIPES["时间卡"])
            
            if "resources" not in data:
                data["resources"] = {}
            
            for resource, amount in required_resources.items():
                if data["resources"].get(resource, 0) < amount:
                    return False, f"资源不足：需要{amount}个{resource}"
            
            for resource, amount in required_resources.items():
                data["resources"][resource] -= amount
            
            data["resources"][card_level] = data["resources"].get(card_level, 0) + 1
            save()
            return True, f"合成{card_level}成功！"
        
        # 购物车弹窗状态
        show_cart = False
        cart_scroll_y = 0
        
        # 扫码支付状态
        qr_verify_code = ""
        show_qr_payment = False
        qr_input_text = ""
        qr_payment_success = False

        # 商城配置
        RESOURCE_SHOP = [
            {"name": "水", "amount": 100},
            {"name": "煤炭", "amount": 50},
            {"name": "木头", "amount": 80},
            {"name": "食物", "amount": 60},
            {"name": "金元宝", "amount": 20},
            {"name": "时间卡", "amount": 1},
            {"name": "时间卡+", "amount": 1},
            {"name": "时间卡++", "amount": 1},
            {"name": "宠物食物", "amount": 5},
            {"name": "宠物蛋", "amount": 1},
            {"name": "稀有宠物蛋", "amount": 1},
            {"name": "史诗宠物蛋", "amount": 1},
            {"name": "传说宠物蛋", "amount": 1}
        ]

        HERO_SHOP = [
            {"name": "张飞", "fragments": 5},
            {"name": "关羽", "fragments": 5},
            {"name": "赵云", "fragments": 5},
            {"name": "马超", "fragments": 5},
            {"name": "黄忠", "fragments": 5},
            {"name": "诸葛亮", "fragments": 5}
        ]

        EQUIP_SHOP = [
            {"name": "青龙偃月刀", "type": "weapon"},
            {"name": "锁子甲", "type": "armor"},
            {"name": "的卢马", "type": "horse"},
            {"name": "孙子兵法", "type": "book"}
        ]

        # 特效
        particles = []
        floating_texts = []
        
        # 背景星星
        stars = []
        for _ in range(40):
            stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 2),
                'alpha': random.randint(30, 100),
                'twinkle': random.uniform(0.02, 0.05)
            })

        # 卡片尺寸（自适应）
        card_width = min(140, SCREEN_WIDTH * 0.15)
        card_height = min(130, SCREEN_HEIGHT * 0.18)
        btn_height = min(35, SCREEN_HEIGHT * 0.05)
        
        # 创建滚动容器（在主循环之前，保持滚动状态）
        container_x = 20
        container_y = 150 * scale
        container_width = SCREEN_WIDTH - 40
        # 计算滚动容器的高度，确保它不会挡住返回按钮
        return_btn_height = min(50, SCREEN_HEIGHT * 0.08)
        container_height = SCREEN_HEIGHT - container_y - return_btn_height - 60  # 为返回按钮留出足够的空间
        scroll_container = ScrollableContainer(container_x, container_y, container_width, container_height, screen)
        
        # 计算内容高度
        # 资源购买区
        resource_cols = min(5, max(3, container_width // int((card_width + 20))))
        resource_rows = (len(RESOURCE_SHOP) + resource_cols - 1) // resource_cols
        resource_section_height = 40 * scale + resource_rows * (card_height + 20)
        
        # 武将碎片区
        hero_cols = min(3, max(2, container_width // int((card_width + 20))))
        hero_rows = (len(HERO_SHOP) + hero_cols - 1) // hero_cols
        hero_section_height = 40 * scale + hero_rows * (card_height + 20)
        
        # 装备购买区
        equip_cols = min(4, max(2, container_width // int((card_width + 20))))
        equip_rows = (len(EQUIP_SHOP) + equip_cols - 1) // equip_cols
        equip_section_height = 40 * scale + equip_rows * (card_height + 20)
        
        # 合成区和抽卡区
        other_section_height = 600 * scale
        
        # 总内容高度
        scroll_container.content_height = resource_section_height + hero_section_height + equip_section_height + other_section_height

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 绘制星星
            for star in stars:
                star['alpha'] += math.sin(pygame.time.get_ticks() * star['twinkle']) * 2
                star['alpha'] = max(20, min(100, star['alpha']))
                star_surf = pygame.Surface((star['size'] * 2, star['size'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(star_surf, (255, 255, 255, int(star['alpha'])), 
                                 (star['size'], star['size']), star['size'])
                screen.blit(star_surf, (star['x'], star['y']))

            # 标题
            title_surf = font_title.render("游戏商城", True, COLORS["accent_gold"])
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 35 * scale))
            screen.blit(title_surf, title_rect)
            
            # 副标题
            sub_surf = font_small.render("全部商品免费购买！", True, COLORS["accent_green"])
            sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 70 * scale))
            screen.blit(sub_surf, sub_rect)

            # 资源栏
            draw_resource_bar(screen, 20, 95 * scale, SCREEN_WIDTH, font_small, scale)
            
            # 计算滚动后的实际绘制位置
            scroll_offset = -scroll_container.scroll_y
            
            # 保存所有按钮，用于事件处理
            resource_btns = []
            hero_btns = []
            equip_btns = []
            level_btns = []
            craft_btn = None
            draw_card_btn = None
            
            # 先绘制滚动容器背景（在按钮之前）
            scroll_container.draw_background()
            
            # 绘制内容
            content_y = 0 + scroll_offset
            
            # 资源购买区
            section_title = font_normal.render("资源购买", True, COLORS["accent_blue"])
            screen.blit(section_title, (container_x + 10, container_y + content_y))
            content_y += 40 * scale
            
            start_y = content_y
            for idx, res in enumerate(RESOURCE_SHOP):
                col = idx % resource_cols
                row = idx // resource_cols
                x = container_x + 10 + col * (card_width + 15)
                y = container_y + start_y + row * (card_height + 20)
                
                # 只绘制在容器内的卡片
                if y + card_height > container_y and y < container_y + container_height:
                    icon = RESOURCE_ICONS.get(res['name'], "📦")
                    draw_shop_item_card(screen, x, y, card_width, card_height, 
                                      icon, res['name'], f"×{res['amount']}", font_small, font_icon, scale)
                    
                    # 购买按钮 - 使用相对位置，不进行额外的缩放
                    btn_x = x + 10
                    btn_y = y + card_height - btn_height - 5
                    btn = AnimatedButton(
                        btn_x, btn_y, (card_width - 20) // 2 - 2, btn_height,
                        "购买", font_small, COLORS["btn_green"], COLORS["btn_green_hover"], (255, 255, 255), 1.0
                    )
                    btn.update((mx, my))
                    btn.draw(screen)
                    resource_btns.append((btn, res["name"], res["amount"]))
                    
                    # 加入购物车按钮
                    cart_btn_x = x + 10 + (card_width - 20) // 2 + 2
                    cart_btn = AnimatedButton(
                        cart_btn_x, btn_y, (card_width - 20) // 2 - 2, btn_height,
                        "购物车", font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"], (255, 255, 255), 1.0
                    )
                    cart_btn.update((mx, my))
                    cart_btn.draw(screen)
                    resource_btns.append((cart_btn, res["name"], res["amount"], "cart"))
            
            content_y += resource_rows * (card_height + 20) + 50 * scale
            
            # 武将碎片区
            section_title = font_normal.render("武将碎片", True, COLORS["accent_purple"])
            screen.blit(section_title, (container_x + 10, container_y + content_y))
            content_y += 40 * scale
            
            start_y = content_y
            for idx, hero in enumerate(HERO_SHOP):
                col = idx % hero_cols
                row = idx // hero_cols
                x = container_x + 10 + col * (card_width + 20)
                y = container_y + start_y + row * (card_height + 20)
                
                # 只绘制在容器内的卡片
                if y + card_height > container_y and y < container_y + container_height:
                    icon = HERO_ICONS.get(hero['name'], "👤")
                    current_frags = data["hero_fragments"].get(hero["name"], 0)
                    draw_shop_item_card(screen, x, y, card_width, card_height,
                                      icon, hero['name'], f"碎片×{hero['fragments']}", font_small, font_icon, scale)
                    
                    # 当前拥有
                    have_surf = font_small.render(f"拥有: {current_frags}", True, COLORS["text_gray"])
                    screen.blit(have_surf, (x + 10, y + card_height * 0.65))
                    
                    # 购买按钮 - 使用相对位置，不进行额外的缩放
                    btn_x = x + 10
                    btn_y = y + card_height - btn_height - 5
                    btn = AnimatedButton(
                        btn_x, btn_y, (card_width - 20) // 2 - 2, btn_height,
                        "购买", font_small, COLORS["btn_blue"], COLORS["btn_blue_hover"], (255, 255, 255), 1.0
                    )
                    btn.update((mx, my))
                    btn.draw(screen)
                    hero_btns.append((btn, hero["name"], hero["fragments"]))
                    
                    # 加入购物车按钮
                    cart_btn_x = x + 10 + (card_width - 20) // 2 + 2
                    cart_btn = AnimatedButton(
                        cart_btn_x, btn_y, (card_width - 20) // 2 - 2, btn_height,
                        "购物车", font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"], (255, 255, 255), 1.0
                    )
                    cart_btn.update((mx, my))
                    cart_btn.draw(screen)
                    hero_btns.append((cart_btn, hero["name"], hero["fragments"], "cart"))
            
            content_y += hero_rows * (card_height + 20) + 50 * scale
            
            # 装备购买区
            section_title = font_normal.render("装备购买", True, COLORS["accent_red"])
            screen.blit(section_title, (container_x + 10, container_y + content_y))
            content_y += 40 * scale
            
            start_y = content_y
            for idx, equip in enumerate(EQUIP_SHOP):
                col = idx % equip_cols
                row = idx // equip_cols
                x = container_x + 10 + col * (card_width + 15)
                y = container_y + start_y + row * (card_height + 20)
                
                # 只绘制在容器内的卡片
                if y + card_height > container_y and y < container_y + container_height:
                    icon = EQUIP_ICONS.get(equip['name'], "装备")
                    draw_shop_item_card(screen, x, y, card_width, card_height,
                                      icon, equip['name'], "装备", font_small, font_icon, scale)
                    
                    # 购买按钮 - 使用相对位置，不进行额外的缩放
                    btn_x = x + 10
                    btn_y = y + card_height - btn_height - 5
                    btn = AnimatedButton(
                        btn_x, btn_y, (card_width - 20) // 2 - 2, btn_height,
                        "购买", font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"], (255, 255, 255), 1.0
                    )
                    btn.update((mx, my))
                    btn.draw(screen)
                    equip_btns.append((btn, equip["name"], equip["type"]))
                    
                    # 加入购物车按钮
                    cart_btn_x = x + 10 + (card_width - 20) // 2 + 2
                    cart_btn = AnimatedButton(
                        cart_btn_x, btn_y, (card_width - 20) // 2 - 2, btn_height,
                        "购物车", font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"], (255, 255, 255), 1.0
                    )
                    cart_btn.update((mx, my))
                    cart_btn.draw(screen)
                    equip_btns.append((cart_btn, equip["name"], equip["type"], "cart"))
            
            content_y += equip_rows * (card_height + 20) + 50 * scale
            
            # 合成区
            section_title = font_small.render("时间卡合成", True, COLORS["accent_purple"])
            screen.blit(section_title, (container_x + 10, container_y + content_y))
            content_y += 35 * scale
            
            # 时间卡等级选择
            card_levels = ["时间卡", "时间卡+", "时间卡++"]
            selected_level = 0
            craft_start_y = content_y
            
            for i, level in enumerate(card_levels):
                x = container_x + 10 + i * 100
                y = container_y + craft_start_y
                
                if y + 40 > container_y and y < container_y + container_height:
                    level_btn = AnimatedButton(
                        x, y,
                        90, 35,
                        level, font_small, 
                        COLORS["btn_blue"] if i == selected_level else (80, 80, 120), 
                        COLORS["btn_blue_hover"],
                        (255, 255, 255), 1.0
                    )
                    level_btn.update((mx, my))
                    level_btn.draw(screen)
                    level_btns.append((level_btn, i))
                    if i == selected_level:
                        # 显示选中状态
                        pygame.draw.rect(screen, COLORS["accent_gold"], 
                                       (x, y, 90, 35), 2, border_radius=8)
            
            # 合成卡片
            craft_card_x = container_x + 10
            craft_card_y = container_y + craft_start_y + 60
            craft_card_width = min(300, container_width * 0.7)
            craft_card_height = 150
            
            if craft_card_y + craft_card_height > container_y and craft_card_y < container_y + container_height:
                selected_card = card_levels[selected_level]
                recipe = TIME_CARD_RECIPES[selected_card]
                
                # 合成卡片背景
                craft_surf = pygame.Surface((craft_card_width, craft_card_height), pygame.SRCALPHA)
                pygame.draw.rect(craft_surf, (40, 45, 65, 220), (0, 0, craft_card_width, craft_card_height), border_radius=12)
                screen.blit(craft_surf, (craft_card_x, craft_card_y))
                pygame.draw.rect(screen, COLORS["accent_gold"], (craft_card_x, craft_card_y, craft_card_width, craft_card_height), 2, border_radius=12)
                
                # 图标
                icon_surf = font_icon.render("时间卡", True, COLORS["text_white"])
                icon_rect = icon_surf.get_rect(center=(craft_card_x + 40, craft_card_y + craft_card_height // 2))
                screen.blit(icon_surf, icon_rect)
                
                # 合成信息
                info_y = craft_card_y + 30 * scale
                craft_info = [
                    (selected_card, "1个"),
                    ("需要:", ""),
                    ("水", str(recipe["水"])),
                    ("煤炭", str(recipe["煤炭"])),
                    ("木头", str(recipe["木头"])),
                    ("食物", str(recipe["食物"]))
                ]
                
                for i, (text, value) in enumerate(craft_info):
                    text_surf = font_small.render(text, True, COLORS["text_white"])
                    value_surf = font_small.render(value, True, COLORS["accent_gold"])
                    screen.blit(text_surf, (craft_card_x + 80, info_y + i * 20 * scale))
                    screen.blit(value_surf, (craft_card_x + craft_card_width - 60, info_y + i * 20 * scale))
                
                # 合成按钮
                craft_btn = AnimatedButton(
                    craft_card_x + 80, craft_card_y + craft_card_height - 40, craft_card_width - 90, 35,
                    "合成", font_small, COLORS["btn_blue"], COLORS["btn_blue_hover"], (255, 255, 255),
                    1.0
                )
                craft_btn.update((mx, my))
                craft_btn.draw(screen)
            
            content_y += 250 * scale
            
            # 抽卡区
            section_title = font_small.render("免费抽卡", True, COLORS["accent_purple"])
            screen.blit(section_title, (container_x + 10, container_y + content_y))
            content_y += 35 * scale
            
            # 抽卡卡片
            draw_card_width = min(200, container_width * 0.5)
            draw_card_height = 150
            draw_card_x = container_x + 10
            draw_card_y = container_y + content_y
            
            if draw_card_y + draw_card_height > container_y and draw_card_y < container_y + container_height:
                draw_shop_item_card(screen, draw_card_x, draw_card_y, draw_card_width, draw_card_height,
                                  "抽卡", "随机抽卡", "1-5碎片", font_small, font_icon, scale)
                
                draw_card_btn = AnimatedButton(
                    draw_card_x + 15, draw_card_y + draw_card_height - 45,
                    draw_card_width - 30, 40,
                    "免费抽取", font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"], (255, 255, 255),
                    1.0
                )
                draw_card_btn.update((mx, my))
                draw_card_btn.draw(screen)
            
            content_y += 180 * scale
            
            # 扫码支付区
            section_title = font_small.render("扫码支付（免费）", True, COLORS["accent_green"])
            screen.blit(section_title, (container_x + 10, container_y + content_y))
            content_y += 35 * scale
            
            qr_card_width = min(200, container_width * 0.5)
            qr_card_height = 220
            qr_card_x = container_x + 10
            qr_card_y = container_y + content_y
            
            qr_rect = None
            if qr_card_y + qr_card_height > container_y and qr_card_y < container_y + container_height:
                qr_bg = pygame.Surface((qr_card_width, qr_card_height), pygame.SRCALPHA)
                pygame.draw.rect(qr_bg, (40, 45, 65, 220), (0, 0, qr_card_width, qr_card_height), border_radius=12)
                screen.blit(qr_bg, (qr_card_x, qr_card_y))
                pygame.draw.rect(screen, COLORS["accent_gold"], (qr_card_x, qr_card_y, qr_card_width, qr_card_height), 2, border_radius=12)
                
                # 二维码区域
                qr_size = min(120, qr_card_width * 0.6)
                qr_x = qr_card_x + (qr_card_width - qr_size) // 2
                qr_y = qr_card_y + 20
                
                qr_surf = pygame.Surface((qr_size, qr_size), pygame.SRCALPHA)
                qr_surf.fill((255, 255, 255))
                
                # 绘制简单的QR码图案（使用固定种子避免闪烁）
                cell_size = qr_size // 21
                random.seed(42)
                for i in range(21):
                    for j in range(21):
                        if ((i < 7 and j < 7) or (i < 7 and j > 13) or (i > 13 and j < 7)):
                            if (i < 5 and j < 5) or (i < 5 and j > 15) or (i > 15 and j < 5):
                                pygame.draw.rect(qr_surf, (0, 0, 0), (j * cell_size, i * cell_size, cell_size, cell_size))
                            if (i == 3 + (j < 7) * 14) and (j == 3 + (i < 7) * 14):
                                pygame.draw.rect(qr_surf, (255, 255, 255), (j * cell_size - cell_size, i * cell_size - cell_size, cell_size * 3, cell_size * 3))
                                pygame.draw.rect(qr_surf, (0, 0, 0), (j * cell_size, i * cell_size, cell_size, cell_size))
                        elif random.random() > 0.5:
                            pygame.draw.rect(qr_surf, (0, 0, 0), (j * cell_size, i * cell_size, cell_size, cell_size))
                
                screen.blit(qr_surf, (qr_x, qr_y))
                
                # 微信图标
                wx_icon = font_icon.render("微信支付", True, (0, 150, 50))
                wx_rect = wx_icon.get_rect(center=(qr_card_x + qr_card_width // 2, qr_y + qr_size + 25))
                screen.blit(wx_icon, wx_rect)
                
                # 点击二维码提示
                hint_text = font_small.render("点击二维码获取校验码", True, COLORS["text_gray"])
                hint_rect = hint_text.get_rect(center=(qr_card_x + qr_card_width // 2, qr_y + qr_size + 50))
                screen.blit(hint_text, hint_rect)
                
                qr_rect = pygame.Rect(qr_x, qr_y, qr_size, qr_size)
            
            content_y += 250 * scale
            
            # 绘制滚动容器
            scroll_container.draw()

            # 返回按钮（自适应）
            return_btn_width = min(160, SCREEN_WIDTH * 0.25)
            return_btn_height = min(50, SCREEN_HEIGHT * 0.08)
            return_btn_y = SCREEN_HEIGHT - return_btn_height - 30
            return_btn = AnimatedButton(
                (SCREEN_WIDTH - return_btn_width) // 2, return_btn_y,
                return_btn_width, return_btn_height, "返回", font_normal,
                (60, 120, 60), (80, 160, 80), (255, 255, 255),
                1.0  # 使用1.0作为缩放因子，因为我们已经根据屏幕大小计算了正确的尺寸
            )
            return_btn.update((mx, my))
            return_btn.draw(screen)

            # 购物车图标按钮
            cart_btn_size = min(60, SCREEN_WIDTH * 0.08)
            cart_btn_x = SCREEN_WIDTH - cart_btn_size - 20
            cart_btn_y = 20 * scale
            cart_icon_rect = pygame.Rect(cart_btn_x, cart_btn_y, cart_btn_size, cart_btn_size)
            
            cart_surf = pygame.Surface((cart_btn_size, cart_btn_size), pygame.SRCALPHA)
            pygame.draw.rect(cart_surf, COLORS["btn_gold"], (0, 0, cart_btn_size, cart_btn_size), border_radius=10)
            pygame.draw.rect(cart_surf, COLORS["text_white"], (0, 0, cart_btn_size, cart_btn_size), 2, border_radius=10)
            
            cart_icon_text = font_icon.render("🛒", True, COLORS["text_white"])
            cart_icon_rect_text = cart_icon_text.get_rect(center=(cart_btn_size // 2, cart_btn_size // 2 - 5))
            cart_surf.blit(cart_icon_text, cart_icon_rect_text)
            
            if cart_icon_rect.collidepoint(mx, my):
                glow_surf = pygame.Surface((cart_btn_size + 10, cart_btn_size + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*COLORS["btn_gold_hover"], 50), (5, 5, cart_btn_size, cart_btn_size), border_radius=12)
                screen.blit(glow_surf, (cart_btn_x - 5, cart_btn_y - 5))
            
            screen.blit(cart_surf, (cart_btn_x, cart_btn_y))
            
            # 购物车数量徽章
            cart_count = cart.get_total_count()
            if cart_count > 0:
                badge_size = min(24, cart_btn_size * 0.4)
                badge_x = cart_btn_x + cart_btn_size - badge_size - 5
                badge_y = cart_btn_y + 5
                
                badge_surf = pygame.Surface((badge_size, badge_size), pygame.SRCALPHA)
                pygame.draw.circle(badge_surf, COLORS["accent_red"], (badge_size // 2, badge_size // 2), badge_size // 2)
                
                count_text = font_small.render(str(cart_count) if cart_count < 100 else "99", True, COLORS["text_white"])
                count_rect = count_text.get_rect(center=(badge_size // 2, badge_size // 2))
                badge_surf.blit(count_text, count_rect)
                
                screen.blit(badge_surf, (badge_x, badge_y))

            # 购物车弹窗
            if show_cart:
                overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay_surf.fill((0, 0, 0, 180))
                screen.blit(overlay_surf, (0, 0))
                
                cart_width = min(400, SCREEN_WIDTH * 0.85)
                cart_height = min(500, SCREEN_HEIGHT * 0.7)
                cart_x = (SCREEN_WIDTH - cart_width) // 2
                cart_y = (SCREEN_HEIGHT - cart_height) // 2
                
                cart_bg = pygame.Surface((cart_width, cart_height), pygame.SRCALPHA)
                pygame.draw.rect(cart_bg, (35, 40, 60, 240), (0, 0, cart_width, cart_height), border_radius=15)
                pygame.draw.rect(screen, COLORS["accent_gold"], (cart_x, cart_y, cart_width, cart_height), 2, border_radius=15)
                screen.blit(cart_bg, (cart_x, cart_y))
                
                cart_title = font_normal.render("购物车", True, COLORS["accent_gold"])
                cart_title_rect = cart_title.get_rect(center=(cart_x + cart_width // 2, cart_y + 30 * scale))
                screen.blit(cart_title, cart_title_rect)
                
                # 关闭按钮
                close_btn_x = cart_x + cart_width - 40
                close_btn_y = cart_y + 15
                close_btn_rect = pygame.Rect(close_btn_x, close_btn_y, 25, 25)
                
                close_surf = pygame.Surface((25, 25), pygame.SRCALPHA)
                pygame.draw.circle(close_surf, COLORS["accent_red"], (12, 12), 12)
                pygame.draw.circle(close_surf, COLORS["text_white"], (12, 12), 10)
                close_text = font_small.render("×", True, COLORS["accent_red"])
                close_text_rect = close_text.get_rect(center=(12, 12))
                close_surf.blit(close_text, close_text_rect)
                
                if close_btn_rect.collidepoint(mx, my):
                    pygame.draw.circle(screen, COLORS["text_white"], (close_btn_x + 12, close_btn_y + 12), 14)
                screen.blit(close_surf, (close_btn_x, close_btn_y))
                
                # 购物车内容区域
                content_area_y = cart_y + 60
                content_area_height = cart_height - 140
                
                if cart.is_empty():
                    empty_text = font_normal.render("购物车是空的", True, COLORS["text_gray"])
                    empty_rect = empty_text.get_rect(center=(cart_x + cart_width // 2, cart_y + cart_height // 2))
                    screen.blit(empty_text, empty_rect)
                else:
                    total_items_height = len(cart.items) * 50 * scale
                    cart_scroll_y = max(0, min(total_items_height - content_area_height, cart_scroll_y))
                    
                    for i, item in enumerate(cart.items):
                        item_y = content_area_y + i * 50 * scale - cart_scroll_y
                        
                        if item_y + 45 * scale > content_area_y and item_y < content_area_y + content_area_height:
                            item_bg = pygame.Surface((cart_width - 30, 45 * scale), pygame.SRCALPHA)
                            pygame.draw.rect(item_bg, (45, 50, 75, 200), (0, 0, cart_width - 30, 45 * scale), border_radius=8)
                            screen.blit(item_bg, (cart_x + 15, item_y))
                            
                            # 商品名称
                            item_name = font_small.render(item['name'], True, COLORS["text_white"])
                            screen.blit(item_name, (cart_x + 25, item_y + 12 * scale))
                            
                            # 数量控制
                            minus_btn_x = cart_x + cart_width - 140
                            minus_btn_y = item_y + 7 * scale
                            minus_btn_rect = pygame.Rect(minus_btn_x, minus_btn_y, 30 * scale, 30 * scale)
                            
                            pygame.draw.rect(screen, (80, 80, 100), minus_btn_rect, border_radius=5)
                            minus_text = font_small.render("-", True, COLORS["text_white"])
                            minus_text_rect = minus_text.get_rect(center=minus_btn_rect.center)
                            screen.blit(minus_text, minus_text_rect)
                            
                            # 数量显示
                            qty_text = font_small.render(str(item['amount']), True, COLORS["accent_gold"])
                            qty_rect = qty_text.get_rect(center=(cart_x + cart_width - 105, item_y + 22 * scale))
                            screen.blit(qty_text, qty_rect)
                            
                            plus_btn_x = cart_x + cart_width - 85
                            plus_btn_y = item_y + 7 * scale
                            plus_btn_rect = pygame.Rect(plus_btn_x, plus_btn_y, 30 * scale, 30 * scale)
                            
                            pygame.draw.rect(screen, COLORS["btn_green"], plus_btn_rect, border_radius=5)
                            plus_text = font_small.render("+", True, COLORS["text_white"])
                            plus_text_rect = plus_text.get_rect(center=plus_btn_rect.center)
                            screen.blit(plus_text, plus_text_rect)
                            
                            # 删除按钮
                            del_btn_x = cart_x + cart_width - 45
                            del_btn_y = item_y + 7 * scale
                            del_btn_rect = pygame.Rect(del_btn_x, del_btn_y, 30 * scale, 30 * scale)
                            
                            pygame.draw.rect(screen, COLORS["accent_red"], del_btn_rect, border_radius=5)
                            del_text = font_small.render("×", True, COLORS["text_white"])
                            del_text_rect = del_text.get_rect(center=del_btn_rect.center)
                            screen.blit(del_text, del_text_rect)
                
                # 结算按钮和清空按钮
                clear_btn = AnimatedButton(
                    cart_x + 20, cart_y + cart_height - 55,
                    (cart_width - 50) // 2, 40,
                    "清空", font_small, COLORS["accent_red"], (255, 100, 100), (255, 255, 255), 1.0
                )
                clear_btn.update((mx, my))
                clear_btn.draw(screen)
                
                checkout_btn = AnimatedButton(
                    cart_x + (cart_width - 50) // 2 + 30, cart_y + cart_height - 55,
                    (cart_width - 50) // 2, 40,
                    "结算", font_small, COLORS["btn_green"], COLORS["btn_green_hover"], (255, 255, 255), 1.0
                )
                checkout_btn.update((mx, my))
                checkout_btn.draw(screen)

            # 扫码支付弹窗
            if show_qr_payment:
                overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay_surf.fill((0, 0, 0, 180))
                screen.blit(overlay_surf, (0, 0))
                
                # 弹窗主界面
                popup_width = min(600, SCREEN_WIDTH * 0.9)
                popup_height = min(500, SCREEN_HEIGHT * 0.8)
                popup_x = (SCREEN_WIDTH - popup_width) // 2
                popup_y = (SCREEN_HEIGHT - popup_height) // 2
                
                popup_bg = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
                pygame.draw.rect(popup_bg, (35, 40, 60, 240), (0, 0, popup_width, popup_height), border_radius=15)
                pygame.draw.rect(screen, COLORS["accent_gold"], (popup_x, popup_y, popup_width, popup_height), 2, border_radius=15)
                screen.blit(popup_bg, (popup_x, popup_y))
                
                # 标题
                title_text = font_title.render("扫码结算", True, COLORS["accent_gold"])
                title_rect = title_text.get_rect(center=(popup_x + popup_width // 2, popup_y + 35))
                screen.blit(title_text, title_rect)
                
                # 生成真实二维码
                qr_content = f"校验码:{qr_verify_code}"
                qr_img = qrcode.make(qr_content, box_size=4)
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer)
                qr_buffer.seek(0)
                qr_surface = pygame.image.load(qr_buffer)
                
                # 二维码显示区域
                qr_size = min(180, popup_width * 0.4)
                qr_scaled = pygame.transform.scale(qr_surface, (qr_size, qr_size))
                qr_x = popup_x + (popup_width - qr_size) // 2
                qr_y = popup_y + 70
                screen.blit(qr_scaled, (qr_x, qr_y))
                
                # 扫码提示
                scan_tip = font_small.render("请使用微信/支付宝扫码", True, COLORS["text_white"])
                scan_tip_rect = scan_tip.get_rect(center=(popup_x + popup_width // 2, qr_y + qr_size + 25))
                screen.blit(scan_tip, scan_tip_rect)
                
                # 手机预览提示
                phone_hint = font_small.render("扫码后手机显示：校验码:" + qr_verify_code, True, COLORS["accent_green"])
                phone_hint_rect = phone_hint.get_rect(center=(popup_x + popup_width // 2, qr_y + qr_size + 55))
                screen.blit(phone_hint, phone_hint_rect)
                
                # 输入框
                input_bg = pygame.Surface((popup_width - 80, 50), pygame.SRCALPHA)
                pygame.draw.rect(input_bg, COLORS["bg_light"], (0, 0, popup_width - 80, 50), border_radius=10)
                pygame.draw.rect(screen, COLORS["accent_gold"], (popup_x + 40, qr_y + qr_size + 80, popup_width - 80, 50), 2, border_radius=10)
                screen.blit(input_bg, (popup_x + 40, qr_y + qr_size + 80))
                
                input_text = font_title.render(qr_input_text, True, COLORS["text_white"])
                input_rect = input_text.get_rect(center=(popup_x + popup_width // 2, qr_y + qr_size + 105))
                screen.blit(input_text, input_rect)
                
                # 数字键盘
                keypad_y = qr_y + qr_size + 150
                keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', '←']
                key_width = (popup_width - 80) // 3
                key_height = 45
                
                for i, key in enumerate(keys):
                    key_x = popup_x + 40 + (i % 3) * key_width
                    key_y = keypad_y + (i // 3) * (key_height + 5)
                    
                    if key == "":
                        continue
                    
                    key_rect = pygame.Rect(key_x, key_y, key_width - 3, key_height)
                    
                    key_color = COLORS["btn_blue"] if key != "←" else COLORS["accent_red"]
                    key_surf = pygame.Surface((key_width - 3, key_height), pygame.SRCALPHA)
                    pygame.draw.rect(key_surf, key_color, (0, 0, key_width - 3, key_height), border_radius=8)
                    screen.blit(key_surf, (key_x, key_y))
                    
                    key_text = font_normal.render(key, True, COLORS["text_white"])
                    key_text_rect = key_text.get_rect(center=key_rect.center)
                    screen.blit(key_text, key_text_rect)
                
                # 确认按钮
                confirm_btn = AnimatedButton(
                    popup_x + 40, keypad_y + 4 * (key_height + 5) + 10,
                    popup_width - 80, 45,
                    "确认支付", font_normal, COLORS["btn_green"], COLORS["btn_green_hover"], (255, 255, 255), 1.0
                )
                confirm_btn.update((mx, my))
                confirm_btn.draw(screen)
                
                # 关闭按钮
                qr_close_btn_x = popup_x + popup_width - 45
                qr_close_btn_y = popup_y + 15
                qr_close_btn_rect = pygame.Rect(qr_close_btn_x, qr_close_btn_y, 30, 30)
                
                qr_close_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(qr_close_surf, COLORS["accent_red"], (15, 15), 15)
                pygame.draw.circle(qr_close_surf, COLORS["text_white"], (15, 15), 12)
                qr_close_text = font_normal.render("×", True, COLORS["accent_red"])
                qr_close_text_rect = qr_close_text.get_rect(center=(15, 15))
                qr_close_surf.blit(qr_close_text, qr_close_text_rect)
                screen.blit(qr_close_surf, (qr_close_btn_x, qr_close_btn_y))
                
                # 成功提示
                if qr_payment_success:
                    success_bg = pygame.Surface((popup_width - 40, 60), pygame.SRCALPHA)
                    pygame.draw.rect(success_bg, (50, 150, 80, 200), (0, 0, popup_width - 40, 60), border_radius=10)
                    screen.blit(success_bg, (popup_x + 20, popup_y + 25))
                    
                    success_text = font_normal.render("支付成功！已发放购物车商品！", True, COLORS["text_white"])
                    success_rect = success_text.get_rect(center=(popup_x + popup_width // 2, popup_y + 55))
                    screen.blit(success_text, success_rect)

            # 更新和绘制特效
            for p in particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    particles.remove(p)

            for ft in floating_texts[:]:
                ft.update()
                ft.draw(screen)
                if ft.life <= 0:
                    floating_texts.remove(ft)

            # 获取所有事件
            events = pygame.event.get()
            
            # 处理滚动容器事件，检查是否点击了滚动条
            clicked_scrollbar = False
            for event in events:
                if scroll_container.handle_event(event, (mx, my)):
                    clicked_scrollbar = True

            # 事件处理
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 只处理鼠标左键点击事件，不处理滚轮事件
                    if event.button != 1:
                        continue
                    # 如果点击了滚动条，跳过按钮点击处理
                    if clicked_scrollbar:
                        continue
                        
                    # 资源购买
                    for btn, res_name, amount, *is_cart in resource_btns:
                        if btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            if is_cart and is_cart[0] == "cart":
                                cart.add_item("resource", res_name, amount)
                                floating_texts.append(FloatingText(
                                    f"已加入购物车", mx, my, COLORS["accent_gold"], font_normal
                                ))
                                for _ in range(10):
                                    particle_color = random.choice([COLORS["accent_gold"], (255, 200, 100)])
                                    particles.append(Particle(mx, my, particle_color, random.uniform(2, 4), random.uniform(2, 4), random.randint(20, 30)))
                            else:
                                if buy_resource(res_name, amount):
                                    play_sound(success_sound)
                                    floating_texts.append(FloatingText(
                                        f"+{amount} {res_name}", mx, my, COLORS["accent_green"], font_normal
                                    ))
                                    for _ in range(20):
                                        particle_color = random.choice([COLORS["accent_green"], (100, 255, 100), (50, 200, 50)])
                                        particles.append(Particle(mx, my, particle_color, random.uniform(3, 6), random.uniform(3, 7), random.randint(30, 40)))
                    # 武将碎片
                    for btn, hero_name, fragments, *is_cart in hero_btns:
                        if btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            if is_cart and is_cart[0] == "cart":
                                cart.add_item("hero", hero_name, fragments)
                                floating_texts.append(FloatingText(
                                    f"已加入购物车", mx, my, COLORS["accent_gold"], font_normal
                                ))
                                for _ in range(10):
                                    particle_color = random.choice([COLORS["accent_gold"], (255, 200, 100)])
                                    particles.append(Particle(mx, my, particle_color, random.uniform(2, 4), random.uniform(2, 4), random.randint(20, 30)))
                            else:
                                if buy_hero_fragments(hero_name, fragments):
                                    play_sound(success_sound)
                                    floating_texts.append(FloatingText(
                                        f"+{fragments} {hero_name}碎片", mx, my, COLORS["accent_blue"], font_normal
                                    ))
                                    for _ in range(20):
                                        particle_color = random.choice([COLORS["accent_blue"], (100, 150, 255), (50, 100, 200)])
                                        particles.append(Particle(mx, my, particle_color, random.uniform(3, 6), random.uniform(3, 7), random.randint(30, 40)))
                    # 装备购买
                    for btn, equip_name, equip_type, *is_cart in equip_btns:
                        if btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            if is_cart and is_cart[0] == "cart":
                                cart.add_item("equip", equip_name, 1, {"type": equip_type})
                                floating_texts.append(FloatingText(
                                    f"已加入购物车", mx, my, COLORS["accent_gold"], font_normal
                                ))
                                for _ in range(10):
                                    particle_color = random.choice([COLORS["accent_gold"], (255, 200, 100)])
                                    particles.append(Particle(mx, my, particle_color, random.uniform(2, 4), random.uniform(2, 4), random.randint(20, 30)))
                            else:
                                if buy_equip(equip_name, equip_type):
                                    play_sound(success_sound)
                                    floating_texts.append(FloatingText(
                                        f"获得 {equip_name}", mx, my, COLORS["accent_gold"], font_normal
                                    ))
                                    for _ in range(20):
                                        particle_color = random.choice([COLORS["accent_gold"], (255, 200, 100), (200, 160, 50)])
                                        particles.append(Particle(mx, my, particle_color, random.uniform(3, 6), random.uniform(3, 7), random.randint(30, 40)))
                    # 时间卡等级选择
                    card_levels = ["时间卡", "时间卡+", "时间卡++"]
                    for i, level in enumerate(card_levels):
                        level_rect = pygame.Rect(container_x + 10 + i * 100, craft_start_y, 90, 35)
                        if level_rect.collidepoint(mx, my):
                            selected_level = i
                            play_sound(click_sound)
                            break
                    
                    # 合成时间卡
                    if craft_btn and craft_btn.rect.collidepoint(mx, my):
                        play_sound(click_sound)
                        selected_card = card_levels[selected_level]
                        success, message = craft_time_card(selected_card)
                        if success:
                            play_sound(success_sound)
                            floating_texts.append(FloatingText(
                                message, mx, my, COLORS["accent_green"], font_normal
                            ))
                            for _ in range(25):
                                # 生成多种颜色的粒子
                                particle_color = random.choice([COLORS["accent_green"], (100, 255, 100), (50, 200, 50), (150, 255, 150)])
                                particles.append(Particle(mx, my, particle_color, random.uniform(4, 7), random.uniform(4, 8), random.randint(35, 45)))
                        else:
                            floating_texts.append(FloatingText(
                                message, mx, my, (255, 100, 100), font_normal
                            ))
                    # 抽卡
                    if draw_card_btn and draw_card_btn.rect.collidepoint(mx, my):
                        play_sound(click_sound)
                        hero, fragments = random_draw_hero()
                        play_sound(success_sound)
                        floating_texts.append(FloatingText(
                            f"恭喜 {hero} +{fragments}碎片!", 
                            draw_card_x + draw_card_width // 2, draw_card_y - 30, 
                            COLORS["accent_purple"], font_normal
                        ))
                        for _ in range(40):
                            # 生成多种颜色的粒子
                            particle_color = random.choice([COLORS["accent_gold"], COLORS["accent_purple"], (255, 150, 255), (200, 100, 200)])
                            particles.append(Particle(
                                draw_card_x + draw_card_width // 2, draw_card_y + draw_card_height // 2,
                                particle_color,
                                random.uniform(5, 8), random.uniform(5, 12), random.randint(45, 55)
                            ))
                    # 返回
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
                    
                    # 购物车图标点击
                    if cart_icon_rect.collidepoint(mx, my):
                        play_sound(click_sound)
                        show_cart = not show_cart
                        cart_scroll_y = 0
                    
                    # 购物车弹窗事件
                    if show_cart:
                        # 关闭按钮
                        if close_btn_rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            show_cart = False
                        
                        # 清空购物车
                        if clear_btn and clear_btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            cart.clear()
                            floating_texts.append(FloatingText(
                                "购物车已清空", cart_x + cart_width // 2, cart_y + cart_height // 2, 
                                COLORS["accent_red"], font_normal
                            ))
                        
                        # 结算按钮
                        if checkout_btn and checkout_btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            if not cart.is_empty():
                                qr_verify_code = str(random.randint(100000, 999999))
                                qr_input_text = ""
                                qr_payment_success = False
                                show_cart = False
                                show_qr_payment = True
                        
                        # 购物车商品数量修改
                        if not cart.is_empty():
                            for i, item in enumerate(cart.items):
                                item_y = content_area_y + i * 50 * scale - cart_scroll_y
                                
                                if item_y + 45 * scale > content_area_y and item_y < content_area_y + content_area_height:
                                    minus_btn_x = cart_x + cart_width - 140
                                    minus_btn_y = item_y + 7 * scale
                                    minus_btn_rect = pygame.Rect(minus_btn_x, minus_btn_y, 30 * scale, 30 * scale)
                                    
                                    plus_btn_x = cart_x + cart_width - 85
                                    plus_btn_y = item_y + 7 * scale
                                    plus_btn_rect = pygame.Rect(plus_btn_x, plus_btn_y, 30 * scale, 30 * scale)
                                    
                                    del_btn_x = cart_x + cart_width - 45
                                    del_btn_y = item_y + 7 * scale
                                    del_btn_rect = pygame.Rect(del_btn_x, del_btn_y, 30 * scale, 30 * scale)
                                    
                                    if minus_btn_rect.collidepoint(mx, my):
                                        play_sound(click_sound)
                                        cart.update_amount(i, item['amount'] - 1)
                                    elif plus_btn_rect.collidepoint(mx, my):
                                        play_sound(click_sound)
                                        cart.update_amount(i, item['amount'] + 1)
                                    elif del_btn_rect.collidepoint(mx, my):
                                        play_sound(click_sound)
                                        cart.remove_item(i)
                    
                    # 二维码点击事件
                    if qr_rect and qr_rect.collidepoint(mx, my):
                        play_sound(click_sound)
                        qr_verify_code = str(random.randint(100000, 999999))
                        qr_input_text = ""
                        qr_payment_success = False
                        show_qr_payment = True
                    
                    # 扫码支付弹窗事件
                    if show_qr_payment:
                        # 关闭按钮
                        if qr_close_btn_rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            show_qr_payment = False
                            qr_verify_code = ""
                            qr_input_text = ""
                            qr_payment_success = False
                        
                        # 数字键盘点击
                        keypad_y = qr_y + qr_size + 150
                        keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', '←']
                        key_width = (popup_width - 80) // 3
                        key_height = 45
                        
                        for i, key in enumerate(keys):
                            key_x = popup_x + 40 + (i % 3) * key_width
                            key_y = keypad_y + (i // 3) * (key_height + 5)
                            
                            if key == "":
                                continue
                            
                            key_rect = pygame.Rect(key_x, key_y, key_width - 3, key_height)
                            if key_rect.collidepoint(mx, my):
                                play_sound(click_sound)
                                if key == "←":
                                    qr_input_text = qr_input_text[:-1]
                                elif len(qr_input_text) < 6:
                                    qr_input_text += key
                        
                        # 确认按钮
                        if confirm_btn and confirm_btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            if qr_input_text == qr_verify_code:
                                qr_payment_success = True
                                play_sound(success_sound)
                                
                                success_count = 0
                                for item in cart.items[:]:
                                    item_type = item['item_type']
                                    name = item['name']
                                    amount = item['amount']
                                    
                                    if item_type == "resource":
                                        buy_resource(name, amount)
                                        success_count += 1
                                    elif item_type == "hero":
                                        buy_hero_fragments(name, amount)
                                        success_count += 1
                                    elif item_type == "equip":
                                        equip_type = item['extra_data'].get('type', 'weapon') if item['extra_data'] else 'weapon'
                                        buy_equip(name, equip_type)
                                        success_count += 1
                                
                                cart.clear()
                                
                                floating_texts.append(FloatingText(
                                    f"支付成功！共{success_count}件商品已发放！", 
                                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 
                                    COLORS["accent_green"], font_normal
                                ))
                                for _ in range(40):
                                    particle_color = random.choice([COLORS["accent_green"], (100, 255, 100), (50, 200, 50), COLORS["accent_gold"]])
                                    particles.append(Particle(
                                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                        particle_color, random.uniform(5, 10), random.uniform(5, 10), random.randint(40, 60)
                                    ))
                            
                            else:
                                floating_texts.append(FloatingText(
                                    "校验码错误！", 
                                    popup_x + popup_width // 2, popup_y + popup_height - 50, 
                                    COLORS["accent_red"], font_normal
                                ))

            pygame.display.flip()
            clock.tick(60)

        safe_exit("商城模块")
    except Exception as e:
        print(f"异常：{str(e)}")
        print("详细错误信息：")
        traceback.print_exc()
        safe_exit("商城模块", str(e))

if __name__ == "__main__":
    main()
