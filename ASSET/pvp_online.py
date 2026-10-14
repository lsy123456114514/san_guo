#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在线PVP对战 - 对战入口大厅（转调可用的联机与聊天模块）"""

import pygame

from ASSET.game_data import logger, get_font, open_window, draw_gradient_bg, data
from ASSET import safe_exit

COLORS = {
    "bg_top": (16, 20, 38),
    "bg_bottom": (10, 12, 24),
    "panel": (30, 38, 64),
    "gold": (255, 215, 0),
    "blue": (70, 140, 210),
    "green": (90, 200, 130),
    "text": (235, 240, 250),
    "gray": (155, 168, 195),
    "dim": (110, 122, 148),
}


class PVPOnline:
    """在线对战入口：展示玩家信息 + 两个直达按钮。"""

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.font_title = get_font(42)
        self.font_main = get_font(25)
        self.font_small = get_font(19)
        self.msg = ""
        self.msg_timer = 0
        self._buttons = []

    def _flash(self, text, secs=2.5):
        self.msg = text
        self.msg_timer = pygame.time.get_ticks() + int(secs * 1000)

    def _go_pvp(self):
        try:
            from ASSET.pvp_p2p import main as pvp_main
            pygame.event.clear()
            pvp_main()
        except Exception as e:
            logger.info("PVP联机打开失败：%s", e)
            self._flash("对战模块一时没能打开，详情见日志")

    def _go_chat(self):
        try:
            from ASSET.world_chat import main as chat_main
            pygame.event.clear()
            chat_main(self.screen)
        except Exception as e:
            logger.info("世界聊天打开失败：%s", e)
            self._flash("聊天模块一时没能打开，详情见日志")

    def run(self):
        clock = pygame.time.Clock()
        running = True
        entries = [
            ("进入对战房间", "选将双人对战，胜者涨排行分", COLORS["blue"], self._go_pvp),
            ("去世界聊天约人", "先喊一嗓子，再拉人进房间", COLORS["green"], self._go_chat),
            ("返回", "", (90, 100, 140), None),
        ]
        while running:
            draw_gradient_bg(self.screen, COLORS["bg_top"], COLORS["bg_bottom"])

            title = self.font_title.render("在线PVP对战", True, COLORS["gold"])
            self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 48))

            name = data.get("player_name", "主公")
            info = (f"主公 {name} · 等级 {data.get('player_level', 1)}"
                    f" · 战力 {data.get('player_power', 1000)}")
            i_sur = self.font_small.render(info, True, COLORS["gray"])
            self.screen.blit(i_sur, (self.width // 2 - i_sur.get_width() // 2, 108))

            bw = min(480, self.width - 80)
            bh = 84
            gap = 22
            total = len(entries) * bh + (len(entries) - 1) * gap
            y = (self.height - total) // 2 + 16
            x = (self.width - bw) // 2
            mouse = pygame.mouse.get_pos()
            self._buttons = []

            for label, desc, color, action in entries:
                r = pygame.Rect(x, y, bw, bh)
                hover = r.collidepoint(mouse)
                pygame.draw.rect(self.screen, color if hover else COLORS["panel"],
                                 r, border_radius=14)
                if not hover:
                    pygame.draw.rect(self.screen, color, r, 2, border_radius=14)
                t_sur = self.font_main.render(label, True, COLORS["text"])
                self.screen.blit(t_sur, (x + 26, y + 14))
                if desc:
                    d_sur = self.font_small.render(desc, True,
                                                   COLORS["text"] if hover
                                                   else COLORS["dim"])
                    self.screen.blit(d_sur, (x + 26, y + 50))
                self._buttons.append((r, action))
                y += bh + gap

            if self.msg and pygame.time.get_ticks() < self.msg_timer:
                tip = self.font_small.render(self.msg, True, (230, 120, 120))
                self.screen.blit(tip, (20, self.height - 40))

            hint = self.font_small.render("ESC 返回", True, COLORS["dim"])
            self.screen.blit(hint, (self.width - hint.get_width() - 20,
                                    self.height - 40))
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
            pygame.display.set_caption("在线PVP对战")
        PVPOnline(screen).run()
        return True
    except Exception as e:
        logger.info("在线PVP模块异常：%s", e)
        return False


if __name__ == "__main__":
    main()
