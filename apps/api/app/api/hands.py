from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.repositories.hands import HandsRepository
from app.db.session import get_db

router = APIRouter(prefix="/v1/hands", tags=["hands"])


@router.get("")
async def list_hands(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
) -> dict[str, object]:
    rows = await HandsRepository(db).list_for_user(user_id, min(limit, 200))
    return {"data": [dict(row) for row in rows], "page": {"next_after": None, "has_more": False}}


@router.get("/{hand_id}")
async def get_hand(
    hand_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    detail = await HandsRepository(db).get_detail_for_user(user_id, hand_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Hand not found")
    return {
        "hand": dict(detail["hand"]),
        "seats": [dict(row) for row in detail["seats"]],
        "actions": [dict(row) for row in detail["actions"]],
        "pots": [dict(row) for row in detail["pots"]],
    }


@router.get("/{hand_id}/raw", response_class=PlainTextResponse)
async def get_raw_hand(
    hand_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> str:
    row = await HandsRepository(db).get_for_user(user_id, hand_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Hand not found")
    return str(row["raw_text"])
