from fastapi import APIRouter, Depends, HTTPException, status
from app.services.admin_service import AdminService, get_admin_service
from app.schemas.public import (
    AdminLoginRequest, AdminLoginResponse, UserAssetDetail,
    GivePointsRequest, GivePointsResponse, AnnouncementRequest, 
    AnnouncementResponse, MarketUpdateRequest, MarketUpdateResponse,
    MarketLimitRequest, MarketLimitResponse, ErrorResponse
)
from app.core.security import get_current_admin
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/login", 
    response_model=AdminLoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "認證失敗"}
    },
    summary="管理員登入",
    description="使用密碼登入管理員介面，成功後回傳 JWT Token"
)

# 管理員登入
async def admin_login(
    request: AdminLoginRequest,
    admin_service: AdminService = Depends(get_admin_service)
) -> AdminLoginResponse:
    return await admin_service.login(request)


@router.get(
    "/user",
    response_model=List[UserAssetDetail],
    responses={
        401: {"model": ErrorResponse, "description": "未授權"},
        404: {"model": ErrorResponse, "description": "使用者不存在"}
    },
    summary="查詢使用者資產明細",
    description="查詢所有使用者或指定使用者的資產明細，包括點數、持股、總資產等"
)
async def get_users(
    user: Optional[str] = None,
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
) -> List[UserAssetDetail]:
    """查詢使用者資產明細
    
    Args:
        user: 可選，指定使用者id。如果不提供則回傳所有使用者
        current_admin: 目前管理員（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        使用者資產明細列表
    """
    return await admin_service.get_user_details(user)


@router.post(
    "/users/give-points",
    response_model=GivePointsResponse,
    responses={
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        401: {"model": ErrorResponse, "description": "未授權"},
        404: {"model": ErrorResponse, "description": "使用者或群組不存在"}
    },
    summary="給予點數",
    description="給指定使用者或群組成員發放點數，支援個人和群組兩種模式"
)
async def give_points(
    request: GivePointsRequest,
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
) -> GivePointsResponse:
    """給予點數
    
    Args:
        request: 給點數請求，包含目標、類型和數量
        current_admin: 目前管理員（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        操作結果
    """
    return await admin_service.give_points(request)


@router.post(
    "/announcement",
    response_model=AnnouncementResponse,
    responses={
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        401: {"model": ErrorResponse, "description": "未授權"}
    },
    summary="發布公告",
    description="發布系統公告，可選擇是否廣播到 Telegram Bot"
)
async def create_announcement(
    request: AnnouncementRequest,
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
) -> AnnouncementResponse:
    """發布公告
    
    Args:
        request: 公告請求，包含標題、內容和廣播設定
        current_admin: 目前管理員（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        操作結果
    """
    return await admin_service.create_announcement(request)


@router.post(
    "/market/update",
    response_model=MarketUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        401: {"model": ErrorResponse, "description": "未授權"}
    },
    summary="更新市場開放時間",
    description="設定股票交易市場的開放時間段"
)
async def update_market_hours(
    request: MarketUpdateRequest,
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
) -> MarketUpdateResponse:
    """更新市場開放時間
    
    Args:
        request: 市場時間更新請求
        current_admin: 目前管理員（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        操作結果
    """
    return await admin_service.update_market_hours(request)


@router.post(
    "/market/set-limit",
    response_model=MarketLimitResponse,
    responses={
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        401: {"model": ErrorResponse, "description": "未授權"}
    },
    summary="設定漲跌限制",
    description="設定當日股票交易的漲跌幅限制百分比"
)
async def set_trading_limit(
    request: MarketLimitRequest,
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
) -> MarketLimitResponse:
    """設定漲跌限制
    
    Args:
        request: 漲跌限制請求
        current_admin: 目前管理員（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        操作結果
    """
    return await admin_service.set_trading_limit(request)


# 額外的管理員功能端點

@router.get(
    "/announcements",
    summary="取得公告列表",
    description="取得所有系統公告"
)
async def get_announcements(
    limit: int = 20,
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    """取得公告列表"""
    # 這個功能在原始 API 規格書中沒有，但對管理員很有用
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        announcements_cursor = db[Collections.ANNOUNCEMENTS].find().sort(
            "created_at", -1
        ).limit(limit)
        announcements = await announcements_cursor.to_list(length=None)
        
        # 轉換 ObjectId 為字符串
        for announcement in announcements:
            announcement["_id"] = str(announcement["_id"])
        
        return announcements
        
    except Exception as e:
        logger.error(f"Failed to get announcements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve announcements"
        )


@router.get(
    "/stats",
    summary="取得系統統計",
    description="取得系統整體統計資訊"
)
async def get_system_stats(
    current_admin=Depends(get_current_admin)
):
    """取得系統統計資訊"""
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        # 統計使用者數量
        total_users = await db[Collections.USERS].count_documents({})
        
        # 統計總點數
        total_points_pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$points"}}}
        ]
        total_points_result = await db[Collections.USERS].aggregate(total_points_pipeline).to_list(1)
        total_points = total_points_result[0]["total"] if total_points_result else 0
        
        # 統計總股票數量
        total_stocks_pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$stock_amount"}}}
        ]
        total_stocks_result = await db[Collections.STOCKS].aggregate(total_stocks_pipeline).to_list(1)
        total_stocks = total_stocks_result[0]["total"] if total_stocks_result else 0
        
        # 統計群組數量
        total_groups = await db[Collections.GROUPS].count_documents({})
        
        # 統計交易次數
        total_trades = await db[Collections.STOCK_ORDERS].count_documents({"status": "filled"})
        
        return {
            "total_users": total_users,
            "total_groups": total_groups,
            "total_points": total_points,
            "total_stocks": total_stocks,
            "total_trades": total_trades,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )

# 取得所有學員資料
@router.get(
    "/students",
    summary="取得所有學員資料",
    description="取得所有學員的基本資料，包括使用者id、所屬隊伍等"
)
async def get_students(
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    """取得所有學員資料"""
    try:
        return await admin_service.list_all_users()
        
    except Exception as e:
        logger.error(f"Failed to get students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student data"
        )
    
# 取得所有隊伍資料
@router.get(
    "/teams",
    summary="取得所有隊伍資料",
    description="取得所有隊伍的基本資料，包括隊伍名稱、成員數量等"
)
async def get_teams(
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    """取得所有隊伍資料"""
    try:
        return await admin_service.list_all_teams()
        
    except Exception as e:
        logger.error(f"Failed to get teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team data"
        )
    
 
# 最終結算（將所有使用者持股以固定價格轉點數，並清除其股票）
@router.post(
    "/final-settlement",
    response_model=GivePointsResponse,
    responses={
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="執行最終結算",
    description="將所有使用者的持股以固定價格轉換為點數，並清除其股票"
)
async def final_settlement(
    current_admin=Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
) -> GivePointsResponse:
    """最終結算
    
    Args:
        current_admin: 目前管理員（自動注入）
        admin_service: 管理員服務（自動注入）

    Returns:
        操作結果
    """
    return await admin_service.final_settlement()