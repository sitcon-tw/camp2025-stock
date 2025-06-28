# RBAC 相關的 Pydantic 模型定義

from pydantic import BaseModel, Field
from typing import List, Optional, Set
from app.core.rbac import Role, Permission

class UserRoleInfo(BaseModel):
    """使用者角色資訊"""
    user_id: str = Field(..., description="使用者ID")
    username: str = Field(..., description="使用者名稱")
    role: Role = Field(..., description="使用者角色")
    permissions: List[Permission] = Field(..., description="使用者權限列表")
    
    class Config:
        use_enum_values = True

class RoleUpdateRequest(BaseModel):
    """角色更新請求"""
    user_id: str = Field(..., description="使用者ID")
    new_role: Role = Field(..., description="新角色")
    reason: Optional[str] = Field(None, description="更新原因")
    
    class Config:
        use_enum_values = True

class RoleUpdateResponse(BaseModel):
    """角色更新回應"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="回應訊息")
    user_role_info: Optional[UserRoleInfo] = Field(None, description="更新後的使用者角色資訊")

class PermissionCheckRequest(BaseModel):
    """權限檢查請求"""
    user_id: str = Field(..., description="使用者ID")
    required_permission: Permission = Field(..., description="所需權限")
    
    class Config:
        use_enum_values = True

class PermissionCheckResponse(BaseModel):
    """權限檢查回應"""
    user_id: str = Field(..., description="使用者ID")
    role: Role = Field(..., description="使用者角色")
    required_permission: Permission = Field(..., description="所需權限")
    has_permission: bool = Field(..., description="是否有權限")
    
    class Config:
        use_enum_values = True

class RoleListResponse(BaseModel):
    """角色列表回應"""
    available_roles: List[dict] = Field(..., description="可用角色列表")
    role_permissions: dict = Field(..., description="角色權限對應")

class UserPermissionSummary(BaseModel):
    """使用者權限摘要"""
    user_id: str = Field(..., description="使用者ID")
    username: str = Field(..., description="使用者名稱")
    role: Role = Field(..., description="角色")
    permissions_count: int = Field(..., description="權限數量")
    can_give_points: bool = Field(..., description="是否可發放點數")
    can_create_announcement: bool = Field(..., description="是否可發布公告")
    can_manage_system: bool = Field(..., description="是否可管理系統")
    
    class Config:
        use_enum_values = True