import time
from ASSET.game_data import data, save

class ActivityCenter:
    """活动中心 - 借鉴冰河时代的活动推送机制"""
    
    def __init__(self):
        if "activities" not in data:
            data["activities"] = {
                "current": [],
                "upcoming": [],
                "history": [],
                "claimed_rewards": []
            }
        
        self.activities = self._load_activities()
        self._refresh_activities()
    
    def _load_activities(self):
        """加载活动配置"""
        return [
            {
                "id": "daily_login",
                "name": "每日登录",
                "description": "每日登录游戏领取奖励",
                "icon": "🎁",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "rewards": {"金元宝": 100, "经验": 200},
                "type": "daily"
            },
            {
                "id": "first_recharge",
                "name": "首充大礼",
                "description": "首次充值获得双倍奖励",
                "icon": "💰",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "rewards": {"金元宝": 500, "传说武将碎片": 50},
                "type": "limited"
            },
            {
                "id": "weekend_bonus",
                "name": "周末狂欢",
                "description": "周末登录领取双倍奖励",
                "icon": "🎉",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "rewards": {"金元宝": 300, "高级招募令": 1},
                "type": "weekend"
            },
            {
                "id": "consume_reward",
                "name": "消费返利",
                "description": "累计消费金元宝返利",
                "icon": "🛒",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "rewards": {"金元宝": 200, "稀有武将碎片": 30},
                "type": "consume"
            },
            {
                "id": "battle_pass",
                "name": "战斗通行证",
                "description": "完成赛季任务获得奖励",
                "icon": "⚔️",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "rewards": {"金元宝": 1000, "顶级招募令": 2},
                "type": "season"
            },
            {
                "id": "new_server",
                "name": "新手特惠",
                "description": "新服务器专属福利",
                "icon": "🌟",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "rewards": {"金元宝": 800, "传说武将": 1},
                "type": "newbie"
            },
            {
                "id": "festival_spring",
                "name": "春季庆典",
                "description": "春季限时活动",
                "icon": "🌸",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "rewards": {"金元宝": 500, "春季限定皮肤": 1},
                "type": "seasonal"
            },
            {
                "id": "anniversary",
                "name": "周年庆典",
                "description": "周年庆典限时福利",
                "icon": "🎂",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "rewards": {"金元宝": 2000, "周年限定武将": 1},
                "type": "limited"
            }
        ]
    
    def _refresh_activities(self):
        """刷新活动状态"""
        current_time = time.time()
        
        for activity in self.activities:
            if activity["id"] in data["activities"]["claimed_rewards"]:
                continue
            
            if activity["type"] == "daily":
                daily_reward = data.get("daily_reward", {})
                last_checkin = daily_reward.get("last_checkin_date", "")
                today = time.strftime("%Y-%m-%d")
                
                if last_checkin != today:
                    if activity not in data["activities"]["current"]:
                        data["activities"]["current"].append(activity["id"])
            elif activity["type"] == "weekend":
                weekday = time.strftime("%w")
                if weekday in ["0", "6"]:
                    if activity not in data["activities"]["current"]:
                        data["activities"]["current"].append(activity["id"])
            elif activity["type"] == "season":
                season = data.get("season", {})
                if season.get("season_points", 0) > 0:
                    if activity not in data["activities"]["current"]:
                        data["activities"]["current"].append(activity["id"])
    
    def claim_reward(self, activity_id):
        """领取活动奖励"""
        if activity_id in data["activities"]["claimed_rewards"]:
            return False, "奖励已领取"
        
        activity = next((a for a in self.activities if a["id"] == activity_id), None)
        if not activity:
            return False, "活动不存在"
        
        rewards = activity["rewards"]
        
        for reward_type, amount in rewards.items():
            if reward_type in data["resources"]:
                data["resources"][reward_type] += amount
            else:
                data["resources"][reward_type] = amount
        
        data["activities"]["claimed_rewards"].append(activity_id)
        
        if activity_id in data["activities"]["current"]:
            data["activities"]["current"].remove(activity_id)
        
        save()
        
        return True, rewards
    
    def get_current_activities(self):
        """获取当前活动"""
        result = []
        for activity_id in data["activities"]["current"]:
            activity = next((a for a in self.activities if a["id"] == activity_id), None)
            if activity:
                result.append({
                    "id": activity["id"],
                    "name": activity["name"],
                    "description": activity["description"],
                    "icon": activity["icon"],
                    "rewards": activity["rewards"],
                    "type": activity["type"],
                    "claimed": activity_id in data["activities"]["claimed_rewards"]
                })
        return result
    
    def get_all_activities(self):
        """获取所有活动"""
        return [{
            "id": a["id"],
            "name": a["name"],
            "description": a["description"],
            "icon": a["icon"],
            "rewards": a["rewards"],
            "type": a["type"],
            "claimed": a["id"] in data["activities"]["claimed_rewards"]
        } for a in self.activities]


class MailSystem:
    """邮件系统 - 游戏内消息和奖励发放"""
    
    def __init__(self):
        if "mail" not in data:
            data["mail"] = {
                "inbox": [],
                "sent": [],
                "archived": []
            }
        
        self._check_system_mails()
    
    def _check_system_mails(self):
        """检查系统邮件"""
        achievements = data.get("achievements", {})
        unclaimed_achievements = [a for a in achievements.get("unlocked", []) 
                                if a not in achievements.get("claimed_rewards", [])]
        
        if unclaimed_achievements:
            self.add_mail(
                sender="系统",
                title="🏅 成就奖励待领取",
                content=f"您有{len(unclaimed_achievements)}个成就奖励待领取，快去领取吧！",
                attachments={"金元宝": 50},
                mail_type="achievement"
            )
        
        task_chains = data.get("task_chains", {})
        if task_chains.get("completed_chains"):
            self.add_mail(
                sender="系统",
                title="⚔️ 任务链完成奖励",
                content="恭喜您完成了任务链，快来领取奖励吧！",
                attachments={"金元宝": 100},
                mail_type="task"
            )
    
    def add_mail(self, sender, title, content, attachments=None, mail_type="system"):
        """添加邮件"""
        mail = {
            "id": int(time.time() * 1000),
            "sender": sender,
            "title": title,
            "content": content,
            "attachments": attachments or {},
            "type": mail_type,
            "time": time.time(),
            "read": False,
            "claimed": False
        }
        
        data["mail"]["inbox"].append(mail)
        
        if len(data["mail"]["inbox"]) > 100:
            oldest = data["mail"]["inbox"].pop(0)
            data["mail"]["archived"].append(oldest)
        
        save()
    
    def read_mail(self, mail_id):
        """读取邮件"""
        for mail in data["mail"]["inbox"]:
            if mail["id"] == mail_id:
                mail["read"] = True
                save()
                return mail
        return None
    
    def claim_attachment(self, mail_id):
        """领取附件"""
        for mail in data["mail"]["inbox"]:
            if mail["id"] == mail_id:
                if mail["claimed"]:
                    return False, "附件已领取"
                
                attachments = mail.get("attachments", {})
                if not attachments:
                    return False, "无附件"
                
                for reward_type, amount in attachments.items():
                    if reward_type in data["resources"]:
                        data["resources"][reward_type] += amount
                    else:
                        data["resources"][reward_type] = amount
                
                mail["claimed"] = True
                save()
                
                return True, attachments
        
        return False, "邮件不存在"
    
    def delete_mail(self, mail_id):
        """删除邮件"""
        for mail in data["mail"]["inbox"]:
            if mail["id"] == mail_id:
                data["mail"]["inbox"].remove(mail)
                data["mail"]["archived"].append(mail)
                save()
                return True
        return False
    
    def get_unread_count(self):
        """获取未读邮件数量"""
        return sum(1 for mail in data["mail"]["inbox"] if not mail["read"])
    
    def get_inbox(self):
        """获取收件箱"""
        return [{
            "id": m["id"],
            "sender": m["sender"],
            "title": m["title"],
            "content": m["content"],
            "attachments": m.get("attachments", {}),
            "type": m["type"],
            "time": m["time"],
            "read": m["read"],
            "claimed": m["claimed"]
        } for m in data["mail"]["inbox"]]


class CheckinCalendar:
    """签到日历 - 现代化签到界面"""
    
    def __init__(self):
        if "checkin_calendar" not in data:
            data["checkin_calendar"] = {
                "current_month": time.strftime("%Y-%m"),
                "checkins": {},
                "monthly_rewards_claimed": [],
                "streak_rewards_claimed": []
            }
        
        self._check_new_month()
    
    def _check_new_month(self):
        """检查是否新月"""
        current_month = time.strftime("%Y-%m")
        if data["checkin_calendar"]["current_month"] != current_month:
            data["checkin_calendar"]["current_month"] = current_month
            data["checkin_calendar"]["monthly_rewards_claimed"] = []
            save()
    
    def can_checkin(self):
        """检查是否可以签到"""
        today = time.strftime("%Y-%m-%d")
        return today not in data["checkin_calendar"]["checkins"]
    
    def checkin(self):
        """签到"""
        if not self.can_checkin():
            return False, "今天已签到"
        
        today = time.strftime("%Y-%m-%d")
        data["checkin_calendar"]["checkins"][today] = time.time()
        
        self._update_daily_reward_streak()
        
        save()
        return True, self._get_checkin_reward()
    
    def _update_daily_reward_streak(self):
        """更新每日奖励系统"""
        daily_reward = data.get("daily_reward", {})
        today = time.strftime("%Y-%m-%d")
        
        if daily_reward.get("last_checkin_date"):
            last_date = daily_reward["last_checkin_date"]
            last_time = time.mktime(time.strptime(last_date, "%Y-%m-%d"))
            today_time = time.mktime(time.strptime(today, "%Y-%m-%d"))
            days_diff = (today_time - last_time) / (24 * 3600)
            
            if days_diff == 1:
                daily_reward["consecutive_days"] += 1
            elif days_diff > 1:
                daily_reward["consecutive_days"] = 1
        else:
            daily_reward["consecutive_days"] = 1
        
        daily_reward["last_checkin_date"] = today
        daily_reward["monthly_checkins"] = daily_reward.get("monthly_checkins", 0) + 1
        
        save()
    
    def _get_checkin_reward(self):
        """获取签到奖励"""
        consecutive = data.get("daily_reward", {}).get("consecutive_days", 0)
        
        rewards = [
            {"金元宝": 50, "经验": 100},
            {"金元宝": 60, "经验": 150},
            {"金元宝": 70, "经验": 200},
            {"金元宝": 80, "经验": 250},
            {"金元宝": 100, "经验": 300, "item": "中级经验丹"},
            {"金元宝": 120, "经验": 350},
            {"金元宝": 200, "经验": 500, "item": "高级招募令"}
        ]
        
        day_index = (consecutive - 1) % 7
        reward = rewards[day_index]
        
        for reward_type, amount in reward.items():
            if reward_type == "item":
                if "items" not in data:
                    data["items"] = {}
                data["items"][amount] = data["items"].get(amount, 0) + 1
            else:
                if reward_type in data["resources"]:
                    data["resources"][reward_type] += amount
                else:
                    data["resources"][reward_type] = amount
        
        return reward
    
    def get_month_checkins(self):
        """获取本月签到情况"""
        current_month = data["checkin_calendar"]["current_month"]
        checkins = data["checkin_calendar"]["checkins"]
        
        days_in_month = self._get_days_in_month()
        
        result = []
        for day in range(1, days_in_month + 1):
            date_str = f"{current_month}-{day:02d}"
            checked = date_str in checkins
            is_today = date_str == time.strftime("%Y-%m-%d")
            
            result.append({
                "day": day,
                "date": date_str,
                "checked": checked,
                "is_today": is_today
            })
        
        return result
    
    def _get_days_in_month(self):
        """获取当月天数"""
        current = data["checkin_calendar"]["current_month"]
        year, month = map(int, current.split("-"))
        
        if month == 12:
            next_month = f"{year + 1}-01"
        else:
            next_month = f"{year}-{month + 1:02d}"
        
        days = (time.strptime(next_month, "%Y-%m-%d")[:2] if month != 12 
                else (year + 1, 1))
        
        if isinstance(days, tuple) and len(days) == 2:
            year, month = days
            if month == 1:
                year -= 1
            month = 12 if month == 1 else month - 1
        
        from calendar import monthrange
        return monthrange(year, month)[1]
    
    def claim_monthly_reward(self):
        """领取月累计奖励"""
        month_checkins = sum(1 for c in self.get_month_checkins() if c["checked"])
        current_month = data["checkin_calendar"]["current_month"]
        
        if month_checkins < 15:
            return False, f"本月签到{month_checkins}天，需要15天才能领取"
        
        if current_month in data["checkin_calendar"]["monthly_rewards_claimed"]:
            return False, "本月奖励已领取"
        
        rewards = {"金元宝": 500, "稀有武将碎片": 30}
        
        for reward_type, amount in rewards.items():
            if reward_type in data["resources"]:
                data["resources"][reward_type] += amount
            else:
                data["resources"][reward_type] = amount
        
        data["checkin_calendar"]["monthly_rewards_claimed"].append(current_month)
        save()
        
        return True, rewards
    
    def get_streak_rewards(self):
        """获取连续签到奖励配置"""
        return [
            {"days": 7, "name": "一周签到", "rewards": {"金元宝": 100, "中级经验丹": 1}},
            {"days": 14, "name": "两周签到", "rewards": {"金元宝": 200, "高级招募令": 1}},
            {"days": 21, "name": "三周签到", "rewards": {"金元宝": 300, "稀有武将碎片": 20}},
            {"days": 30, "name": "整月签到", "rewards": {"金元宝": 500, "传说武将碎片": 30}}
        ]


class LeaderboardSystem:
    """排行榜系统 - 借鉴冰河时代的竞争机制"""
    
    def __init__(self):
        if "leaderboard" not in data:
            data["leaderboard"] = {
                "player_rank": 0,
                "categories": {
                    "power": [],
                    "wealth": [],
                    "achievements": [],
                    "pvp": []
                }
            }
        
        self.categories = ["power", "wealth", "achievements", "pvp"]
    
    def update_rankings(self):
        """更新排行榜"""
        self._update_power_ranking()
        self._update_wealth_ranking()
        self._update_achievement_ranking()
        self._update_pvp_ranking()
    
    def _update_power_ranking(self):
        """更新战力排行"""
        power = 0
        for hero in data.get("heroes", {}).values():
            power += hero.get("attack", 0) + hero.get("defense", 0)
        
        player_entry = {
            "player_id": "player",
            "player_name": data.get("username", "玩家"),
            "score": power,
            "time": time.time()
        }
        
        rankings = data["leaderboard"]["categories"]["power"]
        
        for entry in rankings:
            if entry["player_id"] == "player":
                rankings.remove(entry)
                break
        
        rankings.append(player_entry)
        rankings.sort(key=lambda x: x["score"], reverse=True)
        rankings[:100]
        
        for i, entry in enumerate(rankings):
            if entry["player_id"] == "player":
                data["leaderboard"]["player_rank"] = i + 1
                break
    
    def _update_wealth_ranking(self):
        """更新财富排行"""
        total_gold = data.get("resources", {}).get("金元宝", 0)
        
        player_entry = {
            "player_id": "player",
            "player_name": data.get("username", "玩家"),
            "score": total_gold,
            "time": time.time()
        }
        
        rankings = data["leaderboard"]["categories"]["wealth"]
        
        for entry in rankings:
            if entry["player_id"] == "player":
                rankings.remove(entry)
                break
        
        rankings.append(player_entry)
        rankings.sort(key=lambda x: x["score"], reverse=True)
        rankings[:100]
    
    def _update_achievement_ranking(self):
        """更新成就排行"""
        achievements_count = len(data.get("achievements", {}).get("unlocked", []))
        
        player_entry = {
            "player_id": "player",
            "player_name": data.get("username", "玩家"),
            "score": achievements_count,
            "time": time.time()
        }
        
        rankings = data["leaderboard"]["categories"]["achievements"]
        
        for entry in rankings:
            if entry["player_id"] == "player":
                rankings.remove(entry)
                break
        
        rankings.append(player_entry)
        rankings.sort(key=lambda x: x["score"], reverse=True)
        rankings[:100]
    
    def _update_pvp_ranking(self):
        """更新PVP排行"""
        victories = data.get("battle_stats", {}).get("victories", 0)
        
        player_entry = {
            "player_id": "player",
            "player_name": data.get("username", "玩家"),
            "score": victories,
            "time": time.time()
        }
        
        rankings = data["leaderboard"]["categories"]["pvp"]
        
        for entry in rankings:
            if entry["player_id"] == "player":
                rankings.remove(entry)
                break
        
        rankings.append(player_entry)
        rankings.sort(key=lambda x: x["score"], reverse=True)
        rankings[:100]
    
    def get_category_ranking(self, category):
        """获取指定分类的排行"""
        if category not in self.categories:
            return []
        
        rankings = data["leaderboard"]["categories"][category][:100]
        
        result = []
        for i, entry in enumerate(rankings):
            result.append({
                "rank": i + 1,
                "player_id": entry["player_id"],
                "player_name": entry["player_name"],
                "score": entry["score"]
            })
        
        return result
    
    def get_player_rank(self, category):
        """获取玩家在指定分类的排名"""
        if category not in self.categories:
            return 0
        
        rankings = data["leaderboard"]["categories"][category]
        
        for i, entry in enumerate(rankings):
            if entry["player_id"] == "player":
                return i + 1
        
        return 0
    
    def get_top_players(self, category, limit=10):
        """获取指定分类的前几名"""
        rankings = self.get_category_ranking(category)
        return rankings[:limit]
