"""增强版 2D 世界地图 - 多地形、NPC、移动"""

import pygame
import math
import random
import json
import os
import time
from ASSET.game_data import data, save, get_system_font_name, load_sound, logger, draw_gradient_bg, cull_dead, get_font
from ASSET import safe_exit

# 简单的Perlin噪声实现
class SimpleNoise:
    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)
        self.perm = list(range(256))
        random.shuffle(self.perm)
        self.perm = self.perm * 2
    
    def fade(self, t):
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def lerp(self, t, a, b):
        return a + t * (b - a)
    
    def grad(self, hash_val, x, y):
        h = hash_val & 3
        if h == 0:
            return x + y
        elif h == 1:
            return -x + y
        elif h == 2:
            return x - y
        else:
            return -x - y
    
    def noise(self, x, y):
        X = int(x) & 255
        Y = int(y) & 255
        
        x -= int(x)
        y -= int(y)
        
        u = self.fade(x)
        v = self.fade(y)
        
        A = self.perm[X] + Y
        B = self.perm[X + 1] + Y
        
        return self.lerp(v, 
                        self.lerp(u, self.grad(self.perm[A], x, y),
                                  self.grad(self.perm[B], x - 1, y)),
                        self.lerp(u, self.grad(self.perm[A + 1], x, y - 1),
                                  self.grad(self.perm[B + 1], x - 1, y - 1)))
    
    def pnoise2(self, x, y, octaves=1, persistence=0.5, lacunarity=2.0):
        total = 0
        frequency = 1
        amplitude = 1
        max_value = 0
        
        for _ in range(octaves):
            total += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        return total / max_value if max_value > 0 else 0

# 三国风格颜色主题
COLORS = {
    "bg_dark": (20, 25, 35),
    "bg_light": (35, 40, 50),
    "accent_gold": (218, 165, 32),
    "accent_red": (180, 60, 60),
    "accent_green": (60, 140, 60),
    "accent_blue": (70, 130, 180),
    "accent_blue_dark": (50, 100, 150),
    "text_white": (255, 250, 240),
    "text_gray": (160, 160, 160),
    "terrain_grass": (100, 140, 80),
    "terrain_hill": (140, 130, 90),
    "terrain_mountain": (120, 110, 100),
    "terrain_water": (50, 90, 130),
    "terrain_forest": (50, 90, 50),
}

# 地点类型配置
LOCATION_TYPES = {
    "主城": {"color": (180, 140, 80), "size": 20, "power": 1000, "icon": "城"},
    "关隘": {"color": (140, 120, 100), "size": 16, "power": 800, "icon": "关"},
    "军营": {"color": (160, 80, 60), "size": 14, "power": 600, "icon": "营"},
    "村庄": {"color": (120, 150, 100), "size": 12, "power": 200, "icon": "村"},
    "矿山": {"color": (100, 100, 110), "size": 12, "power": 300, "icon": "矿"},
    "港口": {"color": (80, 120, 160), "size": 14, "power": 400, "icon": "港"},
}

class Particle:
    """粒子效果"""
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
        self.size = max(0.5, self.size - 0.05)
        return self.life > 0  # 返回是否仍然存活
    
    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int(255 * (self.life / self.max_life))
        color = self.color[:3] if len(self.color) > 3 else self.color
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

class MarchingArmy:
    """行军中的军队"""
    def __init__(self, start_pos, end_pos, target_loc_idx, player_power, target_power, speed=3):
        self.start_x, self.start_y = start_pos
        self.end_x, self.end_y = end_pos
        self.x = self.start_x
        self.y = self.start_y
        self.target_loc_idx = target_loc_idx
        self.player_power = player_power
        self.target_power = target_power
        self.speed = speed
        self.progress = 0.0
        self.total_distance = math.hypot(self.end_x - self.start_x, self.end_y - self.start_y)
        self.finished = False
        self.victory = None  # None=进行中, True=胜利, False=失败
        self.particles = []
        self.animation_frame = 0
        self.battle_started = False
        self.max_particles = 50  # 限制最大粒子数量
        
        # 计算方向角度
        self.angle = math.atan2(self.end_y - self.start_y, self.end_x - self.start_x)
        
    def update(self):
        if self.finished:
            # 只更新粒子，直到粒子消失
            if not self.particles:
                return
        else:
            # 更新进度
            move_distance = self.speed
            self.progress += move_distance / self.total_distance
            
            if self.progress >= 1.0:
                self.progress = 1.0
                self.x = self.end_x
                self.y = self.end_y
                
                # 到达目标，开始战斗判定
                if not self.battle_started:
                    self.battle_started = True
                    # 战力判定
                    if self.player_power >= self.target_power:
                        self.victory = True
                        # 胜利特效，限制粒子数量
                        particle_count = min(20, self.max_particles - len(self.particles))
                        for _ in range(particle_count):
                            self.particles.append(Particle(
                                self.x, self.y, COLORS["accent_gold"],
                                random.uniform(2, 5),
                                random.uniform(3, 6),
                                random.randint(40, 60)
                            ))
                    else:
                        self.victory = False
                        # 失败特效，限制粒子数量
                        particle_count = min(15, self.max_particles - len(self.particles))
                        for _ in range(particle_count):
                            self.particles.append(Particle(
                                self.x, self.y, (150, 50, 50),
                                random.uniform(1, 3),
                                random.uniform(2, 4),
                                random.randint(30, 40)
                            ))
                    
                    self.finished = True
            else:
                self.x = self.start_x + (self.end_x - self.start_x) * self.progress
                self.y = self.start_y + (self.end_y - self.start_y) * self.progress
            
            # 生成行军粒子效果，限制粒子数量
            self.animation_frame += 1
            if self.animation_frame % 3 == 0 and len(self.particles) < self.max_particles:
                # 尘土效果
                dust_color = (180, 160, 140)
                offset_x = math.sin(self.animation_frame * 0.1) * 5
                self.particles.append(Particle(
                    self.x + offset_x + random.uniform(-8, 8),
                    self.y + random.uniform(-3, 3),
                    dust_color,
                    random.uniform(0.3, 1.0),
                    random.uniform(2, 4),
                    random.randint(15, 30)
                ))
        
        # 更新粒子，使用列表推导式提高效率
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, surface, offset_x, offset_y, zoom):
        # 转换坐标
        screen_x = int(self.x * zoom + offset_x)
        screen_y = int(self.y * zoom + offset_y)
        
        # 绘制行军路径（虚线）
        start_screen_x = int(self.start_x * zoom + offset_x)
        start_screen_y = int(self.start_y * zoom + offset_y)
        end_screen_x = int(self.end_x * zoom + offset_x)
        end_screen_y = int(self.end_y * zoom + offset_y)
        
        # 绘制已行进的实线路径
        pygame.draw.line(surface, (200, 180, 140), 
                        (start_screen_x, start_screen_y), 
                        (screen_x, screen_y), max(1, int(2 * zoom)))
        
        # 绘制剩余路径（半透明）
        pygame.draw.line(surface, (200, 180, 140, 100), 
                        (screen_x, screen_y), 
                        (end_screen_x, end_screen_y), max(1, int(2 * zoom)))
        
        # 绘制军队图标
        army_size = max(6, int(10 * zoom))
        
        # 军队阴影
        shadow_offset = max(2, int(3 * zoom))
        pygame.draw.ellipse(surface, (30, 30, 30), 
                           (screen_x - army_size + shadow_offset, 
                            screen_y - army_size//2 + shadow_offset,
                            army_size * 2, army_size))
        
        # 军队主体（圆形旗帜）
        flag_color = COLORS["accent_red"] if self.victory is None else (
            COLORS["accent_gold"] if self.victory else (150, 50, 50)
        )
        
        # 绘制圆形军队标记
        pygame.draw.circle(surface, flag_color, (screen_x, screen_y - army_size//2), army_size)
        pygame.draw.circle(surface, (60, 30, 30), (screen_x, screen_y - army_size//2), army_size, max(1, int(2 * zoom)))
        
        # 绘制粒子
        for p in self.particles:
            p.draw(surface)

class TerrainRenderer:
    """连续地形渲染器"""
    def __init__(self, map_width, map_height):
        self.map_width = map_width
        self.map_height = map_height
        self.scale = 0.008  # 进一步增大噪声缩放，减少计算复杂度
        self.noise_gen = SimpleNoise(seed=42)  # 使用固定种子保证一致性
        self.color_cache = {}  # 颜色缓存
        self.terrain_cache = {}  # 地形类型缓存
        self.grid_size = 40  # 增大网格大小，减少缓存项
        self.max_cache_size = 10000  # 限制缓存大小，避免内存泄漏
    
    def clear_cache(self):
        """清理缓存，避免内存泄漏"""
        if len(self.color_cache) > self.max_cache_size:
            # 只保留最近使用的缓存项
            self.color_cache = dict(list(self.color_cache.items())[-self.max_cache_size//2:])
        if len(self.terrain_cache) > self.max_cache_size:
            # 只保留最近使用的缓存项
            self.terrain_cache = dict(list(self.terrain_cache.items())[-self.max_cache_size//2:])
        
    def get_terrain_type(self, x, y):
        """获取地形类型（优化版）"""
        # 使用更大的网格进行缓存，减少缓存项数量
        cache_key = (int(x // self.grid_size), int(y // self.grid_size))
        if cache_key in self.terrain_cache:
            return self.terrain_cache[cache_key]
        
        # 进一步降低噪声复杂度以提高性能
        h = self.noise_gen.pnoise2(x * self.scale, y * self.scale, octaves=1, persistence=0.5, lacunarity=2.0)
        h = (h * 2) - 1  # 映射到[-1, 1]
        
        # 简化地形类型判断，减少条件分支
        if h < -0.1:
            terrain_type = "water"
        elif h < 0.0:
            terrain_type = "grass"
        elif h < 0.15:
            terrain_type = "hill"
        elif h < 0.3:
            terrain_type = "forest"
        else:
            terrain_type = "mountain"
        
        # 缓存地形类型
        self.terrain_cache[cache_key] = terrain_type
        return terrain_type
    
    def get_terrain_color(self, x, y):
        """获取地形颜色"""
        # 使用更大的网格进行缓存，减少缓存项数量
        cache_key = (int(x // self.grid_size), int(y // self.grid_size))
        if cache_key in self.color_cache:
            return self.color_cache[cache_key]
        
        terrain_type = self.get_terrain_type(x, y)
        
        # 根据地形类型获取颜色
        if terrain_type == "water":
            color = COLORS["terrain_water"]
        elif terrain_type == "grass":
            color = COLORS["terrain_grass"]
        elif terrain_type == "hill":
            color = COLORS["terrain_hill"]
        elif terrain_type == "forest":
            color = COLORS["terrain_forest"]
        else:  # mountain
            color = COLORS["terrain_mountain"]
        
        # 缓存颜色
        self.color_cache[cache_key] = color
        return color
    
    def draw(self, surface, offset_x, offset_y, zoom, screen_width, screen_height):
        """绘制地形（优化版）"""
        # 计算可见区域（世界坐标）
        world_left = max(0, int(-offset_x / zoom) - 40)
        world_top = max(0, int(-offset_y / zoom) - 40)
        world_right = min(self.map_width, int((screen_width - offset_x) / zoom) + 40)
        world_bottom = min(self.map_height, int((screen_height - offset_y) / zoom) + 40)
        
        # 确保至少渲染一些地形
        if world_left >= world_right:
            world_left = 0
            world_right = min(self.map_width, int(screen_width / zoom) + 1)
        if world_top >= world_bottom:
            world_top = 0
            world_bottom = min(self.map_height, int(screen_height / zoom) + 1)
        
        # 根据缩放级别动态调整像素块大小，更大的缩放使用更大的像素块
        pixel_size = max(30, int(30 * zoom))  # 增大像素块大小
        
        # 预计算颜色和位置，减少计算量
        # 批量计算和绘制，减少pygame.draw调用
        rects = []
        colors = []
        
        for wy in range(world_top, world_bottom, pixel_size):
            for wx in range(world_left, world_right, pixel_size):
                # 计算屏幕位置
                screen_x = int((wx * zoom) + offset_x)
                screen_y = int((wy * zoom) + offset_y)
                size = max(1, int(pixel_size * zoom))
                
                # 只绘制在屏幕内的部分
                if 0 <= screen_x < screen_width and 0 <= screen_y < screen_height:
                    # 使用更大的网格计算颜色，减少噪声计算
                    grid_x = int(wx / self.grid_size) * self.grid_size
                    grid_y = int(wy / self.grid_size) * self.grid_size
                    color = self.get_terrain_color(grid_x, grid_y)
                    rects.append((screen_x, screen_y, size + 1, size + 1))
                    colors.append(color)
        
        # 批量绘制，减少pygame.draw调用次数
        for rect, color in zip(rects, colors):
            pygame.draw.rect(surface, color, rect)
        
        # 定期清理缓存，避免内存泄漏
        self.clear_cache()

def draw_location(surface, x, y, loc_type, level, zoom, font, selected=False, hover=False):
    """绘制地点（建筑风格）"""
    config = LOCATION_TYPES[loc_type]
    color = config["color"]
    # 增大基础大小
    base_size = 30  # 基础大小
    size = max(15, int(base_size * zoom))
    
    # 转换屏幕坐标
    screen_x = int(x)
    screen_y = int(y)
    
    # 只在必要时绘制细节
    draw_details = zoom > 0.2
    draw_windows = zoom > 0.3
    draw_level = zoom > 0.4
    draw_label = (hover or selected) or zoom > 0.6
    
    # 选中或悬停时的发光效果
    if (selected or hover) and draw_details:
        for i in range(3, 0, -1):
            glow_radius = size + i * 8
            alpha = 60 - i * 15
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*color[:3], alpha), (0, 0, glow_radius * 2, glow_radius * 2), border_radius=8)
            surface.blit(glow_surf, (screen_x - glow_radius, screen_y - glow_radius))
    
    # 绘制地点主体（建筑风格）
    # 底部阴影
    if draw_details:
        shadow_offset = max(2, int(4 * zoom))
        pygame.draw.rect(surface, (30, 30, 30), 
                       (screen_x - size + shadow_offset, 
                        screen_y - size//2 + shadow_offset,
                        size * 2, size * 2), border_radius=4)
    
    # 主体建筑
    # 底部基座
    if draw_details:
        base_height = int(size * 0.3)
        pygame.draw.rect(surface, (80, 60, 40), 
                       (screen_x - size, screen_y - size + base_height, 
                        size * 2, base_height), border_radius=2)
    
    # 主体建筑
    building_height = size * 1.5
    pygame.draw.rect(surface, color, 
                   (screen_x - size + 2, screen_y - size, 
                    size * 2 - 4, building_height), border_radius=4)
    
    # 建筑边框
    if draw_details:
        pygame.draw.rect(surface, (60, 40, 30), 
                       (screen_x - size + 2, screen_y - size, 
                        size * 2 - 4, building_height), 2, border_radius=4)
    
    # 窗户（像素风格）
    if draw_windows:
        window_size = max(3, int(4 * zoom))
        window_spacing = max(2, int(6 * zoom))
        window_rows = 2
        window_cols = 3
        
        for row in range(window_rows):
            for col in range(window_cols):
                window_x = screen_x - size + 8 + col * (window_size + window_spacing)
                window_y = screen_y - size + 8 + row * (window_size + window_spacing)
                if window_x + window_size < screen_x + size and window_y + window_size < screen_y - size + building_height:
                    pygame.draw.rect(surface, (255, 220, 180), 
                                   (window_x, window_y, window_size, window_size))
    
    # 等级数字
    if draw_level:
        level_text = font.render(str(level), True, (255, 255, 255))
        text_rect = level_text.get_rect(center=(screen_x, screen_y - size//2))
        surface.blit(level_text, text_rect)
    
    # 地点类型标签
    if draw_label:
        label = config["icon"]
        label_text = font.render(label, True, (255, 255, 255))
        text_rect = label_text.get_rect(center=(screen_x, screen_y + size))
        surface.blit(label_text, text_rect)

def draw_power_comparison(surface, x, y, player_power, target_power, font):
    """绘制战力对比"""
    # 背景面板
    panel_width = 200
    panel_height = 80
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (30, 30, 40, 220), (0, 0, panel_width, panel_height), border_radius=8)
    surface.blit(panel, (x, y))
    
    # 标题
    title = font.render("战力对比", True, COLORS["accent_gold"])
    surface.blit(title, (x + 10, y + 5))
    
    # 玩家战力
    player_text = font.render(f"我方: {player_power}", True, COLORS["accent_green"])
    surface.blit(player_text, (x + 10, y + 30))
    
    # 目标战力
    target_text = font.render(f"敌方: {target_power}", True, COLORS["accent_red"])
    surface.blit(target_text, (x + 10, y + 50))
    
    # 战力条
    total_power = player_power + target_power
    if total_power > 0:
        player_ratio = player_power / total_power
        bar_width = 180
        bar_height = 8
        
        # 背景条
        pygame.draw.rect(surface, (60, 60, 60), (x + 10, y + 70, bar_width, bar_height))
        
        # 玩家战力条
        pygame.draw.rect(surface, COLORS["accent_green"], 
                        (x + 10, y + 70, int(bar_width * player_ratio), bar_height))
        
        # 敌方战力条
        pygame.draw.rect(surface, COLORS["accent_red"], 
                        (x + 10 + int(bar_width * player_ratio), y + 70, 
                         int(bar_width * (1 - player_ratio)), bar_height))

def show_occupy_menu(surface, x, y, loc, font, screen_width, screen_height):
    """显示占领菜单"""
    # 菜单配置
    menu_width = 250
    menu_height = 200
    menu_x = x - menu_width // 2
    menu_y = y - menu_height // 2
    
    # 确保菜单在屏幕内
    menu_x = max(10, min(screen_width - menu_width - 10, menu_x))
    menu_y = max(10, min(screen_height - menu_height - 10, menu_y))
    
    # 绘制背景
    menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
    pygame.draw.rect(surface, (40, 40, 60, 240), menu_rect, border_radius=10)
    pygame.draw.rect(surface, (80, 80, 120), menu_rect, 2, border_radius=10)
    
    # 标题
    title = font.render("占领操作", True, (255, 255, 255))
    title_rect = title.get_rect(center=(menu_x + menu_width // 2, menu_y + 30))
    surface.blit(title, title_rect)
    
    # 地点信息
    loc_info = font.render(f"{loc['type']} Lv.{loc['level']}", True, (200, 200, 200))
    loc_rect = loc_info.get_rect(center=(menu_x + menu_width // 2, menu_y + 60))
    surface.blit(loc_info, loc_rect)
    
    # 占领时间计算
    base_time = loc['level'] * 60  # 基础时间（秒）
    time_text = font.render(f"占领时间: {base_time}秒", True, (255, 255, 255))
    time_rect = time_text.get_rect(center=(menu_x + menu_width // 2, menu_y + 90))
    surface.blit(time_text, time_rect)
    
    # 按钮
    btn_width = 120
    btn_height = 40
    btn_y = menu_y + 130
    
    # 占领按钮
    occupy_btn = pygame.Rect(menu_x + 25, btn_y, btn_width, btn_height)
    pygame.draw.rect(surface, COLORS["accent_green"], occupy_btn, border_radius=5)
    occupy_text = font.render("开始占领", True, (255, 255, 255))
    occupy_rect = occupy_text.get_rect(center=occupy_btn.center)
    surface.blit(occupy_text, occupy_rect)
    
    # 取消按钮
    cancel_btn = pygame.Rect(menu_x + 25 + btn_width + 10, btn_y, btn_width, btn_height)
    pygame.draw.rect(surface, (150, 80, 80), cancel_btn, border_radius=5)
    cancel_text = font.render("取消", True, (255, 255, 255))
    cancel_rect = cancel_text.get_rect(center=cancel_btn.center)
    surface.blit(cancel_text, cancel_rect)
    
    return occupy_btn, cancel_btn

def show_town(button_rect, surface, screen_width, screen_height, font_main, font_small, clock):
    """显示我的城镇"""
    # 城镇大小
    TOWN_SIZE = 1000
    TOWN_DISPLAY_SIZE = min(600, screen_width * 0.8, screen_height * 0.8)
    
    # 计算城镇窗口位置
    town_x = (screen_width - TOWN_DISPLAY_SIZE) // 2
    town_y = (screen_height - TOWN_DISPLAY_SIZE) // 2
    
    # 城镇背景
    town_rect = pygame.Rect(town_x, town_y, TOWN_DISPLAY_SIZE, TOWN_DISPLAY_SIZE)
    pygame.draw.rect(surface, (30, 30, 55, 240), town_rect, border_radius=10)
    pygame.draw.rect(surface, (80, 80, 120), town_rect, 2, border_radius=10)
    
    # 标题
    title = font_main.render("我的城镇", True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, town_y - 30))
    surface.blit(title, title_rect)
    
    # 城镇网格
    grid_size = 50
    grid_count = TOWN_DISPLAY_SIZE // grid_size
    
    for i in range(grid_count + 1):
        x = town_x + i * grid_size
        y = town_y + i * grid_size
        pygame.draw.line(surface, (60, 60, 90), (x, town_y), (x, town_y + TOWN_DISPLAY_SIZE))
        pygame.draw.line(surface, (60, 60, 90), (town_x, y), (town_x + TOWN_DISPLAY_SIZE, y))
    
    # 加载建筑数据
    from ASSET.game_data import BUILDINGS
    
    # 确保建筑数据存在
    if "buildings" not in data:
        data["buildings"] = {}
    
    # 建筑位置
    building_positions = {
        "town_hall": (2, 2),
        "farm": (1, 3),
        "mine": (3, 3),
        "mill": (2, 4),
        "barracks": (4, 2),
        "hospital": (1, 1),
        "research_lab": (4, 4),
        "market": (3, 1),
        "blacksmith": (0, 2),
        "stable": (2, 0),
        "watchtower": (4, 0),
        "library": (0, 4),
        "temple": (0, 0),
        "warehouse": (4, 1),
        "training_ground": (1, 4),
        "defense_wall": (3, 4)
    }
    
    # 绘制建筑
    building_buttons = []
    for building_id, pos in building_positions.items():
        if building_id in BUILDINGS:
            x = town_x + pos[0] * grid_size + grid_size // 2
            y = town_y + pos[1] * grid_size + grid_size // 2
            size = grid_size - 10
            
            # 建筑等级
            level = data["buildings"].get(building_id, 0)
            
            # 建筑颜色
            if level > 0:
                color = COLORS["accent_green"]
            else:
                color = COLORS["accent_blue_dark"]
            
            # 绘制建筑
            pygame.draw.rect(surface, color, (x - size//2, y - size//2, size, size), border_radius=5)
            pygame.draw.rect(surface, (255, 215, 0), (x - size//2, y - size//2, size, size), 2, border_radius=5)
            
            # 建筑名称
            name = BUILDINGS[building_id]["name"]
            name_text = font_small.render(name, True, COLORS["text_white"])
            name_rect = name_text.get_rect(center=(x, y - 10))
            surface.blit(name_text, name_rect)
            
            # 建筑等级
            level_text = font_small.render(f"Lv.{level}", True, COLORS["text_white"])
            level_rect = level_text.get_rect(center=(x, y + 10))
            surface.blit(level_text, level_rect)
            
            # 建筑按钮
            building_buttons.append((pygame.Rect(x - size//2, y - size//2, size, size), building_id))
    
    # 关闭按钮
    close_btn = pygame.Rect(town_x + TOWN_DISPLAY_SIZE - 40, town_y - 35, 30, 30)
    pygame.draw.rect(surface, (150, 80, 80), close_btn, border_radius=5)
    close_text = font_small.render("×", True, COLORS["text_white"])
    close_rect = close_text.get_rect(center=close_btn.center)
    surface.blit(close_text, close_rect)
    
    # 等待用户点击
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                
                # 检查关闭按钮
                if close_btn.collidepoint(mx, my):
                    waiting = False
                
                # 检查建筑点击
                for rect, building_id in building_buttons:
                    if rect.collidepoint(mx, my):
                        show_building_menu(surface, mx, my, building_id, font_main, font_small, clock)
                        break
        
        # 绘制背景（半透明）
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 128), (0, 0, screen_width, screen_height))
        surface.blit(overlay, (0, 0))
        
        # 重绘城镇
        # 城镇背景
        pygame.draw.rect(surface, (30, 30, 55, 240), town_rect, border_radius=10)
        pygame.draw.rect(surface, (80, 80, 120), town_rect, 2, border_radius=10)
        
        # 标题
        surface.blit(title, title_rect)
        
        # 城镇网格
        for i in range(grid_count + 1):
            x = town_x + i * grid_size
            y = town_y + i * grid_size
            pygame.draw.line(surface, (60, 60, 90), (x, town_y), (x, town_y + TOWN_DISPLAY_SIZE))
            pygame.draw.line(surface, (60, 60, 90), (town_x, y), (town_x + TOWN_DISPLAY_SIZE, y))
        
        # 重绘建筑
        building_buttons = []
        for building_id, pos in building_positions.items():
            if building_id in BUILDINGS:
                x = town_x + pos[0] * grid_size + grid_size // 2
                y = town_y + pos[1] * grid_size + grid_size // 2
                size = grid_size - 10
                
                # 建筑等级
                level = data["buildings"].get(building_id, 0)
                
                # 建筑颜色
                if level > 0:
                    color = COLORS["accent_green"]
                else:
                    color = COLORS["accent_blue_dark"]
                
                # 绘制建筑
                pygame.draw.rect(surface, color, (x - size//2, y - size//2, size, size), border_radius=5)
                pygame.draw.rect(surface, (255, 215, 0), (x - size//2, y - size//2, size, size), 2, border_radius=5)
                
                # 建筑名称
                name = BUILDINGS[building_id]["name"]
                name_text = font_small.render(name, True, COLORS["text_white"])
                name_rect = name_text.get_rect(center=(x, y - 10))
                surface.blit(name_text, name_rect)
                
                # 建筑等级
                level_text = font_small.render(f"Lv.{level}", True, COLORS["text_white"])
                level_rect = level_text.get_rect(center=(x, y + 10))
                surface.blit(level_text, level_rect)
                
                # 建筑按钮
                building_buttons.append((pygame.Rect(x - size//2, y - size//2, size, size), building_id))
        
        # 关闭按钮
        pygame.draw.rect(surface, (150, 80, 80), close_btn, border_radius=5)
        surface.blit(close_text, close_rect)
        
        pygame.display.flip()
        clock.tick(60)

def show_building_menu(surface, x, y, building_id, font_main, font_small, clock):
    """显示建筑菜单"""
    from ASSET.game_data import BUILDINGS
    
    building_info = BUILDINGS[building_id]
    current_level = data["buildings"].get(building_id, 0)
    max_level = len(building_info["levels"])
    
    # 菜单配置
    menu_width = 300
    menu_height = 250
    menu_x = x - menu_width // 2
    menu_y = y - menu_height // 2
    
    # 确保菜单在屏幕内
    menu_x = max(10, min(surface.get_width() - menu_width - 10, menu_x))
    menu_y = max(10, min(surface.get_height() - menu_height - 10, menu_y))
    
    # 绘制背景
    menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
    pygame.draw.rect(surface, (40, 40, 60, 240), menu_rect, border_radius=10)
    pygame.draw.rect(surface, (80, 80, 120), menu_rect, 2, border_radius=10)
    
    # 标题
    title = font_main.render(building_info["name"], True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(menu_x + menu_width // 2, menu_y + 30))
    surface.blit(title, title_rect)
    
    # 描述
    desc = font_small.render(building_info["description"], True, COLORS["text_white"])
    desc_rect = desc.get_rect(center=(menu_x + menu_width // 2, menu_y + 70))
    surface.blit(desc, desc_rect)
    
    # 等级信息
    level_text = font_small.render(f"当前等级: Lv.{current_level}", True, COLORS["text_white"])
    surface.blit(level_text, (menu_x + 20, menu_y + 100))
    
    # 按钮
    btn_width = 120
    btn_height = 40
    btn_y = menu_y + 180
    
    # 升级按钮
    upgrade_btn = pygame.Rect(menu_x + 20, btn_y, btn_width, btn_height)
    if current_level < max_level:
        next_level_cost = building_info["levels"][current_level]["cost"]
        can_afford = all(data["resources"].get(res, 0) >= cost for res, cost in next_level_cost.items())
        
        if can_afford:
            upgrade_color = COLORS["accent_green"]
        else:
            upgrade_color = COLORS["accent_red"]
        
        pygame.draw.rect(surface, upgrade_color, upgrade_btn, border_radius=5)
        upgrade_text = font_small.render("升级", True, COLORS["text_white"])
        upgrade_rect = upgrade_text.get_rect(center=upgrade_btn.center)
        surface.blit(upgrade_text, upgrade_rect)
    
    # 功能按钮
    action_btn = pygame.Rect(menu_x + 160, btn_y, btn_width, btn_height)
    pygame.draw.rect(surface, COLORS["accent_blue"], action_btn, border_radius=5)
    
    # 根据建筑类型设置功能按钮文本
    if building_id == "hospital":
        action_text = "治疗"
    elif building_id == "market":
        action_text = "交易"
    elif building_id == "barracks":
        action_text = "训练"
    else:
        action_text = "查看"
    
    action_text_surf = font_small.render(action_text, True, COLORS["text_white"])
    action_rect = action_text_surf.get_rect(center=action_btn.center)
    surface.blit(action_text_surf, action_rect)
    
    # 等待用户点击
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                
                # 检查升级按钮
                if current_level < max_level and upgrade_btn.collidepoint(mx, my):
                    next_level_cost = building_info["levels"][current_level]["cost"]
                    can_afford = all(data["resources"].get(res, 0) >= cost for res, cost in next_level_cost.items())
                    
                    if can_afford:
                        # 扣除资源
                        for res, cost in next_level_cost.items():
                            data["resources"][res] -= cost
                        
                        # 升级建筑
                        data["buildings"][building_id] = current_level + 1
                        
                        # 应用建筑效果
                        apply_building_effects()
                        
                        # 保存数据
                        from ASSET.game_data import save
                        save()
                        
                        waiting = False
                
                # 检查功能按钮
                elif action_btn.collidepoint(mx, my):
                    if building_id == "hospital":
                        # 治疗功能
                        show_hospital_menu(surface, font_main, font_small, clock)
                    # 其他功能可以在这里添加
                    waiting = False
                
                # 点击菜单外关闭
                elif not menu_rect.collidepoint(mx, my):
                    waiting = False
        
        pygame.display.flip()
        clock.tick(60)

def show_hospital_menu(surface, font_main, font_small, clock):
    """显示医院治疗菜单"""
    # 菜单配置
    menu_width = 300
    menu_height = 200
    menu_x = (surface.get_width() - menu_width) // 2
    menu_y = (surface.get_height() - menu_height) // 2
    
    # 绘制背景
    menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
    pygame.draw.rect(surface, (40, 40, 60, 240), menu_rect, border_radius=10)
    pygame.draw.rect(surface, (80, 80, 120), menu_rect, 2, border_radius=10)
    
    # 标题
    title = font_main.render("医院", True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(menu_x + menu_width // 2, menu_y + 30))
    surface.blit(title, title_rect)
    
    # 治疗信息
    heal_text = font_small.render("治疗士兵，恢复战斗力", True, COLORS["text_white"])
    heal_rect = heal_text.get_rect(center=(menu_x + menu_width // 2, menu_y + 80))
    surface.blit(heal_text, heal_rect)
    
    # 治疗按钮
    heal_btn = pygame.Rect(menu_x + 50, menu_y + 120, 200, 40)
    pygame.draw.rect(surface, COLORS["accent_green"], heal_btn, border_radius=5)
    heal_btn_text = font_small.render("开始治疗", True, COLORS["text_white"])
    heal_btn_rect = heal_btn_text.get_rect(center=heal_btn.center)
    surface.blit(heal_btn_text, heal_btn_rect)
    
    # 等待用户点击
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                
                # 检查治疗按钮
                if heal_btn.collidepoint(mx, my):
                    # 治疗效果
                    if "player_power" in data:
                        data["player_power"] = min(data.get("player_power_max", 1000), data["player_power"] + 100)
                    else:
                        data["player_power"] = 600
                        data["player_power_max"] = 1000
                    
                    # 保存数据
                    from ASSET.game_data import save
                    save()
                    
                    waiting = False
                
                # 点击菜单外关闭
                elif not menu_rect.collidepoint(mx, my):
                    waiting = False
        
        pygame.display.flip()
        clock.tick(60)

def apply_building_effects():
    """应用建筑效果"""
    from ASSET.game_data import BUILDINGS
    
    # 重置所有建筑效果
    data["resource_bonus"] = 1.0
    data["hero_attack_bonus"] = 1.0
    data["hero_defense_bonus"] = 1.0
    data["research_speed_bonus"] = 1.0
    data["gold_bonus"] = 1.0
    
    # 应用每个建筑的效果
    for building_id, level in data.get("buildings", {}).items():
        if building_id in BUILDINGS and level > 0:
            building_info = BUILDINGS[building_id]
            if level <= len(building_info["levels"]):
                effect = building_info["levels"][level - 1]["effect"]
                
                # 应用效果
                for key, value in effect.items():
                    if key == "resource_bonus":
                        data["resource_bonus"] += value
                    elif key == "hero_attack":
                        if "hero_attack_bonus" not in data:
                            data["hero_attack_bonus"] = 1.0
                        data["hero_attack_bonus"] += value
                    elif key == "hero_defense":
                        if "hero_defense_bonus" not in data:
                            data["hero_defense_bonus"] = 1.0
                        data["hero_defense_bonus"] += value
                    elif key == "research_speed":
                        if "research_speed_bonus" not in data:
                            data["research_speed_bonus"] = 1.0
                        data["research_speed_bonus"] += value
                    elif key == "gold_bonus":
                        data["gold_bonus"] += value

def main():
    """增强地图主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
        
        # 分辨率适配
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            SCREEN_WIDTH = 1200
            SCREEN_HEIGHT = 800
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🗺️ 三国地图")
        clock = pygame.time.Clock()

        # 地图配置
        MAP_SIZE = (10000, 10000)
        MAX_LOCATIONS = 100
        
        # 字体初始化
        def init_font(size):
            return get_font(size)

        font_small = init_font(12)
        font_main = init_font(16)
        font_title = init_font(22)

        # 初始化地形渲染器
        terrain_renderer = TerrainRenderer(MAP_SIZE[0], MAP_SIZE[1])

        # 地图数据文件路径
        def get_map_data_path():
            # 确保地图数据目录存在
            map_dir = os.path.join(os.path.dirname(__file__), "..", "data", "maps")
            os.makedirs(map_dir, exist_ok=True)
            # 基于用户名生成文件路径
            username = data.get("username", "player")
            return os.path.join(map_dir, f"{username}_map_data.json")
        
        # 生成地图地点
        def generate_locations(num_locations):
            locations = []
            map_w, map_h = MAP_SIZE
            
            # 确保有主城
            locations.append({
                "x": map_w // 2, 
                "y": map_h // 2, 
                "type": "主城", 
                "level": 10, 
                "desc": "玩家主城",
                "power": LOCATION_TYPES["主城"]["power"],
                "owner": "player"
            })
            
            for i in range(num_locations - 1):
                while True:
                    x = random.randint(100, map_w - 100)
                    y = random.randint(100, map_h - 100)
                    valid = True
                    for loc in locations:
                        if math.hypot(x - loc["x"], y - loc["y"]) < 300:  # 增大间距避免重叠
                            valid = False
                            break
                    if valid:
                        break

                loc_type = random.choice(["关隘", "军营", "村庄", "矿山", "港口"])
                level = random.randint(1, 10)
                power = int(LOCATION_TYPES[loc_type]["power"] * (0.5 + level * 0.1))
                
                locations.append({
                    "x": x,
                    "y": y,
                    "type": loc_type,
                    "level": level,
                    "desc": LOCATION_TYPES[loc_type]["icon"],
                    "power": power,
                    "owner": "enemy" if loc_type == "军营" else "neutral"
                })

            return locations
        
        # 保存地图数据
        def save_map_data(locations):
            try:
                # 验证用户名和密码
                username = data.get("username", "")
                password = data.get("password", "")
                if not username or not password:
                    logger.info("错误: 未登录，无法保存地图数据")
                    return False
                
                # 保存地图数据
                map_data = {
                    "username": username,
                    "locations": locations,
                    "timestamp": time.time()
                }
                
                map_path = get_map_data_path()
                with open(map_path, 'w', encoding='utf-8') as f:
                    json.dump(map_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"地图数据已保存到: {map_path}")
                return True
            except Exception as e:
                logger.info(f"保存地图数据失败: {e}")
                return False
        
        # 加载地图数据
        def load_map_data():
            try:
                # 验证用户名和密码
                username = data.get("username", "")
                password = data.get("password", "")
                if not username or not password:
                    logger.info("错误: 未登录，无法加载地图数据")
                    return None
                
                map_path = get_map_data_path()
                if not os.path.exists(map_path):
                    logger.info("地图数据文件不存在，将生成新地图")
                    return None
                
                with open(map_path, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                
                # 验证用户名
                if map_data.get("username") != username:
                    logger.info("错误: 地图数据与当前用户不匹配")
                    return None
                
                logger.info(f"成功加载地图数据，包含 {len(map_data.get('locations', []))} 个地点")
                return map_data.get("locations")
            except Exception as e:
                logger.info(f"加载地图数据失败: {e}")
                return None
        
        # 加载或生成地图数据
        locations = load_map_data()
        if locations is None:
            logger.info(f"生成新地图，大小: {MAP_SIZE[0]}x{MAP_SIZE[1]}, 地点数量: {MAX_LOCATIONS}")
            locations = generate_locations(MAX_LOCATIONS)
            save_map_data(locations)
        else:
            logger.info(f"加载现有地图，包含 {len(locations)} 个地点")
        
        # 计算玩家综合战力
        def calculate_player_power():
            """根据武将属性计算综合战力"""
            base_power = 100  # 基础战力
            
            # 从存档获取武将数据
            heroes = data.get("heroes", [])
            hero_count = len(heroes)
            
            # 武将数量加成
            count_bonus = hero_count * 50
            
            # 武将品质加成
            quality_bonus = 0
            quality_multipliers = {
                "普通": 1,
                "优秀": 1.5,
                "稀有": 2,
                "史诗": 3,
                "传说": 5
            }
            
            # 武将阵营加成
            faction_bonus = 0
            faction_count = {}
            
            # 武将坐骑加成
            mount_bonus = 0
            
            # 武将道具加成
            item_bonus = 0
            
            for hero in heroes:
                # 品质加成
                quality = hero.get("quality", "普通")
                quality_bonus += quality_multipliers.get(quality, 1) * 100
                
                # 阵营统计
                faction = hero.get("faction", "")
                if faction:
                    faction_count[faction] = faction_count.get(faction, 0) + 1
                
                # 坐骑加成
                mount = hero.get("mount", {})
                if mount:
                    mount_bonus += mount.get("power_bonus", 0)
                
                # 道具加成
                items = hero.get("items", [])
                for item in items:
                    item_bonus += item.get("power_bonus", 0)
            
            # 阵营加成（同阵营武将越多，加成越高）
            for count in faction_count.values():
                if count >= 3:
                    faction_bonus += (count - 2) * 50
            
            # 计算总战力
            total_power = base_power + count_bonus + quality_bonus + faction_bonus + mount_bonus + item_bonus
            
            # 确保战力有一个合理的最小值
            total_power = max(500, total_power)
            
            # 保存计算结果
            data["player_power"] = total_power
            data["player_power_max"] = total_power * 1.5
            
            return total_power
        
        # 计算玩家战力
        player_power = calculate_player_power()
        
        # 行军中的军队列表
        marching_armies = []
        
        # 相机控制
        camera_x = -MAP_SIZE[0] // 2 + SCREEN_WIDTH // 2
        camera_y = -MAP_SIZE[1] // 2 + SCREEN_HEIGHT // 2
        zoom = 0.4
        min_zoom = 0.2
        max_zoom = 1.5
        
        # 交互状态
        selected_location = None
        hover_location = None
        dragging = False
        drag_start = (0, 0)
        camera_start = (0, 0)
        show_occupy_menu_flag = False
        occupy_menu_loc = None
        occupy_btn_rect = None
        cancel_btn_rect = None
        
        # 特效
        particles = []
        max_global_particles = 100  # 限制全局粒子数量
        
        # 消息提示
        message = None
        message_timer = 0
        
        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 转换鼠标坐标到世界坐标（预计算）
            zoom_inv = 1.0 / zoom  # 预计算缩放倒数
            world_mx = (mx - camera_x) * zoom_inv
            world_my = (my - camera_y) * zoom_inv
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        # 检查是否点击了地点
                        clicked_location = None
                        # 预计算点击区域大小
                        base_size = 30
                        click_radius = base_size / 2
                        click_radius_squared = click_radius * click_radius  # 预计算平方，避免开方
                        
                        # 只检查屏幕附近的地点，减少计算量
                        for i, loc in enumerate(locations):
                            # 快速距离检查（使用平方避免开方）
                            dx = world_mx - loc["x"]
                            dy = world_my - loc["y"]
                            if dx*dx + dy*dy < click_radius_squared:
                                clicked_location = i
                                break
                        
                        if clicked_location is not None:
                            if selected_location is not None and selected_location != clicked_location:
                                # 准备行军
                                start_loc = locations[selected_location]
                                target_loc = locations[clicked_location]
                                
                                # 判断是否可以攻占
                                if target_loc["owner"] == "player":
                                    message = "该地点已经是你的领地"
                                    message_timer = 120
                                else:
                                    # 创建行军
                                    start_pos = (start_loc["x"], start_loc["y"])
                                    end_pos = (target_loc["x"], target_loc["y"])
                                    army = MarchingArmy(
                                        start_pos, end_pos, clicked_location,
                                        player_power, target_loc["power"],
                                        speed=4
                                    )
                                    marching_armies.append(army)
                                    
                                    # 战力对比提示
                                    if player_power < target_loc["power"]:
                                        message = f"警告：敌方战力({target_loc['power']})高于我方({player_power})！"
                                    else:
                                        message = f"进攻！我方战力({player_power}) vs 敌方({target_loc['power']})"
                                    message_timer = 180
                                    
                                    # 添加特效，限制粒子数量
                                    particle_count = min(10, max_global_particles - len(particles))
                                    for _ in range(particle_count):
                                        particles.append(Particle(
                                            mx, my, COLORS["accent_gold"],
                                            random.uniform(1, 3),
                                            random.uniform(2, 4),
                                            random.randint(25, 40)
                                        ))
                            
                            selected_location = clicked_location
                        else:
                            dragging = True
                            drag_start = (mx, my)
                            camera_start = (camera_x, camera_y)
                    
                    elif event.button == 3:  # 右键显示占领菜单
                        # 检查是否点击了地点
                        clicked_location = None
                        # 使用与左键相同的预计算值
                        base_size = 30
                        click_radius = base_size / 2
                        click_radius_squared = click_radius * click_radius  # 预计算平方，避免开方
                        
                        # 只检查屏幕附近的地点，减少计算量
                        for i, loc in enumerate(locations):
                            # 快速距离检查（使用平方避免开方）
                            dx = world_mx - loc["x"]
                            dy = world_my - loc["y"]
                            if dx*dx + dy*dy < click_radius_squared:
                                clicked_location = i
                                break
                        
                        if clicked_location is not None:
                            # 显示占领菜单
                            show_occupy_menu_flag = True
                            occupy_menu_loc = locations[clicked_location]
                            # 计算菜单位置
                            menu_x = mx
                            menu_y = my
                    
                    elif event.button == 4:  # 滚轮上
                        new_zoom = min(zoom * 1.1, max_zoom)
                        camera_x = mx - (mx - camera_x) * (new_zoom / zoom)
                        camera_y = my - (my - camera_y) * (new_zoom / zoom)
                        zoom = new_zoom
                    
                    elif event.button == 5:  # 滚轮下
                        new_zoom = max(zoom / 1.1, min_zoom)
                        camera_x = mx - (mx - camera_x) * (new_zoom / zoom)
                        camera_y = my - (my - camera_y) * (new_zoom / zoom)
                        zoom = new_zoom
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        dragging = False
                
                elif event.type == pygame.MOUSEMOTION:
                    if dragging:
                        # 修正：相机拖动方向应该与鼠标移动方向相同
                        camera_x = camera_start[0] + (mx - drag_start[0])
                        camera_y = camera_start[1] + (my - drag_start[1])
                    
                    # 检查悬停
                    hover_location = None
                    # 预计算悬停区域大小
                    base_size = 30
                    hover_radius = base_size / 2
                    hover_radius_squared = hover_radius * hover_radius  # 预计算平方，避免开方
                    
                    # 只检查屏幕附近的地点，减少计算量
                    for i, loc in enumerate(locations):
                        # 快速距离检查（使用平方避免开方）
                        dx = world_mx - loc["x"]
                        dy = world_my - loc["y"]
                        if dx*dx + dy*dy < hover_radius_squared:
                            hover_location = i
                            break
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # R键重置视角
                        camera_x = -MAP_SIZE[0] // 2 + SCREEN_WIDTH // 2
                        camera_y = -MAP_SIZE[1] // 2 + SCREEN_HEIGHT // 2
                        zoom = 0.4

            # 更新行军中的军队
            for army in marching_armies[:]:
                army.update()
                if army.finished:
                    if army.victory:
                        # 占领成功
                        locations[army.target_loc_idx]["owner"] = "player"
                        message = f"攻占成功！获得 {locations[army.target_loc_idx]['desc']}"
                        message_timer = 150
                    else:
                        # 占领失败
                        message = "攻占失败，战力不足！"
                        message_timer = 150
                    marching_armies.remove(army)
            
            # 更新粒子，使用列表推导式提高效率
            particles = [p for p in particles if p.update()]
            
            # 更新消息
            if message_timer > 0:
                message_timer -= 1
            else:
                message = None

            # 绘制
            # 背景
            screen.fill(COLORS["bg_dark"])
            
            # 绘制地形
            terrain_renderer.draw(screen, camera_x, camera_y, zoom, SCREEN_WIDTH, SCREEN_HEIGHT)
            
            # 绘制行军中的军队
            for army in marching_armies:
                army.draw(screen, camera_x, camera_y, zoom)
            
            # 绘制地点
            # 按距离相机的远近排序，远处的先绘制，近处的后绘制
            # 这样可以减少过度绘制
            locations_with_depth = []
            for i, loc in enumerate(locations):
                # 计算屏幕坐标
                screen_x = loc["x"] * zoom + camera_x
                screen_y = loc["y"] * zoom + camera_y
                # 使用y坐标作为深度（简单的2D深度排序）
                depth = screen_y
                locations_with_depth.append((depth, i, screen_x, screen_y, loc))
            
            # 按深度排序
            locations_with_depth.sort(key=lambda x: x[0])
            
            # 绘制排序后的地点
            for depth, i, screen_x, screen_y, loc in locations_with_depth:
                draw_location(screen, 
                            screen_x, 
                            screen_y,
                            loc["type"], loc["level"], zoom, font_small,
                            selected=(i == selected_location),
                            hover=(i == hover_location))
            
            # 绘制粒子
            for p in particles:
                p.draw(screen)
            
            # 绘制UI
            # 顶部面板
            panel_surf = pygame.Surface((SCREEN_WIDTH, 55), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (25, 25, 35, 200), (0, 0, SCREEN_WIDTH, 55))
            screen.blit(panel_surf, (0, 0))
            pygame.draw.line(screen, COLORS["accent_gold"], (0, 55), (SCREEN_WIDTH, 55), 2)
            
            # 标题
            title = font_title.render("⚔️ 三国争霸地图", True, COLORS["accent_gold"])
            screen.blit(title, (15, 12))
            
            # 战力显示
            power_text = font_main.render(f"战力: {player_power}", True, COLORS["accent_green"])
            screen.blit(power_text, (200, 15))
            
            # 操作提示
            hint_text = font_small.render("左键选择/攻占 | 右键取消 | 滚轮缩放 | R重置", 
                                         True, COLORS["text_gray"])
            hint_rect = hint_text.get_rect(right=SCREEN_WIDTH - 100, centery=27)
            screen.blit(hint_text, hint_rect)
            
            # 返回按钮
            return_btn = pygame.Rect(SCREEN_WIDTH - 90, 12, 75, 30)
            pygame.draw.rect(screen, (60, 100, 60), return_btn, border_radius=5)
            pygame.draw.rect(screen, (80, 140, 80), return_btn, 2, border_radius=5)
            return_text = font_small.render("↩️ 返回", True, COLORS["text_white"])
            return_text_rect = return_text.get_rect(center=return_btn.center)
            screen.blit(return_text, return_text_rect)
            
            # 检查返回按钮点击
            if pygame.mouse.get_pressed()[0] and return_btn.collidepoint(mx, my):
                running = False
            
            # 我的城镇按钮
            town_btn = pygame.Rect(SCREEN_WIDTH - 180, SCREEN_HEIGHT - 80, 160, 60)
            pygame.draw.rect(screen, (220, 160, 80), town_btn, border_radius=8)
            pygame.draw.rect(screen, (255, 215, 0), town_btn, 2, border_radius=8)
            town_text = font_main.render("我的城镇", True, COLORS["text_white"])
            town_text_rect = town_text.get_rect(center=town_btn.center)
            screen.blit(town_text, town_text_rect)
            
            # 检查城镇按钮点击
            if pygame.mouse.get_pressed()[0] and town_btn.collidepoint(mx, my):
                show_town(town_btn, screen, SCREEN_WIDTH, SCREEN_HEIGHT, font_main, font_small, clock)
            
            # 绘制占领菜单
            if show_occupy_menu_flag and occupy_menu_loc:
                occupy_btn_rect, cancel_btn_rect = show_occupy_menu(
                    screen, menu_x, menu_y, occupy_menu_loc, font_main, SCREEN_WIDTH, SCREEN_HEIGHT
                )
                
                # 检查菜单按钮点击
                if pygame.mouse.get_pressed()[0]:
                    if occupy_btn_rect and occupy_btn_rect.collidepoint(mx, my):
                        # 开始占领
                        show_occupy_menu_flag = False
                        # 找到地点索引
                        target_idx = None
                        for i, loc in enumerate(locations):
                            if loc == occupy_menu_loc:
                                target_idx = i
                                break
                        if target_idx is not None:
                            # 创建行军
                            start_pos = (locations[0]["x"], locations[0]["y"])
                            end_pos = (occupy_menu_loc["x"], occupy_menu_loc["y"])
                            army = MarchingArmy(
                                start_pos, end_pos, target_idx,
                                player_power, occupy_menu_loc["power"],
                                speed=4
                            )
                            marching_armies.append(army)
                            
                            # 战力对比提示
                            if player_power < occupy_menu_loc["power"]:
                                message = f"警告：敌方战力({occupy_menu_loc['power']})高于我方({player_power})！"
                            else:
                                message = f"进攻！我方战力({player_power}) vs 敌方({occupy_menu_loc['power']})"
                            message_timer = 180
                    elif cancel_btn_rect and cancel_btn_rect.collidepoint(mx, my):
                        # 取消占领
                        show_occupy_menu_flag = False
            
            # 选中地点信息
            if selected_location is not None:
                loc = locations[selected_location]
                info_y = 65
                
                # 信息背景
                info_bg = pygame.Surface((250, 80), pygame.SRCALPHA)
                pygame.draw.rect(info_bg, (30, 30, 40, 220), (0, 0, 250, 80), border_radius=8)
                screen.blit(info_bg, (15, info_y))
                
                # 地点信息
                info_text = font_main.render(f"{loc['desc']} Lv{loc['level']}", 
                                           True, COLORS["accent_gold"])
                screen.blit(info_text, (25, info_y + 5))
                
                # 战力信息
                power_info = font_small.render(f"战力: {loc['power']}", 
                                              True, COLORS["text_white"])
                screen.blit(power_info, (25, info_y + 30))
                
                # 所有者
                owner_color = COLORS["accent_green"] if loc["owner"] == "player" else COLORS["accent_red"]
                owner_text = "己方" if loc["owner"] == "player" else ("敌方" if loc["owner"] == "enemy" else "中立")
                owner_info = font_small.render(f"归属: {owner_text}", True, owner_color)
                screen.blit(owner_info, (25, info_y + 50))
                
                # 如果选中的是敌方或中立地点，显示战力对比
                if loc["owner"] != "player" and selected_location is not None:
                    draw_power_comparison(screen, 280, info_y, player_power, loc["power"], font_small)
            
            # 消息提示
            if message:
                msg_surf = font_main.render(message, True, COLORS["accent_gold"])
                msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
                
                # 消息背景
                msg_bg = pygame.Surface((msg_rect.width + 20, msg_rect.height + 10), pygame.SRCALPHA)
                pygame.draw.rect(msg_bg, (30, 30, 40, 200), (0, 0, msg_rect.width + 20, msg_rect.height + 10), border_radius=8)
                screen.blit(msg_bg, (msg_rect.x - 10, msg_rect.y - 5))
                
                screen.blit(msg_surf, msg_rect)

            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        logger.info(f"地图系统错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        safe_exit()

if __name__ == "__main__":
    main()
