#!/usr/bin/env python3
"""
VibeVoice 性能測試腳本
測試 VibeVoice 的短/長文本性能，並輸出音檔
"""

import asyncio
import time
import sys
import os
from datetime import datetime

# 添加路徑
sys.path.append('/app')
sys.path.append('/app/app')

from tts_vibe import TTSVibeService

async def test_vibe_performance():
    """測試 VibeVoice 性能並輸出音檔"""
    
    print("=== VibeVoice 性能測試 ===")
    
    # 創建輸出目錄
    output_dir = "/app/outputs/vibe_test"
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化 VibeVoice
    print("\n🎤 初始化 VibeVoice...")
    vibe_service = TTSVibeService()
    
    await vibe_service.initialize()
    
    if not vibe_service.is_ready():
        print("❌ VibeVoice 初始化失敗")
        return
    
    print("✅ VibeVoice 初始化完成")
    
    # 測試文本（與 BreezyVoice 測試相同）
    test_cases = [
        {
            'name': 'short',
            'text': '你好，歡迎使用語音合成系統！今天天氣真不錯。',
            'description': '短文本測試'
        },
        {
            'name': 'medium', 
            'text': '這是一個中等長度的測試文本。我們將測試語音合成的品質和速度。VibeVoice 是一個高品質的語音合成系統，能夠產生自然流暢的語音輸出。讓我們來聽聽效果如何吧！',
            'description': '中等長度文本測試'
        },
        {
            'name': 'long',
            'text': '這是一個較長的測試文本，用於評估語音合成系統在處理長文本時的性能表現。VibeVoice 是一個先進的語音合成技術，具有優秀的語音品質和不錯的合成速度。在實際應用中，我們經常需要合成各種長度的文本內容，包括短句、段落和完整的文章。通過這次測試，我們可以了解系統在不同文本長度下的表現，包括合成速度、音檔品質和系統穩定性。希望這個測試能幫助我們更好地了解 VibeVoice 的能力和特點。',
            'description': '長文本測試'
        }
    ]
    
    results = []
    
    # 執行測試
    for i, test_case in enumerate(test_cases, 1):
        name = test_case['name']
        text = test_case['text']
        description = test_case['description']
        
        print(f"\n{'='*60}")
        print(f"📝 測試 {i}/{len(test_cases)}: {description}")
        print(f"文本長度: {len(text)} 字")
        print(f"文本預覽: {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"{'='*60}")
        
        try:
            # 開始計時
            start_time = time.time()
            
            # 執行合成（使用 VibeVoice 的參數）
            print("🎤 開始語音合成...")
            audio_bytes = await vibe_service.synthesize(text, cfg_scale=1.0)
            
            # 結束計時
            end_time = time.time()
            duration = end_time - start_time
            
            # 計算性能指標
            text_length = len(text)
            audio_size = len(audio_bytes)
            chars_per_second = text_length / duration if duration > 0 else 0
            
            # 保存音檔
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vibe_{name}_{timestamp}.wav"
            output_path = os.path.join(output_dir, filename)
            
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            
            # 記錄結果
            result = {
                'name': name,
                'description': description,
                'text_length': text_length,
                'duration': duration,
                'audio_size': audio_size,
                'chars_per_second': chars_per_second,
                'filename': filename,
                'output_path': output_path,
                'success': True
            }
            results.append(result)
            
            # 輸出結果
            print(f"✅ {description} 合成成功!")
            print(f"   📏 文本長度: {text_length} 字")
            print(f"   ⏱️  合成時間: {duration:.2f} 秒")
            print(f"   🎵 音檔大小: {audio_size:,} bytes")
            print(f"   🚀 處理速度: {chars_per_second:.2f} 字/秒")
            print(f"   💾 音檔路徑: {output_path}")
            
        except Exception as e:
            print(f"❌ {description} 合成失敗: {e}")
            import traceback
            traceback.print_exc()
            result = {
                'name': name,
                'description': description,
                'error': str(e),
                'success': False
            }
            results.append(result)
        
        # 短暫休息
        if i < len(test_cases):
            print("⏳ 休息 3 秒...")
            await asyncio.sleep(3)
    
    # 生成總結報告
    print(f"\n{'='*80}")
    print("📊 VibeVoice 性能測試報告")
    print(f"{'='*80}")
    
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        print(f"\n✅ 成功測試: {len(successful_results)}/{len(test_cases)}")
        print(f"\n{'測試類型':<15} | {'文本長度':<10} | {'合成時間':<10} | {'處理速度':<12}")
        print("-" * 60)
        
        for result in successful_results:
            name = result['name']
            text_length = result['text_length']
            duration = result['duration']
            chars_per_sec = result['chars_per_second']
            
            print(f"{name:<15} | {text_length:<10} | {duration:<10.2f} | {chars_per_sec:<12.2f}")
        
        print(f"\n🎵 生成的音檔:")
        print("-" * 40)
        for result in successful_results:
            filename = result['filename']
            description = result['description']
            print(f"  {filename} - {description}")
        
        print(f"\n📁 所有音檔保存在: {output_dir}")
        print("🎧 請播放音檔聽取效果！")
        
        # 性能分析
        if len(successful_results) >= 2:
            short_result = next((r for r in successful_results if r['name'] == 'short'), None)
            long_result = next((r for r in successful_results if r['name'] == 'long'), None)
            
            if short_result and long_result:
                short_speed = short_result['chars_per_second']
                long_speed = long_result['chars_per_second']
                
                print(f"\n📈 性能分析:")
                print(f"   短文本處理速度: {short_speed:.2f} 字/秒")
                print(f"   長文本處理速度: {long_speed:.2f} 字/秒")
                
                if short_speed > long_speed:
                    ratio = short_speed / long_speed
                    print(f"   短文本比長文本快 {ratio:.2f} 倍")
                else:
                    ratio = long_speed / short_speed
                    print(f"   長文本比短文本快 {ratio:.2f} 倍")
    else:
        print("❌ 所有測試都失敗了")
    
    print(f"\n🎉 測試完成！")

if __name__ == "__main__":
    asyncio.run(test_vibe_performance())
