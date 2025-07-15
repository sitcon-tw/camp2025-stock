# RBAC 服務層實作
# 處理角色權限的業務邏輯

from typing import List, Dict, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from app.core.rbac import Role, Permission, RBACService, ROLE_PERMISSIONS
from app.schemas.rbac import (
    UserRoleInfo, RoleUpdateRequest, RoleUpdateResponse,
    PermissionCheckRequest, PermissionCheckResponse, 
    RoleListResponse, UserPermissionSummary
)
from datetime import datetime, timezone
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

class RBACManagementService:
    """RBAC 管理服務"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
    
    async def get_user_role_info(self, user_id: str) -> UserRoleInfo:
        """
        取得使用者角色資訊
        
        Args:
            user_id: 使用者ID
            
        Returns:
            使用者角色資訊
        """
        try:
            # 特殊處理：管理員使用者
            if user_id == "admin":
                admin_role = Role.ADMIN
                admin_permissions = list(ROLE_PERMISSIONS.get(admin_role, set()))
                
                return UserRoleInfo(
                    user_id="admin",
                    username="系統管理員",
                    role=admin_role,
                    permissions=admin_permissions,
                    can_give_points=Permission.GIVE_POINTS in admin_permissions,
                    can_create_announcement=Permission.CREATE_ANNOUNCEMENT in admin_permissions,
                    can_view_all_users=Permission.VIEW_ALL_USERS in admin_permissions,
                    can_manage_system=Permission.SYSTEM_ADMIN in admin_permissions,
                    can_generate_qrcode=Permission.GENERATE_QRCODE in admin_permissions
                )
            
            # 查詢使用者資料
            query_conditions = [
                {"id": user_id},
                {"name": user_id}
            ]
            
            # 只有當 user_id 是有效的 ObjectId 格式時才加入 _id 查詢
            try:
                query_conditions.append({"_id": ObjectId(user_id)})
            except:
                pass  # 如果不是有效的 ObjectId，忽略此查詢條件
            
            user = await self.db[Collections.USERS].find_one({
                "$or": query_conditions
            })
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"找不到使用者: {user_id}"
                )
            
            # 取得角色和權限
            user_role = Role(user.get("role", Role.STUDENT.value))
            user_permissions = list(ROLE_PERMISSIONS.get(user_role, set()))
            
            return UserRoleInfo(
                user_id=str(user["_id"]),
                username=user.get("name", user.get("id", "未知")),
                role=user_role,
                permissions=user_permissions,
                can_give_points=Permission.GIVE_POINTS in user_permissions,
                can_create_announcement=Permission.CREATE_ANNOUNCEMENT in user_permissions,
                can_view_all_users=Permission.VIEW_ALL_USERS in user_permissions,
                can_manage_system=Permission.SYSTEM_ADMIN in user_permissions,
                can_generate_qrcode=Permission.GENERATE_QRCODE in user_permissions
            )
            
        except Exception as e:
            logger.error(f"Failed to get user role info for {user_id}: {e}")
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="無法取得使用者角色資訊"
            )
    
    async def update_user_role(self, request: RoleUpdateRequest) -> RoleUpdateResponse:
        """
        更新使用者角色
        
        Args:
            request: 角色更新請求
            
        Returns:
            角色更新回應
        """
        try:
            # 特殊處理：不允許更新管理員角色
            if request.user_id == "admin":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="無法更新系統管理員角色"
                )
            
            # 查詢使用者
            query_conditions = [
                {"id": request.user_id},
                {"name": request.user_id}
            ]
            
            # 只有當 user_id 是有效的 ObjectId 格式時才加入 _id 查詢
            try:
                query_conditions.append({"_id": ObjectId(request.user_id)})
            except:
                pass  # 如果不是有效的 ObjectId，忽略此查詢條件
            
            user = await self.db[Collections.USERS].find_one({
                "$or": query_conditions
            })
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"找不到使用者: {request.user_id}"
                )
            
            # 更新角色
            result = await self.db[Collections.USERS].update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "role": request.new_role,
                        "role_updated_at": datetime.now(timezone.utc),
                        "role_update_reason": request.reason or "系統更新"
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="角色更新失敗"
                )
            
            # 記錄角色變更
            await self._log_role_change(
                user_id=user["_id"],
                old_role=user.get("role", Role.STUDENT.value),
                new_role=request.new_role,
                reason=request.reason
            )
            
            # 取得更新後的使用者角色資訊
            updated_info = await self.get_user_role_info(str(user["_id"]))
            
            logger.info(f"Role updated for user {request.user_id}: {request.new_role}")
            
            return RoleUpdateResponse(
                success=True,
                message=f"使用者 {request.user_id} 的角色已更新為 {request.new_role}",
                user_role_info=updated_info
            )
            
        except Exception as e:
            logger.error(f"Failed to update user role: {e}")
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="角色更新失敗"
            )
    
    async def check_user_permission(self, request: PermissionCheckRequest) -> PermissionCheckResponse:
        """
        檢查使用者權限
        
        Args:
            request: 權限檢查請求
            
        Returns:
            權限檢查回應
        """
        try:
            # 特殊處理：管理員擁有所有權限
            if request.user_id == "admin":
                return PermissionCheckResponse(
                    user_id="admin",
                    role=Role.ADMIN,
                    required_permission=request.required_permission,
                    has_permission=True  # 管理員擁有所有權限
                )
            
            # 取得使用者角色資訊
            user_info = await self.get_user_role_info(request.user_id)
            
            # 檢查權限
            has_permission = request.required_permission in user_info.permissions
            
            return PermissionCheckResponse(
                user_id=request.user_id,
                role=user_info.role,
                required_permission=request.required_permission,
                has_permission=has_permission
            )
            
        except Exception as e:
            logger.error(f"Failed to check user permission: {e}")
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="權限檢查失敗"
            )
    
    async def get_available_roles(self) -> RoleListResponse:
        """
        取得可用角色列表
        
        Returns:
            角色列表回應
        """
        try:
            available_roles = []
            role_permissions = {}
            
            for role in Role:
                permissions = ROLE_PERMISSIONS.get(role, set())
                available_roles.append({
                    "role": role.value,
                    "description": self._get_role_description(role),
                    "permissions_count": len(permissions)
                })
                role_permissions[role.value] = [p.value for p in permissions]
            
            return RoleListResponse(
                available_roles=available_roles,
                role_permissions=role_permissions
            )
            
        except Exception as e:
            logger.error(f"Failed to get available roles: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="無法取得角色列表"
            )
    
    async def list_users_by_role(self, role: Optional[Role] = None) -> List[UserPermissionSummary]:
        """
        依角色列出使用者
        
        Args:
            role: 指定角色，None 則列出所有使用者
            
        Returns:
            使用者權限摘要列表
        """
        try:
            # 建構查詢條件
            query = {}
            if role:
                query["role"] = role.value
            
            # 查詢使用者
            users_cursor = self.db[Collections.USERS].find(query)
            users = await users_cursor.to_list(length=None)
            
            summaries = []
            for user in users:
                user_role = Role(user.get("role", Role.STUDENT.value))
                permissions = ROLE_PERMISSIONS.get(user_role, set())
                
                summary = UserPermissionSummary(
                    user_id=str(user["_id"]),
                    username=user.get("name", user.get("id", "未知")),
                    role=user_role,
                    permissions_count=len(permissions),
                    can_give_points=Permission.GIVE_POINTS in permissions,
                    can_create_announcement=Permission.CREATE_ANNOUNCEMENT in permissions,
                    can_manage_system=Permission.SYSTEM_ADMIN in permissions
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Failed to list users by role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="無法取得使用者列表"
            )
    
    async def _log_role_change(self, user_id: ObjectId, old_role: str, new_role: str, reason: Optional[str]):
        """
        記錄角色變更
        
        Args:
            user_id: 使用者ID
            old_role: 舊角色
            new_role: 新角色
            reason: 變更原因
        """
        try:
            log_entry = {
                "user_id": user_id,
                "type": "role_change",
                "old_role": old_role,
                "new_role": new_role,
                "reason": reason or "系統更新",
                "created_at": datetime.now(timezone.utc)
            }
            
            await self.db[Collections.POINT_LOGS].insert_one(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log role change: {e}")
    
    @staticmethod
    def _get_role_description(role: Role) -> str:
        """
        取得角色描述
        
        Args:
            role: 角色
            
        Returns:
            角色描述
        """
        descriptions = {
            Role.STUDENT: "一般學員 - 可以交易股票、轉帳點數",
            Role.POINT_MANAGER: "點數管理員 - 可以發放點數給使用者",
            Role.ANNOUNCER: "公告員 - 可以發布系統公告",
            Role.ADMIN: "系統管理員 - 擁有完整系統管理權限"
        }
        return descriptions.get(role, "未知角色")

# 依賴注入函數
def get_rbac_service() -> RBACManagementService:
    """RBAC 管理服務的依賴注入函數"""
    return RBACManagementService()

def get_rbac_management_service() -> RBACManagementService:
    """RBAC 管理服務的依賴注入函數（向後相容）"""
    return RBACManagementService()
