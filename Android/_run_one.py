# -*- coding: utf-8 -*-
"""单个模块 dummy 测试入口：python run_one.py <模块名>"""
import os, sys, time, threading
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
sys.path.insert(0, r'c:\Users\a\Desktop\san_guo\Android')
os.chdir(r'c:\Users\a\Desktop\san_guo\Android')
import pygame

def q():
    time.sleep(1.0)
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    except Exception:
        pass

threading.Thread(target=q, daemon=True).start()

mod = sys.argv[1]
try:
    m = __import__('ASSET.' + mod, fromlist=['main'])
    if hasattr(m, 'main'):
        m.main()
        print('OK')
    else:
        print('NO_MAIN')
except SystemExit:
    print('SYSTEM_EXIT')
except Exception as e:
    print('EXC:', type(e).__name__, e)
