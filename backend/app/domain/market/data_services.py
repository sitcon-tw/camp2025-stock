# 市場數據領域服務
# 負責市場數據相關的業務邏輯

from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging
from bson import ObjectId

from ..common.exceptions import DomainException
from .repositories import MarketConfigRepository
from ..trading.repositories import TradeRepository, OrderRepository
from ..user.repositories import UserRepository
from ..trading.repositories import StockRepository

logger = logging.getLogger(__name__)


class MarketDataDomainService:
    """市場數據領域服務 - 處理市場數據計算和聚合"""
    
    def __init__(
        self,
        market_config_repository: MarketConfigRepository,
        trade_repository: TradeRepository,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        stock_repository: StockRepository
    ):
        self.market_config_repository = market_config_repository
        self.trade_repository = trade_repository
        self.order_repository = order_repository
        self.user_repository = user_repository
        self.stock_repository = stock_repository

    async def calculate_price_summary(self) -> Dict[str, Any]:
        """
        計算價格摘要
        領域邏輯：整合各種價格數據並計算統計指標
        """
        try:
            # 取得平均價格
            average_price = await self._get_current_average_price()
            
            # 取得最新成交價
            last_price = await self._get_latest_trade_price(average_price)
            
            # 取得今日交易統計
            today_stats = await self._calculate_daily_statistics()
            
            # 計算漲跌
            open_price = today_stats.get("open_price", last_price)
            change = last_price - open_price
            change_percent = (change / open_price * 100) if open_price > 0 else 0
            
            # 取得漲跌限制
            limit_percent = await self._get_trading_limit_percent()
            
            return {
                "last_price": last_price,
                "average_price": average_price,
                "change_display": f"{'+' if change >= 0 else ''}{change:+.0f}",
                "change_percent_display": f"{'+' if change_percent >= 0 else ''}{change_percent:+.1f}%",
                "high_price": today_stats.get("high_price", last_price),
                "low_price": today_stats.get("low_price", last_price),
                "open_price": open_price,
                "total_volume": today_stats.get("total_volume", 0),
                "limit_percent": limit_percent
            }
        except Exception as e:
            logger.error(f"Failed to calculate price summary: {e}")
            raise DomainException(f"計算價格摘要失敗: {str(e)}")

    async def get_market_status(self) -> Dict[str, Any]:
        """取得市場狀態"""
        try:
            # 檢查手動控制
            is_open = await self._check_market_open_status()
            
            if is_open:
                status_message = "市場開放中"
                next_close_time = await self._get_next_close_time()
                next_open_time = None
            else:
                status_message = "市場關閉中"
                next_open_time = await self._get_next_open_time()
                next_close_time = None
            
            return {
                "is_open": is_open,
                "status_message": status_message,
                "next_open_time": next_open_time,
                "next_close_time": next_close_time
            }
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            raise DomainException(f"取得市場狀態失敗: {str(e)}")

    async def get_trading_hours(self) -> Dict[str, Any]:
        """取得交易時間設定"""
        try:
            trading_hours = await self.market_config_repository.get_trading_hours()
            return {
                "trading_hours": trading_hours or [],
                "timezone": "Asia/Taipei"
            }
        except Exception as e:
            logger.error(f"Failed to get trading hours: {e}")
            raise DomainException(f"取得交易時間失敗: {str(e)}")

    async def calculate_user_rankings(self) -> List[Dict[str, Any]]:
        """
        計算使用者排行榜
        領域邏輯：根據總資產價值排序使用者
        """
        try:
            users = await self.user_repository.find_all()
            current_price = await self._get_current_average_price()
            
            rankings = []
            for user in users:
                # 取得股票持有
                stock_holding = await self.stock_repository.find_by_user_id(user.id)
                stock_amount = stock_holding.stock_amount if stock_holding else 0
                stock_value = stock_amount * current_price
                total_value = user.points + stock_value
                
                rankings.append({
                    "username": user.name or "未知使用者",
                    "total_value": total_value,
                    "points": user.points,
                    "stock_value": stock_value,
                    "team": user.team or "無隊伍"
                })
            
            # 按總資產排序
            rankings.sort(key=lambda x: x["total_value"], reverse=True)
            
            # 加入排名
            for i, entry in enumerate(rankings, 1):
                entry["rank"] = i
            
            return rankings[:50]  # 回傳前50名
            
        except Exception as e:
            logger.error(f"Failed to calculate user rankings: {e}")
            raise DomainException(f"計算排行榜失敗: {str(e)}")

    async def get_public_announcements(self) -> List[Dict[str, Any]]:
        """取得公開公告"""
        try:
            # 這裡應該從公告repository取得資料
            # 暫時回傳空列表，等後續實現AnnouncementRepository
            return []
        except Exception as e:
            logger.error(f"Failed to get public announcements: {e}")
            raise DomainException(f"取得公開公告失敗: {str(e)}")

    async def get_comprehensive_price_info(self) -> Dict[str, Any]:
        """取得綜合價格資訊"""
        try:
            current_price = await self._get_current_average_price()
            latest_price = await self._get_latest_trade_price(current_price)
            daily_stats = await self._calculate_daily_statistics()
            limit_percent = await self._get_trading_limit_percent()
            
            # 計算漲跌限制價格
            limit_up = int(current_price * (1 + limit_percent / 10000))
            limit_down = int(current_price * (1 - limit_percent / 10000))
            
            open_price = daily_stats.get("open_price", current_price)
            change_amount = latest_price - open_price
            change_percent = (change_amount / open_price * 100) if open_price > 0 else 0
            
            return {
                "current_price": latest_price,
                "open_price": open_price,
                "high_price": daily_stats.get("high_price", latest_price),
                "low_price": daily_stats.get("low_price", latest_price),
                "volume": daily_stats.get("total_volume", 0),
                "turnover": daily_stats.get("total_turnover", 0),
                "change_amount": change_amount,
                "change_percent": change_percent,
                "limit_up": limit_up,
                "limit_down": limit_down,
                "last_update_time": datetime.now(timezone.utc)
            }
        except Exception as e:
            logger.error(f"Failed to get comprehensive price info: {e}")
            raise DomainException(f"取得綜合價格資訊失敗: {str(e)}")

    # 私有輔助方法

    async def _get_current_average_price(self) -> int:
        """取得目前平均價格"""
        try:
            # 取得最近5筆成交的平均價格
            recent_trades = await self.trade_repository.find_recent_trades(5)
            if not recent_trades:
                return 20  # 預設價格
            
            total_price = sum(trade["price"] for trade in recent_trades)
            return int(total_price / len(recent_trades))
        except Exception:
            return 20

    async def _get_latest_trade_price(self, fallback_price: int) -> int:
        """取得最新成交價格"""
        try:
            latest_trades = await self.trade_repository.find_recent_trades(1)
            if latest_trades:
                return latest_trades[0]["price"]
            return fallback_price
        except Exception:
            return fallback_price

    async def _calculate_daily_statistics(self) -> Dict[str, Any]:
        """計算當日交易統計"""
        try:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            daily_trades = await self.trade_repository.find_trades_after(today_start)
            
            if not daily_trades:
                return {
                    "open_price": 20,
                    "high_price": 20,
                    "low_price": 20,
                    "total_volume": 0,
                    "total_turnover": 0
                }
            
            prices = [trade["price"] for trade in daily_trades]
            volumes = [trade["quantity"] for trade in daily_trades]
            
            return {
                "open_price": daily_trades[0]["price"] if daily_trades else 20,
                "high_price": max(prices),
                "low_price": min(prices),
                "total_volume": sum(volumes),
                "total_turnover": sum(trade["price"] * trade["quantity"] for trade in daily_trades)
            }
        except Exception:
            return {
                "open_price": 20,
                "high_price": 20,
                "low_price": 20,
                "total_volume": 0,
                "total_turnover": 0
            }

    async def _get_trading_limit_percent(self) -> int:
        """取得交易限制百分比 (basis points)"""
        try:
            limit_config = await self.market_config_repository.get_trading_limit()
            return limit_config.get("limit_percent", 2000)  # 預設20%
        except Exception:
            return 2000

    async def _check_market_open_status(self) -> bool:
        """檢查市場開放狀態"""
        try:
            # 先檢查手動控制
            manual_control = await self.market_config_repository.get_manual_control()
            if manual_control:
                return manual_control.get("is_open", False)
            
            # 檢查交易時間
            trading_hours = await self.market_config_repository.get_trading_hours()
            if not trading_hours:
                return False
            
            now = datetime.now(timezone.utc)
            # 簡化邏輯，實際實現需要更複雜的時間比較
            return True  # 暫時回傳True
        except Exception:
            return False

    async def _get_next_open_time(self) -> Optional[datetime]:
        """取得下次開市時間"""
        # 這裡需要實現複雜的時間計算邏輯
        return None

    async def _get_next_close_time(self) -> Optional[datetime]:
        """取得下次收市時間"""
        # 這裡需要實現複雜的時間計算邏輯
        return None