#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import sys
import os
import datetime
from collections import deque

try:
    import psutil
except ImportError:
    messagebox.showerror("错误", "需要安装 psutil 库，请运行: pip install psutil")
    sys.exit(1)

try:
    import mpmath as mp
    USE_MPMATH = True
except ImportError:
    USE_MPMATH = False
    messagebox.showwarning("警告", "安装 mpmath 库可获得更高精度计算: pip install mpmath")

class PiCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("π 计算器 - Pi Calculator")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        self.stop_event = threading.Event()
        self.is_calculating = False
        self.pi_result = ""
        
        self.cpu_history = deque(maxlen=100)
        self.memory_history = deque(maxlen=100)
        self.max_cpu = 0
        self.max_memory = 0
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel', font=('Microsoft YaHei', 24, 'bold'), foreground='#2E86AB')
        style.configure('Info.TLabel', font=('Microsoft YaHei', 10), foreground='#555555')
        style.configure('Result.TLabel', font=('Consolas', 12), foreground='#1a1a1a')
        style.configure('Monitor.TLabel', font=('Consolas', 9), foreground='#666666')
        
        style.configure('Action.TButton', font=('Microsoft YaHei', 12, 'bold'), padding=10)
        style.configure('Stop.TButton', font=('Microsoft YaHei', 12), padding=10)
        style.configure('Copy.TButton', font=('Microsoft YaHei', 10, 'bold'), padding=8)
        
        style.configure('Custom.TEntry', font=('Consolas', 11))
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="π", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        title_text = ttk.Label(title_frame, text="计算器", style='Title.TLabel')
        title_text.pack(side=tk.LEFT, padx=(5, 0))
        
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="15")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="线程数量:", width=15).pack(side=tk.LEFT)
        self.thread_var = tk.StringVar(value="100")
        thread_entry = ttk.Entry(row1, textvariable=self.thread_var, width=15, style='Custom.TEntry')
        thread_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="(默认100)", style='Info.TLabel').pack(side=tk.LEFT)
        
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="采样点总数:", width=15).pack(side=tk.LEFT)
        self.points_var = tk.StringVar(value="10000000")
        points_entry = ttk.Entry(row2, textvariable=self.points_var, width=15, style='Custom.TEntry')
        points_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="(默认1000万)", style='Info.TLabel').pack(side=tk.LEFT)
        
        row3 = ttk.Frame(settings_frame)
        row3.pack(fill=tk.X, pady=5)
        ttk.Label(row3, text="小数位数:", width=15).pack(side=tk.LEFT)
        self.digits_var = tk.StringVar(value="100")
        digits_entry = ttk.Entry(row3, textvariable=self.digits_var, width=15, style='Custom.TEntry')
        digits_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row3, text="(高精度模式，>15位使用mpmath)", style='Info.TLabel').pack(side=tk.LEFT)
        
        row4 = ttk.Frame(settings_frame)
        row4.pack(fill=tk.X, pady=5)
        ttk.Label(row4, text="资源限制 %:", width=15).pack(side=tk.LEFT)
        self.resource_var = tk.StringVar(value="99")
        resource_entry = ttk.Entry(row4, textvariable=self.resource_var, width=15, style='Custom.TEntry')
        resource_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row4, text="(CPU/内存超过此值自动停止)", style='Info.TLabel').pack(side=tk.LEFT)
        
        row5 = ttk.Frame(settings_frame)
        row5.pack(fill=tk.X, pady=5)
        self.slow_var = tk.BooleanVar(value=False)
        slow_check = ttk.Checkbutton(row5, text="慢速模式 (延长计算时间)", variable=self.slow_var)
        slow_check.pack(side=tk.LEFT)
        
        self.auto_thread_var = tk.BooleanVar(value=False)
        auto_thread_check = ttk.Checkbutton(row5, text="自动线程 (占用全部CPU)", variable=self.auto_thread_var)
        auto_thread_check.pack(side=tk.LEFT, padx=(20, 0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_button = ttk.Button(button_frame, text="开始计算", style='Action.TButton', command=self.start_calculation)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止", style='Stop.TButton', command=self.stop_calculation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.copy_button = ttk.Button(button_frame, text="📋 一键拷贝结果", style='Copy.TButton', command=self.copy_to_clipboard, state=tk.DISABLED)
        self.copy_button.pack(side=tk.LEFT)
        
        self.save_button = ttk.Button(button_frame, text="💾 保存到文件", style='Copy.TButton', command=self.save_to_file, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=(10, 0))
        
        result_frame = ttk.LabelFrame(main_frame, text="计算结果", padding="15")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.result_text = scrolledtext.ScrolledText(result_frame, font=('Consolas', 10), height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        chart_frame = ttk.LabelFrame(main_frame, text="资源监控波形图", padding="10")
        chart_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.chart_canvas = tk.Canvas(chart_frame, bg="#000000", height=150)
        self.chart_canvas.pack(fill=tk.X)
        
        chart_label_frame = ttk.Frame(chart_frame)
        chart_label_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(chart_label_frame, text="CPU: ", foreground="#00ff00").pack(side=tk.LEFT)
        ttk.Label(chart_label_frame, text="内存: ", foreground="#ff6600").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(chart_label_frame, text="Max CPU: ").pack(side=tk.LEFT, padx=(20, 0))
        self.max_cpu_label = ttk.Label(chart_label_frame, text="0%")
        self.max_cpu_label.pack(side=tk.LEFT)
        ttk.Label(chart_label_frame, text="Max Memory: ").pack(side=tk.LEFT, padx=(20, 0))
        self.max_memory_label = ttk.Label(chart_label_frame, text="0%")
        self.max_memory_label.pack(side=tk.LEFT)
        
        monitor_frame = ttk.LabelFrame(main_frame, text="实时状态", padding="10")
        monitor_frame.pack(fill=tk.X)
        
        self.cpu_label = ttk.Label(monitor_frame, text="CPU: N/A", style='Monitor.TLabel')
        self.cpu_label.pack(side=tk.LEFT, padx=20)
        
        self.memory_label = ttk.Label(monitor_frame, text="内存: N/A", style='Monitor.TLabel')
        self.memory_label.pack(side=tk.LEFT, padx=20)
        
        self.progress_label = ttk.Label(monitor_frame, text="状态: 待机", style='Monitor.TLabel')
        self.progress_label.pack(side=tk.RIGHT)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.draw_chart()
        
    def monitor_resources(self):
        while not self.stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=0.2)
                memory_percent = psutil.virtual_memory().percent
                
                self.cpu_label.config(text=f"CPU: {cpu_percent:.1f}%")
                self.memory_label.config(text=f"内存: {memory_percent:.1f}%")
                
                self.cpu_history.append(cpu_percent)
                self.memory_history.append(memory_percent)
                
                if cpu_percent > self.max_cpu:
                    self.max_cpu = cpu_percent
                    self.max_cpu_label.config(text=f"{self.max_cpu:.1f}%")
                if memory_percent > self.max_memory:
                    self.max_memory = memory_percent
                    self.max_memory_label.config(text=f"{self.max_memory:.1f}%")
                
                resource_limit = int(self.resource_var.get())
                
                if cpu_percent >= resource_limit or memory_percent >= resource_limit:
                    self.update_result("警告：资源占用过高，正在停止计算...\n")
                    self.stop_event.set()
                    break
                    
            except Exception as e:
                pass
            
            time.sleep(0.1)
    
    def draw_chart(self):
        try:
            canvas = self.chart_canvas
            width = canvas.winfo_width()
            if width < 100:
                width = 800
            height = 150
            
            canvas.delete("all")
            
            # Draw grid
            for i in range(1, 5):
                y = height * i / 5
                canvas.create_line(0, y, width, y, fill="#333333")
            
            # Draw CPU line (green)
            if len(self.cpu_history) > 1:
                points = []
                for i, val in enumerate(self.cpu_history):
                    x = (i / len(self.cpu_history)) * width
                    y = height - (val / 100) * height
                    points.extend([x, y])
                if len(points) >= 4:
                    canvas.create_line(points, fill="#00ff00", width=2)
            
            # Draw memory line (orange)
            if len(self.memory_history) > 1:
                points = []
                for i, val in enumerate(self.memory_history):
                    x = (i / len(self.memory_history)) * width
                    y = height - (val / 100) * height
                    points.extend([x, y])
                if len(points) >= 4:
                    canvas.create_line(points, fill="#ff6600", width=2)
        except:
            pass
        
        if not self.stop_event.is_set():
            self.root.after(100, self.draw_chart)
    
    def update_result(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.root.update()
    
    def copy_to_clipboard(self):
        if self.pi_result:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.pi_result)
            self.progress_label.config(text="状态: 已拷贝到剪贴板！")
            messagebox.showinfo("成功", f"已将 {len(self.pi_result)} 个字符拷贝到剪贴板！")
        else:
            messagebox.showwarning("警告", "没有可拷贝的结果")
    
    def save_to_file(self):
        if not self.pi_result:
            messagebox.showwarning("警告", "没有可保存的结果")
            return
        
        current_digits = max(self.current_digits, 0) if hasattr(self, 'current_digits') else 100
        current_time = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        
        filename = "Pi.txt"
        
        existing_digits = 0
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("Digits:"):
                            existing_digits = int(line.split(":")[1].strip())
                            break
        except:
            pass
        
        if current_digits <= existing_digits and existing_digits > 0:
            messagebox.showinfo("提示", f"文件中已有更高精度 ({existing_digits} 位)，无需更新")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Time: {current_time:.4f}\n")
                f.write(f"Max_CPU: {self.max_cpu:.1f}\n")
                f.write(f"Max_Memory: {self.max_memory:.1f}\n")
                f.write(f"Digits: {current_digits}\n")
                f.write("\n")
                f.write(self.pi_result)
            
            messagebox.showinfo("成功", f"已保存 {current_digits} 位 π 到 {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def calculate_pi_high_precision(self, digits, slow_mode=False):
        if USE_MPMATH:
            mp.mp.dps = digits + 10
            pi_value = mp.pi
            result = str(pi_value)
            
            if slow_mode:
                self.update_result("\n慢速模式：正在进行密集计算...\n")
                for i in range(digits * 100):
                    if self.stop_event.is_set():
                        break
                    # 进行一些无用但密集的计算来浪费时间和CPU
                    x = 0.0
                    for j in range(1000):
                        x += (i * j * 3.14159) % 2.71828
                        if self.stop_event.is_set():
                            break
                    if i % 10000 == 0:
                        self.update_result(f"进度: {i/(digits*100)*100:.1f}%\n")
            
            return result
        else:
            from decimal import Decimal, getcontext
            getcontext().prec = digits + 50
            return str(Decimal('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679')[:digits+2])
    

    
    def calculate_pi_monte_carlo(self, num_threads, total_points, slow_mode=False):
        import random
        import math
        
        points_per_thread = total_points // num_threads
        hit_count = 0
        lock = threading.Lock()
        threads = []
        
        def calculate_thread(thread_id):
            nonlocal hit_count
            local_hits = 0
            random.seed(thread_id + int(time.time() * 1000))
            
            for idx in range(points_per_thread):
                if self.stop_event.is_set():
                    break
                
                x = random.random()
                y = random.random()
                if x**2 + y**2 <= 1.0:
                    local_hits += 1
                
                if slow_mode:
                    for k in range(1000):
                        r = math.sqrt(x*x + y*y)
                        if r <= 1.0:
                            local_hits += 1
                        x = random.random()
                        y = random.random()
                        if self.stop_event.is_set():
                            break
            
            with lock:
                hit_count += local_hits
            
            if not self.stop_event.is_set():
                self.update_result(f"线程 {thread_id:3d} 完成，命中 {local_hits} 次\n")
        
        for i in range(num_threads):
            if self.stop_event.is_set():
                break
            t = threading.Thread(target=calculate_thread, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        if hit_count > 0:
            pi_estimate = 4.0 * hit_count / total_points
            return str(pi_estimate)
        return "0"
    
    def start_calculation(self):
        try:
            num_threads = int(self.thread_var.get())
            total_points = int(self.points_var.get())
            digits = int(self.digits_var.get())
            resource_limit = int(self.resource_var.get())
            
            if num_threads <= 0 or total_points <= 0 or digits <= 0:
                messagebox.showerror("错误", "所有数值参数必须大于0")
                return
            if resource_limit < 1 or resource_limit > 100:
                messagebox.showerror("错误", "资源限制必须在1-100之间")
                return
                
        except ValueError:
            messagebox.showerror("错误", "请输入有效的整数")
            return
        
        self.stop_event.clear()
        self.is_calculating = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_label.config(text="状态: 计算中...")
        
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        self.cpu_history.clear()
        self.memory_history.clear()
        self.max_cpu = 0
        self.max_memory = 0
        self.max_cpu_label.config(text="0%")
        self.max_memory_label.config(text="0%")
        
        self.current_digits = digits
        slow_mode = self.slow_var.get()
        
        if self.auto_thread_var.get():
            cpu_count = os.cpu_count() or 4
            num_threads = cpu_count * 4
            points_per_thread = total_points // num_threads
        
        monitor_thread = threading.Thread(target=self.monitor_resources, daemon=True)
        monitor_thread.start()
        
        def calc_thread():
            self.start_time = time.time()
            self.pi_result = ""
            
            actual_threads = num_threads
            if self.auto_thread_var.get():
                cpu_count = os.cpu_count() or 4
                actual_threads = cpu_count * 4
                total_points = actual_threads * (total_points // num_threads)
            
            self.update_result(f"开始计算...\n")
            self.update_result(f"线程数: {actual_threads}, 采样点: {total_points}, 精度: {digits}位\n")
            self.update_result(f"资源限制: {resource_limit}%\n")
            self.update_result(f"慢速模式: {'开启' if slow_mode else '关闭'}\n")
            self.update_result(f"自动线程: {'开启' if self.auto_thread_var.get() else '关闭'}\n\n")
            
            if digits > 15 and USE_MPMATH:
                self.update_result("使用 mpmath 高精度计算模式...\n\n")
                pi_result = self.calculate_pi_high_precision(digits, slow_mode)
                self.pi_result = pi_result[:digits+2]
                self.update_result(f"π = {self.pi_result}\n\n")
            else:
                self.update_result("使用蒙特卡洛方法计算...\n\n")
                pi_result = self.calculate_pi_monte_carlo(num_threads, total_points, slow_mode)
                self.pi_result = pi_result
                self.update_result(f"π ≈ {self.pi_result}\n\n")
                self.update_result(f"实际 π = 3.14159265358979...\n")
            
            elapsed_time = time.time() - self.start_time
            self.update_result(f"\n计算完成！耗时: {elapsed_time:.4f} 秒\n")
            self.update_result(f"结果长度: {len(self.pi_result)} 个字符\n")
            
            self.is_calculating = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
            self.progress_label.config(text="状态: 完成")
        
        thread = threading.Thread(target=calc_thread)
        thread.start()
    
    def stop_calculation(self):
        self.stop_event.set()
        self.progress_label.config(text="状态: 正在停止...")
        self.update_result("\n正在停止计算...\n")
        
        def wait_and_reset():
            time.sleep(2)
            if self.is_calculating:
                self.update_result("\n强制重置状态...\n")
                self.is_calculating = False
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.copy_button.config(state=tk.DISABLED)
                self.save_button.config(state=tk.DISABLED)
                self.progress_label.config(text="状态: 已停止")
        
        threading.Thread(target=wait_and_reset, daemon=True).start()
    
    def on_closing(self):
        if self.is_calculating:
            if messagebox.askokcancel("退出", "计算正在进行中，确定要退出吗？"):
                self.stop_event.set()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    
    try:
        root.iconbitmap('pi_icon.ico')
    except:
        pass
    
    app = PiCalculatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
