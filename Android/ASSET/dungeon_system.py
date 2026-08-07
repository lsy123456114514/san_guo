import time
import random
from ASSET.game_data import data, save, logger, draw_gradient_bg, cull_dead, get_font

class DungeonSystem:
    """副本挑战系统"""
    
    def __init__(self):
        # 确保数据存在
        if "dungeon" not in data:
            data["dungeon"] = {
                "unlocked_dungeons": [],
                "completed_floors": {},
                "best_scores": {},
                "daily_challenges": [],
                "weekly_challenges": [],
                "claimed_rewards": [],
                "last_daily_reset": 0,
                "last_weekly_reset": 0
            }
        
        self.dungeons = self._load_dungeons()
        self._refresh_challenges()
    
    def _load_dungeons(self):
        """加载副本配置"""
        return [
            {
                "id": "dungeon_normal",
                "name": "普通副本",
                "description": "适合新手的初级副本",
                "difficulty": "normal",
                "floors": 10,
                "base_rewards": {"金元宝": 50, "经验": 100},
                "boss_floor": 10,
                "boss_rewards": {"金元宝": 200, "武将碎片": 20}
            },
            {
                "id": "dungeon_hard",
                "name": "困难副本",
                "description": "挑战你的战斗技巧",
                "difficulty": "hard",
                "floors": 20,
                "base_rewards": {"金元宝": 100, "经验": 200},
                "boss_floor": 20,
                "boss_rewards": {"金元宝": 500, "稀有武将碎片": 30},
                "unlock_condition": {"dungeon": "dungeon_normal", "floor": 10}
            },
            {
                "id": "dungeon_elite",
                "name": "精英副本",
                "description": "只有真正的强者才能通过",
                "difficulty": "elite",
                "floors": 30,
                "base_rewards": {"金元宝": 200, "经验": 400},
                "boss_floor": 30,
                "boss_rewards": {"金元宝": 1000, "传说武将碎片": 50},
                "unlock_condition": {"dungeon": "dungeon_hard", "floor": 20}
            },
            {
                "id": "dungeon_endless",
                "name": "无尽副本",
                "description": "没有尽头的挑战",
                "difficulty": "endless",
                "floors": 999,
                "base_rewards": {"金元宝": 100, "经验": 150},
                "boss_floor": 10,
                "boss_rewards": {"金元宝": 300, "武将碎片": 15},
                "unlock_condition": {"dungeon": "dungeon_elite", "floor": 30}
            },
            {
                "id": "dungeon_tower",
                "name": "试炼之塔",
                "description": "攀登无尽的高塔",
                "difficulty": "tower",
                "floors": 100,
                "base_rewards": {"金元宝": 150, "经验": 300},
                "boss_floor": 50,
                "boss_rewards": {"金元宝": 800, "传说武将碎片": 40},
                "unlock_condition": {"dungeon": "dungeon_elite", "floor": 30}
            }
        ]
    
    def _refresh_challenges(self):
        """刷新每日和每周挑战"""
        today = time.strftime("%Y-%m-%d")
        current_week = time.strftime("%Y-%W")
        
        # 刷新每日挑战
        if data["dungeon"]["last_daily_reset"] != today:
            data["dungeon"]["daily_challenges"] = self._generate_daily_challenges()
            data["dungeon"]["last_daily_reset"] = today
            save()
        
        # 刷新每周挑战
        if data["dungeon"]["last_weekly_reset"] != current_week:
            data["dungeon"]["weekly_challenges"] = self._generate_weekly_challenges()
            data["dungeon"]["last_weekly_reset"] = current_week
            save()
    
    def _generate_daily_challenges(self):
        """生成每日挑战"""
        challenges = [
            {"id": "daily_clear_1", "name": "初战告捷", "description": "通关任意副本1层", "target": 1, "rewards": {"金元宝": 100, "经验": 200}},
            {"id": "daily_clear_5", "name": "连战连捷", "description": "通关任意副本5层", "target": 5, "rewards": {"金元宝": 200, "中级经验丹": 1}},
            {"id": "daily_win_3", "name": "常胜将军", "description": "赢得3场战斗", "target": 3, "rewards": {"金元宝": 150, "经验": 300}},
            {"id": "daily_combo_5", "name": "连击高手", "description": "达成5连击", "target": 5, "rewards": {"金元宝": 120, "武将碎片": 10}}
        ]
        return challenges
    
    def _generate_weekly_challenges(self):
        """生成每周挑战"""
        challenges = [
            {"id": "weekly_clear_20", "name": "副本达人", "description": "通关副本20层", "target": 20, "rewards": {"金元宝": 500, "高级招募令": 1}},
            {"id": "weekly_clear_50", "name": "副本精英", "description": "通关副本50层", "target": 50, "rewards": {"金元宝": 1000, "稀有武将碎片": 30}},
            {"id": "weekly_win_10", "name": "百战百胜", "description": "赢得10场战斗", "target": 10, "rewards": {"金元宝": 600, "经验": 1000}},
            {"id": "weekly_ultimate_5", "name": "必杀之威", "description": "使用5次必杀技", "target": 5, "rewards": {"金元宝": 400, "技能书": 20}}
        ]
        return challenges
    
    def is_dungeon_unlocked(self, dungeon_id):
        """检查副本是否解锁"""
        dungeon = next((d for d in self.dungeons if d["id"] == dungeon_id), None)
        if not dungeon:
            return False
        
        if dungeon_id in data["dungeon"]["unlocked_dungeons"]:
            return True
        
        # 检查解锁条件
        if not dungeon.get("unlock_condition"):
            return True  # 默认解锁
        
        condition = dungeon["unlock_condition"]
        required_dungeon = condition.get("dungeon")
        required_floor = condition.get("floor")
        
        if required_dungeon and required_floor:
            completed_floor = data["dungeon"]["completed_floors"].get(required_dungeon, 0)
            if completed_floor >= required_floor:
                data["dungeon"]["unlocked_dungeons"].append(dungeon_id)
                save()
                return True
        
        return False
    
    def enter_dungeon(self, dungeon_id):
        """进入副本"""
        if not self.is_dungeon_unlocked(dungeon_id):
            return False, "副本未解锁"
        
        dungeon = next((d for d in self.dungeons if d["id"] == dungeon_id), None)
        if not dungeon:
            return False, "副本不存在"
        
        # 记录进入时间
        data["dungeon"]["current_dungeon"] = dungeon_id
        data["dungeon"]["current_floor"] = 1
        save()
        
        return True, dungeon
    
    def complete_floor(self, dungeon_id, floor):
        """完成副本层"""
        dungeon = next((d for d in self.dungeons if d["id"] == dungeon_id), None)
        if not dungeon:
            return False, "副本不存在"
        
        # 更新最高层数
        current_max = data["dungeon"]["completed_floors"].get(dungeon_id, 0)
        if floor > current_max:
            data["dungeon"]["completed_floors"][dungeon_id] = floor
            save()
        
        # 检查是否通关BOSS层
        if floor % dungeon["boss_floor"] == 0:
            return self._handle_boss_reward(dungeon, floor)
        else:
            return self._handle_normal_reward(dungeon)
    
    def _handle_normal_reward(self, dungeon):
        """处理普通层奖励"""
        rewards = dungeon["base_rewards"]
        
        for resource, amount in rewards.items():
            if resource in data["resources"]:
                data["resources"][resource] += amount
            else:
                data["resources"][resource] = amount
        
        save()
        return True, rewards
    
    def _handle_boss_reward(self, dungeon, floor):
        """处理BOSS层奖励"""
        rewards = dungeon["boss_rewards"]
        
        for resource, amount in rewards.items():
            if resource in data["resources"]:
                data["resources"][resource] += amount
            else:
                data["resources"][resource] = amount
        
        # 更新最高分
        if dungeon["id"] not in data["dungeon"]["best_scores"] or floor > data["dungeon"]["best_scores"][dungeon["id"]]:
            data["dungeon"]["best_scores"][dungeon["id"]] = floor
        
        save()
        return True, rewards
    
    def claim_challenge_reward(self, challenge_id):
        """领取挑战奖励"""
        if challenge_id in data["dungeon"]["claimed_rewards"]:
            return False, "奖励已领取"
        
        # 检查每日挑战
        for challenge in data["dungeon"]["daily_challenges"]:
            if challenge["id"] == challenge_id:
                # 检查进度
                progress = data["dungeon"]["task_progress"].get(challenge_id, 0)
                if progress < challenge["target"]:
                    return False, "挑战未完成"
                
                # 发放奖励
                for reward, amount in challenge["rewards"].items():
                    if reward in data["resources"]:
                        data["resources"][reward] += amount
                    else:
                        data["resources"][reward] = amount
                
                data["dungeon"]["claimed_rewards"].append(challenge_id)
                save()
                return True, challenge["rewards"]
        
        # 检查每周挑战
        for challenge in data["dungeon"]["weekly_challenges"]:
            if challenge["id"] == challenge_id:
                # 检查进度
                progress = data["dungeon"]["task_progress"].get(challenge_id, 0)
                if progress < challenge["target"]:
                    return False, "挑战未完成"
                
                # 发放奖励
                for reward, amount in challenge["rewards"].items():
                    if reward in data["resources"]:
                        data["resources"][reward] += amount
                    else:
                        data["resources"][reward] = amount
                
                data["dungeon"]["claimed_rewards"].append(challenge_id)
                save()
                return True, challenge["rewards"]
        
        return False, "挑战不存在"
    
    def update_challenge_progress(self, challenge_type, amount=1):
        """更新挑战进度"""
        # 更新每日挑战进度
        for challenge in data["dungeon"]["daily_challenges"]:
            if challenge_type in challenge["id"]:
                current = data["dungeon"]["task_progress"].get(challenge["id"], 0)
                data["dungeon"]["task_progress"][challenge["id"]] = min(challenge["target"], current + amount)
        
        # 更新每周挑战进度
        for challenge in data["dungeon"]["weekly_challenges"]:
            if challenge_type in challenge["id"]:
                current = data["dungeon"]["task_progress"].get(challenge["id"], 0)
                data["dungeon"]["task_progress"][challenge["id"]] = min(challenge["target"], current + amount)
        
        save()
    
    def get_dungeon_info(self, dungeon_id):
        """获取副本信息"""
        dungeon = next((d for d in self.dungeons if d["id"] == dungeon_id), None)
        if not dungeon:
            return None
        
        return {
            "id": dungeon["id"],
            "name": dungeon["name"],
            "description": dungeon["description"],
            "difficulty": dungeon["difficulty"],
            "total_floors": dungeon["floors"],
            "completed_floors": data["dungeon"]["completed_floors"].get(dungeon_id, 0),
            "best_score": data["dungeon"]["best_scores"].get(dungeon_id, 0),
            "unlocked": self.is_dungeon_unlocked(dungeon_id),
            "base_rewards": dungeon["base_rewards"],
            "boss_floor": dungeon["boss_floor"],
            "boss_rewards": dungeon["boss_rewards"]
        }
    
    def get_all_dungeons(self):
        """获取所有副本信息"""
        result = []
        for dungeon in self.dungeons:
            result.append(self.get_dungeon_info(dungeon["id"]))
        return result
    
    def get_daily_challenges(self):
        """获取每日挑战"""
        result = []
        for challenge in data["dungeon"]["daily_challenges"]:
            progress = data["dungeon"]["task_progress"].get(challenge["id"], 0)
            claimed = challenge["id"] in data["dungeon"]["claimed_rewards"]
            
            result.append({
                "id": challenge["id"],
                "name": challenge["name"],
                "description": challenge["description"],
                "target": challenge["target"],
                "current": progress,
                "rewards": challenge["rewards"],
                "claimed": claimed
            })
        return result
    
    def get_weekly_challenges(self):
        """获取每周挑战"""
        result = []
        for challenge in data["dungeon"]["weekly_challenges"]:
            progress = data["dungeon"]["task_progress"].get(challenge["id"], 0)
            claimed = challenge["id"] in data["dungeon"]["claimed_rewards"]
            
            result.append({
                "id": challenge["id"],
                "name": challenge["name"],
                "description": challenge["description"],
                "target": challenge["target"],
                "current": progress,
                "rewards": challenge["rewards"],
                "claimed": claimed
            })
        return result
    
    def generate_floor_enemy(self, dungeon_id, floor):
        """生成楼层敌人"""
        dungeon = next((d for d in self.dungeons if d["id"] == dungeon_id), None)
        if not dungeon:
            return None
        
        difficulty_multiplier = {
            "normal": 1.0,
            "hard": 1.5,
            "elite": 2.0,
            "endless": 1.0 + floor * 0.1,
            "tower": 1.0 + floor * 0.08
        }
        
        multiplier = difficulty_multiplier.get(dungeon["difficulty"], 1.0)
        
        # 生成随机敌人
        enemy_names = ["黄巾军", "山贼", "马贼", "流寇", "叛军", "土匪", "刺客", "间谍"]
        
        return {
            "name": random.choice(enemy_names),
            "level": floor * 2,
            "attack": int(50 * floor * multiplier),
            "defense": int(30 * floor * multiplier),
            "hp": int(500 * floor * multiplier),
            "rewards": {
                "金元宝": int(20 * floor * multiplier),
                "经验": int(50 * floor * multiplier)
            }
        }