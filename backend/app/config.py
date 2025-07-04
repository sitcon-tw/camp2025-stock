import os
from datetime import timezone, timedelta
from dotenv import load_dotenv
from app.core.config_loader import get_config_with_env, get_config_int, get_config_bool, get_config_list

load_dotenv()

class Settings:
    # MongoDB 設定
    CAMP_MONGO_URI: str = get_config_with_env("database.mongo_uri", "CAMP_MONGO_URI", "mongodb://localhost:27017")
    CAMP_DATABASE_NAME: str = get_config_with_env("database.database_name", "CAMP_DATABASE_NAME", "sitcon_camp_2025")
    
    # JWT 設定
    CAMP_JWT_SECRET: str = get_config_with_env("auth.jwt_secret", "CAMP_JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    CAMP_JWT_EXPIRE_MINUTES: int = get_config_int("auth.jwt_expire_minutes", int(os.getenv("CAMP_JWT_EXPIRE_MINUTES", "1440")))  # 24 小時
    
    # 管理員設定
    CAMP_ADMIN_PASSWORD: str = get_config_with_env("auth.admin_password", "CAMP_ADMIN_PASSWORD", "admin123")
    
    # API 設定
    CAMP_INTERNAL_API_KEY: str = get_config_with_env("auth.internal_api_key", "CAMP_INTERNAL_API_KEY", "neverGonnaGiveYouUp")
    
    # CORS 設定
    CAMP_ALLOWED_HOSTS: list = get_config_list("network.allowed_hosts", os.getenv("CAMP_ALLOWED_HOSTS", "*").split(","))
    
    # Telegram Bot API URL
    CAMP_TELEGRAM_BOT_API_URL: str = get_config_with_env("network.telegram_bot_api_url", "CAMP_TELEGRAM_BOT_API_URL", "https://camp.sitcon.party/bot/broadcast/")
    
    # Telegram Bot Token for OAuth verification
    CAMP_TELEGRAM_BOT_TOKEN: str = get_config_with_env("network.telegram_bot_token", "CAMP_TELEGRAM_BOT_TOKEN", "")
    
    # 環境設定
    CAMP_ENVIRONMENT: str = get_config_with_env("system.environment", "CAMP_ENVIRONMENT", "development")
    CAMP_DEBUG: bool = get_config_bool("system.debug", os.getenv("CAMP_DEBUG", "True").lower() == "true")
    
    # 時區設定 (Asia/Taipei UTC+8)
    timezone = timezone(timedelta(hours=8))
    
    # 交易系統設定
    INITIAL_STOCK_PRICE: int = get_config_int("trading.initial_stock_price", 20)
    DEFAULT_STOCK_PRICE: int = get_config_int("trading.default_stock_price", 20)
    
    # IPO 設定（優先使用環境變數）
    IPO_INITIAL_SHARES: int = get_config_with_env("trading.ipo.initial_shares", "CAMP_IPO_INITIAL_SHARES", 1000000)
    IPO_INITIAL_PRICE: int = get_config_with_env("trading.ipo.initial_price", "CAMP_IPO_INITIAL_PRICE", 20)
    
    # 交易限制設定
    DEFAULT_TRADING_LIMIT_PERCENT: int = get_config_int("trading.trading_limits.default_limit_percent", 2000)
    
    # 交易相關設定（對應 config_refactored.py 中的環境變數）
    MIN_TRADE_AMOUNT: int = get_config_with_env("trading.min_trade_amount", "CAMP_MIN_TRADE_AMOUNT", 1)
    MAX_TRADE_AMOUNT: int = get_config_with_env("trading.max_trade_amount", "CAMP_MAX_TRADE_AMOUNT", 1000000)
    TRADING_FEE_PERCENTAGE: float = get_config_with_env("trading.trading_fee_percentage", "CAMP_TRADING_FEE_PCT", 0.01)
    MIN_TRADING_FEE: int = get_config_with_env("trading.min_trading_fee", "CAMP_MIN_TRADING_FEE", 1)
    TRANSFER_FEE_PERCENTAGE: float = get_config_with_env("trading.transfer_fee_percentage", "CAMP_TRANSFER_FEE_PCT", 0.01)
    MIN_TRANSFER_FEE: int = get_config_with_env("trading.min_transfer_fee", "CAMP_MIN_TRANSFER_FEE", 1)
    
    # 使用者設定
    INITIAL_USER_BALANCE: int = get_config_int("user.initial_balance", 0)
    INITIAL_USER_STOCKS: int = get_config_int("user.initial_stocks", 0)
    
    # 學員預設設定
    STUDENT_DEFAULT_ENABLED: bool = get_config_bool("user.student_defaults.enabled", False)
    STUDENT_INITIAL_POINTS: int = get_config_int("user.student_defaults.initial_points", 100)
    
    # 重置設定
    RESET_DEFAULT_BALANCE: int = get_config_int("maintenance.reset.default_initial_balance", 10000)
    RESET_DEFAULT_STOCKS: int = get_config_int("maintenance.reset.default_initial_stocks", 0)
    
    # 最終結算設定
    FINAL_SETTLEMENT_PRICE: int = get_config_int("maintenance.final_settlement.default_price", 20)
    
    # 網路設定（對應額外的環境變數）
    NOTIFICATION_TIMEOUT: int = get_config_with_env("network.notification_timeout", "CAMP_NOTIFICATION_TIMEOUT", 30)
    
    @property
    def is_development(self) -> bool:
        return self.CAMP_ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.CAMP_ENVIRONMENT == "production"


settings = Settings()
