from pydantic import BaseModel, Field
from typing import List, Optional


# ========== 系統使用者管理相關模型 ==========


class StudentUpdateData(BaseModel):
    """學員更新資料"""
    id: str = Field(..., description="學員ID")
    name: str = Field(..., description="學員姓名")
    team: str = Field(..., description="學員組別")


class StudentUpdateRequest(BaseModel):
    """學員資料更新請求"""
    data: List[StudentUpdateData] = Field(..., description="學員資料列表")


class StudentInfo(BaseModel):
    """學員資訊"""
    id: str = Field(..., description="學員ID")
    name: str = Field(..., description="學員姓名")
    team: Optional[str] = Field(None, description="學員組別")
    enabled: bool = Field(False, description="是否已啟用")


class StudentUpdateResponse(BaseModel):
    """學員資料更新回應"""
    ok: bool = Field(..., description="是否成功")
    message: str = Field(..., description="更新狀況")
    students: List[StudentInfo] = Field(..., description="學生列表")


class StudentActivationRequest(BaseModel):
    """學員啟用請求"""
    id: str = Field(..., description="學員ID（驗證碼）")
    name: Optional[str] = Field("", description="學員姓名（可選，可為空字串）")
    telegram_id: str = Field(None, description="Telegram ID")


class StudentActivationResponse(BaseModel):
    """學員啟用回應"""
    ok: bool = Field(..., description="是否成功")
    message: str = Field(..., description="啟用結果訊息")
