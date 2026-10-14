#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""邮件中心 - 收件箱、附件领取、已读与删除"""

import time
import pygame

from ASSET.game_data import (
    data, save, logger, get_font, open_window, draw_gradient_bg,
)
from ASSET.gameplay_systems import MailSystem
from ASSET import safe_exit

COLORS = {
    "bg_dark": (15, 18, 35),
    "panel": (28, 34, 58),
    "panel_light": (38, 48, 78),
    "panel_sel": (48, 62, 98),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 180),
    "accent_green": (80, 190, 120),
    "accent_red": (200, 90, 90),
    "text_white": (235, 240, 250),
    "text_gray": (150, 165, 190),
    "text_dim": (110, 125, 150),
    "divider": (55, 68, 100),
}


def _strip_emoji(text):
    """字体缺 emoji 字形，渲染前剔除以免显示成方块。"""
    out = []
    for ch in str(text):
        o = ord(ch)
        if o > 0xFFFF or 0x2190 <= o <= 0x2BFF or 0xFE00 <= o <= 0xFE0F:
            continue
        out.append(ch)
    return "".join(out).strip() or "（无标题）"


def _fmt_time(ts):
    try:
        return time.strftime("%m-%d %H:%M", time.localtime(ts))
    except Exception:
        return "--"


def _wrap_text(font, text, max_w):
    """按像素宽度折行。"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if font.size(cur + ch)[0] > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


class MailCenter:
    """邮件中心主界面：左列表 / 右详情 / 底部操作。"""

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.mail = MailSystem()
        self.sel = 0
        self.scroll = 0
        self.msg = ""
        self.msg_timer = 0
        self.font_title = get_font(40)
        self.font_main = get_font(24)
        self.font_small = get_font(19)

    # ── 布局 ─────────────────────────────────────────
    def _layout(self):
        pad = 20
        top = 92
        bottom = self.height - 86
        list_w = int(self.width * 0.38)
        return {
            "list": pygame.Rect(pad, top, list_w, bottom - top),
            "detail": pygame.Rect(pad + list_w + 16, top,
                                  self.width - pad * 2 - list_w - 16, bottom - top),
            "btn_y": self.height - 70,
        }

    def _row_h(self):
        return 64

    def _visible_rows(self, L):
        return max(1, (L["list"].height - 8) // self._row_h())

    def _inbox(self):
        return self.mail.get_inbox()

    def _clamp(self, mails):
        if not mails:
            self.sel = 0
            self.scroll = 0
            return
        self.sel = max(0, min(self.sel, len(mails) - 1))
        vis = self._visible_rows(self._layout())
        if self.sel < self.scroll:
            self.scroll = self.sel
        if self.sel >= self.scroll + vis:
            self.scroll = self.sel - vis + 1
        self.scroll = max(0, min(self.scroll, max(0, len(mails) - vis)))

    def _flash(self, text, secs=2.2):
        self.msg = text
        self.msg_timer = pygame.time.get_ticks() + int(secs * 1000)

    # ── 绘制 ─────────────────────────────────────────
    def draw(self, L, mails):
        draw_gradient_bg(self.screen, (18, 22, 42), (10, 12, 26))
        unread = self.mail.get_unread_count()

        title = self.font_title.render("邮件中心", True, COLORS["accent_gold"])
        self.screen.blit(title, (20, 16))
        sub = self.font_small.render(
            f"共 {len(mails)} 封 · 未读 {unread}", True, COLORS["text_gray"])
        self.screen.blit(sub, (20 + title.get_width() + 18, 30))

        self._draw_list(L["list"], mails)
        self._draw_detail(L["detail"], mails)

        if self.msg and pygame.time.get_ticks() < self.msg_timer:
            tip = self.font_small.render(self.msg, True, COLORS["accent_green"])
            self.screen.blit(tip, (20, self.height - 40))

        hint = self.font_small.render(
            "上下键/滚轮 选择 · 回车 读信 · ESC 返回", True, COLORS["text_dim"])
        self.screen.blit(hint, (self.width - hint.get_width() - 20, self.height - 40))

    def _draw_list(self, rect, mails):
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=12)
        inner = rect.inflate(-8, -8)
        row_h = self._row_h()
        vis = self._visible_rows(self._layout())
        clip = self.screen.subsurface(inner)
        clip.set_clip(inner)

        if not mails:
            empty = self.font_main.render("收件箱是空的", True, COLORS["text_dim"])
            clip.blit(empty, (inner.width // 2 - empty.get_width() // 2,
                              inner.height // 2 - empty.get_height() // 2))
            del clip
            return

        for i in range(vis):
            idx = self.scroll + i
            if idx >= len(mails):
                break
            m = mails[idx]
            y = 4 + i * row_h
            r = pygame.Rect(0, y, inner.width, row_h - 6)
            selected = (idx == self.sel)
            pygame.draw.rect(clip, COLORS["panel_sel"] if selected else COLORS["panel_light"],
                             r, border_radius=8)
            if selected:
                pygame.draw.rect(clip, COLORS["accent_gold"], r, 2, border_radius=8)

            dot_c = COLORS["accent_gold"] if not m["read"] else COLORS["text_dim"]
            pygame.draw.circle(clip, dot_c, (14, r.centery), 5)

            sender = _strip_emoji(m["sender"])[:6]
            s_sur = self.font_small.render(sender, True, COLORS["text_gray"])
            clip.blit(s_sur, (28, r.y + 6))

            title = _strip_emoji(m["title"])
            t_color = COLORS["text_white"] if not m["read"] else COLORS["text_gray"]
            t_sur = self.font_main.render(title[:16], True, t_color)
            clip.blit(t_sur, (28, r.y + 28))

            ts = self.font_small.render(_fmt_time(m["time"]), True, COLORS["text_dim"])
            clip.blit(ts, (r.width - ts.get_width() - 10, r.y + 6))

            if m.get("attachments") and not m.get("claimed"):
                badge = self.font_small.render("有附件", True, COLORS["accent_green"])
                clip.blit(badge, (r.width - badge.get_width() - 10, r.y + 30))
        del clip

    def _draw_detail(self, rect, mails):
        pygame.draw.rect(self.screen, COLORS["panel"], rect, border_radius=12)
        if not mails:
            tip = self.font_main.render("选一封信看看吧", True, COLORS["text_dim"])
            self.screen.blit(tip, (rect.centerx - tip.get_width() // 2,
                                   rect.centery - tip.get_height() // 2))
            return

        m = self.mail.read_mail(mails[self.sel]["id"]) or mails[self.sel]
        pad = 18
        x = rect.x + pad
        y = rect.y + pad
        max_w = rect.width - pad * 2

        title = _strip_emoji(m["title"])
        t_sur = self.font_title.render(title[:20], True, COLORS["accent_gold"])
        self.screen.blit(t_sur, (x, y))
        y += t_sur.get_height() + 8

        meta = f"发件人 {_strip_emoji(m['sender'])} · {_fmt_time(m['time'])}"
        m_sur = self.font_small.render(meta, True, COLORS["text_gray"])
        self.screen.blit(m_sur, (x, y))
        y += m_sur.get_height() + 10
        pygame.draw.line(self.screen, COLORS["divider"], (x, y), (rect.right - pad, y))
        y += 12

        for line in _wrap_text(self.font_small, _strip_emoji(m["content"]), max_w):
            if y > rect.bottom - 90:
                break
            c_sur = self.font_small.render(line, True, COLORS["text_white"])
            self.screen.blit(c_sur, (x, y))
            y += c_sur.get_height() + 6

        att = m.get("attachments") or {}
        if att:
            y = max(y, rect.bottom - 78)
            label = "附件：" + "、".join(
                f"{_strip_emoji(k)} x{v}" for k, v in att.items())
            if m.get("claimed"):
                label += "（已领取）"
            a_sur = self.font_small.render(label[:40], True,
                                           COLORS["text_dim"] if m.get("claimed")
                                           else COLORS["accent_green"])
            self.screen.blit(a_sur, (x, y))

    def _draw_buttons(self, L, mails):
        """底部三键：领取附件 / 删除 / 返回。"""
        y = L["btn_y"]
        defs = [
            ("领取附件", COLORS["accent_green"], self._claim),
            ("删除", COLORS["accent_red"], self._delete),
            ("返回", (90, 100, 140), None),
        ]
        bw, bh, gap = 160, 46, 18
        total = len(defs) * bw + (len(defs) - 1) * gap
        x = (self.width - total) // 2
        self._buttons = []
        mouse = pygame.mouse.get_pos()
        for text, color, action in defs:
            r = pygame.Rect(x, y, bw, bh)
            hover = r.collidepoint(mouse)
            pygame.draw.rect(self.screen, color if not hover else
                             tuple(min(255, c + 30) for c in color),
                             r, border_radius=10)
            if action is None or (action is self._claim and (
                    not mails or not (mails[self.sel].get("attachments") or {})
                    or mails[self.sel].get("claimed"))):
                veil = pygame.Surface((bw, bh), pygame.SRCALPHA)
                veil.fill((10, 12, 24, 140))
                self.screen.blit(veil, (x, y))
            t_sur = self.font_main.render(text, True, COLORS["text_white"])
            self.screen.blit(t_sur, (r.centerx - t_sur.get_width() // 2,
                                     r.centery - t_sur.get_height() // 2))
            self._buttons.append((r, action))
            x += bw + gap

    # ── 操作 ─────────────────────────────────────────
    def _claim(self, mails):
        if not mails:
            return
        m = mails[self.sel]
        ok, res = self.mail.claim_attachment(m["id"])
        self._flash(f"领取成功：{res}" if ok else str(res))

    def _delete(self, mails):
        if not mails:
            return
        if self.mail.delete_mail(mails[self.sel]["id"]):
            self._flash("邮件已删除（进了归档）")
            self.sel = max(0, self.sel - 1)

    # ── 主循环 ───────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            L = self._layout()
            mails = self._inbox()
            self._clamp(mails)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.sel = max(0, self.sel - 1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.sel = min(max(0, len(mails) - 1), self.sel + 1)
                    elif event.key == pygame.K_RETURN:
                        self._claim(mails)
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll = max(0, min(self.scroll - event.y,
                                             max(0, len(mails) - self._visible_rows(L))))
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    hit = False
                    for r, action in getattr(self, "_buttons", []):
                        if r.collidepoint(event.pos):
                            hit = True
                            if action is None:
                                running = False
                            else:
                                action(mails)
                            break
                    if not hit and L["list"].collidepoint(event.pos):
                        i = (event.pos[1] - L["list"].y - 4) // self._row_h()
                        idx = self.scroll + i
                        if 0 <= idx < len(mails):
                            self.sel = idx

            self.draw(L, mails)
            self._draw_buttons(L, mails)
            pygame.display.flip()
            clock.tick(60)

        return True


def main():
    try:
        if not pygame.get_init():
            pygame.init()
        screen = open_window()
        pygame.display.set_caption("邮件中心")
        MailCenter(screen).run()
        safe_exit("邮件中心")
    except Exception as e:
        logger.info("邮件中心异常：%s", e)
        safe_exit("邮件中心", str(e))


if __name__ == "__main__":
    main()
