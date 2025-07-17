# 公開API應用服務
# 負責協調公開數據查詢的業務流程

from __future__ import annotations
from typing import List
import logging

from app.core.base_classes import BaseApplicationService
from app.domain.market.data_services import MarketDataDomainService
from app.domain.trading.data_services import TradingDataDomainService
from app.schemas.public import (
    PriceSummary, PriceDepth, TradeRecord, LeaderboardEntry, 
    MarketStatus, TradingHoursResponse, OrderBookEntry, MarketTimeSlot, 
    PublicAnnouncement, MarketPriceInfo
)
from app.infrastructure.cache.cache_service import cached

logger = logging.getLogger(__name__)


class PublicApplicationService(BaseApplicationService):
    """
    公開API應用服務
    SRP 原則：專注於公開數據查詢的應用邏輯
    """
    
    def __init__(
        self, 
        market_data_service: MarketDataDomainService,
        trading_data_service: TradingDataDomainService
    ):
        super().__init__("PublicApplicationService")
        self.market_data_service = market_data_service
        self.trading_data_service = trading_data_service
    
    @cached(ttl=5, key_prefix="price")
    async def get_price_summary(self) -> PriceSummary:
        """
        取得股票價格摘要用例
        Clean Code 原則：將複雜業務邏輯委託給領域服務
        """
        try:
            # 委託給領域服務處理業務邏輯
            price_data = await self.market_data_service.calculate_price_summary()
            
            return PriceSummary(
                lastPrice=price_data["last_price"],
                averagePrice=price_data["average_price"],
                change=price_data["change_display"],
                changePercent=price_data["change_percent_display"],
                high=price_data["high_price"],
                low=price_data["low_price"],
                open=price_data["open_price"],
                volume=price_data["total_volume"],
                limitPercent=price_data["limit_percent"]
            )
        except Exception as e:
            logger.error(f"Failed to get price summary: {e}")
            # 回傳預設值避免API失敗
            return PriceSummary(
                lastPrice=20,
                averagePrice=20,
                change="+0",
                changePercent="+0.0%",
                high=20,
                low=20,
                open=20,
                volume=0,
                limitPercent=2000
            )
    
    @cached(ttl=10, key_prefix="price_depth")
    async def get_price_depth(self) -> PriceDepth:
        """取得價格深度用例"""
        try:
            depth_data = await self.trading_data_service.get_order_book_depth()
            
            return PriceDepth(
                buyOrders=[
                    OrderBookEntry(price=order["price"], quantity=order["quantity"])
                    for order in depth_data["buy_orders"]
                ],
                sellOrders=[
                    OrderBookEntry(price=order["price"], quantity=order["quantity"])
                    for order in depth_data["sell_orders"]
                ]
            )
        except Exception as e:
            logger.error(f"Failed to get price depth: {e}")
            return PriceDepth(buyOrders=[], sellOrders=[])
    
    @cached(ttl=10, key_prefix="trade_records")
    async def get_trade_records(self, limit: int = 20) -> List[TradeRecord]:
        """取得交易記錄用例"""
        try:
            trades_data = await self.trading_data_service.get_recent_trades(limit)
            
            return [
                TradeRecord(
                    price=trade["price"],
                    quantity=trade["quantity"],
                    timestamp=trade["timestamp"],
                    side=trade["side"]
                )
                for trade in trades_data
            ]
        except Exception as e:
            logger.error(f"Failed to get trade records: {e}")
            return []
    
    @cached(ttl=30, key_prefix="leaderboard")
    async def get_leaderboard(self) -> List[LeaderboardEntry]:
        """取得排行榜用例"""
        try:
            leaderboard_data = await self.market_data_service.calculate_user_rankings()
            
            return [
                LeaderboardEntry(
                    rank=entry["rank"],
                    username=entry["username"],
                    totalValue=entry["total_value"],
                    points=entry["points"],
                    stockValue=entry["stock_value"],
                    team=entry["team"]
                )
                for entry in leaderboard_data
            ]
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return []
    
    @cached(ttl=60, key_prefix="market_status")
    async def get_market_status(self) -> MarketStatus:
        """取得市場狀態用例"""
        try:
            status_data = await self.market_data_service.get_market_status()
            
            return MarketStatus(
                isOpen=status_data["is_open"],
                message=status_data["status_message"],
                nextOpenTime=status_data.get("next_open_time"),
                nextCloseTime=status_data.get("next_close_time")
            )
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return MarketStatus(
                isOpen=False,
                message="市場狀態查詢失敗",
                nextOpenTime=None,
                nextCloseTime=None
            )
    
    @cached(ttl=300, key_prefix="trading_hours")
    async def get_trading_hours(self) -> TradingHoursResponse:
        """取得交易時間設定用例"""
        try:
            hours_data = await self.market_data_service.get_trading_hours()
            
            return TradingHoursResponse(
                tradingHours=[
                    MarketTimeSlot(
                        start=slot["start"],
                        end=slot["end"],
                        timezone=slot.get("timezone", "Asia/Taipei")
                    )
                    for slot in hours_data["trading_hours"]
                ],
                timezone=hours_data.get("timezone", "Asia/Taipei")
            )
        except Exception as e:
            logger.error(f"Failed to get trading hours: {e}")
            return TradingHoursResponse(tradingHours=[], timezone="Asia/Taipei")
    
    @cached(ttl=60, key_prefix="announcements")
    async def get_public_announcements(self) -> List[PublicAnnouncement]:
        """取得公開公告用例"""
        try:
            announcements_data = await self.market_data_service.get_public_announcements()
            
            return [
                PublicAnnouncement(
                    id=announcement["id"],
                    title=announcement["title"],
                    message=announcement["message"],
                    createdAt=announcement["created_at"],
                    priority=announcement.get("priority", "normal")
                )
                for announcement in announcements_data
            ]
        except Exception as e:
            logger.error(f"Failed to get public announcements: {e}")
            return []
    
    @cached(ttl=5, key_prefix="market_price_info")
    async def get_market_price_info(self) -> MarketPriceInfo:
        """取得市場價格資訊用例"""
        try:
            price_info = await self.market_data_service.get_comprehensive_price_info()
            
            return MarketPriceInfo(
                currentPrice=price_info["current_price"],
                openPrice=price_info["open_price"],
                highPrice=price_info["high_price"],
                lowPrice=price_info["low_price"],
                volume=price_info["volume"],
                turnover=price_info["turnover"],
                changeAmount=price_info["change_amount"],
                changePercent=price_info["change_percent"],
                limitUp=price_info["limit_up"],
                limitDown=price_info["limit_down"],
                lastUpdateTime=price_info["last_update_time"]
            )
        except Exception as e:
            logger.error(f"Failed to get market price info: {e}")
            # 回傳預設值
            return MarketPriceInfo(
                currentPrice=20,
                openPrice=20,
                highPrice=20,
                lowPrice=20,
                volume=0,
                turnover=0,
                changeAmount=0,
                changePercent=0.0,
                limitUp=24,
                limitDown=16,
                lastUpdateTime=None
            )