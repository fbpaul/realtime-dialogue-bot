#!/usr/bin/env python3
"""
簡單的 API 測試腳本
"""

import requests
import json
import os
import time
import numpy as np
import wave

# API 基礎 URL
BASE_URL = "http://10.204.245.170:8945"

def test_health():
    """測試健康檢查端點"""
    print("🔍 測試健康檢查...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康檢查通過: {data}")
            return True
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康檢查錯誤: {e}")
        return False

def create_test_audio():
    """創建一個簡單的測試音頻文件（正弦波）"""
    print("🎵 創建測試音頻文件...")
    
    # 音頻參數
    sample_rate = 16000
    duration = 3  # 3秒
    frequency = 440  # A4 音符
    
    # 生成正弦波
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # 保存為 WAV 文件
    output_path = "test_audio.wav"
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # 單聲道
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"✅ 測試音頻文件已創建: {output_path}")
    return output_path

def test_stt(audio_file_path):
    """測試 STT (語音轉文字) 功能"""
    print("\n🎤 測試 STT (語音轉文字)...")
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'file': ('test.wav', audio_file, 'audio/wav')}
            
            print("📤 上傳音頻文件...")
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/stt", 
                files=files,
                timeout=30
            )
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ STT 轉錄成功:")
                print(f"   文字: {result.get('text', 'N/A')}")
                print(f"   成功: {result.get('success', 'N/A')}")
                print(f"   響應時間: {response_time:.2f}秒")
                return result.get('text', '')
            else:
                print(f"❌ STT 轉錄失敗: {response.status_code}")
                print(f"   錯誤: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ STT 測試錯誤: {e}")
        return None

def test_llm_chat(message="你好，請自我介紹一下"):
    """測試 LLM 對話功能"""
    print(f"\n🤖 測試 LLM 對話...")
    print(f"   輸入: {message}")
    
    try:
        data = {
            "text": message
        }
        
        print("💭 生成回應中...")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat", 
            data=data,
            timeout=60
        )
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            reply = result.get('response', '')
            print(f"✅ LLM 回應成功:")
            print(f"   回應: {reply}")
            print(f"   響應時間: {response_time:.2f}秒")
            return reply
        else:
            print(f"❌ LLM 回應失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ LLM 測試錯誤: {e}")
        return None

def test_tts(text="這是一個測試的語音合成，使用 VibeVoice 模型", speaker_voice_path=None):
    """測試 TTS (文字轉語音) 功能"""
    print(f"\n🔊 測試 TTS (文字轉語音)...")
    print(f"   文字: {text}")
    if speaker_voice_path:
        print(f"   指定語者音檔: {speaker_voice_path}")
    
    try:
        # 使用 JSON 格式而不是表單數據
        data = {
            "text": text,
            "cfg_scale": 1.0
        }
        
        # 如果有指定語者音檔路徑，加入參數
        if speaker_voice_path:
            data["speaker_voice_path"] = speaker_voice_path
        
        print("🎵 合成語音中...")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/tts", 
            json=data,  # 使用 json= 而不是 data=
            timeout=60
        )
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            # 保存音頻文件
            timestamp = int(time.time())
            filename_suffix = "_custom" if speaker_voice_path else "_default"
            output_filename = f"tts_output_{timestamp}{filename_suffix}.wav"
            with open(output_filename, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_filename)
            print(f"✅ TTS 合成成功:")
            print(f"   輸出文件: {output_filename}")
            print(f"   文件大小: {file_size:,} bytes")
            print(f"   響應時間: {response_time:.2f}秒")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            return output_filename
        else:
            print(f"❌ TTS 合成失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ TTS 測試錯誤: {e}")
        return None

def test_conversation_flow():
    """測試完整對話流程"""
    print(f"\n🔄 測試完整對話流程...")
    
    try:
        # 記錄整體開始時間
        total_start_time = time.time()
        
        # 1. 檢查是否有指定音頻文件，否則創建測試音頻
        if os.path.exists("./開心.wav"):
            audio_file = "./開心.wav"
            print(f"使用現有音頻文件: {audio_file}")
        else:
            audio_file = create_test_audio()
        
        # 2. STT: 音頻轉文字
        transcribed_text = test_stt(audio_file)
        if not transcribed_text:
            # 如果 STT 失敗，使用預設文字
            transcribed_text = "你好，請告訴我今天的天氣如何？"
            print(f"⚠️  STT 失敗，使用預設文字: {transcribed_text}")
        
        # 3. LLM: 生成回應
        llm_response = test_llm_chat(transcribed_text)
        if not llm_response:
            print("❌ 對話流程中斷：LLM 回應失敗")
            return False
            
        # 4. TTS: 文字轉語音
        audio_output = test_tts(llm_response)
        if not audio_output:
            print("❌ 對話流程中斷：TTS 合成失敗")
            return False
        
        # 計算總時間
        total_time = time.time() - total_start_time
            
        print(f"\n✅ 完整對話流程測試成功！")
        print(f"   轉錄文字: {transcribed_text}")
        print(f"   LLM 回應: {llm_response}")
        print(f"   輸出音頻: {audio_output}")
        print(f"   🕐 總響應時間: {total_time:.2f}秒")
        
        # 清理創建的測試文件（不刪除用戶指定的文件）
        if audio_file == "test_audio.wav":
            try:
                os.remove(audio_file)
                print(f"🗑️  清理測試文件: {audio_file}")
            except:
                pass
            
        return True
        
    except Exception as e:
        print(f"❌ 對話流程測試錯誤: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🚀 開始 API 功能測試")
    print("=" * 60)
    
    # 1. 健康檢查
    if not test_health():
        print("❌ 服務不可用，結束測試")
        return
    
    print("\n" + "=" * 60)
    
    # 2. 個別功能測試
    print("📋 個別功能測試:")
    
    # LLM 測試
    test_llm_chat("你好，請自我介紹一下")
    
    # TTS 測試 - 使用預設語者
    test_tts("您好，我是語音助理，很高興為您服務！")
    
    # TTS 測試 - 使用指定語者音檔 (如果存在)
    custom_voice_path = "/app/voices/zh-Xinran_woman.wav"
    # custom_voice_path = "./backend/voices/zh-Novem_man.wav"
    if os.path.exists(custom_voice_path):
        print(f"\n🎤 測試指定語者音檔功能:")
        test_tts("這是使用指定語者音檔的測試。", speaker_voice_path=custom_voice_path)
    else:
        print(f"\n⚠️  指定語者音檔不存在: {custom_voice_path}")
    
    print("\n" + "=" * 60)
    
    # 3. 完整流程測試
    print("🔄 完整對話流程測試:")
    test_conversation_flow()
    
    print("\n" + "=" * 60)
    print("✅ 測試完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
