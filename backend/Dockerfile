# 使用支援 CUDA 12.1 + cuDNN 9 的官方映像
FROM nvidia/cuda:12.1.0-cudnn9-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# OpenSSL FIPS 設定（避免某些套件報錯）
ENV OPENSSL_CONF=""
ENV OPENSSL_FIPS=""
ENV OPENSSL_MODULES=""
ENV OPENSSL_ALLOW_PROXY_CERTS=1
ENV OPENSSL_ENABLE_MD5_VERIFY=1
ENV OPENSSL_FORCE_FIPS_MODE=0
ENV FIPS_MODE=0
ENV LIBCRYPTO_FIPS=0

# 安裝系統依賴與 Python 3.10
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
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
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# 升級 pip
RUN python -m pip install --upgrade pip setuptools wheel

# 安裝 PyTorch + CUDA 12.1 相容版本
RUN pip install --no-cache-dir torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121

# 安裝核心 ML 套件
RUN pip install --no-cache-dir \
    transformers==4.44.0 \
    accelerate \
    diffusers \
    librosa \
    soundfile \
    numpy \
    scipy

# 安裝 faster-whisper 與 ctranslate2
RUN pip install --no-cache-dir \
    faster-whisper \
    ctranslate2

# 安裝其他依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 建立必要目錄
RUN mkdir -p /app/uploads /app/outputs /app/models

# 複製 BreezyVoice 和 VibeVoice
COPY BreezyVoice/ ./BreezyVoice/
COPY VibeVoice/ ./VibeVoice/

# 安裝 VibeVoice
WORKDIR /app/VibeVoice
RUN pip install -e . --no-deps --no-cache-dir || echo "VibeVoice install may have warnings, continuing..."

# 安裝 BreezyVoice 依賴
WORKDIR /app/BreezyVoice
RUN pip install --no-cache-dir --no-deps -r requirements.txt || echo "Some packages may have failed, continuing..."

# 安裝特殊依賴
RUN pip install https://www.modelscope.cn/models/speech_tts/speech_kantts_ttsfrd/resolve/master/ttsfrd_dependency-0.1-py3-none-any.whl || echo "ttsfrd_dependency install failed, continuing..."
RUN pip install https://www.modelscope.cn/models/speech_tts/speech_kantts_ttsfrd/resolve/master/ttsfrd-0.3.9-cp310-cp310-linux_x86_64.whl || echo "ttsfrd install failed, continuing..."

# 回到主目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUTF8=1
ENV HF_HUB_CACHE=/app/models
ENV TRANSFORMERS_CACHE=/app/models
ENV HF_HOME=/app/models
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 設定 cuDNN 路徑（已由 base image 提供）
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu"

# 複製應用程式代碼
COPY app/ ./app/

# 暴露端口
EXPOSE 8000

# 保持容器運行
CMD ["tail", "-f", "/dev/null"]