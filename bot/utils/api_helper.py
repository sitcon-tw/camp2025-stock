from os import environ
from typing import Dict

import httpx
from dotenv import load_dotenv

from utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()

BACKEND_URL = environ.get("BACKEND_URL")
BACKEND_TOKEN = environ.get("BACKEND_TOKEN") or environ.get("INTERNAL_API_KEY")

if BACKEND_URL.endswith("/"):
    BACKEND_URL = BACKEND_URL[:-1]


def get(path, protected_route=False, **kwargs) -> Dict:
    headers = kwargs.get("headers", {}) or {}

    if protected_route:
        headers = headers.copy()
        headers["token"] = BACKEND_TOKEN

    response = httpx.get(f"{BACKEND_URL}{path}", headers=headers, **kwargs)
    _log_api_error(response, path)

    try:
        return response.json()
    except Exception:
        # Return a standardized error response for non-JSON responses
        return {"detail": "error", "status_code": response.status_code}


def post(path, protected_route=False, **kwargs) -> Dict:
    headers = kwargs.get("headers", {}) or {}

    if protected_route:
        headers = headers.copy()
        headers["token"] = BACKEND_TOKEN

    response = httpx.post(f"{BACKEND_URL}{path}", headers=headers, **kwargs)
    _log_api_error(response, path)

    try:
        return response.json()
    except Exception:
        # Return a standardized error response for non-JSON responses
        return {"detail": "error", "status_code": response.status_code}


def put(path, protected_route=False, **kwargs) -> Dict:
    headers = kwargs.get("headers", {}) or {}

    if protected_route:
        headers = headers.copy()
        headers["token"] = BACKEND_TOKEN

    response = httpx.put(f"{BACKEND_URL}{path}", headers=headers, **kwargs)
    _log_api_error(response, path)

    try:
        return response.json()
    except Exception:
        # Return a standardized error response for non-JSON responses
        return {"detail": "error", "status_code": response.status_code}


def delete(path, protected_route=False, **kwargs) -> Dict:
    headers = kwargs.get("headers", {}) or {}

    if protected_route:
        headers = headers.copy()
        headers["token"] = BACKEND_TOKEN

    response = httpx.delete(f"{BACKEND_URL}{path}", headers=headers, **kwargs)
    _log_api_error(response, path)

    try:
        return response.json()
    except Exception:
        # Return a standardized error response for non-JSON responses
        return {"detail": "error", "status_code": response.status_code}


def _log_api_error(response: httpx.Response, path):
    status_code = response.status_code

    if 200 <= status_code < 300:
        return
    
    # 更友善的錯誤訊息
    if status_code == 404:
        logger.error(f"🌐 API 端點不存在: {path} (404)")
    elif status_code == 401:
        logger.error(f"🔒 API 認證失敗: {path} (401)")
    elif status_code == 403:
        logger.error(f"🚫 API 權限不足: {path} (403)")
    elif status_code >= 500:
        logger.error(f"💥 後端伺服器錯誤: {path} ({status_code})")
    else:
        logger.error(f"🌐 API 請求失敗: {path} ({status_code})")


def test_backend_connection():
    """測試與後端的連線狀態並記錄結果"""
    logger.info("🔗 正在測試與後端的連線...")
    logger.info(f"📡 後端 URL: {BACKEND_URL}")
    logger.info(f"🔑 認證 Token: {'已設定' if BACKEND_TOKEN else '未設定'}")
    
    try:
        # 測試健康檢查端點
        response = httpx.get(f"{BACKEND_URL}/api/bot/health", 
                           headers={"token": BACKEND_TOKEN},
                           timeout=5.0)
        
        if response.status_code == 200:
            logger.info("✅ 後端連線成功！")
            try:
                health_data = response.json()
                logger.info(f"🏥 後端狀態: {health_data.get('status', 'unknown')}")
                logger.info(f"📋 服務: {health_data.get('service', 'unknown')}")
            except:
                logger.info("✅ 後端連線成功（但回應格式異常）")
        else:
            logger.warning(f"⚠️ 後端回應異常狀態碼: {response.status_code}")
            
    except httpx.ConnectError:
        logger.error("❌ 無法連接到後端服務！請檢查後端是否正在運行")
    except httpx.TimeoutException:
        logger.error("❌ 連接後端超時！")
    except Exception as e:
        logger.error(f"❌ 連接後端時發生錯誤: {e}")
    
    # 測試一個需要認證的端點
    try:
        response = httpx.post(f"{BACKEND_URL}/api/bot/portfolio",
                            headers={"token": BACKEND_TOKEN, "Content-Type": "application/json"},
                            json={"from_user": "__test_connection__"},
                            timeout=5.0)
        
        if response.status_code in [200, 404]:  # 404 是預期的（測試使用者不存在）
            logger.info("✅ 後端 API 認證成功！")
        elif response.status_code == 401:
            logger.error("❌ 後端 API 認證失敗！請檢查 TOKEN 設定")
        else:
            logger.warning(f"⚠️ 後端 API 測試回應異常: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ 測試後端 API 認證時發生錯誤: {e}")
