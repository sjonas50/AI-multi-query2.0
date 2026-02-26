"""Simple JWT auth for small team use, with rate limiting."""

import time
from collections import defaultdict

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from backend.config import AUTH_SECRET, JWT_SECRET

security = HTTPBearer()

TOKEN_EXPIRY_SECONDS = 7 * 86400  # 7 days

# Rate limiting: max 5 login attempts per IP per 60 seconds
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 60
_login_attempts: dict[str, list[float]] = defaultdict(list)


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    token: str
    expires_in: int = TOKEN_EXPIRY_SECONDS


def create_token() -> str:
    return jwt.encode(
        {"exp": time.time() + TOKEN_EXPIRY_SECONDS, "iat": time.time()},
        JWT_SECRET,
        algorithm="HS256",
    )


def verify_password(password: str) -> bool:
    return password == AUTH_SECRET


def check_rate_limit(request: Request):
    """Check login rate limit for the requester's IP."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Prune old attempts outside the window
    _login_attempts[ip] = [
        t for t in _login_attempts[ip] if now - t < _LOGIN_WINDOW_SECONDS
    ]

    if len(_login_attempts[ip]) >= _LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again in 60 seconds.",
            headers={"Retry-After": str(_LOGIN_WINDOW_SECONDS)},
        )

    _login_attempts[ip].append(now)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
