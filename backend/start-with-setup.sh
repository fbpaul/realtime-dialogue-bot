#!/bin/bash

# 複製 llm_tools 到後端目錄
echo "正在複製 llm_tools..."
cp -r ../repo_ref/llm_tools /data/paul.fc.tsai_data/realtime-dialogue/backend/

# 建置並啟動服務
echo "正在建置 Podman 映像..."
cd /data/paul.fc.tsai_data/realtime-dialogue/backend
podman build -t realtime-dialogue-backend .

# 建立必要的目錄
mkdir -p uploads outputs

# 執行容器
echo "正在啟動容器..."
podman run -d \
  --name realtime-dialogue-backend \
  -p 8945:8000 \
  -v $(pwd)/uploads:/app/uploads:Z \
  -v $(pwd)/outputs:/app/outputs:Z \
  -v $(pwd)/llm_tools:/app/llm_tools:Z \
  -e PYTHONUTF8=1 \
  --restart unless-stopped \
  realtime-dialogue-backend

# 等待服務啟動
echo "等待服務啟動中..."
sleep 20

# 檢查容器狀態
echo "檢查容器狀態..."
podman ps --filter name=realtime-dialogue-backend

# 檢查健康狀態
echo "檢查 API 健康狀態..."
curl -s http://10.204.245.170:8945/health | python -m json.tool || echo "服務尚未完全啟動，請稍等..."

echo ""
echo "後端服務已啟動！"
echo "API 文件: http://10.204.245.170:8945/docs"
echo "健康檢查: http://10.204.245.170:8945/health"
echo ""
echo "查看日誌: podman logs -f realtime-dialogue-backend"
echo "停止服務: podman stop realtime-dialogue-backend"
echo "移除容器: podman rm realtime-dialogue-backend"
