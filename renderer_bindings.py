
import ctypes
import os

class ProjectileData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('vx', ctypes.c_float),
        ('vy', ctypes.c_float),
        ('vz', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('radius', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class PickupData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('size', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class TechBlockData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('size', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class TreeData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('z', ctypes.c_float),
        ('base_height', ctypes.c_float),
        ('height', ctypes.c_float),
        ('width', ctypes.c_float)
    ]

class StructureData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('z', ctypes.c_float),
        ('width', ctypes.c_float),
        ('height', ctypes.c_float),
        ('depth', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class LocationData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class NPCData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('animation_offset', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class EnemyData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('current_health', ctypes.c_float),
        ('max_health', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class GeneralData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('has_weapon', ctypes.c_int),
        ('weapon_type', ctypes.c_int)
    ]

class PetData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('size', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class PlayerData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('rotation', ctypes.c_float)
    ]

class FollowerData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('type', ctypes.c_int)
    ]

class ParticleData(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('z', ctypes.c_float),
        ('r', ctypes.c_float),
        ('g', ctypes.c_float),
        ('b', ctypes.c_float),
        ('alpha', ctypes.c_float),
        ('size', ctypes.c_float)
    ]

class Renderer:
    def __init__(self):
        self.dll = None
        self.is_available = False
        self._load_dll()
    
    def _load_dll(self):
        dll_paths = [
            'opengl_renderer.dll',
            './opengl_renderer.dll',
            os.path.join(os.path.dirname(__file__), 'opengl_renderer.dll')
        ]
        
        for path in dll_paths:
            try:
                self.dll = ctypes.CDLL(path)
                self._setup_functions()
                self.is_available = True
                print(f'成功加载C++渲染器: {path}')
                return
            except Exception as e:
                pass
        
        print('警告: C++渲染器DLL未加载，OpenGL渲染将使用Python实现')
    
    def _setup_functions(self):
        self.dll.get_last_error.restype = ctypes.c_char_p
        
        self.dll.init_renderer.argtypes = [ctypes.c_int, ctypes.c_int]
        self.dll.init_renderer.restype = None
        
        self.dll.render_terrain.argtypes = [
            ctypes.c_float, ctypes.c_float, ctypes.c_float,
            ctypes.c_float, ctypes.c_float, ctypes.c_float
        ]
        self.dll.render_terrain.restype = None
        
        self.dll.render_projectiles.argtypes = [
            ctypes.POINTER(ProjectileData), ctypes.c_int
        ]
        self.dll.render_projectiles.restype = None
        
        self.dll.render_pickups.argtypes = [
            ctypes.POINTER(PickupData), ctypes.c_int
        ]
        self.dll.render_pickups.restype = None
        
        self.dll.render_tech_blocks.argtypes = [
            ctypes.POINTER(TechBlockData), ctypes.c_int
        ]
        self.dll.render_tech_blocks.restype = None
        
        self.dll.render_trees.argtypes = [
            ctypes.POINTER(TreeData), ctypes.c_int
        ]
        self.dll.render_trees.restype = None
        
        self.dll.render_structures.argtypes = [
            ctypes.POINTER(StructureData), ctypes.c_int
        ]
        self.dll.render_structures.restype = None
        
        self.dll.render_locations.argtypes = [
            ctypes.POINTER(LocationData), ctypes.c_int
        ]
        self.dll.render_locations.restype = None
        
        self.dll.render_npcs.argtypes = [
            ctypes.POINTER(NPCData), ctypes.c_int
        ]
        self.dll.render_npcs.restype = None
        
        self.dll.render_enemies.argtypes = [
            ctypes.POINTER(EnemyData), ctypes.c_int
        ]
        self.dll.render_enemies.restype = None
        
        self.dll.render_generals.argtypes = [
            ctypes.POINTER(GeneralData), ctypes.c_int
        ]
        self.dll.render_generals.restype = None
        
        self.dll.render_pets.argtypes = [
            ctypes.POINTER(PetData), ctypes.c_int
        ]
        self.dll.render_pets.restype = None
        
        self.dll.render_player.argtypes = [
            ctypes.POINTER(PlayerData)
        ]
        self.dll.render_player.restype = None
        
        self.dll.render_followers.argtypes = [
            ctypes.POINTER(FollowerData), ctypes.c_int
        ]
        self.dll.render_followers.restype = None
        
        self.dll.render_particles.argtypes = [
            ctypes.POINTER(ParticleData), ctypes.c_int
        ]
        self.dll.render_particles.restype = None
    
    def get_last_error(self):
        if self.dll:
            return self.dll.get_last_error()
        return None
    
    def init_renderer(self, width, height):
        if self.dll:
            self.dll.init_renderer(width, height)
    
    def render_terrain(self, player_x, player_y, player_z, visible_range, block_size, height):
        if self.dll:
            self.dll.render_terrain(player_x, player_y, player_z, visible_range, block_size, height)
    
    def render_projectiles(self, projectiles):
        if self.dll and projectiles:
            arr = (ProjectileData * len(projectiles))(*projectiles)
            self.dll.render_projectiles(arr, len(projectiles))
    
    def render_pickups(self, pickups):
        if self.dll and pickups:
            arr = (PickupData * len(pickups))(*pickups)
            self.dll.render_pickups(arr, len(pickups))
    
    def render_tech_blocks(self, blocks):
        if self.dll and blocks:
            arr = (TechBlockData * len(blocks))(*blocks)
            self.dll.render_tech_blocks(arr, len(blocks))
    
    def render_trees(self, trees):
        if self.dll and trees:
            arr = (TreeData * len(trees))(*trees)
            self.dll.render_trees(arr, len(trees))
    
    def render_structures(self, structures):
        if self.dll and structures:
            arr = (StructureData * len(structures))(*structures)
            self.dll.render_structures(arr, len(structures))
    
    def render_locations(self, locations):
        if self.dll and locations:
            arr = (LocationData * len(locations))(*locations)
            self.dll.render_locations(arr, len(locations))
    
    def render_npcs(self, npcs):
        if self.dll and npcs:
            arr = (NPCData * len(npcs))(*npcs)
            self.dll.render_npcs(arr, len(npcs))
    
    def render_enemies(self, enemies):
        if self.dll and enemies:
            arr = (EnemyData * len(enemies))(*enemies)
            self.dll.render_enemies(arr, len(enemies))
    
    def render_generals(self, generals):
        if self.dll and generals:
            arr = (GeneralData * len(generals))(*generals)
            self.dll.render_generals(arr, len(generals))
    
    def render_pets(self, pets):
        if self.dll and pets:
            arr = (PetData * len(pets))(*pets)
            self.dll.render_pets(arr, len(pets))
    
    def render_player(self, player):
        if self.dll and player:
            self.dll.render_player(ctypes.byref(player))
    
    def render_followers(self, followers):
        if self.dll and followers:
            arr = (FollowerData * len(followers))(*followers)
            self.dll.render_followers(arr, len(followers))
    
    def render_particles(self, particles):
        if self.dll and particles:
            arr = (ParticleData * len(particles))(*particles)
            self.dll.render_particles(arr, len(particles))

renderer = Renderer()
