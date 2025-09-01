#!/bin/bash

# 測試後端 API 的腳本

API_BASE="http://10.204.245.170:8945"

echo "=== 測試後端 API ==="

# 1. 健康檢查
echo "1. 測試健康檢查..."
curl -s "$API_BASE/health" | python -m json.tool

echo -e "\n"

# 2. 測試根路徑
echo "2. 測試根路徑..."
curl -s "$API_BASE/" | python -m json.tool

echo -e "\n"

# 3. 測試聊天 API
echo "3. 測試聊天 API..."
curl -s -X POST "$API_BASE/chat" \
  -F "text=你好，我想測試一下聊天功能" | python -m json.tool

echo -e "\n"

# 4. 測試 TTS API (簡單文字)
echo "4. 測試 TTS API..."
curl -s -X POST "$API_BASE/tts" \
  -F "text=你好，這是語音合成測試" \
  --output test_tts_output.wav

if [ -f "test_tts_output.wav" ]; then
    echo "TTS 輸出檔案已產生: test_tts_output.wav"
    ls -la test_tts_output.wav
else
    echo "TTS 測試失敗"
fi

echo -e "\n"

# 5. 查看容器日誌
echo "5. 查看容器日誌 (最後 20 行)..."
podman logs --tail 20 realtime-dialogue-backend

echo -e "\n=== 測試完成 ==="
