#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""领土争霸 - 占领州郡、升级城池、收取资源产出"""

import time
import pygame

from ASSET.game_data import (
    data, save, logger, get_font, open_window, draw_gradient_bg,
)
from ASSET.strategy_map_system import TerritoryManager
from ASSET import safe_exit

COLORS = {
    "bg_top": (22, 26, 40),
    "bg_bottom": (12, 14, 26),
    "panel": (30, 36, 58),
    "panel_light": (40, 48, 76),
    "panel_sel": (54, 66, 104),
    "gold": (255, 215, 0),
    "green": (90, 200, 130),
    "red": (220, 100, 100),
    "blue": (90, 150, 220),
    "text": (235, 240, 250),
    "gray": (155, 168, 195),
    "dim": (110, 122, 148),
    "divider": (60, 70, 100),
}

TYPE_NAME = {
    "city": "城池", "mine": "矿场", "farm": "农田",
    "forest": "林场", "port": "港口",
}
TYPE_COLOR = {
    "city": (220, 170, 90), "mine": (180, 180, 200), "farm": (120, 200, 120),
    "forest": (90, 170, 110), "port": (100, 170, 220),
}


def _fmt_prod(d):
    return "、".join(f"{k}{v}" for k, v in d.items())


class TerritoryWar:
    """领土主界面：顶部国力 / 左列表 / 右详情与操作。"""

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.sys = TerritoryManager()
        self.sel = 0
        self.scroll = 0
        self.msg = ""
        self.msg_timer = 0
        self.font_title = get_font(38)
        self.font_main = get_font(23)
        self.font_small = get_font(18)

    # ── 数据 ─────────────────────────────────────────
    def _all(self):
        return self.sys.get_all_territories()

    def _flash(self, text, secs=2.4):
        self.msg = text
        self.msg_timer = pygame.time.get_ticks() + int(secs * 1000)

    def _player_power(self):
        return int(data.get("player_power", 1000))

    # ── 布局 ─────────────────────────────────────────
    def _layout(self):
        pad = 16
        top = 96
        bottom = self.height - 56
        list_w = int(self.width * 0.44)
        return {
            "list": pygame.Rect(pad, top, list_w, bottom - top),
            "detail": pygame.Rect(pad + list_w + 14, top,
                                  self.width - pad * 2 - list_w - 14, bottom - top),
        }

    def _row_h(self):
        return 60

    def _visible_rows(self, L):
        return max(1, (L["list"].height - 8) // self._row_h())

    def _clamp(self, items):
        vis = self._visible_rows(self._layout())
        if not items:
            self.sel = 0
            self.scroll = 0
            return
        self.sel = max(0, min(self.sel, len(items) - 1))
        if self.sel < self.scroll:
            self.scroll = self.sel
        if self.sel >= self.scroll + vis:
            self.scroll = self.sel - vis + 1
        self.scroll = max(0, min(self.scroll, max(0, len(items) - vis)))

    # ── 绘制 ─────────────────────────────────────────
    def draw(self, L, items):
        draw_gradient_bg(self.screen, COLORS["bg_top"], COLORS["bg_bottom"])

        owned = self.sys.get_owned_territories()
        power = self.sys.get_total_power()
        prod = self.sys.get_production_rate()

        title = self.font_title.render("领土争霸", True, COLORS["gold"])
        self.screen.blit(title, (16, 12))
        stats = (f"已占 {len(owned)}/{len(items)} · 总战力 {power}"
                 f" · 我方战力 {self._player_power()}")
        s_sur = self.font_small.render(stats, True, COLORS["gray"])
        self.screen.blit(s_sur, (16 + title.get_width() + 16, 26))

        prod_txt = "产出/轮：" + (_fmt_prod(prod) if prod else "暂无领土产出")
        p_sur = self.font_small.render(prod_txt, True, COLORS["green"] if prod
                                       else COLORS["dim"])
        self.screen.blit(p_sur, (16, 62))

        collect_btn = pygame.Rect(self.width - 130, 18, 114, 40)
        hover = collect_btn.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, COLORS["green"] if not hover
                         else (120, 220, 150), collect_btn, border_radius=10)
        t = self.font_main.render("收取产出", True, (16, 34, 20))
        self.screen.blit(t, (collect_btn.centerx - t.get_width() // 2,
                             collect_btn.centery - t.get_height() // 2))
        self._collect_rect = collect_btn

        self._draw_list(L["list"], items)
        self._draw_detail(L["detail"], items)

        if self.msg and pygame.time.get_ticks() < self.msg_timer:
            tip = self.font_small.render(self.msg, True, COLORS["green"])
            self.screen.blit(tip, (16, self.height - 34))
        hint = self.font_small.render(
            "上下键/滚轮 选择 · 右侧操作 · ESC 返回", True, COLORS["dim"])
        self.screen.blit(hint, (self.width - hint.get_width() - 16, self.height - 34))

    def _draw_list(self, rect, items):
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=12)
        inner = rect.inflate(-8, -8)
        clip = self.screen.subsurface(inner)
        row_h = self._row_h()
        vis = self._visible_rows(self._layout())

        for i in range(vis):
            idx = self.scroll + i
            if idx >= len(items):
                break
            t = items[idx]
            y = 2 + i * row_h
            r = pygame.Rect(0, y, inner.width, row_h - 6)
            selected = (idx == self.sel)
            pygame.draw.rect(clip, COLORS["panel_sel"] if selected
                             else COLORS["panel_light"], r, border_radius=8)
            if selected:
                pygame.draw.rect(clip, COLORS["gold"], r, 2, border_radius=8)

            tc = TYPE_COLOR.get(t["type"], COLORS["gray"])
            pygame.draw.rect(clip, tc, (10, r.centery - 9, 18, 18), border_radius=4)

            n_sur = self.font_main.render(t["name"], True,
                                          COLORS["text"] if t["owned"] else COLORS["gray"])
            clip.blit(n_sur, (38, r.y + 6))

            sub = TYPE_NAME.get(t["type"], t["type"])
            if t["owned"]:
                sub += f" · Lv.{t['level']} · 驻军{t['garrison']}"
            else:
                sub += f" · 防御{t['defense']}"
            s_sur = self.font_small.render(sub, True, COLORS["dim"])
            clip.blit(s_sur, (38, r.y + 32))

            flag = "我方" if t["owned"] else "中立"
            f_color = COLORS["green"] if t["owned"] else COLORS["dim"]
            f_sur = self.font_small.render(flag, True, f_color)
            clip.blit(f_sur, (r.width - f_sur.get_width() - 10,
                              r.centery - f_sur.get_height() // 2))
        del clip

    def _draw_detail(self, rect, items):
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=12)
        if not items:
            return
        t = items[self.sel]
        pad = 16
        x, y = rect.x + pad, rect.y + pad

        rc = TYPE_COLOR.get(t["type"], COLORS["gray"])
        badge = pygame.Rect(x, y + 4, 34, 34)
        pygame.draw.rect(self.screen, rc, badge, border_radius=8)
        short = TYPE_NAME.get(t["type"], "?")
        b_sur = self.font_small.render(short[:2], True, (20, 24, 36))
        self.screen.blit(b_sur, (badge.centerx - b_sur.get_width() // 2,
                                 badge.centery - b_sur.get_height() // 2))

        n_sur = self.font_title.render(t["name"], True, COLORS["text"])
        self.screen.blit(n_sur, (x + 46, y))
        tag = "我方领土" if t["owned"] else "中立"
        g_sur = self.font_small.render(tag, True,
                                       COLORS["green"] if t["owned"] else COLORS["dim"])
        self.screen.blit(g_sur, (x + 46 + n_sur.get_width() + 12, y + 10))
        y += 48
        pygame.draw.line(self.screen, COLORS["divider"], (x, y), (rect.right - pad, y))
        y += 12

        rows = [
            ("类型", TYPE_NAME.get(t["type"], t["type"])),
            ("防御", str(t["defense"])),
            ("产出", _fmt_prod(t["base_production"])),
        ]
        if t["owned"]:
            rows += [("等级", f"Lv.{t['level']}（满级10）"),
                     ("驻军", str(t["garrison"]))]
        for label, val in rows:
            l_sur = self.font_small.render(label, True, COLORS["dim"])
            self.screen.blit(l_sur, (x, y))
            v_sur = self.font_small.render(val, True, COLORS["text"])
            self.screen.blit(v_sur, (x + 64, y))
            y += v_sur.get_height() + 10

        y += 8
        self._action_rects = []
        if not t["owned"]:
            self._draw_action(x, y, rect.width - pad * 2,
                              "占领（需战力 %d）" % t["defense"],
                              COLORS["blue"], "occupy" if self._player_power()
                              >= t["defense"] else None)
        else:
            self._draw_action(x, y, rect.width - pad * 2, "升级（消耗元宝+粮食）",
                              COLORS["gold"], "upgrade" if t["level"] < 10 else None)
            self._draw_action(x, y + 52, rect.width - pad * 2, "增援驻军 +500",
                              COLORS["green"], "reinforce")

    def _draw_action(self, x, y, w, label, color, action):
        r = pygame.Rect(x, y, w, 44)
        enabled = action is not None
        base = color if enabled else (70, 76, 96)
        mouse = pygame.mouse.get_pos()
        if enabled and r.collidepoint(mouse):
            base = tuple(min(255, c + 30) for c in base)
        pygame.draw.rect(self.screen, base, r, border_radius=10)
        t_sur = self.font_main.render(label, True, COLORS["text"] if enabled
                                      else COLORS["dim"])
        self.screen.blit(t_sur, (r.centerx - t_sur.get_width() // 2,
                                 r.centery - t_sur.get_height() // 2))
        if enabled:
            self._action_rects.append((r, action))

    # ── 操作 ─────────────────────────────────────────
    def _do_action(self, action, items):
        t = items[self.sel]
        if action == "occupy":
            ok, res = self.sys.occupy_territory(t["id"], self._player_power())
        elif action == "upgrade":
            ok, res = self.sys.upgrade_territory(t["id"])
        elif action == "reinforce":
            ok, res = self.sys.reinforce_garrison(t["id"], 500)
        else:
            return
        self._flash(str(res) if not ok else str(res))
        # 占领/升级后刷新内部缓存
        self.sys = TerritoryManager()

    def _collect(self):
        ok, res = self.sys.collect_resources()
        self._flash(str(res))
        if ok:
            self.sys = TerritoryManager()

    # ── 主循环 ───────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            L = self._layout()
            items = self._all()
            self._clamp(items)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.sel = max(0, self.sel - 1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.sel = min(max(0, len(items) - 1), self.sel + 1)
                    elif event.key == pygame.K_RETURN and items:
                        t = items[self.sel]
                        self._do_action("occupy" if not t["owned"] else "upgrade",
                                        items)
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll = max(0, min(self.scroll - event.y,
                                             max(0, len(items) - self._visible_rows(L))))
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    hit = False
                    if getattr(self, "_collect_rect", None) and \
                            self._collect_rect.collidepoint(event.pos):
                        hit = True
                        self._collect()
                    if not hit:
                        for r, action in getattr(self, "_action_rects", []):
                            if r.collidepoint(event.pos):
                                hit = True
                                self._do_action(action, items)
                                break
                    if not hit and L["list"].collidepoint(event.pos):
                        i = (event.pos[1] - L["list"].y - 2) // self._row_h()
                        idx = self.scroll + i
                        if 0 <= idx < len(items):
                            self.sel = idx

            items = self._all()  # 操作后重取
            self.draw(L, items)
            pygame.display.flip()
            clock.tick(60)

        return True


def main():
    try:
        if not pygame.get_init():
            pygame.init()
        screen = open_window()
        pygame.display.set_caption("领土争霸")
        TerritoryWar(screen).run()
        safe_exit("领土争霸")
    except Exception as e:
        logger.info("领土争霸异常：%s", e)
        safe_exit("领土争霸", str(e))


if __name__ == "__main__":
    main()
