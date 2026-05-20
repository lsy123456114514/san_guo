import pygame
import time
from ASSET.game_data import data, save

class ModernUI:
    """现代化UI组件系统 - 借鉴成功游戏的设计"""
    
    # 深色科技风配色方案
    COLORS = {
        "bg_dark": (15, 20, 30),
        "bg_panel": (25, 35, 50),
        "bg_hover": (40, 55, 75),
        "accent_cyan": (0, 212, 255),
        "accent_gold": (255, 215, 0),
        "accent_green": (50, 205, 50),
        "accent_red": (255, 69, 0),
        "accent_purple": (138, 43, 226),
        "text_primary": (255, 255, 255),
        "text_secondary": (180, 180, 200),
        "border": (60, 80, 100),
        "progress_bg": (40, 50, 65),
        "gradient_start": (0, 150, 200),
        "gradient_end": (0, 100, 150)
    }
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self._init_fonts()
        
        # 动画状态
        self.animations = {}
        self.transitions = {}
        
        # 通知系统
        self.notifications = []
        self.max_notifications = 5
        
        # 快捷操作
        self.quick_actions = [
            {"id": "checkin", "name": "签到", "icon": "📅", "color": self.COLORS["accent_cyan"]},
            {"id": "daily_task", "name": "任务", "icon": "📋", "color": self.COLORS["accent_gold"]},
            {"id": "dungeon", "name": "副本", "icon": "🏰", "color": self.COLORS["accent_green"]},
            {"id": "recruit", "name": "招募", "icon": "⚔️", "color": self.COLORS["accent_purple"]},
            {"id": "shop", "name": "商店", "icon": "🛒", "color": self.COLORS["accent_red"]},
            {"id": "mail", "name": "邮件", "icon": "📧", "color": self.COLORS["text_secondary"]}
        ]
    
    def _init_fonts(self):
        """初始化字体"""
        try:
            self.font_large = pygame.font.SysFont("Microsoft YaHei", 24, bold=True)
            self.font_medium = pygame.font.SysFont("Microsoft YaHei", 18)
            self.font_small = pygame.font.SysFont("Microsoft YaHei", 14)
            self.font_tiny = pygame.font.SysFont("Microsoft YaHei", 12)
        except:
            self.font_large = pygame.font.Font(None, 36)
            self.font_medium = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
            self.font_tiny = pygame.font.Font(None, 14)
    
    def draw_gradient_rect(self, surface, rect, color1, color2, vertical=True):
        """绘制渐变矩形"""
        rect = pygame.Rect(rect)
        if vertical:
            for i in range(rect.height):
                ratio = i / rect.height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (rect.x, rect.y + i), (rect.x + rect.width, rect.y + i))
        else:
            for i in range(rect.width):
                ratio = i / rect.width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (rect.x + i, rect.y), (rect.x + i, rect.y + rect.height))
    
    def draw_rounded_rect(self, surface, rect, color, radius=10, border=0, border_color=None):
        """绘制圆角矩形"""
        rect = pygame.Rect(rect)
        if border > 0 and border_color:
            pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)
        else:
            pygame.draw.rect(surface, color, rect, 0, border_radius=radius)
    
    def draw_progress_bar(self, surface, x, y, width, height, progress, color, bg_color=None, show_text=True):
        """绘制进度条"""
        if bg_color:
            pygame.draw.rect(surface, bg_color, (x, y, width, height), border_radius=height//2)
        
        if progress > 0:
            fill_width = int(width * min(1.0, progress))
            self.draw_gradient_rect(surface, (x, y, fill_width, height), 
                                    self._lighten_color(color, 30), color)
            pygame.draw.rect(surface, color, (x, y, fill_width, height), border_radius=height//2)
        
        if show_text:
            text = f"{int(progress * 100)}%"
            text_surface = self.font_small.render(text, True, self.COLORS["text_primary"])
            text_rect = text_surface.get_rect(center=(x + width//2, y + height//2))
            surface.blit(text_surface, text_rect)
    
    def _lighten_color(self, color, amount):
        """提亮颜色"""
        return tuple(min(255, c + amount) for c in color)
    
    def add_notification(self, message, notification_type="info", duration=3):
        """添加通知"""
        notification = {
            "message": message,
            "type": notification_type,
            "time": time.time(),
            "duration": duration,
            "alpha": 255
        }
        self.notifications.append(notification)
        
        if len(self.notifications) > self.max_notifications:
            self.notifications.pop(0)
        
        save()
    
    def update_notifications(self):
        """更新通知状态"""
        current_time = time.time()
        self.notifications = [n for n in self.notifications 
                              if current_time - n["time"] < n["duration"]]
        
        for i, notification in enumerate(self.notifications):
            elapsed = current_time - notification["time"]
            fade_start = notification["duration"] - 0.5
            
            if elapsed > fade_start:
                notification["alpha"] = max(0, int(255 * (notification["duration"] - elapsed) / 0.5))
    
    def draw_notifications(self, surface):
        """绘制通知"""
        self.update_notifications()
        
        x = self.screen_width - 320
        y = 20
        
        for i, notification in enumerate(self.notifications):
            notification_height = 50
            
            bg_color = self.COLORS["bg_panel"]
            if notification["type"] == "reward":
                bg_color = self.COLORS["accent_gold"]
            elif notification["type"] == "warning":
                bg_color = self.COLORS["accent_red"]
            elif notification["type"] == "success":
                bg_color = self.COLORS["accent_green"]
            
            self.draw_rounded_rect(surface, (x, y + i * (notification_height + 10), 300, notification_height), 
                                   bg_color, radius=8)
            
            text = notification["message"]
            if len(text) > 20:
                text = text[:18] + "..."
            
            text_surface = self.font_small.render(text, True, self.COLORS["text_primary"])
            surface.blit(text_surface, (x + 15, y + i * (notification_height + 10) + 15))
    
    def draw_quick_action_bar(self, surface, x, y, action_size=60, gap=10):
        """绘制快捷操作栏"""
        total_width = len(self.quick_actions) * action_size + (len(self.quick_actions) - 1) * gap
        start_x = (self.screen_width - total_width) // 2
        
        for i, action in enumerate(self.quick_actions):
            ax = start_x + i * (action_size + gap)
            ay = y
            
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = (ax <= mouse_pos[0] <= ax + action_size and 
                         ay <= mouse_pos[1] <= ay + action_size)
            
            color = action["color"] if is_hovered else self._lighten_color(action["color"], -30)
            
            self.draw_rounded_rect(surface, (ax, ay, action_size, action_size), 
                                   self.COLORS["bg_panel"], radius=12)
            self.draw_rounded_rect(surface, (ax, ay, action_size, action_size), 
                                   color, radius=12, border=2)
            
            icon_text = self.font_large.render(action["icon"], True, self.COLORS["text_primary"])
            icon_rect = icon_text.get_rect(center=(ax + action_size//2, ay + action_size//2 - 5))
            surface.blit(icon_text, icon_rect)
            
            name_text = self.font_tiny.render(action["name"], True, self.COLORS["text_secondary"])
            name_rect = name_text.get_rect(center=(ax + action_size//2, ay + action_size - 12))
            surface.blit(name_text, name_rect)
    
    def draw_bottom_panel(self, surface, resources, weather_info=None):
        """绘制底部资源面板"""
        panel_height = 80
        y = self.screen_height - panel_height
        
        self.draw_gradient_rect(surface, (0, y, self.screen_width, panel_height),
                                self.COLORS["bg_panel"], self.COLORS["bg_dark"])
        
        pygame.draw.line(surface, self.COLORS["border"], (0, y), (self.screen_width, y), 2)
        
        x_offset = 20
        resource_display = [
            ("💰", "金元宝", resources.get("金元宝", 0)),
            ("🍚", "粮食", resources.get("粮食", 0)),
            ("⚔️", "战力", self._calculate_power()),
            ("🔥", "温度", self._get_temperature())
        ]
        
        for icon, name, value in resource_display:
            self._draw_resource_item(surface, x_offset, y + 15, icon, name, value)
            x_offset += 150
        
        if weather_info:
            self._draw_weather_info(surface, self.screen_width - 200, y + 15, weather_info)
    
    def _draw_resource_item(self, surface, x, y, icon, name, value):
        """绘制单个资源项"""
        icon_text = self.font_medium.render(icon, True, self.COLORS["text_primary"])
        surface.blit(icon_text, (x, y))
        
        name_text = self.font_small.render(name, True, self.COLORS["text_secondary"])
        surface.blit(name_text, (x + 30, y))
        
        value_text = self.font_medium.render(str(value), True, self.COLORS["accent_gold"])
        surface.blit(value_text, (x + 30, y + 20))
    
    def _draw_weather_info(self, surface, x, y, weather_info):
        """绘制天气信息"""
        icon = weather_info.get("icon", "☀️")
        temp = weather_info.get("temperature", 25)
        weather_name = weather_info.get("name", "晴天")
        
        icon_text = self.font_large.render(icon, True, self.COLORS["text_primary"])
        surface.blit(icon_text, (x, y))
        
        temp_text = self.font_medium.render(f"{temp}°C", True, self.COLORS["accent_cyan"])
        surface.blit(temp_text, (x + 40, y + 5))
        
        weather_text = self.font_small.render(weather_name, True, self.COLORS["text_secondary"])
        surface.blit(weather_text, (x + 40, y + 28))
    
    def _calculate_power(self):
        """计算总战力"""
        power = 0
        for hero in data.get("heroes", {}).values():
            power += hero.get("attack", 0) + hero.get("defense", 0) + hero.get("hp", 0) // 10
        return max(100, power)
    
    def _get_temperature(self):
        """获取模拟温度"""
        return 25
    
    def draw_top_bar(self, surface, season_info=None):
        """绘制顶部状态栏"""
        bar_height = 50
        
        self.draw_gradient_rect(surface, (0, 0, self.screen_width, bar_height),
                                self.COLORS["bg_panel"], self.COLORS["bg_dark"])
        
        pygame.draw.line(surface, self.COLORS["border"], (0, bar_height), (self.screen_width, bar_height), 2)
        
        left_x = 20
        title = "三国霸业"
        title_surface = self.font_large.render(title, True, self.COLORS["accent_gold"])
        surface.blit(title_surface, (left_x, 12))
        
        if season_info:
            season_text = f"{season_info.get('season', '春')}季"
            season_surface = self.font_medium.render(season_text, True, self.COLORS["accent_green"])
            surface.blit(season_surface, (left_x + 150, 15))
        
        right_x = self.screen_width - 150
        
        time_str = time.strftime("%H:%M")
        time_surface = self.font_medium.render(time_str, True, self.COLORS["text_secondary"])
        surface.blit(time_surface, (right_x, 15))
        
        date_str = time.strftime("%Y-%m-%d")
        date_surface = self.font_small.render(date_str, True, self.COLORS["text_secondary"])
        surface.blit(date_surface, (right_x, 32))
    
    def draw_today_goals_panel(self, surface, x, y, width=350, height=300):
        """绘制今日目标面板"""
        self.draw_rounded_rect(surface, (x, y, width, height), 
                               self.COLORS["bg_panel"], radius=15, border=2, 
                               border_color=self.COLORS["border"])
        
        title = "今日目标"
        title_surface = self.font_large.render(title, True, self.COLORS["accent_gold"])
        surface.blit(title_surface, (x + 20, y + 15))
        
        goals = self._get_today_goals()
        
        goal_y = y + 60
        for goal in goals:
            self._draw_goal_item(surface, x + 15, goal_y, width - 30, goal)
            goal_y += 60
        
        progress = sum(1 for g in goals if g["completed"]) / len(goals) if goals else 0
        
        progress_bar_y = y + height - 40
        self.draw_progress_bar(surface, x + 15, progress_bar_y, width - 30, 20, progress,
                               self.COLORS["accent_cyan"], self.COLORS["progress_bg"])
    
    def _draw_goal_item(self, surface, x, y, width, goal):
        """绘制单个目标项"""
        self.draw_rounded_rect(surface, (x, y, width, 50), 
                               self.COLORS["bg_hover"], radius=8)
        
        check_mark = "✅" if goal["completed"] else "⬜"
        check_surface = self.font_medium.render(check_mark, True, self.COLORS["text_primary"])
        surface.blit(check_surface, (x + 10, y + 12))
        
        name_surface = self.font_small.render(goal["name"], True, 
                                              self.COLORS["text_primary"] if goal["completed"] 
                                              else self.COLORS["text_secondary"])
        surface.blit(name_surface, (x + 40, y + 8))
        
        progress_text = f"{goal['progress']}/{goal['target']}"
        progress_surface = self.font_tiny.render(progress_text, True, self.COLORS["text_secondary"])
        surface.blit(progress_surface, (x + 40, y + 30))
        
        if not goal["completed"] and goal["progress"] < goal["target"]:
            bar_width = int((width - 60) * goal["progress"] / goal["target"])
            pygame.draw.rect(surface, self.COLORS["accent_cyan"], 
                            (x + 55, y + 35, bar_width, 5), border_radius=3)
    
    def _get_today_goals(self):
        """获取今日目标"""
        goals = []
        
        daily_reward = data.get("daily_reward", {})
        consecutive = daily_reward.get("consecutive_days", 0)
        goals.append({
            "name": f"每日签到 ({consecutive}天)",
            "completed": daily_reward.get("last_checkin_date") == time.strftime("%Y-%m-%d"),
            "progress": 1 if goals[-1]["completed"] else 0,
            "target": 1
        })
        
        task_chains = data.get("task_chains", {})
        daily_tasks = task_chains.get("daily_tasks", [])
        completed_daily = sum(1 for tid in daily_tasks if tid in task_chains.get("claimed_rewards", []))
        goals.append({
            "name": f"完成每日任务 ({completed_daily}/{len(daily_tasks)})",
            "completed": completed_daily >= len(daily_tasks) if daily_tasks else False,
            "progress": completed_daily,
            "target": len(daily_tasks)
        })
        
        battle_stats = data.get("battle_stats", {})
        victories = battle_stats.get("victories", 0)
        goals.append({
            "name": "赢得战斗",
            "completed": victories > 0,
            "progress": min(1, victories),
            "target": 1
        })
        
        dungeon = data.get("dungeon", {})
        completed_floors = sum(dungeon.get("completed_floors", {}).values())
        goals.append({
            "name": f"通关副本 ({completed_floors}层)",
            "completed": completed_floors > 0,
            "progress": min(10, completed_floors),
            "target": 10
        })
        
        return goals
    
    def draw_activity_reminder(self, surface, x, y):
        """绘制活动提醒"""
        activities = self._get_active_activities()
        
        if not activities:
            return
        
        activity = activities[0]
        
        self.draw_rounded_rect(surface, (x, y, 280, 70), 
                               self.COLORS["accent_gold"], radius=10, border=3)
        
        icon_text = self.font_large.render("🎁", True, self.COLORS["bg_dark"])
        surface.blit(icon_text, (x + 15, y + 15))
        
        name_text = self.font_medium.render(activity["name"], True, self.COLORS["bg_dark"])
        surface.blit(name_text, (x + 60, y + 12))
        
        time_text = self.font_small.render(f"剩余: {activity['time_left']}", 
                                          True, self.COLORS["bg_dark"])
        surface.blit(time_text, (x + 60, y + 38))
    
    def _get_active_activities(self):
        """获取当前活动"""
        activities = []
        
        season = data.get("season", {})
        season_points = season.get("season_points", 0)
        if season_points > 0:
            activities.append({
                "name": "赛季进行中",
                "time_left": f"{season.get('season_duration', 604800) // 86400}天"
            })
        
        daily_reward = data.get("daily_reward", {})
        if daily_reward.get("last_checkin_date") != time.strftime("%Y-%m-%d"):
            activities.append({
                "name": "每日签到待领取",
                "time_left": "今日有效"
            })
        
        return activities
    
    def draw_modern_button(self, surface, x, y, width, height, text, callback=None, button_type="primary"):
        """绘制现代化按钮"""
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = (x <= mouse_pos[0] <= x + width and y <= mouse_pos[1] <= y + height)
        
        colors = {
            "primary": (self.COLORS["accent_cyan"], self._lighten_color(self.COLORS["accent_cyan"], 20)),
            "secondary": (self.COLORS["accent_gold"], self._lighten_color(self.COLORS["accent_gold"], 20)),
            "danger": (self.COLORS["accent_red"], self._lighten_color(self.COLORS["accent_red"], 20)),
            "success": (self.COLORS["accent_green"], self._lighten_color(self.COLORS["accent_green"], 20))
        }
        
        color = colors.get(button_type, colors["primary"])
        current_color = color[1] if is_hovered else color[0]
        
        self.draw_rounded_rect(surface, (x, y, width, height), 
                               current_color, radius=8)
        
        text_surface = self.font_medium.render(text, True, self.COLORS["text_primary"])
        text_rect = text_surface.get_rect(center=(x + width//2, y + height//2))
        surface.blit(text_surface, text_rect)
        
        return is_hovered
    
    def get_clicked_action(self, x, y, action_size=60, gap=10):
        """获取点击的快捷操作"""
        total_width = len(self.quick_actions) * action_size + (len(self.quick_actions) - 1) * gap
        start_x = (self.screen_width - total_width) // 2
        bar_y = self.screen_height - 80 - action_size
        
        for i, action in enumerate(self.quick_actions):
            ax = start_x + i * (action_size + gap)
            ay = bar_y
            
            if ax <= x <= ax + action_size and ay <= y <= ay + action_size:
                return action["id"]
        
        return None


class NotificationSystem:
    """通知系统 - 借鉴冰河时代的推送机制"""
    
    def __init__(self):
        if "notifications" not in data:
            data["notifications"] = {
                "unread": [],
                "read": [],
                "settings": {
                    "daily_reminder": True,
                    "activity_alert": True,
                    "reward_notification": True
                }
            }
        
        self.notifications = data["notifications"]
    
    def add_notification(self, title, content, notification_type="system"):
        """添加通知"""
        notification = {
            "id": int(time.time() * 1000),
            "title": title,
            "content": content,
            "type": notification_type,
            "time": time.time(),
            "read": False
        }
        
        self.notifications["unread"].append(notification)
        
        if len(self.notifications["unread"]) > 50:
            old = self.notifications["unread"].pop(0)
            self.notifications["read"].append(old)
        
        save()
    
    def mark_as_read(self, notification_id):
        """标记为已读"""
        for notif in self.notifications["unread"]:
            if notif["id"] == notification_id:
                notif["read"] = True
                self.notifications["unread"].remove(notif)
                self.notifications["read"].append(notif)
                save()
                break
    
    def get_unread_count(self):
        """获取未读数量"""
        return len([n for n in self.notifications["unread"] if not n["read"]])
    
    def check_and_notify(self):
        """检查并发送通知"""
        settings = self.notifications["settings"]
        
        if settings["daily_reminder"]:
            self._check_daily_reminder()
        
        if settings["activity_alert"]:
            self._check_activity_alert()
        
        if settings["reward_notification"]:
            self._check_reward_notification()
    
    def _check_daily_reminder(self):
        """检查每日提醒"""
        daily_reward = data.get("daily_reward", {})
        if daily_reward.get("last_checkin_date") != time.strftime("%Y-%m-%d"):
            self.add_notification("📅 每日签到", "今日签到奖励待领取，点击前往领取！", "reminder")
    
    def _check_activity_alert(self):
        """检查活动提醒"""
        season = data.get("season", {})
        if season.get("season_points", 0) > 0:
            time_left = season.get("season_duration", 604800) - (time.time() - season.get("season_start_time", 0))
            if 0 < time_left < 86400:
                self.add_notification("🏆 赛季即将结束", "赛季即将结束，记得领取奖励！", "alert")
    
    def _check_reward_notification(self):
        """检查奖励通知"""
        achievements = data.get("achievements", {})
        unclaimed = [a for a in achievements.get("unlocked", []) 
                    if a not in achievements.get("claimed_rewards", [])]
        if unclaimed:
            self.add_notification("🏅 成就可领取", f"有{len(unclaimed)}个成就奖励待领取！", "reward")
