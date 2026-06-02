# -*- coding: utf-8 -*-
"""
麦克风测试脚本
"""

import speech_recognition as sr

def test_microphone():
    """测试麦克风"""
    recognizer = sr.Recognizer()
    
    print("=" * 50)
    print("   麦克风测试")
    print("=" * 50)
    print()
    
    # 列出所有可用的麦克风
    print("可用麦克风设备:")
    for i, microphone in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  [{i}] {microphone}")
    print()
    
    # 测试默认麦克风
    print("测试默认麦克风...")
    try:
        with sr.Microphone() as source:
            print("🎤 麦克风已打开！请说话...")
            print("   （麦克风蓝灯应该亮了）")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("   环境噪音校准完成")
            
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("   录音完成")
        
        # 尝试识别
        try:
            text = recognizer.recognize_google(audio, language='zh-CN')
            print(f"\n✅ 识别成功: {text}")
        except sr.UnknownValueError:
            print("\n⚠️ 无法识别语音内容")
        except sr.RequestError as e:
            print(f"\n❌ 语音服务错误: {e}")
        
        print("\n✅ 麦克风测试完成！")
        
    except Exception as e:
        print(f"\n❌ 麦克风测试失败: {e}")
        print("   可能需要检查麦克风权限或选择正确的设备")

if __name__ == "__main__":
    test_microphone()
