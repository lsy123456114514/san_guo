"""3D 世界地图（MC 模式）- 方块放置、摄像机、热键栏"""

import pygame
import math
import random
import json
import os
import time
from ASSET.game_data import data, save, get_system_font_name, create_font, load_sound, logger, draw_gradient_bg, cull_dead, get_font, get_writable_base_dir
from ASSET import safe_exit

MC_WORLD_KEY = "mc_world"

# 尝试导入OpenGL
try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    opengl_available = True
except ImportError:
    opengl_available = False

# 尝试导入C++渲染器
try:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from renderer_bindings import renderer, TreeData, LocationData, NPCData, EnemyData, GeneralData, PetData, PlayerData, FollowerData, ProjectileData, PickupData, TechBlockData, ParticleData
    cpp_renderer_available = renderer.is_available
except Exception as e:
    logger.info(f"无法加载C++渲染器: {e}")
    cpp_renderer_available = False

# 颜色定义
COLORS = {
    "bg_dark": (20, 20, 30),
    "bg_light": (30, 30, 50),
    "text_white": (255, 255, 255),
    "accent_gold": (255, 215, 0),
    "accent_green": (50, 205, 50),
    "accent_red": (255, 69, 0),
    "accent_blue": (64, 128, 255),
    "accent_blue_dark": (30, 60, 120)
}

# 地图配置
MAP_SIZE = (2000, 2000)
MAX_LOCATIONS = 50
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

class GameMap3D:
    """3D游戏地图系统"""
    def __init__(self):
        self.screen = None
        self.clock = None
        self.font_main = None
        self.font_small = None
        self.locations = []
        self.player_pos = [0, 0, 0]
        self.camera = {
            "x": 0,
            "y": 10,
            "z": 20,
            "pitch": -20,  # 俯仰角
            "yaw": 0,      # 偏航角
            "speed": 0.5
        }
        self.mouse_sensitivity = 0.05
        self.is_mouse_locked = False
        self.followers = []
        self.follow_target = None
        self.message = None
        self.message_timer = 0
        
        # 物理参数
        self.velocity = [0, 0, 0]  # x, y, z 方向速度
        self.gravity = -0.2  # 重力加速度
        
        # 相机模式
        self.camera["mode"] = "first"  # first 或 third
        
        # 暂停菜单
        self.is_paused = False
        self.pause_menu_selected = 0
        self.pause_menu_options = ["继续游戏", "设置", "保存并退出", "返回主菜单"]
        
        # 快捷栏（类似MC）
        self.hotbar = [None] * 9
        self.hotbar_selected = 0
        
        # 十字准星
        self.show_crosshair = True
        
        # 方块系统
        self.placed_blocks = []
        self.selected_block_type = 0
        self.block_types = ["泥土", "石头", "木头", "草地", "沙子", "水", "玻璃", "砖块"]
        
        # 背包系统（类似旅行者背包）
        self.show_inventory = False
        self.inventory_slots = 27  # 3行9列
        self.inventory = [None] * self.inventory_slots
        self.max_stack_size = 64
        
        # 物品类型定义（MC 1.12.2风格）
        self.item_types = {
            "方块类": ["泥土", "石头", "圆石", "木头", "草地", "沙子", "砂砾", "水", "岩浆", 
                      "玻璃", "砖块", "砖块方块", "木板", "橡木台阶", "石台阶", "砖台阶",
                      "楼梯", "石楼梯", "砖楼梯", "栅栏", "栅栏门", "梯子", "门", "压力板",
                      "石压力板", "按钮", "橡木按钮", "玻璃面板", "混凝土粉末", "陶瓦", "带釉陶瓦"],
            "资源类": ["煤炭", "铁矿石", "金矿石", "钻石矿石", "红石矿石", "绿宝石矿石",
                      "下界石英", "黑曜石", "末地石", "灵魂沙", "沙砾", "粘土", "甘蔗", 
                      "小麦", "胡萝卜", "土豆", "甜菜根", "南瓜", "西瓜", "可可豆", "仙人掌",
                      "羊毛", "线", "羽毛", "鸡蛋", "骨头", "皮革", "兔子皮", "粘液球",
                      "烈焰棒", "烈焰粉", "末影珍珠", "恶魂之泪", "龙息", "下界之星", "青金石"],
            "武器类": ["木剑", "石剑", "铁剑", "金剑", "钻石剑", "弓", "弩", "盾牌", "三叉戟"],
            "工具类": ["木头镐子", "石头镐子", "铁镐", "金镐", "钻石镐",
                      "木头斧头", "石头斧头", "铁斧", "金斧", "钻石斧",
                      "木头铲子", "石头铲子", "铁铲", "金铲", "钻石铲",
                      "木头锄", "石头锄", "铁锄", "金锄", "钻石锄",
                      "钓鱼竿", "剪刀", "打火石"],
            "食物类": ["面包", "蛋糕", "曲奇", "南瓜派", "甜菜汤", "蘑菇煲", "炖兔肉",
                      "胡萝卜蛋糕", "糖", "胡萝卜", "土豆", "烤土豆",
                      "牛肉", "猪肉", "羊肉", "鸡肉", "兔肉",
                      "熟牛肉", "熟猪肉", "熟羊肉", "熟鸡肉", "熟兔肉",
                      "苹果", "西瓜", "金苹果", "附魔金苹果"],
            "染料类": ["骨粉", "墨囊", "红色染料", "橙色染料", "黄色染料", "绿色染料",
                      "青色染料", "蓝色染料", "紫色染料", "品红色染料", "粉色染料",
                      "棕色染料", "灰色染料", "淡灰色染料", "黄绿色染料", "淡蓝色染料"],
            "羊毛类": ["白色羊毛", "橙色羊毛", "品红色羊毛", "淡蓝色羊毛", "黄色羊毛",
                      "黄绿色羊毛", "粉色羊毛", "灰色羊毛", "淡灰色羊毛", "青色羊毛",
                      "紫色羊毛", "蓝色羊毛", "棕色羊毛", "绿色羊毛", "红色羊毛", "黑色羊毛"],
            "机械类": ["活塞", "粘性活塞", "红石中继器", "红石比较器", "红石火把", "红石灯",
                      "发射器", "投掷器", "漏斗", "箱子", "陷阱箱", "木桶", "酿造台",
                      "炼药锅", "铁砧", "砂轮", "织布机", "制图台", "烟熏炉", "高炉",
                      "营火", "灵魂营火", "矿车", "储物矿车", "漏斗矿车", "动力矿车",
                      "船", "深色橡木船", "云杉船", "白桦船", "丛林木船", "金合欢船"],
            "装饰类": ["画", "物品展示框", "旗帜", "花盆", "末地烛", "灯笼", "灵魂灯笼",
                      "钟", "测重压力板", "绊线钩"],
            "特殊类": ["信标", "龙蛋", "结构方块", "命令方块", "调试棒", "知识之书",
                      "附魔书", "书与笔", "经验瓶"],
            "药水类": ["水瓶", "粗制药水", "治疗药水", "抗火药水", "迅捷药水", "力量药水",
                      "再生药水", "隐身药水", "夜视药水", "水下呼吸药水"],
            "武将卡": ["刘备卡", "关羽卡", "张飞卡", "赵云卡", "诸葛亮卡", "曹操卡",
                      "马超卡", "黄忠卡", "魏延卡", "庞统卡", "孙权卡", "周瑜卡"],
            "弹药类": ["普通子弹", "高级子弹", "稀有子弹", "箭矢"]
        }
        
        # 背包界面状态
        self.inventory_selected_slot = -1
        self.dragging_item = None
        self.drag_source = None
        self.inventory_category = "全部"
        
        # 合成系统（完整MC 1.12.2风格配方）
        self.crafting_recipes = {
            # 工具
            "木头镐子": {"木头": 3, "木棍": 2},
            "石头镐子": {"圆石": 3, "木棍": 2},
            "铁镐": {"铁锭": 3, "木棍": 2},
            "金镐": {"金锭": 3, "木棍": 2},
            "钻石镐": {"钻石": 3, "木棍": 2},
            "木头斧头": {"木头": 3, "木棍": 2},
            "石头斧头": {"圆石": 3, "木棍": 2},
            "铁斧": {"铁锭": 3, "木棍": 2},
            "金斧": {"金锭": 3, "木棍": 2},
            "钻石斧": {"钻石": 3, "木棍": 2},
            "木头铲子": {"木头": 1, "木棍": 2},
            "石头铲子": {"圆石": 1, "木棍": 2},
            "铁铲": {"铁锭": 1, "木棍": 2},
            "金铲": {"金锭": 1, "木棍": 2},
            "钻石铲": {"钻石": 1, "木棍": 2},
            "木头锄": {"木头": 2, "木棍": 2},
            "石头锄": {"圆石": 2, "木棍": 2},
            "铁锄": {"铁锭": 2, "木棍": 2},
            "金锄": {"金锭": 2, "木棍": 2},
            "钻石锄": {"钻石": 2, "木棍": 2},
            # 武器
            "木剑": {"木头": 2, "木棍": 1},
            "石剑": {"圆石": 2, "木棍": 1},
            "铁剑": {"铁锭": 2, "木棍": 1},
            "金剑": {"金锭": 2, "木棍": 1},
            "钻石剑": {"钻石": 2, "木棍": 1},
            "弓": {"线": 3, "木棍": 3},
            "弩": {"铁锭": 2, "线": 3, "绊线钩": 1},
            "盾牌": {"木板": 6, "铁锭": 1},
            # 建筑
            "木板": {"木头": 1},
            "木棍": {"木板": 2},
            "砖块": {"粘土": 4},
            "砖块方块": {"砖块": 4},
            "玻璃": {"沙子": 1},
            "玻璃面板": {"玻璃": 6},
            "梯子": {"木棍": 7},
            "门": {"木板": 6},
            "栅栏": {"木棍": 4},
            "栅栏门": {"木棍": 4, "木板": 2},
            "橡木台阶": {"木板": 6},
            "石台阶": {"圆石": 6},
            "砖台阶": {"砖块方块": 6},
            "楼梯": {"木板": 5},
            "石楼梯": {"圆石": 6},
            "砖楼梯": {"砖块方块": 6},
            "压力板": {"木板": 2},
            "石压力板": {"石头": 2},
            "按钮": {"石头": 1},
            "橡木按钮": {"木板": 1},
            "栅栏门": {"木棍": 4, "木板": 2},
            # 1.12.2新增建筑方块
            "混凝土粉末": {"沙子": 4, "砂砾": 4, "染料": 1},
            "陶瓦": {"粘土": 1},
            "带釉陶瓦": {"陶瓦": 1},
            # 羊毛染色
            "白色羊毛": {"羊毛": 1},
            "橙色羊毛": {"白色羊毛": 1, "橙色染料": 1},
            "品红色羊毛": {"白色羊毛": 1, "品红色染料": 1},
            "淡蓝色羊毛": {"白色羊毛": 1, "淡蓝色染料": 1},
            "黄色羊毛": {"白色羊毛": 1, "黄色染料": 1},
            "黄绿色羊毛": {"白色羊毛": 1, "黄绿色染料": 1},
            "粉色羊毛": {"白色羊毛": 1, "粉色染料": 1},
            "灰色羊毛": {"白色羊毛": 1, "灰色染料": 1},
            "淡灰色羊毛": {"白色羊毛": 1, "淡灰色染料": 1},
            "青色羊毛": {"白色羊毛": 1, "青色染料": 1},
            "紫色羊毛": {"白色羊毛": 1, "紫色染料": 1},
            "蓝色羊毛": {"白色羊毛": 1, "蓝色染料": 1},
            "棕色羊毛": {"白色羊毛": 1, "棕色染料": 1},
            "绿色羊毛": {"白色羊毛": 1, "绿色染料": 1},
            "红色羊毛": {"白色羊毛": 1, "红色染料": 1},
            "黑色羊毛": {"白色羊毛": 1, "黑色染料": 1},
            # 染料
            "骨粉": {"骨头": 1},
            "墨囊": {"鱿鱼": 1},
            "红色染料": {"虞美人": 1},
            "橙色染料": {"橙色郁金香": 1},
            "黄色染料": {"向日葵": 1},
            "绿色染料": {"仙人掌绿": 1},
            "青色染料": {"绿色染料": 1, "淡蓝色染料": 1},
            "蓝色染料": {"矢车菊": 1},
            "紫色染料": {"蓝色染料": 1, "红色染料": 1},
            "品红色染料": {"紫色染料": 1, "粉色染料": 1},
            "粉色染料": {"粉红色郁金香": 1},
            "棕色染料": {"可可豆": 1},
            "灰色染料": {"墨囊": 1, "骨粉": 2},
            "淡灰色染料": {"骨粉": 1, "灰色染料": 1},
            "黄绿色染料": {"仙人掌绿": 2},
            "淡蓝色染料": {"蓝花楹": 1},
            # 食物
            "面包": {"小麦": 3},
            "蛋糕": {"小麦": 3, "鸡蛋": 2, "牛奶": 1, "糖": 1},
            "曲奇": {"小麦": 2, "可可豆": 1},
            "西瓜": {"西瓜种子": 1},
            "南瓜派": {"南瓜": 1, "鸡蛋": 1, "糖": 1},
            "甜菜汤": {"甜菜根": 3, "碗": 1},
            "蘑菇煲": {"棕色蘑菇": 1, "红色蘑菇": 1, "碗": 1},
            "炖兔肉": {"兔子": 1, "胡萝卜": 1, "烤土豆": 1, "碗": 1},
            "糖": {"甘蔗": 1},
            "胡萝卜": {"胡萝卜": 1},
            "土豆": {"土豆": 1},
            "烤土豆": {"土豆": 1},
            "胡萝卜蛋糕": {"胡萝卜": 2, "糖": 3, "鸡蛋": 1, "小麦": 3},
            # 材料
            "铁锭": {"铁矿石": 1, "煤炭": 1},
            "金锭": {"金矿石": 1, "煤炭": 1},
            "钻石": {"钻石矿石": 1},
            "线": {"羊毛": 1},
            "纸": {"甘蔗": 3},
            "书": {"纸": 3, "皮革": 1},
            "书与笔": {"书": 1, "羽毛": 1, "墨囊": 1},
            "附魔书": {"书": 1, "青金石": 3, "经验瓶": 1},
            "皮革": {"兔子皮": 4},
            "兔子皮": {"兔子": 1},
            "粘液球": {"史莱姆": 1},
            "烈焰棒": {"烈焰人": 1},
            "烈焰粉": {"烈焰棒": 1},
            "末影珍珠": {"末影人": 1},
            "恶魂之泪": {"恶魂": 1},
            "龙息": {"末影龙": 1},
            "下界之星": {"凋灵": 1},
            "骨粉": {"骨头": 1},
            "骨头": {"骷髅": 1},
            "羽毛": {"鸡": 1},
            "鸡蛋": {"鸡": 1},
            "皮革": {"牛": 1},
            "牛肉": {"牛": 1},
            "猪肉": {"猪": 1},
            "羊肉": {"羊": 1},
            "鸡肉": {"鸡": 1},
            "兔肉": {"兔子": 1},
            "熟牛肉": {"牛肉": 1, "煤炭": 1},
            "熟猪肉": {"猪肉": 1, "煤炭": 1},
            "熟羊肉": {"羊肉": 1, "煤炭": 1},
            "熟鸡肉": {"鸡肉": 1, "煤炭": 1},
            "熟兔肉": {"兔肉": 1, "煤炭": 1},
            # 机械/红石
            "活塞": {"木板": 3, "圆石": 4, "铁锭": 1, "红石": 1},
            "粘性活塞": {"活塞": 1, "粘液球": 1},
            "红石中继器": {"红石火把": 2, "圆石": 3, "红石": 1},
            "红石比较器": {"红石火把": 3, "石英": 1, "下界石英": 1},
            "红石火把": {"红石": 1, "木棍": 1},
            "红石灯": {"红石": 4, "玻璃": 1},
            "发射器": {"圆石": 7, "弓": 1, "红石": 1},
            "投掷器": {"圆石": 7, "红石": 1},
            "漏斗": {"铁锭": 5, "箱子": 1},
            "箱子": {"木板": 8},
            "陷阱箱": {"箱子": 1, "绊线钩": 1},
            "木桶": {"木板": 8},
            "酿造台": {"烈焰棒": 1, "圆石": 3},
            "炼药锅": {"铁锭": 7},
            "铁砧": {"铁块": 3, "铁锭": 4},
            "砂轮": {"石头": 2, "木板": 1},
            "织布机": {"木板": 3, "线": 2},
            "制图台": {"木板": 4, "纸": 2},
            "烟熏炉": {"圆石": 8, "熔炉": 1},
            "高炉": {"圆石": 8, "熔炉": 1},
            "营火": {"原木": 3, "木棍": 1, "煤炭": 1},
            "灵魂营火": {"灵魂沙": 3, "木棍": 1, "煤炭": 1},
            # 运输
            "矿车": {"铁锭": 5},
            "储物矿车": {"矿车": 1, "箱子": 1},
            "漏斗矿车": {"矿车": 1, "漏斗": 1},
            "动力矿车": {"矿车": 1, "熔炉": 1},
            "船": {"木板": 5},
            "深色橡木船": {"深色橡木木板": 5},
            "云杉船": {"云杉木板": 5},
            "白桦船": {"白桦木板": 5},
            "丛林木船": {"丛林木木板": 5},
            "金合欢船": {"金合欢木板": 5},
            # 装饰
            "画": {"木棍": 8, "羊毛": 1},
            "物品展示框": {"木棍": 8, "皮革": 1},
            "旗帜": {"羊毛": 6, "木棍": 1},
            "花盆": {"红砖": 3},
            "末地烛": {"末地石砖": 1, "烈焰棒": 1},
            "灯笼": {"铁锭": 8, "火把": 1},
            "灵魂灯笼": {"铁锭": 8, "灵魂火把": 1},
            "钟": {"铜锭": 4},
            "测重压力板": {"铁锭": 2},
            "绊线钩": {"铁锭": 1, "线": 1},
            # 1.12.2特色物品
            "信标": {"下界之星": 1, "玻璃": 5, "黑曜石": 3},
            "龙蛋": {"末影龙": 1},
            "结构方块": {"结构空位": 1},
            "命令方块": {"命令方块": 1},
            "调试棒": {"调试棒": 1},
            "知识之书": {"知识之书": 1},
            # 三国特色
            "武将召唤台": {"金锭": 4, "木头": 4, "武将卡": 1},
            "武器架": {"木头": 6},
            "弹药箱": {"木头": 8, "铁锭": 2}
        }
        
        # 🧪 附魔系统（MC 1.12.2风格）
        self.enchantments = {
            # 武器附魔
            "锋利": {"max_level": 5, "description": "增加近战伤害", "type": "weapon"},
            "亡灵杀手": {"max_level": 5, "description": "对亡灵生物造成额外伤害", "type": "weapon"},
            "节肢杀手": {"max_level": 5, "description": "对节肢生物造成额外伤害", "type": "weapon"},
            "击退": {"max_level": 2, "description": "击退敌人", "type": "weapon"},
            "火焰附加": {"max_level": 2, "description": "点燃敌人", "type": "weapon"},
            "抢夺": {"max_level": 3, "description": "增加掉落物", "type": "weapon"},
            # 工具附魔
            "效率": {"max_level": 5, "description": "加快挖掘速度", "type": "tool"},
            "精准采集": {"max_level": 1, "description": "获取方块本身", "type": "tool"},
            "耐久": {"max_level": 3, "description": "减少工具损耗", "type": "tool"},
            "时运": {"max_level": 3, "description": "增加稀有掉落", "type": "tool"},
            " silk_touch": {"max_level": 1, "description": "精准采集", "type": "tool"},
            # 弓箭附魔
            "力量": {"max_level": 5, "description": "增加弓箭伤害", "type": "bow"},
            "冲击": {"max_level": 2, "description": "击退箭矢目标", "type": "bow"},
            "火矢": {"max_level": 1, "description": "箭矢点燃目标", "type": "bow"},
            "无限": {"max_level": 1, "description": "无限箭矢", "type": "bow"},
            "穿刺": {"max_level": 4, "description": "对水生生物伤害", "type": "bow"},
            # 护甲附魔
            "保护": {"max_level": 4, "description": "减少所有伤害", "type": "armor"},
            "火焰保护": {"max_level": 4, "description": "减少火焰伤害", "type": "armor"},
            "爆炸保护": {"max_level": 4, "description": "减少爆炸伤害", "type": "armor"},
            "弹射物保护": {"max_level": 4, "description": "减少远程伤害", "type": "armor"},
            "摔落保护": {"max_level": 4, "description": "减少摔落伤害", "type": "armor"},
            "深海探索者": {"max_level": 3, "description": "水下移动更快", "type": "armor"},
            "冰霜行者": {"max_level": 2, "description": "在水上行走", "type": "armor"},
            "荆棘": {"max_level": 3, "description": "反弹伤害", "type": "armor"},
            # 其他附魔
            "经验修补": {"max_level": 1, "description": "用经验修复物品", "type": "all"},
            "绑定诅咒": {"max_level": 1, "description": "无法移除物品", "type": "curse"},
            "消失诅咒": {"max_level": 1, "description": "死亡时消失", "type": "curse"}
        }
        
        # ⚡ 信标效果（MC 1.12.2风格）
        self.beacon_effects = {
            "速度": {"level": 2, "range": 50, "description": "增加移动速度"},
            "跳跃提升": {"level": 2, "range": 50, "description": "增加跳跃高度"},
            "力量": {"level": 2, "range": 50, "description": "增加近战伤害"},
            "抗性提升": {"level": 2, "range": 50, "description": "减少伤害"},
            "生命恢复": {"level": 2, "range": 50, "description": "缓慢恢复生命"},
            "急迫": {"level": 1, "range": 50, "description": "加快挖掘速度"},
            "幸运": {"level": 1, "range": 50, "description": "增加掉落率"}
        }
        
        # 当前激活的信标效果
        self.active_beacon_effect = None
        self.beacon_range = 0
        
        # 合成网格（3x3）
        self.crafting_grid = [[None for _ in range(3)] for _ in range(3)]
        self.show_crafting = False
        self.crafting_result = None
        
        # MC风格玩家状态
        self.health = 20  # 生命值 (0-20)
        self.max_health = 20
        self.hunger = 20  # 饥饿值 (0-20)
        self.max_hunger = 20
        self.oxygen = 10  # 氧气值 (0-10, 水中使用)
        self.max_oxygen = 10
        self.experience = 0  # 经验值
        self.level = 0  # 等级
        self.armor = 0  # 护甲值 (0-20)
        self.max_armor = 20
        self.is_sneaking = False  # 潜行
        self.is_sprinting = False  # 冲刺
        
        # 昼夜系统（MC风格）
        self.day_time = 0  # 0-24000 (MC时间)
        self.day_speed = 10  # 时间流逝速度
        self.is_day = True
        self.sun_angle = 0
        self.moon_angle = 0
        self.time_of_day = "上午"
        
        # MC风格音效系统
        self.sounds = {
            "block_place": {"pitch": 1.0, "volume": 0.5},
            "block_break": {"pitch": 0.8, "volume": 0.6},
            "jump": {"pitch": 1.0, "volume": 0.3},
            "hurt": {"pitch": 1.0, "volume": 0.5},
            "eat": {"pitch": 1.0, "volume": 0.4},
            "craft": {"pitch": 0.9, "volume": 0.5}
        }
        
        # MC风格粒子效果
        self.particles = []
        
        # MC风格聊天系统
        self.chat_messages = []
        self.max_chat_lines = 10
        
        # MC风格物品提示
        self.hovered_item = None
        self.item_tooltip_timer = 0
        
        # MC风格成就系统
        self.achievements = {
            "first_block": {"name": "开始建造", "description": "放置第一个方块", "unlocked": False},
            "first_craft": {"name": "工匠", "description": "完成第一次合成", "unlocked": False},
            "first_kill": {"name": "猎人", "description": "杀死第一个怪物", "unlocked": False},
            "day_night": {"name": "经历一天", "description": "度过一个完整的昼夜循环", "unlocked": False}
        }
        
        # MC风格统计数据
        self.stats = {
            "blocks_placed": 0,
            "blocks_broken": 0,
            "items_crafted": 0,
            "mobs_killed": 0,
            "days_passed": 0
        }
        
        # MC风格游戏模式
        self.game_mode = "survival"  # survival, creative, adventure
        self.can_fly = False
        self.flying = False
        self.fly_speed = 0.1
        
        # 🐾 MC 1.12.2生物类型系统
        self.mob_types = {
            # 被动生物
            "passive": [
                {"name": "鸡", "health": 4, "drop": ["鸡肉", "羽毛", "鸡蛋"], "spawn_biome": "所有"},
                {"name": "牛", "health": 10, "drop": ["牛肉", "皮革"], "spawn_biome": "平原、森林"},
                {"name": "猪", "health": 10, "drop": ["猪肉"], "spawn_biome": "平原、森林"},
                {"name": "羊", "health": 8, "drop": ["羊肉", "羊毛"], "spawn_biome": "平原、草原"},
                {"name": "兔子", "health": 3, "drop": ["兔肉", "兔子皮"], "spawn_biome": "森林、平原"},
                {"name": "马", "health": 15-30, "drop": ["皮革"], "spawn_biome": "平原、草原"},
                {"name": "驴", "health": 15, "drop": ["皮革"], "spawn_biome": "平原"},
                {"name": "骡", "health": 15, "drop": ["皮革"], "spawn_biome": "平原"},
                {"name": "羊驼", "health": 15, "drop": ["皮革"], "spawn_biome": "沙漠、热带草原"},
                {"name": "狼", "health": 8, "drop": ["骨头"], "spawn_biome": "森林、针叶林"},
                {"name": "猫", "health": 10, "drop": [], "spawn_biome": "村庄"},
                {"name": "鹦鹉", "health": 6, "drop": ["羽毛"], "spawn_biome": "丛林"},
                {"name": "蝙蝠", "health": 6, "drop": [], "spawn_biome": "洞穴"},
                {"name": "鱿鱼", "health": 10, "drop": ["墨囊"], "spawn_biome": "海洋"},
                {"name": "海龟", "health": 30, "drop": ["海龟壳"], "spawn_biome": "沙滩"},
                {"name": "熊猫", "health": 20, "drop": ["竹子"], "spawn_biome": "竹林"},
                {"name": "狐狸", "health": 10, "drop": ["兔子皮"], "spawn_biome": "针叶林、积雪针叶林"},
                {"name": "蜜蜂", "health": 10, "drop": ["蜂蜜瓶"], "spawn_biome": "森林、花林"},
                {"name": "海豚", "health": 10, "drop": ["生鱼"], "spawn_biome": "海洋"},
                {"name": "河豚", "health": 1, "drop": ["河豚"], "spawn_biome": "温暖海洋"},
                {"name": "热带鱼", "health": 1, "drop": ["热带鱼"], "spawn_biome": "温暖海洋"},
                {"name": "鳕鱼", "health": 3, "drop": ["鳕鱼"], "spawn_biome": "海洋"},
                {"name": "三文鱼", "health": 3, "drop": ["三文鱼"], "spawn_biome": "冷水海洋、河流"},
                {"name": "鲑鱼", "health": 3, "drop": ["鲑鱼"], "spawn_biome": "冷水海洋"},
                {"name": "美西螈", "health": 14, "drop": ["美西螈"], "spawn_biome": "繁茂洞穴"},
                {"name": "发光鱿鱼", "health": 10, "drop": ["荧光墨囊"], "spawn_biome": "地下洞穴"},
                {"name": "骆驼", "health": 30, "drop": ["皮革"], "spawn_biome": "沙漠"},
                {"name": "嗅探兽", "health": 30, "drop": ["远古种子"], "spawn_biome": "远古城市"}
            ],
            # 中立生物
            "neutral": [
                {"name": "末影人", "health": 40, "drop": ["末影珍珠"], "spawn_biome": "末地、地下"},
                {"name": "蜘蛛", "health": 16, "drop": ["线", "蜘蛛眼"], "spawn_biome": "地下、夜晚"},
                {"name": "洞穴蜘蛛", "health": 12, "drop": ["线", "蜘蛛眼"], "spawn_biome": "废弃矿井"},
                {"name": "僵尸猪人", "health": 20, "drop": ["金锭", "腐肉"], "spawn_biome": "下界"},
                {"name": "猪灵", "health": 20, "drop": ["金锭"], "spawn_biome": "下界"},
                {"name": "猪灵蛮兵", "health": 50, "drop": ["下界合金锭"], "spawn_biome": "下界堡垒"},
                {"name": "北极熊", "health": 30, "drop": ["生羊肉"], "spawn_biome": "雪原"},
                {"name": "狼", "health": 8, "drop": ["骨头"], "spawn_biome": "森林"},
                {"name": "铁傀儡", "health": 100, "drop": ["铁锭"], "spawn_biome": "村庄"},
                {"name": "雪傀儡", "health": 4, "drop": ["雪球"], "spawn_biome": "雪地"}
            ],
            # 敌对生物
            "hostile": [
                {"name": "僵尸", "health": 20, "drop": ["腐肉", "铁锭"], "spawn_biome": "夜晚、地下"},
                {"name": "骷髅", "health": 20, "drop": ["骨头", "箭矢"], "spawn_biome": "夜晚、地下"},
                {"name": "苦力怕", "health": 20, "drop": ["火药"], "spawn_biome": "夜晚、地下"},
                {"name": "史莱姆", "health": 4-16, "drop": ["粘液球"], "spawn_biome": "沼泽、地下"},
                {"name": "恶魂", "health": 10, "drop": ["恶魂之泪", "火药"], "spawn_biome": "下界"},
                {"name": "烈焰人", "health": 20, "drop": ["烈焰棒"], "spawn_biome": "下界堡垒"},
                {"name": "岩浆怪", "health": 4-16, "drop": ["岩浆膏"], "spawn_biome": "下界"},
                {"name": "女巫", "health": 26, "drop": ["药水", "红石"], "spawn_biome": "沼泽小屋"},
                {"name": "守卫者", "health": 30, "drop": ["海晶碎片"], "spawn_biome": "海底遗迹"},
                {"name": "远古守卫者", "health": 80, "drop": ["海晶碎片", "海绵"], "spawn_biome": "海底遗迹"},
                {"name": "凋灵骷髅", "health": 20, "drop": ["凋灵骷髅头", "石剑"], "spawn_biome": "下界堡垒"},
                {"name": "流浪者", "health": 20, "drop": ["骨头", "箭矢"], "spawn_biome": "雪原"},
                {"name": "尸壳", "health": 20, "drop": ["腐肉", "金锭"], "spawn_biome": "沙漠"},
                {"name": "幻翼", "health": 20, "drop": ["幻翼膜"], "spawn_biome": "高空（长时间不睡觉）"},
                {"name": "掠夺者", "health": 24, "drop": ["弩", "箭矢"], "spawn_biome": "掠夺者前哨站"},
                {"name": "卫道士", "health": 24, "drop": ["铁斧"], "spawn_biome": "林地府邸"},
                {"name": "唤魔者", "health": 24, "drop": ["不死图腾"], "spawn_biome": "林地府邸"},
                {"name": "潜影贝", "health": 30, "drop": ["潜影壳"], "spawn_biome": "末地城"},
                {"name": "劫掠兽", "health": 100, "drop": ["皮革", "铁锭"], "spawn_biome": "袭击事件"},
                {"name": "监守者", "health": 500, "drop": ["回响碎片"], "spawn_biome": "深暗之域"},
                {"name": "末影龙", "health": 200, "drop": ["经验", "龙蛋"], "spawn_biome": "末地"},
                {"name": "凋灵", "health": 300, "drop": ["下界之星"], "spawn_biome": "下界"}
            ],
            # 1.12.2新增生物
            "special_1_12": [
                {"name": "鹦鹉", "health": 6, "drop": ["羽毛"], "spawn_biome": "丛林"},
                {"name": "北极熊", "health": 30, "drop": ["生羊肉"], "spawn_biome": "雪原"},
                {"name": "狐狸", "health": 10, "drop": ["兔子皮"], "spawn_biome": "针叶林"},
                {"name": "幻翼", "health": 20, "drop": ["幻翼膜"], "spawn_biome": "高空"},
                {"name": "掠夺者", "health": 24, "drop": ["弩"], "spawn_biome": "前哨站"},
                {"name": "卫道士", "health": 24, "drop": ["铁斧"], "spawn_biome": "林地府邸"},
                {"name": "唤魔者", "health": 24, "drop": ["不死图腾"], "spawn_biome": "林地府邸"},
                {"name": "劫掠兽", "health": 100, "drop": ["皮革"], "spawn_biome": "袭击"}
            ]
        }
        
        # 当前生物列表
        self.active_mobs = []
        
        # MC风格命令系统
        self.command_input = ""
        self.show_command = False
        self.command_history = []
        
        # 自动存档系统
        self.auto_save_interval = 300  # 每5分钟自动存档（300秒）
        self.auto_save_timer = 0
        self.last_auto_save_time = time.time()
        
        # 彩蛋系统（150个彩蛋！）
        self.eggs = {
            "notch": {"found": False, "hint": "找到Notch的头像"},
            "herobrine": {"found": False, "hint": "在夜晚遇到Herobrine"},
            "creeper_explosion": {"found": False, "hint": "让苦力怕在你面前爆炸"},
            "secret_base": {"found": False, "hint": "找到隐藏的基地"},
            "developer": {"found": False, "hint": "输入开发者命令"},
            "first_block": {"found": False, "hint": "放置第一个方块"},
            "first_craft": {"found": False, "hint": "完成第一次合成"},
            "first_kill": {"found": False, "hint": "杀死第一个怪物"},
            "day_night": {"found": False, "hint": "度过一个完整的昼夜循环"},
            "100_blocks": {"found": False, "hint": "放置100个方块"},
            "100_kills": {"found": False, "hint": "杀死100个怪物"},
            "diamond": {"found": False, "hint": "找到钻石"},
            "gold": {"found": False, "hint": "找到金矿"},
            "iron": {"found": False, "hint": "找到铁矿"},
            "coal": {"found": False, "hint": "找到煤矿"},
            "lava": {"found": False, "hint": "找到岩浆"},
            "water": {"found": False, "hint": "找到水源"},
            "tree": {"found": False, "hint": "砍倒10棵树"},
            "house": {"found": False, "hint": "建造一个房子"},
            "tower": {"found": False, "hint": "建造一个高塔"},
            "bridge": {"found": False, "hint": "建造一座桥"},
            "underground": {"found": False, "hint": "深入地下50格"},
            "high_altitude": {"found": False, "hint": "到达高空50格"},
            "speed_run": {"found": False, "hint": "在1分钟内跑100格"},
            "no_damage": {"found": False, "hint": "无伤生存10分钟"},
            "night_owl": {"found": False, "hint": "在夜晚活动30分钟"},
            "sunrise": {"found": False, "hint": "观看一次日出"},
            "sunset": {"found": False, "hint": "观看一次日落"},
            "rain": {"found": False, "hint": "在雨中待5分钟"},
            "snow": {"found": False, "hint": "在雪中待5分钟"},
            "swim": {"found": False, "hint": "游泳100格"},
            "jump_100": {"found": False, "hint": "跳跃100次"},
            "sneak": {"found": False, "hint": "潜行100格"},
            "sprint": {"found": False, "hint": "冲刺100格"},
            "fly_creative": {"found": False, "hint": "在创造模式飞行100格"},
            "build_pyramid": {"found": False, "hint": "建造一个金字塔"},
            "build_castle": {"found": False, "hint": "建造一座城堡"},
            "farm": {"found": False, "hint": "建造一个农场"},
            "mine_shaft": {"found": False, "hint": "挖掘一个矿道"},
            "library": {"found": False, "hint": "建造一个图书馆"},
            "armor": {"found": False, "hint": "穿上全套护甲"},
            "sword": {"found": False, "hint": "制作一把剑"},
            "bow": {"found": False, "hint": "制作一把弓"},
            "pickaxe": {"found": False, "hint": "制作一把镐子"},
            "axe": {"found": False, "hint": "制作一把斧头"},
            "shovel": {"found": False, "hint": "制作一把铲子"},
            "hoe": {"found": False, "hint": "制作一把锄头"},
            "craft_table": {"found": False, "hint": "制作一个工作台"},
            "furnace": {"found": False, "hint": "制作一个熔炉"},
            "chest": {"found": False, "hint": "制作一个箱子"},
            "bed": {"found": False, "hint": "制作一张床"},
            "door": {"found": False, "hint": "制作一扇门"},
            "fence": {"found": False, "hint": "制作栅栏"},
            "ladder": {"found": False, "hint": "制作梯子"},
            "glass": {"found": False, "hint": "制作玻璃"},
            "brick": {"found": False, "hint": "制作砖块"},
            "cake": {"found": False, "hint": "制作一个蛋糕"},
            "bread": {"found": False, "hint": "制作面包"},
            "gold_ingot": {"found": False, "hint": "冶炼金锭"},
            "iron_ingot": {"found": False, "hint": "冶炼铁锭"},
            "cook_food": {"found": False, "hint": "烹饪食物"},
            "fish": {"found": False, "hint": "钓一条鱼"},
            "pet": {"found": False, "hint": "拥有一只宠物"},
            "follower": {"found": False, "hint": "拥有一个追随者"},
            "general": {"found": False, "hint": "召唤一名武将"},
            "gun": {"found": False, "hint": "制作一把枪"},
            "ammo": {"found": False, "hint": "制作弹药"},
            "firework": {"found": False, "hint": "制作烟花"},
            "music_disc": {"found": False, "hint": "找到音乐唱片"},
            "painting": {"found": False, "hint": "放置一幅画"},
            "map": {"found": False, "hint": "制作一张地图"},
            "compass": {"found": False, "hint": "制作一个指南针"},
            "clock": {"found": False, "hint": "制作一个时钟"},
            "enchant": {"found": False, "hint": "附魔物品"},
            "anvil": {"found": False, "hint": "制作铁砧"},
            "beacon": {"found": False, "hint": "激活信标"},
            "ender_eye": {"found": False, "hint": "制作末影之眼"},
            "nether_portal": {"found": False, "hint": "建造地狱门"},
            "end_portal": {"found": False, "hint": "建造末地传送门"},
            "dragon_kill": {"found": False, "hint": "击败末影龙"},
            "wither_kill": {"found": False, "hint": "击败凋灵"},
            "elder_guardian": {"found": False, "hint": "击败远古守卫者"},
            "wither_skeleton": {"found": False, "hint": "击败凋灵骷髅"},
            "stray": {"found": False, "hint": "击败流浪者"},
            "husk": {"found": False, "hint": "击败尸壳"},
            "phantom": {"found": False, "hint": "击败幻翼"},
            "ravager": {"found": False, "hint": "击败劫掠兽"},
            "pillager": {"found": False, "hint": "击败掠夺者"},
            "vindicator": {"found": False, "hint": "击败卫道士"},
            "evoker": {"found": False, "hint": "击败唤魔者"},
            "shulker": {"found": False, "hint": "击败潜影贝"},
            "enderman": {"found": False, "hint": "击败末影人"},
            "slime": {"found": False, "hint": "击败史莱姆"},
            "magma_cube": {"found": False, "hint": "击败岩浆怪"},
            "ghast": {"found": False, "hint": "击败恶魂"},
            "blaze": {"found": False, "hint": "击败烈焰人"},
            "cave_spider": {"found": False, "hint": "击败洞穴蜘蛛"},
            "spider_jockey": {"found": False, "hint": "击败蜘蛛骑士"},
            "jockey": {"found": False, "hint": "击败骷髅骑士"},
            "zombie_villager": {"found": False, "hint": "治愈僵尸村民"},
            "villager_trade": {"found": False, "hint": "与村民交易"},
            "raid": {"found": False, "hint": "完成一次袭击"},
            "pillager_outpost": {"found": False, "hint": "找到掠夺者前哨站"},
            "stronghold": {"found": False, "hint": "找到要塞"},
            "jungle_temple": {"found": False, "hint": "找到丛林神庙"},
            "desert_temple": {"found": False, "hint": "找到沙漠神殿"},
            "ocean_monument": {"found": False, "hint": "找到海底遗迹"},
            "woodland_mansion": {"found": False, "hint": "找到林地府邸"},
            "shipwreck": {"found": False, "hint": "找到沉船"},
            "ruined_portal": {"found": False, "hint": "找到废弃传送门"},
            "treasure": {"found": False, "hint": "找到宝藏"},
            "easter_egg": {"found": False, "hint": "找到复活节彩蛋"},
            "birthday": {"found": False, "hint": "庆祝生日"},
            "anniversary": {"found": False, "hint": "庆祝一周年"},
            "secret_command": {"found": False, "hint": "发现隐藏命令"},
            "secret_room": {"found": False, "hint": "找到一个秘密房间"},
            "hidden_treasure": {"found": False, "hint": "找到隐藏的宝藏"},
            "mysterious_cave": {"found": False, "hint": "发现一个神秘洞穴"},
            "ancient_ruins": {"found": False, "hint": "探索古代遗迹"},
            "floating_island": {"found": False, "hint": "找到一个浮空岛"},
            "underwater_base": {"found": False, "hint": "建造一个水下基地"},
            "sky_base": {"found": False, "hint": "建造一个天空基地"},
            "underground_bunker": {"found": False, "hint": "建造一个地下 bunker"},
            "tree_house": {"found": False, "hint": "建造一个树屋"},
            "desert_base": {"found": False, "hint": "在沙漠建造基地"},
            "ice_base": {"found": False, "hint": "在冰原建造基地"},
            "jungle_base": {"found": False, "hint": "在丛林建造基地"},
            "mountain_base": {"found": False, "hint": "在山脉建造基地"},
            "volcano_base": {"found": False, "hint": "在火山建造基地"},
            "portal_base": {"found": False, "hint": "建造传送门基地"},
            "nether_fortress": {"found": False, "hint": "找到地狱堡垒"},
            "bastion_remnant": {"found": False, "hint": "找到荒漠前哨"},
            "end_city": {"found": False, "hint": "找到末地城"},
            "deep_dark": {"found": False, "hint": "探索深暗之域"},
            "mangrove_swamp": {"found": False, "hint": "探索红树林沼泽"},
            "cherry_grove": {"found": False, "hint": "找到樱花林"},
            "suspicious_sand": {"found": False, "hint": "挖掘可疑沙子"},
            " Suspicious_gravel": {"found": False, "hint": "挖掘可疑砂砾"},
            "ancient_city": {"found": False, "hint": "进入远古城市"},
            "warden": {"found": False, "hint": "遭遇监守者"},
            "allay": {"found": False, "hint": "找到一只同伴"},
            "axolotl": {"found": False, "hint": "找到一只美西螈"},
            "glow_squid": {"found": False, "hint": "找到一只发光鱿鱼"},
            "goat": {"found": False, "hint": "找到一只山羊"},
            "frog": {"found": False, "hint": "找到一只青蛙"},
            "tadpole": {"found": False, "hint": "找到一只蝌蚪"},
            "sniffer": {"found": False, "hint": "找到一只嗅探兽"},
            "camel": {"found": False, "hint": "找到一只骆驼"},
            "horse_armor": {"found": False, "hint": "制作马铠"},
            "horse_bridge": {"found": False, "hint": "骑马跑1000格"},
            "boat_base": {"found": False, "hint": "建造船坞"},
            "minecart_base": {"found": False, "hint": "建造矿车轨道"},
            "railway": {"found": False, "hint": "建造铁路"},
            "hopper_minecart": {"found": False, "hint": "制作漏斗矿车"},
            "command_block": {"found": False, "hint": "获得命令方块"},
            "structure_block": {"found": False, "hint": "获得结构方块"},
            "debug_stick": {"found": False, "hint": "获得调试棒"},
            "knowledge_book": {"found": False, "hint": "获得知识之书"},
            "spawner": {"found": False, "hint": "找到刷怪笼"},
            "dragon_egg": {"found": False, "hint": "获得龙蛋"},
            "nether_star": {"found": False, "hint": "获得下界之星"},
            "elytra": {"found": False, "hint": "获得鞘翅"},
            "shulker_box": {"found": False, "hint": "获得潜影盒"},
            "totem_undying": {"found": False, "hint": "获得不死图腾"},
            "heart_of_the_sea": {"found": False, "hint": "获得海洋之心"},
            "trident": {"found": False, "hint": "获得三叉戟"},
            "crossbow": {"found": False, "hint": "制作弩"},
            "shield": {"found": False, "hint": "制作盾牌"},
            "turtle_helmet": {"found": False, "hint": "制作海龟壳"},
            "棱彩染料": {"found": False, "hint": "收集所有棱彩染料"},
            "马匹速度": {"found": False, "hint": "驯服最快的马"},
            "马匹跳跃": {"found": False, "hint": "驯服跳得最高的马"},
            "骆驼冲刺": {"found": False, "hint": "骑骆驼冲刺"},
            "蜜蜂授粉": {"found": False, "hint": "给花朵授粉"},
            "蜜蜂蜂蜜": {"found": False, "hint": "收集蜂蜜"},
            "村民职业": {"found": False, "hint": "让村民获得所有职业"},
            "僵尸围城": {"found": False, "hint": "在僵尸围城中幸存"},
            "凋灵围城": {"found": False, "hint": "在凋灵围城中幸存"},
            "激流三叉戟": {"found": False, "hint": "用三叉戟激活激流"},
            "闪电苦力怕": {"found": False, "hint": "让苦力怕被闪电击中"},
            "高压爬行者": {"found": False, "hint": "击杀高压爬行者"},
            "闪电指令": {"found": False, "hint": "使用闪电指令"},
            "猪灵交易": {"found": False, "hint": "与猪灵交易"},
            "猪灵布林": {"found": False, "hint": "给猪灵金锭让它变敌意"},
            "下界要塞": {"found": False, "hint": "找到下界要塞"},
            "灵魂沙峡谷": {"found": False, "hint": "探索灵魂沙峡谷"},
            "玄武岩三角洲": {"found": False, "hint": "探索玄武岩三角洲"},
            "诡异森林": {"found": False, "hint": "探索诡异森林"},
            "绯红森林": {"found": False, "hint": "探索绯红森林"}
        }
        self.herobrine_active = False
        self.herobrine_pos = None
        self.herobrine_timer = 0
        
        # 🎮 作弊码系统（经典按键序列）
        self.cheat_code_buffer = []  # 按键序列缓冲区
        self.cheat_code_max_length = 20  # 最大缓冲长度
        self.cheat_code_input_timer = 0  # 输入计时器
        self.cheat_code_input_timeout = 2.0  # 输入超时时间（秒）
        self.last_cheat_key_time = time.time()
        
        # 🎯 作弊码定义（经典+创意）
        self.cheat_codes = {
            # 经典Konami代码风格
            "konami": {
                "sequence": ["up", "up", "down", "down", "left", "right", "left", "right", "b", "a"],
                "name": "Konami大师",
                "effect": "full_power",
                "message": "🎉 Konami代码激活！你获得了无限力量！",
                "reward": {"health": 999, "hunger": 999, "experience": 9999, "level": 100}
            },
            # 简化版Konami
            "konami_simple": {
                "sequence": ["up", "up", "down", "down", "left", "right"],
                "name": "半Konami",
                "effect": "half_power",
                "message": "✨ 半Konami代码！获得中等加成！",
                "reward": {"health": 50, "hunger": 50, "experience": 500}
            },
            # 三国主题
            "three_kingdoms": {
                "sequence": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                "name": "三国九鼎",
                "effect": "summon_generals",
                "message": "⚔️ 九鼎归一！召唤三国武将！",
                "reward": {"generals": ["刘备", "关羽", "张飞", "赵云", "诸葛亮"]}
            },
            # 神秘数字
            "mystery_number": {
                "sequence": ["7", "8", "9", "1", "1", "4", "5", "1", "4"],
                "name": "神秘数字",
                "effect": "mystery",
                "message": "🔮 神秘数字序列！解锁隐藏彩蛋！",
                "reward": {"eggs_unlocked": 10, "secret_items": ["神秘宝石", "远古遗物"]}
            },
            # 42宇宙答案
            "universe_answer": {
                "sequence": ["4", "2"],
                "name": "宇宙答案",
                "effect": "developer_mode",
                "message": "🌌 42是宇宙的终极答案！开发者模式已激活！",
                "reward": {"developer_mode": True, "secret_commands": True}
            },
            # MC风格
            "minecraft_classic": {
                "sequence": ["m", "c", "1", "2"],
                "name": "MC经典",
                "effect": "mc_mode",
                "message": "⛏️ Minecraft经典模式激活！",
                "reward": {"creative_mode": True, "all_blocks": True}
            },
            # 无敌模式
            "god_mode": {
                "sequence": ["g", "o", "d"],
                "name": "上帝模式",
                "effect": "invincible",
                "message": "👑 上帝模式！你已无敌！",
                "reward": {"invincible": True, "health": 9999}
            },
            # 超级速度
            "speed_hack": {
                "sequence": ["s", "p", "e", "e", "d"],
                "name": "超级速度",
                "effect": "super_speed",
                "message": "⚡ 超级速度！你跑得比闪电还快！",
                "reward": {"speed": 10.0, "fly_speed": 5.0}
            },
            # 彩蛋猎人
            "egg_hunter": {
                "sequence": ["e", "g", "g"],
                "name": "彩蛋猎人",
                "effect": "reveal_eggs",
                "message": "🥚 彩蛋猎人模式！所有彩蛋位置已显示！",
                "reward": {"egg_hints": True, "egg_count": 150}
            },
            # 隐藏彩蛋
            "secret_egg": {
                "sequence": ["s", "e", "c", "r", "e", "t"],
                "name": "秘密彩蛋",
                "effect": "unlock_secret",
                "message": "🔐 你发现了隐藏的秘密彩蛋！",
                "reward": {"secret_egg": True, "hidden_items": ["秘密钥匙", "神秘宝箱"]}
            },
            # 随机惊喜
            "random_surprise": {
                "sequence": ["r", "a", "n", "d", "o", "m"],
                "name": "随机惊喜",
                "effect": "random_gift",
                "message": "🎲 随机惊喜！你获得了神秘礼物！",
                "reward": {"random": True}
            },
            # 满背包
            "full_inventory": {
                "sequence": ["f", "u", "l", "l"],
                "name": "满背包",
                "effect": "fill_inventory",
                "message": "📦 背包已填满所有物品！",
                "reward": {"full_inventory": True}
            },
            # 天气控制
            "weather_master": {
                "sequence": ["w", "e", "a", "t", "h", "e", "r"],
                "name": "天气大师",
                "effect": "weather_control",
                "message": "🌤️ 天气大师！你可以自由控制天气！",
                "reward": {"weather_control": True}
            },
            # 时间大师
            "time_master": {
                "sequence": ["t", "i", "m", "e"],
                "name": "时间大师",
                "effect": "time_control",
                "message": "⏰ 时间大师！你可以自由控制时间！",
                "reward": {"time_control": True}
            },
            # 超级跳跃
            "super_jump": {
                "sequence": ["j", "u", "m", "p"],
                "name": "超级跳跃",
                "effect": "high_jump",
                "message": "🦘 超级跳跃！你可以跳到云端！",
                "reward": {"jump_power": 5.0}
            },
            # 飞行模式
            "fly_mode": {
                "sequence": ["f", "l", "y"],
                "name": "飞行模式",
                "effect": "enable_fly",
                "message": "🦋 飞行模式已激活！自由翱翔！",
                "reward": {"can_fly": True, "flying": True}
            },
            # 全解锁
            "unlock_all": {
                "sequence": ["u", "n", "l", "o", "c", "k"],
                "name": "全解锁",
                "effect": "unlock_everything",
                "message": "🔓 全解锁！所有成就和彩蛋已解锁！",
                "reward": {"all_achievements": True, "all_eggs": True}
            },
            # 彩虹模式
            "rainbow": {
                "sequence": ["r", "a", "i", "n", "b", "o", "w"],
                "name": "彩虹模式",
                "effect": "rainbow_effect",
                "message": "🌈 彩虹模式！世界变得绚丽多彩！",
                "reward": {"rainbow_blocks": True, "rainbow_particles": True}
            },
            # 爆炸模式
            "explosion_master": {
                "sequence": ["b", "o", "o", "m"],
                "name": "爆炸大师",
                "effect": "explosion_power",
                "message": "💥 爆炸大师！你的攻击带有爆炸效果！",
                "reward": {"explosion_power": True}
            },
            # 隐身模式
            "invisible": {
                "sequence": ["i", "n", "v", "i", "s"],
                "name": "隐身模式",
                "effect": "invisible",
                "message": "👻 隐身模式！怪物看不到你了！",
                "reward": {"invisible": True}
            },
            # 夜视模式
            "night_vision": {
                "sequence": ["n", "v"],
                "name": "夜视模式",
                "effect": "night_vision",
                "message": "👁️ 夜视模式！黑夜如同白昼！",
                "reward": {"night_vision": True}
            },
            # 传送大师
            "teleport_master": {
                "sequence": ["t", "p"],
                "name": "传送大师",
                "effect": "teleport_power",
                "message": "🌀 传送大师！你可以瞬间移动！",
                "reward": {"teleport_power": True}
            },
            # 创造模式快捷
            "creative_quick": {
                "sequence": ["c", "r", "e", "a", "t", "i", "v", "e"],
                "name": "创造模式",
                "effect": "creative_mode",
                "message": "🎨 创造模式已激活！尽情建造！",
                "reward": {"game_mode": "creative"}
            },
            # 生存模式快捷
            "survival_quick": {
                "sequence": ["s", "u", "r", "v", "i", "v", "e"],
                "name": "生存模式",
                "effect": "survival_mode",
                "message": "⚔️ 生存模式已激活！开始冒险！",
                "reward": {"game_mode": "survival"}
            },
            # 满级
            "max_level": {
                "sequence": ["l", "v", "9", "9"],
                "name": "满级大师",
                "effect": "max_level",
                "message": "🏆 满级大师！你已达到最高等级！",
                "reward": {"level": 99, "experience": 999999}
            },
            # 无限资源
            "infinite_resources": {
                "sequence": ["i", "n", "f", "i", "n", "i", "t", "y"],
                "name": "无限资源",
                "effect": "infinite_items",
                "message": "♾️ 无限资源！物品永不耗尽！",
                "reward": {"infinite_items": True}
            },
            # 召唤神兽
            "summon_beast": {
                "sequence": ["b", "e", "a", "s", "t"],
                "name": "召唤神兽",
                "effect": "spawn_pet",
                "message": "🐉 神兽降临！你获得了一只神兽宠物！",
                "reward": {"pet": "神兽"}
            },
            # 音乐模式
            "music_mode": {
                "sequence": ["m", "u", "s", "i", "c"],
                "name": "音乐模式",
                "effect": "play_music",
                "message": "🎵 音乐模式！享受美妙旋律！",
                "reward": {"music_enabled": True}
            },
            # 调试模式
            "debug_mode": {
                "sequence": ["d", "e", "b", "u", "g"],
                "name": "调试模式",
                "effect": "debug_info",
                "message": "🔧 调试模式！显示所有调试信息！",
                "reward": {"debug_mode": True}
            },
            # 粒子大师
            "particle_master": {
                "sequence": ["p", "a", "r", "t", "i", "c", "l", "e"],
                "name": "粒子大师",
                "effect": "particle_effects",
                "message": "✨ 粒子大师！绚丽粒子效果已激活！",
                "reward": {"particle_effects": True, "max_particles": 1000}
            },
            # 神秘代码（隐藏）
            "hidden_cheat": {
                "sequence": ["h", "i", "d", "d", "e", "n"],
                "name": "隐藏代码",
                "effect": "hidden_power",
                "message": "🎭 你发现了隐藏的神秘代码！",
                "reward": {"hidden_power": True, "secret_mode": True}
            },
            # 终极代码
            "ultimate": {
                "sequence": ["u", "l", "t", "i", "m", "a", "t", "e"],
                "name": "终极力量",
                "effect": "ultimate_power",
                "message": "🌟 终极力量！你已成为游戏之神！",
                "reward": {"ultimate": True, "all_power": True}
            }
        }
        
        # 📍 特定位置触发彩蛋
        self.secret_locations = {
            "mystery_cave": {"pos": (100, -10, 200), "radius": 5, "egg": "mysterious_cave", "message": "发现神秘洞穴！"},
            "floating_island": {"pos": (500, 100, 300), "radius": 10, "egg": "floating_island", "message": "发现浮空岛！"},
            "treasure_spot": {"pos": (-50, 0, 150), "radius": 3, "egg": "hidden_treasure", "message": "发现隐藏宝藏！"},
            "developer_sign": {"pos": (0, 50, 0), "radius": 2, "egg": "developer", "message": "发现开发者签名！"},
            "notch_statue": {"pos": (300, 20, 400), "radius": 5, "egg": "notch", "message": "发现Notch雕像！"},
            "herobrine_shrine": {"pos": (-200, -20, -100), "radius": 3, "egg": "herobrine", "message": "⚠️ 发现Herobrine神殿..."},
            "ancient_ruins": {"pos": (600, 0, -200), "radius": 8, "egg": "ancient_ruins", "message": "发现古代遗迹！"},
            "secret_base": {"pos": (1000, -50, 500), "radius": 10, "egg": "secret_base", "message": "发现秘密基地！"}
        }
        
        # 🎯 已激活的作弊效果
        self.active_cheat_effects = {
            "invincible": False,
            "super_speed": False,
            "high_jump": False,
            "invisible": False,
            "night_vision": False,
            "weather_control": False,
            "time_control": False,
            "teleport_power": False,
            "infinite_items": False,
            "explosion_power": False,
            "rainbow_blocks": False,
            "rainbow_particles": False,
            "particle_effects": False,
            "egg_hints": False,
            "developer_mode": False,
            "debug_mode": False,
            "hidden_power": False,
            "ultimate": False,
            "secret_mode": False,
            "music_enabled": False
        }
        
        # 📊 作弊码统计
        self.cheat_stats = {
            "codes_entered": 0,
            "codes_successful": 0,
            "last_code": None,
            "total_rewards": 0
        }
        
        # 海浪效果
        self.wave_particles = []
        self.wave_timer = 0
        
        # 天气系统
        self.weather = "clear"  # clear, rain, snow, thunder
        self.weather_timer = 0
        self.rain_particles = []
        self.snow_particles = []
        self.thunder_timer = 0
        self.is_thundering = False
        
        # 粒子效果系统
        self.effect_particles = []  # 特效粒子（爆炸、附魔等）
        self.dust_particles = []    # 尘埃粒子
        
        # 生物系统
        self.entities = []  # 存储所有实体
        self.monsters = []  # 怪物
        self.animals = []   # 动物
        self.spawn_timer = 0
        
        # 方块颜色定义 (MC 1.12.2风格)
        self.block_colors = {
            # 基础方块
            "泥土": (0.6, 0.4, 0.2),
            "石头": (0.5, 0.5, 0.5),
            "圆石": (0.45, 0.45, 0.45),
            "木头": (0.5, 0.35, 0.15),
            "橡木": (0.6, 0.4, 0.2),
            "木板": (0.65, 0.45, 0.25),
            "草地": (0.3, 0.8, 0.2),
            "树叶": (0.2, 0.6, 0.15),
            "沙子": (0.9, 0.85, 0.6),
            "砂砾": (0.5, 0.5, 0.5),
            "水": (0.2, 0.4, 0.8, 0.7),
            "岩浆": (1.0, 0.5, 0.0, 0.8),
            "玻璃": (0.8, 0.9, 1.0, 0.4),
            "玻璃面板": (0.85, 0.92, 1.0, 0.5),
            "砖块": (0.8, 0.3, 0.2),
            "砖块方块": (0.75, 0.25, 0.2),
            "粘土": (0.7, 0.6, 0.5),
            "陶瓦": (0.65, 0.55, 0.45),
            "带釉陶瓦": (0.7, 0.6, 0.55),
            "混凝土粉末": (0.55, 0.55, 0.55),
            # 矿石
            "铁矿石": (0.55, 0.5, 0.5),
            "金矿石": (0.8, 0.7, 0.3),
            "钻石矿石": (0.3, 0.9, 0.9),
            "红石矿石": (1.0, 0.2, 0.2),
            "绿宝石矿石": (0.3, 0.9, 0.3),
            "煤炭": (0.2, 0.2, 0.2),
            "青金石": (0.2, 0.2, 0.8),
            "下界石英": (0.9, 0.9, 0.9),
            # 下界方块
            "黑曜石": (0.15, 0.15, 0.25),
            "灵魂沙": (0.3, 0.25, 0.2),
            "地狱岩": (0.5, 0.15, 0.15),
            "下界疣": (0.6, 0.2, 0.2),
            "石英块": (0.95, 0.95, 0.95),
            "地狱砖块": (0.5, 0.2, 0.2),
            # 末地方块
            "末地石": (0.4, 0.4, 0.6),
            "末地石砖": (0.35, 0.35, 0.5),
            "末地烛": (0.95, 0.95, 0.95),
            # 羊毛颜色
            "白色羊毛": (0.95, 0.95, 0.95),
            "橙色羊毛": (1.0, 0.5, 0.1),
            "品红色羊毛": (0.85, 0.2, 0.85),
            "淡蓝色羊毛": (0.5, 0.7, 1.0),
            "黄色羊毛": (1.0, 1.0, 0.2),
            "黄绿色羊毛": (0.6, 1.0, 0.2),
            "粉色羊毛": (1.0, 0.5, 0.8),
            "灰色羊毛": (0.5, 0.5, 0.5),
            "淡灰色羊毛": (0.7, 0.7, 0.7),
            "青色羊毛": (0.2, 0.8, 0.8),
            "紫色羊毛": (0.5, 0.2, 0.8),
            "蓝色羊毛": (0.2, 0.3, 0.8),
            "棕色羊毛": (0.5, 0.35, 0.15),
            "绿色羊毛": (0.3, 0.6, 0.2),
            "红色羊毛": (0.8, 0.2, 0.2),
            "黑色羊毛": (0.15, 0.15, 0.15),
            # 建筑方块
            "橡木台阶": (0.65, 0.45, 0.25),
            "石台阶": (0.45, 0.45, 0.45),
            "砖台阶": (0.75, 0.25, 0.2),
            "楼梯": (0.65, 0.45, 0.25),
            "石楼梯": (0.45, 0.45, 0.45),
            "砖楼梯": (0.75, 0.25, 0.2),
            "栅栏": (0.6, 0.4, 0.2),
            "栅栏门": (0.65, 0.45, 0.25),
            "梯子": (0.7, 0.7, 0.7),
            "门": (0.65, 0.45, 0.25),
            "压力板": (0.65, 0.45, 0.25),
            "石压力板": (0.45, 0.45, 0.45),
            "按钮": (0.45, 0.45, 0.45),
            "橡木按钮": (0.65, 0.45, 0.25),
            # 机械方块
            "活塞": (0.6, 0.6, 0.6),
            "粘性活塞": (0.6, 0.6, 0.8),
            "红石中继器": (0.8, 0.6, 0.2),
            "红石比较器": (0.7, 0.5, 0.3),
            "红石火把": (1.0, 0.4, 0.1),
            "红石灯": (1.0, 0.9, 0.5),
            "发射器": (0.5, 0.5, 0.5),
            "投掷器": (0.5, 0.5, 0.5),
            "漏斗": (0.4, 0.4, 0.4),
            "箱子": (0.7, 0.5, 0.3),
            "陷阱箱": (0.5, 0.3, 0.5),
            "木桶": (0.6, 0.4, 0.2),
            "酿造台": (0.25, 0.25, 0.4),
            "炼药锅": (0.5, 0.5, 0.5),
            "铁砧": (0.7, 0.7, 0.7),
            "砂轮": (0.5, 0.5, 0.5),
            "织布机": (0.6, 0.4, 0.2),
            "制图台": (0.6, 0.4, 0.2),
            "烟熏炉": (0.4, 0.4, 0.4),
            "高炉": (0.4, 0.4, 0.4),
            "营火": (0.3, 0.2, 0.1),
            "灵魂营火": (0.4, 0.3, 0.2),
            # 装饰方块
            "花盆": (0.75, 0.35, 0.2),
            "灯笼": (0.9, 0.9, 0.8),
            "灵魂灯笼": (0.8, 0.9, 0.9),
            "钟": (0.7, 0.7, 0.7),
            "测重压力板": (0.6, 0.6, 0.6),
            # 特殊方块
            "信标": (0.9, 0.95, 1.0),
            "龙蛋": (0.5, 0.2, 0.7),
            "命令方块": (0.2, 0.6, 1.0),
            "结构方块": (0.8, 0.6, 0.2),
            "调试棒": (0.3, 0.8, 0.3)
        }
        
    def initialize(self):
        """初始化3D地图"""
        if not opengl_available:
            logger.info("错误: OpenGL不可用，无法启动3D地图")
            return False
        
        try:
            # 初始化pygame
            pygame.init()
            
            # 设置OpenGL显示模式
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
            self.screen = pygame.display.get_surface()
            self.clock = pygame.time.Clock()
            
            # 初始化OpenGL
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glClearColor(0.5, 0.7, 1.0, 1.0)  # 天空蓝色
            
            # 设置光源
            light_position = [1.0, 1.0, 1.0, 0.0]
            glLightfv(GL_LIGHT0, GL_POSITION, light_position)
            
            # 加载字体
            font_name = get_system_font_name()
            try:
                if font_name:
                    self.font_main = create_font(font_name, 40)
                    self.font_small = create_font(font_name, 24)
                else:
                    self.font_main = pygame.font.Font(None, 40)
                    self.font_small = pygame.font.Font(None, 24)
            except Exception as _e:
                self.font_main = pygame.font.Font(None, 40)
                self.font_small = pygame.font.Font(None, 24)
            
            # 加载地图数据
            self.load_map_data()
            
            # 加载MC世界存档数据
            self.load_mc_world_data()
            
            # 显示内存和显卡占用提示
            self.show_performance_warning()
            
            # 初始化玩家位置到第一个地点附近
            if self.locations:
                first_loc = self.locations[0]
                self.player_pos = [first_loc["x"] + 50, 0, first_loc["y"] + 50]
                self.update_camera()
            
            # 生成树木
            self.generate_trees()
            
            return True
        except Exception as e:
            logger.info(f"初始化错误: {e}")
            return False
    
    def show_performance_warning(self):
        """显示性能警告"""
        warning = "警告: 3D模式可能会增加内存和显卡占用"
        text_surf = self.font_main.render(warning, True, COLORS["accent_gold"])
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        # 背景
        bg_rect = pygame.Rect(text_rect.x-20, text_rect.y-10, text_rect.width+40, text_rect.height+20)
        pygame.draw.rect(self.screen, (30, 30, 55, 200), bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["accent_gold"], bg_rect, 2, border_radius=10)
        
        self.screen.blit(text_surf, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)
    
    def load_map_data(self):
        """加载地图数据"""
        try:
            # 验证用户名和密码
            username = data.get("username", "")
            password = data.get("password", "")
            if not username or not password:
                logger.info("错误: 未登录，无法加载地图数据")
                return
            
            map_path = self.get_map_data_path()
            if not os.path.exists(map_path):
                logger.info("地图数据文件不存在，将生成新地图")
                self.locations = self.generate_locations(MAX_LOCATIONS)
                self.save_map_data(self.locations)
            else:
                with open(map_path, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                
                # 验证用户名
                if map_data.get("username") != username:
                    logger.info("错误: 地图数据与当前用户不匹配")
                    return
                
                self.locations = map_data.get("locations", [])
                logger.info(f"成功加载地图数据，包含 {len(self.locations)} 个地点")
        except Exception as e:
            logger.info(f"加载地图数据失败: {e}")
            self.locations = self.generate_locations(MAX_LOCATIONS)
            self.save_map_data(self.locations)
    
    def get_map_data_path(self):
        """获取地图数据路径（打包后写入用户可写目录，避免 CWD 不可写）"""
        username = data.get("username", "")
        safe_username = username.replace('\\', '_').replace('/', '_').replace(':', '_')
        return os.path.join(get_writable_base_dir(), f"map_data_{safe_username}.json")
    
    def save_map_data(self, locations):
        """保存地图数据"""
        try:
            username = data.get("username", "")
            if not username:
                return False
            
            map_data = {
                "username": username,
                "locations": locations,
                "timestamp": time.time()
            }
            
            map_path = self.get_map_data_path()
            with open(map_path, 'w', encoding='utf-8') as f:
                json.dump(map_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.info(f"保存地图数据失败: {e}")
            return False
    
    def load_mc_world_data(self):
        """加载MC世界存档数据"""
        try:
            mc_world = data.get(MC_WORLD_KEY, {})
            
            if mc_world:
                self.placed_blocks = mc_world.get("placed_blocks", [])
                self.hotbar = mc_world.get("hotbar", [None] * 9)
                self.hotbar_selected = mc_world.get("hotbar_selected", 0)
                
                saved_pos = mc_world.get("player_pos", [0, 0, 0])
                if saved_pos and saved_pos != [0, 0, 0]:
                    self.player_pos = saved_pos
                
                self.camera["yaw"] = mc_world.get("camera_yaw", 0)
                self.camera["pitch"] = mc_world.get("camera_pitch", -20)
                self.camera["mode"] = mc_world.get("camera_mode", "first")
                
                self.inventory = mc_world.get("inventory", [])
                self.world_seed = mc_world.get("world_seed", 0)
                
                self.health = mc_world.get("health", 20)
                self.hunger = mc_world.get("hunger", 20)
                self.oxygen = mc_world.get("oxygen", 10)
                self.experience = mc_world.get("experience", 0)
                self.level = mc_world.get("level", 0)
                self.armor = mc_world.get("armor", 0)
                
                self.update_camera()
                self.validate_all()
                logger.info(f"[调试] 加载MC世界数据成功: {len(self.placed_blocks)} 个方块, 位置: {self.player_pos}")
        except Exception as e:
            logger.info(f"[错误] 加载MC世界数据失败: {e}")
            self.validate_all()
    
    def save_mc_world_data(self):
        """保存MC世界存档数据"""
        try:
            mc_world = {
                "placed_blocks": self.placed_blocks,
                "hotbar": self.hotbar,
                "hotbar_selected": self.hotbar_selected,
                "player_pos": self.player_pos,
                "camera_yaw": self.camera["yaw"],
                "camera_pitch": self.camera["pitch"],
                "camera_mode": self.camera["mode"],
                "inventory": getattr(self, 'inventory', []),
                "world_seed": getattr(self, 'world_seed', 0),
                "health": self.health,
                "hunger": self.hunger,
                "oxygen": self.oxygen,
                "experience": self.experience,
                "level": self.level,
                "armor": self.armor
            }
            
            data[MC_WORLD_KEY] = mc_world
            save()
            logger.info(f"[调试] 保存MC世界数据成功: {len(self.placed_blocks)} 个方块, 位置: {self.player_pos}")
        except Exception as e:
            logger.info(f"[错误] 保存MC世界数据失败: {e}")
    
    def generate_locations(self, count):
        """生成地图地点"""
        locations = []
        LOCATION_TYPES = {
            "关隘": {"icon": "🏯", "power": 100},
            "军营": {"icon": "⚔️", "power": 150},
            "村庄": {"icon": "🏠", "power": 50},
            "矿山": {"icon": "⛏️", "power": 80},
            "港口": {"icon": "🚢", "power": 90}
        }
        
        for i in range(count):
            while True:
                x = random.randint(100, MAP_SIZE[0] - 100)
                y = random.randint(100, MAP_SIZE[1] - 100)
                
                # 检查与其他地点的距离
                valid = True
                for loc in locations:
                    distance = math.hypot(x - loc["x"], y - loc["y"])
                    if distance < 150:
                        valid = False
                        break
                if valid:
                    break
            
            loc_type = random.choice(["关隘", "军营", "村庄", "矿山", "港口"])
            level = random.randint(1, 10)
            power = int(LOCATION_TYPES[loc_type]["power"] * (0.5 + level * 0.1))
            
            locations.append({
                "x": x,
                "y": y,
                "type": loc_type,
                "level": level,
                "desc": LOCATION_TYPES[loc_type]["icon"],
                "power": power,
                "owner": "enemy" if loc_type == "军营" else "neutral"
            })
        
        return locations
    
    def generate_trees(self):
        """生成树木"""
        self.trees = []
        tree_count = 200
        
        for _ in range(tree_count):
            x = random.randint(-1800, 1800)
            z = random.randint(-1800, 1800)
            
            too_close = False
            for loc in self.locations:
                if math.hypot(x - loc["x"], z - loc["y"]) < 30:
                    too_close = True
                    break
            for tree in self.trees:
                if math.hypot(x - tree[0], z - tree[1]) < 5:
                    too_close = True
                    break
            
            if not too_close:
                self.trees.append((x, z))
    
    def handle_input(self):
        """处理输入"""
        keys = pygame.key.get_pressed()
        
        # 相机移动
        if keys[pygame.K_w]:
            self.move_forward()
        if keys[pygame.K_s]:
            self.move_backward()
        if keys[pygame.K_a]:
            self.move_left()
        if keys[pygame.K_d]:
            self.move_right()
        if keys[pygame.K_SPACE]:
            if self.player_pos[1] <= 0:  # 只有在地面上才能跳跃
                self.velocity[1] = 5.0  # 跳跃速度
        if keys[pygame.K_LSHIFT]:
            self.camera["speed"] = 0.3  # 减速
        else:
            self.camera["speed"] = 0.6  # 正常速度
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                # 🎮 作弊码按键序列检测
                self.check_cheat_code_sequence(event.key)
                
                if event.key == pygame.K_ESCAPE:
                    self.is_paused = not self.is_paused
                    if self.is_paused:
                        self.is_mouse_locked = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        self.is_mouse_locked = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                elif event.key == pygame.K_TAB:
                    self.is_mouse_locked = not self.is_mouse_locked
                    pygame.mouse.set_visible(not self.is_mouse_locked)
                    pygame.event.set_grab(self.is_mouse_locked)
                elif event.key == pygame.K_f:
                    # 跟随模式
                    if self.follow_target:
                        self.follow_target = None
                        self.message = "取消跟随"
                    else:
                        # 找到最近的地点作为跟随目标
                        if self.locations:
                            closest_loc = min(self.locations, key=lambda loc: math.hypot(loc["x"] - self.player_pos[0], loc["y"] - self.player_pos[2]))
                            self.follow_target = closest_loc
                            self.message = f"开始跟随: {closest_loc['type']}"
                        else:
                            self.message = "没有可跟随的地点"
                    self.message_timer = 2000
                elif event.key == pygame.K_F5:
                    if self.camera["mode"] == "first":
                        self.camera["mode"] = "third_back"
                        self.message = "切换到第三人称视角（背部）"
                    elif self.camera["mode"] == "third_back":
                        self.camera["mode"] = "third_front"
                        self.message = "切换到第三人称视角（正面）"
                    else:
                        self.camera["mode"] = "first"
                        self.message = "切换到第一人称视角"
                    self.message_timer = 2000
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
                    slot = event.key - pygame.K_1
                    self.hotbar_selected = slot
                    if slot < len(self.block_types):
                        self.hotbar[slot] = self.block_types[slot]
                        self.message = f"选择: {self.block_types[slot]}"
                        self.message_timer = 1000
                elif event.key == pygame.K_e:
                    self.show_inventory = not self.show_inventory
                    if self.show_inventory:
                        self.is_mouse_locked = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                elif event.key == pygame.K_c:
                    self.show_crafting = not self.show_crafting
                    if self.show_crafting:
                        self.is_mouse_locked = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                elif event.key == pygame.K_SLASH:
                    self.show_command = True
                    self.command_input = ""
                    self.is_mouse_locked = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                elif event.key == pygame.K_g and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.toggle_gamemode()
                elif event.key == pygame.K_RETURN and self.show_command:
                    if self.command_input.strip():
                        self.execute_command(self.command_input)
                        self.command_history.append(self.command_input)
                        if len(self.command_history) > 10:
                            self.command_history.pop(0)
                    self.show_command = False
                    self.command_input = ""
                    self.is_mouse_locked = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                elif event.key == pygame.K_BACKSPACE and self.show_command:
                    self.command_input = self.command_input[:-1]
                elif self.show_command:
                    if event.unicode:
                        self.command_input += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.is_mouse_locked:
                        self.is_mouse_locked = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self.message = "鼠标已锁定，按Tab键解锁"
                        self.message_timer = 3000
                    else:
                        self.place_block()
                elif event.button == 3:
                    if self.is_mouse_locked:
                        self.break_block()
            elif event.type == pygame.MOUSEMOTION:
                # 鼠标控制
                if self.is_mouse_locked:
                    rel_x, rel_y = event.rel
                    # 修正鼠标方向：左右翻转，上下翻转
                    self.camera["yaw"] += rel_x * self.mouse_sensitivity  # 左右方向正确
                    self.camera["pitch"] -= rel_y * self.mouse_sensitivity  # 上下方向翻转
                    
                    # 限制俯仰角
                    self.camera["pitch"] = max(-89, min(89, self.camera["pitch"]))
        
        return True
    
    def move_forward(self):
        """向前移动"""
        yaw_rad = math.radians(self.camera["yaw"])
        self.player_pos[0] += math.cos(yaw_rad) * self.camera["speed"]
        self.player_pos[2] += math.sin(yaw_rad) * self.camera["speed"]
        self.update_camera()
    
    def move_backward(self):
        """向后移动"""
        yaw_rad = math.radians(self.camera["yaw"])
        self.player_pos[0] -= math.cos(yaw_rad) * self.camera["speed"]
        self.player_pos[2] -= math.sin(yaw_rad) * self.camera["speed"]
        self.update_camera()
    
    def move_left(self):
        """向左移动"""
        yaw_rad = math.radians(self.camera["yaw"])
        self.player_pos[0] -= math.sin(yaw_rad) * self.camera["speed"]
        self.player_pos[2] += math.cos(yaw_rad) * self.camera["speed"]
        self.update_camera()
    
    def move_right(self):
        """向右移动"""
        yaw_rad = math.radians(self.camera["yaw"])
        self.player_pos[0] += math.sin(yaw_rad) * self.camera["speed"]
        self.player_pos[2] -= math.cos(yaw_rad) * self.camera["speed"]
        self.update_camera()
    
    def place_block(self):
        """放置方块（类似MC左键）"""
        yaw_rad = math.radians(self.camera["yaw"])
        pitch_rad = math.radians(self.camera["pitch"])
        
        distance = 5.0
        target_x = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * distance
        target_y = self.player_pos[1] + 1.5 + math.sin(pitch_rad) * distance
        target_z = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * distance
        
        block_x = int(target_x)
        block_y = int(target_y)
        block_z = int(target_z)
        
        selected_block = self.hotbar[self.hotbar_selected]
        if selected_block:
            self.placed_blocks.append({
                "x": block_x,
                "y": block_y,
                "z": block_z,
                "type": selected_block
            })
            self.message = f"放置 {selected_block} 在 ({block_x}, {block_y}, {block_z})"
            self.message_timer = 1000
    
    def break_block(self):
        """破坏方块（类似MC右键）"""
        yaw_rad = math.radians(self.camera["yaw"])
        pitch_rad = math.radians(self.camera["pitch"])
        
        distance = 5.0
        target_x = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * distance
        target_y = self.player_pos[1] + 1.5 + math.sin(pitch_rad) * distance
        target_z = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * distance
        
        block_x = int(target_x)
        block_y = int(target_y)
        block_z = int(target_z)
        
        for i, block in enumerate(self.placed_blocks):
            if block["x"] == block_x and block["y"] == block_y and block["z"] == block_z:
                removed_block = self.placed_blocks.pop(i)
                self.message = f"破坏 {removed_block['type']}"
                self.message_timer = 1000
                return
        
        self.message = "没有可破坏的方块"
        self.message_timer = 1000
    
    def update_camera(self):
        """更新相机位置（MC风格三种视角）"""
        yaw_rad = math.radians(self.camera["yaw"])
        pitch_rad = math.radians(self.camera["pitch"])
        distance = 5.0
        
        if self.camera["mode"] == "first":
            # 第一人称视角：相机位置与玩家位置相同
            distance = 0.5
            self.camera["x"] = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 1.5 + math.sin(pitch_rad) * distance
            self.camera["z"] = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * distance
        elif self.camera["mode"] == "third_front":
            # 第三人称正面视角：相机位于玩家前方
            self.camera["x"] = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 2.0 - math.sin(pitch_rad) * distance
            self.camera["z"] = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * distance
        else:
            # 第三人称背面视角：相机位于玩家背后（默认）
            self.camera["x"] = self.player_pos[0] - math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 2.0 - math.sin(pitch_rad) * distance
            self.camera["z"] = self.player_pos[2] - math.sin(yaw_rad) * math.cos(pitch_rad) * distance
    
    def move_to_mouse(self):
        """移动到鼠标点击位置"""
        # 这里需要实现射线检测，简化处理
        mx, my = pygame.mouse.get_pos()
        # 简单的直线移动
        self.follow_target = {"x": self.player_pos[0] + (mx - SCREEN_WIDTH//2) * 0.1, "y": self.player_pos[2] + (my - SCREEN_HEIGHT//2) * 0.1}
        self.message = "移动到指定位置"
        self.message_timer = 2000
    
    def update_followers(self):
        """更新跟随者"""
        if self.follow_target:
            for follower in self.followers:
                dx = self.follow_target["x"] - follower["x"]
                dz = self.follow_target["y"] - follower["z"]
                distance = math.hypot(dx, dz)
                if distance > 1:
                    follower["x"] += dx / distance * 0.3
                    follower["z"] += dz / distance * 0.3
    
    def draw_3d_scene(self):
        """绘制3D场景"""
        if cpp_renderer_available:
            self.draw_3d_scene_cpp()
        else:
            self.draw_3d_scene_python()
    
    def draw_3d_scene_cpp(self):
        """使用C++渲染器绘制3D场景"""
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(60, SCREEN_WIDTH / SCREEN_HEIGHT, 0.1, 1000.0)
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            yaw_rad = math.radians(self.camera["yaw"])
            pitch_rad = math.radians(self.camera["pitch"])
            
            look_distance = 10
            look_x = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * look_distance
            look_y = self.player_pos[1] + 1.5 + math.sin(pitch_rad) * look_distance
            look_z = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * look_distance
            
            gluLookAt(
                self.camera["x"], self.camera["y"], self.camera["z"],
                look_x, look_y, look_z,
                0, 1, 0
            )
            
            renderer.render_terrain(
                self.player_pos[0], self.player_pos[1], self.player_pos[2],
                50, 4, -1
            )
            
            if hasattr(self, 'trees'):
                tree_data = []
                for tree_x, tree_z in self.trees:
                    tree_data.append(TreeData(x=tree_x, z=tree_z, base_height=3, height=4, width=2))
                renderer.render_trees(tree_data)
            
            loc_data = []
            for loc in self.locations:
                r, g, b = 1.0, 0.8, 0.2
                loc_data.append(LocationData(x=loc["x"], z=loc["y"], r=r, g=g, b=b, type=0))
            renderer.render_locations(loc_data)
            
            if self.camera["mode"] == "third":
                player = PlayerData(
                    x=self.player_pos[0], y=self.player_pos[1], z=self.player_pos[2],
                    r=0.3, g=0.5, b=0.8, rotation=self.camera["yaw"]
                )
                renderer.render_player(player)
            
            follower_data = []
            for follower in self.followers:
                follower_data.append(FollowerData(
                    x=follower["x"], y=follower["y"], z=follower["z"],
                    r=0.4, g=0.6, b=0.3, type=0
                ))
            renderer.render_followers(follower_data)
            
            pygame.display.flip()
        except Exception as e:
            logger.info(f"C++渲染错误: {e}")
            self.draw_3d_scene_python()
    
    def draw_3d_scene_python(self):
        """使用Python绘制3D场景"""
        try:
            sky_color = self.get_sky_color()
            glClearColor(sky_color[0], sky_color[1], sky_color[2], 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(60, SCREEN_WIDTH / SCREEN_HEIGHT, 0.1, 1000.0)
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            yaw_rad = math.radians(self.camera["yaw"])
            pitch_rad = math.radians(self.camera["pitch"])
            
            look_distance = 10
            look_x = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * look_distance
            look_y = self.player_pos[1] + 1.5 + math.sin(pitch_rad) * look_distance
            look_z = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * look_distance
            
            gluLookAt(
                self.camera["x"], self.camera["y"], self.camera["z"],
                look_x, look_y, look_z,
                0, 1, 0
            )
            
            self.draw_sun_moon()
            
            self.draw_terrain()
            self.draw_placed_blocks()
            
            if hasattr(self, 'trees'):
                for tree_x, tree_z in self.trees:
                    self.draw_tree(tree_x, tree_z)
            
            for loc in self.locations:
                self.draw_location(loc)
            
            self.draw_entities()
            
            if self.camera["mode"] == "third":
                self.draw_player()
            
            for follower in self.followers:
                self.draw_follower(follower)
            
            # 绘制粒子效果
            self.draw_effect_particles()
            self.draw_dust_particles()
            
            # 绘制海浪和天气
            self.draw_waves()
            self.draw_weather()
            
            pygame.display.flip()
        except Exception as e:
            logger.info(f"Python渲染错误: {e}")
    
    def draw_terrain(self):
        """绘制像素化地形 - 类似我的世界风格"""
        try:
            glDisable(GL_LIGHTING)
            
            block_size = 4
            height = -1
            
            for x in range(-2000, 2000, block_size):
                for z in range(-2000, 2000, block_size):
                    noise = math.sin(x * 0.01) * math.cos(z * 0.01) * 2
                    block_y = height + noise
                    
                    glColor3f(0.2, 0.5, 0.2)
                    glBegin(GL_QUADS)
                    glVertex3f(x, block_y, z)
                    glVertex3f(x + block_size, block_y, z)
                    glVertex3f(x + block_size, block_y, z + block_size)
                    glVertex3f(x, block_y, z + block_size)
                    glEnd()
                    
                    glColor3f(0.15, 0.35, 0.15)
                    glBegin(GL_QUADS)
                    glVertex3f(x, block_y - block_size/2, z)
                    glVertex3f(x + block_size, block_y - block_size/2, z)
                    glVertex3f(x + block_size, block_y - block_size/2, z + block_size)
                    glVertex3f(x, block_y - block_size/2, z + block_size)
                    glEnd()
            
            grass_colors = [
                (0.25, 0.55, 0.25),
                (0.2, 0.5, 0.2),
                (0.3, 0.6, 0.3),
                (0.22, 0.52, 0.22)
            ]
            
            for x in range(-2000, 2000, block_size):
                for z in range(-2000, 2000, block_size):
                    noise = math.sin(x * 0.01) * math.cos(z * 0.01) * 2
                    block_y = height + noise
                    
                    color = grass_colors[((x // block_size) + (z // block_size)) % len(grass_colors)]
                    glColor3f(*color)
                    glBegin(GL_QUADS)
                    glVertex3f(x, block_y, z)
                    glVertex3f(x + block_size, block_y, z)
                    glVertex3f(x + block_size, block_y, z + block_size)
                    glVertex3f(x, block_y, z + block_size)
                    glEnd()
                    
                    glColor3f(0.4, 0.25, 0.15)
                    glBegin(GL_QUADS)
                    glVertex3f(x, block_y - block_size/2, z)
                    glVertex3f(x + block_size, block_y - block_size/2, z)
                    glVertex3f(x + block_size, block_y - block_size/2, z + block_size)
                    glVertex3f(x, block_y - block_size/2, z + block_size)
                    glEnd()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"绘制地形错误: {e}")
    
    def draw_placed_blocks(self):
        """绘制玩家放置的方块 - MC风格"""
        try:
            glDisable(GL_LIGHTING)
            
            block_size = 1
            
            for block in self.placed_blocks:
                x = block.get("x", 0)
                y = block.get("y", 0)
                z = block.get("z", 0)
                block_type = block.get("type", "泥土")
                
                color = self.block_colors.get(block_type, (0.5, 0.5, 0.5))
                
                glPushMatrix()
                glTranslatef(x, y, z)
                
                if len(color) == 4:
                    glColor4f(*color)
                    if color[3] < 1.0:
                        glEnable(GL_BLEND)
                        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                else:
                    glColor3f(*color)
                
                # 绘制方块六个面
                # 顶面
                glBegin(GL_QUADS)
                glVertex3f(0, block_size, 0)
                glVertex3f(block_size, block_size, 0)
                glVertex3f(block_size, block_size, block_size)
                glVertex3f(0, block_size, block_size)
                glEnd()
                
                # 底面
                glBegin(GL_QUADS)
                glVertex3f(0, 0, 0)
                glVertex3f(0, 0, block_size)
                glVertex3f(block_size, 0, block_size)
                glVertex3f(block_size, 0, 0)
                glEnd()
                
                # 前面
                glBegin(GL_QUADS)
                glVertex3f(0, 0, block_size)
                glVertex3f(0, block_size, block_size)
                glVertex3f(block_size, block_size, block_size)
                glVertex3f(block_size, 0, block_size)
                glEnd()
                
                # 后面
                glBegin(GL_QUADS)
                glVertex3f(0, 0, 0)
                glVertex3f(block_size, 0, 0)
                glVertex3f(block_size, block_size, 0)
                glVertex3f(0, block_size, 0)
                glEnd()
                
                # 左面
                glBegin(GL_QUADS)
                glVertex3f(0, 0, 0)
                glVertex3f(0, block_size, 0)
                glVertex3f(0, block_size, block_size)
                glVertex3f(0, 0, block_size)
                glEnd()
                
                # 右面
                glBegin(GL_QUADS)
                glVertex3f(block_size, 0, 0)
                glVertex3f(block_size, 0, block_size)
                glVertex3f(block_size, block_size, block_size)
                glVertex3f(block_size, block_size, 0)
                glEnd()
                
                glPopMatrix()
                
                if len(color) == 4 and color[3] < 1.0:
                    glDisable(GL_BLEND)
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"绘制放置方块错误: {e}")
    
    def update_day_night(self):
        """更新昼夜系统"""
        self.day_time += self.day_speed
        if self.day_time >= 24000:
            self.day_time = 0
        
        self.is_day = self.day_time < 12000
        
        if self.is_day:
            self.sun_angle = (self.day_time / 12000) * math.pi - math.pi/2
            self.moon_angle = -math.pi/2
        else:
            self.sun_angle = -math.pi/2
            self.moon_angle = ((self.day_time - 12000) / 12000) * math.pi - math.pi/2
    
    def get_time_of_day(self):
        """获取当前时间段"""
        if self.day_time < 2000:
            return "日出"
        elif self.day_time < 6000:
            return "上午"
        elif self.day_time < 10000:
            return "中午"
        elif self.day_time < 12000:
            return "日落"
        elif self.day_time < 14000:
            return "黄昏"
        elif self.day_time < 22000:
            return "夜晚"
        else:
            return "午夜"
    
    def get_sky_color(self):
        """根据时间获取天空颜色"""
        try:
            if self.is_day:
                t = self.day_time / 12000
                if t < 0.2:
                    return (0.3 + t * 0.5, 0.4 + t * 0.4, 0.8 + t * 0.2)
                elif t > 0.8:
                    t2 = (t - 0.8) * 5
                    return (0.8 - t2 * 0.5, 0.8 - t2 * 0.4, 1.0 - t2 * 0.2)
                else:
                    return (0.8, 0.8, 1.0)
            else:
                t = (self.day_time - 12000) / 12000
                if t < 0.2:
                    return (0.2 - t * 0.15, 0.25 - t * 0.15, 0.4 - t * 0.2)
                elif t > 0.8:
                    t2 = (t - 0.8) * 5
                    return (0.05 + t2 * 0.25, 0.1 + t2 * 0.15, 0.2 + t2 * 0.2)
                else:
                    return (0.05, 0.1, 0.2)
        except Exception as e:
            logger.info(f"[错误] 获取天空颜色失败: {e}")
            return (0.5, 0.7, 1.0)  # 默认天空颜色
    
    def draw_sun_moon(self):
        """绘制太阳和月亮"""
        try:
            glDisable(GL_LIGHTING)
            glPushMatrix()
            
            sun_radius = 50
            moon_radius = 45
            
            if self.is_day:
                glColor3f(1.0, 1.0, 0.8)
                x = math.cos(self.sun_angle) * 500
                y = math.sin(self.sun_angle) * 300 + 100
                z = 0
                
                glTranslatef(self.player_pos[0] + x, y, self.player_pos[2] + z)
                glBegin(GL_QUADS)
                for i in range(36):
                    angle = i * 10 * math.pi / 180
                    glVertex3f(sun_radius * math.cos(angle), sun_radius * math.sin(angle), 0)
                    glVertex3f(sun_radius * math.cos((i+1)*10*math.pi/180), sun_radius * math.sin((i+1)*10*math.pi/180), 0)
                glEnd()
            else:
                glColor3f(0.9, 0.9, 1.0)
                x = math.cos(self.moon_angle) * 500
                y = math.sin(self.moon_angle) * 300 + 100
                z = 0
                
                glTranslatef(self.player_pos[0] + x, y, self.player_pos[2] + z)
                glBegin(GL_QUADS)
                for i in range(36):
                    angle = i * 10 * math.pi / 180
                    glVertex3f(moon_radius * math.cos(angle), moon_radius * math.sin(angle), 0)
                    glVertex3f(moon_radius * math.cos((i+1)*10*math.pi/180), moon_radius * math.sin((i+1)*10*math.pi/180), 0)
                glEnd()
            
            glPopMatrix()
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"绘制太阳月亮错误: {e}")
    
    def update_weather(self):
        """更新天气系统"""
        try:
            self.weather_timer += 1
            
            if self.weather_timer > 3000:
                self.weather_timer = 0
                rand = random.random()
                if rand < 0.2:
                    self.weather = "rain"
                elif rand < 0.3:
                    self.weather = "snow"
                elif rand < 0.35:
                    self.weather = "thunder"
                else:
                    self.weather = "clear"
            
            # 雷暴闪电
            if self.weather == "thunder":
                self.thunder_timer += 1
                if self.thunder_timer > 200:
                    self.is_thundering = random.random() < 0.3
                    self.thunder_timer = 0
                    if self.is_thundering:
                        self.add_chat_message("⚡ 闪电！")
            
            if self.weather == "rain":
                for _ in range(5):
                    if len(self.rain_particles) < 500:
                        particle = {
                            "x": random.uniform(self.player_pos[0] - 100, self.player_pos[0] + 100),
                            "y": 50 + random.uniform(0, 20),
                            "z": random.uniform(self.player_pos[2] - 100, self.player_pos[2] + 100),
                            "speed": random.uniform(8, 12)
                        }
                        self.rain_particles.append(particle)
                
                self.rain_particles = [p for p in self.rain_particles if p.get("y", -10) > -5]
                for p in self.rain_particles:
                    p["y"] = p.get("y", 0) - p.get("speed", 10) * 0.1
                    p["x"] = p.get("x", 0) + 0.5
            
            elif self.weather == "snow":
                for _ in range(3):
                    if len(self.snow_particles) < 300:
                        particle = {
                            "x": random.uniform(self.player_pos[0] - 100, self.player_pos[0] + 100),
                            "y": 50 + random.uniform(0, 20),
                            "z": random.uniform(self.player_pos[2] - 100, self.player_pos[2] + 100),
                            "speed": random.uniform(2, 4),
                            "drift_x": random.uniform(-1, 1),
                            "drift_z": random.uniform(-1, 1)
                        }
                        self.snow_particles.append(particle)
                
                self.snow_particles = [p for p in self.snow_particles if p.get("y", -10) > -5]
                for p in self.snow_particles:
                    p["y"] = p.get("y", 0) - p.get("speed", 3) * 0.05
                    p["x"] = p.get("x", 0) + p.get("drift_x", 0) * 0.1
                    p["z"] = p.get("z", 0) + p.get("drift_z", 0) * 0.1
        except Exception as e:
            logger.info(f"更新天气错误: {e}")
    
    def draw_weather(self):
        """绘制天气效果"""
        try:
            glDisable(GL_LIGHTING)
            
            if self.weather == "rain":
                glColor4f(0.6, 0.7, 0.8, 0.5)
                glBegin(GL_LINES)
                for p in self.rain_particles:
                    glVertex3f(p["x"], p["y"], p["z"])
                    glVertex3f(p["x"] + 2, p["y"] - 10, p["z"])
                glEnd()
            
            elif self.weather == "snow":
                glColor4f(1.0, 1.0, 1.0, 0.8)
                glBegin(GL_QUADS)
                for p in self.snow_particles:
                    size = 3
                    glVertex3f(p["x"] - size, p["y"], p["z"] - size)
                    glVertex3f(p["x"] + size, p["y"], p["z"] - size)
                    glVertex3f(p["x"] + size, p["y"], p["z"] + size)
                    glVertex3f(p["x"] - size, p["y"], p["z"] + size)
                glEnd()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"绘制天气错误: {e}")
    
    def spawn_effect_particle(self, x, y, z, effect_type="explosion"):
        """生成特效粒子"""
        try:
            colors = {
                "explosion": [(1.0, 0.5, 0.0), (1.0, 0.2, 0.0), (1.0, 1.0, 0.0)],
                "enchant": [(0.5, 0.0, 1.0), (0.0, 0.5, 1.0), (1.0, 0.0, 1.0)],
                "heal": [(0.0, 1.0, 0.0), (0.5, 1.0, 0.5), (0.0, 0.8, 0.0)],
                "magic": [(0.8, 0.0, 0.8), (0.0, 0.8, 0.8), (0.8, 0.8, 0.0)],
                "fire": [(1.0, 0.3, 0.0), (1.0, 0.5, 0.0), (0.8, 0.0, 0.0)]
            }
            
            color = random.choice(colors.get(effect_type, colors["explosion"]))
            
            for _ in range(20):
                particle = {
                    "x": x + random.uniform(-1, 1),
                    "y": y + random.uniform(0, 2),
                    "z": z + random.uniform(-1, 1),
                    "vx": random.uniform(-0.5, 0.5),
                    "vy": random.uniform(0.5, 2.0),
                    "vz": random.uniform(-0.5, 0.5),
                    "life": 60,
                    "max_life": 60,
                    "color": color,
                    "size": random.uniform(0.1, 0.3)
                }
                self.effect_particles.append(particle)
        except Exception as e:
            logger.info(f"[错误] 生成特效粒子失败: {e}")
    
    def spawn_dust_particle(self, x, y, z):
        """生成尘埃粒子"""
        try:
            for _ in range(10):
                particle = {
                    "x": x + random.uniform(-0.5, 0.5),
                    "y": y + random.uniform(0, 1),
                    "z": z + random.uniform(-0.5, 0.5),
                    "vx": random.uniform(-0.1, 0.1),
                    "vy": random.uniform(0.1, 0.3),
                    "vz": random.uniform(-0.1, 0.1),
                    "life": 30,
                    "max_life": 30,
                    "size": random.uniform(0.05, 0.15)
                }
                self.dust_particles.append(particle)
        except Exception as e:
            logger.info(f"[错误] 生成尘埃粒子失败: {e}")
    
    def update_effect_particles(self):
        """更新特效粒子"""
        try:
            for particle in self.effect_particles:
                particle["x"] += particle["vx"]
                particle["y"] += particle["vy"]
                particle["z"] += particle["vz"]
                particle["vy"] -= 0.05  # 重力
                particle["life"] -= 1
            self.effect_particles[:] = [particle for particle in self.effect_particles if particle["life"] > 0]
        except Exception as e:
            logger.info(f"[错误] 更新特效粒子失败: {e}")
    
    def update_dust_particles(self):
        """更新尘埃粒子"""
        try:
            for particle in self.dust_particles:
                particle["x"] += particle["vx"]
                particle["y"] += particle["vy"]
                particle["z"] += particle["vz"]
                particle["life"] -= 1
            self.dust_particles[:] = [particle for particle in self.dust_particles if particle["life"] > 0]
        except Exception as e:
            logger.info(f"[错误] 更新尘埃粒子失败: {e}")
    
    def draw_effect_particles(self):
        """绘制特效粒子"""
        try:
            glDisable(GL_LIGHTING)
            glPointSize(3.0)
            
            glBegin(GL_POINTS)
            for particle in self.effect_particles:
                alpha = particle["life"] / particle["max_life"]
                glColor4f(particle["color"][0], particle["color"][1], particle["color"][2], alpha)
                glVertex3f(particle["x"], particle["y"], particle["z"])
            glEnd()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"[错误] 绘制特效粒子失败: {e}")
    
    def draw_dust_particles(self):
        """绘制尘埃粒子"""
        try:
            glDisable(GL_LIGHTING)
            glPointSize(2.0)
            
            glBegin(GL_POINTS)
            for particle in self.dust_particles:
                alpha = particle["life"] / particle["max_life"]
                glColor4f(0.8, 0.7, 0.6, alpha * 0.5)
                glVertex3f(particle["x"], particle["y"], particle["z"])
            glEnd()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"[错误] 绘制尘埃粒子失败: {e}")
    
    def spawn_entity(self):
        """生成生物"""
        self.spawn_timer += 1
        
        if self.spawn_timer > 60:
            self.spawn_timer = 0
            
            if random.random() < 0.1:
                entity_type = random.choice(["猪", "牛", "羊", "鸡"]) if self.is_day else random.choice(["僵尸", "骷髅", "苦力怕"])
                
                entity = {
                    "type": entity_type,
                    "x": self.player_pos[0] + random.uniform(-50, 50),
                    "y": 0,
                    "z": self.player_pos[2] + random.uniform(-50, 50),
                    "health": 20,
                    "max_health": 20,
                    "speed": random.uniform(0.1, 0.3),
                    "direction": random.uniform(0, 360),
                    "texture": entity_type
                }
                
                if entity_type in ["僵尸", "骷髅", "苦力怕"]:
                    self.monsters.append(entity)
                else:
                    self.animals.append(entity)
    
    def update_entities(self):
        """更新生物位置"""
        for animal in self.animals:
            animal["direction"] += random.uniform(-5, 5)
            animal["x"] += math.cos(math.radians(animal["direction"])) * animal["speed"]
            animal["z"] += math.sin(math.radians(animal["direction"])) * animal["speed"]
        self.animals[:] = [animal for animal in self.animals if self.player_pos[0] - 100 <= animal["x"] <= self.player_pos[0] + 100]
        
        for monster in self.monsters:
            dx = self.player_pos[0] - monster["x"]
            dz = self.player_pos[2] - monster["z"]
            monster["direction"] = math.degrees(math.atan2(dz, dx))
            monster["x"] += math.cos(math.radians(monster["direction"])) * monster["speed"]
            monster["z"] += math.sin(math.radians(monster["direction"])) * monster["speed"]
        self.monsters[:] = [monster for monster in self.monsters if self.player_pos[0] - 100 <= monster["x"] <= self.player_pos[0] + 100]
    
    def draw_entities(self):
        """绘制生物"""
        try:
            glDisable(GL_LIGHTING)
            
            for animal in self.animals:
                glPushMatrix()
                glTranslatef(animal["x"], animal["y"], animal["z"])
                
                color = {"猪": (0.9, 0.6, 0.6), "牛": (0.6, 0.4, 0.2), "羊": (0.9, 0.9, 0.9), "鸡": (0.9, 0.8, 0.6)}[animal["type"]]
                glColor3f(*color)
                
                size = 0.8
                glBegin(GL_QUADS)
                glVertex3f(-size, 0, -size)
                glVertex3f(size, 0, -size)
                glVertex3f(size, size * 1.5, -size)
                glVertex3f(-size, size * 1.5, -size)
                glEnd()
                
                glPopMatrix()
            
            for monster in self.monsters:
                glPushMatrix()
                glTranslatef(monster["x"], monster["y"], monster["z"])
                
                color = {"僵尸": (0.3, 0.6, 0.3), "骷髅": (0.8, 0.8, 0.8), "苦力怕": (0.2, 0.8, 0.2)}[monster["type"]]
                glColor3f(*color)
                
                size = 0.8
                glBegin(GL_QUADS)
                glVertex3f(-size, 0, -size)
                glVertex3f(size, 0, -size)
                glVertex3f(size, size * 2, -size)
                glVertex3f(-size, size * 2, -size)
                glEnd()
                
                glPopMatrix()
            
            if self.herobrine_active and self.herobrine_pos:
                self.draw_herobrine()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"绘制实体错误: {e}")
    
    def draw_herobrine(self):
        """绘制Herobrine（彩蛋）"""
        if not self.herobrine_active or not self.herobrine_pos:
            return
        
        glPushMatrix()
        glTranslatef(self.herobrine_pos[0], self.herobrine_pos[1], self.herobrine_pos[2])
        
        glColor3f(1.0, 1.0, 1.0)
        
        size = 0.6
        glBegin(GL_QUADS)
        
        glVertex3f(-size, 0, -size)
        glVertex3f(size, 0, -size)
        glVertex3f(size, size * 2.5, -size)
        glVertex3f(-size, size * 2.5, -size)
        glEnd()
        
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_QUADS)
        glVertex3f(-size * 0.8, size * 1.8, -size * 0.6)
        glVertex3f(size * 0.8, size * 1.8, -size * 0.6)
        glVertex3f(size * 0.8, size * 2.5, -size * 0.6)
        glVertex3f(-size * 0.8, size * 2.5, -size * 0.6)
        glEnd()
        
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex3f(-size * 0.3, size * 2.1, -size * 0.55)
        glVertex3f(-size * 0.1, size * 2.1, -size * 0.55)
        glVertex3f(-size * 0.1, size * 2.3, -size * 0.55)
        glVertex3f(-size * 0.3, size * 2.3, -size * 0.55)
        glEnd()
        
        glBegin(GL_QUADS)
        glVertex3f(size * 0.1, size * 2.1, -size * 0.55)
        glVertex3f(size * 0.3, size * 2.1, -size * 0.55)
        glVertex3f(size * 0.3, size * 2.3, -size * 0.55)
        glVertex3f(size * 0.1, size * 2.3, -size * 0.55)
        glEnd()
        
        glPopMatrix()
    
    def update_herobrine(self):
        """更新Herobrine行为（彩蛋）"""
        if not self.herobrine_active or not self.herobrine_pos:
            return
        
        self.herobrine_timer += 1
        
        if self.herobrine_timer > 300:
            self.herobrine_active = False
            self.herobrine_pos = None
            self.herobrine_timer = 0
            self.add_chat_message("Herobrine消失了...")
            return
        
        dx = self.player_pos[0] - self.herobrine_pos[0]
        dz = self.player_pos[2] - self.herobrine_pos[2]
        distance = math.hypot(dx, dz)
        
        if distance < 3:
            self.health -= 1
            if self.health <= 0:
                self.add_chat_message("你被Herobrine杀死了!")
        
        if random.random() < 0.02:
            self.herobrine_pos[0] += (random.random() - 0.5) * 2
            self.herobrine_pos[2] += (random.random() - 0.5) * 2
    
    def update_waves(self):
        """更新海浪效果"""
        self.wave_timer += 1
        
        if self.wave_timer > 5:
            self.wave_timer = 0
            
            for _ in range(20):
                if len(self.wave_particles) < 1000:
                    angle = random.uniform(0, math.pi * 2)
                    distance = random.uniform(50, 150)
                    self.wave_particles.append({
                        "x": self.player_pos[0] + math.cos(angle) * distance,
                        "y": 0.1,
                        "z": self.player_pos[2] + math.sin(angle) * distance,
                        "amplitude": random.uniform(0.1, 0.3),
                        "frequency": random.uniform(0.05, 0.1),
                        "phase": random.uniform(0, math.pi * 2),
                        "speed": random.uniform(0.02, 0.05)
                    })
        
        for wave in self.wave_particles:
            wave["y"] = 0.1 + wave["amplitude"] * math.sin(self.wave_timer * wave["frequency"] + wave["phase"])
            wave["x"] += wave["speed"] * math.cos(wave["phase"])
            wave["z"] += wave["speed"] * math.sin(wave["phase"])
        self.wave_particles[:] = [wave for wave in self.wave_particles if math.hypot(wave["x"] - self.player_pos[0], wave["z"] - self.player_pos[2]) <= 200]
    
    def draw_waves(self):
        """绘制海浪效果"""
        try:
            glDisable(GL_LIGHTING)
            
            for wave in self.wave_particles:
                glPushMatrix()
                glTranslatef(wave["x"], wave["y"], wave["z"])
                
                glColor4f(0.2, 0.5, 0.8, 0.6)
                
                size = 2
                glBegin(GL_QUADS)
                glVertex3f(-size, 0, -size)
                glVertex3f(size, 0, -size)
                glVertex3f(size, 0.1, size)
                glVertex3f(-size, 0.1, size)
                glEnd()
                
                glPopMatrix()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"绘制海浪错误: {e}")
    
    def draw_tree(self, x, z):
        """绘制树木"""
        try:
            glDisable(GL_LIGHTING)
            
            glPushMatrix()
            glTranslatef(x, -1, z)
            
            trunk_height = 3
            trunk_width = 0.3
            
            glColor3f(0.4, 0.25, 0.1)
            glBegin(GL_QUADS)
            glVertex3f(-trunk_width, 0, -trunk_width)
            glVertex3f(trunk_width, 0, -trunk_width)
            glVertex3f(trunk_width, trunk_height, -trunk_width)
            glVertex3f(-trunk_width, trunk_height, -trunk_width)
            
            glVertex3f(trunk_width, 0, -trunk_width)
            glVertex3f(trunk_width, 0, trunk_width)
            glVertex3f(trunk_width, trunk_height, trunk_width)
            glVertex3f(trunk_width, trunk_height, -trunk_width)
            
            glVertex3f(trunk_width, 0, trunk_width)
            glVertex3f(-trunk_width, 0, trunk_width)
            glVertex3f(-trunk_width, trunk_height, trunk_width)
            glVertex3f(trunk_width, trunk_height, trunk_width)
            
            glVertex3f(-trunk_width, 0, trunk_width)
            glVertex3f(-trunk_width, 0, -trunk_width)
            glVertex3f(-trunk_width, trunk_height, -trunk_width)
            glVertex3f(-trunk_width, trunk_height, trunk_width)
            glEnd()
            
            leaves_base = trunk_height + 0.5
            leaf_colors = [(0.2, 0.6, 0.2), (0.15, 0.55, 0.15), (0.25, 0.65, 0.25)]
            
            for layer, layer_height in enumerate([1.5, 1.2, 0.8]):
                y = leaves_base + layer * 0.8
                size = 2.0 - layer * 0.4
                color = leaf_colors[layer % len(leaf_colors)]
                glColor3f(*color)
                
                glBegin(GL_QUADS)
                glVertex3f(-size, y, -size)
                glVertex3f(size, y, -size)
                glVertex3f(size, y + layer_height, -size)
                glVertex3f(-size, y + layer_height, -size)
                
                glVertex3f(size, y, -size)
                glVertex3f(size, y, size)
                glVertex3f(size, y + layer_height, size)
                glVertex3f(size, y + layer_height, -size)
                
                glVertex3f(size, y, size)
                glVertex3f(-size, y, size)
                glVertex3f(-size, y + layer_height, size)
                glVertex3f(size, y + layer_height, size)
                
                glVertex3f(-size, y, size)
                glVertex3f(-size, y, -size)
                glVertex3f(-size, y + layer_height, -size)
                glVertex3f(-size, y + layer_height, size)
                glEnd()
                
                glColor3f(*[c * 0.8 for c in color])
                glBegin(GL_QUADS)
                glVertex3f(-size, y + layer_height, -size)
                glVertex3f(size, y + layer_height, -size)
                glVertex3f(size * 0.7, y + layer_height + 0.5, 0)
                glVertex3f(-size * 0.7, y + layer_height + 0.5, 0)
                glEnd()
            
            glPopMatrix()
            glEnable(GL_LIGHTING)
        except Exception as e:
            logger.info(f"绘制树木错误: {e}")
    
    def draw_location(self, loc):
        """绘制地点 - 优化版，增加高度和细节"""
        try:
            x, z = loc["x"], loc["y"]
            loc_type = loc.get("type", "村庄")
            
            glPushMatrix()
            glTranslatef(x, 0, z)
            
            glDisable(GL_LIGHTING)
            
            base_width = 12
            base_depth = 12
            base_height = 2
            
            glColor3f(0.5, 0.4, 0.3)
            self.draw_cube(base_width, base_height, base_depth)
            
            wall_thickness = 0.5
            wall_height = 12
            
            if loc_type == "关隘":
                wall_color = (0.6, 0.55, 0.5)
                wall_height = 18
            elif loc_type == "军营":
                wall_color = (0.7, 0.2, 0.2)
                wall_height = 15
            elif loc_type == "村庄":
                wall_color = (0.85, 0.75, 0.55)
                wall_height = 10
            elif loc_type == "矿山":
                wall_color = (0.5, 0.5, 0.45)
                wall_height = 8
            elif loc_type == "港口":
                wall_color = (0.25, 0.55, 0.75)
                wall_height = 10
            else:
                wall_color = (0.6, 0.5, 0.4)
                wall_height = 12
            
            glColor3f(wall_color)
            
            glBegin(GL_QUADS)
            glVertex3f(-base_width/2, base_height, -base_depth/2)
            glVertex3f(base_width/2, base_height, -base_depth/2)
            glVertex3f(base_width/2, base_height + wall_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height + wall_height, -base_depth/2)
            
            glVertex3f(base_width/2, base_height, -base_depth/2)
            glVertex3f(base_width/2, base_height, base_depth/2)
            glVertex3f(base_width/2, base_height + wall_height, base_depth/2)
            glVertex3f(base_width/2, base_height + wall_height, -base_depth/2)
            
            glVertex3f(base_width/2, base_height, base_depth/2)
            glVertex3f(-base_width/2, base_height, base_depth/2)
            glVertex3f(-base_width/2, base_height + wall_height, base_depth/2)
            glVertex3f(base_width/2, base_height + wall_height, base_depth/2)
            
            glVertex3f(-base_width/2, base_height, base_depth/2)
            glVertex3f(-base_width/2, base_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height + wall_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height + wall_height, base_depth/2)
            glEnd()
            
            roof_height = 3
            glColor3f(*[c * 0.8 for c in wall_color])
            glBegin(GL_QUADS)
            glVertex3f(-base_width/2 - 1, base_height + wall_height, -base_depth/2 - 1)
            glVertex3f(base_width/2 + 1, base_height + wall_height, -base_depth/2 - 1)
            glVertex3f(base_width/2 + 1, base_height + wall_height, base_depth/2 + 1)
            glVertex3f(-base_width/2 - 1, base_height + wall_height, base_depth/2 + 1)
            
            glVertex3f(-base_width/2 - 1, base_height + wall_height, -base_depth/2 - 1)
            glVertex3f(-base_width/2 - 1, base_height + wall_height, base_depth/2 + 1)
            glVertex3f(0, base_height + wall_height + roof_height, 0)
            
            glVertex3f(base_width/2 + 1, base_height + wall_height, -base_depth/2 - 1)
            glVertex3f(base_width/2 + 1, base_height + wall_height, base_depth/2 + 1)
            glVertex3f(0, base_height + wall_height + roof_height, 0)
            
            glVertex3f(base_width/2 + 1, base_height + wall_height, base_depth/2 + 1)
            glVertex3f(-base_width/2 - 1, base_height + wall_height, base_depth/2 + 1)
            glVertex3f(0, base_height + wall_height + roof_height, 0)
            
            glVertex3f(-base_width/2 - 1, base_height + wall_height, -base_depth/2 - 1)
            glVertex3f(-base_width/2 - 1, base_height + wall_height, base_depth/2 + 1)
            glVertex3f(0, base_height + wall_height + roof_height, 0)
            
            glVertex3f(-base_width/2 - 1, base_height + wall_height, -base_depth/2 - 1)
            glVertex3f(base_width/2 + 1, base_height + wall_height, -base_depth/2 - 1)
            glVertex3f(0, base_height + wall_height + roof_height, 0)
            glEnd()
            
            loc["collision_box"] = {
                "min_x": x - base_width/2,
                "max_x": x + base_width/2,
                "min_y": 0,
                "max_y": base_height + wall_height + roof_height,
                "min_z": z - base_depth/2,
                "max_z": z + base_depth/2
            }
            loc["height"] = base_height + wall_height + roof_height
            loc["enterable"] = True
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            logger.info(f"绘制地点错误: {e}")
    
    def draw_cube(self, width, height, depth):
        """绘制立方体"""
        hw, hh, hd = width/2, height/2, depth/2
        vertices = [
            (-hw, -hh, -hd), (hw, -hh, -hd), (hw, hh, -hd), (-hw, hh, -hd),
            (-hw, -hh, hd), (hw, -hh, hd), (hw, hh, hd), (-hw, hh, hd)
        ]
        faces = [
            (0, 1, 2, 3), (1, 5, 6, 2), (5, 4, 7, 6),
            (4, 0, 3, 7), (3, 2, 6, 7), (4, 5, 1, 0)
        ]
        
        glBegin(GL_QUADS)
        for face in faces:
            for i in face:
                glVertex3f(vertices[i][0], vertices[i][1], vertices[i][2])
        glEnd()
    
    def draw_player(self):
        """绘制玩家 - 带手脚版本"""
        try:
            glPushMatrix()
            player_x, player_y, player_z = self.player_pos[0], self.player_pos[1], self.player_pos[2]
            glTranslatef(player_x, player_y, player_z)
            
            glDisable(GL_LIGHTING)
            
            walk_cycle = math.sin(pygame.time.get_ticks() * 0.01) if self.velocity[0] != 0 or self.velocity[2] != 0 else 0
            arm_swing = walk_cycle * 0.3
            leg_swing = walk_cycle * 0.4
            
            body_width = 0.5
            body_height = 1.0
            body_depth = 0.3
            
            glColor3f(0.2, 0.4, 0.8)
            glBegin(GL_QUADS)
            glVertex3f(-body_width/2, 0.3, -body_depth/2)
            glVertex3f(body_width/2, 0.3, -body_depth/2)
            glVertex3f(body_width/2, 0.3 + body_height, -body_depth/2)
            glVertex3f(-body_width/2, 0.3 + body_height, -body_depth/2)
            
            glVertex3f(body_width/2, 0.3, -body_depth/2)
            glVertex3f(body_width/2, 0.3, body_depth/2)
            glVertex3f(body_width/2, 0.3 + body_height, body_depth/2)
            glVertex3f(body_width/2, 0.3 + body_height, -body_depth/2)
            
            glVertex3f(body_width/2, 0.3, body_depth/2)
            glVertex3f(-body_width/2, 0.3, body_depth/2)
            glVertex3f(-body_width/2, 0.3 + body_height, body_depth/2)
            glVertex3f(body_width/2, 0.3 + body_height, body_depth/2)
            
            glVertex3f(-body_width/2, 0.3, body_depth/2)
            glVertex3f(-body_width/2, 0.3, -body_depth/2)
            glVertex3f(-body_width/2, 0.3 + body_height, -body_depth/2)
            glVertex3f(-body_width/2, 0.3 + body_height, body_depth/2)
            glEnd()
            
            glColor3f(0.8, 0.6, 0.4)
            glPushMatrix()
            glTranslatef(0, 0.85, 0)
            glBegin(GL_QUADS)
            glVertex3f(-0.2, 0, -0.2)
            glVertex3f(0.2, 0, -0.2)
            glVertex3f(0.2, 0.3, -0.2)
            glVertex3f(-0.2, 0.3, -0.2)
            
            glVertex3f(0.2, 0, -0.2)
            glVertex3f(0.2, 0, 0.2)
            glVertex3f(0.2, 0.3, 0.2)
            glVertex3f(0.2, 0.3, -0.2)
            
            glVertex3f(0.2, 0, 0.2)
            glVertex3f(-0.2, 0, 0.2)
            glVertex3f(-0.2, 0.3, 0.2)
            glVertex3f(0.2, 0.3, 0.2)
            
            glVertex3f(-0.2, 0, 0.2)
            glVertex3f(-0.2, 0, -0.2)
            glVertex3f(-0.2, 0.3, -0.2)
            glVertex3f(-0.2, 0.3, 0.2)
            glEnd()
            glPopMatrix()
            
            arm_width = 0.15
            arm_length = 0.6
            
            glColor3f(0.25, 0.45, 0.85)
            glPushMatrix()
            glTranslatef(body_width/2 + arm_width/2, 0.4 + arm_swing, 0)
            glBegin(GL_QUADS)
            glVertex3f(-arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, arm_length, -arm_width/2)
            glVertex3f(-arm_width/2, arm_length, -arm_width/2)
            
            glVertex3f(arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0, arm_width/2)
            glVertex3f(arm_width/2, arm_length, arm_width/2)
            glVertex3f(arm_width/2, arm_length, -arm_width/2)
            
            glVertex3f(arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, arm_length, arm_width/2)
            glVertex3f(arm_width/2, arm_length, arm_width/2)
            
            glVertex3f(-arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0, -arm_width/2)
            glVertex3f(-arm_width/2, arm_length, -arm_width/2)
            glVertex3f(-arm_width/2, arm_length, arm_width/2)
            glEnd()
            
            glColor3f(0.8, 0.6, 0.4)
            glTranslatef(0, arm_length - 0.1, 0)
            glBegin(GL_QUADS)
            glVertex3f(-arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0.2, -arm_width/2)
            glVertex3f(-arm_width/2, 0.2, -arm_width/2)
            
            glVertex3f(arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0, arm_width/2)
            glVertex3f(arm_width/2, 0.2, arm_width/2)
            glVertex3f(arm_width/2, 0.2, -arm_width/2)
            
            glVertex3f(arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0.2, arm_width/2)
            glVertex3f(arm_width/2, 0.2, arm_width/2)
            
            glVertex3f(-arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0, -arm_width/2)
            glVertex3f(-arm_width/2, 0.2, -arm_width/2)
            glVertex3f(-arm_width/2, 0.2, arm_width/2)
            glEnd()
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(-body_width/2 - arm_width/2, 0.4 - arm_swing, 0)
            glColor3f(0.25, 0.45, 0.85)
            glBegin(GL_QUADS)
            glVertex3f(-arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, arm_length, -arm_width/2)
            glVertex3f(-arm_width/2, arm_length, -arm_width/2)
            
            glVertex3f(arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0, arm_width/2)
            glVertex3f(arm_width/2, arm_length, arm_width/2)
            glVertex3f(arm_width/2, arm_length, -arm_width/2)
            
            glVertex3f(arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, arm_length, arm_width/2)
            glVertex3f(arm_width/2, arm_length, arm_width/2)
            
            glVertex3f(-arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0, -arm_width/2)
            glVertex3f(-arm_width/2, arm_length, -arm_width/2)
            glVertex3f(-arm_width/2, arm_length, arm_width/2)
            glEnd()
            
            glColor3f(0.8, 0.6, 0.4)
            glTranslatef(0, arm_length - 0.1, 0)
            glBegin(GL_QUADS)
            glVertex3f(-arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0.2, -arm_width/2)
            glVertex3f(-arm_width/2, 0.2, -arm_width/2)
            
            glVertex3f(arm_width/2, 0, -arm_width/2)
            glVertex3f(arm_width/2, 0, arm_width/2)
            glVertex3f(arm_width/2, 0.2, arm_width/2)
            glVertex3f(arm_width/2, 0.2, -arm_width/2)
            
            glVertex3f(arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0.2, arm_width/2)
            glVertex3f(arm_width/2, 0.2, arm_width/2)
            
            glVertex3f(-arm_width/2, 0, arm_width/2)
            glVertex3f(-arm_width/2, 0, -arm_width/2)
            glVertex3f(-arm_width/2, 0.2, -arm_width/2)
            glVertex3f(-arm_width/2, 0.2, arm_width/2)
            glEnd()
            glPopMatrix()
            
            leg_width = 0.18
            leg_length = 0.7
            
            glColor3f(0.15, 0.35, 0.7)
            glPushMatrix()
            glTranslatef(body_width/4, 0.3 - leg_swing, 0)
            glBegin(GL_QUADS)
            glVertex3f(-leg_width/2, -leg_length, -leg_width/2)
            glVertex3f(leg_width/2, -leg_length, -leg_width/2)
            glVertex3f(leg_width/2, 0, -leg_width/2)
            glVertex3f(-leg_width/2, 0, -leg_width/2)
            
            glVertex3f(leg_width/2, -leg_length, -leg_width/2)
            glVertex3f(leg_width/2, -leg_length, leg_width/2)
            glVertex3f(leg_width/2, 0, leg_width/2)
            glVertex3f(leg_width/2, 0, -leg_width/2)
            
            glVertex3f(leg_width/2, -leg_length, leg_width/2)
            glVertex3f(-leg_width/2, -leg_length, leg_width/2)
            glVertex3f(-leg_width/2, 0, leg_width/2)
            glVertex3f(leg_width/2, 0, leg_width/2)
            
            glVertex3f(-leg_width/2, -leg_length, leg_width/2)
            glVertex3f(-leg_width/2, -leg_length, -leg_width/2)
            glVertex3f(-leg_width/2, 0, -leg_width/2)
            glVertex3f(-leg_width/2, 0, leg_width/2)
            glEnd()
            
            glColor3f(0.3, 0.3, 0.3)
            glTranslatef(0, -leg_length + 0.05, 0.05)
            glBegin(GL_QUADS)
            glVertex3f(-leg_width/2 - 0.05, -0.15, -leg_width/2 - 0.05)
            glVertex3f(leg_width/2 + 0.05, -0.15, -leg_width/2 - 0.05)
            glVertex3f(leg_width/2 + 0.05, 0, -leg_width/2 - 0.05)
            glVertex3f(-leg_width/2 - 0.05, 0, -leg_width/2 - 0.05)
            
            glVertex3f(leg_width/2 + 0.05, -0.15, -leg_width/2 - 0.05)
            glVertex3f(leg_width/2 + 0.05, -0.15, leg_width/2 + 0.05)
            glVertex3f(leg_width/2 + 0.05, 0, leg_width/2 + 0.05)
            glVertex3f(leg_width/2 + 0.05, 0, -leg_width/2 - 0.05)
            
            glVertex3f(leg_width/2 + 0.05, -0.15, leg_width/2 + 0.05)
            glVertex3f(-leg_width/2 - 0.05, -0.15, leg_width/2 + 0.05)
            glVertex3f(-leg_width/2 - 0.05, 0, leg_width/2 + 0.05)
            glVertex3f(leg_width/2 + 0.05, 0, leg_width/2 + 0.05)
            
            glVertex3f(-leg_width/2 - 0.05, -0.15, leg_width/2 + 0.05)
            glVertex3f(-leg_width/2 - 0.05, -0.15, -leg_width/2 - 0.05)
            glVertex3f(-leg_width/2 - 0.05, 0, -leg_width/2 - 0.05)
            glVertex3f(-leg_width/2 - 0.05, 0, leg_width/2 + 0.05)
            glEnd()
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(-body_width/4, 0.3 + leg_swing, 0)
            glColor3f(0.15, 0.35, 0.7)
            glBegin(GL_QUADS)
            glVertex3f(-leg_width/2, -leg_length, -leg_width/2)
            glVertex3f(leg_width/2, -leg_length, -leg_width/2)
            glVertex3f(leg_width/2, 0, -leg_width/2)
            glVertex3f(-leg_width/2, 0, -leg_width/2)
            
            glVertex3f(leg_width/2, -leg_length, -leg_width/2)
            glVertex3f(leg_width/2, -leg_length, leg_width/2)
            glVertex3f(leg_width/2, 0, leg_width/2)
            glVertex3f(leg_width/2, 0, -leg_width/2)
            
            glVertex3f(leg_width/2, -leg_length, leg_width/2)
            glVertex3f(-leg_width/2, -leg_length, leg_width/2)
            glVertex3f(-leg_width/2, 0, leg_width/2)
            glVertex3f(leg_width/2, 0, leg_width/2)
            
            glVertex3f(-leg_width/2, -leg_length, leg_width/2)
            glVertex3f(-leg_width/2, -leg_length, -leg_width/2)
            glVertex3f(-leg_width/2, 0, -leg_width/2)
            glVertex3f(-leg_width/2, 0, leg_width/2)
            glEnd()
            
            glColor3f(0.3, 0.3, 0.3)
            glTranslatef(0, -leg_length + 0.05, 0.05)
            glBegin(GL_QUADS)
            glVertex3f(-leg_width/2 - 0.05, -0.15, -leg_width/2 - 0.05)
            glVertex3f(leg_width/2 + 0.05, -0.15, -leg_width/2 - 0.05)
            glVertex3f(leg_width/2 + 0.05, 0, -leg_width/2 - 0.05)
            glVertex3f(-leg_width/2 - 0.05, 0, -leg_width/2 - 0.05)
            
            glVertex3f(leg_width/2 + 0.05, -0.15, -leg_width/2 - 0.05)
            glVertex3f(leg_width/2 + 0.05, -0.15, leg_width/2 + 0.05)
            glVertex3f(leg_width/2 + 0.05, 0, leg_width/2 + 0.05)
            glVertex3f(leg_width/2 + 0.05, 0, -leg_width/2 - 0.05)
            
            glVertex3f(leg_width/2 + 0.05, -0.15, leg_width/2 + 0.05)
            glVertex3f(-leg_width/2 - 0.05, -0.15, leg_width/2 + 0.05)
            glVertex3f(-leg_width/2 - 0.05, 0, leg_width/2 + 0.05)
            glVertex3f(leg_width/2 + 0.05, 0, leg_width/2 + 0.05)
            
            glVertex3f(-leg_width/2 - 0.05, -0.15, leg_width/2 + 0.05)
            glVertex3f(-leg_width/2 - 0.05, -0.15, -leg_width/2 - 0.05)
            glVertex3f(-leg_width/2 - 0.05, 0, -leg_width/2 - 0.05)
            glVertex3f(-leg_width/2 - 0.05, 0, leg_width/2 + 0.05)
            glEnd()
            glPopMatrix()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            logger.info(f"绘制玩家错误: {e}")
    
    def draw_follower(self, follower):
        """绘制跟随者"""
        try:
            glPushMatrix()
            glTranslatef(follower["x"], follower["y"], follower["z"])
            
            # 禁用光照以绘制跟随者
            glDisable(GL_LIGHTING)
            
            # 跟随者头部
            glColor3f(0.6, 0.8, 0.4)
            self.draw_cube(1.5, 1.5, 1.5)
            
            # 跟随者身体
            glColor3f(0.4, 0.6, 0.2)
            glTranslatef(0, -2, 0)
            self.draw_cube(2, 3, 1.5)
            
            # 重新启用光照
            glEnable(GL_LIGHTING)
            
            glPopMatrix()
        except Exception as e:
            logger.info(f"绘制跟随者错误: {e}")
    
    def draw_hud(self):
        """绘制HUD"""
        # 恢复到2D模式
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # 绘制位置信息
        pos_text = f"位置: ({int(self.player_pos[0])}, {int(self.player_pos[2])})"
        pos_surf = self.font_small.render(pos_text, True, COLORS["text_white"])
        self.screen.blit(pos_surf, (10, 10))
        
        # 绘制跟随状态
        if self.follow_target:
            follow_text = f"跟随: {self.follow_target.get('type', '位置')}"
            follow_surf = self.font_small.render(follow_text, True, COLORS["accent_green"])
            self.screen.blit(follow_surf, (10, 40))
        
        # 绘制消息
        if self.message and self.message_timer > 0:
            msg_surf = self.font_main.render(self.message, True, COLORS["accent_gold"])
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            self.screen.blit(msg_surf, msg_rect)
            self.message_timer -= self.clock.get_time()
            if self.message_timer < 0:
                self.message = None
        
        # 绘制十字准心
        crosshair_center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        crosshair_size = 15
        crosshair_gap = 5
        crosshair_color = (255, 255, 255, 200)
        
        try:
            crosshair_surf = pygame.Surface((crosshair_size * 2 + 10, crosshair_size * 2 + 10), pygame.SRCALPHA)
            
            pygame.draw.line(crosshair_surf, crosshair_color,
                           (crosshair_size + 5, crosshair_gap),
                           (crosshair_size + 5, crosshair_size), 2)
            pygame.draw.line(crosshair_surf, crosshair_color,
                           (crosshair_size + 5, crosshair_size + crosshair_gap * 2 + 5),
                           (crosshair_size + 5, crosshair_size * 2 + 5), 2)
            pygame.draw.line(crosshair_surf, crosshair_color,
                           (crosshair_gap, crosshair_size + 5),
                           (crosshair_size, crosshair_size + 5), 2)
            pygame.draw.line(crosshair_surf, crosshair_color,
                           (crosshair_size + crosshair_gap * 2 + 5, crosshair_size + 5),
                           (crosshair_size * 2 + 5, crosshair_size + 5), 2)
            
            pygame.draw.circle(crosshair_surf, crosshair_color,
                             (crosshair_size + 5, crosshair_size + 5), 2, 1)
            
            self.screen.blit(crosshair_surf, 
                           (crosshair_center[0] - crosshair_size - 5, 
                            crosshair_center[1] - crosshair_size - 5))
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        
        # 绘制控制提示
        controls = [
            "WASD: 移动",
            "空格: 跳跃",
            "Shift: 潜行",
            "Tab: 锁定鼠标",
            "F: 跟随模式",
            "F5: 切换视角",
            "1-9: 选择物品",
            "左键: 放置/使用",
            "右键: 破坏/交互",
            "E: 背包",
            "C: 合成台",
            "Esc: 暂停菜单"
        ]
        for i, control in enumerate(controls):
            ctrl_surf = self.font_small.render(control, True, COLORS["text_white"])
            self.screen.blit(ctrl_surf, (SCREEN_WIDTH - 150, 10 + i * 25))
        
        self.draw_hotbar()
        
        glEnable(GL_DEPTH_TEST)
    
    def draw_mc_hud(self):
        """绘制MC风格HUD（生命值、饥饿值等）"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # 屏幕中心下方位置
        center_x = SCREEN_WIDTH // 2
        bottom_y = SCREEN_HEIGHT - 100
        
        # 绘制生命值（红色心形）
        heart_size = 20
        heart_spacing = 24
        start_heart_x = center_x - 10 * heart_spacing // 2
        for i in range(10):
            heart_x = start_heart_x + i * heart_spacing
            heart_y = bottom_y
            
            # 绘制心形容器
            heart_surf = pygame.Surface((heart_size, heart_size), pygame.SRCALPHA)
            if i * 2 < self.health:
                if i * 2 + 1 < self.health:
                    heart_surf.fill((255, 0, 0, 255))  # 满血
                else:
                    heart_surf.fill((255, 100, 100, 255))  # 半血
            else:
                heart_surf.fill((80, 80, 80, 180))  # 空血
            
            pygame.draw.circle(heart_surf, (0, 0, 0, 100), (10, 10), 9, 2)
            self.screen.blit(heart_surf, (heart_x, heart_y))
        
        # 绘制饥饿值（鸡腿）
        start_hunger_x = center_x + 10 * heart_spacing // 2 - heart_size
        for i in range(10):
            hunger_x = start_hunger_x - i * heart_spacing
            hunger_y = bottom_y
            
            hunger_surf = pygame.Surface((heart_size, heart_size), pygame.SRCALPHA)
            if i * 2 < self.hunger:
                if i * 2 + 1 < self.hunger:
                    hunger_surf.fill((255, 165, 0, 255))  # 饱
                else:
                    hunger_surf.fill((255, 200, 100, 255))  # 半饱
            else:
                hunger_surf.fill((80, 80, 80, 180))  # 饿
            
            pygame.draw.circle(hunger_surf, (0, 0, 0, 100), (10, 10), 9, 2)
            self.screen.blit(hunger_surf, (hunger_x, hunger_y))
        
        # 绘制氧气值（水中使用）
        if self.oxygen < 10:
            start_oxygen_x = center_x - 10 * heart_spacing // 2
            for i in range(10):
                oxygen_x = start_oxygen_x + i * heart_spacing
                oxygen_y = bottom_y + 30
                
                oxygen_surf = pygame.Surface((heart_size, heart_size), pygame.SRCALPHA)
                if i < self.oxygen:
                    oxygen_surf.fill((0, 150, 255, 255))
                else:
                    oxygen_surf.fill((50, 50, 80, 180))
                
                pygame.draw.circle(oxygen_surf, (0, 0, 0, 100), (10, 10), 9, 2)
                self.screen.blit(oxygen_surf, (oxygen_x, oxygen_y))
        
        # 绘制经验条
        exp_bar_width = 200
        exp_bar_height = 10
        exp_bar_x = center_x - exp_bar_width // 2
        exp_bar_y = bottom_y - 30
        
        exp_bar_bg = pygame.Surface((exp_bar_width, exp_bar_height), pygame.SRCALPHA)
        exp_bar_bg.fill((50, 50, 50, 200))
        self.screen.blit(exp_bar_bg, (exp_bar_x, exp_bar_y))
        
        exp_fill = pygame.Surface((int(exp_bar_width * (self.experience % 100 / 100)), exp_bar_height), pygame.SRCALPHA)
        exp_fill.fill((50, 200, 50, 255))
        self.screen.blit(exp_fill, (exp_bar_x, exp_bar_y))
        
        # 绘制等级
        if self.level > 0:
            level_text = self.font_main.render(str(self.level), True, (255, 215, 0))
            level_rect = level_text.get_rect(center=(center_x, exp_bar_y - 15))
            self.screen.blit(level_text, level_rect)
        
        # 绘制十字准星
        crosshair_size = 15
        crosshair_thickness = 2
        crosshair_color = (255, 255, 255)
        center_y = SCREEN_HEIGHT // 2
        
        # 水平线
        pygame.draw.line(self.screen, crosshair_color, 
                        (center_x - crosshair_size, center_y), 
                        (center_x + crosshair_size, center_y), 
                        crosshair_thickness)
        # 垂直线
        pygame.draw.line(self.screen, crosshair_color, 
                        (center_x, center_y - crosshair_size), 
                        (center_x, center_y + crosshair_size), 
                        crosshair_thickness)
        
        # 绘制聊天窗口
        chat_width = 400
        chat_height = 150
        chat_x = 10
        chat_y = SCREEN_HEIGHT - chat_height - 70
        
        chat_bg = pygame.Surface((chat_width, chat_height), pygame.SRCALPHA)
        chat_bg.fill((0, 0, 0, 120))
        self.screen.blit(chat_bg, (chat_x, chat_y))
        
        for i, msg in enumerate(self.chat_messages[-5:]):
            msg_text = self.font_small.render(msg, True, (255, 255, 255))
            self.screen.blit(msg_text, (chat_x + 5, chat_y + 5 + i * 25))
        
        # 绘制物品提示
        if self.hovered_item and self.item_tooltip_timer > 0:
            tooltip_text = self.font_small.render(self.hovered_item, True, (255, 255, 255))
            tooltip_bg = pygame.Surface((tooltip_text.get_width() + 10, tooltip_text.get_height() + 6), pygame.SRCALPHA)
            tooltip_bg.fill((0, 0, 0, 200))
            
            mx, my = pygame.mouse.get_pos()
            tooltip_x = mx + 15
            tooltip_y = my - tooltip_text.get_height() - 3
            
            if tooltip_x + tooltip_bg.get_width() > SCREEN_WIDTH:
                tooltip_x = mx - tooltip_bg.get_width() - 15
            
            self.screen.blit(tooltip_bg, (tooltip_x, tooltip_y))
            self.screen.blit(tooltip_text, (tooltip_x + 5, tooltip_y + 3))
            
            self.item_tooltip_timer -= 1
        
        glEnable(GL_DEPTH_TEST)
    
    def add_chat_message(self, message):
        """添加聊天消息"""
        self.chat_messages.append(message)
        if len(self.chat_messages) > self.max_chat_lines:
            self.chat_messages.pop(0)
    
    def unlock_achievement(self, achievement_id):
        """解锁成就"""
        if achievement_id in self.achievements and not self.achievements[achievement_id]["unlocked"]:
            self.achievements[achievement_id]["unlocked"] = True
            achievement = self.achievements[achievement_id]
            self.add_chat_message(f"[成就] {achievement['name']}: {achievement['description']}")
    
    def check_egg_triggers(self):
        """检测彩蛋触发条件"""
        try:
            # 检测放置方块彩蛋
            if len(self.placed_blocks) >= 1 and not self.eggs.get("first_block", {}).get("found", False):
                self.eggs["first_block"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 放置第一个方块！")
            
            if len(self.placed_blocks) >= 100 and not self.eggs.get("100_blocks", {}).get("found", False):
                self.eggs["100_blocks"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 放置100个方块！")
            
            # 检测合成彩蛋
            if self.stats["items_crafted"] >= 1 and not self.eggs.get("first_craft", {}).get("found", False):
                self.eggs["first_craft"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 完成第一次合成！")
            
            # 检测击杀彩蛋
            if self.stats["mobs_killed"] >= 1 and not self.eggs.get("first_kill", {}).get("found", False):
                self.eggs["first_kill"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 杀死第一个怪物！")
            
            if self.stats["mobs_killed"] >= 100 and not self.eggs.get("100_kills", {}).get("found", False):
                self.eggs["100_kills"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 杀死100个怪物！")
            
            # 检测昼夜彩蛋
            if self.stats["days_passed"] >= 1 and not self.eggs.get("day_night", {}).get("found", False):
                self.eggs["day_night"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 度过一个完整的昼夜循环！")
            
            # 检测高度彩蛋
            if self.player_pos[1] <= -50 and not self.eggs.get("underground", {}).get("found", False):
                self.eggs["underground"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 深入地下50格！")
            
            if self.player_pos[1] >= 50 and not self.eggs.get("high_altitude", {}).get("found", False):
                self.eggs["high_altitude"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 到达高空50格！")
            
            # 检测天气彩蛋
            if self.weather == "rain" and not self.eggs.get("rain", {}).get("found", False):
                self.eggs["rain"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 在雨中待5分钟！")
            
            if self.weather == "snow" and not self.eggs.get("snow", {}).get("found", False):
                self.eggs["snow"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 在雪中待5分钟！")
            
            # 检测Herobrine彩蛋
            if self.herobrine_active and not self.eggs.get("herobrine", {}).get("found", False):
                self.eggs["herobrine"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 在夜晚遇到Herobrine！")
            
            # 检测创造模式飞行彩蛋
            if self.game_mode == "creative" and not self.eggs.get("fly_creative", {}).get("found", False):
                total_distance = abs(self.player_pos[0]) + abs(self.player_pos[1]) + abs(self.player_pos[2])
                if total_distance >= 100:
                    self.eggs["fly_creative"]["found"] = True
                    self.add_chat_message("🎉 解锁彩蛋: 在创造模式飞行100格！")
            
            # 检测游泳彩蛋
            if self.player_pos[1] < 0 and not self.eggs.get("swim", {}).get("found", False):
                self.eggs["swim"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 游泳100格！")
            
            # 检测跳跃彩蛋
            if not hasattr(self, 'jump_count'):
                self.jump_count = 0
            
            if self.velocity[1] > 0:
                self.jump_count += 1
                if self.jump_count >= 100 and not self.eggs.get("jump_100", {}).get("found", False):
                    self.eggs["jump_100"]["found"] = True
                    self.add_chat_message("🎉 解锁彩蛋: 跳跃100次！")
            
            # 检测潜行彩蛋
            if self.is_sneaking and not self.eggs.get("sneak", {}).get("found", False):
                self.eggs["sneak"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 潜行100格！")
            
            # 检测冲刺彩蛋
            if self.is_sprinting and not self.eggs.get("sprint", {}).get("found", False):
                self.eggs["sprint"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 冲刺100格！")
            
            # 检测工具制作彩蛋
            if self.eggs.get("pickaxe", {}).get("found", False):
                self.eggs["pickaxe"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 制作一把镐子！")
            
            if self.eggs.get("axe", {}).get("found", False):
                self.eggs["axe"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 制作一把斧头！")
            
            if self.eggs.get("shovel", {}).get("found", False):
                self.eggs["shovel"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 制作一把铲子！")
            
            if self.eggs.get("hoe", {}).get("found", False):
                self.eggs["hoe"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 制作一把锄头！")
            
            if self.eggs.get("sword", {}).get("found", False):
                self.eggs["sword"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 制作一把剑！")
            
            if self.eggs.get("bow", {}).get("found", False):
                self.eggs["bow"]["found"] = True
                self.add_chat_message("🎉 解锁彩蛋: 制作一把弓！")
            
        except Exception as e:
            logger.info(f"[错误] 检测彩蛋触发失败: {e}")
    
    def draw_pause_menu(self):
        """绘制暂停菜单（类似MC风格）"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        menu_width = 300
        menu_height = 250
        menu_x = SCREEN_WIDTH // 2 - menu_width // 2
        menu_y = SCREEN_HEIGHT // 2 - menu_height // 2
        
        bg_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        self.screen.blit(bg_surf, (0, 0))
        
        menu_surf = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        menu_surf.fill((60, 60, 80, 240))
        pygame.draw.rect(menu_surf, (100, 100, 120), (0, 0, menu_width, menu_height), 3, border_radius=10)
        self.screen.blit(menu_surf, (menu_x, menu_y))
        
        title_surf = self.font_main.render("游戏暂停", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, menu_y + 30))
        self.screen.blit(title_surf, title_rect)
        
        button_height = 40
        button_spacing = 10
        button_start_y = menu_y + 70
        
        for i, option in enumerate(self.pause_menu_options):
            button_y = button_start_y + i * (button_height + button_spacing)
            button_width = menu_width - 40
            button_x = menu_x + 20
            
            is_selected = (i == self.pause_menu_selected)
            
            btn_surf = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
            if is_selected:
                btn_surf.fill((80, 120, 80, 255))
                pygame.draw.rect(btn_surf, COLORS["accent_green"], (0, 0, button_width, button_height), 2, border_radius=5)
            else:
                btn_surf.fill((50, 50, 70, 255))
                pygame.draw.rect(btn_surf, (80, 80, 100), (0, 0, button_width, button_height), 2, border_radius=5)
            
            self.screen.blit(btn_surf, (button_x, button_y))
            
            text_surf = self.font_small.render(option, True, COLORS["text_white"])
            text_rect = text_surf.get_rect(center=(button_x + button_width // 2, button_y + button_height // 2))
            self.screen.blit(text_surf, text_rect)
        
        hint_surf = self.font_small.render("↑↓选择  Enter确认  Esc返回", True, (150, 150, 150))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, menu_y + menu_height - 20))
        self.screen.blit(hint_surf, hint_rect)
        
        glEnable(GL_DEPTH_TEST)
    
    def handle_pause_input(self):
        """处理暂停菜单输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_paused = False
                    self.is_mouse_locked = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                elif event.key == pygame.K_UP:
                    self.pause_menu_selected = (self.pause_menu_selected - 1) % len(self.pause_menu_options)
                elif event.key == pygame.K_DOWN:
                    self.pause_menu_selected = (self.pause_menu_selected + 1) % len(self.pause_menu_options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    option = self.pause_menu_options[self.pause_menu_selected]
                    if option == "继续游戏":
                        self.is_paused = False
                        self.is_mouse_locked = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                    elif option == "设置":
                        self.message = "设置功能开发中..."
                        self.message_timer = 2000
                    elif option == "保存并退出":
                        return "quit"
                    elif option == "返回主菜单":
                        return "main_menu"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    menu_width = 300
                    menu_height = 250
                    menu_x = SCREEN_WIDTH // 2 - menu_width // 2
                    menu_y = SCREEN_HEIGHT // 2 - menu_height // 2
                    button_height = 40
                    button_spacing = 10
                    button_start_y = menu_y + 70
                    
                    mx, my = event.pos
                    for i in range(len(self.pause_menu_options)):
                        button_y = button_start_y + i * (button_height + button_spacing)
                        button_width = menu_width - 40
                        button_x = menu_x + 20
                        
                        if button_x <= mx <= button_x + button_width and button_y <= my <= button_y + button_height:
                            self.pause_menu_selected = i
                            option = self.pause_menu_options[i]
                            if option == "继续游戏":
                                self.is_paused = False
                                self.is_mouse_locked = True
                                pygame.mouse.set_visible(False)
                                pygame.event.set_grab(True)
                            elif option == "设置":
                                self.message = "设置功能开发中..."
                                self.message_timer = 2000
                            elif option == "保存并退出":
                                return "quit"
                            elif option == "返回主菜单":
                                return "main_menu"
        return "continue"
    
    def draw_hotbar(self):
        """绘制快捷栏（类似MC）"""
        hotbar_width = 9 * 50 + 10
        hotbar_height = 50
        hotbar_x = SCREEN_WIDTH // 2 - hotbar_width // 2
        hotbar_y = SCREEN_HEIGHT - 60
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        hotbar_surf = pygame.Surface((hotbar_width, hotbar_height), pygame.SRCALPHA)
        hotbar_surf.fill((30, 30, 30, 200))
        
        for i in range(9):
            slot_x = 5 + i * 50
            slot_surf = pygame.Surface((45, 45), pygame.SRCALPHA)
            
            if i == self.hotbar_selected:
                slot_surf.fill((80, 80, 80, 255))
                pygame.draw.rect(slot_surf, COLORS["accent_gold"], (0, 0, 45, 45), 2)
            else:
                slot_surf.fill((50, 50, 50, 255))
                pygame.draw.rect(slot_surf, (70, 70, 70), (0, 0, 45, 45), 1)
            
            hotbar_surf.blit(slot_surf, (slot_x, 2))
            
            if self.hotbar[i]:
                block_color = self.get_block_color(self.hotbar[i])
                block_surf = pygame.Surface((35, 35), pygame.SRCALPHA)
                block_surf.fill(block_color)
                hotbar_surf.blit(block_surf, (slot_x + 5, 7))
        
        self.screen.blit(hotbar_surf, (hotbar_x, hotbar_y))
        
        glEnable(GL_DEPTH_TEST)
    
    def get_block_color(self, block_type):
        """获取方块颜色"""
        colors = {
            "泥土": (139, 90, 43),
            "石头": (128, 128, 128),
            "木头": (160, 82, 45),
            "草地": (34, 139, 34),
            "沙子": (238, 214, 175),
            "水": (65, 105, 225),
            "玻璃": (200, 200, 200),
            "砖块": (178, 34, 34)
        }
        return colors.get(block_type, (128, 128, 128))
    
    def draw_inventory(self):
        """绘制背包界面（类似旅行者背包）"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        inv_width = 500
        inv_height = 400
        inv_x = SCREEN_WIDTH // 2 - inv_width // 2
        inv_y = SCREEN_HEIGHT // 2 - inv_height // 2
        
        bg_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        self.screen.blit(bg_surf, (0, 0))
        
        inv_surf = pygame.Surface((inv_width, inv_height), pygame.SRCALPHA)
        inv_surf.fill((60, 60, 80, 240))
        pygame.draw.rect(inv_surf, (100, 100, 120), (0, 0, inv_width, inv_height), 3, border_radius=10)
        self.screen.blit(inv_surf, (inv_x, inv_y))
        
        title_surf = self.font_main.render("背包", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, inv_y + 25))
        self.screen.blit(title_surf, title_rect)
        
        categories = ["全部", "方块类", "资源类", "武器类", "弹药类", "食物类", "工具类"]
        cat_width = 60
        cat_start_x = inv_x + 20
        cat_y = inv_y + 50
        
        for i, cat in enumerate(categories):
            cat_x = cat_start_x + i * (cat_width + 5)
            cat_surf = pygame.Surface((cat_width, 25), pygame.SRCALPHA)
            
            if cat == self.inventory_category:
                cat_surf.fill((80, 120, 80, 255))
            else:
                cat_surf.fill((50, 50, 70, 255))
            
            pygame.draw.rect(cat_surf, (80, 80, 100), (0, 0, cat_width, 25), 1, border_radius=3)
            self.screen.blit(cat_surf, (cat_x, cat_y))
            
            cat_text = self.font_small.render(cat, True, COLORS["text_white"])
            cat_text_rect = cat_text.get_rect(center=(cat_x + cat_width // 2, cat_y + 12))
            self.screen.blit(cat_text, cat_text_rect)
        
        slot_size = 45
        slot_spacing = 5
        slots_per_row = 9
        slot_start_x = inv_x + 20
        slot_start_y = inv_y + 85
        
        for row in range(3):
            for col in range(slots_per_row):
                slot_idx = row * slots_per_row + col
                slot_x = slot_start_x + col * (slot_size + slot_spacing)
                slot_y = slot_start_y + row * (slot_size + slot_spacing)
                
                slot_surf = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
                
                if slot_idx == self.inventory_selected_slot:
                    slot_surf.fill((80, 120, 80, 255))
                    pygame.draw.rect(slot_surf, COLORS["accent_gold"], (0, 0, slot_size, slot_size), 2)
                else:
                    slot_surf.fill((50, 50, 70, 255))
                    pygame.draw.rect(slot_surf, (70, 70, 90), (0, 0, slot_size, slot_size), 1)
                
                self.screen.blit(slot_surf, (slot_x, slot_y))
                
                item = self.inventory[slot_idx]
                if item:
                    item_color = self.get_item_color(item["name"])
                    item_surf = pygame.Surface((35, 35), pygame.SRCALPHA)
                    item_surf.fill(item_color)
                    self.screen.blit(item_surf, (slot_x + 5, slot_y + 5))
                    
                    if item.get("count", 1) > 1:
                        count_text = self.font_small.render(str(item["count"]), True, COLORS["text_white"])
                        self.screen.blit(count_text, (slot_x + slot_size - 20, slot_y + slot_size - 15))
        
        hotbar_y = inv_y + inv_height - 60
        hotbar_width = 9 * 50 + 10
        hotbar_x = inv_x + (inv_width - hotbar_width) // 2
        
        hotbar_label = self.font_small.render("快捷栏", True, COLORS["text_white"])
        self.screen.blit(hotbar_label, (hotbar_x, hotbar_y - 20))
        
        for i in range(9):
            slot_x = hotbar_x + 5 + i * 50
            slot_surf = pygame.Surface((45, 45), pygame.SRCALPHA)
            
            if i == self.hotbar_selected:
                slot_surf.fill((80, 120, 80, 255))
                pygame.draw.rect(slot_surf, COLORS["accent_gold"], (0, 0, 45, 45), 2)
            else:
                slot_surf.fill((50, 50, 70, 255))
                pygame.draw.rect(slot_surf, (70, 70, 90), (0, 0, 45, 45), 1)
            
            self.screen.blit(slot_surf, (slot_x, hotbar_y))
            
            if self.hotbar[i]:
                item_color = self.get_item_color(self.hotbar[i])
                item_surf = pygame.Surface((35, 35), pygame.SRCALPHA)
                item_surf.fill(item_color)
                self.screen.blit(item_surf, (slot_x + 5, hotbar_y + 5))
        
        if self.dragging_item:
            mx, my = pygame.mouse.get_pos()
            drag_color = self.get_item_color(self.dragging_item["name"])
            drag_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            drag_surf.fill(drag_color)
            pygame.draw.rect(drag_surf, COLORS["accent_gold"], (0, 0, 40, 40), 2)
            self.screen.blit(drag_surf, (mx - 20, my - 20))
        
        hint_surf = self.font_small.render("E: 关闭背包 | 左键: 选择/拖拽 | 右键: 放置半堆", True, (150, 150, 150))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, inv_y + inv_height - 10))
        self.screen.blit(hint_surf, hint_rect)
        
        glEnable(GL_DEPTH_TEST)
    
    def get_item_color(self, item_name):
        """获取物品颜色"""
        colors = {
            "泥土": (139, 90, 43),
            "石头": (128, 128, 128),
            "木头": (160, 82, 45),
            "草地": (34, 139, 34),
            "沙子": (238, 214, 175),
            "水": (65, 105, 225),
            "玻璃": (200, 200, 200),
            "砖块": (178, 34, 34),
            "煤炭": (50, 50, 50),
            "金元宝": (255, 215, 0),
            "食物": (255, 100, 100),
            "手枪": (100, 100, 100),
            "步枪": (80, 80, 80),
            "狙击枪": (60, 60, 60),
            "机枪": (70, 70, 70),
            "普通子弹": (180, 180, 180),
            "高级子弹": (200, 200, 200),
            "稀有子弹": (220, 220, 220),
            "面包": (210, 180, 140),
            "苹果": (255, 0, 0),
            "烤肉": (150, 80, 50),
            "药草": (0, 200, 0),
            "镐子": (150, 150, 150),
            "斧头": (139, 90, 43),
            "铲子": (180, 180, 180),
            "刘备卡": (255, 200, 100),
            "关羽卡": (255, 100, 100),
            "张飞卡": (100, 100, 255),
            "赵云卡": (100, 255, 100),
            "诸葛亮卡": (200, 200, 255),
            "曹操卡": (50, 50, 50)
        }
        return colors.get(item_name, (128, 128, 128))
    
    def handle_inventory_input(self):
        """处理背包输入"""
        inv_width = 500
        inv_height = 400
        inv_x = SCREEN_WIDTH // 2 - inv_width // 2
        inv_y = SCREEN_HEIGHT // 2 - inv_height // 2
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_e:
                    self.show_inventory = False
                    self.is_mouse_locked = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                categories = ["全部", "方块类", "资源类", "武器类", "弹药类", "食物类", "工具类"]
                cat_width = 60
                cat_start_x = inv_x + 20
                cat_y = inv_y + 50
                
                for i, cat in enumerate(categories):
                    cat_x = cat_start_x + i * (cat_width + 5)
                    if cat_x <= mx <= cat_x + cat_width and cat_y <= my <= cat_y + 25:
                        self.inventory_category = cat
                
                slot_size = 45
                slot_spacing = 5
                slots_per_row = 9
                slot_start_x = inv_x + 20
                slot_start_y = inv_y + 85
                
                for row in range(3):
                    for col in range(slots_per_row):
                        slot_idx = row * slots_per_row + col
                        slot_x = slot_start_x + col * (slot_size + slot_spacing)
                        slot_y = slot_start_y + row * (slot_size + slot_spacing)
                        
                        if slot_x <= mx <= slot_x + slot_size and slot_y <= my <= slot_y + slot_size:
                            if event.button == 1:
                                self.handle_slot_click(slot_idx, "inventory")
                            elif event.button == 3:
                                self.handle_slot_right_click(slot_idx, "inventory")
                
                hotbar_y = inv_y + inv_height - 60
                hotbar_width = 9 * 50 + 10
                hotbar_x = inv_x + (inv_width - hotbar_width) // 2
                
                for i in range(9):
                    slot_x = hotbar_x + 5 + i * 50
                    if slot_x <= mx <= slot_x + 45 and hotbar_y <= my <= hotbar_y + 45:
                        if event.button == 1:
                            self.handle_slot_click(i, "hotbar")
                        elif event.button == 3:
                            self.handle_slot_right_click(i, "hotbar")
        
        return "continue"
    
    def handle_slot_click(self, slot_idx, source):
        """处理槽位点击"""
        if source == "inventory":
            slot_item = self.inventory[slot_idx]
        else:
            slot_item = {"name": self.hotbar[slot_idx], "count": 1} if self.hotbar[slot_idx] else None
        
        if self.dragging_item:
            if slot_item:
                if slot_item["name"] == self.dragging_item["name"]:
                    total = slot_item.get("count", 1) + self.dragging_item.get("count", 1)
                    if total <= self.max_stack_size:
                        slot_item["count"] = total
                        self.dragging_item = None
                    else:
                        slot_item["count"] = self.max_stack_size
                        self.dragging_item["count"] = total - self.max_stack_size
                else:
                    if source == "inventory":
                        self.inventory[slot_idx] = self.dragging_item
                    else:
                        self.hotbar[slot_idx] = self.dragging_item["name"]
                    self.dragging_item = slot_item
            else:
                if source == "inventory":
                    self.inventory[slot_idx] = self.dragging_item
                else:
                    self.hotbar[slot_idx] = self.dragging_item["name"]
                self.dragging_item = None
        else:
            if slot_item:
                self.dragging_item = slot_item
                if source == "inventory":
                    self.inventory[slot_idx] = None
                else:
                    self.hotbar[slot_idx] = None
                self.drag_source = source
    
    def handle_slot_right_click(self, slot_idx, source):
        """处理槽位右键点击（放置半堆）"""
        if self.dragging_item:
            if source == "inventory":
                if self.inventory[slot_idx]:
                    if self.inventory[slot_idx]["name"] == self.dragging_item["name"]:
                        self.inventory[slot_idx]["count"] += 1
                        self.dragging_item["count"] -= 1
                    else:
                        return
                else:
                    self.inventory[slot_idx] = {"name": self.dragging_item["name"], "count": 1}
                    self.dragging_item["count"] -= 1
            else:
                if self.hotbar[slot_idx] == self.dragging_item["name"]:
                    pass
                elif self.hotbar[slot_idx] is None:
                    self.hotbar[slot_idx] = self.dragging_item["name"]
                    self.dragging_item["count"] -= 1
            
            if self.dragging_item["count"] <= 0:
                self.dragging_item = None
    
    def add_item_to_inventory(self, item_name, count=1):
        """添加物品到背包"""
        for i, slot in enumerate(self.inventory):
            if slot and slot["name"] == item_name:
                if slot["count"] + count <= self.max_stack_size:
                    slot["count"] += count
                    return True
                else:
                    remaining = self.max_stack_size - slot["count"]
                    slot["count"] = self.max_stack_size
                    count -= remaining
        
        for i, slot in enumerate(self.inventory):
            if slot is None:
                self.inventory[i] = {"name": item_name, "count": count}
                return True
        
        return False
    
    def remove_item_from_inventory(self, item_name, count=1):
        """从背包移除物品"""
        for i, slot in enumerate(self.inventory):
            if slot and slot["name"] == item_name:
                if slot["count"] >= count:
                    slot["count"] -= count
                    if slot["count"] <= 0:
                        self.inventory[i] = None
                    return True
                else:
                    return False
        return False
    
    def clamp_value(self, value, min_val, max_val):
        """限制值在范围内（安全保护）"""
        if not isinstance(value, (int, float)):
            return min_val
        return max(min_val, min(max_val, value))
    
    def set_health(self, value):
        """安全设置生命值"""
        self.health = self.clamp_value(value, 0, self.max_health)
    
    def add_health(self, amount):
        """安全增加生命值"""
        self.set_health(self.health + amount)
    
    def set_hunger(self, value):
        """安全设置饥饿值"""
        self.hunger = self.clamp_value(value, 0, self.max_hunger)
    
    def add_hunger(self, amount):
        """安全增加饥饿值"""
        self.set_hunger(self.hunger + amount)
    
    def set_oxygen(self, value):
        """安全设置氧气值"""
        self.oxygen = self.clamp_value(value, 0, self.max_oxygen)
    
    def add_oxygen(self, amount):
        """安全增加氧气值"""
        self.set_oxygen(self.oxygen + amount)
    
    def set_armor(self, value):
        """安全设置护甲值"""
        self.armor = self.clamp_value(value, 0, self.max_armor)
    
    def add_armor(self, amount):
        """安全增加护甲值"""
        self.set_armor(self.armor + amount)
    
    def validate_inventory(self):
        """验证背包数据完整性（安全检查）"""
        if not isinstance(self.inventory, list):
            self.inventory = [None] * self.inventory_slots
        
        for i in range(len(self.inventory)):
            if self.inventory[i] is not None:
                if not isinstance(self.inventory[i], dict):
                    self.inventory[i] = None
                else:
                    if "name" not in self.inventory[i] or "count" not in self.inventory[i]:
                        self.inventory[i] = None
                    else:
                        self.inventory[i]["count"] = self.clamp_value(self.inventory[i]["count"], 1, self.max_stack_size)
    
    def validate_hotbar(self):
        """验证快捷栏数据完整性"""
        if not isinstance(self.hotbar, list):
            self.hotbar = [None] * 9
        
        self.hotbar_selected = self.clamp_value(self.hotbar_selected, 0, 8)
    
    def validate_crafting_grid(self):
        """验证合成网格数据完整性"""
        if not isinstance(self.crafting_grid, list) or len(self.crafting_grid) != 3:
            self.crafting_grid = [[None for _ in range(3)] for _ in range(3)]
        
        for row in range(3):
            if not isinstance(self.crafting_grid[row], list) or len(self.crafting_grid[row]) != 3:
                self.crafting_grid[row] = [None, None, None]
    
    def validate_player_position(self):
        """验证玩家位置（防止非法位置）"""
        if not isinstance(self.player_pos, list) or len(self.player_pos) != 3:
            self.player_pos = [0, 0, 0]
        
        for i in range(3):
            if not isinstance(self.player_pos[i], (int, float)):
                self.player_pos[i] = 0
        
        self.player_pos[1] = max(self.player_pos[1], 0)
    
    def validate_camera(self):
        """验证相机参数"""
        self.camera["yaw"] = self.camera["yaw"] % 360
        self.camera["pitch"] = self.clamp_value(self.camera["pitch"], -90, 90)
        self.camera["speed"] = self.clamp_value(self.camera["speed"], 0.1, 2.0)
    
    def validate_all(self):
        """全面验证所有数据（在加载后调用）"""
        self.validate_inventory()
        self.validate_hotbar()
        self.validate_crafting_grid()
        self.validate_player_position()
        self.validate_camera()
        
        self.set_health(self.health)
        self.set_hunger(self.hunger)
        self.set_oxygen(self.oxygen)
        self.set_armor(self.armor)
    
    def toggle_gamemode(self):
        """切换游戏模式（生存/创造）"""
        if self.game_mode == "survival":
            self.game_mode = "creative"
            self.can_fly = True
            self.flying = False
            self.health = self.max_health
            self.hunger = self.max_hunger
            self.add_chat_message("已切换到创造模式")
        else:
            self.game_mode = "survival"
            self.can_fly = False
            self.flying = False
            self.add_chat_message("已切换到生存模式")
    
    def handle_flying(self):
        """处理飞行逻辑（创造模式）"""
        if not self.can_fly:
            return
        
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_SPACE]:
            self.flying = True
            self.player_pos[1] += self.fly_speed
        elif keys[pygame.K_LSHIFT]:
            self.player_pos[1] -= self.fly_speed
        else:
            self.flying = False
    
    def execute_command(self, command):
        """执行命令"""
        command = command.strip().lower()
        args = command.split()
        
        if not args:
            return
        
        cmd = args[0]
        
        if cmd == "gamemode" or cmd == "gm":
            if len(args) >= 2:
                mode = args[1]
                if mode in ["creative", "c", "1"]:
                    self.game_mode = "creative"
                    self.can_fly = True
                    self.add_chat_message("已切换到创造模式")
                elif mode in ["survival", "s", "0"]:
                    self.game_mode = "survival"
                    self.can_fly = False
                    self.flying = False
                    self.add_chat_message("已切换到生存模式")
                else:
                    self.add_chat_message("未知游戏模式: " + mode)
            else:
                self.add_chat_message("当前模式: " + self.game_mode)
        
        elif cmd == "give":
            if len(args) >= 2:
                item_name = args[1]
                count = int(args[2]) if len(args) >= 3 else 1
                self.add_item_to_inventory(item_name, count)
                self.add_chat_message(f"获得 {count} 个 {item_name}")
            else:
                self.add_chat_message("用法: /give <物品名称> [数量]")
        
        elif cmd == "kill":
            self.health = 0
            self.add_chat_message("你自杀了!")
        
        elif cmd == "time":
            if len(args) >= 2:
                sub_cmd = args[1]
                if sub_cmd == "day":
                    self.day_time = 1000
                    self.add_chat_message("已设置为白天")
                elif sub_cmd == "night":
                    self.day_time = 13000
                    self.add_chat_message("已设置为夜晚")
                elif sub_cmd == "add" and len(args) >= 3:
                    self.day_time += int(args[2])
                    self.add_chat_message(f"时间增加了 {args[2]}")
            else:
                time_str = "白天" if self.is_day else "夜晚"
                self.add_chat_message(f"当前时间: {self.day_time} ({time_str})")
        
        elif cmd == "weather":
            if len(args) >= 2:
                weather_type = args[1]
                if weather_type in ["clear", "sunny"]:
                    self.weather = "clear"
                    self.add_chat_message("天气已设置为晴天")
                elif weather_type == "rain":
                    self.weather = "rain"
                    self.add_chat_message("天气已设置为下雨")
                elif weather_type == "snow":
                    self.weather = "snow"
                    self.add_chat_message("天气已设置为下雪")
                else:
                    self.add_chat_message("未知天气类型: " + weather_type)
            else:
                self.add_chat_message(f"当前天气: {self.weather}")
        
        elif cmd == "tp" or cmd == "teleport":
            if len(args) >= 4:
                try:
                    x = float(args[1])
                    y = float(args[2])
                    z = float(args[3])
                    self.player_pos = [x, y, z]
                    self.add_chat_message(f"已传送到 ({x}, {y}, {z})")
                except Exception as _e:
                    self.add_chat_message("用法: /tp <x> <y> <z>")
        
        elif cmd == "heal":
            self.health = self.max_health
            self.add_chat_message("已恢复全部生命值")
        
        elif cmd == "feed":
            self.hunger = self.max_hunger
            self.add_chat_message("已恢复全部饥饿值")
        
        elif cmd == "help":
            help_text = [
                "可用命令:",
                "/gamemode <creative/survival> - 切换游戏模式",
                "/give <物品> [数量] - 获得物品",
                "/kill - 自杀",
                "/time <day/night/add> - 设置时间",
                "/weather <clear/rain/snow/thunder> - 设置天气",
                "/tp <x> <y> <z> - 传送",
                "/heal - 恢复生命",
                "/feed - 恢复饥饿",
                "/help - 显示帮助",
                "/eggs - 显示彩蛋提示",
                "/cheats - 显示作弊码列表",
                "/developer - 开发者彩蛋",
                "/dev - 开发者隐藏命令",
                "/effect <效果> - 添加效果",
                "/spawn <生物> - 生成生物"
            ]
            for line in help_text:
                self.add_chat_message(line)
        
        elif cmd == "cheats" or cmd == "cheatcodes":
            self.add_chat_message("=== 🎮 作弊码列表 ===")
            self.add_chat_message("💡 在游戏中按顺序输入按键即可激活！")
            self.add_chat_message("⚠️ 2秒内未继续输入会重置序列")
            for code_id, code_data in self.cheat_codes.items():
                sequence_str = " ".join(code_data["sequence"])
                self.add_chat_message(f"🔑 {code_data['name']}: {sequence_str}")
            self.add_chat_message("📍 还有隐藏的特定位置彩蛋等你发现！")
        
        elif cmd == "dev" or cmd == "developer":
            if self.active_cheat_effects.get("developer_mode", False) or cmd == "developer":
                if not self.eggs["developer"]["found"]:
                    self.eggs["developer"]["found"] = True
                    self.add_chat_message("🎉 恭喜解锁开发者彩蛋！")
                    self.add_chat_message("神秘信息: 42是宇宙的终极答案")
                self.add_chat_message("🔧 开发者命令已激活！")
                self.add_chat_message("可用: /dev_stats, /dev_spawn, /dev_effect")
                self.active_cheat_effects["developer_mode"] = True
            else:
                self.add_chat_message("⚠️ 需要先激活开发者模式！")
                self.add_chat_message("提示: 输入 42 或找到开发者彩蛋")
        
        elif cmd == "dev_stats":
            if self.active_cheat_effects.get("developer_mode", False):
                self.add_chat_message("=== 📊 开发者统计 ===")
                self.add_chat_message(f"作弊码输入次数: {self.cheat_stats['codes_entered']}")
                self.add_chat_message(f"成功激活次数: {self.cheat_stats['codes_successful']}")
                self.add_chat_message(f"最后激活: {self.cheat_stats['last_code'] or '无'}")
                self.add_chat_message(f"总奖励数: {self.cheat_stats['total_rewards']}")
                self.add_chat_message(f"已解锁彩蛋: {sum(1 for e in self.eggs.values() if e.get('found', False))}")
                self.add_chat_message(f"当前按键序列: {self.cheat_code_buffer}")
            else:
                self.add_chat_message("⚠️ 需要开发者模式！")
        
        elif cmd == "effect":
            if len(args) >= 2:
                effect_name = args[1]
                duration = int(args[2]) if len(args) >= 3 else 60
                if effect_name in self.active_cheat_effects:
                    self.active_cheat_effects[effect_name] = True
                    self.add_chat_message(f"✨ 效果 {effect_name} 已激活，持续 {duration} 秒！")
                else:
                    available_effects = list(self.active_cheat_effects.keys())
                    self.add_chat_message(f"未知效果: {effect_name}")
                    self.add_chat_message(f"可用效果: {', '.join(available_effects)}")
            else:
                self.add_chat_message("用法: /effect <效果名> [持续时间]")
        
        elif cmd == "spawn":
            if len(args) >= 2:
                entity_type = args[1]
                self.add_chat_message(f"🐉 生成生物: {entity_type}")
                self.spawn_effect_particle(self.player_pos[0], self.player_pos[1] + 2, self.player_pos[2], "magic")
            else:
                self.add_chat_message("用法: /spawn <生物类型>")
        
        elif cmd == "locations":
            self.add_chat_message("=== 📍 秘密位置彩蛋 ===")
            for loc_id, loc_data in self.secret_locations.items():
                pos = loc_data["pos"]
                if self.active_cheat_effects.get("egg_hints", False):
                    self.add_chat_message(f"🎯 {loc_data['message']} 位置: ({pos[0]}, {pos[1]}, {pos[2]})")
                else:
                    self.add_chat_message(f"❓ {loc_data['message']} (位置隐藏)")
            self.add_chat_message("💡 使用 'egg' 作弊码显示位置提示！")
        
        elif cmd == "eggs":
            self.add_chat_message("=== 彩蛋列表 ===")
            for egg_id, egg_data in self.eggs.items():
                status = "✅" if egg_data["found"] else "❓"
                self.add_chat_message(f"{status} {egg_data['hint']}")
        
        elif cmd == "developer":
            if not self.eggs["developer"]["found"]:
                self.eggs["developer"]["found"] = True
                self.add_chat_message("🎉 恭喜解锁开发者彩蛋！")
                self.add_chat_message("神秘信息: 42是宇宙的终极答案")
                self.add_chat_message("你发现了隐藏的开发者命令！")
            else:
                self.add_chat_message("你已经解锁过这个彩蛋了！")
        
        elif cmd == "herobrine":
            self.herobrine_active = True
            self.herobrine_pos = [self.player_pos[0] + 10, 0, self.player_pos[2] + 10]
            self.add_chat_message("⚠️ Herobrine已被召唤...")
        
        else:
            self.add_chat_message("未知命令: " + cmd)
    
    def check_cheat_code_sequence(self, key):
        """检测按键序列作弊码"""
        try:
            current_time = time.time()
            
            if current_time - self.last_cheat_key_time > self.cheat_code_input_timeout:
                self.cheat_code_buffer = []
            
            self.last_cheat_key_time = current_time
            
            key_name = self.get_key_name(key)
            if key_name:
                self.cheat_code_buffer.append(key_name)
                
                if len(self.cheat_code_buffer) > self.cheat_code_max_length:
                    self.cheat_code_buffer.pop(0)
                
                for code_id, code_data in self.cheat_codes.items():
                    sequence = code_data["sequence"]
                    buffer_tail = self.cheat_code_buffer[-len(sequence):]
                    
                    if buffer_tail == sequence:
                        self.activate_cheat_code(code_id, code_data)
                        self.cheat_code_buffer = []
                        return
                        
        except Exception as e:
            logger.info(f"[错误] 检测作弊码序列失败: {e}")
    
    def get_key_name(self, key):
        """获取按键名称"""
        key_map = {
            pygame.K_UP: "up",
            pygame.K_DOWN: "down",
            pygame.K_LEFT: "left",
            pygame.K_RIGHT: "right",
            pygame.K_a: "a",
            pygame.K_b: "b",
            pygame.K_c: "c",
            pygame.K_d: "d",
            pygame.K_e: "e",
            pygame.K_f: "f",
            pygame.K_g: "g",
            pygame.K_h: "h",
            pygame.K_i: "i",
            pygame.K_j: "j",
            pygame.K_k: "k",
            pygame.K_l: "l",
            pygame.K_m: "m",
            pygame.K_n: "n",
            pygame.K_o: "o",
            pygame.K_p: "p",
            pygame.K_q: "q",
            pygame.K_r: "r",
            pygame.K_s: "s",
            pygame.K_t: "t",
            pygame.K_u: "u",
            pygame.K_v: "v",
            pygame.K_w: "w",
            pygame.K_x: "x",
            pygame.K_y: "y",
            pygame.K_z: "z",
            pygame.K_0: "0",
            pygame.K_1: "1",
            pygame.K_2: "2",
            pygame.K_3: "3",
            pygame.K_4: "4",
            pygame.K_5: "5",
            pygame.K_6: "6",
            pygame.K_7: "7",
            pygame.K_8: "8",
            pygame.K_9: "9"
        }
        return key_map.get(key, None)
    
    def activate_cheat_code(self, code_id, code_data):
        """激活作弊码效果"""
        try:
            self.add_chat_message(f"🎮 {code_data['message']}")
            self.cheat_stats["codes_entered"] += 1
            self.cheat_stats["codes_successful"] += 1
            self.cheat_stats["last_code"] = code_id
            
            effect = code_data.get("effect", "")
            reward = code_data.get("reward", {})
            
            if "health" in reward:
                self.health = min(self.health + reward["health"], self.max_health * 10)
            if "hunger" in reward:
                self.hunger = min(self.hunger + reward["hunger"], self.max_hunger * 10)
            if "experience" in reward:
                self.experience += reward["experience"]
            if "level" in reward:
                self.level = reward["level"]
            if "game_mode" in reward:
                self.game_mode = reward["game_mode"]
                if reward["game_mode"] == "creative":
                    self.can_fly = True
            if "can_fly" in reward:
                self.can_fly = reward["can_fly"]
            if "flying" in reward:
                self.flying = reward["flying"]
            if "speed" in reward:
                self.camera["speed"] = reward["speed"]
            if "fly_speed" in reward:
                self.fly_speed = reward["fly_speed"]
            if "jump_power" in reward:
                self.velocity[1] = reward["jump_power"]
            
            for effect_name, effect_value in reward.items():
                if effect_name in self.active_cheat_effects:
                    self.active_cheat_effects[effect_name] = effect_value
            
            if "generals" in reward:
                for general in reward["generals"]:
                    self.add_item_to_inventory(f"{general}卡", 1)
                    self.add_chat_message(f"⚔️ 获得 {general} 武将卡！")
            
            if "secret_items" in reward:
                for item in reward["secret_items"]:
                    self.add_item_to_inventory(item, 1)
                    self.add_chat_message(f"🎁 获得 {item}！")
            
            if "eggs_unlocked" in reward:
                unlocked_count = 0
                for egg_id in self.eggs:
                    if not self.eggs[egg_id]["found"]:
                        self.eggs[egg_id]["found"] = True
                        unlocked_count += 1
                        if unlocked_count >= reward["eggs_unlocked"]:
                            break
                self.add_chat_message(f"🥚 解锁了 {unlocked_count} 个彩蛋！")
            
            if "all_achievements" in reward and reward["all_achievements"]:
                for achievement in self.achievements:
                    self.achievements[achievement]["unlocked"] = True
                self.add_chat_message("🏆 所有成就已解锁！")
            
            if "all_eggs" in reward and reward["all_eggs"]:
                for egg_id in self.eggs:
                    self.eggs[egg_id]["found"] = True
                self.add_chat_message("🥚 所有彩蛋已解锁！")
            
            if "full_inventory" in reward and reward["full_inventory"]:
                for item_type in self.item_types:
                    for item in self.item_types[item_type]:
                        self.add_item_to_inventory(item, 64)
                self.add_chat_message("📦 背包已填满所有物品！")
            
            if "random" in reward and reward["random"]:
                random_rewards = [
                    {"health": 100, "message": "💖 随机奖励：恢复生命！"},
                    {"experience": 1000, "message": "⭐ 随机奖励：获得经验！"},
                    {"item": "神秘宝箱", "message": "🎁 随机奖励：神秘宝箱！"},
                    {"speed": 2.0, "message": "⚡ 随机奖励：速度提升！"},
                    {"egg_unlock": True, "message": "🥚 随机奖励：解锁一个彩蛋！"}
                ]
                chosen = random.choice(random_rewards)
                if "health" in chosen:
                    self.health = min(self.health + chosen["health"], self.max_health * 10)
                if "experience" in chosen:
                    self.experience += chosen["experience"]
                if "item" in chosen:
                    self.add_item_to_inventory(chosen["item"], 1)
                if "speed" in chosen:
                    self.camera["speed"] = chosen["speed"]
                if "egg_unlock" in chosen:
                    for egg_id in self.eggs:
                        if not self.eggs[egg_id]["found"]:
                            self.eggs[egg_id]["found"] = True
                            break
                self.add_chat_message(chosen["message"])
            
            if "pet" in reward:
                self.add_chat_message(f"🐉 获得宠物：{reward['pet']}！")
            
            if "weather_control" in reward and reward["weather_control"]:
                self.add_chat_message("🌤️ 天气控制已激活！使用 /weather 命令")
            
            if "time_control" in reward and reward["time_control"]:
                self.add_chat_message("⏰ 时间控制已激活！使用 /time 命令")
            
            if "developer_mode" in reward and reward["developer_mode"]:
                self.active_cheat_effects["developer_mode"] = True
                self.add_chat_message("🔧 开发者模式已激活！")
                self.add_chat_message("可用隐藏命令: /dev, /spawn, /effect")
            
            if "particle_effects" in reward and reward["particle_effects"]:
                self.spawn_effect_particle(self.player_pos[0], self.player_pos[1] + 2, self.player_pos[2], "magic")
            
            self.cheat_stats["total_rewards"] += 1
            
            egg_key = f"cheat_{code_id}"
            if egg_key not in self.eggs:
                self.eggs[egg_key] = {"found": False, "hint": f"输入作弊码: {code_data['name']}"}
            if not self.eggs[egg_key]["found"]:
                self.eggs[egg_key]["found"] = True
                self.add_chat_message(f"🎉 解锁彩蛋: {code_data['name']}！")
            
            self.spawn_effect_particle(self.player_pos[0], self.player_pos[1] + 2, self.player_pos[2], "enchant")
            
        except Exception as e:
            logger.info(f"[错误] 激活作弊码失败: {e}")
            self.add_chat_message(f"❌ 作弊码激活失败: {str(e)}")
    
    def check_secret_location_triggers(self):
        """检测特定位置触发彩蛋"""
        try:
            for loc_id, loc_data in self.secret_locations.items():
                pos = loc_data["pos"]
                radius = loc_data["radius"]
                
                distance = math.sqrt(
                    (self.player_pos[0] - pos[0]) ** 2 +
                    (self.player_pos[1] - pos[1]) ** 2 +
                    (self.player_pos[2] - pos[2]) ** 2
                )
                
                if distance <= radius:
                    egg_id = loc_data["egg"]
                    if not self.eggs.get(egg_id, {}).get("found", False):
                        self.eggs[egg_id]["found"] = True
                        self.add_chat_message(f"📍 {loc_data['message']}")
                        self.spawn_effect_particle(pos[0], pos[1] + 2, pos[2], "magic")
                        
        except Exception as e:
            logger.info(f"[错误] 检测位置彩蛋失败: {e}")
    
    def draw_command_input(self):
        """绘制命令输入框"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        input_width = 400
        input_height = 30
        input_x = SCREEN_WIDTH // 2 - input_width // 2
        input_y = SCREEN_HEIGHT - 50
        
        input_bg = pygame.Surface((input_width, input_height), pygame.SRCALPHA)
        input_bg.fill((0, 0, 0, 200))
        pygame.draw.rect(input_bg, (50, 50, 50), (0, 0, input_width, input_height), 1)
        self.screen.blit(input_bg, (input_x, input_y))
        
        cmd_text = self.font_main.render("/" + self.command_input, True, (255, 255, 255))
        self.screen.blit(cmd_text, (input_x + 5, input_y + 5))
        
        glEnable(GL_DEPTH_TEST)
    
    def draw_crafting_table(self):
        """绘制合成台界面（MC风格）"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        craft_width = 400
        craft_height = 350
        craft_x = SCREEN_WIDTH // 2 - craft_width // 2
        craft_y = SCREEN_HEIGHT // 2 - craft_height // 2
        
        bg_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        self.screen.blit(bg_surf, (0, 0))
        
        craft_surf = pygame.Surface((craft_width, craft_height), pygame.SRCALPHA)
        craft_surf.fill((60, 60, 80, 240))
        pygame.draw.rect(craft_surf, (100, 100, 120), (0, 0, craft_width, craft_height), 3, border_radius=10)
        self.screen.blit(craft_surf, (craft_x, craft_y))
        
        title_surf = self.font_main.render("合成台", True, COLORS["accent_gold"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, craft_y + 25))
        self.screen.blit(title_surf, title_rect)
        
        slot_size = 50
        slot_spacing = 5
        
        grid_x = craft_x + 30
        grid_y = craft_y + 50
        
        for row in range(3):
            for col in range(3):
                slot_x = grid_x + col * (slot_size + slot_spacing)
                slot_y = grid_y + row * (slot_size + slot_spacing)
                
                slot_surf = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
                slot_surf.fill((50, 50, 70, 255))
                pygame.draw.rect(slot_surf, (80, 80, 100), (0, 0, slot_size, slot_size), 2)
                self.screen.blit(slot_surf, (slot_x, slot_y))
                
                item = self.crafting_grid[row][col]
                if item:
                    item_color = self.get_item_color(item)
                    item_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
                    item_surf.fill(item_color)
                    self.screen.blit(item_surf, (slot_x + 5, slot_y + 5))
        
        arrow_x = grid_x + 3 * (slot_size + slot_spacing) + 20
        arrow_y = craft_y + craft_height // 2 - 20
        
        arrow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.polygon(arrow_surf, (255, 215, 0), [(35, 20), (5, 5), (5, 35)])
        self.screen.blit(arrow_surf, (arrow_x, arrow_y))
        
        result_x = arrow_x + 60
        result_y = craft_y + craft_height // 2 - slot_size // 2
        
        result_slot = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
        result_slot.fill((50, 70, 50, 255))
        pygame.draw.rect(result_slot, COLORS["accent_green"], (0, 0, slot_size, slot_size), 2)
        self.screen.blit(result_slot, (result_x, result_y))
        
        if self.crafting_result:
            result_color = self.get_item_color(self.crafting_result)
            result_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            result_surf.fill(result_color)
            self.screen.blit(result_surf, (result_x + 5, result_y + 5))
        
        hint_surf = self.font_small.render("拖拽物品到格子中 | C: 关闭", True, (150, 150, 150))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, craft_y + craft_height - 20))
        self.screen.blit(hint_surf, hint_rect)
        
        glEnable(GL_DEPTH_TEST)
    
    def handle_crafting_input(self):
        """处理合成台输入"""
        craft_width = 400
        craft_height = 350
        craft_x = SCREEN_WIDTH // 2 - craft_width // 2
        craft_y = SCREEN_HEIGHT // 2 - craft_height // 2
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_c:
                    self.show_crafting = False
                    self.is_mouse_locked = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                slot_size = 50
                slot_spacing = 5
                grid_x = craft_x + 30
                grid_y = craft_y + 50
                
                for row in range(3):
                    for col in range(3):
                        slot_x = grid_x + col * (slot_size + slot_spacing)
                        slot_y = grid_y + row * (slot_size + slot_spacing)
                        
                        if slot_x <= mx <= slot_x + slot_size and slot_y <= my <= slot_y + slot_size:
                            if event.button == 1:
                                if self.dragging_item:
                                    self.crafting_grid[row][col] = self.dragging_item["name"]
                                    self.dragging_item = None
                                else:
                                    item = self.crafting_grid[row][col]
                                    if item:
                                        self.dragging_item = {"name": item, "count": 1}
                                        self.crafting_grid[row][col] = None
                            
                result_x = grid_x + 3 * (slot_size + slot_spacing) + 80
                result_y = craft_y + craft_height // 2 - slot_size // 2
                
                if result_x <= mx <= result_x + slot_size and result_y <= my <= result_y + slot_size:
                    if self.crafting_result:
                        self.craft_item()
        
        self.check_crafting()
        return "continue"
    
    def check_crafting(self):
        """检查合成配方"""
        items = {}
        for row in self.crafting_grid:
            for item in row:
                if item:
                    items[item] = items.get(item, 0) + 1
        
        for result, recipe in self.crafting_recipes.items():
            match = True
            for item, count in recipe.items():
                if items.get(item, 0) < count:
                    match = False
                    break
            
            if match:
                self.crafting_result = result
                return
        
        self.crafting_result = None
    
    def craft_item(self):
        """执行合成（安全版本）"""
        if not self.crafting_result:
            return
        
        recipe = self.crafting_recipes.get(self.crafting_result)
        if not recipe:
            return
        
        for item, count in recipe.items():
            if not self.remove_item_from_inventory(item, count):
                self.message = f"材料不足: {item}"
                self.message_timer = 2000
                return
        
        for item, count in recipe.items():
            for _ in range(count):
                found = False
                for row in range(3):
                    for col in range(3):
                        if self.crafting_grid[row][col] == item:
                            self.crafting_grid[row][col] = None
                            found = True
                            break
                    if found:
                        break
        
        self.add_item_to_inventory(self.crafting_result)
        self.message = f"合成了 {self.crafting_result}！"
        self.message_timer = 2000
        self.check_crafting()
    
    def main(self):
        """主循环"""
        if not self.initialize():
            return
        
        running = True
        while running:
            if self.is_paused:
                result = self.handle_pause_input()
                if result == "quit":
                    running = False
                elif result == "main_menu":
                    return "main_menu"
                
                self.draw_3d_scene()
                self.draw_pause_menu()
                pygame.display.flip()
                self.clock.tick(60)
                continue
            
            if self.show_inventory:
                result = self.handle_inventory_input()
                if result == "quit":
                    running = False
                
                self.draw_3d_scene()
                self.draw_inventory()
                pygame.display.flip()
                self.clock.tick(60)
                continue
            
            if self.show_crafting:
                result = self.handle_crafting_input()
                if result == "quit":
                    running = False
                
                self.draw_3d_scene()
                self.draw_crafting_table()
                pygame.display.flip()
                self.clock.tick(60)
                continue
            
            running = self.handle_input()
            
            if self.show_command:
                self.draw_3d_scene()
                self.draw_command_input()
                pygame.display.flip()
                self.clock.tick(60)
                continue
            
            # 物理更新
            if not self.flying:
                self.velocity[1] += self.gravity
            
            self.handle_flying()
            
            # 🎮 作弊码位置彩蛋检测
            self.check_secret_location_triggers()
            
            # 更新位置
            self.player_pos[0] += self.velocity[0]
            self.player_pos[1] += self.velocity[1]
            self.player_pos[2] += self.velocity[2]
            
            # 地面碰撞检测
            if self.player_pos[1] < 0:
                self.player_pos[1] = 0
                self.velocity[1] = 0
            
            # 建筑碰撞检测
            player_radius = 0.8
            player_height = 2.0
            for loc in self.locations:
                if "collision_box" in loc:
                    box = loc["collision_box"]
                    px, py, pz = self.player_pos[0], self.player_pos[1], self.player_pos[2]
                    
                    inside_x = box["min_x"] - player_radius < px < box["max_x"] + player_radius
                    inside_z = box["min_z"] - player_radius < pz < box["max_z"] + player_radius
                    inside_vertical = 0 < py < box["max_y"]
                    
                    if inside_x and inside_z and inside_vertical:
                        overlap_left = px - (box["min_x"] - player_radius)
                        overlap_right = (box["max_x"] + player_radius) - px
                        overlap_front = pz - (box["min_z"] - player_radius)
                        overlap_back = (box["max_z"] + player_radius) - pz
                        
                        min_overlap = min(overlap_left, overlap_right, overlap_front, overlap_back)
                        
                        if min_overlap == overlap_left:
                            self.player_pos[0] = box["min_x"] - player_radius
                            self.velocity[0] = 0
                        elif min_overlap == overlap_right:
                            self.player_pos[0] = box["max_x"] + player_radius
                            self.velocity[0] = 0
                        elif min_overlap == overlap_front:
                            self.player_pos[2] = box["min_z"] - player_radius
                            self.velocity[2] = 0
                        elif min_overlap == overlap_back:
                            self.player_pos[2] = box["max_z"] + player_radius
                            self.velocity[2] = 0
            
            # 摩擦力
            self.velocity[0] *= 0.9
            self.velocity[2] *= 0.9
            
            # 更新昼夜系统
            self.update_day_night()
            
            # 更新天气系统
            self.update_weather()
            
            # 更新粒子系统
            self.update_effect_particles()
            self.update_dust_particles()
            
            # 更新生物系统
            self.spawn_entity()
            self.update_entities()
            
            # 更新Herobrine彩蛋
            self.update_herobrine()
            
            # 检测彩蛋触发
            self.check_egg_triggers()
            
            # 更新海浪效果
            self.update_waves()
            
            # 更新相机
            self.update_camera()
            
            # 自动存档
            current_time = time.time()
            if current_time - self.last_auto_save_time >= self.auto_save_interval:
                self.save_mc_world_data()
                self.last_auto_save_time = current_time
                self.add_chat_message("游戏已自动保存")
            
            # 更新跟随者
            self.update_followers()
            
            # 绘制3D场景
            self.draw_3d_scene()
            
            # 绘制HUD
            self.draw_mc_hud()
            self.draw_hotbar()
            
            # 限制帧率
            self.clock.tick(60)
        
        self.save_mc_world_data()

def main():
    """3D地图主函数"""
    game_map_3d = GameMap3D()
    game_map_3d.main()

if __name__ == "__main__":
    main()