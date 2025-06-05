from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService, get_user_service
from app.schemas.user import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserLoginRequest, UserLoginResponse, UserPortfolio,
    StockOrderRequest, StockOrderResponse,
    TransferRequest, TransferResponse,
    UserPointLog, UserStockOrder
)
from app.core.security import get_current_user
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 使用者認證 ==========

@router.post(
    "/login",
    response_model=UserLoginResponse,
    summary="使用者登入",
    description="使用者登入，取得認證 Token"
)
async def login_user(
    request: UserLoginRequest,
    user_service: UserService = Depends(get_user_service)
) -> UserLoginResponse:
    """
    使用者登入
    
    Args:
        request: 登入請求
        
    Returns:
        登入結果和 Token
    """
    return await user_service.login_user(request)


# ========== 使用者資產管理 ==========

@router.get(
    "/portfolio",
    response_model=UserPortfolio,
    summary="查詢投資組合",
    description="查詢目前使用者的點數、持股和總資產"
)
async def get_portfolio(
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> UserPortfolio:
    """
    查詢使用者投資組合
    
    Returns:
        使用者的完整投資組合資訊
    """
    return await user_service.get_user_portfolio(current_user["sub"])


@router.get(
    "/points/history",
    response_model=List[UserPointLog],
    summary="查詢點數記錄",
    description="查詢使用者的點數變動記錄"
)
async def get_point_history(
    limit: int = 50,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> List[UserPointLog]:
    """
    查詢使用者點數記錄
    
    Args:
        limit: 查詢筆數限制
        
    Returns:
        點數變動記錄列表
    """
    return await user_service.get_user_point_logs(current_user["sub"], limit)


# ========== 股票交易 ==========

@router.post(
    "/stock/order",
    response_model=StockOrderResponse,
    summary="下股票訂單",
    description="下買入或賣出股票的訂單，支援市價單和限價單"
)
async def place_stock_order(
    request: StockOrderRequest,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> StockOrderResponse:
    """
    下股票訂單
    
    Args:
        request: 訂單請求，包含類型、方向、數量、價格等
        
    Returns:
        下單結果
    """
    return await user_service.place_stock_order(current_user["sub"], request)


@router.get(
    "/stock/orders",
    response_model=List[UserStockOrder],
    summary="查詢股票訂單記錄",
    description="查詢使用者的股票交易訂單記錄"
)
async def get_stock_orders(
    limit: int = 50,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> List[UserStockOrder]:
    """
    查詢使用者股票訂單記錄
    
    Args:
        limit: 查詢筆數限制
        
    Returns:
        股票訂單記錄列表
    """
    return await user_service.get_user_stock_orders(current_user["sub"], limit)


# ========== 點數轉帳 ==========

@router.post(
    "/transfer",
    response_model=TransferResponse,
    summary="點數轉帳",
    description="轉帳點數給其他使用者，收取 1% 手續費"
)
async def transfer_points(
    request: TransferRequest,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> TransferResponse:
    """
    點數轉帳
    
    Args:
        request: 轉帳請求，包含收款人和金額
        
    Returns:
        轉帳結果
    """
    return await user_service.transfer_points(current_user["sub"], request)


# ========== 使用者資訊 ==========

@router.get(
    "/profile",
    summary="查詢使用者資料",
    description="查詢目前使用者的基本資料"
)
async def get_user_profile(
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    查詢使用者基本資料
    
    Returns:
        使用者基本資訊
    """
    try:
        from app.core.database import get_database, Collections
        from bson import ObjectId
        db = get_database()
        
        user = await db[Collections.USERS].find_one({"_id": ObjectId(current_user["sub"])})
        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")
        
        return {
            "username": user.get("username"),
            "email": user.get("email"),
            "team": user.get("team"),
            "points": user.get("points", 0),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="取得使用者資料失敗"
        )


# ========== 便利功能 ==========

@router.get(
    "/dashboard",
    summary="使用者儀表板",
    description="取得使用者儀表板資訊，包含投資組合和最近活動"
)
async def get_user_dashboard(
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    使用者儀表板
    
    Returns:
        儀表板資訊
    """
    try:
        # 取得投資組合
        portfolio = await user_service.get_user_portfolio(current_user["sub"])
        
        # 取得最近點數記錄
        recent_point_logs = await user_service.get_user_point_logs(current_user["sub"], 10)
        
        # 取得最近股票訂單
        recent_stock_orders = await user_service.get_user_stock_orders(current_user["sub"], 10)
        
        # 取得目前股價
        current_price = await user_service._get_current_stock_price()
        
        return {
            "portfolio": portfolio.dict(),
            "current_stock_price": current_price,
            "recent_activities": {
                "point_logs": [log.dict() for log in recent_point_logs],
                "stock_orders": [order.dict() for order in recent_stock_orders]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="取得儀表板資訊失敗"
        )


@router.get(
    "/stats",
    summary="使用者統計",
    description="取得使用者的詳細統計資訊"
)
async def get_user_stats(
    current_user=Depends(get_current_user)
):
    """
    使用者統計資訊
    
    Returns:
        使用者統計資料
    """
    try:
        from app.core.database import get_database, Collections
        from bson import ObjectId
        db = get_database()
        
        user_id = ObjectId(current_user["sub"])
        
        # 統計交易次數
        total_trades = await db[Collections.STOCK_ORDERS].count_documents({
            "user_id": user_id,
            "status": "completed"
        })
        
        # 統計買入次數
        buy_trades = await db[Collections.STOCK_ORDERS].count_documents({
            "user_id": user_id,
            "side": "buy",
            "status": "completed"
        })
        
        # 統計賣出次數
        sell_trades = await db[Collections.STOCK_ORDERS].count_documents({
            "user_id": user_id,
            "side": "sell",
            "status": "completed"
        })
        
        # 統計轉帳次數
        transfer_out = await db[Collections.POINT_LOGS].count_documents({
            "user_id": user_id,
            "type": "transfer_out"
        })
        
        transfer_in = await db[Collections.POINT_LOGS].count_documents({
            "user_id": user_id,
            "type": "transfer_in"
        })
        
        # 取得使用者基本資訊
        user = await db[Collections.USERS].find_one({"_id": user_id})
        
        return {
            "trading_stats": {
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades
            },
            "transfer_stats": {
                "transfers_sent": transfer_out,
                "transfers_received": transfer_in
            },
            "account_info": {
                "member_since": user.get("created_at").isoformat() if user.get("created_at") else None,
                "team": user.get("team"),
                "current_points": user.get("points", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="取得統計資訊失敗"
        )
