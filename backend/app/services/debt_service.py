"""
債務管理服務
處理用戶欠款相關邏輯
"""

import logging
from typing import Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import Collections
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DebtService:
    """債務管理服務"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_user_debt_info(self, user_id: ObjectId) -> Dict[str, Any]:
        """
        獲取用戶債務信息
        
        Args:
            user_id: 用戶ID
            
        Returns:
            dict: 包含債務信息的字典
        """
        try:
            user = await self.db[Collections.USERS].find_one({"_id": user_id})
            
            if not user:
                return {
                    'success': False,
                    'message': '使用者不存在',
                    'user_exists': False
                }
            
            points = user.get("points", 0)
            owed_points = user.get("owed_points", 0)
            frozen = user.get("frozen", False)
            enabled = user.get("enabled", True)
            
            # 計算實際可用餘額
            available_balance = points - owed_points
            
            return {
                'success': True,
                'user_exists': True,
                'user_id': str(user_id),
                'name': user.get('name', 'Unknown'),
                'points': points,
                'owed_points': owed_points,
                'available_balance': available_balance,
                'frozen': frozen,
                'enabled': enabled,
                'has_debt': owed_points > 0,
                'can_trade': enabled and not frozen and owed_points == 0
            }
            
        except Exception as e:
            logger.error(f"Error getting debt info for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'獲取債務信息失敗: {str(e)}',
                'user_exists': False
            }
    
    async def validate_user_can_spend(self, user_id: ObjectId, amount: int) -> Dict[str, Any]:
        """
        驗證用戶是否可以消費指定金額
        
        Args:
            user_id: 用戶ID
            amount: 消費金額
            
        Returns:
            dict: 驗證結果
        """
        try:
            debt_info = await self.get_user_debt_info(user_id)
            
            if not debt_info['success']:
                return debt_info
            
            if not debt_info['user_exists']:
                return {
                    'success': False,
                    'can_spend': False,
                    'message': '使用者不存在'
                }
            
            if not debt_info['enabled']:
                return {
                    'success': False,
                    'can_spend': False,
                    'message': '帳戶未啟用'
                }
            
            if debt_info['frozen']:
                return {
                    'success': False,
                    'can_spend': False,
                    'message': '帳戶已凍結，無法進行交易'
                }
            
            if debt_info['has_debt']:
                return {
                    'success': False,
                    'can_spend': False,
                    'message': f'帳戶有欠款 {debt_info["owed_points"]} 點，請先償還後才能進行交易',
                    'owed_points': debt_info['owed_points']
                }
            
            if debt_info['available_balance'] < amount:
                return {
                    'success': False,
                    'can_spend': False,
                    'message': f'餘額不足。需要: {amount} 點，可用: {debt_info["available_balance"]} 點',
                    'available_balance': debt_info['available_balance'],
                    'required_amount': amount
                }
            
            return {
                'success': True,
                'can_spend': True,
                'message': '可以進行交易',
                'available_balance': debt_info['available_balance']
            }
            
        except Exception as e:
            logger.error(f"Error validating user spending for {user_id}: {e}")
            return {
                'success': False,
                'can_spend': False,
                'message': f'驗證失敗: {str(e)}'
            }
    
    async def repay_debt(self, user_id: ObjectId, amount: int, admin_id: Optional[ObjectId] = None) -> Dict[str, Any]:
        """
        償還欠款功能
        
        Args:
            user_id: 用戶ID
            amount: 償還金額
            admin_id: 管理員ID (可選)
            
        Returns:
            dict: 償還結果
        """
        try:
            async with await self.db.client.start_session() as session:
                async with session.start_transaction():
                    user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
                    
                    if not user:
                        return {
                            'success': False,
                            'message': '使用者不存在'
                        }
                    
                    current_points = user.get("points", 0)
                    owed_points = user.get("owed_points", 0)
                    
                    if owed_points == 0:
                        return {
                            'success': False,
                            'message': '該用戶沒有欠款'
                        }
                    
                    if current_points < amount:
                        return {
                            'success': False,
                            'message': f'點數不足以償還欠款。需要: {amount} 點，擁有: {current_points} 點'
                        }
                    
                    # 計算實際償還金額（不能超過欠款總額）
                    repay_amount = min(amount, owed_points)
                    
                    # 更新用戶資料
                    await self.db[Collections.USERS].update_one(
                        {"_id": user_id},
                        {
                            "$inc": {"points": -repay_amount, "owed_points": -repay_amount},
                            "$set": {"updated_at": datetime.now(timezone.utc)}
                        },
                        session=session
                    )
                    
                    # 檢查是否完全償還，解除凍結
                    remaining_debt = owed_points - repay_amount
                    if remaining_debt == 0:
                        await self.db[Collections.USERS].update_one(
                            {"_id": user_id},
                            {"$set": {"frozen": False}},
                            session=session
                        )
                    
                    # 記錄償還歷史
                    repay_log = {
                        "user_id": user_id,
                        "admin_id": admin_id,
                        "repay_amount": repay_amount,
                        "previous_debt": owed_points,
                        "remaining_debt": remaining_debt,
                        "timestamp": datetime.now(timezone.utc),
                        "type": "debt_repayment"
                    }
                    
                    # 記錄到點數歷史
                    await self.db[Collections.POINT_LOGS].insert_one(repay_log, session=session)
                    
                    return {
                        'success': True,
                        'message': f'已償還 {repay_amount} 點欠款',
                        'repaid_amount': repay_amount,
                        'remaining_debt': remaining_debt,
                        'account_unfrozen': remaining_debt == 0
                    }
                    
        except Exception as e:
            logger.error(f"Error repaying debt for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'償還欠款失敗: {str(e)}'
            }
    
    async def add_debt(self, user_id: ObjectId, amount: int, reason: str, admin_id: Optional[ObjectId] = None) -> Dict[str, Any]:
        """
        添加欠款（管理員功能）
        
        Args:
            user_id: 用戶ID
            amount: 欠款金額
            reason: 欠款原因
            admin_id: 管理員ID
            
        Returns:
            dict: 添加結果
        """
        try:
            async with await self.db.client.start_session() as session:
                async with session.start_transaction():
                    user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
                    
                    if not user:
                        return {
                            'success': False,
                            'message': '使用者不存在'
                        }
                    
                    if amount <= 0:
                        return {
                            'success': False,
                            'message': '欠款金額必須大於 0'
                        }
                    
                    current_debt = user.get("owed_points", 0)
                    new_debt = current_debt + amount
                    
                    # 更新用戶資料
                    await self.db[Collections.USERS].update_one(
                        {"_id": user_id},
                        {
                            "$inc": {"owed_points": amount},
                            "$set": {
                                "frozen": True,  # 有欠款時自動凍結
                                "updated_at": datetime.now(timezone.utc)
                            }
                        },
                        session=session
                    )
                    
                    # 記錄欠款歷史
                    debt_log = {
                        "user_id": user_id,
                        "admin_id": admin_id,
                        "debt_amount": amount,
                        "reason": reason,
                        "previous_debt": current_debt,
                        "new_debt": new_debt,
                        "timestamp": datetime.now(timezone.utc),
                        "type": "debt_added"
                    }
                    
                    await self.db[Collections.POINT_LOGS].insert_one(debt_log, session=session)
                    
                    return {
                        'success': True,
                        'message': f'已添加 {amount} 點欠款',
                        'added_amount': amount,
                        'total_debt': new_debt,
                        'account_frozen': True
                    }
                    
        except Exception as e:
            logger.error(f"Error adding debt for user {user_id}: {e}")
            return {
                'success': False,
                'message': f'添加欠款失敗: {str(e)}'
            }
    
    async def get_all_debtors(self) -> Dict[str, Any]:
        """
        獲取所有有欠款的用戶列表
        
        Returns:
            dict: 欠款用戶列表
        """
        try:
            debtors_cursor = self.db[Collections.USERS].find(
                {"owed_points": {"$gt": 0}},
                {
                    "_id": 1,
                    "id": 1,
                    "name": 1,
                    "points": 1,
                    "owed_points": 1,
                    "frozen": 1,
                    "enabled": 1,
                    "team": 1,
                    "updated_at": 1
                }
            ).sort("owed_points", -1)
            
            debtors = []
            total_debt = 0
            
            async for user in debtors_cursor:
                owed_points = user.get("owed_points", 0)
                total_debt += owed_points
                
                debtors.append({
                    "user_id": str(user["_id"]),
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "points": user.get("points", 0),
                    "owed_points": owed_points,
                    "available_balance": user.get("points", 0) - owed_points,
                    "frozen": user.get("frozen", False),
                    "enabled": user.get("enabled", True),
                    "team": user.get("team"),
                    "updated_at": user.get("updated_at")
                })
            
            return {
                'success': True,
                'debtors': debtors,
                'total_debtors': len(debtors),
                'total_debt': total_debt
            }
            
        except Exception as e:
            logger.error(f"Error getting debtors list: {e}")
            return {
                'success': False,
                'message': f'獲取欠款用戶列表失敗: {str(e)}',
                'debtors': [],
                'total_debtors': 0,
                'total_debt': 0
            }


# 依賴注入
def get_debt_service() -> DebtService:
    """獲取債務管理服務實例"""
    from app.core.database import get_database
    db = get_database()
    return DebtService(db)