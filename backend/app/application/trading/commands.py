"""
Trading Commands
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from bson import ObjectId

from ..common.interfaces import Command


@dataclass
class PlaceOrderCommand(Command):
    """下單命令"""
    symbol: str
    order_type: str  # "buy" or "sell"
    quantity: int
    price: int
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.order_type not in ["buy", "sell"]:
            raise ValueError("Order type must be 'buy' or 'sell'")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")


@dataclass
class CancelOrderCommand(Command):
    """取消訂單命令"""
    order_id: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.order_id:
            raise ValueError("Order ID is required")


@dataclass
class CreateStockCommand(Command):
    """創建股票命令"""
    symbol: str
    name: str
    initial_price: int
    total_shares: int
    available_shares: int
    stock_type: str = "normal"
    min_price: int = 1
    max_price: int = 1000000
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if not self.name:
            raise ValueError("Name is required")
        if self.initial_price <= 0:
            raise ValueError("Initial price must be positive")
        if self.total_shares <= 0:
            raise ValueError("Total shares must be positive")
        if self.available_shares < 0:
            raise ValueError("Available shares cannot be negative")
        if self.available_shares > self.total_shares:
            raise ValueError("Available shares cannot exceed total shares")


@dataclass
class UpdateStockPriceCommand(Command):
    """更新股票價格命令"""
    symbol: str
    new_price: int
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.new_price <= 0:
            raise ValueError("New price must be positive")


@dataclass
class UpdateStockAvailabilityCommand(Command):
    """更新股票可用性命令"""
    symbol: str
    available_shares: int
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.available_shares < 0:
            raise ValueError("Available shares cannot be negative")


@dataclass
class OpenMarketCommand(Command):
    """開市命令"""
    symbol: Optional[str] = None  # None 表示開放所有市場
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class CloseMarketCommand(Command):
    """收市命令"""
    symbol: Optional[str] = None  # None 表示關閉所有市場
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class ExecuteTradeCommand(Command):
    """執行交易命令"""
    buy_order_id: str
    sell_order_id: str
    quantity: int
    price: int
    
    def __post_init__(self):
        super().__post_init__()
        if not self.buy_order_id:
            raise ValueError("Buy order ID is required")
        if not self.sell_order_id:
            raise ValueError("Sell order ID is required")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price <= 0:
            raise ValueError("Price must be positive")


@dataclass
class MatchOrdersCommand(Command):
    """撮合訂單命令"""
    symbol: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")


@dataclass
class BatchMatchOrdersCommand(Command):
    """批量撮合訂單命令"""
    symbols: Optional[list] = None  # None 表示撮合所有股票
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class CreateIPOCommand(Command):
    """創建IPO命令"""
    symbol: str
    name: str
    ipo_price: int
    total_shares: int
    ipo_start_time: datetime
    ipo_end_time: datetime
    allocation_method: str = "fcfs"  # "fcfs" (first-come-first-serve) or "lottery"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if not self.name:
            raise ValueError("Name is required")
        if self.ipo_price <= 0:
            raise ValueError("IPO price must be positive")
        if self.total_shares <= 0:
            raise ValueError("Total shares must be positive")
        if self.ipo_start_time >= self.ipo_end_time:
            raise ValueError("IPO start time must be before end time")
        if self.allocation_method not in ["fcfs", "lottery"]:
            raise ValueError("Allocation method must be 'fcfs' or 'lottery'")


@dataclass
class ParticipateIPOCommand(Command):
    """參與IPO命令"""
    symbol: str
    quantity: int
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")


@dataclass
class ProcessIPOAllocationCommand(Command):
    """處理IPO分配命令"""
    symbol: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")


@dataclass
class SetTradingLimitsCommand(Command):
    """設置交易限制命令"""
    user_id: str
    daily_trade_limit: Optional[int] = None
    position_limit: Optional[int] = None
    price_deviation_limit: Optional[float] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.user_id:
            raise ValueError("User ID is required")
        if self.daily_trade_limit is not None and self.daily_trade_limit < 0:
            raise ValueError("Daily trade limit cannot be negative")
        if self.position_limit is not None and self.position_limit < 0:
            raise ValueError("Position limit cannot be negative")
        if self.price_deviation_limit is not None and (self.price_deviation_limit < 0 or self.price_deviation_limit > 1):
            raise ValueError("Price deviation limit must be between 0 and 1")


@dataclass
class FreezeUserTradingCommand(Command):
    """凍結用戶交易命令"""
    target_user_id: str
    reason: str
    duration_hours: Optional[int] = None  # None 表示永久凍結
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if not self.reason:
            raise ValueError("Reason is required")
        if self.duration_hours is not None and self.duration_hours <= 0:
            raise ValueError("Duration must be positive")


@dataclass
class UnfreezeUserTradingCommand(Command):
    """解凍用戶交易命令"""
    target_user_id: str
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class BulkCancelOrdersCommand(Command):
    """批量取消訂單命令"""
    order_ids: list
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.order_ids:
            raise ValueError("Order IDs list is required")
        if not all(isinstance(order_id, str) for order_id in self.order_ids):
            raise ValueError("All order IDs must be strings")


@dataclass
class ForceClosePositionCommand(Command):
    """強制平倉命令"""
    target_user_id: str
    symbol: str
    quantity: Optional[int] = None  # None 表示全部平倉
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("Quantity must be positive")


@dataclass
class AdjustUserPositionCommand(Command):
    """調整用戶持倉命令"""
    target_user_id: str
    symbol: str
    quantity_change: int  # 正數增加，負數減少
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.quantity_change == 0:
            raise ValueError("Quantity change cannot be zero")


@dataclass
class SetMarketHoursCommand(Command):
    """設置市場時間命令"""
    open_time: str  # HH:MM format
    close_time: str  # HH:MM format
    timezone: str = "Asia/Taipei"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.open_time or not self.close_time:
            raise ValueError("Open time and close time are required")
        # 簡單的時間格式驗證
        try:
            hours, minutes = self.open_time.split(":")
            int(hours), int(minutes)
            hours, minutes = self.close_time.split(":")
            int(hours), int(minutes)
        except (ValueError, IndexError):
            raise ValueError("Time must be in HH:MM format")


@dataclass
class CreateTradingSessionCommand(Command):
    """創建交易時段命令"""
    session_name: str
    start_time: datetime
    end_time: datetime
    allowed_symbols: Optional[list] = None  # None 表示允許所有股票
    
    def __post_init__(self):
        super().__post_init__()
        if not self.session_name:
            raise ValueError("Session name is required")
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")


@dataclass
class EndTradingSessionCommand(Command):
    """結束交易時段命令"""
    session_id: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.session_id:
            raise ValueError("Session ID is required")


@dataclass
class RecalculatePortfolioCommand(Command):
    """重新計算投資組合命令"""
    target_user_id: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GenerateTradingReportCommand(Command):
    """生成交易報告命令"""
    report_type: str  # "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
    include_users: Optional[list] = None
    include_symbols: Optional[list] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.report_type not in ["daily", "weekly", "monthly"]:
            raise ValueError("Report type must be 'daily', 'weekly', or 'monthly'")
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")


@dataclass
class BackupTradingDataCommand(Command):
    """備份交易數據命令"""
    backup_type: str = "full"  # "full", "incremental"
    include_historical: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if self.backup_type not in ["full", "incremental"]:
            raise ValueError("Backup type must be 'full' or 'incremental'")


@dataclass
class RestoreTradingDataCommand(Command):
    """恢復交易數據命令"""
    backup_id: str
    restore_point: datetime
    
    def __post_init__(self):
        super().__post_init__()
        if not self.backup_id:
            raise ValueError("Backup ID is required")