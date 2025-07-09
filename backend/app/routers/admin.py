from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.services.admin_service import AdminService, get_admin_service
from app.services.user_service import UserService, get_user_service
from app.schemas.public import (
    AdminLoginRequest, AdminLoginResponse, UserAssetDetail,
    GivePointsRequest, GivePointsResponse, AnnouncementRequest, 
    AnnouncementResponse, MarketUpdateRequest, MarketUpdateResponse,
    MarketLimitRequest, MarketLimitResponse, ErrorResponse, Trade, PointLog
)
from app.core.security import get_current_user
from app.core.rbac import RBACService, Permission, require_admin_role, ROLE_PERMISSIONS
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
    # 檢查管理員權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.VIEW_ALL_USERS not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要查看所有使用者權限（目前角色：{user_role.value}）"
        )
    
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
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> GivePointsResponse:
    """給予點數
    
    Args:
        request: 給點數請求，包含目標、類型和數量
        current_user: 目前使用者（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        操作結果
    """
    # 檢查點數管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.GIVE_POINTS not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要點數管理權限（目前角色：{user_role.value}）"
        )
    
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
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> AnnouncementResponse:
    """發布公告
    
    Args:
        request: 公告請求，包含標題、內容和廣播設定
        current_user: 目前使用者（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        操作結果
    """
    # 檢查公告管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.CREATE_ANNOUNCEMENT not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要公告管理權限（目前角色：{user_role.value}）"
        )
    
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
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> MarketUpdateResponse:
    """更新市場開放時間
    
    Args:
        request: 市場時間更新請求
        current_user: 目前使用者（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        操作結果
    """
    # 檢查市場管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.MANAGE_MARKET not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要市場管理權限（目前角色：{user_role.value}）"
        )
    
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
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> MarketLimitResponse:
    """設定漲跌限制
    
    Args:
        request: 漲跌限制請求
        current_user: 目前使用者（自動注入）
        admin_service: 管理員服務（自動注入）
    
    Returns:
        操作結果
    """
    # 檢查市場管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.MANAGE_MARKET not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要市場管理權限（目前角色：{user_role.value}）"
        )
    
    return await admin_service.set_trading_limit(request)


# 額外的管理員功能端點

@router.get(
    "/announcements",
    summary="取得公告列表",
    description="取得所有系統公告"
)
async def get_announcements(
    limit: int = Query(50, ge=1, le=200, description="查詢筆數限制（1-200筆）"),
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """取得公告列表"""
    # 檢查公告管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.CREATE_ANNOUNCEMENT not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要公告管理權限（目前角色：{user_role.value}）"
        )
    
    # 這個功能在原始 API 規格書中沒有，但對管理員很有用
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        announcements_cursor = db[Collections.ANNOUNCEMENTS].find().sort(
            "created_at", -1
        ).limit(limit)
        announcements = await announcements_cursor.to_list(length=None)
        
        # 轉換 ObjectId 為字元串
        for announcement in announcements:
            announcement["_id"] = str(announcement["_id"])
        
        return announcements
        
    except Exception as e:
        logger.error(f"Failed to get announcements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve announcements"
        )


@router.delete(
    "/announcement/{announcement_id}",
    responses={
        200: {"description": "公告刪除成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        404: {"model": ErrorResponse, "description": "公告不存在"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="刪除公告",
    description="刪除指定的公告"
)
async def delete_announcement(
    announcement_id: str,
    current_user: dict = Depends(get_current_user)
):
    """刪除公告
    
    Args:
        announcement_id: 公告ID
        current_user: 目前使用者（自動注入）
        
    Returns:
        操作結果
    """
    # 檢查公告管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.CREATE_ANNOUNCEMENT not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要公告管理權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.core.database import get_database, Collections
        from bson import ObjectId
        from bson.errors import InvalidId
        
        db = get_database()
        
        # 驗證 ObjectId 格式
        try:
            obj_id = ObjectId(announcement_id)
        except InvalidId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的公告ID格式"
            )
        
        # 查詢公告是否存在
        announcement = await db[Collections.ANNOUNCEMENTS].find_one(
            {"_id": obj_id}
        )
        
        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到指定的公告"
            )
        
        # 軟刪除公告 - 標記為已刪除而非真正刪除
        from datetime import datetime, timezone
        
        result = await db[Collections.ANNOUNCEMENTS].update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc),
                    "deleted_by": current_user.get('user_id', 'unknown')
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="標記公告為已刪除失敗"
            )
        
        logger.info(f"Announcement soft deleted: {announcement_id} by user {current_user.get('user_id', 'unknown')}")
        
        # 軟刪除不發送系統通知，因為公告仍然存在於系統中，只是標記為已刪除
        
        return {
            "ok": True,
            "message": "公告已標記為已刪除",
            "deletedAnnouncementId": announcement_id,
            "deletedAnnouncementTitle": announcement.get("title", ""),
            "soft_deleted": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete announcement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除公告時發生錯誤"
        )


@router.get(
    "/stats",
    summary="取得系統統計",
    description="取得系統整體統計資訊"
)
async def get_system_stats(
    current_user: dict = Depends(get_current_user)
):
    """取得系統統計資訊"""
    # 檢查系統管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
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
        
        # 統計隊伍數量（從 USERS 集合的 team 字段統計）
        teams = await db[Collections.USERS].distinct("team")
        # 過濾掉 None 和空字串
        total_groups = len([t for t in teams if t is not None and t.strip() != ""])
        
        # 統計交易次數
        total_trades = await db[Collections.STOCK_ORDERS].count_documents({"status": "filled"})
        
        return {
            "total_users": total_users,
            "total_groups": total_groups,
            "total_points": total_points,
            "total_stocks": total_stocks,
            "total_trades": total_trades,
            "generated_at": datetime.now(datetime.timezone.utc).isoformat()
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
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """取得所有學員資料"""
    # 檢查查看所有使用者權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.VIEW_ALL_USERS not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要查看所有使用者權限（目前角色：{user_role.value}）"
        )
    
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
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """取得所有隊伍資料"""
    # 檢查查看所有使用者權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.VIEW_ALL_USERS not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要查看所有使用者權限（目前角色：{user_role.value}）"
        )
    
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
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> GivePointsResponse:
    """最終結算
    
    Args:
        current_user: 目前使用者（自動注入）
        admin_service: 管理員服務（自動注入）

    Returns:
        操作結果
    """
    # 檢查系統管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    return await admin_service.final_settlement()


@router.get(
    "/ipo/status",
    responses={
        200: {"description": "IPO狀態查詢成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="查詢IPO狀態",
    description="查詢目前IPO狀態資訊"
)
async def get_ipo_status(
    current_user: dict = Depends(get_current_user)
):
    """查詢IPO狀態
    
    Args:
        current_user: 目前使用者（自動注入）

    Returns:
        IPO狀態資訊
    """
    # 檢查系統管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.core.database import get_database, Collections
        
        db = get_database()
        
        # 查詢IPO狀態
        ipo_config = await db[Collections.MARKET_CONFIG].find_one(
            {"type": "ipo_status"}
        )
        
        if ipo_config:
            return {
                "ok": True,
                "initialShares": ipo_config.get("initial_shares", 1000000),
                "sharesRemaining": ipo_config.get("shares_remaining", 1000000),
                "initialPrice": ipo_config.get("initial_price", 20),
                "updatedAt": ipo_config.get("updated_at").isoformat() if ipo_config.get("updated_at") else None
            }
        else:
            # IPO未初始化，返回預設值
            import os
            try:
                initial_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000"))
                initial_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20"))
            except (ValueError, TypeError):
                initial_shares = 1000000
                initial_price = 20
            
            return {
                "ok": True,
                "initialShares": initial_shares,
                "sharesRemaining": initial_shares,
                "initialPrice": initial_price,
                "updatedAt": None,
                "note": "IPO未初始化，顯示預設值"
            }
        
    except Exception as e:
        logger.error(f"Failed to get IPO status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢IPO狀態失敗"
        )


@router.post(
    "/ipo/reset",
    responses={
        200: {"description": "重置成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="重置IPO狀態",
    description="重置IPO狀態，恢復到初始股數"
)
async def reset_ipo(
    initial_shares: int = None,
    initial_price: int = None,
    current_user: dict = Depends(get_current_user)
):
    """重置IPO狀態
    
    Args:
        initial_shares: 初始股數（如果不提供則使用預設設定）
        initial_price: 初始價格（如果不提供則使用預設設定）
        current_user: 目前使用者（自動注入）

    Returns:
        操作結果
    """
    # 檢查系統管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.core.database import get_database, Collections
        from datetime import datetime, timezone
        import os
        
        db = get_database()
        
        # 如果沒有提供參數，從資料庫預設設定或環境變數獲取
        if initial_shares is None or initial_price is None:
            # 查詢資料庫中的預設設定
            defaults_config = await db[Collections.MARKET_CONFIG].find_one(
                {"type": "ipo_defaults"}
            )
            
            if defaults_config:
                if initial_shares is None:
                    initial_shares = defaults_config.get("default_initial_shares", 1000000)
                if initial_price is None:
                    initial_price = defaults_config.get("default_initial_price", 20)
            else:
                # 回退到環境變數或硬編碼預設值
                if initial_shares is None:
                    try:
                        initial_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000"))
                    except (ValueError, TypeError):
                        initial_shares = 1000000
                        
                if initial_price is None:
                    try:
                        initial_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20"))
                    except (ValueError, TypeError):
                        initial_price = 20
        
        # 重置或建立IPO狀態
        await db[Collections.MARKET_CONFIG].update_one(
            {"type": "ipo_status"},
            {
                "$set": {
                    "type": "ipo_status",
                    "initial_shares": initial_shares,
                    "shares_remaining": initial_shares,
                    "initial_price": initial_price,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        logger.info(f"IPO reset: {initial_shares} shares @ {initial_price} points each")
        
        # 傳送系統公告到 Telegram Bot
        try:
            from app.services.admin_service import AdminService
            admin_service = AdminService(db)
            await admin_service._send_system_announcement(
                title="🔄 IPO狀態重置",
                message=f"管理員已重置IPO狀態。新的IPO發行：{initial_shares:,} 股，每股 {initial_price} 點。系統將重新開始IPO申購流程。"
            )
        except Exception as e:
            logger.error(f"Failed to send IPO reset announcement: {e}")
        
        return {
            "ok": True,
            "message": f"IPO已重置：{initial_shares} 股，每股 {initial_price} 點",
            "initialShares": initial_shares,
            "initialPrice": initial_price
        }
        
    except Exception as e:
        logger.error(f"Failed to reset IPO: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置IPO失敗"
        )


@router.post(
    "/ipo/update",
    responses={
        200: {"description": "更新成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="更新IPO參數",
    description="更新IPO剩餘股數或價格，不重置整個IPO狀態"
)
async def update_ipo(
    shares_remaining: int = None,
    initial_price: int = None,
    current_user: dict = Depends(get_current_user)
):
    """更新IPO參數
    
    Args:
        shares_remaining: 剩餘股數（可選）
        initial_price: IPO價格（可選）
        current_user: 目前使用者（自動注入）

    Returns:
        操作結果
    """
    # 檢查系統管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.core.database import get_database, Collections
        from datetime import datetime, timezone
        
        db = get_database()
        
        # 構建更新字段
        update_fields = {"updated_at": datetime.now(timezone.utc)}
        
        if shares_remaining is not None:
            update_fields["shares_remaining"] = max(0, shares_remaining)
        
        if initial_price is not None:
            update_fields["initial_price"] = max(1, initial_price)
        
        # 更新IPO狀態
        result = await db[Collections.MARKET_CONFIG].update_one(
            {"type": "ipo_status"},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            # IPO設定不存在，建立新的
            await db[Collections.MARKET_CONFIG].insert_one({
                "type": "ipo_status",
                "initial_shares": 1000000,
                "shares_remaining": shares_remaining if shares_remaining is not None else 0,
                "initial_price": initial_price if initial_price is not None else 20,
                "updated_at": datetime.now(timezone.utc)
            })
        
        # 取得更新後的狀態
        updated_config = await db[Collections.MARKET_CONFIG].find_one(
            {"type": "ipo_status"}
        )
        
        message_parts = []
        if shares_remaining is not None:
            message_parts.append(f"剩餘股數: {shares_remaining}")
        if initial_price is not None:
            message_parts.append(f"IPO價格: {initial_price} 點")
        
        message = f"IPO已更新：{', '.join(message_parts)}" if message_parts else "IPO狀態已更新"
        
        logger.info(f"IPO updated: {message}")
        
        # 傳送系統公告到 Telegram Bot
        try:
            from app.services.admin_service import AdminService
            admin_service = AdminService(db)
            
            # 構建詳細的公告訊息
            announcement_parts = []
            if shares_remaining is not None:
                announcement_parts.append(f"剩餘股數已調整為 {shares_remaining:,} 股")
            if initial_price is not None:
                announcement_parts.append(f"IPO價格已調整為 {initial_price} 點/股")
            
            detailed_message = f"管理員已更新IPO參數：{', '.join(announcement_parts)}。"
            
            # 如果剩餘股數設為0，加入特別說明
            if shares_remaining is not None and shares_remaining == 0:
                detailed_message += " 由於IPO股數已售罄，市價單將改由限價單撮合，股價將依市場供需變動。"
            
            await admin_service._send_system_announcement(
                title="📊 IPO參數更新",
                message=detailed_message
            )
        except Exception as e:
            logger.error(f"Failed to send IPO update announcement: {e}")
        
        return {
            "ok": True,
            "message": message,
            "initialShares": updated_config.get("initial_shares", 1000000),
            "sharesRemaining": updated_config.get("shares_remaining", 0),
            "initialPrice": updated_config.get("initial_price", 20)
        }
        
    except Exception as e:
        logger.error(f"Failed to update IPO: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新IPO失敗"
        )


@router.post(
    "/reset/alldata",
    responses={
        200: {"description": "重置成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="重置所有資料",
    description="清空所有資料庫集合，將系統恢復到初始狀態"
)
async def reset_all_data(
    current_user: dict = Depends(get_current_user)
):
    """重置所有資料
    
    Args:
        current_user: 目前使用者（自動注入）

    Returns:
        操作結果
    """
    # 檢查系統管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.core.database import get_database, Collections
        from datetime import datetime, timezone
        import os
        
        db = get_database()
        
        logger.warning("Starting complete database reset - this will delete ALL data")
        
        # 記錄重置前的統計
        collections_to_reset = Collections.all_collections()
        
        reset_stats = {}
        for collection_name in collections_to_reset:
            try:
                count = await db[collection_name].count_documents({})
                reset_stats[collection_name] = count
                logger.info(f"Collection {collection_name}: {count} documents")
            except Exception as e:
                logger.warning(f"Could not count {collection_name}: {e}")
                reset_stats[collection_name] = "unknown"
        
        # 清空所有集合
        total_deleted = 0
        for collection_name in collections_to_reset:
            try:
                result = await db[collection_name].delete_many({})
                deleted_count = result.deleted_count
                total_deleted += deleted_count
                logger.info(f"Deleted {deleted_count} documents from {collection_name}")
            except Exception as e:
                logger.error(f"Failed to delete from {collection_name}: {e}")
        
        # 重新初始化基本設定
        try:
            # 初始化IPO狀態
            initial_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000"))
            initial_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20"))
        except (ValueError, TypeError):
            initial_shares = 1000000
            initial_price = 20
        
        # 建立初始IPO設定
        await db[Collections.MARKET_CONFIG].insert_one({
            "type": "ipo_status",
            "initial_shares": initial_shares,
            "shares_remaining": initial_shares,
            "initial_price": initial_price,
            "updated_at": datetime.now(timezone.utc)
        })
        
        # 建立預設市場開放時間 (9:00-17:00 UTC)
        current_time = datetime.now(timezone.utc)
        start_time = int(current_time.replace(hour=9, minute=0, second=0).timestamp())
        end_time = int(current_time.replace(hour=17, minute=0, second=0).timestamp())
        
        await db[Collections.MARKET_CONFIG].insert_one({
            "type": "market_hours",
            "openTime": [
                {"start": start_time, "end": end_time}
            ],
            "updated_at": datetime.now(timezone.utc)
        })
        
        # 建立預設漲跌限制 (20%)
        await db[Collections.MARKET_CONFIG].insert_one({
            "type": "trading_limit",
            "limitPercent": 2000,  # 20% = 2000 basis points
            "updated_at": datetime.now(timezone.utc)
        })
        
        # 重置目前價格為 IPO 初始價格
        await db[Collections.MARKET_CONFIG].insert_one({
            "type": "current_price",
            "price": initial_price,
            "updated_at": datetime.now(timezone.utc)
        })
        
        logger.warning(f"Database reset completed: {total_deleted} documents deleted")
        
        # 傳送系統公告到 Telegram Bot
        try:
            # 使用 admin_service 傳送系統公告
            from app.services.admin_service import AdminService
            admin_service = AdminService(db)
            await admin_service._send_system_announcement(
                title="🔄 系統資料重置完成",
                message=f"管理員已執行系統重置作業，共清除 {total_deleted} 筆記錄。系統已恢復到初始狀態，所有使用者資料已清空。"
            )
        except Exception as e:
            logger.error(f"Failed to send reset announcement: {e}")
        
        return {
            "ok": True,
            "message": f"資料庫已完全重置，共刪除 {total_deleted} 筆記錄",
            "deletedDocuments": total_deleted,
            "resetCollections": list(reset_stats.keys()),
            "collectionStats": reset_stats,
            "initializedConfigs": {
                "ipo": {"shares": initial_shares, "price": initial_price},
                "market_hours": {"start": start_time, "end": end_time},
                "trading_limit": 2000
            },
            "resetAt": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset all data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置所有資料失敗: {str(e)}"
        )


@router.post(
    "/reset/except-users",
    responses={
        200: {"description": "清除成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="清除所有資料（保留使用者）",
    description="⚠️ 危險操作：清除所有資料庫集合，但保留使用者資料和隊伍資料（包括 Telegram 綁定和大頭貼）"
)
async def reset_all_data_except_users(
    current_user: dict = Depends(get_current_user)
):
    """清除所有資料（保留使用者）
    
    Args:
        current_user: 目前使用者（自動注入）

    Returns:
        操作結果
    """
    # 檢查系統管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.core.database import get_database, Collections
        from datetime import datetime, timezone
        import os
        
        db = get_database()
        
        logger.warning("Starting database reset - clearing all data except users")
        
        # 要清除的集合（排除使用者和群組相關資料）
        collections_to_clear = [
            Collections.POINT_LOGS,
            Collections.STOCKS,
            Collections.STOCK_ORDERS,
            Collections.TRADES,
            Collections.ANNOUNCEMENTS,
            Collections.MARKET_CONFIG,
            Collections.PVP_CHALLENGES,
            Collections.QR_CODES,
        ]
        
        # 記錄清除前的統計
        reset_stats = {}
        for collection_name in collections_to_clear:
            try:
                count = await db[collection_name].count_documents({})
                reset_stats[collection_name] = count
                logger.info(f"Collection {collection_name}: {count} documents")
            except Exception as e:
                logger.warning(f"Could not count {collection_name}: {e}")
                reset_stats[collection_name] = "unknown"
        
        # 清空指定集合
        total_deleted = 0
        for collection_name in collections_to_clear:
            try:
                result = await db[collection_name].delete_many({})
                deleted_count = result.deleted_count
                total_deleted += deleted_count
                logger.info(f"Deleted {deleted_count} documents from {collection_name}")
            except Exception as e:
                logger.error(f"Failed to delete from {collection_name}: {e}")
        
        # 重新初始化基本設定
        try:
            # 初始化IPO狀態
            initial_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000"))
            initial_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20"))
        except (ValueError, TypeError):
            initial_shares = 1000000
            initial_price = 20
        
        # 建立初始IPO設定
        await db[Collections.MARKET_CONFIG].insert_one({
            "type": "ipo_status",
            "initial_shares": initial_shares,
            "shares_remaining": initial_shares,
            "initial_price": initial_price,
            "updated_at": datetime.now(timezone.utc)
        })
        
        # 建立預設市場開放時間 (9:00-17:00 UTC)
        current_time = datetime.now(timezone.utc)
        start_time = int(current_time.replace(hour=9, minute=0, second=0).timestamp())
        end_time = int(current_time.replace(hour=17, minute=0, second=0).timestamp())
        
        await db[Collections.MARKET_CONFIG].insert_one({
            "type": "market_hours",
            "openTime": [
                {"start": start_time, "end": end_time}
            ],
            "updated_at": datetime.now(timezone.utc)
        })
        
        # 建立預設漲跌限制 (20%)
        await db[Collections.MARKET_CONFIG].insert_one({
            "type": "trading_limit",
            "limitPercent": 2000,  # 20% = 2000 basis points
            "updated_at": datetime.now(timezone.utc)
        })
        
        # 重置目前價格為 IPO 初始價格
        await db[Collections.MARKET_CONFIG].insert_one({
            "type": "current_price",
            "price": initial_price,
            "updated_at": datetime.now(timezone.utc)
        })
        
        # 重置所有使用者的點數和持股
        users_reset_result = await db[Collections.USERS].update_many(
            {},
            {"$set": {"points": 0}}
        )
        
        logger.warning(f"Database reset (except users) completed: {total_deleted} documents deleted, {users_reset_result.modified_count} users reset")
        
        # 傳送系統公告到 Telegram Bot
        try:
            from app.services.admin_service import AdminService
            admin_service = AdminService(db)
            await admin_service._send_system_announcement(
                title="🔄 系統資料重置完成（保留使用者）",
                message=f"管理員已執行部分系統重置作業，共清除 {total_deleted} 筆記錄。使用者資料和隊伍資料（包括 Telegram 綁定和大頭貼）已保留，但所有使用者點數已重置為 0。"
            )
        except Exception as e:
            logger.error(f"Failed to send reset announcement: {e}")
        
        return {
            "ok": True,
            "message": f"資料庫已部分重置（保留使用者），共刪除 {total_deleted} 筆記錄，重置 {users_reset_result.modified_count} 位使用者點數",
            "deletedDocuments": total_deleted,
            "resetUsers": users_reset_result.modified_count,
            "clearedCollections": collections_to_clear,
            "preservedCollections": [Collections.USERS, Collections.GROUPS],
            "collectionStats": reset_stats,
            "initializedConfigs": {
                "ipo": {"shares": initial_shares, "price": initial_price},
                "market_hours": {"start": start_time, "end": end_time},
                "trading_limit": 2000
            },
            "resetAt": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset data except users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置資料失敗: {str(e)}"
        )


@router.post(
    "/test-announcement",
    responses={
        200: {"description": "測試公告成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="測試系統公告",
    description="測試系統公告功能是否正常工作"
)
async def test_announcement(
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """測試系統公告功能"""
    try:
        await admin_service._send_system_announcement(
            title="🧪 測試公告",
            message="這是一個測試公告，用來驗證系統公告功能是否正常工作。"
        )
        
        return {
            "ok": True,
            "message": "測試公告已傳送"
        }
        
    except Exception as e:
        logger.error(f"Failed to send test announcement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"傳送測試公告失敗: {str(e)}"
        )



@router.get(
    "/ipo/defaults",
    responses={
        200: {"description": "IPO預設設定查詢成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="查詢IPO預設設定",
    description="查詢IPO的預設初始股數和價格設定"
)
async def get_ipo_defaults(
    current_user: dict = Depends(get_current_user)
):
    """查詢IPO預設設定"""
    try:
        from app.core.database import get_database, Collections
        
        db = get_database()
        
        # 查詢IPO預設設定
        defaults_config = await db[Collections.MARKET_CONFIG].find_one(
            {"type": "ipo_defaults"}
        )
        
        if defaults_config:
            return {
                "ok": True,
                "defaultInitialShares": defaults_config.get("default_initial_shares", 1000000),
                "defaultInitialPrice": defaults_config.get("default_initial_price", 20),
                "updatedAt": defaults_config.get("updated_at").isoformat() if defaults_config.get("updated_at") else None
            }
        else:
            # 如果沒有設定，回傳環境變數或預設值
            import os
            try:
                default_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000"))
                default_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20"))
            except (ValueError, TypeError):
                default_shares = 1000000
                default_price = 20
            
            return {
                "ok": True,
                "defaultInitialShares": default_shares,
                "defaultInitialPrice": default_price,
                "updatedAt": None,
                "note": "使用預設設定（未在資料庫中設定）"
            }
        
    except Exception as e:
        logger.error(f"Failed to get IPO defaults: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢IPO預設設定失敗"
        )


@router.post(
    "/ipo/defaults",
    responses={
        200: {"description": "IPO預設設定更新成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="更新IPO預設設定",
    description="更新IPO的預設初始股數和價格設定"
)
async def update_ipo_defaults(
    default_initial_shares: int = None,
    default_initial_price: int = None,
    current_user: dict = Depends(get_current_user)
):
    """更新IPO預設設定"""
    try:
        from app.core.database import get_database, Collections
        from datetime import datetime, timezone
        
        db = get_database()
        
        # 構建更新字段
        update_fields = {"updated_at": datetime.now(timezone.utc)}
        
        if default_initial_shares is not None:
            update_fields["default_initial_shares"] = max(1, default_initial_shares)
        
        if default_initial_price is not None:
            update_fields["default_initial_price"] = max(1, default_initial_price)
        
        if len(update_fields) == 1:  # 只有 updated_at 字段
            return {
                "ok": False,
                "message": "沒有提供任何要更新的參數"
            }
        
        # 更新IPO預設設定
        result = await db[Collections.MARKET_CONFIG].update_one(
            {"type": "ipo_defaults"},
            {"$set": update_fields},
            upsert=True
        )
        
        # 取得更新後的設定
        updated_config = await db[Collections.MARKET_CONFIG].find_one(
            {"type": "ipo_defaults"}
        )
        
        message_parts = []
        if default_initial_shares is not None:
            message_parts.append(f"預設股數: {default_initial_shares}")
        if default_initial_price is not None:
            message_parts.append(f"預設價格: {default_initial_price} 點")
        
        message = f"IPO預設設定已更新：{', '.join(message_parts)}" if message_parts else "IPO預設設定已更新"
        
        logger.info(f"IPO defaults updated: {message}")
        
        # 傳送系統公告到 Telegram Bot
        try:
            from app.services.admin_service import AdminService
            admin_service = AdminService(db)
            
            # 構建詳細的公告訊息
            announcement_parts = []
            if default_initial_shares is not None:
                announcement_parts.append(f"預設初始股數已調整為 {default_initial_shares:,} 股")
            if default_initial_price is not None:
                announcement_parts.append(f"預設IPO價格已調整為 {default_initial_price} 點/股")
            
            detailed_message = f"管理員已更新IPO預設設定：{', '.join(announcement_parts)}。這將影響未來的IPO重置操作。"
            
            await admin_service._send_system_announcement(
                title="⚙️ IPO預設設定更新",
                message=detailed_message
            )
        except Exception as e:
            logger.error(f"Failed to send IPO defaults update announcement: {e}")
        
        return {
            "ok": True,
            "message": message,
            "defaultInitialShares": updated_config.get("default_initial_shares", 1000000),
            "defaultInitialPrice": updated_config.get("default_initial_price", 20)
        }
        
    except Exception as e:
        logger.error(f"Failed to update IPO defaults: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新IPO預設設定失敗"
        )




@router.get(
    "/system/check-negative-balances",
    responses={
        200: {"description": "負點數檢查成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="檢查負點數使用者",
    description="檢查系統中是否有負點數的使用者"
)
async def check_negative_balances(
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """檢查負點數使用者"""
    try:
        result = await admin_service.check_and_fix_negative_balances(fix_mode=False)
        return result
        
    except Exception as e:
        logger.error(f"Failed to check negative balances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"檢查負點數失敗: {str(e)}"
        )


@router.post(
    "/system/fix-negative-balances",
    responses={
        200: {"description": "負點數修復成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="修復負點數使用者",
    description="將所有負點數使用者的點數重置為0"
)
async def fix_negative_balances(
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """修復負點數使用者"""
    try:
        result = await admin_service.check_and_fix_negative_balances(fix_mode=True)
        logger.info(f"Negative balances fixed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to fix negative balances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修復負點數失敗: {str(e)}"
        )


@router.post(
    "/system/trigger-balance-check",
    responses={
        200: {"description": "系統全面檢查成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="觸發系統全面點數檢查",
    description="對所有使用者進行全面的點數完整性檢查，如發現負點數會立即傳送警報"
)
async def trigger_system_wide_balance_check(
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """觸發系統全面點數檢查"""
    try:
        result = await admin_service.trigger_system_wide_balance_check()
        logger.info(f"System-wide balance check completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to trigger system-wide balance check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"系統全面檢查失敗: {str(e)}"
        )


@router.post(
    "/pvp/cleanup",
    responses={
        200: {"description": "PVP 挑戰清理成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="清理過期的 PVP 挑戰",
    description="清理所有過期或卡住的 PVP 挑戰"
)
async def cleanup_pvp_challenges(
    current_user: dict = Depends(get_current_user)
):
    """清理過期的 PVP 挑戰"""
    try:
        from app.core.database import get_database, Collections
        
        db = get_database()
        now = datetime.now(timezone.utc)
        
        # 清理過期的挑戰
        expired_result = await db[Collections.PVP_CHALLENGES].update_many(
            {
                "status": {"$in": ["pending", "waiting_accepter"]},
                "expires_at": {"$lt": now}
            },
            {"$set": {"status": "expired"}}
        )
        
        # 獲取所有進行中的挑戰統計
        pending_count = await db[Collections.PVP_CHALLENGES].count_documents({
            "status": {"$in": ["pending", "waiting_accepter"]}
        })
        
        expired_count = await db[Collections.PVP_CHALLENGES].count_documents({
            "status": "expired"
        })
        
        completed_count = await db[Collections.PVP_CHALLENGES].count_documents({
            "status": "completed"
        })
        
        logger.info(f"PVP cleanup: expired {expired_result.modified_count} challenges")
        
        return {
            "ok": True,
            "message": f"清理完成，過期了 {expired_result.modified_count} 個挑戰",
            "stats": {
                "expired_now": expired_result.modified_count,
                "pending": pending_count,
                "expired_total": expired_count,
                "completed": completed_count
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup PVP challenges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理 PVP 挑戰失敗: {str(e)}"
        )


@router.delete(
    "/pvp/all",
    responses={
        200: {"description": "所有 PVP 資料刪除成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="刪除所有 PVP 資料",
    description="⚠️ 危險操作：刪除資料庫中所有的 PVP 挑戰記錄"
)
async def delete_all_pvp_data(
    current_user: dict = Depends(get_current_user)
):
    """刪除所有 PVP 資料"""
    try:
        from app.core.database import get_database, Collections
        
        db = get_database()
        
        # 獲取刪除前的統計資料
        total_count = await db[Collections.PVP_CHALLENGES].count_documents({})
        pending_count = await db[Collections.PVP_CHALLENGES].count_documents({
            "status": {"$in": ["pending", "waiting_accepter", "waiting_creator"]}
        })
        completed_count = await db[Collections.PVP_CHALLENGES].count_documents({
            "status": "completed"
        })
        expired_count = await db[Collections.PVP_CHALLENGES].count_documents({
            "status": "expired"
        })
        
        # 刪除所有PVP挑戰記錄
        delete_result = await db[Collections.PVP_CHALLENGES].delete_many({})
        
        logger.warning(f"Admin {current_user.get('username', 'unknown')} deleted all PVP data: {delete_result.deleted_count} records")
        
        return {
            "ok": True,
            "message": f"已刪除所有 PVP 資料，共 {delete_result.deleted_count} 筆記錄",
            "deleted_stats": {
                "total_deleted": delete_result.deleted_count,
                "pending_deleted": pending_count,
                "completed_deleted": completed_count,
                "expired_deleted": expired_count
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to delete all PVP data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除所有 PVP 資料失敗: {str(e)}"
        )


# ========== 轉點數手續費設定 ==========

@router.get(
    "/transfer/fee-config",
    responses={
        200: {"description": "手續費設定查詢成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="查詢轉點數手續費設定",
    description="查詢目前轉點數的手續費率和最低手續費設定"
)
async def get_transfer_fee_config(
    current_user: dict = Depends(get_current_user)
):
    """查詢轉點數手續費設定"""
    try:
        from app.core.database import get_database, Collections
        
        db = get_database()
        
        # 查詢手續費設定
        fee_config = await db[Collections.MARKET_CONFIG].find_one({
            "type": "transfer_fee"
        })
        
        if fee_config:
            return {
                "ok": True,
                "feeRate": fee_config.get("fee_rate", 10.0),
                "minFee": fee_config.get("min_fee", 1),
                "updatedAt": fee_config.get("updated_at").isoformat() if fee_config.get("updated_at") else None
            }
        else:
            # 如果沒有設定，回傳預設值
            return {
                "ok": True,
                "feeRate": 10.0,
                "minFee": 1,
                "updatedAt": None,
                "note": "使用預設設定（未在資料庫中設定）"
            }
        
    except Exception as e:
        logger.error(f"Failed to get transfer fee config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢手續費設定失敗"
        )


@router.post(
    "/transfer/fee-config",
    responses={
        200: {"description": "手續費設定更新成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="更新轉點數手續費設定",
    description="更新轉點數的手續費率和最低手續費設定"
)
async def update_transfer_fee_config(
    fee_rate: float = None,
    min_fee: int = None,
    current_user: dict = Depends(get_current_user)
):
    """更新轉點數手續費設定"""
    try:
        from app.core.database import get_database, Collections
        from datetime import datetime, timezone
        
        db = get_database()
        
        # 驗證參數
        if fee_rate is not None and (fee_rate < 0 or fee_rate > 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手續費率必須在 0-100% 之間"
            )
        
        if min_fee is not None and min_fee < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="最低手續費不能小於 0"
            )
        
        # 構建更新字段
        update_fields = {"updated_at": datetime.now(timezone.utc)}
        
        if fee_rate is not None:
            update_fields["fee_rate"] = fee_rate
        
        if min_fee is not None:
            update_fields["min_fee"] = min_fee
        
        if len(update_fields) == 1:  # 只有 updated_at 字段
            return {
                "ok": False,
                "message": "沒有提供任何要更新的參數"
            }
        
        # 更新手續費設定
        result = await db[Collections.MARKET_CONFIG].update_one(
            {"type": "transfer_fee"},
            {
                "$set": update_fields,
                "$setOnInsert": {
                    "type": "transfer_fee"
                }
            },
            upsert=True
        )
        
        # 取得更新後的設定
        updated_config = await db[Collections.MARKET_CONFIG].find_one(
            {"type": "transfer_fee"}
        )
        
        message_parts = []
        if fee_rate is not None:
            message_parts.append(f"手續費率: {fee_rate}%")
        if min_fee is not None:
            message_parts.append(f"最低手續費: {min_fee} 點")
        
        message = f"轉點數手續費設定已更新：{', '.join(message_parts)}" if message_parts else "轉點數手續費設定已更新"
        
        logger.info(f"Transfer fee config updated: {message}")
        
        # 傳送系統公告到 Telegram Bot
        try:
            from app.services.admin_service import AdminService
            admin_service = AdminService(db)
            
            # 構建詳細的公告訊息
            announcement_parts = []
            if fee_rate is not None:
                announcement_parts.append(f"手續費率已調整為 {fee_rate}%")
            if min_fee is not None:
                announcement_parts.append(f"最低手續費已調整為 {min_fee} 點")
            
            detailed_message = f"管理員已更新轉點數手續費設定：{', '.join(announcement_parts)}。新的手續費將立即生效。"
            
            await admin_service._send_system_announcement(
                title="💰 轉點數手續費更新",
                message=detailed_message
            )
        except Exception as e:
            logger.error(f"Failed to send transfer fee update announcement: {e}")
        
        return {
            "ok": True,
            "message": message,
            "feeRate": updated_config.get("fee_rate", 10.0),
            "minFee": updated_config.get("min_fee", 1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update transfer fee config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新手續費設定失敗"
        )


@router.post(
    "/fix-negative-stocks",
    summary="修復負股票持有量",
    description="修復系統中的負股票持有量問題，可選擇是否同時取消相關使用者的待成交賣單"
)
async def fix_negative_stocks(
    cancel_pending_orders: bool = True,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    修復負股票持有量
    
    Args:
        cancel_pending_orders: 是否同時取消相關使用者的待成交賣單（預設為 True）
        
    Returns:
        修復結果，包含修復的記錄數量和取消的訂單數量
    """
    try:
        logger.info(f"Admin {current_user.get('username')} initiated negative stock fix, cancel_orders={cancel_pending_orders}")
        
        result = await user_service.fix_negative_stocks(cancel_pending_orders)
        
        if result["success"]:
            logger.info(f"Negative stock fix completed: {result['fixed_count']} stocks fixed, {result['cancelled_orders']} orders cancelled")
        else:
            logger.warning(f"Negative stock fix partially completed: {result.get('message')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to fix negative stocks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修復負股票失敗: {str(e)}"
        )


@router.post(
    "/fix-invalid-orders",
    summary="修復無效訂單",
    description="修復系統中的無效訂單（quantity <= 0 但狀態不是 filled）"
)
async def fix_invalid_orders(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    修復無效訂單
    
    查找並修復 quantity <= 0 但狀態不是 filled 的異常訂單
    
    Returns:
        修復結果，包含修復的訂單數量和詳細訊息
    """
    try:
        logger.info(f"Admin {current_user.get('username')} initiated invalid orders fix")
        
        result = await user_service.fix_invalid_orders()
        
        if result["success"]:
            logger.info(f"Invalid orders fix completed: {result['fixed_count']} orders fixed")
        else:
            logger.warning(f"Invalid orders fix failed: {result.get('message')}")
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to fix invalid orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修復無效訂單失敗: {str(e)}"
        )


@router.get(
    "/pending-orders",
    responses={
        200: {"description": "等待撮合訂單查詢成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="查詢所有等待撮合的訂單",
    description="查詢所有狀態為等待撮合的股票訂單，包括pending、partial和pending_limit狀態的訂單"
)
async def get_pending_orders(
    limit: int = Query(100, ge=1, le=500, description="查詢筆數限制（1-500筆）"),
    current_user: dict = Depends(get_current_user)
):
    """查詢所有等待撮合的訂單
    
    Args:
        limit: 查詢筆數限制（預設100筆）
        current_user: 目前使用者（自動注入）
    
    Returns:
        等待撮合的訂單列表，包含訂單詳細資訊和使用者資訊
    """
    # 檢查查看所有使用者權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.VIEW_ALL_USERS not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要查看所有使用者權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.core.database import get_database, Collections
        from datetime import datetime, timezone
        
        db = get_database()
        
        # 查詢所有等待撮合的訂單
        pipeline = [
            # 首先篩選等待撮合的訂單
            {
                "$match": {
                    "status": {"$in": ["pending", "partial", "pending_limit"]}
                }
            },
            # 加入使用者資訊
            {
                "$lookup": {
                    "from": Collections.USERS,
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            # 解構使用者資訊陣列
            {
                "$unwind": {
                    "path": "$user_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            # 選擇需要的欄位
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "order_id": 1,
                    "user_id": {"$toString": "$user_id"},
                    "username": "$user_info.name",
                    "user_telegram_id": "$user_info.telegram_id",
                    "user_team": "$user_info.team",
                    "side": 1,
                    "order_type": 1,
                    "quantity": 1,
                    "original_quantity": 1,
                    "price": 1,
                    "status": 1,
                    "created_at": 1,
                    "updated_at": 1
                }
            },
            # 按建立時間倒序排列
            {"$sort": {"created_at": -1}},
            # 限制回傳筆數
            {"$limit": limit}
        ]
        
        # 執行聚合查詢
        orders_cursor = db[Collections.STOCK_ORDERS].aggregate(pipeline)
        orders = await orders_cursor.to_list(length=None)
        
        # 統計不同狀態的訂單數量
        status_stats = await db[Collections.STOCK_ORDERS].aggregate([
            {
                "$match": {
                    "status": {"$in": ["pending", "partial", "pending_limit"]}
                }
            },
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_quantity": {"$sum": "$quantity"}
                }
            }
        ]).to_list(length=None)
        
        # 格式化統計資料
        stats = {
            "pending": {"count": 0, "total_quantity": 0},
            "partial": {"count": 0, "total_quantity": 0},
            "pending_limit": {"count": 0, "total_quantity": 0}
        }
        
        for stat in status_stats:
            if stat["_id"] in stats:
                stats[stat["_id"]] = {
                    "count": stat["count"],
                    "total_quantity": stat["total_quantity"]
                }
        
        # 計算總計
        total_count = sum(stat["count"] for stat in stats.values())
        total_quantity = sum(stat["total_quantity"] for stat in stats.values())
        
        # 處理日期格式
        for order in orders:
            if order.get("created_at"):
                order["created_at"] = order["created_at"].isoformat() if isinstance(order["created_at"], datetime) else order["created_at"]
            if order.get("updated_at"):
                order["updated_at"] = order["updated_at"].isoformat() if isinstance(order["updated_at"], datetime) else order["updated_at"]
        
        logger.info(f"Admin {current_user.get('username')} queried pending orders: {len(orders)} orders returned")
        
        return {
            "ok": True,
            "orders": orders,
            "stats": {
                "total_orders": total_count,
                "total_quantity": total_quantity,
                "returned_count": len(orders),
                "status_breakdown": stats
            },
            "query_info": {
                "limit": limit,
                "queried_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get pending orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢等待撮合訂單失敗: {str(e)}"
        )


@router.post(
    "/trigger-matching",
    responses={
        200: {"description": "手動觸發撮合成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="手動觸發訂單撮合",
    description="立即執行一次訂單撮合，用於解決撮合延遲或測試撮合功能"
)
async def trigger_manual_matching(
    current_user: dict = Depends(get_current_user)
):
    """手動觸發訂單撮合
    
    Args:
        current_user: 目前使用者（自動注入）
    
    Returns:
        撮合執行結果
    """
    # 檢查系統管理權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.services.matching_scheduler import get_matching_scheduler
        from datetime import datetime, timezone
        
        # 獲取撮合調度器
        scheduler = get_matching_scheduler()
        if not scheduler:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="撮合調度器未初始化"
            )
        
        # 檢查調度器狀態
        scheduler_status = scheduler.get_status()
        
        start_time = datetime.now(timezone.utc)
        
        # 觸發撮合
        await scheduler.trigger_matching("admin_manual_trigger")
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Admin {current_user.get('username')} manually triggered order matching, duration: {duration:.2f}s")
        
        return {
            "ok": True,
            "message": "手動撮合執行完成",
            "execution_time": f"{duration:.2f}s",
            "triggered_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "scheduler_status": scheduler_status
        }
        
    except Exception as e:
        logger.error(f"Manual matching trigger failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"手動觸發撮合失敗: {str(e)}"
        )


@router.get(
    "/price-limit-info",
    responses={
        200: {"description": "價格限制資訊查詢成功"},
        401: {"model": ErrorResponse, "description": "未授權"},
        500: {"model": ErrorResponse, "description": "系統錯誤"}
    },
    summary="查詢價格限制資訊",
    description="查詢目前的價格限制設定和基準價格，用於診斷訂單限制問題"
)
async def get_price_limit_info(
    test_price: float = Query(14.0, description="測試價格（預設14點）"),
    current_user: dict = Depends(get_current_user)
):
    """查詢價格限制資訊
    
    Args:
        test_price: 要測試的價格
        current_user: 目前使用者（自動注入）
    
    Returns:
        價格限制的詳細資訊
    """
    # 檢查查看所有使用者權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.VIEW_ALL_USERS not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要查看所有使用者權限（目前角色：{user_role.value}）"
        )
    
    try:
        from app.services.user_service import get_user_service
        from datetime import datetime, timezone
        
        user_service = get_user_service()
        
        # 獲取價格限制資訊
        limit_info = await user_service._get_price_limit_info(test_price)
        
        # 檢查測試價格是否在限制範圍內
        is_within_limit = await user_service._check_price_limit(test_price)
        
        logger.info(f"Admin {current_user.get('username')} queried price limit info for price {test_price}")
        
        return {
            "ok": True,
            "test_price": test_price,
            "within_limit": is_within_limit,
            "limit_info": limit_info,
            "queried_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get price limit info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢價格限制資訊失敗: {str(e)}"
        )


@router.get(
    "/trades",
    response_model=List[Trade],
    responses={
        401: {"model": ErrorResponse, "description": "未授權"},
    },
    summary="查詢所有交易紀錄",
    description="查詢系統中所有的交易紀錄"
)
async def get_all_trades(
    limit: int = Query(1000, ge=1, le=5000),
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> List[Trade]:
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.VIEW_ALL_USERS not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要查看所有使用者權限（目前角色：{user_role.value}）"
        )
    
    return await admin_service.get_all_trades(limit)


@router.get(
    "/points/history",
    response_model=List[PointLog],
    responses={
        401: {"model": ErrorResponse, "description": "未授權"},
    },
    summary="查詢所有點數紀錄",
    description="查詢系統中所有的點數交易紀錄"
)
async def get_all_point_logs(
    limit: int = Query(1000, ge=1, le=5000),
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> List[PointLog]:
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.VIEW_ALL_USERS not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要查看所有使用者權限（目前角色：{user_role.value}）"
        )
    
    return await admin_service.get_all_point_logs(limit)


# 動態價格級距功能已移除，改為固定漲跌限制