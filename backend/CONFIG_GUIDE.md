# 配置文件使用說明

本項目現在支持通過 YAML 配置文件來控制後端 API 的所有模型和相關參數。

## 🎯 主要改進

### 1. **統一的 TTS 接口格式**
- `TTSBreezyService` 和 `TTSVibeService` 現在有相同的輸入/輸出格式
- 都返回 `bytes` 類型的音檔數據
- 支持語者管理和緩存機制

### 2. **配置文件驅動**
- 所有服務配置都在 `config.yaml` 中管理
- 支持動態切換 TTS 提供者（BreezyVoice 或 VibeVoice）
- 靈活的服務啟用/停用控制

### 3. **模型初始化與推論分離**
- BreezyVoice 現在支持初始化時載入模型，推論時直接使用
- 大幅提升推論速度（從數分鐘降到 18-20 秒）

## 🚀 使用方式

### 啟動服務器

```bash
# 使用預設配置
python start_server.py

# 使用 BreezyVoice TTS
python start_server.py -c config_breezy.yaml

# 使用 VibeVoice TTS  
python start_server.py -c config_vibe.yaml

# 自定義主機和端口
python start_server.py --host 0.0.0.0 --port 8080 --debug
```

### API 調用

**統一的 TTS 端點**（自動根據配置選擇 TTS 提供者）：
```bash
curl -X POST "http://localhost:8000/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，我是語音助手",
    "speaker_voice_path": "/path/to/speaker.wav",  # 可選
    "cfg_scale": 1.0  # 僅 VibeVoice 使用
  }' \
  --output output.wav
```

**查看服務狀態**：
```bash
curl http://localhost:8000/
```

## ⚙️ 配置文件說明

### 基本結構
```yaml
api:           # API 服務配置
tts:           # TTS 配置
  provider:    # 選擇 "breezy" 或 "vibe"
  breezy:      # BreezyVoice 配置
  vibe:        # VibeVoice 配置
stt:           # STT 配置
chat:          # LLM 聊天配置
paths:         # 路徑配置
```

### TTS 提供者切換

**使用 BreezyVoice**：
```yaml
tts:
  provider: "breezy"
  breezy:
    enabled: true
    model_repo: "MediaTek-Research/BreezyVoice-300M"
    default_speaker:
      audio_path: "/app/BreezyVoice/data/example.wav"
      transcription: "參考音檔的逐字稿內容"  # 可省去 ASR 時間
  vibe:
    enabled: false
```

**使用 VibeVoice**：
```yaml
tts:
  provider: "vibe"
  breezy:
    enabled: false
  vibe:
    enabled: true
    model_name: "microsoft/VibeVoice-1.5B"
    synthesis:
      cfg_scale: 1.0
```

## 🔧 服務控制

### 啟用/停用服務
```yaml
stt:
  enabled: false    # 停用語音轉文字
tts:
  provider: "breezy" # 但仍可指定 TTS 提供者
  breezy:
    enabled: true    # 啟用 BreezyVoice
chat:
  enabled: false    # 停用聊天功能
```

### 語者管理

**BreezyVoice 語者設定**：
```yaml
tts:
  breezy:
    default_speaker:
      audio_path: "/path/to/speaker.wav"
      transcription: "這是參考音檔的內容"  # 提供逐字稿可加速合成
```

**VibeVoice 語者設定**：
```yaml
tts:
  vibe:
    default_speaker:
      voices_dir: "./voices"
      default_voice: "zh-Xinran_woman.wav"
```

## 📊 性能對比

| TTS 提供者 | 初始化時間 | 推論時間 | 特點 |
|-----------|------------|----------|------|
| BreezyVoice | 較長（模型載入） | ~18-20秒 | 支持注音標註，需要參考音檔 |
| VibeVoice | 中等 | ~10-30秒 | 支持多語者，CFG 調節 |

## 🎯 最佳實踐

1. **BreezyVoice 使用建議**：
   - 提供準確的參考音檔逐字稿可大幅加速合成
   - 適合需要特定語者音色的應用

2. **VibeVoice 使用建議**：
   - 適合多語者應用
   - 可通過 `cfg_scale` 調節音質

3. **生產部署**：
   - 使用 `config.yaml` 管理所有配置
   - 設定 CORS 為具體的前端網址
   - 定期清理緩存和輸出文件

## 🔄 切換 TTS 提供者

只需修改配置文件中的 `tts.provider` 並重啟服務：

```bash
# 切換到 BreezyVoice
sed -i 's/provider: "vibe"/provider: "breezy"/' config.yaml
python start_server.py

# 切換到 VibeVoice  
sed -i 's/provider: "breezy"/provider: "vibe"/' config.yaml
python start_server.py
```

現在你的後端 API 已完全支持配置文件控制，可以靈活切換 TTS 提供者和調整各種參數！
