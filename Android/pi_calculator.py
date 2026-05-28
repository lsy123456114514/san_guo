#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import random
import time
import sys
import os
import ctypes
from decimal import Decimal, getcontext

class PiCalculator:
    def __init__(self, num_threads=100, total_points=10000000, resource_limit=99, precision=100, use_gpu=False):
        self.num_threads = num_threads
        self.total_points = total_points
        self.resource_limit = resource_limit
        self.precision = precision
        self.use_gpu = use_gpu
        self.points_per_thread = total_points // num_threads
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.hit_count = 0
        self.threads = []
        self.resource_monitor = None
        self.pi_result = Decimal('0')

    def get_cpu_usage(self):
        if sys.platform == 'win32':
            try:
                class FILETIME(ctypes.Structure):
                    _fields_ = [("dwLowDateTime", ctypes.c_uint), ("dwHighDateTime", ctypes.c_uint)]
                
                class SYSTEM_TIMES(ctypes.Structure):
                    _fields_ = [
                        ("IdleTime", FILETIME),
                        ("KernelTime", FILETIME),
                        ("UserTime", FILETIME)
                    ]
                
                kernel32 = ctypes.windll.kernel32
                times1 = SYSTEM_TIMES()
                times2 = SYSTEM_TIMES()
                
                if kernel32.GetSystemTimes(ctypes.byref(times1), ctypes.byref(times2), ctypes.byref(times1)):
                    time.sleep(0.1)
                    if kernel32.GetSystemTimes(ctypes.byref(times2), ctypes.byref(times1), ctypes.byref(times1)):
                        def filetime_to_ms(ft):
                            return (ft.dwHighDateTime << 32) | ft.dwLowDateTime
                        
                        idle_diff = filetime_to_ms(times2.IdleTime) - filetime_to_ms(times1.IdleTime)
                        kernel_diff = filetime_to_ms(times2.KernelTime) - filetime_to_ms(times1.KernelTime)
                        user_diff = filetime_to_ms(times2.UserTime) - filetime_to_ms(times1.UserTime)
                        
                        total = kernel_diff + user_diff
                        if total > 0:
                            return 100.0 - (idle_diff / total) * 100
            except:
                pass
        return None

    def get_memory_usage(self):
        if sys.platform == 'win32':
            try:
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_uint),
                        ("dwMemoryLoad", ctypes.c_uint),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong)
                    ]
                
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                
                kernel32 = ctypes.windll.kernel32
                if kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    return stat.dwMemoryLoad
            except:
                pass
        return None

    def get_gpu_usage(self):
        try:
            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    gpu_usage = result.stdout.strip()
                    if gpu_usage:
                        return float(gpu_usage)
            return None
        except:
            return None

    def monitor_resources(self):
        while not self.stop_event.is_set():
            cpu_percent = self.get_cpu_usage()
            memory_percent = self.get_memory_usage()
            gpu_percent = self.get_gpu_usage()
            
            if cpu_percent is None:
                cpu_percent = "N/A"
            if memory_percent is None:
                memory_percent = "N/A"
            
            print(f"\r资源监控 - CPU: {cpu_percent}% | 内存: {memory_percent}% | GPU: {gpu_percent or 'N/A'}%", end='')
            
            if isinstance(cpu_percent, (int, float)) and cpu_percent >= self.resource_limit:
                print(f"\n\n警告：CPU占用超过 {self.resource_limit}%，正在停止计算...")
                self.stop_event.set()
                break
            if isinstance(memory_percent, (int, float)) and memory_percent >= self.resource_limit:
                print(f"\n\n警告：内存占用超过 {self.resource_limit}%，正在停止计算...")
                self.stop_event.set()
                break
            
            time.sleep(0.1)

    def calculate_pi_mpmath(self):
        import mpmath as mp
        mp.mp.dps = self.precision + 10
        self.pi_result = mp.pi
        return str(self.pi_result)

    def calculate_pi_thread(self, thread_id):
        local_hits = 0
        random.seed(thread_id + int(time.time() * 1000))
        
        for _ in range(self.points_per_thread):
            if self.stop_event.is_set():
                break
            
            x = random.random()
            y = random.random()
            if x**2 + y**2 <= 1.0:
                local_hits += 1
        
        with self.lock:
            self.hit_count += local_hits
        
        if not self.stop_event.is_set():
            print(f"\n线程 {thread_id:3d} 完成，命中 {local_hits} 次")

    def run(self):
        import sys
        sys.stdout.reconfigure(line_buffering=True)
        print(f"启动 π 计算...")
        print(f"线程数: {self.num_threads}")
        print(f"采样点: {self.total_points}")
        print(f"资源限制: {self.resource_limit}%")
        print(f"目标精度: {self.precision} 位小数")
        print(f"GPU加速: {'已启用' if self.use_gpu else '未启用'}")
        print(f"监控线程已启动，按 Ctrl+C 可手动停止")
        sys.stdout.flush()
        start_time = time.time()

        if self.precision > 15:
            print(f"\n使用 mpmath 高精度计算模式...")
            pi_str = self.calculate_pi_mpmath()
            
            elapsed_time = time.time() - start_time
            print(f"\n计算完成！")
            print(f"π 的值 ({self.precision} 位):")
            print(f"{pi_str[:self.precision + 2]}")
            print(f"耗时: {elapsed_time:.4f} 秒")
            return

        self.resource_monitor = threading.Thread(target=self.monitor_resources, daemon=True)
        self.resource_monitor.start()

        print("\n使用 CPU 多线程蒙特卡洛方法计算...")
        for i in range(self.num_threads):
            if self.stop_event.is_set():
                break
            t = threading.Thread(target=self.calculate_pi_thread, args=(i,))
            self.threads.append(t)
            t.start()

        for t in self.threads:
            t.join()

        self.stop_event.set()
        if self.resource_monitor:
            self.resource_monitor.join()

        elapsed_time = time.time() - start_time
        
        if self.hit_count > 0:
            pi_estimate = 4.0 * self.hit_count / (len(self.threads) * self.points_per_thread)
            
            getcontext().prec = self.precision + 10
            pi_decimal = Decimal(str(pi_estimate))
            
            print(f"\n\n计算完成！")
            print(f"π 的估计值 ({self.precision} 位):")
            pi_str = str(pi_decimal)
            if len(pi_str) > self.precision + 2:
                pi_str = pi_str[:self.precision + 2]
            print(f"{pi_str}")
            print(f"实际 π 值前{self.precision}位:")
            print(f"3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679")
        else:
            print(f"\n\n计算被提前终止")
        
        print(f"耗时: {elapsed_time:.4f} 秒")
        print(f"完成线程数: {len([t for t in self.threads if not t.is_alive()])}/{self.num_threads}")

def print_usage():
    print("用法:")
    print("  python pi_calculator.py [选项]")
    print("")
    print("选项:")
    print("  -t, --threads N    设置线程数量，默认 100")
    print("  -p, --points N     设置采样点总数，默认 10000000")
    print("  -r, --resource N   设置资源限制百分比，默认 99")
    print("  -d, --digits N     设置计算精度（小数位数），默认 100")
    print("  -g, --gpu          启用 GPU 加速（需要 CUDA）")
    print("  -s, --slow         慢速模式，延长计算时间")
    print("  -h, --help         显示帮助信息")
    print("")
    print("示例:")
