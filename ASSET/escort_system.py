"""镖局押运系统 - 派遣镖队押运货物，经过时间后结算随机事件与奖励。

玩法说明：
    * 玩家从若干条镖路中选择一条，派遣镖队押运。
    * 押运需要真实时间等待，期间可在界面查看进度。
    * 到达目的地后按镖路风险随机触发事件（顺利 / 遇劫 / 天灾），
      事件决定最终获得的奖励倍率。
    * 押运累积经验提升镖局等级，等级解锁更高级、收益更高的镖路。
"""

import os
import time
import random
import datetime

import pygame

from ASSET.game_data import data, save, logger, draw_gradient_bg, get_font
from ASSET import safe_exit

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

COLORS = {
    "bg_dark": (18, 14, 10),
    "bg_light": (38, 28, 18),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 180),
    "accent_blue_light": (100, 149, 237),
    "accent_red": (200, 80, 80),
    "accent_green": (80, 180, 80),
    "accent_orange": (230, 150, 60),
    "text_white": (255, 255, 255),
    "text_gray": (185, 180, 170),
    "panel_bg": (45, 35, 25),
}

# 镖路定义：duration 单位秒，reward 为基准金元宝，risk 为出险概率
ROUTES = [
    {"name": "近郊短途", "duration": 30, "reward": 80, "risk": 0.10, "min_level": 1},
    {"name": "城际商道", "duration": 60, "reward": 200, "risk": 0.20, "min_level": 1},
    {"name": "边关镖路", "duration": 120, "reward": 480, "risk": 0.35, "min_level": 3},
    {"name": "塞外险途", "duration": 300, "reward": 1400, "risk": 0.55, "min_level": 5},
]

RESOURCE_DROPS = ["木头", "食物", "煤炭", "水"]

MAX_HISTORY = 8


class Button:
    """简洁的按钮控件（与其它系统保持一致的视觉风格）。"""

    def __init__(self, text, x, y, width, height, font,
                 normal_color=COLORS["accent_blue"],
                 hover_color=COLORS["accent_blue_light"],
                 text_color=COLORS["text_white"],
                 enabled=True):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.enabled = enabled
        self.is_hovered = False

    def draw(self, surface):
        if not self.enabled:
            color = (70, 70, 70)
        else:
            color = self.hover_color if self.is_hovered else self.normal_color

        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        border = COLORS["accent_gold"] if self.enabled else (110, 110, 110)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=10)

        text_color = self.text_color if self.enabled else (150, 150, 150)
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        shadow = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.enabled and self.rect.collidepoint(mouse_pos)

    def hit(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


def draw_title(surface, text, y_pos, screen_width, font_big):
    """绘制带发光与阴影效果的标题。"""
    for offset in range(5, 0, -1):
        alpha = max(0, 50 - offset * 8)
        glow = font_big.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow, (glow_rect.x + offset, glow_rect.y))

    title = font_big.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    shadow = font_big.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)


def show_message(surface, message, font_main, duration=1600):
    """显示一条居中提示消息。"""
    screen_width = surface.get_width()
    screen_height = surface.get_height()

    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    panel_width = min(560, int(screen_width * 0.7))
    panel_height = 150
    panel_x = (screen_width - panel_width) // 2
    panel_y = (screen_height - panel_height) // 2

    panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (60, 45, 30, 235), (0, 0, panel_width, panel_height), border_radius=15)
    surface.blit(panel_surf, (panel_x, panel_y))
    pygame.draw.rect(surface, COLORS["accent_gold"],
                     (panel_x, panel_y, panel_width, panel_height), 3, border_radius=15)

    text_surf = font_main.render(message, True, COLORS["text_white"])
    text_rect = text_surf.get_rect(center=(screen_width // 2, panel_y + panel_height // 2))
    surface.blit(text_surf, text_rect)

    pygame.display.flip()
    pygame.time.wait(duration)


def _format_remaining(seconds):
    seconds = max(0, int(seconds))
    minutes, sec = divmod(seconds, 60)
    if minutes:
        return f"{minutes}分{sec:02d}秒"
    return f"{sec}秒"


class EscortSystem:
    """镖局押运的核心逻辑，负责状态管理、派遣与结算。"""

    def __init__(self):
        self._ensure_data()

    # -- 数据初始化 --------------------------------------------------------
    def _ensure_data(self):
        escort = data.get("escort")
        if not isinstance(escort, dict):
            escort = {}
        escort.setdefault("level", 1)
        escort.setdefault("exp", 0)
        escort.setdefault("reputation", 0)
        escort.setdefault("total_runs", 0)
        escort.setdefault("active", None)
        escort.setdefault("history", [])
        if not isinstance(escort.get("history"), list):
            escort["history"] = []
        data["escort"] = escort

    @property
    def state(self):
        return data["escort"]

    def get_status(self):
        return {
            "level": self.state["level"],
            "exp": self.state["exp"],
            "required_exp": 100 * self.state["level"],
            "reputation": self.state["reputation"],
            "total_runs": self.state["total_runs"],
        }

    def route_unlocked(self, route):
        return self.state["level"] >= route["min_level"]

    def is_busy(self):
        return self.state.get("active") is not None

    # -- 派遣 --------------------------------------------------------------
    def dispatch(self, route):
        if self.is_busy():
            return False, "镖队正在押运途中，请等待返回。"
        if not self.route_unlocked(route):
            return False, f"镖局等级不足，需要 {route['min_level']} 级。"

        now = time.time()
        self.state["active"] = {
            "name": route["name"],
            "start_time": now,
            "end_time": now + route["duration"],
            "duration": route["duration"],
            "reward": route["reward"],
            "risk": route["risk"],
        }
        save()
        return True, f"镖队已出发前往「{route['name']}」，预计 {_format_remaining(route['duration'])}后返回。"

    # -- 结算 --------------------------------------------------------------
    def update(self):
        """检查押运是否完成；完成则结算并返回结果文本，否则返回 None。"""
        active = self.state.get("active")
        if not active:
            return None
        if time.time() < active["end_time"]:
            return None

        result_text = self._resolve(active)
        self.state["active"] = None
        save()
        return result_text

    def _resolve(self, active):
        roll = random.random()
        risk = active["risk"]
        base = active["reward"]

        if roll < risk * 0.6:
            outcome = "bandit"
        elif roll < risk:
            outcome = "disaster"
        else:
            outcome = "smooth"

        if outcome == "smooth":
            gold = base
            rep = 2
            text = f"「{active['name']}」顺利抵达，获得 {gold} 金元宝！"
        elif outcome == "bandit":
            gold = int(base * 0.5)
            rep = 1
            text = f"「{active['name']}」途中遭遇劫匪，损失部分货物，仅得 {gold} 金元宝。"
        else:  # disaster
            gold = int(base * 0.1)
            rep = 0
            text = f"「{active['name']}」遭遇天灾，货物损毁严重，仅剩 {gold} 金元宝。"

        # 发放金元宝
        data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + gold

        # 概率掉落基础资源
        drop_text = ""
        if outcome != "disaster" and random.random() < 0.7:
            res = random.choice(RESOURCE_DROPS)
            amount = max(5, gold // 4)
            data["resources"][res] = data["resources"].get(res, 0) + amount
            drop_text = f" 另获 {res}×{amount}。"

        # 经验 / 声望 / 次数
        self.state["exp"] += max(10, active["reward"] // 4)
        self.state["reputation"] += rep
        self.state["total_runs"] += 1
        self._check_level_up()

        # 记录历史
        self.state["history"].append({
            "name": active["name"],
            "outcome": outcome,
            "gold": gold,
            "time": datetime.datetime.now().strftime("%m-%d %H:%M"),
        })
        self.state["history"] = self.state["history"][-MAX_HISTORY:]

        return text + drop_text

    def _check_level_up(self):
        required = 100 * self.state["level"]
        leveled = False
        while self.state["exp"] >= required:
            self.state["exp"] -= required
            self.state["level"] += 1
            leveled = True
            required = 100 * self.state["level"]
        if leveled:
            logger.info("[镖局] 升级至 %s 级", self.state["level"])
        return leveled


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------

def _draw_panel(surface, rect, title, font, color=COLORS["accent_gold"]):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*COLORS["panel_bg"], 220), (0, 0, rect.width, rect.height), border_radius=12)
    surface.blit(panel, (rect.x, rect.y))
    pygame.draw.rect(surface, color, rect, 2, border_radius=12)
    if title:
        title_surf = font.render(title, True, color)
        surface.blit(title_surf, (rect.x + 16, rect.y + 12))


def draw_escort_system(screen, system, fonts, route_buttons):
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    font_big, font_main, font_small = fonts

    draw_title(screen, "镖局押运", screen_height * 0.08, screen_width, font_big)

    status = system.get_status()

    # 状态面板
    status_rect = pygame.Rect(40, screen_height * 0.16, screen_width - 80, 90)
    _draw_panel(screen, status_rect, "镖局状态", font_main)
    info = (f"等级 {status['level']}    经验 {status['exp']}/{status['required_exp']}"
            f"    声望 {status['reputation']}    押运次数 {status['total_runs']}")
    screen.blit(font_small.render(info, True, COLORS["text_white"]),
                (status_rect.x + 16, status_rect.y + 52))

    # 押运进度 / 镖路选择
    list_top = status_rect.bottom + 24
    active = system.state.get("active")

    if active:
        active_rect = pygame.Rect(40, list_top, screen_width - 80, 120)
        _draw_panel(screen, active_rect, "押运中", font_main, color=COLORS["accent_orange"])

        remaining = max(0, int(active["end_time"] - time.time()))
        total = max(1, active["duration"])
        progress = min(1.0, (time.time() - active["start_time"]) / total)

        screen.blit(font_small.render(
            f"镖队正前往「{active['name']}」  剩余 {_format_remaining(remaining)}",
            True, COLORS["text_white"]),
            (active_rect.x + 16, active_rect.y + 52))

        bar_x = active_rect.x + 16
        bar_y = active_rect.y + 84
        bar_w = active_rect.width - 32
        bar_h = 18
        pygame.draw.rect(screen, (60, 50, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=9)
        pygame.draw.rect(screen, COLORS["accent_green"],
                         (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=9)
        pygame.draw.rect(screen, (120, 110, 100), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=9)
    else:
        header = font_main.render("选择镖路", True, COLORS["accent_gold"])
        screen.blit(header, (40, list_top))
        list_top += 44

        for route, btn in route_buttons:
            unlocked = system.route_unlocked(route)
            btn.enabled = unlocked and not system.is_busy()
            if not unlocked:
                btn.normal_color = (90, 90, 90)
                btn.text = f"{route['name']}  (需 {route['min_level']} 级)"
            else:
                btn.text = (f"{route['name']}  {_format_remaining(route['duration'])}"
                            f"  约{route['reward']}金  风险{int(route['risk'] * 100)}%")
            btn.draw(screen)

    # 押运记录
    history_top = screen_height - 250
    if history_top > list_top:
        hist_rect = pygame.Rect(40, history_top, screen_width - 80, 180)
        _draw_panel(screen, hist_rect, "最近押运", font_small, color=COLORS["accent_blue"])
        history = system.state.get("history", [])
        y = hist_rect.y + 44
        if not history:
            screen.blit(font_small.render("暂无记录", True, COLORS["text_gray"]),
                        (hist_rect.x + 16, y))
        else:
            for rec in reversed(history[-5:]):
                if rec["outcome"] == "smooth":
                    color = COLORS["accent_green"]
                    tag = "顺利"
                elif rec["outcome"] == "bandit":
                    color = COLORS["accent_red"]
                    tag = "遇劫"
                else:
                    color = COLORS["accent_orange"]
                    tag = "天灾"
                line = f"[{rec['time']}] {rec['name']}  {tag}  +{rec['gold']}金"
                screen.blit(font_small.render(line, True, color), (hist_rect.x + 16, y))
                y += 26


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    """镖局押运系统主函数。"""
    try:
        if not pygame.get_init():
            pygame.init()

        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            screen_width, screen_height = info.current_w, info.current_h
        else:
            resolution = data['settings']['graphics']['resolution']
            try:
                screen_width, screen_height = map(int, resolution.split('x'))
            except (ValueError, AttributeError):
                screen_width, screen_height = 900, 700

        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("镖局押运")
        clock = pygame.time.Clock()

        font_big = get_font(48)
        font_main = get_font(30)
        font_small = get_font(22)
        fonts = (font_big, font_main, font_small)

        system = EscortSystem()

        # 镖路按钮
        route_buttons = []
        btn_width = min(620, screen_width - 120)
        btn_height = 58
        start_y = screen_height * 0.16 + 90 + 24 + 44
        for i, route in enumerate(ROUTES):
            x = (screen_width - btn_width) // 2
            y = start_y + i * (btn_height + 12)
            btn = Button(route["name"], x, y, btn_width, btn_height, font_small)
            route_buttons.append((route, btn))

        back_btn = Button("返回", screen_width - 150, screen_height - 66, 120, 48, font_small)

        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()

            # 结算完成的押运
            result = system.update()
            if result:
                show_message(screen, result, font_main)

            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            draw_escort_system(screen, system, fonts, route_buttons)

            back_btn.check_hover(mouse_pos)
            back_btn.draw(screen)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_btn.hit(event.pos):
                        running = False
                    elif not system.is_busy():
                        for route, btn in route_buttons:
                            if btn.hit(event.pos):
                                ok, message = system.dispatch(route)
                                show_message(screen, message, font_main)
                                break

            clock.tick(60)

        safe_exit("镖局押运")
    except Exception as e:
        logger.info(f"镖局押运异常：{str(e)}")
        import traceback
        traceback.print_exc()
        safe_exit("镖局押运", str(e))


if __name__ == "__main__":
    main()
