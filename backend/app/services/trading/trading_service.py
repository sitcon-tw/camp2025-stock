from __future__ import annotations
from ...infrastructure.database.base_service import BaseService
from ..market import get_market_service
from app.core.database import Collections
from app.schemas.user import StockOrderRequest, StockOrderResponse
from datetime import datetime, timezone
from bson import ObjectId
from typing import Dict, Any, Optional, List
import logging
import asyncio
import random

logger = logging.getLogger(__name__)


def get_trading_service() -> TradingService:
    """TradingService 的依賴注入函數"""
    return TradingService()


class TradingService(BaseService):
    """交易服務 - 負責處理股票交易相關功能"""
    
    def __init__(self, db=None):
        super().__init__(db)
        self.market_service = get_market_service()
    
    async def place_stock_order(self, user_id: str, request: StockOrderRequest) -> StockOrderResponse:
        """下股票訂單"""
        try:
            # 檢查市場是否開放
            if not await self.market_service.is_market_open():
                return StockOrderResponse(
                    success=False,
                    message="市場目前未開放交易"
                )
            
            # 驗證使用者和訂單
            user_oid = ObjectId(user_id)
            user = await self._get_user_by_id(user_id)
            if not user:
                return StockOrderResponse(
                    success=False,
                    message="使用者不存在"
                )
            
            # 驗證訂單基本資訊
            validation_result = await self._validate_order_basic(request)
            if not validation_result["valid"]:
                return StockOrderResponse(
                    success=False,
                    message=validation_result["message"]
                )
            
            # 檢查價格限制
            order_status = "pending"
            limit_exceeded = False
            limit_info = None
            
            if request.order_type == "limit":
                limit_info = await self.market_service.get_price_limit_info(request.price)
                if not limit_info["within_limit"]:
                    order_status = "pending_limit"
                    limit_exceeded = True
                    logger.info(f"Order price {request.price} exceeds daily limit, order will be queued")
            
            # 檢查使用者資金和持股
            balance_check = await self._check_user_balance(user, request)
            if not balance_check["valid"]:
                return StockOrderResponse(
                    success=False,
                    message=balance_check["message"]
                )
            
            # 建立訂單
            order_doc = await self._create_order_document(user_oid, request, order_status, limit_exceeded)
            
            # 執行訂單
            if request.order_type == "market":
                return await self._execute_market_order(user_oid, order_doc)
            else:
                return await self._execute_limit_order(order_doc, limit_exceeded, limit_info)
                
        except Exception as e:
            logger.error(f"Failed to place stock order: {e}")
            return StockOrderResponse(
                success=False,
                message=f"下單失敗：{str(e)}"
            )
    
    async def cancel_stock_order(self, user_id: str, order_id: str, reason: str = "user_cancelled") -> Dict[str, Any]:
        """取消股票訂單"""
        try:
            user_oid = ObjectId(user_id)
            order_oid = ObjectId(order_id)
            
            # 查找訂單
            order = await self.db[Collections.STOCK_ORDERS].find_one({
                "_id": order_oid,
                "user_id": user_oid,
                "status": {"$in": ["pending", "partial", "pending_limit"]}
            })
            
            if not order:
                return {
                    "success": False,
                    "message": "訂單不存在或無法取消"
                }
            
            # 取消訂單
            await self.db[Collections.STOCK_ORDERS].update_one(
                {"_id": order_oid},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancelled_at": datetime.now(timezone.utc),
                        "cancel_reason": reason
                    }
                }
            )
            
            # 如果是買單，退還點數
            if order["side"] == "buy":
                await self._refund_order_points(user_oid, order)
            
            # 清除快取
            await self.cache_invalidator.invalidate_user_portfolio_cache(user_id)
            await self.cache_invalidator.invalidate_price_related_caches()
            
            logger.info(f"Order cancelled: {order_id} by user {user_id}, reason: {reason}")
            
            return {
                "success": True,
                "message": "訂單已取消",
                "order_id": order_id
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return {
                "success": False,
                "message": f"取消訂單失敗：{str(e)}"
            }
    
    async def get_user_stock_orders(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取使用者股票訂單"""
        try:
            user_oid = ObjectId(user_id)
            
            orders_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"user_id": user_oid}
            ).sort("created_at", -1).limit(limit)
            
            orders = await orders_cursor.to_list(length=limit)
            
            # 格式化訂單資料
            formatted_orders = []
            for order in orders:
                formatted_order = {
                    "order_id": str(order["_id"]),
                    "order_type": order.get("order_type", "limit"),
                    "side": order.get("side", "buy"),
                    "quantity": self._get_display_quantity(order),
                    "price": order.get("price", 0),
                    "status": order.get("status", "pending"),
                    "created_at": order.get("created_at"),
                    "filled_quantity": order.get("filled_quantity", 0),
                    "filled_price": order.get("filled_price"),
                    "filled_at": order.get("filled_at")
                }
                formatted_orders.append(formatted_order)
            
            return formatted_orders
            
        except Exception as e:
            logger.error(f"Failed to get user stock orders: {e}")
            return []
    
    async def _validate_order_basic(self, request: StockOrderRequest) -> Dict[str, Any]:
        """驗證訂單基本資訊"""
        if request.quantity <= 0:
            return {"valid": False, "message": "訂單數量必須大於 0"}
        
        if request.order_type not in ["market", "limit"]:
            return {"valid": False, "message": "無效的訂單類型"}
        
        if request.side not in ["buy", "sell"]:
            return {"valid": False, "message": "無效的交易方向"}
        
        if request.order_type == "limit" and request.price <= 0:
            return {"valid": False, "message": "限價單價格必須大於 0"}
        
        return {"valid": True, "message": ""}
    
    async def _check_user_balance(self, user: Dict[str, Any], request: StockOrderRequest) -> Dict[str, Any]:
        """檢查使用者餘額和持股"""
        user_oid = user["_id"]
        
        if request.side == "buy":
            return await self._check_buy_balance(user, request)
        else:
            return await self._check_sell_balance(user_oid, request)
    
    async def _check_buy_balance(self, user: Dict[str, Any], request: StockOrderRequest) -> Dict[str, Any]:
        """檢查買入餘額"""
        if request.order_type == "market":
            current_price = await self.market_service.get_current_stock_price()
            required_points = int(current_price * request.quantity)
        else:
            required_points = int(request.price * request.quantity)
        
        user_points = user.get("points", 0)
        if user_points < required_points:
            return {
                "valid": False,
                "message": f"點數不足，需要 {required_points} 點，目前你的點數: {user_points}"
            }
        
        return {"valid": True, "message": ""}
    
    async def _check_sell_balance(self, user_oid: ObjectId, request: StockOrderRequest) -> Dict[str, Any]:
        """檢查賣出持股"""
        # 獲取持股
        stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user_oid})
        current_stocks = stock_holding.get("stock_amount", 0) if stock_holding else 0
        
        if current_stocks < 0:
            return {
                "valid": False,
                "message": f"帳戶異常：股票持有量為負數 ({current_stocks} 股)，請聯繫管理員處理"
            }
        
        # 檢查待售訂單
        pending_sell_result = await self.db[Collections.STOCK_ORDERS].aggregate([
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
        ]).to_list(1)
        
        total_pending_sells = pending_sell_result[0]["total_pending"] if pending_sell_result else 0
        total_sell_requirement = request.quantity + total_pending_sells
        
        if current_stocks < total_sell_requirement:
            if total_pending_sells > 0:
                return {
                    "valid": False,
                    "message": f"持股不足：您已有 {total_pending_sells} 股待賣訂單，加上本次 {request.quantity} 股，總計 {total_sell_requirement} 股超過您的持股 {current_stocks} 股"
                }
            else:
                return {
                    "valid": False,
                    "message": f"持股不足，需要 {request.quantity} 股，僅有 {current_stocks} 股"
                }
        
        return {"valid": True, "message": ""}
    
    async def _create_order_document(self, user_oid: ObjectId, request: StockOrderRequest, 
                                   order_status: str, limit_exceeded: bool) -> Dict[str, Any]:
        """建立訂單文件"""
        order_doc = {
            "user_id": user_oid,
            "order_type": request.order_type,
            "side": request.side,
            "quantity": request.quantity,
            "price": request.price,
            "status": order_status,
            "created_at": datetime.now(timezone.utc),
            "stock_amount": request.quantity if request.side == "buy" else -request.quantity
        }
        
        if limit_exceeded:
            order_doc["limit_exceeded"] = True
            order_doc["limit_note"] = f"Order price {request.price} exceeds daily trading limit"
        
        return order_doc
    
    async def _execute_market_order(self, user_oid: ObjectId, order_doc: Dict[str, Any]) -> StockOrderResponse:
        """執行市價單"""
        max_retries = 5
        retry_delay = 0.01
        
        for attempt in range(max_retries):
            try:
                return await self._execute_market_order_with_transaction(user_oid, order_doc)
            except Exception as e:
                error_str = str(e)
                if "Transaction numbers are only allowed on a replica set member or mongos" in error_str:
                    return await self._execute_market_order_without_transaction(user_oid, order_doc)
                elif "WriteConflict" in error_str and attempt < max_retries - 1:
                    self._log_write_conflict("market_order", attempt, max_retries)
                    await asyncio.sleep(retry_delay * (2 ** attempt) + random.uniform(0, 0.001))
                else:
                    raise
        
        raise Exception("Market order execution failed after maximum retries")
    
    async def _execute_market_order_with_transaction(self, user_oid: ObjectId, order_doc: Dict[str, Any]) -> StockOrderResponse:
        """使用事務執行市價單"""
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                return await self._execute_market_order_logic(user_oid, order_doc, session)
    
    async def _execute_market_order_without_transaction(self, user_oid: ObjectId, order_doc: Dict[str, Any]) -> StockOrderResponse:
        """不使用事務執行市價單"""
        return await self._execute_market_order_logic(user_oid, order_doc)
    
    async def _execute_market_order_logic(self, user_oid: ObjectId, order_doc: Dict[str, Any], session=None) -> StockOrderResponse:
        """市價單執行邏輯"""
        current_price = await self.market_service.get_current_stock_price()
        order_doc["price"] = current_price
        
        if order_doc["side"] == "buy":
            required_points = int(current_price * order_doc["quantity"])
            
            # 扣除點數
            update_result = await self.db[Collections.USERS].update_one(
                {"_id": user_oid, "points": {"$gte": required_points}},
                {"$inc": {"points": -required_points}},
                session=session
            )
            
            if update_result.matched_count == 0:
                return StockOrderResponse(
                    success=False,
                    message="點數不足或使用者不存在"
                )
            
            # 增加持股
            await self.db[Collections.STOCKS].update_one(
                {"user_id": user_oid},
                {"$inc": {"stock_amount": order_doc["quantity"]}},
                upsert=True,
                session=session
            )
            
            # 記錄點數變化
            await self._log_point_change(
                user_oid, "stock_purchase", -required_points,
                f"購買 {order_doc['quantity']} 股 @ {current_price}",
                session=session
            )
            
        else:  # sell
            # 檢查並減少持股
            update_result = await self.db[Collections.STOCKS].update_one(
                {"user_id": user_oid, "stock_amount": {"$gte": order_doc["quantity"]}},
                {"$inc": {"stock_amount": -order_doc["quantity"]}},
                session=session
            )
            
            if update_result.matched_count == 0:
                return StockOrderResponse(
                    success=False,
                    message="持股不足"
                )
            
            # 增加點數
            earned_points = int(current_price * order_doc["quantity"])
            await self.db[Collections.USERS].update_one(
                {"_id": user_oid},
                {"$inc": {"points": earned_points}},
                session=session
            )
            
            # 記錄點數變化
            await self._log_point_change(
                user_oid, "stock_sale", earned_points,
                f"賣出 {order_doc['quantity']} 股 @ {current_price}",
                session=session
            )
        
        # 記錄訂單為已完成
        order_doc.update({
            "status": "filled",
            "filled_price": current_price,
            "filled_quantity": order_doc["quantity"],
            "filled_at": datetime.now(timezone.utc)
        })
        
        result = await self.db[Collections.STOCK_ORDERS].insert_one(order_doc, session=session)
        order_id = str(result.inserted_id)
        
        # 清除快取
        await self.cache_invalidator.invalidate_user_portfolio_cache(str(user_oid))
        await self.cache_invalidator.invalidate_price_related_caches()
        
        return StockOrderResponse(
            success=True,
            order_id=order_id,
            message=f"市價單已成交，價格: {current_price} 元/股",
            executed_price=current_price,
            executed_quantity=order_doc["quantity"]
        )
    
    async def _execute_limit_order(self, order_doc: Dict[str, Any], limit_exceeded: bool, limit_info: Optional[Dict[str, Any]]) -> StockOrderResponse:
        """執行限價單"""
        # 插入訂單
        result = await self._insert_order_with_retry(order_doc)
        order_id = str(result.inserted_id)
        
        # 清除快取
        await self.cache_invalidator.invalidate_user_portfolio_cache(str(order_doc["user_id"]))
        await self.cache_invalidator.invalidate_price_related_caches()
        
        if limit_exceeded:
            # 構建限制訊息
            limit_msg = f"限價單已提交但因超出漲跌限制而暫時等待 ({order_doc['side']} {order_doc['quantity']} 股 @ {order_doc['price']} 元)"
            if limit_info:
                limit_msg += f"\n📊 當日漲跌限制：{limit_info['limit_percent']:.1f}%"
                limit_msg += f"\n📈 基準價格：{limit_info['reference_price']:.2f} 元"
                limit_msg += f"\n📊 允許交易範圍：{limit_info['min_price']:.2f} ~ {limit_info['max_price']:.2f} 元"
            
            return StockOrderResponse(
                success=True,
                order_id=order_id,
                message=limit_msg
            )
        else:
            # 觸發異步撮合
            from ..matching import get_order_matching_service
            matching_service = get_order_matching_service()
            await matching_service.trigger_async_matching("limit_order_placed")
            
            success_msg = f"限價單已提交，等待撮合 ({order_doc['side']} {order_doc['quantity']} 股 @ {order_doc['price']} 元)"
            if limit_info:
                success_msg += f"\n📊 當日漲跌限制：{limit_info['limit_percent']:.1f}% (範圍：{limit_info['min_price']:.2f} ~ {limit_info['max_price']:.2f} 元)"
            
            return StockOrderResponse(
                success=True,
                order_id=order_id,
                message=success_msg
            )
    
    async def _insert_order_with_retry(self, order_doc: Dict[str, Any]):
        """帶重試機制的訂單插入"""
        max_retries = 3
        retry_delay = 0.01
        
        for attempt in range(max_retries):
            try:
                return await self.db[Collections.STOCK_ORDERS].insert_one(order_doc)
            except Exception as e:
                if "WriteConflict" in str(e) and attempt < max_retries - 1:
                    self._log_write_conflict("insert_order", attempt, max_retries)
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    raise
        
        raise Exception("Order insertion failed after maximum retries")
    
    async def _refund_order_points(self, user_oid: ObjectId, order: Dict[str, Any]):
        """退還訂單點數"""
        if order["side"] == "buy":
            refund_amount = int(order["price"] * order["quantity"])
            filled_quantity = order.get("filled_quantity", 0)
            
            if filled_quantity > 0:
                # 部分成交，只退還未成交部分
                remaining_quantity = order["quantity"] - filled_quantity
                refund_amount = int(order["price"] * remaining_quantity)
            
            if refund_amount > 0:
                await self.db[Collections.USERS].update_one(
                    {"_id": user_oid},
                    {"$inc": {"points": refund_amount}}
                )
                
                await self._log_point_change(
                    user_oid, "order_refund", refund_amount,
                    f"訂單取消退款 - 訂單ID: {order['_id']}"
                )
    
    def _get_display_quantity(self, order: Dict[str, Any]) -> int:
        """獲取顯示數量"""
        if order.get("status") == "partial":
            return order.get("quantity", 0)
        else:
            return order.get("quantity", 0)