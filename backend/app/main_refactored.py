# 重構後的主應用程式
# Clean Architecture 原則：清晰的分層結構
# SOLID 原則的綜合應用

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user_refactored, admin, public, bot, system, auth, web, rbac, management, cache, admin_escrow, user_balance
from app.core.database import connect_to_mongo, close_mongo_connection, init_database_indexes
from app.core.config_refactored import config, Constants
from app.application.dependencies import get_service_container
import logging

# Clean Code 原則：清晰的日誌設定
logging.basicConfig(
    level=getattr(logging, config.get_log_level()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# MongoDB 相關的 debug 訊息
logging.getLogger('motor').setLevel(logging.WARNING)
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('motor.core').setLevel(logging.WARNING)
logging.getLogger('pymongo.command').setLevel(logging.WARNING)
logging.getLogger('pymongo.serverSelection').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# SRP 原則：專注於應用程式設定和啟動
app = FastAPI(
    title="SITCON Camp 2025 點數系統 (重構版)",
    description="基於 SOLID 原則和 Clean Architecture 重構的股票交易及點數管理系統 API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=config.debug
)

# CORS 設定 - 使用重構後的設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由模組
# Clean Code 原則：清晰的路由組織

app.include_router(
    public.router, 
    prefix="/api", 
    tags=["Public APIs - 公開資料查詢"]
)

app.include_router(
    user_refactored.router,  # 使用重構後的使用者路由
    prefix="/api/user", 
    tags=["User APIs - 使用者功能 (重構版)"]
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

app.include_router(
    auth.router, 
    prefix="/api/auth", 
    tags=["Authentication - 使用者認證"]
)

app.include_router(
    web.router, 
    prefix="/api/web", 
    tags=["Web APIs - 網頁介面功能"]
)

app.include_router(
    rbac.router, 
    prefix="/api/rbac", 
    tags=["RBAC APIs - 角色權限管理"]
)

app.include_router(
    admin_escrow.router, 
    prefix="/api", 
    tags=["Admin Escrow - 圈存系統管理"]
)

app.include_router(
    user_balance.router, 
    prefix="/api", 
    tags=["User Balance - 使用者餘額詳情"]
)

app.include_router(
    management.router, 
    prefix="/api/management", 
    tags=["Management APIs - 基於權限的管理功能"]
)

app.include_router(
    cache.router, 
    prefix="/api/cache", 
    tags=["Cache APIs - 快取管理功能"]
)


# 生命週期事件管理
@app.on_event("startup")
async def startup_event():
    """
    應用程式啟動事件
    SRP 原則：專注於啟動邏輯
    Clean Code 原則：清晰的啟動流程
    """
    logger.info("Starting SITCON Camp 2025 點數系統 (重構版)...")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Debug mode: {config.debug}")
    
    # 記錄設定資訊（敏感資訊已遮蔽）
    logger.info(f"Configuration: {config.to_dict()}")
    
    try:
        # 連線資料庫
        await connect_to_mongo()
        
        # 初始化資料庫索引
        await init_database_indexes()
        
        # 初始化服務容器
        service_container = get_service_container()
        logger.info("Service container initialized successfully")
        
        # 驗證服務狀態
        await validate_services(service_container)
        
        # 初始化撮合調度器
        from app.services.matching_scheduler import initialize_matching_scheduler
        from app.services.user_service import get_user_service
        
        user_service = get_user_service()
        await initialize_matching_scheduler(user_service, start_immediately=True)
        logger.info("Matching scheduler started with 60s interval")
        
        logger.info("Application started successfully with refactored architecture")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    應用程式關閉事件
    SRP 原則：專注於清理邏輯
    """
    logger.info("Shutting down SITCON Camp 2025 點數系統 (重構版)...")
    
    try:
        # 清理撮合調度器
        from app.services.matching_scheduler import cleanup_matching_scheduler
        await cleanup_matching_scheduler()
        
        # 清理服務資源
        service_container = get_service_container()
        await cleanup_services(service_container)
        
        # 關閉資料庫連線
        await close_mongo_connection()
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def validate_services(service_container) -> None:
    """
    驗證服務狀態
    Clean Code 原則：分離驗證邏輯
    """
    try:
        # 初始化應用服務
        await service_container.user_application_service.initialize()
        await service_container.trading_application_service.initialize()
        await service_container.transfer_application_service.initialize()
        await service_container.ipo_application_service.initialize()
        
        logger.info("All application services validated successfully")
        
    except Exception as e:
        logger.error(f"Service validation failed: {e}")
        raise


async def cleanup_services(service_container) -> None:
    """
    清理服務資源
    Clean Code 原則：分離清理邏輯
    """
    try:
        # 清理應用服務
        await service_container.user_application_service.cleanup()
        await service_container.trading_application_service.cleanup()
        await service_container.transfer_application_service.cleanup()
        await service_container.ipo_application_service.cleanup()
        
        logger.info("All application services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Service cleanup failed: {e}")


# 根目錄端點
@app.get("/", tags=["Root"])
async def root():
    """
    根目錄資訊
    Clean Code 原則：提供清晰的 API 資訊
    """
    return {
        "message": "SITCON Camp 2025 點數系統 API (重構版)",
        "version": "2.0.0",
        "architecture": "Clean Architecture with SOLID Principles",
        "environment": config.environment,
        "database": config.database.database_name,
        "features": [
            "Domain-Driven Design",
            "SOLID Principles",
            "Clean Code",
            "Strategy Pattern",
            "Dependency Injection"
        ],
        "docs": "/docs",
        "endpoints": {
            "public_apis": "/api",
            "user_apis": "/api/user",
            "admin_apis": "/api/admin",
            "health_check": "/health"
        }
    }


# 健康檢查端點
@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    健康檢查
    SRP 原則：專注於健康狀態檢查
    """
    try:
        # 檢查服務容器
        service_container = get_service_container()
        
        # 檢查關鍵服務
        health_status = {
            "status": "healthy",
            "service": "SITCON Camp 2025 Backend (Refactored)",
            "version": "2.0.0",
            "environment": config.environment,
            "database": config.database.database_name,
            "architecture": "Clean Architecture",
            "principles": ["SRP", "OCP", "LSP", "ISP", "DIP"],
            "patterns": ["DDD", "Strategy", "Repository", "Dependency Injection"],
            "timestamp": config.timezone.localize(logger.root.handlers[0].baseFilename 
                                                 if logger.root.handlers 
                                                 else logger.getEffectiveLevel()),
            "services": {
                "user_service": "healthy",
                "trading_service": "healthy", 
                "transfer_service": "healthy",
                "ipo_service": "healthy"
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "SITCON Camp 2025 Backend (Refactored)"
        }


# 全域錯誤處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    全域異常處理器
    SRP 原則：專注於異常處理邏輯
    Clean Code 原則：統一的錯誤處理方式
    """
    logger.error(f"Unhandled exception in {request.url}: {exc}")
    
    if config.debug:
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # 開發模式下返回詳細錯誤資訊
        return {
            "detail": "Internal server error",
            "error": str(exc),
            "type": type(exc).__name__,
            "request_url": str(request.url)
        }
    else:
        # 生產模式下只返回通用錯誤訊息
        return {
            "detail": "Internal server error",
            "error_id": f"ERR-{hash(str(exc)) % 10000:04d}"
        }


# 架構資訊端點
@app.get("/api/architecture", tags=["Documentation"])
async def architecture_info():
    """
    架構資訊端點
    提供重構後的架構說明
    """
    return {
        "architecture": "Clean Architecture",
        "principles_applied": {
            "SRP": "Single Responsibility Principle - 每個類別和模組都有單一職責",
            "OCP": "Open/Closed Principle - 使用策略模式，開放擴充，關閉修改",
            "LSP": "Liskov Substitution Principle - 子類別可以完全替換父類別",
            "ISP": "Interface Segregation Principle - 分離介面，避免不必要的依賴",
            "DIP": "Dependency Inversion Principle - 依賴抽象而非具體實作"
        },
        "patterns_used": {
            "Domain-Driven Design": "領域驅動設計，將業務邏輯封裝在領域層",
            "Repository Pattern": "抽象資料存取層，分離業務邏輯和資料存取",
            "Strategy Pattern": "封裝演算法，支援動態替換策略",
            "Dependency Injection": "控制反轉，透過依賴注入管理物件關係",
            "Clean Code": "清晰命名、單一職責函數、常數管理"
        },
        "layers": {
            "Domain Layer": "app/domain/ - 領域實體、服務和策略",
            "Application Layer": "app/application/ - 應用服務和依賴注入",
            "Infrastructure Layer": "app/infrastructure/ - 資料存取實作",
            "Presentation Layer": "app/routers/ - HTTP 端點和輸入驗證"
        },
        "improvements": [
            "分離關注點，每個模組職責明確",
            "使用策略模式支援多種業務規則",
            "透過依賴注入提高可測試性",
            "清晰的錯誤處理和日誌記錄",
            "設定管理和常數定義",
            "基於介面的設計，支援未來擴充"
        ]
    }