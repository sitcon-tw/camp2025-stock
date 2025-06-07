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
import os

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
    
    async def _get_or_initialize_ipo_config(self, session=None) -> dict:
        """
        從資料庫獲取 IPO 設定，如果不存在則從環境變數初始化。
        環境變數: IPO_INITIAL_SHARES, IPO_INITIAL_PRICE
        """
        # 首先嘗試直接獲取
        ipo_config = await self.db[Collections.MARKET_CONFIG].find_one(
            {"type": "ipo_status"}, 
            session=session
        )
        if ipo_config:
            return ipo_config
            
        # 如果不存在，則從環境變數讀取設定並以原子操作寫入
        try:
            initial_shares = int(os.getenv("IPO_INITIAL_SHARES", "1000"))
            initial_price = int(os.getenv("IPO_INITIAL_PRICE", "20"))
        except (ValueError, TypeError):
            logger.error("無效的 IPO 環境變數，使用預設值。")
            initial_shares = 1000
            initial_price = 20
        
        ipo_doc_on_insert = {
            "type": "ipo_status",
            "initial_shares": initial_shares,
            "shares_remaining": initial_shares,
            "initial_price": initial_price,
            "updated_at": datetime.now(timezone.utc)
        }

        # 使用 upsert + $setOnInsert 原子性地創建文件，避免競爭條件
        await self.db[Collections.MARKET_CONFIG].update_one(
            {"type": "ipo_status"},
            {"$setOnInsert": ipo_doc_on_insert},
            upsert=True,
            session=session
        )

        # 現在，文件保證存在，再次獲取它
        ipo_config = await self.db[Collections.MARKET_CONFIG].find_one(
            {"type": "ipo_status"}, 
            session=session
        )
        
        logger.info(f"從環境變數初始化 IPO 狀態: {initial_shares} 股，每股 {initial_price} 點。")
        return ipo_config

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
            
            # 防護性檢查：確保價格不為 None
            if current_price is None:
                logger.warning("Current stock price is None, using default price 20")
                current_price = 20
            
            # 計算平均成本
            avg_cost = await self._calculate_user_avg_cost(user_oid)
            
            stocks = stock_holding.get("stock_amount", 0)
            stock_value = stocks * current_price
            total_value = user.get("points", 0) + stock_value
            
            return UserPortfolio(
                username=user.get("name", user.get("id", "unknown")),
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
                    # 防護性檢查：確保價格不為 None
                    if current_price is None:
                        logger.warning("Current stock price is None, using default price 20")
                        current_price = 20
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
        # 嘗試使用事務，如果失敗則使用非事務模式
        try:
            return await self._transfer_points_with_transaction(from_user_id, request)
        except Exception as e:
            error_str = str(e)
            # 檢查是否為事務不支援的錯誤
            if "Transaction numbers are only allowed on a replica set member or mongos" in error_str:
                logger.warning("MongoDB transactions not supported, falling back to non-transactional mode")
                return await self._transfer_points_without_transaction(from_user_id, request)
            else:
                logger.error(f"Transfer failed: {e}")
                return TransferResponse(
                    success=False,
                    message="轉帳失敗"
                )

    async def _transfer_points_with_transaction(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """使用事務進行轉帳（適用於 replica set 或 sharded cluster）"""
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await self._execute_transfer(from_user_id, request, session)

    async def _transfer_points_without_transaction(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """不使用事務進行轉帳（適用於 standalone MongoDB）"""
        return await self._execute_transfer(from_user_id, request, None)

    async def _execute_transfer(self, from_user_id: str, request: TransferRequest, session=None) -> TransferResponse:
        """執行轉帳邏輯"""
        # 取得發送方使用者
        from_user_oid = ObjectId(from_user_id)
        from_user = await self.db[Collections.USERS].find_one({"_id": from_user_oid}, session=session)
        if not from_user:
            return TransferResponse(
                success=False,
                message="發送方使用者不存在"
            )
        
        # 取得接收方使用者 - 改為支援name或id查詢
        to_user = await self.db[Collections.USERS].find_one({
            "$or": [
                {"name": request.to_username},
                {"id": request.to_username}
            ]
        }, session=session)
        if not to_user:
            return TransferResponse(
                success=False,
                message="接收方使用者不存在"
            )
        
        # 檢查是否為同一人
        if str(from_user["_id"]) == str(to_user["_id"]):
            return TransferResponse(
                success=False,
                message="無法轉帳給自己"
            )
        
        # 計算手續費 (10% 或至少 1 點)
        fee = max(1, int(request.amount * 0.1))
        total_deduct = request.amount + fee
        
        # 檢查餘額
        if from_user.get("points", 0) < total_deduct:
            return TransferResponse(
                success=False,
                message=f"點數不足（需要 {total_deduct} 點，含手續費 {fee}）"
            )
        
        # 執行轉帳
        transaction_id = str(uuid.uuid4())
        
        # 扣除發送方點數
        await self.db[Collections.USERS].update_one(
            {"_id": from_user_oid},
            {"$inc": {"points": -total_deduct}},
            session=session
        )
        
        # 增加接收方點數
        await self.db[Collections.USERS].update_one(
            {"_id": to_user["_id"]},
            {"$inc": {"points": request.amount}},
            session=session
        )
        
        # 記錄轉帳日誌
        await self._log_point_change(
            from_user_oid,
            "transfer_out",
            -total_deduct,
            f"轉帳給 {to_user.get('name', to_user.get('id', request.to_username))} (含手續費 {fee})",
            transaction_id,
            session=session
        )
        
        await self._log_point_change(
            to_user["_id"],
            "transfer_in",
            request.amount,
            f"收到來自 {from_user.get('name', from_user.get('id', 'unknown'))} 的轉帳",
            transaction_id,
            session=session
        )
        
        # 如果有事務則提交
        if session:
            await session.commit_transaction()
        
        return TransferResponse(
            success=True,
            message="轉帳成功",
            transaction_id=transaction_id,
            fee=fee
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
    
    async def _get_user_(self, username: str):
        """根據用戶名或ID查詢使用者"""
        user = await self.db[Collections.USERS].find_one({
            "$or": [
                {"name": username},
                {"id": username},
                {"telegram_id": username},
                {"telegram_nickname": username}
            ]
        })
        if not user:
            raise HTTPException(status_code=404, detail=f"使用者 '{username}' 不存在")
        return user
    
    async def get_user_portfolio_by_username(self, username: str) -> UserPortfolio:
        """根據用戶名查詢使用者投資組合"""
        try:
            user = await self._get_user_(username)
            return await self.get_user_portfolio(str(user["_id"]))
        except Exception as e:
            logger.error(f"Failed to get user portfolio by username: {e}")
            raise
    
    async def place_stock_order_by_username(self, username: str, request: StockOrderRequest) -> StockOrderResponse:
        """根據用戶名下股票訂單"""
        try:
            user = await self._get_user_(username)
            return await self.place_stock_order(str(user["_id"]), request)
        except Exception as e:
            logger.error(f"Failed to place stock order by username: {e}")
            raise
    
    async def transfer_points_by_username(self, from_username: str, request: TransferRequest) -> TransferResponse:
        """根據用戶名轉帳點數"""
        try:
            user = await self._get_user_(from_username)
            return await self.transfer_points(str(user["_id"]), request)
        except Exception as e:
            logger.error(f"Failed to transfer points by username: {e}")
            raise
    
    async def get_user_point_logs_by_username(self, username: str, limit: int = 50) -> List[UserPointLog]:
        """根據用戶名查詢使用者點數記錄"""
        try:
            user = await self._get_user_(username)
            return await self.get_user_point_logs(str(user["_id"]), limit)
        except Exception as e:
            logger.error(f"Failed to get user point logs by username: {e}")
            raise
    
    async def get_user_stock_orders_by_username(self, username: str, limit: int = 50) -> List[UserStockOrder]:
        """根據用戶名查詢使用者股票訂單記錄"""
        try:
            user = await self._get_user_(username)
            return await self.get_user_stock_orders(str(user["_id"]), limit)
        except Exception as e:
            logger.error(f"Failed to get user stock orders by username: {e}")
            raise
    
    async def get_user_profile_by_id(self, username: str) -> dict:
        """根據用戶名查詢使用者基本資料"""
        try:
            user = await self._get_user_(username)
            return {
                "id": user.get("id"),
                "name": user.get("name"),
                "team": user.get("team"),
                "telegram_id": user.get("telegram_id"),
                "telegram_nickname": user.get("telegram_nickname"),
                "enabled": user.get("enabled", False),
                "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
            }
        except Exception as e:
            logger.error(f"Failed to get user profile by username: {e}")
            raise
    
    # 記錄點數變化
    async def _log_point_change(self, user_id, change_type: str, amount: int, 
                              note: str, transaction_id: str = None, session=None):
        try:
            # 確保 user_id 是 ObjectId
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
                
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
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
            
            await self.db[Collections.POINT_LOGS].insert_one(log_entry, session=session)
        except Exception as e:
            logger.error(f"Failed to log point change: {e}")
    
    # 取得目前股票價格（單位：元）
    async def _get_current_stock_price(self) -> int:
        try:
            # 從最近的成交記錄取得價格
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "filled"},
                sort=[("created_at", -1)]
            )
            
            if latest_trade:
                price = latest_trade.get("price")
                # 檢查價格是否有效（不為 None 且大於 0）
                if price is not None and price > 0:
                    return price
                # 如果 price 欄位為 None，嘗試使用 filled_price
                filled_price = latest_trade.get("filled_price")
                if filled_price is not None and filled_price > 0:
                    return filled_price
            
            # 如果沒有成交記錄，從市場配置取得
            price_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "current_price"}
            )
            
            if price_config:
                config_price = price_config.get("price")
                if config_price is not None and config_price > 0:
                    return config_price
            
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
                
                if price is None or price <= 0:
                    logger.warning(f"Order {order.get('_id')} has invalid price {price} for avg cost calculation. Skipping.")
                    continue
                if quantity is None or quantity <= 0:
                    logger.warning(f"Order {order.get('_id')} has invalid quantity {quantity} for avg cost calculation. Skipping.")
                    continue
                
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
        # 嘗試使用事務，如果失敗則使用非事務模式
        try:
            return await self._execute_market_order_with_transaction(user_oid, order_doc)
        except Exception as e:
            error_str = str(e)
            # 檢查是否為事務不支援的錯誤
            if "Transaction numbers are only allowed on a replica set member or mongos" in error_str:
                logger.warning("MongoDB transactions not supported, falling back to non-transactional mode for market order")
                return await self._execute_market_order_without_transaction(user_oid, order_doc)
            else:
                logger.error(f"Market order execution failed: {e}")
                return StockOrderResponse(
                    success=False,
                    message="市價單執行失敗"
                )

    async def _execute_market_order_with_transaction(self, user_oid: ObjectId, order_doc: dict) -> StockOrderResponse:
        """使用事務執行市價單交易（適用於 replica set 或 sharded cluster）"""
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await self._execute_market_order_logic(user_oid, order_doc, session)

    async def _execute_market_order_without_transaction(self, user_oid: ObjectId, order_doc: dict) -> StockOrderResponse:
        """不使用事務執行市價單交易（適用於 standalone MongoDB）"""
        return await self._execute_market_order_logic(user_oid, order_doc, None)

    async def _execute_market_order_logic(self, user_oid: ObjectId, order_doc: dict, session=None) -> StockOrderResponse:
        """市價單交易邏輯"""
        try:
            side = order_doc["side"]
            quantity = order_doc["quantity"]
            
            # 決定價格和來源
            price = None
            is_ipo_purchase = False
            message = ""
            
            if side == "buy":
                ipo_config = await self._get_or_initialize_ipo_config(session=session)
                if ipo_config and ipo_config.get("shares_remaining", 0) >= quantity:
                    user = await self.db[Collections.USERS].find_one({"_id": user_oid}, session=session)
                    ipo_price = ipo_config["initial_price"]
                    if user.get("points", 0) >= quantity * ipo_price:
                        price = ipo_price
                        is_ipo_purchase = True
                        message = f"市價單已向系統申購成交，價格: {price}"

            if price is None:
                price = await self._get_current_stock_price()
                # 防護性檢查：確保價格不為 None
                if price is None:
                    logger.warning("Current stock price is None, using default price 20")
                    price = 20
                message = f"市價單已成交，價格: {price}"

            current_price = price
            
            # 計算交易金額
            trade_amount = quantity * current_price
            
            # 買入前再次確認點數
            if side == "buy":
                user = await self.db[Collections.USERS].find_one({"_id": user_oid}, session=session)
                if user.get("points", 0) < trade_amount:
                    return StockOrderResponse(success=False, message=f"點數不足，需要 {trade_amount} 點")

            # 更新訂單狀態
            order_doc.update({
                "status": "filled",
                "filled_price": current_price,
                "filled_quantity": quantity,
                "filled_at": datetime.now(timezone.utc)
            })
            
            # 插入已完成的訂單
            result = await self.db[Collections.STOCK_ORDERS].insert_one(order_doc, session=session)
            
            # 記錄交易記錄
            await self.db[Collections.TRADES].insert_one({
                "buy_order_id": result.inserted_id,
                "sell_order_id": None,
                "buy_user_id": user_oid,
                "sell_user_id": "SYSTEM" if is_ipo_purchase else "MARKET",
                "price": current_price,
                "quantity": quantity,
                "amount": trade_amount,
                "created_at": order_doc["filled_at"]
            }, session=session)

            # 更新 IPO 剩餘數量
            if is_ipo_purchase:
                await self.db[Collections.MARKET_CONFIG].update_one(
                    {"type": "ipo_status"},
                    {"$inc": {"shares_remaining": -quantity}},
                    session=session
                )
            
            return StockOrderResponse(
                success=True,
                order_id=str(result.inserted_id),
                message=message,
                executed_price=current_price
            )
            
        except Exception as e:
            logger.error(f"Failed to execute market order logic: {e}")
            # 如果在事務中，則中止
            if session and session.in_transaction:
                await session.abort_transaction()
            return StockOrderResponse(
                success=False,
                message="市價單執行失敗"
            )
    
    # 嘗試撮合訂單
    async def _try_match_orders(self):
        """嘗試撮合買賣訂單"""
        try:
            # 查找待成交的買賣單，並按價格-時間優先級排序
            buy_orders_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"side": "buy", "status": {"$in": ["pending", "partial"]}, "order_type": "limit"}
            ).sort([("price", -1), ("created_at", 1)])
            
            sell_orders_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"side": "sell", "status": {"$in": ["pending", "partial"]}, "order_type": "limit"}
            ).sort([("price", 1), ("created_at", 1)])

            buy_book = await buy_orders_cursor.to_list(None)
            sell_book = await sell_orders_cursor.to_list(None)

            # 將系統 IPO 作為一個虛擬賣單加入
            ipo_config = await self._get_or_initialize_ipo_config()
            if ipo_config and ipo_config.get("shares_remaining", 0) > 0:
                system_sell_order = {
                    "_id": "SYSTEM_IPO",
                    "user_id": "SYSTEM",
                    "side": "sell",
                    "quantity": ipo_config["shares_remaining"],
                    "price": ipo_config["initial_price"],
                    "status": "pending",
                    "order_type": "limit",
                    "is_system_order": True,
                    "created_at": datetime.min.replace(tzinfo=timezone.utc)
                }
                sell_book.append(system_sell_order)
                # 重新排序賣單，確保系統訂單在價格相同時排在時間較早的用戶訂單之後
                sell_book.sort(key=lambda x: (x.get('price', float('inf')), x.get('created_at', datetime.now(timezone.utc))))

            # 優化的撮合邏輯
            buy_idx, sell_idx = 0, 0
            while buy_idx < len(buy_book) and sell_idx < len(sell_book):
                buy_order = buy_book[buy_idx]
                sell_order = sell_book[sell_idx]

                # 確保訂單仍有數量
                if buy_order.get("quantity", 0) <= 0:
                    buy_idx += 1
                    continue
                if sell_order.get("quantity", 0) <= 0:
                    sell_idx += 1
                    continue

                if buy_order["price"] >= sell_order["price"]:
                    # 價格匹配，進行交易
                    await self._match_orders(buy_order, sell_order)

                    # 根據交易後的數量更新索引
                    if buy_order.get("quantity", 0) <= 0:
                        buy_idx += 1
                    if sell_order.get("quantity", 0) <= 0:
                        sell_idx += 1
                else:
                    # 買價小於賣價，由於賣單已按價格排序，後續也不可能成交，故結束
                    break
                    
        except Exception as e:
            logger.error(f"Failed to match orders: {e}")
    
    async def _match_orders(self, buy_order: dict, sell_order: dict):
        """撮合訂單 - 自動選擇事務或非事務模式"""
        # 嘗試使用事務，如果失敗則使用非事務模式
        try:
            await self._match_orders_with_transaction(buy_order, sell_order)
        except Exception as e:
            error_str = str(e)
            # 檢查是否為事務不支援的錯誤
            if "Transaction numbers are only allowed on a replica set member or mongos" in error_str:
                logger.warning("MongoDB transactions not supported, falling back to non-transactional mode for order matching")
                await self._match_orders_without_transaction(buy_order, sell_order)
            else:
                logger.error(f"Order matching failed: {e}")
                raise

    async def _match_orders_with_transaction(self, buy_order: dict, sell_order: dict):
        """使用事務執行訂單撮合（適用於 replica set 或 sharded cluster）"""
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                await self._match_orders_logic(buy_order, sell_order, session)

    async def _match_orders_without_transaction(self, buy_order: dict, sell_order: dict):
        """不使用事務執行訂單撮合（適用於 standalone MongoDB）"""
        await self._match_orders_logic(buy_order, sell_order, None)

    async def _match_orders_logic(self, buy_order: dict, sell_order: dict, session=None):
        """訂單撮合邏輯"""
        try:
            # 計算成交數量和價格
            trade_quantity = min(buy_order["quantity"], sell_order["quantity"])
            trade_price = buy_order["price"]  # 以買方出價成交
            trade_amount = trade_quantity * trade_price
            now = datetime.now(timezone.utc)
            
            is_system_sale = sell_order.get("is_system_order", False)

            # 更新訂單狀態和剩餘數量 (在記憶體中，供撮合循環使用)
            buy_order["quantity"] -= trade_quantity
            sell_order["quantity"] -= trade_quantity
            
            buy_order["status"] = "filled" if buy_order["quantity"] == 0 else "partial"
            if not is_system_sale:
                sell_order["status"] = "filled" if sell_order["quantity"] == 0 else "partial"
            
            # 更新買方訂單 (資料庫)
            await self.db[Collections.STOCK_ORDERS].update_one(
                {"_id": buy_order["_id"]},
                {
                    "$set": {"quantity": buy_order["quantity"], "status": buy_order["status"], "filled_at": now},
                    "$inc": {"filled_quantity": trade_quantity},
                    "$max": {"filled_price": trade_price} # 記錄最高的成交價
                },
                session=session
            )
            
            # 更新賣方訂單或系統庫存 (資料庫)
            if not is_system_sale:
                await self.db[Collections.STOCK_ORDERS].update_one(
                    {"_id": sell_order["_id"]},
                    {
                        "$set": {"quantity": sell_order["quantity"], "status": sell_order["status"], "filled_at": now},
                        "$inc": {"filled_quantity": trade_quantity},
                        "$max": {"filled_price": trade_price} # 記錄最高的成交價
                    },
                    session=session
                )
            else:
                # 更新系統 IPO 庫存
                await self.db[Collections.MARKET_CONFIG].update_one(
                    {"type": "ipo_status"},
                    {"$inc": {"shares_remaining": -trade_quantity}},
                    session=session
                )
            
            # 更新使用者資產
            # 買方：扣除點數，增加股票
            await self.db[Collections.USERS].update_one(
                {"_id": buy_order["user_id"]},
                {"$inc": {"points": -trade_amount}},
                session=session
            )
            await self.db[Collections.STOCKS].update_one(
                {"user_id": buy_order["user_id"]},
                {"$inc": {"stock_amount": trade_quantity}},
                upsert=True,
                session=session
            )
            
            # 賣方：增加點數，減少股票
            if not is_system_sale:
                await self.db[Collections.USERS].update_one(
                    {"_id": sell_order["user_id"]},
                    {"$inc": {"points": trade_amount}},
                    session=session
                )
                await self.db[Collections.STOCKS].update_one(
                    {"user_id": sell_order["user_id"]},
                    {"$inc": {"stock_amount": -trade_quantity}},
                    session=session
                )
            
            # 記錄交易記錄
            await self.db[Collections.TRADES].insert_one({
                "buy_order_id": buy_order["_id"],
                "sell_order_id": None if is_system_sale else sell_order["_id"],
                "buy_user_id": buy_order["user_id"],
                "sell_user_id": "SYSTEM" if is_system_sale else sell_order["user_id"],
                "price": trade_price,
                "quantity": trade_quantity,
                "amount": trade_amount,
                "created_at": now
            }, session=session)
            
            logger.info(f"Orders matched: {trade_quantity} shares at {trade_price}")
            
        except Exception as e:
            logger.error(f"Failed to match orders logic: {e}")
            if session and session.in_transaction:
                await session.abort_transaction()
            raise

    async def _match_orders_with_transaction_legacy(self, buy_order: dict, sell_order: dict):
        """使用事務執行訂單撮合 - 已棄用，保留用於參考"""
        async with await self.db.client.start_session() as session:
            try:
                async with session.start_transaction():
                    # 計算成交數量和價格
                    trade_quantity = min(buy_order["quantity"], sell_order["quantity"])
                    trade_price = sell_order["price"]  # 以賣單價格成交
                    trade_amount = trade_quantity * trade_price
                    now = datetime.now(timezone.utc)
                    
                    # 更新訂單狀態
                    buy_order["quantity"] -= trade_quantity
                    sell_order["quantity"] -= trade_quantity
                    
                    if buy_order["quantity"] == 0:
                        buy_order["status"] = "filled"
                    else:
                        buy_order["status"] = "partial"
                        
                    if sell_order["quantity"] == 0:
                        sell_order["status"] = "filled"
                    else:
                        sell_order["status"] = "partial"
                    
                    # 更新資料庫中的訂單
                    await self.db[Collections.STOCK_ORDERS].update_one(
                        {"_id": buy_order["_id"]},
                        {"$set": {
                            "quantity": buy_order["quantity"],
                            "status": buy_order["status"],
                            "filled_price": trade_price,
                            "filled_quantity": trade_quantity,
                            "filled_at": now
                        }},
                        session=session
                    )
                    
                    await self.db[Collections.STOCK_ORDERS].update_one(
                        {"_id": sell_order["_id"]},
                        {"$set": {
                            "quantity": sell_order["quantity"],
                            "status": sell_order["status"],
                            "filled_price": trade_price,
                            "filled_quantity": trade_quantity,
                            "filled_at": now
                        }},
                        session=session
                    )
                    
                    # 更新使用者資產
                    # 買方：扣除點數，增加股票
                    await self.db[Collections.USERS].update_one(
                        {"_id": buy_order["user_id"]},
                        {"$inc": {"points": -trade_amount}},
                        session=session
                    )
                    await self.db[Collections.STOCKS].update_one(
                        {"user_id": buy_order["user_id"]},
                        {"$inc": {"stock_amount": trade_quantity}},
                        upsert=True,
                        session=session
                    )
                    
                    # 賣方：增加點數，減少股票
                    await self.db[Collections.USERS].update_one(
                        {"_id": sell_order["user_id"]},
                        {"$inc": {"points": trade_amount}},
                        session=session
                    )
                    await self.db[Collections.STOCKS].update_one(
                        {"user_id": sell_order["user_id"]},
                        {"$inc": {"stock_amount": -trade_quantity}},
                        session=session
                    )
                    
                    # 記錄交易記錄
                    await self.db[Collections.TRADES].insert_one({
                        "buy_order_id": buy_order["_id"],
                        "sell_order_id": sell_order["_id"],
                        "buy_user_id": buy_order["user_id"],
                        "sell_user_id": sell_order["user_id"],
                        "price": trade_price,
                        "quantity": trade_quantity,
                        "amount": trade_amount,
                        "created_at": now
                    }, session=session)
                    
                    # 提交事務
                    await session.commit_transaction()
                    
                    logger.info(f"Orders matched: {trade_quantity} shares at {trade_price}")
                    
            except Exception as e:
                
                logger.error(f"Failed to match orders with transaction: {e}")
    
    # ========== 新增學員管理方法 ==========
    
    async def create_student(self, student_id: str, username: str) -> bool:
        """
        建立新學員
        
        Args:
            student_id: 學員ID（唯一不變的識別碼）
            username: 學員姓名
            
        Returns:
            bool: 是否建立成功
        """
        try:
            # 檢查是否已存在
            existing_student = await self.db[Collections.USERS].find_one({
                "id": student_id
            })
            if existing_student:
                logger.warning(f"Student with id {student_id} already exists")
                return False
            
            # 建立學員記錄
            student_doc = {
                "id": student_id,
                "name": username,
                "team": None,  # 等待後續更新
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await self.db[Collections.USERS].insert_one(student_doc)
            
            if result.inserted_id:
                logger.info(f"Student created successfully: {student_id} - {username}")
                return True
            else:
                logger.error(f"Failed to create student: {student_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating student {student_id}: {e}")
            return False
    
    async def update_students(self, student_data: List[dict]) -> dict:
        """
        批量更新學員資料（支援新增學員，enabled 預設 false）
        
        Args:
            student_data: 學員資料列表，包含 id, name, team
            
        Returns:
            dict: 更新結果和學生列表
        """
        try:
            updated_count = 0
            created_count = 0
            errors = []
            
            # 批量更新學員資料
            for student in student_data:
                try:
                    result = await self.db[Collections.USERS].update_one(
                        {"id": student["id"]},
                        {
                            "$set": {
                                "name": student["name"],
                                "team": student["team"],
                                "updated_at": datetime.now(timezone.utc)
                            },
                            "$setOnInsert": {
                                "enabled": False,  # 新學員預設未啟用
                                "points": 100,     # 初始點數
                                "created_at": datetime.now(timezone.utc)
                            }
                        },
                        upsert=True  # 允許建立新記錄
                    )
                    
                    if result.matched_count > 0:
                        updated_count += 1
                        logger.info(f"Updated student: {student['id']} - {student['name']} - {student['team']}")
                    elif result.upserted_id:
                        created_count += 1
                        logger.info(f"Created student: {student['id']} - {student['name']} - {student['team']}")
                        
                        # 為新學員初始化股票持有記錄
                        await self.db[Collections.STOCKS].insert_one({
                            "user_id": result.upserted_id,
                            "stock_amount": 0,
                            "updated_at": datetime.now(timezone.utc)
                        })
                        
                except Exception as e:
                    error_msg = f"Error updating student {student['id']}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # 獲取更新後的學生列表（只包含有 id 欄位的學員）
            students_cursor = self.db[Collections.USERS].find(
                {"id": {"$exists": True}},  # 只查詢有 id 欄位的文件
                {
                    "_id": 0,
                    "id": 1,
                    "name": 1,
                    "team": 1,
                    "enabled": 1
                }
            )
            
            students = []
            async for student in students_cursor:
                students.append({
                    "id": student.get("id", ""),
                    "name": student.get("name", ""),
                    "team": student.get("team", ""),
                    "enabled": student.get("enabled", False)
                })
            
            # 準備回應訊息
            message = f"成功更新 {updated_count} 位學員"
            if created_count > 0:
                message += f"，新增 {created_count} 位學員"
            if errors:
                message += f"，{len(errors)} 個錯誤"
            
            return {
                "success": True,
                "message": message,
                "students": students,
                "updated_count": updated_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error in batch update students: {e}")
            return {
                "success": False,
                "message": f"批量更新失敗: {str(e)}",
                "students": [],
                "updated_count": 0,
                "errors": [str(e)]
            }
    
    async def activate_student(self, student_id: str, telegram_id: str, telegram_nickname: str) -> dict:
        """
        啟用學員帳號（只需 ID 存在即可）
        
        Args:
            student_id: 學員 ID（驗證碼）
            
        Returns:
            dict: 啟用結果
        """
        try:
            # 查找學員是否存在
            student = await self.db[Collections.USERS].find_one({
                "id": student_id
            })
            
            if not student:
                return {
                    "ok": False,
                    "message": "noexist"
                }
            
            # 檢查是否已經啟用
            if student.get("enabled", False):
                return {
                    "ok": False,
                    "message": f"already_activated"
                }
            
            # 啟用學員帳號
            result = await self.db[Collections.USERS].update_one(
                {"id": student_id},
                {
                    "$set": {
                        "enabled": True,
                        "telegram_id": telegram_id,
                        "telegram_nickname": telegram_nickname,
                        "activated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Student activated: {student_id} - {student.get('name', 'Unknown')}")
                return {
                    "ok": True,
                    "message": f"success:{student.get('name', student_id)}"
                }
            else:
                return {
                    "ok": False,
                    "message": "error"
                }
                
        except Exception as e:
            logger.error(f"Error activating student {student_id}: {e}")
            return {
                "ok": False,
                "message": f"啟用失敗: {str(e)}"
            }
    
    async def get_student_status(self, student_id: str) -> dict:
        """
        查詢學員狀態
        
        Args:
            student_id: 學員 ID
            
        Returns:
            dict: 學員狀態資訊
        """
        try:
            # 查找學員
            student = await self.db[Collections.USERS].find_one({
                "id": student_id
            })
            
            if not student:
                return {
                    "ok": False,
                    "message": f"學員 ID '{student_id}' 不存在"
                }
            
            return {
                "ok": True,
                "message": "查詢成功",
                "id": student.get("id"),
                "name": student.get("name"),
                "enabled": student.get("enabled", False),
                "team": student.get("team")
            }
                
        except Exception as e:
            logger.error(f"Error getting student status {student_id}: {e}")
            return {
                "ok": False,
                "message": f"查詢失敗: {str(e)}"
            }
    
    async def get_student_info(self, student_id: str) -> dict:
        """
        查詢學員詳細資訊
        
        Args:
            student_id: 學員 ID
            
        Returns:
            dict: 學員詳細資訊
        """
        try:
            # 查找學員
            student = await self.db[Collections.USERS].find_one({
                "id": student_id
            })
            
            if not student:
                raise HTTPException(
                    status_code=404,
                    detail=f"學員 ID '{student_id}' 不存在"
                )
            
            return {
                "id": student.get("id"),
                "name": student.get("name"),
                "team": student.get("team"),
                "enabled": student.get("enabled", False)
            }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting student info {student_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"查詢學員資訊失敗: {str(e)}"
            )
