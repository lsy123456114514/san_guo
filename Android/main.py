#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MC风格三国游戏 - Android重构版
仅修改 Android 文件夹
"""
import os
import sys

# 安卓路径适配
if 'ANDROID_DATA' in os.environ:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'ASSET'))

# 初始化pygame
import pygame

# 屏幕设置
if 'ANDROID_DATA' in os.environ:
    pygame.init()
    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
else:
    pygame.init()
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("MC风格三国 - MC Kingdoms")
clock = pygame.time.Clock()

# 导入MC风格3D游戏
from ASSET.game_map_3d import GameMap3D

def main():
    """主函数"""
    try:
        # 创建MC游戏实例
        game = GameMap3D()
        
        # 初始化游戏
        if not game.initialize():
            print("游戏初始化失败！")
            pygame.quit()
            return False
        
        # 运行游戏主循环
        running = game.main()
        
        # 清理
        pygame.quit()
        return running
        
    except Exception as e:
        print(f"游戏运行错误: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        return False

if __name__ == "__main__":
    main()
