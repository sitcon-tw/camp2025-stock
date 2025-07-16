"""
User Application Services
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime
import logging

from ..common.interfaces import (
    ApplicationService, CommandResult, QueryResult, UnitOfWork, 
    EventPublisher, AuthorizationService, CacheService, NotificationService,
    require_permission, Permission, ValidationError, AuthorizationError, BusinessLogicError
)
from .commands import *
from .queries import *
from ...domain.user.entities import User, PointLog, PointChangeType
from ...domain.user.repositories import UserRepository, PointLogRepository
from ...domain.common.exceptions import (
    EntityNotFoundException, InsufficientPointsException, 
    BusinessRuleException, ValidationException
)
from ...infrastructure.container import DIContainer

logger = logging.getLogger(__name__)


class UserApplicationService(ApplicationService):
    """使用者應用服務"""
    
    def __init__(self, container: DIContainer):
        super().__init__()
        self.container = container
        self.user_repository: UserRepository = None
        self.point_log_repository: PointLogRepository = None
        self.unit_of_work: UnitOfWork = None
        self.event_publisher: EventPublisher = None
        self.authorization_service: AuthorizationService = None
        self.cache_service: CacheService = None
        self.notification_service: NotificationService = None
    
    async def initialize(self) -> None:
        """初始化服務"""
        try:
            self.user_repository = await self.container.get(UserRepository)
            self.point_log_repository = await self.container.get(PointLogRepository)
            self.unit_of_work = await self.container.get(UnitOfWork)
            self.event_publisher = await self.container.get(EventPublisher)
            self.authorization_service = await self.container.get(AuthorizationService)
            self.cache_service = await self.container.get(CacheService)
            self.notification_service = await self.container.get(NotificationService)
        except Exception as e:
            logger.error(f"Error initializing UserApplicationService: {e}")
            # 如果容器服務不可用，使用 None 作為默認值
            pass
    
    async def cleanup(self) -> None:
        """清理服務"""
        pass
    
    # Command Handlers
    
    async def create_user(self, command: CreateUserCommand) -> CommandResult:
        """創建用戶"""
        try:
            if not self.user_repository:
                return CommandResult.failure_result("Service not initialized", ["service_not_initialized"])
            
            async with self.unit_of_work if self.unit_of_work else self._empty_context():
                # 檢查 Telegram ID 是否已存在
                existing_user = await self.user_repository.find_by_telegram_id(command.telegram_id)
                if existing_user:
                    return CommandResult.failure_result(
                        "User with this Telegram ID already exists",
                        ["telegram_id_exists"]
                    )
                
                # 檢查學生 ID 是否已存在（如果提供）
                if command.student_id:
                    existing_student = await self.user_repository.find_by_student_id(command.student_id)
                    if existing_student:
                        return CommandResult.failure_result(
                            "User with this Student ID already exists",
                            ["student_id_exists"]
                        )
                
                # 創建用戶
                user = User(
                    telegram_id=command.telegram_id,
                    username=command.username,
                    points=command.points,
                    student_id=command.student_id,
                    real_name=command.real_name,
                    group_id=command.group_id
                )
                
                # 保存用戶
                user = await self.user_repository.save(user)
                
                # 如果有初始點數，創建點數記錄
                if command.points > 0 and self.point_log_repository:
                    point_log = user.add_points(
                        command.points,
                        PointChangeType.INITIAL,
                        "Initial points"
                    )
                    await self.point_log_repository.save(point_log)
                
                # 發布領域事件
                await self._publish_domain_events(user)
                
                # 清除相關緩存
                await self._clear_user_cache(str(user.id))
                
                return CommandResult.success_result(
                    "User created successfully",
                    {"user_id": str(user.id)}
                )
                
        except ValidationException as e:
            return CommandResult.failure_result(f"Validation error: {e.message}", [e.field])
        except BusinessRuleException as e:
            return CommandResult.failure_result(f"Business rule error: {e.message}", [e.code])
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return CommandResult.failure_result("Failed to create user", ["internal_error"])
    
    @require_permission(Permission("user.update"))
    async def update_user_profile(self, command: UpdateUserProfileCommand) -> CommandResult:
        """更新用戶資料"""
        try:
            if not self.user_repository:
                return CommandResult.failure_result("Service not initialized", ["service_not_initialized"])
            
            async with self.unit_of_work if self.unit_of_work else self._empty_context():
                user = await self.user_repository.find_by_id(ObjectId(command.target_user_id))
                if not user:
                    return CommandResult.failure_result("User not found", ["user_not_found"])
                
                # 檢查權限：只能更新自己的資料或需要管理員權限
                if command.user_id != command.target_user_id:
                    if self.authorization_service and not await self.authorization_service.check_permission(
                        command.user_id, Permission("user.update.others")
                    ):
                        raise AuthorizationError("Permission denied")
                
                # 更新用戶資料
                user.update_profile(
                    username=command.username or user.username,
                    real_name=command.real_name,
                    student_id=command.student_id,
                    group_id=command.group_id
                )
                
                # 保存更新
                await self.user_repository.update(user)
                
                # 發布領域事件
                await self._publish_domain_events(user)
                
                # 清除緩存
                await self._clear_user_cache(command.target_user_id)
                
                return CommandResult.success_result("User profile updated successfully")
                
        except AuthorizationError as e:
            return CommandResult.failure_result(f"Authorization error: {e.message}", ["permission_denied"])
        except ValidationException as e:
            return CommandResult.failure_result(f"Validation error: {e.message}", [e.field])
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return CommandResult.failure_result("Failed to update user profile", ["internal_error"])
    
    async def transfer_points(self, command: TransferPointsCommand) -> CommandResult:
        """轉帳點數"""
        try:
            if not self.user_repository:
                return CommandResult.failure_result("Service not initialized", ["service_not_initialized"])
            
            async with self.unit_of_work if self.unit_of_work else self._empty_context():
                # 獲取發送者
                sender = await self.user_repository.find_by_id(ObjectId(command.user_id))
                if not sender:
                    return CommandResult.failure_result("Sender not found", ["sender_not_found"])
                
                # 獲取接收者
                recipient = await self.user_repository.find_by_id(ObjectId(command.recipient_user_id))
                if not recipient:
                    return CommandResult.failure_result("Recipient not found", ["recipient_not_found"])
                
                # 執行轉帳
                sender_log, recipient_log = sender.transfer_to(
                    recipient,
                    command.amount,
                    command.description
                )
                
                # 保存變更
                await self.user_repository.update(sender)
                await self.user_repository.update(recipient)
                
                if self.point_log_repository:
                    await self.point_log_repository.save(sender_log)
                    await self.point_log_repository.save(recipient_log)
                
                # 發布領域事件
                await self._publish_domain_events(sender)
                await self._publish_domain_events(recipient)
                
                # 清除緩存
                await self._clear_user_cache(command.user_id)
                await self._clear_user_cache(command.recipient_user_id)
                
                # 發送通知
                if self.notification_service:
                    await self.notification_service.send_notification(
                        command.user_id,
                        f"You transferred {command.amount} points to {recipient.username}"
                    )
                    await self.notification_service.send_notification(
                        command.recipient_user_id,
                        f"You received {command.amount} points from {sender.username}"
                    )
                
                return CommandResult.success_result(
                    "Points transferred successfully",
                    {
                        "sender_balance": sender.points,
                        "recipient_balance": recipient.points
                    }
                )
                
        except BusinessRuleException as e:
            return CommandResult.failure_result(f"Transfer failed: {e.message}", [e.code])
        except InsufficientPointsException as e:
            return CommandResult.failure_result(
                f"Insufficient points: required {e.required}, available {e.available}",
                ["insufficient_points"]
            )
        except Exception as e:
            logger.error(f"Error transferring points: {e}")
            return CommandResult.failure_result("Failed to transfer points", ["internal_error"])
    
    # Query Handlers
    
    async def get_user_by_id(self, query: GetUserByIdQuery) -> QueryResult[Dict[str, Any]]:
        """根據ID獲取用戶"""
        try:
            if not self.user_repository:
                return QueryResult.failure_result("Service not initialized", ["service_not_initialized"])
            
            # 嘗試從緩存獲取
            cache_key = f"user:{query.target_user_id}"
            cached_user = None
            if self.cache_service:
                cached_user = await self.cache_service.get(cache_key)
            
            if cached_user:
                user_data = cached_user
            else:
                user = await self.user_repository.find_by_id(ObjectId(query.target_user_id))
                if not user:
                    return QueryResult.failure_result("User not found", ["user_not_found"])
                
                user_data = user.to_dict()
                
                # 緩存用戶數據
                if self.cache_service:
                    await self.cache_service.set(cache_key, user_data, ttl=300)  # 5分鐘
            
            # 檢查權限：只能查看自己的詳細資料或需要管理員權限
            if query.user_id and query.user_id != query.target_user_id:
                if self.authorization_service and not await self.authorization_service.check_permission(
                    query.user_id, Permission("user.view.others")
                ):
                    # 移除敏感信息
                    user_data = self._sanitize_user_data(user_data)
            
            # 包含權限信息
            if query.include_permissions and query.user_id and self.authorization_service:
                if await self.authorization_service.check_permission(
                    query.user_id, Permission("user.permissions.view")
                ):
                    permissions = await self.authorization_service.get_user_permissions(query.target_user_id)
                    user_data["permissions"] = [p.name for p in permissions]
            
            # 包含統計信息
            if query.include_stats:
                user_data["stats"] = await self._get_user_stats(query.target_user_id)
            
            return QueryResult.success_result(user_data)
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return QueryResult.failure_result("Failed to get user", ["internal_error"])
    
    async def get_user_point_history(self, query: GetUserPointHistoryQuery) -> QueryResult[List[Dict[str, Any]]]:
        """獲取用戶點數歷史"""
        try:
            if not self.point_log_repository:
                return QueryResult.failure_result("Service not initialized", ["service_not_initialized"])
            
            # 檢查權限
            if query.user_id and query.user_id != query.target_user_id:
                if self.authorization_service and not await self.authorization_service.check_permission(
                    query.user_id, Permission("user.points.view.others")
                ):
                    raise AuthorizationError("Permission denied")
            
            # 獲取點數歷史
            if query.change_type:
                point_logs = await self.point_log_repository.find_by_user_id_and_type(
                    ObjectId(query.target_user_id),
                    query.change_type,
                    query.skip,
                    query.limit
                )
            else:
                point_logs = await self.point_log_repository.find_by_user_id(
                    ObjectId(query.target_user_id),
                    query.skip,
                    query.limit
                )
            
            # 轉換為字典格式
            history_data = []
            for log in point_logs:
                log_data = log.to_dict()
                
                # 添加格式化信息
                log_data["formatted_amount"] = log.get_formatted_amount()
                log_data["change_type_display"] = log.get_change_type_display()
                log_data["is_positive"] = log.is_positive_change()
                
                history_data.append(log_data)
            
            return QueryResult.success_result(history_data, total_count=len(history_data))
            
        except AuthorizationError as e:
            return QueryResult.failure_result(f"Authorization error: {e.message}", ["permission_denied"])
        except Exception as e:
            logger.error(f"Error getting user point history: {e}")
            return QueryResult.failure_result("Failed to get point history", ["internal_error"])
    
    # Helper Methods
    
    async def _publish_domain_events(self, aggregate_root) -> None:
        """發布領域事件"""
        if self.event_publisher and hasattr(aggregate_root, 'domain_events'):
            for event in aggregate_root.domain_events:
                await self.event_publisher.publish(event)
            aggregate_root.clear_domain_events()
    
    async def _clear_user_cache(self, user_id: str) -> None:
        """清除用戶緩存"""
        if self.cache_service:
            cache_patterns = [
                f"user:{user_id}",
                f"user_stats:{user_id}",
                f"user_permissions:{user_id}",
                f"user_*:{user_id}"
            ]
            
            for pattern in cache_patterns:
                await self.cache_service.clear_pattern(pattern)
    
    def _sanitize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理用戶數據，移除敏感信息"""
        sanitized = user_data.copy()
        
        # 移除敏感字段
        sensitive_fields = ["telegram_id", "student_id", "email", "phone"]
        for field in sensitive_fields:
            if field in sanitized:
                sanitized.pop(field)
        
        return sanitized
    
    async def _get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶統計"""
        # 實現用戶統計邏輯
        # 這裡可以整合各種統計數據
        return {
            "total_transactions": 0,
            "total_points_earned": 0,
            "total_points_spent": 0,
            "last_activity": None,
            "account_age_days": 0
        }
    
    async def _empty_context(self):
        """空上下文管理器"""
        return EmptyContext()


class EmptyContext:
    """空上下文管理器"""
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass