from __future__ import annotations
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

# 依賴注入函數
def get_public_service() -> PublicService:
    """PublicService 的依賴注入函數"""
    return PublicService()

# 公開服務類別
class PublicService:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
    
    # 取得股票價格摘要
    async def get_price_summary(self) -> PriceSummary:
        try:
            # 取得最新成交價格
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "completed"},
                sort=[("created_at", -1)]
            )
            
            # 取得今日所有成交記錄來計算統計資料
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
            
            # 計算統計資料
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
                    stock_value=stock_value
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
    
    # 取得歷史價格資料
    async def get_price_history(self, hours: int = 24) -> List[dict]:
        try:
            from datetime import timedelta
            import random
            
            # 計算時間範圍
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            # 先嘗試從真實交易記錄獲取資料
            trades_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": "completed",
                "created_at": {"$gte": start_time, "$lte": end_time}
            }).sort("created_at", 1)
            
            real_trades = await trades_cursor.to_list(length=None)
            
            # 獲取目前價格
            current_price = await self._get_current_stock_price()
            
            if len(real_trades) >= 10:
                # 如果有足夠的真實交易資料
                history = []
                for trade in real_trades:
                    history.append({
                        "timestamp": trade.get("created_at", end_time).isoformat(),
                        "price": trade.get("price", current_price)
                    })
                return history
            else:
                # 產生模擬歷史資料
                history = []
                data_points = min(hours * 2, 100)  # 每30分鐘一個點，最多100個點
                
                # 基礎價格（目前價格的90%-110%範圍）
                base_price = current_price * (0.9 + random.random() * 0.2)
                
                for i in range(data_points):
                    # 計算時間點
                    time_offset = timedelta(hours=hours) * (i / (data_points - 1))
                    timestamp = start_time + time_offset
                    
                    # 產生價格（漸變到目前價格）
                    progress = i / (data_points - 1)
                    
                    # 隨機波動
                    volatility = (random.random() - 0.5) * 0.05 * current_price  # 5%的波動
                    
                    # 趨勢：逐漸向目前價格靠近
                    trend_price = base_price + (current_price - base_price) * progress
                    
                    # 最終價格
                    price = max(trend_price + volatility, current_price * 0.5)  # 確保不會過低
                    
                    # 最後一個點設為目前價格
                    if i == data_points - 1:
                        price = current_price
                    
                    history.append({
                        "timestamp": timestamp.isoformat(),
                        "price": round(price, 2)
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            # 回傳基本的模擬資料
            current_price = 20.0
            end_time = datetime.now(timezone.utc)
            history = []
            
            for i in range(20):
                timestamp = end_time - timedelta(minutes=i * 30)
                price = current_price + (random.random() - 0.5) * 2
                history.append({
                    "timestamp": timestamp.isoformat(),
                    "price": round(price, 2)
                })
            
            return list(reversed(history))
