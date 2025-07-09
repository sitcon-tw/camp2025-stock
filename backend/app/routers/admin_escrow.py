from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.services.escrow_service import get_escrow_service, EscrowService
from app.core.rbac import Role, check_admin_permission
from app.core.security import get_current_user
import logging

router = APIRouter(prefix="/admin/escrow", tags=["admin-escrow"])
logger = logging.getLogger(__name__)

@router.get("/user/{user_id}")
async def get_user_escrows(
    user_id: str,
    status: Optional[str] = Query(None, description="篩選狀態: active, completed, cancelled"),
    current_user: dict = Depends(get_current_user),
    escrow_service: EscrowService = Depends(get_escrow_service)
):
    """獲取用戶的圈存記錄"""
    check_admin_permission(current_user, Role.ADMIN)
    
    try:
        escrows = await escrow_service.get_user_escrows(user_id, status)
        return {
            "success": True,
            "data": escrows,
            "count": len(escrows)
        }
    except Exception as e:
        logger.error(f"Failed to get user escrows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_escrow_stats(
    current_user: dict = Depends(get_current_user),
    escrow_service: EscrowService = Depends(get_escrow_service)
):
    """獲取圈存系統統計信息"""
    check_admin_permission(current_user, Role.ADMIN)
    
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        # 統計各種狀態的圈存記錄
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_amount": {"$sum": "$amount"}
            }}
        ]
        
        status_stats = await db[Collections.ESCROWS].aggregate(pipeline).to_list(None)
        
        # 統計各種類型的圈存記錄
        type_pipeline = [
            {"$group": {
                "_id": "$type",
                "count": {"$sum": 1},
                "total_amount": {"$sum": "$amount"}
            }}
        ]
        
        type_stats = await db[Collections.ESCROWS].aggregate(type_pipeline).to_list(None)
        
        # 統計活躍圈存總額
        active_escrows = await db[Collections.ESCROWS].aggregate([
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": None,
                "total_active_amount": {"$sum": "$amount"},
                "active_count": {"$sum": 1}
            }}
        ]).to_list(None)
        
        active_total = active_escrows[0] if active_escrows else {"total_active_amount": 0, "active_count": 0}
        
        return {
            "success": True,
            "data": {
                "status_stats": status_stats,
                "type_stats": type_stats,
                "active_total": active_total["total_active_amount"],
                "active_count": active_total["active_count"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get escrow stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel/{escrow_id}")
async def cancel_escrow(
    escrow_id: str,
    reason: str = Query(..., description="取消原因"),
    current_user: dict = Depends(get_current_user),
    escrow_service: EscrowService = Depends(get_escrow_service)
):
    """管理員取消圈存記錄"""
    check_admin_permission(current_user, Role.ADMIN)
    
    try:
        success = await escrow_service.cancel_escrow(escrow_id, f"admin_cancel: {reason}")
        
        if success:
            return {
                "success": True,
                "message": f"圈存記錄 {escrow_id} 已取消"
            }
        else:
            return {
                "success": False,
                "message": "圈存取消失敗"
            }
    except Exception as e:
        logger.error(f"Failed to cancel escrow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_expired_escrows(
    max_age_hours: int = Query(24, description="過期時間（小時）"),
    current_user: dict = Depends(get_current_user),
    escrow_service: EscrowService = Depends(get_escrow_service)
):
    """清理過期的圈存記錄"""
    check_admin_permission(current_user, Role.ADMIN)
    
    try:
        cleanup_count = await escrow_service.cleanup_expired_escrows(max_age_hours)
        
        return {
            "success": True,
            "message": f"已清理 {cleanup_count} 個過期的圈存記錄",
            "cleanup_count": cleanup_count
        }
    except Exception as e:
        logger.error(f"Failed to cleanup expired escrows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_escrow_logs(
    user_id: Optional[str] = Query(None, description="用戶ID篩選"),
    limit: int = Query(100, description="限制結果數量"),
    current_user: dict = Depends(get_current_user)
):
    """獲取圈存操作日誌"""
    check_admin_permission(current_user, Role.ADMIN)
    
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        # 構建查詢條件
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        # 查詢圈存日誌
        logs_cursor = db[Collections.ESCROW_LOGS].find(query).sort("created_at", -1).limit(limit)
        logs = await logs_cursor.to_list(length=None)
        
        # 轉換ObjectId為字串
        for log in logs:
            log["_id"] = str(log["_id"])
        
        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Failed to get escrow logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def escrow_system_health(
    current_user: dict = Depends(get_current_user)
):
    """檢查圈存系統健康狀態"""
    check_admin_permission(current_user, Role.ADMIN)
    
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        # 檢查是否有長時間未處理的圈存
        from datetime import datetime, timezone, timedelta
        
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        old_active_escrows = await db[Collections.ESCROWS].find({
            "status": "active",
            "created_at": {"$lt": one_hour_ago}
        }).to_list(None)
        
        # 檢查用戶圈存金額是否與實際圈存記錄一致
        inconsistent_users = []
        
        # 使用聚合查詢找出圈存金額不一致的用戶
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": "$user_id",
                "total_escrow": {"$sum": "$amount"}
            }},
            {"$lookup": {
                "from": Collections.USERS,
                "localField": "_id",
                "foreignField": "_id",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
            {"$project": {
                "user_id": "$_id",
                "total_escrow": 1,
                "user_escrow_amount": "$user_info.escrow_amount",
                "name": "$user_info.name"
            }},
            {"$match": {
                "$expr": {"$ne": ["$total_escrow", "$user_escrow_amount"]}
            }}
        ]
        
        inconsistent_results = await db[Collections.ESCROWS].aggregate(pipeline).to_list(None)
        
        # 轉換結果
        for result in inconsistent_results:
            inconsistent_users.append({
                "user_id": str(result["user_id"]),
                "name": result["name"],
                "calculated_escrow": result["total_escrow"],
                "user_escrow_amount": result["user_escrow_amount"]
            })
        
        health_status = {
            "healthy": len(old_active_escrows) == 0 and len(inconsistent_users) == 0,
            "old_active_escrows": len(old_active_escrows),
            "inconsistent_users": len(inconsistent_users),
            "details": {
                "old_active_escrows": [str(e["_id"]) for e in old_active_escrows],
                "inconsistent_users": inconsistent_users
            }
        }
        
        return {
            "success": True,
            "data": health_status
        }
    except Exception as e:
        logger.error(f"Failed to check escrow system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))