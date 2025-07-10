from __future__ import annotations
from fastapi import Depends, HTTPException, status
from app.core.database import get_database, Collections
from app.schemas.public import (
    AdminLoginRequest, AdminLoginResponse, UserAssetDetail,
    GivePointsRequest, GivePointsResponse, AnnouncementRequest,
    AnnouncementResponse, MarketUpdateRequest, MarketUpdateResponse,
    MarketLimitRequest, MarketLimitResponse, Trade, PointLog
)
from app.schemas.user import UserBasicInfo
from app.core.security import verify_CAMP_ADMIN_PASSWORD, create_access_token
from app.core.exceptions import (
    AuthenticationException, UserNotFoundException,
    GroupNotFoundException, AdminException
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging
import os
import requests
from app.core.config_refactored import config


logger = logging.getLogger(__name__)

# 依賴注入函數


def get_admin_service() -> AdminService:
    """AdminService 的依賴注入函數"""
    return AdminService()

# 管理員服務類別


class AdminService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db

    # 管理員登入
    async def login(self, request: AdminLoginRequest) -> AdminLoginResponse:
        try:
            if not verify_CAMP_ADMIN_PASSWORD(request.password):
                raise AuthenticationException("Invalid admin password")

            # 建立 JWT Token（包含角色資訊以便 RBAC 系統識別）
            access_token = create_access_token(data={
                "sub": "admin",
                "type": "admin",
                "role": "admin",
                "user_id": "admin"
            })

            logger.info("Admin login successful")
            return AdminLoginResponse(token=access_token)

        except Exception as e:
            logger.error(f"Admin login failed: {e}")
            raise AuthenticationException("Login failed")

    # 　查詢使用者資產明細
    async def get_user_details(self, username: Optional[str] = None) -> List[UserAssetDetail]:
        try:
            # 構建查詢條件 -  ID-based 系統
            query = {}
            if username:
                # 支援用 ID 或姓名查詢
                query = {
                    "$or": [
                        {"name": username},
                        {"id": username}
                    ]
                }

            # 查詢使用者資料
            users_cursor = self.db[Collections.USERS].find(query)
            users = await users_cursor.to_list(length=None)

            if not users and username:
                raise UserNotFoundException(username)

            result = []
            for user in users:
                # 計算使用者的股票持有
                stock_holding = await self.db[Collections.STOCKS].find_one(
                    {"user_id": user["_id"]}
                ) or {"stock_amount": 0}

                # 取得目前股票價格（假設從市場設定取得，單位：元）
                market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                    {"type": "current_price"}
                ) or {"price": 20}  # 預設價格 20 元

                current_price = market_config.get("price", 20)
                stocks = stock_holding.get("stock_amount", 0)
                stock_value = stocks * current_price

                # 計算平均成本（從交易記錄計算）
                avg_cost = await self._calculate_avg_cost(user["_id"])

                user_detail = UserAssetDetail(
                    username=user.get("name", "Unknown"),  # 使用新的 name 字段
                    team=user.get("team", "Unknown"),
                    points=user.get("points", 0),
                    stocks=stocks,
                    avgCost=avg_cost,
                    stockValue=stock_value,
                    total=user.get("points", 0) + stock_value
                )
                result.append(user_detail)

            logger.info(f"Retrieved {len(result)} user details")
            return result

        except Exception as e:
            logger.error(f"Failed to get user details: {e}")
            if isinstance(e, (UserNotFoundException, HTTPException)):
                raise
            raise AdminException("Failed to retrieve user details")

    # 給予點數
    async def give_points(self, request: GivePointsRequest) -> GivePointsResponse:
        try:
            if request.type == "user":
                # 給個人點數 - 新的 ID-based 系統
                user = await self.db[Collections.USERS].find_one({
                    "$or": [
                        {"name": request.username},
                        {"id": request.username}
                    ]
                })
                if not user:
                    raise UserNotFoundException(request.username)

                # 更新使用者點數
                await self.db[Collections.USERS].update_one(
                    {"_id": user["_id"]},
                    {"$inc": {"points": request.amount}}
                )

                # 記錄點數變化
                await self._log_point_change(
                    user["_id"],
                    "admin_give",
                    request.amount,
                    note=f"管理員給予點數"
                )

                message = f"Successfully gave {request.amount} points to user {request.username}"

            elif request.type == "group":
                # 給群組所有成員點數 - 直接使用 team 字段
                team_name = request.username  # 這裡 username 實際是 team name

                # 找到該團隊的所有成員
                users_cursor = self.db[Collections.USERS].find(
                    {"team": team_name}
                )
                users = await users_cursor.to_list(length=None)

                if not users:
                    raise GroupNotFoundException(team_name)

                # 批量更新點數
                user_ids = [user["_id"] for user in users]
                await self.db[Collections.USERS].update_many(
                    {"_id": {"$in": user_ids}},
                    {"$inc": {"points": request.amount}}
                )

                # 記錄所有使用者的點數變化
                for user in users:
                    await self._log_point_change(
                        user["_id"],
                        "admin_give_group",
                        request.amount,
                        note=f"管理員給予群組 {team_name} 點數"
                    )

                message = f"Successfully gave {request.amount} points to {len(users)} users in group {team_name}"

            else:
                raise AdminException("Invalid type, must be 'user' or 'group'")

            logger.info(message)
            return GivePointsResponse(ok=True, message=message)

        except Exception as e:
            logger.error(f"Failed to give points: {e}")
            if isinstance(e, (UserNotFoundException, GroupNotFoundException, AdminException, HTTPException)):
                raise
            raise AdminException("Failed to give points")

    # 建立公告
    async def create_announcement(self, request: AnnouncementRequest) -> AnnouncementResponse:
        try:
            announcement_doc = {
                "title": request.title,
                "message": request.message,
                "broadcast": request.broadcast,
                "created_at": datetime.now(timezone.utc),
                "created_by": "admin"
            }

            # 儲存公告到資料庫
            result = await self.db[Collections.ANNOUNCEMENTS].insert_one(announcement_doc)

            # 如果需要廣播，這裡可以加入 Telegram Bot 推送邏輯
            if request.broadcast:
                CAMP_TELEGRAM_BOT_API_URL = config.external_services.telegram_bot_api_url
                if not CAMP_TELEGRAM_BOT_API_URL:
                    raise AdminException("Telegram Bot API URL not configured")
                # 使用 requests 傳送 POST 請求到 Telegram Bot API
                payload = {
                    "title": request.title,
                    "message": request.message
                }
                headers = {
                    "Content-Type": "application/json",
                    "token": config.security.internal_api_key
                }
                logger.info(
                    f"Broadcasting announcement: {request.title} - {request.message} to Telegram Bot API {CAMP_TELEGRAM_BOT_API_URL}")
                try:
                    response = requests.post(
                        CAMP_TELEGRAM_BOT_API_URL, json=payload, headers=headers, timeout=10)
                    if response.status_code != 200:
                        logger.warning(f"Failed to broadcast announcement: {response.text}")
                        # 不要因為廣播失敗就拋出異常，只記錄警告
                    else:
                        logger.info(f"Announcement successfully broadcasted: {request.title}")
                except requests.exceptions.RequestException as req_e:
                    logger.warning(f"Request failed during announcement broadcast: {req_e}")
                    # 不要因為網絡問題就拋出異常，只記錄警告

            logger.info(f"Announcement created with ID: {result.inserted_id}")
            return AnnouncementResponse(
                ok=True,
                message="Announcement created successfully"
            )

        except Exception as e:
            logger.error(f"Failed to create announcement: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise AdminException(f"Failed to create announcement: {str(e)}")

    # 系統自動公告（用於重置和結算）
    async def _send_system_announcement(self, title: str, message: str):
        """傳送系統自動公告到 Telegram Bot"""
        try:
            logger.info(f"Starting system announcement: {title}")

            # 儲存公告到資料庫
            announcement_doc = {
                "title": title,
                "message": message,
                "broadcast": True,
                "created_at": datetime.now(timezone.utc),
                "created_by": "system"
            }
            result = await self.db[Collections.ANNOUNCEMENTS].insert_one(announcement_doc)
            logger.info(
                f"Announcement saved to database with ID: {result.inserted_id}")

            # 廣播到 Telegram Bot
            CAMP_TELEGRAM_BOT_API_URL = config.external_services.telegram_bot_api_url
            CAMP_INTERNAL_API_KEY = config.security.internal_api_key

            logger.info(f"Bot API URL: {CAMP_TELEGRAM_BOT_API_URL}")
            logger.info(
                f"API Key: {CAMP_INTERNAL_API_KEY[:10]}..." if CAMP_INTERNAL_API_KEY else "API Key: None")

            if CAMP_TELEGRAM_BOT_API_URL:
                payload = {
                    "title": title,
                    "message": message
                }
                headers = {
                    "Content-Type": "application/json",
                    "token": CAMP_INTERNAL_API_KEY
                }

                logger.info(
                    f"Sending POST request to: {CAMP_TELEGRAM_BOT_API_URL}")
                logger.info(f"Payload: {payload}")

                response = requests.post(
                    CAMP_TELEGRAM_BOT_API_URL, json=payload, headers=headers, timeout=10)

                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response text: {response.text}")

                if response.status_code == 200:
                    logger.info(
                        f"System announcement broadcasted successfully: {title}")
                else:
                    logger.warning(
                        f"Failed to broadcast system announcement: HTTP {response.status_code} - {response.text}")
            else:
                logger.warning(
                    "Telegram Bot API URL not configured, skipping broadcast")

        except Exception as e:
            logger.error(
                f"Failed to send system announcement: {e}", exc_info=True)
            # 不拋出異常，避免影響主要操作

    # 更新市場開放時間
    async def update_market_hours(self, request: MarketUpdateRequest) -> MarketUpdateResponse:
        try:
            market_config = {
                "type": "market_hours",
                "openTime": [slot.dict() for slot in request.open_time],
                "updated_at": datetime.now(timezone.utc),
                "updated_by": "admin"
            }

            # 更新或插入市場設定
            await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "market_hours"},
                {"$set": market_config},
                upsert=True
            )

            logger.info("Market hours updated successfully")
            return MarketUpdateResponse(ok=True)

        except Exception as e:
            logger.error(f"Failed to update market hours: {e}")
            raise AdminException("Failed to update market hours")

    # 設定漲跌限制
    async def set_trading_limit(self, request: MarketLimitRequest) -> MarketLimitResponse:
        try:
            # 如果百分比為0，刪除固定限制設定（切換回動態模式）
            if request.limit_percent == 0:
                await self.db[Collections.MARKET_CONFIG].delete_one(
                    {"type": "trading_limit"}
                )
                logger.info("Trading limit cleared, using default fixed limit")
                return MarketLimitResponse(
                    ok=True, 
                    limit_percent=0, 
                    message="固定限制已清除，使用預設固定限制20%"
                )
            
            # 將傳入的百分比轉換為基點 (basis points)
            limit_in_basis_points = request.limit_percent * 100

            limit_config = {
                "type": "trading_limit",
                "limitPercent": limit_in_basis_points,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": "admin"
            }

            # 更新或插入漲跌限制設定
            await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "trading_limit"},
                {"$set": limit_config},
                upsert=True
            )

            logger.info(
                f"Trading limit set to {request.limit_percent}% ({limit_in_basis_points} bp)")
            return MarketLimitResponse(ok=True, limit_percent=request.limit_percent, message=f"固定限制設定為 {request.limit_percent}%")

        except Exception as e:
            logger.error(f"Failed to set trading limit: {e}")
            raise AdminException("Failed to set trading limit")

    # 計算使用者的平均持股成本（單位：元）
    async def _calculate_avg_cost(self, user_id: str) -> int:
        try:
            # 查詢使用者的買入交易記錄
            buy_orders_cursor = self.db[Collections.STOCK_ORDERS].find({
                "user_id": user_id,
                "stock_amount": {"$gt": 0},  # 買入訂單
                "status": "filled"
            })
            buy_orders = await buy_orders_cursor.to_list(length=None)

            if not buy_orders:
                return 20  # 預設初始價格（20 元）

            total_cost = 0
            total_shares = 0

            for order in buy_orders:
                price = order.get("price") or 20  # Handle None price
                # Handle None stock_amount
                stock_amount = order.get("stock_amount") or 0
                cost = price * stock_amount
                total_cost += cost
                total_shares += stock_amount

            return int(total_cost / total_shares) if total_shares > 0 else 20

        except Exception as e:
            logger.error(f"Failed to calculate average cost: {e}")
            return 20  # 回傳預設價格

    # 記錄點數變化
    async def _log_point_change(self, user_id: str, operation_type: str,
                                amount: int, note: str = ""):
        try:
            # 取得使用者目前餘額
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            current_balance = user.get("points", 0) if user else 0

            log_entry = {
                "user_id": user_id,
                "type": operation_type,
                "amount": amount,
                "note": note,
                "created_at": datetime.now(timezone.utc),
                "balance_after": current_balance
            }

            await self.db[Collections.POINT_LOGS].insert_one(log_entry)

        except Exception as e:
            logger.error(f"Failed to log point change: {e}")

    # 列出所有學員，回傳其使用者id和所屬隊伍
    async def list_all_users(self) -> List[Dict[str, str]]:
        try:
            # 更新為新的 ID-based 系統字段，包含 enabled 狀態和債務訊息
            users_cursor = self.db[Collections.USERS].find(
                {}, {"id": 1, "name": 1, "team": 1, "telegram_id": 1, "telegram_nickname": 1, "enabled": 1, "points": 1, "owed_points": 1, "frozen": 1, "created_at": 1, "updated_at": 1})
            users = await users_cursor.to_list(length=None)

            result = []
            for user in users:
                # 獲取使用者的股票持有量（從 STOCKS 集合中獲取）
                stock_holding = await self.db[Collections.STOCKS].find_one(
                    {"user_id": user["_id"]}
                ) or {"stock_amount": 0}
                
                # 計算股票價值
                market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                    {"type": "current_price"}
                ) or {"price": 20}  # 預設價格 20 元
                
                current_price = market_config.get("price", 20)
                stock_amount = stock_holding.get("stock_amount", 0)
                total_value = user.get("points", 0) + (stock_amount * current_price)

                result.append({
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "team": user.get("team"),
                    "telegram_id": user.get("telegram_id"),
                    "telegram_nickname": user.get("telegram_nickname"),
                    "enabled": user.get("enabled", False),
                    "points": user.get("points", 0),
                    "owed_points": user.get("owed_points", 0),
                    "frozen": user.get("frozen", False),
                    "stock_amount": stock_amount,
                    "total_value": total_value,
                    "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
                    "updated_at": user.get("updated_at").isoformat() if user.get("updated_at") else None
                })

            return result

        except Exception as e:
            logger.error(f"Failed to list all users: {e}")
            raise AdminException("Failed to retrieve user list")

    async def list_basic_users(self) -> List[UserBasicInfo]:
        """取得所有使用者的基本資料（僅包含使用者名、Telegram ID、隊伍）"""
        try:
            users_cursor = self.db[Collections.USERS].find(
                {}, {"id": 1, "name": 1, "team": 1, "telegram_id": 1})
            users = await users_cursor.to_list(length=None)

            result = []
            for user in users:
                result.append(UserBasicInfo(
                    username=user.get("name") or user.get("id"),
                    telegram_id=user.get("telegram_id"),
                    team=user.get("team", "未知隊伍")
                ))
            logger.info(f"Retrieved {len(result)} users")
            return result

        except Exception as e:
            logger.error(f"Failed to get basic users: {e}")
            raise AdminException("Failed to get basic users")

    # 列出所有團隊，回傳其名稱、成員數量和點數總和
    async def list_all_teams(self) -> List[Dict[str, str]]:
        try:
            # 從 USERS 集合中統計實際的團隊資訊
            pipeline = [
                # 過濾有團隊資訊的使用者
                {"$match": {"team": {"$ne": None, "$exists": True}}},
                # 按團隊分組並計算成員數量和點數總和
                {"$group": {
                    "_id": "$team",
                    "member_count": {"$sum": 1},
                    "total_points": {"$sum": {"$ifNull": ["$points", 0]}}
                }},
                # 按成員數量降序排列
                {"$sort": {"member_count": -1}}
            ]

            team_stats = await self.db[Collections.USERS].aggregate(pipeline).to_list(None)

            # 轉換為期望的格式
            result = [
                {
                    "name": stat["_id"],
                    "member_count": stat["member_count"],
                    "total_points": stat["total_points"]
                }
                for stat in team_stats
            ]

            logger.info(f"Retrieved {len(result)} teams from user data")
            return result

        except Exception as e:
            logger.error(f"Failed to list all teams: {e}")
            raise AdminException("Failed to retrieve team list")

    # 最終結算：將所有使用者的股票以固定價格換算為點數並清空股票
    async def final_settlement(self, final_price: int = 20) -> GivePointsResponse:
        try:
            users_cursor = self.db[Collections.USERS].find({})
            users = await users_cursor.to_list(length=None)
            updated_users = 0

            for user in users:
                user_id = user["_id"]
                stocks_doc = await self.db[Collections.STOCKS].find_one({"user_id": user_id}) or {}
                stock_amount = stocks_doc.get("stock_amount", 0)

                if stock_amount > 0:
                    gain = stock_amount * final_price

                    # 更新點數與清除股票
                    await self.db[Collections.USERS].update_one(
                        {"_id": user_id},
                        {
                            "$inc": {"points": gain},
                        }
                    )
                    await self.db[Collections.STOCKS].update_one(
                        {"user_id": user_id},
                        {"$set": {"stock_amount": 0}}
                    )

                    await self._log_point_change(
                        user_id=user_id,
                        operation_type="final_settlement",
                        amount=gain,
                        note=f"最終結算：{stock_amount} 股 × {final_price} 元"
                    )

                    updated_users += 1

            # 清除所有進行中的掛單
            cancelled_orders_result = await self.db[Collections.STOCK_ORDERS].update_many(
                {"status": {"$in": ["pending", "partial", "pending_limit"]}},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.now(timezone.utc),
                        "cancellation_reason": "final_settlement"
                    }
                }
            )

            cancelled_orders_count = cancelled_orders_result.modified_count
            logger.info(
                f"Cancelled {cancelled_orders_count} pending orders during final settlement")

            message = f"Final settlement complete for {updated_users} users, cancelled {cancelled_orders_count} pending orders"
            logger.info(message)

            # 傳送系統公告到 Telegram Bot
            await self._send_system_announcement(
                title="📊 強制結算完成",
                message=f"系統已完成強制結算作業，共處理 {updated_users} 位使用者的持股，取消 {cancelled_orders_count} 筆進行中的掛單。所有股票已按固定價格 {final_price} 元轉換為點數。"
            )

            return GivePointsResponse(ok=True, message=message)

        except Exception as e:
            logger.error(f"Failed during final settlement: {e}")
            raise AdminException("Failed during final settlement")


    # 檢查和修復負點數使用者
    async def check_and_fix_negative_balances(self, fix_mode: bool = False) -> Dict[str, any]:
        """
        檢查系統中是否有負點數的使用者，並可選擇性修復

        Args:
            fix_mode: 是否自動修復負點數（設為0）

        Returns:
            dict: 檢查結果和修復統計
        """
        try:
            # 查找所有負點數的使用者
            negative_users = await self.db[Collections.USERS].find(
                {"points": {"$lt": 0}}
            ).to_list(None)

            if not negative_users:
                return {
                    "success": True,
                    "message": "沒有發現負點數使用者",
                    "negative_count": 0,
                    "fixed_count": 0,
                    "negative_users": []
                }

            # 準備負點數使用者列表
            negative_user_list = []
            for user in negative_users:
                user_info = {
                    "user_id": str(user["_id"]),
                    "username": user.get("username", user.get("name", "未知")),
                    "points": user.get("points", 0),
                    "team": user.get("team", "無")
                }
                negative_user_list.append(user_info)

            fixed_count = 0
            if fix_mode:
                # 修復模式：將所有負點數設為0
                for user in negative_users:
                    original_points = user.get("points", 0)

                    # 設定點數為0
                    await self.db[Collections.USERS].update_one(
                        {"_id": user["_id"]},
                        {"$set": {"points": 0}}
                    )

                    # 記錄修復操作
                    from app.services.user_service import UserService
                    user_service = UserService(self.db)
                    await user_service._log_point_change(
                        user_id=user["_id"],
                        change_type="admin_fix",
                        amount=abs(original_points),
                        note=f"系統修復負點數：{original_points} -> 0"
                    )

                    fixed_count += 1
                    logger.info(
                        f"Fixed negative balance for user {user.get('username', user['_id'])}: {original_points} -> 0")

                # 傳送系統公告
                await self._send_system_announcement(
                    title="🔧 系統維護通知",
                    message=f"系統已修復 {fixed_count} 位使用者的負點數問題。所有負點數已重置為 0。"
                )

            return {
                "success": True,
                "message": f"發現 {len(negative_users)} 位負點數使用者" + (f"，已修復 {fixed_count} 位" if fix_mode else ""),
                "negative_count": len(negative_users),
                "fixed_count": fixed_count,
                "negative_users": negative_user_list
            }

        except Exception as e:
            logger.error(f"Failed to check/fix negative balances: {e}")
            raise AdminException(f"檢查負點數失敗: {str(e)}")

    # 手動觸發全面點數完整性檢查
    async def trigger_system_wide_balance_check(self) -> Dict[str, any]:
        """
        對所有使用者進行全面的點數完整性檢查

        Returns:
            dict: 檢查結果統計
        """
        try:
            # 取得所有使用者
            all_users = await self.db[Collections.USERS].find({}).to_list(None)

            negative_users = []
            total_checked = 0

            for user in all_users:
                total_checked += 1
                user_id = user["_id"]
                current_balance = user.get("points", 0)

                if current_balance < 0:
                    username = user.get("username", user.get("name", "未知"))
                    team = user.get("team", "無")

                    negative_users.append({
                        "user_id": str(user_id),
                        "username": username,
                        "team": team,
                        "points": current_balance
                    })

                    # 傳送即時警報
                    logger.error(
                        f"SYSTEM-WIDE CHECK: Negative balance detected - User: {username}, Balance: {current_balance}")

            # 如果發現負點數，傳送彙總報告
            if negative_users:
                summary_message = f"🚨 系統全面檢查結果\n\n"
                summary_message += f"📊 檢查總數：{total_checked} 位使用者\n"
                summary_message += f"⚠️ 發現負點數：{len(negative_users)} 位\n\n"
                summary_message += "負點數使用者列表：\n"

                for i, user in enumerate(negative_users[:5], 1):  # 最多顯示5位
                    summary_message += f"{i}. {user['username']} ({user['team']})：{user['points']} 點\n"

                if len(negative_users) > 5:
                    summary_message += f"...還有 {len(negative_users) - 5} 位使用者\n"

                summary_message += f"\n⏰ 檢查時間：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"

                await self._send_system_announcement(
                    title="🚨 系統全面檢查警報",
                    message=summary_message
                )

            return {
                "success": True,
                "message": f"系統全面檢查完成",
                "total_checked": total_checked,
                "negative_count": len(negative_users),
                "negative_users": negative_users,
                "check_time": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to trigger system-wide balance check: {e}")
            raise AdminException(f"系統全面檢查失敗: {str(e)}")

    async def get_all_trades(self, limit: int) -> List[Trade]:
        try:
            # 使用聚合管道來聯接使用者資料並轉換字段
            pipeline = [
                # 排序：最新的交易在前
                {"$sort": {"created_at": -1}},
                # 限制結果數量
                {"$limit": limit},
                # 聯接買方使用者資料
                {
                    "$lookup": {
                        "from": Collections.USERS,
                        "localField": "buy_user_id", 
                        "foreignField": "_id",
                        "as": "buyer_info"
                    }
                },
                # 聯接賣方使用者資料 (排除系統賣方)
                {
                    "$lookup": {
                        "from": Collections.USERS,
                        "localField": "sell_user_id",
                        "foreignField": "_id", 
                        "as": "seller_info"
                    }
                },
                # 轉換為期望的格式
                {
                    "$project": {
                        "id": {"$toString": "$_id"},
                        "buyer_username": {
                            "$cond": {
                                "if": {"$eq": [{"$size": "$buyer_info"}, 0]},
                                "then": "未知使用者",
                                "else": {"$arrayElemAt": ["$buyer_info.name", 0]}
                            }
                        },
                        "seller_username": {
                            "$cond": {
                                "if": {"$in": ["$sell_user_id", ["SYSTEM", "MARKET"]]},
                                "then": "$sell_user_id",
                                "else": {
                                    "$cond": {
                                        "if": {"$eq": [{"$size": "$seller_info"}, 0]},
                                        "then": "未知使用者", 
                                        "else": {"$arrayElemAt": ["$seller_info.name", 0]}
                                    }
                                }
                            }
                        },
                        "price": 1,
                        "amount": "$quantity",
                        "timestamp": "$created_at"
                    }
                }
            ]
            
            trades_cursor = self.db[Collections.TRADES].aggregate(pipeline)
            trades = await trades_cursor.to_list(length=None)
            
            # 轉換為 Trade 物件
            return [Trade(**trade) for trade in trades]
            
        except Exception as e:
            logger.error(f"Failed to get all trades: {e}")
            raise AdminException("Failed to retrieve trades")

    async def get_all_point_logs(self, limit: int) -> List[PointLog]:
        try:
            # 只查詢有 amount 欄位的記錄（排除 role_change 等非點數交易記錄）
            logs_cursor = self.db[Collections.POINT_LOGS].find({"amount": {"$exists": True}}).sort("created_at", -1).limit(limit)
            logs_raw = await logs_cursor.to_list(length=None)
            
            # 轉換為 PointLog 物件，處理 ObjectId 轉換和不同記錄格式
            point_logs = []
            for log in logs_raw:
                # 將 ObjectId 轉換為字串
                log_dict = {
                    "user_id": str(log["user_id"]),
                    "type": log.get("type", "qr_scan"),  # 如果沒有 type，可能是 QR 掃描
                    "amount": log["amount"],
                    "note": log["note"],
                    "created_at": log["created_at"],
                    "balance_after": log["balance_after"]
                }
                
                # 如果有 qr_id，則表示是 QR 掃描記錄
                if "qr_id" in log and "type" not in log:
                    log_dict["type"] = "qr_scan"
                
                point_logs.append(PointLog(**log_dict))
            
            return point_logs
            
        except Exception as e:
            logger.error(f"Failed to get all point logs: {e}")
            raise AdminException("Failed to retrieve point logs")

    async def trigger_manual_matching(self) -> dict:
        """手動觸發訂單撮合"""
        try:
            from app.services.matching_scheduler import get_matching_scheduler
            
            scheduler = get_matching_scheduler()
            if not scheduler:
                raise AdminException("Matching scheduler not initialized")
                
            # 檢查是否正在撮合
            if scheduler.is_matching_in_progress():
                return {
                    "success": False,
                    "message": "Order matching is already in progress"
                }
                
            # 觸發撮合
            await scheduler.trigger_matching("manual_admin_trigger")
            
            return {
                "success": True,
                "message": "Manual order matching triggered successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger manual matching: {e}")
            raise AdminException(f"Failed to trigger manual matching: {str(e)}")
