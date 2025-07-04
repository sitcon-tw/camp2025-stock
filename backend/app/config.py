import os
from datetime import timezone, timedelta
from dotenv import load_dotenv
from app.core.config_loader import get_config_with_env, get_config_int, get_config_bool, get_config_list, get_config

load_dotenv()

class Settings:
    # MongoDB 設定 - 環境變數優先，其次 config.yml
    CAMP_MONGO_URI: str = get_config_with_env("database.mongo_uri", "CAMP_MONGO_URI")
    CAMP_DATABASE_NAME: str = get_config_with_env("database.database_name", "CAMP_DATABASE_NAME")
    
    # JWT 設定 - 從 config.yml 取得預設值
    CAMP_JWT_SECRET: str = get_config_with_env("auth.jwt_secret", "CAMP_JWT_SECRET")
    JWT_ALGORITHM: str = get_config("auth.jwt_algorithm", "HS256")  # 簡單字串可以保留備用預設值
    CAMP_JWT_EXPIRE_MINUTES: int = get_config_with_env("auth.jwt_expire_minutes", "CAMP_JWT_EXPIRE_MINUTES")
    
    # 管理員設定
    CAMP_ADMIN_PASSWORD: str = get_config_with_env("auth.admin_password", "CAMP_ADMIN_PASSWORD")
    
    # API 設定
    CAMP_INTERNAL_API_KEY: str = get_config_with_env("auth.internal_api_key", "CAMP_INTERNAL_API_KEY")
    
    # CORS 設定 - 特殊處理列表型態
    CAMP_ALLOWED_HOSTS: list = get_config_list("network.allowed_hosts") or (
        os.getenv("CAMP_ALLOWED_HOSTS", "").split(",") if os.getenv("CAMP_ALLOWED_HOSTS") else ["*"]
    )
    
    # Telegram Bot 設定
    CAMP_TELEGRAM_BOT_API_URL: str = get_config_with_env("network.telegram_bot_api_url", "CAMP_TELEGRAM_BOT_API_URL")
    CAMP_TELEGRAM_BOT_TOKEN: str = get_config_with_env("network.telegram_bot_token", "CAMP_TELEGRAM_BOT_TOKEN")
    
    # 環境設定
    CAMP_ENVIRONMENT: str = get_config_with_env("system.environment", "CAMP_ENVIRONMENT")
    CAMP_DEBUG: bool = (
        get_config_bool("system.debug") if get_config("system.debug") is not None 
        else (os.getenv("CAMP_DEBUG", "True").lower() == "true")
    )
    
    # 時區設定 (Asia/Taipei UTC+8)
    timezone = timezone(timedelta(hours=8))
    
    # 交易系統設定 - 完全從 config.yml 取得
    INITIAL_STOCK_PRICE: int = get_config_int("trading.initial_stock_price")
    DEFAULT_STOCK_PRICE: int = get_config_int("trading.default_stock_price")
    
    # IPO 設定 - 環境變數優先，其次 config.yml
    IPO_INITIAL_SHARES: int = get_config_with_env("trading.ipo.initial_shares", "CAMP_IPO_INITIAL_SHARES")
    IPO_INITIAL_PRICE: int = get_config_with_env("trading.ipo.initial_price", "CAMP_IPO_INITIAL_PRICE")
    
    # 交易限制設定
    DEFAULT_TRADING_LIMIT_PERCENT: int = get_config_int("trading.trading_limits.default_limit_percent")
    
    # 交易相關設定
    MIN_TRADE_AMOUNT: int = get_config_with_env("trading.min_trade_amount", "CAMP_MIN_TRADE_AMOUNT")
    MAX_TRADE_AMOUNT: int = get_config_with_env("trading.max_trade_amount", "CAMP_MAX_TRADE_AMOUNT")
    TRADING_FEE_PERCENTAGE: float = get_config_with_env("trading.trading_fee_percentage", "CAMP_TRADING_FEE_PCT")
    MIN_TRADING_FEE: int = get_config_with_env("trading.min_trading_fee", "CAMP_MIN_TRADING_FEE")
    TRANSFER_FEE_PERCENTAGE: float = get_config_with_env("trading.transfer_fee_percentage", "CAMP_TRANSFER_FEE_PCT")
    MIN_TRANSFER_FEE: int = get_config_with_env("trading.min_transfer_fee", "CAMP_MIN_TRANSFER_FEE")
    
    # 使用者設定
    INITIAL_USER_BALANCE: int = get_config_int("user.initial_balance")
    INITIAL_USER_STOCKS: int = get_config_int("user.initial_stocks")
    
    # 學員預設設定
    STUDENT_DEFAULT_ENABLED: bool = get_config_bool("user.student_defaults.enabled")
    STUDENT_INITIAL_POINTS: int = get_config_int("user.student_defaults.initial_points")
    
    # 重置設定
    RESET_DEFAULT_BALANCE: int = get_config_int("maintenance.reset.default_initial_balance")
    RESET_DEFAULT_STOCKS: int = get_config_int("maintenance.reset.default_initial_stocks")
    
    # 最終結算設定
    FINAL_SETTLEMENT_PRICE: int = get_config_int("maintenance.final_settlement.default_price")
    
    # 網路設定
    NOTIFICATION_TIMEOUT: int = get_config_with_env("network.notification_timeout", "CAMP_NOTIFICATION_TIMEOUT")
    
    @property
    def is_development(self) -> bool:
        return self.CAMP_ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.CAMP_ENVIRONMENT == "production"


settings = Settings()
