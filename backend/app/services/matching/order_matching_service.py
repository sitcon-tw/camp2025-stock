from __future__ import annotations
from ...infrastructure.database.base_service import BaseService
from ..market import get_market_service
from app.core.database import Collections
from datetime import datetime, timezone
from bson import ObjectId
from typing import Dict, Any, List, Optional
import logging
import asyncio
import random

logger = logging.getLogger(__name__)


def get_order_matching_service() -> OrderMatchingService:
    """OrderMatchingService 的依賴注入函數"""
    return OrderMatchingService()


class OrderMatchingService(BaseService):
    """訂單撮合服務 - 負責處理訂單撮合邏輯"""
    
    def __init__(self, db=None):
        super().__init__(db)
        self.market_service = get_market_service()
    
    async def try_match_orders(self) -> Dict[str, Any]:
        """嘗試撮合買賣訂單"""
        try:
            # 獲取待撮合的訂單
            buy_book = await self._get_buy_orders()
            sell_book = await self._get_sell_orders()
            
            # 安全排序訂單
            buy_book = self._sort_orders_safely(buy_book, is_buy=True)
            sell_book = self._sort_orders_safely(sell_book, is_buy=False)
            
            # 加入系統 IPO 訂單
            sell_book = await self._add_system_ipo_orders(sell_book)
            
            # 執行撮合
            matches_found = await self._execute_matching(buy_book, sell_book)
            
            # 重新啟用限制訂單
            await self._reactivate_limit_orders()
            
            return {
                "success": True,
                "matches_found": matches_found,
                "buy_orders": len(buy_book),
                "sell_orders": len(sell_book)
            }
            
        except Exception as e:
            logger.error(f"Failed to match orders: {e}")
            return {
                "success": False,
                "error": str(e),
                "matches_found": 0
            }
    
    async def match_single_order_pair(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any]) -> Dict[str, Any]:
        """撮合單一訂單對"""
        max_retries = 8
        retry_delay = 0.003
        
        for attempt in range(max_retries):
            try:
                result = await self._match_orders_with_transaction(buy_order, sell_order)
                if attempt > 0:
                    logger.info(f"Order matching succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # 檢查是否為事務不支援的錯誤
                if "Transaction numbers are only allowed on a replica set member or mongos" in error_str:
                    logger.warning("MongoDB transactions not supported, falling back to non-transactional mode")
                    return await self._match_orders_without_transaction(buy_order, sell_order)
                
                # 檢查是否為可重試的錯誤
                elif ("WriteConflict" in error_str or "TransientTransactionError" in error_str) and attempt < max_retries - 1:
                    self._log_write_conflict("order_matching", attempt, max_retries)
                    delay = retry_delay * (2 ** attempt) + random.uniform(0, 0.001)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Order matching failed after {attempt + 1} attempts: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "trade_quantity": 0
                    }
        
        return {
            "success": False,
            "error": "Order matching failed after maximum retries",
            "trade_quantity": 0
        }
    
    async def _get_buy_orders(self) -> List[Dict[str, Any]]:
        """獲取買單"""
        cursor = self.db[Collections.STOCK_ORDERS].find(
            {
                "side": "buy",
                "status": {"$in": ["pending", "partial", "pending_limit"]},
                "order_type": {"$in": ["limit", "market_converted"]}
            }
        ).sort([("price", -1), ("created_at", 1)])
        
        return await cursor.to_list(None)
    
    async def _get_sell_orders(self) -> List[Dict[str, Any]]:
        """獲取賣單"""
        cursor = self.db[Collections.STOCK_ORDERS].find(
            {
                "side": "sell",
                "status": {"$in": ["pending", "partial", "pending_limit"]},
                "order_type": {"$in": ["limit", "market_converted"]}
            }
        ).sort([("price", 1), ("created_at", 1)])
        
        return await cursor.to_list(None)
    
    def _sort_orders_safely(self, orders: List[Dict[str, Any]], is_buy: bool) -> List[Dict[str, Any]]:
        """安全排序訂單"""
        def safe_sort_key(order):
            price = order.get('price', 0 if not is_buy else float('inf'))
            created_at = order.get('created_at')
            
            # 確保 created_at 是 timezone-aware
            if created_at is None:
                created_at = datetime.now(timezone.utc)
            elif isinstance(created_at, datetime) and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            elif not isinstance(created_at, datetime):
                created_at = datetime.now(timezone.utc)
            
            return (price, created_at)
        
        # 買單按價格降序排序，賣單按價格升序排序
        return sorted(orders, key=safe_sort_key, reverse=is_buy)
    
    async def _add_system_ipo_orders(self, sell_book: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """加入系統 IPO 訂單"""
        try:
            ipo_config = await self.market_service.get_ipo_config()
            if not ipo_config:
                ipo_config = await self.market_service.initialize_ipo_config()
            
            shares_remaining = ipo_config.get("shares_remaining", 0)
            
            logger.info(f"IPO status check: config exists={ipo_config is not None}, shares_remaining={shares_remaining}")
            
            if shares_remaining > 0:
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
                
                # 重新排序包含系統 IPO 訂單的賣單
                sell_book = self._sort_orders_safely(sell_book, is_buy=False)
            else:
                logger.info(f"❌ IPO not added to sell book: no shares remaining (remaining: {shares_remaining})")
        
        except Exception as e:
            logger.error(f"Failed to add system IPO orders: {e}")
        
        return sell_book
    
    async def _execute_matching(self, buy_book: List[Dict[str, Any]], sell_book: List[Dict[str, Any]]) -> int:
        """執行撮合邏輯"""
        buy_idx, sell_idx = 0, 0
        matches_found = 0
        
        logger.info(f"🔍Starting order matching: {len(buy_book)} buy orders, {len(sell_book)} sell orders")
        
        while buy_idx < len(buy_book) and sell_idx < len(sell_book):
            buy_order = buy_book[buy_idx]
            sell_order = sell_book[sell_idx]
            
            # 驗證訂單有效性
            if not self._validate_order_for_matching(buy_order, True):
                buy_idx += 1
                continue
            
            if not self._validate_order_for_matching(sell_order, False):
                sell_idx += 1
                continue
            
            # 檢查價格限制
            if not await self._check_price_limits(buy_order, sell_order):
                # 如果價格限制不通過，跳過相應的訂單
                if buy_order.get("status") == "pending_limit":
                    buy_idx += 1
                if sell_order.get("status") == "pending_limit":
                    sell_idx += 1
                continue
            
            # 檢查價格匹配
            buy_price = buy_order.get("price", 0)
            sell_price = sell_order.get("price", float('inf'))
            
            if buy_price >= sell_price:
                # 防止自我交易
                if buy_order.get("user_id") == sell_order.get("user_id"):
                    logger.warning(f"Prevented self-trading for user {buy_order.get('user_id')}")
                    sell_idx += 1
                    continue
                
                # 執行撮合
                is_system_sale = sell_order.get("is_system_order", False)
                logger.info(f"Matching orders: Buy {buy_order.get('quantity')} @ {buy_price} vs Sell {sell_order.get('quantity')} @ {sell_price} {'(SYSTEM IPO)' if is_system_sale else ''}")
                
                result = await self.match_single_order_pair(buy_order, sell_order)
                if result["success"]:
                    matches_found += 1
                
                # 更新索引
                if buy_order.get("quantity", 0) <= 0:
                    buy_idx += 1
                if sell_order.get("quantity", 0) <= 0:
                    sell_idx += 1
            else:
                # 買價小於賣價，無法撮合
                logger.debug(f"No more matches possible: buy price {buy_price} < sell price {sell_price}")
                break
        
        if matches_found > 0:
            logger.info(f"Order matching completed: {matches_found} matches executed")
        
        return matches_found
    
    def _validate_order_for_matching(self, order: Dict[str, Any], is_buy: bool) -> bool:
        """驗證訂單是否可以撮合"""
        quantity = order.get("quantity", 0)
        if quantity <= 0:
            side = "buy" if is_buy else "sell"
            logger.warning(f"Skipping {side} order with invalid quantity: {quantity}, order_id: {order.get('_id')}")
            return False
        
        return True
    
    async def _check_price_limits(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any]) -> bool:
        """檢查價格限制"""
        # 檢查買單價格限制
        if buy_order.get("status") == "pending_limit":
            buy_price = buy_order.get("price", 0)
            if await self.market_service.check_price_limit(buy_price):
                await self.db[Collections.STOCK_ORDERS].update_one(
                    {"_id": buy_order["_id"]},
                    {"$set": {"status": "pending"}}
                )
                buy_order["status"] = "pending"
                logger.info(f"Buy order {buy_order['_id']} price limit lifted")
            else:
                return False
        
        # 檢查賣單價格限制
        if sell_order.get("status") == "pending_limit":
            sell_price = sell_order.get("price", 0)
            if await self.market_service.check_price_limit(sell_price):
                await self.db[Collections.STOCK_ORDERS].update_one(
                    {"_id": sell_order["_id"]},
                    {"$set": {"status": "pending"}}
                )
                sell_order["status"] = "pending"
                logger.info(f"Sell order {sell_order['_id']} price limit lifted")
            else:
                return False
        
        return True
    
    async def _reactivate_limit_orders(self):
        """重新啟用限制訂單"""
        try:
            pending_limit_orders = await self.db[Collections.STOCK_ORDERS].find(
                {"status": "pending_limit", "order_type": "limit"}
            ).to_list(None)
            
            reactivated_count = 0
            for order in pending_limit_orders:
                order_price = order.get("price", 0)
                
                if await self.market_service.check_price_limit(order_price):
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
                await self.try_match_orders()
                
        except Exception as e:
            logger.error(f"Failed to reactivate limit orders: {e}")
    
    async def _match_orders_with_transaction(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any]) -> Dict[str, Any]:
        """使用事務撮合訂單"""
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await self._match_orders_logic(buy_order, sell_order, session)
    
    async def _match_orders_without_transaction(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any]) -> Dict[str, Any]:
        """不使用事務撮合訂單"""
        return await self._match_orders_logic(buy_order, sell_order)
    
    async def _match_orders_logic(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any], session=None) -> Dict[str, Any]:
        """撮合訂單邏輯"""
        try:
            # 決定成交價格
            trade_price = await self._determine_fair_trade_price(buy_order, sell_order)
            
            # 計算交易數量
            buy_quantity = buy_order.get("quantity", 0)
            sell_quantity = sell_order.get("quantity", 0)
            trade_quantity = min(buy_quantity, sell_quantity)
            
            if trade_quantity <= 0:
                return {"success": False, "error": "Invalid trade quantity", "trade_quantity": 0}
            
            # 執行交易
            await self._execute_trade(buy_order, sell_order, trade_quantity, trade_price, session)
            
            # 更新訂單狀態
            await self._update_order_status(buy_order, sell_order, trade_quantity, trade_price, session)
            
            # 處理 IPO 訂單
            if sell_order.get("is_system_order"):
                await self._handle_ipo_trade(trade_quantity, session)
            
            # 發送通知
            await self._send_trade_notifications(buy_order, sell_order, trade_quantity, trade_price)
            
            # 清除快取
            await self._invalidate_trade_caches(buy_order, sell_order)
            
            logger.info(f"Trade executed: {trade_quantity} shares @ {trade_price}")
            
            return {
                "success": True,
                "trade_quantity": trade_quantity,
                "trade_price": trade_price
            }
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            return {"success": False, "error": str(e), "trade_quantity": 0}
    
    async def _determine_fair_trade_price(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any]) -> float:
        """決定公平的成交價格"""
        buy_price = buy_order.get("price", 0)
        sell_price = sell_order.get("price", float('inf'))
        buy_order_type = buy_order.get("order_type", "limit")
        sell_order_type = sell_order.get("order_type", "limit")
        is_system_sale = sell_order.get("is_system_order", False)
        
        try:
            # 如果是系統 IPO 訂單，使用 IPO 價格
            if is_system_sale:
                logger.info(f"System IPO trade: using IPO price {sell_price}")
                return sell_price
            
            # 市價單與限價單的撮合
            if buy_order_type in ["market", "market_converted"]:
                if sell_order_type == "limit":
                    return sell_price
                else:
                    return await self.market_service.get_current_stock_price()
            
            elif sell_order_type in ["market", "market_converted"]:
                if buy_order_type == "limit":
                    return buy_price
                else:
                    return await self.market_service.get_current_stock_price()
            
            # 限價單與限價單的撮合
            elif buy_order_type == "limit" and sell_order_type == "limit":
                buy_time = buy_order.get("created_at")
                sell_time = sell_order.get("created_at")
                
                if buy_time and sell_time:
                    return buy_price if buy_time < sell_time else sell_price
                else:
                    return sell_price
            
            # 預設情況
            else:
                if buy_price > 0 and sell_price < float('inf'):
                    return (buy_price + sell_price) / 2
                else:
                    return await self.market_service.get_current_stock_price()
                    
        except Exception as e:
            logger.error(f"Error determining fair trade price: {e}")
            return sell_price if sell_price < float('inf') else buy_price
    
    async def _execute_trade(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any], 
                           trade_quantity: int, trade_price: float, session=None):
        """執行交易"""
        buyer_id = buy_order["user_id"]
        seller_id = sell_order["user_id"]
        
        # 處理買方
        if buyer_id != "SYSTEM":
            # 扣除買方點數
            required_points = int(trade_price * trade_quantity)
            await self.db[Collections.USERS].update_one(
                {"_id": buyer_id},
                {"$inc": {"points": -required_points}},
                session=session
            )
            
            # 增加買方持股
            await self.db[Collections.STOCKS].update_one(
                {"user_id": buyer_id},
                {"$inc": {"stock_amount": trade_quantity}},
                upsert=True,
                session=session
            )
            
            # 記錄買方點數變化
            await self._log_point_change(
                buyer_id, "stock_purchase", -required_points,
                f"購買 {trade_quantity} 股 @ {trade_price}",
                session=session
            )
        
        # 處理賣方
        if seller_id != "SYSTEM":
            # 減少賣方持股
            await self.db[Collections.STOCKS].update_one(
                {"user_id": seller_id},
                {"$inc": {"stock_amount": -trade_quantity}},
                session=session
            )
            
            # 增加賣方點數
            earned_points = int(trade_price * trade_quantity)
            await self.db[Collections.USERS].update_one(
                {"_id": seller_id},
                {"$inc": {"points": earned_points}},
                session=session
            )
            
            # 記錄賣方點數變化
            await self._log_point_change(
                seller_id, "stock_sale", earned_points,
                f"賣出 {trade_quantity} 股 @ {trade_price}",
                session=session
            )
    
    async def _update_order_status(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any], 
                                 trade_quantity: int, trade_price: float, session=None):
        """更新訂單狀態"""
        current_time = datetime.now(timezone.utc)
        
        # 更新買單
        buy_quantity = buy_order.get("quantity", 0)
        buy_filled_quantity = buy_order.get("filled_quantity", 0) + trade_quantity
        buy_remaining = buy_quantity - buy_filled_quantity
        
        if buy_remaining <= 0:
            # 完全成交
            await self.db[Collections.STOCK_ORDERS].update_one(
                {"_id": buy_order["_id"]},
                {
                    "$set": {
                        "status": "filled",
                        "filled_quantity": buy_filled_quantity,
                        "filled_price": trade_price,
                        "filled_at": current_time
                    }
                },
                session=session
            )
            buy_order["quantity"] = 0
        else:
            # 部分成交
            await self.db[Collections.STOCK_ORDERS].update_one(
                {"_id": buy_order["_id"]},
                {
                    "$set": {
                        "status": "partial",
                        "filled_quantity": buy_filled_quantity,
                        "filled_price": trade_price,
                        "quantity": buy_remaining
                    }
                },
                session=session
            )
            buy_order["quantity"] = buy_remaining
        
        # 更新賣單
        if not sell_order.get("is_system_order"):
            sell_quantity = sell_order.get("quantity", 0)
            sell_filled_quantity = sell_order.get("filled_quantity", 0) + trade_quantity
            sell_remaining = sell_quantity - sell_filled_quantity
            
            if sell_remaining <= 0:
                # 完全成交
                await self.db[Collections.STOCK_ORDERS].update_one(
                    {"_id": sell_order["_id"]},
                    {
                        "$set": {
                            "status": "filled",
                            "filled_quantity": sell_filled_quantity,
                            "filled_price": trade_price,
                            "filled_at": current_time
                        }
                    },
                    session=session
                )
                sell_order["quantity"] = 0
            else:
                # 部分成交
                await self.db[Collections.STOCK_ORDERS].update_one(
                    {"_id": sell_order["_id"]},
                    {
                        "$set": {
                            "status": "partial",
                            "filled_quantity": sell_filled_quantity,
                            "filled_price": trade_price,
                            "quantity": sell_remaining
                        }
                    },
                    session=session
                )
                sell_order["quantity"] = sell_remaining
        else:
            # 系統訂單，更新剩餘數量
            sell_order["quantity"] = sell_order.get("quantity", 0) - trade_quantity
    
    async def _handle_ipo_trade(self, trade_quantity: int, session=None):
        """處理 IPO 交易"""
        try:
            await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "ipo_status"},
                {
                    "$inc": {"shares_remaining": -trade_quantity},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                },
                session=session
            )
            logger.info(f"IPO shares remaining reduced by {trade_quantity}")
        except Exception as e:
            logger.error(f"Failed to handle IPO trade: {e}")
    
    async def _send_trade_notifications(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any], 
                                      trade_quantity: int, trade_price: float):
        """發送交易通知"""
        try:
            # 這裡可以整合通知服務
            # 暫時只記錄日誌
            logger.info(f"Trade notification: {trade_quantity} shares @ {trade_price}")
        except Exception as e:
            logger.error(f"Failed to send trade notifications: {e}")
    
    async def _invalidate_trade_caches(self, buy_order: Dict[str, Any], sell_order: Dict[str, Any]):
        """清除交易相關快取"""
        try:
            # 清除使用者組合快取
            if buy_order.get("user_id") != "SYSTEM":
                await self.cache_invalidator.invalidate_user_portfolio_cache(str(buy_order["user_id"]))
            
            if sell_order.get("user_id") != "SYSTEM":
                await self.cache_invalidator.invalidate_user_portfolio_cache(str(sell_order["user_id"]))
            
            # 清除價格相關快取
            await self.cache_invalidator.invalidate_price_related_caches()
            
        except Exception as e:
            logger.error(f"Failed to invalidate trade caches: {e}")
    
    async def trigger_async_matching(self, reason: str = "manual_trigger"):
        """觸發異步撮合"""
        try:
            # 這裡可以整合排程器
            await self.try_match_orders()
            logger.debug(f"Triggered async matching: {reason}")
        except Exception as e:
            logger.error(f"Failed to trigger async matching: {e}")