"""
Trading Domain Value Objects
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from enum import Enum
import pytz
from ..common.value_objects import ValueObject


class TradingPairType(Enum):
    """交易對類型"""
    NORMAL = "normal"
    IPO = "ipo"
    SPECIAL = "special"


@dataclass(frozen=True)
class TradingPair(ValueObject):
    """交易對值物件"""
    base_symbol: str
    quote_symbol: str = "POINTS"
    pair_type: TradingPairType = TradingPairType.NORMAL
    
    def __post_init__(self):
        if not self.base_symbol:
            raise ValueError("Base symbol is required")
        if len(self.base_symbol) > 10:
            raise ValueError("Base symbol cannot exceed 10 characters")
        if not self.quote_symbol:
            raise ValueError("Quote symbol is required")
    
    def get_pair_name(self) -> str:
        """獲取交易對名稱"""
        return f"{self.base_symbol}/{self.quote_symbol}"
    
    def is_ipo_pair(self) -> bool:
        """是否為 IPO 交易對"""
        return self.pair_type == TradingPairType.IPO
    
    def is_special_pair(self) -> bool:
        """是否為特殊交易對"""
        return self.pair_type == TradingPairType.SPECIAL


@dataclass(frozen=True)
class PriceLevel(ValueObject):
    """價格檔位值物件"""
    price: int
    quantity: int
    order_count: int = 1
    
    def __post_init__(self):
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if self.order_count < 0:
            raise ValueError("Order count cannot be negative")
    
    def get_total_value(self) -> int:
        """獲取總價值"""
        return self.price * self.quantity
    
    def add_quantity(self, quantity: int) -> PriceLevel:
        """增加數量"""
        if quantity < 0:
            raise ValueError("Cannot add negative quantity")
        return PriceLevel(
            price=self.price,
            quantity=self.quantity + quantity,
            order_count=self.order_count + 1
        )
    
    def remove_quantity(self, quantity: int) -> PriceLevel:
        """移除數量"""
        if quantity < 0:
            raise ValueError("Cannot remove negative quantity")
        if quantity > self.quantity:
            raise ValueError("Cannot remove more than available quantity")
        
        new_quantity = self.quantity - quantity
        new_order_count = max(0, self.order_count - 1)
        
        return PriceLevel(
            price=self.price,
            quantity=new_quantity,
            order_count=new_order_count
        )


@dataclass(frozen=True)
class OrderBook(ValueObject):
    """訂單簿值物件"""
    symbol: str
    buy_levels: List[PriceLevel]
    sell_levels: List[PriceLevel]
    timestamp: datetime
    
    def __post_init__(self):
        if not self.symbol:
            raise ValueError("Symbol is required")
        
        # 驗證買單價格降序排列
        for i in range(len(self.buy_levels) - 1):
            if self.buy_levels[i].price < self.buy_levels[i + 1].price:
                raise ValueError("Buy levels must be sorted in descending price order")
        
        # 驗證賣單價格升序排列
        for i in range(len(self.sell_levels) - 1):
            if self.sell_levels[i].price > self.sell_levels[i + 1].price:
                raise ValueError("Sell levels must be sorted in ascending price order")
    
    def get_best_bid(self) -> Optional[PriceLevel]:
        """獲取最佳買價"""
        return self.buy_levels[0] if self.buy_levels else None
    
    def get_best_ask(self) -> Optional[PriceLevel]:
        """獲取最佳賣價"""
        return self.sell_levels[0] if self.sell_levels else None
    
    def get_spread(self) -> Optional[int]:
        """獲取買賣價差"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return best_ask.price - best_bid.price
        return None
    
    def get_spread_percentage(self) -> Optional[float]:
        """獲取買賣價差百分比"""
        spread = self.get_spread()
        best_bid = self.get_best_bid()
        
        if spread is not None and best_bid:
            return (spread / best_bid.price) * 100
        return None
    
    def get_total_bid_volume(self) -> int:
        """獲取總買單量"""
        return sum(level.quantity for level in self.buy_levels)
    
    def get_total_ask_volume(self) -> int:
        """獲取總賣單量"""
        return sum(level.quantity for level in self.sell_levels)
    
    def get_buy_depth(self, levels: int = 5) -> List[Dict[str, Any]]:
        """獲取買單深度"""
        return [
            {
                "price": level.price,
                "quantity": level.quantity,
                "orders": level.order_count,
                "total_value": level.get_total_value()
            }
            for level in self.buy_levels[:levels]
        ]
    
    def get_sell_depth(self, levels: int = 5) -> List[Dict[str, Any]]:
        """獲取賣單深度"""
        return [
            {
                "price": level.price,
                "quantity": level.quantity,
                "orders": level.order_count,
                "total_value": level.get_total_value()
            }
            for level in self.sell_levels[:levels]
        ]
    
    def is_empty(self) -> bool:
        """訂單簿是否為空"""
        return len(self.buy_levels) == 0 and len(self.sell_levels) == 0
    
    def has_crossing_orders(self) -> bool:
        """是否有交叉訂單"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return best_bid.price >= best_ask.price
        return False
    
    @classmethod
    def create(cls, symbol: str, buy_orders: List, sell_orders: List) -> OrderBook:
        """從訂單列表創建訂單簿"""
        # 聚合買單
        buy_price_map = {}
        for order in buy_orders:
            price = order.price
            if price not in buy_price_map:
                buy_price_map[price] = {"quantity": 0, "count": 0}
            buy_price_map[price]["quantity"] += order.remaining_quantity
            buy_price_map[price]["count"] += 1
        
        # 聚合賣單
        sell_price_map = {}
        for order in sell_orders:
            price = order.price
            if price not in sell_price_map:
                sell_price_map[price] = {"quantity": 0, "count": 0}
            sell_price_map[price]["quantity"] += order.remaining_quantity
            sell_price_map[price]["count"] += 1
        
        # 創建價格檔位
        buy_levels = [
            PriceLevel(price=price, quantity=data["quantity"], order_count=data["count"])
            for price, data in sorted(buy_price_map.items(), reverse=True)
        ]
        
        sell_levels = [
            PriceLevel(price=price, quantity=data["quantity"], order_count=data["count"])
            for price, data in sorted(sell_price_map.items())
        ]
        
        return cls(
            symbol=symbol,
            buy_levels=buy_levels,
            sell_levels=sell_levels,
            timestamp=datetime.utcnow()
        )


class MarketStatus(Enum):
    """市場狀態"""
    CLOSED = "closed"
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    MAINTENANCE = "maintenance"


@dataclass(frozen=True)
class MarketState(ValueObject):
    """市場狀態值物件"""
    status: MarketStatus
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    opened_by: Optional[str] = None
    closed_by: Optional[str] = None
    reason: str = ""
    
    def is_open(self) -> bool:
        """市場是否開放"""
        return self.status == MarketStatus.OPEN
    
    def is_closed(self) -> bool:
        """市場是否關閉"""
        return self.status == MarketStatus.CLOSED
    
    def is_in_maintenance(self) -> bool:
        """市場是否在維護中"""
        return self.status == MarketStatus.MAINTENANCE
    
    def open_market(self, opened_by: str, reason: str = "") -> MarketState:
        """開市"""
        return MarketState(
            status=MarketStatus.OPEN,
            opened_at=datetime.utcnow(),
            closed_at=None,
            opened_by=opened_by,
            closed_by=None,
            reason=reason
        )
    
    def close_market(self, closed_by: str, reason: str = "") -> MarketState:
        """收市"""
        return MarketState(
            status=MarketStatus.CLOSED,
            opened_at=self.opened_at,
            closed_at=datetime.utcnow(),
            opened_by=self.opened_by,
            closed_by=closed_by,
            reason=reason
        )
    
    def enter_maintenance(self, reason: str = "") -> MarketState:
        """進入維護模式"""
        return MarketState(
            status=MarketStatus.MAINTENANCE,
            opened_at=self.opened_at,
            closed_at=self.closed_at,
            opened_by=self.opened_by,
            closed_by=self.closed_by,
            reason=reason
        )
    
    def get_duration(self) -> Optional[int]:
        """獲取開市時長（秒）"""
        if self.opened_at:
            end_time = self.closed_at or datetime.utcnow()
            return int((end_time - self.opened_at).total_seconds())
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "status": self.status.value,
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "opened_by": self.opened_by,
            "closed_by": self.closed_by,
            "reason": self.reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MarketState:
        """從字典創建"""
        return cls(
            status=MarketStatus(data.get("status", "closed")),
            opened_at=data.get("opened_at"),
            closed_at=data.get("closed_at"),
            opened_by=data.get("opened_by"),
            closed_by=data.get("closed_by"),
            reason=data.get("reason", "")
        )


@dataclass(frozen=True)
class TradingHours(ValueObject):
    """交易時間值物件"""
    open_time: time
    close_time: time
    timezone: str = "Asia/Taipei"
    
    def __post_init__(self):
        if not self.open_time or not self.close_time:
            raise ValueError("Open time and close time are required")
        
        if self.open_time >= self.close_time:
            raise ValueError("Open time must be before close time")
        
        # 驗證時區
        try:
            pytz.timezone(self.timezone)
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {self.timezone}")
    
    def is_trading_time(self, check_time: Optional[datetime] = None) -> bool:
        """檢查是否在交易時間內"""
        if not check_time:
            check_time = datetime.now(pytz.timezone(self.timezone))
        
        current_time = check_time.time()
        return self.open_time <= current_time <= self.close_time
    
    def get_next_open_time(self, from_time: Optional[datetime] = None) -> datetime:
        """獲取下一個開市時間"""
        if not from_time:
            from_time = datetime.now(pytz.timezone(self.timezone))
        
        tz = pytz.timezone(self.timezone)
        current_date = from_time.date()
        
        # 嘗試當天的開市時間
        next_open = tz.localize(datetime.combine(current_date, self.open_time))
        
        # 如果當天開市時間已過，則取明天的開市時間
        if next_open <= from_time:
            next_day = current_date.replace(day=current_date.day + 1)
            next_open = tz.localize(datetime.combine(next_day, self.open_time))
        
        return next_open
    
    def get_next_close_time(self, from_time: Optional[datetime] = None) -> datetime:
        """獲取下一個收市時間"""
        if not from_time:
            from_time = datetime.now(pytz.timezone(self.timezone))
        
        tz = pytz.timezone(self.timezone)
        current_date = from_time.date()
        
        # 嘗試當天的收市時間
        next_close = tz.localize(datetime.combine(current_date, self.close_time))
        
        # 如果當天收市時間已過，則取明天的收市時間
        if next_close <= from_time:
            next_day = current_date.replace(day=current_date.day + 1)
            next_close = tz.localize(datetime.combine(next_day, self.close_time))
        
        return next_close
    
    def get_trading_duration(self) -> int:
        """獲取交易時長（秒）"""
        today = datetime.now().date()
        open_dt = datetime.combine(today, self.open_time)
        close_dt = datetime.combine(today, self.close_time)
        return int((close_dt - open_dt).total_seconds())


@dataclass(frozen=True)
class TradingSession(ValueObject):
    """交易時段值物件"""
    session_id: str
    trading_hours: TradingHours
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        if not self.session_id:
            raise ValueError("Session ID is required")
        if not self.trading_hours:
            raise ValueError("Trading hours are required")
        if not self.start_time:
            raise ValueError("Start time is required")
        
        if self.end_time and self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
    
    def is_trading_time(self, check_time: Optional[datetime] = None) -> bool:
        """檢查是否在交易時間內"""
        if not self.is_active:
            return False
        
        if not check_time:
            check_time = datetime.utcnow()
        
        # 檢查是否在時段範圍內
        if check_time < self.start_time:
            return False
        
        if self.end_time and check_time > self.end_time:
            return False
        
        # 檢查是否在交易時間內
        return self.trading_hours.is_trading_time(check_time)
    
    def end_session(self) -> TradingSession:
        """結束交易時段"""
        return TradingSession(
            session_id=self.session_id,
            trading_hours=self.trading_hours,
            start_time=self.start_time,
            end_time=datetime.utcnow(),
            is_active=False
        )
    
    def get_session_duration(self) -> Optional[int]:
        """獲取時段長度（秒）"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return None
    
    def get_remaining_time(self) -> Optional[int]:
        """獲取剩餘時間（秒）"""
        if not self.is_active or not self.end_time:
            return None
        
        now = datetime.utcnow()
        if now >= self.end_time:
            return 0
        
        return int((self.end_time - now).total_seconds())
    
    def get_session_info(self) -> Dict[str, Any]:
        """獲取時段資訊"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "is_active": self.is_active,
            "duration": self.get_session_duration(),
            "remaining_time": self.get_remaining_time(),
            "trading_hours": {
                "open_time": self.trading_hours.open_time.isoformat(),
                "close_time": self.trading_hours.close_time.isoformat(),
                "timezone": self.trading_hours.timezone
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "session_id": self.session_id,
            "trading_hours": {
                "open_time": self.trading_hours.open_time.isoformat(),
                "close_time": self.trading_hours.close_time.isoformat(),
                "timezone": self.trading_hours.timezone
            },
            "start_time": self.start_time,
            "end_time": self.end_time,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TradingSession:
        """從字典創建"""
        trading_hours_data = data.get("trading_hours", {})
        trading_hours = TradingHours(
            open_time=datetime.fromisoformat(trading_hours_data.get("open_time", "09:00:00")).time(),
            close_time=datetime.fromisoformat(trading_hours_data.get("close_time", "16:00:00")).time(),
            timezone=trading_hours_data.get("timezone", "Asia/Taipei")
        )
        
        return cls(
            session_id=data.get("session_id", ""),
            trading_hours=trading_hours,
            start_time=data.get("start_time", datetime.utcnow()),
            end_time=data.get("end_time"),
            is_active=data.get("is_active", True)
        )
    
    @classmethod
    def create_session(cls, session_id: str = None) -> TradingSession:
        """創建新的交易時段"""
        if not session_id:
            from bson import ObjectId
            session_id = str(ObjectId())
        
        # 預設交易時間為台北時間 9:00-16:00
        default_hours = TradingHours(
            open_time=time(9, 0, 0),
            close_time=time(16, 0, 0),
            timezone="Asia/Taipei"
        )
        
        return cls(
            session_id=session_id,
            trading_hours=default_hours,
            start_time=datetime.utcnow(),
            is_active=True
        )


@dataclass(frozen=True)
class TradeExecutionResult(ValueObject):
    """交易執行結果值物件"""
    trade_id: str
    symbol: str
    buyer_id: str
    seller_id: str
    quantity: int
    price: int
    total_amount: int
    buy_order_id: str
    sell_order_id: str
    executed_at: datetime
    execution_type: str = "match"  # match, partial, full
    
    def __post_init__(self):
        if not self.trade_id:
            raise ValueError("Trade ID is required")
        if not self.symbol:
            raise ValueError("Symbol is required")
        if not self.buyer_id or not self.seller_id:
            raise ValueError("Buyer and seller IDs are required")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.total_amount != self.quantity * self.price:
            raise ValueError("Total amount must equal quantity × price")
    
    def is_partial_execution(self) -> bool:
        """是否為部分成交"""
        return self.execution_type == "partial"
    
    def is_full_execution(self) -> bool:
        """是否為完全成交"""
        return self.execution_type == "full"
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """獲取執行摘要"""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "price": self.price,
            "total_amount": self.total_amount,
            "execution_type": self.execution_type,
            "executed_at": self.executed_at
        }


@dataclass(frozen=True)
class PriceMovement(ValueObject):
    """價格變動值物件"""
    symbol: str
    old_price: int
    new_price: int
    change_amount: int
    change_percentage: float
    timestamp: datetime
    
    def __post_init__(self):
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.old_price <= 0 or self.new_price <= 0:
            raise ValueError("Prices must be positive")
        
        # 驗證計算的一致性
        expected_change = self.new_price - self.old_price
        if self.change_amount != expected_change:
            raise ValueError("Change amount calculation is incorrect")
        
        expected_percentage = (expected_change / self.old_price) * 100
        if abs(self.change_percentage - expected_percentage) > 0.01:
            raise ValueError("Change percentage calculation is incorrect")
    
    def is_price_increase(self) -> bool:
        """價格是否上漲"""
        return self.change_amount > 0
    
    def is_price_decrease(self) -> bool:
        """價格是否下跌"""
        return self.change_amount < 0
    
    def is_price_unchanged(self) -> bool:
        """價格是否無變化"""
        return self.change_amount == 0
    
    def get_formatted_change(self) -> str:
        """獲取格式化的變動字符串"""
        sign = "+" if self.change_amount > 0 else ""
        return f"{sign}{self.change_amount} ({sign}{self.change_percentage:.2f}%)"
    
    def is_significant_movement(self, threshold: float = 5.0) -> bool:
        """是否為重大價格變動"""
        return abs(self.change_percentage) >= threshold
    
    @classmethod
    def create(cls, symbol: str, old_price: int, new_price: int, 
               timestamp: Optional[datetime] = None) -> PriceMovement:
        """創建價格變動值物件"""
        if not timestamp:
            timestamp = datetime.utcnow()
        
        change_amount = new_price - old_price
        change_percentage = (change_amount / old_price) * 100 if old_price > 0 else 0
        
        return cls(
            symbol=symbol,
            old_price=old_price,
            new_price=new_price,
            change_amount=change_amount,
            change_percentage=change_percentage,
            timestamp=timestamp
        )