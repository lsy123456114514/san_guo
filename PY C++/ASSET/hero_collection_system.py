import time
from ASSET.game_data import data, save
from ASSET.hero_database import HERO_DATABASE, HERO_FACTION_MAP

class HeroCollectionSystem:
    """武将图鉴收集系统 - 收集天下名将，解锁奖励"""
    
    def __init__(self):
        # 确保数据存在
        if "hero_collection" not in data:
            data["hero_collection"] = {
                "collected": [],
                "collection_progress": 0,
                "unlocked_bonuses": [],
                "claimed_rewards": []
            }
        
        self.heroes = self._load_hero_data()
        self.bonuses = self._load_collection_bonuses()
    
    def _load_hero_data(self):
        """加载武将图鉴数据（从HERO_DATABASE动态生成，覆盖全部135名武将）"""
        hero_list = []
        for hero_name, hero_info in HERO_DATABASE.items():
            faction_key = hero_info.get("faction", "qun")
            faction_name = HERO_FACTION_MAP.get(faction_key, {}).get("name", "群雄")
            rarity_map = {
                1: "common",
                2: "rare",
                3: "epic",
                4: "legendary",
                5: "mythic"
            }
            rarity = rarity_map.get(hero_info.get("quality", 2), "common")
            
            hero_list.append({
                "id": f"hero_{hero_name}",
                "name": hero_name,
                "faction": faction_name,
                "rarity": rarity,
                "description": hero_info.get("description", ""),
                "skill": hero_info.get("skill_name", "普通攻击"),
                "element": hero_info.get("element", "火")
            })
        return hero_list
    
    def _load_collection_bonuses(self):
        """加载收集奖励配置"""
        return [
            {"id": "bonus_5", "name": "初窥门径", "description": "收集5名武将", "target": 5, "rewards": {"金元宝": 200, "经验": 300}},
            {"id": "bonus_10", "name": "小有成就", "description": "收集10名武将", "target": 10, "rewards": {"金元宝": 500, "中级经验丹": 2}},
            {"id": "bonus_20", "name": "人才济济", "description": "收集20名武将", "target": 20, "rewards": {"金元宝": 800, "高级招募令": 1}},
            {"id": "bonus_30", "name": "群英荟萃", "description": "收集30名武将", "target": 30, "rewards": {"金元宝": 1200, "顶级招募令": 1}},
            {"id": "bonus_50", "name": "名将如云", "description": "收集50名武将", "target": 50, "rewards": {"金元宝": 2000, "稀有武将碎片": 50}},
            {"id": "bonus_80", "name": "威震天下", "description": "收集80名武将", "target": 80, "rewards": {"金元宝": 3500, "传说武将碎片": 80, "顶级招募令": 3}},
            {"id": "bonus_100", "name": "一统江山", "description": "收集100名武将", "target": 100, "rewards": {"金元宝": 5000, "神话武将碎片": 100}},
            {"id": "bonus_all", "name": "天下无双", "description": "收集所有武将", "target": 135, "rewards": {"金元宝": 10000, "神话武将碎片": 200, "至尊称号": "名将收藏家"}}
        ]
    
    def add_hero(self, hero_id):
        """添加武将到图鉴"""
        if hero_id not in data["hero_collection"]["collected"]:
            data["hero_collection"]["collected"].append(hero_id)
            self._update_progress()
            save()
            return True
        return False
    
    def _update_progress(self):
        """更新收集进度"""
        total_heroes = len(self.heroes)
        collected_count = len(data["hero_collection"]["collected"])
        data["hero_collection"]["collection_progress"] = int((collected_count / total_heroes) * 100)
    
    def get_collection_progress(self):
        """获取收集进度"""
        return data["hero_collection"]["collection_progress"]
    
    def get_collected_count(self):
        """获取已收集数量"""
        return len(data["hero_collection"]["collected"])
    
    def get_total_count(self):
        """获取武将总数"""
        return len(self.heroes)
    
    def is_collected(self, hero_id):
        """检查武将是否已收集"""
        return hero_id in data["hero_collection"]["collected"]
    
    def get_all_heroes(self):
        """获取所有武将信息（含收集状态）"""
        result = []
        for hero in self.heroes:
            result.append({
                "id": hero["id"],
                "name": hero["name"],
                "faction": hero["faction"],
                "rarity": hero["rarity"],
                "description": hero["description"],
                "skill": hero["skill"],
                "element": hero["element"],
                "collected": hero["id"] in data["hero_collection"]["collected"]
            })
        return result
    
    def get_hero_by_id(self, hero_id):
        """根据ID获取武将信息"""
        hero = next((h for h in self.heroes if h["id"] == hero_id), None)
        if hero:
            return {
                "id": hero["id"],
                "name": hero["name"],
                "faction": hero["faction"],
                "rarity": hero["rarity"],
                "description": hero["description"],
                "skill": hero["skill"],
                "element": hero["element"],
                "collected": hero["id"] in data["hero_collection"]["collected"]
            }
        return None
    
    def get_heroes_by_faction(self, faction):
        """按阵营获取武将"""
        heroes = self.get_all_heroes()
        return [h for h in heroes if h["faction"] == faction]
    
    def get_heroes_by_rarity(self, rarity):
        """按稀有度获取武将"""
        heroes = self.get_all_heroes()
        return [h for h in heroes if h["rarity"] == rarity]
    
    def check_bonus_unlock(self):
        """检查是否有新奖励解锁"""
        unlocked = []
        collected_count = self.get_collected_count()
        
        for bonus in self.bonuses:
            if bonus["id"] not in data["hero_collection"]["unlocked_bonuses"]:
                if collected_count >= bonus["target"]:
                    data["hero_collection"]["unlocked_bonuses"].append(bonus["id"])
                    unlocked.append(bonus)
                    save()
        
        return unlocked
    
    def claim_bonus_reward(self, bonus_id):
        """领取收集奖励"""
        if bonus_id in data["hero_collection"]["claimed_rewards"]:
            return False, "奖励已领取"
        
        if bonus_id not in data["hero_collection"]["unlocked_bonuses"]:
            return False, "奖励未解锁"
        
        bonus = next((b for b in self.bonuses if b["id"] == bonus_id), None)
        if not bonus:
            return False, "奖励不存在"
        
        # 发放奖励
        for reward, amount in bonus["rewards"].items():
            if reward in data["resources"]:
                data["resources"][reward] += amount
            else:
                data["resources"][reward] = amount
        
        data["hero_collection"]["claimed_rewards"].append(bonus_id)
        save()
        
        return True, bonus["rewards"]
    
    def get_all_bonuses(self):
        """获取所有收集奖励状态"""
        collected_count = self.get_collected_count()
        result = []
        
        for bonus in self.bonuses:
            unlocked = bonus["id"] in data["hero_collection"]["unlocked_bonuses"]
            claimed = bonus["id"] in data["hero_collection"]["claimed_rewards"]
            
            result.append({
                "id": bonus["id"],
                "name": bonus["name"],
                "description": bonus["description"],
                "target": bonus["target"],
                "current": collected_count,
                "rewards": bonus["rewards"],
                "unlocked": unlocked,
                "claimed": claimed
            })
        
        return result
    
    def get_faction_progress(self):
        """获取各阵营收集进度"""
        factions = ["蜀", "魏", "吴", "群雄"]
        result = {}
        
        for faction in factions:
            faction_heroes = self.get_heroes_by_faction(faction)
            collected = sum(1 for h in faction_heroes if h["collected"])
            total = len(faction_heroes)
            result[faction] = {
                "collected": collected,
                "total": total,
                "progress": int((collected / total) * 100) if total > 0 else 0
            }
        
        return result