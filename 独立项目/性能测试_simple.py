#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版性能测试脚本
"""

import pygame
import time
import random

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TEST_FRAMES = 100

COLORS = {
    "bg": (20, 20, 30),
    "gold": (255, 215, 0)
}


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(2, 6)
        self.color = COLORS["gold"]
        self.life = 100
        self.max_life = 100
    
    def update(self):
        self.life -= 1
        self.size = max(1, self.size - 0.05)
    
    def is_alive(self):
        return self.life > 0


def test_naive_particles():
    """测试原始粒子渲染"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    particles = [Particle(random.randint(0, SCREEN_WIDTH), 
                         random.randint(0, SCREEN_HEIGHT)) 
                for _ in range(300)]
    
    start = time.time()
    for _ in range(TEST_FRAMES):
        screen.fill(COLORS["bg"])
        for p in particles:
            p.update()
            if not p.is_alive():
                p.x = random.randint(0, SCREEN_WIDTH)
                p.y = random.randint(0, SCREEN_HEIGHT)
                p.life = p.max_life
                p.size = random.randint(2, 6)
            
            # 原始方式：每帧创建新 Surface
            size = int(p.size)
            surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            alpha = int(255 * (p.life / p.max_life))
            pygame.draw.circle(surf, (*COLORS["gold"], alpha), (size, size), size)
            screen.blit(surf, (int(p.x - size), int(p.y - size)))
        
        pygame.display.flip()
    
    elapsed = time.time() - start
    pygame.display.quit()
    return TEST_FRAMES / elapsed


# 粒子缓存
particle_cache = {}

def test_cached_particles():
    """测试缓存粒子渲染"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    particles = [Particle(random.randint(0, SCREEN_WIDTH), 
                         random.randint(0, SCREEN_HEIGHT)) 
                for _ in range(300)]
    
    global particle_cache
    particle_cache.clear()
    
    start = time.time()
    for _ in range(TEST_FRAMES):
        screen.fill(COLORS["bg"])
        for p in particles:
            p.update()
            if not p.is_alive():
                p.x = random.randint(0, SCREEN_WIDTH)
                p.y = random.randint(0, SCREEN_HEIGHT)
                p.life = p.max_life
                p.size = random.randint(2, 6)
            
            # 优化方式：使用缓存
            size = int(p.size)
            alpha = int(255 * (p.life / p.max_life))
            
            key = (size, COLORS["gold"])
            if key not in particle_cache:
                surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*COLORS["gold"], 255), (size, size), size)
                particle_cache[key] = surf
            
            cached_surf = particle_cache[key]
            cached_surf.set_alpha(alpha)
            screen.blit(cached_surf, (int(p.x - size), int(p.y - size)))
        
        pygame.display.flip()
    
    elapsed = time.time() - start
    pygame.display.quit()
    return TEST_FRAMES / elapsed


def test_naive_background():
    """测试原始背景渲染"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    start = time.time()
    for _ in range(TEST_FRAMES):
        # 原始方式：每帧逐行绘制渐变
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(40 * (1 - ratio) + 20 * ratio)
            g = int(20 * (1 - ratio) + 10 * ratio)
            b = int(30 * (1 - ratio) + 40 * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        pygame.display.flip()
    
    elapsed = time.time() - start
    pygame.display.quit()
    return TEST_FRAMES / elapsed


# 背景缓存
bg_cache = None

def test_cached_background():
    """测试缓存背景渲染"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    global bg_cache
    bg_cache = None
    
    start = time.time()
    for _ in range(TEST_FRAMES):
        # 优化方式：使用缓存
        if bg_cache is None:
            bg_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for y in range(SCREEN_HEIGHT):
                ratio = y / SCREEN_HEIGHT
                r = int(40 * (1 - ratio) + 20 * ratio)
                g = int(20 * (1 - ratio) + 10 * ratio)
                b = int(30 * (1 - ratio) + 40 * ratio)
                pygame.draw.line(bg_cache, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        screen.blit(bg_cache, (0, 0))
        pygame.display.flip()
    
    elapsed = time.time() - start
    pygame.display.quit()
    return TEST_FRAMES / elapsed


def main():
    print("="*60)
    print("三国游戏 - 简化性能测试")
    print("="*60)
    
    print("\n正在测试...")
    
    fps_naive_particle = test_naive_particles()
    fps_cached_particle = test_cached_particles()
    fps_naive_bg = test_naive_background()
    fps_cached_bg = test_cached_background()
    
    print("\n" + "="*60)
    print("测试结果")
    print("="*60)
    print(f"{'测试项':<20} | {'原始FPS':<10} | {'优化FPS':<10} | {'提升倍数':<10}")
    print("-"*60)
    print(f"{'粒子渲染':<20} | {fps_naive_particle:<10.1f} | {fps_cached_particle:<10.1f} | {(fps_cached_particle/fps_naive_particle):<10.2f}x")
    print(f"{'背景渲染':<20} | {fps_naive_bg:<10.1f} | {fps_cached_bg:<10.1f} | {(fps_cached_bg/fps_naive_bg):<10.2f}x")
    print("="*60)
    
    print("\n测试完成！")
    print("\n结论：通过简单的缓存优化，可以获得显著的性能提升！")
    
    pygame.quit()


if __name__ == "__main__":
    main()
