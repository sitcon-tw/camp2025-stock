from fastapi import Depends, HTTPException, status
from app.core.database import get_database, Collections
from app.schemas.public import (
    PriceSummary, PriceDepth, TradeRecord, LeaderboardEntry, 
    MarketStatus, OrderBookEntry, MarketTimeSlot
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from typing import List
import logging

logger = logging.getLogger(__name__)

# 公開服務類
class PublicService:
    def __init__(self, db: AsyncIOMotorDatabase = Depends(get_database)):
        self.db = db
    
    # 取得股票價格摘要
    async def get_price_summary(self) -> PriceSummary:
        try:
            # 取得最新成交價格
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "completed"},
                sort=[("created_at", -1)]
            )
            
            # 取得今日所有成交記錄來計算統計數據
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            trades_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": "completed",
                "created_at": {"$gte": today_start}
            }).sort("created_at", 1)
            
            trades = await trades_cursor.to_list(length=None)
            
            if not trades:
                # 沒有交易記錄，回傳初始值
                return PriceSummary(
                    lastPrice=20.0,
                    change="+0",
                    changePercent="+0.0%",
                    high=20.0,
                    low=20.0,
                    open=20.0,
                    volume=0,
                    limitPercent=20.0
                )
            
            # 計算統計數據
            prices = [trade.get("price", 20.0) for trade in trades]
            volumes = [abs(trade.get("stock_amount", 0)) for trade in trades]
            
            last_price = latest_trade.get("price", 20.0) if latest_trade else 20.0
            open_price = trades[0].get("price", 20.0)
            high_price = max(prices)
            low_price = min(prices)
            total_volume = sum(volumes)
            
            # 計算漲跌
            change = last_price - open_price
            change_percent = (change / open_price * 100) if open_price > 0 else 0
            
            # 取得漲跌限制
            limit_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "trading_limit"}
            )
            limit_percent = limit_config.get("limitPercent", 20.0) if limit_config else 20.0
            
            return PriceSummary(
                lastPrice=last_price,
                change=f"{'+' if change >= 0 else ''}{change:.2f}",
                changePercent=f"{'+' if change_percent >= 0 else ''}{change_percent:.1f}%",
                high=high_price,
                low=low_price,
                open=open_price,
                volume=total_volume,
                limitPercent=limit_percent
            )
            
        except Exception as e:
            logger.error(f"Failed to get price summary: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve price summary"
            )
    
    # 取得五檔報價
    async def get_price_depth(self) -> PriceDepth:
        try:
            # 取得買方掛單（價格從高到低）
            buy_orders_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": "pending",
                "stock_amount": {"$gt": 0}  # 買單
            }).sort("price", -1).limit(5)
            
            # 取得賣方掛單（價格從低到高）
            sell_orders_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": "pending",
                "stock_amount": {"$lt": 0}  # 賣單
            }).sort("price", 1).limit(5)
            
            buy_orders = await buy_orders_cursor.to_list(length=5)
            sell_orders = await sell_orders_cursor.to_list(length=5)
            
            # 聚合相同價格的訂單
            buy_aggregated = {}
            for order in buy_orders:
                price = order.get("price", 0)
                quantity = abs(order.get("stock_amount", 0))
                buy_aggregated[price] = buy_aggregated.get(price, 0) + quantity
            
            sell_aggregated = {}
            for order in sell_orders:
                price = order.get("price", 0)
                quantity = abs(order.get("stock_amount", 0))
                sell_aggregated[price] = sell_aggregated.get(price, 0) + quantity
            
            # 轉換為回應格式
            buy_entries = [
                OrderBookEntry(price=price, quantity=quantity)
                for price, quantity in sorted(buy_aggregated.items(), reverse=True)
            ]
            
            sell_entries = [
                OrderBookEntry(price=price, quantity=quantity)
                for price, quantity in sorted(sell_aggregated.items())
            ]
            
            return PriceDepth(
                buy=buy_entries,
                sell=sell_entries
            )
            
        except Exception as e:
            logger.error(f"Failed to get price depth: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve price depth"
            )
    
    # 取得最近成交記錄
    async def get_recent_trades(self, limit: int = 20) -> List[TradeRecord]:
        try:
            trades_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": "completed"
            }).sort("created_at", -1).limit(limit)
            
            trades = await trades_cursor.to_list(length=limit)
            
            trade_records = []
            for trade in trades:
                trade_records.append(TradeRecord(
                    price=trade.get("price", 0),
                    quantity=abs(trade.get("stock_amount", 0)),
                    timestamp=trade.get("created_at", datetime.now(timezone.utc)).isoformat()
                ))
            
            return trade_records
            
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve recent trades"
            )
    
    # 取得排行榜
    async def get_leaderboard(self) -> List[LeaderboardEntry]:
        try:
            # 取得所有使用者
            users_cursor = self.db[Collections.USERS].find({})
            users = await users_cursor.to_list(length=None)
            
            # 取得目前股票價格
            current_price = await self._get_current_stock_price()
            
            leaderboard = []
            for user in users:
                # 取得使用者持股
                stock_holding = await self.db[Collections.STOCKS].find_one(
                    {"user_id": user["_id"]}
                ) or {"stock_amount": 0}
                
                stocks = stock_holding.get("stock_amount", 0)
                stock_value = stocks * current_price
                
                # 取得使用者所屬隊伍
                team_name = "Unknown"
                if user.get("group_id"):
                    group = await self.db[Collections.GROUPS].find_one(
                        {"_id": user["group_id"]}
                    )
                    team_name = group.get("name", "Unknown") if group else "Unknown"
                
                leaderboard.append(LeaderboardEntry(
                    username=user.get("username", user.get("name", "Unknown")),
                    team=team_name,
                    points=user.get("points", 0),
                    stockValue=stock_value
                ))
            
            # 按總價值排序（點數 + 股票價值）
            leaderboard.sort(
                key=lambda x: x.points + x.stock_value,
                reverse=True
            )
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve leaderboard"
            )
    
    # 取得市場狀態
    async def get_market_status(self) -> MarketStatus:
        try:
            # 取得市場開放時間配置
            market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "market_hours"}
            )
            
            current_time = datetime.now(timezone.utc)
            current_timestamp = int(current_time.timestamp())
            
            # 預設開放時間（如果沒有配置）
            default_open_times = [
                MarketTimeSlot(
                    start=int(current_time.replace(hour=9, minute=0, second=0).timestamp()),
                    end=int(current_time.replace(hour=17, minute=0, second=0).timestamp())
                )
            ]
            
            if market_config and "openTime" in market_config:
                open_times = [
                    MarketTimeSlot(start=slot["start"], end=slot["end"])
                    for slot in market_config["openTime"]
                ]
            else:
                open_times = default_open_times
            
            # 檢查目前是否在開放時間內
            is_open = any(
                slot.start <= current_timestamp <= slot.end
                for slot in open_times
            )
            
            return MarketStatus(
                isOpen=is_open,
                currentTime=current_time.isoformat(),
                openTime=open_times
            )
            
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve market status"
            )
    
    # 取得目前股票價格
    async def _get_current_stock_price(self) -> float:
        try:
            # 從最近的成交記錄取得價格
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "completed"},
                sort=[("created_at", -1)]
            )
            
            if latest_trade:
                return latest_trade.get("price", 20.0)
            
            # 如果沒有成交記錄，從市場配置取得
            price_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "current_price"}
            )
            
            if price_config:
                return price_config.get("price", 20.0)
            
            # 預設價格
            return 20.0
            
        except Exception as e:
            logger.error(f"Failed to get current stock price: {e}")
            return 20.0
