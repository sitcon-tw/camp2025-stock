# 領域服務 (Domain Services)
# SRP 原則：每個服務專注於特定的業務邏輯
# DDD 原則：包含不屬於特定實體的業務邏輯

from typing import Optional, Tuple
from decimal import Decimal
from datetime import datetime
import uuid
import logging
import requests

from .entities import User, Stock, StockOrder, Transfer
from .repositories import (
    UserRepository, StockRepository, StockOrderRepository, 
    TransferRepository, MarketConfigRepository
)
from .strategies import (
    OrderExecutionStrategy, MarketOrderStrategy, LimitOrderStrategy,
    FeeCalculationStrategy, PercentageFeeStrategy
)
import hashlib
import hmac
from app.core.config_refactored import config

logger = logging.getLogger(__name__)


class AuthenticationDomainService:
    """
    認證領域服務
    SRP 原則：專注於認證相關的業務邏輯
    包含 Telegram OAuth 驗證等認證規則
    """
    
    def verify_telegram_oauth(self, auth_data: dict, bot_token: str) -> bool:
        """
        驗證 Telegram OAuth 認證資料
        領域邏輯：按照 Telegram 官方規範驗證資料完整性
        """
        # 取得 hash 值
        received_hash = auth_data.pop('hash', None)
        if not received_hash:
            logger.debug("No hash provided in auth data")
            return False
        
        # 準備驗證字串 - 排除 None 值的欄位，測試
        auth_data_items = []
        for key, value in sorted(auth_data.items()):
            if value is not None:
                auth_data_items.append(f"{key}={value}")
        
        data_check_string = '\n'.join(auth_data_items)
        logger.debug(f"Data check string: {data_check_string}")
        
        # 計算預期的 hash
        logger.debug(f"Bot token length: {len(bot_token)}")
        logger.debug(f"Data check string bytes: {data_check_string.encode()}")
        
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        logger.debug(f"Secret key (first 10 bytes): {secret_key[:10].hex()}")
        
        expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        logger.debug(f"Expected hash: {expected_hash}")
        logger.debug(f"Received hash: {received_hash}")
        
        result = hmac.compare_digest(received_hash, expected_hash)
        logger.debug(f"Hash verification result: {result}")
        
        return result
    
    def validate_user_eligibility(self, user: Optional[User]) -> Tuple[bool, str]:
        """
        驗證使用者登入資格
        領域規則：檢查使用者是否存在且已啟用
        """
        if not user:
            return False, "使用者未註冊，請先透過 Telegram Bot 進行註冊"
        
        if not user.is_active:
            return False, "使用者帳號未啟用"
        
        return True, "驗證成功"


class UserDomainService:
    """
    使用者領域服務
    SRP 原則：專注於使用者相關的業務邏輯
    DIP 原則：依賴抽象介面而非具體實作
    """
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def authenticate_user(self, username: str, telegram_id: Optional[int] = None) -> Optional[User]:
        """
        驗證使用者身份
        Clean Code 原則：函數名稱清楚表達功能
        """
        user = await self.user_repo.get_by_username(username)
        
        if not user or not user.is_active:
            logger.warning(f"Authentication failed for user: {username}")
            return None
        
        # 如果提供了 telegram_id，需要驗證符合
        if telegram_id and user.telegram_id != telegram_id:
            logger.warning(f"Telegram ID mismatch for user: {username}")
            return None
        
        return user
    
    async def register_user(self, username: str, email: str, team: str, 
                          telegram_id: Optional[int] = None) -> str:
        """
        註冊新使用者
        SRP 原則：專注於使用者註冊邏輯
        """
        # 檢查使用者是否已存在
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise ValueError("user_already_exists")
        
        # 建立新使用者實體
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            team=team,
            points=100,  # 初始點數
            telegram_id=telegram_id,
            created_at=datetime.now()
        )
        
        return await self.user_repo.create(user)


class StockTradingService:
    """
    股票交易領域服務
    SRP 原則：專注於股票交易業務邏輯
    DIP 原則：依賴抽象介面
    OCP 原則：使用策略模式，支援不同執行策略而不修改核心邏輯
    """
    
    def __init__(self, user_repo: UserRepository, stock_repo: StockRepository, 
                 order_repo: StockOrderRepository, market_repo: MarketConfigRepository,
                 execution_strategies: dict = None):
        self.user_repo = user_repo
        self.stock_repo = stock_repo
        self.order_repo = order_repo
        self.market_repo = market_repo
        
        # OCP 原則：策略模式 - 可替換的執行策略
        self.execution_strategies = execution_strategies or {
            "market": MarketOrderStrategy(),
            "limit": LimitOrderStrategy()
        }
    
    async def place_order(self, user_id: str, order_type: str, side: str, 
                         quantity: int, price: Optional[Decimal] = None) -> Tuple[str, Optional[Decimal]]:
        """
        下股票訂單
        Clean Code 原則：函數參數清楚明確
        SRP 原則：專注於訂單處理邏輯
        """
        # 驗證訂單參數
        if order_type not in ["market", "limit"]:
            raise ValueError("invalid_order_type")
        if side not in ["buy", "sell"]:
            raise ValueError("invalid_side")
        if quantity <= 0:
            raise ValueError("invalid_quantity")
        if order_type == "limit" and (not price or price <= 0):
            raise ValueError("invalid_price_for_limit_order")
        
        # 獲取使用者和股票資訊
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("user_not_found")
        
        stock = await self.stock_repo.get_by_user_id(user_id)
        
        # 建立訂單實體
        order = StockOrder(
            order_id=str(uuid.uuid4()),
            user_id=user_id,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price,
            created_at=datetime.now()
        )
        
        # OCP 原則：使用策略模式決定是否立即執行
        strategy = self.execution_strategies.get(order_type)
        if not strategy:
            raise ValueError("unsupported_order_type")
        
        # 獲取市場資料
        market_data = {
            "current_price": await self.market_repo.get_market_price()
        }
        
        # 檢查是否可立即執行
        if await strategy.can_execute(order, market_data):
            execution_price = await strategy.calculate_execution_price(order, market_data)
            return await self._execute_order(order, execution_price, user, stock)
        
        # 無法立即執行，保存訂單等待撮合
        order_id = await self.order_repo.create(order)
        return order_id, None
    
    async def _execute_order(self, order: StockOrder, execution_price: Decimal, 
                           user: User, stock: Optional[Stock]) -> Tuple[str, Decimal]:
        """
        執行訂單
        SRP 原則：專注於訂單執行邏輯
        Clean Code 原則：私有方法明確標示
        """
        total_cost = execution_price * order.quantity
        
        if order.side == "buy":
            # 買入邏輯
            if not user.can_transfer(int(total_cost)):
                raise ValueError("insufficient_points")
            
            # 扣除點數
            user.deduct_points(int(total_cost))
            await self.user_repo.update_points(user.user_id, user.points)
            
            # 更新股票持倉
            if stock:
                stock.buy_shares(order.quantity, execution_price)
                await self.stock_repo.update_quantity(
                    user.user_id, stock.quantity, float(stock.avg_cost)
                )
            else:
                # 建立新的股票持倉
                new_stock = Stock(
                    user_id=user.user_id,
                    quantity=order.quantity,
                    avg_cost=execution_price,
                    updated_at=datetime.now()
                )
                await self.stock_repo.save(new_stock)
        
        else:  # sell
            # 賣出邏輯
            if not stock or not stock.can_sell(order.quantity):
                raise ValueError("insufficient_stocks")
            
            # 更新股票持倉
            stock.sell_shares(order.quantity)
            await self.stock_repo.update_quantity(
                user.user_id, stock.quantity, float(stock.avg_cost)
            )
            
            # 增加點數
            user.add_points(int(total_cost))
            await self.user_repo.update_points(user.user_id, user.points)
        
        # 更新訂單狀態
        order.execute(execution_price)
        order_id = await self.order_repo.create(order)
        
        # 傳送交易通知
        await self._send_trade_notification(
            user_id=user.user_id,
            action=order.side,
            quantity=order.quantity,
            price=float(execution_price),
            total_amount=float(total_cost),
            order_id=order_id
        )
        
        return order_id, execution_price

    async def _send_trade_notification(self, user_id: str, action: str, quantity: int, 
                                     price: float, total_amount: float, order_id: str):
        """傳送交易通知到 Telegram Bot"""
        try:
            if not config.external_services.telegram_bot_api_url or not config.security.internal_api_key:
                logger.warning("Telegram Bot API 設定不完整，跳過通知傳送")
                return
            
            # 獲取使用者的 Telegram ID
            user = await self.user_repo.get_by_id(user_id)
            if not user or not hasattr(user, 'telegram_id') or not user.telegram_id:
                logger.warning(f"無法傳送通知：使用者 {user_id} 未設定 telegram_id")
                return
            
            # 構建通知請求
            notification_url = f"{config.external_services.telegram_bot_api_url.rstrip('/')}/bot/notification/trade"
            
            payload = {
                "user_id": user.telegram_id,
                "action": action,
                "quantity": quantity,
                "price": price,
                "total_amount": total_amount,
                "order_id": order_id
            }
            
            headers = {
                "Content-Type": "application/json",
                "token": config.security.internal_api_key
            }
            
            # 傳送通知（設定短超時避免阻塞交易）
            response = requests.post(
                notification_url,
                json=payload,
                headers=headers,
                timeout=5  # 5秒超時
            )
            
            if response.status_code == 200:
                logger.info(f"成功傳送 {action} 交易通知給使用者 {user.telegram_id}")
            else:
                logger.warning(f"傳送交易通知失敗: HTTP {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"傳送交易通知超時，使用者: {user_id}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"傳送交易通知網路錯誤: {e}")
        except Exception as e:
            logger.error(f"傳送交易通知發生未預期錯誤: {e}")

    async def cancel_order(self, order_id: str, user_id: str, reason: str = "user_cancelled") -> bool:
        """
        取消訂單
        
        Args:
            order_id: 訂單 ID
            user_id: 使用者 ID (用於驗證擁有權)
            reason: 取消原因
            
        Returns:
            bool: 是否成功取消
            
        Raises:
            ValueError: 訂單不存在、無權限或無法取消
        """
        # 取得訂單
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("order_not_found")
        
        # 驗證使用者擁有權
        if order.user_id != user_id:
            raise ValueError("order_not_owned")
        
        # 詳細檢查是否可以取消
        if not order.can_cancel():
            raise ValueError(f"order_cannot_be_cancelled_status_{order.status}")
        
        # 檢查剩餘數量
        if order.quantity <= 0:
            raise ValueError("order_has_no_remaining_quantity")
        
        # 記錄取消操作詳情
        logger.info(f"準備取消訂單 - 訂單: {order_id}, 狀態: {order.status}, 類型: {order.order_type}, 數量: {order.quantity}, 使用者: {user_id}")
        
        # 取消訂單
        order.cancel(reason)
        
        # 更新資料庫 - 這裡應該使用原子操作，但目前的 repository 介面可能不支援
        # 在實際生產環境中，repository 層應該提供原子更新的方法
        await self.order_repo.update_status(
            order_id=order_id,
            status="cancelled",
            executed_price=None
        )
        
        logger.info(f"訂單已取消: {order_id}, 使用者: {user_id}, 原因: {reason}")
        
        # 發送取消通知
        await self._send_cancellation_notification(
            user_id=user_id,
            order_id=order_id,
            order_type=order.order_type,
            side=order.side,
            quantity=order.quantity,
            price=float(order.price) if order.price else 0.0,
            reason=reason
        )
        
        return True

    async def _send_cancellation_notification(self, user_id: str, order_id: str, 
                                            order_type: str, side: str, quantity: int,
                                            price: float, reason: str):
        """發送取消訂單通知"""
        try:
            if not config.external_services.telegram_bot_api_url or not config.security.internal_api_key:
                logger.warning("Telegram Bot API 設定不完整，跳過取消通知傳送")
                return
            
            # 獲取使用者的 Telegram ID
            user = await self.user_repo.get_by_id(user_id)
            if not user or not hasattr(user, 'telegram_id') or not user.telegram_id:
                logger.warning(f"無法傳送取消通知：使用者 {user_id} 未設定 telegram_id")
                return
            
            # 構建取消通知 (使用直接訊息而非特定格式)
            action_text = "買入" if side == "buy" else "賣出"
            type_text = "市價單" if order_type == "market" else "限價單"
            
            message = f"🚫 您的訂單已取消\n\n• 訂單號碼：{order_id}\n• 類型：{type_text}\n• 操作：{action_text}\n• 數量：{quantity}\n• 價格：{price:.2f}\n• 取消原因：{reason}"
            
            notification_url = f"{config.external_services.telegram_bot_api_url.rstrip('/')}/bot/direct/send"
            
            payload = {
                "user_id": user.telegram_id,
                "message": message,
                "parse_mode": "MarkdownV2"
            }
            
            headers = {
                "Content-Type": "application/json",
                "token": config.security.internal_api_key
            }
            
            response = requests.post(
                notification_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"成功傳送取消通知給使用者 {user.telegram_id}")
            else:
                logger.warning(f"傳送取消通知失敗: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"傳送取消通知發生錯誤: {e}")


class TransferService:
    """
    轉帳領域服務
    SRP 原則：專注於轉帳業務邏輯
    DIP 原則：依賴抽象介面
    OCP 原則：使用策略模式支援不同手續費計算方式
    """
    
    def __init__(self, user_repo: UserRepository, transfer_repo: TransferRepository,
                 fee_strategy: FeeCalculationStrategy = None):
        self.user_repo = user_repo
        self.transfer_repo = transfer_repo
        # OCP 原則：可替換的手續費計算策略
        self.fee_strategy = fee_strategy or PercentageFeeStrategy()
    
    async def transfer_points(self, from_user_id: str, to_username: str, 
                            amount: int, note: Optional[str] = None) -> str:
        """
        執行點數轉帳
        SRP 原則：專注於轉帳邏輯
        Clean Code 原則：參數命名清楚
        """
        if amount <= 0:
            raise ValueError("invalid_amount")
        
        # 獲取轉出和轉入使用者
        from_user = await self.user_repo.get_by_id(from_user_id)
        to_user = await self.user_repo.get_by_username(to_username)
        
        if not from_user:
            raise ValueError("from_user_not_found")
        if not to_user:
            raise ValueError("to_user_not_found")
        if from_user.user_id == to_user.user_id:
            raise ValueError("cannot_transfer_to_self")
        
        # OCP 原則：使用策略模式計算手續費
        fee = self.fee_strategy.calculate_fee(amount, "regular")  # 可根據使用者類型調整
        
        # 建立轉帳實體
        transfer = Transfer(
            transfer_id=str(uuid.uuid4()),
            from_user_id=from_user_id,
            to_user_id=to_user.user_id,
            amount=amount,
            fee=fee,
            note=note,
            created_at=datetime.now()
        )
        
        # 檢查餘額是否足夠（含手續費）
        total_deduction = transfer.get_total_deduction()
        if not from_user.can_transfer(total_deduction):
            raise ValueError("insufficient_points_with_fee")
        
        # 執行轉帳
        from_user.deduct_points(total_deduction)
        to_user.add_points(amount)
        
        # 更新使用者點數
        await self.user_repo.update_points(from_user.user_id, from_user.points)
        await self.user_repo.update_points(to_user.user_id, to_user.points)
        
        # 記錄轉帳
        transfer.execute()
        transfer_id = await self.transfer_repo.create(transfer)
        
        return transfer_id


class IPOService:
    """
    IPO 領域服務
    SRP 原則：專注於 IPO 相關業務邏輯
    DDD 原則：封裝 IPO 的複雜業務規則
    """
    
    def __init__(self, user_repo: UserRepository, stock_repo: StockRepository, 
                 market_repo: MarketConfigRepository):
        self.user_repo = user_repo
        self.stock_repo = stock_repo
        self.market_repo = market_repo
    
    async def purchase_ipo_shares(self, user_id: str, quantity: int) -> Tuple[int, Decimal]:
        """
        購買 IPO 股份
        SRP 原則：專注於 IPO 購買邏輯
        """
        if quantity <= 0:
            raise ValueError("invalid_quantity")
        
        # 獲取 IPO 設定
        ipo_config = await self.market_repo.get_ipo_config()
        if not ipo_config:
            raise ValueError("ipo_not_available")
        
        shares_remaining = ipo_config.get("shares_remaining", 0)
        ipo_price = Decimal(str(ipo_config.get("initial_price", 20)))
        
        if quantity > shares_remaining:
            raise ValueError("insufficient_ipo_shares")
        
        # 獲取使用者
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("user_not_found")
        
        total_cost = int(ipo_price * quantity)
        if not user.can_transfer(total_cost):
            raise ValueError("insufficient_points")
        
        # 執行 IPO 購買
        user.deduct_points(total_cost)
        await self.user_repo.update_points(user.user_id, user.points)
        
        # 更新股票持倉
        existing_stock = await self.stock_repo.get_by_user_id(user_id)
        if existing_stock:
            existing_stock.buy_shares(quantity, ipo_price)
            await self.stock_repo.update_quantity(
                user_id, existing_stock.quantity, float(existing_stock.avg_cost)
            )
        else:
            new_stock = Stock(
                user_id=user_id,
                quantity=quantity,
                avg_cost=ipo_price,
                updated_at=datetime.now()
            )
            await self.stock_repo.save(new_stock)
        
        # 更新 IPO 設定
        ipo_config["shares_remaining"] -= quantity
        await self.market_repo.update_ipo_config(ipo_config)
        
        return total_cost, ipo_price