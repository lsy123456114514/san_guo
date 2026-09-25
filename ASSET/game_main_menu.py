"""游戏主菜单模块 — 登录后主菜单系统

提供以下核心功能：
  · 三国主题主菜单界面（带下拉菜单分组导航）
  · 启动动画（科技感 + 三国风格）
  · 游戏设置菜单（分辨率、全屏、音效等）
  · 子模块动态调度（通过 importlib 按需加载 ASSET 下各子系统）
  · 小游戏中心、退出确认菜单
  · 鼠标拖尾、粒子系统、浮动文字等视觉特效
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 导入
# ═══════════════════════════════════════════════════════════════════════════════

import os
import sys
import subprocess
import platform
import pygame
import math
import random
import logging
from ASSET.fun_effects import PetSprite, FloatingParticles
from ASSET.game_data import data, save, draw_gradient_bg, ensure_defaults
from ASSET.secret_puzzle import (
    TriggerDetector,        # 卧龙密令·第6环 五行序列触发器
    KeySequenceDetector,    # 卧龙密令·第4环 WOLONG键盘拼字
    PasswordGate,           # 卧龙密令·第5环 前厅密码锁
    TrigramPuzzle,          # 卧龙密令·第7环 八阵图（成功后级联密室）
    puzzle_flags,
)

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

# ═══════════════════════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════════════════════

MENU_FPS = 60
STARTUP_DURATION_MS = 5000
MOUSE_TRAIL_MAX = 20
PARTICLE_MAX = 50
CLOUD_COUNT = 10
COMET_MAX = 5

# 全局变量（延迟初始化）
screen = None
clock = None

# ── 简易音效（文件缺失或音效关闭时静默降级）──
_SFX_CACHE = {}

def play_sfx(name):
    """播放 sounds/ 下的音效，受设置里的音效开关控制。"""
    try:
        if not data.get('settings', {}).get('sound', {}).get('enable', True):
            return
        snd = _SFX_CACHE.get(name)
        if snd is None:
            from ASSET.game_data import load_sound
            snd = load_sound(name)
            _SFX_CACHE[name] = snd
        if snd:
            snd.play()
    except Exception as _e:
        logger.debug("[异常静默] play_sfx %s: %s", name, _e)
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None

# ═══════════════════════════════════════════════════════════════════════════════
# 粒子/特效类
# ═══════════════════════════════════════════════════════════════════════════════

class MouseTrail:
    """鼠标跟随特效 — 在光标周围生成渐隐彩色圆形拖尾，营造动态光迹效果。"""
    def __init__(self, max_trails=MOUSE_TRAIL_MAX):
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
        for trail in self.trails:
            trail['size'] *= 0.95
            trail['alpha'] *= 0.9
        self.trails[:] = [trail for trail in self.trails if trail['alpha'] >= 5 and trail['size'] >= 1]
    
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
            except Exception as _e:
                logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

class DynamicLight:
    """动态光效 — 一个会脉冲缩放、微幅飘动的径向渐变光源。"""
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
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

# ═══════════════════════════════════════════════════════════════════════════════
# UI控件类
# ═══════════════════════════════════════════════════════════════════════════════

class ScrollableContainer:
    """可滚动容器 — 在有限区域内显示长列表，支持鼠标滚轮和拖拽滚动。"""
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
    """动画精灵 — 按帧序列播放动画，支持自动循环和降级渲染。"""
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
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

class FloatingText:
    """浮动文字 — 从指定位置缓缓上浮并淡出的文字标签，常用于提示信息。"""
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
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

class GlowingEffect:
    """发光效果 — 在指定矩形区域周围绘制脉冲式辉光。"""
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
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

class ParticleSystem:
    """粒子系统 — 管理多个 Particle 实例的生成、更新与回收，支持多种粒子类型。"""
    def __init__(self, max_particles=PARTICLE_MAX):
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
        alive = []
        for p in self.particles:
            try:
                p.update()
                p.x += math.sin(p.y * 0.02) * 0.5
                if p.life <= 0:
                    self.redundant_storage.append(p)
                    continue
                alive.append(p)
            except Exception as _e:
                logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        self.particles = alive

    def draw(self, surface):
        alive = []
        for p in self.particles:
            try:
                p.draw(surface)
                alive.append(p)
            except Exception as _e:
                logger.debug("[异常静默] particle draw %s: %s", type(_e).__name__, _e)
        self.particles = alive

class SafeSurface:
    """安全绘表面 — 对 pygame.Surface 操作做异常兜底，防止绘制错误导致崩溃。"""
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
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
            
    def draw_circle(self, color, center, radius, width=0):
        try:
            pygame.draw.circle(self.surface, color, center, radius, width)
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

# 平台检测
def is_android():
    """检测是否为安卓平台"""
    return 'ANDROID_DATA' in os.environ

def is_ios():
    """检测是否为iOS平台"""
    return 'IOS_DATA' in os.environ

def _get_physical_resolution():
    """获取屏幕真实物理像素分辨率，Windows 下通过 ctypes 绕过 DPI 缩放。"""
    if platform.system() == "Windows":
        try:
            import ctypes
            w = ctypes.windll.user32.GetSystemMetrics(0)
            h = ctypes.windll.user32.GetSystemMetrics(1)
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass
    try:
        sizes = pygame.display.get_desktop_sizes()
        if sizes:
            return sizes[0]
    except Exception:
        pass
    info = pygame.display.Info()
    return info.current_w, info.current_h

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
    """统一走 game_data.get_font（内置中文字体），保证主菜单与登录页同一套字体。"""
    global FONT_MAIN, FONT_SMALL, FONT_BIG

    if is_mobile():
        base_size, small_size, big_size = 48, 32, 72
    else:
        base_size, small_size, big_size = 40, 28, 60

    try:
        from ASSET.game_data import get_font
        FONT_MAIN = get_font(base_size)
        FONT_SMALL = get_font(small_size)
        FONT_BIG = get_font(big_size)
        logger.info("统一字体加载成功（game_data.get_font）")
        return
    except Exception as e:
        logger.error("统一字体加载失败，回退系统字体: %s", e)

    for font_name in get_font_list():
        try:
            if font_name is None:
                FONT_MAIN = pygame.font.Font(None, base_size)
                FONT_SMALL = pygame.font.Font(None, small_size)
                FONT_BIG = pygame.font.Font(None, big_size)
            else:
                FONT_MAIN = pygame.font.SysFont(font_name, base_size)
                FONT_SMALL = pygame.font.SysFont(font_name, small_size)
                FONT_BIG = pygame.font.SysFont(font_name, big_size)

            if test_font_renderable(FONT_MAIN, "中文") and test_font_renderable(FONT_MAIN, "测试中文ABC123"):
                logger.info(f"回退使用字体: {font_name if font_name else '默认字体'}")
                return
        except Exception as e:
            logger.error(f"字体 {font_name} 加载失败: {e}")
            continue

    logger.warning("使用 Pygame 默认字体")
    FONT_MAIN = pygame.font.Font(None, base_size)
    FONT_SMALL = pygame.font.Font(None, small_size)
    FONT_BIG = pygame.font.Font(None, big_size)


def repair_display():
    """子模块退出后的统一修复：重建失效的 screen，并探测字体。

    部分子模块退出时会调用 ``safe_exit``（pygame.quit + pygame.init），
    此后旧的 screen 与所有已缓存的 Font 对象全部作废——仅重建 screen
    不够，主菜单继续渲染会抛 ``Invalid font``。这里用一次探针渲染检测
    字体死活，死了就清空 game_data/font_manager 的字体缓存再 ``init_fonts()``。
    """
    global screen, FONT_MAIN, FONT_SMALL, FONT_BIG
    global _BG_CACHE, _BG_CACHE_KEY, _TITLE_CACHE, _SFX_CACHE

    # ── 0) pygame 子系统 ──
    # 部分旧模块退出时直接调用 pygame.quit()（而不是 safe_exit），
    # 字体/音频/显示子系统被整体拆除。此时旧 screen 是"僵尸"对象，
    # 探测可能假通过，继续往已释放的显存上画会触发 0xC0000005 硬崩。
    # 所以先看子系统状态：掉线就整体重建，并强制换新 screen、清空缓存。
    subsystem_down = False
    try:
        if not pygame.get_init() or not pygame.display.get_init():
            subsystem_down = True
            pygame.init()
            pygame.display.init()
    except Exception:
        subsystem_down = True
        try:
            pygame.init()
        except Exception:
            pass

    if subsystem_down:
        # 与 safe_exit 一致：丢弃全部缓存的 Font/Surface/Sound
        try:
            import ASSET.game_data as _gd
            if hasattr(_gd, "clear_caches"):
                _gd.clear_caches()
        except Exception:
            pass
        _BG_CACHE = None
        _BG_CACHE_KEY = None
        _TITLE_CACHE.clear()
        _SFX_CACHE.clear()
        logger.warning("[显示修复] pygame 子系统曾被整体退出，已重建并清空缓存")

    # ── 1) screen ──
    if subsystem_down:
        # 子系统重建前的旧 surface 一律作废，跳过探测直接换新
        need_screen = True
    else:
        need_screen = False
        try:
            if screen is None or not screen.get_enabled():
                raise ValueError("screen invalid")
            screen.get_size()
            # safe_exit 走过 display.quit+init+set_mode 后，系统当前 surface
            # 已经是新对象而我们的 screen 还是旧的 —— 探测会"假通过"，
            # 必须对比身份后换新
            _sys_surface = pygame.display.get_surface()
            if _sys_surface is not None and _sys_surface is not screen:
                raise ValueError("screen replaced by subsystem rebuild")
        except Exception:
            need_screen = True

    if need_screen:
        _BG_CACHE = None
        _BG_CACHE_KEY = None
        _TITLE_CACHE.clear()
        ensure_defaults()
        if is_android():
            sw, sh = _get_physical_resolution()
            screen = pygame.display.set_mode((sw, sh))
        elif data['settings']['graphics'].get('fullscreen', False):
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            try:
                w, h = map(int, data['settings']['graphics']['resolution'].split('x'))
                screen = pygame.display.set_mode((w, h))
            except Exception:
                screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("游戏主菜单")

    # ── 2) 字体探针 ──
    try:
        if FONT_MAIN is None:
            raise ValueError("font is None")
        FONT_MAIN.render("修", True, (255, 255, 255))
    except Exception:
        try:
            pygame.font.init()
        except Exception:
            pass
        try:
            import ASSET.game_data as _gd
            if hasattr(_gd, "_FONT_CACHE"):
                _gd._FONT_CACHE.clear()
        except Exception:
            pass
        try:
            from ASSET import font_manager as _fm
            if hasattr(_fm, "clear_font_cache"):
                _fm.clear_font_cache()
        except Exception:
            pass
        init_fonts()
        logger.warning("[显示修复] 字体已被子模块 quit 作废，缓存已清空并重建")

    pygame.event.clear()


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
    """基础粒子 — 具有位置、速度、颜色、大小和寿命属性的视觉粒子单元。"""
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
        color = self.color[:3]
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

class Button:
    """按钮控件 — 带悬停缩放、点击反馈、发光特效和粒子装饰的交互按钮。"""
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
        """检查鼠标悬停（进入瞬间播轻音）"""
        was = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_hovered and not was:
            play_sfx("hover.wav")

    def check_click(self, mouse_pos):
        """检查点击（先清冷却，避免悬停时 is_clicked 卡死导致点不动）。"""
        now = pygame.time.get_ticks()
        if self.is_clicked and now - self.click_timer > 200:
            self.is_clicked = False
        if self.is_hovered and pygame.mouse.get_pressed()[0] and not self.is_clicked:
            self.is_clicked = True
            self.click_timer = now
            return True
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
            color = self.hover_color
        elif self.is_clicked:
            # 按下态：常态色压暗
            color = tuple(max(0, int(c * 0.75)) for c in self.normal_color)
        else:
            color = self.normal_color

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
            text_surf = self.font.render(self.text, True, self.text_color)
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

        for p in self.particles:
            p.update()
            p.draw(surface)
        self.particles[:] = [p for p in self.particles if p.life > 0]

        for p in self.click_particles:
            p.update()
            p.draw(surface)
        self.click_particles[:] = [p for p in self.click_particles if p.life > 0]

class DropdownMenu:
    """下拉菜单 — 可展开/收起的选项列表，支持左右自适应弹出方向。"""
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
        self.scroll_index = 0  # 长列表滚动窗口起点

    def max_visible(self, screen_height):
        """屏幕内最多能显示的条目数"""
        item_height = min(40, screen_height * 0.06)
        fit = int((screen_height - self.rect.y - 20) // max(1, item_height))
        return max(3, min(len(self.items), fit))

    def scroll(self, direction, screen_height):
        """滚动长下拉列表（direction: -1 上 / 1 下）"""
        limit = max(0, len(self.items) - self.max_visible(screen_height))
        self.scroll_index = max(0, min(limit, self.scroll_index + direction))

    def update_items(self, screen_width, screen_height):
        """更新下拉菜单项的位置（长列表按窗口裁剪，防止溢出屏幕）"""
        self.dropdown_items = []
        if self.is_open:
            item_height = min(40, screen_height * 0.06)
            visible = self.max_visible(screen_height)
            window = self.items[self.scroll_index:self.scroll_index + visible]
            to_right = self.rect.x + self.rect.width * 2 < screen_width
            base_x = self.rect.x + self.rect.width + 10 if to_right else self.rect.x - self.rect.width - 10
            for i, (item_text, item_code) in enumerate(window):
                item_y = self.rect.y + i * item_height
                item_rect = pygame.Rect(base_x, item_y, self.rect.width, item_height)
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
            color = self.hover_color
        else:
            color = self.normal_color

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

clouds = []

for i in range(CLOUD_COUNT):
    clouds.append({
        'x': random.randint(-100, 900),
        'y': random.randint(-100, 700),
        'size': random.randint(30, 80),
        'alpha': random.randint(20, 50),
        'speed_x': random.uniform(-0.1, 0.1),
        'speed_y': random.uniform(-0.05, 0.05)
    })
# ═══════════════════════════════════════════════════════════════════════════════
# 菜单功能函数
# ═══════════════════════════════════════════════════════════════════════════════

_BG_CACHE = None
_BG_CACHE_KEY = None
_SPARK_SPRITES = {}
_RAINBOW_SPRITES = {}


def _rainbow_sprite(size, hue, alpha):
    """按（尺寸, 色相档, 透明度档）缓存彩虹粒子精灵，避免每帧新建 Surface。"""
    key = (size, hue // 12, alpha // 32)
    sprite = _RAINBOW_SPRITES.get(key)
    if sprite is None:
        h = (hue // 12) * 12 + 6
        r = int(127 + 127 * math.sin(h * math.pi / 180))
        g = int(127 + 127 * math.sin((h + 120) * math.pi / 180))
        b = int(127 + 127 * math.sin((h + 240) * math.pi / 180))
        sprite = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(sprite, (r, g, b, alpha), (size, size), size)
        if len(_RAINBOW_SPRITES) > 500:
            _RAINBOW_SPRITES.clear()
        _RAINBOW_SPRITES[key] = sprite
    return sprite


def _build_spark_sprite(size):
    """预渲染单颗星光的光点，避免每帧新建 SRCALPHA Surface。"""
    surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 215, 0, 255), (size * 2, size * 2), size * 2)
    return surf


def _build_cloud_sprite(cloud):
    """把一朵云的三层椭圆烘焙成 Surface（尺寸与透明度创建时就固定）。"""
    size = cloud['size']
    surf = pygame.Surface((size * 2, size), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (255, 215, 0, cloud['alpha']), (0, size // 4, size, size // 2))
    pygame.draw.ellipse(surf, (255, 215, 0, cloud['alpha'] // 2), (size // 2, 0, size, size // 2))
    pygame.draw.ellipse(surf, (255, 215, 0, cloud['alpha'] // 3), (size // 3, size // 3, size, size // 2))
    return surf


def _render_static_background(screen_width, screen_height):
    """渐变天空 + 装饰边框 + 中式纹样 + 印章 — 不随帧变化，只渲染一次并缓存。"""
    surf = pygame.Surface((screen_width, screen_height))
    for y in range(screen_height):
        ratio = y / max(screen_height, 1)
        r = int(40 * (1 - ratio) + 20 * ratio)
        g = int(20 * (1 - ratio) + 10 * ratio)
        b = int(30 * (1 - ratio) + 40 * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (screen_width, y))

    border_width = 15
    border_color = (139, 69, 19, 30)
    pygame.draw.rect(surf, border_color, (0, 0, screen_width, border_width))
    pygame.draw.rect(surf, border_color, (0, screen_height - border_width, screen_width, border_width))
    pygame.draw.rect(surf, border_color, (0, 0, border_width, screen_height))
    pygame.draw.rect(surf, border_color, (screen_width - border_width, 0, border_width, screen_height))

    inner_border = 30
    pygame.draw.rect(surf, border_color, (inner_border, inner_border, screen_width - inner_border * 2, 2))
    pygame.draw.rect(surf, border_color, (inner_border, screen_height - inner_border, screen_width - inner_border * 2, 2))
    pygame.draw.rect(surf, border_color, (inner_border, inner_border, 2, screen_height - inner_border * 2))
    pygame.draw.rect(surf, border_color, (screen_width - inner_border, inner_border, 2, screen_height - inner_border * 2))

    draw_chinese_pattern(surf, 50, 50, 40, (139, 69, 19))
    draw_chinese_pattern(surf, screen_width - 90, 50, 40, (139, 69, 19))
    draw_chinese_pattern(surf, 50, screen_height - 90, 40, (139, 69, 19))
    draw_chinese_pattern(surf, screen_width - 90, screen_height - 90, 40, (139, 69, 19))

    def draw_seal(target, x, y, size, text):
        try:
            pygame.draw.circle(target, (200, 80, 80, 120), (x, y), size // 2)
            pygame.draw.circle(target, (200, 80, 80, 150), (x, y), size // 2 - 5, 3)
            if FONT_SMALL:
                text_surf = FONT_SMALL.render(text, True, (200, 80, 80, 180))
                if text_surf:
                    text_rect = text_surf.get_rect(center=(x, y))
                    target.blit(text_surf, text_rect)
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

    draw_seal(surf, screen_width - 100, 100, 60, "三国")
    draw_seal(surf, 100, screen_height - 100, 60, "霸业")
    return surf


def draw_three_kingdoms_background(surface, screen_width, screen_height):
    """绘制三国主题背景 — 静态层走缓存 blit，只有云与星光逐帧绘制。"""
    global _BG_CACHE, _BG_CACHE_KEY
    try:
        key = (screen_width, screen_height, id(FONT_SMALL))
        if key != _BG_CACHE_KEY:
            _BG_CACHE = _render_static_background(screen_width, screen_height)
            _BG_CACHE_KEY = key
        surface.blit(_BG_CACHE, (0, 0))

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

            sprite = cloud.get('sprite')
            if sprite is None:
                sprite = cloud['sprite'] = _build_cloud_sprite(cloud)
            surface.blit(sprite, (cloud['x'] - cloud['size'], cloud['y']))

        for i in range(6):
            x = random.randint(0, screen_width)
            y = random.randint(0, screen_height)
            size = random.randint(1, 2)
            alpha = random.randint(20, 40)
            sprite = _SPARK_SPRITES.get(size)
            if sprite is None:
                sprite = _SPARK_SPRITES[size] = _build_spark_sprite(size)
            sprite.set_alpha(alpha)
            surface.blit(sprite, (x - size * 2, y - size * 2))
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
    except Exception as _e:
        logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

_TITLE_CACHE = {}


def _render_title_block(text, y_pos, screen_width):
    """把标题横幅（底板+纹样+辉光字+下划线）整体渲染进一张缓存图。"""
    title_width = FONT_BIG.size(text)[0] + 100
    title_height = 80
    title_x = (screen_width - title_width) // 2
    title_y = y_pos - 20
    block_height = int(y_pos + 70)
    block = pygame.Surface((screen_width, block_height), pygame.SRCALPHA)

    scroll_surf = pygame.Surface((title_width, title_height), pygame.SRCALPHA)
    pygame.draw.rect(scroll_surf, (60, 30, 20, 200), (0, 0, title_width, title_height), border_radius=5)
    pygame.draw.rect(scroll_surf, (139, 69, 19), (0, 0, title_width, title_height), 3, border_radius=5)
    block.blit(scroll_surf, (title_x, title_y))

    pattern_size = 40
    draw_chinese_pattern(block, title_x - pattern_size - 10, title_y + 20, pattern_size, COLORS["accent_gold"])
    draw_chinese_pattern(block, title_x + title_width + 10, title_y + 20, pattern_size, COLORS["accent_gold"])

    for offset in range(8, 0, -1):
        alpha = 60 - offset * 7
        glow_surf = FONT_BIG.render(text, True, (255, 215, 0))
        if glow_surf:
            glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
            glow_surf.set_alpha(alpha)
            block.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
            block.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))

    title = FONT_BIG.render(text, True, (255, 215, 0))
    if title:
        title_rect = title.get_rect(center=(screen_width // 2, y_pos))
        shadow = FONT_BIG.render(text, True, (0, 0, 0))
        if shadow:
            block.blit(shadow, (title_rect.x + 4, title_rect.y + 4))
        block.blit(title, title_rect)

    line_y = y_pos + 50
    line_color = (139, 69, 19)
    pygame.draw.line(block, line_color, (screen_width // 2 - 200, line_y), (screen_width // 2 - 80, line_y), 3)
    pygame.draw.line(block, line_color, (screen_width // 2 - 200, line_y - 5), (screen_width // 2 - 200, line_y + 5), 3)
    pygame.draw.line(block, line_color, (screen_width // 2 - 80, line_y - 5), (screen_width // 2 - 80, line_y + 5), 3)
    pygame.draw.line(block, line_color, (screen_width // 2 + 80, line_y), (screen_width // 2 + 200, line_y), 3)
    pygame.draw.line(block, line_color, (screen_width // 2 + 80, line_y - 5), (screen_width // 2 + 80, line_y + 5), 3)
    pygame.draw.line(block, line_color, (screen_width // 2 + 200, line_y - 5), (screen_width // 2 + 200, line_y + 5), 3)
    pygame.draw.circle(block, COLORS["accent_gold"], (screen_width // 2, line_y), 10)
    pygame.draw.circle(block, (139, 69, 19), (screen_width // 2, line_y), 6)
    return block


def draw_three_kingdoms_title(surface, text, y_pos, screen_width):
    """绘制三国风格标题 — 静态横幅走缓存，避免每帧十几次字体渲染。"""
    try:
        if FONT_BIG is None:
            return
        key = (text, y_pos, screen_width, id(FONT_BIG))
        block = _TITLE_CACHE.get(key)
        if block is None:
            block = _render_title_block(text, y_pos, screen_width)
            if len(_TITLE_CACHE) > 4:
                _TITLE_CACHE.clear()
            _TITLE_CACHE[key] = block
        surface.blit(block, (0, 0))
    except Exception as _e:
        logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

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
    except Exception as _e:
        logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

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
    except Exception as _e:
        logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

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
    except Exception as _e:
        logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

def clear():
    """清屏"""
    if screen:
        screen.fill(COLORS["bg_dark"])

def run_module(module_file):
    """动态加载并运行 ASSET 目录下的子模块，调用其 main() 函数；退出后重建 screen。"""
    global screen
    try:
        # 文件名去 .py 即模块名，统一动态导入，避免冗长的 if/elif 分支
        module_name = module_file[:-3] if module_file.endswith('.py') else module_file
        import importlib
        mod = importlib.import_module("ASSET." + module_name)
        if hasattr(mod, 'main'):
            mod.main()

        # 子模块退出后可能调用了 safe_exit（pygame.quit + pygame.init），
        # 统一修复 screen 与被作废的字体缓存
        repair_display()

    except Exception as e:
        logger.error("打开「%s」时出错了：%s", module_file, e)
        import traceback
        logger.error(traceback.format_exc())
        # 模块异常退出同样可能拆过 pygame/字体（safe_exit、模块内部 quit），
        # 不修复的话主菜单会黑屏只剩按钮边框，之后点击也像“未响应”。
        try:
            repair_display()
        except Exception as e2:
            logger.error("子模块异常后修复显示失败：%s", e2)
        # 玩家面前只说人话，技术细节留在 game.log
        try:
            show_message("这个功能一时没能打开，详情已记入日志")
        except Exception as e2:
            logger.error("提示框绘制失败：%s", e2)
            pygame.time.wait(800)

def mini_games_menu():
    """小游戏中心菜单 — 展示所有小游戏入口按钮并处理启动。"""
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
        ("三国知识问答", "quiz_system.py"),
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
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])

        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))

        for p in particles[:]:
            p.update()
            p.draw(screen)

        draw_title(screen, "小游戏中心", screen_height * 0.12, screen_width)

        mouse_pos = pygame.mouse.get_pos()

        for btn, code in mini_games_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn, code in mini_games_buttons:
                    if btn.rect.collidepoint(event.pos):
                        if code == "back":
                            running = False
                        else:
                            run_module(code)
                            if update_achievement_progress:
                                update_achievement_progress("mini_game_played")

        clock.tick(MENU_FPS)

# ═══════════════════════════════════════════════════════════════════════════════
# 模块调度
# ═══════════════════════════════════════════════════════════════════════════════

# ============ 模块路由表 ============
# 所有下拉菜单项统一在此注册，避免冗长的 if/elif 分支。
# 新增功能时只需在此登记一行，再在下方菜单项列表中加入对应条目即可。
MODULE_ROUTES = {
    "1": "pvp_p2p.py",              # PVP联机
    "2": "game_map_pygame.py",      # 游戏地图（2D）
    "28": "game_map_3d.py",         # 3D地图
    "29": "hero_recruitment.py",    # 武将招募
    "31": "newbie_guide.py",        # 新手引导
    "32": "background_story.py",    # 背景故事
    "3": "battle_system.py",        # 副本挑战
    "7": "hero_warehouse.py",       # 武将仓库
    "8": "activity_system.py",      # 活动中心
    "12": "tech_tree.py",           # 科技树系统
    "21": "building_system.py",     # 建筑系统
    "22": "talent_system.py",       # 天赋系统
    "11": "achievement_system.py",  # 成就系统
    "13": "ranking_system.py",      # 排行榜系统
    "14": "daily_checkin.py",       # 每日签到
    "6": "shop_system.py",          # 游戏商城
    "16": "social_system.py",       # 社交系统
    "17": "equipment_system.py",    # 装备系统
    "18": "trading_system.py",      # 交易系统
    "19": "pet_system.py",          # 宠物系统
    "30": "fashion_system.py",      # 时装系统
    "20": "quest_system.py",        # 任务系统（含每日任务标签）
    "23": "fishing_system.py",      # 钓鱼系统
    "24": "alchemy_system.py",      # 炼金系统
    "25": "ai_system.py",           # 游戏内AI
    "26": "faq_system.py",          # 疑难解答
    "27": "weather_system.py",      # 天气系统
    # ===== 以下为补齐的菜单项（此前菜单中可见但点击无响应）=====
    "33": "racing_mode.py",             # 竞速模式（新增玩法）
    "34": "game_map_3d.py",             # 生存模式（3D地图默认生存模式）
    "35": "pet_system.py",              # 宠物进化
    "36": "quest_system.py",            # 每日任务
    "37": "limited_time_events.py",     # 限时活动
    "38": "pet_arena.py",               # 宠物竞技场
    "39": "lucky_wheel.py",             # 幸运转盘
    "40": "escort_system.py",           # 镖局押运（新增玩法）
}

# 需要特殊处理逻辑的菜单项（不走 run_module 动态导入）
SPECIAL_HANDLERS = {
    "10": mini_games_menu,   # 小游戏中心
}

def custom_resolution_dialog(settings_lines, current_w, current_h):
    """打开一个仿设置界面的 tkinter 窗口，让玩家拖动窗口边缘调整分辨率。

    该窗口在视觉上尽量贴近 pygame 的设置界面（深色背景、金色标题、
    相同的设置项），玩家拖动窗口边缘改变尺寸后点击「应用」或「确定」，
    函数会读取窗口的客户区大小并返回，交由调用方应用到真正的 pygame 屏幕。

    Args:
        settings_lines: 当前设置项的展示文本列表（用于仿制界面）。
        current_w: 当前屏幕宽度，用作窗口初始尺寸。
        current_h: 当前屏幕高度，用作窗口初始尺寸。

    Returns:
        ``(width, height)`` 元组；若玩家取消或 tkinter 不可用则返回 ``None``。
    """
    try:
        import tkinter as tk
    except Exception as _e:
        logger.info("[设置] tkinter 不可用，无法使用自定义分辨率：%s", _e)
        return None

    # 隐藏 pygame 窗口，营造“界面被替换”的视觉效果
    try:
        pygame.display.iconify()
    except Exception as _e:
        logger.debug("[设置] iconify 失败: %s", _e)

    def _restore_window():
        """还原被最小化的 pygame 窗口（Windows 下用 ShowWindow(SW_RESTORE)）。"""
        try:
            if sys.platform == "win32":
                import ctypes
                hwnd = pygame.display.get_wm_info().get("window")
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 9)       # SW_RESTORE
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as _e:
            logger.debug("[设置] 还原 pygame 窗口失败: %s", _e)

    result = {"size": None}

    try:
        root = tk.Tk()
    except Exception as _e:
        logger.info("[设置] 创建 tkinter 窗口失败：%s", _e)
        _restore_window()
        return None

    root.title("游戏设置")
    root.configure(bg="#141428")
    root.minsize(480, 360)
    root.resizable(True, True)
    try:
        root.geometry(f"{current_w}x{current_h}")
        root.update_idletasks()
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        pos_x = max(0, (screen_w - current_w) // 2)
        pos_y = max(0, (screen_h - current_h) // 2)
        root.geometry(f"{current_w}x{current_h}+{pos_x}+{pos_y}")
    except Exception as _e:
        logger.debug("[设置] 设置 tkinter 几何尺寸失败: %s", _e)

    font_title = ("Microsoft YaHei", 20, "bold")
    font_text = ("Microsoft YaHei", 12)
    font_btn = ("Microsoft YaHei", 12, "bold")

    tk.Label(root, text="游戏设置", fg="#FFD700", bg="#141428",
             font=font_title).pack(pady=(22, 6))
    tk.Label(root, text="拖动窗口边缘即可调整分辨率", fg="#B0B0C8", bg="#141428",
             font=font_text).pack(pady=(0, 10))

    size_var = tk.StringVar()

    def refresh_size(_event=None):
        try:
            size_var.set(f"当前分辨率：{root.winfo_width()} x {root.winfo_height()}")
        except Exception:
            pass

    tk.Label(root, textvariable=size_var, fg="#FFFFFF", bg="#141428",
             font=font_text).pack(pady=(0, 12))
    root.bind("<Configure>", refresh_size)

    # 仿制设置项
    for line in settings_lines:
        tk.Label(root, text=line, fg="#FFFFFF", bg="#20203A", font=font_text,
                 width=30, pady=8).pack(pady=3)

    btn_frame = tk.Frame(root, bg="#141428")
    btn_frame.pack(side="bottom", pady=18)

    def confirm():
        try:
            result["size"] = (root.winfo_width(), root.winfo_height())
        except Exception:
            result["size"] = None
        root.destroy()

    def cancel():
        result["size"] = None
        root.destroy()

    tk.Button(btn_frame, text="应用", command=confirm, bg="#4A8CC7", fg="white",
              font=font_btn, width=8, relief="flat").pack(side="left", padx=8)
    tk.Button(btn_frame, text="确定", command=confirm, bg="#50B450", fg="white",
              font=font_btn, width=8, relief="flat").pack(side="left", padx=8)
    tk.Button(btn_frame, text="取消", command=cancel, bg="#C85050", fg="white",
              font=font_btn, width=8, relief="flat").pack(side="left", padx=8)

    try:
        root.update()
    except Exception:
        pass
    refresh_size()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass

    try:
        root.mainloop()
    except Exception as _e:
        logger.info("[设置] tkinter 主循环异常：%s", _e)

    _restore_window()
    return result["size"]

def setting_menu():
    """游戏设置菜单 — 分辨率、全屏、地图容量、音效等选项的循环切换与即时生效。"""

    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    except Exception:
        pass

    particles = []

    def apply_display():
        """立即把设置里的分辨率/全屏应用到窗口（原先只保存、不生效）。

        注意：不能用 pygame.display.Info().current_w 做上限——窗口化时它可能返回
        当前窗口尺寸，导致“分辨率调越大、窗口反而越小”的正反馈。这里用显示器
        的物理分辨率 get_desktop_sizes() 作为上限。
        """
        global screen
        fullscreen = data['settings']['graphics'].get('fullscreen', False)
        try:
            if fullscreen:
                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                w, h = map(int, data['settings']['graphics']['resolution'].split('x'))
                try:
                    desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
                except Exception:
                    desktop_w, desktop_h = 1920, 1080
                w = max(320, min(w, desktop_w))
                h = max(240, min(h, desktop_h))
                screen = pygame.display.set_mode((w, h))
            pygame.display.set_caption("游戏设置")
        except Exception as _e:
            logger.debug("[设置] 应用分辨率失败: %s", _e)

    def get_settings_text():
        if 'fullscreen' not in data['settings']['graphics']:
            data['settings']['graphics']['fullscreen'] = False
            save()

        return [
            f"分辨率：{data['settings']['graphics']['resolution']}",
            f"全屏模式：{'开' if data['settings']['graphics']['fullscreen'] else '关'}",
            f"地图最大元素：{data['settings']['map']['max_locations']}",
            f"音效：{'开' if data['settings']['sound']['enable'] else '关'}"
        ]

    running = True
    setting_buttons = []
    settings_sig = None  # 上次构建按钮时的（文本列表, 宽高）签名
    while running:
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        button_width = min(400, screen_width * 0.5)
        button_height = min(56, screen_height * 0.075)
        button_spacing = min(18, screen_height * 0.022)

        setting_items = get_settings_text() + ["应用", "确定", "返回主菜单"]
        total_height = len(setting_items) * button_height + (len(setting_items) - 1) * button_spacing
        start_y = max(screen_height * 0.18, (screen_height - total_height) / 2)

        # 仅当设置文本或布局变化时重建按钮 — 每帧重建会重置 hover 动画
        sig = (tuple(setting_items), screen_width, screen_height)
        if sig != settings_sig:
            settings_sig = sig
            setting_buttons = []
            for i, text in enumerate(setting_items):
                x = (screen_width - button_width) // 2
                y = start_y + i * (button_height + button_spacing)
                if text == "应用":
                    normal_color = COLORS["accent_blue"]
                elif text == "确定":
                    normal_color = COLORS["accent_green"]
                elif text == "返回主菜单":
                    normal_color = (100, 100, 150)
                else:
                    normal_color = COLORS["accent_blue"]
                btn = Button(text, x, y, button_width, button_height, FONT_SMALL,
                             normal_color=normal_color)
                setting_buttons.append(btn)

        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])

        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))

        for p in particles[:]:
            p.update()
            p.draw(screen)

        draw_title(screen, "游戏设置", screen_height * 0.12, screen_width)

        mouse_pos = pygame.mouse.get_pos()

        for btn in setting_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, btn in enumerate(setting_buttons):
                    if btn.rect.collidepoint(event.pos):
                        if i == 0:
                            resolutions = ["600x500", "800x600", "1024x768", "1280x720",
                                           "1366x768", "1920x1080", "自定义"]
                            current = data['settings']['graphics']['resolution']
                            try:
                                idx = resolutions.index(current)
                                next_idx = (idx + 1) % len(resolutions)
                            except ValueError:
                                next_idx = 0
                            chosen = resolutions[next_idx]
                            if chosen == "自定义":
                                size = custom_resolution_dialog(
                                    get_settings_text(),
                                    screen.get_width(), screen.get_height()
                                )
                                if size:
                                    cw, ch = size
                                    try:
                                        desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
                                    except Exception:
                                        desktop_w, desktop_h = 1920, 1080
                                    cw = max(320, min(cw, desktop_w))
                                    ch = max(240, min(ch, desktop_h))
                                    data['settings']['graphics']['resolution'] = f"{cw}x{ch}"
                                    save()
                                    apply_display()
                                    show_message(f"已应用自定义分辨率 {cw}x{ch}")
                                else:
                                    show_message("已取消自定义分辨率")
                            else:
                                data['settings']['graphics']['resolution'] = chosen
                                save()
                                apply_display()
                        elif i == 1:
                            data['settings']['graphics']['fullscreen'] = not data['settings']['graphics']['fullscreen']
                            save()
                            apply_display()
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
                            apply_display()
                            save()
                            show_message("设置已应用")
                        elif i == 5:
                            apply_display()
                            save()
                            running = False
                        elif i == 6:
                            running = False

        clock.tick(MENU_FPS)

def input_save_name(screen, font_title, font_input):
    """输入存档名称。Esc/取消/点面板外返回 None，回车确认。"""
    w, h = screen.get_width(), screen.get_height()
    panel = pygame.Rect(w // 4, h // 2 - 80, w // 2, 165)
    input_box = pygame.Rect(panel.x + 20, panel.y + 55, panel.width - 40, 44)
    cancel_rect = pygame.Rect(panel.right - 100, panel.bottom - 38, 80, 28)
    text = ""
    max_len = 16
    active = True
    clock = pygame.time.Clock()
    try:
        pygame.key.set_text_input_enabled(True)
    except AttributeError:
        pass

    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif event.unicode and event.unicode.isprintable() and len(text) < max_len:
                    text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cancel_rect.collidepoint(event.pos):
                    return None
                if not panel.collidepoint(event.pos):
                    return None

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40, 40, 70), panel, border_radius=10)
        pygame.draw.rect(screen, (139, 69, 19), panel, 2, border_radius=10)
        pygame.draw.rect(screen, (255, 215, 0), panel, 1, border_radius=10)

        if font_title:
            title = font_title.render("给这次征程起个名字", True, (255, 215, 0))
            if title:
                screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 26)))

        pygame.draw.rect(screen, (25, 25, 45), input_box, border_radius=6)
        pygame.draw.rect(screen, (140, 140, 190), input_box, 2, border_radius=6)
        if font_input:
            shown = text if text else "例：赤壁之战"
            color = (255, 255, 255) if text else (140, 140, 160)
            txt_surface = font_input.render(shown, True, color)
            if txt_surface:
                clip = txt_surface.get_rect(midleft=(input_box.x + 8, input_box.centery))
                screen.blit(txt_surface, clip)
            # 光标闪烁
            if text and (pygame.time.get_ticks() // 400) % 2 == 0:
                cx = clip.right + 3
                pygame.draw.line(screen, (255, 215, 0),
                                 (cx, input_box.y + 8), (cx, input_box.bottom - 8), 2)
            # 字数提示（独立一行，不与按钮挤在一起）
            counter = font_input.render(f"{len(text)}/{max_len}", True, (150, 150, 170))
            if counter:
                screen.blit(counter, counter.get_rect(right=input_box.right - 6,
                                                      centery=input_box.centery))
            hint = font_input.render("回车确认 · Esc取消", True, (160, 160, 180))
            if hint:
                screen.blit(hint, hint.get_rect(midleft=(panel.x + 20, panel.bottom - 24)))

        pygame.draw.rect(screen, (90, 50, 50), cancel_rect, border_radius=6)
        pygame.draw.rect(screen, (180, 100, 100), cancel_rect, 1, border_radius=6)
        if font_input:
            label = font_input.render("取消", True, (255, 220, 220))
            if label:
                screen.blit(label, label.get_rect(center=cancel_rect.center))

        pygame.display.flip()
        clock.tick(30)

    return text if text else "未命名征程"

def show_message(message):
    """显示消息 — 带面板的 Toast，点击/按键可提前关闭。"""
    if not (FONT_MAIN and screen):
        return
    w, h = screen.get_width(), screen.get_height()
    deadline = pygame.time.get_ticks() + 1500
    closed = False
    while pygame.time.get_ticks() < deadline and not closed:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.event.post(event)
                return
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                closed = True
                break
        if closed:
            break

        remaining = deadline - pygame.time.get_ticks()
        # 最后 400ms 淡出
        alpha = min(255, int(remaining / 400 * 255)) if remaining < 400 else 255

        try:
            msg_surface = FONT_MAIN.render(message, True, (255, 240, 210))
        except Exception as _e:
            # 字体被子模块 quit 作废时不静默：记日志并直接结束提示
            logger.error("提示框字体渲染失败：%s: %s", type(_e).__name__, _e)
            break
        if msg_surface:
            panel_w = msg_surface.get_width() + 60
            panel_h = msg_surface.get_height() + 36
            px, py = w // 2 - panel_w // 2, h // 2 - panel_h // 2

            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((30, 26, 20, min(230, alpha)))
            screen.blit(panel, (px, py))
            pygame.draw.rect(screen, (255, 215, 0), (px, py, panel_w, panel_h), 2, border_radius=10)

            msg_surface.set_alpha(alpha)
            screen.blit(msg_surface, msg_surface.get_rect(center=(w // 2, h // 2)))
            pygame.display.flip()
        pygame.time.wait(30)

# ═══════════════════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """主菜单主循环 — 创建窗口、初始化字体、构建下拉菜单和按钮、渲染背景特效并处理用户交互。"""
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG

    if not pygame.get_init():
        pygame.init()

    init_fonts()

    if FONT_MAIN is None or FONT_SMALL is None or FONT_BIG is None:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 28)
        FONT_BIG = pygame.font.Font(None, 60)

    ensure_defaults()
    if 'fullscreen' not in data['settings']['graphics']:
        data['settings']['graphics']['fullscreen'] = False
        save()

    resolution = data['settings']['graphics']['resolution']
    fullscreen = data['settings']['graphics']['fullscreen']

    if is_android():
        screen_width, screen_height = _get_physical_resolution()
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
                screen_width, screen_height = _get_physical_resolution()
                screen = pygame.display.set_mode((screen_width, screen_height))

    pygame.display.set_caption("游戏主菜单")
    clock = pygame.time.Clock()

    if "tutorial_completed" not in data or not data["tutorial_completed"]:
        try:
            from ASSET.newbie_guide import main as guide_main
            guide_main()
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

    def build_menu():
        """构建主菜单元素 — 统一几何参数，小分辨率下自动压缩防溢出。"""
        bw = min(300, screen_width * 0.35)
        bh = min(55, screen_height * 0.07)
        bs = min(15, screen_height * 0.025)
        n = 8  # 行数
        # 8 行总高不能超出可用区域（顶部留 28%，底部留 20px）
        available = screen_height * 0.80 - 20
        total = n * bh + (n - 1) * bs
        if total > available:
            scale = available / total
            bh = max(28, bh * scale)
            bs = max(4, bs * scale)
            total = n * bh + (n - 1) * bs
        sy = min(screen_height * 0.28, screen_height - total - 20)
        x = (screen_width - bw) // 2

        elements = []
        drop_items = [
            ("游戏核心", game_core_items),
            ("游戏系统", game_system_items),
            ("社交与排行", social_items),
            ("其他功能", other_items),
        ]
        for i, (label, items) in enumerate(drop_items):
            elements.append(("dropdown", DropdownMenu(
                label, x, sy + i * (bh + bs), bw, bh, FONT_SMALL, items)))

        plain_buttons = [
            ("保存进度", "4", (100, 100, 150)),
            ("读取存档", "15", (100, 100, 150)),
            ("游戏设置", "5", (100, 100, 150)),
            ("退出游戏", "9", COLORS["accent_red"]),
        ]
        for j, (label, code, color) in enumerate(plain_buttons):
            btn = Button(label, x, sy + (4 + j) * (bh + bs), bw, bh,
                         FONT_SMALL, normal_color=color)
            elements.append(("button", (btn, code)))
        return elements

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
        ("镖局押运", "40"),
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
        ("限时活动", "37"),
        ("幸运转盘", "39")
    ]

    menu_elements = build_menu()
    focus_idx = [0]  # 键盘焦点索引（list 包一层便于闭包内修改）
    puzzle_trigger = TriggerDetector()  # 卧龙密令·第6环：五行序列触发器
    key_seq = KeySequenceDetector()     # 卧龙密令·第4环：WOLONG键盘拼字

    # 一键自动测试驱动（SAN_GUO_AUTOTEST=1 时由根目录 auto_test.py 注入）
    auto_driver = None
    if os.environ.get("SAN_GUO_AUTOTEST") == "1":
        try:
            from auto_test import AutoTestDriver
            auto_driver = AutoTestDriver()
            logger.info("[自动测试] 驱动已装载，将模拟点击各模块进出")
        except Exception as _e:
            logger.error("[自动测试] 驱动装载失败: %s", _e)

    def restore_screen():
        """子彩蛋/子模块退出后修复显示，并重建菜单元素。

        子模块可能调用 safe_exit 导致 pygame.quit：screen 与所有缓存字体
        都会作废。repair_display 负责修复本身；但旧菜单按钮对象仍握着
        死字体引用（无论修复发生在 run_module 内还是这里），所以每次
        退出子模块后都无条件 build_menu() 重建一遍——开销可忽略。
        """
        nonlocal screen_width, screen_height
        repair_display()
        try:
            screen_width, screen_height = screen.get_size()
        except Exception:
            pass
        menu_elements[:] = build_menu()

    def activate_code(code):
        """菜单项激活 — 鼠标点击与键盘 Enter 共用。"""
        nonlocal running, screen_width, screen_height
        global screen
        play_sfx("click.wav")

        # 卧龙密令·第6环：检测五行序列（水→火→木→金→土）
        try:
            if puzzle_trigger.on_menu_click(code, pygame.time.get_ticks()):
                flags = puzzle_flags()
                if not flags.get("gate_passed"):
                    # 五行之力被前厅之门挡住（第5环未过）
                    play_sfx("deny.wav")
                    show_message("五行之力涌动，却被一道无形之门挡住……（残卷二曰：先开前厅）")
                    return
                if flags.get("completed"):
                    play_sfx("confirm.wav")
                    show_message("密室已空，卧龙之谜尽数解开。")
                    return
                play_sfx("confirm.wav")
                # 第7环八阵图，成功后其内部级联第8-10环密室
                TrigramPuzzle(screen).run()
                restore_screen()
                return
            if puzzle_trigger.progress > 0:
                # 序列进行中：静默吞掉该次点击，不打开任何界面
                return
        except Exception as _e:
            logger.debug("[卧龙密令] 触发器异常: %s", _e)
        if code == "4":
            username = data.get("username", "player")
            save_name = input_save_name(screen, FONT_MAIN, FONT_SMALL)
            if save_name:
                from ASSET.login_system import save_user_progress, save_game
                save_user_progress(username, data)
                success, message = save_game(username, save_name, data)
                if success:
                    play_sfx("confirm.wav")
                    show_message("存好了，主公可随时再战。")
                else:
                    play_sfx("deny.wav")
                    show_message(f"这次没存上：{message}")
        elif code == "15":
            username = data.get("username", "player")
            from ASSET.login_system import show_save_manager
            save_result = show_save_manager(screen, FONT_BIG, FONT_MAIN, FONT_SMALL, username, data)
            if save_result:
                data.clear()
                data.update(save_result)
                ensure_defaults()
                save()
                show_message("读档成功，欢迎回来。")
        elif code == "5":
            old_width = screen_width
            old_height = screen_height
            setting_menu()
            screen_width = screen.get_width()
            screen_height = screen.get_height()
            if screen_width != old_width or screen_height != old_height:
                menu_elements[:] = build_menu()
        elif code == "9":
            exit_choice = show_exit_menu()
            if exit_choice == "exit_game":
                save()
                play_sfx("confirm.wav")
                show_message("青山不改，绿水长流，后会有期。")
                running = False
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
                running = False
        elif code in SPECIAL_HANDLERS:
            SPECIAL_HANDLERS[code]()
            restore_screen()
        elif code in MODULE_ROUTES:
            run_module(MODULE_ROUTES[code])
            restore_screen()

    if auto_driver is not None:
        auto_driver.bind(menu_elements, activate_code)

    particles = []

    moving_elements = []
    
    
    
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

        # 一键自动测试：每帧驱动一步（移动光标→展开菜单→点击模块）
        if auto_driver is not None:
            try:
                auto_driver.step()
            except Exception as _e:
                logger.error("[自动测试] 驱动异常: %s", _e)

        draw_three_kingdoms_background(screen, screen_width, screen_height)
        
        if random.random() < 0.005 and len(comet_trails) < COMET_MAX:
            hue = random.randint(0, 360)
            r = int(127 + 127 * math.sin(hue * math.pi / 180))
            g = int(127 + 127 * math.sin((hue + 120) * math.pi / 180))
            b = int(127 + 127 * math.sin((hue + 240) * math.pi / 180))
            dot = pygame.Surface((3, 3), pygame.SRCALPHA)
            pygame.draw.circle(dot, (r, g, b, 255), (1, 1), 1)
            comet_trails.append({
                'x': screen_width + 50,
                'y': random.randint(0, screen_height // 2),
                'speed': random.uniform(3.0, 6.0),
                'length': random.randint(80, 150),
                'alpha': random.randint(100, 200),
                'hue': hue,
                'dot': dot
            })
        
        for comet in comet_trails:
            comet['x'] -= comet['speed']
            try:
                dot = comet['dot']
                for i in range(int(comet['length'])):
                    alpha = int(comet['alpha'] * (1 - i / comet['length']))
                    x_pos = comet['x'] + i
                    y_pos = comet['y'] + math.sin(current_time * 0.05 + i * 0.1) * 3
                    if 0 <= x_pos <= screen_width and 0 <= y_pos <= screen_height:
                        try:
                            dot.set_alpha(alpha)
                            screen.blit(dot, (int(x_pos), int(y_pos)))
                        except Exception as _e:
                            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
            except Exception as _e:
                logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        
        comet_trails[:] = [comet for comet in comet_trails if comet['x'] >= -comet['length']]
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
        
        for rp in rainbow_particles:
            rp['y'] -= rp['speed']
            rp['x'] += math.sin(current_time * 0.02 + rp['hue'] * 0.1) * 0.5
            rp['hue'] = (rp['hue'] + 1) % 360
            try:
                sprite = _rainbow_sprite(int(rp['size']), rp['hue'], rp['alpha'])
                screen.blit(sprite, (int(rp['x'] - rp['size']), int(rp['y'] - rp['size'])))
            except Exception as _e:
                logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

        rainbow_particles[:] = [rp for rp in rainbow_particles if rp['y'] >= -20]
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
                surf = decor.get('sprite')
                if surf is None:
                    size = int(decor['size'])
                    if size <= 0:
                        size = 5
                    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    decor_alpha = max(1, min(255, decor['alpha']))
                    if decor['type'] == 'star':
                        pygame.draw.polygon(surf, (255, 215, 0, decor_alpha), 
                                          [(size, 0), (size + size//2, size), (size, size * 2), 
                                           (size - size//2, size)])
                    elif decor['type'] == 'diamond':
                        pygame.draw.polygon(surf, (255, 215, 0, decor_alpha),
                                          [(size, 0), (size * 2, size), (size, size * 2), (0, size)])
                    else:
                        pygame.draw.circle(surf, (255, 215, 0, decor_alpha), (size, size), size)
                    decor['sprite'] = surf
                screen.blit(surf, (int(decor['x'] - decor['size']), int(decor['y'] - decor['size'])))
            except Exception as _e:
                logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

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

        for element in moving_elements:
            element['x'] += element['speed_x']
            element['y'] += element['speed_y']
            element['life'] -= 1

            if element['life'] > 0:
                try:
                    surf = element.get('sprite')
                    if surf is None:
                        w = int(element['size'])
                        h = int(element['size'] // 2)
                        surf = pygame.Surface((w, h), pygame.SRCALPHA)
                        pygame.draw.ellipse(surf, (255, 215, 0, element['alpha']), (0, 0, w, h))
                        element['sprite'] = surf
                    screen.blit(surf, (int(element['x']), int(element['y'])))
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        moving_elements[:] = [element for element in moving_elements if element['life'] > 0]

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
        
        try:
            mouse_trail.update()
            mouse_trail.draw(screen)
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

        # 卧龙密令：五行序列的闪光特效提示（屏幕顶部）
        try:
            puzzle_trigger.update(pygame.time.get_ticks())
            if FONT_SMALL:
                puzzle_trigger.draw_flash(screen, FONT_SMALL)
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        
        try:
            floating_particles.update()
            floating_particles.draw(screen)
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        
        mouse_pos = pygame.mouse.get_pos()
        try:
            pet_sprite.update(mouse_pos)
            pet_sprite.draw(screen)
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

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
                    except Exception as _e:
                        logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

        for element_type, element in menu_elements:
            if element_type == "dropdown":
                element.draw(screen)
                if hasattr(element, 'is_open') and element.is_open:
                    for opt_idx, (item_text, item_code, item_rect) in enumerate(element.dropdown_items):
                        try:
                            if item_rect.collidepoint(mouse_pos):
                                highlight_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
                                pygame.draw.rect(highlight_surf, (255, 215, 0, 60),
                                               (0, 0, item_rect.width, item_rect.height),
                                               border_radius=8)
                                screen.blit(highlight_surf, (item_rect.x, item_rect.y))
                        except Exception as _e:
                            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                running = False

            # 滚轮：滚动展开中的长下拉列表
            if event.type == pygame.MOUSEWHEEL:
                for _t, _e in menu_elements:
                    if _t == "dropdown" and _e.is_open:
                        _e.scroll(-1 if event.y > 0 else 1, screen_height)
                        break

            # 键盘导航：↑↓ 移焦点，Enter 确认，Esc 关下拉
            if event.type == pygame.KEYDOWN:
                # 卧龙密令·第4环：主菜单默念 WOLONG 即叩前厅（第5环密码锁）
                try:
                    if key_seq.on_key(event):
                        play_sfx("confirm.wav")
                        PasswordGate(screen).run()
                        restore_screen()
                        continue
                except Exception as _e:
                    logger.debug("[卧龙密令] 键序异常: %s", _e)

                if event.key == pygame.K_ESCAPE:
                    _open = [e for t, e in menu_elements
                             if t == "dropdown" and e.is_open]
                    if _open:
                        _open[0].is_open = False
                elif event.key in (pygame.K_UP, pygame.K_DOWN):
                    focus_idx[0] = (focus_idx[0] + (1 if event.key == pygame.K_DOWN else -1)) % len(menu_elements)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    _et, _el = menu_elements[focus_idx[0]]
                    if _et == "dropdown":
                        _el.is_open = not _el.is_open
                    else:
                        activate_code(_el[1])

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    for i in range(15):
                        mouse_trail.add_trail(
                            event.pos[0] + random.randint(-20, 20),
                            event.pos[1] + random.randint(-20, 20)
                        )
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
                
                for element_type, element in menu_elements:
                    if element_type == "dropdown":
                        clicked, code = element.check_click(mouse_pos)
                        if clicked and code:
                            activate_code(code)
                            break
                    elif element_type == "button":
                        btn, code = element
                        if btn.check_click(mouse_pos):
                            activate_code(code)
                            break

        # 键盘焦点高亮（金色描边，与回纹角一致）
        if focus_idx[0] < len(menu_elements):
            _ft, _fe = menu_elements[focus_idx[0]]
            _fr = _fe.rect if hasattr(_fe, "rect") else None
            if _fr:
                pygame.draw.rect(screen, (255, 215, 0), _fr.inflate(8, 8), 2, border_radius=10)
                pygame.display.flip()

        clock.tick(MENU_FPS)

def show_exit_menu():
    """退出确认弹窗 — 提供「退出游戏」「退出登录」「取消」三个选项。"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    panel_width = 430
    panel_height = 210
    panel_x = (screen_width - panel_width) // 2
    panel_y = (screen_height - panel_height) // 2

    button_width = 110
    button_height = 46
    button_spacing = 16
    # 三个按钮总宽 110*3+16*2 = 362 < 430，两侧各留 ~34px 内边距
    buttons_total = button_width * 3 + button_spacing * 2
    row_x = panel_x + (panel_width - buttons_total) // 2
    start_y = panel_y + 110

    exit_game_btn = Button("退出游戏", row_x, start_y,
                          button_width, button_height, FONT_SMALL,
                          normal_color=COLORS["accent_red"])

    exit_login_btn = Button("退出登录",
                            row_x + button_width + button_spacing, start_y,
                            button_width, button_height, FONT_SMALL,
                            normal_color=COLORS["accent_blue"])

    cancel_btn = Button("取消",
                        row_x + (button_width + button_spacing) * 2, start_y,
                        button_width, button_height, FONT_SMALL,
                        normal_color=COLORS["accent_green"])

    particles = []

    running = True
    while running:
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])

        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))

        for p in particles[:]:
            p.update()
            p.draw(screen)

        # 暗化遮罩：弹窗观感而非换页
        scrim = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        scrim.fill((0, 0, 0, 140))
        screen.blit(scrim, (0, 0))

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
                save()
                running = False

            # Esc=取消，Enter=默认「取消」，←→ 切换焦点按钮
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "cancel"
                if event.key == pygame.K_RETURN and exit_login_btn.is_hovered:
                    return "exit_login"
                if event.key == pygame.K_RETURN and exit_game_btn.is_hovered:
                    return "exit_game"
                if event.key == pygame.K_RETURN:
                    return "cancel"
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    trio = [exit_game_btn, exit_login_btn, cancel_btn]
                    cur = next((i for i, b in enumerate(trio) if b.is_hovered), 2)
                    nxt = (cur + (1 if event.key == pygame.K_RIGHT else -1)) % 3
                    for i, b in enumerate(trio):
                        b.is_hovered = (i == nxt)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if exit_game_btn.check_click(mouse_pos):
                    return "exit_game"
                elif exit_login_btn.check_click(mouse_pos):
                    return "exit_login"
                elif cancel_btn.check_click(mouse_pos):
                    return "cancel"

        clock.tick(MENU_FPS)

# ═══════════════════════════════════════════════════════════════════════════════
# 启动动画
# ═══════════════════════════════════════════════════════════════════════════════

def startup_animation():
    """启动动画 — 科技感 + 三国主题的开场动画，含网格、数字雨、HUD刻度环、标题揭示和进度条。

    效果组成：
        · 透视科技网格 + 全屏扫描线
        · 数字雨（三国字符 / 0-1 数据流）
        · HUD 旋转刻度环 + 十字准星
        · 标题故障色散 + 扫描揭示 + 外发光
        · 终端式启动日志逐行输出
        · 分段式科技进度条
    """
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

    # ── 科技感配色（青蓝数据色 + 三国金）──
    CYAN = (0, 229, 255)
    CYAN_DIM = (0, 120, 160)
    GOLD = (255, 215, 0)
    RED = (255, 70, 70)
    WHITE = (255, 255, 255)
    BG_TOP = (4, 8, 20)
    BG_BOTTOM = (10, 18, 38)

    DURATION = STARTUP_DURATION_MS
    GRID_STEP = 48

    # ── 预生成静态科技网格（中间亮、两侧暗，带纵深感）──
    grid_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    center_x = screen_width / 2.0
    for gx in range(0, screen_width + GRID_STEP, GRID_STEP):
        falloff = 1.0 - min(1.0, abs(gx - center_x) / max(1.0, screen_width * 0.72))
        alpha = int(38 * falloff) + 6
        pygame.draw.line(grid_surface, (*CYAN_DIM, alpha), (gx, 0), (gx, screen_height))

    # ── 数字雨字模（预渲染，避免每帧重复光栅化中文）──
    glyphs = "三國天下龍虎將帥兵符令01"
    glyph_cache = {ch: FONT_SMALL.render(ch, True, CYAN) for ch in set(glyphs)}
    rain = []
    col_count = max(1, screen_width // 26)
    for i in range(col_count):
        rain.append({
            "x": i * 26 + 8,
            "y": random.uniform(-screen_height, 0),
            "speed": random.uniform(90, 260),
            "glyph": random.choice(glyphs),
            "tail": random.randint(4, 9),
        })

    # ── 粒子 / 流光 ──
    particles = []
    streaks = []

    def spawn_particle():
        return {
            "x": random.uniform(0, screen_width),
            "y": random.uniform(0, screen_height),
            "vx": random.uniform(-18, 18),
            "vy": random.uniform(-26, -6),
            "life": random.uniform(1.0, 3.0),
            "max_life": 3.0,
            "size": random.uniform(1.0, 2.6),
            "color": GOLD if random.random() < 0.55 else CYAN,
        }

    for _ in range(80):
        p = spawn_particle()
        p["life"] = random.uniform(0.2, p["max_life"])
        particles.append(p)

    def spawn_streak():
        return {
            "x": random.uniform(0, screen_width),
            "y": random.uniform(-screen_height, 0),
            "length": random.uniform(50, 180),
            "speed": random.uniform(180, 460),
            "color": CYAN if random.random() < 0.7 else GOLD,
            "alpha": random.randint(40, 140),
        }

    for _ in range(16):
        s = spawn_streak()
        s["y"] = random.uniform(0, screen_height)
        streaks.append(s)

    BOOT_LINES = [
        "> 初始化天命协议 v3.0 ........... OK",
        "> 校准九州星图 ................. OK",
        "> 接入群雄数据链 ............... OK",
        "> 解密诸侯密档 ................. OK",
        "> 推演天下大势 ................. OK",
        "> 唤醒沉睡英魂 ................. OK",
        "> 校验虎符密钥 ................. OK",
        "> 系统就绪 // 恭迎主公",
    ]

    def draw_grid(offset):
        screen.blit(grid_surface, (0, 0))
        oy = int(offset) % GRID_STEP
        for gy in range(-GRID_STEP + oy, screen_height + GRID_STEP, GRID_STEP):
            pygame.draw.line(screen, (*CYAN_DIM, 22), (0, gy), (screen_width, gy))

    def draw_scanline(t):
        y = int((t * 300) % (screen_height + 200)) - 100
        band = pygame.Surface((screen_width, 100), pygame.SRCALPHA)
        for i in range(100):
            a = int(52 * (1 - abs(i - 50) / 50.0))
            if a > 0:
                pygame.draw.line(band, (*CYAN, a), (0, i), (screen_width, i))
        screen.blit(band, (0, y))

    def draw_reticle(cx, cy, t, radius):
        for r, col, width, count, spin in (
                (radius, (*CYAN, 160), 2, 48, 0.7),
                (radius + 30, (*GOLD, 80), 1, 20, -0.4),
                (radius - 40, (*CYAN, 70), 1, 72, 1.1)):
            size = r * 2 + 6
            ring = pygame.Surface((size, size), pygame.SRCALPHA)
            c = (size // 2, size // 2)
            pygame.draw.circle(ring, col, c, r, width)
            for i in range(count):
                ang = math.pi * 2 * i / count + t * spin
                inner = r - (8 if i % 6 == 0 else 4)
                outer = r + (9 if i % 6 == 0 else 3)
                pygame.draw.line(ring, col,
                                 (c[0] + math.cos(ang) * inner, c[1] + math.sin(ang) * inner),
                                 (c[0] + math.cos(ang) * outer, c[1] + math.sin(ang) * outer),
                                 width)
            screen.blit(ring, (cx - c[0], cy - c[1]))
        pygame.draw.line(screen, (*GOLD, 130), (cx - radius - 46, cy), (cx - radius + 6, cy), 1)
        pygame.draw.line(screen, (*GOLD, 130), (cx + radius - 6, cy), (cx + radius + 46, cy), 1)
        pygame.draw.line(screen, (*GOLD, 130), (cx, cy - radius - 46), (cx, cy - radius + 6), 1)
        pygame.draw.line(screen, (*GOLD, 130), (cx, cy + radius - 6), (cx, cy + radius + 46), 1)

    def draw_title(t, reveal):
        text = "三国霸业"
        title_surf = FONT_BIG.render(text, True, GOLD)
        if not title_surf:
            return
        tw, th = title_surf.get_size()
        cx, cy = screen_width // 2, int(screen_height * 0.34)
        panel_w, panel_h = tw + 140, th + 44
        px, py = cx - panel_w // 2, cy - panel_h // 2

        # 标题面板 + 四角科技卡扣
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (48, 22, 14, 205), (0, 0, panel_w, panel_h), border_radius=6)
        pygame.draw.rect(panel, (*GOLD, 160), (0, 0, panel_w, panel_h), 2, border_radius=6)
        for corner in ((0, 0), (panel_w - 14, 0), (0, panel_h - 14), (panel_w - 14, panel_h - 14)):
            pygame.draw.rect(panel, (*CYAN, 220), (*corner, 14, 14), 2)
        screen.blit(panel, (px, py))

        # 两侧中式纹样
        draw_chinese_pattern(screen, px - 44, py + panel_h // 2 - 17, 34, GOLD)
        draw_chinese_pattern(screen, px + panel_w + 10, py + panel_h // 2 - 17, 34, GOLD)

        # 外发光
        for offset, alpha in ((7, 40), (5, 60), (3, 80), (1, 110)):
            glow = pygame.transform.smoothscale(title_surf, (tw + offset * 4, th + offset * 2))
            glow.set_alpha(alpha)
            screen.blit(glow, (cx - glow.get_width() // 2, cy - glow.get_height() // 2))

        # 扫描揭示：仅显示扫描线以上部分
        scan_y = py + int(panel_h * reveal)
        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(px, py, panel_w, max(0, scan_y - py)))
        if random.random() < 0.18:  # 故障色散
            shift = random.randint(2, 5)
            r_surf = FONT_BIG.render(text, True, RED)
            c_surf = FONT_BIG.render(text, True, CYAN)
            if r_surf and c_surf:
                r_surf.set_alpha(90)
                c_surf.set_alpha(90)
                screen.blit(r_surf, (cx - tw // 2 - shift, cy - th // 2))
                screen.blit(c_surf, (cx - tw // 2 + shift, cy - th // 2))
        screen.blit(title_surf, (cx - tw // 2, cy - th // 2))
        screen.set_clip(prev_clip)

        if reveal < 1.0:  # 扫描亮点
            pygame.draw.line(screen, (*CYAN, 230), (px, scan_y), (px + panel_w, scan_y), 2)

    def draw_boot_log(elapsed):
        x = 46
        line_h = 26
        base_y = screen_height * 0.56
        shown = min(len(BOOT_LINES), int(elapsed / 420) + 1)
        blink = (pygame.time.get_ticks() // 400) % 2 == 0
        for i in range(shown):
            color = GOLD if i == len(BOOT_LINES) - 1 else CYAN
            surf = FONT_SMALL.render(BOOT_LINES[i], True, color)
            if surf:
                screen.blit(surf, (x, base_y + i * line_h))
        if shown < len(BOOT_LINES) and blink:
            cy = base_y + shown * line_h
            pygame.draw.rect(screen, CYAN, (x, cy + 2, 10, 18))

    def draw_progress(progress, t):
        bar_w = max(120, min(560, int(screen_width * 0.72)))
        bar_h = 22
        bar_x = (screen_width - bar_w) // 2
        bar_y = int(screen_height * 0.82)

        frame = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(frame, (8, 16, 30, 220), (0, 0, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(frame, (*CYAN, 150), (0, 0, bar_w, bar_h), 2, border_radius=4)
        screen.blit(frame, (bar_x, bar_y))

        seg = 28
        gap = 4
        seg_w = max(1, (bar_w - 12 - (seg - 1) * gap) // seg)
        filled = int(seg * progress)
        for i in range(seg):
            sx = bar_x + 6 + i * (seg_w + gap)
            if i < filled:
                color = GOLD if i >= seg - 3 else CYAN
                pygame.draw.rect(screen, color, (sx, bar_y + 6, seg_w, bar_h - 12), border_radius=2)
            else:
                pygame.draw.rect(screen, (*CYAN_DIM, 60), (sx, bar_y + 6, seg_w, bar_h - 12), border_radius=2)

        scan_x = bar_x + 6 + int((bar_w - 12 - seg_w) * ((t * 0.6) % 1.0))
        hl = pygame.Surface((seg_w, bar_h - 12), pygame.SRCALPHA)
        hl.fill((*WHITE, 90))
        screen.blit(hl, (scan_x, bar_y + 6))

        pct = FONT_SMALL.render(f"启动进度 {int(progress * 100):02d}%", True, WHITE)
        if pct:
            screen.blit(pct, (bar_x, bar_y - 30))
        phase = FONT_SMALL.render("// 天机推演中 //", True, GOLD)
        if phase:
            screen.blit(phase, (bar_x + bar_w - phase.get_width(), bar_y - 30))

    def update_effects(dt):
        # 数字雨（头部亮、尾部渐隐）
        for drop in rain:
            drop["y"] += drop["speed"] * dt
            if drop["y"] > screen_height + 120:
                drop["y"] = random.uniform(-260, -20)
                drop["x"] = random.randint(0, max(1, screen_width - 20))
                drop["glyph"] = random.choice(glyphs)
            surf = glyph_cache.get(drop["glyph"])
            if surf:
                for k in range(drop["tail"]):
                    y = drop["y"] - k * 22
                    if -20 <= y <= screen_height:
                        s = surf.copy()
                        s.set_alpha(max(10, int(150 * (1 - k / drop["tail"]))))
                        screen.blit(s, (drop["x"], y))
        # 流光
        for st in streaks:
            st["y"] += st["speed"] * dt
            if st["y"] - st["length"] > screen_height:
                st.update(spawn_streak())
            line = pygame.Surface((2, int(st["length"])), pygame.SRCALPHA)
            line.fill((*st["color"], st["alpha"]))
            screen.blit(line, (st["x"], st["y"] - st["length"]))
        # 粒子
        for p in particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] <= 0 or p["y"] < -20 or p["x"] < -20 or p["x"] > screen_width + 20:
                p.update(spawn_particle())
            alpha = max(0, min(255, int(220 * (p["life"] / p["max_life"]))))
            r = max(1, int(p["size"]))
            dot = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*p["color"], alpha), (r + 1, r + 1), r)
            pygame.draw.circle(dot, (*p["color"], max(0, alpha - 120)), (r + 1, r + 1), r + 1, 1)
            screen.blit(dot, (p["x"] - r, p["y"] - r))

    running = True
    start_time = pygame.time.get_ticks()

    while running:
        dt = min(clock.tick(MENU_FPS) / 1000.0, 0.05)
        elapsed = pygame.time.get_ticks() - start_time
        progress = min(elapsed / DURATION, 1.0)
        t = elapsed / 1000.0
        if progress >= 1.0:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                running = False

        draw_gradient_bg(screen, BG_TOP, BG_BOTTOM)
        draw_grid(t * 40)
        update_effects(dt)
        draw_reticle(screen_width // 2, int(screen_height * 0.34), t,
                     max(200, int(screen_width * 0.16)))
        draw_title(t, min(1.0, progress / 0.35))
        draw_boot_log(elapsed)
        draw_progress(progress, t)
        draw_scanline(t)

        pygame.display.flip()

    # 结束闪光过渡
    for i in range(10):
        flash = pygame.Surface((screen_width, screen_height))
        flash.fill(WHITE)
        flash.set_alpha(int(200 * (1 - i / 10.0)))
        screen.blit(flash, (0, 0))
        pygame.display.flip()
        clock.tick(MENU_FPS)
