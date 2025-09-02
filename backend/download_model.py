from huggingface_hub import snapshot_download
import os

# Spart TTS
snapshot_download(repo_id="SparkAudio/Spark-TTS-0.5B", local_dir="models/Spark-TTS-0.5B", local_dir_use_symlinks=False)

# IndexTTS
# snapshot_path = snapshot_download(repo_id="IndexTeam/IndexTTS-1.5", local_dir="models/IndexTTS-1.5", local_dir_use_symlinks=False)