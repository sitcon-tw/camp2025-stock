"""
用戶分片服務 - 分散式優化的核心組件
將用戶分佈到不同的分片中，減少併發衝突
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

class ShardStatus(Enum):
    """分片狀態"""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"

@dataclass
class ShardInfo:
    """分片資訊"""
    shard_id: int
    status: ShardStatus
    load: int  # 當前負載
    max_load: int  # 最大負載
    created_at: datetime
    last_heartbeat: datetime

class UserShardingService:
    """
    用戶分片服務
    
    功能：
    1. 用戶哈希分片
    2. 分片負載均衡
    3. 分片狀態監控
    4. 動態分片調整
    """
    
    def __init__(self, num_shards: int = 16):
        self.num_shards = num_shards
        self.shards: Dict[int, ShardInfo] = {}
        self.user_shard_cache: Dict[str, int] = {}
        
        # 分片統計
        self.shard_stats = defaultdict(lambda: {
            "operations": 0,
            "errors": 0,
            "response_time": 0.0,
            "last_operation": None
        })
        
        # 初始化分片
        self._initialize_shards()
        
        logger.info(f"UserShardingService initialized with {num_shards} shards")
    
    def _initialize_shards(self):
        """初始化所有分片"""
        now = datetime.now(timezone.utc)
        
        for shard_id in range(self.num_shards):
            self.shards[shard_id] = ShardInfo(
                shard_id=shard_id,
                status=ShardStatus.ACTIVE,
                load=0,
                max_load=1000,  # 每個分片最大1000個並發操作
                created_at=now,
                last_heartbeat=now
            )
    
    def get_user_shard(self, user_id: str) -> int:
        """獲取用戶所屬的分片ID"""
        
        # 檢查緩存
        if user_id in self.user_shard_cache:
            return self.user_shard_cache[user_id]
        
        # 使用一致性哈希算法
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        shard_id = hash_value % self.num_shards
        
        # 檢查分片是否可用
        if self.shards[shard_id].status != ShardStatus.ACTIVE:
            # 如果分片不可用，找到最近的可用分片
            shard_id = self._find_alternative_shard(shard_id)
        
        # 緩存結果
        self.user_shard_cache[user_id] = shard_id
        
        logger.debug(f"User {user_id} assigned to shard {shard_id}")
        return shard_id
    
    def _find_alternative_shard(self, preferred_shard: int) -> int:
        """找到替代的可用分片"""
        
        # 從首選分片開始，順序尋找可用分片
        for offset in range(1, self.num_shards):
            candidate_shard = (preferred_shard + offset) % self.num_shards
            
            if (self.shards[candidate_shard].status == ShardStatus.ACTIVE and
                self.shards[candidate_shard].load < self.shards[candidate_shard].max_load):
                
                logger.warning(f"Shard {preferred_shard} unavailable, using shard {candidate_shard}")
                return candidate_shard
        
        # 如果沒有可用分片，返回負載最低的分片
        return self._get_least_loaded_shard()
    
    def _get_least_loaded_shard(self) -> int:
        """獲取負載最低的分片"""
        
        min_load = float('inf')
        best_shard = 0
        
        for shard_id, shard_info in self.shards.items():
            if (shard_info.status == ShardStatus.ACTIVE and 
                shard_info.load < min_load):
                min_load = shard_info.load
                best_shard = shard_id
        
        return best_shard
    
    def get_shard_info(self, shard_id: int) -> Optional[ShardInfo]:
        """獲取分片資訊"""
        return self.shards.get(shard_id)
    
    def update_shard_load(self, shard_id: int, load_delta: int):
        """更新分片負載"""
        if shard_id in self.shards:
            self.shards[shard_id].load += load_delta
            self.shards[shard_id].last_heartbeat = datetime.now(timezone.utc)
            
            # 確保負載不會變成負數
            if self.shards[shard_id].load < 0:
                self.shards[shard_id].load = 0
    
    def record_operation(self, shard_id: int, operation_type: str, 
                        response_time: float, success: bool):
        """記錄分片操作統計"""
        
        stats = self.shard_stats[shard_id]
        stats["operations"] += 1
        stats["response_time"] = (stats["response_time"] + response_time) / 2
        stats["last_operation"] = datetime.now(timezone.utc)
        
        if not success:
            stats["errors"] += 1
    
    def get_users_in_shard(self, shard_id: int) -> List[str]:
        """獲取分片中的所有用戶"""
        return [user_id for user_id, user_shard in self.user_shard_cache.items() 
                if user_shard == shard_id]
    
    def set_shard_status(self, shard_id: int, status: ShardStatus):
        """設定分片狀態"""
        if shard_id in self.shards:
            old_status = self.shards[shard_id].status
            self.shards[shard_id].status = status
            
            logger.info(f"Shard {shard_id} status changed from {old_status} to {status}")
            
            # 如果分片被禁用，清除相關用戶緩存
            if status == ShardStatus.DISABLED:
                self._clear_shard_cache(shard_id)
    
    def _clear_shard_cache(self, shard_id: int):
        """清除分片的用戶緩存"""
        users_to_remove = [user_id for user_id, user_shard in self.user_shard_cache.items() 
                          if user_shard == shard_id]
        
        for user_id in users_to_remove:
            del self.user_shard_cache[user_id]
        
        logger.info(f"Cleared cache for {len(users_to_remove)} users in shard {shard_id}")
    
    def get_shard_statistics(self) -> Dict[str, Any]:
        """獲取分片統計資訊"""
        
        total_operations = sum(stats["operations"] for stats in self.shard_stats.values())
        total_errors = sum(stats["errors"] for stats in self.shard_stats.values())
        
        shard_details = {}
        for shard_id, shard_info in self.shards.items():
            stats = self.shard_stats[shard_id]
            user_count = len(self.get_users_in_shard(shard_id))
            
            shard_details[f"shard_{shard_id}"] = {
                "status": shard_info.status.value,
                "load": shard_info.load,
                "max_load": shard_info.max_load,
                "user_count": user_count,
                "operations": stats["operations"],
                "errors": stats["errors"],
                "error_rate": stats["errors"] / max(stats["operations"], 1) * 100,
                "avg_response_time": stats["response_time"],
                "last_operation": stats["last_operation"].isoformat() if stats["last_operation"] else None
            }
        
        return {
            "total_shards": self.num_shards,
            "active_shards": sum(1 for s in self.shards.values() if s.status == ShardStatus.ACTIVE),
            "total_operations": total_operations,
            "total_errors": total_errors,
            "overall_error_rate": total_errors / max(total_operations, 1) * 100,
            "cached_users": len(self.user_shard_cache),
            "shard_details": shard_details
        }
    
    async def rebalance_shards(self):
        """重新平衡分片負載"""
        
        logger.info("Starting shard rebalancing...")
        
        # 計算平均負載
        total_load = sum(shard.load for shard in self.shards.values() 
                        if shard.status == ShardStatus.ACTIVE)
        active_shards = sum(1 for shard in self.shards.values() 
                          if shard.status == ShardStatus.ACTIVE)
        
        if active_shards == 0:
            logger.error("No active shards available for rebalancing")
            return
        
        avg_load = total_load / active_shards
        
        # 找出負載過高的分片
        overloaded_shards = [
            shard_id for shard_id, shard in self.shards.items()
            if (shard.status == ShardStatus.ACTIVE and 
                shard.load > avg_load * 1.5)  # 超過平均負載150%
        ]
        
        if overloaded_shards:
            logger.info(f"Found {len(overloaded_shards)} overloaded shards: {overloaded_shards}")
            
            # 實際的重新平衡邏輯會在這裡實現
            # 這可能涉及到將一些用戶遷移到其他分片
            # 或者調整分片的最大負載限制
            
            for shard_id in overloaded_shards:
                self.shards[shard_id].max_load = int(self.shards[shard_id].max_load * 1.2)
                logger.info(f"Increased max_load for shard {shard_id} to {self.shards[shard_id].max_load}")
        
        logger.info("Shard rebalancing completed")

# 分片上下文管理器
class ShardContext:
    """分片上下文管理器 - 用於追蹤分片操作"""
    
    def __init__(self, sharding_service: UserShardingService, 
                 shard_id: int, operation_type: str):
        self.sharding_service = sharding_service
        self.shard_id = shard_id
        self.operation_type = operation_type
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = asyncio.get_event_loop().time()
        self.sharding_service.update_shard_load(self.shard_id, 1)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - self.start_time
        success = exc_type is None
        
        self.sharding_service.update_shard_load(self.shard_id, -1)
        self.sharding_service.record_operation(
            self.shard_id, self.operation_type, response_time, success
        )

# 全域分片服務實例
_sharding_service: Optional[UserShardingService] = None

def get_sharding_service() -> Optional[UserShardingService]:
    """獲取分片服務實例"""
    return _sharding_service

def initialize_sharding_service(num_shards: int = 16) -> UserShardingService:
    """初始化分片服務"""
    global _sharding_service
    _sharding_service = UserShardingService(num_shards)
    logger.info(f"Sharding service initialized with {num_shards} shards")
    return _sharding_service