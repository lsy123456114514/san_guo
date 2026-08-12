"""PvP 点对点联机对战协议层"""

import os
import pygame
import platform
import random
import math
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
from ASSET import safe_exit

# 颜色主题
COLORS = {
    "bg_dark": (15, 15, 35),
    "bg_light": (25, 25, 50),
    "accent_gold": (255, 215, 0),
    "accent_red": (220, 60, 60),
    "accent_green": (60, 220, 60),
    "accent_blue": (70, 130, 180),
    "accent_blue_light": (100, 149, 237),
    "accent_blue_dark": (50, 100, 150),
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 200),
    "panel_bg": (40, 40, 70, 200)
}

class Particle:
    """粒子效果 - 支持普通圆形与星形闪烁粒子"""
    def __init__(self, x, y, color, speed, size, life, particle_type="normal"):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = random.uniform(-speed, speed)
        self.speed_y = random.uniform(-speed, speed)
        self.size = size
        self.life = life
        self.max_life = life
        self.type = particle_type
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        if self.type == "sparkle":
            self.size = max(0, self.size - 0.2)
        else:
            self.size = max(1, self.size - 0.1)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        if self.type == "sparkle":
            # 星形粒子
            points = []
            for i in range(5):
                angle = math.pi * 2 * i / 5 - math.pi / 2
                px = self.x + math.cos(angle) * self.size
                py = self.y + math.sin(angle) * self.size
                points.append((px, py))
                angle = math.pi * 2 * (i + 0.5) / 5 - math.pi / 2
                px = self.x + math.cos(angle) * (self.size * 0.5)
                py = self.y + math.sin(angle) * (self.size * 0.5)
                points.append((px, py))
            pygame.draw.polygon(surface, self.color, points)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class AnimatedButton:
    """动画按钮 - 悬停缩放、发光与星形粒子特效"""
    def __init__(self, text, x, y, width, height, font, 
                 normal_color=COLORS["accent_blue"], 
                 hover_color=COLORS["accent_blue_light"], 
                 text_color=COLORS["text_white"],
                 icon=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.is_clicked = False
        self.click_timer = 0
        self.icon = icon
        self.particles = []
        self.glow_alpha = 0
        self.scale = 1.0
        self.target_scale = 1.0
    
    def draw(self, surface):
        # 缩放动画
        if self.is_hovered:
            self.target_scale = 1.05
        else:
            self.target_scale = 1.0
        self.scale += (self.target_scale - self.scale) * 0.1
        
        # 计算缩放后的矩形
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_x = self.rect.x + (self.rect.width - scaled_width) // 2
        scaled_y = self.rect.y + (self.rect.height - scaled_height) // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        # 发光效果
        if self.is_hovered:
            self.glow_alpha = min(120, self.glow_alpha + 8)
        else:
            self.glow_alpha = max(0, self.glow_alpha - 8)
        
        if self.glow_alpha > 0:
            for offset in range(3, 0, -1):
                glow_surf = pygame.Surface((scaled_width + offset * 10, scaled_height + offset * 10), pygame.SRCALPHA)
                alpha = self.glow_alpha // offset
                pygame.draw.rect(glow_surf, (*self.hover_color[:3], alpha), 
                               (0, 0, scaled_width + offset * 10, scaled_height + offset * 10), border_radius=15)
                surface.blit(glow_surf, (scaled_x - offset * 5, scaled_y - offset * 5))
        
        # 按钮颜色
        color = self.hover_color if self.is_hovered else self.normal_color
        if self.is_clicked:
            color = COLORS["accent_blue_dark"]
        
        # 渐变效果
        for i in range(scaled_height):
            ratio = i / scaled_height
            gradient_color = (
                int(color[0] * (1 - ratio) + min(255, color[0] + 30) * ratio),
                int(color[1] * (1 - ratio) + min(255, color[1] + 30) * ratio),
                int(color[2] * (1 - ratio) + min(255, color[2] + 30) * ratio)
            )
            pygame.draw.line(surface, gradient_color, 
                           (scaled_x, scaled_y + i),
                           (scaled_x + scaled_width, scaled_y + i))
        
        # 按钮边框
        pygame.draw.rect(surface, COLORS["text_white"], scaled_rect, 2, border_radius=10)
        pygame.draw.rect(surface, COLORS["accent_gold"], scaled_rect, 1, border_radius=10)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        # 文字阴影
        shadow_surf = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)
        
        # 粒子效果
        if self.is_hovered and random.random() < 0.4:
            self.particles.append(Particle(
                random.randint(scaled_x, scaled_x + scaled_width),
                random.randint(scaled_y, scaled_y + scaled_height),
                COLORS["accent_gold"], 1.5, random.randint(2, 4), 40, "sparkle"
            ))
        
        for p in self.particles:
            p.update()
            p.draw(surface)
        self.particles[:] = [p for p in self.particles if p.life > 0]

    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def check_click(self, mouse_pos):
        if self.is_hovered and pygame.mouse.get_pressed()[0]:
            if not self.is_clicked:
                self.is_clicked = True
                self.click_timer = pygame.time.get_ticks()
                return True
        elif self.is_clicked:
            if pygame.time.get_ticks() - self.click_timer > 200:
                self.is_clicked = False
        return False

def draw_title(surface, text, y_pos, screen_width, font, color=COLORS["accent_gold"]):
    """绘制带特效的标题"""
    # 发光效果
    for offset in range(5, 0, -1):
        alpha = max(0, 60 - offset * 10)
        glow_surf = font.render(text, True, (*color[:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    surface.blit(glow_surf, (glow_rect.x + dx, glow_rect.y + dy))
    
    # 主标题
    title = font.render(text, True, color)
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    
    # 阴影
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)
    
    # 装饰线
    line_y = y_pos + font.get_height() // 2 + 15
    pygame.draw.line(surface, color, 
                    (screen_width // 2 - 120, line_y),
                    (screen_width // 2 - 40, line_y), 3)
    pygame.draw.line(surface, color,
                    (screen_width // 2 + 40, line_y),
                    (screen_width // 2 + 120, line_y), 3)
    # 中间装饰
    pygame.draw.circle(surface, color, (screen_width // 2, line_y), 6)
    pygame.draw.circle(surface, COLORS["bg_dark"], (screen_width // 2, line_y), 4)

def draw_battle_effect(surface, screen_width, screen_height, progress):
    """绘制战斗特效"""
    # 闪光效果
    if progress < 0.3:
        alpha = int(255 * (1 - progress / 0.3))
        flash_surf = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        flash_surf.fill((255, 255, 255, alpha))
        surface.blit(flash_surf, (0, 0))
    
    # 冲击波
    center_x, center_y = screen_width // 2, screen_height // 2
    max_radius = max(screen_width, screen_height) // 2
    for i in range(3):
        radius = int(max_radius * (progress + i * 0.2) % max_radius)
        alpha = int(150 * (1 - radius / max_radius))
        if alpha > 0:
            pygame.draw.circle(surface, (*COLORS["accent_gold"][:3], alpha), 
                             (center_x, center_y), radius, 3)

def main():
    """P2P联机主函数"""
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
            # 使用设置的分辨率
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 800
                SCREEN_HEIGHT = 600
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("⚔️ PVP联机对战")
        clock = pygame.time.Clock()

        # 字体初始化
        def init_font(size):
            return get_font(size)

        font_main = init_font(28 if not 'ANDROID_DATA' in os.environ else 40)
        font_small = init_font(22 if not 'ANDROID_DATA' in os.environ else 30)
        font_big = init_font(48 if not 'ANDROID_DATA' in os.environ else 60)

        # 游戏状态
        state = "main"
        opponent = None
        battle_result = None
        battle_progress = 0
        battle_start_time = 0

        # 模拟对手列表
        opponents = [
            {"name": "新手战士", "level": 5, "power": 500, "rank": "青铜", "color": (180, 120, 80)},
            {"name": "精英骑士", "level": 12, "power": 1200, "rank": "白银", "color": (180, 180, 200)},
            {"name": "皇家卫士", "level": 18, "power": 1800, "rank": "黄金", "color": (255, 215, 0)},
            {"name": "传说英雄", "level": 25, "power": 2500, "rank": "钻石", "color": (100, 200, 255)}
        ]

        # 按钮
        buttons = []
        def create_buttons():
            buttons.clear()
            if state == "main":
                btn_width = 280 if not 'ANDROID_DATA' in os.environ else 350
                btn_height = 60 if not 'ANDROID_DATA' in os.environ else 70
                start_y = SCREEN_HEIGHT * 0.35
                spacing = 80
                
                buttons.append(AnimatedButton("⚡ 快速匹配", (SCREEN_WIDTH - btn_width)//2, start_y, btn_width, btn_height, font_small, 
                                            normal_color=COLORS["accent_green"]))
                buttons.append(AnimatedButton("👥 挑战玩家", (SCREEN_WIDTH - btn_width)//2, start_y + spacing, btn_width, btn_height, font_small))
                buttons.append(AnimatedButton("🔙 返回主菜单", (SCREEN_WIDTH - btn_width)//2, start_y + spacing * 2, btn_width, btn_height, font_small,
                                            normal_color=(100, 100, 130)))
            elif state == "opponents":
                btn_width = 350 if not 'ANDROID_DATA' in os.environ else 450
                btn_height = 55 if not 'ANDROID_DATA' in os.environ else 65
                start_y = SCREEN_HEIGHT * 0.25
                spacing = 70
                
                for i, opp in enumerate(opponents):
                    color = opp["color"]
                    buttons.append(AnimatedButton(f"{opp['name']} | Lv{opp['level']} | {opp['rank']}", 
                                               (SCREEN_WIDTH - btn_width)//2, start_y + i * spacing, btn_width, btn_height, font_small,
                                               normal_color=color))
                buttons.append(AnimatedButton("🔙 返回", (SCREEN_WIDTH - btn_width)//2, start_y + len(opponents) * spacing + 20, btn_width, btn_height, font_small,
                                            normal_color=(100, 100, 130)))
            elif state == "battle":
                pass
            elif state == "result":
                btn_width = 250 if not 'ANDROID_DATA' in os.environ else 320
                btn_height = 60 if not 'ANDROID_DATA' in os.environ else 70
                
                result_color = COLORS["accent_green"] if battle_result == "win" else COLORS["accent_red"]
                buttons.append(AnimatedButton("🔄 再次挑战", (SCREEN_WIDTH - btn_width)//2, SCREEN_HEIGHT * 0.65, btn_width, btn_height, font_small,
                                            normal_color=result_color))
                buttons.append(AnimatedButton("🔙 返回主菜单", (SCREEN_WIDTH - btn_width)//2, SCREEN_HEIGHT * 0.75, btn_width, btn_height, font_small,
                                            normal_color=(100, 100, 130)))

        create_buttons()

        # 背景粒子
        bg_particles = []
        for _ in range(30):
            bg_particles.append(Particle(
                random.randint(0, SCREEN_WIDTH),
                random.randint(0, SCREEN_HEIGHT),
                COLORS["accent_gold"], 0.3, random.randint(1, 3), random.randint(100, 200), "normal"
            ))

        # 主循环
        running = True
        while running:
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 更新和绘制背景粒子
            for p in bg_particles:
                p.update()
                if p.x < 0 or p.x > SCREEN_WIDTH or p.y < 0 or p.y > SCREEN_HEIGHT or p.life <= 0:
                    p.x = random.randint(0, SCREEN_WIDTH)
                    p.y = random.randint(0, SCREEN_HEIGHT)
                    p.life = p.max_life
                p.draw(screen)
            
            mouse_pos = pygame.mouse.get_pos()

            if state == "main":
                # 标题
                draw_title(screen, "PVP联机对战", SCREEN_HEIGHT * 0.12, SCREEN_WIDTH, font_big)
                
                # 玩家信息面板
                panel_width = 400
                panel_height = 80
                panel_x = (SCREEN_WIDTH - panel_width) // 2
                panel_y = SCREEN_HEIGHT * 0.22
                
                # 面板背景
                panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
                pygame.draw.rect(panel_surf, (40, 40, 70, 180), (0, 0, panel_width, panel_height), border_radius=15)
                screen.blit(panel_surf, (panel_x, panel_y))
                pygame.draw.rect(screen, COLORS["accent_gold"], (panel_x, panel_y, panel_width, panel_height), 2, border_radius=15)
                
                # 玩家信息
                player_level = data.get('player_level', 1)
                player_power = data.get('player_power', 1000)
                player_info = f"🏆 等级: {player_level}  |  ⚔️ 战力: {player_power}"
                info_text = font_small.render(player_info, True, COLORS["text_white"])
                info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + panel_height // 2))
                screen.blit(info_text, info_rect)

            elif state == "opponents":
                # 标题
                draw_title(screen, "选择对手", SCREEN_HEIGHT * 0.12, SCREEN_WIDTH, font_big)
                
                # 提示文字
                tip_text = font_small.render("点击选择要挑战的对手", True, COLORS["text_gray"])
                tip_rect = tip_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.2))
                screen.blit(tip_text, tip_rect)

            elif state == "battle":
                # 计算战斗进度
                if battle_start_time > 0:
                    elapsed = pygame.time.get_ticks() - battle_start_time
                    battle_progress = min(1.0, elapsed / 2000)
                
                # 战斗特效
                draw_battle_effect(screen, SCREEN_WIDTH, SCREEN_HEIGHT, battle_progress)
                
                # 标题
                draw_title(screen, "战斗中...", SCREEN_HEIGHT * 0.15, SCREEN_WIDTH, font_big, COLORS["accent_red"])
                
                if opponent:
                    # VS 文字
                    vs_text = font_big.render("VS", True, COLORS["accent_red"])
                    vs_rect = vs_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.4))
                    screen.blit(vs_text, vs_rect)
                    
                    # 对手信息
                    opp_text = font_main.render(f"{opponent['name']}", True, opponent['color'])
                    opp_rect = opp_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.5))
                    screen.blit(opp_text, opp_rect)
                    
                    # 进度条
                    bar_width = 300
                    bar_height = 20
                    bar_x = (SCREEN_WIDTH - bar_width) // 2
                    bar_y = SCREEN_HEIGHT * 0.6
                    
                    # 进度条背景
                    pygame.draw.rect(screen, (50, 50, 70), (bar_x, bar_y, bar_width, bar_height), border_radius=10)
                    # 进度条填充
                    fill_width = int(bar_width * battle_progress)
                    if fill_width > 0:
                        pygame.draw.rect(screen, COLORS["accent_gold"], (bar_x, bar_y, fill_width, bar_height), border_radius=10)
                    # 进度条边框
                    pygame.draw.rect(screen, COLORS["text_white"], (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)

            elif state == "result":
                # 结果标题
                result_color = COLORS["accent_green"] if battle_result == "win" else COLORS["accent_red"]
                result_text = "🎉 胜利！" if battle_result == "win" else "💔 失败！"
                draw_title(screen, "战斗结果", SCREEN_HEIGHT * 0.12, SCREEN_WIDTH, font_big)
                
                # 结果显示
                result_surf = font_big.render(result_text, True, result_color)
                result_rect = result_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.3))
                # 发光效果
                for offset in range(3, 0, -1):
                    glow_surf = font_big.render(result_text, True, (*result_color[:3], 50))
                    screen.blit(glow_surf, (result_rect.x - offset, result_rect.y))
                    screen.blit(glow_surf, (result_rect.x + offset, result_rect.y))
                screen.blit(result_surf, result_rect)
                
                # 奖励面板
                panel_width = 350
                panel_height = 120
                panel_x = (SCREEN_WIDTH - panel_width) // 2
                panel_y = SCREEN_HEIGHT * 0.4
                
                panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
                pygame.draw.rect(panel_surf, (40, 40, 70, 200), (0, 0, panel_width, panel_height), border_radius=15)
                screen.blit(panel_surf, (panel_x, panel_y))
                pygame.draw.rect(screen, COLORS["accent_gold"], (panel_x, panel_y, panel_width, panel_height), 2, border_radius=15)
                
                if battle_result == "win":
                    reward_title = font_main.render("🎁 战斗奖励", True, COLORS["accent_gold"])
                    reward_text = font_small.render("获得: 金元宝 x50", True, COLORS["text_white"])
                    data['resources']['金元宝'] = data['resources'].get('金元宝', 0) + 50
                    save()
                else:
                    reward_title = font_main.render("📖 经验积累", True, COLORS["accent_blue_light"])
                    reward_text = font_small.render("获得: 经验值 +10", True, COLORS["text_white"])
                
                title_rect = reward_title.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 35))
                text_rect = reward_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 75))
                screen.blit(reward_title, title_rect)
                screen.blit(reward_text, text_rect)

            # 绘制按钮
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(screen)

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, btn in enumerate(buttons):
                        if btn.check_click(mouse_pos):
                            if state == "main":
                                if i == 0:  # 快速匹配
                                    opponent = random.choice(opponents)
                                    state = "battle"
                                    battle_start_time = pygame.time.get_ticks()
                                    battle_progress = 0
                                    pygame.time.set_timer(pygame.USEREVENT, 2500)
                                elif i == 1:  # 挑战玩家
                                    state = "opponents"
                                    create_buttons()
                                elif i == 2:  # 返回主菜单
                                    running = False
                            elif state == "opponents":
                                if i < len(opponents):  # 选择对手
                                    opponent = opponents[i]
                                    state = "battle"
                                    battle_start_time = pygame.time.get_ticks()
                                    battle_progress = 0
                                    pygame.time.set_timer(pygame.USEREVENT, 2500)
                                else:  # 返回
                                    state = "main"
                                    create_buttons()
                            elif state == "result":
                                if i == 0:  # 再次挑战
                                    state = "battle"
                                    battle_start_time = pygame.time.get_ticks()
                                    battle_progress = 0
                                    pygame.time.set_timer(pygame.USEREVENT, 2500)
                                elif i == 1:  # 返回主菜单
                                    running = False
                if event.type == pygame.USEREVENT:
                    # 战斗结束
                    pygame.time.set_timer(pygame.USEREVENT, 0)
                    # 根据战力计算胜率
                    player_power = data.get('player_power', 1000)
                    if opponent:
                        power_diff = player_power - opponent['power']
                        win_chance = 0.5 + (power_diff / 2000)  # 基础50%胜率，根据战力差调整
                        win_chance = max(0.2, min(0.8, win_chance))  # 限制在20%-80%
                        battle_result = "win" if random.random() < win_chance else "lose"
                    else:
                        battle_result = "win" if random.random() > 0.3 else "lose"
                    state = "result"
                    create_buttons()

            pygame.display.flip()
            clock.tick(60)

        return
    except Exception as e:
        logger.info(f"PVP模块异常：{str(e)}")
        return

if __name__ == "__main__":
    main()
