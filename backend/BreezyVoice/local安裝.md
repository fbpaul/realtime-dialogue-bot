## 在 Conda 環境中設定 PATH（只對該環境有效）
```bash
conda activate your_env_name
export PATH="/home/paul.fc.tsai/ffmpeg-7.0.2-amd64-static:$PATH"
```
# 安裝核心依賴
pip install openai-whisper
pip install WeTextProcessing
pip install opencc-python-reimplemented
pip install g2pw
pip install inflect==7.3.1
pip install conformer==0.3.2
pip install diffusers==0.32.0
pip install hydra-core==1.3.2
pip install gdown==5.1.0
pip install wget==3.2
# 安裝 ttsfrd_dependency
pip install https://www.modelscope.cn/models/speech_tts/speech_kantts_ttsfrd/resolve/master/ttsfrd_dependency-0.1-py3-none-any.whl

# 安裝 ttsfrd (注意這個是針對 Python 3.10 的)
pip install https://www.modelscope.cn/models/speech_tts/speech_kantts_ttsfrd/resolve/master/ttsfrd-0.3.9-cp310-cp310-linux_x86_64.whl
# 測試是否能運行 BreezyVoice
cd BreezyVoice
python single_inference.py --help