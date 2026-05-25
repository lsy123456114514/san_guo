import pygame
import math
import random
import json
import os
import time
from ASSET.game_data import data, save, get_system_font_name, load_sound
from ASSET import safe_exit

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    opengl_available = True
except ImportError:
    opengl_available = False

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

MAP_SIZE = (2000, 2000)
MAX_LOCATIONS = 50
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

class GameMap3D:
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
            "pitch": -20,
            "yaw": 0,
            "speed": 0.5,
            "mode": "first"
        }
        self.mouse_sensitivity = 0.05
        self.is_mouse_locked = False
        self.followers = []
        self.follow_target = None
        self.message = None
        self.message_timer = 0
        self.velocity = [0, 0, 0]
        self.gravity = -0.35
        self.friction = 0.85
        self.npcs = []
        self.selected_npc = None
        self.npc_interaction_distance = 8
        self.large_structures = []
        self.render_cache = {}
        self.cache_valid = False
        self.selected_location = None
        self.owned_territories = []
        self.trees = []

    def initialize(self):
        if not opengl_available:
            print("错误: OpenGL不可用，无法启动3D地图")
            return False
        
        try:
            pygame.init()
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
            self.screen = pygame.display.get_surface()
            self.clock = pygame.time.Clock()
            
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glClearColor(0.1, 0.1, 0.2, 1.0)
            
            light_position = [1.0, 1.0, 1.0, 0.0]
            glLightfv(GL_LIGHT0, GL_POSITION, light_position)
            
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
            
            self.load_map_data()
            self.load_owned_territories()
            self.show_performance_warning()
            
            if self.locations:
                first_loc = self.locations[0]
                self.player_pos = [first_loc["x"] + 50, 2, first_loc["y"] + 50]
                self.update_camera()
            
            self.generate_trees()
            self.generate_large_structures()
            self.generate_npcs()
            self.cache_terrain()
            
            return True
        except Exception as e:
            print(f"初始化错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_performance_warning(self):
        warning = "3D主城 - 按右键与NPC交互 | E进入地点 | R收集资源"
        text_surf = self.font_main.render(warning, True, COLORS["accent_gold"])
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        bg_rect = pygame.Rect(text_rect.x-20, text_rect.y-10, text_rect.width+40, text_rect.height+20)
        pygame.draw.rect(self.screen, (30, 30, 55, 200), bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["accent_gold"], bg_rect, 2, border_radius=10)
        
        self.screen.blit(text_surf, text_rect)
        pygame.display.flip()
        pygame.time.wait(2000)
    
    def load_map_data(self):
        try:
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
                
                if map_data.get("username") != username:
                    print("错误: 地图数据与当前用户不匹配")
                    return
                
                self.locations = map_data.get("locations", [])
                print(f"成功加载地图数据，包含 {len(self.locations)} 个地点")
        except Exception as e:
            print(f"加载地图数据失败: {e}")
            self.locations = self.generate_locations(MAX_LOCATIONS)
            self.save_map_data(self.locations)
    
    def load_owned_territories(self):
        try:
            self.owned_territories = data.get('territory', {}).get('owned_territories', [])
            print(f"已加载 {len(self.owned_territories)} 个占领地点")
        except Exception as e:
            print(f"加载占领数据失败: {e}")
            self.owned_territories = []
    
    def get_map_data_path(self):
        username = data.get("username", "")
        safe_username = username.replace('\\', '_').replace('/', '_').replace(':', '_')
        return f"map_data_{safe_username}.json"
    
    def save_map_data(self, locations):
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
        locations = []
        LOCATION_TYPES = {
            "关隘": {"icon": "🏯", "power": 100, "color": (0.6, 0.55, 0.5)},
            "军营": {"icon": "⚔️", "power": 150, "color": (0.7, 0.2, 0.2)},
            "村庄": {"icon": "🏠", "power": 50, "color": (0.85, 0.75, 0.55)},
            "矿山": {"icon": "⛏️", "power": 80, "color": (0.5, 0.5, 0.45)},
            "港口": {"icon": "🚢", "power": 90, "color": (0.25, 0.55, 0.75)},
            "城池": {"icon": "🏰", "power": 200, "color": (0.65, 0.45, 0.35)},
            "驿站": {"icon": "🏇", "power": 60, "color": (0.6, 0.5, 0.4)},
            "集市": {"icon": "🏪", "power": 70, "color": (0.75, 0.6, 0.4)}
        }
        
        for i in range(count):
            while True:
                x = random.randint(100, MAP_SIZE[0] - 100)
                y = random.randint(100, MAP_SIZE[1] - 100)
                
                valid = True
                for loc in locations:
                    distance = math.hypot(x - loc["x"], y - loc["y"])
                    if distance < 150:
                        valid = False
                        break
                if valid:
                    break
            
            loc_type = random.choice(list(LOCATION_TYPES.keys()))
            level = random.randint(1, 10)
            power = int(LOCATION_TYPES[loc_type]["power"] * (0.5 + level * 0.1))
            
            is_owned = loc_type in self.owned_territories or random.random() < 0.2
            
            locations.append({
                "x": x,
                "y": y,
                "type": loc_type,
                "level": level,
                "desc": LOCATION_TYPES[loc_type]["icon"],
                "power": power,
                "owner": "player" if is_owned else ("enemy" if loc_type == "军营" else "neutral"),
                "color": LOCATION_TYPES[loc_type]["color"]
            })
        
        return locations
    
    def generate_trees(self):
        self.trees = []
        tree_count = 300
        
        for _ in range(tree_count):
            x = random.randint(-1800, 1800)
            z = random.randint(-1800, 1800)
            
            too_close = False
            for loc in self.locations:
                if math.hypot(x - loc["x"], z - loc["y"]) < 40:
                    too_close = True
                    break
            for tree in self.trees:
                if math.hypot(x - tree[0], z - tree[1]) < 8:
                    too_close = True
                    break
            
            if not too_close:
                self.trees.append((x, z, random.uniform(0.8, 1.5)))
    
    def generate_large_structures(self):
        self.large_structures = []
        
        STRUCTURE_TYPES = [
            {"name": "皇宫", "size": 30, "height": 25, "color": (0.8, 0.7, 0.2), "icon": "🏛️"},
            {"name": "城墙", "size": 60, "height": 12, "color": (0.5, 0.5, 0.5), "icon": "🧱"},
            {"name": "塔楼", "size": 15, "height": 30, "color": (0.6, 0.5, 0.4), "icon": "🗼"},
            {"name": "神庙", "size": 20, "height": 18, "color": (0.7, 0.6, 0.5), "icon": "⛩️"},
            {"name": "仓库", "size": 25, "height": 10, "color": (0.6, 0.4, 0.3), "icon": "🏭"}
        ]
        
        for _ in range(8):
            while True:
                x = random.randint(-1500, 1500)
                z = random.randint(-1500, 1500)
                
                too_close = False
                for struct in self.large_structures:
                    if math.hypot(x - struct["x"], z - struct["z"]) < 200:
                        too_close = True
                        break
                if not too_close:
                    break
            
            struct_type = random.choice(STRUCTURE_TYPES)
            self.large_structures.append({
                "x": x,
                "z": z,
                **struct_type
            })
    
    def generate_npcs(self):
        self.npcs = []
        
        NPC_TYPES = [
            {"name": "武将招募官", "dialogue": "欢迎来到主城！需要招募武将吗？", "action": "hero_recruit", "module": "hero_recruitment.py", "color": (0.2, 0.6, 0.8)},
            {"name": "商人", "dialogue": "欢迎光临！我这里有各种珍贵物品。", "action": "shop", "module": "shop_system.py", "color": (0.8, 0.6, 0.2)},
            {"name": "任务发布者", "dialogue": "勇士，我有一个危险的任务...", "action": "quest", "module": "quest_system.py", "color": (0.6, 0.3, 0.8)},
            {"name": "铁匠", "dialogue": "需要打造或强化装备吗？", "action": "equipment", "module": "equipment_system.py", "color": (0.5, 0.5, 0.5)},
            {"name": "药师", "dialogue": "我可以帮你炼制药剂。", "action": "alchemy", "module": "alchemy_system.py", "color": (0.3, 0.7, 0.3)},
            {"name": "史官", "dialogue": "想听三国的故事吗？", "action": "story", "module": "background_story.py", "color": (0.7, 0.5, 0.3)},
            {"name": "军需官", "dialogue": "需要补给吗？金元宝、时间卡应有尽有！", "action": "resources", "module": "shop_system.py", "color": (0.2, 0.5, 0.8)},
            {"name": "竞技场管理员", "dialogue": "想参加PVP竞技吗？", "action": "pvp", "module": "pvp_p2p.py", "color": (0.8, 0.3, 0.3)}
        ]
        
        for npc_type in NPC_TYPES:
            while True:
                x = random.randint(-500, 500)
                z = random.randint(-500, 500)
                
                too_close = False
                for npc in self.npcs:
                    if math.hypot(x - npc["x"], z - npc["z"]) < 50:
                        too_close = True
                        break
                if not too_close:
                    break
            
            self.npcs.append({
                "x": x,
                "z": z,
                "y": 0,
                **npc_type,
                "animation_offset": random.uniform(0, math.pi * 2),
                "move_dir": random.uniform(0, math.pi * 2),
                "move_speed": random.uniform(0.3, 0.8),
                "original_x": x,
                "original_z": z,
                "wander_range": 15
            })
    
    def cache_terrain(self):
        self.render_cache = {
            "trees": [],
            "locations": [],
            "structures": [],
            "npcs": []
        }
        
        for tree in self.trees:
            x, z, scale = tree
            self.render_cache["trees"].append({
                "x": x,
                "z": z,
                "scale": scale
            })
        
        for loc in self.locations:
            self.render_cache["locations"].append({
                "x": loc["x"],
                "y": loc["y"],
                "type": loc["type"],
                "color": loc["color"],
                "owner": loc["owner"],
                "level": loc["level"]
            })
        
        for struct in self.large_structures:
            self.render_cache["structures"].append({
                "x": struct["x"],
                "z": struct["z"],
                "size": struct["size"],
                "height": struct["height"],
                "color": struct["color"],
                "name": struct["name"]
            })
        
        self.cache_valid = True
        print("地形缓存已生成")
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        move_speed = self.camera["speed"] * (0.4 if keys[pygame.K_LSHIFT] else 1.0)
        
        if keys[pygame.K_w]:
            self.move_forward(move_speed)
        if keys[pygame.K_s]:
            self.move_backward(move_speed)
        if keys[pygame.K_a]:
            self.move_left(move_speed)
        if keys[pygame.K_d]:
            self.move_right(move_speed)
        if keys[pygame.K_SPACE]:
            if self.player_pos[1] <= 0.5:
                self.velocity[1] = 6.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.is_mouse_locked:
                        self.is_mouse_locked = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        return False
                elif event.key == pygame.K_TAB:
                    self.is_mouse_locked = not self.is_mouse_locked
                    pygame.mouse.set_visible(not self.is_mouse_locked)
                    pygame.event.set_grab(self.is_mouse_locked)
                elif event.key == pygame.K_f:
                    if self.follow_target:
                        self.follow_target = None
                        self.message = "取消跟随"
                    else:
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
                elif event.key == pygame.K_g:
                    self.gravity = -0.35 if self.gravity != -0.35 else -0.2
                    self.message = f"引力: {'正常' if self.gravity == -0.35 else '减弱'}"
                    self.message_timer = 2000
                elif event.key == pygame.K_e:
                    self.check_location_interaction()
                elif event.key == pygame.K_r:
                    self.collect_nearby_resources()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.is_mouse_locked:
                        self.is_mouse_locked = True
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self.message = "鼠标已锁定，按Tab键解锁"
                        self.message_timer = 3000
                    else:
                        self.move_to_mouse()
                elif event.button == 3:
                    self.check_npc_interaction()
            elif event.type == pygame.MOUSEMOTION:
                if self.is_mouse_locked:
                    rel_x, rel_y = event.rel
                    self.camera["yaw"] += rel_x * self.mouse_sensitivity
                    self.camera["pitch"] -= rel_y * self.mouse_sensitivity
                    self.camera["pitch"] = max(-89, min(89, self.camera["pitch"]))
        
        return True
    
    def check_npc_interaction(self):
        for npc in self.npcs:
            distance = math.hypot(
                npc["x"] - self.player_pos[0],
                npc["z"] - self.player_pos[2]
            )
            if distance <= self.npc_interaction_distance:
                self.selected_npc = npc
                self.message = f"右键NPC: {npc['name']}"
                self.message_timer = 3000
                self.show_npc_dialog(npc)
                return
        
        self.selected_npc = None
        self.message = "附近没有NPC"
        self.message_timer = 2000
    
    def show_npc_dialog(self, npc):
        self.npc_dialog_active = True
        self.selected_option = 0
        
        options = [
            {"text": f"进入{npc['name']}功能", "action": "enter"},
            {"text": "继续探索", "action": "cancel"}
        ]
        
        while self.npc_dialog_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.npc_dialog_active = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if options[self.selected_option]["action"] == "enter":
                            self.npc_dialog_active = False
                            self.execute_npc_action(npc)
                            return
                        else:
                            self.npc_dialog_active = False
                            return
                    elif event.key == pygame.K_ESCAPE:
                        self.npc_dialog_active = False
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        for i, option in enumerate(options):
                            option_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 180 + i * 40, 300, 35)
                            if option_rect.collidepoint(mouse_pos):
                                if option["action"] == "enter":
                                    self.npc_dialog_active = False
                                    self.execute_npc_action(npc)
                                    return
                                else:
                                    self.npc_dialog_active = False
                                    return
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw_3d_scene()
            
            dialog_width = 400
            dialog_height = 200
            dialog_x = SCREEN_WIDTH // 2 - dialog_width // 2
            dialog_y = SCREEN_HEIGHT - 250
            
            dialog_surf = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
            pygame.draw.rect(dialog_surf, (20, 20, 40, 230), (0, 0, dialog_width, dialog_height), border_radius=15)
            pygame.draw.rect(dialog_surf, COLORS["accent_gold"], (0, 0, dialog_width, dialog_height), 3, border_radius=15)
            
            name_surf = self.font_main.render(npc["name"], True, COLORS["accent_gold"])
            dialog_surf.blit(name_surf, (20, 15))
            
            dialogue_surf = self.font_small.render(npc["dialogue"], True, COLORS["text_white"])
            dialog_surf.blit(dialogue_surf, (20, 55))
            
            pygame.draw.line(dialog_surf, COLORS["accent_gold"], (20, 90), (dialog_width - 20, 90), 1)
            
            for i, option in enumerate(options):
                option_y = 100 + i * 40
                option_rect = pygame.Rect(20, option_y, dialog_width - 40, 35)
                
                if i == self.selected_option:
                    pygame.draw.rect(dialog_surf, (60, 60, 100), option_rect, border_radius=8)
                    pygame.draw.rect(dialog_surf, COLORS["accent_gold"], option_rect, 2, border_radius=8)
                    option_color = COLORS["accent_gold"]
                else:
                    pygame.draw.rect(dialog_surf, (40, 40, 70), option_rect, border_radius=8)
                    option_color = COLORS["text_white"]
                
                option_surf = self.font_small.render(option["text"], True, option_color)
                dialog_surf.blit(option_surf, (option_rect.x + 15, option_rect.y + 8))
            
            self.screen.blit(dialog_surf, (dialog_x, dialog_y))
            
            hint_surf = self.font_small.render("↑↓选择 | 回车确认 | ESC取消", True, (150, 150, 150))
            self.screen.blit(hint_surf, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT - 40))
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def execute_npc_action(self, npc):
        module_file = npc.get("module", "")
        if module_file:
            self.message = f"正在打开: {npc['name']}"
            self.message_timer = 2000
            
            pygame.time.wait(500)
            
            try:
                if module_file == "hero_recruitment.py":
                    from ASSET.hero_recruitment import main as hero_main
                    hero_main()
                elif module_file == "shop_system.py":
                    from ASSET.shop_system import main as shop_main
                    shop_main()
                elif module_file == "quest_system.py":
                    from ASSET.quest_system import main as quest_main
                    quest_main()
                elif module_file == "equipment_system.py":
                    from ASSET.equipment_system import main as equipment_main
                    equipment_main()
                elif module_file == "alchemy_system.py":
                    from ASSET.alchemy_system import main as alchemy_main
                    alchemy_main()
                elif module_file == "background_story.py":
                    from ASSET.background_story import main as story_main
                    story_main()
                elif module_file == "pvp_p2p.py":
                    from ASSET.pvp_p2p import main as pvp_main
                    pvp_main()
                else:
                    self.message = f"功能模块 {module_file} 尚未实现"
                    self.message_timer = 2000
            except Exception as e:
                self.message = f"打开功能失败: {str(e)[:20]}"
                self.message_timer = 2000
            
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
            self.screen = pygame.display.get_surface()
    
    def check_location_interaction(self):
        interaction_distance = 25
        closest_location = None
        closest_distance = float('inf')
        
        for loc in self.locations:
            distance = math.hypot(
                loc["x"] - self.player_pos[0],
                loc["y"] - self.player_pos[2]
            )
            if distance < closest_distance:
                closest_distance = distance
                closest_location = loc
        
        if closest_location and closest_distance <= interaction_distance:
            self.show_location_dialog(closest_location)
        else:
            self.message = "附近没有可进入的地点"
            self.message_timer = 2000
    
    def show_location_dialog(self, loc):
        self.location_dialog_active = True
        self.selected_option = 0
        
        loc_type = loc.get("type", "地点")
        owner = loc.get("owner", "neutral")
        level = loc.get("level", 1)
        power = loc.get("power", 0)
        
        if owner == "player":
            options = [
                {"text": "进入地点", "action": "enter"},
                {"text": "查看详情", "action": "info"},
                {"text": "离开", "action": "cancel"}
            ]
        elif owner == "enemy":
            options = [
                {"text": "挑战占领", "action": "battle"},
                {"text": "查看详情", "action": "info"},
                {"text": "离开", "action": "cancel"}
            ]
        else:
            options = [
                {"text": "尝试占领", "action": "capture"},
                {"text": "查看详情", "action": "info"},
                {"text": "离开", "action": "cancel"}
            ]
        
        while self.location_dialog_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.location_dialog_active = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        action = options[self.selected_option]["action"]
                        self.location_dialog_active = False
                        self.handle_location_action(loc, action)
                        return
                    elif event.key == pygame.K_ESCAPE:
                        self.location_dialog_active = False
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        for i, option in enumerate(options):
                            option_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 220 + i * 40, 300, 35)
                            if option_rect.collidepoint(mouse_pos):
                                action = option["action"]
                                self.location_dialog_active = False
                                self.handle_location_action(loc, action)
                                return
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw_3d_scene()
            
            dialog_width = 400
            dialog_height = 280
            dialog_x = SCREEN_WIDTH // 2 - dialog_width // 2
            dialog_y = SCREEN_HEIGHT - 330
            
            dialog_surf = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
            pygame.draw.rect(dialog_surf, (20, 20, 40, 230), (0, 0, dialog_width, dialog_height), border_radius=15)
            pygame.draw.rect(dialog_surf, COLORS["accent_gold"], (0, 0, dialog_width, dialog_height), 3, border_radius=15)
            
            name_surf = self.font_main.render(loc_type, True, COLORS["accent_gold"])
            dialog_surf.blit(name_surf, (20, 15))
            
            owner_text = f"归属: {'已占领' if owner == 'player' else '敌方' if owner == 'enemy' else '中立'}"
            owner_color = COLORS["accent_green"] if owner == "player" else COLORS["accent_red"] if owner == "enemy" else COLORS["text_white"]
            owner_surf = self.font_small.render(owner_text, True, owner_color)
            dialog_surf.blit(owner_surf, (20, 55))
            
            level_surf = self.font_small.render(f"等级: {level}", True, COLORS["text_white"])
            dialog_surf.blit(level_surf, (20, 80))
            
            power_surf = self.font_small.render(f"战力: {power}", True, COLORS["text_white"])
            dialog_surf.blit(power_surf, (20, 105))
            
            pygame.draw.line(dialog_surf, COLORS["accent_gold"], (20, 135), (dialog_width - 20, 135), 1)
            
            for i, option in enumerate(options):
                option_y = 145 + i * 40
                option_rect = pygame.Rect(20, option_y, dialog_width - 40, 35)
                
                if i == self.selected_option:
                    pygame.draw.rect(dialog_surf, (60, 60, 100), option_rect, border_radius=8)
                    pygame.draw.rect(dialog_surf, COLORS["accent_gold"], option_rect, 2, border_radius=8)
                    option_color = COLORS["accent_gold"]
                else:
                    pygame.draw.rect(dialog_surf, (40, 40, 70), option_rect, border_radius=8)
                    option_color = COLORS["text_white"]
                
                option_surf = self.font_small.render(option["text"], True, option_color)
                dialog_surf.blit(option_surf, (option_rect.x + 15, option_rect.y + 8))
            
            self.screen.blit(dialog_surf, (dialog_x, dialog_y))
            
            hint_surf = self.font_small.render("↑↓选择 | 回车确认 | ESC取消", True, (150, 150, 150))
            self.screen.blit(hint_surf, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT - 40))
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def handle_location_action(self, loc, action):
        if action == "enter":
            self.message = f"进入 {loc['type']}..."
            self.message_timer = 2000
            try:
                from ASSET.game_map_pygame import main as map_main
                map_main()
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
                self.screen = pygame.display.get_surface()
            except Exception as e:
                self.message = f"进入失败: {str(e)[:20]}"
                self.message_timer = 2000
        elif action == "battle":
            self.message = f"开始挑战 {loc['type']}..."
            self.message_timer = 2000
            try:
                from ASSET.battle_system import main as battle_main
                battle_main()
                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
                self.screen = pygame.display.get_surface()
                self.message = f"战斗结束!"
                self.message_timer = 3000
            except Exception as e:
                self.message = f"挑战失败: {str(e)[:20]}"
                self.message_timer = 2000
        elif action == "capture":
            self.message = f"尝试占领 {loc['type']}..."
            self.message_timer = 2000
            loc["owner"] = "player"
            self.message = f"成功占领 {loc['type']}!"
            self.message_timer = 3000
        elif action == "info":
            info_text = f"{loc['type']} - 等级{loc.get('level', 1)} - 战力{loc.get('power', 0)}"
            self.message = info_text
            self.message_timer = 3000
    
    def collect_nearby_resources(self):
        collect_distance = 30
        collected = {"金元宝": 0, "时间卡": 0}
        
        for loc in self.locations:
            if loc.get("owner") == "player":
                distance = math.hypot(
                    loc["x"] - self.player_pos[0],
                    loc["y"] - self.player_pos[2]
                )
                if distance <= collect_distance:
                    loc_type = loc.get("type", "")
                    if loc_type in ["矿山", "集市", "港口"]:
                        gold_bonus = loc.get("level", 1) * 10
                        collected["金元宝"] += gold_bonus
                    elif loc_type in ["驿站", "城池"]:
                        time_bonus = loc.get("level", 1)
                        collected["时间卡"] += time_bonus
        
        if collected["金元宝"] > 0 or collected["时间卡"] > 0:
            resources = data.get('resources', {})
            resources['金元宝'] = resources.get('金元宝', 0) + collected["金元宝"]
            resources['时间卡'] = resources.get('时间卡', 0) + collected["时间卡"]
            data['resources'] = resources
            save()
            
            self.message = f"收集: 金元宝+{collected['金元宝']} 时间卡+{collected['时间卡']}"
            self.message_timer = 3000
        else:
            self.message = "附近没有可收集的资源"
            self.message_timer = 2000
    
    def move_forward(self, speed):
        yaw_rad = math.radians(self.camera["yaw"])
        self.velocity[0] += math.cos(yaw_rad) * speed
        self.velocity[2] += math.sin(yaw_rad) * speed
        self.update_camera()
    
    def move_backward(self, speed):
        yaw_rad = math.radians(self.camera["yaw"])
        self.velocity[0] -= math.cos(yaw_rad) * speed
        self.velocity[2] -= math.sin(yaw_rad) * speed
        self.update_camera()
    
    def move_left(self, speed):
        yaw_rad = math.radians(self.camera["yaw"])
        self.velocity[0] -= math.sin(yaw_rad) * speed
        self.velocity[2] += math.cos(yaw_rad) * speed
        self.update_camera()
    
    def move_right(self, speed):
        yaw_rad = math.radians(self.camera["yaw"])
        self.velocity[0] += math.sin(yaw_rad) * speed
        self.velocity[2] -= math.cos(yaw_rad) * speed
        self.update_camera()
    
    def update_camera(self):
        yaw_rad = math.radians(self.camera["yaw"])
        pitch_rad = math.radians(self.camera["pitch"])
        
        if self.camera["mode"] == "first":
            distance = 0.5
            self.camera["x"] = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 1.8 + math.sin(pitch_rad) * distance
            self.camera["z"] = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * distance
        else:
            distance = 6.0
            self.camera["x"] = self.player_pos[0] - math.cos(yaw_rad) * math.cos(pitch_rad) * distance
            self.camera["y"] = self.player_pos[1] + 2.5 - math.sin(pitch_rad) * distance
            self.camera["z"] = self.player_pos[2] - math.sin(yaw_rad) * math.cos(pitch_rad) * distance
    
    def move_to_mouse(self):
        mx, my = pygame.mouse.get_pos()
        self.follow_target = {
            "x": self.player_pos[0] + (mx - SCREEN_WIDTH//2) * 0.15,
            "y": self.player_pos[2] + (my - SCREEN_HEIGHT//2) * 0.15
        }
        self.message = "移动到指定位置"
        self.message_timer = 2000
    
    def update_followers(self):
        if self.follow_target:
            for follower in self.followers:
                dx = self.follow_target["x"] - follower["x"]
                dz = self.follow_target["y"] - follower["z"]
                distance = math.hypot(dx, dz)
                if distance > 1:
                    follower["x"] += dx / distance * 0.3
                    follower["z"] += dz / distance * 0.3
    
    def update_npcs(self):
        for npc in self.npcs:
            npc["animation_offset"] += 0.02
            
            wander_angle = npc["move_dir"] + time.time() * npc["move_speed"]
            npc["x"] = npc["original_x"] + math.sin(wander_angle) * npc["wander_range"]
            npc["z"] = npc["original_z"] + math.cos(wander_angle) * npc["wander_range"]
    
    def draw_3d_scene(self):
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(60, SCREEN_WIDTH / SCREEN_HEIGHT, 0.1, 5000.0)
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            yaw_rad = math.radians(self.camera["yaw"])
            pitch_rad = math.radians(self.camera["pitch"])
            
            look_distance = 10
            look_x = self.player_pos[0] + math.cos(yaw_rad) * math.cos(pitch_rad) * look_distance
            look_y = self.player_pos[1] + 1.8 + math.sin(pitch_rad) * look_distance
            look_z = self.player_pos[2] + math.sin(yaw_rad) * math.cos(pitch_rad) * look_distance
            
            gluLookAt(
                self.camera["x"], self.camera["y"], self.camera["z"],
                look_x, look_y, look_z,
                0, 1, 0
            )
            
            self.draw_terrain()
            
            if hasattr(self, 'trees'):
                for tree in self.trees:
                    x, z, scale = tree
                    self.draw_tree(x, z, scale)
            
            for struct in self.large_structures:
                self.draw_large_structure(struct)
            
            for loc in self.locations:
                self.draw_location(loc)
            
            for npc in self.npcs:
                self.draw_npc(npc)
            
            if self.camera["mode"] == "third":
                self.draw_player()
            
            for follower in self.followers:
                self.draw_follower(follower)
            
            pygame.display.flip()
        except Exception as e:
            print(f"渲染错误: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_terrain(self):
        try:
            glDisable(GL_LIGHTING)
            
            block_size = 5
            height = -2
            
            visible_range = 200
            
            start_x = int((self.player_pos[0] - visible_range) / block_size) * block_size
            end_x = int((self.player_pos[0] + visible_range) / block_size) * block_size
            start_z = int((self.player_pos[2] - visible_range) / block_size) * block_size
            end_z = int((self.player_pos[2] + visible_range) / block_size) * block_size
            
            for x in range(start_x, end_x, block_size):
                for z in range(start_z, end_z, block_size):
                    noise = math.sin(x * 0.008) * math.cos(z * 0.008) * 3 + \
                            math.sin(x * 0.015) * math.sin(z * 0.015) * 2
                    block_y = height + noise
                    
                    if block_y < self.player_pos[1] - 30:
                        continue
                    
                    grass_color_intensity = 0.2 + noise * 0.05
                    glColor3f(0.2 + grass_color_intensity, 0.5 + grass_color_intensity, 0.2 + grass_color_intensity)
                    
                    glBegin(GL_QUADS)
                    glVertex3f(x, block_y, z)
                    glVertex3f(x + block_size, block_y, z)
                    glVertex3f(x + block_size, block_y, z + block_size)
                    glVertex3f(x, block_y, z + block_size)
                    glEnd()
            
            glEnable(GL_LIGHTING)
        except Exception as e:
            print(f"绘制地形错误: {e}")
    
    def draw_tree(self, x, z, scale=1.0):
        try:
            glDisable(GL_LIGHTING)
            
            glPushMatrix()
            glTranslatef(x, -1, z)
            glScalef(scale, scale, scale)
            
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
                y = leaves_base + layer * 0.6
                size = 2.0 - layer * 0.35
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
            
            glPopMatrix()
            glEnable(GL_LIGHTING)
        except Exception as e:
            print(f"绘制树木错误: {e}")
    
    def draw_large_structure(self, struct):
        try:
            x, z = struct["x"], struct["z"]
            size = struct["size"]
            height = struct["height"]
            color = struct["color"]
            
            glPushMatrix()
            glTranslatef(x, 0, z)
            
            glDisable(GL_LIGHTING)
            
            glColor3f(*color)
            
            glBegin(GL_QUADS)
            glVertex3f(-size/2, 0, -size/2)
            glVertex3f(size/2, 0, -size/2)
            glVertex3f(size/2, height, -size/2)
            glVertex3f(-size/2, height, -size/2)
            
            glVertex3f(size/2, 0, -size/2)
            glVertex3f(size/2, 0, size/2)
            glVertex3f(size/2, height, size/2)
            glVertex3f(size/2, height, -size/2)
            
            glVertex3f(size/2, 0, size/2)
            glVertex3f(-size/2, 0, size/2)
            glVertex3f(-size/2, height, size/2)
            glVertex3f(size/2, height, size/2)
            
            glVertex3f(-size/2, 0, size/2)
            glVertex3f(-size/2, 0, -size/2)
            glVertex3f(-size/2, height, -size/2)
            glVertex3f(-size/2, height, size/2)
            glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制大型结构错误: {e}")
    
    def draw_location(self, loc):
        try:
            x, z = loc["x"], loc["y"]
            loc_type = loc.get("type", "村庄")
            color = loc.get("color", (0.6, 0.5, 0.4))
            owner = loc.get("owner", "neutral")
            
            glPushMatrix()
            glTranslatef(x, 0, z)
            
            glDisable(GL_LIGHTING)
            
            base_width = 15
            base_depth = 15
            base_height = 2
            
            if owner == "player":
                glColor3f(0.3, 0.6, 0.3)
            elif owner == "enemy":
                glColor3f(0.6, 0.3, 0.3)
            else:
                glColor3f(*color)
            
            glBegin(GL_QUADS)
            glVertex3f(-base_width/2, 0, -base_depth/2)
            glVertex3f(base_width/2, 0, -base_depth/2)
            glVertex3f(base_width/2, base_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height, -base_depth/2)
            
            glVertex3f(base_width/2, 0, -base_depth/2)
            glVertex3f(base_width/2, 0, base_depth/2)
            glVertex3f(base_width/2, base_height, base_depth/2)
            glVertex3f(base_width/2, base_height, -base_depth/2)
            
            glVertex3f(base_width/2, 0, base_depth/2)
            glVertex3f(-base_width/2, 0, base_depth/2)
            glVertex3f(-base_width/2, base_height, base_depth/2)
            glVertex3f(base_width/2, base_height, base_depth/2)
            
            glVertex3f(-base_width/2, 0, base_depth/2)
            glVertex3f(-base_width/2, 0, -base_depth/2)
            glVertex3f(-base_width/2, base_height, -base_depth/2)
            glVertex3f(-base_width/2, base_height, base_depth/2)
            glEnd()
            
            wall_height = {
                "关隘": 18,
                "军营": 15,
                "村庄": 10,
                "矿山": 8,
                "港口": 10,
                "城池": 22,
                "驿站": 8,
                "集市": 9
            }.get(loc_type, 12)
            
            glColor3f(*color)
            
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
            
            if owner == "player":
                glColor3f(0.8, 0.8, 0)
                glBegin(GL_LINE_LOOP)
                glVertex3f(-base_width/2 - 2, base_height + wall_height + 5, -base_depth/2 - 2)
                glVertex3f(base_width/2 + 2, base_height + wall_height + 5, -base_depth/2 - 2)
                glVertex3f(base_width/2 + 2, base_height + wall_height + 5, base_depth/2 + 2)
                glVertex3f(-base_width/2 - 2, base_height + wall_height + 5, base_depth/2 + 2)
                glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制地点错误: {e}")
    
    def draw_npc(self, npc):
        try:
            glPushMatrix()
            glTranslatef(npc["x"], npc["y"], npc["z"])
            
            glDisable(GL_LIGHTING)
            
            bounce = math.sin(npc["animation_offset"]) * 0.2
            
            glColor3f(*npc["color"])
            
            body_height = 1.8
            body_width = 0.4
            body_depth = 0.3
            
            glTranslatef(0, body_height/2 + bounce, 0)
            
            glBegin(GL_QUADS)
            glVertex3f(-body_width/2, -body_height/2, -body_depth/2)
            glVertex3f(body_width/2, -body_height/2, -body_depth/2)
            glVertex3f(body_width/2, body_height/2, -body_depth/2)
            glVertex3f(-body_width/2, body_height/2, -body_depth/2)
            
            glVertex3f(body_width/2, -body_height/2, -body_depth/2)
            glVertex3f(body_width/2, -body_height/2, body_depth/2)
            glVertex3f(body_width/2, body_height/2, body_depth/2)
            glVertex3f(body_width/2, body_height/2, -body_depth/2)
            
            glVertex3f(body_width/2, -body_height/2, body_depth/2)
            glVertex3f(-body_width/2, -body_height/2, body_depth/2)
            glVertex3f(-body_width/2, body_height/2, body_depth/2)
            glVertex3f(body_width/2, body_height/2, body_depth/2)
            
            glVertex3f(-body_width/2, -body_height/2, body_depth/2)
            glVertex3f(-body_width/2, -body_height/2, -body_depth/2)
            glVertex3f(-body_width/2, body_height/2, -body_depth/2)
            glVertex3f(-body_width/2, body_height/2, body_depth/2)
            glEnd()
            
            distance_to_player = math.hypot(
                npc["x"] - self.player_pos[0],
                npc["z"] - self.player_pos[2]
            )
            
            if distance_to_player <= self.npc_interaction_distance:
                glColor3f(1.0, 1.0, 0.0)
                glBegin(GL_LINE_LOOP)
                for i in range(12):
                    angle = i * math.pi * 2 / 12
                    r = 1.2
                    glVertex3f(r * math.cos(angle), 2.5 + math.sin(time.time() * 3) * 0.2, r * math.sin(angle))
                glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制NPC错误: {e}")
    
    def draw_player(self):
        try:
            glPushMatrix()
            player_x, player_y, player_z = self.player_pos[0], self.player_pos[1], self.player_pos[2]
            glTranslatef(player_x, player_y, player_z)
            
            glDisable(GL_LIGHTING)
            
            glColor3f(0.2, 0.4, 0.8)
            glBegin(GL_QUADS)
            glVertex3f(-0.25, 0, -0.15)
            glVertex3f(0.25, 0, -0.15)
            glVertex3f(0.25, 1.8, -0.15)
            glVertex3f(-0.25, 1.8, -0.15)
            
            glVertex3f(0.25, 0, -0.15)
            glVertex3f(0.25, 0, 0.15)
            glVertex3f(0.25, 1.8, 0.15)
            glVertex3f(0.25, 1.8, -0.15)
            
            glVertex3f(0.25, 0, 0.15)
            glVertex3f(-0.25, 0, 0.15)
            glVertex3f(-0.25, 1.8, 0.15)
            glVertex3f(0.25, 1.8, 0.15)
            
            glVertex3f(-0.25, 0, 0.15)
            glVertex3f(-0.25, 0, -0.15)
            glVertex3f(-0.25, 1.8, -0.15)
            glVertex3f(-0.25, 1.8, 0.15)
            glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制玩家错误: {e}")
    
    def draw_follower(self, follower):
        try:
            glPushMatrix()
            glTranslatef(follower["x"], follower["y"], follower["z"])
            
            glDisable(GL_LIGHTING)
            
            glColor3f(0.6, 0.8, 0.4)
            
            glBegin(GL_QUADS)
            glVertex3f(-0.75, 0, -0.75)
            glVertex3f(0.75, 0, -0.75)
            glVertex3f(0.75, 1.5, -0.75)
            glVertex3f(-0.75, 1.5, -0.75)
            
            glVertex3f(0.75, 0, -0.75)
            glVertex3f(0.75, 0, 0.75)
            glVertex3f(0.75, 1.5, 0.75)
            glVertex3f(0.75, 1.5, -0.75)
            
            glVertex3f(0.75, 0, 0.75)
            glVertex3f(-0.75, 0, 0.75)
            glVertex3f(-0.75, 1.5, 0.75)
            glVertex3f(0.75, 1.5, 0.75)
            
            glVertex3f(-0.75, 0, 0.75)
            glVertex3f(-0.75, 0, -0.75)
            glVertex3f(-0.75, 1.5, -0.75)
            glVertex3f(-0.75, 1.5, 0.75)
            glEnd()
            
            glEnable(GL_LIGHTING)
            glPopMatrix()
        except Exception as e:
            print(f"绘制跟随者错误: {e}")
    
    def draw_hud(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        pos_text = f"位置: ({int(self.player_pos[0])}, {int(self.player_pos[1])}, {int(self.player_pos[2])})"
        pos_surf = self.font_small.render(pos_text, True, COLORS["text_white"])
        self.screen.blit(pos_surf, (10, 10))
        
        if self.follow_target:
            follow_text = f"跟随: {self.follow_target.get('type', '位置')}"
            follow_surf = self.font_small.render(follow_text, True, COLORS["accent_green"])
            self.screen.blit(follow_surf, (10, 40))
        
        resources = data.get('resources', {})
        gold = resources.get('金元宝', 0)
        time_card = resources.get('时间卡', 0)
        resource_text = f"金元宝: {gold} | 时间卡: {time_card}"
        resource_surf = self.font_small.render(resource_text, True, COLORS["accent_gold"])
        self.screen.blit(resource_surf, (10, 70))
        
        owned_count = len([loc for loc in self.locations if loc.get('owner') == 'player'])
        total_count = len(self.locations)
        territory_text = f"占领地点: {owned_count}/{total_count}"
        territory_surf = self.font_small.render(territory_text, True, COLORS["accent_green"])
        self.screen.blit(territory_surf, (10, 100))
        
        if self.message and self.message_timer > 0:
            msg_surf = self.font_main.render(self.message, True, COLORS["accent_gold"])
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            self.screen.blit(msg_surf, msg_rect)
            self.message_timer -= self.clock.get_time()
            if self.message_timer < 0:
                self.message = None
        
        controls = [
            "WASD: 移动",
            "空格: 跳跃",
            "E: 进入地点",
            "R: 收集资源",
            "Tab: 锁定鼠标",
            "F: 跟随模式",
            "F5: 切换视角",
            "右键: 与NPC交互"
        ]
        
        for i, control in enumerate(controls):
            control_surf = self.font_small.render(control, True, (200, 200, 200))
            self.screen.blit(control_surf, (SCREEN_WIDTH - 150, 10 + i * 25))
        
        glEnable(GL_DEPTH_TEST)
    
    def update_physics(self):
        self.velocity[1] += self.gravity
        
        self.velocity[0] *= self.friction
        self.velocity[2] *= self.friction
        
        if abs(self.velocity[0]) < 0.01:
            self.velocity[0] = 0
        if abs(self.velocity[2]) < 0.01:
            self.velocity[2] = 0
        
        self.player_pos[0] += self.velocity[0]
        self.player_pos[1] += self.velocity[1]
        self.player_pos[2] += self.velocity[2]
        
        if self.player_pos[1] < 0:
            self.player_pos[1] = 0
            self.velocity[1] = 0
        
        self.player_pos[0] = max(-1800, min(1800, self.player_pos[0]))
        self.player_pos[2] = max(-1800, min(1800, self.player_pos[2]))
        
        self.update_camera()
    
    def run(self):
        if not self.initialize():
            return
        
        running = True
        while running:
            self.clock.tick(60)
            
            running = self.handle_input()
            
            self.update_physics()
            self.update_npcs()
            self.update_followers()
            
            self.draw_3d_scene()
            self.draw_hud()
            
            pygame.display.flip()
        
        pygame.quit()

def main():
    game = GameMap3D()
    game.run()
