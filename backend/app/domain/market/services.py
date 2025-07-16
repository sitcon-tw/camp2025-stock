"""
Market Domain Services
"""
from __future__ import annotations
from typing import Optional, List
from datetime import time
from bson import ObjectId
from .entities import MarketConfig, IPOConfig, Announcement, MarketStatus
from .repositories import MarketConfigRepository, IPOConfigRepository, AnnouncementRepository
from app.shared.exceptions import DomainException
import logging

logger = logging.getLogger(__name__)


class MarketDomainService:
    """市場領域服務"""
    
    def __init__(
        self,
        market_config_repository: MarketConfigRepository,
        ipo_config_repository: IPOConfigRepository,
        announcement_repository: AnnouncementRepository
    ):
        self.market_config_repository = market_config_repository
        self.ipo_config_repository = ipo_config_repository
        self.announcement_repository = announcement_repository
    
    async def get_market_status(self) -> MarketConfig:
        """獲取市場狀態"""
        config = await self.market_config_repository.find_by_type("market_hours")
        if not config:
            # 創建默認配置
            config = MarketConfig(
                config_type="market_hours",
                status=MarketStatus.CLOSED,
                manual_control=False
            )
            config = await self.market_config_repository.save(config)
        
        return config
    
    async def set_manual_market_control(self, is_open: bool) -> MarketConfig:
        """設定手動市場控制"""
        config = await self.get_market_status()
        config.set_manual_control(is_open)
        await self.market_config_repository.update(config)
        return config
    
    async def set_scheduled_market_hours(self, open_time: time, close_time: time) -> MarketConfig:
        """設定預定市場時間"""
        config = await self.get_market_status()
        config.set_scheduled_hours(open_time, close_time)
        await self.market_config_repository.update(config)
        return config
    
    async def is_market_open(self) -> bool:
        """檢查市場是否開放"""
        config = await self.get_market_status()
        return config.is_market_open()
    
    async def get_ipo_config(self) -> IPOConfig:
        """獲取 IPO 配置"""
        config = await self.ipo_config_repository.find_by_type("ipo_status")
        if not config:
            # 創建默認 IPO 配置
            config = IPOConfig(
                config_type="ipo_status",
                initial_shares=1000,
                initial_price=100,
                is_active=False
            )
            config = await self.ipo_config_repository.save(config)
        
        return config
    
    async def configure_ipo(self, initial_shares: int, initial_price: int, is_active: bool) -> IPOConfig:
        """配置 IPO"""
        if initial_shares <= 0:
            raise DomainException("初始股數必須大於 0")
        
        if initial_price <= 0:
            raise DomainException("初始價格必須大於 0")
        
        config = await self.get_ipo_config()
        config.update_settings(initial_shares, initial_price)
        
        if is_active:
            config.activate()
        else:
            config.deactivate()
        
        await self.ipo_config_repository.update(config)
        return config
    
    async def is_ipo_active(self) -> bool:
        """檢查 IPO 是否活躍"""
        config = await self.get_ipo_config()
        return config.is_active
    
    async def create_announcement(self, title: str, content: str) -> Announcement:
        """創建公告"""
        if not title or len(title.strip()) == 0:
            raise DomainException("公告標題不能為空")
        
        if not content or len(content.strip()) == 0:
            raise DomainException("公告內容不能為空")
        
        announcement = Announcement(
            title=title.strip(),
            content=content.strip(),
            is_active=True
        )
        
        return await self.announcement_repository.save(announcement)
    
    async def update_announcement(self, announcement_id: ObjectId, title: str, content: str) -> Announcement:
        """更新公告"""
        announcement = await self.announcement_repository.find_by_id(announcement_id)
        if not announcement:
            raise DomainException("公告不存在")
        
        if not title or len(title.strip()) == 0:
            raise DomainException("公告標題不能為空")
        
        if not content or len(content.strip()) == 0:
            raise DomainException("公告內容不能為空")
        
        announcement.update_content(title.strip(), content.strip())
        await self.announcement_repository.update(announcement)
        return announcement
    
    async def toggle_announcement(self, announcement_id: ObjectId, is_active: bool) -> Announcement:
        """切換公告狀態"""
        announcement = await self.announcement_repository.find_by_id(announcement_id)
        if not announcement:
            raise DomainException("公告不存在")
        
        if is_active:
            announcement.activate()
        else:
            announcement.deactivate()
        
        await self.announcement_repository.update(announcement)
        return announcement
    
    async def get_active_announcements(self) -> List[Announcement]:
        """獲取活躍公告"""
        return await self.announcement_repository.find_active_announcements()
    
    async def get_all_announcements(self, skip: int = 0, limit: int = 100) -> List[Announcement]:
        """獲取所有公告"""
        return await self.announcement_repository.find_all(skip, limit)
    
    async def delete_announcement(self, announcement_id: ObjectId) -> bool:
        """刪除公告"""
        announcement = await self.announcement_repository.find_by_id(announcement_id)
        if not announcement:
            raise DomainException("公告不存在")
        
        return await self.announcement_repository.delete(announcement_id)