from pydantic import BaseModel, Field
from typing import Optional

class ArcadeActionRequest(BaseModel):
    """遊戲廳操作請求"""
    from_user: str = Field(..., description="使用者id")
    amount: int = Field(..., description="點數金額", gt=0)
    game_type: str = Field(..., description="遊戲類型")
    note: Optional[str] = Field(None, description="操作備註")

class ArcadeActionResponse(BaseModel):
    """遊戲廳操作回應"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作訊息")
    balance_before: int = Field(..., description="操作前餘額")
    balance_after: int = Field(..., description="操作後餘額")
    transaction_id: Optional[str] = Field(None, description="交易ID")

class ArcadeHealthResponse(BaseModel):
    """遊戲廳健康檢查回應"""
    status: str = Field(..., description="服務狀態")
    service: str = Field(..., description="服務名稱")
    message: str = Field(..., description="服務訊息")