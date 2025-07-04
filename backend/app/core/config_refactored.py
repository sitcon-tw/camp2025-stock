# 重構後的設定類
# SRP 原則：專注於設定管理
# Clean Code 原則：清晰的命名、常數管理、類型提示

import os
from datetime import timezone, timedelta
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """
    資料庫設定
    SRP 原則：專注於資料庫相關設定
    Clean Code 原則：使用 dataclass 提高可讀性
    """
    mongo_uri: str
    database_name: str
    connection_timeout: int = 30
    max_pool_size: int = 100
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """從環境變數建立設定"""
        return cls(
            mongo_uri=os.getenv("CAMP_MONGO_URI", "mongodb://localhost:27017"),
            database_name=os.getenv("CAMP_DATABASE_NAME", "sitcon_camp_2025"),
            connection_timeout=int(os.getenv("CAMP_DB_TIMEOUT", "30")),
            max_pool_size=int(os.getenv("CAMP_DB_POOL_SIZE", "100"))
        )


@dataclass
class JWTConfig:
    """
    JWT 設定
    SRP 原則：專注於 JWT 相關設定
    """
    secret_key: str
    algorithm: str = "HS256"
    expire_minutes: int = 1440  # 24 小時
    
    @classmethod
    def from_env(cls) -> 'JWTConfig':
        """從環境變數建立設定"""
        return cls(
            secret_key=os.getenv("CAMP_JWT_SECRET", "your-secret-key"),
            algorithm=os.getenv("CAMP_JWT_ALGORITHM", "HS256"),
            expire_minutes=int(os.getenv("CAMP_JWT_EXPIRE_MINUTES", "1440"))
        )


@dataclass
class SecurityConfig:
    """
    安全設定
    SRP 原則：專注於安全相關設定
    """
    admin_password: str
    internal_api_key: str
    allowed_hosts: List[str]
    cors_origins: List[str]
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """從環境變數建立設定"""
        allowed_hosts = os.getenv("CAMP_ALLOWED_HOSTS", "*").split(",")
        cors_origins = os.getenv("CAMP_CORS_ORIGINS", "*").split(",")
        
        return cls(
            admin_password=os.getenv("CAMP_ADMIN_PASSWORD", "admin123"),
            internal_api_key=os.getenv("CAMP_INTERNAL_API_KEY", "neverGonnaGiveYouUp"),
            allowed_hosts=[host.strip() for host in allowed_hosts],
            cors_origins=[origin.strip() for origin in cors_origins]
        )


@dataclass
class TradingConfig:
    """
    交易設定
    SRP 原則：專注於交易相關設定
    DDD 原則：將業務規則集中管理
    """
    ipo_initial_shares: int
    ipo_initial_price: int
    min_trade_amount: int = 1
    max_trade_amount: int = 1000000
    trading_fee_percentage: float = 0.01
    min_trading_fee: int = 1
    transfer_fee_percentage: float = 0.01
    min_transfer_fee: int = 1
    
    @classmethod
    def from_env(cls) -> 'TradingConfig':
        """從環境變數建立設定"""
        return cls(
            ipo_initial_shares=int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000")),
            ipo_initial_price=int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20")),
            min_trade_amount=int(os.getenv("CAMP_MIN_TRADE_AMOUNT", "1")),
            max_trade_amount=int(os.getenv("CAMP_MAX_TRADE_AMOUNT", "1000000")),
            trading_fee_percentage=float(os.getenv("CAMP_TRADING_FEE_PCT", "0.01")),
            min_trading_fee=int(os.getenv("CAMP_MIN_TRADING_FEE", "1")),
            transfer_fee_percentage=float(os.getenv("CAMP_TRANSFER_FEE_PCT", "0.01")),
            min_transfer_fee=int(os.getenv("CAMP_MIN_TRANSFER_FEE", "1"))
        )


@dataclass
class ExternalServiceConfig:
    """
    外部服務設定
    SRP 原則：專注於外部服務相關設定
    """
    telegram_bot_api_url: str
    notification_timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'ExternalServiceConfig':
        """從環境變數建立設定"""
        return cls(
            telegram_bot_api_url=os.getenv(
                "CAMP_TELEGRAM_BOT_API_URL", 
                "https://camp.sitcon.party/bot/broadcast/"
            ),
            notification_timeout=int(os.getenv("CAMP_NOTIFICATION_TIMEOUT", "30"))
        )


class ApplicationConfig:
    """
    應用程式主設定類
    SRP 原則：整合各個設定模組
    Facade Pattern：提供統一的設定介面
    Clean Code 原則：清晰的組織結構和命名
    """
    
    def __init__(self):
        self.database = DatabaseConfig.from_env()
        self.jwt = JWTConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.trading = TradingConfig.from_env()
        self.external_services = ExternalServiceConfig.from_env()
        
        # 環境相關設定
        self.environment = os.getenv("CAMP_ENVIRONMENT", "development")
        self.debug = os.getenv("CAMP_DEBUG", "True").lower() == "true"
        self.timezone = timezone(timedelta(hours=8))  # Asia/Taipei UTC+8
        
        # 開發模式下記錄環境變數
        if self.is_development:
            self._log_env_vars()
    
    @property
    def is_development(self) -> bool:
        """判斷是否為開發環境"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """判斷是否為生產環境"""
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        """判斷是否為測試環境"""
        return self.environment == "testing"
    
    def get_log_level(self) -> str:
        """
        獲取日誌級別
        Clean Code 原則：根據環境動態決定設定
        """
        if self.is_development:
            return "DEBUG"
        elif self.is_testing:
            return "WARNING"
        else:
            return "INFO"
    
    def validate(self) -> None:
        """
        驗證設定的有效性
        Fail Fast 原則：儘早發現設定錯誤
        """
        if not self.jwt.secret_key or self.jwt.secret_key == "your-secret-key":
            if self.is_production:
                raise ValueError("JWT secret key must be set in production")
        
        if not self.database.mongo_uri:
            raise ValueError("Database URI is required")
        
        if self.trading.ipo_initial_shares <= 0:
            raise ValueError("IPO initial shares must be positive")
        
        if self.trading.ipo_initial_price <= 0:
            raise ValueError("IPO initial price must be positive")
    
    def _log_env_vars(self) -> None:
        """
        開發模式下記錄環境變數
        用於 Zeabur 等雲端平台的Debug
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 需要記錄的環境變數
        env_vars_to_log = [
            "CAMP_ENVIRONMENT",
            "CAMP_DEBUG", 
            "CAMP_TELEGRAM_BOT_TOKEN",
            "CAMP_TELEGRAM_BOT_API_URL",
            "CAMP_MONGO_URI",
            "CAMP_DATABASE_NAME",
            "CAMP_JWT_SECRET",
            "CAMP_JWT_EXPIRE_MINUTES",
            "CAMP_ADMIN_PASSWORD",
            "CAMP_INTERNAL_API_KEY",
            "CAMP_ALLOWED_HOSTS"
        ]
        
        logger.info("=== Development Environment Variables ===")
        for var in env_vars_to_log:
            value = os.getenv(var)
            if value:
                # 敏感資料部分隱藏，但 TELEGRAM_BOT_TOKEN 完整顯示用於Debug
                if var == "CAMP_TELEGRAM_BOT_TOKEN":
                    logger.info(f"{var}: {value}")
                elif var in ["CAMP_JWT_SECRET", "CAMP_ADMIN_PASSWORD", "CAMP_MONGO_URI"]:
                    if len(value) > 10:
                        masked_value = value[:5] + "..." + value[-3:]
                    else:
                        masked_value = "***"
                    logger.info(f"{var}: {masked_value}")
                else:
                    logger.info(f"{var}: {value}")
            else:
                logger.info(f"{var}: (not set)")
        logger.info("=== End Environment Variables ===")
    
    def get_database_url(self) -> str:
        """獲取完整的資料庫連接 URL"""
        return f"{self.database.mongo_uri}/{self.database.database_name}"
    
    def to_dict(self) -> dict:
        """
        轉換為字典格式（用於記錄或除錯）
        注意：敏感資訊會被遮蔽
        """
        return {
            "environment": self.environment,
            "debug": self.debug,
            "database": {
                "database_name": self.database.database_name,
                "connection_timeout": self.database.connection_timeout,
                "max_pool_size": self.database.max_pool_size
                # mongo_uri 被故意省略以保護敏感資訊
            },
            "jwt": {
                "algorithm": self.jwt.algorithm,
                "expire_minutes": self.jwt.expire_minutes
                # secret_key 被故意省略以保護敏感資訊
            },
            "trading": {
                "ipo_initial_shares": self.trading.ipo_initial_shares,
                "ipo_initial_price": self.trading.ipo_initial_price,
                "min_trade_amount": self.trading.min_trade_amount,
                "max_trade_amount": self.trading.max_trade_amount
            }
        }


# 全域設定實例
# Singleton Pattern：確保整個應用使用相同的設定
config = ApplicationConfig()

# 在應用啟動時驗證設定
config.validate()


# 常數定義
# Clean Code 原則：使用常數而非魔術數字
class Constants:
    """
    應用常數定義
    Clean Code 原則：集中管理常數，避免魔術數字
    """
    
    # 使用者相關
    DEFAULT_USER_POINTS = 100
    MIN_USERNAME_LENGTH = 2
    MAX_USERNAME_LENGTH = 50
    
    # 交易相關
    ORDER_STATUS_PENDING = "pending"
    ORDER_STATUS_FILLED = "filled"
    ORDER_STATUS_CANCELLED = "cancelled"
    
    ORDER_TYPE_MARKET = "market"
    ORDER_TYPE_LIMIT = "limit"
    ORDER_TYPE_STOP_LOSS = "stop_loss"
    
    ORDER_SIDE_BUY = "buy"
    ORDER_SIDE_SELL = "sell"
    
    # 轉帳相關
    TRANSFER_STATUS_PENDING = "pending"
    TRANSFER_STATUS_COMPLETED = "completed"
    TRANSFER_STATUS_FAILED = "failed"
    
    # API 響應
    API_SUCCESS = True
    API_FAILURE = False
    
    # 時間相關
    SECONDS_PER_MINUTE = 60
    MINUTES_PER_HOUR = 60
    HOURS_PER_DAY = 24