# -*- coding: utf-8 -*-
"""任务/主线/章节系统 - 每日/每周/主线任务调度与领取奖励"""
import pygame
from ASSET.game_data import data, get_system_font_name, draw_gradient_bg, open_window
from ASSET.task_chain_system import TaskChainSystem
from ASSET import safe_exit

# ============ 常量 ============

COLORS = {
    "bg_dark": (15, 20, 35),
    "bg_light": (25, 30, 50),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 220),
    "accent_green": (60, 200, 100),
    "accent_purple": (180, 100, 220),
    "accent_red": (220, 80, 80),
    "text_white": (255, 255, 255),
    "text_gray": (160, 170, 190),
    "panel_bg": (35, 40, 60, 230),
    "btn_green": (50, 160, 80),
    "btn_green_hover": (70, 200, 100),
    "btn_blue": (60, 120, 200),
    "btn_blue_hover": (80, 160, 255),
}

# ============ 按钮控件 ============

class Button:
    """通用按钮"""

    def __init__(self, text, x, y, width, height, font):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.hover = False

    def draw(self, surface):
        color = COLORS["btn_green_hover"] if self.hover else COLORS["btn_green"]
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=8)
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

# ============ 绘制函数 ============

# ============ 主入口 ============

def main(screen=None):
    """任务系统主界面"""
    try:
        if not pygame.get_init():
            pygame.init()

        # 分辨率适配 - 优先使用传入的共享 screen
        if screen is not None:
            SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
        else:
            screen = open_window()
            SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

        pygame.display.set_caption("任务系统")
        clock = pygame.time.Clock()

        # 字体
        font_name = get_system_font_name()
        try:
            FONT_MAIN = pygame.font.Font(font_name, 22) if font_name else pygame.font.SysFont(None, 26)
            FONT_SMALL = pygame.font.Font(font_name, 16) if font_name else pygame.font.SysFont(None, 20)
            FONT_BIG = pygame.font.Font(font_name, 32) if font_name else pygame.font.SysFont(None, 38)
        except Exception:
            FONT_MAIN = pygame.font.SysFont(None, 26)
            FONT_SMALL = pygame.font.SysFont(None, 20)
            FONT_BIG = pygame.font.SysFont(None, 38)

        task_system = TaskChainSystem()
        running = True
        selected_tab = "daily"  # daily / weekly / main
        scroll_offset = 0       # 任务列表滚动量（像素）

        while running:
            mx, my = pygame.mouse.get_pos()

            # 绘制背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])

            # 绘制标题
            title_surf = FONT_BIG.render("📋 任务系统", True, COLORS["accent_gold"])
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
            screen.blit(title_surf, title_rect)

            # 标签按钮
            tab_width = min(150, SCREEN_WIDTH // 5)
            tab_height = 40
            tab_y = 80

            daily_btn = Button("每日任务", 50, tab_y, tab_width, tab_height, FONT_MAIN)
            weekly_btn = Button("每周任务", 50 + tab_width + 10, tab_y, tab_width, tab_height, FONT_MAIN)
            main_btn = Button("主线任务", 50 + (tab_width + 10) * 2, tab_y, tab_width, tab_height, FONT_MAIN)

            daily_btn.update((mx, my))
            weekly_btn.update((mx, my))
            main_btn.update((mx, my))

            # 高亮选中标签
            if selected_tab == "daily":
                daily_btn.hover = True
            elif selected_tab == "weekly":
                weekly_btn.hover = True
            elif selected_tab == "main":
                main_btn.hover = True

            daily_btn.draw(screen)
            weekly_btn.draw(screen)
            main_btn.draw(screen)

            # 列表可视区：标题栏下方 ~ 返回按钮上方
            task_list_y = tab_y + tab_height + 20
            list_bottom = SCREEN_HEIGHT - 70
            try:
                if selected_tab == "daily":
                    tasks = task_system.get_daily_tasks() if hasattr(task_system, 'get_daily_tasks') else []
                elif selected_tab == "weekly":
                    tasks = task_system.get_weekly_tasks() if hasattr(task_system, 'get_weekly_tasks') else []
                else:
                    tasks = task_system.get_main_tasks() if hasattr(task_system, 'get_main_tasks') else []
            except Exception:
                tasks = []

            if not isinstance(tasks, list):
                tasks = []

            # 滚动范围与夹取，避免列表压到返回按钮/画出屏幕
            card_h, card_gap = 70, 10
            total_h = len(tasks) * (card_h + card_gap)
            visible_h = max(1, list_bottom - task_list_y)
            max_scroll = max(0, total_h - visible_h)
            scroll_offset = max(0, min(scroll_offset, max_scroll))

            if not tasks:
                empty_surf = FONT_MAIN.render("暂无任务", True, COLORS["text_gray"])
                screen.blit(empty_surf, empty_surf.get_rect(
                    center=(SCREEN_WIDTH // 2, (task_list_y + list_bottom) // 2)))

            # 绘制任务列表（裁剪到可视区）
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    continue
                task_y = task_list_y + i * (card_h + card_gap) - scroll_offset
                if task_y + card_h < task_list_y or task_y > list_bottom:
                    continue  # 可视区外不画

                # 任务背景
                card_rect = pygame.Rect(50, task_y, SCREEN_WIDTH - 100, card_h)
                task_bg = pygame.Surface((card_rect.width, card_h), pygame.SRCALPHA)
                pygame.draw.rect(task_bg, COLORS["panel_bg"], (0, 0, card_rect.width, card_h), border_radius=8)
                pygame.draw.rect(task_bg, COLORS["accent_gold"], (0, 0, card_rect.width, card_h), 2, border_radius=8)
                screen.blit(task_bg, (card_rect.x, card_rect.y))

                # 任务名称
                name = task.get("name", "未知任务")
                name_surf = FONT_MAIN.render(name, True, COLORS["text_white"])
                screen.blit(name_surf, (card_rect.x + 10, card_rect.y + 5))

                # 任务描述（主线任务没有描述就显示奖励）
                desc = task.get("description", "")
                if desc:
                    desc_surf = FONT_SMALL.render(desc, True, COLORS["text_gray"])
                    screen.blit(desc_surf, (card_rect.x + 10, card_rect.y + 30))

                # 进度：任务系统返回 current/target，老结构才是 task_progress
                progress = task.get("current")
                total = task.get("target", 1)
                if progress is None:
                    task_progress = task.get("task_progress", {})
                    if isinstance(task_progress, dict):
                        progress = task_progress.get("progress", 0)
                        total = task_progress.get("target", total)
                    elif isinstance(task_progress, (int, float)):
                        progress = task_progress

                if not isinstance(progress, (int, float)):
                    progress = 0
                if not isinstance(total, (int, float)) or total == 0:
                    total = 1

                done = progress >= total
                claimed = bool(task.get("claimed", False))
                progress_percent = max(0.0, min(1.0, progress / total))

                # 进度条背景
                bar_x = card_rect.x + 10
                bar_w = card_rect.width - 110
                progress_bg = pygame.Rect(bar_x, card_rect.y + 52, bar_w, 12)
                pygame.draw.rect(screen, COLORS["bg_dark"], progress_bg, border_radius=6)

                # 进度条填充
                progress_fill = pygame.Rect(bar_x, card_rect.y + 52, int(bar_w * progress_percent), 12)
                pygame.draw.rect(screen,
                                 COLORS["accent_green"] if done else COLORS["accent_blue"],
                                 progress_fill, border_radius=6)

                # 进度文本
                progress_text = FONT_SMALL.render(f"{int(progress)}/{int(total)}", True, COLORS["text_white"])
                screen.blit(progress_text, (bar_x + bar_w + 8, card_rect.y + 48))

                # 状态角标：已领取 / 已完成
                if claimed or done:
                    tag = "已领取" if claimed else "已完成"
                    tag_color = COLORS["accent_green"] if claimed else COLORS["accent_gold"]
                    tag_surf = FONT_SMALL.render(tag, True, tag_color)
                    screen.blit(tag_surf, (card_rect.right - tag_surf.get_width() - 10, card_rect.y + 5))

            # 滚动提示
            if max_scroll > 0:
                hint = FONT_SMALL.render("滚轮滚动查看更多", True, COLORS["text_gray"])
                screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 30, tab_y + 10))

            # 返回按钮
            return_btn = Button("返回", 20, SCREEN_HEIGHT - 60, 100, 40, FONT_MAIN)
            return_btn.update((mx, my))
            return_btn.draw(screen)

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    click_x, click_y = event.pos

                    if daily_btn.rect.collidepoint(click_x, click_y):
                        selected_tab = "daily"
                        scroll_offset = 0
                    elif weekly_btn.rect.collidepoint(click_x, click_y):
                        selected_tab = "weekly"
                        scroll_offset = 0
                    elif main_btn.rect.collidepoint(click_x, click_y):
                        selected_tab = "main"
                        scroll_offset = 0
                    elif return_btn.rect.collidepoint(click_x, click_y):
                        running = False
                elif event.type == pygame.MOUSEWHEEL:
                    scroll_offset -= event.y * 40

            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        safe_exit("任务系统", str(e))

if __name__ == "__main__":
    main()
