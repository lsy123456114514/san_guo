# -*- coding: utf-8 -*-
"""
声纹识别系统 - 终极版
功能：录入、识别、录音音频、持续监听、自动播放
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import librosa
import sounddevice as sd
from scipy.spatial.distance import cosine
import json
import os
from pathlib import Path
import threading
import time
from pygame import mixer


class VoiceprintUltimate:
    def __init__(self, root):
        self.root = root
        self.root.title("🔊 声纹识别系统 - 终极版")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        self.data_dir = Path("voice_data_ultimate")
        self.audio_recordings_dir = self.data_dir / "recordings"
        self.data_dir.mkdir(exist_ok=True)
        self.audio_recordings_dir.mkdir(exist_ok=True)
        
        self.voices_file = self.data_dir / "voices.json"
        self.user_audio_file = self.data_dir / "user_audio.json"
        self.voices = self.load_voices()
        self.user_audio = self.load_user_audio()
        
        self.is_listening = False
        self.listen_thread = None
        self.mixer_initialized = False
        self.current_recording_name = None
        self.is_playing_audio = False
        self.play_cooldown_until = 0
        
        self.setup_ui()
        self.update_user_list()
    
    def load_voices(self):
        if self.voices_file.exists():
            with open(self.voices_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_voices(self):
        with open(self.voices_file, 'w', encoding='utf-8') as f:
            json.dump(self.voices, f, ensure_ascii=False, indent=2)
    
    def load_user_audio(self):
        if self.user_audio_file.exists():
            with open(self.user_audio_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_user_audio(self):
        with open(self.user_audio_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_audio, f, ensure_ascii=False, indent=2)
    
    def init_mixer(self):
        if not self.mixer_initialized:
            try:
                mixer.init()
                self.mixer_initialized = True
            except Exception as e:
                messagebox.showerror("错误", f"无法初始化音频播放器: {e}")
    
    def play_audio(self, audio_path):
        try:
            self.init_mixer()
            if os.path.exists(audio_path):
                self.is_playing_audio = True
                self.play_cooldown_until = time.time() + 1
                
                mixer.music.load(audio_path)
                mixer.music.play()
                
                self.root.after(1000, self.on_playback_complete)
                
                return True
            return False
        except Exception as e:
            print(f"播放错误: {e}")
            self.is_playing_audio = False
            return False
    
    def on_playback_complete(self):
        self.is_playing_audio = False
    
    def setup_ui(self):
        title_label = tk.Label(
            self.root,
            text="🔊 声纹识别系统 - 终极版",
            font=("Microsoft YaHei", 24, "bold"),
            bg="#2C3E50",
            fg="white",
            pady=15
        )
        title_label.pack(fill=tk.X)
        
        main_frame = tk.Frame(self.root, bg="#ECF0F1", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(main_frame, bg="#ECF0F1")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = tk.Frame(main_frame, bg="#ECF0F1")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_input_panel(left_frame)
        self.setup_user_list_panel(right_frame)
        self.setup_control_panel(left_frame)
    
    def setup_input_panel(self, parent):
        input_frame = tk.LabelFrame(
            parent,
            text="📝 录入 & 录音",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#2C3E50",
            padx=10,
            pady=10
        )
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            input_frame,
            text="姓名:",
            font=("Microsoft YaHei", 10),
            bg="#ECF0F1"
        ).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.name_entry = tk.Entry(input_frame, font=("Microsoft YaHei", 10), width=20)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
        
        self.register_btn = tk.Button(
            input_frame,
            text="🎤 录入声纹",
            font=("Microsoft YaHei", 10, "bold"),
            bg="#3498DB",
            fg="white",
            activebackground="#2980B9",
            padx=15,
            pady=8,
            command=self.register_voice
        )
        self.register_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.status_label = tk.Label(
            input_frame,
            text="状态: 准备就绪",
            font=("Microsoft YaHei", 9),
            bg="#ECF0F1",
            fg="#7F8C8D",
            width=25
        )
        self.status_label.grid(row=1, column=0, columnspan=4, pady=5)
        
        separator = tk.Frame(input_frame, height=2, bd=1, relief=tk.SUNKEN, bg="#BDC3C7")
        separator.grid(row=2, column=0, columnspan=4, sticky=tk.EW, pady=10)
        
        tk.Label(
            input_frame,
            text="录音音频 (设为监听播放):",
            font=("Microsoft YaHei", 10, "bold"),
            bg="#ECF0F1",
            fg="#8E44AD"
        ).grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W)
        
        self.record_audio_btn = tk.Button(
            input_frame,
            text="🔴 开始录音 (3秒)",
            font=("Microsoft YaHei", 10, "bold"),
            bg="#E74C3C",
            fg="white",
            activebackground="#C0392B",
            padx=15,
            pady=8,
            command=self.record_audio_for_user
        )
        self.record_audio_btn.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        self.audio_status = tk.Label(
            input_frame,
            text="未录音",
            font=("Microsoft YaHei", 9),
            bg="#ECF0F1",
            fg="#95A5A6",
            width=15
        )
        self.audio_status.grid(row=4, column=2, columnspan=2, padx=5, pady=5)
        
        self.save_audio_btn = tk.Button(
            input_frame,
            text="💾 保存为音频",
            font=("Microsoft YaHei", 9),
            bg="#27AE60",
            fg="white",
            activebackground="#229954",
            padx=10,
            pady=5,
            command=self.save_recorded_audio
        )
        self.save_audio_btn.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        self.test_audio_btn = tk.Button(
            input_frame,
            text="▶️ 试听",
            font=("Microsoft YaHei", 9),
            bg="#3498DB",
            fg="white",
            activebackground="#2980B9",
            padx=10,
            pady=5,
            command=self.test_recorded_audio
        )
        self.test_audio_btn.grid(row=5, column=2, columnspan=2, padx=5, pady=5, sticky=tk.EW)
    
    def setup_user_list_panel(self, parent):
        list_frame = tk.LabelFrame(
            parent,
            text="👥 用户管理",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#2C3E50",
            padx=10,
            pady=10
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.users_listbox = tk.Listbox(
            list_frame,
            font=("Microsoft YaHei", 9),
            yscrollcommand=scrollbar.set,
            height=15,
            bg="white",
            selectbackground="#3498DB",
            selectforeground="white"
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.users_listbox.yview)
        
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        btn_row = tk.Frame(list_frame, bg="#ECF0F1")
        btn_row.pack(fill=tk.X, pady=(10, 0))
        
        self.refresh_btn = tk.Button(
            btn_row,
            text="🔄 刷新",
            font=("Microsoft YaHei", 8),
            bg="#95A5A6",
            fg="white",
            padx=8,
            pady=4,
            command=self.update_user_list
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        
        self.re_register_btn = tk.Button(
            btn_row,
            text="🎤 重新录入",
            font=("Microsoft YaHei", 8),
            bg="#3498DB",
            fg="white",
            padx=8,
            pady=4,
            command=self.reregister_selected_user
        )
        self.re_register_btn.pack(side=tk.LEFT, padx=2)
        
        self.delete_btn = tk.Button(
            btn_row,
            text="🗑️ 删除",
            font=("Microsoft YaHei", 8),
            bg="#E74C3C",
            fg="white",
            padx=8,
            pady=4,
            command=self.delete_selected_user
        )
        self.delete_btn.pack(side=tk.LEFT, padx=2)
        
        self.clear_all_btn = tk.Button(
            btn_row,
            text="⚠️ 清空全部",
            font=("Microsoft YaHei", 8),
            bg="#C0392B",
            fg="white",
            padx=8,
            pady=4,
            command=self.clear_all_users
        )
        self.clear_all_btn.pack(side=tk.LEFT, padx=2)
        
        self.play_btn = tk.Button(
            btn_row,
            text="▶️ 播放音频",
            font=("Microsoft YaHei", 8),
            bg="#27AE60",
            fg="white",
            padx=8,
            pady=4,
            command=self.play_selected_user_audio
        )
        self.play_btn.pack(side=tk.LEFT, padx=2)
    
    def setup_control_panel(self, parent):
        control_frame = tk.LabelFrame(
            parent,
            text="🎯 控制面板",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#E74C3C",
            padx=10,
            pady=10
        )
        control_frame.pack(fill=tk.X)
        
        self.listen_btn = tk.Button(
            control_frame,
            text="🔴 开始持续监听",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#E74C3C",
            fg="white",
            activebackground="#C0392B",
            padx=30,
            pady=15,
            command=self.toggle_listening
        )
        self.listen_btn.pack(pady=10)
        
        tk.Label(
            control_frame,
            text="💡 开启后持续监听，识别到已注册用户后自动播放其音频",
            font=("Microsoft YaHei", 8),
            bg="#ECF0F1",
            fg="#7F8C8D"
        ).pack(pady=5)
        
        self.listen_status = tk.Label(
            control_frame,
            text="监听状态: 已停止",
            font=("Microsoft YaHei", 11),
            bg="#ECF0F1",
            fg="#7F8C8D"
        )
        self.listen_status.pack(pady=5)
        
        self.listen_result = tk.Label(
            control_frame,
            text="",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#27AE60"
        )
        self.listen_result.pack(pady=5)
        
        separator2 = tk.Frame(control_frame, height=2, bd=1, relief=tk.SUNKEN, bg="#BDC3C7")
        separator2.pack(fill=tk.X, pady=10)
        
        self.recognize_btn = tk.Button(
            control_frame,
            text="🎤 单次识别 (3秒)",
            font=("Microsoft YaHei", 10, "bold"),
            bg="#27AE60",
            fg="white",
            activebackground="#229954",
            padx=20,
            pady=10,
            command=self.recognize_voice
        )
        self.recognize_btn.pack(pady=5)
        
        self.recognize_result = tk.Label(
            control_frame,
            text="",
            font=("Microsoft YaHei", 10),
            bg="#ECF0F1",
            fg="#3498DB"
        )
        self.recognize_result.pack(pady=5)
    
    def update_user_list(self):
        self.users_listbox.delete(0, tk.END)
        if not self.voices:
            self.users_listbox.insert(0, "(暂无注册用户)")
        else:
            for name in sorted(self.voices.keys()):
                has_voice = "✓"
                has_audio = "✓" if name in self.user_audio and os.path.exists(self.user_audio[name]) else "✗"
                self.users_listbox.insert(tk.END, f"{name} [声纹:{has_voice}] [音频:{has_audio}]")
    
    def on_user_select(self, event):
        selection = self.users_listbox.curselection()
        if selection:
            user_text = self.users_listbox.get(selection[0])
            name = user_text.split(" [")[0]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name)
            
            if name in self.user_audio and os.path.exists(self.user_audio[name]):
                self.audio_status.config(text=f"已设置音频", fg="#27AE60")
            else:
                self.audio_status.config(text="未录音", fg="#95A5A6")
    
    def extract_features(self, audio, sr):
        if audio is None or len(audio) == 0:
            raise ValueError("音频数据为空")
        
        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        
        if not np.isfinite(audio).all():
            audio = np.clip(audio, -1.0, 1.0)
        
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        mfccs_mean = np.mean(mfccs.T, axis=0)
        
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        chroma_mean = np.mean(chroma.T, axis=0)
        
        mel = librosa.feature.melspectrogram(y=audio, sr=sr)
        mel_mean = np.mean(mel.T, axis=0)
        
        features = np.concatenate([mfccs_mean, chroma_mean, mel_mean])
        return features
    
    def record_audio_async(self, duration=3, samplerate=16000):
        audio_buffer = []
        
        def callback(indata, frame_count, time, status):
            audio_buffer.append(indata.copy())
        
        stream = sd.InputStream(
            samplerate=samplerate,
            channels=1,
            dtype='float32',
            callback=callback
        )
        
        with stream:
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(0.1)
        
        if audio_buffer:
            audio = np.concatenate(audio_buffer)
            audio = audio.flatten()
        else:
            audio = np.zeros(int(duration * samplerate), dtype='float32')
        
        return audio, samplerate
    
    def register_voice(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入姓名！")
            return
        
        self.register_btn.config(state=tk.DISABLED, text="录入中...")
        self.status_label.config(text="请对着麦克风说话...", fg="#E67E22")
        
        def recording():
            try:
                audio, sr = self.record_audio_async(3)
                features = self.extract_features(audio, sr)
                
                self.voices[name] = features.tolist()
                self.save_voices()
                
                self.root.after(0, self.on_register_complete, name)
            except Exception as e:
                self.root.after(0, lambda: self.on_register_error(str(e)))
        
        threading.Thread(target=recording, daemon=True).start()
    
    def on_register_complete(self, name):
        self.register_btn.config(state=tk.NORMAL, text="🎤 录入声纹")
        self.status_label.config(text=f"✓ {name} 录入成功！", fg="#27AE60")
        self.update_user_list()
        messagebox.showinfo("成功", f"✓ 用户 '{name}' 声纹录入成功！")
    
    def on_register_error(self, error_msg):
        self.register_btn.config(state=tk.NORMAL, text="🎤 录入声纹")
        self.status_label.config(text="录入失败", fg="#E74C3C")
        messagebox.showerror("错误", f"录入失败: {error_msg}")
    
    def record_audio_for_user(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("提示", "请先输入或选择姓名！")
            return
        
        self.current_recording_name = name
        self.record_audio_btn.config(state=tk.DISABLED, text="录音中...")
        self.audio_status.config(text="正在录音...", fg="#E67E22")
        
        def recording():
            try:
                audio, sr = self.record_audio_async(3)
                
                timestamp = int(time.time())
                filename = self.audio_recordings_dir / f"{name}_{timestamp}.wav"
                
                import scipy.io.wavfile as wavfile
                wavfile.write(str(filename), sr, (audio * 32767).astype(np.int16))
                
                self.recorded_audio_path = str(filename)
                self.root.after(0, self.on_record_complete, name)
            except Exception as e:
                self.root.after(0, lambda: self.on_record_error(str(e)))
        
        threading.Thread(target=recording, daemon=True).start()
    
    def on_record_complete(self, name):
        self.record_audio_btn.config(state=tk.NORMAL, text="🔴 开始录音 (3秒)")
        self.audio_status.config(text="录音完成 ✓", fg="#27AE60")
        messagebox.showinfo("成功", f"✓ 为 '{name}' 录音成功！\n\n现在点击【保存为音频】将此录音设为监听播放音频。")
    
    def on_record_error(self, error_msg):
        self.record_audio_btn.config(state=tk.NORMAL, text="🔴 开始录音 (3秒)")
        self.audio_status.config(text="录音失败", fg="#E74C3C")
        messagebox.showerror("错误", f"录音失败: {error_msg}")
    
    def save_recorded_audio(self):
        if not hasattr(self, 'recorded_audio_path'):
            messagebox.showwarning("提示", "请先录制音频！")
            return
        
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入姓名！")
            return
        
        self.user_audio[name] = self.recorded_audio_path
        self.save_user_audio()
        
        messagebox.showinfo("成功", f"✓ 已为 '{name}' 保存音频！")
        self.update_user_list()
        self.audio_status.config(text=f"已保存: {name}", fg="#27AE60")
    
    def test_recorded_audio(self):
        if not hasattr(self, 'recorded_audio_path'):
            messagebox.showwarning("提示", "请先录制音频！")
            return
        
        if os.path.exists(self.recorded_audio_path):
            self.play_audio(self.recorded_audio_path)
            messagebox.showinfo("播放", "正在播放录音...")
        else:
            messagebox.showerror("错误", "音频文件不存在！")
    
    def reregister_selected_user(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请选择要重新录入的用户！")
            return
        
        user_text = self.users_listbox.get(selection[0])
        name = user_text.split(" [")[0]
        
        result = messagebox.askyesno("确认", f"确定要重新录入 '{name}' 的声纹吗？\n原有声纹将被覆盖！")
        if result:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name)
            self.register_voice()
    
    def delete_selected_user(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请选择要删除的用户！")
            return
        
        user_text = self.users_listbox.get(selection[0])
        name = user_text.split(" [")[0]
        
        result = messagebox.askyesno("确认", f"确定删除用户 '{name}' 吗？")
        if result:
            if name in self.voices:
                del self.voices[name]
                self.save_voices()
            if name in self.user_audio:
                audio_path = self.user_audio[name]
                del self.user_audio[name]
                self.save_user_audio()
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except:
                        pass
            
            self.update_user_list()
            messagebox.showinfo("成功", f"✓ 用户 '{name}' 已删除")
    
    def clear_all_users(self):
        if not self.voices:
            messagebox.showwarning("提示", "暂无用户可删除！")
            return
        
        result = messagebox.askyesno(
            "⚠️ 警告",
            "确定要清空所有用户数据吗？\n此操作不可恢复！",
            icon='warning'
        )
        if result:
            for audio_path in self.user_audio.values():
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except:
                        pass
            
            self.voices.clear()
            self.user_audio.clear()
            self.save_voices()
            self.save_user_audio()
            
            self.update_user_list()
            messagebox.showinfo("成功", "✓ 所有用户数据已清空！")
    
    def play_selected_user_audio(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请选择用户！")
            return
        
        user_text = self.users_listbox.get(selection[0])
        name = user_text.split(" [")[0]
        
        if name in self.user_audio and os.path.exists(self.user_audio[name]):
            if self.play_audio(self.user_audio[name]):
                messagebox.showinfo("播放", f"正在播放 {name} 的音频...")
            else:
                messagebox.showerror("错误", "播放失败！")
        else:
            messagebox.showwarning("提示", f"用户 '{name}' 尚未设置音频！\n可以为其录制音频。")
    
    def toggle_listening(self):
        if not self.is_listening:
            if not self.voices:
                messagebox.showwarning("提示", "请先录入声纹！")
                return
            
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        self.is_listening = True
        self.listen_btn.config(text="⏹ 停止监听", bg="#95A5A6")
        self.listen_status.config(text="监听状态: 监听中...", fg="#E74C3C")
        self.listen_result.config(text="")
        
        self.listen_thread = threading.Thread(target=self.listening_loop, daemon=True)
        self.listen_thread.start()
    
    def stop_listening(self):
        self.is_listening = False
        self.is_playing_audio = False
        self.play_cooldown_until = 0
        try:
            mixer.music.stop()
        except:
            pass
        self.listen_btn.config(text="🔴 开始持续监听", bg="#E74C3C")
        self.listen_status.config(text="监听状态: 已停止", fg="#7F8C8D")
        self.listen_result.config(text="")
    
    def listening_loop(self):
        last_recognized = None
        cooldown_until = 0
        
        while self.is_listening:
            try:
                current_time = time.time()
                
                if self.is_playing_audio or current_time < self.play_cooldown_until:
                    if current_time < self.play_cooldown_until:
                        remaining = int(self.play_cooldown_until - current_time)
                        self.root.after(0, lambda r=remaining: self.listen_status.config(
                            text=f"监听状态: 回声检测中... ({r}秒)",
                            fg="#E67E22"
                        ))
                    time.sleep(0.5)
                    continue
                
                audio, sr = self.record_audio_async(2)
                features = self.extract_features(audio, sr)
                
                audio_energy = np.sqrt(np.mean(audio**2))
                if audio_energy < 0.01:
                    time.sleep(0.3)
                    continue
                
                best_match = None
                best_score = 0
                
                for name, voice_features in self.voices.items():
                    voice_array = np.array(voice_features)
                    similarity = 1 - cosine(features, voice_array)
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = name
                
                if best_match and best_score >= 0.7:
                    if current_time > cooldown_until and best_match != last_recognized:
                        last_recognized = best_match
                        cooldown_until = current_time + 5
                        
                        self.root.after(0, lambda n=best_match, s=best_score: self.listen_result.config(
                            text=f"✓ 识别: {n} ({s:.2%})",
                            fg="#27AE60"
                        ))
                        
                        if best_match in self.user_audio and os.path.exists(self.user_audio[best_match]):
                            self.root.after(0, lambda p=self.user_audio[best_match]: self.play_audio(p))
                        else:
                            self.root.after(0, lambda: self.listen_result.config(
                                text=f"识别: {best_match} - 无音频",
                                fg="#E67E22"
                            ))
                
                self.root.after(0, lambda: self.listen_status.config(
                    text="监听状态: 监听中...",
                    fg="#27AE60"
                ))
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"监听错误: {e}")
                time.sleep(1)
        
        self.root.after(0, lambda: self.listen_status.config(text="监听状态: 已停止", fg="#7F8C8D"))
    
    def recognize_voice(self):
        if not self.voices:
            messagebox.showwarning("提示", "请先录入声纹！")
            return
        
        self.recognize_btn.config(state=tk.DISABLED, text="识别中...")
        self.recognize_result.config(text="请对着麦克风说话...", fg="#E67E22")
        
        def recognizing():
            try:
                audio, sr = self.record_audio_async(3)
                features = self.extract_features(audio, sr)
                
                best_match = None
                best_score = 0
                
                for name, voice_features in self.voices.items():
                    voice_array = np.array(voice_features)
                    similarity = 1 - cosine(features, voice_array)
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = name
                
                self.root.after(0, self.on_recognize_complete, best_match, best_score)
            except Exception as e:
                self.root.after(0, lambda: self.on_recognize_error(str(e)))
        
        threading.Thread(target=recognizing, daemon=True).start()
    
    def on_recognize_complete(self, best_match, best_score):
        self.recognize_btn.config(state=tk.NORMAL, text="🎤 单次识别 (3秒)")
        
        if best_match and best_score >= 0.7:
            audio_info = ""
            if best_match in self.user_audio and os.path.exists(self.user_audio[best_match]):
                audio_info = " [有音频]"
            
            self.recognize_result.config(
                text=f"识别: {best_match} ({best_score:.2%}){audio_info}",
                fg="#27AE60"
            )
        else:
            self.recognize_result.config(
                text=f"未识别 (最佳: {best_score:.2%})",
                fg="#E74C3C"
            )
    
    def on_recognize_error(self, error_msg):
        self.recognize_btn.config(state=tk.NORMAL, text="🎤 单次识别 (3秒)")
        self.recognize_result.config(text="识别失败", fg="#E74C3C")


def main():
    root = tk.Tk()
    app = VoiceprintUltimate(root)
    root.mainloop()


if __name__ == "__main__":
    main()
