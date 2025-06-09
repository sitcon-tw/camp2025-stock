# 應用服務層
# Clean Architecture 原則：協調領域服務和基礎設施
# SRP 原則：每個應用服務專注於特定的用例

from typing import Optional, List, Tuple
from decimal import Decimal

from app.domain.services import (
    UserDomainService, StockTradingService, TransferService, IPOService
)
from app.core.base_classes import BaseApplicationService
from app.domain.repositories import (
    UserRepository, StockRepository, StockOrderRepository, 
    TransferRepository, MarketConfigRepository
)
from app.schemas.user import (
    UserLoginRequest, UserLoginResponse, UserRegistrationRequest, UserRegistrationResponse,
    StockOrderRequest, StockOrderResponse, TransferRequest, TransferResponse,
    UserPortfolio, UserPointLog, UserStockOrder
)
from app.core.security import create_access_token
import logging

logger = logging.getLogger(__name__)


class UserApplicationService(BaseApplicationService):
    """
    使用者應用服務
    SRP 原則：專注於使用者相關的應用邏輯
    Clean Architecture 原則：協調領域服務和外部介面
    """
    
    def __init__(self, user_domain_service: UserDomainService):
        super().__init__("UserApplicationService")
        self.user_domain_service = user_domain_service
    
    async def login_user(self, request: UserLoginRequest) -> UserLoginResponse:
        """
        使用者登入用例
        Clean Code 原則：函數名稱清楚表達意圖
        """
        try:
            user = await self.user_domain_service.authenticate_user(
                request.username, request.telegram_id
            )
            
            if not user:
                return UserLoginResponse(
                    success=False,
                    message="使用者不存在或未啟用"
                )
            
            # 生成 JWT Token
            token = create_access_token(data={"sub": user.user_id})
            
            return UserLoginResponse(
                success=True,
                token=token,
                user={
                    "id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "team": user.team,
                    "points": user.points
                }
            )
        except Exception as e:
            logger.error(f"Login failed for user {request.username}: {e}")
            return UserLoginResponse(success=False, message="登入失敗")
    
    async def register_user(self, request: UserRegistrationRequest) -> UserRegistrationResponse:
        """
        使用者註冊用例
        SRP 原則：專注於註冊流程的協調
        """
        try:
            user_id = await self.user_domain_service.register_user(
                request.username, request.email, request.team, request.telegram_id
            )
            
            return UserRegistrationResponse(
                success=True,
                message="註冊成功",
                user_id=user_id
            )
        except ValueError as e:
            error_messages = {
                "user_already_exists": "使用者名稱已存在",
            }
            message = error_messages.get(str(e), "註冊失敗")
            return UserRegistrationResponse(success=False, message=message)
        except Exception as e:
            logger.error(f"Registration failed for user {request.username}: {e}")
            return UserRegistrationResponse(success=False, message="註冊失敗")


class TradingApplicationService(BaseApplicationService):
    """
    交易應用服務
    SRP 原則：專注於交易相關的應用邏輯
    """
    
    def __init__(self, trading_service: StockTradingService, user_repo: UserRepository, 
                 stock_repo: StockRepository, order_repo: StockOrderRepository):
        super().__init__("TradingApplicationService")
        self.trading_service = trading_service
        self.user_repo = user_repo
        self.stock_repo = stock_repo
        self.order_repo = order_repo
    
    async def place_stock_order(self, user_id: str, request: StockOrderRequest) -> StockOrderResponse:
        """
        下股票訂單用例
        Clean Code 原則：使用明確的命名和參數
        """
        try:
            price = Decimal(str(request.price)) if request.price else None
            order_id, executed_price = await self.trading_service.place_order(
                user_id, request.order_type, request.side, request.quantity, price
            )
            
            if executed_price:
                # 市價單立即成交
                return StockOrderResponse(
                    success=True,
                    order_id=order_id,
                    message="訂單已成交",
                    executed_price=int(executed_price),
                    executed_quantity=request.quantity
                )
            else:
                # 限價單等待撮合
                return StockOrderResponse(
                    success=True,
                    order_id=order_id,
                    message="限價單已提交，等待撮合"
                )
        
        except ValueError as e:
            error_messages = {
                "invalid_order_type": "無效的訂單類型",
                "invalid_side": "無效的交易方向",
                "invalid_quantity": "無效的數量",
                "invalid_price_for_limit_order": "限價單必須指定價格",
                "user_not_found": "使用者不存在",
                "insufficient_points": "點數不足",
                "insufficient_stocks": "持股不足"
            }
            message = error_messages.get(str(e), "下單失敗")
            return StockOrderResponse(success=False, order_id=None, message=message)
        
        except Exception as e:
            logger.error(f"Order placement failed for user {user_id}: {e}")
            return StockOrderResponse(success=False, order_id=None, message="下單失敗")
    
    async def get_user_portfolio(self, user_id: str) -> Optional[UserPortfolio]:
        """
        獲取使用者投資組合
        SRP 原則：專注於投資組合資料的組合
        """
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                return None
            
            stock = await self.stock_repo.get_by_user_id(user_id)
            
            if stock:
                # 假設目前市價為平均成本（實際應該從市場價格服務獲取）
                current_price = float(stock.avg_cost)
                stock_value = int(stock.quantity * current_price)
                total_value = user.points + stock_value
                
                return UserPortfolio(
                    username=user.username,
                    points=user.points,
                    stocks=stock.quantity,
                    stockValue=stock_value,
                    totalValue=total_value,
                    avgCost=float(stock.avg_cost)
                )
            else:
                return UserPortfolio(
                    username=user.username,
                    points=user.points,
                    stocks=0,
                    stockValue=0,
                    totalValue=user.points,
                    avgCost=0.0
                )
        
        except Exception as e:
            logger.error(f"Failed to get portfolio for user {user_id}: {e}")
            return None
    
    async def get_user_orders(self, user_id: str, limit: int = 20) -> List[UserStockOrder]:
        """
        獲取使用者訂單歷史
        Clean Code 原則：函數參數有合理的預設值
        """
        try:
            orders = await self.order_repo.get_by_user_id(user_id, limit)
            
            return [
                UserStockOrder(
                    order_id=order.order_id,
                    order_type=order.order_type,
                    side=order.side,
                    quantity=order.quantity,
                    price=int(order.price) if order.price else None,
                    status=order.status,
                    created_at=order.created_at.isoformat() if order.created_at else "",
                    executed_at=order.executed_at.isoformat() if order.executed_at else None
                )
                for order in orders
            ]
        
        except Exception as e:
            logger.error(f"Failed to get orders for user {user_id}: {e}")
            return []


class TransferApplicationService(BaseApplicationService):
    """
    轉帳應用服務
    SRP 原則：專注於轉帳相關的應用邏輯
    """
    
    def __init__(self, transfer_service: TransferService, transfer_repo: TransferRepository):
        super().__init__("TransferApplicationService")
        self.transfer_service = transfer_service
        self.transfer_repo = transfer_repo
    
    async def transfer_points(self, from_user_id: str, request: TransferRequest) -> TransferResponse:
        """
        點數轉帳用例
        Clean Code 原則：參數和返回值類型明確
        """
        try:
            transfer_id = await self.transfer_service.transfer_points(
                from_user_id, request.to_username, request.amount, request.note
            )
            
            # 獲取轉帳記錄以取得手續費資訊
            transfer = await self.transfer_repo.get_by_id(transfer_id)
            fee = transfer.fee if transfer else 0
            
            return TransferResponse(
                success=True,
                message="轉帳成功",
                transaction_id=transfer_id,
                fee=fee
            )
        
        except ValueError as e:
            error_messages = {
                "invalid_amount": "無效的轉帳金額",
                "from_user_not_found": "轉出使用者不存在",
                "to_user_not_found": "收款使用者不存在",
                "cannot_transfer_to_self": "不能轉帳給自己",
                "insufficient_points_with_fee": "點數不足（含手續費）"
            }
            message = error_messages.get(str(e), "轉帳失敗")
            return TransferResponse(success=False, message=message)
        
        except Exception as e:
            logger.error(f"Transfer failed from user {from_user_id}: {e}")
            return TransferResponse(success=False, message="轉帳失敗")


class IPOApplicationService(BaseApplicationService):
    """
    IPO 應用服務
    SRP 原則：專注於 IPO 相關的應用邏輯
    """
    
    def __init__(self, ipo_service: IPOService):
        super().__init__("IPOApplicationService")
        self.ipo_service = ipo_service
    
    async def purchase_ipo_shares(self, user_id: str, quantity: int) -> StockOrderResponse:
        """
        購買 IPO 股份用例
        DDD 原則：將複雜的 IPO 業務邏輯封裝在領域服務中
        """
        try:
            total_cost, ipo_price = await self.ipo_service.purchase_ipo_shares(user_id, quantity)
            
            return StockOrderResponse(
                success=True,
                order_id=None,  # IPO 不產生訂單ID
                message=f"IPO 購買成功，共花費 {total_cost} 點",
                executed_price=int(ipo_price),
                executed_quantity=quantity
            )
        
        except ValueError as e:
            error_messages = {
                "invalid_quantity": "無效的數量",
                "ipo_not_available": "IPO 不可用",
                "insufficient_ipo_shares": "IPO 股份不足",
                "user_not_found": "使用者不存在",
                "insufficient_points": "點數不足"
            }
            message = error_messages.get(str(e), "IPO 購買失敗")
            return StockOrderResponse(success=False, order_id=None, message=message)
        
        except Exception as e:
            logger.error(f"IPO purchase failed for user {user_id}: {e}")
            return StockOrderResponse(success=False, order_id=None, message="IPO 購買失敗")