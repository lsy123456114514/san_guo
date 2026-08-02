import os
import pygame
import platform
import time
import random
import math
from ASSET.game_data import data, save, get_system_font_name, load_sound, EQUIP_SKILLS, HERO_SKILLS, ELEMENTS, GUNS, HERO_BONDS, ELEMENT_WEAKNESS, safe_get, log_error
from ASSET.hero_database import HERO_DATABASE, FACTIONS as HERO_FACTION_MAP, EQUIPMENT_DATABASE, PASSIVE_EFFECTS
from ASSET.weather_system import WeatherSystem
from ASSET.event_system import EventSystem
from ASSET.welfare_center import get_vip_bonus
from ASSET.formation_system import FORMATIONS, apply_formation
from ASSET.divine_weapon_system import DIVINE_WEAPONS, is_divine_weapon, apply_divine_weapon
from ASSET.achievement_system import AchievementSystem
from ASSET import safe_exit

# 意味深长的话 - 胜利时
VICTORY_QUOTES = [
    "胜败乃兵家常事，今日之胜，不过是漫漫征途中的一粟。",
    "功名万里外，心事一杯中。天下未定，岂可懈怠？",
    "将军百战死，壮士十年归。每一场胜利，都是用鲜血换来的。",
    "天下大势，合久必分，分久必合。你的征途，才刚刚开始。",
    "非淡泊无以明志，非宁静无以致远。勿因一胜而骄，前路漫漫。",
    "大江东去，浪淘尽，千古风流人物。今日你亦是风流人物。",
    "鞠躬尽瘁，死而后已。为天下苍生而战，方为真英雄。",
    "宁教我负天下人，休教天下人负我。权谋之下，谁又能分清对错？",
    "勿以善小而不为，勿以恶小而为之。王者之道，在于仁心。",
    "古今多少事，都付笑谈中。待天下一统，再与故人把酒言欢。",
]

# 意味深长的话 - 失败时
DEFEAT_QUOTES = [
    "胜败乃兵家常事，英雄不问出处，亦不惧失败。",
    "天将降大任于斯人也，必先苦其心志。今日之败，是明日之胜的序章。",
    "留得青山在，不怕没柴烧。只要信念未灭，终有卷土重来之日。",
    "苦心人，天不负，卧薪尝胆，三千越甲可吞吴。",
    "失败是成功之母，每一道伤痕都是成长的勋章。",
    "风萧萧兮易水寒，壮士一去兮不复还。但你不同，你还有机会重来。",
    "不经一番寒彻骨，怎得梅花扑鼻香。坚持下去，终见曙光。",
    "山重水复疑无路，柳暗花明又一村。转机，往往就在再坚持一下之中。",
    "天下英雄谁敌手？失败只是告诉你，还需更强。",
    "千磨万击还坚劲，任尔东西南北风。真正的英雄，是从废墟中站起来的。",
]

def update_battle_stats(win, player_heroes, enemy_heroes, damage_dealt, damage_taken):
    """更新战斗统计数据到存档"""
    if "battle_stats" not in data:
        data["battle_stats"] = {
            "total_battles": 0,
            "victories": 0,
            "defeats": 0,
            "max_combo": 0,
            "ultimate_used_count": 0,
            "total_kills": 0,
            "skill_kills": 0,
            "win_streak": 0,
            "single_battle_kills": 0,
            "total_heal": 0,
            "formation_kills": 0,
            "damage_taken": 0,
            "battles_won": 0,
            "total_score": 0
        }
    
    data["battle_stats"]["total_battles"] += 1
    
    if win:
        data["battle_stats"]["victories"] += 1
        data["battle_stats"]["battles_won"] += 1
        data["battle_stats"]["win_streak"] += 1
        data["battle_stats"]["single_battle_kills"] += len(enemy_heroes)
        data["battle_stats"]["total_kills"] += len(enemy_heroes)
        data["battle_stats"]["total_score"] += damage_dealt
    else:
        data["battle_stats"]["defeats"] += 1
        data["battle_stats"]["win_streak"] = 0
    
    # 更新最大连击数
    max_combo = max([h.combo_count for h in player_heroes] + [0])
    data["battle_stats"]["max_combo"] = max(data["battle_stats"]["max_combo"], max_combo)
    
    # 更新必杀技使用次数
    ultimate_count = sum([h.rage for h in player_heroes]) // 100
    data["battle_stats"]["ultimate_used_count"] += ultimate_count
    
    # 更新承受伤害
    data["battle_stats"]["damage_taken"] += damage_taken
    
    # 检查称号解锁
    unlocked_titles = TitleSystem.check_titles(data["battle_stats"])
    if unlocked_titles:
        for title_id in unlocked_titles:
            if title_id not in data.get("unlocked_titles", []):
                if "unlocked_titles" not in data:
                    data["unlocked_titles"] = []
                data["unlocked_titles"].append(title_id)
                title_name = TitleSystem.TITLES[title_id]["name"]
                print(f"🎉 解锁新称号：{title_name}！")
    
    save()
    
    return unlocked_titles

def generate_battle_drops(player_level, enemy_count, battle_rating):
    """生成战斗掉落奖励"""
    from ASSET.game_data import ITEMS_DATABASE
    
    vip_bonus = get_vip_bonus()
    
    drops = []
    
    base_gold = 50 + player_level * 10
    gold_amount = int(base_gold * (1 + enemy_count * 0.3) * (1 + battle_rating * 0.1))
    
    # 应用VIP金币加成
    gold_bonus = float(vip_bonus["gold_bonus"].replace("%", "")) / 100
    gold_amount = int(gold_amount * (1 + gold_bonus))
    
    if gold_amount > 0:
        drops.append({"type": "gold", "amount": gold_amount})
    
    # 应用VIP掉落率加成
    drop_rate_bonus = float(vip_bonus["drop_rate"].replace("%", "")) / 100
    
    drop_chance = (0.3 + battle_rating * 0.1) * (1 + drop_rate_bonus)
    if random.random() < drop_chance:
        common_items = [name for name, info in ITEMS_DATABASE.items() if info.get("rarity") == "common"]
        if common_items:
            item_name = random.choice(common_items)
            drops.append({"type": "item", "name": item_name, "count": 1})
    
    rare_drop_chance = (0.1 + battle_rating * 0.05) * (1 + drop_rate_bonus)
    if random.random() < rare_drop_chance:
        rare_items = [name for name, info in ITEMS_DATABASE.items() if info.get("rarity") in ["rare", "epic"]]
        if rare_items:
            item_name = random.choice(rare_items)
            drops.append({"type": "item", "name": item_name, "count": 1})
    
    equipment_drop_chance = (0.15 + battle_rating * 0.05) * (1 + drop_rate_bonus)
    if random.random() < equipment_drop_chance:
        equip_names = list(EQUIPMENT_DATABASE.keys())
        if equip_names:
            equip_name = random.choice(equip_names)
            drops.append({"type": "equipment", "name": equip_name})
    
    return drops

def apply_drops(drops):
    """应用掉落奖励到玩家"""
    rewards = []
    for drop in drops:
        if drop["type"] == "gold":
            if "resources" not in data:
                data["resources"] = {}
            data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + drop["amount"]
            rewards.append(f"获得 {drop['amount']} 金元宝")
        elif drop["type"] == "item":
            if "inventory" not in data:
                data["inventory"] = {}
            data["inventory"][drop["name"]] = data["inventory"].get(drop["name"], 0) + drop["count"]
            rewards.append(f"获得物品: {drop['name']} x{drop['count']}")
        elif drop["type"] == "equipment":
            equip_info = EQUIPMENT_DATABASE.get(drop["name"], {})
            equip_type = equip_info.get("type", "weapon")
            if "equips" not in data:
                data["equips"] = {}
            if equip_type not in data["equips"]:
                data["equips"][equip_type] = []
            data["equips"][equip_type].append(drop["name"])
            rewards.append(f"获得装备: {drop['name']}")
    
    if rewards:
        save()
    return rewards

def calculate_battle_rating(player_heroes, enemy_heroes, turns_taken, damage_dealt, damage_taken):
    """计算战斗评价（1-5星）"""
    rating = 0
    
    if not player_heroes or not enemy_heroes:
        return 1
    
    # 基础分：胜利得1星
    if all(h.hp > 0 for h in player_heroes):
        rating += 1
    
    # 速度分：回合数少加分
    max_turns = len(enemy_heroes) * 3
    if turns_taken <= max_turns:
        rating += 1
    if turns_taken <= max_turns // 2:
        rating += 1
    
    # 生存分：受伤少加分
    total_hp = sum(h.max_hp for h in player_heroes)
    if total_hp > 0:
        survival_rate = (total_hp - damage_taken) / total_hp
        if survival_rate > 0.7:
            rating += 1
        if survival_rate > 0.9:
            rating += 1
    
    # 效率分：伤害输出
    total_enemy_hp = sum(h.max_hp for h in enemy_heroes)
    if damage_dealt >= total_enemy_hp:
        rating += 1
    
    return min(5, max(1, rating))

def get_rating_stars(rating):
    """获取评价星级图标"""
    return "★" * rating + "☆" * (5 - rating)

class BattleRewardEngine:
    """战斗奖励引擎 - 整合战斗评价、掉落生成、经验分配、奖励显示"""
    
    def __init__(self):
        self.rating = 0
        self.drops = []
        self.experience_rewards = []
        self.level_up_messages = []
        self.final_rewards = {}
    
    def calculate_rewards(self, player_heroes, enemy_heroes, turns_taken, damage_dealt, damage_taken, player_level):
        """计算所有奖励"""
        enemy_count = len(enemy_heroes)
        
        self.rating = calculate_battle_rating(player_heroes, enemy_heroes, turns_taken, damage_dealt, damage_taken)
        
        self.drops = generate_battle_drops(player_level, enemy_count, self.rating)
        
        # 获取VIP加成
        vip_bonus = get_vip_bonus()
        exp_bonus = float(vip_bonus["exp_bonus"].replace("%", "")) / 100
        
        # 计算经验：基于敌人等级、数量和评价
        enemy_level = enemy_heroes[0].level if enemy_heroes else 1
        base_exp = 50 * enemy_level * enemy_count * (1 + self.rating * 0.2)
        
        # 应用VIP经验加成
        base_exp = int(base_exp * (1 + exp_bonus))
        
        for hero in player_heroes:
            if hero.hp > 0:
                # 高级武将获得的经验更少（需要更多经验升级）
                level_penalty = max(0.3, 1 - (hero.level - 1) * 0.05)
                hero_exp = int(base_exp * level_penalty)
                level_messages = hero.add_experience(hero_exp)
                self.experience_rewards.append(f"{hero.name} 获得 {hero_exp} 经验")
                self.level_up_messages.extend(level_messages)
        
        self.final_rewards = self._merge_rewards()
        
        return self.final_rewards
    
    def _merge_rewards(self):
        """合并所有奖励到字典格式"""
        rewards = {}
        for drop in self.drops:
            if drop["type"] == "gold":
                rewards["金元宝"] = rewards.get("金元宝", 0) + drop["amount"]
            elif drop["type"] == "item":
                rewards[drop["name"]] = rewards.get(drop["name"], 0) + drop["count"]
            elif drop["type"] == "equipment":
                rewards[drop["name"]] = rewards.get(drop["name"], 0) + 1
        
        apply_drops(self.drops)
        
        return rewards
    
    def draw_reward_panel(self, screen, font_title, font_normal, font_small):
        """绘制奖励面板"""
        panel_width = 450
        panel_height = 350
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = 120
        
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (40, 40, 70, 220), (0, 0, panel_width, panel_height), border_radius=15)
        screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(screen, COLORS["accent_gold"], 
                       (panel_x, panel_y, panel_width, panel_height), 2, border_radius=15)
        
        title_surf = font_title.render("🎉 战斗胜利！", True, COLORS["accent_green"])
        screen.blit(title_surf, (panel_x + panel_width // 2 - title_surf.get_width() // 2, panel_y + 15))
        
        rating_text = f"评价: {get_rating_stars(self.rating)} ({self.rating}/5)"
        rating_surf = font_normal.render(rating_text, True, COLORS["accent_gold"])
        screen.blit(rating_surf, (panel_x + panel_width // 2 - rating_surf.get_width() // 2, panel_y + 55))
        
        y_offset = panel_y + 95
        
        if self.level_up_messages:
            level_title = font_small.render("🎊 升级提示", True, COLORS["accent_red"])
            screen.blit(level_title, (panel_x + 20, y_offset))
            y_offset += 25
            for msg in self.level_up_messages[:3]:
                msg_surf = font_small.render(msg, True, COLORS["text_white"])
                screen.blit(msg_surf, (panel_x + 30, y_offset))
                y_offset += 25
        
        reward_title = font_small.render("💎 获得奖励", True, COLORS["accent_gold"])
        screen.blit(reward_title, (panel_x + 20, y_offset))
        y_offset += 25
        
        for res, amt in self.final_rewards.items():
            icon = {"水": "💧", "煤炭": "⚫", "木头": "🪵", "食物": "🍞", "金元宝": "💰", 
                    "普通子弹": "🔫", "高级子弹": "🔫🔫", "稀有子弹": "🔫🔥"}.get(res, "📦")
            reward_text = font_small.render(f"{icon} {res} × {amt}", True, COLORS["text_white"])
            screen.blit(reward_text, (panel_x + 30, y_offset))
            y_offset += 25
        
        if self.experience_rewards:
            exp_title = font_small.render("📚 经验获取", True, COLORS["accent_blue"])
            screen.blit(exp_title, (panel_x + 20, y_offset))
            y_offset += 25
            for exp_msg in self.experience_rewards[:3]:
                exp_surf = font_small.render(exp_msg, True, COLORS["text_white"])
                screen.blit(exp_surf, (panel_x + 30, y_offset))
            y_offset += 20

class ElementSystem:
    """元素系统 - 整合元素颜色、克制关系、共鸣伤害、弱点加成"""
    
    ELEMENT_COLORS = {
        "火": (255, 100, 100),
        "水": (100, 150, 255),
        "土": (150, 100, 50),
        "风": (100, 200, 100),
        "雷": (200, 100, 255)
    }
    
    ELEMENT_COUNTER = {
        "火": {"target": "风", "text": "🔥克制🌿", "damage_bonus": 0.3},
        "水": {"target": "火", "text": "💧克制🔥", "damage_bonus": 0.3},
        "土": {"target": "水", "text": "🪨克制💧", "damage_bonus": 0.3},
        "风": {"target": "土", "text": "🌿克制🪨", "damage_bonus": 0.3},
        "雷": {"target": "水", "text": "⚡克制💧", "damage_bonus": 0.3}
    }
    
    ELEMENT_SYNERGY_EFFECTS = {
        "火_风": {"type": "wildfire", "aoe": True, "damage": 20},
        "水_火": {"type": "steam", "damage": 30},
        "土_水": {"type": "mud", "slow": 2},
        "风_土": {"type": "dust", "blind": 1},
        "雷_水": {"type": "thunder", "stun": 1},
        "火_水": {"type": "steam", "damage": 30},
        "火_土": {"type": "lava", "burn_turns": 3, "burn_damage": 10},
        "水_土": {"type": "mud", "slow": 2},
        "水_风": {"type": "frost", "slow": 1},
        "雷_土": {"type": "earthquake", "aoe": True, "damage": 15},
        "雷_风": {"type": "storm", "aoe": True, "damage": 25},
        "雷_火": {"type": "explosion", "aoe": True, "damage": 35}
    }
    
    ELEMENT_WEAKNESS_BONUS = {
        "火": {"weak_to": "水", "bonus": 1.5},
        "水": {"weak_to": "土", "bonus": 1.5},
        "土": {"weak_to": "风", "bonus": 1.5},
        "风": {"weak_to": "火", "bonus": 1.5},
        "雷": {"weak_to": "土", "bonus": 1.5}
    }
    
    @classmethod
    def get_color(cls, element, default=(255, 215, 0)):
        """获取元素颜色"""
        return cls.ELEMENT_COLORS.get(element, default)
    
    @classmethod
    def is_counter(cls, attacker_element, defender_element):
        """检查是否克制"""
        if attacker_element in cls.ELEMENT_COUNTER:
            return cls.ELEMENT_COUNTER[attacker_element]["target"] == defender_element
        return False
    
    @classmethod
    def get_counter_bonus(cls, attacker_element, defender_element):
        """获取克制伤害加成"""
        if cls.is_counter(attacker_element, defender_element):
            return cls.ELEMENT_COUNTER[attacker_element]["damage_bonus"]
        return 0.0
    
    @classmethod
    def get_counter_text(cls, attacker_element, defender_element):
        """获取克制显示文本"""
        if cls.is_counter(attacker_element, defender_element):
            return cls.ELEMENT_COUNTER[attacker_element]["text"]
        return None
    
    @classmethod
    def get_synergy_effect(cls, attacker_element, defender_element):
        """获取元素共鸣效果"""
        key = f"{attacker_element}_{defender_element}"
        return cls.ELEMENT_SYNERGY_EFFECTS.get(key)
    
    @classmethod
    def get_weakness_bonus(cls, attacker_element, defender_element):
        """获取弱点伤害加成"""
        if defender_element in cls.ELEMENT_WEAKNESS_BONUS:
            weakness = cls.ELEMENT_WEAKNESS_BONUS[defender_element]
            if attacker_element == weakness["weak_to"]:
                return weakness["bonus"]
        return 1.0
    
    @classmethod
    def get_total_damage_modifier(cls, attacker_element, defender_element):
        """获取总伤害修正（克制+弱点）"""
        modifier = 1.0
        modifier += cls.get_counter_bonus(attacker_element, defender_element)
        modifier *= cls.get_weakness_bonus(attacker_element, defender_element)
        return modifier
    
    @classmethod
    def draw_element_counter(cls, surface, attacker_element, defender_element, x, y, font):
        """绘制元素克制关系显示"""
        text = cls.get_counter_text(attacker_element, defender_element)
        if text:
            text_surf = font.render(text, True, COLORS["accent_gold"])
            text_rect = text_surf.get_rect(center=(x, y))
            surface.blit(text_surf, text_rect)
            return True
        return False
    
    @classmethod
    def apply_synergy_effects(cls, attacker, target):
        """应用元素共鸣效果到目标"""
        synergy = cls.get_synergy_effect(attacker.element, target.element)
        if not synergy:
            return None
        
        messages = []
        effect_type = synergy.get("type")
        
        if effect_type == "steam":
            extra_damage = synergy["damage"]
            target.hp = max(0, target.hp - extra_damage)
            messages.append(f"💨 蒸汽效果！{target.name}受到{extra_damage}点额外伤害")
        elif effect_type == "wildfire" and synergy.get("aoe"):
            messages.append(f"🔥 野火蔓延！")
        elif effect_type == "lava":
            target.burn_turns = synergy.get("burn_turns", 3)
            target.burn_damage = synergy.get("burn_damage", 10)
            messages.append(f"🌋 熔岩灼烧！{target.name}被点燃")
        elif effect_type == "frost":
            target.slow_turns = synergy.get("slow", 1)
            target.add_debuff("freeze", 1)
            messages.append(f"❄️ 霜冻效果！{target.name}被冻结")
        elif effect_type == "thunder":
            target.add_debuff("stun", 1)
            messages.append(f"⚡ 雷击效果！{target.name}被眩晕")
        elif effect_type == "poison":
            target.add_debuff("poison", 3, 15)
            messages.append(f"☠️ 毒雾效果！{target.name}中毒")
        elif effect_type == "mud":
            target.slow_turns = synergy.get("slow", 2)
            messages.append(f"🪨 泥浆效果！{target.name}被减速")
        
        return messages

class AITacticalDecision:
    """AI战术决策系统 - 评估威胁、选择目标、选择行动"""
    
    @classmethod
    def evaluate_threats(cls, hero, enemies):
        """评估敌人威胁等级"""
        threats = []
        for enemy in enemies:
            if enemy.hp <= 0:
                continue
            
            threat_score = 0
            
            threat_score += enemy.attack * (1 - enemy.hp / enemy.max_hp)
            
            threat_score += enemy.speed * 0.5
            
            if enemy.can_use_ultimate():
                threat_score += 100
            
            if ElementSystem.is_counter(enemy.element, hero.element):
                threat_score += 50
            
            threat_score += len(enemy.minions) * 20
            
            threats.append({"enemy": enemy, "score": threat_score})
        
        threats.sort(key=lambda x: x["score"], reverse=True)
        return threats
    
    @classmethod
    def choose_target(cls, hero, allies, enemies):
        """选择攻击目标"""
        alive_enemies = [e for e in enemies if e.hp > 0]
        if not alive_enemies:
            return None
        
        threats = cls.evaluate_threats(hero, alive_enemies)
        
        if len(alive_enemies) >= 2:
            low_hp_enemy = min(alive_enemies, key=lambda x: x.hp / x.max_hp)
            if low_hp_enemy.hp / low_hp_enemy.max_hp < 0.3:
                return low_hp_enemy
        
        best_counter = None
        counter_bonus = 0
        for enemy in alive_enemies:
            bonus = ElementSystem.get_counter_bonus(hero.element, enemy.element)
            if bonus > counter_bonus:
                counter_bonus = bonus
                best_counter = enemy
        
        if best_counter and counter_bonus > 0:
            return best_counter
        
        if threats:
            return threats[0]["enemy"]
        
        return alive_enemies[0]
    
    @classmethod
    def choose_action(cls, hero, allies, enemies):
        """选择行动类型（普通攻击/必杀技/战术技能/防御）"""
        alive_allies = [a for a in allies if a.hp > 0 and a != hero]
        alive_enemies = [e for e in enemies if e.hp > 0]
        
        if not alive_enemies:
            return "idle", None
        
        if hero.can_use_tactical():
            tactical_chance = 0.3
            if len(alive_enemies) >= 3:
                tactical_chance = 0.5
            if random.random() < tactical_chance:
                return "tactical", cls.choose_target(hero, allies, alive_enemies)
        
        if hero.can_use_ultimate():
            ultimate_threshold = 70
            if hero.rage >= hero.ultimate_skill["rage_cost"] + 10:
                return "ultimate", cls.choose_target(hero, allies, alive_enemies)
            
            high_threat = any(t["score"] > 150 for t in cls.evaluate_threats(hero, alive_enemies))
            if high_threat:
                return "ultimate", cls.choose_target(hero, allies, alive_enemies)
        
        if hero.rage >= 80:
            return "ultimate", cls.choose_target(hero, allies, alive_enemies)
        
        avg_hp = sum(a.hp / a.max_hp for a in alive_allies) / len(alive_allies) if alive_allies else 1.0
        if avg_hp < 0.4:
            return "defend", None
        
        return "attack", cls.choose_target(hero, allies, alive_enemies)

class TerrainSystem:
    """地形系统 - 山地/河流/森林/平原地形修正"""
    
    TERRAIN_TYPES = {
        "平原": {
            "name": "平原",
            "description": "地势平坦，适合骑兵冲锋",
            "attack_modifier": 1.1,
            "defense_modifier": 0.9,
            "speed_modifier": 1.15,
            "crit_modifier": 1.0,
            "element_bonus": None
        },
        "山地": {
            "name": "山地",
            "description": "地势险峻，易守难攻",
            "attack_modifier": 0.9,
            "defense_modifier": 1.2,
            "speed_modifier": 0.85,
            "crit_modifier": 0.95,
            "element_bonus": "土"
        },
        "河流": {
            "name": "河流",
            "description": "水流湍急，影响移动",
            "attack_modifier": 1.0,
            "defense_modifier": 0.95,
            "speed_modifier": 0.75,
            "crit_modifier": 1.05,
            "element_bonus": "水"
        },
        "森林": {
            "name": "森林",
            "description": "树木茂密，隐蔽性强",
            "attack_modifier": 1.0,
            "defense_modifier": 1.1,
            "speed_modifier": 0.9,
            "crit_modifier": 1.1,
            "element_bonus": "风"
        },
        "雪地": {
            "name": "雪地",
            "description": "天寒地冻，行动迟缓",
            "attack_modifier": 0.95,
            "defense_modifier": 1.05,
            "speed_modifier": 0.7,
            "crit_modifier": 0.9,
            "element_bonus": "水"
        },
        "沙漠": {
            "name": "沙漠",
            "description": "烈日炎炎，消耗体力",
            "attack_modifier": 1.05,
            "defense_modifier": 0.9,
            "speed_modifier": 1.0,
            "crit_modifier": 1.15,
            "element_bonus": "火"
        }
    }
    
    @classmethod
    def get_random_terrain(cls):
        """获取随机地形"""
        return random.choice(list(cls.TERRAIN_TYPES.keys()))
    
    @classmethod
    def get_terrain_info(cls, terrain_name):
        """获取地形信息"""
        return cls.TERRAIN_TYPES.get(terrain_name, cls.TERRAIN_TYPES["平原"])
    
    @classmethod
    def get_attack_modifier(cls, terrain_name, hero_element=None):
        """获取攻击修正"""
        terrain = cls.get_terrain_info(terrain_name)
        modifier = terrain["attack_modifier"]
        if terrain["element_bonus"] and hero_element == terrain["element_bonus"]:
            modifier *= 1.15
        return modifier
    
    @classmethod
    def get_defense_modifier(cls, terrain_name, hero_element=None):
        """获取防御修正"""
        terrain = cls.get_terrain_info(terrain_name)
        modifier = terrain["defense_modifier"]
        if terrain["element_bonus"] and hero_element == terrain["element_bonus"]:
            modifier *= 1.15
        return modifier
    
    @classmethod
    def get_speed_modifier(cls, terrain_name, hero_element=None):
        """获取速度修正"""
        terrain = cls.get_terrain_info(terrain_name)
        modifier = terrain["speed_modifier"]
        if terrain["element_bonus"] and hero_element == terrain["element_bonus"]:
            modifier *= 1.1
        return modifier
    
    @classmethod
    def get_crit_modifier(cls, terrain_name):
        """获取暴击修正"""
        terrain = cls.get_terrain_info(terrain_name)
        return terrain["crit_modifier"]

class BattleLog:
    """战斗日志系统"""
    
    LOG_LEVELS = {
        "info": {"color": (200, 200, 200), "prefix": "[INFO]"},
        "damage": {"color": (255, 100, 100), "prefix": "[伤害]"},
        "heal": {"color": (100, 255, 100), "prefix": "[治疗]"},
        "buff": {"color": (100, 200, 255), "prefix": "[增益]"},
        "debuff": {"color": (255, 150, 50), "prefix": "[减益]"},
        "critical": {"color": (255, 200, 0), "prefix": "[暴击]"},
        "ultimate": {"color": (255, 100, 255), "prefix": "[必杀]"},
        "tactical": {"color": (150, 200, 255), "prefix": "[战术]"},
        "system": {"color": (100, 150, 200), "prefix": "[系统]"},
        "achievement": {"color": (255, 215, 0), "prefix": "[成就]"}
    }
    
    def __init__(self):
        self.logs = []
        self.max_logs = 100
    
    def add_log(self, message, level="info"):
        """添加日志"""
        log_entry = {
            "message": message,
            "level": level,
            "timestamp": pygame.time.get_ticks()
        }
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
    
    def get_logs(self, count=10):
        """获取最近的日志"""
        return self.logs[-count:]
    
    def get_log_color(self, level):
        """获取日志颜色"""
        return self.LOG_LEVELS.get(level, self.LOG_LEVELS["info"])["color"]
    
    def get_log_prefix(self, level):
        """获取日志前缀"""
        return self.LOG_LEVELS.get(level, self.LOG_LEVELS["info"])["prefix"]
    
    def clear(self):
        """清空日志"""
        self.logs = []
    
    def draw_logs(self, surface, x, y, width, height, font, count=10):
        """绘制战斗日志"""
        logs_to_draw = self.get_logs(count)
        log_height = height // count
        
        for i, log in enumerate(logs_to_draw):
            color = self.get_log_color(log["level"])
            prefix = self.get_log_prefix(log["level"])
            
            text = f"{prefix} {log['message']}"
            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect()
            text_rect.x = x + 10
            text_rect.y = y + i * log_height
            
            if text_rect.width > width - 20:
                text_surf = font.render(text[:40] + "...", True, color)
            
            surface.blit(text_surf, text_rect)

class TroopSystem:
    """兵种系统"""
    
    TROOP_TYPES = {
        "infantry": {
            "name": "步兵",
            "icon": "🛡️",
            "base_stats": {"attack": 80, "defense": 120, "speed": 60, "hp": 1000},
            "advantages": ["cavalry"],
            "disadvantages": ["archer"],
            "skills": ["防御阵型", "盾墙"]
        },
        "cavalry": {
            "name": "骑兵",
            "icon": "🐎",
            "base_stats": {"attack": 120, "defense": 80, "speed": 150, "hp": 900},
            "advantages": ["archer", "mage"],
            "disadvantages": ["infantry"],
            "skills": ["冲锋", "践踏"]
        },
        "archer": {
            "name": "弓兵",
            "icon": "🏹",
            "base_stats": {"attack": 150, "defense": 50, "speed": 80, "hp": 700},
            "advantages": ["mage"],
            "disadvantages": ["cavalry"],
            "skills": ["穿透射击", "箭雨"]
        },
        "mage": {
            "name": "策士",
            "icon": "📜",
            "base_stats": {"attack": 100, "defense": 40, "speed": 70, "hp": 600},
            "advantages": ["infantry"],
            "disadvantages": ["cavalry", "archer"],
            "skills": ["法术攻击", "治疗"]
        }
    }
    
    TROOP_ADVANTAGE_BONUS = 0.3
    TROOP_DISADVANTAGE_PENALTY = 0.2
    
    @classmethod
    def get_troop_bonus(cls, attacker_troop, defender_troop):
        """获取兵种克制加成"""
        if attacker_troop in cls.TROOP_TYPES and defender_troop in cls.TROOP_TYPES:
            attacker_data = cls.TROOP_TYPES[attacker_troop]
            if defender_troop in attacker_data["advantages"]:
                return cls.TROOP_ADVANTAGE_BONUS
            if defender_troop in attacker_data["disadvantages"]:
                return -cls.TROOP_DISADVANTAGE_PENALTY
        return 0

class TitleSystem:
    """称号系统"""
    
    TITLES = {
        "武圣": {
            "description": "天下无敌的武将",
            "requirements": {"total_kills": 1000},
            "effects": {"attack": 100, "crit_rate": 0.15},
            "rarity": "legendary"
        },
        "智圣": {
            "description": "智慧无双的谋士",
            "requirements": {"skill_kills": 500},
            "effects": {"skill_damage": 0.5, "mp_regen": 20},
            "rarity": "legendary"
        },
        "常胜将军": {
            "description": "从未败北的将军",
            "requirements": {"win_streak": 50},
            "effects": {"attack": 50, "defense": 50, "hp": 500},
            "rarity": "epic"
        },
        "万人敌": {
            "description": "一人可敌万人",
            "requirements": {"single_battle_kills": 10},
            "effects": {"attack": 80, "crit_damage": 0.4},
            "rarity": "epic"
        },
        "神医": {
            "description": "妙手回春的医者",
            "requirements": {"total_heal": 10000},
            "effects": {"heal_bonus": 0.5, "hp_regen": 30},
            "rarity": "epic"
        },
        "破阵大师": {
            "description": "精通各种阵型",
            "requirements": {"formation_kills": 300},
            "effects": {"attack": 40, "defense": 40, "speed": 30},
            "rarity": "rare"
        },
        "连击王": {
            "description": "连击无人能敌",
            "requirements": {"max_combo": 50},
            "effects": {"attack": 30, "crit_rate": 0.1},
            "rarity": "rare"
        },
        "防御大师": {
            "description": "铜墙铁壁般的防御",
            "requirements": {"damage_taken": 50000},
            "effects": {"defense": 100, "damage_reduction": 0.2},
            "rarity": "rare"
        },
        "新手": {
            "description": "初出茅庐的战士",
            "requirements": {"battles_won": 1},
            "effects": {"attack": 10, "defense": 10},
            "rarity": "common"
        },
        "老兵": {
            "description": "身经百战的老兵",
            "requirements": {"battles_won": 50},
            "effects": {"attack": 30, "defense": 30, "hp": 200},
            "rarity": "common"
        },
        "名将": {
            "description": "威震一方的名将",
            "requirements": {"battles_won": 200},
            "effects": {"attack": 60, "defense": 60, "speed": 30},
            "rarity": "uncommon"
        },
        "传说": {
            "description": "成为传说中的人物",
            "requirements": {"total_score": 100000},
            "effects": {"attack": 150, "defense": 150, "hp": 1000, "speed": 50},
            "rarity": "legendary"
        }
    }
    
    RARITY_COLORS = {
        "common": (200, 200, 200),
        "uncommon": (100, 255, 100),
        "rare": (100, 150, 255),
        "epic": (180, 100, 255),
        "legendary": (255, 200, 50)
    }
    
    @classmethod
    def check_titles(cls, player_stats):
        """检查可获得的称号"""
        unlocked = []
        for title_id, title_data in cls.TITLES.items():
            requirements = title_data["requirements"]
            meets_all = True
            for req, value in requirements.items():
                if player_stats.get(req, 0) < value:
                    meets_all = False
                    break
            if meets_all:
                unlocked.append(title_id)
        return unlocked
    
    @classmethod
    def apply_title_effects(cls, hero, title_id):
        """应用称号效果"""
        if title_id not in cls.TITLES:
            return
        
        effects = cls.TITLES[title_id]["effects"]
        for stat, value in effects.items():
            if hasattr(hero, stat):
                current = getattr(hero, stat)
                setattr(hero, stat, current + value)
        
        hero.title = title_id
        hero.title_description = cls.TITLES[title_id]["description"]

class HeroSpecialtySystem:
    """武将专精系统 - 每个武将可以选择一个专精方向"""
    
    SPECIALTY_TYPES = {
        "warrior": {
            "name": "猛将",
            "icon": "⚔️",
            "description": "擅长近身战斗，攻击力强大",
            "effects": {
                "attack": 100,
                "crit_rate": 0.1,
                "crit_damage": 0.2
            },
            "skills": ["狂暴打击", "破甲攻击"]
        },
        "tank": {
            "name": "盾将",
            "icon": "🛡️",
            "description": "擅长防御，保护队友",
            "effects": {
                "defense": 100,
                "hp": 500,
                "damage_reduction": 0.15
            },
            "skills": ["铁壁", "嘲讽"]
        },
        "mage": {
            "name": "策士",
            "icon": "📜",
            "description": "擅长法术攻击，技能伤害高",
            "effects": {
                "skill_damage": 0.3,
                "mp": 200,
                "crit_rate": 0.08
            },
            "skills": ["法术精通", "元素强化"]
        },
        "healer": {
            "name": "医士",
            "icon": "💊",
            "description": "擅长治疗，支援队友",
            "effects": {
                "heal_bonus": 0.3,
                "hp": 300,
                "defense": 50
            },
            "skills": ["妙手回春", "群体治疗"]
        },
        "archer": {
            "name": "弓手",
            "icon": "🏹",
            "description": "擅长远程攻击，速度快",
            "effects": {
                "attack": 80,
                "speed": 50,
                "crit_rate": 0.12
            },
            "skills": ["穿透射击", "致命一击"]
        },
        "assassin": {
            "name": "刺客",
            "icon": "🗡️",
            "description": "擅长暴击和闪避，一击致命",
            "effects": {
                "crit_rate": 0.15,
                "crit_damage": 0.3,
                "dodge_bonus": 0.1
            },
            "skills": ["潜行", "背刺"]
        },
        "strategist": {
            "name": "军师",
            "icon": "🧠",
            "description": "擅长策略，削弱敌人",
            "effects": {
                "skill_damage": 0.2,
                "defense": 30,
                "speed": 30
            },
            "skills": ["谋略", "计策"]
        },
        "support": {
            "name": "辅助",
            "icon": "✨",
            "description": "擅长增益，强化队友",
            "effects": {
                "heal_bonus": 0.2,
                "mp": 150,
                "speed": 20
            },
            "skills": ["鼓舞", "祝福"]
        }
    }
    
    SPECIALTY_MASTERY_LEVELS = {
        1: {"name": "入门", "multiplier": 1.0, "cost": {"gold": 1000, "mastery_points": 1}},
        2: {"name": "熟练", "multiplier": 1.2, "cost": {"gold": 3000, "mastery_points": 3}},
        3: {"name": "精通", "multiplier": 1.5, "cost": {"gold": 8000, "mastery_points": 6}},
        4: {"name": "大师", "multiplier": 2.0, "cost": {"gold": 20000, "mastery_points": 10}},
        5: {"name": "宗师", "multiplier": 3.0, "cost": {"gold": 50000, "mastery_points": 20}}
    }
    
    @classmethod
    def get_specialty(cls, specialty_id):
        """获取专精数据"""
        return cls.SPECIALTY_TYPES.get(specialty_id)
    
    @classmethod
    def apply_specialty(cls, hero, specialty_id, mastery_level=1):
        """应用专精效果"""
        specialty = cls.get_specialty(specialty_id)
        if not specialty:
            return False, "专精类型不存在"
        
        multiplier = cls.SPECIALTY_MASTERY_LEVELS.get(mastery_level, {}).get("multiplier", 1.0)
        
        for stat, value in specialty["effects"].items():
            if hasattr(hero, stat):
                current = getattr(hero, stat)
                setattr(hero, stat, current + int(value * multiplier))
        
        hero.specialty = specialty_id
        hero.specialty_mastery = mastery_level
        hero.specialty_name = specialty["name"]
        
        return True, f"成功选择{specialty['name']}专精 Lv.{mastery_level}"
    
    @classmethod
    def upgrade_mastery(cls, hero, gold, mastery_points):
        """升级专精等级"""
        if not hasattr(hero, 'specialty') or not hero.specialty:
            return False, "请先选择专精"
        
        current_level = hero.specialty_mastery if hasattr(hero, 'specialty_mastery') else 1
        
        if current_level >= 5:
            return False, "已达到最高专精等级"
        
        upgrade_cost = cls.SPECIALTY_MASTERY_LEVELS.get(current_level + 1, {}).get("cost", {})
        if gold < upgrade_cost.get("gold", 0):
            return False, "金元宝不足"
        if mastery_points < upgrade_cost.get("mastery_points", 0):
            return False, "专精点数不足"
        
        new_level = current_level + 1
        hero.specialty_mastery = new_level
        
        specialty = cls.get_specialty(hero.specialty)
        multiplier = cls.SPECIALTY_MASTERY_LEVELS.get(new_level, {}).get("multiplier", 1.0)
        
        for stat, value in specialty["effects"].items():
            if hasattr(hero, stat):
                base_value = getattr(hero, stat)
                prev_multiplier = cls.SPECIALTY_MASTERY_LEVELS.get(current_level, {}).get("multiplier", 1.0)
                diff = int(value * (multiplier - prev_multiplier))
                setattr(hero, stat, base_value + diff)
        
        save()
        return True, f"专精升级到{cls.SPECIALTY_MASTERY_LEVELS[new_level]['name']}"

class TalentSystem:
    """战斗天赋系统 - 每级获得天赋点，解锁战斗被动效果"""
    
    TALENT_TREES = {
        "offense": {
            "name": "攻击系",
            "icon": "⚔️",
            "talents": [
                {"id": "power_strike", "name": "力量打击", "level": 1, "description": "攻击力+5%", "effect": {"attack_bonus": 0.05}},
                {"id": "critical_eye", "name": "鹰眼", "level": 2, "description": "暴击率+3%", "effect": {"crit_rate": 0.03}},
                {"id": "piercing", "name": "穿透", "level": 3, "description": "无视敌人10%防御", "effect": {"armor_penetration": 0.1}},
                {"id": "fury", "name": "狂怒", "level": 4, "description": "生命值低于50%时攻击力+20%", "effect": {"low_hp_boost": 0.2}},
                {"id": "execute", "name": "处决", "level": 5, "description": "对生命值低于30%的敌人造成额外50%伤害", "effect": {"execute_bonus": 0.5}},
                {"id": "overkill", "name": "屠戮", "level": 6, "description": "击杀敌人后攻击力提升10%，持续2回合", "effect": {"kill_boost": 0.1}},
                {"id": "god_of_war", "name": "战神", "level": 7, "description": "攻击力+20%，暴击伤害+50%", "effect": {"attack_bonus": 0.2, "crit_damage": 0.5}}
            ]
        },
        "defense": {
            "name": "防御系",
            "icon": "🛡️",
            "talents": [
                {"id": "iron_skin", "name": "铁皮", "level": 1, "description": "防御力+5%", "effect": {"defense_bonus": 0.05}},
                {"id": "regeneration", "name": "再生", "level": 2, "description": "每回合恢复2%最大生命值", "effect": {"hp_regen": 0.02}},
                {"id": "damage_shield", "name": "护盾", "level": 3, "description": "受到攻击时获得等同于攻击力10%的护盾", "effect": {"damage_shield": 0.1}},
                {"id": "counter", "name": "反击", "level": 4, "description": "受到攻击时有10%概率反击", "effect": {"counter_rate": 0.1}},
                {"id": "fortress", "name": "堡垒", "level": 5, "description": "防御力+15%，受到暴击伤害减少50%", "effect": {"defense_bonus": 0.15, "crit_damage_reduction": 0.5}},
                {"id": "immortal", "name": "不死", "level": 6, "description": "受到致命伤害时有20%概率不死并恢复30%生命", "effect": {"immortal_chance": 0.2, "immortal_heal": 0.3}},
                {"id": "impervious", "name": "金刚不坏", "level": 7, "description": "伤害减免+30%，每回合恢复5%生命", "effect": {"damage_reduction": 0.3, "hp_regen": 0.05}}
            ]
        },
        "support": {
            "name": "支援系",
            "icon": "✨",
            "talents": [
                {"id": "healer", "name": "医者", "level": 1, "description": "治疗效果+10%", "effect": {"heal_bonus": 0.1}},
                {"id": "mana_master", "name": "法力大师", "level": 2, "description": "技能伤害+5%", "effect": {"skill_damage": 0.05}},
                {"id": "purify", "name": "净化", "level": 3, "description": "每回合有15%概率清除一个负面状态", "effect": {"purify_chance": 0.15}},
                {"id": "blessing", "name": "祝福", "level": 4, "description": "友方全体攻击力+5%", "effect": {"party_attack_bonus": 0.05}},
                {"id": "resurrection", "name": "复活", "level": 5, "description": "战斗中死亡时有10%概率复活并恢复50%生命", "effect": {"resurrect_chance": 0.1, "resurrect_heal": 0.5}},
                {"id": "divine_favor", "name": "神佑", "level": 6, "description": "友方全体受到伤害减少10%", "effect": {"party_damage_reduction": 0.1}},
                {"id": "savior", "name": "救世主", "level": 7, "description": "治疗效果+50%，技能伤害+20%", "effect": {"heal_bonus": 0.5, "skill_damage": 0.2}}
            ]
        },
        "agility": {
            "name": "敏捷系",
            "icon": "🐆",
            "talents": [
                {"id": "swift", "name": "迅捷", "level": 1, "description": "速度+5%", "effect": {"speed_bonus": 0.05}},
                {"id": "dodge_master", "name": "闪避大师", "level": 2, "description": "闪避率+3%", "effect": {"dodge_bonus": 0.03}},
                {"id": "parry", "name": "格挡", "level": 3, "description": "有10%概率格挡50%伤害", "effect": {"parry_rate": 0.1, "parry_reduction": 0.5}},
                {"id": "backstab", "name": "背刺", "level": 4, "description": "攻击敌人背后时伤害+30%", "effect": {"backstab_bonus": 0.3}},
                {"id": "shadow_step", "name": "影步", "level": 5, "description": "闪避后下一次攻击必定暴击", "effect": {"dodge_crit": True}},
                {"id": "wind_walk", "name": "风行", "level": 6, "description": "速度+20%，闪避率+10%", "effect": {"speed_bonus": 0.2, "dodge_bonus": 0.1}},
                {"id": "ghost", "name": "鬼魅", "level": 7, "description": "闪避率+20%，暴击率+15%", "effect": {"dodge_bonus": 0.2, "crit_rate": 0.15}}
            ]
        }
    }
    
    @classmethod
    def get_talent_tree(cls, tree_id):
        """获取天赋树"""
        return cls.TALENT_TREES.get(tree_id)
    
    @classmethod
    def unlock_talent(cls, hero, tree_id, talent_id, talent_points):
        """解锁天赋"""
        tree = cls.get_talent_tree(tree_id)
        if not tree:
            return False, "天赋树不存在"
        
        talent = None
        for t in tree["talents"]:
            if t["id"] == talent_id:
                talent = t
                break
        
        if not talent:
            return False, "天赋不存在"
        
        if talent_points < talent["level"]:
            return False, "天赋点数不足"
        
        if "talents" not in hero.__dict__:
            hero.talents = []
        
        if talent_id in hero.talents:
            return False, "天赋已解锁"
        
        hero.talents.append(talent_id)
        
        for stat, value in talent["effect"].items():
            if stat not in hero.bond_bonuses:
                hero.bond_bonuses[stat] = 0
            hero.bond_bonuses[stat] += value
        
        save()
        return True, f"成功解锁天赋：{talent['name']}"

class HeroRebirthSystem:
    """武将转生系统 - 消耗材料将武将转化为更高品质"""
    
    REBIRTH_CONFIG = {
        "rare": {
            "name": "稀有转生",
            "required_quality": "rare",
            "target_quality": "epic",
            "cost": {"gold": 5000, "rebirth_stones": 10, "hero_fragments": 50},
            "stats_multiplier": 1.5,
            "description": "将稀有武将转生为史诗武将"
        },
        "epic": {
            "name": "史诗转生",
            "required_quality": "epic",
            "target_quality": "legendary",
            "cost": {"gold": 20000, "rebirth_stones": 30, "hero_fragments": 150},
            "stats_multiplier": 2.0,
            "description": "将史诗武将转生为传说武将"
        },
        "legendary": {
            "name": "传说转生",
            "required_quality": "legendary",
            "target_quality": "mythic",
            "cost": {"gold": 50000, "rebirth_stones": 100, "hero_fragments": 500},
            "stats_multiplier": 3.0,
            "description": "将传说武将转生为神话武将"
        },
        "mythic": {
            "name": "神话转生",
            "required_quality": "mythic",
            "target_quality": "transcendent",
            "cost": {"gold": 100000, "rebirth_stones": 300, "hero_fragments": 1000},
            "stats_multiplier": 4.0,
            "description": "将神话武将转生为超越武将"
        }
    }
    
    QUALITY_ORDER = ["common", "good", "rare", "epic", "legendary", "mythic", "transcendent"]
    
    QUALITY_NAMES = {
        "common": "普通",
        "good": "优秀",
        "rare": "稀有",
        "epic": "史诗",
        "legendary": "传说",
        "mythic": "神话",
        "transcendent": "超越"
    }
    
    @classmethod
    def can_rebirth(cls, hero, gold, rebirth_stones, hero_fragments):
        """检查是否可以转生"""
        quality = hero.quality if hasattr(hero, 'quality') else "common"
        
        if quality not in cls.REBIRTH_CONFIG:
            return False, f"{cls.QUALITY_NAMES.get(quality, quality)}武将无法继续转生"
        
        config = cls.REBIRTH_CONFIG[quality]
        
        if gold < config["cost"]["gold"]:
            return False, f"金元宝不足，需要{config['cost']['gold']}"
        if rebirth_stones < config["cost"]["rebirth_stones"]:
            return False, f"转生石不足，需要{config['cost']['rebirth_stones']}"
        if hero_fragments < config["cost"]["hero_fragments"]:
            return False, f"武将碎片不足，需要{config['cost']['hero_fragments']}"
        
        return True, f"可以进行{config['name']}"
    
    @classmethod
    def rebirth(cls, hero, gold, rebirth_stones, hero_fragments):
        """执行转生"""
        quality = hero.quality if hasattr(hero, 'quality') else "common"
        
        success, msg = cls.can_rebirth(hero, gold, rebirth_stones, hero_fragments)
        if not success:
            return False, msg
        
        config = cls.REBIRTH_CONFIG[quality]
        target_quality = config["target_quality"]
        
        multiplier = config["stats_multiplier"]
        base_multiplier = cls._get_quality_multiplier(quality)
        new_multiplier = cls._get_quality_multiplier(target_quality)
        actual_multiplier = new_multiplier / base_multiplier
        
        stats = ["attack", "defense", "hp", "speed", "crit_rate", "crit_damage", "skill_damage"]
        for stat in stats:
            if hasattr(hero, stat):
                original_value = getattr(hero, stat)
                new_value = int(original_value * actual_multiplier)
                setattr(hero, stat, new_value)
        
        hero.quality = target_quality
        hero.rebirth_count = hero.rebirth_count + 1 if hasattr(hero, 'rebirth_count') else 1
        
        save()
        return True, f"{hero.name}成功转生为{cls.QUALITY_NAMES[target_quality]}品质！"
    
    @classmethod
    def _get_quality_multiplier(cls, quality):
        """获取品质属性倍率"""
        multipliers = {
            "common": 1.0,
            "good": 1.2,
            "rare": 1.5,
            "epic": 2.0,
            "legendary": 3.0,
            "mythic": 4.0,
            "transcendent": 5.0
        }
        return multipliers.get(quality, 1.0)
    
    @classmethod
    def get_rebirth_cost(cls, hero):
        """获取转生所需材料"""
        quality = hero.quality if hasattr(hero, 'quality') else "common"
        if quality not in cls.REBIRTH_CONFIG:
            return None, "无法继续转生"
        return cls.REBIRTH_CONFIG[quality]["cost"], None

# 颜色主题
COLORS = {
    "bg_dark": (15, 15, 30),
    "bg_light": (25, 25, 45),
    "accent_gold": (255, 215, 0),
    "accent_red": (220, 60, 60),
    "accent_green": (60, 220, 100),
    "accent_blue": (70, 130, 220),
    "accent_purple": (180, 100, 220),
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 200),
    "hp_green": (60, 200, 60),
    "hp_red": (220, 60, 60),
    "hp_bg": (60, 60, 80)
}

class Particle:
    def __init__(self, x, y, color, speed, size, life, angle=None):
        self.x = x
        self.y = y
        self.color = color
        if angle is not None:
            self.speed_x = math.cos(angle) * speed
            self.speed_y = math.sin(angle) * speed
        else:
            self.speed_x = random.uniform(-speed, speed)
            self.speed_y = random.uniform(-speed, speed)
        self.size = size
        self.life = life
        self.max_life = life
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += 0.2  # 重力
        self.life -= 1
        self.size = max(0.5, self.size - 0.03)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class FloatingText:
    def __init__(self, text, x, y, color, font, is_damage=True):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.life = 50
        self.max_life = 50
        self.speed_y = -2 if is_damage else -1
        self.scale = 1.0
    
    def update(self):
        self.y += self.speed_y
        self.life -= 1
        if self.life > 40:
            self.scale = min(1.5, self.scale + 0.05)
        else:
            self.scale = max(1.0, self.scale - 0.02)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        text_surf = self.font.render(self.text, True, self.color)
        scaled_size = (int(text_surf.get_width() * self.scale), int(text_surf.get_height() * self.scale))
        scaled_surf = pygame.transform.scale(text_surf, scaled_size)
        scaled_surf.set_alpha(alpha)
        rect = scaled_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(scaled_surf, rect)

class AnimatedButton:
    def __init__(self, x, y, width, height, text, font, 
                 normal_color=(200, 50, 50), hover_color=(230, 80, 80),
                 text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.scale = 1.0
        self.glow_alpha = 0
        self.particles = []
    
    def update(self, mouse_pos):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered:
            self.scale = min(1.05, self.scale + 0.01)
            self.glow_alpha = min(100, self.glow_alpha + 5)
            if not was_hovered:
                for _ in range(5):
                    self.particles.append(Particle(
                        random.randint(self.rect.x, self.rect.x + self.rect.width),
                        self.rect.y + self.rect.height,
                        COLORS["accent_gold"],
                        2, random.randint(2, 4), 20
                    ))
        else:
            self.scale = max(1.0, self.scale - 0.01)
            self.glow_alpha = max(0, self.glow_alpha - 5)
        
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
    
    def draw(self, surface):
        # 发光效果
        if self.glow_alpha > 0:
            glow_surf = pygame.Surface((self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*self.hover_color[:3], self.glow_alpha),
                           (10, 10, self.rect.width, self.rect.height), border_radius=10)
            surface.blit(glow_surf, (self.rect.x - 10, self.rect.y - 10))
        
        # 按钮主体
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_x = self.rect.x + (self.rect.width - scaled_width) // 2
        scaled_y = self.rect.y + (self.rect.height - scaled_height) // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        color = self.hover_color if self.is_hovered else self.normal_color
        
        # 渐变按钮
        for i in range(scaled_height):
            ratio = i / scaled_height
            r = int(color[0] * (1 - ratio * 0.3))
            g = int(color[1] * (1 - ratio * 0.3))
            b = int(color[2] * (1 - ratio * 0.3))
            pygame.draw.line(surface, (r, g, b), 
                           (scaled_x, scaled_y + i), 
                           (scaled_x + scaled_width, scaled_y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], scaled_rect, 2, border_radius=8)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)
        
        # 粒子
        for p in self.particles:
            p.draw(surface)

def draw_gradient_background(surface, color1, color2):
    """绘制渐变背景"""
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_health_bar(surface, x, y, width, height, current, maximum, color):
    """绘制血条"""
    ratio = max(0, current / maximum)
    
    # 背景
    pygame.draw.rect(surface, COLORS["hp_bg"], (x, y, width, height), border_radius=5)
    
    # 血条
    if ratio > 0:
        bar_width = int(width * ratio)
        # 渐变
        for i in range(bar_width):
            r = int(color[0] * (1 - i / bar_width * 0.3))
            g = int(color[1] * (1 - i / bar_width * 0.3))
            b = int(color[2] * (1 - i / bar_width * 0.3))
            pygame.draw.line(surface, (r, g, b), (x + i, y), (x + i, y + height))
    
    # 边框
    pygame.draw.rect(surface, COLORS["text_white"], (x, y, width, height), 2, border_radius=5)
    
    # 数值
    font = pygame.font.Font(None, 24)
    text = font.render(f"{current}/{maximum}", True, COLORS["text_white"])
    text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
    surface.blit(text, text_rect)

def draw_character_card(surface, x, y, is_player, hp, max_hp, level, font):
    """绘制角色卡片"""
    card_width = 200
    card_height = 250
    
    # 卡片背景
    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (40, 40, 70, 200), (0, 0, card_width, card_height), border_radius=15)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, COLORS["accent_gold"], (x, y, card_width, card_height), 2, border_radius=15)
    
    # 角色图标
    icon = "🛡️" if is_player else "👹"
    icon_font = pygame.font.Font(None, 80)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + card_width // 2, y + 70))
    surface.blit(icon_surf, icon_rect)
    
    # 名称
    name = "玩家" if is_player else "敌人"
    name_surf = font.render(name, True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + card_width // 2, y + 130))
    surface.blit(name_surf, name_rect)
    
    # 等级
    level_surf = font.render(f"Lv.{level}", True, COLORS["text_gray"])
    level_rect = level_surf.get_rect(center=(x + card_width // 2, y + 160))
    surface.blit(level_surf, level_rect)
    
    # 血条
    hp_color = COLORS["hp_green"] if is_player else COLORS["hp_red"]
    draw_health_bar(surface, x + 20, y + 190, card_width - 40, 25, hp, max_hp, hp_color)

def draw_skill_effect(surface, center_x, center_y, skill_type):
    """绘制技能特效"""
    if skill_type == "weapon":
        # 武器技能：剑气效果
        for i in range(5):
            length = 100 + i * 20
            width = 5 + i
            alpha = max(0, 200 - i * 40)
            effect_surf = pygame.Surface((length, width), pygame.SRCALPHA)
            pygame.draw.rect(effect_surf, (*COLORS["accent_red"][:3], alpha), (0, 0, length, width))
            # 旋转效果
            rotated_surf = pygame.transform.rotate(effect_surf, i * 10)
            surface.blit(rotated_surf, (center_x - 150 - length // 2, center_y - width // 2))
    elif skill_type == "armor":
        # 防具技能：防御护盾效果
        for i in range(4):
            radius = 50 + i * 20
            alpha = max(0, 150 - i * 40)
            effect_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(effect_surf, (*COLORS["accent_green"][:3], alpha), (radius, radius), radius, 3)
            surface.blit(effect_surf, (center_x - 150 - radius, center_y - radius))
    elif skill_type == "horse":
        # 坐骑技能：速度提升效果
        for i in range(6):
            x = center_x - 150 + i * 30
            y = center_y - 20 + random.randint(-10, 10)
            alpha = max(0, 200 - i * 30)
            effect_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(effect_surf, (*COLORS["accent_blue"][:3], alpha), (10, 10), 5)
            surface.blit(effect_surf, (x, y))
    else:  # book
        # 书籍技能：魔法书效果
        for i in range(5):
            radius = 30 + i * 15
            alpha = max(0, 180 - i * 40)
            effect_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(effect_surf, (*COLORS["accent_purple"][:3], alpha), (radius, radius), radius, 2)
            # 星形效果
            points = []
            for j in range(5):
                angle = math.pi / 2 + j * math.pi * 2 / 5
                px = radius + math.cos(angle) * radius
                py = radius + math.sin(angle) * radius
                points.append((px, py))
            pygame.draw.polygon(effect_surf, (*COLORS["accent_gold"][:3], alpha), points)
            surface.blit(effect_surf, (center_x - 150 - radius, center_y - radius))

def draw_battle_effect(surface, center_x, center_y, is_player_attack):
    """绘制战斗特效"""
    # 冲击波效果
    for i in range(3):
        radius = 20 + i * 15
        alpha = max(0, 150 - i * 40)
        color = COLORS["accent_blue"] if is_player_attack else COLORS["accent_red"]
        effect_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(effect_surf, (*color[:3], alpha), (radius, radius), radius, 3)
        target_x = center_x - 150 if is_player_attack else center_x + 150
        surface.blit(effect_surf, (target_x - radius, center_y - radius))

# 元素颜色映射
# 武将图标
HERO_ICONS = {
    "赵云": "⚔️",
    "关羽": "🗡️",
    "张飞": "🛡️",
    "马超": "🐎",
    "黄忠": "🏹",
    "诸葛亮": "🧠",
    "周瑜": "🔥",
    "吕布": "💥",
    "貂蝉": "🌸",
    "华佗": "🌿"
}

# 小弟类
class Minion:
    def __init__(self, element):
        self.element = element
        self.max_hp = 30
        self.hp = self.max_hp
        self.damage = 10
    
    def attack(self, target):
        target.hp = max(0, target.hp - self.damage)
        return self.damage

# 武将类
class Hero:
    def __init__(self, name, level=1, hero_data=None):
        self.name = name
        self.level = level
        # 优先使用hero_data中的详细属性，否则从HERO_SKILLS获取基础技能
        if hero_data:
            self.skill = {
                "name": hero_data.get("skill_name", "普通攻击"),
                "damage": hero_data.get("skill_damage", 20),
                "element": hero_data.get("element", "火"),
                "description": hero_data.get("skill_description", "基础攻击"),
                "type": hero_data.get("skill_type", "normal"),
            }
            # 使用真实属性
            self.base_attack = hero_data.get("attack", 100)
            self.base_defense = hero_data.get("defense", 80)
            self.base_health = hero_data.get("health", 500)
            self.base_speed = hero_data.get("speed", 60)
            self.base_critical = hero_data.get("critical", 0.05)
            # 成长属性
            self.growth_attack = hero_data.get("growth_attack", 10)
            self.growth_defense = hero_data.get("growth_defense", 8)
            self.growth_health = hero_data.get("growth_health", 50)
            self.growth_speed = hero_data.get("growth_speed", 4)
            # 计算当前等级属性
            self.max_hp = int(self.base_health + (level - 1) * self.growth_health)
            self.hp = self.max_hp
            self.attack = int(self.base_attack + (level - 1) * self.growth_attack)
            self.defense = int(self.base_defense + (level - 1) * self.growth_defense)
            self.speed = int(self.base_speed + (level - 1) * self.growth_speed)
            self.critical = self.base_critical
            # 终极技能和被动
            self.ultimate_data = {
                "name": hero_data.get("ultimate_name", "必杀技"),
                "damage": hero_data.get("ultimate_damage", 100),
                "element": hero_data.get("ultimate_element", hero_data.get("element", "火")),
                "type": hero_data.get("ultimate_type", "normal"),
                "description": hero_data.get("ultimate_description", ""),
            }
            self.passive_name = hero_data.get("passive_name", "")
            self.passive_description = hero_data.get("passive_description", "")
        else:
            # 旧版兼容模式：从HERO_SKILLS获取基础技能
            self.skill = HERO_SKILLS.get(name, {
                "name": "普通攻击",
                "damage": 20,
                "element": "火",
                "description": "基础攻击"
            })
            self.base_attack = self.skill.get("damage", 20) * 5
            self.base_defense = 80
            self.base_health = 500
            self.base_speed = 60
            self.base_critical = 0.05
            self.max_hp = 100 + level * 20
            self.hp = self.max_hp
            self.attack = self.base_attack
            self.defense = self.base_defense
            self.speed = self.base_speed
            self.critical = self.base_critical
            self.ultimate_data = None
        
        self.element = self.skill["element"]
        # 经验和等级系统
        self.experience = 0
        self.experience_to_next_level = self._calculate_exp_to_level(level)
        # 根据等级生成小弟
        self.minions = []
        minion_count = min(5, level)
        for i in range(minion_count):
            minion = Minion(self.element)
            self.minions.append(minion)
        # 装备技能
        self.equip_skills = {
            "weapon": None,
            "armor": None,
            "horse": None,
            "book": None
        }
        # 枪械数据
        self.gun = None
        self.gun_multiplier = 1.0
        self.base_power = 100 + level * 20
        # 羁绊效果数据
        self.active_bonds = []
        self.bond_bonuses = {
            "damage_bonus": 0.0,
            "hp_bonus": 0.0,
            "crit_bonus": 0.0,
            "skill_damage": 0.0,
            "heal_bonus": 0.0,
            "speed_bonus": 0.0,
            # 新增羁绊效果类型（来自HERO_BONDS_EXPANDED的38条羁绊）
            "attack_bonus": 0.0,       # 攻击加成（与damage_bonus叠加）
            "all_bonus": 0.0,          # 全属性加成（已分发到各项）
            "fire_damage": 0.0,        # 火属性伤害加成
            "dodge_bonus": 0.0,        # 闪避概率
            "damage_reduction": 0.0,   # 伤害减免
            "defense_bonus": 0.0,      # 防御加成（减伤）
            "crit_damage": 0.0,        # 暴击伤害加成
        }
        # 被动技能效果
        self.passive_effects = {}
        self._parse_passive_skills()
        # 元素共鸣效果
        self.element_buffs = []
        self.shield = 0
        self.slow_turns = 0
        self.burn_turns = 0
        self.burn_damage = 0
        # 连击系统
        self.combo_count = 0
        self.max_combo = 15
        self.combo_timer = 0
        self.combo_timeout = 4000
        self.combo_bonus_stages = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.3, 2.6, 3.0, 3.5]
        # 必杀技系统
        self.rage = 0
        self.max_rage = 100
        self.rage_per_hit = 10
        self.ultimate_skill = self.get_ultimate_skill()
        self.ultimate_cooldown = 0
        self.max_ultimate_cooldown = 3
        # 战术技能系统
        self.tactical_skill = self.get_tactical_skill()
        self.tactical_cooldown = 0
        # Buff/Debuff系统
        self.buffs = []
        self.debuffs = []
        # 眩晕状态
        self.is_stunned = False
        # 地形修正
        self.terrain = None
        self.stun_turns = 0
        # 中毒状态
        self.is_poisoned = False
        self.poison_turns = 0
        self.poison_damage = 0
        # 冰冻状态
        self.is_frozen = False
        self.freeze_turns = 0
        # 沉默状态
        self.is_silenced = False
        self.silence_turns = 0
        # 攻击力增益
        self.attack_buff = 0.0
        # 防御力增益
        self.defense_buff = 0.0
        # 突破系统
        self.breakthrough_level = 0
        self.max_breakthrough = 5
        self.breakthrough_bonus = 0.0
        # 觉醒系统
        self.is_awakened = False
        self.awakened_name = ""
        self.awakened_bonus = 0.0
        # 缘分系统
        self.active_fates = []
        # 神兵系统
        self.divine_weapon = None
        self.divine_weapon_effect = ""
        # 称号系统
        self.title = ""
        self.title_description = ""
        # 兵种系统
        self.troop_type = "infantry"
        # 阵型系统
        self.formation = None
        # 专精系统
        self.specialty = None
        self.specialty_mastery = 1
        self.specialty_name = ""
        # 天赋系统
        self.talents = []
    
    def _calculate_exp_to_level(self, level):
        """计算升级所需经验"""
        return int(100 * (1.5 ** (level - 1)))
    
    def add_experience(self, exp_amount):
        """添加经验并检查升级"""
        messages = []
        self.experience += exp_amount
        
        while self.experience >= self.experience_to_next_level:
            self.experience -= self.experience_to_next_level
            self.level += 1
            self.experience_to_next_level = self._calculate_exp_to_level(self.level)
            
            # 升级属性提升
            self.max_hp += int(self.max_hp * 0.15)
            self.hp = self.max_hp
            self.attack += int(self.attack * 0.12)
            self.defense += int(self.defense * 0.1)
            self.speed += int(self.speed * 0.05)
            
            messages.append(f"{self.name} 升级至 Lv.{self.level}！")
        
        return messages
    
    def get_exp_progress(self):
        """获取经验进度百分比"""
        return min(1.0, self.experience / self.experience_to_next_level)
    
    def breakthrough(self, materials, gold):
        """突破武将，提升基础属性"""
        if self.breakthrough_level >= self.max_breakthrough:
            return False, "已达到最高突破等级"
        
        costs = self._get_breakthrough_cost(self.breakthrough_level + 1)
        if gold < costs["gold"]:
            return False, "金元宝不足"
        if materials < costs["materials"]:
            return False, "突破材料不足"
        
        self.breakthrough_level += 1
        self.breakthrough_bonus = self.breakthrough_level * 0.2
        
        self.max_hp = int(self.max_hp * 1.3)
        self.hp = self.max_hp
        self.attack = int(self.attack * 1.25)
        self.defense = int(self.defense * 1.2)
        self.speed = int(self.speed * 1.15)
        
        return True, f"{self.name} 突破至 +{self.breakthrough_level}！"
    
    def _get_breakthrough_cost(self, target_level):
        """获取突破所需资源"""
        base_cost = {"gold": 500, "materials": 20}
        multiplier = 2 ** (target_level - 1)
        return {
            "gold": base_cost["gold"] * multiplier,
            "materials": base_cost["materials"] * multiplier
        }
    
    def can_breakthrough(self, materials, gold):
        """检查是否可以突破"""
        if self.breakthrough_level >= self.max_breakthrough:
            return False, "已达到最高突破等级"
        costs = self._get_breakthrough_cost(self.breakthrough_level + 1)
        if gold < costs["gold"]:
            return False, f"金元宝不足，需要{costs['gold']}"
        if materials < costs["materials"]:
            return False, f"突破材料不足，需要{costs['materials']}"
        return True, "可以突破"
    
    def awaken(self, dragon_crystals):
        """觉醒武将，大幅提升属性并获得新技能"""
        if self.is_awakened:
            return False, "已经觉醒"
        
        if dragon_crystals < 100:
            return False, "龙晶不足，需要100个"
        
        self.is_awakened = True
        self.awakened_name = f"真·{self.name}"
        self.awakened_bonus = 0.5
        
        self.max_hp = int(self.max_hp * 1.8)
        self.hp = self.max_hp
        self.attack = int(self.attack * 1.6)
        self.defense = int(self.defense * 1.4)
        self.speed = int(self.speed * 1.3)
        
        self.skill["damage"] = int(self.skill["damage"] * 1.5)
        if self.ultimate_data:
            self.ultimate_data["damage"] = int(self.ultimate_data["damage"] * 1.8)
        
        return True, f"{self.name} 觉醒为 {self.awakened_name}！"
    
    def get_ultimate_skill(self):
        """获取必杀技（优先使用hero_data中的详细数据）"""
        if self.ultimate_data:
            return {
                "name": self.ultimate_data["name"],
                "damage": self.ultimate_data["damage"],
                "element": self.ultimate_data["element"],
                "rage_cost": 100,
                "description": self.ultimate_data["description"]
            }
        # 旧版静态数据（兼容旧代码）
        ultimate_skills = {
            "赵云": {"name": "七进七出", "damage": 150, "element": "风", "rage_cost": 100, "description": "赵云的终极技能，连续攻击敌人"},
            "关羽": {"name": "青龙偃月斩", "damage": 200, "element": "火", "rage_cost": 100, "description": "关羽的终极技能，强力斩击"},
            "张飞": {"name": "怒吼", "damage": 180, "element": "土", "rage_cost": 100, "description": "张飞的终极技能，震退敌人"},
            "诸葛亮": {"name": "天雷阵", "damage": 220, "element": "雷", "rage_cost": 100, "description": "诸葛亮的终极技能，召唤天雷"},
            "曹操": {"name": "乱世枭雄", "damage": 190, "element": "火", "rage_cost": 100, "description": "曹操的终极技能，统御攻击"},
            "吕布": {"name": "战神降临", "damage": 250, "element": "雷", "rage_cost": 100, "description": "吕布的终极技能，无敌攻击"},
            "貂蝉": {"name": "倾国倾城", "damage": 160, "element": "水", "rage_cost": 100, "description": "貂蝉的终极技能，魅惑攻击"},
            "黄忠": {"name": "百步穿杨", "damage": 210, "element": "风", "rage_cost": 100, "description": "黄忠的终极技能，远程狙击"},
            "马超": {"name": "西凉风暴", "damage": 180, "element": "土", "rage_cost": 100, "description": "马超的终极技能，骑兵突击"},
            "周瑜": {"name": "业火焚城", "damage": 230, "element": "火", "rage_cost": 100, "description": "周瑜的终极技能，火烧连营"}
        }
        return ultimate_skills.get(self.name, {
            "name": "必杀技",
            "damage": 150,
            "element": self.element,
            "rage_cost": 100,
            "description": "强力必杀技"
        })
    
    def get_tactical_skill(self):
        """获取将帅兵法战术技能"""
        from ASSET.hero_database import TACTICAL_SKILLS
        return TACTICAL_SKILLS.get(self.name, None)
    
    def can_use_tactical(self):
        """检查是否可以使用战术技能"""
        if not self.tactical_skill:
            return False
        if self.tactical_cooldown > 0:
            return False
        return True
    
    def use_tactical(self, allies, enemies):
        """使用战术技能"""
        if not self.can_use_tactical():
            return None
        
        skill = self.tactical_skill
        self.tactical_cooldown = skill.get("cooldown", 4)
        effect = skill.get("effect", "")
        
        messages = []
        
        if effect == "dodge":
            self.add_buff("dodge_up", skill.get("duration", 2))
            messages.append(f"【{skill['name']}】{self.name}使用空城计！接下来{skill['duration']}回合闪避率大幅提升！")
        
        elif effect == "combo_attack":
            targets = min(skill.get("targets", 5), len(enemies))
            damage_modifier = skill.get("damage_modifier", 0.8)
            for i in range(targets):
                if enemies[i].hp > 0:
                    damage = int(self.attack * damage_modifier)
                    enemies[i].hp = max(0, enemies[i].hp - damage)
                    messages.append(f"【{skill['name']}】{self.name}连斩！{enemies[i].name}受到{damage}点伤害！")
        
        elif effect == "debuff_all":
            debuff_type = skill.get("debuff_type", "confusion")
            duration = skill.get("duration", 2)
            for enemy in enemies:
                if enemy.hp > 0:
                    enemy.add_debuff(debuff_type, duration)
            messages.append(f"【{skill['name']}】{self.name}使敌军军心涣散！所有敌人陷入{debuff_type}状态！")
        
        elif effect == "heal_all":
            heal_amount = skill.get("heal_amount", 0.3)
            for ally in allies:
                heal = int(ally.max_hp * heal_amount)
                ally.hp = min(ally.max_hp, ally.hp + heal)
                messages.append(f"【{skill['name']}】{self.name}恢复{ally.name} {heal}点生命！")
        
        elif effect == "multi_attack":
            targets = min(skill.get("targets", 7), len(enemies))
            damage_modifier = skill.get("damage_modifier", 0.6)
            for i in range(targets):
                if enemies[i].hp > 0:
                    damage = int(self.attack * damage_modifier)
                    enemies[i].hp = max(0, enemies[i].hp - damage)
                    messages.append(f"【{skill['name']}】{self.name}七进七出！{enemies[i].name}受到{damage}点伤害！")
        
        elif effect == "fear":
            duration = skill.get("duration", 1)
            for enemy in enemies:
                if enemy.hp > 0:
                    enemy.add_debuff("fear", duration)
            messages.append(f"【{skill['name']}】{self.name}一声怒吼！敌军胆寒！")
        
        elif effect == "fire_aoe":
            damage = skill.get("damage", 150)
            burn_duration = skill.get("burn_duration", 3)
            for enemy in enemies:
                if enemy.hp > 0:
                    enemy.hp = max(0, enemy.hp - damage)
                    enemy.burn_turns = burn_duration
                    messages.append(f"【{skill['name']}】{self.name}火烧赤壁！{enemy.name}受到{damage}点伤害并被点燃！")
        
        elif effect == "buff_self":
            buff_type = skill.get("buff_type", "power_up")
            duration = skill.get("duration", 3)
            power_bonus = skill.get("power_bonus", 0.5)
            self.add_buff(buff_type, duration, power_bonus)
            messages.append(f"【{skill['name']}】{self.name}隐忍待发！攻击力提升{int(power_bonus * 100)}%！")
        
        elif effect == "charge":
            if enemies:
                target = enemies[0]
                damage_multiplier = skill.get("damage_multiplier", 2.0)
                damage = int(self.attack * damage_multiplier)
                target.hp = max(0, target.hp - damage)
                messages.append(f"【{skill['name']}】{self.name}铁骑冲锋！{target.name}受到{damage}点伤害！")
        
        elif effect == "piercing_shot":
            if enemies:
                target = enemies[0]
                damage_modifier = skill.get("damage_modifier", 1.5)
                damage = int(self.attack * damage_modifier)
                target.hp = max(0, target.hp - damage)
                messages.append(f"【{skill['name']}】{self.name}百步穿杨！{target.name}受到{damage}点伤害！")
        
        elif effect == "surprise_attack":
            if enemies:
                target = enemies[0]
                damage_modifier = skill.get("damage_modifier", 1.8)
                damage = int(self.attack * damage_modifier * 2)
                target.hp = max(0, target.hp - damage)
                messages.append(f"【{skill['name']}】{self.name}出奇制胜！{target.name}受到{damage}点暴击伤害！")
        
        elif effect == "rage_boost":
            rage_amount = skill.get("rage_amount", 50)
            self.rage = min(100, self.rage + rage_amount)
            messages.append(f"【{skill['name']}】{self.name}继承遗志！恢复{rage_amount}点怒气！")
        
        elif effect == "chain_reaction":
            chain_count = skill.get("chain_count", 3)
            damage_modifier = skill.get("damage_modifier", 0.7)
            for i in range(min(chain_count, len(enemies))):
                if enemies[i].hp > 0:
                    damage = int(self.attack * damage_modifier * (i + 1))
                    enemies[i].hp = max(0, enemies[i].hp - damage)
                    messages.append(f"【{skill['name']}】连环计！{enemies[i].name}受到{damage}点伤害！")
        
        elif effect == "wildfire":
            aoe_damage = skill.get("aoe_damage", 100)
            for enemy in enemies:
                if enemy.hp > 0:
                    enemy.hp = max(0, enemy.hp - aoe_damage)
                    messages.append(f"【{skill['name']}】{self.name}火烧连营！{enemy.name}受到{aoe_damage}点伤害！")
        
        elif effect == "stealth_attack":
            if enemies:
                target = enemies[0]
                damage_multiplier = skill.get("damage_multiplier", 2.5)
                damage = int(self.attack * damage_multiplier)
                target.hp = max(0, target.hp - damage)
                messages.append(f"【{skill['name']}】{self.name}白衣渡江！{target.name}受到{damage}点伤害！")
        
        elif effect == "night_raid":
            targets = min(skill.get("targets", 3), len(enemies))
            damage_multiplier = skill.get("damage_multiplier", 1.5)
            for i in range(targets):
                if enemies[i].hp > 0:
                    damage = int(self.attack * damage_multiplier)
                    enemies[i].hp = max(0, enemies[i].hp - damage)
                    messages.append(f"【{skill['name']}】{self.name}百骑劫营！{enemies[i].name}受到{damage}点伤害！")
        
        elif effect == "overpower":
            if enemies:
                target = enemies[0]
                damage_multiplier = skill.get("damage_multiplier", 3.0)
                damage = int(self.attack * damage_multiplier)
                target.hp = max(0, target.hp - damage)
                messages.append(f"【{skill['name']}】{self.name}天下无双！{target.name}受到{damage}点伤害！")
        
        elif effect == "charm":
            duration = skill.get("duration", 2)
            for enemy in enemies:
                if enemy.hp > 0:
                    enemy.add_debuff("charm", duration)
            messages.append(f"【{skill['name']}】{self.name}倾国倾城！敌军被迷惑！")
        
        elif effect == "buff_all":
            buff_type = skill.get("buff_type", "defense_up")
            duration = skill.get("duration", 3)
            defense_bonus = skill.get("defense_bonus", 0.3)
            for ally in allies:
                ally.add_buff(buff_type, duration, defense_bonus)
            messages.append(f"【{skill['name']}】{self.name}稳固军心！所有友军防御提升{int(defense_bonus * 100)}%！")
        
        elif effect == "recruit":
            minion_count = skill.get("minion_count", 2)
            for _ in range(minion_count):
                minion = Minion(self.element)
                self.minions.append(minion)
            messages.append(f"【{skill['name']}】{self.name}招兵买马！获得{minion_count}名小弟！")
        
        return messages
    
    def _parse_passive_skills(self):
        """解析被动技能效果，优先使用PASSIVE_EFFECTS注册表，兼容旧版描述解析"""
        if not self.passive_name:
            return
        
        # 优先使用结构化的PASSIVE_EFFECTS注册表
        if self.passive_name in PASSIVE_EFFECTS:
            self.passive_effects = PASSIVE_EFFECTS[self.passive_name].copy()
            return
        
        # 兼容旧版：从描述中解析效果
        desc = self.passive_description
        
        if "恢复" in desc or "回血" in desc:
            if "全体" in desc:
                self.passive_effects["heal_all"] = self._extract_percentage(desc, 5) / 100
            else:
                self.passive_effects["heal_self"] = self._extract_percentage(desc, 5) / 100
        
        if "暴击" in desc:
            self.passive_effects["crit_bonus"] = self._extract_percentage(desc, 20) / 100
        
        if "闪避" in desc:
            self.passive_effects["dodge_bonus"] = self._extract_percentage(desc, 15) / 100
        
        if "护盾" in desc:
            if "概率" in desc:
                self.passive_effects["shield_chance"] = self._extract_percentage(desc, 20) / 100
            else:
                self.passive_effects["shield_amount"] = self._extract_number(desc, 100)
        
        if "攻击力提升" in desc or "攻击提升" in desc:
            self.passive_effects["hp_based_attack"] = self._extract_percentage(desc, 40) / 100
        
        if "击杀" in desc and "恢复" in desc:
            self.passive_effects["lifesteal_on_kill"] = self._extract_percentage(desc, 20) / 100
        
        if "伤害减免" in desc or "减伤" in desc:
            self.passive_effects["damage_reduction"] = self._extract_percentage(desc, 10) / 100
        
        if "速度" in desc and "提升" in desc:
            self.passive_effects["speed_bonus"] = self._extract_percentage(desc, 10) / 100

    def _extract_percentage(self, text, default=10):
        """从文本中提取百分比数字"""
        import re
        match = re.search(r'(\d+)%', text)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
        return default

    def _extract_number(self, text, default=100):
        """从文本中提取数字"""
        import re
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
        return default

    def apply_passive_effects(self, allies=None, enemies=None):
        """应用被动技能效果"""
        if not self.passive_effects:
            return []
        
        messages = []
        
        # 重置被动攻击加成，每回合重新计算（防止永久叠加）
        self.attack_buff = 0
        
        # 基础恢复效果
        if "heal_self" in self.passive_effects:
            heal_amount = int(self.max_hp * self.passive_effects["heal_self"])
            self.hp = min(self.max_hp, self.hp + heal_amount)
            messages.append(f"{self.name}的{self.passive_name}恢复了{heal_amount}点生命")
        
        if "heal_all" in self.passive_effects and allies:
            heal_amount = int(self.max_hp * self.passive_effects["heal_all"])
            for ally in allies:
                ally.hp = min(ally.max_hp, ally.hp + heal_amount)
            messages.append(f"{self.name}的{self.passive_name}恢复了己方全体{heal_amount}点生命")
        
        # 护盾效果
        if "shield_chance" in self.passive_effects:
            if random.random() < self.passive_effects["shield_chance"]:
                shield_amount = self.passive_effects.get("shield_amount", int(self.max_hp * 0.2))
                self.shield += shield_amount
                messages.append(f"{self.name}的{self.passive_name}获得了{shield_amount}点护盾")
        
        # 基于生命值的攻击加成
        if "hp_based_attack" in self.passive_effects:
            hp_ratio = self.hp / self.max_hp
            if hp_ratio < 0.5:
                bonus = self.passive_effects["hp_based_attack"] * (1 - hp_ratio)
                self.attack_buff = bonus
                messages.append(f"{self.name}的{self.passive_name}激活，攻击力提升{int(bonus*100)}%")
        
        # 固定攻击加成
        if "attack_bonus" in self.passive_effects:
            self.attack_buff += self.passive_effects["attack_bonus"]
            messages.append(f"{self.name}的{self.passive_name}提升攻击力{int(self.passive_effects['attack_bonus']*100)}%")
        
        # 速度加成
        if "speed_bonus" in self.passive_effects:
            self.bond_bonuses["speed_bonus"] += self.passive_effects["speed_bonus"]
            messages.append(f"{self.name}的{self.passive_name}提升速度{int(self.passive_effects['speed_bonus']*100)}%")
        
        # 伤害减免
        if "damage_reduction" in self.passive_effects:
            self.bond_bonuses["damage_reduction"] += self.passive_effects["damage_reduction"]
        
        # 暴击伤害加成
        if "crit_damage" in self.passive_effects:
            self.bond_bonuses["crit_damage"] += self.passive_effects["crit_damage"]
        
        # 暴击率加成
        if "crit_bonus" in self.passive_effects:
            self.bond_bonuses["crit_bonus"] += self.passive_effects["crit_bonus"]
        
        # 闪避率加成
        if "dodge_bonus" in self.passive_effects:
            self.bond_bonuses["dodge_bonus"] += self.passive_effects["dodge_bonus"]
        
        # 队友加成效果
        if "ally_buff" in self.passive_effects and allies:
            ally_buff = self.passive_effects["ally_buff"]
            for ally_name, buffs in ally_buff.items():
                for ally in allies:
                    if ally.name == ally_name:
                        for stat, value in buffs.items():
                            if stat == "attack":
                                ally.attack_buff += value
                            elif stat == "defense":
                                ally.bond_bonuses["defense_bonus"] += value
                        messages.append(f"{self.name}的{self.passive_name}使{ally_name}属性提升")
        
        return messages

    def trigger_passive_on_kill(self, target):
        """击杀目标时触发被动效果"""
        messages = []
        
        if "lifesteal_on_kill" in self.passive_effects:
            heal_amount = int(target.max_hp * self.passive_effects["lifesteal_on_kill"])
            self.hp = min(self.max_hp, self.hp + heal_amount)
            messages.append(f"{self.name}击杀{target.name}，{self.passive_name}恢复了{heal_amount}点生命")
        
        # 队友阵亡时的增益效果（继承遗志）
        if "death_buff" in self.passive_effects:
            bonus = self.passive_effects["death_buff"]
            self.attack_buff += bonus
            self.bond_bonuses["defense_bonus"] += bonus
            self.bond_bonuses["speed_bonus"] += bonus
            messages.append(f"{target.name}阵亡，{self.name}的{self.passive_name}激活，全属性提升{int(bonus*100)}%")
        
        return messages

    def add_combo(self):
        """增加连击数"""
        if self.combo_count < self.max_combo:
            self.combo_count += 1
        self.combo_timer = pygame.time.get_ticks()
    
    def reset_combo(self):
        """重置连击"""
        self.combo_count = 0
    
    def update_combo(self):
        """更新连击状态"""
        if pygame.time.get_ticks() - self.combo_timer > self.combo_timeout:
            self.reset_combo()
    
    def get_combo_bonus(self):
        """获取连击伤害加成（进阶版）"""
        if self.combo_count == 0:
            return 1.0
        base_bonus = 1.0 + self.combo_count * 0.1
        stage_index = min(self.combo_count - 1, len(self.combo_bonus_stages) - 1)
        return base_bonus * self.combo_bonus_stages[stage_index]
    
    def get_combo_rage_bonus(self):
        """获取连击怒气回复奖励"""
        if self.combo_count == 0:
            return 0
        return int(self.combo_count * 5)
    
    def add_combo_reward(self):
        """应用连击奖励（怒气回复）"""
        rage_bonus = self.get_combo_rage_bonus()
        if rage_bonus > 0:
            self.rage = min(100, self.rage + rage_bonus)
            return rage_bonus
        return 0
    
    def add_buff(self, buff_type, duration, value=0.0):
        """添加Buff效果"""
        self.buffs.append({
            "type": buff_type,
            "duration": duration,
            "value": value
        })
        if buff_type == "attack":
            self.attack_buff += value
        elif buff_type == "defense":
            self.defense_buff += value
    
    def add_debuff(self, debuff_type, duration, value=0.0):
        """添加Debuff效果"""
        self.debuffs.append({
            "type": debuff_type,
            "duration": duration,
            "value": value
        })
        if debuff_type == "stun":
            self.is_stunned = True
            self.stun_turns = duration
        elif debuff_type == "poison":
            self.is_poisoned = True
            self.poison_turns = duration
            self.poison_damage = value
        elif debuff_type == "freeze":
            self.is_frozen = True
            self.freeze_turns = duration
        elif debuff_type == "silence":
            self.is_silenced = True
            self.silence_turns = duration
    
    def update_buffs_debuffs(self):
        """更新Buff和Debuff状态"""
        # 更新必杀技冷却
        if self.ultimate_cooldown > 0:
            self.ultimate_cooldown -= 1
        
        # 更新战术技能冷却
        if self.tactical_cooldown > 0:
            self.tactical_cooldown -= 1
        
        # 更新Buff
        self.buffs = [b for b in self.buffs if b["duration"] > 0]
        for buff in self.buffs:
            buff["duration"] -= 1
        
        # 更新Debuff
        self.debuffs = [d for d in self.debuffs if d["duration"] > 0]
        
        if self.is_stunned:
            self.stun_turns -= 1
            if self.stun_turns <= 0:
                self.is_stunned = False
        
        if self.is_poisoned:
            self.poison_turns -= 1
            if self.poison_turns <= 0:
                self.is_poisoned = False
                self.poison_damage = 0
        
        if self.is_frozen:
            self.freeze_turns -= 1
            if self.freeze_turns <= 0:
                self.is_frozen = False
        
        if self.is_silenced:
            self.silence_turns -= 1
            if self.silence_turns <= 0:
                self.is_silenced = False
    
    def can_act(self):
        """检查是否可以行动"""
        return not (self.is_stunned or self.is_frozen)
    
    def add_rage(self, amount=10):
        """增加怒气"""
        self.rage = min(self.max_rage, self.rage + amount)
    
    def can_use_ultimate(self):
        """检查是否可以使用必杀技（考虑冷却）"""
        if self.ultimate_cooldown > 0:
            return False
        return self.rage >= self.ultimate_skill["rage_cost"]
    
    def use_ultimate(self, target):
        """使用必杀技"""
        if not self.can_use_ultimate():
            return 0, False
        
        self.rage -= self.ultimate_skill["rage_cost"]
        self.ultimate_cooldown = self.max_ultimate_cooldown
        damage = self.ultimate_skill["damage"] * (1 + self.bond_bonuses["damage_bonus"] + self.bond_bonuses["attack_bonus"])
        damage *= self.get_combo_bonus()
        # 应用技能伤害加成
        damage *= (1 + self.bond_bonuses["skill_damage"])
        # 应用元素伤害修正（克制+弱点）
        damage_modifier = ElementSystem.get_total_damage_modifier(self.element, target.element)
        damage *= damage_modifier
        # 应用兵种克制效果
        troop_bonus = TroopSystem.get_troop_bonus(self.troop_type, target.troop_type)
        damage *= (1 + troop_bonus)
        
        # 应用目标闪避
        if random.random() < target.bond_bonuses["dodge_bonus"]:
            # 重置连击
            self.reset_combo()
            return 0, False
        
        # 应用目标防御力Debuff
        if target.defense_buff < 0:
            damage *= (1 - target.defense_buff)
        
        # 应用目标伤害减免和防御加成
        damage *= (1 - target.bond_bonuses["damage_reduction"])
        damage *= (1 - target.bond_bonuses["defense_bonus"] * 0.5)
        
        # 处理护盾
        if target.shield > 0:
            if target.shield >= damage:
                target.shield -= damage
                # 重置连击
                self.reset_combo()
                return damage, False
            else:
                damage -= target.shield
                target.shield = 0
        
        target.hp = max(0, target.hp - damage)
        
        # 重置连击
        self.reset_combo()
        
        return damage, True

    def apply_bond_effects(self, all_hero_names):
        """检查并应用羁绊效果（整合了缘分系统）"""
        self.active_bonds = []
        # 重置所有羁绊加成
        for k in self.bond_bonuses:
            self.bond_bonuses[k] = 0.0
        
        for bond_id, bond_data in HERO_BONDS.items():
            bond_heroes = bond_data["heroes"]
            # 检查是否满足羁绊条件
            requirement = bond_data.get("requirement", len(bond_heroes))
            if requirement == 1:
                if self.name in bond_heroes:
                    self.active_bonds.append(bond_id)
                    effect = bond_data["effect"]
                    etype = effect["type"]
                    value = effect["value"]
                    if etype in self.bond_bonuses:
                        self.bond_bonuses[etype] += value
                    # all_bonus 特殊处理：全属性加成分发到各项
                    if etype == "all_bonus":
                        self.bond_bonuses["damage_bonus"] += value
                        self.bond_bonuses["hp_bonus"] += value
                        self.bond_bonuses["defense_bonus"] += value * 0.5
                        self.bond_bonuses["speed_bonus"] += value * 0.5
                    # 应用额外效果
                    if "extra_effects" in bond_data:
                        for extra_type, extra_value in bond_data["extra_effects"].items():
                            if extra_type in self.bond_bonuses:
                                self.bond_bonuses[extra_type] += extra_value
                    # 记录特殊效果
                    if "special" in bond_data:
                        if "active_bond_specials" not in self.__dict__:
                            self.active_bond_specials = []
                        self.active_bond_specials.append(bond_data["special"])
            else:
                common_heroes = set(all_hero_names) & set(bond_heroes)
                if len(common_heroes) >= requirement:
                    # 满足羁绊条件
                    self.active_bonds.append(bond_id)
                    effect = bond_data["effect"]
                    etype = effect["type"]
                    value = effect["value"]
                    if etype in self.bond_bonuses:
                        self.bond_bonuses[etype] += value
                    # all_bonus 特殊处理：全属性加成分发到各项
                    if etype == "all_bonus":
                        self.bond_bonuses["damage_bonus"] += value
                        self.bond_bonuses["hp_bonus"] += value
                        self.bond_bonuses["defense_bonus"] += value * 0.5
                        self.bond_bonuses["speed_bonus"] += value * 0.5
                    # 应用额外效果
                    if "extra_effects" in bond_data:
                        for extra_type, extra_value in bond_data["extra_effects"].items():
                            if extra_type in self.bond_bonuses:
                                self.bond_bonuses[extra_type] += extra_value
                    # 记录特殊效果
                    if "special" in bond_data:
                        if "active_bond_specials" not in self.__dict__:
                            self.active_bond_specials = []
                        self.active_bond_specials.append(bond_data["special"])
        
        # 应用羁绊属性加成到实际属性
        if self.bond_bonuses["hp_bonus"] > 0:
            self.max_hp = int(self.max_hp * (1 + self.bond_bonuses["hp_bonus"]))
            self.hp = min(self.hp + int(self.max_hp * self.bond_bonuses["hp_bonus"]), self.max_hp)
        if self.bond_bonuses["speed_bonus"] > 0:
            self.speed = int(self.speed * (1 + self.bond_bonuses["speed_bonus"]))

    def get_power_with_gun(self):
        """获取带枪械加成的武力值"""
        base_power = self.attack
        return base_power * self.gun_multiplier * (1 + self.bond_bonuses["damage_bonus"] + self.bond_bonuses["attack_bonus"])

    def has_bullets(self):
        """检查是否有足够的子弹"""
        if not self.gun:
            return True
        gun_data = GUNS.get(self.gun, {})
        bullet_type = gun_data.get("bullet_type", "普通子弹")
        bullet_cost = gun_data.get("bullets_per_round", 1)
        return data["resources"].get(bullet_type, 0) >= bullet_cost

    def consume_bullets(self):
        """消耗子弹"""
        if not self.gun:
            return True
        gun_data = GUNS.get(self.gun, {})
        bullet_type = gun_data.get("bullet_type", "普通子弹")
        bullet_cost = gun_data.get("bullets_per_round", 1)
        if data["resources"].get(bullet_type, 0) >= bullet_cost:
            data["resources"][bullet_type] -= bullet_cost
            save()
            return True
        return False

    def set_gun(self, gun_type):
        """设置枪械"""
        if gun_type and gun_type in GUNS:
            self.gun = gun_type
            self.gun_multiplier = GUNS[gun_type]["damage_multiplier"]
        else:
            self.gun = None
            self.gun_multiplier = 1.0

    def attack(self, target):
        # 使用真实攻击力属性（来自hero_data），而非技能伤害+等级的简化公式
        damage = self.attack
        # 应用攻击力Buff
        damage *= (1 + self.attack_buff)
        
        # 应用VIP伤害加成
        vip_bonus = get_vip_bonus()
        damage *= (1 + float(vip_bonus["damage_bonus"].replace("%", "")) / 100)
        
        # 应用羁绊攻击加成（damage_bonus + attack_bonus）
        damage *= (1 + self.bond_bonuses["damage_bonus"] + self.bond_bonuses["attack_bonus"])
        # 应用技能伤害加成
        damage *= (1 + self.bond_bonuses["skill_damage"])
        # 应用元素伤害修正（克制+弱点）
        damage_modifier = ElementSystem.get_total_damage_modifier(self.element, target.element)
        damage *= damage_modifier
        # 应用兵种克制效果
        troop_bonus = TroopSystem.get_troop_bonus(self.troop_type, target.troop_type)
        damage *= (1 + troop_bonus)
        # 应用暴击
        if random.random() < self.bond_bonuses["crit_bonus"]:
            damage *= (1.5 + self.bond_bonuses["crit_damage"])
        # 应用枪械
        if self.gun and self.has_bullets():
            damage *= self.gun_multiplier
            self.consume_bullets()
        
        # 应用目标闪避
        if random.random() < target.bond_bonuses["dodge_bonus"]:
            return 0, "dodge"
        
        # 应用目标防御力Debuff
        if target.defense_buff < 0:
            damage *= (1 - target.defense_buff)
        
        # 应用目标伤害减免和防御加成
        damage *= (1 - target.bond_bonuses["damage_reduction"])
        damage *= (1 - target.bond_bonuses["defense_bonus"] * 0.5)
        
        # 处理护盾
        if target.shield > 0:
            if target.shield >= damage:
                target.shield -= damage
                return damage, "shield"
            else:
                damage -= target.shield
                target.shield = 0
        
        target.hp = max(0, target.hp - damage)
        
        # 应用元素伤害修正（克制+弱点）
        damage_modifier = ElementSystem.get_total_damage_modifier(self.element, target.element)
        damage *= damage_modifier
        # 应用兵种克制效果
        troop_bonus = TroopSystem.get_troop_bonus(self.troop_type, target.troop_type)
        damage *= (1 + troop_bonus)
        
        # 应用元素共鸣效果
        synergy_messages = ElementSystem.apply_synergy_effects(self, target)
        if synergy_messages:
            for msg in synergy_messages:
                self.battle_log.append(msg)
        
        # 应用连击奖励（怒气回复）
        self.add_combo_reward()
        
        return damage, "normal"
    
    def perform_combo_attack(self, allies, target):
        """发动武将合击（同阵营或同元素武将共同攻击）"""
        if len(allies) < 2:
            return 0, False
        
        same_faction = []
        same_element = []
        faction = HERO_FACTIONS.get(self.name, "")
        
        for ally in allies:
            if ally != self and ally.hp > 0:
                ally_faction = HERO_FACTIONS.get(ally.name, "")
                if ally_faction == faction and faction:
                    same_faction.append(ally)
                if ally.element == self.element:
                    same_element.append(ally)
        
        combo_allies = same_faction[:2] if same_faction else same_element[:2]
        
        if not combo_allies:
            return 0, False
        
        total_damage = 0
        multiplier = 1.0 + len(combo_allies) * 0.5
        
        for ally in combo_allies:
            damage = ally.skill["damage"] * multiplier * (1 + ally.bond_bonuses["damage_bonus"] + ally.bond_bonuses["attack_bonus"])
            total_damage += damage
            target.hp = max(0, target.hp - damage)
        
        damage = self.skill["damage"] * multiplier * (1 + self.bond_bonuses["damage_bonus"] + self.bond_bonuses["attack_bonus"])
        total_damage += damage
        target.hp = max(0, target.hp - damage)
        
        return total_damage, True
    
    def use_skill(self, skill_type, target):
        """使用装备技能"""
        if skill_type in self.equip_skills and self.equip_skills[skill_type]:
            skill = self.equip_skills[skill_type]
            if skill_type == "weapon":
                # 武器技能：高伤害
                damage = skill["damage"] * 1.5
                target.hp = max(0, target.hp - damage)
                return damage, "weapon"
            elif skill_type == "armor":
                # 防具技能：恢复生命值
                heal = skill["defense"] * 2
                self.hp = min(self.max_hp, self.hp + heal)
                return heal, "armor"
            elif skill_type == "horse":
                # 坐骑技能：速度加成，增加攻击力
                speed_bonus = skill["speed"] * 0.1
                damage = self.skill["damage"] * (1 + speed_bonus)
                target.hp = max(0, target.hp - damage)
                return damage, "horse"
            elif skill_type == "book":
                # 书籍技能：暴击
                critical = skill["critical"]
                damage = self.skill["damage"] * 2 if random.random() < critical else self.skill["damage"]
                target.hp = max(0, target.hp - damage)
                return damage, "book"
        return 0, None

# 绘制小弟
def draw_minion(surface, x, y, minion, is_player):
    """绘制小弟"""
    minion_size = 30
    
    # 小弟图标
    icon = "👾"
    icon_font = pygame.font.Font(None, 24)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    
    # 小弟背景
    minion_color = ElementSystem.get_color(minion.element, (255, 215, 0))
    pygame.draw.circle(surface, minion_color, (x, y), minion_size // 2)
    pygame.draw.circle(surface, COLORS["text_white"], (x, y), minion_size // 2, 1)
    
    # 绘制图标
    icon_rect = icon_surf.get_rect(center=(x, y))
    surface.blit(icon_surf, icon_rect)
    
    # 血条
    hp_ratio = minion.hp / minion.max_hp
    hp_width = minion_size - 4
    hp_height = 4
    hp_x = x - hp_width // 2
    hp_y = y + minion_size // 2 + 5
    
    # 血条背景
    pygame.draw.rect(surface, COLORS["hp_bg"], (hp_x, hp_y, hp_width, hp_height), border_radius=2)
    
    # 血条
    if hp_ratio > 0:
        bar_width = int(hp_width * hp_ratio)
        hp_color = COLORS["hp_green"] if hp_ratio > 0.5 else COLORS["hp_red"]
        pygame.draw.rect(surface, hp_color, (hp_x, hp_y, bar_width, hp_height), border_radius=2)

# 绘制武将卡片
def draw_hero_card(surface, x, y, hero, is_player, font_normal, font_small):
    """绘制武将卡片"""
    card_width = 180
    card_height = 220

    # 卡片背景
    card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
    bg_color = (40, 60, 80, 200) if is_player else (80, 40, 40, 200)
    pygame.draw.rect(card_surf, bg_color, (0, 0, card_width, card_height), border_radius=15)
    surface.blit(card_surf, (x, y))

    # 边框
    border_color = ElementSystem.get_color(hero.element, (255, 215, 0))
    pygame.draw.rect(surface, border_color, (x, y, card_width, card_height), 2, border_radius=15)

    # 武将图标
    icon = HERO_ICONS.get(hero.name, "👤")
    icon_font = pygame.font.Font(None, 60)
    icon_surf = icon_font.render(icon, True, COLORS["text_white"])
    icon_rect = icon_surf.get_rect(center=(x + card_width // 2, y + 60))
    surface.blit(icon_surf, icon_rect)

    # 名称
    name_surf = font_normal.render(hero.name, True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(x + card_width // 2, y + 110))
    surface.blit(name_surf, name_rect)

    # 技能
    skill_surf = font_small.render(hero.skill["name"], True, COLORS["text_white"])
    skill_rect = skill_surf.get_rect(center=(x + card_width // 2, y + 140))
    surface.blit(skill_surf, skill_rect)

    # 元素
    element_surf = font_small.render(f"元素: {hero.element}", True, border_color)
    element_rect = element_surf.get_rect(center=(x + card_width // 2, y + 165))
    surface.blit(element_surf, element_rect)

    # 枪械信息
    if hero.gun:
        gun_info_text = f"🔫 {GUNS[hero.gun]['name']} {hero.gun_multiplier}x"
        gun_color = COLORS["accent_red"]
        gun_surf = font_small.render(gun_info_text, True, gun_color)
        gun_rect = gun_surf.get_rect(center=(x + card_width // 2, y + 185))
        surface.blit(gun_surf, gun_rect)
    
    # 羁绊信息
    if hero.active_bonds:
        bond_texts = []
        for bond_id in hero.active_bonds:
            bond_data = HERO_BONDS[bond_id]
            bond_texts.append(f"✨{bond_data['name']}")
        bond_display = " ".join(bond_texts)
        bond_surf = font_small.render(bond_display, True, COLORS["accent_gold"])
        bond_rect = bond_surf.get_rect(center=(x + card_width // 2, y + 205))
        surface.blit(bond_surf, bond_rect)
        # 调整小弟位置
        minion_y = y + card_height + 10
    else:
        # 小弟数量
        minion_count = sum(1 for m in hero.minions if m.hp > 0)
        minion_text = f"小弟: {minion_count}/{len(hero.minions)}"
        minion_surf = font_small.render(minion_text, True, COLORS["text_white"])
        minion_rect = minion_surf.get_rect(center=(x + card_width // 2, y + 205))
        surface.blit(minion_surf, minion_rect)

    # 血条
    hp_ratio = hero.hp / hero.max_hp
    hp_width = card_width - 30
    hp_height = 15
    hp_x = x + 15
    hp_y = y + card_height - 25

    # 血条背景
    pygame.draw.rect(surface, COLORS["hp_bg"], (hp_x, hp_y, hp_width, hp_height), border_radius=5)

    # 血条
    if hp_ratio > 0:
        bar_width = int(hp_width * hp_ratio)
        hp_color = COLORS["hp_green"] if hp_ratio > 0.5 else COLORS["hp_red"]
        pygame.draw.rect(surface, hp_color, (hp_x, hp_y, bar_width, hp_height), border_radius=5)

    # 边框
    pygame.draw.rect(surface, COLORS["text_white"], (hp_x, hp_y, hp_width, hp_height), 1, border_radius=5)

    # 生命值
    hp_text = f"{hero.hp}/{hero.max_hp}"
    hp_surf = font_small.render(hp_text, True, COLORS["text_white"])
    hp_rect = hp_surf.get_rect(center=(x + card_width // 2, y + card_height - 8))
    surface.blit(hp_surf, hp_rect)

    # 绘制小弟
    if hero.hp > 0:
        minion_x = x + 20
        minion_y_calc = y + card_height + 10
        for i, minion in enumerate(hero.minions):
            if minion.hp > 0:
                draw_minion(surface, minion_x, minion_y_calc, minion, is_player)
                minion_x += 40

# 绘制元素特效
def draw_element_effect(surface, center_x, center_y, element):
    """绘制元素特效"""
    color = ElementSystem.get_color(element, (255, 215, 0))
    
    # 元素粒子
    for i in range(8):
        radius = 5 + i * 3
        alpha = max(0, 200 - i * 25)
        effect_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(effect_surf, (*color[:3], alpha), (radius, radius), radius)
        surface.blit(effect_surf, (center_x - radius, center_y - radius))

# 武将阵营配置 - 从HERO_DATABASE动态构建（覆盖全部135名武将）
# 旧版仅21条静态数据，新版自动同步数据库的faction字段
_FACTION_CN_MAP = {k: v.get("name", "群") for k, v in HERO_FACTION_MAP.items()}
HERO_FACTIONS = {
    hero_name: _FACTION_CN_MAP.get(info.get("faction", "qun"), "群")
    for hero_name, info in HERO_DATABASE.items()
}

# 选择武将函数
def select_heroes(screen, font_title, font_normal, font_small):
    """选择上阵武将"""
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    # 获取可用武将
    available_heroes = list(data["heroes"].keys())
    if not available_heroes:
        # 如果没有武将，使用默认武将
        available_heroes = list(HERO_SKILLS.keys())[:3]
    
    # 选择的武将
    selected_heroes = []
    max_heroes = min(5, 1 + data["normal_dungeon"] // 2)
    
    # 按钮设置
    button_width = min(200, SCREEN_WIDTH * 0.3)
    button_height = min(50, SCREEN_HEIGHT * 0.07)
    button_spacing = min(15, SCREEN_HEIGHT * 0.025)
    
    # 主循环
    running = True
    scroll_offset = 0
    while running:
        mx, my = pygame.mouse.get_pos()
        
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        title_surf = font_title.render("选择上阵武将", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title_surf, title_rect)
        
        # 选择提示
        hint_surf = font_normal.render(f"请选择 {max_heroes} 个武将上阵", True, COLORS["text_white"])
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(hint_surf, hint_rect)
        
        # 绘制可用武将
        hero_buttons = []
        start_y = 120
        for i, hero_name in enumerate(available_heroes):
            y = start_y + i * (button_height + button_spacing) - scroll_offset
            if y > -button_height and y < SCREEN_HEIGHT - 100:
                # 检查是否已选择
                is_selected = hero_name in selected_heroes
                # 按钮颜色
                button_color = COLORS["accent_green"] if is_selected else COLORS["accent_blue"]
                hover_color = COLORS["accent_green"] if is_selected else COLORS["accent_blue"]
                
                # 创建按钮
                btn = AnimatedButton(
                    (SCREEN_WIDTH - button_width) // 2,
                    y,
                    button_width,
                    button_height,
                    f"{hero_name} (Lv.{data['heroes'].get(hero_name, {}).get('star', 1)})",
                    font_normal,
                    normal_color=button_color,
                    hover_color=hover_color
                )
                btn.update((mx, my))
                btn.draw(screen)
                hero_buttons.append((btn, hero_name))
        
        # 绘制已选择的武将
        selected_text = font_normal.render("已选择: " + ", ".join(selected_heroes) if selected_heroes else "已选择: 无", True, COLORS["text_white"])
        screen.blit(selected_text, (20, SCREEN_HEIGHT - 80))
        
        # 确认按钮
        confirm_btn = AnimatedButton(
            (SCREEN_WIDTH - button_width) // 2,
            SCREEN_HEIGHT - 60,
            button_width,
            button_height,
            "确认选择",
            font_normal,
            normal_color=COLORS["accent_green"],
            hover_color=COLORS["accent_green"]
        )
        confirm_btn.update((mx, my))
        confirm_btn.draw(screen)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return []
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 处理武将选择
                for btn, hero_name in hero_buttons:
                    if btn.rect.collidepoint(mx, my):
                        if hero_name in selected_heroes:
                            selected_heroes.remove(hero_name)
                        elif len(selected_heroes) < max_heroes:
                            selected_heroes.append(hero_name)
                # 处理确认按钮
                if confirm_btn.rect.collidepoint(mx, my) and len(selected_heroes) >= 1:
                    return selected_heroes
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset = max(0, scroll_offset - event.y * 30)
        
        pygame.display.flip()
        clock.tick(60)
    
    return []

# 选择宠物函数
def select_pet(screen, font_title, font_normal, font_small):
    """选择上阵宠物"""
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    # 获取可用宠物
    available_pets = []
    if 'pet' in data:
        available_pets.append(data['pet'])
    if 'pet_warehouse' in data:
        available_pets.extend(data['pet_warehouse'])
    
    # 过滤出等级够高的宠物（至少3级）
    available_pets = [pet for pet in available_pets if pet.get('level', 1) >= 3]
    
    # 如果没有符合条件的宠物，返回None
    if not available_pets:
        return None
    
    # 按钮设置
    button_width = min(250, SCREEN_WIDTH * 0.4)
    button_height = min(60, SCREEN_HEIGHT * 0.08)
    button_spacing = min(20, SCREEN_HEIGHT * 0.03)
    
    # 主循环
    running = True
    selected_pet = None
    while running:
        mx, my = pygame.mouse.get_pos()
        
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        title_surf = font_title.render("选择上阵宠物", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title_surf, title_rect)
        
        # 绘制可用宠物
        pet_buttons = []
        start_y = 100
        for i, pet_dict in enumerate(available_pets):
            y = start_y + i * (button_height + button_spacing)
            if y < SCREEN_HEIGHT - 100:
                # 宠物信息
                pet_name = pet_dict.get('name', '未知宠物')
                pet_level = pet_dict.get('level', 1)
                pet_type = pet_dict.get('type', '普通')
                
                # 按钮
                btn = AnimatedButton(
                    (SCREEN_WIDTH - button_width) // 2,
                    y,
                    button_width,
                    button_height,
                    f"{pet_name} (Lv.{pet_level}, {pet_type})",
                    font_normal,
                    normal_color=COLORS["accent_purple"],
                    hover_color=COLORS["accent_purple"]
                )
                btn.update((mx, my))
                btn.draw(screen)
                pet_buttons.append((btn, pet_dict))
        
        # 跳过按钮
        skip_btn = AnimatedButton(
            (SCREEN_WIDTH - button_width) // 2,
            SCREEN_HEIGHT - 60,
            button_width,
            button_height,
            "跳过选择",
            font_normal,
            normal_color=(100, 100, 150),
            hover_color=(120, 120, 180)
        )
        skip_btn.update((mx, my))
        skip_btn.draw(screen)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 处理宠物选择
                for btn, pet_dict in pet_buttons:
                    if btn.rect.collidepoint(mx, my):
                        selected_pet = pet_dict
                        return selected_pet
                # 处理跳过按钮
                if skip_btn.rect.collidepoint(mx, my):
                    return None
        
        pygame.display.flip()
        clock.tick(60)
    
    return None

def select_formation(screen, font_title, font_normal, font_small):
    """选择战斗阵型"""
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    # 按钮设置
    button_width = min(280, SCREEN_WIDTH * 0.45)
    button_height = min(50, SCREEN_HEIGHT * 0.07)
    button_spacing = min(15, SCREEN_HEIGHT * 0.02)
    
    running = True
    selected_formation = None
    while running:
        mx, my = pygame.mouse.get_pos()
        
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        title_surf = font_title.render("⚔️ 选择战斗阵型", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title_surf, title_rect)
        
        # 阵型列表
        formations = list(FormationSystem.FORMATIONS.items())
        formation_buttons = []
        start_y = 100
        
        for i, (form_id, form_data) in enumerate(formations):
            y = start_y + i * (button_height + button_spacing)
            if y < SCREEN_HEIGHT - 100:
                effects = form_data["effects"]
                desc = f"{form_data['name']} - 攻击{int((effects['attack_modifier']-1)*100):+d}% 防御{int((effects['defense_modifier']-1)*100):+d}% 速度{int((effects['speed_modifier']-1)*100):+d}%"
                
                btn = AnimatedButton(
                    (SCREEN_WIDTH - button_width) // 2,
                    y,
                    button_width,
                    button_height,
                    desc,
                    font_small,
                    normal_color=COLORS["accent_blue"],
                    hover_color=COLORS["accent_purple"]
                )
                btn.update((mx, my))
                btn.draw(screen)
                formation_buttons.append((btn, form_id))
                
                # 特殊效果提示
                special_y = y + button_height + 5
                special_surf = font_small.render(f"✨ {form_data['special']}", True, COLORS["accent_gold"])
                special_rect = special_surf.get_rect(x=(SCREEN_WIDTH - button_width) // 2 + 10, y=special_y)
                screen.blit(special_surf, special_rect)
        
        # 默认按钮（不选择阵型）
        default_btn = AnimatedButton(
            (SCREEN_WIDTH - button_width) // 2,
            SCREEN_HEIGHT - 60,
            button_width,
            button_height,
            "默认阵型",
            font_normal,
            normal_color=(100, 100, 150),
            hover_color=(120, 120, 180)
        )
        default_btn.update((mx, my))
        default_btn.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn, form_id in formation_buttons:
                    if btn.rect.collidepoint(mx, my):
                        selected_formation = form_id
                        return selected_formation
                if default_btn.rect.collidepoint(mx, my):
                    return None
        
        pygame.display.flip()
        clock.tick(60)
    
    return None

# 应用阵营增益
def apply_faction_bonus(heroes):
    """应用阵营增益"""
    # 统计各阵营的武将数量
    faction_count = {}
    for hero in heroes:
        faction = HERO_FACTIONS.get(hero.name, "无")
        faction_count[faction] = faction_count.get(faction, 0) + 1
    
    # 应用增益
    for hero in heroes:
        faction = HERO_FACTIONS.get(hero.name, "无")
        count = faction_count.get(faction, 0)
        if count >= 2:
            # 2个同阵营武将：攻击力+10%
            hero.skill["damage"] *= 1.1
        if count >= 3:
            # 3个同阵营武将：生命值+15%
            hero.max_hp *= 1.15
            hero.hp = hero.max_hp
        if count >= 4:
            # 4个同阵营武将：防御力+20%
            for minion in hero.minions:
                minion.max_hp *= 1.2
                minion.hp = minion.max_hp
        if count >= 5:
            # 5个同阵营武将：所有属性+25%
            hero.skill["damage"] *= 1.25
            hero.max_hp *= 1.25
            hero.hp = hero.max_hp
            for minion in hero.minions:
                minion.max_hp *= 1.25
                minion.hp = minion.max_hp
                minion.damage *= 1.25

# 应用宠物增益
def apply_pet_bonus(heroes, pet):
    """应用宠物增益"""
    if pet:
        # 根据宠物等级和属性提供增益
        level = pet.get('level', 1)
        attack_bonus = pet.get('attributes', {}).get('attack', 10) * 0.01
        defense_bonus = pet.get('attributes', {}).get('defense', 5) * 0.01
        speed_bonus = pet.get('attributes', {}).get('speed', 8) * 0.005
        
        for hero in heroes:
            # 攻击力增益
            hero.skill["damage"] *= (1 + attack_bonus * level * 0.1)
            # 生命值增益
            hero.max_hp *= (1 + defense_bonus * level * 0.1)
            hero.hp = hero.max_hp
            # 速度增益（影响攻击顺序）
            for minion in hero.minions:
                minion.damage *= (1 + speed_bonus * level * 0.1)

# 武将战斗主函数
def main():
    """武将回合制战斗主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
            pygame.mixer.init()
        
        # 分辨率适配
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            # 使用设置的分辨率（安全获取，避免KeyError）
            resolution = safe_get(data, ['settings', 'graphics', 'resolution'], "800x600")
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except (ValueError, AttributeError):
                log_error(f"Invalid resolution format: {resolution}")
                SCREEN_WIDTH = 800
                SCREEN_HEIGHT = 600
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("⚔️ 武将回合制战斗")
        clock = pygame.time.Clock()

        # 字体初始化
        def init_font(size):
            font_name = get_system_font_name()
            try:
                return pygame.font.SysFont(font_name, size)
            except Exception:
                return pygame.font.Font(None, size)

        font_title = init_font(36 if not 'ANDROID_DATA' in os.environ else 52)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        font_damage = init_font(32 if not 'ANDROID_DATA' in os.environ else 48)

        # 加载音效
        attack_sound = load_sound("attack.wav")
        win_sound = load_sound("win.wav")
        skill_sound = load_sound("skill.wav")

        def play_sound(sound):
            if sound and data['settings']['sound']['enable']:
                try:
                    sound.play()
                except Exception:
                    pass

        # 天气系统初始化
        weather_system = WeatherSystem()
        current_weather = weather_system.get_current_weather()
        weather_effects = weather_system.get_weather_effects()
        
        # 天气影响战斗的效果
        weather_bonus = {
            "晴天": {"attack_bonus": 0.1, "defense_bonus": 0.0},
            "多云": {"attack_bonus": 0.05, "defense_bonus": 0.05},
            "雨天": {"attack_bonus": -0.1, "defense_bonus": 0.1, "water_element_bonus": 0.2},
            "雷暴": {"attack_bonus": 0.15, "defense_bonus": -0.1, "thunder_damage": 20, "lightning_element_bonus": 0.3},
            "雪天": {"attack_bonus": -0.05, "defense_bonus": 0.15, "ice_element_bonus": 0.2}
        }

        def get_weather_bonus():
            """获取天气加成"""
            if current_weather:
                return weather_bonus.get(current_weather["name"], {})
            return {}

        def apply_weather_effects(heroes, is_player):
            """对武将应用天气效果"""
            bonus = get_weather_bonus()
            for hero in heroes:
                # 攻击力加成
                attack_bonus = bonus.get("attack_bonus", 0)
                hero.skill["damage"] *= (1 + attack_bonus)
                
                # 防御力加成（应用到小弟）
                defense_bonus = bonus.get("defense_bonus", 0)
                for minion in hero.minions:
                    minion.max_hp = int(minion.max_hp * (1 + defense_bonus))
                    minion.hp = minion.max_hp
                
                # 元素特定加成
                element_bonus_key = f"{hero.element}_element_bonus"
                if element_bonus_key in bonus:
                    hero.skill["damage"] *= (1 + bonus[element_bonus_key])

        # 获取玩家等级
        player_level = data["normal_dungeon"]
        
        # 选择上阵武将
        selected_hero_names = select_heroes(screen, font_title, font_normal, font_small)
        if not selected_hero_names:
            # 如果没有选择武将，返回
            return
        
        # 选择上阵宠物
        selected_pet = select_pet(screen, font_title, font_normal, font_small)
        
        # 选择战斗阵型
        selected_formation = select_formation(screen, font_title, font_normal, font_small)
        
        # 初始化装备技能（支持新格式：装备名称列表，兼容旧格式：数字索引）
        equip_skills = {}
        equip_stats = {}
        for equip_type in ["weapon", "armor", "horse", "book"]:
            equip_data = data["equips"].get(equip_type, [])
            
            # 兼容旧格式（数字索引）
            if isinstance(equip_data, int):
                equip_skills[equip_type] = EQUIP_SKILLS.get(equip_type, {}).get(equip_data, None)
                equip_stats[equip_type] = {}
            else:
                # 新格式（装备名称列表）- 使用最后一个装备（最新购买的）
                if equip_data and len(equip_data) > 0:
                    equip_name = equip_data[-1]
                    equip_info = EQUIPMENT_DATABASE.get(equip_name, {})
                    
                    # 获取装备强化等级（从equipment_system存储中读取）
                    enhance_level = 0
                    equipment_data = data.get("equipment", {})
                    equip_type_map = {
                        "weapon": "weapons",
                        "armor": "armors",
                        "horse": "accessories",
                        "book": "accessories"
                    }
                    storage_type = equip_type_map.get(equip_type, "accessories")
                    for equip in equipment_data.get(storage_type, []):
                        if equip.get("name") == equip_name:
                            enhance_level = equip.get("enhancement_level", 0)
                            break
                    
                    # 应用强化属性加成
                    enhance_bonus = EquipmentEnhanceSystem.get_enhance_bonus(enhance_level)
                    equip_stats[equip_type] = {
                        k: int(v * enhance_bonus) for k, v in equip_info.get("stats", {}).items()
                    }
                    
                    # 生成装备技能描述（包含强化等级）
                    stats_desc = ", ".join([f"{v}{k}" for k, v in equip_stats[equip_type].items()])
                    equip_skills[equip_type] = {
                        "name": f"{equip_name} +{enhance_level}",
                        "description": equip_info.get("description", f"装备效果：{stats_desc}"),
                        **equip_stats[equip_type]
                    }
                else:
                    equip_skills[equip_type] = None
                    equip_stats[equip_type] = {}
        
        # 玩家武将
        player_heroes = []
        for hero_name in selected_hero_names:
            hero_data = data["heroes"].get(hero_name, {})
            star = hero_data.get("star", 1)
            # 传入完整的hero_data，使Hero类能使用真实属性
            hero = Hero(hero_name, star, hero_data)
            # 分配装备技能
            hero.equip_skills = equip_skills.copy()
            
            # 应用装备属性加成
            for equip_type, stats in equip_stats.items():
                for stat_name, stat_value in stats.items():
                    if hasattr(hero, stat_name):
                        current_value = getattr(hero, stat_name)
                        setattr(hero, stat_name, current_value + stat_value)
            
            # 分配枪械
            if hero_name in data.get("hero_guns", {}):
                gun_info = data["hero_guns"][hero_name]
                hero.set_gun(gun_info.get("gun_type"))
                # 应用枪械升级倍率
                gun_level = gun_info.get("gun_level", 1)
                base_multiplier = GUNS[gun_info.get("gun_type")]["damage_multiplier"]
                hero.gun_multiplier = gun_info.get("gun_multiplier", base_multiplier)
            
            # 应用神兵效果
            for equip_type in ["weapon", "armor", "horse", "book"]:
                equip_data = data["equips"].get(equip_type, [])
                if equip_data and len(equip_data) > 0:
                    equip_name = equip_data[-1]
                    if is_divine_weapon(equip_name):
                        apply_divine_weapon(hero, equip_name)
            
            player_heroes.append(hero)
        
        # 应用武将羁绊效果
        all_player_hero_names = [h.name for h in player_heroes]
        for hero in player_heroes:
            hero.apply_bond_effects(all_player_hero_names)
        
        # 应用阵营增益
        apply_faction_bonus(player_heroes)
        
        # 应用宠物增益
        apply_pet_bonus(player_heroes, selected_pet)
        
        # 应用阵型效果
        if selected_formation:
            apply_formation(selected_formation, player_heroes)
        
        # 应用天气效果
        apply_weather_effects(player_heroes, True)
        
        # 敌人武将 - 增加难度梯度
        enemy_heroes = []
        enemy_names = list(HERO_SKILLS.keys())
        random.shuffle(enemy_names)
        
        # 敌人等级随着玩家等级提升而增加，但保持合理的难度梯度
        enemy_level = min(player_level, player_level // 2 + 3)
        
        for hero_name in enemy_names[:max_heroes]:
            # 从HERO_SKILLS获取完整的武将数据，使敌人使用真实属性
            hero_data = HERO_SKILLS.get(hero_name, {})
            hero = Hero(hero_name, enemy_level, hero_data)
            # 敌人装备技能随着难度提升而增强
            enemy_equip_skills = {
                "weapon": {"damage": 15 + player_level * 2, "defense": 0, "speed": 0, "critical": 0.1 + player_level * 0.01},
                "armor": {"damage": 0, "defense": 10 + player_level * 1.5, "speed": 0, "critical": 0},
                "horse": {"damage": 0, "defense": 0, "speed": 3 + player_level * 0.2, "critical": 0},
                "book": {"damage": 0, "defense": 0, "speed": 0, "critical": 0.2 + player_level * 0.01}
            }
            hero.equip_skills = enemy_equip_skills
            enemy_heroes.append(hero)
        
        # 应用天气效果到敌人
        apply_weather_effects(enemy_heroes, False)

        # 战斗数据
        turn = 0
        battle_over = False
        win = False
        animating = False
        animation_timer = 0
        current_attack = None  # (attacker, target, damage, element)
        victory_quote = ""
        defeat_quote = ""
        
        # 地形系统 - 随机选择战斗地形
        terrain = TerrainSystem.get_random_terrain()
        
        # 设置所有武将的地形属性
        for hero in player_heroes + enemy_heroes:
            hero.terrain = terrain
        
        # 应用地形属性修正
        for hero in player_heroes + enemy_heroes:
            hero.attack = int(hero.attack * TerrainSystem.get_attack_modifier(terrain, hero.element))
            hero.defense = int(hero.defense * TerrainSystem.get_defense_modifier(terrain, hero.element))
            hero.speed = int(hero.speed * TerrainSystem.get_speed_modifier(terrain, hero.element))
        
        # 战斗统计数据（用于评价计算）
        damage_dealt = 0
        damage_taken = 0
        reward_engine = None

        # 物资产出 - 增加稳定奖励和难度梯度
        base_reward = data["normal_dungeon"]
        # 随着难度增加，奖励逐渐提升，但保持稳定增长
        battle_rewards = {
            "水": int(10 * base_reward * (1 + base_reward * 0.05)),
            "煤炭": int(5 * base_reward * (1 + base_reward * 0.05)),
            "木头": int(8 * base_reward * (1 + base_reward * 0.05)),
            "食物": int(7 * base_reward * (1 + base_reward * 0.05)),
            "金元宝": int(2 * base_reward * (1 + base_reward * 0.08)),
            "普通子弹": int(5 * base_reward * (1 + base_reward * 0.03)),
            "高级子弹": int(3 * base_reward * (1 + base_reward * 0.02)),
            "稀有子弹": int(1 * base_reward * (1 + base_reward * 0.01))
        }

        # 增加额外奖励机会
        if random.random() < 0.3:
            # 有30%几率获得额外奖励
            extra_reward = random.choice(["水", "煤炭", "木头", "食物", "金元宝"])
            battle_rewards[extra_reward] += int(battle_rewards[extra_reward] * 0.5)

        # 特效
        particles = []
        floating_texts = []
        
        # 装备技能卡片
        skill_cards = []
        card_width = min(120, SCREEN_WIDTH * 0.15)
        card_height = min(80, SCREEN_HEIGHT * 0.12)
        card_y = SCREEN_HEIGHT - card_height - 30
        
        # 技能类型和颜色
        skill_info = [
            ("weapon", "⚔️ 武器", (200, 60, 60), (240, 90, 90)),
            ("armor", "🛡️ 防具", (60, 120, 60), (80, 160, 80)),
            ("horse", "🐎 坐骑", (60, 120, 200), (80, 160, 255)),
            ("book", "📚 书籍", (180, 100, 220), (200, 130, 255))
        ]
        
        for i, (skill_type, skill_name, normal_color, hover_color) in enumerate(skill_info):
            x = 50 + i * (card_width + 15)
            if x + card_width > SCREEN_WIDTH - 50:
                break
            card = AnimatedButton(
                x, card_y,
                card_width, card_height, skill_name, font_small,
                normal_color=normal_color, hover_color=hover_color
            )
            skill_cards.append((card, skill_type))

        # 武将技能卡片
        hero_skill_cards = []
        hero_card_width = min(150, SCREEN_WIDTH * 0.18)
        hero_card_height = min(80, SCREEN_HEIGHT * 0.12)
        hero_card_y = SCREEN_HEIGHT - hero_card_height - card_height - 50

        # 必杀技卡片
        ultimate_card_width = min(200, SCREEN_WIDTH * 0.25)
        ultimate_card_height = min(70, SCREEN_HEIGHT * 0.1)
        ultimate_card_y = SCREEN_HEIGHT - card_height - hero_card_height - ultimate_card_height - 70
        ultimate_card = AnimatedButton(
            (SCREEN_WIDTH - ultimate_card_width) // 2, ultimate_card_y,
            ultimate_card_width, ultimate_card_height, "🔥 必杀技", font_small,
            normal_color=(200, 50, 50), hover_color=(255, 80, 80)
        )


        # 返回按钮（提前创建）
        return_btn_width = min(180, SCREEN_WIDTH * 0.25)
        return_btn_height = min(50, SCREEN_HEIGHT * 0.08)
        return_btn_y = SCREEN_HEIGHT - return_btn_height - 30
        return_btn = AnimatedButton(
            (SCREEN_WIDTH - return_btn_width) // 2, return_btn_y,
            return_btn_width, return_btn_height, "↩️ 返回", font_normal,
            normal_color=(60, 150, 60), hover_color=(80, 200, 80)
        )

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 背景装饰
            for i in range(5):
                y = 100 + i * 100
                alpha = 20 + i * 10
                pygame.draw.line(screen, (*COLORS["accent_gold"][:3], alpha), (0, y), (SCREEN_WIDTH, y), 1)

            if not battle_over:
                # 标题
                title_surf = font_title.render("⚔️ 武将回合制战斗", True, COLORS["accent_gold"])
                title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
                screen.blit(title_surf, title_rect)
                
                # 回合数
                turn_surf = font_normal.render(f"第 {turn} 回合", True, COLORS["text_gray"])
                turn_rect = turn_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
                screen.blit(turn_surf, turn_rect)
                
                # 天气显示
                if current_weather:
                    weather_icon = {"晴天": "☀️", "多云": "☁️", "雨天": "🌧️", "雷暴": "⛈️", "雪天": "❄️"}.get(current_weather["name"], "🌤️")
                    weather_text = f"{weather_icon} {current_weather['name']}"
                    weather_surf = font_small.render(weather_text, True, current_weather["color"])
                    screen.blit(weather_surf, (20, 20))

                # 绘制玩家武将
                player_y = 120
                for i, hero in enumerate(player_heroes):
                    if hero.hp > 0:
                        x = 50 + i * 200
                        if x + 180 > SCREEN_WIDTH // 2:
                            break
                        draw_hero_card(screen, x, player_y, hero, True, font_normal, font_small)

                # 绘制敌人武将
                enemy_y = 120
                for i, hero in enumerate(enemy_heroes):
                    if hero.hp > 0:
                        x = SCREEN_WIDTH - 230 - i * 200
                        if x < SCREEN_WIDTH // 2:
                            break
                        draw_hero_card(screen, x, enemy_y, hero, False, font_normal, font_small)

                # 战斗特效
                if animating:
                    animation_timer += 1
                    if current_attack:
                        attacker, target, damage, element = current_attack
                        # 计算攻击位置
                        if hasattr(attacker, 'name'):  # 是武将
                            try:
                                if attacker in player_heroes:
                                    attacker_x = 50 + player_heroes.index(attacker) * 200 + 90
                                elif attacker in enemy_heroes:
                                    attacker_x = SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90
                                else:
                                    attacker_x = SCREEN_WIDTH // 2
                            except Exception:
                                attacker_x = SCREEN_WIDTH // 2
                        else:  # 是小弟
                            # 找到小弟所属的武将
                            attacker_x = SCREEN_WIDTH // 2
                            try:
                                for hero in player_heroes:
                                    if attacker in hero.minions:
                                        attacker_x = 50 + player_heroes.index(hero) * 200 + 90
                                        break
                                else:
                                    for hero in enemy_heroes:
                                        if attacker in hero.minions:
                                            attacker_x = SCREEN_WIDTH - 230 - enemy_heroes.index(hero) * 200 + 90
                                            break
                            except Exception:
                                pass
                        
                        try:
                            if target in player_heroes:
                                target_x = 50 + player_heroes.index(target) * 200 + 90
                            elif target in enemy_heroes:
                                target_x = SCREEN_WIDTH - 230 - enemy_heroes.index(target) * 200 + 90
                            else:
                                target_x = SCREEN_WIDTH // 2
                        except Exception:
                            target_x = SCREEN_WIDTH // 2
                        # 绘制攻击特效
                        draw_element_effect(screen, target_x, 230, element)
                    if animation_timer > 30:
                        animating = False
                        animation_timer = 0
                        current_attack = None

                # 武将技能卡片
            hero_skill_cards = []
            for i, hero in enumerate(player_heroes):
                if hero.hp > 0:
                    x = 50 + i * (hero_card_width + 15)
                    if x + hero_card_width > SCREEN_WIDTH - 50:
                        break
                    # 创建武将技能卡片
                    card = AnimatedButton(
                        x, hero_card_y,
                        hero_card_width, hero_card_height, f"{hero.name}: {hero.skill['name']}", font_small,
                        normal_color=ElementSystem.get_color(hero.element, (200, 150, 50)),
                        hover_color=ElementSystem.get_color(hero.element, (240, 190, 90))
                    )
                    if not animating:
                        card.update((mx, my))
                    card.draw(screen)
                    hero_skill_cards.append((card, hero))

            # 技能卡片
            for card, skill_type in skill_cards:
                if not animating:
                    card.update((mx, my))
                card.draw(screen)

            # 更新武将连击状态
            for hero in player_heroes + enemy_heroes:
                hero.update_combo()

            # 绘制连击显示
            combo_text = font_small.render(f"连击: {max(h.combo_count for h in player_heroes)}", True, COLORS["accent_gold"])
            screen.blit(combo_text, (SCREEN_WIDTH // 2 - 60, 50))

            # 绘制怒气条
            if player_heroes:
                main_hero = player_heroes[0]
                rage_ratio = main_hero.rage / main_hero.max_rage
                rage_width = 200
                rage_height = 20
                rage_x = SCREEN_WIDTH // 2 - rage_width // 2
                rage_y = 30
                
                pygame.draw.rect(screen, COLORS["hp_bg"], (rage_x, rage_y, rage_width, rage_height), border_radius=10)
                rage_bar_width = int(rage_width * rage_ratio)
                pygame.draw.rect(screen, (255, 100, 50), (rage_x, rage_y, rage_bar_width, rage_height), border_radius=10)
                pygame.draw.rect(screen, COLORS["text_white"], (rage_x, rage_y, rage_width, rage_height), 2, border_radius=10)
                
                rage_text = font_small.render(f"怒气: {main_hero.rage}/{main_hero.max_rage}", True, COLORS["text_white"])
                screen.blit(rage_text, (SCREEN_WIDTH // 2 - 50, rage_y - 20))

            # 必杀技按钮
            has_rage = any(h.can_use_ultimate() for h in player_heroes if h.hp > 0)
            if has_rage:
                ultimate_card.text = f"🔥 {main_hero.ultimate_skill['name']}"
                ultimate_card.normal_color = (255, 80, 80)
                ultimate_card.hover_color = (255, 120, 120)
            else:
                ultimate_card.text = "🔥 必杀技 (蓄力中)"
                ultimate_card.normal_color = (100, 50, 50)
                ultimate_card.hover_color = (120, 60, 60)
            
            if not animating:
                ultimate_card.update((mx, my))
                ultimate_card.draw(screen)

                # 武将信息
                hero_info_y = SCREEN_HEIGHT - card_height - hero_card_height - 130
                info_text = f"我方武将: {sum(1 for h in player_heroes if h.hp > 0)}/{len(player_heroes)}"
                info_surf = font_small.render(info_text, True, COLORS["text_white"])
                screen.blit(info_surf, (50, hero_info_y))

                info_text = f"敌方武将: {sum(1 for h in enemy_heroes if h.hp > 0)}/{len(enemy_heroes)}"
                info_surf = font_small.render(info_text, True, COLORS["text_white"])
                screen.blit(info_surf, (SCREEN_WIDTH - 200, hero_info_y))

                bullet_info_y = hero_info_y + 25
                for bullet_type in ["普通子弹", "高级子弹", "稀有子弹"]:
                    amount = data["resources"].get(bullet_type, 0)
                    bullet_icon = "🔫"
                    bullet_text = f"{bullet_icon} {bullet_type}: {amount}"
                    bullet_surf = font_small.render(bullet_text, True, COLORS["text_gray"])
                    screen.blit(bullet_surf, (50, bullet_info_y))
                    bullet_info_y += 20

                # 更新和绘制特效
                for p in particles[:]:
                    p.update()
                    p.draw(screen)
                    if p.life <= 0:
                        particles.remove(p)

                for ft in floating_texts[:]:
                    ft.update()
                    ft.draw(screen)
                    if ft.life <= 0:
                        floating_texts.remove(ft)

                # 事件处理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.MOUSEBUTTONDOWN and not animating:
                        # 必杀技按钮点击
                        if ultimate_card.rect.collidepoint(mx, my) and not battle_over:
                            play_sound(skill_sound)
                            animating = True
                            animation_timer = 0
                            
                            # 找到可以使用必杀技的武将
                            for hero in player_heroes:
                                if hero.hp > 0 and hero.can_use_ultimate():
                                    alive_enemies = [h for h in enemy_heroes if h.hp > 0]
                                    if alive_enemies:
                                        target = random.choice(alive_enemies)
                                        damage, success = hero.use_ultimate(target)
                                        if success:
                                            damage_dealt += damage
                                            current_attack = (hero, target, damage, hero.element)
                                            
                                            # 伤害数字（特殊效果）
                                            target_x = SCREEN_WIDTH - 230 - enemy_heroes.index(target) * 200 + 90
                                            damage_text = f"💥 -{int(damage)}"
                                            floating_texts.append(FloatingText(
                                                damage_text, target_x, 200,
                                                (255, 100, 50), font_damage
                                            ))
                                            
                                            # 必杀技特效 - 流星效果
                                            for _ in range(3):
                                                particles.append(Particle(
                                                    random.randint(0, SCREEN_WIDTH), 0,
                                                    (255, 150, 50), 0, 10, random.randint(30, 50)
                                                ))
                                            
                                            # 大量爆炸粒子
                                            for _ in range(50):
                                                particles.append(Particle(
                                                    target_x, 230,
                                                    (255, 200, 100), 8, random.randint(5, 15), 60
                                                ))
                                            
                                            # 检查敌人是否全部死亡
                                            if all(h.hp <= 0 for h in enemy_heroes):
                                                battle_over = True
                                                win = True
                                                play_sound(win_sound)
                                                for res, amt in battle_rewards.items():
                                                    data["resources"][res] = data["resources"].get(res, 0) + amt
                                                data["normal_dungeon"] += 1
                                                save()
                                                
                                                for _ in range(50):
                                                    particles.append(Particle(
                                                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                        COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                                    ))
                                            else:
                                                # 敌人回合
                                                for attacker in enemy_heroes:
                                                    if attacker.hp > 0:
                                                        alive_players = [h for h in player_heroes if h.hp > 0]
                                                        if alive_players:
                                                            target = random.choice(alive_players)
                                                            damage, attack_type = attacker.attack(target)
                                                            # 只统计实际造成的HP伤害（不包含护盾抵挡的伤害）
                                                            if attack_type != "shield":
                                                                damage_taken += damage
                                                            current_attack = (attacker, target, damage, attacker.element)
                                                            
                                                            target_x = 50 + player_heroes.index(target) * 200 + 90
                                                            if attack_type == "shield":
                                                                damage_text = f"🛡️ -{int(damage)}"
                                                            else:
                                                                damage_text = f"-{int(damage)}"
                                                            floating_texts.append(FloatingText(
                                                                damage_text, target_x, 200,
                                                                ElementSystem.get_color(attacker.element, COLORS["accent_red"]), font_damage
                                                            ))
                                                            
                                                            draw_element_effect(screen, target_x, 230, attacker.element)
                                                            
                                                            if all(h.hp <= 0 for h in player_heroes):
                                                                battle_over = True
                                                                win = False
                                                                break
                                                        else:
                                                            battle_over = True
                                                            win = False
                                                            break
                                            
                                            turn += 1
                                            
                                            # 玩家回合开始时应用被动技能效果
                                            alive_allies = [h for h in player_heroes if h.hp > 0]
                                            for hero in player_heroes:
                                                if hero.hp > 0:
                                                    passive_messages = hero.apply_passive_effects(allies=alive_allies)
                                                    for msg in passive_messages:
                                                        hero_x = 50 + player_heroes.index(hero) * 200 + 90
                                                        floating_texts.append(FloatingText(
                                                            msg, hero_x, 200,
                                                            COLORS["accent_green"], font_small
                                                        ))
                                            break
                            break
                        
                        # 武将技能卡片点击
                        for card, hero in hero_skill_cards:
                            if card.rect.collidepoint(mx, my) and not battle_over:
                                play_sound(skill_sound)
                                animating = True
                                animation_timer = 0
                                
                                # 玩家使用武将技能（大招）
                                if hero.hp > 0:
                                    # 选择一个活着的敌人
                                    alive_enemies = [h for h in enemy_heroes if h.hp > 0]
                                    if alive_enemies:
                                        target = random.choice(alive_enemies)
                                        # 使用武将的大招（技能）
                                        damage, attack_type = hero.attack(target)
                                        damage *= hero.get_combo_bonus()
                                        hero.add_combo()
                                        hero.add_rage()
                                        if damage > 0:
                                            damage_dealt += damage
                                            current_attack = (hero, target, damage, hero.element)
                                            
                                            # 伤害数字
                                            target_x = SCREEN_WIDTH - 230 - enemy_heroes.index(target) * 200 + 90
                                            damage_text = f"-{int(damage)}"
                                            floating_texts.append(FloatingText(
                                                damage_text, target_x, 200,
                                                ElementSystem.get_color(hero.element, COLORS["accent_red"]), font_damage
                                            ))
                                            
                                            # 技能特效
                                            draw_element_effect(screen, target_x, 230, hero.element)
                                            
                                            # 技能粒子
                                            for _ in range(20):
                                                angle = math.atan2(230 - 230, target_x - (50 + player_heroes.index(hero) * 200 + 90))
                                                particles.append(Particle(
                                                    50 + player_heroes.index(hero) * 200 + 90,
                                                    230,
                                                    ElementSystem.get_color(hero.element, COLORS["accent_red"]),
                                                    6, random.randint(5, 10), 50, angle
                                                ))
                                            
                                            # 检查击杀触发被动技能
                                            if target.hp <= 0:
                                                passive_messages = hero.trigger_passive_on_kill(target)
                                                for msg in passive_messages:
                                                    floating_texts.append(FloatingText(
                                                        msg, target_x, 200,
                                                        COLORS["accent_green"], font_small
                                                    ))
                                            
                                            # 小弟攻击
                                            for minion in hero.minions:
                                                if minion.hp > 0:
                                                    damage = minion.attack(target)
                                                    damage_dealt += damage
                                                    current_attack = (minion, target, damage, minion.element)
                                                    
                                                    # 伤害数字
                                                    damage_text = f"-{damage}"
                                                    floating_texts.append(FloatingText(
                                                        damage_text, target_x, 200,
                                                        ElementSystem.get_color(minion.element, COLORS["accent_red"]), font_small
                                                    ))
                                                    
                                                    # 攻击粒子
                                                    for _ in range(8):
                                                        angle = math.atan2(230 - 230, target_x - (50 + player_heroes.index(hero) * 200 + 90))
                                                        particles.append(Particle(
                                                            50 + player_heroes.index(hero) * 200 + 90,
                                                            230,
                                                            ElementSystem.get_color(minion.element, COLORS["accent_red"]),
                                                            3, random.randint(3, 5), 30, angle
                                                        ))
                                            
                                            # 检查敌人是否全部死亡
                                            if all(h.hp <= 0 for h in enemy_heroes):
                                                battle_over = True
                                                win = True
                                                play_sound(win_sound)
                                                # 发放奖励
                                                for res, amt in battle_rewards.items():
                                                    data["resources"][res] = data["resources"].get(res, 0) + amt
                                                data["normal_dungeon"] += 1
                                                save()
                                                
                                                # 胜利特效
                                                for _ in range(50):
                                                    particles.append(Particle(
                                                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                        COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                                    ))
                                            else:
                                                # 敌人回合
                                                for attacker in enemy_heroes:
                                                    if attacker.hp > 0:
                                                        alive_players = [h for h in player_heroes if h.hp > 0]
                                                        alive_enemies = [e for e in enemy_heroes if e.hp > 0]
                                                        if alive_players:
                                                            # 使用AI战术决策系统选择目标和行动
                                                            action_type, target = AITacticalDecision.choose_action(
                                                                attacker, alive_enemies, alive_players
                                                            )
                                                            
                                                            if action_type == "ultimate" and target:
                                                                damage, success = attacker.use_ultimate(target)
                                                                if success and damage > 0:
                                                                    current_attack = (attacker, target, damage, attacker.element)
                                                                    target_x = 50 + player_heroes.index(target) * 200 + 90
                                                                    floating_texts.append(FloatingText(
                                                                        f"💥 -{int(damage)}", target_x, 200,
                                                                        COLORS["accent_gold"], font_damage
                                                                    ))
                                                            elif action_type == "tactical" and target:
                                                                tactical_messages = attacker.use_tactical(alive_enemies, alive_players)
                                                                if tactical_messages:
                                                                    for msg in tactical_messages:
                                                                        attacker.battle_log.append(msg)
                                                            elif action_type == "defend":
                                                                attacker.add_buff("defense_up", 1, 0.3)
                                                            elif action_type == "attack" and target:
                                                                damage, attack_type = attacker.attack(target)
                                                                if damage > 0:
                                                                    current_attack = (attacker, target, damage, attacker.element)
                                                                    target_x = 50 + player_heroes.index(target) * 200 + 90
                                                                    if attack_type == "shield":
                                                                        damage_text = f"🛡️ -{int(damage)}"
                                                                    else:
                                                                        damage_text = f"-{int(damage)}"
                                                                    floating_texts.append(FloatingText(
                                                                        damage_text, target_x, 200,
                                                                        ElementSystem.get_color(attacker.element, COLORS["accent_red"]), font_damage
                                                                    ))
                                                                
                                                                # 技能特效
                                                                draw_element_effect(screen, target_x, 230, attacker.element)
                                                                
                                                                # 技能粒子
                                                                for _ in range(20):
                                                                    angle = math.atan2(230 - 230, target_x - (SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90))
                                                                    particles.append(Particle(
                                                                        SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90,
                                                                        230,
                                                                        ElementSystem.get_color(attacker.element, COLORS["accent_red"]),
                                                                        6, random.randint(5, 10), 50, angle
                                                                    ))
                                                                
                                                                # 小弟攻击
                                                                for minion in attacker.minions:
                                                                    if minion.hp > 0:
                                                                        damage = minion.attack(target)
                                                                        current_attack = (minion, target, damage, minion.element)
                                                                        
                                                                        # 伤害数字
                                                                        damage_text = f"-{damage}"
                                                                        floating_texts.append(FloatingText(
                                                                            damage_text, target_x, 200,
                                                                            ElementSystem.get_color(minion.element, COLORS["accent_red"]), font_small
                                                                        ))
                                                                        
                                                                        # 攻击粒子
                                                                        for _ in range(8):
                                                                            angle = math.atan2(230 - 230, target_x - (SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90))
                                                                            particles.append(Particle(
                                                                                SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90,
                                                                                230,
                                                                                ElementSystem.get_color(minion.element, COLORS["accent_red"]),
                                                                                3, random.randint(3, 5), 30, angle
                                                                            ))
                                                                
                                                                # 检查玩家是否全部死亡
                                                                if all(h.hp <= 0 for h in player_heroes):
                                                                    battle_over = True
                                                                    win = False
                                                                    # 失败特效
                                                                    for _ in range(30):
                                                                        particles.append(Particle(
                                                                            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                                            COLORS["accent_red"], 6, random.randint(3, 8), 60
                                                                        ))
                                                                    break
                                                        else:
                                                            # 没有玩家了
                                                            battle_over = True
                                                            win = False
                                                            # 失败特效
                                                            for _ in range(30):
                                                                particles.append(Particle(
                                                                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                                    COLORS["accent_red"], 6, random.randint(3, 8), 60
                                                                ))
                                                            break
                                            
                                            # 回合结束 - 处理元素效果和Buff/Debuff
                                            for hero in player_heroes + enemy_heroes:
                                                if hero.hp > 0:
                                                    # 处理灼烧效果
                                                    if hero.burn_turns > 0:
                                                        burn_dmg = hero.burn_damage
                                                        hero.hp = max(0, hero.hp - burn_dmg)
                                                        floating_texts.append(FloatingText(
                                                            f"🔥 灼烧 -{burn_dmg}", SCREEN_WIDTH // 2, 300,
                                                            COLORS["accent_red"], font_small
                                                        ))
                                                        hero.burn_turns -= 1
                                                    
                                                    # 处理中毒效果
                                                    if hero.is_poisoned:
                                                        poison_dmg = hero.poison_damage
                                                        hero.hp = max(0, hero.hp - poison_dmg)
                                                        floating_texts.append(FloatingText(
                                                            f"☠️ 中毒 -{poison_dmg}", SCREEN_WIDTH // 2, 320,
                                                            (100, 200, 100), font_small
                                                        ))
                                                    
                                                    # 更新Buff和Debuff状态
                                                    hero.update_buffs_debuffs()
                                                    
                                                    # 处理减速
                                                    if hero.slow_turns > 0:
                                                        hero.slow_turns -= 1
                                            
                                            # 回合结束
                                            turn += 1
                                    else:
                                        # 没有敌人了
                                        battle_over = True
                                        win = True
                                        play_sound(win_sound)
                                        # 使用奖励引擎计算所有奖励
                                        reward_engine = BattleRewardEngine()
                                        battle_rewards = reward_engine.calculate_rewards(
                                            player_heroes, enemy_heroes, turn, damage_dealt, damage_taken, player_level
                                        )
                                        # 发放奖励
                                        for res, amt in battle_rewards.items():
                                            data["resources"][res] = data["resources"].get(res, 0) + amt
                                        data["normal_dungeon"] += 1
                                        save()
                                        
                                        # 胜利特效
                                        for _ in range(50):
                                            particles.append(Particle(
                                                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                            ))
                        
                        # 技能卡片点击
                        for card, skill_type in skill_cards:
                            if card.rect.collidepoint(mx, my) and not battle_over:
                                play_sound(skill_sound)
                                animating = True
                                animation_timer = 0
                                
                                # 玩家使用装备技能
                                for attacker in player_heroes:
                                    if attacker.hp > 0:
                                        # 选择一个活着的敌人
                                        alive_enemies = [h for h in enemy_heroes if h.hp > 0]
                                        if alive_enemies:
                                            target = random.choice(alive_enemies)
                                            damage, skill_effect = attacker.use_skill(skill_type, target)
                                            if damage > 0:
                                                current_attack = (attacker, target, damage, attacker.element)
                                                
                                                # 伤害数字
                                                target_x = SCREEN_WIDTH - 230 - enemy_heroes.index(target) * 200 + 90
                                                if skill_type == "armor":
                                                    # 防具技能：恢复
                                                    damage_text = f"+{int(damage)}"
                                                    floating_texts.append(FloatingText(
                                                        damage_text, 50 + player_heroes.index(attacker) * 200 + 90, 200,
                                                        COLORS["accent_green"], font_damage, False
                                                    ))
                                                else:
                                                    # 其他技能：伤害
                                                    damage_text = f"-{int(damage)}"
                                                    floating_texts.append(FloatingText(
                                                        damage_text, target_x, 200,
                                                        ElementSystem.get_color(attacker.element, COLORS["accent_red"]), font_damage
                                                    ))
                                                
                                                # 技能特效
                                                if skill_effect:
                                                    draw_skill_effect(screen, 50 + player_heroes.index(attacker) * 200 + 90, 230, skill_effect)
                                                
                                                # 技能粒子
                                                for _ in range(20):
                                                    angle = math.atan2(230 - 230, target_x - (50 + player_heroes.index(attacker) * 200 + 90))
                                                    particles.append(Particle(
                                                        50 + player_heroes.index(attacker) * 200 + 90,
                                                        230,
                                                        ElementSystem.get_color(attacker.element, COLORS["accent_red"]),
                                                        6, random.randint(5, 10), 50, angle
                                                    ))
                                                
                                                # 检查敌人是否全部死亡
                                                if all(h.hp <= 0 for h in enemy_heroes):
                                                    battle_over = True
                                                    win = True
                                                    play_sound(win_sound)
                                                    # 发放奖励
                                                    for res, amt in battle_rewards.items():
                                                        data["resources"][res] = data["resources"].get(res, 0) + amt
                                                    data["normal_dungeon"] += 1
                                                    save()
                                                    
                                                    # 胜利特效
                                                    for _ in range(50):
                                                        particles.append(Particle(
                                                            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                            COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                                        ))
                                                    break
                                        else:
                                            # 没有敌人了
                                            battle_over = True
                                            win = True
                                            play_sound(win_sound)
                                            # 发放奖励
                                            for res, amt in battle_rewards.items():
                                                data["resources"][res] = data["resources"].get(res, 0) + amt
                                            data["normal_dungeon"] += 1
                                            save()
                                            
                                            # 胜利特效
                                            for _ in range(50):
                                                particles.append(Particle(
                                                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                                    COLORS["accent_gold"], 8, random.randint(5, 10), 80
                                                ))
                                            break
                                
                                # 敌人回合
                                if not battle_over:
                                    for attacker in enemy_heroes:
                                        if attacker.hp > 0:
                                            # 选择一个活着的玩家武将
                                            alive_players = [h for h in player_heroes if h.hp > 0]
                                            if alive_players:
                                                target = random.choice(alive_players)
                                                # 敌人也使用技能
                                                skill_types = ["weapon", "armor", "horse", "book"]
                                                skill_type = random.choice(skill_types)
                                                damage, skill_effect = attacker.use_skill(skill_type, target)
                                                if damage > 0:
                                                    current_attack = (attacker, target, damage, attacker.element)
                                                    
                                                    # 伤害数字
                                                    target_x = 50 + player_heroes.index(target) * 200 + 90
                                                    if skill_type == "armor":
                                                        # 防具技能：恢复
                                                        damage_text = f"+{int(damage)}"
                                                        floating_texts.append(FloatingText(
                                                            damage_text, SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90, 200,
                                                            COLORS["accent_green"], font_damage, False
                                                        ))
                                                    else:
                                                        # 其他技能：伤害
                                                        damage_text = f"-{int(damage)}"
                                                        floating_texts.append(FloatingText(
                                                            damage_text, target_x, 200,
                                                            ElementSystem.get_color(attacker.element, COLORS["accent_red"]), font_damage
                                                        ))
                                                    
                                                    # 技能特效
                                                    if skill_effect:
                                                        draw_skill_effect(screen, SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90, 230, skill_effect)
                                                    
                                                    # 技能粒子
                                                    for _ in range(20):
                                                        angle = math.atan2(230 - 230, target_x - (SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90))
                                                        particles.append(Particle(
                                                            SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90,
                                                            230,
                                                            ElementSystem.get_color(attacker.element, COLORS["accent_red"]),
                                                            6, random.randint(5, 10), 50, angle
                                                        ))
                                                    
                                                    # 检查玩家是否全部死亡
                                                    if all(h.hp <= 0 for h in player_heroes):
                                                        battle_over = True
                                                        win = False
                                                        break
                                                else:
                                                    # 如果技能没有效果，使用普通攻击
                                                    damage = attacker.attack(target)
                                                    current_attack = (attacker, target, damage, attacker.element)
                                                    
                                                    # 伤害数字
                                                    target_x = 50 + player_heroes.index(target) * 200 + 90
                                                    damage_text = f"-{damage}"
                                                    floating_texts.append(FloatingText(
                                                        damage_text, target_x, 200,
                                                        ElementSystem.get_color(attacker.element, COLORS["accent_red"]), font_damage
                                                    ))
                                                    
                                                    # 攻击粒子
                                                    for _ in range(15):
                                                        angle = math.atan2(230 - 230, target_x - (SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90))
                                                        particles.append(Particle(
                                                            SCREEN_WIDTH - 230 - enemy_heroes.index(attacker) * 200 + 90,
                                                            230,
                                                            ElementSystem.get_color(attacker.element, COLORS["accent_red"]),
                                                            5, random.randint(4, 8), 40, angle
                                                        ))
                                                        
                                                    # 检查玩家是否全部死亡
                                                    if all(h.hp <= 0 for h in player_heroes):
                                                        battle_over = True
                                                        win = False
                                                        break
                                            else:
                                                # 没有玩家了
                                                battle_over = True
                                                win = False
                                                break
                                
                                turn += 1
                                break
                        

            else:
                # 战斗结果
                if win:
                    if reward_engine:
                        reward_engine.draw_reward_panel(screen, font_title, font_normal, font_small)
                    else:
                        # 兼容旧版
                        win_surf = font_title.render("🎉 战斗胜利！", True, COLORS["accent_green"])
                        win_rect = win_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
                        screen.blit(win_surf, win_rect)
                        
                        panel_y = 140
                        panel_surf = pygame.Surface((400, 280), pygame.SRCALPHA)
                        pygame.draw.rect(panel_surf, (40, 40, 70, 200), (0, 0, 400, 280), border_radius=15)
                        screen.blit(panel_surf, ((SCREEN_WIDTH - 400) // 2, panel_y))
                        pygame.draw.rect(screen, COLORS["accent_gold"], 
                                       ((SCREEN_WIDTH - 400) // 2, panel_y, 400, 280), 2, border_radius=15)
                        
                        reward_title = font_normal.render("💎 获得奖励", True, COLORS["accent_gold"])
                        screen.blit(reward_title, ((SCREEN_WIDTH - 400) // 2 + 20, panel_y + 20))
                        
                        y_offset = panel_y + 70
                        for res, amt in battle_rewards.items():
                            icon = {"水": "💧", "煤炭": "⚫", "木头": "🪵", "食物": "🍞", "金元宝": "💰", "普通子弹": "🔫", "高级子弹": "🔫🔫", "稀有子弹": "🔫🔥"}.get(res, "📦")
                            reward_text = font_small.render(f"{icon} {res} × {amt}", True, COLORS["text_white"])
                            screen.blit(reward_text, ((SCREEN_WIDTH - 400) // 2 + 40, y_offset))
                            y_offset += 40
                    
                    # 意味深长的话
                    if not victory_quote:
                        victory_quote = random.choice(VICTORY_QUOTES)
                    quote_surf = font_small.render(victory_quote, True, COLORS["accent_gold"])
                    quote_rect = quote_surf.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 300))
                    screen.blit(quote_surf, quote_rect)
                else:
                    # 失败标题
                    lose_surf = font_title.render("💀 战斗失败！", True, COLORS["accent_red"])
                    lose_rect = lose_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
                    screen.blit(lose_surf, lose_rect)
                    
                    hint_surf = font_normal.render("请重新挑战", True, COLORS["text_gray"])
                    hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, 220))
                    screen.blit(hint_surf, hint_rect)
                    
                    # 意味深长的话
                    if not defeat_quote:
                        defeat_quote = random.choice(DEFEAT_QUOTES)
                    quote_surf = font_small.render(defeat_quote, True, COLORS["text_white"])
                    quote_rect = quote_surf.get_rect(center=(SCREEN_WIDTH // 2, 290))
                    screen.blit(quote_surf, quote_rect)

                # 返回按钮（使用预先创建的按钮）
                return_btn.update((mx, my))
                return_btn.draw(screen)

                # 特效
                for p in particles[:]:
                    p.update()
                    p.draw(screen)
                    if p.life <= 0:
                        particles.remove(p)

                # 事件处理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if return_btn.rect.collidepoint(mx, my):
                            running = False

            pygame.display.flip()
            clock.tick(60)

        # 确保退出时更新统计
        if battle_over:
            update_battle_stats(win, player_heroes, enemy_heroes, damage_dealt, damage_taken)
        
        safe_exit("战斗模块")
    except Exception as e:
        safe_exit("战斗模块", str(e))

if __name__ == "__main__":
    main()
