"""打砖块小游戏系统（内置休闲玩法）"""

import os
import pygame
import random
import math
import platform
from ASSET.game_data import data, get_system_font_name, save, logger, get_font, draw_gradient_bg
from ASSET import safe_exit

class BreakoutGame:
    def __init__(self, screen, font_normal, font_small):
        self.screen = screen
        self.font_normal = font_normal
        self.font_small = font_small
        self.width, self.height = screen.get_size()
        self.reset()
    
    def reset(self):
        # 初始化 paddle
        self.paddle_width = 100
        self.paddle_height = 15
        self.paddle_x = (self.width - self.paddle_width) // 2
        self.paddle_y = self.height - 50
        self.paddle_speed = 8
        
        # 初始化球
        self.ball_radius = 8
        self.ball_x = self.width // 2
        self.ball_y = self.paddle_y - self.ball_radius
        self.ball_dx = random.choice([-5, 5])
        self.ball_dy = -5
        
        # 初始化砖块
        self.bricks = []
        brick_rows = 5
        brick_cols = 10
        brick_width = (self.width - 100) // brick_cols
        brick_height = 25
        
        for row in range(brick_rows):
            for col in range(brick_cols):
                brick_x = 50 + col * brick_width
                brick_y = 80 + row * brick_height
                color = (255 - row * 40, 100 + row * 30, 150)
                self.bricks.append({
                    'rect': pygame.Rect(brick_x, brick_y, brick_width - 2, brick_height - 2),
                    'color': color,
                    'active': True
                })
        
        # 游戏状态
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.game_win = False
    
    def update(self):
        if self.game_over or self.game_win:
            return
        
        # 更新球的位置
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        
        # 边界碰撞检测
        if self.ball_x - self.ball_radius <= 0 or self.ball_x + self.ball_radius >= self.width:
            self.ball_dx = -self.ball_dx
        if self.ball_y - self.ball_radius <= 0:
            self.ball_dy = -self.ball_dy
        
        # 球与 paddle 碰撞检测
        if (self.ball_y + self.ball_radius >= self.paddle_y and
            self.ball_x >= self.paddle_x and
            self.ball_x <= self.paddle_x + self.paddle_width):
            # 计算碰撞位置，使球的反弹角度与碰撞位置有关
            hit_pos = (self.ball_x - self.paddle_x) / self.paddle_width
            angle = (hit_pos - 0.5) * 2 * 0.7  # 最大70度角
            speed = (self.ball_dx**2 + self.ball_dy**2)**0.5
            self.ball_dx = speed * math.sin(angle)
            self.ball_dy = -speed * math.cos(angle)
        
        # 球与砖块碰撞检测
        for brick in self.bricks:
            if brick['active'] and brick['rect'].collidepoint(self.ball_x, self.ball_y):
                brick['active'] = False
                self.ball_dy = -self.ball_dy
                self.score += 10
                break
        
        # 检查游戏胜利
        if all(not brick['active'] for brick in self.bricks):
            self.game_win = True
        
        # 检查球是否掉落
        if self.ball_y - self.ball_radius >= self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            else:
                # 重置球的位置
                self.ball_x = self.width // 2
                self.ball_y = self.paddle_y - self.ball_radius
                self.ball_dx = random.choice([-5, 5])
                self.ball_dy = -5
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and (self.game_over or self.game_win):
                self.reset()
    
    def update_input(self):
        # 持续检查按键状态，实现长按移动
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.paddle_x = max(0, self.paddle_x - self.paddle_speed)
        if keys[pygame.K_RIGHT]:
            self.paddle_x = min(self.width - self.paddle_width, self.paddle_x + self.paddle_speed)
    
    def draw(self):
        # 绘制背景
        self.screen.fill((15, 20, 35))
        
        # 绘制 paddle
        paddle_rect = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height)
        pygame.draw.rect(self.screen, (100, 200, 200), paddle_rect, border_radius=5)
        
        # 绘制球
        pygame.draw.circle(self.screen, (255, 255, 255), (int(self.ball_x), int(self.ball_y)), self.ball_radius)
        
        # 绘制砖块
        for brick in self.bricks:
            if brick['active']:
                pygame.draw.rect(self.screen, brick['color'], brick['rect'], border_radius=3)
        
        # 绘制分数和生命值
        score_text = f"分数: {self.score}"
        score_surf = self.font_normal.render(score_text, True, (255, 255, 255))
        self.screen.blit(score_surf, (20, 20))
        
        lives_text = f"生命: {self.lives}"
        lives_surf = self.font_normal.render(lives_text, True, (255, 255, 255))
        self.screen.blit(lives_surf, (self.width - lives_surf.get_width() - 20, 20))
        
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
            reward = self.score // 20
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
            reward = self.score // 15
            if reward > 0:
                reward_text = f"获得金元宝: {reward}"
                reward_surf = self.font_small.render(reward_text, True, (255, 210, 0))
                self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 80))
                # 保存奖励
                data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
                save()

def main():
    """打砖块游戏主函数"""
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
        pygame.display.set_caption("打砖块")
        clock = pygame.time.Clock()
        
        # 字体初始化
        def init_font(size):
            return get_font(size)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        
        # 创建游戏实例
        game = BreakoutGame(screen, font_normal, font_small)
        
        # 主循环
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                game.handle_input(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            
            # 更新输入
            game.update_input()
            
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