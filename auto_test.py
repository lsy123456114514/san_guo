#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键自动测试 — 模拟手动操作，逐个点击各模块进入并退出
========================================================

用法（项目根目录）::

    py auto_test.py                 # 图形界面（双击 exe 同效）：勾选模块、看日志
    py auto_test.py --all           # 无界面全量测试（脚本 / agent 后台运行）
    py auto_test.py --list          # 只列出计划点击的菜单项，不执行
    py auto_test.py --only 23,17    # 只测指定菜单码
    py auto_test.py --rounds 3      # 连测 3 轮（查偶发问题）
    py auto_test.py --fast          # 压缩界面延时，跑得更快
    py auto_test.py --keep-save     # 不备份/恢复存档（保留测试改动）
    py auto_test.py --gui           # 强制打开图形界面（忽略其余参数）

分发规则::

    无参数或带 --gui → tkinter 图形界面（子进程跑测试，GUI 转播报告文件）
    带任何其它参数   → 无界面 CLI，直接前台运行（stdout 不可用时自动恢复）

测试流程::

    1. 备份存档 → 启动真实主菜单（跳过开场动画与新手引导）
    2. AutoTestDriver 每帧驱动一步：
         移动光标到下拉菜单 → 展开 → 逐项悬停 → 点击进入模块
    3. 每个模块先由看门狗投递一轮“按键漫游”（方向/Tab/空格/回车/数字），
       再交替投递 ESC/QUIT 使其自动退出——顺带覆盖模块内部交互
    4. 记录 OK / FAIL / HANG；若上次进程硬崩（段错误等），本轮报告会点名
    5. 全部走完后发送 QUIT 退出主菜单，恢复存档，输出明细与汇总

退出码::

    0 = 全部通过   1 = 有失败   2 = 有模块挂起（看门狗超时强杀）
    3 = 已有实例在运行（报告文件被占用）
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
import re
import threading

# ══════════════════════════════════════════════════════════════
# 常量
# ══════════════════════════════════════════════════════════════

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(ROOT, "auto_test_report.txt")
SAVE_PATH = os.path.join(ROOT, "ASSET", "save.json")
STATE_PATH = os.path.join(ROOT, "auto_test_state.json")
SHOT_DIR = os.path.join(ROOT, "test_shots")
SHOT_TIMES = (0.5, 1.6, 4.0)   # --shots 时：进模块后第几秒截图（布局期 / 漫游期 / 慢启动模块）

# 不自动点击的菜单码：存档对话框 / 设置 / 退出确认 / 读档（含弹窗或会结束进程）
SKIP_CODES = {"4", "5", "9", "15"}

DELAY_OPEN = 0.35     # 展开下拉菜单后的停留（秒）
DELAY_HOVER = 0.25    # 悬停到条目上的停留
DELAY_SCROLL = 0.12   # 长列表滚动一格的间隔
DELAY_SETTLE = 0.70   # 模块退出后回到菜单的安定时间

WATCHDOG_START = 1.0     # 模块启动多久后开始投递事件
WATCHDOG_INTERVAL = 0.35 # ESC/QUIT 投递间隔
SPRAY_DURATION = 1.6     # 进入模块后先“按键漫游”的时长（秒）
SPRAY_INTERVAL = 0.20    # 漫游按键投递间隔
HANG_TIMEOUT = 90.0      # 无任何进展多久判定为挂起

STATE_OPEN = "open"
STATE_FIND = "find"
STATE_HOVER = "hover"
STATE_CLICK = "click"
STATE_AFTER = "after"

_results = []          # [(file, label, status, elapsed, note)]
_heartbeat = {"t": time.perf_counter()}
_current = {"label": "", "file": "", "code": ""}
_report_lock = threading.Lock()
_opts = None           # argparse 选项（run() 里赋值，驱动器从中读取）
_driver = {"obj": None}  # 当前驱动器实例（gmm.main() 内创建，run() 检查完成状态）


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


def _git_rev() -> str:
    """取当前 git 短提交号（失败返回 unknown）。"""
    try:
        import subprocess
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             cwd=ROOT, capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _init_report() -> None:
    """覆盖写入报告头。"""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    args = " ".join(sys.argv[1:]) or "(无)"
    header = (
        "==== 三国群英传 · 一键自动测试 ====\n"
        f"start   : {stamp}\n"
        f"python  : {sys.version.split()[0]}  platform: {sys.platform}  "
        f"git: {_git_rev()}\n"
        f"args    : {args}\n"
        f"mode    : 菜单点击 + 模块内按键漫游，逐模块进入并退出\n"
        "------------------------------------\n"
    )
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(header)
    print(header, end="", flush=True)


def _write_state(code: str, label: str, mod_file: str) -> None:
    """进入模块前落盘状态标记：进程硬崩（段错误等）时残留，供下轮点名。"""
    try:
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "code": code, "label": label,
                       "file": mod_file, "t": time.strftime("%Y-%m-%d %H:%M:%S")},
                      f, ensure_ascii=False)
        os.replace(tmp, STATE_PATH)
    except Exception:
        pass


def _clear_state() -> None:
    try:
        if os.path.exists(STATE_PATH):
            os.remove(STATE_PATH)
    except Exception:
        pass


# ── 截图：挂在 display.flip/update 上，只在“整帧画完、即将翻页”时保存 ──
# 旧实现用后台线程到点直接读屏幕，会截到渲染到一半的帧（表现为“内容丢失”假象）。
_pending_shots = []      # [{"deadline": float, "path": str}]
_shot_hooked = {"on": False}


def _install_shot_hook() -> None:
    """把截图动作插到 pygame.display.flip/update 调用之前（帧内容最完整的一刻）。"""
    if _shot_hooked["on"]:
        return
    _shot_hooked["on"] = True
    try:
        import pygame

        orig_flip = pygame.display.flip
        orig_update = pygame.display.update

        def _grab_surface():
            """取当前帧画面。OPENGL 模式下 display surface 不含 GL 内容，
            需在翻页前直接从帧缓冲 glReadPixels 读取（翻页前读的是 BACK 缓冲）。"""
            surf = pygame.display.get_surface()
            if surf is None:
                return None
            if not (surf.get_flags() & pygame.OPENGL):
                return surf
            if threading.current_thread() is not threading.main_thread():
                return surf  # 非主线程没有当前 GL 上下文，读不了
            try:
                from OpenGL.GL import glReadPixels, glFinish, GL_RGB, GL_UNSIGNED_BYTE
                import ctypes

                w, h = surf.get_size()
                glFinish()
                buf = (ctypes.c_ubyte * (w * h * 3))()
                glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, buf)
                gl_surf = pygame.image.frombuffer(bytes(buf), (w, h), "RGB")
                return pygame.transform.flip(gl_surf, False, True)
            except Exception:
                return surf

        def _save_due():
            if not _pending_shots:
                return
            now = time.perf_counter()
            for shot in list(_pending_shots):
                if now < shot["deadline"]:
                    continue
                _pending_shots.remove(shot)
                try:
                    surf = _grab_surface()
                    if surf is not None:
                        os.makedirs(SHOT_DIR, exist_ok=True)
                        pygame.image.save(surf, shot["path"])
                except Exception:
                    pass

        def flip(*a, **k):
            _save_due()
            return orig_flip(*a, **k)

        def update(*a, **k):
            _save_due()
            return orig_update(*a, **k)

        pygame.display.flip = flip
        pygame.display.update = update
    except Exception:
        pass


def _take_shot_async(tag: str, delay: float) -> None:
    """delay 秒后截当前窗口存为 test_shots/<code>_<label>_<tag>.png。"""
    code = _current.get("code") or "0"
    label = (_current.get("label") or "unknown").strip()
    for ch in '\\/:*?"<>|':
        label = label.replace(ch, "_")
    path = os.path.join(SHOT_DIR, f"{code}_{label}_{tag}.png")

    _install_shot_hook()
    _pending_shots.append({"deadline": time.perf_counter() + delay, "path": path})

    def _worker():
        # 兜底：deadline+1.5s 还没翻过页（模块卡死/无帧）就直接读屏，聊胜于无
        time.sleep(delay + 1.5)
        for shot in list(_pending_shots):
            if shot["path"] == path:
                _pending_shots.remove(shot)
                try:
                    import pygame
                    surf = pygame.display.get_surface()
                    if surf is not None:
                        if surf.get_flags() & pygame.OPENGL:
                            # GL 模式非主线程读不到帧缓冲，白图没意义，留给翻页钩子
                            continue
                        os.makedirs(SHOT_DIR, exist_ok=True)
                        pygame.image.save(surf, path)
                except Exception:
                    pass

    threading.Thread(target=_worker, daemon=True).start()


def _cancel_pending_shots() -> None:
    """模块结束时丢掉未拍的截图，避免拍到主菜单却顶着模块的文件名。"""
    _pending_shots.clear()


def _check_stale_state() -> None:
    """上轮进程硬崩时状态文件会残留 → 在本轮报告开头点名。"""
    if not os.path.exists(STATE_PATH):
        return
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            st = json.load(f)
        _report(f"[CRASH] 上次运行进程硬崩于 {st.get('label', '?')} "
                f"({st.get('code', '?')}) {st.get('file', '?')}  "
                f"@{st.get('t', '?')}，本轮重点观察")
    except Exception:
        _report("[CRASH] 上次运行残留状态文件（无法解析）")
    _clear_state()


# ══════════════════════════════════════════════════════════════
# 看门狗：让子模块自动退出
# ══════════════════════════════════════════════════════════════

class _Watchdog(threading.Thread):
    """模块运行期间自动投递按键：先漫游交互，再 ESC/QUIT 退出。"""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self._stop_flag = False

    def stop(self) -> None:
        self._stop_flag = True

    def run(self) -> None:
        try:
            import pygame
        except Exception:
            return
        time.sleep(WATCHDOG_START)
        # 漫游按键：模拟玩家在模块里随便按，覆盖内部交互路径
        spray_keys = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                      pygame.K_TAB, pygame.K_RETURN, pygame.K_SPACE,
                      pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_BACKSPACE]
        spray_unicode = {pygame.K_RETURN: "\r", pygame.K_SPACE: " ",
                         pygame.K_TAB: "\t", pygame.K_1: "1",
                         pygame.K_2: "2", pygame.K_3: "3"}
        t0 = time.perf_counter()
        flip = 0
        while not self._stop_flag:
            try:
                if time.perf_counter() - t0 < SPRAY_DURATION:
                    k = spray_keys[flip % len(spray_keys)]
                    ev = pygame.event.Event(pygame.KEYDOWN, key=k,
                                            unicode=spray_unicode.get(k, ""),
                                            mod=0)
                    pygame.event.post(ev)
                    flip += 1
                    time.sleep(SPRAY_INTERVAL)
                    continue
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
        self.total_rounds = max(1, int(getattr(_opts, "rounds", 1) or 1))
        self.rounds_left = self.total_rounds
        self.list_only = bool(getattr(_opts, "list_only", False))
        _driver["obj"] = self

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

        # --only 过滤：只保留指定菜单码
        only = getattr(_opts, "only", None)
        if only:
            missing = [c for c in only if c not in {q[0] for q in self.queue}]
            self.queue = [q for q in self.queue if q[0] in only]
            for c in sorted(missing):
                _report(f"[SKIP] --only 菜单码 {c} 未匹配到可测菜单项"
                        f"（不存在 / 被跳过 / 模块文件重复）")

        total = len(self.queue)
        _report(f"计划点击 {total} 个模块（跳过存档/设置/退出类菜单项）")
        if self.total_rounds > 1:
            _report(f"轮次  : 共 {self.total_rounds} 轮")
        if getattr(_opts, "fast", False):
            _report("模式  : --fast（界面延时已压缩）")
        if self.list_only:
            for code, label, title in self.queue:
                _report(f"  {code:>4}  {label}  [下拉:{title}]  "
                        f"{MODULE_ROUTES_FILE(code)}")
            self.idx = len(self.queue)  # 只列出：让 step 直接走收尾，不点击
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
            _current["code"] = code
            # 先落盘再进入：若模块硬崩（如 0xC0000005），报告里能看出崩在谁身上
            _write_state(code, label, MODULE_ROUTES_FILE(code))
            _report(f"-> 进入 {label} ({code}) {MODULE_ROUTES_FILE(code)}", echo=False)
            self.activate(code)
            # 走到这里 = 模块已退回主菜单
            self.entered += 1
            _clear_state()
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
        """队列走完：多轮则重开一轮；否则关闭菜单并投递 QUIT。"""
        import pygame
        for etype, el in self.menu_elements:
            if etype == "dropdown":
                el.is_open = False
        if self.rounds_left > 1:
            # 还有下一轮：重置状态机继续，不退出主菜单
            self.rounds_left -= 1
            done = self.total_rounds - self.rounds_left
            self.idx = 0
            self.state = STATE_OPEN
            self.next_at = time.perf_counter() + DELAY_SETTLE
            self._dbg_key = None
            _report(f"==== 第 {done} 轮完成（累计进入 {self.entered}），"
                    f"开始第 {done + 1}/{self.total_rounds} 轮 ====")
            return
        self.finished = True
        _report("------------------------------------")
        if self.list_only:
            _report(f"--list 完成：计划 {len(self.queue)} 项，仅列出不点击")
        else:
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
        if getattr(_opts, "shots", False):
            for _i, _t in enumerate(SHOT_TIMES):
                _take_shot_async("abcd"[_i] if _i < 4 else str(_i), _t)
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
            _cancel_pending_shots()
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

def _acquire_instance_lock():
    """单实例锁：同一时刻只允许一个 auto_test 写报告。

    返回 fd（持有到进程退出，由操作系统自动释放，无残留问题）；
    已有实例占用时返回 None。
    """
    lock_path = os.path.join(ROOT, ".auto_test.lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o666)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    os.write(fd, str(os.getpid()).encode("ascii"))
    return fd


def _parse_args(argv=None):
    """解析命令行参数。"""
    ap = argparse.ArgumentParser(
        prog="auto_test",
        description="三国群英传 · 一键自动测试（模拟手动点击各模块进出）")
    ap.add_argument("--only", metavar="码[,码…]",
                    help="只测指定菜单码，逗号分隔（配合 --list 查码）")
    ap.add_argument("--rounds", type=int, default=1,
                    help="重复测试轮数（默认 1，查偶发问题可加到 3+）")
    ap.add_argument("--fast", action="store_true",
                    help="压缩界面延时，跑得更快")
    ap.add_argument("--list", dest="list_only", action="store_true",
                    help="只列出计划点击的菜单项，不执行点击")
    ap.add_argument("--keep-save", action="store_true",
                    help="不备份/恢复存档（保留测试期间的改动）")
    ap.add_argument("--shots", action="store_true",
                    help="每个模块截图两张存入 test_shots/（排查界面布局问题）")
    ap.add_argument("--all", action="store_true",
                    help="全量测试全部模块（等价于不带 --only；供无界面后台运行）")
    ap.add_argument("--gui", action="store_true",
                    help="强制打开图形界面（会忽略其余参数）")
    return ap.parse_args(argv)


def run(opts) -> int:
    """执行一键自动测试，返回退出码。"""
    global _opts, DELAY_OPEN, DELAY_HOVER, DELAY_SCROLL, DELAY_SETTLE
    _opts = opts
    if opts.only:
        opts.only = {c.strip() for c in opts.only.split(",") if c.strip()}
    opts.rounds = max(1, int(opts.rounds or 1))

    lock_fd = _acquire_instance_lock()
    if lock_fd is None:
        print("[auto_test] 已有实例在运行（报告被先启动者占用），本次退出")
        return 3
    os.environ["SAN_GUO_AUTOTEST"] = "1"
    os.chdir(ROOT)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    # 关键：本脚本以 __main__ 运行，而 game_main_menu 里 `from auto_test import`
    # 会再加载一份同名模块，导致 _current/_results/_heartbeat 两套实例互不相通。
    # 这里把 __main__ 注册为 auto_test，保证全进程只有这一个实例。
    sys.modules["auto_test"] = sys.modules[__name__]

    _init_report()
    _check_stale_state()

    if opts.fast:
        DELAY_OPEN *= 0.6
        DELAY_HOVER *= 0.6
        DELAY_SCROLL *= 0.6
        DELAY_SETTLE *= 0.6

    if opts.shots and not opts.only:
        # 全量跑才清空；--only 增量复验时保留已有截图
        try:
            shutil.rmtree(SHOT_DIR, ignore_errors=True)
            os.makedirs(SHOT_DIR, exist_ok=True)
        except Exception:
            pass
    elif opts.shots:
        os.makedirs(SHOT_DIR, exist_ok=True)

    # 备份存档，测试结束后恢复
    save_backup = None
    if not opts.keep_save and os.path.exists(SAVE_PATH):
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

        # 主循环若中途退出（driver 未走完队列），如实记 FAIL
        drv = _driver["obj"]
        if drv is not None and not drv.finished and not opts.list_only:
            _report(f"[FAIL] 主循环提前退出：driver 停在 idx={drv.idx} "
                    f"state={drv.state}（队列共 {len(drv.queue)} 项，"
                    f"已进入 {drv.entered} 项）")
            exit_code = 1

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
        _clear_state()

    # --only 全部没匹配上 → 视为参数错误
    if opts.only and not opts.list_only and not _results:
        _report("[FAIL] --only 未匹配到任何可测模块")
        exit_code = 1 if exit_code == 0 else exit_code

    # 明细 + 汇总
    ok = sum(1 for r in _results if r[2] == "OK")
    fail = len(_results) - ok
    _report("------------------------------------")
    if _results:
        _report("模块明细（按进入顺序）:")
        for i, (name, label, status, elapsed, note) in enumerate(_results, 1):
            _report(f"  {i:>2}. {status:<4} {elapsed:6.2f}s  {name}  ({label})"
                    + (f"  — {note}" if note else ""))
        total_t = sum(r[3] for r in _results)
        _report(f"  小计: {len(_results)} 项，OK {ok} / FAIL {fail}，"
                f"模块累计耗时 {total_t:.1f}s")
    _report(f"summary : 共 {len(_results)} 个模块，OK {ok}，FAIL {fail}")
    if fail and exit_code == 0:
        exit_code = 1
    _report(f"exit    : {exit_code}")
    _report(f"report  : {REPORT_PATH}")
    return exit_code


# ══════════════════════════════════════════════════════════════
# 无界面 CLI 模式：打包成 windowed exe 后 stdout/stderr 不可用，需先恢复
# ══════════════════════════════════════════════════════════════

def _ensure_stdio() -> None:
    """确保 sys.stdout/sys.stderr 可写。

    顺序：已有可用流 → 包装仍然存在的 fd 1/2（重定向到文件/管道时）→
    AttachConsole 挂到父进程控制台 → 兜底指向 devnull（保证 print 不炸）。
    """
    if os.name != "nt":
        return
    import locale
    enc = locale.getpreferredencoding(False) or "utf-8"
    attached = False
    for name, fd in (("stdout", 1), ("stderr", 2)):
        cur = getattr(sys, name, None)
        if cur is not None and hasattr(cur, "write"):
            continue
        stream = None
        try:
            os.fstat(fd)
            stream = os.fdopen(fd, "w", encoding=enc, errors="replace",
                               closefd=False)
        except OSError:
            pass
        if stream is None:
            try:
                import ctypes
                k32 = ctypes.windll.kernel32
                if not attached:
                    attached = bool(k32.AttachConsole(-1))  # -1 = 父进程控制台
                if attached:
                    stream = open("CONOUT$", "w", encoding=enc,
                                  errors="replace")
            except Exception:
                stream = None
        if stream is None:
            try:
                stream = open(os.devnull, "w", encoding="utf-8")
            except OSError:
                continue
        try:
            setattr(sys, name, stream)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# 图形界面模式（无参数 / --gui 启动；测试本体在子进程无界面运行）
# ══════════════════════════════════════════════════════════════

def _gui_menu_items() -> list:
    """解析主菜单源码，返回可测模块清单 [(菜单码, 标签), ...]。

    只做正则提取、不 import 游戏（避免把 pygame 拖进 GUI 进程）；
    去重口径与驱动 bind() 一致：同一模块文件只保留首个菜单码。
    """
    path = os.path.join(ROOT, "ASSET", "game_main_menu.py")
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
    except OSError:
        return []
    routes = {}
    m = re.search(r"MODULE_ROUTES\s*=\s*\{(.*?)\}", src, re.S)
    if m:
        routes = dict(re.findall(r'"(\d+)"\s*:\s*"([^"]+)"', m.group(1)))
    special = set()
    m = re.search(r"SPECIAL_HANDLERS\s*=\s*\{(.*?)\}", src, re.S)
    if m:
        special = set(re.findall(r'"(\d+)"\s*:', m.group(1)))
    items, seen = [], set()
    for label, code in re.findall(r'\(\s*"([^"]+)"\s*,\s*"(\d+)"\s*\)', src):
        mod = routes.get(code) or (f"special:{code}" if code in special else None)
        if not mod or code in SKIP_CODES or mod in seen:
            continue
        seen.add(mod)
        items.append((code, label))
    return items


def _run_gui() -> int:
    """图形界面入口：勾选模块 → 子进程跑测试 → 实时转播报告文件。"""
    _ensure_stdio()
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except Exception as e:
        print(f"[auto_test] tkinter 不可用（{e}），回退无界面全量测试")
        return run(_parse_args(["--all"]))

    import subprocess

    items = _gui_menu_items()
    if not items:
        print("[auto_test] 未能从主菜单源码解析出可测模块，回退无界面全量测试")
        return run(_parse_args(["--all"]))

    try:
        root = tk.Tk()
    except Exception as e:
        print(f"[auto_test] 无法创建图形窗口（{e}），回退无界面全量测试")
        return run(_parse_args(["--all"]))

    root.title("三国群英传 · 自动测试")
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    gw, gh = min(960, int(sw * 0.85)), min(700, int(sh * 0.85))
    root.geometry(f"{gw}x{gh}+{(sw - gw) // 2}+{(sh - gh) // 2}")
    root.minsize(700, 500)

    EXIT_MSG = {0: "全部通过", 1: "有失败", 2: "挂起强杀",
                3: "已有实例在运行"}
    state = {"proc": None, "offset": 0, "pending": b"",
             "killed": False, "t0": 0.0}

    # ── 选项行 ─────────────────────────────────────────
    opt_fr = ttk.Frame(root, padding=(10, 8))
    opt_fr.pack(fill="x")
    fast_v = tk.BooleanVar(value=True)
    shots_v = tk.BooleanVar(value=False)
    keep_v = tk.BooleanVar(value=False)
    ttk.Checkbutton(opt_fr, text="快速模式 (--fast)",
                    variable=fast_v).pack(side="left")
    ttk.Checkbutton(opt_fr, text="截图 (--shots)",
                    variable=shots_v).pack(side="left", padx=(10, 0))
    ttk.Checkbutton(opt_fr, text="保留存档 (--keep-save)",
                    variable=keep_v).pack(side="left", padx=(10, 0))
    ttk.Label(opt_fr, text="轮数:").pack(side="left", padx=(16, 4))
    rounds_v = tk.IntVar(value=1)
    ttk.Spinbox(opt_fr, from_=1, to=20, width=4,
                textvariable=rounds_v).pack(side="left")

    # ── 模块勾选列表 ───────────────────────────────────
    mod_fr = ttk.LabelFrame(
        root, text=f"模块（{len(items)} 个，勾选要测的）", padding=8)
    mod_fr.pack(fill="both", expand=False, padx=10, pady=(0, 6))
    lst_bar = ttk.Frame(mod_fr)
    lst_bar.pack(fill="x", pady=(0, 4))
    lst_fr = ttk.Frame(mod_fr)
    lst_fr.pack(fill="both", expand=True)
    lst = tk.Listbox(lst_fr, selectmode="extended", exportselection=False,
                     height=10, font=("Microsoft YaHei UI", 9))
    lst_sb = ttk.Scrollbar(lst_fr, orient="vertical", command=lst.yview)
    lst.configure(yscrollcommand=lst_sb.set)
    lst_sb.pack(side="right", fill="y")
    lst.pack(side="left", fill="both", expand=True)
    for code, label in items:
        lst.insert("end", f"{code:>3}  {label}")
    lst.selection_set(0, "end")

    def _select_all(on: bool) -> None:
        lst.selection_clear(0, "end")
        if on:
            lst.selection_set(0, "end")

    ttk.Button(lst_bar, text="全选", width=6,
               command=lambda: _select_all(True)).pack(side="left")
    ttk.Button(lst_bar, text="清空", width=6,
               command=lambda: _select_all(False)).pack(side="left", padx=6)

    # ── 日志 ──────────────────────────────────────────
    log_fr = ttk.Frame(root, padding=(10, 0))
    log_fr.pack(fill="both", expand=True)
    log = tk.Text(log_fr, height=14, wrap="none", state="disabled",
                  font=("Consolas", 9), background="#101418",
                  foreground="#d7dde3")
    log.tag_configure("fail", foreground="#ff6b6b")
    log.tag_configure("ok", foreground="#7bd88f")
    log.tag_configure("sys", foreground="#8ecae6")
    log_sb = ttk.Scrollbar(log_fr, orient="vertical", command=log.yview)
    log.configure(yscrollcommand=log_sb.set)
    log_sb.pack(side="right", fill="y")
    log.pack(side="left", fill="both", expand=True)

    def _append(text: str, tag: str = None) -> None:
        log.configure(state="normal")
        for line in text.splitlines():
            if not line:
                continue
            t = tag
            if t is None:
                if "[FAIL]" in line or "[CRASH]" in line or "[HANG]" in line:
                    t = "fail"
                elif "[OK]" in line or line.lstrip().startswith("summary"):
                    t = "ok"
                elif line.startswith("===="):
                    t = "sys"
            if t:
                log.insert("end", line + "\n", t)
            else:
                log.insert("end", line + "\n")
        log.see("end")
        log.configure(state="disabled")

    def _log_reset() -> None:
        log.configure(state="normal")
        log.delete("1.0", "end")
        log.configure(state="disabled")

    # ── 按钮 / 状态行 ─────────────────────────────────
    act_fr = ttk.Frame(root, padding=(10, 6))
    act_fr.pack(fill="x")
    status_v = tk.StringVar(value=f"就绪 · {len(items)} 个可测模块")
    status_lb = ttk.Label(act_fr, textvariable=status_v, foreground="#555")
    status_lb.pack(side="right")

    def _cleanup_after_kill() -> None:
        """子进程被强杀时 finally 不会执行：GUI 负责恢复存档与状态标记。"""
        bak = SAVE_PATH + ".autotest_bak"
        try:
            if os.path.exists(bak):
                shutil.move(bak, SAVE_PATH)
                _append("[GUI] 已恢复测试前存档\n", tag="sys")
        except Exception:
            pass
        _clear_state()

    def _open(path: str, what: str) -> None:
        if not os.path.exists(path):
            messagebox.showinfo(what, f"尚不存在：\n{path}")
            return
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror(what, str(e))

    def _start() -> None:
        if state["proc"] is not None:
            return
        sel = [items[i][0] for i in lst.curselection()]
        if not sel:
            messagebox.showwarning("未选模块", "请至少勾选一个要测试的模块。")
            return
        args = []
        if len(sel) == len(items):
            args.append("--all")
        else:
            args += ["--only", ",".join(sel)]
        if fast_v.get():
            args.append("--fast")
        if shots_v.get():
            args.append("--shots")
        if keep_v.get():
            args.append("--keep-save")
        r = int(rounds_v.get() or 1)
        if r > 1:
            args += ["--rounds", str(r)]
        if getattr(sys, "frozen", False):
            base = [sys.executable]
        else:
            base = [sys.executable, os.path.abspath(__file__)]
        cmd = base + args
        # 跳过报告文件里残留的旧内容；子进程覆盖写时 size 变小会自动归零
        try:
            state["offset"] = os.path.getsize(REPORT_PATH)
        except OSError:
            state["offset"] = 0
        state["pending"] = b""
        state["killed"] = False
        state["t0"] = time.time()
        _log_reset()
        try:
            proc = subprocess.Popen(
                cmd, cwd=ROOT, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000 if os.name == "nt" else 0)
        except Exception as e:
            messagebox.showerror("启动失败", str(e))
            return
        state["proc"] = proc
        btn_start.configure(state="disabled")
        btn_stop.configure(state="normal")
        _append(f"[GUI] 启动: {' '.join(cmd)}\n", tag="sys")
        root.after(300, _poll)

    def _stop() -> None:
        proc = state["proc"]
        if proc is None or proc.poll() is not None:
            return
        state["killed"] = True
        try:
            proc.terminate()
        except Exception:
            pass
        status_v.set("正在停止…")

    def _tail() -> None:
        try:
            size = os.path.getsize(REPORT_PATH)
        except OSError:
            size = 0
        if size < state["offset"]:
            # 子进程已覆盖写新报告，从头转播
            state["offset"] = 0
            state["pending"] = b""
        if size > state["offset"]:
            try:
                with open(REPORT_PATH, "rb") as f:
                    f.seek(state["offset"])
                    data = f.read()
            except OSError:
                data = b""
            state["offset"] = size
            state["pending"] += data
            cut = state["pending"].rfind(b"\n")  # 只取整行，防多字节被截断
            if cut >= 0:
                _append(state["pending"][:cut + 1].decode("utf-8",
                                                          errors="replace"))
                state["pending"] = state["pending"][cut + 1:]

    def _poll() -> None:
        proc = state["proc"]
        if proc is None:
            return
        _tail()
        rc = proc.poll()
        if rc is None:
            status_v.set(f"运行中… {int(time.time() - state['t0'])}s")
            root.after(300, _poll)
            return
        if state["pending"]:
            _append(state["pending"].decode("utf-8", errors="replace"))
            state["pending"] = b""
        state["proc"] = None
        btn_start.configure(state="normal")
        btn_stop.configure(state="disabled")
        if state["killed"]:
            state["killed"] = False
            _cleanup_after_kill()
            status_v.set("已手动停止")
            _append("[GUI] 已停止测试\n", tag="sys")
        else:
            msg = EXIT_MSG.get(rc, f"退出码 {rc}")
            status_v.set(f"完成 · 退出码 {rc} · {msg}")
            _append(f"[GUI] 子进程退出，{msg}\n", tag="sys")
        if os.environ.get("SAN_GUO_GUI_AUTOEXIT"):
            root.after(800, root.destroy)

    btn_start = ttk.Button(act_fr, text="▶ 开始测试", command=_start)
    btn_start.pack(side="left", padx=(0, 6))
    btn_stop = ttk.Button(act_fr, text="■ 停止", command=_stop,
                          state="disabled")
    btn_stop.pack(side="left", padx=(0, 6))
    ttk.Button(act_fr, text="打开报告",
               command=lambda: _open(REPORT_PATH, "报告")
               ).pack(side="left", padx=(0, 6))
    ttk.Button(act_fr, text="打开截图",
               command=lambda: _open(SHOT_DIR, "截图目录")
               ).pack(side="left")

    def _on_close() -> None:
        proc = state["proc"]
        if proc is not None and proc.poll() is None:
            if not messagebox.askyesno(
                    "退出", "测试仍在运行，停止测试并退出？"):
                return
            try:
                proc.terminate()
            except Exception:
                pass
            _cleanup_after_kill()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    _append("[GUI] 勾选模块后点「开始测试」；测试在后台无界面运行，"
            "日志来自报告文件。\n", tag="sys")

    # 自动化冒烟钩子：SAN_GUO_GUI_AUTOSTART="码[,码]" 预选并自动开始，
    # SAN_GUO_GUI_AUTOEXIT=1 测试结束后自动关窗（供无头环境验证 GUI 链路）
    auto = os.environ.get("SAN_GUO_GUI_AUTOSTART")
    if auto is not None:
        if auto:
            want = {c.strip() for c in auto.split(",") if c.strip()}
            lst.selection_clear(0, "end")
            for i, (code, _lab) in enumerate(items):
                if code in want:
                    lst.selection_set(i)
        root.after(400, _start)
    root.mainloop()
    return 0


def main() -> None:
    """入口：无参数或带 --gui → 图形界面；带其它参数 → 无界面 CLI。"""
    argv = sys.argv[1:]
    if not argv or "--gui" in argv:
        sys.exit(_run_gui())
    _ensure_stdio()
    sys.exit(run(_parse_args(argv)))


if __name__ == "__main__":
    main()
