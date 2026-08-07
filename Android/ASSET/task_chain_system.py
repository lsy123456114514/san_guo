import time
from ASSET.game_data import data, save, logger, draw_gradient_bg, cull_dead, get_font

class TaskChainSystem:
    """任务链系统 - 引导玩家持续游玩，形成循环"""
    
    def __init__(self):
        # 确保数据存在
        if "task_chains" not in data:
            data["task_chains"] = {
                "active_chains": [],
                "completed_chains": [],
                "current_tasks": {},
                "task_progress": {},
                "daily_tasks": [],
                "weekly_tasks": [],
                "claimed_rewards": []
            }
        
        self.task_chains = self._load_task_chains()
        self.daily_tasks_list = self._load_daily_tasks()
        self.weekly_tasks_list = self._load_weekly_tasks()
        
        self._refresh_daily_tasks()
        self._refresh_weekly_tasks()
    
    def _load_task_chains(self):
        """加载任务链配置"""
        return [
            {
                "id": "chain_newbie",
                "name": "初入江湖",
                "description": "完成新手引导，开启你的三国之旅",
                "icon": "🚀",
                "tasks": [
                    {"id": "task_first_battle", "name": "初试锋芒", "description": "完成一场战斗", "target": 1, "stat": "battles"},
                    {"id": "task_recruit_first", "name": "招兵买马", "description": "招募一名武将", "target": 1, "stat": "recruits"},
                    {"id": "task_win_first", "name": "旗开得胜", "description": "赢得一场胜利", "target": 1, "stat": "wins"},
                    {"id": "task_upgrade_first", "name": "提升实力", "description": "提升一名武将等级", "target": 1, "stat": "upgrades"}
                ],
                "rewards": {"金元宝": 500, "高级招募令": 1, "经验": 1000},
                "unlock_condition": None,
                "type": "main"
            },
            {
                "id": "chain_battle_master",
                "name": "百战之路",
                "description": "成为真正的战斗大师",
                "icon": "⚔️",
                "tasks": [
                    {"id": "task_battle_10", "name": "十战十捷", "description": "完成10场战斗", "target": 10, "stat": "battles"},
                    {"id": "task_win_5", "name": "常胜将军", "description": "赢得5场胜利", "target": 5, "stat": "wins"},
                    {"id": "task_combo_5", "name": "连击高手", "description": "达成5连击", "target": 5, "stat": "max_combo"},
                    {"id": "task_ultimate_3", "name": "必杀之威", "description": "使用3次必杀技", "target": 3, "stat": "ultimates"}
                ],
                "rewards": {"金元宝": 1000, "顶级招募令": 1, "装备精炼石": 10},
                "unlock_condition": {"chain": "chain_newbie"},
                "type": "main"
            },
            {
                "id": "chain_collector",
                "name": "收藏达人",
                "description": "收集天下名将",
                "icon": "📚",
                "tasks": [
                    {"id": "task_collect_5", "name": "小有成就", "description": "拥有5名武将", "target": 5, "stat": "hero_count"},
                    {"id": "task_collect_rare", "name": "稀有收藏", "description": "拥有一名稀有武将", "target": 1, "stat": "rare_hero"},
                    {"id": "task_collect_10", "name": "人才济济", "description": "拥有10名武将", "target": 10, "stat": "hero_count"},
                    {"id": "task_collect_legendary", "name": "传说降临", "description": "拥有一名传说武将", "target": 1, "stat": "legendary_hero"}
                ],
                "rewards": {"金元宝": 1500, "传说武将碎片": 50, "顶级招募令": 2},
                "unlock_condition": {"chain": "chain_newbie"},
                "type": "collection"
            },
            {
                "id": "chain_strategy",
                "name": "谋略无双",
                "description": "运用智慧取得胜利",
                "icon": "🧠",
                "tasks": [
                    {"id": "task_story_3", "name": "熟读兵法", "description": "完成3个剧情事件", "target": 3, "stat": "story_events"},
                    {"id": "task_event_5", "name": "随机应变", "description": "完成5个随机事件", "target": 5, "stat": "random_events"},
                    {"id": "task_alliance", "name": "合纵连横", "description": "完成结盟事件", "target": 1, "stat": "alliance"},
                    {"id": "task_kingdom", "name": "霸业初成", "description": "完成建国剧情", "target": 1, "stat": "kingdom"}
                ],
                "rewards": {"金元宝": 2000, "策略点": 100, "高级招募令": 3},
                "unlock_condition": {"chain": "chain_battle_master"},
                "type": "strategy"
            },
            {
                "id": "chain_endgame",
                "name": "天下一统",
                "description": "最终的挑战",
                "icon": "👑",
                "tasks": [
                    {"id": "task_battle_100", "name": "百战百胜", "description": "完成100场战斗", "target": 100, "stat": "battles"},
                    {"id": "task_win_50", "name": "所向披靡", "description": "赢得50场胜利", "target": 50, "stat": "wins"},
                    {"id": "task_collect_20", "name": "群英荟萃", "description": "拥有20名武将", "target": 20, "stat": "hero_count"},
                    {"id": "task_final_boss", "name": "终极对决", "description": "击败最终BOSS", "target": 1, "stat": "final_boss"}
                ],
                "rewards": {"金元宝": 5000, "传说武将碎片": 200, "至尊称号": "天下霸主"},
                "unlock_condition": {"chain": "chain_strategy"},
                "type": "endgame"
            }
        ]
    
    def _load_daily_tasks(self):
        """加载每日任务配置"""
        return [
            {"id": "daily_battle", "name": "日常练兵", "description": "完成3场战斗", "target": 3, "stat": "daily_battles", "rewards": {"金元宝": 100, "经验": 200}},
            {"id": "daily_win", "name": "胜利之师", "description": "赢得1场胜利", "target": 1, "stat": "daily_wins", "rewards": {"金元宝": 150, "经验": 300}},
            {"id": "daily_checkin", "name": "每日签到", "description": "完成今日签到", "target": 1, "stat": "daily_checkin", "rewards": {"金元宝": 50, "经验": 100}},
            {"id": "daily_event", "name": "事件处理", "description": "完成1个事件", "target": 1, "stat": "daily_events", "rewards": {"金元宝": 80, "经验": 150}},
            {"id": "daily_resource", "name": "资源收集", "description": "收集500资源", "target": 500, "stat": "daily_resources", "rewards": {"金元宝": 120, "经验": 250}}
        ]
    
    def _load_weekly_tasks(self):
        """加载每周任务配置"""
        return [
            {"id": "weekly_battle_20", "name": "周常练兵", "description": "完成20场战斗", "target": 20, "stat": "weekly_battles", "rewards": {"金元宝": 500, "高级招募令": 1}},
            {"id": "weekly_win_10", "name": "常胜将军", "description": "赢得10场胜利", "target": 10, "stat": "weekly_wins", "rewards": {"金元宝": 600, "中级经验丹": 3}},
            {"id": "weekly_checkin_5", "name": "坚持不懈", "description": "本周签到5天", "target": 5, "stat": "weekly_checkins", "rewards": {"金元宝": 400, "装备精炼石": 5}},
            {"id": "weekly_hero", "name": "招贤纳士", "description": "招募3名武将", "target": 3, "stat": "weekly_recruits", "rewards": {"金元宝": 300, "高级招募令": 1}},
            {"id": "weekly_story", "name": "剧情推进", "description": "完成2个剧情事件", "target": 2, "stat": "weekly_stories", "rewards": {"金元宝": 700, "顶级招募令": 1}}
        ]
    
    def _refresh_daily_tasks(self):
        """刷新每日任务"""
        today = time.strftime("%Y-%m-%d")
        if data["task_chains"].get("last_daily_refresh") != today:
            data["task_chains"]["daily_tasks"] = []
            data["task_chains"]["task_progress"] = {}
            
            for task in self.daily_tasks_list:
                data["task_chains"]["daily_tasks"].append(task["id"])
                data["task_chains"]["task_progress"][task["id"]] = 0
            
            data["task_chains"]["last_daily_refresh"] = today
            save()
    
    def _refresh_weekly_tasks(self):
        """刷新每周任务"""
        current_week = time.strftime("%Y-%W")
        if data["task_chains"].get("last_weekly_refresh") != current_week:
            data["task_chains"]["weekly_tasks"] = []
            
            for task in self.weekly_tasks_list:
                data["task_chains"]["weekly_tasks"].append(task["id"])
                data["task_chains"]["task_progress"][task["id"]] = 0
            
            data["task_chains"]["last_weekly_refresh"] = current_week
            save()
    
    def _get_stat_value(self, stat_key):
        """获取统计值"""
        if stat_key == "battles":
            return data.get("battle_stats", {}).get("total_battles", 0)
        elif stat_key == "wins":
            return data.get("battle_stats", {}).get("victories", 0)
        elif stat_key == "recruits":
            return data.get("recruit_count", 0)
        elif stat_key == "upgrades":
            return data.get("upgrade_count", 0)
        elif stat_key == "max_combo":
            return data.get("battle_stats", {}).get("max_combo", 0)
        elif stat_key == "ultimates":
            return data.get("battle_stats", {}).get("ultimate_used_count", 0)
        elif stat_key == "hero_count":
            return len(data.get("heroes", {}))
        elif stat_key == "rare_hero":
            return 1 if any(h.get("star", 1) >= 2 for h in data.get("heroes", {}).values()) else 0
        elif stat_key == "legendary_hero":
            return 1 if any(h.get("star", 1) >= 3 for h in data.get("heroes", {}).values()) else 0
        elif stat_key == "story_events":
            return len([e for e in data.get("event_system", {}).get("event_history", []) if "story" in e])
        elif stat_key == "random_events":
            return len([e for e in data.get("event_system", {}).get("event_history", []) if "random" in e])
        elif stat_key == "alliance":
            return 1 if "alliance" in data else 0
        elif stat_key == "kingdom":
            return 1 if data.get("story_progress", {}).get("king_title") else 0
        elif stat_key == "final_boss":
            return 1 if data.get("story_progress", {}).get("boss_battle") else 0
        elif stat_key.startswith("daily_"):
            return data["task_chains"]["task_progress"].get(stat_key, 0)
        elif stat_key.startswith("weekly_"):
            return data["task_chains"]["task_progress"].get(stat_key, 0)
        return 0
    
    def update_task_progress(self, stat_key, amount=1):
        """更新任务进度"""
        # 更新每日任务进度
        for task in self.daily_tasks_list:
            if task["stat"] == stat_key:
                current = data["task_chains"]["task_progress"].get(task["id"], 0)
                data["task_chains"]["task_progress"][task["id"]] = min(task["target"], current + amount)
                save()
                break
        
        # 更新每周任务进度
        for task in self.weekly_tasks_list:
            if task["stat"] == stat_key:
                current = data["task_chains"]["task_progress"].get(task["id"], 0)
                data["task_chains"]["task_progress"][task["id"]] = min(task["target"], current + amount)
                save()
                break
        
        # 更新任务链进度
        for chain in self.task_chains:
            if chain["id"] in data["task_chains"]["completed_chains"]:
                continue
            
            for task in chain["tasks"]:
                if task["stat"] == stat_key:
                    current = data["task_chains"]["task_progress"].get(task["id"], 0)
                    data["task_chains"]["task_progress"][task["id"]] = min(task["target"], current + amount)
                    save()
    
    def get_task_progress(self, task_id):
        """获取任务进度"""
        return data["task_chains"]["task_progress"].get(task_id, 0)
    
    def is_task_complete(self, task_id):
        """检查任务是否完成"""
        # 检查每日任务
        for task in self.daily_tasks_list:
            if task["id"] == task_id:
                return data["task_chains"]["task_progress"].get(task_id, 0) >= task["target"]
        
        # 检查每周任务
        for task in self.weekly_tasks_list:
            if task["id"] == task_id:
                return data["task_chains"]["task_progress"].get(task_id, 0) >= task["target"]
        
        # 检查任务链任务
        for chain in self.task_chains:
            for task in chain["tasks"]:
                if task["id"] == task_id:
                    return data["task_chains"]["task_progress"].get(task_id, 0) >= task["target"]
        
        return False
    
    def claim_task_reward(self, task_id):
        """领取任务奖励"""
        if task_id in data["task_chains"]["claimed_rewards"]:
            return False, "奖励已领取"
        
        # 检查每日任务
        for task in self.daily_tasks_list:
            if task["id"] == task_id:
                if not self.is_task_complete(task_id):
                    return False, "任务未完成"
                
                for reward, amount in task["rewards"].items():
                    if reward in data["resources"]:
                        data["resources"][reward] += amount
                    else:
                        data["resources"][reward] = amount
                
                data["task_chains"]["claimed_rewards"].append(task_id)
                save()
                return True, task["rewards"]
        
        # 检查每周任务
        for task in self.weekly_tasks_list:
            if task["id"] == task_id:
                if not self.is_task_complete(task_id):
                    return False, "任务未完成"
                
                for reward, amount in task["rewards"].items():
                    if reward in data["resources"]:
                        data["resources"][reward] += amount
                    else:
                        data["resources"][reward] = amount
                
                data["task_chains"]["claimed_rewards"].append(task_id)
                save()
                return True, task["rewards"]
        
        return False, "任务不存在"
    
    def check_chain_complete(self, chain_id):
        """检查任务链是否完成"""
        chain = next((c for c in self.task_chains if c["id"] == chain_id), None)
        if not chain:
            return False
        
        if chain_id in data["task_chains"]["completed_chains"]:
            return True
        
        for task in chain["tasks"]:
            if not self.is_task_complete(task["id"]):
                return False
        
        return True
    
    def claim_chain_reward(self, chain_id):
        """领取任务链奖励"""
        if chain_id in data["task_chains"]["completed_chains"]:
            return False, "任务链已完成"
        
        chain = next((c for c in self.task_chains if c["id"] == chain_id), None)
        if not chain:
            return False, "任务链不存在"
        
        if not self.check_chain_complete(chain_id):
            return False, "任务链未完成"
        
        # 发放奖励
        for reward, amount in chain["rewards"].items():
            if reward in data["resources"]:
                data["resources"][reward] += amount
            else:
                data["resources"][reward] = amount
        
        data["task_chains"]["completed_chains"].append(chain_id)
        save()
        
        return True, chain["rewards"]
    
    def get_active_chains(self):
        """获取活跃的任务链"""
        active = []
        
        for chain in self.task_chains:
            # 检查解锁条件
            if chain["unlock_condition"]:
                required_chain = chain["unlock_condition"].get("chain")
                if required_chain and required_chain not in data["task_chains"]["completed_chains"]:
                    continue
            
            active.append(chain)
        
        return active
    
    def get_daily_tasks(self):
        """获取每日任务"""
        result = []
        for task_id in data["task_chains"]["daily_tasks"]:
            task = next((t for t in self.daily_tasks_list if t["id"] == task_id), None)
            if task:
                result.append({
                    "id": task["id"],
                    "name": task["name"],
                    "description": task["description"],
                    "target": task["target"],
                    "current": data["task_chains"]["task_progress"].get(task["id"], 0),
                    "rewards": task["rewards"],
                    "claimed": task["id"] in data["task_chains"]["claimed_rewards"]
                })
        return result
    
    def get_weekly_tasks(self):
        """获取每周任务"""
        result = []
        for task_id in data["task_chains"]["weekly_tasks"]:
            task = next((t for t in self.weekly_tasks_list if t["id"] == task_id), None)
            if task:
                result.append({
                    "id": task["id"],
                    "name": task["name"],
                    "description": task["description"],
                    "target": task["target"],
                    "current": data["task_chains"]["task_progress"].get(task["id"], 0),
                    "rewards": task["rewards"],
                    "claimed": task["id"] in data["task_chains"]["claimed_rewards"]
                })
        return result