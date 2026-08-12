# -*- coding: utf-8 -*-
"""验证：3D地图(OpenGL表面)返回后，run_module 的恢复逻辑能否重建普通窗口"""
import os, sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

def main():
    pygame.init()
    pygame.display.set_caption("test")
    # 模拟主菜单普通窗口
    screen = pygame.display.set_mode((1280, 720))
    print("[1] 主菜单窗口 OK, flags=%s" % hex(screen.get_flags()))

    # 模拟 3D 地图切换到 OpenGL
    gl_surface = pygame.display.set_mode((1024, 768), pygame.OPENGL | pygame.DOUBLEBUF)
    print("[2] OpenGL 表面 OK, flags=%s" % hex(gl_surface.get_flags()))
    cur = pygame.display.get_surface()
    print("[3] get_surface flags=%s, is_opengl=%s" % (hex(cur.get_flags()), bool(cur.get_flags() & pygame.OPENGL)))

    # 模拟 run_module 恢复逻辑
    pygame.event.clear()
    try:
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        cur_surface = pygame.display.get_surface()
        is_opengl = bool(cur_surface) and bool(cur_surface.get_flags() & pygame.OPENGL)
        print("[4] 恢复检测: cur_surface=%s, is_opengl=%s" % (cur_surface, is_opengl))
        if cur_surface is None or is_opengl:
            old_w, old_h = (screen.get_width(), screen.get_height()) if screen else (800, 600)
            screen = pygame.display.set_mode((old_w, old_h))
            print("[5] 已重建普通窗口 %dx%d, flags=%s" % (old_w, old_h, hex(screen.get_flags())))
    except Exception as _e:
        print("[ERR] 恢复异常: %s: %s" % (type(_e).__name__, _e))
        pygame.quit()
        return 1

    # 验证普通 blit 是否正常
    try:
        screen.fill((30, 30, 30))
        pygame.display.flip()
        print("[6] 普通窗口渲染 OK")
    except Exception as _e:
        print("[ERR] 渲染异常: %s: %s" % (type(_e).__name__, _e))
        pygame.quit()
        return 1

    pygame.quit()
    print("[OK] 全部通过")
    return 0

if __name__ == "__main__":
    sys.exit(main())
