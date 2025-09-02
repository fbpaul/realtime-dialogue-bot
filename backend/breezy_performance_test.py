#!/usr/bin/env python3
"""
TTS 性能比較測試腳本 - 簡化版
僅測試 BreezyVoice，因為 VibeVoice 初始化較複雜
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

async def test_breezy_vs_breezy_optimized():
    """測試 BreezyVoice 在不同設置下的性能"""
    
    print("=== BreezyVoice 性能比較測試 ===")
    
    # 創建輸出目錄
    output_dir = "/app/outputs/comparison"
    os.makedirs(output_dir, exist_ok=True)
    
    # 測試文本
    test_texts = {
        'short': '你好，歡迎使用語音合成系統！今天天氣真不錯。',
        'medium': '這是一個中等長度的測試文本。我們將測試語音合成的品質和速度。BreezyVoice 是一個高品質的語音合成系統，能夠產生自然流暢的語音輸出。讓我們來聽聽效果如何吧！',
        'long': '這是一個較長的測試文本，用於評估語音合成系統在處理長文本時的性能表現。BreezyVoice 是基於 CosyVoice 技術的語音合成系統，具有優秀的語音品質和相當不錯的合成速度。在實際應用中，我們經常需要合成各種長度的文本內容，包括短句、段落和完整的文章。通過這次測試，我們可以了解系統在不同文本長度下的表現，包括合成速度、音檔品質和系統穩定性。希望這個測試能幫助我們更好地了解優化後的 BreezyVoice 的能力和特點。'
    }
    
    results = []
    
    # 測試配置
    configs = [
        {
            'name': 'optimized',
            'description': '優化版本（緩存+預熱+並行）',
            'parallel': True,
            'max_concurrent': 3
        },
        {
            'name': 'standard',
            'description': '標準版本（僅緩存）',
            'parallel': False,
            'max_concurrent': 1
        }
    ]
    
    for config in configs:
        config_name = config['name']
        config_desc = config['description']
        
        print(f"\n{'='*80}")
        print(f"🔧 測試配置: {config_desc}")
        print(f"{'='*80}")
        
        # 初始化服務
        breezy_service = TTSBreezyService()
        breezy_service.configure_optimization(
            use_mixed_precision=True,
            parallel_synthesis=config['parallel'],
            max_concurrent_segments=config['max_concurrent']
        )
        
        await breezy_service.initialize()
        
        if not breezy_service.is_ready():
            print(f"❌ {config_desc} 初始化失敗")
            continue
        
        print(f"✅ {config_desc} 初始化完成")
        
        # 測試每種文本類型
        for text_type, text in test_texts.items():
            print(f"\n� 測試 {text_type} 文本 ({len(text)} 字)")
            
            try:
                start_time = time.time()
                audio_bytes = await breezy_service.synthesize(text)
                end_time = time.time()
                
                duration = end_time - start_time
                text_length = len(text)
                chars_per_second = text_length / duration
                
                # 保存音檔
                timestamp = datetime.now().strftime("%H%M%S")
                filename = f"breezy_{config_name}_{text_type}_{timestamp}.wav"
                output_path = os.path.join(output_dir, filename)
                
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                
                result = {
                    'config': config_name,
                    'config_desc': config_desc,
                    'text_type': text_type,
                    'text_length': text_length,
                    'duration': duration,
                    'chars_per_second': chars_per_second,
                    'filename': filename,
                    'success': True
                }
                results.append(result)
                
                print(f"✅ 合成成功: {duration:.2f}s, {chars_per_second:.2f} 字/秒")
                print(f"   音檔: {filename}")
                
            except Exception as e:
                print(f"❌ 合成失敗: {e}")
                results.append({
                    'config': config_name,
                    'text_type': text_type,
                    'error': str(e),
                    'success': False
                })
        
        await asyncio.sleep(2)  # 短暫休息
    
    # 生成比較報告
    print(f"\n{'='*80}")
    print("� BreezyVoice 配置比較報告")
    print(f"{'='*80}")
    
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        # 按文本類型分組比較
        for text_type in ['short', 'medium', 'long']:
            text_results = [r for r in successful_results if r['text_type'] == text_type]
            
            if len(text_results) >= 2:
                print(f"\n📈 {text_type.upper()} 文本比較:")
                print("-" * 60)
                
                for result in text_results:
                    config_desc = result['config_desc']
                    duration = result['duration']
                    speed = result['chars_per_second']
                    print(f"{config_desc:<30} | {duration:8.2f}s | {speed:8.2f} 字/秒")
                
                # 比較性能
                optimized = next((r for r in text_results if r['config'] == 'optimized'), None)
                standard = next((r for r in text_results if r['config'] == 'standard'), None)
                
                if optimized and standard:
                    if optimized['chars_per_second'] > standard['chars_per_second']:
                        ratio = optimized['chars_per_second'] / standard['chars_per_second']
                        print(f"🚀 優化版本比標準版本快 {ratio:.2f} 倍")
                    else:
                        ratio = standard['chars_per_second'] / optimized['chars_per_second']
                        print(f"⚠️ 標準版本比優化版本快 {ratio:.2f} 倍")
        
        # 音檔列表
        print(f"\n🎵 生成的音檔:")
        print("-" * 80)
        for result in successful_results:
            config_desc = result['config_desc']
            text_type = result['text_type']
            filename = result['filename']
            print(f"{filename:<35} | {config_desc:<30} | {text_type}")
        
        print(f"\n📁 所有音檔保存在: {output_dir}")
        print("🎧 請聽取音檔比較不同配置下的效果")
    
    print(f"\n🎉 比較測試完成！")

if __name__ == "__main__":
    asyncio.run(test_breezy_vs_breezy_optimized())
