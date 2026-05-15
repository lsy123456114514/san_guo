import os
import pygame
import platform
from ASSET.game_data import data, get_system_font_name
from ASSET import safe_exit
from ASSET import snake_game, push_box, breakout, minesweeper, game_2048, tetris, gobang

def main():
    """活动中心主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
        
        # 分辨率适配
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            # 使用设置的分辨率
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 700
                SCREEN_HEIGHT = 500
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("活动中心")
        clock = pygame.time.Clock()

        # 字体初始化
        def init_font(size):
            font_name = get_system_font_name()
            try:
                return pygame.font.SysFont(font_name, size)
            except Exception:
                return pygame.font.Font(None, size)

        font_title = init_font(32 if not 'ANDROID_DATA' in os.environ else 48)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)

        # 颜色定义
        COLOR_BG = (15, 20, 35)
        COLOR_TITLE = (255, 210, 0)
        COLOR_TEXT_MAIN = (255, 255, 255)
        COLOR_TEXT_EMPTY = (150, 150, 150)
        COLOR_BTN = (40, 100, 200)
        COLOR_BTN_HOVER = (60, 130, 230)

        def draw_text(text, x, y, font, color=COLOR_TEXT_MAIN):
            """绘制文字"""
            surf = font.render(text, True, color)
            screen.blit(surf, (x, y))

        # 游戏按钮
        btn_width = min(150, SCREEN_WIDTH * 0.2)
        btn_height = min(80, SCREEN_HEIGHT * 0.12)
        btn_spacing = 20
        
        # 游戏列表
        games = [
            ("🐍 贪吃蛇", snake_game.main),
            ("📦 推箱子", push_box.main),
            ("🎯 打砖块", breakout.main),
            ("💣 扫雷", minesweeper.main),
            ("🔢 2048", game_2048.main),
            ("🧱 俄罗斯方块", tetris.main),
            ("⚫ 五子棋", gobang.main)
        ]
        
        # 计算按钮布局
        cols = min(3, SCREEN_WIDTH // (btn_width + btn_spacing))
        rows = (len(games) + cols - 1) // cols
        start_x = (SCREEN_WIDTH - (cols * btn_width + (cols - 1) * btn_spacing)) // 2
        start_y = 120
        
        # 创建按钮矩形
        game_buttons = []
        for i, (name, func) in enumerate(games):
            row = i // cols
            col = i % cols
            x = start_x + col * (btn_width + btn_spacing)
            y = start_y + row * (btn_height + btn_spacing)
            game_buttons.append({
                'rect': pygame.Rect(x, y, btn_width, btn_height),
                'name': name,
                'func': func
            })
        
        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            screen.fill(COLOR_BG)

            # 标题
            title_text = "游戏活动中心"
            draw_text(title_text, (SCREEN_WIDTH - font_title.size(title_text)[0])//2, 30, font_title, COLOR_TITLE)

            # 游戏按钮
            for game in game_buttons:
                rect = game['rect']
                name = game['name']
                pygame.draw.rect(screen, COLOR_BTN_HOVER if rect.collidepoint(mx, my) else COLOR_BTN, rect, border_radius=8)
                draw_text(name, rect.x + (rect.width - font_normal.size(name)[0])//2, rect.y + 20, font_normal)
                draw_text("完成获得金元宝", rect.x + (rect.width - font_small.size("完成获得金元宝")[0])//2, rect.y + 50, font_small, (255, 210, 0))

            # 活动列表
            y = start_y + rows * (btn_height + btn_spacing) + 40
            if not data["activities"]:
                empty_text = "当前暂无其他活动，敬请期待！"
                draw_text(empty_text, (SCREEN_WIDTH - font_normal.size(empty_text)[0])//2, y, font_normal, COLOR_TEXT_EMPTY)
            else:
                # 绘制自定义活动
                for act_name, act_info in data["activities"].items():
                    act_text = f"{act_name}（{act_info['start']}-{act_info['end']}）"
                    draw_text(act_text, 50, y, font_normal)
                    reward_text = f"奖励：{act_info['reward']}"
                    draw_text(reward_text, 80, y + 40, font_small, (255, 200, 0))
                    y += 80

            # 返回按钮（自适应）
            return_btn_width = min(160, SCREEN_WIDTH * 0.25)
            return_btn_height = min(40, SCREEN_HEIGHT * 0.08)
            return_btn_y = SCREEN_HEIGHT - return_btn_height - 30
            return_btn = pygame.Rect((SCREEN_WIDTH - return_btn_width)//2, return_btn_y, return_btn_width, return_btn_height)
            pygame.draw.rect(screen, COLOR_BTN_HOVER if return_btn.collidepoint(mx, my) else COLOR_BTN, return_btn)
            draw_text("返回主菜单", return_btn.x + (return_btn.width - font_small.size("返回主菜单")[0])//2, return_btn.y + 10, font_small)

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if return_btn.collidepoint(mx, my):
                        running = False
                    else:
                        # 检查游戏按钮点击
                        for game in game_buttons:
                            if game['rect'].collidepoint(mx, my):
                                game['func']()
                                # 重新获取鼠标位置，避免按钮仍然被悬停
                                mx, my = pygame.mouse.get_pos()
                                break

            pygame.display.flip()
            clock.tick(30)

        safe_exit("活动模块")
    except Exception as e:
        safe_exit("活动模块", str(e))

if __name__ == "__main__":
    main()