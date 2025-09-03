#!/usr/bin/env python3
"""
IndexTTS 語者克隆功能測試腳本
"""
import asyncio
import os
import sys
import time

# 添加 app 目錄到路徑
sys.path.append('./app')

from app.tts_index import TTSIndexService

async def test_index_voice_cloning():
    """測試 IndexTTS 語者克隆功能"""
    
    print("=" * 60)
    print("IndexTTS 語者克隆功能測試")
    print("=" * 60)
    
    # 初始化 IndexTTS 服務
    tts_service = TTSIndexService()
    
    # 測試初始化
    print("\n1. 測試 IndexTTS 初始化...")
    success = await tts_service.initialize()
    if not success:
        print("❌ IndexTTS 初始化失敗")
        return
    
    print("✅ IndexTTS 初始化成功")
    
    # 檢查可用語者
    print("\n2. 檢查可用語者...")
    speakers = tts_service.get_speakers()
    print(f"找到 {len(speakers)} 個語者:")
    for speaker in speakers[:5]:  # 只顯示前5個
        print(f"  - {speaker['id']}: {speaker['name']}")
    
    if not speakers:
        print("❌ 沒有找到可用的語者")
        return
    
    # 測試文字
    test_texts = [
        "這是一段測試語音，用來驗證 IndexTTS 的語者克隆效果。",
        "你好，我是使用 IndexTTS 生成的語音，聲音應該和參考語者相似。",
        "語者克隆技術可以讓合成語音保持原始語者的聲音特徵。"
    ]
    
    # 使用不同語者進行測試
    test_speakers = speakers[:3] if len(speakers) >= 3 else speakers
    
    for i, speaker in enumerate(test_speakers):
        speaker_id = speaker['id']
        speaker_name = speaker['name']
        
        print(f"\n3.{i+1} 測試語者: {speaker_name} (ID: {speaker_id})")
        print(f"語者音檔: {speaker['path']}")
        
        # 檢查語者音檔是否存在
        if not os.path.exists(speaker['path']):
            print(f"❌ 語者音檔不存在: {speaker['path']}")
            continue
        
        # 選擇測試文字
        test_text = test_texts[i % len(test_texts)]
        print(f"測試文字: {test_text}")
        
        try:
            # 開始語音合成
            start_time = time.time()
            print("開始語音合成...")
            
            # 使用 synthesize_to_file 方法直接生成檔案
            output_path = await tts_service.synthesize_to_file(
                text=test_text,
                speaker_id=speaker_id
            )
            
            synthesis_time = time.time() - start_time
            
            # 檢查結果
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ 語音合成成功!")
                print(f"   耗時: {synthesis_time:.2f} 秒")
                print(f"   檔案: {output_path}")
                print(f"   大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                # 可以播放測試（如果有播放器）
                # print(f"   播放指令: play {output_path}")
                
            else:
                print(f"❌ 語音合成失敗，未產生檔案")
                
        except Exception as e:
            print(f"❌ 語音合成過程中發生錯誤: {e}")
    
    # 測試使用自定義語者檔案
    print(f"\n4. 測試使用自定義語者檔案...")
    custom_speaker_path = "./voices/zh-Novem_man.wav"
    
    if os.path.exists(custom_speaker_path):
        test_text = "這是使用自定義語者檔案的測試語音。"
        print(f"自定義語者: {custom_speaker_path}")
        print(f"測試文字: {test_text}")
        
        try:
            start_time = time.time()
            
            output_path = await tts_service.synthesize_to_file(
                text=test_text,
                speaker_voice_path=custom_speaker_path
            )
            
            synthesis_time = time.time() - start_time
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ 自定義語者合成成功!")
                print(f"   耗時: {synthesis_time:.2f} 秒")
                print(f"   檔案: {output_path}")
                print(f"   大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            else:
                print(f"❌ 自定義語者合成失敗")
                
        except Exception as e:
            print(f"❌ 自定義語者合成錯誤: {e}")
    else:
        print(f"❌ 自定義語者檔案不存在: {custom_speaker_path}")
    
    # 清理資源
    tts_service.cleanup()
    
    print("\n" + "=" * 60)
    print("IndexTTS 語者克隆測試完成!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_index_voice_cloning())
