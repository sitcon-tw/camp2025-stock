from __future__ import annotations
from fastapi import Depends, HTTPException, status
from app.core.database import get_database, Collections
from app.schemas.public import (
    AdminLoginRequest, AdminLoginResponse, UserAssetDetail,
    GivePointsRequest, GivePointsResponse, AnnouncementRequest, 
    AnnouncementResponse, MarketUpdateRequest, MarketUpdateResponse,
    MarketLimitRequest, MarketLimitResponse
)
from app.core.security import verify_CAMP_ADMIN_PASSWORD, create_access_token
from app.core.exceptions import (
    AuthenticationException, UserNotFoundException, 
    GroupNotFoundException, AdminException
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
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
                
                # 取得目前股票價格（假設從市場配置取得，單位：元）
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
        """發送系統自動公告到 Telegram Bot"""
        try:
            # 儲存公告到資料庫
            announcement_doc = {
                "title": title,
                "message": message,
                "broadcast": True,
                "created_at": datetime.utcnow(),
                "created_by": "system"
            }
            await self.db[Collections.ANNOUNCEMENTS].insert_one(announcement_doc)
            
            # 廣播到 Telegram Bot
            CAMP_TELEGRAM_BOT_API_URL = settings.CAMP_TELEGRAM_BOT_API_URL
            if CAMP_TELEGRAM_BOT_API_URL:
                payload = {
                    "title": title,
                    "message": message
                }
                headers = {
                    "Content-Type": "application/json",
                    "token": settings.CAMP_INTERNAL_API_KEY
                }
                logger.info(f"Broadcasting system announcement: {title}")
                response = requests.post(CAMP_TELEGRAM_BOT_API_URL, json=payload, headers=headers)
                if response.status_code == 200:
                    logger.info(f"System announcement broadcasted successfully: {title}")
                else:
                    logger.warning(f"Failed to broadcast system announcement: {response.text}")
            else:
                logger.warning("Telegram Bot API URL not configured, skipping broadcast")
                
        except Exception as e:
            logger.error(f"Failed to send system announcement: {e}")
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
            
            # 更新或插入市場配置
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
            limit_config = {
                "type": "trading_limit",
                "limitPercent": request.limit_percent,
                "updated_at": datetime.utcnow(),
                "updated_by": "admin"
            }
            
            # 更新或插入漲跌限制配置
            await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "trading_limit"},
                {"$set": limit_config},
                upsert=True
            )
            
            logger.info(f"Trading limit set to {request.limit_percent}%")
            return MarketLimitResponse(ok=True)
            
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
            users_cursor = self.db[Collections.USERS].find({}, {"id": 1, "name": 1, "team": 1, "enabled": 1})
            users = await users_cursor.to_list(length=None)
            
            result = []
            for user in users:
                user_id = user.get("id", user.get("username", str(user.get("_id", "unknown"))))
                user_name = user.get("name", user.get("username", "Unknown"))
                
                result.append({
                    "id": user_id,
                    "username": user_name,  # 為了前端相容性，保持 username 
                    "name": user_name,       # 新的 name 字段
                    "team": user.get("team", "Unknown"),
                    "enabled": user.get("enabled", False)  # 新增啟用狀態
                })
            logger.info(f"Retrieved {len(result)} users")
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

            message = f"Final settlement complete for {updated_users} users"
            logger.info(message)
            
            # 發送系統公告到 Telegram Bot
            await self._send_system_announcement(
                title="📊 強制結算完成",
                message=f"系統已完成強制結算作業，共處理 {updated_users} 位使用者的持股。所有股票已按固定價格 {final_price} 元轉換為點數。"
            )
            
            return GivePointsResponse(ok=True, message=message)

        except Exception as e:
            logger.error(f"Failed during final settlement: {e}")
            raise AdminException("Failed during final settlement")