import time
from ASSET.game_data import data, save

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
        """加载武将图鉴数据"""
        return [
            # 蜀国武将
            {"id": "hero_zhaoyun", "name": "赵云", "faction": "蜀", "rarity": "legendary", "description": "一身是胆，长坂坡七进七出", "skill": "龙胆", "element": "风"},
            {"id": "hero_guanyu", "name": "关羽", "faction": "蜀", "rarity": "legendary", "description": "武圣，青龙偃月刀无敌", "skill": "青龙斩", "element": "雷"},
            {"id": "hero_zhangfei", "name": "张飞", "faction": "蜀", "rarity": "legendary", "description": "猛张飞，当阳桥吓退曹军", "skill": "咆哮", "element": "火"},
            {"id": "hero_maochao", "name": "马超", "faction": "蜀", "rarity": "rare", "description": "西凉马超，勇冠三军", "skill": "铁骑", "element": "风"},
            {"id": "hero_huangzhong", "name": "黄忠", "faction": "蜀", "rarity": "rare", "description": "老当益壮，百步穿杨", "skill": "箭术", "element": "土"},
            {"id": "hero_zhugekongming", "name": "诸葛亮", "faction": "蜀", "rarity": "legendary", "description": "卧龙先生，智谋无双", "skill": "空城计", "element": "水"},
            {"id": "hero_liubei", "name": "刘备", "faction": "蜀", "rarity": "legendary", "description": "蜀汉开国皇帝，仁德著称", "skill": "仁德", "element": "土"},
            {"id": "hero_weiyan", "name": "魏延", "faction": "蜀", "rarity": "common", "description": "蜀汉猛将", "skill": "反骨", "element": "火"},
            {"id": "hero_pangtong", "name": "庞统", "faction": "蜀", "rarity": "rare", "description": "凤雏，与卧龙齐名", "skill": "连环计", "element": "水"},
            {"id": "hero_jiangwei", "name": "姜维", "faction": "蜀", "rarity": "rare", "description": "继承武侯遗志", "skill": "九伐中原", "element": "风"},
            
            # 魏国武将
            {"id": "hero_caocao", "name": "曹操", "faction": "魏", "rarity": "legendary", "description": "乱世枭雄，挟天子以令诸侯", "skill": "奸雄", "element": "暗"},
            {"id": "hero_zhangliao", "name": "张辽", "faction": "魏", "rarity": "rare", "description": "威震逍遥津", "skill": "八百破十万", "element": "风"},
            {"id": "hero_xuchu", "name": "许褚", "faction": "魏", "rarity": "rare", "description": "虎痴，力大无穷", "skill": "蛮力", "element": "土"},
            {"id": "hero_dianwei", "name": "典韦", "faction": "魏", "rarity": "rare", "description": "古之恶来，忠心护主", "skill": "双戟", "element": "火"},
            {"id": "hero_sima yi", "name": "司马懿", "faction": "魏", "rarity": "legendary", "description": "冢虎，隐忍待时", "skill": "隐忍", "element": "暗"},
            {"id": "hero_xunyu", "name": "荀彧", "faction": "魏", "rarity": "rare", "description": "王佐之才", "skill": "王佐", "element": "水"},
            {"id": "hero_guojia", "name": "郭嘉", "faction": "魏", "rarity": "rare", "description": "鬼才，英年早逝", "skill": "十胜十败", "element": "风"},
            {"id": "hero_zhuangxiu", "name": "夏侯惇", "faction": "魏", "rarity": "common", "description": "独眼将军", "skill": "拔矢啖睛", "element": "火"},
            {"id": "hero_zhanghe", "name": "张郃", "faction": "魏", "rarity": "common", "description": "河北四庭柱之一", "skill": "巧变", "element": "土"},
            {"id": "hero_jiaxu", "name": "贾诩", "faction": "魏", "rarity": "rare", "description": "毒士，计谋深远", "skill": "毒计", "element": "暗"},
            
            # 吴国武将
            {"id": "hero_zhouyu", "name": "周瑜", "faction": "吴", "rarity": "legendary", "description": "大都督，雄姿英发", "skill": "火烧赤壁", "element": "火"},
            {"id": "hero_sunquan", "name": "孙权", "faction": "吴", "rarity": "legendary", "description": "江东之主，碧眼紫髯", "skill": "江东之虎", "element": "水"},
            {"id": "hero_gan ning", "name": "甘宁", "faction": "吴", "rarity": "rare", "description": "锦帆贼，勇猛善战", "skill": "百骑劫营", "element": "水"},
            {"id": "hero_lvmeng", "name": "吕蒙", "faction": "吴", "rarity": "rare", "description": "士别三日，刮目相看", "skill": "白衣渡江", "element": "水"},
            {"id": "hero_luxun", "name": "陆逊", "faction": "吴", "rarity": "legendary", "description": "儒将，火烧连营", "skill": "火攻", "element": "火"},
            {"id": "hero_sunce", "name": "孙策", "faction": "吴", "rarity": "rare", "description": "小霸王，英年早逝", "skill": "霸王", "element": "风"},
            {"id": "hero_huanggai", "name": "黄盖", "faction": "吴", "rarity": "common", "description": "苦肉计，火烧赤壁", "skill": "苦肉计", "element": "火"},
            {"id": "hero_zhengjiang", "name": "蒋钦", "faction": "吴", "rarity": "common", "description": "江东十二虎臣", "skill": "水战", "element": "水"},
            {"id": "hero_xuzhou", "name": "徐盛", "faction": "吴", "rarity": "common", "description": "江东十二虎臣", "skill": "疑城", "element": "土"},
            {"id": "hero_panzhang", "name": "潘璋", "faction": "吴", "rarity": "common", "description": "擒获关羽", "skill": "擒将", "element": "土"},
            
            # 群雄武将
            {"id": "hero_lvbu", "name": "吕布", "faction": "群雄", "rarity": "legendary", "description": "人中吕布，马中赤兔", "skill": "方天画戟", "element": "雷"},
            {"id": "hero_diaochan", "name": "貂蝉", "faction": "群雄", "rarity": "legendary", "description": "绝世美女，连环计", "skill": "倾城", "element": "水"},
            {"id": "hero_huatuo", "name": "华佗", "faction": "群雄", "rarity": "rare", "description": "神医，妙手回春", "skill": "青囊", "element": "木"},
            {"id": "hero_dongzhuo", "name": "董卓", "faction": "群雄", "rarity": "common", "description": "西凉军阀，祸乱朝纲", "skill": "残暴", "element": "火"},
            {"id": "hero_luoyang", "name": "袁绍", "faction": "群雄", "rarity": "rare", "description": "四世三公，河北霸主", "skill": "名门", "element": "土"},
            {"id": "hero_yingxiong", "name": "袁术", "faction": "群雄", "rarity": "common", "description": "仲家皇帝", "skill": "称帝", "element": "土"},
            {"id": "hero_wangyun", "name": "王允", "faction": "群雄", "rarity": "common", "description": "连环计策划者", "skill": "连环", "element": "水"},
            {"id": "hero_xiahouyuan", "name": "夏侯渊", "faction": "群雄", "rarity": "common", "description": "用兵神速", "skill": "神速", "element": "风"},
            {"id": "hero_caohong", "name": "曹洪", "faction": "群雄", "rarity": "common", "description": "舍命救主", "skill": "忠勇", "element": "火"},
            {"id": "hero_zhangji", "name": "张济", "faction": "群雄", "rarity": "common", "description": "西凉军将领", "skill": "劫掠", "element": "风"}
        ]
    
    def _load_collection_bonuses(self):
        """加载收集奖励配置"""
        return [
            {"id": "bonus_5", "name": "初窥门径", "description": "收集5名武将", "target": 5, "rewards": {"金元宝": 200, "经验": 300}},
            {"id": "bonus_10", "name": "小有成就", "description": "收集10名武将", "target": 10, "rewards": {"金元宝": 500, "中级经验丹": 2}},
            {"id": "bonus_15", "name": "人才济济", "description": "收集15名武将", "target": 15, "rewards": {"金元宝": 800, "高级招募令": 1}},
            {"id": "bonus_20", "name": "群英荟萃", "description": "收集20名武将", "target": 20, "rewards": {"金元宝": 1200, "顶级招募令": 1}},
            {"id": "bonus_25", "name": "名将如云", "description": "收集25名武将", "target": 25, "rewards": {"金元宝": 1500, "稀有武将碎片": 30}},
            {"id": "bonus_30", "name": "天下名将", "description": "收集30名武将", "target": 30, "rewards": {"金元宝": 2000, "传说武将碎片": 50}},
            {"id": "bonus_35", "name": "威震天下", "description": "收集35名武将", "target": 35, "rewards": {"金元宝": 3000, "顶级招募令": 2}},
            {"id": "bonus_all", "name": "天下无双", "description": "收集所有武将", "target": 40, "rewards": {"金元宝": 5000, "传说武将碎片": 200, "至尊称号": "名将收藏家"}}
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