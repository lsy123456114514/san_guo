"""贪吃蛇小游戏系统（内置休闲玩法）"""

import os
import pygame
import random
import platform
from ASSET.game_data import data, get_system_font_name, save, logger, get_font, draw_gradient_bg
from ASSET import safe_exit

class SnakeGame:
    def __init__(self, screen, font_normal, font_small):
        self.screen = screen
        self.font_normal = font_normal
        self.font_small = font_small
        self.width, self.height = screen.get_size()
        self.cell_size = 20
        self.grid_width = self.width // self.cell_size
        self.grid_height = self.height // self.cell_size
        self.level = 1
        self.levels = [
            {"target_score": 50, "time_limit": 60, "speed": 10},    # 关卡1
            {"target_score": 100, "time_limit": 50, "speed": 12},   # 关卡2
            {"target_score": 150, "time_limit": 40, "speed": 14},   # 关卡3
            {"target_score": 200, "time_limit": 30, "speed": 16},   # 关卡4
            {"target_score": 250, "time_limit": 25, "speed": 18}    # 关卡5
        ]
        self.reset()
    
    def reset(self):
        # 初始化蛇
        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = (1, 0)  # 初始方向：右
        self.next_direction = (1, 0)
        # 生成食物
        self.food = self.generate_food()
        # 游戏状态
        self.score = 0
        self.game_over = False
        self.game_win = False
        self.start_time = pygame.time.get_ticks()
        # 获取当前关卡的设置
        level_data = self.levels[min(self.level - 1, len(self.levels) - 1)]
        self.time_limit = level_data["time_limit"]
        self.target_score = level_data["target_score"]
        self.speed = level_data["speed"]
    
    def show_level_up(self):
        # 显示关卡升级信息
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        level_up_text = f"恭喜升级到关卡 {self.level}！"
        level_up_surf = self.font_normal.render(level_up_text, True, (100, 255, 100))
        self.screen.blit(level_up_surf, ((self.width - level_up_surf.get_width()) // 2, self.height // 2 - 40))
        
        level_info = self.levels[min(self.level - 1, len(self.levels) - 1)]
        info_text = f"目标分数: {level_info['target_score']}, 时间: {level_info['time_limit']}s, 速度: {level_info['speed']}"
        info_surf = self.font_small.render(info_text, True, (255, 255, 255))
        self.screen.blit(info_surf, ((self.width - info_surf.get_width()) // 2, self.height // 2))
        
        continue_text = "按空格键继续"
        continue_surf = self.font_small.render(continue_text, True, (255, 210, 0))
        self.screen.blit(continue_surf, ((self.width - continue_surf.get_width()) // 2, self.height // 2 + 40))
        
        pygame.display.flip()
        
        # 等待玩家按空格键
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.game_over = True
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    waiting = False
                    self.game_over = True
    
    def generate_food(self):
        while True:
            food = (random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1))
            if food not in self.snake:
                return food
    
    def update(self):
        if self.game_over:
            return
        
        # 更新方向
        self.direction = self.next_direction
        
        # 移动蛇头
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % self.grid_width, (head_y + dy) % self.grid_height)
        
        # 检查碰撞
        if new_head in self.snake[1:]:
            self.game_over = True
            return
        
        # 检查食物
        if new_head == self.food:
            self.snake.insert(0, new_head)
            self.food = self.generate_food()
            self.score += 10
        else:
            self.snake.insert(0, new_head)
            self.snake.pop()
        
        # 检查关卡升级
        if self.score >= self.target_score:
            if self.level < len(self.levels):
                self.level += 1
                # 显示关卡升级信息
                self.show_level_up()
                self.reset()
            else:
                # 所有关卡完成
                self.game_win = True
                return
        
        # 检查时间
        elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000
        if elapsed_time >= self.time_limit:
            self.game_over = True
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and self.direction != (0, 1):
                self.next_direction = (0, -1)
            elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                self.next_direction = (0, 1)
            elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                self.next_direction = (-1, 0)
            elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                self.next_direction = (1, 0)
    
    def draw(self):
        # 绘制背景
        self.screen.fill((15, 20, 35))
        
        # 绘制网格
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size - 1, self.cell_size - 1)
                pygame.draw.rect(self.screen, (30, 40, 60), rect)
        
        # 绘制食物
        food_x, food_y = self.food
        food_rect = pygame.Rect(food_x * self.cell_size, food_y * self.cell_size, self.cell_size, self.cell_size)
        pygame.draw.rect(self.screen, (255, 100, 100), food_rect)
        
        # 绘制蛇
        for i, (x, y) in enumerate(self.snake):
            snake_rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
            color = (100, 200, 100) if i == 0 else (50, 150, 50)
            pygame.draw.rect(self.screen, color, snake_rect)
        
        # 绘制关卡信息
        level_text = f"关卡: {self.level}"
        level_surf = self.font_normal.render(level_text, True, (255, 255, 255))
        self.screen.blit(level_surf, (20, 20))
        
        # 绘制分数和目标分数
        score_text = f"分数: {self.score}/{self.target_score}"
        score_surf = self.font_normal.render(score_text, True, (255, 255, 255))
        self.screen.blit(score_surf, (20, 50))
        
        # 绘制时间
        elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000
        time_text = f"时间: {self.time_limit - elapsed_time}s"
        time_surf = self.font_normal.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surf, (self.width - time_surf.get_width() - 20, 20))
        
        # 绘制速度
        speed_text = f"速度: {self.speed}"
        speed_surf = self.font_normal.render(speed_text, True, (255, 255, 255))
        self.screen.blit(speed_surf, (self.width - speed_surf.get_width() - 20, 50))
        
        # 游戏胜利画面
        if self.game_win:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            win_text = "恭喜通关所有关卡！"
            win_surf = self.font_normal.render(win_text, True, (100, 255, 100))
            self.screen.blit(win_surf, ((self.width - win_surf.get_width()) // 2, self.height // 2 - 60))
            
            final_score_text = f"最终分数: {self.score}"
            final_score_surf = self.font_small.render(final_score_text, True, (255, 255, 255))
            self.screen.blit(final_score_surf, ((self.width - final_score_surf.get_width()) // 2, self.height // 2 - 20))
            
            restart_text = "按空格键重新开始"
            restart_surf = self.font_small.render(restart_text, True, (255, 210, 0))
            self.screen.blit(restart_surf, ((self.width - restart_surf.get_width()) // 2, self.height // 2 + 20))
            
            # 计算奖励（通关所有关卡获得额外奖励）
            reward = (self.score // 10) + 50  # 额外50个金元宝奖励
            reward_text = f"获得金元宝: {reward}"
            reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
            self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 60))
            # 保存奖励
            data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
            save()
        
        # 游戏结束画面
        elif self.game_over:
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
            reward = self.score // 10
            if reward > 0:
                reward_text = f"获得金元宝: {reward}"
                reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
                self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 80))
                # 保存奖励
                data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
                save()

def main():
    """贪吃蛇游戏主函数"""
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
        pygame.display.set_caption("贪吃蛇")
        clock = pygame.time.Clock()
        
        # 字体初始化
        def init_font(size):
            return get_font(size)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        
        # 创建游戏实例
        game = SnakeGame(screen, font_normal, font_small)
        
        # 主循环
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                game.handle_input(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game.game_over:
                    game.reset()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            
            # 更新游戏
            game.update()
            
            # 绘制游戏
            game.draw()
            
            pygame.display.flip()
            clock.tick(game.speed)  # 使用游戏的速度属性控制蛇的速度
        
        safe_exit("贪吃蛇游戏")
    except Exception as e:
        safe_exit("贪吃蛇游戏", str(e))

if __name__ == "__main__":
    main()