import os
import uuid
import time
from typing import Optional, List
import torch
from huggingface_hub import snapshot_download

from vibevoice.modular.modeling_vibevoice_inference import VibeVoiceForConditionalGenerationInference
from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor

class TTSVibeService:
    def __init__(self):
        self.is_initialized = False
        self.model = None
        self.processor = None
        
        # 路徑設定
        self.model_path = "./models/VibeVoice"
        self.output_dir = "./outputs"
        self.uploads_dir = "./uploads"
        self.voices_dir = "./voices"
        
        # 語者管理 - 改為字典形式，支持快速查找和緩存
        self.speakers = {}  # {speaker_id: {"name": str, "path": str, "processed": bool}}
        self.speaker_cache = {}  # 緩存處理過的語者特徵
        
        # 確保所有必要目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs("./models", exist_ok=True)
        os.makedirs(self.voices_dir, exist_ok=True)

    async def initialize(self, model_name: str = "DevParker/VibeVoice7b-low-vram", speaker_voices: Optional[List[str]] = None, speaker_names: Optional[List[str]] = None):
        """初始化 VibeVoice TTS 系統
        
        Args:
            model_name: 使用的模型名稱，可選 "microsoft/VibeVoice-1.5B" 或 "DevParker/VibeVoice7b-low-vram"
            speaker_voices: 固定參考語者音檔路徑列表
            speaker_names: 語者名稱列表，對應 speaker_voices
        """
        try:
            print("正在初始化 VibeVoice TTS...")
            
            # 下載模型到本地
            await self._download_model(model_name)
            
            # 載入 processor
            print(f"載入 processor 從 {self.model_path}")
            self.processor = VibeVoiceProcessor.from_pretrained(self.model_path)
            
            # 載入模型
            print(f"載入模型從 {self.model_path}")
            try:
                # 首先嘗試不使用 flash attention
                self.model = VibeVoiceForConditionalGenerationInference.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.bfloat16,
                    device_map='cuda' if torch.cuda.is_available() else 'cpu',
                    attn_implementation='sdpa'
                )
                print("使用 SDPA attention 載入模型成功")
            except Exception as e:
                print(f"使用 SDPA attention 載入失敗，嘗試預設設定: {e}")
                try:
                    self.model = VibeVoiceForConditionalGenerationInference.from_pretrained(
                        self.model_path,
                        torch_dtype=torch.bfloat16,
                        device_map='cuda' if torch.cuda.is_available() else 'cpu'
                    )
                    print("使用預設 attention 載入模型成功")
                except Exception as e2:
                    print(f"載入模型失敗: {e2}")
                    raise e2
            
            self.model.eval()
            self.model.set_ddpm_inference_steps(num_steps=10)
            
            # 設定固定語者
            await self._setup_speakers(speaker_voices, speaker_names)
            
            self.is_initialized = True
            print("VibeVoice TTS 初始化完成!")
            
        except Exception as e:
            print(f"TTS 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            self.is_initialized = False

    async def _download_model(self, model_name: str):
        """下載 VibeVoice 模型"""
        try:
            if os.path.exists(self.model_path) and os.listdir(self.model_path):
                print("VibeVoice 模型已存在，跳過下載")
                return
            
            print(f"正在下載 VibeVoice 模型: {model_name}")
            snapshot_download(
                repo_id=model_name,
                local_dir=self.model_path,
                local_dir_use_symlinks=False
            )
            print("VibeVoice 模型下載完成!")
            
        except Exception as e:
            print(f"模型下載失敗: {e}")
            raise

    async def _setup_speakers(self, speaker_voices: Optional[List[str]], speaker_names: Optional[List[str]]):
        """設定語者音檔並預加載"""
        if speaker_voices and all(os.path.exists(path) for path in speaker_voices):
            # 使用自訂語者音檔
            for i, voice_path in enumerate(speaker_voices):
                speaker_id = f"custom_{i}"
                speaker_name = speaker_names[i] if speaker_names and i < len(speaker_names) else f"Speaker{i+1}"
                await self._add_speaker(speaker_id, speaker_name, voice_path)
            print(f"載入自訂語者: {len(speaker_voices)} 個")
        else:
            # 使用預設語者音檔
            await self._setup_default_voices()

    async def _setup_default_voices(self):
        """設定並預加載預設語者音檔"""
        # 使用指定的單一語者音檔
        default_voice_path = os.path.abspath("./voices/zh-Xinran_woman.wav")
        
        if os.path.exists(default_voice_path):
            await self._add_speaker("default", "zh-Xinran_woman", default_voice_path)
            print(f"載入預設語者: zh-Xinran_woman")
        else:
            print(f"警告: 找不到指定的語者音檔: {default_voice_path}")
            # 備用方案：尋找 voices 目錄中的所有 .wav 檔案
            if os.path.exists(self.voices_dir):
                voice_files = [f for f in os.listdir(self.voices_dir) if f.endswith('.wav')]
                for i, voice_file in enumerate(voice_files[:3]):  # 最多載入3個語者
                    voice_path = os.path.abspath(os.path.join(self.voices_dir, voice_file))
                    speaker_name = os.path.splitext(voice_file)[0]
                    await self._add_speaker(f"backup_{i}", speaker_name, voice_path)
                print(f"載入備用語者: {len(voice_files)} 個")
            else:
                print("警告: voices 目錄不存在，無語者音檔可用")

    async def _add_speaker(self, speaker_id: str, speaker_name: str, voice_path: str):
        """添加並預處理語者音檔"""
        if not os.path.exists(voice_path):
            raise Exception(f"語者音檔不存在: {voice_path}")
        
        voice_path = os.path.abspath(voice_path)
        self.speakers[speaker_id] = {
            "name": speaker_name,
            "path": voice_path,
            "processed": False
        }
        
        # 預處理語者音檔（這裡可以加入語者特徵提取等預處理步驟）
        # 目前只是標記為已處理，實際處理在合成時進行
        self.speakers[speaker_id]["processed"] = True
        print(f"  預加載語者: {speaker_name} ({os.path.basename(voice_path)})")

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
        return self.is_initialized and self.model is not None

    async def save_temp_audio(self, audio_data: bytes, prefix: str = "temp") -> str:
        """儲存暫存音檔"""
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.wav"
        file_path = os.path.join(self.uploads_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(audio_data)
        
        return file_path

    async def synthesize(self, text: str, speaker_voice_path: Optional[str] = None, cfg_scale: float = 1.0, save_file: bool = False) -> bytes:
        """合成語音
        
        Args:
            text: 要合成的文字內容
            speaker_voice_path: 指定語者音檔路徑（可選）
            cfg_scale: CFG 尺度參數，控制生成品質
            save_file: 是否保存檔案（用於分段合成避免遞迴）
            
        Returns:
            bytes: 合成的音檔內容
        """
        if not self.is_ready():
            raise Exception("TTS 系統尚未初始化")
        
        # 檢查文字長度，決定是否需要分段處理
        if len(text) > 150 and not save_file:  # save_file=True 表示已經在分段處理中
            print(f"文字較長({len(text)}字元)，啟用分段處理...")
            return await self._synthesize_long_text(text, speaker_voice_path, cfg_scale)
        
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
                    await self._add_speaker(speaker_id, speaker_name, speaker_voice_path)
                    print(f"動態加載語者: {speaker_name}")
                
                speaker_info = self.speakers[speaker_id]
                final_voice_path = speaker_info["path"]
                
            else:
                # 使用預設語者
                default_speaker_id = self.get_default_speaker_id()
                if not default_speaker_id:
                    raise Exception("沒有可用的語者音檔")
                
                speaker_info = self.speakers[default_speaker_id]
                final_voice_path = speaker_info["path"]
            
            print(f"使用語者: {speaker_info['name']} ({final_voice_path})")
            
            # 檢查是否已在快取中
            cache_key = f"{text}:{final_voice_path}:{cfg_scale}"
            if cache_key in self.speaker_cache:
                print("使用快取的語音")
                return self.speaker_cache[cache_key]
            
            # 合成語音
            print(f"合成文本: {text}")
            audio_data = await self._run_synthesis(text, final_voice_path, cfg_scale, save_file=False)
            
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

    async def _run_synthesis(self, text: str, voice_path: str, cfg_scale: float = 1.0, save_file: bool = False) -> bytes:
        """執行實際的語音合成
        
        Args:
            text: 要合成的文字
            voice_path: 語者音檔路徑
            cfg_scale: CFG 尺度參數
            
        Returns:
            bytes: 音檔內容
        """
        # 格式化文字為 VibeVoice 格式
        formatted_text = f"Speaker 1: {text}"
        
        # 根據文字長度動態調整參數
        text_length = len(text)
        if text_length > 100:
            # 長文字使用較保守的參數
            cfg_scale = min(cfg_scale * 0.8, 1.0)
            max_new_tokens = min(text_length * 15, 800)  # 限制最大生成長度
            print(f"長文字模式 - CFG調整為: {cfg_scale:.2f}, Max tokens: {max_new_tokens}")
        elif text_length > 50:
            max_new_tokens = min(text_length * 18, 1000)
            print(f"中等文字模式 - Max tokens: {max_new_tokens}")
        else:
            max_new_tokens = min(text_length * 25, 500)
            print(f"短文字模式 - Max tokens: {max_new_tokens}")
        
        print(f"開始合成語音...")
        print(f"文字長度: {text_length} 字元")
        print(f"文字: {text}")
        print(f"CFG Scale: {cfg_scale}")
        
        # 準備輸入
        inputs = self.processor(
            text=[formatted_text],
            voice_samples=[[voice_path]],
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )
        
        # 移動到 GPU（如果可用）
        if torch.cuda.is_available():
            inputs = {k: v.cuda() if hasattr(v, 'cuda') else v for k, v in inputs.items()}
        
        # 準備生成配置
        generation_config = {
            'do_sample': True,      # 使用採樣而非貪心搜索
            'temperature': 0.1,    # 適中的隨機性
            'top_p': 0.9,          # Nucleus sampling
        }
        
        # 生成語音 - 使用優化的參數
        start_time = time.time()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,  # 限制生成長度
                cfg_scale=cfg_scale,
                tokenizer=self.processor.tokenizer,
                generation_config=generation_config,
                verbose=False,
            )
        
        generation_time = time.time() - start_time
        
        # 檢查輸出
        if outputs.speech_outputs and outputs.speech_outputs[0] is not None:
            # 計算音頻時長
            sample_rate = 24000  # VibeVoice 使用 24kHz
            audio_samples = outputs.speech_outputs[0].shape[-1] if len(outputs.speech_outputs[0].shape) > 0 else len(outputs.speech_outputs[0])
            audio_duration = audio_samples / sample_rate
            rtf = generation_time / audio_duration if audio_duration > 0 else float('inf')
            
            print(f"生成時間: {generation_time:.2f} 秒")
            print(f"音頻時長: {audio_duration:.2f} 秒")
            print(f"RTF: {rtf:.2f}x")
            
            # 準備暫存檔案路徑
            output_filename = f"tts_output_{uuid.uuid4().hex[:8]}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 儲存音頻到暫存檔案
            self.processor.save_audio(
                outputs.speech_outputs[0],
                output_path=output_path,
            )
            
            # 讀取音檔內容為 bytes
            with open(output_path, "rb") as f:
                audio_data = f.read()
            
            # 清理暫存檔案
            if save_file is False:
                try:
                    os.remove(output_path)
                except:
                    pass  # 忽略清理錯誤
            else:
                print(f"TTS 合成完成，音檔路徑: {output_path}")
            print(f"TTS 合成完成，音檔大小: {len(audio_data)} bytes")
            return audio_data
        else:
            raise Exception("TTS 未生成音頻輸出")

    async def synthesize_conversation(self, conversation_text: str, cfg_scale: float = 1.0) -> str:
        """合成對話格式的語音
        
        Args:
            conversation_text: 對話文字，格式如 "Speaker 1: Hello\nSpeaker 2: Hi there"
            cfg_scale: CFG 尺度參數
            
        Returns:
            str: 合成的音檔路徑
        """
        if not self.is_ready():
            raise Exception("TTS 系統尚未初始化")
        
        if not self.default_speaker_voices:
            raise Exception("未設定語者音檔")
        
        try:
            # 準備輸出檔案路徑
            output_filename = f"conversation_{uuid.uuid4().hex[:8]}.wav"
            output_path = os.path.join(self.output_dir, output_filename)
            
            print(f"開始合成對話語音...")
            print(f"對話內容: {conversation_text[:100]}...")
            print(f"使用 {len(self.default_speaker_voices)} 個語者")
            
            # 準備輸入
            inputs = self.processor(
                text=[conversation_text],
                voice_samples=[self.default_speaker_voices],
                padding=True,
                return_tensors="pt",
                return_attention_mask=True,
            )
            
            # 生成語音
            start_time = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=None,
                    cfg_scale=cfg_scale,
                    tokenizer=self.processor.tokenizer,
                    generation_config={'do_sample': False},
                    verbose=False,
                )
            
            generation_time = time.time() - start_time
            
            # 檢查輸出並儲存
            if outputs.speech_outputs and outputs.speech_outputs[0] is not None:
                # 計算音頻時長
                sample_rate = 24000
                audio_samples = outputs.speech_outputs[0].shape[-1] if len(outputs.speech_outputs[0].shape) > 0 else len(outputs.speech_outputs[0])
                audio_duration = audio_samples / sample_rate
                rtf = generation_time / audio_duration if audio_duration > 0 else float('inf')
                
                print(f"生成時間: {generation_time:.2f} 秒")
                print(f"音頻時長: {audio_duration:.2f} 秒")
                print(f"RTF: {rtf:.2f}x")
                
                # 儲存音頻
                self.processor.save_audio(
                    outputs.speech_outputs[0],
                    output_path=output_path,
                )
                
                print(f"對話合成完成: {output_path}")
                return output_path
            else:
                raise Exception("TTS 未生成音頻輸出")
        
        except Exception as e:
            print(f"對話合成錯誤: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"對話合成失敗: {str(e)}")

    async def set_speaker_voices(self, speaker_voices: List[str], speaker_names: Optional[List[str]] = None):
        """動態設定語者音檔
        
        Args:
            speaker_voices: 語者音檔路徑列表
            speaker_names: 語者名稱列表（可選）
        """
        if not all(os.path.exists(path) for path in speaker_voices):
            raise Exception("部分語者音檔不存在")
        
        # 清空現有語者
        self.speakers.clear()
        self.speaker_cache.clear()
        
        # 添加新語者
        for i, voice_path in enumerate(speaker_voices):
            speaker_id = f"user_defined_{i}"
            speaker_name = speaker_names[i] if speaker_names and i < len(speaker_names) else f"Speaker{i+1}"
            await self._add_speaker(speaker_id, speaker_name, voice_path)
        
        print(f"已更新語者音檔: {len(speaker_voices)} 個語者")

    async def _synthesize_long_text(self, text: str, speaker_voice_path: Optional[str], cfg_scale: float) -> bytes:
        """處理長文字的分段合成
        
        Args:
            text: 長文字內容
            speaker_voice_path: 語者音檔路徑
            cfg_scale: CFG 參數
            
        Returns:
            bytes: 合併後的音檔內容
        """
        import re
        
        # 按標點符號分段，但保持合理長度
        sentences = re.split(r'[。！？.!?]\s*', text)
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果當前段落加上這句話不會太長，就合併
            if len(current_segment + sentence) < 100:
                current_segment += sentence + "。"
            else:
                if current_segment:
                    segments.append(current_segment.rstrip("。"))
                current_segment = sentence + "。"
        
        # 處理最後一段
        if current_segment:
            segments.append(current_segment.rstrip("。"))
        
        print(f"文字分為 {len(segments)} 段處理")
        
        # 為每段合成音檔
        audio_segments = []
        for i, segment in enumerate(segments):
            print(f"處理第 {i+1}/{len(segments)} 段: {segment[:30]}...")
            # 使用 save_file=True 避免遞迴分段
            audio_data = await self.synthesize(segment, speaker_voice_path, cfg_scale * 0.9, save_file=True)
            audio_segments.append(audio_data)
        
        # 合併音檔段落
        return await self._merge_audio_segments(audio_segments)

    async def _merge_audio_segments(self, audio_segments: List[bytes]) -> bytes:
        """合併多個音檔段落
        
        Args:
            audio_segments: 音檔段落的 bytes 列表
            
        Returns:
            bytes: 合併後的音檔內容
        """
        import wave
        import io
        import tempfile
        
        if not audio_segments:
            raise Exception("沒有音檔段落可合併")
        
        if len(audio_segments) == 1:
            return audio_segments[0]
        
        try:
            # 創建暫存檔案來處理音檔合併
            merged_audio = io.BytesIO()
            
            # 讀取第一個音檔來設定參數
            first_audio = io.BytesIO(audio_segments[0])
            with wave.open(first_audio, 'rb') as first_wave:
                params = first_wave.getparams()
                
                # 創建輸出音檔
                with wave.open(merged_audio, 'wb') as output_wave:
                    output_wave.setparams(params)
                    
                    # 寫入第一個音檔
                    first_audio.seek(0)
                    with wave.open(first_audio, 'rb') as wave_file:
                        output_wave.writeframes(wave_file.readframes(wave_file.getnframes()))
                    
                    # 寫入其他音檔（跳過 WAV 檔頭）
                    for audio_data in audio_segments[1:]:
                        audio_io = io.BytesIO(audio_data)
                        with wave.open(audio_io, 'rb') as wave_file:
                            # 添加短暫的靜音間隔 (0.2秒)
                            silence_frames = int(params.framerate * 0.2)
                            silence_data = b'\x00' * (silence_frames * params.sampwidth * params.nchannels)
                            output_wave.writeframes(silence_data)
                            
                            # 添加音檔內容
                            output_wave.writeframes(wave_file.readframes(wave_file.getnframes()))
            
            merged_audio.seek(0)
            result = merged_audio.read()
            print(f"成功合併 {len(audio_segments)} 個音檔段落，總大小: {len(result)} bytes")
            return result
            
        except Exception as e:
            print(f"音檔合併失敗: {e}")
            # 如果合併失敗，返回第一個段落
            return audio_segments[0]

    def get_speaker_info(self) -> dict:
        """取得語者資訊"""
        speakers = []
        for speaker_id, info in self.speakers.items():
            speakers.append({
                "id": speaker_id,
                "name": info["name"],
                "voice_path": info["path"],
                "processed": info["processed"]
            })
        
        return {
            "speakers": speakers,
            "total_speakers": len(self.speakers),
            "cache_size": len(self.speaker_cache),
            "default_speaker_id": self.get_default_speaker_id()
        }

# 測試腳本
if __name__ == "__main__":
    import asyncio
    
    async def test_tts():
        tts_service = TTSVibeService()
        
        # 初始化 (使用較小的 1.5B 模型測試)
        await tts_service.initialize(model_name="microsoft/VibeVoice-1.5B")
        
        if not tts_service.is_ready():
            print("TTS 系統未準備好，無法進行測試")
            return
        
        print(f"語者資訊: {tts_service.get_speaker_info()}")
        
        # 測試單句合成
        test_text = "你要不要聽聽看你在說什麼"
        print(f"正在合成語音: {test_text}")
        
        try:
            audio_data = await tts_service.synthesize(test_text, save_file=True)
            print(f"語音合成成功，音檔大小: {len(audio_data)} bytes")
            
            # 測試使用指定語者
            voice_path = "./voices/zh-Novem_man.wav"
            if os.path.exists(voice_path):
                audio_data2 = await tts_service.synthesize(test_text, speaker_voice_path=voice_path, save_file=True)
                print(f"指定語者合成成功，音檔大小: {len(audio_data2)} bytes")
            
        except Exception as e:
            print(f"語音合成失敗: {e}")
    
    asyncio.run(test_tts())
