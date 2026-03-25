"""AISEO company configuration endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import get_current_user, require_admin
from backend.services import company_config_service as ccs

router = APIRouter(prefix="/api/aiseo", tags=["aiseo"])


# --- Schemas ---


class CompanyConfigUpdate(BaseModel):
    target_company: Optional[str] = None
    company_domains: Optional[str] = None
    industry: Optional[str] = None
    analyze_responses: Optional[str] = None
    enable_enhanced_analysis: Optional[str] = None
    track_history: Optional[str] = None
    domain_classification: Optional[str] = None
    negative_signal_detection: Optional[str] = None
    accuracy_verification: Optional[str] = None
    weekly_reporting: Optional[str] = None


class CompetitorCreate(BaseModel):
    name: str
    domain: str


class AccuracyFactCreate(BaseModel):
    label: str
    field_key: str
    correct_value: str


# --- Endpoints ---


@router.get("/config")
async def get_aiseo_config(_user=Depends(get_current_user)):
    """Return full AISEO configuration."""
    config = ccs.get_config()
    competitors = ccs.list_competitors()
    facts = ccs.list_accuracy_facts()
    return {
        "config": config,
        "competitors": competitors,
        "accuracy_facts": facts,
    }


@router.put("/config")
async def update_aiseo_config(body: CompanyConfigUpdate, _user=Depends(require_admin)):
    """Update AISEO company configuration (admin only)."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    ccs.set_config(updates)
    return ccs.get_config()


@router.get("/competitors")
async def list_competitors(_user=Depends(get_current_user)):
    return {"competitors": ccs.list_competitors()}


@router.post("/competitors")
async def add_competitor(body: CompetitorCreate, _user=Depends(get_current_user)):
    try:
        competitor = ccs.add_competitor(body.name, body.domain)
        return competitor
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/competitors/{competitor_id}")
async def remove_competitor(competitor_id: int, _user=Depends(get_current_user)):
    if not ccs.remove_competitor(competitor_id):
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"ok": True}


@router.get("/accuracy-facts")
async def list_accuracy_facts(_user=Depends(get_current_user)):
    return {"facts": ccs.list_accuracy_facts()}


@router.post("/accuracy-facts")
async def add_accuracy_fact(body: AccuracyFactCreate, _user=Depends(get_current_user)):
    try:
        fact = ccs.add_accuracy_fact(body.label, body.field_key, body.correct_value)
        return fact
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/accuracy-facts/{fact_id}")
async def update_accuracy_fact(fact_id: int, body: AccuracyFactCreate, _user=Depends(get_current_user)):
    if not ccs.update_accuracy_fact(fact_id, body.label, body.field_key, body.correct_value):
        raise HTTPException(status_code=404, detail="Fact not found")
    return {"ok": True}


@router.delete("/accuracy-facts/{fact_id}")
async def remove_accuracy_fact(fact_id: int, _user=Depends(get_current_user)):
    if not ccs.remove_accuracy_fact(fact_id):
        raise HTTPException(status_code=404, detail="Fact not found")
    return {"ok": True}
