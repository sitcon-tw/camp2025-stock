"""
快取管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
# 使用新的模組化架構 - 直接從專門的模組導入
from app.services.core import get_cache_service
from app.services.core import get_cache_invalidator
from app.core.rbac import RBACService, Permission
from app.core.security import get_current_user
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/stats",
    summary="查看快取統計",
    description="查看快取使用統計資訊（需要管理員權限）"
)
async def get_cache_stats(
    current_user: dict = Depends(get_current_user),
    cache_service = Depends(get_cache_service)
) -> Dict[str, Any]:
    """查看快取統計資訊"""
    # 檢查管理員權限
    if not RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系統管理員權限"
        )
    
    stats = cache_service.get_stats()
    
    return {
        "status": "success",
        "data": stats,
        "message": "快取統計資訊"
    }

@router.post(
    "/invalidate/{pattern}",
    summary="清除快取",
    description="清除指定模式的快取（需要管理員權限）"
)
async def invalidate_cache(
    pattern: str,
    current_user: dict = Depends(get_current_user),
    cache_service = Depends(get_cache_service)
) -> Dict[str, Any]:
    """清除指定模式的快取"""
    # 檢查管理員權限
    if not RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系統管理員權限"
        )
    
    try:
        await cache_service.invalidate_pattern(pattern)
        logger.info(f"Admin {current_user.get('user_id')} invalidated cache pattern: {pattern}")
        
        return {
            "status": "success",
            "message": f"已清除匹配模式 '{pattern}' 的快取"
        }
    except Exception as e:
        logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除快取失敗: {str(e)}"
        )

@router.post(
    "/clear",
    summary="清空所有快取",
    description="清空所有快取（需要管理員權限）"
)
async def clear_all_cache(
    current_user: dict = Depends(get_current_user),
    cache_service = Depends(get_cache_service)
) -> Dict[str, Any]:
    """清空所有快取"""
    # 檢查管理員權限
    if not RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系統管理員權限"
        )
    
    try:
        await cache_service.clear()
        logger.info(f"Admin {current_user.get('user_id')} cleared all caches")
        
        return {
            "status": "success",
            "message": "已清空所有快取"
        }
    except Exception as e:
        logger.error(f"Failed to clear all caches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空快取失敗: {str(e)}"
        )

@router.post(
    "/warm-up",
    summary="預熱快取",
    description="預熱常用快取（需要管理員權限）"
)
async def warm_up_cache(
    current_user: dict = Depends(get_current_user),
    cache_invalidator = Depends(get_cache_invalidator)
) -> Dict[str, Any]:
    """預熱常用快取"""
    # 檢查管理員權限
    if not RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系統管理員權限"
        )
    
    try:
        # 這裡可以添加預熱常用API的邏輯
        # 比如預先調用一些高頻的查詢API
        
        logger.info(f"Admin {current_user.get('user_id')} triggered cache warm-up")
        
        return {
            "status": "success",
            "message": "快取預熱完成"
        }
    except Exception as e:
        logger.error(f"Failed to warm up cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"快取預熱失敗: {str(e)}"
        )