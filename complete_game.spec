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
    'numpy',
    'math',
    'random',
    'time',
    'json',
    'sys',
]

# 添加ASSET下所有Python模块
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
    hiddenimports.append(mod)

a = Analysis(
    ['ASSET\\game_main_menu.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ASSET', 'ASSET'),
        ('ASSET/fonts', 'ASSET/fonts'),
        ('ASSET/sounds', 'ASSET/sounds'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='三国名将传完整版',
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
