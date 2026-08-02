#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import platform

# PyInstaller打包后的资源路径处理
def get_resource_path(relative_path):
    """获取资源文件路径（支持PyInstaller打包）"""
    try:
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
    except Exception:
        # 正常运行时的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

os.environ['SDL_VIDEO_CENTERED'] = '1'
os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
import pygame

# 添加ASSET路径
sys.path.append(get_resource_path('ASSET'))

# 导入配置管理器
from ASSET.config_manager import config_manager

def get_safe_resolution(screen_width, screen_height, min_width=640, min_height=400, ratio=0.75):
    """获取安全的窗口尺寸，确保不超出屏幕，留足够边距"""
    # 计算建议尺寸（屏幕的75%，留25%边距）
    safe_width = int(screen_width * ratio)
    safe_height = int(screen_height * ratio)
    
    # 确保不小于最小值
    safe_width = max(min_width, safe_width)
    safe_height = max(min_height, safe_height)
    
    # 确保不超过屏幕（留至少100像素边距）
    safe_width = min(safe_width, screen_width - 100)
    safe_height = min(safe_height, screen_height - 100)
    
    # 确保宽高比合理（4:3 ~ 16:9）
    aspect_ratio = safe_width / safe_height
    if aspect_ratio < 4/3:
        safe_width = int(safe_height * 4/3)
    elif aspect_ratio > 16/9:
        safe_height = int(safe_width * 9/16)
    
    return safe_width, safe_height

def validate_resolution(configured_width, configured_height):
    """验证并修正配置的分辨率，确保不会超出屏幕"""
    pygame.init()
    info = pygame.display.Info()
    screen_width_full = info.current_w
    screen_height_full = info.current_h
    
    # 如果配置的分辨率超过屏幕，自动调整
    if configured_width > screen_width_full - 50 or configured_height > screen_height_full - 50:
        print(f"配置分辨率 {configured_width}x{configured_height} 超过屏幕 {screen_width_full}x{screen_height_full}，自动调整...")
        return get_safe_resolution(screen_width_full, screen_height_full)
    
    # 确保最小值
    configured_width = max(640, configured_width)
    configured_height = max(360, configured_height)
    
    return configured_width, configured_height

def hide_file(filepath):
    """隐藏文件（仅Windows）"""
    if platform.system() == "Windows" and os.path.exists(filepath):
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(filepath, 0x02)
        except Exception:
            pass

# 导入反反编译保护模块
sys.path.append(get_resource_path('ASSET'))
from ASSET.anti_decompile import protect_function, anti_decompile

# 安卓路径适配
if 'ANDROID_DATA' in os.environ:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(get_resource_path('ASSET'))
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
    
    # 使用配置管理器获取安全的分辨率（适配小屏幕）
    SCREEN_WIDTH, SCREEN_HEIGHT = config_manager.get_safe_resolution(
        screen_width_full, screen_height_full
    )
    print(f"使用分辨率: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

# 全局初始化
pygame.mixer.init()
screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.FULLSCREEN if 'ANDROID_DATA' in os.environ else 0
)
pygame.display.set_caption("游戏主程序")
clock = pygame.time.Clock()

# 登录状态文件路径
LOGIN_STATE_PATH = get_resource_path("ASSET/login_state.json")

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
    global SCREEN_WIDTH, SCREEN_HEIGHT
    
    # 每次启动都显示词典系统（伪装界面），自适应窗口大小
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h
    width, height = get_safe_resolution(screen_w, screen_h, 600, 400)
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
            
            # 使用安全的屏幕尺寸
            info = pygame.display.Info()
            screen_w, screen_h = info.current_w, info.current_h
            width, height = get_safe_resolution(screen_w, screen_h, 600, 400)
            
            if 'ANDROID_DATA' in os.environ:
                # Android设备使用全屏
                screen = pygame.display.set_mode((screen_w, screen_h))
            else:
                # PC设备根据设置
                resolution = data['settings']['graphics']['resolution']
                fullscreen = data['settings']['graphics']['fullscreen']
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    try:
                        cfg_width, cfg_height = map(int, resolution.split('x'))
                        width, height = get_safe_resolution(cfg_width, cfg_height, 600, 400)
                        screen = pygame.display.set_mode((width, height))
                    except ValueError:
                        screen = pygame.display.set_mode((width, height))
            
            # 更新全局屏幕尺寸变量
            SCREEN_WIDTH = screen.get_width()
            SCREEN_HEIGHT = screen.get_height()
            
            # 确保时钟初始化
            clock = pygame.time.Clock()
            
            # 更新game_main_menu模块的全局变量
            import ASSET.game_main_menu
            ASSET.game_main_menu.screen = screen
            ASSET.game_main_menu.clock = clock
            ASSET.game_main_menu.SCREEN_WIDTH = SCREEN_WIDTH
            ASSET.game_main_menu.SCREEN_HEIGHT = SCREEN_HEIGHT
            
            # 运行启动动画
            try:
                startup_animation()
            except Exception as e:
                print(f"启动动画失败: {e}")
            
            # 显示游戏主程序
            pygame.display.set_caption("游戏主程序")
            
            # 运行主菜单
            try:
                menu_main()
            except Exception as e:
                print(f"主菜单运行失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 保存用户进度
            save_user_progress(saved_username, data)
            # 保留登录状态，不清除
        else:
            # 没有保存的登录状态，运行启动动画
            try:
                startup_animation()
            except Exception as e:
                print(f"启动动画失败: {e}")
            
            # 显示登录界面
            success, username, user_data = login_main()
            
            if success:
                # 登录成功，加载用户数据
                data.clear()
                data.update(user_data)
                data["username"] = username
                
                # 保存登录状态
                save_login_state(username, user_data)
                
                # 使用安全的屏幕尺寸
                info = pygame.display.Info()
                screen_w, screen_h = info.current_w, info.current_h
                width, height = get_safe_resolution(screen_w, screen_h, 600, 400)
                
                if 'ANDROID_DATA' in os.environ:
                    screen = pygame.display.set_mode((screen_w, screen_h))
                else:
                    resolution = data['settings']['graphics']['resolution']
                    fullscreen = data['settings']['graphics']['fullscreen']
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        try:
                            cfg_width, cfg_height = map(int, resolution.split('x'))
                            width, height = get_safe_resolution(cfg_width, cfg_height, 600, 400)
                            screen = pygame.display.set_mode((width, height))
                        except ValueError:
                            screen = pygame.display.set_mode((width, height))
                
                # 更新全局变量
                SCREEN_WIDTH = screen.get_width()
                SCREEN_HEIGHT = screen.get_height()
                
                import ASSET.game_main_menu
                ASSET.game_main_menu.screen = screen
                ASSET.game_main_menu.clock = pygame.time.Clock()
                ASSET.game_main_menu.SCREEN_WIDTH = SCREEN_WIDTH
                ASSET.game_main_menu.SCREEN_HEIGHT = SCREEN_HEIGHT
                
                # 显示游戏主程序
                pygame.display.set_caption("游戏主程序")
                
                # 运行主菜单
                try:
                    menu_main()
                except Exception as e:
                    print(f"主菜单运行失败: {e}")
                    import traceback
                    traceback.print_exc()
                
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
