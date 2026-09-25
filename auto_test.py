#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键自动测试 — 模拟手动操作，逐个点击各模块进入并退出
========================================================

用法（项目根目录）::

    py auto_test.py

测试流程::

    1. 备份存档 → 启动真实主菜单（跳过开场动画与新手引导）
    2. AutoTestDriver 每帧驱动一步：
         移动光标到下拉菜单 → 展开 → 逐项悬停 → 点击进入模块
    3. 每个模块由看门狗线程投递 ESC/QUIT 事件使其自动退出
    4. 记录 OK / FAIL / HANG，写入 auto_test_report.txt
    5. 全部走完后发送 QUIT 退出主菜单，恢复存档，输出汇总

退出码::

    0 = 全部通过   1 = 有失败   2 = 有模块挂起（看门狗超时强杀）
"""

import os
import sys
import time
import shutil
import logging
import threading

# ══════════════════════════════════════════════════════════════
# 常量
# ══════════════════════════════════════════════════════════════

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(ROOT, "auto_test_report.txt")
SAVE_PATH = os.path.join(ROOT, "ASSET", "save.json")

# 不自动点击的菜单码：存档对话框 / 设置 / 退出确认 / 读档（含弹窗或会结束进程）
SKIP_CODES = {"4", "5", "9", "15"}

DELAY_OPEN = 0.35     # 展开下拉菜单后的停留（秒）
DELAY_HOVER = 0.25    # 悬停到条目上的停留
DELAY_SCROLL = 0.12   # 长列表滚动一格的间隔
DELAY_SETTLE = 0.70   # 模块退出后回到菜单的安定时间

WATCHDOG_START = 1.0     # 模块启动多久后开始投递退出事件
WATCHDOG_INTERVAL = 0.35 # 退出事件投递间隔
HANG_TIMEOUT = 90.0      # 无任何进展多久判定为挂起

STATE_OPEN = "open"
STATE_FIND = "find"
STATE_HOVER = "hover"
STATE_CLICK = "click"
STATE_AFTER = "after"

_results = []          # [(file, label, status, elapsed, note)]
_heartbeat = {"t": time.perf_counter()}
_current = {"label": "", "file": ""}
_report_lock = threading.Lock()


# ══════════════════════════════════════════════════════════════
# 报告
# ══════════════════════════════════════════════════════════════

def _report(line: str, echo: bool = True) -> None:
    """追加一行到报告文件（并可选打印到控制台）。"""
    with _report_lock:
        try:
            with open(REPORT_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
    if echo:
        try:
            print(line, flush=True)
        except Exception:
            pass


def _init_report() -> None:
    """覆盖写入报告头。"""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    header = (
        "==== 三国群英传 · 一键自动测试 ====\n"
        f"start: {stamp}\n"
        f"mode  : 模拟手动点击，逐模块进入并退出\n"
        "------------------------------------\n"
    )
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(header)
    print(header, end="", flush=True)


# ══════════════════════════════════════════════════════════════
# 看门狗：让子模块自动退出
# ══════════════════════════════════════════════════════════════

class _Watchdog(threading.Thread):
    """模块运行期间持续投递 ESC/QUIT，使其自动退回主菜单。"""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self._stop_flag = False

    def stop(self) -> None:
        self._stop_flag = True

    def run(self) -> None:
        time.sleep(WATCHDOG_START)
        flip = 0
        while not self._stop_flag:
            try:
                import pygame
                if flip % 2 == 0:
                    ev = pygame.event.Event(pygame.KEYDOWN,
                                            key=pygame.K_ESCAPE, unicode="", mod=0)
                else:
                    ev = pygame.event.Event(pygame.QUIT)
                pygame.event.post(ev)
            except Exception:
                pass
            flip += 1
            time.sleep(WATCHDOG_INTERVAL)


# ══════════════════════════════════════════════════════════════
# 自动测试驱动（被 game_main_menu.main() 装载）
# ══════════════════════════════════════════════════════════════

class AutoTestDriver:
    """
    主菜单帧驱动器。

    每帧推进一个状态：展开下拉 → 定位条目（含滚动）→
    悬停光标 → 点击进入（模块同步运行，退出后回到这里）→ 下一项。
    全部完成后向主菜单投递 QUIT 结束测试。
    """

    def __init__(self) -> None:
        self.menu_elements = None
        self.activate = None
        self.queue = []          # [(code, label, dropdown_title)]
        self.idx = 0
        self.state = STATE_OPEN
        self.next_at = 0.0
        self.finished = False
        self.entered = 0

    # ── 组装目标队列 ──────────────────────────────────

    def bind(self, menu_elements, activate_code) -> None:
        """绑定菜单元素与激活函数，按菜单顺序生成待点队列。"""
        import pygame  # noqa: F401  确保已初始化
        self.menu_elements = menu_elements
        self.activate = activate_code

        from ASSET.game_main_menu import MODULE_ROUTES, SPECIAL_HANDLERS
        seen_files = set()
        for etype, el in menu_elements:
            if etype != "dropdown":
                continue
            for text, code in el.items:
                mod_file = MODULE_ROUTES.get(code)
                if mod_file is None and code in SPECIAL_HANDLERS:
                    mod_file = f"special:{code}"  # 小游戏中心等特殊入口
                if not mod_file or code in SKIP_CODES:
                    continue
                if mod_file in seen_files:
                    continue  # 同一模块文件只测一次（如 28/34 都是 3D 地图）
                seen_files.add(mod_file)
                # 只存下拉标题：子模块退出后菜单会被重建，旧对象引用会失效
                self.queue.append((code, text, el.text))

        total = len(self.queue)
        _report(f"计划点击 {total} 个模块（跳过存档/设置/退出类菜单项）")
        _report("------------------------------------")

    def _dropdown(self, title: str):
        """按标题从当前 menu_elements 解析下拉对象（菜单可能已被重建）。"""
        if self.menu_elements is None:
            return None
        for etype, el in self.menu_elements:
            if etype == "dropdown" and el.text == title:
                return el
        return None

    # ── 帧驱动 ────────────────────────────────────────

    def step(self) -> None:
        """每帧调用一次；内部按延时推进状态机。"""
        _heartbeat["t"] = time.perf_counter()
        if self.finished:
            return
        if self.idx >= len(self.queue):
            self._finish()
            return
        now = time.perf_counter()
        if now < self.next_at:
            return

        code, label, dd_title = self.queue[self.idx]
        import pygame
        # 状态/目标变化时落盘时间戳（仅文件），用于定位状态机卡顿
        key = (self.idx, self.state)
        if getattr(self, "_dbg_key", None) != key:
            self._dbg_key = key
            _report(f"[drv {time.strftime('%H:%M:%S')}] idx={self.idx} "
                    f"state={self.state} target={label}", echo=False)
        dd = self._dropdown(dd_title)
        if dd is None:
            _report(f"[SKIP] 找不到下拉「{dd_title}」，跳过 {label}")
            self._advance()
            return

        if self.state == STATE_OPEN:
            # 光标移到下拉标题并展开
            pygame.mouse.set_pos(dd.rect.center)
            dd.is_open = True
            self.state = STATE_FIND
            self.next_at = now + DELAY_OPEN

        elif self.state == STATE_FIND:
            # 在展开列表中定位目标（超出可视区则滚动）
            if not dd.is_open:
                # 上一个模块退出后菜单被整体重建，下拉已复位为关闭
                dd.is_open = True
                pygame.mouse.set_pos(dd.rect.center)
            sw, sh = pygame.display.get_surface().get_size()
            dd.update_items(sw, sh)
            codes = [c for _, c, _ in dd.dropdown_items]
            if code in codes:
                rect = next(r for _, c, r in dd.dropdown_items if c == code)
                pygame.mouse.set_pos(rect.center)
                self.state = STATE_HOVER
                self.next_at = now + DELAY_HOVER
            else:
                dd.scroll(1, sh)
                dd.update_items(sw, sh)
                if not dd.dropdown_items:
                    # 滚到底仍找不到：跳过（防御）
                    _report(f"[SKIP] {label} ({code}) 在菜单中不可见")
                    self._advance()
                else:
                    self.next_at = now + DELAY_SCROLL

        elif self.state == STATE_HOVER:
            # 模拟点击：直接进入（激活函数内部会同步运行模块）
            _current["label"] = label
            _current["file"] = MODULE_ROUTES_FILE(code)
            # 先落盘再进入：若模块硬崩（如 0xC0000005），报告里能看出崩在谁身上
            _report(f"-> 进入 {label} ({code}) {MODULE_ROUTES_FILE(code)}", echo=False)
            self.activate(code)
            # 走到这里 = 模块已退回主菜单
            self.entered += 1
            _heartbeat["t"] = time.perf_counter()
            self.state = STATE_AFTER
            self.next_at = time.perf_counter() + DELAY_SETTLE

        elif self.state == STATE_AFTER:
            # 判断下一个目标是否仍在同一个下拉里
            self.idx += 1
            if self.idx >= len(self.queue):
                self._finish()
                return
            _, _, next_title = self.queue[self.idx]
            if next_title == dd_title:
                self.state = STATE_FIND  # 下拉保持展开，直接找下一项
                self.next_at = now + DELAY_HOVER
            else:
                dd.is_open = False
                dd.scroll_index = 0
                self.state = STATE_OPEN
                self.next_at = now + DELAY_SETTLE

    def _advance(self) -> None:
        """跳过当前目标，复用 AFTER 的推进逻辑。"""
        self.state = STATE_AFTER
        self.next_at = time.perf_counter()

    def _finish(self) -> None:
        """全部点击完成：关闭菜单并投递 QUIT 结束主菜单循环。"""
        import pygame
        for etype, el in self.menu_elements:
            if etype == "dropdown":
                el.is_open = False
        self.finished = True
        _report("------------------------------------")
        _report(f"点击完成，共进入 {self.entered} 个模块，正在退出主菜单…")
        try:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        except Exception:
            pass


def MODULE_ROUTES_FILE(code: str) -> str:
    """取菜单码对应的模块文件名（用于报告）。"""
    try:
        from ASSET.game_main_menu import MODULE_ROUTES
        return MODULE_ROUTES.get(code, code)
    except Exception:
        return code


# ══════════════════════════════════════════════════════════════
# run_module / SPECIAL_HANDLERS 包装：计时 + 错误捕获 + 看门狗
# ══════════════════════════════════════════════════════════════

class _ErrorRecorder(logging.Handler):
    """记录模块运行期间的 ERROR 级日志，用于判定 FAIL。"""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self.messages = []

    def emit(self, record) -> None:
        try:
            self.messages.append(record.getMessage())
        except Exception:
            pass


def _make_wrapper(orig_fn, kind: str):
    """包装 run_module / 特殊处理器，套上看门狗与结果记录。"""

    def wrapper(*args):
        import pygame

        rec = _ErrorRecorder()
        root = logging.getLogger()
        root.addHandler(rec)
        # 模块日志多挂在 "ASSET" 系 logger 上（可能 propagate=False），
        # 两边都挂确保 ERROR 逃不过判定
        aset_logger = logging.getLogger("ASSET")
        aset_logger.addHandler(rec)
        wd = _Watchdog()
        wd.start()
        t0 = time.perf_counter()
        _heartbeat["t"] = t0
        status, note = "OK", ""
        target = args[0] if args else kind
        _current["file"] = target if isinstance(target, str) else str(target)
        try:
            orig_fn(*args)
        except SystemExit:
            status = "OK"
            note = "SystemExit(已吞)"
        except Exception as e:
            status = "FAIL"
            note = f"抛出异常: {type(e).__name__}: {e}"
        finally:
            wd.stop()
            wd.join(timeout=1.0)
            # 清掉看门狗可能残留的退出事件，避免误杀主菜单
            time.sleep(0.05)
            try:
                pygame.event.clear()
            except Exception:
                pass
            root.removeHandler(rec)
            aset_logger.removeHandler(rec)
        elapsed = time.perf_counter() - t0

        if status == "OK" and rec.messages:
            status = "FAIL"
            note = rec.messages[0][:160]

        name = target if isinstance(target, str) else getattr(target, "__name__", str(target))
        label = _current["label"] or ""
        _results.append((name, label, status, elapsed, note))
        _report(f"[{status}] {elapsed:6.2f}s  {name}  ({label})" +
                (f"  — {note}" if note else ""))
        _heartbeat["t"] = time.perf_counter()

    return wrapper


# ══════════════════════════════════════════════════════════════
# 看门狗之上的死监控：模块彻底挂起时强杀并记 HANG
# ══════════════════════════════════════════════════════════════

def _deadman() -> None:
    while True:
        time.sleep(5)
        stale = time.perf_counter() - _heartbeat["t"]
        if stale > HANG_TIMEOUT:
            _report(f"[HANG] 超过 {int(stale)}s 无进展，疑似挂在 "
                    f"{_current['file']} ({_current['label']})")
            _report("exit  : 2 (挂起强杀)")
            # 尽力恢复存档备份
            try:
                bak = SAVE_PATH + ".autotest_bak"
                if os.path.exists(bak):
                    shutil.move(bak, SAVE_PATH)
            except Exception:
                pass
            os._exit(2)


# ══════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════

def run() -> int:
    """执行一键自动测试，返回退出码。"""
    os.environ["SAN_GUO_AUTOTEST"] = "1"
    os.chdir(ROOT)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    # 关键：本脚本以 __main__ 运行，而 game_main_menu 里 `from auto_test import`
    # 会再加载一份同名模块，导致 _current/_results/_heartbeat 两套实例互不相通。
    # 这里把 __main__ 注册为 auto_test，保证全进程只有这一个实例。
    sys.modules["auto_test"] = sys.modules[__name__]

    _init_report()

    # 备份存档，测试结束后恢复
    save_backup = None
    if os.path.exists(SAVE_PATH):
        save_backup = SAVE_PATH + ".autotest_bak"
        shutil.copy2(SAVE_PATH, save_backup)

    # 死监控先行
    threading.Thread(target=_deadman, daemon=True).start()

    exit_code = 0
    try:
        import pygame
        import ASSET.game_main_menu as gmm

        # 跳过开场动画（5 秒）与新手引导
        if hasattr(gmm, "startup_animation"):
            gmm.startup_animation = lambda *a, **k: None
        try:
            gmm.data["tutorial_completed"] = True
        except Exception:
            pass

        # 包装模块入口：计时 + 错误捕获 + 看门狗自动退出
        gmm.run_module = _make_wrapper(gmm.run_module, "module")
        for _code, _fn in list(gmm.SPECIAL_HANDLERS.items()):
            gmm.SPECIAL_HANDLERS[_code] = _make_wrapper(_fn, "special")

        # 跑真实主菜单，由 AutoTestDriver 驱动点击
        gmm.main()

    except Exception as e:
        _report(f"[CRASH] 主流程异常: {type(e).__name__}: {e}")
        import traceback
        _report(traceback.format_exc())
        exit_code = 1
    finally:
        # 恢复存档
        try:
            if save_backup and os.path.exists(save_backup):
                shutil.move(save_backup, SAVE_PATH)
        except Exception:
            pass

    # 汇总
    ok = sum(1 for r in _results if r[2] == "OK")
    fail = len(_results) - ok
    _report("------------------------------------")
    _report(f"summary : 共 {len(_results)} 个模块，OK {ok}，FAIL {fail}")
    if fail and exit_code == 0:
        exit_code = 1
    _report(f"exit    : {exit_code}")
    _report(f"report  : {REPORT_PATH}")
    return exit_code


def main() -> None:
    """控制台入口。"""
    sys.exit(run())


if __name__ == "__main__":
    main()
