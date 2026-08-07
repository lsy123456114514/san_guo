"""Pygame 2D 世界地图经典版"""

import os
import pygame
import random
import math
import platform
from ASSET.game_data import data, save, get_system_font_name, load_sound, logger, draw_gradient_bg, cull_dead, get_font
from ASSET import safe_exit

# 颜色主题
COLORS = {
    "bg_dark": (10, 15, 30),
    "bg_light": (20, 25, 45),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 180),
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 200),
    "panel_bg": (40, 40, 70, 200)
}

# 地点类型配置
LOCATION_TYPES = {
    "矿产": {
        "color": (180, 180, 190),
        "glow": (220, 220, 230),
        "icon": "⛏️",
        "hostile": False,
        "output": {"金元宝": 5, "煤炭": 10}
    },
    "农田": {
        "color": (100, 200, 100),
        "glow": (150, 255, 150),
        "icon": "🌾",
        "hostile": False,
        "output": {"食物": 15, "水": 5}
    },
    "煤矿": {
        "color": (80, 80, 90),
        "glow": (120, 120, 130),
        "icon": "⚫",
        "hostile": False,
        "output": {"煤炭": 20}
    },
    "水井": {
        "color": (80, 150, 220),
        "glow": (120, 200, 255),
        "icon": "💧",
        "hostile": False,
        "output": {"水": 25}
    },
    "敌对单位": {
        "color": (220, 80, 80),
        "glow": (255, 120, 120),
        "icon": "⚔️",
        "hostile": True,
        "output": {}
    }
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
        self.size = max(0.5, self.size - 0.05)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        # 只使用RGB部分，确保颜色参数有效
        color = self.color[:3]  # 只取RGB值，去掉alpha通道
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

class FloatingText:
    def __init__(self, text, x, y, color, font):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.life = 60
        self.max_life = 60
        self.speed_y = -1
    
    def update(self):
        self.y += self.speed_y
        self.life -= 1
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (int(self.x), int(self.y)))

def draw_gradient_bg(surface, color1, color2):
    """绘制渐变背景"""
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_grid(surface, offset_x, offset_y, screen_width, screen_height, grid_size=100):
    """绘制网格背景"""
    grid_color = (40, 45, 65)
    
    start_x = offset_x % grid_size
    start_y = offset_y % grid_size
    
    for x in range(start_x, screen_width, grid_size):
        pygame.draw.line(surface, grid_color, (x, 0), (x, screen_height))
    
    for y in range(start_y, screen_height, grid_size):
        pygame.draw.line(surface, grid_color, (0, y), (screen_width, y))

def draw_location(surface, x, y, loc_type, level, radius, font, selected=False, hover=False, capturing=False, capture_progress=0):
    """绘制地点"""
    config = LOCATION_TYPES[loc_type]
    color = config["color"]
    glow_color = config["glow"]
    
    # 选中或悬停时的发光效果
    if selected or hover:
        for i in range(3, 0, -1):
            glow_radius = radius + i * 5
            alpha = 100 - i * 25
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color[:3], alpha), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (x - glow_radius, y - glow_radius))
    
    # 占领中效果
    if capturing:
        # 占领进度环
        progress_radius = radius + 8
        progress_angle = int(360 * capture_progress)
        # 只使用RGB部分，确保颜色参数有效
        pygame.draw.circle(surface, (255, 215, 0), (x, y), progress_radius)
        pygame.draw.arc(surface, COLORS["accent_gold"], 
                      (x - progress_radius, y - progress_radius, progress_radius * 2, progress_radius * 2),
                      -math.pi/2, -math.pi/2 + math.radians(progress_angle), 3)
    
    # 外圈
    pygame.draw.circle(surface, glow_color, (x, y), radius + 3)
    # 主体
    pygame.draw.circle(surface, color, (x, y), radius)
    # 内圈高光
    pygame.draw.circle(surface, tuple(min(255, c + 30) for c in color), (x, y), radius - 3)
    # 边框
    pygame.draw.circle(surface, COLORS["text_white"], (x, y), radius, 2)
    
    # 等级文字
    level_text = font.render(str(level), True, COLORS["text_white"])
    text_rect = level_text.get_rect(center=(x, y))
    # 文字阴影
    shadow_text = font.render(str(level), True, (0, 0, 0))
    surface.blit(shadow_text, (text_rect.x + 1, text_rect.y + 1))
    surface.blit(level_text, text_rect)
    
    # 占领中文字
    if capturing:
        capture_text = font.render("占领中...", True, COLORS["accent_gold"])
        capture_rect = capture_text.get_rect(center=(x, y + radius + 20))
        surface.blit(capture_text, capture_rect)

def draw_popup(surface, x, y, loc, font_small, font_main, capturing=False, time_card_count=0):
    """绘制地点信息弹窗"""
    loc_type = loc[2]
    level = loc[3]
    output = loc[4]
    config = LOCATION_TYPES[loc_type]
    
    popup_w = 220
    
    # 动态计算弹窗高度
    info_lines = 1  # 至少有一行信息
    if output:
        info_lines = len(output)
    
    # 如果正在占领，增加高度以显示时间卡按钮
    if capturing and not config["hostile"]:
        popup_h = 80 + info_lines * 22 + 80  # 标题 + 信息 + 两个按钮
    else:
        popup_h = 80 + info_lines * 22 + 40  # 标题 + 信息 + 一个按钮
    
    # 确保弹窗不超出屏幕
    if x + popup_w > surface.get_width():
        x = surface.get_width() - popup_w - 10
    if y + popup_h > surface.get_height():
        y = surface.get_height() - popup_h - 10
    
    popup_rect = pygame.Rect(x, y, popup_w, popup_h)
    
    # 弹窗背景
    popup_surf = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
    pygame.draw.rect(popup_surf, (35, 35, 60, 230), (0, 0, popup_w, popup_h), border_radius=12)
    surface.blit(popup_surf, (x, y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], popup_rect, 2, border_radius=12)
    
    # 标题栏
    title_rect = pygame.Rect(x, y, popup_w, 35)
    pygame.draw.rect(surface, (*config["color"][:3], 180), title_rect, border_radius=12)
    pygame.draw.rect(surface, config["color"], (x, y + 30, popup_w, 5))
    
    # 图标和名称
    icon_text = font_main.render(config["icon"], True, COLORS["text_white"])
    name_text = font_small.render(f"{loc_type} Lv{level}", True, COLORS["text_white"])
    surface.blit(icon_text, (x + 15, y + 5))
    surface.blit(name_text, (x + 50, y + 8))
    
    # 产出信息
    y_offset = y + 45
    if output:
        for res, amt in output.items():
            res_text = font_small.render(f"{res}: +{amt}", True, COLORS["accent_gold"])
            surface.blit(res_text, (x + 15, y_offset))
            y_offset += 22
    else:
        warning_text = font_small.render("⚠️ 敌对单位", True, COLORS["text_gray"])
        surface.blit(warning_text, (x + 15, y_offset))
        y_offset += 22
    
    # 按钮（根据类型显示不同按钮）
    btn_rect = pygame.Rect(x + 15, y + popup_h - 45, popup_w - 30, 35)
    time_card_btn = None
    
    if not config["hostile"]:
        if capturing:
            # 正在占领时显示时间卡按钮
            time_card_btn = pygame.Rect(x + 15, y + popup_h - 85, popup_w - 30, 35)
            
            # 时间卡按钮
            for i in range(35):
                ratio = i / 35
                btn_color = (
                    int(60 * (1 - ratio) + 100 * ratio),
                    int(120 * (1 - ratio) + 160 * ratio),
                    int(200 * (1 - ratio) + 255 * ratio)
                )
                pygame.draw.line(surface, btn_color, (time_card_btn.x, time_card_btn.y + i), 
                               (time_card_btn.x + time_card_btn.width, time_card_btn.y + i))
            
            pygame.draw.rect(surface, COLORS["text_white"], time_card_btn, 2, border_radius=8)
            time_card_text = font_small.render(f"⏰ 使用时间卡 ({time_card_count})", True, COLORS["text_white"])
            time_card_text_rect = time_card_text.get_rect(center=time_card_btn.center)
            surface.blit(time_card_text, time_card_text_rect)
        
        # 占领按钮
        for i in range(35):
            ratio = i / 35
            btn_color = (
                int(60 * (1 - ratio) + 100 * ratio),
                int(180 * (1 - ratio) + 220 * ratio),
                int(60 * (1 - ratio) + 100 * ratio)
            )
            pygame.draw.line(surface, btn_color, (btn_rect.x, btn_rect.y + i), 
                           (btn_rect.x + btn_rect.width, btn_rect.y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], btn_rect, 2, border_radius=8)
        btn_text = font_small.render("✨ 占领" if not capturing else "放弃占领", True, COLORS["text_white"])
    else:
        # 攻击按钮
        for i in range(35):
            ratio = i / 35
            btn_color = (
                int(220 * (1 - ratio) + 255 * ratio),
                int(60 * (1 - ratio) + 100 * ratio),
                int(60 * (1 - ratio) + 100 * ratio)
            )
            pygame.draw.line(surface, btn_color, (btn_rect.x, btn_rect.y + i), 
                           (btn_rect.x + btn_rect.width, btn_rect.y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], btn_rect, 2, border_radius=8)
        btn_text = font_small.render("⚔️ 攻击", True, COLORS["text_white"])
    
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    surface.blit(btn_text, btn_text_rect)
    
    return btn_rect, time_card_btn

def draw_ui_panel(surface, screen_width, screen_height, font):
    """绘制UI面板"""
    # 顶部信息栏
    panel_height = 50
    panel_surf = pygame.Surface((screen_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (25, 25, 45, 200), (0, 0, screen_width, panel_height))
    surface.blit(panel_surf, (0, 0))
    pygame.draw.line(surface, COLORS["accent_gold"], (0, panel_height), (screen_width, panel_height), 2)
    
    # 标题
    title = font.render("🗺️ 世界地图", True, COLORS["accent_gold"])
    surface.blit(title, (20, 12))
    
    # 返回按钮（自适应）
    return_btn_width = min(80, screen_width * 0.12)
    return_btn_height = min(30, screen_height * 0.06)
    return_btn = pygame.Rect(screen_width - return_btn_width - 10, 10, return_btn_width, return_btn_height)
    pygame.draw.rect(surface, (60, 120, 60), return_btn, border_radius=5)
    pygame.draw.rect(surface, (80, 160, 80), return_btn, 2, border_radius=5)
    return_text = font.render("↩️ 返回", True, COLORS["text_white"])
    return_text_rect = return_text.get_rect(center=return_btn.center)
    surface.blit(return_text, return_text_rect)
    
    # 操作提示（根据屏幕宽度自适应字体大小）
    hint_text = font.render("左键拖动 | 右键选中 | 滚轮缩放 | R重置", True, COLORS["text_gray"])
    hint_rect = hint_text.get_rect(right=screen_width - return_btn_width - 20, centery=panel_height // 2)
    surface.blit(hint_text, hint_rect)
    
    return return_btn

def main():
    """地图主函数"""
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
            SCREEN_WIDTH = 800
            SCREEN_HEIGHT = 600
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🗺️ 游戏地图")
        clock = pygame.time.Clock()

        # 地图配置
        MAP_SIZE = (10000, 10000)
        MAX_LOCATIONS = data["settings"]["map"]["max_locations"]
        DRAW_RADIUS = 18 if not 'ANDROID_DATA' in os.environ else 28

        # 字体初始化
        def init_font(size):
            return get_font(size)

        font_small = init_font(16 if not 'ANDROID_DATA' in os.environ else 22)
        font_main = init_font(20 if not 'ANDROID_DATA' in os.environ else 26)

        # 加载音效
        click_sound = load_sound("click.wav")

        def play_sound(sound):
            if sound and data['settings']['sound']['enable']:
                try:
                    sound.play()
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

        # 生成地图地点
        def generate_map(num_locations):
            locations = []
            map_w, map_h = MAP_SIZE

            for _ in range(num_locations):
                while True:
                    x = random.randint(0, map_w)
                    y = random.randint(0, map_h)
                    valid = True
                    for (lx, ly, _, _, _) in locations:
                        if math.hypot(x - lx, y - ly) < 150:
                            valid = False
                            break
                    if valid:
                        break

                loc_type = random.choice(list(LOCATION_TYPES.keys()))
                level = random.randint(1, 10)
                output = {k: v * level for k, v in LOCATION_TYPES[loc_type]["output"].items()}
                locations.append((x, y, loc_type, level, output))

            return locations

        # 占领地点
        def occupy_location(loc):
            x, y, loc_type, level, output = loc
            if not LOCATION_TYPES[loc_type]["hostile"]:
                for res, amt in output.items():
                    data["resources"][res] = data["resources"].get(res, 0) + amt
                save()
                return True, output
            return False, {}

        # 初始化地图
        locations = generate_map(MAX_LOCATIONS)
        view_offset = [0, 0]
        zoom_level = 1.0
        min_zoom = 0.5
        max_zoom = 10.0
        drag_start = None
        selected_loc = None
        hover_loc = None
        
        # 占领系统
        capturing_loc = None  # 当前正在占领的地点索引
        capture_start_time = 0  # 占领开始时间
        capture_duration = 1  # 基础占领时间（分钟）
        time_card_reduction = 0  # 时间卡减少的时间（分钟）
        
        # 时间卡等级配置
        TIME_CARD_LEVELS = {
            "时间卡": 0.5,  # 减少30秒
            "时间卡+": 1.0,  # 减少1分钟
            "时间卡++": 1.5   # 减少1分30秒
        }
        
        # 特效
        particles = []
        floating_texts = []
        
        # 背景星星
        stars = []
        for _ in range(50):
            stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'alpha': random.randint(50, 150),
                'twinkle': random.uniform(0.02, 0.05)
            })

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 绘制星星
            for star in stars:
                star['alpha'] += math.sin(pygame.time.get_ticks() * star['twinkle']) * 2
                star['alpha'] = max(30, min(150, star['alpha']))
                star_surf = pygame.Surface((star['size'] * 2, star['size'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(star_surf, (255, 255, 255, int(star['alpha'])), 
                                 (star['size'], star['size']), star['size'])
                screen.blit(star_surf, (star['x'], star['y']))
            
            # 绘制网格
            draw_grid(screen, view_offset[0], view_offset[1], SCREEN_WIDTH, SCREEN_HEIGHT)

            # 拖动地图
            if pygame.mouse.get_pressed()[0] and my > 50:  # 不在UI区域拖动
                if drag_start is None:
                    drag_start = (mx, my)
                else:
                    dx = mx - drag_start[0]
                    dy = my - drag_start[1]
                    view_offset[0] += dx
                    view_offset[1] += dy
                    drag_start = (mx, my)
            else:
                drag_start = None

            # 检测悬停
            hover_loc = None
            offset_x, offset_y = view_offset
            
            # 占领进度更新
            current_time = pygame.time.get_ticks() / 1000  # 转换为秒
            capture_progress = 0
            if capturing_loc is not None:
                elapsed_time = current_time - capture_start_time
                total_duration = max(0.1, (capture_duration - time_card_reduction) * 60)  # 转换为秒
                capture_progress = min(1.0, elapsed_time / total_duration)
                
                # 占领完成
                if elapsed_time >= total_duration:
                    loc = locations[capturing_loc]
                    success, output = occupy_location(loc)
                    
                    if success:
                        # 占领成功特效
                        screen_x = (loc[0] + offset_x) * zoom_level
                        screen_y = (loc[1] + offset_y) * zoom_level
                        
                        for _ in range(20):
                            particles.append(Particle(
                                screen_x, screen_y,
                                COLORS["accent_gold"],
                                4, random.randint(4, 8), 40
                            ))
                        
                        # 浮动文字
                        for res, amt in output.items():
                            floating_texts.append(FloatingText(
                                f"+{amt} {res}",
                                screen_x - 30, screen_y - 30,
                                COLORS["accent_gold"],
                                font_main
                            ))
                        
                        # 移除已占领的地点
                        locations.pop(capturing_loc)
                        if selected_loc == capturing_loc:
                            selected_loc = None
                    
                    capturing_loc = None
                    time_card_reduction = 0
            
            # 绘制地点
            for idx, (x, y, loc_type, level, output) in enumerate(locations):
                # 应用缩放
                screen_x = (x + offset_x) * zoom_level
                screen_y = (y + offset_y) * zoom_level
                scaled_radius = int(DRAW_RADIUS * zoom_level)

                if -50 <= screen_x <= SCREEN_WIDTH + 50 and -50 <= screen_y <= SCREEN_HEIGHT + 50:
                    # 检测悬停
                    is_hover = math.hypot(mx - screen_x, my - screen_y) <= scaled_radius + 5
                    if is_hover:
                        hover_loc = idx
                    
                    is_selected = (selected_loc == idx)
                    is_capturing = (capturing_loc == idx)
                    current_progress = capture_progress if is_capturing else 0
                    
                    draw_location(screen, int(screen_x), int(screen_y), loc_type, level, 
                                scaled_radius, font_small, is_selected, is_hover, 
                                is_capturing, current_progress)

            # 绘制选中弹窗
            occupy_btn = None
            time_card_btn = None
            if selected_loc is not None:
                loc = locations[selected_loc]
                # 使用选中地点的屏幕坐标，而不是鼠标坐标
                loc_x, loc_y = loc[0] + offset_x, loc[1] + offset_y
                popup_x = loc_x + 30
                popup_y = loc_y + 30
                
                # 确保弹窗不超出屏幕
                if popup_x + 220 > SCREEN_WIDTH:
                    popup_x = loc_x - 240
                if popup_y + 140 > SCREEN_HEIGHT:
                    popup_y = loc_y - 160
                
                # 计算时间卡总数
                time_card_count = 0
                for card_name in TIME_CARD_LEVELS:
                    time_card_count += data["resources"].get(card_name, 0)
                
                # 检查是否正在占领
                is_capturing = (capturing_loc == selected_loc)
                
                occupy_btn, time_card_btn = draw_popup(screen, popup_x, popup_y, loc, font_small, font_main, is_capturing, time_card_count)

            # 绘制UI面板
            return_btn = draw_ui_panel(screen, SCREEN_WIDTH, SCREEN_HEIGHT, font_small)

            # 更新和绘制粒子
            for p in particles[:]:
                p.update()
                p.draw(screen)

            # 更新和绘制浮动文字
            for ft in floating_texts[:]:
                ft.update()
                ft.draw(screen)

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        view_offset = [0, 0]
                        zoom_level = 1.0
                    if event.key == pygame.K_ESCAPE:
                        running = False
                
                if event.type == pygame.MOUSEWHEEL:
                    # 滚轮缩放
                    if event.y > 0:
                        zoom_level = min(max_zoom, zoom_level + 0.1)
                    elif event.y < 0:
                        zoom_level = max(min_zoom, zoom_level - 0.1)
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 检查返回按钮
                    if return_btn.collidepoint(mx, my):
                        running = False
                    
                    if event.button == 3:  # 右键选中
                        for idx, (x, y, loc_type, level, output) in enumerate(locations):
                            # 应用缩放计算屏幕坐标
                            screen_x = (x + offset_x) * zoom_level
                            screen_y = (y + offset_y) * zoom_level
                            scaled_radius = int(DRAW_RADIUS * zoom_level)
                            
                            if math.hypot(mx - screen_x, my - screen_y) <= scaled_radius + 10:
                                selected_loc = idx
                                play_sound(click_sound)
                                
                                # 选中特效
                                for _ in range(10):
                                    particles.append(Particle(
                                        screen_x, screen_y,
                                        LOCATION_TYPES[loc_type]["glow"],
                                        3, random.randint(3, 6), 30
                                    ))
                                break
                    
                    elif event.button == 1:  # 左键点击
                        # 时间卡按钮点击
                        if selected_loc is not None and time_card_btn and time_card_btn.collidepoint(event.pos):
                            if capturing_loc == selected_loc:
                                # 检查时间卡（从高级到低级）
                                used_card = None
                                used_reduction = 0
                                for card_name, reduction in sorted(TIME_CARD_LEVELS.items(), key=lambda x: x[1], reverse=True):
                                    if data["resources"].get(card_name, 0) > 0:
                                        used_card = card_name
                                        used_reduction = reduction
                                        data["resources"][card_name] -= 1
                                        save()
                                        break
                                
                                if used_card:
                                    # 减少剩余占领时间
                                    current_time = pygame.time.get_ticks() / 1000
                                    elapsed_time = current_time - capture_start_time
                                    original_duration = (capture_duration - time_card_reduction) * 60
                                    remaining_time = max(0, original_duration - elapsed_time)
                                    
                                    # 应用时间卡减少
                                    new_remaining_time = max(0, remaining_time - (used_reduction * 60))
                                    
                                    # 更新占领开始时间，相当于加快进度
                                    capture_start_time = current_time - (original_duration - new_remaining_time)
                                    
                                    # 时间卡使用提示
                                    floating_texts.append(FloatingText(
                                        f"使用{used_card}减少占领时间！",
                                        mx, my - 30,
                                        COLORS["accent_gold"],
                                        font_main
                                    ))
                                    
                                    # 特效
                                    loc = locations[selected_loc]
                                    screen_x = (loc[0] + offset_x) * zoom_level
                                    screen_y = (loc[1] + offset_y) * zoom_level
                                    
                                    for _ in range(10):
                                        particles.append(Particle(
                                            screen_x, screen_y,
                                            COLORS["accent_blue"],
                                            3, random.randint(3, 6), 30
                                        ))
                                else:
                                    # 没有时间卡
                                    floating_texts.append(FloatingText(
                                        "没有时间卡可用！",
                                        mx, my - 30,
                                        (255, 100, 100),
                                        font_main
                                    ))
                        
                        # 占领按钮点击
                        elif selected_loc is not None and occupy_btn and occupy_btn.collidepoint(event.pos):
                            loc = locations[selected_loc]
                            if not LOCATION_TYPES[loc[2]]["hostile"]:
                                if capturing_loc == selected_loc:
                                    # 放弃占领
                                    capturing_loc = None
                                    time_card_reduction = 0
                                    floating_texts.append(FloatingText(
                                        "已放弃占领",
                                        mx, my - 30,
                                        COLORS["text_gray"],
                                        font_main
                                    ))
                                else:
                                    # 开始占领
                                    if capturing_loc is None:
                                        # 检查时间卡（从高级到低级）
                                        used_card = None
                                        for card_name, reduction in sorted(TIME_CARD_LEVELS.items(), key=lambda x: x[1], reverse=True):
                                            if data["resources"].get(card_name, 0) > 0:
                                                time_card_reduction = reduction
                                                data["resources"][card_name] -= 1
                                                save()
                                                used_card = card_name
                                                break
                                        
                                        if used_card:
                                            # 时间卡使用提示
                                            floating_texts.append(FloatingText(
                                                f"使用{used_card}减少占领时间！",
                                                mx, my - 30,
                                                COLORS["accent_gold"],
                                                font_main
                                            ))
                                        else:
                                            time_card_reduction = 0
                                        
                                        capturing_loc = selected_loc
                                        capture_start_time = pygame.time.get_ticks() / 1000  # 转换为秒
                                        play_sound(click_sound)
                                        
                                        # 占领开始特效
                                        screen_x = (loc[0] + offset_x) * zoom_level
                                        screen_y = (loc[1] + offset_y) * zoom_level
                                        
                                        for _ in range(10):
                                            particles.append(Particle(
                                                screen_x, screen_y,
                                                COLORS["accent_gold"],
                                                2, random.randint(3, 5), 20
                                            ))
                                        
                                        # 占领开始提示
                                        total_time = max(0.1, capture_duration - time_card_reduction)
                                        floating_texts.append(FloatingText(
                                            f"开始占领... 需要 {total_time:.1f} 分钟",
                                            screen_x - 60, screen_y - 40,
                                            COLORS["accent_gold"],
                                            font_main
                                        ))
                                    else:
                                        # 已在占领其他地点
                                        floating_texts.append(FloatingText(
                                            "已在占领其他地点！",
                                            mx, my - 30,
                                            (255, 100, 100),
                                            font_main
                                        ))
                            else:
                                # 攻击敌对单位
                                import random
                                # 计算奖励
                                level = loc[3]
                                gold_reward = random.randint(10 * level, 30 * level)
                                other_rewards = []
                                
                                # 随机生成其他奖励
                                resource_types = ["水", "煤炭", "木头", "食物"]
                                num_other_rewards = random.randint(1, 3)
                                for _ in range(num_other_rewards):
                                    resource = random.choice(resource_types)
                                    amount = random.randint(5 * level, 15 * level)
                                    other_rewards.append((resource, amount))
                                
                                # 显示攻击成功和奖励信息
                                floating_texts.append(FloatingText(
                                    f"攻击成功！获得金元宝 {gold_reward}",
                                    mx, my - 30,
                                    COLORS["accent_gold"],
                                    font_main
                                ))
                                
                                for resource, amount in other_rewards:
                                    floating_texts.append(FloatingText(
                                        f"+{amount} {resource}",
                                        mx, my - 60 - len(other_rewards) * 20,
                                        COLORS["accent_blue"],
                                        font_main
                                    ))
                                
                                # 保存奖励
                                data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + gold_reward
                                for resource, amount in other_rewards:
                                    data["resources"][resource] = data["resources"].get(resource, 0) + amount
                                save()
                                
                                # 攻击特效
                                screen_x = (loc[0] + offset_x) * zoom_level
                                screen_y = (loc[1] + offset_y) * zoom_level
                                
                                for _ in range(20):
                                    particles.append(Particle(
                                        screen_x, screen_y,
                                        (255, 100, 100),  # 红色粒子
                                        5, random.randint(4, 8), 40
                                    ))
                                
                                # 移除被攻击的敌对单位
                                locations.pop(selected_loc)
                                selected_loc = None
                                play_sound(click_sound)

            pygame.display.flip()
            clock.tick(60)

        safe_exit("地图模块")
    except Exception as e:
        safe_exit("地图模块", str(e))

if __name__ == "__main__":
    main()
