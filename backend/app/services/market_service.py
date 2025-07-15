from __future__ import annotations
from app.services.base_service import BaseService
from app.core.database import Collections
from app.core.config_refactored import config
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


def get_market_service() -> MarketService:
    """MarketService 的依賴注入函數"""
    return MarketService()


class MarketService(BaseService):
    """市場服務 - 負責處理市場開放狀態、價格限制等功能"""
    
    async def is_market_open(self) -> bool:
        """檢查市場是否開放"""
        try:
            # 首先檢查手動控制
            manual_control = await self.db[Collections.MARKET_CONFIG].find_one({"type": "manual_control"})
            if manual_control:
                return manual_control.get("is_open", False)
            
            # 檢查市場時間設定
            market_hours = await self.db[Collections.MARKET_CONFIG].find_one({"type": "market_hours"})
            if not market_hours:
                return False
            
            # 檢查當前時間是否在交易時間內
            now = datetime.now(timezone.utc)
            current_hour = now.hour
            current_minute = now.minute
            current_time_minutes = current_hour * 60 + current_minute
            
            start_time = market_hours.get("start_time", "09:00")
            end_time = market_hours.get("end_time", "17:00")
            
            start_hour, start_minute = map(int, start_time.split(":"))
            end_hour, end_minute = map(int, end_time.split(":"))
            
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            return start_minutes <= current_time_minutes <= end_minutes
            
        except Exception as e:
            logger.error(f"Failed to check market open status: {e}")
            return False
    
    async def get_current_stock_price(self) -> int:
        """獲取當前股票價格"""
        try:
            # 查找最近的成交記錄
            recent_trade = await self.db[Collections.STOCK_ORDERS].find_one(
                {"status": "filled", "filled_price": {"$exists": True}},
                sort=[("filled_at", -1)]
            )
            
            if recent_trade and "filled_price" in recent_trade:
                return int(recent_trade["filled_price"])
            
            # 如果沒有成交記錄，使用 IPO 初始價格
            ipo_config = await self.get_ipo_config()
            if ipo_config:
                return ipo_config.get("initial_price", 20)
            
            # 預設價格
            return 20
            
        except Exception as e:
            logger.error(f"Failed to get current stock price: {e}")
            return 20
    
    async def get_ipo_config(self) -> Optional[Dict[str, Any]]:
        """獲取 IPO 配置"""
        try:
            return await self.db[Collections.MARKET_CONFIG].find_one({"type": "ipo_status"})
        except Exception as e:
            logger.error(f"Failed to get IPO config: {e}")
            return None
    
    async def initialize_ipo_config(self, session=None) -> Dict[str, Any]:
        """初始化 IPO 配置"""
        try:
            # 首先嘗試獲取現有配置
            ipo_config = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "ipo_status"}, 
                session=session
            )
            if ipo_config:
                return ipo_config
            
            # 從環境變數讀取配置
            try:
                initial_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES", "1000000"))
                initial_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE", "20"))
            except (ValueError, TypeError):
                logger.error("無效的 IPO 環境變數，使用預設值。")
                initial_shares = 1000000
                initial_price = 20
            
            ipo_doc = {
                "type": "ipo_status",
                "initial_shares": initial_shares,
                "shares_remaining": initial_shares,
                "initial_price": initial_price,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # 使用 upsert 原子性地建立文件
            await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "ipo_status"},
                {"$setOnInsert": ipo_doc},
                upsert=True,
                session=session
            )
            
            return ipo_doc
            
        except Exception as e:
            logger.error(f"Failed to initialize IPO config: {e}")
            raise
    
    async def check_price_limit(self, order_price: float) -> bool:
        """檢查價格是否在漲跌限制內"""
        try:
            limit_info = await self.get_price_limit_info(order_price)
            return limit_info["within_limit"]
        except Exception as e:
            logger.error(f"Failed to check price limit: {e}")
            return True  # 預設允許交易
    
    async def get_price_limit_info(self, order_price: float) -> Dict[str, Any]:
        """獲取價格限制資訊"""
        try:
            # 檢查是否啟用價格限制
            limit_config = await self.db[Collections.MARKET_CONFIG].find_one({"type": "price_limit"})
            if not limit_config or not limit_config.get("enabled", False):
                return {
                    "within_limit": True,
                    "limit_enabled": False,
                    "message": "價格限制未啟用"
                }
            
            limit_type = limit_config.get("limit_type", "percentage")
            
            if limit_type == "percentage":
                return await self._get_percentage_limit_info(order_price, limit_config)
            elif limit_type == "fixed":
                return await self._get_fixed_limit_info(order_price, limit_config)
            else:
                return {
                    "within_limit": True,
                    "limit_enabled": False,
                    "message": "未知的價格限制類型"
                }
                
        except Exception as e:
            logger.error(f"Failed to get price limit info: {e}")
            return {
                "within_limit": True,
                "limit_enabled": False,
                "message": f"價格限制檢查失敗: {str(e)}"
            }
    
    async def _get_percentage_limit_info(self, order_price: float, limit_config: Dict[str, Any]) -> Dict[str, Any]:
        """獲取百分比限制資訊"""
        reference_price = await self._get_reference_price_for_limit()
        limit_percent = limit_config.get("limit_percent", 10.0)
        
        min_price = reference_price * (1 - limit_percent / 100)
        max_price = reference_price * (1 + limit_percent / 100)
        
        within_limit = min_price <= order_price <= max_price
        
        return {
            "within_limit": within_limit,
            "limit_enabled": True,
            "limit_type": "percentage",
            "limit_percent": limit_percent,
            "reference_price": reference_price,
            "min_price": min_price,
            "max_price": max_price,
            "order_price": order_price,
            "message": f"價格限制: ±{limit_percent}%，允許範圍: {min_price:.2f} - {max_price:.2f}"
        }
    
    async def _get_fixed_limit_info(self, order_price: float, limit_config: Dict[str, Any]) -> Dict[str, Any]:
        """獲取固定限制資訊"""
        reference_price = await self._get_reference_price_for_limit()
        limit_amount = limit_config.get("limit_amount", 2.0)
        
        min_price = reference_price - limit_amount
        max_price = reference_price + limit_amount
        
        within_limit = min_price <= order_price <= max_price
        
        return {
            "within_limit": within_limit,
            "limit_enabled": True,
            "limit_type": "fixed",
            "limit_amount": limit_amount,
            "reference_price": reference_price,
            "min_price": min_price,
            "max_price": max_price,
            "order_price": order_price,
            "message": f"價格限制: ±{limit_amount}元，允許範圍: {min_price:.2f} - {max_price:.2f}"
        }
    
    async def _get_reference_price_for_limit(self) -> float:
        """獲取價格限制的參考價格"""
        try:
            # 首先檢查是否有固定的參考價格設定
            reference_config = await self.db[Collections.MARKET_CONFIG].find_one({"type": "reference_price"})
            if reference_config and reference_config.get("price"):
                return float(reference_config["price"])
            
            # 使用當前股票價格作為參考
            current_price = await self.get_current_stock_price()
            return float(current_price)
            
        except Exception as e:
            logger.error(f"Failed to get reference price: {e}")
            return 20.0  # 預設參考價格