#!/usr/bin/env python3
"""
IndexTTS 服務測試腳本
"""
import asyncio
import sys
import os

# 添加路徑
sys.path.append('/app/backend')

async def test_index_tts():
    """測試 IndexTTS 服務"""
    try:
        from app.tts_index import TTSIndexService
        
        print("=== IndexTTS 服務測試 ===")
        
        # 初始化服務
        tts_service = TTSIndexService()
        print(f"服務初始化完成，模型路徑: {tts_service.model_dir}")
        
        # 初始化模型
        success = await tts_service.initialize()
        if not success:
            print("❌ IndexTTS 初始化失敗")
            return
        
        print("✅ IndexTTS 初始化成功")
        print(f"服務狀態: {tts_service.is_ready()}")
        
        # 檢查語者
        speakers = tts_service.get_speakers()
        print(f"可用語者數量: {len(speakers)}")
        for speaker in speakers:
            print(f"  - {speaker['id']}: {speaker['name']} ({speaker['path']})")
        
        # 測試語音合成
        test_text = "大家好，我現在正在體驗 IndexTTS 語音合成技術，效果非常不錯！"
        
        # 使用 index-tts 目錄中的測試語者
        test_voice = "./voices/zh-IndexTTS_man.wav"
        
        if os.path.exists(test_voice):
            print(f"\n開始語音合成測試...")
            print(f"文字: {test_text}")
            print(f"語者音檔: {test_voice}")
            
            output_path = await tts_service.synthesize_with_speaker_file(test_text, test_voice)
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / 1024  # KB
                print(f"✅ 語音合成成功!")
                print(f"輸出檔案: {output_path}")
                print(f"檔案大小: {file_size:.1f} KB")
            else:
                print("❌ 語音合成失敗，未產生輸出檔案")
        else:
            print(f"⚠️  測試語者檔案不存在: {test_voice}")
            print("請確保 index-tts/tests/sample_prompt.wav 存在")
        
        # 清理資源
        tts_service.cleanup()
        print("\n✅ IndexTTS 測試完成")
        
    except Exception as e:
        print(f"❌ IndexTTS 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_index_tts())
