#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bug上报系统 - 玩家可以直接在游戏中上报Bug
"""
import pygame
import sys
import os
from ASSET.game_main_menu import Button, init_fonts
from ASSET.log_system import report_bug, read_bug_reports, log_info

FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None
screen = None
clock = None

def main():
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG
    
    if not pygame.get_init():
        pygame.init()
    
    init_fonts()
    from ASSET.game_main_menu import FONT_MAIN as MAIN_FONT, FONT_SMALL as SMALL_FONT, FONT_BIG as BIG_FONT
    FONT_MAIN = MAIN_FONT
    FONT_SMALL = SMALL_FONT
    FONT_BIG = BIG_FONT
    
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Bug上报")
    clock = pygame.time.Clock()
    
    button_width = 140
    button_height = 55
    
    back_btn = Button("返回", (screen_width - button_width) // 2, screen_height - button_height - 30, button_width, button_height, FONT_SMALL)
    
    title_input = ""
    desc_input = ""
    step_input = ""
    user_input = ""
    
    input_fields = [
        {"label": "Bug标题", "text": "", "max_len": 50, "y_offset": 150, "is_title": True},
        {"label": "Bug描述", "text": "", "max_len": 200, "y_offset": 230, "is_desc": True},
        {"label": "复现步骤", "text": "", "max_len": 100, "y_offset": 310, "is_step": True},
        {"label": "联系方式", "text": "", "max_len": 50, "y_offset": 390, "is_user": True},
    ]
    
    active_field = None
    report_success = False
    report_id = None
    
    running = True
    while running:
        screen.fill((30, 30, 60))
        
        title_surf = FONT_BIG.render("🐛 Bug上报", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(screen_width // 2, 50))
        screen.blit(title_surf, title_rect)
        
        tip_text = FONT_SMALL.render("请详细描述您遇到的问题，我们会尽快处理！", True, (150, 150, 150))
        tip_rect = tip_text.get_rect(center=(screen_width // 2, 100))
        screen.blit(tip_text, tip_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        for field in input_fields:
            field_y = field["y_offset"]
            
            label_surf = FONT_SMALL.render(field["label"], True, (200, 200, 200))
            screen.blit(label_surf, (screen_width // 2 - 200, field_y - 35))
            
            box_width = 400
            box_height = 35 if field.get("is_desc") else 35
            
            box_rect = pygame.Rect(screen_width // 2 - box_width // 2, field_y, box_width, box_height)
            
            if field == active_field:
                pygame.draw.rect(screen, (60, 80, 120), box_rect, border_radius=5)
                pygame.draw.rect(screen, (255, 215, 0), box_rect, 2, border_radius=5)
            else:
                pygame.draw.rect(screen, (50, 50, 80), box_rect, border_radius=5)
                pygame.draw.rect(screen, (80, 80, 100), box_rect, 1, border_radius=5)
            
            text_surf = FONT_SMALL.render(field["text"], True, (255, 255, 255))
            text_x = box_rect.left + 10
            text_y = box_rect.top + (box_height - text_surf.get_height()) // 2
            screen.blit(text_surf, (text_x, text_y))
            
            if field == active_field:
                cursor_x = text_x + text_surf.get_width()
                cursor_y = text_y
                pygame.draw.line(screen, (255, 255, 255), (cursor_x, cursor_y), (cursor_x, cursor_y + text_surf.get_height()), 2)
        
        submit_btn = Button("提交Bug", screen_width // 2 - 70, 470, 140, 45, FONT_SMALL)
        submit_btn.check_hover(mouse_pos)
        submit_btn.draw(screen)
        
        if report_success:
            success_panel = pygame.Surface((400, 200), pygame.SRCALPHA)
            pygame.draw.rect(success_panel, (40, 80, 40, 220), (0, 0, 400, 200), border_radius=15)
            screen.blit(success_panel, ((screen_width - 400) // 2, screen_height // 2 - 100))
            pygame.draw.rect(screen, (0, 255, 0), ((screen_width - 400) // 2, screen_height // 2 - 100, 400, 200), 2, border_radius=15)
            
            success_title = FONT_BIG.render("✓ 提交成功！", True, (0, 255, 0))
            success_rect = success_title.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
            screen.blit(success_title, success_rect)
            
            id_text = FONT_SMALL.render(f"Bug报告ID: {report_id}", True, (255, 255, 255))
            id_rect = id_text.get_rect(center=(screen_width // 2, screen_height // 2 + 10))
            screen.blit(id_text, id_rect)
            
            thanks_text = FONT_SMALL.render("感谢您的反馈，我们会尽快处理！", True, (255, 215, 0))
            thanks_rect = thanks_text.get_rect(center=(screen_width // 2, screen_height // 2 + 50))
            screen.blit(thanks_text, thanks_rect)
            
            ok_btn = Button("确定", screen_width // 2 - 50, screen_height // 2 + 90, 100, 40, FONT_SMALL)
            ok_btn.check_hover(mouse_pos)
            ok_btn.draw(screen)
        
        back_btn.check_hover(mouse_pos)
        back_btn.draw(screen)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.rect.collidepoint(event.pos):
                    running = False
                
                if report_success:
                    if ok_btn.rect.collidepoint(event.pos):
                        report_success = False
                        report_id = None
                        for field in input_fields:
                            field["text"] = ""
                else:
                    if submit_btn.rect.collidepoint(event.pos):
                        title = input_fields[0]["text"].strip()
                        desc = input_fields[1]["text"].strip()
                        steps = input_fields[2]["text"].strip().split("\n") if input_fields[2]["text"] else []
                        user_info = {"contact": input_fields[3]["text"].strip()} if input_fields[3]["text"] else {}
                        
                        if title and desc:
                            report_id = report_bug(title, desc, steps, user_info=user_info)
                            log_info(f"玩家提交Bug: {title}")
                            report_success = True
                    
                    for field in input_fields:
                        field_y = field["y_offset"]
                        box_width = 400
                        box_height = 35
                        box_rect = pygame.Rect(screen_width // 2 - box_width // 2, field_y, box_width, box_height)
                        if box_rect.collidepoint(event.pos):
                            active_field = field
                            break
                    else:
                        active_field = None
            
            if event.type == pygame.KEYDOWN:
                if active_field and not report_success:
                    if event.key == pygame.K_BACKSPACE:
                        active_field["text"] = active_field["text"][:-1]
                    elif event.key == pygame.K_RETURN:
                        if active_field.get("is_desc"):
                            if len(active_field["text"]) + 1 <= active_field["max_len"]:
                                active_field["text"] += "\n"
                    elif len(active_field["text"]) < active_field["max_len"]:
                        active_field["text"] += event.unicode
        
        clock.tick(60)

if __name__ == "__main__":
    main()
