#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
電話銷售對話模擬腳本
模擬兩個人的電話銷售對話，測試 LLM、TTS、STT 的完整流程
"""

import asyncio
import aiohttp
import json
import time
import os
import uuid
from datetime import datetime
from typing import List, Dict, Tuple
import difflib
import statistics
import argparse

# API 配置
API_HOST = "http://10.204.245.170:8945"

class PhoneSalesSimulator:
    def __init__(self, api_host: str = API_HOST):
        self.api_host = api_host
        self.session = None
        self.conversation_id = str(uuid.uuid4())
        self.conversation_history = []  # 新增對話歷史記錄
        self.metrics = {
            'llm_times': [],
            'tts_times': [],
            'stt_times': [],
            'accuracies': [],
            'llm_speeds': [],  # 新增 LLM 速度指標
            'tts_speeds': [],  # 新增 TTS 速度指標
            'stt_speeds': [],  # 新增 STT 速度指標
            'llm_char_counts': [],  # 新增字數統計
            'stt_char_counts': [],  # 新增字數統計
            'total_rounds': 0
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_api_connection(self) -> bool:
        """測試 API 連接"""
        try:
            async with self.session.get(f"{self.api_host}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ API 連接成功: {health_data}")
                    return True
                else:
                    print(f"❌ API 健康檢查失敗: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API 連接失敗: {e}")
            return False
    
    def generate_sales_dialogue_prompts(self) -> List[Dict[str, str]]:
        """生成電話銷售對話的提示詞"""
        return [
            # 第1輪 - 銷售員開場
            {
                "role": "salesperson",
                "prompt": "你是一位專業的保險銷售員，名叫小王，正在進行電話銷售。請用友善但專業的語調打電話給客戶，介紹自己和你們公司的醫療保險產品。記住這是對話的開始，要自然地開場。回覆要簡潔自然，大約30-50字。"
            },
            # 第2輪 - 客戶回應  
            {
                "role": "customer",
                "prompt": "你是一位30歲的上班族李先生，剛接到保險銷售電話。你對醫療保險有些基本了解，但對電話銷售有些戒心。請根據銷售員的介紹給出自然的回應，可以表現出一些興趣但也有疑慮。回覆要簡潔，大約20-40字。"
            },
            # 第3輪 - 銷售員介紹產品
            {
                "role": "salesperson", 
                "prompt": "根據客戶的回應，請介紹你們醫療保險產品的主要優勢，如保障範圍廣、理賠快速、保費合理等。要針對客戶的疑慮給出回應，語調要有說服力但不強硬。回覆大約40-60字。"
            },
            # 第4輪 - 客戶詢問細節
            {
                "role": "customer",
                "prompt": "你對產品有些興趣，但作為謹慎的消費者，想了解更多具體細節，如每月保費多少、理賠條件、等待期等。請根據之前的對話內容提出具體問題。回覆大約30-50字。"
            },
            # 第5輪 - 銷售員解答疑問
            {
                "role": "salesperson",
                "prompt": "客戶詢問了具體的產品細節，請提供專業的保費資訊和理賠條件說明。要針對客戶提出的具體問題給出回答，展現專業知識並建立信任。回覆大約50-70字。"
            },
            # 第6輪 - 客戶考慮中
            {
                "role": "customer", 
                "prompt": "聽了銷售員的詳細介紹，你覺得產品還不錯，但需要時間考慮，想跟配偶討論一下。請根據前面的對話表現出認真考慮但不急於決定的態度。回覆大約30-40字。"
            },
            # 第7輪 - 銷售員促進成交
            {
                "role": "salesperson",
                "prompt": "客戶需要考慮時間，這很正常。請提供一些促進成交的誘因，如本月限時優惠、免費健康檢查等額外服務，但要保持專業不能太推銷。要尊重客戶需要討論的想法。回覆大約40-60字。"
            },
            # 第8輪 - 客戶提出異議
            {
                "role": "customer",
                "prompt": "你對優惠有興趣，但還是有些擔心，想比較其他保險公司的類似產品，或者想了解是否有更便宜的方案。表現出精明消費者的態度，根據對話內容提出合理疑問。回覆大約30-50字。"
            },
            # 第9輪 - 銷售員處理異議
            {
                "role": "salesperson",
                "prompt": "客戶想比較其他產品這很正常，請專業地強調你們公司的獨特優勢和競爭力，比如服務品質、理賠速度、網點覆蓋等。要尊重客戶的決定過程，不要過於強勢。回覆大約50-60字。"
            },
            # 第10輪 - 客戶最終決定
            {
                "role": "customer",
                "prompt": "經過這次詳細的對話，你決定先不立即購買，但對銷售員小王的專業態度印象很好。你願意留下聯絡方式，表示可能會在未來一周內給出最終決定。回覆大約30-40字。"
            }
        ]
    
    async def call_llm_api(self, prompt: str, role: str) -> Tuple[str, float]:
        """調用 LLM API，包含對話歷史"""
        start_time = time.time()
        
        try:
            # 構建包含歷史的完整提示
            full_prompt = self.build_prompt_with_history(prompt, role)
            
            data = aiohttp.FormData()
            data.add_field('text', full_prompt)
            data.add_field('conversation_id', self.conversation_id)
            
            async with self.session.post(f"{self.api_host}/chat", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    llm_response = result['response']
                    llm_time = time.time() - start_time
                    
                    # 將回應添加到歷史記錄
                    self.conversation_history.append({
                        "role": role,
                        "content": llm_response
                    })
                    
                    return llm_response, llm_time
                else:
                    error_text = await response.text()
                    raise Exception(f"LLM API 錯誤 {response.status}: {error_text}")
                    
        except Exception as e:
            print(f"❌ LLM API 調用失敗: {e}")
            default_response = f"抱歉，我現在無法回應。"
            # 即使失敗也記錄到歷史，保持對話連貫性
            self.conversation_history.append({
                "role": role,
                "content": default_response
            })
            return default_response, time.time() - start_time
    
    def build_prompt_with_history(self, current_prompt: str, current_role: str) -> str:
        """構建包含對話歷史的完整提示"""
        if not self.conversation_history:
            # 第一輪對話，無歷史記錄
            return f"角色設定：{current_prompt}\n\n請直接開始對話，不要說「作為...」這樣的開場白。"
        
        # 構建歷史對話記錄
        history_text = "對話歷史記錄：\n"
        for i, msg in enumerate(self.conversation_history, 1):
            role_name = "銷售員" if msg["role"] == "salesperson" else "客戶"
            history_text += f"{i}. {role_name}：{msg['content']}\n"
        
        # 當前角色指示
        current_role_name = "銷售員" if current_role == "salesperson" else "客戶" 
        
        full_prompt = f"""{history_text}

角色指示：
你現在是{current_role_name}，請根據以上對話歷史和以下角色設定進行回應：

{current_prompt}

請確保回應：
1. 與之前的對話內容保持連貫
2. 符合角色設定
3. 自然流暢，不要重複之前說過的話
4. 直接回應，不要說「作為...」這樣的開場白

請直接開始你的回應："""
        
        return full_prompt
    
    def reset_conversation(self):
        """重置對話歷史，開始新的對話"""
        self.conversation_history = []
        self.conversation_id = str(uuid.uuid4())
        print(f"🔄 對話已重置，新的對話ID: {self.conversation_id}")
    
    def get_conversation_summary(self) -> str:
        """獲取對話摘要"""
        if not self.conversation_history:
            return "暫無對話記錄"
        
        summary = f"對話輪次: {len(self.conversation_history)}\n"
        summary += "對話概要:\n"
        for i, msg in enumerate(self.conversation_history, 1):
            role_name = "銷售員" if msg["role"] == "salesperson" else "客戶"
            content_preview = msg['content'][:30] + "..." if len(msg['content']) > 30 else msg['content']
            summary += f"  {i}. {role_name}: {content_preview}\n"
        
        return summary
    
    async def call_tts_api(self, text: str) -> Tuple[bytes, float]:
        """調用 TTS API"""
        start_time = time.time()
        
        try:
            payload = {
                "text": text,
                "speaker_voice_path": None,
                "cfg_scale": 1.0
            }
            
            async with self.session.post(
                f"{self.api_host}/tts", 
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    tts_time = time.time() - start_time
                    return audio_data, tts_time
                else:
                    error_text = await response.text()
                    raise Exception(f"TTS API 錯誤 {response.status}: {error_text}")
                    
        except Exception as e:
            print(f"❌ TTS API 調用失敗: {e}")
            return b"", time.time() - start_time
    
    async def call_stt_api(self, audio_data: bytes) -> Tuple[str, float]:
        """調用 STT API"""
        start_time = time.time()
        
        try:
            data = aiohttp.FormData()
            data.add_field('file', audio_data, filename='audio.wav', content_type='audio/wav')
            
            async with self.session.post(f"{self.api_host}/stt", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    stt_time = time.time() - start_time
                    return result['transcription'], stt_time
                else:
                    error_text = await response.text()
                    raise Exception(f"STT API 錯誤 {response.status}: {error_text}")
                    
        except Exception as e:
            print(f"❌ STT API 調用失敗: {e}")
            return "", time.time() - start_time
    
    def calculate_accuracy(self, original: str, transcribed: str) -> float:
        """計算轉譯準確度 - 使用萊文斯坦距離，先去除標點符號"""
        if not original or not transcribed:
            return 0.0
        
        def remove_punctuation(text: str) -> str:
            """去除標點符號（包含全形和半形）"""
            import string
            import re
            
            # 半形標點符號
            halfwidth_punctuation = string.punctuation
            
            # 全形標點符號
            fullwidth_punctuation = '！？。，、；：「」『』（）〔〕【】〈〉《》""''…—–－'
            
            # 其他常見標點符號
            other_punctuation = '·•‧°'
            
            # 合併所有標點符號
            all_punctuation = halfwidth_punctuation + fullwidth_punctuation + other_punctuation
            
            # 去除標點符號和空格
            cleaned_text = ''.join(char for char in text if char not in all_punctuation)
            
            # 去除多餘的空白字符
            cleaned_text = re.sub(r'\s+', '', cleaned_text)
            
            return cleaned_text
        
        def levenshtein_distance(s1: str, s2: str) -> int:
            """計算萊文斯坦距離"""
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        # 先去除標點符號
        cleaned_original = remove_punctuation(original).lower()
        cleaned_transcribed = remove_punctuation(transcribed).lower()
        
        # 如果去除標點後都為空，則返回100%準確度
        if not cleaned_original and not cleaned_transcribed:
            return 100.0
        
        # 計算距離
        distance = levenshtein_distance(cleaned_original, cleaned_transcribed)
        max_length = max(len(cleaned_original), len(cleaned_transcribed))
        
        if max_length == 0:
            return 100.0
        
        # 準確度 = (1 - 距離/最大長度) * 100
        accuracy = (1 - distance / max_length) * 100
        return max(0.0, accuracy)
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """計算兩個字符串之間的萊文斯坦距離"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # 計算插入、刪除、替換的成本
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def save_audio_file(self, audio_data: bytes, filename: str) -> str:
        """保存音檔"""
        if not os.path.exists("simulation_outputs"):
            os.makedirs("simulation_outputs")
        
        file_path = os.path.join("simulation_outputs", filename)
        with open(file_path, "wb") as f:
            f.write(audio_data)
        return file_path
    
    async def simulate_phone_sales_round(self, round_num: int, role: str, prompt: str) -> Dict:
        """模擬一輪電話銷售對話"""
        print(f"\n{'='*50}")
        print(f"第 {round_num} 輪對話 - {role}")
        print(f"{'='*50}")
        
        # 顯示對話歷史（從第2輪開始）
        if round_num > 1:
            print(f"📚 對話歷史 ({len(self.conversation_history)} 條記錄):")
            for i, msg in enumerate(self.conversation_history, 1):
                role_name = "銷售員" if msg["role"] == "salesperson" else "客戶"
                print(f"   {i}. {role_name}：{msg['content']}")
            print()
        
        # Step 1: LLM 生成回應
        print(f"🤖 當前角色提示: {prompt[:80]}...")
        llm_response, llm_time = await self.call_llm_api(prompt, role)
        
        # 計算 LLM 字數和速度
        llm_char_count = len(llm_response)
        llm_speed = llm_char_count / llm_time if llm_time > 0 else 0
        
        role_name = "銷售員" if role == "salesperson" else "客戶"
        print(f"💬 {role_name}回應: {llm_response}")
        print(f"⏱️  LLM 處理時間: {llm_time:.3f}s")
        print(f"🚀 LLM 速度: {llm_speed:.1f} 字/秒 ({llm_char_count} 字)")
        
        # Step 2: TTS 轉語音
        print(f"🔊 TTS 轉換中...")
        audio_data, tts_time = await self.call_tts_api(llm_response)
        audio_filename = f"round_{round_num:02d}_{role}_{uuid.uuid4().hex[:8]}.wav"
        
        # 計算 TTS 速度
        tts_speed = llm_char_count / tts_time if tts_time > 0 else 0
        
        if audio_data:
            audio_path = self.save_audio_file(audio_data, audio_filename)
            print(f"🎵 音檔已保存: {audio_path}")
            print(f"⏱️  TTS 處理時間: {tts_time:.3f}s")
            print(f"🚀 TTS 速度: {tts_speed:.1f} 字/秒")
        else:
            print(f"❌ TTS 轉換失敗")
            audio_path = None
        
        # Step 3: STT 轉回文字
        if audio_data:
            print(f"🎤 STT 轉換中...")
            stt_result, stt_time = await self.call_stt_api(audio_data)
            
            # 計算 STT 字數和速度
            stt_char_count = len(stt_result)
            stt_speed = stt_char_count / stt_time if stt_time > 0 else 0
            
            print(f"📝 STT 結果: {stt_result}")
            print(f"⏱️  STT 處理時間: {stt_time:.3f}s")
            print(f"🚀 STT 速度: {stt_speed:.1f} 字/秒 ({stt_char_count} 字)")
            
            # 計算準確度
            accuracy = self.calculate_accuracy(llm_response, stt_result)
            print(f"🎯 轉譯準確度: {accuracy:.2f}%")
        else:
            stt_result = ""
            stt_time = 0
            stt_char_count = 0
            stt_speed = 0
            accuracy = 0
        
        # 記錄指標
        self.metrics['llm_times'].append(llm_time)
        self.metrics['tts_times'].append(tts_time)
        self.metrics['stt_times'].append(stt_time)
        self.metrics['accuracies'].append(accuracy)
        self.metrics['llm_speeds'].append(llm_speed)
        self.metrics['tts_speeds'].append(tts_speed)
        self.metrics['stt_speeds'].append(stt_speed)
        self.metrics['llm_char_counts'].append(llm_char_count)
        self.metrics['stt_char_counts'].append(stt_char_count)
        
        return {
            'round': round_num,
            'role': role,
            'prompt': prompt,
            'llm_response': llm_response,
            'llm_time': llm_time,
            'llm_speed': llm_speed,
            'llm_char_count': llm_char_count,
            'tts_time': tts_time,
            'tts_speed': tts_speed,
            'stt_result': stt_result,
            'stt_time': stt_time,
            'stt_speed': stt_speed,
            'stt_char_count': stt_char_count,
            'accuracy': accuracy,
            'audio_file': audio_filename if audio_data else None,
            'conversation_history_length': len(self.conversation_history)
        }
    
    async def run_simulation(self, rounds: int = 10) -> List[Dict]:
        """運行完整的電話銷售模擬"""
        print(f"🚀 開始電話銷售對話模擬 ({rounds} 輪)")
        print(f"🔗 API 地址: {self.api_host}")
        print(f"💼 對話ID: {self.conversation_id}")
        
        # 測試 API 連接
        if not await self.test_api_connection():
            print("❌ API 連接失敗，無法繼續模擬")
            return []
        
        # 生成對話提示
        prompts = self.generate_sales_dialogue_prompts()[:rounds]
        results = []
        
        start_time = time.time()
        
        # 執行每一輪對話
        for i, prompt_data in enumerate(prompts, 1):
            try:
                result = await self.simulate_phone_sales_round(
                    i, prompt_data['role'], prompt_data['prompt']
                )
                results.append(result)
                
            except Exception as e:
                print(f"❌ 第 {i} 輪對話失敗: {e}")
                continue
        
        total_time = time.time() - start_time
        self.metrics['total_rounds'] = len(results)
        
        # 顯示總結報告
        self.print_summary_report(results, total_time)
        
        return results
    
    def print_summary_report(self, results: List[Dict], total_time: float):
        """打印總結報告"""
        print(f"\n{'='*60}")
        print(f"📊 電話銷售對話模擬總結報告")
        print(f"{'='*60}")
        
        if not results:
            print("❌ 沒有成功完成的對話輪次")
            return
        
        print(f"✅ 完成輪次: {len(results)}")
        print(f"⏱️  總耗時: {total_time:.2f}s")
        print(f"🔄 平均每輪耗時: {total_time/len(results):.2f}s")
        
        # 計算總字數統計
        total_llm_chars = sum(self.metrics['llm_char_counts'])
        total_stt_chars = sum(self.metrics['stt_char_counts'])
        print(f"📝 總生成字數: {total_llm_chars} 字")
        print(f"🎯 總轉譯字數: {total_stt_chars} 字")
        
        # LLM 性能統計
        if self.metrics['llm_times']:
            llm_avg_time = statistics.mean(self.metrics['llm_times'])
            llm_min_time = min(self.metrics['llm_times'])
            llm_max_time = max(self.metrics['llm_times'])
            llm_avg_speed = statistics.mean(self.metrics['llm_speeds'])
            llm_min_speed = min(self.metrics['llm_speeds'])
            llm_max_speed = max(self.metrics['llm_speeds'])
            
            print(f"\n🤖 LLM 性能:")
            print(f"   平均響應時間: {llm_avg_time:.3f}s")
            print(f"   最快響應時間: {llm_min_time:.3f}s")
            print(f"   最慢響應時間: {llm_max_time:.3f}s")
            print(f"   平均生成速度: {llm_avg_speed:.1f} 字/秒")
            print(f"   最快生成速度: {llm_max_speed:.1f} 字/秒")
            print(f"   最慢生成速度: {llm_min_speed:.1f} 字/秒")
        
        # TTS 性能統計
        if self.metrics['tts_times']:
            tts_avg_time = statistics.mean(self.metrics['tts_times'])
            tts_min_time = min(self.metrics['tts_times'])
            tts_max_time = max(self.metrics['tts_times'])
            tts_avg_speed = statistics.mean(self.metrics['tts_speeds'])
            tts_min_speed = min(self.metrics['tts_speeds'])
            tts_max_speed = max(self.metrics['tts_speeds'])
            
            print(f"\n🔊 TTS 性能:")
            print(f"   平均轉換時間: {tts_avg_time:.3f}s")
            print(f"   最快轉換時間: {tts_min_time:.3f}s")
            print(f"   最慢轉換時間: {tts_max_time:.3f}s")
            print(f"   平均轉換速度: {tts_avg_speed:.1f} 字/秒")
            print(f"   最快轉換速度: {tts_max_speed:.1f} 字/秒")
            print(f"   最慢轉換速度: {tts_min_speed:.1f} 字/秒")
        
        # STT 性能統計
        if self.metrics['stt_times']:
            stt_avg_time = statistics.mean(self.metrics['stt_times'])
            stt_min_time = min(self.metrics['stt_times'])
            stt_max_time = max(self.metrics['stt_times'])
            stt_avg_speed = statistics.mean(self.metrics['stt_speeds'])
            stt_min_speed = min(self.metrics['stt_speeds'])
            stt_max_speed = max(self.metrics['stt_speeds'])
            
            print(f"\n🎤 STT 性能:")
            print(f"   平均轉換時間: {stt_avg_time:.3f}s")
            print(f"   最快轉換時間: {stt_min_time:.3f}s")
            print(f"   最慢轉換時間: {stt_max_time:.3f}s")
            print(f"   平均識別速度: {stt_avg_speed:.1f} 字/秒")
            print(f"   最快識別速度: {stt_max_speed:.1f} 字/秒")
            print(f"   最慢識別速度: {stt_min_speed:.1f} 字/秒")
        
        # 準確度統計
        if self.metrics['accuracies']:
            acc_avg = statistics.mean(self.metrics['accuracies'])
            acc_min = min(self.metrics['accuracies'])
            acc_max = max(self.metrics['accuracies'])
            print(f"\n🎯 轉譯準確度:")
            print(f"   平均準確度: {acc_avg:.2f}%")
            print(f"   最低準確度: {acc_min:.2f}%")
            print(f"   最高準確度: {acc_max:.2f}%")
        
        # 整體效能指標
        self.print_overall_metrics(results, total_time)
        
        # 顯示完整對話記錄
        if self.conversation_history:
            print(f"\n💬 完整對話記錄:")
            print("-" * 50)
            for i, msg in enumerate(self.conversation_history, 1):
                role_name = "銷售員小王" if msg["role"] == "salesperson" else "客戶李先生"
                print(f"{i:2d}. {role_name}：{msg['content']}")
        
        # 保存詳細結果到文件
        self.save_detailed_results(results)
    
    def print_overall_metrics(self, results: List[Dict], total_time: float):
        """計算並顯示整體效能指標"""
        print(f"\n{'='*60}")
        print(f"🏆 整體效能指標 (Performance Dashboard)")
        print(f"{'='*60}")
        
        if not results:
            return
        
        # 基本統計
        total_llm_chars = sum(self.metrics['llm_char_counts'])
        total_stt_chars = sum(self.metrics['stt_char_counts'])
        avg_accuracy = statistics.mean(self.metrics['accuracies']) if self.metrics['accuracies'] else 0
        
        # 整體速度 (字/秒)
        overall_llm_speed = total_llm_chars / sum(self.metrics['llm_times']) if sum(self.metrics['llm_times']) > 0 else 0
        overall_tts_speed = total_llm_chars / sum(self.metrics['tts_times']) if sum(self.metrics['tts_times']) > 0 else 0
        overall_stt_speed = total_stt_chars / sum(self.metrics['stt_times']) if sum(self.metrics['stt_times']) > 0 else 0
        
        # 端到端延遲 (每輪的總處理時間)
        end_to_end_times = []
        for result in results:
            total_round_time = result['llm_time'] + result['tts_time'] + result['stt_time']
            end_to_end_times.append(total_round_time)
        
        avg_end_to_end = statistics.mean(end_to_end_times) if end_to_end_times else 0
        min_end_to_end = min(end_to_end_times) if end_to_end_times else 0
        max_end_to_end = max(end_to_end_times) if end_to_end_times else 0
        
        # 計算效能評分 (0-100分)
        def calculate_performance_score():
            # 速度分數 (30%)
            speed_score = 0
            if overall_llm_speed > 0:
                # LLM速度評分：>50字/秒=滿分，<10字/秒=0分
                llm_score = min(100, max(0, (overall_llm_speed - 10) / 40 * 100))
                # TTS速度評分：>30字/秒=滿分，<5字/秒=0分  
                tts_score = min(100, max(0, (overall_tts_speed - 5) / 25 * 100))
                # STT速度評分：>40字/秒=滿分，<8字/秒=0分
                stt_score = min(100, max(0, (overall_stt_speed - 8) / 32 * 100))
                speed_score = (llm_score + tts_score + stt_score) / 3
            
            # 準確度分數 (40%)
            accuracy_score = avg_accuracy
            
            # 穩定性分數 (30%) - 基於標準差，越小越好
            stability_score = 0
            if len(end_to_end_times) > 1:
                std_dev = statistics.stdev(end_to_end_times)
                cv = std_dev / avg_end_to_end if avg_end_to_end > 0 else 0  # 變異係數
                # 變異係數<0.2=滿分，>0.5=0分
                stability_score = min(100, max(0, (0.5 - cv) / 0.3 * 100))
            else:
                stability_score = 100  # 單次測試給滿分
            
            # 總分
            total_score = speed_score * 0.3 + accuracy_score * 0.4 + stability_score * 0.3
            return total_score, speed_score, accuracy_score, stability_score
        
        total_score, speed_score, accuracy_score, stability_score = calculate_performance_score()
        
        print(f"📈 整體表現: {total_score:.1f}/100")
        print()
        print(f"🚀 整體速度指標:")
        print(f"   LLM 整體速度: {overall_llm_speed:.1f} 字/秒")
        print(f"   TTS 整體速度: {overall_tts_speed:.1f} 字/秒") 
        print(f"   STT 整體速度: {overall_stt_speed:.1f} 字/秒")
        print()
        print(f"⏱️  端到端延遲:")
        print(f"   平均處理時間: {avg_end_to_end:.3f}s")
        print(f"   最快處理時間: {min_end_to_end:.3f}s")
        print(f"   最慢處理時間: {max_end_to_end:.3f}s")
        print()
        print(f"📊 評分細項:")
        print(f"   速度評分: {speed_score:.1f}/100 (權重30%)")
        print(f"   準確度評分: {accuracy_score:.1f}/100 (權重40%)")
        print(f"   穩定性評分: {stability_score:.1f}/100 (權重30%)")
        print()
        print(f"🎯 處理效率:")
        print(f"   總字數處理: {total_llm_chars} 字")
        print(f"   平均每秒處理: {total_llm_chars/total_time:.1f} 字/秒")
        print(f"   系統吞吐量: {len(results)/total_time:.2f} 輪/秒")
    
    def save_detailed_results(self, results: List[Dict]):
        """保存詳細結果到JSON文件"""
        if not os.path.exists("simulation_outputs"):
            os.makedirs("simulation_outputs")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_outputs/phone_sales_simulation_{timestamp}.json"
        
        report_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "api_host": self.api_host,
                "conversation_id": self.conversation_id,
                "total_rounds": len(results)
            },
            "conversation_history": self.conversation_history,  # 加入完整對話歷史
            "metrics": self.metrics,
            "results": results
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 詳細結果已保存到: {filename}")

async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="電話銷售對話模擬腳本")
    parser.add_argument("--api-host", default=API_HOST, help="API 主機地址")
    parser.add_argument("--rounds", type=int, default=10, help="對話輪次數量")
    parser.add_argument("--show-history", action="store_true", help="顯示詳細對話歷史")
    
    args = parser.parse_args()
    
    print("🎯 電話銷售對話模擬器 v2.0 (含對話歷史)")
    print("=" * 60)
    print(f"📍 API地址: {args.api_host}")
    print(f"🔢 輪次數量: {args.rounds}")
    print(f"📚 顯示歷史: {'是' if args.show_history else '否'}")
    
    async with PhoneSalesSimulator(args.api_host) as simulator:
        results = await simulator.run_simulation(args.rounds)
        
        if results:
            print(f"\n🎉 模擬完成！共完成 {len(results)} 輪對話")
            
            if args.show_history:
                print(f"\n📋 對話摘要:")
                print(simulator.get_conversation_summary())
        else:
            print(f"\n😞 模擬失敗，請檢查 API 服務是否正常運行")

if __name__ == "__main__":
    asyncio.run(main())

# python phone_sales_simulation.py --rounds 10 --show-history
