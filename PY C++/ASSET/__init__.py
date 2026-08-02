import os
import sys
import pygame

# 全局退出标志
EXIT_FLAG = False

def safe_exit(module_name="模块", error=""):
    """优雅退出：适配安卓/PC，不再直接退出程序，改为设置退出标志"""
    global EXIT_FLAG
    print(f"\n【退出】{module_name} 已关闭")
    if error:
        print(f"异常：{error}")

    # 清理 pygame 显示和音频（不调用pygame.quit()避免影响主程序）
    if pygame.get_init():
        try:
            pygame.display.quit()
            pygame.mixer.quit()
        except Exception:
            pass

    # 安卓特殊处理
    if 'ANDROID_DATA' in os.environ:
        try:
            import android
            android.exit()
        except Exception:
            pass

    # 设置退出标志，由主程序处理退出
    EXIT_FLAG = True

__all__ = ["safe_exit", "EXIT_FLAG"]
