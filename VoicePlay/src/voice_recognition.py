# -*- coding: utf-8 -*-
"""
声纹识别核心模块
提供说话人识别功能
"""

import numpy as np
import librosa
import sounddevice as sd
from scipy.spatial.distance import cosine
import json
import os
from pathlib import Path


class VoiceRecognizer:
    """声纹识别器"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.voices_file = self.data_dir / "voices.json"
        self.user_audio_file = self.data_dir / "user_audio.json"
        self.voices = self.load_voices()
        self.user_audio = self.load_user_audio()
    
    def load_voices(self):
        """加载已保存的声纹数据"""
        if self.voices_file.exists():
            with open(self.voices_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_voices(self):
        """保存声纹数据"""
        with open(self.voices_file, 'w', encoding='utf-8') as f:
            json.dump(self.voices, f, ensure_ascii=False, indent=2)
    
    def load_user_audio(self):
        """加载用户音频映射"""
        if self.user_audio_file.exists():
            with open(self.user_audio_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_user_audio(self):
        """保存用户音频映射"""
        with open(self.user_audio_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_audio, f, ensure_ascii=False, indent=2)
    
    def extract_features(self, audio, sr):
        """从音频中提取特征"""
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
        """录制音频"""
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
            import time
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(0.1)
        
        if audio_buffer:
            audio = np.concatenate(audio_buffer)
            audio = audio.flatten()
        else:
            audio = np.zeros(int(duration * samplerate), dtype='float32')
        
        return audio, samplerate
    
    def register_voice(self, name):
        """录入新声纹"""
        audio, sr = self.record_audio(3)
        features = self.extract_features(audio, sr)
        self.voices[name] = features.tolist()
        self.save_voices()
        return True
    
    def recognize(self, threshold=0.75):
        """识别说话人"""
        audio, sr = self.record_audio(2)
        
        audio_energy = np.sqrt(np.mean(audio**2))
        if audio_energy < 0.02:
            return None, 0
        
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
            return best_match, best_score
        return None, best_score
    
    def delete_voice(self, name):
        """删除声纹"""
        if name in self.voices:
            del self.voices[name]
            self.save_voices()
        if name in self.user_audio:
            del self.user_audio[name]
            self.save_user_audio()
    
    def set_user_audio(self, name, audio_path):
        """设置用户触发音频"""
        self.user_audio[name] = audio_path
        self.save_user_audio()
    
    def get_user_audio(self, name):
        """获取用户触发音频"""
        return self.user_audio.get(name, None)
    
    def list_users(self):
        """获取所有用户列表"""
        return list(self.voices.keys())
