from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.core.config import Settings, get_settings
from app.db.repositories.imports import ImportsRepository
from app.db.session import get_db
from app.services.imports import ImportsService

router = APIRouter(prefix="/v1/imports", tags=["imports"])


class CreateImportRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(min_length=64, max_length=64)


class CreateImportResponse(BaseModel):
    import_id: UUID
    upload_url: str
    upload_method: str
    expires_at: datetime
    max_size_bytes: int


class CompleteImportRequest(BaseModel):
    raw_text: str | None = None


@router.post("", response_model=CreateImportResponse, status_code=status.HTTP_201_CREATED)
async def create_import(
    payload: CreateImportRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CreateImportResponse:
    service = ImportsService(db, settings)
    import_id, presigned = await service.create_upload(
        user_id,
        payload.filename,
        payload.size_bytes,
        payload.sha256,
    )
    return CreateImportResponse(
        import_id=import_id,
        upload_url=presigned.upload_url,
        upload_method=presigned.upload_method,
        expires_at=presigned.expires_at,
        max_size_bytes=settings.max_upload_mb_free * 1024 * 1024,
    )


@router.post("/{import_id}/complete", status_code=status.HTTP_202_ACCEPTED)
async def complete_import(
    import_id: UUID,
    payload: CompleteImportRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    service = ImportsService(db, settings)
    if payload.raw_text is not None:
        await service.store_uploaded_content(user_id, import_id, payload.raw_text.encode("utf-8"))
    try:
        summary = await service.process_import(user_id, import_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Import not found") from exc
    return {"status": "processing", "summary": summary}


@router.get("")
async def list_imports(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    rows = await ImportsRepository(db).list_for_user(user_id)
    return {"data": [dict(row) for row in rows], "page": {"next_after": None, "has_more": False}}


@router.get("/{import_id}")
async def get_import(
    import_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    row = await ImportsRepository(db).get_for_user(user_id, import_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Import not found")
    return dict(row)


@router.get("/{import_id}/events")
async def import_events(import_id: UUID) -> str:
    return f'event: status\ndata: {{"import_id":"{import_id}","status":"done"}}\n\n'
