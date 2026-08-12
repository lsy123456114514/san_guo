# -*- coding: utf-8 -*-
"""临时测试：模拟从主菜单 run_module 进入商城，3秒后自动QUIT"""
import sys
import threading
import time

BASE = r'c:\Users\a\Desktop\san_guo\Android'
sys.path.insert(0, BASE)
import os
os.chdir(BASE)

import pygame
pygame.init()
screen = pygame.display.set_mode((900, 700))

from ASSET import game_main_menu as gmm
gmm.screen = screen
gmm.clock = pygame.time.Clock()

def quit_soon():
    time.sleep(3)
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    except Exception:
        pass

threading.Thread(target=quit_soon, daemon=True).start()

try:
    gmm.run_module('shop_system.py')
    print('MENU_SHOP_OK - 返回主菜单')
    print('窗口尺寸:', pygame.display.get_surface().get_size())
except Exception as e:
    import traceback
    print('异常:', type(e).__name__, e)
    traceback.print_exc()
