"""宠物竞技场 - 宠物对战玩法"""

import pygame
import time
import random
import os
import sys
import math

# 添加父目录到Python路径，确保可以正确导入ASSET模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
from ASSET.game_main_menu import Button, COLORS, draw_gradient_background, draw_title, Particle
from ASSET.pet_system import Pet

# 全局变量（延迟初始化）
screen = None
clock = None
FONT_MAIN = None
FONT_SMALL = None

class BattlePet:
    """战斗中的宠物"""
    def __init__(self, pet):
        self.pet = pet
        self.max_health = 100 + pet.attributes['defense'] * 5
        self.current_health = self.max_health
        self.energy = 100
        self.status = []  # 状态效果
        self.last_turn_time = time.time()
    
    def take_damage(self, damage):
        """受到伤害"""
        damage = max(1, damage - self.pet.attributes['defense'])
        self.current_health = max(0, self.current_health - damage)
        return damage
    
    def heal(self, amount):
        """恢复生命值"""
        self.current_health = min(self.max_health, self.current_health + amount)
        return amount
    
    def use_skill(self, skill):
        """使用技能"""
        if self.energy >= 20:
            self.energy -= 20
            return True
        return False
    
    def is_defeated(self):
        """是否被击败"""
        return self.current_health <= 0
    
    def update(self):
        """更新状态"""
        # 恢复能量
        self.energy = min(100, self.energy + 5)
        # 处理状态效果
        current_time = time.time()
        if current_time - self.last_turn_time > 1:
            for status in self.status:
                if status['type'] == 'poison':
                    self.take_damage(5)
                elif status['type'] == 'bleed':
                    self.take_damage(3)
                status['duration'] -= 1
            self.status[:] = [status for status in self.status if status['duration'] > 0]

            self.last_turn_time = current_time

def draw_battle_scene(surface, player_pet, enemy_pet, battle_log):
    """绘制战斗场景"""
    screen_width = surface.get_width()
    screen_height = surface.get_height()
    
    # 绘制玩家宠物
    player_x = screen_width // 4
    player_y = screen_height * 3 // 4
    draw_pet_visual(surface, player_pet.pet, player_x, player_y, 120)
    
    # 绘制玩家宠物状态栏
    player_health_bar = pygame.Rect(player_x - 100, player_y + 70, 200, 20)
    pygame.draw.rect(surface, (80, 80, 100), player_health_bar, border_radius=10)
    health_percent = player_pet.current_health / player_pet.max_health
    pygame.draw.rect(surface, COLORS["accent_green"], (player_x - 100, player_y + 70, 200 * health_percent, 20), border_radius=10)
    
    player_energy_bar = pygame.Rect(player_x - 100, player_y + 100, 200, 10)
    pygame.draw.rect(surface, (80, 80, 100), player_energy_bar, border_radius=5)
    energy_percent = player_pet.energy / 100
    pygame.draw.rect(surface, COLORS["accent_blue"], (player_x - 100, player_y + 100, 200 * energy_percent, 10), border_radius=5)
    
    player_name = FONT_MAIN.render(player_pet.pet.name, True, COLORS["text_white"])
    surface.blit(player_name, (player_x - player_name.get_width() // 2, player_y - 80))
    
    # 绘制敌方宠物
    enemy_x = screen_width * 3 // 4
    enemy_y = screen_height // 4
    draw_pet_visual(surface, enemy_pet.pet, enemy_x, enemy_y, 120)
    
    # 绘制敌方宠物状态栏
    enemy_health_bar = pygame.Rect(enemy_x - 100, enemy_y + 70, 200, 20)
    pygame.draw.rect(surface, (80, 80, 100), enemy_health_bar, border_radius=10)
    health_percent = enemy_pet.current_health / enemy_pet.max_health
    pygame.draw.rect(surface, COLORS["accent_red"], (enemy_x - 100, enemy_y + 70, 200 * health_percent, 20), border_radius=10)
    
    enemy_energy_bar = pygame.Rect(enemy_x - 100, enemy_y + 100, 200, 10)
    pygame.draw.rect(surface, (80, 80, 100), enemy_energy_bar, border_radius=5)
    energy_percent = enemy_pet.energy / 100
    pygame.draw.rect(surface, COLORS["accent_blue"], (enemy_x - 100, enemy_y + 100, 200 * energy_percent, 10), border_radius=5)
    
    enemy_name = FONT_MAIN.render(enemy_pet.pet.name, True, COLORS["text_white"])
    surface.blit(enemy_name, (enemy_x - enemy_name.get_width() // 2, enemy_y - 80))
    
    # 绘制战斗日志
    log_y = screen_height // 2 - 100
    log_width = screen_width - 200
    log_height = 150
    
    pygame.draw.rect(surface, (30, 30, 55, 180), (100, log_y, log_width, log_height), border_radius=10)
    pygame.draw.rect(surface, COLORS["accent_gold"], (100, log_y, log_width, log_height), 2, border_radius=10)
    
    for i, log in enumerate(battle_log[-5:]):  # 只显示最近5条日志
        log_text = FONT_SMALL.render(log, True, COLORS["text_white"])
        surface.blit(log_text, (120, log_y + 20 + i * 25))

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

def create_enemy_pet(level):
    """创建敌方宠物"""
    pet_names = ["小老鼠", "小猫", "小狗", "小兔子", "小鸟"]
    pet_types = ["普通", "稀有", "史诗"]
    
    name = random.choice(pet_names)
    pet_type = random.choice(pet_types)
    
    pet = Pet(name, pet_type)
    pet.level = level
    pet.experience = 0
    pet.max_experience = 100
    
    # 根据等级设置属性
    for attr in pet.attributes:
        pet.attributes[attr] = 10 + level * 2
    
    # 随机学习技能
    skills = ["火球术", "水疗术", "土墙术", "风刃术", "雷击术"]
    for _ in range(min(level // 10, 3)):
        skill = random.choice(skills)
        pet.learn_skill(skill)
    
    return pet

def battle(player_pet, enemy_pet):
    """宠物对战"""
    global screen, clock, FONT_MAIN, FONT_SMALL
    
    player_battle_pet = BattlePet(player_pet)
    enemy_battle_pet = BattlePet(enemy_pet)
    
    battle_log = []
    battle_log.append(f"战斗开始！{player_pet.name} vs {enemy_pet.name}")
    
    # 装饰粒子
    particles = []
    
    running = True
    battle_phase = "player_turn"  # player_turn, enemy_turn, battle_end
    player_skill = None
    
    while running:
        # 获取当前屏幕大小
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # 按钮设置
        button_width = min(150, screen_width * 0.25)
        button_height = min(50, screen_height * 0.07)
        button_spacing = min(15, screen_height * 0.025)
        
        # 渐变背景
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
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
        
        # 绘制战斗场景
        draw_battle_scene(screen, player_battle_pet, enemy_battle_pet, battle_log)
        
        # 绘制技能按钮
        if battle_phase == "player_turn":
            skill_buttons = []
            start_x = screen_width // 2 - (len(player_pet.skills) * (button_width + button_spacing)) // 2
            start_y = screen_height * 0.9
            
            for i, skill in enumerate(player_pet.skills):
                skill_button = Button(skill['name'], start_x + i * (button_width + button_spacing), start_y, button_width, button_height, FONT_SMALL)
                skill_buttons.append((skill_button, skill))
                skill_button.check_hover(pygame.mouse.get_pos())
                skill_button.draw(screen)
            
            # 普通攻击按钮
            attack_button = Button("普通攻击", screen_width // 2 - button_width // 2, start_y + button_height + button_spacing, button_width, button_height, FONT_SMALL)
            attack_button.check_hover(pygame.mouse.get_pos())
            attack_button.draw(screen)
        
        # 绘制战斗结果
        if battle_phase == "battle_end":
            result_y = screen_height // 2
            if player_battle_pet.is_defeated():
                result_text = FONT_MAIN.render("战斗失败！", True, COLORS["accent_red"])
            else:
                result_text = FONT_MAIN.render("战斗胜利！", True, COLORS["accent_green"])
            surface.blit(result_text, (screen_width // 2 - result_text.get_width() // 2, result_y))
            
            # 退出按钮
            exit_button = Button("退出", screen_width // 2 - button_width // 2, result_y + 50, button_width, button_height, FONT_SMALL)
            exit_button.check_hover(pygame.mouse.get_pos())
            exit_button.draw(screen)
        
        pygame.display.flip()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if battle_phase == "player_turn":
                    # 处理技能按钮点击
                    for skill_button, skill in skill_buttons:
                        if skill_button.rect.collidepoint(event.pos):
                            if player_battle_pet.use_skill(skill):
                                # 使用技能
                                if skill['type'] == 'attack':
                                    damage = skill['power'] + player_pet.attributes['attack']
                                    enemy_battle_pet.take_damage(damage)
                                    battle_log.append(f"{player_pet.name}使用了{skill['name']}，造成{damage}点伤害")
                                elif skill['type'] == 'heal':
                                    heal_amount = skill['power']
                                    player_battle_pet.heal(heal_amount)
                                    battle_log.append(f"{player_pet.name}使用了{skill['name']}，恢复了{heal_amount}点生命值")
                                elif skill['type'] == 'defense':
                                    player_battle_pet.status.append({'type': 'shield', 'duration': 3, 'power': skill['power']})
                                    battle_log.append(f"{player_pet.name}使用了{skill['name']}，获得了防御加成")
                                elif skill['type'] == 'buff':
                                    player_battle_pet.status.append({'type': 'buff', 'duration': 5, 'power': skill['power']})
                                    battle_log.append(f"{player_pet.name}使用了{skill['name']}，获得了属性加成")
                                
                                # 切换到敌方回合
                                battle_phase = "enemy_turn"
                                break
                    
                    # 处理普通攻击按钮
                    if attack_button.rect.collidepoint(event.pos):
                        # 普通攻击
                        damage = player_pet.attributes['attack']
                        enemy_battle_pet.take_damage(damage)
                        battle_log.append(f"{player_pet.name}使用了普通攻击，造成{damage}点伤害")
                        
                        # 切换到敌方回合
                        battle_phase = "enemy_turn"
                
                if battle_phase == "battle_end":
                    if exit_button.rect.collidepoint(event.pos):
                        return
        
        # 敌方回合
        if battle_phase == "enemy_turn":
            # 等待1秒后执行敌方行动
            pygame.time.wait(1000)
            
            # 敌方行动
            if enemy_battle_pet.energy >= 20 and enemy_pet.skills:
                # 使用技能
                skill = random.choice(enemy_pet.skills)
                if enemy_battle_pet.use_skill(skill):
                    if skill['type'] == 'attack':
                        damage = skill['power'] + enemy_pet.attributes['attack']
                        player_battle_pet.take_damage(damage)
                        battle_log.append(f"{enemy_pet.name}使用了{skill['name']}，造成{damage}点伤害")
                    elif skill['type'] == 'heal':
                        heal_amount = skill['power']
                        enemy_battle_pet.heal(heal_amount)
                        battle_log.append(f"{enemy_pet.name}使用了{skill['name']}，恢复了{heal_amount}点生命值")
                    elif skill['type'] == 'defense':
                        enemy_battle_pet.status.append({'type': 'shield', 'duration': 3, 'power': skill['power']})
                        battle_log.append(f"{enemy_pet.name}使用了{skill['name']}，获得了防御加成")
                    elif skill['type'] == 'buff':
                        enemy_battle_pet.status.append({'type': 'buff', 'duration': 5, 'power': skill['power']})
                        battle_log.append(f"{enemy_pet.name}使用了{skill['name']}，获得了属性加成")
            else:
                # 普通攻击
                damage = enemy_pet.attributes['attack']
                player_battle_pet.take_damage(damage)
                battle_log.append(f"{enemy_pet.name}使用了普通攻击，造成{damage}点伤害")
            
            # 检查战斗是否结束
            if player_battle_pet.is_defeated() or enemy_battle_pet.is_defeated():
                battle_phase = "battle_end"
                if not player_battle_pet.is_defeated():
                    # 战斗胜利，获得经验和奖励
                    experience = enemy_pet.level * 10
                    player_pet.add_experience(experience)
                    battle_log.append(f"战斗胜利！获得{experience}点经验")
                    # 随机获得宠物食物
                    food_reward = random.randint(1, 3)
                    data['resources']['pet_food'] = data['resources'].get('pet_food', 0) + food_reward
                    battle_log.append(f"获得{food_reward}个宠物食物")
                    save()
            else:
                # 切换到玩家回合
                battle_phase = "player_turn"
        
        # 更新宠物状态
        player_battle_pet.update()
        enemy_battle_pet.update()
        
        clock.tick(60)

def pet_arena_menu():
    """宠物竞技场菜单"""
    global screen, clock, FONT_MAIN, FONT_SMALL
    
    # 确保宠物数据存在
    if 'pet' not in data:
        data['pet'] = Pet().to_dict()
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
        button_width = min(200, screen_width * 0.3)
        button_height = min(60, screen_height * 0.08)
        button_spacing = min(20, screen_height * 0.03)
        
        # 渐变背景
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
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
        
        # 标题
        draw_title(screen, "宠物竞技场", screen_height * 0.12, screen_width)
        
        # 绘制宠物信息
        pet_x = screen_width // 2
        pet_y = screen_height // 2 - 100
        
        # 绘制宠物视觉效果
        draw_pet_visual(screen, pet, pet_x, pet_y, 150)
        
        # 宠物信息
        name_text = FONT_MAIN.render(f"{pet.name} (Lv.{pet.level})", True, COLORS["text_white"])
        type_text = FONT_SMALL.render(f"类型: {pet.type}", True, COLORS["text_white"])
        element_text = FONT_SMALL.render(f"元素: {pet.element}", True, COLORS["text_white"])
        
        screen.blit(name_text, (pet_x - name_text.get_width() // 2, pet_y - 100))
        screen.blit(type_text, (pet_x - type_text.get_width() // 2, pet_y - 60))
        screen.blit(element_text, (pet_x - element_text.get_width() // 2, pet_y - 30))
        
        # 绘制挑战按钮
        challenge_buttons = []
        start_y = screen_height * 0.7
        
        challenge_levels = [(10, "初级挑战"), (20, "中级挑战"), (30, "高级挑战"), (50, "终极挑战")]
        for i, (level, label) in enumerate(challenge_levels):
            if pet.level >= level - 5:
                challenge_button = Button(label, screen_width // 2 - button_width // 2, start_y + i * (button_height + button_spacing), button_width, button_height, FONT_SMALL)
                challenge_buttons.append((challenge_button, level))
                challenge_button.check_hover(pygame.mouse.get_pos())
                challenge_button.draw(screen)
            else:
                # 未解锁的挑战
                lock_text = FONT_SMALL.render(f"{label} (Lv.{level}解锁)", True, (100, 100, 100))
                screen.blit(lock_text, (screen_width // 2 - lock_text.get_width() // 2, start_y + i * (button_height + button_spacing) + 15))
        
        # 返回按钮
        back_button = Button("返回", screen_width // 2 - button_width // 2, start_y + len(challenge_levels) * (button_height + button_spacing) + 20, button_width, button_height, FONT_SMALL, normal_color=(100, 100, 150))
        back_button.check_hover(pygame.mouse.get_pos())
        back_button.draw(screen)
        
        pygame.display.flip()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 处理挑战按钮点击
                for challenge_button, level in challenge_buttons:
                    if challenge_button.rect.collidepoint(event.pos):
                        # 创建敌方宠物
                        enemy_pet = create_enemy_pet(level)
                        # 开始战斗
                        battle(pet, enemy_pet)
                        # 保存宠物数据
                        data['pet'] = pet.to_dict()
                        save()
                        break
                
                # 处理返回按钮
                if back_button.rect.collidepoint(event.pos):
                    running = False
        
        clock.tick(60)

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
    except Exception as _e:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 28)

def main():
    """宠物竞技场主函数"""
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
    
    # 运行宠物竞技场菜单
    pet_arena_menu()

if __name__ == '__main__':
    main()
