import time
from ASSET.game_data import data, save

class QuestSystem:
    """任务链系统 - 引导玩家持续游玩"""
    
    def __init__(self):
        # 确保数据存在
        if "quests" not in data:
            data["quests"] = {
                "active_quests": [],
                "completed_quests": [],
                "claimed_rewards": [],
                "quest_progress": {},
                "daily_quests_reset_time": 0,
                "weekly_quests_reset_time": 0
            }
        
        self.quests = self._load_quests()
    
    def _load_quests(self):
        """加载任务配置"""
        return {
            # 主线任务链
            "main": {
                "name": "主线任务",
                "description": "跟随主线剧情，开启你的三国征程",
                "icon": "📜",
                "chain": [
                    {
                        "id": "main_1",
                        "name": "初入江湖",
                        "description": "完成新手引导",
                        "type": "main",
                        "goal": {"new_player_guide": 1},
                        "rewards": {"金元宝": 100, "经验": 200},
                        "next_quest": "main_2",
                        "priority": 1
                    },
                    {
                        "id": "main_2",
                        "name": "招募武将",
                        "description": "招募你的第一名武将",
                        "type": "main",
                        "goal": {"hero_count": 1},
                        "rewards": {"金元宝": 200, "经验": 300},
                        "next_quest": "main_3",
                        "priority": 1
                    },
                    {
                        "id": "main_3",
                        "name": "首次战斗",
                        "description": "完成第一场战斗",
                        "type": "main",
                        "goal": {"total_battles": 1},
                        "rewards": {"金元宝": 300, "经验": 400},
                        "next_quest": "main_4",
                        "priority": 1
                    },
                    {
                        "id": "main_4",
                        "name": "战胜强敌",
                        "description": "获得5场胜利",
                        "type": "main",
                        "goal": {"victories": 5},
                        "rewards": {"金元宝": 500, "高级招募令": 1},
                        "next_quest": "main_5",
                        "priority": 1
                    },
                    {
                        "id": "main_5",
                        "name": "剧情推进",
                        "description": "完成第一个剧情事件",
                        "type": "main",
                        "goal": {"story_completed": 1},
                        "rewards": {"金元宝": 500, "经验": 600},
                        "next_quest": "main_6",
                        "priority": 1
                    },
                    {
                        "id": "main