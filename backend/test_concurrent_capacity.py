#!/usr/bin/env python3
"""
併發能力測試腳本
測試 LLM、STT、TTS API 的併發處理能力
"""

import asyncio
import aiohttp
import time
import json
import sys
import psutil
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict, Tuple

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConcurrentAPITester:
    def __init__(self, base_url: str = "http://localhost:8945"):
        self.base_url = base_url
        self.results = {
            'llm': [],
            'tts': [],
            'stt': []
        }
        
    async def test_llm_endpoint(self, session: aiohttp.ClientSession, text: str) -> Dict:
        """測試 LLM API"""
        start_time = time.time()
        try:
            data = aiohttp.FormData()
            data.add_field('text', text)
            
            async with session.post(f"{self.base_url}/chat", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()
                    return {
                        'success': True,
                        'response_time': end_time - start_time,
                        'response_length': len(result.get('response', '')),
                        'error': None
                    }
                else:
                    return {
                        'success': False,
                        'response_time': time.time() - start_time,
                        'error': f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    async def test_tts_endpoint(self, session: aiohttp.ClientSession, text: str) -> Dict:
        """測試 TTS API"""
        start_time = time.time()
        try:
            payload = {
                "text": text,
                "speaker_voice_path": None,
                "cfg_scale": 1.0
            }
            
            async with session.post(
                f"{self.base_url}/tts", 
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    end_time = time.time()
                    return {
                        'success': True,
                        'response_time': end_time - start_time,
                        'audio_size': len(audio_data),
                        'error': None
                    }
                else:
                    return {
                        'success': False,
                        'response_time': time.time() - start_time,
                        'error': f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    async def test_stt_endpoint(self, session: aiohttp.ClientSession, audio_file: str) -> Dict:
        """測試 STT API"""
        start_time = time.time()
        try:
            # 使用測試音檔
            audio_path = Path(audio_file)
            if not audio_path.exists():
                return {
                    'success': False,
                    'response_time': 0,
                    'error': f"Audio file not found: {audio_file}"
                }
            
            data = aiohttp.FormData()
            data.add_field('file', 
                          open(audio_path, 'rb'), 
                          filename=audio_path.name,
                          content_type='audio/wav')
            
            async with session.post(f"{self.base_url}/stt", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()
                    return {
                        'success': True,
                        'response_time': end_time - start_time,
                        'transcription_length': len(result.get('transcription', '')),
                        'error': None
                    }
                else:
                    return {
                        'success': False,
                        'response_time': time.time() - start_time,
                        'error': f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    async def run_concurrent_test(self, 
                                 endpoint: str, 
                                 concurrent_users: int, 
                                 requests_per_user: int = 1) -> List[Dict]:
        """執行併發測試"""
        logger.info(f"測試 {endpoint} - {concurrent_users} 個併發用戶，每用戶 {requests_per_user} 個請求")
        
        # 測試用的文字和音檔
        test_text = "你好，這是一個測試語音合成的文字，用來評估系統的併發處理能力。"
        test_audio = "./local_voice/zh-Paul_man.wav"  # 使用現有的測試音檔
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300)  # 5分鐘超時
        ) as session:
            tasks = []
            
            for user_id in range(concurrent_users):
                for req_id in range(requests_per_user):
                    if endpoint == 'llm':
                        task = self.test_llm_endpoint(session, f"{test_text} (用戶{user_id}-請求{req_id})")
                    elif endpoint == 'tts':
                        task = self.test_tts_endpoint(session, f"{test_text} (用戶{user_id}-請求{req_id})")
                    elif endpoint == 'stt':
                        task = self.test_stt_endpoint(session, test_audio)
                    
                    tasks.append(task)
            
            # 執行所有任務
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # 處理結果
            successful_results = []
            failed_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_results.append({'error': str(result), 'success': False})
                elif result.get('success', False):
                    successful_results.append(result)
                else:
                    failed_results.append(result)
            
            logger.info(f"{endpoint} 測試完成:")
            logger.info(f"  總時間: {total_time:.2f}s")
            logger.info(f"  成功: {len(successful_results)}/{len(tasks)}")
            logger.info(f"  失敗: {len(failed_results)}/{len(tasks)}")
            
            if successful_results:
                avg_response_time = np.mean([r['response_time'] for r in successful_results])
                max_response_time = np.max([r['response_time'] for r in successful_results])
                min_response_time = np.min([r['response_time'] for r in successful_results])
                
                logger.info(f"  平均響應時間: {avg_response_time:.2f}s")
                logger.info(f"  最大響應時間: {max_response_time:.2f}s")
                logger.info(f"  最小響應時間: {min_response_time:.2f}s")
                logger.info(f"  吞吐量: {len(successful_results)/total_time:.2f} 請求/秒")
            
            return successful_results, failed_results, total_time
    
    def get_system_resources(self) -> Dict:
        """獲取系統資源使用情況"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        result = {
            'cpu_percent': cpu_percent,
            'memory_total_gb': memory.total / (1024**3),
            'memory_used_gb': memory.used / (1024**3),
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3)
        }
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                result.update({
                    'gpu_memory_used_gb': gpu.memoryUsed / 1024,
                    'gpu_memory_total_gb': gpu.memoryTotal / 1024,
                    'gpu_memory_percent': (gpu.memoryUsed / gpu.memoryTotal) * 100,
                    'gpu_utilization': gpu.load * 100
                })
        except ImportError:
            pass
        
        return result
    
    async def capacity_test(self):
        """執行完整的容量測試"""
        logger.info("開始 API 併發容量測試")
        logger.info("=" * 60)
        
        # 測試不同的併發用戶數
        concurrent_levels = [1, 2, 5, 10, 15, 20, 25, 30]
        
        results_summary = {
            'llm': {},
            'tts': {},
            'stt': {},
            'system_resources': {}
        }
        
        for endpoint in ['llm', 'tts', 'stt']:
            logger.info(f"\n測試 {endpoint.upper()} API")
            logger.info("-" * 40)
            
            for concurrent_users in concurrent_levels:
                # 記錄測試前的系統資源
                resources_before = self.get_system_resources()
                
                try:
                    successful, failed, total_time = await self.run_concurrent_test(
                        endpoint, concurrent_users, 1
                    )
                    
                    # 記錄測試後的系統資源
                    resources_after = self.get_system_resources()
                    
                    success_rate = len(successful) / concurrent_users if concurrent_users > 0 else 0
                    throughput = len(successful) / total_time if total_time > 0 else 0
                    avg_response_time = np.mean([r['response_time'] for r in successful]) if successful else 0
                    
                    results_summary[endpoint][concurrent_users] = {
                        'success_rate': success_rate,
                        'throughput': throughput,
                        'avg_response_time': avg_response_time,
                        'total_requests': concurrent_users,
                        'successful_requests': len(successful),
                        'failed_requests': len(failed),
                        'total_time': total_time,
                        'resources_before': resources_before,
                        'resources_after': resources_after
                    }
                    
                    # 如果成功率低於 80%，停止增加併發數
                    if success_rate < 0.8:
                        logger.warning(f"{endpoint} 在 {concurrent_users} 併發用戶時成功率低於 80%，停止測試")
                        break
                    
                    # 等待系統恢復
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"測試 {endpoint} 時發生錯誤: {e}")
                    break
        
        # 生成報告
        self.generate_report(results_summary)
        
        return results_summary
    
    def generate_report(self, results: Dict):
        """生成容量測試報告"""
        logger.info("\n" + "=" * 60)
        logger.info("容量測試報告")
        logger.info("=" * 60)
        
        for endpoint, data in results.items():
            if endpoint == 'system_resources':
                continue
                
            logger.info(f"\n{endpoint.upper()} API 測試結果:")
            logger.info("-" * 30)
            
            max_concurrent = 0
            best_throughput = 0
            
            for concurrent_users, metrics in data.items():
                success_rate = metrics['success_rate'] * 100
                throughput = metrics['throughput']
                avg_time = metrics['avg_response_time']
                
                logger.info(f"併發用戶: {concurrent_users:2d} | "
                          f"成功率: {success_rate:5.1f}% | "
                          f"吞吐量: {throughput:5.2f} req/s | "
                          f"平均響應: {avg_time:5.2f}s")
                
                if success_rate >= 80:  # 成功率 >= 80% 才算可用
                    max_concurrent = concurrent_users
                    best_throughput = max(best_throughput, throughput)
            
            logger.info(f"\n{endpoint.upper()} 建議最大併發用戶數: {max_concurrent}")
            logger.info(f"{endpoint.upper()} 最佳吞吐量: {best_throughput:.2f} 請求/秒")

async def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8945"
    
    logger.info(f"測試 API 服務: {base_url}")
    
    tester = ConcurrentAPITester(base_url)
    results = await tester.capacity_test()
    
    # 保存結果到文件
    output_file = "concurrent_capacity_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"\n測試結果已保存到: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
