"""
Trading Application Services
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.domain.trading.entities import Stock, StockOrder, UserStock, OrderType, OrderStatus
from app.domain.trading.repositories import StockRepository, OrderRepository, UserStockRepository
from app.domain.trading.services import TradingDomainService
from app.domain.user.repositories import UserRepository
from app.shared.exceptions import DomainException, ValidationException
import logging

logger = logging.getLogger(__name__)


class TradingApplicationService:
    """交易應用服務"""
    
    def __init__(
        self,
        stock_repository: StockRepository,
        order_repository: OrderRepository,
        user_stock_repository: UserStockRepository,
        user_repository: UserRepository
    ):
        self.stock_repository = stock_repository
        self.order_repository = order_repository
        self.user_stock_repository = user_stock_repository
        self.user_repository = user_repository
        self.domain_service = TradingDomainService(
            stock_repository=stock_repository,
            order_repository=order_repository,
            user_stock_repository=user_stock_repository,
            user_repository=user_repository
        )
    
    async def place_order(self, user_id: str, symbol: str, order_type: str, quantity: int, price: int) -> Dict[str, Any]:
        """下單"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationException("無效的使用者 ID")
            
            if not symbol or len(symbol.strip()) == 0:
                raise ValidationException("股票代碼不能為空")
            
            if order_type not in ["buy", "sell"]:
                raise ValidationException("訂單類型必須是 buy 或 sell")
            
            if quantity <= 0:
                raise ValidationException("數量必須大於 0")
            
            if price <= 0:
                raise ValidationException("價格必須大於 0")
            
            order = await self.domain_service.place_order(
                user_id=ObjectId(user_id),
                symbol=symbol.strip().upper(),
                order_type=OrderType(order_type),
                quantity=quantity,
                price=price
            )
            
            return {
                "success": True,
                "order": {
                    "id": str(order.id),
                    "user_id": str(order.user_id),
                    "symbol": order.symbol,
                    "order_type": order.order_type.value,
                    "quantity": order.quantity,
                    "price": order.price,
                    "status": order.status.value,
                    "created_at": order.created_at.isoformat() if order.created_at else None
                },
                "message": "下單成功"
            }
            
        except DomainException as e:
            logger.error(f"Domain error during place order: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during place order: {e}")
            return {
                "success": False,
                "message": "下單失敗，請稍後再試"
            }
    
    async def cancel_order(self, order_id: str, user_id: str) -> Dict[str, Any]:
        """取消訂單"""
        try:
            if not ObjectId.is_valid(order_id) or not ObjectId.is_valid(user_id):
                raise ValidationException("無效的 ID")
            
            success = await self.domain_service.cancel_order(
                order_id=ObjectId(order_id),
                user_id=ObjectId(user_id)
            )
            
            if success:
                return {
                    "success": True,
                    "message": "取消訂單成功"
                }
            else:
                return {
                    "success": False,
                    "message": "取消訂單失敗"
                }
                
        except DomainException as e:
            logger.error(f"Domain error during cancel order: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during cancel order: {e}")
            return {
                "success": False,
                "message": "取消訂單失敗，請稍後再試"
            }
    
    async def get_user_portfolio(self, user_id: str) -> Dict[str, Any]:
        """獲取使用者投資組合"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationException("無效的使用者 ID")
            
            portfolio = await self.domain_service.get_user_portfolio(ObjectId(user_id))
            
            return {
                "success": True,
                "portfolio": [
                    {
                        "symbol": stock.symbol,
                        "quantity": stock.quantity,
                        "average_price": stock.average_price,
                        "total_value": stock.total_value,
                        "created_at": stock.created_at.isoformat() if stock.created_at else None
                    }
                    for stock in portfolio
                ]
            }
            
        except DomainException as e:
            logger.error(f"Domain error getting portfolio: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting portfolio: {e}")
            return {
                "success": False,
                "message": "獲取投資組合失敗"
            }
    
    async def get_user_orders(self, user_id: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """獲取使用者訂單"""
        try:
            if not ObjectId.is_valid(user_id):
                raise ValidationException("無效的使用者 ID")
            
            orders = await self.domain_service.get_user_orders(ObjectId(user_id), skip, limit)
            
            return {
                "success": True,
                "orders": [
                    {
                        "id": str(order.id),
                        "symbol": order.symbol,
                        "order_type": order.order_type.value,
                        "quantity": order.quantity,
                        "price": order.price,
                        "filled_quantity": order.filled_quantity,
                        "remaining_quantity": order.remaining_quantity,
                        "status": order.status.value,
                        "created_at": order.created_at.isoformat() if order.created_at else None
                    }
                    for order in orders
                ]
            }
            
        except DomainException as e:
            logger.error(f"Domain error getting user orders: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting user orders: {e}")
            return {
                "success": False,
                "message": "獲取訂單失敗"
            }
    
    async def get_order_book(self, symbol: str) -> Dict[str, Any]:
        """獲取訂單簿"""
        try:
            if not symbol or len(symbol.strip()) == 0:
                raise ValidationException("股票代碼不能為空")
            
            order_book = await self.domain_service.get_order_book(symbol.strip().upper())
            
            return {
                "success": True,
                "order_book": {
                    "symbol": order_book["symbol"],
                    "buy_orders": [
                        {
                            "id": str(order.id),
                            "price": order.price,
                            "quantity": order.remaining_quantity,
                            "created_at": order.created_at.isoformat() if order.created_at else None
                        }
                        for order in order_book["buy_orders"]
                    ],
                    "sell_orders": [
                        {
                            "id": str(order.id),
                            "price": order.price,
                            "quantity": order.remaining_quantity,
                            "created_at": order.created_at.isoformat() if order.created_at else None
                        }
                        for order in order_book["sell_orders"]
                    ]
                }
            }
            
        except DomainException as e:
            logger.error(f"Domain error getting order book: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting order book: {e}")
            return {
                "success": False,
                "message": "獲取訂單簿失敗"
            }
    
    async def get_all_stocks(self) -> Dict[str, Any]:
        """獲取所有股票"""
        try:
            stocks = await self.stock_repository.find_all()
            
            return {
                "success": True,
                "stocks": [
                    {
                        "symbol": stock.symbol,
                        "name": stock.name,
                        "current_price": stock.current_price,
                        "available_shares": stock.available_shares,
                        "total_shares": stock.total_shares,
                        "updated_at": stock.updated_at.isoformat() if stock.updated_at else None
                    }
                    for stock in stocks
                ]
            }
            
        except Exception as e:
            logger.error(f"Unexpected error getting all stocks: {e}")
            return {
                "success": False,
                "message": "獲取股票列表失敗"
            }
    
    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """獲取股票資訊"""
        try:
            if not symbol or len(symbol.strip()) == 0:
                raise ValidationException("股票代碼不能為空")
            
            stock = await self.stock_repository.find_by_symbol(symbol.strip().upper())
            if not stock:
                raise DomainException("股票不存在")
            
            return {
                "success": True,
                "stock": {
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "current_price": stock.current_price,
                    "available_shares": stock.available_shares,
                    "total_shares": stock.total_shares,
                    "updated_at": stock.updated_at.isoformat() if stock.updated_at else None
                }
            }
            
        except DomainException as e:
            logger.error(f"Domain error getting stock info: {e}")
            return {
                "success": False,
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting stock info: {e}")
            return {
                "success": False,
                "message": "獲取股票資訊失敗"
            }