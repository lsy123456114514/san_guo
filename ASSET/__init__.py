"""ASSET 包入口 - 模块导出与安全退出工具

提供以下公共能力：
    1. safe_exit: 优雅退出（适配安卓/PC，捕获并打印异常后退出）
    2. draw_gradient_bg / cull_dead / get_font: 由 game_data 模块再导出，供子系统直接 `from ASSET import ...` 使用
"""

import os
import sys
import pygame
from ASSET.game_data import draw_gradient_bg, cull_dead, get_font, logger


def safe_exit(module_name="模块", error=""):
    """安全退出当前模块，返回主菜单（不终止进程）。

    子模块调用此函数后应 return，让 run_module() 正常返回主菜单。
    主菜单自身的退出由 main.py 末尾的 sys.exit(0) 处理。
    """
    print(f"\n【退出】{module_name} 已关闭")
    if error:
        print(f"异常：{error}")
    if pygame.get_init():
        try:
            pygame.quit()
        except Exception as _e:
            logger.debug("[异常静默] pygame.quit: %s: %s", type(_e).__name__, _e)
        # 重新初始化 pygame，让主菜单可以继续使用
        try:
            pygame.init()
        except Exception as _e:
            logger.debug("[异常静默] pygame.init: %s: %s", type(_e).__name__, _e)
    if 'ANDROID_DATA' in os.environ:
        try:
            import android
            android.exit()
        except Exception as _e:
            logger.debug("[异常静默] android.exit: %s: %s", type(_e).__name__, _e)


__all__ = ["safe_exit", "draw_gradient_bg", "cull_dead", "get_font", "logger"]
