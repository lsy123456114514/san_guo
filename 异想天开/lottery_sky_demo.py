#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异想天开 · 抽奖星空穿越 DEMO v2（真实贴图 + 连续运镜）

相对 v1 的改进（按反馈）：
  1. 地球 = 真实 NASA 蓝色星球贴图（earth_atmos_2048.jpg）+ 真实云层贴图，
     用 numpy 逐像素光线求交裹到 3D 球体上（球面任意位置都有像素，不存在多边形棱角/
     空洞），带自转、晨昏线、大气边缘辉光。
  2. 摄像机全程连续运动：一条平滑的时间线插值，不再一个阶段“跨”一下；
     空格跳过也是快进式过渡（短促缩放），不是硬切。
  3. 云改用 fBm 分形噪声程序生成（棉絮状、有厚薄层次），不再是圆片拼贴。

流程（连续时间线，约 20 秒）：
  遮罩变浅 → 露出天空并持续上升（穿云、天色变暗）→ 飞出大气层见真实地球
  → 7 颗亮星汇聚成北斗、逐段连线充能 → 光柱射向地球、镜头跟随俯冲
  → 白光化作奖品卡

贴图来源：NASA Blue Marble（公有领域），存放在 异想天开/assets/。
缺失贴图时自动回退为程序生成的地球，仍可运行。

操作：空格/点击=快进到下一幕  R=再抽  T=完整重放  ESC=退出
运行：py 异想天开\\lottery_sky_demo.py
"""
import math
import os
import random
import time

import pygame

# numpy 用于 3D 球体逐像素渲染
try:
    import numpy as np
    HAS_NP = True
except Exception:
    HAS_NP = False

W, H = 1280, 720
FPS = 60
HERE = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(HERE, "assets")

# 连续时间线上的“幕”边界（秒）。相机参数全部由 t 平滑插值，不在此处硬切。
ACTS = {
    "mask": 0.0,        # 遮罩变浅
    "sky": 2.6,         # 露出天空、开始上升
    "space": 10.4,      # 冲出大气层、地球完整可见
    "constellation": 13.6,  # 汇聚北斗、连线充能
    "beam": 18.6,       # 光柱射向地球 + 俯冲跟随
    "prize": 24.0,      # 白光化作奖品
}
ACT_ORDER = ["mask", "sky", "space", "constellation", "beam", "prize"]
TOTAL_END = 27.0        # 时间线走完（之后停在奖品页）

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

# 北斗七星（屏幕归一化坐标，星座幕补间到位）
DIPPER = [(-0.52, 0.16), (-0.34, 0.30), (-0.14, 0.28), (0.02, 0.12),
          (0.18, 0.00), (0.36, -0.06), (0.52, -0.18)]


def clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def lerp(a, b, t):
    return a + (b - a) * clamp01(t)


def lerp_col(c1, c2, t):
    t = clamp01(t)
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def ease_out(t):
    return 1 - (1 - clamp01(t)) ** 3


def ease_in(t):
    t = clamp01(t)
    return t * t * t


def ease_in_out(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def norm(t0, t1, t):
    """把 [t0,t1] 区间内的 t 归一化到 0..1 并夹紧（连续时间线的核心工具）"""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp01((t - t0) / (t1 - t0))


def act_at(t):
    """当前所处的幕（按时间线判定）"""
    cur = ACT_ORDER[0]
    for name in ACT_ORDER:
        if t >= ACTS[name] - 1e-6:
            cur = name
    return cur


_font_cache = {}


def font(sz):
    f = _font_cache.get(sz)
    if f is None:
        f = pygame.font.SysFont("microsoftyahei,simhei", sz)
        _font_cache[sz] = f
    return f


# ── 贴图加载 ─────────────────────────────────────────────────────────────
def _load_texture():
    """返回 (地球日面 RGB ndarray float32 0..1, 云层 alpha ndarray 0..1) 或 (None, None)"""
    if not HAS_NP:
        return None, None
    day_path = os.path.join(ASSET_DIR, "earth_day.jpg")
    if not os.path.exists(day_path):
        # 回退：仓库根目录用户放置的贴图
        alt = os.path.join(os.path.dirname(HERE), "earth_atmos_2048.jpg")
        if os.path.exists(alt):
            day_path = alt
        else:
            alt2 = os.path.join(HERE, "earth_atmos_2048.jpg")
            if os.path.exists(alt2):
                day_path = alt2
    if not os.path.exists(day_path):
        return None, None
    try:
        from PIL import Image
        img = Image.open(day_path).convert("RGB")
        if img.width > 1024:  # 缩一半，渲染够用且更快
            img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        day = np.asarray(img, dtype=np.float32) / 255.0
        cloud = None
        cpath = os.path.join(ASSET_DIR, "earth_clouds.png")
        try:   # 云层文件损坏时只丢云层，不连累日面
            if os.path.exists(cpath):
                cimg = Image.open(cpath).convert("RGBA")
                if cimg.width > 1024:
                    cimg = cimg.resize((cimg.width // 2, cimg.height // 2), Image.LANCZOS)
                if cimg.size != (day.shape[1], day.shape[0]):
                    cimg = cimg.resize((day.shape[1], day.shape[0]), Image.LANCZOS)
                ca = np.asarray(cimg, dtype=np.float32)[..., 3] / 255.0
                # 云层烘焙进日面贴图：渲染时省掉整整一次全图双线性采样
                # （单次地球渲染成本近半——性能关键）。代价是云不再有
                # 相对地表的独立自转，0.032 rad/s 下几乎看不出。
                day = day * (1 - ca[..., None] * 0.9) + 0.96 * ca[..., None] * 0.9
        except Exception:
            pass
        return day, cloud
    except Exception:
        return None, None


def _fallback_earth_tex(w=512, h=256):
    """贴图缺失时的程序地球（噪声大陆），保证 demo 不至于没画面"""
    rng = np.random.default_rng(42)
    lat = np.linspace(-math.pi / 2, math.pi / 2, h, dtype=np.float32)[:, None]
    lon = np.linspace(-math.pi, math.pi, w, dtype=np.float32)[None, :]
    tex = np.zeros((h, w, 3), dtype=np.float32)
    # 海洋渐变
    tex[..., 0] = 0.06 + 0.05 * np.cos(lat) ** 2
    tex[..., 1] = 0.18 + 0.12 * np.cos(lat) ** 2
    tex[..., 2] = 0.42 + 0.18 * np.cos(lat) ** 2
    # 噪声大陆
    field = rng.random((h // 8, w // 8), dtype=np.float32)
    field = np.repeat(np.repeat(field, 8, axis=0), 8, axis=1)
    land = field > 0.62
    tex[land, 0] = 0.25
    tex[land, 1] = 0.45
    tex[land, 2] = 0.20
    # 极帽（lat 是 (h,1) 列向量，布尔蒙版按行广播）
    cap = np.abs(lat[:, 0]) > 1.28
    tex[cap] = (0.93, 0.96, 1.0)
    return tex, None


# ── 3D 地球：numpy 逐像素光线求交 + 球面贴图（无多边形、无空洞） ─────────
class Earth3D:
    """把等距圆柱投影贴图裹到 3D 球上。

    对屏幕每个像素投一条视线与单位球求交，取交点法线反算经纬度采样贴图。
    球面每像素都有颜色，因此不存在 v1 那种多边形缝隙/空洞。
    """

    def __init__(self, day_tex, cloud_tex):
        self.day = day_tex
        self.cloud = cloud_tex
        self.spin = 0.0            # 自转角（弧度）
        self.tilt = 0.38           # 地轴倾角（弧度，约 22°）
        # 后台渲染：主线程只拿最新结果，绝不等 numpy（避免几百 ms 巨帧卡顿）
        self._latest_key = None    # 主线程写：请求的 (size, spin)
        self._latest_surf = None
        self._latest_sun = (-0.55, -0.35, 0.76)
        self._cache_key = None     # 渲染线程内部缓存
        self._cache_surf = None
        # 预生成经纬度网格（与贴图尺寸一致）
        h, w = day_tex.shape[:2]
        lat = np.linspace(math.pi / 2, -math.pi / 2, h, dtype=np.float32)[:, None]
        lon = np.linspace(-math.pi, math.pi, w, endpoint=False, dtype=np.float32)[None, :]
        self.lat_grid = np.broadcast_to(lat, (h, w))
        self.lon_grid = np.broadcast_to(lon, (h, w))
        # 同步预热一帧：让 _latest_surf 立刻有内容，主线程不会看到空球
        try:
            self.render(256, self._latest_sun)
        except Exception:
            pass

    def kick(self, size, sun_dir=(-0.55, -0.35, 0.76)):
        """主线程调用：请求一帧渲染（不等待）。渲染由后台线程空闲时完成。

        返回当前最新可用的 surface（可能落后一帧/低分辨率，但绝不卡）。
        """
        key = (size, round(self.spin, 2))
        self._latest_key = key       # 单个原子引用写，后台线程看到就重渲染
        self._latest_sun = sun_dir
        return self._latest_surf

    def _sample(self, tex, u, v):
        """双线性采样；u,v 为 0..1 归一坐标（已是 ndarray float32）

        注意所有中间量必须保持 float32：float32 - int32 在 numpy 里会提升成
        float64，中间数组体积翻倍且更慢（实测占单次渲染成本的一半）。
        """
        h, w = tex.shape[:2]
        x = np.clip(u * (w - 1), 0, w - 1.001)
        y = np.clip(v * (h - 1), 0, h - 1.001)
        x0 = x.astype(np.int32)
        y0 = y.astype(np.int32)
        fx = np.subtract(x, x0, dtype=np.float32)   # 显式 float32，防提升
        fy = np.subtract(y, y0, dtype=np.float32)
        if tex.ndim == 3:
            fx = fx[..., None]
            fy = fy[..., None]
        x1 = x0 + 1
        y1 = y0 + 1
        c00 = tex[y0, x0]
        c01 = tex[y0, x1]
        c10 = tex[y1, x0]
        c11 = tex[y1, x1]
        top = c00 + (c01 - c00) * fx     # 少一个临时数组的写法
        bot = c10 + (c11 - c10) * fx
        return top + (bot - top) * fy

    def render(self, size, sun_dir=(-0.55, -0.35, 0.76)):
        """渲染球体到 (size,size) 的 RGBA surface。size = 球直径像素。

        仅由后台渲染线程调用；主线程请用 kick()。
        """
        # spin 量化到 0.01 rad：自转很慢，相邻帧可复用缓存（性能关键）
        key = (size, round(self.spin, 2))
        if key == self._cache_key and self._cache_surf is not None:
            return self._cache_surf

        # 屏幕像素 → 视口单位坐标（-1..1），z 朝屏幕外
        lin = np.linspace(-1.0, 1.0, size, dtype=np.float32)
        X, Y = np.meshgrid(lin, lin)
        R2 = X * X + Y * Y
        inside = R2 <= 1.0
        Z = np.zeros_like(X)
        Z[inside] = np.sqrt(1.0 - R2[inside])

        # 法线 = 交点单位向量；绕 X 轴倾转（地轴），再绕 Y 轴自转
        ct, st = math.cos(self.tilt), math.sin(self.tilt)
        ny = Y * ct - Z * st
        nz = Y * st + Z * ct
        nx = X
        cs, ss = math.cos(self.spin), math.sin(self.spin)
        rx = nx * cs + nz * ss
        rz = -nx * ss + nz * cs
        ry = ny

        # 反算经纬度（rx,ry,rz 是“地固系”下的单位向量）
        lat_v = np.arcsin(np.clip(ry, -1.0, 1.0))          # -π/2..π/2
        lon_v = np.arctan2(rx, rz)                          # -π..π
        u = (lon_v + math.pi) / (2 * math.pi)
        v = 0.5 - lat_v / math.pi

        # 云层（比地表稍快一点的自转：把云采样经度整体平移）
        cloud_a = None
        if self.cloud is not None:
            u_c = np.mod(u + 0.012, 1.0)
            cloud_a = self._sample(self.cloud, u_c, v)

        # 日面颜色
        day_rgb = self._sample(self.day, np.mod(u, 1.0), v)
        if day_rgb.ndim == 2:
            day_rgb = np.repeat(day_rgb[..., None], 3, axis=-1)

        # 晨昏线：法线 · 太阳（太阳在屏幕坐标系：y 朝下，故上为负）
        sx, sy, sz = sun_dir
        ndl = rx * sx + ry * sy + rz * sz
        light = np.clip((ndl + 0.12) / 0.5, 0.0, 1.0)  # 柔化的晨昏线
        light = light * light * (3 - 2 * light)

        rgb = day_rgb * (0.04 + 1.05 * light[..., None])
        if cloud_a is not None:
            # 注意：cloud_a 和 light 都是 2D，必须同为 2D 相乘；
            # 若 light 加了 [...,None] 会广播成 (size,size,size) 的内存炸弹
            cloud_lit = cloud_a * (0.08 + 1.1 * light)
            rgb = rgb * (1 - cloud_a[..., None] * 0.9) + cloud_lit[..., None] * 0.9

        # 大气边缘辉光（Fresnel）：朝向观众的边缘泛蓝
        fres = np.clip(1.0 - Z, 0.0, 1.0) ** 2.2
        atmo = np.stack([fres * 0.35, fres * 0.62, fres * 1.0], axis=-1)
        rgb = rgb + atmo * (0.25 + 0.75 * light[..., None])

        rgb = np.clip(rgb, 0.0, 1.0)

        # 拼 RGBA（球外全透明，边缘 2px 抗锯齿）
        alpha = np.clip((1.0 - R2) * size * 0.5, 0.0, 1.0)
        alpha = np.where(inside | (R2 <= 1.06), alpha, 0.0)
        out = np.zeros((size, size, 4), dtype=np.uint8)
        out[..., :3] = (rgb * 255).astype(np.uint8)
        out[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)

        # numpy (H,W,4) → pygame surface（RGBA 只能走 frombytes）
        surf = pygame.image.frombytes(out.tobytes(), (size, size), "RGBA")
        self._cache_key = key
        self._cache_surf = surf
        self._latest_surf = surf    # 发布给主线程（原子引用写，永不阻塞）
        return surf


# ── fBm 分形噪声云（写实棉絮状） ─────────────────────────────────────────
def _value_noise(w, h, cells, rng):
    """双线性插值的值噪声"""
    gw = max(2, cells)
    gh = max(2, int(cells * h / w))
    grid = rng.random((gh, gw)).astype(np.float32)
    ys = np.linspace(0, gh - 1, h, dtype=np.float32)
    xs = np.linspace(0, gw - 1, w, dtype=np.float32)
    y0 = np.clip(ys.astype(np.int32), 0, gh - 2)
    x0 = np.clip(xs.astype(np.int32), 0, gw - 2)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    g00 = grid[np.ix_(y0, x0)]
    g01 = grid[np.ix_(y0, x0 + 1)]
    g10 = grid[np.ix_(y0 + 1, x0)]
    g11 = grid[np.ix_(y0 + 1, x0 + 1)]
    top = g00 * (1 - fx) + g01 * fx
    bot = g10 * (1 - fx) + g11 * fx
    return top * (1 - fy) + bot * fy


def make_cloud(w=560, h=220, seed=1, density=0.52):
    """生成一团 fBm 云：多层值噪声叠加 + 软阈值 alpha，白亮顶部带阴影"""
    rng = np.random.default_rng(seed)
    field = np.zeros((h, w), dtype=np.float32)
    amp, cells = 1.0, 3
    for _ in range(5):
        field += amp * _value_noise(w, h, cells, rng)
        amp *= 0.55
        cells = int(cells * 2.1)
    field /= field.max() + 1e-6

    # 椭圆羽化蒙版，让云边缘自然消散
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = (xx / w - 0.5) * 2
    dy = (yy / h - 0.5) * 2
    vign = np.clip(1.0 - (dx * dx + dy * dy * 1.4), 0, 1)
    a = np.clip((field - (1.0 - density)) * 3.2, 0, 1) * vign

    arr = np.zeros((h, w, 4), dtype=np.uint8)
    # 顶部受光更亮，底部略灰 → 有立体感
    shade = 0.78 + 0.30 * (1.0 - yy / h) * (0.5 + 0.5 * field)
    arr[..., 0] = np.clip(shade * 255, 0, 255)
    arr[..., 1] = np.clip(shade * 255, 0, 255)
    arr[..., 2] = np.clip(np.minimum(shade * 1.04, 1.0) * 255, 0, 255)
    arr[..., 3] = (a * 235).astype(np.uint8)
    surf = pygame.image.frombytes(arr.tobytes(), (w, h), "RGBA")
    return surf


def make_stars(n=300):
    """视差星空：三层深度、闪烁、星座阶段的 7 颗亮星"""
    stars = []
    for _ in range(n):
        depth = random.uniform(0.3, 1.0)
        stars.append({
            "x": random.uniform(0, W), "y": random.uniform(0, H),
            "r": max(1, int(random.choice([1, 1, 1, 2, 2, 3]) * depth)),
            "tw": random.uniform(0, math.tau),
            "ts": random.uniform(1.5, 4.0),
            "depth": depth,
            "big": False,
            "hx": 0.0, "hy": 0.0,
            "px": 0.0, "py": 0.0,   # 汇聚起点（星座幕补间）
        })
    for s in random.sample(stars, 7):
        s["big"] = True
        s["r"] = 5
        s["depth"] = 1.0
    return stars


def make_beam(w=300, h=760):
    """程序化光柱：横向高斯 + 纵向渐隐，金白色"""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if HAS_NP:
        xs = np.linspace(-1.0, 1.0, w, dtype=np.float32)
        ys = np.linspace(0.0, 1.0, h, dtype=np.float32)[::-1].copy()
        gx = np.exp(-3.0 * xs * xs)                      # 横向高斯
        core = np.exp(-14.0 * xs * xs)                   # 白热核心
        gy = np.clip(0.30 + ys * 0.95, 0, 1)             # 纵向渐隐
        a = np.clip(gx[None, :] * gy[:, None], 0, 1)
        r = np.clip(1.0 * a + core[None, :] * gy[:, None], 0, 1)
        g = np.clip(0.86 * a + core[None, :] * gy[:, None], 0, 1)
        b = np.clip(0.48 * a + core[None, :] * gy[:, None], 0, 1)
        arr = np.zeros((h, w, 4), dtype=np.uint8)
        arr[..., 0] = (r * 255).astype(np.uint8)
        arr[..., 1] = (g * 255).astype(np.uint8)
        arr[..., 2] = (b * 255).astype(np.uint8)
        arr[..., 3] = (a * 235).astype(np.uint8)
        surf = pygame.image.frombytes(arr.tobytes(), (w, h), "RGBA")
    else:
        cx = w // 2
        for x in range(w):
            d = abs(x - cx) / cx
            a = int(220 * math.exp(-3.0 * d * d))
            if a <= 0:
                continue
            col = (255, 250, 225) if d < 0.2 else (255, 214, 120)
            pygame.draw.line(surf, (*col, a), (x, 0), (x, h))
        for x in range(max(0, cx - 4), min(w, cx + 4)):
            pygame.draw.line(surf, (255, 255, 255, 235), (x, 0), (x, h))
    return surf


def draw_icon(surf, kind, cx, cy, s):
    """奖品小图标：基础图形现画"""
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


def kf(t, keys):
    """关键帧插值：keys = [(时间, 值), ...]，段内 smoothstep 缓动，端点连续。

    所有相机参数（地球位置/大小、遮罩、天色）都走这条时间线，
    相邻段共享端点值 → 全程无跳切。
    """
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        t0, v0 = keys[i]
        t1, v1 = keys[i + 1]
        if t0 <= t <= t1:
            p = ease_in_out((t - t0) / (t1 - t0) if t1 > t0 else 1.0)
            return v0 + (v1 - v0) * p
    return keys[-1][1]


class LotterySky:
    """连续时间线状态机：所有相机参数由 t 平滑插值，画面之间无跳切"""

    def __init__(self):
        if not pygame.get_init():   # 自包含：不依赖调用方先 pygame.init()
            pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("抽奖星空穿越 DEMO - 异想天开")
        self.world = pygame.Surface((W, H))   # 震屏期的离屏缓冲
        self.offscreen = self.world
        self.running = True

        # 真实贴图（缺失则回退程序地球）
        day, cloud = _load_texture()
        self.real_tex = day is not None
        if day is None and HAS_NP:
            day, cloud = _fallback_earth_tex()
        self.earth = Earth3D(day, cloud) if (HAS_NP and day is not None) else None
        self.fallback_earth = None if self.earth else self._make_fallback_earth()

        self.stars = make_stars()
        self._star_home = [(s["x"], s["y"]) for s in self.stars if s["big"]]
        # 亮星当前所在位置（补间用），初始 = 随机散落位
        for s in random.sample([x for x in self.stars if x["big"]], 7):
            s["px"], s["py"] = s["x"], s["y"]

        # 程序云（fBm），先生成 7 团滚动使用
        try:
            self.cloud_tex = [make_cloud(seed=100 + i,
                                         density=0.42 + 0.06 * (i % 3)) for i in range(7)]
        except Exception:
            self.cloud_tex = []
        self.clouds = []      # 实例: [贴图, x, y, 缩放, 速度, 预缩放面]

        # 上升幕的“海拔感”素材（全部程序生成，构建一次反复用）
        self.ground_surf = self._make_ground()   # 远去的大地/城市剪影
        self.birds = []        # 实例: [x, y, vx, 尺寸, 扑翼相位]
        self._sun_cache = None    # 太阳辉光面缓存
        self._sun_arm = None      # (半长, 眩光横条面) 缓存
        self._sun_arm_v = None    # (半长, 旋转后的竖条面) 缓存
        self._sea_cache = None    # (尺寸, 云海带面) 缓存
        self._ground_cache = None # (尺寸, 缓存缩放后的地面面)

        self.beam_tex = make_beam()

        # 时间线
        self.t = 0.0          # 全局时间（连续）
        self.fast_forward = 0.0  # >0 时快进（跳过键），带缓动不是硬切
        self.global_t = 0.0   # 装饰动画时钟（闪烁等）
        self.shake = 0.0
        self.flash = 0.0
        self.impact_wave = 0.0
        self.card_t = 0.0
        self._glow_cache = None      # (半径, 辉光面) 缓存
        self._beam_cache_key = None  # (尺寸, 高度, 角度) → 旋转后光柱面
        self._grad_cache = None      # (量化色键, 渐变面) 缓存
        self._hud_cache = None       # (阶段文本, 署名面) 缓存
        self.phase_changed = ""  # 触发一次性事件（震屏/闪光）的幕名

        self.prize_name = pick_prize()
        self.prize_meta = next(p for p in PRIZE_POOL if p[0] == self.prize_name)

        # 后台渲染线程：地球 numpy 渲染单次要几十~两百多 ms，若在主线程做
        # 会产生巨帧卡顿。放到后台线程后，主线程只取最新贴图，绝不等待。
        import threading
        self._earth_stop = threading.Event()
        self._earth_thread = threading.Thread(target=self._earth_render_loop,
                                              daemon=True, name="earth-render")
        self._earth_thread.start()

    def _earth_render_loop(self):
        """后台地球渲染循环：主线程通过 earth.kick() 提交 (size, spin) 需求。"""
        while not self._earth_stop.is_set():
            key = getattr(self.earth, "_latest_key", None)
            if key is None:
                time.sleep(0.004)
                continue
            size, _spin_q = key
            # 需求没变时跳过（渲染结果已缓存在 _latest_surf）
            if getattr(self.earth, "_cache_key", None) != key:
                try:
                    self.earth.render(size, self.earth._latest_sun)
                except Exception:
                    pass   # 渲染出错也不拖垮主线程（会回退到旧贴图）
                time.sleep(0.001)   # 刚画完一帧，稍让出 GIL
            else:
                time.sleep(0.003)   # 无新需求，空转等下一次 kick

    def _make_fallback_earth(self):
        """连 numpy 都没有时的平面回退球（保底可运行）"""
        r = 300
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        rng = random.Random(42)
        for i in range(r, 0, -2):
            t = i / r
            pygame.draw.circle(surf, (int(lerp(45, 18, t)), int(lerp(112, 55, t)),
                                      int(lerp(200, 135, t)), 255), (r, r), i)
        for _ in range(9):
            ang = rng.uniform(0, math.tau)
            dist = rng.uniform(0, r * 0.6)
            bx, by = r + math.cos(ang) * dist, r + math.sin(ang) * dist
            for _ in range(6):
                rr = rng.randint(r // 9, r // 4)
                ox, oy = int(bx + rng.randint(-r // 5, r // 5)), int(by + rng.randint(-r // 6, r // 6))
                if (ox - r) ** 2 + (oy - r) ** 2 < (r - rr - 6) ** 2:
                    pygame.draw.circle(surf, (70, 140, 85, 255), (ox, oy), rr)
        return surf

    def _make_ground(self):
        """上升幕开场的程序大地：草地 + 远山 + 城市天际线 + 河流。

        构建一次（1280x260 的 RGBA 面），随海拔下移/缩放/淡出，省逐帧重算。
        """
        gh = 260
        s = pygame.Surface((W, gh), pygame.SRCALPHA)
        rng = random.Random(2024)
        # 草地纵向渐变（上浅下深）
        for y in range(gh):
            k = y / (gh - 1)
            pygame.draw.line(s, lerp_col((104, 168, 96), (66, 118, 70), k),
                             (0, y), (W, y))
        # 远山剪影（一条起伏轮廓线之下的暗色带）
        ridge = [(0, gh)]
        x = 0
        while x <= W:
            ridge.append((x, 96 + int(22 * math.sin(x * 0.011)
                                      + rng.uniform(-9, 9))))
            x += 26
        ridge.append((W, gh))
        pygame.draw.polygon(s, (78, 108, 88), ridge)
        # 城市天际线（中偏右的楼群，剪影 + 亮窗）
        base_y = 140
        bx = int(W * 0.52)
        for i in range(14):
            bw = rng.randint(26, 58)
            bh = rng.randint(30, 118)
            x0 = bx + rng.randint(-230, 260)
            pygame.draw.rect(s, (62, 78, 96), (x0, base_y - bh, bw, bh))
            for wy in range(base_y - bh + 6, base_y - 4, 11):
                for wx in range(x0 + 4, x0 + bw - 4, 9):
                    if rng.random() < 0.45:
                        pygame.draw.rect(s, (255, 224, 150), (wx, wy, 3, 4))
        # 河流（蜿蜒亮带）
        riv = [(0, 200)]
        for x in range(0, W + 20, 20):
            riv.append((x, 200 + int(15 * math.sin(x * 0.017))))
        riv += [(W, gh), (0, gh)]
        pygame.draw.polygon(s, (108, 168, 212), riv)
        return s

    def _draw_ground(self):
        """大地随海拔下坠远去：位置下移、缓慢缩小、带大气雾感淡出。"""
        if self.t < 2.4:
            return
        a = ease_in_out(norm(2.9, 8.2, self.t))     # 上升进度
        if a >= 1.0:
            return
        gy = int(lerp(H * 0.70, H * 2.4, ease_in(a)))   # 加速坠出画面
        sc = lerp(1.0, 1.28, a)                          # 越近越大→透视感
        gw, gh = int(W * sc), int(260 * sc)
        key = (gw, gh)
        if self._ground_cache is None or self._ground_cache[0] != key:
            g2 = pygame.transform.smoothscale(self.ground_surf, (gw, gh))
            self._ground_cache = (key, g2)
        g2 = self._ground_cache[1]
        # 大气雾感：越远越泛蓝白（alpha 上升 = 被雾吃掉）
        g2.set_alpha(int(255 * (1 - a * 0.92)))
        self.world.blit(g2, (int(W * 0.5 - gw * 0.5), gy))

    def _draw_sun(self, dusk):
        """白昼太阳 + 眩光（随天色变暗淡出）"""
        sa = 1.0 - dusk
        if sa <= 0.03:
            return
        sx, sy = int(W * 0.19), int(H * 0.20)
        r = int(lerp(46, 22, dusk))
        # 辉光（多层圆，按半径缓存）
        if self._sun_cache is None or self._sun_cache[0] != r:
            gs = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
            for rr, al in ((r * 2.6, 26), (r * 1.7, 54), (r * 1.15, 130)):
                pygame.draw.circle(gs, (255, 246, 214, al), (r * 3, r * 3), int(rr))
            self._sun_cache = (r, gs)
        gs = self._sun_cache[1]
        gs.set_alpha(int(255 * sa))
        self.world.blit(gs, (sx - r * 3, sy - r * 3))
        pygame.draw.circle(self.world, (255, 252, 236), (sx, sy), r)
        # 眩光十字（预烘径向渐变条，缓存；避免逐帧 set_at 的慢循环）
        arm = r * 4
        if self._sun_arm is None or self._sun_arm[0] != arm:
            bar = pygame.Surface((arm * 2, 5), pygame.SRCALPHA)
            for x in range(arm * 2):
                f = 1 - abs(x - arm) / arm
                f *= f
                a2 = int(190 * f)
                pygame.draw.line(bar, (255, 248, 220, a2), (x, 0), (x, 4))
            self._sun_arm = (arm, bar)
        bar = self._sun_arm[1]
        bar.set_alpha(int(255 * sa))
        self.world.blit(bar, (sx - arm, sy - 2))
        if self._sun_arm_v is None or self._sun_arm_v[0] != arm:
            base = self._sun_arm[1]                # 未设 alpha 的原始横条
            self._sun_arm_v = (arm, pygame.transform.rotate(base, 90))
        bar2 = self._sun_arm_v[1]
        bar2.set_alpha(int(255 * sa))
        self.world.blit(bar2, (sx - bar2.get_width() // 2,
                               sy - bar2.get_height() // 2))

    def _draw_birds(self, dusk):
        """飞鸟掠过（上升早段，扑翼 + 向下掠出画面，强化“我们在升空”）"""
        if not self.birds:
            return
        col = lerp_col((48, 56, 72), (120, 132, 150), dusk * 0.7)
        for b in self.birds:
            bx, by, bs, ph = int(b[0]), int(b[1]), b[2], b[3]
            if not (-40 <= bx <= W + 40 and -40 <= by <= H + 40):
                continue
            wing = bs * (0.35 + 0.65 * abs(math.sin(ph)))   # 扑翼
            pygame.draw.lines(self.world, col, False,
                              [(bx - bs, by - wing * 0.7), (bx, by),
                               (bx + bs, by - wing * 0.7)], max(1, int(bs * 0.28)))

    def _draw_cloudsea(self, dusk):
        """高空俯瞰的云海带：上升中后期铺在画面下缘，慢慢被甩到身后。"""
        a = ease_in_out(norm(5.4, 10.2, self.t))
        if a <= 0.01 or not self.cloud_tex:
            return
        gy = int(lerp(H * 0.78, H * 1.35, a))     # 缓慢下沉出画
        gw = int(W * 1.25)
        if self._sea_cache is None or self._sea_cache[0] != gw:
            tex = self.cloud_tex[0]
            band = pygame.transform.smoothscale(tex, (gw, int(H * 0.30)))
            self._sea_cache = (gw, band)
        band = self._sea_cache[1]
        band.set_alpha(int(210 * (1 - a) * (1 - dusk * 0.55)))
        self.world.blit(band, (int(W * 0.5 - gw * 0.5), gy))

    # ── 连续时间线上的派生量 ──────────────────────────────
    def _mask_alpha(self):
        """遮罩不透明度：0→2.0s 保持全遮，2.0→2.9s 揭开（smoothstep）"""
        return 1.0 - ease_in_out(norm(2.0, 2.9, self.t))

    def _sky_dusk(self):
        """天色变暗程度：2.9→10.4s 从白天到太空黑"""
        return ease_in_out(norm(3.2, 10.4, self.t))

    def _star_alpha(self):
        return ease_in_out(norm(6.0, 10.4, self.t))

    def _alt(self):
        """上升进度（驱动镜头轻微上移/云速），全程缓入缓出"""
        return ease_in_out(norm(2.9, 10.4, self.t))

    def _dive(self):
        """俯冲进度：光柱击中地球后镜头加速扑向地面"""
        return ease_in(norm(19.6, 23.6, self.t))

    def _earth_view(self):
        """地球在屏幕上的 (cx, cy, 半径)：随上升缓慢入画，俯冲时放大扑面"""
        a = self._alt()
        d = self._dive()
        # 上升期：从右下方缓慢滑入（缓动，无突跳）
        cx = lerp(W * 0.78, W * 0.50, ease_in_out(norm(4.5, 10.4, self.t)))
        cy = lerp(H * 1.55, H * 1.02, a)
        r = lerp(H * 0.62, H * 0.72, a)
        # 太空停留期微小漂浮
        drift = math.sin(self.global_t * 0.5) * 4 * (1 - d)
        cy += drift
        # 俯冲期：快速放大扑面而来
        if d > 0:
            r = r * (1 + d * 5.5)
            cy = lerp(cy, H * 0.46, d)
            cx = lerp(cx, W * 0.5, d)
        return cx, cy, r

    def _dipper_center(self):
        """北斗七星阵列中心（屏幕坐标）"""
        return W * 0.5, H * 0.33

    def _constellation_p(self):
        """亮星汇聚进度：13.6→16.4s"""
        return ease_in_out(norm(13.6, 16.4, self.t))

    def _line_p(self):
        """连线进度：15.4→17.6s"""
        return ease_in_out(norm(15.4, 17.6, self.t))

    def _charge_p(self):
        """充能进度：17.4→18.6s"""
        return ease_in_out(norm(17.4, 18.6, self.t))

    def _beam_p(self):
        """光柱从北斗射向地球的长度进度：18.6→19.6s"""
        return ease_in_out(norm(18.6, 19.6, self.t))

    def act(self):
        return act_at(self.t if self.fast_forward <= 0 else min(self.t + self.fast_forward, TOTAL_END))

    # ── 更新 ──────────────────────────────────────────────
    def update(self, dt):
        self.global_t += dt
        # 快进：向下一幕边界平滑推进（跳过 = 加速，不是硬切）
        if self.fast_forward > 0:
            step = min(self.fast_forward, dt * 14.0)
            self.t += step
            self.fast_forward -= step
            if self.fast_forward <= 1e-6:
                # 对齐到幕边界，避免停在半路
                nxt = [ACTS[a] for a in ACT_ORDER if ACTS[a] > self.t + 1e-6]
                if nxt:
                    self.t = min(self.t, nxt[0])
                self.fast_forward = 0.0
        else:
            self.t = min(self.t + dt, TOTAL_END)

        # 一次性幕事件：震屏 / 闪光（由时间线触发，重放时会重演）
        act_now = act_at(self.t)
        if act_now != self.phase_changed:
            if act_now == "beam" and self.phase_changed != "beam":
                self.shake = 1.0
                self.flash = 0.85
                self.impact_wave = 1.0
            elif act_now == "space" and self.phase_changed in ("sky", "mask"):
                pass  # 进太空不闪光，保持连续
            self.phase_changed = act_now

        # 到达开奖时间：白光峰值后再放卡片
        if self.t >= ACTS["prize"] - 0.001 and self.card_t <= 0.0:
            self.flash = max(self.flash, 1.0)
            self.card_t = 1e-4

        self.flash = max(0.0, self.flash - dt * 1.3)
        self.shake = max(0.0, self.shake - dt * 1.6)
        self.impact_wave = max(0.0, self.impact_wave - dt * 0.55)
        if self.card_t > 0:
            self.card_t = clamp01(self.card_t + dt * 1.5)

        # 地球自转（0.032 rad/s ≈ 每分钟 3 度，慢而真实；配合 spin 量化
        # 控制完整重渲染频率——这是帧时间大头）
        if self.earth is not None:
            self.earth.spin += dt * 0.032

        # 云层：上升期自上而下掠过（镜头在上升），越到后期越快、越淡
        self._update_clouds(dt)
        self._update_birds(dt)

    def _update_birds(self, dt):
        """上升早段的飞鸟：随机掠过，向下（我们升空的相对运动）扑翼飞走"""
        if 3.0 <= self.t <= 7.2 and random.random() < dt * 1.1 and len(self.birds) < 9:
            bs = random.uniform(5, 11)
            self.birds.append([random.uniform(-40, W + 40),
                               random.uniform(-30, H * 0.5),
                               bs,
                               random.uniform(0, math.tau)])   # 相位
        alive = []
        for b in self.birds:
            b[1] += (170 + 260 * self._alt()) * dt     # 向下掠（我们升空）
            b[0] += random.uniform(-14, 14) * dt * 6   # 轻微左右摆
            b[3] += dt * random.uniform(9, 15)         # 扑翼频率
            if b[1] < H + 60:
                alive.append(b)
        self.birds = alive

    def _update_clouds(self, dt):
        a = self._alt()
        in_sky = 2.9 <= self.t <= 11.0
        if in_sky and len(self.cloud_tex) and random.random() < dt * 1.6:
            tex = random.choice(self.cloud_tex)
            sc = random.uniform(0.55, 1.35)
            # 云实例自带已缩放贴图：绘制时不必逐帧 smoothscale（上升期
            # 均帧大头）；缩放在生成时算一次，之后只做 alpha blit
            base = pygame.transform.smoothscale(
                tex, (max(2, int(tex.get_width() * sc)),
                      max(2, int(tex.get_height() * sc))))
            self.clouds.append([tex,
                                random.uniform(-tex.get_width() * 0.3, W - 60),
                                random.uniform(-180, -60),
                                sc,
                                random.uniform(260, 520) * (0.5 + a * 1.6),
                                base])
        alive = []
        for c in self.clouds:
            c[2] += c[4] * dt                       # 向下（我们向上升）
            c[3] += dt * 0.28                       # 越近越大（扑面感）
            if c[2] < H + 320 * c[3]:
                alive.append(c)
        self.clouds = alive
        if not in_sky:
            self.clouds = [c for c in self.clouds if c[2] < H]

    # ── 快捷操作 ──────────────────────────────────────────
    def skip(self):
        act = act_at(self.t)
        if act == "prize":
            self.reroll()
            return
        idx = ACT_ORDER.index(act)
        if idx + 1 < len(ACT_ORDER):
            nxt = ACTS[ACT_ORDER[idx + 1]]
            self.fast_forward = max(0.0, nxt - self.t)

    def reroll(self):
        self.prize_name = pick_prize()
        self.prize_meta = next(p for p in PRIZE_POOL if p[0] == self.prize_name)
        self.t = ACTS["constellation"] - 0.6
        self.card_t = 0.0
        self.flash = 1.0
        self.fast_forward = 0.0
        self.phase_changed = act_at(self.t)
        for (hx, hy), s in zip(self._star_home, [x for x in self.stars if x["big"]]):
            s["x"], s["y"] = hx, hy

    def replay(self):
        self.t = 0.0
        self.card_t = 0.0
        self.flash = 0.0
        self.fast_forward = 0.0
        self.phase_changed = ""
        self.clouds.clear()
        self.prize_name = pick_prize()
        self.prize_meta = next(p for p in PRIZE_POOL if p[0] == self.prize_name)
        for (hx, hy), s in zip(self._star_home, [x for x in self.stars if x["big"]]):
            s["x"], s["y"] = hx, hy

    # ── 绘制 ──────────────────────────────────────────────
    def _grad(self, top, bottom, surface=None):
        """垂直渐变：top 在上、bottom 在下。

        颜色量化到 4 级并缓存整幅渐变——dusk 缓慢变化时大部分帧直接命中，
        省掉每帧 2x2→1280x720 的 smoothscale（1.6ms/帧）。
        """
        s = surface or self.world
        key = (top[0] // 4, top[1] // 4, top[2] // 4,
               bottom[0] // 4, bottom[1] // 4, bottom[2] // 4)
        cached = self._grad_cache
        if cached is None or cached[0] != key:
            q = tuple(v * 4 for v in key[:3]), tuple(v * 4 for v in key[3:])
            h = pygame.Surface((2, 2))
            h.set_at((0, 0), q[0])
            h.set_at((1, 0), q[0])
            h.set_at((0, 1), q[1])
            h.set_at((1, 1), q[1])
            surf = pygame.transform.smoothscale(h, (W, H))
            self._grad_cache = (key, surf)
            cached = self._grad_cache
        s.blit(cached[1], (0, 0))

    def draw(self):
        # 无震屏时直接画到显示表面，省掉每帧一整屏 blit（约 2ms/帧）；
        # 每帧开头的全屏渐变会覆盖整个画面，直接画不会留残影
        direct = self.shake <= 0.001
        self.world = self.screen if direct else self.offscreen
        w = self.world
        dusk = self._sky_dusk()

        # 天空底色（白天蓝 → 太空黑，平滑插值）
        top = lerp_col((105, 168, 235), (3, 4, 14), dusk)
        bot = lerp_col((198, 228, 252), (10, 15, 38), dusk)
        self._grad(top, bot)

        # 星空（带视差上移 —— 镜头在上升）
        self._draw_stars()

        # ── 上升幕（sky）的海拔感细节：太阳/大地远去/飞鸟/云海 ──
        if 2.4 <= self.t < 10.6:
            self._draw_sun(dusk)      # 白昼太阳 + 眩光（在云后、天空前）
        self._draw_ground()           # 开场大地：下坠远去 + 大气雾感淡出
        if self.t >= 10.4 - 1.0:      # 云海铺在下缘（上升中后期）
            self._draw_cloudsea(dusk)

        # 云（遮罩后到进太空前）
        self._draw_clouds(dusk)

        # 飞鸟（上升早段，向下掠出，强化升空感）
        if 2.9 <= self.t < 7.4:
            self._draw_birds(dusk)

        # 地球（真实贴图 3D 球体 / 回退）
        self._draw_earth()

        # 北斗 + 连线 + 充能
        if self.t >= ACTS["constellation"] - 0.5:
            self._draw_constellation()

        # 光柱（北斗 → 地球）+ 俯冲速度线
        if self.t >= ACTS["beam"] - 0.001:
            self._draw_beam()

        # 遮罩（0→2.9s：深色游戏背景逐渐变浅到全白 → 揭开）
        self._draw_mask()

        # 全屏白光
        if self.flash > 0.003:
            f = pygame.Surface((W, H))
            f.fill((255, 255, 255))
            f.set_alpha(int(255 * self.flash))
            w.blit(f, (0, 0))

        # 奖品卡（白光之上，弹出更有仪式感）
        if self.card_t > 0:
            self._draw_prize_card()

        # 世界整体震屏（仅震屏期走离屏缓冲 + 偏移 blit）
        if not direct:
            self.screen.fill((0, 0, 0))
            ox = int(math.sin(self.global_t * 47) * self.shake * 9)
            oy = int(math.cos(self.global_t * 39) * self.shake * 7)
            self.screen.blit(w, (ox, oy))
        self._draw_hud()
        pygame.display.flip()

    def _draw_stars(self):
        sa = self._star_alpha()
        if sa <= 0.01:
            return
        # 星星整体随上升缓慢下移（视差），进太空后回稳
        par = (1 - self._alt()) * 40
        big_pos = self._big_star_positions()
        big_i = 0
        dive = self._dive()
        for st in self.stars:
            if st["big"]:
                x, y = big_pos[big_i]
                big_i += 1
            else:
                x = st["x"]
                y = st["y"] + par * st["depth"]
            if not (-8 <= x <= W + 8 and -8 <= y <= H + 8):
                continue
            tw = 0.55 + 0.45 * math.sin(self.global_t * st["ts"] + st["tw"])
            col = (255, 255, 255) if not st["big"] else (255, 246, 205)
            sz = max(1, int(st["r"] * tw))
            # 俯冲时星星拉出速度线
            if dive > 0.03:
                dx, dy = x - W / 2, y - H / 2
                ln = dive * 46 * st["depth"]
                if (dx * dx + dy * dy) > 1:
                    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
                    pygame.draw.line(self.world, col,
                                     (int(x), int(y)),
                                     (int(x + ux * ln), int(y + uy * ln)),
                                     1 if not st["big"] else 2)
            pygame.draw.circle(self.world, col, (int(x), int(y)), sz)
            if st["big"]:
                pygame.draw.circle(self.world, col, (int(x), int(y)), sz + 5, 1)

    def _big_star_positions(self):
        """7 颗亮星当前位置：随机散落 → 汇聚成北斗（缓动补间）"""
        p = self._constellation_p()
        cx, cy = self._dipper_center()
        out = []
        for i, s in enumerate([x for x in self.stars if x["big"]]):
            if "px" not in s:
                s["px"], s["py"] = s["x"], s["y"]
            tx = cx + DIPPER[i][0] * 300
            ty = cy + DIPPER[i][1] * 300
            # 每颗星错峰出发（延时），更自然
            pi = clamp01((p - i * 0.055) / (1 - 0.055 * 6))
            out.append((lerp(s["px"], tx, pi), lerp(s["py"], ty, pi)))
        return out

    def _draw_clouds(self, dusk):
        if not self.clouds:
            return
        fade = 1.0 - ease_in_out(norm(8.6, 10.6, self.t))  # 进太空前散尽
        if fade <= 0.02:
            return
        for c in self.clouds:
            img = c[5]   # 生成时已缩放好的贴图（省掉逐帧 smoothscale）
            # 高度越高云越稀薄发灰
            a = int(235 * fade * (1 - dusk * 0.75))
            if a <= 3:
                continue
            img.set_alpha(a)
            self.world.blit(img, (int(c[1]), int(c[2])))

    def _draw_earth(self):
        t = self.t
        if t < 3.6:   # 遮罩期地球还看不见（其实就在下方，随上升入画）
            return
        cx, cy, r = self._earth_view()
        if r < 8:
            return
        reveal = ease_in_out(norm(3.6, 7.5, t))  # 从云雾/晨光中逐渐显现
        disp = int(r * 2)
        if self.earth is not None:
            # 渲染分辨率上限保帧率；再量化到 24px 档，让 spin 缓存在
            # 尺寸缓慢变化时也大量命中（性能关键）。768 上限：单次渲染
            # ~300ms，配合 0.032 rad/s 自转 + 0.01 量化 → 均摊 <10ms/帧
            px = max(64, min(disp, 768))
            px = max(64, int(px // 24) * 24)
            # 提交渲染需求（不阻塞）；拿到的可能是上一帧/低分辨率贴图，但绝不卡
            img = self.earth.kick(px)
            if img is None:   # 线程还没出第一帧（启动瞬间），先留空
                return
            src_w = img.get_width()   # 后台贴图尺寸可能略滞后于最新需求
            piece, dest = img, (int(cx - r), int(cy - r))
            if disp > src_w:
                # 俯冲期显示尺寸可达数千像素：只放大屏幕上可见的那块源图，
                # 避免整张巨图 smoothscale + 整张 blit（性能关键）
                k = disp / src_w
                sx = int((0 - (cx - r)) / k)
                sy = int((0 - (cy - r)) / k)
                src = pygame.Rect(sx, sy, int(W / k) + 2, int(H / k) + 2)
                src = src.clip(pygame.Rect(0, 0, src_w, src_w))
                if src.w > 2 and src.h > 2:
                    piece = pygame.transform.smoothscale(
                        img.subsurface(src), (int(src.w * k), int(src.h * k)))
                    dest = (int(cx - r + src.x * k), int(cy - r + src.y * k))
                else:
                    piece = None
            # 大气辉光（球体外圈柔光；球大到溢出屏幕时环已在视野外，跳过）
            if piece is not None and reveal > 0.05 and r * 1.03 < math.hypot(W, H):
                gl = self._get_glow(int(r))
                if gl is not None:
                    gl.set_alpha(int(255 * reveal))
                    self.world.blit(gl, (int(cx) - gl.get_width() // 2,
                                         int(cy) - gl.get_height() // 2))
        else:
            if disp != self.fallback_earth.get_width():
                piece = pygame.transform.smoothscale(self.fallback_earth, (disp, disp))
            else:
                piece = self.fallback_earth
            dest = (int(cx - r), int(cy - r))
        if piece is not None:
            if reveal < 0.99:
                piece = piece.copy()
                piece.set_alpha(int(255 * reveal))
            self.world.blit(piece, dest)

        # 光柱落点冲击波（球太大时环已出视野，跳过；限制表面尺寸）
        if self.impact_wave > 0.01 and r * 1.3 < math.hypot(W, H):
            rr = min(900, int((1 - self.impact_wave) * r * 1.1) + 26)
            wv = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(wv, (255, 240, 180, int(170 * self.impact_wave)),
                               (rr, rr), rr, max(2, int(r * 0.05)))
            pygame.draw.circle(wv, (255, 255, 255, int(120 * self.impact_wave)),
                               (rr, rr), max(1, rr - 10), 3)
            self.world.blit(wv, (int(cx) - rr, int(cy) - rr))

    def _get_glow(self, r_int):
        """大气辉光按半径缓存（太空停留期半径恒定，不逐帧重建大表面）"""
        if self._glow_cache is not None and self._glow_cache[0] == r_int:
            return self._glow_cache[1]
        glow_r = int(r_int * 1.16)
        if glow_r * 2 > 1800:
            return None
        gl = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for rr, al in ((int(r_int * 1.16), 46), (int(r_int * 1.08), 70)):
            pygame.draw.circle(gl, (120, 190, 255, al), (glow_r, glow_r), rr)
        self._glow_cache = (r_int, gl)
        return gl

    def _draw_constellation(self):
        pts = [(int(x), int(y)) for x, y in self._big_star_positions()]
        lp = self._line_p()
        # 逐段连线
        n = len(pts) - 1
        shown = lp * n
        for i in range(n):
            seg = clamp01(shown - i)
            if seg <= 0:
                break
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            xh, yh = int(lerp(x1, x2, seg)), int(lerp(y1, y2, seg))
            pygame.draw.line(self.world, (255, 232, 155), (x1, y1), (xh, yh), 2)
            pygame.draw.line(self.world, (255, 255, 240), (x1, y1), (xh, yh), 1)
        # 充能光球（连线完成后中心聚能）
        cp = self._charge_p()
        if cp > 0:
            cx = sum(p[0] for p in pts) // len(pts)
            cy = sum(p[1] for p in pts) // len(pts)
            base = int(cp * 70)
            for rr, a in ((base + 30, int(70 * cp)), (int(base * 0.62) + 14, int(150 * cp)),
                          (int(base * 0.3) + 6, int(240 * cp))):
                if rr <= 0:
                    continue
                gl = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
                pygame.draw.circle(gl, (255, 250, 214, a), (rr, rr), rr)
                self.world.blit(gl, (cx - rr, cy - rr))
            # 充能脉冲环
            pr = int(cp * 130) + 20
            ring = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 240, 170, int(160 * (1 - cp) + 60)),
                               (pr, pr), pr, 2)
            self.world.blit(ring, (cx - pr, cy - pr))

    def _draw_beam(self):
        pts = [(int(x), int(y)) for x, y in self._big_star_positions()]
        sx = sum(p[0] for p in pts) // len(pts)
        sy = sum(p[1] for p in pts) // len(pts)
        # 目标 = 地球圆心方向上的球面点（镜头俯冲时地球在动，逐帧重算）
        ecx, ecy, er = self._earth_view()
        dx, dy = ecx - sx, ecy - sy
        dist = math.hypot(dx, dy) or 1
        tx = sx + dx / dist * (dist - er)   # 球面近端
        ty = sy + dy / dist * (dist - er)

        bp = self._beam_p()
        if bp <= 0.01:
            return
        # 光柱本体：从北斗射向地球，长度按 bp 生长（后段跟随俯冲拉长）
        seg_len = dist * bp
        ux, uy = dx / dist, dy / dist
        ex, ey = sx + ux * seg_len, sy + uy * seg_len
        # 旋转 + 缩放后的光柱按 (量化尺寸, 量化角度) 缓存：俯冲期逐帧重建
        # smoothscale+rotate 是均帧大头；角度/尺寸变化缓慢，量化后大量命中
        tex = self.beam_tex
        bw = int(tex.get_width() * (0.8 + self._dive() * 1.6))
        bh = max(32, int(seg_len + 40))
        ang = math.degrees(math.atan2(ux, uy))
        bkey = (max(8, bw), bh, int(ang))
        if getattr(self, "_beam_cache_key", None) == bkey:
            beam = self._beam_cache.copy()             # copy：下面 set_alpha 不污染缓存
        else:
            beam = pygame.transform.smoothscale(tex, (max(8, bw), bh))
            beam = pygame.transform.rotate(beam, ang)   # 贴图默认朝下，转到 (ux,uy)
            if bh < 2048:                               # 过大的不缓存（少见）
                self._beam_cache_key, self._beam_cache = bkey, beam
            beam = beam.copy()
        beam.set_alpha(int(235 * min(1.0, bp * 1.4)))
        # rotate 后的定位：旋转中心要落在 (sx,sy)→(ex,ey) 中点
        midx, midy = (sx + ex) / 2, (sy + ey) / 2
        self.world.blit(beam, (int(midx - beam.get_width() / 2),
                               int(midy - beam.get_height() / 2)))
        # 白热核心线
        pygame.draw.line(self.world, (255, 255, 255), (sx, sy), (int(ex), int(ey)),
                         max(2, int(6 * bp)))
        # 起点闪光
        fl = max(10, int(18 + 26 * math.sin(self.global_t * 9) + 40 * bp))
        gl = pygame.Surface((fl * 2, fl * 2), pygame.SRCALPHA)
        pygame.draw.circle(gl, (255, 250, 220, 200), (fl, fl), fl)
        self.world.blit(gl, (sx - fl, sy - fl))
        # 落点爆闪
        if bp > 0.92:
            il = int(30 + 60 * (bp - 0.92) / 0.08)
            il_s = pygame.Surface((il * 2, il * 2), pygame.SRCALPHA)
            pygame.draw.circle(il_s, (255, 255, 240, 220), (il, il), il)
            self.world.blit(il_s, (int(tx) - il, int(ty) - il))

    def _draw_mask(self):
        """0→2.9s：深色“游戏界面”遮罩逐渐变浅 → 全白 → 揭开露出天空"""
        a = self._mask_alpha()
        if a <= 0.005:
            return
        p = ease_in_out(norm(0.6, 2.2, self.t))     # 变浅进度
        # 底色：深色游戏风 → 纯白
        base = lerp_col((26, 27, 48), (255, 255, 255), p)
        m = pygame.Surface((W, H))
        m.fill(base)
        # 遮罩上的“旧界面”剪影（面板/按钮轮廓），随变浅一同淡出
        sil_a = int(200 * (1 - p))
        if sil_a > 4:
            tints = (52, 56, 92)
            for i, rect in enumerate([(60, 120, 300, 180), (400, 120, 300, 180),
                                      (740, 120, 300, 180), (60, 340, 640, 240),
                                      (740, 340, 480, 240)]):
                r = pygame.Rect(rect)
                s = pygame.Surface(r.size)
                s.fill(tints)
                s.set_alpha(sil_a)
                m.blit(s, r.topleft)
                pygame.draw.rect(m, (86, 92, 140), r, 2)
            txt = font(30).render("正在离开这个世界…", True, (255, 220, 130))
            txt.set_alpha(sil_a + 40)
            m.blit(txt, txt.get_rect(center=(W // 2, H - 140)))
        m.set_alpha(int(255 * a))
        self.world.blit(m, (0, 0))

    def _draw_prize_card(self):
        name, rarity, rcol, icon = self.prize_meta
        e = ease_out(self.card_t)
        # 卡片从白光中放大弹出（带一点回弹）
        pop = 1.0 + 0.10 * math.sin(min(self.card_t, 1.0) * math.pi) * (1 - self.card_t * 0.5)
        cw, ch = int(lerp(300, 560, e) * pop), int(lerp(180, 330, e) * pop)
        cx, cy = W // 2, H // 2 - 16
        card = pygame.Rect(cx - cw // 2, cy - ch // 2, cw, ch)

        # 卡底
        pygame.draw.rect(self.world, (26, 26, 52), card, border_radius=20)
        pygame.draw.rect(self.world, rcol, card, 4, border_radius=20)
        for i, a in ((7, 70), (13, 34)):   # 稀有度双层外发光
            pygame.draw.rect(self.world, rcol, card.inflate(i * 2, i * 2), 2, border_radius=24)

        if e > 0.3:
            a = clamp01((e - 0.3) / 0.7)
            # 稀有度徽带
            tag = font(24).render(rarity, True, (22, 22, 34))
            tag_bg = pygame.Rect(0, 0, tag.get_width() + 30, 36)
            tag_bg.center = (cx, card.y + 36)
            pygame.draw.rect(self.world, rcol, tag_bg, border_radius=18)
            self.world.blit(tag, tag.get_rect(center=tag_bg.center))
            # 图标
            icon_surf = pygame.Surface((170, 170), pygame.SRCALPHA)
            draw_icon(icon_surf, icon, 85, 85, 55)
            icon_surf.set_alpha(int(255 * a))
            self.world.blit(icon_surf, (cx - 85, card.y + 56))
            # 名称
            nm = font(34).render(name, True, (255, 255, 255))
            nm.set_alpha(int(255 * a))
            self.world.blit(nm, nm.get_rect(center=(cx, card.bottom - 78)))
            # 程序生成声明（重点）
            note = font(18).render("纯由程序生成 · Procedurally Generated", True, (178, 184, 212))
            note.set_alpha(int(235 * a))
            self.world.blit(note, note.get_rect(center=(cx, card.bottom - 34)))
        # 按钮
        if self.card_t >= 1.0:
            self._draw_button("再抽一次", cx - 155, card.bottom + 50, (80, 130, 220))
            self._draw_button("完整重放", cx + 15, card.bottom + 50, (90, 170, 110))

    def _draw_button(self, label, x, y, col):
        rect = pygame.Rect(x, y, 140, 46)
        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my)
        c = tuple(min(255, v + 40) if hover else v for v in col)
        pygame.draw.rect(self.world, c, rect, border_radius=11)
        pygame.draw.rect(self.world, (255, 255, 255), rect, 2, border_radius=11)
        t = font(22).render(label, True, (255, 255, 255))
        self.world.blit(t, t.get_rect(center=rect.center))
        return rect

    def _button_rects(self):
        cx, cy = W // 2, H // 2 - 16
        top = cy + 165 + 50
        return (pygame.Rect(cx - 155, top, 140, 46), pygame.Rect(cx + 15, top, 140, 46))

    def _draw_hud(self):
        # 静态文本（提示/署名）与阶段行都按字符串缓存，避免每帧 font.render
        cache = self._hud_cache
        if cache is None:
            cache = ({}, None, None)
        tips = "空格/点击=快进到下一幕   R=再抽   T=完整重放   ESC=退出"
        tag_s = "贴图: NASA Blue Marble(公有领域) · 其余全部程序实时生成 · by lsy123456114514"
        t = cache[1]
        if t is None:
            t = font(16).render(tips, True, (215, 220, 240))
            t.set_alpha(150)
        phase_cn = {"mask": "遮罩", "sky": "上升", "space": "太空", "constellation": "星座连线",
                    "beam": "光柱返航", "prize": "开奖"}
        phase_s = "阶段: %s   %.1fs" % (phase_cn.get(self.act(), ""), self.t)
        pt = cache[0].get(phase_s)
        if pt is None:
            pt = font(16).render(phase_s, True, (255, 220, 130))
            pt.set_alpha(170)
            if len(cache[0]) > 8:   # 防止时间戳字符串无限堆积
                cache[0].clear()
            cache[0][phase_s] = pt
        st = cache[2]
        if st is None:
            st = font(14).render(tag_s, True, (190, 196, 220))
            st.set_alpha(140)
        self._hud_cache = (cache[0], t, st)
        self.screen.blit(t, (16, H - 30))
        self.screen.blit(pt, (16, 12))
        self.screen.blit(st, (16, H - 52))

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
                    if act_at(self.t) == "prize" and self.card_t >= 1.0:
                        r1, r2 = self._button_rects()
                        if r1.collidepoint(ev.pos):
                            self.reroll()
                        elif r2.collidepoint(ev.pos):
                            self.replay()
                        else:
                            self.skip()
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
