"""Tests for File model."""

import pytest
from sqlalchemy import select

from models import User, Request, File


class TestFileModel:
    """Test File model creation and properties."""

    async def _create_request(self, db_session: any) -> Request:
        """Helper to create test request."""
        user = User(telegram_id=900, username="file_user")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Request with files",
            description="File testing",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        return request

    @pytest.mark.asyncio
    async def test_create_file(self, db_session: any) -> None:
        """Test creating a file attachment."""
        request = await self._create_request(db_session)

        file = File(
            request_id=request.id,
            file_id="tg_file_123",
            file_type="photo",
        )
        db_session.add(file)
        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        created = await db_session.scalar(stmt)

        assert created is not None
        assert created.file_id == "tg_file_123"
        assert created.file_type == "photo"

    @pytest.mark.asyncio
    async def test_file_types(self, db_session: any) -> None:
        """Test different file types."""
        request = await self._create_request(db_session)

        types = ["photo", "document", "video"]

        for ftype in types:
            file = File(
                request_id=request.id,
                file_id=f"file_{ftype}",
                file_type=ftype,
            )
            db_session.add(file)

        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 3
        assert any(f.file_type == "photo" for f in files)
        assert any(f.file_type == "document" for f in files)
        assert any(f.file_type == "video" for f in files)

    @pytest.mark.asyncio
    async def test_file_relationship_to_request(self, db_session: any) -> None:
        """Test file relationship to request."""
        request = await self._create_request(db_session)

        file = File(
            request_id=request.id,
            file_id="related_file",
            file_type="photo",
        )
        db_session.add(file)
        await db_session.commit()

        stmt = select(File).where(File.id == file.id)
        retrieved = await db_session.scalar(stmt)

        assert retrieved.request_id == request.id

    @pytest.mark.asyncio
    async def test_file_timestamps(self, db_session: any) -> None:
        """Test file creation timestamp."""
        request = await self._create_request(db_session)

        file = File(
            request_id=request.id,
            file_id="timestamped_file",
            file_type="document",
        )
        db_session.add(file)
        await db_session.commit()

        stmt = select(File).where(File.id == file.id)
        retrieved = await db_session.scalar(stmt)

        assert retrieved.uploaded_at is not None
