#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import platform
import pygame

# 字体文件路径
FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')

# 内置字体文件名
BUILTIN_FONTS = {
    'primary': 'NotoSansSC-Regular.ttf',      # 主要中文字体
    'bold': 'NotoSansSC-Bold.ttf',            # 粗体
    'light': 'NotoSansSC-Light.ttf',          # 细体
    'emoji': 'NotoColorEmoji.ttf'             # Emoji字体
}

def ensure_fonts():
    """确保字体文件存在，如果不存在则下载或使用系统字体"""
    os.makedirs(FONT_DIR, exist_ok=True)
    
    # 检查内置字体是否存在
    missing_fonts = []
    for font_name, filename in BUILTIN_FONTS.items():
        font_path = os.path.join(FONT_DIR, filename)
        if not os.path.exists(font_path):
            missing_fonts.append(filename)
    
    if missing_fonts:
        print(f"警告：缺少字体文件: {missing_fonts}")
        print("将使用系统字体作为备选")
        return False
    
    return True

def get_builtin_font_path(font_type='primary'):
    """获取内置字体文件路径"""
    filename = BUILTIN_FONTS.get(font_type, BUILTIN_FONTS['primary'])
    return os.path.join(FONT_DIR, filename)

def load_font(size, font_type='primary', bold=False):
    """加载字体，优先使用内置字体，失败则回退到系统字体"""
    try:
        # 优先尝试内置字体
        font_path = get_builtin_font_path(font_type if not bold else 'bold')
        if os.path.exists(font_path):
            return pygame.font.Font(font_path, size)
    except Exception as e:
        print(f"加载内置字体失败: {e}")
    
    # 回退到系统字体
    return get_system_font(size, bold)

def get_system_font(size, bold=False):
    """获取系统字体作为备选"""
    system = platform.system()
    
    font_names = []
    if system == "Windows":
        font_names = [
            "Microsoft YaHei",
            "SimHei",
            "Microsoft YaHei UI",
            "Segoe UI",
            "Arial"
        ]
    elif system == "Darwin":  # macOS
        font_names = [
            "PingFang SC",
            "Hiragino Sans GB",
            "Songti SC",
            "Helvetica"
        ]
    elif system == "Linux":
        font_names = [
            "Noto Sans CJK SC",
            "WenQuanYi Micro Hei",
            "SimHei",
            "DejaVu Sans"
        ]
    
    # 尝试加载系统字体
    for font_name in font_names:
        try:
            font = pygame.font.SysFont(font_name, size, bold=bold)
            if font:
                return font
        except Exception:
            continue
    
    # 最后的兜底方案
    return pygame.font.Font(None, size)

def load_font_with_fallback(size, font_type='primary'):
    """加载字体，提供完整的降级方案"""
    # 方案1：尝试内置字体
    try:
        font_path = get_builtin_font_path(font_type)
        if os.path.exists(font_path):
            return pygame.font.Font(font_path, size)
    except Exception:
        pass
    
    # 方案2：尝试系统字体
    try:
        system_font = get_system_font(size)
        if system_font:
            return system_font
    except Exception:
        pass
    
    # 方案3：使用Pygame默认字体
    return pygame.font.Font(None, size)

def load_all_fonts(base_size=24):
    """批量加载多种大小的字体"""
    fonts = {
        'title': load_font(base_size * 2),
        'large': load_font(base_size * 1.5),
        'normal': load_font(base_size),
        'small': load_font(base_size * 0.8),
        'tiny': load_font(base_size * 0.6)
    }
    return fonts

# 全局字体缓存
_font_cache = {}

def get_cached_font(size, font_type='primary'):
    """获取缓存的字体，避免重复加载"""
    key = (size, font_type)
    if key not in _font_cache:
        _font_cache[key] = load_font_with_fallback(size, font_type)
    return _font_cache[key]

def clear_font_cache():
    """清除字体缓存"""
    _font_cache.clear()
