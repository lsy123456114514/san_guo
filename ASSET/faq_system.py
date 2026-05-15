#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pygame
import os
from ASSET.game_data import data, save, get_system_font_name
from ASSET.game_main_menu import Button, draw_gradient_background, COLORS

# 字体变量
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None

# 常见问题列表
FAQs = [
    {
        "id": 1,
        "question": "如何获得金元宝？",
        "answer": "金元宝可以通过以下方式获得：\n1. 完成游戏任务\n2. 挑战副本\n3. 出售物品\n4. 钓鱼系统\n5. 炼金系统\n6. 每日签到奖励"
    },
    {
        "id": 2,
        "question": "如何提升武将等级？",
        "answer": "提升武将等级的方法：\n1. 让武将参与战斗\n2. 使用经验丹\n3. 完成特定任务获得经验奖励\n4. 在训练场中训练武将"
    },
    {
        "id": 3,
        "question": "如何获得稀有武将？",
        "answer": "获得稀有武将的途径：\n1. 在武将商城中购买\n2. 参与活动获取武将碎片\n3. 挑战高级副本\n4. 抽奖系统"
    },
    {
        "id": 4,
        "question": "建筑系统有什么作用？",
        "answer": "建筑系统的作用：\n1. 资源中心：提高资源产出速度\n2. 训练场：提高武将攻击力\n3. 研究实验室：加速科技研究速度\n4. 宝库：增加金元宝产出\n5. 兵营：提高武将防御力"
    },
    {
        "id": 5,
        "question": "天赋系统如何使用？",
        "answer": "天赋系统使用方法：\n1. 通过游戏进度获得天赋点\n2. 在天赋系统界面分配天赋点\n3. 不同天赋类别提供不同的属性加成\n4. 天赋点可以根据需要重新分配"
    },
    {
        "id": 6,
        "question": "钓鱼系统如何玩？",
        "answer": "钓鱼系统玩法：\n1. 选择钓鱼地点\n2. 使用鱼饵进行钓鱼\n3. 根据提示时机点击收杆\n4. 获得各种鱼类，出售获取金元宝\n5. 升级钓鱼等级解锁更多地点"
    },
    {
        "id": 7,
        "question": "炼金系统有什么用？",
        "answer": "炼金系统的作用：\n1. 将低级资源合成为高级资源\n2. 制作特殊物品和道具\n3. 提高资源利用效率\n4. 解锁新的合成配方"
    },
    {
        "id": 8,
        "question": "如何提升装备等级？",
        "answer": "提升装备等级的方法：\n1. 在装备系统中强化装备\n2. 使用强化石和金币\n3. 装备等级提升会增加属性加成\n4. 高级装备需要更高等级的强化材料"
    },
    {
        "id": 9,
        "question": "宠物系统如何使用？",
        "answer": "宠物系统使用方法：\n1. 在宠物系统中选择宠物\n2. 给宠物喂食提升等级\n3. 宠物提供各种属性加成\n4. 不同宠物有不同的技能和效果"
    },
    {
        "id": 10,
        "question": "游戏内AI如何使用？",
        "answer": "游戏内AI使用方法：\n1. 在游戏内AI界面开启AI功能\n2. 确保本地已安装OLLAMA并运行\n3. 输入模型完整名称（如：llama3）\n4. 输入OLLAMA地址（默认：http://localhost:11434）\n5. 在聊天界面与AI对话"
    }
]

def draw_title(surface, text, y_pos, screen_width):
    """绘制带特效的标题"""
    global FONT_BIG
    # 发光效果
    for offset in range(5, 0, -1):
        alpha = 50 - offset * 8
        glow_surf = FONT_BIG.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    # 主标题
    title = FONT_BIG.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    
    # 阴影
    shadow = FONT_BIG.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)
    
    # 装饰线
    line_y = y_pos + 40
    pygame.draw.line(surface, COLORS["accent_gold"], 
                    (screen_width // 2 - 150, line_y),
                    (screen_width // 2 - 50, line_y), 3)
    pygame.draw.line(surface, COLORS["accent_gold"],
                    (screen_width // 2 + 50, line_y),
                    (screen_width // 2 + 150, line_y), 3)
    # 中间装饰
    pygame.draw.circle(surface, COLORS["accent_gold"], (screen_width // 2, line_y), 8)
    pygame.draw.circle(surface, COLORS["bg_dark"], (screen_width // 2, line_y), 5)

def draw_resource_panel(surface, x, y, width, height):
    """绘制资源面板"""
    global FONT_SMALL
    panel_rect = pygame.Rect(x, y, width, height)
    
    # 面板背景
    panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (30, 30, 55, 180), (0, 0, width, height), border_radius=10)
    surface.blit(panel_surf, (x, y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], panel_rect, 2, border_radius=10)
    
    # 资源图标和文字
    resources = [
        ("金元宝", data['resources']['金元宝'], COLORS["accent_gold"]),
        ("水", data['resources']['水'], COLORS["accent_blue"]),
        ("食物", data['resources']['食物'], (200, 150, 100))
    ]
    
    spacing = width // len(resources)
    for i, (icon, value, color) in enumerate(resources):
        icon_x = x + i * spacing + spacing // 2
        icon_y = y + height // 2
        
        # 资源名称背景
        pygame.draw.rect(surface, (40, 40, 70), (icon_x - 40, icon_y - 12, 80, 24), border_radius=12)
        pygame.draw.rect(surface, color, (icon_x - 40, icon_y - 12, 80, 24), 2, border_radius=12)
        
        # 文字
        text = FONT_SMALL.render(f"{icon}: {value}", True, COLORS["text_white"])
        text_rect = text.get_rect(center=(icon_x, icon_y))
        surface.blit(text, text_rect)

def main():
    """疑难解答主函数"""
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG
    
    # 初始化pygame
    if not pygame.get_init():
        pygame.init()
    
    # 获取屏幕大小
    if 'ANDROID_DATA' in os.environ:
        # Android设备使用全屏
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        screen = pygame.display.set_mode((screen_width, screen_height))
    else:
        # PC设备
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
    
    pygame.display.set_caption("疑难解答")
    clock = pygame.time.Clock()
    
    # 初始化字体
    font_name = get_system_font_name()
    try:
        if font_name:
            FONT_MAIN = pygame.font.SysFont(font_name, 40)
            FONT_SMALL = pygame.font.SysFont(font_name, 28)
            FONT_BIG = pygame.font.SysFont(font_name, 60)
        else:
            FONT_MAIN = pygame.font.Font(None, 40)
            FONT_SMALL = pygame.font.Font(None, 28)
            FONT_BIG = pygame.font.Font(None, 60)
    except Exception:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 28)
        FONT_BIG = pygame.font.Font(None, 60)
    
    # 主循环
    running = True
    selected_faq = None
    scroll_y = 0
    
    while running:
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        draw_title(screen, "疑难解答", screen_height * 0.1, screen_width)
        
        # 资源面板
        panel_width = min(500, screen_width * 0.7)
        draw_resource_panel(screen, (screen_width - panel_width) // 2, 
                          screen_height * 0.18, panel_width, 50)
        
        # FAQ列表区域
        faq_list_area = pygame.Rect(50, screen_height * 0.3, screen_width - 100, screen_height * 0.5)
        pygame.draw.rect(screen, (30, 30, 55, 200), faq_list_area, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], faq_list_area, 2, border_radius=10)
        
        # 显示FAQ列表
        y_offset = faq_list_area.y + 10 - scroll_y
        for faq in FAQs:
            # 问题按钮
            question_text = f"Q: {faq['question']}"
            question_btn = Button(
                question_text,
                faq_list_area.x + 10,
                y_offset,
                faq_list_area.width - 20,
                50,
                FONT_SMALL,
                normal_color=COLORS["accent_blue"] if selected_faq != faq['id'] else COLORS["accent_gold"]
            )
            question_btn.check_hover(pygame.mouse.get_pos())
            question_btn.draw(screen)
            
            # 如果是选中的FAQ，显示答案
            if selected_faq == faq['id']:
                # 答案区域
                answer_area = pygame.Rect(faq_list_area.x + 20, y_offset + 60, faq_list_area.width - 40, 200)
                pygame.draw.rect(screen, (40, 40, 70, 200), answer_area, border_radius=5)
                
                # 显示答案
                answer_lines = faq['answer'].split('\n')
                answer_y = answer_area.y + 10
                for line in answer_lines:
                    answer_surf = FONT_SMALL.render(line, True, COLORS["text_white"])
                    screen.blit(answer_surf, (answer_area.x + 10, answer_y))
                    answer_y += answer_surf.get_height() + 5
                
                y_offset += 220
            else:
                y_offset += 60
        
        # 滚动条
        max_scroll = max(0, (len(FAQs) * 60 + (220 if selected_faq else 0)) - faq_list_area.height)
        if max_scroll > 0:
            scroll_bar_height = (faq_list_area.height / (len(FAQs) * 60 + (220 if selected_faq else 0))) * faq_list_area.height
            scroll_bar_y = faq_list_area.y + (scroll_y / max_scroll) * (faq_list_area.height - scroll_bar_height)
            scroll_bar = pygame.Rect(faq_list_area.right - 15, scroll_bar_y, 10, scroll_bar_height)
            pygame.draw.rect(screen, COLORS["accent_gold"], scroll_bar, border_radius=5)
        
        # 返回按钮
        back_btn = Button(
            "返回主菜单",
            screen_width - 200,
            screen_height - 60,
            180,
            50,
            FONT_SMALL,
            normal_color=COLORS["accent_blue_dark"]
        )
        back_btn.check_hover(pygame.mouse.get_pos())
        back_btn.draw(screen)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                pygame.quit()
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # 检查FAQ按钮点击
                y_offset = faq_list_area.y + 10 - scroll_y
                for faq in FAQs:
                    question_btn = Button(
                        f"Q: {faq['question']}",
                        faq_list_area.x + 10,
                        y_offset,
                        faq_list_area.width - 20,
                        50,
                        FONT_SMALL
                    )
                    if question_btn.check_click(mouse_pos):
                        if selected_faq == faq['id']:
                            selected_faq = None
                        else:
                            selected_faq = faq['id']
                        scroll_y = 0  # 重置滚动位置
                        break
                    
                    if selected_faq == faq['id']:
                        y_offset += 220
                    else:
                        y_offset += 60
                
                # 检查返回按钮
                if back_btn.check_click(mouse_pos):
                    save()
                    return
                
                # 检查滚动条
                if max_scroll > 0:
                    scroll_bar_height = (faq_list_area.height / (len(FAQs) * 60 + (220 if selected_faq else 0))) * faq_list_area.height
                    scroll_bar = pygame.Rect(faq_list_area.right - 15, faq_list_area.y, 10, faq_list_area.height)
                    if scroll_bar.collidepoint(mouse_pos):
                        # 拖动滚动条
                        dragging = True
                        while dragging:
                            for drag_event in pygame.event.get():
                                if drag_event.type == pygame.MOUSEBUTTONUP:
                                    dragging = False
                                elif drag_event.type == pygame.MOUSEMOTION:
                                    drag_y = drag_event.pos[1]
                                    scroll_ratio = (drag_y - faq_list_area.y) / faq_list_area.height
                                    scroll_y = max(0, min(max_scroll, scroll_ratio * max_scroll))
                        
            # 鼠标滚轮滚动
            if event.type == pygame.MOUSEWHEEL:
                if max_scroll > 0:
                    scroll_y = max(0, min(max_scroll, scroll_y - event.y * 20))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
