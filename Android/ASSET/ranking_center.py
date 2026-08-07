import os
import pygame
import random
import math
import json
from ASSET.game_data import data, save, get_system_font_name, load_sound
from ASSET import safe_exit

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
    "btn_gold_hover": (255, 200, 80),
    "rank_1": (255, 215, 0),
    "rank_2": (192, 192, 192),
    "rank_3": (205, 127, 50)
}

class Particle:
    def __init__(self, x, y, color, speed, size, life, gravity=0.1):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = random.uniform(-speed, speed)
        self.speed_y = random.uniform(-speed, speed)
        self.gravity = gravity
        self.size = size
        self.life = life
        self.max_life = life
    
    def update(self):
        self.speed_y += self.gravity
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        self.size = max(0.5, self.size - 0.05)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
        color = (*self.color[:3], alpha)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

class Button:
    def __init__(self, text, x, y, width, height, font, normal_color=COLORS["btn_blue"], hover_color=COLORS["btn_blue_hover"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.is_hovered = False
    
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.normal_color
        
        for i in range(self.rect.height):
            ratio = i / self.rect.height
            r = int(color[0] * (1 - ratio * 0.3))
            g = int(color[1] * (1 - ratio * 0.3))
            b = int(color[2] * (1 - ratio * 0.3))
            pygame.draw.line(surface, (r, g, b), 
                           (self.rect.x, self.rect.y + i), 
                           (self.rect.x + self.rect.width, self.rect.y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class RankingCenter:
    def __init__(self):
        self._init_data()
        self.ranking_types = self._load_ranking_types()
        self._generate_sample_data()
    
    def _init_data(self):
        if "ranking_center" not in data:
            data["ranking_center"] = {
                "pvp_wins": [],
                "total_play_time": [],
                "achievements_unlocked": [],
                "hero_power": [],
                "dungeon_floor": [],
                "guild_power": [],
                "total_battles": [],
                "mini_game_scores": {},
                "last_updated": {}
            }
            save()
    
    def _load_ranking_types(self):
        return [
            {"id": "pvp_wins", "name": "PVP胜利榜", "description": "竞技场胜利次数", "unit": "次", "icon": "⚔️"},
            {"id": "total_play_time", "name": "游戏时长榜", "description": "累计游戏时间", "unit": "分钟", "icon": "⏱️"},
            {"id": "achievements_unlocked", "name": "成就解锁榜", "description": "解锁成就数量", "unit": "个", "icon": "🏆"},
            {"id": "hero_power", "name": "武将战力榜", "description": "武将总战斗力", "unit": "战力", "icon": "💪"},
            {"id": "dungeon_floor", "name": "副本进度榜", "description": "通关副本层数", "unit": "层", "icon": "🏰"},
            {"id": "guild_power", "name": "军团战力榜", "description": "军团总战斗力", "unit": "战力", "icon": "👥"},
            {"id": "total_battles", "name": "战斗场次榜", "description": "总战斗次数", "unit": "场", "icon": "🔥"}
        ]
    
    def _generate_sample_data(self):
        sample_players = ["战神关羽", "卧龙诸葛", "猛张飞", "锦马超", "常山赵云", "霸王孙策", "小霸王", "无双吕布", "美周郎", "虎痴许褚"]
        
        if not data["ranking_center"]["pvp_wins"]:
            for player in sample_players:
                data["ranking_center"]["pvp_wins"].append({
                    "player": player,
                    "wins": random.randint(50, 500),
                    "avatar": random.choice(["⚔️", "🛡️", "🏹", "🗡️", "🔮"])
                })
            data["ranking_center"]["pvp_wins"].sort(key=lambda x: x["wins"], reverse=True)
        
        if not data["ranking_center"]["total_play_time"]:
            for player in sample_players:
                data["ranking_center"]["total_play_time"].append({
                    "player": player,
                    "time": random.randint(100, 5000),
                    "avatar": random.choice(["⚔️", "🛡️", "🏹", "🗡️", "🔮"])
                })
            data["ranking_center"]["total_play_time"].sort(key=lambda x: x["time"], reverse=True)
        
        if not data["ranking_center"]["achievements_unlocked"]:
            for player in sample_players:
                data["ranking_center"]["achievements_unlocked"].append({
                    "player": player,
                    "achievements": random.randint(5, 50),
                    "avatar": random.choice(["⚔️", "🛡️", "🏹", "🗡️", "🔮"])
                })
            data["ranking_center"]["achievements_unlocked"].sort(key=lambda x: x["achievements"], reverse=True)
        
        if not data["ranking_center"]["hero_power"]:
            for player in sample_players:
                data["ranking_center"]["hero_power"].append({
                    "player": player,
                    "power": random.randint(10000, 200000),
                    "avatar": random.choice(["⚔️", "🛡️", "🏹", "🗡️", "🔮"])
                })
            data["ranking_center"]["hero_power"].sort(key=lambda x: x["power"], reverse=True)
        
        if not data["ranking_center"]["dungeon_floor"]:
            for player in sample_players:
                data["ranking_center"]["dungeon_floor"].append({
                    "player": player,
                    "floor": random.randint(1, 100),
                    "avatar": random.choice(["⚔️", "🛡️", "🏹", "🗡️", "🔮"])
                })
            data["ranking_center"]["dungeon_floor"].sort(key=lambda x: x["floor"], reverse=True)
        
        if not data["ranking_center"]["guild_power"]:
            for player in sample_players:
                data["ranking_center"]["guild_power"].append({
                    "player": player,
                    "power": random.randint(50000, 500000),
                    "avatar": random.choice(["⚔️", "🛡️", "🏹", "🗡️", "🔮"])
                })
            data["ranking_center"]["guild_power"].sort(key=lambda x: x["power"], reverse=True)
        
        if not data["ranking_center"]["total_battles"]:
            for player in sample_players:
                data["ranking_center"]["total_battles"].append({
                    "player": player,
                    "battles": random.randint(100, 2000),
                    "avatar": random.choice(["⚔️", "🛡️", "🏹", "🗡️", "🔮"])
                })
            data["ranking_center"]["total_battles"].sort(key=lambda x: x["battles"], reverse=True)
        
        save()
    
    def get_ranking_data(self, ranking_id):
        return data["ranking_center"].get(ranking_id, [])
    
    def get_ranking_type(self, ranking_id):
        return next((r for r in self.ranking_types if r["id"] == ranking_id), None)
    
    def get_player_rank(self, player_name, ranking_id):
        data_list = data["ranking_center"].get(ranking_id, [])
        for i, item in enumerate(data_list):
            if item["player"] == player_name:
                return i + 1
        return None
    
    def update_ranking(self, ranking_id, player_name, value, avatar="⚔️"):
        data_list = data["ranking_center"].get(ranking_id, [])
        
        existing = next((item for item in data_list if item["player"] == player_name), None)
        if existing:
            key_map = {
                "pvp_wins": "wins",
                "total_play_time": "time",
                "achievements_unlocked": "achievements",
                "hero_power": "power",
                "dungeon_floor": "floor",
                "guild_power": "power",
                "total_battles": "battles"
            }
            key = key_map.get(ranking_id, "value")
            existing[key] = value
        else:
            key_map = {
                "pvp_wins": {"player": player_name, "wins": value, "avatar": avatar},
                "total_play_time": {"player": player_name, "time": value, "avatar": avatar},
                "achievements_unlocked": {"player": player_name, "achievements": value, "avatar": avatar},
                "hero_power": {"player": player_name, "power": value, "avatar": avatar},
                "dungeon_floor": {"player": player_name, "floor": value, "avatar": avatar},
                "guild_power": {"player": player_name, "power": value, "avatar": avatar},
                "total_battles": {"player": player_name, "battles": value, "avatar": avatar}
            }
            data_list.append(key_map.get(ranking_id, {"player": player_name, "value": value, "avatar": avatar}))
        
        sort_key_map = {
            "pvp_wins": "wins",
            "total_play_time": "time",
            "achievements_unlocked": "achievements",
            "hero_power": "power",
            "dungeon_floor": "floor",
            "guild_power": "power",
            "total_battles": "battles"
        }
        data_list.sort(key=lambda x: x[sort_key_map.get(ranking_id, "value")], reverse=True)
        
        data["ranking_center"][ranking_id] = data_list[:100]
        data["ranking_center"]["last_updated"][ranking_id] = time.time()
        save()

def draw_gradient_background(surface, color1, color2):
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_title(surface, text, y, screen_width, font):
    for offset in range(5, 0, -1):
        alpha = 50 - offset * 8
        glow_surf = font.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    title = font.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y))
    
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)

def draw_rank_item(surface, rank, item, x, y, width, height, font_main, font_small, ranking_type):
    item_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, COLORS["panel_bg"], item_rect, border_radius=8)
    
    if rank == 1:
        pygame.draw.rect(surface, COLORS["rank_1"], item_rect, 3, border_radius=8)
        rank_text = font_main.render("🥇", True, COLORS["rank_1"])
    elif rank == 2:
        pygame.draw.rect(surface, COLORS["rank_2"], item_rect, 3, border_radius=8)
        rank_text = font_main.render("🥈", True, COLORS["rank_2"])
    elif rank == 3:
        pygame.draw.rect(surface, COLORS["rank_3"], item_rect, 3, border_radius=8)
        rank_text = font_main.render("🥉", True, COLORS["rank_3"])
    else:
        rank_text = font_small.render(str(rank), True, COLORS["text_gray"])
    
    surface.blit(rank_text, (x + 20, y + height // 2 - rank_text.get_height() // 2))
    
    avatar_text = font_main.render(item.get("avatar", "⚔️"), True, COLORS["accent_gold"])
    surface.blit(avatar_text, (x + 60, y + height // 2 - avatar_text.get_height() // 2))
    
    name_text = font_main.render(item["player"], True, COLORS["text_white"])
    surface.blit(name_text, (x + 100, y + height // 2 - name_text.get_height() // 2))
    
    value_key_map = {
        "pvp_wins": "wins",
        "total_play_time": "time",
        "achievements_unlocked": "achievements",
        "hero_power": "power",
        "dungeon_floor": "floor",
        "guild_power": "power",
        "total_battles": "battles"
    }
    value_key = value_key_map.get(ranking_type["id"], "value")
    value = item.get(value_key, 0)
    
    if value >= 10000:
        value_str = f"{value/10000:.1f}万"
    elif value >= 1000:
        value_str = f"{value/1000:.1f}k"
    else:
        value_str = str(value)
    
    value_text = font_main.render(f"{value_str} {ranking_type['unit']}", True, COLORS["accent_green"])
    surface.blit(value_text, (x + width - 180, y + height // 2 - value_text.get_height() // 2))

def main():
    try:
        if not pygame.get_init():
            pygame.init()
            pygame.mixer.init()
        
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 900
                SCREEN_HEIGHT = 700
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("排行榜中心")
        clock = pygame.time.Clock()
        
        scale = min(SCREEN_WIDTH / 900, SCREEN_HEIGHT / 700)
        
        def init_font(size):
            font_name = get_system_font_name()
            adjusted_size = int(size * scale)
            try:
                return pygame.font.SysFont(font_name, adjusted_size)
            except Exception:
                return pygame.font.Font(None, adjusted_size)
        
        font_title = init_font(48)
        font_main = init_font(28)
        font_small = init_font(22)
        
        ranking_center = RankingCenter()
        
        particles = []
        
        current_ranking = 0
        scroll_offset = 0
        is_scrolling = False
        last_mouse_y = 0
        
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            if random.random() < 0.05:
                particles.append(Particle(
                    random.randint(0, SCREEN_WIDTH),
                    random.randint(0, SCREEN_HEIGHT),
                    COLORS["accent_gold"], 0.5, 2, 100
                ))
            
            for p in particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    particles.remove(p)
            
            draw_title(screen, "排行榜中心", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            tabs_per_row = min(3, SCREEN_WIDTH // 220)
            tab_width = min(180, SCREEN_WIDTH * 0.25)
            tab_height = 45
            tab_spacing = 20
            
            tab_start_x = (SCREEN_WIDTH - (tabs_per_row * tab_width + (tabs_per_row - 1) * tab_spacing)) // 2
            tab_start_y = SCREEN_HEIGHT * 0.18
            
            type_buttons = []
            for i, ranking_type in enumerate(ranking_center.ranking_types):
                row = i // tabs_per_row
                col = i % tabs_per_row
                x = tab_start_x + col * (tab_width + tab_spacing)
                y = tab_start_y + row * (tab_height + tab_spacing)
                
                is_selected = i == current_ranking
                btn_color = COLORS["btn_gold"] if is_selected else COLORS["btn_blue"]
                hover_color = COLORS["btn_gold_hover"] if is_selected else COLORS["btn_blue_hover"]
                
                btn = Button(f"{ranking_type['icon']} {ranking_type['name']}", x, y, tab_width, tab_height, font_small, btn_color, hover_color)
                btn.update((mx, my))
                btn.draw(screen)
                type_buttons.append((btn, i))
            
            content_y = SCREEN_HEIGHT * 0.28 + (len(ranking_center.ranking_types) // tabs_per_row) * (tab_height + tab_spacing)
            
            current_type = ranking_center.ranking_types[current_ranking]
            ranking_data = ranking_center.get_ranking_data(current_type["id"])
            
            ranking_title = font_main.render(f"{current_type['icon']} {current_type['name']}", True, COLORS["accent_gold"])
            screen.blit(ranking_title, (50, content_y))
            
            desc_text = font_small.render(current_type["description"], True, COLORS["text_gray"])
            screen.blit(desc_text, (50, content_y + 35))
            
            list_y = content_y + 60
            list_width = min(800, SCREEN_WIDTH - 100)
            list_x = (SCREEN_WIDTH - list_width) // 2
            list_height = SCREEN_HEIGHT - list_y - 100
            
            list_surf = pygame.Surface((list_width, list_height), pygame.SRCALPHA)
            pygame.draw.rect(list_surf, (35, 40, 60, 200), (0, 0, list_width, list_height), border_radius=12)
            screen.blit(list_surf, (list_x, list_y))
            pygame.draw.rect(screen, COLORS["accent_gold"], (list_x, list_y, list_width, list_height), 2, border_radius=12)
            
            header_rect = pygame.Rect(list_x, list_y, list_width, 40)
            pygame.draw.rect(screen, (40, 45, 70, 200), header_rect)
            pygame.draw.line(screen, COLORS["accent_gold"], (list_x + 20, list_y + 40), (list_x + list_width - 20, list_y + 40), 2)
            
            rank_header = font_small.render("排名", True, COLORS["accent_gold"])
            screen.blit(rank_header, (list_x + 30, list_y + 10))
            
            player_header = font_small.render("玩家", True, COLORS["accent_gold"])
            screen.blit(player_header, (list_x + 100, list_y + 10))
            
            score_header = font_small.render("数值", True, COLORS["accent_gold"])
            screen.blit(score_header, (list_x + list_width - 100, list_y + 10))
            
            item_height = 55
            max_scroll = max(0, len(ranking_data) * item_height - (list_height - 40))
            
            clip_rect = pygame.Rect(list_x, list_y + 40, list_width, list_height - 40)
            screen.set_clip(clip_rect)
            
            for i, item in enumerate(ranking_data):
                item_y = list_y + 45 + i * item_height - scroll_offset
                if -item_height <= item_y <= list_height:
                    draw_rank_item(screen, i + 1, item, list_x + 10, item_y, list_width - 20, item_height - 5, font_main, font_small, current_type)
            
            screen.set_clip(None)
            
            if max_scroll > 0:
                scrollbar_width = 8
                scrollbar_x = list_x + list_width - 15
                scrollbar_height = max(30, list_height * list_height / (len(ranking_data) * item_height))
                scrollbar_y_ratio = scroll_offset / max_scroll
                scrollbar_y = list_y + 40 + (list_height - 40 - scrollbar_height) * scrollbar_y_ratio
                
                pygame.draw.rect(screen, (50, 50, 70), (scrollbar_x, list_y + 40, scrollbar_width, list_height - 40), border_radius=4)
                pygame.draw.rect(screen, COLORS["accent_gold"], (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height), border_radius=4)
            
            player_name = data.get("player", {}).get("name", "玩家")
            player_rank = ranking_center.get_player_rank(player_name, current_type["id"])
            
            if player_rank:
                rank_text = font_small.render(f"你的排名: 第{player_rank}名", True, COLORS["accent_green"])
            else:
                rank_text = font_small.render("你尚未上榜", True, COLORS["text_gray"])
            screen.blit(rank_text, (list_x + 20, list_y + list_height + 10))
            
            return_btn = Button("返回", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, font_main)
            return_btn.update((mx, my))
            return_btn.draw(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn, idx in type_buttons:
                        if btn.rect.collidepoint(mx, my):
                            current_ranking = idx
                            scroll_offset = 0
                            break
                    
                    if list_x <= mx <= list_x + list_width and list_y + 40 <= my <= list_y + list_height:
                        is_scrolling = True
                        last_mouse_y = my
                    
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    is_scrolling = False
                elif event.type == pygame.MOUSEMOTION:
                    if is_scrolling:
                        delta_y = my - last_mouse_y
                        scroll_offset = max(0, min(max_scroll, scroll_offset - delta_y))
                        last_mouse_y = my
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("排行榜中心")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("排行榜中心", str(e))

if __name__ == "__main__":
    main()