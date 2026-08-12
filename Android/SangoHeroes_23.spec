# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ASSET', 'ASSET'), ('data', 'data'), ('ASSET/fonts', 'fonts')],
    hiddenimports=['ASSET.achievement_system', 'ASSET.activity_system', 'ASSET.ai_system', 'ASSET.alchemy_system', 'ASSET.anti_decompile', 'ASSET.auto_update', 'ASSET.background_story', 'ASSET.battle_system', 'ASSET.breakout', 'ASSET.building_system', 'ASSET.chat_server', 'ASSET.daily_checkin', 'ASSET.daily_reward_system', 'ASSET.dictionary_system', 'ASSET.dungeon_system', 'ASSET.effect_system', 'ASSET.equipment_system', 'ASSET.event_system', 'ASSET.faq_system', 'ASSET.fashion_system', 'ASSET.fishing_system', 'ASSET.font_manager', 'ASSET.fun_effects', 'ASSET.gameplay_systems', 'ASSET.game_2048', 'ASSET.game_data', 'ASSET.game_main_menu', 'ASSET.game_map_3d', 'ASSET.game_map_enhanced', 'ASSET.game_map_pygame', 'ASSET.gobang', 'ASSET.hero_collection_system', 'ASSET.hero_recruitment', 'ASSET.hero_warehouse', 'ASSET.languages', 'ASSET.limited_time_events', 'ASSET.login_system', 'ASSET.minesweeper', 'ASSET.modern_ui_system', 'ASSET.network_pvp', 'ASSET.newbie_guide', 'ASSET.p2p_ngrok', 'ASSET.pet_arena', 'ASSET.pet_system', 'ASSET.push_box', 'ASSET.pvp_online', 'ASSET.pvp_p2p', 'ASSET.pvp_super', 'ASSET.quest_system', 'ASSET.racing_mode', 'ASSET.ranking_system', 'ASSET.secure_network', 'ASSET.shop_system', 'ASSET.snake_game', 'ASSET.social_system', 'ASSET.strategy_map_system', 'ASSET.talent_system', 'ASSET.task_chain_system', 'ASSET.tech_tree', 'ASSET.tetris', 'ASSET.trading_system', 'ASSET.weather_system', 'ASSET.whiteboard', 'ASSET.world_chat', 'pkg_resources', 'jaraco.functools'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'numpy', 'pandas', 'scipy', 'matplotlib', 'torch', 'tensorflow', 'cv2', 'PyQt5', 'PySide2', 'PIL.ImageQt'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SangoHeroes_23',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
