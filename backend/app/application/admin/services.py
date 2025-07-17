# 管理員應用服務層
# DDD Application Service - 負責協調領域服務和基礎設施

from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

from app.core.base_classes import BaseApplicationService
from app.domain.admin.services import AdminDomainService
from app.domain.user.services import UserDomainService
from app.domain.market.services import MarketDomainService
from app.domain.admin.services import (
    AuthenticationException, UserNotFoundException,
    GroupNotFoundException, AdminException
)
from app.schemas.public import (
    AdminLoginRequest, AdminLoginResponse, UserAssetDetail,
    GivePointsRequest, GivePointsResponse, AnnouncementRequest,
    AnnouncementResponse, MarketUpdateRequest, MarketUpdateResponse,
    MarketLimitRequest, MarketLimitResponse, Trade, PointLog
)
from app.schemas.user import UserBasicInfo

logger = logging.getLogger(__name__)


class AdminApplicationService(BaseApplicationService):
    """
    管理員應用服務
    負責協調管理員相關的業務流程
    符合 DDD Application Service 模式
    """

    def __init__(
        self,
        admin_domain_service: AdminDomainService,
        user_domain_service: UserDomainService,
        market_domain_service: MarketDomainService
    ):
        super().__init__("AdminApplicationService")
        self.admin_domain_service = admin_domain_service
        self.user_domain_service = user_domain_service
        self.market_domain_service = market_domain_service

    async def login_admin(self, request: AdminLoginRequest) -> AdminLoginResponse:
        """管理員登入用例"""
        try:
            token = await self.admin_domain_service.authenticate_admin(request.password)
            logger.info("Admin login successful")
            return AdminLoginResponse(token=token)
        except AuthenticationException as e:
            logger.error(f"Admin login failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Admin login failed: {e}")
            raise AuthenticationException("Login failed")

    async def get_user_details(self, username: Optional[str] = None) -> List[UserAssetDetail]:
        """查詢使用者資產明細用例"""
        try:
            return await self.admin_domain_service.get_user_asset_details(username)
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get user details: {e}")
            raise AdminException("Failed to retrieve user details")

    async def give_points_to_user(self, request: GivePointsRequest) -> GivePointsResponse:
        """給予點數用例"""
        try:
            if request.type == "user":
                result = await self.admin_domain_service.give_points_to_user(
                    request.username, request.amount
                )
            elif request.type == "group":
                result = await self.admin_domain_service.give_points_to_group(
                    request.username, request.amount
                )
            else:
                raise AdminException("Invalid type, must be 'user' or 'group'")

            logger.info(result["message"])
            return GivePointsResponse(ok=True, message=result["message"])

        except (UserNotFoundException, GroupNotFoundException, AdminException):
            raise
        except Exception as e:
            logger.error(f"Failed to give points: {e}")
            raise AdminException("Failed to give points")

    async def create_announcement(self, request: AnnouncementRequest) -> AnnouncementResponse:
        """建立公告用例"""
        try:
            await self.admin_domain_service.create_announcement(
                title=request.title,
                message=request.message,
                broadcast=request.broadcast
            )
            
            logger.info(f"Announcement created: {request.title}")
            return AnnouncementResponse(
                ok=True,
                message="Announcement created successfully"
            )
        except Exception as e:
            logger.error(f"Failed to create announcement: {e}")
            raise AdminException(f"Failed to create announcement: {str(e)}")

    async def update_market_hours(self, request: MarketUpdateRequest) -> MarketUpdateResponse:
        """更新市場開放時間用例"""
        try:
            await self.market_domain_service.update_market_hours(
                [slot.dict() for slot in request.open_time]
            )
            logger.info("Market hours updated successfully")
            return MarketUpdateResponse(ok=True)
        except Exception as e:
            logger.error(f"Failed to update market hours: {e}")
            raise AdminException("Failed to update market hours")

    async def set_trading_limit(self, request: MarketLimitRequest) -> MarketLimitResponse:
        """設定漲跌限制用例"""
        try:
            result = await self.market_domain_service.set_trading_limit(request.limit_percent)
            
            return MarketLimitResponse(
                ok=True,
                limit_percent=result["limit_percent"],
                message=result["message"]
            )
        except Exception as e:
            logger.error(f"Failed to set trading limit: {e}")
            raise AdminException("Failed to set trading limit")

    async def perform_final_settlement(self, final_price: int = 20) -> GivePointsResponse:
        """最終結算用例"""
        try:
            result = await self.admin_domain_service.perform_final_settlement(final_price)
            logger.info(result["message"])
            return GivePointsResponse(ok=True, message=result["message"])
        except Exception as e:
            logger.error(f"Failed during final settlement: {e}")
            raise AdminException("Failed during final settlement")

    async def list_all_users(self) -> List[Dict[str, str]]:
        """列出所有使用者用例"""
        try:
            return await self.admin_domain_service.list_all_users()
        except Exception as e:
            logger.error(f"Failed to list all users: {e}")
            raise AdminException("Failed to retrieve user list")

    async def list_basic_users(self) -> List[UserBasicInfo]:
        """取得所有使用者基本資料用例"""
        try:
            users_data = await self.admin_domain_service.list_basic_users()
            return [UserBasicInfo(**user) for user in users_data]
        except Exception as e:
            logger.error(f"Failed to get basic users: {e}")
            raise AdminException("Failed to get basic users")

    async def list_all_teams(self) -> List[Dict[str, str]]:
        """列出所有團隊用例"""
        try:
            return await self.admin_domain_service.list_all_teams()
        except Exception as e:
            logger.error(f"Failed to list all teams: {e}")
            raise AdminException("Failed to retrieve team list")

    async def check_and_fix_negative_balances(self, fix_mode: bool = False) -> Dict[str, any]:
        """檢查和修復負點數使用者用例"""
        try:
            return await self.admin_domain_service.check_and_fix_negative_balances(fix_mode)
        except Exception as e:
            logger.error(f"Failed to check/fix negative balances: {e}")
            raise AdminException(f"檢查負點數失敗: {str(e)}")

    async def trigger_system_wide_balance_check(self) -> Dict[str, any]:
        """觸發全面點數完整性檢查用例"""
        try:
            return await self.admin_domain_service.trigger_system_wide_balance_check()
        except Exception as e:
            logger.error(f"Failed to trigger system-wide balance check: {e}")
            raise AdminException(f"系統全面檢查失敗: {str(e)}")

    async def get_all_trades(self, limit: int) -> List[Trade]:
        """取得所有交易記錄用例"""
        try:
            trades_data = await self.admin_domain_service.get_all_trades(limit)
            return [Trade(**trade) for trade in trades_data]
        except Exception as e:
            logger.error(f"Failed to get all trades: {e}")
            raise AdminException("Failed to retrieve trades")

    async def get_all_point_logs(self, limit: int) -> List[PointLog]:
        """取得所有點數日誌用例"""
        try:
            logs_data = await self.admin_domain_service.get_all_point_logs(limit)
            return [PointLog(**log) for log in logs_data]
        except Exception as e:
            logger.error(f"Failed to get all point logs: {e}")
            raise AdminException("Failed to retrieve point logs")

    async def trigger_manual_matching(self) -> dict:
        """手動觸發訂單撮合用例"""
        try:
            return await self.admin_domain_service.trigger_manual_matching()
        except Exception as e:
            logger.error(f"Failed to trigger manual matching: {e}")
            raise AdminException(f"Failed to trigger manual matching: {str(e)}")