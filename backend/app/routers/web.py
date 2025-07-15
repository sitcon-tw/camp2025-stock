from fastapi import APIRouter, Depends, HTTPException, status
from app.services import UserService, get_user_service
from app.services.admin_service import AdminService, get_admin_service
from app.schemas.user import (
    UserPortfolio, StockOrderRequest, StockOrderResponse,
    TransferRequest, TransferResponse, UserPointLog, UserStockOrder, UserBasicInfo
)
from app.schemas.public import UserAssetDetail, ErrorResponse, QRCodeRedeemRequest, QRCodeRedeemResponse, GivePointsRequest, PointLog
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.security import get_current_user
from app.core.rbac import RBACService, Permission
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== QR Code 管理 Schemas ==========

class QRCodeCreateRequest(BaseModel):
    qr_data: str = Field(..., description="QR Code 資料")
    points: int = Field(..., description="點數數量")

class QRCodeRecord(BaseModel):
    id: str = Field(..., description="QR Code ID")
    qr_data: str = Field(..., description="QR Code 資料")
    points: int = Field(..., description="點數數量")
    created_at: datetime = Field(..., description="創建時間")
    used: bool = Field(default=False, description="是否已使用")
    used_by: Optional[str] = Field(None, description="使用者ID")
    used_at: Optional[datetime] = Field(None, description="使用時間")
    created_by: str = Field(..., description="創建者ID")


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
        user_id = current_user.get("user_id")
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
        logger.error(
            f"Failed to get portfolio for user {current_user.get('user_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得投資組合資訊"
        )


@router.get(
    "/points/history",
    response_model=List[PointLog],
    summary="查詢所有點數記錄",
    description="查詢整個系統的點數變動記錄"
)
async def get_point_history(
    limit: int = None,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> List[PointLog]:
    """
    查詢所有點數記錄

    Args:
        limit: 查詢筆數限制（None 表示無限制，返回所有記錄）
        current_user: 目前使用者資訊（從 JWT Token 解析）
        user_service: 使用者服務（自動注入）

    Returns:
        點數變動記錄列表
    """
    try:
        # 驗證使用者身份
        if not current_user.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的使用者 Token"
            )

        # 使用簡化版查詢來避免聚合管道timeout問題
        logs = await user_service.get_all_point_logs_simple(limit)
        
        # 轉換為 PointLog 格式，確保所有欄位都有有效值
        from datetime import datetime, timezone
        
        result = []
        for log in logs:
            # 確保 created_at 有效
            created_at = log.get("created_at")
            if created_at is None:
                created_at = datetime.now(timezone.utc)
            elif isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = datetime.now(timezone.utc)
            
            try:
                point_log = PointLog(
                    user_id=log.get("user_id", ""),
                    user_name=log.get("user_name", "Unknown"),
                    type=log.get("type", "unknown"),
                    amount=log.get("amount", 0),
                    note=log.get("note", ""),
                    created_at=created_at,
                    balance_after=log.get("balance_after", 0),
                    transfer_partner=log.get("transfer_partner"),
                    transaction_id=log.get("transaction_id", "")
                )
                result.append(point_log)
            except Exception as e:
                # 記錄有問題的資料但不中斷整個請求
                logger.warning(f"Skipping invalid point log record: {e}, log: {log}")
                continue
        
        return result

    except Exception as e:
        logger.error(
            f"Failed to get point history for user {current_user.get('user_id')}: {e}")
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
        user_id = current_user.get("user_id")
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
        logger.error(
            f"Failed to place order for user {current_user.get('user_id')}: {e}")
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
        user_id = current_user.get("user_id")
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
        logger.error(
            f"Failed to get stock orders for user {current_user.get('user_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得股票訂單記錄"
        )


@router.delete(
    "/stock/orders/{order_id}",
    response_model=dict,
    summary="取消股票訂單",
    description="取消指定的股票訂單"
)
async def cancel_stock_order(
    order_id: str,
    reason: str = "user_cancelled",
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> dict:
    """
    取消股票訂單
    
    Args:
        order_id: 訂單 ID
        reason: 取消原因
        current_user: 目前使用者（透過 JWT Token 取得）
        user_service: 使用者服務
        
    Returns:
        取消結果
        
    Raises:
        HTTPException: 當取消失敗時
    """
    try:
        user_id = current_user.get("user_id")
        telegram_id = current_user.get("telegram_id")
        
        logger.info(f"取消訂單 - JWT Token 內容: user_id={user_id}, telegram_id={telegram_id}")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT Token 中缺少 user_id"
            )
        
        logger.info(f"取消訂單 - 使用 JWT 中的 user_id: {user_id}")
        
        # 呼叫取消訂單方法
        result = await user_service.cancel_stock_order(user_id, order_id, reason)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "取消訂單失敗")
            )
        
        return result
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id} for user {current_user.get('user_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "取消訂單時發生錯誤"
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
        user_id = current_user.get("user_id")
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
        logger.error(
            f"Failed to transfer points for user {current_user.get('user_id')}: {e}")
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
        user_id = current_user.get("user_id")
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
        logger.error(
            f"Failed to get profile for user {current_user.get('user_id')}: {e}")
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
        logger.error(
            f"Failed to get users for user {current_user.get('user_id')}: {e}")
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
        logger.error(
            f"Failed to get students for user {current_user.get('user_id')}: {e}")
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
        logger.error(
            f"Failed to get teams for user {current_user.get('user_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "無法取得隊伍資料"
        )


# ========== QR Code 兌換 ==========

@router.post(
    "/qr/redeem",
    response_model=QRCodeRedeemResponse,
    summary="QR Code 兌換點數",
    description="使用 QR Code 兌換點數"
)
async def redeem_qr_code(
    request: QRCodeRedeemRequest,
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> QRCodeRedeemResponse:
    """
    QR Code 兌換點數
    
    Args:
        request: QR Code 兌換請求
        current_user: 目前使用者資訊（從 JWT Token 解析）
        admin_service: 管理員服務（自動注入）
        
    Returns:
        兌換結果
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
        
        # 檢查 QR Code 記錄是否存在且未使用
        qr_record = await db[Collections.QR_CODES].find_one({"id": qr_id})
        
        if not qr_record:
            return QRCodeRedeemResponse(
                ok=False,
                message="無效的 QR Code"
            )
        
        if qr_record.get("used", False):
            return QRCodeRedeemResponse(
                ok=False,
                message=f"此 QR Code 已經被 {qr_record.get('used_by', '其他人')} 兌換過了"
            )
        
        # 給予點數
        give_points_request = GivePointsRequest(
            username=current_user["user_id"],
            type="user",
            amount=points
        )
        
        # 給予點數
        await admin_service.give_points(give_points_request)
        
        # 標記 QR Code 為已使用
        await db[Collections.QR_CODES].update_one(
            {"id": qr_id},
            {
                "$set": {
                    "used": True,
                    "used_by": current_user["user_id"],
                    "used_at": datetime.now()
                }
            }
        )
        
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


# ========== QR Code 管理 API ==========

@router.post(
    "/qr/create",
    response_model=QRCodeRecord,
    summary="創建 QR Code 記錄",
    description="創建並保存 QR Code 記錄到資料庫"
)
async def create_qr_code(
    request: QRCodeCreateRequest,
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> QRCodeRecord:
    """
    創建 QR Code 記錄
    
    Args:
        request: QR Code 創建請求
        current_user: 目前使用者資訊（從 JWT Token 解析）
        admin_service: 管理員服務（自動注入）
        
    Returns:
        創建的 QR Code 記錄
    """
    import json
    
    # 檢查權限
    if not RBACService.has_permission(current_user, Permission.GENERATE_QRCODE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足：需要 QR Code 生成權限"
        )
    
    # 驗證點數範圍
    if not isinstance(request.points, int) or request.points < 1 or request.points > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="點數必須在 1-1000 範圍內"
        )
    
    try:
        # 解析 QR Code 資料以驗證格式
        qr_data = json.loads(request.qr_data)
        qr_id = qr_data.get("id")
        qr_type = qr_data.get("type")
        qr_points = qr_data.get("points")
        
        if not qr_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR Code 資料中缺少 ID"
            )
        
        # 驗證 QR Code 資料結構
        if qr_type != "points_redeem":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR Code 類型必須為 points_redeem"
            )
        
        if qr_points != request.points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR Code 資料中的點數與請求點數不一致"
            )
        
        # 保存到資料庫
        from app.core.database import get_database, Collections
        db = get_database()
        
        qr_record = {
            "id": qr_id,
            "qr_data": request.qr_data,
            "points": request.points,
            "created_at": datetime.now(),
            "used": False,
            "used_by": None,
            "used_at": None,
            "created_by": current_user["user_id"]
        }
        
        await db[Collections.QR_CODES].insert_one(qr_record)
        
        return QRCodeRecord(**qr_record)
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR Code 格式錯誤"
        )
    except Exception as e:
        logger.error(f"創建 QR Code 記錄失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建 QR Code 記錄失敗"
        )


@router.get(
    "/qr/list",
    response_model=List[QRCodeRecord],
    summary="查詢 QR Code 記錄",
    description="查詢所有 QR Code 記錄及使用狀況"
)
async def list_qr_codes(
    limit: int = 100,
    used: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
) -> List[QRCodeRecord]:
    """
    查詢 QR Code 記錄列表
    
    Args:
        limit: 查詢筆數限制（預設 100）
        used: 篩選條件：True=已使用, False=未使用, None=全部
        current_user: 目前使用者資訊（從 JWT Token 解析）
        
    Returns:
        QR Code 記錄列表
    """
    # 檢查權限 - 只有有 QR Code 權限的用戶才能查看所有記錄，否則只能查看自己創建的
    has_qr_permission = RBACService.has_permission(current_user, Permission.GENERATE_QRCODE)
    
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        # 構建查詢條件
        query = {}
        if not has_qr_permission:
            # 沒有 QR Code 權限的用戶只能查看自己創建的記錄
            query["created_by"] = current_user["user_id"]
        
        if used is not None:
            query["used"] = used
        
        # 查詢記錄
        cursor = db[Collections.QR_CODES].find(query).sort("created_at", -1).limit(limit)
        records = await cursor.to_list(length=limit)
        
        # 轉換為 Pydantic 模型
        qr_records = []
        for record in records:
            # 移除 MongoDB 的 _id 字段
            record.pop("_id", None)
            qr_records.append(QRCodeRecord(**record))
        
        return qr_records
        
    except Exception as e:
        logger.error(f"查詢 QR Code 記錄失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢 QR Code 記錄失敗"
        )


# ========== 使用者大頭照 API ==========

@router.get(
    "/users/{username}/avatar",
    summary="獲取使用者大頭照",
    description="根據使用者名獲取使用者的大頭照 URL"
)
async def get_user_avatar(
    username: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> dict:
    """
    獲取指定使用者的大頭照 URL
    
    Args:
        username: 使用者名
        current_user: 目前使用者（透過 JWT Token 取得）
        user_service: 使用者服務
        
    Returns:
        包含大頭照 URL 的字典
        
    Raises:
        HTTPException: 當使用者不存在或獲取失敗時
    """
    try:
        # 獲取使用者資訊
        user = await user_service._get_user_(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"使用者 {username} 不存在"
            )
        
        return {
            "username": username,
            "display_name": user.get("name") or user.get("username") or username,
            "photo_url": user.get("photo_url"),
            "has_avatar": user.get("photo_url") is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get avatar for user {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取使用者大頭照"
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
