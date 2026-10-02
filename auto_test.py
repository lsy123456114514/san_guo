#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键自动测试 — 模拟手动操作，逐个点击各模块进入并退出
========================================================

用法（项目根目录）::

    py auto_test.py                 # 全量测试
    py auto_test.py --list          # 只列出计划点击的菜单项，不执行
    py auto_test.py --only 23,17    # 只测指定菜单码
    py auto_test.py --rounds 3      # 连测 3 轮（查偶发问题）
    py auto_test.py --fast          # 压缩界面延时，跑得更快
    py auto_test.py --keep-save     # 不备份/恢复存档（保留测试改动）

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


def main() -> None:
    """控制台入口。"""
    sys.exit(run(_parse_args()))


if __name__ == "__main__":
    main()
