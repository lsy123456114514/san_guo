#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 - 统一日志管理、Bug上报、时间同步
支持多版本兼容、日志轮转、性能监控
"""
import os
import sys
import time
import datetime
import traceback
import threading
import socket
import urllib.request
import json
import platform
import gzip
import shutil

GAME_VERSION = "2.0.0"
DATA_VERSION = 3

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "game.log")
ERROR_FILE = os.path.join(LOG_DIR, "error.log")
BUG_REPORT_FILE = os.path.join(LOG_DIR, "bug_reports.log")
PERF_FILE = os.path.join(LOG_DIR, "performance.log")

LOG_LEVELS = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4
}

LOG_LEVEL_NAMES = {v: k for k, v in LOG_LEVELS.items()}

current_log_level = LOG_LEVELS["INFO"]
log_lock = threading.Lock()
start_time = time.time()
performance_stats = {
    'frames': 0,
    'fps_values': [],
    'memory_usage': [],
    'last_report_time': 0
}


def init_log_system():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    rotate_logs()
    
    log_message("INFO", "=" * 60)
    log_message("INFO", f"游戏启动 - 版本: {GAME_VERSION}, 数据版本: {DATA_VERSION}")
    log_message("INFO", "=" * 60)
    log_message("INFO", f"日志目录: {LOG_DIR}")
    log_message("INFO", f"操作系统: {platform.system()} {platform.release()}")
    log_message("INFO", f"Python版本: {sys.version.split()[0]}")
    log_message("INFO", f"CPU: {platform.processor()}")
    log_message("INFO", f"架构: {platform.machine()}")
    log_message("INFO", f"启动时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def rotate_logs(max_size_mb=10, max_backups=5):
    log_files = [LOG_FILE, ERROR_FILE, BUG_REPORT_FILE, PERF_FILE]
    
    for file_path in log_files:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb >= max_size_mb:
                for i in range(max_backups - 1, 0, -1):
                    old_path = f"{file_path}.{i}"
                    new_path = f"{file_path}.{i + 1}"
                    if os.path.exists(old_path):
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        os.rename(old_path, new_path)
                
                backup_path = f"{file_path}.1"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                
                with open(file_path, 'rb') as f_in:
                    with gzip.open(backup_path + '.gz', 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                open(file_path, 'w').close()
                log_message("INFO", f"日志轮转: {file_path} -> {backup_path}.gz")


def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def log_message(level, message):
    global current_log_level
    
    level = level.upper()
    level_num = LOG_LEVELS.get(level, 1)
    
    if level_num < current_log_level:
        return
    
    timestamp = get_timestamp()
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    with log_lock:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
            
            if level in ["ERROR", "CRITICAL"]:
                with open(ERROR_FILE, "a", encoding="utf-8") as f:
                    f.write(log_line)
            
            if level_num <= LOG_LEVELS["DEBUG"]:
                print(log_line.strip())
        except Exception:
            pass


def debug(message):
    log_message("DEBUG", message)


def info(message):
    log_message("INFO", message)


def warning(message):
    log_message("WARNING", message)


def error(message, exception=None):
    if exception:
        trace_str = traceback.format_exc()
        log_message("ERROR", f"{message}\n{trace_str}")
    else:
        log_message("ERROR", message)


def critical(message, exception=None):
    if exception:
        trace_str = traceback.format_exc()
        log_message("CRITICAL", f"{message}\n{trace_str}")
    else:
        log_message("CRITICAL", message)


def set_log_level(level):
    global current_log_level
    level = level.upper()
    current_log_level = LOG_LEVELS.get(level, LOG_LEVELS["INFO"])
    log_message("INFO", f"日志级别设置为: {level}")


def log_performance(fps=None, memory_mb=None):
    global performance_stats
    
    performance_stats['frames'] += 1
    
    if fps is not None:
        performance_stats['fps_values'].append(fps)
        if len(performance_stats['fps_values']) > 60:
            performance_stats['fps_values'].pop(0)
    
    if memory_mb is not None:
        performance_stats['memory_usage'].append(memory_mb)
        if len(performance_stats['memory_usage']) > 60:
            performance_stats['memory_usage'].pop(0)
    
    now = time.time()
    if now - performance_stats['last_report_time'] >= 10:
        avg_fps = sum(performance_stats['fps_values']) / len(performance_stats['fps_values']) if performance_stats['fps_values'] else 0
        avg_memory = sum(performance_stats['memory_usage']) / len(performance_stats['memory_usage']) if performance_stats['memory_usage'] else 0
        
        with log_lock:
            try:
                with open(PERF_FILE, "a", encoding="utf-8") as f:
                    f.write(f"[{get_timestamp()}] FPS: {avg_fps:.1f}, Memory: {avg_memory:.2f} MB\n")
            except Exception:
                pass
        
        performance_stats['last_report_time'] = now


class BugReport:
    def __init__(self):
        self.reports = []
    
    def report_bug(self, title, description, steps=None, screenshot_path=None, user_info=None):
        report = {
            "id": int(time.time() * 1000),
            "timestamp": get_timestamp(),
            "title": title,
            "description": description,
            "steps": steps if steps else [],
            "screenshot_path": screenshot_path,
            "user_info": user_info if user_info else {},
            "system_info": {
                "os": platform.system(),
                "os_version": platform.release(),
                "python_version": sys.version.split()[0],
                "game_version": GAME_VERSION,
                "data_version": DATA_VERSION,
                "screen_resolution": f"{getattr(sys, '_MEIPASS', 'N/A')}",
                "cpu": platform.processor(),
                "architecture": platform.machine(),
                "memory": self._get_memory_info()
            }
        }
        
        self.reports.append(report)
        
        with log_lock:
            try:
                with open(BUG_REPORT_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            except Exception:
                pass
        
        log_message("INFO", f"Bug上报: {title}")
        return report["id"]
    
    def _get_memory_info(self):
        try:
            import psutil
            mem = psutil.virtual_memory()
            return f"Total: {mem.total // (1024**3)} GB, Available: {mem.available // (1024**3)} GB"
        except ImportError:
            return "psutil not available"
    
    def get_reports(self):
        return self.reports
    
    def clear_reports(self):
        self.reports = []


bug_report = BugReport()


def report_bug(title, description, steps=None, screenshot_path=None, user_info=None):
    return bug_report.report_bug(title, description, steps, screenshot_path, user_info)


def auto_report_exception(exception, context=""):
    title = f"自动捕获异常: {type(exception).__name__}"
    description = f"{str(exception)}\n\n上下文: {context}\n\n堆栈信息:\n{traceback.format_exc()}"
    
    bug_report.report_bug(title, description)
    log_message("ERROR", f"自动上报异常: {title}")


def sync_time_from_windows_server():
    if platform.system() != "Windows":
        return False
    
    ntp_servers = [
        "time.windows.com",
        "ntp.aliyun.com",
        "cn.pool.ntp.org",
        "time.nist.gov"
    ]
    
    for server in ntp_servers:
        try:
            import struct
            
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(5)
            
            data = b'\x1b' + 47 * b'\0'
            client.sendto(data, (server, 123))
            
            response, _ = client.recvfrom(1024)
            client.close()
            
            if len(response) >= 48:
                ntp_time = struct.unpack('!12I', response)[10]
                ntp_time -= 2208988800
                
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    FILETIME = ctypes.c_int64(ntp_time * 10000000)
                    kernel32.SetSystemTime(FILETIME)
                    
                    log_message("INFO", f"时间同步成功，服务器: {server}")
                    return True
                except Exception as e:
                    log_message("WARNING", f"设置系统时间失败: {e}")
                    continue
        except Exception as e:
            log_message("WARNING", f"时间同步失败，服务器: {server} - {e}")
            continue
    
    log_message("ERROR", "所有时间服务器同步失败")
    return False


def sync_time_via_http():
    http_servers = [
        "https://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp",
        "https://time1.api.aliyun.com/time/now",
        "https://api.pingcc.cn/time"
    ]
    
    for url in http_servers:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read().decode('utf-8')
                
                try:
                    json_data = json.loads(data)
                    if "data" in json_data:
                        json_data = json_data["data"]
                    
                    if "t" in json_data:
                        timestamp = int(json_data["t"]) // 1000
                    elif "timestamp" in json_data:
                        timestamp = int(json_data["timestamp"])
                    elif "time" in json_data:
                        timestamp = int(json_data["time"])
                    else:
                        continue
                    
                    if platform.system() == "Windows":
                        try:
                            import ctypes
                            kernel32 = ctypes.windll.kernel32
                            FILETIME = ctypes.c_int64(timestamp * 10000000)
                            kernel32.SetSystemTime(FILETIME)
                            
                            log_message("INFO", f"HTTP时间同步成功，服务器: {url}")
                            return True
                        except Exception as e:
                            log_message("WARNING", f"设置系统时间失败: {e}")
                            continue
                    else:
                        log_message("INFO", f"获取时间成功(非Windows): {url}, 时间戳: {timestamp}")
                        return True
                except (json.JSONDecodeError, KeyError):
                    continue
        except Exception as e:
            log_message("WARNING", f"HTTP时间同步失败，服务器: {url} - {e}")
            continue
    
    log_message("ERROR", "所有HTTP时间服务器同步失败")
    return False


def sync_time():
    log_message("INFO", "开始时间同步...")
    
    if platform.system() == "Windows":
        if sync_time_from_windows_server():
            return
        
        if sync_time_via_http():
            return
    else:
        if sync_time_via_http():
            return
    
    log_message("WARNING", "时间同步失败，使用本地时间")


def get_log_file_path():
    return LOG_FILE


def get_error_file_path():
    return ERROR_FILE


def get_bug_report_path():
    return BUG_REPORT_FILE


def read_logs(lines=100):
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except Exception:
        return []


def read_errors(lines=50):
    try:
        with open(ERROR_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except Exception:
        return []


def read_bug_reports():
    reports = []
    try:
        with open(BUG_REPORT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        reports.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass
    return reports


def clear_logs():
    with log_lock:
        try:
            with open(LOG_FILE, "w") as f:
                pass
            with open(ERROR_FILE, "w") as f:
                pass
            with open(PERF_FILE, "w") as f:
                pass
            log_message("INFO", "日志已清空")
        except Exception:
            pass


def install_exception_handler():
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        trace_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log_message("CRITICAL", f"未捕获异常: {exc_type.__name__}\n{trace_str}")
        
        auto_report_exception(exc_value, "全局异常处理")
    
    sys.excepthook = handle_exception
    
    def handle_thread_exception(args):
        exc_type, exc_value, exc_traceback = args.exc_type, args.exc_value, args.exc_traceback
        
        if issubclass(exc_type, SystemExit):
            return
        
        trace_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        log_message("CRITICAL", f"线程异常: {exc_type.__name__}\n{trace_str}")
        
        auto_report_exception(exc_value, "线程异常")
    
    if hasattr(threading, 'excepthook'):
        threading.excepthook = handle_thread_exception
        log_message("INFO", "线程异常处理器已安装")
    else:
        log_message("WARNING", "当前Python版本不支持线程异常处理(Python 3.8+)")
    
    log_message("INFO", "异常处理器已安装")


def get_game_version():
    return GAME_VERSION


def get_data_version():
    return DATA_VERSION


def log_version_info():
    log_message("INFO", f"游戏版本: {GAME_VERSION}")
    log_message("INFO", f"数据版本: {DATA_VERSION}")


init_log_system()
install_exception_handler()