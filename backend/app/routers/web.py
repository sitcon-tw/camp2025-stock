from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService, get_user_service
from app.services.admin_service import AdminService, get_admin_service
from app.schemas.user import (
    UserPortfolio, StockOrderRequest, StockOrderResponse,
    TransferRequest, TransferResponse, UserPointLog, UserStockOrder, UserBasicInfo
)
from app.schemas.public import UserAssetDetail, ErrorResponse
from app.core.security import get_current_user
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 使用者資產管理 ==========

@router.get(
    "/portfolio",
    response_model=UserPortfolio,
    summary="查詢投資組合",
    description="查詢使用者的投資組合"
)
async def get_portfolio(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> UserPortfolio:
    """
    查詢使用者投資組合
    
    Args:
        current_user: 目前使用者資訊（從 JWT Token 解析）
        user_service: 使用者服務（自動注入）
        
    Returns:
        使用者的完整投資組合資訊
    """
    try:
        user_id = current_user.get("sub")
        telegram_id = current_user.get("telegram_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的使用者 Token"
            )
        
        # 使用現有的 bot API 方法，但直接通過 telegram_id 查找
        if telegram_id:
            user = await user_service.get_user_by_telegram_id(telegram_id)
            if user:
                return await user_service.get_user_portfolio_by_username(user.get("id"))
        
        # 如果沒有 telegram_id，嘗試使用 user_id
        return await user_service.get_user_portfolio_by_username(user_id)
        
    except Exception as e:
        logger.error(f"Failed to get portfolio for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得投資組合資訊"
        )


@router.get(
    "/points/history",
    response_model=List[UserPointLog],
    summary="查詢點數記錄",
    description="查詢使用者的點數變動記錄"
)
async def get_point_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> List[UserPointLog]:
    """
    查詢使用者點數記錄
    
    Args:
        limit: 查詢筆數限制（預設 50）
        current_user: 目前使用者資訊（從 JWT Token 解析）
        user_service: 使用者服務（自動注入）
        
    Returns:
        點數變動記錄列表
    """
    try:
        user_id = current_user.get("sub")
        telegram_id = current_user.get("telegram_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的使用者 Token"
            )
        
        # 使用現有的 bot API 方法
        if telegram_id:
            user = await user_service.get_user_by_telegram_id(telegram_id)
            if user:
                return await user_service.get_user_point_logs_by_username(user.get("id"), limit)
        
        return await user_service.get_user_point_logs_by_username(user_id, limit)
        
    except Exception as e:
        logger.error(f"Failed to get point history for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得點數記錄"
        )


# ========== 股票交易 ==========

@router.post(
    "/stock/order",
    response_model=StockOrderResponse,
    summary="下股票訂單",
    description="下買入或賣出股票的訂單"
)
async def place_stock_order(
    order_request: StockOrderRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> StockOrderResponse:
    """
    下股票訂單
    
    Args:
        order_request: 訂單請求資訊
        current_user: 目前使用者資訊（從 JWT Token 解析）
        user_service: 使用者服務（自動注入）
        
    Returns:
        下單結果
    """
    try:
        user_id = current_user.get("sub")
        telegram_id = current_user.get("telegram_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的使用者 Token"
            )
        
        # 使用現有的 bot API 方法
        if telegram_id:
            user = await user_service.get_user_by_telegram_id(telegram_id)
            if user:
                return await user_service.place_stock_order_by_username(user.get("id"), order_request)
        
        return await user_service.place_stock_order_by_username(user_id, order_request)
        
    except Exception as e:
        logger.error(f"Failed to place order for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法下訂單"
        )


@router.get(
    "/stock/orders",
    response_model=List[UserStockOrder],
    summary="查詢股票訂單記錄",
    description="查詢使用者的股票交易訂單記錄"
)
async def get_stock_orders(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> List[UserStockOrder]:
    """
    查詢使用者股票訂單記錄
    
    Args:
        limit: 查詢筆數限制（預設 50）
        current_user: 目前使用者資訊（從 JWT Token 解析）
        user_service: 使用者服務（自動注入）
        
    Returns:
        股票訂單記錄列表
    """
    try:
        user_id = current_user.get("sub")
        telegram_id = current_user.get("telegram_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的使用者 Token"
            )
        
        # 使用現有的 bot API 方法
        if telegram_id:
            user = await user_service.get_user_by_telegram_id(telegram_id)
            if user:
                return await user_service.get_user_stock_orders_by_username(user.get("id"), limit)
        
        return await user_service.get_user_stock_orders_by_username(user_id, limit)
        
    except Exception as e:
        logger.error(f"Failed to get stock orders for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得股票訂單記錄"
        )


# ========== 點數轉帳 ==========

@router.post(
    "/transfer",
    response_model=TransferResponse,
    summary="點數轉帳",
    description="轉帳點數給其他使用者"
)
async def transfer_points(
    transfer_request: TransferRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> TransferResponse:
    """
    點數轉帳
    
    Args:
        transfer_request: 轉帳請求資訊
        current_user: 目前使用者資訊（從 JWT Token 解析）
        user_service: 使用者服務（自動注入）
        
    Returns:
        轉帳結果
    """
    try:
        user_id = current_user.get("sub")
        telegram_id = current_user.get("telegram_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的使用者 Token"
            )
        
        # 使用現有的 bot API 方法
        if telegram_id:
            user = await user_service.get_user_by_telegram_id(telegram_id)
            if user:
                return await user_service.transfer_points_by_username(user.get("id"), transfer_request)
        
        return await user_service.transfer_points_by_username(user_id, transfer_request)
        
    except Exception as e:
        logger.error(f"Failed to transfer points for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法轉帳點數"
        )


# ========== 使用者資訊 ==========

@router.get(
    "/profile",
    summary="查詢使用者資料",
    description="查詢使用者的基本資料"
)
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    查詢使用者基本資料
    
    Args:
        current_user: 目前使用者資訊（從 JWT Token 解析）
        user_service: 使用者服務（自動注入）
        
    Returns:
        使用者基本資訊
    """
    try:
        user_id = current_user.get("sub")
        telegram_id = current_user.get("telegram_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的使用者 Token"
            )
        
        # 使用現有的 bot API 方法
        if telegram_id:
            user = await user_service.get_user_by_telegram_id(telegram_id)
            if user:
                return await user_service.get_user_profile_by_id(user.get("id"))
        
        return await user_service.get_user_profile_by_id(user_id)
        
    except Exception as e:
        logger.error(f"Failed to get profile for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得使用者資料"
        )


# ========== 管理功能 ==========

@router.get(
    "/users",
    response_model=List[UserAssetDetail],
    responses={
        401: {"model": ErrorResponse, "description": "未授權"},
        404: {"model": ErrorResponse, "description": "使用者不存在"}
    },
    summary="查詢所有使用者資產明細",
    description="查詢所有使用者或指定使用者的資產明細，包括點數、持股、總資產等"
)
async def get_users(
    user: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> List[UserAssetDetail]:
    """查詢使用者資產明細
    
    Args:
        user: 可選，指定使用者id。如果不提供則回傳所有使用者
        current_user: 目前使用者（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        使用者資產明細列表
    """
    try:
        return await admin_service.get_user_details(user)
    except Exception as e:
        logger.error(f"Failed to get users for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得使用者資產明細"
        )


@router.get(
    "/students",
    summary="取得所有學員基本資料",
    description="取得所有學員的基本資料，包括使用者名、Telegram ID、隊伍",
    response_model=List[UserBasicInfo]
)
async def get_students(
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> List[UserBasicInfo]:
    """取得所有學員基本資料（僅包含使用者名、Telegram ID、隊伍）"""
    try:
        return await admin_service.list_basic_users()
        
    except Exception as e:
        logger.error(f"Failed to get students for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得學員資料"
        )


@router.get(
    "/teams",
    summary="取得所有隊伍資料",
    description="取得所有隊伍的基本資料，包括隊伍名稱、成員數量等"
)
async def get_teams(
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """取得所有隊伍資料"""
    try:
        return await admin_service.list_all_teams()
        
    except Exception as e:
        logger.error(f"Failed to get teams for user {current_user.get('sub')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得隊伍資料"
        )


# ========== 健康檢查 ==========

@router.get("/health")
async def web_health_check():
    """Web API 健康檢查"""
    return {
        "status": "healthy",
        "service": "Web API",
        "message": "Web API is running properly"
    }