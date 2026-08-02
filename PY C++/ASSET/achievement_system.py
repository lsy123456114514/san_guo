import time
import os
import pygame
import sys
from ASSET.game_data import data, save
from ASSET.dictionary_system import get_system_font_name

COLORS = {
    "bg_dark": (10, 10, 25),
    "bg_light": (20, 20, 45),
    "accent_gold": (255, 215, 0),
    "accent_red": (255, 100, 100),
    "accent_blue": (100, 150, 255),
    "accent_green": (100, 255, 150),
    "text_white": (255, 255, 255),
    "text_gray": (150, 150, 150),
    "border": (80, 80, 120)
}

class AchievementSystem:
    """成就系统 - 给予玩家成就感和目标感"""
    
    def __init__(self):
        # 确保数据存在
        if "achievements" not in data:
            data["achievements"] = {
                "unlocked": [],
                "progress": {},
                "claimed_rewards": []
            }
        
        self.achievements = self._load_achievements()
    
    def _load_achievements(self):
        """加载成就配置"""
        return [
            # 战斗成就
            {
                "id": "first_battle",
                "name": "初出茅庐",
                "description": "完成第一场战斗",
                "icon": "⚔️",
                "type": "battle",
                "goal": 1,
                "stat_key": "total_battles",
                "rewards": {"金元宝": 100, "经验": 200},
                "rarity": "common",
                "tier": 1
            },
            {
                "id": "victory_10",
                "name": "百战百胜",
                "description": "获得10场胜利",
                "icon": "🏆",
                "type": "battle",
                "goal": 10,
                "stat_key": "victories",
                "rewards": {"金元宝": 200, "经验": 500},
                "rarity": "common",
                "tier": 2
            },
            {
                "id": "victory_50",
                "name": "常胜将军",
                "description": "获得50场胜利",
                "icon": "⭐",
                "type": "battle",
                "goal": 50,
                "stat_key": "victories",
                "rewards": {"金元宝": 500, "高级招募令": 1},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "victory_100",
                "name": "战神",
                "description": "获得100场胜利",
                "icon": "👑",
                "type": "battle",
                "goal": 100,
                "stat_key": "victories",
                "rewards": {"金元宝": 1000, "顶级招募令": 1},
                "rarity": "legendary",
                "tier": 4
            },
            {
                "id": "max_combo_10",
                "name": "连击大师",
                "description": "达成10连击",
                "icon": "🔥",
                "type": "battle",
                "goal": 10,
                "stat_key": "max_combo",
                "rewards": {"金元宝": 300, "经验": 400},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "ultimate_10",
                "name": "必杀达人",
                "description": "使用10次必杀技",
                "icon": "💥",
                "type": "battle",
                "goal": 10,
                "stat_key": "ultimate_used_count",
                "rewards": {"金元宝": 200, "经验": 300},
                "rarity": "common",
                "tier": 2
            },
            # 收集成就
            {
                "id": "collect_5_heroes",
                "name": "招贤纳士",
                "description": "拥有5名武将",
                "icon": "👥",
                "type": "collection",
                "goal": 5,
                "stat_key": "hero_count",
                "rewards": {"金元宝": 200, "经验": 300},
                "rarity": "common",
                "tier": 2
            },
            {
                "id": "collect_10_heroes",
                "name": "人才济济",
                "description": "拥有10名武将",
                "icon": "🌟",
                "type": "collection",
                "goal": 10,
                "stat_key": "hero_count",
                "rewards": {"金元宝": 500, "高级招募令": 1},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "collect_20_heroes",
                "name": "群英荟萃",
                "description": "拥有20名武将",
                "icon": "👑",
                "type": "collection",
                "goal": 20,
                "stat_key": "hero_count",
                "rewards": {"金元宝": 1000, "顶级招募令": 2},
                "rarity": "legendary",
                "tier": 4
            },
            {
                "id": "legendary_hero",
                "name": "名将降临",
                "description": "获得一名传说武将",
                "icon": "💎",
                "type": "collection",
                "goal": 1,
                "stat_key": "legendary_count",
                "rewards": {"金元宝": 300, "经验": 500},
                "rarity": "rare",
                "tier": 3
            },
            # 签到成就
            {
                "id": "checkin_7",
                "name": "持之以恒",
                "description": "连续签到7天",
                "icon": "📅",
                "type": "checkin",
                "goal": 7,
                "stat_key": "consecutive_checkins",
                "rewards": {"金元宝": 300, "中级经验丹": 2},
                "rarity": "common",
                "tier": 2
            },
            {
                "id": "checkin_30",
                "name": "坚持不懈",
                "description": "连续签到30天",
                "icon": "🌙",
                "type": "checkin",
                "goal": 30,
                "stat_key": "consecutive_checkins",
                "rewards": {"金元宝": 1000, "顶级招募令": 1},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "checkin_100",
                "name": "百炼成钢",
                "description": "累计签到100天",
                "icon": "💪",
                "type": "checkin",
                "goal": 100,
                "stat_key": "total_checkins",
                "rewards": {"金元宝": 2000, "稀有武将碎片": 30},
                "rarity": "legendary",
                "tier": 4
            },
            # 资源成就
            {
                "id": "gold_10000",
                "name": "腰缠万贯",
                "description": "累计获得10000金元宝",
                "icon": "💰",
                "type": "resource",
                "goal": 10000,
                "stat_key": "total_gold",
                "rewards": {"金元宝": 500, "经验": 500},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "resource_master",
                "name": "富甲一方",
                "description": "所有资源都达到1000",
                "icon": "📦",
                "type": "resource",
                "goal": 1000,
                "stat_key": "max_resource",
                "rewards": {"金元宝": 800, "装备精炼石": 10},
                "rarity": "rare",
                "tier": 3
            },
            # 剧情成就
            {
                "id": "first_story",
                "name": "乱世启程",
                "description": "完成第一个剧情事件",
                "icon": "📜",
                "type": "story",
                "goal": 1,
                "stat_key": "story_completed",
                "rewards": {"金元宝": 100, "经验": 200},
                "rarity": "common",
                "tier": 1
            },
            {
                "id": "story_all",
                "name": "一统天下",
                "description": "完成所有剧情事件",
                "icon": "🌍",
                "type": "story",
                "goal": 10,
                "stat_key": "story_completed",
                "rewards": {"金元宝": 2000, "传说武将碎片": 100},
                "rarity": "legendary",
                "tier": 5
            },
            # 社交成就
            {
                "id": "friend_5",
                "name": "广交朋友",
                "description": "拥有5位好友",
                "icon": "🤝",
                "type": "social",
                "goal": 5,
                "stat_key": "friend_count",
                "rewards": {"金元宝": 200, "经验": 300},
                "rarity": "common",
                "tier": 2
            },
            {
                "id": "friend_20",
                "name": "四海之内皆兄弟",
                "description": "拥有20位好友",
                "icon": "👨‍👩‍👧‍👦",
                "type": "social",
                "goal": 20,
                "stat_key": "friend_count",
                "rewards": {"金元宝": 500, "高级招募令": 1},
                "rarity": "rare",
                "tier": 3
            }
        ]
    
    def _get_stat_value(self, stat_key):
        """获取统计值"""
        if stat_key == "hero_count":
            return len(data.get("heroes", {}))
        elif stat_key == "legendary_count":
            heroes = data.get("heroes", {})
            count = 0
            for hero in heroes.values():
                if hero.get("star", 1) >= 3:
                    count += 1
            return count
        elif stat_key == "consecutive_checkins":
            return data.get("daily_reward", {}).get("consecutive_days", 0)
        elif stat_key == "total_checkins":
            return data.get("daily_reward", {}).get("monthly_checkins", 0)
        elif stat_key == "story_completed":
            return len(data.get("event_system", {}).get("event_history", []))
        elif stat_key == "friend_count":
            return len(data.get("friends", {}).get("list", []))
        elif stat_key == "total_gold":
            return data.get("resources", {}).get("金元宝", 0)
        elif stat_key == "max_resource":
            resources = data.get("resources", {})
            return max(resources.values(), default=0)
        elif stat_key in data.get("battle_stats", {}):
            return data["battle_stats"].get(stat_key, 0)
        return 0
    
    def check_achievements(self):
        """检查成就解锁"""
        unlocked_this_time = []
        
        for achievement in self.achievements:
            achievement_id = achievement["id"]
            
            if achievement_id in data["achievements"]["unlocked"]:
                continue
            
            current_value = self._get_stat_value(achievement["stat_key"])
            
            if current_value >= achievement["goal"]:
                data["achievements"]["unlocked"].append(achievement_id)
                data["achievements"]["progress"][achievement_id] = 100
                unlocked_this_time.append(achievement)
                save()
        
        return unlocked_this_time
    
    def get_progress(self, achievement_id):
        """获取成就进度"""
        achievement = next((a for a in self.achievements if a["id"] == achievement_id), None)
        if not achievement:
            return 0
        
        current_value = self._get_stat_value(achievement["stat_key"])
        return min(100, int((current_value / achievement["goal"]) * 100))
    
    def claim_reward(self, achievement_id):
        """领取成就奖励"""
        if achievement_id in data["achievements"]["claimed_rewards"]:
            return False, "奖励已领取"
        
        achievement = next((a for a in self.achievements if a["id"] == achievement_id), None)
        if not achievement:
            return False, "成就不存在"
        
        if achievement_id not in data["achievements"]["unlocked"]:
            return False, "成就未解锁"
        
        # 发放奖励
        for reward, amount in achievement["rewards"].items():
            if reward in data["resources"]:
                data["resources"][reward] += amount
            else:
                data["resources"][reward] = amount
        
        data["achievements"]["claimed_rewards"].append(achievement_id)
        save()
        
        return True, achievement["rewards"]
    
    def get_all_achievements(self):
        """获取所有成就状态"""
        result = []
        
        for achievement in self.achievements:
            unlocked = achievement["id"] in data["achievements"]["unlocked"]
            claimed = achievement["id"] in data["achievements"]["claimed_rewards"]
            progress = self.get_progress(achievement["id"])
            
            result.append({
                "id": achievement["id"],
                "name": achievement["name"],
                "description": achievement["description"],
                "icon": achievement["icon"],
                "type": achievement["type"],
                "goal": achievement["goal"],
                "current": self._get_stat_value(achievement["stat_key"]),
                "progress": progress,
                "unlocked": unlocked,
                "claimed": claimed,
                "rewards": achievement["rewards"],
                "rarity": achievement["rarity"],
                "tier": achievement["tier"]
            })
        
        return result
    
    def get_unclaimed_rewards(self):
        """获取未领取奖励的成就"""
        unclaimed = []
        
        for achievement in self.achievements:
            if achievement["id"] in data["achievements"]["unlocked"]:
                if achievement["id"] not in data["achievements"]["claimed_rewards"]:
                    unclaimed.append(achievement)
        
        return unclaimed
    
    def get_achievement_by_id(self, achievement_id):
        """根据ID获取成就"""
        return next((a for a in self.achievements if a["id"] == achievement_id), None)


def draw_gradient_background(screen, color1, color2):
    """绘制渐变背景"""
    height = screen.get_height()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))


class Button:
    """简单按钮类"""
    def __init__(self, text, x, y, width, height, font, normal_color=(100, 100, 150), hover_color=(120, 120, 180), text_color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
    
    def draw(self, screen):
        color = self.hover_color if self.hovered else self.normal_color
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height), border_radius=8)
        pygame.draw.rect(screen, COLORS["accent_gold"], (self.x, self.y, self.width, self.height), 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
        screen.blit(text_surf, text_rect)
    
    def check_click(self, mouse_pos):
        mx, my = mouse_pos
        return self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height


def main():
    """成就系统主界面"""
    try:
        if not pygame.get_init():
            pygame.init()
        
        resolution = data['settings']['graphics']['resolution']
        try:
            width, height = map(int, resolution.split('x'))
        except ValueError:
            width, height = 800, 600
        
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("🏆 成就系统")
        clock = pygame.time.Clock()
        
        font_name = get_system_font_name()
        try:
            FONT_MAIN = pygame.font.SysFont(font_name, 28)
            FONT_SMALL = pygame.font.SysFont(font_name, 22)
            FONT_BIG = pygame.font.SysFont(font_name, 36)
        except Exception:
            FONT_MAIN = pygame.font.Font(None, 28)
            FONT_SMALL = pygame.font.Font(None, 22)
            FONT_BIG = pygame.font.Font(None, 36)
        
        achievement_system = AchievementSystem()
        
        running = True
        selected_tab = "all"
        scroll_y = 0
        
        while running:
            mx, my = pygame.mouse.get_pos()
            
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            title_surf = FONT_BIG.render("🏆 成就系统", True, COLORS["accent_gold"])
            title_rect = title_surf.get_rect(center=(width // 2, 40))
            screen.blit(title_surf, title_rect)
            
            tabs = [("全部", "all"), ("战斗", "battle"), ("收集", "collection"), ("签到", "checkin"), ("进阶", "advanced")]
            tab_width = 120
            tab_height = 40
            tab_start_x = (width - len(tabs) * tab_width) // 2
            
            for i, (tab_name, tab_code) in enumerate(tabs):
                tab_x = tab_start_x + i * tab_width
                tab_y = 80
                color = COLORS["accent_gold"] if selected_tab == tab_code else COLORS["border"]
                pygame.draw.rect(screen, color, (tab_x, tab_y, tab_width, tab_height), border_radius=5)
                text_color = COLORS["bg_dark"] if selected_tab == tab_code else COLORS["text_white"]
                text_surf = FONT_MAIN.render(tab_name, True, text_color)
                text_rect = text_surf.get_rect(center=(tab_x + tab_width//2, tab_y + tab_height//2))
                screen.blit(text_surf, text_rect)
                
                if tab_x <= mx <= tab_x + tab_width and tab_y <= my <= tab_y + tab_height:
                    pygame.draw.rect(screen, COLORS["text_white"], (tab_x, tab_y, tab_width, tab_height), 2, border_radius=5)
                    if pygame.mouse.get_pressed()[0]:
                        selected_tab = tab_code
            
            filtered_achievements = []
            if selected_tab == "all":
                filtered_achievements = achievement_system.achievements
            else:
                filtered_achievements = [a for a in achievement_system.achievements if a["type"] == selected_tab]
            
            panel_y = 130
            panel_width = width - 40
            panel_height = height - panel_y - 60
            
            pygame.draw.rect(screen, COLORS["bg_light"], (20, panel_y, panel_width, panel_height), border_radius=10)
            pygame.draw.rect(screen, COLORS["border"], (20, panel_y, panel_width, panel_height), 2, border_radius=10)
            
            item_height = 80
            total_height = len(filtered_achievements) * item_height
            
            for i, achievement in enumerate(filtered_achievements):
                item_y = panel_y + 10 + i * item_height - scroll_y
                
                if item_y + item_height < panel_y or item_y > panel_y + panel_height:
                    continue
                
                is_unlocked = achievement["id"] in data["achievements"]["unlocked"]
                is_claimed = achievement["id"] in data["achievements"]["claimed_rewards"]
                
                bg_color = COLORS["accent_gold"] if is_unlocked else COLORS["border"]
                pygame.draw.rect(screen, bg_color, (30, item_y, panel_width - 20, item_height - 10), border_radius=8)
                
                icon_x = 45
                icon_y = item_y + item_height//2 - 20
                icon_surf = FONT_BIG.render(achievement["icon"], True, COLORS["bg_dark"] if is_unlocked else COLORS["text_gray"])
                screen.blit(icon_surf, (icon_x, icon_y))
                
                name_x = 95
                name_y = item_y + 15
                name_surf = FONT_MAIN.render(achievement["name"], True, COLORS["bg_dark"] if is_unlocked else COLORS["text_gray"])
                screen.blit(name_surf, (name_x, name_y))
                
                desc_x = 95
                desc_y = item_y + 40
                desc_surf = FONT_SMALL.render(achievement["description"], True, COLORS["text_gray"] if is_unlocked else COLORS["text_gray"])
                screen.blit(desc_surf, (desc_x, desc_y))
                
                rewards_text = ", ".join([f"{k}:{v}" for k, v in achievement["rewards"].items()])
                rewards_surf = FONT_SMALL.render(rewards_text, True, COLORS["accent_green"])
                rewards_x = width - 30 - rewards_surf.get_width()
                rewards_y = item_y + item_height//2 - rewards_surf.get_height()//2
                screen.blit(rewards_surf, (rewards_x, rewards_y))
                
                if is_unlocked and not is_claimed:
                    claim_btn = Button("领取", rewards_x - 80, item_y + 15, 70, 30, FONT_SMALL, COLORS["accent_green"], COLORS["accent_gold"])
                    claim_btn.hovered = claim_btn.check_click((mx, my))
                    claim_btn.draw(screen)
                    if claim_btn.check_click((mx, my)) and pygame.mouse.get_pressed()[0]:
                        achievement_system.claim_reward(achievement["id"])
            
            back_btn = Button("返回", 20, height - 45, 100, 35, FONT_MAIN)
            back_btn.hovered = back_btn.check_click((mx, my))
            back_btn.draw(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_btn.check_click((mx, my)):
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                    scroll_y = max(0, scroll_y - 50)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                    scroll_y = min(total_height - panel_height, scroll_y + 50)
            
            pygame.display.flip()
            clock.tick(30)
        
        pygame.display.set_mode((width, height))
    
    except Exception as e:
        print(f"成就系统错误: {e}")
        import traceback
        traceback.print_exc()