# 使用者投資組合應用服務
# 專注於使用者投資組合相關的業務流程

from typing import Optional, List
import logging

from app.core.base_classes import BaseApplicationService
from app.domain.user.repositories import UserRepository
from app.domain.trading.repositories import StockRepository, StockOrderRepository
from app.schemas.user import UserPortfolio, UserPointLog, UserStockOrder

logger = logging.getLogger(__name__)


class UserPortfolioApplicationService(BaseApplicationService):
    """
    使用者投資組合應用服務
    SRP 原則：專注於投資組合相關的應用邏輯
    """
    
    def __init__(
        self, 
        user_repository: UserRepository,
        stock_repository: StockRepository,
        stock_order_repository: StockOrderRepository
    ):
        super().__init__("UserPortfolioApplicationService")
        self.user_repository = user_repository
        self.stock_repository = stock_repository
        self.stock_order_repository = stock_order_repository
    
    async def get_user_portfolio(self, user_id: str) -> Optional[UserPortfolio]:
        """
        獲取使用者投資組合
        SRP 原則：專注於投資組合資料的組合
        """
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return None
            
            stock = await self.stock_repository.get_by_user_id(user_id)
            
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
            orders = await self.stock_order_repository.get_by_user_id(user_id, limit)
            
            return [
                UserStockOrder(
                    order_id=order.order_id,
                    order_type=order.order_type,
                    side=order.side,
                    quantity=self._get_display_quantity_from_entity(order),
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
    
    def _get_display_quantity_from_entity(self, order) -> int:
        """
        從 Domain 實體取得顯示數量
        
        對於已成交訂單，顯示成交數量；對於進行中訂單，顯示剩餘數量
        
        Args:
            order: StockOrder 實體
            
        Returns:
            顯示用的數量
        """
        if order.status == "filled":
            # 已成交訂單：顯示成交數量
            if hasattr(order, 'filled_quantity') and order.filled_quantity > 0:
                return order.filled_quantity
            elif order.quantity == 0:
                # 對於舊的訂單記錄，如果 quantity 為 0 且狀態是 filled
                # 檢查是否有其他可用的數量欄位
                if hasattr(order, 'original_quantity') and order.original_quantity:
                    return order.original_quantity
                else:
                    # 如果找不到真實數量資訊，記錄問題並返回 0
                    logger.warning(f"Order {order.order_id} has filled status but no quantity data")
                    return 0
            else:
                # 原始數量 = 目前剩餘 + 已成交
                filled_qty = getattr(order, 'filled_quantity', 0)
                return order.quantity + filled_qty
        else:
            # 進行中或部分成交訂單：顯示剩餘數量
            return order.quantity