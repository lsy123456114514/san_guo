# -*- coding: utf-8 -*-
"""异想天开 · 新旧 UI 切换 DEMO

同一套界面控件，在两套风格之间平滑切换（动画插值，不是硬切）：

  旧版「经典」  直角边框 + 深蓝灰配色 + 实心按钮（取自 game_main_menu COLORS）
  新版「现代」  大圆角玻璃面板 + 青/金点缀 + 悬停发光（取自 modern_ui_system COLORS）

操作：
  空格 / Tab / 点击切换键 = 在两套风格间平滑切换
  鼠标移动 = 看按钮悬停反馈（两套风格的反馈都不同）
  ESC = 退出

全部程序实时生成，无图片素材。开发者署名: by lsy123456114514
"""

import math
import os
import random
import sys

import pygame

W, H = 1280, 720

# 两套风格的调色板（与仓库内两套 UI 保持一致）
STYLE_OLD = {
    "name": "旧版 · 经典",
    "bg_top": (18, 20, 40),
    "bg_bottom": (8, 10, 22),
    "panel": (30, 30, 55),
    "panel_border": (78, 108, 168),
    "panel_alpha": 210,
    "radius": 4,          # 近乎直角
    "title": (200, 214, 240),
    "accent": (70, 130, 180),
    "accent_light": (100, 149, 237),
    "btn_text": (235, 240, 250),
    "bar_bg": (40, 44, 70),
    "top_line": (100, 130, 180),
    "text_dim": (150, 158, 185),
}

STYLE_NEW = {
    "name": "新版 · 现代",
    "bg_top": (15, 24, 38),
    "bg_bottom": (8, 12, 20),
    "panel": (22, 32, 48),
    "panel_border": (0, 212, 255),
    "panel_alpha": 140,
    "radius": 20,         # 大圆角
    "title": (255, 215, 0),
    "accent": (0, 212, 255),
    "accent_light": (120, 235, 255),
    "btn_text": (255, 255, 255),
    "bar_bg": (30, 42, 60),
    "top_line": (255, 215, 0),
    "text_dim": (140, 165, 190),
}

BTN_DEFS = [
    ("⚔️ 出 征", (0, 200, 140)),
    ("🏪 商 店", (255, 170, 0)),
    ("🎒 背 包", (150, 110, 255)),
    ("⚙️ 设 置", (120, 130, 150)),
]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_col(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def clamp01(x):
    return max(0.0, min(1.0, x))


_FONT_CACHE = {}


def font(sz):
    """按字号缓存字体（SysFont 每次调用都会解析字体名，很贵）"""
    f = _FONT_CACHE.get(sz)
    if f is None:
        f = pygame.font.SysFont("microsoftyahei,simhei", sz)
        _FONT_CACHE[sz] = f
    return f


class UISwitchDemo:
    """同一套控件、双风格插值渲染。style_t: 0=旧版 1=新版，中间为渐变过程。"""

    def __init__(self):
        if not pygame.get_init():
            pygame.init()
        pygame.display.set_caption("异想天开 · 新旧 UI 切换 DEMO - by lsy123456114514")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.style_t = 0.0          # 当前风格插值位置
        self.target = 0.0           # 目标风格
        self.global_t = 0.0
        # 每个按钮的悬停进度（0..1，帧率无关的指数逼近，两套风格共用）
        self.hover_p = [0.0] * len(BTN_DEFS)
        self.click_p = [0.0] * len(BTN_DEFS)
        self.bar = 0.62             # 示例进度条
        self.bar_dir = 1
        self.switch_count = 0
        self._bg_cache = None       # (量化色键, 背景渐变面)
        # 粒子：切换瞬间从面板中心迸发的碎光
        self.sparkles = []
        random.seed()
        self.btn_rects = []
        self._layout()

    # ── 布局 ────────────────────────────────────────────
    def _layout(self):
        pw, ph = 560, 470
        self.panel = pygame.Rect((W - pw) // 2, (H - ph) // 2 + 8, pw, ph)
        self.btn_rects = []
        bw, bh, gap = 236, 58, 24
        for i in range(len(BTN_DEFS)):
            row, col = divmod(i, 2)
            x = self.panel.x + (pw - bw * 2 - gap) // 2 + col * (bw + gap)
            y = self.panel.y + 150 + row * (bh + gap)
            self.btn_rects.append(pygame.Rect(x, y, bw, bh))
        self.bar_rect = pygame.Rect(self.panel.x + 70, self.panel.y + 390, pw - 140, 18)
        self.toggle_rect = pygame.Rect(self.panel.x + pw - 168, self.panel.y + 20, 140, 34)

    # ── 输入 ────────────────────────────────────────────
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                elif e.key in (pygame.K_SPACE, pygame.K_TAB):
                    self._flip()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.toggle_rect.collidepoint(e.pos):
                    self._flip()
                for i, r in enumerate(self.btn_rects):
                    if r.collidepoint(e.pos):
                        self.click_p[i] = 1.0

    def _flip(self):
        self.target = 1.0 - self.target
        self.switch_count += 1
        cx, cy = self.panel.center
        for _ in range(46):   # 风格切换的碎光粒子
            a = random.uniform(0, math.tau)
            sp = random.uniform(60, 380)
            self.sparkles.append([
                cx + random.uniform(-160, 160),
                cy + random.uniform(-120, 120),
                math.cos(a) * sp, math.sin(a) * sp,
                random.uniform(0.4, 0.9),
                random.uniform(1.5, 4.0),
            ])

    # ── 更新 ────────────────────────────────────────────
    def update(self, dt):
        self.global_t += dt
        # 风格插值（指数逼近 → 帧率无关的平滑过渡）
        k = 1.0 - math.exp(-dt * 5.0)
        self.style_t += (self.target - self.style_t) * k
        if abs(self.style_t - self.target) < 0.002:
            self.style_t = self.target
        # 悬停进度
        mx, my = pygame.mouse.get_pos()
        for i, r in enumerate(self.btn_rects):
            goal = 1.0 if r.collidepoint((mx, my)) else 0.0
            self.hover_p[i] += (goal - self.hover_p[i]) * (1.0 - math.exp(-dt * 12.0))
            self.click_p[i] = max(0.0, self.click_p[i] - dt * 4.0)
        # 示例进度条往复
        self.bar += self.bar_dir * dt * 0.12
        if self.bar >= 1.0:
            self.bar, self.bar_dir = 1.0, -1
        elif self.bar <= 0.0:
            self.bar, self.bar_dir = 0.0, 1
        # 粒子
        alive = []
        for p in self.sparkles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.96
            p[3] *= 0.96
            p[4] -= dt
            if p[4] > 0:
                alive.append(p)
        self.sparkles = alive

    # ── 混合风格 ────────────────────────────────────────
    def _mix(self, key):
        return lerp_col(STYLE_OLD[key], STYLE_NEW[key], self.style_t)

    def _mix_f(self, key):
        return lerp(STYLE_OLD[key], STYLE_NEW[key], self.style_t)

    # ── 绘制 ────────────────────────────────────────────
    def draw(self):
        t = self.style_t
        # 背景垂直渐变（按量化颜色缓存，避免每帧 2x2→1280x720 smoothscale）
        key = tuple(v // 4 for v in self._mix("bg_top") + self._mix("bg_bottom"))
        if self._bg_cache is None or self._bg_cache[0] != key:
            bg = pygame.Surface((2, 2))
            bg.fill(self._mix("bg_top"))
            pygame.draw.line(bg, self._mix("bg_bottom"), (0, 1), (1, 1))
            self._bg_cache = (key, pygame.transform.smoothscale(bg, (W, H)))
        self.screen.blit(self._bg_cache[1], (0, 0))
        # 星点背景（现代版更亮一点）
        self._draw_stars(t)

        self._draw_panel(t)
        self._draw_buttons(t)
        self._draw_bar(t)
        self._draw_toggle(t)
        self._draw_sparkles()
        self._draw_hud(t)
        pygame.display.flip()

    def _draw_stars(self, t):
        for i in range(70):
            x = (i * 197 + 61) % W
            y = (i * 263 + 37) % H
            tw = 0.5 + 0.5 * math.sin(self.global_t * 2 + i)
            c = self._mix("text_dim")
            c = tuple(min(255, int(v * (0.4 + 0.9 * tw * (0.4 + 0.6 * t)))) for v in c)
            r = 1 if i % 3 else 2
            pygame.draw.circle(self.screen, c, (x, y), r)

    def _rounded(self, rect, color, radius, border=0, border_color=None):
        """圆角矩形；radius=0 时退化为直角（旧版）"""
        radius = int(radius)
        if radius <= 1:
            pygame.draw.rect(self.screen, color, rect)
            if border:
                pygame.draw.rect(self.screen, border_color, rect, border)
        else:
            pygame.draw.rect(self.screen, color, rect, border_radius=radius)
            if border:
                pygame.draw.rect(self.screen, border_color, rect, border,
                                 border_radius=radius)

    def _draw_panel(self, t):
        p = self.panel
        # 面板底色（现代版更通透：alpha 随风格降低）
        base = self._mix("panel")
        alpha = self._mix_f("panel_alpha")
        surf = pygame.Surface((p.w, p.h), pygame.SRCALPHA)
        radius = self._mix_f("radius")
        pygame.draw.rect(surf, (*base, int(alpha)), (0, 0, p.w, p.h),
                         border_radius=int(radius))
        # 描边：旧版细蓝灰，现代版亮青且带辉光
        bc = self._mix("panel_border")
        bw = int(round(lerp(2, 2, t)))
        pygame.draw.rect(surf, bc, (0, 0, p.w, p.h), bw, border_radius=int(radius))
        if t > 0.02:
            glow = pygame.Surface((p.w, p.h), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*bc, int(60 * t)), (0, 0, p.w, p.h),
                             max(2, int(6 * t)), border_radius=int(radius))
            surf.blit(glow, (0, 0))
        # 顶部装饰线（旧版蓝灰横线 / 现代版金色横线）
        tl = self._mix("top_line")
        pygame.draw.rect(surf, (*tl, 200), (24, 0, p.w - 48, 3))
        self.screen.blit(surf, p.topleft)

        title = self._mix("title")
        f = font(int(lerp(30, 34, t)))
        ts = f.render("三国志 · 异想天开", True, title)
        self.screen.blit(ts, ts.get_rect(centerx=p.centerx, y=p.y + 52))
        f2 = font(15)
        sub = f2.render(STYLE_OLD["name"] if t < 0.5 else STYLE_NEW["name"],
                        True, self._mix("text_dim"))
        self.screen.blit(sub, sub.get_rect(centerx=p.centerx, y=p.y + 96))

    def _draw_buttons(self, t):
        radius = self._mix_f("radius") + 4 * t   # 现代版按钮圆角略大于面板
        for i, (label, _c) in enumerate(BTN_DEFS):
            r = self.btn_rects[i]
            hp, cp = self.hover_p[i], self.click_p[i]
            # 悬停缩放：两套风格都有，但现代版更夸张（1.05）
            sc = 1.0 + hp * lerp(0.03, 0.06, t) - cp * 0.04
            rr = pygame.Rect(0, 0, int(r.w * sc), int(r.h * sc))
            rr.center = r.center
            # 底色：旧版=统一按钮蓝；现代版=保留各功能色且更饱和
            old_c = lerp_col(STYLE_OLD["accent"], (16, 24, 46), 0.35)
            new_c = lerp_col(_c, (255, 255, 255), 0.08)
            base = lerp_col(old_c, new_c, t)
            base = lerp_col(base, (255, 255, 255), hp * lerp(0.08, 0.18, t))
            base = lerp_col(base, self._mix("accent_light"), cp * 0.5)
            # 现代版：悬停发光
            if t > 0.02 and hp > 0.02:
                gl = pygame.Surface((rr.w + 28, rr.h + 28), pygame.SRCALPHA)
                gr = pygame.Rect(0, 0, gl.get_width(), gl.get_height())
                pygame.draw.rect(gl, (*self._mix("accent"), int(70 * hp * t)),
                                 gr, border_radius=int(radius + 14))
                self.screen.blit(gl, (rr.x - 14, rr.y - 14))
            self._rounded(rr, base, radius, 2, lerp_col(base, (255, 255, 255), 0.35))
            tc = self._mix("btn_text")
            f = font(int(lerp(19, 21, t)))
            ts = f.render(label, True, tc)
            self.screen.blit(ts, ts.get_rect(center=rr.center))

    def _draw_bar(self, t):
        br = self.bar_rect
        radius = self._mix_f("radius") // 2 + int(6 * t)
        self._rounded(br, self._mix("bar_bg"), radius)
        fill = pygame.Rect(br.x, br.y, int(br.w * self.bar), br.h)
        # 旧版纯色填充 → 现代版青色渐变填充
        fs = pygame.Surface((max(1, fill.w), fill.h), pygame.SRCALPHA)
        c1 = self._mix("accent")
        c2 = self._mix("accent_light")
        for x in range(fs.get_width()):
            k = x / max(1, fs.get_width() - 1)
            pygame.draw.line(fs, lerp_col(c1, c2, 0.5 + 0.5 * math.sin(k * 2 - self.global_t * 3)),
                             (x, 0), (x, fs.get_height()))
        if radius > 1:
            mask = pygame.Surface(fs.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255), mask.get_rect(),
                             border_radius=int(radius))
            fs.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(fs, fill.topleft)
        f = font(15)
        lab = f.render("国力 %d%%" % int(self.bar * 100), True, self._mix("text_dim"))
        self.screen.blit(lab, lab.get_rect(centerx=br.centerx, y=br.y - 24))

    def _draw_toggle(self, t):
        r = self.toggle_rect
        # 滑块式切换开关：左=旧版 右=新版，随 style_t 平滑滑动
        track = pygame.Rect(r.x, r.y, r.w, r.h)
        radius = lerp(6, r.h // 2, t)
        self._rounded(track, self._mix("bar_bg"), radius, 2, self._mix("accent"))
        kx = lerp(r.h // 2, r.w - r.h // 2, t)
        kcolor = lerp_col(STYLE_OLD["accent_light"], STYLE_NEW["accent"], t)
        pygame.draw.circle(self.screen, kcolor, (int(r.x + kx), r.centery), r.h // 2 - 5)
        f = font(14)
        ts = f.render("风格切换", True, self._mix("text_dim"))
        self.screen.blit(ts, (r.x, r.y - 22))

    def _draw_sparkles(self):
        for x, y, _vx, _vy, life, size in self.sparkles:
            a = int(255 * clamp01(life / 0.9))
            s = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, a),
                               (s.get_width() // 2, s.get_height() // 2), int(size))
            self.screen.blit(s, (x - s.get_width() // 2, y - s.get_height() // 2))

    def _draw_hud(self, t):
        f = font(15)
        tip = f.render("空格 / Tab / 点击开关 = 平滑切换新旧 UI   ESC = 退出",
                       True, self._mix("text_dim"))
        tip.set_alpha(170)
        self.screen.blit(tip, (16, H - 28))
        tag = f.render("风格 %s  切换 %d 次  ·  全部程序实时生成 · by lsy123456114514"
                       % (("%.0f%%" % (t * 100)), self.switch_count),
                       True, self._mix("text_dim"))
        tag.set_alpha(140)
        self.screen.blit(tag, (16, 12))

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    UISwitchDemo().run()
