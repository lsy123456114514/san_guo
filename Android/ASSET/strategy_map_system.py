import pygame
import math
import random
import json
import time
from ASSET.game_data import data, save, get_system_font_name
from ASSET import safe_exit

class TerritoryManager:
    """领土管理系统"""
    
    def __init__(self):
        # 确保数据存在
        if "territory" not in data:
            data["territory"] = {
                "owned_territories": [],
                "territory_levels": {},
                "resource_production": {},
                "garrisons": {},
                "last_collection_time": 0,
                "total_power": 0
            }
        
        self.territories = self._load_territory_data()
        self.production_interval = 300  # 5分钟收集一次
        self._update_total_power()
    
    def _load_territory_data(self):
        """加载领土数据"""
        return [
            # 中原地区
            {"id": "zhou", "name": "豫州", "x": 400, "y": 350, "type": "city", "base_production": {"金元宝": 100, "粮食": 50}, "defense": 500, "faction": "neutral"},
            {"id": "yan", "name": "兖州", "x": 450, "y": 300, "type": "city", "base_production": {"金元宝": 80, "粮食": 60}, "defense": 400, "faction": "neutral"},
            {"id": "qing", "name": "青州", "x": 500, "y": 250, "type": "city", "base_production": {"金元宝": 90, "粮食": 45}, "defense": 450, "faction": "neutral"},
            {"id": "ji", "name": "冀州", "x": 550, "y": 280, "type": "city", "base_production": {"金元宝": 120, "粮食": 55}, "defense": 550, "faction": "neutral"},
            {"id": "bing", "name": "并州", "x": 520, "y": 330, "type": "city", "base_production": {"金元宝": 70, "粮食": 50}, "defense": 380, "faction": "neutral"},
            {"id": "you", "name": "幽州", "x": 600, "y": 260, "type": "city", "base_production": {"金元宝": 60, "粮食": 40}, "defense": 350, "faction": "neutral"},
            
            # 关中地区
            {"id": "yong", "name": "雍州", "x": 280, "y": 320, "type": "city", "base_production": {"金元宝": 110, "粮食": 70}, "defense": 580, "faction": "neutral"},
            {"id": "liang", "name": "凉州", "x": 200, "y": 300, "type": "city", "base_production": {"金元宝": 50, "粮食": 35}, "defense": 320, "faction": "neutral"},
            {"id": "hanzhong", "name": "汉中", "x": 300, "y": 380, "type": "city", "base_production": {"金元宝": 65, "粮食": 55}, "defense": 360, "faction": "neutral"},
            
            # 江南地区
            {"id": "yang", "name": "扬州", "x": 480, "y": 450, "type": "city", "base_production": {"金元宝": 130, "粮食": 80}, "defense": 600, "faction": "neutral"},
            {"id": "jing", "name": "荆州", "x": 380, "y": 420, "type": "city", "base_production": {"金元宝": 95, "粮食": 75}, "defense": 480, "faction": "neutral"},
            {"id": "yue", "name": "交州", "x": 420, "y": 520, "type": "city", "base_production": {"金元宝": 45, "粮食": 45}, "defense": 280, "faction": "neutral"},
            
            # 巴蜀地区
            {"id": "shu", "name": "益州", "x": 280, "y": 450, "type": "city", "base_production": {"金元宝": 85, "粮食": 90}, "defense": 420, "faction": "neutral"},
            {"id": "nanzhong", "name": "南中", "x": 250, "y": 500, "type": "city", "base_production": {"金元宝": 35, "粮食": 30}, "defense": 220, "faction": "neutral"},
            
            # 资源点
            {"id": "mine_1", "name": "铁矿", "x": 350, "y": 280, "type": "mine", "base_production": {"铁矿": 30}, "defense": 150, "faction": "neutral"},
            {"id": "mine_2", "name": "铜矿", "x": 480, "y": 380, "type": "mine", "base_production": {"铜矿": 25}, "defense": 120, "faction": "neutral"},
            {"id": "farm_1", "name": "良田", "x": 380, "y": 350, "type": "farm", "base_production": {"粮食": 60}, "defense": 80, "faction": "neutral"},
            {"id": "farm_2", "name": "粮仓", "x": 450, "y": 420, "type": "farm", "base_production": {"粮食": 80}, "defense": 100, "faction": "neutral"},
            {"id": "forest_1", "name": "林场", "x": 520, "y": 380, "type": "forest", "base_production": {"木材": 40}, "defense": 90, "faction": "neutral"},
            {"id": "port_1", "name": "港口", "x": 550, "y": 480, "type": "port", "base_production": {"金元宝": 50}, "defense": 180, "faction": "neutral"}
        ]
    
    def _update_total_power(self):
        """更新总战力"""
        total = 0
        for territory_id in data["territory"]["owned_territories"]:
            territory = self.get_territory(territory_id)
            if territory:
                level = data["territory"]["territory_levels"].get(territory_id, 1)
                total += territory["defense"] * level
        data["territory"]["total_power"] = total
        save()
    
    def get_territory(self, territory_id):
        """获取领土信息"""
        return next((t for t in self.territories if t["id"] == territory_id), None)
    
    def is_owned(self, territory_id):
        """检查是否拥有领土"""
        return territory_id in data["territory"]["owned_territories"]
    
    def occupy_territory(self, territory_id, player_power):
        """占领领土"""
        territory = self.get_territory(territory_id)
        if not territory:
            return False, "领土不存在"
        
        if self.is_owned(territory_id):
            return False, "已拥有该领土"
        
        # 检查战力是否足够
        defense = territory["defense"]
        if player_power < defense:
            return False, f"战力不足！需要{defense}战力"
        
        # 占领领土
        data["territory"]["owned_territories"].append(territory_id)
        data["territory"]["territory_levels"][territory_id] = 1
        data["territory"]["garrisons"][territory_id] = player_power // 2
        
        # 更新领土所属势力
        for t in self.territories:
            if t["id"] == territory_id:
                t["faction"] = "player"
        
        self._update_total_power()
        save()
        
        return True, f"成功占领{territory['name']}！"
    
    def upgrade_territory(self, territory_id):
        """升级领土"""
        if territory_id not in data["territory"]["owned_territories"]:
            return False, "未拥有该领土"
        
        current_level = data["territory"]["territory_levels"].get(territory_id, 1)
        if current_level >= 10:
            return False, "已达到最高等级"
        
        # 计算升级费用
        cost = {"金元宝": current_level * 500, "粮食": current_level * 200}
        
        # 检查资源是否足够
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"{resource}不足！需要{amount}"
        
        # 消耗资源
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        # 升级
        data["territory"]["territory_levels"][territory_id] = current_level + 1
        self._update_total_power()
        save()
        
        return True, f"升级成功！当前等级: {current_level + 1}"
    
    def collect_resources(self):
        """收集所有领土产出"""
        current_time = time.time()
        if current_time - data["territory"]["last_collection_time"] < self.production_interval:
            remaining = int((self.production_interval - (current_time - data["territory"]["last_collection_time"])) // 60)
            return False, f"资源尚未产出，还剩{remaining}分钟"
        
        total_collected = {}
        
        for territory_id in data["territory"]["owned_territories"]:
            territory = self.get_territory(territory_id)
            if not territory:
                continue
            
            level = data["territory"]["territory_levels"].get(territory_id, 1)
            
            for resource, base_amount in territory["base_production"].items():
                amount = base_amount * level
                
                if resource in data["resources"]:
                    data["resources"][resource] += amount
                else:
                    data["resources"][resource] = amount
                
                total_collected[resource] = total_collected.get(resource, 0) + amount
        
        data["territory"]["last_collection_time"] = current_time
        save()
        
        return True, total_collected
    
    def get_all_territories(self):
        """获取所有领土状态"""
        result = []
        for territory in self.territories:
            owned = self.is_owned(territory["id"])
            level = data["territory"]["territory_levels"].get(territory["id"], 1) if owned else 0
            garrison = data["territory"]["garrisons"].get(territory["id"], 0)
            
            result.append({
                "id": territory["id"],
                "name": territory["name"],
                "x": territory["x"],
                "y": territory["y"],
                "type": territory["type"],
                "base_production": territory["base_production"],
                "defense": territory["defense"],
                "faction": territory["faction"],
                "owned": owned,
                "level": level,
                "garrison": garrison
            })
        
        return result
    
    def get_owned_territories(self):
        """获取已拥有的领土"""
        return [t for t in self.get_all_territories() if t["owned"]]
    
    def get_production_rate(self):
        """获取总产出率"""
        production = {}
        
        for territory in self.get_owned_territories():
            level = territory["level"]
            for resource, base_amount in territory["base_production"].items():
                production[resource] = production.get(resource, 0) + base_amount * level
        
        return production
    
    def reinforce_garrison(self, territory_id, power):
        """增援驻军"""
        if territory_id not in data["territory"]["owned_territories"]:
            return False, "未拥有该领土"
        
        current_garrison = data["territory"]["garrisons"].get(territory_id, 0)
        data["territory"]["garrisons"][territory_id] = current_garrison + power
        
        self._update_total_power()
        save()
        
        return True, f"驻军已增援！当前驻军: {current_garrison + power}"
    
    def get_total_power(self):
        """获取总战力"""
        return data["territory"]["total_power"]

class SeasonSystem:
    """赛季系统"""
    
    def __init__(self):
        # 确保数据存在
        if "season" not in data:
            data["season"] = {
                "current_season": 1,
                "season_start_time": time.time(),
                "season_duration": 7 * 24 * 3600,  # 7天一个赛季
                "season_points": 0,
                "season_rank": 0,
                "season_rewards_claimed": [],
                "historical_best_rank": 0
            }
        
        self.season_rewards = self._load_season_rewards()
        self._check_season_end()
    
    def _load_season_rewards(self):
        """加载赛季奖励配置"""
        return [
            {"rank": 1, "name": "赛季冠军", "rewards": {"金元宝": 10000, "传说武将碎片": 500, "至尊称号": "赛季霸主"}},
            {"rank": 2, "name": "赛季亚军", "rewards": {"金元宝": 6000, "传说武将碎片": 300, "称号": "赛季强者"}},
            {"rank": 3, "name": "赛季季军", "rewards": {"金元宝": 4000, "传说武将碎片": 200, "称号": "赛季高手"}},
            {"rank": 10, "name": "十强选手", "rewards": {"金元宝": 2000, "稀有武将碎片": 100}},
            {"rank": 50, "name": "五十强", "rewards": {"金元宝": 1000, "稀有武将碎片": 50}},
            {"rank": 100, "name": "百强选手", "rewards": {"金元宝": 500, "高级招募令": 2}},
            {"rank": 500, "name": "五百强", "rewards": {"金元宝": 200, "中级经验丹": 5}},
            {"rank": 1000, "name": "千强选手", "rewards": {"金元宝": 100, "初级经验丹": 10}}
        ]
    
    def _check_season_end(self):
        """检查赛季是否结束"""
        current_time = time.time()
        if current_time >= data["season"]["season_start_time"] + data["season"]["season_duration"]:
            self._end_season()
    
    def _end_season(self):
        """结束赛季"""
        # 保存历史最佳排名
        if data["season"]["season_rank"] > 0:
            if data["season"]["season_rank"] < data["season"]["historical_best_rank"] or data["season"]["historical_best_rank"] == 0:
                data["season"]["historical_best_rank"] = data["season"]["season_rank"]
        
        # 重置赛季数据
        data["season"]["current_season"] += 1
        data["season"]["season_start_time"] = time.time()
        data["season"]["season_points"] = 0
        data["season"]["season_rank"] = 0
        data["season"]["season_rewards_claimed"] = []
        save()
    
    def add_points(self, points):
        """添加赛季积分"""
        data["season"]["season_points"] += points
        save()
        return data["season"]["season_points"]
    
    def get_current_season(self):
        """获取当前赛季"""
        return data["season"]["current_season"]
    
    def get_season_points(self):
        """获取赛季积分"""
        return data["season"]["season_points"]
    
    def get_season_progress(self):
        """获取赛季进度（0-100）"""
        elapsed = time.time() - data["season"]["season_start_time"]
        total = data["season"]["season_duration"]
        return min(100, int((elapsed / total) * 100)) if total > 0 else 0
    
    def get_time_remaining(self):
        """获取剩余时间（秒）"""
        remaining = data["season"]["season_start_time"] + data["season"]["season_duration"] - time.time()
        return max(0, remaining)
    
    def get_time_remaining_str(self):
        """获取剩余时间字符串"""
        remaining = self.get_time_remaining()
        days = remaining // (24 * 3600)
        hours = (remaining % (24 * 3600)) // 3600
        minutes = (remaining % 3600) // 60
        return f"{int(days)}天 {int(hours)}时 {int(minutes)}分"
    
    def claim_season_reward(self, rank):
        """领取赛季奖励"""
        if rank in data["season"]["season_rewards_claimed"]:
            return False, "奖励已领取"
        
        reward = next((r for r in self.season_rewards if r["rank"] == rank), None)
        if not reward:
            return False, "奖励不存在"
        
        # 检查排名是否达标（模拟排名检查）
        if data["season"]["season_rank"] > rank and rank > 1:
            return False, "排名未达标"
        
        # 发放奖励
        for reward_type, amount in reward["rewards"].items():
            if reward_type in data["resources"]:
                data["resources"][reward_type] += amount
            else:
                data["resources"][reward_type] = amount
        
        data["season"]["season_rewards_claimed"].append(rank)
        save()
        
        return True, reward["rewards"]
    
    def get_all_rewards(self):
        """获取所有赛季奖励状态"""
        result = []
        
        for reward in self.season_rewards:
            claimed = reward["rank"] in data["season"]["season_rewards_claimed"]
            available = data["season"]["season_rank"] <= reward["rank"] or reward["rank"] == 1
            
            result.append({
                "rank": reward["rank"],
                "name": reward["name"],
                "rewards": reward["rewards"],
                "claimed": claimed,
                "available": available
            })
        
        return result

class GuildSystem:
    """公会系统"""
    
    def __init__(self):
        # 确保数据存在
        if "guild" not in data:
            data["guild"] = {
                "id": None,
                "name": "",
                "level": 1,
                "experience": 0,
                "members": [],
                "leader": "",
                "join_requests": [],
                "guild_war_score": 0,
                "territories": [],
                "daily_bonus_claimed": False,
                "last_daily_claim": 0
            }
        
        self.guild_levels = self._load_guild_levels()
    
    def _load_guild_levels(self):
        """加载公会等级配置"""
        return [
            {"level": 1, "max_members": 10, "exp_required": 0, "bonus": {"金元宝": 10, "经验": 5}},
            {"level": 2, "max_members": 15, "exp_required": 1000, "bonus": {"金元宝": 20, "经验": 10}},
            {"level": 3, "max_members": 20, "exp_required": 3000, "bonus": {"金元宝": 30, "经验": 15}},
            {"level": 4, "max_members": 25, "exp_required": 6000, "bonus": {"金元宝": 40, "经验": 20}},
            {"level": 5, "max_members": 30, "exp_required": 10000, "bonus": {"金元宝": 50, "经验": 30}},
            {"level": 6, "max_members": 35, "exp_required": 15000, "bonus": {"金元宝": 60, "经验": 40}},
            {"level": 7, "max_members": 40, "exp_required": 21000, "bonus": {"金元宝": 70, "经验": 50}},
            {"level": 8, "max_members": 45, "exp_required": 28000, "bonus": {"金元宝": 80, "经验": 60}},
            {"level": 9, "max_members": 50, "exp_required": 36000, "bonus": {"金元宝": 90, "经验": 70}},
            {"level": 10, "max_members": 60, "exp_required": 45000, "bonus": {"金元宝": 100, "经验": 100}}
        ]
    
    def create_guild(self, name, leader_id):
        """创建公会"""
        if data["guild"]["id"]:
            return False, "已加入或创建公会"
        
        data["guild"]["id"] = f"guild_{int(time.time())}"
        data["guild"]["name"] = name
        data["guild"]["leader"] = leader_id
        data["guild"]["members"] = [leader_id]
        save()
        
        return True, f"公会 {name} 创建成功！"
    
    def join_guild(self, guild_id):
        """加入公会"""
        if data["guild"]["id"]:
            return False, "已加入或创建公会"
        
        # 简化处理：直接加入
        data["guild"]["id"] = guild_id
        data["guild"]["members"].append("player")
        save()
        
        return True, "加入公会成功！"
    
    def leave_guild(self):
        """离开公会"""
        if not data["guild"]["id"]:
            return False, "未加入公会"
        
        if data["guild"]["leader"] == "player":
            # 如果是会长，需要先转移权限或解散
            return False, "会长需要先解散公会或转移权限"
        
        data["guild"]["members"].remove("player")
        data["guild"]["id"] = None
        data["guild"]["name"] = ""
        data["guild"]["leader"] = ""
        save()
        
        return True, "已离开公会"
    
    def add_member(self, member_id):
        """添加成员"""
        if not data["guild"]["id"]:
            return False, "未加入公会"
        
        if data["guild"]["leader"] != "player":
            return False, "只有会长可以添加成员"
        
        current_level = data["guild"]["level"]
        max_members = self.guild_levels[current_level - 1]["max_members"]
        
        if len(data["guild"]["members"]) >= max_members:
            return False, "公会成员已满"
        
        data["guild"]["members"].append(member_id)
        save()
        
        return True, "成员添加成功"
    
    def add_experience(self, exp):
        """添加公会经验"""
        if not data["guild"]["id"]:
            return False, "未加入公会"
        
        data["guild"]["experience"] += exp
        
        # 检查升级
        current_level = data["guild"]["level"]
        while current_level < len(self.guild_levels):
            exp_required = self.guild_levels[current_level]["exp_required"]
            if data["guild"]["experience"] >= exp_required:
                data["guild"]["level"] = current_level + 1
                current_level += 1
            else:
                break
        
        save()
        
        return True, f"公会经验 +{exp}"
    
    def claim_daily_bonus(self):
        """领取每日公会奖励"""
        if not data["guild"]["id"]:
            return False, "未加入公会"
        
        today = time.strftime("%Y-%m-%d")
        if data["guild"]["last_daily_claim"] == today:
            return False, "今日奖励已领取"
        
        level = data["guild"]["level"]
        bonus = self.guild_levels[level - 1]["bonus"]
        
        for resource, amount in bonus.items():
            if resource in data["resources"]:
                data["resources"][resource] += amount
            else:
                data["resources"][resource] = amount
        
        data["guild"]["last_daily_claim"] = today
        data["guild"]["daily_bonus_claimed"] = True
        save()
        
        return True, bonus
    
    def get_guild_info(self):
        """获取公会信息"""
        if not data["guild"]["id"]:
            return None
        
        level = data["guild"]["level"]
        current_exp = data["guild"]["experience"]
        next_exp = self.guild_levels[level]["exp_required"] if level < len(self.guild_levels) else 0
        
        return {
            "id": data["guild"]["id"],
            "name": data["guild"]["name"],
            "level": level,
            "experience": current_exp,
            "next_level_exp": next_exp,
            "members_count": len(data["guild"]["members"]),
            "max_members": self.guild_levels[level - 1]["max_members"],
            "leader": data["guild"]["leader"],
            "daily_bonus": self.guild_levels[level - 1]["bonus"],
            "daily_claimed": data["guild"]["daily_bonus_claimed"]
        }
    
    def get_member_list(self):
        """获取成员列表"""
        return data["guild"]["members"]
    
    def upgrade_guild_territory(self, territory_id):
        """升级公会领土"""
        if not data["guild"]["id"]:
            return False, "未加入公会"
        
        if data["guild"]["leader"] != "player":
            return False, "只有会长可以升级领土"
        
        if territory_id not in data["guild"]["territories"]:
            return False, "未拥有该领土"
        
        # 简化处理：直接升级
        data["guild"]["guild_war_score"] += 100
        save()
        
        return True, "领土升级成功"

class HeroAdvancementSystem:
    """武将进阶系统"""
    
    def __init__(self):
        # 确保数据存在
        if "hero_advancement" not in data:
            data["hero_advancement"] = {
                "advanced_heroes": {},
                "awakened_heroes": [],
                "skill_enhancements": {}
            }
        
        self.advancement_costs = self._load_advancement_costs()
        self.awakening_materials = self._load_awakening_materials()
    
    def _load_advancement_costs(self):
        """加载进阶消耗配置"""
        return [
            {"star": 2, "cost": {"武将碎片": 50, "金元宝": 100}},
            {"star": 3, "cost": {"武将碎片": 100, "金元宝": 300}},
            {"star": 4, "cost": {"武将碎片": 200, "金元宝": 600}},
            {"star": 5, "cost": {"武将碎片": 400, "金元宝": 1200}},
            {"star": 6, "cost": {"武将碎片": 800, "金元宝": 2500}},
            {"star": 7, "cost": {"武将碎片": 1500, "金元宝": 5000}},
            {"star": 8, "cost": {"武将碎片": 3000, "金元宝": 10000}},
            {"star": 9, "cost": {"武将碎片": 6000, "金元宝": 20000}},
            {"star": 10, "cost": {"武将碎片": 12000, "金元宝": 50000}}
        ]
    
    def _load_awakening_materials(self):
        """加载觉醒材料配置"""
        return {
            "normal": {"觉醒石": 10, "金元宝": 500},
            "rare": {"觉醒石": 30, "金元宝": 1500},
            "legendary": {"觉醒石": 100, "金元宝": 5000}
        }
    
    def advance_hero(self, hero_id):
        """进阶武将"""
        hero = data.get("heroes", {}).get(hero_id)
        if not hero:
            return False, "武将不存在"
        
        current_star = hero.get("star", 1)
        if current_star >= 10:
            return False, "已达到最高星级"
        
        # 获取进阶消耗
        cost_info = next((c for c in self.advancement_costs if c["star"] == current_star + 1), None)
        if not cost_info:
            return False, "无法进阶"
        
        # 检查资源是否足够
        for resource, amount in cost_info["cost"].items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"{resource}不足！需要{amount}"
        
        # 消耗资源
        for resource, amount in cost_info["cost"].items():
            data["resources"][resource] -= amount
        
        # 进阶
        hero["star"] = current_star + 1
        
        # 记录进阶信息
        if hero_id not in data["hero_advancement"]["advanced_heroes"]:
            data["hero_advancement"]["advanced_heroes"][hero_id] = []
        data["hero_advancement"]["advanced_heroes"][hero_id].append({
            "star": hero["star"],
            "time": time.time()
        })
        
        save()
        
        return True, f"武将进阶成功！当前星级: {hero['star']}"
    
    def awaken_hero(self, hero_id):
        """觉醒武将"""
        hero = data.get("heroes", {}).get(hero_id)
        if not hero:
            return False, "武将不存在"
        
        if hero_id in data["hero_advancement"]["awakened_heroes"]:
            return False, "武将已觉醒"
        
        if hero.get("star", 1) < 5:
            return False, "需要5星以上才能觉醒"
        
        # 根据稀有度获取材料需求
        rarity = hero.get("rarity", "normal")
        materials = self.awakening_materials.get(rarity, self.awakening_materials["normal"])
        
        # 检查材料是否足够
        for resource, amount in materials.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"{resource}不足！需要{amount}"
        
        # 消耗材料
        for resource, amount in materials.items():
            data["resources"][resource] -= amount
        
        # 觉醒
        data["hero_advancement"]["awakened_heroes"].append(hero_id)
        hero["awakened"] = True
        
        # 提升属性
        hero["attack"] = int(hero.get("attack", 100) * 1.5)
        hero["defense"] = int(hero.get("defense", 50) * 1.5)
        hero["hp"] = int(hero.get("hp", 500) * 1.5)
        
        save()
        
        return True, "武将觉醒成功！属性大幅提升"
    
    def enhance_skill(self, hero_id, skill_index):
        """强化技能"""
        hero = data.get("heroes", {}).get(hero_id)
        if not hero:
            return False, "武将不存在"
        
        skills = hero.get("skills", [])
        if skill_index >= len(skills):
            return False, "技能不存在"
        
        skill = skills[skill_index]
        current_level = skill.get("level", 1)
        if current_level >= 10:
            return False, "技能已达到最高等级"
        
        # 计算升级消耗
        cost = {"金元宝": current_level * 100, "技能书": current_level * 10}
        
        # 检查资源是否足够
        for resource, amount in cost.items():
            if data["resources"].get(resource, 0) < amount:
                return False, f"{resource}不足！需要{amount}"
        
        # 消耗资源
        for resource, amount in cost.items():
            data["resources"][resource] -= amount
        
        # 升级技能
        skill["level"] = current_level + 1
        skill["damage"] = int(skill.get("damage", 100) * 1.1)
        
        # 记录强化信息
        if hero_id not in data["hero_advancement"]["skill_enhancements"]:
            data["hero_advancement"]["skill_enhancements"][hero_id] = {}
        data["hero_advancement"]["skill_enhancements"][hero_id][skill_index] = current_level + 1
        
        save()
        
        return True, f"技能强化成功！当前等级: {current_level + 1}"
    
    def get_hero_advancement_info(self, hero_id):
        """获取武将进阶信息"""
        hero = data.get("heroes", {}).get(hero_id)
        if not hero:
            return None
        
        advanced_info = data["hero_advancement"]["advanced_heroes"].get(hero_id, [])
        awakened = hero_id in data["hero_advancement"]["awakened_heroes"]
        skill_enhancements = data["hero_advancement"]["skill_enhancements"].get(hero_id, {})
        
        return {
            "hero_id": hero_id,
            "name": hero.get("name", ""),
            "current_star": hero.get("star", 1),
            "awakened": awakened,
            "advanced_history": advanced_info,
            "skill_levels": skill_enhancements,
            "next_advance_cost": self._get_next_advance_cost(hero.get("star", 1)),
            "awakening_cost": self._get_awakening_cost(hero.get("rarity", "normal"))
        }
    
    def _get_next_advance_cost(self, current_star):
        """获取下一阶进阶消耗"""
        if current_star >= 10:
            return None
        return next((c["cost"] for c in self.advancement_costs if c["star"] == current_star + 1), None)
    
    def _get_awakening_cost(self, rarity):
        """获取觉醒消耗"""
        return self.awakening_materials.get(rarity, self.awakening_materials["normal"])
    
    def get_all_heroes_advancement(self):
        """获取所有武将的进阶状态"""
        result = []
        for hero_id, hero in data.get("heroes", {}).items():
            info = self.get_hero_advancement_info(hero_id)
            if info:
                result.append(info)
        return result


def draw_gradient_background(screen, color1, color2):
    height = screen.get_height()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))


class Button:
    def __init__(self, text, x, y, width, height, font, color=(100, 100, 150), hover_color=(120, 120, 180), text_color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
    
    def draw(self, screen):
        col = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, col, (self.x, self.y, self.width, self.height), border_radius=8)
        pygame.draw.rect(screen, (255, 215, 0), (self.x, self.y, self.width, self.height), 2, border_radius=8)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
        screen.blit(text_surf, text_rect)
    
    def check_click(self, mx, my):
        return self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height


def main():
    """战略地图系统主界面"""
    try:
        if not pygame.get_init():
            pygame.init()
        
        resolution = data['settings']['graphics']['resolution']
        try:
            width, height = map(int, resolution.split('x'))
        except ValueError:
            width, height = 800, 600
        
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("🏰 战略地图")
        clock = pygame.time.Clock()
        
        font_name = get_system_font_name()
        try:
            font_big = pygame.font.SysFont(font_name, 36)
            font_main = pygame.font.SysFont(font_name, 26)
            font_small = pygame.font.SysFont(font_name, 20)
        except Exception:
            font_big = pygame.font.Font(None, 36)
            font_main = pygame.font.Font(None, 26)
            font_small = pygame.font.Font(None, 20)
        
        territory_manager = TerritoryManager()
        
        running = True
        scroll_y = 0
        
        while running:
            mx, my = pygame.mouse.get_pos()
            
            draw_gradient_background(screen, (10, 15, 30), (25, 35, 55))
            
            title_surf = font_big.render("🏰 战略地图系统", True, (255, 215, 0))
            screen.blit(title_surf, (width//2 - title_surf.get_width()//2, 30))
            
            owned_count = len(data["territory"]["owned_territories"])
            total_power = data["territory"]["total_power"]
            
            info_surf = font_main.render(f"已占领领土: {owned_count} | 总战力: {total_power}", True, (255, 255, 255))
            screen.blit(info_surf, (20, 80))
            
            panel_y = 110
            panel_width = width - 40
            
            pygame.draw.rect(screen, (40, 40, 70), (20, panel_y, panel_width, height - panel_y - 70), border_radius=10)
            pygame.draw.rect(screen, (80, 80, 120), (20, panel_y, panel_width, height - panel_y - 70), 2, border_radius=10)
            
            text_y = panel_y + 20
            for terr in territory_manager.territories[:15]:
                text_surf = font_small.render(f"📍 {terr['name']} - 防御: {terr['defense']}", True, (255, 255, 255))
                screen.blit(text_surf, (40, text_y - scroll_y))
                text_y += 35
            
            back_btn = Button("⏎ 返回", 20, height - 50, 120, 40, font_main)
            back_btn.hovered = back_btn.check_click(mx, my)
            back_btn.draw(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_btn.check_click(mx, my):
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                    scroll_y = max(0, scroll_y - 50)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                    scroll_y = min(500, scroll_y + 50)
            
            pygame.display.flip()
            clock.tick(30)
        
        pygame.display.quit()
        pygame.mixer.quit()
    
    except Exception as e:
        print(f"战略地图错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()