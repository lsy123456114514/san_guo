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
    """优雅退出：适配安卓/PC。

    在异常分支中仅打印日志而不抛出，避免退出流程本身再次崩溃。
    """
    print(f"\n【退出】{module_name} 已关闭")
    if error:
        print(f"异常：{error}")
    if pygame.get_init():
        try:
            pygame.quit()
        except Exception as _e:
            logger.debug("[异常静默] pygame.quit: %s: %s", type(_e).__name__, _e)
    if 'ANDROID_DATA' in os.environ:
        try:
            import android
            android.exit()
        except Exception as _e:
            logger.debug("[异常静默] android.exit: %s: %s", type(_e).__name__, _e)
    else:
        sys.exit(0)


__all__ = ["safe_exit", "draw_gradient_bg", "cull_dead", "get_font", "logger"]
