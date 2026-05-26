from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping, desc, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import import_errors, imports


class ImportsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_import(self, values: dict[str, Any]) -> RowMapping:
        result = await self.session.execute(insert(imports).values(**values).returning(imports))
        return result.mappings().one()

    async def get_for_user(self, user_id: UUID, import_id: UUID) -> RowMapping | None:
        result = await self.session.execute(
            select(imports).where(imports.c.user_id == user_id, imports.c.id == import_id)
        )
        return result.mappings().one_or_none()

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> list[RowMapping]:
        result = await self.session.execute(
            select(imports)
            .where(imports.c.user_id == user_id)
            .order_by(desc(imports.c.created_at))
            .limit(limit)
        )
        return list(result.mappings().all())

    async def update_status(
        self,
        import_id: UUID,
        status: str,
        **values: Any,
    ) -> None:
        payload = dict(values)
        if status == "processing":
            payload.setdefault("started_at", datetime.now(UTC))
        if status in {"succeeded", "partial", "failed"}:
            payload.setdefault("finished_at", datetime.now(UTC))
        payload["status"] = status
        await self.session.execute(
            update(imports).where(imports.c.id == import_id).values(**payload)
        )

    async def add_error(
        self,
        import_id: UUID,
        line_start: int,
        line_end: int,
        raw_excerpt: str,
        error_code: str,
        error_message: str,
    ) -> None:
        await self.session.execute(
            insert(import_errors).values(
                import_id=import_id,
                line_start=line_start,
                line_end=line_end,
                raw_excerpt=raw_excerpt[:2000],
                error_code=error_code,
                error_message=error_message,
            )
        )
