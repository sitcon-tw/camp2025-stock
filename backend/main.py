# SITCON Camp 2025 點數系統主入口
# 這個文件用於開發環境啟動


from app.main_refactored import app
from os import environ

CAMP_ENVIRONMENT = environ.get("CAMP_ENVIRONMENT", "development")
PORT = environ.get("PORT", 8000)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_refactored:app",
        host="0.0.0.0",
        port=int(PORT),
        reload=CAMP_ENVIRONMENT == "development",
        log_level="info"
    )
