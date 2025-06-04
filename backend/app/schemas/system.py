from pydantic import BaseModel, Field
from typing import List, Optional


# ========== 系統使用者管理相關模型 ==========

class StudentCreateRequest(BaseModel):
    """建立學員請求"""
    id: str = Field(..., description="學員ID（不會變更的唯一識別碼）")
    username: str = Field(..., description="學員姓名")


class StudentCreateResponse(BaseModel):
    """建立學員回應"""
    ok: bool = Field(..., description="是否成功")
    name: str = Field(..., description="學員姓名")


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


class StudentUpdateResponse(BaseModel):
    """學員資料更新回應"""
    ok: bool = Field(..., description="是否成功")
    message: str = Field(..., description="更新狀況")
    students: List[StudentInfo] = Field(..., description="學生列表")
