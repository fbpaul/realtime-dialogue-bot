import os
import uuid
import time
from typing import Optional, List
import sys
import torch
import shutil
from app.config import config

# 添加 IndexTTS 路徑
sys.path.append('/app/index-tts')

class TTSIndexService:
    def __init__(self):
        self.is_initialized = False
        self.tts = None
        
        # 路徑設定
        self.model_dir = "./models/IndexTTS-1.5/"
        self.cfg_path = "./models/IndexTTS-1.5/config.yaml"
        self.output_dir = "./outputs"
        self.uploads_dir = "./uploads"
        self.voices_dir = "./voices"
        
        # 語者管理 - 與其他 TTS 引擎格式一致
        self.speakers = {}  # {speaker_id: {"name": str, "path": str, "transcription": str}}
        self.default_speaker_path = None  # 預設語者路徑
        
        # 從配置文件載入參數
        self._load_config()
        
        # 確保所有必要目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.voices_dir, exist_ok=True)
        os.makedirs("./models", exist_ok=True)
        
    def _load_config(self):
        """從配置文件載入 TTS Index 參數"""
        tts_config = config.get_tts_config("index")
        self.device = tts_config.get("device", "cuda:1" if torch.cuda.is_available() else "cpu")
        self.model_dir = tts_config.get("model_dir", self.model_dir)
        self.cfg_path = tts_config.get("cfg_path", self.cfg_path)
        
        # 從配置文件讀取預設語者設定
        default_speaker_config = tts_config.get("default_speaker", {})
        self.default_speaker_path = default_speaker_config.get("audio_path", None)
        
        print(f"TTS Index 配置載入: device={self.device}, model_dir={self.model_dir}")
        if self.default_speaker_path:
            print(f"預設語者: {self.default_speaker_path}")

    async def initialize(self):
        """初始化 IndexTTS 模型"""
        if self.is_initialized:
            print("IndexTTS 已經初始化完成")
            return True
            
        try:
            print("正在初始化 IndexTTS...")
            
            # 檢查模型目錄是否存在
            if not os.path.exists(self.model_dir):
                print(f"錯誤: IndexTTS 模型目錄不存在: {self.model_dir}")
                print("請確保已下載 IndexTTS-1.5 模型到指定路徑")
                return False
                
            if not os.path.exists(self.cfg_path):
                print(f"錯誤: IndexTTS 配置文件不存在: {self.cfg_path}")
                return False
            
            # 導入並初始化 IndexTTS
            from indextts.infer import IndexTTS
            
            self.tts = IndexTTS(
                model_dir=self.model_dir,
                cfg_path=self.cfg_path
            )
            
            self.is_initialized = True
            print("IndexTTS 初始化完成!")
            
            # 載入預設語者
            await self._load_default_speakers()
            return True
            
        except Exception as e:
            print(f"IndexTTS 初始化失敗: {e}")
            return False
    
    async def _load_default_speakers(self):
        """載入預設語者"""
        try:
            # 掃描 voices 目錄中的音檔
            if os.path.exists(self.voices_dir):
                for filename in os.listdir(self.voices_dir):
                    if filename.endswith(('.wav', '.mp3', '.flac')):
                        speaker_id = os.path.splitext(filename)[0]
                        speaker_path = os.path.join(self.voices_dir, filename)
                        
                        self.speakers[speaker_id] = {
                            "name": speaker_id,
                            "path": speaker_path,
                            "transcription": ""  # IndexTTS 不需要文字轉錄
                        }
                        print(f"載入語者: {speaker_id}")
            
            print(f"總共載入 {len(self.speakers)} 個語者")
            
        except Exception as e:
            print(f"載入預設語者失敗: {e}")
    
    def is_ready(self) -> bool:
        """檢查模型是否準備就緒"""
        return self.is_initialized and self.tts is not None
    
    def get_speakers(self) -> List[dict]:
        """取得可用語者清單"""
        return [
            {
                "id": speaker_id,
                "name": speaker_data["name"],
                "path": speaker_data["path"]
            }
            for speaker_id, speaker_data in self.speakers.items()
        ]
    
    async def add_speaker(self, speaker_file_path: str, speaker_name: str = None, transcription: str = "") -> str:
        """新增語者"""
        try:
            if not os.path.exists(speaker_file_path):
                raise Exception(f"語者音檔不存在: {speaker_file_path}")
            
            # 生成語者 ID
            speaker_id = speaker_name or f"speaker_{int(time.time())}"
            
            # 複製音檔到 voices 目錄
            file_extension = os.path.splitext(speaker_file_path)[1]
            target_path = os.path.join(self.voices_dir, f"{speaker_id}{file_extension}")
            shutil.copy2(speaker_file_path, target_path)
            
            # 添加到語者清單
            self.speakers[speaker_id] = {
                "name": speaker_name or speaker_id,
                "path": target_path,
                "transcription": transcription
            }
            
            print(f"成功新增語者: {speaker_id}")
            return speaker_id
            
        except Exception as e:
            print(f"新增語者失敗: {e}")
            raise e
    
    async def synthesize(self, text: str, speaker_voice_path: str = None, speaker_id: str = None) -> str:
        """合成語音"""
        if not self.is_ready():
            raise Exception("IndexTTS 尚未初始化")
        
        try:
            start_time = time.time()
            
            # 決定使用的語者音檔
            voice_path = None
            if speaker_voice_path and os.path.exists(speaker_voice_path):
                voice_path = speaker_voice_path
                print(f"使用指定的語者音檔: {speaker_voice_path}")
            elif speaker_id and speaker_id in self.speakers:
                voice_path = self.speakers[speaker_id]["path"]
                print(f"使用語者 ID: {speaker_id}")
            else:
                # 優先使用配置文件中的預設語者
                if self.default_speaker_path and os.path.exists(self.default_speaker_path):
                    voice_path = self.default_speaker_path
                    print(f"使用配置文件中的預設語者: {self.default_speaker_path}")
                elif self.speakers:
                    # 如果配置的預設語者不存在，則使用第一個可用語者
                    first_speaker = next(iter(self.speakers.values()))
                    voice_path = first_speaker["path"]
                    print(f"配置的預設語者不可用，使用第一個可用語者: {voice_path}")
                else:
                    raise Exception("沒有可用的語者音檔")
            
            if not os.path.exists(voice_path):
                raise Exception(f"語者音檔不存在: {voice_path}")
            
            # 生成輸出檔名
            output_filename = f"indextts_output_{uuid.uuid4().hex[:8]}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            print(f"開始合成語音...")
            print(f"文字: {text}")
            print(f"語者音檔: {voice_path}")
            print(f"輸出檔案: {output_path}")
            
            # 調用 IndexTTS 進行推論
            self.tts.infer(voice_path, text, output_path=output_path)
            
            # 檢查輸出檔案是否存在
            if not os.path.exists(output_path):
                raise Exception("語音合成失敗，未產生輸出檔案")
            
            synthesis_time = time.time() - start_time
            print(f"IndexTTS 語音合成完成! 耗時: {synthesis_time:.2f} 秒")
            
            # 讀取音檔內容為 bytes（與其他 TTS 引擎保持一致）
            with open(output_path, "rb") as f:
                audio_data = f.read()
            
            print(f"音檔大小: {len(audio_data)} bytes")
            print(f"音檔儲存於: {output_path}")
            
            return audio_data
            
        except Exception as e:
            print(f"IndexTTS 語音合成失敗: {e}")
            raise e
    
    async def synthesize_with_speaker_file(self, text: str, speaker_file_path: str) -> bytes:
        """使用指定語者檔案合成語音"""
        return await self.synthesize(text, speaker_voice_path=speaker_file_path)
    
    async def synthesize_to_file(self, text: str, speaker_voice_path: str = None, speaker_id: str = None) -> str:
        """合成語音並返回檔案路徑（如果需要保留檔案）"""
        if not self.is_ready():
            raise Exception("IndexTTS 尚未初始化")
        
        try:
            start_time = time.time()
            
            # 決定使用的語者音檔
            voice_path = None
            if speaker_voice_path and os.path.exists(speaker_voice_path):
                voice_path = speaker_voice_path
            elif speaker_id and speaker_id in self.speakers:
                voice_path = self.speakers[speaker_id]["path"]
            else:
                # 使用第一個可用的語者
                if self.speakers:
                    first_speaker = next(iter(self.speakers.values()))
                    voice_path = first_speaker["path"]
                else:
                    raise Exception("沒有可用的語者音檔")
            
            if not os.path.exists(voice_path):
                raise Exception(f"語者音檔不存在: {voice_path}")
            
            # 生成輸出檔名
            output_filename = f"indextts_output_{uuid.uuid4().hex[:8]}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            print(f"開始合成語音到檔案...")
            print(f"文字: {text}")
            print(f"語者音檔: {voice_path}")
            print(f"輸出檔案: {output_path}")
            
            # 調用 IndexTTS 進行推論
            self.tts.infer(voice_path, text, output_path=output_path)
            
            # 檢查輸出檔案是否存在
            if not os.path.exists(output_path):
                raise Exception("語音合成失敗，未產生輸出檔案")
            
            synthesis_time = time.time() - start_time
            print(f"IndexTTS 語音合成到檔案完成! 耗時: {synthesis_time:.2f} 秒")
            print(f"檔案路徑: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"IndexTTS 語音合成到檔案失敗: {e}")
            raise e
    
    def cleanup(self):
        """清理資源"""
        try:
            if hasattr(self, 'tts') and self.tts is not None:
                # IndexTTS 可能沒有特定的清理方法
                self.tts = None
            self.is_initialized = False
            print("IndexTTS 資源清理完成")
        except Exception as e:
            print(f"IndexTTS 資源清理失敗: {e}")
