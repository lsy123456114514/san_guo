#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""超级PVP对战大厅 - 联机对战 / 世界聊天 / 本地模拟 一键直达"""

import pygame

from ASSET.game_data import logger, get_font, open_window, draw_gradient_bg, data
from ASSET import safe_exit

COLORS = {
    "bg_top": (18, 22, 40),
    "bg_bottom": (10, 12, 24),
    "panel": (32, 40, 66),
    "panel_light": (44, 54, 86),
    "gold": (255, 215, 0),
    "blue": (80, 150, 220),
    "red": (210, 90, 90),
    "green": (90, 200, 130),
    "purple": (160, 110, 220),
    "text": (235, 240, 250),
    "gray": (155, 168, 195),
    "dim": (110, 122, 148),
}


class SuperPVP:
    """大厅主界面：四个大按钮直达各玩法。"""

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.font_title = get_font(44)
        self.font_main = get_font(26)
        self.font_small = get_font(19)
        self.msg = ""
        self.msg_timer = 0
        self._buttons = []
        self._entries = [
            ("PVP联机对战", "选将双人对战，比武力与技能", COLORS["blue"], self._go_pvp),
            ("世界聊天", "全服频道，约战问路卖东西", COLORS["green"], self._go_chat),
            ("本地模拟战", "和 AI 打一场，热热手", COLORS["purple"], self._go_mock),
            ("返回", "回到上级菜单", (90, 100, 140), None),
        ]

    def _flash(self, text, secs=2.5):
        self.msg = text
        self.msg_timer = pygame.time.get_ticks() + int(secs * 1000)

    # ── 入口动作（各自 try/except，失败只提示不崩）──────
    def _go_pvp(self):
        try:
            from ASSET.pvp_p2p import main as pvp_main
            pygame.event.clear()
            pvp_main()
        except Exception as e:
            logger.info("PVP联机打开失败：%s", e)
            self._flash("PVP联机一时没能打开，详情见日志")

    def _go_chat(self):
        try:
            from ASSET.world_chat import main as chat_main
            pygame.event.clear()
            chat_main(self.screen)
        except Exception as e:
            logger.info("世界聊天打开失败：%s", e)
            self._flash("世界聊天一时没能打开，详情见日志")

    def _go_mock(self):
        """本地模拟战：简单回合制数值对撞，不依赖网络。"""
        try:
            power = int(data.get("player_power", 1000))
            foe = max(200, int(power * 0.9))
            me, enemy = power, foe
            round_no = 1
            log = []
            clock = pygame.time.Clock()
            running = True
            while running:
                draw_gradient_bg(self.screen, (24, 20, 44), (12, 10, 24))
                title = self.font_title.render("本地模拟战", True, COLORS["gold"])
                self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 30))

                hp_w = min(420, self.width // 2 - 40)
                for i, (name, cur, mx, color) in enumerate([
                        ("我方", me, power, COLORS["green"]),
                        ("敌方", enemy, foe, COLORS["red"])]):
                    x = 40 + i * (hp_w + 40)
                    bar = pygame.Rect(x, 100, hp_w, 26)
                    pygame.draw.rect(self.screen, COLORS["panel"], bar, border_radius=8)
                    ratio = max(0.0, cur / max(mx, 1))
                    fill = bar.copy()
                    fill.width = int(hp_w * ratio)
                    pygame.draw.rect(self.screen, color, fill, border_radius=8)
                    t = self.font_small.render(f"{name} {max(0,cur)}/{mx}", True,
                                               COLORS["text"])
                    self.screen.blit(t, (x, 132))

                y = 190
                for line in log[-12:]:
                    s = self.font_small.render(line, True, COLORS["gray"])
                    self.screen.blit(s, (60, y))
                    y += 26

                btn = pygame.Rect(self.width // 2 - 110, self.height - 86, 220, 52)
                hover = btn.collidepoint(pygame.mouse.get_pos())
                pygame.draw.rect(self.screen, COLORS["blue"] if not hover
                                 else (110, 180, 240), btn, border_radius=12)
                label = "再打一场" if (me <= 0 or enemy <= 0) else \
                        f"第 {round_no} 回合 · 点击攻击"
                bt = self.font_main.render(label, True, COLORS["text"])
                self.screen.blit(bt, (btn.centerx - bt.get_width() // 2,
                                      btn.centery - bt.get_height() // 2))

                quit_hint = self.font_small.render("ESC 返回大厅", True, COLORS["dim"])
                self.screen.blit(quit_hint, (self.width - quit_hint.get_width() - 20,
                                             self.height - 36))

                pygame.display.flip()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                            and btn.collidepoint(event.pos):
                        if me <= 0 or enemy <= 0:
                            me, enemy, round_no, log = power, foe, 1, []
                            continue
                        import random
                        dmg_m = max(30, int(power * random.uniform(0.15, 0.3)))
                        dmg_e = max(20, int(foe * random.uniform(0.1, 0.25)))
                        enemy -= dmg_m
                        log.append(f"第{round_no}回合：我方打出 {dmg_m} 伤害")
                        if enemy > 0:
                            me -= dmg_e
                            log.append(f"第{round_no}回合：敌方反击 {dmg_e} 伤害")
                        round_no += 1
                        if enemy <= 0:
                            log.append("胜利！敌方被击溃")
                        elif me <= 0:
                            log.append("战败……回去练练再来")
                clock.tick(60)
            pygame.event.clear()
        except Exception as e:
            logger.info("模拟战异常：%s", e)
            self._flash("模拟战出错了，详情见日志")

    # ── 大厅绘制 ─────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            draw_gradient_bg(self.screen, COLORS["bg_top"], COLORS["bg_bottom"])

            name = data.get("player_name", "主公")
            title = self.font_title.render("超级对战大厅", True, COLORS["gold"])
            self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 40))
            sub = self.font_small.render(
                f"{name} · 战力 {data.get('player_power', 1000)}",
                True, COLORS["gray"])
            self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, 96))

            bw = min(520, self.width - 80)
            bh = 78
            gap = 18
            total = len(self._entries) * bh + (len(self._entries) - 1) * gap
            y = (self.height - total) // 2 + 10
            x = (self.width - bw) // 2
            mouse = pygame.mouse.get_pos()
            self._buttons = []

            for label, desc, color, action in self._entries:
                r = pygame.Rect(x, y, bw, bh)
                hover = r.collidepoint(mouse)
                pygame.draw.rect(self.screen,
                                 color if hover else COLORS["panel"],
                                 r, border_radius=14)
                if not hover:
                    pygame.draw.rect(self.screen, color, r, 2, border_radius=14)
                t_sur = self.font_main.render(label, True, COLORS["text"])
                self.screen.blit(t_sur, (x + 24, y + 12))
                d_sur = self.font_small.render(desc, True,
                                               COLORS["text"] if hover else COLORS["dim"])
                self.screen.blit(d_sur, (x + 24, y + 46))
                self._buttons.append((r, action))
                y += bh + gap

            if self.msg and pygame.time.get_ticks() < self.msg_timer:
                tip = self.font_small.render(self.msg, True, COLORS["red"])
                self.screen.blit(tip, (20, self.height - 40))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for r, action in self._buttons:
                        if r.collidepoint(event.pos):
                            if action is None:
                                running = False
                            else:
                                action()
                            break
            clock.tick(60)
        return True


def main(screen=None):
    try:
        if not pygame.get_init():
            pygame.init()
        if screen is None:
            screen = open_window()
            pygame.display.set_caption("超级对战大厅")
        SuperPVP(screen).run()
        return True
    except Exception as e:
        logger.info("超级PVP异常: %s", e)
        return False


if __name__ == "__main__":
    main()
