#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染优化器 - 脏矩形、帧缓存、批处理绘制"""

import logging
import time
import pygame

logger = logging.getLogger(__name__)


class DirtyRectManager:
    """脏矩形管理器：只重绘变化区域"""

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self._dirty_rects = []
        self._full_redraw = True

    def mark_dirty(self, rect):
        if rect is None:
            return
        self._dirty_rects.append(rect)
        if len(self._dirty_rects) > 8:
            self._full_redraw = True

    def mark_full(self):
        self._full_redraw = True

    def get_dirty_rects(self):
        if self._full_redraw:
            self._dirty_rects.clear()
            self._full_redraw = False
            return [pygame.Rect(0, 0, self.width, self.height)]
        rects = self._dirty_rects[:]
        self._dirty_rects.clear()
        return rects

    @property
    def needs_full_redraw(self):
        return self._full_redraw


class FrameCache:
    """帧缓存：静态背景双缓冲，避免每帧重绘"""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._cache = None
        self._dirty = True

    def invalidate(self):
        self._dirty = True

    def get_surface(self):
        if self._dirty or self._cache is None:
            self._cache = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._dirty = True
        return self._cache, self._dirty

    def commit(self):
        self._dirty = False

    def blit_to(self, target, pos=(0, 0)):
        if self._cache and not self._dirty:
            target.blit(self._cache, pos)


class RenderBatch:
    """渲染批处理：收集同类绘制操作后一次性提交"""

    def __init__(self):
        self._circles = []
        self._rects = []
        self._lines = []

    def add_circle(self, surface, color, pos, radius, width=0):
        self._circles.append((surface, color, pos, radius, width))

    def add_rect(self, surface, color, rect, width=0):
        self._rects.append((surface, color, rect, width))

    def add_line(self, surface, color, start, end, width=1):
        self._lines.append((surface, color, start, end, width))

    def flush(self):
        for surf, color, pos, radius, width in self._circles:
            try:
                pygame.draw.circle(surf, color, pos, radius, width)
            except Exception:
                pass
        self._circles.clear()

        for surf, color, rect, width in self._rects:
            try:
                pygame.draw.rect(surf, color, rect, width)
            except Exception:
                pass
        self._rects.clear()

        for surf, color, start, end, width in self._lines:
            try:
                pygame.draw.line(surf, color, start, end, width)
            except Exception:
                pass
        self._lines.clear()

    def clear(self):
        self._circles.clear()
        self._rects.clear()
        self._lines.clear()

    @property
    def count(self):
        return len(self._circles) + len(self._rects) + len(self._lines)


class FPSCounter:
    """FPS 统计"""

    def __init__(self):
        self._frames = 0
        self._fps = 0.0
        self._last_time = time.time()
        self._min_fps = 999.0
        self._max_fps = 0.0

    def tick(self):
        self._frames += 1
        now = time.time()
        elapsed = now - self._last_time
        if elapsed >= 1.0:
            self._fps = self._frames / elapsed
            self._min_fps = min(self._min_fps, self._fps)
            self._max_fps = max(self._max_fps, self._fps)
            self._frames = 0
            self._last_time = now

    @property
    def fps(self):
        return round(self._fps, 1)

    @property
    def min_fps(self):
        return round(self._min_fps, 1) if self._min_fps < 999 else 0

    @property
    def max_fps(self):
        return round(self._max_fps, 1)

    def draw(self, surface, x=5, y=5, font=None):
        color = (0, 255, 0) if self.fps >= 50 else (255, 255, 0) if self.fps >= 30 else (255, 0, 0)
        text = f"FPS: {self.fps}"
        if font:
            surf = font.render(text, True, color)
            surface.blit(surf, (x, y))
        else:
            try:
                small_font = pygame.font.SysFont(None, 20)
                surf = small_font.render(text, True, color)
                surface.blit(surf, (x, y))
            except Exception:
                pass

    def reset_stats(self):
        self._min_fps = 999.0
        self._max_fps = 0.0
