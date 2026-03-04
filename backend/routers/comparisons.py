"""Cross-provider comparison endpoints."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from backend.auth import get_current_user
from backend.models.schemas import ComparisonRequest
from backend.services.comparison_service import generate_comparison

router = APIRouter(prefix="/api/comparisons", tags=["comparisons"])


@router.post("")
async def create_comparison(request: ComparisonRequest, _user=Depends(get_current_user)):
    """Generate an AI-powered comparison of provider responses."""
    if len(request.responses) < 2:
        raise HTTPException(status_code=400, detail="At least 2 provider responses required")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, generate_comparison, request.query, request.responses
    )
    return result
