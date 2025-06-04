from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService, get_user_service
from app.schemas.bot import (
    BotUserRegistrationRequest, BotStockOrderRequest, BotTransferRequest,
    BotPortfolioRequest, BotPointHistoryRequest, BotStockOrdersRequest,
    BotProfileRequest, TelegramWebhookRequest, BroadcastRequest, BroadcastAllRequest
)
from app.schemas.user import (
    UserRegistrationResponse, UserPortfolio, StockOrderResponse,
    TransferResponse, UserPointLog, UserStockOrder
)
from app.core.security import verify_bot_token
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== BOT 使用者註冊 ==========

@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    summary="BOT 使用者註冊",
    description="透過 BOT 註冊新使用者帳號"
)
async def bot_register_user(
    request: BotUserRegistrationRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> UserRegistrationResponse:
    """
    BOT 使用者註冊
    
    Args:
        request: BOT 註冊請求，包含 from_user 和使用者資訊
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        註冊結果
    """
    # 將 BOT 請求轉換為標準請求，使用 from_user 作為 username
    from app.schemas.user import UserRegistrationRequest
    
    standard_request = UserRegistrationRequest(
        username=request.from_user,  # 直接使用 from_user 作為 username
        email=request.email or f"{request.from_user}@temp.local",  # 如果沒有 email，使用臨時 email
        team=request.team,
        activation_code=request.activation_code,
        telegram_id=request.telegram_id
    )
    
    return await user_service.register_user(standard_request)


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
    return await user_service.get_user_profile_by_username(request.from_user)


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


# ========== Telegram Bot Webhook ==========

@router.post(
    "/webhook",
    summary="Telegram Bot Webhook",
    description="處理來自 Telegram 的 webhook 更新"
)
async def telegram_webhook(
    request: TelegramWebhookRequest,
    token_verified: bool = Depends(verify_bot_token)
):
    """
    處理 Telegram webhook 更新
    
    Args:
        request: Telegram webhook 請求資料
        token_verified: token 驗證結果
        
    Returns:
        處理結果
    """
    try:
        logger.info(f"Received Telegram webhook: update_id={request.update_id}")
        
        # TODO 這裡可以新增實際的 webhook 處理邏輯
        # 例如：處理消息、回調查詢等 
        
        return {
            "ok": True,
            "message": "Webhook processed successfully",
            "update_id": request.update_id
        }
        
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


# ========== 廣播功能 ==========

@router.post(
    "/broadcast",
    summary="向指定群組廣播訊息",
    description="向指定的群組列表廣播訊息"
)
async def broadcast_to_groups(
    request: BroadcastRequest,
    token_verified: bool = Depends(verify_bot_token)
):
    """
    向指定群組廣播訊息
    
    Args:
        request: 廣播請求，包含標題、訊息和目標群組
        token_verified: token 驗證結果
        
    Returns:
        廣播結果
    """
    try:
        logger.info(f"Broadcasting to {len(request.groups)} groups: {request.title}")
        
        # TODO 實際的廣播邏輯
        
        successful_groups = []
        failed_groups = []
        
        for group_id in request.groups:
            try:
                # 模擬廣播邏輯
                # 實際實作時會使用 Telegram Bot API
                logger.info(f"Broadcasting to group {group_id}")
                successful_groups.append(group_id)
            except Exception as e:
                logger.error(f"Failed to broadcast to group {group_id}: {e}")
                failed_groups.append(group_id)
        
        return {
            "ok": True,
            "message": "Broadcast completed",
            "title": request.title,
            "total_groups": len(request.groups),
            "successful_groups": len(successful_groups),
            "failed_groups": len(failed_groups),
            "successful_group_ids": successful_groups,
            "failed_group_ids": failed_groups
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast: {str(e)}"
        )


@router.post(
    "/broadcast/all",
    summary="向所有群組廣播訊息",
    description="向所有註冊的群組廣播訊息"
)
async def broadcast_to_all_groups(
    request: BroadcastAllRequest,
    token_verified: bool = Depends(verify_bot_token)
):
    """
    向所有群組廣播訊息
    
    Args:
        request: 廣播請求，包含標題和訊息
        token_verified: token 驗證結果
        
    Returns:
        廣播結果
    """
    try:
        logger.info(f"Broadcasting to all groups: {request.title}")
        
        # 這裡可以添加實際的廣播邏輯
        # 例如：從資料庫取得所有群組，然後透過 Telegram Bot API 發送訊息
        
        # 模擬取得所有群組
        all_groups = [1001, 1002, 1003]  # 實際實作時從資料庫取得
        
        successful_groups = []
        failed_groups = []
        
        for group_id in all_groups:
            try:
                # 模擬廣播邏輯
                logger.info(f"Broadcasting to group {group_id}")
                successful_groups.append(group_id)
            except Exception as e:
                logger.error(f"Failed to broadcast to group {group_id}: {e}")
                failed_groups.append(group_id)
        
        return {
            "ok": True,
            "message": "Broadcast to all groups completed",
            "title": request.title,
            "total_groups": len(all_groups),
            "successful_groups": len(successful_groups),
            "failed_groups": len(failed_groups),
            "successful_group_ids": successful_groups,
            "failed_group_ids": failed_groups
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast to all: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast to all: {str(e)}"
        )
