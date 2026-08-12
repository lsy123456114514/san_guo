"""扫雷小游戏系统（内置休闲玩法）"""

import os
import pygame
import random
import platform
from ASSET.game_data import data, get_system_font_name, save, logger, get_font, draw_gradient_bg
from ASSET import safe_exit

class MinesweeperGame:
    def __init__(self, screen, font_normal, font_small):
        self.screen = screen
        self.font_normal = font_normal
        self.font_small = font_small
        self.width, self.height = screen.get_size()
        self.cell_size = 30
        self.rows = 16
        self.cols = 16
        self.mines = 40
        self.reset()
    
    def reset(self):
        # 初始化游戏板
        self.board = []
        self.revealed = []
        self.flagged = []
        
        for row in range(self.rows):
            board_row = []
            revealed_row = []
            for col in range(self.cols):
                board_row.append(0)
                revealed_row.append(False)
            self.board.append(board_row)
            self.revealed.append(revealed_row)
        
        # 随机放置地雷
        mine_count = 0
        while mine_count < self.mines:
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)
            if self.board[row][col] != -1:
                self.board[row][col] = -1
                mine_count += 1
        
        # 计算每个格子周围的地雷数
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] == -1:
                    continue
                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        r = row + dr
                        c = col + dc
                        if 0 <= r < self.rows and 0 <= c < self.cols:
                            if self.board[r][c] == -1:
                                count += 1
                self.board[row][col] = count
        
        # 游戏状态
        self.game_over = False
        self.game_win = False
        self.score = 0
        self.start_time = pygame.time.get_ticks()
    
    def reveal(self, row, col):
        if self.game_over or self.game_win:
            return
        
        if self.revealed[row][col] or (row, col) in self.flagged:
            return
        
        self.revealed[row][col] = True
        
        # 踩到地雷
        if self.board[row][col] == -1:
            self.game_over = True
            return
        
        # 空白格子，递归揭示周围的格子
        if self.board[row][col] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    r = row + dr
                    c = col + dc
                    if 0 <= r < self.rows and 0 <= c < self.cols:
                        self.reveal(r, c)
        
        # 检查游戏胜利
        revealed_count = sum(row.count(True) for row in self.revealed)
        if revealed_count == self.rows * self.cols - self.mines:
            self.game_win = True
    
    def toggle_flag(self, row, col):
        if self.game_over or self.game_win:
            return
        
        if self.revealed[row][col]:
            return
        
        if (row, col) in self.flagged:
            self.flagged.remove((row, col))
        else:
            self.flagged.append((row, col))
    
    def get_cell_pos(self, mouse_pos):
        # 计算游戏板的偏移量，使游戏居中
        board_width = self.cols * self.cell_size
        board_height = self.rows * self.cell_size
        offset_x = (self.width - board_width) // 2
        offset_y = (self.height - board_height) // 2
        
        x, y = mouse_pos
        col = (x - offset_x) // self.cell_size
        row = (y - offset_y) // self.cell_size
        
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return row, col
        return None
    
    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cell_pos = self.get_cell_pos(event.pos)
            if cell_pos:
                row, col = cell_pos
                if event.button == 1:  # 左键
                    self.reveal(row, col)
                elif event.button == 3:  # 右键
                    self.toggle_flag(row, col)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and (self.game_over or self.game_win):
                self.reset()
    
    def draw(self):
        # 绘制背景
        self.screen.fill((15, 20, 35))
        
        # 计算游戏板的偏移量，使游戏居中
        board_width = self.cols * self.cell_size
        board_height = self.rows * self.cell_size
        offset_x = (self.width - board_width) // 2
        offset_y = (self.height - board_height) // 2
        
        # 绘制游戏板
        for row in range(self.rows):
            for col in range(self.cols):
                x = offset_x + col * self.cell_size
                y = offset_y + row * self.cell_size
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                
                if self.revealed[row][col]:
                    if self.board[row][col] == -1:
                        # 地雷
                        pygame.draw.rect(self.screen, (200, 80, 80), rect)
                        pygame.draw.circle(self.screen, (0, 0, 0), (x + self.cell_size // 2, y + self.cell_size // 2), self.cell_size // 3)
                    else:
                        # 已揭示的格子
                        pygame.draw.rect(self.screen, (30, 40, 60), rect)
                        if self.board[row][col] > 0:
                            # 显示周围地雷数
                            colors = [
                                (0, 0, 255),    # 1
                                (0, 150, 0),    # 2
                                (255, 0, 0),    # 3
                                (128, 0, 128),  # 4
                                (139, 69, 19),  # 5
                                (0, 128, 128),  # 6
                                (0, 0, 0),      # 7
                                (128, 128, 128) # 8
                            ]
                            text = str(self.board[row][col])
                            text_surf = self.font_small.render(text, True, colors[self.board[row][col] - 1])
                            text_rect = text_surf.get_rect(center=rect.center)
                            self.screen.blit(text_surf, text_rect)
                else:
                    # 未揭示的格子
                    pygame.draw.rect(self.screen, (50, 60, 80), rect)
                    if (row, col) in self.flagged:
                        # 标记
                        pygame.draw.polygon(self.screen, (255, 0, 0), [
                            (x + self.cell_size // 2, y + 5),
                            (x + 5, y + self.cell_size - 5),
                            (x + self.cell_size - 5, y + self.cell_size - 5)
                        ])
                
                # 格子边框
                pygame.draw.rect(self.screen, (20, 30, 50), rect, 1)
        
        # 绘制信息
        time_elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        time_text = f"时间: {time_elapsed}s"
        time_surf = self.font_normal.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surf, (20, 20))
        
        mines_text = f"地雷: {self.mines - len(self.flagged)}"
        mines_surf = self.font_normal.render(mines_text, True, (255, 255, 255))
        self.screen.blit(mines_surf, (self.width - mines_surf.get_width() - 20, 20))
        
        # 游戏结束画面
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = "游戏结束"
            game_over_surf = self.font_normal.render(game_over_text, True, (255, 100, 100))
            self.screen.blit(game_over_surf, ((self.width - game_over_surf.get_width()) // 2, self.height // 2 - 40))
            
            restart_text = "按空格键重新开始"
            restart_surf = self.font_small.render(restart_text, True, (255, 210, 0))
            self.screen.blit(restart_surf, ((self.width - restart_surf.get_width()) // 2, self.height // 2))
        
        # 游戏胜利画面
        elif self.game_win:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            win_text = "游戏胜利！"
            win_surf = self.font_normal.render(win_text, True, (100, 255, 100))
            self.screen.blit(win_surf, ((self.width - win_surf.get_width()) // 2, self.height // 2 - 40))
            
            time_text = f"用时: {time_elapsed}s"
            time_surf = self.font_small.render(time_text, True, (255, 255, 255))
            self.screen.blit(time_surf, ((self.width - time_surf.get_width()) // 2, self.height // 2))
            
            restart_text = "按空格键重新开始"
            restart_surf = self.font_small.render(restart_text, True, (255, 210, 0))
            self.screen.blit(restart_surf, ((self.width - restart_surf.get_width()) // 2, self.height // 2 + 40))
            
            # 计算奖励
            reward = max(10, 50 - time_elapsed)
            reward_text = f"获得金元宝: {reward}"
            reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
            self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 80))
            # 保存奖励
            data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
            save()

def main():
    """扫雷游戏主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
        pygame.mixer.init()
        
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
                SCREEN_WIDTH = 800
                SCREEN_HEIGHT = 600
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("扫雷")
        clock = pygame.time.Clock()
        
        # 字体初始化
        def init_font(size):
            return get_font(size)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        
        # 创建游戏实例
        game = MinesweeperGame(screen, font_normal, font_small)
        
        # 主循环
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                game.handle_input(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            
            # 绘制游戏
            game.draw()
            
            pygame.display.flip()
            clock.tick(60)
        
        return
    except Exception as e:
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()