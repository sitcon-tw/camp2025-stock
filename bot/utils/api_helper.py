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
        logger.error(f"Endpoint does not exist {path} (404)")
    elif status_code == 401:
        logger.error(f"Authentication failed {path} (401)")
    elif status_code == 403:
        logger.error(f"Unauthorized {path} (403)")
    elif status_code >= 500:
        logger.error(f"Backend server error {path} ({status_code})")
    else:
        logger.error(f"Failed to send request to backend {path} ({status_code})")


def test_backend_connection():
    logger.info("Testing connection with backend")
    logger.info(f"Backend URL: {BACKEND_URL}")
    logger.info(f"Authentication token: {'configured' if BACKEND_TOKEN else 'unset'}")

    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/bot/health",
            headers={"token": BACKEND_TOKEN},
            timeout=5.0
        )

        if response.status_code == 200:
            logger.info("Successfully connected to backend")

            health_data = response.json()
            logger.info(f"Backend status: {health_data.get('status', 'unknown')}")
            logger.info(f"Backend services: {health_data.get('service', 'unknown')}")
        else:
            logger.warning(f"Backend request error code: {response.status_code}")

    except httpx.ConnectError:
        logger.error("Unable to connect to backend")
    except httpx.TimeoutException:
        logger.error("Timeout when connecting to backend")
    except Exception as e:
        logger.error(f"An error occurred when connecting to backend: {e}")

    response = httpx.post(
        f"{BACKEND_URL}/api/bot/portfolio",
        headers={"token": BACKEND_TOKEN, "Content-Type": "application/json"},
        json={"from_user": "__test_connection__"},
        timeout=5.0
    )

    if response.status_code in [200, 404]:
        logger.info("Successfully tested backend authentication token")
    elif response.status_code == 401:
        logger.error("Unauthorized, please check backend authentication token")
    else:
        logger.warning(f"An error occurred when requesting test data: {response.status_code}")

