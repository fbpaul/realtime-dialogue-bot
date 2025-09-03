import os
import uuid
import time
import sys
import torch
import soundfile as sf
from typing import Optional, List
import shutil
from app.config import config

# 添加 Spark-TTS 路徑
sys.path.append('/app/Spark-TTS')
sys.path.append('/app/Spark-TTS/cli')

class TTSSparkService:
    def __init__(self):
        self.is_initialized = False
        self.spark_tts = None
        
        # 路徑設定
        self.model_dir = "./models/Spark-TTS-0.5B"
        self.spark_tts_path = "/app/Spark-TTS"
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
        """從配置文件載入 TTS Spark 參數"""
        tts_config = config.get_tts_config("spark")
        self.device_id = tts_config.get("device_id", 0)
        self.device = f"cuda:{self.device_id}" if torch.cuda.is_available() else "cpu"
        self.model_dir = tts_config.get("model_dir", self.model_dir)
        
        # Spark-TTS 特有參數
        self.default_prompt_text = tts_config.get("default_prompt_text", "欸這個很有趣耶，趕快跟我說一下吧")
        self.default_gender = tts_config.get("gender", "male")  # male, female
        self.default_pitch = tts_config.get("pitch", "moderate")  # very_low, low, moderate, high, very_high
        self.default_speed = tts_config.get("speed", "moderate")  # very_low, low, moderate, high, very_high
        
        # 從配置文件讀取預設語者設定
        default_speaker_config = tts_config.get("default_speaker", {})
        self.default_speaker_path = default_speaker_config.get("audio_path", None)
        if default_speaker_config.get("transcription"):
            self.default_prompt_text = default_speaker_config.get("transcription")
        
        print(f"TTS Spark 配置載入: device={self.device}, model_dir={self.model_dir}")
        if self.default_speaker_path:
            print(f"預設語者: {self.default_speaker_path}")
            print(f"預設提示文字: {self.default_prompt_text}")

    async def initialize(self):
        """初始化 Spark-TTS 模型"""
        if self.is_initialized:
            print("Spark-TTS 已經初始化完成")
            return True
            
        try:
            print("正在初始化 Spark-TTS...")
            
            # 檢查模型目錄是否存在
            if not os.path.exists(self.model_dir):
                print(f"錯誤: Spark-TTS 模型目錄不存在: {self.model_dir}")
                print("請確保已下載 Spark-TTS-0.5B 模型到指定路徑")
                return False
                
            # 檢查必要的子目錄
            llm_dir = os.path.join(self.model_dir, "LLM")
            config_file = os.path.join(self.model_dir, "config.yaml")
            
            if not os.path.exists(llm_dir):
                print(f"錯誤: LLM 目錄不存在: {llm_dir}")
                return False
                
            if not os.path.exists(config_file):
                print(f"錯誤: 配置文件不存在: {config_file}")
                return False
            
            # 導入並初始化 Spark-TTS
            from cli.SparkTTS import SparkTTS
            
            # 設置設備
            if torch.cuda.is_available():
                device = torch.device(f"cuda:{self.device_id}")
            else:
                device = torch.device("cpu")
            
            self.spark_tts = SparkTTS(
                model_dir=self.model_dir,
                device=device
            )
            
            self.is_initialized = True
            print(f"Spark-TTS 初始化完成! 使用設備: {device}")
            
            # 載入預設語者
            await self._load_default_speakers()
            return True
            
        except Exception as e:
            print(f"Spark-TTS 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
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
                            "transcription": self.default_prompt_text  # 使用預設提示文字
                        }
                        print(f"載入語者: {speaker_id}")
            
            print(f"總共載入 {len(self.speakers)} 個語者")
            
        except Exception as e:
            print(f"載入預設語者失敗: {e}")
    
    def is_ready(self) -> bool:
        """檢查模型是否準備就緒"""
        return self.is_initialized and self.spark_tts is not None
    
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
    
    async def add_speaker(self, speaker_file_path: str, speaker_name: str = None, 
                         transcription: str = None) -> str:
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
                "transcription": transcription or self.default_prompt_text
            }
            
            print(f"成功新增語者: {speaker_id}")
            return speaker_id
            
        except Exception as e:
            print(f"新增語者失敗: {e}")
            raise e
    
    async def synthesize(self, text: str, speaker_voice_path: str = None, 
                        speaker_id: str = None, prompt_text: str = None,
                        gender: str = None, pitch: str = None, speed: str = None,
                        use_voice_cloning: bool = True) -> bytes:
        """合成語音
        
        Args:
            text: 要合成的文字
            speaker_voice_path: 語者音檔路徑
            speaker_id: 語者 ID
            prompt_text: 提示文字
            gender: 性別 (僅在 use_voice_cloning=False 時使用)
            pitch: 音調 (僅在 use_voice_cloning=False 時使用)
            speed: 語速 (僅在 use_voice_cloning=False 時使用)
            use_voice_cloning: 是否使用語者克隆模式
        """
        if not self.is_ready():
            raise Exception("Spark-TTS 尚未初始化")
        
        try:
            start_time = time.time()
            
            # 決定使用的語者音檔和提示文字
            voice_path = None
            used_prompt_text = prompt_text or self.default_prompt_text
            
            if speaker_voice_path and os.path.exists(speaker_voice_path):
                voice_path = speaker_voice_path
            elif speaker_id and speaker_id in self.speakers:
                voice_path = self.speakers[speaker_id]["path"]
                used_prompt_text = self.speakers[speaker_id]["transcription"]
            else:
                # 如果沒有指定語者，且要使用語者克隆，則使用第一個可用的語者
                if use_voice_cloning and self.speakers:
                    first_speaker = next(iter(self.speakers.values()))
                    voice_path = first_speaker["path"]
                    used_prompt_text = first_speaker["transcription"]
                elif not use_voice_cloning:
                    # 語音控制模式不需要語者音檔
                    voice_path = None
                else:
                    raise Exception("語者克隆模式需要指定語者音檔")
            
            # 檢查語者音檔是否存在（僅在語者克隆模式下）
            if use_voice_cloning:
                if not voice_path or not os.path.exists(voice_path):
                    raise Exception(f"語者音檔不存在: {voice_path}")
            
            # 生成輸出檔名
            output_filename = f"spark_output_{uuid.uuid4().hex[:8]}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 記錄使用的模式和參數
            if use_voice_cloning:
                print(f"開始合成語音 (語者克隆模式)...")
                print(f"文字: {text}")
                print(f"語者音檔: {voice_path}")
                print(f"提示文字: {used_prompt_text}")
            else:
                print(f"開始合成語音 (語音控制模式)...")
                print(f"文字: {text}")
                print(f"參數: gender={gender or self.default_gender}, pitch={pitch or self.default_pitch}, speed={speed or self.default_speed}")
            
            print(f"輸出檔案: {output_path}")
            
            # 調用 Spark-TTS 進行推論
            with torch.no_grad():
                if use_voice_cloning:
                    # 語者克隆模式：使用語者音檔，不傳遞 gender/pitch/speed
                    wav = self.spark_tts.inference(
                        text,
                        prompt_speech_path=voice_path,
                        prompt_text=used_prompt_text,
                        # 注意：不傳遞 gender, pitch, speed 參數
                    )
                else:
                    # 語音控制模式：使用性別/音調/語速參數，不使用語者音檔
                    wav = self.spark_tts.inference(
                        text,
                        prompt_speech_path=None,  # 不使用語者音檔
                        prompt_text=None,
                        gender=gender or self.default_gender,
                        pitch=pitch or self.default_pitch,
                        speed=speed or self.default_speed,
                    )
                
                # 保存音頻文件
                sf.write(output_path, wav, samplerate=16000)
            
            # 檢查輸出檔案是否存在
            if not os.path.exists(output_path):
                raise Exception("語音合成失敗，未產生輸出檔案")
            
            synthesis_time = time.time() - start_time
            mode_str = "語者克隆" if use_voice_cloning else "語音控制"
            print(f"Spark-TTS 語音合成完成! ({mode_str}模式) 耗時: {synthesis_time:.2f} 秒")
            
            # 讀取音檔內容為 bytes（與其他 TTS 引擎保持一致）
            with open(output_path, "rb") as f:
                audio_data = f.read()
            
            print(f"音檔大小: {len(audio_data)} bytes")
            print(f"音檔儲存於: {output_path}")
            
            return audio_data
            
        except Exception as e:
            print(f"Spark-TTS 語音合成失敗: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    async def synthesize_with_speaker_file(self, text: str, speaker_file_path: str, 
                                          prompt_text: str = None, use_voice_cloning: bool = True) -> bytes:
        """使用指定語者檔案合成語音
        
        Args:
            text: 要合成的文字
            speaker_file_path: 語者音檔路徑
            prompt_text: 提示文字
            use_voice_cloning: 是否使用語者克隆模式 (預設為 True)
        """
        return await self.synthesize(
            text, 
            speaker_voice_path=speaker_file_path, 
            prompt_text=prompt_text,
            use_voice_cloning=use_voice_cloning
        )
    
    async def synthesize_to_file(self, text: str, speaker_voice_path: str = None, 
                               speaker_id: str = None, prompt_text: str = None,
                               gender: str = None, pitch: str = None, speed: str = None,
                               use_voice_cloning: bool = True) -> str:
        """合成語音並返回檔案路徑（如果需要保留檔案）"""
        if not self.is_ready():
            raise Exception("Spark-TTS 尚未初始化")
        
        try:
            start_time = time.time()
            
            # 決定使用的語者音檔和提示文字
            voice_path = None
            used_prompt_text = prompt_text or self.default_prompt_text
            
            if speaker_voice_path and os.path.exists(speaker_voice_path):
                voice_path = speaker_voice_path
            elif speaker_id and speaker_id in self.speakers:
                voice_path = self.speakers[speaker_id]["path"]
                used_prompt_text = self.speakers[speaker_id]["transcription"]
            else:
                # 如果沒有指定語者，且要使用語者克隆，則使用第一個可用的語者
                if use_voice_cloning and self.speakers:
                    first_speaker = next(iter(self.speakers.values()))
                    voice_path = first_speaker["path"]
                    used_prompt_text = first_speaker["transcription"]
                elif not use_voice_cloning:
                    # 語音控制模式不需要語者音檔
                    voice_path = None
                else:
                    raise Exception("語者克隆模式需要指定語者音檔")
            
            # 檢查語者音檔是否存在（僅在語者克隆模式下）
            if use_voice_cloning:
                if not voice_path or not os.path.exists(voice_path):
                    raise Exception(f"語者音檔不存在: {voice_path}")
            
            # 生成輸出檔名
            output_filename = f"spark_output_{uuid.uuid4().hex[:8]}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 記錄使用的模式和參數
            if use_voice_cloning:
                print(f"開始合成語音到檔案 (語者克隆模式)...")
                print(f"文字: {text}")
                print(f"語者音檔: {voice_path}")
                print(f"提示文字: {used_prompt_text}")
            else:
                print(f"開始合成語音到檔案 (語音控制模式)...")
                print(f"文字: {text}")
                print(f"參數: gender={gender or self.default_gender}, pitch={pitch or self.default_pitch}, speed={speed or self.default_speed}")
            
            print(f"輸出檔案: {output_path}")
            
            # 調用 Spark-TTS 進行推論
            with torch.no_grad():
                if use_voice_cloning:
                    # 語者克隆模式：使用語者音檔，不傳遞 gender/pitch/speed
                    wav = self.spark_tts.inference(
                        text,
                        prompt_speech_path=voice_path,
                        prompt_text=used_prompt_text,
                        # 注意：不傳遞 gender, pitch, speed 參數
                    )
                else:
                    # 語音控制模式：使用性別/音調/語速參數，不使用語者音檔
                    wav = self.spark_tts.inference(
                        text,
                        prompt_speech_path=None,  # 不使用語者音檔
                        prompt_text=None,
                        gender=gender or self.default_gender,
                        pitch=pitch or self.default_pitch,
                        speed=speed or self.default_speed,
                    )
                
                # 保存音頻文件
                sf.write(output_path, wav, samplerate=16000)
            
            # 檢查輸出檔案是否存在
            if not os.path.exists(output_path):
                raise Exception("語音合成失敗，未產生輸出檔案")
            
            synthesis_time = time.time() - start_time
            mode_str = "語者克隆" if use_voice_cloning else "語音控制"
            print(f"Spark-TTS 語音合成到檔案完成! ({mode_str}模式) 耗時: {synthesis_time:.2f} 秒")
            print(f"檔案路徑: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"Spark-TTS 語音合成到檔案失敗: {e}")
            raise e
    
    def cleanup(self):
        """清理資源"""
        try:
            if hasattr(self, 'spark_tts') and self.spark_tts is not None:
                # Spark-TTS 可能沒有特定的清理方法，但我們可以清理模型引用
                if hasattr(self.spark_tts, 'model'):
                    self.spark_tts.model = None
                if hasattr(self.spark_tts, 'tokenizer'):
                    self.spark_tts.tokenizer = None
                if hasattr(self.spark_tts, 'audio_tokenizer'):
                    self.spark_tts.audio_tokenizer = None
                self.spark_tts = None
            self.is_initialized = False
            print("Spark-TTS 資源清理完成")
        except Exception as e:
            print(f"Spark-TTS 資源清理失敗: {e}")
