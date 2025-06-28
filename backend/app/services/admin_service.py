from __future__ import annotations
from fastapi import Depends, HTTPException, status
from app.core.database import get_database, Collections
from app.schemas.public import (
    AdminLoginRequest, AdminLoginResponse, UserAssetDetail,
    GivePointsRequest, GivePointsResponse, AnnouncementRequest, 
    AnnouncementResponse, MarketUpdateRequest, MarketUpdateResponse,
    MarketLimitRequest, MarketLimitResponse
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
from app.config import settings


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
            
            # 建立 JWT Token
            access_token = create_access_token(data={"sub": "admin"})
            
            logger.info("Admin login successful")
            return AdminLoginResponse(token=access_token)
            
        except Exception as e:
            logger.error(f"Admin login failed: {e}")
            raise AuthenticationException("Login failed")
    
    #　查詢使用者資產明細
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
                "created_at": datetime.utcnow(),
                "created_by": "admin"
            }
            
            # 儲存公告到資料庫
            result = await self.db[Collections.ANNOUNCEMENTS].insert_one(announcement_doc)
            
            # 如果需要廣播，這裡可以加入 Telegram Bot 推送邏輯
            if request.broadcast:
                CAMP_TELEGRAM_BOT_API_URL = settings.CAMP_TELEGRAM_BOT_API_URL
                if not CAMP_TELEGRAM_BOT_API_URL:
                    raise AdminException("Telegram Bot API URL not configured")
                # 使用 requests 傳送 POST 請求到 Telegram Bot API
                payload = {
                    "title": request.title,
                    "message": request.message
                }
                headers = {
                    "Content-Type": "application/json",
                    "token": settings.CAMP_INTERNAL_API_KEY
                }
                logger.info(f"Broadcasting announcement: {request.title} - {request.message} to Telegram Bot API {CAMP_TELEGRAM_BOT_API_URL}")
                response = requests.post(CAMP_TELEGRAM_BOT_API_URL, json=payload, headers=headers)
                if response.status_code != 200:
                    raise AdminException(f"Failed to broadcast announcement: {response.text}")
                logger.info(f"Announcement should be broadcasted: {request.title}")
            
            logger.info(f"Announcement created with ID: {result.inserted_id}")
            return AnnouncementResponse(
                ok=True, 
                message="Announcement created successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to create announcement: {e}")
            raise AdminException("Failed to create announcement")
    
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
                "created_at": datetime.utcnow(),
                "created_by": "system"
            }
            result = await self.db[Collections.ANNOUNCEMENTS].insert_one(announcement_doc)
            logger.info(f"Announcement saved to database with ID: {result.inserted_id}")
            
            # 廣播到 Telegram Bot
            CAMP_TELEGRAM_BOT_API_URL = settings.CAMP_TELEGRAM_BOT_API_URL
            CAMP_INTERNAL_API_KEY = settings.CAMP_INTERNAL_API_KEY
            
            logger.info(f"Bot API URL: {CAMP_TELEGRAM_BOT_API_URL}")
            logger.info(f"API Key: {CAMP_INTERNAL_API_KEY[:10]}..." if CAMP_INTERNAL_API_KEY else "API Key: None")
            
            if CAMP_TELEGRAM_BOT_API_URL:
                payload = {
                    "title": title,
                    "message": message
                }
                headers = {
                    "Content-Type": "application/json",
                    "token": CAMP_INTERNAL_API_KEY
                }
                
                logger.info(f"Sending POST request to: {CAMP_TELEGRAM_BOT_API_URL}")
                logger.info(f"Payload: {payload}")
                
                response = requests.post(CAMP_TELEGRAM_BOT_API_URL, json=payload, headers=headers, timeout=10)
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response text: {response.text}")
                
                if response.status_code == 200:
                    logger.info(f"System announcement broadcasted successfully: {title}")
                else:
                    logger.warning(f"Failed to broadcast system announcement: HTTP {response.status_code} - {response.text}")
            else:
                logger.warning("Telegram Bot API URL not configured, skipping broadcast")
                
        except Exception as e:
            logger.error(f"Failed to send system announcement: {e}", exc_info=True)
            # 不拋出異常，避免影響主要操作
    
    # 更新市場開放時間
    async def update_market_hours(self, request: MarketUpdateRequest) -> MarketUpdateResponse:
        try:
            market_config = {
                "type": "market_hours",
                "openTime": [slot.dict() for slot in request.open_time],
                "updated_at": datetime.utcnow(),
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
            # 將傳入的百分比轉換為基點 (basis points)
            limit_in_basis_points = request.limit_percent * 100
            
            limit_config = {
                "type": "trading_limit",
                "limitPercent": limit_in_basis_points,
                "updated_at": datetime.utcnow(),
                "updated_by": "admin"
            }
            
            # 更新或插入漲跌限制設定
            await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "trading_limit"},
                {"$set": limit_config},
                upsert=True
            )
            
            logger.info(f"Trading limit set to {request.limit_percent}% ({limit_in_basis_points} bp)")
            return MarketLimitResponse(ok=True, limit_percent=request.limit_percent, message=f"Trading limit set to {request.limit_percent}% ({limit_in_basis_points} bp)")
            
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
                stock_amount = order.get("stock_amount") or 0  # Handle None stock_amount
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
                "created_at": datetime.utcnow(),
                "balance_after": current_balance
            }
            
            await self.db[Collections.POINT_LOGS].insert_one(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log point change: {e}")

    # 列出所有學員，回傳其使用者id和所屬隊伍
    async def list_all_users(self) -> List[Dict[str, str]]:
        try:
            # 更新為新的 ID-based 系統字段，包含 enabled 狀態
            users_cursor = self.db[Collections.USERS].find({}, {"id": 1, "name": 1, "team": 1, "telegram_id": 1, "telegram_nickname": 1, "enabled": 1, "points": 1, "stock_amount": 1, "created_at": 1})
            users = await users_cursor.to_list(length=None)
            
            result = []
            for user in users:
                
                result.append({
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "team": user.get("team"),
                    "telegram_id": user.get("telegram_id"),
                    "telegram_nickname": user.get("telegram_nickname"),
                    "enabled": user.get("enabled", False),
                    "points": user.get("points", 0),
                    "stock_amount": user.get("stock_amount", 0),
                    "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
                })
    
    async def list_basic_users(self) -> List[UserBasicInfo]:
        """取得所有使用者的基本資料（僅包含使用者名、Telegram ID、隊伍）"""
        try:
            users_cursor = self.db[Collections.USERS].find({}, {"id": 1, "name": 1, "team": 1, "telegram_id": 1})
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
            raise AdminException("Failed to get basic users") from e
            return result
            
        except Exception as e:
            logger.error(f"Failed to list all users: {e}")
            raise AdminException("Failed to retrieve user list")

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
            logger.info(f"Cancelled {cancelled_orders_count} pending orders during final settlement")

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

    # 手動開盤（包含集合競價）
    async def open_market(self) -> Dict[str, any]:
        try:
            # 首先執行集合競價
            from app.services.user_service import UserService
            user_service = UserService()
            
            call_auction_result = await user_service.call_auction_matching()
            
            # 更新市場狀態為開盤
            await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "manual_control"},
                {
                    "$set": {
                        "is_open": True,
                        "last_updated": datetime.utcnow(),
                        "last_action": "open",
                        "open_time": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # 傳送開盤公告
            if call_auction_result.get("success"):
                announcement_message = f"🔔 市場開盤公告\n\n"
                announcement_message += f"📈 集合競價結果：{call_auction_result.get('matched_volume', 0)} 股於 {call_auction_result.get('auction_price', 0)} 元成交\n"
                announcement_message += f"🎯 市場現已開放交易！"
            else:
                announcement_message = f"🔔 市場開盤公告\n\n"
                announcement_message += f"📊 集合競價：{call_auction_result.get('message', '無成交')}\n"
                announcement_message += f"🎯 市場現已開放交易！"
            
            await self._send_system_announcement(
                title="🔔 市場開盤",
                message=announcement_message
            )
            
            logger.info("Market opened successfully with call auction")
            return {
                "success": True,
                "message": "市場開盤成功",
                "call_auction_result": call_auction_result
            }
            
        except Exception as e:
            logger.error(f"Failed to open market: {e}")
            raise AdminException(f"開盤失敗: {str(e)}")

    # 手動收盤
    async def close_market(self) -> Dict[str, any]:
        try:
            # 取得目前股價作為收盤價
            from app.services.public_service import PublicService
            public_service = PublicService(self.db)
            current_price = await public_service._get_current_stock_price()
            
            # 取得最後成交時間
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "filled"},
                sort=[("created_at", -1)]
            )
            last_trade_time = latest_trade.get("created_at") if latest_trade else None
            
            # 更新市場狀態為收盤，並儲存收盤價
            await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "manual_control"},
                {
                    "$set": {
                        "is_open": False,
                        "last_updated": datetime.utcnow(),
                        "last_action": "close",
                        "close_time": datetime.utcnow(),
                        "closing_price": current_price,
                        "last_trade_time": last_trade_time
                    }
                },
                upsert=True
            )
            
            # 傳送收盤公告
            announcement_message = f"🔔 市場收盤公告\n\n"
            announcement_message += f"⏰ 市場已停止交易\n"
            announcement_message += f"💰 收盤價：{current_price} 元\n"
            announcement_message += f"📊 所有新訂單將暫停處理"
            
            await self._send_system_announcement(
                title="🔔 市場收盤",
                message=announcement_message
            )
            
            logger.info("Market closed successfully")
            return {
                "success": True,
                "message": "市場收盤成功"
            }
            
        except Exception as e:
            logger.error(f"Failed to close market: {e}")
            raise AdminException(f"收盤失敗: {str(e)}")

    # 取得手動市場狀態
    async def get_manual_market_status(self) -> Dict[str, any]:
        try:
            manual_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "manual_control"}
            )
            
            if manual_config:
                return {
                    "is_open": manual_config.get("is_open", False),
                    "last_updated": manual_config.get("last_updated"),
                    "last_action": manual_config.get("last_action"),
                    "open_time": manual_config.get("open_time"),
                    "close_time": manual_config.get("close_time")
                }
            else:
                # 如果沒有手動控制設定，預設為關閉
                return {
                    "is_open": False,
                    "last_updated": None,
                    "last_action": None,
                    "open_time": None,
                    "close_time": None
                }
                
        except Exception as e:
            logger.error(f"Failed to get manual market status: {e}")
            raise AdminException("無法取得市場狀態")

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
                    logger.info(f"Fixed negative balance for user {user.get('username', user['_id'])}: {original_points} -> 0")
                
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
                    logger.error(f"SYSTEM-WIDE CHECK: Negative balance detected - User: {username}, Balance: {current_balance}")
            
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