# 認證授權應用服務
# 負責協調RBAC相關的業務流程

from typing import List, Dict, Optional
import logging

from app.core.base_classes import BaseApplicationService
from app.domain.auth.services import RBACDomainService
from app.schemas.rbac import (
    UserRoleInfo, RoleUpdateRequest, RoleUpdateResponse,
    PermissionCheckRequest, PermissionCheckResponse, 
    RoleListResponse, UserPermissionSummary
)
from app.core.rbac import Permission

logger = logging.getLogger(__name__)


class RBACApplicationService(BaseApplicationService):
    """
    RBAC應用服務
    SRP 原則：專注於權限管理相關的應用邏輯
    """
    
    def __init__(self, rbac_domain_service: RBACDomainService):
        super().__init__("RBACApplicationService")
        self.rbac_domain_service = rbac_domain_service

    async def get_user_role_info(self, user_id: str) -> UserRoleInfo:
        """取得使用者角色資訊用例"""
        try:
            role_data = await self.rbac_domain_service.get_user_role_info(user_id)
            
            return UserRoleInfo(
                user_id=role_data["user_id"],
                username=role_data["username"],
                role=role_data["role"],
                permissions=role_data["permissions"],
                can_give_points=role_data["can_give_points"],
                can_manage_announcements=role_data["can_manage_announcements"],
                can_view_all_users=role_data["can_view_all_users"],
                updated_at=role_data["updated_at"],
                is_active=role_data["is_active"]
            )
        except Exception as e:
            logger.error(f"Failed to get user role info for {user_id}: {e}")
            raise

    async def update_user_role(self, request: RoleUpdateRequest, updated_by: str) -> RoleUpdateResponse:
        """更新使用者角色用例"""
        try:
            update_result = await self.rbac_domain_service.update_user_role(
                request.user_id, request.new_role, updated_by
            )
            
            return RoleUpdateResponse(
                success=True,
                message=f"使用者 {request.user_id} 的角色已更新為 {request.new_role}",
                user_id=update_result["user_id"],
                username=update_result["username"],
                old_role=update_result["old_role"],
                new_role=update_result["new_role"],
                updated_by=update_result["updated_by"],
                updated_at=update_result["updated_at"]
            )
        except Exception as e:
            logger.error(f"Failed to update user role: {e}")
            return RoleUpdateResponse(
                success=False,
                message=f"更新角色失敗: {str(e)}",
                user_id=request.user_id,
                username="",
                old_role=None,
                new_role=request.new_role,
                updated_by=updated_by,
                updated_at=None
            )

    async def check_user_permission(self, request: PermissionCheckRequest) -> PermissionCheckResponse:
        """檢查使用者權限用例"""
        try:
            has_permission = await self.rbac_domain_service.check_user_permission(
                request.user_id, request.permission
            )
            
            return PermissionCheckResponse(
                user_id=request.user_id,
                permission=request.permission,
                granted=has_permission,
                message="權限檢查完成"
            )
        except Exception as e:
            logger.error(f"Failed to check permission for {request.user_id}: {e}")
            return PermissionCheckResponse(
                user_id=request.user_id,
                permission=request.permission,
                granted=False,
                message=f"權限檢查失敗: {str(e)}"
            )

    async def get_user_permission_summary(self, user_id: str) -> UserPermissionSummary:
        """取得使用者權限摘要用例"""
        try:
            summary_data = await self.rbac_domain_service.get_user_permission_summary(user_id)
            
            return UserPermissionSummary(
                user_id=summary_data["user_id"],
                username=summary_data["username"],
                role=summary_data["role"],
                total_permissions=summary_data["total_permissions"],
                categorized_permissions=summary_data["categorized_permissions"],
                is_admin=summary_data["is_admin"],
                last_updated=summary_data["last_updated"]
            )
        except Exception as e:
            logger.error(f"Failed to get permission summary for {user_id}: {e}")
            raise

    async def list_all_roles(self) -> RoleListResponse:
        """列出所有角色用例"""
        try:
            roles_data = await self.rbac_domain_service.list_all_roles()
            
            return RoleListResponse(
                roles=roles_data,
                total_count=len(roles_data),
                message="角色列表查詢成功"
            )
        except Exception as e:
            logger.error(f"Failed to list all roles: {e}")
            return RoleListResponse(
                roles=[],
                total_count=0,
                message=f"查詢角色列表失敗: {str(e)}"
            )

    async def verify_admin_permission(self, user_id: str) -> bool:
        """驗證管理員權限的便捷方法"""
        try:
            return await self.rbac_domain_service.check_user_permission(
                user_id, Permission.SYSTEM_ADMIN
            )
        except Exception as e:
            logger.error(f"Failed to verify admin permission for {user_id}: {e}")
            return False

    async def verify_give_points_permission(self, user_id: str) -> bool:
        """驗證給予點數權限的便捷方法"""
        try:
            return await self.rbac_domain_service.check_user_permission(
                user_id, Permission.GIVE_POINTS
            )
        except Exception as e:
            logger.error(f"Failed to verify give points permission for {user_id}: {e}")
            return False

    async def verify_announcement_permission(self, user_id: str) -> bool:
        """驗證公告管理權限的便捷方法"""
        try:
            return await self.rbac_domain_service.check_user_permission(
                user_id, Permission.MANAGE_ANNOUNCEMENTS
            )
        except Exception as e:
            logger.error(f"Failed to verify announcement permission for {user_id}: {e}")
            return False