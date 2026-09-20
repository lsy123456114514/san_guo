#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一 UI 组件库 - 过渡动画、面板、按钮、进度条、Toast、文字特效"""

import math
import time
import logging
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
# 过渡动画管理器
# ═══════════════════════════════════════════════════════════

class TransitionManager:
    """屏幕过渡效果：淡入淡出、滑动"""

    FADE_IN = 'fade_in'
    FADE_OUT = 'fade_out'
    SLIDE_LEFT = 'slide_left'
    SLIDE_RIGHT = 'slide_right'

    def __init__(self):
        self._active = False
        self._type = None
        self._duration = 500
        self._start_time = 0
        self._progress = 0.0
        self._callback = None

    @property
    def is_active(self):
        return self._active

    @property
    def progress(self):
        return self._progress

    def fade_in(self, duration=500, callback=None):
        self._start(self.FADE_IN, duration, callback)

    def fade_out(self, duration=500, callback=None):
        self._start(self.FADE_OUT, duration, callback)

    def slide_left(self, duration=400, callback=None):
        self._start(self.SLIDE_LEFT, duration, callback)

    def slide_right(self, duration=400, callback=None):
        self._start(self.SLIDE_RIGHT, duration, callback)

    def _start(self, t, duration, callback):
        self._active = True
        self._type = t
        self._duration = max(1, duration)
        self._start_time = pygame.time.get_ticks()
        self._progress = 0.0
        self._callback = callback

    def update(self):
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

    def apply(self, surface):
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
    def _ease(t):
        return t * t * (3.0 - 2.0 * t)


# ═══════════════════════════════════════════════════════════
# UI 面板
# ═══════════════════════════════════════════════════════════

class UIPanel:
    """带标题的圆角面板"""

    def __init__(self, x, y, width, height, title=None, style='dark'):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.style = style

    def draw(self, surface):
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

    def contains(self, point):
        return self.rect.collidepoint(point)


# ═══════════════════════════════════════════════════════════
# 按钮
# ═══════════════════════════════════════════════════════════

class UIButton:
    """风格化按钮，支持 hover/press 动画"""

    STYLE_COLORS = {
        'primary': ((0, 180, 230), (0, 200, 255)),
        'secondary': ((200, 170, 50), (255, 215, 0)),
        'danger': ((200, 40, 40), (220, 50, 50)),
        'success': ((40, 170, 60), (50, 200, 80)),
    }

    def __init__(self, x, y, width, height, text, style='primary'):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.style = style
        self._hover = False
        self._pressed = False
        self._scale = 1.0

    def handle_event(self, event):
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

    def update(self):
        target = 0.95 if self._pressed else (1.05 if self._hover else 1.0)
        self._scale += (target - self._scale) * 0.2

    def draw(self, surface):
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
# 进度条
# ═══════════════════════════════════════════════════════════

class ProgressBar:
    """带动画的进度条"""

    def __init__(self, x, y, width, height, max_value=100, color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_value = max(1, max_value)
        self.target_value = 0
        self.display_value = 0
        self.color = color or COLORS['accent_cyan']
        self.show_text = True

    def set_value(self, val):
        self.target_value = max(0, min(self.max_value, val))

    def update(self):
        diff = self.target_value - self.display_value
        if abs(diff) < 0.5:
            self.display_value = self.target_value
        else:
            self.display_value += diff * 0.15

    def draw(self, surface):
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
# Toast 通知
# ═══════════════════════════════════════════════════════════

class ToastNotification:
    """顶部弹出通知"""

    STYLE_COLORS = {
        'info': COLORS['accent_cyan'],
        'success': COLORS['green'],
        'warning': COLORS['orange'],
        'error': COLORS['red'],
    }

    def __init__(self, text, duration=2000, style='info', screen_width=800):
        self.text = text
        self.duration = max(1, duration)
        self.color = self.STYLE_COLORS.get(style, COLORS['accent_cyan'])
        self.screen_width = screen_width
        self._start = pygame.time.get_ticks()
        self._alive = True
        self.font = get_font(18)

    @property
    def is_alive(self):
        return self._alive

    def update(self):
        if pygame.time.get_ticks() - self._start > self.duration:
            self._alive = False
        return self._alive

    def draw(self, surface):
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
# 打字机文字特效
# ═══════════════════════════════════════════════════════════

class TextReveal:
    """逐字显示文字效果"""

    def __init__(self, text, speed=30):
        self.text = text
        self.speed = speed  # 字/秒
        self._start = pygame.time.get_ticks()
        self._revealed = 0
        self._done = False

    @property
    def is_complete(self):
        return self._done

    def update(self):
        if self._done:
            return
        elapsed = (pygame.time.get_ticks() - self._start) / 1000.0
        self._revealed = min(len(self.text), int(elapsed * self.speed))
        if self._revealed >= len(self.text):
            self._done = True

    def skip(self):
        self._revealed = len(self.text)
        self._done = True

    def draw(self, surface, x, y, font=None, color=None):
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
