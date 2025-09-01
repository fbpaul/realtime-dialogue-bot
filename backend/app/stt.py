from faster_whisper import WhisperModel
import tempfile
import os
import io
import numpy as np
import soundfile as sf
from typing import Optional, Union
from opencc import OpenCC

class STTService:
    def __init__(self):
        self.model = None
        self.model_name = "large-v3-turbo"  # Faster-Whisper Large V3 turbo
        self.model_path = "./models"
        self.converter = OpenCC('s2twp')
    async def initialize(self):
        """初始化 Faster-Whisper 模型"""
        try:
            print(f"正在載入 Faster-Whisper {self.model_name} 模型...")
            # 使用 faster-whisper，支援 GPU 加速
            self.model = WhisperModel(
                self.model_name,
                download_root =self.model_path,
                device="auto",  # 自動選擇 CPU 或 CUDA
                compute_type="auto"  # 自動選擇精度
            )
            print("Faster-Whisper 模型載入完成!")
        except Exception as e:
            print(f"Faster-Whisper {self.model_name} 模型載入失敗: {e}")
            # 如果 large-v3 載入失敗，嘗試載入 base 模型
            try:
                print("嘗試載入 base 模型...")
                self.model = WhisperModel(
                    "base",
                    download_root =self.model_path,
                    device="auto",
                    compute_type="auto"
                )
                self.model_name = "base"
                print("Faster-Whisper base 模型載入完成!")
            except Exception as e2:
                print(f"所有模型載入都失敗: {e2}")
                raise e2
    
    def is_ready(self) -> bool:
        """檢查模型是否準備就緒"""
        return self.model is not None
    
    async def transcribe(self, audio_data: Union[bytes, np.ndarray], sample_rate: int = 16000) -> str:
        """將音檔轉換成文字"""
        if not self.is_ready():
            raise Exception("STT 模型尚未初始化")
        
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file_path = tmp_file.name
            
            # 根據輸入類型處理音頻數據
            if isinstance(audio_data, np.ndarray):
                # 如果是 numpy 陣列，使用 soundfile 寫入 WAV 文件
                sf.write(tmp_file_path, audio_data, sample_rate)
            elif isinstance(audio_data, bytes):
                # 如果是 bytes，直接寫入文件
                with open(tmp_file_path, 'wb') as f:
                    f.write(audio_data)
            else:
                raise ValueError(f"不支持的音頻數據類型: {type(audio_data)}")
            
            # 使用 Faster-Whisper 進行語音辨識
            segments, info = self.model.transcribe(
                tmp_file_path,
                language="zh",  # 指定中文
                task="transcribe",
                beam_size=5,  # 提升準確度
                best_of=5
            )
            
            # 清理暫存檔
            os.unlink(tmp_file_path)
            
            # 合併所有 segments 的文字
            text = "".join([segment.text for segment in segments]).strip()
            text = self.converter.convert(text)  # 繁體中文轉換
            # print(f"STT 辨識結果: {text}")
            
            return text
        
        except Exception as e:
            print(f"STT 轉換錯誤: {e}")
            # 嘗試清理暫存檔
            try:
                if 'tmp_file_path' in locals():
                    os.unlink(tmp_file_path)
            except:
                pass
            
            raise Exception(f"語音辨識失敗: {str(e)}")
    
    async def transcribe_file(self, file_path: str) -> str:
        """直接從檔案路徑進行語音辨識"""
        if not self.is_ready():
            raise Exception("STT 模型尚未初始化")
        
        try:
            segments, info = self.model.transcribe(
                file_path,
                language="zh",
                task="transcribe",
                beam_size=5,
                best_of=5
            )
            
            # 合併所有 segments 的文字
            text = "".join([segment.text for segment in segments]).strip()
            text = self.converter.convert(text)  # 繁體中文轉換
            # print(f"STT 辨識結果: {text}")
            
            return text
        
        except Exception as e:
            print(f"STT 轉換錯誤: {e}")
            raise Exception(f"語音辨識失敗: {str(e)}")

# 測試腳本
if __name__ == "__main__":
    import asyncio
    
    async def test_stt():
        stt_service = STTService()
        await stt_service.initialize()
        
        if not stt_service.is_ready():
            print("STT 系統未準備好，無法進行測試")
            return
        
        # 測試使用範例音檔
        test_audio_path = "./test_files/shorts.wav"  # 請確保有一個測試音檔在此路徑
        if not os.path.exists(test_audio_path):
            print(f"找不到測試音檔: {test_audio_path}")
            return
        
        with open(test_audio_path, "rb") as f:
            audio_bytes = f.read()
        
        text = await stt_service.transcribe(audio_bytes)
        print(f"辨識結果: {text}")
    
    asyncio.run(test_stt())    