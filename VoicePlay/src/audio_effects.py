# -*- coding: utf-8 -*-
"""
音频特效模块
提供变声和音效功能（简化版）
"""

import numpy as np
import sounddevice as sd
import wave
import os


class AudioEffects:
    """音频特效处理器 - 简化版"""
    
    def __init__(self):
        self.sample_rate = 44100
        self.current_effect = None
    
    def apply_effect(self, audio, effect_name):
        """应用特效"""
        if effect_name == 'none' or effect_name is None:
            return audio
        
        try:
            if effect_name == 'loli':  # 萝莉音（简单提升音高）
                return self._apply_pitch_shift(audio, 3)
            elif effect_name == 'uncle':  # 大叔音（降低音高）
                return self._apply_pitch_shift(audio, -3)
            elif effect_name == 'robot':  # 机器人音
                return self._apply_robot_effect(audio)
            elif effect_name == 'echo':  # 回声
                return self._apply_echo(audio)
            elif effect_name == 'megaphone':  # 扩音器
                return np.clip(audio * 1.5, -1.0, 1.0)
            else:
                return audio
        except:
            return audio
    
    def _apply_pitch_shift(self, audio, semitones):
        """简单的音调调整"""
        # 简单重采样来模拟音高变化
        rate = 2.0 ** (semitones / 12.0)
        new_length = int(len(audio) / rate)
        indices = np.linspace(0, len(audio) - 1, new_length)
        shifted = np.interp(indices, np.arange(len(audio)), audio)
        # 调整回原长度
        result = np.zeros_like(audio)
        result[:min(len(shifted), len(audio))] = shifted[:min(len(shifted), len(audio))]
        return result
    
    def _apply_robot_effect(self, audio):
        """机器人效果"""
        # 采样和保持效果
        step = 100
        result = np.zeros_like(audio)
        for i in range(0, len(audio), step):
            if i + step <= len(audio):
                result[i:i+step] = audio[i]
        return result
    
    def _apply_echo(self, audio):
        """回声效果"""
        delay = int(0.3 * self.sample_rate)
        echo = np.zeros_like(audio)
        echo[:len(audio)] = audio
        if delay < len(audio):
            echo[delay:] += 0.5 * audio[:-delay]
        return echo
    
    def record_and_play(self, duration=3, effect='none'):
        """录音并播放"""
        print(f"正在录音 {duration} 秒...")
        
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        audio = audio.flatten()
        
        if effect != 'none':
            audio = self.apply_effect(audio, effect)
        
        print("正在播放...")
        sd.play(audio, self.sample_rate)
        sd.wait()
        
        return audio
    
    def save_recording(self, audio, filepath):
        """保存录音到文件"""
        # 转换为16位PCM
        audio_int = (audio * 32767).astype(np.int16)
        
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int.tobytes())
