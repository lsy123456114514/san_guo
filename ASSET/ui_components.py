#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified UI Component Library for the San Guo game engine.

Provides reusable UI elements with smooth transitions, styled panels,
animated buttons, progress bars, toast notifications, and text reveal
effects:

* **TransitionManager** – screen fade and slide transitions.
* **UIPanel** – rounded-corner panel with optional title.
* **UIButton** – styled button with hover/press animations.
* **ProgressBar** – animated progress bar with percentage display.
* **ToastNotification** – temporary top-of-screen notification.
* **TextReveal** – typewriter-style text reveal effect.
"""

import math
import time
import logging
from typing import Optional, Tuple
import pygame

logger = logging.getLogger(__name__)

try:
    from ASSET.game_data import get_font, draw_gradient_bg
except ImportError:
    get_font = lambda s: pygame.font.SysFont("Microsoft YaHei", s)
    draw_gradient_bg = None

COLORS = {
    'bg_dark': (15, 15, 30),
    'bg_panel': (25, 25, 50, 220),
    'accent_gold': (255, 215, 0),
    'accent_cyan': (0, 200, 255),
    'text_white': (255, 255, 255),
    'text_gray': (160, 160, 160),
    'red': (220, 50, 50),
    'green': (50, 200, 80),
    'blue': (50, 120, 220),
    'orange': (255, 165, 0),
    'purple': (180, 80, 255),
}


# ═══════════════════════════════════════════════════════════
# Transition Manager
# ═══════════════════════════════════════════════════════════

class TransitionManager:
    """Screen transition effects: fade-in, fade-out, slide-left, slide-right.

    Manages the lifecycle of a single active transition. Call :meth:`update`
    each frame to advance the animation, then :meth:`apply` to composite
    the effect onto the target surface.

    Attributes:
        FADE_IN: Fade-in transition type.
        FADE_OUT: Fade-out transition type.
        SLIDE_LEFT: Slide-left transition type.
        SLIDE_RIGHT: Slide-right transition type.
    """

    FADE_IN = 'fade_in'
    FADE_OUT = 'fade_out'
    SLIDE_LEFT = 'slide_left'
    SLIDE_RIGHT = 'slide_right'

    def __init__(self) -> None:
        self._active: bool = False
        self._type: Optional[str] = None
        self._duration: int = 500
        self._start_time: int = 0
        self._progress: float = 0.0
        self._callback: Optional[callable] = None

    @property
    def is_active(self) -> bool:
        """Whether a transition is currently in progress."""
        return self._active

    @property
    def progress(self) -> float:
        """Current transition progress from 0.0 to 1.0."""
        return self._progress

    def fade_in(self, duration: int = 500, callback: Optional[callable] = None) -> None:
        """Start a fade-in transition.

        Args:
            duration: Transition duration in milliseconds.
            callback: Optional function called when the transition completes.
        """
        self._start(self.FADE_IN, duration, callback)

    def fade_out(self, duration: int = 500, callback: Optional[callable] = None) -> None:
        """Start a fade-out transition.

        Args:
            duration: Transition duration in milliseconds.
            callback: Optional function called when the transition completes.
        """
        self._start(self.FADE_OUT, duration, callback)

    def slide_left(self, duration: int = 400, callback: Optional[callable] = None) -> None:
        """Start a slide-left transition.

        Args:
            duration: Transition duration in milliseconds.
            callback: Optional function called when the transition completes.
        """
        self._start(self.SLIDE_LEFT, duration, callback)

    def slide_right(self, duration: int = 400, callback: Optional[callable] = None) -> None:
        """Start a slide-right transition.

        Args:
            duration: Transition duration in milliseconds.
            callback: Optional function called when the transition completes.
        """
        self._start(self.SLIDE_RIGHT, duration, callback)

    def _start(self, t: str, duration: int, callback: Optional[callable]) -> None:
        """Initialize and begin a new transition.

        Args:
            t: Transition type constant.
            duration: Duration in milliseconds.
            callback: Optional completion callback.
        """
        self._active = True
        self._type = t
        self._duration = max(1, duration)
        self._start_time = pygame.time.get_ticks()
        self._progress = 0.0
        self._callback = callback

    def update(self) -> bool:
        """Advance the transition by one frame.

        Returns:
            ``True`` when the transition has finished.
        """
        if not self._active:
            return True
        elapsed = pygame.time.get_ticks() - self._start_time
        self._progress = min(1.0, elapsed / self._duration)
        if self._progress >= 1.0:
            self._active = False
            if self._callback:
                self._callback()
            return True
        return False

    def apply(self, surface: pygame.Surface) -> None:
        """Composite the current transition effect onto *surface*.

        Args:
            surface: The target surface to apply the effect to.
        """
        if not self._active:
            return
        w, h = surface.get_size()
        t = self._progress

        if self._type == self.FADE_IN:
            alpha = int(255 * (1.0 - self._ease(t)))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            surface.blit(overlay, (0, 0))

        elif self._type == self.FADE_OUT:
            alpha = int(255 * self._ease(t))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            surface.blit(overlay, (0, 0))

        elif self._type == self.SLIDE_LEFT:
            offset = int(w * (1.0 - self._ease(t)))
            overlay = pygame.Surface((w, h))
            overlay.blit(surface, (0, 0))
            surface.fill((0, 0, 0))
            surface.blit(overlay, (-offset, 0))

        elif self._type == self.SLIDE_RIGHT:
            offset = int(w * (1.0 - self._ease(t)))
            overlay = pygame.Surface((w, h))
            overlay.blit(surface, (0, 0))
            surface.fill((0, 0, 0))
            surface.blit(overlay, (offset, 0))

    @staticmethod
    def _ease(t: float) -> float:
        """Apply smooth-step easing to a progress value.

        Args:
            t: Progress value in [0.0, 1.0].

        Returns:
            Eased value in [0.0, 1.0].
        """
        return t * t * (3.0 - 2.0 * t)


# ═══════════════════════════════════════════════════════════
# UI Panel
# ═══════════════════════════════════════════════════════════

class UIPanel:
    """Rounded-corner panel with an optional title header.

    Args:
        x: Horizontal pixel position.
        y: Vertical pixel position.
        width: Panel width in pixels.
        height: Panel height in pixels.
        title: Optional title text displayed at the top.
        style: Visual style key (currently only ``'dark'`` is used).
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 title: Optional[str] = None, style: str = 'dark') -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.title: Optional[str] = title
        self.style: str = style

    def draw(self, surface: pygame.Surface) -> None:
        """Render the panel onto *surface*.

        Args:
            surface: Destination surface.
        """
        x, y, w, h = self.rect.x, self.rect.y, self.rect.w, self.rect.h
        bg = COLORS.get('bg_panel', (25, 25, 50, 220))
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill(bg)
        pygame.draw.rect(panel, (80, 80, 120), (0, 0, w, h), 2, border_radius=12)
        surface.blit(panel, (x, y))

        if self.title:
            try:
                font = get_font(22)
                txt = font.render(self.title, True, COLORS['accent_gold'])
                surface.blit(txt, (x + 15, y + 10))
                pygame.draw.line(surface, (80, 80, 120), (x + 10, y + 38), (x + w - 10, y + 38), 1)
            except Exception:
                pass

    def contains(self, point: Tuple[int, int]) -> bool:
        """Check whether a point lies inside the panel.

        Args:
            point: ``(x, y)`` screen coordinate.

        Returns:
            ``True`` if the point is within the panel bounds.
        """
        return self.rect.collidepoint(point)


# ═══════════════════════════════════════════════════════════
# UI Button
# ═══════════════════════════════════════════════════════════

class UIButton:
    """Styled button with hover/press scale animations.

    Supports four visual styles: ``'primary'``, ``'secondary'``,
    ``'danger'``, and ``'success'``.

    Args:
        x: Horizontal pixel position.
        y: Vertical pixel position.
        width: Button width in pixels.
        height: Button height in pixels.
        text: Button label.
        style: Visual style key.
    """

    STYLE_COLORS = {
        'primary': ((0, 180, 230), (0, 200, 255)),
        'secondary': ((200, 170, 50), (255, 215, 0)),
        'danger': ((200, 40, 40), (220, 50, 50)),
        'success': ((40, 170, 60), (50, 200, 80)),
    }

    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, style: str = 'primary') -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.style: str = style
        self._hover: bool = False
        self._pressed: bool = False
        self._scale: float = 1.0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process a pygame event for hover/click detection.

        Args:
            event: A pygame event object.

        Returns:
            ``True`` when the button has been clicked (mouse-up inside).
        """
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
            self._pressed = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.rect.collidepoint(event.pos):
                self._pressed = False
                return True
            self._pressed = False
        return False

    def update(self) -> None:
        """Animate the button scale based on hover/press state."""
        target = 0.95 if self._pressed else (1.05 if self._hover else 1.0)
        self._scale += (target - self._scale) * 0.2

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button onto *surface*.

        Args:
            surface: Destination surface.
        """
        self.update()
        colors = self.STYLE_COLORS.get(self.style, self.STYLE_COLORS['primary'])
        base_color = colors[1] if self._hover else colors[0]

        w = int(self.rect.w * self._scale)
        h = int(self.rect.h * self._scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2

        btn_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, (*base_color, 230), (0, 0, w, h), border_radius=8)
        if self._hover:
            pygame.draw.rect(btn_surf, (255, 255, 255, 60), (2, 2, w - 4, h // 2), border_radius=6)
        pygame.draw.rect(btn_surf, (255, 255, 255, 100), (0, 0, w, h), 2, border_radius=8)

        try:
            font = get_font(max(14, h // 3))
            txt = font.render(self.text, True, COLORS['text_white'])
            btn_surf.blit(txt, txt.get_rect(center=(w // 2, h // 2)))
        except Exception:
            pass

        surface.blit(btn_surf, (x, y))


# ═══════════════════════════════════════════════════════════
# Progress Bar
# ═══════════════════════════════════════════════════════════

class ProgressBar:
    """Animated progress bar with percentage text display.

    Args:
        x: Horizontal pixel position.
        y: Vertical pixel position.
        width: Bar width in pixels.
        height: Bar height in pixels.
        max_value: Maximum value representing 100%.
        color: Fill colour as an RGB tuple.
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 max_value: int = 100, color: Optional[Tuple[int, int, int]] = None) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.max_value: int = max(1, max_value)
        self.target_value: float = 0
        self.display_value: float = 0
        self.color: Tuple[int, int, int] = color or COLORS['accent_cyan']
        self.show_text: bool = True

    def set_value(self, val: float) -> None:
        """Set the target progress value (clamped to [0, max_value]).

        Args:
            val: Desired progress value.
        """
        self.target_value = max(0, min(self.max_value, val))

    def update(self) -> None:
        """Smoothly animate the display value toward the target."""
        diff = self.target_value - self.display_value
        if abs(diff) < 0.5:
            self.display_value = self.target_value
        else:
            self.display_value += diff * 0.15

    def draw(self, surface: pygame.Surface) -> None:
        """Render the progress bar onto *surface*.

        Args:
            surface: Destination surface.
        """
        self.update()
        x, y, w, h = self.rect
        # 背景
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (40, 40, 60, 180), (0, 0, w, h), border_radius=h // 2)
        surface.blit(bg, (x, y))

        # 填充
        fill_w = int(w * (self.display_value / self.max_value))
        if fill_w > 0:
            fg = pygame.Surface((fill_w, h), pygame.SRCALPHA)
            pygame.draw.rect(fg, (*self.color, 230), (0, 0, fill_w, h), border_radius=h // 2)
            # 高光
            pygame.draw.rect(fg, (255, 255, 255, 50), (2, 2, max(0, fill_w - 4), h // 3), border_radius=h // 2)
            surface.blit(fg, (x, y))

        if self.show_text:
            try:
                font = get_font(max(12, h - 4))
                pct = int(self.display_value / self.max_value * 100)
                txt = font.render(f"{pct}%", True, COLORS['text_white'])
                surface.blit(txt, txt.get_rect(center=self.rect.center))
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════
# Toast Notification
# ═══════════════════════════════════════════════════════════

class ToastNotification:
    """Temporary notification that slides in at the top of the screen.

    Supports four styles: ``'info'``, ``'success'``, ``'warning'``, and
    ``'error'``.  The notification automatically fades in, stays visible
    for *duration* milliseconds, then fades out.

    Args:
        text: Message text.
        duration: Display duration in milliseconds.
        style: Visual style key.
        screen_width: Width of the screen for horizontal centering.
    """

    STYLE_COLORS = {
        'info': COLORS['accent_cyan'],
        'success': COLORS['green'],
        'warning': COLORS['orange'],
        'error': COLORS['red'],
    }

    def __init__(self, text: str, duration: int = 2000, style: str = 'info',
                 screen_width: int = 800) -> None:
        self.text: str = text
        self.duration: int = max(1, duration)
        self.color: Tuple[int, int, int] = self.STYLE_COLORS.get(style, COLORS['accent_cyan'])
        self.screen_width: int = screen_width
        self._start: int = pygame.time.get_ticks()
        self._alive: bool = True
        self.font: pygame.font.Font = get_font(18)

    @property
    def is_alive(self) -> bool:
        """Whether the notification is still visible."""
        return self._alive

    def update(self) -> bool:
        """Advance the notification timer.

        Returns:
            ``True`` if the notification is still alive.
        """
        if pygame.time.get_ticks() - self._start > self.duration:
            self._alive = False
        return self._alive

    def draw(self, surface: pygame.Surface) -> None:
        """Render the notification onto *surface*.

        Args:
            surface: Destination surface.
        """
        if not self._alive:
            return
        elapsed = pygame.time.get_ticks() - self._start
        # 淡入(前200ms) -> 保持 -> 淡出(后300ms)
        if elapsed < 200:
            alpha = int(255 * elapsed / 200)
        elif elapsed > self.duration - 300:
            alpha = int(255 * (self.duration - elapsed) / 300)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        try:
            txt_surf = self.font.render(self.text, True, COLORS['text_white'])
        except Exception:
            return
        tw, th = txt_surf.get_size()
        pw = tw + 30
        ph = th + 16
        px = (self.screen_width - pw) // 2
        py = 10

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((*self.color, min(alpha, 200)))
        pygame.draw.rect(panel, (*self.color, alpha), (0, 0, pw, ph), 2, border_radius=8)
        panel.blit(txt_surf, (15, 8))
        surface.blit(panel, (px, py))


# ═══════════════════════════════════════════════════════════
# Text Reveal Effect
# ═══════════════════════════════════════════════════════════

class TextReveal:
    """Typewriter-style text reveal effect.

    Characters appear one at a time at a configurable speed.  Call
    :meth:`skip` to instantly reveal all text.

    Args:
        text: Full text to display.
        speed: Characters revealed per second.
    """

    def __init__(self, text: str, speed: int = 30) -> None:
        self.text: str = text
        self.speed: int = speed  # 字/秒
        self._start: int = pygame.time.get_ticks()
        self._revealed: int = 0
        self._done: bool = False

    @property
    def is_complete(self) -> bool:
        """Whether all text has been revealed."""
        return self._done

    def update(self) -> None:
        """Advance the reveal animation by one frame."""
        if self._done:
            return
        elapsed = (pygame.time.get_ticks() - self._start) / 1000.0
        self._revealed = min(len(self.text), int(elapsed * self.speed))
        if self._revealed >= len(self.text):
            self._done = True

    def skip(self) -> None:
        """Immediately reveal all text without animation."""
        self._revealed = len(self.text)
        self._done = True

    def draw(self, surface: pygame.Surface, x: int, y: int,
             font: Optional[pygame.font.Font] = None,
             color: Optional[Tuple[int, int, int]] = None) -> None:
        """Render the revealed portion of the text onto *surface*.

        Supports newline characters for multi-line display.

        Args:
            surface: Destination surface.
            x: Horizontal pixel position.
            y: Vertical pixel position.
            font: Optional pygame font.  Defaults to size 20.
            color: Text colour.  Defaults to white.
        """
        self.update()
        if font is None:
            font = get_font(20)
        if color is None:
            color = COLORS['text_white']
        shown = self.text[:self._revealed]
        if not shown:
            return
        # 支持换行
        lines = shown.split('\n')
        for i, line in enumerate(lines):
            try:
                txt = font.render(line, True, color)
                surface.blit(txt, (x, y + i * (font.get_height() + 4)))
            except Exception:
                pass
