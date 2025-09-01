#!/usr/bin/env python3
"""
測試 TTS 優化效果
"""

import requests
import json
import time
import os

# API 基礎 URL
BASE_URL = "http://10.204.245.170:8945"

def test_tts_optimization():
    """測試 TTS 優化效果"""
    print("🔍 測試 TTS 優化效果...")
    
    # 測試用例
    test_cases = [
        {
            "name": "短文字",
            "text": "你好，這是一個簡短的測試。",
            "expected_time": 5.0
        },
        {
            "name": "中等文字", 
            "text": "這是一個中等長度的測試文字，用來檢驗TTS系統的處理效能。我們期望看到更快的處理速度和更好的品質。",
            "expected_time": 10.0
        },
        {
            "name": "長文字",
            "text": "好呀！你想聊些什麼有趣的事情呢？是最新鮮的趣聞、搞笑的段子還是令人驚奇的小知識？告訴我你最感興趣的方向吧！我可以分享科技新發現、歷史冷知識、或者一些日常生活中的小妙招。比如說，你知道嗎？章魚有三顆心臟，而且牠們的血液是藍色的！還有，蜜蜂在飛行時翅膀每秒鐘震動約230次，這就是為什麼我們能聽到嗡嗡聲。",
            "expected_time": 25.0
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 測試 {i}: {test_case['name']}")
        print(f"   文字長度: {len(test_case['text'])} 字元")
        print(f"   預期時間: < {test_case['expected_time']} 秒")
        
        try:
            data = {
                "text": test_case["text"],
                "cfg_scale": 1.0
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/tts", json=data, timeout=120)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                audio_data = response.content
                file_size = len(audio_data)
                
                # 儲存測試結果
                filename = f"optimized_tts_{test_case['name']}_{int(time.time())}.wav"
                with open(filename, 'wb') as f:
                    f.write(audio_data)
                
                # 判斷是否達到預期
                performance_ok = response_time <= test_case['expected_time']
                status = "✅" if performance_ok else "⚠️"
                
                print(f"   {status} 處理時間: {response_time:.2f} 秒")
                print(f"   📁 檔案大小: {file_size:,} bytes")
                print(f"   💾 儲存為: {filename}")
                
                results.append({
                    "test": test_case['name'],
                    "text_length": len(test_case['text']),
                    "processing_time": response_time,
                    "expected_time": test_case['expected_time'],
                    "performance_ok": performance_ok,
                    "file_size": file_size
                })
                
            else:
                print(f"   ❌ 失敗: {response.status_code} - {response.text}")
                results.append({
                    "test": test_case['name'],
                    "text_length": len(test_case['text']),
                    "processing_time": None,
                    "expected_time": test_case['expected_time'],
                    "performance_ok": False,
                    "error": f"{response.status_code} - {response.text}"
                })
                
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
            results.append({
                "test": test_case['name'],
                "text_length": len(test_case['text']),
                "processing_time": None,
                "expected_time": test_case['expected_time'],
                "performance_ok": False,
                "error": str(e)
            })
    
    # 總結報告
    print(f"\n📋 優化效果總結:")
    print("=" * 60)
    
    successful_tests = [r for r in results if r['processing_time'] is not None]
    performance_good = [r for r in successful_tests if r['performance_ok']]
    
    if successful_tests:
        avg_time = sum(r['processing_time'] for r in successful_tests) / len(successful_tests)
        print(f"✅ 成功測試: {len(successful_tests)}/{len(results)}")
        print(f"🚀 效能良好: {len(performance_good)}/{len(successful_tests)}")
        print(f"⏱️  平均處理時間: {avg_time:.2f} 秒")
        
        # 詳細結果
        for result in results:
            if result['processing_time']:
                ratio = result['processing_time'] / result['expected_time']
                status = "🟢" if ratio <= 1.0 else "🟡" if ratio <= 1.5 else "🔴"
                print(f"   {status} {result['test']}: {result['processing_time']:.2f}s ({result['text_length']}字)")
    else:
        print("❌ 所有測試都失敗了")
    
    return results

def test_cache_effect():
    """測試快取效果"""
    print(f"\n🗃️  測試快取效果...")
    
    test_text = "測試快取效果的文字內容。"
    
    # 第一次請求（無快取）
    print("第一次請求（建立快取）:")
    start_time = time.time()
    response1 = requests.post(f"{BASE_URL}/tts", json={"text": test_text, "cfg_scale": 1.0})
    time1 = time.time() - start_time
    print(f"  時間: {time1:.2f} 秒")
    
    # 第二次請求（應該使用快取）
    print("第二次請求（使用快取）:")
    start_time = time.time()
    response2 = requests.post(f"{BASE_URL}/tts", json={"text": test_text, "cfg_scale": 1.0})
    time2 = time.time() - start_time
    print(f"  時間: {time2:.2f} 秒")
    
    if response1.status_code == 200 and response2.status_code == 200:
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"🚀 快取加速比: {speedup:.1f}x")
        return True
    else:
        print("❌ 快取測試失敗")
        return False

if __name__ == "__main__":
    print("🔧 TTS 優化效果測試")
    print("=" * 60)
    
    # 健康檢查
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服務運行正常")
        else:
            print("❌ 服務不可用")
            exit(1)
    except:
        print("❌ 無法連接服務")
        exit(1)
    
    # 執行優化測試
    optimization_results = test_tts_optimization()
    
    # 執行快取測試
    cache_results = test_cache_effect()
    
    print(f"\n✅ 測試完成！")
