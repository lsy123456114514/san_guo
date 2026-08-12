"""排行榜系统 - 战力/胜场/副本进度榜单"""

import os
import pygame
import json
import random
import math
from ASSET.game_data import data, save, logger, draw_gradient_bg, cull_dead, get_font
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
    "btn_blue_hover": (80, 160, 255)
}

class Button:
    """按钮控件 - 悬停变色与文字渲染"""
    def __init__(self, text, x, y, width, height, font):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.is_hovered = False
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        color = (50, 60, 90) if not self.is_hovered else (60, 70, 110)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class ScrollableContainer:
    """滚动容器 - 支持滚轮拖拽与项目渲染的列表区域"""
    def __init__(self, x, y, width, height, item_height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.item_height = item_height
        self.scroll_offset = 0
        self.is_scrolling = False
        self.last_mouse_y = 0
        
    def set_items(self, items):
        self.items = items
        self.max_scroll = max(0, len(items) * self.item_height - self.height)
        
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
    
    def get_item_at(self, mouse_x, mouse_y):
        if not self.is_mouse_in_container((mouse_x, mouse_y)):
            return None
        item_index = (mouse_y - self.y + self.scroll_offset) // self.item_height
        if 0 <= item_index < len(self.items):
            return self.items[item_index]
        return None
    
    def draw(self, surface):
        container_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        clip_rect = pygame.Rect(0, 0, self.width, self.height)
        container_surface.set_clip(clip_rect)
        
        for i, item in enumerate(self.items):
            item_y = self.y + i * self.item_height - self.scroll_offset
            if -self.item_height <= item_y <= self.height:
                self.render_item(container_surface, item, self.x, item_y, i)
        
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

class RankingScrollContainer(ScrollableContainer):
    """排行榜滚动容器 - 渲染名次、玩家与得分的排行项"""
    def __init__(self, x, y, width, height, item_height, items, font_small, ranking_types, current_ranking):
        super().__init__(x, y, width, height, item_height)
        self.items = items
        self.font_small = font_small
        self.ranking_types = ranking_types
        self.current_ranking = current_ranking
        self.max_scroll = max(0, len(items) * item_height - height)
        
    def render_item(self, surface, item, x, y, i):
        rank_text = self.font_small.render(str(i + 1), True, COLORS["text_white"])
        surface.blit(rank_text, (x + 10, y + 5))
        
        player_text = self.font_small.render(item['player'], True, COLORS["text_white"])
        surface.blit(player_text, (x + 40, y + 5))
        
        if self.ranking_types[self.current_ranking][1] == 'pvp_wins':
            score = item['wins']
        elif self.ranking_types[self.current_ranking][1] == 'total_play_time':
            score = item['time']
        else:
            score = item['achievements']
        
        ranking_unit = self.ranking_types[self.current_ranking][2]
        score_text = self.font_small.render(f"{score} {ranking_unit}", True, COLORS["accent_green"])
        surface.blit(score_text, (x + self.width - 150, y + 5))

class Particle:
    """粒子效果 - 带透明度渐变的圆形粒子"""
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
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        color = (*self.color[:3], alpha)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

def draw_title(surface, text, y, screen_width):
    """绘制标题"""
    font = get_font(48)
    title_surf = font.render(text, True, COLORS["accent_gold"])
    title_rect = title_surf.get_rect(center=(screen_width // 2, y))
    surface.blit(title_surf, title_rect)
    
    # 标题下划线
    underline_width = title_rect.width * 1.2
    underline_x = (screen_width - underline_width) // 2
    pygame.draw.line(surface, COLORS["accent_gold"], 
                   (underline_x, y + 35), (underline_x + underline_width, y + 35), 3)

def get_system_font_name():
    """获取系统字体名称"""
    if 'ANDROID_DATA' in os.environ:
        return None
    
    # 尝试常见的中文字体
    fonts = ["Microsoft YaHei", "SimHei", "Arial", "sans-serif"]
    for font in fonts:
        try:
            test_font = pygame.font.SysFont(font, 24)
            if test_font:
                return font
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
    return None

def main():
    """排行榜系统主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
            pygame.mixer.init()
        
        # 分辨率适配：优先复用当前显示表面，避免返回主菜单错位
        cur_surface = pygame.display.get_surface()
        if cur_surface is not None:
            SCREEN_WIDTH, SCREEN_HEIGHT = cur_surface.get_size()
            screen = cur_surface
        else:
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
        pygame.display.set_caption("排行榜系统")
        clock = pygame.time.Clock()

        # 计算缩放因子
        scale = min(SCREEN_WIDTH / 900, SCREEN_HEIGHT / 700)

        # 字体初始化（根据屏幕大小自适应）
        def init_font(size):
            return get_font(size)

        font_title = init_font(36 if not 'ANDROID_DATA' in os.environ else 52)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)

        # 确保排行榜数据存在
        if 'rankings' not in data:
            data['rankings'] = {
                'pvp_wins': [],
                'mini_game_scores': {},
                'total_play_time': [],
                'achievements_unlocked': []
            }
            save()

        # 排行榜数据
        rankings = data['rankings']

        # 生成示例数据（如果排行榜为空）
        if not rankings['pvp_wins']:
            # 生成示例PVP胜利排行
            sample_players = ["玩家1", "玩家2", "玩家3", "玩家4", "玩家5", "玩家6", "玩家7", "玩家8", "玩家9", "玩家10"]
            for player in sample_players:
                rankings['pvp_wins'].append({
                    'player': player,
                    'wins': random.randint(1, 100)
                })
            # 按胜利次数排序
            rankings['pvp_wins'].sort(key=lambda x: x['wins'], reverse=True)
            save()

        if not rankings['total_play_time']:
            # 生成示例游戏时间排行
            sample_players = ["玩家1", "玩家2", "玩家3", "玩家4", "玩家5", "玩家6", "玩家7", "玩家8", "玩家9", "玩家10"]
            for player in sample_players:
                rankings['total_play_time'].append({
                    'player': player,
                    'time': random.randint(60, 3600)
                })
            # 按游戏时间排序
            rankings['total_play_time'].sort(key=lambda x: x['time'], reverse=True)
            save()

        if not rankings['achievements_unlocked']:
            # 生成示例成就解锁排行
            sample_players = ["玩家1", "玩家2", "玩家3", "玩家4", "玩家5", "玩家6", "玩家7", "玩家8", "玩家9", "玩家10"]
            for player in sample_players:
                rankings['achievements_unlocked'].append({
                    'player': player,
                    'achievements': random.randint(1, 20)
                })
            # 按成就数量排序
            rankings['achievements_unlocked'].sort(key=lambda x: x['achievements'], reverse=True)
            save()

        # 排行榜类型
        ranking_types = [
            ("PVP胜利次数", "pvp_wins", "胜利次数"),
            ("游戏总时间", "total_play_time", "分钟"),
            ("成就解锁数", "achievements_unlocked", "个")
        ]
        current_ranking = 0

        # 装饰粒子
        particles = []

        # 主循环
        running = True
        scroll_container = None
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 装饰粒子
            if random.random() < 0.1:
                particles.append(Particle(
                    random.randint(0, SCREEN_WIDTH),
                    random.randint(0, SCREEN_HEIGHT),
                    COLORS["accent_gold"], 0.5, 2, 100
                ))
            
            for p in particles[:]:
                p.update()
                p.draw(screen)

            # 标题
            draw_title(screen, "排行榜系统", SCREEN_HEIGHT * 0.12, SCREEN_WIDTH)

            # 排行榜类型选择
            type_buttons = []
            type_start_x = (SCREEN_WIDTH - len(ranking_types) * 200) // 2
            type_start_y = SCREEN_HEIGHT * 0.22
            
            for i, (name, key, unit) in enumerate(ranking_types):
                x = type_start_x + i * 200
                y = type_start_y
                btn = Button(name, x, y, 180, 40, font_small)
                btn.check_hover((mx, my))
                btn.draw(screen)
                type_buttons.append((btn, i))
                
                if i == current_ranking:
                    pygame.draw.rect(screen, COLORS["accent_gold"], 
                                   (x, y, 180, 40), 2, border_radius=8)

            # 显示排行榜
            ranking_data = rankings[ranking_types[current_ranking][1]]
            ranking_name = ranking_types[current_ranking][0]
            ranking_unit = ranking_types[current_ranking][2]

            # 排行榜标题
            ranking_title = font_normal.render(f"{ranking_name}排行榜", True, COLORS["accent_blue"])
            ranking_title_rect = ranking_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.32))
            screen.blit(ranking_title, ranking_title_rect)

            # 排行榜列表
            list_start_y = SCREEN_HEIGHT * 0.4
            list_width = min(600, SCREEN_WIDTH * 0.7)
            list_x = (SCREEN_WIDTH - list_width) // 2
            list_height = min(400, SCREEN_HEIGHT * 0.5)

            # 列表背景
            list_surf = pygame.Surface((list_width, list_height), pygame.SRCALPHA)
            pygame.draw.rect(list_surf, (35, 40, 60, 200), (0, 0, list_width, list_height), border_radius=12)
            screen.blit(list_surf, (list_x, list_start_y))
            pygame.draw.rect(screen, COLORS["accent_gold"], (list_x, list_start_y, list_width, list_height), 2, border_radius=12)

            # 表头
            header_font = font_small
            rank_header = header_font.render("排名", True, COLORS["accent_gold"])
            player_header = header_font.render("玩家", True, COLORS["accent_gold"])
            score_header = header_font.render(f"{ranking_name}", True, COLORS["accent_gold"])
            
            screen.blit(rank_header, (list_x + 30, list_start_y + 20))
            screen.blit(player_header, (list_x + 100, list_start_y + 20))
            screen.blit(score_header, (list_x + list_width - 150, list_start_y + 20))

            # 分隔线
            pygame.draw.line(screen, COLORS["accent_gold"], 
                           (list_x + 20, list_start_y + 50), (list_x + list_width - 20, list_start_y + 50), 2)

            # 创建滚动容器
            if scroll_container is None or scroll_container.items != ranking_data:
                scroll_container = RankingScrollContainer(
                    list_x + 10, list_start_y + 60, list_width - 20, list_height - 70, 35,
                    ranking_data, font_small, ranking_types, current_ranking
                )
            
            scroll_container.current_ranking = current_ranking
            scroll_container.draw(screen)

            # 返回按钮
            return_btn = Button("返回主菜单", (SCREEN_WIDTH - 200) // 2, SCREEN_HEIGHT - 80, 200, 50, font_normal)
            return_btn.check_hover((mx, my))
            return_btn.draw(screen)

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn, idx in type_buttons:
                        if btn.rect.collidepoint(mx, my):
                            current_ranking = idx
                            scroll_container = None
                            break
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
                
                if scroll_container:
                    scroll_container.handle_event(event)

            pygame.display.flip()
            clock.tick(60)

        return
    except Exception as e:
        logger.info(f"异常：{str(e)}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()