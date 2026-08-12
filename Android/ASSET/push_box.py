"""推箱子小游戏系统（内置休闲玩法）"""

import os
import pygame
import platform
from ASSET.game_data import data, get_system_font_name, save, logger, get_font, draw_gradient_bg
from ASSET import safe_exit

class PushBoxGame:
    def __init__(self, screen, font_normal, font_small):
        self.screen = screen
        self.font_normal = font_normal
        self.font_small = font_small
        self.width, self.height = screen.get_size()
        self.cell_size = 40
        self.levels = self.load_levels()
        self.current_level = 0
        self.reset()
    
    def load_levels(self):
        # 定义多个推箱子关卡，从简单到复杂
        levels = [
            # 关卡1
            [
                "########",
                "#      #",
                "#  $   #",
                "#@ .   #",
                "#      #",
                "########"
            ],
            # 关卡2
            [
                "########",
                "#  $ $ #",
                "#@ . . #",
                "#      #",
                "########"
            ],
            # 关卡3
            [
                "########",
                "#$     #",
                "# $    #",
                "#@ . . #",
                "#      #",
                "########"
            ],
            # 关卡4
            [
                "########",
                "# . $ . #",
                "# $   $ #",
                "#@     #",
                "########"
            ],
            # 关卡5
            [
                "#########",
                "#   #   #",
                "# $ # $ #",
                "#@  #  .#",
                "# . # . #",
                "#########"
            ],
            # 关卡6
            [
                "########",
                "#   .  #",
                "# $ #  #",
                "#$  #  #",
                "#@  .  #",
                "########"
            ],
            # 关卡7
            [
                "###########",
                "#     #   #",
                "# $   # $ #",
                "# $ $   $ #",
                "#@ . . . #",
                "###########"
            ],
            # 关卡8
            [
                "########",
                "#..$   #",
                "#$ $   #",
                "#@     #",
                "#  $   #",
                "#  .   #",
                "########"
            ]
        ]
        return levels
    
    def reset(self):
        if self.current_level >= len(self.levels):
            self.current_level = 0
        
        level = self.levels[self.current_level]
        self.grid = []
        self.player_pos = (0, 0)
        self.boxes = []
        self.targets = []
        
        for y, row in enumerate(level):
            grid_row = []
            for x, char in enumerate(row):
                if char == '@':
                    self.player_pos = (x, y)
                    grid_row.append(' ')
                elif char == '$':
                    self.boxes.append((x, y))
                    grid_row.append(' ')
                elif char == '.':
                    self.targets.append((x, y))
                    grid_row.append('.')
                else:
                    grid_row.append(char)
            self.grid.append(grid_row)
        
        self.game_over = False
        self.steps = 0
    
    def move(self, dx, dy):
        if self.game_over:
            return
        
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        
        # 检查边界
        if new_x < 0 or new_x >= len(self.grid[0]) or new_y < 0 or new_y >= len(self.grid):
            return
        
        # 检查是否是墙
        if self.grid[new_y][new_x] == '#':
            return
        
        # 检查是否有箱子
        if (new_x, new_y) in self.boxes:
            # 计算箱子的新位置
            box_new_x = new_x + dx
            box_new_y = new_y + dy
            
            # 检查箱子是否可以移动
            if (box_new_x < 0 or box_new_x >= len(self.grid[0]) or 
                box_new_y < 0 or box_new_y >= len(self.grid) or 
                self.grid[box_new_y][box_new_x] == '#' or 
                (box_new_x, box_new_y) in self.boxes):
                return
            
            # 移动箱子
            self.boxes.remove((new_x, new_y))
            self.boxes.append((box_new_x, box_new_y))
        
        # 移动玩家
        self.player_pos = (new_x, new_y)
        self.steps += 1
        
        # 检查是否完成
        if all(box in self.targets for box in self.boxes):
            self.game_over = True
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.move(0, -1)
            elif event.key == pygame.K_DOWN:
                self.move(0, 1)
            elif event.key == pygame.K_LEFT:
                self.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                self.move(1, 0)
            elif event.key == pygame.K_SPACE and self.game_over:
                self.current_level += 1
                self.reset()
    
    def draw(self):
        # 绘制背景
        self.screen.fill((15, 20, 35))
        
        # 计算偏移量，使游戏居中
        level_width = len(self.grid[0]) * self.cell_size
        level_height = len(self.grid) * self.cell_size
        offset_x = (self.width - level_width) // 2
        offset_y = (self.height - level_height) // 2
        
        # 绘制网格
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                rect = pygame.Rect(offset_x + x * self.cell_size, offset_y + y * self.cell_size, self.cell_size, self.cell_size)
                if cell == '#':
                    pygame.draw.rect(self.screen, (100, 100, 150), rect)
                elif cell == '.':
                    pygame.draw.rect(self.screen, (30, 60, 90), rect)
                    # 绘制目标点
                    target_rect = pygame.Rect(offset_x + x * self.cell_size + 10, offset_y + y * self.cell_size + 10, self.cell_size - 20, self.cell_size - 20)
                    pygame.draw.rect(self.screen, (255, 210, 0), target_rect, border_radius=5)
                else:
                    pygame.draw.rect(self.screen, (30, 40, 60), rect)
        
        # 绘制箱子
        for (x, y) in self.boxes:
            box_rect = pygame.Rect(offset_x + x * self.cell_size + 5, offset_y + y * self.cell_size + 5, self.cell_size - 10, self.cell_size - 10)
            color = (255, 150, 50) if (x, y) in self.targets else (200, 100, 50)
            pygame.draw.rect(self.screen, color, box_rect, border_radius=5)
        
        # 绘制玩家
        player_rect = pygame.Rect(offset_x + self.player_pos[0] * self.cell_size + 8, offset_y + self.player_pos[1] * self.cell_size + 8, self.cell_size - 16, self.cell_size - 16)
        pygame.draw.rect(self.screen, (100, 200, 100), player_rect, border_radius=10)
        
        # 绘制信息
        level_text = f"关卡: {self.current_level + 1}/{len(self.levels)}"
        level_surf = self.font_normal.render(level_text, True, (255, 255, 255))
        self.screen.blit(level_surf, (20, 20))
        
        steps_text = f"步数: {self.steps}"
        steps_surf = self.font_normal.render(steps_text, True, (255, 255, 255))
        self.screen.blit(steps_surf, (20, 60))
        
        # 游戏结束画面
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # 检查是否通关所有关卡
            if self.current_level >= len(self.levels) - 1:
                # 通关所有关卡
                win_text = "恭喜通关所有关卡！"
                win_surf = self.font_normal.render(win_text, True, (100, 255, 100))
                self.screen.blit(win_surf, ((self.width - win_surf.get_width()) // 2, self.height // 2 - 60))
                
                steps_text = f"总步数: {self.steps}"
                steps_surf = self.font_small.render(steps_text, True, (255, 255, 255))
                self.screen.blit(steps_surf, ((self.width - steps_surf.get_width()) // 2, self.height // 2 - 20))
                
                restart_text = "按空格键重新开始"
                restart_surf = self.font_small.render(restart_text, True, (255, 210, 0))
                self.screen.blit(restart_surf, ((self.width - restart_surf.get_width()) // 2, self.height // 2 + 20))
                
                # 计算奖励（通关所有关卡获得额外奖励）
                reward = len(self.levels) * 10 + 50  # 额外50个金元宝奖励
                reward_text = f"获得金元宝: {reward}"
                reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
                self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 60))
            else:
                # 完成单个关卡
                win_text = "关卡完成！"
                win_surf = self.font_normal.render(win_text, True, (255, 210, 0))
                self.screen.blit(win_surf, ((self.width - win_surf.get_width()) // 2, self.height // 2 - 40))
                
                steps_text = f"总步数: {self.steps}"
                steps_surf = self.font_small.render(steps_text, True, (255, 255, 255))
                self.screen.blit(steps_surf, ((self.width - steps_surf.get_width()) // 2, self.height // 2))
                
                next_text = "按空格键进入下一关"
                next_surf = self.font_small.render(next_text, True, (255, 210, 0))
                self.screen.blit(next_surf, ((self.width - next_surf.get_width()) // 2, self.height // 2 + 40))
                
                # 计算奖励
                reward = (len(self.levels) - self.current_level) * 5
                reward_text = f"获得金元宝: {reward}"
                reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
                self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 80))
            
            # 保存奖励
            data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
            save()

def main():
    """推箱子游戏主函数"""
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
        pygame.display.set_caption("推箱子")
        clock = pygame.time.Clock()
        
        # 字体初始化
        def init_font(size):
            return get_font(size)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        
        # 创建游戏实例
        game = PushBoxGame(screen, font_normal, font_small)
        
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