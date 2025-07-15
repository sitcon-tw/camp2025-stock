"""
使用者狀態驗證中間件
處理使用者狀態檢查，包括凍結、欠款等情況
"""

import logging
from typing import Dict, Any, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import Collections

logger = logging.getLogger(__name__)


class UserValidationService:
    """使用者狀態驗證服務"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def validate_user_status(self, user_id: ObjectId, session=None) -> Dict[str, Any]:
        """
        驗證使用者狀態，包括凍結和欠款檢查
        
        Args:
            user_id: 使用者ID
            session: 資料庫session（可選）
            
        Returns:
            dict: 驗證結果
        """
        try:
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            
            if not user:
                return {
                    'valid': False,
                    'can_trade': False,
                    'can_transfer': False,
                    'message': '使用者不存在',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # 檢查帳戶是否啟用
            if not user.get("enabled", True):
                return {
                    'valid': False,
                    'can_trade': False,
                    'can_transfer': False,
                    'message': '帳戶未啟用',
                    'error_code': 'ACCOUNT_DISABLED',
                    'user_data': {
                        'name': user.get('name', 'Unknown'),
                        'points': user.get('points', 0),
                        'enabled': user.get('enabled', False)
                    }
                }
            
            # 檢查帳戶是否凍結
            if user.get("frozen", False):
                return {
                    'valid': False,
                    'can_trade': False,
                    'can_transfer': False,
                    'message': '帳戶已凍結',
                    'error_code': 'ACCOUNT_FROZEN',
                    'user_data': {
                        'name': user.get('name', 'Unknown'),
                        'points': user.get('points', 0),
                        'owed_points': user.get('owed_points', 0),
                        'frozen': True
                    }
                }
            
            # 檢查是否有欠款
            owed_points = user.get("owed_points", 0)
            if owed_points > 0:
                return {
                    'valid': False,
                    'can_trade': False,
                    'can_transfer': False,
                    'message': f'帳戶有欠款 {owed_points} 點，請先償還',
                    'error_code': 'HAS_DEBT',
                    'owed_points': owed_points,
                    'user_data': {
                        'name': user.get('name', 'Unknown'),
                        'points': user.get('points', 0),
                        'owed_points': owed_points,
                        'available_balance': user.get('points', 0) - owed_points
                    }
                }
            
            # 狀態正常
            return {
                'valid': True,
                'can_trade': True,
                'can_transfer': True,
                'message': '狀態正常',
                'error_code': None,
                'user_data': {
                    'name': user.get('name', 'Unknown'),
                    'points': user.get('points', 0),
                    'owed_points': 0,
                    'available_balance': user.get('points', 0),
                    'enabled': True,
                    'frozen': False
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating user status for {user_id}: {e}")
            return {
                'valid': False,
                'can_trade': False,
                'can_transfer': False,
                'message': f'驗證失敗: {str(e)}',
                'error_code': 'VALIDATION_ERROR'
            }
    
    async def validate_user_can_spend(self, user_id: ObjectId, amount: int, operation_type: str = "spend", session=None) -> Dict[str, Any]:
        """
        驗證使用者是否可以消費指定金額
        
        Args:
            user_id: 使用者ID
            amount: 消費金額
            operation_type: 操作類型（spend, transfer, trade等）
            session: 資料庫session（可選）
            
        Returns:
            dict: 驗證結果
        """
        try:
            # 首先檢查使用者狀態
            status_result = await self.validate_user_status(user_id, session)
            
            if not status_result['valid']:
                return {
                    'can_spend': False,
                    'message': status_result['message'],
                    'error_code': status_result['error_code'],
                    'user_data': status_result.get('user_data', {})
                }
            
            # 檢查金額是否有效
            if amount <= 0:
                return {
                    'can_spend': False,
                    'message': '金額必須大於 0',
                    'error_code': 'INVALID_AMOUNT',
                    'user_data': status_result['user_data']
                }
            
            # 檢查餘額是否足夠
            user_data = status_result['user_data']
            available_balance = user_data['available_balance']
            
            if available_balance < amount:
                return {
                    'can_spend': False,
                    'message': f'餘額不足。需要: {amount} 點，可用: {available_balance} 點',
                    'error_code': 'INSUFFICIENT_BALANCE',
                    'required_amount': amount,
                    'available_balance': available_balance,
                    'user_data': user_data
                }
            
            # 可以消費
            return {
                'can_spend': True,
                'message': f'可以進行 {operation_type} 操作',
                'error_code': None,
                'available_balance': available_balance,
                'user_data': user_data
            }
            
        except Exception as e:
            logger.error(f"Error validating spending for user {user_id}: {e}")
            return {
                'can_spend': False,
                'message': f'驗證失敗: {str(e)}',
                'error_code': 'VALIDATION_ERROR'
            }
    
    async def validate_user_can_trade(self, user_id: ObjectId, side: str, quantity: int, session=None) -> Dict[str, Any]:
        """
        驗證使用者是否可以進行交易
        
        Args:
            user_id: 使用者ID
            side: 交易方向（buy/sell）
            quantity: 交易數量
            session: 資料庫session（可選）
            
        Returns:
            dict: 驗證結果
        """
        try:
            # 檢查使用者狀態
            status_result = await self.validate_user_status(user_id, session)
            
            if not status_result['valid']:
                return {
                    'can_trade': False,
                    'message': status_result['message'],
                    'error_code': status_result['error_code'],
                    'user_data': status_result.get('user_data', {})
                }
            
            # 檢查交易參數
            if side not in ["buy", "sell"]:
                return {
                    'can_trade': False,
                    'message': '交易方向無效',
                    'error_code': 'INVALID_SIDE',
                    'user_data': status_result['user_data']
                }
            
            if quantity <= 0:
                return {
                    'can_trade': False,
                    'message': '交易數量必須大於 0',
                    'error_code': 'INVALID_QUANTITY',
                    'user_data': status_result['user_data']
                }
            
            # 對於賣單，檢查持股數量
            if side == "sell":
                stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user_id}, session=session)
                current_stocks = stock_holding.get("stock_amount", 0) if stock_holding else 0
                
                if current_stocks < quantity:
                    return {
                        'can_trade': False,
                        'message': f'持股不足。需要: {quantity} 股，持有: {current_stocks} 股',
                        'error_code': 'INSUFFICIENT_STOCKS',
                        'required_stocks': quantity,
                        'current_stocks': current_stocks,
                        'user_data': status_result['user_data']
                    }
            
            # 可以交易
            return {
                'can_trade': True,
                'message': f'可以進行 {side} 交易',
                'error_code': None,
                'user_data': status_result['user_data']
            }
            
        except Exception as e:
            logger.error(f"Error validating trading for user {user_id}: {e}")
            return {
                'can_trade': False,
                'message': f'交易驗證失敗: {str(e)}',
                'error_code': 'VALIDATION_ERROR'
            }
    
    async def get_user_trading_info(self, user_id: ObjectId, session=None) -> Dict[str, Any]:
        """
        獲取使用者交易相關訊息
        
        Args:
            user_id: 使用者ID
            session: 資料庫session（可選）
            
        Returns:
            dict: 使用者交易訊息
        """
        try:
            # 獲取使用者基本訊息
            user = await self.db[Collections.USERS].find_one({"_id": user_id}, session=session)
            if not user:
                return {
                    'success': False,
                    'message': '使用者不存在',
                    'user_exists': False
                }
            
            # 獲取持股訊息
            stock_holding = await self.db[Collections.STOCKS].find_one({"user_id": user_id}, session=session)
            current_stocks = stock_holding.get("stock_amount", 0) if stock_holding else 0
            
            # 計算可用餘額
            points = user.get("points", 0)
            owed_points = user.get("owed_points", 0)
            available_balance = points - owed_points
            
            return {
                'success': True,
                'user_exists': True,
                'user_id': str(user_id),
                'name': user.get('name', 'Unknown'),
                'points': points,
                'owed_points': owed_points,
                'available_balance': available_balance,
                'current_stocks': current_stocks,
                'enabled': user.get('enabled', True),
                'frozen': user.get('frozen', False),
                'can_trade': user.get('enabled', True) and not user.get('frozen', False) and owed_points == 0,
                'can_transfer': user.get('enabled', True) and not user.get('frozen', False) and owed_points == 0
            }
            
        except Exception as e:
            logger.error(f"Error getting user trading info for {user_id}: {e}")
            return {
                'success': False,
                'message': f'獲取使用者訊息失敗: {str(e)}',
                'user_exists': False
            }


# 依賴注入
def get_user_validation_service() -> UserValidationService:
    """獲取使用者驗證服務實例"""
    from app.core.database import get_database
    db = get_database()
    return UserValidationService(db)


# 快速驗證函數
async def quick_validate_user_can_spend(user_id: ObjectId, amount: int, operation_type: str = "spend") -> Dict[str, Any]:
    """
    快速驗證使用者是否可以消費
    
    Args:
        user_id: 使用者ID
        amount: 消費金額
        operation_type: 操作類型
        
    Returns:
        dict: 驗證結果
    """
    from app.core.database import get_database
    db = get_database()
    service = UserValidationService(db)
    return await service.validate_user_can_spend(user_id, amount, operation_type)


async def quick_validate_user_can_trade(user_id: ObjectId, side: str, quantity: int) -> Dict[str, Any]:
    """
    快速驗證使用者是否可以交易
    
    Args:
        user_id: 使用者ID
        side: 交易方向
        quantity: 交易數量
        
    Returns:
        dict: 驗證結果
    """
    from app.core.database import get_database
    db = get_database()
    service = UserValidationService(db)
    return await service.validate_user_can_trade(user_id, side, quantity)