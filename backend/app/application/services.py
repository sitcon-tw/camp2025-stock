# 應用服務層
# Clean Architecture 原則：協調領域服務和基礎設施
# SRP 原則：每個應用服務專注於特定的用例

from typing import Optional, List, Tuple
from decimal import Decimal

from app.domain.services import (
    UserDomainService, StockTradingService, TransferService, IPOService,
    AuthenticationDomainService
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
                    message="使用者不存在或帳號未啟用"
                )
            
            # 產生 JWT Token
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
            # 檢查市場是否開放
            if not await self._is_market_open():
                return StockOrderResponse(
                    success=False,
                    order_id=None,
                    message="市場目前未開放交易"
                )
            
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
                "insufficient_stocks": "持股不足",
                "unsupported_order_type": "不支援的訂單類型"
            }
            error_str = str(e)
            message = error_messages.get(error_str, error_str)
            logger.error(f"Order validation failed for user {user_id}: {error_str}")
            return StockOrderResponse(success=False, order_id=None, message=message)
        
        except Exception as e:
            logger.error(f"Order placement failed for user {user_id}: {e}")
            return StockOrderResponse(success=False, order_id=None, message="下單失敗")
    
    async def _is_market_open(self) -> bool:
        """檢查市場是否開放交易"""
        try:
            from datetime import datetime, timezone, timedelta
            from app.core.database import database_manager
            from app.core.enums import Collections
            
            # 檢查預定時間
            market_config = await database_manager.db[Collections.MARKET_CONFIG].find_one(
                {"type": "market_hours"}
            )
            
            if not market_config or "openTime" not in market_config:
                # 如果沒有設定，預設市場開放
                return True
            
            # 取得目前台北時間 (UTC+8)
            taipei_tz = timezone(timedelta(hours=8))
            current_time = datetime.now(timezone.utc).astimezone(taipei_tz)
            current_hour = current_time.hour
            current_minute = current_time.minute
            current_seconds_of_day = current_hour * 3600 + current_minute * 60 + current_time.second
            
            # 檢查目前是否在任何一個開放時間段內
            for slot in market_config["openTime"]:
                # 將儲存的時間戳轉換為當日的秒數
                start_dt = datetime.fromtimestamp(slot["start"], tz=timezone.utc).astimezone(taipei_tz)
                end_dt = datetime.fromtimestamp(slot["end"], tz=timezone.utc).astimezone(taipei_tz)
                
                start_seconds = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
                end_seconds = end_dt.hour * 3600 + end_dt.minute * 60 + end_dt.second
                
                # 處理跨日情況（例如 23:00 到 01:00）
                if start_seconds <= end_seconds:
                    # 同一天內的時間段
                    if start_seconds <= current_seconds_of_day <= end_seconds:
                        return True
                else:
                    # 跨日時間段
                    if current_seconds_of_day >= start_seconds or current_seconds_of_day <= end_seconds:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check market status: {e}")
            # 出錯時預設開放，避免影響交易
            return True
    
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

    async def cancel_stock_order(self, user_id: str, order_id: str, reason: str = "user_cancelled") -> StockOrderResponse:
        """
        取消股票訂單用例
        
        Args:
            user_id: 使用者 ID
            order_id: 訂單 ID  
            reason: 取消原因
            
        Returns:
            StockOrderResponse: 取消結果
        """
        try:
            # 檢查市場是否開放取消操作（根據業務需求決定）
            # 通常取消操作在市場關閉時也應該允許
            
            success = await self.trading_service.cancel_order(user_id, order_id, reason)
            
            if success:
                return StockOrderResponse(
                    success=True,
                    order_id=order_id,
                    message="訂單已成功取消"
                )
            else:
                return StockOrderResponse(
                    success=False,
                    order_id=order_id,
                    message="取消訂單失敗"
                )
                
        except ValueError as e:
            # 處理業務邏輯錯誤
            error_messages = {
                "order_not_found": "訂單不存在",
                "order_not_owned": "您沒有權限取消此訂單",
                "order_cannot_be_cancelled_status_filled": "已成交的訂單無法取消",
                "order_cannot_be_cancelled_status_cancelled": "訂單已經被取消",
                "order_has_no_remaining_quantity": "訂單已無剩餘數量可取消",
            }
            
            error_str = str(e)
            if error_str.startswith("order_cannot_be_cancelled_status_"):
                status = error_str.replace("order_cannot_be_cancelled_status_", "")
                message = f"訂單狀態為 {status}，無法取消"
            else:
                message = error_messages.get(error_str, error_str)
            
            logger.warning(f"Order cancellation failed for user {user_id}, order {order_id}: {error_str}")
            return StockOrderResponse(success=False, order_id=order_id, message=message)
            
        except Exception as e:
            logger.error(f"Order cancellation failed for user {user_id}, order {order_id}: {e}")
            return StockOrderResponse(success=False, order_id=order_id, message="取消訂單時發生錯誤")


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


class AuthenticationApplicationService(BaseApplicationService):
    """
    認證應用服務
    SRP 原則：專注於認證相關的用例編排
    Clean Architecture 原則：協調領域服務和外部介面
    """
    
    def __init__(
        self, 
        auth_domain_service: AuthenticationDomainService,
        user_repo: UserRepository
    ):
        super().__init__("AuthenticationApplicationService")
        self.auth_domain_service = auth_domain_service
        self.user_repo = user_repo
    
    async def telegram_oauth_login(
        self, 
        auth_data: dict, 
        bot_token: str
    ) -> Tuple[bool, Optional[dict], str]:
        """
        Telegram OAuth 登入用例
        協調認證驗證、使用者查找和資格檢查
        
        Returns:
            (success, user_data, message)
        """
        try:
            # 1. 驗證 Telegram OAuth 資料
            logger.debug(f"Received auth data: {auth_data}")
            if not self.auth_domain_service.verify_telegram_oauth(auth_data.copy(), bot_token):
                logger.warning(f"Invalid Telegram auth data for user {auth_data.get('id')}")
                return False, None, "Invalid Telegram authentication data"
            
            # 2. 查找使用者
            telegram_id = auth_data.get('id')
            if not telegram_id:
                return False, None, "缺少 Telegram ID"
            
            user = await self.user_repo.get_by_telegram_id(telegram_id)
            
            # 3. 驗證使用者資格
            is_eligible, message = self.auth_domain_service.validate_user_eligibility(user)
            if not is_eligible:
                return False, None, message
            
            # 4. 準備使用者資訊（移除敏感資料）
            user_info = {
                "id": user.user_id,
                "name": user.username,
                "team": user.team,
                "points": user.points,
                "telegram_id": user.telegram_id
            }
            
            logger.info(f"Successful Telegram OAuth login for user: {user.user_id}")
            return True, user_info, "登入成功"
            
        except Exception as e:
            logger.error(f"Telegram OAuth error: {e}")
            return False, None, "認證過程發生錯誤"