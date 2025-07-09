# 管理功能路由 - 基於角色權限的管理 API

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.core.security import get_current_user
from app.core.rbac import (
    Permission, require_give_points_permission, require_announcement_permission,
    require_view_all_users_permission, RBACService
)
from app.services.admin_service import AdminService, get_admin_service
from app.schemas.public import (
    UserAssetDetail, GivePointsRequest, GivePointsResponse, 
    AnnouncementRequest, AnnouncementResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ========== 點數管理 ==========

@router.post(
    "/give-points",
    response_model=GivePointsResponse,
    summary="發放點數",
    description="給指定使用者或群組發放點數（需要點數管理權限）"
)
async def give_points_with_permission(
    request: GivePointsRequest,
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> GivePointsResponse:
    """
    發放點數（需要點數管理權限）
    
    權限要求：
    - point_manager: 可發放點數
    - admin: 可發放點數
    """
    # 檢查權限
    if not RBACService.has_permission(current_user, Permission.GIVE_POINTS):
        user_role = RBACService.get_user_role(current_user)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要點數管理權限（目前角色：{user_role.value}）"
        )
    
    logger.info(f"User {current_user.get('user_id', 'unknown')} giving points: {request.dict()}")
    return await admin_service.give_points(request)

# ========== 公告管理 ==========

@router.post(
    "/announcement", 
    response_model=AnnouncementResponse,
    summary="發布公告",
    description="發布系統公告（需要公告權限）"
)
async def create_announcement_with_permission(
    request: AnnouncementRequest,
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> AnnouncementResponse:
    """
    發布公告（需要公告權限）
    
    權限要求：
    - announcer: 可發布公告
    - admin: 可發布公告
    """
    # 檢查權限
    if not RBACService.has_permission(current_user, Permission.CREATE_ANNOUNCEMENT):
        user_role = RBACService.get_user_role(current_user)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要公告權限（目前角色：{user_role.value}）"
        )
    
    logger.info(f"User {current_user.get('user_id', 'unknown')} creating announcement: {request.title}")
    return await admin_service.create_announcement(request)

# ========== 使用者查詢 ==========

@router.get(
    "/users",
    response_model=List[UserAssetDetail], 
    summary="查詢使用者資產",
    description="查詢所有使用者或指定使用者的資產明細（需要查看所有使用者權限）"
)
async def get_users_with_permission(
    user: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> List[UserAssetDetail]:
    """
    查詢使用者資產（需要查看所有使用者權限）
    
    權限要求：
    - point_manager: 可查看所有使用者（用於發放點數）
    - announcer: 可查看所有使用者（用於確認對象）
    - admin: 可查看所有使用者
    """
    # 檢查權限
    if not RBACService.has_permission(current_user, Permission.VIEW_ALL_USERS):
        user_role = RBACService.get_user_role(current_user)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要查看所有使用者權限（目前角色：{user_role.value}）"
        )
    
    return await admin_service.get_user_details(user)

# ========== 權限資訊 ==========

@router.get(
    "/my-role",
    summary="查看我的角色和權限",
    description="查看目前使用者的角色和權限資訊"
)
async def get_my_role_info(
    current_user: dict = Depends(get_current_user)
):
    """查看目前使用者的角色和權限"""
    user_role = RBACService.get_user_role(current_user)
    user_permissions = RBACService.get_user_permissions(current_user)
    
    return {
        "user_id": current_user.get("user_id") or current_user.get("sub"),
        "role": user_role.value,
        "permissions": [p.value for p in user_permissions],
        "can_give_points": Permission.GIVE_POINTS in user_permissions,
        "can_create_announcement": Permission.CREATE_ANNOUNCEMENT in user_permissions,
        "can_view_all_users": Permission.VIEW_ALL_USERS in user_permissions,
        "can_manage_system": Permission.SYSTEM_ADMIN in user_permissions,
        "can_generate_qrcode": Permission.GENERATE_QRCODE in user_permissions
    }

@router.get(
    "/permissions",
    summary="列出所有可用權限",
    description="列出系統中所有可用的權限"
)
async def list_all_permissions(
    current_user: dict = Depends(get_current_user)
):
    """列出所有可用權限"""
    permissions = []
    for permission in Permission:
        permissions.append({
            "permission": permission.value,
            "description": _get_permission_description(permission)
        })
    
    return {
        "permissions": permissions,
        "user_permissions": [p.value for p in RBACService.get_user_permissions(current_user)]
    }

def _get_permission_description(permission: Permission) -> str:
    """取得權限描述"""
    descriptions = {
        Permission.VIEW_OWN_DATA: "查看自己的資料",
        Permission.TRADE_STOCKS: "股票交易",
        Permission.TRANSFER_POINTS: "轉帳點數",
        Permission.VIEW_ALL_USERS: "查看所有使用者",
        Permission.GIVE_POINTS: "發放點數",
        Permission.CREATE_ANNOUNCEMENT: "發布公告",
        Permission.MANAGE_USERS: "管理使用者",
        Permission.MANAGE_MARKET: "管理市場",
        Permission.SYSTEM_ADMIN: "系統管理"
    }
    return descriptions.get(permission, "未知權限")