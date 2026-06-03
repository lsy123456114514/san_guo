import json
import os
import platform
import pygame

def hide_file(filepath):
    """隐藏文件（仅Windows）"""
    if platform.system() == "Windows":
        try:
            if not filepath or not isinstance(filepath, str):
                return
            if not os.path.exists(filepath):
                return
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(filepath, 0x80)
            ctypes.windll.kernel32.SetFileAttributesW(filepath, 0x02)
        except Exception:
            pass

# 基础配置
RESOURCES = ["水", "煤炭", "木头", "食物", "金元宝", "时间卡", "宠物食物", "普通子弹", "高级子弹", "稀有子弹"]

# 字体变量 - 初始值
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None
FONT_TINY = None
# 枪械配置
GUNS = {
    "pistol": {
        "name": "手枪",
        "damage_multiplier": 1.5,
        "bullets_per_round": 1,
        "bullet_type": "普通子弹",
        "price": 50,
        "level": 1
    },
    "rifle": {
        "name": "步枪",
        "damage_multiplier": 2.0,
        "bullets_per_round": 2,
        "bullet_type": "高级子弹",
        "price": 100,
        "level": 2
    },
    "sniper": {
        "name": "狙击枪",
        "damage_multiplier": 2.5,
        "bullets_per_round": 1,
        "bullet_type": "稀有子弹",
        "price": 200,
        "level": 3
    },
    "machine_gun": {
        "name": "机枪",
        "damage_multiplier": 3.0,
        "bullets_per_round": 5,
        "bullet_type": "普通子弹",
        "price": 150,
        "level": 2
    }
}

# 武将羁绊配置 - 三国历史特色
HERO_BONDS = {
    "taoyuan": {
        "name": "桃园结义",
        "heroes": ["刘备", "关羽", "张飞"],
        "effect": {
            "type": "damage_bonus",
            "value": 0.3,
            "description": "攻击 +30%"
        }
    },
    "c_brothers": {
        "name": "曹氏兄弟",
        "heroes": ["曹操", "曹丕", "曹植"],
        "effect": {
            "type": "hp_bonus",
            "value": 0.25,
            "description": "生命 +25%"
        }
    },
    "five_tigers": {
        "name": "五虎上将",
        "heroes": ["关羽", "张飞", "赵云", "马超", "黄忠"],
        "effect": {
            "type": "crit_bonus",
            "value": 0.2,
            "description": "暴击 +20%"
        }
    },
    "liang_zhou": {
        "name": "卧龙凤雏",
        "heroes": ["诸葛亮", "庞统"],
        "effect": {
            "type": "skill_damage",
            "value": 0.35,
            "description": "技能伤害 +35%"
        }
    },
    "jiang_dong": {
        "name": "江东二乔",
        "heroes": ["大乔", "小乔"],
        "effect": {
            "type": "heal_bonus",
            "value": 0.3,
            "description": "治疗 +30%"
        }
    },
    "sun_family": {
        "name": "孙氏父子",
        "heroes": ["孙坚", "孙策", "孙权"],
        "effect": {
            "type": "speed_bonus",
            "value": 0.25,
            "description": "速度 +25%"
        }
    }
}

# 元素共鸣增强配置
ELEMENT_SYNERGIES = {
    "fire_fire": {"type": "burn", "damage": 15, "turns": 3, "desc": "灼烧：每回合15伤害，持续3回合"},
    "water_water": {"type": "heal", "amount": 20, "desc": "治愈：回复20生命"},
    "wood_wood": {"type": "shield", "amount": 25, "desc": "护盾：获得25点护盾"},
    "fire_water": {"type": "steam", "damage": 30, "desc": "蒸汽：对敌人造成30伤害"},
    "wood_fire": {"type": "wildfire", "damage": 35, "aoe": True, "desc": "野火：35伤害，可攻击所有敌人"},
    "water_fire": {"type": "steam", "damage": 30, "desc": "蒸汽：对敌人造成30伤害"},
    "fire_wood": {"type": "wildfire", "damage": 35, "aoe": True, "desc": "野火：35伤害，可攻击所有敌人"},
    "water_wood": {"type": "heal_shield", "heal": 15, "shield": 15, "desc": "生命之泉：回复15生命并获得15护盾"},
    "fire_metal": {"type": "lava", "damage": 40, "desc": "熔岩：40伤害，附带灼烧"},
    "water_metal": {"type": "frost", "damage": 25, "slow": 1, "desc": "寒冰：25伤害并减速1回合"}
}

# 元素弱点配置（玩家攻击敌人时）
ELEMENT_WEAKNESS = {
    "火": {"weak_to": "水", "bonus": 1.5, "desc": "火被水克制，伤害×1.5"},
    "水": {"weak_to": "雷", "bonus": 1.5, "desc": "水被雷克制，伤害×1.5"},
    "木": {"weak_to": "火", "bonus": 1.5, "desc": "木被火克制，伤害×1.5"},
    "雷": {"weak_to": "土", "bonus": 1.5, "desc": "雷被土克制，伤害×1.5"},
    "土": {"weak_to": "木", "bonus": 1.5, "desc": "土被木克制，伤害×1.5"},
    "风": {"weak_to": "土", "bonus": 1.5, "desc": "风被土克制，伤害×1.5"}
}

# 元素能量配置
ELEMENT_ENERGY = {
    "fire": {"color": (255, 100, 50), "max": 100},
    "water": {"color": (50, 150, 255), "max": 100},
    "wood": {"color": (100, 200, 100), "max": 100},
    "metal": {"color": (200, 200, 200), "max": 100},
    "earth": {"color": (180, 140, 100), "max": 100},
    "wind": {"color": (200, 200, 100), "max": 100}
}
# 路径适配：安卓用内部存储，PC用本地
if 'ANDROID_DATA' in os.environ:
    from android.storage import app_storage_path
    SAVE_PATH = os.path.join(app_storage_path(), "save.json")
else:
    SAVE_PATH = os.path.join(os.path.dirname(__file__), "save.json")
SOUND_DIR = os.path.join(os.path.dirname(__file__), "sounds")

# 全局设置
SETTINGS = {
    "graphics": {
        "resolution": "auto",  # 自动适应屏幕分辨率
        "fullscreen": False,
        "fps_limit": 60
    },
    "map": {
        "max_locations": 50
    },
    "sound": {
        "enable": True,
        "volume": 0.7
    },
    "language": {
        "current": "zh",
        "supported": ["zh", "en", "ja"]
    },
    "time": {
        "speed": 1,  # 时间流速倍率
        "base_time": 60  # 基础时间消耗（秒）
    }
}

def get_system_font_name():
    """跨系统中文字体适配（含安卓）"""
    # 打开日志文件
    try:
        log_file = open("debug.log", "a", encoding="utf-8")
        hide_file("debug.log")
    except Exception:
        log_file = None
    
    s = platform.system()
    if s == "Windows":
        # 尝试多个Windows中文字体，按优先级排序
        # 优先选择同时支持中文和emoji的字体
        font_list = [
            "Microsoft YaHei",      # 微软雅黑，优先选择这个，它在Windows上更常用
            "SimHei",               # 黑体
            "Microsoft YaHei UI",  # 微软雅黑UI
            "Segoe UI",             # Windows默认字体，支持emoji
            "Arial",                # 通用字体
            None                     # 默认字体
        ]
        for font_name in font_list:
            try:
                if font_name:
                    font = pygame.font.SysFont(font_name, 12)
                else:
                    font = pygame.font.Font(None, 12)
                
                # 测试字体是否能正确渲染中文
                test_text = "测试中文"
                test_surface = font.render(test_text, True, (255, 255, 255))
                if test_surface and test_surface.get_width() > 0:
                    # 写入日志文件
                    if log_file:
                        log_file.write(f"选择字体: {font_name if font_name else '默认字体'}\n")
                        log_file.close()
                    return font_name
            except Exception as e:
                # 写入日志文件
                if log_file:
                    log_file.write(f"字体 {font_name} 失败: {e}\n")
                continue
        # 关闭日志文件
        if log_file:
            log_file.close()
        return None
    elif s == "Darwin":
        if log_file:
            log_file.write("选择字体: PingFang SC\n")
            log_file.close()
        return "PingFang SC"
    elif s == "Linux" or 'ANDROID_DATA' in os.environ:
        if log_file:
            log_file.write("选择字体: DroidSansFallback\n")
            log_file.close()
        return "DroidSansFallback"  # 安卓默认中文字体
    
    # 关闭日志文件
    if log_file:
        log_file.close()
    return None

def load_sound(file_name: str):
    """加载音效：无文件/静音则跳过"""
    if not SETTINGS["sound"]["enable"]:
        return None
    sound_path = os.path.join(SOUND_DIR, file_name)
    if not os.path.exists(sound_path):
        return None
    try:
        sound = pygame.mixer.Sound(sound_path)
        sound.set_volume(SETTINGS["sound"]["volume"])
        return sound
    except Exception:
        return None

# 元素类型
ELEMENTS = ["火", "水", "土", "风", "雷"]

# 武将技能
HERO_SKILLS = {
    "赵云": {
        "name": "龙胆亮枪",
        "damage": 30,
        "element": "风",
        "description": "快速刺击，带有风元素伤害"
    },
    "关羽": {
        "name": "青龙偃月",
        "damage": 40,
        "element": "火",
        "description": "强力斩击，带有火元素伤害"
    },
    "张飞": {
        "name": "丈八蛇矛",
        "damage": 35,
        "element": "土",
        "description": "范围攻击，带有土元素伤害"
    },
    "诸葛亮": {
        "name": "八阵图",
        "damage": 45,
        "element": "雷",
        "description": "法术攻击，带有雷元素伤害"
    },
    "曹操": {
        "name": "魏武挥鞭",
        "damage": 38,
        "element": "火",
        "description": "统帅攻击，带有火元素伤害"
    },
    "吕布": {
        "name": "方天画戟",
        "damage": 50,
        "element": "雷",
        "description": "终极攻击，带有雷元素伤害"
    },
    "貂蝉": {
        "name": "倾国倾城",
        "damage": 25,
        "element": "水",
        "description": "魅惑攻击，带有水元素伤害"
    },
    "黄忠": {
        "name": "百步穿杨",
        "damage": 42,
        "element": "风",
        "description": "远程攻击，带有风元素伤害"
    },
    "马超": {
        "name": "西凉铁骑",
        "damage": 32,
        "element": "土",
        "description": "冲锋攻击，带有土元素伤害"
    },
    "周瑜": {
        "name": "火烧赤壁",
        "damage": 48,
        "element": "火",
        "description": "范围攻击，带有火元素伤害"
    },
    "刘备": {
        "name": "仁义之剑",
        "damage": 35,
        "element": "风",
        "description": "仁者无敌，带有风元素伤害"
    },
    "孙权": {
        "name": "江东之盾",
        "damage": 30,
        "element": "水",
        "description": "守护江东，带有水元素伤害"
    },
    "司马懿": {
        "name": "空城计",
        "damage": 45,
        "element": "雷",
        "description": "智谋无双，带有雷元素伤害"
    },
    "魏延": {
        "name": "反骨之勇",
        "damage": 40,
        "element": "火",
        "description": "勇猛无比，带有火元素伤害"
    },
    "庞统": {
        "name": "连环计",
        "damage": 42,
        "element": "土",
        "description": "计谋百出，带有土元素伤害"
    },
    "姜维": {
        "name": "天水麒麟",
        "damage": 38,
        "element": "风",
        "description": "麒麟之才，带有风元素伤害"
    },
    "许褚": {
        "name": "虎痴之力",
        "damage": 48,
        "element": "土",
        "description": "力大无穷，带有土元素伤害"
    },
    "典韦": {
        "name": "古之恶来",
        "damage": 50,
        "element": "火",
        "description": "恶来之勇，带有火元素伤害"
    },
    "张辽": {
        "name": "威震逍遥津",
        "damage": 45,
        "element": "风",
        "description": "威震八方，带有风元素伤害"
    },
    "甘宁": {
        "name": "锦帆贼",
        "damage": 40,
        "element": "水",
        "description": "水上霸主，带有水元素伤害"
    }
}

# 装备技能对应关系
EQUIP_SKILLS = {
    "weapon": {
        0: {"name": "普通攻击", "damage": 20, "description": "基础攻击"},
        1: {"name": "横扫千军", "damage": 30, "description": "范围攻击"},
        2: {"name": "破釜沉舟", "damage": 40, "description": "高伤害攻击"},
        3: {"name": "青龙偃月", "damage": 50, "description": "强力攻击"},
        4: {"name": "方天画戟", "damage": 60, "description": "终极攻击"},
        5: {"name": "丈八蛇矛", "damage": 65, "description": "大范围攻击"},
        6: {"name": "龙胆亮枪", "damage": 70, "description": "快速连续攻击"},
        7: {"name": "雌雄双股剑", "damage": 75, "description": "双重攻击"},
        8: {"name": "青釭剑", "damage": 80, "description": "破甲攻击"},
        9: {"name": "七星宝刀", "damage": 90, "description": "秒杀攻击"}
    },
    "armor": {
        0: {"name": "普通防御", "defense": 5, "description": "基础防御"},
        1: {"name": "铁布衫", "defense": 10, "description": "增强防御"},
        2: {"name": "金钟罩", "defense": 15, "description": "高级防御"},
        3: {"name": "玄武甲", "defense": 20, "description": "超强防御"},
        4: {"name": "麒麟甲", "defense": 25, "description": "终极防御"},
        5: {"name": "藤甲", "defense": 30, "description": "物理防御"},
        6: {"name": "明光铠", "defense": 35, "description": "全面防御"},
        7: {"name": "黄金甲", "defense": 40, "description": "皇家防御"},
        8: {"name": "锁子甲", "defense": 45, "description": "灵活防御"},
        9: {"name": "九龙甲", "defense": 50, "description": "无敌防御"}
    },
    "horse": {
        0: {"name": "普通坐骑", "speed": 1, "description": "基础速度"},
        1: {"name": "赤兔马", "speed": 2, "description": "增加速度"},
        2: {"name": "的卢马", "speed": 3, "description": "高级速度"},
        3: {"name": "汗血宝马", "speed": 4, "description": "超快速度"},
        4: {"name": "独角兽", "speed": 5, "description": "终极速度"},
        5: {"name": "爪黄飞电", "speed": 6, "description": "神速"},
        6: {"name": "绝影", "speed": 7, "description": "无影速度"},
        7: {"name": "惊帆", "speed": 8, "description": "疾风速度"},
        8: {"name": "乌云踏雪", "speed": 9, "description": "闪电速度"},
        9: {"name": "赤龙驹", "speed": 10, "description": "瞬间移动"}
    },
    "book": {
        0: {"name": "普通书籍", "critical": 0.05, "description": "基础暴击"},
        1: {"name": "孙子兵法", "critical": 0.1, "description": "增加暴击"},
        2: {"name": "鬼谷子", "critical": 0.15, "description": "高级暴击"},
        3: {"name": "周易", "critical": 0.2, "description": "超高暴击"},
        4: {"name": "天书", "critical": 0.25, "description": "终极暴击"},
        5: {"name": "三略", "critical": 0.3, "description": "战略暴击"},
        6: {"name": "六韬", "critical": 0.35, "description": "战术暴击"},
        7: {"name": "奇门遁甲", "critical": 0.4, "description": "神秘暴击"},
        8: {"name": "太平要术", "critical": 0.45, "description": "法术暴击"},
        9: {"name": "南华真经", "critical": 0.5, "description": "仙术暴击"}
    }
}

# 任务系统配置
DAILY_TASKS = [
    {
        "id": "daily_battle",
        "name": "日常战斗",
        "description": "完成3次战斗",
        "target": 3,
        "reward": {"金元宝": 20, "食物": 50},
        "type": "battle_completed"
    },
    {
        "id": "daily_explore",
        "name": "日常探索",
        "description": "探索5个地点",
        "target": 5,
        "reward": {"金元宝": 15, "水": 60},
        "type": "location_explored"
    },
    {
        "id": "daily_mini_game",
        "name": "日常小游戏",
        "description": "玩2次小游戏",
        "target": 2,
        "reward": {"金元宝": 10, "木头": 40},
        "type": "mini_game_played"
    },
    {
        "id": "daily_resource",
        "name": "日常资源",
        "description": "收集100资源",
        "target": 100,
        "reward": {"金元宝": 25, "煤炭": 30},
        "type": "resource_collected"
    }
]

WEEKLY_TASKS = [
    {
        "id": "weekly_battle",
        "name": "周常战斗",
        "description": "完成15次战斗",
        "target": 15,
        "reward": {"金元宝": 100, "食物": 200},
        "type": "battle_completed"
    },
    {
        "id": "weekly_explore",
        "name": "周常探索",
        "description": "探索20个地点",
        "target": 20,
        "reward": {"金元宝": 80, "水": 250},
        "type": "location_explored"
    },
    {
        "id": "weekly_mini_game",
        "name": "周常小游戏",
        "description": "玩10次小游戏",
        "target": 10,
        "reward": {"金元宝": 60, "木头": 180},
        "type": "mini_game_played"
    },
    {
        "id": "weekly_hero",
        "name": "周常武将",
        "description": "获得1个新武将",
        "target": 1,
        "reward": {"金元宝": 120, "煤炭": 150},
        "type": "hero_unlocked"
    }
]

# 成就系统配置
ACHIEVEMENTS = {
    "gameplay": [
        {
            "id": "first_game",
            "name": "初次尝试",
            "description": "完成第一个小游戏",
            "target": 1,
            "reward": {"金元宝": 10},
            "type": "mini_game_played"
        },
        {
            "id": "game_master",
            "name": "游戏大师",
            "description": "完成所有小游戏",
            "target": 7,
            "reward": {"金元宝": 100},
            "type": "mini_game_played"
        },
        {
            "id": "pvp_warrior",
            "name": "PVP勇士",
            "description": "参与10次PVP战斗",
            "target": 10,
            "reward": {"金元宝": 50},
            "type": "pvp_played"
        },
        {
            "id": "dungeon_crawler",
            "name": "副本探索者",
            "description": "完成10次副本挑战",
            "target": 10,
            "reward": {"金元宝": 50},
            "type": "dungeon_completed"
        }
    ],
    "collection": [
        {
            "id": "hero_collector",
            "name": "武将收集者",
            "description": "拥有3个武将",
            "target": 3,
            "reward": {"金元宝": 30},
            "type": "hero_owned"
        },
        {
            "id": "equipment_master",
            "name": "装备大师",
            "description": "拥有所有类型的装备",
            "target": 4,
            "reward": {"金元宝": 40},
            "type": "equipment_owned"
        }
    ],
    "resource": [
        {
            "id": "wealthy",
            "name": "富甲一方",
            "description": "拥有1000个金元宝",
            "target": 1000,
            "reward": {"金元宝": 200},
            "type": "gold_collected"
        },
        {
            "id": "resourceful",
            "name": "资源丰富",
            "description": "每种资源都达到100",
            "target": 100,
            "reward": {"金元宝": 50},
            "type": "resources_collected"
        }
    ]
}

# 时装系统配置
FASHION_ITEMS = {
    "hero_skins": {
        "normal": {
            "name": "默认皮肤",
            "description": "角色默认外观",
            "cost": {},
            "effects": {},
            "unlocked": True
        },
        "golden": {
            "name": "黄金战甲",
            "description": "金光闪闪的战甲，彰显尊贵",
            "cost": {"金元宝": 500},
            "effects": {"attack": 5},
            "unlocked": False
        },
        "dragon": {
            "name": "龙之化身",
            "description": "龙纹战甲，威风凛凛",
            "cost": {"金元宝": 800},
            "effects": {"attack": 10, "defense": 5},
            "unlocked": False
        },
        "phoenix": {
            "name": "凤凰涅槃",
            "description": "凤凰火羽，华丽非凡",
            "cost": {"金元宝": 1000},
            "effects": {"attack": 15, "defense": 10},
            "unlocked": False
        },
        "shadow": {
            "name": "暗影刺客",
            "description": "暗影缠身，神秘莫测",
            "cost": {"金元宝": 1200},
            "effects": {"attack": 20, "speed": 2},
            "unlocked": False
        },
        "immortal": {
            "name": "仙人之姿",
            "description": "仙人下凡，超凡脱俗",
            "cost": {"金元宝": 1500},
            "effects": {"attack": 25, "defense": 15, "speed": 3},
            "unlocked": False
        }
    },
    "weapon_skins": {
        "normal": {
            "name": "默认武器",
            "description": "武器默认外观",
            "cost": {},
            "effects": {},
            "unlocked": True
        },
        "golden": {
            "name": "黄金武器",
            "description": "黄金打造的武器，光芒四射",
            "cost": {"金元宝": 300},
            "effects": {"attack": 3},
            "unlocked": False
        },
        "dragon": {
            "name": "龙纹武器",
            "description": "刻有龙纹的武器，威力无穷",
            "cost": {"金元宝": 500},
            "effects": {"attack": 6},
            "unlocked": False
        },
        "crystal": {
            "name": "水晶武器",
            "description": "水晶铸造的武器，晶莹剔透",
            "cost": {"金元宝": 700},
            "effects": {"attack": 9},
            "unlocked": False
        },
        "demon": {
            "name": "恶魔武器",
            "description": "恶魔之力注入的武器，凶焰滔天",
            "cost": {"金元宝": 900},
            "effects": {"attack": 12},
            "unlocked": False
        }
    },
    "mount_skins": {
        "normal": {
            "name": "默认坐骑",
            "description": "坐骑默认外观",
            "cost": {},
            "effects": {},
            "unlocked": True
        },
        "unicorn": {
            "name": "独角兽",
            "description": "传说中的神兽，优雅高贵",
            "cost": {"金元宝": 600},
            "effects": {"speed": 2},
            "unlocked": False
        },
        "phoenix": {
            "name": "凤凰",
            "description": "凤凰坐骑，翱翔天际",
            "cost": {"金元宝": 900},
            "effects": {"speed": 3},
            "unlocked": False
        },
        "dragon": {
            "name": "神龙",
            "description": "神龙坐骑，威力无边",
            "cost": {"金元宝": 1200},
            "effects": {"speed": 4},
            "unlocked": False
        }
    }
}

# 科技树配置 (树状结构)
TECH_TREE = {
    "resource": {
        "id": "resource",
        "name": "资源科技",
        "description": "提高资源采集效率",
        "parent": None,
        "children": ["resource_basic", "resource_efficiency"],
        "level": 0,
        "cost": {},
        "effects": {}
    },
    "resource_basic": {
        "id": "resource_basic",
        "name": "基础采集",
        "description": "提高所有资源采集速度10%",
        "parent": "resource",
        "children": ["resource_advanced"],
        "level": 1,
        "cost": {"金元宝": 100},
        "effects": {"resource_gather_speed": 0.1}
    },
    "resource_advanced": {
        "id": "resource_advanced",
        "name": "高级采集",
        "description": "提高所有资源采集速度20%",
        "parent": "resource_basic",
        "children": ["resource_professional"],
        "level": 2,
        "cost": {"金元宝": 200},
        "effects": {"resource_gather_speed": 0.2}
    },
    "resource_professional": {
        "id": "resource_professional",
        "name": "专业采集",
        "description": "提高所有资源采集速度30%",
        "parent": "resource_advanced",
        "children": ["resource_master"],
        "level": 3,
        "cost": {"金元宝": 300},
        "effects": {"resource_gather_speed": 0.3}
    },
    "resource_master": {
        "id": "resource_master",
        "name": "大师采集",
        "description": "提高所有资源采集速度40%",
        "parent": "resource_professional",
        "children": ["resource_legend"],
        "level": 4,
        "cost": {"金元宝": 400},
        "effects": {"resource_gather_speed": 0.4}
    },
    "resource_legend": {
        "id": "resource_legend",
        "name": "传奇采集",
        "description": "提高所有资源采集速度50%",
        "parent": "resource_master",
        "children": [],
        "level": 5,
        "cost": {"金元宝": 500},
        "effects": {"resource_gather_speed": 0.5}
    },
    "resource_efficiency": {
        "id": "resource_efficiency",
        "name": "资源效率",
        "description": "提高资源存储容量20%",
        "parent": "resource",
        "children": ["resource_storage"],
        "level": 1,
        "cost": {"金元宝": 150},
        "effects": {"resource_capacity": 0.2}
    },
    "resource_storage": {
        "id": "resource_storage",
        "name": "高级存储",
        "description": "提高资源存储容量40%",
        "parent": "resource_efficiency",
        "children": ["resource_logistics"],
        "level": 2,
        "cost": {"金元宝": 300},
        "effects": {"resource_capacity": 0.4}
    },
    "resource_logistics": {
        "id": "resource_logistics",
        "name": "物流管理",
        "description": "提高资源运输效率30%",
        "parent": "resource_storage",
        "children": [],
        "level": 3,
        "cost": {"金元宝": 450},
        "effects": {"resource_transport": 0.3}
    },
    "occupation": {
        "id": "occupation",
        "name": "占领科技",
        "description": "提高领地占领速度",
        "parent": None,
        "children": ["occupation_fast", "occupation_strategy"],
        "level": 0,
        "cost": {},
        "effects": {}
    },
    "occupation_fast": {
        "id": "occupation_fast",
        "name": "快速占领",
        "description": "提高占领速度20%",
        "parent": "occupation",
        "children": ["occupation_efficient"],
        "level": 1,
        "cost": {"金元宝": 150},
        "effects": {"occupation_speed": 0.2}
    },
    "occupation_efficient": {
        "id": "occupation_efficient",
        "name": "高效占领",
        "description": "提高占领速度40%",
        "parent": "occupation_fast",
        "children": ["occupation_lightning"],
        "level": 2,
        "cost": {"金元宝": 300},
        "effects": {"occupation_speed": 0.4}
    },
    "occupation_lightning": {
        "id": "occupation_lightning",
        "name": "闪电占领",
        "description": "提高占领速度60%",
        "parent": "occupation_efficient",
        "children": ["occupation_mastery"],
        "level": 3,
        "cost": {"金元宝": 450},
        "effects": {"occupation_speed": 0.6}
    },
    "occupation_mastery": {
        "id": "occupation_mastery",
        "name": "占领精通",
        "description": "提高占领速度80%",
        "parent": "occupation_lightning",
        "children": [],
        "level": 4,
        "cost": {"金元宝": 600},
        "effects": {"occupation_speed": 0.8}
    },
    "occupation_strategy": {
        "id": "occupation_strategy",
        "name": "占领策略",
        "description": "减少占领消耗15%",
        "parent": "occupation",
        "children": ["occupation_tactics"],
        "level": 1,
        "cost": {"金元宝": 200},
        "effects": {"occupation_cost": 0.15}
    },
    "occupation_tactics": {
        "id": "occupation_tactics",
        "name": "占领战术",
        "description": "减少占领消耗30%",
        "parent": "occupation_strategy",
        "children": [],
        "level": 2,
        "cost": {"金元宝": 400},
        "effects": {"occupation_cost": 0.3}
    },
    "combat": {
        "id": "combat",
        "name": "战斗科技",
        "description": "提高战斗能力",
        "parent": None,
        "children": ["combat_attack", "combat_speed", "combat_critical"],
        "level": 0,
        "cost": {},
        "effects": {}
    },
    "combat_attack": {
        "id": "combat_attack",
        "name": "攻击力提升",
        "description": "提高所有武将攻击力10%",
        "parent": "combat",
        "children": ["combat_advanced_attack"],
        "level": 1,
        "cost": {"金元宝": 200},
        "effects": {"combat_attack": 0.1}
    },
    "combat_advanced_attack": {
        "id": "combat_advanced_attack",
        "name": "高级攻击力",
        "description": "提高所有武将攻击力20%",
        "parent": "combat_attack",
        "children": ["combat_master_attack"],
        "level": 2,
        "cost": {"金元宝": 400},
        "effects": {"combat_attack": 0.2}
    },
    "combat_master_attack": {
        "id": "combat_master_attack",
        "name": "大师攻击力",
        "description": "提高所有武将攻击力30%",
        "parent": "combat_advanced_attack",
        "children": [],
        "level": 3,
        "cost": {"金元宝": 600},
        "effects": {"combat_attack": 0.3}
    },
    "combat_speed": {
        "id": "combat_speed",
        "name": "攻击速度",
        "description": "提高攻击速度15%",
        "parent": "combat",
        "children": ["combat_advanced_speed"],
        "level": 1,
        "cost": {"金元宝": 250},
        "effects": {"combat_speed": 0.15}
    },
    "combat_advanced_speed": {
        "id": "combat_advanced_speed",
        "name": "高级攻击速度",
        "description": "提高攻击速度30%",
        "parent": "combat_speed",
        "children": [],
        "level": 2,
        "cost": {"金元宝": 500},
        "effects": {"combat_speed": 0.3}
    },
    "combat_critical": {
        "id": "combat_critical",
        "name": "暴击率",
        "description": "提高暴击率5%",
        "parent": "combat",
        "children": ["combat_advanced_critical"],
        "level": 1,
        "cost": {"金元宝": 300},
        "effects": {"combat_critical": 0.05}
    },
    "combat_advanced_critical": {
        "id": "combat_advanced_critical",
        "name": "高级暴击率",
        "description": "提高暴击率10%",
        "parent": "combat_critical",
        "children": ["combat_master_critical"],
        "level": 2,
        "cost": {"金元宝": 600},
        "effects": {"combat_critical": 0.1}
    },
    "combat_master_critical": {
        "id": "combat_master_critical",
        "name": "大师暴击率",
        "description": "提高暴击率15%",
        "parent": "combat_advanced_critical",
        "children": [],
        "level": 3,
        "cost": {"金元宝": 900},
        "effects": {"combat_critical": 0.15}
    },
    "defense": {
        "id": "defense",
        "name": "防御科技",
        "description": "提高防御能力",
        "parent": None,
        "children": ["defense_basic", "defense_resistance", "defense_regen"],
        "level": 0,
        "cost": {},
        "effects": {}
    },
    "defense_basic": {
        "id": "defense_basic",
        "name": "基础防御",
        "description": "提高所有武将防御力10%",
        "parent": "defense",
        "children": ["defense_advanced"],
        "level": 1,
        "cost": {"金元宝": 150},
        "effects": {"combat_defense": 0.1}
    },
    "defense_advanced": {
        "id": "defense_advanced",
        "name": "高级防御",
        "description": "提高所有武将防御力20%",
        "parent": "defense_basic",
        "children": ["defense_master"],
        "level": 2,
        "cost": {"金元宝": 300},
        "effects": {"combat_defense": 0.2}
    },
    "defense_master": {
        "id": "defense_master",
        "name": "大师防御",
        "description": "提高所有武将防御力30%",
        "parent": "defense_advanced",
        "children": [],
        "level": 3,
        "cost": {"金元宝": 450},
        "effects": {"combat_defense": 0.3}
    },
    "defense_resistance": {
        "id": "defense_resistance",
        "name": "元素抗性",
        "description": "提高元素抗性10%",
        "parent": "defense",
        "children": ["defense_advanced_resistance"],
        "level": 1,
        "cost": {"金元宝": 200},
        "effects": {"element_resistance": 0.1}
    },
    "defense_advanced_resistance": {
        "id": "defense_advanced_resistance",
        "name": "高级元素抗性",
        "description": "提高元素抗性20%",
        "parent": "defense_resistance",
        "children": [],
        "level": 2,
        "cost": {"金元宝": 400},
        "effects": {"element_resistance": 0.2}
    },
    "defense_regen": {
        "id": "defense_regen",
        "name": "生命恢复",
        "description": "提高生命恢复速度15%",
        "parent": "defense",
        "children": ["defense_advanced_regen"],
        "level": 1,
        "cost": {"金元宝": 250},
        "effects": {"health_regen": 0.15}
    },
    "defense_advanced_regen": {
        "id": "defense_advanced_regen",
        "name": "高级生命恢复",
        "description": "提高生命恢复速度30%",
        "parent": "defense_regen",
        "children": [],
        "level": 2,
        "cost": {"金元宝": 500},
        "effects": {"health_regen": 0.3}
    },
    "special": {
        "id": "special",
        "name": "特殊科技",
        "description": "特殊能力提升",
        "parent": None,
        "children": ["special_hero", "special_equip", "special_research"],
        "level": 0,
        "cost": {},
        "effects": {}
    },
    "special_hero": {
        "id": "special_hero",
        "name": "武将强化",
        "description": "提高武将基础属性5%",
        "parent": "special",
        "children": ["special_hero_advanced"],
        "level": 1,
        "cost": {"金元宝": 300},
        "effects": {"hero_bonus": 0.05}
    },
    "special_hero_advanced": {
        "id": "special_hero_advanced",
        "name": "高级武将强化",
        "description": "提高武将基础属性10%",
        "parent": "special_hero",
        "children": ["special_hero_master"],
        "level": 2,
        "cost": {"金元宝": 600},
        "effects": {"hero_bonus": 0.1}
    },
    "special_hero_master": {
        "id": "special_hero_master",
        "name": "大师武将强化",
        "description": "提高武将基础属性15%",
        "parent": "special_hero_advanced",
        "children": [],
        "level": 3,
        "cost": {"金元宝": 900},
        "effects": {"hero_bonus": 0.15}
    },
    "special_equip": {
        "id": "special_equip",
        "name": "装备强化",
        "description": "提高装备效果10%",
        "parent": "special",
        "children": ["special_equip_advanced"],
        "level": 1,
        "cost": {"金元宝": 350},
        "effects": {"equip_bonus": 0.1}
    },
    "special_equip_advanced": {
        "id": "special_equip_advanced",
        "name": "高级装备强化",
        "description": "提高装备效果20%",
        "parent": "special_equip",
        "children": [],
        "level": 2,
        "cost": {"金元宝": 700},
        "effects": {"equip_bonus": 0.2}
    },
    "special_research": {
        "id": "special_research",
        "name": "研究加速",
        "description": "提高科技研究速度20%",
        "parent": "special",
        "children": ["special_research_advanced"],
        "level": 1,
        "cost": {"金元宝": 400},
        "effects": {"research_speed": 0.2}
    },
    "special_research_advanced": {
        "id": "special_research_advanced",
        "name": "高级研究加速",
        "description": "提高科技研究速度40%",
        "parent": "special_research",
        "children": [],
        "level": 2,
        "cost": {"金元宝": 800},
        "effects": {"research_speed": 0.4}
    }
}

# 建筑系统配置
BUILDINGS = {
    "resource_center": {
        "name": "资源中心",
        "description": "提高所有资源产出速度",
        "levels": [
            {"cost": {"金元宝": 100}, "effect": {"resource_bonus": 0.1}},
            {"cost": {"金元宝": 200}, "effect": {"resource_bonus": 0.2}},
            {"cost": {"金元宝": 300}, "effect": {"resource_bonus": 0.3}},
            {"cost": {"金元宝": 500}, "effect": {"resource_bonus": 0.4}},
            {"cost": {"金元宝": 800}, "effect": {"resource_bonus": 0.5}}
        ]
    },
    "training_ground": {
        "name": "训练场",
        "description": "提高武将攻击力",
        "levels": [
            {"cost": {"金元宝": 150}, "effect": {"hero_attack": 0.1}},
            {"cost": {"金元宝": 300}, "effect": {"hero_attack": 0.2}},
            {"cost": {"金元宝": 450}, "effect": {"hero_attack": 0.3}},
            {"cost": {"金元宝": 750}, "effect": {"hero_attack": 0.4}},
            {"cost": {"金元宝": 1200}, "effect": {"hero_attack": 0.5}}
        ]
    },
    "research_lab": {
        "name": "研究实验室",
        "description": "加速科技研究速度",
        "levels": [
            {"cost": {"金元宝": 200}, "effect": {"research_speed": 0.1}},
            {"cost": {"金元宝": 400}, "effect": {"research_speed": 0.2}},
            {"cost": {"金元宝": 600}, "effect": {"research_speed": 0.3}},
            {"cost": {"金元宝": 1000}, "effect": {"research_speed": 0.4}},
            {"cost": {"金元宝": 1600}, "effect": {"research_speed": 0.5}}
        ]
    },
    "treasure_house": {
        "name": "宝库",
        "description": "增加金元宝产出",
        "levels": [
            {"cost": {"金元宝": 250}, "effect": {"gold_bonus": 0.15}},
            {"cost": {"金元宝": 500}, "effect": {"gold_bonus": 0.3}},
            {"cost": {"金元宝": 750}, "effect": {"gold_bonus": 0.45}},
            {"cost": {"金元宝": 1250}, "effect": {"gold_bonus": 0.6}},
            {"cost": {"金元宝": 2000}, "effect": {"gold_bonus": 0.75}}
        ]
    },
    "barracks": {
        "name": "兵营",
        "description": "提高武将防御力",
        "levels": [
            {"cost": {"金元宝": 180}, "effect": {"hero_defense": 0.1}},
            {"cost": {"金元宝": 360}, "effect": {"hero_defense": 0.2}},
            {"cost": {"金元宝": 540}, "effect": {"hero_defense": 0.3}},
            {"cost": {"金元宝": 900}, "effect": {"hero_defense": 0.4}},
            {"cost": {"金元宝": 1440}, "effect": {"hero_defense": 0.5}}
        ]
    }
}

# 天赋系统配置
TALENT_TREE = {
    "resource": {
        "name": "资源天赋",
        "description": "增加资源产出和存储",
        "talents": [
            {"id": "resource_gatherer", "name": "资源采集者", "description": "提高资源采集速度10%", "cost": 1, "effect": {"resource_gather_speed": 0.1}},
            {"id": "resource_steward", "name": "资源管理员", "description": "提高资源存储容量20%", "cost": 2, "effect": {"resource_capacity": 0.2}},
            {"id": "resource_master", "name": "资源大师", "description": "所有资源产出增加15%", "cost": 3, "effect": {"resource_bonus": 0.15}},
            {"id": "resource_tycoon", "name": "资源大亨", "description": "金元宝产出增加20%", "cost": 4, "effect": {"gold_bonus": 0.2}}
        ]
    },
    "combat": {
        "name": "战斗天赋",
        "description": "增强武将战斗能力",
        "talents": [
            {"id": "combat_attack", "name": "攻击力提升", "description": "提高武将攻击力10%", "cost": 1, "effect": {"hero_attack": 0.1}},
            {"id": "combat_defense", "name": "防御力提升", "description": "提高武将防御力10%", "cost": 1, "effect": {"hero_defense": 0.1}},
            {"id": "combat_critical", "name": "暴击率提升", "description": "提高暴击率5%", "cost": 2, "effect": {"combat_critical": 0.05}},
            {"id": "combat_master", "name": "战斗大师", "description": "所有武将属性提升15%", "cost": 4, "effect": {"hero_bonus": 0.15}}
        ]
    },
    "tech": {
        "name": "科技天赋",
        "description": "加速科技研究",
        "talents": [
            {"id": "tech_researcher", "name": "研究员", "description": "提高科技研究速度10%", "cost": 1, "effect": {"research_speed": 0.1}},
            {"id": "tech_scientist", "name": "科学家", "description": "提高科技研究速度20%", "cost": 2, "effect": {"research_speed": 0.2}},
            {"id": "tech_inventor", "name": "发明家", "description": "科技研究成本降低15%", "cost": 3, "effect": {"tech_cost_reduction": 0.15}},
            {"id": "tech_master", "name": "科技大师", "description": "科技研究速度提升30%", "cost": 4, "effect": {"research_speed": 0.3}},
        ]
    },
    "special": {
        "name": "特殊天赋",
        "description": "提供独特能力",
        "talents": [
            {"id": "special_luck", "name": "幸运星", "description": "获得稀有物品的概率提高10%", "cost": 2, "effect": {"luck_bonus": 0.1}},
            {"id": "special_speed", "name": "速度之星", "description": "攻击速度提升15%", "cost": 2, "effect": {"attack_speed": 0.15}},
            {"id": "special_endurance", "name": "耐力", "description": "武将生命值提高20%", "cost": 3, "effect": {"hero_health": 0.2}},
            {"id": "special_legend", "name": "传奇", "description": "所有属性提升20%", "cost": 5, "effect": {"all_bonus": 0.2}},
        ]
    }
}

# 存档模板
default_save = {
    "username": "",
    "password": "",
    "resources": {r:0 for r in RESOURCES},
    "normal_dungeon": 1,
    "infinite_dungeon": 1,
    "hero_fragments": {},
    "heroes": {},
    "hero_guns": {},
    "equips": {"weapon":0, "armor":0, "horse":0, "book":0},
    "activities": {
        "春节活动": {
            "start": "2026-02-01",
            "end": "2026-02-20",
            "reward": "金元宝*200, 食物*500, 限定武将皮肤*1"
        },
        "情人节活动": {
            "start": "2026-02-10",
            "end": "2026-02-20",
            "reward": "金元宝*150, 玫瑰*99, 情侣时装*1"
        },
        "夏季庆典": {
            "start": "2026-07-01",
            "end": "2026-07-31",
            "reward": "金元宝*250, 西瓜*100, 夏季限定坐骑*1"
        },
        "周年庆典": {
            "start": "2026-10-01",
            "end": "2026-10-15",
            "reward": "金元宝*500, 周年限定武将*1, 传说装备*1"
        },
        "万圣节活动": {
            "start": "2026-10-25",
            "end": "2026-11-05",
            "reward": "金元宝*200, 南瓜灯*50, 万圣节皮肤*1"
        }
    },
    "achievements": {
        "completed": [],
        "progress": {}
    },
    "tech_tree": {
        "unlocked": ["resource", "occupation", "combat", "defense", "special"]
    },
    "buildings": {},
    "talents": {
        "points": 0,
        "unlocked": []
    },
    "settings": SETTINGS,
    "last_login": 0,
    "last_auto_save": 0,
    "resource_bonus": 1.0,
    "passive_income": {
        "水": 0.1,
        "煤炭": 0.05,
        "木头": 0.08,
        "食物": 0.07,
        "金元宝": 0.02
    },
    "unlocked_income_slots": 1,
    "total_play_time": 0,
    "hero_levels": {},
    "equip_levels": {"weapon":1, "armor":1, "horse":1, "book":1},
    "unlocked_features": [],
    "prestige_level": 0,
    "tasks": {
        "daily": {
            "last_reset": 0,
            "progress": {},
            "completed": []
        },
        "weekly": {
            "last_reset": 0,
            "progress": {},
            "completed": []
        }
    },
    "rankings": {
        "pvp_wins": [],
        "mini_game_scores": {},
        "total_play_time": [],
        "achievements_unlocked": []
    },
    "checkin": {
        "last_checkin": "",
        "consecutive_days": 0,
        "total_checkins": 0,
        "rewards_claimed": []
    },
    "time_tasks": {
        "active": [],
        "completed": []
    },
    "weather": {
        "current_weather": None,
        "weather_start_time": 0,
        "weather_duration": 0,
        "current_holiday": None,
        "current_season": None,
        "current_time_of_day": None,
        "game_time": 0,
        "time_speed": 1.0
    },
    "event_system": {
        "event_history": [],
        "last_event_time": 0,
        "event_cooldown": 30
    },
    "story_progress": {
        "current_chapter": 0,
        "completed_events": [],
        "unlocked_endings": []
    },
    "battle_stats": {
        "total_battles": 0,
        "victories": 0,
        "defeats": 0,
        "max_combo": 0,
        "ultimate_used_count": 0
    },
    "daily_reward": {
        "last_checkin_date": "",
        "consecutive_days": 0,
        "monthly_checkins": 0,
        "claimed_rewards": [],
        "current_month": 0
    },
    "achievements": {
        "unlocked": [],
        "progress": {},
        "claimed_rewards": []
    },
    "task_chains": {
        "active_chains": [],
        "completed_chains": [],
        "current_tasks": {},
        "task_progress": {},
        "daily_tasks": [],
        "weekly_tasks": [],
        "claimed_rewards": [],
        "last_daily_refresh": "",
        "last_weekly_refresh": ""
    },
    "hero_collection": {
        "collected": [],
        "collection_progress": 0,
        "unlocked_bonuses": [],
        "claimed_rewards": []
    },
    "territory": {
        "owned_territories": [],
        "territory_levels": {},
        "resource_production": {},
        "garrisons": {},
        "last_collection_time": 0,
        "total_power": 0
    },
    "season": {
        "current_season": 1,
        "season_start_time": 0,
        "season_duration": 7 * 24 * 3600,
        "season_points": 0,
        "season_rank": 0,
        "season_rewards_claimed": [],
        "historical_best_rank": 0
    },
    "guild": {
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
        "last_daily_claim": ""
    },
    "hero_advancement": {
        "advanced_heroes": {},
        "awakened_heroes": [],
        "skill_enhancements": {}
    },
    "dungeon": {
        "unlocked_dungeons": [],
        "completed_floors": {},
        "best_scores": {},
        "daily_challenges": [],
        "weekly_challenges": [],
        "claimed_rewards": [],
        "task_progress": {},
        "last_daily_reset": "",
        "last_weekly_reset": ""
    },
    "notifications": {
        "unread": [],
        "read": [],
        "settings": {
            "daily_reminder": True,
            "activity_alert": True,
            "reward_notification": True
        }
    },
    "mail": {
        "inbox": [],
        "sent": [],
        "archived": []
    },
    "checkin_calendar": {
        "current_month": "",
        "checkins": {},
        "monthly_rewards_claimed": [],
        "streak_rewards_claimed": []
    },
    "leaderboard": {
        "player_rank": 0,
        "categories": {
            "power": [],
            "wealth": [],
            "achievements": [],
            "pvp": []
        }
    },
    "mc_world": {
        "placed_blocks": [],
        "hotbar": [None] * 9,
        "hotbar_selected": 0,
        "player_pos": [0, 0, 0],
        "camera_yaw": 0,
        "camera_pitch": -20,
        "camera_mode": "first",
        "inventory": [],
        "world_seed": 0
    }
}

data = default_save.copy()

def calculate_passive_income():
    """计算并添加被动收入"""
    import time
    current_time = int(time.time())
    last_login = data.get('last_login', 0)
    if last_login > 0:
        time_diff = current_time - last_login
        if time_diff > 60:  # 至少1分钟
            # 计算被动收入
            for resource, rate in data.get('passive_income', {}).items():
                income = int(time_diff * rate * data.get('resource_bonus', 1.0))
                if income > 0:
                    data['resources'][resource] = data['resources'].get(resource, 0) + income
        
    # 更新最后登录时间
    data['last_login'] = current_time
    save()

def load():
    """加载存档"""
    global data
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 检查并添加缺失的键
            if 'achievements' not in data:
                data['achievements'] = {
                    "completed": [],
                    "progress": {}
                }
            
            # 确保achievements中的子键存在
            if 'completed' not in data['achievements']:
                data['achievements']['completed'] = []
            if 'progress' not in data['achievements']:
                data['achievements']['progress'] = {}
            
            # 检查并添加被动收入相关键
            if 'last_login' not in data:
                data['last_login'] = 0
            if 'resource_bonus' not in data:
                data['resource_bonus'] = 1.0
            if 'passive_income' not in data:
                data['passive_income'] = default_save['passive_income']
            
            # 检查并添加天气系统相关键
            if 'weather' not in data:
                data['weather'] = default_save['weather']
            # 检查天气系统中的新字段
            weather_keys = ['current_season', 'current_time_of_day', 'game_time', 'time_speed']
            for key in weather_keys:
                if key not in data['weather']:
                    data['weather'][key] = default_save['weather'][key]
            if 'unlocked_income_slots' not in data:
                data['unlocked_income_slots'] = 1
            
            # 检查并添加事件系统相关键
            if 'event_system' not in data:
                data['event_system'] = default_save['event_system']
            if 'story_progress' not in data:
                data['story_progress'] = default_save['story_progress']
            if 'battle_stats' not in data:
                data['battle_stats'] = default_save['battle_stats']
            
            # 检查并添加科技树相关键
            if 'tech_tree' not in data:
                data['tech_tree'] = default_save['tech_tree']
            if 'total_play_time' not in data:
                data['total_play_time'] = 0
            
            # 检查并添加成长系统相关键
            if 'hero_levels' not in data:
                data['hero_levels'] = {}
            if 'hero_guns' not in data:
                data['hero_guns'] = {}
            if 'equip_levels' not in data:
                data['equip_levels'] = default_save['equip_levels']
            if 'unlocked_features' not in data:
                data['unlocked_features'] = []
            if 'prestige_level' not in data:
                data['prestige_level'] = 0
            
            # 检查并添加任务系统相关键
            if 'tasks' not in data:
                data['tasks'] = default_save['tasks']
            else:
                if 'daily' not in data['tasks']:
                    data['tasks']['daily'] = default_save['tasks']['daily']
                if 'weekly' not in data['tasks']:
                    data['tasks']['weekly'] = default_save['tasks']['weekly']
            
            # 检查并添加排行榜系统相关键
            if 'rankings' not in data:
                data['rankings'] = default_save['rankings']
            
            # 检查并添加每日签到系统相关键
            if 'checkin' not in data:
                data['checkin'] = default_save['checkin']
            
            # 检查并添加缺失的资源
            for resource in RESOURCES:
                if resource not in data['resources']:
                    data['resources'][resource] = 0
            
            # 检查并添加自动保存相关键
            if 'last_auto_save' not in data:
                data['last_auto_save'] = 0
            
            # 确保设置存在
            if 'settings' not in data:
                data['settings'] = SETTINGS.copy()
            
            # 检查并添加每日签到系统相关键
            if 'daily_reward' not in data:
                data['daily_reward'] = default_save['daily_reward']
            
            # 检查并添加成就系统相关键（新格式）
            if 'achievements' not in data:
                data['achievements'] = default_save['achievements']
            else:
                if 'unlocked' not in data['achievements']:
                    data['achievements']['unlocked'] = []
                if 'progress' not in data['achievements']:
                    data['achievements']['progress'] = {}
                if 'claimed_rewards' not in data['achievements']:
                    data['achievements']['claimed_rewards'] = []
            
            # 检查并添加任务链系统相关键
            if 'task_chains' not in data:
                data['task_chains'] = default_save['task_chains']
            
            # 检查并添加武将图鉴系统相关键
            if 'hero_collection' not in data:
                data['hero_collection'] = default_save['hero_collection']
            
            # 检查并添加领土系统相关键
            if 'territory' not in data:
                data['territory'] = default_save['territory']
            
            # 检查并添加赛季系统相关键
            if 'season' not in data:
                data['season'] = default_save['season']
                data['season']['season_start_time'] = int(time.time())
            
            # 检查并添加公会系统相关键
            if 'guild' not in data:
                data['guild'] = default_save['guild']
            
            # 检查并添加武将进阶系统相关键
            if 'hero_advancement' not in data:
                data['hero_advancement'] = default_save['hero_advancement']
            
            # 检查并添加副本系统相关键
            if 'dungeon' not in data:
                data['dungeon'] = default_save['dungeon']
            
            if 'mc_world' not in data:
                data['mc_world'] = default_save['mc_world']
            else:
                mc_keys = ['placed_blocks', 'hotbar', 'hotbar_selected', 'player_pos', 'camera_yaw', 'camera_pitch', 'camera_mode', 'inventory', 'world_seed']
                for key in mc_keys:
                    if key not in data['mc_world']:
                        data['mc_world'][key] = default_save['mc_world'][key]
            
            calculate_passive_income()

        except Exception as e:
            import logging
            logging.error(f"加载存档失败: {e}")
            data = default_save.copy()
            calculate_passive_income()

def save():
    """保存存档"""
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        hide_file(SAVE_PATH)
    except Exception as e:
        import logging
        logging.error(f"保存存档失败: {e}")

def auto_save():
    """自动保存功能"""
    # 每5分钟自动保存一次
    import time
    current_time = int(time.time())
    if 'last_auto_save' not in data:
        data['last_auto_save'] = 0
    
    if current_time - data['last_auto_save'] > 300:  # 5分钟
        save()
        data['last_auto_save'] = current_time
        return True
    return False

# 初始化加载存档
load()
