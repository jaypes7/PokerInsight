import hashlib
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.repositories.hands import HandsRepository
from app.db.repositories.imports import ImportsRepository
from app.parser.assembler import parse_hand
from app.parser.errors import ParseError
from app.parser.splitter import decode_hand_history, split_hands
from app.services.storage import ObjectStorage, PresignedPut


class ImportsService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.imports = ImportsRepository(session)
        self.hands = HandsRepository(session)
        self.storage = ObjectStorage(settings)

    async def create_upload(
        self,
        user_id: UUID,
        filename: str,
        size_bytes: int,
        sha256: str,
    ) -> tuple[UUID, PresignedPut]:
        empty = await self.imports.create_import(
            {
                "user_id": user_id,
                "original_filename": filename,
                "file_size_bytes": size_bytes,
                "file_hash": sha256,
                "storage_key": "pending",
            }
        )
        import_id = empty["id"]
        presigned = self.storage.generate_presigned_put(user_id, import_id)
        await self.imports.update_status(import_id, "pending", storage_key=presigned.storage_key)
        await self.session.commit()
        return import_id, presigned

    async def store_uploaded_content(self, user_id: UUID, import_id: UUID, content: bytes) -> None:
        row = await self.imports.get_for_user(user_id, import_id)
        if row is None:
            raise KeyError("import not found")
        await self.storage.put_object(row["storage_key"], content)
        await self.imports.update_status(
            import_id, "uploaded", file_hash=hashlib.sha256(content).hexdigest()
        )
        await self.session.commit()

    async def process_import(self, user_id: UUID, import_id: UUID) -> dict[str, int]:
        row = await self.imports.get_for_user(user_id, import_id)
        if row is None:
            raise KeyError("import not found")
        await self.imports.update_status(import_id, "processing")
        content = await self.storage.get_object(row["storage_key"])
        text = decode_hand_history(content)
        chunks = ["\n".join(lines) for lines in split_hands(text.splitlines())]
        drafts = []
        errors = 0
        for chunk in chunks:
            try:
                drafts.append(parse_hand(chunk))
            except ParseError as exc:
                errors += 1
                await self.imports.add_error(
                    import_id,
                    exc.line_start,
                    exc.line_end,
                    exc.raw_excerpt or chunk[:2000],
                    exc.code,
                    exc.message,
                )
        imported = await self.hands.insert_many(user_id, import_id, drafts)
        status = "succeeded" if errors == 0 else "partial"
        await self.imports.update_status(
            import_id,
            status,
            total_hands_detected=len(chunks),
            total_hands_imported=imported,
            total_hands_duplicate=max(len(drafts) - imported, 0),
            total_errors=errors,
        )
        await self.session.commit()
        return {"detected": len(chunks), "imported": imported, "errors": errors}
