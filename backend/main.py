"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import (
    TOKEN_EXPIRY_SECONDS,
    check_rate_limit,
    create_token,
    get_current_user,
)
from backend.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.routers import queries, providers, results, analysis, reports, collections, comparisons, admin, aiseo
from backend.services import user_service, company_config_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    user_service.init_db()
    company_config_service.init_db()
    yield


app = FastAPI(title="AI Multi-Query", version="1.0.0", lifespan=lifespan)

import os

_allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_extra = os.getenv("ALLOWED_ORIGINS", "")
if _extra:
    _allowed_origins.extend([o.strip() for o in _extra.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(queries.router)
app.include_router(providers.router)
app.include_router(results.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(collections.router)
app.include_router(comparisons.router)
app.include_router(admin.router)
app.include_router(aiseo.router)


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    check_rate_limit(request)
    user = user_service.authenticate(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"], user["role"])
    return TokenResponse(token=token, expires_in=TOKEN_EXPIRY_SECONDS, user=user)


@app.post("/api/auth/register", response_model=TokenResponse)
async def register(body: RegisterRequest, request: Request):
    check_rate_limit(request)
    try:
        user = user_service.redeem_invite(
            code=body.invite_code,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = create_token(user["id"], user["role"])
    return TokenResponse(token=token, expires_in=TOKEN_EXPIRY_SECONDS, user=user)


@app.get("/api/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user


@app.get("/api/health")
async def health():
    return {"status": "ok"}
