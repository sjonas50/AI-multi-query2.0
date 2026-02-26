"""Analysis and trends endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.auth import get_current_user
from backend.services import analysis_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/history")
async def get_analysis_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    provider: Optional[str] = None,
    q: Optional[str] = None,
    _user=Depends(get_current_user),
):
    return analysis_service.get_analysis_history(
        page=page, limit=limit, provider=provider, query_search=q
    )


@router.get("/trends")
async def get_trends(
    weeks: int = Query(4, ge=1, le=52),
    _user=Depends(get_current_user),
):
    return analysis_service.get_historical_trends(weeks)


@router.get("/domains")
async def get_domain_trends(_user=Depends(get_current_user)):
    return analysis_service.get_domain_trends()


@router.get("/competitors")
async def get_competitor_mentions(_user=Depends(get_current_user)):
    return analysis_service.get_competitor_mentions()
