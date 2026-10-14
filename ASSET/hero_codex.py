#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英雄图鉴 - 收集进度、势力筛选、图鉴奖励领取"""

import pygame

from ASSET.game_data import (
    data, save, logger, get_font, open_window, draw_gradient_bg,
)
from ASSET.hero_collection_system import HeroCollectionSystem
from ASSET import safe_exit

COLORS = {
    "bg_top": (20, 18, 40),
    "bg_bottom": (12, 10, 24),
    "panel": (30, 32, 60),
    "panel_light": (42, 46, 80),
    "panel_sel": (56, 62, 104),
    "gold": (255, 215, 0),
    "blue": (86, 140, 220),
    "green": (90, 200, 130),
    "red": (220, 100, 100),
    "text": (235, 240, 250),
    "gray": (155, 168, 195),
    "dim": (110, 122, 148),
    "divider": (60, 66, 100),
}

RARITY_COLOR = {
    "legendary": (255, 200, 60),
    "rare": (120, 170, 255),
    "common": (160, 170, 190),
}
RARITY_NAME = {
    "legendary": "传说",
    "rare": "稀有",
    "common": "普通",
}
FACTIONS = ["全部", "蜀", "魏", "吴", "群雄"]


def _wrap(font, text, max_w):
    lines, cur = [], ""
    for ch in text:
        if font.size(cur + ch)[0] > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


class HeroCodex:
    """图鉴主界面：顶部进度 / 左势力筛选+武将列表 / 右详情+奖励。"""

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.sys = HeroCollectionSystem()
        self.faction = "全部"
        self.sel_id = None
        self.scroll = 0
        self.msg = ""
        self.msg_timer = 0
        self.font_title = get_font(38)
        self.font_main = get_font(23)
        self.font_small = get_font(18)

    # ── 数据 ─────────────────────────────────────────
    def _heroes(self):
        hs = self.sys.get_all_heroes()
        if self.faction != "全部":
            hs = [h for h in hs if h["faction"] == self.faction]
        return hs

    def _selected(self):
        if self.sel_id is None:
            return None
        return next((h for h in self.sys.get_all_heroes()
                     if h["id"] == self.sel_id), None)

    def _flash(self, text, secs=2.2):
        self.msg = text
        self.msg_timer = pygame.time.get_ticks() + int(secs * 1000)

    # ── 布局 ─────────────────────────────────────────
    def _layout(self):
        pad = 16
        top = 108
        bottom = self.height - 56
        list_w = int(self.width * 0.42)
        return {
            "list": pygame.Rect(pad, top, list_w, bottom - top),
            "detail": pygame.Rect(pad + list_w + 14, top,
                                  self.width - pad * 2 - list_w - 14,
                                  int((bottom - top) * 0.58)),
            "bonus": pygame.Rect(pad + list_w + 14,
                                 top + int((bottom - top) * 0.58) + 12,
                                 self.width - pad * 2 - list_w - 14,
                                 (bottom - top) - int((bottom - top) * 0.58) - 12),
        }

    def _row_h(self):
        return 56

    def _visible_rows(self, L):
        return max(1, (L["list"].height - 76) // self._row_h())

    def _clamp(self, heroes):
        vis = self._visible_rows(self._layout())
        self.scroll = max(0, min(self.scroll, max(0, len(heroes) - vis)))

    # ── 绘制 ─────────────────────────────────────────
    def draw(self, L, heroes):
        draw_gradient_bg(self.screen, COLORS["bg_top"], COLORS["bg_bottom"])

        title = self.font_title.render("英雄图鉴", True, COLORS["gold"])
        self.screen.blit(title, (16, 14))

        got, total = self.sys.get_collected_count(), self.sys.get_total_count()
        prog = self.sys.get_collection_progress()
        bar_w = 260
        bar = pygame.Rect(16 + title.get_width() + 20, 26, bar_w, 16)
        pygame.draw.rect(self.screen, COLORS["panel"], bar, border_radius=8)
        if prog > 0:
            fill = bar.copy()
            fill.width = int(bar_w * prog / 100)
            pygame.draw.rect(self.screen, COLORS["green"], fill, border_radius=8)
        p_sur = self.font_small.render(f"{got}/{total}  ({prog}%)", True, COLORS["gray"])
        self.screen.blit(p_sur, (bar.right + 12, 22))

        self._draw_faction_bar(L)
        self._draw_list(L["list"], heroes)
        self._draw_detail(L["detail"])
        self._draw_bonus(L["bonus"])

        if self.msg and pygame.time.get_ticks() < self.msg_timer:
            tip = self.font_small.render(self.msg, True, COLORS["green"])
            self.screen.blit(tip, (16, self.height - 36))
        hint = self.font_small.render(
            "上下键/滚轮 选择 · 点击武将看详情 · ESC 返回", True, COLORS["dim"])
        self.screen.blit(hint, (self.width - hint.get_width() - 16, self.height - 36))

    def _draw_faction_bar(self, L):
        x = L["list"].x
        y = L["list"].y
        self._faction_rects = []
        mouse = pygame.mouse.get_pos()
        for name in FACTIONS:
            w = 62
            r = pygame.Rect(x, y, w, 34)
            active = (name == self.faction)
            hover = r.collidepoint(mouse)
            c = COLORS["gold"] if active else (COLORS["panel_light"] if not hover
                                               else COLORS["panel_sel"])
            pygame.draw.rect(self.screen, c, r, border_radius=8)
            t = self.font_small.render(name, True,
                                       COLORS["bg_bottom"] if active else COLORS["text"])
            self.screen.blit(t, (r.centerx - t.get_width() // 2,
                                 r.centery - t.get_height() // 2))
            self._faction_rects.append((r, name))
            x += w + 8

    def _draw_list(self, rect, heroes):
        body = pygame.Rect(rect.x, rect.y + 44, rect.width, rect.height - 44)
        pygame.draw.rect(self.screen, COLORS["panel"], body, border_radius=12)
        inner = body.inflate(-8, -8)
        clip = self.screen.subsurface(inner)

        if not heroes:
            tip = self.font_main.render("该势力暂无图鉴武将", True, COLORS["dim"])
            clip.blit(tip, (inner.width // 2 - tip.get_width() // 2,
                            inner.height // 2 - tip.get_height() // 2))
            del clip
            return

        row_h = self._row_h()
        vis = self._visible_rows(self._layout())
        for i in range(vis):
            idx = self.scroll + i
            if idx >= len(heroes):
                break
            h = heroes[idx]
            y = 2 + i * row_h
            r = pygame.Rect(0, y, inner.width, row_h - 6)
            selected = (h["id"] == self.sel_id)
            pygame.draw.rect(clip, COLORS["panel_sel"] if selected else COLORS["panel_light"],
                             r, border_radius=8)
            if selected:
                pygame.draw.rect(clip, COLORS["gold"], r, 2, border_radius=8)

            rc = RARITY_COLOR.get(h["rarity"], COLORS["gray"])
            pygame.draw.circle(clip, rc, (14, r.centery), 6)

            name = h["name"] if h["collected"] else "？？？"
            n_color = COLORS["text"] if h["collected"] else COLORS["dim"]
            n_sur = self.font_main.render(f"{name}", True, n_color)
            clip.blit(n_sur, (30, r.y + 6))

            sub = f"{h['faction']} · {RARITY_NAME.get(h['rarity'], '?')}"
            s_sur = self.font_small.render(sub, True, COLORS["gray"])
            clip.blit(s_sur, (30, r.y + 30))

            if h["collected"]:
                ok = self.font_small.render("已收集", True, COLORS["green"])
            else:
                ok = self.font_small.render("未收集", True, COLORS["dim"])
            clip.blit(ok, (r.width - ok.get_width() - 10, r.centery - ok.get_height() // 2))
        del clip

    def _draw_detail(self, rect):
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=12)
        h = self._selected()
        if not h:
            tip = self.font_main.render("点一个武将查看详情", True, COLORS["dim"])
            self.screen.blit(tip, (rect.centerx - tip.get_width() // 2,
                                   rect.centery - tip.get_height() // 2))
            return

        pad = 14
        x, y = rect.x + pad, rect.y + pad
        rc = RARITY_COLOR.get(h["rarity"], COLORS["gray"])
        name = h["name"] if h["collected"] else "？？？"
        n_sur = self.font_title.render(name, True, rc)
        self.screen.blit(n_sur, (x, y))
        tag = self.font_small.render(
            f"{h['faction']} · {RARITY_NAME.get(h['rarity'], '?')} · {h['element']}",
            True, COLORS["gray"])
        self.screen.blit(tag, (x + n_sur.get_width() + 14, y + 10))
        y += n_sur.get_height() + 10
        pygame.draw.line(self.screen, COLORS["divider"],
                         (x, y), (rect.right - pad, y))
        y += 10

        rows = [
            ("技能", h["skill"]),
            ("简介", h["description"] if h["collected"] else "尚未收集，去招募里抽吧"),
        ]
        for label, val in rows:
            l_sur = self.font_small.render(label, True, COLORS["dim"])
            self.screen.blit(l_sur, (x, y))
            for line in _wrap(self.font_small, val, rect.width - pad * 2 - 60)[:3]:
                v_sur = self.font_small.render(line, True, COLORS["text"])
                self.screen.blit(v_sur, (x + 56, y))
                y += v_sur.get_height() + 4
            y += 6

    def _draw_bonus(self, rect):
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=12)
        head = self.font_small.render("图鉴奖励", True, COLORS["gold"])
        self.screen.blit(head, (rect.x + 12, rect.y + 8))

        bonuses = self.sys.get_all_bonuses()
        mouse = pygame.mouse.get_pos()
        y = rect.y + 34
        self._bonus_rects = []
        row_h = 34
        for b in bonuses[:max(1, (rect.height - 40) // row_h)]:
            r = pygame.Rect(rect.x + 8, y, rect.width - 16, row_h - 4)
            if b["claimed"]:
                c = COLORS["panel_light"]
            elif b["unlocked"]:
                c = COLORS["panel_sel"]
            else:
                c = (26, 28, 50)
            pygame.draw.rect(self.screen, c, r, border_radius=6)

            status = "已领" if b["claimed"] else ("可领" if b["unlocked"] else f"{b['current']}/{b['target']}")
            s_color = COLORS["dim"] if not b["unlocked"] else COLORS["green"]
            name_sur = self.font_small.render(f"{b['name']}  {status}", True, s_color)
            self.screen.blit(name_sur, (r.x + 8, r.centery - name_sur.get_height() // 2))

            if b["unlocked"] and not b["claimed"]:
                btn = pygame.Rect(r.right - 74, r.y + 3, 66, r.height - 6)
                hover = btn.collidepoint(mouse)
                pygame.draw.rect(self.screen, COLORS["green"] if not hover
                                 else (120, 220, 150), btn, border_radius=6)
                t = self.font_small.render("领取", True, (18, 30, 20))
                self.screen.blit(t, (btn.centerx - t.get_width() // 2,
                                     btn.centery - t.get_height() // 2))
                self._bonus_rects.append((btn, b["id"]))
            y += row_h

    # ── 主循环 ───────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            L = self._layout()
            heroes = self._heroes()
            self._clamp(heroes)
            if self.sel_id is None and heroes:
                self.sel_id = heroes[0]["id"]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if heroes:
                            i = next((k for k, h in enumerate(heroes)
                                      if h["id"] == self.sel_id), 0)
                            self.sel_id = heroes[max(0, i - 1)]["id"]
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if heroes:
                            i = next((k for k, h in enumerate(heroes)
                                      if h["id"] == self.sel_id), 0)
                            self.sel_id = heroes[min(len(heroes) - 1, i + 1)]["id"]
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll = max(0, min(self.scroll - event.y,
                                             max(0, len(heroes) - self._visible_rows(L))))
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    hit = False
                    for r, bid in getattr(self, "_bonus_rects", []):
                        if r.collidepoint(event.pos):
                            hit = True
                            ok, res = self.sys.claim_bonus_reward(bid)
                            self._flash(f"领取成功：{res}" if ok else str(res))
                            break
                    if hit:
                        continue
                    for r, name in getattr(self, "_faction_rects", []):
                        if r.collidepoint(event.pos):
                            hit = True
                            self.faction = name
                            self.scroll = 0
                            hs = self._heroes()
                            self.sel_id = hs[0]["id"] if hs else None
                            break
                    if hit:
                        continue
                    body = pygame.Rect(L["list"].x, L["list"].y + 44,
                                       L["list"].width, L["list"].height - 44)
                    if body.collidepoint(event.pos):
                        i = (event.pos[1] - body.y - 2) // self._row_h()
                        idx = self.scroll + i
                        if 0 <= idx < len(heroes):
                            self.sel_id = heroes[idx]["id"]

            self.draw(L, heroes)
            pygame.display.flip()
            clock.tick(60)

        return True


def main():
    try:
        if not pygame.get_init():
            pygame.init()
        screen = open_window()
        pygame.display.set_caption("英雄图鉴")
        HeroCodex(screen).run()
        safe_exit("英雄图鉴")
    except Exception as e:
        logger.info("英雄图鉴异常：%s", e)
        safe_exit("英雄图鉴", str(e))


if __name__ == "__main__":
    main()
