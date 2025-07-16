"""
Market Domain Repositories (Interfaces)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from bson import ObjectId
from .entities import MarketConfig, IPOConfig, Announcement


class MarketConfigRepository(ABC):
    """市場配置存儲庫接口"""
    
    @abstractmethod
    async def find_by_type(self, config_type: str) -> Optional[MarketConfig]:
        """根據配置類型查找配置"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[MarketConfig]:
        """查找所有配置"""
        pass
    
    @abstractmethod
    async def save(self, config: MarketConfig) -> MarketConfig:
        """儲存配置"""
        pass
    
    @abstractmethod
    async def update(self, config: MarketConfig) -> bool:
        """更新配置"""
        pass
    
    @abstractmethod
    async def delete(self, config_id: ObjectId) -> bool:
        """刪除配置"""
        pass


class IPOConfigRepository(ABC):
    """IPO 配置存儲庫接口"""
    
    @abstractmethod
    async def find_active_config(self) -> Optional[IPOConfig]:
        """查找活躍的 IPO 配置"""
        pass
    
    @abstractmethod
    async def find_by_type(self, config_type: str) -> Optional[IPOConfig]:
        """根據配置類型查找 IPO 配置"""
        pass
    
    @abstractmethod
    async def save(self, config: IPOConfig) -> IPOConfig:
        """儲存 IPO 配置"""
        pass
    
    @abstractmethod
    async def update(self, config: IPOConfig) -> bool:
        """更新 IPO 配置"""
        pass
    
    @abstractmethod
    async def delete(self, config_id: ObjectId) -> bool:
        """刪除 IPO 配置"""
        pass


class AnnouncementRepository(ABC):
    """公告存儲庫接口"""
    
    @abstractmethod
    async def find_by_id(self, announcement_id: ObjectId) -> Optional[Announcement]:
        """根據 ID 查找公告"""
        pass
    
    @abstractmethod
    async def find_active_announcements(self) -> List[Announcement]:
        """查找活躍的公告"""
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Announcement]:
        """查找所有公告"""
        pass
    
    @abstractmethod
    async def save(self, announcement: Announcement) -> Announcement:
        """儲存公告"""
        pass
    
    @abstractmethod
    async def update(self, announcement: Announcement) -> bool:
        """更新公告"""
        pass
    
    @abstractmethod
    async def delete(self, announcement_id: ObjectId) -> bool:
        """刪除公告"""
        pass