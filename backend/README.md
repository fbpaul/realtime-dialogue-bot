# 🎙️ Realtime Dialogue Backend

基於 GPU 加速的即時語音對話後端服務，整合 STT (語音轉文字)、LLM (大語言模型) 和 TTS (文字轉語音) 功能。

## 🚀 功能特色

- **語音轉文字 (STT)**: 使用 Faster-Whisper 提供高精度語音識別
- **對話生成 (LLM)**: 整合大語言模型進行智慧對話
- **文字轉語音 (TTS)**: 採用 Microsoft VibeVoice-1.5B 模型，支援多語者語音合成
- **GPU 加速**: 完全支援 CUDA GPU 加速，大幅提升處理速度
- **智慧快取**: 語者預加載和音檔快取機制，避免重複計算
- **分段處理**: 長文字自動分段合成，優化處理效率
- **容器化部署**: 支援 Docker 和 Podman 容器部署

## 📋 系統需求

- **硬體**: NVIDIA GPU (支援 CUDA 12.1+)
- **軟體**: 
  - Python 3.10+
  - CUDA 12.1+
  - Docker/Podman
- **記憶體**: 建議 16GB+ RAM, 8GB+ VRAM

## 🏗️ 架構設計

```
backend/
├── app/                    # 核心應用程式
│   ├── main.py            # FastAPI 主應用
│   ├── stt.py             # 語音轉文字服務
│   ├── tts_vibe.py        # VibeVoice TTS 服務
│   ├── chat.py            # LLM 對話服務
│   └── __init__.py
├── voices/                # 語者音檔目錄
├── models/                # AI 模型快取
├── outputs/               # TTS 輸出目錄
├── uploads/               # 檔案上傳目錄
├── Dockerfile             # Docker 建構檔
├── docker-compose.yml     # Docker Compose 設定
├── requirements.txt       # Python 依賴套件
└── README.md
```

## 🛠️ 安裝部署

### 方法 1: Docker/Podman 部署 (推薦)

1. **建構映像檔**
```bash
# 使用 Docker
docker build -t realtime-dialogue-backend .

# 或使用 Podman
podman build -t realtime-dialogue-backend .
```

2. **啟動服務**
```bash
# 使用現有的啟動腳本
./start-podman.sh

# 或手動啟動
podman run -d \
  --name realtime-dialogue-backend \
  --gpus all \
  -p 8945:8000 \
  -v $(pwd)/voices:/app/voices:ro \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/outputs:/app/outputs \
  realtime-dialogue-backend
```

### 方法 2: 本地開發環境

1. **安裝依賴**
```bash
pip install -r requirements.txt
```

2. **設定環境**
```bash
# 確保 CUDA 可用
python -c "import torch; print(torch.cuda.is_available())"

# 設定語者音檔目錄
mkdir -p voices outputs uploads
```

3. **啟動服務**
```bash
cd app
python main.py
# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔧 設定說明

### 環境變數

- `CUDA_VISIBLE_DEVICES`: 指定使用的 GPU (預設: 所有可用 GPU)
- `TTS_MODEL_NAME`: TTS 模型名稱 (預設: microsoft/VibeVoice-1.5B)
- `STT_MODEL_NAME`: STT 模型名稱 (預設: large-v3)

### 語者音檔

將語者音檔放置在 `voices/` 目錄下，支援格式：
- `.wav` (建議)
- `.mp3`
- `.flac`

檔案命名建議：`{語言}-{姓名}_{性別}.wav`
例如：`zh-Xinran_woman.wav`

## 📡 API 端點

### 健康檢查
```
GET /health
```
回傳系統狀態和各模組就緒狀態。

### 語音轉文字
```
POST /stt
Content-Type: multipart/form-data

Parameters:
- file: 音檔 (WAV, MP3, FLAC)
```

### LLM 對話
```
POST /chat
Content-Type: application/x-www-form-urlencoded

Parameters:
- text: 對話內容
- conversation_id: 對話 ID (可選)
```

### 文字轉語音
```
POST /tts
Content-Type: application/json

Body:
{
  "text": "要合成的文字內容",
  "speaker_voice_path": "/app/voices/zh-Xinran_woman.wav",  // 可選
  "cfg_scale": 1.0  // 可選，控制生成品質 (0.5-2.0)
}
```

### 完整對話流程
```
POST /conversation
Content-Type: multipart/form-data

Parameters:
- audio_file: 使用者語音檔
- conversation_id: 對話 ID (可選)
```

### 語者資訊
```
GET /speaker_info
```
取得當前載入的語者資訊。

## 🎯 效能優化

### 語者預加載機制
- 系統啟動時預先載入預設語者
- 動態語者會被快取避免重複處理
- 支援最多 50 個音檔快取

### 長文字分段處理
- 超過 150 字元的文字會自動分段
- 智慧標點符號分割
- 段落間添加適當靜音間隔

### GPU 記憶體管理
- 自動 GPU 記憶體配置
- 批次處理優化
- 動態參數調整

## 📊 效能基準

在 RTX 4090 GPU 上的測試結果：

| 功能 | 短文字 (<20字) | 中等文字 (20-100字) | 長文字 (100+字) |
|------|----------------|-------------------|----------------|
| STT  | ~0.5秒         | ~1.0秒            | ~2.0秒         |
| LLM  | ~0.8秒         | ~1.2秒            | ~2.5秒         |
| TTS  | ~3.0秒         | ~8.0秒            | ~15秒          |

*注意：首次載入模型需要額外的初始化時間*

## 📜 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 👥 開發團隊

- **主要開發者**: paul.fc.tsai
- **專案維護**: paul.fc.tsai
