#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendering Optimization System for the San Guo game engine.

Provides low-level rendering utilities to minimize redundant draw calls and
improve frame throughput:

* **DirtyRectManager** – tracks which screen regions have changed so only
  those areas are redrawn each frame.
* **FrameCache** – a double-buffered surface for static backgrounds that
  rarely change, avoiding a full re-render every tick.
* **RenderBatch** – collects similar draw primitives (circles, rects, lines)
  and submits them in a single pass to reduce state switches.
* **FPSCounter** – lightweight frame-rate tracker with min/max statistics
  and on-screen display.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Tuple

import pygame

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Dirty Rectangle Manager
# ═══════════════════════════════════════════════════════════════════════════════


class DirtyRectManager:
    """Manages dirty rectangles so that only changed screen regions are redrawn.

    When the number of accumulated dirty rectangles exceeds a threshold (8),
    the manager automatically switches to a full-screen redraw to avoid
    excessive fragmented blitting.

    Args:
        screen_width: Width of the screen in pixels.
        screen_height: Height of the screen in pixels.
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.width: int = screen_width
        self.height: int = screen_height
        self._dirty_rects: List[pygame.Rect] = []
        self._full_redraw: bool = True

    def mark_dirty(self, rect: pygame.Rect) -> None:
        """Mark a rectangular region as needing redraw.

        Args:
            rect: The screen rectangle that has changed.  ``None`` is silently
                  ignored.
        """
        if rect is None:
            return
        self._dirty_rects.append(rect)
        if len(self._dirty_rects) > 8:
            self._full_redraw = True

    def mark_full(self) -> None:
        """Force a full-screen redraw on the next ``get_dirty_rects`` call."""
        self._full_redraw = True

    def get_dirty_rects(self) -> List[pygame.Rect]:
        """Return and clear the current set of dirty rectangles.

        Returns:
            A list containing either a single full-screen rect (when a full
            redraw was requested) or the individual dirty rects accumulated
            since the last call.
        """
        if self._full_redraw:
            self._dirty_rects.clear()
            self._full_redraw = False
            return [pygame.Rect(0, 0, self.width, self.height)]
        rects = self._dirty_rects[:]
        self._dirty_rects.clear()
        return rects

    @property
    def needs_full_redraw(self) -> bool:
        """``True`` when the next call to ``get_dirty_rects`` will return a
        full-screen rect."""
        return self._full_redraw


# ═══════════════════════════════════════════════════════════════════════════════
# Frame Cache (Double Buffer)
# ═══════════════════════════════════════════════════════════════════════════════


class FrameCache:
    """Double-buffered surface cache for static or rarely-changing backgrounds.

    By rendering expensive backgrounds into an off-screen surface once and
    blitting it afterwards, per-frame cost is dramatically reduced.

    Args:
        width: Surface width in pixels.
        height: Surface height in pixels.
    """

    def __init__(self, width: int, height: int) -> None:
        self.width: int = width
        self.height: int = height
        self._cache: Optional[pygame.Surface] = None
        self._dirty: bool = True

    def invalidate(self) -> None:
        """Mark the cache as stale so a new surface is created on the next
        ``get_surface`` call."""
        self._dirty = True

    def get_surface(self) -> Tuple[pygame.Surface, bool]:
        """Return the cached surface and whether it needs re-rendering.

        Returns:
            A ``(surface, is_dirty)`` tuple.  When ``is_dirty`` is ``True``
            the caller should redraw its content onto the returned surface
            before calling :meth:`commit`.
        """
        if self._dirty or self._cache is None:
            self._cache = pygame.Surface(
                (self.width, self.height), pygame.SRCALPHA
            )
            self._dirty = True
        return self._cache, self._dirty

    def commit(self) -> None:
        """Mark the current frame as complete so subsequent blits use the
        cached version."""
        self._dirty = False

    def blit_to(
        self,
        target: pygame.Surface,
        pos: Tuple[int, int] = (0, 0),
    ) -> None:
        """Blit the cached surface onto *target* only if the cache is clean.

        Args:
            target: Destination surface.
            pos: Top-left position on the destination surface.
        """
        if self._cache and not self._dirty:
            target.blit(self._cache, pos)


# ═══════════════════════════════════════════════════════════════════════════════
# Render Batch
# ═══════════════════════════════════════════════════════════════════════════════


class RenderBatch:
    """Batches similar drawing primitives and submits them in one pass.

    Grouping draw calls by type (circles, rects, lines) minimises pygame
    state changes and improves throughput when many shapes must be drawn per
    frame.
    """

    def __init__(self) -> None:
        self._circles: List[Tuple] = []
        self._rects: List[Tuple] = []
        self._lines: List[Tuple] = []

    def add_circle(
        self,
        surface: pygame.Surface,
        color: Tuple[int, ...],
        pos: Tuple[int, int],
        radius: int,
        width: int = 0,
    ) -> None:
        """Queue a circle for later drawing.

        Args:
            surface: Target surface.
            color: RGB or RGBA colour tuple.
            pos: Centre of the circle.
            radius: Circle radius in pixels.
            width: Border width (``0`` for filled).
        """
        self._circles.append((surface, color, pos, radius, width))

    def add_rect(
        self,
        surface: pygame.Surface,
        color: Tuple[int, ...],
        rect: pygame.Rect,
        width: int = 0,
    ) -> None:
        """Queue a rectangle for later drawing.

        Args:
            surface: Target surface.
            color: RGB or RGBA colour tuple.
            rect: Rectangle area.
            width: Border width (``0`` for filled).
        """
        self._rects.append((surface, color, rect, width))

    def add_line(
        self,
        surface: pygame.Surface,
        color: Tuple[int, ...],
        start: Tuple[int, int],
        end: Tuple[int, int],
        width: int = 1,
    ) -> None:
        """Queue a line for later drawing.

        Args:
            surface: Target surface.
            color: RGB or RGBA colour tuple.
            start: Starting point.
            end: Ending point.
            width: Line thickness in pixels.
        """
        self._lines.append((surface, color, start, end, width))

    def flush(self) -> None:
        """Submit all queued draw operations and clear the batch.

        Individual draw errors are caught and silently ignored to prevent a
        single bad primitive from crashing the render loop.
        """
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

    def clear(self) -> None:
        """Discard all queued operations without drawing them."""
        self._circles.clear()
        self._rects.clear()
        self._lines.clear()

    @property
    def count(self) -> int:
        """Total number of queued draw operations across all primitive types."""
        return len(self._circles) + len(self._rects) + len(self._lines)


# ═══════════════════════════════════════════════════════════════════════════════
# FPS Counter
# ═══════════════════════════════════════════════════════════════════════════════


class FPSCounter:
    """Tracks frames-per-second with min/max statistics.

    Call :meth:`tick` once per frame.  Every second the counter recomputes
    the current FPS and resets its accumulator.  Use :meth:`draw` to render
    the value on-screen with a colour-coded indicator.
    """

    def __init__(self) -> None:
        self._frames: int = 0
        self._fps: float = 0.0
        self._last_time: float = time.time()
        self._min_fps: float = 999.0
        self._max_fps: float = 0.0

    def tick(self) -> None:
        """Record one frame.  Should be called once per game loop iteration."""
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
    def fps(self) -> float:
        """Current frames per second, rounded to one decimal place."""
        return round(self._fps, 1)

    @property
    def min_fps(self) -> float:
        """Lowest FPS recorded since the last :meth:`reset_stats` call."""
        return round(self._min_fps, 1) if self._min_fps < 999 else 0

    @property
    def max_fps(self) -> float:
        """Highest FPS recorded since the last :meth:`reset_stats` call."""
        return round(self._max_fps, 1)

    def draw(
        self,
        surface: pygame.Surface,
        x: int = 5,
        y: int = 5,
        font: Optional[pygame.font.Font] = None,
    ) -> None:
        """Render the FPS label onto *surface*.

        Colour coding: green ≥ 50 FPS, yellow ≥ 30 FPS, red < 30 FPS.

        Args:
            surface: Destination surface.
            x: Horizontal pixel position.
            y: Vertical pixel position.
            font: Optional pygame font.  Falls back to the default system font
                  when ``None``.
        """
        color = (
            (0, 255, 0) if self.fps >= 50
            else (255, 255, 0) if self.fps >= 30
            else (255, 0, 0)
        )
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

    def reset_stats(self) -> None:
        """Reset the recorded min/max FPS values."""
        self._min_fps = 999.0
        self._max_fps = 0.0
