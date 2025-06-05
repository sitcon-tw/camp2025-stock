from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService, get_user_service
from app.schemas.system import (
    StudentUpdateRequest, StudentUpdateResponse, StudentInfo,
    StudentActivationRequest, StudentActivationResponse
)
from app.core.security import verify_bot_token
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ========== 學員管理 API ==========

@router.post(
    "/users/activate",
    response_model=StudentActivationResponse,
    summary="啟用學員帳號",
    description="透過驗證碼啟用學員帳號（只需 ID 存在即可）"
)
async def activate_student(
    request: StudentActivationRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> StudentActivationResponse:
    """
    啟用學員帳號
    
    Args:
        request: 包含學員ID的啟用請求（name 可選）
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        啟用結果
    """
    try:
        # 啟用學員帳號（不驗證 name）
        result = await user_service.activate_student(request.id, request.telegram_id)
        
        return StudentActivationResponse(
            ok=result["ok"],
            message=result["message"]
        )
                
    except Exception as e:
        logger.error(f"學員啟用失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="啟用失敗，請聯繫管理員"
        )


@router.post(
    "/users/update",
    response_model=StudentUpdateResponse,
    summary="更新學員資料",
    description="批量更新學員姓名和組別"
)
async def update_students(
    request: StudentUpdateRequest,
    token_verified: bool = Depends(verify_bot_token),
    user_service: UserService = Depends(get_user_service)
) -> StudentUpdateResponse:
    """
    更新學員資料
    
    Args:
        request: 包含學員資料的更新請求
        token_verified: token 驗證結果（透過 header 傳入）
        
    Returns:
        更新結果和學生列表
    """
    try:
        # 將 Pydantic 模型轉換為字典列表
        student_data_dicts = [student.model_dump() for student in request.data]
        
        # 批量更新學員資料
        result = await user_service.update_students(student_data_dicts)
        
        if result["success"]:
            # 轉換學生列表格式
            students = [
                StudentInfo(
                    id=student["id"],
                    name=student["name"], 
                    team=student.get("team"),
                    enabled=student.get("enabled", False)
                )
                for student in result["students"]
            ]
            
            return StudentUpdateResponse(
                ok=True,
                message=result["message"],
                students=students
            )
        else:
            return StudentUpdateResponse(
                ok=False,
                message=result["message"],
                students=[]
            )
                
    except Exception as e:
        logger.error(f"學員更新失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失敗，請聯繫管理員"
        )
