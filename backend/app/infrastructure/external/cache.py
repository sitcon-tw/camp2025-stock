"""
Cache Service Implementations
"""
import json
import pickle
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import asyncio
import logging

from ...application.common.interfaces import CacheService
from ...domain.common.exceptions import BusinessRuleException

logger = logging.getLogger(__name__)


class CacheProvider(ABC):
    """緩存提供者接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設置緩存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """刪除緩存值"""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> None:
        """清除匹配模式的緩存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> None:
        """設置過期時間"""
        pass


class MemoryCacheProvider(CacheProvider):
    """內存緩存提供者"""
    
    def __init__(self, default_ttl: int = 3600):
        self.cache: Dict[str, Any] = {}
        self.expiry: Dict[str, datetime] = {}
        self.default_ttl = default_ttl
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """啟動清理任務"""
        self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def _cleanup_expired(self):
        """清理過期的緩存項"""
        while True:
            try:
                now = datetime.utcnow()
                expired_keys = []
                
                for key, expire_time in self.expiry.items():
                    if now >= expire_time:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    self.cache.pop(key, None)
                    self.expiry.pop(key, None)
                
                await asyncio.sleep(60)  # 每分鐘清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        try:
            # 檢查是否過期
            if key in self.expiry:
                if datetime.utcnow() >= self.expiry[key]:
                    # 已過期，刪除
                    self.cache.pop(key, None)
                    self.expiry.pop(key, None)
                    return None
            
            return self.cache.get(key)
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設置緩存值"""
        try:
            self.cache[key] = value
            
            # 設置過期時間
            if ttl is None:
                ttl = self.default_ttl
            
            if ttl > 0:
                self.expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
    
    async def delete(self, key: str) -> None:
        """刪除緩存值"""
        try:
            self.cache.pop(key, None)
            self.expiry.pop(key, None)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
    
    async def clear_pattern(self, pattern: str) -> None:
        """清除匹配模式的緩存"""
        try:
            import fnmatch
            
            keys_to_delete = []
            for key in self.cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                await self.delete(key)
                
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
    
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        try:
            # 檢查是否過期
            if key in self.expiry:
                if datetime.utcnow() >= self.expiry[key]:
                    # 已過期，刪除
                    self.cache.pop(key, None)
                    self.expiry.pop(key, None)
                    return False
            
            return key in self.cache
            
        except Exception as e:
            logger.error(f"Error checking cache key existence {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> None:
        """設置過期時間"""
        try:
            if key in self.cache:
                self.expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
        except Exception as e:
            logger.error(f"Error setting expiry for cache key {key}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        return {
            "total_keys": len(self.cache),
            "expired_keys": len([k for k, v in self.expiry.items() if datetime.utcnow() >= v]),
            "memory_usage": sum(len(str(v)) for v in self.cache.values())
        }
    
    async def cleanup(self):
        """清理資源"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class RedisCacheProvider(CacheProvider):
    """Redis 緩存提供者"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600, key_prefix: str = "sitcon:"):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.redis = None
    
    async def _get_redis(self):
        """獲取 Redis 連接"""
        if not self.redis:
            import aioredis
            self.redis = await aioredis.from_url(self.redis_url)
        return self.redis
    
    def _make_key(self, key: str) -> str:
        """生成完整的鍵名"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            
            value = await redis.get(full_key)
            if value is None:
                return None
            
            # 嘗試反序列化
            return self._deserialize(value)
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設置緩存值"""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            
            # 序列化值
            serialized_value = self._serialize(value)
            
            if ttl is None:
                ttl = self.default_ttl
            
            if ttl > 0:
                await redis.setex(full_key, ttl, serialized_value)
            else:
                await redis.set(full_key, serialized_value)
                
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
    
    async def delete(self, key: str) -> None:
        """刪除緩存值"""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            await redis.delete(full_key)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
    
    async def clear_pattern(self, pattern: str) -> None:
        """清除匹配模式的緩存"""
        try:
            redis = await self._get_redis()
            full_pattern = self._make_key(pattern)
            
            # 獲取匹配的鍵
            keys = await redis.keys(full_pattern)
            
            if keys:
                await redis.delete(*keys)
                
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
    
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            return await redis.exists(full_key)
        except Exception as e:
            logger.error(f"Error checking cache key existence {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> None:
        """設置過期時間"""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            await redis.expire(full_key, ttl)
        except Exception as e:
            logger.error(f"Error setting expiry for cache key {key}: {e}")
    
    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        try:
            # 嘗試 JSON 序列化
            return json.dumps(value, default=str).encode('utf-8')
        except (TypeError, ValueError):
            # 如果 JSON 序列化失敗，使用 pickle
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """反序列化值"""
        try:
            # 嘗試 JSON 反序列化
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # 如果 JSON 反序列化失敗，使用 pickle
            return pickle.loads(value)
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        try:
            redis = await self._get_redis()
            info = await redis.info()
            
            return {
                "used_memory": info.get('used_memory', 0),
                "used_memory_human": info.get('used_memory_human', '0B'),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "connected_clients": info.get('connected_clients', 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    async def cleanup(self):
        """清理資源"""
        if self.redis:
            await self.redis.close()


class LayeredCacheProvider(CacheProvider):
    """分層緩存提供者"""
    
    def __init__(self, l1_cache: CacheProvider, l2_cache: Optional[CacheProvider] = None):
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        # 先從 L1 緩存獲取
        value = await self.l1_cache.get(key)
        if value is not None:
            return value
        
        # 如果 L1 沒有，從 L2 獲取
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value is not None:
                # 將值回寫到 L1 緩存
                await self.l1_cache.set(key, value, ttl=300)  # 5分鐘
                return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設置緩存值"""
        # 同時寫入 L1 和 L2 緩存
        await self.l1_cache.set(key, value, ttl)
        
        if self.l2_cache:
            await self.l2_cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """刪除緩存值"""
        await self.l1_cache.delete(key)
        
        if self.l2_cache:
            await self.l2_cache.delete(key)
    
    async def clear_pattern(self, pattern: str) -> None:
        """清除匹配模式的緩存"""
        await self.l1_cache.clear_pattern(pattern)
        
        if self.l2_cache:
            await self.l2_cache.clear_pattern(pattern)
    
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        if await self.l1_cache.exists(key):
            return True
        
        if self.l2_cache:
            return await self.l2_cache.exists(key)
        
        return False
    
    async def expire(self, key: str, ttl: int) -> None:
        """設置過期時間"""
        await self.l1_cache.expire(key, ttl)
        
        if self.l2_cache:
            await self.l2_cache.expire(key, ttl)
    
    async def cleanup(self):
        """清理資源"""
        if hasattr(self.l1_cache, 'cleanup'):
            await self.l1_cache.cleanup()
        
        if self.l2_cache and hasattr(self.l2_cache, 'cleanup'):
            await self.l2_cache.cleanup()


class CacheServiceImpl(CacheService):
    """緩存服務實現"""
    
    def __init__(self, provider: CacheProvider):
        self.provider = provider
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        return await self.provider.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設置緩存值"""
        await self.provider.set(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """刪除緩存值"""
        await self.provider.delete(key)
    
    async def clear_pattern(self, pattern: str) -> None:
        """清除匹配模式的緩存"""
        await self.provider.clear_pattern(pattern)
    
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        return await self.provider.exists(key)
    
    async def expire(self, key: str, ttl: int) -> None:
        """設置過期時間"""
        await self.provider.expire(key, ttl)
    
    async def get_or_set(self, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        """獲取或設置緩存值"""
        value = await self.get(key)
        if value is not None:
            return value
        
        # 如果沒有緩存，調用工廠函數生成值
        if asyncio.iscoroutinefunction(factory_func):
            value = await factory_func()
        else:
            value = factory_func()
        
        if value is not None:
            await self.set(key, value, ttl)
        
        return value
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        if hasattr(self.provider, 'get_stats'):
            return await self.provider.get_stats()
        return {}
    
    async def cleanup(self):
        """清理資源"""
        if hasattr(self.provider, 'cleanup'):
            await self.provider.cleanup()


# 工廠函數
def create_cache_service(config: Dict[str, Any]) -> CacheService:
    """創建緩存服務"""
    cache_type = config.get('type', 'memory')
    
    if cache_type == 'memory':
        provider = MemoryCacheProvider(
            default_ttl=config.get('default_ttl', 3600)
        )
    elif cache_type == 'redis':
        provider = RedisCacheProvider(
            redis_url=config['redis_url'],
            default_ttl=config.get('default_ttl', 3600),
            key_prefix=config.get('key_prefix', 'sitcon:')
        )
    elif cache_type == 'layered':
        # 分層緩存：內存 + Redis
        l1_provider = MemoryCacheProvider(default_ttl=300)  # 5分鐘
        l2_provider = RedisCacheProvider(
            redis_url=config['redis_url'],
            default_ttl=config.get('default_ttl', 3600),
            key_prefix=config.get('key_prefix', 'sitcon:')
        )
        provider = LayeredCacheProvider(l1_provider, l2_provider)
    else:
        raise ValueError(f"Unsupported cache type: {cache_type}")
    
    return CacheServiceImpl(provider)