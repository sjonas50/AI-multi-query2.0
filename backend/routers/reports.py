"""Reports endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from backend.auth import get_current_user
from backend.services import results_service, analysis_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
async def list_reports(_user=Depends(get_current_user)):
    return results_service.list_reports()


@router.get("/{filename}")
async def get_report(filename: str, _user=Depends(get_current_user)):
    content = results_service.get_report(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"filename": filename, "content": content}


@router.post("/generate")
async def generate_report(_user=Depends(get_current_user)):
    path = analysis_service.generate_weekly_report()
    if not path:
        raise HTTPException(status_code=500, detail="Failed to generate report. Ensure enhanced analysis modules are available.")
    return {"path": path}
