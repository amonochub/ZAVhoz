"""Tests for file handler."""

import pytest
from sqlalchemy import select

from models import User, Request, File


class TestFileHandler:
    """Test file upload and management."""

    async def _create_request(self, db_session: any) -> Request:
        """Helper to create test request."""
        user = User(telegram_id=700, username="file_user")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Request with files",
            description="Testing file attachments",
            location="Room 1",
        )
        db_session.add(request)
        await db_session.commit()

        return request

    @pytest.mark.asyncio
    async def test_attach_file_to_request(self, db_session: any) -> None:
        """Test attaching file to request."""
        request = await self._create_request(db_session)

        file = File(
            request_id=request.id,
            file_id="test_file_123",
            file_type="photo",
        )
        db_session.add(file)
        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        attached = await db_session.scalar(stmt)

        assert attached is not None
        assert attached.file_id == "test_file_123"

    @pytest.mark.asyncio
    async def test_multiple_files_per_request(self, db_session: any) -> None:
        """Test multiple files on single request."""
        request = await self._create_request(db_session)

        for i in range(3):
            file = File(
                request_id=request.id,
                file_id=f"file_{i}",
                file_type="photo",
            )
            db_session.add(file)

        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 3

    @pytest.mark.asyncio
    async def test_file_types(self, db_session: any) -> None:
        """Test different file types."""
        request = await self._create_request(db_session)

        file_types = ["photo", "document", "video"]
        for ftype in file_types:
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
        types = [f.file_type for f in files]
        assert "photo" in types
        assert "document" in types
        assert "video" in types
