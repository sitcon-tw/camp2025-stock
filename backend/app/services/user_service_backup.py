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
from app.services.cache_service import cached, get_cache_service, CacheKeys
from app.services.cache_invalidation import get_cache_invalidator
from app.core.security import create_access_token
from app.core.config_refactored import config
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from bson import ObjectId
import logging
import random
import uuid
import asyncio
import os
import requests
import time
from collections import defaultdict

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
        self.cache_service = get_cache_service()
        self.cache_invalidator = get_cache_invalidator()
        
        # 寫入衝突統計
        self.write_conflict_stats = defaultdict(int)
        self.last_conflict_log_time = time.time()
    
    def _log_write_conflict(self, operation: str, attempt: int, max_retries: int):
        """記錄寫入衝突統計"""
        self.write_conflict_stats[operation] += 1
        
        # 每 60 秒輸出一次統計報告
        current_time = time.time()
        if current_time - self.last_conflict_log_time > 60:
            total_conflicts = sum(self.write_conflict_stats.values())
            logger.warning(f"寫入衝突統計報告：總計 {total_conflicts} 次衝突")
            for op, count in self.write_conflict_stats.items():
                logger.warning(f"  {op}: {count} 次")
            self.last_conflict_log_time = current_time
            
        logger.info(f"{operation} WriteConflict 第 {attempt + 1}/{max_retries} 次嘗試失敗，將重試...")
    
    async def _get_or_initialize_ipo_config(self, session=None) -> dict:
        """
        從資料庫獲取 IPO 設定，如果不存在則從環境變數初始化。
        環境變數: CAMP_IPO_INITIAL_SHARES, CAMP_IPO_INITIAL_PRICE
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
            initial_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000"))
            initial_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20"))
        except (ValueError, TypeError):
            logger.error("無效的 IPO 環境變數，使用預設值。")
            initial_shares = 1000000
            initial_price = 20
        
        ipo_doc_on_insert = {
            "type": "ipo_status",
            "initial_shares": initial_shares,
            "shares_remaining": initial_shares,
            "initial_price": initial_price,
            "updated_at": datetime.now(timezone.utc)
        }

        # 使用 upsert + $setOnInsert 原子性地建立文件，避免競爭條件
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
                    message="使用者不存在或帳號未啟用"
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
    
    # 根據 Telegram ID 查找使用者
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        """根據 Telegram ID 查找使用者"""
        try:
            user = await self.db[Collections.USERS].find_one({"telegram_id": telegram_id})
            return user
        except Exception as e:
            logger.error(f"Failed to get user by Telegram ID {telegram_id}: {e}")
            return None
    
    # 取得使用者投資組合
    @cached(ttl=10, key_prefix="user_portfolio")
    async def get_user_portfolio(self, user_id: str) -> UserPortfolio:
        try:
            # 取得使用者資訊
            user_oid = ObjectId(user_id)
            user = await self.db[Collections.USERS].find_one({"_id": user_oid})
            if not user:
                logger.error(f"User not found for portfolio request: {user_id}")
                raise HTTPException(status_code=404, detail=f"使用者不存在：ID {user_id}")
            
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
                detail=f"取得投資組合失敗：{str(e)}"
            )
    
    # 檢查價格是否在漲跌限制內
    async def _check_price_limit(self, order_price: float) -> bool:
        """檢查訂單價格是否在漲跌限制內（基於前日收盤價）"""
        try:
            # 🚨 砸盤測試模式：暫時允許所有價格
            logger.info(f"🧪 TESTING MODE: Price limit check bypassed for price {order_price}")
            return True
            
            # === 原始限制邏輯（已註解） ===
            # # 取得前日收盤價作為基準價格（更符合現實股市）
            # reference_price = await self._get_reference_price_for_limit()
            # 
            # if reference_price is None:
            #     logger.warning("Unable to determine reference price for price limit check")
            #     return True  # 無法確定基準價格時允許交易
            # 
            # # 取得固定漲跌限制
            # limit_percent = await self._get_fixed_price_limit()
            # 
            # # 計算漲跌停價格
            # max_price = reference_price * (1 + limit_percent / 100.0)
            # min_price = reference_price * (1 - limit_percent / 100.0)
            # 
            # logger.info(f"Price limit check: order_price={order_price}, reference_price={reference_price}, limit={limit_percent}%, range=[{min_price:.2f}, {max_price:.2f}]")
            # 
            # # 檢查訂單價格是否在限制範圍內
            # return min_price <= order_price <= max_price
            
        except Exception as e:
            logger.error(f"Failed to check price limit: {e}")
            # 發生錯誤時，預設允許交易
            return True
    
    async def _get_price_limit_info(self, order_price: float) -> dict:
        """取得價格限制的詳細資訊"""
        try:
            # 🚨 砸盤測試模式：所有價格都在限制範圍內
            logger.info(f"🧪 TESTING MODE: Price limit info bypassed for price {order_price}")
            return {
                "within_limit": True,  # 強制返回 True
                "reference_price": 20.0,
                "limit_percent": 0.0,
                "min_price": 0.0,
                "max_price": 999999.0,  # 使用大數值代替 infinity
                "order_price": order_price,
                "note": "Testing mode: all prices allowed"
            }
            
            # === 原始限制邏輯（已註解） ===
            # # 取得前一日收盤價作為基準價格
            # reference_price = await self._get_reference_price_for_limit()
            # 
            # # 如果無法取得前一日收盤價，使用預設值
            # if reference_price is None or reference_price <= 0:
            #     logger.warning("Cannot determine reference price, using default price 20.0")
            #     reference_price = 20.0
            # 
            # # 取得固定漲跌限制
            # limit_percent = await self._get_fixed_price_limit()
            # 
            # # 計算漲跌停價格
            # max_price = reference_price * (1 + limit_percent / 100.0)
            # min_price = reference_price * (1 - limit_percent / 100.0)
            # 
            # # 檢查是否在限制範圍內
            # within_limit = min_price <= order_price <= max_price
            # 
            # logger.info(f"Price limit check: reference={reference_price}, limit={limit_percent}%, " +
            #            f"range={min_price:.2f}~{max_price:.2f}, order={order_price}, within={within_limit}")
            # 
            # return {
            #     "within_limit": within_limit,
            #     "reference_price": reference_price,
            #     "limit_percent": limit_percent,
            #     "min_price": min_price,
            #     "max_price": max_price,
            #     "order_price": order_price
            # }
            
        except Exception as e:
            logger.error(f"Failed to get price limit info: {e}")
            return {
                "within_limit": True,
                "reference_price": 20.0,
                "limit_percent": 0.0,
                "min_price": 0.0,
                "max_price": 999999.0,  # 使用大數值代替 infinity
                "order_price": order_price,
                "note": f"取得價格限制資訊失敗: {str(e)}"
            }

    async def _get_reference_price_for_limit(self) -> float:
        """取得漲跌限制的基準價格（前日收盤價）"""
        try:
            # 取得今日開始時間 (使用 Asia/Taipei 時區)
            from app.config import settings
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
            
            # 最後回到市場設定或預設價格
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

    async def _get_fixed_price_limit(self) -> float:
        """取得固定漲跌限制百分比"""
        try:
            # 檢查是否有管理員設定的固定限制
            limit_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "trading_limit"}
            )
            
            if limit_config and limit_config.get("limitPercent"):
                # 如果管理員有設定固定限制，使用該設定
                fixed_limit = float(limit_config.get("limitPercent", 2000)) / 100.0
                logger.debug(f"Using admin configured limit: {fixed_limit}%")
                return fixed_limit
            
            # 預設固定限制 20%
            logger.debug("Using default fixed limit: 20.0%")
            return 20.0
            
        except Exception as e:
            logger.error(f"Failed to get fixed price limit: {e}")
            return 20.0  # 預設 20%

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
            limit_info = None
            if request.order_type == "limit":
                # 取得漲跌限制資訊
                limit_info = await self._get_price_limit_info(request.price)
                if not limit_info["within_limit"]:
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
                
                # 檢查目前有多少股票正在待售（pending sell orders）
                pending_sell_pipeline = [
                    {
                        "$match": {
                            "user_id": user_oid,
                            "side": "sell",
                            "status": {"$in": ["pending", "pending_limit", "partial"]}
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total_pending": {"$sum": "$quantity"}
                        }
                    }
                ]
                
                pending_result = await self.db[Collections.STOCK_ORDERS].aggregate(pending_sell_pipeline).to_list(1)
                total_pending_sells = pending_result[0]["total_pending"] if pending_result else 0
                
                if current_stocks < 0:
                    logger.error(f"User {user_oid} has negative stock amount: {current_stocks}")
                    return StockOrderResponse(
                        success=False,
                        message=f"帳戶異常：股票持有量為負數 ({current_stocks} 股)，請聯繫管理員處理"
                    )
                
                # 檢查新訂單加上現有待售訂單是否超過持股
                total_sell_requirement = request.quantity + total_pending_sells
                if current_stocks < total_sell_requirement:
                    if total_pending_sells > 0:
                        return StockOrderResponse(
                            success=False,
                            message=f"持股不足：您已有 {total_pending_sells} 股待賣訂單，加上本次 {request.quantity} 股，總計 {total_sell_requirement} 股超過您的持股 {current_stocks} 股"
                        )
                    else:
                        return StockOrderResponse(
                            success=False,
                            message=f"持股不足，需要 {request.quantity} 股，僅有 {current_stocks} 股"
                        )
            
            # 額外的運行時驗證
            if request.quantity <= 0:
                return StockOrderResponse(
                    success=False,
                    message="訂單數量必須大於 0"
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
                # 限價單可以直接掛單等待撮合，不需要檢查即時流動性
                
                # 限價單加入訂單簿（帶重試機制）
                result = await self._insert_order_with_retry(order_doc)
                order_id = str(result.inserted_id)
                
                if limit_exceeded:
                    logger.info(f"Limit order queued due to price limit: user {user_oid}, {request.side} {request.quantity} shares @ {request.price}, order_id: {order_id}")
                    
                    # 構建詳細的限制訊息
                    limit_msg = f"限價單已提交但因超出漲跌限制而暫時等待 ({request.side} {request.quantity} 股 @ {request.price} 元)\n"
                    if limit_info:
                        limit_msg += f"📊 當日漲跌限制：{limit_info['limit_percent']:.1f}%\n"
                        limit_msg += f"📈 基準價格：{limit_info['reference_price']:.2f} 元\n"
                        limit_msg += f"📊 允許交易範圍：{limit_info['min_price']:.2f} ~ {limit_info['max_price']:.2f} 元"
                    
                    return StockOrderResponse(
                        success=True,
                        order_id=order_id,
                        message=limit_msg
                    )
                else:
                    logger.info(f"Limit order placed: user {user_oid}, {request.side} {request.quantity} shares @ {request.price}, order_id: {order_id}")
                
                # 觸發異步撮合（不阻塞響應）
                await self._trigger_async_matching("limit_order_placed")
                
                # 清除價格相關快取
                await self.cache_invalidator.invalidate_price_related_caches()
                await self.cache_invalidator.invalidate_user_portfolio_cache(user_id)
                
                # 檢查訂單狀態（一般為 pending）
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
                    # 如果有限制資訊，在成功訊息中顯示
                    success_msg = f"限價單已提交，等待撮合 ({request.side} {request.quantity} 股 @ {request.price} 元)"
                    if limit_info:
                        success_msg += f"\n📊 當日漲跌限制：{limit_info['limit_percent']:.1f}% (範圍：{limit_info['min_price']:.2f} ~ {limit_info['max_price']:.2f} 元)"
                    
                    return StockOrderResponse(
                        success=True,
                        order_id=order_id,
                        message=success_msg
                    )
                
        except Exception as e:
            logger.error(f"Failed to place stock order: {e}")
            return StockOrderResponse(
                success=False,
                message=f"下單失敗：{str(e)}"
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
                    message=f"轉帳失敗：{str(e)}"
                )

    async def _transfer_points_with_transaction(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """使用事務進行轉帳（適用於 replica set 或 sharded cluster）"""
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await self._execute_transfer(from_user_id, request, session)

    async def _transfer_points_without_transaction(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """不使用事務進行轉帳（適用於 standalone MongoDB）"""
        return await self._execute_transfer(from_user_id, request, None)

    async def _get_transfer_fee_config(self):
        """獲取轉點數手續費設定"""
        try:
            fee_config = await self.db[Collections.MARKET_CONFIG].find_one({
                "type": "transfer_fee"
            })
            
            if fee_config:
                return {
                    "fee_rate": fee_config.get("fee_rate", 10.0),  # 預設 10%
                    "min_fee": fee_config.get("min_fee", 1)       # 預設最少 1 點
                }
            else:
                # 如果沒有設定，使用預設值
                return {
                    "fee_rate": 10.0,  # 10%
                    "min_fee": 1       # 最少 1 點
                }
        except Exception as e:
            logger.error(f"Error getting transfer fee config: {e}")
            return {
                "fee_rate": 10.0,  # 預設 10%
                "min_fee": 1       # 預設最少 1 點
            }

    async def _execute_transfer(self, from_user_id: str, request: TransferRequest, session=None) -> TransferResponse:
        """執行轉帳邏輯"""
        # 取得傳送方使用者
        from_user_oid = ObjectId(from_user_id)
        from_user = await self.db[Collections.USERS].find_one({"_id": from_user_oid}, session=session)
        if not from_user:
            return TransferResponse(
                success=False,
                message="傳送方使用者不存在"
            )
        
        # 取得接收方使用者 - 改為支援name或id查詢
        to_user = await self.db[Collections.USERS].find_one({
            "$or": [
                {"name": request.to_username},
                {"id": request.to_username},
                {"telegram_id": request.to_username}
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
        
        # 計算手續費 (動態設定)
        fee_config = await self._get_transfer_fee_config()
        fee = max(fee_config["min_fee"], int(request.amount * fee_config["fee_rate"] / 100.0))
        total_deduct = request.amount + fee
        
        # 檢查餘額
        if from_user.get("points", 0) < total_deduct:
            return TransferResponse(
                success=False,
                message=f"點數不足（需要 {total_deduct} 點，含手續費 {fee}）"
            )
        
        # 執行轉帳
        transaction_id = str(uuid.uuid4())
        
        # 安全扣除傳送方點數
        deduction_result = await self._safe_deduct_points(
            user_id=from_user_oid,
            amount=total_deduct,
            operation_note=f"轉帳給 {to_user.get('name', to_user.get('id', request.to_username))}：{request.amount} 點 (含手續費 {fee} 點)",
            change_type="transfer_out",
            transaction_id=transaction_id,
            session=session
        )
        
        if not deduction_result['success']:
            return TransferResponse(
                success=False,
                message=deduction_result['message']
            )
        
        # 增加接收方點數
        await self.db[Collections.USERS].update_one(
            {"_id": to_user["_id"]},
            {"$inc": {"points": request.amount}},
            session=session
        )
        
        # 只記錄接收方的點數變化日誌（發送方的記錄已經在 _safe_deduct_points 中處理）
        await self._log_point_change(
            to_user["_id"],
            "transfer_in",
            request.amount,
            f"收到來自 {from_user.get('name', from_user.get('id', 'unknown'))} 的轉帳",
            transaction_id,
            session=session
        )
        
        # 注意：當使用 async with session.start_transaction() 時，事務會自動提交
        # 不需要手動呼叫 session.commit_transaction()
        
        # 轉帳完成後檢查點數完整性
        await self._validate_transaction_integrity(
            user_ids=[from_user_oid, to_user["_id"]],
            operation_name=f"轉帳 - {request.amount} 點 (含手續費 {fee} 點)"
        )
        
        # 清除相關使用者的投資組合快取
        await self.cache_invalidator.invalidate_user_portfolio_cache(str(from_user_oid))
        await self.cache_invalidator.invalidate_user_portfolio_cache(str(to_user["_id"]))
        
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

    # 取得所有點數記錄（給一般使用者）- 簡化版
    async def get_all_point_logs_simple(self, limit: int = None) -> List[dict]:
        """簡化版點數記錄查詢，避免複雜聚合管道timeout"""
        try:
            # 簡單查詢，只查詢基本欄位
            query = {"amount": {"$exists": True}}
            
            cursor = self.db[Collections.POINT_LOGS].find(query).sort("created_at", -1)
            
            if limit is not None and limit > 0:
                cursor = cursor.limit(limit)
            
            logs = await cursor.to_list(length=None)
            
            # 收集所有唯一的 user_id 來批量查詢使用者資訊
            user_ids = set()
            for log in logs:
                user_id = log.get("user_id")
                if user_id:
                    user_ids.add(user_id)
            
            # 建立 user_id 到使用者名稱的映射
            user_name_map = {}
            
            if user_ids:
                # 批量查詢所有相關使用者
                # 處理 ObjectId 類型的 user_id（透過 _id 查詢）
                objectid_user_ids = [uid for uid in user_ids if isinstance(uid, ObjectId)]
                if objectid_user_ids:
                    async for user in self.db[Collections.USERS].find({"_id": {"$in": objectid_user_ids}}, {"_id": 1, "name": 1}):
                        user_name_map[user["_id"]] = user.get("name", "Unknown")
                
                # 處理字串類型的 user_id（透過 id 查詢）
                string_user_ids = [uid for uid in user_ids if isinstance(uid, str)]
                if string_user_ids:
                    async for user in self.db[Collections.USERS].find({"id": {"$in": string_user_ids}}, {"id": 1, "name": 1}):
                        user_name_map[user["id"]] = user.get("name", "Unknown")
            
            # 處理記錄，加入使用者名稱
            processed_logs = []
            for log in logs:
                user_id = log.get("user_id")
                user_name = user_name_map.get(user_id, "Unknown")
                
                processed_log = {
                    "user_id": str(user_id) if user_id else "",
                    "user_name": user_name,
                    "type": log.get("type", "unknown"),
                    "amount": log.get("amount", 0),
                    "note": log.get("note", ""),
                    "created_at": log.get("created_at"),
                    "balance_after": log.get("balance_after", 0),
                    "transaction_id": log.get("transaction_id", "")
                }
                processed_logs.append(processed_log)
            
            return processed_logs
            
        except Exception as e:
            logger.error(f"Failed to get all point logs (simple): {e}")
            raise
    
    # 取得所有點數記錄（給一般使用者）
    async def get_all_point_logs(self, limit: int = None) -> List[dict]:
        try:
            # 使用聚合管道來聯接使用者資料
            pipeline = [
                # 只查詢有 amount 欄位的記錄（排除 role_change 等非點數交易記錄）
                {"$match": {"amount": {"$exists": True}}},
                # 排序：最新的記錄在前
                {"$sort": {"created_at": -1}},
            ]
            
            # 只在有限制時才加入 $limit 階段
            if limit is not None and limit > 0:
                pipeline.append({"$limit": limit})
            
            # 繼續添加其他管道階段
            pipeline.extend([
                # 先嘗試用 _id 關聯（ObjectId 類型的 user_id）
                {
                    "$lookup": {
                        "from": Collections.USERS,
                        "localField": "user_id",
                        "foreignField": "_id",
                        "as": "user_info_by_objectid"
                    }
                },
                # 再嘗試用 id 關聯（字串類型的 user_id）
                {
                    "$lookup": {
                        "from": Collections.USERS,
                        "localField": "user_id",
                        "foreignField": "id",
                        "as": "user_info_by_id"
                    }
                },
                # 合併兩個結果，優先使用 ObjectId 匹配的結果
                {
                    "$addFields": {
                        "user_info": {
                            "$cond": {
                                "if": {"$gt": [{"$size": "$user_info_by_objectid"}, 0]},
                                "then": {"$arrayElemAt": ["$user_info_by_objectid", 0]},
                                "else": {
                                    "$cond": {
                                        "if": {"$gt": [{"$size": "$user_info_by_id"}, 0]},
                                        "then": {"$arrayElemAt": ["$user_info_by_id", 0]},
                                        "else": "$$REMOVE"
                                    }
                                }
                            }
                        }
                    }
                },
                # 移除中間結果
                {
                    "$unset": ["user_info_by_objectid", "user_info_by_id"]
                },
                # 投影最終結果
                {
                    "$project": {
                        "user_id": {"$toString": "$user_id"},
                        "user_name": {
                            "$ifNull": [
                                "$user_info.name",
                                {"$ifNull": ["$user_info.username", "Unknown"]}
                            ]
                        },
                        "type": {"$ifNull": ["$type", "unknown"]},
                        "amount": {"$ifNull": ["$amount", 0]},
                        "note": {"$ifNull": ["$note", ""]},
                        "created_at": {"$ifNull": ["$created_at", "$$NOW"]},
                        "balance_after": {"$ifNull": ["$balance_after", 0]},
                        "transaction_id": {"$ifNull": ["$transaction_id", ""]}
                    }
                }
            ])
            
            cursor = self.db[Collections.POINT_LOGS].aggregate(pipeline)
            
            # 如果沒有限制，使用 to_list() 不指定 length
            if limit is None:
                logs = await cursor.to_list(length=None)
            else:
                logs = await cursor.to_list(length=limit)
            
            # 處理轉帳記錄，提取轉帳對象資訊
            processed_logs = []
            for log in logs:
                transfer_partner = None
                
                # 處理轉帳記錄
                if log.get("type") in ["transfer_out", "transfer_in"]:
                    note = log.get("note", "")
                    if log.get("type") == "transfer_out":
                        # 從 "轉帳給 Alice (含手續費 5)" 提取 "Alice"
                        import re
                        match = re.search(r"轉帳給 ([^(]+)", note)
                        if match:
                            transfer_partner = match.group(1).strip()
                    elif log.get("type") == "transfer_in":
                        # 從 "收到來自 Bob 的轉帳" 提取 "Bob"
                        import re
                        match = re.search(r"收到來自 ([^的]+) 的轉帳", note)
                        if match:
                            transfer_partner = match.group(1).strip()
                
                log["transfer_partner"] = transfer_partner
                processed_logs.append(log)
            
            logger.info(f"Successfully retrieved {len(processed_logs)} point logs (limit: {limit})")
            return processed_logs
            
        except Exception as e:
            logger.error(f"Failed to get all point logs: {e}")
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
                    user_id=str(order.get("user_id")),
                    order_type=order.get("order_type", "unknown"),
                    side=order.get("side", "unknown"),
                    quantity=self._get_display_quantity(order),
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
    
    def _get_display_quantity(self, order: dict) -> int:
        """
        取得訂單顯示數量
        
        對於已成交訂單，顯示成交數量；對於進行中訂單，顯示剩餘數量
        
        Args:
            order: 訂單文件
            
        Returns:
            顯示用的數量
        """
        status = order.get("status", "unknown")
        current_quantity = order.get("quantity", 0)
        filled_quantity = order.get("filled_quantity", 0)
        
        if status == "filled":
            # 已成交訂單：顯示成交數量
            if filled_quantity > 0:
                return filled_quantity
            elif current_quantity == 0 and filled_quantity == 0:
                # 對於舊的訂單記錄，缺少 filled_quantity 欄位
                # 查看是否有其他可用的數量欄位
                original_quantity = order.get("original_quantity")
                stock_amount = order.get("stock_amount")  # 一些舊記錄可能用這個欄位
                
                if original_quantity:
                    return original_quantity
                elif stock_amount:
                    return abs(stock_amount)  # 取絕對值，因為賣單可能是負數
                else:
                    # 如果真的找不到任何數量資訊，保留 0 並記錄問題
                    logger.warning(f"Order {order.get('_id')} has filled status but no quantity data")
                    return 0  # 保持真實性，顯示實際的 0
            else:
                # 原始數量 = 目前剩餘 + 已成交
                return current_quantity + filled_quantity
        else:
            # 進行中或部分成交訂單：顯示剩餘數量  
            return current_quantity
    
    # ========== BOT 專用方法 - 基於使用者名查詢 ==========
    
    async def _get_user_(self, username: str):
        """根據使用者名或ID查詢使用者"""
        # Special handling for numeric lookups
        if username.isdigit():
            # For numeric values, try both id field and telegram_id field
            # First try id field (internal user ID)
            user_by_id = await self.db[Collections.USERS].find_one({"id": username})
            if user_by_id:
                logger.info(f"Found user by id '{username}': id={user_by_id.get('id')}, name={user_by_id.get('name')}, points={user_by_id.get('points')}, enabled={user_by_id.get('enabled')}")
                return user_by_id
                
            # Then try telegram_id field
            user_by_telegram = await self.db[Collections.USERS].find_one({"telegram_id": int(username)})
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
            logger.error(f"User lookup failed: no matches found for username '{username}'")
            raise HTTPException(status_code=404, detail=f"使用者不存在：找不到使用者名 '{username}'")
        
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
        """根據使用者名查詢使用者投資組合"""
        try:
            user = await self._get_user_(username)
            logger.info(f"PORTFOLIO: Using user {user.get('id')} (ObjectId: {user['_id']}) for portfolio query. Points: {user.get('points')}")
            return await self.get_user_portfolio(str(user["_id"]))
        except Exception as e:
            logger.error(f"Failed to get user portfolio by username: {e}")
            raise
    
    async def place_stock_order_by_username(self, username: str, request: StockOrderRequest) -> StockOrderResponse:
        """根據使用者名下股票訂單"""
        try:
            user = await self._get_user_(username)
            logger.info(f"STOCK ORDER: Using user {user.get('id')} (ObjectId: {user['_id']}) for order placement. Points: {user.get('points')}")
            return await self.place_stock_order(str(user["_id"]), request)
        except Exception as e:
            logger.error(f"Failed to place stock order by username: {e}")
            raise
    
    async def transfer_points_by_username(self, from_username: str, request: TransferRequest) -> TransferResponse:
        """根據使用者名轉帳點數"""
        try:
            # 額外檢查：防止用不同的使用者名稱格式指向同一人的自我轉帳
            from_user = await self._get_user_(from_username)
            
            # 嘗試解析目標使用者以進行自我轉帳檢查
            try:
                to_user = await self._get_user_(request.to_username)
                
                # 檢查是否為同一人（多種標識符檢查）
                if (str(from_user["_id"]) == str(to_user["_id"]) or 
                    from_user.get("telegram_id") == to_user.get("telegram_id") or
                    (from_user.get("telegram_id") and str(from_user.get("telegram_id")) == request.to_username) or
                    (to_user.get("telegram_id") and str(to_user.get("telegram_id")) == from_username)):
                    return TransferResponse(
                        success=False,
                        message="無法轉帳給自己"
                    )
            except HTTPException:
                # 如果目標使用者不存在，讓後續邏輯處理
                pass
            
            return await self.transfer_points(str(from_user["_id"]), request)
        except Exception as e:
            logger.error(f"Failed to transfer points by username: {e}")
            raise
    
    async def get_user_point_logs_by_username(self, username: str, limit: int = 50) -> List[UserPointLog]:
        """根據使用者名查詢使用者點數記錄"""
        try:
            user = await self._get_user_(username)
            return await self.get_user_point_logs(str(user["_id"]), limit)
        except Exception as e:
            logger.error(f"Failed to get user point logs by username: {e}")
            raise
    
    async def get_user_stock_orders_by_username(self, username: str, limit: int = 50) -> List[UserStockOrder]:
        """根據使用者名查詢使用者股票訂單記錄"""
        try:
            user = await self._get_user_(username)
            return await self.get_user_stock_orders(str(user["_id"]), limit)
        except Exception as e:
            logger.error(f"Failed to get user stock orders by username: {e}")
            raise
    
    async def get_user_profile_by_id(self, username: str) -> dict:
        """根據使用者名查詢使用者基本資料"""
        try:
            user = await self._get_user_(username)
            
            # 從 stocks collection 讀取正確的股票持有量
            stock_holding = await self.db[Collections.STOCKS].find_one(
                {"user_id": user["_id"]}
            ) or {"stock_amount": 0}
            
            return {
                "id": user.get("id"),
                "name": user.get("name"),
                "team": user.get("team"),
                "telegram_id": user.get("telegram_id"),
                "telegram_nickname": user.get("telegram_nickname"),
                "enabled": user.get("enabled", False),
                "points": user.get("points", 0),
                "stock_amount": stock_holding.get("stock_amount", 0),
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
    
    # 安全的點數扣除（防止負點數）
    async def _safe_deduct_points(self, user_id: ObjectId, amount: int, 
                                operation_note: str, change_type: str = "deduction", 
                                transaction_id: str = None, session=None) -> dict:
        """
        安全地扣除使用者點數，防止產生負數餘額（含欠款檢查）
        
        Args:
            user_id: 使用者ID
            amount: 要扣除的點數
            operation_note: 操作說明
            session: 資料庫session（用於交易）
            
        Returns:
            dict: {'success': bool, 'message': str, 'balance_before': int, 'balance_after': int}
        """
        try:
            # 首先檢查使用者狀態和欠款情況
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            if not user:
                return {
                    'success': False,
                    'message': '使用者不存在',
                    'balance_before': 0,
                    'balance_after': 0
                }
            
            # 檢查帳戶狀態
            if not user.get("enabled", True):
                return {
                    'success': False,
                    'message': '帳戶未啟用',
                    'balance_before': user.get("points", 0),
                    'balance_after': user.get("points", 0)
                }
            
            if user.get("frozen", False):
                return {
                    'success': False,
                    'message': '帳戶已凍結，無法進行交易',
                    'balance_before': user.get("points", 0),
                    'balance_after': user.get("points", 0)
                }
            
            # 檢查欠款情況
            points = user.get("points", 0)
            owed_points = user.get("owed_points", 0)
            
            if owed_points > 0:
                return {
                    'success': False,
                    'message': f'帳戶有欠款 {owed_points} 點，請先償還後才能進行交易',
                    'balance_before': points,
                    'balance_after': points,
                    'owed_points': owed_points
                }
            
            # 計算實際可用餘額
            available_balance = points - owed_points
            
            if available_balance < amount:
                return {
                    'success': False,
                    'message': f'餘額不足（含欠款檢查）。需要: {amount} 點，可用: {available_balance} 點',
                    'balance_before': points,
                    'balance_after': points,
                    'available_balance': available_balance
                }
            
            # 使用 MongoDB 的條件更新確保原子性（包含凍結和欠款檢查）
            update_result = await self.db[Collections.USERS].update_one(
                {
                    "_id": user_id,
                    "points": {"$gte": amount},  # 確保扣除後不會變負數
                    "frozen": {"$ne": True},     # 確保不是凍結狀態
                    "$or": [
                        {"owed_points": {"$exists": False}},  # 沒有欠款字段
                        {"owed_points": {"$lte": 0}}          # 或者欠款為0
                    ]
                },
                {"$inc": {"points": -amount}},
                session=session
            )
            
            if update_result.modified_count == 0:
                # 扣除失敗，重新檢查原因
                user_recheck = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
                current_balance = user_recheck.get("points", 0) if user_recheck else 0
                current_owed = user_recheck.get("owed_points", 0) if user_recheck else 0
                
                return {
                    'success': False,
                    'message': f'扣除失敗。可能原因：餘額不足、帳戶凍結或有欠款。目前餘額: {current_balance} 點，欠款: {current_owed} 點',
                    'balance_before': current_balance,
                    'balance_after': current_balance
                }
            
            # 扣除成功，取得更新後的餘額
            user_after = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            balance_after = user_after.get("points", 0) if user_after else 0
            balance_before = balance_after + amount
            
            # 記錄點數變化
            await self._log_point_change(
                user_id=user_id,
                change_type=change_type,
                amount=-amount,
                note=operation_note,
                transaction_id=transaction_id,
                session=session
            )
            
            logger.info(f"Safe point deduction successful: user {user_id}, amount {amount}, balance: {balance_before} -> {balance_after}")
            
            return {
                'success': True,
                'message': f'成功扣除 {amount} 點',
                'balance_before': balance_before,
                'balance_after': balance_after
            }
            
        except Exception as e:
            logger.error(f"Failed to safely deduct points: user {user_id}, amount {amount}, error: {e}")
            return {
                'success': False,
                'message': f'點數扣除失敗: {str(e)}',
                'balance_before': 0,
                'balance_after': 0
            }
    
    # 實時檢查負點數並傳送警報
    async def _check_and_alert_negative_balance(self, user_id: ObjectId, operation_context: str = "") -> bool:
        """
        檢查指定使用者是否有負點數，如有則傳送警報
        
        Args:
            user_id: 使用者ID
            operation_context: 操作情境描述
            
        Returns:
            bool: True if balance is negative, False otherwise
        """
        try:
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            if not user:
                return False
            
            current_balance = user.get("points", 0)
            if current_balance < 0:
                username = user.get("username", user.get("name", "未知"))
                team = user.get("team", "無")
                
                # 記錄警報日誌
                logger.error(f"NEGATIVE BALANCE DETECTED: User ID: {user_id} has {current_balance} points after {operation_context}")
                
                # 傳送即時警報到 Telegram Bot
                try:
                    from app.services.admin_service import AdminService
                    admin_service = AdminService(self.db)
                    await admin_service._send_system_announcement(
                        title="🚨 負點數警報",
                        message=f"檢測到負點數！\n👤 使用者：{username}\n🏷️ 隊伍：{team}\n💰 目前點數：{current_balance}\n📍 操作情境：{operation_context}\n⏰ 時間：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                except Exception as e:
                    logger.error(f"Failed to send negative balance alert: {e}")
                
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to check negative balance: {e}")
            return False
    
    # 交易驗證包裝器
    async def _validate_transaction_integrity(self, user_ids: list, operation_name: str):
        """
        交易完成後驗證所有涉及使用者的點數完整性
        
        Args:
            user_ids: 涉及的使用者ID列表
            operation_name: 操作名稱
        """
        try:
            negative_detected = False
            for user_id in user_ids:
                if isinstance(user_id, str):
                    user_id = ObjectId(user_id)
                
                is_negative = await self._check_and_alert_negative_balance(
                    user_id=user_id,
                    operation_context=operation_name
                )
                if is_negative:
                    negative_detected = True
            
            if negative_detected:
                logger.warning(f"Transaction integrity check failed for operation: {operation_name}")
        except Exception as e:
            logger.error(f"Failed to validate transaction integrity: {e}")
    
    # 取得目前股票價格（近5筆成交均價，單位：元）
    async def _get_current_stock_price(self) -> int:
        try:
            # 從最近5筆成交記錄計算平均價格
            recent_trades_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"status": "filled"},
                sort=[("created_at", -1)]
            ).limit(5)
            
            recent_trades = await recent_trades_cursor.to_list(5)
            
            if recent_trades:
                valid_prices = []
                for trade in recent_trades:
                    price = trade.get("price")
                    if price is not None and price > 0:
                        valid_prices.append(price)
                    else:
                        # 如果 price 欄位為 None，嘗試使用 filled_price
                        filled_price = trade.get("filled_price")
                        if filled_price is not None and filled_price > 0:
                            valid_prices.append(filled_price)
                
                if valid_prices:
                    # 計算平均價格（四捨五入到整數）
                    average_price = sum(valid_prices) / len(valid_prices)
                    return round(average_price)
            
            # 如果沒有成交記錄，從市場設定取得
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
            from datetime import datetime, timezone, timedelta
            
            # 檢查預定時間
            market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "market_hours"}
            )
            
            if not market_config or "openTime" not in market_config:
                # 如果沒有設定，預設市場開放
                return True
            
            # 取得目前台北時間 (UTC+8)
            taipei_tz = timezone(timedelta(hours=8))
            current_time = datetime.now(timezone.utc).astimezone(taipei_tz)
            current_hour = current_time.hour
            current_minute = current_time.minute
            current_seconds_of_day = current_hour * 3600 + current_minute * 60 + current_time.second
            
            # 檢查目前是否在任何一個開放時間段內
            for slot in market_config["openTime"]:
                # 將儲存的時間戳轉換為當日的秒數
                start_dt = datetime.fromtimestamp(slot["start"], tz=timezone.utc).astimezone(taipei_tz)
                end_dt = datetime.fromtimestamp(slot["end"], tz=timezone.utc).astimezone(taipei_tz)
                
                start_seconds = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
                end_seconds = end_dt.hour * 3600 + end_dt.minute * 60 + end_dt.second
                
                # 處理跨日情況（例如 23:00 到 01:00）
                if start_seconds <= end_seconds:
                    # 同一天內的時間段
                    if start_seconds <= current_seconds_of_day <= end_seconds:
                        return True
                else:
                    # 跨日時間段
                    if current_seconds_of_day >= start_seconds or current_seconds_of_day <= end_seconds:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            # 出錯時預設開放，避免影響交易
            return True
    
    # 帶重試機制的訂單插入
    async def _insert_order_with_retry(self, order_doc: dict):
        """帶重試機制的訂單插入"""
        max_retries = 5
        retry_delay = 0.003
        
        for attempt in range(max_retries):
            try:
                result = await self.db[Collections.STOCK_ORDERS].insert_one(order_doc)
                if attempt > 0:
                    logger.info(f"Order insert succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # 檢查是否為寫入衝突錯誤
                if "WriteConflict" in error_str or "TransientTransactionError" in error_str:
                    if attempt < max_retries - 1:
                        self._log_write_conflict("order_insert", attempt, max_retries)
                        import asyncio
                        import random
                        jitter = random.uniform(0.8, 1.2)
                        await asyncio.sleep(retry_delay * jitter)
                        retry_delay *= 1.6
                        continue
                    else:
                        logger.error(f"Order insert WriteConflict persisted after {max_retries} attempts")
                        raise
                else:
                    logger.error(f"Order insert failed with non-retryable error: {e}")
                    raise

    # 執行市價單
    async def _execute_market_order(self, user_oid: ObjectId, order_doc: dict) -> StockOrderResponse:
        """執行市價單交易，帶增強重試機制"""
        max_retries = 8  # 增加重試次數至 8 次
        retry_delay = 0.003  # 3ms 初始延遲
        
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
                        self._log_write_conflict("market_order", attempt, max_retries)
                        import asyncio
                        import random
                        # 添加隨機延遲以避免雷群效應
                        jitter = random.uniform(0.8, 1.2)
                        await asyncio.sleep(retry_delay * jitter)
                        retry_delay *= 1.6  # 略為加強的指數退避
                        continue
                    else:
                        logger.warning(f"Market order WriteConflict persisted after {max_retries} attempts, falling back to non-transactional mode")
                        return await self._execute_market_order_without_transaction(user_oid, order_doc)
                
                else:
                    logger.error(f"Failed to execute market order with non-retryable error: {e}")
                    return StockOrderResponse(
                        success=False,
                        message=f"市價單執行失敗：{str(e)}"
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
                    
                    # 建立一個臨時的買單用於撮合
                    temp_buy_order = {
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
                    
                    # 執行撮合 - 撮合邏輯會處理所有資產轉移，包括扣點數
                    await self._match_orders_logic(temp_buy_order, best_sell_order, session=session)
                    
                    message = f"市價買單已與限價賣單撮合成交，價格: {price} 元/股"
                    
                    # 撮合完成後直接返回，不需要再次處理資產轉移
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
                    
                    # 建立一個臨時的賣單用於撮合
                    temp_sell_order = {
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
                    
                    # 執行撮合 - 撮合邏輯會處理所有資產轉移，包括股票扣除和點數增加
                    await self._match_orders_logic(best_buy_order, temp_sell_order, session=session)
                    
                    message = f"市價賣單已與限價買單撮合成交，價格: {price} 元/股"
                    
                    # 撮合完成後直接返回，不需要再次處理資產轉移
                    return StockOrderResponse(
                        success=True,
                        order_id=str(temp_result.inserted_id),
                        message=message,
                        executed_price=price,
                        executed_quantity=quantity
                    )

            if price is None:
                # 對於買單：如果沒有賣單可撮合且 IPO 也無法購買，則拒絕交易
                if side == "buy":
                    # 查詢更詳細的市場狀況以提供具體錯誤訊息
                    sell_orders_count = await self.db[Collections.STOCK_ORDERS].count_documents({
                        "side": "sell", 
                        "status": {"$in": ["pending", "partial"]},
                        "order_type": "limit",
                        "quantity": {"$gt": 0}
                    }, session=session)
                    
                    ipo_config = await self.db[Collections.MARKET_CONFIG].find_one(
                        {"type": "ipo_status"}, session=session
                    )
                    remaining_shares = ipo_config.get("shares_remaining", 0) if ipo_config else 0
                    ipo_price = ipo_config.get("initial_price", 20) if ipo_config else 20
                    required_points = quantity * ipo_price
                    
                    user = await self.db[Collections.USERS].find_one({"_id": user_oid}, session=session)
                    user_points = user.get("points", 0) if user else 0
                    
                    await session.abort_transaction()
                    logger.warning(f"Market buy order rejected: no sell orders available and IPO exhausted for user {user_oid}")
                    
                    detail_parts = []
                    if sell_orders_count == 0:
                        detail_parts.append("市場上沒有可用的賣單")
                    else:
                        detail_parts.append(f"市場上有 {sell_orders_count} 個賣單但無法撮合")
                    
                    if remaining_shares < quantity:
                        detail_parts.append(f"IPO 剩餘股數不足（需要 {quantity} 股，剩餘 {remaining_shares} 股）")
                    elif user_points < required_points:
                        detail_parts.append(f"IPO 點數不足（需要 {required_points} 點，擁有 {user_points} 點）")
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"無法執行市價買單：{', '.join(detail_parts)}"
                    )
                
                # 對於賣單：使用市場價格（因為是賣出現有股票）
                price = await self._get_current_stock_price()
                # 防護性檢查：確保價格不為 None
                if price is None:
                    logger.warning("Current stock price is None, using default price 20")
                    price = 20
                message = f"市價賣單已按市價成交，價格: {price} 元/股"
                logger.info(f"Market sell order execution: user {user_oid} sold {quantity} shares at market price {price}")

            # 計算交易金額
            trade_amount = quantity * price
            
            # 對於買單：確認點數並執行 IPO 購買或市價交易
            if side == "buy":
                user = await self.db[Collections.USERS].find_one({"_id": user_oid}, session=session)
                if user.get("points", 0) < trade_amount:
                    current_points = user.get("points", 0)
                    return StockOrderResponse(success=False, message=f"點數不足，需要 {trade_amount} 點，目前你的點數: {current_points}")
                
                # 更新訂單狀態
                order_doc.update({
                    "status": "filled",
                    "price": price,
                    "filled_price": price,
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
                    "price": price,
                    "quantity": quantity,
                    "amount": trade_amount,
                    "created_at": order_doc["filled_at"]
                }, session=session)

                # 安全扣除使用者點數
                deduction_result = await self._safe_deduct_points(
                    user_id=user_oid,
                    amount=trade_amount,
                    operation_note=f"市價買單成交：{quantity} 股 @ {price} 元",
                    change_type="stock_purchase",
                    session=session
                )
                
                if not deduction_result['success']:
                    logger.error(f"Point deduction failed: {deduction_result['message']}")
                    return StockOrderResponse(
                        success=False,
                        message=deduction_result['message']
                    )
                
                # 增加股票持有
                await self.db[Collections.STOCKS].update_one(
                    {"user_id": user_oid},
                    {"$inc": {"stock_amount": quantity}},
                    upsert=True,
                    session=session
                )

                # 更新 IPO 剩餘數量 - 使用原子操作確保不會減成負數
                if is_ipo_purchase:
                    ipo_update_result = await self.db[Collections.MARKET_CONFIG].update_one(
                        {
                            "type": "ipo_status",
                            "shares_remaining": {"$gte": quantity}  # 確保有足夠股數
                        },
                        {"$inc": {"shares_remaining": -quantity}},
                        session=session
                    )
                    
                    # 驗證 IPO 更新是否成功
                    if ipo_update_result.modified_count == 0:
                        # 查詢實際剩餘股數以提供更詳細的錯誤訊息
                        current_ipo = await self.db[Collections.MARKET_CONFIG].find_one(
                            {"type": "ipo_status"}, session=session
                        )
                        remaining_shares = current_ipo.get("shares_remaining", 0) if current_ipo else 0
                        logger.error(f"Failed to update IPO stock in market order: insufficient shares for quantity {quantity}, remaining: {remaining_shares}")
                        if session and session.in_transaction:
                            await session.abort_transaction()
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"IPO 股數不足，無法完成交易。需要 {quantity} 股，剩餘 {remaining_shares} 股"
                        )
                    
                    logger.info(f"✅ Market order IPO stock updated: reduced by {quantity} shares")
                
            elif side == "sell":
                # 賣單執行時確認持股
                stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user_oid}, session=session)
                current_stocks = stock_holding.get("stock_amount", 0) if stock_holding else 0
                if current_stocks < quantity:
                    if current_stocks < 0:
                        logger.error(f"User {user_oid} has negative stock amount: {current_stocks}")
                        return StockOrderResponse(
                            success=False, 
                            message=f"帳戶異常：股票持有量為負數 ({current_stocks} 股)，請聯繫管理員處理"
                        )
                    else:
                        return StockOrderResponse(
                            success=False, 
                            message=f"持股不足，需要 {quantity} 股，僅有 {current_stocks} 股"
                        )
                
                # 更新訂單狀態
                order_doc.update({
                    "status": "filled",
                    "price": price,
                    "filled_price": price,
                    "filled_quantity": quantity,
                    "filled_at": datetime.now(timezone.utc)
                })
                
                # 插入已完成的訂單
                result = await self.db[Collections.STOCK_ORDERS].insert_one(order_doc, session=session)
                
                # 記錄交易記錄
                await self.db[Collections.TRADES].insert_one({
                    "buy_order_id": None,
                    "sell_order_id": result.inserted_id,
                    "buy_user_id": "MARKET",
                    "sell_user_id": user_oid,
                    "price": price,
                    "quantity": quantity,
                    "amount": trade_amount,
                    "created_at": order_doc["filled_at"]
                }, session=session)

                # 增加使用者點數
                await self.db[Collections.USERS].update_one(
                    {"_id": user_oid},
                    {"$inc": {"points": trade_amount}},
                    session=session
                )
                
                # 使用原子操作確保股票數量不會變成負數
                stock_update_result = await self.db[Collections.STOCKS].update_one(
                    {
                        "user_id": user_oid,
                        "stock_amount": {"$gte": quantity}  # 確保有足夠股票
                    },
                    {"$inc": {"stock_amount": -quantity}},
                    session=session
                )
                
                # 驗證股票更新是否成功
                if stock_update_result.modified_count == 0:
                    # 查詢實際持股數量以提供詳細錯誤訊息
                    current_holding = await self.db[Collections.STOCKS].find_one({"user_id": user_oid}, session=session)
                    current_stocks = current_holding.get("stock_amount", 0) if current_holding else 0
                    logger.error(f"Market sell order stock deduction failed for user {user_oid}: insufficient shares, quantity {quantity}, current: {current_stocks}")
                    return StockOrderResponse(
                        success=False,
                        message=f"股票不足，需要賣出 {quantity} 股，實際持有 {current_stocks} 股"
                    )
                
                logger.info(f"Market sell order: user {user_oid} sold {quantity} shares at {price}")

            # 交易完成後檢查點數完整性
            await self._validate_transaction_integrity(
                user_ids=[user_oid],
                operation_name=f"市價單執行 - {quantity} 股 @ {price} 元"
            )
            
            return StockOrderResponse(
                success=True,
                order_id=str(result.inserted_id),
                message=message,
                executed_price=price
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
                message=f"市價單執行失敗：{str(e)}"
            )
    
    # 嘗試撮合訂單
    async def _try_match_orders(self):
        """嘗試撮合買賣訂單"""
        try:
            # 查找待成交的買賣單，包含等待限價的訂單
            # 修復：也包含 "pending_limit" 狀態，在撮合時動態檢查價格限制
            buy_orders_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"side": "buy", "status": {"$in": ["pending", "partial", "pending_limit"]}, "order_type": {"$in": ["limit", "market_converted"]}}
            ).sort([("price", -1), ("created_at", 1)])
            
            sell_orders_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"side": "sell", "status": {"$in": ["pending", "partial", "pending_limit"]}, "order_type": {"$in": ["limit", "market_converted"]}}
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

            # 將系統 IPO 作為一個虛擬賣單加入（僅當確實有剩餘股數時）
            ipo_config = await self._get_or_initialize_ipo_config()
            shares_remaining = ipo_config.get("shares_remaining", 0) if ipo_config else 0
            
            logger.info(f"IPO status check: config exists={ipo_config is not None}, shares_remaining={shares_remaining}")
            
            if ipo_config and shares_remaining > 0:
                system_sell_order = {
                    "_id": "SYSTEM_IPO",
                    "user_id": "SYSTEM",
                    "side": "sell",
                    "quantity": shares_remaining,
                    "price": ipo_config["initial_price"],
                    "status": "pending",
                    "order_type": "limit",
                    "is_system_order": True,
                    "created_at": datetime.min.replace(tzinfo=timezone.utc)
                }
                sell_book.append(system_sell_order)
                logger.info(f"✅ Added system IPO to sell book: {shares_remaining} shares @ {ipo_config['initial_price']}")
                
                # 重新排序賣單包含系統IPO訂單
                sell_book.sort(key=lambda x: safe_sort_key(x, reverse_price=False))
            else:
                logger.info(f"❌ IPO not added to sell book: no shares remaining (remaining: {shares_remaining})")

            # 優化的撮合邏輯
            buy_idx, sell_idx = 0, 0
            matches_found = 0
            
            logger.info(f"🔍Starting order matching: {len(buy_book)} buy orders, {len(sell_book)} sell orders")
            
            while buy_idx < len(buy_book) and sell_idx < len(sell_book):
                buy_order = buy_book[buy_idx]
                sell_order = sell_book[sell_idx]

                # 確保訂單仍有數量且有效
                buy_quantity = buy_order.get("quantity", 0)
                sell_quantity = sell_order.get("quantity", 0)
                
                if buy_quantity <= 0:
                    logger.warning(f"Skipping buy order with invalid quantity: {buy_quantity}, order_id: {buy_order.get('_id')}")
                    buy_idx += 1
                    continue
                if sell_quantity <= 0:
                    logger.warning(f"Skipping sell order with invalid quantity: {sell_quantity}, order_id: {sell_order.get('_id')}")
                    sell_idx += 1
                    continue

                buy_price = buy_order.get("price", 0)
                sell_price = sell_order.get("price", float('inf'))
                
                # 檢查訂單是否受價格限制影響
                buy_status = buy_order.get("status")
                sell_status = sell_order.get("status")
                
                # 如果訂單狀態為 "pending_limit"，需要重新檢查價格限制
                if buy_status == "pending_limit":
                    if await self._check_price_limit(buy_price):
                        # 價格現在允許了，更新狀態為 pending
                        await self.db[Collections.STOCK_ORDERS].update_one(
                            {"_id": buy_order["_id"]},
                            {"$set": {"status": "pending"}}
                        )
                        buy_order["status"] = "pending"  # 更新本地副本
                        logger.info(f"Buy order {buy_order['_id']} price limit lifted, status changed from pending_limit to pending")
                    else:
                        # 價格仍然受限，跳過這個買單
                        buy_idx += 1
                        continue
                
                if sell_status == "pending_limit":
                    if await self._check_price_limit(sell_price):
                        # 價格現在允許了，更新狀態為 pending
                        await self.db[Collections.STOCK_ORDERS].update_one(
                            {"_id": sell_order["_id"]},
                            {"$set": {"status": "pending"}}
                        )
                        sell_order["status"] = "pending"  # 更新本地副本
                        logger.info(f"Sell order {sell_order['_id']} price limit lifted, status changed from pending_limit to pending")
                    else:
                        # 價格仍然受限，跳過這個賣單
                        sell_idx += 1
                        continue
                
                if buy_price >= sell_price:
                    # 檢查是否為自我交易
                    if buy_order.get("user_id") == sell_order.get("user_id"):
                        logger.warning(f"Prevented self-trading for user {buy_order.get('user_id')}")
                        # 跳過賣單，避免無限循環
                        sell_idx += 1
                        continue
                    
                    # 價格符合，進行交易
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
    
    async def _trigger_async_matching(self, reason: str = "manual_trigger"):
        """觸發異步撮合（不阻塞目前請求）"""
        try:
            from app.services.matching_scheduler import get_matching_scheduler
            
            scheduler = get_matching_scheduler()
            if scheduler:
                await scheduler.trigger_matching_async(reason)
                logger.debug(f"Triggered async matching: {reason}")
            else:
                logger.warning("Matching scheduler not available, falling back to sync matching")
                # 後備方案：同步撮合（但限制執行時間）
                try:
                    await asyncio.wait_for(self._try_match_orders(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Sync matching timeout, order will be matched later")
                    
        except Exception as e:
            logger.error(f"Failed to trigger async matching: {e}")

    async def _determine_fair_trade_price(self, buy_order: dict, sell_order: dict) -> float:
        """決定公平的成交價格"""
        buy_price = buy_order.get("price", 0)
        sell_price = sell_order.get("price", float('inf'))
        buy_order_type = buy_order.get("order_type", "limit")
        sell_order_type = sell_order.get("order_type", "limit")
        is_system_sale = sell_order.get("is_system_order", False)
        
        try:
            # 如果是系統IPO訂單，使用IPO價格
            if is_system_sale:
                logger.info(f"System IPO trade: using IPO price {sell_price}")
                return sell_price
            
            # 市價單與限價單的撮合
            if buy_order_type == "market" or buy_order_type == "market_converted":
                if sell_order_type == "limit":
                    # 市價買單 vs 限價賣單：使用賣方限價
                    logger.info(f"Market buy vs limit sell: using sell price {sell_price}")
                    return sell_price
                else:
                    # 市價買單 vs 市價賣單：使用當前市場價格
                    current_price = await self._get_current_stock_price()
                    logger.info(f"Market buy vs market sell: using current price {current_price}")
                    return current_price
            
            elif sell_order_type == "market" or sell_order_type == "market_converted":
                if buy_order_type == "limit":
                    # 限價買單 vs 市價賣單：使用買方限價
                    logger.info(f"Limit buy vs market sell: using buy price {buy_price}")
                    return buy_price
                else:
                    # 市價賣單 vs 市價買單：使用當前市場價格
                    current_price = await self._get_current_stock_price()
                    logger.info(f"Market sell vs market buy: using current price {current_price}")
                    return current_price
            
            # 限價單與限價單的撮合
            elif buy_order_type == "limit" and sell_order_type == "limit":
                # 檢查哪個訂單先提交（時間優先）
                buy_time = buy_order.get("created_at")
                sell_time = sell_order.get("created_at")
                
                if buy_time and sell_time:
                    if buy_time < sell_time:
                        # 買單先提交，使用買方價格
                        logger.info(f"Limit vs limit (buy first): using buy price {buy_price}")
                        return buy_price
                    else:
                        # 賣單先提交，使用賣方價格
                        logger.info(f"Limit vs limit (sell first): using sell price {sell_price}")
                        return sell_price
                else:
                    # 無法確定時間，使用賣方價格（對賣方有利）
                    logger.info(f"Limit vs limit (time unknown): using sell price {sell_price}")
                    return sell_price
            
            # 預設情況：使用中間價格
            else:
                if buy_price > 0 and sell_price < float('inf'):
                    mid_price = (buy_price + sell_price) / 2
                    logger.info(f"Default case: using mid price {mid_price} (buy: {buy_price}, sell: {sell_price})")
                    return mid_price
                else:
                    # 如果價格異常，使用當前市場價格
                    current_price = await self._get_current_stock_price()
                    logger.info(f"Price anomaly: using current price {current_price}")
                    return current_price
                    
        except Exception as e:
            logger.error(f"Error determining fair trade price: {e}")
            # 發生錯誤時回退到賣方價格
            return sell_price if sell_price < float('inf') else buy_price


    
    async def _match_orders(self, buy_order: dict, sell_order: dict):
        """撮合訂單 - 自動選擇事務或非事務模式，帶增強重試機制"""
        max_retries = 8  # 增加重試次數至 8 次
        retry_delay = 0.003  # 3ms 初始延遲
        
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
                        self._log_write_conflict("order_matching", attempt, max_retries)
                        import asyncio
                        import random
                        # 添加隨機延遲以避免雷群效應
                        jitter = random.uniform(0.8, 1.2)
                        await asyncio.sleep(retry_delay * jitter)
                        retry_delay *= 1.6  # 略為加強的指數退避
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
            # 注意：自我交易檢查已在主循環中處理
            
            # 計算成交數量和價格
            trade_quantity = min(buy_order["quantity"], sell_order["quantity"])
            
            # 更公平的價格決定機制
            trade_price = await self._determine_fair_trade_price(buy_order, sell_order)
            trade_amount = trade_quantity * trade_price
            now = datetime.now(timezone.utc)
            
            is_system_sale = sell_order.get("is_system_order", False)
            
            # 記錄詳細的撮合信息
            logger.info(f"💰 Trade executed: {trade_quantity} shares @ {trade_price} = {trade_amount} points")
            logger.info(f"📊 Order details: Buy({buy_order.get('order_type', 'unknown')} @ {buy_order.get('price', 0)}) vs Sell({sell_order.get('order_type', 'unknown')} @ {sell_order.get('price', 0)}) {'[SYSTEM IPO]' if is_system_sale else ''}")
            logger.info(f"👥 Users: {buy_order.get('user_id', 'unknown')} (buyer) vs {sell_order.get('user_id', 'unknown')} (seller)")

            # 使用原子操作更新買方訂單 (資料庫)
            buy_update_result = await self.db[Collections.STOCK_ORDERS].update_one(
                {"_id": buy_order["_id"], "quantity": {"$gte": trade_quantity}},
                {
                    "$inc": {"quantity": -trade_quantity, "filled_quantity": trade_quantity},
                    "$set": {
                        "filled_at": now,
                        "price": trade_price  # 確保 price 欄位也被更新為最新成交價
                    },
                    "$max": {"filled_price": trade_price} # 記錄最高的成交價
                },
                session=session
            )
            
            # 驗證買方訂單更新是否成功
            if buy_update_result.modified_count == 0:
                # 買方訂單更新失敗，可能是並發問題或數量不足
                current_buy_order = await self.db[Collections.STOCK_ORDERS].find_one({"_id": buy_order["_id"]}, session=session)
                current_quantity = current_buy_order.get("quantity", 0) if current_buy_order else 0
                buy_user_id = buy_order["user_id"]
                logger.error(f"Buy order atomic update failed for user ID: {buy_user_id}: needed {trade_quantity}, current quantity: {current_quantity}")
                raise Exception(f"訂單撮合失敗 - 買方訂單數量不足：需要 {trade_quantity} 股，剩餘 {current_quantity} 股")
            
            # 更新賣方訂單或系統庫存 (資料庫)
            if not is_system_sale:
                sell_update_result = await self.db[Collections.STOCK_ORDERS].update_one(
                    {"_id": sell_order["_id"], "quantity": {"$gte": trade_quantity}},
                    {
                        "$inc": {"quantity": -trade_quantity, "filled_quantity": trade_quantity},
                        "$set": {
                            "filled_at": now,
                            "price": trade_price  # 確保 price 欄位也被更新為最新成交價
                        },
                        "$max": {"filled_price": trade_price} # 記錄最高的成交價
                    },
                    session=session
                )
                
                # 驗證賣方訂單更新是否成功
                if sell_update_result.modified_count == 0:
                    current_sell_order = await self.db[Collections.STOCK_ORDERS].find_one({"_id": sell_order["_id"]}, session=session)
                    current_quantity = current_sell_order.get("quantity", 0) if current_sell_order else 0
                    sell_user_id = sell_order["user_id"]
                    logger.error(f"Sell order atomic update failed for user ID: {sell_user_id}: needed {trade_quantity}, current quantity: {current_quantity}")
                    raise Exception(f"訂單撮合失敗 - 賣方訂單數量不足：需要 {trade_quantity} 股，剩餘 {current_quantity} 股")
            else:
                # 更新系統 IPO 庫存 - 使用原子操作確保不會減成負數
                ipo_update_result = await self.db[Collections.MARKET_CONFIG].update_one(
                    {
                        "type": "ipo_status",
                        "shares_remaining": {"$gte": trade_quantity}  # 確保有足夠股數
                    },
                    {"$inc": {"shares_remaining": -trade_quantity}},
                    session=session
                )
                
                # 驗證 IPO 更新是否成功
                if ipo_update_result.modified_count == 0:
                    # 查詢實際剩餘 IPO 股數
                    current_ipo = await self.db[Collections.MARKET_CONFIG].find_one({"type": "ipo_status"}, session=session)
                    remaining_shares = current_ipo.get("shares_remaining", 0) if current_ipo else 0
                    logger.error(f"Failed to update IPO stock: insufficient shares for quantity {trade_quantity}, remaining: {remaining_shares}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"IPO 股數不足，無法完成交易。需要 {trade_quantity} 股，剩餘 {remaining_shares} 股"
                    )
                
                logger.info(f"✅ IPO stock updated: reduced by {trade_quantity} shares")
            
            # 更新使用者資產
            # 買方：安全扣除點數
            deduction_result = await self._safe_deduct_points(
                user_id=buy_order["user_id"],
                amount=trade_amount,
                operation_note=f"訂單撮合成交：{trade_quantity} 股 @ {trade_price} 元",
                change_type="stock_purchase",
                session=session
            )
            
            if not deduction_result['success']:
                buy_user_id = buy_order["user_id"]
                logger.error(f"Order matching point deduction failed for user ID: {buy_user_id}: {deduction_result['message']}")
                raise Exception(f"訂單撮合失敗 - 買方點數不足：需要 {trade_amount} 點，{deduction_result['message']}")
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
                # 使用原子操作確保股票數量不會變成負數
                stock_update_result = await self.db[Collections.STOCKS].update_one(
                    {
                        "user_id": sell_order["user_id"],
                        "stock_amount": {"$gte": trade_quantity}  # 確保有足夠股票
                    },
                    {"$inc": {"stock_amount": -trade_quantity}},
                    session=session
                )
                
                # 驗證股票更新是否成功
                if stock_update_result.modified_count == 0:
                    # 查詢實際持股數量以提供詳細錯誤訊息
                    current_holding = await self.db[Collections.STOCKS].find_one({"user_id": sell_order["user_id"]}, session=session)
                    current_stocks = current_holding.get("stock_amount", 0) if current_holding else 0
                    sell_user_id = sell_order["user_id"]
                    logger.error(f"Order matching stock deduction failed for user ID: {sell_user_id}: insufficient shares, quantity {trade_quantity}, current: {current_stocks}")
                    raise Exception(f"訂單撮合失敗 - 賣方股票不足：需要賣出 {trade_quantity} 股，實際持有 {current_stocks} 股")
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
            
            # 更新內存中的訂單數量和狀態（供撮合循環使用）
            buy_order["quantity"] -= trade_quantity
            buy_order["status"] = "filled" if buy_order["quantity"] == 0 else "partial"
            
            if not is_system_sale:
                sell_order["quantity"] -= trade_quantity
                sell_order["status"] = "filled" if sell_order["quantity"] == 0 else "partial"
            
            # 更新訂單狀態為 filled（僅在數量為 0 時）
            if buy_order["quantity"] == 0:
                await self.db[Collections.STOCK_ORDERS].update_one(
                    {"_id": buy_order["_id"]},
                    {"$set": {
                        "status": "filled",
                        "executed_at": datetime.now(timezone.utc)
                    }},
                    session=session
                )
            if not is_system_sale and sell_order["quantity"] == 0:
                await self.db[Collections.STOCK_ORDERS].update_one(
                    {"_id": sell_order["_id"]},
                    {"$set": {
                        "status": "filled", 
                        "executed_at": datetime.now(timezone.utc)
                    }},
                    session=session
                )
            
            logger.info(f"Orders matched: {trade_quantity} shares at {trade_price}")
            
            # 傳送交易通知給相關使用者
            await self._send_trade_notifications(
                buy_order=buy_order,
                sell_order=sell_order if not is_system_sale else None,
                trade_quantity=trade_quantity,
                trade_price=trade_price,
                trade_amount=trade_amount,
                is_system_sale=is_system_sale,
                session=session
            )
            
            # 交易完成後檢查涉及使用者的點數完整性
            user_ids_to_check = [buy_order["user_id"]]
            if not is_system_sale:
                user_ids_to_check.append(sell_order["user_id"])
            
            await self._validate_transaction_integrity(
                user_ids=user_ids_to_check,
                operation_name=f"訂單撮合 - {trade_quantity} 股 @ {trade_price} 元"
            )
            
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
                    # 買方：安全扣除點數
                    deduction_result = await self._safe_deduct_points(
                        user_id=buy_order["user_id"],
                        amount=trade_amount,
                        operation_note=f"訂單部分成交：{trade_quantity} 股 @ {trade_price} 元",
                        change_type="stock_purchase",
                        session=session
                    )
                    
                    if not deduction_result['success']:
                        logger.error(f"Partial order point deduction failed: {deduction_result['message']}")
                        raise Exception(f"買方點數不足: {deduction_result['message']}")
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
                    # 使用原子操作確保股票數量不會變成負數
                    stock_update_result = await self.db[Collections.STOCKS].update_one(
                        {
                            "user_id": sell_order["user_id"],
                            "stock_amount": {"$gte": trade_quantity}  # 確保有足夠股票
                        },
                        {"$inc": {"stock_amount": -trade_quantity}},
                        session=session
                    )
                    
                    # 驗證股票更新是否成功
                    if stock_update_result.modified_count == 0:
                        # 查詢實際持股數量以提供詳細錯誤訊息
                        current_holding = await self.db[Collections.STOCKS].find_one({"user_id": sell_order["user_id"]}, session=session)
                        current_stocks = current_holding.get("stock_amount", 0) if current_holding else 0
                        logger.error(f"Failed to update stock: insufficient shares for user {sell_order['user_id']}, quantity {trade_quantity}, current: {current_stocks}")
                        raise Exception(f"賣方股票不足：需要賣出 {trade_quantity} 股，實際持有 {current_stocks} 股")
                    
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
                    
                    # 注意：當使用 async with session.start_transaction() 時，事務會自動提交
                    # 不需要手動呼叫 session.commit_transaction()
                    
                    logger.info(f"Orders matched: {trade_quantity} shares at {trade_price}")
                    
            except Exception as e:
                
                logger.error(f"Failed to match orders with transaction: {e}")
    
    # ========== 新增學員管理方法 ==========
    
    async def create_student(self, student_id: str, username: str) -> bool:
        """
        建立新學員
        
        Args:
            student_id: 學員ID（唯一不變的辨識碼）
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
                                "stock_amount": 10,  # 10 股
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
                        
                        # 為新學員初始化股票持有記錄，給予5股初始股票
                        await self.db[Collections.STOCKS].insert_one({
                            "user_id": result.upserted_id,
                            "stock_amount": 10, # 10 股
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
                "message": f"批量更新使用者狀態失敗: {str(e)}",
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
                "message": f"查詢學員資料失敗: {str(e)}"
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

    # ========== PVP 猜拳功能 ==========
    
    async def create_pvp_challenge(self, from_user: str, amount: int, chat_id: str):
        """建立 PVP 挑戰 - 委託給 GameService"""
        from app.services.game_service import GameService
        
        game_service = GameService(self.db)
        return await game_service.create_pvp_challenge(from_user, amount, chat_id)
    
    async def set_pvp_creator_choice(self, from_user: str, challenge_id: str, choice: str):
        """設定 PVP 發起人的選擇 - 委託給 GameService"""
        from app.services.game_service import GameService
        
        game_service = GameService(self.db)
        return await game_service.set_pvp_creator_choice(from_user, challenge_id, choice)

    async def accept_pvp_challenge(self, from_user: str, challenge_id: str, choice: str):
        """接受 PVP 挑戰並進行猜拳遊戲 - 委託給 GameService"""
        from app.services.game_service import GameService
        
        game_service = GameService(self.db)
        return await game_service.accept_pvp_challenge(from_user, challenge_id, choice)
    
    async def cancel_pvp_challenge(self, user_id: str, challenge_id: str):
        """取消 PVP 挑戰 - 委託給 GameService"""
        from app.services.game_service import GameService
        
        game_service = GameService(self.db)
        return await game_service.cancel_pvp_challenge(user_id, challenge_id)
    
    async def simple_accept_pvp_challenge(self, from_user: str, challenge_id: str):
        """簡單 PVP 挑戰接受 - 委託給 GameService"""
        from app.services.game_service import GameService
        
        game_service = GameService(self.db)
        return await game_service.simple_accept_pvp_challenge(from_user, challenge_id)
    
    async def fix_negative_stocks(self, cancel_pending_orders: bool = True) -> dict:
        """
        修復負股票持有量
        
        Args:
            cancel_pending_orders: 是否同時取消相關使用者的待成交賣單
            
        Returns:
            dict: 修復結果
        """
        try:
            # 查找所有負股票持有量的記錄
            negative_stocks_cursor = self.db[Collections.STOCKS].find({"stock_amount": {"$lt": 0}})
            negative_stocks = await negative_stocks_cursor.to_list(length=None)
            
            if not negative_stocks:
                logger.info("沒有發現負股票持有量，無需修復")
                return {
                    "success": True,
                    "message": "沒有發現負股票持有量，無需修復",
                    "fixed_count": 0,
                    "cancelled_orders": 0
                }
            
            logger.info(f"找到 {len(negative_stocks)} 個負股票持有記錄")
            
            # 記錄負股票使用者詳情
            negative_users = []
            for stock in negative_stocks:
                user_id = stock.get("user_id")
                amount = stock.get("stock_amount", 0)
                
                # 獲取使用者訊息
                user = await self.db[Collections.USERS].find_one({"_id": user_id})
                username = user.get("name", "Unknown") if user else "Unknown"
                
                negative_users.append({
                    "user_id": str(user_id),
                    "username": username,
                    "negative_amount": amount
                })
                logger.warning(f"使用者 ID: {user_id} 持有 {amount} 股")
            
            cancelled_orders_count = 0
            
            if cancel_pending_orders:
                # 取消相關使用者的待成交賣單
                negative_user_ids = [stock["user_id"] for stock in negative_stocks]
                
                cancel_result = await self.db[Collections.STOCK_ORDERS].update_many(
                    {
                        "user_id": {"$in": negative_user_ids},
                        "side": "sell",
                        "status": {"$in": ["pending", "pending_limit", "partial"]}
                    },
                    {
                        "$set": {
                            "status": "cancelled",
                            "cancelled_at": datetime.now(timezone.utc),
                            "cancel_reason": "系統修復：負股票持有量"
                        }
                    }
                )
                cancelled_orders_count = cancel_result.modified_count
                logger.info(f"已取消 {cancelled_orders_count} 個待成交賣單")
            
            # 將負股票設為 0
            fix_result = await self.db[Collections.STOCKS].update_many(
                {"stock_amount": {"$lt": 0}},
                {"$set": {"stock_amount": 0}}
            )
            fixed_count = fix_result.modified_count
            logger.info(f"已修復 {fixed_count} 個負股票記錄，全部設為 0 股")
            
            # 驗證修復結果
            remaining_negative = await self.db[Collections.STOCKS].count_documents({"stock_amount": {"$lt": 0}})
            
            if remaining_negative == 0:
                logger.info("✅ 修復完成，所有負股票問題已解決")
                return {
                    "success": True,
                    "message": "修復完成，所有負股票問題已解決",
                    "fixed_count": fixed_count,
                    "cancelled_orders": cancelled_orders_count,
                    "negative_users": negative_users
                }
            else:
                logger.warning(f"⚠️ 仍有 {remaining_negative} 個負股票記錄")
                return {
                    "success": False,
                    "message": f"修復部分完成，仍有 {remaining_negative} 個負股票記錄",
                    "fixed_count": fixed_count,
                    "cancelled_orders": cancelled_orders_count,
                    "remaining_negative": remaining_negative,
                    "negative_users": negative_users
                }
                
        except Exception as e:
            logger.error(f"修復負股票過程中發生錯誤: {e}")
            return {
                "success": False,
                "message": f"修復過程中發生錯誤: {str(e)}",
                "fixed_count": 0,
                "cancelled_orders": 0
            }
    
    async def fix_invalid_orders(self) -> dict:
        """
        修復無效的訂單（quantity <= 0 但不是 filled 狀態）
        
        Returns:
            dict: 修復結果
        """
        try:
            # 查找無效的訂單（quantity <= 0 但狀態不是 filled）
            invalid_orders_cursor = self.db[Collections.STOCK_ORDERS].find({
                "$and": [
                    {"quantity": {"$lte": 0}},
                    {"status": {"$nin": ["filled", "cancelled"]}}
                ]
            })
            invalid_orders = await invalid_orders_cursor.to_list(length=None)
            
            if not invalid_orders:
                logger.info("沒有發現無效訂單，無需修復")
                return {
                    "success": True,
                    "message": "沒有發現無效訂單，無需修復",
                    "fixed_count": 0,
                    "invalid_orders": []
                }
            
            logger.warning(f"找到 {len(invalid_orders)} 個無效訂單")
            
            # 記錄無效訂單詳情
            invalid_order_details = []
            for order in invalid_orders:
                user_id = order.get("user_id")
                user = await self.db[Collections.USERS].find_one({"_id": user_id})
                username = user.get("name", "Unknown") if user else "Unknown"
                
                invalid_order_details.append({
                    "order_id": str(order["_id"]),
                    "user_id": str(user_id),
                    "username": username,
                    "quantity": order.get("quantity", 0),
                    "side": order.get("side", "unknown"),
                    "status": order.get("status", "unknown"),
                    "created_at": order.get("created_at"),
                    "filled_quantity": order.get("filled_quantity", 0)
                })
                
                logger.warning(f"無效訂單: User ID: {user_id} - Order {order['_id']}: quantity={order.get('quantity', 0)}, status={order.get('status', 'unknown')}")
            
            # 修復策略：將這些訂單標記為已取消
            fix_result = await self.db[Collections.STOCK_ORDERS].update_many(
                {
                    "$and": [
                        {"quantity": {"$lte": 0}},
                        {"status": {"$nin": ["filled", "cancelled"]}}
                    ]
                },
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.now(timezone.utc),
                        "cancel_reason": "系統修復：無效數量訂單（quantity <= 0）"
                    }
                }
            )
            
            fixed_count = fix_result.modified_count
            logger.info(f"已修復 {fixed_count} 個無效訂單，標記為已取消")
            
            return {
                "success": True,
                "message": f"修復完成，已取消 {fixed_count} 個無效訂單",
                "fixed_count": fixed_count,
                "invalid_orders": invalid_order_details
            }
                
        except Exception as e:
            logger.error(f"修復無效訂單過程中發生錯誤: {e}")
            return {
                "success": False,
                "message": f"修復過程中發生錯誤: {str(e)}",
                "fixed_count": 0,
                "invalid_orders": []
            }

    async def _send_trade_notifications(self, buy_order: dict, sell_order: dict, trade_quantity: int, 
                                      trade_price: float, trade_amount: float, is_system_sale: bool, session=None):
        """傳送交易通知給買方和賣方"""
        try:
            # 獲取買方使用者資訊
            buy_user = await self.db[Collections.USERS].find_one({"_id": buy_order["user_id"]}, session=session)
            if not buy_user or not buy_user.get("telegram_id"):
                logger.warning(f"無法傳送買方通知：使用者 {buy_order['user_id']} 未設定 telegram_id")
            else:
                await self._send_single_trade_notification(
                    user_telegram_id=buy_user["telegram_id"],
                    action="buy",
                    quantity=trade_quantity,
                    price=trade_price,
                    total_amount=trade_amount,
                    order_id=str(buy_order["_id"])
                )
            
            # 獲取賣方使用者資訊（如果不是系統 IPO 交易）
            if not is_system_sale and sell_order:
                sell_user = await self.db[Collections.USERS].find_one({"_id": sell_order["user_id"]}, session=session)
                if not sell_user or not sell_user.get("telegram_id"):
                    logger.warning(f"無法傳送賣方通知：使用者 {sell_order['user_id']} 未設定 telegram_id")
                else:
                    await self._send_single_trade_notification(
                        user_telegram_id=sell_user["telegram_id"],
                        action="sell",
                        quantity=trade_quantity,
                        price=trade_price,
                        total_amount=trade_amount,
                        order_id=str(sell_order["_id"])
                    )
                    
        except Exception as e:
            # 通知傳送失敗不應該影響交易本身
            logger.error(f"傳送交易通知時發生錯誤: {e}")

    async def _send_single_trade_notification(self, user_telegram_id: int, action: str, quantity: int, 
                                            price: float, total_amount: float, order_id: str):
        """傳送單一交易通知"""
        try:
            if not config.external_services.telegram_bot_api_url or not config.security.internal_api_key:
                logger.warning("Telegram Bot API 設定不完整，跳過通知傳送")
                return
            
            # 構建通知請求
            notification_url = f"{config.external_services.telegram_bot_api_url.rstrip('/')}/bot/notification/trade"
            
            payload = {
                "user_id": user_telegram_id,
                "action": action,
                "quantity": quantity,
                "price": price,
                "total_amount": total_amount,
                "order_id": order_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "token": config.security.internal_api_key
            }
            
            # 傳送通知（設定短超時避免阻塞交易）
            response = requests.post(
                notification_url,
                json=payload,
                headers=headers,
                timeout=5  # 5秒超時
            )
            
            if response.status_code == 200:
                logger.info(f"成功傳送 {action} 交易通知給使用者 {user_telegram_id}")
            else:
                logger.warning(f"傳送交易通知失敗: HTTP {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"傳送交易通知超時，使用者: {user_telegram_id}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"傳送交易通知網路錯誤: {e}")
        except Exception as e:
            logger.error(f"傳送交易通知發生未預期錯誤: {e}")

    async def cancel_stock_order(self, user_id: str, order_id: str, reason: str = "user_cancelled") -> dict:
        """
        取消股票訂單 (舊架構方法)
        
        Args:
            user_id: 使用者 ID
            order_id: 訂單 ID
            reason: 取消原因
            
        Returns:
            dict: 取消結果
        """
        try:
            # 轉換 order_id 為 ObjectId
            try:
                order_oid = ObjectId(order_id)
            except Exception:
                return {
                    "success": False,
                    "message": "無效的訂單 ID 格式"
                }
            
            # 取得訂單
            order = await self.db[Collections.STOCK_ORDERS].find_one({"_id": order_oid})
            if not order:
                return {
                    "success": False,
                    "message": "訂單不存在"
                }
            
            # 驗證使用者擁有權
            # 由於訂單的 user_id 是 MongoDB ObjectId，但目前的 user_id 是內部 ID，需要轉換
            order_user_id = order.get("user_id")
            
            # 通過內部 user_id 查找對應的 MongoDB ObjectId
            current_user = await self._get_user_(user_id)
            if not current_user:
                logger.warning(f"無法找到目前使用者: {user_id}")
                return {
                    "success": False,
                    "message": "目前使用者不存在"
                }
            
            current_user_oid = current_user.get("_id")
            
            logger.info(f"權限驗證 - 訂單使用者ObjectId: {order_user_id} ({type(order_user_id)})")
            logger.info(f"權限驗證 - 目前使用者ID: {user_id} -> ObjectId: {current_user_oid} ({type(current_user_oid)})")
            logger.info(f"權限驗證 - ObjectId比較結果: {order_user_id == current_user_oid}")
            
            if order_user_id != current_user_oid:
                logger.warning(f"權限驗證失敗 - 訂單 {order_id} 屬於使用者 {order_user_id}，但目前使用者為 {user_id}")
                return {
                    "success": False,
                    "message": f"您沒有權限取消此訂單 (訂單使用者: {order_user_id}, 目前使用者: {user_id})"
                }
            
            # 詳細檢查訂單是否可以取消
            order_status = order.get("status", "")
            order_type = order.get("order_type", "")
            filled_quantity = order.get("filled_quantity", 0)
            remaining_quantity = order.get("quantity", 0)
            
            # 基本狀態檢查
            cancellable_statuses = ["pending", "partial", "pending_limit"]
            
            if order_status not in cancellable_statuses:
                status_messages = {
                    "filled": "已成交的訂單無法取消",
                    "cancelled": "訂單已經被取消"
                }
                message = status_messages.get(order_status, f"訂單狀態為 {order_status}，無法取消")
                logger.warning(f"嘗試取消不可取消的訂單 - 訂單: {order_id}, 狀態: {order_status}, 使用者: {user_id}")
                return {
                    "success": False,
                    "message": message
                }
            
            # 檢查是否還有可取消的數量
            if remaining_quantity <= 0:
                logger.warning(f"嘗試取消無剩餘數量的訂單 - 訂單: {order_id}, 剩餘數量: {remaining_quantity}, 使用者: {user_id}")
                return {
                    "success": False,
                    "message": "訂單已無剩餘數量可取消"
                }
            
            # 檢查訂單是否在撮合中
            # 這可以通過檢查訂單的最後更新時間來判斷
            last_updated = order.get("updated_at", order.get("created_at"))
            if last_updated:
                from datetime import timedelta
                now = datetime.now(timezone.utc)
                # 確保 last_updated 有時區訊息，如果沒有則假設為 UTC
                if isinstance(last_updated, datetime):
                    if last_updated.tzinfo is None:
                        last_updated = last_updated.replace(tzinfo=timezone.utc)
                    # 如果訂單在最近 10 秒內有更新，可能正在撮合中
                    if (now - last_updated) < timedelta(seconds=10):
                        logger.info(f"訂單可能正在撮合中，等待後重試 - 訂單: {order_id}, 使用者: {user_id}")
                        return {
                            "success": False,
                            "message": "訂單可能正在撮合中，請稍後再試"
                        }
            
            # 記錄取消操作
            logger.info(f"準備取消訂單 - 訂單: {order_id}, 狀態: {order_status}, 類型: {order_type}, 剩餘數量: {remaining_quantity}, 已成交: {filled_quantity}, 使用者: {user_id}")
            
            # 使用原子操作更新訂單狀態，確保只有可取消狀態的訂單才會被更新
            now = datetime.now(timezone.utc)
            update_result = await self.db[Collections.STOCK_ORDERS].update_one(
                {
                    "_id": order_oid,
                    "status": {"$in": cancellable_statuses},  # 再次確認狀態
                    "quantity": {"$gt": 0}  # 確保還有剩餘數量
                },
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": now,
                        "cancel_reason": reason,
                        "updated_at": now
                    }
                }
            )
            
            if update_result.modified_count == 0:
                # 可能是在更新過程中訂單狀態發生了變化
                logger.warning(f"取消訂單失敗，可能訂單狀態已變更 - 訂單: {order_id}, 使用者: {user_id}")
                
                # 重新查詢訂單狀態
                updated_order = await self.db[Collections.STOCK_ORDERS].find_one({"_id": order_oid})
                if updated_order:
                    current_status = updated_order.get("status", "")
                    if current_status == "cancelled":
                        return {
                            "success": True,
                            "message": "訂單已經被取消",
                            "order_id": order_id
                        }
                    elif current_status == "filled":
                        return {
                            "success": False,
                            "message": "訂單已成交，無法取消"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"取消訂單失敗，訂單狀態已變更為 {current_status}"
                        }
                else:
                    return {
                        "success": False,
                        "message": "訂單不存在"
                    }
            
            logger.info(f"訂單已取消: {order_id}, 使用者: {user_id}, 原因: {reason}")
            
            # 發送取消通知
            await self._send_cancellation_notification_legacy(
                user_id=user_id,
                order_id=order_id,
                order_type=order.get("order_type", "unknown"),
                side=order.get("side", "unknown"),
                quantity=order.get("quantity", 0),
                price=order.get("price", 0.0),
                reason=reason
            )
            
            return {
                "success": True,
                "message": "訂單已成功取消",
                "order_id": order_id
            }
            
        except Exception as e:
            logger.error(f"取消訂單時發生錯誤 - 使用者: {user_id}, 訂單: {order_id}, 錯誤: {e}")
            return {
                "success": False,
                "message": "取消訂單時發生錯誤"
            }

    async def _send_cancellation_notification_legacy(self, user_id: str, order_id: str, 
                                                   order_type: str, side: str, quantity: int,
                                                   price: float, reason: str):
        """發送取消訂單通知 (舊架構版本)"""
        try:
            if not config.external_services.telegram_bot_api_url or not config.security.internal_api_key:
                logger.warning("Telegram Bot API 設定不完整，跳過取消通知傳送")
                return
            
            # 獲取使用者的 Telegram ID
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            if not user or not user.get("telegram_id"):
                logger.warning(f"無法傳送取消通知：使用者 {user_id} 未設定 telegram_id")
                return
            
            # 構建取消通知
            action_text = "買入" if side == "buy" else "賣出"
            type_text = "市價單" if order_type == "market" else "限價單"
            
            message = f"🚫 您的訂單已取消\n\n• 訂單號碼：{order_id}\n• 類型：{type_text}\n• 操作：{action_text}\n• 數量：{quantity}\n• 價格：{price:.2f}\n• 取消原因：{reason}"
            
            notification_url = f"{config.external_services.telegram_bot_api_url.rstrip('/')}/bot/direct/send"
            
            payload = {
                "user_id": user["telegram_id"],
                "message": message,
                "parse_mode": "MarkdownV2"
            }
            
            headers = {
                "Content-Type": "application/json",
                "token": config.security.internal_api_key
            }
            
            response = requests.post(
                notification_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"成功傳送取消通知給使用者 {user['telegram_id']}")
            else:
                logger.warning(f"傳送取消通知失敗: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"傳送取消通知發生錯誤: {e}")


    # PVP 相關方法
    async def get_user_active_pvp_challenges(self, user_id: str) -> dict:
        """查詢使用者的活躍 PVP 挑戰"""
        try:
            from app.services.game_service import get_game_service
            game_service = get_game_service()
            return await game_service.get_user_active_challenges(user_id)
        except Exception as e:
            logger.error(f"查詢使用者活躍挑戰失敗: {e}")
            return {
                "success": False,
                "message": "查詢挑戰失敗",
                "challenges": []
            }
