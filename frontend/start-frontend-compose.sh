#!/bin/bash

echo "🚀 啟動 Realtime Dialogue 前端 (podman-compose 版本)..."

# 停止現有服務
echo "🛑 停止現有服務..."
podman-compose down

# 啟動服務
echo "🐳 啟動 podman Compose 服務..."
podman-compose up -d

# 等待容器啟動
echo "⏱️  等待容器啟動..."
sleep 5

# 檢查容器狀態
if [ ! "$(podman ps -q -f name=realtime-dialogue-frontend)" ]; then
    echo "❌ 容器啟動失敗"
    podman-compose logs
    exit 1
fi

echo "✅ 容器已啟動，現在進入容器執行前端設置..."

# 進入容器並執行前端設置
podman-compose exec realtime-dialogue-frontend bash -c "
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
