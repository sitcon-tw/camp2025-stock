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

# 使用者服務類
class UserService:
    def __init__(self, db: AsyncIOMotorDatabase = Depends(get_database)):
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
            
            # 檢查 email 是否已存在
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
    
    # 取得目前股價
    async def _get_current_stock_price(self) -> float:
        try:
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "completed"},
                sort=[("executed_at", -1)]
            )
            return latest_trade.get("price", 20.0) if latest_trade else 20.0
        except:
            return 20.0
    
    # 計算使用者平均持股成本
    async def _calculate_user_avg_cost(self, user_id) -> float:
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
                
            buy_orders_cursor = self.db[Collections.STOCK_ORDERS].find({
                "user_id": user_id,
                "side": "buy",
                "status": "completed"
            })
            buy_orders = await buy_orders_cursor.to_list(length=None)
            
            if not buy_orders:
                return 20.0
            
            total_cost = sum(order.get("price", 20) * order.get("quantity", 0) for order in buy_orders)
            total_shares = sum(order.get("quantity", 0) for order in buy_orders)
            
            return total_cost / total_shares if total_shares > 0 else 20.0
        except:
            return 20.0
    
    # 檢查市場是否開放
    async def _is_market_open(self) -> bool:
        try:
            market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "market_hours"}
            )
            
            if not market_config or "openTime" not in market_config:
                return True  # 如果沒設定 預設開放
            
            current_timestamp = int(datetime.now(timezone.utc).timestamp())
            
            for time_slot in market_config["openTime"]:
                if time_slot["start"] <= current_timestamp <= time_slot["end"]:
                    return True
            
            return False
        except:
            return True  # 出錯時預設開放
    
    # 執行市價單
    async def _execute_market_order(self, user_id, order_doc: dict) -> StockOrderResponse:
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
                
            current_price = await self._get_current_stock_price()
            quantity = order_doc["quantity"]
            
            # 更新訂單為已執行
            order_doc.update({
                "price": current_price,
                "status": "completed",
                "executed_at": datetime.now(timezone.utc)
            })
            
            result = await self.db[Collections.STOCK_ORDERS].insert_one(order_doc)
            
            # 更新使用者資產
            if order_doc["side"] == "buy":
                points_change = -int(current_price * quantity)
                stocks_change = quantity
            else:
                points_change = int(current_price * quantity)
                stocks_change = -quantity
            
            # 更新點數
            await self.db[Collections.USERS].update_one(
                {"_id": user_id},
                {"$inc": {"points": points_change}}
            )
            
            # 更新持股
            await self.db[Collections.STOCKS].update_one(
                {"user_id": user_id},
                {
                    "$inc": {"stock_amount": stocks_change},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                },
                upsert=True
            )
            
            # 記錄點數變化
            await self._log_point_change(
                user_id,
                f"stock_{order_doc['side']}",
                points_change,
                f"股票{order_doc['side']} {quantity}股 @ {current_price}"
            )
            
            return StockOrderResponse(
                success=True,
                order_id=str(result.inserted_id),
                message="市價單執行成功",
                executed_price=current_price,
                executed_quantity=quantity
            )
            
        except Exception as e:
            logger.error(f"Failed to execute market order: {e}")
            return StockOrderResponse(
                success=False,
                message="市價單執行失敗"
            )
    
    # 嘗試撮合訂單
    async def _try_match_orders(self):
        try:
            # 簡化的撮合邏輯
            # 取得最高買單和最低賣單
            buy_order = await self.db[Collections.STOCK_ORDERS].find_one(
                {"side": "buy", "status": "pending"},
                sort=[("price", -1)]
            )
            
            sell_order = await self.db[Collections.STOCK_ORDERS].find_one(
                {"side": "sell", "status": "pending"},
                sort=[("price", 1)]
            )
            
            # 如果買價 >= 賣價，則成交
            if buy_order and sell_order and buy_order["price"] >= sell_order["price"]:
                await self._execute_matched_orders(buy_order, sell_order)
        
        except Exception as e:
            logger.error(f"Order matching failed: {e}")
    
    # 執行撮合的訂單
    async def _execute_matched_orders(self, buy_order: dict, sell_order: dict):
        # 撮合邏輯 (目前先簡化)
        pass
    
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
