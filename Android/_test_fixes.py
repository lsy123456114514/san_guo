# -*- coding: utf-8 -*-
"""子进程逐个测试修改过的模块 main() 入口（dummy 驱动 + 3 秒后自动退出）"""
import subprocess
import sys

ROOT = r"C:\Users\a\Desktop\san_guo\Android"
MODULES = [
    "pet_system", "social_system", "fashion_system", "weather_system",
    "achievement_system", "ranking_system", "daily_checkin", "quest_system",
    "talent_system", "equipment_system", "alchemy_system", "hero_recruitment",
]

RUNNER = r'''
import os, sys, time
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
pygame.init()
pygame.display.set_mode((900, 700))
mod = __import__("ASSET.%s", fromlist=["*"])
import threading
def _q():
    time.sleep(3)
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    except Exception:
        pass
threading.Thread(target=_q, daemon=True).start()
try:
    mod.main()
    print("RESULT: OK")
except SystemExit:
    print("RESULT: EXIT")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("RESULT: FAIL")
'''

failed = []
for m in MODULES:
    print("=" * 40)
    print("测试:", m)
    code = RUNNER % m
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, cwd=ROOT, timeout=70,
        )
        tail = (r.stdout or "")[-800:] + (r.stderr or "")[-800:]
        if "RESULT: OK" in tail or "RESULT: EXIT" in tail:
            print("PASS")
        elif "RESULT: FAIL" in tail:
            print("FAIL")
            failed.append(m)
        else:
            print("TIMEOUT/NO-MARKER")
            failed.append(m)
        print(tail)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        failed.append(m)
    except Exception as e:
        print("RUN-ERR:", e)
        failed.append(m)

print("=" * 40)
if failed:
    print("失败模块:", failed)
else:
    print("全部通过")
