"""
Configuration Management System
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Type, List
from dataclasses import dataclass, field
from pathlib import Path
import logging
from enum import Enum

from ...domain.common.exceptions import BusinessRuleException

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Environment(Enum):
    """應用環境"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """資料庫配置"""
    host: str = "localhost"
    port: int = 27017
    name: str = "sitcon_stock"
    username: Optional[str] = None
    password: Optional[str] = None
    connection_timeout: int = 30
    max_pool_size: int = 100
    min_pool_size: int = 10
    
    @property
    def url(self) -> str:
        """獲取資料庫連接URL"""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"mongodb://{self.host}:{self.port}/{self.name}"


@dataclass
class CacheConfig:
    """緩存配置"""
    type: str = "memory"  # memory, redis, layered
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600
    key_prefix: str = "sitcon:"
    max_memory_size: int = 100  # MB
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "type": self.type,
            "redis_url": self.redis_url,
            "default_ttl": self.default_ttl,
            "key_prefix": self.key_prefix,
            "max_memory_size": self.max_memory_size
        }


@dataclass
class NotificationConfig:
    """通知配置"""
    telegram: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "bot_token": "",
        "base_url": "https://api.telegram.org/bot"
    })
    email: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "smtp_host": "localhost",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "use_tls": True
    })
    websocket: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True
    })
    default_channels: List[str] = field(default_factory=lambda: ["telegram"])
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "telegram": self.telegram,
            "email": self.email,
            "websocket": self.websocket,
            "default_channels": self.default_channels
        }


@dataclass
class EventConfig:
    """事件配置"""
    type: str = "memory"  # memory, redis
    redis_url: str = "redis://localhost:6379"
    channel_prefix: str = "events:"
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "type": self.type,
            "redis_url": self.redis_url,
            "channel_prefix": self.channel_prefix,
            "batch_size": self.batch_size,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }


@dataclass
class SecurityConfig:
    """安全配置"""
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    token_expire_minutes: int = 1440  # 24 hours
    password_hash_rounds: int = 12
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "secret_key": self.secret_key,
            "algorithm": self.algorithm,
            "token_expire_minutes": self.token_expire_minutes,
            "password_hash_rounds": self.password_hash_rounds,
            "max_login_attempts": self.max_login_attempts,
            "lockout_duration": self.lockout_duration
        }


@dataclass
class TradingConfig:
    """交易配置"""
    market_open_time: str = "09:00"
    market_close_time: str = "17:00"
    timezone: str = "Asia/Taipei"
    max_order_amount: int = 1000000
    min_order_amount: int = 1
    max_orders_per_user: int = 100
    default_trading_fee: float = 0.001  # 0.1%
    price_precision: int = 2
    quantity_precision: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "market_open_time": self.market_open_time,
            "market_close_time": self.market_close_time,
            "timezone": self.timezone,
            "max_order_amount": self.max_order_amount,
            "min_order_amount": self.min_order_amount,
            "max_orders_per_user": self.max_orders_per_user,
            "default_trading_fee": self.default_trading_fee,
            "price_precision": self.price_precision,
            "quantity_precision": self.quantity_precision
        }


@dataclass
class LoggingConfig:
    """日誌配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10  # MB
    backup_count: int = 5
    console_output: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "level": self.level,
            "format": self.format,
            "file_path": self.file_path,
            "max_file_size": self.max_file_size,
            "backup_count": self.backup_count,
            "console_output": self.console_output
        }


@dataclass
class ApplicationConfig:
    """應用配置"""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    api_prefix: str = "/api/v1"
    docs_enabled: bool = True
    
    # 子配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    events: EventConfig = field(default_factory=EventConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def is_production(self) -> bool:
        """檢查是否為生產環境"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """檢查是否為開發環境"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """檢查是否為測試環境"""
        return self.environment == Environment.TESTING


class ConfigProvider(ABC):
    """配置提供者接口"""
    
    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """加載配置"""
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any]) -> None:
        """保存配置"""
        pass


class FileConfigProvider(ConfigProvider):
    """文件配置提供者"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
    
    def load_config(self) -> Dict[str, Any]:
        """從文件加載配置"""
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
            raise BusinessRuleException(f"Failed to save config: {e}", "config_save_failed")


class EnvironmentConfigProvider(ConfigProvider):
    """環境變量配置提供者"""
    
    def __init__(self, prefix: str = "SITCON_"):
        self.prefix = prefix
    
    def load_config(self) -> Dict[str, Any]:
        """從環境變量加載配置"""
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix):].lower()
                config[config_key] = self._convert_value(value)
        
        return config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到環境變量"""
        for key, value in config.items():
            env_key = f"{self.prefix}{key.upper()}"
            os.environ[env_key] = str(value)
    
    def _convert_value(self, value: str) -> Any:
        """轉換值類型"""
        # 嘗試轉換為布爾值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 嘗試轉換為數字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # 嘗試轉換為JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        return value


class CompositeConfigProvider(ConfigProvider):
    """複合配置提供者"""
    
    def __init__(self, providers: List[ConfigProvider]):
        self.providers = providers
    
    def load_config(self) -> Dict[str, Any]:
        """從多個提供者加載配置"""
        config = {}
        
        for provider in self.providers:
            try:
                provider_config = provider.load_config()
                config.update(provider_config)
            except Exception as e:
                logger.warning(f"Failed to load config from provider {provider.__class__.__name__}: {e}")
        
        return config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到第一個提供者"""
        if self.providers:
            self.providers[0].save_config(config)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, provider: ConfigProvider):
        self.provider = provider
        self._config: Optional[ApplicationConfig] = None
    
    def load_config(self) -> ApplicationConfig:
        """加載配置"""
        if self._config is None:
            raw_config = self.provider.load_config()
            self._config = self._build_config(raw_config)
        
        return self._config
    
    def reload_config(self) -> ApplicationConfig:
        """重新加載配置"""
        self._config = None
        return self.load_config()
    
    def save_config(self, config: ApplicationConfig) -> None:
        """保存配置"""
        raw_config = self._serialize_config(config)
        self.provider.save_config(raw_config)
        self._config = config
    
    def get_config(self) -> ApplicationConfig:
        """獲取配置"""
        return self.load_config()
    
    def update_config(self, updates: Dict[str, Any]) -> ApplicationConfig:
        """更新配置"""
        config = self.load_config()
        
        # 更新配置
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.save_config(config)
        return config
    
    def _build_config(self, raw_config: Dict[str, Any]) -> ApplicationConfig:
        """構建配置對象"""
        config = ApplicationConfig()
        
        # 基本配置
        config.environment = Environment(raw_config.get('environment', 'development'))
        config.debug = raw_config.get('debug', False)
        config.host = raw_config.get('host', '0.0.0.0')
        config.port = raw_config.get('port', 8000)
        config.reload = raw_config.get('reload', False)
        config.cors_enabled = raw_config.get('cors_enabled', True)
        config.cors_origins = raw_config.get('cors_origins', ['*'])
        config.api_prefix = raw_config.get('api_prefix', '/api/v1')
        config.docs_enabled = raw_config.get('docs_enabled', True)
        
        # 資料庫配置
        db_config = raw_config.get('database', {})
        config.database = DatabaseConfig(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 27017),
            name=db_config.get('name', 'sitcon_stock'),
            username=db_config.get('username'),
            password=db_config.get('password'),
            connection_timeout=db_config.get('connection_timeout', 30),
            max_pool_size=db_config.get('max_pool_size', 100),
            min_pool_size=db_config.get('min_pool_size', 10)
        )
        
        # 緩存配置
        cache_config = raw_config.get('cache', {})
        config.cache = CacheConfig(
            type=cache_config.get('type', 'memory'),
            redis_url=cache_config.get('redis_url', 'redis://localhost:6379'),
            default_ttl=cache_config.get('default_ttl', 3600),
            key_prefix=cache_config.get('key_prefix', 'sitcon:'),
            max_memory_size=cache_config.get('max_memory_size', 100)
        )
        
        # 通知配置
        notification_config = raw_config.get('notification', {})
        config.notification = NotificationConfig(
            telegram=notification_config.get('telegram', {
                "enabled": True,
                "bot_token": "",
                "base_url": "https://api.telegram.org/bot"
            }),
            email=notification_config.get('email', {
                "enabled": False,
                "smtp_host": "localhost",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "use_tls": True
            }),
            websocket=notification_config.get('websocket', {"enabled": True}),
            default_channels=notification_config.get('default_channels', ['telegram'])
        )
        
        # 事件配置
        events_config = raw_config.get('events', {})
        config.events = EventConfig(
            type=events_config.get('type', 'memory'),
            redis_url=events_config.get('redis_url', 'redis://localhost:6379'),
            channel_prefix=events_config.get('channel_prefix', 'events:'),
            batch_size=events_config.get('batch_size', 100),
            max_retries=events_config.get('max_retries', 3),
            retry_delay=events_config.get('retry_delay', 1.0)
        )
        
        # 安全配置
        security_config = raw_config.get('security', {})
        config.security = SecurityConfig(
            secret_key=security_config.get('secret_key', 'your-secret-key-here'),
            algorithm=security_config.get('algorithm', 'HS256'),
            token_expire_minutes=security_config.get('token_expire_minutes', 1440),
            password_hash_rounds=security_config.get('password_hash_rounds', 12),
            max_login_attempts=security_config.get('max_login_attempts', 5),
            lockout_duration=security_config.get('lockout_duration', 900)
        )
        
        # 交易配置
        trading_config = raw_config.get('trading', {})
        config.trading = TradingConfig(
            market_open_time=trading_config.get('market_open_time', '09:00'),
            market_close_time=trading_config.get('market_close_time', '17:00'),
            timezone=trading_config.get('timezone', 'Asia/Taipei'),
            max_order_amount=trading_config.get('max_order_amount', 1000000),
            min_order_amount=trading_config.get('min_order_amount', 1),
            max_orders_per_user=trading_config.get('max_orders_per_user', 100),
            default_trading_fee=trading_config.get('default_trading_fee', 0.001),
            price_precision=trading_config.get('price_precision', 2),
            quantity_precision=trading_config.get('quantity_precision', 0)
        )
        
        # 日誌配置
        logging_config = raw_config.get('logging', {})
        config.logging = LoggingConfig(
            level=logging_config.get('level', 'INFO'),
            format=logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file_path=logging_config.get('file_path'),
            max_file_size=logging_config.get('max_file_size', 10),
            backup_count=logging_config.get('backup_count', 5),
            console_output=logging_config.get('console_output', True)
        )
        
        return config
    
    def _serialize_config(self, config: ApplicationConfig) -> Dict[str, Any]:
        """序列化配置對象"""
        return {
            'environment': config.environment.value,
            'debug': config.debug,
            'host': config.host,
            'port': config.port,
            'reload': config.reload,
            'cors_enabled': config.cors_enabled,
            'cors_origins': config.cors_origins,
            'api_prefix': config.api_prefix,
            'docs_enabled': config.docs_enabled,
            'database': {
                'host': config.database.host,
                'port': config.database.port,
                'name': config.database.name,
                'username': config.database.username,
                'password': config.database.password,
                'connection_timeout': config.database.connection_timeout,
                'max_pool_size': config.database.max_pool_size,
                'min_pool_size': config.database.min_pool_size
            },
            'cache': config.cache.to_dict(),
            'notification': config.notification.to_dict(),
            'events': config.events.to_dict(),
            'security': config.security.to_dict(),
            'trading': config.trading.to_dict(),
            'logging': config.logging.to_dict()
        }


# 全局配置管理器
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """獲取全局配置管理器"""
    global _global_config_manager
    if _global_config_manager is None:
        # 創建複合配置提供者
        providers = [
            EnvironmentConfigProvider(),
            FileConfigProvider("config/application.json")
        ]
        composite_provider = CompositeConfigProvider(providers)
        _global_config_manager = ConfigManager(composite_provider)
    
    return _global_config_manager


def set_config_manager(manager: ConfigManager):
    """設置全局配置管理器"""
    global _global_config_manager
    _global_config_manager = manager


def get_config() -> ApplicationConfig:
    """獲取應用配置"""
    return get_config_manager().get_config()


# 便利函數
def get_database_config() -> DatabaseConfig:
    """獲取資料庫配置"""
    return get_config().database


def get_cache_config() -> CacheConfig:
    """獲取緩存配置"""
    return get_config().cache


def get_notification_config() -> NotificationConfig:
    """獲取通知配置"""
    return get_config().notification


def get_events_config() -> EventConfig:
    """獲取事件配置"""
    return get_config().events


def get_security_config() -> SecurityConfig:
    """獲取安全配置"""
    return get_config().security


def get_trading_config() -> TradingConfig:
    """獲取交易配置"""
    return get_config().trading


def get_logging_config() -> LoggingConfig:
    """獲取日誌配置"""
    return get_config().logging