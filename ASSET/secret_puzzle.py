#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卧龙密令 — 十环嵌套隐藏解谜彩蛋系统
=========================================

完整谜题链路（每一环都藏在不起眼处）::

  第1环  暗桩线索    疑难解答里一条"玩家传闻"Q&A，点破两片残卷的存在
  第2环  隐藏残卷一  ASSET/fonts/.sys_cache_7f3a.dat
                    5层解码(反序→XOR→Base64→反序→XOR) → 五行暗语
  第3环  隐藏残卷二  ASSET/fonts/.sys_cache_b2e9.dat
                    十六进制 + 凯撒偏移三格 → 前厅钥匙与四位密锁
  第4环  键盘拼字    主菜单中默念 W-O-L-O-N-G 叩开前厅
  第5环  前厅密码锁  四位数字（孔明卒年之岁），答错有递进提示
  第6环  五行序列    10秒内依序点击 钓鱼→炼金→装备→商城→建筑
                    （须先过前厅，否则五行之力被无形之门挡住）
  第7环  八阵图      按先天八卦之序点击 乾兑离震巽坎艮坤
                    两次答错后给出卦序提示
  第8环  密室六题    三国主题文字谜题 ×6
  第9环  元谜题      回到第2环的暗语本身：五行的第五个字
  第10环 真结局      大手笔奖励 + 隐藏成就「卧龙传人」+ 真结局画面

进度持久化在 ``data['secret_puzzle']`` 中。
"""

import os
import sys
import base64
import random
import pygame
from typing import List, Tuple, Optional, Dict, Any

from ASSET.game_data import data, save, get_font, draw_gradient_bg, logger

# ══════════════════════════════════════════════════════════════
# 常量配置
# ══════════════════════════════════════════════════════════════

# 残卷一：伪装成系统缓存（5层编码）
HIDDEN_FILE = os.path.join(os.path.dirname(__file__), "fonts", ".sys_cache_7f3a.dat")
KEY_1 = b"san_guo_2026"
KEY_2 = b"secret_dragon_7"
FILE_HEADER = b"CACHE_DATA_V3\x00\x01\x00\x00"

# 残卷二：十六进制 + 凯撒偏移（1层编码）
SECOND_FILE = os.path.join(os.path.dirname(__file__), "fonts", ".sys_cache_b2e9.dat")
SECOND_HEADER = b"RAWHEX_V2:"
HEX_ALPHABET = "0123456789abcdef"
HEX_CAESAR_SHIFT = 3

# 第4环：主菜单键盘拼字
WOLONG_KEYS = "WOLONG"

# 第5环：前厅四位密锁（孔明卒于234年）
GATE_PASSWORD = 234

# 第6环：五行触发序列 — 水=23钓鱼, 火=24炼金, 木=17装备, 金=6商城, 土=21建筑
TRIGGER_SEQUENCE: List[str] = ["23", "24", "17", "6", "21"]
TRIGGER_WINDOW_MS = 10000  # 十息 = 10秒

# 五行颜色
ELEMENT_COLORS = {
    "水": (50, 150, 255),
    "火": (255, 80, 50),
    "木": (50, 200, 80),
    "金": (255, 215, 0),
    "土": (180, 140, 80),
}

# 第7环：先天八卦点击顺序
TRIGRAM_ORDER: List[str] = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
TRIGRAM_HINT = "先天八卦之序：乾☰ 兑☱ 离☲ 震☳ 巽☴ 坎☵ 艮☶ 坤☷"

# 第8环：密室六道文字谜题（三国主题）
RIDDLES: List[Dict[str, Any]] = [
    {
        "q": "草船借箭，诸葛亮借的是什么风？",
        "a": ["东风", "东南风"],
        "hint": "赤壁之战，风向助了周瑜一把",
    },
    {
        "q": "空城计中，诸葛亮在城楼上弹的是什么乐器？",
        "a": ["琴", "古琴", "瑶琴"],
        "hint": "司马懿听琴声而退兵",
    },
    {
        "q": "既生瑜，何生亮——说出「既生瑜」的那个人",
        "a": ["周瑜", "周公瑾"],
        "hint": "东吴大都督，赤壁之战统帅",
    },
    {
        "q": "上方谷火攻司马懿，天降什么浇灭了大火？",
        "a": ["大雨", "雨"],
        "hint": "谋事在人，成事在天",
    },
    {
        "q": "过五关斩六将，关羽最终投奔了谁？",
        "a": ["刘备", "刘皇叔", "大哥"],
        "hint": "桃园结义的另一位",
    },
    {
        "q": "「天下大势，分久必合」——接下半句",
        "a": ["合久必分"],
        "hint": "《三国演义》开篇第一句",
    },
]

# 第9环：元谜题（答案在第2环的暗语里）
META_RIDDLE: Dict[str, Any] = {
    "q": "残卷暗语所列『水火木金土』，依其序第五字为何？",
    "a": ["土"],
    "hint": "回到最初剥开的那句话，数一数它的末位",
}

# 界面颜色
COLORS = {
    "bg_dark": (10, 10, 25),
    "gold": (255, 215, 0),
    "cyan": (0, 200, 255),
    "white": (255, 255, 255),
    "gray": (150, 150, 150),
    "red": (220, 50, 50),
    "green": (50, 200, 80),
    "purple": (180, 80, 255),
}


# ══════════════════════════════════════════════════════════════
# 进度持久化
# ══════════════════════════════════════════════════════════════

def puzzle_flags() -> Dict[str, Any]:
    """取（或初始化）卧龙密令的进度标记字典并落盘引用。"""
    return data.setdefault("secret_puzzle", {})


# ══════════════════════════════════════════════════════════════
# 解码器（第2、3环）
# ══════════════════════════════════════════════════════════════

def decode_hidden_file() -> Optional[str]:
    """
    第2环：解码残卷一（5层编码）。

    解码流程::

      去头 → 反转 → XOR(KEY_2) → Base64 → 反转 → XOR(KEY_1)

    Returns:
        解码后的明文（五行暗语），文件缺失或失败返回 None
    """
    if not os.path.exists(HIDDEN_FILE):
        return None
    try:
        with open(HIDDEN_FILE, "rb") as f:
            raw = f.read()
        if not raw.startswith(FILE_HEADER):
            return None
        payload = raw[len(FILE_HEADER):]
        payload = payload[::-1]
        payload = bytes(payload[i] ^ KEY_2[i % len(KEY_2)] for i in range(len(payload)))
        payload = base64.b64decode(payload)
        payload = payload[::-1]
        payload = bytes(payload[i] ^ KEY_1[i % len(KEY_1)] for i in range(len(payload)))
        return payload.decode("utf-8")
    except Exception as e:
        logger.debug("[卧龙密令] 残卷一解码失败: %s", e)
        return None


def _caesar_hex(text: str, shift: int) -> str:
    """十六进制字符集上的凯撒偏移。"""
    out = []
    for ch in text:
        idx = HEX_ALPHABET.index(ch)
        out.append(HEX_ALPHABET[(idx + shift) % 16])
    return "".join(out)


def decode_second_file() -> Optional[str]:
    """
    第3环：解码残卷二（十六进制 + 凯撒偏移三格）。

    解码流程::

      去头 → 凯撒 -3 → 十六进制还原 → UTF-8

    Returns:
        解码后的明文（前厅钥匙 + 密锁提示），失败返回 None
    """
    if not os.path.exists(SECOND_FILE):
        return None
    try:
        with open(SECOND_FILE, "rb") as f:
            raw = f.read()
        if not raw.startswith(SECOND_HEADER):
            return None
        body = raw[len(SECOND_HEADER):].decode("ascii")
        unshifted = _caesar_hex(body, -HEX_CAESAR_SHIFT)
        return bytes.fromhex(unshifted).decode("utf-8")
    except Exception as e:
        logger.debug("[卧龙密令] 残卷二解码失败: %s", e)
        return None


# ══════════════════════════════════════════════════════════════
# 第4环：键盘拼字检测器
# ══════════════════════════════════════════════════════════════

class KeySequenceDetector:
    """
    主菜单键盘拼字检测器。

    在主菜单中依次敲出 W-O-L-O-N-G 即叩开前厅。
    拼错或中断自动从头计，敲对全部字母返回 True。
    """

    def __init__(self, sequence: str = WOLONG_KEYS) -> None:
        self.sequence = sequence
        self.progress = 0

    def on_key(self, event: pygame.event.Event) -> bool:
        """
        喂入一个 KEYDOWN 事件。

        Returns:
            True 表示拼字完成
        """
        if event.type != pygame.KEYDOWN:
            return False
        ch = (event.unicode or "").strip().upper()
        if not ch or not ch.isalpha():
            return False
        if ch == self.sequence[self.progress]:
            self.progress += 1
            if self.progress >= len(self.sequence):
                self.progress = 0
                return True
        else:
            # 拼错：若当前字母恰是首字母则重新起头
            self.progress = 1 if ch == self.sequence[0] else 0
        return False


# ══════════════════════════════════════════════════════════════
# 第6环：五行序列触发器
# ══════════════════════════════════════════════════════════════

class TriggerDetector:
    """
    菜单序列触发检测器（第6环）。

    十息（10秒）内按 五行之序 点击菜单项即触发，
    每步在屏幕顶端点亮对应的五行字。
    """

    def __init__(self) -> None:
        self.progress: int = 0
        self.last_click_ms: int = 0
        self.element_flash: List[Tuple[str, int]] = []

    def on_menu_click(self, code: str, now_ms: int) -> bool:
        """
        检测菜单点击是否匹配触发序列。

        Args:
            code: 被点击的菜单项代码
            now_ms: 当前时间戳 pygame.time.get_ticks()

        Returns:
            True 表示五行序列完成
        """
        if now_ms - self.last_click_ms > TRIGGER_WINDOW_MS:
            self.progress = 0
        self.last_click_ms = now_ms

        if code == TRIGGER_SEQUENCE[self.progress]:
            self.progress += 1
            element = ["水", "火", "木", "金", "土"][self.progress - 1]
            self.element_flash.append((element, now_ms))
            if self.progress >= len(TRIGGER_SEQUENCE):
                self.progress = 0
                return True
        else:
            if code == TRIGGER_SEQUENCE[0]:
                self.progress = 1
                self.element_flash.append(("水", now_ms))
            else:
                self.progress = 0
        return False

    def update(self, now_ms: int) -> None:
        """清理过期的五行闪光。"""
        self.element_flash = [
            (e, t) for e, t in self.element_flash
            if now_ms - t < 1500
        ]

    def draw_flash(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """在屏幕顶端绘制五行闪光特效。"""
        now = pygame.time.get_ticks()
        for i, (element, t) in enumerate(self.element_flash):
            age = now - t
            if age > 1500:
                continue
            alpha = 255 - int(255 * age / 1500)
            color = ELEMENT_COLORS.get(element, COLORS["gold"])
            try:
                txt = font.render(element, True, color)
                x = 40 + i * 50
                y = 10
                glow = pygame.Surface((44, 44), pygame.SRCALPHA)
                glow.fill((*color, min(alpha, 80)))
                surface.blit(glow, (x - 4, y - 4))
                surface.blit(txt, (x + 6, y + 6))
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════
# 第5环：前厅密码锁
# ══════════════════════════════════════════════════════════════

class PasswordGate:
    """
    前厅四位密锁（第5环）。

    输入四位数字，答案是孔明卒年（234）。
    答错有三级递进提示；正确则 ``gate_passed = True``。
    """

    MAX_DIGITS = 4

    # 答错后的递进提示（按错的次数取用）
    WRONG_HINTS = [
        "锁孔四位——残卷二说过，锁乃孔明卒年之岁。",
        "……再想想。孔明卒于建兴十二年。",
        "亮，字孔明，卒于公元二三四年。四位：〇二三四。",
    ]

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.sw, self.sh = screen.get_size()
        self.running = True
        self.input_text: str = ""
        self.feedback: str = ""
        self.feedback_color = COLORS["red"]
        self.wrong_count = 0
        self.unlocked = False
        self.show_success = False
        self.clock = pygame.time.Clock()
        self.font_title = get_font(38)
        self.font_text = get_font(20)
        self.font_digit = get_font(34)

    def handle_events(self) -> None:
        """处理键盘/鼠标事件。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.show_success:
                    self.running = False
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._check_password()
                else:
                    ch = event.unicode or ""
                    if ch.isdigit() and len(self.input_text) < self.MAX_DIGITS:
                        self.input_text += ch
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.show_success:
                    self.running = False

    def _check_password(self) -> None:
        """校验四位密锁。"""
        if not self.input_text:
            return
        try:
            entered = int(self.input_text)
        except ValueError:
            entered = -1
        if entered == GATE_PASSWORD:
            self.unlocked = True
            self.show_success = True
            flags = puzzle_flags()
            flags["gate_passed"] = True
            save()
            logger.info("[卧龙密令] 前厅密锁已解开")
        else:
            self.wrong_count += 1
            self.feedback = self.WRONG_HINTS[min(self.wrong_count - 1, len(self.WRONG_HINTS) - 1)]
            self.feedback_color = COLORS["red"]
            self.input_text = ""

    def run(self) -> bool:
        """运行密码锁界面，返回是否解锁。"""
        while self.running:
            self.handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        return self.unlocked

    def _draw(self) -> None:
        """绘制密码锁界面。"""
        draw_gradient_bg(self.screen, COLORS["bg_dark"], (5, 5, 15))
        cx = self.sw // 2

        title = self.font_title.render("◈ 前 厅 · 密 锁 ◈", True, COLORS["gold"])
        self.screen.blit(title, title.get_rect(centerx=cx, y=self.sh * 0.18))

        sub = self.font_text.render("四孔之锁，闻于残卷二", True, COLORS["gray"])
        self.screen.blit(sub, sub.get_rect(centerx=cx, y=self.sh * 0.18 + 52))

        if self.show_success:
            ok = self.font_title.render("锁开 · 前厅已入", True, COLORS["green"])
            self.screen.blit(ok, ok.get_rect(centerx=cx, y=self.sh * 0.42))
            tip = self.font_text.render(
                "残卷二末句犹在耳畔：「先开前厅，方行五行」", True, COLORS["cyan"])
            self.screen.blit(tip, tip.get_rect(centerx=cx, y=self.sh * 0.42 + 60))
            hint = self.font_text.render("—— 点击任意处离开 ——", True, COLORS["white"])
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                self.screen.blit(hint, hint.get_rect(centerx=cx, y=self.sh * 0.70))
            return

        # 四个数字孔位
        box_w, box_h, gap = 64, 76, 16
        total_w = self.MAX_DIGITS * box_w + (self.MAX_DIGITS - 1) * gap
        start_x = cx - total_w // 2
        box_y = self.sh * 0.38
        for i in range(self.MAX_DIGITS):
            rect = pygame.Rect(start_x + i * (box_w + gap), box_y, box_w, box_h)
            pygame.draw.rect(self.screen, (30, 30, 60), rect, border_radius=10)
            pygame.draw.rect(self.screen, COLORS["cyan"], rect, 2, border_radius=10)
            if i < len(self.input_text):
                d = self.font_digit.render(self.input_text[i], True, COLORS["white"])
                self.screen.blit(d, d.get_rect(center=rect.center))

        # 输入提示
        tip = self.font_text.render("输入四位数字，回车确认", True, COLORS["gray"])
        self.screen.blit(tip, tip.get_rect(centerx=cx, y=box_y + box_h + 24))

        # 反馈
        if self.feedback:
            ft = self.font_text.render(self.feedback, True, self.feedback_color)
            self.screen.blit(ft, ft.get_rect(centerx=cx, y=box_y + box_h + 60))

        esc = self.font_text.render("ESC 离开", True, COLORS["gray"])
        self.screen.blit(esc, (20, self.sh - 44))


# ══════════════════════════════════════════════════════════════
# 第7环：八阵图
# ══════════════════════════════════════════════════════════════

# 3×3 九宫布局（名称, 卦象符号）；中心为太极
_TRIGRAM_LAYOUT: List[List[Optional[Tuple[str, str]]]] = [
    [("乾", "☰"), ("坎", "☵"), ("艮", "☶")],
    [("巽", "☴"), None, ("震", "☳")],
    [("坤", "☷"), ("离", "☲"), ("兑", "☱")],
]


class TrigramPuzzle:
    """
    八阵图（第7环）。

    按先天八卦之序 乾→兑→离→震→巽→坎→艮→坤 点击卦位。
    答错闪红并累计，连错三次清空进度；
    错过两次后显示卦序提示。
    成功返回 True，随后进入密室。
    """

    WRONGS_FOR_HINT = 2
    WRONGS_FOR_RESET = 3

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.sw, self.sh = screen.get_size()
        self.running = True
        self.progress = 0
        self.mistakes = 0
        self.flash_name: Optional[str] = None
        self.flash_ok = False
        self.flash_until = 0
        self.solved = False
        self.clock = pygame.time.Clock()
        self.font_title = get_font(38)
        self.font_text = get_font(20)
        self.font_trigram = get_font(40)
        self.font_name = get_font(18)

        # 九宫格区域
        cell = min(self.sw, self.sh) // 5
        self.cell = cell
        gx = cx = self.sw // 2 - cell * 3 // 2
        gy = self.sh // 2 - cell * 3 // 2 + 20
        self.grid_rect = pygame.Rect(gx, gy, cell * 3, cell * 3)

    def handle_events(self) -> None:
        """处理键盘/鼠标事件。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.solved:
                    self.running = False
                    return
                self._click(event.pos)

    def _click(self, pos: Tuple[int, int]) -> None:
        """处理卦位点击。"""
        if not self.grid_rect.collidepoint(pos):
            return
        col = (pos[0] - self.grid_rect.x) // self.cell
        row = (pos[1] - self.grid_rect.y) // self.cell
        if not (0 <= row < 3 and 0 <= col < 3):
            return
        cell_data = _TRIGRAM_LAYOUT[row][col]
        if cell_data is None:
            return  # 中心太极不可点
        name = cell_data[0]

        if name == TRIGRAM_ORDER[self.progress]:
            self.flash_name, self.flash_ok = name, True
            self.flash_until = pygame.time.get_ticks() + 350
            self.progress += 1
            if self.progress >= len(TRIGRAM_ORDER):
                self.solved = True
                logger.info("[卧龙密令] 八阵图已破")
        else:
            self.flash_name, self.flash_ok = name, False
            self.flash_until = pygame.time.get_ticks() + 350
            self.mistakes += 1
            if self.mistakes % self.WRONGS_FOR_RESET == 0:
                self.progress = 0  # 连错三次，阵眼重排

    def run(self) -> bool:
        """运行八阵图，成功返回 True（随即进入密室）。"""
        while self.running:
            self.handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        if self.solved:
            # 直接级联进入密室
            chamber = SecretChamber(self.screen)
            chamber.run()
        return self.solved

    def _draw(self) -> None:
        """绘制八阵图。"""
        draw_gradient_bg(self.screen, COLORS["bg_dark"], (8, 6, 18))
        cx = self.sw // 2

        title = self.font_title.render("◈ 八 阵 图 ◈", True, COLORS["gold"])
        self.screen.blit(title, title.get_rect(centerx=cx, y=40))

        sub = self.font_text.render(
            f"定阵 {self.progress}/{len(TRIGRAM_ORDER)}　·　错 {self.mistakes}",
            True, COLORS["cyan"])
        self.screen.blit(sub, sub.get_rect(centerx=cx, y=92))

        now = pygame.time.get_ticks()
        for r in range(3):
            for c in range(3):
                rect = pygame.Rect(
                    self.grid_rect.x + c * self.cell,
                    self.grid_rect.y + r * self.cell,
                    self.cell, self.cell)
                cell_data = _TRIGRAM_LAYOUT[r][c]
                if cell_data is None:
                    # 中心太极
                    pygame.draw.rect(self.screen, (25, 20, 45), rect, border_radius=12)
                    pygame.draw.rect(self.screen, (90, 80, 140), rect, 1, border_radius=12)
                    pygame.draw.circle(self.screen, COLORS["white"],
                                       rect.center, self.cell // 6, 1)
                    pygame.draw.circle(self.screen, COLORS["white"],
                                       (rect.centerx, rect.centery - self.cell // 12),
                                       self.cell // 12)
                    pygame.draw.circle(self.screen, COLORS["bg_dark"],
                                       (rect.centerx, rect.centery + self.cell // 12),
                                       self.cell // 12, 2)
                    continue

                name, symbol = cell_data
                # 闪光反馈
                border = (70, 60, 110)
                if self.flash_name == name and now < self.flash_until:
                    border = COLORS["green"] if self.flash_ok else COLORS["red"]
                pygame.draw.rect(self.screen, (28, 24, 55), rect.inflate(-8, -8),
                                 border_radius=10)
                pygame.draw.rect(self.screen, border, rect.inflate(-8, -8), 2,
                                 border_radius=10)

                sym = self.font_trigram.render(symbol, True, COLORS["white"])
                self.screen.blit(sym, sym.get_rect(centerx=rect.centerx,
                                                    centery=rect.centery - 14))
                nm = self.font_name.render(name, True, COLORS["gold"])
                self.screen.blit(nm, nm.get_rect(centerx=rect.centerx,
                                                 centery=rect.centery + 26))

        # 卦序提示（答错两次后给出）
        if self.mistakes >= self.WRONGS_FOR_HINT:
            ht = self.font_text.render(TRIGRAM_HINT, True, COLORS["purple"])
            self.screen.blit(ht, ht.get_rect(centerx=cx, y=self.grid_rect.bottom + 26))

        if self.solved:
            overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))
            t = self.font_title.render("阵成 · 密室石门缓缓开启", True, COLORS["green"])
            self.screen.blit(t, t.get_rect(centerx=cx, y=self.sh // 2 - 30))
            tip = self.font_text.render("—— 点击继续 ——", True, COLORS["white"])
            self.screen.blit(tip, tip.get_rect(centerx=cx, y=self.sh // 2 + 24))

        esc = self.font_text.render("ESC 离开", True, COLORS["gray"])
        self.screen.blit(esc, (20, self.sh - 44))


# ══════════════════════════════════════════════════════════════
# 第8-10环：卧龙密室
# ══════════════════════════════════════════════════════════════

class SecretChamber:
    """
    卧龙密室（第8-10环）。

    状态机::

      intro → riddle×6 → meta元谜题 → reward → true_ending → done

    第8环：六道三国文字谜题；
    第9环：元谜题（答案在残卷一的暗语里）；
    第10环：真结局与最终奖励。
    """

    STATE_INTRO = 0
    STATE_RIDDLE = 1
    STATE_META = 2
    STATE_REWARD = 3
    STATE_TRUE_END = 4

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.sw, self.sh = screen.get_size()
        self.running = True
        self.state = self.STATE_INTRO
        self.riddle_idx = 0
        self.answer_input = ""
        self.feedback = ""
        self.feedback_timer = 0
        self.wrong_count = 0
        self.particles: List[Dict[str, Any]] = []
        self.clock = pygame.time.Clock()
        flags = puzzle_flags()
        self.reward_granted = bool(flags.get("reward_granted"))
        self.is_replay = bool(flags.get("completed"))

        self.font_title = get_font(42)
        self.font_text = get_font(22)
        self.font_input = get_font(26)
        self.font_small = get_font(16)

    # ── 事件处理 ──────────────────────────────────────

    def handle_events(self) -> None:
        """处理键盘/鼠标事件。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.state in (self.STATE_RIDDLE, self.STATE_META):
                    self._handle_answer_key(event)
                elif self.state == self.STATE_REWARD:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._enter_true_end()
                elif self.state == self.STATE_TRUE_END:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                        self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == self.STATE_INTRO:
                    self.state = self.STATE_RIDDLE
                    self.answer_input = ""
                elif self.state == self.STATE_REWARD:
                    self._enter_true_end()
                elif self.state == self.STATE_TRUE_END:
                    self.running = False

    def _handle_answer_key(self, event: pygame.event.Event) -> None:
        """处理谜题输入。"""
        if event.key == pygame.K_RETURN:
            self._check_answer()
        elif event.key == pygame.K_BACKSPACE:
            self.answer_input = self.answer_input[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.running = False
        else:
            ch = event.unicode
            if ch and len(self.answer_input) < 20:
                self.answer_input += ch

    @property
    def _current_riddle(self) -> Dict[str, Any]:
        """当前题目（六题之后是元谜题）。"""
        if self.state == self.STATE_META or self.riddle_idx >= len(RIDDLES):
            return META_RIDDLE
        return RIDDLES[self.riddle_idx]

    def _check_answer(self) -> None:
        """校验答案（第8环或第9环）。"""
        riddle = self._current_riddle
        user = self.answer_input.strip()
        if user in riddle["a"]:
            self.feedback = "✓ 回答正确!"
            self.feedback_timer = 90
            self.answer_input = ""
            if self.state == self.STATE_META or self.riddle_idx >= len(RIDDLES):
                self.state = self.STATE_REWARD
            else:
                self.riddle_idx += 1
                if self.riddle_idx >= len(RIDDLES):
                    # 六题尽破 → 元谜题
                    self.state = self.STATE_META
                    self.answer_input = ""
        else:
            self.wrong_count += 1
            self.feedback = f"✗ 不对哦… 提示: {riddle['hint']}"
            self.feedback_timer = 120
            self.answer_input = ""

    def _enter_true_end(self) -> None:
        """领取奖励并进入真结局（第10环）。"""
        self._grant_reward()
        self.state = self.STATE_TRUE_END

    def _grant_reward(self) -> None:
        """发放最终奖励（只发一次）。"""
        if self.reward_granted:
            return
        self.reward_granted = True
        try:
            resources = data.get("resources", {})
            resources["金元宝"] = resources.get("金元宝", 0) + 10000
            resources["木头"] = resources.get("木头", 0) + 5000
            resources["食物"] = resources.get("食物", 0) + 5000
            resources["水"] = resources.get("水", 0) + 5000
            resources["煤炭"] = resources.get("煤炭", 0) + 5000
            data.setdefault("achievements", {})
            data["achievements"]["secret_chamber_found"] = {
                "unlocked": True,
                "name": "卧龙传人",
                "desc": "发现了隐藏的卧龙密令, 通过了全部十环谜题",
            }
            data["secret_hero_unlocked"] = True
            flags = puzzle_flags()
            flags["reward_granted"] = True
            flags["completed"] = True
            flags["true_ending"] = True
            save()
            logger.info("[卧龙密令] 真结局达成，奖励已发放")
        except Exception as e:
            logger.error("[卧龙密令] 奖励发放失败: %s", e)

    # ── 主循环 ────────────────────────────────────────

    def run(self) -> None:
        """密室主循环。"""
        while self.running:
            self.handle_events()
            self._update()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)

    def _update(self) -> None:
        """帧更新。"""
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    def _draw(self) -> None:
        """按状态绘制。"""
        draw_gradient_bg(self.screen, COLORS["bg_dark"], (5, 5, 15))
        if self.state == self.STATE_INTRO:
            self._draw_intro()
        elif self.state == self.STATE_RIDDLE:
            self._draw_riddle(self._current_riddle, f"谜题 {self.riddle_idx + 1}/{len(RIDDLES)}",
                              self.riddle_idx)
        elif self.state == self.STATE_META:
            self._draw_riddle(META_RIDDLE, "元谜题 · 回望来路", -1)
        elif self.state == self.STATE_REWARD:
            self._draw_reward()
        elif self.state == self.STATE_TRUE_END:
            self._draw_true_end()

    def _draw_intro(self) -> None:
        """第8环开场。"""
        cx = self.sw // 2
        t = self.font_title.render("◈ 卧 龙 密 室 ◈", True, COLORS["gold"])
        self.screen.blit(t, t.get_rect(centerx=cx, y=self.sh * 0.22))
        pygame.draw.line(self.screen, COLORS["gold"],
                         (cx - 150, self.sh * 0.29), (cx + 150, self.sh * 0.29), 2)
        lines = [
            "你破了八阵图，推开了这扇从没画在菜单里的门。",
            "孔明于此留题七道——六道叙三国旧事，",
            "一道回望你来时路上的暗语。",
            "",
            "七题尽答，方见真结局。",
            "",
            "—— 点击任意位置，开始挑战 ——",
        ]
        for i, line in enumerate(lines):
            color = COLORS["cyan"] if i == len(lines) - 1 else COLORS["white"]
            s = self.font_text.render(line, True, color)
            self.screen.blit(s, s.get_rect(centerx=cx, y=self.sh * 0.34 + i * 36))

    def _draw_riddle(self, riddle: Dict[str, Any], label: str, idx: int) -> None:
        """绘制谜题界面（第8/9环通用）。"""
        cx = self.sw // 2

        # 进度点
        for i in range(len(RIDDLES)):
            color = COLORS["green"] if i < self.riddle_idx else (
                COLORS["gold"] if i == self.riddle_idx and self.state == self.STATE_RIDDLE
                else COLORS["gray"])
            pygame.draw.circle(self.screen, color, (cx - 75 + i * 30, 46), 9)
        pt = self.font_small.render(label, True, COLORS["gray"])
        self.screen.blit(pt, pt.get_rect(centerx=cx, y=64))

        qt = self.font_title.render(
            "元谜题" if idx < 0 else f"第 {idx + 1} 题", True, COLORS["gold"])
        self.screen.blit(qt, qt.get_rect(centerx=cx, y=self.sh * 0.20))

        self._draw_wrapped_text(riddle["q"], cx - 280, self.sh * 0.30, 560)

        # 输入框
        box_w, box_h = 400, 50
        box_x = cx - box_w // 2
        box_y = self.sh * 0.52
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (30, 30, 60), box_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLORS["cyan"], box_rect, 2, border_radius=8)
        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        it = self.font_input.render(self.answer_input + cursor, True, COLORS["white"])
        self.screen.blit(it, (box_x + 12, box_y + 10))
        ph = self.font_small.render("输入答案后按回车", True, COLORS["gray"])
        self.screen.blit(ph, ph.get_rect(centerx=cx, y=box_y + box_h + 10))

        if self.feedback_timer > 0 and self.feedback:
            color = COLORS["green"] if self.feedback.startswith("✓") else COLORS["red"]
            ft = self.font_text.render(self.feedback, True, color)
            self.screen.blit(ft, ft.get_rect(centerx=cx, y=box_y + box_h + 45))

        if self.wrong_count > 0:
            wt = self.font_small.render(f"已答错 {self.wrong_count} 次", True, COLORS["gray"])
            self.screen.blit(wt, (20, self.sh - 40))

    def _draw_reward(self) -> None:
        """第10环·奖励界面。"""
        cx = self.sw // 2
        if random.random() < 0.3:
            self.particles.append({
                "x": random.randint(0, self.sw),
                "y": self.sh + 10,
                "vy": random.uniform(-3, -6),
                "color": random.choice([COLORS["gold"], COLORS["cyan"], COLORS["purple"]]),
                "life": 120,
            })
        for p in self.particles[:]:
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)
            else:
                pygame.draw.circle(self.screen, p["color"],
                                   (int(p["x"]), int(p["y"])), 3)

        t = self.font_title.render("✦ 七题皆破 · 秘宝现世 ✦", True, COLORS["gold"])
        self.screen.blit(t, t.get_rect(centerx=cx, y=self.sh * 0.16))

        rewards = [
            "金元宝 ×10000",
            "木头 ×5000",
            "食物 ×5000",
            "水 ×5000",
            "煤炭 ×5000",
            "",
            "隐藏成就:「卧龙传人」",
            "隐藏标记: secret_hero_unlocked = True",
        ]
        for i, line in enumerate(rewards):
            if not line:
                continue
            color = COLORS["purple"] if ("成就" in line or "标记" in line) else COLORS["cyan"]
            s = self.font_text.render(line, True, color)
            self.screen.blit(s, s.get_rect(centerx=cx, y=self.sh * 0.27 + i * 34))

        if self.reward_granted and self.is_replay:
            rt = self.font_small.render("（奖励此前已领取，不重复发放）", True, COLORS["gray"])
            self.screen.blit(rt, rt.get_rect(centerx=cx, y=self.sh * 0.72))

        hint = self.font_text.render("点击或回车 · 走向真结局", True, COLORS["green"])
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            self.screen.blit(hint, hint.get_rect(centerx=cx, y=self.sh * 0.80))

    def _draw_true_end(self) -> None:
        """第10环·真结局画面。"""
        cx = self.sw // 2
        t = self.font_title.render("— 真 结 局 —", True, COLORS["purple"])
        self.screen.blit(t, t.get_rect(centerx=cx, y=self.sh * 0.24))
        pygame.draw.line(self.screen, COLORS["purple"],
                         (cx - 130, self.sh * 0.31), (cx + 130, self.sh * 0.31), 2)
        lines = [
            "残卷、前厅、五行、八阵、七题——",
            "十环相扣，皆是千年前那位卧龙的考校。",
            "",
            "「非非常人，不能得非常之宝。」",
            "",
            "秘宝已入囊中，成就已刻上石壁。",
            "此间之秘，天下知者寥寥。",
            "",
            "—— 按 ESC 或点击，返回主菜单 ——",
        ]
        for i, line in enumerate(lines):
            color = COLORS["gold"] if line.startswith("「") else COLORS["white"]
            s = self.font_text.render(line, True, color)
            self.screen.blit(s, s.get_rect(centerx=cx, y=self.sh * 0.36 + i * 34))

    def _draw_wrapped_text(self, text: str, x: int, y: int, max_w: int) -> None:
        """中文逐字换行绘制。"""
        line = ""
        for ch in text:
            test = line + ch
            if self.font_text.size(test)[0] > max_w:
                s = self.font_text.render(line, True, COLORS["white"])
                self.screen.blit(s, (x, y))
                y += 34
                line = ch
            else:
                line = test
        if line:
            s = self.font_text.render(line, True, COLORS["white"])
            self.screen.blit(s, (x, y))


# ══════════════════════════════════════════════════════════════
# 模块入口
# ══════════════════════════════════════════════════════════════

def main() -> None:
    """直接运行（调试用）：从八阵图开始走完整条链路。"""
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((900, 650))
    pygame.display.set_caption("卧龙密令")
    TrigramPuzzle(screen).run()


if __name__ == "__main__":
    main()
