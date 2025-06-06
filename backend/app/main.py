from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import admin, public, user, bot, system
from app.core.database import connect_to_mongo, close_mongo_connection, init_database_indexes
from app.config import settings
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SITCON Camp 2025 點數系統",
    description="股票交易及點數管理系統 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由模組

app.include_router(
    public.router, 
    prefix="/api", 
    tags=["Public APIs - 公開資料查詢"]
)

app.include_router(
    user.router, 
    prefix="/api/user", 
    tags=["User APIs - 使用者功能"]
)

app.include_router(
    bot.router, 
    prefix="/api/bot", 
    tags=["Bot APIs - BOT 專用功能"]
)

app.include_router(
    system.router, 
    prefix="/api/system", 
    tags=["System APIs - 系統管理功能"]
)

app.include_router(
    admin.router, 
    prefix="/api/admin", 
    tags=["Admin Management - 管理員後台"]
)

# 生命週期事件 (啟動事件)
@app.on_event("startup")
async def startup_event():
    logger.info("Starting SITCON Camp 2025 點數系統...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # 連線資料庫
    await connect_to_mongo()
    
    # 初始化 index
    await init_database_indexes()
    
    logger.info("Application started successfully")

# 程式結束清理事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down SITCON Camp 2025 點數系統...")
    await close_mongo_connection()
    logger.info("Application shutdown complete")

# 根目錄 endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "SITCON Camp 2025 點數系統 API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": settings.DATABASE_NAME,
        "docs": "/docs",
        "endpoints": {
            "public_apis": "/api",
            "user_apis": "/api/user",
            "admin_apis": "/api/admin",
            "health_check": "/health"
        }
    }

# 健康檢查 endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "SITCON Camp 2025 Backend",
        "database": settings.DATABASE_NAME,
        "environment": settings.ENVIRONMENT
    }

# 全域錯誤處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    if settings.DEBUG:
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    return {
        "detail": "Internal server error"
    }
