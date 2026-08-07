#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学白板模块 - 可以写字、画图、标注
支持多种工具：画笔、橡皮擦、文字输入、形状绘制
"""

import pygame
import os
import sys

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (50, 200, 50)
BLUE = (50, 100, 255)
PURPLE = (150, 50, 200)
PINK = (255, 100, 150)
GRAY = (128, 128, 128)

COLOR_PALETTE = [
    BLACK, RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, GRAY, WHITE
]

def get_safe_resolution(screen_width, screen_height, min_width=800, min_height=600, ratio=0.85):
    """获取安全的窗口尺寸，确保不超出屏幕"""
    safe_width = int(screen_width * ratio)
    safe_height = int(screen_height * ratio)
    safe_width = max(min_width, safe_width)
    safe_height = max(min_height, safe_height)
    safe_width = min(safe_width, screen_width - 50)
    safe_height = min(safe_height, screen_height - 50)
    return safe_width, safe_height

class DrawingTool:
    def __init__(self, color=BLACK, width=5):
        self.color = color
        self.width = width
        self.start_pos = None

    def draw(self, surface, pos, start_pos=None):
        """绘制图形"""
        pass

class Pen(DrawingTool):
    """画笔工具"""
    def draw(self, surface, pos, last_pos):
        if last_pos:
            pygame.draw.line(surface, self.color, last_pos, pos, self.width)

class Eraser(DrawingTool):
    """橡皮擦"""
    def draw(self, surface, pos, last_pos):
        if last_pos:
            pygame.draw.line(surface, WHITE, last_pos, pos, self.width * 4)

class Rectangle(DrawingTool):
    """矩形工具"""
    def draw(self, surface, pos, start_pos):
        if start_pos:
            rect = pygame.Rect(
                min(start_pos[0], pos[0]),
                min(start_pos[1], pos[1]),
                abs(pos[0] - start_pos[0]),
                abs(pos[1] - start_pos[1])
            )
            pygame.draw.rect(surface, self.color, rect, self.width)

class Circle(DrawingTool):
    """圆形工具"""
    def draw(self, surface, pos, start_pos):
        if start_pos:
            radius = int(((pos[0] - start_pos[0])**2 + (pos[1] - start_pos[1])**2)**0.5)
            pygame.draw.circle(surface, self.color, start_pos, radius, self.width)

class Line(DrawingTool):
    """直线工具"""
    def draw(self, surface, pos, start_pos):
        if start_pos:
            pygame.draw.line(surface, self.color, start_pos, pos, self.width)

class TextTool(DrawingTool):
    """文字输入工具"""
    def __init__(self, color=BLACK, width=5):
        super().__init__(color, width)
        self.text = ""
        self.font_size = 32
        self.font = None

    def draw_text(self, surface, pos, text, font=None):
        if text and font:
            text_surf = font.render(text, True, self.color)
            surface.blit(text_surf, pos)

class Whiteboard:
    def __init__(self, screen):
        self.screen = screen
        self.original_screen = screen
        self.width, self.height = screen.get_size()
        
        # 获取屏幕尺寸，确保窗口不超出
        info = pygame.display.Info()
        screen_w, screen_h = info.current_w, info.current_h
        if self.width > screen_w - 50 or self.height > screen_h - 50:
            self.width, self.height = get_safe_resolution(screen_w, screen_h, 800, 600)
            self.screen = pygame.display.set_mode((self.width, self.height))
        
        self.is_fullscreen = False
        self.original_size = (self.width, self.height)
        
        # 工具栏高度
        self.toolbar_height = 55
        # 创建画布
        self.canvas_height = self.height - self.toolbar_height
        self.canvas = pygame.Surface((self.width, self.canvas_height))
        self.canvas.fill(WHITE)
        
        # 绘图历史
        self.history = []
        self.history_index = -1
        self.max_history = 50
        
        # 当前工具
        self.current_tool = Pen(BLACK, 5)
        self.current_color = BLACK
        self.current_width = 5
        
        # 工具列表
        self.tools = {
            'pen': Pen,
            'eraser': Eraser,
            'rect': Rectangle,
            'circle': Circle,
            'line': Line,
            'text': TextTool
        }
        self.current_tool_name = 'pen'
        
        # 字体
        self.font = None
        self.font_small = None
        self.init_fonts()
        
        # 颜色选择器位置（自适应宽度）
        self.color_palette_rect = pygame.Rect(10, 10, min(300, self.width - 400), 35)
        
        # 按钮自适应布局
        self.buttons = self.create_buttons()
        
        # 状态
        self.running = True
        self.last_pos = None
        self.start_pos = None
        self.text_input = ""
        self.inputting_text = False
        self.input_pos = None
        
        # 时钟
        self.clock = pygame.time.Clock()
    
    def init_fonts(self):
        """初始化字体，小屏幕使用更小的字体"""
        try:
            font_size = 28 if self.width < 1024 else 32
            font_small_size = 18 if self.width < 1024 else 20
            self.font = pygame.font.SysFont("Microsoft YaHei", font_size)
            self.font_small = pygame.font.SysFont("Microsoft YaHei", font_small_size)
        except Exception:
            font_size = 24 if self.width < 1024 else 32
            font_small_size = 16 if self.width < 1024 else 20
            self.font = pygame.font.Font(None, font_size)
            self.font_small = pygame.font.Font(None, font_small_size)
    
    def create_buttons(self):
        """创建工具按钮，自适应布局"""
        # 根据屏幕宽度调整按钮大小和间距
        btn_width = 55 if self.width < 1024 else 60
        btn_height = 35 if self.width < 1024 else 40
        spacing = 5 if self.width < 1024 else 8
        
        buttons = []
        # 第一行按钮
        x = 330
        tool_buttons = [
            ('pen', BLUE, '画笔'),
            ('eraser', GRAY, '橡皮'),
            ('rect', GREEN, '矩形'),
            ('circle', PURPLE, '圆形'),
            ('line', ORANGE, '直线'),
            ('text', RED, '文字'),
        ]
        
        for name, color, text in tool_buttons:
            if x + btn_width > self.width - 360:
                break
            buttons.append(
                {'name': name, 'rect': pygame.Rect(x, 10, btn_width, btn_height), 
                 'color': color, 'text': text}
            )
            x += btn_width + spacing
        
        # 第二行按钮（如果空间足够）
        y = btn_height + 15 if self.height > 600 else 10
        if self.width > 800:
            action_buttons = [
                ('clear', (200, 50, 50), '清除'),
                ('undo', (50, 150, 200), '撤销'),
                ('save', (50, 180, 50), '保存'),
                ('fullscreen', (100, 100, 180), '全屏'),
                ('back', (150, 150, 150), '返回'),
            ]
            
            x = self.width - 80
            for name, color, text in reversed(action_buttons):
                x -= btn_width + spacing
                if x < 330:
                    break
                buttons.append(
                    {'name': name, 'rect': pygame.Rect(x, y, btn_width, btn_height), 
                     'color': color, 'text': text}
                )
        
        return buttons
    
    def to_canvas_pos(self, pos):
        """将屏幕坐标转换为画布坐标"""
        return (pos[0], pos[1] - self.toolbar_height)
    
    def to_screen_pos(self, pos):
        """将画布坐标转换为屏幕坐标"""
        return (pos[0], pos[1] + self.toolbar_height)
    
    def is_on_canvas(self, pos):
        """检查是否在画布区域"""
        return pos[1] >= self.toolbar_height
    
    def draw_color_palette(self):
        """绘制颜色选择器，自适应宽度"""
        palette_width = self.color_palette_rect.width
        color_count = len(COLOR_PALETTE)
        color_width = (palette_width - 10) // color_count
        color_width = max(20, color_width)
        
        pygame.draw.rect(self.screen, (240, 240, 240), self.color_palette_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.color_palette_rect, 2, border_radius=5)
        
        for i, color in enumerate(COLOR_PALETTE):
            rect = pygame.Rect(
                self.color_palette_rect.x + 5 + i * color_width,
                self.color_palette_rect.y + 5,
                color_width - 2,
                self.color_palette_rect.height - 10
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=3)
            if color == self.current_color:
                pygame.draw.rect(self.screen, (255, 215, 0), rect, 3, border_radius=3)
    
    def draw_width_slider(self):
        """绘制粗细滑块，自适应位置"""
        slider_rect = pygame.Rect(
            self.color_palette_rect.x,
            self.color_palette_rect.bottom + 5,
            self.color_palette_rect.width,
            20
        )
        
        pygame.draw.rect(self.screen, (240, 240, 240), slider_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, slider_rect, 2, border_radius=5)
        
        # 滑块
        slider_x = slider_rect.x + 10 + (self.current_width - 1) * 3
        slider_rect = pygame.Rect(slider_x - 4, slider_rect.y + 3, 16, 14)
        pygame.draw.circle(self.screen, self.current_color, slider_rect.center, 7)
    
    def draw_buttons(self):
        """绘制工具按钮"""
        mouse_pos = pygame.mouse.get_pos()
        
        for btn in self.buttons:
            name = btn['name']
            rect = btn['rect']
            
            hovered = rect.collidepoint(mouse_pos)
            
            if name == self.current_tool_name and name not in ['clear', 'undo', 'save', 'fullscreen', 'back']:
                color = (100, 180, 255)
            elif hovered:
                color = tuple(min(c + 30, 255) for c in btn['color'])
            else:
                color = btn['color']
            
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            
            if self.font_small:
                text_surf = self.font_small.render(btn['text'], True, WHITE)
                text_rect = text_surf.get_rect(center=rect.center)
                self.screen.blit(text_surf, text_rect)
    
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.color_palette_rect.collidepoint(mouse_pos):
                    palette_width = self.color_palette_rect.width
                    color_count = len(COLOR_PALETTE)
                    color_width = (palette_width - 10) // color_count
                    color_width = max(20, color_width)
                    color_index = (mouse_pos[0] - self.color_palette_rect.x - 5) // color_width
                    if 0 <= color_index < len(COLOR_PALETTE):
                        self.current_color = COLOR_PALETTE[color_index]
                        self.update_tool()
                elif pygame.Rect(
                    self.color_palette_rect.x,
                    self.color_palette_rect.bottom + 5,
                    self.color_palette_rect.width,
                    20
                ).collidepoint(mouse_pos):
                    new_width = (mouse_pos[0] - self.color_palette_rect.x - 10) // 3 + 1
                    self.current_width = max(1, min(40, new_width))
                    self.update_tool()
                else:
                    button_clicked = False
                    for btn in self.buttons:
                        if btn['rect'].collidepoint(mouse_pos):
                            self.handle_button_click(btn['name'])
                            button_clicked = True
                            break
                    
                    if not button_clicked and not self.inputting_text and self.is_on_canvas(mouse_pos):
                        canvas_pos = self.to_canvas_pos(mouse_pos)
                        self.last_pos = canvas_pos
                        if self.current_tool_name in ['rect', 'circle', 'line']:
                            self.start_pos = canvas_pos
            
            if event.type == pygame.MOUSEBUTTONUP:
                if self.start_pos and self.current_tool_name in ['rect', 'circle', 'line']:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.is_on_canvas(mouse_pos):
                        canvas_pos = self.to_canvas_pos(mouse_pos)
                        self.current_tool.draw(self.canvas, canvas_pos, self.start_pos)
                        self.save_to_history()
                self.last_pos = None
                self.start_pos = None
            
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                if pygame.mouse.get_pressed()[0] and not self.inputting_text and self.is_on_canvas(mouse_pos):
                    canvas_pos = self.to_canvas_pos(mouse_pos)
                    if self.last_pos:
                        if self.current_tool_name == 'pen' or self.current_tool_name == 'eraser':
                            self.current_tool.draw(self.canvas, canvas_pos, self.last_pos)
                            self.last_pos = canvas_pos
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                
                if self.inputting_text:
                    if event.key == pygame.K_RETURN:
                        if self.text_input and self.font:
                            if self.input_pos:
                                text_surf = self.font.render(self.text_input, True, self.current_color)
                                self.canvas.blit(text_surf, self.input_pos)
                                self.save_to_history()
                        self.text_input = ""
                        self.inputting_text = False
                        self.input_pos = None
                    elif event.key == pygame.K_BACKSPACE:
                        self.text_input = self.text_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.text_input = ""
                        self.inputting_text = False
                        self.input_pos = None
                    elif event.unicode:
                        self.text_input += event.unicode
        
        return True
    
    def toggle_fullscreen(self):
        """切换全屏"""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.original_size)
        
        self.width, self.height = self.screen.get_size()
        self.canvas_height = self.height - self.toolbar_height
        self.canvas = pygame.Surface((self.width, self.canvas_height))
        self.canvas.fill(WHITE)
        
        self.buttons = self.create_buttons()
        
        if self.history:
            temp = pygame.Surface((self.width, self.canvas_height))
            temp.fill(WHITE)
            self.canvas = temp
            self.history = [self.canvas.copy()]
            self.history_index = 0
    
    def handle_button_click(self, name):
        """处理按钮点击"""
        if name == 'clear':
            self.canvas.fill(WHITE)
            self.save_to_history()
        elif name == 'undo':
            self.undo()
        elif name == 'save':
            self.save_canvas()
        elif name == 'fullscreen':
            self.toggle_fullscreen()
        elif name == 'back':
            self.running = False
        elif name == 'text':
            self.inputting_text = True
            mouse_pos = pygame.mouse.get_pos()
            if self.is_on_canvas(mouse_pos):
                self.input_pos = self.to_canvas_pos(mouse_pos)
            else:
                self.input_pos = (100, 100)
            self.text_input = ""
        else:
            self.current_tool_name = name
            self.update_tool()
    
    def update_tool(self):
        """更新当前工具"""
        tool_class = self.tools.get(self.current_tool_name, Pen)
        if self.current_tool_name == 'eraser':
            self.current_tool = tool_class(WHITE, self.current_width)
        else:
            self.current_tool = tool_class(self.current_color, self.current_width)
    
    def save_to_history(self):
        """保存到历史"""
        self.history = self.history[:self.history_index + 1]
        temp_surface = self.canvas.copy()
        self.history.append(temp_surface)
        self.history_index += 1
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.history_index -= 1
    
    def undo(self):
        """撤销"""
        if self.history_index > 0:
            self.history_index -= 1
            self.canvas.blit(self.history[self.history_index], (0, 0))
        elif self.history_index == 0 and self.history:
            self.canvas.fill(WHITE)
    
    def save_canvas(self):
        """保存画布为图片"""
        try:
            import time
            filename = f"whiteboard_{int(time.time())}.png"
            pygame.image.save(self.canvas, filename)
            print(f"白板已保存为: {filename}")
        except Exception as e:
            print(f"保存失败: {e}")
    
    def run(self):
        """运行白板"""
        self.save_to_history()
        
        while self.running:
            if not self.handle_events():
                break
            
            self.screen.fill((240, 240, 240))
            
            canvas_screen_rect = pygame.Rect(0, self.toolbar_height, self.width, self.canvas_height)
            pygame.draw.rect(self.screen, WHITE, canvas_screen_rect)
            pygame.draw.rect(self.screen, BLACK, canvas_screen_rect, 2)
            
            self.screen.blit(self.canvas, (0, self.toolbar_height))
            
            if self.start_pos and self.current_tool_name in ['rect', 'circle', 'line']:
                mouse_pos = pygame.mouse.get_pos()
                if self.is_on_canvas(mouse_pos):
                    canvas_pos = self.to_canvas_pos(mouse_pos)
                    temp_surface = self.canvas.copy()
                    self.current_tool.draw(temp_surface, canvas_pos, self.start_pos)
                    self.screen.blit(temp_surface, (0, self.toolbar_height))
            
            self.draw_color_palette()
            self.draw_width_slider()
            self.draw_buttons()
            
            if self.inputting_text and self.font:
                text_surf = self.font.render(self.text_input + "|", True, self.current_color)
                if self.input_pos:
                    screen_pos = self.to_screen_pos(self.input_pos)
                    self.screen.blit(text_surf, screen_pos)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return

def main(screen=None):
    """白板主函数，自适应窗口大小"""
    if screen is None:
        pygame.init()
        info = pygame.display.Info()
        screen_w, screen_h = info.current_w, info.current_h
        width, height = get_safe_resolution(screen_w, screen_h, 800, 600)
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("教学白板")
    
    whiteboard = Whiteboard(screen)
    whiteboard.run()
    
    pygame.quit()
    return True

if __name__ == '__main__':
    main()
