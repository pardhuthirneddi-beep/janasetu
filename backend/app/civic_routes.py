from __future__ import annotations

import hashlib
import uuid
from pathlib import PurePosixPath

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import main as core

router = APIRouter()
MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024
SIGNATURES = {
    b"%PDF-": ("application/pdf", "pdf"),
    b"\x89PNG\r\n\x1a\n": ("image/png", "png"),
    b"\xff\xd8\xff": ("image/jpeg", "jpg"),
}


class AssignmentIn(BaseModel):
    staff_user_id: int = Field(gt=0)


@router.get("/api/v1/staff/me")
def staff_me(user=Depends(core.require_roles("staff", "reviewer", "admin"))):
    return {"authorized": True, "role": user.role, "displayName": user.display_name}


@router.get("/api/v1/staff/users")
def staff_users(user=Depends(core.require_roles("staff", "admin")), db: Session = Depends(core.get_db)):
    users = db.scalars(select(core.User).where(core.User.role.in_(("staff", "admin"))).order_by(core.User.display_name)).all()
    return {"items": [{"id": u.id, "displayName": u.display_name or f"Staff #{u.id}", "role": u.role} for u in users]}


@router.get("/api/v1/staff/overview")
def staff_overview(user=Depends(core.require_roles("staff", "reviewer", "admin")), db: Session = Depends(core.get_db)):
    counts = {key: value for key, value in db.execute(select(core.Grievance.status, func.count()).group_by(core.Grievance.status)).all()}
    return {
        "label": "JanSetu operational case counts only — not government statistics. No synthetic cases are included.",
        "governmentStatistics": False,
        "countsByStatus": counts,
        "total": sum(counts.values()),
    }


@router.post("/api/v1/staff/grievances/{reference}/assign")
def assign_case(reference: str, body: AssignmentIn, user=Depends(core.require_roles("staff", "admin")), db: Session = Depends(core.get_db)):
    grievance = db.scalar(select(core.Grievance).where(core.Grievance.reference == reference))
    if not grievance:
        raise HTTPException(404, "JanSetu grievance not found")
    target = db.get(core.User, body.staff_user_id)
    if not target or target.role not in ("staff", "admin"):
        raise HTTPException(422, "Target user is not a provisioned case handler")
    for previous in db.scalars(select(core.Assignment).where(core.Assignment.grievance_id == grievance.id, core.Assignment.active.is_(True))).all():
        previous.active = False
    db.add(core.Assignment(grievance_id=grievance.id, staff_id=target.id, assigned_by_id=user.id, active=True))
    grievance.assigned_to_id = target.id
    grievance.updated_at = core.now()
    core.audit(db, user, "case_assigned", "grievance", reference)
    db.commit()
    return {"reference": reference, "assignedTo": {"id": target.id, "displayName": target.display_name, "role": target.role}}


async def _presign(method: str, key: str) -> str:
    settings = core.settings
    if not settings.manus_api_url or not settings.manus_api_key:
        raise HTTPException(503, "Managed private storage is not configured")
    endpoint = settings.manus_api_url.rstrip("/") + f"/v1/storage/presign/{method}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(endpoint, params={"path": key}, headers={"Authorization": "Bearer " + settings.manus_api_key})
            response.raise_for_status()
            result = response.json()
    except Exception:
        raise HTTPException(502, "Managed storage could not issue an authorized transfer")
    url = result.get("url") if isinstance(result, dict) else None
    if not url:
        raise HTTPException(502, "Managed storage did not return a transfer URL")
    return url


def _sniff(payload: bytes) -> tuple[str, str] | None:
    for signature, metadata in SIGNATURES.items():
        if payload.startswith(signature):
            return metadata
    return None


@router.post("/api/v1/grievances/{reference}/attachments", status_code=201)
async def upload_attachment(reference: str, request: Request, file: UploadFile = File(...), user=Depends(core.require_roles("citizen")), db: Session = Depends(core.get_db)):
    grievance = core.owned_grievance(reference, user, db)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_ATTACHMENT_BYTES + 256 * 1024:
                raise HTTPException(413, "Attachments must be 8 MiB or smaller")
        except ValueError:
            raise HTTPException(400, "Invalid content-length")
    payload = await file.read(MAX_ATTACHMENT_BYTES + 1)
    if not payload:
        raise HTTPException(422, "Attachment is empty")
    if len(payload) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(413, "Attachments must be 8 MiB or smaller")
    detected = _sniff(payload)
    if not detected:
        raise HTTPException(415, "Allowed attachments are PDF, PNG, or JPEG with a valid file signature")
    content_type, extension = detected
    if file.content_type != content_type:
        raise HTTPException(415, "Declared content type does not match the file signature")
    key = f"attachments/{uuid.uuid4().hex}.{extension}"
    put_url = await _presign("put", key)
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            uploaded = await client.put(put_url, content=payload, headers={"Content-Type": content_type})
            uploaded.raise_for_status()
    except Exception:
        raise HTTPException(502, "The private attachment upload did not complete")
    file_name = PurePosixPath((file.filename or "attachment").replace("\\", "/")).name[:255] or "attachment"
    row = core.AttachmentMetadata(
        grievance_id=grievance.id,
        owner_id=user.id,
        storage_key=key,
        file_name=file_name,
        content_type=content_type,
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    db.add(row)
    core.audit(db, user, "private_attachment_uploaded", "grievance", reference)
    db.commit()
    return {"id": row.id, "fileName": row.file_name, "contentType": row.content_type, "sizeBytes": row.size_bytes, "downloadUrl": f"/api/v1/grievances/{reference}/attachments/{row.id}/download"}


@router.get("/api/v1/grievances/{reference}/attachments/{attachment_id}/download")
async def download_attachment(reference: str, attachment_id: int, user=Depends(core.current_user), db: Session = Depends(core.get_db)):
    grievance = core.owned_grievance(reference, user, db)
    row = db.scalar(select(core.AttachmentMetadata).where(core.AttachmentMetadata.id == attachment_id, core.AttachmentMetadata.grievance_id == grievance.id))
    if not row or (user.role == "citizen" and row.owner_id != user.id):
        raise HTTPException(404, "Attachment not found")
    signed_url = await _presign("get", row.storage_key)
    return RedirectResponse(signed_url, status_code=302)
