"""
配置管理模組
用於讀取和管理 YAML 配置文件
"""
import yaml
import os
from typing import Dict, Any, Optional, List

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"配置文件載入成功: {self.config_path}")
            return config
        except Exception as e:
            print(f"配置文件載入失敗: {e}")
            # 返回預設配置
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """預設配置"""
        return {
            "api": {
                "title": "Realtime Dialogue API",
                "version": "1.0.0",
                "host": "0.0.0.0",
                "port": 8000
            },
            "tts": {
                "provider": "breezy",
                "breezy": {"enabled": True},
                "vibe": {"enabled": False}
            },
            "stt": {"enabled": True},
            "chat": {"enabled": True}
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """獲取配置值，支援點分割的路徑如 'tts.provider'"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_api_config(self) -> Dict[str, Any]:
        """獲取 API 配置"""
        return self.get("api", {})
    
    def get_tts_provider(self) -> str:
        """獲取 TTS 提供者"""
        return self.get("tts.provider", "breezy")
    
    def get_tts_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """獲取 TTS 配置"""
        if provider is None:
            provider = self.get_tts_provider()
        return self.get(f"tts.{provider}", {})
    
    def get_stt_config(self) -> Dict[str, Any]:
        """獲取 STT 配置"""
        return self.get("stt", {})
    
    def get_chat_config(self) -> Dict[str, Any]:
        """獲取 Chat 配置"""
        return self.get("chat", {})
    
    def get_paths_config(self) -> Dict[str, Any]:
        """獲取路徑配置"""
        return self.get("paths", {})
    
    def is_service_enabled(self, service: str) -> bool:
        """檢查服務是否啟用"""
        return self.get(f"{service}.enabled", True)
    
    def ensure_directories(self):
        """確保配置中的目錄存在"""
        paths = self.get_paths_config()
        for path_name, path_value in paths.items():
            if isinstance(path_value, str) and path_value:
                os.makedirs(path_value, exist_ok=True)
                print(f"確保目錄存在: {path_name} -> {path_value}")

# 全域配置實例
config = Config()
