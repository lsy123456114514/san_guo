"""竞速模式小游戏系统（三国主题无尽跑酷）"""

import os
import pygame
import random
from ASSET.game_data import data, save, logger, get_font
from ASSET import safe_exit


class RacingMode:
    """三国主题无尽竞速跑酷
    玩家骑乘骏马在大地上奔驰，躲避滚石、拒马与箭矢，
    跑得越远得分越高，同时可获得金元宝奖励。
    """

    # 三条车道（上/中/下）对应的屏幕纵向位置比例
    LANES = (0.28, 0.48, 0.68)

    def __init__(self, screen, font_normal, font_small):
        self.screen = screen
        self.font_normal = font_normal
        self.font_small = font_small
        self.width, self.height = screen.get_size()
        self.reset()

    def reset(self):
        """重置游戏状态"""
        # 玩家状态
        self.lane = 1                       # 当前车道（0上 1中 2下）
        self.horse_y = int(self.height * self.LANES[self.lane])
        self.jumping = False                # 是否处于跳跃
        self.jump_height = 0.0
        self.jump_velocity = 0.0

        # 跑道与障碍
        self.obstacles = []                 # 障碍物列表
        self.spawn_timer = 0
        self.speed = 6.0                    # 基础滚动速度
        self.max_speed = 16.0
        self.distance = 0                   # 奔跑距离（米）
        self.reward_given = 0               # 已发放的奖励

        # 状态
        self.game_over = False

        # 背景装饰
        self.ground_scroll = 0
        self.clouds = [(random.randint(0, self.width), random.randint(20, 140), random.randint(40, 90))
                       for _ in range(5)]

    # ---------- 更新逻辑 ----------
    def update(self):
        if self.game_over:
            return

        # 速度随距离提升，难度递增
        self.speed = min(self.max_speed, self.speed + 0.008)
        self.distance += self.speed / 10

        # 跳跃物理（重力模拟）
        if self.jumping:
            self.jump_velocity -= 0.55
            self.jump_height += self.jump_velocity
            if self.jump_height <= 0:
                self.jumping = False
                self.jump_height = 0.0

        # 生成障碍物
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn_timer = random.randint(35, 90)
            if len(self.obstacles) < 6:
                self._spawn_obstacle()

        # 更新障碍物位置并进行碰撞检测
        for obs in self.obstacles[:]:
            obs['x'] -= self.speed
            if obs['x'] < -60:
                self.obstacles.remove(obs)
                continue
            # 跳跃状态下可越过障碍
            if obs['lane'] == self.lane and not self.jumping:
                player_rect = pygame.Rect(70, int(self.horse_y - 30), 55, 60)
                obs_rect = pygame.Rect(int(obs['x']), int(self.height * self.LANES[obs['lane']] - 25), obs['w'], 50)
                if player_rect.colliderect(obs_rect):
                    self.game_over = True

        # 云朵缓慢飘动
        for cloud in self.clouds:
            cloud[0] -= 0.3
            if cloud[0] < -100:
                cloud[0] = self.width + 100

        # 地面滚动
        self.ground_scroll = (self.ground_scroll + self.speed) % 80

    def _spawn_obstacle(self):
        """生成一个障碍物"""
        self.obstacles.append({
            'lane': random.randint(0, 2),
            'x': self.width + 40,
            'w': random.choice((30, 36)),
            'type': random.choice(('stone', 'spear', 'arrow')),
        })

    # ---------- 输入处理 ----------
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.game_over:
                if event.key in (pygame.K_SPACE, pygame.K_r):
                    self.reset()
            else:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._switch_lane(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._switch_lane(1)
                elif event.key in (pygame.K_SPACE, pygame.K_j):
                    self._jump()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.game_over:
                self.reset()
            else:
                x, y = event.pos
                if x > self.width * 0.6:
                    self._jump()          # 点击右半屏跳跃
                else:
                    self._switch_lane(1 if y > self.height * 0.5 else -1)

    def update_input(self):
        """持续按键：上下切换车道"""
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._switch_lane(-1)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self._switch_lane(1)

    def _switch_lane(self, delta):
        new_lane = max(0, min(2, self.lane + delta))
        if new_lane != self.lane:
            self.lane = new_lane
            self.horse_y = int(self.height * self.LANES[self.lane])

    def _jump(self):
        if not self.jumping:
            self.jumping = True
            self.jump_velocity = 9.0

    # ---------- 绘制 ----------
    def draw(self):
        self._draw_sky()
        self._draw_ground()
        self._draw_obstacles()
        self._draw_horse()
        self._draw_hud()
        if self.game_over:
            self._draw_game_over()

    def _draw_sky(self):
        """天空渐变 + 云朵 + 远山"""
        for y in range(self.height):
            ratio = y / self.height
            color = (95 + int(60 * ratio), 130 + int(50 * ratio), 175 + int(30 * ratio))
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))
        # 远山
        pygame.draw.polygon(self.screen, (60, 90, 110), [
            (0, int(self.height * 0.35)), (self.width * 0.2, int(self.height * 0.22)),
            (self.width * 0.4, int(self.height * 0.34)), (self.width * 0.65, int(self.height * 0.2)),
            (self.width, int(self.height * 0.33)), (self.width, int(self.height * 0.4)), (0, int(self.height * 0.4)),
        ])
        # 云朵
        for cx, cy, cw in self.clouds:
            pygame.draw.ellipse(self.screen, (235, 240, 245), (int(cx), int(cy), cw, cw // 2))

    def _draw_ground(self):
        """草地 + 车道分隔线"""
        ground_y = int(self.height * 0.84)
        pygame.draw.rect(self.screen, (74, 138, 64), (0, ground_y, self.width, self.height - ground_y))
        # 车道分隔虚线
        for lane in (1, 2):
            y = int(self.height * (self.LANES[lane] + 0.13))
            for x in range(-80, self.width + 80, 80):
                dx = (x + self.ground_scroll) % (self.width + 160) - 80
                pygame.draw.rect(self.screen, (210, 200, 160), (dx, y, 40, 3))

    def _draw_obstacles(self):
        for obs in self.obstacles:
            x = int(obs['x'])
            lane_y = int(self.height * self.LANES[obs['lane']])
            if obs['type'] == 'stone':        # 滚石
                pygame.draw.circle(self.screen, (110, 110, 115), (x, lane_y + 6), 18)
                pygame.draw.circle(self.screen, (140, 140, 145), (x - 4, lane_y + 2), 8)
            elif obs['type'] == 'spear':      # 拒马
                pygame.draw.rect(self.screen, (120, 78, 45), (x, lane_y - 20, obs['w'], 28), border_radius=3)
                pygame.draw.polygon(self.screen, (200, 200, 205), [
                    (x + 4, lane_y + 8), (x + 8, lane_y + 8), (x + 6, lane_y - 4)])
                pygame.draw.polygon(self.screen, (200, 200, 205), [
                    (x + obs['w'] - 4, lane_y + 8), (x + obs['w'] - 8, lane_y + 8), (x + obs['w'] - 6, lane_y - 4)])
            else:                             # 箭矢
                pygame.draw.rect(self.screen, (200, 60, 50), (x, lane_y - 3, obs['w'], 6))
                pygame.draw.polygon(self.screen, (230, 230, 230), [
                    (x + obs['w'] + 6, lane_y), (x + obs['w'] - 2, lane_y - 6), (x + obs['w'] - 2, lane_y + 6)])

    def _draw_horse(self):
        """绘制骑马武将（马身 + 马头 + 骑手）"""
        base_x = 75
        base_y = self.horse_y - int(self.jump_height * 4)
        # 马身
        pygame.draw.ellipse(self.screen, (110, 75, 40), (base_x - 25, base_y - 12, 55, 28))
        # 马腿
        for leg_dx in (-18, -8, 8, 18):
            pygame.draw.rect(self.screen, (90, 60, 32), (base_x + leg_dx, base_y + 8, 8, 14))
        # 马头
        pygame.draw.rect(self.screen, (110, 75, 40), (base_x + 30, base_y - 18, 14, 20), border_radius=4)
        pygame.draw.circle(self.screen, (30, 30, 30), (base_x + 38, base_y - 12), 2)
        # 骑手（武将）
        pygame.draw.rect(self.screen, (200, 60, 40), (base_x - 6, base_y - 42, 16, 30), border_radius=5)
        pygame.draw.circle(self.screen, (230, 190, 150), (base_x + 2, base_y - 48), 7)
        # 披风飘动
        pygame.draw.polygon(self.screen, (210, 180, 60), [
            (base_x - 4, base_y - 40), (base_x - 24, base_y - 26), (base_x - 2, base_y - 26)])
        # 跳跃尘土
        if self.jumping:
            pygame.draw.ellipse(self.screen, (170, 160, 130), (base_x - 30, base_y + 16, 40, 10))

    def _draw_hud(self):
        distance_text = self.font_normal.render(f"距离: {int(self.distance)} 米", True, (255, 255, 255))
        self.screen.blit(distance_text, (20, 20))
        speed_text = self.font_small.render(f"速度: {self.speed:.1f}", True, (230, 230, 230))
        self.screen.blit(speed_text, (20, 58))
        hint_text = self.font_small.render("↑↓切换车道 空格跳跃  ESC返回", True, (200, 220, 255))
        self.screen.blit(hint_text, (self.width - hint_text.get_width() - 20, 20))

    def _draw_game_over(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title_surf = self.font_normal.render("马失前蹄！竞速结束", True, (255, 120, 100))
        self.screen.blit(title_surf, ((self.width - title_surf.get_width()) // 2, self.height // 2 - 60))

        dist_surf = self.font_small.render(f"奔跑距离: {int(self.distance)} 米", True, (255, 255, 255))
        self.screen.blit(dist_surf, ((self.width - dist_surf.get_width()) // 2, self.height // 2 - 20))

        # 结算金元宝奖励
        reward = int(self.distance) // 100
        if reward > 0 and reward > self.reward_given:
            self.reward_given = reward
            data["resources"]["金元宝"] = data["resources"].get("金元宝", 0) + reward
            save()
        reward_surf = self.font_small.render(f"获得金元宝: {self.reward_given}", True, (255, 210, 0))
        self.screen.blit(reward_surf, ((self.width - reward_surf.get_width()) // 2, self.height // 2 + 20))

        restart_surf = self.font_small.render("按 空格/R 重新开始，ESC 返回主菜单", True, (200, 220, 255))
        self.screen.blit(restart_surf, ((self.width - restart_surf.get_width()) // 2, self.height // 2 + 60))


def main():
    """竞速模式主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
        pygame.mixer.init()

        # 分辨率适配（与其它游戏模块保持一致）
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 800
                SCREEN_HEIGHT = 600

        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("竞速模式")
        clock = pygame.time.Clock()

        # 字体初始化
        font_normal = get_font(36 if 'ANDROID_DATA' in os.environ else 24)
        font_small = get_font(28 if 'ANDROID_DATA' in os.environ else 18)

        # 创建游戏实例
        game = RacingMode(screen, font_normal, font_small)

        # 主循环
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    game.handle_input(event)

            # 更新输入
            game.update_input()

            # 更新与绘制
            game.update()
            game.draw()

            pygame.display.flip()
            clock.tick(60)

        safe_exit("竞速模式")
    except Exception as e:
        safe_exit("竞速模式", str(e))


if __name__ == "__main__":
    main()
