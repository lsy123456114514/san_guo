# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

# 收集所有模块
hiddenimports = [
    'pygame',
    'OpenGL',
    'OpenGL.GL',
    'OpenGL.GLU',
    'math',
    'random',
    'time',
    'json',
    'sys',
]

# 添加ASSET下所有Python模块（须带包前缀，裸名会报 Hidden import not found）
asset_modules = [
    'achievement_system',
    'activity_system',
    'alchemy_system',
    'background_story',
    'battle_system',
    'building_system',
    'daily_checkin',
    'daily_reward_system',
    'dungeon_system',
    'equipment_system',
    'event_system',
    'fashion_system',
    'fishing_system',
    'game_data',
    'game_main_menu',
    'game_map_3d',
    'game_map_enhanced',
    'game_map_pygame',
    'gameplay_systems',
    'hero_collection_system',
    'hero_recruitment',
    'hero_warehouse',
    'login_system',
    'whiteboard',
    'dictionary_system',
    'pet_arena',
    'pet_system',
    'quest_system',
    'ranking_system',
    'shop_system',
    'strategy_map_system',
    'talent_system',
    'tech_tree',
    'trading_system',
    'weather_system',
]

for mod in asset_modules:
    hiddenimports.append('ASSET.' + mod)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ASSET', 'ASSET'),
        ('ASSET/fonts', 'ASSET/fonts'),
        ('ASSET/sounds', 'ASSET/sounds'),
        # C++ 渲染器 DLL（game_map_3d.py 在打包后从 _internal/ 查找）
        ('opengl_renderer.dll', '.'),
        ('renderer_bindings.py', '.'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'numpy.libs', 'setuptools', 'pip', 'tkinter',
              'PyQt5', 'matplotlib', 'scipy', 'pandas', 'PIL'],
    noarchive=False,
    optimize=0,
)

# 排除缓存字节码（运行时用不到，白占 ~3MB）
a.datas = [d for d in a.datas if '__pycache__' not in d[0]]

# 去重：pygame 子目录里的 DLL 与顶层同名 DLL 重复（~6MB），留顶层即可
def _bn(p):
    return os.path.basename(p.replace('/', os.sep)).lower()

def _dirname(p):
    return os.path.dirname(p.replace('/', os.sep))

_top = {_bn(d[0]) for d in a.binaries if _dirname(d[0]) in ('', '.')}
a.binaries = [d for d in a.binaries
              if _dirname(d[0]) in ('', '.') or _bn(d[0]) not in _top]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='三国名将传完整版',
    icon='ASSET/icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='三国名将传完整版',
)
