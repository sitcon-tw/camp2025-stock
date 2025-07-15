from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database, Collections
from datetime import datetime, timezone
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

def get_ipo_service() -> IPOService:
    """IPOService 的依賴注入函數"""
    return IPOService()

class IPOService:
    """IPO 服務 - 負責處理 IPO 初次公開發行相關功能"""
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        if db is None:
            self.db = get_database()
        else:
            self.db = db
    
    async def get_or_initialize_ipo_config(self, session=None) -> dict:
        """
        從資料庫獲取 IPO 設定，如果不存在則從環境變數初始化。
        環境變數: CAMP_IPO_INITIAL_SHARES, CAMP_IPO_INITIAL_PRICE
        """
        # 首先嘗試直接獲取
        ipo_config = await self.db[Collections.MARKET_CONFIG].find_one(
            {"type": "ipo_status"}, 
            session=session
        )
        if ipo_config:
            return ipo_config
            
        # 如果不存在，則從環境變數讀取設定並以原子操作寫入
        try:
            initial_shares = int(os.getenv("CAMP_IPO_INITIAL_SHARES"))
            initial_price = int(os.getenv("CAMP_IPO_INITIAL_PRICE"))
        except (ValueError, TypeError):
            logger.error("無效的 IPO 環境變數，使用預設值。")
            initial_shares = 1000000
            initial_price = 20
        
        ipo_doc_on_insert = {
            "type": "ipo_status",
            "initial_shares": initial_shares,
            "shares_remaining": initial_shares,
            "initial_price": initial_price,
            "updated_at": datetime.now(timezone.utc)
        }

        # 使用 upsert + $setOnInsert 原子性地建立文件，避免競爭條件
        await self.db[Collections.MARKET_CONFIG].update_one(
            {"type": "ipo_status"},
            {"$setOnInsert": ipo_doc_on_insert},
            upsert=True,
            session=session
        )

        # 現在，文件保證存在，再次獲取它
        ipo_config = await self.db[Collections.MARKET_CONFIG].find_one(
            {"type": "ipo_status"}, 
            session=session
        )
        
        logger.info(f"從環境變數初始化 IPO 狀態: {initial_shares} 股，每股 {initial_price} 點。")
        return ipo_config
    
    async def get_ipo_status(self) -> dict:
        """獲取 IPO 狀態資訊"""
        try:
            ipo_config = await self.get_or_initialize_ipo_config()
            return {
                "success": True,
                "initial_shares": ipo_config.get("initial_shares", 0),
                "shares_remaining": ipo_config.get("shares_remaining", 0),
                "initial_price": ipo_config.get("initial_price", 0),
                "updated_at": ipo_config.get("updated_at")
            }
        except Exception as e:
            logger.error(f"Failed to get IPO status: {e}")
            return {
                "success": False,
                "message": f"獲取 IPO 狀態失敗: {str(e)}"
            }
    
    async def update_ipo_shares(self, shares_to_deduct: int, session=None) -> dict:
        """
        更新 IPO 剩餘股數（原子操作）
        
        Args:
            shares_to_deduct: 要扣除的股數
            session: 資料庫 session（用於交易）
            
        Returns:
            dict: 更新結果
        """
        try:
            # 使用原子操作確保不會減成負數
            update_result = await self.db[Collections.MARKET_CONFIG].update_one(
                {
                    "type": "ipo_status",
                    "shares_remaining": {"$gte": shares_to_deduct}
                },
                {
                    "$inc": {"shares_remaining": -shares_to_deduct},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                },
                session=session
            )
            
            if update_result.modified_count == 0:
                # 更新失敗，查詢實際剩餘股數
                current_ipo = await self.db[Collections.MARKET_CONFIG].find_one(
                    {"type": "ipo_status"}, session=session
                )
                remaining_shares = current_ipo.get("shares_remaining", 0) if current_ipo else 0
                return {
                    "success": False,
                    "message": f"IPO 股數不足，需要 {shares_to_deduct} 股，剩餘 {remaining_shares} 股",
                    "shares_remaining": remaining_shares
                }
            
            # 更新成功，獲取更新後的狀態
            updated_ipo = await self.db[Collections.MARKET_CONFIG].find_one(
                {"type": "ipo_status"}, session=session
            )
            
            logger.info(f"✅ IPO stock updated: reduced by {shares_to_deduct} shares, remaining: {updated_ipo.get('shares_remaining', 0)}")
            
            return {
                "success": True,
                "message": f"成功扣除 {shares_to_deduct} 股",
                "shares_remaining": updated_ipo.get("shares_remaining", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to update IPO shares: {e}")
            return {
                "success": False,
                "message": f"更新 IPO 股數失敗: {str(e)}"
            }
    
    async def check_ipo_availability(self, required_shares: int) -> dict:
        """
        檢查 IPO 是否有足夠股數可供購買
        
        Args:
            required_shares: 需要的股數
            
        Returns:
            dict: 檢查結果
        """
        try:
            ipo_config = await self.get_or_initialize_ipo_config()
            shares_remaining = ipo_config.get("shares_remaining", 0)
            initial_price = ipo_config.get("initial_price", 0)
            
            if shares_remaining >= required_shares:
                return {
                    "available": True,
                    "shares_remaining": shares_remaining,
                    "price": initial_price,
                    "total_cost": required_shares * initial_price
                }
            else:
                return {
                    "available": False,
                    "shares_remaining": shares_remaining,
                    "price": initial_price,
                    "message": f"IPO 股數不足，需要 {required_shares} 股，剩餘 {shares_remaining} 股"
                }
                
        except Exception as e:
            logger.error(f"Failed to check IPO availability: {e}")
            return {
                "available": False,
                "message": f"檢查 IPO 可用性失敗: {str(e)}"
            }
    
    async def reset_ipo_shares(self, new_shares: int, new_price: Optional[int] = None) -> dict:
        """
        重設 IPO 股數和價格（管理員功能）
        
        Args:
            new_shares: 新的股數
            new_price: 新的價格（可選）
            
        Returns:
            dict: 重設結果
        """
        try:
            update_data = {
                "shares_remaining": new_shares,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if new_price is not None:
                update_data["initial_price"] = new_price
            
            result = await self.db[Collections.MARKET_CONFIG].update_one(
                {"type": "ipo_status"},
                {"$set": update_data},
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id:
                logger.info(f"IPO reset: shares={new_shares}, price={new_price}")
                return {
                    "success": True,
                    "message": f"IPO 設定已重設：股數 {new_shares}，價格 {new_price if new_price else '未變更'}"
                }
            else:
                return {
                    "success": False,
                    "message": "IPO 重設失敗"
                }
                
        except Exception as e:
            logger.error(f"Failed to reset IPO: {e}")
            return {
                "success": False,
                "message": f"重設 IPO 失敗: {str(e)}"
            }