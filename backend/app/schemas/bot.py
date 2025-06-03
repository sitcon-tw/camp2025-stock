from pydantic import BaseModel, Field, validator
from typing import Optional
from app.schemas.user import (
    UserRegistrationResponse, UserPortfolio, StockOrderResponse,
    TransferResponse, UserPointLog, UserStockOrder
)


# ========== BOT 專用請求模型 ==========

class BotUserRegistrationRequest(BaseModel):
    """BOT 使用者註冊請求 - 包含 from_user"""
    from_user: str = Field(..., min_length=2, max_length=50, description="要註冊的使用者名稱")
    email: Optional[str] = Field(None, description="電子郵件")
    team: str = Field(..., description="隊伍名稱")
    activation_code: Optional[str] = Field(None, description="啟用代碼")
    telegram_id: Optional[int] = Field(None, description="Telegram ID")
    
    @validator('email')
    def validate_email(cls, v):
        if v is None:
            return v
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v


class BotStockOrderRequest(BaseModel):
    """BOT 股票訂單請求 - 包含 from_user"""
    from_user: str = Field(..., description="使用者名稱")
    order_type: str = Field(..., description="訂單類型：market 或 limit")
    side: str = Field(..., description="買賣方向：buy 或 sell")
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


class BotTransferRequest(BaseModel):
    """BOT 轉帳請求 - 包含 from_user"""
    from_user: str = Field(..., description="轉帳發起人使用者名")
    to_username: str = Field(..., description="收款人使用者名")
    amount: int = Field(..., gt=0, description="轉帳金額")
    note: Optional[str] = Field(None, max_length=200, description="備註")


# ========== BOT 查詢請求模型 ==========

class BotPortfolioRequest(BaseModel):
    """BOT 查詢投資組合請求"""
    from_user: str = Field(..., description="使用者名稱")


class BotPointHistoryRequest(BaseModel):
    """BOT 查詢點數記錄請求"""
    from_user: str = Field(..., description="使用者名稱")
    limit: int = Field(default=50, gt=0, le=100, description="查詢筆數限制")


class BotStockOrdersRequest(BaseModel):
    """BOT 查詢股票訂單請求"""
    from_user: str = Field(..., description="使用者名稱")
    limit: int = Field(default=50, gt=0, le=100, description="查詢筆數限制")


class BotProfileRequest(BaseModel):
    """BOT 查詢使用者資料請求"""
    from_user: str = Field(..., description="使用者名稱")
