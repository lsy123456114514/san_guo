# -*- coding: utf-8 -*-
"""批量测试：subprocess 逐个跑模块，超时保护"""
import os, subprocess, sys, time

BASE = r'c:\Users\a\Desktop\san_guo\Android'
PY = r'G:\软件\python\python.exe'

MODULES = [
    "pvp_p2p", "game_map_pygame", "game_map_3d", "hero_recruitment",
    "newbie_guide", "background_story", "battle_system", "hero_warehouse",
    "activity_system", "tech_tree", "building_system", "talent_system",
    "achievement_system", "ranking_system", "daily_checkin", "shop_system",
    "social_system", "equipment_system", "trading_system", "pet_system",
    "fashion_system", "quest_system", "fishing_system", "alchemy_system",
    "ai_system", "faq_system", "weather_system", "limited_time_events",
    "pet_arena", "dictionary_system", "dungeon_system", "event_system",
    "fishing_system", "mini_games",
]

ok, fail = [], []
for m in MODULES:
    t0 = time.time()
    try:
        r = subprocess.run([PY, '_run_one.py', m], cwd=BASE, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=30)
        out = (r.stdout or '').strip().splitlines()[-1:] or ['']
        line = out[0].strip() if out else ''
        dt = time.time() - t0
        if r.returncode == 0 and (line == 'OK' or line == 'SYSTEM_EXIT'):
            print(f'[{dt:5.1f}s] OK     {m}')
            ok.append(m)
        else:
            print(f'[{dt:5.1f}s] FAIL   {m}  ->  {line} (rc={r.returncode})')
            if r.returncode != 0:
                err = (r.stderr or '').strip().splitlines()
                print('        stderr:', (err[-2] if len(err) >= 2 else err[-1] if err else '')[:200])
            fail.append((m, line or f'rc={r.returncode}'))
    except subprocess.TimeoutExpired:
        print(f'[timeout] TIMEOUT {m}')
        fail.append((m, 'TIMEOUT'))

print()
print('OK:', len(ok), ' FAIL:', len(fail))
for m in ok:
    print('  [OK]', m)
for m, e in fail:
    print('  [FAIL]', m, '->', e)
