#!/usr/bin/env python3
"""
BreezyVoice vs VibeVoice 性能比較測試
測試兩個 TTS 模型在短文本和長文本下的表現
"""

import asyncio
import time
import sys
import os
from datetime import datetime

# 添加路徑
sys.path.append('/app')
sys.path.append('/app/app')

from tts_breezy import TTSBreezyService
from tts_vibe import TTSVibeService

async def main():
    """主測試函數"""
    
    print("=== BreezyVoice vs VibeVoice 性能比較 ===")
    
    # 創建輸出目錄
    output_dir = "/app/outputs/tts_comparison"
    os.makedirs(output_dir, exist_ok=True)
    
    # 測試文本
    short_text = "你好，歡迎使用語音合成系統！今天天氣真不錯。"
    long_text = "這是一個較長的測試文本，用於評估語音合成系統在處理長文本時的性能表現。BreezyVoice 是基於 CosyVoice 技術的語音合成系統，具有優秀的語音品質和相當不錯的合成速度。VibeVoice 則是另一種先進的語音合成技術，也能產生自然流暢的語音。在實際應用中，我們經常需要合成各種長度的文本內容。通過這次比較測試，我們可以了解兩種技術在速度、品質和穩定性方面的差異，為未來的應用選擇提供參考依據。"
    
    tests = [
        {"name": "short", "text": short_text, "description": "短文本"},
        {"name": "long", "text": long_text, "description": "長文本"}
    ]
    
    results = []
    
    # 測試 BreezyVoice
    print("\n🎵 測試 BreezyVoice...")
    try:
        breezy_service = TTSBreezyService()
        breezy_service.configure_optimization(
            use_mixed_precision=True,
            parallel_synthesis=True,
            max_concurrent_segments=3
        )
        
        await breezy_service.initialize()
        
        if breezy_service.is_ready():
            print("✅ BreezyVoice 初始化成功")
            
            for test in tests:
                test_name = test["name"]
                text = test["text"]
                description = test["description"]
                
                print(f"\n📝 BreezyVoice {description} ({len(text)} 字)")
                
                try:
                    start_time = time.time()
                    audio_bytes = await breezy_service.synthesize(text)
                    duration = time.time() - start_time
                    
                    # 保存音檔
                    timestamp = datetime.now().strftime("%H%M%S")
                    filename = f"breezy_{test_name}_{timestamp}.wav"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(audio_bytes)
                    
                    result = {
                        'model': 'BreezyVoice',
                        'test_type': test_name,
                        'text_length': len(text),
                        'duration': duration,
                        'speed': len(text) / duration,
                        'filename': filename,
                        'success': True
                    }
                    results.append(result)
                    
                    print(f"✅ 合成時間: {duration:.2f}s, 速度: {result['speed']:.2f} 字/秒")
                    print(f"   音檔: {filename}")
                    
                except Exception as e:
                    print(f"❌ BreezyVoice {description} 失敗: {e}")
                    results.append({
                        'model': 'BreezyVoice',
                        'test_type': test_name,
                        'error': str(e),
                        'success': False
                    })
        else:
            print("❌ BreezyVoice 初始化失敗")
    
    except Exception as e:
        print(f"❌ BreezyVoice 服務錯誤: {e}")
    
    # 休息一下
    await asyncio.sleep(3)
    
    # 測試 VibeVoice
    print("\n🎤 測試 VibeVoice...")
    try:
        vibe_service = TTSVibeService()
        await vibe_service.initialize()
        
        if vibe_service.is_ready():
            print("✅ VibeVoice 初始化成功")
            
            for test in tests:
                test_name = test["name"]
                text = test["text"]
                description = test["description"]
                
                print(f"\n📝 VibeVoice {description} ({len(text)} 字)")
                
                try:
                    start_time = time.time()
                    audio_bytes = await vibe_service.synthesize(text, cfg_scale=1.0)
                    duration = time.time() - start_time
                    
                    # 保存音檔
                    timestamp = datetime.now().strftime("%H%M%S")
                    filename = f"vibe_{test_name}_{timestamp}.wav"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(audio_bytes)
                    
                    result = {
                        'model': 'VibeVoice',
                        'test_type': test_name,
                        'text_length': len(text),
                        'duration': duration,
                        'speed': len(text) / duration,
                        'filename': filename,
                        'success': True
                    }
                    results.append(result)
                    
                    print(f"✅ 合成時間: {duration:.2f}s, 速度: {result['speed']:.2f} 字/秒")
                    print(f"   音檔: {filename}")
                    
                except Exception as e:
                    print(f"❌ VibeVoice {description} 失敗: {e}")
                    results.append({
                        'model': 'VibeVoice',
                        'test_type': test_name,
                        'error': str(e),
                        'success': False
                    })
        else:
            print("❌ VibeVoice 初始化失敗")
    
    except Exception as e:
        print(f"❌ VibeVoice 服務錯誤: {e}")
    
    # 生成比較報告
    print(f"\n{'='*80}")
    print("📊 性能比較結果")
    print(f"{'='*80}")
    
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        # 按測試類型分組
        for test_type in ['short', 'long']:
            test_results = [r for r in successful_results if r['test_type'] == test_type]
            
            if test_results:
                test_desc = "短文本" if test_type == "short" else "長文本"
                print(f"\n🏁 {test_desc} 比較:")
                print("-" * 60)
                
                for result in test_results:
                    model = result['model']
                    duration = result['duration']
                    speed = result['speed']
                    filename = result['filename']
                    print(f"{model:<12} | {duration:8.2f}s | {speed:8.2f} 字/秒 | {filename}")
                
                # 比較速度
                breezy_result = next((r for r in test_results if r['model'] == 'BreezyVoice'), None)
                vibe_result = next((r for r in test_results if r['model'] == 'VibeVoice'), None)
                
                if breezy_result and vibe_result:
                    breezy_speed = breezy_result['speed']
                    vibe_speed = vibe_result['speed']
                    
                    if breezy_speed > vibe_speed:
                        ratio = breezy_speed / vibe_speed
                        print(f"🏆 BreezyVoice 比 VibeVoice 快 {ratio:.2f} 倍")
                    else:
                        ratio = vibe_speed / breezy_speed
                        print(f"🏆 VibeVoice 比 BreezyVoice 快 {ratio:.2f} 倍")
        
        print(f"\n🎵 生成的音檔:")
        print("-" * 50)
        for result in successful_results:
            model = result['model']
            test_type = result['test_type']
            filename = result['filename']
            test_desc = "短文本" if test_type == "short" else "長文本"
            print(f"  {filename} - {model} {test_desc}")
        
        print(f"\n📁 音檔位置: {output_dir}")
        print("🎧 請播放音檔比較兩種模型的音質差異")
    
    else:
        print("❌ 沒有成功的測試結果")
    
    print(f"\n🎉 比較測試完成！")

if __name__ == "__main__":
    asyncio.run(main())
