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

## 🧪 測試驗證

### 執行完整測試
```bash
python test_api.py
```

### 執行效能測試
```bash
python test_tts_optimization.py
```

### 個別模組測試
```bash
# 測試 STT
python -c "from app.stt import STTService; import asyncio; asyncio.run(STTService().test())"

# 測試 TTS
python app/tts_vibe.py

# 測試 LLM
python -c "from app.chat import ChatService; import asyncio; asyncio.run(ChatService().test())"
```

## 📊 效能基準

在 RTX 4090 GPU 上的測試結果：

| 功能 | 短文字 (<20字) | 中等文字 (20-100字) | 長文字 (100+字) |
|------|----------------|-------------------|----------------|
| STT  | ~0.5秒         | ~1.0秒            | ~2.0秒         |
| LLM  | ~0.8秒         | ~1.2秒            | ~2.5秒         |
| TTS  | ~3.0秒         | ~8.0秒            | ~15秒          |

*注意：首次載入模型需要額外的初始化時間*

## 🔍 故障排除

### 常見問題

1. **CUDA 錯誤**
   - 確認 GPU 驅動程式更新
   - 檢查 CUDA 版本相容性
   - 重新安裝 PyTorch with CUDA

2. **記憶體不足**
   - 減少批次大小
   - 清理快取：`torch.cuda.empty_cache()`
   - 檢查 GPU 記憶體使用量

3. **語音合成品質差**
   - 調整 `cfg_scale` 參數 (0.7-1.2)
   - 使用高品質語者音檔
   - 確認文字格式正確

4. **模型載入緩慢**
   - 使用 SSD 儲存模型
   - 預先下載模型檔案
   - 確認網路連線穩定

### 日誌查看
```bash
# Docker 日誌
docker logs realtime-dialogue-backend

# Podman 日誌
podman logs realtime-dialogue-backend

# 即時日誌
docker logs -f realtime-dialogue-backend
```

## 🔧 進階設定

### 自訂 TTS 參數
```python
# 在 tts_vibe.py 中調整
DEFAULT_CFG_SCALE = 1.0        # 生成品質控制
MAX_CACHE_SIZE = 50           # 快取大小限制
SEGMENT_LENGTH_THRESHOLD = 150 # 分段處理閾值
```

### 語者管理
```python
# 動態添加語者
await tts_service.set_speaker_voices(
    speaker_voices=["/path/to/voice1.wav", "/path/to/voice2.wav"],
    speaker_names=["Speaker1", "Speaker2"]
)
```

## 🤝 開發貢獻

1. Fork 此專案
2. 建立功能分支：`git checkout -b feature/new-feature`
3. 提交變更：`git commit -am 'Add new feature'`
4. 推送到分支：`git push origin feature/new-feature`
5. 建立 Pull Request

## 📄 授權協議

本專案採用 MIT 授權協議 - 詳見 [LICENSE](LICENSE) 檔案。

## 🙏 致謝

- **Faster-Whisper**: 語音識別模型
- **Microsoft VibeVoice**: 高品質 TTS 模型
- **FastAPI**: Web 框架
- **PyTorch**: 深度學習框架

---

**版本**: v1.0.0  
**更新日期**: 2025-09-01  
**維護者**: Paul FC Tsai
