"""
User Presentation Layer - API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.application.dependencies import get_user_application_service
from app.application.user.services import UserApplicationService
from app.schemas.user import (
    UserLoginRequest, UserLoginResponse, UserPortfolio,
    TransferRequest, TransferResponse,
    UserPointLog
)
from app.core.security import get_current_user
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request: UserLoginRequest,
    user_service: UserApplicationService = Depends(get_user_application_service)
):
    """使用者登入"""
    try:
        result = await user_service.login_user(request.telegram_id, request.username)
        
        if result["success"]:
            return UserLoginResponse(
                success=True,
                message=result["message"],
                user_id=result["user_id"],
                username=result["username"],
                points=result["points"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登入失敗"
        )


@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    user_service: UserApplicationService = Depends(get_user_application_service)
):
    """獲取使用者資料"""
    try:
        result = await user_service.get_user_profile(current_user["user_id"])
        
        if result["success"]:
            return result["user"]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取使用者資料失敗"
        )


@router.post("/transfer", response_model=TransferResponse)
async def transfer_points(
    request: TransferRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserApplicationService = Depends(get_user_application_service)
):
    """轉帳點數"""
    try:
        result = await user_service.transfer_points(
            from_user_id=current_user["user_id"],
            to_user_id=request.to_user_id,
            amount=request.amount,
            description=request.description or ""
        )
        
        if result["success"]:
            return TransferResponse(
                success=True,
                message=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="轉帳失敗"
        )


@router.get("/point-history", response_model=List[UserPointLog])
async def get_point_history(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    user_service: UserApplicationService = Depends(get_user_application_service)
):
    """獲取點數歷史"""
    try:
        result = await user_service.get_point_history(
            user_id=current_user["user_id"],
            skip=skip,
            limit=limit
        )
        
        if result["success"]:
            return [
                UserPointLog(
                    id=log["id"],
                    change_type=log["change_type"],
                    amount=log["amount"],
                    description=log["description"],
                    timestamp=log["timestamp"],
                    related_user_id=log["related_user_id"]
                )
                for log in result["logs"]
            ]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        logger.error(f"Get point history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取點數歷史失敗"
        )