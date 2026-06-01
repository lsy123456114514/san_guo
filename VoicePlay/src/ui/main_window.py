# -*- coding: utf-8 -*-
"""
主窗口模块
VoicePlay的主界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os


class VoicePlayWindow:
    """主窗口类"""
    
    def __init__(self, root):
        self.root = root
        self.setup_style()
        self.create_widgets()
    
    def setup_style(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel', 
                       font=('Microsoft YaHei', 16, 'bold'),
                       foreground='#ffffff',
                       background='#2C3E50')
        
        style.configure('Tab.TNotebook',
                       background='#1a1a2e',
                       foreground='#ffffff')
        
        style.map('Tab.TNotebook.Tab',
                  background=[('selected', '#3498DB'), ('!selected', '#2C3E50')],
                  foreground=[('selected', '#ffffff'), ('!selected', '#bdc3c7')])
    
    def create_widgets(self):
        """创建界面组件"""
        self.create_notebook()
        
    def create_notebook(self):
        """创建多标签页"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_voice_tab()
        self.create_visual_tab()
        self.create_command_tab()
        self.create_fun_tab()
    
    def create_voice_tab(self):
        """创建声纹识别标签页"""
        voice_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(voice_frame, text='🎯 声纹识别')
        
        self.voice_recognizer = None
        
        top_frame = ttk.Frame(voice_frame)
        top_frame.pack(fill='x', pady=5)
        
        ttk.Label(top_frame, text='姓名:', font=('Microsoft YaHei', 12)).pack(side='left', padx=5)
        self.voice_name_entry = ttk.Entry(top_frame, font=('Microsoft YaHei', 12), width=20)
        self.voice_name_entry.pack(side='left', padx=5)
        
        ttk.Button(top_frame, text='🎤 录入声纹', 
                   command=self.register_voice).pack(side='left', padx=5)
        
        ttk.Button(top_frame, text='🔍 识别', 
                   command=self.recognize_voice).pack(side='left', padx=5)
        
        ttk.Button(top_frame, text='🔄 持续监听', 
                   command=self.toggle_listening).pack(side='left', padx=5)
        
        self.listen_status = ttk.Label(top_frame, text='', font=('Microsoft YaHei', 10))
        self.listen_status.pack(side='left', padx=10)
        
        self.voice_result = ttk.Label(voice_frame, text='', 
                                      font=('Microsoft YaHei', 14, 'bold'))
        self.voice_result.pack(pady=10)
        
        user_list_frame = ttk.LabelFrame(voice_frame, text='已注册用户', padding=10)
        user_list_frame.pack(fill='both', expand=True, pady=10)
        
        self.user_listbox = tk.Listbox(user_list_frame, 
                                       font=('Microsoft YaHei', 11),
                                       height=8,
                                       bg='#1a1a2e',
                                       fg='#ffffff',
                                       selectbackground='#3498DB')
        self.user_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(user_list_frame, orient='vertical', 
                                  command=self.user_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.user_listbox.config(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(voice_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text='🗑️ 删除', 
                   command=self.delete_user).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text='🔊 设置音频', 
                   command=self.set_user_audio).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text='▶️ 播放音频', 
                   command=self.play_user_audio).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text='⚠️ 清空全部', 
                   command=self.clear_all_users).pack(side='left', padx=5)
        
        self.init_voice_recognizer()
    
    def init_voice_recognizer(self):
        """初始化声纹识别器"""
        try:
            import sys
            import os
            src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            from voice_recognition import VoiceRecognizer
            self.voice_recognizer = VoiceRecognizer()
            self.update_user_list()
        except Exception as e:
            self.voice_recognizer = None
            messagebox.showwarning('提示', f'声纹识别模块初始化失败: {e}')
    
    def update_user_list(self):
        """更新用户列表"""
        self.user_listbox.delete(0, tk.END)
        if self.voice_recognizer:
            users = self.voice_recognizer.list_users()
            if users:
                for user in users:
                    has_audio = self.voice_recognizer.get_user_audio(user)
                    audio_status = '✓' if has_audio else '✗'
                    self.user_listbox.insert(tk.END, f'{user} [音频:{audio_status}]')
            else:
                self.user_listbox.insert(0, '(暂无用户)')
    
    def register_voice(self):
        """录入声纹"""
        name = self.voice_name_entry.get().strip()
        if not name:
            messagebox.showwarning('提示', '请输入姓名！')
            return
        
        if not self.voice_recognizer:
            messagebox.showerror('错误', '声纹识别器未初始化！')
            return
        
        self.voice_result.config(text='正在录入声纹...', foreground='#f39c12')
        
        def task():
            try:
                self.voice_recognizer.register_voice(name)
                self.root.after(0, lambda: self.on_register_complete(name))
            except Exception as e:
                self.root.after(0, lambda: self.on_register_error(str(e)))
        
        threading.Thread(target=task, daemon=True).start()
    
    def on_register_complete(self, name):
        """录入完成"""
        self.voice_result.config(text=f'✓ {name} 声纹录入成功！', foreground='#27ae60')
        self.update_user_list()
    
    def on_register_error(self, error):
        """录入失败"""
        self.voice_result.config(text=f'✗ 录入失败: {error}', foreground='#e74c3c')
    
    def recognize_voice(self):
        """识别说话人"""
        if not self.voice_recognizer:
            messagebox.showerror('错误', '声纹识别器未初始化！')
            return
        
        self.voice_result.config(text='正在识别...', foreground='#f39c12')
        
        def task():
            try:
                name, score = self.voice_recognizer.recognize()
                self.root.after(0, lambda: self.on_recognize_complete(name, score))
            except Exception as e:
                self.root.after(0, lambda: self.on_recognize_error(str(e)))
        
        threading.Thread(target=task, daemon=True).start()
    
    def on_recognize_complete(self, name, score):
        """识别完成"""
        if name:
            self.voice_result.config(text=f'✓ 识别: {name} ({score:.2%})', foreground='#27ae60')
        else:
            self.voice_result.config(text='✗ 未识别到匹配的声纹', foreground='#e74c3c')
    
    def on_recognize_error(self, error):
        """识别失败"""
        self.voice_result.config(text=f'✗ 识别失败: {error}', foreground='#e74c3c')
    
    def toggle_listening(self):
        """切换持续监听"""
        if not self.voice_recognizer:
            messagebox.showerror('错误', '声纹识别器未初始化！')
            return
        
        if hasattr(self, 'is_listening') and self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """开始持续监听"""
        self.is_listening = True
        self.listen_status.config(text='监听中...', foreground='#e74c3c')
        
        def listening_loop():
            while self.is_listening:
                try:
                    name, score = self.voice_recognizer.recognize()
                    if name:
                        self.root.after(0, lambda n=name, s=score: 
                                       self.voice_result.config(
                                           text=f'✓ 识别: {n} ({s:.2%})',
                                           foreground='#27ae60'))
                        audio_path = self.voice_recognizer.get_user_audio(name)
                        if audio_path and os.path.exists(audio_path):
                            self.play_audio_file(audio_path)
                            time.sleep(2)
                    time.sleep(0.5)
                except:
                    time.sleep(1)
        
        threading.Thread(target=listening_loop, daemon=True).start()
    
    def stop_listening(self):
        """停止监听"""
        self.is_listening = False
        self.listen_status.config(text='已停止', foreground='#7f8c8d')
    
    def play_audio_file(self, filepath):
        """播放音频文件"""
        try:
            from pygame import mixer
            mixer.init()
            mixer.music.load(filepath)
            mixer.music.play()
        except:
            pass
    
    def delete_user(self):
        """删除用户"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning('提示', '请选择用户！')
            return
        
        user_text = self.user_listbox.get(selection[0])
        name = user_text.split(' [')[0]
        
        if messagebox.askyesno('确认', f'确定删除 {name} 吗？'):
            self.voice_recognizer.delete_voice(name)
            self.update_user_list()
            messagebox.showinfo('成功', f'{name} 已删除')
    
    def set_user_audio(self):
        """设置用户音频"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning('提示', '请选择用户！')
            return
        
        user_text = self.user_listbox.get(selection[0])
        name = user_text.split(' [')[0]
        
        filepath = filedialog.askopenfilename(filetypes=[('音频文件', '*.wav *.mp3')])
        if filepath:
            self.voice_recognizer.set_user_audio(name, filepath)
            self.update_user_list()
            messagebox.showinfo('成功', f'已为 {name} 设置音频')
    
    def play_user_audio(self):
        """播放用户音频"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning('提示', '请选择用户！')
            return
        
        user_text = self.user_listbox.get(selection[0])
        name = user_text.split(' [')[0]
        
        audio_path = self.voice_recognizer.get_user_audio(name)
        if audio_path and os.path.exists(audio_path):
            self.play_audio_file(audio_path)
        else:
            messagebox.showwarning('提示', '该用户未设置音频！')
    
    def clear_all_users(self):
        """清空所有用户"""
        if not self.voice_recognizer.list_users():
            messagebox.showwarning('提示', '没有用户可删除！')
            return
        
        if messagebox.askyesno('⚠️ 警告', '确定清空所有用户？此操作不可恢复！'):
            for user in self.voice_recognizer.list_users():
                self.voice_recognizer.delete_voice(user)
            self.update_user_list()
            messagebox.showinfo('成功', '所有用户已清空')
    
    def create_visual_tab(self):
        """创建可视化标签页"""
        visual_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(visual_frame, text='🎨 声音可视化')
        
        self.visualizer_canvas = tk.Canvas(visual_frame, 
                                           bg='#1a1a2e',
                                           width=800,
                                           height=300)
        self.visualizer_canvas.pack(fill='both', expand=True)
        
        control_frame = ttk.Frame(visual_frame)
        control_frame.pack(fill='x', pady=10)
        
        ttk.Button(control_frame, text='▶️ 开始', 
                   command=self.start_visualization).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text='⏹ 停止', 
                   command=self.stop_visualization).pack(side='left', padx=5)
        
        self.visualizer = None
    
    def start_visualization(self):
        """开始可视化"""
        try:
            from audio_visualizer import SoundWaveVisualizer
            self.visualizer = SoundWaveVisualizer(self.visualizer_canvas)
            self.visualizer.start()
        except Exception as e:
            messagebox.showerror('错误', f'启动可视化失败: {e}')
    
    def stop_visualization(self):
        """停止可视化"""
        if self.visualizer:
            self.visualizer.stop()
            self.visualizer_canvas.delete('all')
    
    def create_command_tab(self):
        """创建语音命令标签页"""
        command_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(command_frame, text='🗣️ 语音命令')
        
        top_frame = ttk.Frame(command_frame)
        top_frame.pack(fill='x', pady=5)
        
        ttk.Label(top_frame, text='命令:', font=('Microsoft YaHei', 12)).pack(side='left', padx=5)
        self.command_phrase = ttk.Entry(top_frame, font=('Microsoft YaHei', 12), width=20)
        self.command_phrase.pack(side='left', padx=5)
        
        ttk.Label(top_frame, text='动作:', font=('Microsoft YaHei', 12)).pack(side='left', padx=5)
        self.command_action = ttk.Entry(top_frame, font=('Microsoft YaHei', 12), width=30)
        self.command_action.pack(side='left', padx=5)
        
        ttk.Button(top_frame, text='➕ 添加', 
                   command=self.add_command).pack(side='left', padx=5)
        
        ttk.Button(top_frame, text='🎤 监听', 
                   command=self.listen_command).pack(side='left', padx=5)
        
        self.command_result = ttk.Label(command_frame, text='', 
                                        font=('Microsoft YaHei', 12))
        self.command_result.pack(pady=10)
        
        command_list_frame = ttk.LabelFrame(command_frame, text='已添加命令', padding=10)
        command_list_frame.pack(fill='both', expand=True, pady=10)
        
        self.command_listbox = tk.Listbox(command_list_frame, 
                                          font=('Microsoft YaHei', 11),
                                          height=10,
                                          bg='#1a1a2e',
                                          fg='#ffffff',
                                          selectbackground='#3498DB')
        self.command_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(command_list_frame, orient='vertical', 
                                  command=self.command_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.command_listbox.config(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(command_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text='🗑️ 删除选中', 
                   command=self.delete_command).pack(side='left', padx=5)
        
        self.init_commands()
    
    def init_commands(self):
        """初始化命令管理器"""
        try:
            import sys
            import os
            src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            from voice_commands import VoiceCommands
            self.command_manager = VoiceCommands()
            self.update_command_list()
        except Exception as e:
            self.command_manager = None
            messagebox.showwarning('提示', f'语音命令模块未安装，此功能不可用: {e}')
    
    def update_command_list(self):
        """更新命令列表"""
        self.command_listbox.delete(0, tk.END)
        if self.command_manager:
            for phrase, action in self.command_manager.commands.items():
                self.command_listbox.insert(tk.END, f'{phrase} → {action}')
    
    def add_command(self):
        """添加命令"""
        if not self.command_manager:
            messagebox.showerror('错误', '命令管理器未初始化！')
            return
            
        phrase = self.command_phrase.get().strip()
        action = self.command_action.get().strip()
        
        if not phrase or not action:
            messagebox.showwarning('提示', '请输入命令短语和动作！')
            return
        
        self.command_manager.add_command(phrase, action)
        self.update_command_list()
        messagebox.showinfo('成功', f'已添加命令: {phrase}')
        
        self.command_phrase.delete(0, tk.END)
        self.command_action.delete(0, tk.END)
    
    def delete_command(self):
        """删除命令"""
        if not self.command_manager:
            messagebox.showerror('错误', '命令管理器未初始化！')
            return
            
        selection = self.command_listbox.curselection()
        if not selection:
            messagebox.showwarning('提示', '请选择命令！')
            return
        
        command_text = self.command_listbox.get(selection[0])
        phrase = command_text.split(' → ')[0]
        
        self.command_manager.remove_command(phrase)
        self.update_command_list()
        messagebox.showinfo('成功', f'已删除命令: {phrase}')
    
    def listen_command(self):
        """监听命令"""
        if not self.command_manager:
            messagebox.showerror('错误', '命令管理器未初始化！')
            return
        
        self.command_result.config(text='正在监听...', foreground='#f39c12')
        
        def task():
            try:
                success, msg = self.command_manager.listen_and_execute()
                self.root.after(0, lambda: self.on_command_result(success, msg))
            except Exception as e:
                self.root.after(0, lambda: self.command_result.config(
                    text=f'错误: {e}', foreground='#e74c3c'))
        
        threading.Thread(target=task, daemon=True).start()
    
    def on_command_result(self, success, msg):
        """命令执行结果"""
        if success:
            self.command_result.config(text=msg, foreground='#27ae60')
        else:
            self.command_result.config(text=msg, foreground='#e74c3c')
    
    def create_fun_tab(self):
        """创建趣味功能标签页"""
        fun_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(fun_frame, text='🎭 趣味功能')
        
        effect_frame = ttk.LabelFrame(fun_frame, text='变声效果', padding=10)
        effect_frame.pack(fill='x', pady=10)
        
        self.effect_var = tk.StringVar(value='none')
        effects = [
            ('无效果', 'none'),
            ('🎀 萝莉音', 'loli'),
            ('👴 大叔音', 'uncle'),
            ('🤖 机器人', 'robot'),
            ('📢 扩音器', 'megaphone'),
            ('🌊 回声', 'echo'),
            ('🏛️ 混响', 'reverb'),
        ]
        
        for text, value in effects:
            ttk.Radiobutton(effect_frame, text=text, variable=self.effect_var, 
                           value=value).pack(side='left', padx=10)
        
        control_frame = ttk.Frame(fun_frame)
        control_frame.pack(fill='x', pady=10)
        
        ttk.Button(control_frame, text='🎤 录音并播放', 
                   command=self.record_with_effect).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text='💾 保存录音', 
                   command=self.save_recording).pack(side='left', padx=5)
        
        self.fun_result = ttk.Label(fun_frame, text='', 
                                    font=('Microsoft YaHei', 12))
        self.fun_result.pack(pady=10)
        
        self.effect_processor = None
        self.last_recording = None
    
    def record_with_effect(self):
        """录音并应用效果"""
        try:
            from audio_effects import AudioEffects
            self.effect_processor = AudioEffects()
            
            effect = self.effect_var.get()
            self.fun_result.config(text=f'正在录音... (效果: {effect})', foreground='#f39c12')
            
            def task():
                try:
                    audio = self.effect_processor.record_and_play(duration=3, effect=effect)
                    self.last_recording = audio
                    self.root.after(0, lambda: self.fun_result.config(
                        text='✓ 录音播放完成！', foreground='#27ae60'))
                except Exception as e:
                    self.root.after(0, lambda: self.fun_result.config(
                        text=f'✗ 失败: {e}', foreground='#e74c3c'))
            
            threading.Thread(target=task, daemon=True).start()
        
        except Exception as e:
            messagebox.showerror('错误', f'初始化音效处理器失败: {e}')
    
    def save_recording(self):
        """保存录音"""
        if not self.last_recording is None:
            filepath = filedialog.asksaveasfilename(
                defaultextension='.wav',
                filetypes=[('WAV文件', '*.wav')]
            )
            if filepath:
                self.effect_processor.save_recording(self.last_recording, filepath)
                messagebox.showinfo('成功', '录音已保存！')
        else:
            messagebox.showwarning('提示', '请先录音！')
