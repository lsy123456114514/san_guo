#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化渲染模块
提供高性能的渲染工具函数
"""

import pygame
import math
from functools import lru_cache

# 全局缓存字典
_surface_cache = {}
_gradient_cache = {}
_particle_cache = {}


def clear_cache():
    """清空所有缓存"""
    _surface_cache.clear()
    _gradient_cache.clear()
    _particle_cache.clear()


@lru_cache(maxsize=128)
def create_cached_surface(size, flags=0):
    """创建并缓存 Surface"""
    key = (size, flags)
    if key not in _surface_cache:
        _surface_cache[key] = pygame.Surface(size, flags)
    return _surface_cache[key].copy()


def draw_gradient_background_cached(surface, color1, color2, cache_key=None):
    """
    绘制渐变背景（缓存版）
    
    Args:
        surface: 目标 Surface
        color1: 起始颜色 (r, g, b)
        color2: 结束颜色 (r, g, b)
        cache_key: 缓存键，用于识别不同的渐变
    """
    width, height = surface.get_size()
    
    if cache_key is None:
        cache_key = (color1, color2, width, height)
    
    if cache_key not in _gradient_cache:
        # 生成并缓存渐变
        gradient_surf = pygame.Surface((width, height))
        for y in range(height):
            ratio = y / max(height, 1)
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(gradient_surf, (r, g, b), (0, y), (width, y))
        _gradient_cache[cache_key] = gradient_surf
    
    surface.blit(_gradient_cache[cache_key], (0, 0))


class CachedParticleRenderer:
    """缓存粒子渲染器"""
    
    def __init__(self):
        self.cache = {}
    
    def draw_circle(self, surface, x, y, size, color, alpha=255):
        """
        绘制圆形粒子（使用缓存）
        
        Args:
            surface: 目标 Surface
            x, y: 位置
            size: 大小
            color: 颜色 (r, g, b)
            alpha: 透明度
        """
        key = (size, color)
        
        if key not in self.cache:
            # 创建并缓存粒子
            surf_size = size * 2
            surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, 255), (size, size), size)
            self.cache[key] = surf
        
        cached_surf = self.cache[key]
        if alpha < 255:
            cached_surf = cached_surf.copy()
            cached_surf.set_alpha(alpha)
        
        surface.blit(cached_surf, (int(x - size), int(y - size)))
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


# 全局粒子渲染器实例
_particle_renderer = CachedParticleRenderer()


def draw_particle_cached(surface, x, y, size, color, alpha=255):
    """
    绘制粒子（全局缓存版）
    """
    _particle_renderer.draw_circle(surface, x, y, size, color, alpha)


class CachedLightRenderer:
    """缓存光晕渲染器"""
    
    def __init__(self):
        self.cache = {}
    
    def draw_glow(self, surface, x, y, radius, color, intensity=1.0):
        """
        绘制发光效果（使用缓存）
        
        Args:
            surface: 目标 Surface
            x, y: 位置
            radius: 半径
            color: 颜色 (r, g, b)
            intensity: 强度 0.0-1.0
        """
        key = (radius, color)
        
        if key not in self.cache:
            # 创建并缓存光晕
            surf_size = int(radius * 2 + 20)
            surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center = int(radius + 10)
            
            # 多层叠加产生光晕效果
            for r in range(int(radius), 0, -2):
                alpha = int(30 * (1 - r / radius))
                pygame.draw.circle(surf, (*color, alpha), (center, center), r)
            
            self.cache[key] = surf
        
        cached_surf = self.cache[key]
        if intensity < 1.0:
            cached_surf = cached_surf.copy()
            cached_surf.set_alpha(int(255 * intensity))
        
        offset = int(radius + 10)
        surface.blit(cached_surf, (int(x - offset), int(y - offset)))
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


# 全局光晕渲染器实例
_light_renderer = CachedLightRenderer()


def draw_glow_cached(surface, x, y, radius, color, intensity=1.0):
    """
    绘制光晕（全局缓存版）
    """
    _light_renderer.draw_glow(surface, x, y, radius, color, intensity)


class FPSCounter:
    """FPS 计数器"""
    
    def __init__(self, history_size=30):
        self.frame_times = []
        self.history_size = history_size
        self.last_time = None
    
    def begin_frame(self):
        """开始一帧"""
        self.last_time = pygame.time.get_ticks()
    
    def end_frame(self):
        """结束一帧，返回当前 FPS"""
        if self.last_time is None:
            return 0
        
        current_time = pygame.time.get_ticks()
        frame_time = current_time - self.last_time
        
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.history_size:
            self.frame_times.pop(0)
        
        if len(self.frame_times) > 0:
            avg_time = sum(self.frame_times) / len(self.frame_times)
            return 1000 / max(avg_time, 1)
        
        return 0
    
    def get_fps(self):
        """获取当前 FPS"""
        if len(self.frame_times) > 0:
            avg_time = sum(self.frame_times) / len(self.frame_times)
            return 1000 / max(avg_time, 1)
        return 0
    
    def draw_fps(self, surface, x, y, font, color=(255, 255, 255)):
        """在屏幕上绘制 FPS"""
        fps = self.get_fps()
        text = font.render(f"FPS: {fps:.1f}", True, color)
        surface.blit(text, (x, y))


# 性能优化装饰器
def benchmark(func):
    """
    性能测试装饰器
    打印函数执行时间
    """
    import time
    
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 耗时: {(end - start) * 1000:.2f}ms")
        return result
    
    return wrapper


# 简单的对象池实现
class ObjectPool:
    """对象池 - 用于减少频繁创建/销毁对象的开销"""
    
    def __init__(self, create_func, initial_size=10):
        """
        Args:
            create_func: 创建对象的函数
            initial_size: 初始大小
        """
        self.create_func = create_func
        self.pool = [create_func() for _ in range(initial_size)]
        self.in_use = []
    
    def acquire(self):
        """获取一个对象"""
        if self.pool:
            obj = self.pool.pop()
        else:
            obj = self.create_func()
        self.in_use.append(obj)
        return obj
    
    def release(self, obj):
        """归还一个对象"""
        if obj in self.in_use:
            self.in_use.remove(obj)
            self.pool.append(obj)
    
    def release_all(self):
        """归还所有在用对象"""
        self.pool.extend(self.in_use)
        self.in_use.clear()


# 导出主要组件
__all__ = [
    'clear_cache',
    'draw_gradient_background_cached',
    'CachedParticleRenderer',
    'draw_particle_cached',
    'CachedLightRenderer',
    'draw_glow_cached',
    'FPSCounter',
    'benchmark',
    'ObjectPool',
]
