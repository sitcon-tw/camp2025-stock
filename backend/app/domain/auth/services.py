# 認證授權領域服務
# 負責處理RBAC相關的業務邏輯

from __future__ import annotations
from typing import List, Dict, Optional, Set
import logging
from datetime import datetime, timezone
from bson import ObjectId

from ..common.exceptions import DomainException, AuthorizationException
from ..user.repositories import UserRepository
from app.core.rbac import Role, Permission, ROLE_PERMISSIONS

logger = logging.getLogger(__name__)


class RBACDomainService:
    """RBAC領域服務 - 處理角色權限相關的業務邏輯"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user_role_info(self, user_id: str) -> Dict[str, any]:
        """
        取得使用者角色資訊
        領域邏輯：根據使用者資料決定其角色和權限
        """
        try:
            # 特殊處理：管理員使用者
            if user_id == "admin":
                admin_role = Role.ADMIN
                admin_permissions = list(ROLE_PERMISSIONS.get(admin_role, set()))
                
                return {
                    "user_id": "admin",
                    "username": "系統管理員",
                    "role": admin_role,
                    "permissions": admin_permissions,
                    "can_give_points": Permission.GIVE_POINTS in admin_permissions,
                    "can_manage_announcements": Permission.MANAGE_ANNOUNCEMENTS in admin_permissions,
                    "can_view_all_users": Permission.VIEW_ALL_USERS in admin_permissions,
                    "updated_at": datetime.now(timezone.utc),
                    "is_active": True
                }
            
            # 一般使用者
            user = await self.user_repository.find_by_id(ObjectId(user_id))
            if not user:
                raise DomainException(f"使用者 {user_id} 不存在")
            
            # 取得使用者角色，預設為學生
            user_role = getattr(user, 'role', Role.STUDENT)
            user_permissions = list(ROLE_PERMISSIONS.get(user_role, set()))
            
            return {
                "user_id": user_id,
                "username": user.name or "未知使用者",
                "role": user_role,
                "permissions": user_permissions,
                "can_give_points": Permission.GIVE_POINTS in user_permissions,
                "can_manage_announcements": Permission.MANAGE_ANNOUNCEMENTS in user_permissions,
                "can_view_all_users": Permission.VIEW_ALL_USERS in user_permissions,
                "updated_at": user.updated_at or user.created_at,
                "is_active": getattr(user, 'enabled', True)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user role info for {user_id}: {e}")
            raise DomainException(f"取得使用者角色資訊失敗: {str(e)}")

    async def update_user_role(self, user_id: str, new_role: Role, updated_by: str) -> Dict[str, any]:
        """
        更新使用者角色
        領域邏輯：驗證角色變更的有效性並執行更新
        """
        try:
            # 管理員使用者不能更改角色
            if user_id == "admin":
                raise DomainException("不能更改系統管理員的角色")
            
            user = await self.user_repository.find_by_id(ObjectId(user_id))
            if not user:
                raise DomainException(f"使用者 {user_id} 不存在")
            
            old_role = getattr(user, 'role', Role.STUDENT)
            
            # 驗證角色變更的業務規則
            self._validate_role_change(old_role, new_role)
            
            # 更新使用者角色
            user.role = new_role
            user.updated_at = datetime.now(timezone.utc)
            
            await self.user_repository.update(user)
            
            logger.info(f"User {user_id} role updated from {old_role} to {new_role} by {updated_by}")
            
            return {
                "user_id": user_id,
                "username": user.name,
                "old_role": old_role,
                "new_role": new_role,
                "updated_by": updated_by,
                "updated_at": user.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to update user role for {user_id}: {e}")
            raise DomainException(f"更新使用者角色失敗: {str(e)}")

    async def check_user_permission(self, user_id: str, required_permission: Permission) -> bool:
        """
        檢查使用者權限
        領域邏輯：根據使用者角色判斷是否具備特定權限
        """
        try:
            user_info = await self.get_user_role_info(user_id)
            user_permissions = set(user_info["permissions"])
            
            has_permission = required_permission in user_permissions
            
            logger.debug(f"Permission check for user {user_id}: {required_permission} = {has_permission}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Failed to check permission for user {user_id}: {e}")
            return False

    async def get_user_permission_summary(self, user_id: str) -> Dict[str, any]:
        """
        取得使用者權限摘要
        領域邏輯：整理使用者的完整權限資訊
        """
        try:
            user_info = await self.get_user_role_info(user_id)
            user_permissions = set(user_info["permissions"])
            
            # 按類別整理權限
            permission_categories = {
                "點數管理": [
                    Permission.GIVE_POINTS,
                    Permission.VIEW_POINT_LOGS
                ],
                "用戶管理": [
                    Permission.VIEW_ALL_USERS,
                    Permission.MANAGE_USERS
                ],
                "公告管理": [
                    Permission.MANAGE_ANNOUNCEMENTS,
                    Permission.VIEW_ANNOUNCEMENTS
                ],
                "系統管理": [
                    Permission.MANAGE_MARKET,
                    Permission.SYSTEM_ADMIN
                ]
            }
            
            categorized_permissions = {}
            for category, perms in permission_categories.items():
                categorized_permissions[category] = [
                    {"permission": perm, "granted": perm in user_permissions}
                    for perm in perms
                ]
            
            return {
                "user_id": user_id,
                "username": user_info["username"],
                "role": user_info["role"],
                "total_permissions": len(user_permissions),
                "categorized_permissions": categorized_permissions,
                "is_admin": user_info["role"] == Role.ADMIN,
                "last_updated": user_info["updated_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get permission summary for user {user_id}: {e}")
            raise DomainException(f"取得使用者權限摘要失敗: {str(e)}")

    async def list_all_roles(self) -> List[Dict[str, any]]:
        """
        列出所有可用角色
        領域邏輯：提供系統中定義的所有角色及其權限
        """
        try:
            roles_info = []
            
            for role in Role:
                permissions = list(ROLE_PERMISSIONS.get(role, set()))
                
                roles_info.append({
                    "role": role,
                    "role_name": self._get_role_display_name(role),
                    "permissions": permissions,
                    "permission_count": len(permissions),
                    "is_admin_role": role == Role.ADMIN,
                    "description": self._get_role_description(role)
                })
            
            return roles_info
            
        except Exception as e:
            logger.error(f"Failed to list all roles: {e}")
            raise DomainException(f"列出所有角色失敗: {str(e)}")

    def _validate_role_change(self, old_role: Role, new_role: Role) -> None:
        """
        驗證角色變更的業務規則
        領域邏輯：確保角色變更符合業務規則
        """
        # 不能將管理員角色降級（安全考量）
        if old_role == Role.ADMIN and new_role != Role.ADMIN:
            raise DomainException("不能將管理員角色降級")
        
        # 不能直接升級為管理員（需要特殊程序）
        if old_role != Role.ADMIN and new_role == Role.ADMIN:
            raise DomainException("不能直接升級為管理員角色")
        
        # 角色必須在有效範圍內
        if new_role not in Role:
            raise DomainException(f"無效的角色: {new_role}")

    def _get_role_display_name(self, role: Role) -> str:
        """取得角色顯示名稱"""
        role_names = {
            Role.STUDENT: "學生",
            Role.QRCODE_MANAGER: "QR碼管理員",
            Role.POINT_MANAGER: "點數管理員",
            Role.QR_POINT_MANAGER: "QR點數管理員",
            Role.ANNOUNCER: "公告管理員",
            Role.ADMIN: "系統管理員"
        }
        return role_names.get(role, str(role))

    def _get_role_description(self, role: Role) -> str:
        """取得角色描述"""
        role_descriptions = {
            Role.STUDENT: "基本學生權限，可以進行交易和查看資訊",
            Role.QRCODE_MANAGER: "可以管理QR碼相關功能",
            Role.POINT_MANAGER: "可以管理點數分配",
            Role.QR_POINT_MANAGER: "可以管理QR碼和點數",
            Role.ANNOUNCER: "可以發布和管理公告",
            Role.ADMIN: "具有系統完整管理權限"
        }
        return role_descriptions.get(role, "無描述")