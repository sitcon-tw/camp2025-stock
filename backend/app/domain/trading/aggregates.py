"""
Trading Domain Aggregates
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from dataclasses import dataclass

from .entities import Stock, StockOrder, UserStock, OrderType, OrderStatus
from .value_objects import TradingPair, OrderBook, MarketState, TradingSession
from ..user.entities import User, PointChangeType
from ..common.events import AggregateRoot, DomainEvent
from ..common.exceptions import (
    BusinessRuleException, InsufficientResourceException, 
    ValidationException, MarketClosedException
)
from ..common.value_objects import Money, Quantity, Price


@dataclass
class TradeExecutedEvent(DomainEvent):
    """交易執行事件"""
    trade_id: str
    buyer_id: str
    seller_id: str
    symbol: str
    quantity: int
    price: int
    total_amount: int
    executed_at: datetime


@dataclass
class MarketStateChangedEvent(DomainEvent):
    """市場狀態變更事件"""
    old_state: str
    new_state: str
    symbol: str
    changed_at: datetime


class TradingAggregate(AggregateRoot):
    """
    交易聚合根
    管理完整的交易流程，包含股票、訂單、市場狀態
    """
    
    def __init__(
        self,
        symbol: str,
        stock: Stock,
        market_state: MarketState,
        id: Optional[ObjectId] = None
    ):
        super().__init__()
        self.id = id or ObjectId()
        self.symbol = symbol
        self.stock = stock
        self.market_state = market_state
        self.active_orders: List[StockOrder] = []
        self.trading_session = TradingSession.create_session()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # 驗證聚合一致性
        self._validate_aggregate_consistency()
    
    def _validate_aggregate_consistency(self) -> None:
        """驗證聚合一致性"""
        if not self.stock:
            raise ValidationException("Stock is required for trading aggregate", "stock")
        
        if self.stock.symbol != self.symbol:
            raise ValidationException("Stock symbol must match aggregate symbol", "symbol")
        
        if not self.market_state:
            raise ValidationException("Market state is required", "market_state")
    
    def open_market(self, opened_by: ObjectId, reason: str = "") -> None:
        """開市"""
        if self.market_state.is_open():
            raise BusinessRuleException("Market is already open", "market_already_open")
        
        old_state = self.market_state.status
        self.market_state = self.market_state.open_market(opened_by, reason)
        self.updated_at = datetime.utcnow()
        
        # 發布市場狀態變更事件
        self.add_domain_event(MarketStateChangedEvent(
            event_id=str(ObjectId()),
            occurred_at=datetime.utcnow(),
            old_state=old_state,
            new_state=self.market_state.status,
            symbol=self.symbol,
            changed_at=datetime.utcnow()
        ))
        
        # 增加版本號
        self.increment_version()
    
    def close_market(self, closed_by: ObjectId, reason: str = "") -> None:
        """收市"""
        if not self.market_state.is_open():
            raise BusinessRuleException("Market is not open", "market_not_open")
        
        old_state = self.market_state.status
        self.market_state = self.market_state.close_market(closed_by, reason)
        self.updated_at = datetime.utcnow()
        
        # 取消所有未完成訂單
        cancelled_orders = []
        for order in self.active_orders:
            if order.is_active():
                order.cancel_order()
                cancelled_orders.append(order)
        
        # 發布市場狀態變更事件
        self.add_domain_event(MarketStateChangedEvent(
            event_id=str(ObjectId()),
            occurred_at=datetime.utcnow(),
            old_state=old_state,
            new_state=self.market_state.status,
            symbol=self.symbol,
            changed_at=datetime.utcnow()
        ))
        
        # 增加版本號
        self.increment_version()
    
    def place_order(self, user: User, order_type: OrderType, 
                   quantity: int, price: int) -> StockOrder:
        """下單"""
        # 檢查市場是否開放
        if not self.market_state.is_open():
            raise MarketClosedException("Market is closed for trading")
        
        # 檢查交易時段
        if not self.trading_session.is_trading_time():
            raise BusinessRuleException("Not in trading hours", "outside_trading_hours")
        
        # 驗證訂單
        self._validate_order(user, order_type, quantity, price)
        
        # 創建訂單
        order = StockOrder(
            user_id=user.id,
            symbol=self.symbol,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        
        # 處理資源預留
        if order_type == OrderType.BUY:
            self._handle_buy_order_placement(user, order)
        else:
            self._handle_sell_order_placement(user, order)
        
        # 添加到活躍訂單列表
        self.active_orders.append(order)
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
        
        return order
    
    def _validate_order(self, user: User, order_type: OrderType, 
                       quantity: int, price: int) -> None:
        """驗證訂單"""
        if quantity <= 0 or quantity > 1000000:
            raise ValidationException("Invalid quantity", "quantity", quantity)
        
        if price <= 0 or price > 1000000:
            raise ValidationException("Invalid price", "price", price)
        
        # 檢查價格偏差
        if abs(price - self.stock.current_price) / self.stock.current_price > 0.1:
            raise BusinessRuleException("Price deviation too large", "price_deviation")
        
        # 檢查股票可用性
        if not self.stock.is_available():
            raise BusinessRuleException("Stock is not available", "stock_unavailable")
        
        # 訂單類型特定驗證
        if order_type == OrderType.BUY:
            # 檢查用戶餘額
            total_cost = quantity * price
            if not user.has_sufficient_points(total_cost):
                raise InsufficientResourceException(
                    "Insufficient points for buy order",
                    "points", total_cost, user.points
                )
            
            # 檢查股票供應
            if not self.stock.can_buy(quantity):
                raise InsufficientResourceException(
                    "Insufficient shares available",
                    "shares", quantity, self.stock.available_shares
                )
    
    def _handle_buy_order_placement(self, user: User, order: StockOrder) -> None:
        """處理買單下單"""
        # 扣除用戶點數
        total_cost = order.quantity * order.price
        user.deduct_points(total_cost, PointChangeType.TRADING_BUY, 
                          f"Buy order for {order.symbol}")
        
        # 預留股票
        self.stock.reserve_shares(order.quantity)
    
    def _handle_sell_order_placement(self, user: User, order: StockOrder) -> None:
        """處理賣單下單"""
        # 這裡需要檢查用戶持股，但由於聚合邊界，
        # 實際的持股扣除應該在應用服務層處理
        pass
    
    def cancel_order(self, order_id: ObjectId, user: User) -> bool:
        """取消訂單"""
        order = self._find_order_by_id(order_id)
        if not order:
            raise ValidationException("Order not found", "order_id")
        
        if order.user_id != user.id:
            raise BusinessRuleException("Cannot cancel order of another user", "unauthorized")
        
        if not order.is_active():
            raise BusinessRuleException("Order is not active", "order_inactive")
        
        # 取消訂單
        order.cancel_order()
        
        # 釋放資源
        self._release_order_resources(order, user)
        
        # 從活躍訂單中移除
        self.active_orders = [o for o in self.active_orders if o.id != order_id]
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
        
        return True
    
    def _release_order_resources(self, order: StockOrder, user: User) -> None:
        """釋放訂單資源"""
        if order.order_type == OrderType.BUY:
            # 退還點數
            refund_amount = order.remaining_quantity * order.price
            user.add_points(refund_amount, PointChangeType.TRADING_BUY, 
                           "Refund for cancelled buy order")
            
            # 釋放股票
            self.stock.release_shares(order.remaining_quantity)
    
    def execute_trade(self, buy_order: StockOrder, sell_order: StockOrder,
                     match_quantity: int, match_price: int) -> Dict[str, Any]:
        """執行交易"""
        # 驗證交易條件
        if not self.market_state.is_open():
            raise MarketClosedException("Cannot execute trade when market is closed")
        
        if not buy_order.can_match_with(sell_order):
            raise BusinessRuleException("Orders cannot be matched", "orders_incompatible")
        
        if match_quantity > min(buy_order.remaining_quantity, sell_order.remaining_quantity):
            raise BusinessRuleException("Match quantity exceeds available quantity", "excessive_quantity")
        
        # 執行交易
        trade_id = str(ObjectId())
        
        # 更新訂單狀態
        buy_order.fill_order(match_quantity, match_price)
        sell_order.fill_order(match_quantity, match_price)
        
        # 更新股票價格
        self.stock.update_price(match_price, f"Trade execution: {trade_id}")
        
        # 創建交易記錄
        trade_result = {
            "trade_id": trade_id,
            "buy_order_id": str(buy_order.id),
            "sell_order_id": str(sell_order.id),
            "symbol": self.symbol,
            "quantity": match_quantity,
            "price": match_price,
            "total_amount": match_quantity * match_price,
            "buyer_id": str(buy_order.user_id),
            "seller_id": str(sell_order.user_id),
            "executed_at": datetime.utcnow()
        }
        
        # 發布交易執行事件
        self.add_domain_event(TradeExecutedEvent(
            event_id=trade_id,
            occurred_at=datetime.utcnow(),
            trade_id=trade_id,
            buyer_id=str(buy_order.user_id),
            seller_id=str(sell_order.user_id),
            symbol=self.symbol,
            quantity=match_quantity,
            price=match_price,
            total_amount=match_quantity * match_price,
            executed_at=datetime.utcnow()
        ))
        
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
        
        return trade_result
    
    def get_order_book(self) -> OrderBook:
        """獲取訂單簿"""
        buy_orders = [o for o in self.active_orders if o.is_buy_order() and o.is_active()]
        sell_orders = [o for o in self.active_orders if o.is_sell_order() and o.is_active()]
        
        return OrderBook.create(self.symbol, buy_orders, sell_orders)
    
    def get_market_depth(self) -> Dict[str, Any]:
        """獲取市場深度"""
        order_book = self.get_order_book()
        
        return {
            "symbol": self.symbol,
            "buy_depth": order_book.get_buy_depth(),
            "sell_depth": order_book.get_sell_depth(),
            "spread": order_book.get_spread(),
            "market_state": self.market_state.status
        }
    
    def update_stock_price(self, new_price: int, reason: str = "") -> None:
        """更新股票價格"""
        if not self.market_state.is_open():
            raise MarketClosedException("Cannot update price when market is closed")
        
        self.stock.update_price(new_price, reason)
        self.updated_at = datetime.utcnow()
        
        # 增加版本號
        self.increment_version()
    
    def get_trading_statistics(self) -> Dict[str, Any]:
        """獲取交易統計"""
        total_orders = len(self.active_orders)
        buy_orders = len([o for o in self.active_orders if o.is_buy_order()])
        sell_orders = len([o for o in self.active_orders if o.is_sell_order()])
        
        return {
            "symbol": self.symbol,
            "total_orders": total_orders,
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "current_price": self.stock.current_price,
            "available_shares": self.stock.available_shares,
            "total_shares": self.stock.total_shares,
            "market_state": self.market_state.status,
            "trading_session": self.trading_session.get_session_info()
        }
    
    def _find_order_by_id(self, order_id: ObjectId) -> Optional[StockOrder]:
        """根據 ID 查找訂單"""
        for order in self.active_orders:
            if order.id == order_id:
                return order
        return None
    
    def add_active_order(self, order: StockOrder) -> None:
        """添加活躍訂單"""
        if order.symbol != self.symbol:
            raise ValidationException("Order symbol must match aggregate symbol", "symbol")
        
        if order not in self.active_orders:
            self.active_orders.append(order)
            self.updated_at = datetime.utcnow()
    
    def remove_inactive_orders(self) -> List[StockOrder]:
        """移除非活躍訂單"""
        inactive_orders = [o for o in self.active_orders if not o.is_active()]
        self.active_orders = [o for o in self.active_orders if o.is_active()]
        
        if inactive_orders:
            self.updated_at = datetime.utcnow()
        
        return inactive_orders
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "symbol": self.symbol,
            "stock": self.stock.to_dict(),
            "market_state": self.market_state.to_dict(),
            "active_orders": [order.to_dict() for order in self.active_orders],
            "trading_session": self.trading_session.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TradingAggregate:
        """從字典創建聚合"""
        aggregate = cls(
            symbol=data.get("symbol", ""),
            stock=Stock.from_dict(data.get("stock", {})),
            market_state=MarketState.from_dict(data.get("market_state", {})),
            id=data.get("_id")
        )
        
        # 恢復活躍訂單
        active_orders_data = data.get("active_orders", [])
        for order_data in active_orders_data:
            order = StockOrder.from_dict(order_data)
            aggregate.active_orders.append(order)
        
        # 恢復交易時段
        trading_session_data = data.get("trading_session", {})
        if trading_session_data:
            aggregate.trading_session = TradingSession.from_dict(trading_session_data)
        
        aggregate.created_at = data.get("created_at", datetime.utcnow())
        aggregate.updated_at = data.get("updated_at", datetime.utcnow())
        aggregate.version = data.get("version", 1)
        
        return aggregate


class PortfolioAggregate(AggregateRoot):
    """
    投資組合聚合根
    管理用戶的完整投資組合
    """
    
    def __init__(
        self,
        user_id: ObjectId,
        user_stocks: List[UserStock] = None,
        id: Optional[ObjectId] = None
    ):
        super().__init__()
        self.id = id or ObjectId()
        self.user_id = user_id
        self.user_stocks = user_stocks or []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # 驗證聚合一致性
        self._validate_aggregate_consistency()
    
    def _validate_aggregate_consistency(self) -> None:
        """驗證聚合一致性"""
        if not self.user_id:
            raise ValidationException("User ID is required", "user_id")
        
        # 檢查所有持股都屬於同一用戶
        for stock in self.user_stocks:
            if stock.user_id != self.user_id:
                raise ValidationException("All stocks must belong to the same user", "user_stocks")
    
    def add_stock_position(self, symbol: str, quantity: int, price: int) -> UserStock:
        """添加股票持倉"""
        existing_stock = self._find_stock_by_symbol(symbol)
        
        if existing_stock:
            # 更新現有持倉
            existing_stock.add_shares(quantity, price)
            self.updated_at = datetime.utcnow()
            return existing_stock
        else:
            # 創建新持倉
            new_stock = UserStock(
                user_id=self.user_id,
                symbol=symbol,
                quantity=quantity,
                average_price=price
            )
            self.user_stocks.append(new_stock)
            self.updated_at = datetime.utcnow()
            return new_stock
    
    def remove_stock_position(self, symbol: str, quantity: int) -> bool:
        """移除股票持倉"""
        stock = self._find_stock_by_symbol(symbol)
        if not stock:
            return False
        
        success = stock.remove_shares(quantity)
        if success:
            # 如果持倉歸零，從列表中移除
            if stock.quantity == 0:
                self.user_stocks = [s for s in self.user_stocks if s.symbol != symbol]
            
            self.updated_at = datetime.utcnow()
            # 增加版本號
            self.increment_version()
        
        return success
    
    def calculate_portfolio_value(self, stock_prices: Dict[str, int]) -> Dict[str, Any]:
        """計算投資組合價值"""
        total_value = 0
        total_cost = 0
        positions = []
        
        for stock in self.user_stocks:
            if stock.quantity > 0:
                current_price = stock_prices.get(stock.symbol, 0)
                current_value = stock.quantity * current_price
                cost_basis = stock.quantity * stock.average_price
                profit_loss = current_value - cost_basis
                profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
                
                total_value += current_value
                total_cost += cost_basis
                
                positions.append({
                    "symbol": stock.symbol,
                    "quantity": stock.quantity,
                    "average_price": stock.average_price,
                    "current_price": current_price,
                    "cost_basis": cost_basis,
                    "current_value": current_value,
                    "profit_loss": profit_loss,
                    "profit_loss_percentage": profit_loss_pct
                })
        
        total_profit_loss = total_value - total_cost
        total_profit_loss_pct = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "user_id": str(self.user_id),
            "total_value": total_value,
            "total_cost": total_cost,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percentage": total_profit_loss_pct,
            "positions": positions,
            "position_count": len(positions)
        }
    
    def get_diversification_metrics(self) -> Dict[str, Any]:
        """獲取多元化指標"""
        if not self.user_stocks:
            return {
                "concentration_risk": "LOW",
                "diversification_score": 100,
                "position_count": 0,
                "largest_position_ratio": 0
            }
        
        # 計算每個持倉的價值比例
        total_value = sum(stock.quantity * stock.average_price for stock in self.user_stocks)
        
        if total_value == 0:
            return {
                "concentration_risk": "LOW",
                "diversification_score": 100,
                "position_count": 0,
                "largest_position_ratio": 0
            }
        
        position_ratios = []
        for stock in self.user_stocks:
            if stock.quantity > 0:
                ratio = (stock.quantity * stock.average_price) / total_value
                position_ratios.append(ratio)
        
        # 計算最大持倉比例
        max_ratio = max(position_ratios) if position_ratios else 0
        
        # 計算多元化分數
        diversification_score = 100 - (max_ratio * 100)
        
        # 判斷風險等級
        if max_ratio > 0.5:
            risk_level = "HIGH"
        elif max_ratio > 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "concentration_risk": risk_level,
            "diversification_score": diversification_score,
            "position_count": len(position_ratios),
            "largest_position_ratio": max_ratio
        }
    
    def _find_stock_by_symbol(self, symbol: str) -> Optional[UserStock]:
        """根據股票代碼查找持倉"""
        for stock in self.user_stocks:
            if stock.symbol == symbol:
                return stock
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "user_stocks": [stock.to_dict() for stock in self.user_stocks],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PortfolioAggregate:
        """從字典創建聚合"""
        user_stocks = []
        for stock_data in data.get("user_stocks", []):
            user_stocks.append(UserStock.from_dict(stock_data))
        
        aggregate = cls(
            user_id=data.get("user_id"),
            user_stocks=user_stocks,
            id=data.get("_id")
        )
        
        aggregate.created_at = data.get("created_at", datetime.utcnow())
        aggregate.updated_at = data.get("updated_at", datetime.utcnow())
        aggregate.version = data.get("version", 1)
        
        return aggregate