"""
Trading Domain Services
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
    處理複雜的交易業務邏輯和規則
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
    
    async def place_order(self, user_id: ObjectId, symbol: str, order_type: OrderType, quantity: int, price: int) -> StockOrder:
        """下單"""
        if quantity <= 0:
            raise DomainException("數量必須大於 0")
        
        if price <= 0:
            raise DomainException("價格必須大於 0")
        
        # 檢查股票是否存在
        stock = await self.stock_repository.find_by_symbol(symbol)
        if not stock:
            raise DomainException("股票不存在")
        
        # 檢查使用者是否存在
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise DomainException("使用者不存在")
        
        # 創建訂單
        order = StockOrder(
            user_id=user_id,
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING
        )
        
        # 買單檢查餘額
        if order_type == OrderType.BUY:
            total_cost = quantity * price
            if user.points < total_cost:
                raise InsufficientBalanceException("餘額不足")
        
        # 賣單檢查持股
        elif order_type == OrderType.SELL:
            user_stock = await self.user_stock_repository.find_by_user_and_symbol(user_id, symbol)
            if not user_stock or user_stock.quantity < quantity:
                raise DomainException("持股不足")
        
        # 儲存訂單
        return await self.order_repository.save(order)
    
    async def cancel_order(self, order_id: ObjectId, user_id: ObjectId) -> bool:
        """取消訂單"""
        order = await self.order_repository.find_by_id(order_id)
        if not order:
            raise DomainException("訂單不存在")
        
        if order.user_id != user_id:
            raise DomainException("無權取消此訂單")
        
        if not order.is_active():
            raise DomainException("訂單已完成或已取消")
        
        order.cancel_order()
        return await self.order_repository.update(order)
    
    async def execute_trade(self, buy_order: StockOrder, sell_order: StockOrder, trade_quantity: int, trade_price: int) -> bool:
        """執行交易"""
        if not buy_order.is_active() or not sell_order.is_active():
            raise DomainException("訂單已完成或已取消")
        
        if buy_order.symbol != sell_order.symbol:
            raise DomainException("股票代碼不匹配")
        
        if trade_quantity <= 0:
            raise DomainException("交易數量必須大於 0")
        
        if trade_quantity > min(buy_order.remaining_quantity, sell_order.remaining_quantity):
            raise DomainException("交易數量超過可用數量")
        
        # 獲取交易雙方使用者
        buyer = await self.user_repository.find_by_id(buy_order.user_id)
        seller = await self.user_repository.find_by_id(sell_order.user_id)
        
        if not buyer or not seller:
            raise DomainException("使用者不存在")
        
        # 計算交易金額
        total_amount = trade_quantity * trade_price
        
        # 檢查買方餘額
        if buyer.points < total_amount:
            raise InsufficientBalanceException("買方餘額不足")
        
        # 檢查賣方持股
        seller_stock = await self.user_stock_repository.find_by_user_and_symbol(seller.id, buy_order.symbol)
        if not seller_stock or seller_stock.quantity < trade_quantity:
            raise DomainException("賣方持股不足")
        
        # 執行交易
        # 1. 更新買方點數和持股
        buyer.deduct_points(total_amount)
        await self.user_repository.update(buyer)
        
        buyer_stock = await self.user_stock_repository.find_by_user_and_symbol(buyer.id, buy_order.symbol)
        if buyer_stock:
            buyer_stock.add_shares(trade_quantity, trade_price)
            await self.user_stock_repository.update(buyer_stock)
        else:
            new_stock = UserStock(
                user_id=buyer.id,
                symbol=buy_order.symbol,
                quantity=trade_quantity,
                average_price=trade_price,
                total_value=total_amount
            )
            await self.user_stock_repository.save(new_stock)
        
        # 2. 更新賣方點數和持股
        seller.add_points(total_amount)
        await self.user_repository.update(seller)
        
        seller_stock.remove_shares(trade_quantity)
        if seller_stock.quantity == 0:
            await self.user_stock_repository.delete(seller.id, buy_order.symbol)
        else:
            await self.user_stock_repository.update(seller_stock)
        
        # 3. 更新訂單狀態
        buy_order.fill_order(trade_quantity)
        sell_order.fill_order(trade_quantity)
        
        await self.order_repository.update(buy_order)
        await self.order_repository.update(sell_order)
        
        return True
    
    async def get_user_portfolio(self, user_id: ObjectId) -> List[UserStock]:
        """獲取使用者投資組合"""
        return await self.user_stock_repository.find_by_user_id(user_id)
    
    async def get_user_orders(self, user_id: ObjectId, skip: int = 0, limit: int = 100) -> List[StockOrder]:
        """獲取使用者訂單"""
        return await self.order_repository.find_by_user_id(user_id, skip, limit)
    
    async def get_stock_orders(self, symbol: str, skip: int = 0, limit: int = 100) -> List[StockOrder]:
        """獲取股票訂單"""
        return await self.order_repository.find_by_symbol(symbol, skip, limit)
    
    async def get_order_book(self, symbol: str) -> dict:
        """獲取訂單簿"""
        active_orders = await self.order_repository.find_active_orders(symbol)
        
        buy_orders = [order for order in active_orders if order.order_type == OrderType.BUY]
        sell_orders = [order for order in active_orders if order.order_type == OrderType.SELL]
        
        # 排序買單（價格從高到低）
        buy_orders.sort(key=lambda x: x.price, reverse=True)
        
        # 排序賣單（價格從低到高）
        sell_orders.sort(key=lambda x: x.price)
        
        return {
            "symbol": symbol,
            "buy_orders": buy_orders,
            "sell_orders": sell_orders
        }