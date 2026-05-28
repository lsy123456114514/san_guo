#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import datetime

try:
    import psutil
except ImportError:
    psutil = None

try:
    import mpmath as mp
    USE_MPMATH = True
except ImportError:
    USE_MPMATH = False

class PiCalculatorLight:
    def __init__(self, root):
        self.root = root
        self.root.title("π计算器")
        self.root.geometry("600x500")
        
        self.stop_event = threading.Event()
        self.is_calculating = False
        self.pi_result = ""
        
        self.create_widgets()
    
    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="π计算器", font=('Arial', 16, 'bold')).pack(pady=10)
        
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="小数位数:").pack(side=tk.LEFT)
        self.digits_entry = ttk.Entry(row1, width=10)
        self.digits_entry.insert(0, "100")
        self.digits_entry.pack(side=tk.LEFT, padx=5)
        
        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="线程数:").pack(side=tk.LEFT)
        self.threads_entry = ttk.Entry(row2, width=10)
        self.threads_entry.insert(0, "4")
        self.threads_entry.pack(side=tk.LEFT, padx=5)
        
        self.start_button = ttk.Button(frame, text="开始计算", command=self.start_calculation)
        self.start_button.pack(pady=10)
        
        self.stop_button = ttk.Button(frame, text="停止", command=self.stop_calculation, state=tk.DISABLED)
        self.stop_button.pack(pady=5)
        
        self.result_text = tk.Text(frame, wrap=tk.WORD, state=tk.DISABLED, height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.status_label = ttk.Label(frame, text="状态: 就绪")
        self.status_label.pack(pady=5)
    
    def update_result(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.root.update()
    
    def calculate_pi(self, digits):
        if USE_MPMATH:
            mp.mp.dps = digits + 10
            return str(mp.pi)[:digits+2]
        else:
            return "3.14159265358979323846"
    
    def start_calculation(self):
        try:
            digits = int(self.digits