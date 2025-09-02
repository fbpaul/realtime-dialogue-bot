#!/usr/bin/env python3
"""
啟動腳本 - 根據配置文件啟動 API 服務器
"""
import uvicorn
import argparse
import os
import sys

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import config

def main():
    parser = argparse.ArgumentParser(description="Realtime Dialogue Bot API Server")
    parser.add_argument("--config", "-c", default="config.yaml", help="配置文件路徑")
    parser.add_argument("--host", default=None, help="服務器主機地址")
    parser.add_argument("--port", type=int, default=None, help="服務器端口")
    parser.add_argument("--reload", action="store_true", help="啟用自動重載")
    parser.add_argument("--debug", action="store_true", help="啟用調試模式")
    
    args = parser.parse_args()
    
    # 重新載入配置（如果指定了不同的配置文件）
    if args.config != "config.yaml":
        global config
        from app.config import Config
        config = Config(args.config)
    
    # 從配置文件或命令行參數獲取服務器設定
    api_config = config.get_api_config()
    host = args.host or api_config.get("host", "0.0.0.0")
    port = args.port or api_config.get("port", 8000)
    
    print("=" * 50)
    print("🚀 Realtime Dialogue Bot API Server")
    print("=" * 50)
    print(f"配置文件: {args.config}")
    print(f"服務地址: http://{host}:{port}")
    print(f"TTS 提供者: {config.get_tts_provider()}")
    print(f"啟用的服務:")
    print(f"  - STT: {'✅' if config.is_service_enabled('stt') else '❌'}")
    print(f"  - TTS: {'✅' if config.is_service_enabled('tts') else '❌'}")
    print(f"  - Chat: {'✅' if config.is_service_enabled('chat') else '❌'}")
    print("=" * 50)
    
    # 啟動服務器
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=args.reload or args.debug,
        log_level="debug" if args.debug else "info"
    )

if __name__ == "__main__":
    main()
