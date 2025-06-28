# RBAC 管理 API 端點

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.security import get_current_user
from app.core.rbac import (
    Role, Permission, RBACService, 
    require_system_admin_permission, require_admin_role
)
from app.services.rbac_service import RBACManagementService, get_rbac_management_service
from app.schemas.rbac import (
    UserRoleInfo, RoleUpdateRequest, RoleUpdateResponse,
    PermissionCheckRequest, PermissionCheckResponse,
    RoleListResponse, UserPermissionSummary
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ========== 角色管理 ==========

@router.get(
    "/roles",
    response_model=RoleListResponse,
    summary="取得可用角色列表",
    description="取得系統中所有可用的角色和對應權限"
)
async def get_available_roles(
    current_user: dict = Depends(get_current_user),
    rbac_service: RBACManagementService = Depends(get_rbac_management_service)
) -> RoleListResponse:
    """取得可用角色列表"""
    return await rbac_service.get_available_roles()

@router.get(
    "/users/role/{user_id}",
    response_model=UserRoleInfo,
    summary="取得使用者角色資訊",
    description="取得指定使用者的角色和權限資訊"
)
async def get_user_role(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    rbac_service: RBACManagementService = Depends(get_rbac_management_service)
) -> UserRoleInfo:
    """取得使用者角色資訊"""
    # 檢查權限：只有管理員或本人可以查看
    current_user_id = current_user.get("user_id") or current_user.get("sub")
    current_role = RBACService.get_user_role(current_user)
    
    if current_role != Role.ADMIN and current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能查看自己的角色資訊"
        )
    
    return await rbac_service.get_user_role_info(user_id)

@router.put(
    "/users/role",
    response_model=RoleUpdateResponse,
    summary="更新使用者角色",
    description="更新指定使用者的角色（需要管理員權限）"
)
async def update_user_role(
    request: RoleUpdateRequest,
    current_user: dict = Depends(require_admin_role()),
    rbac_service: RBACManagementService = Depends(get_rbac_management_service)
) -> RoleUpdateResponse:
    """更新使用者角色（僅限管理員）"""
    return await rbac_service.update_user_role(request)

# ========== 權限檢查 ==========

@router.post(
    "/check-permission",
    response_model=PermissionCheckResponse,
    summary="檢查使用者權限",
    description="檢查指定使用者是否有特定權限"
)
async def check_user_permission(
    request: PermissionCheckRequest,
    current_user: dict = Depends(get_current_user),
    rbac_service: RBACManagementService = Depends(get_rbac_management_service)
) -> PermissionCheckResponse:
    """檢查使用者權限"""
    # 檢查權限：只有管理員或本人可以查看
    current_user_id = current_user.get("user_id") or current_user.get("sub")
    current_role = RBACService.get_user_role(current_user)
    
    if current_role != Role.ADMIN and current_user_id != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能檢查自己的權限"
        )
    
    return await rbac_service.check_user_permission(request)

@router.get(
    "/my-permissions",
    response_model=UserRoleInfo,
    summary="取得自己的權限資訊",
    description="取得當前使用者的角色和權限資訊"
)
async def get_my_permissions(
    current_user: dict = Depends(get_current_user),
    rbac_service: RBACManagementService = Depends(get_rbac_management_service)
) -> UserRoleInfo:
    """取得自己的權限資訊"""
    user_id = current_user.get("user_id") or current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無效的使用者 Token"
        )
    
    return await rbac_service.get_user_role_info(user_id)

# ========== 使用者管理 ==========

@router.get(
    "/users",
    response_model=List[UserPermissionSummary],
    summary="取得使用者權限摘要",
    description="取得所有使用者或指定角色的使用者權限摘要（需要管理員權限）"
)
async def list_users_by_role(
    role: Optional[Role] = Query(None, description="篩選角色"),
    current_user: dict = Depends(require_admin_role()),
    rbac_service: RBACManagementService = Depends(get_rbac_management_service)
) -> List[UserPermissionSummary]:
    """取得使用者權限摘要（僅限管理員）"""
    return await rbac_service.list_users_by_role(role)

# ========== 權限測試端點 ==========

@router.get(
    "/test/student",
    summary="測試學員權限",
    description="測試端點：需要學員權限"
)
async def test_student_permission(
    current_user: dict = Depends(get_current_user)
):
    """測試學員權限"""
    if not RBACService.has_permission(current_user, Permission.VIEW_OWN_DATA):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要學員權限"
        )
    
    return {
        "message": "學員權限測試通過",
        "user_role": RBACService.get_user_role(current_user),
        "permissions": [p.value for p in RBACService.get_user_permissions(current_user)]
    }

@router.get(
    "/test/point-manager",
    summary="測試點數管理員權限",
    description="測試端點：需要點數管理員權限"
)
async def test_point_manager_permission(
    current_user: dict = Depends(get_current_user)
):
    """測試點數管理員權限"""
    if not RBACService.has_permission(current_user, Permission.GIVE_POINTS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要點數管理員權限"
        )
    
    return {
        "message": "點數管理員權限測試通過",
        "user_role": RBACService.get_user_role(current_user),
        "permissions": [p.value for p in RBACService.get_user_permissions(current_user)]
    }

@router.get(
    "/test/announcer",
    summary="測試公告員權限",
    description="測試端點：需要公告員權限"
)
async def test_announcer_permission(
    current_user: dict = Depends(get_current_user)
):
    """測試公告員權限"""
    if not RBACService.has_permission(current_user, Permission.CREATE_ANNOUNCEMENT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要公告員權限"
        )
    
    return {
        "message": "公告員權限測試通過",
        "user_role": RBACService.get_user_role(current_user),
        "permissions": [p.value for p in RBACService.get_user_permissions(current_user)]
    }

@router.get(
    "/test/admin",
    summary="測試管理員權限",
    description="測試端點：需要管理員權限"
)
async def test_admin_permission(
    current_user: dict = Depends(require_admin_role())
):
    """測試管理員權限"""
    return {
        "message": "管理員權限測試通過",
        "user_role": RBACService.get_user_role(current_user),
        "permissions": [p.value for p in RBACService.get_user_permissions(current_user)]
    }