"""JWT auth with per-user accounts, rate limiting, and admin guard."""

import time
from collections import defaultdict

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.config import JWT_SECRET
from backend.services import user_service

security = HTTPBearer()

TOKEN_EXPIRY_SECONDS = 7 * 86400  # 7 days

# Rate limiting: max 5 login attempts per IP per 60 seconds
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 60
_login_attempts: dict[str, list[float]] = defaultdict(list)


def create_token(user_id: str, role: str) -> str:
    return jwt.encode(
        {
            "sub": user_id,
            "role": role,
            "exp": time.time() + TOKEN_EXPIRY_SECONDS,
            "iat": time.time(),
        },
        JWT_SECRET,
        algorithm="HS256",
    )


def check_rate_limit(request: Request):
    """Check login rate limit for the requester's IP."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()

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
    """Decode JWT and return the user dict from the database."""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that ensures the current user is an admin."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
