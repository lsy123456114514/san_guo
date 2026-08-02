# -*- mode: python ; coding: utf-8 -*-

import os

VERSION_FILE = 'version.txt'

def get_next_version():
    """获取下一个版本号"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            try:
                version = int(f.read().strip())
            except:
                version = 1
    else:
        version = 1
    version += 1
    with open(VERSION_FILE, 'w') as f:
        f.write(str(version))
    return version

def get_versioned_exe_name(base_name, output_dir='dist'):
    """生成带递增版本号的exe文件名"""
    version = get_next_version()
    return f"{base_name}_{version}.exe"


block_cipher = None


a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[('ASSET', 'ASSET'), ('data', 'data')],
             hiddenimports=['pygame', 'ASSET.battle_system', 'ASSET.game_data', 'ASSET.hero_database', 'ASSET.equipment_system', 'ASSET.weather_system', 'ASSET.event_system', 'ASSET.welfare_center', 'ASSET.formation_system', 'ASSET.divine_weapon_system', 'ASSET.achievement_system', 'ASSET.ai_system', 'ASSET.shop_system', 'ASSET.login_system', 'ASSET.quest_system', 'ASSET.hero_recruitment', 'ASSET.hero_collection_system', 'ASSET.modern_ui_system', 'ASSET.fashion_system', 'ASSET.pet_system', 'ASSET.mount_system', 'ASSET.alchemy_system', 'ASSET.dungeon_system', 'ASSET.pvp_super', 'ASSET.network_pvp', 'ASSET.social_system', 'ASSET.trading_system', 'ASSET.strategy_map_system', 'ASSET.bug_report_system', 'ASSET.checkin_center', 'ASSET.config_editor', 'ASSET.custom_hero_editor', 'ASSET.data_access_layer', 'ASSET.data_validator', 'ASSET.developer_console', 'ASSET.equipment_management', 'ASSET.event_center', 'ASSET.game_state_manager', 'ASSET.hero_management', 'ASSET.hero_rebirth_system', 'ASSET.legion_system', 'ASSET.log_system', 'ASSET.official_rank_system', 'ASSET.ranking_center', 'ASSET.subordinate_system', 'ASSET.font_manager', 'ASSET.languages', 'ASSET.logger', 'ASSET.security_utils', 'ASSET.anti_decompile', 'ASSET.auto_update', 'ASSET.background_story', 'ASSET.breakout', 'ASSET.building_system', 'ASSET.chat_server', 'ASSET.config_manager', 'ASSET.daily_checkin', 'ASSET.daily_reward_system', 'ASSET.dictionary_system', 'ASSET.effect_system', 'ASSET.faq_system', 'ASSET.fishing_system', 'ASSET.fun_effects', 'ASSET.game_2048', 'ASSET.game_main_menu', 'ASSET.game_map_3d', 'ASSET.game_map_enhanced', 'ASSET.game_map_pygame', 'ASSET.gameplay_systems', 'ASSET.gobang', 'ASSET.hero_warehouse', 'ASSET.limited_time_events', 'ASSET.minesweeper', 'ASSET.newbie_guide', 'ASSET.optimized_render', 'ASSET.p2p_ngrok', 'ASSET.pet_arena', 'ASSET.push_box', 'ASSET.ranking_system', 'ASSET.secure_network', 'ASSET.snake_game', 'ASSET.talent_system', 'ASSET.task_chain_system', 'ASSET.tech_tree', 'ASSET.tetris', 'ASSET.visual_effects', 'ASSET.whiteboard', 'ASSET.world_chat', 'ASSET.activity_system'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['tkinter', 'PyQt5', 'wx', 'numpy', 'scipy', 'matplotlib', 'pandas', 'tensorflow', 'torch', 'sklearn'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe_name = get_versioned_exe_name('SangoHeroes')

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name=exe_name,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
