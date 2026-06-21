#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'e:\\san_guo\\py c++')

import os
import pygame

# 初始化pygame
pygame.init()

# 测试字体加载
print("=== 字体加载测试 ===")

# 检查字体文件路径
font_dir = os.path.join('e:\\san_guo\\py c++\\ASSET', 'fonts')
font_path = os.path.join(font_dir, '字魂白鸽天行体(商用需授权).ttf')
print(f"字体目录: {font_dir}")
print(f"字体文件: {font_path}")
print(f"文件存在: {os.path.exists(font_path)}")
print(f"文件大小: {os.path.getsize(font_path) if os.path.exists(font_path) else 'N/A'} bytes")

# 尝试加载字体
try:
    font = pygame.font.Font(font_path, 40)
    print("✓ pygame.font.Font加载成功")
    
    # 渲染测试文字
    text_surface = font.render("测试中文字体", True, (255, 255, 255))
    print("✓ 文字渲染成功")
    print(f"渲染表面尺寸: {text_surface.get_size()}")
    
except Exception as e:
    print(f"✗ 加载失败: {type(e).__name__}: {e}")

# 测试font_manager
print("\n=== font_manager测试 ===")
try:
    from ASSET.font_manager import load_font, get_builtin_font_path, FONT_DIR, BUILTIN_FONTS
    
    print(f"FONT_DIR: {FONT_DIR}")
    print(f"BUILTIN_FONTS: {BUILTIN_FONTS}")
    print(f"get_builtin_font_path('primary'): {get_builtin_font_path('primary')}")
    
    font = load_font(40)
    print("✓ load_font加载成功")
    
    # 检查是否使用了内置字体
    if font.path:
        print(f"字体路径: {font.path}")
        if '字魂白鸽' in font.path:
            print("✓ 成功使用了字魂白鸽字体！")
        else:
            print(f"✗ 使用的是其他字体: {os.path.basename(font.path)}")
    else:
        print("✗ 使用的是默认字体(None)")
        
except Exception as e:
    print(f"✗ font_manager测试失败: {type(e).__name__}: {e}")

print("\n=== 测试完成 ===")
pygame.quit()
