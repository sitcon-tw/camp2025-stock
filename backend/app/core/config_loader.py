import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    """設定載入器，負責讀取和管理 config.yml 設定文件"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化設定載入器
        
        Args:
            config_path: 設定文件路徑，如果不提供則使用預設路徑
        """
        if config_path is None:
            # 預設設定文件路徑：backend/config.yml
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yml"
        
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """載入設定文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"設定文件不存在: {self.config_path}")
                self._config = {}
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
                
            logger.info(f"成功載入設定文件: {self.config_path}")
            
        except Exception as e:
            logger.error(f"載入設定文件失敗: {e}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        獲取設定值
        
        Args:
            key: 設定鍵，支援點號分隔的嵌套鍵 (如: "trading.ipo.initial_price")
            default: 預設值
            
        Returns:
            設定值或預設值
        """
        if not self._config:
            return default
        
        # 支援點號分隔的嵌套鍵
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default
    
    def get_int(self, key: str, default: int = 0) -> int:
        """獲取整數設定值"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"無法將設定值轉換為整數: {key}={value}, 使用預設值: {default}")
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """獲取浮點數設定值"""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"無法將設定值轉換為浮點數: {key}={value}, 使用預設值: {default}")
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """獲取布林設定值"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def get_list(self, key: str, default: list = None) -> list:
        """獲取列表設定值"""
        if default is None:
            default = []
        value = self.get(key, default)
        return value if isinstance(value, list) else default
    
    def get_dict(self, key: str, default: dict = None) -> dict:
        """獲取字典設定值"""
        if default is None:
            default = {}
        value = self.get(key, default)
        return value if isinstance(value, dict) else default
    
    def get_with_env_override(self, key: str, env_var: str, fallback_default: Any = None) -> Any:
        """
        獲取設定值，優先使用環境變數，然後使用 config.yml
        
        Args:
            key: 設定鍵
            env_var: 環境變數名稱
            fallback_default: 緊急備用預設值（只在 config.yml 也沒有時使用）
            
        Returns:
            環境變數值 > config.yml 值 > 緊急備用預設值
        """
        # 優先使用環境變數
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value
        
        # 其次使用 config.yml 設定文件（這應該是主要的預設值來源）
        config_value = self.get(key)
        if config_value is not None:
            return config_value
        
        # 最後使用緊急備用預設值（理論上不應該走到這裡）
        if fallback_default is not None:
            logger.warning(f"Using emergency fallback default for {key}: {fallback_default}")
        return fallback_default
    
    def reload(self) -> None:
        """重新載入設定文件"""
        self._load_config()
    
    def dump_config(self) -> Dict[str, Any]:
        """返回完整的設定字典（用於調試）"""
        return self._config.copy() if self._config else {}

# 全局設定實例
config_loader = ConfigLoader()

# 便捷函數
def get_config(key: str, default: Any = None) -> Any:
    """獲取設定值的便捷函數"""
    return config_loader.get(key, default)

def get_config_int(key: str, default: int = 0) -> int:
    """獲取整數設定值的便捷函數"""
    return config_loader.get_int(key, default)

def get_config_float(key: str, default: float = 0.0) -> float:
    """獲取浮點數設定值的便捷函數"""
    return config_loader.get_float(key, default)

def get_config_bool(key: str, default: bool = False) -> bool:
    """獲取布林設定值的便捷函數"""
    return config_loader.get_bool(key, default)

def get_config_list(key: str, default: list = None) -> list:
    """獲取列表設定值的便捷函數"""
    return config_loader.get_list(key, default)

def get_config_dict(key: str, default: dict = None) -> dict:
    """獲取字典設定值的便捷函數"""
    return config_loader.get_dict(key, default)

def get_config_with_env(key: str, env_var: str, default: Any = None) -> Any:
    """獲取設定值（優先環境變數）的便捷函數"""
    return config_loader.get_with_env_override(key, env_var, default)