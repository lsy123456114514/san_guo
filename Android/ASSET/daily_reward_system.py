import time
import json
import os
from ASSET.game_data import data, save, default_save, logger, draw_gradient_bg, cull_dead, get_font

class DailyRewardSystem:
    """每日签到奖励系统"""
    
    def __init__(self):
        # 确保数据存在
        if "daily_reward" not in data:
            data["daily_reward"] = {
                "last_checkin_date": "",
                "consecutive_days": 0,
                "monthly_checkins": 0,
                "claimed_rewards": [],
                "current_month": 0
            }
        
        self.rewards = self._load_rewards()
    
    def _load_rewards(self):
        """加载签到奖励配置"""
        return [
            {"day": 1, "rewards": {"金元宝": 50, "经验": 100}, "bonus": None},
            {"day": 2, "rewards": {"金元宝": 60, "经验": 150}, "bonus": None},
            {"day": 3, "rewards": {"金元宝": 70, "经验": 200}, "bonus": None},
            {"day": 4, "rewards": {"金元宝": 80, "经验": 250}, "bonus": None},
            {"day": 5, "rewards": {"金元宝": 100, "经验": 300}, "bonus": {"item": "中级经验丹", "count": 1}},
            {"day": 6, "rewards": {"金元宝": 120, "经验": 350}, "bonus": None},
            {"day": 7, "rewards": {"金元宝": 200, "经验": 500}, "bonus": {"item": "高级招募令", "count": 1}},
            {"day": 8, "rewards": {"金元宝": 100, "经验": 200}, "bonus": None},
            {"day": 9, "rewards": {"金元宝": 110, "经验": 250}, "bonus": None},
            {"day": 10, "rewards": {"金元宝": 120, "经验": 300}, "bonus": {"item": "中级经验丹", "count": 2}},
            {"day": 11, "rewards": {"金元宝": 130, "经验": 350}, "bonus": None},
            {"day": 12, "rewards": {"金元宝": 140, "经验": 400}, "bonus": None},
            {"day": 13, "rewards": {"金元宝": 150, "经验": 450}, "bonus": None},
            {"day": 14, "rewards": {"金元宝": 300, "经验": 600}, "bonus": {"item": "顶级招募令", "count": 1}},
            {"day": 15, "rewards": {"金元宝": 150, "经验": 300}, "bonus": {"item": "装备精炼石", "count": 5}},
            {"day": 16, "rewards": {"金元宝": 160, "经验": 350}, "bonus": None},
            {"day": 17, "rewards": {"金元宝": 170, "经验": 400}, "bonus": None},
            {"day": 18, "rewards": {"金元宝": 180, "经验": 450}, "bonus": None},
            {"day": 19, "rewards": {"金元宝": 190, "经验": 500}, "bonus": {"item": "中级经验丹", "count": 3}},
            {"day": 20, "rewards": {"金元宝": 200, "经验": 550}, "bonus": {"item": "高级招募令", "count": 1}},
            {"day": 21, "rewards": {"金元宝": 210, "经验": 600}, "bonus": None},
            {"day": 22, "rewards": {"金元宝": 220, "经验": 650}, "bonus": None},
            {"day": 23, "rewards": {"金元宝": 230, "经验": 700}, "bonus": None},
            {"day": 24, "rewards": {"金元宝": 240, "经验": 750}, "bonus": None},
            {"day": 25, "rewards": {"金元宝": 250, "经验": 800}, "bonus": {"item": "顶级招募令", "count": 1}},
            {"day": 26, "rewards": {"金元宝": 260, "经验": 850}, "bonus": {"item": "装备精炼石", "count": 10}},
            {"day": 27, "rewards": {"金元宝": 270, "经验": 900}, "bonus": None},
            {"day": 28, "rewards": {"金元宝": 280, "经验": 950}, "bonus": None},
            {"day": 29, "rewards": {"金元宝": 290, "经验": 1000}, "bonus": None},
            {"day": 30, "rewards": {"金元宝": 500, "经验": 1500}, "bonus": {"item": "稀有武将碎片", "count": 50}}
        ]
    
    def _get_today(self):
        """获取今天的日期字符串"""
        return time.strftime("%Y-%m-%d")
    
    def _get_current_month(self):
        """获取当前月份"""
        return int(time.strftime("%Y%m"))
    
    def can_checkin(self):
        """检查是否可以签到"""
        today = self._get_today()
        return data["daily_reward"]["last_checkin_date"] != today
    
    def get_consecutive_days(self):
        """获取连续签到天数"""
        return data["daily_reward"]["consecutive_days"]
    
    def get_monthly_checkins(self):
        """获取本月签到次数"""
        # 检查是否跨月
        current_month = self._get_current_month()
        if data["daily_reward"]["current_month"] != current_month:
            data["daily_reward"]["monthly_checkins"] = 0
            data["daily_reward"]["current_month"] = current_month
            save()
        return data["daily_reward"]["monthly_checkins"]
    
    def claim_reward(self):
        """领取签到奖励"""
        if not self.can_checkin():
            return False, "今天已经签到过了"
        
        today = self._get_today()
        current_month = self._get_current_month()
        
        # 检查是否跨月或跨年
        if data["daily_reward"]["current_month"] != current_month:
            data["daily_reward"]["monthly_checkins"] = 0
            data["daily_reward"]["current_month"] = current_month
            data["daily_reward"]["consecutive_days"] = 0
        
        # 检查是否连续签到
        last_date = data["daily_reward"]["last_checkin_date"]
        if last_date:
            last_time = time.mktime(time.strptime(last_date, "%Y-%m-%d"))
            today_time = time.mktime(time.strptime(today, "%Y-%m-%d"))
            days_diff = (today_time - last_time) / (24 * 3600)
            
            if days_diff == 1:
                data["daily_reward"]["consecutive_days"] += 1
            elif days_diff > 1:
                data["daily_reward"]["consecutive_days"] = 1
        else:
            data["daily_reward"]["consecutive_days"] = 1
        
        # 增加本月签到次数
        data["daily_reward"]["monthly_checkins"] += 1
        data["daily_reward"]["last_checkin_date"] = today
        
        # 获取奖励
        day = data["daily_reward"]["monthly_checkins"]
        if day <= len(self.rewards):
            reward = self.rewards[day - 1]
            claimed_id = f"{current_month}_{day}"
            
            # 发放奖励
            for resource, amount in reward["rewards"].items():
                if resource in data["resources"]:
                    data["resources"][resource] += amount
                else:
                    data["resources"][resource] = amount
            
            # 发放额外奖励
            if reward["bonus"]:
                bonus_item = reward["bonus"]["item"]
                bonus_count = reward["bonus"]["count"]
                if "items" not in data:
                    data["items"] = {}
                if bonus_item in data["items"]:
                    data["items"][bonus_item] += bonus_count
                else:
                    data["items"][bonus_item] = bonus_count
            
            data["daily_reward"]["claimed_rewards"].append(claimed_id)
            save()
            
            return True, reward
        else:
            return False, "本月签到次数已达上限"
    
    def get_today_reward(self):
        """获取今日奖励预览"""
        month_checkins = self.get_monthly_checkins()
        next_day = month_checkins + 1
        if next_day <= len(self.rewards):
            return self.rewards[next_day - 1]
        return None
    
    def get_rewards_status(self):
        """获取所有奖励状态"""
        current_month = self._get_current_month()
        status = []
        
        for i, reward in enumerate(self.rewards):
            day = i + 1
            claimed_id = f"{current_month}_{day}"
            claimed = claimed_id in data["daily_reward"]["claimed_rewards"]
            available = day <= self.get_monthly_checkins() + 1
            
            status.append({
                "day": day,
                "rewards": reward["rewards"],
                "bonus": reward["bonus"],
                "claimed": claimed,
                "available": available
            })
        
        return status