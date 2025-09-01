import os
import subprocess
import tempfile
import uuid
from typing import Optional
import shutil
from huggingface_hub import snapshot_download

class TTSService:
    def __init__(self):
        self.is_initialized = False
        self.breezy_voice_path = "/app/BreezyVoice"
        self.model_path = "/app/models/BreezyVoice"
        self.output_dir = "/app/outputs"
        self.uploads_dir = "/app/uploads"
        
        # 固定參考音檔設定
        self.default_speaker_audio = None
        self.speaker_transcription = None  # 可選的參考音檔轉錄文字
        
        # 確保所有必要目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs("./models", exist_ok=True)

    async def initialize(self, speaker_audio_path: Optional[str] = None, speaker_transcription: Optional[str] = None):
        """初始化 BreezyVoice TTS 系統
        
        Args:
            speaker_audio_path: 固定參考音檔路徑，初始化後將用於所有合成
            speaker_transcription: 參考音檔的轉錄文字（可選，用於提升品質）
        """
        try:
            print("正在初始化 BreezyVoice TTS...")
            
            # 檢查 BreezyVoice 代碼是否已存在
            if not os.path.exists(self.breezy_voice_path):
                print("BreezyVoice 代碼尚未安裝，請先透過 Docker 建置包含 BreezyVoice 的環境")
                self.is_initialized = False
                return
            
            # 下載 BreezyVoice 模型（如果尚未下載）
            await self._download_model()
            
            # 檢查必要檔案是否存在
            single_inference_path = os.path.join(self.breezy_voice_path, "single_inference.py")
            if not os.path.exists(single_inference_path):
                print(f"找不到 {single_inference_path}")
                self.is_initialized = False
                return
            
            # 設定固定參考音檔
            if speaker_audio_path and os.path.exists(speaker_audio_path):
                self.default_speaker_audio = os.path.abspath(speaker_audio_path)
                self.speaker_transcription = speaker_transcription
                print(f"使用固定參考音檔: {self.default_speaker_audio}")
            else:
                # 使用預設的語者音檔 - 使用絕對路徑
                default_path = os.path.abspath(os.path.join(self.breezy_voice_path, "data/example.wav"))
                if os.path.exists(default_path):
                    self.default_speaker_audio = default_path
                    print(f"使用預設參考音檔: {default_path}")
                else:
                    print(f"警告: 找不到預設參考音檔 {default_path}")
                    # 嘗試不使用參考音檔
                    self.default_speaker_audio = None
                    print("將嘗試不使用參考音檔進行合成")
            
            self.is_initialized = True
            print("BreezyVoice TTS 初始化完成!")
            
        except Exception as e:
            print(f"TTS 初始化失敗: {e}")
            self.is_initialized = False
    
    async def _download_model(self):
        """下載 BreezyVoice 模型"""
        try:
            if os.path.exists(self.model_path) and os.listdir(self.model_path):
                print("BreezyVoice 模型已存在，跳過下載")
                return
            
            print("正在下載 BreezyVoice 模型...")
            # 從 Hugging Face 下載模型，使用正確的模型 ID
            snapshot_download(
                repo_id="MediaTek-Research/BreezyVoice-300M",  # 使用 300M 版本
                local_dir=self.model_path,
                local_dir_use_symlinks=False
            )
            print("BreezyVoice 模型下載完成!")
            
        except Exception as e:
            print(f"模型下載失敗: {e}")
            # 如果 Hugging Face 下載失敗，使用預設模型路徑
            print("將使用預設模型配置")
    
    def is_ready(self) -> bool:
        """檢查 TTS 是否準備就緒"""
        return self.is_initialized
    
    async def save_temp_audio(self, audio_data: bytes, prefix: str = "temp") -> str:
        """儲存暫存音檔"""
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.wav"
        file_path = os.path.join(self.uploads_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(audio_data)
        
        return file_path
    
    async def synthesize(self, text: str) -> str:
        """使用固定參考音檔合成語音
        
        Args:
            text: 要合成的文字內容
            
        Returns:
            str: 合成的音檔路徑
        """
        if not self.is_ready():
            raise Exception("TTS 系統尚未初始化")
        
        try:
            # 準備輸出檔案路徑
            output_filename = f"tts_output_{uuid.uuid4().hex[:8]}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 準備 BreezyVoice 指令
            cmd = [
                "python", 
                "single_inference.py",
                "--content_to_synthesize", text,
                "--output_path", os.path.abspath(output_path),
            ]
            
            # 使用固定的參考音檔
            if self.default_speaker_audio:
                cmd.extend(["--speaker_prompt_audio_path", self.default_speaker_audio])
                
                # 如果有提供參考音檔的轉錄文字，也加入指令
                if self.speaker_transcription:
                    cmd.extend(["--speaker_prompt_text", self.speaker_transcription])
            
            # 設定模型路徑
            if os.path.exists(self.model_path):
                cmd.extend([
                    "--model_path", os.path.abspath(self.model_path)
                ])
            else:
                # 使用預設的 Hugging Face 模型
                cmd.extend([
                    "--model_path", "MediaTek-Research/BreezyVoice-300M"
                ])
            
            print(f"執行 TTS 指令: {' '.join(cmd)}")
            print(f"執行目錄: {os.path.abspath(self.breezy_voice_path)}")
            print(f"使用參考音檔: {self.default_speaker_audio}")
            
            # 執行 BreezyVoice
            print("開始執行 BreezyVoice，這可能需要幾分鐘時間...")
            result = subprocess.run(
                cmd,
                cwd=self.breezy_voice_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 分鐘超時
            )
            
            if result.returncode != 0:
                error_msg = f"BreezyVoice 執行失敗: {result.stderr}"
                print(error_msg)
                print(f"stdout: {result.stdout}")
                raise Exception(error_msg)
            
            # 檢查輸出檔案是否成功產生
            if not os.path.exists(output_path):
                raise Exception("TTS 輸出檔案未成功產生")
            
            print(f"TTS 合成完成: {output_path}")
            return output_path
        
        except subprocess.TimeoutExpired:
            raise Exception("TTS 處理超時")
        except Exception as e:
            print(f"TTS 合成錯誤: {e}")
            raise Exception(f"語音合成失敗: {str(e)}")
    
    async def synthesize_simple(self, text: str) -> str:
        """簡化版語音合成（使用固定參考音檔）"""
        return await self.synthesize(text)
    
    async def set_speaker_reference(self, speaker_audio_path: str, speaker_transcription: Optional[str] = None):
        """動態設定參考音檔（如果需要更換固定參考音檔時使用）
        
        Args:
            speaker_audio_path: 新的參考音檔路徑
            speaker_transcription: 參考音檔的轉錄文字（可選）
        """
        if os.path.exists(speaker_audio_path):
            self.default_speaker_audio = os.path.abspath(speaker_audio_path)
            self.speaker_transcription = speaker_transcription
            print(f"已更新參考音檔: {self.default_speaker_audio}")
        else:
            raise Exception(f"參考音檔不存在: {speaker_audio_path}")
    
    def get_speaker_reference(self) -> Optional[str]:
        """取得目前使用的參考音檔路徑"""
        return self.default_speaker_audio

# 測試腳本
if __name__ == "__main__":
    import asyncio
    
    async def test_tts():
        tts_service = TTSService()
        
        # 可以在初始化時指定固定參考音檔
        # await tts_service.initialize(speaker_audio_path="./custom_speaker.wav", speaker_transcription="這是我的聲音")
        
        # 或使用預設參考音檔
        await tts_service.initialize()
        
        if not tts_service.is_ready():
            print("TTS 系統未準備好，無法進行測試")
            return
        
        print(f"目前使用的參考音檔: {tts_service.get_speaker_reference()}")
        
        test_text = "余先生你好我是台北富邦銀行電銷專員"
        print(f"正在合成語音: {test_text}")
        
        try:
            output_path = await tts_service.synthesize(test_text)
            print(f"語音合成成功，輸出檔案: {output_path}")
        except Exception as e:
            print(f"語音合成失敗: {e}")
    
    asyncio.run(test_tts())