from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


# ========== 使用者註冊和認證相關模型 ==========

#　使用者註冊請求
class UserRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="使用者id")
    email: str = Field(..., description="電子郵件")
    team: str = Field(..., description="隊伍名稱")
    activation_code: Optional[str] = Field(None, description="啟用代碼")
    telegram_id: Optional[int] = Field(None, description="Telegram ID")
    
    @validator('email')
    def validate_email(cls, v):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v


# 使用者註冊回應
class UserRegistrationResponse(BaseModel):
    success: bool = Field(..., description="註冊是否成功")
    message: str = Field(..., description="回應訊息")
    user_id: Optional[str] = Field(None, description="使用者ID")


#　使用者登入請求
class UserLoginRequest(BaseModel):
    username: str = Field(..., description="使用者id")
    password: Optional[str] = Field(None, description="密碼（如果需要）")
    telegram_id: Optional[int] = Field(None, description="Telegram ID")


# 使用者登入回應
class UserLoginResponse(BaseModel):
    success: bool = Field(..., description="登入是否成功")
    token: Optional[str] = Field(None, description="使用者 Token")
    user: Optional[dict] = Field(None, description="使用者資訊")


# ========== Telegram OAuth 相關模型 ==========

class TelegramOAuthRequest(BaseModel):
    """Telegram OAuth 認證請求"""
    id: int = Field(..., description="Telegram 使用者 ID")
    first_name: str = Field(..., description="名字")
    last_name: Optional[str] = Field(None, description="姓氏")
    username: Optional[str] = Field(None, description="使用者名稱")
    photo_url: Optional[str] = Field(None, description="大頭照 URL")
    auth_date: int = Field(..., description="認證時間戳")
    hash: str = Field(..., description="認證雜湊值")


class TelegramOAuthResponse(BaseModel):
    """Telegram OAuth 認證回應"""
    success: bool = Field(..., description="認證是否成功")
    token: Optional[str] = Field(None, description="JWT Token")
    user: Optional[dict] = Field(None, description="使用者資訊")
    message: Optional[str] = Field(None, description="回應訊息")


# ========== 股票交易相關模型 ==========

# 股票下單請求
class StockOrderRequest(BaseModel):
    order_type: str = Field(..., description="訂單類型 (market, limit)")
    side: str = Field(..., description="交易方向 (buy, sell)")
    quantity: int = Field(..., gt=0, description="數量")
    price: Optional[int] = Field(None, gt=0, description="價格（元，限價單必填）")
    
    @validator('order_type')
    def validate_order_type(cls, v):
        if v not in ['market', 'limit']:
            raise ValueError('order_type must be "market" or "limit"')
        return v
    
    @validator('side')
    def validate_side(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError('side must be "buy" or "sell"')
        return v
    
    @validator('price')
    def validate_price_for_limit_order(cls, v, values):
        if values.get('order_type') == 'limit' and v is None:
            raise ValueError('Price is required for limit orders')
        return v


# 股票下單回應
class StockOrderResponse(BaseModel):
    success: bool = Field(..., description="下單是否成功")
    order_id: Optional[str] = Field(None, description="訂單ID")
    message: str = Field(..., description="回應訊息")
    executed_price: Optional[int] = Field(None, description="成交價格（元）")
    executed_quantity: Optional[int] = Field(None, description="成交數量")


# 使用者投資組合
class UserPortfolio(BaseModel):
    username: str = Field(..., description="使用者id")
    points: int = Field(..., description="可用點數餘額")
    escrow_amount: int = Field(0, description="圈存金額", alias="escrowAmount")
    total_balance: int = Field(..., description="總餘額 (可用+圈存)", alias="totalBalance")
    stocks: int = Field(..., description="持股數量")
    stock_value: int = Field(..., description="股票價值（元）", alias="stockValue")
    total_value: int = Field(..., description="總資產（元）", alias="totalValue")
    avg_cost: float = Field(..., description="平均成本（元）", alias="avgCost")
    
    class Config:
        populate_by_name = True


# 轉帳請求
class TransferRequest(BaseModel):
    to_username: str = Field(..., description="收款人使用者名")
    amount: int = Field(..., gt=0, description="轉帳金額")
    note: Optional[str] = Field(None, max_length=200, description="備註")


# 轉帳回應
class TransferResponse(BaseModel):
    success: bool = Field(..., description="轉帳是否成功")
    message: str = Field(..., description="回應訊息")
    transaction_id: Optional[str] = Field(None, description="交易ID")
    fee: Optional[int] = Field(None, description="手續費")


# PVP 挑戰請求
class PVPChallengeRequest(BaseModel):
    amount: int = Field(..., gt=0, description="挑戰金額")


# PVP 挑戰回應
class PVPChallengeResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    challenge_id: Optional[str] = Field(None, description="挑戰ID")
    message: str = Field(..., description="回應訊息")


# 接受 PVP 挑戰請求
class PVPAcceptRequest(BaseModel):
    challenge_id: str = Field(..., description="挑戰ID")


# PVP 結果
class PVPResult(BaseModel):
    success: bool = Field(..., description="是否成功")
    winner: Optional[str] = Field(None, description="勝利者")
    amount: Optional[int] = Field(None, description="金額")
    message: str = Field(..., description="結果訊息")


# ========== 使用者查詢相關模型 ==========

# 簡化的使用者基本資料（給一般使用者的 Web API）
class UserBasicInfo(BaseModel):
    username: str = Field(..., description="使用者id")
    telegram_id: Optional[int] = Field(None, description="Telegram ID")
    team: str = Field(..., description="隊伍名稱")
    
    class Config:
        populate_by_name = True

# 使用者點數記錄
class UserPointLog(BaseModel):
    type: str = Field(..., description="操作類型")
    amount: int = Field(..., description="點數變化")
    balance_after: int = Field(..., description="操作後餘額")
    note: str = Field(..., description="備註")
    created_at: str = Field(..., description="時間")


# 使用者股票訂單
class UserStockOrder(BaseModel):
    order_id: str = Field(..., description="訂單ID")
    user_id: str = Field(..., description="使用者ID")
    order_type: str = Field(..., description="訂單類型")
    side: str = Field(..., description="買賣方向")
    quantity: int = Field(..., description="數量")
    price: Optional[int] = Field(None, description="價格（元）")
    status: str = Field(..., description="狀態")
    created_at: str = Field(..., description="建立時間")
    executed_at: Optional[str] = Field(None, description="成交時間")
