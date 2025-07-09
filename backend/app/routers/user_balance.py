from fastapi import APIRouter, Depends, HTTPException
from app.services.user_service import get_user_service, UserService
from app.core.security import get_current_user
from pydantic import BaseModel, Field
from typing import Optional
import logging

router = APIRouter(prefix="/user/balance", tags=["user-balance"])
logger = logging.getLogger(__name__)

class UserBalanceDetail(BaseModel):
    """用戶餘額詳情"""
    username: str = Field(..., description="使用者名稱")
    available_points: int = Field(..., description="可用餘額", alias="availablePoints")
    escrow_amount: int = Field(..., description="圈存金額", alias="escrowAmount")
    total_balance: int = Field(..., description="總餘額 (可用+圈存)", alias="totalBalance")
    
    class Config:
        populate_by_name = True

@router.get("/detail", response_model=UserBalanceDetail)
async def get_user_balance_detail(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """獲取用戶詳細餘額信息"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="無效的使用者ID")
        
        from app.core.database import get_database, Collections
        from bson import ObjectId
        
        db = get_database()
        user_oid = ObjectId(user_id)
        
        # 獲取用戶資料
        user = await db[Collections.USERS].find_one({"_id": user_oid})
        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")
        
        available_points = user.get("points", 0)
        escrow_amount = user.get("escrow_amount", 0)
        total_balance = available_points + escrow_amount
        
        return UserBalanceDetail(
            username=user.get("name", user.get("id", "Unknown")),
            availablePoints=available_points,
            escrowAmount=escrow_amount,
            totalBalance=total_balance
        )
        
    except Exception as e:
        logger.error(f"Failed to get user balance detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/escrows")
async def get_user_escrows(
    current_user: dict = Depends(get_current_user)
):
    """獲取用戶的圈存記錄"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="無效的使用者ID")
        
        from app.services.escrow_service import get_escrow_service
        escrow_service = get_escrow_service()
        
        # 獲取用戶所有圈存記錄
        escrows = await escrow_service.get_user_escrows(user_id)
        
        # 計算統計信息
        active_escrows = [e for e in escrows if e.get("status") == "active"]
        total_active_amount = sum(e.get("amount", 0) for e in active_escrows)
        
        return {
            "success": True,
            "data": {
                "escrows": escrows,
                "statistics": {
                    "total_escrows": len(escrows),
                    "active_escrows": len(active_escrows),
                    "total_active_amount": total_active_amount
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user escrows: {e}")
        raise HTTPException(status_code=500, detail=str(e))