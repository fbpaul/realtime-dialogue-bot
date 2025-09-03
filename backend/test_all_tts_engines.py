#!/usr/bin/env python3
"""
修正版全方位 TTS 引擎測試腳本
測試所有 TTS 引擎的語者克隆功能，計算生成時間和 RTF (Real Time Factor)
"""
import asyncio
import os
import sys
import time
import uuid
import wave
import librosa
from typing import Dict, List, Tuple

# 添加 app 目錄到路徑
sys.path.append('./app')

from app.tts_breezy import TTSBreezyService
from app.tts_vibe import TTSVibeService
from app.tts_index import TTSIndexService
from app.tts_spark import TTSSparkService

# 測試配置
TEST_TEXTS = [
    "這是第一段測試文本，用來評估語音合成的基本效果和語者克隆的準確性。",
    "第二段文本比較長一些，包含更多的語音變化和語調轉換，能夠更好地測試TTS引擎的穩定性和自然度表現。",
    "最後這段文本涵蓋了各種語音現象，包括停頓、重音、語氣變化等，是對TTS引擎綜合性能的全面考驗和驗證。"
]

# 選用的語者（確保這些語者檔案存在）
TEST_SPEAKERS = [
    {
        "id": "zh-Novem_man", 
        "name": "Novem男聲", 
        "path": "./voices/zh-Novem_man.wav",
        "prompt_text": "欸這個很有趣耶，趕快跟我說一下吧"  
    },
    {
        "id": "zh-Xinran_woman", 
        "name": "Xinran女聲", 
        "path": "./voices/zh-Xinran_woman.wav",
        "prompt_text": "我喜歡讀村上春樹，他說，如果你愛上了某個星球的一朵花，那麼只要在夜晚仰望星空，就會覺得漫天的繁星就像一朵朵盛開的花。以前我對這句話一知半解，現在好像有點懂了，因為妳我開始留意很多以前不曾關心的事，開始對這個世界有了更多的好奇和善意，你就像那朵獨一無二的花，讓我的整個星空都變得有意義、璀璨又不再孤單。"
    },
    {
        "id": "zh-SparkTTS_man", 
        "name": "SparkTTS男聲", 
        "path": "./voices/zh-SparkTTS_man.wav",
        "prompt_text": "吃燕窩就選燕之屋，本節目由26年專注高品質燕窩的燕之屋冠名播出。豆奶牛奶換著喝，營養更均衡，本節目由豆本豆豆奶特約播出。"
    }
]

class TTSPerformanceTester:
    def __init__(self):
        self.results = {}
        self.output_dir = "./outputs/tts_test_results"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_audio_duration(self, audio_path: str) -> float:
        """計算音頻檔案長度（秒）"""
        try:
            # 使用 librosa 獲取音頻時長
            duration = librosa.get_duration(filename=audio_path)
            return duration
        except:
            try:
                # 備用方法：使用 wave 模組
                with wave.open(audio_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    duration = frames / float(sample_rate)
                    return duration
            except:
                return 0.0
    
    def calculate_rtf(self, synthesis_time: float, audio_duration: float) -> float:
        """計算 RTF (Real Time Factor)"""
        if audio_duration <= 0:
            return float('inf')
        return synthesis_time / audio_duration
    
    def format_time(self, seconds: float) -> str:
        """格式化時間顯示"""
        return f"{seconds:.3f}s"
    
    def format_rtf(self, rtf: float) -> str:
        """格式化 RTF 顯示"""
        if rtf == float('inf'):
            return "∞"
        return f"{rtf:.3f}"
    
    async def test_breezy_tts(self) -> Dict:
        """測試 BreezyVoice TTS"""
        print("\n" + "="*60)
        print("測試 BreezyVoice TTS")
        print("="*60)
        
        try:
            service = TTSBreezyService()
            
            # 初始化
            print("初始化 BreezyVoice...")
            await service.initialize()
            if not service.is_ready():
                print("❌ BreezyVoice 初始化失敗")
                return {"status": "failed", "error": "初始化失敗"}
            
            print("✅ BreezyVoice 初始化成功")
            
            results = {"status": "success", "tests": []}
            
            # 使用可用的語者清單
            speakers_to_test = getattr(self, 'test_speakers', TEST_SPEAKERS)
            
            for i, text in enumerate(TEST_TEXTS):
                for j, speaker in enumerate(speakers_to_test):
                    if not os.path.exists(speaker["path"]):
                        continue
                        
                    test_name = f"Text{i+1}_Speaker{j+1}"
                    print(f"\n測試 {test_name}: {speaker['name']}")
                    print(f"文本: {text[:50]}...")
                    
                    try:
                        start_time = time.time()
                        
                        # BreezyVoice 使用 synthesize 方法
                        audio_data = await service.synthesize(
                            text=text,
                            speaker_voice_path=speaker["path"]
                        )
                        
                        synthesis_time = time.time() - start_time
                        
                        if audio_data:
                            # 手動保存音頻檔案
                            output_filename = f"breezy_output_{uuid.uuid4().hex[:8]}.wav"
                            output_path = os.path.join("./outputs", output_filename)
                            
                            with open(output_path, "wb") as f:
                                f.write(audio_data)
                            
                            if os.path.exists(output_path):
                                audio_duration = self.get_audio_duration(output_path)
                                rtf = self.calculate_rtf(synthesis_time, audio_duration)
                                file_size = len(audio_data)
                                
                                result = {
                                    "test_name": test_name,
                                    "text_length": len(text),
                                    "speaker": speaker["name"],
                                    "synthesis_time": synthesis_time,
                                    "audio_duration": audio_duration,
                                    "rtf": rtf,
                                    "file_size": file_size,
                                    "output_path": output_path,
                                    "success": True
                                }
                                results["tests"].append(result)
                                
                                print(f"✅ 成功 - 合成時間: {self.format_time(synthesis_time)}, "
                                      f"音頻長度: {self.format_time(audio_duration)}, "
                                      f"RTF: {self.format_rtf(rtf)}")
                            else:
                                print(f"❌ 失敗 - 檔案保存失敗")
                                results["tests"].append({
                                    "test_name": test_name,
                                    "success": False,
                                    "error": "檔案保存失敗"
                                })
                        else:
                            print(f"❌ 失敗 - 未生成音頻資料")
                            results["tests"].append({
                                "test_name": test_name,
                                "success": False,
                                "error": "未生成音頻資料"
                            })
                            
                    except Exception as e:
                        print(f"❌ 錯誤: {e}")
                        results["tests"].append({
                            "test_name": test_name,
                            "success": False,
                            "error": str(e)
                        })
            
            # BreezyVoice 沒有 cleanup 方法，直接設為 None
            service.is_initialized = False
            return results
            
        except Exception as e:
            print(f"❌ BreezyVoice 測試失敗: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_vibe_tts(self) -> Dict:
        """測試 VibeVoice TTS"""
        print("\n" + "="*60)
        print("測試 VibeVoice TTS")
        print("="*60)
        
        try:
            service = TTSVibeService()
            
            # 初始化
            print("初始化 VibeVoice...")
            await service.initialize()
            if not service.is_ready():
                print("❌ VibeVoice 初始化失敗")
                return {"status": "failed", "error": "初始化失敗"}
            
            print("✅ VibeVoice 初始化成功")
            
            results = {"status": "success", "tests": []}
            
            # 使用可用的語者清單
            speakers_to_test = getattr(self, 'test_speakers', TEST_SPEAKERS)
            
            for i, text in enumerate(TEST_TEXTS):
                for j, speaker in enumerate(speakers_to_test):
                    if not os.path.exists(speaker["path"]):
                        continue
                        
                    test_name = f"Text{i+1}_Speaker{j+1}"
                    print(f"\n測試 {test_name}: {speaker['name']}")
                    print(f"文本: {text[:50]}...")
                    
                    try:
                        start_time = time.time()
                        
                        # VibeVoice 使用 synthesize 方法
                        audio_data = await service.synthesize(
                            text=text,
                            speaker_voice_path=speaker["path"]
                        )
                        
                        synthesis_time = time.time() - start_time
                        
                        if audio_data:
                            # 手動保存音頻檔案
                            output_filename = f"vibe_output_{uuid.uuid4().hex[:8]}.wav"
                            output_path = os.path.join("./outputs", output_filename)
                            
                            with open(output_path, "wb") as f:
                                f.write(audio_data)
                            
                            if os.path.exists(output_path):
                                audio_duration = self.get_audio_duration(output_path)
                                rtf = self.calculate_rtf(synthesis_time, audio_duration)
                                file_size = len(audio_data)
                                
                                result = {
                                    "test_name": test_name,
                                    "text_length": len(text),
                                    "speaker": speaker["name"],
                                    "synthesis_time": synthesis_time,
                                    "audio_duration": audio_duration,
                                    "rtf": rtf,
                                    "file_size": file_size,
                                    "output_path": output_path,
                                    "success": True
                                }
                                results["tests"].append(result)
                                
                                print(f"✅ 成功 - 合成時間: {self.format_time(synthesis_time)}, "
                                      f"音頻長度: {self.format_time(audio_duration)}, "
                                      f"RTF: {self.format_rtf(rtf)}")
                            else:
                                print(f"❌ 失敗 - 檔案保存失敗")
                                results["tests"].append({
                                    "test_name": test_name,
                                    "success": False,
                                    "error": "檔案保存失敗"
                                })
                        else:
                            print(f"❌ 失敗 - 未生成音頻資料")
                            results["tests"].append({
                                "test_name": test_name,
                                "success": False,
                                "error": "未生成音頻資料"
                            })
                            
                    except Exception as e:
                        print(f"❌ 錯誤: {e}")
                        results["tests"].append({
                            "test_name": test_name,
                            "success": False,
                            "error": str(e)
                        })
            
            # VibeVoice 沒有 cleanup 方法，直接設為 None
            service.is_initialized = False
            return results
            
        except Exception as e:
            print(f"❌ VibeVoice 測試失敗: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_index_tts(self) -> Dict:
        """測試 IndexTTS"""
        print("\n" + "="*60)
        print("測試 IndexTTS")
        print("="*60)
        
        try:
            service = TTSIndexService()
            
            # 初始化
            print("初始化 IndexTTS...")
            success = await service.initialize()
            if not success:
                print("❌ IndexTTS 初始化失敗")
                return {"status": "failed", "error": "初始化失敗"}
            
            print("✅ IndexTTS 初始化成功")
            
            results = {"status": "success", "tests": []}
            
            # 使用可用的語者清單
            speakers_to_test = getattr(self, 'test_speakers', TEST_SPEAKERS)
            
            for i, text in enumerate(TEST_TEXTS):
                for j, speaker in enumerate(speakers_to_test):
                    if not os.path.exists(speaker["path"]):
                        continue
                        
                    test_name = f"Text{i+1}_Speaker{j+1}"
                    print(f"\n測試 {test_name}: {speaker['name']}")
                    print(f"文本: {text[:50]}...")
                    
                    try:
                        start_time = time.time()
                        
                        # 使用語者檔案進行合成
                        output_path = await service.synthesize_to_file(
                            text=text,
                            speaker_voice_path=speaker["path"]
                        )
                        
                        synthesis_time = time.time() - start_time
                        
                        if os.path.exists(output_path):
                            audio_duration = self.get_audio_duration(output_path)
                            rtf = self.calculate_rtf(synthesis_time, audio_duration)
                            file_size = os.path.getsize(output_path)
                            
                            result = {
                                "test_name": test_name,
                                "text_length": len(text),
                                "speaker": speaker["name"],
                                "synthesis_time": synthesis_time,
                                "audio_duration": audio_duration,
                                "rtf": rtf,
                                "file_size": file_size,
                                "output_path": output_path,
                                "success": True
                            }
                            results["tests"].append(result)
                            
                            print(f"✅ 成功 - 合成時間: {self.format_time(synthesis_time)}, "
                                  f"音頻長度: {self.format_time(audio_duration)}, "
                                  f"RTF: {self.format_rtf(rtf)}")
                        else:
                            print(f"❌ 失敗 - 未生成音頻檔案")
                            
                    except Exception as e:
                        print(f"❌ 錯誤: {e}")
                        results["tests"].append({
                            "test_name": test_name,
                            "success": False,
                            "error": str(e)
                        })
            
            service.cleanup()
            return results
            
        except Exception as e:
            print(f"❌ IndexTTS 測試失敗: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_spark_tts(self) -> Dict:
        """測試 Spark-TTS"""
        print("\n" + "="*60)
        print("測試 Spark-TTS")
        print("="*60)
        
        try:
            service = TTSSparkService()
            
            # 初始化
            print("初始化 Spark-TTS...")
            success = await service.initialize()
            if not success:
                print("❌ Spark-TTS 初始化失敗")
                return {"status": "failed", "error": "初始化失敗"}
            
            print("✅ Spark-TTS 初始化成功")
            
            results = {"status": "success", "tests": []}
            
            # 使用可用的語者清單
            speakers_to_test = getattr(self, 'test_speakers', TEST_SPEAKERS)
            
            for i, text in enumerate(TEST_TEXTS):
                for j, speaker in enumerate(speakers_to_test):
                    if not os.path.exists(speaker["path"]):
                        continue
                        
                    test_name = f"Text{i+1}_Speaker{j+1}"
                    print(f"\n測試 {test_name}: {speaker['name']}")
                    print(f"文本: {text[:50]}...")
                    
                    try:
                        start_time = time.time()
                        
                        # 檢查語者是否有轉錄文字，如果沒有則跳過
                        speaker_prompt_text = speaker.get("prompt_text", "")
                        if not speaker_prompt_text:
                            print(f"⚠️  跳過 - 語者 {speaker['name']} 缺少轉錄文字")
                            results["tests"].append({
                                "test_name": test_name,
                                "success": False,
                                "error": "缺少轉錄文字"
                            })
                            continue
                        
                        # 使用語者克隆模式進行合成
                        output_path = await service.synthesize_to_file(
                            text=text,
                            speaker_voice_path=speaker["path"],
                            prompt_text=speaker_prompt_text,  # 使用語者特定的轉錄文字
                            use_voice_cloning=True  # 確保使用語者克隆模式
                        )
                        
                        synthesis_time = time.time() - start_time
                        
                        if os.path.exists(output_path):
                            audio_duration = self.get_audio_duration(output_path)
                            rtf = self.calculate_rtf(synthesis_time, audio_duration)
                            file_size = os.path.getsize(output_path)
                            
                            result = {
                                "test_name": test_name,
                                "text_length": len(text),
                                "speaker": speaker["name"],
                                "synthesis_time": synthesis_time,
                                "audio_duration": audio_duration,
                                "rtf": rtf,
                                "file_size": file_size,
                                "output_path": output_path,
                                "success": True
                            }
                            results["tests"].append(result)
                            
                            print(f"✅ 成功 - 合成時間: {self.format_time(synthesis_time)}, "
                                  f"音頻長度: {self.format_time(audio_duration)}, "
                                  f"RTF: {self.format_rtf(rtf)}")
                        else:
                            print(f"❌ 失敗 - 未生成音頻檔案")
                            
                    except Exception as e:
                        print(f"❌ 錯誤: {e}")
                        results["tests"].append({
                            "test_name": test_name,
                            "success": False,
                            "error": str(e)
                        })
            
            service.cleanup()
            return results
            
        except Exception as e:
            print(f"❌ Spark-TTS 測試失敗: {e}")
            return {"status": "failed", "error": str(e)}
    
    def print_summary(self, all_results: Dict):
        """打印測試總結"""
        print("\n" + "="*80)
        print("測試總結報告")
        print("="*80)
        
        tts_engines = ["BreezyVoice", "VibeVoice", "IndexTTS", "Spark-TTS"]
        
        print(f"\n{'TTS引擎':<15} {'成功/總數':<10} {'平均RTF':<12} {'平均合成時間':<15} {'狀態':<10}")
        print("-" * 70)
        
        for engine_name, results in all_results.items():
            if results["status"] == "failed":
                print(f"{engine_name:<15} {'N/A':<10} {'N/A':<12} {'N/A':<15} {'失敗':<10}")
                continue
            
            successful_tests = [t for t in results["tests"] if t.get("success", False)]
            total_tests = len(results["tests"])
            success_count = len(successful_tests)
            
            if success_count > 0:
                avg_rtf = sum(t["rtf"] for t in successful_tests if t["rtf"] != float('inf')) / len([t for t in successful_tests if t["rtf"] != float('inf')])
                avg_time = sum(t["synthesis_time"] for t in successful_tests) / success_count
                
                print(f"{engine_name:<15} {success_count}/{total_tests:<7} {avg_rtf:<12.3f} {avg_time:<15.3f} {'正常':<10}")
            else:
                print(f"{engine_name:<15} {success_count}/{total_tests:<7} {'N/A':<12} {'N/A':<15} {'異常':<10}")
        
        # 詳細結果
        print(f"\n詳細測試結果:")
        print("-" * 80)
        
        for engine_name, results in all_results.items():
            if results["status"] == "failed":
                print(f"\n{engine_name}: 測試失敗 - {results.get('error', '未知錯誤')}")
                continue
            
            print(f"\n{engine_name}:")
            successful_tests = [t for t in results["tests"] if t.get("success", False)]
            
            if successful_tests:
                for test in successful_tests:
                    print(f"  {test['test_name']}: RTF={self.format_rtf(test['rtf'])}, "
                          f"時間={self.format_time(test['synthesis_time'])}, "
                          f"音頻={self.format_time(test['audio_duration'])}")
            else:
                print(f"  無成功的測試")
    
    async def run_all_tests(self):
        """運行所有 TTS 引擎測試"""
        print("開始全方位 TTS 引擎測試")
        print(f"測試文本數: {len(TEST_TEXTS)}")
        print(f"測試語者數: {len(TEST_SPEAKERS)}")
        print(f"預期測試總數: {len(TEST_TEXTS) * len(TEST_SPEAKERS) * 4} (每引擎)")
        
        # 檢查語者檔案是否存在
        available_speakers = []
        for speaker in TEST_SPEAKERS:
            if os.path.exists(speaker["path"]):
                available_speakers.append(speaker)
                print(f"✅ 語者檔案存在: {speaker['name']}")
            else:
                print(f"❌ 語者檔案不存在: {speaker['name']} - {speaker['path']}")
        
        if not available_speakers:
            print("❌ 沒有可用的語者檔案，測試終止")
            return
        
        # 使用可用語者清單
        self.test_speakers = available_speakers
        
        # 運行各個引擎的測試
        all_results = {}
        
        # 測試 BreezyVoice
        all_results["BreezyVoice"] = await self.test_breezy_tts()
        
        # 測試 VibeVoice  
        all_results["VibeVoice"] = await self.test_vibe_tts()
        
        # 測試 IndexTTS
        all_results["IndexTTS"] = await self.test_index_tts()
        
        # 測試 Spark-TTS
        all_results["Spark-TTS"] = await self.test_spark_tts()
        
        # 打印總結
        self.print_summary(all_results)
        
        return all_results

async def main():
    """主函數"""
    tester = TTSPerformanceTester()
    results = await tester.run_all_tests()
    
    # 可以將結果保存到檔案
    import json
    results_file = "./outputs/tts_test_results_fixed.json"
    
    # 將結果中的不可序列化對象轉換
    serializable_results = {}
    for engine, data in results.items():
        serializable_results[engine] = {
            "status": data["status"],
            "tests": []
        }
        
        if "tests" in data:
            for test in data["tests"]:
                serializable_test = {k: v for k, v in test.items() if k != "output_path"}
                if "rtf" in serializable_test and serializable_test["rtf"] == float('inf'):
                    serializable_test["rtf"] = "infinity"
                serializable_results[engine]["tests"].append(serializable_test)
        
        if "error" in data:
            serializable_results[engine]["error"] = data["error"]
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n測試結果已保存至: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
