"""Historical results browsing endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.auth import get_current_user
from backend.services import results_service

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("")
async def list_results(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    _user=Depends(get_current_user),
):
    return results_service.list_results(page=page, limit=limit, search=search)


@router.get("/{filename}")
async def get_result(filename: str, _user=Depends(get_current_user)):
    result = results_service.get_result(filename)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result
