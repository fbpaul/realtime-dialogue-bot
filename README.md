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
| **Spark-TTS** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 克隆語者 | 良好 |

### 詳細測試結果

基於標準測試用例的 RTF (Real Time Factor) 性能測試結果：

#### BreezyVoice 測試結果
| 文本 | 語者 | RTF | 合成時間 | 音頻長度 |
|------|------|-----|----------|----------|
| 短文字 | Speaker1 | 2.230 | 22.088s | 9.903s |
| 短文字 | Speaker2 | 2.176 | 42.799s | 19.667s |
| 短文字 | Speaker3 | 3.095 | 19.582s | 6.327s |
| 中等文字 | Speaker1 | 1.569 | 22.710s | 14.478s |
| 中等文字 | Speaker2 | 1.713 | 62.698s | 36.595s |
| 中等文字 | Speaker3 | 2.859 | 23.232s | 8.127s |
| 長文字 | Speaker1 | 1.901 | 28.208s | 14.838s |
| 長文字 | Speaker2 | 1.967 | 81.422s | 41.390s |
| 長文字 | Speaker3 | 2.302 | 21.195s | 9.207s |

#### VibeVoice 測試結果
| 文本 | 語者 | RTF | 合成時間 | 音頻長度 |
|------|------|-----|----------|----------|
| 短文字 | Speaker1 | 1.019 | 7.065s | 6.933s |
| 短文字 | Speaker2 | 0.851 | 6.124s | 7.200s |
| 短文字 | Speaker3 | 0.831 | 5.427s | 6.533s |
| 中等文字 | Speaker1 | 0.820 | 12.906s | 15.733s |
| 中等文字 | Speaker2 | 0.827 | 8.379s | 10.133s |
| 中等文字 | Speaker3 | 0.822 | 8.216s | 10.000s |
| 長文字 | Speaker1 | 0.819 | 10.488s | 12.800s |
| 長文字 | Speaker2 | 0.822 | 9.096s | 11.067s |
| 長文字 | Speaker3 | 0.820 | 9.951s | 12.133s |

#### IndexTTS 測試結果
| 文本 | 語者 | RTF | 合成時間 | 音頻長度 |
|------|------|-----|----------|----------|
| 短文字 | Speaker1 | 0.540 | 4.079s | 7.552s |
| 短文字 | Speaker2 | 0.439 | 3.314s | 7.552s |
| 短文字 | Speaker3 | 0.483 | 3.070s | 6.357s |
| 中等文字 | Speaker1 | 0.444 | 4.541s | 10.240s |
| 中等文字 | Speaker2 | 0.426 | 4.367s | 10.240s |
| 中等文字 | Speaker3 | 0.446 | 4.358s | 9.771s |
| 長文字 | Speaker1 | 0.445 | 4.972s | 11.179s |
| 長文字 | Speaker2 | 0.444 | 4.890s | 11.008s |
| 長文字 | Speaker3 | 0.448 | 4.489s | 10.027s |

#### Spark-TTS 測試結果
| 文本 | 語者 | RTF | 合成時間 | 音頻長度 |
|------|------|-----|----------|----------|
| 短文字 | Speaker1 | 1.160 | 9.302s | 8.020s |
| 短文字 | Speaker3 | 1.032 | 5.245s | 5.080s |
| 中等文字 | Speaker1 | 1.004 | 10.484s | 10.440s |
| 中等文字 | Speaker3 | 1.009 | 8.414s | 8.340s |
| 長文字 | Speaker1 | 1.000 | 10.476s | 10.480s |
| 長文字 | Speaker3 | 1.002 | 8.680s | 8.660s |

#### 性能總結
- **IndexTTS**: 最快的合成速度，平均 RTF ≈ 0.45，適合即時應用，但中國口音較重
- **VibeVoice**: RTF ≈ 0.82，如果克隆語者音檔品質不佳，無法生成好的聲音
- **Spark-TTS**: 近即時性能，RTF ≈ 1.0，接近實時合成，中國口音重
- **BreezyVoice**: RTF ≈ 1.5-3.0，較低的中國口音，但會跳針，導致速度評估起來很慢 (莫名生成太長的語音)

*RTF (Real Time Factor): 值越小表示合成速度越快。RTF=1.0 表示實時合成速度*

### 系統性能指標
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

# 文字轉語音（支援語者克隆）
POST /tts
{
  "text": "要合成的文字",
  "speaker_voice_path": "./voices/zh-CustomSpeaker.wav",  # 可選，語者克隆音檔路徑
  "cfg_scale": 1.0  # 可選，僅 VibeVoice 使用
}

# 文字對話（包含 TTS 和語者克隆）
POST /text_chat
{
  "message": "你好，今天天氣如何？",
  "speaker_voice_path": "./voices/zh-CustomSpeaker.wav",  # 可選，語者克隆
  "speaker_id": "zh-Novem_man",  # 可選，使用預設語者 ID
  "use_voice_cloning": true,  # 可選，是否使用語者克隆（Spark-TTS）
  "gender": "female",  # 可選，性別設定（Spark-TTS 語音控制模式）
  "pitch": "high",     # 可選，音調設定（Spark-TTS 語音控制模式）
  "speed": "moderate"  # 可選，語速設定（Spark-TTS 語音控制模式）
}

# 完整語音對話流程（支援語者克隆）
POST /conversation
Content-Type: multipart/form-data
- audio_file: 用戶語音檔案
- conversation_id: 對話 ID（可選）
- speaker_voice_path: 語者克隆音檔路徑（可選）
- speaker_id: 預設語者 ID（可選）

# 獲取可用語者列表
GET /speakers

# 服務健康檢查
GET /health/{service}  # stt, llm, tts
```

### 語者克隆使用示例

```bash
# 1. 獲取可用語者列表
curl -X GET "http://localhost:8000/speakers"

# 2. 使用語者克隆進行 TTS
curl -X POST "http://localhost:8000/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，這是語者克隆測試",
    "speaker_voice_path": "./voices/zh-Novem_man.wav"
  }' \
  --output cloned_voice.wav

# 3. 文字對話 + 語者克隆
curl -X POST "http://localhost:8000/text_chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "告訴我關於人工智慧的歷史",
    "speaker_voice_path": "./voices/zh-CustomSpeaker.wav",
    "use_voice_cloning": true
  }'

# 4. Spark-TTS 語音控制模式
curl -X POST "http://localhost:8000/text_chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "這是語音控制模式測試",
    "use_voice_cloning": false,
    "gender": "female",
    "pitch": "high",
    "speed": "moderate"
  }'
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

# 通過 API 使用自定義語者進行語者克隆
curl -X POST "http://localhost:8000/text_chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "使用自定義語者的測試",
    "speaker_voice_path": "./voices/zh-CustomSpeaker.wav"
  }'
```

### 語者克隆最佳實踐
1. **語者音檔品質**: 使用清晰、無背景噪音的 WAV 格式音檔
2. **音檔長度**: 建議 3-10 秒，包含完整句子
3. **語言一致性**: 語者音檔語言應與合成文字語言一致
4. **引擎選擇**: 
   - IndexTTS: 速度最快，適合即時應用
   - VibeVoice: 品質較好但對音檔品質要求高
   - Spark-TTS: 支援語者克隆和語音控制兩種模式
   - BreezyVoice: 品質最佳但速度較慢

### 測試工具
```bash
# 測試語者克隆功能
python test_voice_cloning_api.py

# 測試 TTS 引擎性能比較
python test_all_tts_engines.py

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