"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Request
from backend.auth import LoginRequest, TokenResponse, create_token, verify_password, check_rate_limit
from backend.routers import queries, providers, results, analysis, reports

app = FastAPI(title="AI Multi-Query", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    check_rate_limit(request)
    if not verify_password(body.password):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid password")
    return TokenResponse(token=create_token())


@app.get("/api/health")
async def health():
    return {"status": "ok"}
