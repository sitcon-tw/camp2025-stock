from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService, get_user_service
from app.services.admin_service import AdminService, get_admin_service
from app.schemas.bot import (
    BotStockOrderRequest, BotTransferRequest,
    BotPortfolioRequest, BotPointHistoryRequest, BotStockOrdersRequest,
    BotProfileRequest, TelegramWebhookRequest, BroadcastRequest, BroadcastAllRequest,
    PVPCreateRequest, PVPAcceptRequest, PVPResponse
)
from app.schemas.user import (
    UserRegistrationResponse, UserPortfolio, StockOrderResponse,
    TransferResponse, UserPointLog, UserStockOrder
)
from app.core.security import verify_bot_token
from typing import List, Dict, Union, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()



# ========== BOT 使用者資產管理 ==========

@router.post(
    "/portfolio",
    response_model=UserPortfolio,
    summary="BOT 查詢投資組合",
    description="透過 BOT 查詢使用者的投資組合"
)
async def bot_get_portfolio(
    request: BotPortfolioRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> UserPortfolio:
    """
    BOT 查詢使用者投資組合
    
    Args:
        request: 包含 from_user 的查詢請求
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        使用者的完整投資組合資訊
    """
    return await user_service.get_user_portfolio_by_username(request.from_user)


@router.post(
    "/debug",
    summary="BOT Debug User Data",
    description="Debug user data lookup issues"
)
async def bot_debug_user(
    request: BotPortfolioRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
):
    """Debug user data"""
    return await user_service.debug_user_data(request.from_user)


@router.post(
    "/points/history",
    response_model=List[UserPointLog],
    summary="BOT 查詢點數記錄",
    description="透過 BOT 查詢使用者的點數變動記錄"
)
async def bot_get_point_history(
    request: BotPointHistoryRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> List[UserPointLog]:
    """
    BOT 查詢使用者點數記錄
    
    Args:
        request: 包含 from_user 和查詢參數的請求
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        點數變動記錄列表
    """
    return await user_service.get_user_point_logs_by_username(request.from_user, request.limit)


# ========== BOT 股票交易 ==========

@router.post(
    "/stock/order",
    response_model=StockOrderResponse,
    summary="BOT 下股票訂單",
    description="透過 BOT 下買入或賣出股票的訂單"
)
async def bot_place_stock_order(
    request: BotStockOrderRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> StockOrderResponse:
    """
    BOT 下股票訂單
    
    Args:
        request: BOT 訂單請求，包含 from_user 和訂單資訊
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        下單結果
    """
    # 將 BOT 請求轉換為標準請求
    from app.schemas.user import StockOrderRequest
    
    standard_request = StockOrderRequest(
        order_type=request.order_type,
        side=request.side,
        quantity=request.quantity,
        price=request.price
    )
    
    return await user_service.place_stock_order_by_username(request.from_user, standard_request)


@router.post(
    "/stock/orders",
    response_model=List[UserStockOrder],
    summary="BOT 查詢股票訂單記錄",
    description="透過 BOT 查詢使用者的股票交易訂單記錄"
)
async def bot_get_stock_orders(
    request: BotStockOrdersRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> List[UserStockOrder]:
    """
    BOT 查詢使用者股票訂單記錄
    
    Args:
        request: 包含 from_user 和查詢參數的請求
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        股票訂單記錄列表
    """
    return await user_service.get_user_stock_orders_by_username(request.from_user, request.limit)


# ========== BOT 點數轉帳 ==========

@router.post(
    "/transfer",
    response_model=TransferResponse,
    summary="BOT 點數轉帳",
    description="透過 BOT 轉帳點數給其他使用者"
)
async def bot_transfer_points(
    request: BotTransferRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> TransferResponse:
    """
    BOT 點數轉帳
    
    Args:
        request: BOT 轉帳請求，包含 from_user、收款人和金額
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        轉帳結果
    """
    # 將 BOT 請求轉換為標準請求
    from app.schemas.user import TransferRequest
    
    standard_request = TransferRequest(
        to_username=request.to_username,
        amount=request.amount,
        note=request.note
    )
    
    return await user_service.transfer_points_by_username(request.from_user, standard_request)


# ========== BOT 使用者資訊 ==========

@router.post(
    "/profile",
    summary="BOT 查詢使用者資料",
    description="透過 BOT 查詢使用者的基本資料"
)
async def bot_get_user_profile(
    request: BotProfileRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
):
    """
    BOT 查詢使用者基本資料
    
    Args:
        request: 包含 from_user 的查詢請求
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        使用者基本資訊
    """
    return await user_service.get_user_profile_by_id(request.from_user)


# ========== BOT 健康檢查 ==========

@router.get(
    "/health",
    summary="BOT API 健康檢查",
    description="檢查 BOT API 是否正常運作"
)
async def bot_health_check():
    """
    BOT API 健康檢查
    
    Returns:
        API 狀態資訊
    """
    return {
        "status": "healthy",
        "service": "BOT API",
        "message": "BOT API is running properly"
    }





# ========== BOT 學員管理 ==========

@router.get(
    "/students",
    response_model=List[Dict[str, Any]],
    summary="BOT 取得所有學員資料",
    description="透過 BOT 取得所有學員的基本資料，包括使用者id、所屬隊伍等"
)
async def bot_get_students(
    token_verified: bool = Depends(verify_bot_token),
    admin_service: AdminService = Depends(get_admin_service)
) -> List[Dict[str, Any]]:
    """
    BOT 取得所有學員資料
    
    Args:
        token_verified: token 驗證結果（透過 header 傳入）
        admin_service: 管理員服務（自動注入）
        
    Returns:
        所有學員的基本資料列表
    """
    try:
        return await admin_service.list_all_users()
        
    except Exception as e:
        logger.error(f"BOT failed to get students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student data"
        )


# 取得所有組別，包含名稱，成員數量和總點數
@router.get(
    "/teams",
    response_model=List[Dict[str, Any]],
    summary="BOT 取得所有隊伍資料",
    description="透過 BOT 取得所有隊伍的基本資料，包括隊伍名稱、成員數量等"
)
async def bot_get_teams(
    token_verified: bool = Depends(verify_bot_token),
    admin_service: AdminService = Depends(get_admin_service)
) -> List[Dict[str, Any]]:
    """
    BOT 取得所有隊伍資料
    
    Args:
        token_verified: token 驗證結果（透過 header 傳入）
        admin_service: 管理員服務（自動注入）
        
    Returns:
        所有隊伍的基本資料列表
    """
    try:
        return await admin_service.list_all_teams()
        
    except Exception as e:
        logger.error(f"BOT failed to get teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team data"
        )


# ========== BOT PVP 猜拳 ==========

@router.post(
    "/pvp/create",
    response_model=PVPResponse,
    summary="BOT 建立 PVP 挑戰",
    description="透過 BOT 在群組中建立 PVP 猜拳挑戰"
)
async def bot_create_pvp_challenge(
    request: PVPCreateRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> PVPResponse:
    """
    BOT 建立 PVP 挑戰
    
    Args:
        request: PVP 建立請求，包含發起者、金額、群組 ID
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        PVP 建立結果
    """
    return await user_service.create_pvp_challenge(request.from_user, request.amount, request.chat_id)


@router.post(
    "/pvp/creator-choice",
    response_model=PVPResponse,
    summary="BOT 設定 PVP 發起人選擇",
    description="透過 BOT 設定 PVP 發起人的猜拳選擇"
)
async def bot_set_pvp_creator_choice(
    request: PVPAcceptRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> PVPResponse:
    """
    BOT 設定 PVP 發起人選擇
    
    Args:
        request: PVP 選擇請求，包含發起者、挑戰 ID、出拳選擇
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        設定結果
    """
    return await user_service.set_pvp_creator_choice(request.from_user, request.challenge_id, request.choice)


@router.post(
    "/pvp/accept",
    response_model=PVPResponse,
    summary="BOT 接受 PVP 挑戰",
    description="透過 BOT 接受 PVP 猜拳挑戰並進行遊戲"
)
async def bot_accept_pvp_challenge(
    request: PVPAcceptRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> PVPResponse:
    """
    BOT 接受 PVP 挑戰
    
    Args:
        request: PVP 接受請求，包含接受者、挑戰 ID、出拳選擇
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        PVP 遊戲結果
    """
    return await user_service.accept_pvp_challenge(request.from_user, request.challenge_id, request.choice)

    
