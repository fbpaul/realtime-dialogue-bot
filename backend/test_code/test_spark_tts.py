#!/usr/bin/env python3
"""
Spark-TTS 服務測試腳本
"""
import asyncio
import sys
import os

# 添加路徑
sys.path.append('/app/backend')

async def test_spark_tts():
    """測試 Spark-TTS 服務"""
    try:
        from app.tts_spark import TTSSparkService
        
        print("=== Spark-TTS 服務測試 ===")
        
        # 初始化服務
        tts_service = TTSSparkService()
        print(f"服務初始化完成，模型路徑: {tts_service.model_dir}")
        
        # 初始化模型
        success = await tts_service.initialize()
        if not success:
            print("❌ Spark-TTS 初始化失敗")
            return
        
        print("✅ Spark-TTS 初始化成功")
        print(f"服務狀態: {tts_service.is_ready()}")
        
        # 檢查語者
        speakers = tts_service.get_speakers()
        print(f"可用語者數量: {len(speakers)}")
        for speaker in speakers:
            print(f"  - {speaker['id']}: {speaker['name']} ({speaker['path']})")
        
        # 測試語音合成
        test_text = "你好，我是台北富邦銀行電銷專員，很高興為您服務！"
        
        # 使用預設語者
        test_voice = "./voices/zh-Novem_man.wav"
        
        if os.path.exists(test_voice):
            print(f"\n開始語音合成測試...")
            print(f"文字: {test_text}")
            print(f"語者音檔: {test_voice}")
            
            # 測試 synthesize 方法（返回 bytes）
            audio_bytes = await tts_service.synthesize_with_speaker_file(
                test_text, 
                test_voice,
                prompt_text="欸這個很有趣耶，趕快跟我說一下吧"
            )
            
            if isinstance(audio_bytes, bytes) and len(audio_bytes) > 0:
                file_size = len(audio_bytes) / 1024  # KB
                print(f"✅ 語音合成成功!")
                print(f"音頻大小: {file_size:.1f} KB")
            else:
                print("❌ 語音合成失敗，未產生音頻數據")
                
            # 測試 synthesize_to_file 方法（返回檔案路徑）
            print(f"\n測試檔案輸出...")
            output_path = await tts_service.synthesize_to_file(
                "這是另一個測試，用來驗證檔案輸出功能。",
                speaker_voice_path=test_voice,
                gender="male",
                pitch="moderate",
                speed="moderate"
            )
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / 1024
                print(f"✅ 檔案輸出成功!")
                print(f"輸出檔案: {output_path}")
                print(f"檔案大小: {file_size:.1f} KB")
            else:
                print("❌ 檔案輸出失敗")
        else:
            print(f"⚠️  測試語者檔案不存在: {test_voice}")
            print("請確保語者檔案存在")
        
        # 清理資源
        tts_service.cleanup()
        print("\n✅ Spark-TTS 測試完成")
        
    except Exception as e:
        print(f"❌ Spark-TTS 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_spark_tts())
