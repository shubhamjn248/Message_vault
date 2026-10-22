import hmac
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic_auth = HTTPBasic()

def require_auth(credentials: HTTPBasicCredentials = Depends(basic_auth)) -> str:
    expected_user = os.getenv("APP_USERNAME")
    expected_password = os.getenv("APP_PASSWORD")
    user_ok = hmac.compare_digest(credentials.username.encode(), expected_user.encode())
    password_ok = hmac.compare_digest(credentials.password.encode(), expected_password.encode())
    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
