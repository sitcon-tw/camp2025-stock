# 策略模式實作
# OCP 原則：開放擴充，關閉修改 - 新增策略不需修改現有程式碼
# Strategy Pattern：封裝演算法，使其可互換

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from decimal import Decimal
from .entities import StockOrder


class OrderExecutionStrategy(ABC):
    """
    訂單執行策略抽象基類
    OCP 原則：定義抽象介面，新增執行策略不需修改現有程式碼
    Strategy Pattern：封裝不同的訂單執行邏輯
    """
    
    @abstractmethod
    async def can_execute(self, order: StockOrder, market_data: dict) -> bool:
        """判斷訂單是否可執行"""
        pass
    
    @abstractmethod
    async def calculate_execution_price(self, order: StockOrder, market_data: dict) -> Decimal:
        """計算執行價格"""
        pass


class MarketOrderStrategy(OrderExecutionStrategy):
    """
    市價單執行策略
    SRP 原則：專注於市價單的執行邏輯
    """
    
    async def can_execute(self, order: StockOrder, market_data: dict) -> bool:
        """市價單總是可以執行（假設有流動性）"""
        return order.order_type == "market" and order.status == "pending"
    
    async def calculate_execution_price(self, order: StockOrder, market_data: dict) -> Decimal:
        """使用目前市場價格執行"""
        current_price = market_data.get("current_price")
        if not current_price:
            raise ValueError("market_price_not_available")
        return Decimal(str(current_price))


class LimitOrderStrategy(OrderExecutionStrategy):
    """
    限價單執行策略
    SRP 原則：專注於限價單的執行邏輯
    """
    
    async def can_execute(self, order: StockOrder, market_data: dict) -> bool:
        """限價單需要滿足價格條件"""
        if order.order_type != "limit" or order.status != "pending":
            return False
        
        current_price = market_data.get("current_price")
        if not current_price or not order.price:
            return False
        
        current_price = Decimal(str(current_price))
        
        if order.side == "buy":
            # 買入限價單：市價 <= 限價
            return current_price <= order.price
        else:  # sell
            # 賣出限價單：市價 >= 限價
            return current_price >= order.price
    
    async def calculate_execution_price(self, order: StockOrder, market_data: dict) -> Decimal:
        """使用限價作為執行價格"""
        if not order.price:
            raise ValueError("limit_price_not_set")
        return order.price


class StopLossOrderStrategy(OrderExecutionStrategy):
    """
    停損單執行策略
    OCP 原則：新增停損單策略，不需修改現有程式碼
    """
    
    async def can_execute(self, order: StockOrder, market_data: dict) -> bool:
        """停損單需要觸及停損價格"""
        if order.order_type != "stop_loss" or order.status != "pending":
            return False
        
        current_price = market_data.get("current_price")
        stop_price = order.price  # 假設 price 欄位存儲停損價格
        
        if not current_price or not stop_price:
            return False
        
        current_price = Decimal(str(current_price))
        
        if order.side == "sell":
            # 停損賣出：市價 <= 停損價
            return current_price <= stop_price
        else:  # buy (stop buy)
            # 停損買入：市價 >= 停損價
            return current_price >= stop_price
    
    async def calculate_execution_price(self, order: StockOrder, market_data: dict) -> Decimal:
        """停損單觸發後以市價執行"""
        current_price = market_data.get("current_price")
        if not current_price:
            raise ValueError("market_price_not_available")
        return Decimal(str(current_price))


class FeeCalculationStrategy(ABC):
    """
    手續費計算策略抽象基類
    OCP 原則：新增手續費計算方式不需修改現有程式碼
    """
    
    @abstractmethod
    def calculate_fee(self, amount: int, user_type: str = "regular") -> int:
        """計算手續費"""
        pass


class PercentageFeeStrategy(FeeCalculationStrategy):
    """
    百分比手續費策略
    SRP 原則：專注於百分比手續費計算
    """
    
    def __init__(self, percentage: float = 0.01, min_fee: int = 1):
        self.percentage = percentage
        self.min_fee = min_fee
    
    def calculate_fee(self, amount: int, user_type: str = "regular") -> int:
        """計算百分比手續費"""
        fee = max(self.min_fee, int(amount * self.percentage))
        
        # VIP 使用者可享受折扣
        if user_type == "vip":
            fee = int(fee * 0.5)
        
        return fee


class FixedFeeStrategy(FeeCalculationStrategy):
    """
    固定手續費策略
    SRP 原則：專注於固定手續費計算
    """
    
    def __init__(self, fixed_amount: int = 5):
        self.fixed_amount = fixed_amount
    
    def calculate_fee(self, amount: int, user_type: str = "regular") -> int:
        """計算固定手續費"""
        return self.fixed_amount


class TieredFeeStrategy(FeeCalculationStrategy):
    """
    階梯式手續費策略
    OCP 原則：新增階梯式手續費，不需修改現有程式碼
    """
    
    def __init__(self):
        self.tiers = [
            (1000, 1),      # 1000 以下收 1 點
            (10000, 5),     # 1000-10000 收 5 點
            (50000, 20),    # 10000-50000 收 20 點
            (float('inf'), 50)  # 50000 以上收 50 點
        ]
    
    def calculate_fee(self, amount: int, user_type: str = "regular") -> int:
        """計算階梯式手續費"""
        for threshold, fee in self.tiers:
            if amount <= threshold:
                return fee
        return self.tiers[-1][1]  # 預設使用最高階的手續費


class OrderMatchingStrategy(ABC):
    """
    訂單撮合策略抽象基類
    OCP 原則：支援不同的撮合演算法
    """
    
    @abstractmethod
    async def match_orders(self, buy_orders: list, sell_orders: list) -> list:
        """撮合買賣訂單"""
        pass


class FIFOMatchingStrategy(OrderMatchingStrategy):
    """
    先進先出撮合策略
    SRP 原則：專注於 FIFO 撮合邏輯
    """
    
    async def match_orders(self, buy_orders: list, sell_orders: list) -> list:
        """按時間順序撮合訂單"""
        matches = []
        
        # 按價格排序：買單價格高的優先，賣單價格低的優先
        buy_orders.sort(key=lambda x: (-float(x.price or 0), x.created_at))
        sell_orders.sort(key=lambda x: (float(x.price or float('inf')), x.created_at))
        
        i, j = 0, 0
        while i < len(buy_orders) and j < len(sell_orders):
            buy_order = buy_orders[i]
            sell_order = sell_orders[j]
            
            # 檢查價格是否符合
            if buy_order.price and sell_order.price and buy_order.price >= sell_order.price:
                # 計算撮合數量（取較小值）
                match_quantity = min(buy_order.quantity, sell_order.quantity)
                match_price = sell_order.price  # 使用賣方價格
                
                matches.append({
                    "buy_order": buy_order,
                    "sell_order": sell_order,
                    "quantity": match_quantity,
                    "price": match_price
                })
                
                # 更新訂單數量
                buy_order.quantity -= match_quantity
                sell_order.quantity -= match_quantity
                
                # 移除已完全撮合的訂單
                if buy_order.quantity == 0:
                    i += 1
                if sell_order.quantity == 0:
                    j += 1
            else:
                # 無法撮合，跳過價格較差的訂單
                if not buy_order.price or not sell_order.price:
                    break
                if buy_order.price < sell_order.price:
                    i += 1
                else:
                    j += 1
        
        return matches


class ProRataMatchingStrategy(OrderMatchingStrategy):
    """
    按比例撮合策略
    OCP 原則：新增撮合策略，不修改現有程式碼
    """
    
    async def match_orders(self, buy_orders: list, sell_orders: list) -> list:
        """按比例分配撮合數量"""
        # 簡化實作，實際可能需要更複雜的按比例分配邏輯
        return await FIFOMatchingStrategy().match_orders(buy_orders, sell_orders)