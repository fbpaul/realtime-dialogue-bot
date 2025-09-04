# 🎤 Realtime Dialogue Frontend

即時語音對話系統的前端界面，使用 Vue 3 + Vite 構建。

## ✨ 功能特色

- 🎤 **語音錄製**：一鍵錄音，實時語音輸入
- 🤖 **智能對話**：與 AI 助理進行自然語言交流
- 🔊 **語音合成**：高品質的中文語音輸出
- 📱 **響應式設計**：支援各種設備和螢幕尺寸
- 🎨 **現代化 UI**：美觀簡潔的使用者介面

## 🛠 技術棧

- **框架**: Vue 3 (Composition API)
- **建構工具**: Vite
- **樣式**: CSS3 + Flexbox
- **音訊處理**: Web Audio API + MediaRecorder
- **HTTP 客戶端**: Fetch API

## 🚀 快速開始

### 方式一：本地運行（需要本機安裝 Node.js）
```bash
# 給腳本執行權限
chmod +x start-frontend.sh

# 啟動前端
./start-frontend.sh
```

### 方式二：Docker 直接運行
```bash
# 給腳本執行權限
chmod +x start-frontend-docker.sh

# 啟動前端容器並執行
./start-frontend-docker.sh
```

### 方式三：使用 Docker Compose
```bash
# 給腳本執行權限
chmod +x start-frontend-compose.sh

# 啟動服務
./start-frontend-compose.sh
```

### 手動進入 Docker 容器
如果需要手動操作：
```bash
# 啟動容器
docker-compose up -d

# 進入容器
docker-compose exec realtime-dialogue-frontend bash

# 在容器內安裝依賴
npm install

# 在容器內啟動開發服務器
npm run dev -- --host 0.0.0.0 --port 8946
```

## 🌐 存取位址

- **前端界面**: http://10.204.245.170:8946
- **後端 API**: http://10.204.245.170:8945

## 📁 專案結構

```
frontend/
├── src/
│   ├── components/          # Vue 組件
│   ├── assets/              # 靜態資源
│   ├── App.vue              # 主應用組件
│   └── main.js              # 應用入口
├── docker-compose.yml       # Docker Compose 配置
├── package.json             # 專案配置
├── vite.config.js          # Vite 配置
├── start-frontend.sh        # 本地啟動腳本
├── start-frontend-docker.sh # Docker 啟動腳本
└── start-frontend-compose.sh # Docker Compose 啟動腳本
```

## 🔧 開發說明

### 本地開發環境要求
- Node.js >= 16.0.0
- npm >= 7.0.0

### 可用的 npm 指令
```bash
npm install        # 安裝依賴
npm run dev        # 啟動開發服務器
npm run build      # 建構生產版本
npm run preview    # 預覽生產版本
```

### Docker 環境
- Docker >= 20.0.0
- Docker Compose >= 2.0.0

## 📜 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](../LICENSE) 檔案

## 👥 開發團隊

- **主要開發者**: paul.fc.tsai
- **專案維護**: paul.fc.tsai