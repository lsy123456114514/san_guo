# -*- coding: utf-8 -*-
"""临时测试：真实窗口跑 shop_system.main()，3秒后自动QUIT，捕获异常"""
import sys
import threading
import time

BASE = r'c:\Users\a\Desktop\san_guo\Android'
sys.path.insert(0, BASE)
import os
os.chdir(BASE)

import pygame

def quit_soon():
    time.sleep(3)
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    except Exception:
        pass

threading.Thread(target=quit_soon, daemon=True).start()

try:
    from ASSET import shop_system
    shop_system.main()
    print('SHOP_OK - main() 正常返回')
except Exception as e:
    import traceback
    print('异常:', type(e).__name__, e)
    traceback.print_exc()
