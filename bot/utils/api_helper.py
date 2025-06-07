from os import environ
from typing import Dict

import httpx
from dotenv import load_dotenv

from utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()

BACKEND_URL = environ.get("BACKEND_URL")
BACKEND_TOKEN = environ.get("BACKEND_TOKEN")

if BACKEND_URL.endswith("/"):
    BACKEND_URL = BACKEND_URL[:-1]


def get(path, protected_route=False, **kwargs) -> Dict:
    headers = kwargs.get("headers", {}) or {}

    if protected_route:
        headers = headers.copy()
        headers["token"] = BACKEND_TOKEN

    response = httpx.get(f"{BACKEND_URL}{path}", headers=headers, **kwargs)
    _log_api_error(response, path)

    return response.json()


def post(path, protected_route=False, **kwargs) -> Dict:
    headers = kwargs.get("headers", {}) or {}

    if protected_route:
        headers = headers.copy()
        headers["token"] = BACKEND_TOKEN

    response = httpx.post(f"{BACKEND_URL}{path}", headers=headers, **kwargs)
    _log_api_error(response, path)

    return response.json()


def put(path, protected_route=False, **kwargs) -> Dict:
    headers = kwargs.get("headers", {}) or {}

    if protected_route:
        headers = headers.copy()
        headers["token"] = BACKEND_TOKEN

    response = httpx.put(f"{BACKEND_URL}{path}", headers=headers, **kwargs)
    _log_api_error(response, path)

    return response.json()


def delete(path, protected_route=False, **kwargs) -> Dict:
    headers = kwargs.get("headers", {}) or {}

    if protected_route:
        headers = headers.copy()
        headers["token"] = BACKEND_TOKEN

    response = httpx.delete(f"{BACKEND_URL}{path}", headers=headers, **kwargs)
    _log_api_error(response, path)

    return response.json()


def _log_api_error(response: httpx.Response, path):
    status_code = response.status_code

    if 200 <= status_code < 300:
        return
    logger.error(f"{path} returned status code {status_code}")
