"""
快取服務 - 減少資料庫查詢頻率
"""
from typing import Any, Optional, Dict, Callable, Awaitable
from datetime import datetime, timedelta
import asyncio
import json
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CacheEntry:
    """快取條目"""
    def __init__(self, data: Any, ttl: int):
        self.data = data
        self.created_at = datetime.now()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl)

class CacheService:
    """內存快取服務"""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._default_ttl = 30  # 預設30秒TTL
        
    def _get_lock(self, key: str) -> asyncio.Lock:
        """獲取或創建鎖"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """從快取獲取資料"""
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            logger.debug(f"Cache hit for key: {key}")
            return entry.data
        
        # 清理過期條目
        if entry and entry.is_expired():
            logger.debug(f"Cache expired for key: {key}")
            self._cache.pop(key, None)
            self._locks.pop(key, None)
        
        return None
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """設置快取資料"""
        ttl = ttl or self._default_ttl
        self._cache[key] = CacheEntry(data, ttl)
        logger.debug(f"Cache set for key: {key}, ttl: {ttl}s")
    
    async def invalidate(self, key: str) -> None:
        """清除指定快取"""
        self._cache.pop(key, None)
        self._locks.pop(key, None)
        logger.debug(f"Cache invalidated for key: {key}")
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """清除匹配模式的快取"""
        keys_to_remove = [key for key in self._cache.keys() if pattern in key]
        for key in keys_to_remove:
            await self.invalidate(key)
        logger.debug(f"Cache invalidated for pattern: {pattern}, removed {len(keys_to_remove)} keys")
    
    async def clear(self) -> None:
        """清空所有快取"""
        self._cache.clear()
        self._locks.clear()
        logger.debug("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取快取統計"""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_keys": list(self._cache.keys())
        }

# 全域快取實例
_cache_service = CacheService()

def get_cache_service() -> CacheService:
    """獲取快取服務實例"""
    return _cache_service

def cached(ttl: int = 30, key_prefix: str = ""):
    """
    快取裝飾器
    
    Args:
        ttl: 快取過期時間（秒）
        key_prefix: 快取鍵前綴
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成快取鍵
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{hash(str(args))}"
            if kwargs:
                cache_key += f":{hash(str(sorted(kwargs.items())))}"
            
            # 嘗試從快取獲取
            cached_result = await _cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 使用鎖防止重複計算
            lock = _cache_service._get_lock(cache_key)
            async with lock:
                # 雙重檢查
                cached_result = await _cache_service.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 執行原函數
                result = await func(*args, **kwargs)
                
                # 快取結果
                await _cache_service.set(cache_key, result, ttl)
                
                return result
        
        return wrapper
    return decorator

# 針對高頻查詢的專用快取鍵
class CacheKeys:
    """快取鍵常量"""
    PRICE_SUMMARY = "price:summary"
    PRICE_DEPTH = "price:depth"
    TRADE_HISTORY = "trade:history"
    LEADERBOARD = "leaderboard"
    MARKET_STATUS = "market:status"
    TRADING_HOURS = "trading:hours"
    SYSTEM_STATS = "system:stats"
    USER_PORTFOLIO = "user:portfolio"
    STOCK_ORDERS = "stock:orders"
    ANNOUNCEMENTS = "announcements"
    
    @staticmethod
    def user_portfolio(user_id: str) -> str:
        return f"{CacheKeys.USER_PORTFOLIO}:{user_id}"
    
    @staticmethod
    def stock_orders(user_id: str) -> str:
        return f"{CacheKeys.STOCK_ORDERS}:{user_id}"
    
    @staticmethod
    def trade_history(limit: int) -> str:
        return f"{CacheKeys.TRADE_HISTORY}:{limit}"
    
    @staticmethod
    def announcements(limit: int) -> str:
        return f"{CacheKeys.ANNOUNCEMENTS}:{limit}"