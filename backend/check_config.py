#!/usr/bin/env python3
"""
配置檢查腳本 - 驗證模型路徑和配置設定
"""
import os
import sys
import yaml
from pathlib import Path

def check_path(path, description):
    """檢查路徑是否存在"""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {path}")
    return exists

def check_config():
    """檢查配置和模型路徑"""
    print("🔍 檢查模型配置和路徑...")
    print("=" * 60)
    
    # 檢查配置文件
    config_path = "config.yaml"
    if not check_path(config_path, "主配置文件"):
        print("❌ 主配置文件不存在，無法繼續檢查")
        return
    
    # 載入配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("\n📁 檢查 backend/models 目錄結構...")
    models_dir = "./models"
    check_path(models_dir, "models 目錄")
    
    if os.path.exists(models_dir):
        print("  模型目錄內容:")
        for item in sorted(os.listdir(models_dir)):
            item_path = os.path.join(models_dir, item)
            if os.path.isdir(item_path):
                print(f"    📁 {item}")
            else:
                print(f"    📄 {item}")
    
    print("\n🎤 STT 配置檢查...")
    stt_config = config.get("stt", {})
    if stt_config.get("enabled"):
        model_name = stt_config.get("model", "large-v3-turbo")
        model_path = stt_config.get("model_path", "./models")
        print(f"  模型: {model_name}")
        check_path(model_path, "STT 模型路徑")
        
        # 檢查 Hugging Face 格式的模型目錄
        hf_model_dir = f"{models_dir}/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo"
        check_path(hf_model_dir, "Faster-Whisper 模型目錄")
    else:
        print("  STT 已停用")
    
    print("\n🔊 TTS 配置檢查...")
    tts_config = config.get("tts", {})
    provider = tts_config.get("provider", "breezy")
    print(f"  TTS 提供者: {provider}")
    
    if provider == "breezy":
        breezy_config = tts_config.get("breezy", {})
        if breezy_config.get("enabled"):
            model_path = breezy_config.get("model_path", "./models/BreezyVoice")
            breezy_voice_path = breezy_config.get("breezy_voice_path", "/app/BreezyVoice")
            default_speaker = breezy_config.get("default_speaker", {})
            
            check_path(model_path, "BreezyVoice 模型路徑")
            check_path(breezy_voice_path, "BreezyVoice 代碼路徑")
            
            # 檢查 Hugging Face 格式的 BreezyVoice 模型
            hf_breezy_dir = f"{models_dir}/models--MediaTek-Research--BreezyVoice-300M"
            check_path(hf_breezy_dir, "BreezyVoice HF 模型目錄")
            
            speaker_audio = default_speaker.get("audio_path")
            if speaker_audio:
                check_path(speaker_audio, "預設語者音檔")
        else:
            print("  BreezyVoice 已停用")
    
    elif provider == "vibe":
        vibe_config = tts_config.get("vibe", {})
        if vibe_config.get("enabled"):
            model_path = vibe_config.get("model_path", "./models/VibeVoice")
            default_speaker = vibe_config.get("default_speaker", {})
            
            check_path(model_path, "VibeVoice 模型路徑")
            
            voices_dir = default_speaker.get("voices_dir", "./voices")
            check_path(voices_dir, "語者音檔目錄")
        else:
            print("  VibeVoice 已停用")
    
    print("\n💬 LLM 配置檢查...")
    chat_config = config.get("chat", {})
    if chat_config.get("enabled"):
        use_llm_tools = chat_config.get("use_llm_tools", True)
        print(f"  使用 llm_tools: {use_llm_tools}")
        
        if use_llm_tools:
            llm_tools_config = chat_config.get("llm_tools_config", "./llm_tools/configs/models.yaml")
            llm_tools_model = chat_config.get("llm_tools_model", "Qwen2.5-32B-Instruct-GPTQ-Int4")
            
            check_path(llm_tools_config, "LLM Tools 配置文件")
            print(f"  LLM Tools 模型: {llm_tools_model}")
        else:
            local_model_path = chat_config.get("model_path")
            if local_model_path:
                check_path(local_model_path, "本地 LLM 模型路徑")
    else:
        print("  LLM 已停用")
    
    print("\n📂 檢查其他路徑...")
    paths_config = config.get("paths", {})
    for path_name, path_value in paths_config.items():
        if path_value:
            check_path(path_value, f"{path_name} 目錄")
    
    print("\n" + "=" * 60)
    print("✅ 配置檢查完成")

if __name__ == "__main__":
    check_config()
