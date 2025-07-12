"""
Public test endpoints for rate limiting functionality
"""
from fastapi import APIRouter, Request
from app.middleware.rate_limiter import rate_limiter
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/rate-limit/test",
    summary="測試 Rate Limiting",
    description="公開的測試端點，用於驗證 Rate Limiting 功能"
)
async def test_rate_limiting(request: Request) -> Dict:
    """測試 Rate Limiting 功能"""
    
    ip = rate_limiter.get_client_ip(request)
    
    return {
        "message": "Rate limiting test successful",
        "your_ip": ip,
        "is_banned": rate_limiter.is_ip_banned(ip),
        "stats": rate_limiter.get_stats()
    }

@router.get(
    "/rate-limit/simulate-fail",
    summary="模擬失敗嘗試",
    description="模擬管理員登入失敗，用於測試 IP 封鎖功能"
)
async def simulate_failed_attempt(request: Request) -> Dict:
    """模擬失敗嘗試以測試封鎖功能"""
    
    ip = rate_limiter.get_client_ip(request)
    
    # 記錄一次失敗嘗試
    rate_limiter.record_failed_attempt(ip, "/api/admin/login")
    
    return {
        "message": "Simulated failed attempt recorded",
        "your_ip": ip,
        "is_banned_now": rate_limiter.is_ip_banned(ip),
        "stats": rate_limiter.get_stats()
    }