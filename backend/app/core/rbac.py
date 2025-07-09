# Role-Based Access Control (RBAC) 系統
# 實作權限組和權限檢查功能

from enum import Enum
from typing import List, Dict, Optional, Set
from fastapi import HTTPException, status, Depends
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class Role(str, Enum):
    """使用者角色定義"""
    STUDENT = "student"           # 一般學員
    QRCODE_MANAGER = "qrcode_manager"  # QR Code管理員
    POINT_MANAGER = "point_manager"  # 發放點數權限
    ANNOUNCER = "announcer"       # 發公告權限
    ADMIN = "admin"              # 完整管理員權限

class Permission(str, Enum):
    """權限定義"""
    # 基本權限
    VIEW_OWN_DATA = "view_own_data"           # 查看自己的資料
    TRADE_STOCKS = "trade_stocks"             # 股票交易
    TRANSFER_POINTS = "transfer_points"       # 轉帳點數
    
    # 管理權限
    VIEW_ALL_USERS = "view_all_users"         # 查看所有使用者
    GIVE_POINTS = "give_points"               # 發放點數
    CREATE_ANNOUNCEMENT = "create_announcement"  # 發布公告
    GENERATE_QRCODE = "generate_qrcode"       # 生成QR Code
    
    # 系統管理權限
    MANAGE_USERS = "manage_users"             # 管理使用者
    MANAGE_MARKET = "manage_market"           # 管理市場
    SYSTEM_ADMIN = "system_admin"             # 系統管理

# 角色權限對應表
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.STUDENT: {
        Permission.VIEW_OWN_DATA,
        Permission.TRADE_STOCKS,
        Permission.TRANSFER_POINTS,
    },
    Role.QRCODE_MANAGER: {
        Permission.VIEW_OWN_DATA,
        Permission.TRADE_STOCKS,
        Permission.TRANSFER_POINTS,
        Permission.GENERATE_QRCODE,
    },
    Role.POINT_MANAGER: {
        Permission.VIEW_OWN_DATA,
        Permission.TRADE_STOCKS,
        Permission.TRANSFER_POINTS,
        Permission.VIEW_ALL_USERS,
        Permission.GIVE_POINTS,
    },
    Role.ANNOUNCER: {
        Permission.VIEW_OWN_DATA,
        Permission.TRADE_STOCKS,
        Permission.TRANSFER_POINTS,
        Permission.VIEW_ALL_USERS,
        Permission.CREATE_ANNOUNCEMENT,
    },
    Role.ADMIN: {
        # 管理員擁有所有權限
        Permission.VIEW_OWN_DATA,
        Permission.TRADE_STOCKS,
        Permission.TRANSFER_POINTS,
        Permission.VIEW_ALL_USERS,
        Permission.GIVE_POINTS,
        Permission.CREATE_ANNOUNCEMENT,
        Permission.GENERATE_QRCODE,
        Permission.MANAGE_USERS,
        Permission.MANAGE_MARKET,
        Permission.SYSTEM_ADMIN,
    }
}

class RBACService:
    """權限控制服務"""
    
    @staticmethod
    async def get_user_role_from_db(user: dict) -> Role:
        """
        從資料庫查詢使用者角色
        
        Args:
            user: 使用者資訊字典
            
        Returns:
            使用者角色
        """
        try:
            # 檢查是否為管理員 token
            if user.get("sub") == "admin":
                return Role.ADMIN
            
            # 從資料庫查詢使用者角色
            user_id = user.get("user_id") or user.get("sub")
            if not user_id:
                return Role.STUDENT
            
            from app.core.database import get_database, Collections
            from bson import ObjectId
            
            db = get_database()
            
            # 構建查詢條件
            query_conditions = [
                {"id": user_id},
                {"name": user_id}
            ]
            
            # 只有當 user_id 是有效的 ObjectId 格式時才加入 _id 查詢
            try:
                query_conditions.append({"_id": ObjectId(user_id)})
            except:
                pass
            
            user_doc = await db[Collections.USERS].find_one({
                "$or": query_conditions
            })
            
            if user_doc and user_doc.get("role"):
                try:
                    return Role(user_doc["role"])
                except ValueError:
                    return Role.STUDENT
            
            return Role.STUDENT
            
        except Exception as e:
            logger.warning(f"Failed to get user role from database: {e}")
            return Role.STUDENT
    
    @staticmethod
    def get_user_role(user: dict) -> Role:
        """
        從使用者資訊中取得角色
        
        Args:
            user: 使用者資訊字典
            
        Returns:
            使用者角色
        """
        # 檢查是否為管理員 token
        if user.get("sub") == "admin":
            return Role.ADMIN
            
        # 從使用者資料中取得角色，預設為學員
        user_role = user.get("role", Role.STUDENT.value)
        
        try:
            return Role(user_role)
        except ValueError:
            logger.warning(f"Unknown role '{user_role}' for user {user.get('user_id', 'unknown')}, defaulting to student")
            return Role.STUDENT
    
    @staticmethod
    def get_user_permissions(user: dict) -> Set[Permission]:
        """
        取得使用者的所有權限
        
        Args:
            user: 使用者資訊字典
            
        Returns:
            使用者權限集合
        """
        role = RBACService.get_user_role(user)
        return ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def has_permission(user: dict, required_permission: Permission) -> bool:
        """
        檢查使用者是否有指定權限
        
        Args:
            user: 使用者資訊字典
            required_permission: 所需權限
            
        Returns:
            是否有權限
        """
        user_permissions = RBACService.get_user_permissions(user)
        return required_permission in user_permissions
    
    @staticmethod
    def has_any_permission(user: dict, required_permissions: List[Permission]) -> bool:
        """
        檢查使用者是否有任一指定權限
        
        Args:
            user: 使用者資訊字典
            required_permissions: 所需權限列表
            
        Returns:
            是否有任一權限
        """
        user_permissions = RBACService.get_user_permissions(user)
        return any(perm in user_permissions for perm in required_permissions)
    
    @staticmethod
    def has_all_permissions(user: dict, required_permissions: List[Permission]) -> bool:
        """
        檢查使用者是否有所有指定權限
        
        Args:
            user: 使用者資訊字典
            required_permissions: 所需權限列表
            
        Returns:
            是否有所有權限
        """
        user_permissions = RBACService.get_user_permissions(user)
        return all(perm in user_permissions for perm in required_permissions)

# 權限檢查裝飾器
def require_permission(required_permission: Permission):
    """
    權限檢查裝飾器
    
    Args:
        required_permission: 所需權限
        
    Returns:
        裝飾器函數
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 從 kwargs 中取得 current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登入才能存取此功能"
                )
            
            if not RBACService.has_permission(current_user, required_permission):
                user_role = RBACService.get_user_role(current_user)
                logger.warning(
                    f"Access denied: User {current_user.get('user_id', 'unknown')} "
                    f"with role {user_role} attempted to access {required_permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"權限不足：需要 {required_permission.value} 權限"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(required_permissions: List[Permission]):
    """
    需要任一權限的檢查裝飾器
    
    Args:
        required_permissions: 所需權限列表
        
    Returns:
        裝飾器函數
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登入才能存取此功能"
                )
            
            if not RBACService.has_any_permission(current_user, required_permissions):
                user_role = RBACService.get_user_role(current_user)
                permissions_str = ", ".join([p.value for p in required_permissions])
                logger.warning(
                    f"Access denied: User {current_user.get('user_id', 'unknown')} "
                    f"with role {user_role} attempted to access one of: {permissions_str}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"權限不足：需要以下任一權限：{permissions_str}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# FastAPI 依賴函數
def get_current_user_with_permission(required_permission: Permission):
    """
    取得有指定權限的目前使用者的依賴函數
    
    Args:
        required_permission: 所需權限
        
    Returns:
        依賴函數
    """
    def check_permission(current_user: dict):
        if not RBACService.has_permission(current_user, required_permission):
            user_role = RBACService.get_user_role(current_user)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {required_permission.value} 權限"
            )
        return current_user
    
    return check_permission

def get_current_user_with_role(required_role: Role):
    """
    取得有指定角色的目前使用者的依賴函數
    
    Args:
        required_role: 所需角色
        
    Returns:
        依賴函數
    """
    def check_role(current_user: dict):
        user_role = RBACService.get_user_role(current_user)
        if user_role != required_role and user_role != Role.ADMIN:  # 管理員可以存取所有功能
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {required_role.value} 角色"
            )
        return current_user
    
    return check_role

# 便利函數：檢查權限的 FastAPI 依賴
def require_student_role():
    """需要學員角色"""
    from app.core.security import get_current_user
    
    def check_student_role(current_user: dict = Depends(get_current_user)):
        user_role = RBACService.get_user_role(current_user)
        if user_role != Role.STUDENT and user_role != Role.ADMIN:  # 管理員可以存取所有功能
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Role.STUDENT.value} 角色"
            )
        return current_user
    return check_student_role

def require_qrcode_manager_role():
    """需要QR Code管理員角色"""
    from app.core.security import get_current_user
    
    def check_qrcode_manager_role(current_user: dict = Depends(get_current_user)):
        user_role = RBACService.get_user_role(current_user)
        if user_role != Role.QRCODE_MANAGER and user_role != Role.ADMIN:  # 管理員可以存取所有功能
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Role.QRCODE_MANAGER.value} 角色"
            )
        return current_user
    return check_qrcode_manager_role

def require_point_manager_role():
    """需要點數管理員角色"""
    from app.core.security import get_current_user
    
    def check_point_manager_role(current_user: dict = Depends(get_current_user)):
        user_role = RBACService.get_user_role(current_user)
        if user_role != Role.POINT_MANAGER and user_role != Role.ADMIN:  # 管理員可以存取所有功能
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Role.POINT_MANAGER.value} 角色"
            )
        return current_user
    return check_point_manager_role

def require_announcer_role():
    """需要公告員角色"""
    from app.core.security import get_current_user
    
    def check_announcer_role(current_user: dict = Depends(get_current_user)):
        user_role = RBACService.get_user_role(current_user)
        if user_role != Role.ANNOUNCER and user_role != Role.ADMIN:  # 管理員可以存取所有功能
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Role.ANNOUNCER.value} 角色"
            )
        return current_user
    return check_announcer_role

def require_admin_role():
    """需要管理員角色"""
    from app.core.security import get_current_user
    
    async def check_admin_role(current_user: dict = Depends(get_current_user)):
        user_role = await RBACService.get_user_role_from_db(current_user)
        if user_role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Role.ADMIN.value} 角色"
            )
        return current_user
    return check_admin_role

# 便利函數：檢查權限的 FastAPI 依賴
def require_give_points_permission():
    """需要發放點數權限"""
    from app.core.security import get_current_user
    
    def check_give_points_permission(current_user: dict = Depends(get_current_user)):
        if not RBACService.has_permission(current_user, Permission.GIVE_POINTS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Permission.GIVE_POINTS.value} 權限"
            )
        return current_user
    return check_give_points_permission

def require_announcement_permission():
    """需要發公告權限"""
    from app.core.security import get_current_user
    
    def check_announcement_permission(current_user: dict = Depends(get_current_user)):
        if not RBACService.has_permission(current_user, Permission.CREATE_ANNOUNCEMENT):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Permission.CREATE_ANNOUNCEMENT.value} 權限"
            )
        return current_user
    return check_announcement_permission

def require_view_all_users_permission():
    """需要查看所有使用者權限"""
    from app.core.security import get_current_user
    
    def check_view_all_users_permission(current_user: dict = Depends(get_current_user)):
        if not RBACService.has_permission(current_user, Permission.VIEW_ALL_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Permission.VIEW_ALL_USERS.value} 權限"
            )
        return current_user
    return check_view_all_users_permission

def require_qrcode_permission():
    """需要QR Code生成權限"""
    from app.core.security import get_current_user
    
    def check_qrcode_permission(current_user: dict = Depends(get_current_user)):
        if not RBACService.has_permission(current_user, Permission.GENERATE_QRCODE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Permission.GENERATE_QRCODE.value} 權限"
            )
        return current_user
    return check_qrcode_permission

def require_system_admin_permission():
    """需要系統管理權限"""
    from app.core.security import get_current_user
    
    def check_system_admin_permission(current_user: dict = Depends(get_current_user)):
        if not RBACService.has_permission(current_user, Permission.SYSTEM_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {Permission.SYSTEM_ADMIN.value} 權限"
            )
        return current_user
    return check_system_admin_permission

def check_admin_permission(current_user: dict, required_role: Role):
    """
    檢查管理員權限的便利函數
    
    Args:
        current_user: 目前使用者資訊
        required_role: 所需角色
        
    Raises:
        HTTPException: 如果權限不足
    """
    user_role = RBACService.get_user_role(current_user)
    if user_role != required_role and user_role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"權限不足：需要 {required_role.value} 角色"
        )