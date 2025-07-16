"""
Enhanced Trading Domain Services
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

from .entities import Stock, StockOrder, UserStock, OrderType, OrderStatus
from .repositories import StockRepository, OrderRepository, UserStockRepository
from ..user.entities import User, PointChangeType
from ..user.repositories import UserRepository
from ..common.exceptions import (
    BusinessRuleException, InsufficientResourceException, 
    ValidationException, MarketClosedException, InvalidOrderException
)
from ..common.events import DomainEvent
from ..common.value_objects import Money, Quantity, Price

logger = logging.getLogger(__name__)


class TradingDomainService:
    """
    交易領域服務
    處理複雜的交易業務邏輯
    """
    
    def __init__(
        self,
        stock_repository: StockRepository,
        order_repository: OrderRepository,
        user_stock_repository: UserStockRepository,
        user_repository: UserRepository
    ):
        self.stock_repository = stock_repository
        self.order_repository = order_repository
        self.user_stock_repository = user_stock_repository
        self.user_repository = user_repository
    
    async def validate_order(self, user: User, stock: Stock, order_type: OrderType, 
                           quantity: int, price: int) -> None:
        """驗證訂單的業務規則"""
        
        # 檢查市場是否開放
        if not await self._is_market_open():
            raise MarketClosedException("Market is currently closed")
        
        # 檢查股票是否存在且可交易
        if not stock:
            raise ValidationException("Stock not found", "symbol")
        
        if not stock.is_available():
            raise BusinessRuleException("Stock is not available for trading", "stock_unavailable")
        
        # 檢查數量和價格限制
        if quantity <= 0 or quantity > 1000000:
            raise ValidationException("Invalid quantity", "quantity", quantity)
        
        if price <= 0 or price > 1000000:
            raise ValidationException("Invalid price", "price", price)
        
        # 檢查價格是否在合理範圍內（±10%）
        price_deviation = abs(price - stock.current_price) / stock.current_price
        if price_deviation > 0.1:  # 10% 限制
            raise BusinessRuleException("Price deviates too much from current price", "price_deviation")
        
        # 買單特定驗證
        if order_type == OrderType.BUY:
            await self._validate_buy_order(user, stock, quantity, price)
        
        # 賣單特定驗證
        elif order_type == OrderType.SELL:
            await self._validate_sell_order(user, stock, quantity, price)
    
    async def _validate_buy_order(self, user: User, stock: Stock, quantity: int, price: int) -> None:
        """驗證買單"""
        # 檢查用戶是否有足夠的點數
        total_cost = quantity * price
        if not user.has_sufficient_points(total_cost):
            raise InsufficientResourceException(
                "Insufficient points for buy order",
                "points",
                total_cost,
                user.points
            )
        
        # 檢查股票是否有足夠的可用股數
        if not stock.can_buy(quantity):
            raise InsufficientResourceException(
                f"Insufficient shares for {stock.symbol}",
                "shares",
                quantity,
                stock.available_shares
            )
        
        # 檢查用戶是否達到持倉限制
        user_stock = await self.user_stock_repository.find_by_user_and_symbol(user.id, stock.symbol)
        current_position = user_stock.quantity if user_stock else 0
        max_position = stock.total_shares // 10  # 最多持有總股數的10%
        
        if current_position + quantity > max_position:
            raise BusinessRuleException(
                f"Position would exceed maximum allowed ({max_position})",
                "position_limit"
            )
    
    async def _validate_sell_order(self, user: User, stock: Stock, quantity: int, price: int) -> None:
        """驗證賣單"""
        # 檢查用戶是否有足夠的股票
        user_stock = await self.user_stock_repository.find_by_user_and_symbol(user.id, stock.symbol)
        if not user_stock or not user_stock.can_sell(quantity):
            available_quantity = user_stock.quantity if user_stock else 0
            raise InsufficientResourceException(
                f"Insufficient shares to sell",
                "shares",
                quantity,
                available_quantity
            )
    
    async def place_order(self, user: User, stock: Stock, order_type: OrderType, 
                         quantity: int, price: int) -> StockOrder:
        """下單"""
        # 驗證訂單
        await self.validate_order(user, stock, order_type, quantity, price)
        
        # 創建訂單
        order = StockOrder(
            user_id=user.id,
            symbol=stock.symbol,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        
        # 處理資源預留
        if order_type == OrderType.BUY:
            # 扣除用戶點數
            total_cost = quantity * price
            user.deduct_points(total_cost, PointChangeType.TRADING_BUY, f"Buy order for {stock.symbol}")
            
            # 預留股票
            stock.reserve_shares(quantity)
            
        elif order_type == OrderType.SELL:
            # 預留用戶股票
            user_stock = await self.user_stock_repository.find_by_user_and_symbol(user.id, stock.symbol)
            if not user_stock.remove_shares(quantity):
                raise BusinessRuleException("Failed to reserve shares for sell order", "reserve_failed")
            
            # 更新用戶持股
            await self.user_stock_repository.update(user_stock)
        
        # 保存訂單
        await self.order_repository.save(order)
        
        # 更新股票和用戶資料
        await self.stock_repository.update(stock)
        await self.user_repository.update(user)
        
        logger.info(f"Order placed: {order.id} for user {user.id}")
        return order
    
    async def cancel_order(self, order: StockOrder, user: User) -> None:
        """取消訂單"""
        if order.user_id != user.id:
            raise BusinessRuleException("Cannot cancel order of another user", "unauthorized")
        
        if not order.is_active():
            raise BusinessRuleException("Cannot cancel inactive order", "order_inactive")
        
        # 取消訂單
        order.cancel_order()
        
        # 釋放資源
        await self._release_order_resources(order, user)
        
        # 保存變更
        await self.order_repository.update(order)
        await self.user_repository.update(user)
        
        logger.info(f"Order cancelled: {order.id} for user {user.id}")
    
    async def _release_order_resources(self, order: StockOrder, user: User) -> None:
        """釋放訂單資源"""
        stock = await self.stock_repository.find_by_symbol(order.symbol)
        
        if order.order_type == OrderType.BUY:
            # 退還點數
            refund_amount = order.remaining_quantity * order.price
            user.add_points(refund_amount, PointChangeType.TRADING_BUY, f"Refund for cancelled buy order")
            
            # 釋放股票
            stock.release_shares(order.remaining_quantity)
            await self.stock_repository.update(stock)
            
        elif order.order_type == OrderType.SELL:
            # 退還股票
            user_stock = await self.user_stock_repository.find_by_user_and_symbol(user.id, order.symbol)
            if user_stock:
                user_stock.add_shares(order.remaining_quantity, user_stock.average_price)
                await self.user_stock_repository.update(user_stock)
            else:
                # 創建新的持股記錄
                user_stock = UserStock(
                    user_id=user.id,
                    symbol=order.symbol,
                    quantity=order.remaining_quantity,
                    average_price=order.price
                )
                await self.user_stock_repository.save(user_stock)
    
    async def match_orders(self, symbol: str) -> List[Dict]:
        """撮合訂單"""
        # 獲取活躍的買單和賣單
        buy_orders = await self._get_active_buy_orders(symbol)
        sell_orders = await self._get_active_sell_orders(symbol)
        
        # 按價格排序
        buy_orders.sort(key=lambda x: (-x.price, x.created_at))  # 價格高的優先，時間早的優先
        sell_orders.sort(key=lambda x: (x.price, x.created_at))  # 價格低的優先，時間早的優先
        
        matches = []
        
        # 撮合邏輯
        for buy_order in buy_orders:
            for sell_order in sell_orders:
                if buy_order.can_match_with(sell_order):
                    match_result = await self._execute_match(buy_order, sell_order)
                    if match_result:
                        matches.append(match_result)
                    
                    # 如果買單已完全成交，跳出內層循環
                    if buy_order.is_fully_filled():
                        break
        
        return matches
    
    async def _get_active_buy_orders(self, symbol: str) -> List[StockOrder]:
        """獲取活躍的買單"""
        orders = await self.order_repository.find_active_orders(symbol)
        return [order for order in orders if order.is_buy_order()]
    
    async def _get_active_sell_orders(self, symbol: str) -> List[StockOrder]:
        """獲取活躍的賣單"""
        orders = await self.order_repository.find_active_orders(symbol)
        return [order for order in orders if order.is_sell_order()]
    
    async def _execute_match(self, buy_order: StockOrder, sell_order: StockOrder) -> Optional[Dict]:
        """執行訂單撮合"""
        # 計算成交數量
        match_quantity = min(buy_order.remaining_quantity, sell_order.remaining_quantity)
        
        # 確定成交價格（使用賣單價格）
        match_price = sell_order.price
        
        # 執行交易
        buy_order.fill_order(match_quantity, match_price)
        sell_order.fill_order(match_quantity, match_price)
        
        # 更新買方
        buyer = await self.user_repository.find_by_id(buy_order.user_id)
        await self._update_buyer_position(buyer, sell_order.symbol, match_quantity, match_price)
        
        # 更新賣方
        seller = await self.user_repository.find_by_id(sell_order.user_id)
        await self._update_seller_position(seller, sell_order.symbol, match_quantity, match_price)
        
        # 處理價格差異退款（如果買單價格高於成交價格）
        if buy_order.price > match_price:
            price_diff = buy_order.price - match_price
            refund_amount = match_quantity * price_diff
            buyer.add_points(refund_amount, PointChangeType.TRADING_BUY, "Price difference refund")
        
        # 保存變更
        await self.order_repository.update(buy_order)
        await self.order_repository.update(sell_order)
        await self.user_repository.update(buyer)
        await self.user_repository.update(seller)
        
        # 返回撮合結果
        return {
            "buy_order_id": str(buy_order.id),
            "sell_order_id": str(sell_order.id),
            "symbol": buy_order.symbol,
            "quantity": match_quantity,
            "price": match_price,
            "total_amount": match_quantity * match_price,
            "buyer_id": str(buyer.id),
            "seller_id": str(seller.id),
            "executed_at": datetime.utcnow()
        }
    
    async def _update_buyer_position(self, buyer: User, symbol: str, quantity: int, price: int) -> None:
        """更新買方持股"""
        user_stock = await self.user_stock_repository.find_by_user_and_symbol(buyer.id, symbol)
        
        if user_stock:
            user_stock.add_shares(quantity, price)
            await self.user_stock_repository.update(user_stock)
        else:
            # 創建新的持股記錄
            user_stock = UserStock(
                user_id=buyer.id,
                symbol=symbol,
                quantity=quantity,
                average_price=price
            )
            await self.user_stock_repository.save(user_stock)
    
    async def _update_seller_position(self, seller: User, symbol: str, quantity: int, price: int) -> None:
        """更新賣方點數"""
        # 賣方獲得點數
        total_amount = quantity * price
        seller.add_points(total_amount, PointChangeType.TRADING_SELL, f"Sell {symbol}")
    
    async def calculate_portfolio_value(self, user_id: str) -> Dict:
        """計算投資組合價值"""
        user_stocks = await self.user_stock_repository.find_by_user_id(user_id)
        
        total_value = 0
        total_cost = 0
        positions = []
        
        for user_stock in user_stocks:
            if user_stock.quantity > 0:
                stock = await self.stock_repository.find_by_symbol(user_stock.symbol)
                if stock:
                    current_value = user_stock.quantity * stock.current_price
                    cost_basis = user_stock.quantity * user_stock.average_price
                    profit_loss = current_value - cost_basis
                    profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
                    
                    total_value += current_value
                    total_cost += cost_basis
                    
                    positions.append({
                        "symbol": user_stock.symbol,
                        "quantity": user_stock.quantity,
                        "average_price": user_stock.average_price,
                        "current_price": stock.current_price,
                        "cost_basis": cost_basis,
                        "current_value": current_value,
                        "profit_loss": profit_loss,
                        "profit_loss_percentage": profit_loss_pct
                    })
        
        total_profit_loss = total_value - total_cost
        total_profit_loss_pct = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percentage": total_profit_loss_pct,
            "positions": positions
        }
    
    async def _is_market_open(self) -> bool:
        """檢查市場是否開放"""
        # 這裡應該實現實際的市場開放檢查邏輯
        # 暫時返回 True
        return True
    
    async def get_order_book(self, symbol: str) -> Dict:
        """獲取訂單簿"""
        buy_orders = await self._get_active_buy_orders(symbol)
        sell_orders = await self._get_active_sell_orders(symbol)
        
        # 按價格聚合
        buy_book = {}
        sell_book = {}
        
        for order in buy_orders:
            price = order.price
            if price not in buy_book:
                buy_book[price] = 0
            buy_book[price] += order.remaining_quantity
        
        for order in sell_orders:
            price = order.price
            if price not in sell_book:
                sell_book[price] = 0
            sell_book[price] += order.remaining_quantity
        
        # 排序
        buy_orders_sorted = sorted(buy_book.items(), key=lambda x: -x[0])  # 價格降序
        sell_orders_sorted = sorted(sell_book.items(), key=lambda x: x[0])  # 價格升序
        
        return {
            "symbol": symbol,
            "buy_orders": [{"price": price, "quantity": qty} for price, qty in buy_orders_sorted],
            "sell_orders": [{"price": price, "quantity": qty} for price, qty in sell_orders_sorted]
        }


class OrderMatchingService:
    """
    訂單撮合服務
    專門處理訂單匹配邏輯
    """
    
    def __init__(self, trading_service: TradingDomainService):
        self.trading_service = trading_service
    
    async def match_orders_for_symbol(self, symbol: str) -> List[Dict]:
        """為特定股票撮合訂單"""
        return await self.trading_service.match_orders(symbol)
    
    async def match_all_orders(self) -> Dict[str, List[Dict]]:
        """撮合所有股票的訂單"""
        # 獲取所有有活躍訂單的股票
        all_symbols = await self._get_symbols_with_active_orders()
        
        results = {}
        for symbol in all_symbols:
            matches = await self.match_orders_for_symbol(symbol)
            if matches:
                results[symbol] = matches
        
        return results
    
    async def _get_symbols_with_active_orders(self) -> List[str]:
        """獲取有活躍訂單的股票代碼"""
        # 這裡應該實現實際的查詢邏輯
        # 暫時返回空列表
        return []


class RiskManagementService:
    """
    風險管理服務
    處理交易風險控制
    """
    
    def __init__(self, trading_service: TradingDomainService):
        self.trading_service = trading_service
    
    async def check_position_risk(self, user_id: str, symbol: str, quantity: int) -> Dict:
        """檢查持倉風險"""
        user_stock = await self.trading_service.user_stock_repository.find_by_user_and_symbol(user_id, symbol)
        stock = await self.trading_service.stock_repository.find_by_symbol(symbol)
        
        current_position = user_stock.quantity if user_stock else 0
        new_position = current_position + quantity
        
        # 計算風險指標
        position_ratio = new_position / stock.total_shares if stock else 0
        max_position_ratio = 0.1  # 最大持倉比率 10%
        
        return {
            "current_position": current_position,
            "new_position": new_position,
            "position_ratio": position_ratio,
            "max_position_ratio": max_position_ratio,
            "is_risky": position_ratio > max_position_ratio,
            "risk_level": "HIGH" if position_ratio > 0.08 else "MEDIUM" if position_ratio > 0.05 else "LOW"
        }
    
    async def check_concentration_risk(self, user_id: str) -> Dict:
        """檢查投資組合集中度風險"""
        user_stocks = await self.trading_service.user_stock_repository.find_by_user_id(user_id)
        
        if not user_stocks:
            return {"concentration_risk": "LOW", "diversification_score": 100}
        
        # 計算投資組合總價值
        total_value = 0
        position_values = []
        
        for user_stock in user_stocks:
            if user_stock.quantity > 0:
                stock = await self.trading_service.stock_repository.find_by_symbol(user_stock.symbol)
                if stock:
                    position_value = user_stock.quantity * stock.current_price
                    total_value += position_value
                    position_values.append(position_value)
        
        # 計算最大單一持倉比率
        max_position_ratio = max(position_values) / total_value if total_value > 0 else 0
        
        # 計算多元化分數
        diversification_score = 100 - (max_position_ratio * 100)
        
        # 判斷風險等級
        if max_position_ratio > 0.5:
            risk_level = "HIGH"
        elif max_position_ratio > 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "concentration_risk": risk_level,
            "max_position_ratio": max_position_ratio,
            "diversification_score": diversification_score,
            "total_positions": len(position_values)
        }