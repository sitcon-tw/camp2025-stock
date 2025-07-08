# 撮合調度服務
# 負責定期撮合和異步撮合任務

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class MatchingScheduler:
    """
    撮合調度器
    SRP 原則：專注於撮合任務的調度和執行
    """
    
    def __init__(self, user_service):
        self.user_service = user_service
        self._periodic_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._matching_in_progress = False
        
    async def start_periodic_matching(self, interval_seconds: int = 60):
        """開始定期撮合任務"""
        if self._is_running:
            logger.warning("Periodic matching is already running")
            return
            
        self._is_running = True
        self._periodic_task = asyncio.create_task(
            self._periodic_matching_loop(interval_seconds)
        )
        logger.info(f"Started periodic matching with {interval_seconds}s interval")
        
    async def stop_periodic_matching(self):
        """停止定期撮合任務"""
        self._is_running = False
        if self._periodic_task:
            self._periodic_task.cancel()
            try:
                await self._periodic_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped periodic matching")
        
    async def _periodic_matching_loop(self, interval_seconds: int):
        """定期撮合循環"""
        while self._is_running:
            try:
                await asyncio.sleep(interval_seconds)
                if self._is_running:  # 檢查是否仍在運行
                    await self.trigger_matching("periodic_task")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic matching: {e}")
                # 繼續運行，不因單次錯誤而停止
                
    async def trigger_matching_async(self, reason: str = "async_trigger"):
        """異步觸發撮合（不阻塞調用者）"""
        if self._matching_in_progress:
            logger.debug(f"Matching already in progress, skipping {reason}")
            return
            
        # 建立異步任務，不等待完成
        asyncio.create_task(self.trigger_matching(reason))
        
    async def trigger_matching(self, reason: str = "manual_trigger"):
        """執行撮合（會阻塞直到完成）"""
        if self._matching_in_progress:
            logger.debug(f"Matching already in progress, skipping {reason}")
            return
            
        self._matching_in_progress = True
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍Starting order matching (reason: {reason})")
            await self.user_service._try_match_orders()
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"☑️Completed order matching in {duration:.2f}s (reason: {reason})")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌Order matching failed after {duration:.2f}s (reason: {reason}): {e}")
            
        finally:
            self._matching_in_progress = False
            
    def is_matching_in_progress(self) -> bool:
        """檢查是否正在撮合"""
        return self._matching_in_progress
        
    def get_status(self) -> dict:
        """獲取調度器狀態"""
        return {
            "is_running": self._is_running,
            "matching_in_progress": self._matching_in_progress,
            "task_active": self._periodic_task is not None and not self._periodic_task.done()
        }


# 全域調度器實例
_matching_scheduler: Optional[MatchingScheduler] = None


def get_matching_scheduler() -> Optional[MatchingScheduler]:
    """獲取撮合調度器實例"""
    return _matching_scheduler


def set_matching_scheduler(scheduler: MatchingScheduler):
    """設置撮合調度器實例"""
    global _matching_scheduler
    _matching_scheduler = scheduler


async def initialize_matching_scheduler(user_service, start_immediately: bool = True):
    """初始化撮合調度器"""
    global _matching_scheduler
    
    if _matching_scheduler:
        await _matching_scheduler.stop_periodic_matching()
        
    _matching_scheduler = MatchingScheduler(user_service)
    
    if start_immediately:
        # 啟動定期撮合（每分鐘）
        await _matching_scheduler.start_periodic_matching(interval_seconds=60)
        
    logger.info("Matching scheduler initialized")
    return _matching_scheduler


async def cleanup_matching_scheduler():
    """清理撮合調度器"""
    global _matching_scheduler
    
    if _matching_scheduler:
        await _matching_scheduler.stop_periodic_matching()
        _matching_scheduler = None
        logger.info("Matching scheduler cleaned up")