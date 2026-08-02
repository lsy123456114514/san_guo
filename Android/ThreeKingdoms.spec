# -*- mode: python ; coding: utf-8 -*-
"""
三国群英传游戏打包配置
包含所有必要的依赖和资源文件
版本信息：v1.0.0
开发者：三国游戏开发团队
"""

import sys
import os

# 获取当前目录（在spec文件中使用sys.argv[0]）
current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# 定义资源目录
asset_dir = os.path.join(current_dir, 'ASSET')
data_dir = os.path.join(current_dir, 'data')
voice_dir = os.path.join(current_dir, 'voice_data')
fonts_dir = os.path.join(asset_dir, 'fonts')
logs_dir = os.path.join(asset_dir, 'logs')

# 收集所有需要打包的数据文件
datas = [
    # 核心资源目录
    (asset_dir, 'ASSET'),
    (data_dir, 'data'),
    (voice_dir, 'voice_data'),
    
    # 单独的资源文件
    ('map_data_lsy.json', '.'),
    ('map_data_weqwqewq.json', '.'),
    
    # C++渲染器相关
    ('opengl_renderer.dll', '.'),
    ('renderer_bindings.py', '.'),
]

# 二进制文件
binaries = [
    ('opengl_renderer.dll', '.'),
]

# 隐藏导入（确保所有依赖都被打包）
hiddenimports = [
    'pkg_resources',
    'pygame',
    'pygame._view',
    'json',
    'os',
    'sys',
    'time',
    'random',
    'math',
    'platform',
    'threading',
    'socket',
    'datetime',
    'traceback',
    'collections',
    'typing',
    'hashlib',
    'shutil',
    'subprocess',
    
    # ASSET模块
    'ASSET.game_data',
    'ASSET.game_main_menu',
    'ASSET.battle_system',
    'ASSET.font_manager',
    'ASSET.login_system',
    'ASSET.logger',
    'ASSET.pet_system',
    'ASSET.pet_arena',
    'ASSET.dictionary_system',
    'ASSET.weather_system',
    'ASSET.event_system',
    'ASSET.equipment_system',
    'ASSET.hero_recruitment',
    'ASSET.hero_collection_system',
    'ASSET.hero_warehouse',
    'ASSET.task_chain_system',
    'ASSET.quest_system',
    'ASSET.daily_checkin',
    'ASSET.daily_reward_system',
    'ASSET.shop_system',
    'ASSET.trading_system',
    'ASSET.ranking_system',
    'ASSET.social_system',
    'ASSET.world_chat',
    'ASSET.pvp_super',
    'ASSET.network_pvp',
    'ASSET.p2p_ngrok',
    'ASSET.secure_network',
    'ASSET.dungeon_system',
    'ASSET.fishing_system',
    'ASSET.alchemy_system',
    'ASSET.building_system',
    'ASSET.talent_system',
    'ASSET.tech_tree',
    'ASSET.fashion_system',
    'ASSET.achievement_system',
    'ASSET.activity_system',
    'ASSET.limited_time_events',
    'ASSET.newbie_guide',
    'ASSET.modern_ui_system',
    'ASSET.optimized_render',
    'ASSET.visual_effects',
    'ASSET.fun_effects',
    'ASSET.gameplay_systems',
    'ASSET.game_map_3d',
    'ASSET.game_map_pygame',
    'ASSET.game_map_enhanced',
    'ASSET.whiteboard',
    'ASSET.faq_system',
    'ASSET.languages',
    'ASSET.anti_decompile',
    'ASSET.auto_update',
    'ASSET.background_story',
    'ASSET.chat_server',
    'ASSET.config_manager',
    'ASSET.security_utils',
    
    # 小游戏模块
    'ASSET.snake_game',
    'ASSET.push_box',
    'ASSET.breakout',
    'ASSET.minesweeper',
    'ASSET.game_2048',
    'ASSET.tetris',
    'ASSET.gobang',
    
    # AI相关
    'ASSET.ai_system',
]

# 排除不必要的模块以减小体积
excludes = [
    'tkinter',
    'PyQt5',
    'PyQt6',
    'wx',
    'numpy',
    'scipy',
    'matplotlib',
    'pandas',
    'tensorflow',
    'torch',
    'sklearn',
    'PIL',
    'imageio',
    'moviepy',
    'pywin32',
    'win32com',
]

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ThreeKingdoms',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)