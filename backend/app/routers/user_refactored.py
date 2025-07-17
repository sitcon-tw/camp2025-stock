# 重構後的使用者路由
# OCP 原則：開放擴充，關閉修改 - 通過依賴注入和介面抽象實作
# SRP 原則：每個端點專注於單一職責
# Clean Code 原則：清晰的命名和結構

from fastapi import APIRouter, Depends, HTTPException, status
from app.application.dependencies import (
    get_user_application_service,
    get_trading_application_service,
    get_transfer_application_service,
    get_ipo_application_service
)
from app.application.services import (
    UserApplicationService,
    TradingApplicationService,
    TransferApplicationService,
    IPOApplicationService
)
from app.schemas.user import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserLoginRequest, UserLoginResponse, UserPortfolio,
    StockOrderRequest, StockOrderResponse,
    TransferRequest, TransferResponse,
    UserPointLog, UserStockOrder
)
from app.schemas.public import QRCodeRedeemRequest, QRCodeRedeemResponse
from app.core.security import get_current_user
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 使用者認證端點 ==========

@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    request: UserLoginRequest,
    user_service: UserApplicationService = Depends(get_user_application_service)
):
    """
    使用者登入
    SRP 原則：專注於登入邏輯的 HTTP 介面
    DIP 原則：依賴抽象的應用服務，而非具體實作
    Clean Code 原則：函數名稱和參數清楚表達意圖
    """
    return await user_service.login_user(request)


@router.post("/register", response_model=UserRegistrationResponse)
async def register_user(
    request: UserRegistrationRequest,
    user_service: UserApplicationService = Depends(get_user_application_service)
):
    """
    使用者註冊
    SRP 原則：專注於註冊邏輯的 HTTP 介面
    OCP 原則：透過依賴注入，新增功能不需修改此端點
    """
    return await user_service.register_user(request)


# ========== 投資組合查詢端點 ==========

@router.get("/portfolio", response_model=UserPortfolio)
async def get_user_portfolio(
    current_user: dict = Depends(get_current_user),
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """
    獲取使用者投資組合
    SRP 原則：專注於投資組合查詢
    Clean Code 原則：函數職責單一且明確
    """
    portfolio = await trading_service.get_user_portfolio(current_user["user_id"])
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return portfolio


# ========== 股票交易端點 ==========

@router.post("/stock/order", response_model=StockOrderResponse)
async def place_stock_order(
    request: StockOrderRequest,
    current_user: dict = Depends(get_current_user),
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """
    下股票訂單
    SRP 原則：專注於股票訂單的 HTTP 處理
    DIP 原則：依賴抽象的交易服務
    """
    return await trading_service.place_stock_order(current_user["user_id"], request)


@router.get("/stock/orders", response_model=List[UserStockOrder])
async def get_user_stock_orders(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """
    獲取使用者股票訂單歷史
    SRP 原則：專注於訂單歷史查詢
    Clean Code 原則：預設參數值合理
    """
    return await trading_service.get_user_orders(current_user["user_id"], limit)


@router.delete("/stock/orders/{order_id}", response_model=StockOrderResponse)
async def cancel_stock_order(
    order_id: str,
    reason: str = "user_cancelled",
    current_user: dict = Depends(get_current_user),
    trading_service: TradingApplicationService = Depends(get_trading_application_service)
):
    """
    取消股票訂單
    SRP 原則：專注於訂單取消功能
    """
    return await trading_service.cancel_stock_order(
        user_id=current_user["user_id"],
        order_id=order_id,
        reason=reason
    )


@router.post("/stock/ipo", response_model=StockOrderResponse)
async def purchase_ipo_shares(
    quantity: int,
    current_user: dict = Depends(get_current_user),
    ipo_service: IPOApplicationService = Depends(get_ipo_application_service)
):
    """
    購買 IPO 股份
    SRP 原則：專注於 IPO 購買的 HTTP 處理
    OCP 原則：IPO 邏輯變更不影響此端點
    """
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive"
        )
    
    return await ipo_service.purchase_ipo_shares(current_user["user_id"], quantity)


# ========== 轉帳端點 ==========

@router.post("/transfer", response_model=TransferResponse)
async def transfer_points(
    request: TransferRequest,
    current_user: dict = Depends(get_current_user),
    transfer_service: TransferApplicationService = Depends(get_transfer_application_service)
):
    """
    點數轉帳
    SRP 原則：專注於轉帳的 HTTP 處理
    DIP 原則：依賴抽象的轉帳服務
    Clean Code 原則：參數驗證清晰
    """
    return await transfer_service.transfer_points(current_user["user_id"], request)


# ========== QR Code 兌換端點 ==========

@router.post("/qr/redeem", response_model=QRCodeRedeemResponse)
async def redeem_qr_code(
    request: QRCodeRedeemRequest,
    current_user: dict = Depends(get_current_user),
    transfer_service: TransferApplicationService = Depends(get_transfer_application_service)
):
    """
    QR Code 兌換點數
    SRP 原則：專注於 QR Code 兌換的 HTTP 處理
    DIP 原則：依賴抽象的轉帳服務
    """
    import json
    from datetime import datetime
    
    try:
        # 解析 QR Code 資料
        qr_data = json.loads(request.qr_data)
        
        # 驗證 QR Code 格式
        if qr_data.get("type") != "points_redeem":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的 QR Code 類型"
            )
        
        qr_id = qr_data.get("id")
        points = qr_data.get("points")
        
        if not qr_id or not points or points <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR Code 資料不完整"
            )
        
        # 檢查 QR Code 是否已經使用過
        from app.core.database import get_database, Collections
        db = get_database()
        
        # 檢查是否已經兌換過
        existing_redemption = await db[Collections.POINT_LOGS].find_one({
            "qr_id": qr_id,
            "user_id": current_user["user_id"]
        })
        
        if existing_redemption:
            return QRCodeRedeemResponse(
                ok=False,
                message="此 QR Code 已經兌換過了"
            )
        
        # 檢查是否有其他人兌換過
        other_redemption = await db[Collections.POINT_LOGS].find_one({
            "qr_id": qr_id
        })
        
        if other_redemption:
            return QRCodeRedeemResponse(
                ok=False,
                message="此 QR Code 已經被其他人兌換過了"
            )
        
        # 給予點數
        from app.application.admin.services import AdminApplicationService as AdminService
        admin_service = AdminService(db)
        
        # 使用 admin_service 的 give_points 功能
        from app.schemas.public import GivePointsRequest
        give_points_request = GivePointsRequest(
            target=current_user["user_id"],
            type="user",
            amount=points
        )
        
        # 給予點數
        await admin_service.give_points(give_points_request)
        
        # 點數記錄已由 admin_service.give_points 處理，不需要重複記錄
        
        return QRCodeRedeemResponse(
            ok=True,
            message=f"成功兌換 {points} 點數！",
            points=points
        )
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR Code 格式錯誤"
        )
    except Exception as e:
        logger.error(f"QR Code 兌換失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="兌換失敗，請稍後再試"
        )


# ========== 歷史記錄端點 ==========

@router.get("/logs", response_model=List[UserPointLog])
async def get_user_point_logs(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    # 注意：這裡需要一個新的 LogService，暫時使用佔位符
    # log_service: LogApplicationService = Depends(get_log_application_service)
):
    """
    獲取使用者點數變動記錄
    SRP 原則：專注於記錄查詢
    TODO: 實作 LogApplicationService
    """
    # 暫時返回空列表，需要實作 LogService
    return []


# ========== 健康檢查端點 ==========

@router.get("/health")
async def user_service_health():
    """
    使用者服務健康檢查
    SRP 原則：專注於健康狀態回報
    Clean Code 原則：簡單明瞭的健康檢查
    """
    return {
        "status": "healthy",
        "service": "user_service",
        "message": "User service is running with refactored architecture"
    }