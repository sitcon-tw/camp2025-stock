# SITCON Camp 2025 點數系統主入口
# 這個文件用於開發環境啟動


from app.main import app
from os import environ

CAMP_ENVIRONMENT = environ.get("CAMP_ENVIRONMENT", "development")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=CAMP_ENVIRONMENT == "development",
        log_level="info"
    )
