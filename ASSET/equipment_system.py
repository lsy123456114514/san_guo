import os
import pygame
import random
import datetime
from ASSET.game_data import data, save, get_system_font_name
from ASSET.languages import get_text
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
    "panel_bg": (30, 30, 55, 200),
    "accent_purple": (128, 0, 128)
}

class Button:
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
                self.render_item(container_surface, item, self.x, item_y)
        
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

class EquipmentScrollContainer(ScrollableContainer):
    def __init__(self, x, y, width, height, item_height, items, font_main, font_small, equip_type):
        super().__init__(x, y, width, height, item_height)
        self.items = items
        self.font_main = font_main
        self.font_small = font_small
        self.equip_type = equip_type
        self.max_scroll = max(0, len(items) * item_height - height)
        
    def render_item(self, surface, equip, x, y):
        equip_rect = pygame.Rect(x, y, self.width - 20, self.item_height - 5)
        
        pygame.draw.rect(surface, (40, 40, 70, 200), equip_rect, border_radius=10)
        pygame.draw.rect(surface, COLORS["accent_gold"], equip_rect, 2, border_radius=10)
        
        name_surf = self.font_main.render(f"{equip['name']} ({equip['level_name']})", True, COLORS["accent_gold"])
        level_surf = self.font_small.render(f"强化等级: {equip['enhancement_level']}", True, COLORS["text_white"])
        attr_text = ", ".join([f"{k}:{v}" for k, v in equip["attributes"].items()])
        attr_surf = self.font_small.render(f"属性: {attr_text}", True, COLORS["text_gray"])
        
        surface.blit(name_surf, (x + 10, y + 5))
        surface.blit(level_surf, (x + 10, y + 30))
        surface.blit(attr_surf, (x + 10, y + 50))

def draw_gradient_background(surface, color1, color2):
    """绘制渐变背景"""
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

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

class EquipmentSystem:
    """装备系统"""
    def __init__(self):
        # 初始化装备数据
        if "equipment" not in data:
            data["equipment"] = {
                "weapons": [],
                "armors": [],
                "accessories": [],
                "mounts": []
            }
        
        # 装备类型
        self.equip_types = ["weapon", "armor", "accessory"]
        
        # 装备等级
        self.equip_levels = {
            "zh": ["普通", "优秀", "稀有", "史诗", "传说"],
            "en": ["Common", "Uncommon", "Rare", "Epic", "Legendary"],
            "ja": ["一般", "珍しい", "希少", "エピック", "伝説"]
        }
        
        # 装备属性
        self.equip_attributes = {
            "weapon": {
                "zh": ["攻击力", "暴击率", "攻击速度"],
                "en": ["Attack", "Critical Rate", "Attack Speed"],
                "ja": ["攻撃力", "クリティカル率", "攻撃速度"]
            },
            "armor": {
                "zh": ["防御力", "生命值", "闪避率"],
                "en": ["Defense", "HP", "Dodge Rate"],
                "ja": ["防御力", "HP", "回避率"]
            },
            "accessory": {
                "zh": ["暴击伤害", "冷却缩减", "移动速度"],
                "en": ["Critical Damage", "Cooldown Reduction", "Movement Speed"],
                "ja": ["クリティカルダメージ", "冷却短縮", "移動速度"]
            }
        }
        
        # 装备名称
        self.equip_names = {
            "weapon": {
                "zh": ["青龙偃月刀", "方天画戟", "丈八蛇矛", "龙胆亮银枪", "雌雄双股剑"],
                "en": ["Green Dragon Crescent Blade", "Heavenly Halberd", "Serpent Spear", "Dragon Bright Silver Spear", "Twin Swords"],
                "ja": ["青龍偃月刀", "方天画戟", "丈八蛇矛", "龍胆亮銀槍", "雌雄双股剣"]
            },
            "armor": {
                "zh": ["锁子甲", "连环铠", "明光铠", "雁翎甲", "金缕玉衣"],
                "en": ["Chain Mail", "Link Armor", "Bright Light Armor", "Wild Goose Feather Armor", "Golden Threaded Jade Robe"],
                "ja": ["鎖子甲", "連環鎧", "明光鎧", "雁翎甲", "金縷玉衣"]
            },
            "accessory": {
                "zh": ["赤兔马", "的卢马", "绝影", "爪黄飞电", "乌云踏雪"],
                "en": ["Red Hare", "Di Lu", "Shadow", "Claw Yellow Flying Lightning", "Dark Cloud Treading Snow"],
                "ja": ["赤兎馬", "的盧馬", "絶影", "爪黄飛電", "烏雲踏雪"]
            }
        }
    
    def create_equipment(self, equip_type, level=0):
        """创建装备"""
        # 获取当前语言
        current_lang = data['settings']['language']['current']
        
        # 获取装备等级名称
        level_name = self.equip_levels.get(current_lang, self.equip_levels["zh"])[level]
        
        # 获取装备属性
        attributes = self.equip_attributes[equip_type].get(current_lang, self.equip_attributes[equip_type]["zh"])
        
        # 生成装备名称
        names = self.equip_names[equip_type].get(current_lang, self.equip_names[equip_type]["zh"])
        name = random.choice(names)
        
        # 生成装备属性
        equip_attributes = {}
        for attr in attributes:
            # 基础属性值
            base_value = random.randint(10, 20) * (level + 1)
            # 随机波动
            value = base_value + random.randint(-2, 2)
            equip_attributes[attr] = max(1, value)
        
        # 生成装备
        equipment = {
            "id": f"equip_{datetime.datetime.now().timestamp()}",
            "name": name,
            "type": equip_type,
            "level": level,
            "level_name": level_name,
            "attributes": equip_attributes,
            "enhancement_level": 0,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # 添加到对应类型的装备列表
        if equip_type == "weapon":
            data["equipment"]["weapons"].append(equipment)
        elif equip_type == "armor":
            data["equipment"]["armors"].append(equipment)
        else:
            data["equipment"]["accessories"].append(equipment)
        
        save()
        return equipment
    
    def enhance_equipment(self, equipment):
        """强化装备"""
        import time
        # 获取当前语言
        current_lang = data.get('settings', {}).get('language', {}).get('current', 'zh')
        
        # 计算强化时间（基础时间 * 强化等级 / 2）
        base_time = data.get('settings', {}).get('time', {}).get('base_time', 60)
        time_required = base_time * (equipment["enhancement_level"] + 1) / 2
        
        # 创建时间任务
        task = {
            "id": f"task_{time.time()}",
            "type": "enhance_equipment",
            "equipment_id": equipment["id"],
            "equipment_type": equipment["type"],
            "start_level": equipment["enhancement_level"],
            "start_time": time.time(),
            "end_time": time.time() + time_required,
            "status": "active"
        }
        
        data["time_tasks"]["active"].append(task)
        save()
        return True, f"装备强化已开始，需要 {int(time_required)} 秒"
        
        # 强化成功率
        success_rate = max(30, 90 - equipment["enhancement_level"] * 5)
        
        # 检查是否成功
        if random.randint(1, 100) <= success_rate:
            # 强化成功
            equipment["enhancement_level"] += 1
            
            # 提升属性
            for attr in equipment["attributes"]:
                # 每次强化提升10%的属性
                equipment["attributes"][attr] = int(equipment["attributes"][attr] * 1.1)
            
            save()
            # 根据语言返回不同的消息
            if current_lang == "zh":
                return True, f"装备强化成功！当前强化等级：{equipment['enhancement_level']}"
            elif current_lang == "en":
                return True, f"Equipment enhanced successfully! Current level: {equipment['enhancement_level']}"
            elif current_lang == "ja":
                return True, f"装備の強化に成功しました！現在のレベル：{equipment['enhancement_level']}"
            else:
                return True, f"装备强化成功！当前强化等级：{equipment['enhancement_level']}"
        else:
            # 强化失败
            if current_lang == "zh":
                return False, "装备强化失败！"
            elif current_lang == "en":
                return False, "Equipment enhancement failed!"
            elif current_lang == "ja":
                return False, "装備の強化に失敗しました！"
            else:
                return False, "装备强化失败！"

class MountSystem:
    """坐骑系统"""
    def __init__(self):
        # 初始化坐骑数据
        if "mounts" not in data:
            data["mounts"] = {
                "owned": [],
                "active": None
            }
        
        # 坐骑列表
        self.mount_types = [
            {"name": "赤兔马", "speed": 150, "rarity": "史诗", "ability": "冲锋：短时间内速度提升50%"},
            {"name": "的卢马", "speed": 140, "rarity": "稀有", "ability": "跳跃：可以跳过障碍物"},
            {"name": "绝影", "speed": 130, "rarity": "稀有", "ability": "闪避：有几率闪避敌人攻击"},
            {"name": "爪黄飞电", "speed": 120, "rarity": "优秀", "ability": "耐力：持续奔跑时间更长"},
            {"name": "乌云踏雪", "speed": 110, "rarity": "普通", "ability": "稳定：不容易被打下马"}
        ]
    
    def get_mount_by_name(self, name):
        for mount in self.mount_types:
            if mount["name"] == name:
                return mount
        return None
    
    def obtain_mount(self, mount_name):
        """获得坐骑"""
        import time
        mount = self.get_mount_by_name(mount_name)
        if mount:
            # 检查是否已经拥有
            for owned_mount in data["mounts"]["owned"]:
                if owned_mount["name"] == mount_name:
                    return False, "已经拥有该坐骑"
            
            # 计算获得时间（基础时间 * 3）
            base_time = data.get('settings', {}).get('time', {}).get('base_time', 60)
            time_required = base_time * 3
            
            # 创建时间任务
            task = {
                "id": f"task_{time.time()}",
                "type": "obtain_mount",
                "mount_name": mount_name,
                "mount_data": {
                    "name": mount_name,
                    "level": 1,
                    "exp": 0,
                    "speed": mount["speed"],
                    "rarity": mount["rarity"],
                    "ability": mount["ability"],
                    "obtained_at": datetime.datetime.now().isoformat()
                },
                "start_time": time.time(),
                "end_time": time.time() + time_required,
                "status": "active"
            }
            
            data["time_tasks"]["active"].append(task)
            save()
            return True, f"坐骑获得已开始，需要 {int(time_required)} 秒"
        return False, "坐骑不存在"
    
    def activate_mount(self, mount_name):
        """激活坐骑"""
        import time
        for mount in data["mounts"]["owned"]:
            if mount["name"] == mount_name:
                # 计算激活时间（基础时间 * 1.5）
                base_time = data.get('settings', {}).get('time', {}).get('base_time', 60)
                time_required = base_time * 1.5
                
                # 创建时间任务
                task = {
                    "id": f"task_{time.time()}",
                    "type": "activate_mount",
                    "mount_name": mount_name,
                    "start_time": time.time(),
                    "end_time": time.time() + time_required,
                    "status": "active"
                }
                
                data["time_tasks"]["active"].append(task)
                save()
                return True, f"坐骑激活已开始，需要 {int(time_required)} 秒"
        return False, "坐骑不存在"

class SkillSystem:
    """技能系统"""
    def __init__(self):
        # 初始化技能数据
        if "skills" not in data:
            data["skills"] = {
                "learned": [],
                "equipped": []
            }
        
        # 技能列表
        self.skill_types = [
            {"name": "横扫千军", "type": "攻击", "damage": 200, "cooldown": 10, "description": "对周围敌人造成范围伤害"},
            {"name": "金钟罩", "type": "防御", "defense": 150, "cooldown": 15, "description": "暂时提升防御力"},
            {"name": "治疗术", "type": "辅助", "heal": 100, "cooldown": 8, "description": "恢复生命值"},
            {"name": "闪电击", "type": "攻击", "damage": 250, "cooldown": 12, "description": "对单个敌人造成高额伤害"},
            {"name": "加速术", "type": "辅助", "speed": 50, "cooldown": 10, "description": "提升移动速度"}
        ]
    
    def learn_skill(self, skill_name):
        """学习技能"""
        import time
        for skill in self.skill_types:
            if skill["name"] == skill_name:
                # 检查是否已经学习
                for learned_skill in data["skills"]["learned"]:
                    if learned_skill["name"] == skill_name:
                        return False, "已经学习过该技能"
                
                # 计算学习时间（基础时间 * 技能冷却时间 / 10）
                base_time = data.get('settings', {}).get('time', {}).get('base_time', 60)
                time_required = base_time * (skill["cooldown"] / 10)
                
                # 创建时间任务
                task = {
                    "id": f"task_{time.time()}",
                    "type": "learn_skill",
                    "skill_name": skill_name,
                    "skill_data": {
                        "name": skill_name,
                        "type": skill["type"],
                        "level": 1,
                        "exp": 0,
                        "damage": skill["damage"],
                        "defense": skill.get("defense", 0),
                        "heal": skill.get("heal", 0),
                        "speed": skill.get("speed", 0),
                        "cooldown": skill["cooldown"],
                        "description": skill["description"],
                        "learned_at": datetime.datetime.now().isoformat()
                    },
                    "start_time": time.time(),
                    "end_time": time.time() + time_required,
                    "status": "active"
                }
                
                data["time_tasks"]["active"].append(task)
                save()
                return True, f"技能学习已开始，需要 {int(time_required)} 秒"
        return False, "技能不存在"
    
    def equip_skill(self, skill_name):
        """装备技能"""
        # 检查是否学习过该技能
        learned = False
        for skill in data["skills"]["learned"]:
            if skill["name"] == skill_name:
                learned = True
                break
        
        if not learned:
            return False, "尚未学习该技能"
        
        # 检查是否已经装备
        for equipped_skill in data["skills"]["equipped"]:
            if equipped_skill["name"] == skill_name:
                return False, "已经装备该技能"
        
        # 检查装备槽位
        if len(data["skills"]["equipped"]) >= 3:
            return False, "装备槽位已满"
        
        # 装备技能
        data["skills"]["equipped"].append(skill_name)
        save()
        return True, f"{skill_name} 已装备！"

class GuildSystem:
    """公会系统"""
    def __init__(self):
        # 初始化公会数据
        if "guild" not in data:
            data["guild"] = {
                "name": "",
                "level": 1,
                "members": [],
                "resources": 0,
                "created_at": None
            }
    
    def create_guild(self, guild_name):
        """创建公会"""
        if data["guild"]["name"]:
            return False, "已经加入或创建了公会"
        
        data["guild"]["name"] = guild_name
        data["guild"]["members"].append({
            "username": data.get("username", "player"),
            "role": "leader",
            "join_date": datetime.datetime.now().isoformat()
        })
        data["guild"]["created_at"] = datetime.datetime.now().isoformat()
        save()
        return True, f"公会 {guild_name} 创建成功！"
    
    def join_guild(self, guild_name):
        """加入公会"""
        if data["guild"]["name"]:
            return False, "已经加入或创建了公会"
        
        # 这里简化处理，实际应该有公会列表
        data["guild"]["name"] = guild_name
        data["guild"]["members"].append({
            "username": data.get("username", "player"),
            "role": "member",
            "join_date": datetime.datetime.now().isoformat()
        })
        save()
        return True, f"成功加入公会 {guild_name}！"

class TradingSystem:
    """交易系统"""
    def __init__(self):
        # 初始化交易数据
        if "trading" not in data:
            data["trading"] = {
                "offers": []
            }

    def create_offer(self, item_type, item_name, price):
        """创建交易 offer"""
        offer = {
            "id": f"offer_{datetime.datetime.now().timestamp()}",
            "seller": data.get("username", "player"),
            "item_type": item_type,
            "item_name": item_name,
            "price": price,
            "created_at": datetime.datetime.now().isoformat(),
            "status": "active"
        }
        data["trading"]["offers"].append(offer)
        save()
        return True, "交易 offer 创建成功！"

    def buy_item(self, offer_id):
        """购买物品"""
        for offer in data["trading"]["offers"]:
            if offer["id"] == offer_id and offer["status"] == "active":
                # 检查金币是否足够
                if data["resources"].get("金元宝", 0) >= offer["price"]:
                    # 扣除金币
                    data["resources"]["金元宝"] -= offer["price"]
                    # 标记交易完成
                    offer["status"] = "completed"
                    offer["buyer"] = data.get("username", "player")
                    offer["completed_at"] = datetime.datetime.now().isoformat()
                    save()
                    return True, f"购买成功！"
                else:
                    return False, "金币不足"
        return False, "交易 offer 不存在"

    def buy_bullets_direct(self, bullet_type, quantity, price_per_unit):
        """直接从商店购买子弹"""
        total_price = quantity * price_per_unit
        if data["resources"].get("金元宝", 0) >= total_price:
            data["resources"]["金元宝"] -= total_price
            data["resources"][bullet_type] = data["resources"].get(bullet_type, 0) + quantity
            save()
            return True, f"购买成功！获得 {quantity} 颗 {bullet_type}"
        else:
            return False, "金币不足"

def draw_bullet_shop(screen, font_big, font_main, font_small):
    """绘制子弹商店"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    # 标题
    draw_title(screen, "🔫 子弹商店", screen_height * 0.1, screen_width, font_big)

    trading_system = TradingSystem()

    # 子弹类型和价格
    bullet_types = [
        {"name": "普通子弹", "price": 5, "icon": "🔫", "color": COLORS["text_gray"]},
        {"name": "高级子弹", "price": 15, "icon": "🔫🔫", "color": COLORS["accent_blue"]},
        {"name": "稀有子弹", "price": 50, "icon": "🔫🔥", "color": COLORS["accent_red"]}
    ]

    y_offset = screen_height * 0.2

    for bullet in bullet_types:
        bullet_rect = pygame.Rect(50, y_offset, screen_width - 100, 100)

        # 背景
        pygame.draw.rect(screen, (40, 40, 70, 200), bullet_rect, border_radius=10)
        pygame.draw.rect(screen, bullet["color"], bullet_rect, 2, border_radius=10)

        # 子弹信息
        name_surf = font_main.render(f"{bullet['icon']} {bullet['name']}", True, bullet["color"])
        price_surf = font_small.render(f"价格: {bullet['price']} 金元宝/颗", True, COLORS["text_white"])
        owned_surf = font_small.render(f"拥有: {data['resources'].get(bullet['name'], 0)}", True, COLORS["text_gray"])

        screen.blit(name_surf, (60, y_offset + 10))
        screen.blit(price_surf, (60, y_offset + 45))
        screen.blit(owned_surf, (60, y_offset + 70))

        # 购买按钮组
        buy_1_btn = Button("买1", screen_width - 280, y_offset + 30, 70, 40, font_small, normal_color=COLORS["accent_green"])
        buy_10_btn = Button("买10", screen_width - 190, y_offset + 30, 70, 40, font_small, normal_color=COLORS["accent_green"])
        buy_100_btn = Button("买100", screen_width - 100, y_offset + 30, 70, 40, font_small, normal_color=COLORS["accent_green"])

        buy_1_btn.draw(screen)
        buy_10_btn.draw(screen)
        buy_100_btn.draw(screen)

        y_offset += 110

    return trading_system, bullet_types

def draw_equipment_system(screen, font_big, font_main, font_small):
    """绘制装备系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 获取当前语言
    current_lang = data.get('settings', {}).get('language', {}).get('current', 'zh')
    
    # 标题
    draw_title(screen, "装备系统", screen_height * 0.1, screen_width, font_big)
    
    equipment_system = EquipmentSystem()
    
    # 装备列表
    y_offset = screen_height * 0.2
    
    # 武器
    weapon_title = font_main.render("武器", True, COLORS["accent_blue"])
    screen.blit(weapon_title, (50, y_offset))
    y_offset += 40
    
    if not data["equipment"]["weapons"]:
        empty_surf = font_small.render("暂无武器", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for equip in data["equipment"]["weapons"]:
            equip_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
            
            # 背景
            pygame.draw.rect(screen, (40, 40, 70, 200), equip_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["accent_gold"], equip_rect, 2, border_radius=10)
            
            # 装备信息
            name_surf = font_main.render(f"{equip['name']} ({equip['level_name']})", True, COLORS["accent_gold"])
            level_surf = font_small.render(f"强化等级: {equip['enhancement_level']}", True, COLORS["text_white"])
            
            # 属性
            attr_text = ", ".join([f"{k}:{v}" for k, v in equip["attributes"].items()])
            attr_surf = font_small.render(f"属性: {attr_text}", True, COLORS["text_gray"])
            
            screen.blit(name_surf, (60, y_offset + 10))
            screen.blit(level_surf, (60, y_offset + 35))
            screen.blit(attr_surf, (60, y_offset + 55))
            
            # 强化按钮
            enhance_btn = Button("强化", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
            enhance_btn.draw(screen)
            
            y_offset += 90
    
    # 护甲
    y_offset += 20
    armor_title = font_main.render("护甲", True, COLORS["accent_green"])
    screen.blit(armor_title, (50, y_offset))
    y_offset += 40
    
    if not data["equipment"]["armors"]:
        empty_surf = font_small.render("暂无护甲", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for equip in data["equipment"]["armors"]:
            equip_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
            
            # 背景
            pygame.draw.rect(screen, (40, 40, 70, 200), equip_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["accent_gold"], equip_rect, 2, border_radius=10)
            
            # 装备信息
            name_surf = font_main.render(f"{equip['name']} ({equip['level_name']})", True, COLORS["accent_gold"])
            level_surf = font_small.render(f"强化等级: {equip['enhancement_level']}", True, COLORS["text_white"])
            
            # 属性
            attr_text = ", ".join([f"{k}:{v}" for k, v in equip["attributes"].items()])
            attr_surf = font_small.render(f"属性: {attr_text}", True, COLORS["text_gray"])
            
            screen.blit(name_surf, (60, y_offset + 10))
            screen.blit(level_surf, (60, y_offset + 35))
            screen.blit(attr_surf, (60, y_offset + 55))
            
            # 强化按钮
            enhance_btn = Button("强化", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
            enhance_btn.draw(screen)
            
            y_offset += 90
    
    # 饰品
    y_offset += 20
    accessory_title = font_main.render("饰品", True, COLORS["accent_purple"])
    screen.blit(accessory_title, (50, y_offset))
    y_offset += 40
    
    if not data["equipment"]["accessories"]:
        empty_surf = font_small.render("暂无饰品", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for equip in data["equipment"]["accessories"]:
            equip_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
            
            # 背景
            pygame.draw.rect(screen, (40, 40, 70, 200), equip_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["accent_gold"], equip_rect, 2, border_radius=10)
            
            # 装备信息
            name_surf = font_main.render(f"{equip['name']} ({equip['level_name']})", True, COLORS["accent_gold"])
            level_surf = font_small.render(f"强化等级: {equip['enhancement_level']}", True, COLORS["text_white"])
            
            # 属性
            attr_text = ", ".join([f"{k}:{v}" for k, v in equip["attributes"].items()])
            attr_surf = font_small.render(f"属性: {attr_text}", True, COLORS["text_gray"])
            
            screen.blit(name_surf, (60, y_offset + 10))
            screen.blit(level_surf, (60, y_offset + 35))
            screen.blit(attr_surf, (60, y_offset + 55))
            
            # 强化按钮
            enhance_btn = Button("强化", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
            enhance_btn.draw(screen)
            
            y_offset += 90

def draw_mount_system(screen, font_big, font_main, font_small):
    """绘制坐骑系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "坐骑系统", screen_height * 0.1, screen_width, font_big)
    
    mount_system = MountSystem()
    
    # 坐骑列表
    y_offset = screen_height * 0.2
    
    for mount in mount_system.mount_types:
        mount_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
        
        # 背景
        pygame.draw.rect(screen, (40, 40, 70, 200), mount_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], mount_rect, 2, border_radius=10)
        
        # 坐骑信息
        name_surf = font_main.render(mount["name"], True, COLORS["accent_gold"])
        speed_surf = font_small.render(f"速度: {mount['speed']}", True, COLORS["text_white"])
        rarity_surf = font_small.render(f"稀有度: {mount['rarity']}", True, COLORS["text_gray"])
        ability_surf = font_small.render(f"技能: {mount['ability']}", True, COLORS["text_white"])
        
        screen.blit(name_surf, (60, y_offset + 10))
        screen.blit(speed_surf, (60, y_offset + 35))
        screen.blit(rarity_surf, (200, y_offset + 35))
        screen.blit(ability_surf, (60, y_offset + 55))
        
        # 获得按钮
        obtain_btn = Button("获得", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
        obtain_btn.draw(screen)
        
        y_offset += 90

def draw_skill_system(screen, font_big, font_main, font_small):
    """绘制技能系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "技能系统", screen_height * 0.1, screen_width, font_big)
    
    skill_system = SkillSystem()
    
    # 技能列表
    y_offset = screen_height * 0.2
    
    for skill in skill_system.skill_types:
        skill_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
        
        # 背景
        pygame.draw.rect(screen, (40, 40, 70, 200), skill_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], skill_rect, 2, border_radius=10)
        
        # 技能信息
        name_surf = font_main.render(skill["name"], True, COLORS["accent_gold"])
        type_surf = font_small.render(f"类型: {skill['type']}", True, COLORS["text_white"])
        cooldown_surf = font_small.render(f"冷却: {skill['cooldown']}秒", True, COLORS["text_gray"])
        description_surf = font_small.render(f"描述: {skill['description']}", True, COLORS["text_white"])
        
        screen.blit(name_surf, (60, y_offset + 10))
        screen.blit(type_surf, (60, y_offset + 35))
        screen.blit(cooldown_surf, (200, y_offset + 35))
        screen.blit(description_surf, (60, y_offset + 55))
        
        # 学习按钮
        learn_btn = Button("学习", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
        learn_btn.draw(screen)
        
        y_offset += 90

def draw_guild_system(screen, font_big, font_main, font_small):
    """绘制公会系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "公会系统", screen_height * 0.1, screen_width, font_big)
    
    guild_system = GuildSystem()
    
    y_offset = screen_height * 0.2
    
    if data["guild"]["name"]:
        # 已加入公会
        guild_rect = pygame.Rect(50, y_offset, screen_width - 100, 120)
        
        # 背景
        pygame.draw.rect(screen, (40, 40, 70, 200), guild_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], guild_rect, 2, border_radius=10)
        
        # 公会信息
        name_surf = font_main.render(f"公会名称: {data['guild']['name']}", True, COLORS["accent_gold"])
        level_surf = font_small.render(f"公会等级: {data['guild']['level']}", True, COLORS["text_white"])
        members_surf = font_small.render(f"成员数量: {len(data['guild']['members'])}", True, COLORS["text_gray"])
        resources_surf = font_small.render(f"公会资源: {data['guild']['resources']}", True, COLORS["text_white"])
        
        screen.blit(name_surf, (60, y_offset + 10))
        screen.blit(level_surf, (60, y_offset + 40))
        screen.blit(members_surf, (60, y_offset + 70))
        screen.blit(resources_surf, (60, y_offset + 100))
    else:
        # 未加入公会
        create_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
        
        # 背景
        pygame.draw.rect(screen, (40, 40, 70, 200), create_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], create_rect, 2, border_radius=10)
        
        # 提示信息
        info_surf = font_main.render("您尚未加入或创建公会", True, COLORS["text_white"])
        screen.blit(info_surf, (60, y_offset + 30))
        
        # 创建和加入按钮
        create_btn = Button("创建公会", screen_width - 300, y_offset + 10, 130, 60, font_small, normal_color=COLORS["accent_green"])
        create_btn.draw(screen)
        
        join_btn = Button("加入公会", screen_width - 150, y_offset + 10, 130, 60, font_small, normal_color=COLORS["accent_blue"])
        join_btn.draw(screen)

def draw_trading_system(screen, font_big, font_main, font_small):
    """绘制交易系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "交易系统", screen_height * 0.1, screen_width, font_big)
    
    trading_system = TradingSystem()
    
    # 交易 offer 列表
    y_offset = screen_height * 0.2
    
    if not data["trading"]["offers"]:
        empty_surf = font_small.render("暂无交易 offer", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for offer in data["trading"]["offers"]:
            if offer["status"] == "active":
                offer_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
                
                # 背景
                pygame.draw.rect(screen, (40, 40, 70, 200), offer_rect, border_radius=10)
                pygame.draw.rect(screen, COLORS["accent_gold"], offer_rect, 2, border_radius=10)
                
                # 交易信息
                item_surf = font_main.render(f"{offer['item_name']}", True, COLORS["accent_gold"])
                seller_surf = font_small.render(f"卖家: {offer['seller']}", True, COLORS["text_white"])
                price_surf = font_small.render(f"价格: {offer['price']} 金元宝", True, COLORS["text_gray"])
                
                screen.blit(item_surf, (60, y_offset + 10))
                screen.blit(seller_surf, (60, y_offset + 35))
                screen.blit(price_surf, (200, y_offset + 35))
                
                # 购买按钮
                buy_btn = Button("购买", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
                buy_btn.draw(screen)
                
                y_offset += 90

def main():
    """装备系统主函数"""
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
        pygame.display.set_caption("装备系统")
        clock = pygame.time.Clock()

        # 字体初始化（根据屏幕大小自适应）
        def init_font(size):
            font_name = get_system_font_name()
            # 根据屏幕大小调整字体
            adjusted_size = int(size * min(SCREEN_WIDTH / 900, SCREEN_HEIGHT / 700))
            try:
                return pygame.font.SysFont(font_name, adjusted_size)
            except Exception:
                return pygame.font.Font(None, adjusted_size)

        font_big = init_font(48)
        font_main = init_font(32)
        font_small = init_font(24)

        # 系统初始化
        equipment_system = EquipmentSystem()
        mount_system = MountSystem()
        skill_system = SkillSystem()
        guild_system = GuildSystem()
        trading_system = TradingSystem()

        # 当前页面
        current_page = "equipment"  # equipment, mount, skill, guild, trading

        # 主循环
        running = True
        while running:
            import time
            mx, my = pygame.mouse.get_pos()
            
            # 处理时间任务
            current_time = time.time()
            completed_tasks = []
            
            # 确保time_tasks数据存在
            if "time_tasks" not in data:
                data["time_tasks"] = {"active": [], "completed": []}
            
            for task in data["time_tasks"]["active"]:
                if current_time >= task["end_time"]:
                    # 任务完成，执行相应操作
                    if task["type"] == "learn_skill":
                        # 学习技能
                        data["skills"]["learned"].append(task["skill_data"])
                        show_message(screen, f"技能 {task['skill_name']} 学习完成！", font_main)
                    elif task["type"] == "enhance_equipment":
                        # 强化装备
                        for equip in data["equipment"][task["equipment_type"] + "s"]:
                            if equip["id"] == task["equipment_id"]:
                                # 强化成功
                                equip["enhancement_level"] += 1
                                # 提升属性
                                for attr in equip["attributes"]:
                                    equip["attributes"][attr] = int(equip["attributes"][attr] * 1.1)
                                show_message(screen, f"装备强化成功！当前强化等级：{equip['enhancement_level']}", font_main)
                                break
                    elif task["type"] == "obtain_mount":
                        # 获得坐骑
                        data["mounts"]["owned"].append(task["mount_data"])
                        show_message(screen, f"成功获得 {task['mount_name']}！", font_main)
                    elif task["type"] == "activate_mount":
                        # 激活坐骑
                        data["mounts"]["active"] = task["mount_name"]
                        show_message(screen, f"{task['mount_name']} 已激活！", font_main)
                    
                    # 标记任务为已完成
                    task["status"] = "completed"
                    completed_tasks.append(task)
            
            # 移动已完成的任务到completed列表
            for task in completed_tasks:
                data["time_tasks"]["active"].remove(task)
                data["time_tasks"]["completed"].append(task)
            
            # 保存数据
            if completed_tasks:
                save()
            
            # 渐变背景
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 导航按钮
            nav_buttons = [
                ("装备系统", "equipment", 50, SCREEN_HEIGHT - 70),
                ("坐骑系统", "mount", 200, SCREEN_HEIGHT - 70),
                ("技能系统", "skill", 350, SCREEN_HEIGHT - 70),
                ("公会系统", "guild", 500, SCREEN_HEIGHT - 70),
                ("交易系统", "trading", 650, SCREEN_HEIGHT - 70),
                ("子弹商店", "bullets", 800, SCREEN_HEIGHT - 70),
                ("返回", "back", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70)
            ]

            for text, page, x, y in nav_buttons:
                btn = Button(text, x, y, 120, 50, font_small)
                btn.check_hover((mx, my))
                btn.draw(screen)

            # 绘制当前页面
            if current_page == "equipment":
                draw_equipment_system(screen, font_big, font_main, font_small)
            elif current_page == "mount":
                draw_mount_system(screen, font_big, font_main, font_small)
            elif current_page == "skill":
                draw_skill_system(screen, font_big, font_main, font_small)
            elif current_page == "guild":
                draw_guild_system(screen, font_big, font_main, font_small)
            elif current_page == "trading":
                draw_trading_system(screen, font_big, font_main, font_small)
            elif current_page == "bullets":
                draw_bullet_shop(screen, font_big, font_main, font_small)
            
            # 绘制时间任务状态
            if data["time_tasks"]["active"]:
                task_y = 50
                for task in data["time_tasks"]["active"]:
                    remaining_time = max(0, int(task["end_time"] - current_time))
                    task_text = f"{task['type']}: {remaining_time}秒"
                    task_surf = font_small.render(task_text, True, COLORS["accent_gold"])
                    screen.blit(task_surf, (SCREEN_WIDTH - 200, task_y))
                    task_y += 30
            
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
                    
                    # 处理页面内按钮
                    if current_page == "equipment":
                        # 处理装备强化
                        y_offset = SCREEN_HEIGHT * 0.2 + 40
                        for equip in data["equipment"]["weapons"]:
                            enhance_btn = Button("强化", SCREEN_WIDTH - 150, y_offset + 20, 100, 40, font_small)
                            if enhance_btn.rect.collidepoint(event.pos):
                                success, message = equipment_system.enhance_equipment(equip)
                                show_message(screen, message, font_main)
                            y_offset += 90
                        
                        y_offset = SCREEN_HEIGHT * 0.2 + 40 + len(data["equipment"]["weapons"]) * 90 + 20
                        for equip in data["equipment"]["armors"]:
                            enhance_btn = Button("强化", SCREEN_WIDTH - 150, y_offset + 20, 100, 40, font_small)
                            if enhance_btn.rect.collidepoint(event.pos):
                                success, message = equipment_system.enhance_equipment(equip)
                                show_message(screen, message, font_main)
                            y_offset += 90
                        
                        y_offset = SCREEN_HEIGHT * 0.2 + 40 + (len(data["equipment"]["weapons"]) + len(data["equipment"]["armors"])) * 90 + 40
                        for equip in data["equipment"]["accessories"]:
                            enhance_btn = Button("强化", SCREEN_WIDTH - 150, y_offset + 20, 100, 40, font_small)
                            if enhance_btn.rect.collidepoint(event.pos):
                                success, message = equipment_system.enhance_equipment(equip)
                                show_message(screen, message, font_main)
                            y_offset += 90
                    
                    elif current_page == "mount":
                        # 处理坐骑获得
                        y_offset = SCREEN_HEIGHT * 0.2
                        for mount in mount_system.mount_types:
                            obtain_btn = Button("获得", SCREEN_WIDTH - 150, y_offset + 20, 100, 40, font_small)
                            if obtain_btn.rect.collidepoint(event.pos):
                                success, message = mount_system.obtain_mount(mount["name"])
                                show_message(screen, message, font_main)
                            y_offset += 90
                    
                    elif current_page == "skill":
                        # 处理技能学习
                        y_offset = SCREEN_HEIGHT * 0.2
                        for skill in skill_system.skill_types:
                            learn_btn = Button("学习", SCREEN_WIDTH - 150, y_offset + 20, 100, 40, font_small)
                            if learn_btn.rect.collidepoint(event.pos):
                                success, message = skill_system.learn_skill(skill["name"])
                                show_message(screen, message, font_main)
                            y_offset += 90
                    
                    elif current_page == "guild":
                        # 处理公会创建和加入
                        if not data["guild"]["name"]:
                            create_btn = Button("创建公会", SCREEN_WIDTH - 300, SCREEN_HEIGHT * 0.2 + 10, 130, 60, font_small)
                            join_btn = Button("加入公会", SCREEN_WIDTH - 150, SCREEN_HEIGHT * 0.2 + 10, 130, 60, font_small)
                            if create_btn.rect.collidepoint(event.pos):
                                # 简化处理，直接创建公会
                                success, message = guild_system.create_guild("测试公会")
                                show_message(screen, message, font_main)
                            elif join_btn.rect.collidepoint(event.pos):
                                # 简化处理，直接加入公会
                                success, message = guild_system.join_guild("测试公会")
                                show_message(screen, message, font_main)
                    
                    elif current_page == "trading":
                        # 处理交易购买
                        y_offset = SCREEN_HEIGHT * 0.2
                        for offer in data["trading"]["offers"]:
                            if offer["status"] == "active":
                                buy_btn = Button("购买", SCREEN_WIDTH - 150, y_offset + 20, 100, 40, font_small)
                                if buy_btn.rect.collidepoint(event.pos):
                                    success, message = trading_system.buy_item(offer["id"])
                                    show_message(screen, message, font_main)
                                y_offset += 90

                    elif current_page == "bullets":
                        bullet_types = [
                            {"name": "普通子弹", "price": 5},
                            {"name": "高级子弹", "price": 15},
                            {"name": "稀有子弹", "price": 50}
                        ]
                        y_offset = SCREEN_HEIGHT * 0.2
                        for bullet in bullet_types:
                            buy_1_btn = Button("买1", SCREEN_WIDTH - 280, y_offset + 30, 70, 40, font_small)
                            buy_10_btn = Button("买10", SCREEN_WIDTH - 190, y_offset + 30, 70, 40, font_small)
                            buy_100_btn = Button("买100", SCREEN_WIDTH - 100, y_offset + 30, 70, 40, font_small)
                            if buy_1_btn.rect.collidepoint(event.pos):
                                success, message = trading_system.buy_bullets_direct(bullet["name"], 1, bullet["price"])
                                show_message(screen, message, font_main)
                            elif buy_10_btn.rect.collidepoint(event.pos):
                                success, message = trading_system.buy_bullets_direct(bullet["name"], 10, bullet["price"])
                                show_message(screen, message, font_main)
                            elif buy_100_btn.rect.collidepoint(event.pos):
                                success, message = trading_system.buy_bullets_direct(bullet["name"], 100, bullet["price"])
                                show_message(screen, message, font_main)
                            y_offset += 110
            
            clock.tick(60)
        
        safe_exit("装备系统")
    except Exception as e:
        print(f"异常：{str(e)}")
        print("详细错误信息：")
        import traceback
        traceback.print_exc()
        safe_exit("装备系统", str(e))

if __name__ == "__main__":
    main()
