from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_bot_token
from app.schemas.arcade import ArcadeActionRequest, ArcadeActionResponse, ArcadeHealthResponse, ArcadePointsRequest
from app.services import UserService, get_user_service
from app.core.database import Collections
from bson import ObjectId
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/arcade/deduct", response_model=ArcadeActionResponse, deprecated=True)
async def arcade_deduct_points(
    request: ArcadeActionRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> ArcadeActionResponse:
    """遊戲廳扣除點數 (已棄用，請使用 /arcade/points)"""
    try:
        # 根據username獲取使用者ID
        user = await user_service.db[Collections.USERS].find_one({
            "$or": [
                {"name": request.from_user},
                {"id": request.from_user}
            ]
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {request.from_user}"
            )
        
        # 產生交易ID
        transaction_id = str(uuid.uuid4())
        
        # 準備操作備註
        operation_note = f"遊戲廳扣款 - 遊戲類型: {request.game_type}"
        if request.note:
            operation_note += f", 備註: {request.note}"
        
        # 使用UserService的安全扣除方法
        result = await user_service._safe_deduct_points(
            user_id=user["_id"],
            amount=request.amount,
            operation_note=operation_note,
            change_type="arcade_deduct",
            transaction_id=transaction_id
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        
        logger.info(f"Arcade deduct successful: user {request.from_user}, amount {request.amount}, game {request.game_type}")
        
        return ArcadeActionResponse(
            success=True,
            message=f"成功扣除 {request.amount} 點",
            balance_before=result['balance_before'],
            balance_after=result['balance_after'],
            transaction_id=transaction_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Arcade deduct failed: user {request.from_user}, amount {request.amount}, error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="遊戲廳扣款失敗"
        )

@router.post("/arcade/add", response_model=ArcadeActionResponse, deprecated=True)
async def arcade_add_points(
    request: ArcadeActionRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> ArcadeActionResponse:
    """遊戲廳增加點數 (已棄用，請使用 /arcade/points)"""
    try:
        # 根據username獲取使用者ID
        user = await user_service.db[Collections.USERS].find_one({
            "$or": [
                {"name": request.from_user},
                {"id": request.from_user}
            ]
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {request.from_user}"
            )
        
        # 產生交易ID
        transaction_id = str(uuid.uuid4())
        
        # 準備操作備註
        operation_note = f"遊戲廳加款 - 遊戲類型: {request.game_type}"
        if request.note:
            operation_note += f", 備註: {request.note}"
        
        # 獲取操作前餘額
        balance_before = user.get("points", 0)
        
        # 檢查帳戶狀態
        if not user.get("enabled", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="帳戶未啟用"
            )
        
        if user.get("frozen", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="帳戶已凍結，無法進行操作"
            )
        
        # 檢查是否有欠款，優先償還欠款
        current_owed = user.get("owed_points", 0)
        
        if current_owed > 0:
            # 有欠款，優先償還
            current_points = user.get("points", 0)
            
            # 總可用於償還的金額 = 現有點數 + 新給予的點數
            total_available = current_points + request.amount
            
            # 計算實際償還金額（不能超過欠款總額）
            actual_repay = min(total_available, current_owed)
            
            # 計算償還後剩餘的點數
            remaining_points = total_available - actual_repay
            
            # 更新邏輯：
            # 1. 將現有點數歸零
            # 2. 減少相應的欠款
            # 3. 設定剩餘點數（如果有的話）
            update_doc = {
                "$set": {"points": remaining_points},
                "$inc": {"owed_points": -actual_repay}
            }
            
            # 如果完全償還欠款，解除凍結
            if actual_repay >= current_owed:
                update_doc["$set"]["frozen"] = False
            
            await user_service.db[Collections.USERS].update_one(
                {"_id": user["_id"]},
                update_doc
            )
            
            # 記錄償還訊息
            if actual_repay > 0:
                repay_note = f"遊戲廳加款 {request.amount} 點 + 現有 {current_points} 點，共償還欠款: {actual_repay} 點"
                await user_service._log_point_change(
                    user["_id"],
                    "debt_repayment",
                    actual_repay,
                    repay_note,
                    transaction_id
                )
            
            # 記錄剩餘點數（如果有）
            if remaining_points > 0:
                await user_service._log_point_change(
                    user["_id"],
                    "arcade_add",
                    remaining_points,
                    f"償還欠款後剩餘點數: {remaining_points} 點 - {operation_note}",
                    transaction_id
                )
            
            balance_after = remaining_points
        else:
            # 沒有欠款，直接增加點數
            await user_service.db[Collections.USERS].update_one(
                {"_id": user["_id"]},
                {"$inc": {"points": request.amount}}
            )
            
            # 記錄點數變化
            await user_service._log_point_change(
                user["_id"],
                "arcade_add",
                request.amount,
                operation_note,
                transaction_id
            )
            
            balance_after = balance_before + request.amount
        
        logger.info(f"Arcade add successful: user {request.from_user}, amount {request.amount}, game {request.game_type}")
        
        return ArcadeActionResponse(
            success=True,
            message=f"成功增加 {request.amount} 點",
            balance_before=balance_before,
            balance_after=balance_after,
            transaction_id=transaction_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Arcade add failed: user {request.from_user}, amount {request.amount}, error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="遊戲廳加款失敗"
        )

@router.post("/arcade/points", response_model=ArcadeActionResponse)
async def arcade_manage_points(
    request: ArcadePointsRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> ArcadeActionResponse:
    """遊戲廳點數管理（支持加點和扣點）"""
    try:
        # 根據username獲取使用者ID
        user = await user_service.db[Collections.USERS].find_one({
            "$or": [
                {"name": request.from_user},
                {"id": request.from_user}
            ]
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {request.from_user}"
            )
        
        # 產生交易ID
        transaction_id = str(uuid.uuid4())
        
        # 判斷是加點還是扣點
        if request.amount > 0:
            # 加點邏輯
            operation_note = f"遊戲廳加款 - 遊戲類型: {request.game_type}"
            if request.note:
                operation_note += f", 備註: {request.note}"
            
            # 獲取操作前餘額
            balance_before = user.get("points", 0)
            
            # 檢查帳戶狀態
            if not user.get("enabled", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="帳戶未啟用"
                )
            
            if user.get("frozen", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="帳戶已凍結，無法進行操作"
                )
            
            # 檢查是否有欠款，優先償還欠款
            current_owed = user.get("owed_points", 0)
            
            if current_owed > 0:
                # 有欠款，優先償還
                current_points = user.get("points", 0)
                total_available = current_points + request.amount
                actual_repay = min(total_available, current_owed)
                remaining_points = total_available - actual_repay
                
                update_doc = {
                    "$set": {"points": remaining_points},
                    "$inc": {"owed_points": -actual_repay}
                }
                
                if actual_repay >= current_owed:
                    update_doc["$set"]["frozen"] = False
                
                await user_service.db[Collections.USERS].update_one(
                    {"_id": user["_id"]},
                    update_doc
                )
                
                if actual_repay > 0:
                    repay_note = f"遊戲廳加款 {request.amount} 點 + 現有 {current_points} 點，共償還欠款: {actual_repay} 點"
                    await user_service._log_point_change(
                        user["_id"],
                        "debt_repayment",
                        actual_repay,
                        repay_note,
                        transaction_id
                    )
                
                if remaining_points > 0:
                    await user_service._log_point_change(
                        user["_id"],
                        "arcade_add",
                        remaining_points,
                        f"償還欠款後剩餘點數: {remaining_points} 點 - {operation_note}",
                        transaction_id
                    )
                
                balance_after = remaining_points
            else:
                # 沒有欠款，直接增加點數
                await user_service.db[Collections.USERS].update_one(
                    {"_id": user["_id"]},
                    {"$inc": {"points": request.amount}}
                )
                
                await user_service._log_point_change(
                    user["_id"],
                    "arcade_add",
                    request.amount,
                    operation_note,
                    transaction_id
                )
                
                balance_after = balance_before + request.amount
            
            message = f"成功增加 {request.amount} 點"
        
        else:
            # 扣點邏輯 (amount < 0)
            deduct_amount = abs(request.amount)  # 轉為正數處理
            operation_note = f"遊戲廳扣款 - 遊戲類型: {request.game_type}"
            if request.note:
                operation_note += f", 備註: {request.note}"
            
            # 使用UserService的安全扣除方法
            result = await user_service._safe_deduct_points(
                user_id=user["_id"],
                amount=deduct_amount,
                operation_note=operation_note,
                change_type="arcade_deduct",
                transaction_id=transaction_id
            )
            
            if not result['success']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result['message']
                )
            
            balance_before = result['balance_before']
            balance_after = result['balance_after']
            message = f"成功扣除 {deduct_amount} 點"
        
        logger.info(f"Arcade points operation successful: user {request.from_user}, amount {request.amount}, game {request.game_type}")
        
        return ArcadeActionResponse(
            success=True,
            message=message,
            balance_before=balance_before,
            balance_after=balance_after,
            transaction_id=transaction_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        operation_type = "加款" if request.amount > 0 else "扣款"
        logger.error(f"Arcade {operation_type} failed: user {request.from_user}, amount {request.amount}, error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"遊戲廳{operation_type}失敗"
        )

@router.get("/arcade/health", response_model=ArcadeHealthResponse)
async def arcade_health_check() -> ArcadeHealthResponse:
    """遊戲廳 API 健康檢查"""
    return ArcadeHealthResponse(
        status="healthy",
        service="Arcade API",
        message="遊戲廳 API 運行正常"
    )