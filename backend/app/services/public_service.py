from __future__ import annotations
from fastapi import Depends, HTTPException, status
from app.core.database import get_database, Collections
from app.schemas.public import (
    PriceSummary, PriceDepth, TradeRecord, LeaderboardEntry, 
    MarketStatus, TradingHoursResponse, OrderBookEntry, MarketTimeSlot, PublicAnnouncement,
    MarketPriceInfo
)
from app.services.cache_service import cached, get_cache_service, CacheKeys
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
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
    @cached(ttl=5, key_prefix="price")
    async def get_price_summary(self) -> PriceSummary:
        try:
            # 取得近5筆平均價格
            average_price = await self._get_current_stock_price()
            
            # 取得最後一筆成交的即時價格（按成交時間排序）
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "filled"},
                sort=[("filled_at", -1), ("created_at", -1)]
            )
            
            # 即時價格 = 最後一筆成交價，優先使用 price，如果沒有則使用 filled_price
            # 解釋：
            # 如果沒有成交記錄，則使用平均價格作為即時價格
            # 如果有成交記錄，則使用最後一筆成交的價格
            # 如果沒有 price，則使用 filled_price，如果兩者都沒有，則使用 average_price
            # filled_price: 是在成交時的價格，可能會有延遲
            # average_price: 是近5筆成交的平均價格
            
            
            if latest_trade:
                last_price = latest_trade.get("price")
                if last_price is None:
                    last_price = latest_trade.get("filled_price", average_price)
                logger.debug(f"Latest trade: price={latest_trade.get('price')}, filled_price={latest_trade.get('filled_price')}, final_last_price={last_price}")
            else:
                last_price = average_price
                logger.debug(f"No latest trade found, using average_price={average_price}")
            
            # 取得今日所有成交記錄來計算統計資料
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            trades_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": "filled",
                "created_at": {"$gte": today_start}
            }).sort("created_at", 1)
            
            trades = await trades_cursor.to_list(length=None)
            
            if not trades:
                # 沒有交易記錄，回傳初始值
                return PriceSummary(
                    lastPrice=last_price,
                    averagePrice=average_price,
                    change="+0",
                    changePercent="+0.0%",
                    high=last_price,
                    low=last_price,
                    open=last_price,
                    volume=0,
                    limitPercent=2000  # 20% = 2000 basis points
                )
            
            # 計算統計資料（價格以元為單位）
            prices = [trade.get("price", 20) for trade in trades if trade.get("price") is not None]
            volumes = [abs(trade.get("stock_amount", 0)) for trade in trades]
            
            open_price = next((trade.get("price", 20) for trade in trades if trade.get("price") is not None), 20)
            high_price = max(prices) if prices else last_price
            low_price = min(prices) if prices else last_price
            total_volume = sum(volumes)
            
            # 計算漲跌（基於即時價格和開盤價）
            change = last_price - open_price
            change_percent = (change / open_price * 100) if open_price > 0 else 0
            
            # 取得漲跌限制（以 basis points 為單位）
            limit_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "trading_limit"}
            )
            limit_percent = limit_config.get("limitPercent", 2000) if limit_config else 2000
            
            return PriceSummary(
                lastPrice=last_price,
                averagePrice=average_price,
                change=f"{'+' if change >= 0 else ''}{change}",
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
    @cached(ttl=2, key_prefix="price")
    async def get_price_depth(self) -> PriceDepth:
        try:
            # 取得買方掛單（價格從高到低）
            # 修復：應該查詢所有等待撮合的狀態，並使用 side 欄位判斷買賣方向
            buy_orders_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": {"$in": ["pending", "partial", "pending_limit"]},
                "side": "buy",  # 使用 side 欄位而不是 stock_amount
                "quantity": {"$gt": 0}  # 確保還有剩餘數量
            }).sort("price", -1).limit(5)
            
            # 取得賣方掛單（價格從低到高）
            sell_orders_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": {"$in": ["pending", "partial", "pending_limit"]},
                "side": "sell",  # 使用 side 欄位而不是 stock_amount
                "quantity": {"$gt": 0}  # 確保還有剩餘數量
            }).sort("price", 1).limit(5)
            
            buy_orders = await buy_orders_cursor.to_list(length=5)
            sell_orders = await sell_orders_cursor.to_list(length=5)
            
            # 聚合相同價格的訂單
            buy_aggregated = {}
            for order in buy_orders:
                price = order.get("price", 0)
                # 修復：使用 quantity 欄位，這是剩餘待撮合的數量
                quantity = order.get("quantity", 0)
                if quantity > 0:  # 只聚合有效的數量
                    buy_aggregated[price] = buy_aggregated.get(price, 0) + quantity
            
            sell_aggregated = {}
            for order in sell_orders:
                price = order.get("price", 0)
                # 修復：使用 quantity 欄位，這是剩餘待撮合的數量
                quantity = order.get("quantity", 0)
                if quantity > 0:  # 只聚合有效的數量
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
    @cached(ttl=10, key_prefix="trade")
    async def get_recent_trades(self, limit: int = 20) -> List[TradeRecord]:
        try:
            trades_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": "filled"
            }).sort("created_at", -1).limit(limit)
            
            trades = await trades_cursor.to_list(length=limit)
            
            trade_records = []
            for trade in trades:
                # Get price from either 'price' or 'filled_price' field
                price = trade.get("price")
                if price is None:
                    price = trade.get("filled_price")
                
                # Skip trades with invalid or missing price data
                if price is None or price <= 0:
                    continue
                    
                trade_records.append(TradeRecord(
                    price=int(price),
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
    @cached(ttl=60, key_prefix="leaderboard")
    async def get_leaderboard(self) -> List[LeaderboardEntry]:
        try:
            # 取得所有使用者
            users_cursor = self.db[Collections.USERS].find({})
            users = await users_cursor.to_list(length=None)
            
            # 取得目前股票價格
            current_price = await self._get_current_stock_price()
            
            # 防護性檢查：確保價格不為 None
            if current_price is None:
                logger.warning("Current stock price is None, using default price 20")
                current_price = 20
            
            leaderboard = []
            for user in users:
                # 取得使用者持股
                stock_holding = await self.db[Collections.STOCKS].find_one(
                    {"user_id": user["_id"]}
                ) or {"stock_amount": 0}
                
                stocks = stock_holding.get("stock_amount", 0)
                stock_value = stocks * current_price
                
                # 取得使用者所屬隊伍
                team_name = user.get("team", "Unknown") or "Unknown"
                
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
    @cached(ttl=30, key_prefix="market")
    async def get_market_status(self) -> MarketStatus:
        try:
            # 取得市場開放時間設定
            market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "market_hours"}
            )
            
            current_time = datetime.now(timezone.utc)
            current_timestamp = int(current_time.timestamp())
            
            # 預設開放時間（如果沒有設定）
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
            
            # 使用統一的市場開放檢查邏輯
            is_open = await self._is_market_open()
            
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
    
    # 取得目前股票價格（近5筆成交均價，單位：元）
    async def _get_current_stock_price(self) -> int:
        try:
            # 從最近5筆成交記錄計算平均價格
            recent_trades_cursor = self.db[Collections.STOCK_ORDERS].find(
                {"status": "filled"},
                sort=[("created_at", -1)]
            ).limit(5)
            
            recent_trades = await recent_trades_cursor.to_list(5)
            
            if recent_trades:
                valid_prices = []
                for trade in recent_trades:
                    price = trade.get("price")
                    if price is not None and price > 0:
                        valid_prices.append(price)
                    else:
                        # 如果 price 欄位為 None，嘗試使用 filled_price
                        filled_price = trade.get("filled_price")
                        if filled_price is not None and filled_price > 0:
                            valid_prices.append(filled_price)
                
                if valid_prices:
                    # 計算平均價格（四捨五入到整數）
                    average_price = sum(valid_prices) / len(valid_prices)
                    return round(average_price)
            
            # 如果沒有成交記錄，從市場設定取得
            price_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "current_price"}
            )
            
            if price_config:
                config_price = price_config.get("price")
                if config_price is not None and config_price > 0:
                    return config_price
            
            # 預設價格（20 元）
            return 20
            
        except Exception as e:
            logger.error(f"Failed to get current stock price: {e}")
            return 20
    
    # 取得歷史價格資料
    async def get_price_history(self, hours: int = 24) -> List[dict]:
        try:
            from datetime import timedelta
            
            # 計算時間範圍
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            # 從真實交易記錄獲取資料
            trades_cursor = self.db[Collections.STOCK_ORDERS].find({
                "status": "filled",
                "created_at": {"$gte": start_time, "$lte": end_time}
            }).sort("created_at", 1)
            
            real_trades = await trades_cursor.to_list(length=None)
            
            # 轉換為回應格式
            history = []
            for trade in real_trades:
                price = trade.get("price")
                if price is not None:  # Skip trades with None price
                    history.append({
                        "timestamp": trade.get("created_at", end_time).isoformat(),
                        "price": int(price)
                    })
            
            return history
                
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            # 發生錯誤時回傳空陣列
            return []
    
    # 取得交易時間列表
    async def get_trading_hours(self) -> TradingHoursResponse:
        try:
            # 取得市場開放時間設定
            market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "market_hours"}
            )
            
            current_time = datetime.now(timezone.utc)
            current_timestamp = int(current_time.timestamp())
            
            # 預設開放時間（如果沒有設定）
            default_open_times = [
                MarketTimeSlot(
                    start=int(current_time.replace(hour=9, minute=0, second=0).timestamp()),
                    end=int(current_time.replace(hour=17, minute=0, second=0).timestamp())
                )
            ]
            
            if market_config and "openTime" in market_config:
                trading_hours = [
                    MarketTimeSlot(start=slot["start"], end=slot["end"])
                    for slot in market_config["openTime"]
                ]
            else:
                trading_hours = default_open_times
            
            # 使用統一的市場開放檢查邏輯
            is_currently_open = await self._is_market_open()
            
            return TradingHoursResponse(
                tradingHours=trading_hours,
                currentTime=current_time.isoformat(),
                isCurrentlyOpen=is_currently_open
            )
            
        except Exception as e:
            logger.error(f"Failed to get trading hours: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve trading hours"
            )
    
    # 取得公開公告列表
    async def get_public_announcements(self, limit: int = 10) -> List[PublicAnnouncement]:
        """
        取得公開公告列表
        
        Args:
            limit: 查詢筆數限制，預設 10 筆
            
        Returns:
            List[PublicAnnouncement]: 公告列表，按時間倒序排列
        """
        try:
            # 查詢公告資料（按時間倒序），排除已刪除的公告
            announcements_cursor = self.db[Collections.ANNOUNCEMENTS].find({
                "$or": [
                    {"is_deleted": {"$exists": False}},  # 舊資料沒有 is_deleted 欄位
                    {"is_deleted": False}                # 新資料明確標記為未刪除
                ]
            }).sort("created_at", -1).limit(limit)
            
            announcements = await announcements_cursor.to_list(length=None)
            
            # 轉換為 PublicAnnouncement 格式
            result = []
            for announcement in announcements:
                result.append(PublicAnnouncement(
                    id=str(announcement["_id"]),
                    title=announcement.get("title", ""),
                    message=announcement.get("message", ""),
                    createdAt=announcement.get("created_at", datetime.now(timezone.utc)).isoformat()
                ))
            
            logger.info(f"Retrieved {len(result)} public announcements")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get public announcements: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve announcements"
            )
    
    # 取得今日交易統計
    async def get_daily_trading_stats(self) -> dict:
        """
        取得今日交易統計資訊
        
        Returns:
            dict: 包含成交筆數、成交額等統計資訊
        """
        try:
            # 計算今日時間範圍
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 聚合查詢今日交易統計
            pipeline = [
                {
                    "$match": {
                        "status": "filled",
                        "created_at": {"$gte": today_start}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_trades": {"$sum": 1},  # 成交筆數
                        "total_volume": {"$sum": {"$abs": "$stock_amount"}},  # 成交股數
                        "total_amount": {  # 成交額
                            "$sum": {
                                "$multiply": [
                                    {"$abs": "$stock_amount"}, 
                                    {"$ifNull": ["$price", {"$ifNull": ["$filled_price", 20]}]}
                                ]
                            }
                        }
                    }
                }
            ]
            
            result = await self.db[Collections.STOCK_ORDERS].aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                return {
                    "total_trades": stats.get("total_trades", 0),
                    "total_volume": stats.get("total_volume", 0), 
                    "total_amount": int(stats.get("total_amount", 0))
                }
            else:
                return {
                    "total_trades": 0,
                    "total_volume": 0,
                    "total_amount": 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get daily trading stats: {e}")
            # 發生錯誤時回傳預設值
            return {
                "total_trades": 0,
                "total_volume": 0,
                "total_amount": 0
            }
    
    # 取得IPO狀態
    async def get_ipo_status(self) -> dict:
        """
        取得IPO狀態資訊
        
        Returns:
            dict: IPO狀態資訊
        """
        try:
            # 查詢IPO設定
            ipo_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "ipo_status"}
            )
            
            if ipo_config:
                return {
                    "available": True,
                    "initialShares": ipo_config.get("initial_shares", 0),
                    "sharesRemaining": ipo_config.get("shares_remaining", 0),
                    "initialPrice": ipo_config.get("initial_price", 20),
                    "updatedAt": ipo_config.get("updated_at", datetime.now(timezone.utc)).isoformat()
                }
            else:
                # IPO還未初始化，返回預設值
                import os
                try:
                    initial_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000"))
                    initial_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20"))
                except (ValueError, TypeError):
                    initial_shares = 1000000
                    initial_price = 20
                
                return {
                    "available": True,
                    "initialShares": initial_shares,
                    "sharesRemaining": initial_shares,
                    "initialPrice": initial_price,
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                    "note": "IPO not yet initialized, showing default values"
                }
                
        except Exception as e:
            logger.error(f"Failed to get IPO status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve IPO status"
            )
    
    # 檢查市場是否開放（與 user_service 邏輯一致）
    async def _is_market_open(self) -> bool:
        """檢查市場是否開放交易"""
        try:
            from datetime import datetime, timezone, timedelta
            
            # 檢查預定時間
            market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "market_hours"}
            )
            
            if not market_config or "openTime" not in market_config:
                # 如果沒有設定，預設市場開放
                return True
            
            # 取得目前台北時間 (UTC+8)
            taipei_tz = timezone(timedelta(hours=8))
            current_time = datetime.now(timezone.utc).astimezone(taipei_tz)
            current_hour = current_time.hour
            current_minute = current_time.minute
            current_seconds_of_day = current_hour * 3600 + current_minute * 60 + current_time.second
            
            # 檢查目前是否在任何一個開放時間段內
            for slot in market_config["openTime"]:
                # 將儲存的時間戳轉換為當日的秒數
                start_dt = datetime.fromtimestamp(slot["start"], tz=timezone.utc).astimezone(taipei_tz)
                end_dt = datetime.fromtimestamp(slot["end"], tz=timezone.utc).astimezone(taipei_tz)
                
                start_seconds = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
                end_seconds = end_dt.hour * 3600 + end_dt.minute * 60 + end_dt.second
                
                # 處理跨日情況（例如 23:00 到 01:00）
                if start_seconds <= end_seconds:
                    # 同一天內的時間段
                    if start_seconds <= current_seconds_of_day <= end_seconds:
                        return True
                else:
                    # 跨日時間段
                    if current_seconds_of_day >= start_seconds or current_seconds_of_day <= end_seconds:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            # 出錯時預設開放，避免影響交易
            return True

    # 取得市場價格資訊
    async def get_market_price_info(self) -> MarketPriceInfo:
        try:
            # 取得目前股價
            current_price = await self._get_current_stock_price()
            
            # 取得市場狀態和收盤價資訊
            market_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "manual_control"}
            )
            
            # 取得最後成交時間
            latest_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "filled"},
                sort=[("created_at", -1)]
            )
            
            last_trade_time = None
            if latest_trade and latest_trade.get("created_at"):
                last_trade_time = latest_trade["created_at"].isoformat()
            
            # 市場狀態 - 使用與 user_service 一致的邏輯
            market_is_open = await self._is_market_open()
            
            # 收盤價和收盤時間
            closing_price = None
            last_close_time = None
            if market_config:
                closing_price = market_config.get("closing_price")
                if market_config.get("close_time"):
                    last_close_time = market_config["close_time"].isoformat()
            
            # 下次開盤初始價 = 上次收盤價 (如果有收盤價的話)
            opening_price = closing_price if closing_price else current_price
            
            return MarketPriceInfo(
                currentPrice=current_price,
                closingPrice=closing_price,
                openingPrice=opening_price,
                lastCloseTime=last_close_time,
                marketIsOpen=market_is_open,
                lastTradeTime=last_trade_time
            )
            
        except Exception as e:
            logger.error(f"Failed to get market price info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve market price information"
            )
