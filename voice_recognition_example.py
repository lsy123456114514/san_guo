# -*- coding: utf-8 -*-
"""
声纹识别使用示例
展示如何在三国游戏中集成声纹识别功能
"""

from voice_recognition import VoiceprintRecognizer


def simple_example():
    print("简单声纹识别示例\n")
    
    recognizer = VoiceprintRecognizer()
    
    print("=" * 50)
    print("步骤1: 录入声纹")
    print("=" * 50)
    
    name = input("请输入要录入的姓名 (直接回车跳过录入): ").strip()
    
    if name:
        recognizer.register_voice(name, duration=3)
    
    print("\n" + "=" * 50)
    print("步骤2: 识别说话人")
    print("=" * 50)
    
    if recognizer.voices:
        print("\n现在尝试识别...")
        result, score = recognizer.recognize(duration=3)
        
        if result:
            print(f"\n成功识别！说话人是: {result}")
            print(f"相似度: {score:.2%}")
        else:
            print("\n未能识别到已录入的声纹")
    else:
        print("\n没有已录入的声纹，无法识别")
    
    print("\n" + "=" * 50)
    print("已注册的声纹列表")
    print("=" * 50)
    recognizer.list_registered()


def game_integration_example():
    print("\n\n游戏集成示例\n")
    print("在三国游戏中，声纹识别可以用于:")
    print("1. 玩家登录验证 - 通过声音识别玩家身份")
    print("2. 多人游戏身份确认 - 确认是哪个玩家在说话")
    print("3. 语音指令识别 - 识别特定玩家的语音命令")
    print()
    
    recognizer = VoiceprintRecognizer()
    
    print("示例场景: 游戏登录")
    print("-" * 30)
    
    print("\n1. 录入玩家声纹")
    player_name = input("请输入游戏ID: ").strip()
    
    if player_name:
        confirm = input(f"是否为玩家 '{player_name}' 录入声纹? (y/n): ").strip().lower()
        
        if confirm == 'y':
            recognizer.register_voice(player_name, duration=3)
            print(f"\n✓ 玩家 {player_name} 声纹录入完成！")
    
    print("\n2. 游戏中身份验证")
    if recognizer.voices:
        print("检测到玩家说话，正在验证身份...")
        result, score = recognizer.recognize(duration=3)
        
        if result:
            print(f"\n✓ 身份验证成功！欢迎回来，{result}！")
        else:
            print("\n✗ 身份验证失败")


if __name__ == "__main__":
    simple_example()
    
    use_in_game = input("\n\n是否查看游戏集成示例? (y/n): ").strip().lower()
    
    if use_in_game == 'y':
        game_integration_example()
