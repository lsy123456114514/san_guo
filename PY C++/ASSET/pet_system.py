import pygame
import time
import random
import os
import sys
import math

# 添加父目录到Python路径，确保可以正确导入ASSET模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ASSET.game_data import data, save, get_system_font_name
from ASSET.game_main_menu import Button, COLORS, draw_gradient_background, draw_title, Particle

# 全局变量（延迟初始化）
screen = None
clock = None
FONT_MAIN = None
FONT_SMALL = None

class Pet:
    def __init__(self, name="小老鼠", pet_type="普通"):
        self.name = name
        self.type = pet_type  # 宠物类型
        self.age = 0  # 年龄（天）
        self.hunger = 100  # 饥饿度（0-100）
        self.happiness = 100  # 快乐度（0-100）
        self.growth = 0  # 成长值（0-100）
        self.stage = 1  # 成长阶段（1-3）
        self.level = 1  # 宠物等级
        self.experience = 0  # 经验值
        self.max_experience = 100  # 升级所需经验
        self.attributes = {  # 宠物属性
            "attack": 10,  # 攻击力
            "defense": 5,  # 防御力
            "speed": 8,  # 速度
            "luck": 3  # 幸运值
        }
        self.element = random.choice(["火", "水", "土", "风", "雷"])  # 宠物元素属性
        self.is_equipped = False  # 是否上阵
        self.last_feed_time = time.time()
        self.last_growth_time = time.time()
        self.last_happiness_time = time.time()
        self.last_play_time = 0  # 上次玩耍时间（用于冷却）
        self.play_cooldown = 30  # 玩耍冷却时间（秒）
        self.skills = []  # 宠物技能
        self.skill_points = 0  # 技能点
        self.equipment = {  # 宠物装备
            "collar": None,  # 项圈
            "accessory": None,  # 饰品
            "armor": None  # 护甲
        }
    
    def update(self):
        """更新宠物状态"""
        current_time = time.time()
        
        # 每小时减少饥饿度
        if current_time - self.last_feed_time > 3600:
            self.hunger = max(0, self.hunger - 10)
            self.last_feed_time = current_time
        
        # 每24小时增加年龄和成长值
        if current_time - self.last_growth_time > 86400:
            self.age += 1
            self.growth = min(100, self.growth + 20)
            self.last_growth_time = current_time
            
            # 检查是否升级
            if self.growth >= 100:
                self.stage = min(3, self.stage + 1)
                self.growth = 0
        
        # 每30分钟减少快乐度
        if current_time - self.last_happiness_time > 1800:
            self.happiness = max(0, self.happiness - 5)
            self.last_happiness_time = current_time
    
    def feed(self, food_amount=20):
        """喂食宠物"""
        self.hunger = min(100, self.hunger + food_amount)
        self.last_feed_time = time.time()
    
    def play(self, happiness_amount=25):
        """与宠物玩耍"""
        current_time = time.time()
        if current_time - self.last_play_time >= self.play_cooldown:
            self.happiness = min(100, self.happiness + happiness_amount)
            self.last_happiness_time = time.time()
            self.last_play_time = current_time
            # 玩耍获得经验值
            self.add_experience(5)
            return True
        else:
            return False
    
    def add_experience(self, amount):
        """添加经验值"""
        self.experience += amount
        while self.experience >= self.max_experience:
            self.level_up()
    
    def level_up(self):
        """宠物升级"""
        self.level += 1
        self.experience -= self.max_experience
        self.max_experience = int(self.max_experience * 1.5)
        # 升级时提升属性
        for attr in self.attributes:
            self.attributes[attr] += 2
        # 成长值增加
        self.growth = min(100, self.growth + 10)
        # 升级获得技能点
        self.skill_points += 1
        # 检查是否可以进化
        self.check_evolution()
    
    def can_evolve(self):
        """检查宠物是否可以进化"""
        return self.stage == 3 and self.level >= 30

    def evolve(self):
        """宠物进化"""
        if not self.can_evolve():
            return False

        if not hasattr(self, 'evolution_level'):
            self.evolution_level = 1
        else:
            self.evolution_level += 1

        self.level = 1
        self.max_experience = 100

        for attr in self.attributes:
            self.attributes[attr] += 10

        self.growth = 0

        evolution_suffixes = ["", "·进化", "·超进化", "·究极进化"]
        if not hasattr(self, 'original_name'):
            self.original_name = self.name

        if self.evolution_level < len(evolution_suffixes):
            self.name = f"{self.original_name}{evolution_suffixes[self.evolution_level]}"
        else:
            self.name = f"{self.original_name}·{self.evolution_level}阶进化"

        if self.type == "普通":
            self.type = "稀有"
        elif self.type == "稀有":
            self.type = "史诗"
        elif self.type == "史诗":
            self.type = "传说"

        return True

    def check_evolution(self):
        """检查并执行进化"""
        if self.can_evolve():
            self.evolve()
    
    def get_evolution_name(self):
        """获取进化阶段名称"""
        if not hasattr(self, 'evolution_level'):
            return "普通"
        evolution_names = ["普通", "进化", "超进化", "究极进化"]
        if self.evolution_level < len(evolution_names):
            return evolution_names[self.evolution_level]
        return f"{self.evolution_level}阶进化"
    
    def learn_skill(self, skill_name):
        """学习技能"""
        if self.skill_points > 0:
            # 检查技能是否已学习
            for skill in self.skills:
                if skill['name'] == skill_name:
                    return False
            
            # 技能列表
            skills = {
                "火球术": {"type": "attack", "power": 20, "element": "火", "cooldown": 5},
                "水疗术": {"type": "heal", "power": 15, "element": "水", "cooldown": 8},
                "土墙术": {"type": "defense", "power": 10, "element": "土", "cooldown": 10},
                "风刃术": {"type": "attack", "power": 18, "element": "风", "cooldown": 4},
                "雷击术": {"type": "attack", "power": 25, "element": "雷", "cooldown": 7},
                "速度提升": {"type": "buff", "power": 5, "element": "风", "cooldown": 15},
                "防御强化": {"type": "buff", "power": 8, "element": "土", "cooldown": 12},
                "攻击增幅": {"type": "buff", "power": 10, "element": "火", "cooldown": 10}
            }
            
            if skill_name in skills:
                skill = skills[skill_name]
                self.skills.append({
                    "name": skill_name,
                    "type": skill["type"],
                    "power": skill["power"],
                    "element": skill["element"],
                    "cooldown": skill["cooldown"],
                    "level": 1,
                    "last_used": 0
                })
                self.skill_points -= 1
                return True
        return False
    
    def use_skill(self, skill_name):
        """使用技能"""
        current_time = time.time()
        for skill in self.skills:
            if skill['name'] == skill_name:
                if current_time - skill['last_used'] >= skill['cooldown']:
                    skill['last_used'] = current_time
                    return True
        return False
    
    def upgrade_skill(self, skill_name):
        """升级技能"""
        if self.skill_points > 0:
            for skill in self.skills:
                if skill['name'] == skill_name:
                    skill['level'] += 1
                    skill['power'] += 5
                    self.skill_points -= 1
                    return True
        return False
    
    def equip_item(self, item_type, item):
        """装备物品"""
        if item_type in self.equipment:
            self.equipment[item_type] = item
            # 根据装备类型提升属性
            if item_type == "collar":
                self.attributes["attack"] += 5
            elif item_type == "accessory":
                self.attributes["speed"] += 5
            elif item_type == "armor":
                self.attributes["defense"] += 5
            return True
        return False
    
    def unequip_item(self, item_type):
        """卸下装备"""
        if item_type in self.equipment and self.equipment[item_type]:
            # 恢复属性
            if item_type == "collar":
                self.attributes["attack"] -= 5
            elif item_type == "accessory":
                self.attributes["speed"] -= 5
            elif item_type == "armor":
                self.attributes["defense"] -= 5
            self.equipment[item_type] = None
            return True
        return False
    
    def to_dict(self):
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type,
            "age": self.age,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "growth": self.growth,
            "stage": self.stage,
            "level": self.level,
            "experience": self.experience,
            "max_experience": self.max_experience,
            "attributes": self.attributes,
            "element": self.element,
            "is_equipped": self.is_equipped,
            "last_feed_time": self.last_feed_time,
            "last_growth_time": self.last_growth_time,
            "last_happiness_time": self.last_happiness_time,
            "last_play_time": self.last_play_time,
            "play_cooldown": self.play_cooldown,
            "evolution_level": getattr(self, 'evolution_level', 0),
            "original_name": getattr(self, 'original_name', self.name),
            "skills": self.skills,
            "skill_points": self.skill_points,
            "equipment": self.equipment
        }
    
    @classmethod
    def from_dict(cls, pet_dict):
        """从字典创建宠物"""
        pet = cls(pet_dict.get("name", "小老鼠"), pet_dict.get("type", "普通"))
        pet.age = pet_dict.get("age", 0)
        pet.hunger = pet_dict.get("hunger", 100)
        pet.happiness = pet_dict.get("happiness", 100)
        pet.growth = pet_dict.get("growth", 0)
        pet.stage = pet_dict.get("stage", 1)
        pet.level = pet_dict.get("level", 1)
        pet.experience = pet_dict.get("experience", 0)
        pet.max_experience = pet_dict.get("max_experience", 100)
        pet.attributes = pet_dict.get("attributes", {"attack": 10, "defense": 5, "speed": 8, "luck": 3})
        pet.element = pet_dict.get("element", random.choice(["火", "水", "土", "风", "雷"]))
        pet.is_equipped = pet_dict.get("is_equipped", False)
        pet.last_feed_time = pet_dict.get("last_feed_time", time.time())
        pet.last_growth_time = pet_dict.get("last_growth_time", time.time())
        pet.last_happiness_time = pet_dict.get("last_happiness_time", time.time())
        pet.last_play_time = pet_dict.get("last_play_time", 0)
        pet.play_cooldown = pet_dict.get("play_cooldown", 30)
        # 进化相关属性
        pet.evolution_level = pet_dict.get("evolution_level", 0)
        pet.original_name = pet_dict.get("original_name", pet.name)
        # 技能和装备相关属性
        pet.skills = pet_dict.get("skills", [])
        pet.skill_points = pet_dict.get("skill_points", 0)
        pet.equipment = pet_dict.get("equipment", {"collar": None, "accessory": None, "armor": None})
        return pet

def init_fonts():
    """初始化字体"""
    global FONT_MAIN, FONT_SMALL
    font_name = get_system_font_name()
    try:
        if font_name:
            FONT_MAIN = pygame.font.SysFont(font_name, 40)
            FONT_SMALL = pygame.font.SysFont(font_name, 28)
        else:
            FONT_MAIN = pygame.font.Font(None, 40)
            FONT_SMALL = pygame.font.Font(None, 28)
    except Exception:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 28)
    
    # 确保game_main_menu.py中的字体也被初始化
    try:
        import ASSET.game_main_menu
        if ASSET.game_main_menu.FONT_BIG is None:
            if font_name:
                ASSET.game_main_menu.FONT_BIG = pygame.font.SysFont(font_name, 60)
            else:
                ASSET.game_main_menu.FONT_BIG = pygame.font.Font(None, 60)
    except Exception:
        pass

def draw_pet_status(surface, pet, x, y, width, height):
    """绘制宠物状态面板"""
    # 面板背景
    panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (30, 30, 55, 180), (0, 0, width, height), border_radius=10)
    surface.blit(panel_surf, (x, y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], (x, y, width, height), 2, border_radius=10)
    
    # 宠物信息 - 分两行显示避免重叠
    name_text = FONT_MAIN.render(f"{pet.name} ({pet.get_stage_name()})", True, COLORS["accent_gold"])
    evolution_text = FONT_SMALL.render(f"进化阶段: {pet.get_evolution_name()}", True, COLORS["accent_gold"])
    type_text = FONT_SMALL.render(f"类型: {pet.type}", True, COLORS["text_white"])
    element_text = FONT_SMALL.render(f"元素: {pet.element}", True, COLORS["text_white"])
    age_text = FONT_SMALL.render(f"年龄: {pet.age} 天", True, COLORS["text_white"])
    level_text = FONT_SMALL.render(f"等级: {pet.level}", True, COLORS["text_white"])
    
    surface.blit(name_text, (x + 20, y + 20))
    surface.blit(evolution_text, (x + 20, y + 50))
    # 第一行：类型和元素
    surface.blit(type_text, (x + 20, y + 80))
    surface.blit(element_text, (x + 200, y + 80))
    # 第二行：年龄和等级
    surface.blit(age_text, (x + 20, y + 110))
    surface.blit(level_text, (x + 200, y + 110))
    
    # 进化信息
    if pet.can_evolve():
        evolve_text = FONT_SMALL.render("可以进化！", True, COLORS["accent_green"])
        surface.blit(evolve_text, (x + 350, y + 110))
    elif pet.stage == 3:
        evolve_needed = 30 - pet.level
        if evolve_needed > 0:
            evolve_text = FONT_SMALL.render(f"还需 {evolve_needed} 级可进化", True, COLORS["text_white"])
            surface.blit(evolve_text, (x + 350, y + 110))
    
    # 经验值条
    exp_percent = pet.experience / pet.max_experience
    exp_width = width - 40
    pygame.draw.rect(surface, (80, 80, 100), (x + 20, y + 140, exp_width, 20), border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_purple"], (x + 20, y + 140, exp_width * exp_percent, 20), border_radius=10)
    exp_text = FONT_SMALL.render(f"经验值: {pet.experience}/{pet.max_experience}", True, COLORS["text_white"])
    surface.blit(exp_text, (x + 20, y + 170))
    
    # 饥饿度条
    hunger_percent = pet.hunger / 100
    pygame.draw.rect(surface, (80, 80, 100), (x + 20, y + 210, exp_width, 20), border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_green"], (x + 20, y + 210, exp_width * hunger_percent, 20), border_radius=10)
    hunger_text = FONT_SMALL.render(f"饥饿度: {pet.hunger}%", True, COLORS["text_white"])
    surface.blit(hunger_text, (x + 20, y + 240))
    
    # 快乐度条
    happiness_percent = pet.happiness / 100
    pygame.draw.rect(surface, (80, 80, 100), (x + 20, y + 280, exp_width, 20), border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_blue"], (x + 20, y + 280, exp_width * happiness_percent, 20), border_radius=10)
    happiness_text = FONT_SMALL.render(f"快乐度: {pet.happiness}%", True, COLORS["text_white"])
    surface.blit(happiness_text, (x + 20, y + 310))
    
    # 成长值条
    growth_percent = pet.growth / 100
    pygame.draw.rect(surface, (80, 80, 100), (x + 20, y + 350, exp_width, 20), border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_gold"], (x + 20, y + 350, exp_width * growth_percent, 20), border_radius=10)
    growth_text = FONT_SMALL.render(f"成长值: {pet.growth}%", True, COLORS["text_white"])
    surface.blit(growth_text, (x + 20, y + 380))
    
    # 属性显示
    attr_y = y + 420
    attr_names = {"attack": "攻击力", "defense": "防御力", "speed": "速度", "luck": "幸运值"}
    for i, (attr, value) in enumerate(pet.attributes.items()):
        attr_text = FONT_SMALL.render(f"{attr_names.get(attr, attr)}: {value}", True, COLORS["text_white"])
        surface.blit(attr_text, (x + 20 + i * 100, attr_y))
    
    # 技能点显示
    skill_points_y = attr_y + 40
    skill_points_text = FONT_SMALL.render(f"技能点: {pet.skill_points}", True, COLORS["accent_gold"])

    surface.blit(skill_points_text, (x + 20, skill_points_y))
    
    # 技能显示
    skills_y = skill_points_y + 40
    skills_title = FONT_SMALL.render("技能:", True, COLORS["accent_gold"])
    surface.blit(skills_title, (x + 20, skills_y))
    
    for i, skill in enumerate(pet.skills[:3]):  # 只显示前3个技能
        skill_text = FONT_SMALL.render(f"{skill['name']} (Lv.{skill['level']})", True, COLORS["text_white"])
        surface.blit(skill_text, (x + 20, skills_y + 30 + i * 25))

    # 装备显示
    equipment_y = skills_y + 150
    equipment_title = FONT_SMALL.render("装备:", True, COLORS["accent_gold"])
    surface.blit(equipment_title, (x + 20, equipment_y))
    
    equipment_types = {"collar": "项圈", "accessory": "饰品", "armor": "护甲"}
    for i, (eq_type, eq_name) in enumerate(equipment_types.items()):
        equipment = pet.equipment.get(eq_type, None)
        if equipment:
            eq_text = FONT_SMALL.render(f"{eq_name}: {equipment}", True, COLORS["text_white"])
        else:
            eq_text = FONT_SMALL.render(f"{eq_name}: 未装备", True, COLORS["text_gray"])
        surface.blit(eq_text, (x + 20, equipment_y + 30 + i * 25))

def draw_pet_visual(surface, pet, x, y, size):
    """绘制宠物视觉效果"""
    # 根据成长阶段绘制不同大小的宠物
    pet_size = size * (0.8 + pet.stage * 0.2)
    
    # 绘制宠物主体
    pygame.draw.circle(surface, (128, 128, 128), (x, y), int(pet_size * 0.4))
    
    # 绘制耳朵
    pygame.draw.circle(surface, (128, 128, 128), (x - int(pet_size * 0.2), y - int(pet_size * 0.2)), int(pet_size * 0.15))
    pygame.draw.circle(surface, (128, 128, 128), (x + int(pet_size * 0.2), y - int(pet_size * 0.2)), int(pet_size * 0.15))
    
    # 绘制眼睛
    pygame.draw.circle(surface, (255, 255, 255), (x - int(pet_size * 0.15), y), int(pet_size * 0.08))
    pygame.draw.circle(surface, (255, 255, 255), (x + int(pet_size * 0.15), y), int(pet_size * 0.08))
    pygame.draw.circle(surface, (0, 0, 0), (x - int(pet_size * 0.15), y), int(pet_size * 0.04))
    pygame.draw.circle(surface, (0, 0, 0), (x + int(pet_size * 0.15), y), int(pet_size * 0.04))
    
    # 绘制鼻子
    pygame.draw.circle(surface, (255, 0, 0), (x, y + int(pet_size * 0.1)), int(pet_size * 0.05))
    
    # 绘制胡须
    for i in range(3):
        angle = -0.5 + i * 0.25
        length = pet_size * 0.2
        pygame.draw.line(surface, (0, 0, 0), (x, y + int(pet_size * 0.1)), 
                       (x + int(length * math.cos(angle)), y + int(pet_size * 0.1) + int(length * math.sin(angle))), 2)
        pygame.draw.line(surface, (0, 0, 0), (x, y + int(pet_size * 0.1)), 
                       (x - int(length * math.cos(angle)), y + int(pet_size * 0.1) + int(length * math.sin(angle))), 2)

def play_with_pet():
    """带宠物玩小游戏"""
    # 这里可以实现一个简单的小游戏
    # 暂时返回一些食物作为奖励
    food_reward = random.randint(1, 3)
    return food_reward

def pet_menu():
    """宠物菜单"""
    global screen, clock, FONT_MAIN, FONT_SMALL
    
    # 确保字体初始化
    if FONT_MAIN is None or FONT_SMALL is None:
        init_fonts()
    
    # 保存原始屏幕
    original_screen = screen
    
    # 设置宠物系统专用分辨率 1000x1000
    PET_SCREEN_WIDTH = 1800
    PET_SCREEN_HEIGHT = 1000
    
    # 创建宠物系统专用屏幕
    pet_screen = pygame.display.set_mode((PET_SCREEN_WIDTH, PET_SCREEN_HEIGHT))
    screen = pet_screen
    
    # 更新game_main_menu模块的屏幕引用
    import ASSET.game_main_menu
    ASSET.game_main_menu.screen = pet_screen
    
    screen_width = PET_SCREEN_WIDTH
    screen_height = PET_SCREEN_HEIGHT
    
    # 确保宠物数据存在
    if 'pet' not in data:
        data['pet'] = Pet().to_dict()
        save()
    
    # 确保宠物仓库存在
    if 'pet_warehouse' not in data:
        data['pet_warehouse'] = []
        save()
    
    # 确保各种宠物蛋存在
    pet_egg_types = ["pet_eggs", "rare_pet_eggs", "epic_pet_eggs", "legendary_pet_eggs"]
    for egg_type in pet_egg_types:
        if egg_type not in data['resources']:
            data['resources'][egg_type] = 0
            save()
    
    # 确保孵化队列存在
    if 'hatch_queue' not in data:
        data['hatch_queue'] = []
        save()
    
    # 确保宠物食物存在
    if 'pet_food' not in data['resources']:
        data['resources']['pet_food'] = 0
        save()
    
    pet = Pet.from_dict(data['pet'])
    
    # 装饰粒子
    particles = []
    
    running = True
    while running:
        # 获取当前屏幕大小
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # 按钮设置
        button_width = min(150, screen_width * 0.25)
        button_height = min(50, screen_height * 0.07)
        button_spacing = min(15, screen_height * 0.025)
        
        # 更新宠物状态
        pet.update()
        
        # 检查孵化队列
        current_time = time.time()
        completed_hatches = []
        for i, hatch_item in enumerate(data['hatch_queue']):
            if current_time - hatch_item['hatch_start_time'] >= hatch_item['hatch_time']:
                # 孵化完成，添加到宠物仓库
                data['pet_warehouse'].append(hatch_item['pet'])
                completed_hatches.append(i)
        
        # 移除已完成的孵化
        for i in reversed(completed_hatches):
            data['hatch_queue'].pop(i)
        
        if completed_hatches:
            save()
        
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 装饰粒子
        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))
        
        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)
        
        # 标题
        draw_title(screen, "宠物系统", screen_height * 0.12, screen_width)
        
        # 绘制宠物视觉效果
        pet_x = screen_width // 4
        pet_y = screen_height // 2
        draw_pet_visual(screen, pet, pet_x, pet_y, 150)
        
        # 绘制宠物状态面板
        status_x = screen_width // 2
        status_y = screen_height // 2 - 200
        draw_pet_status(screen, pet, status_x, status_y, 400, 420)
        
        # 绘制资源数量
        resources_y = screen_height * 0.75
        food_text = FONT_SMALL.render(f"宠物食物: {data['resources'].get('pet_food', 0)}", True, COLORS["text_white"])
        eggs_text = FONT_SMALL.render(f"宠物蛋: {data['resources'].get('pet_eggs', 0)}", True, COLORS["text_white"])
        rare_eggs_text = FONT_SMALL.render(f"稀有宠物蛋: {data['resources'].get('rare_pet_eggs', 0)}", True, COLORS["text_white"])
        epic_eggs_text = FONT_SMALL.render(f"史诗宠物蛋: {data['resources'].get('epic_pet_eggs', 0)}", True, COLORS["text_white"])
        legendary_eggs_text = FONT_SMALL.render(f"传说宠物蛋: {data['resources'].get('legendary_pet_eggs', 0)}", True, COLORS["text_white"])
        
        screen.blit(food_text, (screen_width // 2 - food_text.get_width() // 2, resources_y))
        screen.blit(eggs_text, (screen_width // 2 - eggs_text.get_width() // 2, resources_y + 30))
        screen.blit(rare_eggs_text, (screen_width // 4 - rare_eggs_text.get_width() // 2, resources_y + 60))
        screen.blit(epic_eggs_text, (screen_width // 2 - epic_eggs_text.get_width() // 2, resources_y + 60))
        screen.blit(legendary_eggs_text, (screen_width * 3 // 4 - legendary_eggs_text.get_width() // 2, resources_y + 60))
        
        # 绘制孵化队列
        if data['hatch_queue']:
            hatch_y = resources_y + 90
            hatch_title = FONT_SMALL.render("孵化中:", True, COLORS["accent_gold"])
            screen.blit(hatch_title, (screen_width // 2 - hatch_title.get_width() // 2, hatch_y))
            
            current_time = time.time()
            for i, hatch_item in enumerate(data['hatch_queue']):
                pet_info = hatch_item['pet']
                elapsed_time = current_time - hatch_item['hatch_start_time']
                progress = min(1.0, elapsed_time / hatch_item['hatch_time'])
                
                # 计算剩余时间
                remaining_time = max(0, hatch_item['hatch_time'] - elapsed_time)
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                time_text = f"剩余: {minutes}分{seconds}秒"
                
                # 绘制孵化进度条
                hatch_x = screen_width // 2 - 200
                hatch_item_y = hatch_y + 30 + i * 50
                progress_width = 400
                
                pygame.draw.rect(screen, (80, 80, 100), (hatch_x, hatch_item_y, progress_width, 20), border_radius=10)
                pygame.draw.rect(screen, COLORS["accent_green"], (hatch_x, hatch_item_y, progress_width * progress, 20), border_radius=10)
                
                # 绘制宠物信息
                pet_name = pet_info['name']
                pet_type = pet_info['type']
                pet_text = FONT_SMALL.render(f"{pet_name} ({pet_type})", True, COLORS["text_white"])
                time_text_surf = FONT_SMALL.render(time_text, True, COLORS["text_white"])
                
                screen.blit(pet_text, (hatch_x, hatch_item_y - 25))
                screen.blit(time_text_surf, (hatch_x + progress_width - time_text_surf.get_width(), hatch_item_y - 25))
        
        # 创建按钮
        button_y = screen_height * 0.9
        
        feed_button = Button("喂食", screen_width // 2 - 5 * button_width // 2 - 4 * button_spacing // 2, button_y, button_width, button_height, FONT_SMALL)
        play_button = Button("玩耍", screen_width // 2 - 3 * button_width // 2 - 2 * button_spacing // 2, button_y, button_width, button_height, FONT_SMALL)
        hatch_button = Button("孵化", screen_width // 2 - button_width // 2, button_y, button_width, button_height, FONT_SMALL)
        warehouse_button = Button("宠物仓库", screen_width // 2 + button_width // 2 + button_spacing, button_y, button_width, button_height, FONT_SMALL)
        evolve_button = Button("进化", screen_width // 2 + 3 * button_width // 2 + 2 * button_spacing, button_y, button_width, button_height, FONT_SMALL, normal_color=COLORS["accent_purple"])
        back_button = Button("返回", screen_width // 2 - button_width // 2, button_y + button_height + button_spacing, button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
        
        # 处理鼠标
        mouse_pos = pygame.mouse.get_pos()
        feed_button.check_hover(mouse_pos)
        play_button.check_hover(mouse_pos)
        hatch_button.check_hover(mouse_pos)
        warehouse_button.check_hover(mouse_pos)
        evolve_button.check_hover(mouse_pos)
        back_button.check_hover(mouse_pos)
        
        # 绘制按钮
        feed_button.draw(screen)
        play_button.draw(screen)
        hatch_button.draw(screen)
        warehouse_button.draw(screen)
        evolve_button.draw(screen)
        back_button.draw(screen)
        
        pygame.display.flip()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if feed_button.rect.collidepoint(event.pos):
                    # 喂食宠物
                    if data['resources'].get('pet_food', 0) > 0:
                        pet.feed()
                        data['resources']['pet_food'] -= 1
                        data['pet'] = pet.to_dict()
                        save()
                    elif data['resources'].get('金元宝', 0) >= 10:
                        # 用金元宝购买食物并喂食
                        pet.feed()
                        data['resources']['金元宝'] -= 10
                        data['pet'] = pet.to_dict()
                        save()
                elif play_button.rect.collidepoint(event.pos):
                    # 带宠物玩小游戏
                    if pet.play():
                        food_reward = play_with_pet()
                        data['resources']['pet_food'] = data['resources'].get('pet_food', 0) + food_reward
                        data['pet'] = pet.to_dict()
                        save()
                elif hatch_button.rect.collidepoint(event.pos):
                    # 打开孵化选择界面
                    selected_egg = hatch_selection_menu()
                    
                    if selected_egg:
                        egg_key, pet_type, hatch_time = selected_egg
                        
                        # 减少宠物蛋数量
                        data['resources'][egg_key] = data['resources'].get(egg_key, 0) - 1
                        
                        # 随机生成宠物名称
                        pet_names = ["小老鼠", "小猫", "小狗", "小兔子", "小鸟"]
                        pet_name = random.choice(pet_names)
                        # 创建新宠物
                        new_pet = Pet(pet_name, pet_type)
                        # 根据宠物类型设置初始属性
                        if pet_type == "稀有":
                            for attr in new_pet.attributes:
                                new_pet.attributes[attr] += 5
                        elif pet_type == "史诗":
                            for attr in new_pet.attributes:
                                new_pet.attributes[attr] += 10
                        elif pet_type == "传说":
                            for attr in new_pet.attributes:
                                new_pet.attributes[attr] += 15
                        # 添加到孵化队列
                        hatch_item = {
                            "pet": new_pet.to_dict(),
                            "hatch_start_time": time.time(),
                            "hatch_time": hatch_time
                        }
                        data['hatch_queue'].append(hatch_item)
                        save()
                elif warehouse_button.rect.collidepoint(event.pos):
                    # 打开宠物仓库
                    pet_warehouse_menu()
                elif evolve_button.rect.collidepoint(event.pos):
                    # 进化宠物
                    if pet.can_evolve():
                        if pet.evolve():
                            data['pet'] = pet.to_dict()
                            save()
                    else:
                        # 显示进化条件不满足的提示
                        pass
                elif back_button.rect.collidepoint(event.pos):
                    # 保存宠物数据
                    data['pet'] = pet.to_dict()
                    save()
                    running = False
        
        clock.tick(60)
    
    # 恢复原始屏幕
    screen = original_screen
    import ASSET.game_main_menu
    ASSET.game_main_menu.screen = original_screen
    pygame.display.set_mode(original_screen.get_size())

def hatch_selection_menu():
    """孵化选择界面 - 让用户选择要孵化哪个宠物蛋"""
    global screen, clock, FONT_MAIN, FONT_SMALL
    
    # 装饰粒子
    particles = []
    
    # 定义可用的宠物蛋
    egg_types = [
        ("pet_eggs", "普通宠物蛋", "普通", 300, COLORS["text_white"]),
        ("rare_pet_eggs", "稀有宠物蛋", "稀有", 600, COLORS["accent_blue"]),
        ("epic_pet_eggs", "史诗宠物蛋", "史诗", 1800, COLORS["accent_purple"]),
        ("legendary_pet_eggs", "传说宠物蛋", "传说", 3600, COLORS["accent_gold"])
    ]
    
    running = True
    selected_egg = None
    
    while running:
        # 获取当前屏幕大小
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # 按钮设置
        button_width = min(250, screen_width * 0.4)
        button_height = min(60, screen_height * 0.08)
        button_spacing = min(20, screen_height * 0.03)
        
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 装饰粒子
        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))
        
        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)
        
        # 标题
        draw_title(screen, "选择要孵化的宠物蛋", screen_height * 0.12, screen_width)
        
        # 绘制可用的宠物蛋
        egg_buttons = []
        start_y = screen_height * 0.25
        
        for i, (egg_key, egg_name, pet_type, hatch_time, color) in enumerate(egg_types):
            egg_count = data['resources'].get(egg_key, 0)
            
            # 计算按钮位置
            btn_x = screen_width // 2 - button_width // 2
            btn_y = start_y + i * (button_height + button_spacing)
            
            # 创建按钮
            if egg_count > 0:
                btn_text = f"{egg_name} (拥有: {egg_count})"
                btn_color = color
            else:
                btn_text = f"{egg_name} (未拥有)"
                btn_color = (100, 100, 100)
            
            egg_button = Button(btn_text, btn_x, btn_y, button_width, button_height, FONT_SMALL, 
                               normal_color=btn_color, hover_color=btn_color)
            egg_buttons.append((egg_button, egg_key, pet_type, hatch_time, egg_count > 0))
            
            # 检查悬停和绘制
            mouse_pos = pygame.mouse.get_pos()
            egg_button.check_hover(mouse_pos)
            egg_button.draw(screen)
        
        # 返回按钮
        back_button = Button("返回", screen_width // 2 - button_width // 2, 
                            screen_height * 0.85, button_width, button_height, 
                            FONT_SMALL, normal_color=(100, 100, 150))
        back_button.check_hover(pygame.mouse.get_pos())
        back_button.draw(screen)
        
        pygame.display.flip()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                return None
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                # 处理宠物蛋按钮点击
                for egg_button, egg_key, pet_type, hatch_time, has_egg in egg_buttons:
                    if egg_button.rect.collidepoint(mouse_pos):
                        if has_egg:
                            selected_egg = (egg_key, pet_type, hatch_time)
                            running = False
                        break
                
                # 处理返回按钮
                if back_button.rect.collidepoint(mouse_pos):
                    return None
        
        clock.tick(60)
    
    return selected_egg

def pet_warehouse_menu():
    """宠物仓库菜单"""
    global screen, clock, FONT_MAIN, FONT_SMALL
    
    # 确保宠物仓库存在
    if 'pet_warehouse' not in data:
        data['pet_warehouse'] = []
        save()
    
    # 装饰粒子
    particles = []
    
    running = True
    while running:
        # 获取当前屏幕大小
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # 按钮设置
        button_width = min(200, screen_width * 0.3)
        button_height = min(50, screen_height * 0.07)
        button_spacing = min(15, screen_height * 0.025)
        
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 装饰粒子
        if random.random() < 0.1:
            particles.append(Particle(
                random.randint(0, screen_width),
                random.randint(0, screen_height),
                COLORS["accent_gold"], 0.5, 2, 100
            ))
        
        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)
        
        # 标题
        draw_title(screen, "宠物仓库", screen_height * 0.12, screen_width)
        
        # 绘制宠物列表
        warehouse_y = screen_height * 0.2
        pet_buttons = []
        
        for i, pet_dict in enumerate(data['pet_warehouse']):
            pet = Pet.from_dict(pet_dict)
            pet_x = screen_width // 2 - 300
            pet_y = warehouse_y + i * 80
            
            # 绘制宠物卡片
            card_rect = pygame.Rect(pet_x, pet_y, 600, 70)
            pygame.draw.rect(screen, (30, 30, 55, 180), card_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["accent_gold"], card_rect, 2, border_radius=10)
            
            # 宠物信息
            name_text = FONT_MAIN.render(f"{pet.name} ({pet.type})", True, COLORS["accent_gold"])
            level_text = FONT_SMALL.render(f"等级: {pet.level}", True, COLORS["text_white"])
            status_text = FONT_SMALL.render(f"状态: {'已上阵' if pet.is_equipped else '未上阵'}", True, COLORS["text_white"])
            
            screen.blit(name_text, (pet_x + 20, pet_y + 10))
            screen.blit(level_text, (pet_x + 20, pet_y + 40))
            screen.blit(status_text, (pet_x + 150, pet_y + 40))
            
            # 上阵/下阵按钮
            equip_text = "下阵" if pet.is_equipped else "上阵"
            equip_button = Button(equip_text, pet_x + 450, pet_y + 10, 120, 50, FONT_SMALL)
            pet_buttons.append((equip_button, i))
            equip_button.check_hover(pygame.mouse.get_pos())
            equip_button.draw(screen)
        
        # 空仓库提示
        if not data['pet_warehouse']:
            empty_text = FONT_MAIN.render("宠物仓库为空，快去孵化宠物吧！", True, COLORS["text_white"])
            screen.blit(empty_text, (screen_width // 2 - empty_text.get_width() // 2, screen_height // 2))
        
        # 返回按钮
        back_button = Button("返回", screen_width // 2 - button_width // 2, screen_height * 0.9, button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
        back_button.check_hover(pygame.mouse.get_pos())
        back_button.draw(screen)
        
        pygame.display.flip()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 处理宠物按钮点击
                for equip_button, pet_index in pet_buttons:
                    if equip_button.rect.collidepoint(event.pos):
                        # 切换宠物上阵状态
                        pet_dict = data['pet_warehouse'][pet_index]
                        pet_dict['is_equipped'] = not pet_dict['is_equipped']
                        save()
                        break
                
                # 处理返回按钮
                if back_button.rect.collidepoint(event.pos):
                    running = False
        
        clock.tick(60)

def main():
    """宠物系统主函数"""
    global screen, clock
    
    # 确保pygame初始化
    if not pygame.get_init():
        pygame.init()
    
    # 确保屏幕和时钟初始化
    if screen is None:
        # 如果屏幕未初始化，创建一个默认屏幕
        screen = pygame.display.set_mode((800, 600))
    if clock is None:
        clock = pygame.time.Clock()
    
    # 初始化字体
    init_fonts()
    
    # 运行宠物菜单
    pet_menu()

# 导入必要的模块
import math
from ASSET.game_main_menu import Particle

if __name__ == '__main__':
    main()
