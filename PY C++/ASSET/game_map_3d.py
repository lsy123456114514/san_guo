import pygame
import math
import random
import json
import os
import time
from ASSET.game_data import data, save, get_system_font_name, load_sound
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
    print(f"无法加载C++渲染器: {e}")
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
        
        # 物品类型定义
        self.item_types = {
            "方块类": ["泥土", "石头", "木头", "草地", "沙子", "水", "玻璃", "砖块"],
            "资源类": ["水", "煤炭", "木头", "食物", "金元宝", "时间卡", "宠物食物"],
            "武器类": ["手枪", "步枪", "狙击枪", "机枪", "弓", "弩"],
            "弹药类": ["普通子弹", "高级子弹", "稀有子弹", "箭矢"],
            "武将卡": ["刘备卡", "关羽卡", "张飞卡", "赵云卡", "诸葛亮卡", "曹操卡"],
            "食物类": ["面包", "苹果", "烤肉", "药草", "零食"],
            "工具类": ["镐子", "斧头", "铲子", "锄头", "钓鱼竿"],
            "材料类": ["铁锭", "铜锭", "金锭", "皮革", "布料"]
        }
        
        # 背包界面状态
        self.inventory_selected_slot = -1
        self.dragging_item = None
        self.drag_source = None
        self.inventory_category = "全部"
        
        # 合成系统（完整MC风格配方）
        self.crafting_recipes = {
            # 工具
            "木头镐子": {"木头": 3, "木棍": 2},
            "石头镐子": {"圆石": 3, "木棍": 2},
            "铁镐": {"铁锭": 3, "木棍": 2},
            "木头斧头": {"木头": 3, "木棍": 2},
            "石头斧头": {"圆石": 3, "木棍": 2},
            "铁斧": {"铁锭": 3, "木棍": 2},
            "木头铲子": {"木头": 1, "木棍": 2},
            "石头铲子": {"圆石": 1, "木棍": 2},
            "铁铲": {"铁锭": 1, "木棍": 2},
            "木头锄": {"木头": 2, "木棍": 2},
            "石头锄": {"圆石": 2, "木棍": 2},
            "铁锄": {"铁锭": 2, "木棍": 2},
            # 武器
            "木剑": {"木头": 2, "木棍": 1},
            "石剑": {"圆石": 2, "木棍": 1},
            "铁剑": {"铁锭": 2, "木棍": 1},
            "弓": {"线": 3, "木棍": 3},
            # 建筑
            "木板": {"木头": 1},
            "木棍": {"木板": 2},
            "砖块": {"粘土": 4},
            "玻璃": {"沙子": 1},
            "梯子": {"木棍": 7},
            "门": {"木板": 6},
            "栅栏": {"木棍": 4},
            # 食物
            "面包": {"小麦": 3},
            "蛋糕": {"小麦": 3, "鸡蛋": 2, "牛奶": 1, "糖": 1},
            # 材料
            "铁锭": {"铁矿石": 1, "煤炭": 1},
            "金锭": {"金矿石": 1, "煤炭": 1},
            "线": {"羊毛": 1},
            "纸": {"甘蔗": 3},
            "书": {"纸": 3, "皮革": 1},
            # 三国特色
            "武将召唤台": {"金锭": 4, "木头": 4, "武将卡": 1},
            "武器架": {"木头": 6},
            "弹药箱": {"木头": 8, "铁锭": 2}
        }
        
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
        
        # 天气系统
        self.weather = "clear"  # clear, rain, snow
        self.weather_timer = 0
        self.rain_particles = []
        self.snow_particles = []
        
        # 生物系统
        self.entities = []  # 存储所有实体
        self.monsters = []  # 怪物
        self.animals = []   # 动物
        self.spawn_timer = 0
        
        # 方块颜色定义 (MC风格)
        self.block_colors = {
            "泥土": (0.6, 0.4, 0.2),
            "石头": (0.5, 0.5, 0.5),
            "木头": (0.5, 0.35, 0.15),
            "草地": (0.3, 0.8, 0.2),
            "沙子": (0.9, 0.85, 0.6),
            "水": (0.2, 0.4, 0.8, 0.7),
            "玻璃": (0.8, 0.9, 1.0, 0.4),
            "砖块": (0.8, 0.3, 0.2),
            "树叶": (0.2, 0.6, 0.15),
            "橡木": (0.6, 0.4, 0.2),
            "圆石": (0.45, 0.45, 0.45),
            "铁矿石": (0.55, 0.5, 0.5),
            "煤炭": (0.2, 0.2, 0.2),
            "金矿石": (0.8, 0.7, 0.3)
        }
        
    def initialize(self):
        """初始化3D地图"""
        if not opengl_available:
            print("错误: OpenGL不可用，无法启动3D地图")
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
                    self.font_main = pygame.font.SysFont(font_name, 40)
                    self.font_small = pygame.font.SysFont(font_name, 24)
                else:
                    self.font_main = pygame.font.Font(None, 40)
                    self.font_small = pygame.font.Font(None, 24)
            except Exception:
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
            print(f"初始化错误: {e}")
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
                print("错误: 未登录，无法加载地图数据")
                return
            
            map_path = self.get_map_data_path()
            if not os.path.exists(map_path):
                print("地图数据文件不存在，将生成新地图")
                self.locations = self.generate_locations(MAX_LOCATIONS)
                self.save_map_data(self.locations)
            else:
                with open(map_path, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                
                # 验证用户名
                if map_data.get("username") != username:
                    print("错误: 地图数据与当前用户不匹配")
                    return
                
                self.locations = map_data.get("locations", [])
                print(f"成功加载地图数据，包含 {len(self.locations)} 个地点")
        except Exception as e:
            print(f"加载地图数据失败: {e}")
            self.locations = self.generate_locations(MAX_LOCATIONS)
            self.save_map_data(self.locations)
    
    def get_map_data_path(self):
        """获取地图数据路径"""
        username = data.get("username", "")
        safe_username = username.replace('\\', '_').replace('/', '_').replace(':', '_')
        return f"map_data_{safe_username}.json"
    
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
            print(f"保存地图数据失败: {e}")
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
                
                # 加载MC状态
                self.health = mc_world.get("health", 20)
                self.hunger = mc_world.get("hunger", 20)
                self.oxygen = mc_world.get("oxygen", 10)
                self.experience = mc_world.get("experience", 0)
                self.level = mc_world.get("level", 0)
                self.armor = mc_world.get("armor", 0)
                
                self.update_camera()
                self.validate_all()
                print(f"加载MC世界数据成功: {len(self.placed_blocks)} 个方块")
        except Exception as e:
            print(f"加载MC世界数据失败: {e}")
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
            print(f"保存MC世界数据成功: {len(self.placed_blocks)} 个方块")
        except Exception as e:
            print(f"保存MC世界数据失败: {e}")
    
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
            print(f"C++渲染错误: {e}")
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
            
            self.draw_weather()
            
            pygame.display.flip()
        except Exception as e:
            print(f"Python渲染错误: {e}")
    
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
            print(f"绘制地形错误: {e}")
    
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
            print(f"绘制放置方块错误: {e}")
    
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
            pass
    
    def update_weather(self):
        """更新天气系统"""
        self.weather_timer += 1
        
        if self.weather_timer > 3000:
            self.weather_timer = 0
            rand = random.random()
            if rand < 0.3:
                self.weather = "rain"
            elif rand < 0.4:
                self.weather = "snow"
            else:
                self.weather = "clear"
        
        if self.weather == "rain":
            for _ in range(5):
                if len(self.rain_particles) < 500:
                    self.rain_particles.append({
                        "x": random.uniform(self.player_pos[0] - 100, self.player_pos[0] + 100),
                        "y": 50 + random.uniform(0, 20),
                        "z": random.uniform(self.player_pos[2] - 100, self.player_pos[2] + 100),
                        "speed": random.uniform(8, 12)
                    })
            
            self.rain_particles = [p for p in self.rain_particles if p["y"] > -5]
            for p in self.rain_particles:
                p["y"] -= p["speed"] * 0.1
                p["x"] += 0.5
        
        elif self.weather == "snow":
            for _ in range(3):
                if len(self.snow_particles) < 300:
                    self.snow_particles.append({
                        "x": random.uniform(self.player_pos[0] - 100, self.player_pos[0] + 100),
                        "y": 50 + random.uniform(0, 20),
                        "z": random.uniform(self.player_pos[2] - 100, self.player_pos[2] + 100),
                        "speed": random.uniform(2, 4),
                        "drift_x": random.uniform(-1, 1),
                        "drift_z": random.uniform(-1, 1)
                    })
            
            self.snow_particles = [p for p in self.snow_particles if p["y"] > -5]
            for p in self.snow_particles:
                p["y"] -= p["speed"] * 0.05
                p["x"] += p["drift_x"] * 0.1
                p["z"] += p["drift_z"] * 0.1
    
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
            pass
    
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
            
            if animal["x"] < self.player_pos[0] - 100 or animal["x"] > self.player_pos[0] + 100:
                self.animals.remove(animal)
                break
        
        for monster in self.monsters:
            dx = self.player_pos[0] - monster["x"]
            dz = self.player_pos[2] - monster["z"]
            monster["direction"] = math.degrees(math.atan2(dz, dx))
            monster["x"] += math.cos(math.radians(monster["direction"])) * monster["speed"]
            monster["z"] += math.sin(math.radians(monster["direction"])) * monster["speed"]
            
            if monster["x"] < self.player_pos[0] - 100 or monster["x"] > self.player_pos[0] + 100:
                self.monsters.remove(monster)
                break
    
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
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            pass
    
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
            print(f"绘制树木错误: {e}")
    
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
            print(f"绘制地点错误: {e}")
    
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
            print(f"绘制玩家错误: {e}")
    
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
            print(f"绘制跟随者错误: {e}")
    
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
        except Exception:
            pass
        
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
            
            # 物理更新
            # 应用重力
            self.velocity[1] += self.gravity
            
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
            
            # 更新生物系统
            self.spawn_entity()
            self.update_entities()
            
            # 更新相机
            self.update_camera()
            
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
        pygame.quit()

def main():
    """3D地图主函数"""
    game_map_3d = GameMap3D()
    game_map_3d.main()

if __name__ == "__main__":
    main()