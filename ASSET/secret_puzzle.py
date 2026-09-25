#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卧龙密令 - 五层嵌套隐藏解谜彩蛋系统
=========================================

谜题链路:
  第1层 隐藏加密文件  ASSET/fonts/.sys_cache_7f3a.dat
       ↓ 5层解码 (反序→XOR→Base64→XOR→反序)
  第2层 解码提示      "水火木金土, 十息之内, 依序而行"
       ↓ 五行对应菜单项
  第3层 菜单序列触发    钓鱼→炼金→装备→商城→建筑 (10秒内)
       ↓ 打开密室
  第4层 三道谜题       三国主题谜语
       ↓ 全部答对
  第5层 最终奖励       稀有武将+海量资源+隐藏成就
"""

import os
import sys
import base64
import math
import random
import logging
import pygame
from typing import List, Tuple, Optional, Dict, Any

from ASSET.game_data import data, save, get_font, draw_gradient_bg, logger, render_text

# ══════════════════════════════════════════════════════════════
# 常量配置
# ══════════════════════════════════════════════════════════════

# 隐藏文件路径（伪装成系统缓存）
HIDDEN_FILE = os.path.join(os.path.dirname(__file__), "fonts", ".sys_cache_7f3a.dat")

# 解码密钥
KEY_1 = b"san_guo_2026"
KEY_2 = b"secret_dragon_7"
FILE_HEADER = b"CACHE_DATA_V3\x00\x01\x00\x00"

# 触发序列: 五行 → 菜单代码 (水=23钓鱼, 火=24炼金, 木=17装备, 金=6商城, 土=21建筑)
TRIGGER_SEQUENCE: List[str] = ["23", "24", "17", "6", "21"]
TRIGGER_WINDOW_MS = 10000  # 10秒内完成

# 五行颜色
ELEMENT_COLORS = {
    "水": (50, 150, 255),
    "火": (255, 80, 50),
    "木": (50, 200, 80),
    "金": (255, 215, 0),
    "土": (180, 140, 80),
}

# 三道谜题 (三国主题)
RIDDLES = [
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
        "q": "既生瑜，何生亮——说出'既生瑜'的那个人",
        "a": ["周瑜", "周公瑾"],
        "hint": "东吴大都督，赤壁之战统帅",
    },
]

# 颜色主题
COLORS = {
    "bg_dark": (10, 10, 25),
    "bg_panel": (20, 20, 45, 230),
    "gold": (255, 215, 0),
    "cyan": (0, 200, 255),
    "white": (255, 255, 255),
    "gray": (150, 150, 150),
    "red": (220, 50, 50),
    "green": (50, 200, 80),
    "purple": (180, 80, 255),
}


# ══════════════════════════════════════════════════════════════
# 解码器
# ══════════════════════════════════════════════════════════════

def decode_hidden_file() -> Optional[str]:
    """
    解码隐藏的加密文件。

    5层解码流程:
      1. 去除伪造的缓存头
      2. 反转字节序
      3. XOR(KEY_2)
      4. Base64 解码
      5. 再次反转字节序
      6. XOR(KEY_1)

    Returns:
        解码后的明文字符串, 文件不存在或解码失败返回 None
    """
    if not os.path.exists(HIDDEN_FILE):
        return None
    try:
        with open(HIDDEN_FILE, "rb") as f:
            raw = f.read()

        # Step 1: 去头
        if not raw.startswith(FILE_HEADER):
            return None
        payload = raw[len(FILE_HEADER):]

        # Step 2: 反转
        payload = payload[::-1]

        # Step 3: XOR KEY_2
        payload = bytes(payload[i] ^ KEY_2[i % len(KEY_2)] for i in range(len(payload)))

        # Step 4: Base64
        payload = base64.b64decode(payload)

        # Step 5: 反转（解掉编码时的二次反转）
        payload = payload[::-1]

        # Step 6: XOR KEY_1
        payload = bytes(payload[i] ^ KEY_1[i % len(KEY_1)] for i in range(len(payload)))

        return payload.decode("utf-8")
    except Exception as e:
        logger.debug("[卧龙密令] 解码失败: %s", e)
        return None


def get_puzzle_hint() -> Optional[str]:
    """获取解码后的提示文本（供调试/作弊用）"""
    return decode_hidden_file()


# ══════════════════════════════════════════════════════════════
# 触发检测器
# ══════════════════════════════════════════════════════════════

class TriggerDetector:
    """
    菜单序列触发检测器。

    在主菜单中按照特定顺序点击菜单项,
    在时间窗口内完成即触发秘密密室。
    """

    def __init__(self) -> None:
        self.progress: int = 0       # 当前匹配到序列的第几步
        self.last_click_ms: int = 0  # 上次点击的时间戳
        self.element_flash: List[Tuple[str, float]] = []  # 五行闪光特效

    def on_menu_click(self, code: str, now_ms: int) -> bool:
        """
        检测菜单点击是否匹配触发序列。

        Args:
            code: 被点击的菜单项代码 (如 "23")
            now_ms: 当前时间戳 (pygame.time.get_ticks())

        Returns:
            True 表示序列完成, 应该打开秘密密室
        """
        # 超时重置
        if now_ms - self.last_click_ms > TRIGGER_WINDOW_MS:
            self.progress = 0

        self.last_click_ms = now_ms

        if code == TRIGGER_SEQUENCE[self.progress]:
            self.progress += 1
            # 闪光特效
            element = ["水", "火", "木", "金", "土"][self.progress - 1]
            self.element_flash.append((element, now_ms))
            # 序列完成
            if self.progress >= len(TRIGGER_SEQUENCE):
                self.progress = 0
                return True
        else:
            # 不匹配, 从头开始 (如果当前点击恰好是第一步)
            if code == TRIGGER_SEQUENCE[0]:
                self.progress = 1
                element = "水"
                self.element_flash.append((element, now_ms))
            else:
                self.progress = 0
        return False

    def update(self, now_ms: int) -> None:
        """清理过期的闪光特效"""
        self.element_flash = [
            (e, t) for e, t in self.element_flash
            if now_ms - t < 1500
        ]

    def draw_flash(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """绘制五行闪光特效（屏幕顶部）"""
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
                # 闪光背景
                glow = pygame.Surface((44, 44), pygame.SRCALPHA)
                glow.fill((*color, min(alpha, 80)))
                surface.blit(glow, (x - 4, y - 4))
                surface.blit(txt, (x + 6, y + 6))
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════
# 秘密密室 (最终彩蛋界面)
# ══════════════════════════════════════════════════════════════

class SecretChamber:
    """
    秘密密室 — 三道谜题 + 最终奖励。

    状态机:
      intro → riddle_0 → riddle_1 → riddle_2 → reward → done
    """

    # 界面状态
    STATE_INTRO = 0
    STATE_RIDDLE = 1
    STATE_REWARD = 2
    STATE_DONE = 3

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.sw, self.sh = screen.get_size()
        self.running = True
        self.state = self.STATE_INTRO
        self.riddle_idx = 0
        self.answer_input: str = ""
        self.feedback: str = ""
        self.feedback_timer: int = 0
        self.wrong_count: int = 0
        self.particles: List[Dict[str, Any]] = []
        self.clock = pygame.time.Clock()
        self.reward_granted = False

        # 字体
        self.font_title = get_font(42)
        self.font_text = get_font(22)
        self.font_input = get_font(26)
        self.font_small = get_font(16)

    # ── 事件处理 ──────────────────────────────────────

    def handle_events(self) -> None:
        """处理键盘/鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.state == self.STATE_RIDDLE:
                    self._handle_riddle_key(event)
                elif self.state == self.STATE_REWARD:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._grant_reward()
                        self.state = self.STATE_DONE
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == self.STATE_INTRO:
                    self.state = self.STATE_RIDDLE
                    self.riddle_idx = 0
                    self.answer_input = ""
                elif self.state == self.STATE_REWARD:
                    self._grant_reward()
                    self.state = self.STATE_DONE

    def _handle_riddle_key(self, event: pygame.event.Event) -> None:
        """处理谜题输入的键盘事件"""
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

    def _check_answer(self) -> None:
        """检查谜题答案"""
        riddle = RIDDLES[self.riddle_idx]
        user = self.answer_input.strip()
        if user in riddle["a"]:
            self.feedback = "✓ 回答正确!"
            self.feedback_timer = 90
            self.answer_input = ""
            self.riddle_idx += 1
            if self.riddle_idx >= len(RIDDLES):
                self.state = self.STATE_REWARD
        else:
            self.wrong_count += 1
            self.feedback = f"✗ 不对哦... 提示: {riddle['hint']}"
            self.feedback_timer = 120
            self.answer_input = ""

    def _grant_reward(self) -> None:
        """发放最终奖励"""
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
            # 解锁隐藏成就
            data.setdefault("achievements", {})
            data["achievements"]["secret_chamber_found"] = {
                "unlocked": True,
                "name": "卧龙传人",
                "desc": "发现了隐藏的卧龙密令, 通过了三道谜题",
            }
            # 解锁隐藏武将标记
            data["secret_hero_unlocked"] = True
            save()
        except Exception as e:
            logger.error("[卧龙密令] 奖励发放失败: %s", e)

    # ── 主循环 ────────────────────────────────────────

    def run(self) -> None:
        """密室主循环"""
        while self.running:
            self.handle_events()
            self._update()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)

    def _update(self) -> None:
        """更新帧状态"""
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    def _draw(self) -> None:
        """绘制当前状态"""
        draw_gradient_bg(self.screen, COLORS["bg_dark"], (5, 5, 15))

        if self.state == self.STATE_INTRO:
            self._draw_intro()
        elif self.state == self.STATE_RIDDLE:
            self._draw_riddle()
        elif self.state == self.STATE_REWARD:
            self._draw_reward()
        elif self.state == self.STATE_DONE:
            self._draw_done()

    def _draw_intro(self) -> None:
        """绘制开场"""
        cx = self.sw // 2
        # 标题
        t = self.font_title.render("◈ 卧 龙 密 室 ◈", True, COLORS["gold"])
        self.screen.blit(t, t.get_rect(centerx=cx, y=self.sh * 0.25))
        # 分隔线
        pygame.draw.line(self.screen, COLORS["gold"],
                         (cx - 150, self.sh * 0.32), (cx + 150, self.sh * 0.32), 2)
        # 描述
        lines = [
            "你发现了隐藏在系统深处的卧龙密令。",
            "千年前，诸葛孔明留下三道谜题，",
            "唯有真正懂三国之人，方可参透。",
            "",
            "三道谜题，答对全部方得秘宝。",
            "",
            "—— 点击任意位置，开始挑战 ——",
        ]
        for i, line in enumerate(lines):
            color = COLORS["cyan"] if i == len(lines) - 1 else COLORS["white"]
            s = self.font_text.render(line, True, color)
            self.screen.blit(s, s.get_rect(centerx=cx, y=self.sh * 0.38 + i * 36))

    def _draw_riddle(self) -> None:
        """绘制谜题界面"""
        cx = self.sw // 2
        riddle = RIDDLES[self.riddle_idx]

        # 进度
        for i in range(len(RIDDLES)):
            color = COLORS["green"] if i < self.riddle_idx else (
                COLORS["gold"] if i == self.riddle_idx else COLORS["gray"]
            )
            pygame.draw.circle(self.screen, color, (cx - 30 + i * 30, 50), 10)
        pt = self.font_small.render(f"谜题 {self.riddle_idx + 1}/{len(RIDDLES)}", True, COLORS["gray"])
        self.screen.blit(pt, pt.get_rect(centerx=cx, y=68))

        # 题目
        qt = self.font_title.render(f"第 {self.riddle_idx + 1} 题", True, COLORS["gold"])
        self.screen.blit(qt, qt.get_rect(centerx=cx, y=self.sh * 0.22))

        # 问题文本 (自动换行)
        self._draw_wrapped_text(riddle["q"], cx - 280, self.sh * 0.32, 560)

        # 输入框
        box_w, box_h = 400, 50
        box_x = cx - box_w // 2
        box_y = self.sh * 0.52
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (30, 30, 60), box_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLORS["cyan"], box_rect, 2, border_radius=8)
        # 光标闪烁
        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        it = self.font_input.render(self.answer_input + cursor, True, COLORS["white"])
        self.screen.blit(it, (box_x + 12, box_y + 10))
        # 提示文字
        ph = self.font_small.render("输入答案后按回车", True, COLORS["gray"])
        self.screen.blit(ph, ph.get_rect(centerx=cx, y=box_y + box_h + 10))

        # 反馈
        if self.feedback_timer > 0 and self.feedback:
            color = COLORS["green"] if self.feedback.startswith("✓") else COLORS["red"]
            ft = self.font_text.render(self.feedback, True, color)
            self.screen.blit(ft, ft.get_rect(centerx=cx, y=box_y + box_h + 45))

        # 答错次数
        if self.wrong_count > 0:
            wt = self.font_small.render(f"已答错 {self.wrong_count} 次", True, COLORS["gray"])
            self.screen.blit(wt, (20, self.sh - 40))

    def _draw_reward(self) -> None:
        """绘制奖励界面"""
        cx = self.sw // 2

        # 粒子效果
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

        t = self.font_title.render("✦ 三题皆破 · 秘宝现世 ✦", True, COLORS["gold"])
        self.screen.blit(t, t.get_rect(centerx=cx, y=self.sh * 0.18))

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
            color = COLORS["purple"] if "成就" in line or "标记" in line else COLORS["cyan"]
            if not line:
                continue
            s = self.font_text.render(line, True, color)
            self.screen.blit(s, s.get_rect(centerx=cx, y=self.sh * 0.30 + i * 34))

        hint = self.font_text.render("点击任意位置领取奖励", True, COLORS["green"])
        # 闪烁
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            self.screen.blit(hint, hint.get_rect(centerx=cx, y=self.sh * 0.78))

    def _draw_done(self) -> None:
        """绘制完成界面"""
        cx = self.sw // 2
        t = self.font_title.render("密室已通关", True, COLORS["green"])
        self.screen.blit(t, t.get_rect(centerx=cx, y=self.sh * 0.35))
        lines = [
            "秘宝已收入囊中。",
            "卧龙之谜，就此终结。",
            "",
            "按 ESC 返回主菜单",
        ]
        for i, line in enumerate(lines):
            color = COLORS["cyan"] if "ESC" in line else COLORS["white"]
            s = self.font_text.render(line, True, color)
            self.screen.blit(s, s.get_rect(centerx=cx, y=self.sh * 0.45 + i * 34))

    def _draw_wrapped_text(self, text: str, x: int, y: int, max_w: int) -> None:
        """自动换行绘制文本"""
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
    """直接运行 (调试用): 打开秘密密室"""
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((900, 650))
    pygame.display.set_caption("卧龙密室")
    chamber = SecretChamber(screen)
    chamber.run()


if __name__ == "__main__":
    main()
