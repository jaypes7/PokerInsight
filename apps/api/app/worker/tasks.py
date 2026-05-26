import asyncio
from uuid import UUID

from sqlalchemy.sql import Select

from app.core.config import get_settings
from app.db.session import SessionFactory
from app.services.imports import ImportsService
from app.worker.celery_app import celery_app


@celery_app.task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3}
)
def process_import(_task: object, import_id: str) -> dict[str, int]:
    return asyncio.run(_process_import(UUID(import_id)))


async def _process_import(import_id: UUID) -> dict[str, int]:
    async with SessionFactory() as session:
        # Worker receives trusted internal IDs; fetch user_id first to keep service tenant-aware.
        result = await session.execute(imports_table_select(import_id))
        row = result.mappings().one_or_none()
        if row is None:
            raise KeyError("import not found")
        return await ImportsService(session, get_settings()).process_import(
            row["user_id"], import_id
        )


def imports_table_select(import_id: UUID) -> Select[tuple[object]]:
    from sqlalchemy import select

    from app.db.schema import imports

    return select(imports).where(imports.c.id == import_id)
