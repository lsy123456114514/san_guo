"""无头验证 C++ 渲染器：地形/放置方块/粒子渲染调用不崩溃"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
try:
    screen = pygame.display.set_mode((800, 600), pygame.OPENGL | pygame.DOUBLEBUF)
    print("[OK] GL 上下文创建成功")
except Exception as e:
    print(f"[SKIP] dummy 驱动不支持 GL 上下文: {e}")
    sys.exit(0)

from renderer_bindings import renderer, BlockData, ParticleData, TreeData, LocationData

print("[OK] C++ 渲染器可用:", renderer.is_available)
if not renderer.is_available:
    print("[FAIL] 渲染器不可用")
    sys.exit(1)

# 初始化渲染器
renderer.init_renderer(800, 600)

# 1. 噪声地形渲染（范围 100，C++ 循环）
renderer.render_terrain(0.0, 0.0, 0.0, 100.0, 4.0, -1.0)
print("[OK] render_terrain(100) 噪声地形")

# 2. 放置方块（含透明方块）
blocks = [
    BlockData(x=0, y=0, z=0, r=1.0, g=0.0, b=0.0, a=1.0, type=0),
    BlockData(x=1, y=0, z=0, r=0.2, g=0.4, b=0.8, a=0.7, type=1),  # 水
    BlockData(x=2, y=0, z=0, r=0.8, g=0.9, b=1.0, a=0.4, type=2),  # 玻璃
]
renderer.render_placed_blocks(blocks)
print("[OK] render_placed_blocks x3 (含透明)")

# 3. 树
trees = [TreeData(x=10, z=10, base_height=3, height=4, width=2)]
renderer.render_trees(trees)
print("[OK] render_trees")

# 4. 建筑
locs = [LocationData(x=20, z=20, r=1.0, g=0.8, b=0.2, type=0)]
renderer.render_locations(locs)
print("[OK] render_locations")

# 5. 粒子
parts = [
    ParticleData(x=0, y=1, z=0, r=1.0, g=1.0, b=0.0, alpha=0.5, size=3.0),
    ParticleData(x=1, y=1, z=1, r=0.8, g=0.7, b=0.6, alpha=0.3, size=2.0),
]
renderer.render_particles(parts)
print("[OK] render_particles x2")

# 6. 玩家
from renderer_bindings import PlayerData, FollowerData
player = PlayerData(x=0, y=1, z=0, r=0.3, g=0.5, b=0.8, rotation=45.0)
renderer.render_player(player)
followers = [FollowerData(x=1, y=0, z=1, r=0.4, g=0.6, b=0.3, type=0)]
renderer.render_followers(followers)
print("[OK] render_player + render_followers")

pygame.display.flip()
print("ALL C++ RENDER CALLS OK")
