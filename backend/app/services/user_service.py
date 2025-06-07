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
from datetime import datetime, timezone, timedelta
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
    
    # 檢查價格是否在漲跌限制內
    async def _check_price_limit(self, order_price: float) -> bool:
        """檢查訂單價格是否在漲跌限制內（基於前日收盤價）"""
        try:
            # 取得前日收盤價作為基準價格（更符合現實股市）
            reference_price = await self._get_reference_price_for_limit()
            
            if reference_price is None:
                logger.warning("Unable to determine reference price for price limit check")
                return True  # 無法確定基準價格時允許交易
            
            # 取得動態漲跌限制（依股價級距）
            limit_percent = await self._get_dynamic_price_limit(reference_price)
            
            # 計算漲跌停價格
            max_price = reference_price * (1 + limit_percent / 100.0)
            min_price = reference_price * (1 - limit_percent / 100.0)
            
            logger.info(f"Price limit check: order_price={order_price}, reference_price={reference_price}, limit={limit_percent}%, range=[{min_price:.2f}, {max_price:.2f}]")
            
            # 檢查訂單價格是否在限制範圍內
            return min_price <= order_price <= max_price
            
        except Exception as e:
            logger.error(f"Failed to check price limit: {e}")
            # 發生錯誤時，預設允許交易
            return True

    async def _get_reference_price_for_limit(self) -> float:
        """取得漲跌限制的基準價格（前日收盤價）"""
        try:
            # 取得今日開始時間
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_end = today_start - timedelta(seconds=1)
            
            # 查找昨日最後一筆成交記錄作為前日收盤價
            yesterday_last_trade = await self.db[Collections.STOCK_ORDERS].find_one({
                "status": "filled",
                "created_at": {"$lt": today_start}
            }, sort=[("created_at", -1)])
            
            if yesterday_last_trade:
                price = yesterday_last_trade.get("price") or yesterday_last_trade.get("filled_price")
                if price and price > 0:
                    logger.info(f"Using yesterday's closing price as reference: {price}")
                    return float(price)
            
            # 如果沒有昨日交易記錄，查找今日第一筆交易作為開盤價
            today_first_trade = await self.db[Collections.STOCK_ORDERS].find_one({
                "status": "filled",
                "created_at": {"$gte": today_start}
            }, sort=[("created_at", 1)])
            
            if today_first_trade:
                price = today_first_trade.get("price") or today_first_trade.get("filled_price")
                if price and price > 0:
                    logger.info(f"Using today's opening price as reference: {price}")
                    return float(price)
            
            # 最後回到市場配置或預設價格
            price_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "current_price"}
            )
            
            if price_config and price_config.get("price", 0) > 0:
                logger.info(f"Using market config price as reference: {price_config['price']}")
                return float(price_config["price"])
            
            logger.info("Using default reference price: 20")
            return 20.0
            
        except Exception as e:
            logger.error(f"Failed to get reference price: {e}")
            return 20.0

    async def _get_dynamic_price_limit(self, stock_price: float) -> float:
        """取得動態漲跌限制百分比（依股價級距調整）"""
        try:
            # 先檢查是否有管理員設定的固定限制
            limit_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "trading_limit"}
            )
            
            if limit_config and limit_config.get("limitPercent"):
                # 如果管理員有設定固定限制，使用該設定
                fixed_limit = float(limit_config.get("limitPercent", 2000)) / 100.0
                logger.debug(f"Using admin configured limit: {fixed_limit}%")
                return fixed_limit
            
            # 否則使用動態限制（模仿現實股市的級距制度）
            if stock_price < 10:
                limit_percent = 20.0  # 低價股給予較大波動空間
            elif stock_price < 50:
                limit_percent = 15.0  # 中價股
            elif stock_price < 100:
                limit_percent = 10.0  # 高價股
            else:
                limit_percent = 8.0   # 極高價股限制更嚴格
            
            logger.debug(f"Using dynamic limit for price {stock_price}: {limit_percent}%")
            return limit_percent
            
        except Exception as e:
            logger.error(f"Failed to get dynamic price limit: {e}")
            return 10.0  # 預設 10%

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
            
            # 檢查限價單的價格是否在漲跌限制內
            order_status = "pending"
            limit_exceeded = False
            if request.order_type == "limit":
                if not await self._check_price_limit(request.price):
                    # 允許掛單但標記為等待漲跌限制解除狀態
                    order_status = "pending_limit"
                    limit_exceeded = True
                    logger.info(f"Order price {request.price} exceeds daily limit, order will be queued")
            
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
                        message=f"點數不足，需要 {required_points} 點，目前你的點數: {user.get('points', 0)}"
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
                "status": order_status,  # 使用計算出的狀態
                "created_at": datetime.now(timezone.utc),
                "stock_amount": request.quantity if request.side == "buy" else -request.quantity
            }
            
            # 如果超出漲跌限制，記錄額外資訊
            if limit_exceeded:
                order_doc["limit_exceeded"] = True
                order_doc["limit_note"] = f"Order price {request.price} exceeds daily trading limit"
            
            # 如果是市價單，立即執行
            if request.order_type == "market":
                execution_result = await self._execute_market_order(user_oid, order_doc)
                return execution_result
            else:
                # 限價單加入訂單簿
                result = await self.db[Collections.STOCK_ORDERS].insert_one(order_doc)
                order_id = str(result.inserted_id)
                
                if limit_exceeded:
                    logger.info(f"Limit order queued due to price limit: user {user_oid}, {request.side} {request.quantity} shares @ {request.price}, order_id: {order_id}")
                    return StockOrderResponse(
                        success=True,
                        order_id=order_id,
                        message=f"限價單已提交但因超出漲跌限制而暫時等待 ({request.side} {request.quantity} 股 @ {request.price} 元)"
                    )
                else:
                    logger.info(f"Limit order placed: user {user_oid}, {request.side} {request.quantity} shares @ {request.price}, order_id: {order_id}")
                
                # 只有未超出限制的訂單才進行撮合
                await self._try_match_orders()
                
                # 檢查訂單是否已被撮合
                updated_order = await self.db[Collections.STOCK_ORDERS].find_one({"_id": result.inserted_id})
                if updated_order and updated_order.get("status") == "filled":
                    executed_price = updated_order.get("filled_price", request.price)
                    executed_quantity = updated_order.get("filled_quantity", request.quantity)
                    return StockOrderResponse(
                        success=True,
                        order_id=order_id,
                        message=f"限價單已立即成交，價格: {executed_price} 元/股",
                        executed_price=executed_price,
                        executed_quantity=executed_quantity
                    )
                elif updated_order and updated_order.get("status") == "partial":
                    filled_quantity = updated_order.get("filled_quantity", 0)
                    remaining_quantity = updated_order.get("quantity", 0)
                    filled_price = updated_order.get("filled_price", request.price)
                    return StockOrderResponse(
                        success=True,
                        order_id=order_id,
                        message=f"限價單部分成交: {filled_quantity} 股 @ {filled_price} 元，剩餘 {remaining_quantity} 股等待撮合",
                        executed_price=filled_price,
                        executed_quantity=filled_quantity
                    )
                else:
                    return StockOrderResponse(
                        success=True,
                        order_id=order_id,
                        message=f"限價單已提交，等待撮合 ({request.side} {request.quantity} 股 @ {request.price} 元)"
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
        # Special handling for numeric lookups (likely Telegram user IDs)
        if username.isdigit():
            # For numeric values, first try telegram_id field specifically
            user_by_telegram = await self.db[Collections.USERS].find_one({"telegram_id": username})
            if user_by_telegram:
                logger.info(f"Found user by telegram_id '{username}': id={user_by_telegram.get('id')}, name={user_by_telegram.get('name')}, points={user_by_telegram.get('points')}, enabled={user_by_telegram.get('enabled')}")
                return user_by_telegram
        
        # Check for multiple potential matches to debug duplicates
        all_matches_cursor = self.db[Collections.USERS].find({
            "$or": [
                {"name": username},
                {"id": username},
                {"telegram_id": username},
                {"telegram_nickname": username}
            ]
        })
        all_matches = await all_matches_cursor.to_list(length=None)
        
        if not all_matches:
            raise HTTPException(status_code=404, detail="noexist")
        
        # Log all matches for debugging
        if len(all_matches) > 1:
            logger.warning(f"Multiple users found for lookup '{username}':")
            for i, match in enumerate(all_matches):
                logger.warning(f"  Match {i+1}: id={match.get('id')}, name={match.get('name')}, telegram_id={match.get('telegram_id')}, points={match.get('points')}, enabled={match.get('enabled')}")
            
            # Prioritize enabled users with stock activity (non-zero stocks or non-100 points)
            enabled_users = [u for u in all_matches if u.get('enabled', False)]
            if enabled_users:
                # Check each enabled user for stock activity
                for user_candidate in enabled_users:
                    # Check if this user has stock holdings
                    stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user_candidate["_id"]})
                    if stock_holding and stock_holding.get("stock_amount", 0) > 0:
                        logger.info(f"Selected enabled user with stock holdings: {user_candidate.get('id')}")
                        return user_candidate
                
                # If no user has stocks, prefer one with non-default points
                non_default_users = [u for u in enabled_users if u.get('points', 0) != 100]
                if non_default_users:
                    user = non_default_users[0]
                    logger.info(f"Selected enabled user with non-default points: {user.get('id')}")
                else:
                    user = enabled_users[0]
                    logger.info(f"Selected first enabled user: {user.get('id')}")
            else:
                user = all_matches[0]
                logger.info(f"No enabled users found, using first match: {user.get('id')}")
        else:
            user = all_matches[0]
        
        logger.info(f"Found user for lookup '{username}': id={user.get('id')}, name={user.get('name')}, telegram_id={user.get('telegram_id')}, points={user.get('points')}, enabled={user.get('enabled')}")
        
        return user
    
    async def debug_user_data(self, username: str) -> dict:
        """Debug method to inspect all user data and stocks"""
        try:
            # Find all matching users
            all_users_cursor = self.db[Collections.USERS].find({
                "$or": [
                    {"name": username},
                    {"id": username},
                    {"telegram_id": username},
                    {"telegram_nickname": username}
                ]
            })
            all_users = await all_users_cursor.to_list(length=None)
            
            # Find all stock records for these users
            stock_records = []
            for user in all_users:
                stock_record = await self.db[Collections.STOCKS].find_one({"user_id": user["_id"]})
                stock_records.append({
                    "user_id": str(user["_id"]),
                    "stock_record": stock_record
                })
            
            # Find recent stock orders
            recent_orders = []
            for user in all_users:
                orders_cursor = self.db[Collections.STOCK_ORDERS].find(
                    {"user_id": user["_id"]}, 
                    sort=[("created_at", -1)]
                ).limit(5)
                orders = await orders_cursor.to_list(length=5)
                recent_orders.append({
                    "user_id": str(user["_id"]),
                    "orders": [
                        {
                            "order_id": str(order["_id"]),
                            "side": order.get("side"),
                            "quantity": order.get("quantity"),
                            "price": order.get("price"),
                            "status": order.get("status"),
                            "created_at": order.get("created_at").isoformat() if order.get("created_at") else None
                        } for order in orders
                    ]
                })
            
            return {
                "lookup_value": username,
                "users_found": [
                    {
                        "id": user.get("id"),
                        "name": user.get("name"),
                        "telegram_id": user.get("telegram_id"),
                        "points": user.get("points"),
                        "enabled": user.get("enabled"),
                        "user_oid": str(user["_id"])
                    } for user in all_users
                ],
                "stock_records": stock_records,
                "recent_orders": recent_orders
            }
            
        except Exception as e:
            logger.error(f"Debug user data failed: {e}")
            return {"error": str(e)}
    
    async def get_user_portfolio_by_username(self, username: str) -> UserPortfolio:
        """根據用戶名查詢使用者投資組合"""
        try:
            user = await self._get_user_(username)
            logger.info(f"PORTFOLIO: Using user {user.get('id')} (ObjectId: {user['_id']}) for portfolio query. Points: {user.get('points')}")
            return await self.get_user_portfolio(str(user["_id"]))
        except Exception as e:
            logger.error(f"Failed to get user portfolio by username: {e}")
            raise
    
    async def place_stock_order_by_username(self, username: str, request: StockOrderRequest) -> StockOrderResponse:
        """根據用戶名下股票訂單"""
        try:
            user = await self._get_user_(username)
            logger.info(f"STOCK ORDER: Using user {user.get('id')} (ObjectId: {user['_id']}) for order placement. Points: {user.get('points')}")
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
                "points": user.get("points", 0),
                "stock_amount": user.get("stock_amount", 0),
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
        """執行市價單交易，帶重試機制"""
        max_retries = 5  # 增加重試次數
        retry_delay = 0.005  # 5ms 初始延遲
        
        for attempt in range(max_retries):
            try:
                result = await self._execute_market_order_with_transaction(user_oid, order_doc)
                if attempt > 0:
                    logger.info(f"Market order succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # 檢查是否為事務不支援的錯誤
                if "Transaction numbers are only allowed on a replica set member or mongos" in error_str:
                    logger.warning("MongoDB transactions not supported, falling back to non-transactional mode for market order")
                    return await self._execute_market_order_without_transaction(user_oid, order_doc)
                
                # 檢查是否為寫入衝突錯誤（可重試）
                elif "WriteConflict" in error_str or "TransientTransactionError" in error_str:
                    if attempt < max_retries - 1:
                        logger.info(f"Market order WriteConflict detected on attempt {attempt + 1}/{max_retries}, retrying in {retry_delay:.3f}s...")
                        import asyncio
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 1.5  # 較溫和的指數退避
                        continue
                    else:
                        logger.warning(f"Market order WriteConflict persisted after {max_retries} attempts, falling back to non-transactional mode")
                        return await self._execute_market_order_without_transaction(user_oid, order_doc)
                
                else:
                    logger.error(f"Failed to execute market order with non-retryable error: {e}")
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
                # 首先嘗試與現有限價賣單撮合
                best_sell_order = await self.db[Collections.STOCK_ORDERS].find_one(
                    {"side": "sell", "status": {"$in": ["pending", "partial"]}, "order_type": "limit"},
                    sort=[("price", 1)],  # 最低價格優先
                    session=session
                )
                
                if best_sell_order and best_sell_order.get("quantity", 0) > 0:
                    # 有賣單可以撮合，將此市價買單轉換為限價單並執行撮合
                    price = best_sell_order["price"]
                    logger.info(f"Market buy order will match with limit sell order at price {price}")
                    
                    # 創建一個臨時的買單用於撮合
                    temp_buy_order = {
                        "_id": None,  # 將在插入時分配
                        "user_id": user_oid,
                        "side": "buy",
                        "quantity": quantity,
                        "price": price,
                        "status": "pending",
                        "order_type": "market_converted",  # 標記為市價單轉換
                        "created_at": datetime.now(timezone.utc)
                    }
                    
                    # 插入訂單以獲得ID
                    temp_result = await self.db[Collections.STOCK_ORDERS].insert_one(temp_buy_order, session=session)
                    temp_buy_order["_id"] = temp_result.inserted_id
                    
                    # 執行撮合
                    await self._match_orders_logic(temp_buy_order, best_sell_order, session=session)
                    
                    message = f"市價買單已與限價賣單撮合成交，價格: {price} 元/股"
                    
                    return StockOrderResponse(
                        success=True,
                        order_id=str(temp_result.inserted_id),
                        message=message,
                        executed_price=price,
                        executed_quantity=quantity
                    )
                else:
                    # 沒有賣單，檢查是否可以從 IPO 購買
                    ipo_config = await self._get_or_initialize_ipo_config(session=session)
                    if ipo_config and ipo_config.get("shares_remaining", 0) >= quantity:
                        user = await self.db[Collections.USERS].find_one({"_id": user_oid}, session=session)
                        ipo_price = ipo_config["initial_price"]
                        if user.get("points", 0) >= quantity * ipo_price:
                            price = ipo_price
                            is_ipo_purchase = True
                            shares_remaining = ipo_config.get("shares_remaining", 0)
                            message = f"市價單已向系統IPO申購成交，價格: {price} 元/股，系統剩餘: {shares_remaining - quantity} 股"
                            logger.info(f"IPO purchase: user {user_oid} bought {quantity} shares at {price}, remaining: {shares_remaining - quantity}")
            
            elif side == "sell":
                # 賣單：嘗試與現有限價買單撮合
                best_buy_order = await self.db[Collections.STOCK_ORDERS].find_one(
                    {"side": "buy", "status": {"$in": ["pending", "partial"]}, "order_type": "limit"},
                    sort=[("price", -1)],  # 最高價格優先
                    session=session
                )
                
                if best_buy_order and best_buy_order.get("quantity", 0) > 0:
                    # 有買單可以撮合，將此市價賣單轉換為限價單並執行撮合
                    price = best_buy_order["price"]
                    logger.info(f"Market sell order will match with limit buy order at price {price}")
                    
                    # 創建一個臨時的賣單用於撮合
                    temp_sell_order = {
                        "_id": None,  # 將在插入時分配
                        "user_id": user_oid,
                        "side": "sell",
                        "quantity": quantity,
                        "price": price,
                        "status": "pending",
                        "order_type": "market_converted",  # 標記為市價單轉換
                        "created_at": datetime.now(timezone.utc)
                    }
                    
                    # 插入訂單以獲得ID
                    temp_result = await self.db[Collections.STOCK_ORDERS].insert_one(temp_sell_order, session=session)
                    temp_sell_order["_id"] = temp_result.inserted_id
                    
                    # 執行撮合
                    await self._match_orders_logic(best_buy_order, temp_sell_order, session=session)
                    
                    message = f"市價賣單已與限價買單撮合成交，價格: {price} 元/股"
                    
                    return StockOrderResponse(
                        success=True,
                        order_id=str(temp_result.inserted_id),
                        message=message,
                        executed_price=price,
                        executed_quantity=quantity
                    )

            if price is None:
                price = await self._get_current_stock_price()
                # 防護性檢查：確保價格不為 None
                if price is None:
                    logger.warning("Current stock price is None, using default price 20")
                    price = 20
                message = f"市價單已按市價成交，價格: {price} 元/股"
                logger.info(f"Market order execution: user {user_oid} {'bought' if side == 'buy' else 'sold'} {quantity} shares at market price {price}")

            current_price = price
            
            # 計算交易金額
            trade_amount = quantity * current_price
            
            # 買入前再次確認點數，賣出前確認持股
            if side == "buy":
                user = await self.db[Collections.USERS].find_one({"_id": user_oid}, session=session)
                if user.get("points", 0) < trade_amount:
                    return StockOrderResponse(success=False, message=f"點數不足，需要 {trade_amount} 點")
            elif side == "sell":
                # 賣單執行時也要確認持股
                stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user_oid}, session=session)
                current_stocks = stock_holding.get("stock_amount", 0) if stock_holding else 0
                if current_stocks < quantity:
                    return StockOrderResponse(success=False, message=f"持股不足，僅有 {current_stocks} 股")
                
                # 賣單總是按市價執行
                message = f"市價賣單已成交，價格: {price} 元/股"
                logger.info(f"Market sell order: user {user_oid} sold {quantity} shares at {price}")

            # 更新訂單狀態
            order_doc.update({
                "status": "filled",
                "price": current_price,  # 確保 price 欄位被設定為成交價
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

            # 更新用戶資產
            logger.info(f"Updating user assets: user_id={user_oid}, deducting {trade_amount} points, adding {quantity} stocks")
            
            # 扣除用戶點數
            points_update_result = await self.db[Collections.USERS].update_one(
                {"_id": user_oid},
                {"$inc": {"points": -trade_amount}},
                session=session
            )
            logger.info(f"Points update result: matched={points_update_result.matched_count}, modified={points_update_result.modified_count}")
            
            # 增加股票持有
            stocks_update_result = await self.db[Collections.STOCKS].update_one(
                {"user_id": user_oid},
                {"$inc": {"stock_amount": quantity}},
                upsert=True,
                session=session
            )
            logger.info(f"Stocks update result: matched={stocks_update_result.matched_count}, modified={stocks_update_result.modified_count}, upserted={stocks_update_result.upserted_id}")

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
            # 對於 WriteConflict 使用 DEBUG 級別，因為這會被上層重試機制處理
            error_str = str(e)
            if "WriteConflict" in error_str or "TransientTransactionError" in error_str:
                logger.debug(f"Transaction conflict in market order logic (will be retried): {e}")
            else:
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
            # 查找待成交的買賣單，排除超出漲跌限制的訂單
            buy_orders_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"side": "buy", "status": {"$in": ["pending", "partial"]}, "order_type": "limit"}
            ).sort([("price", -1), ("created_at", 1)])
            
            sell_orders_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"side": "sell", "status": {"$in": ["pending", "partial"]}, "order_type": "limit"}
            ).sort([("price", 1), ("created_at", 1)])

            buy_book = await buy_orders_cursor.to_list(None)
            sell_book = await sell_orders_cursor.to_list(None)
            
            # 安全排序函數，確保日期時間比較正常工作
            def safe_sort_key(order, reverse_price=False):
                price = order.get('price', 0 if not reverse_price else float('inf'))
                created_at = order.get('created_at')
                
                # 確保 created_at 是 timezone-aware
                if created_at is None:
                    created_at = datetime.now(timezone.utc)
                elif isinstance(created_at, datetime) and created_at.tzinfo is None:
                    # 如果是 timezone-naive，假設為 UTC
                    created_at = created_at.replace(tzinfo=timezone.utc)
                elif not isinstance(created_at, datetime):
                    created_at = datetime.now(timezone.utc)
                
                return (price, created_at)
            
            # 重新排序買單和賣單以確保日期時間比較安全
            buy_book.sort(key=lambda x: safe_sort_key(x, reverse_price=True), reverse=True)
            sell_book.sort(key=lambda x: safe_sort_key(x, reverse_price=False))

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
                logger.info(f"Added system IPO to sell book: {ipo_config['shares_remaining']} shares @ {ipo_config['initial_price']}")
                
                # 重新排序賣單包含系統IPO訂單
                sell_book.sort(key=lambda x: safe_sort_key(x, reverse_price=False))

            # 優化的撮合邏輯
            buy_idx, sell_idx = 0, 0
            matches_found = 0
            
            logger.info(f"Starting order matching: {len(buy_book)} buy orders, {len(sell_book)} sell orders")
            
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

                buy_price = buy_order.get("price", 0)
                sell_price = sell_order.get("price", float('inf'))
                
                if buy_price >= sell_price:
                    # 價格匹配，進行交易
                    is_system_sale = sell_order.get("is_system_order", False)
                    logger.info(f"Matching orders: Buy {buy_order.get('quantity')} @ {buy_price} vs Sell {sell_order.get('quantity')} @ {sell_price} {'(SYSTEM IPO)' if is_system_sale else ''}")
                    
                    await self._match_orders(buy_order, sell_order)
                    matches_found += 1

                    # 根據交易後的數量更新索引
                    if buy_order.get("quantity", 0) <= 0:
                        buy_idx += 1
                    if sell_order.get("quantity", 0) <= 0:
                        sell_idx += 1
                else:
                    # 買價小於賣價，由於賣單已按價格排序，後續也不可能成交，故結束
                    logger.debug(f"No more matches possible: buy price {buy_price} < sell price {sell_price}")
                    break
            
            if matches_found > 0:
                logger.info(f"Order matching completed: {matches_found} matches executed")
            
            # 撮合完成後，檢查是否有超出限制的訂單可以重新啟用
            await self._reactivate_limit_orders()
                    
        except Exception as e:
            logger.error(f"Failed to match orders: {e}")

    async def _reactivate_limit_orders(self):
        """檢查並重新啟用超出漲跌限制但現在可以交易的訂單"""
        try:
            # 查找所有因價格限制而等待的訂單
            pending_limit_orders = await self.db[Collections.STOCK_ORDERS].find(
                {"status": "pending_limit", "order_type": "limit"}
            ).to_list(None)
            
            reactivated_count = 0
            for order in pending_limit_orders:
                order_price = order.get("price", 0)
                
                # 檢查該訂單的價格現在是否在允許範圍內
                if await self._check_price_limit(order_price):
                    # 價格現在在範圍內，重新啟用訂單
                    await self.db[Collections.STOCK_ORDERS].update_one(
                        {"_id": order["_id"]},
                        {
                            "$set": {
                                "status": "pending",
                                "reactivated_at": datetime.now(timezone.utc)
                            },
                            "$unset": {"limit_exceeded": "", "limit_note": ""}
                        }
                    )
                    reactivated_count += 1
                    logger.info(f"Reactivated order {order['_id']} at price {order_price}")
            
            if reactivated_count > 0:
                logger.info(f"Reactivated {reactivated_count} orders due to price limit changes")
                # 重新啟用訂單後，再次嘗試撮合
                await self._try_match_orders()
                    
        except Exception as e:
            logger.error(f"Failed to reactivate limit orders: {e}")

    async def call_auction_matching(self) -> dict:
        """集合競價撮合機制（類似開盤前的集中撮合）"""
        try:
            # 查找所有待成交的限價單（包括pending和pending_limit狀態）
            buy_orders = await self.db[Collections.STOCK_ORDERS].find(
                {"side": "buy", "status": {"$in": ["pending", "pending_limit"]}, "order_type": "limit"}
            ).sort([("price", -1), ("created_at", 1)]).to_list(None)
            
            sell_orders = await self.db[Collections.STOCK_ORDERS].find(
                {"side": "sell", "status": {"$in": ["pending", "pending_limit"]}, "order_type": "limit"}
            ).sort([("price", 1), ("created_at", 1)]).to_list(None)
            
            # 統計訂單情況
            pending_buy = len([o for o in buy_orders if o.get("status") == "pending"])
            pending_sell = len([o for o in sell_orders if o.get("status") == "pending"])
            limit_buy = len([o for o in buy_orders if o.get("status") == "pending_limit"])
            limit_sell = len([o for o in sell_orders if o.get("status") == "pending_limit"])
            
            # 構建訂單詳細列表
            order_details = {
                "buy_orders": [],
                "sell_orders": []
            }
            
            # 處理買單詳情
            for order in buy_orders:
                user_info = await self.db[Collections.USERS].find_one({"_id": order.get("user_id")})
                username = user_info.get("username", "unknown") if user_info else "unknown"
                order_details["buy_orders"].append({
                    "id": str(order.get("_id")),
                    "username": username,
                    "price": order.get("price"),
                    "quantity": order.get("quantity"),
                    "status": order.get("status"),
                    "created_at": order.get("created_at").isoformat() if order.get("created_at") else None
                })
            
            # 處理賣單詳情
            for order in sell_orders:
                user_info = await self.db[Collections.USERS].find_one({"_id": order.get("user_id")})
                username = user_info.get("username", "unknown") if user_info else "unknown"
                order_details["sell_orders"].append({
                    "id": str(order.get("_id")),
                    "username": username,
                    "price": order.get("price"),
                    "quantity": order.get("quantity"),
                    "status": order.get("status"),
                    "created_at": order.get("created_at").isoformat() if order.get("created_at") else None
                })
            
            if not buy_orders and not sell_orders:
                return {
                    "success": False, 
                    "message": "no orders available for call auction",
                    "order_stats": {
                        "pending_buy": 0, "pending_sell": 0,
                        "limit_buy": 0, "limit_sell": 0
                    },
                    "order_details": order_details
                }
            elif not buy_orders:
                return {
                    "success": False, 
                    "message": f"no buy orders available (有 {pending_sell + limit_sell} 張賣單等待撮合)",
                    "order_stats": {
                        "pending_buy": pending_buy, "pending_sell": pending_sell,
                        "limit_buy": limit_buy, "limit_sell": limit_sell
                    },
                    "order_details": order_details
                }
            elif not sell_orders:
                return {
                    "success": False, 
                    "message": f"no sell orders available (有 {pending_buy + limit_buy} 張買單等待撮合)",
                    "order_stats": {
                        "pending_buy": pending_buy, "pending_sell": pending_sell,
                        "limit_buy": limit_buy, "limit_sell": limit_sell
                    },
                    "order_details": order_details
                }
            
            # 找出最佳撮合價格（最大成交量的價格）
            best_price, max_volume = await self._find_best_auction_price(buy_orders, sell_orders)
            
            if best_price is None:
                return {
                    "success": False, 
                    "message": "no matching price found",
                    "order_details": order_details
                }
            
            # 在最佳價格進行批量撮合
            matched_volume = await self._execute_call_auction(buy_orders, sell_orders, best_price)
            
            logger.info(f"Call auction completed: {matched_volume} shares matched at price {best_price}")
            
            # 發送集合競價公告到 Telegram Bot
            try:
                from app.services.admin_service import AdminService
                admin_service = AdminService(self.db)
                
                # 構建詳細的公告訊息
                announcement_message = f"管理員執行集合競價撮合完成！\n"
                announcement_message += f"📊 撮合結果：{matched_volume} 股於 {best_price} 元成交\n"
                announcement_message += f"📈 處理訂單：{len(buy_orders)} 張買單、{len(sell_orders)} 張賣單\n"
                announcement_message += f"⚖️ 訂單狀態：{pending_buy} 張待撮合買單、{pending_sell} 張待撮合賣單"
                
                if limit_buy > 0 or limit_sell > 0:
                    announcement_message += f"、{limit_buy + limit_sell} 張限制等待訂單"
                
                await admin_service._send_system_announcement(
                    title="📈 集合競價撮合完成",
                    message=announcement_message
                )
            except Exception as e:
                logger.error(f"Failed to send call auction announcement: {e}")
            
            return {
                "success": True,
                "auction_price": best_price,
                "matched_volume": matched_volume,
                "message": f"集合競價完成：{matched_volume} 股於 {best_price} 元成交",
                "order_stats": {
                    "pending_buy": pending_buy, "pending_sell": pending_sell,
                    "limit_buy": limit_buy, "limit_sell": limit_sell,
                    "total_buy_orders": len(buy_orders),
                    "total_sell_orders": len(sell_orders)
                },
                "order_details": order_details
            }
            
        except Exception as e:
            logger.error(f"Failed to execute call auction: {e}")
            return {
                "success": False, 
                "message": f"call auction failed: {str(e)}",
                "order_details": {"buy_orders": [], "sell_orders": []}
            }

    async def _find_best_auction_price(self, buy_orders: list, sell_orders: list) -> tuple:
        """找出集合競價的最佳成交價格"""
        try:
            # 取得所有可能的價格點
            all_prices = set()
            for order in buy_orders + sell_orders:
                all_prices.add(order.get("price", 0))
            
            best_price = None
            max_volume = 0
            
            # 對每個價格計算可能的成交量
            for price in sorted(all_prices):
                # 計算在此價格下的買賣量
                buy_volume = sum(order.get("quantity", 0) for order in buy_orders 
                               if order.get("price", 0) >= price)
                sell_volume = sum(order.get("quantity", 0) for order in sell_orders 
                                if order.get("price", 0) <= price)
                
                # 可成交量是買賣量的較小值
                possible_volume = min(buy_volume, sell_volume)
                
                # 找出最大成交量的價格
                if possible_volume > max_volume:
                    max_volume = possible_volume
                    best_price = price
            
            return best_price, max_volume
            
        except Exception as e:
            logger.error(f"Failed to find best auction price: {e}")
            return None, 0

    async def _execute_call_auction(self, buy_orders: list, sell_orders: list, auction_price: float) -> int:
        """在集合競價價格執行批量撮合"""
        try:
            # 篩選出可在此價格成交的訂單
            eligible_buy_orders = [order for order in buy_orders 
                                 if order.get("price", 0) >= auction_price]
            eligible_sell_orders = [order for order in sell_orders 
                                  if order.get("price", 0) <= auction_price]
            
            # 按時間優先級排序
            eligible_buy_orders.sort(key=lambda x: x.get("created_at"))
            eligible_sell_orders.sort(key=lambda x: x.get("created_at"))
            
            total_matched = 0
            buy_idx = sell_idx = 0
            
            # 進行撮合
            while (buy_idx < len(eligible_buy_orders) and 
                   sell_idx < len(eligible_sell_orders)):
                
                buy_order = eligible_buy_orders[buy_idx]
                sell_order = eligible_sell_orders[sell_idx]
                
                # 計算成交量
                trade_volume = min(
                    buy_order.get("quantity", 0),
                    sell_order.get("quantity", 0)
                )
                
                if trade_volume > 0:
                    # 執行撮合（使用集合競價價格）
                    await self._execute_auction_trade(buy_order, sell_order, auction_price, trade_volume)
                    total_matched += trade_volume
                    
                    # 更新訂單數量
                    buy_order["quantity"] -= trade_volume
                    sell_order["quantity"] -= trade_volume
                
                # 移到下一個訂單
                if buy_order.get("quantity", 0) == 0:
                    buy_idx += 1
                if sell_order.get("quantity", 0) == 0:
                    sell_idx += 1
            
            return total_matched
            
        except Exception as e:
            logger.error(f"Failed to execute call auction trades: {e}")
            return 0

    async def _execute_auction_trade(self, buy_order: dict, sell_order: dict, 
                                   auction_price: float, trade_volume: int):
        """執行集合競價的單筆交易"""
        try:
            now = datetime.now(timezone.utc)
            trade_amount = trade_volume * auction_price
            
            # 更新買方訂單
            new_buy_quantity = buy_order["quantity"] - trade_volume
            buy_status = "filled" if new_buy_quantity == 0 else "partial"
            
            await self.db[Collections.STOCK_ORDERS].update_one(
                {"_id": buy_order["_id"]},
                {
                    "$set": {
                        "quantity": new_buy_quantity,
                        "status": buy_status,
                        "filled_at": now,
                        "auction_price": auction_price
                    },
                    "$inc": {"filled_quantity": trade_volume}
                }
            )
            
            # 更新賣方訂單
            new_sell_quantity = sell_order["quantity"] - trade_volume
            sell_status = "filled" if new_sell_quantity == 0 else "partial"
            
            await self.db[Collections.STOCK_ORDERS].update_one(
                {"_id": sell_order["_id"]},
                {
                    "$set": {
                        "quantity": new_sell_quantity,
                        "status": sell_status,
                        "filled_at": now,
                        "auction_price": auction_price
                    },
                    "$inc": {"filled_quantity": trade_volume}
                }
            )
            
            # 更新用戶資產
            await self.db[Collections.USERS].update_one(
                {"_id": buy_order["user_id"]},
                {"$inc": {"points": -trade_amount}}
            )
            await self.db[Collections.STOCKS].update_one(
                {"user_id": buy_order["user_id"]},
                {"$inc": {"stock_amount": trade_volume}},
                upsert=True
            )
            
            await self.db[Collections.USERS].update_one(
                {"_id": sell_order["user_id"]},
                {"$inc": {"points": trade_amount}}
            )
            await self.db[Collections.STOCKS].update_one(
                {"user_id": sell_order["user_id"]},
                {"$inc": {"stock_amount": -trade_volume}}
            )
            
            # 記錄交易
            await self.db[Collections.TRADES].insert_one({
                "buy_order_id": buy_order["_id"],
                "sell_order_id": sell_order["_id"],
                "buy_user_id": buy_order["user_id"],
                "sell_user_id": sell_order["user_id"],
                "price": auction_price,
                "quantity": trade_volume,
                "amount": trade_amount,
                "trade_type": "call_auction",
                "created_at": now
            })
            
        except Exception as e:
            logger.error(f"Failed to execute auction trade: {e}")
    
    async def _match_orders(self, buy_order: dict, sell_order: dict):
        """撮合訂單 - 自動選擇事務或非事務模式，帶重試機制"""
        max_retries = 5  # 增加重試次數
        retry_delay = 0.005  # 5ms 初始延遲
        
        for attempt in range(max_retries):
            try:
                await self._match_orders_with_transaction(buy_order, sell_order)
                if attempt > 0:
                    logger.info(f"Order matching succeeded on attempt {attempt + 1}")
                return  # 成功則退出
                
            except Exception as e:
                error_str = str(e)
                
                # 檢查是否為事務不支援的錯誤
                if "Transaction numbers are only allowed on a replica set member or mongos" in error_str:
                    logger.warning("MongoDB transactions not supported, falling back to non-transactional mode for order matching")
                    await self._match_orders_without_transaction(buy_order, sell_order)
                    return
                
                # 檢查是否為寫入衝突錯誤（可重試）
                elif "WriteConflict" in error_str or "TransientTransactionError" in error_str:
                    if attempt < max_retries - 1:
                        logger.info(f"WriteConflict detected on attempt {attempt + 1}/{max_retries}, retrying in {retry_delay:.3f}s...")
                        import asyncio
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 1.5  # 較溫和的指數退避
                        continue
                    else:
                        logger.warning(f"WriteConflict persisted after {max_retries} attempts, falling back to non-transactional mode")
                        await self._match_orders_without_transaction(buy_order, sell_order)
                        return
                
                else:
                    logger.error(f"Order matching failed with non-retryable error: {e}")
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
                    "$set": {
                        "quantity": buy_order["quantity"], 
                        "status": buy_order["status"], 
                        "filled_at": now,
                        "price": trade_price  # 確保 price 欄位也被更新為最新成交價
                    },
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
                        "$set": {
                            "quantity": sell_order["quantity"], 
                            "status": sell_order["status"], 
                            "filled_at": now,
                            "price": trade_price  # 確保 price 欄位也被更新為最新成交價
                        },
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
            
            # 賣方：增加點數，減少股票 (只有非系統交易才需要)
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
            else:
                # 系統IPO交易，系統不需要更新點數和持股
                logger.info(f"System IPO sale: {trade_quantity} shares @ {trade_price} to user {buy_order['user_id']}")
            
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
            # 對於 WriteConflict 使用 DEBUG 級別，因為這會被上層重試機制處理
            error_str = str(e)
            if "WriteConflict" in error_str or "TransientTransactionError" in error_str:
                logger.debug(f"Transaction conflict in match orders logic (will be retried): {e}")
            else:
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
