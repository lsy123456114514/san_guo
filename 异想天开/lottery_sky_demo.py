#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异想天开 · 抽奖星空穿越 DEMO（纯程序生成，无任何美术素材）

流程：
  1) 遮罩   —— 深色游戏风背景慢慢变浅，直至全白
  2) 天空   —— 白光散去已是蓝天，镜头持续上升，云层掠过，天色渐暗
  3) 太空   —— 星海浮现，下方是程序绘制的地球
  4) 星座   —— 7 颗亮星汇聚成北斗形，逐段连线充能
  5) 光柱   —— 强光柱从星座射向地球，镜头追随光柱俯冲返回
  6) 奖品   —— 光柱落地化作奖品卡片（按稀有度随机）

操作：空格/点击 = 跳过当前阶段；奖品页按钮可再抽/完整重放；ESC 退出
运行：py 异想天开\\lottery_sky_demo.py
"""
import math
import random

import pygame

W, H = 1280, 720
FPS = 60

PHASES = ["mask", "sky", "space", "constellation", "beam", "prize"]
DUR = {"mask": 2.4, "sky": 4.2, "space": 2.6, "constellation": 3.4, "beam": 3.4}

# (名称, 稀有度, 稀有度颜色, 图标种类)
PRIZE_POOL = [
    ("金元宝 x100",    "普通", (170, 170, 170), "ingot"),
    ("木材 x500",      "普通", (170, 170, 170), "wood"),
    ("高级鱼饵 x10",   "稀有", (80, 170, 255), "fish"),
    ("宠物粮食 x20",   "稀有", (80, 170, 255), "bag"),
    ("稀有武将自选箱", "史诗", (190, 110, 255), "chest"),
    ("天赋重置券 x3",  "史诗", (190, 110, 255), "scroll"),
    ("传说武将·吕布",  "传说", (255, 200, 60), "hero"),
    ("神兵·方天画戟",  "传说", (255, 200, 60), "spear"),
]
RARE_W = {"普通": 46, "稀有": 32, "史诗": 16, "传说": 6}

# 北斗七星（归一化坐标，星座阶段补间到位）
DIPPER = [(-0.52, 0.16), (-0.34, 0.30), (-0.14, 0.28), (0.02, 0.12),
          (0.18, 0.00), (0.36, -0.06), (0.52, -0.18)]


def clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_col(c1, c2, t):
    t = clamp01(t)
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def ease_out(t):
    return 1 - (1 - clamp01(t)) ** 3


def ease_in_out(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


_font_cache = {}


def font(sz):
    f = _font_cache.get(sz)
    if f is None:
        f = pygame.font.SysFont("microsoftyahei,simhei", sz)
        _font_cache[sz] = f
    return f


def make_stars(n=260):
    """程序化星空：普通星 + 预留 7 颗亮星（星座用）"""
    stars = []
    for _ in range(n):
        stars.append({
            "x": random.uniform(0, W), "y": random.uniform(0, H),
            "r": random.choice([1, 1, 1, 2, 2, 3]),
            "tw": random.uniform(0, math.tau),
            "ts": random.uniform(1.5, 4.0),
            "layer": random.uniform(0.25, 1.0),
            "big": False,
            "hx": 0.0, "hy": 0.0,   # 星座阶段的补间位置
        })
    for s in random.sample(stars, 7):
        s["big"] = True
        s["r"] = 4
    return stars


def make_cloud():
    """程序化云：若干白色圆叠成一团"""
    w = random.randint(190, 340)
    h = random.randint(70, 130)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(random.randint(6, 10)):
        r = random.randint(h // 3, h // 2)
        x = random.randint(r, max(r + 1, w - r))
        y = random.randint(r, max(r + 1, h - r))
        pygame.draw.circle(surf, (255, 255, 255, 210), (x, y), r)
    return surf


def make_earth(r=300):
    """程序化地球：大气辉光 + 海洋渐变 + 随机大陆 + 极帽 + 高光"""
    size = r * 2 + 48
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    for extra, a in ((20, 34), (13, 64), (6, 105)):
        pygame.draw.circle(surf, (120, 190, 255, a), (cx, cy), r + extra)
    for i in range(r, 0, -2):
        t = i / r
        pygame.draw.circle(
            surf,
            (int(lerp(45, 18, t)), int(lerp(112, 55, t)), int(lerp(200, 135, t)), 255),
            (cx, cy), i)
    rng = random.Random(42)  # 固定种子：每次打开都是同一颗“程序地球”
    for _ in range(rng.randint(7, 10)):
        ang = rng.uniform(0, math.tau)
        dist = rng.uniform(0, r * 0.62)
        bx = cx + math.cos(ang) * dist
        by = cy + math.sin(ang) * dist * 0.85
        for _ in range(rng.randint(4, 8)):
            rr = rng.randint(max(3, r // 9), max(4, r // 4))
            ox = int(bx + rng.randint(-r // 5, r // 5))
            oy = int(by + rng.randint(-r // 6, r // 6))
            if (ox - cx) ** 2 + (oy - cy) ** 2 < (r - rr - 6) ** 2:
                pygame.draw.circle(surf, (70, 140, 85, 255), (ox, oy), rr)
    pygame.draw.circle(surf, (235, 245, 255, 230), (cx, cy - r + 9), max(4, r // 6))
    pygame.draw.circle(surf, (235, 245, 255, 230), (cx, cy + r - 9), max(4, r // 6))
    pygame.draw.circle(surf, (255, 255, 255, 34), (cx - r // 3, cy - r // 3), r // 2)
    return surf


def make_beam(w=260, h=740):
    """程序化光柱贴图：横向高斯 + 纵向渐隐，金白色"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    for x in range(w):
        d = abs(x - cx) / cx
        a = int(210 * math.exp(-3.2 * d * d))
        if a <= 0:
            continue
        col = (255, 250, 220) if d < 0.22 else (255, 214, 120)
        pygame.draw.line(surf, (*col, a), (x, 0), (x, h))
    # 白热核心
    for x in range(max(0, cx - 5), min(w, cx + 5)):
        pygame.draw.line(surf, (255, 255, 255, 240), (x, 0), (x, h))
    # 纵向渐隐（顶亮底实）
    fade = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        a = int(255 * clamp01(0.35 + y / h * 0.9))
        pygame.draw.line(fade, (255, 255, 255, a), (0, y), (w, y))
    surf.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def draw_icon(surf, kind, cx, cy, s):
    """奖品小图标：全用基础图形现画"""
    if kind == "ingot":
        pygame.draw.ellipse(surf, (255, 205, 70), (cx - s, cy - s * 0.45, s * 2, s * 0.9))
        pygame.draw.ellipse(surf, (255, 235, 150), (cx - s * 0.6, cy - s * 0.65, s * 1.2, s * 0.5))
        pygame.draw.ellipse(surf, (200, 150, 30), (cx - s, cy - s * 0.45, s * 2, s * 0.9), 2)
    elif kind == "wood":
        pygame.draw.rect(surf, (150, 100, 55), (cx - s, cy - s * 0.3, s * 2, s * 0.6), border_radius=4)
        pygame.draw.circle(surf, (210, 170, 110), (cx - s + 5, cy), 6)
        pygame.draw.circle(surf, (170, 120, 70), (cx - s + 5, cy), 3)
    elif kind == "fish":
        pygame.draw.ellipse(surf, (120, 190, 255), (cx - s, cy - s * 0.4, s * 1.6, s * 0.8))
        pygame.draw.polygon(surf, (90, 160, 230),
                            [(cx + s * 0.55, cy), (cx + s, cy - s * 0.45), (cx + s, cy + s * 0.45)])
        pygame.draw.circle(surf, (20, 30, 60), (cx - s * 0.55, cy - 2), 2)
    elif kind == "bag":
        pygame.draw.circle(surf, (190, 150, 90), (cx, cy + 4), int(s * 0.85))
        pygame.draw.rect(surf, (150, 110, 60), (cx - 6, cy - s * 0.9, 12, 10), border_radius=3)
        pygame.draw.line(surf, (110, 80, 40), (cx - 8, cy - s * 0.45), (cx + 8, cy - s * 0.45), 3)
    elif kind == "chest":
        pygame.draw.rect(surf, (140, 90, 45), (cx - s, cy - s * 0.2, s * 2, s * 0.9), border_radius=4)
        pygame.draw.rect(surf, (170, 120, 60), (cx - s, cy - s * 0.75, s * 2, s * 0.55), border_radius=6)
        pygame.draw.rect(surf, (255, 210, 90), (cx - 6, cy - s * 0.25, 12, 14), border_radius=2)
    elif kind == "scroll":
        pygame.draw.rect(surf, (245, 235, 205), (cx - s, cy - s * 0.45, s * 2, s * 0.9), border_radius=4)
        pygame.draw.circle(surf, (200, 180, 130), (cx - s + 3, cy), 7)
        pygame.draw.circle(surf, (200, 180, 130), (cx + s - 3, cy), 7)
        for i in range(3):
            pygame.draw.line(surf, (150, 130, 90),
                             (cx - s * 0.55, cy - s * 0.2 + i * 8), (cx + s * 0.55, cy - s * 0.2 + i * 8), 2)
    elif kind == "hero":
        pygame.draw.circle(surf, (220, 180, 140), (cx, cy + 3), int(s * 0.6))
        pygame.draw.rect(surf, (180, 60, 60), (cx - s * 0.6, cy - s * 0.55, s * 1.2, 8), border_radius=3)
        pygame.draw.polygon(surf, (230, 80, 80),
                            [(cx, cy - s * 0.55), (cx - 5, cy - s * 1.05), (cx + 5, cy - s * 1.05)])
    elif kind == "spear":
        pygame.draw.line(surf, (160, 120, 70), (cx - s * 0.7, cy + s * 0.7), (cx + s * 0.5, cy - s * 0.5), 5)
        pygame.draw.polygon(surf, (210, 215, 225),
                            [(cx + s * 0.5, cy - s * 0.5), (cx + s * 0.95, cy - s * 0.95),
                             (cx + s * 0.62, cy - s * 0.42), (cx + s * 0.42, cy - s * 0.62)])
        pygame.draw.circle(surf, (200, 50, 50), (cx + s * 0.42, cy - s * 0.42), 5)


def pick_prize():
    names = [p[0] for p in PRIZE_POOL]
    weights = [RARE_W[p[1]] for p in PRIZE_POOL]
    return random.choices(names, weights=weights, k=1)[0]


class LotterySky:
    """六阶段状态机：所有画面均为运行时程序生成"""

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("抽奖星空穿越 DEMO - 异想天开")
        self.running = True
        self.stars = make_stars()
        self.clouds = []           # [surface, x, y, speed, scale]
        self.earth = make_earth(300)
        self.beam_tex = make_beam()
        self.t = 0.0               # 当前阶段内时间
        self.phase = "mask"
        self.global_t = 0.0
        self.shake = 0.0
        self.flash = 0.0           # 白屏闪光 0..1
        self.prize_name = pick_prize()
        self.prize_meta = next(p for p in PRIZE_POOL if p[0] == self.prize_name)
        self.card_t = 0.0          # 奖品卡弹出进度
        self.beam_hit = 0.0        # 光柱落地扩散波
        self.const_t = 0.0         # 星星补间进度
        self.line_t = 0.0          # 连线进度
        self.glow_t = 0.0          # 充能进度
        self._star_home = [(s["x"], s["y"]) for s in self.stars]

    def _next_phase(self):
        i = PHASES.index(self.phase)
        if i + 1 < len(PHASES):
            self.phase = PHASES[i + 1]
        self.t = 0.0
        if self.phase == "beam":
            self.flash = 0.0

    def skip(self):
        if self.phase in ("mask", "sky", "space", "constellation", "beam"):
            self._next_phase()
        elif self.phase == "prize":
            self.reroll()

    def reroll(self):
        self.prize_name = pick_prize()
        self.prize_meta = next(p for p in PRIZE_POOL if p[0] == self.prize_name)
        self.phase = "constellation"
        self.t = 0.0
        self.card_t = 0.0
        self.const_t = 0.0
        self.line_t = 0.0
        self.glow_t = 0.0
        for (hx, hy), s in zip(self._star_home, [x for x in self.stars if x["big"]]):
            s["hx"], s["hy"] = hx, hy

    def replay(self):
        self.phase = "mask"
        self.t = 0.0
        self.card_t = 0.0
        self.flash = 0.0
        self.clouds.clear()
        self.prize_name = pick_prize()
        self.prize_meta = next(p for p in PRIZE_POOL if p[0] == self.prize_name)

    # ── 更新 ──────────────────────────────────────────────
    def update(self, dt):
        self.t += dt
        self.global_t += dt
        self.flash = max(0.0, self.flash - dt * 1.6)
        self.shake = max(0.0, self.shake - dt * 2.2)
        self.beam_hit = max(0.0, self.beam_hit - dt * 0.8)

        if self.phase == "mask":
            if self.t >= DUR["mask"]:
                self._next_phase()

        elif self.phase == "sky":
            # 云：从上方生成，随镜头上升向下掠过
            if random.random() < dt * 2.2:
                self.clouds.append([make_cloud(),
                                    random.uniform(-100, W - 60),
                                    random.uniform(-160, -60),
                                    random.uniform(220, 520),
                                    random.uniform(0.5, 1.2)])
            for c in self.clouds:
                c[2] += c[3] * dt * (1 + self.t * 0.5)
            self.clouds = [c for c in self.clouds if c[2] < H + 220]
            if self.t >= DUR["sky"]:
                self._next_phase()

        elif self.phase == "space":
            if self.t >= DUR["space"]:
                # 进星座阶段：先保存亮星原位，再启动补间
                big = [s for s in self.stars if s["big"]]
                cx, cy = W * 0.5, H * 0.34
                for s, (dx, dy) in zip(big, DIPPER):
                    s["hx"] = cx + dx * 300
                    s["hy"] = cy + dy * 300
                self._next_phase()

        elif self.phase == "constellation":
            big = [s for s in self.stars if s["big"]]
            self.const_t = clamp01(self.t / 1.4)
            self.line_t = clamp01((self.t - 1.3) / 1.2)
            self.glow_t = clamp01((self.t - 2.4) / 1.0)
            e = ease_out(self.const_t)
            # 逐星从原位飞向目标
            for i, s in enumerate(big):
                start_x, start_y = self._star_home[i]
                s["x"] = lerp(start_x, s["hx"], e)
                s["y"] = lerp(start_y, s["hy"], e)
            if self.glow_t >= 1.0:
                self.flash = 1.0
                self.shake = 1.0
                self._next_phase()
            elif self.t >= DUR["constellation"]:
                self.flash = 1.0
                self.shake = 1.0
                self._next_phase()

        elif self.phase == "beam":
            # 光柱从星座打向地球；镜头被震退后开始追随俯冲
            if self.t >= 1.6 and self.beam_hit <= 0.0 and self.t < 1.7:
                self.shake = 1.0
                self.beam_hit = 1.0
            if self.t >= DUR["beam"]:
                self.flash = 1.0
                self._next_phase()

        elif self.phase == "prize":
            self.card_t = clamp01(self.card_t + dt * 1.6)

    # ── 绘制 ──────────────────────────────────────────────
    def _sky_grad(self, top, bottom):
        h = pygame.Surface((W, 2), pygame.SRCALPHA)
        for y in range(2):
            pygame.draw.line(h, (*top, 255), (0, y), (W, y))
        return pygame.transform.smoothscale(h, (W, H))

    def draw(self):
        s = self.screen
        if self.phase == "mask":
            # 深色游戏风背景 → 逐渐变浅至白
            p = ease_in_out(self.t / DUR["mask"])
            top = lerp_col((18, 18, 40), (255, 255, 255), p)
            bot = lerp_col((40, 30, 70), (255, 255, 255), p)
            s.blit(self._sky_grad(top, bot), (0, 0))
            if p < 0.55:
                a = int(255 * (1 - p / 0.55))
                txt = font(30).render("正在离开这个世界…", True, (255, 220, 130))
                txt.set_alpha(a)
                s.blit(txt, txt.get_rect(center=(W // 2, H // 2)))

        elif self.phase == "sky":
            p = self.t / DUR["sky"]
            top = lerp_col((110, 170, 235), (8, 10, 30), ease_in_out(p))
            bot = lerp_col((195, 225, 250), (30, 40, 90), ease_in_out(p))
            s.blit(self._sky_grad(top, bot), (0, 0))
            for c in self.clouds:
                surf, x, y, _, sc = c[0], c[1], c[2], c[3], c[4]
                cs = pygame.transform.scale(surf, (int(surf.get_width() * sc), int(surf.get_height() * sc)))
                cs.set_alpha(int(230 * clamp01(1.2 - p)))
                s.blit(cs, (x, y))
            # 天色过半后星星淡入
            if p > 0.5:
                self._draw_stars(clamp01((p - 0.5) * 2.2))
            txt = font(22).render("上升中 %.0f%%" % (p * 100), True, (255, 255, 255))
            txt.set_alpha(180)
            s.blit(txt, (W - txt.get_width() - 24, 20))

        elif self.phase in ("space", "constellation", "beam"):
            s.blit(self._sky_grad((3, 4, 14), (10, 14, 36)), (0, 0))
            self._draw_stars(1.0)
            self._draw_earth_space()
            if self.phase == "constellation":
                self._draw_constellation()
            elif self.phase == "beam":
                self._draw_beam_phase()

        elif self.phase == "prize":
            # 回到夜空背景下开卡
            s.blit(self._sky_grad((3, 4, 14), (10, 14, 36)), (0, 0))
            self._draw_stars(0.8)
            self._draw_prize_card()

        # 全屏闪光 + 抖动提示
        if self.flash > 0:
            f = pygame.Surface((W, H))
            f.fill((255, 255, 255))
            f.set_alpha(int(255 * self.flash))
            s.blit(f, (0, 0))
        self._draw_hud()
        pygame.display.flip()

    def _draw_stars(self, alpha):
        for st in self.stars:
            tw = 0.55 + 0.45 * math.sin(self.global_t * st["ts"] + st["tw"])
            r = st["r"]
            x, y = int(st["x"]), int(st["y"])
            if not (-6 <= x <= W + 6 and -6 <= y <= H + 6):
                continue
            col = (255, 255, 255) if not st["big"] else (255, 244, 200)
            sz = max(1, int(r * tw * alpha))
            if sz > 0:
                pygame.draw.circle(self.screen, col, (x, y), sz)
                if st["big"]:
                    pygame.draw.circle(self.screen, col, (x, y), sz + 4, 1)

    def _draw_earth_space(self):
        e = self.earth
        if self.phase == "beam":
            # 俯冲：地球放大并向上迎面而来
            p = clamp01((self.t - 1.2) / (DUR["beam"] - 1.2))
            sc = 1 + p * 3.2
            ew = int(e.get_width() * sc)
            ee = pygame.transform.smoothscale(e, (ew, ew))
            cx = W // 2 + int(math.sin(self.global_t * 40) * self.shake * 6)
            cy = int(lerp(H * 0.72, H * 0.52, ease_in_out(p)))
            self.screen.blit(ee, (cx - ew // 2, cy - ew // 2))
        else:
            ew = int(e.get_width() * 0.55)
            ee = pygame.transform.smoothscale(e, (ew, ew))
            self.screen.blit(ee, (W // 2 - ew // 2, int(H * 0.66) - ew // 2))

    def _draw_constellation(self):
        big = [s for s in self.stars if s["big"]]
        pts = [(int(s["x"]), int(s["y"])) for s in big]
        # 逐段连线
        n_seg = len(pts) - 1
        shown = self.line_t * n_seg
        for i in range(n_seg):
            seg = clamp01(shown - i)
            if seg <= 0:
                break
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            xh = int(lerp(x1, x2, seg))
            yh = int(lerp(y1, y2, seg))
            pygame.draw.line(self.screen, (255, 230, 150), (x1, y1), (xh, yh), 2)
        # 充能：连线整体增亮 + 中心聚能光球
        if self.glow_t > 0:
            g = ease_in_out(self.glow_t)
            for i in range(n_seg):
                pygame.draw.line(self.screen, (255, 255, 220), pts[i], pts[i + 1], 1 + int(g * 2))
            cx = sum(p[0] for p in pts) // len(pts)
            cy = sum(p[1] for p in pts) // len(pts)
            r = int(g * 46)
            if r > 0:
                for rr, a in ((r, 70), (int(r * 0.6), 140), (int(r * 0.3), 235)):
                    gl = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
                    pygame.draw.circle(gl, (255, 250, 210, a), (rr, rr), rr)
                    self.screen.blit(gl, (cx - rr, cy - rr))

    def _draw_beam_phase(self):
        big = [s for s in self.stars if s["big"]]
        bx = sum(s["x"] for s in big) // len(big)
        by = sum(s["y"] for s in big) // len(big)
        # 光柱打出进度
        bp = clamp01(self.t / 1.5)
        if bp > 0:
            tex = self.beam_tex
            beam_h = int(H * 1.15 * ease_out(bp))
            tw = tex.get_width()
            th = tex.get_height()
            seg = pygame.transform.scale(tex, (tw, beam_h))
            seg.set_alpha(235)
            jx = int(math.sin(self.global_t * 47) * self.shake * 8)
            jy = int(math.cos(self.global_t * 39) * self.shake * 6)
            self.screen.blit(seg, (bx - tw // 2 + jx, by + jy))
            # 落地冲击波
            if self.beam_hit > 0:
                rr = int((1 - self.beam_hit) * 320) + 30
                wv = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
                pygame.draw.circle(wv, (255, 240, 180, int(160 * self.beam_hit)), (rr, rr), rr, 4)
                ey = int(lerp(H * 0.72, H * 0.52, ease_in_out(clamp01((self.t - 1.2) / 2.2))))
                self.screen.blit(wv, (W // 2 - rr, ey - rr))

    def _draw_prize_card(self):
        name, rarity, rcol, icon = self.prize_meta
        e = ease_out(self.card_t)
        cw, ch = int(lerp(340, 560, e)), int(lerp(200, 320, e))
        cx, cy = W // 2, H // 2 - 10
        card = pygame.Rect(cx - cw // 2, cy - ch // 2, cw, ch)
        # 卡底 + 稀有度流光边
        pygame.draw.rect(self.screen, (24, 24, 48), card, border_radius=18)
        pygame.draw.rect(self.screen, rcol, card, 4, border_radius=18)
        for i, a in ((8, 60), (14, 30)):
            pygame.draw.rect(self.screen, rcol, card.inflate(i * 2, i * 2), 2, border_radius=22)
        if e > 0.35:
            a = clamp01((e - 0.35) / 0.65)
            # 稀有度徽带
            tag = font(24).render(rarity, True, (20, 20, 30))
            tag_bg = pygame.Rect(0, 0, tag.get_width() + 28, 34)
            tag_bg.center = (cx, card.y + 34)
            pygame.draw.rect(self.screen, rcol, tag_bg, border_radius=17)
            self.screen.blit(tag, tag.get_rect(center=tag_bg.center))
            # 图标（放大绘制）
            icon_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
            draw_icon(icon_surf, icon, 80, 80, 52)
            self.screen.blit(icon_surf, (cx - 80, card.y + 52))
            # 名称
            nm = font(34).render(name, True, (255, 255, 255))
            nm.set_alpha(int(255 * a))
            self.screen.blit(nm, nm.get_rect(center=(cx, card.bottom - 74)))
            # 声明
            note = font(18).render("纯由程序生成 · Procedurally Generated", True, (170, 175, 200))
            note.set_alpha(int(230 * a))
            self.screen.blit(note, note.get_rect(center=(cx, card.bottom - 30)))
            # 按钮
            self._draw_button("再抽一次", cx - 150, card.bottom + 46, (80, 130, 220))
            self._draw_button("完整重放", cx + 10, card.bottom + 46, (90, 170, 110))

    def _draw_button(self, label, x, y, col):
        rect = pygame.Rect(x, y, 140, 44)
        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my)
        c = tuple(min(255, v + 35) if hover else v for v in col)
        pygame.draw.rect(self.screen, c, rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=10)
        t = font(22).render(label, True, (255, 255, 255))
        self.screen.blit(t, t.get_rect(center=rect.center))
        return rect

    def _button_rects(self):
        cw = 560
        cx, cy = W // 2, H // 2 - 10
        ch = 320
        return (pygame.Rect(cx - 150, cy + ch // 2 + 24, 140, 44),
                pygame.Rect(cx + 10, cy + ch // 2 + 24, 140, 44))

    def _draw_hud(self):
        tips = "空格/点击=跳过当前阶段   R=再抽   T=完整重放   ESC=退出"
        t = font(16).render(tips, True, (200, 205, 230))
        t.set_alpha(140)
        self.screen.blit(t, (16, H - 30))
        phase_cn = {"mask": "遮罩", "sky": "天空", "space": "太空",
                    "constellation": "星座连线", "beam": "光柱返航", "prize": "开奖"}
        pt = font(16).render("阶段: %s" % phase_cn[self.phase], True, (255, 220, 130))
        pt.set_alpha(160)
        self.screen.blit(pt, (16, 12))

    # ── 主循环 ────────────────────────────────────────────
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.running = False
                    elif ev.key == pygame.K_SPACE:
                        self.skip()
                    elif ev.key == pygame.K_r:
                        self.reroll()
                    elif ev.key == pygame.K_t:
                        self.replay()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.phase == "prize" and self.card_t >= 1.0:
                        r1, r2 = self._button_rects()
                        if r1.collidepoint(ev.pos):
                            self.reroll()
                        elif r2.collidepoint(ev.pos):
                            self.replay()
                    else:
                        self.skip()
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    pygame.init()
    try:
        LotterySky().run()
    except Exception:
        import traceback
        traceback.print_exc()
        pygame.quit()


if __name__ == "__main__":
    main()


