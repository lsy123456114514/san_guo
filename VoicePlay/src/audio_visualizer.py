# -*- coding: utf-8 -*-
"""
声音可视化模块
提供炫酷的音频波形显示
"""

import tkinter as tk
import numpy as np
import sounddevice as sd
import threading
import time
import math


class SoundWaveVisualizer:
    """声波可视化器 - 简化版"""
    
    def __init__(self, canvas):
        self.canvas = canvas
        self.is_running = False
        self.amplitude = 0
        self.stream = None
        self.audio_buffer = []
    
    def start(self):
        """开始动画"""
        self.is_running = True
        self.audio_buffer = []
        
        def audio_callback(indata, frames, time, status):
            if not self.is_running:
                return
            # 计算音量
            self.amplitude = np.mean(np.abs(indata)) * 10
        
        try:
            self.stream = sd.InputStream(
                samplerate=44100,
                channels=1,
                callback=audio_callback
            )
            self.stream.start()
        except Exception as e:
            print(f"启动音频流失败: {e}")
        
        # 启动绘制线程
        threading.Thread(target=self.animate, daemon=True).start()
    
    def stop(self):
        """停止动画"""
        self.is_running = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
    
    def animate(self):
        """绘制动画"""
        while self.is_running:
            self.canvas.delete('all')
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width < 10 or height < 10:
                time.sleep(0.1)
                continue
            
            center_y = height // 2
            bar_width = width // 50
            gap = 2
            
            for i in range(50):
                x = i * (bar_width + gap)
                # 简单的波形效果
                wave = 0.5 + 0.5 * math.sin(i * 0.2 + time.time() * 3)
                bar_height = max(10, int(self.amplitude * 50 * wave))
                
                # 渐变色
                gradient = i / 50
                r = int(0xff * gradient)
                g = int(0x44 * (1 - gradient))
                b = int(0xff * (1 - gradient))
                color = f'#{r:02x}{g:02x}{b:02x}'
                
                self.canvas.create_rectangle(
                    x, center_y - bar_height,
                    x + bar_width, center_y + bar_height,
                    fill=color,
                    outline=''
                )
            
            time.sleep(0.05)
