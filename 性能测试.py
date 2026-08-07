#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国游戏性能测试脚本
测试不同渲染方式的性能表现
"""

import pygame
import time
import sys
import random
import math

# 初始化 Pygame
pygame.init()

# 测试配置
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TEST_FRAMES = 200

# 颜色定义
COLORS = {
    "bg_dark": (20, 20, 30),
    "accent_gold": (255, 215, 0),
    "accent_red": (255, 100, 50),
    "accent_blue": (100, 149, 237),
    "text_white": (255, 255, 255)
}


class Particle:
    """粒子类"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.size = random.randint(2, 8)
        self.life = random.randint(100, 200)
        self.color = random.choice([
            COLORS["accent_gold"],
            COLORS["accent_red"],
            COLORS["accent_blue"]
        ])
        self.max_life = self.life
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(1, self.size - 0.05)
    
    def is_alive(self):
        return self.life > 0


def test_particle_rendering_naive(screen, particles):
    """原始粒子渲染 - 每帧创建新 Surface"""
    for p in particles:
        if p.is_alive():
            size = int(p.size)
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            alpha = int(255 * (p.life / p.max_life))
            color = (*p.color[:3], alpha)
            pygame.draw.circle(surf, color, (size, size), size)
            screen.blit(surf, (int(p.x - size), int(p.y - size)))


# 粒子缓存
particle_cache = {}

def test_particle_rendering_cached(screen, particles):
    """优化版粒子渲染 - 使用缓存"""
    global particle_cache
    
    for p in particles:
        if p.is_alive():
            size = int(p.size)
            alpha = int(255 * (p.life / p.max_life))
            color = p.color[:3]
            
            # 缓存键
            cache_key = (size, color)
            
            if cache_key not in particle_cache:
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*color, 255), (size, size), size)
                particle_cache[cache_key] = surf
            
            # 使用缓存并设置透明度
            cached_surf = particle_cache[cache_key]
            cached_surf.set_alpha(alpha)
            screen.blit(cached_surf, (int(p.x - size), int(p.y - size)))


def test_background_rendering_naive(screen):
    """原始背景渲染 - 每帧逐行绘制渐变"""
    width, height = screen.get_size()
    for y in range(height):
        ratio = y / height
        r = int(40 * (1 - ratio) + 20 * ratio)
        g = int(20 * (1 - ratio) + 10 * ratio)
        b = int(30 * (1 - ratio) + 40 * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))


# 背景缓存
bg_cache = None

def test_background_rendering_cached(screen):
    """优化版背景渲染 - 使用缓存"""
    global bg_cache
    
    if bg_cache is None or bg_cache.get_size() != screen.get_size():
        width, height = screen.get_size()
        bg_cache = pygame.Surface((width, height))
        for y in range(height):
            ratio = y / height
            r = int(40 * (1 - ratio) + 20 * ratio)
            g = int(20 * (1 - ratio) + 10 * ratio)
            b = int(30 * (1 - ratio) + 40 * ratio)
            pygame.draw.line(bg_cache, (r, g, b), (0, y), (width, y))
    
    screen.blit(bg_cache, (0, 0))


def run_test(test_name, test_func, setup_func=None):
    """运行性能测试"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    # 准备数据
    particles = []
    if "particle" in test_name.lower():
        particles = [Particle(random.randint(0, SCREEN_WIDTH), 
                             random.randint(0, SCREEN_HEIGHT)) 
                    for _ in range(500)]
    
    # 预热
    if setup_func:
        setup_func(screen)
    
    # 测试
    start_time = time.time()
    frame_count = 0
    
    while frame_count < TEST_FRAMES:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        
        screen.fill(COLORS["bg_dark"])
        
        # 更新粒子
        for p in particles:
            p.update()
            if not p.is_alive():
                p.x = random.randint(0, SCREEN_WIDTH)
                p.y = random.randint(0, SCREEN_HEIGHT)
                p.life = p.max_life
                p.size = random.randint(2, 8)
        
        # 执行测试
        if "particle" in test_name.lower() and particles:
            test_func(screen, particles)
        else:
            test_func(screen)
        
        pygame.display.flip()
        frame_count += 1
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed
    
    print(f"总帧数: {frame_count}")
    print(f"总时间: {elapsed:.3f} 秒")
    print(f"平均 FPS: {fps:.2f}")
    print(f"每帧耗时: {(1000/fps):.2f} 毫秒")
    
    pygame.display.quit()
    return fps


def main():
    """主函数"""
    print("="*60)
    print("三国游戏性能测试工具")
    print("="*60)
    print(f"Pygame 版本: {pygame.version.ver}")
    print(f"屏幕分辨率: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"测试帧数: {TEST_FRAMES}")
    
    results = {}
    
    # 测试 1: 原始粒子渲染
    results["粒子_原始"] = run_test(
        "粒子渲染 (原始版)", 
        test_particle_rendering_naive
    )
    
    # 清空缓存
    global particle_cache
    particle_cache = {}
    
    # 测试 2: 优化粒子渲染
    results["粒子_优化"] = run_test(
        "粒子渲染 (优化版 - 缓存)", 
        test_particle_rendering_cached
    )
    
    # 测试 3: 原始背景渲染
    global bg_cache
    bg_cache = None
    results["背景_原始"] = run_test(
        "背景渲染 (原始版)", 
        test_background_rendering_naive
    )
    
    # 测试 4: 优化背景渲染
    bg_cache = None
    results["背景_优化"] = run_test(
        "背景渲染 (优化版 - 缓存)", 
        test_background_rendering_cached
    )
    
    # 总结
    print("\n" + "="*60)
    print("性能对比总结")
    print("="*60)
    print(f"{'测试项':<20} {'FPS':<10} {'提升倍数':<10}")
    print("-"*40)
    
    if "粒子_原始" in results and "粒子_优化" in results:
        speedup = results["粒子_优化"] / results["粒子_原始"]
        print(f"{'粒子渲染':<20} {results['粒子_优化']:<10.2f} {speedup:<10.2f}x")
    
    if "背景_原始" in results and "背景_优化" in results:
        speedup = results["背景_优化"] / results["背景_原始"]
        print(f"{'背景渲染':<20} {results['背景_优化']:<10.2f} {speedup:<10.2f}x")
    
    print("="*60)
    print("\n测试完成！按任意键退出...")
    
    # 等待用户按键
    pygame.init()
    screen = pygame.display.set_mode((400, 100))
    pygame.display.set_caption("测试完成")
    font = pygame.font.Font(None, 24)
    text = font.render("按任意键退出", True, COLORS["text_white"])
    screen.blit(text, (100, 40))
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
    
    pygame.quit()


if __name__ == "__main__":
    main()
