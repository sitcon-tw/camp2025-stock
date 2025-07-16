"""
Trading Queries
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..common.interfaces import Query


@dataclass
class GetOrderBookQuery(Query):
    """獲取訂單簿查詢"""
    symbol: str
    depth: int = 10
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.depth <= 0 or self.depth > 50:
            raise ValueError("Depth must be between 1 and 50")


@dataclass
class GetUserOrdersQuery(Query):
    """獲取用戶訂單查詢"""
    target_user_id: str
    symbol: Optional[str] = None
    status: Optional[str] = None  # "pending", "filled", "cancelled"
    order_type: Optional[str] = None  # "buy", "sell"
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 500:
            raise ValueError("Limit must be between 1 and 500")
        if self.status and self.status not in ["pending", "filled", "cancelled", "partial_filled"]:
            raise ValueError("Invalid status")
        if self.order_type and self.order_type not in ["buy", "sell"]:
            raise ValueError("Invalid order type")


@dataclass
class GetStockQuery(Query):
    """獲取股票查詢"""
    symbol: str
    include_stats: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")


@dataclass
class GetStocksListQuery(Query):
    """獲取股票列表查詢"""
    stock_type: Optional[str] = None  # "normal", "ipo", "special"
    active_only: bool = True
    search_term: Optional[str] = None
    sort_by: str = "symbol"
    sort_order: str = "asc"
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 200:
            raise ValueError("Limit must be between 1 and 200")
        if self.sort_by not in ["symbol", "name", "current_price", "volume", "market_cap"]:
            raise ValueError("Invalid sort field")
        if self.sort_order not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        if self.stock_type and self.stock_type not in ["normal", "ipo", "special"]:
            raise ValueError("Invalid stock type")


@dataclass
class GetUserPortfolioQuery(Query):
    """獲取用戶投資組合查詢"""
    target_user_id: str
    include_history: bool = False
    include_profit_loss: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetTradingHistoryQuery(Query):
    """獲取交易歷史查詢"""
    target_user_id: Optional[str] = None
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    trade_type: Optional[str] = None  # "buy", "sell"
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 500:
            raise ValueError("Limit must be between 1 and 500")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")
        if self.trade_type and self.trade_type not in ["buy", "sell"]:
            raise ValueError("Invalid trade type")


@dataclass
class GetMarketStatisticsQuery(Query):
    """獲取市場統計查詢"""
    period: str = "today"  # "today", "week", "month", "year", "all"
    include_volume: bool = True
    include_turnover: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        if self.period not in ["today", "week", "month", "year", "all"]:
            raise ValueError("Invalid period")


@dataclass
class GetStockStatisticsQuery(Query):
    """獲取股票統計查詢"""
    symbol: str
    period: str = "today"  # "today", "week", "month", "year", "all"
    include_price_history: bool = False
    include_volume_history: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.period not in ["today", "week", "month", "year", "all"]:
            raise ValueError("Invalid period")


@dataclass
class GetTradingRankingQuery(Query):
    """獲取交易排名查詢"""
    ranking_type: str = "profit"  # "profit", "volume", "trades"
    period: str = "today"  # "today", "week", "month", "year", "all"
    limit: int = 50
    
    def __post_init__(self):
        super().__post_init__()
        if self.ranking_type not in ["profit", "volume", "trades"]:
            raise ValueError("Invalid ranking type")
        if self.period not in ["today", "week", "month", "year", "all"]:
            raise ValueError("Invalid period")
        if self.limit <= 0 or self.limit > 200:
            raise ValueError("Limit must be between 1 and 200")


@dataclass
class GetOrderQuery(Query):
    """獲取訂單查詢"""
    order_id: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.order_id:
            raise ValueError("Order ID is required")


@dataclass
class GetActiveOrdersQuery(Query):
    """獲取活躍訂單查詢"""
    symbol: Optional[str] = None
    order_type: Optional[str] = None  # "buy", "sell"
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 500:
            raise ValueError("Limit must be between 1 and 500")
        if self.order_type and self.order_type not in ["buy", "sell"]:
            raise ValueError("Invalid order type")


@dataclass
class GetMarketDepthQuery(Query):
    """獲取市場深度查詢"""
    symbol: str
    levels: int = 5
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.levels <= 0 or self.levels > 20:
            raise ValueError("Levels must be between 1 and 20")


@dataclass
class GetPriceHistoryQuery(Query):
    """獲取價格歷史查詢"""
    symbol: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    interval: str = "1h"  # "1m", "5m", "15m", "1h", "1d"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")
        if self.interval not in ["1m", "5m", "15m", "1h", "1d"]:
            raise ValueError("Invalid interval")


@dataclass
class GetVolumeAnalysisQuery(Query):
    """獲取成交量分析查詢"""
    symbol: str
    period: str = "today"  # "today", "week", "month"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.period not in ["today", "week", "month"]:
            raise ValueError("Invalid period")


@dataclass
class GetUserTradingStatsQuery(Query):
    """獲取用戶交易統計查詢"""
    target_user_id: str
    period: str = "all"  # "today", "week", "month", "year", "all"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")
        if self.period not in ["today", "week", "month", "year", "all"]:
            raise ValueError("Invalid period")


@dataclass
class GetIPOListQuery(Query):
    """獲取IPO列表查詢"""
    status: Optional[str] = None  # "upcoming", "active", "completed"
    skip: int = 0
    limit: int = 50
    
    def __post_init__(self):
        super().__post_init__()
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        if self.status and self.status not in ["upcoming", "active", "completed"]:
            raise ValueError("Invalid status")


@dataclass
class GetIPODetailsQuery(Query):
    """獲取IPO詳情查詢"""
    symbol: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")


@dataclass
class GetUserIPOParticipationQuery(Query):
    """獲取用戶IPO參與查詢"""
    target_user_id: str
    symbol: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetTradingSessionsQuery(Query):
    """獲取交易時段查詢"""
    active_only: bool = True
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class GetCurrentTradingSessionQuery(Query):
    """獲取當前交易時段查詢"""
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class GetMarketStatusQuery(Query):
    """獲取市場狀態查詢"""
    symbol: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class GetTradingLimitsQuery(Query):
    """獲取交易限制查詢"""
    target_user_id: str
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetRiskMetricsQuery(Query):
    """獲取風險指標查詢"""
    target_user_id: str
    symbol: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.target_user_id:
            raise ValueError("Target user ID is required")


@dataclass
class GetLiquidityAnalysisQuery(Query):
    """獲取流動性分析查詢"""
    symbol: str
    period: str = "today"  # "today", "week", "month"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.period not in ["today", "week", "month"]:
            raise ValueError("Invalid period")


@dataclass
class GetVolatilityAnalysisQuery(Query):
    """獲取波動性分析查詢"""
    symbol: str
    period: str = "month"  # "week", "month", "quarter", "year"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.period not in ["week", "month", "quarter", "year"]:
            raise ValueError("Invalid period")


@dataclass
class GetCorrelationAnalysisQuery(Query):
    """獲取相關性分析查詢"""
    symbols: List[str]
    period: str = "month"  # "week", "month", "quarter", "year"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.symbols or len(self.symbols) < 2:
            raise ValueError("At least 2 symbols are required")
        if len(self.symbols) > 10:
            raise ValueError("Maximum 10 symbols allowed")
        if self.period not in ["week", "month", "quarter", "year"]:
            raise ValueError("Invalid period")


@dataclass
class GetBacktestResultsQuery(Query):
    """獲取回測結果查詢"""
    strategy_id: str
    symbol: str
    start_date: datetime
    end_date: datetime
    
    def __post_init__(self):
        super().__post_init__()
        if not self.strategy_id:
            raise ValueError("Strategy ID is required")
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")


@dataclass
class GetSystemHealthQuery(Query):
    """獲取系統健康狀態查詢"""
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class GetTradingPerformanceQuery(Query):
    """獲取交易性能查詢"""
    period: str = "today"  # "today", "week", "month"
    
    def __post_init__(self):
        super().__post_init__()
        if self.period not in ["today", "week", "month"]:
            raise ValueError("Invalid period")


@dataclass
class GetAuditLogQuery(Query):
    """獲取審計日誌查詢"""
    action_type: Optional[str] = None
    target_user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
    
    def __post_init__(self):
        super().__post_init__()
        if self.skip < 0:
            raise ValueError("Skip cannot be negative")
        if self.limit <= 0 or self.limit > 500:
            raise ValueError("Limit must be between 1 and 500")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")