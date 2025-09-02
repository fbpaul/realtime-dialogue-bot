# 🎙️ Realtime Dialogue Bot

結合 STT（語音轉文字）、TTS（文字轉語音）與 LLM（大型語言模型），實現即時的語音對話機器人系統。

![聊天界面展示](assets/chat_demo.png)

## ✨ 主要功能

- 🎤 **即時語音識別**：支持高精度的中文語音轉文字
- 🧠 **智能對話**：整合大型語言模型，提供自然流暢的對話體驗
- 🔊 **多引擎語音合成**：支持 BreezyVoice、VibeVoice、IndexTTS 三種 TTS 引擎
- 💻 **現代化 UI**：Vue.js 前端，響應式設計，支持桌面和移動端
- ⚡ **高性能優化**：CUDA 加速、模型緩存、混合精度推論

## 🏗️ 系統架構

### 後端 (FastAPI)
```
backend/
├── app/
│   ├── main.py              # FastAPI 主應用
│   ├── config.py            # 配置管理
│   ├── stt.py              # 語音轉文字服務
│   ├── tts_breezy.py       # BreezyVoice TTS
│   ├── tts_vibe.py         # VibeVoice TTS  
│   ├── tts_index.py        # IndexTTS
│   └── chat.py             # LLM 聊天服務
├── config.yaml             # 服務配置文件
├── models/                 # 模型檔案目錄
├── outputs/                # 生成的音頻輸出
└── voices/                 # 語者音檔庫
```

### 前端 (Vue.js)
```
frontend/
├── src/
│   ├── components/
│   │   └── VoiceChat.vue   # 主聊天介面
│   ├── App.vue
│   └── main.js
├── package.json
└── vite.config.js
```

## 🚀 快速開始

### 環境要求
- Python 3.8+
- Node.js 16+
- CUDA 11.8+ (推薦使用 GPU)
- Docker & Podman (容器化部署)

### 1. Clone 專案
```bash
git clone https://github.com/fbpaul/realtime-dialogue-bot.git
cd realtime-dialogue-bot
```

### 2. 後端設置

#### 使用 Docker 部署 (推薦)
```bash
cd backend
# 啟動所有服務
bash start-with-setup.sh
```

#### 手動安裝
```bash
cd backend
# 安裝依賴
pip install -r requirements.txt

# 下載模型檔案
# STT: faster-whisper-large-v3-turbo
# LLM: Qwen2.5-1.5B
# TTS: BreezyVoice-300M, VibeVoice, IndexTTS-1.5

# 啟動服務
python -m app.main
```

### 3. 前端設置

#### 使用 Docker
```bash
cd frontend
bash start-frontend-docker.sh
```

#### 手動安裝
```bash
cd frontend
npm install
npm run dev
```

### 4. 訪問應用
- 前端界面: http://localhost:3000
- 後端 API: http://localhost:8000
- API 文檔: http://localhost:8000/docs

## ⚙️ 配置說明

### 核心配置 (`backend/config.yaml`)

```yaml
# TTS 引擎選擇
tts:
  provider: "index"  # 可選: "breezy", "vibe", "index"
  
  # CUDA 設備分配
  breezy:
    device: "cuda:1"
  vibe:
    device: "cuda:1" 
  index:
    device: "cuda:1"

# STT 配置
stt:
  device: "cuda:0"
  model: "large-v3-turbo"

# LLM 配置  
chat:
  device: "cuda:0"
  use_llm_tools: true
  llm_tools_model: "Qwen2.5-32B-Instruct-GPTQ-Int4"
```

### 設備資源分配
- **STT + LLM**: CUDA:0
- **TTS 引擎**: CUDA:1
- **記憶體優化**: 模型緩存、混合精度、並行處理

## 📊 性能優化

### TTS 引擎比較
| 引擎 | 速度 | 音質 | 語者支持 | 中文表現 |
|------|------|------|----------|----------|
| **BreezyVoice** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 自定義語者 | 優秀 |
| **VibeVoice** | ⭐⭐⭐ | ⭐⭐⭐⭐ | 多語言支持 | 良好 |
| **IndexTTS** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 克隆語者 | 優秀 |

### 性能指標
- **STT 延遲**: ~500-800ms
- **LLM 響應**: ~600-900ms  
- **TTS 合成**: ~2-7s (取決於引擎和文字長度)
- **端到端延遲**: ~3-8s

## 🎯 API 接口

### 主要端點

```bash
# 語音轉文字
POST /stt
Content-Type: multipart/form-data

# 文字對話 (包含 TTS)
POST /text_chat
{
  "message": "你好，今天天氣如何？"
}

# 完整語音對話流程
POST /conversation
Content-Type: multipart/form-data

# 服務健康檢查
GET /health/{service}  # stt, llm, tts
```

### 回應格式
```json
{
  "success": true,
  "response": "今天天氣很不錯！陽光明媚，溫度適宜。",
  "audio_url": "/audio/response_12345.wav",
  "processing_times": {
    "llm_time": 687,
    "tts_time": 5739,
    "total_time": 6427
  }
}
```

## 🛠️ 開發指南

### 新增 TTS 引擎
1. 繼承 `TTSBaseService` 類別
2. 實現 `initialize()` 和 `synthesize()` 方法
3. 在 `config.yaml` 中添加配置
4. 在 `main.py` 中註冊引擎

### 自定義語者
```bash
# 添加新語者到 voices/ 目錄
cp your_voice.wav backend/voices/zh-CustomSpeaker.wav

# 更新配置文件指向新語者
```

### 測試工具
```bash
# 測試 TTS 引擎
python test_indextts_return_type.py

# 性能比較
python tts_comparison.py

# 組件測試  
python test_components.py
```

## 📋 部署選項

### 1. Docker Compose (推薦)
```bash
# 一鍵啟動前後端
docker-compose up -d
```

### 2. 雲端部署
- 支持 AWS, GCP, Azure
- 建議使用 GPU 實例 (T4, V100, A100)
- 至少 16GB RAM, 50GB 儲存空間

## 📄 授權協議

MIT License


## 📞 聯絡方式

- 專案維護者: fbpaul
- GitHub Issues: [提交問題](https://github.com/fbpaul/realtime-dialogue-bot/issues)
- 技術討論: [Discussions](https://github.com/fbpaul/realtime-dialogue-bot/discussions)

---

⭐ 如果這個專案對您有幫助，請給我們一個星星！