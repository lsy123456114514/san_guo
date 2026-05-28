# -*- coding: utf-8 -*-
"""
声纹识别系统 - 说话人识别
用于识别不同的说话人，不管说什么内容都能识别
"""

import numpy as np
import librosa
import sounddevice as sd
from scipy.spatial.distance import cosine
import json
import os
from pathlib import Path


class VoiceprintRecognizer:
    def __init__(self, data_dir="voice_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.voices_file = self.data_dir / "voices.json"
        self.voices = self.load_voices()
    
    def load_voices(self):
        if self.voices_file.exists():
            with open(self.voices_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_voices(self):
        with open(self.voices_file, 'w', encoding='utf-8') as f:
            json.dump(self.voices, f, ensure_ascii=False, indent=2)
    
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
        print(f"请说话，录音时长 {duration} 秒...")
        print("录音中...")
        
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        
        audio = audio.flatten()
        return audio, samplerate
    
    def register_voice(self, name, duration=3):
        print(f"\n正在为 '{name}' 录入声纹...")
        print("请对着麦克风说话...")
        
        audio, sr = self.record_audio(duration)
        features = self.extract_features(audio, sr)
        
        self.voices[name] = features.tolist()
        self.save_voices()
        
        print(f"✓ '{name}' 声纹录入成功！")
        return True
    
    def recognize(self, duration=3, threshold=0.7):
        print("\n正在识别说话人...")
        audio, sr = self.record_audio(duration)
        features = self.extract_features(audio, sr)
        
        best_match = None
        best_score = 0
        
        for name, voice_features in self.voices.items():
            voice_array = np.array(voice_features)
            
            similarity = 1 - cosine(features, voice_array)
            
            if similarity > best_score:
                best_score = similarity
                best_match = name
        
        if best_match and best_score >= threshold:
            print(f"识别结果: {best_match} (相似度: {best_score:.2%})")
            return best_match, best_score
        else:
            print(f"未识别到匹配的声纹 (最佳相似度: {best_score:.2%})")
            return None, best_score
    
    def list_registered(self):
        if not self.voices:
            print("暂无注册的声纹")
            return []
        print("\n已注册的声纹:")
        for i, name in enumerate(self.voices.keys(), 1):
            print(f"  {i}. {name}")
        return list(self.voices.keys())
    
    def delete_voice(self, name):
        if name in self.voices:
            del self.voices[name]
            self.save_voices()
            print(f"已删除 '{name}' 的声纹")
            return True
        print(f"未找到 '{name}' 的声纹")
        return False


def main():
    recognizer = VoiceprintRecognizer()
    
    print("=" * 50)
    print("声纹识别系统")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 录入新声纹")
        print("2. 识别说话人")
        print("3. 查看已注册声纹")
        print("4. 删除声纹")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == '1':
            name = input("请输入姓名: ").strip()
            if name:
                recognizer.register_voice(name)
        
        elif choice == '2':
            if not recognizer.voices:
                print("请先录入声纹！")
            else:
                recognizer.recognize()
        
        elif choice == '3':
            recognizer.list_registered()
        
        elif choice == '4':
            names = recognizer.list_registered()
            if names:
                name = input("请输入要删除的姓名: ").strip()
                if name:
                    recognizer.delete_voice(name)
        
        elif choice == '5':
            print("谢谢使用！")
            break
        
        else:
            print("无效的选项，请重新输入")


if __name__ == "__main__":
    main()
