"""成就系统 - 成就解锁、进度追踪与奖励领取"""

import time
import pygame
from ASSET.game_data import data, save, logger, draw_gradient_bg, cull_dead, get_font

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


# ===================== UI 界面 =====================

def _draw_title(surface, text, y_pos, screen_width):
    """绘制带特效的标题"""
    from ASSET.game_main_menu import COLORS
    font_big = get_font(38)
    for offset in range(5, 0, -1):
        glow_surf = font_big.render(text, True, (*COLORS["accent_gold"][:3], 50 - offset * 8))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    title = font_big.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    shadow = font_big.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)
    line_y = y_pos + 34
    pygame.draw.line(surface, COLORS["accent_gold"],
                     (screen_width // 2 - 120, line_y), (screen_width // 2 - 40, line_y), 3)
    pygame.draw.line(surface, COLORS["accent_gold"],
                     (screen_width // 2 + 40, line_y), (screen_width // 2 + 120, line_y), 3)
    pygame.draw.circle(surface, COLORS["accent_gold"], (screen_width // 2, line_y), 7)
    pygame.draw.circle(surface, COLORS["bg_dark"], (screen_width // 2, line_y), 4)


def main():
    """成就系统主界面"""
    import os
    from ASSET.game_main_menu import Button, COLORS

    if not pygame.get_init():
        pygame.init()

    # 复用当前显示表面（避免改分辨率导致返回错位）
    cur_surface = pygame.display.get_surface()
    if cur_surface is not None:
        screen_width, screen_height = cur_surface.get_size()
        screen = cur_surface
    else:
        screen_width, screen_height = 800, 600
        screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("成就系统")
    clock = pygame.time.Clock()

    font_main = get_font(20)
    font_mid = get_font(17)
    font_small = get_font(15)

    system = AchievementSystem()
    system.check_achievements()
    all_achievements = system.get_all_achievements()

    # 按钮
    back_btn = Button("返回主菜单", screen_width - 200, screen_height - 60, 180, 50,
                      font_main, normal_color=COLORS["accent_blue_dark"])
    up_btn = Button("▲", screen_width - 58, int(screen_height * 0.32), 42, 38,
                    font_mid, normal_color=COLORS["accent_blue"])
    down_btn = Button("▼", screen_width - 58, int(screen_height * 0.40), 42, 38,
                      font_mid, normal_color=COLORS["accent_blue"])

    scroll = 0
    row_h = min(66, screen_height // 8)
    rows_visible = max(1, (screen_height - 190) // row_h)

    toast = ""
    toast_timer = 0

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])

        # 标题
        _draw_title(screen, "成就系统", int(screen_height * 0.05), screen_width)

        # 统计
        unlocked_count = sum(1 for a in all_achievements if a["unlocked"])
        unclaimed_count = sum(1 for a in all_achievements if a["unlocked"] and not a["claimed"])
        stats = f"已解锁 {unlocked_count}/{len(all_achievements)}    可领取奖励 {unclaimed_count}"
        stats_surf = font_main.render(stats, True, COLORS["accent_gold"])
        screen.blit(stats_surf, (screen_width // 2 - stats_surf.get_width() // 2, int(screen_height * 0.12)))

        # 成就列表
        list_x = 15
        list_width = screen_width - 95
        start_y = int(screen_height * 0.18)
        claim_buttons = []
        visible_items = all_achievements[scroll:scroll + rows_visible]
        for i, a in enumerate(visible_items):
            y = start_y + i * row_h
            row_rect = pygame.Rect(list_x, y, list_width, row_h - 6)

            # 行背景
            row_surf = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            row_surf.fill((30, 30, 55, 150))
            screen.blit(row_surf, row_rect.topleft)
            pygame.draw.rect(screen, (60, 60, 100), row_rect, 1, border_radius=6)

            # 类型标签（替代无法正常显示的 emoji 图标）
            _type_labels = {
                "battle": ("战斗", (220, 90, 90)),
                "collection": ("收集", (255, 215, 0)),
                "checkin": ("签到", (90, 200, 120)),
                "resource": ("资源", (90, 150, 230)),
                "story": ("剧情", (190, 120, 230)),
                "social": ("社交", (90, 200, 210)),
            }
            _label_text, _label_color = _type_labels.get(a["type"], (str(a["type"]), COLORS["text_gray"]))
            icon_surf = font_small.render(_label_text, True, _label_color)
            screen.blit(icon_surf, (list_x + 12, y + 12))

            # 名称
            name_surf = font_mid.render(a["name"], True, COLORS["text_white"])
            screen.blit(name_surf, (list_x + 66, y + 4))

            # 描述（超长截断，避免顶出窗口）
            desc = f"{a['description']} ({a['current']}/{a['goal']})"
            if len(desc) > 26:
                desc = desc[:26] + "..."
            desc_surf = font_small.render(desc, True, COLORS["text_gray"])
            screen.blit(desc_surf, (list_x + 66, y + 28))

            # 进度条
            bar_x = list_x + list_width - 230
            bar_y = y + 14
            bar_w = 150
            bar_h = 10
            pygame.draw.rect(screen, (50, 50, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
            bar_color = COLORS["accent_gold"] if a["unlocked"] else COLORS["accent_blue"]
            fill_w = int(bar_w * a["progress"] / 100)
            if fill_w > 0:
                pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=5)
            pct_surf = font_small.render(f"{a['progress']}%", True, COLORS["text_white"])
            screen.blit(pct_surf, (bar_x + bar_w + 6, bar_y - 3))

            # 右侧状态 / 领取按钮
            btn_x = screen_width - 88
            btn_y = y + 8
            if a["unlocked"] and not a["claimed"]:
                claim_btn = Button("领取", btn_x, btn_y, 66, 34, font_small,
                                   normal_color=COLORS["accent_gold"])
                claim_btn.check_hover(mouse_pos)
                claim_btn.draw(screen)
                claim_buttons.append((claim_btn, a))
            elif a["claimed"]:
                done_surf = font_small.render("已领取", True, COLORS["accent_green"])
                screen.blit(done_surf, (btn_x, btn_y + 8))
            else:
                lock_surf = font_small.render("未解锁", True, COLORS["text_gray"])
                screen.blit(lock_surf, (btn_x, btn_y + 8))

        # 滚动按钮
        if scroll > 0:
            up_btn.check_hover(mouse_pos)
            up_btn.draw(screen)
        if scroll + rows_visible < len(all_achievements):
            down_btn.check_hover(mouse_pos)
            down_btn.draw(screen)

        # 返回按钮
        back_btn.check_hover(mouse_pos)
        back_btn.draw(screen)

        # Toast 提示
        if toast and toast_timer > 0:
            toast_timer -= 1
            toast_surf = font_main.render(toast, True, COLORS["accent_gold"])
            toast_rect = toast_surf.get_rect(center=(screen_width // 2, screen_height - 100))
            panel = pygame.Surface((toast_surf.get_width() + 30, 36), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 180))
            screen.blit(panel, (toast_rect.x - 15, toast_rect.y - 3))
            screen.blit(toast_surf, toast_rect)
        if toast_timer <= 0:
            toast = ""

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save()
                    return
                elif event.key == pygame.K_UP:
                    scroll = max(0, scroll - 1)
                elif event.key == pygame.K_DOWN:
                    scroll = min(max(0, len(all_achievements) - rows_visible), scroll + 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.check_click(mouse_pos):
                    save()
                    return
                for btn, a in claim_buttons:
                    if btn.check_click(mouse_pos):
                        ok, msg = system.claim_reward(a["id"])
                        if ok:
                            toast = "领取成功！获得: " + ", ".join(f"{k}x{v}" for k, v in msg.items())
                        else:
                            toast = f"领取失败: {msg}"
                        toast_timer = 90
                        all_achievements = system.get_all_achievements()
                if scroll > 0 and up_btn.check_click(mouse_pos):
                    scroll = max(0, scroll - 1)
                if scroll + rows_visible < len(all_achievements) and down_btn.check_click(mouse_pos):
                    scroll = min(max(0, len(all_achievements) - rows_visible), scroll + 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                scroll = max(0, scroll - 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                scroll = min(max(0, len(all_achievements) - rows_visible), scroll + 1)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()