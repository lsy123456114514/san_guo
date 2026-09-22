"""2048 小游戏系统（内置休闲玩法）"""

import os
import pygame
import random
import platform
from ASSET.game_data import data, get_system_font_name, save, logger, get_font, draw_gradient_bg
from ASSET import safe_exit

class Game2048:
    def __init__(self, screen, font_normal, font_small):
        self.screen = screen
        self.font_normal = font_normal
        self.font_small = font_small
        self.width, self.height = screen.get_size()
        self.grid_size = 4
        self.cell_size = 80
        self.reset()
    
    def reset(self):
        # 初始化游戏板
        self.board = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        # 添加两个初始方块
        self.add_random_tile()
        self.add_random_tile()
        # 游戏状态
        self.score = 0
        self.game_over = False
        self.game_win = False
    
    def add_random_tile(self):
        # 找到所有空白位置
        empty_cells = []
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.board[i][j] == 0:
                    empty_cells.append((i, j))
        
        if empty_cells:
            # 随机选择一个空白位置
            i, j = random.choice(empty_cells)
            # 90%概率生成2，10%概率生成4
            self.board[i][j] = 2 if random.random() < 0.9 else 4
    
    def move(self, direction):
        if self.game_over or self.game_win:
            return False
        
        moved = False
        
        if direction == 'up':
            for j in range(self.grid_size):
                # 移动并合并
                new_col = []
                for i in range(self.grid_size):
                    if self.board[i][j] != 0:
                        new_col.append(self.board[i][j])
                
                # 合并相同的数字
                merged_col = []
                i = 0
                while i < len(new_col):
                    if i + 1 < len(new_col) and new_col[i] == new_col[i + 1]:
                        merged_col.append(new_col[i] * 2)
                        self.score += new_col[i] * 2
                        i += 2
                    else:
                        merged_col.append(new_col[i])
                        i += 1
                
                # 填充空白
                while len(merged_col) < self.grid_size:
                    merged_col.append(0)
                
                # 检查是否有变化
                for i in range(self.grid_size):
                    if self.board[i][j] != merged_col[i]:
                        self.board[i][j] = merged_col[i]
                        moved = True
        
        elif direction == 'down':
            for j in range(self.grid_size):
                # 移动并合并
                new_col = []
                for i in range(self.grid_size):
                    if self.board[i][j] != 0:
                        new_col.append(self.board[i][j])
                
                # 合并相同的数字
                merged_col = []
                i = len(new_col) - 1
                while i >= 0:
                    if i - 1 >= 0 and new_col[i] == new_col[i - 1]:
                        merged_col.insert(0, new_col[i] * 2)
                        self.score += new_col[i] * 2
                        i -= 2
                    else:
                        merged_col.insert(0, new_col[i])
                        i -= 1
                
                # 填充空白
                while len(merged_col) < self.grid_size:
                    merged_col.insert(0, 0)
                
                # 检查是否有变化
                for i in range(self.grid_size):
                    if self.board[i][j] != merged_col[i]:
                        self.board[i][j] = merged_col[i]
                        moved = True
        
        elif direction == 'left':
            for i in range(self.grid_size):
                # 移动并合并
                new_row = []
                for j in range(self.grid_size):
                    if self.board[i][j] != 0:
                        new_row.append(self.board[i][j])
                
                # 合并相同的数字
                merged_row = []
                j = 0
                while j < len(new_row):
                    if j + 1 < len(new_row) and new_row[j] == new_row[j + 1]:
                        merged_row.append(new_row[j] * 2)
                        self.score += new_row[j] * 2
                        j += 2
                    else:
                        merged_row.append(new_row[j])
                        j += 1
                
                # 填充空白
                while len(merged_row) < self.grid_size:
                    merged_row.append(0)
                
                # 检查是否有变化
                for j in range(self.grid_size):
                    if self.board[i][j] != merged_row[j]:
                        self.board[i][j] = merged_row[j]
                        moved = True
        
        elif direction == 'right':
            for i in range(self.grid_size):
                # 移动并合并
                new_row = []
                for j in range(self.grid_size):
                    if self.board[i][j] != 0:
                        new_row.append(self.board[i][j])
                
                # 合并相同的数字
                merged_row = []
                j = len(new_row) - 1
                while j >= 0:
                    if j - 1 >= 0 and new_row[j] == new_row[j - 1]:
                        merged_row.insert(0, new_row[j] * 2)
                        self.score += new_row[j] * 2
                        j -= 2
                    else:
                        merged_row.insert(0, new_row[j])
                        j -= 1
                
                # 填充空白
                while len(merged_row) < self.grid_size:
                    merged_row.insert(0, 0)
                
                # 检查是否有变化
                for j in range(self.grid_size):
                    if self.board[i][j] != merged_row[j]:
                        self.board[i][j] = merged_row[j]
                        moved = True
        
        # 如果有移动，添加新方块
        if moved:
            self.add_random_tile()
            # 检查游戏结束
            self.check_game_over()
            # 检查游戏胜利
            self.check_game_win()
        
        return moved
    
    def check_game_over(self):
        # 检查是否有空白位置
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.board[i][j] == 0:
                    return
        
        # 检查是否有可以合并的相邻方块
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                value = self.board[i][j]
                # 检查右侧
                if j + 1 < self.grid_size and self.board[i][j + 1] == value:
                    return
                # 检查下方
                if i + 1 < self.grid_size and self.board[i + 1][j] == value:
                    return
        
        # 游戏结束
        self.game_over = True
    
    def check_game_win(self):
        # 检查是否有2048方块
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.board[i][j] == 2048:
                    self.game_win = True
                    return
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.move('up')
            elif event.key == pygame.K_DOWN:
                self.move('down')
            elif event.key == pygame.K_LEFT:
                self.move('left')
            elif event.key == pygame.K_RIGHT:
                self.move('right')
            elif event.key == pygame.K_SPACE and (self.game_over or self.game_win):
                self.reset()
    
    def get_tile_color(self, value):
        colors = {
            0: (30, 40, 60),
            2: (238, 228, 218),
            4: (237, 224, 200),
            8: (242, 177, 121),
            16: (245, 149, 99),
            32: (246, 124, 95),
            64: (246, 94, 59),
            128: (237, 207, 114),
            256: (237, 204, 97),
            512: (237, 200, 80),
            1024: (237, 197, 63),
            2048: (237, 194, 46)
        }
        return colors.get(value, (200, 190, 180))
    
    def draw(self):
        # 绘制背景
        self.screen.fill((15, 20, 35))
        
        # 计算游戏板的偏移量，使游戏居中
        board_width = self.grid_size * self.cell_size + (self.grid_size + 1) * 10
        board_height = self.grid_size * self.cell_size + (self.grid_size + 1) * 10
        offset_x = (self.width - board_width) // 2
        offset_y = (self.height - board_height) // 2
        
        # 绘制游戏板
        pygame.draw.rect(self.screen, (20, 30, 50), (offset_x, offset_y, board_width, board_height), border_radius=10)
        
        # 绘制方块
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                value = self.board[i][j]
                x = offset_x + 10 + j * (self.cell_size + 10)
                y = offset_y + 10 + i * (self.cell_size + 10)
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                
                # 绘制方块背景
                color = self.get_tile_color(value)
                pygame.draw.rect(self.screen, color, rect, border_radius=5)
                
                # 绘制方块数字
                if value != 0:
                    # 根据数字大小选择字体大小
                    if value < 100:
                        font_size = 36
                    elif value < 1000:
                        font_size = 30
                    else:
                        font_size = 24
                    
                    # 初始化字体
                    def init_font(size):
                        font_name = get_system_font_name()
                        try:
                            return pygame.font.SysFont(font_name, size)
                        except ValueError:
                            return pygame.font.Font(None, size)
                    
                    font = init_font(font_size)
                    text = str(value)
                    # 根据数字大小选择颜色
                    text_color = (119, 110, 101) if value <= 4 else (249, 246, 242)
                    text_surf = font.render(text, True, text_color)
                    text_rect = text_surf.get_rect(center=rect.center)
                    self.screen.blit(text_surf, text_rect)
        
        # 绘制分数
        score_text = f"分数: {self.score}"
        score_surf = self.font_normal.render(score_text, True, (255, 255, 255))
        self.screen.blit(score_surf, (20, 20))
        
        # 游戏结束画面
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = "游戏结束"
            game_over_surf = self.font_normal.render(game_over_text, True, (255, 100, 100))
            self.screen.blit(game_over_surf, ((self.width - game_over_surf.get_width()) // 2, self.height // 2 - 40))
            
            final_score_text = f"最终分数: {self.score}"
            final_score_surf = self.font_small.render(final_score_text, True, (255, 255, 255))
            self.screen.blit(final_score_surf, ((self.width - final_score_surf.get_width()) // 2, self.height // 2))
            
            restart_text = "按空格键重新开始"
            restart_surf = self.font_small.render(restart_text, True, (255, 210, 0))
            self.screen.blit(restart_surf, ((self.width - restart_surf.get_width()) // 2, self.height // 2 + 40))
            
            # 计算奖励
            reward = self.score // 100
            if reward > 0:
                reward_text = f"获得金元宝: {reward}"
                reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
                self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 80))
                # 保存奖励
                data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
                save()
        
        # 游戏胜利画面
        elif self.game_win:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            win_text = "游戏胜利！"
            win_surf = self.font_normal.render(win_text, True, (100, 255, 100))
            self.screen.blit(win_surf, ((self.width - win_surf.get_width()) // 2, self.height // 2 - 40))
            
            final_score_text = f"最终分数: {self.score}"
            final_score_surf = self.font_small.render(final_score_text, True, (255, 255, 255))
            self.screen.blit(final_score_surf, ((self.width - final_score_surf.get_width()) // 2, self.height // 2))
            
            restart_text = "按空格键重新开始"
            restart_surf = self.font_small.render(restart_text, True, (255, 210, 0))
            self.screen.blit(restart_surf, ((self.width - restart_surf.get_width()) // 2, self.height // 2 + 40))
            
            # 计算奖励
            reward = self.score // 50
            if reward > 0:
                reward_text = f"获得金元宝: {reward}"
                reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
                self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 80))
                # 保存奖励
                data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
                save()

def main():
    """2048游戏主函数"""
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
        pygame.display.set_caption("2048")
        clock = pygame.time.Clock()
        
        # 字体初始化
        def init_font(size):
            return get_font(size)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        
        # 创建游戏实例
        game = Game2048(screen, font_normal, font_small)
        
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
        
        safe_exit("2048游戏")
    except Exception as e:
        safe_exit("2048游戏", str(e))

if __name__ == "__main__":
    main()