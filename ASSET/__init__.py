import os
import sys
import pygame

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
        except Exception:
            pass
    else:
        sys.exit(0)

__all__ = ["safe_exit"]
