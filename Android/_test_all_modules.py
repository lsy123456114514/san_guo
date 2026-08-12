# -*- coding: utf-8 -*-
"""临时批量测试：dummy 驱动跑 MODULE_ROUTES 中所有模块的 main()，逐个捕获异常"""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import sys
import threading
import time

BASE = r'c:\Users\a\Desktop\san_guo\Android'
sys.path.insert(0, BASE)
os.chdir(BASE)

import pygame

def quit_soon(sec):
    time.sleep(sec)
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    except Exception:
        pass

MODULES = [
    "pvp_p2p.py", "game_map_pygame.py", "game_map_3d.py",
    "newbie_guide.py", "background_story.py", "battle_system.py", "hero_warehouse.py",
    "activity_system.py", "tech_tree.py", "building_system.py", "talent_system.py",
    "achievement_system.py", "ranking_system.py", "daily_checkin.py", "shop_system.py",
    "social_system.py", "equipment_system.py", "trading_system.py", "pet_system.py",
    "fashion_system.py", "quest_system.py", "fishing_system.py", "alchemy_system.py",
    "ai_system.py", "faq_system.py", "weather_system.py", "limited_time_events.py",
    "pet_arena.py", "mini_games_menu",
]

ok = []
fail = []

for mod_name in MODULES:
    print('=' * 50)
    print('测试模块:', mod_name)
    threading.Thread(target=quit_soon, args=(1.2,), daemon=True).start()
    try:
        mod = __import__('ASSET.' + mod_name[:-3] if mod_name.endswith('.py') else 'ASSET.' + mod_name,
                         fromlist=['main'])
        if hasattr(mod, 'main'):
            mod.main()
            print('OK - main() 正常返回')
            ok.append(mod_name)
        else:
            print('FAIL - 没有 main() 函数')
            fail.append((mod_name, 'no main()'))
    except SystemExit:
        print('OK - SystemExit(安全退出) 被捕获')
        ok.append(mod_name)
    except Exception as e:
        import traceback
        print('异常:', type(e).__name__, e)
        traceback.print_exc()
        fail.append((mod_name, f'{type(e).__name__}: {e}'))
    time.sleep(0.2)

print()
print('=' * 50)
print('OK 模块:', len(ok))
for m in ok:
    print('  [OK]', m)
print('FAIL 模块:', len(fail))
for m, e in fail:
    print('  [FAIL]', m, '->', e)
