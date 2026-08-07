import pygame
import random
import json
import time
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
from ASSET import safe_exit

class EventSystem:
    def __init__(self):
        self.events = []
        self.current_event = None
        
        # 从存档加载事件系统数据
        event_data = data.get("event_system", {})
        self.event_history = event_data.get("event_history", [])
        self.last_event_time = event_data.get("last_event_time", 0)
        self.event_cooldown = event_data.get("event_cooldown", 30)
        
        # 初始化事件列表
        self.init_events()
    
    def save_to_data(self):
        """保存事件系统数据到存档"""
        data["event_system"] = {
            "event_history": self.event_history,
            "last_event_time": self.last_event_time,
            "event_cooldown": self.event_cooldown
        }
        save()
    
    def init_events(self):
        """初始化事件列表"""
        # 随机事件
        self.random_events = [
            {
                "id": "random_merchant",
                "name": "神秘商人",
                "description": "一位神秘的商人出现在你面前，他愿意以优惠价格出售稀有物品",
                "icon": "🧙‍♂️",
                "type": "random",
                "probability": 0.15,
                "choices": [
                    {"text": "购买稀有装备", "cost": {"金元宝": 200}, "reward": {"equipment": "legendary"}},
                    {"text": "购买神秘宝箱", "cost": {"金元宝": 100}, "reward": {"random_resource": 500}},
                    {"text": "拒绝", "cost": {}, "reward": {}}
                ]
            },
            {
                "id": "random_ambush",
                "name": "遭遇伏击",
                "description": "你被一群强盗伏击！必须战斗才能继续前进",
                "icon": "⚔️",
                "type": "random",
                "probability": 0.1,
                "choices": [
                    {"text": "战斗", "cost": {}, "reward": {"gold": 100, "exp": 50}, "battle": True},
                    {"text": "逃跑", "cost": {"gold": 50}, "reward": {}, "success_rate": 0.7}
                ]
            },
            {
                "id": "random_treasure",
                "name": "发现宝藏",
                "description": "你发现了一个古老的宝箱，里面可能藏有珍贵的宝物",
                "icon": "💎",
                "type": "random",
                "probability": 0.12,
                "choices": [
                    {"text": "打开宝箱", "cost": {}, "reward": {"random_resource": 300}, "success_rate": 0.8},
                    {"text": "谨慎离开", "cost": {}, "reward": {}}
                ]
            },
            {
                "id": "random_healer",
                "name": "神秘医者",
                "description": "一位神秘的医者愿意为你治疗伤病",
                "icon": "🏥",
                "type": "random",
                "probability": 0.1,
                "choices": [
                    {"text": "接受治疗", "cost": {"金元宝": 50}, "reward": {"heal_all": True}},
                    {"text": "拒绝", "cost": {}, "reward": {}}
                ]
            },
            {
                "id": "random_recruit",
                "name": "武将投靠",
                "description": "一位流浪的武将愿意投靠你",
                "icon": "🎖️",
                "type": "random",
                "probability": 0.08,
                "choices": [
                    {"text": "接纳", "cost": {"金元宝": 150}, "reward": {"hero": "random"}},
                    {"text": "婉拒", "cost": {}, "reward": {}}
                ]
            },
            {
                "id": "random_storm",
                "name": "突发风暴",
                "description": "一场突如其来的风暴来袭，你需要做出选择",
                "icon": "🌪️",
                "type": "random",
                "probability": 0.1,
                "choices": [
                    {"text": "寻找庇护", "cost": {"时间卡": 1}, "reward": {"safe": True}},
                    {"text": "冒雨前进", "cost": {"health": -20}, "reward": {"speed_bonus": True}}
                ]
            },
            {
                "id": "random_trader",
                "name": "友好商人",
                "description": "一位友好的商人愿意与你交易",
                "icon": "🏪",
                "type": "random",
                "probability": 0.15,
                "choices": [
                    {"text": "交换资源", "cost": {"木头": 100}, "reward": {"金元宝": 80}},
                    {"text": "购买食物", "cost": {"金元宝": 30}, "reward": {"食物": 150}},
                    {"text": "离开", "cost": {}, "reward": {}}
                ]
            },
            {
                "id": "random_blessing",
                "name": "神明祝福",
                "description": "你受到了神明的祝福",
                "icon": "✨",
                "type": "random",
                "probability": 0.05,
                "choices": [
                    {"text": "接受祝福", "cost": {}, "reward": {"all_stats_bonus": 0.1, "duration": 300}}
                ]
            }
        ]
        
        # 剧情事件
        self.story_events = [
            {
                "id": "story_intro",
                "name": "初入乱世",
                "description": "东汉末年，天下大乱。你作为一方诸侯，立志平定乱世，拯救苍生。你的征程从这里开始...",
                "icon": "📜",
                "type": "story",
                "trigger_condition": {"normal_dungeon": 1},
                "choices": [
                    {"text": "开始征程", "cost": {}, "reward": {"starter_hero": True}}
                ]
            },
            {
                "id": "story_taoyuan",
                "name": "桃园结义",
                "description": "你遇到了两位志同道合的豪杰，三人意气相投，决定结拜为兄弟！",
                "icon": "🌸",
                "type": "story",
                "trigger_condition": {"normal_dungeon": 3},
                "choices": [
                    {"text": "桃园结义", "cost": {}, "reward": {"gold": 300, "bond_bonus": "taoyuan"}}
                ]
            },
            {
                "id": "story_first_victory",
                "name": "初战告捷",
                "description": "你率领军队取得了第一场胜利！士气大振，士兵们对你更加信服。",
                "icon": "🏆",
                "type": "story",
                "trigger_condition": {"normal_dungeon": 5},
                "choices": [
                    {"text": "继续前进", "cost": {}, "reward": {"gold": 500, "exp_bonus": 0.2}}
                ]
            },
            {
                "id": "story_strategy",
                "name": "谋士献策",
                "description": "一位智者前来投奔，献上奇策，助你成就霸业！",
                "icon": "🧠",
                "type": "story",
                "trigger_condition": {"normal_dungeon": 8},
                "choices": [
                    {"text": "采纳妙计", "cost": {}, "reward": {"gold": 800, "strategy_bonus": 0.15}}
                ]
            },
            {
                "id": "story_recruit_hero",
                "name": "名将归附",
                "description": "一位著名的武将听闻你的威名，愿意前来归附！",
                "icon": "🌟",
                "type": "story",
                "trigger_condition": {"normal_dungeon": 10},
                "choices": [
                    {"text": "欢迎加入", "cost": {}, "reward": {"hero": "legendary"}}
                ]
            },
            {
                "id": "story_alliance",
                "name": "结盟抗敌",
                "description": "诸侯联军集结，共同对抗强大的敌人。你决定加入联盟！",
                "icon": "🤝",
                "type": "story",
                "trigger_condition": {"normal_dungeon": 12},
                "choices": [
                    {"text": "加入联军", "cost": {"金元宝": 200}, "reward": {"alliance_bonus": 0.1, "gold": 600}}
                ]
            },
            {
                "id": "story_boss_appear",
                "name": "强敌出现",
                "description": "传说中的猛将出现了！这将是一场艰难的战斗...",
                "icon": "👹",
                "type": "story",
                "trigger_condition": {"normal_dungeon": 15},
                "choices": [
                    {"text": "迎战！", "cost": {}, "reward": {"boss_battle": True}}
                ]
            },
            {
                "id": "story_kingdom",
                "name": "建立王国",
                "description": "经过无数战斗，你终于建立了自己的王国！万民敬仰，霸业初成。",
                "icon": "👑",
                "type": "story",
                "trigger_condition": {"normal_dungeon": 20},
                "choices": [
                    {"text": "登基称王", "cost": {}, "reward": {"king_title": True, "permanent_bonus": 0.1}}
                ]
            }
        ]
    
    def check_event(self):
        """检查是否应该触发事件"""
        current_time = time.time()
        
        # 检查冷却时间
        if current_time - self.last_event_time < self.event_cooldown:
            return None
        
        # 检查剧情事件
        for event in self.story_events:
            if event["id"] not in self.event_history:
                condition = event.get("trigger_condition", {})
                if self.check_condition(condition):
                    self.last_event_time = current_time
                    return event
        
        # 检查随机事件
        for event in self.random_events:
            if random.random() < event["probability"]:
                self.last_event_time = current_time
                return event
        
        return None
    
    def check_condition(self, condition):
        """检查条件是否满足"""
        for key, value in condition.items():
            if data.get(key, 0) >= value:
                return True
        return False
    
    def trigger_event(self, event_id):
        """触发指定事件"""
        # 查找事件
        for event in self.random_events + self.story_events:
            if event["id"] == event_id:
                self.current_event = event
                return event
        return None
    
    def handle_choice(self, choice_index):
        """处理玩家选择"""
        if not self.current_event:
            return None, False
        
        choice = self.current_event["choices"][choice_index]
        
        # 检查资源是否足够
        for resource, amount in choice.get("cost", {}).items():
            if data["resources"].get(resource, 0) < amount:
                return "资源不足", False
        
        # 消耗资源
        for resource, amount in choice.get("cost", {}).items():
            if amount > 0:
                data["resources"][resource] -= amount
        
        # 检查成功率
        success_rate = choice.get("success_rate", 1.0)
        if random.random() > success_rate:
            self.event_history.append(self.current_event["id"])
            self.current_event = None
            return "失败了...", False
        
        # 发放奖励
        reward = choice.get("reward", {})
        self.apply_reward(reward)
        
        # 记录事件历史
        self.event_history.append(self.current_event["id"])
        self.save_to_data()  # 保存到存档
        event_name = self.current_event["name"]
        self.current_event = None
        
        return f"事件完成！", True
    
    def apply_reward(self, reward):
        """应用奖励"""
        # 更新剧情进度
        if "story_progress" not in data:
            data["story_progress"] = {
                "current_chapter": 0,
                "completed_events": [],
                "unlocked_endings": []
            }
        
        for key, value in reward.items():
            if key == "gold":
                data["resources"]["金元宝"] += value
            elif key == "exp":
                # 添加经验值逻辑
                pass
            elif key == "exp_bonus":
                # 添加经验加成
                pass
            elif key == "random_resource":
                resources = ["水", "煤炭", "木头", "食物", "金元宝"]
                resource = random.choice(resources)
                data["resources"][resource] += value
            elif key == "heal_all":
                # 治疗所有武将
                pass
            elif key == "hero":
                # 添加武将
                if value == "random":
                    heroes = ["赵云", "关羽", "张飞", "马超", "黄忠", "诸葛亮"]
                    hero_name = random.choice(heroes)
                    if hero_name not in data["heroes"]:
                        data["heroes"][hero_name] = {"star": 1, "level": 1}
                elif value == "legendary":
                    heroes = ["吕布", "曹操", "周瑜"]
                    hero_name = random.choice(heroes)
                    if hero_name not in data["heroes"]:
                        data["heroes"][hero_name] = {"star": 2, "level": 5}
            elif key == "equipment":
                # 添加装备
                pass
            elif key == "all_stats_bonus":
                # 添加属性加成
                data["event_bonus"] = {"attack": value, "defense": value, "duration": reward.get("duration", 300), "start_time": time.time()}
            elif key == "permanent_bonus":
                data["permanent_bonus"] = value
            elif key == "starter_hero":
                # 添加初始武将
                if "heroes" not in data or len(data["heroes"]) == 0:
                    data["heroes"] = {"赵云": {"star": 1, "level": 1}}
            elif key == "boss_battle":
                # 设置boss战斗标记
                data["story_progress"]["boss_battle"] = True
            elif key == "king_title":
                # 设置王者称号
                data["story_progress"]["king_title"] = True
        
        save()
    
    def get_current_event(self):
        """获取当前事件"""
        return self.current_event

class EventDialog:
    """事件对话框"""
    def __init__(self, screen, font_title, font_main, font_small):
        self.screen = screen
        self.font_title = font_title
        self.font_main = font_main
        self.font_small = font_small
        self.active = False
        self.event = None
        self.selected_choice = -1
        
    def show(self, event):
        """显示事件对话框"""
        self.event = event
        self.active = True
        self.selected_choice = -1
        
    def hide(self):
        """隐藏对话框"""
        self.active = False
        self.event = None
        
    def draw(self):
        """绘制对话框"""
        if not self.active or not self.event:
            return
        
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # 半透明遮罩
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 对话框背景
        dialog_width = min(600, screen_width - 40)
        dialog_height = min(500, screen_height - 100)
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        dialog_surf = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
        pygame.draw.rect(dialog_surf, (40, 40, 70, 220), (0, 0, dialog_width, dialog_height), border_radius=20)
        self.screen.blit(dialog_surf, (dialog_x, dialog_y))
        
        # 边框
        pygame.draw.rect(self.screen, (255, 215, 0), (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=20)
        
        # 标题区域
        title_y = dialog_y + 30
        icon_surf = self.font_title.render(self.event["icon"], True, (255, 215, 0))
        icon_rect = icon_surf.get_rect(left=dialog_x + 30, top=title_y)
        self.screen.blit(icon_surf, icon_rect)
        
        title_surf = self.font_title.render(self.event["name"], True, (255, 215, 0))
        title_rect = title_surf.get_rect(left=dialog_x + 80, top=title_y)
        self.screen.blit(title_surf, title_rect)
        
        # 描述区域
        desc_y = dialog_y + 90
        desc_width = dialog_width - 60
        
        # 分割描述文本
        words = self.event["description"].split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surf = self.font_main.render(test_line, True, (255, 255, 255))
            if test_surf.get_width() <= desc_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        for i, line in enumerate(lines):
            desc_surf = self.font_main.render(line, True, (255, 255, 255))
            self.screen.blit(desc_surf, (dialog_x + 30, desc_y + i * 35))
        
        # 选项区域
        choice_y = dialog_y + 200 + len(lines) * 35
        
        for i, choice in enumerate(self.event["choices"]):
            choice_height = 50
            choice_y_pos = choice_y + i * (choice_height + 10)
            
            # 选项背景
            choice_rect = pygame.Rect(dialog_x + 30, choice_y_pos, dialog_width - 60, choice_height)
            
            if self.selected_choice == i:
                pygame.draw.rect(self.screen, (255, 200, 100), choice_rect, border_radius=10)
                pygame.draw.rect(self.screen, (255, 215, 0), choice_rect, 2, border_radius=10)
            else:
                pygame.draw.rect(self.screen, (60, 60, 100), choice_rect, border_radius=10)
                pygame.draw.rect(self.screen, (150, 150, 180), choice_rect, 1, border_radius=10)
            
            # 选项文本
            choice_text = choice["text"]
            
            # 添加消耗信息
            cost_text = ""
            for resource, amount in choice.get("cost", {}).items():
                if cost_text:
                    cost_text += ", "
                cost_text += f"{resource}: -{amount}"
            
            if cost_text:
                full_text = f"{choice_text} ({cost_text})"
            else:
                full_text = choice_text
            
            choice_surf = self.font_small.render(full_text, True, (255, 255, 255))
            choice_rect_text = choice_surf.get_rect(center=choice_rect.center)
            self.screen.blit(choice_surf, choice_rect_text)
        
        pygame.display.flip()
    
    def handle_event(self, event):
        """处理事件"""
        if not self.active or not self.event:
            return None
        
        mx, my = pygame.mouse.get_pos()
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        dialog_width = min(600, screen_width - 40)
        dialog_height = min(500, screen_height - 100)
        dialog_x = (screen_width - dialog_width) // 2
        
        if event.type == pygame.MOUSEMOTION:
            # 检查选项悬停
            choice_y = dialog_y = (screen_height - dialog_height) // 2 + 200
            lines = len(self.event["description"].split())
            choice_y += lines * 35
            
            for i, choice in enumerate(self.event["choices"]):
                choice_height = 50
                choice_rect = pygame.Rect(dialog_x + 30, choice_y + i * (choice_height + 10), dialog_width - 60, choice_height)
                if choice_rect.collidepoint(mx, my):
                    self.selected_choice = i
                    return None
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 检查选项点击
            choice_y = dialog_y = (screen_height - dialog_height) // 2 + 200
            lines = len(self.event["description"].split())
            choice_y += lines * 35
            
            for i, choice in enumerate(self.event["choices"]):
                choice_height = 50
                choice_rect = pygame.Rect(dialog_x + 30, choice_y + i * (choice_height + 10), dialog_width - 60, choice_height)
                if choice_rect.collidepoint(mx, my):
                    return i
        
        return None

event_system = EventSystem()

def init_event_system():
    """初始化事件系统"""
    global event_system
    event_system = EventSystem()

def get_event_system():
    """获取事件系统实例"""
    return event_system