"""Admin endpoints — invite codes and user management."""

from fastapi import APIRouter, Depends, HTTPException

from backend.auth import require_admin
from backend.models.schemas import InviteCreate
from backend.services import user_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


# --- Invite codes ---


@router.post("/invites")
async def create_invite(body: InviteCreate, admin: dict = Depends(require_admin)):
    code = user_service.create_invite(
        admin_id=admin["id"],
        email=body.email,
        expires_hours=body.expires_hours,
    )
    return {"code": code}


@router.get("/invites")
async def list_invites(admin: dict = Depends(require_admin)):
    return {"items": user_service.list_invites()}


@router.delete("/invites/{code}")
async def revoke_invite(code: str, admin: dict = Depends(require_admin)):
    if not user_service.delete_invite(code):
        raise HTTPException(status_code=404, detail="Invite not found or already used")
    return {"ok": True}


# --- Users ---


@router.get("/users")
async def list_users(admin: dict = Depends(require_admin)):
    return {"items": user_service.list_users()}


@router.delete("/users/{user_id}")
async def remove_user(user_id: str, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    if not user_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}
