"""
Python ctypes 绑定到 C++ OpenGL 渲染模块
"""
import ctypes
import os
import sys

def load_renderer_dll():
    dll_path = None

    possible_paths = [
        os.path.join(os.path.dirname(__file__), "opengl_renderer.dll"),
        os.path.join(os.path.dirname(__file__), "Release", "opengl_renderer.dll"),
        os.path.join(os.path.dirname(__file__), "x64", "Release", "opengl_renderer.dll"),
        os.path.join(os.path.dirname(__file__), "build", "opengl_renderer.dll"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            dll_path = path
            break

    if dll_path is None:
        return None

    try:
        dll = ctypes.CDLL(dll_path)
        return dll
    except Exception as e:
        print(f"加载渲染器 DLL 失败: {e}")
        return None


class Vec3f(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
    ]


class Color4f(ctypes.Structure):
    _fields_ = [
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("a", ctypes.c_float),
    ]


class ProjectileData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("type", ctypes.c_int),
        ("rotation", ctypes.c_float),
    ]


class PickupData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("bob_offset", ctypes.c_float),
        ("rotation", ctypes.c_float),
        ("item_type", ctypes.c_int),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("a", ctypes.c_float),
    ]


class TechBlockData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("tech_type", ctypes.c_int),
        ("active", ctypes.c_int),
        ("rotation", ctypes.c_float),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("a", ctypes.c_float),
    ]


class LocationData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("type", ctypes.c_int),
        ("height", ctypes.c_float),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("owner", ctypes.c_int),
        ("scale", ctypes.c_float),
    ]


class NPCData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("name", ctypes.c_char_p),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("selected", ctypes.c_int),
        ("animation_offset", ctypes.c_float),
    ]


class EnemyData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("type", ctypes.c_int),
        ("health", ctypes.c_float),
        ("max_health", ctypes.c_float),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
    ]


class GeneralData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("name", ctypes.c_char_p),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("has_weapon", ctypes.c_int),
        ("animation_offset", ctypes.c_float),
    ]


class PetData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("type", ctypes.c_int),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("animation_offset", ctypes.c_float),
    ]


class PlayerData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("yaw", ctypes.c_float),
    ]


class FollowerData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("name", ctypes.c_char_p),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
        ("animation_offset", ctypes.c_float),
    ]


class TreeData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("scale", ctypes.c_float),
    ]


class StructureData(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("z", ctypes.c_float),
        ("name", ctypes.c_char_p),
        ("size", ctypes.c_float),
        ("height", ctypes.c_float),
        ("r", ctypes.c_float),
        ("g", ctypes.c_float),
        ("b", ctypes.c_float),
    ]


class OpenGLRenderer:
    _instance = None
    _dll = None

    def __new__(cls):
        if cls._instance is not None:
            return cls._instance
        instance = super().__new__(cls)
        cls._instance = instance
        return instance

    def __init__(self):
        if self._dll is not None:
            return

        self._dll = load_renderer_dll()
        if self._dll is None:
            print("警告: C++ 渲染器 DLL 未加载，OpenGL 渲染将使用 Python 实现")
            self._available = False
            return

        self._setup_function_signatures()
        self._available = True

    def _setup_function_signatures(self):
        dll = self._dll

        dll.init_renderer.argtypes = [ctypes.c_int, ctypes.c_int]
        dll.init_renderer.restype = None

        dll.cleanup_renderer.argtypes = []
        dll.cleanup_renderer.restype = None

        dll.render_terrain.argtypes = [
            ctypes.c_float, ctypes.c_float, ctypes.c_float,
            ctypes.c_float, ctypes.c_float, ctypes.c_float
        ]
        dll.render_terrain.restype = None

        dll.render_projectiles.argtypes = [
            ctypes.POINTER(ProjectileData), ctypes.c_int
        ]
        dll.render_projectiles.restype = None

        dll.render_pickups.argtypes = [
            ctypes.POINTER(PickupData), ctypes.c_int
        ]
        dll.render_pickups.restype = None

        dll.render_tech_block.argtypes = [ctypes.POINTER(TechBlockData)]
        dll.render_tech_block.restype = None

        dll.render_tree.argtypes = [ctypes.POINTER(TreeData)]
        dll.render_tree.restype = None

        dll.render_trees.argtypes = [
            ctypes.POINTER(TreeData), ctypes.c_int
        ]
        dll.render_trees.restype = None

        dll.render_large_structure.argtypes = [ctypes.POINTER(StructureData)]
        dll.render_large_structure.restype = None

        dll.render_structures.argtypes = [
            ctypes.POINTER(StructureData), ctypes.c_int
        ]
        dll.render_structures.restype = None

        dll.render_location.argtypes = [ctypes.POINTER(LocationData)]
        dll.render_location.restype = None

        dll.render_locations.argtypes = [
            ctypes.POINTER(LocationData), ctypes.c_int
        ]
        dll.render_locations.restype = None

        dll.render_npc.argtypes = [ctypes.POINTER(NPCData)]
        dll.render_npc.restype = None

        dll.render_npcs.argtypes = [
            ctypes.POINTER(NPCData), ctypes.c_int
        ]
        dll.render_npcs.restype = None

        dll.render_enemy.argtypes = [ctypes.POINTER(EnemyData)]
        dll.render_enemy.restype = None

        dll.render_enemies.argtypes = [
            ctypes.POINTER(EnemyData), ctypes.c_int
        ]
        dll.render_enemies.restype = None

        dll.render_general.argtypes = [ctypes.POINTER(GeneralData)]
        dll.render_general.restype = None

        dll.render_generals.argtypes = [
            ctypes.POINTER(GeneralData), ctypes.c_int
        ]
        dll.render_generals.restype = None

        dll.render_pet.argtypes = [ctypes.POINTER(PetData)]
        dll.render_pet.restype = None

        dll.render_pets.argtypes = [
            ctypes.POINTER(PetData), ctypes.c_int
        ]
        dll.render_pets.restype = None

        dll.render_player.argtypes = [ctypes.POINTER(PlayerData)]
        dll.render_player.restype = None

        dll.render_follower.argtypes = [ctypes.POINTER(FollowerData)]
        dll.render_follower.restype = None

        dll.render_followers.argtypes = [
            ctypes.POINTER(FollowerData), ctypes.c_int
        ]
        dll.render_followers.restype = None

        dll.render_particles.argtypes = [
            ctypes.POINTER(Vec3f), ctypes.POINTER(Color4f), ctypes.c_int
        ]
        dll.render_particles.restype = None

        dll.get_renderer_error.argtypes = []
        dll.get_renderer_error.restype = ctypes.c_char_p

    @property
    def is_available(self):
        return self._available

    def init_renderer(self, screen_width, screen_height):
        if self._dll:
            self._dll.init_renderer(screen_width, screen_height)

    def cleanup(self):
        if self._dll:
            self._dll.cleanup_renderer()

    def render_terrain(self, player_pos, visible_range=200, block_size=5, height=-2):
        if self._dll:
            self._dll.render_terrain(
                player_pos[0], player_pos[1], player_pos[2],
                visible_range, block_size, height
            )

    def render_projectiles(self, projectiles):
        if not self._dll or not projectiles:
            return

        count = len(projectiles)
        array_type = ProjectileData * count
        data_array = array_type()

        for i, proj in enumerate(projectiles):
            data_array[i].x = proj.get("x", 0)
            data_array[i].y = proj.get("y", 0)
            data_array[i].z = proj.get("z", 0)

            proj_type = proj.get("type", "arrow")
            if proj_type == "arrow":
                data_array[i].type = 0
            elif proj_type == "bolt":
                data_array[i].type = 1
            elif proj_type == "trident":
                data_array[i].type = 2
            else:
                data_array[i].type = 0

            data_array[i].rotation = proj.get("rotation", 0)

        self._dll.render_projectiles(data_array, count)

    def render_pickups(self, pickups, mc_blocks):
        if not self._dll or not pickups:
            return

        count = len(pickups)
        array_type = PickupData * count
        data_array = array_type()

        for i, pickup in enumerate(pickups):
            data_array[i].x = pickup.get("x", 0)
            data_array[i].z = pickup.get("y", 0)
            data_array[i].bob_offset = pickup.get("bob_offset", 0)
            data_array[i].rotation = pickup.get("rotation", 0)

            item_name = pickup.get("item", "stone")
            block_data = mc_blocks.get(item_name, mc_blocks.get("stone", {}))
            color = block_data.get("color", (128, 128, 128))

            if len(color) == 4:
                r, g, b, a = color
            else:
                r, g, b = color
                a = 255

            data_array[i].r = r / 255.0
            data_array[i].g = g / 255.0
            data_array[i].b = b / 255.0
            data_array[i].a = a / 255.0 if a <= 1 else a

        self._dll.render_pickups(data_array, count)

    def render_tech_block(self, tech_block, mc_blocks):
        if not self._dll or not tech_block:
            return

        data = TechBlockData()
        data.x = tech_block.get("x", 0)
        data.z = tech_block.get("z", 0)
        data.tech_type = tech_block.get("type", 0)
        data.active = 1 if tech_block.get("active", False) else 0
        data.rotation = tech_block.get("rotation", 0)

        tech_type_name = tech_block.get("type", "stone")
        block_data = mc_blocks.get(tech_type_name, mc_blocks.get("stone", {}))
        color = block_data.get("color", (100, 100, 110))

        if len(color) == 4:
            r, g, b, a = color
            data.a = a / 255.0 if a <= 1 else a
        else:
            r, g, b = color
            data.a = 0

        data.r = r / 255.0
        data.g = g / 255.0
        data.b = b / 255.0

        self._dll.render_tech_block(ctypes.byref(data))

    def render_tree(self, x, z, scale=1.0):
        if self._dll:
            data = TreeData()
            data.x = x
            data.z = z
            data.scale = scale
            self._dll.render_tree(ctypes.byref(data))

    def render_trees(self, trees):
        if not self._dll or not trees:
            return

        count = len(trees)
        array_type = TreeData * count
        data_array = array_type()

        for i, tree in enumerate(trees):
            data_array[i].x = tree[0]
            data_array[i].z = tree[1]
            data_array[i].scale = tree[2] if len(tree) > 2 else 1.0

        self._dll.render_trees(data_array, count)

    def render_large_structure(self, struct):
        if not self._dll or not struct:
            return

        data = StructureData()
        data.x = struct.get("x", 0)
        data.z = struct.get("z", 0)
        data.name = struct.get("name", b"structure") if isinstance(struct.get("name"), bytes) else struct.get("name", "structure").encode('utf-8')
        data.size = struct.get("size", 20)
        data.height = struct.get("height", 15)
        color = struct.get("color", (0.6, 0.5, 0.4))
        data.r, data.g, data.b = color

        self._dll.render_large_structure(ctypes.byref(data))

    def render_structures(self, structures):
        if not self._dll or not structures:
            return

        count = len(structures)
        array_type = StructureData * count
        data_array = array_type()

        for i, struct in enumerate(structures):
            data_array[i].x = struct.get("x", 0)
            data_array[i].z = struct.get("z", 0)
            data_array[i].name = struct.get("name", b"structure") if isinstance(struct.get("name"), bytes) else struct.get("name", "structure").encode('utf-8')
            data_array[i].size = struct.get("size", 20)
            data_array[i].height = struct.get("height", 15)
            color = struct.get("color", (0.6, 0.5, 0.4))
            data_array[i].r, data_array[i].g, data_array[i].b = color

        self._dll.render_structures(data_array, count)

    def render_location(self, loc):
        if not self._dll or not loc:
            return

        data = LocationData()
        data.x = loc.get("x", 0)
        data.z = loc.get("z", 0)
        data.type = loc.get("type", 0)
        data.height = loc.get("height", 0)
        data.r, data.g, data.b = loc.get("color", (0.5, 0.5, 0.5))
        data.owner = 1 if loc.get("owner", "neutral") == "player" else (2 if loc.get("owner") == "enemy" else 0)
        data.scale = loc.get("scale", 1.0)

        self._dll.render_location(ctypes.byref(data))

    def render_locations(self, locations):
        if not self._dll or not locations:
            return

        count = len(locations)
        array_type = LocationData * count
        data_array = array_type()

        for i, loc in enumerate(locations):
            data_array[i].x = loc.get("x", 0)
            data_array[i].z = loc.get("z", 0)
            data_array[i].type = loc.get("type", 0)
            data_array[i].height = loc.get("height", 0)
            data_array[i].r, data_array[i].g, data_array[i].b = loc.get("color", (0.5, 0.5, 0.5))
            data_array[i].owner = 1 if loc.get("owner", "neutral") == "player" else (2 if loc.get("owner") == "enemy" else 0)
            data_array[i].scale = loc.get("scale", 1.0)

        self._dll.render_locations(data_array, count)

    def render_npc(self, npc):
        if not self._dll or not npc:
            return

        data = NPCData()
        data.x = npc.get("x", 0)
        data.z = npc.get("z", 0)
        data.name = npc.get("name", b"npc") if isinstance(npc.get("name"), bytes) else npc.get("name", "npc").encode('utf-8')
        data.r, data.g, data.b = npc.get("color", (0.8, 0.6, 0.4))
        data.selected = 1 if npc.get("selected", False) else 0
        data.animation_offset = npc.get("animation_offset", 0)

        self._dll.render_npc(ctypes.byref(data))

    def render_npcs(self, npcs):
        if not self._dll or not npcs:
            return

        count = len(npcs)
        array_type = NPCData * count
        data_array = array_type()

        for i, npc in enumerate(npcs):
            data_array[i].x = npc.get("x", 0)
            data_array[i].z = npc.get("z", 0)
            data_array[i].name = npc.get("name", b"npc") if isinstance(npc.get("name"), bytes) else npc.get("name", "npc").encode('utf-8')
            data_array[i].r, data_array[i].g, data_array[i].b = npc.get("color", (0.8, 0.6, 0.4))
            data_array[i].selected = 1 if npc.get("selected", False) else 0
            data_array[i].animation_offset = npc.get("animation_offset", 0)

        self._dll.render_npcs(data_array, count)

    def render_enemy(self, enemy):
        if not self._dll or not enemy:
            return

        data = EnemyData()
        data.x = enemy.get("x", 0)
        data.z = enemy.get("z", 0)
        data.type = enemy.get("type", 0)
        data.health = enemy.get("health", 100)
        data.max_health = enemy.get("max_health", 100)
        data.r, data.g, data.b = enemy.get("color", (0.8, 0.2, 0.2))

        self._dll.render_enemy(ctypes.byref(data))

    def render_enemies(self, enemies):
        if not self._dll or not enemies:
            return

        count = len(enemies)
        array_type = EnemyData * count
        data_array = array_type()

        for i, enemy in enumerate(enemies):
            data_array[i].x = enemy.get("x", 0)
            data_array[i].z = enemy.get("z", 0)
            data_array[i].type = enemy.get("type", 0)
            data_array[i].health = enemy.get("health", 100)
            data_array[i].max_health = enemy.get("max_health", 100)
            data_array[i].r, data_array[i].g, data_array[i].b = enemy.get("color", (0.8, 0.2, 0.2))

        self._dll.render_enemies(data_array, count)

    def render_general(self, general):
        if not self._dll or not general:
            return

        data = GeneralData()
        data.x = general.get("x", 0)
        data.z = general.get("z", 0)
        data.name = general.get("name", b"general") if isinstance(general.get("name"), bytes) else general.get("name", "general").encode('utf-8')
        data.r, data.g, data.b = general.get("color", (0.6, 0.8, 0.6))
        data.has_weapon = 1 if general.get("has_weapon", False) else 0
        data.animation_offset = general.get("animation_offset", 0)

        self._dll.render_general(ctypes.byref(data))

    def render_generals(self, generals):
        if not self._dll or not generals:
            return

        count = len(generals)
        array_type = GeneralData * count
        data_array = array_type()

        for i, general in enumerate(generals):
            data_array[i].x = general.get("x", 0)
            data_array[i].z = general.get("z", 0)
            data_array[i].name = general.get("name", b"general") if isinstance(general.get("name"), bytes) else general.get("name", "general").encode('utf-8')
            data_array[i].r, data_array[i].g, data_array[i].b = general.get("color", (0.6, 0.8, 0.6))
            data_array[i].has_weapon = 1 if general.get("has_weapon", False) else 0
            data_array[i].animation_offset = general.get("animation_offset", 0)

        self._dll.render_generals(data_array, count)

    def render_pet(self, pet):
        if not self._dll or not pet:
            return

        data = PetData()
        data.x = pet.get("x", 0)
        data.z = pet.get("z", 0)
        data.type = pet.get("type", 0)
        data.r, data.g, data.b = pet.get("color", (0.8, 0.6, 0.8))
        data.animation_offset = pet.get("animation_offset", 0)

        self._dll.render_pet(ctypes.byref(data))

    def render_pets(self, pets):
        if not self._dll or not pets:
            return

        count = len(pets)
        array_type = PetData * count
        data_array = array_type()

        for i, pet in enumerate(pets):
            data_array[i].x = pet.get("x", 0)
            data_array[i].z = pet.get("z", 0)
            data_array[i].type = pet.get("type", 0)
            data_array[i].r, data_array[i].g, data_array[i].b = pet.get("color", (0.8, 0.6, 0.8))
            data_array[i].animation_offset = pet.get("animation_offset", 0)

        self._dll.render_pets(data_array, count)

    def render_player(self, player_data):
        if not self._dll or not player_data:
            return

        data = PlayerData()
        data.x = player_data.get("x", 0)
        data.y = player_data.get("y", 0)
        data.z = player_data.get("z", 0)
        data.r, data.g, data.b = player_data.get("color", (0.8, 0.8, 0.8))
        data.yaw = player_data.get("yaw", 0)

        self._dll.render_player(ctypes.byref(data))

    def render_follower(self, follower):
        if not self._dll or not follower:
            return

        data = FollowerData()
        data.x = follower.get("x", 0)
        data.z = follower.get("z", 0)
        data.name = follower.get("name", b"follower") if isinstance(follower.get("name"), bytes) else follower.get("name", "follower").encode('utf-8')
        data.r, data.g, data.b = follower.get("color", (0.6, 0.8, 0.8))
        data.animation_offset = follower.get("animation_offset", 0)

        self._dll.render_follower(ctypes.byref(data))

    def render_followers(self, followers):
        if not self._dll or not followers:
            return

        count = len(followers)
        array_type = FollowerData * count
        data_array = array_type()

        for i, follower in enumerate(followers):
            data_array[i].x = follower.get("x", 0)
            data_array[i].z = follower.get("z", 0)
            data_array[i].name = follower.get("name", b"follower") if isinstance(follower.get("name"), bytes) else follower.get("name", "follower").encode('utf-8')
            data_array[i].r, data_array[i].g, data_array[i].b = follower.get("color", (0.6, 0.8, 0.8))
            data_array[i].animation_offset = follower.get("animation_offset", 0)

        self._dll.render_followers(data_array, count)

    def render_particles(self, positions, colors):
        if not self._dll or not positions:
            return

        count = len(positions)
        pos_array_type = Vec3f * count
        color_array_type = Color4f * count

        pos_array = pos_array_type()
        color_array = color_array_type()

        for i in range(count):
            pos_array[i].x = positions[i].get("x", 0) if isinstance(positions[i], dict) else positions[i][0]
            pos_array[i].y = positions[i].get("y", 0) if isinstance(positions[i], dict) else positions[i][1]
            pos_array[i].z = positions[i].get("z", 0) if isinstance(positions[i], dict) else positions[i][2]

            if isinstance(colors[i], dict):
                color_array[i].r = colors[i].get("r", 1)
                color_array[i].g = colors[i].get("g", 1)
                color_array[i].b = colors[i].get("b", 1)
                color_array[i].a = colors[i].get("a", 1)
            else:
                color_array[i].r = colors[i][0]
                color_array[i].g = colors[i][1]
                color_array[i].b = colors[i][2]
                color_array[i].a = colors[i][3] if len(colors[i]) > 3 else 1

        self._dll.render_particles(pos_array, color_array, count)

    def get_error(self):
        if self._dll:
            return self._dll.get_renderer_error().decode('utf-8')
        return None


renderer = OpenGLRenderer()