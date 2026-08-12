# -*- coding: utf-8 -*-
"""临时测试：dummy 驱动跑 shop_system / game_map_3d 的 main()，2秒后自动QUIT"""
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

def quit_soon():
    time.sleep(2)
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    except Exception:
        pass

threading.Thread(target=quit_soon, daemon=True).start()

def run(mod_name):
    print('=' * 40)
    print('测试模块:', mod_name)
    try:
        mod = __import__('ASSET.' + mod_name, fromlist=['main'])
        if hasattr(mod, 'main'):
            mod.main()
            print('OK - main() 正常返回')
        else:
            print('FAIL - 没有 main() 函数')
    except Exception as e:
        import traceback
        print('异常:', type(e).__name__, e)
        traceback.print_exc()

run('shop_system')
run('game_map_3d')
print('ALL DONE')
