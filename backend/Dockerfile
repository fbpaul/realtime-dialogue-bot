# 使用支援多個 CUDA 版本的基礎映像
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# 避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 設定工作目錄
WORKDIR /app

# 設定環境變數來解決 OpenSSL FIPS 問題
ENV OPENSSL_CONF=""
ENV OPENSSL_FIPS=""
ENV OPENSSL_MODULES=""
ENV OPENSSL_ALLOW_PROXY_CERTS=1
ENV OPENSSL_ENABLE_MD5_VERIFY=1
ENV OPENSSL_FORCE_FIPS_MODE=0
ENV FIPS_MODE=0
ENV LIBCRYPTO_FIPS=0

# 更新系統並安裝基本依賴
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    && apt-get update

# 安裝 Python 3.10 和系統依賴
RUN apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-distutils \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    liblzma-dev \
    pkg-config \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# 安裝 ffmpeg 和音頻處理庫
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

# 升級 pip 並設定
RUN python -m pip install --upgrade pip setuptools wheel

# 安裝 PyTorch 和 CUDA 相關套件 (確保版本兼容性)
RUN pip install --no-cache-dir torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121

# 安裝核心 ML 庫
RUN pip install --no-cache-dir \
    transformers==4.44.0 \
    accelerate \
    diffusers \
    librosa \
    soundfile \
    numpy \
    scipy

# 安裝 faster-whisper 和相關依賴
RUN pip install --no-cache-dir \
    faster-whisper \
    ctranslate2

# 複製 requirements.txt 並安裝其他依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 建立必要目錄
RUN mkdir -p /app/uploads /app/outputs /app/models

# 複製本地的 BreezyVoice 和 VibeVoice 目錄
COPY BreezyVoice/ ./BreezyVoice/
COPY VibeVoice/ ./VibeVoice/

# 安裝 VibeVoice (不覆蓋現有依賴)
WORKDIR /app/VibeVoice
RUN pip install -e . --no-deps --no-cache-dir || echo "VibeVoice install may have warnings, continuing..."

# 進入 BreezyVoice 目錄並安裝依賴 (不覆蓋關鍵依賴)
WORKDIR /app/BreezyVoice
RUN pip install --no-cache-dir --no-deps -r requirements.txt || echo "Some packages may have failed, continuing..."

# 手動安裝 BreezyVoice 的特殊依賴
RUN pip install https://www.modelscope.cn/models/speech_tts/speech_kantts_ttsfrd/resolve/master/ttsfrd_dependency-0.1-py3-none-any.whl || echo "ttsfrd_dependency install failed, continuing..."
RUN pip install https://www.modelscope.cn/models/speech_tts/speech_kantts_ttsfrd/resolve/master/ttsfrd-0.3.9-cp310-cp310-linux_x86_64.whl || echo "ttsfrd install failed, continuing..."

# 回到主工作目錄
WORKDIR /app

# 修復 CUDNN 版本兼容性問題
RUN cd /usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib/ && \
    ln -sf libcudnn_ops_infer.so.8 libcudnn_ops.so.9.1.0 && \
    ln -sf libcudnn_ops_infer.so.8 libcudnn_ops.so.9.1 && \
    ln -sf libcudnn_ops_infer.so.8 libcudnn_ops.so.9 && \
    ln -sf libcudnn_ops_infer.so.8 libcudnn_ops.so && \
    ln -sf libcudnn_cnn_infer.so.8 libcudnn_cnn.so.9.1.0 && \
    ln -sf libcudnn_cnn_infer.so.8 libcudnn_cnn.so.9.1 && \
    ln -sf libcudnn_cnn_infer.so.8 libcudnn_cnn.so.9 && \
    ln -sf libcudnn_cnn_infer.so.8 libcudnn_cnn.so && \
    ln -sf libcudnn_adv_infer.so.8 libcudnn_adv_infer.so.9.1.0 && \
    ln -sf libcudnn_adv_infer.so.8 libcudnn_adv_infer.so.9.1 && \
    ln -sf libcudnn_adv_infer.so.8 libcudnn_adv_infer.so.9 && \
    ln -sf libcudnn_adv_train.so.8 libcudnn_adv_train.so.9.1.0 && \
    ln -sf libcudnn_adv_train.so.8 libcudnn_adv_train.so.9.1 && \
    ln -sf libcudnn_adv_train.so.8 libcudnn_adv_train.so.9 && \
    ln -sf libcudnn_cnn_train.so.8 libcudnn_cnn_train.so.9.1.0 && \
    ln -sf libcudnn_cnn_train.so.8 libcudnn_cnn_train.so.9.1 && \
    ln -sf libcudnn_cnn_train.so.8 libcudnn_cnn_train.so.9 && \
    ln -sf libcudnn_ops_train.so.8 libcudnn_ops_train.so.9.1.0 && \
    ln -sf libcudnn_ops_train.so.8 libcudnn_ops_train.so.9.1 && \
    ln -sf libcudnn_ops_train.so.8 libcudnn_ops_train.so.9

# 複製應用程式代碼
COPY app/ ./app/

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUTF8=1
ENV HF_HUB_CACHE=/app/models
ENV TRANSFORMERS_CACHE=/app/models
ENV HF_HOME=/app/models
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 設定 CUDNN 庫路徑
ENV LD_LIBRARY_PATH="/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.10/dist-packages/ctranslate2.libs:/usr/local/nvidia/lib:/usr/local/nvidia/lib64"

# 暴露端口
EXPOSE 8000

# 改為使用 tail 保持容器運行，方便進入容器測試
CMD ["tail", "-f", "/dev/null"]
