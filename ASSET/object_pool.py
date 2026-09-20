#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用对象池系统 - 减少 GC 压力，提升粒子/子弹/特效性能"""

import logging
import pygame

logger = logging.getLogger(__name__)


class ObjectPool:
    """通用对象池，支持任意可复用对象"""

    def __init__(self, factory, reset_fn=None, initial_size=64, max_size=2048):
        """
        Args:
            factory: 无参工厂函数，返回新对象
            reset_fn: reset_fn(obj) 将对象重置为初始状态
            initial_size: 初始预分配数量
            max_size: 池上限
        """
        self._factory = factory
        self._reset_fn = reset_fn or (lambda o: None)
        self._max = max_size
        self._pool = []
        self._active = 0
        # 预热
        for _ in range(min(initial_size, max_size)):
            self._pool.append(factory())

    def acquire(self):
        """从池中获取一个对象（池空则新建）"""
        if self._pool:
            obj = self._pool.pop()
        else:
            try:
                obj = self._factory()
            except Exception as e:
                logger.debug("[ObjectPool] 工厂创建失败: %s", e)
                return None
        self._active += 1
        return obj

    def release(self, obj):
        """归还对象到池中"""
        if obj is None:
            return
        self._active -= 1
        if len(self._pool) < self._max:
            self._reset_fn(obj)
            self._pool.append(obj)

    def release_many(self, objs):
        """批量归还"""
        for o in objs:
            self.release(o)

    def prewarm(self, count):
        """预热：提前创建对象填充池"""
        for _ in range(min(count, self._max - len(self._pool))):
            self._pool.append(self._factory())

    @property
    def free_count(self):
        return len(self._pool)

    @property
    def active_count(self):
        return self._active

    @property
    def total_count(self):
        return len(self._pool) + self._active

    def clear(self):
        """清空池"""
        self._pool.clear()
        self._active = 0


# ─── 粒子对象池 ────────────────────────────────────────────

class PooledParticle:
    """池化粒子：避免每帧 new/dict 创建"""
    __slots__ = ('x', 'y', 'vx', 'vy', 'size', 'life', 'max_life',
                 'color', 'alpha', 'shape', 'active')

    def __init__(self):
        self.reset()
        self.active = False

    def reset(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.size = 3.0
        self.life = 60
        self.max_life = 60
        self.color = (255, 255, 255)
        self.alpha = 255
        self.shape = 'circle'
        self.active = False


def _reset_particle(p):
    p.active = False


# 全局粒子池（各系统共用）
particle_pool = ObjectPool(
    factory=PooledParticle,
    reset_fn=_reset_particle,
    initial_size=256,
    max_size=4096
)


# ─── Surface 缓存池 ────────────────────────────────────────

class SurfacePool:
    """Surface 复用池：减少 Surface 创建/销毁开销"""

    def __init__(self, max_size=128):
        self._surfaces = {}  # key=(w,h,flags) -> [surface, ...]
        self._max = max_size

    def get(self, width, height, flags=0):
        """获取指定尺寸的 Surface"""
        key = (width, height, flags)
        lst = self._surfaces.get(key)
        if lst:
            return lst.pop()
        try:
            return pygame.Surface((width, height), flags)
        except Exception:
            return None

    def release(self, surface):
        """归还 Surface"""
        if surface is None:
            return
        size = surface.get_size()
        key = (size[0], size[1], surface.get_flags())
        lst = self._surfaces.get(key)
        if lst is None:
            lst = self._surfaces[key] = []
        if len(lst) < self._max:
            surface.fill((0, 0, 0, 0)) if surface.get_alpha() == 0 else None
            lst.append(surface)

    def clear(self):
        self._surfaces.clear()


# 全局 Surface 池
surface_pool = SurfacePool(max_size=128)


# ─── 便捷函数 ──────────────────────────────────────────────

def get_particle(x, y, vx=0, vy=0, size=3, life=60, color=(255, 255, 255),
                 shape='circle'):
    """快速从池中获取并配置一个粒子"""
    p = particle_pool.acquire()
    if p is None:
        return None
    p.x = x
    p.y = y
    p.vx = vx
    p.vy = vy
    p.size = size
    p.life = life
    p.max_life = life
    p.color = color
    p.alpha = 255
    p.shape = shape
    p.active = True
    return p


def draw_pooled_particle(surface, p, camera_x=0, camera_y=0):
    """绘制池化粒子（带 alpha 渐隐）"""
    if p.life <= 0:
        return
    alpha = int(255 * (p.life / p.max_life)) if p.max_life > 0 else 255
    sx = int(p.x - camera_x)
    sy = int(p.y - camera_y)
    r = max(1, int(p.size * (p.life / p.max_life)))
    try:
        if p.shape == 'circle':
            pygame.draw.circle(surface, p.color, (sx, sy), r)
        elif p.shape == 'square':
            pygame.draw.rect(surface, p.color, (sx - r, sy - r, r * 2, r * 2))
        elif p.shape == 'star':
            pygame.draw.polygon(surface, p.color,
                                [(sx, sy - r), (sx + r, sy), (sx, sy + r), (sx - r, sy)])
    except Exception:
        pass


def update_pooled_particles(particles, dt=1.0):
    """批量更新池化粒子，自动回收死亡粒子"""
    dead = []
    alive = []
    for p in particles:
        if not p.active or p.life <= 0:
            dead.append(p)
            continue
        p.x += p.vx * dt
        p.y += p.vy * dt
        p.life -= 1
        if p.life <= 0:
            p.active = False
            dead.append(p)
        else:
            alive.append(p)
    # 批量回收死亡粒子到池
    particle_pool.release_many(dead)
    # 替换原列表内容
    particles.clear()
    particles.extend(alive)
