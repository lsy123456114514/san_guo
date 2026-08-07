import time
from ASSET.game_data import data, save, logger, draw_gradient_bg, cull_dead, get_font

class AchievementSystem:
    """成就系统 - 给予玩家成就感和目标感"""
    
    def __init__(self):
        # 确保数据存在
        if "achievements" not in data:
            data["achievements"] = {
                "unlocked": [],
                "progress": {},
                "claimed_rewards": []
            }
        
        self.achievements = self._load_achievements()
    
    def _load_achievements(self):
        """加载成就配置"""
        return [
            # 战斗成就
            {
                "id": "first_battle",
                "name": "初出茅庐",
                "description": "完成第一场战斗",
                "icon": "⚔️",
                "type": "battle",
                "goal": 1,
                "stat_key": "total_battles",
                "rewards": {"金元宝": 100, "经验": 200},
                "rarity": "common",
                "tier": 1
            },
            {
                "id": "victory_10",
                "name": "百战百胜",
                "description": "获得10场胜利",
                "icon": "🏆",
                "type": "battle",
                "goal": 10,
                "stat_key": "victories",
                "rewards": {"金元宝": 200, "经验": 500},
                "rarity": "common",
                "tier": 2
            },
            {
                "id": "victory_50",
                "name": "常胜将军",
                "description": "获得50场胜利",
                "icon": "⭐",
                "type": "battle",
                "goal": 50,
                "stat_key": "victories",
                "rewards": {"金元宝": 500, "高级招募令": 1},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "victory_100",
                "name": "战神",
                "description": "获得100场胜利",
                "icon": "👑",
                "type": "battle",
                "goal": 100,
                "stat_key": "victories",
                "rewards": {"金元宝": 1000, "顶级招募令": 1},
                "rarity": "legendary",
                "tier": 4
            },
            {
                "id": "max_combo_10",
                "name": "连击大师",
                "description": "达成10连击",
                "icon": "🔥",
                "type": "battle",
                "goal": 10,
                "stat_key": "max_combo",
                "rewards": {"金元宝": 300, "经验": 400},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "ultimate_10",
                "name": "必杀达人",
                "description": "使用10次必杀技",
                "icon": "💥",
                "type": "battle",
                "goal": 10,
                "stat_key": "ultimate_used_count",
                "rewards": {"金元宝": 200, "经验": 300},
                "rarity": "common",
                "tier": 2
            },
            # 收集成就
            {
                "id": "collect_5_heroes",
                "name": "招贤纳士",
                "description": "拥有5名武将",
                "icon": "👥",
                "type": "collection",
                "goal": 5,
                "stat_key": "hero_count",
                "rewards": {"金元宝": 200, "经验": 300},
                "rarity": "common",
                "tier": 2
            },
            {
                "id": "collect_10_heroes",
                "name": "人才济济",
                "description": "拥有10名武将",
                "icon": "🌟",
                "type": "collection",
                "goal": 10,
                "stat_key": "hero_count",
                "rewards": {"金元宝": 500, "高级招募令": 1},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "collect_20_heroes",
                "name": "群英荟萃",
                "description": "拥有20名武将",
                "icon": "👑",
                "type": "collection",
                "goal": 20,
                "stat_key": "hero_count",
                "rewards": {"金元宝": 1000, "顶级招募令": 2},
                "rarity": "legendary",
                "tier": 4
            },
            {
                "id": "legendary_hero",
                "name": "名将降临",
                "description": "获得一名传说武将",
                "icon": "💎",
                "type": "collection",
                "goal": 1,
                "stat_key": "legendary_count",
                "rewards": {"金元宝": 300, "经验": 500},
                "rarity": "rare",
                "tier": 3
            },
            # 签到成就
            {
                "id": "checkin_7",
                "name": "持之以恒",
                "description": "连续签到7天",
                "icon": "📅",
                "type": "checkin",
                "goal": 7,
                "stat_key": "consecutive_checkins",
                "rewards": {"金元宝": 300, "中级经验丹": 2},
                "rarity": "common",
                "tier": 2
            },
            {
                "id": "checkin_30",
                "name": "坚持不懈",
                "description": "连续签到30天",
                "icon": "🌙",
                "type": "checkin",
                "goal": 30,
                "stat_key": "consecutive_checkins",
                "rewards": {"金元宝": 1000, "顶级招募令": 1},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "checkin_100",
                "name": "百炼成钢",
                "description": "累计签到100天",
                "icon": "💪",
                "type": "checkin",
                "goal": 100,
                "stat_key": "total_checkins",
                "rewards": {"金元宝": 2000, "稀有武将碎片": 30},
                "rarity": "legendary",
                "tier": 4
            },
            # 资源成就
            {
                "id": "gold_10000",
                "name": "腰缠万贯",
                "description": "累计获得10000金元宝",
                "icon": "💰",
                "type": "resource",
                "goal": 10000,
                "stat_key": "total_gold",
                "rewards": {"金元宝": 500, "经验": 500},
                "rarity": "rare",
                "tier": 3
            },
            {
                "id": "resource_master",
                "name": "富甲一方",
                "description": "所有资源都达到1000",
                "icon": "📦",
                "type": "resource",
                "goal": 1000,
                "stat_key": "max_resource",
                "rewards": {"金元宝": 800, "装备精炼石": 10},
                "rarity": "rare",
                "tier": 3
            },
            # 剧情成就
            {
                "id": "first_story",
                "name": "乱世启程",
                "description": "完成第一个剧情事件",
                "icon": "📜",
                "type": "story",
                "goal": 1,
                "stat_key": "story_completed",
                "rewards": {"金元宝": 100, "经验": 200},
                "rarity": "common",
                "tier": 1
            },
            {
                "id": "story_all",
                "name": "一统天下",
                "description": "完成所有剧情事件",
                "icon": "🌍",
                "type": "story",
                "goal": 10,
                "stat_key": "story_completed",
                "rewards": {"金元宝": 2000, "传说武将碎片": 100},
                "rarity": "legendary",
                "tier": 5
            },
            # 社交成就
            {
                "id": "friend_5",
                "name": "广交朋友",
                "description": "拥有5位好友",
                "icon": "🤝",
                "type": "social",
                "goal": 5,
                "stat_key": "friend_count",
                "rewards": {"金元宝": 200, "经验": 300},
                "rarity": "common",
                "tier": 2
            },
            {
                "id": "friend_20",
                "name": "四海之内皆兄弟",
                "description": "拥有20位好友",
                "icon": "👨‍👩‍👧‍👦",
                "type": "social",
                "goal": 20,
                "stat_key": "friend_count",
                "rewards": {"金元宝": 500, "高级招募令": 1},
                "rarity": "rare",
                "tier": 3
            }
        ]
    
    def _get_stat_value(self, stat_key):
        """获取统计值"""
        if stat_key == "hero_count":
            return len(data.get("heroes", {}))
        elif stat_key == "legendary_count":
            heroes = data.get("heroes", {})
            count = 0
            for hero in heroes.values():
                if hero.get("star", 1) >= 3:
                    count += 1
            return count
        elif stat_key == "consecutive_checkins":
            return data.get("daily_reward", {}).get("consecutive_days", 0)
        elif stat_key == "total_checkins":
            return data.get("daily_reward", {}).get("monthly_checkins", 0)
        elif stat_key == "story_completed":
            return len(data.get("event_system", {}).get("event_history", []))
        elif stat_key == "friend_count":
            return len(data.get("friends", {}).get("list", []))
        elif stat_key == "total_gold":
            return data.get("resources", {}).get("金元宝", 0)
        elif stat_key == "max_resource":
            resources = data.get("resources", {})
            return max(resources.values(), default=0)
        elif stat_key in data.get("battle_stats", {}):
            return data["battle_stats"].get(stat_key, 0)
        return 0
    
    def check_achievements(self):
        """检查成就解锁"""
        unlocked_this_time = []
        
        for achievement in self.achievements:
            achievement_id = achievement["id"]
            
            if achievement_id in data["achievements"]["unlocked"]:
                continue
            
            current_value = self._get_stat_value(achievement["stat_key"])
            
            if current_value >= achievement["goal"]:
                data["achievements"]["unlocked"].append(achievement_id)
                data["achievements"]["progress"][achievement_id] = 100
                unlocked_this_time.append(achievement)
                save()
        
        return unlocked_this_time
    
    def get_progress(self, achievement_id):
        """获取成就进度"""
        achievement = next((a for a in self.achievements if a["id"] == achievement_id), None)
        if not achievement:
            return 0
        
        current_value = self._get_stat_value(achievement["stat_key"])
        return min(100, int((current_value / achievement["goal"]) * 100))
    
    def claim_reward(self, achievement_id):
        """领取成就奖励"""
        if achievement_id in data["achievements"]["claimed_rewards"]:
            return False, "奖励已领取"
        
        achievement = next((a for a in self.achievements if a["id"] == achievement_id), None)
        if not achievement:
            return False, "成就不存在"
        
        if achievement_id not in data["achievements"]["unlocked"]:
            return False, "成就未解锁"
        
        # 发放奖励
        for reward, amount in achievement["rewards"].items():
            if reward in data["resources"]:
                data["resources"][reward] += amount
            else:
                data["resources"][reward] = amount
        
        data["achievements"]["claimed_rewards"].append(achievement_id)
        save()
        
        return True, achievement["rewards"]
    
    def get_all_achievements(self):
        """获取所有成就状态"""
        result = []
        
        for achievement in self.achievements:
            unlocked = achievement["id"] in data["achievements"]["unlocked"]
            claimed = achievement["id"] in data["achievements"]["claimed_rewards"]
            progress = self.get_progress(achievement["id"])
            
            result.append({
                "id": achievement["id"],
                "name": achievement["name"],
                "description": achievement["description"],
                "icon": achievement["icon"],
                "type": achievement["type"],
                "goal": achievement["goal"],
                "current": self._get_stat_value(achievement["stat_key"]),
                "progress": progress,
                "unlocked": unlocked,
                "claimed": claimed,
                "rewards": achievement["rewards"],
                "rarity": achievement["rarity"],
                "tier": achievement["tier"]
            })
        
        return result
    
    def get_unclaimed_rewards(self):
        """获取未领取奖励的成就"""
        unclaimed = []
        
        for achievement in self.achievements:
            if achievement["id"] in data["achievements"]["unlocked"]:
                if achievement["id"] not in data["achievements"]["claimed_rewards"]:
                    unclaimed.append(achievement)
        
        return unclaimed
    
    def get_achievement_by_id(self, achievement_id):
        """根据ID获取成就"""
        return next((a for a in self.achievements if a["id"] == achievement_id), None)