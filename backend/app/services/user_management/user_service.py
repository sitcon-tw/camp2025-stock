from __future__ import annotations
from .base_service import BaseService
from ..market import get_market_service
from ..trading import get_trading_service
from .transfer_service import get_transfer_service
from ..matching import get_order_matching_service
from app.core.database import Collections
from app.schemas.user import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserLoginRequest, UserLoginResponse, UserPortfolio,
    StockOrderRequest, StockOrderResponse,
    TransferRequest, TransferResponse,
    UserPointLog, UserStockOrder
)
from app.core.security import create_access_token
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


def get_user_service() -> UserService:
    """UserService 的依賴注入函數"""
    return UserService()


class UserService(BaseService):
    """用戶服務 - 負責處理用戶管理相關功能"""
    
    def __init__(self, db=None):
        super().__init__(db)
        self.market_service = get_market_service()
        self.trading_service = get_trading_service()
        self.transfer_service = get_transfer_service()
        self.order_matching_service = get_order_matching_service()
    
    async def login_user(self, request: UserLoginRequest) -> UserLoginResponse:
        """用戶登入"""
        try:
            # 查找用戶
            user = await self.db[Collections.USERS].find_one({"telegram_id": request.telegram_id})
            if not user:
                # 創建新用戶
                user = await self._create_user_from_telegram(request)
                if not user:
                    return UserLoginResponse(
                        success=False,
                        message="用戶創建失敗"
                    )
            
            # 更新最後登入時間
            await self.db[Collections.USERS].update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            
            # 生成 JWT Token
            access_token = create_access_token(
                data={"user_id": str(user["_id"]), "telegram_id": request.telegram_id}
            )
            
            return UserLoginResponse(
                success=True,
                access_token=access_token,
                user_id=str(user["_id"]),
                username=user.get("username", user.get("name", "")),
                message="登入成功"
            )
            
        except Exception as e:
            logger.error(f"Failed to login user: {e}")
            return UserLoginResponse(
                success=False,
                message=f"登入失敗：{str(e)}"
            )
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """根據 Telegram ID 獲取用戶"""
        return await self._get_user_by_telegram_id(telegram_id)
    
    async def get_user_portfolio(self, user_id: str) -> UserPortfolio:
        """獲取用戶投資組合"""
        try:
            user_oid = ObjectId(user_id)
            
            # 獲取用戶資料
            user = await self._get_user_by_id(user_id)
            if not user:
                return UserPortfolio(
                    user_id=user_id,
                    username="未知用戶",
                    points=0,
                    stock_amount=0,
                    stock_value=0,
                    total_value=0,
                    average_cost=0.0
                )
            
            # 獲取持股資料
            stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user_oid})
            stock_amount = stock_holding.get("stock_amount", 0) if stock_holding else 0
            
            # 獲取當前股價
            current_price = await self.market_service.get_current_stock_price()
            
            # 計算平均成本
            avg_cost = await self._calculate_user_avg_cost(user_oid)
            
            # 計算總值
            points = user.get("points", 0)
            stock_value = stock_amount * current_price
            total_value = points + stock_value
            
            return UserPortfolio(
                user_id=user_id,
                username=user.get("username", user.get("name", "")),
                points=points,
                stock_amount=stock_amount,
                stock_value=stock_value,
                total_value=total_value,
                average_cost=avg_cost
            )
            
        except Exception as e:
            logger.error(f"Failed to get user portfolio: {e}")
            return UserPortfolio(
                user_id=user_id,
                username="錯誤",
                points=0,
                stock_amount=0,
                stock_value=0,
                total_value=0,
                average_cost=0.0
            )
    
    async def place_stock_order(self, user_id: str, request: StockOrderRequest) -> StockOrderResponse:
        """下股票訂單（委託給交易服務）"""
        return await self.trading_service.place_stock_order(user_id, request)
    
    async def transfer_points(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """轉帳點數（委託給轉帳服務）"""
        return await self.transfer_service.transfer_points(from_user_id, request)
    
    async def get_user_point_logs(self, user_id: str, limit: int = 50) -> List[UserPointLog]:
        """獲取用戶點數日誌"""
        try:
            user_oid = ObjectId(user_id)
            
            # 獲取點數日誌
            logs_cursor = self.db[Collections.POINT_LOGS].find(
                {"user_id": user_oid}
            ).sort("timestamp", -1).limit(limit)
            
            logs = await logs_cursor.to_list(length=limit)
            
            # 格式化日誌
            formatted_logs = []
            for log in logs:
                formatted_log = UserPointLog(
                    log_id=log.get("log_id", str(log["_id"])),
                    change_type=log.get("change_type", "unknown"),
                    amount=log.get("amount", 0),
                    description=log.get("description", ""),
                    timestamp=log.get("timestamp", log.get("created_at")),
                    balance_after=log.get("balance_after", 0)
                )
                formatted_logs.append(formatted_log)
            
            return formatted_logs
            
        except Exception as e:
            logger.error(f"Failed to get user point logs: {e}")
            return []
    
    async def get_user_stock_orders(self, user_id: str, limit: int = 50) -> List[UserStockOrder]:
        """獲取用戶股票訂單（委託給交易服務）"""
        orders = await self.trading_service.get_user_stock_orders(user_id, limit)
        
        # 轉換為 UserStockOrder 格式
        formatted_orders = []
        for order in orders:
            formatted_order = UserStockOrder(
                order_id=order["order_id"],
                order_type=order["order_type"],
                side=order["side"],
                quantity=order["quantity"],
                price=order["price"],
                status=order["status"],
                created_at=order["created_at"],
                filled_quantity=order.get("filled_quantity", 0),
                filled_price=order.get("filled_price"),
                filled_at=order.get("filled_at")
            )
            formatted_orders.append(formatted_order)
        
        return formatted_orders
    
    async def cancel_stock_order(self, user_id: str, order_id: str, reason: str = "user_cancelled") -> Dict[str, Any]:
        """取消股票訂單（委託給交易服務）"""
        return await self.trading_service.cancel_stock_order(user_id, order_id, reason)
    
    async def get_user_profile_by_id(self, user_id: str) -> Dict[str, Any]:
        """根據 ID 獲取用戶資料"""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                return {"success": False, "message": "用戶不存在"}
            
            # 獲取持股資料
            stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user["_id"]})
            stock_amount = stock_holding.get("stock_amount", 0) if stock_holding else 0
            
            profile = {
                "user_id": str(user["_id"]),
                "username": user.get("username", user.get("name", "")),
                "telegram_id": user.get("telegram_id"),
                "points": user.get("points", 0),
                "stock_amount": stock_amount,
                "enabled": user.get("enabled", True),
                "frozen": user.get("frozen", False),
                "owed_points": user.get("owed_points", 0),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            }
            
            return {"success": True, "profile": profile}
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return {"success": False, "message": f"獲取用戶資料失敗：{str(e)}"}
    
    async def create_student(self, student_id: str, username: str) -> bool:
        """創建學生帳戶"""
        try:
            # 檢查是否已存在
            existing_user = await self.db[Collections.USERS].find_one({"student_id": student_id})
            if existing_user:
                return False
            
            # 創建新學生帳戶
            user_doc = {
                "student_id": student_id,
                "username": username,
                "name": username,
                "points": 0,
                "enabled": False,  # 需要啟用
                "frozen": False,
                "owed_points": 0,
                "created_at": datetime.now(timezone.utc),
                "user_type": "student"
            }
            
            await self.db[Collections.USERS].insert_one(user_doc)
            logger.info(f"Created student account: {student_id} - {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create student: {e}")
            return False
    
    async def activate_student(self, student_id: str, telegram_id: str, telegram_nickname: str) -> Dict[str, Any]:
        """啟用學生帳戶"""
        try:
            # 查找學生帳戶
            student = await self.db[Collections.USERS].find_one({"student_id": student_id})
            if not student:
                return {"success": False, "message": "學生帳戶不存在"}
            
            # 檢查是否已啟用
            if student.get("enabled", False):
                return {"success": False, "message": "帳戶已啟用"}
            
            # 檢查 Telegram ID 是否已被使用
            existing_telegram = await self.db[Collections.USERS].find_one({"telegram_id": telegram_id})
            if existing_telegram:
                return {"success": False, "message": "此 Telegram 帳戶已被使用"}
            
            # 啟用帳戶
            await self.db[Collections.USERS].update_one(
                {"_id": student["_id"]},
                {
                    "$set": {
                        "telegram_id": telegram_id,
                        "telegram_nickname": telegram_nickname,
                        "enabled": True,
                        "activated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Activated student account: {student_id} - {telegram_id}")
            return {"success": True, "message": "帳戶啟用成功"}
            
        except Exception as e:
            logger.error(f"Failed to activate student: {e}")
            return {"success": False, "message": f"啟用失敗：{str(e)}"}
    
    async def get_student_status(self, student_id: str) -> Dict[str, Any]:
        """獲取學生狀態"""
        try:
            student = await self.db[Collections.USERS].find_one({"student_id": student_id})
            if not student:
                return {"success": False, "message": "學生不存在"}
            
            status = {
                "student_id": student_id,
                "username": student.get("username", ""),
                "enabled": student.get("enabled", False),
                "telegram_id": student.get("telegram_id"),
                "telegram_nickname": student.get("telegram_nickname", ""),
                "points": student.get("points", 0),
                "created_at": student.get("created_at"),
                "activated_at": student.get("activated_at")
            }
            
            return {"success": True, "status": status}
            
        except Exception as e:
            logger.error(f"Failed to get student status: {e}")
            return {"success": False, "message": f"獲取狀態失敗：{str(e)}"}
    
    async def update_students(self, student_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量更新學生資料"""
        try:
            success_count = 0
            error_count = 0
            
            for student in student_data:
                student_id = student.get("student_id")
                username = student.get("username")
                
                if not student_id or not username:
                    error_count += 1
                    continue
                
                # 嘗試創建或更新
                result = await self.db[Collections.USERS].update_one(
                    {"student_id": student_id},
                    {
                        "$set": {
                            "username": username,
                            "name": username,
                            "updated_at": datetime.now(timezone.utc)
                        },
                        "$setOnInsert": {
                            "points": 0,
                            "enabled": False,
                            "frozen": False,
                            "owed_points": 0,
                            "created_at": datetime.now(timezone.utc),
                            "user_type": "student"
                        }
                    },
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    success_count += 1
                else:
                    error_count += 1
            
            return {
                "success": True,
                "message": f"處理完成：成功 {success_count}，失敗 {error_count}",
                "success_count": success_count,
                "error_count": error_count
            }
            
        except Exception as e:
            logger.error(f"Failed to update students: {e}")
            return {"success": False, "message": f"批量更新失敗：{str(e)}"}
    
    async def _create_user_from_telegram(self, request: UserLoginRequest) -> Optional[Dict[str, Any]]:
        """從 Telegram 登入請求創建用戶"""
        try:
            user_doc = {
                "telegram_id": request.telegram_id,
                "username": request.username,
                "name": request.username,
                "points": 0,
                "enabled": True,
                "frozen": False,
                "owed_points": 0,
                "created_at": datetime.now(timezone.utc),
                "user_type": "telegram"
            }
            
            result = await self.db[Collections.USERS].insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            
            logger.info(f"Created new user from Telegram: {request.telegram_id} - {request.username}")
            return user_doc
            
        except Exception as e:
            logger.error(f"Failed to create user from Telegram: {e}")
            return None
    
    async def _calculate_user_avg_cost(self, user_oid: ObjectId) -> float:
        """計算用戶平均成本"""
        try:
            # 查找所有買入訂單
            buy_orders = await self.db[Collections.STOCK_ORDERS].find(
                {
                    "user_id": user_oid,
                    "side": "buy",
                    "status": "filled"
                }
            ).to_list(None)
            
            if not buy_orders:
                return 0.0
            
            total_cost = 0.0
            total_quantity = 0
            
            for order in buy_orders:
                filled_quantity = order.get("filled_quantity", order.get("quantity", 0))
                filled_price = order.get("filled_price", order.get("price", 0))
                
                total_cost += filled_quantity * filled_price
                total_quantity += filled_quantity
            
            return total_cost / total_quantity if total_quantity > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate user average cost: {e}")
            return 0.0
    
    # 保留一些原有的方法委託給其他服務
    async def get_all_point_logs(self, limit: int = None) -> List[Dict[str, Any]]:
        """獲取所有點數日誌（管理員功能）"""
        try:
            query = {}
            cursor = self.db[Collections.POINT_LOGS].find(query).sort("timestamp", -1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            logs = await cursor.to_list(length=limit)
            
            # 格式化日誌並加入用戶資訊
            formatted_logs = []
            for log in logs:
                user_id = log.get("user_id")
                user = await self._get_user_by_id(str(user_id)) if user_id else None
                
                formatted_log = {
                    "log_id": log.get("log_id", str(log["_id"])),
                    "user_id": str(user_id) if user_id else None,
                    "username": user.get("username", user.get("name", "未知")) if user else "未知",
                    "change_type": log.get("change_type", "unknown"),
                    "amount": log.get("amount", 0),
                    "description": log.get("description", ""),
                    "timestamp": log.get("timestamp", log.get("created_at")),
                    "balance_after": log.get("balance_after", 0),
                    "transaction_id": log.get("transaction_id")
                }
                formatted_logs.append(formatted_log)
            
            return formatted_logs
            
        except Exception as e:
            logger.error(f"Failed to get all point logs: {e}")
            return []
    
    async def debug_user_data(self, username: str) -> Dict[str, Any]:
        """調試用戶資料"""
        try:
            user = await self.db[Collections.USERS].find_one({"username": username})
            if not user:
                return {"success": False, "message": "用戶不存在"}
            
            # 獲取持股資料
            stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user["_id"]})
            
            # 獲取訂單資料
            orders = await self.db[Collections.STOCK_ORDERS].find(
                {"user_id": user["_id"]}
            ).sort("created_at", -1).limit(10).to_list(10)
            
            # 獲取點數日誌
            point_logs = await self.db[Collections.POINT_LOGS].find(
                {"user_id": user["_id"]}
            ).sort("timestamp", -1).limit(10).to_list(10)
            
            debug_data = {
                "user": {
                    "id": str(user["_id"]),
                    "username": user.get("username", ""),
                    "points": user.get("points", 0),
                    "enabled": user.get("enabled", True),
                    "frozen": user.get("frozen", False),
                    "owed_points": user.get("owed_points", 0)
                },
                "stock_holding": {
                    "stock_amount": stock_holding.get("stock_amount", 0) if stock_holding else 0
                },
                "recent_orders": [
                    {
                        "order_id": str(order["_id"]),
                        "side": order.get("side"),
                        "quantity": order.get("quantity"),
                        "price": order.get("price"),
                        "status": order.get("status"),
                        "created_at": order.get("created_at")
                    } for order in orders
                ],
                "recent_point_logs": [
                    {
                        "change_type": log.get("change_type"),
                        "amount": log.get("amount"),
                        "description": log.get("description"),
                        "timestamp": log.get("timestamp", log.get("created_at")),
                        "balance_after": log.get("balance_after")
                    } for log in point_logs
                ]
            }
            
            return {"success": True, "debug_data": debug_data}
            
        except Exception as e:
            logger.error(f"Failed to debug user data: {e}")
            return {"success": False, "message": f"調試失敗：{str(e)}"}