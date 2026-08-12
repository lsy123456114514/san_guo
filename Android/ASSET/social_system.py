"""社交系统 - 好友/公会/聊天窗口 UI 渲染"""

import os
import pygame
import random
import datetime
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
from ASSET import safe_exit

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
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 200),
    "panel_bg": (30, 30, 55, 200)
}

class Button:
    """按钮控件 - 渐变填充与悬停点击反馈"""
    def __init__(self, text, x, y, width, height, font, 
                 normal_color=COLORS["accent_blue"], 
                 hover_color=COLORS["accent_blue_light"], 
                 text_color=COLORS["text_white"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.is_clicked = False
        self.click_timer = 0
    
    def draw(self, surface):
        # 按钮颜色
        color = self.hover_color if self.is_hovered else self.normal_color
        if self.is_clicked:
            color = COLORS["accent_blue_dark"]
        
        # 渐变效果
        for i in range(self.rect.height):
            alpha = 255 - int(50 * (i / self.rect.height))
            gradient_color = tuple(min(255, c + 20) for c in color[:3])
            pygame.draw.line(surface, gradient_color, 
                           (self.rect.x, self.rect.y + i),
                           (self.rect.x + self.rect.width, self.rect.y + i))
        
        # 按钮边框
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=10)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 1, border_radius=10)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        # 文字阴影
        shadow_surf = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)
    
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

class ScrollableContainer:
    """滚动容器 - 支持滚轮、拖拽与键盘的列表区域"""
    def __init__(self, x, y, width, height, item_height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.item_height = item_height
        self.items = []
        self.scroll_offset = 0
        self.max_scroll = 0
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
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - self.item_height)
                return True
            elif event.key == pygame.K_DOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.item_height)
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
    
    def draw(self, surface, render_func):
        container_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        clip_rect = pygame.Rect(0, 0, self.width, self.height)
        container_surface.set_clip(clip_rect)
        
        for i, item in enumerate(self.items):
            item_y = self.y + i * self.item_height - self.scroll_offset
            if -self.item_height <= item_y <= self.height:
                render_func(container_surface, item, self.x, item_y)
        
        container_surface.set_clip(None)
        surface.blit(container_surface, (self.x, self.y))
        
        if self.max_scroll > 0:
            scrollbar_height = max(30, self.height * self.height / (len(self.items) * self.item_height))
            scrollbar_y = self.y + (self.height - scrollbar_height) * (self.scroll_offset / self.max_scroll if self.max_scroll > 0 else 0)
            
            pygame.draw.rect(surface, (80, 80, 100),
                           (self.x + self.width - 12, self.y + 5, 8, self.height - 10),
                           border_radius=4)
            pygame.draw.rect(surface, (150, 130, 80),
                           (self.x + self.width - 12, scrollbar_y, 8, scrollbar_height),
                           border_radius=4)

def draw_title(surface, text, y_pos, screen_width, font_big):
    """绘制带特效的标题"""
    # 发光效果
    for offset in range(5, 0, -1):
        alpha = 50 - offset * 8
        glow_surf = font_big.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    # 主标题
    title = font_big.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    
    # 阴影
    shadow = font_big.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)

def show_message(surface, message, font_main):
    """显示提示消息"""
    screen_width = surface.get_width()
    screen_height = surface.get_height()
    
    # 半透明遮罩
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))
    
    # 消息面板
    panel_width = 400
    panel_height = 150
    panel_x = (screen_width - panel_width) // 2
    panel_y = (screen_height - panel_height) // 2
    
    panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (40, 40, 70, 200), (0, 0, panel_width, panel_height), border_radius=15)
    surface.blit(panel_surf, (panel_x, panel_y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], 
                    (panel_x, panel_y, panel_width, panel_height), 3, border_radius=15)
    
    # 文字
    text_surf = font_main.render(message, True, COLORS["text_white"])
    text_rect = text_surf.get_rect(center=(screen_width // 2, panel_y + panel_height // 2))
    surface.blit(text_surf, text_rect)
    
    pygame.display.flip()
    pygame.time.wait(2000)

class PetSystem:
    """宠物系统"""
    def __init__(self):
        # 初始化宠物数据
        if "pets" not in data:
            data["pets"] = {
                "owned": [],
                "active": None
            }
        
        # 宠物列表
        self.pet_types = [
            {"name": "小火龙", "type": "fire", "rarity": "common", "effect": "资源产出+5%"},
            {"name": "水精灵", "type": "water", "rarity": "common", "effect": "冷却时间-5%"},
            {"name": "风之翼", "type": "wind", "rarity": "rare", "effect": "移动速度+10%"},
            {"name": "土元素", "type": "earth", "rarity": "rare", "effect": "防御+10%"},
            {"name": "光明天使", "type": "light", "rarity": "epic", "effect": "所有属性+8%"},
            {"name": "黑暗魔兽", "type": "dark", "rarity": "epic", "effect": "攻击+15%"}
        ]
    
    def get_pet_by_name(self, name):
        for pet in self.pet_types:
            if pet["name"] == name:
                return pet
        return None
    
    def adopt_pet(self, pet_name):
        """领养宠物"""
        pet = self.get_pet_by_name(pet_name)
        if pet:
            # 检查是否已经拥有
            for owned_pet in data["pets"]["owned"]:
                if owned_pet["name"] == pet_name:
                    return False, "已经拥有该宠物"
            
            # 添加宠物
            data["pets"]["owned"].append({
                "name": pet_name,
                "level": 1,
                "exp": 0,
                "happiness": 100,
                "last_fed": datetime.datetime.now().isoformat()
            })
            save()
            return True, f"成功领养 {pet_name}！"
        return False, "宠物不存在"
    
    def feed_pet(self, pet_name):
        """喂食宠物"""
        for pet in data["pets"]["owned"]:
            if pet["name"] == pet_name:
                pet["happiness"] = min(100, pet["happiness"] + 20)
                pet["last_fed"] = datetime.datetime.now().isoformat()
                save()
                return True, f"{pet_name} 吃饱了！"
        return False, "宠物不存在"
    
    def activate_pet(self, pet_name):
        """激活宠物"""
        for pet in data["pets"]["owned"]:
            if pet["name"] == pet_name:
                data["pets"]["active"] = pet_name
                save()
                return True, f"{pet_name} 已激活！"
        return False, "宠物不存在"

class TaskSystem:
    """任务系统"""
    def __init__(self):
        # 初始化任务数据
        if "tasks" not in data:
            data["tasks"] = {
                "daily": [],
                "main": [],
                "completed": []
            }
        
        # 每日任务
        self.daily_tasks = [
            {"id": "daily_1", "name": "完成1次PVP", "reward": {"金元宝": 50}, "progress": 0, "target": 1},
            {"id": "daily_2", "name": "收集100资源", "reward": {"水": 100, "木头": 100}, "progress": 0, "target": 100},
            {"id": "daily_3", "name": "登录游戏", "reward": {"时间卡": 1}, "progress": 0, "target": 1}
        ]
        
        # 主线任务
        self.main_tasks = [
            {"id": "main_1", "name": "完成新手教程", "reward": {"金元宝": 100, "武将碎片": {"张飞": 5}}, "progress": 0, "target": 1},
            {"id": "main_2", "name": "等级达到5级", "reward": {"金元宝": 200, "装备": {"武器": 1}}, "progress": 0, "target": 5},
            {"id": "main_3", "name": "收集5个武将", "reward": {"金元宝": 300, "时间卡+": 1}, "progress": 0, "target": 5}
        ]
        
        # 初始化任务
        self.init_tasks()
    
    def init_tasks(self):
        """初始化任务"""
        # 确保 tasks 数据存在（兼容旧存档/缺键情况）
        tasks = data.setdefault("tasks", {})
        tasks.setdefault("daily", [])
        tasks.setdefault("main", [])
        # 检查每日任务
        today = datetime.date.today().isoformat()
        if "last_daily_reset" not in data or data["last_daily_reset"] != today:
            tasks["daily"] = []
            for task in self.daily_tasks:
                tasks["daily"].append(task.copy())
            data["last_daily_reset"] = today
            save()
        
        # 检查主线任务
        if not tasks["main"]:
            for task in self.main_tasks:
                tasks["main"].append(task.copy())
            save()
    
    def complete_task(self, task_id):
        """完成任务"""
        # 检查每日任务
        for task in data["tasks"]["daily"]:
            if task["id"] == task_id and task["progress"] >= task["target"]:
                # 发放奖励
                for resource, amount in task["reward"].items():
                    if isinstance(amount, dict):
                        # 处理特殊奖励如武将碎片
                        for sub_resource, sub_amount in amount.items():
                            if sub_resource not in data:
                                data[sub_resource] = {}
                            data[sub_resource][sub_resource] = data[sub_resource].get(sub_resource, 0) + sub_amount
                    else:
                        # 处理普通资源
                        data["resources"][resource] = data["resources"].get(resource, 0) + amount
                
                # 移动到已完成
                data["tasks"]["completed"].append(task)
                data["tasks"]["daily"].remove(task)
                save()
                return True, "任务完成！"
        
        # 检查主线任务
        for task in data["tasks"]["main"]:
            if task["id"] == task_id and task["progress"] >= task["target"]:
                # 发放奖励
                for resource, amount in task["reward"].items():
                    if isinstance(amount, dict):
                        # 处理特殊奖励如武将碎片
                        for sub_resource, sub_amount in amount.items():
                            if sub_resource not in data:
                                data[sub_resource] = {}
                            data[sub_resource][sub_resource] = data[sub_resource].get(sub_resource, 0) + sub_amount
                    else:
                        # 处理普通资源
                        data["resources"][resource] = data["resources"].get(resource, 0) + amount
                
                # 移动到已完成
                data["tasks"]["completed"].append(task)
                data["tasks"]["main"].remove(task)
                save()
                return True, "任务完成！"
        
        return False, "任务未完成"

class MailSystem:
    """邮件系统"""
    def __init__(self):
        # 初始化邮件数据
        if "mail" not in data:
            data["mail"] = {
                "inbox": [],
                "sent": []
            }
    
    def send_mail(self, subject, content, sender="系统", rewards=None):
        """发送邮件"""
        mail_id = f"mail_{datetime.datetime.now().timestamp()}"
        mail = {
            "id": mail_id,
            "subject": subject,
            "content": content,
            "sender": sender,
            "timestamp": datetime.datetime.now().isoformat(),
            "read": False,
            "rewards": rewards or {}
        }
        data["mail"]["inbox"].append(mail)
        save()
        return True, "邮件发送成功"
    
    def read_mail(self, mail_id):
        """读取邮件"""
        for mail in data["mail"]["inbox"]:
            if mail["id"] == mail_id:
                mail["read"] = True
                save()
                return True, mail
        return False, "邮件不存在"
    
    def claim_rewards(self, mail_id):
        """领取邮件奖励"""
        for mail in data["mail"]["inbox"]:
            if mail["id"] == mail_id:
                # 发放奖励
                for resource, amount in mail["rewards"].items():
                    data["resources"][resource] = data["resources"].get(resource, 0) + amount
                
                # 移动到已发送
                data["mail"]["sent"].append(mail)
                data["mail"]["inbox"].remove(mail)
                save()
                return True, "奖励领取成功"
        return False, "邮件不存在"

class FriendSystem:
    """好友系统"""
    def __init__(self):
        # 初始化好友数据
        if "friends" not in data:
            data["friends"] = {
                "list": [],
                "requests": []
            }
    
    def send_friend_request(self, username):
        """发送好友请求"""
        # 检查是否已经是好友
        for friend in data["friends"]["list"]:
            if friend["username"] == username:
                return False, "已经是好友"
        
        # 检查是否已经发送过请求
        for request in data["friends"]["requests"]:
            if request["from"] == username:
                return False, "已经发送过请求"
        
        # 发送请求
        request_id = f"req_{datetime.datetime.now().timestamp()}"
        request = {
            "id": request_id,
            "from": username,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "pending"
        }
        data["friends"]["requests"].append(request)
        save()
        return True, "好友请求已发送"
    
    def accept_friend_request(self, request_id):
        """接受好友请求"""
        for request in data["friends"]["requests"]:
            if request["id"] == request_id:
                # 添加好友
                friend = {
                    "username": request["from"],
                    "since": datetime.datetime.now().isoformat(),
                    "last_interaction": datetime.datetime.now().isoformat()
                }
                data["friends"]["list"].append(friend)
                
                # 移除请求
                data["friends"]["requests"].remove(request)
                save()
                return True, "好友请求已接受"
        return False, "请求不存在"
    
    def remove_friend(self, username):
        """移除好友"""
        for friend in data["friends"]["list"]:
            if friend["username"] == username:
                data["friends"]["list"].remove(friend)
                save()
                return True, "好友已移除"
        return False, "好友不存在"

def draw_pet_system(screen, font_big, font_main, font_small):
    """绘制宠物系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "宠物系统", screen_height * 0.1, screen_width, font_big)
    
    pet_system = PetSystem()
    
    # 宠物列表
    y_offset = screen_height * 0.2
    for pet in pet_system.pet_types:
        pet_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
        
        # 背景
        pygame.draw.rect(screen, (40, 40, 70, 200), pet_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], pet_rect, 2, border_radius=10)
        
        # 宠物信息
        name_surf = font_main.render(pet["name"], True, COLORS["accent_gold"])
        type_surf = font_small.render(f"类型: {pet['type']}", True, COLORS["text_white"])
        rarity_surf = font_small.render(f"稀有度: {pet['rarity']}", True, COLORS["text_gray"])
        effect_surf = font_small.render(f"效果: {pet['effect']}", True, COLORS["text_white"])
        
        screen.blit(name_surf, (60, y_offset + 10))
        screen.blit(type_surf, (60, y_offset + 35))
        screen.blit(rarity_surf, (60, y_offset + 55))
        screen.blit(effect_surf, (200, y_offset + 35))
        
        # 领养按钮
        adopt_btn = Button("领养", screen_width - 150, y_offset + 20, 100, 40, font_small)
        adopt_btn.draw(screen)
        
        y_offset += 90

def draw_task_system(screen, font_big, font_main, font_small):
    """绘制任务系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "任务系统", screen_height * 0.1, screen_width, font_big)
    
    task_system = TaskSystem()
    
    # 每日任务
    y_offset = screen_height * 0.2
    daily_title = font_main.render("每日任务", True, COLORS["accent_blue"])
    screen.blit(daily_title, (50, y_offset))
    y_offset += 40
    
    for task in data["tasks"]["daily"]:
        task_rect = pygame.Rect(50, y_offset, screen_width - 100, 60)
        
        # 背景
        pygame.draw.rect(screen, (40, 40, 70, 200), task_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], task_rect, 2, border_radius=10)
        
        # 任务信息
        name_surf = font_main.render(task["name"], True, COLORS["text_white"])
        progress_surf = font_small.render(f"进度: {task['progress']}/{task['target']}", True, COLORS["text_gray"])
        reward_text = ", ".join([f"{k}:{v}" for k, v in task["reward"].items()])
        reward_surf = font_small.render(f"奖励: {reward_text}", True, COLORS["accent_gold"])
        
        screen.blit(name_surf, (60, y_offset + 10))
        screen.blit(progress_surf, (60, y_offset + 35))
        screen.blit(reward_surf, (250, y_offset + 35))
        
        # 完成按钮
        if task["progress"] >= task["target"]:
            complete_btn = Button("完成", screen_width - 150, y_offset + 10, 100, 40, font_small, normal_color=COLORS["accent_green"])
            complete_btn.draw(screen)
        
        y_offset += 70
    
    # 主线任务
    y_offset += 20
    main_title = font_main.render("主线任务", True, COLORS["accent_purple"])
    screen.blit(main_title, (50, y_offset))
    y_offset += 40
    
    for task in data["tasks"]["main"]:
        task_rect = pygame.Rect(50, y_offset, screen_width - 100, 60)
        
        # 背景
        pygame.draw.rect(screen, (40, 40, 70, 200), task_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], task_rect, 2, border_radius=10)
        
        # 任务信息
        name_surf = font_main.render(task["name"], True, COLORS["text_white"])
        progress_surf = font_small.render(f"进度: {task['progress']}/{task['target']}", True, COLORS["text_gray"])
        reward_text = ", ".join([f"{k}:{v}" for k, v in task["reward"].items()])
        reward_surf = font_small.render(f"奖励: {reward_text}", True, COLORS["accent_gold"])
        
        screen.blit(name_surf, (60, y_offset + 10))
        screen.blit(progress_surf, (60, y_offset + 35))
        screen.blit(reward_surf, (250, y_offset + 35))
        
        # 完成按钮
        if task["progress"] >= task["target"]:
            complete_btn = Button("完成", screen_width - 150, y_offset + 10, 100, 40, font_small, normal_color=COLORS["accent_green"])
            complete_btn.draw(screen)
        
        y_offset += 70

def draw_mail_system(screen, font_big, font_main, font_small):
    """绘制邮件系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "邮件系统", screen_height * 0.1, screen_width, font_big)
    
    mail_system = MailSystem()
    
    # 邮件列表
    y_offset = screen_height * 0.2
    for mail in data["mail"]["inbox"]:
        mail_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
        
        # 背景
        if not mail["read"]:
            pygame.draw.rect(screen, (40, 60, 90, 200), mail_rect, border_radius=10)
        else:
            pygame.draw.rect(screen, (40, 40, 70, 200), mail_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], mail_rect, 2, border_radius=10)
        
        # 邮件信息
        subject_surf = font_main.render(mail["subject"], True, COLORS["accent_gold"])
        sender_surf = font_small.render(f"发件人: {mail['sender']}", True, COLORS["text_gray"])
        time_surf = font_small.render(mail["timestamp"].split("T")[0], True, COLORS["text_gray"])
        content_surf = font_small.render(mail["content"][:30] + "...", True, COLORS["text_white"])
        
        screen.blit(subject_surf, (60, y_offset + 10))
        screen.blit(sender_surf, (60, y_offset + 35))
        screen.blit(time_surf, (200, y_offset + 35))
        screen.blit(content_surf, (60, y_offset + 55))
        
        # 领取奖励按钮
        if mail["rewards"]:
            claim_btn = Button("领取", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
            claim_btn.draw(screen)
        
        y_offset += 90

def draw_friend_system(screen, font_big, font_main, font_small):
    """绘制好友系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "好友系统", screen_height * 0.1, screen_width, font_big)
    
    friend_system = FriendSystem()
    
    # 好友列表
    y_offset = screen_height * 0.2
    friend_title = font_main.render("好友列表", True, COLORS["accent_blue"])
    screen.blit(friend_title, (50, y_offset))
    y_offset += 40
    
    if not data["friends"]["list"]:
        empty_surf = font_small.render("暂无好友，添加一些好友吧！", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for friend in data["friends"]["list"]:
            friend_rect = pygame.Rect(50, y_offset, screen_width - 100, 60)
            
            # 背景
            pygame.draw.rect(screen, (40, 40, 70, 200), friend_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["accent_gold"], friend_rect, 2, border_radius=10)
            
            # 好友信息
            name_surf = font_main.render(friend["username"], True, COLORS["text_white"])
            since_surf = font_small.render(f"好友时间: {friend['since'].split('T')[0]}", True, COLORS["text_gray"])
            
            screen.blit(name_surf, (60, y_offset + 10))
            screen.blit(since_surf, (60, y_offset + 35))
            
            # 移除好友按钮
            remove_btn = Button("移除", screen_width - 150, y_offset + 10, 100, 40, font_small, normal_color=COLORS["accent_red"])
            remove_btn.draw(screen)
            
            y_offset += 70
    
    # 好友请求
    y_offset += 20
    request_title = font_main.render("好友请求", True, COLORS["accent_purple"])
    screen.blit(request_title, (50, y_offset))
    y_offset += 40
    
    if not data["friends"]["requests"]:
        empty_surf = font_small.render("暂无好友请求", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for request in data["friends"]["requests"]:
            request_rect = pygame.Rect(50, y_offset, screen_width - 100, 60)
            
            # 背景
            pygame.draw.rect(screen, (40, 40, 70, 200), request_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["accent_gold"], request_rect, 2, border_radius=10)
            
            # 请求信息
            from_surf = font_main.render(f"来自: {request['from']}", True, COLORS["text_white"])
            time_surf = font_small.render(request["timestamp"].split("T")[0], True, COLORS["text_gray"])
            
            screen.blit(from_surf, (60, y_offset + 10))
            screen.blit(time_surf, (60, y_offset + 35))
            
            # 接受按钮
            accept_btn = Button("接受", screen_width - 260, y_offset + 10, 100, 40, font_small, normal_color=COLORS["accent_green"])
            accept_btn.draw(screen)
            
            # 拒绝按钮
            reject_btn = Button("拒绝", screen_width - 150, y_offset + 10, 100, 40, font_small, normal_color=COLORS["accent_red"])
            reject_btn.draw(screen)
            
            y_offset += 70

def main():
    """社交系统主函数"""
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
                SCREEN_WIDTH = 900
                SCREEN_HEIGHT = 700
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("社交系统")
        clock = pygame.time.Clock()

        # 字体初始化（根据屏幕大小自适应）
        def init_font(size):
            return get_font(size)

        font_big = init_font(48)
        font_main = init_font(32)
        font_small = init_font(24)

        # 系统初始化
        pet_system = PetSystem()
        task_system = TaskSystem()
        mail_system = MailSystem()
        friend_system = FriendSystem()
        
        # 发送欢迎邮件
        if not data["mail"]["inbox"]:
            mail_system.send_mail(
                "欢迎来到社交系统",
                "恭喜你解锁了社交系统！在这里你可以领养宠物、完成任务、收发邮件和添加好友。",
                "系统",
                {"金元宝": 100, "时间卡": 1}
            )

        # 当前页面（默认好友页，即社交主功能）
        current_page = "friend"  # pet, task, mail, friend
        
        # 滚动容器
        pet_container = ScrollableContainer(50, 120, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200, 90)
        task_container = ScrollableContainer(50, 120, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200, 90)
        mail_container = ScrollableContainer(50, 120, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200, 100)
        friend_container = ScrollableContainer(50, 120, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200, 80)

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 导航按钮
            nav_buttons = [
                ("宠物系统", "pet", 50, SCREEN_HEIGHT - 70),
                ("任务系统", "task", 200, SCREEN_HEIGHT - 70),
                ("邮件系统", "mail", 350, SCREEN_HEIGHT - 70),
                ("好友系统", "friend", 500, SCREEN_HEIGHT - 70),
                ("返回", "back", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70)
            ]
            
            for text, page, x, y in nav_buttons:
                btn = Button(text, x, y, 120, 50, font_small)
                btn.check_hover((mx, my))
                btn.draw(screen)
            
            # 绘制当前页面
            if current_page == "pet":
                draw_title(screen, "宠物系统", SCREEN_HEIGHT * 0.1, SCREEN_WIDTH, font_big)
                pet_system = PetSystem()
                pet_container.set_items(pet_system.pet_types)
                
                def render_pet(surface, pet, x, y):
                    screen_width = surface.get_width()
                    pet_rect = pygame.Rect(0, y - 120, screen_width, 80)
                    pygame.draw.rect(surface, (40, 40, 70, 200), pet_rect, border_radius=10)
                    pygame.draw.rect(surface, COLORS["accent_gold"], pet_rect, 2, border_radius=10)
                    
                    name_surf = font_main.render(pet["name"], True, COLORS["accent_gold"])
                    type_surf = font_small.render(f"类型: {pet['type']}", True, COLORS["text_white"])
                    rarity_surf = font_small.render(f"稀有度: {pet['rarity']}", True, COLORS["text_gray"])
                    effect_surf = font_small.render(f"效果: {pet['effect']}", True, COLORS["text_white"])
                    
                    surface.blit(name_surf, (10, y - 120 + 10))
                    surface.blit(type_surf, (10, y - 120 + 35))
                    surface.blit(rarity_surf, (10, y - 120 + 55))
                    surface.blit(effect_surf, (150, y - 120 + 35))
                    
                    adopt_btn = Button("领养", screen_width - 110, y - 120 + 20, 100, 40, font_small)
                    adopt_btn.draw(surface)
                
                pet_container.draw(screen, render_pet)
            elif current_page == "task":
                draw_title(screen, "任务系统", SCREEN_HEIGHT * 0.1, SCREEN_WIDTH, font_big)
                task_system = TaskSystem()
                all_tasks = data["tasks"]["daily"] + data["tasks"]["main"]
                task_container.set_items(all_tasks)
                
                def render_task(surface, task, x, y):
                    screen_width = surface.get_width()
                    task_rect = pygame.Rect(0, y - 120, screen_width, 80)
                    pygame.draw.rect(surface, (40, 40, 70, 200), task_rect, border_radius=10)
                    pygame.draw.rect(surface, COLORS["accent_gold"], task_rect, 2, border_radius=10)
                    
                    name_surf = font_main.render(task["name"], True, COLORS["accent_gold"])
                    desc_surf = font_small.render(task.get("description", task["name"]), True, COLORS["text_white"])
                    _rewards = task.get("reward", {}) or task.get("rewards", {})
                    reward_text = ", ".join([f"{k}:{v}" for k, v in _rewards.items()])
                    reward_surf = font_small.render(f"奖励: {reward_text}", True, COLORS["text_gray"])
                    
                    surface.blit(name_surf, (10, y - 120 + 10))
                    surface.blit(desc_surf, (10, y - 120 + 35))
                    surface.blit(reward_surf, (10, y - 120 + 55))
                    
                    complete_btn = Button("完成", screen_width - 110, y - 120 + 20, 100, 40, font_small)
                    complete_btn.draw(surface)
                
                task_container.draw(screen, render_task)
            elif current_page == "mail":
                draw_title(screen, "邮件系统", SCREEN_HEIGHT * 0.1, SCREEN_WIDTH, font_big)
                mail_container.set_items(data["mail"]["inbox"])
                
                def render_mail(surface, mail, x, y):
                    screen_width = surface.get_width()
                    mail_rect = pygame.Rect(0, y - 120, screen_width, 90)
                    bg_color = (40, 60, 90, 200) if mail["read"] else (40, 40, 70, 200)
                    pygame.draw.rect(surface, bg_color, mail_rect, border_radius=10)
                    pygame.draw.rect(surface, COLORS["accent_gold"], mail_rect, 2, border_radius=10)
                    
                    subject_surf = font_main.render(mail["subject"], True, COLORS["accent_gold"])
                    sender_surf = font_small.render(f"发件人: {mail['sender']}", True, COLORS["text_white"])
                    time_surf = font_small.render(mail.get("timestamp", mail.get("time", "未知时间")), True, COLORS["text_gray"])
                    
                    surface.blit(subject_surf, (10, y - 120 + 10))
                    surface.blit(sender_surf, (10, y - 120 + 40))
                    surface.blit(time_surf, (10, y - 120 + 65))
                    
                    read_btn = Button("读取", screen_width - 110, y - 120 + 25, 100, 40, font_small)
                    read_btn.draw(surface)
                
                mail_container.draw(screen, render_mail)
            elif current_page == "friend":
                draw_title(screen, "好友系统", SCREEN_HEIGHT * 0.1, SCREEN_WIDTH, font_big)
                friend_container.set_items(data["friends"]["list"] + data["friends"]["requests"])
                
                def render_friend(surface, friend, x, y):
                    screen_width = surface.get_width()
                    friend_rect = pygame.Rect(0, y - 120, screen_width, 70)
                    pygame.draw.rect(surface, (40, 40, 70, 200), friend_rect, border_radius=10)
                    pygame.draw.rect(surface, COLORS["accent_gold"], friend_rect, 2, border_radius=10)
                    
                    name_surf = font_main.render(friend.get("username") or friend.get("from", "未知玩家"), True, COLORS["accent_gold"])
                    status_surf = font_small.render(f"状态: 在线" if friend.get("status", "online") == "online" else "状态: 离线", True, COLORS["text_white"])
                    
                    surface.blit(name_surf, (10, y - 120 + 10))
                    surface.blit(status_surf, (10, y - 120 + 40))
                    
                    if friend.get("status") == "pending":
                        accept_btn = Button("接受", screen_width - 110, y - 120 + 15, 100, 40, font_small)
                        accept_btn.draw(surface)
                    else:
                        chat_btn = Button("聊天", screen_width - 110, y - 120 + 15, 100, 40, font_small)
                        chat_btn.draw(surface)
                
                friend_container.draw(screen, render_friend)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 处理导航按钮
                    for text, page, x, y in nav_buttons:
                        btn = Button(text, x, y, 120, 50, font_small)
                        if btn.rect.collidepoint(event.pos):
                            if page == "back":
                                running = False
                            else:
                                current_page = page
                            break
                    
                    # 处理滚动容器中的点击
                    if current_page == "pet":
                        pet = pet_container.get_item_at(mx, my)
                        if pet:
                            logger.info(f"点击了宠物: {pet['name']}")
                    elif current_page == "task":
                        task = task_container.get_item_at(mx, my)
                        if task:
                            logger.info(f"点击了任务: {task['name']}")
                    elif current_page == "mail":
                        mail = mail_container.get_item_at(mx, my)
                        if mail:
                            logger.info(f"点击了邮件: {mail['subject']}")
                    elif current_page == "friend":
                        friend = friend_container.get_item_at(mx, my)
                        if friend:
                            logger.info(f"点击了好友: {friend['username']}")
                
                # 处理滚动事件
                if current_page == "pet":
                    pet_container.handle_event(event)
                elif current_page == "task":
                    task_container.handle_event(event)
                elif current_page == "mail":
                    mail_container.handle_event(event)
                elif current_page == "friend":
                    friend_container.handle_event(event)
            
            clock.tick(60)
        
        return
    except Exception as e:
        logger.info(f"异常：{str(e)}")
        logger.info("详细错误信息：")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
