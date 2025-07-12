"""
Admin endpoints for managing rate limiting and Fail2Ban system
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user
from app.core.rbac import RBACService, Permission, ROLE_PERMISSIONS
from app.middleware.rate_limiter import rate_limiter
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/rate-limit/stats",
    summary="獲取 Rate Limiting 統計",
    description="查看目前的 IP 封鎖狀態、失敗嘗試次數等統計資訊"
)
async def get_rate_limit_stats(
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """獲取 Rate Limiting 統計資訊"""
    
    # 檢查管理員權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    return rate_limiter.get_stats()

@router.post(
    "/rate-limit/unban/{ip}",
    summary="解除 IP 封鎖",
    description="手動解除特定 IP 的封鎖狀態"
)
async def unban_ip(
    ip: str,
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """手動解除 IP 封鎖"""
    
    # 檢查管理員權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    # 檢查 IP 是否在封鎖清單中
    if ip not in rate_limiter.banned_ips:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IP {ip} 不在封鎖清單中"
        )
    
    # 解除封鎖
    del rate_limiter.banned_ips[ip]
    
    # 清理該 IP 的失敗嘗試記錄
    if ip in rate_limiter.failed_attempts:
        rate_limiter.failed_attempts[ip].clear()
    
    logger.info(f"Admin manually unbanned IP {ip}")
    
    return {
        "success": True,
        "message": f"IP {ip} 已解除封鎖",
        "unbanned_ip": ip
    }

@router.get(
    "/rate-limit/banned-ips",
    summary="獲取封鎖 IP 清單",
    description="查看目前所有被封鎖的 IP 地址"
)
async def get_banned_ips(
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """獲取封鎖 IP 清單"""
    
    # 檢查管理員權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    import time
    current_time = time.time()
    
    # 獲取活躍的封鎖清單
    active_bans = []
    for ip, ban_time in rate_limiter.banned_ips.items():
        remaining_time = int(rate_limiter.ban_duration_seconds - (current_time - ban_time))
        if remaining_time > 0:
            active_bans.append({
                "ip": ip,
                "banned_at": ban_time,
                "remaining_seconds": remaining_time
            })
    
    return {
        "total_banned": len(active_bans),
        "banned_ips": active_bans,
        "ban_duration_seconds": rate_limiter.ban_duration_seconds,
        "max_attempts": rate_limiter.max_attempts,
        "window_seconds": rate_limiter.window_seconds
    }

@router.post(
    "/rate-limit/clear-all-bans",
    summary="清除所有 IP 封鎖",
    description="清除所有被封鎖的 IP 地址（緊急用途）"
)
async def clear_all_bans(
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """清除所有 IP 封鎖"""
    
    # 檢查管理員權限
    user_role = await RBACService.get_user_role_from_db(current_user)
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    
    if Permission.SYSTEM_ADMIN not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要系統管理權限（目前角色：{user_role.value}）"
        )
    
    banned_count = len(rate_limiter.banned_ips)
    
    # 清除所有封鎖
    rate_limiter.banned_ips.clear()
    rate_limiter.failed_attempts.clear()
    
    logger.warning(f"Admin cleared all IP bans ({banned_count} IPs unbanned)")
    
    return {
        "success": True,
        "message": f"已清除所有 IP 封鎖",
        "cleared_count": banned_count
    }