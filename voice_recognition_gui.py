# -*- coding: utf-8 -*-
"""
声纹识别系统 GUI版本
图形界面版的说话人识别系统
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import librosa
import sounddevice as sd
from scipy.spatial.distance import cosine
import json
import os
from pathlib import Path
import threading
import time


class VoiceprintGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔊 声纹识别系统")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.data_dir = Path("voice_data_gui")
        self.data_dir.mkdir(exist_ok=True)
        self.voices_file = self.data_dir / "voices.json"
        self.voices = self.load_voices()
        
        self.is_recording = False
        self.recording_thread = None
        
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
    
    def setup_ui(self):
        title_label = tk.Label(
            self.root,
            text="🔊 声纹识别系统",
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
            text="📝 录入声纹",
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
            width=25
        )
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.register_btn = tk.Button(
            register_frame,
            text="🎤 开始录入 (3秒)",
            font=("Microsoft YaHei", 10, "bold"),
            bg="#3498DB",
            fg="white",
            activebackground="#2980B9",
            activeforeground="white",
            padx=20,
            pady=8,
            command=self.register_voice
        )
        self.register_btn.grid(row=0, column=2, padx=5, pady=5)
        
        recognize_frame = tk.LabelFrame(
            main_frame,
            text="🎯 识别说话人",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ECF0F1",
            fg="#2C3E50",
            padx=15,
            pady=15
        )
        recognize_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.recognize_btn = tk.Button(
            recognize_frame,
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
            recognize_frame,
            text="准备就绪",
            font=("Microsoft YaHei", 10),
            bg="#ECF0F1",
            fg="#7F8C8D"
        )
        self.status_label.pack(pady=5)
        
        self.result_label = tk.Label(
            recognize_frame,
            text="",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#ECF0F1",
            fg="#E74C3C"
        )
        self.result_label.pack(pady=5)
        
        users_frame = tk.LabelFrame(
            main_frame,
            text="👥 已注册用户",
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
            height=6,
            bg="white",
            selectbackground="#3498DB",
            selectforeground="white"
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.users_listbox.yview)
        
        btn_frame = tk.Frame(main_frame, bg="#ECF0F1")
        btn_frame.pack(fill=tk.X)
        
        self.delete_btn = tk.Button(
            btn_frame,
            text="🗑️ 删除选中用户",
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
        
        self.refresh_btn = tk.Button(
            btn_frame,
            text="🔄 刷新列表",
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
    
    def update_user_list(self):
        self.users_listbox.delete(0, tk.END)
        if not self.voices:
            self.users_listbox.insert(0, "(暂无注册用户)")
        else:
            for i, name in enumerate(self.voices.keys(), 1):
                self.users_listbox.insert(tk.END, f"{i}. {name}")
    
    def extract_features(self, audio, sr):
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        mfccs_mean = np.mean(mfccs.T, axis=0)
        
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
        chroma_mean = np.mean(chroma.T, axis=0)
        
        mel = librosa.feature.melspectrogram(y=audio, sr=sr)
        mel_mean = np.mean(mel.T, axis=0)
        
        features = np.concatenate([mfccs_mean, chroma_mean, mel_mean])
        return features
    
    def record_audio(self, duration=3, samplerate=16000):
        self.is_recording = True
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
        
        start_time = time.time()
        while self.is_recording:
            elapsed = time.time() - start_time
            remaining = max(0, int(duration - elapsed))
            
            if elapsed >= duration:
                break
            
            self.root.after(0, lambda r=remaining: self.status_label.config(
                text=f"录音中... {r}秒",
                fg="#E74C3C"
            ))
            time.sleep(0.05)
        
        self.root.after(0, lambda: self.status_label.config(text="录音完成", fg="#27AE60"))
        audio = audio.flatten()
        return audio, samplerate
    
    def register_voice(self):
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning("提示", "请输入姓名！")
            return
        
        if name in self.voices:
            result = messagebox.askyesno("确认", f"用户 '{name}' 已存在，是否覆盖？")
            if not result:
                return
        
        self.register_btn.config(state=tk.DISABLED, text="录音中...")
        self.status_label.config(text="请对着麦克风说话...", fg="#E67E22")
        
        def recording():
            audio, sr = self.record_audio(3)
            features = self.extract_features(audio, sr)
            
            self.voices[name] = features.tolist()
            self.save_voices()
            
            self.root.after(0, self.on_register_complete, name)
        
        threading.Thread(target=recording, daemon=True).start()
    
    def on_register_complete(self, name):
        self.register_btn.config(state=tk.NORMAL, text="🎤 开始录入 (3秒)")
        self.status_label.config(text="录入成功！", fg="#27AE60")
        self.name_entry.delete(0, tk.END)
        self.update_user_list()
        messagebox.showinfo("成功", f"✓ 用户 '{name}' 声纹录入成功！")
        self.status_label.config(text="准备就绪", fg="#7F8C8D")
    
    def recognize_voice(self):
        if not self.voices:
            messagebox.showwarning("提示", "请先录入声纹！")
            return
        
        self.recognize_btn.config(state=tk.DISABLED, text="识别中...")
        self.result_label.config(text="")
        self.status_label.config(text="请对着麦克风说话...", fg="#E67E22")
        
        def recognizing():
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
        
        threading.Thread(target=recognizing, daemon=True).start()
    
    def on_recognize_complete(self, best_match, best_score):
        self.recognize_btn.config(state=tk.NORMAL, text="🎤 开始识别 (3秒)")
        
        if best_match and best_score >= 0.7:
            self.result_label.config(
                text=f"识别结果: {best_match}\n相似度: {best_score:.2%}",
                fg="#27AE60"
            )
            self.status_label.config(text="识别成功！", fg="#27AE60")
        else:
            self.result_label.config(
                text=f"未识别到匹配的声纹\n最佳相似度: {best_score:.2%}",
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
        name = user_text.split(". ", 1)[1] if ". " in user_text else user_text
        
        result = messagebox.askyesno("确认", f"确定删除用户 '{name}' 的声纹吗？")
        if result:
            if name in self.voices:
                del self.voices[name]
                self.save_voices()
                self.update_user_list()
                messagebox.showinfo("成功", f"✓ 用户 '{name}' 已删除")
            else:
                messagebox.showerror("错误", "用户不存在")


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
