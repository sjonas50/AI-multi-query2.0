"""Saved searches / collections endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.services import collections_service

router = APIRouter(prefix="/api/collections", tags=["collections"])


class SaveRequest(BaseModel):
    result_filename: str
    query: str
    tags: list[str] = []
    notes: str = ""
    pinned: bool = False


class UpdateRequest(BaseModel):
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    pinned: Optional[bool] = None


@router.get("")
async def list_saved(
    tag: Optional[str] = None,
    pinned: bool = False,
    _user=Depends(get_current_user),
):
    items = collections_service.list_saved(tag=tag, pinned_only=pinned)
    return {"items": items}


@router.post("")
async def save_search(body: SaveRequest, _user=Depends(get_current_user)):
    item = collections_service.save_search(
        result_filename=body.result_filename,
        query=body.query,
        tags=body.tags,
        notes=body.notes,
        pinned=body.pinned,
    )
    return item


@router.put("/{item_id}")
async def update_search(item_id: str, body: UpdateRequest, _user=Depends(get_current_user)):
    item = collections_service.update_search(
        item_id=item_id,
        tags=body.tags,
        notes=body.notes,
        pinned=body.pinned,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Saved search not found")
    return item


@router.delete("/{item_id}")
async def delete_search(item_id: str, _user=Depends(get_current_user)):
    deleted = collections_service.delete_search(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved search not found")
    return {"status": "deleted"}


@router.get("/tags")
async def list_tags(_user=Depends(get_current_user)):
    tags = collections_service.get_all_tags()
    return {"tags": tags}
