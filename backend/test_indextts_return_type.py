#!/usr/bin/env python3
"""
測試 IndexTTS 服務返回類型修復
"""
import asyncio
import sys
import os

# 添加路徑
sys.path.append('/data/paul.fc.tsai_data/realtime-dialogue-bot/backend')

async def test_indextts_return_type():
    """測試 IndexTTS 返回類型"""
    try:
        from app.tts_index import TTSIndexService
        
        print("=== IndexTTS 返回類型測試 ===")
        
        # 初始化服務
        tts_service = TTSIndexService()
        success = await tts_service.initialize()
        
        if not success:
            print("❌ IndexTTS 初始化失敗")
            return
        
        print("✅ IndexTTS 初始化成功")
        
        # 測試語音合成
        test_text = "這是一個測試文字，用來檢查返回類型。"
        test_voice = "./voices/zh-IndexTTS_man.wav"
        
        if not os.path.exists(test_voice):
            print(f"⚠️  測試語者檔案不存在: {test_voice}")
            print("使用第一個可用的語者...")
            test_voice = None
        
        # 測試 synthesize 方法（應該返回 bytes）
        print(f"\n🔹 測試 synthesize 方法（返回 bytes）...")
        audio_bytes = await tts_service.synthesize(test_text, speaker_voice_path=test_voice)
        
        print(f"返回類型: {type(audio_bytes)}")
        if isinstance(audio_bytes, bytes):
            print(f"✅ 正確返回 bytes，大小: {len(audio_bytes)} bytes")
        else:
            print(f"❌ 錯誤！返回類型不是 bytes: {type(audio_bytes)}")
        
        # 測試 synthesize_to_file 方法（應該返回 str）
        print(f"\n🔹 測試 synthesize_to_file 方法（返回 str）...")
        file_path = await tts_service.synthesize_to_file(test_text, speaker_voice_path=test_voice)
        
        print(f"返回類型: {type(file_path)}")
        if isinstance(file_path, str):
            print(f"✅ 正確返回 str 路徑: {file_path}")
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / 1024
                print(f"檔案存在，大小: {file_size:.1f} KB")
            else:
                print(f"❌ 檔案不存在: {file_path}")
        else:
            print(f"❌ 錯誤！返回類型不是 str: {type(file_path)}")
        
        # 清理資源
        tts_service.cleanup()
        print("\n✅ IndexTTS 返回類型測試完成")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_indextts_return_type())
