# 交易數據領域服務
# 負責交易數據相關的業務邏輯

from __future__ import annotations
from typing import List, Dict, Any
import logging

from ..common.exceptions import DomainException
from .repositories import TradeRepository, OrderRepository

logger = logging.getLogger(__name__)


class TradingDataDomainService:
    """交易數據領域服務 - 處理交易數據查詢和分析"""
    
    def __init__(
        self,
        trade_repository: TradeRepository,
        order_repository: OrderRepository
    ):
        self.trade_repository = trade_repository
        self.order_repository = order_repository

    async def get_order_book_depth(self) -> Dict[str, Any]:
        """
        取得訂單簿深度
        領域邏輯：聚合買賣訂單並按價格分組
        """
        try:
            # 取得活躍的買單和賣單
            active_orders = await self.order_repository.find_active_orders()
            
            buy_orders = []
            sell_orders = []
            
            # 分離買單和賣單
            for order in active_orders:
                if order.get("side") == "buy":
                    buy_orders.append({
                        "price": order.get("price", 0),
                        "quantity": order.get("quantity", 0)
                    })
                elif order.get("side") == "sell":
                    sell_orders.append({
                        "price": order.get("price", 0),
                        "quantity": order.get("quantity", 0)
                    })
            
            # 按價格聚合同價位的訂單
            buy_depth = self._aggregate_orders_by_price(buy_orders, reverse=True)
            sell_depth = self._aggregate_orders_by_price(sell_orders, reverse=False)
            
            return {
                "buy_orders": buy_depth[:10],  # 顯示前10檔
                "sell_orders": sell_depth[:10]
            }
        except Exception as e:
            logger.error(f"Failed to get order book depth: {e}")
            raise DomainException(f"取得訂單簿深度失敗: {str(e)}")

    async def get_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        取得最近交易記錄
        領域邏輯：格式化交易數據供公開顯示
        """
        try:
            trades = await self.trade_repository.find_recent_trades(limit)
            
            formatted_trades = []
            for trade in trades:
                formatted_trades.append({
                    "price": trade.get("price", 0),
                    "quantity": trade.get("quantity", 0),
                    "timestamp": trade.get("timestamp"),
                    "side": self._determine_trade_side(trade)
                })
            
            return formatted_trades
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}")
            raise DomainException(f"取得最近交易記錄失敗: {str(e)}")

    async def calculate_volume_statistics(self) -> Dict[str, Any]:
        """
        計算成交量統計
        領域邏輯：分析交易活動並提供統計數據
        """
        try:
            from datetime import datetime, timezone, timedelta
            
            # 取得今日交易
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_trades = await self.trade_repository.find_trades_after(today_start)
            
            # 取得本週交易
            week_start = today_start - timedelta(days=7)
            week_trades = await self.trade_repository.find_trades_after(week_start)
            
            # 計算統計
            today_volume = sum(trade.get("quantity", 0) for trade in today_trades)
            today_turnover = sum(trade.get("price", 0) * trade.get("quantity", 0) for trade in today_trades)
            
            week_volume = sum(trade.get("quantity", 0) for trade in week_trades)
            week_turnover = sum(trade.get("price", 0) * trade.get("quantity", 0) for trade in week_trades)
            
            return {
                "today_volume": today_volume,
                "today_turnover": today_turnover,
                "today_trades_count": len(today_trades),
                "week_volume": week_volume,
                "week_turnover": week_turnover,
                "week_trades_count": len(week_trades)
            }
        except Exception as e:
            logger.error(f"Failed to calculate volume statistics: {e}")
            raise DomainException(f"計算成交量統計失敗: {str(e)}")

    def _aggregate_orders_by_price(self, orders: List[Dict[str, Any]], reverse: bool = False) -> List[Dict[str, Any]]:
        """
        按價格聚合訂單
        領域邏輯：將同一價格的訂單數量合併
        """
        price_map = {}
        
        for order in orders:
            price = order["price"]
            quantity = order["quantity"]
            
            if price in price_map:
                price_map[price] += quantity
            else:
                price_map[price] = quantity
        
        # 轉換為列表並排序
        aggregated = [
            {"price": price, "quantity": quantity}
            for price, quantity in price_map.items()
        ]
        
        # 排序：買單按價格降序，賣單按價格升序
        aggregated.sort(key=lambda x: x["price"], reverse=reverse)
        
        return aggregated

    def _determine_trade_side(self, trade: Dict[str, Any]) -> str:
        """
        判斷交易方向
        領域邏輯：根據交易數據判斷是買入還是賣出
        """
        # 這裡可以根據交易數據的特定字段來判斷
        # 暫時根據數量的正負來判斷
        quantity = trade.get("quantity", 0)
        if quantity > 0:
            return "buy"
        elif quantity < 0:
            return "sell"
        else:
            return "unknown"