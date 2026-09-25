#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用对象池系统 - 减少 GC 压力，提升粒子/子弹/特效性能

本模块提供三类对象池：

- ``ObjectPool`` — 通用泛型池，可适配任意可复用对象（子弹、音效句柄等）。
  通过工厂函数创建新对象、reset 回调重置状态，支持预热、批量回收与上限控制。

- ``PooledParticle`` / ``particle_pool`` — 面向高频粒子特效优化的池化粒子，
  使用 ``__slots__`` 最小化内存开销，并提供全局共享池实例。

- ``SurfacePool`` / ``surface_pool`` — 按 ``(width, height, flags)`` 维度缓存
  Pygame Surface，避免特效系统频繁创建/销毁 Surface 导致的开销。

模块同时暴露 ``get_particle``、``draw_pooled_particle``、``update_pooled_particles``
等便捷函数，供特效系统直接调用。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional, Sequence, Tuple

import pygame

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 核心对象池 (ObjectPool)
# ═══════════════════════════════════════════════════════════════


class ObjectPool:
    """通用对象池，支持任意可复用对象。

    池维护两个集合：空闲对象列表 ``_pool`` 与活跃对象计数 ``_active``。
    当请求对象时优先从空闲列表取出，列表为空则通过工厂函数新建；
    归还时将对象重置后放回空闲列表（若未超上限）。

    Args:
        factory: 无参工厂函数，返回新对象实例。
        reset_fn: 将对象重置为初始状态的回调；为 None 时不重置。
        initial_size: 初始化时预创建的对象数量。
        max_size: 池允许持有的空闲对象上限。
    """

    def __init__(
        self,
        factory: Callable[[], Any],
        reset_fn: Optional[Callable[[Any], None]] = None,
        initial_size: int = 64,
        max_size: int = 2048,
    ) -> None:
        self._factory = factory
        self._reset_fn = reset_fn or (lambda o: None)
        self._max = max_size
        self._pool: List[Any] = []
        self._active: int = 0
        # 预热
        for _ in range(min(initial_size, max_size)):
            self._pool.append(factory())

    def acquire(self) -> Optional[Any]:
        """从池中获取一个对象（池空则新建）。

        Returns:
            可用的对象实例；若工厂函数异常则返回 None。
        """
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

    def release(self, obj: Any) -> None:
        """归还对象到池中。

        对象会被 ``reset_fn`` 重置后放入空闲列表。
        若池已达上限，对象将被丢弃（由 GC 回收）。

        Args:
            obj: 要归还的对象；传入 None 时静默忽略。
        """
        if obj is None:
            return
        self._active -= 1
        if len(self._pool) < self._max:
            self._reset_fn(obj)
            self._pool.append(obj)

    def release_many(self, objs: Sequence[Any]) -> None:
        """批量归还多个对象到池中。

        Args:
            objs: 可迭代的对象集合，None 元素会被跳过。
        """
        for o in objs:
            self.release(o)

    def prewarm(self, count: int) -> None:
        """预热：提前创建对象填充池，减少运行时分配。

        实际创建数量为 ``min(count, max_size - 当前池大小)``。

        Args:
            count: 期望额外预创建的对象数量。
        """
        for _ in range(min(count, self._max - len(self._pool))):
            self._pool.append(self._factory())

    @property
    def free_count(self) -> int:
        """当前空闲（可直接取出）的对象数量。"""
        return len(self._pool)

    @property
    def active_count(self) -> int:
        """已借出、尚未归还的对象数量。"""
        return self._active

    @property
    def total_count(self) -> int:
        """池中空闲对象与活跃对象的总数量。"""
        return len(self._pool) + self._active

    def clear(self) -> None:
        """清空池，释放所有空闲对象引用，并将活跃计数归零。"""
        self._pool.clear()
        self._active = 0


# ═══════════════════════════════════════════════════════════════
# 粒子对象池 (PooledParticle)
# ═══════════════════════════════════════════════════════════════


class PooledParticle:
    """池化粒子：避免每帧 new/dict 创建。

    使用 ``__slots__`` 固定属性集以降低内存占用与属性访问开销。
    粒子生命周期由 ``life / max_life`` 控制，由外部系统驱动更新与回收。
    """

    __slots__: Tuple[str, ...] = (
        "x", "y", "vx", "vy", "size", "life", "max_life",
        "color", "alpha", "shape", "active",
    )

    def __init__(self) -> None:
        """初始化粒子并将其标记为非活跃状态。"""
        self.reset()
        self.active = False

    def reset(self) -> None:
        """将粒子所有属性重置为默认值。

        此方法在对象归还池时由 ``reset_fn`` 调用。
        """
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.size = 3.0
        self.life = 60
        self.max_life = 60
        self.color = (255, 255, 255)
        self.alpha = 255
        self.shape = "circle"
        self.active = False


def _reset_particle(p: PooledParticle) -> None:
    """粒子归还池时的重置回调，将 active 标记置为 False。"""
    p.active = False


# 全局粒子池（各系统共用）
particle_pool: ObjectPool = ObjectPool(
    factory=PooledParticle,
    reset_fn=_reset_particle,
    initial_size=256,
    max_size=4096,
)


# ═══════════════════════════════════════════════════════════════
# Surface 缓存池 (SurfacePool)
# ═══════════════════════════════════════════════════════════════


class SurfacePool:
    """Surface 复用池：减少 Surface 创建/销毁开销。

    按 ``(width, height, flags)`` 维度分组缓存 Pygame Surface。
    归还时对透明 Surface 执行清屏，避免残留像素。

    Args:
        max_size: 每个维度分组允许缓存的 Surface 最大数量。
    """

    def __init__(self, max_size: int = 128) -> None:
        self._surfaces: dict[Tuple[int, int, int], List[pygame.Surface]] = {}
        self._max = max_size

    def get(self, width: int, height: int, flags: int = 0) -> Optional[pygame.Surface]:
        """获取指定尺寸和标志位的 Surface。

        优先从缓存中取出已有 Surface；若缓存为空则新建。

        Args:
            width: Surface 宽度（像素）。
            height: Surface 高度（像素）。
            flags: 传递给 ``pygame.Surface`` 的标志位。

        Returns:
            可用的 Surface 实例；创建失败时返回 None。
        """
        key = (width, height, flags)
        lst = self._surfaces.get(key)
        if lst:
            return lst.pop()
        try:
            return pygame.Surface((width, height), flags)
        except Exception:
            return None

    def release(self, surface: Optional[pygame.Surface]) -> None:
        """归还 Surface 到缓存池。

        透明 Surface 会被清屏以避免残留像素。
        若该维度分组已达上限，Surface 将被丢弃。

        Args:
            surface: 要归还的 Surface；传入 None 时静默忽略。
        """
        if surface is None:
            return
        size = surface.get_size()
        key = (size[0], size[1], surface.get_flags())
        lst = self._surfaces.get(key)
        if lst is None:
            lst = self._surfaces[key] = []
        if len(lst) < self._max:
            if surface.get_alpha() == 0:
                surface.fill((0, 0, 0, 0))
            lst.append(surface)

    def clear(self) -> None:
        """清空所有缓存的 Surface 引用。"""
        self._surfaces.clear()


# 全局 Surface 池
surface_pool: SurfacePool = SurfacePool(max_size=128)


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════


def get_particle(
    x: float,
    y: float,
    vx: float = 0,
    vy: float = 0,
    size: float = 3,
    life: int = 60,
    color: Tuple[int, int, int] = (255, 255, 255),
    shape: str = "circle",
) -> Optional[PooledParticle]:
    """快速从全局粒子池中获取并配置一个粒子。

    Args:
        x: 粒子世界坐标 X。
        y: 粒子世界坐标 Y。
        vx: X 方向速度分量。
        vy: Y 方向速度分量。
        size: 粒子绘制半径/边长。
        life: 粒子存活帧数。
        color: RGB 颜色元组。
        shape: 绘制形状，支持 ``'circle'``、``'square'``、``'star'``。

    Returns:
        配置完毕的 ``PooledParticle``；池耗尽时返回 None。
    """
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


def draw_pooled_particle(
    surface: pygame.Surface,
    p: PooledParticle,
    camera_x: float = 0,
    camera_y: float = 0,
) -> None:
    """绘制池化粒子到目标 Surface（带 alpha 渐隐与尺寸缩放）。

    粒子在生命周期结束（``life <= 0``）时不绘制。
    透明度与尺寸随剩余生命线性衰减。

    Args:
        surface: 目标绘制 Surface。
        p: 要绘制的池化粒子。
        camera_x: 摄像机世界坐标 X（用于世界坐标到屏幕坐标转换）。
        camera_y: 摄像机世界坐标 Y。
    """
    if p.life <= 0:
        return
    sx = int(p.x - camera_x)
    sy = int(p.y - camera_y)
    r = max(1, int(p.size * (p.life / p.max_life)))
    try:
        if p.shape == "circle":
            pygame.draw.circle(surface, p.color, (sx, sy), r)
        elif p.shape == "square":
            pygame.draw.rect(surface, p.color, (sx - r, sy - r, r * 2, r * 2))
        elif p.shape == "star":
            pygame.draw.polygon(
                surface,
                p.color,
                [(sx, sy - r), (sx + r, sy), (sx, sy + r), (sx - r, sy)],
            )
    except Exception:
        pass


def update_pooled_particles(
    particles: List[PooledParticle],
    dt: float = 1.0,
) -> None:
    """批量更新池化粒子，自动回收死亡粒子。

    遍历粒子列表，推进位置与生命值；生命周期结束的粒子被归还至
    全局粒子池，原列表内容就地替换为存活粒子。

    Args:
        particles: 待更新的粒子列表（会被就地清空并填入存活粒子）。
        dt: 时间步长，用于速度积分。
    """
    dead: List[PooledParticle] = []
    alive: List[PooledParticle] = []
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
