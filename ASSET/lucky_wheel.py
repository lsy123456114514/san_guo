#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""转盘抽奖系统"""

import math
import random
import logging
import pygame

logger = logging.getLogger(__name__)

from ASSET.game_data import data, save, get_font, draw_gradient_bg

COLORS = {
    'bg_dark': (15, 15, 30),
    'accent_gold': (255, 215, 0),
    'accent_cyan': (0, 200, 255),
    'text_white': (255, 255, 255),
    'text_gray': (160, 160, 160),
    'red': (220, 50, 50),
    'green': (50, 200, 80),
}

WHEEL_PRIZES = [
    {"name": "金元宝x100", "color": (255, 215, 0), "icon": "G", "reward": {"金元宝": 100}, "weight": 15},
    {"name": "木头x200", "color": (139, 90, 43), "icon": "W", "reward": {"木头": 200}, "weight": 20},
    {"name": "食物x150", "color": (200, 120, 50), "icon": "F", "reward": {"食物": 150}, "weight": 20},
    {"name": "水x150", "color": (50, 150, 255), "icon": "S", "reward": {"水": 150}, "weight": 20},
    {"name": "煤炭x100", "color": (100, 100, 100), "icon": "C", "reward": {"煤炭": 100}, "weight": 20},
    {"name": "普通子弹x50", "color": (180, 180, 50), "icon": "B", "reward": {"普通子弹": 50}, "weight": 15},
    {"name": "高级子弹x20", "color": (255, 100, 100), "icon": "H", "reward": {"高级子弹": 20}, "weight": 8},
    {"name": "稀有子弹x10", "color": (180, 80, 255), "icon": "R", "reward": {"稀有子弹": 10}, "weight": 4},
    {"name": "时间卡x1", "color": (0, 200, 255), "icon": "T", "reward": {"时间卡": 1}, "weight": 3},
    {"name": "宠物食物x30", "color": (255, 180, 200), "icon": "P", "reward": {"宠物食物": 30}, "weight": 12},
]


class LuckyWheel:
    def __init__(self, screen):
        self.screen = screen
        self.sw, self.sh = screen.get_size()
        self.font_title = get_font(36)
        self.font_text = get_font(20)
        self.font_small = get_font(16)
        self.font_big = get_font(48)
        self.clock = pygame.time.Clock()

        self.running = True
        self.angle = 0.0
        self.spinning = False
        self.spin_speed = 0.0
        self.result_text = ""
        self.result_timer = 0
        self.show_result = False

        cx, cy = self.sw // 2, self.sh // 2 - 20
        self.center_x = cx
        self.center_y = cy
        self.radius = int(min(self.sw, self.sh) * 0.30)

        self.free_tickets = data.get('lucky_tickets', 3)
        self.total_spins = data.get('lucky_spins', 0)

        btn_w, btn_h = 160, 50
        self.btn_rect = pygame.Rect(cx - btn_w // 2, cy + self.radius + 40, btn_w, btn_h)
        self.btn_hover = False
        self.prizes = WHEEL_PRIZES
        self.won_prize = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
                return None
            if event.type == pygame.MOUSEMOTION:
                self.btn_hover = self.btn_rect.collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_rect.collidepoint(event.pos) and not self.spinning:
                    if self.free_tickets > 0:
                        self._start_spin()
        return True

    def _start_spin(self):
        self.spinning = True
        self.spin_speed = random.uniform(18, 25)
        self.show_result = False
        self.won_prize = None
        self.free_tickets -= 1
        data['lucky_tickets'] = self.free_tickets
        self.total_spins += 1
        data['lucky_spins'] = self.total_spins
        save()

    def _calculate_prize(self):
        total_weight = sum(p["weight"] for p in self.prizes)
        sector_angle = 360.0 / len(self.prizes)
        # 指针在顶部(270度方向)，计算转盘停止时指针对应的扇区
        normalized = (360 - (self.angle % 360)) % 360
        hit_index = int(normalized / sector_angle) % len(self.prizes)

        # 加权随机替换（20%概率按权重选）
        if random.random() < 0.2:
            r = random.uniform(0, total_weight)
            cumul = 0
            for i, p in enumerate(self.prizes):
                cumul += p["weight"]
                if r <= cumul:
                    hit_index = i
                    break
        return self.prizes[hit_index]

    def _award_prize(self, prize):
        for res, amt in prize["reward"].items():
            if res in data.get("resources", {}):
                data["resources"][res] += amt
            else:
                data.setdefault("resources", {})[res] = amt
        self.result_text = f"恭喜获得: {prize['name']}!"
        self.show_result = True
        self.result_timer = 180
        self.won_prize = prize
        save()

    def update(self):
        if self.spinning:
            self.angle += self.spin_speed
            self.spin_speed *= 0.985
            if self.spin_speed < 0.3:
                self.spinning = False
                prize = self._calculate_prize()
                self._award_prize(prize)
        if self.show_result:
            self.result_timer -= 1
            if self.result_timer <= 0:
                self.show_result = False

    def _draw_wheel(self):
        cx, cy, r = self.center_x, self.center_y, self.radius
        n = len(self.prizes)
        sector_angle = 360.0 / n

        # 转盘外圈装饰
        pygame.draw.circle(self.screen, (60, 60, 80), (cx, cy), r + 8)
        pygame.draw.circle(self.screen, COLORS['accent_gold'], (cx, cy), r + 8, 3)

        # 灯泡装饰
        for i in range(20):
            a = math.radians(i * 18 + self.angle * 0.3)
            lx = int(cx + (r + 16) * math.cos(a))
            ly = int(cy + (r + 16) * math.sin(a))
            c = COLORS['accent_gold'] if i % 2 == 0 else COLORS['accent_cyan']
            pygame.draw.circle(self.screen, c, (lx, ly), 4)

        for i, prize in enumerate(self.prizes):
            start_angle = math.radians(self.angle + i * sector_angle)
            end_angle = math.radians(self.angle + (i + 1) * sector_angle)

            # 扇形填充
            points = [(cx, cy)]
            for j in range(25):
                a = start_angle + (end_angle - start_angle) * j / 24
                px = int(cx + r * math.cos(a))
                py = int(cy + r * math.sin(a))
                points.append((px, py))
            points.append((cx, cy))

            try:
                pygame.draw.polygon(self.screen, prize["color"], points)
                pygame.draw.polygon(self.screen, (40, 40, 60), points, 2)
            except Exception:
                pass

            # 奖品文字
            mid_angle = (start_angle + end_angle) / 2
            tx = int(cx + r * 0.62 * math.cos(mid_angle))
            ty = int(cy + r * 0.62 * math.sin(mid_angle))
            try:
                txt_surf = self.font_small.render(prize["name"], True, (255, 255, 255))
                txt_rect = txt_surf.get_rect(center=(tx, ty))
                old_center = txt_rect.center
                txt_rect = txt_rect.rotate(-(self.angle + i * sector_angle + sector_angle / 2))
                txt_rect.center = old_center
                self.screen.blit(txt_surf, txt_rect)
            except Exception:
                pass

        # 中心圆
        pygame.draw.circle(self.screen, (30, 30, 50), (cx, cy), 30)
        pygame.draw.circle(self.screen, COLORS['accent_gold'], (cx, cy), 30, 3)
        try:
            ct = self.font_text.render("GO", True, COLORS['accent_gold'])
            self.screen.blit(ct, ct.get_rect(center=(cx, cy)))
        except Exception:
            pass

    def _draw_pointer(self):
        cx, cy, r = self.center_x, self.center_y, self.radius
        # 三角形指针在顶部
        px = cx
        py = cy - r - 14
        points = [(px, py), (px - 12, py + 24), (px + 12, py + 24)]
        pygame.draw.polygon(self.screen, COLORS['red'], points)
        pygame.draw.polygon(self.screen, (255, 255, 255), points, 2)

    def _draw_button(self):
        rect = self.btn_rect
        color = COLORS['accent_gold'] if self.btn_hover else (180, 150, 50)
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS['text_white'], rect, 2, border_radius=10)
        try:
            label = self.font_text.render("抽 奖", True, (15, 15, 30))
            self.screen.blit(label, label.get_rect(center=rect.center))
        except Exception:
            pass

    def _draw_info(self):
        # 剩余次数
        try:
            t = self.font_text.render(f"剩余抽奖次数: {self.free_tickets}", True, COLORS['accent_cyan'])
            self.screen.blit(t, (20, 20))
            t2 = self.font_small.render(f"累计抽奖: {self.total_spins}次", True, COLORS['text_gray'])
            self.screen.blit(t2, (20, 50))
        except Exception:
            pass

    def _draw_result(self):
        if not self.show_result or not self.won_prize:
            return
        # 半透明遮罩
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        # 结果面板
        pw, ph = 400, 200
        px = (self.sw - pw) // 2
        py = (self.sh - ph) // 2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((30, 30, 60, 230))
        pygame.draw.rect(panel, COLORS['accent_gold'], (0, 0, pw, ph), 3, border_radius=15)
        self.screen.blit(panel, (px, py))

        try:
            title = self.font_title.render("抽奖结果", True, COLORS['accent_gold'])
            self.screen.blit(title, title.get_rect(centerx=self.sw // 2, top=py + 20))
            prize_t = self.font_text.render(self.won_prize["name"], True, self.won_prize["color"])
            self.screen.blit(prize_t, prize_t.get_rect(centerx=self.sw // 2, top=py + 75))
            hint = self.font_small.render("点击任意位置关闭", True, COLORS['text_gray'])
            self.screen.blit(hint, hint.get_rect(centerx=self.sw // 2, top=py + 130))
        except Exception:
            pass

    def draw(self):
        draw_gradient_bg(self.screen, COLORS['bg_dark'], (10, 10, 25))
        self._draw_wheel()
        self._draw_pointer()
        self._draw_button()
        self._draw_info()
        self._draw_result()
        try:
            title = self.font_title.render("幸运转盘", True, COLORS['accent_gold'])
            self.screen.blit(title, title.get_rect(centerx=self.sw // 2, top=10))
        except Exception:
            pass

    def main(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        return None


def main(screen):
    """模块入口"""
    wheel = LuckyWheel(screen)
    wheel.main()
    return None
