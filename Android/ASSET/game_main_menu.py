import os
import sys
import subprocess
import platform
import pygame
import math
import random
import logging
from ASSET.fun_effects import PetSprite, FloatingParticles
from ASSET.game_data import data, save, get_system_font_name
from ASSET import safe_exit
from ASSET.login_system import save_game
from ASSET.equipment_system import main as equipment_system_main  # pyright: ignore[reportUnusedImport]

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("game.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局变量（延迟初始化）
screen = None
clock = None
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None

class MouseTrail:
    """鼠标跟随效果"""
    def __init__(self, max_trails=20):
        self.trails = []
        self.max_trails = max_trails
        self.colors = [
            (255, 215, 0), (200, 100, 50), (70, 180, 130),
            (180, 100, 220), (100, 200, 255), (255, 150, 100)
        ]
        self.color_index = 0
        
    def add_trail(self, x, y):
        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1
        self.trails.append({
            'x': x,
            'y': y,
            'size': random.randint(8, 15),
            'alpha': 200,
            'color': color
        })
        if len(self.trails) > self.max_trails:
            self.trails.pop(0)
    
    def update(self):
        for trail in self.trails[:]:
            trail['size'] *= 0.95
            trail['alpha'] *= 0.9
            if trail['alpha'] < 5 or trail['size'] < 1:
                self.trails.remove(trail)
    
    def draw(self, surface):
        for trail in self.trails:
            try:
                if trail['size'] > 1 and trail['alpha'] > 0:
                    size = int(trail['size'])
                    if size > 0:
                        trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                        alpha = int(max(0, min(255, trail['alpha'])))
                        pygame.draw.circle(trail_surf, (*trail['color'], alpha), (size, size), size)
                        surface.blit(trail_surf, (int(trail['x'] - size), int(trail['y'] - size)))
            except Exception:
                pass

class DynamicLight:
    """动态光效类"""
    def __init__(self, x, y, radius=100, color=(255, 215, 0)):
        self.x = x
        self.y = y
        self.radius = radius
        self.base_radius = radius
        self.color = color
        self.pulse = 0
        self.direction = 1
        self.offset_x = 0
        self.offset_y = 0
        
    def update(self):
        self.pulse += 0.03 * self.direction
        if abs(self.pulse) > 1:
            self.direction *= -1
        self.radius = self.base_radius * (0.8 + 0.2 * self.pulse)
        self.offset_x = math.sin(pygame.time.get_ticks() * 0.002) * 5
        self.offset_y = math.cos(pygame.time.get_ticks() * 0.002) * 5
        
    def draw(self, surface):
        try:
            light_surf = pygame.Surface((int(self.radius * 2 + 20), int(self.radius * 2 + 20)), pygame.SRCALPHA)
            center = int(self.radius + 10)
            for r in range(int(self.radius), 0, -2):
                alpha = int(30 * (1 - r / self.radius))
                pygame.draw.circle(light_surf, (*self.color, alpha), (center, center), r)
            surface.blit(light_surf, (int(self.x - self.radius - 10 + self.offset_x), 
                                     int(self.y - self.radius - 10 + self.offset_y)))
        except Exception:
            pass

class ScrollableContainer:
    """通用滚动容器类"""
    def __init__(self, x, y, width, height, item_height, items, render_func):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.item_height = item_height
        self.items = items
        self.render_func = render_func
        self.scroll_offset = 0
        self.max_scroll = max(0, len(items) * item_height - height)
        self.is_scrolling = False
        self.last_mouse_y = 0
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - self.item_height // 2)
                return True
            elif event.button == 5:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.item_height // 2)
                return True
            elif event.button == 1:
                if self.is_mouse_in_container(event.pos):
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
    
    def is_mouse_in_container(self, mouse_pos):
        return (self.x <= mouse_pos[0] <= self.x + self.width and
                self.y <= mouse_pos[1] <= self.y + self.height)
    
    def draw(self, surface):
        container_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        clip_rect = pygame.Rect(0, 0, self.width, self.height)
        container_surface.set_clip(clip_rect)
        
        for i, item in enumerate(self.items):
            item_y = self.y + i * self.item_height - self.scroll_offset
            if -self.item_height <= item_y <= self.height:
                self.render_func(container_surface, item, self.x, item_y)
        
        container_surface.set_clip(None)
        surface.blit(container_surface, (self.x, self.y))
        
        if self.max_scroll > 0:
            scrollbar_height = max(30, self.height * self.height / (len(self.items) * self.item_height))
            scrollbar_y_ratio = self.scroll_offset / self.max_scroll if self.max_scroll > 0 else 0
            scrollbar_y = self.y + (self.height - scrollbar_height) * scrollbar_y_ratio
            
            pygame.draw.rect(surface, (80, 80, 100), 
                           (self.x + self.width - 12, self.y + 5, 8, self.height - 10), 
                           border_radius=4)
            pygame.draw.rect(surface, (150, 130, 80), 
                           (self.x + self.width - 12, scrollbar_y, 8, scrollbar_height), 
                           border_radius=4)

class AnimatedSprite:
    """动画精灵类 - 用于创建流畅的动画效果"""
    def __init__(self, x, y, frames, frame_duration=100):
        self.x = x
        self.y = y
        self.frames = frames
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.last_update = pygame.time.get_ticks()
        self.active = True
        self.redundant_frame = None
        
    def update(self):
        if not self.active:
            return
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update > self.frame_duration:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_update = current_time
            if self.redundant_frame is None and len(self.frames) > 1:
                self.redundant_frame = self.frames[0]
    
    def draw(self, surface):
        if not self.active:
            return
        try:
            if self.current_frame < len(self.frames):
                surface.blit(self.frames[self.current_frame], (self.x, self.y))
            elif self.redundant_frame:
                surface.blit(self.redundant_frame, (self.x, self.y))
        except Exception:
            if self.redundant_frame:
                try:
                    surface.blit(self.redundant_frame, (self.x, self.y))
                except Exception:
                    pass

class FloatingText:
    """浮动文字效果"""
    def __init__(self, text, x, y, color=(255, 215, 0), font=None, speed=-1):
        self.text = text
        self.x = x
        self.y = y
        self.original_y = y
        self.color = color
        self.font = font or FONT_SMALL
        self.speed = speed
        self.alpha = 255
        self.active = True
        self.life = 180
        self.redundant_text = None
        
    def update(self):
        if not self.active:
            return
        self.y += self.speed
        self.life -= 1
        if self.life < 60:
            self.alpha = max(0, int(255 * (self.life / 60)))
        if self.life <= 0 or self.y < -50:
            self.active = False
    
    def draw(self, surface):
        if not self.active or self.alpha <= 0:
            return
        try:
            if self.redundant_text is None:
                self.redundant_text = self.font.render(self.text, True, self.color)
            text_surf = self.font.render(self.text, True, self.color)
            text_surf.set_alpha(self.alpha)
            surface.blit(text_surf, (self.x, self.y))
        except Exception:
            if self.redundant_text:
                try:
                    self.redundant_text.set_alpha(self.alpha)
                    surface.blit(self.redundant_text, (self.x, self.y))
                except Exception:
                    pass

class GlowingEffect:
    """发光效果类"""
    def __init__(self, surface, x, y, width, height, color=(255, 215, 0), intensity=1.0):
        self.surface = surface
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.intensity = intensity
        self.pulse = 0
        self.direction = 1
        self.redundant_surface = None
        
    def update(self):
        self.pulse += 0.05 * self.direction
        if abs(self.pulse) > 1:
            self.direction *= -1
        if self.pulse < 0:
            self.pulse = 0
            self.direction = 1
            
    def draw(self):
        try:
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            alpha = int(50 * self.intensity * (0.5 + self.pulse * 0.5))
            pygame.draw.rect(glow_surf, (*self.color, alpha), 
                           (10, 10, self.width, self.height), border_radius=10)
            self.surface.blit(glow_surf, (self.x - 10, self.y - 10))
        except Exception:
            if self.redundant_surface:
                try:
                    self.surface.blit(self.redundant_surface, (self.x - 10, self.y - 10))
                except Exception:
                    pass

class ParticleSystem:
    """粒子系统 - 更稳定和有趣的粒子效果"""
    def __init__(self, max_particles=50):
        self.particles = []
        self.max_particles = max_particles
        self.types = ['gold', 'fire', 'water', 'nature', 'magic']
        self.redundant_storage = []
        
    def add_particle(self, particle_type, x, y, **kwargs):
        if len(self.particles) >= self.max_particles:
            if self.redundant_storage:
                old_particle = self.redundant_storage.pop(0)
                self.particles.append(old_particle)
                old_particle.reset(x, y, **kwargs)
            return
        
        colors = {
            'gold': (255, 215, 0),
            'fire': (255, 100, 50),
            'water': (70, 130, 180),
            'nature': (80, 180, 80),
            'magic': (180, 100, 220)
        }
        
        particle = Particle(
            x, y,
            colors.get(particle_type, (255, 215, 0)),
            kwargs.get('speed', random.uniform(1.0, 3.0)),
            kwargs.get('size', random.randint(2, 4)),
            kwargs.get('life', random.randint(100, 200))
        )
        self.particles.append(particle)
        
    def update(self):
        for p in self.particles[:]:
            try:
                p.update()
                p.x += math.sin(p.y * 0.02) * 0.5
                if p.life <= 0:
                    self.redundant_storage.append(p)
                    if p in self.particles:
                        self.particles.remove(p)
            except Exception:
                if p in self.particles:
                    self.particles.remove(p)
                    
    def draw(self, surface):
        for p in self.particles[:]:
            try:
                p.draw(surface)
            except Exception:
                if p in self.particles:
                    self.particles.remove(p)

class SafeSurface:
    """安全表面类 - 防止绘制错误"""
    def __init__(self, size, flags=0):
        self.size = size
        self.flags = flags
        self.surface = None
        self.fallback_surface = None
        self.init_surface()
        
    def init_surface(self):
        try:
            self.surface = pygame.Surface(self.size, self.flags)
            self.surface.fill((0, 0, 0, 0))
        except Exception:
            self.surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            
    def blit(self, source, dest, area=None, special_flags=0):
        try:
            return self.surface.blit(source, dest, area, special_flags)
        except Exception:
            if self.fallback_surface:
                try:
                    return self.fallback_surface.blit(source, dest, area, special_flags)
                except Exception:
                    return None
    
    def draw_rect(self, color, rect, width=0, border_radius=0):
        try:
            pygame.draw.rect(self.surface, color, rect, width, border_radius)
        except Exception:
            pass
            
    def draw_circle(self, color, center, radius, width=0):
        try:
            pygame.draw.circle(self.surface, color, center, radius, width)
        except Exception:
            pass

# 平台检测
def is_android():
    """检测是否为安卓平台"""
    return 'ANDROID_DATA' in os.environ

def is_ios():
    """检测是否为iOS平台"""
    return 'IOS_DATA' in os.environ

def get_platform():
    """获取当前平台"""
    if is_android():
        return 'android'
    elif is_ios():
        return 'ios'
    elif platform.system() == 'Darwin':
        return 'macos'
    elif platform.system() == 'Windows':
        return 'windows'
    elif platform.system() == 'Linux':
        return 'linux'
    return 'unknown'

def is_mobile():
    """检测是否为移动平台"""
    return is_android() or is_ios()

def get_screen_size():
    """获取屏幕尺寸"""
    try:
        if is_mobile():
            info = pygame.display.Info()
            return info.current_w, info.current_h
        else:
            return pygame.display.get_surface().get_size()
    except Exception:
        return 800, 600

def get_font_list():
    """获取适合当前平台的中文字体列表"""
    current_platform = get_platform()

    if current_platform == 'windows':
        return [
            "Microsoft YaHei",
            "Microsoft YaHei UI",
            "SimHei",
            "SimSun",
            "KaiTi",
            "FangSong",
            "Segoe UI",
            "Arial",
            "Tahoma",
            None
        ]
    elif current_platform == 'macos':
        return [
            "PingFang SC",
            "Hiragino Sans GB",
            "STHeiti",
            "WenQuanYi Micro Hei",
            "Arial",
            "Helvetica",
            None
        ]
    elif current_platform == 'linux':
        return [
            "Noto Sans CJK SC",
            "Noto Sans CJK",
            "WenQuanYi Micro Hei",
            "WenQuanYi Zen Hei",
            "DroidSansFallback",
            "AR PL UMing CN",
            "AR PL UKai CN",
            "Sans",
            None
        ]
    elif current_platform in ('android', 'ios'):
        return [
            "DroidSansFallback",
            "Roboto",
            "Noto Sans",
            "Helvetica",
            None
        ]
    else:
        return [
            "Arial",
            "Helvetica",
            "Sans-serif",
            None
        ]

def test_font_renderable(font, text="测试"):
    """测试字体是否可以正常渲染"""
    try:
        if font is None:
            return False
        surface = font.render(text, True, (255, 255, 255))
        return surface is not None and surface.get_width() > 0
    except Exception:
        return False

def init_fonts():
    """初始化字体 - 增强兼容性版本"""
    global FONT_MAIN, FONT_SMALL, FONT_BIG

    current_platform = get_platform()
    if is_mobile():
        base_size = 48
        small_size = 32
        big_size = 72
    else:
        base_size = 40
        small_size = 28
        big_size = 60

    system_font = get_system_font_name()
    if system_font:
        font_list = [system_font] + get_font_list()
    else:
        font_list = get_font_list()

    logger.info(f"当前平台: {current_platform}")
    logger.info(f"尝试加载字体列表: {font_list}")

    for font_name in font_list:
        try:
            if font_name is None:
                FONT_MAIN = pygame.font.Font(None, base_size)
                FONT_SMALL = pygame.font.Font(None, small_size)
                FONT_BIG = pygame.font.Font(None, big_size)
            else:
                FONT_MAIN = pygame.font.SysFont(font_name, base_size)
                FONT_SMALL = pygame.font.SysFont(font_name, small_size)
                FONT_BIG = pygame.font.SysFont(font_name, big_size)

            test_text = "测试中文ABC123"
            if test_font_renderable(FONT_MAIN, test_text):
                logger.info(f"成功使用字体: {font_name if font_name else '默认字体'}")

                if not test_font_renderable(FONT_MAIN, "中文"):
                    logger.warning(f"字体 {font_name} 不支持中文，尝试备选方案")
                    continue

                return
        except Exception as e:
            logger.error(f"字体 {font_name} 加载失败: {e}")
            continue

    logger.warning("使用 Pygame 默认字体")
    FONT_MAIN = pygame.font.Font(None, base_size)
    FONT_SMALL = pygame.font.Font(None, small_size)
    FONT_BIG = pygame.font.Font(None, big_size)

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

class Button:
    def __init__(self, text, x, y, width, height, font,
                 normal_color=None,
                 hover_color=None,
                 text_color=None,
                 icon=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color if normal_color is not None else COLORS["accent_blue"]
        self.hover_color = hover_color if hover_color is not None else COLORS["accent_blue_light"]
        self.text_color = text_color if text_color is not None else COLORS["text_white"]
        self.is_hovered = False
        self.is_clicked = False
        self.click_timer = 0
        self.icon = icon
        self.particles = []
        self.glow_alpha = 0
        self.scale = 1.0
        self.target_scale = 1.0
        self.text_offset = 0
        self.click_particles = []

    def check_hover(self, mouse_pos):
        """检查鼠标悬停"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def check_click(self, mouse_pos):
        """检查点击"""
        if self.is_hovered and pygame.mouse.get_pressed()[0]:
            if not self.is_clicked:
                self.is_clicked = True
                self.click_timer = pygame.time.get_ticks()
                return True
        elif self.is_clicked:
            if pygame.time.get_ticks() - self.click_timer > 200:
                self.is_clicked = False
        return False

    def draw(self, surface):
        """绘制按钮"""
        if self.is_hovered:
            self.target_scale = 1.05
            self.text_offset = -2
        elif self.is_clicked:
            self.target_scale = 0.95
            self.text_offset = 0
        else:
            self.target_scale = 1.0
            self.text_offset = 0

        self.scale += (self.target_scale - self.scale) * 0.1

        if self.is_hovered:
            self.glow_alpha = min(100, self.glow_alpha + 7)
        else:
            self.glow_alpha = max(0, self.glow_alpha - 7)

        if self.glow_alpha > 0:
            glow_surf = pygame.Surface((self.rect.width + 16, self.rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 215, 0, self.glow_alpha),
                           (0, 0, self.rect.width + 16, self.rect.height + 16), border_radius=12)
            surface.blit(glow_surf, (self.rect.x - 8, self.rect.y - 8))

        if self.is_hovered:
            color = (80, 50, 40)
        elif self.is_clicked:
            color = (50, 35, 25)
        else:
            color = (60, 40, 30)

        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_x = self.rect.x + (self.rect.width - scaled_width) // 2
        scaled_y = self.rect.y + (self.rect.height - scaled_height) // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)

        pygame.draw.rect(surface, color, scaled_rect, border_radius=8)
        pygame.draw.rect(surface, (139, 69, 19), scaled_rect, 3, border_radius=8)
        pygame.draw.rect(surface, (255, 215, 0), scaled_rect, 1, border_radius=8)

        corner_size = 10
        corners = [
            (scaled_rect.x + 2, scaled_rect.y + 2),
            (scaled_rect.x + scaled_rect.width - corner_size - 2, scaled_rect.y + 2),
            (scaled_rect.x + 2, scaled_rect.y + scaled_rect.height - corner_size - 2),
            (scaled_rect.x + scaled_rect.width - corner_size - 2, scaled_rect.y + scaled_rect.height - corner_size - 2)
        ]
        for cx, cy in corners:
            pygame.draw.rect(surface, (255, 215, 0), (cx, cy, corner_size, corner_size), 1)

        if self.font:
            text_surf = self.font.render(self.text, True, (255, 255, 255))
            if text_surf:
                text_rect = text_surf.get_rect(center=(scaled_rect.centerx, scaled_rect.centery + self.text_offset))
                shadow_surf = self.font.render(self.text, True, (0, 0, 0))
                surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
                surface.blit(text_surf, text_rect)

        if self.is_hovered and random.random() < 0.15:
            particle_colors = [(255, 215, 0), (200, 80, 80), (70, 130, 180)]
            self.particles.append(Particle(
                random.randint(self.rect.x, self.rect.x + self.rect.width),
                random.randint(self.rect.y, self.rect.y + self.rect.height),
                random.choice(particle_colors),
                random.uniform(0.5, 1.5),
                random.randint(2, 4),
                random.randint(80, 150)
            ))

        if self.is_clicked and random.random() < 0.5:
            self.click_particles.append(Particle(
                scaled_rect.centerx,
                scaled_rect.centery,
                (255, 255, 255),
                random.uniform(1.0, 3.0),
                random.randint(3, 6),
                random.randint(50, 100)
            ))

        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)

        for p in self.click_particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.click_particles.remove(p)

class DropdownMenu:
    def __init__(self, text, x, y, width, height, font, items):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.items = items
        self.is_open = False
        self.dropdown_items = []
        self.normal_color = COLORS["accent_blue"]
        self.hover_color = COLORS["accent_blue_light"]
        self.text_color = COLORS["text_white"]
        self.is_hovered = False
        self.glow_alpha = 0

    def update_items(self, screen_width, screen_height):
        """更新下拉菜单项的位置"""
        self.dropdown_items = []
        if self.is_open:
            item_height = min(40, screen_height * 0.06)
            if self.rect.x + self.rect.width * 2 < screen_width:
                for i, (item_text, item_code) in enumerate(self.items):
                    item_y = self.rect.y + i * item_height
                    item_rect = pygame.Rect(self.rect.x + self.rect.width + 10, item_y, self.rect.width, item_height)
                    self.dropdown_items.append((item_text, item_code, item_rect))
            else:
                for i, (item_text, item_code) in enumerate(self.items):
                    item_y = self.rect.y + i * item_height
                    item_rect = pygame.Rect(self.rect.x - self.rect.width - 10, item_y, self.rect.width, item_height)
                    self.dropdown_items.append((item_text, item_code, item_rect))

    def draw(self, surface):
        """绘制下拉菜单"""
        if self.is_hovered:
            self.glow_alpha = min(80, self.glow_alpha + 4)
        else:
            self.glow_alpha = max(0, self.glow_alpha - 4)

        if self.glow_alpha > 0:
            glow_surf = pygame.Surface((self.rect.width + 16, self.rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 215, 0, self.glow_alpha),
                           (0, 0, self.rect.width + 16, self.rect.height + 16), border_radius=12)
            surface.blit(glow_surf, (self.rect.x - 8, self.rect.y - 8))

        if self.is_hovered:
            color = (80, 50, 40)
        else:
            color = (60, 40, 30)

        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (139, 69, 19), self.rect, 3, border_radius=8)
        pygame.draw.rect(surface, (255, 215, 0), self.rect, 1, border_radius=8)

        corner_size = 10
        corners = [
            (self.rect.x + 2, self.rect.y + 2),
            (self.rect.x + self.rect.width - corner_size - 2, self.rect.y + 2),
            (self.rect.x + 2, self.rect.y + self.rect.height - corner_size - 2),
            (self.rect.x + self.rect.width - corner_size - 2, self.rect.y + self.rect.height - corner_size - 2)
        ]
        for cx, cy in corners:
            pygame.draw.rect(surface, (255, 215, 0), (cx, cy, corner_size, corner_size), 1)

        if self.font:
            text_surf = self.font.render(self.text, True, (255, 255, 255))
            if text_surf:
                text_rect = text_surf.get_rect(center=self.rect.center)
                shadow_surf = self.font.render(self.text, True, (0, 0, 0))
                surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
                surface.blit(text_surf, text_rect)

        arrow_text = "v" if self.is_open else ">"
        if self.font:
            arrow_surf = self.font.render(arrow_text, True, (255, 215, 0))
            if arrow_surf:
                arrow_rect = arrow_surf.get_rect(right=self.rect.right - 10, centery=self.rect.centery)
                surface.blit(arrow_surf, arrow_rect)

        if self.is_open:
            for item_text, item_code, item_rect in self.dropdown_items:
                pygame.draw.rect(surface, (50, 35, 25), item_rect, border_radius=5)
                pygame.draw.rect(surface, (139, 69, 19), item_rect, 2, border_radius=5)
                pygame.draw.rect(surface, (255, 215, 0), item_rect, 1, border_radius=5)
                if self.font:
                    item_text_surf = self.font.render(item_text, True, (255, 255, 255))
                    if item_text_surf:
                        item_text_rect = item_text_surf.get_rect(center=item_rect.center)
                        surface.blit(item_text_surf, item_text_rect)

    def check_hover(self, mouse_pos):
        """检查鼠标悬停"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def check_click(self, mouse_pos):
        """检查点击"""
        if self.is_hovered and pygame.mouse.get_pressed()[0]:
            self.is_open = not self.is_open
            return True, None

        if self.is_open:
            for item_text, item_code, item_rect in self.dropdown_items:
                if item_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]:
                    self.is_open = False
                    return True, item_code

        return False, None

def draw_gradient_background(surface, color1, color2):
    """绘制渐变背景"""
    try:
        width, height = surface.get_size()
        for y in range(height):
            ratio = y / max(height, 1)
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    except Exception:
        surface.fill(color1)

clouds = []

for i in range(10):
    clouds.append({
        'x': random.randint(-100, 900),
        'y': random.randint(-100, 700),
        'size': random.randint(30, 80),
        'alpha': random.randint(20, 50),
        'speed_x': random.uniform(-0.1, 0.1),
        'speed_y': random.uniform(-0.05, 0.05)
    })

def draw_three_kingdoms_background(surface, screen_width, screen_height):
    """绘制三国主题背景"""
    try:
        for y in range(screen_height):
            ratio = y / max(screen_height, 1)
            r = int(40 * (1 - ratio) + 20 * ratio)
            g = int(20 * (1 - ratio) + 10 * ratio)
            b = int(30 * (1 - ratio) + 40 * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (screen_width, y))

        for cloud in clouds:
            cloud['x'] += cloud['speed_x']
            cloud['y'] += cloud['speed_y']

            if cloud['x'] > screen_width + 100:
                cloud['x'] = -100
            elif cloud['x'] < -100:
                cloud['x'] = screen_width + 100

            if cloud['y'] > screen_height + 50:
                cloud['y'] = -50
            elif cloud['y'] < -50:
                cloud['y'] = screen_height + 50

            cloud_surf = pygame.Surface((cloud['size'] * 2, cloud['size']), pygame.SRCALPHA)
            pygame.draw.ellipse(cloud_surf, (255, 215, 0, cloud['alpha']), (0, cloud['size'] // 4, cloud['size'], cloud['size'] // 2))
            pygame.draw.ellipse(cloud_surf, (255, 215, 0, cloud['alpha'] // 2), (cloud['size'] // 2, 0, cloud['size'], cloud['size'] // 2))
            pygame.draw.ellipse(cloud_surf, (255, 215, 0, cloud['alpha'] // 3), (cloud['size'] // 3, cloud['size'] // 3, cloud['size'], cloud['size'] // 2))
            surface.blit(cloud_surf, (cloud['x'] - cloud['size'], cloud['y']))

        for i in range(6):
            x = random.randint(0, screen_width)
            y = random.randint(0, screen_height)
            size = random.randint(1, 2)
            alpha = random.randint(20, 40)
            glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 215, 0, alpha), (size * 2, size * 2), size * 2)
            surface.blit(glow_surf, (x - size * 2, y - size * 2))

        border_width = 15
        border_color = (139, 69, 19, 30)
        pygame.draw.rect(surface, border_color, (0, 0, screen_width, border_width))
        pygame.draw.rect(surface, border_color, (0, screen_height - border_width, screen_width, border_width))
        pygame.draw.rect(surface, border_color, (0, 0, border_width, screen_height))
        pygame.draw.rect(surface, border_color, (screen_width - border_width, 0, border_width, screen_height))

        inner_border = 30
        pygame.draw.rect(surface, border_color, (inner_border, inner_border, screen_width - inner_border * 2, 2))
        pygame.draw.rect(surface, border_color, (inner_border, screen_height - inner_border, screen_width - inner_border * 2, 2))
        pygame.draw.rect(surface, border_color, (inner_border, inner_border, 2, screen_height - inner_border * 2))
        pygame.draw.rect(surface, border_color, (screen_width - inner_border, inner_border, 2, screen_height - inner_border * 2))

        draw_chinese_pattern(surface, 50, 50, 40, (139, 69, 19))
        draw_chinese_pattern(surface, screen_width - 90, 50, 40, (139, 69, 19))
        draw_chinese_pattern(surface, 50, screen_height - 90, 40, (139, 69, 19))
        draw_chinese_pattern(surface, screen_width - 90, screen_height - 90, 40, (139, 69, 19))

        def draw_seal(surface, x, y, size, text):
            try:
                pygame.draw.circle(surface, (200, 80, 80, 120), (x, y), size // 2)
                pygame.draw.circle(surface, (200, 80, 80, 150), (x, y), size // 2 - 5, 3)
                if FONT_SMALL:
                    text_surf = FONT_SMALL.render(text, True, (200, 80, 80, 180))
                    if text_surf:
                        text_rect = text_surf.get_rect(center=(x, y))
                        surface.blit(text_surf, text_rect)
            except Exception:
                pass

        draw_seal(surface, screen_width - 100, 100, 60, "三国")
        draw_seal(surface, 100, screen_height - 100, 60, "霸业")
    except Exception:
        surface.fill((10, 10, 25))

def draw_chinese_pattern(surface, x, y, size, color):
    """绘制中式图案装饰"""
    try:
        points = [
            (x, y),
            (x + size, y),
            (x + size, y + size // 3),
            (x + size * 2 // 3, y + size // 3),
            (x + size * 2 // 3, y + size * 2 // 3),
            (x + size, y + size * 2 // 3),
            (x + size, y + size),
            (x, y + size),
            (x, y + size * 2 // 3),
            (x + size // 3, y + size * 2 // 3),
            (x + size // 3, y + size // 3),
            (x, y + size // 3)
        ]
        pygame.draw.polygon(surface, color, points, 2)
    except Exception:
        pass

def draw_three_kingdoms_title(surface, text, y_pos, screen_width):
    """绘制三国风格标题"""
    try:
        if FONT_BIG is None:
            return

        title_width = FONT_BIG.size(text)[0] + 100
        title_height = 80
        title_x = (screen_width - title_width) // 2
        title_y = y_pos - 20

        scroll_surf = pygame.Surface((title_width, title_height), pygame.SRCALPHA)
        pygame.draw.rect(scroll_surf, (60, 30, 20, 200), (0, 0, title_width, title_height), border_radius=5)
        pygame.draw.rect(scroll_surf, (139, 69, 19), (0, 0, title_width, title_height), 3, border_radius=5)
        surface.blit(scroll_surf, (title_x, title_y))

        pattern_size = 40
        draw_chinese_pattern(surface, title_x - pattern_size - 10, title_y + 20, pattern_size, COLORS["accent_gold"])
        draw_chinese_pattern(surface, title_x + title_width + 10, title_y + 20, pattern_size, COLORS["accent_gold"])

        for offset in range(8, 0, -1):
            alpha = 60 - offset * 7
            glow_surf = FONT_BIG.render(text, True, (255, 215, 0))
            if glow_surf:
                glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
                glow_surf.set_alpha(alpha)
                surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
                surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))

        title = FONT_BIG.render(text, True, (255, 215, 0))
        if title:
            title_rect = title.get_rect(center=(screen_width // 2, y_pos))
            shadow = FONT_BIG.render(text, True, (0, 0, 0))
            if shadow:
                surface.blit(shadow, (title_rect.x + 4, title_rect.y + 4))
            surface.blit(title, title_rect)

        line_y = y_pos + 50
        line_color = (139, 69, 19)
        pygame.draw.line(surface, line_color, (screen_width // 2 - 200, line_y), (screen_width // 2 - 80, line_y), 3)
        pygame.draw.line(surface, line_color, (screen_width // 2 - 200, line_y - 5), (screen_width // 2 - 200, line_y + 5), 3)
        pygame.draw.line(surface, line_color, (screen_width // 2 - 80, line_y - 5), (screen_width // 2 - 80, line_y + 5), 3)
        pygame.draw.line(surface, line_color, (screen_width // 2 + 80, line_y), (screen_width // 2 + 200, line_y), 3)
        pygame.draw.line(surface, line_color, (screen_width // 2 + 80, line_y - 5), (screen_width // 2 + 80, line_y + 5), 3)
        pygame.draw.line(surface, line_color, (screen_width // 2 + 200, line_y - 5), (screen_width // 2 + 200, line_y + 5), 3)
        pygame.draw.circle(surface, COLORS["accent_gold"], (screen_width // 2, line_y), 10)
        pygame.draw.circle(surface, (139, 69, 19), (screen_width // 2, line_y), 6)
    except Exception:
        pass

def draw_decorative_frame(surface, rect, color, border_width=3):
    """绘制装饰性边框"""
    try:
        pygame.draw.rect(surface, color, rect, border_width, border_radius=15)
        corner_size = 20
        corners = [
            (rect.x, rect.y),
            (rect.x + rect.width - corner_size, rect.y),
            (rect.x, rect.y + rect.height - corner_size),
            (rect.x + rect.width - corner_size, rect.y + rect.height - corner_size)
        ]
        for cx, cy in corners:
            pygame.draw.rect(surface, COLORS["accent_gold"], (cx, cy, corner_size, corner_size), 2)
    except Exception:
        pass

def draw_resource_panel(surface, x, y, width, height):
    """绘制三国风格资源面板"""
    try:
        panel_rect = pygame.Rect(x, y, width, height)

        panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (60, 40, 30, 200), (0, 0, width, height), border_radius=8)
        surface.blit(panel_surf, (x, y))

        pygame.draw.rect(surface, (139, 69, 19), panel_rect, 3, border_radius=8)
        pygame.draw.rect(surface, (255, 215, 0), panel_rect, 1, border_radius=8)

        corner_size = 12
        corners = [
            (x + 2, y + 2),
            (x + width - corner_size - 2, y + 2),
            (x + 2, y + height - corner_size - 2),
            (x + width - corner_size - 2, y + height - corner_size - 2)
        ]
        for cx, cy in corners:
            pygame.draw.rect(surface, (255, 215, 0), (cx, cy, corner_size, corner_size), 2)

        resources = [
            ("金元宝", data['resources'].get('金元宝', 0), (255, 215, 0)),
            ("水", data['resources'].get('水', 0), (100, 149, 237)),
            ("食物", data['resources'].get('食物', 0), (210, 180, 140))
        ]

        spacing = width // max(len(resources), 1)
        for i, (icon, value, color) in enumerate(resources):
            icon_x = x + i * spacing + spacing // 2
            icon_y = y + height // 2

            bg_rect = pygame.Rect(icon_x - 45, icon_y - 15, 90, 30)
            pygame.draw.rect(surface, (40, 30, 25), bg_rect, border_radius=15)
            pygame.draw.rect(surface, color, bg_rect, 2, border_radius=15)

            if FONT_SMALL:
                text = FONT_SMALL.render(f"{icon}: {value}", True, (255, 255, 255))
                if text:
                    text_rect = text.get_rect(center=(icon_x, icon_y))
                    surface.blit(text, text_rect)
    except Exception:
        pass

def draw_title(surface, text, y_pos, screen_width):
    """绘制带特效的标题"""
    try:
        if FONT_BIG is None:
            return

        for offset in range(5, 0, -1):
            alpha = 50 - offset * 8
            glow_surf = FONT_BIG.render(text, True, COLORS["accent_gold"])
            if glow_surf:
                glow_surf.set_alpha(alpha)
                glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
                surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
                surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))

        title = FONT_BIG.render(text, True, COLORS["accent_gold"])
        if title:
            title_rect = title.get_rect(center=(screen_width // 2, y_pos))
            shadow = FONT_BIG.render(text, True, (0, 0, 0))
            if shadow:
                surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
            surface.blit(title, title_rect)

        line_y = y_pos + 40
        pygame.draw.line(surface, COLORS["accent_gold"],
                        (screen_width // 2 - 150, line_y),
                        (screen_width // 2 - 50, line_y), 3)
        pygame.draw.line(surface, COLORS["accent_gold"],
                        (screen_width // 2 + 50, line_y),
                        (screen_width // 2 + 150, line_y), 3)
        pygame.draw.circle(surface, COLORS["accent_gold"], (screen_width // 2, line_y), 8)
        pygame.draw.circle(surface, COLORS["bg_dark"], (screen_width // 2, line_y), 5)
    except Exception:
        pass

def clear():
    """清屏"""
    global screen
    if screen:
        screen.fill(COLORS["bg_dark"])

def run_module(module_file):
    """运行子模块"""
    try:
        if is_android():
            if module_file == "pvp_p2p.py":
                from ASSET.pvp_p2p import main as pvp_main
                pvp_main()
            elif module_file == "game_map_pygame.py":
                from ASSET.game_map_pygame import main as map_main
                map_main()
            elif module_file == "battle_system.py":
                from ASSET.battle_system import main as battle_main
                battle_main()
            elif module_file == "shop_system.py":
                from ASSET.shop_system import main as shop_main
                shop_main()
            elif module_file == "hero_warehouse.py":
                from ASSET.hero_warehouse import main as hero_main
                hero_main()
            elif module_file == "activity_system.py":
                from ASSET.activity_system import main as activity_main
                activity_main()
            elif module_file == "login_system.py":
                from ASSET.login_system import main as login_main
                login_main()
            elif module_file == "snake_game.py":
                from ASSET.snake_game import main as snake_main
                snake_main()
            elif module_file == "push_box.py":
                from ASSET.push_box import main as push_box_main
                push_box_main()
            elif module_file == "breakout.py":
                from ASSET.breakout import main as breakout_main
                breakout_main()
            elif module_file == "minesweeper.py":
                from ASSET.minesweeper import main as minesweeper_main
                minesweeper_main()
            elif module_file == "game_2048.py":
                from ASSET.game_2048 import main as game_2048_main
                game_2048_main()
            elif module_file == "tetris.py":
                from ASSET.tetris import main as tetris_main
                tetris_main()
            elif module_file == "gobang.py":
                from ASSET.gobang import main as gobang_main
                gobang_main()
            elif module_file == "achievement_system.py":
                from ASSET.achievement_system import main as achievement_main
                achievement_main()
            elif module_file == "tech_tree.py":
                from ASSET.tech_tree import main as tech_tree_main
                tech_tree_main()
            elif module_file == "social_system.py":
                from ASSET.social_system import main as social_main
                social_main()
            elif module_file == "pet_system.py":
                from ASSET.pet_system import main as pet_main
                pet_main()
            elif module_file == "building_system.py":
                from ASSET.building_system import main as building_main
                building_main()
            elif module_file == "talent_system.py":
                from ASSET.talent_system import main as talent_main
                talent_main()
            elif module_file == "fishing_system.py":
                from ASSET.fishing_system import main as fishing_main
                fishing_main()
            elif module_file == "alchemy_system.py":
                from ASSET.alchemy_system import main as alchemy_main
                alchemy_main()
            elif module_file == "quest_system.py":
                from ASSET.quest_system import main as quest_main
                quest_main()
            elif module_file == "trading_system.py":
                from ASSET.trading_system import main as trading_main
                trading_main()
            elif module_file == "equipment_system.py":
                from ASSET.equipment_system import main as equipment_main
                equipment_main()
            elif module_file == "ranking_system.py":
                from ASSET.ranking_system import main as ranking_main
                ranking_main()
            elif module_file == "daily_checkin.py":
                from ASSET.daily_checkin import main as checkin_main
                checkin_main()
            elif module_file == "weather_system.py":
                from ASSET.weather_system import main as weather_main
                weather_main()
            elif module_file == "game_map_3d.py":
                from ASSET.game_map_3d import main as map_3d_main
                map_3d_main()
            elif module_file == "fashion_system.py":
                from ASSET.fashion_system import main as fashion_main
                fashion_main()
            elif module_file == "hero_recruitment.py":
                from ASSET.hero_recruitment import main as hero_main
                hero_main()
            elif module_file == "newbie_guide.py":
                from ASSET.newbie_guide import main as guide_main
                guide_main()
            elif module_file == "background_story.py":
                from ASSET.background_story import main as story_main
                story_main()
            elif module_file == "limited_time_events.py":
                from ASSET.limited_time_events import main as limited_main
                limited_main()
            elif module_file == "pet_arena.py":
                from ASSET.pet_arena import main as arena_main
                arena_main()
        else:
            if module_file == "pvp_p2p.py":
                from ASSET.pvp_p2p import main as pvp_main
                pvp_main()
            elif module_file == "game_map_pygame.py":
                from ASSET.game_map_pygame import main as map_main
                map_main()
            elif module_file == "battle_system.py":
                from ASSET.battle_system import main as battle_main
                battle_main()
            elif module_file == "shop_system.py":
                from ASSET.shop_system import main as shop_main
                shop_main()
            elif module_file == "hero_warehouse.py":
                from ASSET.hero_warehouse import main as hero_main
                hero_main()
            elif module_file == "activity_system.py":
                from ASSET.activity_system import main as activity_main
                activity_main()
            elif module_file == "login_system.py":
                from ASSET.login_system import main as login_main
                login_main()
            elif module_file == "snake_game.py":
                from ASSET.snake_game import main as snake_main
                snake_main()
            elif module_file == "push_box.py":
                from ASSET.push_box import main as push_box_main
                push_box_main()
            elif module_file == "breakout.py":
                from ASSET.breakout import main as breakout_main
                breakout_main()
            elif module_file == "minesweeper.py":
                from ASSET.minesweeper import main as minesweeper_main
                minesweeper_main()
            elif module_file == "game_2048.py":
                from ASSET.game_2048 import main as game_2048_main
                game_2048_main()
            elif module_file == "tetris.py":
                from ASSET.tetris import main as tetris_main
                tetris_main()
            elif module_file == "gobang.py":
                from ASSET.gobang import main as gobang_main
                gobang_main()
            elif module_file == "achievement_system.py":
                from ASSET.achievement_system import main as achievement_main
                achievement_main()
            elif module_file == "tech_tree.py":
                from ASSET.tech_tree import main as tech_tree_main
                tech_tree_main()
            elif module_file == "social_system.py":
                from ASSET.social_system import main as social_main
                social_main()
            elif module_file == "pet_system.py":
                from ASSET.pet_system import main as pet_main
                pet_main()
            elif module_file == "building_system.py":
                from ASSET.building_system import main as building_main
                building_main()
            elif module_file == "talent_system.py":
                from ASSET.talent_system import main as talent_main
                talent_main()
            elif module_file == "fishing_system.py":
                from ASSET.fishing_system import main as fishing_main
                fishing_main()
            elif module_file == "alchemy_system.py":
                from ASSET.alchemy_system import main as alchemy_main
                alchemy_main()
            elif module_file == "quest_system.py":
                from ASSET.quest_system import main as quest_main
                quest_main()
            elif module_file == "trading_system.py":
                from ASSET.trading_system import main as trading_main
                trading_main()
            elif module_file == "equipment_system.py":
                from ASSET.equipment_system import main as equipment_main
                equipment_main()
            elif module_file == "ranking_system.py":
                from ASSET.ranking_system import main as ranking_main
                ranking_main()
            elif module_file == "daily_checkin.py":
                from ASSET.daily_checkin import main as checkin_main
                checkin_main()
            elif module_file == "weather_system.py":
                from ASSET.weather_system import main as weather_main
                weather_main()
            elif module_file == "game_map_3d.py":
                from ASSET.game_map_3d import main as map_3d_main
                map_3d_main()
            elif module_file == "fashion_system.py":
                from ASSET.fashion_system import main as fashion_main
                fashion_main()
            elif module_file == "hero_recruitment.py":
                from ASSET.hero_recruitment import main as hero_main
                hero_main()
            elif module_file == "newbie_guide.py":
                from ASSET.newbie_guide import main as guide_main
                guide_main()
            elif module_file == "background_story.py":
                from ASSET.background_story import main as story_main
                story_main()
            elif module_file == "limited_time_events.py":
                from ASSET.limited_time_events import main as limited_main
                limited_main()
            elif module_file == "pet_arena.py":
                from ASSET.pet_arena import main as arena_main
                arena_main()

        pygame.event.clear()

    except Exception as e:
        logger.error(f"启动模块 {module_file} 失败：{str(e)}")
        logger.error("详细错误信息：")
        import traceback
        logger.error(traceback.format_exc())
        if is_android():
            if FONT_SMALL:
                error_text = FONT_SMALL.render(f"启动失败：{str(e)}", True, (255, 0, 0))
                if error_text and screen:
                    screen.blit(error_text, (50, 50))
                    pygame.display.flip()
            pygame.time.wait(2000)
        else:
            input("按回车返回...")

def mini_games_menu():
    """小游戏中心菜单"""
    global screen, clock
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    try:
        from ASSET.achievement_system import update_achievement_progress
    except Exception:
        update_achievement_progress = None

    mini_games = [
        ("贪吃蛇", "snake_game.py"),
        ("推箱子", "push_box.py"),
        ("打砖块", "breakout.py"),
        ("扫雷", "minesweeper.py"),
        ("2048", "game_2048.py"),
        ("俄罗斯方块", "tetris.py"),
        ("五子棋", "gobang.py"),
        ("返回主菜单", "back")
    ]

    button_width = min(350, screen_width * 0.45)
    button_height = min(55, screen_height * 0.07)
    button_spacing = min(15, screen_height * 0.025)
    start_y = screen_height * 0.22

    total_height = len(mini_games) * button_height + (len(mini_games) - 1) * button_spacing
    if total_height > screen_height * 0.7:
        max_possible_height = screen_height * 0.7
        button_height = max_possible_height / (len(mini_games) + (len(mini_games) - 1) * 0.25)
        button_height = min(button_height, 45)

    mini_games_buttons = []

    for i, (text, code) in enumerate(mini_games):
        x = (screen_width - button_width) // 2
        y = start_y + i * (button_height + button_spacing)
        if code == "back":
            color = (100, 100, 150)
        else:
            color = COLORS["accent_blue"]

        btn = Button(text, x, y, button_width, button_height, FONT_SMALL, normal_color=color)
        mini_games_buttons.append((btn, code))

    particles = []

    running = True
    while running:
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])

        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))

        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)

        draw_title(screen, "小游戏中心", screen_height * 0.12, screen_width)

        mouse_pos = pygame.mouse.get_pos()

        for btn, code in mini_games_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                safe_exit("小游戏中心")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn, code in mini_games_buttons:
                    if btn.rect.collidepoint(event.pos):
                        if code == "back":
                            running = False
                        else:
                            run_module(code)
                            if update_achievement_progress:
                                update_achievement_progress("mini_game_played")

        clock.tick(60)

def setting_menu():
    """设置菜单"""
    global screen, clock

    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import save_login_state
        login_state_available = True
    except Exception:
        save_login_state = None
        login_state_available = False

    particles = []

    resolution_changed = False

    def get_settings_text():
        if 'fullscreen' not in data['settings']['graphics']:
            data['settings']['graphics']['fullscreen'] = False
            save()

        return [
            f"分辨率：{data['settings']['graphics']['resolution']}",
            f"全屏模式：{'开' if data['settings']['graphics']['fullscreen'] else '关'}",
            f"地图最大元素：{data['settings']['map']['max_locations']}",
            f"音效：{'开' if data['settings']['sound']['enable'] else '关'}",
            "返回主菜单"
        ]

    running = True
    while running:
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        button_width = min(400, screen_width * 0.5)
        button_height = min(60, screen_height * 0.08)
        button_spacing = min(25, screen_height * 0.035)
        start_y = screen_height * 0.3

        setting_buttons = []
        for i, text in enumerate(get_settings_text()):
            x = (screen_width - button_width) // 2
            y = start_y + i * (button_height + button_spacing)
            btn = Button(text, x, y, button_width, button_height, FONT_SMALL)
            setting_buttons.append(btn)

        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])

        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))

        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)

        draw_title(screen, "游戏设置", screen_height * 0.12, screen_width)

        mouse_pos = pygame.mouse.get_pos()

        for btn in setting_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                safe_exit("主菜单")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(setting_buttons):
                    if btn.rect.collidepoint(event.pos):
                        if i == 0:
                            resolutions = ["800x600", "1024x768", "1280x720", "1366x768", "1920x1080"]
                            current = data['settings']['graphics']['resolution']
                            try:
                                idx = resolutions.index(current)
                                next_idx = (idx + 1) % len(resolutions)
                            except ValueError:
                                next_idx = 0
                            data['settings']['graphics']['resolution'] = resolutions[next_idx]
                            save()
                            resolution_changed = True
                        elif i == 1:
                            data['settings']['graphics']['fullscreen'] = not data['settings']['graphics']['fullscreen']
                            save()
                            resolution_changed = True
                        elif i == 2:
                            new_max = data['settings']['map']['max_locations'] + 10
                            if new_max > 100:
                                new_max = 10
                            data['settings']['map']['max_locations'] = new_max
                            save()
                        elif i == 3:
                            data['settings']['sound']['enable'] = not data['settings']['sound']['enable']
                            save()
                        elif i == 4:
                            running = False

        clock.tick(60)

def input_save_name(screen, font_title, font_input):
    """输入存档名称"""
    input_box = pygame.Rect(screen.get_width() // 4, screen.get_height() // 2, screen.get_width() // 2, 50)
    text = ""
    active = True
    clock = pygame.time.Clock()

    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

        pygame.draw.rect(screen, (50, 50, 80), input_box)
        pygame.draw.rect(screen, (100, 100, 150), input_box, 2)

        if font_input:
            txt_surface = font_input.render(text, True, (255, 255, 255))
            if txt_surface:
                screen.blit(txt_surface, (input_box.x + 5, input_box.y + 10))

        pygame.display.flip()
        clock.tick(30)

    return text if text else "存档"

def show_message(message):
    """显示消息"""
    if FONT_MAIN:
        msg_surface = FONT_MAIN.render(message, True, (255, 255, 255))
        if msg_surface and screen:
            screen.blit(msg_surface, (screen.get_width() // 2 - msg_surface.get_width() // 2,
                                     screen.get_height() // 2))
            pygame.display.flip()
            pygame.time.wait(2000)

def main():
    """主菜单主循环"""
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG, data

    if not pygame.get_init():
        pygame.init()

    init_fonts()

    if FONT_MAIN is None or FONT_SMALL is None or FONT_BIG is None:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 28)
        FONT_BIG = pygame.font.Font(None, 60)

    if 'fullscreen' not in data['settings']['graphics']:
        data['settings']['graphics']['fullscreen'] = False
        save()

    resolution = data['settings']['graphics']['resolution']
    fullscreen = data['settings']['graphics']['fullscreen']

    if is_android():
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        screen = pygame.display.set_mode((screen_width, screen_height))
    else:
        if fullscreen:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            screen_width = screen.get_width()
            screen_height = screen.get_height()
        else:
            try:
                width, height = map(int, resolution.split('x'))
                screen = pygame.display.set_mode((width, height))
                screen_width = width
                screen_height = height
            except ValueError:
                screen = pygame.display.set_mode((800, 600))
                screen_width = 800
                screen_height = 600

    pygame.display.set_caption("游戏主菜单")
    clock = pygame.time.Clock()

    if "tutorial_completed" not in data or not data["tutorial_completed"]:
        try:
            from ASSET.newbie_guide import main as guide_main
            guide_main()
        except Exception:
            pass

    button_width = min(300, screen_width * 0.35)
    button_height = min(55, screen_height * 0.07)
    button_spacing = min(15, screen_height * 0.025)
    start_y = screen_height * 0.28

    game_core_items = [
        ("PVP联机", "1"),
        ("游戏地图", "2"),
        ("3D地图", "28"),
        ("副本挑战", "3"),
        ("小游戏中心", "10"),
        ("竞速模式", "33"),
        ("生存模式", "34")
    ]

    game_system_items = [
        ("武将仓库", "7"),
        ("武将招募", "29"),
        ("活动中心", "8"),
        ("科技树系统", "12"),
        ("建筑系统", "21"),
        ("天赋系统", "22"),
        ("装备系统", "17"),
        ("宠物系统", "19"),
        ("宠物竞技场", "38"),
        ("时装系统", "30"),
        ("任务系统", "20"),
        ("钓鱼系统", "23"),
        ("炼金系统", "24"),
        ("游戏内AI", "25"),
        ("疑难解答", "26"),
        ("宠物进化", "35")
    ]

    social_items = [
        ("成就系统", "11"),
        ("排行榜系统", "13"),
        ("每日签到", "14"),
        ("社交系统", "16"),
        ("交易系统", "18")
    ]

    other_items = [
        ("游戏商城", "6"),
        ("天气系统", "27"),
        ("新手引导", "31"),
        ("背景故事", "32"),
        ("每日任务", "36"),
        ("限时活动", "37")
    ]

    menu_elements = []

    game_core_menu = DropdownMenu("游戏核心", (screen_width - button_width) // 2, start_y, button_width, button_height, FONT_SMALL, game_core_items)
    menu_elements.append(("dropdown", game_core_menu))

    game_system_menu = DropdownMenu("游戏系统", (screen_width - button_width) // 2, start_y + button_height + button_spacing, button_width, button_height, FONT_SMALL, game_system_items)
    menu_elements.append(("dropdown", game_system_menu))

    social_menu = DropdownMenu("社交与排行", (screen_width - button_width) // 2, start_y + 2 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, social_items)
    menu_elements.append(("dropdown", social_menu))

    other_menu = DropdownMenu("其他功能", (screen_width - button_width) // 2, start_y + 3 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, other_items)
    menu_elements.append(("dropdown", other_menu))

    save_btn = Button("保存进度", (screen_width - button_width) // 2, start_y + 4 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
    menu_elements.append(("button", (save_btn, "4")))

    load_btn = Button("读取存档", (screen_width - button_width) // 2, start_y + 5 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
    menu_elements.append(("button", (load_btn, "15")))

    setting_btn = Button("游戏设置", (screen_width - button_width) // 2, start_y + 6 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
    menu_elements.append(("button", (setting_btn, "5")))

    exit_btn = Button("退出游戏", (screen_width - button_width) // 2, start_y + 7 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, normal_color=COLORS["accent_red"])
    menu_elements.append(("button", (exit_btn, "9")))

    particles = []

    moving_elements = []
    
    floating_texts = []
    
    click_effects = []
    
    mouse_trail = MouseTrail(max_trails=25)
    
    bg_decorations = []
    for i in range(15):
        bg_decorations.append({
            'x': random.randint(0, screen_width),
            'y': random.randint(0, screen_height),
            'size': random.randint(5, 15),
            'alpha': random.randint(10, 30),
            'speed': random.uniform(0.1, 0.3),
            'type': random.choice(['star', 'circle', 'diamond'])
        })
    
    rainbow_particles = []
    
    comet_trails = []
    
    pet_sprite = PetSprite()
    
    floating_particles = FloatingParticles(screen_width, screen_height)

    current_time = 0

    running = True
    while running:
        current_time += 1

        draw_three_kingdoms_background(screen, screen_width, screen_height)
        
        if random.random() < 0.005 and len(comet_trails) < 5:
            comet_trails.append({
                'x': screen_width + 50,
                'y': random.randint(0, screen_height // 2),
                'speed': random.uniform(3.0, 6.0),
                'length': random.randint(80, 150),
                'alpha': random.randint(100, 200),
                'hue': random.randint(0, 360)
            })
        
        for comet in comet_trails[:]:
            comet['x'] -= comet['speed']
            if comet['x'] < -comet['length']:
                comet_trails.remove(comet)
                continue
            try:
                h = comet['hue']
                r = int(127 + 127 * math.sin(h * math.pi / 180))
                g = int(127 + 127 * math.sin((h + 120) * math.pi / 180))
                b = int(127 + 127 * math.sin((h + 240) * math.pi / 180))
                for i in range(int(comet['length'])):
                    alpha = int(comet['alpha'] * (1 - i / comet['length']))
                    x_pos = comet['x'] + i
                    y_pos = comet['y'] + math.sin(current_time * 0.05 + i * 0.1) * 3
                    if 0 <= x_pos <= screen_width and 0 <= y_pos <= screen_height:
                        try:
                            trail_surf = pygame.Surface((3, 3), pygame.SRCALPHA)
                            pygame.draw.circle(trail_surf, (r, g, b, alpha), (1, 1), 1)
                            screen.blit(trail_surf, (int(x_pos), int(y_pos)))
                        except Exception:
                            pass
            except Exception:
                pass
        
        if random.random() < 0.02 and len(rainbow_particles) < 30:
            hue = random.randint(0, 360)
            rainbow_particles.append({
                'x': random.randint(0, screen_width),
                'y': screen_height + 10,
                'speed': random.uniform(0.8, 1.5),
                'hue': hue,
                'size': random.randint(3, 6),
                'alpha': random.randint(150, 255)
            })
        
        for rp in rainbow_particles[:]:
            rp['y'] -= rp['speed']
            rp['x'] += math.sin(current_time * 0.02 + rp['hue'] * 0.1) * 0.5
            rp['hue'] = (rp['hue'] + 1) % 360
            if rp['y'] < -20:
                rainbow_particles.remove(rp)
                continue
            try:
                h = rp['hue']
                r = int(127 + 127 * math.sin(h * math.pi / 180))
                g = int(127 + 127 * math.sin((h + 120) * math.pi / 180))
                b = int(127 + 127 * math.sin((h + 240) * math.pi / 180))
                rainbow_surf = pygame.Surface((int(rp['size'] * 2), int(rp['size'] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(rainbow_surf, (r, g, b, rp['alpha']), (int(rp['size']), int(rp['size'])), int(rp['size']))
                screen.blit(rainbow_surf, (int(rp['x'] - rp['size']), int(rp['y'] - rp['size'])))
            except Exception:
                pass

        for decor in bg_decorations:
            decor['x'] += math.sin(current_time * 0.001 + decor['y'] * 0.01) * decor['speed']
            decor['y'] += math.cos(current_time * 0.001 + decor['x'] * 0.01) * decor['speed']

            if decor['x'] < -50:
                decor['x'] = screen_width + 50
            elif decor['x'] > screen_width + 50:
                decor['x'] = -50
            if decor['y'] < -50:
                decor['y'] = screen_height + 50
            elif decor['y'] > screen_height + 50:
                decor['y'] = -50

            try:
                size = int(decor['size'])
                if size <= 0:
                    size = 5
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                if decor['type'] == 'star':
                    decor_alpha = max(1, min(255, decor['alpha']))
                    pygame.draw.polygon(surf, (255, 215, 0, decor_alpha), 
                                      [(size, 0), (size + size//2, size), (size, size * 2), 
                                       (size - size//2, size)])
                elif decor['type'] == 'diamond':
                    decor_alpha = max(1, min(255, decor['alpha']))
                    pygame.draw.polygon(surf, (255, 215, 0, decor_alpha),
                                      [(size, 0), (size * 2, size), (size, size * 2), (0, size)])
                else:
                    decor_alpha = max(1, min(255, decor['alpha']))
                    pygame.draw.circle(surf, (255, 215, 0, decor_alpha), (size, size), size)
                screen.blit(surf, (int(decor['x'] - decor['size']), int(decor['y'] - decor['size'])))
            except Exception:
                pass

        if random.random() < 0.008:
            moving_elements.append({
                'x': screen_width + 100,
                'y': random.randint(50, screen_height // 3),
                'size': random.randint(60, 120),
                'speed_x': -random.uniform(0.15, 0.25),
                'speed_y': random.uniform(0.08, 0.12),
                'alpha': random.randint(20, 40),
                'life': random.randint(1500, 2500)
            })

        for element in moving_elements[:]:
            element['x'] += element['speed_x']
            element['y'] += element['speed_y']
            element['life'] -= 1

            if element['life'] > 0:
                try:
                    surf = pygame.Surface((int(element['size']), int(element['size'] // 2)), pygame.SRCALPHA)
                    pygame.draw.ellipse(surf, (255, 215, 0, element['alpha']), (0, 0, element['size'], element['size'] // 2))
                    screen.blit(surf, (int(element['x']), int(element['y'])))
                except Exception:
                    pass
            else:
                moving_elements.remove(element)

        if random.random() < 0.1 and len(particles) < 25:
            particle_type = random.choice(['gold', 'red', 'blue'])

            if particle_type == 'gold':
                particles.append(Particle(
                    random.randint(0, screen_width),
                    -10,
                    (255, 215, 0),
                    random.uniform(1.8, 3.2),
                    random.randint(2, 4),
                    random.randint(90, 140)
                ))
            elif particle_type == 'red':
                particles.append(Particle(
                    random.randint(0, screen_width),
                    -10,
                    (200, 80, 80),
                    random.uniform(1.5, 2.8),
                    random.randint(1, 3),
                    random.randint(70, 110)
                ))
            else:
                particles.append(Particle(
                    random.randint(0, screen_width),
                    -10,
                    (70, 130, 180),
                    random.uniform(1.0, 2.2),
                    random.randint(1, 2),
                    random.randint(110, 170)
                ))

        for p in particles[:]:
            p.update()
            p.x += math.sin(p.y * 0.02 + current_time * 0.001) * 0.6
            if p.color == (255, 215, 0):
                if random.random() < 0.15:
                    p.size *= 1.1
            elif p.color == (200, 80, 80):
                p.speed_y += 0.025
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)
        
        try:
            mouse_trail.update()
            mouse_trail.draw(screen)
        except Exception:
            pass
        
        try:
            floating_particles.update()
            floating_particles.draw(screen)
        except Exception:
            pass
        
        try:
            pet_sprite.update(mouse_pos)
            pet_sprite.draw(screen)
        except Exception:
            pass

        draw_three_kingdoms_title(screen, "三国霸业", screen_height * 0.08, screen_width)

        subtitle_text = "群雄逐鹿，谁主沉浮"
        if FONT_MAIN:
            subtitle_surf = FONT_MAIN.render(subtitle_text, True, (255, 255, 255))
            if subtitle_surf:
                subtitle_rect = subtitle_surf.get_rect(center=(screen_width // 2, screen_height * 0.14))
                for offset in range(3, 0, -1):
                    glow_surf = FONT_MAIN.render(subtitle_text, True, (255, 215, 0))
                    if glow_surf:
                        glow_surf.set_alpha(80)
                        screen.blit(glow_surf, (subtitle_rect.x - offset, subtitle_rect.y - offset))
                screen.blit(subtitle_surf, subtitle_rect)

        panel_width = min(500, screen_width * 0.7)
        draw_resource_panel(screen, (screen_width - panel_width) // 2,
                          screen_height * 0.18, panel_width, 50)

        mouse_pos = pygame.mouse.get_pos()

        for element_type, element in menu_elements:
            if element_type == "dropdown":
                element.update_items(screen_width, screen_height)
                element.check_hover(mouse_pos)
            elif element_type == "button":
                btn, code = element
                btn.check_hover(mouse_pos)

        for element_type, element in menu_elements:
            if element_type == "button":
                btn, code = element
                btn.draw(screen)
                if btn.is_hovered:
                    try:
                        glow_rect = btn.rect.inflate(10, 10)
                        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                        for i in range(5, 0, -1):
                            alpha = int(30 * (1 - i / 6))
                            pygame.draw.rect(glow_surf, (255, 215, 0, alpha), 
                                           (i, i, glow_rect.width - i*2, glow_rect.height - i*2),
                                           border_radius=btn.rect.width // 10)
                        screen.blit(glow_surf, (glow_rect.x, glow_rect.y))
                    except Exception:
                        pass

        for element_type, element in menu_elements:
            if element_type == "dropdown":
                element.draw(screen)
                if hasattr(element, 'is_open') and element.is_open:
                    for opt_idx, (item_text, item_code, item_rect) in enumerate(element.dropdown_items):
                        try:
                            if item_rect.collidepoint(mouse_pos):
                                highlight_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
                                pygame.draw.rect(highlight_surf, (100, 180, 255, 80),
                                               (0, 0, item_rect.width, item_rect.height),
                                               border_radius=8)
                                screen.blit(highlight_surf, (item_rect.x, item_rect.y))
                        except Exception:
                            pass

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                safe_exit("主菜单")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    for i in range(15):
                        mouse_trail.add_trail(
                            event.pos[0] + random.randint(-20, 20),
                            event.pos[1] + random.randint(-20, 20)
                        )
                except Exception:
                    pass
                
                for element_type, element in menu_elements:
                    if element_type == "dropdown":
                        clicked, code = element.check_click(mouse_pos)
                        if clicked and code:
                            if code == "1":
                                run_module("pvp_p2p.py")
                            elif code == "2":
                                run_module("game_map_pygame.py")
                            elif code == "28":
                                run_module("game_map_3d.py")
                            elif code == "29":
                                run_module("hero_recruitment.py")
                            elif code == "31":
                                run_module("newbie_guide.py")
                            elif code == "32":
                                run_module("background_story.py")
                            elif code == "3":
                                run_module("battle_system.py")
                            elif code == "7":
                                run_module("hero_warehouse.py")
                            elif code == "8":
                                run_module("activity_system.py")
                            elif code == "12":
                                run_module("tech_tree.py")
                            elif code == "21":
                                run_module("building_system.py")
                            elif code == "22":
                                run_module("talent_system.py")
                            elif code == "11":
                                run_module("achievement_system.py")
                            elif code == "13":
                                run_module("ranking_system.py")
                            elif code == "14":
                                run_module("daily_checkin.py")
                            elif code == "6":
                                run_module("shop_system.py")
                            elif code == "10":
                                mini_games_menu()
                            elif code == "16":
                                run_module("social_system.py")
                            elif code == "17":
                                run_module("equipment_system.py")
                            elif code == "18":
                                run_module("trading_system.py")
                            elif code == "19":
                                run_module("pet_system.py")
                            elif code == "30":
                                run_module("fashion_system.py")
                            elif code == "20":
                                run_module("quest_system.py")
                            elif code == "23":
                                run_module("fishing_system.py")
                            elif code == "24":
                                run_module("alchemy_system.py")
                            elif code == "25":
                                run_module("ai_system.py")
                            elif code == "26":
                                run_module("faq_system.py")
                            elif code == "27":
                                run_module("weather_system.py")
                            break
                    elif element_type == "button":
                        btn, code = element
                        if btn.check_click(mouse_pos):
                            if code == "4":
                                username = data.get("username", "player")
                                save_name = input_save_name(screen, FONT_MAIN, FONT_SMALL)
                                if save_name:
                                    from ASSET.login_system import save_user_progress, save_game
                                    save_user_progress(username, data)
                                    success, message = save_game(username, save_name, data)
                                    if success:
                                        show_message("保存成功！")
                                    else:
                                        show_message(f"保存失败：{message}")
                            elif code == "15":
                                username = data.get("username", "player")
                                from ASSET.login_system import show_save_manager
                                save_result = show_save_manager(screen, FONT_BIG, FONT_MAIN, FONT_SMALL, username, data)
                                if save_result:
                                    data.clear()
                                    data.update(save_result)
                                    save()
                                    show_message("读取存档成功！")
                            elif code == "5":
                                old_width = screen_width
                                old_height = screen_height
                                setting_menu()
                                screen_width = screen.get_width()
                                screen_height = screen.get_height()
                                if screen_width != old_width or screen_height != old_height:
                                    button_width = min(320, screen_width * 0.4)
                                    button_height = min(60, screen_height * 0.08)
                                    button_spacing = min(12, screen_height * 0.02)
                                    start_y = screen_height * 0.25
                                    menu_elements = []
                                    game_core_menu = DropdownMenu("游戏核心", (screen_width - button_width) // 2, start_y, button_width, button_height, FONT_SMALL, game_core_items)
                                    menu_elements.append(("dropdown", game_core_menu))
                                    game_system_menu = DropdownMenu("游戏系统", (screen_width - button_width) // 2, start_y + button_height + button_spacing, button_width, button_height, FONT_SMALL, game_system_items)
                                    menu_elements.append(("dropdown", game_system_menu))
                                    social_menu = DropdownMenu("社交与排行", (screen_width - button_width) // 2, start_y + 2 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, social_items)
                                    menu_elements.append(("dropdown", social_menu))
                                    other_menu = DropdownMenu("其他功能", (screen_width - button_width) // 2, start_y + 3 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, other_items)
                                    menu_elements.append(("dropdown", other_menu))
                                    save_btn = Button("保存进度", (screen_width - button_width) // 2, start_y + 4 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
                                    menu_elements.append(("button", (save_btn, "4")))
                                    load_btn = Button("读取存档", (screen_width - button_width) // 2, start_y + 5 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
                                    menu_elements.append(("button", (load_btn, "15")))
                                    setting_btn = Button("游戏设置", (screen_width - button_width) // 2, start_y + 6 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
                                    menu_elements.append(("button", (setting_btn, "5")))
                                    exit_btn = Button("退出游戏", (screen_width - button_width) // 2, start_y + 7 * (button_height + button_spacing), button_width, button_height, FONT_SMALL, normal_color=COLORS["accent_red"])
                                    menu_elements.append(("button", (exit_btn, "9")))
                            elif code == "9":
                                exit_choice = show_exit_menu()
                                if exit_choice == "exit_game":
                                    save()
                                    show_message("感谢游玩！")
                                    safe_exit("主菜单")
                                elif exit_choice == "exit_login":
                                    save()
                                    data["username"] = ""
                                    data["login_status"] = False
                                    save()
                                    if is_android():
                                        from ASSET.login_system import main as login_main
                                        login_main()
                                    else:
                                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                        login_path = os.path.join(os.path.dirname(__file__), "login_system.py")
                                        env = os.environ.copy()
                                        env['PYTHONPATH'] = project_root
                                        subprocess.Popen([sys.executable, login_path], cwd=project_root, env=env)
                                    safe_exit("主菜单")
                            break

        clock.tick(60)

def show_exit_menu():
    """显示退出选择菜单"""
    global screen, clock
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    panel_width = 400
    panel_height = 200
    panel_x = (screen_width - panel_width) // 2
    panel_y = (screen_height - panel_height) // 2

    button_width = 120
    button_height = 50
    button_spacing = 20
    start_y = panel_y + 80

    exit_game_btn = Button("退出游戏",
                          panel_x + (panel_width - button_width * 3 - button_spacing * 2) // 2,
                          start_y,
                          button_width, button_height, FONT_SMALL,
                          normal_color=COLORS["accent_red"])

    exit_login_btn = Button("退出登录",
                           panel_x + (panel_width - button_width * 3 - button_spacing * 2) // 2 + button_width + button_spacing,
                           start_y,
                           button_width, button_height, FONT_SMALL,
                           normal_color=COLORS["accent_blue"])

    cancel_btn = Button("取消",
                        panel_x + (panel_width - button_width * 3 - button_spacing * 2) // 2 + button_width * 2 + button_spacing * 2,
                        start_y,
                        button_width, button_height, FONT_SMALL,
                        normal_color=COLORS["accent_green"])

    particles = []

    running = True
    while running:
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])

        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))

        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)

        pygame.draw.rect(screen, (30, 30, 55), (panel_x, panel_y, panel_width, panel_height), border_radius=15)
        pygame.draw.rect(screen, (139, 69, 19), (panel_x, panel_y, panel_width, panel_height), 3, border_radius=15)

        if FONT_MAIN:
            title_surf = FONT_MAIN.render("确定要退出吗？", True, (255, 215, 0))
            if title_surf:
                title_rect = title_surf.get_rect(center=(panel_x + panel_width // 2, panel_y + 40))
                screen.blit(title_surf, title_rect)

        mouse_pos = pygame.mouse.get_pos()

        exit_game_btn.check_hover(mouse_pos)
        exit_login_btn.check_hover(mouse_pos)
        cancel_btn.check_hover(mouse_pos)

        exit_game_btn.draw(screen)
        exit_login_btn.draw(screen)
        cancel_btn.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if exit_game_btn.check_click(mouse_pos):
                    return "exit_game"
                elif exit_login_btn.check_click(mouse_pos):
                    return "exit_login"
                elif cancel_btn.check_click(mouse_pos):
                    return "cancel"

        clock.tick(60)

def startup_animation():
    """启动动画"""
    global FONT_MAIN, FONT_SMALL, FONT_BIG
    
    screen_width, screen_height = get_screen_size()

    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()

    init_fonts()

    if FONT_MAIN is None:
        FONT_MAIN = pygame.font.Font(None, 40)
    if FONT_SMALL is None:
        FONT_SMALL = pygame.font.Font(None, 28)
    if FONT_BIG is None:
        FONT_BIG = pygame.font.Font(None, 60)

    particles = []
    running = True
    progress = 0.0
    start_time = pygame.time.get_ticks()

    while running and progress < 1.0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                running = False

        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / 5000.0, 1.0)

        screen.fill((10, 10, 25))

        title_text = "三国霸业"
        title_width = FONT_BIG.size(title_text)[0] + 100
        title_height = 80
        title_x = (screen_width - title_width) // 2
        title_y = screen_height // 2 - title_height

        scroll_surf = pygame.Surface((title_width, title_height), pygame.SRCALPHA)
        pygame.draw.rect(scroll_surf, (60, 30, 20, 200), (0, 0, title_width, title_height), border_radius=5)
        pygame.draw.rect(scroll_surf, (139, 69, 19), (0, 0, title_width, title_height), 3, border_radius=5)
        screen.blit(scroll_surf, (title_x, title_y))

        pattern_size = 40
        draw_chinese_pattern(screen, title_x - pattern_size - 10, title_y + 20, pattern_size, COLORS["accent_gold"])
        draw_chinese_pattern(screen, title_x + title_width + 10, title_y + 20, pattern_size, COLORS["accent_gold"])

        rotation = math.sin(pygame.time.get_ticks() * 0.002) * 2

        for offset in range(8, 0, -1):
            alpha = 100 - offset * 10
            glow_surf = FONT_BIG.render(title_text, True, (255, 215, 0))
            if glow_surf:
                glow_surf.set_alpha(alpha)
                glow_surf_rotated = pygame.transform.rotate(glow_surf, rotation)
                glow_surf_scaled = pygame.transform.scale(glow_surf_rotated, (title_width, title_height))
                screen.blit(glow_surf_scaled, (title_x - offset, title_y - offset))
                screen.blit(glow_surf_scaled, (title_x + offset, title_y + offset))

        title = FONT_BIG.render(title_text, True, (255, 215, 0))
        if title:
            title_rect = title.get_rect(center=(screen_width // 2, title_y + title_height // 2))
            shadow = FONT_BIG.render(title_text, True, (0, 0, 0))
            if shadow:
                screen.blit(shadow, (title_rect.x + 4, title_rect.y + 4))
            screen.blit(title, title_rect)

        subtitle_text = "群雄逐鹿，谁主沉浮"
        if FONT_MAIN:
            subtitle_surf = FONT_MAIN.render(subtitle_text, True, (255, 255, 255))
            if subtitle_surf:
                subtitle_rect = subtitle_surf.get_rect(center=(screen_width // 2, title_y + title_height + 30))
                for offset in range(3, 0, -1):
                    glow_surf = FONT_MAIN.render(subtitle_text, True, (255, 215, 0))
                    if glow_surf:
                        glow_surf.set_alpha(80)
                        screen.blit(glow_surf, (subtitle_rect.x - offset, subtitle_rect.y - offset))
                screen.blit(subtitle_surf, subtitle_rect)

        bar_width = 400
        bar_height = 20
        bar_x = (screen_width - bar_width) // 2
        bar_y = screen_height * 0.7

        pygame.draw.rect(screen, (40, 40, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        pygame.draw.rect(screen, (139, 69, 19), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)

        fill_width = int(bar_width * progress)
        if fill_width > 0:
            fill_surf = pygame.Surface((fill_width, bar_height), pygame.SRCALPHA)
            pygame.draw.rect(fill_surf, (255, 215, 0, 200), (0, 0, fill_width, bar_height), border_radius=10)
            screen.blit(fill_surf, (bar_x, bar_y))

        progress_text = f"起兵造势中... {int(progress * 100)}%"
        if FONT_SMALL:
            progress_surf = FONT_SMALL.render(progress_text, True, (255, 255, 255))
            if progress_surf:
                for offset in range(2, 0, -1):
                    glow_surf = FONT_SMALL.render(progress_text, True, (255, 215, 0))
                    if glow_surf:
                        glow_surf.set_alpha(80)
                        screen.blit(glow_surf, (screen_width // 2 - progress_surf.get_width() // 2 - offset, bar_y + bar_height + 20 - offset))
                screen.blit(progress_surf, (screen_width // 2 - progress_surf.get_width() // 2, bar_y + bar_height + 20))

        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))

        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)

        pygame.display.flip()
        clock.tick(60)
