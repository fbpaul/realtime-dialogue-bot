#!/bin/bash

echo "🚀 啟動 Realtime Dialogue 前端 (Docker 版本)..."

# 檢查是否已有容器運行
if [ "$(docker ps -q -f name=realtime-dialogue-frontend)" ]; then
    echo "⚠️  容器已在運行，正在停止..."
    docker stop realtime-dialogue-frontend
    docker rm realtime-dialogue-frontend
fi

# 啟動 Docker 容器
echo "🐳 啟動 Docker 容器..."
docker run -d \
    --name realtime-dialogue-frontend \
    -p 8946:8946 \
    -v /etc/localtime:/etc/localtime:ro \
    -v /data/paul.fc.tsai_data/realtime-dialogue/frontend:/app \
    --workdir /app \
    --restart unless-stopped \
    node:22.15.1 \
    tail -f /dev/null

# 等待容器啟動
echo "⏱️  等待容器啟動..."
sleep 3

# 檢查容器狀態
if [ ! "$(docker ps -q -f name=realtime-dialogue-frontend)" ]; then
    echo "❌ 容器啟動失敗"
    exit 1
fi

echo "✅ 容器已啟動，現在進入容器執行前端設置..."

# 進入容器並執行前端設置
docker exec realtime-dialogue-frontend bash -c "
    echo '🔧 安裝 npm 依賴...'
    npm install
    
    echo '🔍 檢查後端服務狀態...'
    if curl -s http://10.204.245.170:8945/health > /dev/null 2>&1; then
        echo '✅ 後端服務運行正常'
    else
        echo '⚠️  警告: 後端服務似乎未運行'
    fi
    
    echo '🎨 啟動前端開發服務器...'
    echo '📡 前端地址: http://10.204.245.170:8946'
    echo '🔗 後端代理: http://10.204.245.170:8945'
    
    npm run dev -- --host 0.0.0.0 --port 8946
"
