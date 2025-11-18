"""Admin API endpoints."""

import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models import AdminBlocklist
from app.schemas.responses import BlocklistEntry, BlocklistResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class AddBlocklistRequest(BaseModel):
    """Request to add blocklist entry."""

    type: str  # 'phrase', 'author', 'ticker'
    value: str
    reason: str = ""


class RemoveBlocklistRequest(BaseModel):
    """Request to remove blocklist entry."""

    id: str


def verify_admin_token(authorization: str = Header(...)):
    """Verify admin authorization token."""
    settings = get_settings()

    # Expected format: "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization[7:]  # Remove "Bearer " prefix

    if token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    return token


@router.get("/admin/blocklist", response_model=BlocklistResponse)
def get_blocklist(
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token),
):
    """
    Get current blocklist entries.

    Requires admin authentication.
    """
    entries = db.query(AdminBlocklist).order_by(AdminBlocklist.added_at.desc()).all()

    entry_list = [
        BlocklistEntry(
            id=e.id,
            type=e.type,
            value=e.value,
            reason=e.reason,
            added_by=e.added_by,
            added_at=e.added_at,
        )
        for e in entries
    ]

    return BlocklistResponse(
        entries=entry_list,
        total=len(entry_list),
    )


@router.post("/admin/blocklist")
def add_blocklist_entry(
    request: AddBlocklistRequest,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token),
):
    """
    Add entry to blocklist.

    Requires admin authentication.
    """
    # Validate type
    if request.type not in ["phrase", "author", "ticker"]:
        raise HTTPException(status_code=400, detail="Invalid type")

    # Check if already exists
    existing = (
        db.query(AdminBlocklist)
        .filter(
            AdminBlocklist.type == request.type,
            AdminBlocklist.value == request.value,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Entry already exists")

    # Create entry
    entry = AdminBlocklist(
        id=str(uuid.uuid4()),
        type=request.type,
        value=request.value,
        reason=request.reason,
        added_by="admin",  # TODO: Get from auth context
        added_at=datetime.utcnow(),
    )

    db.add(entry)
    db.commit()

    logger.info(f"Added blocklist entry: {request.type}={request.value}")

    return {"status": "success", "id": entry.id}


@router.delete("/admin/blocklist")
def remove_blocklist_entry(
    request: RemoveBlocklistRequest,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token),
):
    """
    Remove entry from blocklist.

    Requires admin authentication.
    """
    entry = db.query(AdminBlocklist).filter(AdminBlocklist.id == request.id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()

    logger.info(f"Removed blocklist entry: {entry.type}={entry.value}")

    return {"status": "success"}
