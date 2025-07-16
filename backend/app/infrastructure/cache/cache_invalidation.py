"""
快取失效機制 - 當資料變更時自動清除相關快取
"""
from .cache_service import get_cache_service, CacheKeys
import logging

logger = logging.getLogger(__name__)

class CacheInvalidator:
    """快取失效處理器"""
    
    def __init__(self):
        self.cache_service = get_cache_service()
    
    async def invalidate_price_related_caches(self):
        """清除價格相關的快取"""
        await self.cache_service.invalidate_pattern("price:")
        await self.cache_service.invalidate_pattern("trade:")
        await self.cache_service.invalidate_pattern("leaderboard:")
        logger.info("Price-related caches invalidated")
    
    async def invalidate_user_portfolio_cache(self, user_id: str):
        """清除特定使用者的投資組合快取"""
        await self.cache_service.invalidate(CacheKeys.user_portfolio(user_id))
        logger.info(f"User portfolio cache invalidated for user: {user_id}")
    
    async def invalidate_user_orders_cache(self, user_id: str):
        """清除特定使用者的訂單快取"""
        await self.cache_service.invalidate(CacheKeys.stock_orders(user_id))
        logger.info(f"User orders cache invalidated for user: {user_id}")
    
    async def invalidate_market_status_cache(self):
        """清除市場狀態快取"""
        await self.cache_service.invalidate_pattern("market:")
        logger.info("Market status cache invalidated")
    
    async def invalidate_announcements_cache(self):
        """清除公告快取"""
        await self.cache_service.invalidate_pattern("announcements:")
        logger.info("Announcements cache invalidated")
    
    async def invalidate_all_user_portfolios(self):
        """清除所有使用者投資組合快取"""
        await self.cache_service.invalidate_pattern("user_portfolio:")
        logger.info("All user portfolios cache invalidated")

# 全域實例
_cache_invalidator = CacheInvalidator()

def get_cache_invalidator() -> CacheInvalidator:
    """獲取快取失效處理器實例"""
    return _cache_invalidator