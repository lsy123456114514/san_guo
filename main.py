#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import platform

os.environ['SDL_VIDEO_CENTERED'] = '1'
os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
import pygame

def get_safe_resolution(screen_width, screen_height, min_width=640, min_height=360, ratio=0.8):
    """获取安全的窗口尺寸，确保不超出屏幕"""
    safe_width = int(screen_width * ratio)
    safe_height = int(screen_height * ratio)
    safe_width = max(min_width, safe_width)
    safe_height = max(min_height, safe_height)
    safe_width = min(safe_width, screen_width - 50)
    safe_height = min(safe_height, screen_height - 50)
    return safe_width, safe_height

def hide_file(filepath):
    """隐藏文件（仅Windows）"""
    if platform.system() == "Windows" and os.path.exists(filepath):
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(filepath, 0x02)
        except Exception:
            pass

# 导入反反编译保护模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'ASSET'))
from ASSET.anti_decompile import protect_function, anti_decompile

# 安卓路径适配
if 'ANDROID_DATA' in os.environ:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'ASSET'))
    # 安卓全屏
    pygame.init()
    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h
else:
    # 全局初始化
    pygame.init()
    info = pygame.display.Info()
    screen_width_full = info.current_w
    screen_height_full = info.current_h
    
    # 从设置中读取分辨率
    sys.path.append(os.path.join(os.path.dirname(__file__), 'ASSET'))
    from ASSET.game_data import SETTINGS
    resolution = SETTINGS['graphics']['resolution']
    try:
        SCREEN_WIDTH, SCREEN_HEIGHT = map(int, resolution.split('x'))
    except ValueError:
        # 默认分辨率：屏幕的 4/5，但不超过屏幕
        SCREEN_WIDTH, SCREEN_HEIGHT = get_safe_resolution(screen_width_full, screen_height_full)
    
    # 确保窗口不超出屏幕
    SCREEN_WIDTH = min(SCREEN_WIDTH, screen_width_full - 100)
    SCREEN_HEIGHT = min(SCREEN_HEIGHT, screen_height_full - 100)

# 全局初始化
pygame.mixer.init()
screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.FULLSCREEN if 'ANDROID_DATA' in os.environ else 0
)
pygame.display.set_caption("游戏主程序")
clock = pygame.time.Clock()

# 登录状态文件路径
LOGIN_STATE_PATH = os.path.join(os.path.dirname(__file__), "ASSET", "login_state.json")

# 保存登录状态
def save_login_state(username, user_data):
    """保存登录状态"""
    try:
        login_state = {
            "username": username,
            "user_data": user_data,
            "logged_in": True
        }
        with open(LOGIN_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(login_state, f, ensure_ascii=False, indent=2)
        hide_file(LOGIN_STATE_PATH)
    except Exception as e:
        import logging
        logging.error(f"保存登录状态失败: {e}")

# 加载登录状态
def load_login_state():
    """加载登录状态"""
    if os.path.exists(LOGIN_STATE_PATH):
        try:
            with open(LOGIN_STATE_PATH, "r", encoding="utf-8") as f:
                login_state = json.load(f)
                if login_state.get("logged_in", False):
                    return login_state["username"], login_state["user_data"]
        except Exception as e:
            import logging
            logging.error(f"加载登录状态失败: {e}")
    return None, None

# 清除登录状态
def clear_login_state():
    """清除登录状态"""
    try:
        if os.path.exists(LOGIN_STATE_PATH):
            os.remove(LOGIN_STATE_PATH)
    except Exception as e:
        import logging
        logging.error(f"清除登录状态失败: {e}")

# 启动登录系统
from ASSET.login_system import main as login_main
from ASSET.login_system import save_user_progress
from ASSET.game_main_menu import main as menu_main
from ASSET.game_data import data, save
from ASSET.dictionary_system import main as dictionary_main
from ASSET.whiteboard import main as whiteboard_main

# 导入启动动画
from ASSET.game_main_menu import startup_animation

@protect_function
def main_game():
    # 每次启动都显示词典系统（伪装界面），自适应窗口大小
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h
    width, height = get_safe_resolution(screen_w, screen_h, 800, 600)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("英语词典")

    # 运行词典系统
    result = dictionary_main(screen)

    # 检查返回值
    if result == "whiteboard":
        # 启动白板
        import ASSET.whiteboard as whiteboard_module
        pygame.display.set_caption("教学白板")
        whiteboard_module.main(screen)
        # 白板关闭后继续显示词典
        pygame.display.set_caption("英语词典")
        dictionary_main(screen)
    elif result:
        # 触发了游戏进入条件
        # 检查登录状态
        saved_username, saved_user_data = load_login_state()
        
        if saved_username and saved_user_data:
            # 有保存的登录状态，直接加载用户数据
            data.clear()
            data.update(saved_user_data)
            data["username"] = saved_username
            
            # 重新设置屏幕
            if 'ANDROID_DATA' in os.environ:
                # Android设备使用全屏
                info = pygame.display.Info()
                screen_width = info.current_w
                screen_height = info.current_h
                screen = pygame.display.set_mode((screen_width, screen_height))
            else:
                # PC设备根据设置
                resolution = data['settings']['graphics']['resolution']
                fullscreen = data['settings']['graphics']['fullscreen']
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    try:
                        width, height = map(int, resolution.split('x'))
                        screen = pygame.display.set_mode((width, height))
                    except ValueError:
                        screen = pygame.display.set_mode((800, 600))
            
            # 更新全局屏幕尺寸变量
            SCREEN_WIDTH = screen.get_width()
            SCREEN_HEIGHT = screen.get_height()
            
            # 确保时钟初始化
            clock = pygame.time.Clock()
            
            # 导入game_main_menu模块中的全局变量
            from ASSET.game_main_menu import screen as menu_screen, clock as menu_clock
            # 更新game_main_menu模块的全局变量
            import ASSET.game_main_menu
            ASSET.game_main_menu.screen = screen
            ASSET.game_main_menu.clock = clock
            
            # 运行启动动画
            startup_animation()
            
            # 显示游戏主程序
            pygame.display.set_caption("游戏主程序")
            
            # 运行主菜单
            menu_main()
            
            # 保存用户进度
            save_user_progress(saved_username, data)
            # 保留登录状态，不清除
        else:
            # 没有保存的登录状态，运行启动动画
            startup_animation()
            
            # 显示登录界面
            success, username, user_data = login_main()
            
            if success:
                # 登录成功，加载用户数据
                data.clear()
                data.update(user_data)
                data["username"] = username
                
                # 保存登录状态
                save_login_state(username, user_data)
                
                # 显示游戏主程序
                pygame.display.set_caption("游戏主程序")
                
                # 运行主菜单
                menu_main()
                
                # 保存用户进度
                save_user_progress(username, data)
                # 保留登录状态，不清除
            else:
                # 登录失败或退出，结束程序
                clear_login_state()
                pygame.quit()
                sys.exit(0)
    else:
        # 词典系统退出，结束程序
        pygame.quit()
        sys.exit(0)

if __name__ == '__main__':
    try:
        main_game()
    except Exception as e:
        print(f"启动失败：{str(e)}")
        print("详细错误信息：")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(0)
