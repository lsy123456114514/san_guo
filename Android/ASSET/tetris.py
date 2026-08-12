"""俄罗斯方块小游戏系统（内置休闲玩法）"""

import os
import pygame
import random
import platform
from ASSET.game_data import data, get_system_font_name, save, logger, get_font, draw_gradient_bg
from ASSET import safe_exit

class TetrisGame:
    def __init__(self, screen, font_normal, font_small):
        self.screen = screen
        self.font_normal = font_normal
        self.font_small = font_small
        self.width, self.height = screen.get_size()
        self.grid_width = 10
        self.grid_height = 20
        self.cell_size = 30
        self.reset()
    
    def reset(self):
        # 初始化游戏板
        self.board = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        # 定义方块形状
        self.shapes = [
            # I 形
            [[1, 1, 1, 1]],
            # J 形
            [[1, 0, 0], [1, 1, 1]],
            # L 形
            [[0, 0, 1], [1, 1, 1]],
            # O 形
            [[1, 1], [1, 1]],
            # S 形
            [[0, 1, 1], [1, 1, 0]],
            # T 形
            [[0, 1, 0], [1, 1, 1]],
            # Z 形
            [[1, 1, 0], [0, 1, 1]]
        ]
        # 方块颜色
        self.colors = [
            (0, 0, 0),      # 空白
            (0, 255, 255),  # I 形
            (0, 0, 255),    # J 形
            (255, 165, 0),  # L 形
            (255, 255, 0),  # O 形
            (0, 255, 0),    # S 形
            (128, 0, 128),  # T 形
            (255, 0, 0)     # Z 形
        ]
        # 初始化当前方块
        self.current_shape = None
        self.current_pos = (0, 0)
        self.current_color = 0
        # 游戏状态
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        # 下落速度
        self.drop_speed = 1000  # 毫秒
        self.last_drop_time = pygame.time.get_ticks()
        # 生成新方块
        self.spawn_new_shape()
    
    def spawn_new_shape(self):
        # 随机选择一个形状
        shape_index = random.randint(0, len(self.shapes) - 1)
        self.current_shape = self.shapes[shape_index]
        self.current_color = shape_index + 1
        # 初始位置
        self.current_pos = (self.grid_width // 2 - len(self.current_shape[0]) // 2, 0)
        # 检查游戏是否结束
        if not self.is_valid_position(self.current_shape, self.current_pos):
            self.game_over = True
    
    def is_valid_position(self, shape, pos):
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    x = pos[0] + j
                    y = pos[1] + i
                    if (x < 0 or x >= self.grid_width or 
                        y >= self.grid_height or 
                        (y >= 0 and self.board[y][x] != 0)):
                        return False
        return True
    
    def rotate_shape(self, shape):
        # 旋转形状
        return list(zip(*reversed(shape)))
    
    def merge_shape(self):
        # 将当前方块合并到游戏板
        for i, row in enumerate(self.current_shape):
            for j, cell in enumerate(row):
                if cell:
                    x = self.current_pos[0] + j
                    y = self.current_pos[1] + i
                    if y >= 0:
                        self.board[y][x] = self.current_color
        # 检查是否有可消除的行
        self.check_lines()
        # 生成新方块
        self.spawn_new_shape()
    
    def check_lines(self):
        lines_to_clear = []
        for i, row in enumerate(self.board):
            if all(cell != 0 for cell in row):
                lines_to_clear.append(i)
        
        # 消除行
        for line in sorted(lines_to_clear, reverse=True):
            del self.board[line]
            self.board.insert(0, [0 for _ in range(self.grid_width)])
            self.score += 100 * self.level
            self.lines_cleared += 1
        
        # 升级
        if self.lines_cleared >= self.level * 10:
            self.level += 1
            self.drop_speed = max(100, self.drop_speed - 100)
    
    def update(self):
        if self.game_over:
            return
        
        # 自动下落
        current_time = pygame.time.get_ticks()
        if current_time - self.last_drop_time >= self.drop_speed:
            self.last_drop_time = current_time
            # 尝试下移
            new_pos = (self.current_pos[0], self.current_pos[1] + 1)
            if self.is_valid_position(self.current_shape, new_pos):
                self.current_pos = new_pos
            else:
                # 无法下移，合并方块
                self.merge_shape()
    
    def handle_input(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.reset()
            return
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                # 左移
                new_pos = (self.current_pos[0] - 1, self.current_pos[1])
                if self.is_valid_position(self.current_shape, new_pos):
                    self.current_pos = new_pos
            elif event.key == pygame.K_RIGHT:
                # 右移
                new_pos = (self.current_pos[0] + 1, self.current_pos[1])
                if self.is_valid_position(self.current_shape, new_pos):
                    self.current_pos = new_pos
            elif event.key == pygame.K_DOWN:
                # 下移
                new_pos = (self.current_pos[0], self.current_pos[1] + 1)
                if self.is_valid_position(self.current_shape, new_pos):
                    self.current_pos = new_pos
            elif event.key == pygame.K_UP:
                # 旋转
                rotated_shape = self.rotate_shape(self.current_shape)
                if self.is_valid_position(rotated_shape, self.current_pos):
                    self.current_shape = rotated_shape
            elif event.key == pygame.K_SPACE:
                # 快速下落
                while True:
                    new_pos = (self.current_pos[0], self.current_pos[1] + 1)
                    if self.is_valid_position(self.current_shape, new_pos):
                        self.current_pos = new_pos
                    else:
                        self.merge_shape()
                        break
    
    def draw(self):
        # 绘制背景
        self.screen.fill((15, 20, 35))
        
        # 计算游戏板的偏移量，使游戏居中
        board_width = self.grid_width * self.cell_size
        board_height = self.grid_height * self.cell_size
        offset_x = (self.width - board_width) // 2
        offset_y = (self.height - board_height) // 2
        
        # 绘制游戏板
        for i, row in enumerate(self.board):
            for j, cell in enumerate(row):
                if cell != 0:
                    x = offset_x + j * self.cell_size
                    y = offset_y + i * self.cell_size
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    pygame.draw.rect(self.screen, self.colors[cell], rect)
                    pygame.draw.rect(self.screen, (20, 30, 50), rect, 1)
        
        # 绘制当前方块
        for i, row in enumerate(self.current_shape):
            for j, cell in enumerate(row):
                if cell:
                    x = offset_x + (self.current_pos[0] + j) * self.cell_size
                    y = offset_y + (self.current_pos[1] + i) * self.cell_size
                    if y >= 0:  # 只绘制可见部分
                        rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                        pygame.draw.rect(self.screen, self.colors[self.current_color], rect)
                        pygame.draw.rect(self.screen, (20, 30, 50), rect, 1)
        
        # 绘制信息
        score_text = f"分数: {self.score}"
        score_surf = self.font_normal.render(score_text, True, (255, 255, 255))
        self.screen.blit(score_surf, (20, 20))
        
        level_text = f"等级: {self.level}"
        level_surf = self.font_normal.render(level_text, True, (255, 255, 255))
        self.screen.blit(level_surf, (20, 60))
        
        lines_text = f"消除行数: {self.lines_cleared}"
        lines_surf = self.font_normal.render(lines_text, True, (255, 255, 255))
        self.screen.blit(lines_surf, (20, 100))
        
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
            reward = self.score // 200
            if reward > 0:
                reward_text = f"获得金元宝: {reward}"
                reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
                self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 80))
                # 保存奖励
                data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
                save()

def main():
    """俄罗斯方块游戏主函数"""
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
        pygame.display.set_caption("俄罗斯方块")
        clock = pygame.time.Clock()
        
        # 字体初始化
        def init_font(size):
            return get_font(size)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        
        # 创建游戏实例
        game = TetrisGame(screen, font_normal, font_small)
        
        # 主循环
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                game.handle_input(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            
            # 更新游戏
            game.update()
            
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