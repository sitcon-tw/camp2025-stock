import os
from datetime import timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # MongoDB 設定
    CAMP_MONGO_URI: str = os.getenv("CAMP_MONGO_URI", "mongodb://localhost:27017")
    CAMP_DATABASE_NAME: str = os.getenv("CAMP_DATABASE_NAME", "sitcon_camp_2025")
    
    # JWT 設定
    CAMP_JWT_SECRET: str = os.getenv("CAMP_JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    CAMP_JWT_EXPIRE_MINUTES: int = int(os.getenv("CAMP_JWT_EXPIRE_MINUTES", "1440"))  # 24 小時
    
    # 管理員設定
    CAMP_ADMIN_PASSWORD: str = os.getenv("CAMP_ADMIN_PASSWORD", "admin123")
    
    # API 設定
    CAMP_INTERNAL_API_KEY: str = os.getenv("CAMP_INTERNAL_API_KEY", "neverGonnaGiveYouUp")
    
    # CORS 設定
    CAMP_ALLOWED_HOSTS: list = os.getenv("CAMP_ALLOWED_HOSTS", "*").split(",")
    

    # Telegram Bot API URL
    CAMP_TELEGRAM_BOT_API_URL: str = os.getenv("CAMP_TELEGRAM_BOT_API_URL", "https://camp.sitcon.party/bot/broadcast/")
    
    # Telegram Bot Token for OAuth verification
    CAMP_TELEGRAM_BOT_TOKEN: str = os.getenv("CAMP_TELEGRAM_BOT_TOKEN", "")
    
    # 環境設定
    CAMP_ENVIRONMENT: str = os.getenv("CAMP_ENVIRONMENT", "development")
    CAMP_DEBUG: bool = os.getenv("CAMP_DEBUG", "True").lower() == "true"
    
    # 時區設定 (Asia/Taipei UTC+8)
    timezone = timezone(timedelta(hours=8))
    
    @property
    def is_development(self) -> bool:
        return self.CAMP_ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.CAMP_ENVIRONMENT == "production"


settings = Settings()
