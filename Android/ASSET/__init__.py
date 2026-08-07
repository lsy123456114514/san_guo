import os
import sys
import pygame
from ASSET.game_data import draw_gradient_bg, cull_dead, get_font

def safe_exit(module_name="模块", error=""):
    """优雅退出：适配安卓/PC"""
    print(f"\n【退出】{module_name} 已关闭")
    if error:
        print(f"异常：{error}")
    if pygame.get_init():
        pygame.quit()
    if 'ANDROID_DATA' in os.environ:
        try:
            import android
            android.exit()
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
    else:
        sys.exit(0)

__all__ = ["safe_exit"]
