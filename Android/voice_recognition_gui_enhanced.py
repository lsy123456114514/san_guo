# -*- coding: utf-8 -*-
"""
声纹识别系统 GUI增强版
支持持续监听和自动播放音频
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


class VoiceprintGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔊 声纹识别系统 - 增强版")
        self.root.geometry("700x650")
        self.root.resizable(False, False)
        
        self.data_dir = Path("voice_data_gui")
        self.audio_dir = self.data_dir / "user_audio"
        self.data_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
        
        self.voices_file = self.data_dir / "voices.json"
        self.voices = self.load_voices()
        self.user_audio = self.load_user_audio()
        
        self.is_recording = False
        self.is_listening = False
        self.listen_thread = None
        self.mixer_initialized = False
        
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
        audio_file = self.data_dir / "user_audio.json"
        if audio_file.exists():
            with open(audio_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_user_audio(self):
        audio_file = self.data_dir / "user_audio.json"
        with open(audio_file, 'w', encoding='utf-8') as f:
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
                mixer.music.load(audio_path)
                mixer.music.play()
                return True
            return False
        except Exception as e:
            messagebox.showerror("错误", f"播放音频失败: {e}")
            return False
    
    def setup_ui(self):
        title_label = tk.Label(
            self.root,
            text="🔊 声纹识别系统 - 增强版",
            font=("Microsoft YaHei", 24, "bold"),
            bg="#2C3E50",
            fg="white",
            pady=20
        )
        title_label.pack(fill=tk.X)
        
        main_frame = tk.Frame(self.root, bg="#ECF0F1", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        register_frame = tk.LabelFrame(
            main_frame,
            text="📝 录入声纹 & 设置音频",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#2C3E50",
            padx=15,
            pady=15
        )
        register_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            register_frame,
            text="姓名:",
            font=("Microsoft YaHei", 10),
            bg="#ECF0F1"
        ).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.name_entry = tk.Entry(
            register_frame,
            font=("Microsoft YaHei", 10),
            width=20
        )
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.register_btn = tk.Button(
            register_frame,
            text="🎤 录入声纹",
            font=("Microsoft YaHei", 10, "bold"),
            bg="#3498DB",
            fg="white",
            activebackground="#2980B9",
            activeforeground="white",
            padx=15,
            pady=8,
            command=self.register_voice
        )
        self.register_btn.grid(row=0, column=2, padx=5, pady=5)
        
        tk.Label(
            register_frame,
            text="音频:",
            font=("Microsoft YaHei", 10),
            bg="#ECF0F1"
        ).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.audio_entry = tk.Entry(
            register_frame,
            font=("Microsoft YaHei", 10),
            width=20
        )
        self.audio_entry.grid(row=1, column=1, padx=5, pady=5)
        
        self.browse_btn = tk.Button(
            register_frame,
            text="📂 浏览",
            font=("Microsoft YaHei", 9),
            bg="#9B59B6",
            fg="white",
            activebackground="#8E44AD",
            activeforeground="white",
            padx=10,
            pady=5,
            command=self.browse_audio
        )
        self.browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        self.save_audio_btn = tk.Button(
            register_frame,
            text="💾 保存设置",
            font=("Microsoft YaHei", 9, "bold"),
            bg="#16A085",
            fg="white",
            activebackground="#138D75",
            activeforeground="white",
            padx=10,
            pady=5,
            command=self.save_user_audio_setting
        )
        self.save_audio_btn.grid(row=1, column=3, padx=5, pady=5)
        
        listen_frame = tk.LabelFrame(
            main_frame,
            text="🎯 持续监听模式",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#E74C3C",
            padx=15,
            pady=15
        )
        listen_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.listen_btn = tk.Button(
            listen_frame,
            text="🔴 开始持续监听",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#E74C3C",
            fg="white",
            activebackground="#C0392B",
            activeforeground="white",
            padx=30,
            pady=12,
            command=self.toggle_listening
        )
        self.listen_btn.pack(pady=5)
        
        tk.Label(
            listen_frame,
            text="💡 开启后将持续监听，识别到已注册用户后自动播放其设置的音频",
            font=("Microsoft YaHei", 9),
            bg="#ECF0F1",
            fg="#7F8C8D"
        ).pack(pady=5)
        
        self.listen_status = tk.Label(
            listen_frame,
            text="监听状态: 已停止",
            font=("Microsoft YaHei", 11),
            bg="#ECF0F1",
            fg="#7F8C8D"
        )
        self.listen_status.pack(pady=5)
        
        self.listen_result = tk.Label(
            listen_frame,
            text="",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#ECF0F1",
            fg="#27AE60"
        )
        self.listen_result.pack(pady=5)
        
        quick_recognize_frame = tk.LabelFrame(
            main_frame,
            text="🎤 单次识别",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#2C3E50",
            padx=15,
            pady=15
        )
        quick_recognize_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.recognize_btn = tk.Button(
            quick_recognize_frame,
            text="🎤 开始识别 (3秒)",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#27AE60",
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            padx=25,
            pady=10,
            command=self.recognize_voice
        )
        self.recognize_btn.pack(pady=5)
        
        self.status_label = tk.Label(
            quick_recognize_frame,
            text="准备就绪",
            font=("Microsoft YaHei", 10),
            bg="#ECF0F1",
            fg="#7F8C8D"
        )
        self.status_label.pack(pady=5)
        
        self.result_label = tk.Label(
            quick_recognize_frame,
            text="",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#E74C3C"
        )
        self.result_label.pack(pady=5)
        
        users_frame = tk.LabelFrame(
            main_frame,
            text="👥 已注册用户 (带音频)",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#2C3E50",
            padx=15,
            pady=15
        )
        users_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(users_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.users_listbox = tk.Listbox(
            users_frame,
            font=("Microsoft YaHei", 10),
            yscrollcommand=scrollbar.set,
            height=5,
            bg="white",
            selectbackground="#3498DB",
            selectforeground="white"
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.users_listbox.yview)
        
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        btn_frame = tk.Frame(main_frame, bg="#ECF0F1")
        btn_frame.pack(fill=tk.X)
        
        self.delete_btn = tk.Button(
            btn_frame,
            text="🗑️ 删除",
            font=("Microsoft YaHei", 9),
            bg="#E74C3C",
            fg="white",
            activebackground="#C0392B",
            activeforeground="white",
            padx=15,
            pady=5,
            command=self.delete_user
        )
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        self.play_btn = tk.Button(
            btn_frame,
            text="▶️ 播放音频",
            font=("Microsoft YaHei", 9),
            bg="#3498DB",
            fg="white",
            activebackground="#2980B9",
            activeforeground="white",
            padx=15,
            pady=5,
            command=self.play_selected_audio
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = tk.Button(
            btn_frame,
            text="🔄 刷新",
            font=("Microsoft YaHei", 9),
            bg="#95A5A6",
            fg="white",
            activebackground="#7F8C8D",
            activeforeground="white",
            padx=15,
            pady=5,
            command=self.update_user_list
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
    
    def browse_audio(self):
        filename = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg *.m4a"), ("所有文件", "*.*")]
        )
        if filename:
            self.audio_entry.delete(0, tk.END)
            self.audio_entry.insert(0, filename)
    
    def save_user_audio_setting(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入姓名！")
            return
        
        audio_path = self.audio_entry.get().strip()
        if not audio_path:
            messagebox.showwarning("提示", "请选择音频文件！")
            return
        
        if not os.path.exists(audio_path):
            messagebox.showerror("错误", "音频文件不存在！")
            return
        
        if name not in self.user_audio:
            messagebox.showwarning("提示", "请先录入该用户的声纹！")
            return
        
        self.user_audio[name] = audio_path
        self.save_user_audio()
        messagebox.showinfo("成功", f"✓ 已为 '{name}' 保存音频设置！")
    
    def update_user_list(self):
        self.users_listbox.delete(0, tk.END)
        if not self.voices:
            self.users_listbox.insert(0, "(暂无注册用户)")
        else:
            for name in self.voices.keys():
                has_audio = "✓" if name in self.user_audio and os.path.exists(self.user_audio[name]) else "✗"
                self.users_listbox.insert(tk.END, f"{name} [音频:{has_audio}]")
    
    def on_user_select(self, event):
        selection = self.users_listbox.curselection()
        if selection:
            user_text = self.users_listbox.get(selection[0])
            name = user_text.split(" [")[0]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name)
            
            if name in self.user_audio:
                self.audio_entry.delete(0, tk.END)
                self.audio_entry.insert(0, self.user_audio[name])
    
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
    
    def record_audio(self, duration=3, samplerate=16000):
        try:
            sd.stop()
        except:
            pass
        
        audio_buffer = []
        
        def callback(indata, frame_count, time, status):
            if status:
                print(f"录音状态: {status}")
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
                audio, sr = self.record_audio(3)
                features = self.extract_features(audio, sr)
                
                self.voices[name] = features.tolist()
                self.save_voices()
                
                self.root.after(0, self.on_register_complete, name)
            except Exception as e:
                print(f"录入错误: {e}")
                self.root.after(0, lambda: self.on_register_error(str(e)))
        
        threading.Thread(target=recording, daemon=True).start()
    
    def on_register_error(self, error_msg):
        self.register_btn.config(state=tk.NORMAL, text="🎤 录入声纹")
        self.status_label.config(text="录入失败，请重试", fg="#E74C3C")
        messagebox.showerror("错误", f"录入声纹失败: {error_msg}\n请确保麦克风正常工作并对着麦克风说话。")
    
    def on_register_complete(self, name):
        self.register_btn.config(state=tk.NORMAL, text="🎤 录入声纹")
        self.status_label.config(text="录入成功！", fg="#27AE60")
        self.update_user_list()
        messagebox.showinfo("成功", f"✓ 用户 '{name}' 声纹录入成功！\n现在可以为该用户设置音频。")
        self.status_label.config(text="准备就绪", fg="#7F8C8D")
    
    def recognize_voice(self):
        if not self.voices:
            messagebox.showwarning("提示", "请先录入声纹！")
            return
        
        self.recognize_btn.config(state=tk.DISABLED, text="识别中...")
        self.result_label.config(text="")
        self.status_label.config(text="请对着麦克风说话...", fg="#E67E22")
        
        def recognizing():
            try:
                audio, sr = self.record_audio(3)
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
                print(f"识别错误: {e}")
                self.root.after(0, lambda: self.on_recognize_error(str(e)))
        
        threading.Thread(target=recognizing, daemon=True).start()
    
    def on_recognize_error(self, error_msg):
        self.recognize_btn.config(state=tk.NORMAL, text="🎤 开始识别 (3秒)")
        self.result_label.config(text="识别失败，请重试", fg="#E74C3C")
        self.status_label.config(text="出错了", fg="#E74C3C")
    
    def on_recognize_complete(self, best_match, best_score):
        self.recognize_btn.config(state=tk.NORMAL, text="🎤 开始识别 (3秒)")
        
        if best_match and best_score >= 0.7:
            audio_info = ""
            if best_match in self.user_audio and os.path.exists(self.user_audio[best_match]):
                audio_info = "\n✓ 已设置音频"
            
            self.result_label.config(
                text=f"识别: {best_match} ({best_score:.2%}){audio_info}",
                fg="#27AE60"
            )
            self.status_label.config(text="识别成功！", fg="#27AE60")
        else:
            self.result_label.config(
                text=f"未识别 (最佳: {best_score:.2%})",
                fg="#E74C3C"
            )
            self.status_label.config(text="未匹配", fg="#E74C3C")
        
        self.root.after(3000, lambda: self.status_label.config(text="准备就绪", fg="#7F8C8D"))
    
    def delete_user(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的用户！")
            return
        
        user_text = self.users_listbox.get(selection[0])
        name = user_text.split(" [")[0]
        
        result = messagebox.askyesno("确认", f"确定删除用户 '{name}' 吗？")
        if result:
            if name in self.voices:
                del self.voices[name]
                self.save_voices()
            if name in self.user_audio:
                del self.user_audio[name]
                self.save_user_audio()
            self.update_user_list()
            messagebox.showinfo("成功", f"✓ 用户 '{name}' 已删除")
    
    def play_selected_audio(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择用户！")
            return
        
        user_text = self.users_listbox.get(selection[0])
        name = user_text.split(" [")[0]
        
        if name in self.user_audio and os.path.exists(self.user_audio[name]):
            if self.play_audio(self.user_audio[name]):
                messagebox.showinfo("播放", f"正在播放 {name} 的音频...")
        else:
            messagebox.showwarning("提示", f"用户 '{name}' 尚未设置音频！")
    
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
        self.listen_btn.config(text="🔴 开始持续监听", bg="#E74C3C")
        self.listen_status.config(text="监听状态: 已停止", fg="#7F8C8D")
        self.listen_result.config(text="")
    
    def listening_loop(self):
        last_recognized = None
        cooldown_until = 0
        
        while self.is_listening:
            try:
                self.root.after(0, lambda: self.listen_status.config(
                    text=f"监听状态: 监听中... (已识别: {last_recognized or '无'})",
                    fg="#27AE60"
                ))
                
                audio, sr = self.record_audio(2)
                features = self.extract_features(audio, sr)
                
                best_match = None
                best_score = 0
                
                for name, voice_features in self.voices.items():
                    voice_array = np.array(voice_features)
                    similarity = 1 - cosine(features, voice_array)
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = name
                
                current_time = time.time()
                
                if best_match and best_score >= 0.7:
                    if current_time > cooldown_until and best_match != last_recognized:
                        last_recognized = best_match
                        cooldown_until = current_time + 5
                        
                        self.root.after(0, lambda n=best_match, s=best_score: self.listen_result.config(
                            text=f"✓ 识别: {n} ({s:.2%}) - 播放音频",
                            fg="#27AE60"
                        ))
                        
                        if best_match in self.user_audio and os.path.exists(self.user_audio[best_match]):
                            self.root.after(0, lambda p=self.user_audio[best_match]: self.play_audio(p))
                        else:
                            self.root.after(0, lambda: messagebox.showwarning(
                                "提示",
                                f"用户 '{best_match}' 未设置音频文件！"
                            ))
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"监听错误: {e}")
                time.sleep(1)
        
        self.root.after(0, lambda: self.listen_status.config(text="监听状态: 已停止", fg="#7F8C8D"))


def main():
    root = tk.Tk()
    
    try:
        root.iconbitmap(default="icon.ico")
    except:
        pass
    
    app = VoiceprintGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
