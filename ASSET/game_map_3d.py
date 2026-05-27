import pygame
import math
import random
import json
import os
import time
from ASSET.game_data import data, save, get_system_font_name, load_sound
from ASSET import safe_exit

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
                    self.camera["mode"] = "third" if self.camera["mode"] == "first" else "first"
                    self.message = f"切换到{'第三人称' if self.camera['mode'] == 'third' else '第一人称'}视角"
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
                    self.message = "物品栏功能开发中..."
                    self.message_timer = 2000
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
    
    def update_camera(self):
        """更新相机位置"""
        yaw_rad = math.radians(self.camera["yaw"])
        pitch_rad = math.radians(self.camera["pitch"])
        
        if self.camera["mode"] == "first":
            # 第一人称视角：相机位置与玩家位置相同
            # 但稍微偏移到玩家前方
            distance = 0.5
            self.camera["x"] = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 1.5 + math.sin(pitch_rad) * distance  # 眼睛高度
            self.camera["z"] = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * distance
        else:
            # 第三人称视角：相机位于玩家背后
            distance = 5.0
            self.camera["x"] = self.player_pos[0] - math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 2.0 - math.sin(pitch_rad) * distance  # 相机高度
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
            
            self.draw_terrain()
            
            if hasattr(self, 'trees'):
                for tree_x, tree_z in self.trees:
                    self.draw_tree(tree_x, tree_z)
            
            for loc in self.locations:
                self.draw_location(loc)
            
            if self.camera["mode"] == "third":
                self.draw_player()
            
            for follower in self.followers:
                self.draw_follower(follower)
            
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
            "Shift: 减速",
            "Tab: 锁定鼠标",
            "F: 跟随模式",
            "F5: 切换视角",
            "1-9: 选择方块",
            "左键: 放置方块",
            "右键: 破坏方块",
            "Esc: 暂停菜单"
        ]
        for i, control in enumerate(controls):
            ctrl_surf = self.font_small.render(control, True, COLORS["text_white"])
            self.screen.blit(ctrl_surf, (SCREEN_WIDTH - 150, 10 + i * 25))
        
        self.draw_hotbar()
        
        glEnable(GL_DEPTH_TEST)
    
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
            
            # 更新相机
            self.update_camera()
            
            # 更新跟随者
            self.update_followers()
            
            # 绘制3D场景
            self.draw_3d_scene()
            
            # 绘制HUD
            self.draw_hud()
            
            # 限制帧率
            self.clock.tick(60)
        
        pygame.quit()

def main():
    """3D地图主函数"""
    game_map_3d = GameMap3D()
    game_map_3d.main()

if __name__ == "__main__":
    main()