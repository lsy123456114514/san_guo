"""五子棋小游戏系统（内置休闲玩法）"""

import os
import pygame
import random
import platform
from ASSET.game_data import data, get_system_font_name, create_font, save, logger, get_font, draw_gradient_bg
from ASSET import safe_exit

class GobangGame:
    def __init__(self, screen, font_normal, font_small):
        self.screen = screen
        self.font_normal = font_normal
        self.font_small = font_small
        self.width, self.height = screen.get_size()
        self.board_size = 15
        self.cell_size = 40
        self.reset()
        # 敌对单位配置
        self.enemy_units = []
        self.spawn_enemy_units()
    
    def spawn_enemy_units(self):
        """生成敌对单位"""
        # 生成3-5个敌对单位
        enemy_count = random.randint(3, 5)
        for i in range(enemy_count):
            # 随机位置，但不与初始棋子重叠
            while True:
                row = random.randint(0, self.board_size - 1)
                col = random.randint(0, self.board_size - 1)
                if self.board[row][col] == 0:
                    self.enemy_units.append((row, col))
                    break
    
    def reset(self):
        # 初始化游戏板
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        # 0: 空，1: 黑棋，2: 白棋
        self.current_player = 1  # 1: 黑棋先行
        self.game_over = False
        self.winner = 0
        self.last_move = None
        self.score = 0
        # 重新生成敌对单位
        self.enemy_units = []
        self.spawn_enemy_units()
    
    def get_cell_pos(self, mouse_pos):
        # 计算游戏板的偏移量，使游戏居中
        board_width = self.board_size * self.cell_size
        board_height = self.board_size * self.cell_size
        offset_x = (self.width - board_width) // 2
        offset_y = (self.height - board_height) // 2
        
        x, y = mouse_pos
        col = (x - offset_x) // self.cell_size
        row = (y - offset_y) // self.cell_size
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return row, col
        return None
    
    def make_move(self, row, col):
        if self.game_over or self.board[row][col] != 0:
            return False
        
        # 检查是否攻击了敌对单位
        if (row, col) in self.enemy_units:
            # 攻击成功，获得奖励
            # 金元宝奖励 10-30
            gold_reward = random.randint(10, 30)
            # 其他资源奖励
            other_reward = random.choice(["水", "煤炭", "木头", "食物"])
            other_amount = random.randint(5, 15)
            
            # 显示奖励信息
            reward_text = f"攻击成功！获得金元宝 {gold_reward} 和 {other_reward} {other_amount}"
            reward_surf = self.font_normal.render(reward_text, True, (255, 210, 0))
            self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2))
            pygame.display.flip()
            pygame.time.wait(1500)
            
            # 保存奖励
            data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + gold_reward
            data["resources"][other_reward] = data["resources"].get(other_reward, 0) + other_amount
            save()
            
            # 从敌对单位列表中移除
            self.enemy_units.remove((row, col))
        
        self.board[row][col] = self.current_player
        self.last_move = (row, col)
        
        # 检查是否获胜
        if self.check_win(row, col):
            self.game_over = True
            self.winner = self.current_player
            self.score = 100 if self.winner == 1 else 80
            return True
        
        # 检查是否平局
        if all(cell != 0 for row in self.board for cell in row):
            self.game_over = True
            self.winner = 0
            return True
        
        # 切换玩家
        self.current_player = 2 if self.current_player == 1 else 1
        return True
    
    def check_win(self, row, col):
        player = self.board[row][col]
        directions = [
            (0, 1),   # 水平
            (1, 0),   # 垂直
            (1, 1),   # 对角线
            (1, -1)   # 反对角线
        ]
        
        for dx, dy in directions:
            count = 1
            # 正向
            r, c = row + dx, col + dy
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == player:
                count += 1
                r += dx
                c += dy
            # 反向
            r, c = row - dx, col - dy
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == player:
                count += 1
                r -= dx
                c -= dy
            
            if count >= 5:
                return True
        
        return False
    
    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cell_pos = self.get_cell_pos(event.pos)
            if cell_pos:
                row, col = cell_pos
                self.make_move(row, col)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.game_over:
                self.reset()
    
    def draw(self):
        # 绘制背景
        self.screen.fill((15, 20, 35))
        
        # 计算游戏板的偏移量，使游戏居中
        board_width = self.board_size * self.cell_size
        board_height = self.board_size * self.cell_size
        offset_x = (self.width - board_width) // 2
        offset_y = (self.height - board_height) // 2
        
        # 绘制棋盘
        for i in range(self.board_size):
            # 横线
            y = offset_y + i * self.cell_size
            pygame.draw.line(self.screen, (50, 60, 80), (offset_x, y), (offset_x + board_width, y))
            # 竖线
            x = offset_x + i * self.cell_size
            pygame.draw.line(self.screen, (50, 60, 80), (x, offset_y), (x, offset_y + board_height))
        
        # 绘制棋子
        for i, row in enumerate(self.board):
            for j, cell in enumerate(row):
                if cell != 0:
                    x = offset_x + j * self.cell_size
                    y = offset_y + i * self.cell_size
                    color = (0, 0, 0) if cell == 1 else (255, 255, 255)
                    pygame.draw.circle(self.screen, color, (x + self.cell_size // 2, y + self.cell_size // 2), self.cell_size // 3)
                    # 绘制边框
                    pygame.draw.circle(self.screen, (20, 30, 50), (x + self.cell_size // 2, y + self.cell_size // 2), self.cell_size // 3, 1)
        
        # 绘制敌对单位
        for (row, col) in self.enemy_units:
            x = offset_x + col * self.cell_size
            y = offset_y + row * self.cell_size
            # 绘制红色三角形作为敌对单位
            points = [
                (x + self.cell_size // 2, y),
                (x, y + self.cell_size),
                (x + self.cell_size, y + self.cell_size)
            ]
            pygame.draw.polygon(self.screen, (255, 100, 100), points)
            # 绘制边框
            pygame.draw.polygon(self.screen, (20, 30, 50), points, 2)
        
        # 绘制最后一步的标记
        if self.last_move:
            row, col = self.last_move
            x = offset_x + col * self.cell_size
            y = offset_y + row * self.cell_size
            pygame.draw.circle(self.screen, (255, 0, 0), (x + self.cell_size // 2, y + self.cell_size // 2), 5)
        
        # 绘制信息
        player_text = f"当前玩家: {'黑棋' if self.current_player == 1 else '白棋'}"
        player_surf = self.font_normal.render(player_text, True, (255, 255, 255))
        self.screen.blit(player_surf, (20, 20))
        
        # 游戏结束画面
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            if self.winner == 0:
                game_over_text = "平局"
                game_over_surf = self.font_normal.render(game_over_text, True, (255, 210, 0))
            else:
                game_over_text = f"{'黑棋' if self.winner == 1 else '白棋'}获胜！"
                game_over_surf = self.font_normal.render(game_over_text, True, (100, 255, 100) if self.winner == 1 else (255, 100, 100))
            
            self.screen.blit(game_over_surf, ((self.width - game_over_surf.get_width()) // 2, self.height // 2 - 40))
            
            restart_text = "按空格键重新开始"
            restart_surf = self.font_small.render(restart_text, True, (255, 210, 0))
            self.screen.blit(restart_surf, ((self.width - restart_surf.get_width()) // 2, self.height // 2))
            
            # 计算奖励
            if self.winner != 0:
                reward = self.score
                reward_text = f"获得金元宝: {reward}"
                reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
                self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 40))
                # 保存奖励
                data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
                save()

def main():
    """五子棋游戏主函数"""
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
        pygame.display.set_caption("五子棋")
        clock = pygame.time.Clock()
        
        # 字体初始化
        def init_font(size):
            font_name = get_system_font_name()
            try:
                return create_font(font_name, size)
            except ValueError:
                return pygame.font.Font(None, size)
        
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        
        # 创建游戏实例
        game = GobangGame(screen, font_normal, font_small)
        
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