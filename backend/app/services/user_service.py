from __future__ import annotations
from fastapi import Depends, HTTPException, status
from app.core.database import get_database, Collections
from app.schemas.user import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserLoginRequest, UserLoginResponse, UserPortfolio,
    StockOrderRequest, StockOrderResponse,
    TransferRequest, TransferResponse,
    PVPChallengeRequest, PVPChallengeResponse,
    PVPAcceptRequest, PVPResult,
    UserPointLog, UserStockOrder
)
from app.core.security import create_access_token
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
import logging
import random
import uuid

logger = logging.getLogger(__name__)

# 依賴注入函數
def get_user_service() -> UserService:
    """UserService 的依賴注入函數"""
    return UserService()

# 使用者服務類別
class UserService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
    
    # 使用者註冊
    async def register_user(self, request: UserRegistrationRequest) -> UserRegistrationResponse:
        try:
            # 檢查使用者名是否已存在
            existing_user = await self.db[Collections.USERS].find_one({
                "username": request.username
            })
            if existing_user:
                return UserRegistrationResponse(
                    success=False,
                    message="使用者名已存在"
                )
            
            # 檢查 email 是否已存在（跳過臨時 email）
            if not request.email.endswith("@temp.local"):
                existing_email = await self.db[Collections.USERS].find_one({
                    "email": request.email
                })
                if existing_email:
                    return UserRegistrationResponse(
                        success=False,
                        message="Email 已被使用"
                    )
            
            # 查找或建立群組
            group = await self.db[Collections.GROUPS].find_one({"name": request.team})
            if not group:
                group_result = await self.db[Collections.GROUPS].insert_one({
                    "name": request.team,
                    "created_at": datetime.now(timezone.utc)
                })
                group_id = group_result.inserted_id
            else:
                group_id = group["_id"]
            
            # 建立使用者
            user_doc = {
                "username": request.username,
                "email": request.email,
                "team": request.team,
                "group_id": group_id,
                "points": 100,  # 初始點數
                "telegram_id": request.telegram_id,
                "activation_code": request.activation_code,
                "is_active": True,
                "created_at": datetime.now(timezone.utc)
            }
            
            result = await self.db[Collections.USERS].insert_one(user_doc)
            
            # 初始化股票持有記錄
            await self.db[Collections.STOCKS].insert_one({
                "user_id": result.inserted_id,
                "stock_amount": 0,
                "updated_at": datetime.now(timezone.utc)
            })
            
            # 記錄初始點數
            await self._log_point_change(
                result.inserted_id,
                "initial",
                100,
                "使用者註冊初始點數"
            )
            
            logger.info(f"User registered successfully: {request.username}")
            
            return UserRegistrationResponse(
                success=True,
                message="註冊成功",
                user_id=str(result.inserted_id)
            )
            
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            return UserRegistrationResponse(
                success=False,
                message="註冊失敗，請稍後再試"
            )
    
    # 使用者登入
    async def login_user(self, request: UserLoginRequest) -> UserLoginResponse:
        try:
            # 查找使用者
            query = {"username": request.username, "is_active": True}
            if request.telegram_id:
                query["telegram_id"] = request.telegram_id
            
            user = await self.db[Collections.USERS].find_one(query)
            if not user:
                return UserLoginResponse(
                    success=False,
                    message="使用者不存在或未啟用"
                )
            
            # 建立使用者 Token
            token = create_access_token(data={
                "sub": str(user["_id"]),
                "username": user["username"],
                "type": "user"
            })
            
            # 回傳使用者資訊（不包含敏感資料）
            user_info = {
                "username": user["username"],
                "team": user["team"],
                "points": user["points"]
            }
            
            return UserLoginResponse(
                success=True,
                token=token,
                user=user_info
            )
            
        except Exception as e:
            logger.error(f"User login failed: {e}")
            return UserLoginResponse(
                success=False,
                message="登入失敗"
            )
    
    # 取得使用者投資組合
    async def get_user_portfolio(self, user_id: str) -> UserPortfolio:
        try:
            # 取得使用者資訊
            user_oid = ObjectId(user_id)
            user = await self.db[Collections.USERS].find_one({"_id": user_oid})
            if not user:
                raise HTTPException(status_code=404, detail="使用者不存在")
            
            # 取得股票持有
            stock_holding = await self.db[Collections.STOCKS].find_one(
                {"user_id": user_oid}
            ) or {"stock_amount": 0}
            
            # 取得目前股價
            current_price = await self._get_current_stock_price()
            
            # 計算平均成本
            avg_cost = await self._calculate_user_avg_cost(user_oid)
            
            stocks = stock_holding.get("stock_amount", 0)
            stock_value = stocks * current_price
            total_value = user.get("points", 0) + stock_value
            
            return UserPortfolio(
                username=user["username"],
                points=user.get("points", 0),
                stocks=stocks,
                stockValue=stock_value,
                totalValue=total_value,
                avgCost=avg_cost
            )
            
        except Exception as e:
            logger.error(f"Failed to get user portfolio: {e}")
            raise HTTPException(
                status_code=500,
                detail="取得投資組合失敗"
            )
    
    # 下股票訂單
    async def place_stock_order(self, user_id: str, request: StockOrderRequest) -> StockOrderResponse:
        try:
            # 檢查市場是否開放
            if not await self._is_market_open():
                return StockOrderResponse(
                    success=False,
                    message="市場目前未開放交易"
                )
            
            # 取得使用者資訊
            user_oid = ObjectId(user_id)
            user = await self.db[Collections.USERS].find_one({"_id": user_oid})
            if not user:
                return StockOrderResponse(
                    success=False,
                    message="使用者不存在"
                )
            
            # 檢查使用者資金和持股
            if request.side == "buy":
                if request.order_type == "market":
                    current_price = await self._get_current_stock_price()
                    required_points = int(current_price * request.quantity)
                else:
                    required_points = int(request.price * request.quantity)
                
                if user.get("points", 0) < required_points:
                    return StockOrderResponse(
                        success=False,
                        message="點數不足"
                    )
            
            elif request.side == "sell":
                stock_holding = await self.db[Collections.STOCKS].find_one(
                    {"user_id": user_oid}
                )
                current_stocks = stock_holding.get("stock_amount", 0) if stock_holding else 0
                
                if current_stocks < request.quantity:
                    return StockOrderResponse(
                        success=False,
                        message="持股不足"
                    )
            
            # 建立訂單
            order_doc = {
                "user_id": user_oid,
                "order_type": request.order_type,
                "side": request.side,
                "quantity": request.quantity,
                "price": request.price,
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
                "stock_amount": request.quantity if request.side == "buy" else -request.quantity
            }
            
            # 如果是市價單，立即執行
            if request.order_type == "market":
                execution_result = await self._execute_market_order(user_oid, order_doc)
                return execution_result
            else:
                # 限價單加入訂單簿
                result = await self.db[Collections.STOCK_ORDERS].insert_one(order_doc)
                
                # 嘗試撮合
                await self._try_match_orders()
                
                return StockOrderResponse(
                    success=True,
                    order_id=str(result.inserted_id),
                    message="限價單已提交"
                )
                
        except Exception as e:
            logger.error(f"Failed to place stock order: {e}")
            return StockOrderResponse(
                success=False,
                message="下單失敗"
            )
    
    # 轉帳功能
    async def transfer_points(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        try:
            # 取得發送方使用者
            from_user_oid = ObjectId(from_user_id)
            from_user = await self.db[Collections.USERS].find_one({"_id": from_user_oid})
            if not from_user:
                return TransferResponse(
                    success=False,
                    message="發送方使用者不存在"
                )
            
            # 取得接收方使用者
            to_user = await self.db[Collections.USERS].find_one({
                "username": request.to_username
            })
            if not to_user:
                return TransferResponse(
                    success=False,
                    message="接收方使用者不存在"
                )
            
            # 計算手續費 (1%)
            fee = max(1, int(request.amount * 0.01))
            total_deduct = request.amount + fee
            
            # 檢查餘額
            if from_user.get("points", 0) < total_deduct:
                return TransferResponse(
                    success=False,
                    message="餘額不足（包含手續費）"
                )
            
            # 執行轉帳
            transaction_id = str(uuid.uuid4())
            
            # 扣除發送方點數
            await self.db[Collections.USERS].update_one(
                {"_id": from_user_oid},
                {"$inc": {"points": -total_deduct}}
            )
            
            # 增加接收方點數
            await self.db[Collections.USERS].update_one(
                {"_id": to_user["_id"]},
                {"$inc": {"points": request.amount}}
            )
            
            # 記錄轉帳日誌
            await self._log_point_change(
                from_user_oid,
                "transfer_out",
                -total_deduct,
                f"轉帳給 {request.to_username} (含手續費 {fee})",
                transaction_id
            )
            
            await self._log_point_change(
                to_user["_id"],
                "transfer_in",
                request.amount,
                f"收到來自 {from_user['username']} 的轉帳",
                transaction_id
            )
            
            return TransferResponse(
                success=True,
                message="轉帳成功",
                transaction_id=transaction_id,
                fee=fee
            )
            
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return TransferResponse(
                success=False,
                message="轉帳失敗"
            )
    
    # 取得使用者點數記錄
    async def get_user_point_logs(self, user_id: str, limit: int = 50) -> List[UserPointLog]:
        try:
            user_oid = ObjectId(user_id)
            logs_cursor = self.db[Collections.POINT_LOGS].find({
                "user_id": user_oid
            }).sort("created_at", -1).limit(limit)
            
            logs = await logs_cursor.to_list(length=limit)
            
            return [
                UserPointLog(
                    type=log.get("type", "unknown"),
                    amount=log.get("amount", 0),
                    balance_after=log.get("balance_after", 0),
                    note=log.get("note", ""),
                    created_at=log.get("created_at", datetime.now(timezone.utc)).isoformat()
                )
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user point logs: {e}")
            return []
    
    # 取得使用者股票訂單記錄
    async def get_user_stock_orders(self, user_id: str, limit: int = 50) -> List[UserStockOrder]:
        try:
            user_oid = ObjectId(user_id)
            orders_cursor = self.db[Collections.STOCK_ORDERS].find({
                "user_id": user_oid
            }).sort("created_at", -1).limit(limit)
            
            orders = await orders_cursor.to_list(length=limit)
            
            return [
                UserStockOrder(
                    order_id=str(order["_id"]),
                    order_type=order.get("order_type", "unknown"),
                    side=order.get("side", "unknown"),
                    quantity=abs(order.get("stock_amount", 0)),
                    price=order.get("price"),
                    status=order.get("status", "unknown"),
                    created_at=order.get("created_at", datetime.now(timezone.utc)).isoformat(),
                    executed_at=order.get("executed_at").isoformat() if order.get("executed_at") else None
                )
                for order in orders
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user stock orders: {e}")
            return []
    
    # ========== BOT 專用方法 - 基於用戶名查詢 ==========
    
    async def _get_user_by_username(self, username: str):
        """根據用戶名查詢使用者"""
        user = await self.db[Collections.USERS].find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail=f"使用者 '{username}' 不存在")
        return user
    
    async def get_user_portfolio_by_username(self, username: str) -> UserPortfolio:
        """根據用戶名查詢使用者投資組合"""
        try:
            user = await self._get_user_by_username(username)
            return await self.get_user_portfolio(str(user["_id"]))
        except Exception as e:
            logger.error(f"Failed to get user portfolio by username: {e}")
            raise
    
    async def place_stock_order_by_username(self, username: str, request: StockOrderRequest) -> StockOrderResponse:
        """根據用戶名下股票訂單"""
        try:
            user = await self._get_user_by_username(username)
            return await self.place_stock_order(str(user["_id"]), request)
        except Exception as e:
            logger.error(f"Failed to place stock order by username: {e}")
            raise
    
    async def transfer_points_by_username(self, from_username: str, request: TransferRequest) -> TransferResponse:
        """根據用戶名轉帳點數"""
        try:
            user = await self._get_user_by_username(from_username)
            return await self.transfer_points(str(user["_id"]), request)
        except Exception as e:
            logger.error(f"Failed to transfer points by username: {e}")
            raise
    
    async def get_user_point_logs_by_username(self, username: str, limit: int = 50) -> List[UserPointLog]:
        """根據用戶名查詢使用者點數記錄"""
        try:
            user = await self._get_user_by_username(username)
            return await self.get_user_point_logs(str(user["_id"]), limit)
        except Exception as e:
            logger.error(f"Failed to get user point logs by username: {e}")
            raise
    
    async def get_user_stock_orders_by_username(self, username: str, limit: int = 50) -> List[UserStockOrder]:
        """根據用戶名查詢使用者股票訂單記錄"""
        try:
            user = await self._get_user_by_username(username)
            return await self.get_user_stock_orders(str(user["_id"]), limit)
        except Exception as e:
            logger.error(f"Failed to get user stock orders by username: {e}")
            raise
    
    async def get_user_profile_by_username(self, username: str) -> dict:
        """根據用戶名查詢使用者基本資料"""
        try:
            user = await self._get_user_by_username(username)
            return {
                "username": user.get("username"),
                "email": user.get("email"),
                "team": user.get("team"),
                "points": user.get("points", 0),
                "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
            }
        except Exception as e:
            logger.error(f"Failed to get user profile by username: {e}")
            raise
    
    # 記錄點數變化
    async def _log_point_change(self, user_id, change_type: str, amount: int, 
                              note: str, transaction_id: str = None):
        try:
            # 確保 user_id 是 ObjectId
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
                
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            current_balance = user.get("points", 0) if user else 0
            
            log_entry = {
                "user_id": user_id,
                "type": change_type,
                "amount": amount,
                "note": note,
                "balance_after": current_balance,
                "created_at": datetime.now(timezone.utc),
                "transaction_id": transaction_id
            }
            
            await self.db[Collections.POINT_LOGS].insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log point change: {e}")
    
    # 取得目前股票價格（單位：元）
    async def _get_current_stock_price(self) -> int:
        try:
            # 從最近的成交記錄取得價格
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "completed"},
                sort=[("created_at", -1)]
            )
            
            if latest_trade:
                return latest_trade.get("price", 20)
            
            # 如果沒有成交記錄，從市場配置取得
            price_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "current_price"}
            )
            
            if price_config:
                return price_config.get("price", 20)
            
            # 預設價格（20 元）
            return 20
            
        except Exception as e:
            logger.error(f"Failed to get current stock price: {e}")
            return 20
    
    # 計算使用者平均成本
    async def _calculate_user_avg_cost(self, user_oid: ObjectId) -> float:
        """計算使用者的股票平均成本"""
        try:
            # 查詢使用者所有買入訂單
            buy_orders = await self.db[Collections.STOCK_ORDERS].find({
                "user_id": user_oid,
                "side": "buy",
                "status": "filled"
            }).to_list(None)
            
            if not buy_orders:
                return 0.0
            
            total_cost = 0
            total_quantity = 0
            
            for order in buy_orders:
                quantity = order.get("filled_quantity", order.get("quantity", 0))
                price = order.get("filled_price", order.get("price", 0))
                total_cost += quantity * price
                total_quantity += quantity
            
            return total_cost / total_quantity if total_quantity > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate average cost: {e}")
            return 0.0
    
    # 檢查市場是否開放
    async def _is_market_open(self) -> bool:
        """檢查市場是否開放交易"""
        try:
            from datetime import datetime, timezone
            
            # 取得市場開放時間配置
            market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "market_hours"}
            )
            
            if not market_config or "openTime" not in market_config:
                # 如果沒有配置，預設市場開放
                return True
            
            current_timestamp = int(datetime.now(timezone.utc).timestamp())
            
            # 檢查目前是否在任何一個開放時間段內
            for slot in market_config["openTime"]:
                if slot["start"] <= current_timestamp <= slot["end"]:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            # 出錯時預設開放，避免影響交易
            return True
    
    # 執行市價單
    async def _execute_market_order(self, user_oid: ObjectId, order_doc: dict) -> StockOrderResponse:
        """執行市價單交易"""
        try:
            current_price = await self._get_current_stock_price()
            side = order_doc["side"]
            quantity = order_doc["quantity"]
            
            # 計算交易金額
            trade_amount = quantity * current_price
            
            # 更新訂單狀態
            order_doc.update({
                "status": "filled",
                "filled_price": current_price,
                "filled_quantity": quantity,
                "filled_at": datetime.now(timezone.utc)
            })
            
            # 插入已完成的訂單
            result = await self.db[Collections.STOCK_ORDERS].insert_one(order_doc)
            
            # 更新使用者資產
            if side == "buy":
                # 買入：扣除點數，增加股票
                await self.db[Collections.USERS].update_one(
                    {"_id": user_oid},
                    {"$inc": {"points": -trade_amount}}
                )
                await self.db[Collections.STOCKS].update_one(
                    {"user_id": user_oid},
                    {"$inc": {"stock_amount": quantity}},
                    upsert=True
                )
            else:
                # 賣出：增加點數，減少股票
                await self.db[Collections.USERS].update_one(
                    {"_id": user_oid},
                    {"$inc": {"points": trade_amount}}
                )
                await self.db[Collections.STOCKS].update_one(
                    {"user_id": user_oid},
                    {"$inc": {"stock_amount": -quantity}}
                )
            
            return StockOrderResponse(
                success=True,
                order_id=str(result.inserted_id),
                message=f"市價單已成交，價格: {current_price}"
            )
            
        except Exception as e:
            logger.error(f"Failed to execute market order: {e}")
            return StockOrderResponse(
                success=False,
                message="市價單執行失敗"
            )
    
    # 嘗試撮合訂單
    async def _try_match_orders(self):
        """嘗試撮合買賣訂單"""
        try:
            # 簡化實作：查找待成交的買賣單並嘗試撮合
            buy_orders = await self.db[Collections.STOCK_ORDERS].find({
                "side": "buy",
                "status": "pending",
                "order_type": "limit"
            }).sort("price", -1).to_list(None)  # 買單按價格降序
            
            sell_orders = await self.db[Collections.STOCK_ORDERS].find({
                "side": "sell",
                "status": "pending",
                "order_type": "limit"
            }).sort("price", 1).to_list(None)  # 賣單按價格升序
            
            for buy_order in buy_orders:
                for sell_order in sell_orders:
                    # 檢查是否可以撮合
                    if (buy_order["price"] >= sell_order["price"] and 
                        buy_order["quantity"] > 0 and sell_order["quantity"] > 0):
                        
                        # 計算成交數量和價格
                        trade_quantity = min(buy_order["quantity"], sell_order["quantity"])
                        trade_price = sell_order["price"]  # 以賣單價格成交
                        trade_amount = trade_quantity * trade_price
                        
                        # 更新訂單狀態
                        buy_order["quantity"] -= trade_quantity
                        sell_order["quantity"] -= trade_quantity
                        
                        if buy_order["quantity"] == 0:
                            buy_order["status"] = "filled"
                        if sell_order["quantity"] == 0:
                            sell_order["status"] = "filled"
                        
                        # 更新資料庫中的訂單
                        await self.db[Collections.STOCK_ORDERS].update_one(
                            {"_id": buy_order["_id"]},
                            {"$set": {
                                "quantity": buy_order["quantity"],
                                "status": buy_order["status"],
                                "filled_price": trade_price,
                                "filled_quantity": trade_quantity,
                                "filled_at": datetime.now(timezone.utc)
                            }}
                        )
                        
                        await self.db[Collections.STOCK_ORDERS].update_one(
                            {"_id": sell_order["_id"]},
                            {"$set": {
                                "quantity": sell_order["quantity"],
                                "status": sell_order["status"],
                                "filled_price": trade_price,
                                "filled_quantity": trade_quantity,
                                "filled_at": datetime.now(timezone.utc)
                            }}
                        )
                        
                        # 更新使用者資產
                        # 買方：扣除點數，增加股票
                        await self.db[Collections.USERS].update_one(
                            {"_id": buy_order["user_id"]},
                            {"$inc": {"points": -trade_amount}}
                        )
                        await self.db[Collections.STOCKS].update_one(
                            {"user_id": buy_order["user_id"]},
                            {"$inc": {"stock_amount": trade_quantity}},
                            upsert=True
                        )
                        
                        # 賣方：增加點數，減少股票
                        await self.db[Collections.USERS].update_one(
                            {"_id": sell_order["user_id"]},
                            {"$inc": {"points": trade_amount}}
                        )
                        await self.db[Collections.STOCKS].update_one(
                            {"user_id": sell_order["user_id"]},
                            {"$inc": {"stock_amount": -trade_quantity}}
                        )
                        
                        logger.info(f"Orders matched: {trade_quantity} shares at {trade_price}")
            
        except Exception as e:
            logger.error(f"Failed to match orders: {e}")
