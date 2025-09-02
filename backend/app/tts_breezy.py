import os
import subprocess
import tempfile
import uuid
import sys
import time
from typing import Optional, List
import shutil
from huggingface_hub import snapshot_download
import torch
import torchaudio
from app.config import config
from app.config import config

class TTSBreezyService:
    def __init__(self):
        self.is_initialized = False
        self.breezy_voice_path = "/app/BreezyVoice"
        self.model_path = "/app/models/BreezyVoice"
        self.output_dir = "/app/outputs"
        self.uploads_dir = "/app/uploads"
        self.voices_dir = "/app/voices"
        
        # 語者管理 - 與 tts_vibe 格式一致
        self.speakers = {}  # {speaker_id: {"name": str, "path": str, "transcription": str}}
        self.speaker_cache = {}  # 緩存處理過的結果
        
        # 模型實例（在初始化時載入）
        self.cosyvoice = None
        self.bopomofo_converter = None
        
        # === 新增優化緩存 ===
        self.speaker_audio_cache = {}  # 緩存預載入的音檔 {speaker_id: tensor}
        self.speaker_processed_cache = {}  # 緩存處理過的語者數據 {speaker_id: {"normalized": str, "bopomofo": str}}
        self.whisper_asr = None  # 緩存 ASR Pipeline
        self.opencc_converter = None  # 緩存 OpenCC 轉換器
        self.word_utils_imported = False  # 標記 word_utils 是否已匯入
        
        # === 進階優化設置 ===
        self.model_warmed_up = False  # 模型預熱狀態
        self.use_mixed_precision = True  # 是否使用混合精度
        self.quantization_enabled = False  # 是否啟用量化（需要支持）
        self.parallel_synthesis = True  # 是否啟用並行合成
        self.max_concurrent_segments = 3  # 最大並行合成段數
        
        # 從配置文件載入參數
        self._load_config()
        
        # 確保所有必要目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.voices_dir, exist_ok=True)
        os.makedirs("./models", exist_ok=True)
    
    def _load_config(self):
        """從配置文件載入 TTS Breezy 參數"""
        tts_config = config.get_tts_config("breezy")
        self.device = tts_config.get("device", "cuda:1" if torch.cuda.is_available() else "cpu")
        print(f"TTS Breezy 配置載入: device={self.device}")
        
        # 更新設備相關設置
        if "cpu" in self.device:
            self.use_mixed_precision = False  # CPU 不支持混合精度
            print("檢測到 CPU 設備，停用混合精度")
        

    async def initialize(self, model_repo: str = "MediaTek-Research/BreezyVoice-300M", 
                        speaker_voices: Optional[List[str]] = None, 
                        speaker_names: Optional[List[str]] = None,
                        speaker_transcriptions: Optional[List[str]] = None):
        """初始化 BreezyVoice TTS 系統
        
        Args:
            model_repo: 模型倉庫名稱
            speaker_voices: 固定參考語者音檔路徑列表
            speaker_names: 語者名稱列表，對應 speaker_voices
            speaker_transcriptions: 語者逐字稿列表（可選，用於提升品質和速度）
        """
        try:
            print("正在初始化 BreezyVoice TTS...")
            
            # 檢查 BreezyVoice 代碼是否已存在
            if not os.path.exists(self.breezy_voice_path):
                print("BreezyVoice 代碼尚未安裝，請先透過 Docker 建置包含 BreezyVoice 的環境")
                self.is_initialized = False
                return
            
            # 下載 BreezyVoice 模型（如果尚未下載）
            await self._download_model(model_repo)
            
            # 添加 BreezyVoice 路徑到 sys.path
            if self.breezy_voice_path not in sys.path:
                sys.path.insert(0, self.breezy_voice_path)
            
            # 初始化模型
            print("正在載入 CustomCosyVoice 模型...")
            from single_inference import CustomCosyVoice
            from g2pw import G2PWConverter
            
            # 初始化 TTS 主模型
            model_path_to_use = self.model_path if os.path.exists(self.model_path) else model_repo
            self.cosyvoice = CustomCosyVoice(model_path_to_use)
            print("CustomCosyVoice 模型載入完成")
            
            # === 模型優化設置 ===
            await self._optimize_model()
            
            # 驗證模型是否正確載入
            if self.cosyvoice is None or self.cosyvoice.model is None:
                raise Exception("CustomCosyVoice 模型載入失敗")
            
            # 初始化注音轉換工具
            print("正在載入 G2PWConverter...")
            self.bopomofo_converter = G2PWConverter()
            print("G2PWConverter 載入完成")
            
            # 驗證注音轉換工具是否正確載入
            if self.bopomofo_converter is None:
                raise Exception("G2PWConverter 載入失敗")
            
            # === 初始化 word_utils（避免重複匯入） ===
            await self._init_word_utils()
            
            # === 初始化 ASR 和轉換器（避免重複載入） ===
            await self._init_asr_tools()
            
            # 設定固定語者
            await self._setup_speakers(speaker_voices, speaker_names, speaker_transcriptions)
            
            # === 模型預熱 ===
            await self._warmup_model()
            
            self.is_initialized = True
            print("BreezyVoice TTS 初始化完成!")
            
        except Exception as e:
            print(f"TTS 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            self.is_initialized = False
    
    async def _download_model(self, model_repo: str):
        """下載 BreezyVoice 模型"""
        try:
            if os.path.exists(self.model_path) and os.listdir(self.model_path):
                print("BreezyVoice 模型已存在，跳過下載")
                return
            
            print(f"正在下載 BreezyVoice 模型: {model_repo}")
            # 從 Hugging Face 下載模型，使用正確的模型 ID
            snapshot_download(
                repo_id=model_repo,
                local_dir=self.model_path,
                local_dir_use_symlinks=False
            )
            print("BreezyVoice 模型下載完成!")
            
        except Exception as e:
            print(f"模型下載失敗: {e}")
            # 如果 Hugging Face 下載失敗，使用預設模型路徑
            print("將使用預設模型配置")

    async def _init_word_utils(self):
        """初始化 word_utils 模組（只執行一次）"""
        if not self.word_utils_imported:
            try:
                utils_path = os.path.join(self.breezy_voice_path, 'utils')
                if utils_path not in sys.path:
                    sys.path.insert(0, utils_path)
                
                # 全域匯入，避免每次重複
                global word_to_dataset_frequency, char2phn, always_augment_chars
                from word_utils import word_to_dataset_frequency, char2phn, always_augment_chars
                
                self.word_utils_imported = True
                print("word_utils 模組初始化完成")
            except Exception as e:
                print(f"word_utils 初始化失敗: {e}")
                self.word_utils_imported = False

    async def _optimize_model(self):
        """模型層面優化"""
        try:
            print("正在應用模型優化...")
            
            # === 混合精度優化 ===
            if self.use_mixed_precision and torch.cuda.is_available():
                try:
                    # 嘗試啟用混合精度
                    if hasattr(self.cosyvoice.model, 'half'):
                        self.cosyvoice.model = self.cosyvoice.model.half()
                        print("✓ 已啟用 FP16 混合精度")
                    else:
                        print("⚠ 模型不支持 FP16，保持 FP32")
                        self.use_mixed_precision = False
                except Exception as e:
                    print(f"⚠ FP16 啟用失敗: {e}，保持 FP32")
                    self.use_mixed_precision = False
            
            # === 量化優化（實驗性） ===
            # 注意：這需要具體模型支持，可能需要額外配置
            if self.quantization_enabled:
                try:
                    # 動態量化（如果支持）
                    import torch.quantization as quantization
                    if hasattr(self.cosyvoice.model, 'qconfig'):
                        quantization.quantize_dynamic(
                            self.cosyvoice.model, 
                            {torch.nn.Linear}, 
                            dtype=torch.qint8
                        )
                        print("✓ 已啟用 INT8 動態量化")
                    else:
                        print("⚠ 模型不支持量化")
                        self.quantization_enabled = False
                except Exception as e:
                    print(f"⚠ 量化失敗: {e}")
                    self.quantization_enabled = False
            
            # === 模型編譯優化（PyTorch 2.0+） ===
            if hasattr(torch, 'compile') and torch.__version__.startswith('2.'):
                try:
                    self.cosyvoice.model = torch.compile(self.cosyvoice.model, mode="reduce-overhead")
                    print("✓ 已啟用 torch.compile 優化")
                except Exception as e:
                    print(f"⚠ torch.compile 失敗: {e}")
            
            print("模型優化完成")
            
        except Exception as e:
            print(f"模型優化失敗: {e}")

    async def _warmup_model(self):
        """模型預熱機制"""
        if self.model_warmed_up:
            return
        
        try:
            print("正在進行模型預熱...")
            
            # 獲取預設語者進行預熱
            default_speaker_id = self.get_default_speaker_id()
            if not default_speaker_id or default_speaker_id not in self.speaker_audio_cache:
                print("⚠ 沒有可用語者進行預熱")
                return
            
            # 預熱文本（短且常見的句子）
            warmup_texts = [
                "你好",
                "測試語音",
            ]
            
            start_time = time.time()
            
            for i, text in enumerate(warmup_texts):
                try:
                    print(f"  預熱 {i+1}/{len(warmup_texts)}: {text}")
                    # 直接調用核心合成，不保存結果
                    await self._run_warmup_synthesis(text, default_speaker_id)
                except Exception as e:
                    print(f"  預熱失敗 {i+1}: {e}")
            
            end_time = time.time()
            self.model_warmed_up = True
            print(f"✓ 模型預熱完成 ({end_time - start_time:.2f}秒)")
            
        except Exception as e:
            print(f"模型預熱失敗: {e}")

    async def _run_warmup_synthesis(self, text: str, speaker_id: str):
        """執行預熱合成（簡化版本）"""
        try:
            # 獲取緩存的語者數據
            prompt_speech_16k = self.speaker_audio_cache[speaker_id]
            cached_data = self.speaker_processed_cache[speaker_id]
            
            # 處理合成內容
            normalized_content = self.cosyvoice.frontend.text_normalize_new(text, split=False)
            content_with_bopomofo = self._get_bopomofo_rare_cached(normalized_content)
            
            # 執行合成（不保存結果）
            with torch.no_grad():  # 節省內存
                if self.use_mixed_precision and torch.cuda.is_available():
                    with torch.cuda.amp.autocast():
                        _ = self.cosyvoice.inference_zero_shot_no_normalize(
                            content_with_bopomofo,
                            cached_data["bopomofo"],
                            prompt_speech_16k
                        )
                else:
                    _ = self.cosyvoice.inference_zero_shot_no_normalize(
                        content_with_bopomofo,
                        cached_data["bopomofo"], 
                        prompt_speech_16k
                    )
            
        except Exception as e:
            raise Exception(f"預熱合成失敗: {e}")

    async def _init_asr_tools(self):
        """初始化 ASR 和轉換工具（只執行一次）"""
        try:
            print("正在初始化 ASR 工具...")
            from transformers import pipeline
            import opencc
            
            # 初始化 Whisper ASR Pipeline
            # 將設備字符串轉換為 transformers pipeline 格式
            device_id = -1  # 預設 CPU
            if "cuda" in self.device:
                try:
                    device_id = int(self.device.split(":")[-1])  # 提取 cuda:N 中的 N
                except:
                    device_id = 0  # 如果解析失敗，使用 cuda:0
            
            self.whisper_asr = pipeline(
                "automatic-speech-recognition", 
                model="openai/whisper-base",
                device=device_id
            )
            
            # 初始化 OpenCC 轉換器
            self.opencc_converter = opencc.OpenCC('s2t')
            
            print("ASR 工具初始化完成")
        except Exception as e:
            print(f"ASR 工具初始化失敗: {e}")
            self.whisper_asr = None
            self.opencc_converter = None

    async def _setup_speakers(self, speaker_voices: Optional[List[str]], 
                             speaker_names: Optional[List[str]], 
                             speaker_transcriptions: Optional[List[str]]):
        """設定語者音檔並預加載"""
        if speaker_voices and all(os.path.exists(path) for path in speaker_voices):
            # 使用自訂語者音檔
            for i, voice_path in enumerate(speaker_voices):
                speaker_id = f"custom_{i}"
                speaker_name = speaker_names[i] if speaker_names and i < len(speaker_names) else f"Speaker{i+1}"
                transcription = speaker_transcriptions[i] if speaker_transcriptions and i < len(speaker_transcriptions) else None
                await self._add_speaker(speaker_id, speaker_name, voice_path, transcription)
            print(f"載入自訂語者: {len(speaker_voices)} 個")
        else:
            # 使用預設語者音檔
            await self._setup_default_speaker()

    async def _setup_default_speaker(self):
        """設定預設語者"""
        # 使用預設的語者音檔 - 使用絕對路徑
        default_path = os.path.abspath(os.path.join(self.breezy_voice_path, "data/example.wav"))
        if os.path.exists(default_path):
            # 使用用戶提供的逐字稿
            default_transcription = "在密碼學中,加密是將明文資訊改變為難以讀取的密文內容,使之不可讀的方法。只有擁有解密方法的對象,經由解密過程才能將密文還原為正常可讀的內容。"
            await self._add_speaker("default", "example_speaker", default_path, default_transcription)
            print(f"載入預設語者: example_speaker")
        else:
            print(f"警告: 找不到預設參考音檔 {default_path}")
            # 備用方案：尋找 voices 目錄中的 .wav 檔案
            if os.path.exists(self.voices_dir):
                voice_files = [f for f in os.listdir(self.voices_dir) if f.endswith('.wav')]
                for i, voice_file in enumerate(voice_files[:3]):  # 最多載入3個語者
                    voice_path = os.path.abspath(os.path.join(self.voices_dir, voice_file))
                    speaker_name = os.path.splitext(voice_file)[0]
                    await self._add_speaker(f"backup_{i}", speaker_name, voice_path, None)
                if voice_files:
                    print(f"載入備用語者: {len(voice_files)} 個")
                else:
                    print("警告: 沒有可用的語者音檔")

    async def _add_speaker(self, speaker_id: str, speaker_name: str, voice_path: str, transcription: Optional[str] = None):
        """添加語者並預處理所有數據"""
        if not os.path.exists(voice_path):
            raise Exception(f"語者音檔不存在: {voice_path}")
        
        voice_path = os.path.abspath(voice_path)
        self.speakers[speaker_id] = {
            "name": speaker_name,
            "path": voice_path,
            "transcription": transcription
        }
        
        # === 預載入音檔到緩存 ===
        await self._preload_speaker_audio(speaker_id, voice_path)
        
        # === 預處理語者數據到緩存 ===
        await self._preprocess_speaker_data(speaker_id, transcription or "")
        
        print(f"  預加載語者: {speaker_name} ({os.path.basename(voice_path)})")

    async def _preload_speaker_audio(self, speaker_id: str, voice_path: str):
        """預載入語者音檔到緩存"""
        try:
            from cosyvoice.utils.file_utils import load_wav
            prompt_speech_16k = load_wav(voice_path, 16000)
            self.speaker_audio_cache[speaker_id] = prompt_speech_16k
            print(f"    ✓ 音檔已預載入緩存")
        except Exception as e:
            print(f"    ✗ 音檔預載入失敗: {e}")

    async def _preprocess_speaker_data(self, speaker_id: str, transcription: str):
        """預處理語者數據到緩存"""
        try:
            if not transcription:
                # 如果沒有逐字稿，使用 ASR 自動生成
                voice_path = self.speakers[speaker_id]["path"]
                transcription = await self._transcribe_audio_cached(voice_path)
                # 更新 speaker 資料
                self.speakers[speaker_id]["transcription"] = transcription
            
            if transcription and self.cosyvoice:
                # 預處理文字正規化和注音轉換
                normalized_text = self.cosyvoice.frontend.text_normalize_new(transcription, split=False)
                bopomofo_text = self._get_bopomofo_rare_cached(normalized_text)
                
                self.speaker_processed_cache[speaker_id] = {
                    "normalized": normalized_text,
                    "bopomofo": bopomofo_text
                }
                print(f"    ✓ 語者數據已預處理: {len(transcription)}字")
            else:
                print(f"    ⚠ 跳過語者數據預處理（無逐字稿或模型未載入）")
                
        except Exception as e:
            print(f"    ✗ 語者數據預處理失敗: {e}")

    def get_speaker_by_id(self, speaker_id: str) -> Optional[dict]:
        """根據 ID 獲取語者資訊"""
        return self.speakers.get(speaker_id)

    def get_speaker_by_path(self, voice_path: str) -> Optional[str]:
        """根據路徑獲取語者 ID"""
        voice_path = os.path.abspath(voice_path)
        for speaker_id, info in self.speakers.items():
            if info["path"] == voice_path:
                return speaker_id
        return None

    def get_default_speaker_id(self) -> Optional[str]:
        """獲取預設語者 ID"""
        if "default" in self.speakers:
            return "default"
        elif self.speakers:
            return list(self.speakers.keys())[0]
        return None
    
    def is_ready(self) -> bool:
        """檢查 TTS 是否準備就緒"""
        return self.is_initialized and self.cosyvoice is not None and self.bopomofo_converter is not None
    
    def _get_bopomofo_rare(self, text):
        """為生僻字和多音字添加注音標註（舊版本，保留兼容性）"""
        return self._get_bopomofo_rare_cached(text)
    
    def _get_bopomofo_rare_cached(self, text):
        """為生僻字和多音字添加注音標註（優化版本）"""
        try:
            # word_utils 已在初始化時匯入
            if not self.word_utils_imported:
                print("word_utils 未初始化，使用原文字")
                return text
            
            # 使用全域變數，避免重複匯入
            global word_to_dataset_frequency, char2phn, always_augment_chars
            
            res = self.bopomofo_converter(text)
            text_w_bopomofo = [x for x in zip(list(text), res[0])]
            reconstructed_text = ""
            
            for i in range(len(text_w_bopomofo)):
                t = text_w_bopomofo[i]
                try:
                    next_t_char = text_w_bopomofo[i+1][0]
                except:
                    next_t_char = None
                
                if word_to_dataset_frequency[t[0]] < 500 and t[1] != None and next_t_char != '[':
                    # Add the char and the pronunciation
                    reconstructed_text += t[0] + f"[:{t[1]}]"
                
                elif len(char2phn[t[0]]) >= 2:
                    if t[1] != char2phn[t[0]][0] and (word_to_dataset_frequency[t[0]] < 10000 or t[0] in always_augment_chars) and next_t_char != '[':  # Not most common pronunciation
                        # Add the char and the pronunciation
                        reconstructed_text += t[0] + f"[:{t[1]}]"
                    else:
                        reconstructed_text += t[0]
                else:
                    # Add only the char
                    reconstructed_text += t[0]
            
            return reconstructed_text
        except Exception as e:
            print(f"注音轉換失敗，使用原文字: {e}")
            return text
    
    def _transcribe_audio(self, audio_path):
        """語音轉文字（舊版本，保留兼容性）"""
        import asyncio
        return asyncio.run(self._transcribe_audio_cached(audio_path))
    
    async def _transcribe_audio_cached(self, audio_path):
        """語音轉文字（優化版本，使用緩存的 ASR）"""
        try:
            # 使用預初始化的 ASR Pipeline
            if self.whisper_asr is None or self.opencc_converter is None:
                print("ASR 工具未初始化，嘗試重新初始化...")
                await self._init_asr_tools()
                
            if self.whisper_asr is None:
                print("ASR 初始化失敗，無法進行語音轉文字")
                return ""
            
            # 使用緩存的 Pipeline 進行 ASR
            result = self.whisper_asr(
                audio_path,
                generate_kwargs={
                    "language": "zh",  # 指定中文
                    "task": "transcribe"  # 轉錄而非翻譯
                }
            )
            
            # 使用緩存的轉換器
            traditional_text = self.opencc_converter.convert(result["text"])
            print(f"ASR 原始結果: {result['text']}")
            print(f"轉為繁體中文: {traditional_text}")
            return traditional_text
        except Exception as e:
            print(f"語音轉文字失敗: {e}")
            return ""
    
    async def save_temp_audio(self, audio_data: bytes, prefix: str = "temp") -> str:
        """儲存暫存音檔"""
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.wav"
        file_path = os.path.join(self.uploads_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(audio_data)
        
        return file_path
    
    async def synthesize(self, text: str, speaker_voice_path: Optional[str] = None, save_file: bool = False) -> bytes:
        """合成語音 - 與 tts_vibe 格式一致
        
        Args:
            text: 要合成的文字內容
            speaker_voice_path: 指定語者音檔路徑（可選）
            save_file: 是否保存檔案（用於分段合成避免遞迴）
            
        Returns:
            bytes: 合成的音檔內容
        """
        if not self.is_ready():
            raise Exception("TTS 系統尚未初始化或模型載入失敗")

        # 檢查文字長度，決定是否需要分段處理
        if len(text) > 50 and not save_file:  # save_file=True 表示已經在分段處理中
            print(f"文字較長({len(text)}字元)，啟用分段處理...")
            return await self._synthesize_long_text(text, speaker_voice_path)

        try:
            # 決定使用的語者
            if speaker_voice_path:
                # 使用指定的語者音檔
                speaker_voice_path = os.path.abspath(speaker_voice_path)
                if not os.path.exists(speaker_voice_path):
                    raise Exception(f"指定的語者音檔不存在: {speaker_voice_path}")
                
                # 檢查是否已經預加載
                speaker_id = self.get_speaker_by_path(speaker_voice_path)
                if not speaker_id:
                    # 動態添加新語者
                    speaker_name = os.path.splitext(os.path.basename(speaker_voice_path))[0]
                    speaker_id = f"dynamic_{len(self.speakers)}"
                    await self._add_speaker(speaker_id, speaker_name, speaker_voice_path, None)
                    print(f"動態加載語者: {speaker_name}")
                
                speaker_info = self.speakers[speaker_id]
                final_voice_path = speaker_info["path"]
                speaker_transcription = speaker_info["transcription"]
                
            else:
                # 使用預設語者
                default_speaker_id = self.get_default_speaker_id()
                if not default_speaker_id:
                    raise Exception("沒有可用的語者音檔")
                
                speaker_info = self.speakers[default_speaker_id]
                final_voice_path = speaker_info["path"]
                speaker_transcription = speaker_info["transcription"]

            print(f"使用語者: {speaker_info['name']} ({final_voice_path})")

            # 檢查是否已在快取中
            cache_key = f"{text}:{final_voice_path}"
            if cache_key in self.speaker_cache:
                print("使用快取的語音")
                return self.speaker_cache[cache_key]

            # 合成語音
            print(f"合成文本: {text}")
            audio_data = await self._run_synthesis(text, final_voice_path, speaker_transcription)

            # 加入快取（限制快取大小避免記憶體溢出）
            if len(self.speaker_cache) >= 50:  # 最多快取50個結果
                # 刪除最舊的快取項目
                oldest_key = next(iter(self.speaker_cache))
                del self.speaker_cache[oldest_key]

            self.speaker_cache[cache_key] = audio_data

            return audio_data

        except Exception as e:
            print(f"TTS 合成失敗: {str(e)}")
            raise
    
    async def _synthesize_long_text(self, text: str, speaker_voice_path: Optional[str] = None) -> bytes:
        """分段處理長文字（並行優化版本）"""
        import re
        import asyncio
        
        # 以句號、問號、驚嘆號分段
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        print(f"長文字分為 {len(sentences)} 段處理")
        
        if not self.parallel_synthesis or len(sentences) <= 1:
            # 序列處理（原始方式）
            audio_segments = []
            for i, sentence in enumerate(sentences):
                print(f"處理第 {i+1}/{len(sentences)} 段: {sentence}")
                segment_audio = await self.synthesize(sentence, speaker_voice_path, save_file=True)
                audio_segments.append(segment_audio)
        else:
            # 並行處理
            print(f"啟用並行處理，最大併發數: {self.max_concurrent_segments}")
            audio_segments = await self._parallel_synthesize_segments(sentences, speaker_voice_path)
        
        # 合併音訊檔案（需要音訊處理庫的完整實現）
        return await self._merge_audio_segments(audio_segments)

    async def _parallel_synthesize_segments(self, sentences: List[str], speaker_voice_path: Optional[str] = None) -> List[bytes]:
        """並行合成多個片段"""
        import asyncio
        
        # 創建信號量限制並發數量
        semaphore = asyncio.Semaphore(self.max_concurrent_segments)
        
        async def synthesize_with_semaphore(i: int, sentence: str) -> tuple:
            async with semaphore:
                try:
                    print(f"  並行處理第 {i+1} 段: {sentence}")
                    audio_data = await self.synthesize(sentence, speaker_voice_path, save_file=True)
                    print(f"  ✓ 完成第 {i+1} 段")
                    return (i, audio_data)
                except Exception as e:
                    print(f"  ✗ 第 {i+1} 段失敗: {e}")
                    return (i, b'')  # 返回空音檔作為占位
        
        # 並行執行所有片段
        tasks = [synthesize_with_semaphore(i, sentence) for i, sentence in enumerate(sentences)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 按順序排列結果
        audio_segments = [None] * len(sentences)
        for result in results:
            if isinstance(result, Exception):
                print(f"並行合成異常: {result}")
                continue
            i, audio_data = result
            audio_segments[i] = audio_data
        
        # 過濾掉失敗的片段
        return [seg for seg in audio_segments if seg is not None and seg != b'']

    async def _merge_audio_segments(self, audio_segments: List[bytes]) -> bytes:
        """合併音訊片段（簡化實現）"""
        if not audio_segments:
            return b''
        
        # 目前返回第一段作為示例
        # 完整實現需要音訊處理庫來正確合併波形
        print(f"合併 {len(audio_segments)} 個音訊片段（簡化實現：返回第一段）")
        return audio_segments[0]

    async def _run_synthesis(self, text: str, voice_path: str, speaker_transcription: Optional[str] = None) -> bytes:
        """執行實際的語音合成（優化版本）"""
        try:
            # === 優化1: 從緩存獲取預載入的音檔 ===
            speaker_id = self.get_speaker_by_path(voice_path)
            if speaker_id and speaker_id in self.speaker_audio_cache:
                prompt_speech_16k = self.speaker_audio_cache[speaker_id]
                print("✓ 使用緩存的音檔數據")
            else:
                # 如果緩存中沒有，則即時載入（不應該發生，但作為備援）
                print("⚠ 緩存未命中，即時載入音檔...")
                from cosyvoice.utils.file_utils import load_wav
                prompt_speech_16k = load_wav(voice_path, 16000)
            
            # === 優化2: 從緩存獲取預處理的語者數據 ===
            if speaker_id and speaker_id in self.speaker_processed_cache:
                cached_data = self.speaker_processed_cache[speaker_id]
                normalized_speaker_text = cached_data["normalized"]
                speaker_text_with_bopomofo = cached_data["bopomofo"]
                print("✓ 使用緩存的語者處理數據")
            else:
                # 如果緩存中沒有，則即時處理
                print("⚠ 語者數據緩存未命中，即時處理...")
                
                # 取得說話者逐字稿
                if speaker_transcription:
                    speaker_prompt_text = speaker_transcription
                else:
                    # 自動語音辨識（使用緩存的 ASR）
                    print("正在進行語音辨識...")
                    speaker_prompt_text = await self._transcribe_audio_cached(voice_path)
                    print(f"辨識結果: {speaker_prompt_text}")
                
                if not speaker_prompt_text:
                    raise Exception("無法取得說話者逐字稿")
                
                # 文字正規化和注音標註
                normalized_speaker_text = self.cosyvoice.frontend.text_normalize_new(
                    speaker_prompt_text, split=False
                )
                speaker_text_with_bopomofo = self._get_bopomofo_rare_cached(normalized_speaker_text)
            
            # === 處理合成內容（只需處理一次） ===
            print("正在處理合成內容...")
            normalized_content = self.cosyvoice.frontend.text_normalize_new(text, split=False)
            content_with_bopomofo = self._get_bopomofo_rare_cached(normalized_content)
            
            print(f"說話者逐字稿（含注音）: {speaker_text_with_bopomofo}")
            print(f"合成內容（含注音）: {content_with_bopomofo}")
            
            # === 語音合成（混合精度優化） ===
            print("開始語音合成...")
            start_time = time.time()
            
            # 使用混合精度加速
            if self.use_mixed_precision and torch.cuda.is_available():
                with torch.cuda.amp.autocast():
                    with torch.no_grad():  # 推論時不需要梯度
                        output = self.cosyvoice.inference_zero_shot_no_normalize(
                            content_with_bopomofo, 
                            speaker_text_with_bopomofo, 
                            prompt_speech_16k
                        )
            else:
                with torch.no_grad():  # 推論時不需要梯度
                    output = self.cosyvoice.inference_zero_shot_no_normalize(
                        content_with_bopomofo, 
                        speaker_text_with_bopomofo, 
                        prompt_speech_16k
                    )
            
            end_time = time.time()
            print(f"合成時間: {end_time - start_time:.2f} 秒")
            print(f"生成音檔長度: {output['tts_speech'].shape[1]/22050:.2f} 秒")
            
            # === 優化的 tensor 轉換 ===
            # 確保在正確的設備和精度下處理
            audio_tensor = output['tts_speech']
            if self.use_mixed_precision:
                # 轉換回 float32 進行音檔保存
                audio_tensor = audio_tensor.float()
            
            # 轉移到 CPU（如果在 GPU 上）
            if audio_tensor.is_cuda:
                audio_tensor = audio_tensor.cpu()
            
            # 將 tensor 轉換為 bytes
            import io
            buffer = io.BytesIO()
            torchaudio.save(buffer, audio_tensor, 22050, format="wav")
            audio_bytes = buffer.getvalue()
            buffer.close()
            
            return audio_bytes
            
        except Exception as e:
            print(f"語音合成錯誤: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"語音合成失敗: {str(e)}")
    
    async def set_speaker_reference(self, speaker_audio_path: str, speaker_name: str = "custom", speaker_transcription: Optional[str] = None):
        """動態設定參考音檔（如果需要更換固定參考音檔時使用）
        
        Args:
            speaker_audio_path: 新的參考音檔路徑
            speaker_name: 語者名稱
            speaker_transcription: 參考音檔的轉錄文字（可選）
        """
        if os.path.exists(speaker_audio_path):
            speaker_id = "dynamic_current"
            await self._add_speaker(speaker_id, speaker_name, speaker_audio_path, speaker_transcription)
            print(f"已更新參考音檔: {speaker_audio_path}")
        else:
            raise Exception(f"參考音檔不存在: {speaker_audio_path}")
    
    def get_speaker_reference(self) -> Optional[str]:
        """取得目前使用的參考音檔路徑"""
        default_id = self.get_default_speaker_id()
        if default_id and default_id in self.speakers:
            return self.speakers[default_id]["path"]
        return None

    def configure_optimization(self, 
                              use_mixed_precision: bool = True,
                              quantization_enabled: bool = False,
                              parallel_synthesis: bool = True,
                              max_concurrent_segments: int = 3):
        """動態配置優化參數"""
        self.use_mixed_precision = use_mixed_precision
        self.quantization_enabled = quantization_enabled
        self.parallel_synthesis = parallel_synthesis
        self.max_concurrent_segments = max_concurrent_segments
        
        print(f"優化配置已更新:")
        print(f"  混合精度: {'啟用' if use_mixed_precision else '停用'}")
        print(f"  模型量化: {'啟用' if quantization_enabled else '停用'}")
        print(f"  並行合成: {'啟用' if parallel_synthesis else '停用'}")
        print(f"  最大併發段數: {max_concurrent_segments}")

    def get_optimization_status(self) -> dict:
        """獲取當前優化狀態"""
        return {
            "mixed_precision": self.use_mixed_precision,
            "quantization": self.quantization_enabled,
            "parallel_synthesis": self.parallel_synthesis,
            "max_concurrent_segments": self.max_concurrent_segments,
            "model_warmed_up": self.model_warmed_up,
            "cache_size": {
                "speaker_cache": len(self.speaker_cache),
                "audio_cache": len(self.speaker_audio_cache),
                "processed_cache": len(self.speaker_processed_cache)
            }
        }

# 測試腳本
if __name__ == "__main__":
    import asyncio
    
    async def test_tts():
        tts_service = TTSBreezyService()
        
        # 或使用預設參考音檔
        await tts_service.initialize()
        
        if not tts_service.is_ready():
            print("TTS 系統未準備好，無法進行測試")
            return
        
        print(f"目前使用的參考音檔: {tts_service.get_speaker_reference()}")
        
        test_text = "余先生你好我是台北富邦銀行電銷專員"
        print(f"正在合成語音: {test_text}")
        
        try:
            # 測試 1: 手動提供逐字稿（推薦方式，更快更準確）
            print("\n=== 測試 1: 合成語音（返回 bytes） ===")
            audio_bytes = await tts_service.synthesize(test_text)
            print(f"語音合成成功，獲得音檔: {len(audio_bytes)} bytes")
            
            # 保存測試文件
            with open("/app/outputs/test_breezy_output.wav", "wb") as f:
                f.write(audio_bytes)
            print("測試音檔已保存到: /app/outputs/test_breezy_output.wav")
            
        except Exception as e:
            print(f"語音合成失敗: {e}")
    
    asyncio.run(test_tts())