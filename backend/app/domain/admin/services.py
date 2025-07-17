"""
Admin Domain Services
Enhanced to include all admin business logic
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone
import logging
import requests

from .entities import AdminUser, AdminAction, AdminRole
from ..user.repositories import UserRepository, PointLogRepository
from ..trading.repositories import StockRepository, TradeRepository
from ..common.exceptions import (
    DomainException, EntityNotFoundException, AdminDomainException
)

# Create specific exceptions for admin domain
class AuthenticationException(AdminDomainException):
    """認證異常"""
    pass

class UserNotFoundException(AdminDomainException):
    """使用者未找到異常"""
    pass

class GroupNotFoundException(AdminDomainException):
    """群組未找到異常"""
    pass

class AdminException(AdminDomainException):
    """一般管理異常"""
    pass
from app.core.security import verify_CAMP_ADMIN_PASSWORD, create_access_token
from app.core.config_refactored import config

logger = logging.getLogger(__name__)


class AdminDomainService:
    """管理員領域服務 - 包含所有管理員業務邏輯"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        point_log_repository: PointLogRepository,
        stock_repository: StockRepository,
        trade_repository: TradeRepository
    ):
        self.user_repository = user_repository
        self.point_log_repository = point_log_repository
        self.stock_repository = stock_repository
        self.trade_repository = trade_repository

    async def authenticate_admin(self, password: str) -> str:
        """管理員認證並產生 JWT Token"""
        if not verify_CAMP_ADMIN_PASSWORD(password):
            raise AuthenticationException("Invalid admin password")

        token = create_access_token(data={
            "sub": "admin",
            "type": "admin",
            "role": "admin",
            "user_id": "admin"
        })
        
        logger.info("Admin authenticated successfully")
        return token

    async def get_user_asset_details(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """取得使用者資產明細"""
        try:
            # 構建查詢條件
            query_filter = {}
            if username:
                query_filter = {
                    "$or": [
                        {"name": username},
                        {"id": username}
                    ]
                }

            users = await self.user_repository.find_by_filter(query_filter)
            if not users and username:
                raise UserNotFoundException(username)

            result = []
            for user in users:
                # 計算使用者股票持有和價值
                stock_holding = await self.stock_repository.find_by_user_id(user.id)
                stock_amount = stock_holding.stock_amount if stock_holding else 0
                
                # 取得目前股票價格
                current_price = await self._get_current_stock_price()
                stock_value = stock_amount * current_price
                
                # 計算平均成本
                avg_cost = await self._calculate_user_avg_cost(user.id)

                user_detail = {
                    "username": user.name or "Unknown",
                    "team": user.team or "Unknown", 
                    "points": user.points,
                    "stocks": stock_amount,
                    "avgCost": avg_cost,
                    "stockValue": stock_value,
                    "total": user.points + stock_value
                }
                result.append(user_detail)

            logger.info(f"Retrieved {len(result)} user asset details")
            return result

        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get user asset details: {e}")
            raise AdminException("Failed to retrieve user details")

    async def give_points_to_user(self, username: str, amount: int) -> Dict[str, str]:
        """給個別使用者點數"""
        if amount <= 0:
            raise AdminException("Amount must be positive")

        user = await self.user_repository.find_by_username_or_id(username)
        if not user:
            raise UserNotFoundException(username)

        # 檢查是否有欠款，優先償還
        current_owed = user.owed_points or 0
        
        if current_owed > 0:
            total_available = user.points + amount
            actual_repay = min(total_available, current_owed)
            remaining_points = total_available - actual_repay
            
            # 更新點數和欠款
            user.points = remaining_points
            user.owed_points = current_owed - actual_repay
            
            # 如果完全償還欠款，解除凍結
            if actual_repay >= current_owed:
                user.frozen = False
            
            await self.user_repository.update(user)
            
            # 記錄償還日誌
            if actual_repay > 0:
                await self._log_point_change(
                    user.id,
                    "debt_repayment", 
                    actual_repay,
                    f"管理員給予 {amount} 點，償還欠款: {actual_repay} 點"
                )
            
            if remaining_points > 0:
                await self._log_point_change(
                    user.id,
                    "admin_grant",
                    remaining_points,
                    f"償還欠款後剩餘點數: {remaining_points} 點"
                )
        else:
            # 沒有欠款，直接增加點數
            user.add_points(amount)
            await self.user_repository.update(user)
            
            await self._log_point_change(
                user.id,
                "admin_grant",
                amount,
                f"管理員給予點數: {amount} 點"
            )

        return {"message": f"Successfully gave {amount} points to user {username}"}

    async def give_points_to_group(self, team_name: str, amount: int) -> Dict[str, str]:
        """給群組所有成員點數"""
        if amount <= 0:
            raise AdminException("Amount must be positive")

        users = await self.user_repository.find_by_team(team_name)
        if not users:
            raise GroupNotFoundException(team_name)

        # 批量更新點數
        for user in users:
            user.add_points(amount)
            await self.user_repository.update(user)
            
            await self._log_point_change(
                user.id,
                "admin_give_group",
                amount,
                f"管理員給予群組 {team_name} 點數"
            )

        return {"message": f"Successfully gave {amount} points to {len(users)} users in group {team_name}"}

    async def create_announcement(self, title: str, message: str, broadcast: bool = False) -> None:
        """建立公告"""
        announcement_doc = {
            "title": title,
            "message": message,
            "broadcast": broadcast,
            "created_at": datetime.now(timezone.utc),
            "created_by": "admin"
        }

        # 儲存到資料庫 (透過 repository)
        # await self.announcement_repository.create(announcement_doc)

        # 如果需要廣播到 Telegram
        if broadcast:
            await self._broadcast_to_telegram(title, message)

        logger.info(f"Announcement created: {title}")

    async def perform_final_settlement(self, final_price: int = 20) -> Dict[str, str]:
        """執行最終結算"""
        users = await self.user_repository.find_all()
        updated_users = 0
        cancelled_orders = 0

        for user in users:
            stock_holding = await self.stock_repository.find_by_user_id(user.id)
            if stock_holding and stock_holding.stock_amount > 0:
                gain = stock_holding.stock_amount * final_price
                
                # 更新點數並清除股票
                user.add_points(gain)
                await self.user_repository.update(user)
                
                stock_holding.stock_amount = 0
                await self.stock_repository.update(stock_holding)
                
                await self._log_point_change(
                    user.id,
                    "final_settlement",
                    gain,
                    f"最終結算：{stock_holding.stock_amount} 股 × {final_price} 元"
                )
                
                updated_users += 1

        # 清除所有進行中的掛單 (透過相關服務)
        # cancelled_orders = await self.order_service.cancel_all_pending_orders()

        message = f"Final settlement complete for {updated_users} users, cancelled {cancelled_orders} pending orders"
        
        # 傳送系統公告
        await self._send_system_announcement(
            "📊 強制結算完成",
            f"系統已完成強制結算作業，共處理 {updated_users} 位使用者的持股。"
        )

        return {"message": message}

    async def list_all_users(self) -> List[Dict[str, Any]]:
        """列出所有使用者"""
        users = await self.user_repository.find_all()
        result = []
        
        for user in users:
            stock_holding = await self.stock_repository.find_by_user_id(user.id)
            stock_amount = stock_holding.stock_amount if stock_holding else 0
            current_price = await self._get_current_stock_price()
            total_value = user.points + (stock_amount * current_price)

            result.append({
                "id": user.user_id,
                "name": user.name,
                "team": user.team,
                "telegram_id": user.telegram_id,
                "telegram_nickname": user.telegram_nickname,
                "enabled": user.enabled,
                "points": user.points,
                "owed_points": user.owed_points or 0,
                "frozen": user.frozen or False,
                "stock_amount": stock_amount,
                "total_value": total_value,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            })

        return result

    async def list_basic_users(self) -> List[Dict[str, Any]]:
        """取得所有使用者基本資料"""
        users = await self.user_repository.find_all()
        return [
            {
                "username": user.name or user.user_id,
                "telegram_id": user.telegram_id,
                "team": user.team or "未知隊伍"
            }
            for user in users
        ]

    async def list_all_teams(self) -> List[Dict[str, Any]]:
        """列出所有團隊"""
        team_stats = await self.user_repository.get_team_statistics()
        return [
            {
                "name": stat["team"],
                "member_count": stat["member_count"],
                "total_points": stat["total_points"]
            }
            for stat in team_stats
        ]

    async def check_and_fix_negative_balances(self, fix_mode: bool = False) -> Dict[str, Any]:
        """檢查和修復負點數使用者"""
        negative_users = await self.user_repository.find_negative_balance_users()
        
        if not negative_users:
            return {
                "success": True,
                "message": "沒有發現負點數使用者",
                "negative_count": 0,
                "fixed_count": 0,
                "negative_users": []
            }

        negative_user_list = [
            {
                "user_id": str(user.id),
                "username": user.name or "未知",
                "points": user.points,
                "team": user.team or "無"
            }
            for user in negative_users
        ]

        fixed_count = 0
        if fix_mode:
            for user in negative_users:
                original_points = user.points
                user.points = 0
                await self.user_repository.update(user)
                
                await self._log_point_change(
                    user.id,
                    "admin_fix",
                    abs(original_points),
                    f"系統修復負點數：{original_points} -> 0"
                )
                
                fixed_count += 1

            await self._send_system_announcement(
                "🔧 系統維護通知",
                f"系統已修復 {fixed_count} 位使用者的負點數問題。"
            )

        return {
            "success": True,
            "message": f"發現 {len(negative_users)} 位負點數使用者" + (f"，已修復 {fixed_count} 位" if fix_mode else ""),
            "negative_count": len(negative_users),
            "fixed_count": fixed_count,
            "negative_users": negative_user_list
        }

    async def trigger_system_wide_balance_check(self) -> Dict[str, Any]:
        """觸發全面點數完整性檢查"""
        all_users = await self.user_repository.find_all()
        negative_users = [user for user in all_users if user.points < 0]

        if negative_users:
            await self._send_system_announcement(
                "🚨 系統全面檢查警報",
                f"發現 {len(negative_users)} 位使用者有負點數問題"
            )

        return {
            "success": True,
            "message": "系統全面檢查完成",
            "total_checked": len(all_users),
            "negative_count": len(negative_users),
            "negative_users": [
                {
                    "user_id": str(user.id),
                    "username": user.name,
                    "team": user.team,
                    "points": user.points
                }
                for user in negative_users
            ],
            "check_time": datetime.now(timezone.utc).isoformat()
        }

    async def get_all_trades(self, limit: int) -> List[Dict[str, Any]]:
        """取得所有交易記錄"""
        return await self.trade_repository.find_recent_trades_with_user_info(limit)

    async def get_all_point_logs(self, limit: int) -> List[Dict[str, Any]]:
        """取得所有點數日誌"""
        return await self.point_log_repository.find_recent_logs_with_user_info(limit)

    async def trigger_manual_matching(self) -> Dict[str, Any]:
        """手動觸發訂單撮合"""
        # 這個需要透過匹配服務來處理
        # 暫時回傳預設回應
        return {
            "success": True,
            "message": "Manual order matching triggered successfully"
        }

    # 私有輔助方法

    async def _get_current_stock_price(self) -> int:
        """取得目前股票價格"""
        # 透過 market repository 取得
        return 20  # 預設價格

    async def _calculate_user_avg_cost(self, user_id: ObjectId) -> int:
        """計算使用者平均持股成本"""
        trades = await self.trade_repository.find_user_buy_trades(user_id)
        if not trades:
            return 20
        
        total_cost = sum(trade["price"] * trade["quantity"] for trade in trades)
        total_shares = sum(trade["quantity"] for trade in trades)
        
        return int(total_cost / total_shares) if total_shares > 0 else 20

    async def _log_point_change(self, user_id: ObjectId, operation_type: str, amount: int, note: str = "") -> None:
        """記錄點數變化"""
        user = await self.user_repository.find_by_id(user_id)
        current_balance = user.points if user else 0

        log_entry = {
            "user_id": user_id,
            "type": operation_type,
            "amount": amount,
            "note": note,
            "created_at": datetime.now(timezone.utc),
            "balance_after": current_balance
        }

        await self.point_log_repository.create(log_entry)

    async def _broadcast_to_telegram(self, title: str, message: str) -> None:
        """廣播訊息到 Telegram Bot"""
        try:
            telegram_bot_url = config.external_services.telegram_bot_api_url
            if not telegram_bot_url:
                logger.warning("Telegram Bot API URL not configured")
                return

            payload = {"title": title, "message": message}
            headers = {
                "Content-Type": "application/json",
                "token": config.security.internal_api_key
            }

            response = requests.post(telegram_bot_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"Announcement broadcasted successfully: {title}")
            else:
                logger.warning(f"Failed to broadcast: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed during broadcast: {e}")

    async def _send_system_announcement(self, title: str, message: str) -> None:
        """傳送系統公告"""
        await self.create_announcement(title, message, broadcast=True)