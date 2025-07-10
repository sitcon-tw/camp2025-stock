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
    """獲取使用者的圈存記錄"""
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
    user_id: Optional[str] = Query(None, description="使用者ID篩選"),
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
        
        # 檢查使用者圈存金額是否與實際圈存記錄一致
        inconsistent_users = []
        
        # 使用聚合查詢找出圈存金額不一致的使用者
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

@router.post("/refund-all")
async def refund_all_escrows(
    current_user: dict = Depends(get_current_user),
    escrow_service: EscrowService = Depends(get_escrow_service)
):
    """
    退還所有活躍的圈存金額
    這是一個危險的管理員操作，會取消所有正在進行的圈存並退款
    """
    from app.core.rbac import RBACService, Permission
    if not RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN):
        raise HTTPException(status_code=403, detail="權限不足：需要系統管理權限")
    
    try:
        from app.core.database import get_database, Collections
        db = get_database()
        
        logger.info(f"管理員 {current_user.get('username', 'unknown')} 開始執行退還所有圈存操作")
        
        # 獲取所有活躍的圈存記錄
        active_escrows = await db[Collections.ESCROWS].find({
            "status": "active"
        }).to_list(None)
        
        if not active_escrows:
            return {
                "success": True,
                "message": "沒有需要退還的圈存記錄",
                "refunded_count": 0,
                "total_refunded_amount": 0
            }
        
        # 統計信息
        refunded_count = 0
        failed_count = 0
        total_refunded_amount = 0
        failed_escrows = []
        
        # 逐一退還圈存
        for escrow in active_escrows:
            try:
                escrow_id = str(escrow.get("_id"))
                amount = escrow.get("amount", 0)
                user_id = escrow.get("user_id")
                escrow_type = escrow.get("type", "unknown")
                
                # 取消圈存
                success = await escrow_service.cancel_escrow(
                    escrow_id=escrow_id,
                    reason="管理員執行批量退還操作"
                )
                
                if success:
                    refunded_count += 1
                    total_refunded_amount += amount
                    logger.info(f"成功退還圈存: {escrow_id}, 用戶: {user_id}, 金額: {amount}, 類型: {escrow_type}")
                else:
                    failed_count += 1
                    failed_escrows.append({
                        "escrow_id": escrow_id,
                        "user_id": str(user_id),
                        "amount": amount,
                        "type": escrow_type,
                        "reason": "取消操作失敗"
                    })
                    logger.warning(f"退還圈存失敗: {escrow_id}, 用戶: {user_id}")
                    
            except Exception as escrow_error:
                failed_count += 1
                failed_escrows.append({
                    "escrow_id": str(escrow.get("_id", "unknown")),
                    "user_id": str(escrow.get("user_id", "unknown")),
                    "amount": escrow.get("amount", 0),
                    "type": escrow.get("type", "unknown"),
                    "reason": str(escrow_error)
                })
                logger.error(f"處理圈存 {escrow.get('_id')} 時發生錯誤: {escrow_error}")
        
        logger.info(f"批量退還圈存完成 - 成功: {refunded_count}, 失敗: {failed_count}, 總退還金額: {total_refunded_amount}")
        
        return {
            "success": True,
            "message": f"批量退還操作完成",
            "refunded_count": refunded_count,
            "failed_count": failed_count,
            "total_refunded_amount": total_refunded_amount,
            "failed_escrows": failed_escrows if failed_escrows else None
        }
        
    except Exception as e:
        logger.error(f"批量退還圈存操作失敗: {e}")
        raise HTTPException(status_code=500, detail=f"批量退還操作失敗: {str(e)}")

@router.post("/refund-user/{user_id}")
async def refund_user_escrows(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    escrow_service: EscrowService = Depends(get_escrow_service)
):
    """
    退還特定使用者的所有圈存金額
    """
    from app.core.rbac import RBACService, Permission
    if not RBACService.has_permission(current_user, Permission.VIEW_ALL_USERS):
        raise HTTPException(status_code=403, detail="權限不足：需要查看所有使用者權限")
    
    try:
        logger.info(f"管理員 {current_user.get('username', 'unknown')} 開始退還使用者 {user_id} 的圈存")
        
        # 獲取該使用者的所有活躍圈存
        user_escrows = await escrow_service.get_user_escrows(user_id, "active")
        
        if not user_escrows:
            return {
                "success": True,
                "message": f"使用者 {user_id} 沒有需要退還的圈存記錄",
                "refunded_count": 0,
                "total_refunded_amount": 0
            }
        
        refunded_count = 0
        failed_count = 0
        total_refunded_amount = 0
        failed_escrows = []
        
        # 退還該使用者的所有圈存
        for escrow in user_escrows:
            try:
                escrow_id = str(escrow.get("_id"))
                amount = escrow.get("amount", 0)
                escrow_type = escrow.get("type", "unknown")
                
                success = await escrow_service.cancel_escrow(
                    escrow_id=escrow_id,
                    reason=f"管理員退還使用者 {user_id} 的圈存"
                )
                
                if success:
                    refunded_count += 1
                    total_refunded_amount += amount
                    logger.info(f"成功退還使用者圈存: {escrow_id}, 金額: {amount}, 類型: {escrow_type}")
                else:
                    failed_count += 1
                    failed_escrows.append({
                        "escrow_id": escrow_id,
                        "amount": amount,
                        "type": escrow_type,
                        "reason": "取消操作失敗"
                    })
                    
            except Exception as escrow_error:
                failed_count += 1
                failed_escrows.append({
                    "escrow_id": str(escrow.get("_id", "unknown")),
                    "amount": escrow.get("amount", 0),
                    "type": escrow.get("type", "unknown"),
                    "reason": str(escrow_error)
                })
                logger.error(f"處理使用者圈存時發生錯誤: {escrow_error}")
        
        logger.info(f"使用者 {user_id} 圈存退還完成 - 成功: {refunded_count}, 失敗: {failed_count}")
        
        return {
            "success": True,
            "message": f"使用者 {user_id} 的圈存退還完成",
            "user_id": user_id,
            "refunded_count": refunded_count,
            "failed_count": failed_count,
            "total_refunded_amount": total_refunded_amount,
            "failed_escrows": failed_escrows if failed_escrows else None
        }
        
    except Exception as e:
        logger.error(f"退還使用者 {user_id} 圈存失敗: {e}")
        raise HTTPException(status_code=500, detail=f"退還使用者圈存失敗: {str(e)}")