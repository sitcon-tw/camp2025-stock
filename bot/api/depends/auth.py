from os import environ

BACKEND_TOKEN = environ.get("BACKEND_TOKEN")

from fastapi import Header, HTTPException, status

def verify_backend_token(token: str = Header(...)):
    if token != BACKEND_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token is incorrect :D")
    return token